"""
JSONL 事件记录器
- 每个事件一行 JSON,实时刷盘
- 事件格式:
    {"ts": "ISO8601 with ms", "session_id": "...", "event": "exec|...", ...fields}
"""
import json
import time
from datetime import datetime
from pathlib import Path


class SessionRecorder:
    def __init__(self, log_path: Path, session_id: str):
        self.log_path = Path(log_path)
        self.session_id = session_id
        # 父目录已经由 storage.session_dir() 建好
        self._fh = open(self.log_path, "a", encoding="utf-8", buffering=1)
        self.start_ts = time.time()
        self.event_count = 0

    def emit(self, event: str, **fields) -> None:
        record = {
            "ts": datetime.now().isoformat(timespec="milliseconds"),
            "session_id": self.session_id,
            "event": event,
            **fields,
        }
        line = json.dumps(record, ensure_ascii=False)
        self._fh.write(line + "\n")
        self.event_count += 1

    def close(self) -> None:
        if self._fh is not None:
            try:
                self._fh.close()
            except Exception:
                pass
            self._fh = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
