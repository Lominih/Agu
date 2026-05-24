from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import DEFAULT_DATA_PATH, DEFAULT_MODEL_PATH, BASE_DIR
from app.services.dataset import FEATURE_COLUMNS, build_features, latest_snapshot, load_price_data
from app.services.modeling import load_model, score_snapshot, train_model


app = FastAPI(title="A股选股模型", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = BASE_DIR / "frontend"
app.mount("/assets", StaticFiles(directory=frontend_dir), name="assets")


def ensure_model() -> dict:
    prices = load_price_data(DEFAULT_DATA_PATH)
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
    }


@app.get("/")
def index() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/overview")
def overview() -> dict:
    state = ensure_model()
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
        "top_pick": {
            "symbol": top_pick["symbol"],
            "name": top_pick["name"],
            "predicted_return_5": round(float(top_pick["predicted_return_5"]) * 100, 2),
        },
        "trained_now": state["trained"],
        "training_metrics": state["metrics"],
    }


@app.get("/api/picks")
def picks(limit: int = 5) -> dict:
    state = ensure_model()
    ranked = state["ranked"].head(limit).copy()
    records = []
    for row in ranked.to_dict(orient="records"):
        records.append(
            {
                "date": row["date"].strftime("%Y-%m-%d"),
                "symbol": row["symbol"],
                "name": row["name"],
                "close": round(float(row["close"]), 2),
                "ret_5": round(float(row["ret_5"]) * 100, 2),
                "ret_10": round(float(row["ret_10"]) * 100, 2),
                "predicted_return_5": round(float(row["predicted_return_5"]) * 100, 2),
            }
        )
    return {"items": records}


@app.post("/api/train")
def retrain() -> dict:
    prices = load_price_data(DEFAULT_DATA_PATH)
    features = build_features(prices)
    metrics = train_model(features, DEFAULT_MODEL_PATH)
    return {"message": "模型已重新训练", "metrics": metrics}
