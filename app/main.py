# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from datetime import datetime

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.core.config import BASE_DIR, DEFAULT_DATA_PATH, DEFAULT_MODEL_PATH, REAL_DATA_PATH, REFRESH_LOG_PATH
from app.services.dataset import FEATURE_COLUMNS, build_features, build_scoring_frame, get_data_health_report, latest_snapshot, load_price_data
from app.services.hot_news import get_hot_news
from app.services.market_overview import get_market_overview
from app.services.market_watch import (
    add_custom_watchlist_item,
    build_history_payload,
    build_watch_snapshot,
    delete_custom_watchlist_item,
    get_custom_watchlist_snapshot,
    get_intraday_change_history,
    get_watchlist_history,
    search_symbols,
)
from app.services.model_state import read_model_meta, write_model_meta
from app.services.modeling import build_pick_explanations, load_model, score_snapshot, train_model
from app.services.paper_portfolio import export_portfolio_state, get_portfolio_snapshot, import_portfolio_state, place_order, reset_portfolio, update_portfolio_settings
from app.services.refresh_status import get_runtime_refresh_status, write_refresh_status


app = FastAPI(title="A股选股本地实验室", version="0.5.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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


def persist_model_meta(source: str, prices, metrics: dict | None) -> dict | None:
    if not metrics:
        return read_model_meta()
    pool = str(prices["pool"].iloc[0]) if "pool" in prices.columns and not prices.empty else "sample"
    return write_model_meta(
        source=source,
        pool=pool,
        feature_columns=list(FEATURE_COLUMNS),
        metrics={key: value for key, value in metrics.items() if key != "backtest"},
        backtest=metrics.get("backtest"),
    )


def ensure_model(source: str = "real") -> dict:
    state_source = resolve_state_source(source)
    data_source, data_path = get_data_path(state_source)
    prices = load_price_data(data_path, source=data_source, allow_remote_fetch=False)
    train_features = build_features(prices)
    scoring_frame = build_scoring_frame(prices)

    trained = False
    metrics: dict | None = None
    snapshot = latest_snapshot(scoring_frame)
    model_meta = read_model_meta()

    def retrain_current_model() -> tuple[dict | None, Any]:
        fresh_metrics = train_model(train_features, DEFAULT_MODEL_PATH)
        persist_model_meta(data_source, prices, fresh_metrics)
        return fresh_metrics, load_model(DEFAULT_MODEL_PATH)

    if not DEFAULT_MODEL_PATH.exists():
        metrics, model = retrain_current_model()
        trained = True
    else:
        try:
            model = load_model(DEFAULT_MODEL_PATH)
            ranked_probe = score_snapshot(model, snapshot)
            if not model_meta.get("updated_at"):
                metrics, model = retrain_current_model()
                trained = True
                ranked = score_snapshot(model, snapshot)
            else:
                ranked = ranked_probe
        except Exception:
            metrics, model = retrain_current_model()
            trained = True
            ranked = score_snapshot(model, snapshot)

    if "ranked" not in locals():
        ranked = score_snapshot(model, snapshot)
    ranked = build_pick_explanations(model, ranked)
    model_meta = read_model_meta()

    return {
        "trained": trained,
        "metrics": metrics,
        "prices": prices,
        "train_features": train_features,
        "scoring_frame": scoring_frame,
        "ranked": ranked,
        "source": data_source,
        "model_meta": model_meta,
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


class FavoritePayload(BaseModel):
    symbol: str
    name: str | None = None
    kind: str = "stock"


class OrderPayload(BaseModel):
    symbol: str
    side: str
    quantity: int
    price: float | None = None
    price_mode: str | None = "live"
    name: str | None = None


class PortfolioResetPayload(BaseModel):
    initial_cash: float | None = None


class PortfolioSettingsPayload(BaseModel):
    commission_rate: float | None = None
    min_commission: float | None = None
    stamp_duty_rate: float | None = None
    slippage_bps: float | None = None


class PortfolioImportPayload(BaseModel):
    portfolio: dict | None = None


class ScreenerPayload(BaseModel):
    min_predicted_return_5: float | None = 2.0
    min_confidence_score: float | None = 0.45


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
    model_meta = state.get("model_meta") or {}
    health = get_data_health_report(prices)
    return {
        "latest_date": latest_date,
        "universe_size": int(prices["symbol"].nunique()),
        "feature_count": len(FEATURE_COLUMNS),
        "sample_rows": int(len(train_features)),
        "data_source": state["source"],
        "data_health": health,
        "pool": str(prices["pool"].iloc[0]) if "pool" in prices.columns and not prices.empty else "sample",
        "top_pick": {
            "symbol": top_pick["symbol"],
            "name": top_pick["name"],
            "predicted_return_5": round(float(top_pick["predicted_return_5"]) * 100, 2),
        },
        "trained_now": state["trained"],
        "training_metrics": state["metrics"],
        "model_meta": model_meta,
    }


@app.get("/api/model-history")
def model_history() -> dict:
    meta = read_model_meta()
    return {"items": meta.get("history") or [], "updated_at": meta.get("updated_at")}


@app.get("/api/market-overview")
def market_overview(limit: int = 6) -> dict:
    try:
        return get_market_overview(limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"market overview unavailable: {exc}") from exc


@app.get("/api/data-health")
def data_health(source: str = "real") -> dict:
    state_source = resolve_state_source(source)
    _, data_path = get_data_path(state_source)
    prices = load_price_data(data_path, source=state_source, allow_remote_fetch=False)
    return get_data_health_report(prices)


@app.get("/api/hot-news")
def hot_news(limit: int = 16, offset: int = 0, category: str = "all", force_refresh: bool = False) -> dict:
    try:
        return get_hot_news(limit=limit, offset=offset, category=category, force_refresh=force_refresh)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"hot news unavailable: {exc}") from exc


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
                "ret_20": round(float(row["ret_20"]) * 100, 2),
                "predicted_return_5": round(float(row["predicted_return_5"]) * 100, 2),
                "reason_summary": row.get("reason_summary"),
                "reason_tags": row.get("reason_tags") or [],
                "reason_texts": row.get("reason_texts") or [],
                "basis_items": row.get("basis_items") or [],
                "risk_texts": row.get("risk_texts") or [],
                "confidence_score": round(float(row.get("confidence_score") or 0), 2) if row.get("confidence_score") is not None else None,
                "confidence_label": row.get("confidence_label"),
                "risk_score": round(float(row.get("risk_score") or 0), 2) if row.get("risk_score") is not None else None,
                "risk_level": row.get("risk_level"),
            }
        )
    return {"items": records, "source": state["source"], "model_meta": state.get("model_meta")}


