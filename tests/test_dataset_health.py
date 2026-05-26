from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.services.dataset import get_data_health_report, get_incremental_start_date


def test_incremental_start_date_falls_back_when_file_missing(tmp_path: Path) -> None:
    target = tmp_path / "missing.csv"
    assert get_incremental_start_date(target, default_start_date="2024-01-01") == "2024-01-01"


def test_incremental_start_date_uses_overlap(tmp_path: Path) -> None:
    target = tmp_path / "prices.csv"
    pd.DataFrame({"date": pd.to_datetime(["2024-01-01", "2024-03-01"])}).to_csv(target, index=False)
    assert get_incremental_start_date(target, default_start_date="2024-01-01", overlap_days=10) == "2024-02-20"


def test_data_health_warns_for_invalid_rows() -> None:
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-01"]),
            "symbol": ["600519", "600519"],
            "name": ["贵州茅台", "贵州茅台"],
            "close": [100, -1],
            "volume": [1000, -10],
            "source": ["sample", "sample"],
            "pool": ["sample", "sample"],
        }
    )
    report = get_data_health_report(df)
    assert report["status"] == "warn"
    assert report["issues"]
