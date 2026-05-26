from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import DEFAULT_MODEL_PATH, DEFAULT_DATA_PATH, REAL_DATA_PATH  # noqa: E402
from app.services.dataset import FEATURE_COLUMNS, build_features, get_data_health_report, load_price_data  # noqa: E402
from app.services.model_state import write_model_meta  # noqa: E402
from app.services.modeling import train_model  # noqa: E402


def main() -> None:
    source = "real" if REAL_DATA_PATH.exists() else "sample"
    data_path = REAL_DATA_PATH if source == "real" else DEFAULT_DATA_PATH

    prices = load_price_data(data_path, source=source, allow_remote_fetch=False)
    health = get_data_health_report(prices)
    features = build_features(prices)
    metrics = train_model(features, DEFAULT_MODEL_PATH)
    write_model_meta(
        source=source,
        pool=str(prices["pool"].iloc[0]) if "pool" in prices.columns and not prices.empty else source,
        feature_columns=list(FEATURE_COLUMNS),
        metrics={key: value for key, value in metrics.items() if key != "backtest"},
        backtest=metrics.get("backtest"),
    )

    print(f"训练完成，当前数据来源: {source}")
    print(health)
    print(metrics)


if __name__ == "__main__":
    main()
