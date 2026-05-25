from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
STATUS_DIR = DATA_DIR / "status"
CACHE_DIR = STATUS_DIR / "cache"

DEFAULT_MODEL_PATH = MODELS_DIR / "stock_ranker.pkl"
DEFAULT_DATA_PATH = DATA_DIR / "sample_prices.csv"
REAL_DATA_PATH = DATA_DIR / "a_share_prices.csv"
REFRESH_STATUS_PATH = STATUS_DIR / "refresh_status.json"
REFRESH_LOG_PATH = STATUS_DIR / "refresh.log"
MODEL_META_PATH = STATUS_DIR / "model_meta.json"
MARKET_OVERVIEW_CACHE_PATH = STATUS_DIR / "market_overview_cache.json"
HOT_NEWS_CACHE_PATH = STATUS_DIR / "hot_news_cache.json"
STOCK_CATALOG_CACHE_PATH = STATUS_DIR / "stock_catalog_cache.json"
HISTORY_CACHE_DIR = CACHE_DIR / "history"
PAPER_PORTFOLIO_PATH = DATA_DIR / "paper_portfolio.json"

DEFAULT_SAMPLE_SYMBOLS: list[tuple[str, str]] = [
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

INDEX_POOLS: dict[str, dict[str, str]] = {
    "hs300": {"symbol": "000300", "name": "沪深300"},
    "zz500": {"symbol": "000905", "name": "中证500"},
}
