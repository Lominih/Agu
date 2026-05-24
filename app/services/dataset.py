from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import akshare as ak
import numpy as np
import pandas as pd

from app.core.config import DEFAULT_SAMPLE_SYMBOLS, INDEX_POOLS


FEATURE_COLUMNS = [
    "ret_5",
    "ret_10",
    "volatility_10",
    "price_vs_ma10",
    "price_vs_ma20",
    "volume_ratio_5",
]


def generate_sample_dataset(output_path: Path) -> pd.DataFrame:
    """Generate a local sample dataset so the app can run without remote data."""
    rng = np.random.default_rng(7)
    dates = pd.bdate_range("2024-01-02", periods=220)
    rows: list[dict[str, Any]] = []

    for idx, (symbol, name) in enumerate(DEFAULT_SAMPLE_SYMBOLS):
        base_price = 20 + idx * 8
        drift = 0.0007 + idx * 0.00003
        noise = rng.normal(drift, 0.018, size=len(dates))
        prices = base_price * np.cumprod(1 + noise)
        volumes = rng.integers(2_000_000, 20_000_000, size=len(dates))

        for date, close, volume in zip(dates, prices, volumes, strict=True):
            rows.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "name": name,
                    "close": round(float(close), 2),
                    "volume": int(volume),
                    "source": "sample",
                    "pool": "sample",
                }
            )

    df = pd.DataFrame(rows).sort_values(["symbol", "date"]).reset_index(drop=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return df


def load_index_constituents(pool: str = "hs300") -> list[tuple[str, str]]:
    if pool == "all":
        frames = [ak.index_stock_cons_csindex(symbol=meta["symbol"]) for meta in INDEX_POOLS.values()]
        cons_df = pd.concat(frames, ignore_index=True)
    else:
        meta = INDEX_POOLS.get(pool, INDEX_POOLS["hs300"])
        cons_df = ak.index_stock_cons_csindex(symbol=meta["symbol"])

    cons_df = cons_df.rename(columns={"成分券代码": "symbol", "成分券名称": "name"})
    cons_df["symbol"] = cons_df["symbol"].astype(str).str.zfill(6)
    cons_df = cons_df[["symbol", "name"]].drop_duplicates(subset=["symbol"]).reset_index(drop=True)
    return list(cons_df.itertuples(index=False, name=None))


def _fetch_one_symbol(symbol: str, name: str, start_ts: pd.Timestamp, pool: str) -> pd.DataFrame:
    exchange_symbol = ("sh" if symbol.startswith(("600", "601", "603", "605", "688")) else "sz") + symbol
    hist = ak.stock_zh_a_daily(symbol=exchange_symbol, adjust="qfq")
    frame = hist[["date", "close", "volume"]].copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.loc[frame["date"] >= start_ts].reset_index(drop=True)
    frame["symbol"] = symbol
    frame["name"] = name
    frame["source"] = "akshare"
    frame["pool"] = pool
    return frame


def fetch_real_dataset(
    output_path: Path,
    symbols: list[tuple[str, str]] | None = None,
    start_date: str = "2023-01-01",
    pool: str = "hs300",
) -> pd.DataFrame:
    """Fetch A-share daily bars from AKShare for an index-based symbol universe."""
    symbol_list = symbols or load_index_constituents(pool)
    start_ts = pd.Timestamp(start_date)
    frames: list[pd.DataFrame] = []
    errors: list[str] = []
    max_workers = min(8, max(4, len(symbol_list) // 60 or 4))

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(_fetch_one_symbol, symbol, name, start_ts, pool): (symbol, name)
            for symbol, name in symbol_list
        }
        for future in as_completed(future_map):
            symbol, name = future_map[future]
            try:
                frame = future.result()
                if not frame.empty:
                    frames.append(frame)
            except Exception as exc:
                errors.append(f"{symbol} {name}: {exc}")

    if not frames:
        raise RuntimeError(f"未能抓取到任何真实A股数据。最近错误: {errors[:3]}")

    df = pd.concat(frames, ignore_index=True).sort_values(["symbol", "date"]).reset_index(drop=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return df


def load_price_data(csv_path: Path, source: str = "sample") -> pd.DataFrame:
    if not csv_path.exists():
        if source == "real":
            return fetch_real_dataset(csv_path)
        return generate_sample_dataset(csv_path)

    df = pd.read_csv(csv_path, parse_dates=["date"], dtype={"symbol": str, "name": str, "source": str, "pool": str})
    if df.empty:
        if source == "real":
            return fetch_real_dataset(csv_path)
        return generate_sample_dataset(csv_path)

    df["symbol"] = df["symbol"].astype(str).str.zfill(6)
    if "source" not in df.columns:
        df["source"] = source
    if "pool" not in df.columns:
        df["pool"] = "sample" if source == "sample" else "hs300"
    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy().sort_values(["symbol", "date"]).reset_index(drop=True)
    grouped = working.groupby("symbol", group_keys=False)

    working["ret_5"] = grouped["close"].pct_change(5)
    working["ret_10"] = grouped["close"].pct_change(10)
    working["volatility_10"] = grouped["close"].pct_change().rolling(10).std().reset_index(level=0, drop=True)
    working["ma_10"] = grouped["close"].rolling(10).mean().reset_index(level=0, drop=True)
    working["ma_20"] = grouped["close"].rolling(20).mean().reset_index(level=0, drop=True)
    working["volume_ma_5"] = grouped["volume"].rolling(5).mean().reset_index(level=0, drop=True)

    working["price_vs_ma10"] = working["close"] / working["ma_10"] - 1
    working["price_vs_ma20"] = working["close"] / working["ma_20"] - 1
    working["volume_ratio_5"] = working["volume"] / working["volume_ma_5"]

    working["future_return_5"] = grouped["close"].shift(-5) / working["close"] - 1
    working = working.dropna(subset=FEATURE_COLUMNS + ["future_return_5"]).reset_index(drop=True)
    return working


def latest_snapshot(feature_df: pd.DataFrame) -> pd.DataFrame:
    latest_date = feature_df["date"].max()
    snapshot = feature_df.loc[feature_df["date"] == latest_date].copy()
    return snapshot.sort_values("symbol").reset_index(drop=True)
