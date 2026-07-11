"""
test_shell.py -- 用 subprocess 验证 agent-ssh-shell.py 的非交互流程

模拟用户连续输入命令，捕获输出
"""
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BIN = HERE / "bin" / "agent-ssh-shell.py"

# 模拟用户敲的命令序列(每行一条)
USER_INPUT = """whoami
pwd
uname -a
ls -la /home
echo 'audit-this-line'
exit
"""

# 修改为你的服务器信息
PASSWORD = "your-password"
TARGET = "your-username@your-server-ip"


def main():
    print(f"启动 agent-ssh-shell.py: {TARGET}")
    print(f"模拟用户输入 ({len(USER_INPUT.splitlines())} 行命令):")
    for line in USER_INPUT.splitlines():
        print(f"  > {line}")
    print()

    start = time.time()
    proc = subprocess.Popen(
        [sys.executable, str(BIN), TARGET, "--password", PASSWORD],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    try:
        out, err = proc.communicate(input=USER_INPUT, timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()

    elapsed = time.time() - start
    print(f"=== 用时 {elapsed:.2f}s ===\n")

    print("--- 服务端输出(stdout) ---")
    print(out)
    print("--- 我们的日志(stderr) ---")
    print(err)

    # 从 stderr 找 session_id
    import re
    m = re.search(r"session:\s*(\S+)", err)
    if m:
        sid = m.group(1)
        print(f"\nsession_id: {sid}")
        # 验证 JSONL 写入了
        log_path = Path.home() / ".agent-ssh-audit" / "sessions" / time.strftime("%Y-%m-%d") / f"{sid}.jsonl"
        if log_path.exists():
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            print(f"日志: {log_path}")
            print(f"事件数: {len(lines)}")
            # 抽几条事件
            event_types = {}
            for line in lines:
                try:
                    import json
                    e = json.loads(line).get("event", "?")
                    event_types[e] = event_types.get(e, 0) + 1
                except Exception:
                    pass
            print("事件分布:")
            for k, v in sorted(event_types.items(), key=lambda x: -x[1]):
                print(f"  {k}: {v}")
        else:
            print(f"!! 日志不存在: {log_path}")


if __name__ == "__main__":
    main()
