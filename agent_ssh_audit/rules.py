"""
危险命令审计规则
- 每条规则:(name, level, pattern)
- level: "warn" | "critical"
- pattern: 正则
"""
import re
from typing import List, Tuple, Optional

# level: critical = 必须人工 review, warn = 注意

DEFAULT_RULES: List[Tuple[str, str, str]] = [
    # 删库级 —— rm -rf 后面跟根、家目录、或任何绝对路径
    ("rm_rf_root", "critical",
     r"\brm\s+-\w*r\w*\s+/(\s|$|;|\||&|'|\")"),
    ("rm_rf_home", "critical",
     r"\brm\s+-\w*r\w*\s+(~|\$HOME|\.\s*$)"),
    ("rm_rf_absolute", "warn",
     r"\brm\s+-\w*r\w*\s+/\S"),
    ("dd_destructive", "critical",
     r"\bdd\s+.*\bof=/dev/(sd|hd|nvme|vd|mmcblk|xvd)"),
    ("mkfs", "critical", r"\bmkfs(\.\w+)?\s+/dev/"),
    ("chmod_recursive_root", "critical",
     r"\bchmod\s+(-R\s+)?[0-7]{3,4}\s+/\s*($|;|\||&|'|\")"),
    ("chown_recursive_root", "critical",
     r"\bchown\s+(-R\s+)?\S+\s+/\s*($|;|\||&|'|\")"),

    # 远程脚本执行
    ("pipe_to_shell", "critical",
     r"(curl|wget)\s+[^|]*\|\s*(ba)?sh"),

    # 服务影响
    ("system_reboot", "warn",
     r"\b(reboot|shutdown|halt|poweroff|init\s+[06]|systemctl\s+(reboot|poweroff))\b"),
    ("disable_sshd", "critical",
     r"\b(systemctl\s+(stop|disable|mask)\s+ssh(\.service)?|service\s+ssh(d)?\s+stop)\b"),
    ("firewall_flush", "warn", r"\biptables\s+-F\b"),

    # 账号/凭据
    ("passwd_change", "warn", r"(^|\s|;)passwd\b"),
    ("user_mgmt", "warn",
     r"\b(useradd|userdel|usermod|groupadd|groupdel|groupmod)\b"),
    ("edit_passwd_files", "critical",
     r"(>|>>|tee\s+|sed\s+-i.*|(^|\s)(vim?|nano|emacs)\s+)/etc/(passwd|shadow|sudoers|ssh/sshd_config)\b"),

    # 清痕迹
    ("history_clear", "warn",
     r"(\bhistory\s+-c\b|>\s*~/\.bash_history|\brm\s+.*\.bash_history)"),
]


# 安全前缀白名单 —— 匹配上的命令段跳过审计检查
# 注意: 只对拆分后的单段生效,不会漏掉 "ls /tmp; rm -rf /"
SAFE_PREFIXES = (
    "ls ", "ll ", "cat ", "less ", "head ", "tail ", "grep ", "find ",
    "pwd", "echo ", "printf ", "uname ", "whoami", "id", "hostname",
    "date ", "uptime", "df ", "du ", "ps ", "top", "env", "printenv",
    "which ", "whereis ", "type ",
    "git status", "git log", "git diff", "git show", "git branch",
    "docker ps", "docker images", "docker logs", "docker inspect",
    "kubectl get", "kubectl describe", "kubectl logs",
    "systemctl status", "systemctl list",
)


def split_compound(cmd: str) -> List[str]:
    """
    将复合命令按分隔符拆分为独立命令段。

    支持的组合符: ;  &&  ||  |  \\n

    Examples:
        "ls /tmp; rm -rf /"  ->  ["ls /tmp", "rm -rf /"]
        "cat x && echo y"    ->  ["cat x", "echo y"]
        "df -h | grep sda"   ->  ["df -h | grep sda"]  (管道保留)
    """
    # 按 ;  &&  ||  \n 拆分(不含 |,管道是流水线命令不是复合命令)
    segments = re.split(r"\s*(;|&&|\|\|)\s*", cmd)
    parts = []
    buf = ""
    for i, s in enumerate(segments):
        if i % 2 == 0:
            buf = s.strip()
        else:
            if buf and buf not in (";", "&&", "||", "|"):
                parts.append(buf)
    if buf and buf not in (";", "&&", "||", "|"):
        parts.append(buf)
    # 再按换行拆分
    result = []
    for p in parts:
        for line in p.split("\n"):
            line = line.strip()
            if line:
                result.append(line)
    return result


def _is_safe_segment(segment: str) -> bool:
    """
    判断单段命令是否属于安全白名单。

    注意: 管道命令(含 | )会拆分管道各部分分别检查,
    只有所有部分都匹配白名单才返回 True。
    防止 "cat x | curl url | bash" 被 cat 前缀骗过。
    """
    # 管道命令: 必须所有部分都安全
    if "|" in segment:
        parts = segment.split("|")
        return all(_is_safe_segment(p.strip()) for p in parts)

    for safe in SAFE_PREFIXES:
        if segment.startswith(safe):
            return True
    return False


def check_command(cmd: str, rules: Optional[List[Tuple[str, str, str]]] = None) -> List[Tuple[str, str, str]]:
    """
    返回命中列表: [(rule_name, level, matched_text), ...]

    改进(v2):
    - 自动按 ;  &&  ||  |  \\n 拆分复合命令
    - 白名单对每段独立生效(不会漏掉 "ls /tmp; rm -rf /" 中的 rm)
    - 同规则只命中一次(避免重复报警)
    """
    rules = rules or DEFAULT_RULES
    cmd_stripped = cmd.strip()

    # 拆分复合命令
    segments = split_compound(cmd_stripped)
    if not segments:
        segments = [cmd_stripped]

    all_hits: List[Tuple[str, str, str]] = []
    seen_rules: set = set()

    for segment in segments:
        seg = segment.strip()
        if not seg:
            continue
        # 白名单: 仅安全段跳过检查
        if _is_safe_segment(seg):
            continue

        for name, level, pattern in rules:
            if name in seen_rules:
                continue  # 同规则已命中,避免重复
            m = re.search(pattern, seg)
            if m:
                all_hits.append((name, level, m.group(0)))
                seen_rules.add(name)

    return all_hits
