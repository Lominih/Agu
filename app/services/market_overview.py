from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from io import StringIO
import math
import re
import time
from typing import Any

import akshare as ak
import pandas as pd
import requests

from app.core.config import MARKET_OVERVIEW_CACHE_PATH
from app.services.market_watch import normalize_akshare_minute_frame
from app.services.state_store import read_json_file, write_json_file


THS_US_RANK_URL = "https://q.10jqka.com.cn/usa/detail/"
THS_US_RANK_PAGE_TEMPLATE = "https://q.10jqka.com.cn/usa/detail/page/{page}/field/zdf/order/desc/"
THS_US_COMPANY_TEMPLATE = "https://stockpage.10jqka.com.cn/{symbol}/company/"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36"
    )
}

US_INDUSTRY_TRANSLATIONS: dict[str, str] = {
    "Semiconductors": "半导体",
    "Telecommunications Equipment": "通信设备",
    "Computer Processing Hardware": "电脑硬件/存储设备",
    "Computer Communications": "计算机通信",
    "Data Processing Services": "数据处理服务",
    "Electronic Components": "电子元件",
    "Electronic Equipment/Instruments": "电子设备与仪器",
    "Technology Services": "科技服务",
    "Technology services": "科技服务",
    "Internet Software/Services": "互联网软件服务",
    "Packaged Software": "软件",
    "Biotechnology": "生物科技",
    "Medical Specialties": "专科医疗",
    "Pharmaceuticals: Major": "大型制药",
    "Communications": "通信",
    "Aerospace & Defense": "航空航天与国防",
    "Consumer Electronics": "消费电子",
}

