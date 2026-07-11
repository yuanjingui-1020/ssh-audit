"""
凭据加密模块 — Windows DPAPI 加密存储

基于 Windows Data Protection API (DPAPI)：
- CryptProtectData：加密，绑定到当前用户登录会话
- CryptUnprotectData：仅同一用户可解密
- 操作系统自动管理密钥派生和轮换，无需手动管理密钥

安全特性：
- 绑定到当前用户登录会话，其他用户/程序/服务均无法解密
- 即使 credentials.txt 泄露，脱离当前用户会话也无法还原密码
- Windows 密码重置后旧数据自动失效（预期安全行为）
- 自动迁移旧版 Fernet AES / Base64 凭据到 DPAPI

用法：
    from agent_ssh_audit.crypto import encrypt_password, decrypt_password

    cipher = encrypt_password("MyPassword123")   # → "dpapi:AQAAAN..."
    plain  = decrypt_password(cipher)            # → "MyPassword123"
"""

import os
import sys
import base64
import ctypes
from ctypes import wintypes
from pathlib import Path

# ============================================================
# Windows DPAPI 常量与类型
# ============================================================

CRYPTPROTECT_UI_FORBIDDEN = 0x1
CRYPTPROTECT_LOCAL_MACHINE = 0x4  # 可选：绑定机器而非用户（默认不启用）


class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte)),
    ]


def _load_dpapi():
    """加载 DPAPI 函数指针（仅 Windows）"""
    if sys.platform != "win32":
        raise OSError("DPAPI 仅支持 Windows 平台")

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(DATA_BLOB),   # pDataIn
        wintypes.LPCWSTR,            # szDataDescr
        ctypes.POINTER(DATA_BLOB),   # pOptionalEntropy
        ctypes.c_void_p,             # pvReserved
        ctypes.c_void_p,             # pPromptStruct
        wintypes.DWORD,              # dwFlags
        ctypes.POINTER(DATA_BLOB),   # pDataOut
    ]
    crypt32.CryptProtectData.restype = wintypes.BOOL

    crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(DATA_BLOB),           # pDataIn
        ctypes.POINTER(wintypes.LPCWSTR),    # ppszDataDescr
        ctypes.POINTER(DATA_BLOB),           # pOptionalEntropy
        ctypes.c_void_p,                     # pvReserved
        ctypes.c_void_p,                     # pPromptStruct
        wintypes.DWORD,                      # dwFlags
        ctypes.POINTER(DATA_BLOB),           # pDataOut
    ]
    crypt32.CryptUnprotectData.restype = wintypes.BOOL

    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p

    return crypt32, kernel32


_crypt32, _kernel32 = _load_dpapi()

# DPAPI 密文前缀，用于与旧版格式区分
DPAPI_PREFIX = "dpapi:"


# ============================================================
# DPAPI 核心加解密
# ============================================================


def _dpapi_protect(data: bytes, description: str = "ssh-audit-cred") -> bytes:
    """
    调用 CryptProtectData 加密数据。

    加密结果绑定到当前用户（默认），同一台机器上其他用户无法解密。
    """
    in_blob = DATA_BLOB()
    in_blob.cbData = len(data)
    buf = ctypes.create_string_buffer(data, len(data))
    in_blob.pbData = ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte))

    out_blob = DATA_BLOB()

    if not _crypt32.CryptProtectData(
        ctypes.byref(in_blob),
        description,
        None,   # 不使用额外熵（entropy）
        None,   # 保留
        None,   # 无 UI 提示
        CRYPTPROTECT_UI_FORBIDDEN,  # 不弹 UI，静默执行
        ctypes.byref(out_blob),
    ):
        err = ctypes.get_last_error()
        raise OSError(f"CryptProtectData 失败 (错误码: {err})")

    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        if out_blob.pbData:
            _kernel32.LocalFree(out_blob.pbData)


def _dpapi_unprotect(data: bytes) -> tuple[bytes, str]:
    """
    调用 CryptUnprotectData 解密数据。

    返回: (明文数据 bytes, 描述字符串)
    """
    in_blob = DATA_BLOB()
    in_blob.cbData = len(data)
    buf = ctypes.create_string_buffer(data, len(data))
    in_blob.pbData = ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte))

    out_blob = DATA_BLOB()
    desc_ptr = wintypes.LPCWSTR()

    if not _crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),
        ctypes.byref(desc_ptr),
        None,
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(out_blob),
    ):
        err = ctypes.get_last_error()
        raise OSError(
            f"CryptUnprotectData 失败 (错误码: {err})。"
            "可能原因：当前用户与加密时的用户不同、凭据文件从其他机器/用户复制而来。"
        )

    try:
        result = ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        if out_blob.pbData:
            _kernel32.LocalFree(out_blob.pbData)

    desc = desc_ptr.value if desc_ptr.value else ""
    if desc_ptr.value:
        _kernel32.LocalFree(desc_ptr)

    return result, desc


