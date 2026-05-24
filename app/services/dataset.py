from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


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
    symbols = [
        ("600519", "贵州茅台"),
        ("000333", "美的集团"),
        ("600036", "招商银行"),
        ("000651", "格力电器"),
        ("601318", "中国平安"),
        ("002415", "海康威视"),
        ("300750", "宁德时代"),
        ("600276", "恒瑞医药"),
        ("002594", "比亚迪"),
        ("600887", "伊利股份"),
    ]
    dates = pd.bdate_range("2024-01-02", periods=220)
    rows: list[dict] = []

    for idx, (symbol, name) in enumerate(symbols):
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
                }
            )

    df = pd.DataFrame(rows).sort_values(["symbol", "date"]).reset_index(drop=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return df


def load_price_data(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        return generate_sample_dataset(csv_path)

    df = pd.read_csv(csv_path, parse_dates=["date"], dtype={"symbol": str, "name": str})
    if df.empty:
        return generate_sample_dataset(csv_path)
    df["symbol"] = df["symbol"].astype(str).str.zfill(6)
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
