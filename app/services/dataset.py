# -*- coding: utf-8 -*-
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import akshare as ak
import numpy as np
import pandas as pd

from app.core.config import DATA_HEALTH_PATH, DATASET_META_PATH, DEFAULT_SAMPLE_SYMBOLS, INDEX_POOLS
from app.services.state_store import read_json_file, write_json_file


FEATURE_COLUMNS = [
    "ret_5",
    "ret_10",
    "ret_20",
    "volatility_10",
    "volatility_20",
    "price_vs_ma10",
    "price_vs_ma20",
    "ma_gap_10_20",
    "volume_ratio_5",
    "volume_ratio_20",
    "drawdown_20",
    "momentum_spread_5_20",
]

CSI_CONS_COLUMNS = {
    "成分券代码": "symbol",
    "成分券名称": "name",
}


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
    write_dataset_meta(
        {
            "source": "sample",
            "pool": "sample",
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "rows": int(len(df)),
            "symbols": int(df["symbol"].nunique()),
            "latest_date": pd.Timestamp(df["date"].max()).strftime("%Y-%m-%d"),
        }
    )
    return df


def load_index_constituents(pool: str = "hs300") -> list[tuple[str, str]]:
    if pool == "all":
        frames = [ak.index_stock_cons_csindex(symbol=meta["symbol"]) for meta in INDEX_POOLS.values()]
        cons_df = pd.concat(frames, ignore_index=True)
    else:
        meta = INDEX_POOLS.get(pool, INDEX_POOLS["hs300"])
        cons_df = ak.index_stock_cons_csindex(symbol=meta["symbol"])

    cons_df = cons_df.rename(columns=CSI_CONS_COLUMNS)
    missing_columns = {"symbol", "name"} - set(cons_df.columns)
    if missing_columns:
        raise RuntimeError(f"指数成分股字段缺失: {sorted(missing_columns)}")

    cons_df["symbol"] = cons_df["symbol"].astype(str).str.zfill(6)
    cons_df = cons_df[["symbol", "name"]].drop_duplicates(subset=["symbol"]).reset_index(drop=True)
    return list(cons_df.itertuples(index=False, name=None))


