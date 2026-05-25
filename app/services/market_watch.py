from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import akshare as ak
import easyquotation
import pandas as pd

from app.core.config import DATA_DIR, DEFAULT_DATA_PATH, HISTORY_CACHE_DIR, REAL_DATA_PATH, STOCK_CATALOG_CACHE_PATH
from app.services.dataset import load_price_data
from app.services.state_store import read_json_file, write_json_file


CUSTOM_WATCHLIST_PATH = DATA_DIR / "custom_watchlist.json"
INDEX_SYMBOL_ALIASES = {
    "sh000001": "sh000001",
    "000001.sh": "sh000001",
    "000001.xshg": "sh000001",
    "000001_index": "sh000001",
}
INDEX_DISPLAY_NAMES = {
    "sh000001": "上证指数",
}
HISTORY_PERIOD_CONFIG = {
    "day": {"mode": "daily", "default_limit": 60},
    "week": {"mode": "daily", "default_limit": 52, "resample_rule": "W-FRI"},
    "month": {"mode": "daily", "default_limit": 60, "resample_rule": "ME"},
    "quarter": {"mode": "daily", "default_limit": 40, "resample_rule": "QE-DEC"},
    "year": {"mode": "daily", "default_limit": 12, "resample_rule": "YE-DEC"},
    "1m": {"mode": "minute", "default_limit": 240, "minute_period": "1"},
    "5m": {"mode": "minute", "default_limit": 240, "minute_period": "5"},
    "15m": {"mode": "minute", "default_limit": 200, "minute_period": "15"},
    "30m": {"mode": "minute", "default_limit": 160, "minute_period": "30"},
    "60m": {"mode": "minute", "default_limit": 120, "minute_period": "60"},
    "5d": {"mode": "minute_window", "default_limit": 1200, "minute_period": "1", "days": 5},
}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


@lru_cache(maxsize=1)
def get_quote_client():
    return easyquotation.use("sina")


def normalize_symbol(symbol: str) -> str:
    return str(symbol).zfill(6)


def is_index_symbol(symbol: str) -> bool:
    return str(symbol).lower() in INDEX_SYMBOL_ALIASES


def normalize_history_period(period: str | None) -> str:
    value = (period or "day").strip().lower()
    if value not in HISTORY_PERIOD_CONFIG:
        raise ValueError(f"Unsupported period: {period}")
    return value


def normalize_index_symbol(symbol: str) -> str:
    raw = str(symbol).strip().lower()
    return INDEX_SYMBOL_ALIASES.get(raw, raw)


def get_index_display_name(symbol: str) -> str:
    return INDEX_DISPLAY_NAMES.get(normalize_index_symbol(symbol), str(symbol))


def get_default_history_limit(period: str) -> int:
    return int(HISTORY_PERIOD_CONFIG[period]["default_limit"])


def resolve_history_limit(period: str, limit: int | None = None) -> int:
    if limit is None or limit <= 0:
        return get_default_history_limit(period)
    return int(limit)


def clamp_history_limit(period: str, limit: int | None = None) -> int:
    normalized_limit = resolve_history_limit(period, limit)
    return min(normalized_limit, 2400 if HISTORY_PERIOD_CONFIG[period]["mode"] != "daily" else 520)


def safe_float(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_local_price_frame(prefer_real: bool = True) -> pd.DataFrame:
    if prefer_real and REAL_DATA_PATH.exists():
        return load_price_data(REAL_DATA_PATH, source="real", allow_remote_fetch=False)
    return load_price_data(DEFAULT_DATA_PATH, source="sample", allow_remote_fetch=False)


def ensure_ohlc_columns(frame: pd.DataFrame) -> pd.DataFrame:
    working = frame.copy()
    if "open" not in working.columns:
        working["open"] = working["close"]
    if "high" not in working.columns:
        working["high"] = working["close"]
    if "low" not in working.columns:
        working["low"] = working["close"]
    if "volume" not in working.columns:
        working["volume"] = None
    if "amount" not in working.columns:
        working["amount"] = None
    return working


def resample_ohlc_frame(frame: pd.DataFrame, rule: str) -> pd.DataFrame:
    working = ensure_ohlc_columns(frame)
    working["date"] = pd.to_datetime(working["date"])
    working = working.sort_values("date")
    aggregations: dict[str, str] = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }
    if "amount" in working.columns:
        aggregations["amount"] = "sum"
    resampled = (
        working.set_index("date")
        .resample(rule)
        .agg(aggregations)
        .dropna(subset=["open", "high", "low", "close"], how="any")
        .reset_index()
    )
    if not resampled.empty:
        for column in ("symbol", "name", "pool"):
            if column in working.columns and working[column].dropna().shape[0]:
                resampled[column] = working[column].dropna().iloc[-1]
    return resampled


