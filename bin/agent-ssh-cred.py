#!/usr/bin/env python3
"""
agent-ssh-cred 鈥?鍑嵁绠＄悊 CLI

鍩轰簬 Windows DPAPI 鍔犲瘑瀛樺偍 SSH 瀵嗙爜鍒?credentials.txt銆?鍔犲瘑鏁版嵁缁戝畾鍒板綋鍓嶇敤鎴风櫥褰曚細璇濓紝鍏朵粬鐢ㄦ埛/绋嬪簭鏃犳硶瑙ｅ瘑銆?
鐢ㄦ硶:
    python bin/agent-ssh-cred.py store <key> <password>
        鍔犲瘑瀛樺偍瀵嗙爜锛坘ey 閫氬父涓?IP 鎴?user@host锛?
    python bin/agent-ssh-cred.py get <key>
        瑙ｅ瘑骞惰緭鍑哄瘑鐮佺殑 Base64 缂栫爜锛堝彲鐩存帴鍠傜粰 --password-base64锛?
    python bin/agent-ssh-cred.py get-plain <key>
        瑙ｅ瘑骞惰緭鍑烘槑鏂囧瘑鐮侊紙浠呰皟璇曠敤锛屼笉瑕佸湪鐢熶骇涓娇鐢級

    python bin/agent-ssh-cred.py list
        鍒楀嚭鎵€鏈夊嚟鎹?key 鍙婂叾鍔犲瘑鏂瑰紡

    python bin/agent-ssh-cred.py delete <key>
        鍒犻櫎鎸囧畾鍑嵁

    python bin/agent-ssh-cred.py migrate
        鎵弿骞跺崌绾ф墍鏈夋棫鐗堝嚟鎹负 DPAPI 鍔犲瘑

绀轰緥:
    python bin/agent-ssh-cred.py store 192.168.1.100 MySecret123
    python bin/agent-ssh-cred.py get 192.168.1.100
    # 杈撳嚭: <base64 缂栫爜鐨勫瘑鐮?锛堝彲鐩存帴鐢ㄤ綔 --password-base64锛?
闆嗘垚鍒?SSH 鍛戒护:
    $pw = python bin/agent-ssh-cred.py get 192.168.1.100
    python bin/agent-ssh-run.py root@192.168.1.100 "df -h" --password-base64 $pw
"""

import sys
import os
import base64
import argparse
from pathlib import Path

# 灏嗘妧鑳芥牴鐩綍鍔犲叆 sys.path
HERE = Path(__file__).resolve().parent
SKILL_HOME = HERE.parent
sys.path.insert(0, str(SKILL_HOME))

from agent_ssh_audit.crypto import (
    encrypt_password,
    decrypt_password,
    get_credential,
    store_credential,
    list_credentials,
    delete_credential,
    is_encrypted,
    migrate_if_needed,
)
from agent_ssh_audit import storage


def _cred_file() -> Path:
    """credentials.txt 璺緞"""
    return storage.get_home().parent / "credentials.txt"