@app.get("/api/watchlist")
def watchlist(limit: int = 8, source: str = "real") -> dict:
    symbols = get_watch_symbols(limit=limit, source=source)
    snapshot = build_watch_snapshot(symbols)
    return {**snapshot, "source": source}


@app.get("/api/watch-history/{symbol}")
def watch_history(symbol: str, limit: int = 60, period: str = "day") -> dict:
    if period != "day":
        return build_history_payload(symbol, period=period, limit=limit)
    items = get_watchlist_history(symbol, limit=limit)
    return {"items": items, "symbol": str(symbol).zfill(6), "period": "day", "limit": limit}


@app.get("/api/chart-history/{symbol}")
def chart_history(symbol: str, period: str = "day", limit: int = 120) -> dict:
    try:
        return build_history_payload(symbol, period=period, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/history/{symbol}")
def unified_history(symbol: str, period: str = "day", limit: int = 120) -> dict:
    try:
        return build_history_payload(symbol, period=period, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/watch-intraday/{symbol}")
def watch_intraday(symbol: str, trade_date: str) -> dict:
    payload = get_intraday_change_history(symbol, trade_date=trade_date)
    payload["symbol"] = str(symbol)
    return payload


@app.get("/api/search")
def search(query: str, limit: int = 12) -> dict:
    items = search_symbols(query, limit=limit)
    for item in items:
        if item.get("history_status") != "local":
            item["note"] = "该股票不在当前训练池中，仅支持远程查询"
    return {"items": items, "query": query}


@app.get("/api/favorites")
def favorites() -> dict:
    payload = get_custom_watchlist_snapshot()
    return {"items": payload["items"], "updated_at": payload.get("updated_at"), "meta": payload.get("meta")}


@app.post("/api/favorites")
def add_favorite(payload: FavoritePayload | None = Body(default=None), symbol: str | None = None, name: str | None = None, kind: str = "stock") -> dict:
    target_symbol = payload.symbol if payload else symbol
    if not target_symbol:
        raise HTTPException(status_code=400, detail="symbol is required")
    target_name = payload.name if payload else name
    target_kind = payload.kind if payload else kind
    return add_custom_watchlist_item(symbol=target_symbol, name=target_name, kind=target_kind)


@app.delete("/api/favorites/{symbol}")
def delete_favorite(symbol: str, kind: str | None = None) -> dict:
    return delete_custom_watchlist_item(symbol=symbol, kind=kind)


@app.get("/api/portfolio")
def portfolio() -> dict:
    return get_portfolio_snapshot()


@app.post("/api/portfolio/orders")
def portfolio_order(payload: OrderPayload) -> dict:
    try:
        return place_order(
            symbol=payload.symbol,
            side=payload.side,
            quantity=payload.quantity,
            price=payload.price,
            price_mode=payload.price_mode,
            name=payload.name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/portfolio/reset")
def portfolio_reset(payload: PortfolioResetPayload | None = Body(default=None)) -> dict:
    return reset_portfolio(initial_cash=payload.initial_cash if payload else None)


@app.post("/api/portfolio/settings")
def portfolio_settings(payload: PortfolioSettingsPayload) -> dict:
    try:
        return update_portfolio_settings(payload.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/portfolio/export")
def portfolio_export() -> dict:
    return export_portfolio_state()


@app.post("/api/portfolio/import")
def portfolio_import(payload: dict = Body(...)) -> dict:
    try:
        return import_portfolio_state(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/screener")
def screener(min_predicted_return_5: float = 2.0, min_confidence_score: float = 0.45, source: str = "real") -> dict:
    state = ensure_model(source)
    ranked = state["ranked"].copy()
    confidence = ranked["confidence_score"] if "confidence_score" in ranked.columns else 0
    filtered = ranked.loc[(ranked["predicted_return_5"] * 100 >= min_predicted_return_5) & (confidence >= min_confidence_score)].head(40)
    return {
        "items": [
            {
                "symbol": row["symbol"],
                "name": row["name"],
                "predicted_return_5": round(float(row["predicted_return_5"]) * 100, 2),
                "confidence_score": round(float(row.get("confidence_score") or 0), 2) if row.get("confidence_score") is not None else None,
                "confidence_label": row.get("confidence_label"),
                "risk_level": row.get("risk_level"),
                "reason_summary": row.get("reason_summary"),
            }
            for row in filtered.to_dict(orient="records")
        ],
        "source": state["source"],
    }


@app.get("/api/rotation")
def rotation() -> dict:
    market = get_market_overview(limit=8)
    return {
        "updated_at": market.get("updated_at"),
        "items": market.get("a_share_rotation") or [],
    }


@app.get("/api/prepost")
@app.get("/api/prepost")
def prepost() -> dict:
    warnings = []
    market = {}
    hot_items = []
    try:
        market = get_market_overview(limit=4)
    except Exception as exc:
        warnings.append(f"market overview unavailable: {exc}")
    try:
        hot = get_hot_news(limit=8, category="tech")
        hot_items = [
            {
                "title": item.get("title"),
                "summary": item.get("ai_summary") or item.get("summary"),
                "time": item.get("published_at"),
                "tone": item.get("ai_tone"),
            }
            for item in hot.get("items", [])[:8]
        ]
    except Exception as exc:
        warnings.append(f"hot news unavailable: {exc}")
    return {
        "updated_at": market.get("updated_at"),
        "market": market,
        "items": hot_items,
        "warnings": warnings,
    }


@app.get("/api/stock-info/{symbol}")
def stock_info(symbol: str) -> dict:
    hist = build_history_payload(symbol, period="day", limit=5)
    items = hist.get("items", [])
    name = hist.get("name") or symbol
    last = items[-1] if items else {}
    prev = items[-2] if len(items) >= 2 else {}
    price = last.get("close")
    prev_close = prev.get("close")
    change_pct = None
    if price and prev_close and float(prev_close) != 0:
        change_pct = round((float(price) / float(prev_close) - 1) * 100, 2)
    return {
        "symbol": symbol,
        "name": name,
        "price": price,
        "change_pct": change_pct,
        "date": last.get("date"),
    }


@app.get("/api/stock-analysis/{symbol}")
def stock_analysis(symbol: str) -> dict:
    import statistics

    hist = build_history_payload(symbol, period="day", limit=60)
    name = hist.get("name") or symbol
    items = hist.get("items", [])
    close_prices = [float(it.get("close", 0)) for it in items if it.get("close")]

    # Recent returns
    def _ret(n):
        if len(close_prices) >= n + 1 and close_prices[-n - 1] != 0:
            return round((close_prices[-1] / close_prices[-n - 1] - 1) * 100, 2)
        return None

    ret_5, ret_10, ret_20 = _ret(5), _ret(10), _ret(20)
    current_price = close_prices[-1] if close_prices else None

    # Volatility
    daily_changes = []
    for i in range(1, len(close_prices)):
        if close_prices[i - 1] != 0:
            daily_changes.append((close_prices[i] / close_prices[i - 1] - 1) * 100)
    volatility = round(statistics.stdev(daily_changes), 2) if len(daily_changes) > 1 else None

    # Trend
    trend = "flat"
    if len(close_prices) >= 10:
        ma5 = sum(close_prices[-5:]) / 5
        ma10 = sum(close_prices[-10:]) / 10
        if close_prices[-1] > ma5 > ma10:
            trend = "up"
        elif close_prices[-1] < ma5 < ma10:
            trend = "down"

    # Check model picks
    model_signal = None
    try:
        model = load_model()
        if model is not None:
            snapshot = build_scoring_frame()
            if snapshot is not None:
                ranked = score_snapshot(model, snapshot)
                ranked = build_pick_explanations(model, ranked)
                match = ranked[ranked["symbol"] == symbol] if "symbol" in ranked.columns else ranked.head(0)
                if not match.empty:
                    row = match.iloc[0]
                    model_signal = {
                        "rank": int(row.get("rank", 0)),
                        "predicted_return": float(row.get("predicted_return", 0)),
                        "reason": str(row.get("explanation", "")),
                        "confidence": str(row.get("confidence", "")),
                    }
    except Exception:
        pass

    # Hot news
    news_items = []
    try:
        hot = get_hot_news(limit=20, category="all")
        for item in hot.get("items", []):
            title = str(item.get("title", ""))
            if name in title or symbol in title or (name and len(name) >= 2 and name[:2] in title):
                news_items.append({
                    "title": title,
                    "time": item.get("published_at", ""),
                    "summary": item.get("ai_summary") or item.get("summary", ""),
                    "tone": item.get("ai_tone", "neutral"),
                })
    except Exception:
        pass

    # Bullish / bearish signals
    bullish, bearish = [], []
    if trend == "up":
        bullish.append("均线多头排列，短期趋势向上")
    elif trend == "down":
        bearish.append("均线空头排列，短期趋势向下")

    if ret_5 is not None:
        if ret_5 > 3:
            bullish.append(f"近5日涨幅{ret_5}%，短期动能强")
        elif ret_5 < -3:
            bearish.append(f"近5日跌幅{ret_5}%，短期承压")

    if volatility is not None:
        if volatility > 3:
            bearish.append(f"日均波动{volatility}%，风险偏高")
        elif volatility < 1.5:
            bullish.append(f"日均波动{volatility}%，走势平稳")

    if model_signal:
        if model_signal.get("predicted_return", 0) > 1:
            bullish.append(f"模型预测未来5日涨{model_signal['predicted_return']}%")
        elif model_signal.get("predicted_return", 0) < -1:
            bearish.append(f"模型预测未来5日跌{model_signal['predicted_return']}%")

    if not bullish:
        bullish.append("暂无明显利好信号")
    if not bearish:
        bearish.append("暂无明显利空信号")

    # Price history for chart
    price_items = []
    for it in items[-30:]:
        price_items.append({
            "date": it.get("date"),
            "close": it.get("close"),
            "change_pct": it.get("change_pct"),
        })

    return {
        "symbol": symbol,
        "name": name,
        "current_price": current_price,
        "trend": trend,
        "volatility": volatility,
        "returns": {"5d": ret_5, "10d": ret_10, "20d": ret_20},
        "bullish": bullish,
        "bearish": bearish,
        "model_signal": model_signal,
        "related_news": news_items,
        "price_history": price_items,
        "updated_at": datetime.now().isoformat(),
    }

@app.get("/api/alerts")
def alerts() -> dict:
    market = get_market_overview(limit=6)
    items = []
    for sector in (market.get("us_industry_leaders") or [])[:6]:
        items.append(
            {
                "title": f"{sector.get('name')} 领涨",
                "body": f"涨幅 {sector.get('change_pct')}%，领涨股 {sector.get('leader_name') or '-'}",
                "category": "板块",
            }
        )
    return {"updated_at": market.get("updated_at"), "items": items}


@app.post("/api/train")
def retrain(source: str = "real") -> dict:
    state_source = resolve_state_source(source)
    data_source, data_path = get_data_path(state_source)
    prices = load_price_data(data_path, source=data_source, allow_remote_fetch=False)
    features = build_features(prices)
    metrics = train_model(features, DEFAULT_MODEL_PATH)
    model_meta = persist_model_meta(data_source, prices, metrics)
    return {"message": "模型已重新训练", "metrics": metrics, "source": data_source, "model_meta": model_meta}


@app.get("/api/refresh-real-data/status")
def refresh_real_data_status() -> dict:
    return get_runtime_refresh_status()


@app.post("/api/refresh-real-data")
def refresh_real_data(pool: str = "hs300") -> dict:
    status = get_runtime_refresh_status()
    if status["state"] == "running":
        return {"message": "已有真实数据刷新任务在运行", "status": status}

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
    return {"message": "真实数据刷新任务已在后台启动", "status": status}