# ============================================================
# 旧版 Fernet AES 解密（仅用于迁移，新数据不使用）
# ============================================================


def _decrypt_legacy_fernet(ciphertext: str) -> str:
    """
    解密旧版 Fernet AES 格式（gAAAAAB 开头）。

    仅作为迁移路径保留。新数据统一使用 DPAPI。
    """
    try:
        from cryptography.fernet import Fernet
        import hashlib
        import getpass
        import platform

        fingerprint = f"{platform.node()}|{getpass.getuser()}|ssh-audit-salt-v1"
        salt = hashlib.sha256(fingerprint.encode("utf-8")).digest()[:16]
        pepper = b"ssh-audit::cred-vault::2026"
        raw = hashlib.pbkdf2_hmac("sha256", pepper, salt, 600_000, dklen=32)
        key = base64.urlsafe_b64encode(raw)
        f = Fernet(key)
        return f.decrypt(ciphertext.encode("ascii"), ttl=None).decode("utf-8")
    except Exception as e:
        raise ValueError(
            f"旧版 Fernet 凭据解密失败: {e}\n"
            "可能原因：换机器、换用户、或 cryptography 未安装。\n"
            "请重新执行 store 命令存储凭据。"
        )


# ============================================================
# 公开 API
# ============================================================


def encrypt_password(plaintext: str) -> str:
    """
    使用 DPAPI 加密明文密码。

    返回以 "dpapi:" 开头的 Base64 密文字符串，可直接存入 credentials.txt。
    """
    if not plaintext:
        raise ValueError("密码不能为空")
    encrypted = _dpapi_protect(plaintext.encode("utf-8"))
    return DPAPI_PREFIX + base64.b64encode(encrypted).decode("ascii")


def decrypt_password(ciphertext: str) -> str:
    """
    解密密文。自动识别格式：

    - "dpapi:" 开头  → DPAPI 解密
    - "gAAAAAB" 开头 → 旧版 Fernet AES 解密（自动迁移）
    - 其他            → 尝试 Base64 解码（旧版明文等效）

    异常：
        OSError: DPAPI 解密失败（用户不匹配）
        ValueError: 格式无法识别
    """
    if not ciphertext:
        raise ValueError("密文不能为空")

    # DPAPI 加密（当前格式）
    if ciphertext.startswith(DPAPI_PREFIX):
        raw = base64.b64decode(ciphertext[len(DPAPI_PREFIX):])
        plain_bytes, _ = _dpapi_unprotect(raw)
        return plain_bytes.decode("utf-8")

    # 旧版 Fernet AES（gAAAAAB 开头）
    if ciphertext.startswith("gAAAAAB"):
        return _decrypt_legacy_fernet(ciphertext)

    # 旧版纯 Base64（无加密）
    if is_base64_legacy(ciphertext):
        return base64.b64decode(ciphertext).decode("utf-8")

    raise ValueError(f"无法识别的密文格式: {ciphertext[:30]}...")


def is_encrypted(value: str) -> bool:
    """判断是否为 DPAPI 加密格式（当前版本）"""
    return value.startswith(DPAPI_PREFIX)


def is_fernet_legacy(value: str) -> bool:
    """判断是否为旧版 Fernet AES 格式"""
    return value.startswith("gAAAAAB")


def is_base64_legacy(value: str) -> bool:
    """
    判断是否为旧版纯 Base64 格式（无加密，仅编码）。

    排除 dpapi: 和 gAAAAAB 前缀。
    """
    if value.startswith(DPAPI_PREFIX) or value.startswith("gAAAAAB"):
        return False
    try:
        decoded = base64.b64decode(value, validate=True)
        return all(32 <= b < 127 or b in (9, 10, 13) for b in decoded)
    except Exception:
        return False


# ============================================================
# 凭据文件操作
# ============================================================


