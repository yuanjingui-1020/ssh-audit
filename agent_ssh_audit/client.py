"""
SSHAuditClient —— wrap paramiko,所有操作自动写 JSONL 审计日志
"""
import os
import sys
import time
import base64
import select
import socket
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Union, Callable

import paramiko

from . import storage
from .recorder import SessionRecorder
from .rules import check_command, split_compound


class SSHAuditClient:
    """
    用法:
        with SSHAuditClient(host, user, password) as c:
            r = c.run("ls -la /etc")
            print(r.stdout_text)

        # 批量
        with SSHAuditClient(host, user, password) as c:
            for cmd in ["whoami", "uname -a", "uptime"]:
                c.run(cmd)

        # 交互式 shell
        with SSHAuditClient(host, user, password) as c:
            sh = c.shell()
            sh.send("ls -la\\n")
            sh.recv(timeout=1.0)
            sh.close()
    """

    def __init__(
        self,
        host: str,
        user: str,
        password: Optional[str] = None,
        port: int = 22,
        key_filename: Optional[str] = None,
        timeout: float = 30.0,  # 改进: 默认 30s(覆盖慢网络场景)
        session_id: Optional[str] = None,
        extra_audit_meta: Optional[dict] = None,
    ):
        self.host = host
        self.user = user
        self.port = port
        self.password = password
        self.key_filename = key_filename
        self.timeout = timeout

        if session_id is None:
            session_id = storage.new_session_id(host=host, user=user)

        self.session_id = session_id
        self.log_path = storage.session_log_path(session_id)

        self.recorder = SessionRecorder(self.log_path, session_id)
        self._client: Optional[paramiko.SSHClient] = None
        self._shell_channel = None

        self.audit_meta = extra_audit_meta or {}

        auth_method = (
            "publickey" if key_filename else
            "password" if password else
            "none"
        )
        self.recorder.emit(
            "session_start",
            host=host, port=port, user=user,
            auth_method=auth_method,
            meta=self.audit_meta,
            pid=os.getpid(),
            argv=sys.argv[:5],
        )
        storage.append_index({
            "ts": datetime.now().isoformat(timespec="milliseconds"),
            "session_id": session_id,
            "host": host, "port": port, "user": user,
            "auth_method": auth_method,
            "log_path": str(self.log_path),
            "status": "open",
            "pid": os.getpid(),
        })

    # ---------------- 底层连接 ----------------

    def _connect(self):
        if self._client is not None:
            return
        self._client = paramiko.SSHClient()
        # 注意:AutoAddPolicy 仅用于测试环境,生产建议用 RejectPolicy
        # 或预先 load_host_keys()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        kwargs = dict(
            hostname=self.host,
            port=self.port,
            username=self.user,
            timeout=self.timeout,
            allow_agent=False,
            look_for_keys=False,
        )
        if self.key_filename:
            kwargs["key_filename"] = self.key_filename
        elif self.password is not None:
            kwargs["password"] = self.password
        else:
            raise ValueError("必须提供 password 或 key_filename")
        try:
            self._client.connect(**kwargs)
        except (paramiko.AuthenticationException,
                paramiko.SSHException,
                socket.error) as e:
            self.recorder.emit("connect_error", error=str(e), error_type=type(e).__name__)
            raise

    # ---------------- exec 通道 ----------------

    def run(self, cmd: str, timeout: float = 60.0) -> "ExecResult":
        """
        跑一条命令,完整记录
        - exec 事件:开始(拆分复合命令逐段审计)
        - audit_hit 事件(如有命中)
        - exec_output 事件:stdout/stderr 分块
        - exec_done 事件:退出码 + 耗时 + 字节数
        """
        self._connect()
        ts = time.time()
        self.recorder.emit("exec", cmd=cmd, timeout=timeout)

        # 使用新版 check_command(已内置 split_compound)
        for rule, level, matched in check_command(cmd):
            self.recorder.emit(
                "audit_hit",
                level=level, rule=rule,
                matched=matched, cmd=cmd,
            )

        try:
            _stdin, stdout, stderr = self._client.exec_command(cmd, timeout=timeout)
            chan = stdout.channel
        except Exception as e:
            self.recorder.emit("exec_error", cmd=cmd, error=str(e), error_type=type(e).__name__)
            raise

        out_buf = bytearray()
        err_buf = bytearray()
        CHUNK = 4096
        deadline = time.time() + timeout

        try:
            idle_polls = 0
            while True:
                if chan.recv_ready():
                    chunk = chan.recv(CHUNK)
                    if chunk:
                        out_buf.extend(chunk)
                        idle_polls = 0
                        self.recorder.emit(
                            "exec_output", stream="stdout",
                            data=base64.b64encode(chunk).decode("ascii"),
                            size=len(chunk),
                        )
                if chan.recv_stderr_ready():
                    chunk = chan.recv_stderr(CHUNK)
                    if chunk:
                        err_buf.extend(chunk)
                        idle_polls = 0
                        self.recorder.emit(
                            "exec_output", stream="stderr",
                            data=base64.b64encode(chunk).decode("ascii"),
                            size=len(chunk),
                        )
                if chan.exit_status_ready():
                    # 等输出全部排干再 break
                    if not chan.recv_ready() and not chan.recv_stderr_ready():
                        break
                if time.time() > deadline:
                    self.recorder.emit("exec_timeout", cmd=cmd, timeout=timeout)
                    chan.close()
                    break
                # 渐进睡眠: 空闲越久睡越久(20ms→100ms)
                if idle_polls > 10:
                    time.sleep(0.1)
                else:
                    time.sleep(0.02)
                idle_polls += 1
            exit_code = chan.recv_exit_status()
        except Exception as e:
            self.recorder.emit("exec_error", cmd=cmd, error=str(e), error_type=type(e).__name__)
            raise

        duration_ms = int((time.time() - ts) * 1000)
        result = ExecResult(
            exit_code=exit_code,
            stdout=bytes(out_buf),
            stderr=bytes(err_buf),
            duration_ms=duration_ms,
        )
        self.recorder.emit(
            "exec_done",
            cmd=cmd,
            exit_code=exit_code,
            duration_ms=duration_ms,
            bytes_stdout=len(out_buf),
            bytes_stderr=len(err_buf),
        )
        return result

    def run_many(self, cmds: List[str], timeout: float = 60.0,
                 stop_on_error: bool = False) -> List["ExecResult"]:
        """批量跑(同一连接,串行)"""
        results = []
        for cmd in cmds:
            r = self.run(cmd, timeout=timeout)
            results.append(r)
            if stop_on_error and r.exit_code != 0:
                self.recorder.emit("batch_aborted", last_cmd=cmd, exit_code=r.exit_code)
                break
        return results

    # ---------------- shell 通道 ----------------

    def shell(self, term: str = "xterm", width: int = 200, height: int = 60) -> "ShellSession":
        """开交互式 shell"""
        self._connect()
        self._shell_channel = self._client.invoke_shell(term=term, width=width, height=height)
        self.recorder.emit(
            "shell_open", term=term, width=width, height=height,
        )
        return ShellSession(self, self._shell_channel)

    # ---------------- 关闭 ----------------

    def close(self):
        if self._shell_channel is not None:
            try:
                self._shell_channel.close()
            except Exception:
                pass
            self._shell_channel = None
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
        if self.recorder is not None:
            duration = int((time.time() - self.recorder.start_ts) * 1000)
            self.recorder.emit(
                "session_end",
                total_duration_ms=duration,
                event_count=self.recorder.event_count,
            )
            storage.append_index({
                "ts": datetime.now().isoformat(timespec="milliseconds"),
                "session_id": self.session_id,
                "host": self.host, "port": self.port, "user": self.user,
                "log_path": str(self.log_path),
                "status": "closed",
                "total_duration_ms": duration,
                "event_count": self.recorder.event_count,
            })
            self.recorder.close()
            self.recorder = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class ExecResult:
    def __init__(self, exit_code: int, stdout: bytes, stderr: bytes, duration_ms: int):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration_ms = duration_ms

    @property
    def stdout_text(self) -> str:
        return self.stdout.decode("utf-8", errors="replace")

    @property
    def stderr_text(self) -> str:
        return self.stderr.decode("utf-8", errors="replace")

    def __repr__(self):
        return (f"ExecResult(exit={self.exit_code}, "
                f"stdout={len(self.stdout)}B, stderr={len(self.stderr)}B, "
                f"dur={self.duration_ms}ms)")


