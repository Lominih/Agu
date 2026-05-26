from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import traceback


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import DEFAULT_MODEL_PATH, REAL_DATA_PATH, REFRESH_LOG_PATH  # noqa: E402
from app.services.dataset import (  # noqa: E402
    FEATURE_COLUMNS,
    build_features,
    fetch_real_dataset,
    get_data_health_report,
    get_incremental_start_date,
    load_price_data,
    load_index_constituents,
)
from app.services.model_state import write_model_meta  # noqa: E402
from app.services.modeling import train_model  # noqa: E402
from app.services.refresh_status import read_refresh_status, utc_now_iso, write_refresh_status  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh real A-share data and retrain the model.")
    parser.add_argument("--pool", default="hs300", help="Stock pool key, such as hs300 or zz500")
    parser.add_argument("--start-date", default="2023-01-01", help="History start date, e.g. 2023-01-01")
    parser.add_argument("--workers", type=int, default=None, help="Override process pool worker count")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    REFRESH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing_status = read_refresh_status()
    started_at = existing_status.get("started_at") or utc_now_iso()

    write_refresh_status(
        {
            "state": "running",
            "pool": args.pool,
            "pid": os.getpid(),
            "started_at": started_at,
            "finished_at": None,
            "message": f"开始刷新 {args.pool} 真实数据并训练模型",
            "rows": None,
            "symbols": None,
            "metrics": None,
            "error": None,
            "log_path": str(REFRESH_LOG_PATH),
        }
    )

    try:
        symbols = load_index_constituents(args.pool)
        existing_prices = load_price_data(REAL_DATA_PATH, source="real", allow_remote_fetch=False) if REAL_DATA_PATH.exists() else None
        effective_start_date = get_incremental_start_date(REAL_DATA_PATH, default_start_date=args.start_date)
        fetched_prices = fetch_real_dataset(
            REAL_DATA_PATH,
            symbols=symbols,
            start_date=effective_start_date,
            pool=args.pool,
            max_workers=args.workers,
        )
        if existing_prices is not None and not existing_prices.empty:
            prices = (
                fetched_prices.pipe(lambda frame: __import__("pandas").concat([existing_prices, frame], ignore_index=True))
                .drop_duplicates(subset=["symbol", "date"], keep="last")
                .sort_values(["symbol", "date"])
                .reset_index(drop=True)
            )
            prices.to_csv(REAL_DATA_PATH, index=False, encoding="utf-8-sig")
        else:
            prices = fetched_prices
        health = get_data_health_report(prices)
        features = build_features(prices)
        metrics = train_model(features, DEFAULT_MODEL_PATH)
        write_model_meta(
            source="real",
            pool=args.pool,
            feature_columns=list(FEATURE_COLUMNS),
            metrics={key: value for key, value in metrics.items() if key != "backtest"},
            backtest=metrics.get("backtest"),
        )

        write_refresh_status(
            {
                "state": "success",
                "pool": args.pool,
                "pid": os.getpid(),
                "started_at": started_at,
                "message": "真实 A 股数据刷新完成，模型训练完成",
                "rows": int(len(prices)),
                "symbols": int(prices["symbol"].nunique()),
                "start_date": effective_start_date,
                "metrics": metrics,
                "data_health": health,
                "model_version": f"{args.pool}-{effective_start_date}",
                "error": None,
                "finished_at": utc_now_iso(),
                "log_path": str(REFRESH_LOG_PATH),
            }
        )
        return 0
    except Exception as exc:
        error_text = "".join(traceback.format_exception(exc))
        with REFRESH_LOG_PATH.open("w", encoding="utf-8") as fh:
            fh.write(error_text)

        write_refresh_status(
            {
                "state": "failed",
                "pool": args.pool,
                "pid": os.getpid(),
                "started_at": started_at,
                "message": "真实 A 股数据刷新失败",
                "error": str(exc),
                "log_path": str(REFRESH_LOG_PATH),
                "finished_at": utc_now_iso(),
            }
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
