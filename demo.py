#!/usr/bin/env python3
"""
demo.py - 端到端跑通

跑 4 条命令(含 1 条审计会命中的) + 1 段交互式 shell
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from agent_ssh_audit import SSHAuditClient, storage


def main():
    # 修改为你的服务器信息
    HOST = "your-server-ip"
    USER = "your-username"
    PASSWORD = "your-password"
    PORT = 22

    print("=" * 70)
    print(f"agent-ssh-audit demo  目标: {USER}@{HOST}:{PORT}")
    print("=" * 70)

    sid = storage.new_session_id(host=HOST, user=USER)
    print(f"session_id: {sid}")
    print(f"日志: {storage.session_log_path(sid)}")
    print()

    with SSHAuditClient(
        host=HOST, user=USER, port=PORT, password=PASSWORD,
        extra_audit_meta={"agent": "demo.py", "purpose": "end-to-end smoke"},
        session_id=sid,
    ) as c:
        # ---- 1. 单条命令 ----
        print("[1] 单条命令")
        r = c.run("whoami && hostname && uname -a")
        print(f"    exit={r.exit_code}  stdout={r.stdout_text.strip()[:80]}")

        # ---- 2. 批量命令 ----
        print("\n[2] 批量命令(包含审计会命中的危险命令)")
        cmds = [
            "ls -la /home",                               # 安全
            "cat /etc/os-release | head -3",              # 安全
            "echo safe && date",                           # 安全
            # 命中 rm_rf_root
            "rm -rf /tmp/nonexistent_dir_for_audit_test",  # 不会真删东西,但会命中
            # 命中 chmod_recursive_root
            "chmod 777 /etc",                              # 服务器会拒绝,但审计会先命中
        ]
        results = c.run_many(cmds, stop_on_error=False)
        for cmd, r in zip(cmds, results):
            tag = "🔴" if r.exit_code != 0 else "  "
            print(f"    {tag} exit={r.exit_code:>3}  {cmd[:60]}")

        # ---- 3. 交互式 shell ----
        print("\n[3] 交互式 shell(3 条命令)")
        sh = c.shell()
        import time
        time.sleep(0.5)
        # 吃欢迎语
        sh.recv(timeout=0.5)

        for cmd in ["echo INTERACTIVE-1", "pwd", "exit"]:
            sh.send(cmd + "\n")
            time.sleep(0.5)
            out = sh.recv(timeout=0.6)
            print(f"    > {cmd}")
            print(f"      out: {out.decode('utf-8', errors='replace').strip()[:100]}")
        sh.close()

    print()
    print("=" * 70)
    print("全部跑完,审计日志:")
    print(f"  {storage.session_log_path(sid)}")
    print()
    print("查看回放:")
    print(f"  python bin/agent-ssh-replay.py {sid}")
    print(f"  python bin/agent-ssh-replay.py {sid} --json")
    print(f"  python bin/agent-ssh-replay.py {sid} --stream")


if __name__ == "__main__":
    main()