def normalize_akshare_hist_frame(frame: pd.DataFrame) -> pd.DataFrame:
    column_map = {
        "日期": "date",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
        "成交额": "amount",
        "股票代码": "symbol",
        "股票名称": "name",
    }
    working = frame.rename(columns=column_map).copy()
    if "date" not in working.columns:
        raise ValueError("history frame missing date column")
    for column in ("open", "high", "low", "close", "volume", "amount"):
        if column in working.columns:
            working[column] = pd.to_numeric(working[column], errors="coerce")
    return working


def normalize_akshare_minute_frame(frame: pd.DataFrame) -> pd.DataFrame:
    column_map = {
        "day": "date",
        "时间": "date",
        "日期时间": "date",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
        "成交额": "amount",
        "最新价": "close",
    }
    working = frame.rename(columns=column_map).copy()
    if "date" not in working.columns:
        raise ValueError("minute frame missing date column")
    working["date"] = pd.to_datetime(working["date"], errors="coerce")
    for column in ("open", "high", "low", "close", "volume", "amount"):
        if column in working.columns:
            working[column] = pd.to_numeric(working[column], errors="coerce")
    working = working.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return ensure_ohlc_columns(working)


def format_ohlc_history(frame: pd.DataFrame) -> list[dict]:
    working = ensure_ohlc_columns(frame).copy().sort_values("date")
    working["prev_close"] = working["close"].shift(1)
    working["change_pct"] = (working["close"] / working["prev_close"] - 1) * 100
    records: list[dict] = []
    for row in working.to_dict(orient="records"):
        records.append(
            {
                "date": pd.Timestamp(row["date"]).strftime("%Y-%m-%d"),
                "datetime": pd.Timestamp(row["date"]).strftime("%Y-%m-%d 15:00:00"),
                "open": round(float(row["open"]), 2) if pd.notna(row.get("open")) else None,
                "high": round(float(row["high"]), 2) if pd.notna(row.get("high")) else None,
                "low": round(float(row["low"]), 2) if pd.notna(row.get("low")) else None,
                "close": round(float(row["close"]), 2) if pd.notna(row.get("close")) else None,
                "prev_close": round(float(row["prev_close"]), 2) if pd.notna(row.get("prev_close")) else None,
                "volume": int(float(row["volume"])) if pd.notna(row.get("volume")) else None,
                "amount": round(float(row["amount"]), 2) if pd.notna(row.get("amount")) else None,
                "change_pct": round(float(row["change_pct"]), 2) if pd.notna(row.get("change_pct")) else None,
                "name": row.get("name"),
                "symbol": row.get("symbol"),
                "pool": row.get("pool", "sample"),
            }
        )
    return records


def format_history_frame(frame: pd.DataFrame, limit: int | None = None) -> list[dict]:
    working = ensure_ohlc_columns(frame)
    if limit is not None and limit > 0:
        working = working.sort_values("date").tail(limit)
    return format_ohlc_history(working)


def format_minute_history_frame(frame: pd.DataFrame, limit: int | None = None) -> list[dict]:
    working = ensure_ohlc_columns(frame)
    if limit is not None and limit > 0:
        working = working.sort_values("date").tail(limit)
    working = working.sort_values("date").copy()
    working["prev_close"] = working["close"].shift(1)
    working["change_pct"] = (working["close"] / working["prev_close"] - 1) * 100
    records: list[dict] = []
    for row in working.to_dict(orient="records"):
        date_value = pd.Timestamp(row["date"])
        records.append(
            {
                "date": date_value.strftime("%Y-%m-%d"),
                "time": date_value.strftime("%H:%M"),
                "datetime": date_value.strftime("%Y-%m-%d %H:%M:%S"),
                "open": round(float(row["open"]), 2) if pd.notna(row.get("open")) else None,
                "high": round(float(row["high"]), 2) if pd.notna(row.get("high")) else None,
                "low": round(float(row["low"]), 2) if pd.notna(row.get("low")) else None,
                "close": round(float(row["close"]), 2) if pd.notna(row.get("close")) else None,
                "prev_close": round(float(row["prev_close"]), 2) if pd.notna(row.get("prev_close")) else None,
                "change_pct": round(float(row["change_pct"]), 2) if pd.notna(row.get("change_pct")) else None,
                "volume": int(float(row["volume"])) if pd.notna(row.get("volume")) else None,
                "amount": round(float(row["amount"]), 2) if pd.notna(row.get("amount")) else None,
                "name": row.get("name"),
                "symbol": row.get("symbol"),
                "pool": row.get("pool"),
            }
        )
    return records


def fetch_remote_stock_daily_history_frame(symbol: str, limit: int) -> pd.DataFrame:
    frame = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq").copy()
    frame = normalize_akshare_hist_frame(frame)
    frame["date"] = pd.to_datetime(frame["date"])
    frame["symbol"] = normalize_symbol(symbol)
    frame["pool"] = "remote"
    frame["name"] = frame.get("name")
    return ensure_ohlc_columns(frame).sort_values("date").tail(limit).reset_index(drop=True)


