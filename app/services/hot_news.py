from __future__ import annotations

from datetime import datetime
import re
import time
from typing import Any, Callable

import akshare as ak


_CACHE_TTL_SECONDS = 120.0
_HOT_NEWS_CACHE: dict[str, Any] = {
    "expires_at": 0.0,
    "payload": None,
}

_SOURCE_RANK: dict[str, int] = {
    "同花顺": 0,
    "东方财富": 1,
    "财联社": 2,
    "新浪财经": 3,
}

_TAG_RULES: list[tuple[tuple[str, ...], str]] = [
    (("华为", "鸿蒙", "半导体", "芯片", "算力", "人工智能", "AI", "机器人", "光刻"), "科技"),
    (("银行", "券商", "保险", "降准", "降息", "央行", "人民币"), "金融"),
    (("新能源", "光伏", "储能", "风电", "锂电", "电池", "充电"), "新能源"),
    (("医药", "创新药", "医疗", "生物", "疫苗"), "医药"),
    (("地产", "基建", "建筑", "城中村"), "地产基建"),
    (("黄金", "原油", "煤炭", "有色", "铜", "钢铁"), "资源"),
]

_SECTOR_RULES: list[tuple[tuple[str, ...], str]] = [
    (("商业航天", "卫星互联网", "卫星", "火箭", "航天", "北斗"), "商业航天"),
    (("半导体", "芯片", "晶圆", "光刻", "存储", "封测", "EDA"), "半导体"),
    (("6G", "5G", "通信", "光模块", "CPO", "天线"), "通信设备"),
    (("人工智能", "AI", "算力", "大模型", "服务器", "数据中心"), "AI算力"),
    (("机器人", "人形机器人", "自动化"), "机器人"),
    (("医药", "创新药", "医疗", "疫苗", "生物"), "医药"),
    (("光伏", "储能", "风电", "锂电", "电池", "新能源车", "充电"), "新能源"),
    (("券商", "银行", "保险", "央行", "降息", "降准", "人民币"), "金融地产"),
    (("地产", "基建", "建筑", "城中村"), "地产基建"),
    (("军工", "导弹", "战机", "国防"), "军工"),
    (("黄金", "白银", "有色", "铜", "钢铁", "煤炭"), "资源"),
    (("石油", "原油", "天然气"), "油气"),
    (("白羽鸡", "鸡苗", "养殖", "饲料"), "养殖"),
]

_SPECIAL_AI_RULES: list[tuple[tuple[str, ...], str, str]] = [
    (("冲突", "战争", "空袭", "打击", "霍尔木兹", "核不扩散"), "利好黄金原油", "positive"),
    (("油价大幅下跌", "国际油价大幅下跌", "原油跌", "油价下跌"), "利空原油链", "negative"),
    (("降息", "降准", "流动性宽松", "货币宽松"), "利好金融地产", "positive"),
]

_POSITIVE_KEYWORDS: tuple[str, ...] = (
    "获批",
    "签约",
    "中标",
    "订单",
    "融资",
    "增长",
    "回升",
    "景气",
    "提振",
    "突破",
    "扩产",
    "投产",
    "落地",
    "上调",
    "商用",
    "合作",
    "增资",
    "增持",
    "回购",
    "反弹",
)

_NEGATIVE_KEYWORDS: tuple[str, ...] = (
    "下跌",
    "下调",
    "暴跌",
    "制裁",
    "亏损",
    "减持",
    "回落",
    "收紧",
    "裁员",
    "违约",
    "警告",
    "紧张",
    "冻结",
    "打击",
    "空袭",
)

_TECH_FILTER_KEYWORDS: tuple[str, ...] = (
    "半导体",
    "芯片",
    "算力",
    "人工智能",
    "AI",
    "机器人",
    "人形机器人",
    "通信",
    "CPO",
    "光模块",
    "6G",
    "5G",
    "服务器",
    "数据中心",
    "EDA",
    "华为",
    "鸿蒙",
    "光刻",
    "存储",
    "英伟达",
    "GPU",
    "CPU",
    "卫星互联网",
    "卫星通信",
    "商业航天",
    "北斗",
    "智能眼镜",
    "消费电子",
    "手机",
)

_TECH_FILTER_AI_SECTORS: tuple[str, ...] = (
    "半导体",
    "通信设备",
    "AI算力",
    "机器人",
    "商业航天",
)

