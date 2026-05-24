from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import DEFAULT_MODEL_PATH, REAL_DATA_PATH
from app.services.dataset import build_features, fetch_real_dataset, load_index_constituents, load_price_data
from app.services.modeling import train_model


def main() -> None:
    try:
        pool = "hs300"
        symbols = load_index_constituents(pool)
        prices = fetch_real_dataset(REAL_DATA_PATH, symbols=symbols, pool=pool)
        source = f"AKShare真实A股历史数据 ({pool})"
    except Exception:
        prices = load_price_data(REAL_DATA_PATH, source="sample")
        source = "本地样例数据"

    features = build_features(prices)
    metrics = train_model(features, DEFAULT_MODEL_PATH)
    print(f"训练完成，当前数据来源: {source}")
    print(metrics)


if __name__ == "__main__":
    main()
