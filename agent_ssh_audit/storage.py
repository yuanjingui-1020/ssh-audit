"""
存储路径管理
- 默认根目录: ssh-audit - v2 目录下的 logs/（基于脚本位置的相对路径）
- 可用 AGENT_SSH_AUDIT_HOME 环境变量覆盖（不设则自动用相对路径）
- 结构:
    logs/
        sessions/
            2026-06-27/
                <session_id>.jsonl
        index.jsonl
"""
import os
import json
import secrets
from datetime import datetime
from pathlib import Path


def _default_home() -> Path:
    """基于脚本位置计算默认日志目录：ssh-audit - v2 目录下的 LOGS"""
    this_file = Path(__file__).resolve()
    # storage.py → agent_ssh_audit/ → ssh-audit - v2/
    return this_file.parent.parent / "logs"


def _read_machine_env(name: str) -> str | None:
    """从 Windows 注册表读取 Machine 级环境变量（兜底）"""
    if os.name != "nt":
        return None
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        )
        try:
            return winreg.QueryValueEx(key, name)[0]
        finally:
            winreg.CloseKey(key)
    except Exception:
        return None


def get_home() -> Path:
    h = os.environ.get("AGENT_SSH_AUDIT_HOME")
    if not h:
        h = _read_machine_env("AGENT_SSH_AUDIT_HOME")
    if not h:
        h = str(_default_home())
    h = Path(h)
    h.mkdir(parents=True, exist_ok=True)
    return h


def session_dir(date: datetime = None) -> Path:
    """某天的 session 目录"""
    d = (date or datetime.now()).strftime("%Y-%m-%d")
    p = get_home() / "sessions" / d
    p.mkdir(parents=True, exist_ok=True)
    return p


def new_session_id(host: str = "", user: str = "") -> str:
    """生成 session_id: <时间戳>_<host>_<user>_<3位随机>"""
    parts = [datetime.now().strftime("%Y%m%d_%H%M%S")]
    if user:
        parts.append(user)
    if host:
        parts.append(host.replace(".", "_"))
    parts.append(secrets.token_hex(2))
    return "_".join(parts)


def session_log_path(session_id: str, date: datetime = None) -> Path:
    return session_dir(date) / f"{session_id}.jsonl"


def index_path() -> Path:
    return get_home() / "index.jsonl"


def append_index(record: dict) -> None:
    p = index_path()
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def list_sessions(limit: int = 50) -> list:
    """读 index.jsonl, 返回最近的 session 列表"""
    p = index_path()
    if not p.exists():
        return []
    records = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    # 只保留 open 事件对应的 session, 后写 closed 会覆盖 status
    sessions = {}
    for r in records:
        sid = r.get("session_id")
        if sid:
            sessions[sid] = r
    # 时间倒序
    out = list(sessions.values())
    out.sort(key=lambda x: x.get("ts", ""), reverse=True)
    return out[:limit]


def find_session_log(session_id: str) -> Path:
    """在 sessions/ 目录下找给定 session_id 的 .jsonl 文件"""
    home = get_home()
    sessions_root = home / "sessions"
    if not sessions_root.exists():
        raise FileNotFoundError(f"找不到 session: {session_id}")
    for path in sessions_root.rglob(f"{session_id}.jsonl"):
        return path
    raise FileNotFoundError(f"找不到 session: {session_id}")