def cmd_store(args):
    """鍔犲瘑瀛樺偍瀵嗙爜"""
    pw = args.password
    if not pw:
        # 浜や簰寮忚緭鍏ワ紙涓嶅洖鏄撅級
        import getpass as gp
        pw = gp.getpass(f"璇疯緭鍏?{args.key} 鐨勫瘑鐮? ")
        confirm = gp.getpass("鍐嶆杈撳叆纭: ")
        if pw != confirm:
            print("閿欒: 涓ゆ杈撳叆涓嶄竴鑷?, file=sys.stderr)
            sys.exit(1)

    cf = _cred_file()
    store_credential(args.key, pw, cf)
    print(f"宸插姞瀵嗗瓨鍌? {args.key} 鈫?{cf}")


def cmd_get(args):
    """瑙ｅ瘑鑾峰彇瀵嗙爜锛圔ase64 杈撳嚭锛?""
    cf = _cred_file()
    pw = get_credential(args.key, cf)
    if pw is None:
        print(f"閿欒: 鏈壘鍒板嚟鎹?'{args.key}'", file=sys.stderr)
        sys.exit(1)
    # 杈撳嚭 Base64 缂栫爜锛堝彲鐩存帴鐢ㄤ簬 --password-base64锛?    print(base64.b64encode(pw.encode("utf-8")).decode("ascii"))


def cmd_get_plain(args):
    """瑙ｅ瘑鑾峰彇瀵嗙爜锛堟槑鏂囷紝浠呰皟璇曠敤锛?""
    cf = _cred_file()
    pw = get_credential(args.key, cf)
    if pw is None:
        print(f"閿欒: 鏈壘鍒板嚟鎹?'{args.key}'", file=sys.stderr)
        sys.exit(1)
    print(pw)


def cmd_list(args):
    """鍒楀嚭鎵€鏈夊嚟鎹?""
    cf = _cred_file()
    creds = list_credentials(cf)
    if not creds:
        print("(鏃犲嚟鎹?")
        return

    # 琛ㄦ牸杈撳嚭
    max_key = max(len(k) for k, _ in creds) if creds else 10
    print(f"{'KEY':<{max_key}}  {'鍔犲瘑鏂瑰紡'}")
    print(f"{'-'*max_key}  {'-'*20}")
    for key, method in creds:
        flag = "鉁? if method == "DPAPI" else "鈿?
        print(f"{key:<{max_key}}  {flag} {method}")

    legacy_count = sum(1 for _, m in creds if m != "DPAPI")
    if legacy_count:
        print(f"\n鈿?鏈?{legacy_count} 鏉℃棫鐗堝嚟鎹紝杩愯 'migrate' 鍗囩骇涓?DPAPI 鍔犲瘑銆?)


def cmd_delete(args):
    """鍒犻櫎鍑嵁"""
    cf = _cred_file()
    ok = delete_credential(args.key, cf)
    if ok:
        print(f"宸插垹闄? {args.key}")
    else:
        print(f"鏈壘鍒? {args.key}", file=sys.stderr)
        sys.exit(1)


def cmd_migrate(args):
    """鎵弿骞跺崌绾ф墍鏈夋棫鐗堝嚟鎹负 DPAPI"""
    cf = _cred_file()
    if not cf.exists():
        print("credentials.txt 涓嶅瓨鍦紝鏃犻渶杩佺Щ銆?)
        return

    lines = cf.read_text(encoding="utf-8-sig").splitlines()
    migrated = 0
    for line in lines:
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
            continue  # 宸叉槸 DPAPI锛岃烦杩?
        # 灏濊瘯杩佺Щ锛堣嚜鍔ㄨ瘑鍒?Fernet / Base64 绛夋棫鏍煎紡锛?        try:
            migrate_if_needed(k.strip(), v, cf)
            migrated += 1
            print(f"  宸插崌绾? {k.strip()}")
        except Exception as e:
            print(f"  鍗囩骇澶辫触: {k.strip()} 鈥?{e}", file=sys.stderr)

    if migrated:
        print(f"\n鍏卞崌绾?{migrated} 鏉″嚟鎹负 DPAPI 鍔犲瘑銆?)
    else:
        print("娌℃湁闇€瑕佽縼绉荤殑鏃х増鍑嵁銆?)


def main():
    p = argparse.ArgumentParser(
        description="SSH 鍑嵁绠＄悊 鈥?Windows DPAPI 鍔犲瘑瀛樺偍",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
绀轰緥:
  %(prog)s store 192.168.1.100 MyP@ss         # 鍔犲瘑瀛樺偍
  %(prog)s get 192.168.1.100                   # 鑾峰彇 Base64锛堢敤浜?--password-base64锛?  %(prog)s get-plain 192.168.1.100             # 鑾峰彇鏄庢枃锛堣皟璇曠敤锛?  %(prog)s list                                # 鍒楀嚭鎵€鏈?  %(prog)s delete 192.168.1.100                # 鍒犻櫎
  %(prog)s migrate                             # 鍗囩骇鏃х増鍑嵁
        """,
    )
    sub = p.add_subparsers(dest="command", required=True)

    # store
    sp = sub.add_parser("store", help="鍔犲瘑瀛樺偍瀵嗙爜")
    sp.add_argument("key", help="鍑嵁鏍囪瘑锛堝 IP 鎴?user@host锛?)
    sp.add_argument("password", nargs="?", help="瀵嗙爜锛堢渷鐣ュ垯浜や簰杈撳叆锛?)
    sp.set_defaults(func=cmd_store)

    # get
    sp = sub.add_parser("get", help="瑙ｅ瘑鑾峰彇瀵嗙爜锛圔ase64 杈撳嚭锛?)
    sp.add_argument("key", help="鍑嵁鏍囪瘑")
    sp.set_defaults(func=cmd_get)

    # get-plain
    sp = sub.add_parser("get-plain", help="瑙ｅ瘑鑾峰彇瀵嗙爜锛堟槑鏂囷紝璋冭瘯鐢級")
    sp.add_argument("key", help="鍑嵁鏍囪瘑")
    sp.set_defaults(func=cmd_get_plain)

    # list
    sp = sub.add_parser("list", help="鍒楀嚭鎵€鏈夊嚟鎹?)
    sp.set_defaults(func=cmd_list)

    # delete
    sp = sub.add_parser("delete", help="鍒犻櫎鍑嵁")
    sp.add_argument("key", help="鍑嵁鏍囪瘑")
    sp.set_defaults(func=cmd_delete)

    # migrate
    sp = sub.add_parser("migrate", help="鍗囩骇鏃х増鍑嵁涓?DPAPI 鍔犲瘑")
    sp.set_defaults(func=cmd_migrate)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
