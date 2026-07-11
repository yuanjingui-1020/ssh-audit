#!/usr/bin/env python3

"""

agent-ssh-shell 鈥斺€?鍍?ssh 涓€鏍风殑浜や簰寮?shell,鑷姩璁板綍 + 瀹¤ + 鍥炴斁



鐢ㄦ硶:

    python agent-ssh-shell.py appen@192.168.1.100 --password appen

    python agent-ssh-shell.py appen@192.168.1.100 --key ~/.ssh/id_ed25519

    echo pwd | python agent-ssh-shell.py appen@192.168.1.100 --password appen --batch



璺?ssh 琛屼负瀵归綈:

- 杩?shell 鍚庨殢渚挎暡鍛戒护

- exit / logout / quit 閫€

- Ctrl+C 涓柇褰撳墠鍛戒护(涓嶉€€鍑?session)

- 绗簩娆?Ctrl+C 鏂紑

"""

import sys

import os

import re

import time

import json

import argparse

import getpass

from pathlib import Path



HERE = Path(__file__).resolve().parent

sys.path.insert(0, str(HERE.parent))



from agent_ssh_audit import SSHAuditClient, storage, cmd_learner





ANSI_CSI = re.compile(r'\x1b\[[0-9;?]*[a-zA-Z]')

ANSI_OSC = re.compile(r'\x1b\][^\x07\x1b]*\x07')





def strip_ansi(s: str) -> str:

    s = ANSI_OSC.sub("", s)

    s = ANSI_CSI.sub("", s)

    return s





def parse_target(target: str, default_port: int = 22):

    if "@" not in target:

        raise ValueError("target 蹇呴』鏄?user@host[:port]")

    user, host_port = target.split("@", 1)

    if ":" in host_port:

        host, port_s = host_port.split(":", 1)

        port = int(port_s) or default_port

    else:

        host, port = host_port, default_port

    return user, host, port





def drain_output(sh, max_wait: float = 0.4) -> str:

    """鐭疆璇㈣鎵€鏈夊彲鐢ㄨ緭鍑?鍚堟垚涓€娈靛瓧绗︿覆杩斿洖"""

    buf = ""

    deadline = time.time() + max_wait

    while time.time() < deadline:

        chunk = sh.recv(timeout=0.15)

        if chunk:

            buf += strip_ansi(chunk.decode("utf-8", errors="replace"))

        else:

            if buf:

                break  # 宸叉湁杈撳嚭涓旀棤鏂板唴瀹?鍋滄

    return buf





def drain_stderr(sh, max_wait: float = 0.2) -> str:

    buf = ""

    deadline = time.time() + max_wait

    while time.time() < deadline:

        chunk = sh.recv_stderr(timeout=0.15)

        if chunk:

            buf += strip_ansi(chunk.decode("utf-8", errors="replace"))

        else:

            if buf:

                break

    return buf





def extract_prompt(text: str) -> str:

    """浠庤緭鍑烘湯灏炬彁鍙?prompt(浠?$ 鎴?# 缁撳熬鐨勬渶鍚庝竴琛?"""

    text = text.rstrip()

    if not text:

        return ""

    last_line = text.split("\n")[-1].strip()

    if last_line.endswith("$") or last_line.endswith("#"):

        return last_line + " "

    return ""





# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
# 瀛︿範鏃ュ織杈呭姪鍑芥暟
# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€


def _log_shell_cmd(cmd: str, user: str, host: str, sid: str):
    """灏嗕氦浜?shell 涓彂閫佺殑鍛戒护鍐欏叆瀛︿範鏃ュ織"""
    try:
        cmd_learner.log_command(
            cmd=cmd, user=user, host=host,
            session_id=sid,
        )
    except Exception as e:
        print(f"[agent-ssh-shell] 瀛︿範鏃ュ織鍐欏叆澶辫触: {e}", file=sys.stderr)


