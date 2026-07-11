"""

回放器:从 JSONL 还原 session 的完整剧本

"""

import json

import base64

import re

from pathlib import Path

from typing import Iterator, Dict, Any, Optional





ANSI = re.compile(r'\x1b\[[0-9;?]*[a-zA-Z]')

ANSI_OSC = re.compile(r'\x1b\][^\x07\x1b]*\x07')





def load_session(jsonl_path: Path) -> Iterator[Dict[str, Any]]:

    with open(jsonl_path, "r", encoding="utf-8") as f:

        for line in f:

            line = line.strip()

            if not line:

                continue

            yield json.loads(line)





def _strip_ansi(s: str) -> str:

    s = ANSI_OSC.sub("", s)

    s = ANSI.sub("", s)

    return s





def replay_text(jsonl_path: Path, ansi_strip: bool = True, show_timestamps: bool = True) -> str:

    """

    把 JSONL 渲染成"人看的剧本":

    - 命令块

    - 输出块

    - 审计告警

    - 会话起止

    """

    lines = []

    lines.append(f"# Session 回放 — `{jsonl_path.name}`\n")



    cur_cmd = None



    def ts_prefix(ts: str) -> str:

        if show_timestamps and ts:

            return f"`{ts[11:23]}` "

        return ""



    for ev in load_session(jsonl_path):

        e = ev.get("event")

        ts = ev.get("ts", "")



        if e == "session_start":

            lines.append(f"## 🔌 Session 开始  {ts}")

            lines.append(f"- 目标: `{ev.get('user')}@{ev.get('host')}:{ev.get('port')}`")

            lines.append(f"- 认证: `{ev.get('auth_method')}`")

            meta = ev.get("meta") or {}

            if meta:

                lines.append(f"- 元信息: `{json.dumps(meta, ensure_ascii=False)}`")

            lines.append(f"- PID: `{ev.get('pid')}`, argv: `{ev.get('argv')}`")

            lines.append("")

        elif e == "session_end":

            lines.append(f"\n## 🔚 Session 结束  {ts}")

            lines.append(f"- 总耗时: **{ev.get('total_duration_ms')} ms**")

            lines.append(f"- 事件数: **{ev.get('event_count')}**")

        elif e == "connect_error":

            lines.append(f"\n## ❌ 连接失败  {ts}")

            lines.append(f"- `{ev.get('error_type')}`: {ev.get('error')}")

        elif e == "exec":

            cur_cmd = ev.get("cmd", "")

            lines.append(f"\n### ⚡ {ts_prefix(ts)}CMD  `{cur_cmd}`")

            lines.append("```bash")

            lines.append(f"$ {cur_cmd}")

            lines.append("```")

        elif e == "exec_output":

            chunk = base64.b64decode(ev.get("data", ""))

            text = chunk.decode("utf-8", errors="replace")

            if ansi_strip:

                text = _strip_ansi(text)

            tag = ev.get("stream", "stdout").upper()

            lines.append(f"```{tag}")

            lines.append(text.rstrip("\n"))

            lines.append("```")

        elif e == "exec_done":

            lines.append(

                f"<sub>↳ exit=`{ev.get('exit_code')}` "

                f"dur=`{ev.get('duration_ms')}ms` "

                f"stdout=`{ev.get('bytes_stdout')}B` "

                f"stderr=`{ev.get('bytes_stderr')}B`</sub>"

            )

        elif e == "exec_error":

            lines.append(f"- ❌ 错误: `{ev.get('error_type')}` — {ev.get('error')}")

        elif e == "exec_timeout":

            lines.append(f"- ⏱️ 超时 ({ev.get('timeout')}s)")

        elif e == "audit_hit":

            icon = "🔴" if ev.get("level") == "critical" else "🟡"

            lines.append(

                f"> {icon} **{ev.get('level').upper()}** 规则 `{ev.get('rule')}` "

                f"命中 `{ev.get('matched')}` "

                f"(命令: `{ev.get('cmd')}`)"

            )

        elif e == "shell_open":

            lines.append(f"\n### 🖥️ {ts_prefix(ts)}交互 shell 开启")

            lines.append(f"- term=`{ev.get('term')}` size=`{ev.get('width')}x{ev.get('height')}`")

        elif e == "shell_io":

            direction = ev.get("direction", "")

            chunk = base64.b64decode(ev.get("data", ""))

            text = chunk.decode("utf-8", errors="replace")

            if ansi_strip:

                text = _strip_ansi(text)

            if direction == "c2s":

                lines.append(f"\n**{ts_prefix(ts)}📤 CMD**:\n```\n{text}\n```")

            else:

                lines.append(f"\n**{ts_prefix(ts)}📥 OUT**:\n```\n{text}\n```")

        elif e == "shell_close":

            lines.append(f"\n_{ts_prefix(ts)}shell 关闭_")



    return "\n".join(lines) + "\n"





