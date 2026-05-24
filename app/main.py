from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import (
    BASE_DIR,
    DEFAULT_DATA_PATH,
    DEFAULT_MODEL_PATH,
    REAL_DATA_PATH,
    REFRESH_LOG_PATH,
)
from app.services.dataset import (
    FEATURE_COLUMNS,
    build_features,
    build_scoring_frame,
    latest_snapshot,
    load_price_data,
)
from app.services.market_watch import get_watchlist_history, merge_live_and_close
from app.services.modeling import load_model, score_snapshot, train_model
from app.services.refresh_status import get_runtime_refresh_status, write_refresh_status


app = FastAPI(title="A股选股模型", version="0.4.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = BASE_DIR / "frontend"
app.mount("/assets", StaticFiles(directory=frontend_dir), name="assets")


def get_data_path(source: str) -> tuple[str, Path]:
    if source == "real":
        return source, REAL_DATA_PATH
    return "sample", DEFAULT_DATA_PATH


def resolve_state_source(source: str) -> str:
    if source == "real" and REAL_DATA_PATH.exists():
        return "real"
    return "sample"


def ensure_model(source: str = "real") -> dict:
    state_source = resolve_state_source(source)
    data_source, data_path = get_data_path(state_source)
    prices = load_price_data(data_path, source=data_source, allow_remote_fetch=False)
    train_features = build_features(prices)
    scoring_frame = build_scoring_frame(prices)

    trained = False
    metrics: dict | None = None
    if not DEFAULT_MODEL_PATH.exists():
        metrics = train_model(train_features, DEFAULT_MODEL_PATH)
        trained = True

    model = load_model(DEFAULT_MODEL_PATH)
    snapshot = latest_snapshot(scoring_frame)
    ranked = score_snapshot(model, snapshot)

    return {
        "trained": trained,
        "metrics": metrics,
        "prices": prices,
        "train_features": train_features,
        "scoring_frame": scoring_frame,
        "ranked": ranked,
        "source": data_source,
    }


def get_python_executable() -> str:
    venv_python = BASE_DIR / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def get_refresh_script() -> Path:
    return BASE_DIR / "scripts" / "refresh_real_data.py"


def get_watch_symbols(limit: int = 8, source: str = "real") -> list[str]:
    state = ensure_model(source)
    ranked = state["ranked"].head(limit)
    return [str(symbol).zfill(6) for symbol in ranked["symbol"].tolist()]


@app.get("/")
def index() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/overview")
def overview(source: str = "real") -> dict:
    state = ensure_model(source)
    prices = state["prices"]
    train_features = state["train_features"]
    ranked = state["ranked"]

    latest_date = ranked["date"].max().strftime("%Y-%m-%d")
    top_pick = ranked.iloc[0]

    return {
        "latest_date": latest_date,
        "universe_size": int(prices["symbol"].nunique()),
        "feature_count": len(FEATURE_COLUMNS),
        "sample_rows": int(len(train_features)),
        "data_source": state["source"],
        "pool": str(prices["pool"].iloc[0]) if "pool" in prices.columns and not prices.empty else "sample",
        "top_pick": {
            "symbol": top_pick["symbol"],
            "name": top_pick["name"],
            "predicted_return_5": round(float(top_pick["predicted_return_5"]) * 100, 2),
        },
        "trained_now": state["trained"],
        "training_metrics": state["metrics"],
    }


@app.get("/api/picks")
def picks(limit: int = 8, source: str = "real") -> dict:
    state = ensure_model(source)
    ranked = state["ranked"].head(limit).copy()
    records = []
    for row in ranked.to_dict(orient="records"):
        records.append(
            {
                "date": row["date"].strftime("%Y-%m-%d"),
                "symbol": str(row["symbol"]).zfill(6),
                "name": row["name"],
                "close": round(float(row["close"]), 2),
                "ret_5": round(float(row["ret_5"]) * 100, 2),
                "ret_10": round(float(row["ret_10"]) * 100, 2),
                "predicted_return_5": round(float(row["predicted_return_5"]) * 100, 2),
            }
        )
    return {"items": records, "source": state["source"]}


@app.get("/api/watchlist")
def watchlist(limit: int = 8, source: str = "real") -> dict:
    symbols = get_watch_symbols(limit=limit, source=source)
    items = merge_live_and_close(symbols)
    return {"items": items, "source": source}


@app.get("/api/watch-history/{symbol}")
def watch_history(symbol: str, limit: int = 60) -> dict:
    items = get_watchlist_history(symbol, limit=limit)
    return {"items": items, "symbol": str(symbol).zfill(6)}


@app.post("/api/train")
def retrain(source: str = "real") -> dict:
    state_source = resolve_state_source(source)
    data_source, data_path = get_data_path(state_source)
    prices = load_price_data(data_path, source=data_source, allow_remote_fetch=False)
    features = build_features(prices)
    metrics = train_model(features, DEFAULT_MODEL_PATH)
    return {"message": "模型已重新训练", "metrics": metrics, "source": data_source}


@app.get("/api/refresh-real-data/status")
def refresh_real_data_status() -> dict:
    return get_runtime_refresh_status()


@app.post("/api/refresh-real-data")
def refresh_real_data(pool: str = "hs300") -> dict:
    status = get_runtime_refresh_status()
    if status["state"] == "running":
        return {
            "message": "已有真实数据刷新任务在运行",
            "status": status,
        }

    python_executable = get_python_executable()
    script_path = get_refresh_script()
    REFRESH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with REFRESH_LOG_PATH.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            [python_executable, str(script_path), "--pool", pool],
            cwd=str(BASE_DIR),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

    status = write_refresh_status(
        {
            "state": "running",
            "pool": pool,
            "pid": process.pid,
            "started_at": None,
            "finished_at": None,
            "message": f"后台任务已启动，正在刷新 {pool} 数据",
            "rows": None,
            "symbols": None,
            "metrics": None,
            "error": None,
            "log_path": str(REFRESH_LOG_PATH),
        }
    )

    return {
        "message": "真实数据刷新任务已在后台启动",
        "status": status,
    }
