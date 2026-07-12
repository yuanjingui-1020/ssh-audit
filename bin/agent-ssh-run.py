#!/usr/bin/env python3
"""
agent-ssh-run — 跑 SSH 命令,自动 JSONL 审计

用法:
    python agent-ssh-run.py user@host "ls -la /etc" --password xxx
    python agent-ssh-run.py user@host "ls -la /etc" --key ~/.ssh/id_ed25519
    python agent-ssh-run.py user@host --batch cmds.txt
    echo "cmds" | python agent-ssh-run.py user@host --password xxx --batch -

安全增强:
    --password-base64  Base64 编码的密码(避免明文出现在进程列表)
    默认自动清除 AGENT_SSH_PASSWORD 环境变量(退出时)
"""
import sys
import os
import json
import base64
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from agent_ssh_audit import SSHAuditClient, storage, cmd_learner


def parse_target(target: str, default_port: int = 22):
    if "@" not in target:
        raise ValueError("target 必须是 user@host[:port]")
    user, host_port = target.split("@", 1)
    if ":" in host_port:
        host, port_s = host_port.split(":", 1)
        port = int(port_s) or default_port
    else:
        host, port = host_port, default_port
    return user, host, port


def read_password() -> str:
    # 优先级: --password > env AGENT_SSH_PASSWORD > stdin (隐藏回显)
    pw = os.environ.get("AGENT_SSH_PASSWORD")
    if pw:
        return pw
    print("password> ", end="", flush=True, file=sys.stderr)
    try:
        import getpass
        return getpass.getpass("")
    except Exception:
        return sys.stdin.readline().rstrip("\n")


# ──────────────────────────────────────────
# 命令展示辅助函数
# ──────────────────────────────────────────


def _print_cmd_header(cmd: str, user: str, host: str):
    """单条命令的展示头"""
    print(f"\n[agent-ssh] ──▶ {user}@{host} 执行命令:", file=sys.stderr)
    print(f"[agent-ssh]     $ {cmd}", file=sys.stderr)
    print(f"[agent-ssh]     ────────────────────────", file=sys.stderr)


def _print_cmd(cmd: str, idx: int = 1):
    """批量模式下展示单条命令"""
    print(f"[agent-ssh]   [{idx}] $ {cmd}", file=sys.stderr)


def _log_executed_cmd(cmd: str, user: str, host: str, sid: str, note: str = ""):
    """将执行过的命令写入学习日志(Markdown)"""
    try:
        cmd_learner.log_command(
            cmd=cmd, user=user, host=host,
            session_id=sid, note=note,
        )
    except Exception as e:
        print(f"[agent-ssh] 学习日志写入失败: {e}", file=sys.stderr)