_TECH_EXCLUDE_KEYWORDS: tuple[str, ...] = (
    "冲突",
    "战争",
    "空袭",
    "袭击",
    "火箭弹",
    "导弹",
    "武装部队",
    "军方",
    "州长",
    "总统",
    "断水断电",
)

_HOT_NEWS_CATEGORY_LABELS: dict[str, str] = {
    "all": "全部",
    "tech": "科技",
    "finance": "金融",
    "new_energy": "新能源",
    "medicine": "医药",
    "infrastructure": "地产基建",
    "resources": "资源",
}


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _parse_datetime(value: Any, fallback_date: datetime | None = None) -> datetime | None:
    if value is None or value == "":
        return fallback_date

    if isinstance(value, datetime):
        return value

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        numeric = float(value)
        if numeric > 10_000_000_000:
            return datetime.fromtimestamp(numeric / 1000)
        if numeric > 1_000_000_000:
            return datetime.fromtimestamp(numeric)

    normalized = _normalize_text(value)
    if not normalized:
        return fallback_date

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue

    if re.fullmatch(r"\d{2}:\d{2}:\d{2}", normalized):
        base = fallback_date or datetime.now()
        return datetime.strptime(f"{base.strftime('%Y-%m-%d')} {normalized}", "%Y-%m-%d %H:%M:%S")

    return fallback_date