_CACHE: dict[str, dict[str, Any]] = {
    "nasdaq_previous": {"expires_at": 0.0, "value": None},
    "us_rank_pages": {"expires_at": 0.0, "value": None},
    "us_industry_leaders": {"expires_at": 0.0, "value": None},
}
_COMPANY_CACHE: dict[str, dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _safe_float(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_signed_number(value: float | None) -> float | None:
    return None if value is None else round(float(value), 2)


def _normalize_label(value: str | None) -> str:
    return "" if value is None else str(value).replace("\xa0", " ").replace("\u202f", " ").strip()


def _translate_us_industry_label(value: str | None) -> str:
    normalized = _normalize_label(value)
    return US_INDUSTRY_TRANSLATIONS.get(normalized, normalized) if normalized else ""


def _get_cached_value(key: str, ttl_seconds: int, builder):
    cached = _CACHE.get(key)
    now = time.monotonic()
    if cached and cached["value"] is not None and cached["expires_at"] > now:
        return cached["value"]
    value = builder()
    _CACHE[key] = {"expires_at": now + ttl_seconds, "value": value}
    return value


def _get_company_cache(symbol: str) -> dict[str, Any] | None:
    cached = _COMPANY_CACHE.get(symbol)
    if not cached or cached["expires_at"] <= time.monotonic():
        _COMPANY_CACHE.pop(symbol, None)
        return None
    return cached["value"]


def _set_company_cache(symbol: str, value: dict[str, Any], ttl_seconds: int = 60 * 60 * 24) -> dict[str, Any]:
    _COMPANY_CACHE[symbol] = {"expires_at": time.monotonic() + ttl_seconds, "value": value}
    return value


def _extract_total_pages(html_text: str) -> int:
    match = re.search(r'<span class="page_info">\s*(\d+)\s*/\s*(\d+)\s*</span>', html_text)
    return max(1, int(match.group(2))) if match else 1


def _load_ths_table(url: str, encoding: str = "gbk") -> tuple[pd.DataFrame, str]:
    response = requests.get(url, timeout=20, headers=REQUEST_HEADERS)
    response.raise_for_status()
    response.encoding = encoding
    html = response.text
    frames = pd.read_html(StringIO(html))
    if not frames:
        raise ValueError(f"no table found: {url}")
    frame = frames[0].copy()
    frame.columns = [_normalize_label(str(column)) for column in frame.columns]
    return frame, html


def _fetch_ths_us_rank_rows(max_pages: int = 6, max_rows: int = 240) -> dict[str, Any]:
    def _builder() -> dict[str, Any]:
        first_frame, first_html = _load_ths_table(THS_US_RANK_URL)
        total_pages = _extract_total_pages(first_html)
        target_pages = min(max_pages, total_pages)
        frames = [first_frame]
        loaded_pages = 1
        for page in range(2, target_pages + 1):
            try:
                page_frame, _ = _load_ths_table(THS_US_RANK_PAGE_TEMPLATE.format(page=page))
            except Exception:
                continue
            frames.append(page_frame)
            loaded_pages += 1
        merged = pd.concat(frames, ignore_index=True)
        merged["代码"] = merged["代码"].astype(str).str.strip()
        merged["名称"] = merged["名称"].astype(str).str.strip()
        merged["涨跌幅(%)"] = pd.to_numeric(merged["涨跌幅(%)"], errors="coerce")
        merged["现价"] = pd.to_numeric(merged["现价"], errors="coerce")
        merged["涨跌"] = pd.to_numeric(merged["涨跌"], errors="coerce")
        merged = merged.dropna(subset=["代码", "涨跌幅(%)"]).loc[lambda df: df["代码"] != ""].copy()
        merged = merged.sort_values("涨跌幅(%)", ascending=False).head(max_rows).reset_index(drop=True)
        items: list[dict[str, Any]] = []
        for row in merged.to_dict(orient="records"):
            items.append(
                {
                    "symbol": _normalize_label(row.get("代码")),
                    "name": _normalize_label(row.get("名称")),
                    "close": _safe_float(row.get("现价")),
                    "change": _safe_float(row.get("涨跌")),
                    "change_pct": _safe_float(row.get("涨跌幅(%)")),
                }
            )
        return {"items": items, "pages_loaded": loaded_pages, "total_pages": total_pages}

    return _get_cached_value("us_rank_pages", ttl_seconds=60 * 30, builder=_builder)


def _extract_company_field_text(frame: pd.DataFrame, key: str) -> str | None:
    for row in frame.fillna("").astype(str).itertuples(index=False):
        for cell in row:
            if key in cell:
                parts = cell.split("：", 1)
                if len(parts) == 2 and _normalize_label(parts[1]):
                    return _normalize_label(parts[1])
    return None


def _fetch_ths_us_company_profile(symbol: str) -> dict[str, Any]:
    cached = _get_company_cache(symbol)
    if cached is not None:
        return cached
    response = requests.get(THS_US_COMPANY_TEMPLATE.format(symbol=symbol), timeout=20, headers=REQUEST_HEADERS)
    response.raise_for_status()
    response.encoding = "utf-8"
    frames = pd.read_html(StringIO(response.text))
    if len(frames) < 2:
        return _set_company_cache(symbol, {})
    profile_frame = frames[1].copy()
    industry = _extract_company_field_text(profile_frame, "所属行业")
    company_name = _extract_company_field_text(profile_frame, "公司简称")
    english_name = _extract_company_field_text(profile_frame, "英文名称")
    return _set_company_cache(
        symbol,
        {
            "industry_raw": industry,
            "industry_name": _translate_us_industry_label(industry),
            "company_name": company_name,
            "english_name": english_name,
            "source": "同花顺公司概况页",
        },
    )


def get_shanghai_intraday_overview() -> dict:
    frame = ak.stock_zh_a_minute(symbol="sh000001", period="1", adjust="").copy()
    frame = normalize_akshare_minute_frame(frame)
    if frame.empty:
        return {
            "symbol": "sh000001",
            "name": "上证指数",
            "trade_date": None,
            "updated_at": _now_iso(),
            "open": None,
            "prev_close": None,
            "current": None,
            "change": None,
            "change_pct": None,
            "items": [],
            "meta": {"status": "empty", "source": "akshare-minute", "warnings": ["minute frame empty"]},
        }
    frame["trade_day"] = frame["date"].dt.strftime("%Y-%m-%d")
    latest_trade_date = str(frame["trade_day"].iloc[-1])
    day_frame = frame.loc[frame["trade_day"] == latest_trade_date].copy().sort_values("date").reset_index(drop=True)
    day_frame["close"] = pd.to_numeric(day_frame["close"], errors="coerce")
    day_frame["open"] = pd.to_numeric(day_frame["open"], errors="coerce")
    open_price = _safe_float(day_frame.iloc[0]["open"] if not day_frame.empty else None)
    current_price = _safe_float(day_frame.iloc[-1]["close"] if not day_frame.empty else None)
    previous_close = None
    try:
        daily_frame = ak.stock_zh_index_daily(symbol="sh000001").copy().sort_values("date").reset_index(drop=True)
        if not daily_frame.empty:
            daily_frame["date"] = pd.to_datetime(daily_frame["date"])
            daily_frame["close"] = pd.to_numeric(daily_frame["close"], errors="coerce")
            latest_daily_date = pd.Timestamp(daily_frame.iloc[-1]["date"]).strftime("%Y-%m-%d")
            previous_close = _safe_float(daily_frame.iloc[-2]["close"] if latest_daily_date == latest_trade_date and len(daily_frame) >= 2 else daily_frame.iloc[-1]["close"])
    except Exception:
        previous_close = None
    baseline_close = previous_close if previous_close not in (None, 0) else open_price
    change = round(current_price - baseline_close, 2) if baseline_close not in (None, 0) and current_price is not None else None
    change_pct = round((current_price / baseline_close - 1) * 100, 2) if baseline_close not in (None, 0) and current_price is not None else None
    items = [
        {
            "time": pd.Timestamp(row["date"]).strftime("%H:%M"),
            "price": round(float(row["close"]), 3) if pd.notna(row["close"]) else None,
            "change_pct": round((float(row["close"]) / baseline_close - 1) * 100, 2) if pd.notna(row["close"]) and baseline_close not in (None, 0) else None,
        }
        for row in day_frame.to_dict(orient="records")
        if pd.notna(row.get("close"))
    ]
    return {
        "symbol": "sh000001",
        "name": "上证指数",
        "trade_date": latest_trade_date,
        "updated_at": _now_iso(),
        "open": round(open_price, 3) if open_price is not None else None,
        "prev_close": round(previous_close, 3) if previous_close is not None else None,
        "current": round(current_price, 3) if current_price is not None else None,
        "change": _format_signed_number(change),
        "change_pct": _format_signed_number(change_pct),
        "items": items,
        "meta": {"status": "fresh", "source": "akshare-minute", "warnings": []},
    }


def get_nasdaq_previous_change() -> dict:
    def _builder() -> dict:
        frame = ak.index_us_stock_sina(symbol=".IXIC").copy().sort_values("date").reset_index(drop=True)
        if len(frame) < 2:
            return {"symbol": ".IXIC", "name": "纳斯达克", "trade_date": None, "close": None, "change": None, "change_pct": None}
        latest = frame.iloc[-1]
        previous = frame.iloc[-2]
        latest_close = _safe_float(latest.get("close"))
        previous_close = _safe_float(previous.get("close"))
        change = round(latest_close - previous_close, 2) if latest_close is not None and previous_close not in (None, 0) else None
        change_pct = round((latest_close / previous_close - 1) * 100, 2) if latest_close is not None and previous_close not in (None, 0) else None
        return {
            "symbol": ".IXIC",
            "name": "纳斯达克",
            "trade_date": pd.Timestamp(latest["date"]).strftime("%Y-%m-%d"),
            "close": round(latest_close, 2) if latest_close is not None else None,
            "change": _format_signed_number(change),
            "change_pct": _format_signed_number(change_pct),
        }

    return _get_cached_value("nasdaq_previous", ttl_seconds=60 * 60, builder=_builder)


def get_us_industry_leaders(limit: int = 6, trade_date: str | None = None) -> list[dict]:
    def _builder() -> list[dict]:
        rank_payload = _fetch_ths_us_rank_rows(max_pages=3, max_rows=120)
        rank_items = rank_payload.get("items", [])
        symbols = [str(item.get("symbol")) for item in rank_items if item.get("symbol")]
        profiles: dict[str, dict[str, Any]] = {}
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_map = {executor.submit(_fetch_ths_us_company_profile, symbol): symbol for symbol in symbols}
            for future in as_completed(future_map):
                symbol = future_map[future]
                try:
                    profiles[symbol] = future.result()
                except Exception:
                    profiles[symbol] = {}
        grouped: dict[str, dict[str, Any]] = {}
        for item in rank_items:
            symbol = item.get("symbol")
            if not symbol:
                continue
            profile = profiles.get(symbol, {})
            industry_raw = _normalize_label(profile.get("industry_raw"))
            industry_name = _normalize_label(profile.get("industry_name") or industry_raw)
            change_pct = _safe_float(item.get("change_pct"))
            if not industry_name or change_pct is None:
                continue
            group = grouped.setdefault(
                industry_name,
                {
                    "symbol": f"US-{industry_name}",
                    "name": industry_name,
                    "name_en": industry_raw if industry_raw and industry_raw != industry_name else None,
                    "trade_date": trade_date,
                    "stocks": 0,
                    "leader_symbol": None,
                    "leader_name": None,
                    "leader_change_pct": None,
                    "_change_sum": 0.0,
                    "_market_sum": 0.0,
                },
            )
            group["stocks"] += 1
            group["_change_sum"] += change_pct
            close_value = _safe_float(item.get("close"))
            if close_value is not None:
                group["_market_sum"] += max(close_value, 0)
            leader_change = _safe_float(group.get("leader_change_pct"))
            if leader_change is None or change_pct > leader_change:
                group["leader_symbol"] = symbol
                group["leader_name"] = profile.get("company_name") or item.get("name")
                group["leader_change_pct"] = round(change_pct, 2)
        leaders: list[dict[str, Any]] = []
        for industry_name, group in grouped.items():
            stock_count = int(group["stocks"])
            avg_change = round(group["_change_sum"] / stock_count, 2) if stock_count else None
            market_weight = group["_market_sum"] if group["_market_sum"] > 0 else 1.0
            score = round(avg_change * math.log(stock_count + 1, 2), 4) if avg_change is not None else None
            leaders.append(
                {
                    "symbol": group["symbol"],
                    "name": industry_name,
                    "name_en": group["name_en"],
                    "trade_date": trade_date,
                    "change_pct": avg_change,
                    "stocks": stock_count,
                    "source": "同花顺美股涨幅榜 + 公司概况页行业聚合",
                    "leader_symbol": group["leader_symbol"],
                    "leader_name": group["leader_name"],
                    "leader_change_pct": group["leader_change_pct"],
                    "avg_change_pct": avg_change,
                    "market_cap_proxy": round(market_weight, 2),
                    "score": score,
                }
            )
        leaders.sort(key=lambda item: (item.get("score") or float("-inf"), item.get("change_pct") or float("-inf"), item.get("stocks") or 0), reverse=True)
        return leaders

    cached_items = _get_cached_value("us_industry_leaders", ttl_seconds=60 * 30, builder=_builder)
    normalized_items = [dict(item, trade_date=trade_date or item.get("trade_date")) for item in cached_items]
    return normalized_items[:limit]


def get_market_overview(limit: int = 6) -> dict:
    warnings: list[str] = []
    sections: dict[str, Any] = {}
    section_status: dict[str, str] = {}

    try:
        shanghai = get_shanghai_intraday_overview()
        section_status["shanghai"] = shanghai.get("meta", {}).get("status", "fresh")
    except Exception as exc:
        warnings.append(f"上证分时暂不可用: {exc}")
        shanghai = {"symbol": "sh000001", "name": "上证指数", "trade_date": None, "updated_at": _now_iso(), "open": None, "prev_close": None, "current": None, "change": None, "change_pct": None, "items": [], "meta": {"status": "failed", "source": "akshare-minute", "warnings": [str(exc)]}}
        section_status["shanghai"] = "failed"
    sections["shanghai"] = shanghai

    try:
        nasdaq_previous = get_nasdaq_previous_change()
        section_status["nasdaq_previous"] = "fresh"
    except Exception as exc:
        warnings.append(f"纳指数据暂不可用: {exc}")
        nasdaq_previous = {"symbol": ".IXIC", "name": "纳斯达克", "trade_date": None, "close": None, "change": None, "change_pct": None}
        section_status["nasdaq_previous"] = "failed"
    sections["nasdaq_previous"] = nasdaq_previous

    try:
        us_industry_leaders = get_us_industry_leaders(limit=max(limit, 6), trade_date=nasdaq_previous.get("trade_date"))
        section_status["us_industry_leaders"] = "fresh"
    except Exception as exc:
        warnings.append(f"美股行业数据暂不可用: {exc}")
        us_industry_leaders = []
        section_status["us_industry_leaders"] = "failed"
    sections["us_industry_leaders"] = us_industry_leaders

    payload = {
        "updated_at": _now_iso(),
        "warnings": warnings,
        "shanghai": sections["shanghai"],
        "nasdaq_previous": sections["nasdaq_previous"],
        "top_sectors": [],
        "us_sector_leaders": sections["us_industry_leaders"],
        "us_industry_leaders": sections["us_industry_leaders"],
        "us_industry_source": "同花顺美股涨幅榜分页 + 同花顺公司概况页所属行业聚合",
        "meta": {
            "status": "fresh" if not warnings else "degraded",
            "section_status": section_status,
            "updated_at": _now_iso(),
        },
    }

    if payload["shanghai"].get("items") or payload["us_industry_leaders"] or payload["nasdaq_previous"].get("trade_date"):
        write_json_file(MARKET_OVERVIEW_CACHE_PATH, payload)
        return payload

    cached_payload = read_json_file(MARKET_OVERVIEW_CACHE_PATH, default_factory=lambda: None)
    if isinstance(cached_payload, dict):
        meta = dict(cached_payload.get("meta") or {})
        meta.update({"status": "stale-cache", "updated_at": _now_iso(), "warnings": [*(meta.get("warnings") or []), *warnings]})
        cached_payload["meta"] = meta
        cached_payload["warnings"] = [*(cached_payload.get("warnings") or []), *warnings]
        return cached_payload

    return payload