def main():
    p = argparse.ArgumentParser(description="Agent SSH runner with audit")
    p.add_argument("target", help="user@host[:port]")
    p.add_argument("cmd", nargs="?", help="要执行的命令(单条)")
    p.add_argument("--password", help="密码(也可走 stdin / env AGENT_SSH_PASSWORD)")
    p.add_argument("--password-base64", help="Base64 编码的密码(避免密码出现在进程列表)")
    p.add_argument("--key", help="私钥路径")
    p.add_argument("--port", type=int, default=22)
    p.add_argument("--timeout", type=float, default=60.0)
    p.add_argument("--batch", help="批量命令文件路径(- 表示 stdin)")
    p.add_argument("--shell", action="store_true", help="开交互式 shell")
    p.add_argument("--meta", help="元信息(JSON)")
    p.add_argument("--stop-on-error", action="store_true")
    p.add_argument("--show-commands", action=argparse.BooleanOptionalAction,
                    default=True,
                    help="展示执行的命令及其解释(默认开启)")
    p.add_argument("--no-env-cleanup", action="store_true",
                    help="不自动清除 AGENT_SSH_PASSWORD 环境变量(调试用)")
    args = p.parse_args()

    user, host, port = parse_target(args.target, args.port)

    # 密码优先级: --password > --password-base64 > env > stdin
    password = args.password
    if not password and args.password_base64:
        try:
            password = base64.b64decode(args.password_base64).decode("utf-8")
        except Exception as e:
            print(f"[agent-ssh] FATAL: --password-base64 解码失败: {e}", file=sys.stderr)
            sys.exit(1)
    if not args.key and not password:
        password = read_password()
    elif not args.key and password:
        # 设置环境变量供后续使用(exit 时清理)
        os.environ["AGENT_SSH_PASSWORD"] = password

    meta = json.loads(args.meta) if args.meta else {}

    sid = storage.new_session_id(host=host, user=user)
    print(f"[agent-ssh] session: {sid}", file=sys.stderr)
    print(f"[agent-ssh] target:  {user}@{host}:{port}", file=sys.stderr)
    print(f"[agent-ssh] log:     {storage.session_log_path(sid)}", file=sys.stderr)

    try:
        with SSHAuditClient(
            host=host, user=user, port=port,
            password=password, key_filename=args.key,
            extra_audit_meta=meta,
            session_id=sid,
        ) as c:
            if args.shell:
                # shell 模式：走 agent-ssh-shell.py，这里只是兜底兼容
                sh = c.shell()
                print("[agent-ssh] interactive shell (按 Ctrl+C 退出)", file=sys.stderr)
                try:
                    import select
                    while True:
                        r, _, _ = select.select([sys.stdin, sh.channel], [], [], 0.3)
                        if sh.channel in r:
                            data = sh.recv(timeout=0.1)
                            if data:
                                sys.stdout.write(_strip_ansi_local(data.decode("utf-8", errors="replace")))
                                sys.stdout.flush()
                        if sys.stdin in r:
                            line = sys.stdin.readline()
                            if not line:
                                break
                            # Shell 模式下也记录每条命令到学习日志
                            line_stripped = line.strip()
                            if line_stripped and line_stripped not in ("exit", "logout"):
                                _log_executed_cmd(line_stripped, user, host, sid)
                            sh.send(line)
                            if line_stripped in ("exit", "logout"):
                                break
                except KeyboardInterrupt:
                    pass
                finally:
                    sh.close()
                return

            # ── 单条命令 ──
            if args.cmd:
                if args.show_commands:
                    _print_cmd_header(args.cmd, user, host)
                r = c.run(args.cmd, timeout=args.timeout)
                _log_executed_cmd(args.cmd, user, host, sid)
                sys.stdout.write(r.stdout_text)
                sys.stderr.write(r.stderr_text)
                sys.exit(r.exit_code if r.exit_code != 0 else 0)

            # ── 批量命令 ──
            if args.batch:
                if args.batch == "-":
                    cmds = [l.strip() for l in sys.stdin if l.strip() and not l.startswith("#")]
                else:
                    cmds = [l.strip() for l in Path(args.batch).read_text(encoding="utf-8").splitlines()
                            if l.strip() and not l.startswith("#")]
                print(f"[agent-ssh] batch: {len(cmds)} cmds", file=sys.stderr)
                if args.show_commands:
                    print(f"[agent-ssh] 命令列表:", file=sys.stderr)
                    for i, cmd in enumerate(cmds, 1):
                        _print_cmd(cmd, i)
                results = c.run_many(cmds, timeout=args.timeout, stop_on_error=args.stop_on_error)
                # 批量命令逐条写入学习日志
                for cmd in cmds:
                    _log_executed_cmd(cmd, user, host, sid)
                # 批量命令逐条输出，stderr 加序号前缀方便追溯
                for i, r in enumerate(results, 1):
                    if r.stdout:
                        sys.stdout.write(r.stdout_text)
                    if r.stderr:
                        for line in r.stderr_text.splitlines():
                            sys.stderr.write(f"[stderr:{i}] {line}\n")
                any_err = any(r.exit_code != 0 for r in results)
                sys.exit(1 if any_err else 0)

            print("需要一条命令,或 --batch,或 --shell", file=sys.stderr)
            sys.exit(2)
    except Exception as e:
        print(f"[agent-ssh] FATAL: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # 清除环境变量中的密码(除非用户明确要求保留)
        if not args.no_env_cleanup:
            try:
                os.environ.pop("AGENT_SSH_PASSWORD", None)
            except Exception:
                pass


def _strip_ansi_local(s: str) -> str:
    import re
    return re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', s)


if __name__ == "__main__":
    main()
