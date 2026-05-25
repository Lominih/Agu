from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_json_file(path: Path, default_factory: Callable[[], Any] | None = None) -> Any:
    if not path.exists():
        return default_factory() if default_factory else None

    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return default_factory() if default_factory else None


def write_json_file(path: Path, payload: Any) -> Any:
    ensure_parent_dir(path)
    temp_path = path.with_name(f"{path.name}.tmp")
    with temp_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    temp_path.replace(path)
    return payload