class ShellSession:
    """
    交互式 shell 句柄
    - send(data): 客户端 → 服务器(命令)
    - recv(timeout): 服务器 → 客户端(输出),非阻塞读 + gap 检测
    """

    # gap 检测参数: 读到第一个 chunk 后再等 N 轮空闲才返回(防截断)
    _RECV_GAP_ROUNDS = 3
    _RECV_GAP_INTERVAL = 0.05

    def __init__(self, client: SSHAuditClient, channel):
        self.client = client
        self.channel = channel

    def send(self, data: Union[str, bytes]):
        if isinstance(data, str):
            data = data.encode("utf-8")
        self.channel.sendall(data)
        # 审计(检查命令)
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            text = ""
        # 提取"行级"命令做审计(使用新版 split_compound)
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("\x1b"):
                continue
            for rule, level, matched in check_command(line):
                self.client.recorder.emit(
                    "audit_hit", level=level, rule=rule,
                    matched=matched, cmd=line, source="shell",
                )
        self.client.recorder.emit(
            "shell_io", direction="c2s",
            data=base64.b64encode(data).decode("ascii"),
            size=len(data),
        )

    def recv(self, n: int = 4096, timeout: float = 0.3) -> bytes:
        """
        非阻塞读 + gap 间隙检测:
        - 读到第一个 chunk 后继续等 _RECV_GAP_ROUNDS 轮
        - 如果中间又有新数据,重置 gap 计数器
        - 避免输出被截断(旧版边读边 break 的问题)
        """
        data = b""
        deadline = time.time() + timeout
        gap_count = 0

        while time.time() < deadline:
            if self.channel.recv_ready():
                chunk = self.channel.recv(n)
                if chunk:
                    data += chunk
                    gap_count = 0  # 读到数据,重置 gap
                    self.client.recorder.emit(
                        "shell_io", direction="s2c",
                        data=base64.b64encode(chunk).decode("ascii"),
                        size=len(chunk),
                    )
                    continue
            if data:
                # 有数据但当前无可读 → 增加 gap 计数
                gap_count += 1
                if gap_count >= self._RECV_GAP_ROUNDS:
                    break
            time.sleep(self._RECV_GAP_INTERVAL)
        return data

    def recv_stderr(self, n: int = 4096, timeout: float = 0.3) -> bytes:
        data = b""
        deadline = time.time() + timeout
        gap_count = 0

        while time.time() < deadline:
            if self.channel.recv_stderr_ready():
                chunk = self.channel.recv_stderr(n)
                if chunk:
                    data += chunk
                    gap_count = 0
                    self.client.recorder.emit(
                        "shell_io", direction="s2c-err",
                        data=base64.b64encode(chunk).decode("ascii"),
                        size=len(chunk),
                    )
                    continue
            if data:
                gap_count += 1
                if gap_count >= self._RECV_GAP_ROUNDS:
                    break
            time.sleep(self._RECV_GAP_INTERVAL)
        return data

    def close(self):
        try:
            self.channel.close()
        except Exception:
            pass
        self.client.recorder.emit("shell_close")