def fetch_stock_daily_history_frame(symbol: str, limit: int) -> tuple[pd.DataFrame, str]:
    normalized = normalize_symbol(symbol)
    prices = get_local_price_frame(prefer_real=True)
    frame = prices.loc[prices["symbol"].astype(str).str.zfill(6) == normalized].copy()
    if frame.empty:
        return fetch_remote_stock_daily_history_frame(normalized, limit=limit), "remote-history"
    frame["date"] = pd.to_datetime(frame["date"])
    frame["symbol"] = normalized
    return ensure_ohlc_columns(frame).sort_values("date").tail(limit).reset_index(drop=True), "local-history"


def fetch_index_daily_history_frame(symbol: str, limit: int) -> tuple[pd.DataFrame, str]:
    normalized = normalize_index_symbol(symbol)
    if normalized == "sh000001":
        frame = ak.stock_zh_index_daily(symbol="sh000001").copy()
        frame["date"] = pd.to_datetime(frame["date"])
        frame["symbol"] = normalized
        frame["name"] = get_index_display_name(normalized)
        frame["pool"] = "index"
        return ensure_ohlc_columns(frame).sort_values("date").tail(limit).reset_index(drop=True), "index-remote"
    frame = ak.index_zh_a_hist(
        symbol=normalized.removeprefix("sh").removeprefix("sz"),
        period="daily",
        start_date="19700101",
        end_date="22220101",
    ).copy()
    frame = normalize_akshare_hist_frame(frame)
    frame["date"] = pd.to_datetime(frame["date"])
    frame["symbol"] = normalized
    frame["name"] = get_index_display_name(normalized)
    frame["pool"] = "index"
    return ensure_ohlc_columns(frame).sort_values("date").tail(limit).reset_index(drop=True), "index-remote"


def to_sina_symbol(symbol: str) -> str:
    raw = str(symbol).lower()
    if raw.startswith(("sh", "sz", "bj")):
        return raw
    if raw in {"sh000001", "000001.sh", "000001.xshg", "000001_index"}:
        return "sh000001"
    normalized = normalize_symbol(raw)
    if normalized.startswith(("600", "601", "603", "605", "688")):
        return f"sh{normalized}"
    return f"sz{normalized}"


def fetch_minute_history_frame(symbol: str, period: str, limit: int) -> pd.DataFrame:
    minute_period = str(HISTORY_PERIOD_CONFIG[period]["minute_period"])
    limit = clamp_history_limit(period, limit)
    if is_index_symbol(symbol):
        frame = ak.stock_zh_a_minute(symbol=to_sina_symbol(symbol), period=minute_period, adjust="").copy()
        frame = normalize_akshare_minute_frame(frame)
        frame["symbol"] = normalize_index_symbol(symbol)
        frame["name"] = get_index_display_name(symbol)
        frame["pool"] = "index"
        return frame.tail(limit).reset_index(drop=True)
    normalized = normalize_symbol(symbol)
    try:
        frame = ak.stock_zh_a_minute(symbol=to_sina_symbol(normalized), period=minute_period, adjust="").copy()
        frame = normalize_akshare_minute_frame(frame)
    except Exception:
        frame = ak.stock_zh_a_hist_min_em(symbol=normalized, period=minute_period, adjust="").copy()
        frame = normalize_akshare_minute_frame(frame)
    frame["symbol"] = normalized
    frame["pool"] = "minute"
    return frame.tail(limit).reset_index(drop=True)


def fetch_multi_day_minute_history_frame(symbol: str, period: str, limit: int) -> pd.DataFrame:
    days = int(HISTORY_PERIOD_CONFIG[period]["days"])
    frame = fetch_minute_history_frame(symbol, period="1m", limit=max(limit, days * 240))
    if frame.empty:
        return frame
    frame["date"] = pd.to_datetime(frame["date"])
    recent_days = sorted(frame["date"].dt.normalize().unique())[-days:]
    frame = frame.loc[frame["date"].dt.normalize().isin(recent_days)].copy()
    return frame.sort_values("date").tail(clamp_history_limit(period, limit)).reset_index(drop=True)


def get_local_history_snapshot(symbol: str) -> dict[str, Any]:
    if is_index_symbol(symbol):
        return {"has_local_history": False, "latest_date": None, "rows": 0}
    normalized = normalize_symbol(symbol)
    prices = get_local_price_frame(prefer_real=True).copy()
    prices["symbol"] = prices["symbol"].astype(str).str.zfill(6)
    frame = prices.loc[prices["symbol"] == normalized].sort_values("date")
    if frame.empty:
        return {"has_local_history": False, "latest_date": None, "rows": 0}
    return {
        "has_local_history": True,
        "latest_date": pd.Timestamp(frame["date"].iloc[-1]).strftime("%Y-%m-%d"),
        "rows": int(len(frame)),
    }