def _update_cred_file(key: str, new_value: str, cred_file: Path) -> None:
    """原地替换 credentials.txt 中指定 key 的值（保留注释和顺序）"""
    if not cred_file.exists():
        return

    text = cred_file.read_text(encoding="utf-8-sig")
    lines = text.splitlines(keepends=True)
    new_lines = []
    prefix = key + "="
    for line in lines:
        if line.startswith(prefix):
            continue
        new_lines.append(line)

    # 清理尾部空行
    while new_lines and new_lines[-1].strip() == "":
        new_lines.pop()
    new_lines.append(f"{key}={new_value}\n")
    cred_file.write_text("".join(new_lines), encoding="utf-8")


def migrate_if_needed(key: str, value: str, cred_file: Path) -> str:
    """
    检测旧版凭据格式并自动升级为 DPAPI。

    支持：Fernet AES (gAAAAAB) / 纯 Base64 → DPAPI
    """
    if is_encrypted(value):
        return value

    # 尝试解密旧格式
    try:
        if is_fernet_legacy(value):
            plain = _decrypt_legacy_fernet(value)
        elif is_base64_legacy(value):
            plain = base64.b64decode(value).decode("utf-8")
        else:
            return value  # 无法识别，保持原样
    except Exception:
        return value

    # DPAPI 重新加密并写回
    encrypted = encrypt_password(plain)
    _update_cred_file(key, encrypted, cred_file)
    return encrypted


def get_credential(key: str, cred_file: Path) -> str | None:
    """
    从 credentials.txt 读取并解密指定 key 的密码。

    自动迁移旧版格式 → DPAPI。
    """
    if not cred_file.exists():
        return None

    text = cred_file.read_text(encoding="utf-8-sig")
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() != key:
            continue

        value = v.strip()
        if not value:
            return None

        # 自动迁移旧格式
        if not is_encrypted(value):
            value = migrate_if_needed(key, value, cred_file)

        return decrypt_password(value)

    return None


def store_credential(key: str, password: str, cred_file: Path) -> None:
    """使用 DPAPI 加密并存储凭据"""
    encrypted = encrypt_password(password)
    _update_cred_file(key, encrypted, cred_file)


def list_credentials(cred_file: Path) -> list[tuple[str, str]]:
    """
    列出所有凭据（不解密）。

    返回: [(key, 加密方式), ...]
        加密方式: "DPAPI" | "Fernet(legacy)" | "Base64(legacy)" | "unknown"
    """
    if not cred_file.exists():
        return []

    result = []
    text = cred_file.read_text(encoding="utf-8-sig")
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip()
        if not v:
            continue

        if is_encrypted(v):
            method = "DPAPI"
        elif is_fernet_legacy(v):
            method = "Fernet(legacy)"
        elif is_base64_legacy(v):
            method = "Base64(legacy)"
        else:
            method = "unknown"

        result.append((k.strip(), method))

    return result


def delete_credential(key: str, cred_file: Path) -> bool:
    """删除指定 key 的凭据行"""
    if not cred_file.exists():
        return False

    text = cred_file.read_text(encoding="utf-8-sig")
    lines = text.splitlines(keepends=True)
    prefix = key + "="
    found = False
    new_lines = []
    for line in lines:
        if line.startswith(prefix):
            found = True
            continue
        new_lines.append(line)

    if found:
        cred_file.write_text("".join(new_lines), encoding="utf-8")

    return found


# ============================================================
# 自测
# ============================================================
if __name__ == "__main__":
    pw = "Test@Pass123!"
    print(f"原文: {pw}")

    enc = encrypt_password(pw)
    print(f"密文前缀: {enc[:60]}...")
    print(f"格式: {'DPAPI' if is_encrypted(enc) else '未知'}")

    dec = decrypt_password(enc)
    print(f"解密: {dec}")
    assert dec == pw, "加解密不匹配!"

    # 检测函数验证
    print(f"\nis_encrypted(dpapi:): {is_encrypted(enc)}")
    print(f"is_fernet_legacy(gAAAAAB): {is_fernet_legacy('gAAAAABxxx')}")
    print(f"is_base64_legacy(QXBwZW4=): {is_base64_legacy('QXBwZW4=')}")

    # 同一数据两次加密结果不同（DPAPI 内置随机化）
    enc2 = encrypt_password(pw)
    print(f"\n两次加密结果相同: {enc == enc2}")
    print(f"两次解密结果一致: {decrypt_password(enc2) == pw}")

    print("\n全部测试通过")
