from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.config import MODEL_META_PATH
from app.services.state_store import read_json_file, write_json_file


def default_model_meta() -> dict[str, Any]:
    return {
        "updated_at": None,
        "source": None,
        "pool": None,
        "feature_columns": [],
        "metrics": None,
        "backtest": None,
        "history": [],
    }


def read_model_meta() -> dict[str, Any]:
    payload = read_json_file(MODEL_META_PATH, default_factory=default_model_meta)
    base = default_model_meta()
    if isinstance(payload, dict):
        base.update(payload)
    return base


def write_model_meta(
    *,
    source: str,
    pool: str | None,
    feature_columns: list[str],
    metrics: dict[str, Any] | None,
    backtest: dict[str, Any] | None,
) -> dict[str, Any]:
    current = read_model_meta()
    history = list(current.get("history") or [])
    payload = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "pool": pool,
        "feature_columns": feature_columns,
        "metrics": metrics,
        "backtest": backtest,
        "version": f"{source}-{pool}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "history": history[-19:]
        + [
            {
                "updated_at": datetime.now().isoformat(timespec="seconds"),
                "source": source,
                "pool": pool,
                "feature_count": len(feature_columns),
                "metrics": metrics,
                "backtest": backtest,
                "version": f"{source}-{pool}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            }
        ],
    }
    return write_json_file(MODEL_META_PATH, payload)