def replay_json(jsonl_path: Path, decode_b64: bool = True) -> str:

    """pretty print 整个 JSONL 事件流;可选把 base64 data 字段解码成可读文本"""

    out = []

    for ev in load_session(jsonl_path):

        if decode_b64 and isinstance(ev.get("data"), str):

            try:

                raw = base64.b64decode(ev["data"])

                try:

                    text = raw.decode("utf-8")

                    printable_ratio = sum(

                        1 for c in text

                        if c.isprintable() or c in "\n\r\t"

                    ) / max(len(text), 1)

                    if printable_ratio > 0.7:

                        ev["data_text"] = text

                except UnicodeDecodeError:

                    pass

            except Exception:

                pass

        out.append(json.dumps(ev, ensure_ascii=False, indent=2))

    return "\n".join(out)





def replay_text_stream(jsonl_path: Path, ansi_strip: bool = True, show_timestamps: bool = True) -> Iterator[str]:
    """
    流式版本:逐行 yield,避免大 session 占用过多内存。
    用法:
        for line in replay_text_stream(path):
            print(line)
    """
    cur_cmd = None

    def ts_prefix(ts: str) -> str:
        if show_timestamps and ts:
            return f"`{ts[11:23]}` "
        return ""

    yield f"# Session 回放 — `{jsonl_path.name}`\n"

    for ev in load_session(jsonl_path):
        e = ev.get("event")
        ts = ev.get("ts", "")

        if e == "session_start":
            yield f"## \U0001F50C Session 开始  {ts}\n"
            yield f"- 目标: `{ev.get('user')}@{ev.get('host')}:{ev.get('port')}`\n"
            yield f"- 认证: `{ev.get('auth_method')}`\n"
            meta = ev.get("meta") or {}
            if meta:
                yield f"- 元信息: `{json.dumps(meta, ensure_ascii=False)}`\n"
            yield f"- PID: `{ev.get('pid')}`, argv: `{ev.get('argv')}`\n\n"
        elif e == "session_end":
            yield f"\n## \U0001F51A Session 结束  {ts}\n"
            yield f"- 总耗时: **{ev.get('total_duration_ms')} ms**\n"
            yield f"- 事件数: **{ev.get('event_count')}**\n"
        elif e == "connect_error":
            yield f"\n## \u274C 连接失败  {ts}\n"
            yield f"- `{ev.get('error_type')}`: {ev.get('error')}\n"
        elif e == "exec":
            cur_cmd = ev.get("cmd", "")
            yield f"\n### \u26A1 {ts_prefix(ts)}CMD  `{cur_cmd}`\n"
            yield f"```bash\n$ {cur_cmd}\n```\n"
        elif e == "exec_output":
            chunk = base64.b64decode(ev.get("data", ""))
            text = chunk.decode("utf-8", errors="replace")
            if ansi_strip:
                text = _strip_ansi(text)
            tag = ev.get("stream", "stdout").upper()
            yield f"```{tag}\n{text.rstrip(chr(10))}\n```\n"
        elif e == "exec_done":
            yield (
                f"<sub>\u21B3 exit=`{ev.get('exit_code')}` "
                f"dur=`{ev.get('duration_ms')}ms` "
                f"stdout=`{ev.get('bytes_stdout')}B` "
                f"stderr=`{ev.get('bytes_stderr')}B`</sub>\n"
            )
        elif e == "exec_error":
            yield f"- \u274C 错误: `{ev.get('error_type')}` — {ev.get('error')}\n"
        elif e == "exec_timeout":
            yield f"- \u23F1\uFE0F 超时 ({ev.get('timeout')}s)\n"
        elif e == "audit_hit":
            icon = "\U0001F534" if ev.get("level") == "critical" else "\U0001F7E1"
            yield (
                f"> {icon} **{ev.get('level').upper()}** 规则 `{ev.get('rule')}` "
                f"命中 `{ev.get('matched')}` "
                f"(命令: `{ev.get('cmd')}`)\n"
            )
        elif e == "shell_open":
            yield f"\n### \U0001F5A5\uFE0F {ts_prefix(ts)}交互 shell 开启\n"
            yield f"- term=`{ev.get('term')}` size=`{ev.get('width')}x{ev.get('height')}`\n"
        elif e == "shell_io":
            direction = ev.get("direction", "")
            chunk = base64.b64decode(ev.get("data", ""))
            text = chunk.decode("utf-8", errors="replace")
            if ansi_strip:
                text = _strip_ansi(text)
            if direction == "c2s":
                yield f"\n**{ts_prefix(ts)}\U0001F4E4 CMD**:\n```\n{text}\n```\n"
            else:
                yield f"\n**{ts_prefix(ts)}\U0001F4E5 OUT**:\n```\n{text}\n```\n"
        elif e == "shell_close":
            yield f"\n_{ts_prefix(ts)}shell 关闭_\n"


def replay_raw_stream(jsonl_path: Path) -> str:

    """

    仅还原 c2s + s2c 的字节流(像录像机)

    适合回放交互式 shell 会话

    """

    lines = []

    for ev in load_session(jsonl_path):

        e = ev.get("event")

        if e != "shell_io":

            continue

        direction = ev.get("direction", "")

        chunk = base64.b64decode(ev.get("data", ""))

        text = chunk.decode("utf-8", errors="replace")

        text = _strip_ansi(text)

        prefix = "[CMD] " if direction == "c2s" else "[OUT] "

        lines.append(prefix + text.replace("\r", ""))

    return "".join(lines)