def _fetch_one_symbol(symbol: str, name: str, start_ts: pd.Timestamp, pool: str) -> pd.DataFrame:
    exchange_symbol = ("sh" if symbol.startswith(("600", "601", "603", "605", "688")) else "sz") + symbol
    hist = ak.stock_zh_a_daily(
        symbol=exchange_symbol,
        start_date=start_ts.strftime("%Y%m%d"),
        end_date=(pd.Timestamp(datetime.now().date()) + pd.Timedelta(days=1)).strftime("%Y%m%d"),
        adjust="qfq",
    )
    base_columns = ["date", "open", "high", "low", "close", "volume"]
    available_columns = [column for column in base_columns if column in hist.columns]
    frame = hist[available_columns].copy()
    if "amount" in hist.columns:
        frame["amount"] = hist["amount"]
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
    max_workers: int | None = None,
) -> pd.DataFrame:
    """Fetch A-share daily bars from AKShare for an index-based symbol universe."""
    symbol_list = symbols or load_index_constituents(pool)
    start_ts = pd.Timestamp(start_date)
    frames: list[pd.DataFrame] = []
    errors: list[str] = []
    worker_count = max_workers or min(8, max(4, len(symbol_list) // 60 or 4))

    with ProcessPoolExecutor(max_workers=worker_count) as executor:
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
        raise RuntimeError(f"未能抓取到任何真实 A 股数据。最近错误: {errors[:3]}")

    df = pd.concat(frames, ignore_index=True).sort_values(["symbol", "date"]).reset_index(drop=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    write_dataset_meta(
        {
            "source": "akshare",
            "pool": pool,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "rows": int(len(df)),
            "symbols": int(df["symbol"].nunique()),
            "latest_date": pd.Timestamp(df["date"].max()).strftime("%Y-%m-%d"),
        }
    )
    return df


def get_incremental_start_date(existing_path: Path, default_start_date: str = "2023-01-01", overlap_days: int = 20) -> str:
    if not existing_path.exists():
        return default_start_date
    try:
        existing = pd.read_csv(existing_path, usecols=["date"], parse_dates=["date"])
    except Exception:
        return default_start_date
    if existing.empty:
        return default_start_date
    latest_date = pd.Timestamp(existing["date"].max()).normalize()
    incremental_start = latest_date - pd.Timedelta(days=overlap_days)
    default_ts = pd.Timestamp(default_start_date)
    return max(default_ts, incremental_start).strftime("%Y-%m-%d")


def read_dataset_meta() -> dict[str, Any]:
    meta = read_json_file(DATASET_META_PATH, default_factory=lambda: {}) or {}
    if not isinstance(meta, dict):
        return {}
    return meta


def write_dataset_meta(payload: dict[str, Any]) -> dict[str, Any]:
    return write_json_file(DATASET_META_PATH, payload)


def get_data_health_report(df: pd.DataFrame | None = None) -> dict[str, Any]:
    working = df.copy() if df is not None else None
    issues: list[str] = []
    summary = {"rows": 0, "symbols": 0, "latest_date": None, "missing_columns": [], "stale_days": None}

    if working is None:
        meta = read_dataset_meta()
        if meta:
            summary.update(
                {
                    "rows": int(meta.get("rows") or 0),
                    "symbols": int(meta.get("symbols") or 0),
                    "latest_date": meta.get("latest_date"),
                }
            )
        health = {"status": "unknown", "summary": summary, "issues": issues, "updated_at": datetime.now().isoformat(timespec="seconds")}
        write_json_file(DATA_HEALTH_PATH, health)
        return health

    working = working.copy()
    summary["rows"] = int(len(working))
    summary["symbols"] = int(working["symbol"].nunique()) if "symbol" in working.columns else 0
    summary["latest_date"] = pd.Timestamp(working["date"].max()).strftime("%Y-%m-%d") if "date" in working.columns and not working.empty else None

    required_columns = {"date", "symbol", "name", "close", "volume", "source", "pool"}
    missing_columns = sorted(required_columns - set(working.columns))
    summary["missing_columns"] = missing_columns
    if missing_columns:
        issues.append(f"缺少字段: {', '.join(missing_columns)}")

    if "date" in working.columns and not working.empty:
        latest_date = pd.Timestamp(working["date"].max())
        stale_days = (pd.Timestamp(datetime.now().date()) - latest_date.normalize()).days
        summary["stale_days"] = int(stale_days)
        if stale_days > 7:
            issues.append(f"数据已超过 {stale_days} 天未更新")

    if "close" in working.columns and not working.empty:
        close_series = pd.to_numeric(working["close"], errors="coerce")
        if close_series.isna().any():
            issues.append("存在无效收盘价")
        if (close_series <= 0).any():
            issues.append("存在非正价格")

    if "volume" in working.columns and not working.empty:
        volume_series = pd.to_numeric(working["volume"], errors="coerce")
        if (volume_series < 0).any():
            issues.append("存在负成交量")

    if "symbol" in working.columns and "date" in working.columns:
        dup_count = int(working.duplicated(subset=["symbol", "date"]).sum())
        if dup_count:
            issues.append(f"存在 {dup_count} 条重复日线记录")

    status = "healthy" if not issues else "warn"
    health = {"status": status, "summary": summary, "issues": issues, "updated_at": datetime.now().isoformat(timespec="seconds")}
    write_json_file(DATA_HEALTH_PATH, health)
    return health


def incremental_merge_dataset(existing_path: Path, incoming: pd.DataFrame) -> pd.DataFrame:
    if not existing_path.exists():
        return incoming
    try:
        existing = pd.read_csv(existing_path, parse_dates=["date"], dtype={"symbol": str, "name": str, "source": str, "pool": str})
    except Exception:
        return incoming
    merged = pd.concat([existing, incoming], ignore_index=True)
    merged["symbol"] = merged["symbol"].astype(str).str.zfill(6)
    merged = merged.drop_duplicates(subset=["symbol", "date"], keep="last").sort_values(["symbol", "date"]).reset_index(drop=True)
    return merged


def load_price_data(
    csv_path: Path,
    source: str = "sample",
    allow_remote_fetch: bool = True,
) -> pd.DataFrame:
    if not csv_path.exists():
        if source == "real":
            if allow_remote_fetch:
                return fetch_real_dataset(csv_path)
            raise FileNotFoundError(f"真实数据文件不存在: {csv_path}")
        return generate_sample_dataset(csv_path)

    df = pd.read_csv(csv_path, parse_dates=["date"], dtype={"symbol": str, "name": str, "source": str, "pool": str})
    if df.empty:
        if source == "real":
            if allow_remote_fetch:
                return fetch_real_dataset(csv_path)
            raise ValueError(f"真实数据文件为空: {csv_path}")
        return generate_sample_dataset(csv_path)

    df["symbol"] = df["symbol"].astype(str).str.zfill(6)
    if "source" not in df.columns:
        df["source"] = source
    if "pool" not in df.columns:
        df["pool"] = "sample" if source == "sample" else "hs300"
    return df


def _apply_factor_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy().sort_values(["symbol", "date"]).reset_index(drop=True)
    grouped = working.groupby("symbol", group_keys=False)
    close_returns = grouped["close"].pct_change()

    working["ret_5"] = grouped["close"].pct_change(5)
    working["ret_10"] = grouped["close"].pct_change(10)
    working["ret_20"] = grouped["close"].pct_change(20)
    working["volatility_10"] = close_returns.rolling(10).std().reset_index(level=0, drop=True)
    working["volatility_20"] = close_returns.rolling(20).std().reset_index(level=0, drop=True)
    working["ma_10"] = grouped["close"].rolling(10).mean().reset_index(level=0, drop=True)
    working["ma_20"] = grouped["close"].rolling(20).mean().reset_index(level=0, drop=True)
    working["volume_ma_5"] = grouped["volume"].rolling(5).mean().reset_index(level=0, drop=True)
    working["volume_ma_20"] = grouped["volume"].rolling(20).mean().reset_index(level=0, drop=True)
    working["rolling_peak_20"] = grouped["close"].rolling(20).max().reset_index(level=0, drop=True)

    working["price_vs_ma10"] = working["close"] / working["ma_10"] - 1
    working["price_vs_ma20"] = working["close"] / working["ma_20"] - 1
    working["volume_ratio_5"] = working["volume"] / working["volume_ma_5"]
    working["ma_gap_10_20"] = working["ma_10"] / working["ma_20"] - 1
    working["volume_ratio_20"] = working["volume"] / working["volume_ma_20"]
    working["drawdown_20"] = working["close"] / working["rolling_peak_20"] - 1
    working["momentum_spread_5_20"] = working["ret_5"] - working["ret_20"]
    return working


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    working = _apply_factor_pipeline(df)
    grouped = working.groupby("symbol", group_keys=False)
    working["future_return_5"] = grouped["close"].shift(-5) / working["close"] - 1
    working = working.dropna(subset=FEATURE_COLUMNS + ["future_return_5"]).reset_index(drop=True)
    return working


def build_scoring_frame(df: pd.DataFrame) -> pd.DataFrame:
    working = _apply_factor_pipeline(df)
    working = working.dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)
    return working


def latest_snapshot(feature_df: pd.DataFrame) -> pd.DataFrame:
    latest_date = feature_df["date"].max()
    snapshot = feature_df.loc[feature_df["date"] == latest_date].copy()
    return snapshot.sort_values("symbol").reset_index(drop=True)
