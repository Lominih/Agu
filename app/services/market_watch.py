from __future__ import annotations

from functools import lru_cache

import easyquotation
import pandas as pd

from app.services.dataset import load_price_data
from app.core.config import REAL_DATA_PATH, DEFAULT_DATA_PATH


@lru_cache(maxsize=1)
def get_quote_client():
    return easyquotation.use("sina")


def normalize_symbol(symbol: str) -> str:
    return str(symbol).zfill(6)


def get_realtime_quotes(symbols: list[str]) -> dict[str, dict]:
    quote_client = get_quote_client()
    normalized = [normalize_symbol(symbol) for symbol in symbols]
    raw = quote_client.stocks(normalized)
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

    return payload


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


def get_watchlist_history(symbol: str, limit: int = 60) -> list[dict]:
    normalized = normalize_symbol(symbol)
    prices = get_local_price_frame(prefer_real=True)
    frame = prices.loc[prices["symbol"].astype(str).str.zfill(6) == normalized].copy()
    if frame.empty:
        return []

    frame = frame.sort_values("date").tail(limit)
    frame["prev_close"] = frame["close"].shift(1)
    frame["change_pct"] = (frame["close"] / frame["prev_close"] - 1) * 100
    records = []

    for row in frame.to_dict(orient="records"):
        records.append(
            {
                "date": pd.Timestamp(row["date"]).strftime("%Y-%m-%d"),
                "close": round(float(row["close"]), 2),
                "volume": int(float(row["volume"])),
                "change_pct": None if pd.isna(row["change_pct"]) else round(float(row["change_pct"]), 2),
                "name": row["name"],
                "pool": row.get("pool", "sample"),
            }
        )

    return records


def get_watchlist_latest_close(symbols: list[str]) -> dict[str, dict]:
    normalized = [normalize_symbol(symbol) for symbol in symbols]
    prices = get_local_price_frame(prefer_real=True).copy()
    prices["symbol"] = prices["symbol"].astype(str).str.zfill(6)
    frame = prices.loc[prices["symbol"].isin(normalized)].sort_values(["symbol", "date"])
    latest = frame.groupby("symbol", as_index=False).tail(1)
    payload: dict[str, dict] = {}

    for row in latest.to_dict(orient="records"):
        payload[row["symbol"]] = {
            "symbol": row["symbol"],
            "name": row["name"],
            "close": round(float(row["close"]), 2),
            "date": pd.Timestamp(row["date"]).strftime("%Y-%m-%d"),
            "volume": int(float(row["volume"])),
            "pool": row.get("pool", "sample"),
        }

    return payload


def merge_live_and_close(symbols: list[str]) -> list[dict]:
    latest_close = get_watchlist_latest_close(symbols)
    live_quotes = get_realtime_quotes(symbols)
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
                    "pre_close": None,
                    "change_pct": None,
                    "high": None,
                    "low": None,
                    "open": None,
                    "volume": close_info.get("volume"),
                    "amount": None,
                    "fallback_close": close_info.get("close"),
                }
            )

    return merged