def get_history_cache_path(symbol: str, period: str) -> Path:
    normalized_symbol = normalize_index_symbol(symbol) if is_index_symbol(symbol) else normalize_symbol(symbol)
    safe_period = normalize_history_period(period)
    return HISTORY_CACHE_DIR / f"{normalized_symbol}_{safe_period}.json"


def read_history_cache(symbol: str, period: str) -> dict | None:
    return read_json_file(get_history_cache_path(symbol, period), default_factory=lambda: None)


def write_history_cache(payload: dict) -> dict:
    return write_json_file(get_history_cache_path(payload["symbol"], payload["period"]), payload)


def build_history_payload(symbol: str, period: str = "day", limit: int | None = None) -> dict:
    normalized_period = normalize_history_period(period)
    resolved_limit = resolve_history_limit(normalized_period, limit)
    config = HISTORY_PERIOD_CONFIG[normalized_period]
    normalized_symbol = normalize_index_symbol(symbol) if is_index_symbol(symbol) else normalize_symbol(symbol)
    warnings: list[str] = []
    local_snapshot = get_local_history_snapshot(symbol)
    cached_payload = read_history_cache(normalized_symbol, normalized_period)
    source = "unknown"
    source_label = "未知来源"

    try:
        if config["mode"] == "daily":
            if is_index_symbol(symbol):
                frame, source = fetch_index_daily_history_frame(symbol, max(resolved_limit * 3, resolved_limit))
                source_label = "指数远程日线"
            else:
                frame, source = fetch_stock_daily_history_frame(symbol, max(resolved_limit * 3, resolved_limit))
                source_label = "本地历史数据" if source == "local-history" else "远程补抓日线"
                if source != "local-history":
                    warnings.append("本地历史缺失，已回退到远程抓取。")
            if config.get("resample_rule"):
                frame = resample_ohlc_frame(frame, str(config["resample_rule"]))
            items = format_history_frame(frame, limit=resolved_limit)
        elif config["mode"] == "minute":
            frame = fetch_minute_history_frame(symbol, normalized_period, resolved_limit)
            items = format_minute_history_frame(frame, limit=resolved_limit)
            source = "remote-minute"
            source_label = "远程分钟线"
        else:
            frame = fetch_multi_day_minute_history_frame(symbol, normalized_period, resolved_limit)
            items = format_minute_history_frame(frame, limit=resolved_limit)
            source = "remote-minute-window"
            source_label = "远程多日分时"
    except Exception as exc:
        if cached_payload and cached_payload.get("items"):
            cached_payload["items"] = list(cached_payload.get("items", []))[-resolved_limit:]
            cached_payload["limit"] = resolved_limit
            cached_payload["message"] = f"实时抓取失败，已回退到历史缓存：{exc}"
            meta = dict(cached_payload.get("meta") or {})
            meta.update(
                {
                    "updated_at": now_iso(),
                    "stale": True,
                    "status": "stale-cache",
                    "warnings": [*(meta.get("warnings") or []), str(exc)],
                }
            )
            cached_payload["meta"] = meta
            return cached_payload
        raise

    latest_name = items[-1].get("name") if items else (get_index_display_name(symbol) if is_index_symbol(symbol) else None)
    payload = {
        "symbol": normalized_symbol,
        "period": normalized_period,
        "limit": resolved_limit,
        "name": latest_name,
        "items": items,
        "message": "历史数据已更新" if not warnings else "历史数据已加载，包含回退信息",
        "availability": {
            **local_snapshot,
            "history_status": "index" if is_index_symbol(symbol) else ("local" if local_snapshot["has_local_history"] else "remote"),
            "can_fetch_remote": True,
        },
        "meta": {
            "source": source,
            "source_label": source_label,
            "updated_at": now_iso(),
            "as_of": (items[-1].get("datetime") or items[-1].get("date")) if items else None,
            "stale": False,
            "status": "fresh" if not warnings else "degraded",
            "warnings": warnings,
        },
    }
    write_history_cache(payload)
    return payload


def get_realtime_quotes(symbols: list[str], *, return_error: bool = False) -> dict[str, dict] | tuple[dict[str, dict], str | None]:
    quote_client = get_quote_client()
    normalized = [normalize_symbol(symbol) for symbol in symbols]
    try:
        raw = quote_client.stocks(normalized)
    except Exception as exc:
        if return_error:
            return {}, str(exc)
        return {}
    payload: dict[str, dict] = {}
    for symbol in normalized:
        item = raw.get(symbol)
        if not item:
            continue
        payload[symbol] = {
            "symbol": symbol,
            "name": item.get("name"),
            "open": safe_float(item.get("open")),
            "pre_close": safe_float(item.get("close")),
            "price": safe_float(item.get("now")),
            "high": safe_float(item.get("high")),
            "low": safe_float(item.get("low")),
            "volume": safe_float(item.get("turnover")),
            "amount": safe_float(item.get("volume")),
            "bid": safe_float(item.get("buy")),
            "ask": safe_float(item.get("sell")),
            "date": item.get("date"),
            "time": item.get("time"),
        }
    if return_error:
        return payload, None
    return payload


