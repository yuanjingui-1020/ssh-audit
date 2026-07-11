"""

agent-ssh-audit: 让 AI 跑 SSH 时全程有据可查



惰性导入：storage / rules / replay 直接可用（零依赖），

SSHAuditClient / ExecResult / ShellSession 按需加载（需 paramiko）。

"""

__version__ = "0.1.0"

__all__ = ["SSHAuditClient", "ExecResult", "ShellSession", "storage", "rules", "replay", "cmd_learner"]





def __getattr__(name):

    if name in ("SSHAuditClient", "ExecResult", "ShellSession"):

        from . import client as _client

        return getattr(_client, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

