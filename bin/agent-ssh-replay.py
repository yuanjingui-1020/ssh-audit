#!/usr/bin/env python3
"""
agent-ssh-replay — 回放 session

用法:
    python agent-ssh-replay.py <session_id>            # 默认 text 模式
    python agent-ssh-replay.py <session_id> --json     # 原始 JSON 事件流
    python agent-ssh-replay.py <session_id> --stream   # 仅 c2s/s2c 字节流
    python agent-ssh-replay.py --list                  # 列最近 sessions
    python agent-ssh-replay.py --latest                # 回放最近一次
"""
import sys
import io
import argparse
from pathlib import Path

# Windows 终端兼容: gbk/cp936 无法输出 emoji -> 自动换 UTF-8
if sys.platform == "win32" and isinstance(sys.stdout, io.TextIOWrapper):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from agent_ssh_audit import storage, replay


def main():
    p = argparse.ArgumentParser(description="Agent SSH replay")
    p.add_argument("session_id", nargs="?", help="session_id(或 --list / --latest)")
    p.add_argument("--list", "-l", action="store_true", help="列最近 sessions")
    p.add_argument("--latest", action="store_true", help="回放最近一次")
    p.add_argument("--json", action="store_true", help="原始 JSON 事件流")
    p.add_argument("--stream", action="store_true", help="仅 c2s/s2c 字节流")
    p.add_argument("--keep-ansi", action="store_true", help="保留 ANSI")
    args = p.parse_args()

    if args.list:
        rows = storage.list_sessions(limit=50)
        print(f"{'SESSION ID':<55} {'HOST':<25} {'STATUS':<10} {'DURATION':<12} {'EVENTS':<6}")
        print("-" * 110)
        for r in rows:
            dur = f"{r.get('total_duration_ms', 0)} ms" if r.get('status') == 'closed' else "-"
            ev = r.get('event_count', '-')
            host = f"{r.get('user')}@{r.get('host')}:{r.get('port')}"
            print(f"{r.get('session_id'):<55} {host:<25} {r.get('status'):<10} {dur:<12} {ev}")
        print(f"\n共 {len(rows)} 条 session")
        print(f"日志目录: {storage.get_home()}")
        return

    sid = args.session_id
    if args.latest:
        rows = storage.list_sessions(limit=1)
        if not rows:
            print("暂无 session", file=sys.stderr)
            sys.exit(1)
        sid = rows[0]["session_id"]

    if not sid:
        p.error("需要 session_id 或 --list / --latest")

    try:
        path = storage.find_session_log(sid)
    except FileNotFoundError as e:
        print(f"错误: {e}", file=sys.stderr)
        print("提示: 用 --list 列已有 session", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(replay.replay_json(path))
    elif args.stream:
        print(replay.replay_raw_stream(path))
    else:
        print(replay.replay_text(path, ansi_strip=not args.keep_ansi))


if __name__ == "__main__":
    main()
