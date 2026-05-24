from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import BASE_DIR, DEFAULT_DATA_PATH, DEFAULT_MODEL_PATH, REAL_DATA_PATH
from app.services.dataset import (
    FEATURE_COLUMNS,
    build_features,
    fetch_real_dataset,
    load_index_constituents,
    latest_snapshot,
    load_price_data,
)
from app.services.modeling import load_model, score_snapshot, train_model


app = FastAPI(title="A股选股模型", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = BASE_DIR / "frontend"
app.mount("/assets", StaticFiles(directory=frontend_dir), name="assets")


def get_data_path(source: str) -> tuple[str, object]:
    if source == "real":
        return source, REAL_DATA_PATH
    return "sample", DEFAULT_DATA_PATH


def ensure_model(source: str = "real") -> dict:
    data_source, data_path = get_data_path(source)
    try:
        prices = load_price_data(data_path, source=data_source)
    except Exception:
        data_source = "sample"
        _, fallback_path = get_data_path(data_source)
        prices = load_price_data(fallback_path, source=data_source)
    features = build_features(prices)

    trained = False
    metrics: dict | None = None
    if not DEFAULT_MODEL_PATH.exists():
        metrics = train_model(features, DEFAULT_MODEL_PATH)
        trained = True

    model = load_model(DEFAULT_MODEL_PATH)
    snapshot = latest_snapshot(features)
    ranked = score_snapshot(model, snapshot)

    return {
        "trained": trained,
        "metrics": metrics,
        "prices": prices,
        "features": features,
        "ranked": ranked,
        "source": data_source,
    }


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
    features = state["features"]
    ranked = state["ranked"]

    latest_date = ranked["date"].max().strftime("%Y-%m-%d")
    top_pick = ranked.iloc[0]

    return {
        "latest_date": latest_date,
        "universe_size": int(prices["symbol"].nunique()),
        "feature_count": len(FEATURE_COLUMNS),
        "sample_rows": int(len(features)),
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


@app.post("/api/train")
def retrain(source: str = "real") -> dict:
    state_source, data_path = get_data_path(source)
    prices = load_price_data(data_path, source=state_source)
    features = build_features(prices)
    metrics = train_model(features, DEFAULT_MODEL_PATH)
    return {"message": "模型已重新训练", "metrics": metrics, "source": state_source}


@app.post("/api/refresh-real-data")
def refresh_real_data(pool: str = "hs300") -> dict:
    try:
        symbols = load_index_constituents(pool)
        prices = fetch_real_dataset(REAL_DATA_PATH, symbols=symbols, pool=pool)
        features = build_features(prices)
        metrics = train_model(features, DEFAULT_MODEL_PATH)
    except Exception as exc:  # pragma: no cover - surfacing runtime integration issues
        raise HTTPException(status_code=502, detail=f"刷新真实A股数据失败: {exc}") from exc

    return {
        "message": "真实A股数据已刷新并完成训练",
        "rows": int(len(prices)),
        "symbols": int(prices["symbol"].nunique()),
        "pool": pool,
        "metrics": metrics,
    }
