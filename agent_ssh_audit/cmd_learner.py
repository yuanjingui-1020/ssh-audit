"""
cmd_learner 鈥?SSH 鍛戒护瀛︿範鏃ュ織锛堢函 Markdown,鎸夊ぉ褰掓。锛?
涓庡璁℃棩蹇楀畬鍏ㄧ嫭绔嬶細
- 鍙繚瀛樻墽琛岀殑鍛戒护琛岋紝涓嶅惈瀹¤瑙勫垯銆佸惈鍑虹粨鏋滅瓑楂橀樁鏁版嵁
- 姣忓ぉ涓€涓?Markdown 鏂囦欢锛屾柟渚跨炕闃呫€佹悳绱€佸涔?- 绾拷鍔犲啓鍏ワ紝涓嶇牬鍧忓凡鏈夊唴瀹?
璺緞锛?AGENT_SSH_AUDIT_HOME/cmds_learn/YYYY-MM-DD.md
"""
import os
from datetime import datetime
from pathlib import Path

from . import storage


def _learn_dir() -> Path:
    """瀛︿範鏃ュ織鏍圭洰褰曪細$AGENT_SSH_AUDIT_HOME/cmds_learn/"""
    p = storage.get_home() / "cmds_learn"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _daily_path(dt: datetime = None) -> Path:
    """褰撳ぉ瀛︿範鏃ュ織鏂囦欢璺緞"""
    d = (dt or datetime.now()).strftime("%Y-%m-%d")
    return _learn_dir() / f"{d}.md"


def log_command(cmd: str, user: str = "", host: str = "",
                session_id: str = "", note: str = "") -> None:
    """
    杩藉姞璁板綍涓€鏉℃墽琛岃繃鐨勫懡浠よ鍒板綋澶╃殑瀛︿範鏃ュ織銆?
    鍙傛暟:
        cmd:        鎵ц鐨勫懡浠ゅ叏鏂?        user:       鐧诲綍鐢ㄦ埛锛堝彲閫夛級
        host:       鐩爣涓绘満锛堝彲閫夛級
        session_id: 瀹¤ session ID锛堝彲閫夛紝鏂逛究鍏宠仈鍥炴斁锛?        note:       澶囨敞璇存槑锛堝彲閫夛紝AI 鍙啓鍏ョ畝鐭В閲婏級

    鍐欏叆鏍煎紡锛圡arkdown锛?
        ### HH:MM:SS | user@host
        ```bash
        cmd 鍏ㄦ枃
        ```

    鏂囦欢涓嶅瓨鍦ㄦ椂鑷姩鍒涘缓鏂囦欢澶村拰褰撴棩鏍囬銆?    """
    now = datetime.now()
    path = _daily_path(now)
    ts = now.strftime("%H:%M:%S")

    # 鏋勫缓褰掑睘鏍囩
    parts = [ts]
    label_parts = []
    if user:
        label_parts.append(user)
    if host:
        label_parts.append(host)
    if label_parts:
        parts.append("@".join(label_parts))
    if session_id:
        parts.append(f"sid:{session_id}")
    heading = " | ".join(parts)

    # 鏂囦欢澶达紙浠呴娆″啓鍏ユ椂锛?    header = "# SSH 鍛戒护瀛︿範鏃ュ織\n\n"
    day_title = f"## {now.strftime('%Y-%m-%d')}\n\n"

    # 妫€鏌ユ枃浠舵槸鍚﹀瓨鍦ㄤ互鍐冲畾鏄惁鍐欏叆鏂囦欢澶?    if not path.exists():
        with path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(header)
            f.write(day_title)
    else:
        # 妫€鏌ュ綋澶╂爣棰樻槸鍚﹀瓨鍦?        content = path.read_text(encoding="utf-8")
        if day_title.strip() not in content:
            with path.open("a", encoding="utf-8", newline="\n") as f:
                f.write(day_title)

    # 杩藉姞鍏ュ彛
    entry = f"### {heading}\n"
    if note:
        entry += f"> {note}\n\n"
    entry += "```bash\n"
    entry += cmd.rstrip("\n") + "\n"
    entry += "```\n\n"

    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(entry)


def list_daily_files(limit: int = 30) -> list:
    """鍒楀嚭鏈€杩戠殑瀛︿範鏃ュ織鏂囦欢"""
    d = _learn_dir()
    if not d.exists():
        return []
    files = sorted(d.glob("*.md"), reverse=True)
    return [{
        "date": f.stem,
        "path": str(f),
        "size": f.stat().st_size,
    } for f in files[:limit]]


if __name__ == "__main__":
    # 绠€鍗曡嚜娴?    log_command("df -h", user="root", host="192.168.1.1",
                session_id="test_001", note="妫€鏌ョ鐩樹娇鐢ㄧ巼")
    log_command("uname -a", user="root", host="192.168.1.1",
                session_id="test_001")
    log_command("systemctl status nginx", user="appen", host="192.168.1.100",
                note="妫€鏌?Nginx 杩愯鐘舵€?)
    print(f"宸插啓鍏? {_daily_path()}")
    print("鍐呭棰勮:")
    print(_daily_path().read_text(encoding="utf-8"))
