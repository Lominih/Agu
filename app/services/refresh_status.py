from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
from typing import Any

from app.core.config import REFRESH_STATUS_PATH


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_refresh_status() -> dict[str, Any]:
    return {
        "state": "idle",
        "pool": "hs300",
        "pid": None,
        "started_at": None,
        "updated_at": None,
        "finished_at": None,
        "message": "尚未启动真实数据刷新任务",
        "rows": None,
        "symbols": None,
        "metrics": None,
        "error": None,
        "log_path": None,
    }


def read_refresh_status(status_path: Path = REFRESH_STATUS_PATH) -> dict[str, Any]:
    if not status_path.exists():
        return default_refresh_status()

    with status_path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    status = default_refresh_status()
    status.update(payload)
    return status


def write_refresh_status(payload: dict[str, Any], status_path: Path = REFRESH_STATUS_PATH) -> dict[str, Any]:
    status_path.parent.mkdir(parents=True, exist_ok=True)
    enriched = default_refresh_status()
    enriched.update(payload)
    enriched["updated_at"] = utc_now_iso()

    with status_path.open("w", encoding="utf-8") as fh:
        json.dump(enriched, fh, ensure_ascii=False, indent=2)

    return enriched


def is_pid_running(pid: int | None) -> bool:
    if not pid:
        return False

    if os.name == "nt":
        check = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=False,
        )
        output = check.stdout.strip()
        return bool(output) and "No tasks are running" not in output

    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def get_runtime_refresh_status(status_path: Path = REFRESH_STATUS_PATH) -> dict[str, Any]:
    status = read_refresh_status(status_path)

    if status["state"] == "running" and not is_pid_running(status.get("pid")):
        status = write_refresh_status(
            {
                **status,
                "state": "failed",
                "finished_at": utc_now_iso(),
                "message": "后台刷新进程已结束，但未写入成功状态",
                "error": status.get("error") or "后台进程异常退出",
            },
            status_path=status_path,
        )

    return status