def _shorten(text: str, limit: int) -> str:
    text = _normalize_text(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _pick_title(title: Any, body: Any) -> str:
    normalized_title = _normalize_text(title)
    normalized_body = _normalize_text(body)
    if normalized_title:
        return _shorten(normalized_title, 72)
    if not normalized_body:
        return "市场热点快报"
    sentence = re.split(r"[。！？!?]", normalized_body, maxsplit=1)[0]
    return _shorten(sentence or normalized_body, 72)


def _pick_summary(body: Any, title: str) -> str:
    normalized_body = _normalize_text(body)
    if not normalized_body:
        return title
    return _shorten(normalized_body, 140)


def _infer_tag(title: str, summary: str) -> str:
    merged = f"{title} {summary}"
    for keywords, tag in _TAG_RULES:
        if any(keyword in merged for keyword in keywords):
            return tag
    return "快讯"


def _detect_sector(text: str, fallback_tag: str) -> str | None:
    for keywords, sector in _SECTOR_RULES:
        if any(keyword in text for keyword in keywords):
            return sector
    if fallback_tag and fallback_tag != "快讯":
        return fallback_tag
    return None


def _count_hits(text: str, keywords: tuple[str, ...]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def _build_ai_summary(title: str, summary: str, tag: str) -> tuple[str, str]:
    merged = f"{title} {summary}"

    for keywords, ai_summary, ai_tone in _SPECIAL_AI_RULES:
        if any(keyword in merged for keyword in keywords):
            return ai_summary, ai_tone

    sector = _detect_sector(merged, tag)
    positive_score = _count_hits(merged, _POSITIVE_KEYWORDS)
    negative_score = _count_hits(merged, _NEGATIVE_KEYWORDS)

    if positive_score > negative_score:
        return f"利好{sector or '相关板块'}", "positive"
    if negative_score > positive_score:
        return f"利空{sector or '风险偏好'}", "negative"
    if sector:
        return f"关注{sector}", "neutral"
    return "中性观察", "neutral"


def _dedupe_items(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        key = (item.get("title", ""), item.get("published_at", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= limit:
            break
    return deduped


def _normalize_category(category: Any) -> str:
    normalized = _normalize_text(category).lower()
    if normalized in {"tech", "technology", "科技"}:
        return "tech"
    if normalized in {"finance", "financial", "金融"}:
        return "finance"
    if normalized in {"new_energy", "newenergy", "新能源"}:
        return "new_energy"
    if normalized in {"medicine", "medical", "医药"}:
        return "medicine"
    if normalized in {"infrastructure", "property", "地产基建", "地产", "基建"}:
        return "infrastructure"
    if normalized in {"resources", "resource", "资源"}:
        return "resources"
    return "all"


def _matches_tech(item: dict[str, Any]) -> bool:
    tag = _normalize_text(item.get("tag"))
    ai_summary = _normalize_text(item.get("ai_summary"))
    merged = " ".join(
        [
            _normalize_text(item.get("title")),
            _normalize_text(item.get("summary")),
            tag,
            ai_summary,
        ]
    )

    if any(keyword in merged for keyword in _TECH_EXCLUDE_KEYWORDS):
        return False

    if tag == "科技":
        return True

    if any(sector in ai_summary for sector in _TECH_FILTER_AI_SECTORS):
        return True

    return any(keyword in merged for keyword in _TECH_FILTER_KEYWORDS)


def _filter_items_by_category(items: list[dict[str, Any]], category: str) -> list[dict[str, Any]]:
    if category == "tech":
        return [item for item in items if _matches_tech(item)]
    if category == "finance":
        return [item for item in items if _normalize_text(item.get("tag")) == "金融" or "金融" in _normalize_text(item.get("ai_summary"))]
    if category == "new_energy":
        return [item for item in items if _normalize_text(item.get("tag")) == "新能源" or "新能源" in _normalize_text(item.get("ai_summary"))]
    if category == "medicine":
        return [item for item in items if _normalize_text(item.get("tag")) == "医药" or "医药" in _normalize_text(item.get("ai_summary"))]
    if category == "infrastructure":
        return [
            item
            for item in items
            if _normalize_text(item.get("tag")) == "地产基建" or "地产基建" in _normalize_text(item.get("ai_summary"))
        ]
    if category == "resources":
        return [item for item in items if _normalize_text(item.get("tag")) == "资源" or "黄金原油" in _normalize_text(item.get("ai_summary"))]
    return items


def _sort_and_finalize_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(
        items,
        key=lambda item: (
            float(item.get("_sort_ts") or 0.0),
            -int(item.get("_source_rank") or 0),
        ),
        reverse=True,
    )
    finalized: list[dict[str, Any]] = []
    for item in ordered:
        finalized.append({key: value for key, value in item.items() if not key.startswith("_")})
    return finalized


def _normalize_item(
    *,
    title: Any,
    body: Any,
    published_at: Any,
    url: Any,
    source: str,
    published_base: Any = None,
) -> dict[str, Any]:
    normalized_title = _pick_title(title, body)
    normalized_summary = _pick_summary(body, normalized_title)
    normalized_tag = _infer_tag(normalized_title, normalized_summary)
    ai_summary, ai_tone = _build_ai_summary(normalized_title, normalized_summary, normalized_tag)
    base_datetime = _parse_datetime(published_base)
    published_datetime = _parse_datetime(published_at, fallback_date=base_datetime)
    published_display = (
        published_datetime.strftime("%Y-%m-%d %H:%M:%S")
        if published_datetime is not None
        else (_normalize_text(published_at) or "刚刚")
    )
    return {
        "title": normalized_title,
        "summary": normalized_summary,
        "published_at": published_display,
        "url": _normalize_text(url),
        "source": source,
        "tag": normalized_tag,
        "ai_summary": ai_summary,
        "ai_tone": ai_tone,
        "_sort_ts": published_datetime.timestamp() if published_datetime is not None else 0.0,
        "_source_rank": _SOURCE_RANK.get(source, 99),
    }


def _fetch_ths(limit: int) -> list[dict[str, Any]]:
    frame = ak.stock_info_global_ths()
    items = [
        _normalize_item(
            title=row.get("标题"),
            body=row.get("内容"),
            published_at=row.get("发布时间"),
            url=row.get("链接"),
            source="同花顺",
        )
        for row in frame.to_dict(orient="records")
    ]
    return _dedupe_items(items, limit)


def _fetch_em(limit: int) -> list[dict[str, Any]]:
    frame = ak.stock_info_global_em()
    items = [
        _normalize_item(
            title=row.get("标题"),
            body=row.get("摘要"),
            published_at=row.get("发布时间"),
            url=row.get("链接"),
            source="东方财富",
        )
        for row in frame.to_dict(orient="records")
    ]
    return _dedupe_items(items, limit)


def _fetch_cls(limit: int) -> list[dict[str, Any]]:
    frame = ak.stock_info_global_cls()
    items = [
        _normalize_item(
            title=row.get("标题"),
            body=row.get("内容"),
            published_at=row.get("发布时间"),
            url="",
            source="财联社",
            published_base=row.get("发布日期"),
        )
        for row in frame.to_dict(orient="records")
    ]
    return _dedupe_items(items, limit)


def _fetch_sina(limit: int) -> list[dict[str, Any]]:
    frame = ak.stock_info_global_sina()
    items = [
        _normalize_item(
            title="",
            body=row.get("内容"),
            published_at=row.get("时间"),
            url="",
            source="新浪财经",
        )
        for row in frame.to_dict(orient="records")
    ]
    return _dedupe_items(items, limit)


def _build_unavailable_payload(errors: list[str]) -> dict[str, Any]:
    return {
        "items": [],
        "source": "unavailable",
        "source_label": "热点快报",
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "message": "热点快报暂时不可用",
        "errors": errors,
        "category": "all",
        "category_label": _HOT_NEWS_CATEGORY_LABELS["all"],
        "available_categories": _HOT_NEWS_CATEGORY_LABELS,
    }


def get_hot_news(
    limit: int = 20,
    offset: int = 0,
    category: str = "all",
    force_refresh: bool = False,
) -> dict[str, Any]:
    normalized_limit = max(1, min(int(limit or 20), 60))
    normalized_offset = max(0, int(offset or 0))
    normalized_category = _normalize_category(category)
    cached_payload = _HOT_NEWS_CACHE.get("payload")
    if not force_refresh and cached_payload and time.monotonic() < float(_HOT_NEWS_CACHE.get("expires_at", 0.0)):
        all_items = cached_payload.get("items") or []
        filtered_items = _filter_items_by_category(all_items, normalized_category)
        sliced_items = filtered_items[normalized_offset : normalized_offset + normalized_limit]
        return {
            **cached_payload,
            "items": sliced_items,
            "offset": normalized_offset,
            "limit": normalized_limit,
            "total": len(filtered_items),
            "has_more": normalized_offset + len(sliced_items) < len(filtered_items),
            "next_offset": normalized_offset + len(sliced_items),
            "category": normalized_category,
            "category_label": _HOT_NEWS_CATEGORY_LABELS.get(normalized_category, "全部"),
            "available_categories": _HOT_NEWS_CATEGORY_LABELS,
            "source_label": (
                f"{_HOT_NEWS_CATEGORY_LABELS.get(normalized_category, '全部')}热点快报"
                if normalized_category != "all"
                else cached_payload.get("source_label", "聚合热点快报")
            ),
        }

    errors: list[str] = []
    fetchers: list[tuple[str, str, Callable[[int], list[dict[str, Any]]]]] = [
        ("ths", "同花顺全球财经快报", _fetch_ths),
        ("em", "东方财富全球快讯", _fetch_em),
        ("cls", "财联社快讯", _fetch_cls),
        ("sina", "新浪财经快讯", _fetch_sina),
    ]

    merged_items: list[dict[str, Any]] = []
    for source_key, source_label, fetcher in fetchers:
        try:
            items = fetcher(240)
        except Exception as exc:
            errors.append(f"{source_key}: {exc}")
            continue
        if not items:
            errors.append(f"{source_key}: empty result")
            continue
        merged_items.extend(items)

    if not merged_items:
        payload = _build_unavailable_payload(errors)
        _HOT_NEWS_CACHE["payload"] = payload
        _HOT_NEWS_CACHE["expires_at"] = time.monotonic() + _CACHE_TTL_SECONDS
        return payload

    finalized_items = _sort_and_finalize_items(_dedupe_items(merged_items, 320))
    base_payload = {
        "items": finalized_items,
        "source": "merged",
        "source_label": "聚合热点快报",
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "message": "已聚合同花顺、东方财富、财联社和新浪快讯",
        "errors": errors,
        "category": "all",
        "category_label": _HOT_NEWS_CATEGORY_LABELS["all"],
        "available_categories": _HOT_NEWS_CATEGORY_LABELS,
    }

    _HOT_NEWS_CACHE["payload"] = base_payload
    _HOT_NEWS_CACHE["expires_at"] = time.monotonic() + _CACHE_TTL_SECONDS
    filtered_items = _filter_items_by_category(finalized_items, normalized_category)
    sliced_items = filtered_items[normalized_offset : normalized_offset + normalized_limit]
    return {
        **base_payload,
        "items": sliced_items,
        "offset": normalized_offset,
        "limit": normalized_limit,
        "total": len(filtered_items),
        "has_more": normalized_offset + len(sliced_items) < len(filtered_items),
        "next_offset": normalized_offset + len(sliced_items),
        "category": normalized_category,
        "category_label": _HOT_NEWS_CATEGORY_LABELS.get(normalized_category, "全部"),
        "available_categories": _HOT_NEWS_CATEGORY_LABELS,
        "source_label": (
            f"{_HOT_NEWS_CATEGORY_LABELS.get(normalized_category, '全部')}热点快报"
            if normalized_category != "all"
            else base_payload["source_label"]
        ),
    }