@lru_cache(maxsize=1)
def get_all_stock_catalog() -> pd.DataFrame:
    cached_payload = read_json_file(STOCK_CATALOG_CACHE_PATH, default_factory=lambda: {"items": []}) or {"items": []}
    try:
        catalog = ak.stock_info_a_code_name().copy()
        catalog["code"] = catalog["code"].astype(str).str.zfill(6)
        catalog["name"] = catalog["name"].fillna("")
        records = catalog[["code", "name"]].drop_duplicates(subset=["code"]).to_dict(orient="records")
        write_json_file(STOCK_CATALOG_CACHE_PATH, {"updated_at": now_iso(), "items": records})
        return pd.DataFrame(records)
    except Exception:
        records = cached_payload.get("items") or []
        if not records:
            raise
        frame = pd.DataFrame(records)
        frame["code"] = frame["code"].astype(str).str.zfill(6)
        frame["name"] = frame["name"].fillna("")
        return frame[["code", "name"]]


def search_symbols(query: str, limit: int = 12) -> list[dict]:
    keyword = query.strip().lower()
    if not keyword:
        return []

    prices = get_local_price_frame(prefer_real=True).copy()
    prices["symbol"] = prices["symbol"].astype(str).str.zfill(6)
    latest = prices.sort_values(["symbol", "date"]).groupby("symbol", as_index=False).tail(1)
    latest["name"] = latest["name"].fillna("")
    latest["symbol_lower"] = latest["symbol"].str.lower()
    latest["name_lower"] = latest["name"].str.lower()
    matches = latest.loc[
        latest["symbol_lower"].str.contains(keyword, regex=False)
        | latest["name_lower"].str.contains(keyword, regex=False)
    ].copy()

    records = [
        {
            "symbol": row["symbol"],
            "name": row["name"],
            "kind": "stock",
            "latest_date": pd.Timestamp(row["date"]).strftime("%Y-%m-%d"),
            "history_status": "local",
            "history_label": "本地历史",
            "has_local_history": True,
            "can_remote_history": True,
        }
        for row in matches.sort_values(["symbol"]).head(limit).to_dict(orient="records")
    ]

    try:
        catalog = get_all_stock_catalog().copy()
        catalog["code_lower"] = catalog["code"].str.lower()
        catalog["name_lower"] = catalog["name"].str.lower()
        market_matches = catalog.loc[
            catalog["code_lower"].str.contains(keyword, regex=False)
            | catalog["name_lower"].str.contains(keyword, regex=False)
        ].copy()
        records.extend(
            {
                "symbol": row["code"],
                "name": row["name"],
                "kind": "stock",
                "latest_date": None,
                "history_status": "remote",
                "history_label": "远程可抓取",
                "has_local_history": False,
                "can_remote_history": True,
            }
            for row in market_matches.sort_values(["code"]).head(limit * 3).to_dict(orient="records")
        )
    except Exception:
        pass

    index_aliases = [
        {"symbol": "sh000001", "name": "上证指数", "kind": "index", "aliases": ["上证", "沪指", "sh000001"]},
    ]
    for item in index_aliases:
        alias_text = " ".join(item.get("aliases", [])) + f" {item['symbol']} {item['name']}"
        if keyword in alias_text.lower():
            records.insert(
                0,
                {
                    "symbol": item["symbol"],
                    "name": item["name"],
                    "kind": item["kind"],
                    "latest_date": None,
                    "history_status": "index",
                    "history_label": "指数历史",
                    "has_local_history": False,
                    "can_remote_history": True,
                },
            )

    deduped: list[dict] = []
    seen: set[str] = set()
    for item in records:
        key = f"{item.get('kind', 'stock')}:{item['symbol']}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    custom_watchlist = list_custom_watchlist()
    favorite_keys = {f"{item['kind']}:{item['symbol']}" for item in custom_watchlist.get("items", [])}
    for item in deduped:
        normalized_symbol = normalize_index_symbol(item["symbol"]) if item.get("kind") == "index" or is_index_symbol(item["symbol"]) else normalize_symbol(item["symbol"])
        item["is_favorite"] = f"{item.get('kind', 'stock')}:{normalized_symbol}" in favorite_keys
    return deduped[:limit]