def main():

    p = argparse.ArgumentParser(description="Agent SSH interactive shell (audit-enabled)")

    p.add_argument("target", help="user@host[:port]")

    p.add_argument("--password", help="瀵嗙爜(涔熷彲璧?stdin / env)")

    p.add_argument("--key", help="绉侀挜璺緞")

    p.add_argument("--port", type=int, default=22)

    p.add_argument("--meta", help="鍏冧俊鎭?JSON)")

    p.add_argument("--no-color", action="store_true", help="鍏抽棴 ANSI 棰滆壊(榛樿灏辨槸鍏崇殑)")

    p.add_argument("--prompt", help="鎵嬪姩鎸囧畾 prompt 瀛楃涓?榛樿浠庢湇鍔＄杈撳嚭鎻愬彇)")

    args = p.parse_args()



    user, host, port = parse_target(args.target, args.port)



    password = args.password or os.environ.get("AGENT_SSH_PASSWORD")

    if not args.key and not password:

        password = getpass.getpass("password: ")



    meta = json.loads(args.meta) if args.meta else {}



    sid = storage.new_session_id(host=host, user=user)



    print(f"\n[agent-ssh-shell] 宸茶繛鎺?{user}@{host}:{port}", file=sys.stderr)

    print(f"[agent-ssh-shell] session: {sid}", file=sys.stderr)

    print(f"[agent-ssh-shell] 鏃ュ織: {storage.session_log_path(sid)}", file=sys.stderr)

    print(f"[agent-ssh-shell] 杈撳叆鍛戒护,exit / logout / quit 閫€鍑?Ctrl+C 涓柇褰撳墠\n", file=sys.stderr)



    interrupted_once = False

    fixed_prompt = args.prompt  # 濡傛灉鎸囧畾浜嗗氨鍥哄畾鐢?涓嶅啀鎻愬彇(閬垮厤閲嶅)



    try:

        with SSHAuditClient(

            host=host, user=user, port=port,

            password=password, key_filename=args.key,

            extra_audit_meta=meta,

            session_id=sid,

        ) as c:

            sh = c.shell()

            time.sleep(0.3)



            # 鍚冩杩庤 / banner / 绗竴涓?prompt

            initial = drain_output(sh, max_wait=1.2)

            if initial:

                sys.stdout.write(initial)

                sys.stdout.flush()



            while True:

                # 鏈嶅姟绔凡缁忓彂杩囩殑 prompt 浼氬湪 stdout 涓婃樉绀?

                # 鎴戜滑涓嶄紶 prompt 缁?input() 鈥斺€?閬垮厤鍙岄噸 prompt

                try:

                    line = input()

                except EOFError:

                    print("\n[EOF]", file=sys.stderr)

                    break

                except KeyboardInterrupt:

                    if interrupted_once:

                        print("\n[鏂紑]", file=sys.stderr)

                        break

                    interrupted_once = True

                    # 鍙戦€?Ctrl+C (0x03) 缁欐湇鍔″櫒,涓柇褰撳墠鍛戒护

                    sh.send("\x03")

                    out = drain_output(sh, max_wait=0.6)

                    if out:

                        sys.stdout.write(out)

                        sys.stdout.flush()

                    continue



                interrupted_once = False



                if not line:

                    sh.send("\n")

                    time.sleep(0.1)

                    out = drain_output(sh, max_wait=0.3)

                    if out:

                        sys.stdout.write(out)

                        sys.stdout.flush()

                    continue



                # 璁板綍鍛戒护鍒板涔犳棩蹇楋紙鎺掗櫎绌鸿銆侀€€鍑哄懡浠わ級
                line_stripped = line.strip()
                if line_stripped and line_stripped not in ("exit", "logout", "quit"):
                    _log_shell_cmd(line_stripped, user, host, sid)

                sh.send(line + "\n")

                # 鐭疆璇㈣杈撳嚭 鈥斺€?绛夊埌娌℃柊鏁版嵁

                out = drain_output(sh, max_wait=0.5)

                err = drain_stderr(sh, max_wait=0.2)

                combined = out + err

                if combined:

                    sys.stdout.write(combined)

                    sys.stdout.flush()



                if line.strip() in ("exit", "logout", "quit"):

                    break



    except KeyboardInterrupt:

        print("\n[鏂紑]", file=sys.stderr)

    except Exception as e:

        print(f"\n[FATAL] {type(e).__name__}: {e}", file=sys.stderr)

        sys.exit(1)



    print(f"\n[agent-ssh-shell] session 缁撴潫: {sid}", file=sys.stderr)

    replay_py = (Path(__file__).parent / "agent-ssh-replay.py").resolve()

    print(f"[agent-ssh-shell] 鍥炴斁(缁濆璺緞):", file=sys.stderr)

    print(f"  python {replay_py} {sid}", file=sys.stderr)

    print(f"[agent-ssh-shell] 鍥炴斁(鍒囧埌椤圭洰鐩綍):", file=sys.stderr)

    print(f"  cd {Path(__file__).resolve().parent.parent}", file=sys.stderr)

    print(f"  python bin\\agent-ssh-replay.py {sid}", file=sys.stderr)

    print(f"[agent-ssh-shell] 鍒楁墍鏈?sessions:", file=sys.stderr)

    print(f"  python {replay_py} --list", file=sys.stderr)





if __name__ == "__main__":

    main()