def ensure_watchlist_storage() -> None:
    CUSTOM_WATCHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CUSTOM_WATCHLIST_PATH.exists():
        CUSTOM_WATCHLIST_PATH.write_text(json.dumps({"updated_at": None, "items": []}, ensure_ascii=False, indent=2), encoding="utf-8")


def read_custom_watchlist() -> dict:
    ensure_watchlist_storage()
    try:
        payload = json.loads(CUSTOM_WATCHLIST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = {"updated_at": None, "items": []}
    if not isinstance(payload, dict):
        payload = {"updated_at": None, "items": []}
    items = payload.get("items")
    if not isinstance(items, list):
        items = []
    return {"updated_at": payload.get("updated_at"), "items": items}


def write_custom_watchlist(items: list[dict]) -> dict:
    payload = {"updated_at": now_iso(), "items": items}
    temp_path = Path(f"{CUSTOM_WATCHLIST_PATH}.tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(CUSTOM_WATCHLIST_PATH)
    return payload


def normalize_watchlist_item(symbol: str, name: str | None = None, kind: str = "stock", added_at: str | None = None) -> dict:
    normalized_kind = (kind or "stock").strip().lower()
    if normalized_kind == "index" or is_index_symbol(symbol):
        normalized_symbol = normalize_index_symbol(symbol)
        resolved_name = (name or "").strip() or get_index_display_name(normalized_symbol)
        normalized_kind = "index"
    else:
        normalized_symbol = normalize_symbol(symbol)
        resolved_name = (name or "").strip()
    return {
        "symbol": normalized_symbol,
        "name": resolved_name,
        "kind": normalized_kind,
        "added_at": (added_at or "").strip() or now_iso(),
    }


def list_custom_watchlist() -> dict:
    payload = read_custom_watchlist()
    return {
        "updated_at": payload.get("updated_at"),
        "items": [
            normalize_watchlist_item(item.get("symbol", ""), item.get("name"), item.get("kind", "stock"), item.get("added_at"))
            for item in payload.get("items", [])
            if item.get("symbol")
        ],
    }


def add_custom_watchlist_item(symbol: str, name: str | None = None, kind: str = "stock") -> dict:
    payload = read_custom_watchlist()
    normalized_item = normalize_watchlist_item(symbol, name=name, kind=kind)
    items = [
        normalize_watchlist_item(item.get("symbol", ""), item.get("name"), item.get("kind", "stock"), item.get("added_at"))
        for item in payload.get("items", [])
        if item.get("symbol")
    ]
    for item in items:
        if item["symbol"] == normalized_item["symbol"] and item["kind"] == normalized_item["kind"]:
            if normalized_item["name"] and item.get("name") != normalized_item["name"]:
                item["name"] = normalized_item["name"]
                payload = write_custom_watchlist(items)
            return {"item": item, "updated_at": payload.get("updated_at"), "created": False}
    items.append(normalized_item)
    payload = write_custom_watchlist(items)
    return {"item": normalized_item, "updated_at": payload.get("updated_at"), "created": True}


def delete_custom_watchlist_item(symbol: str, kind: str | None = None) -> dict:
    payload = read_custom_watchlist()
    normalized_kind = (kind or ("index" if is_index_symbol(symbol) else "stock")).strip().lower()
    normalized_symbol = normalize_index_symbol(symbol) if normalized_kind == "index" or is_index_symbol(symbol) else normalize_symbol(symbol)
    items = [
        normalize_watchlist_item(item.get("symbol", ""), item.get("name"), item.get("kind", "stock"), item.get("added_at"))
        for item in payload.get("items", [])
        if item.get("symbol")
    ]
    remaining = [item for item in items if not (item["symbol"] == normalized_symbol and item["kind"] == normalized_kind)]
    removed = len(remaining) != len(items)
    payload = write_custom_watchlist(remaining) if removed else payload
    return {"removed": removed, "symbol": normalized_symbol, "kind": normalized_kind, "updated_at": payload.get("updated_at")}


def get_watchlist_latest_close(symbols: list[str]) -> dict[str, dict]:
    normalized = [normalize_symbol(symbol) for symbol in symbols]
    prices = get_local_price_frame(prefer_real=True).copy()
    prices["symbol"] = prices["symbol"].astype(str).str.zfill(6)
    frame = prices.loc[prices["symbol"].isin(normalized)].sort_values(["symbol", "date"])
    frame["prev_close"] = frame.groupby("symbol")["close"].shift(1)
    latest = frame.groupby("symbol", as_index=False).tail(1)
    payload: dict[str, dict] = {}
    for row in latest.to_dict(orient="records"):
        prev_close = row.get("prev_close")
        change_pct = None
        if pd.notna(prev_close) and float(prev_close) != 0:
            change_pct = round((float(row["close"]) / float(prev_close) - 1) * 100, 2)
        payload[row["symbol"]] = {
            "symbol": row["symbol"],
            "name": row["name"],
            "close": round(float(row["close"]), 2),
            "prev_close": round(float(prev_close), 2) if pd.notna(prev_close) else None,
            "change_pct": change_pct,
            "date": pd.Timestamp(row["date"]).strftime("%Y-%m-%d"),
            "volume": int(float(row["volume"])) if pd.notna(row.get("volume")) else None,
            "pool": row.get("pool", "sample"),
        }
    return payload


def merge_live_and_close(symbols: list[str]) -> list[dict]:
    latest_close = get_watchlist_latest_close(symbols)
    live_quotes, live_error = get_realtime_quotes(symbols, return_error=True)
    merged: list[dict] = []
    for symbol in [normalize_symbol(item) for item in symbols]:
        close_info = latest_close.get(symbol, {})
        live = live_quotes.get(symbol)
        if live:
            pre_close = live.get("pre_close") or close_info.get("close")
            price = live.get("price") or close_info.get("close")
            change_pct = None
            if pre_close not in (None, 0) and price is not None:
                change_pct = round((float(price) / float(pre_close) - 1) * 100, 2)
            merged.append(
                {
                    "symbol": symbol,
                    "name": live.get("name") or close_info.get("name"),
                    "mode": "live",
                    "trade_date": live.get("date") or close_info.get("date"),
                    "trade_time": live.get("time"),
                    "price": round(float(price), 2) if price is not None else None,
                    "pre_close": round(float(pre_close), 2) if pre_close is not None else None,
                    "change_pct": change_pct,
                    "high": live.get("high"),
                    "low": live.get("low"),
                    "open": live.get("open"),
                    "volume": live.get("volume"),
                    "amount": live.get("amount"),
                    "fallback_close": close_info.get("close"),
                    "quote_status": "live",
                    "quote_warning": None,
                }
            )
            continue
        if close_info:
            merged.append(
                {
                    "symbol": symbol,
                    "name": close_info.get("name"),
                    "mode": "close",
                    "trade_date": close_info.get("date"),
                    "trade_time": "15:00:00",
                    "price": close_info.get("close"),
                    "pre_close": close_info.get("prev_close"),
                    "change_pct": close_info.get("change_pct"),
                    "high": None,
                    "low": None,
                    "open": None,
                    "volume": close_info.get("volume"),
                    "amount": None,
                    "fallback_close": close_info.get("close"),
                    "quote_status": "fallback-close",
                    "quote_warning": live_error,
                }
            )
    return merged


def build_watch_snapshot(symbols: list[str]) -> dict:
    items = merge_live_and_close(symbols)
    only_live = bool(items) and all(item.get("quote_status") == "live" for item in items)
    return {
        "items": items,
        "meta": {
            "source": "live" if only_live else "mixed",
            "source_label": "实时快照" if only_live else "实时/收盘混合快照",
            "updated_at": now_iso(),
            "fallback_count": sum(1 for item in items if item.get("quote_status") != "live"),
            "warnings": [item.get("quote_warning") for item in items if item.get("quote_warning")],
        },
    }


def get_custom_watchlist_snapshot() -> dict:
    payload = list_custom_watchlist()
    items = payload.get("items", [])
    if not items:
        return {
            "updated_at": payload.get("updated_at"),
            "items": [],
            "meta": {"source": "empty", "source_label": "暂无自选", "updated_at": now_iso(), "warnings": []},
        }
    stock_symbols = [item["symbol"] for item in items if item.get("kind") == "stock"]
    stock_quote_map = {entry["symbol"]: entry for entry in merge_live_and_close(stock_symbols)} if stock_symbols else {}
    merged: list[dict] = []
    for item in items:
        symbol = item["symbol"]
        kind = item.get("kind", "stock")
        if kind == "stock" and symbol in stock_quote_map:
            merged.append({**item, **stock_quote_map[symbol]})
            continue
        latest_items = build_history_payload(symbol, period="day", limit=2).get("items", [])
        latest = latest_items[-1] if latest_items else {}
        merged.append(
            {
                **item,
                "symbol": symbol,
                "name": latest.get("name") or item.get("name") or symbol,
                "mode": "close",
                "trade_date": latest.get("date"),
                "trade_time": "15:00:00" if latest else None,
                "price": latest.get("close"),
                "pre_close": latest.get("prev_close"),
                "change_pct": latest.get("change_pct"),
                "high": latest.get("high"),
                "low": latest.get("low"),
                "open": latest.get("open"),
                "volume": latest.get("volume"),
                "amount": None,
                "fallback_close": latest.get("close"),
                "quote_status": "history",
                "quote_warning": None,
            }
        )
    return {
        "updated_at": payload.get("updated_at"),
        "items": merged,
        "meta": {"source": "mixed", "source_label": "自选快照", "updated_at": now_iso(), "warnings": []},
    }


def get_watchlist_history(symbol: str, limit: int = 60) -> list[dict]:
    payload = build_history_payload(symbol, period="day", limit=limit)
    return payload["items"]


def get_intraday_frame(symbol: str, trade_date: str, period: str = "1") -> pd.DataFrame:
    prefixed_symbol = to_sina_symbol(symbol)
    frame = ak.stock_zh_a_minute(symbol=prefixed_symbol, period=period, adjust="").copy()
    frame = normalize_akshare_minute_frame(frame)
    frame["day"] = frame["date"]
    return frame.loc[frame["day"].dt.strftime("%Y-%m-%d") == trade_date].sort_values("day")


def format_intraday_change_points(frame: pd.DataFrame, previous_close: float) -> list[dict]:
    if frame.empty or previous_close == 0:
        return []
    records: list[dict] = []
    for row in frame.to_dict(orient="records"):
        price = safe_float(row.get("close"))
        if price is None:
            continue
        records.append(
            {
                "time": pd.Timestamp(row["day"]).strftime("%H:%M"),
                "price": round(float(price), 2),
                "change_pct": round((float(price) / float(previous_close) - 1) * 100, 2),
            }
        )
    return records


def build_estimated_intraday_points(day_item: dict, previous_close: float) -> list[dict]:
    if previous_close == 0:
        return []
    open_price = safe_float(day_item.get("open")) or safe_float(day_item.get("close")) or previous_close
    high_price = safe_float(day_item.get("high")) or safe_float(day_item.get("close")) or open_price
    low_price = safe_float(day_item.get("low")) or safe_float(day_item.get("close")) or open_price
    close_price = safe_float(day_item.get("close")) or open_price
    rising = close_price >= open_price
    anchors = [("09:30", open_price), ("10:30", low_price if rising else high_price), ("13:30", high_price if rising else low_price), ("15:00", close_price)]
    return [{"time": label, "price": round(float(price), 2), "change_pct": round((float(price) / float(previous_close) - 1) * 100, 2)} for label, price in anchors]


def get_intraday_change_history(symbol: str, trade_date: str) -> dict:
    normalized_date = pd.Timestamp(trade_date).strftime("%Y-%m-%d")
    daily_items = get_watchlist_history(symbol, limit=400)
    target_index = next((idx for idx, item in enumerate(daily_items) if item.get("date") == normalized_date), None)
    if target_index is None:
        return {
            "symbol": str(symbol),
            "date": normalized_date,
            "mode": "unavailable",
            "resolution": None,
            "estimated": False,
            "baseline": None,
            "name": None,
            "message": "未找到该交易日的历史数据",
            "items": [],
            "meta": {"status": "missing", "updated_at": now_iso(), "warnings": ["history date unavailable"]},
        }
    day_item = daily_items[target_index]
    previous_close = day_item.get("prev_close")
    if previous_close in (None, 0) and target_index > 0:
        previous_close = daily_items[target_index - 1].get("close")
    if previous_close in (None, 0):
        return {
            "symbol": str(symbol),
            "date": normalized_date,
            "mode": "unavailable",
            "resolution": None,
            "estimated": False,
            "baseline": None,
            "name": day_item.get("name"),
            "message": "缺少前收数据，无法绘制当天涨幅线",
            "items": [],
            "meta": {"status": "missing-baseline", "updated_at": now_iso(), "warnings": ["previous close unavailable"]},
        }
    last_error: str | None = None
    for period, resolution in (("1", "1分钟"), ("5", "5分钟")):
        try:
            frame = get_intraday_frame(symbol, normalized_date, period=period)
            points = format_intraday_change_points(frame, float(previous_close))
            if points:
                return {
                    "symbol": str(symbol),
                    "date": normalized_date,
                    "mode": "intraday",
                    "resolution": resolution,
                    "estimated": False,
                    "baseline": round(float(previous_close), 2),
                    "name": day_item.get("name"),
                    "message": f"已切换到 {normalized_date} 的{resolution}涨幅线",
                    "items": points,
                    "meta": {"status": "fresh", "updated_at": now_iso(), "warnings": []},
                }
        except Exception as exc:
            last_error = str(exc)
    estimated_points = build_estimated_intraday_points(day_item, float(previous_close))
    message = "分钟级分时不可用，已回退为基于当日 OHLC 的估算涨幅线"
    if last_error:
        message = f"{message}：{last_error}"
    return {
        "symbol": str(symbol),
        "date": normalized_date,
        "mode": "estimated",
        "resolution": "估算",
        "estimated": True,
        "baseline": round(float(previous_close), 2),
        "name": day_item.get("name"),
        "message": message,
        "items": estimated_points,
        "meta": {"status": "estimated", "updated_at": now_iso(), "warnings": [last_error] if last_error else []},
    }
