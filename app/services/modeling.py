from __future__ import annotations

from pathlib import Path
import pickle
from typing import Any

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

from app.services.dataset import FEATURE_COLUMNS


FEATURE_LABELS = {
    "ret_5": "近5日收益",
    "ret_10": "近10日收益",
    "volatility_10": "近10日波动率",
    "price_vs_ma10": "相对10日均线",
    "price_vs_ma20": "相对20日均线",
    "volume_ratio_5": "量比(5日)",
}


def _format_percent_value(value: float | None, digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return "-"
    numeric = float(value) * 100
    return f"{numeric:+.{digits}f}%"


def _format_plain_percent_value(value: float | None, digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return "-"
    numeric = float(value) * 100
    return f"{numeric:.{digits}f}%"


def _format_contribution_value(value: float | None, digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return "-"
    numeric = float(value) * 100
    return f"{numeric:+.{digits}f}个百分点"


def _format_feature_value(feature: str, value: float | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    numeric = float(value)
    if feature in {"ret_5", "ret_10", "price_vs_ma10", "price_vs_ma20"}:
        return _format_percent_value(numeric)
    if feature == "volatility_10":
        return _format_plain_percent_value(numeric)
    if feature == "volume_ratio_5":
        return f"{numeric:.2f}倍"
    return f"{numeric:.4f}"


def _reason_tag(feature: str, value: float, contribution: float) -> str:
    if feature == "ret_5":
        if value >= 0.08:
            return "短线动量强"
        if value >= 0:
            return "短线动量偏强"
        return "短线修复预期"
    if feature == "ret_10":
        if value >= 0.12:
            return "10日趋势延续"
        if value >= 0:
            return "中段趋势向上"
        return "中段趋势修复"
    if feature == "volatility_10":
        if contribution >= 0 and value <= 0.03:
            return "波动受控"
        if contribution >= 0:
            return "走势弹性活跃"
        return "波动偏大"
    if feature == "price_vs_ma10":
        if value >= 0.08:
            return "强势站上10日线"
        if value >= 0:
            return "位于10日线之上"
        return "贴近10日线"
    if feature == "price_vs_ma20":
        if value >= 0.08:
            return "站上20日线"
        if value >= 0:
            return "中期趋势偏强"
        return "靠近20日线"
    if feature == "volume_ratio_5":
        if value >= 1.8:
            return "量能明显放大"
        if value >= 1.05:
            return "量能配合较好"
        return "量能平稳"
    return FEATURE_LABELS.get(feature, feature)


def _positive_reason_text(feature: str, value: float, contribution: float) -> str:
    formatted_value = _format_feature_value(feature, value)
    formatted_contribution = _format_contribution_value(contribution)
    if feature == "ret_5":
        return f"近5日收益为{formatted_value}，短线动量偏强，拉动模型预测约{formatted_contribution}。"
    if feature == "ret_10":
        return f"近10日收益为{formatted_value}，中段趋势保持上行，拉动模型预测约{formatted_contribution}。"
    if feature == "volatility_10":
        return f"近10日波动率为{formatted_value}，当前波动结构对模型打分偏正面，贡献约{formatted_contribution}。"
    if feature == "price_vs_ma10":
        return f"股价相对10日均线乖离为{formatted_value}，短线站上均线，拉动模型预测约{formatted_contribution}。"
    if feature == "price_vs_ma20":
        return f"股价相对20日均线乖离为{formatted_value}，中期趋势偏强，拉动模型预测约{formatted_contribution}。"
    if feature == "volume_ratio_5":
        return f"量比为{formatted_value}，量能与价格走势形成配合，拉动模型预测约{formatted_contribution}。"
    return f"{FEATURE_LABELS.get(feature, feature)}为{formatted_value}，对模型预测形成约{formatted_contribution}的正向贡献。"


def _risk_reason_text(feature: str, value: float, contribution: float) -> str:
    formatted_value = _format_feature_value(feature, value)
    formatted_contribution = _format_contribution_value(contribution)
    if feature == "ret_5":
        return f"近5日收益为{formatted_value}，短线节奏对模型打分有所拖累，影响约{formatted_contribution}。"
    if feature == "ret_10":
        return f"近10日收益为{formatted_value}，中段趋势力度不足，对模型打分拖累约{formatted_contribution}。"
    if feature == "volatility_10":
        return f"近10日波动率为{formatted_value}，波动偏大，对模型稳定性判断拖累约{formatted_contribution}。"
    if feature == "price_vs_ma10":
        return f"股价相对10日均线乖离为{formatted_value}，短线均线位置不占优，拖累约{formatted_contribution}。"
    if feature == "price_vs_ma20":
        return f"股价相对20日均线乖离为{formatted_value}，中期趋势支撑偏弱，拖累约{formatted_contribution}。"
    if feature == "volume_ratio_5":
        return f"量比为{formatted_value}，量能配合不足，对模型打分拖累约{formatted_contribution}。"
    return f"{FEATURE_LABELS.get(feature, feature)}为{formatted_value}，对模型预测形成约{formatted_contribution}的拖累。"


def _basis_text(feature: str, value: float, contribution: float) -> str:
    formatted_value = _format_feature_value(feature, value)
    formatted_contribution = _format_contribution_value(contribution)
    return f"{FEATURE_LABELS.get(feature, feature)} {formatted_value}，贡献 {formatted_contribution}"


def build_pick_explanations(model: LGBMRegressor, ranked_df: pd.DataFrame) -> pd.DataFrame:
    explained = ranked_df.copy().reset_index(drop=True)
    if explained.empty:
        explained["reason_summary"] = []
        explained["reason_tags"] = []
        explained["reason_texts"] = []
        explained["basis_items"] = []
        explained["risk_texts"] = []
        return explained

    contributions = model.predict(explained[FEATURE_COLUMNS], pred_contrib=True)
    contribution_array = np.asarray(contributions)
    if contribution_array.ndim == 1:
        contribution_array = contribution_array.reshape(1, -1)
    feature_contributions = contribution_array[:, : len(FEATURE_COLUMNS)]

    reason_summaries: list[str] = []
    reason_tags_list: list[list[str]] = []
    reason_texts_list: list[list[str]] = []
    basis_items_list: list[list[dict[str, Any]]] = []
    risk_texts_list: list[list[str]] = []

    for row_index, (_, row) in enumerate(explained.iterrows()):
        feature_items: list[dict[str, Any]] = []
        for feature_index, feature in enumerate(FEATURE_COLUMNS):
            value = float(row[feature]) if pd.notna(row[feature]) else None
            contribution = float(feature_contributions[row_index, feature_index])
            feature_items.append(
                {
                    "feature": feature,
                    "label": FEATURE_LABELS.get(feature, feature),
                    "value": value,
                    "value_display": _format_feature_value(feature, value),
                    "contribution": contribution,
                    "contribution_display": _format_contribution_value(contribution),
                    "is_positive": contribution >= 0,
                    "abs_contribution": abs(contribution),
                }
            )

        positive_items = [item for item in feature_items if item["contribution"] > 0]
        negative_items = [item for item in feature_items if item["contribution"] < 0]
        positive_items.sort(key=lambda item: item["contribution"], reverse=True)
        negative_items.sort(key=lambda item: item["contribution"])

        if not positive_items:
            positive_items = sorted(feature_items, key=lambda item: item["abs_contribution"], reverse=True)[:3]

        top_positive_items = positive_items[:3]
        top_negative_items = negative_items[:2]

        reason_tags = list(dict.fromkeys(_reason_tag(item["feature"], item["value"], item["contribution"]) for item in top_positive_items))
        if not reason_tags:
            reason_tags = ["综合因子占优"]

        reason_texts = [
            _positive_reason_text(item["feature"], item["value"], item["contribution"])
            for item in top_positive_items
        ]
        risk_texts = [
            _risk_reason_text(item["feature"], item["value"], item["contribution"])
            for item in top_negative_items
        ]

        basis_candidates = sorted(feature_items, key=lambda item: item["abs_contribution"], reverse=True)[:4]
        basis_items = [
            {
                "label": item["label"],
                "value_display": item["value_display"],
                "contribution_display": item["contribution_display"],
                "is_positive": item["contribution"] >= 0,
                "text": _basis_text(item["feature"], item["value"], item["contribution"]),
            }
            for item in basis_candidates
        ]

        reason_summary = "、".join(reason_tags[:3])

        reason_summaries.append(reason_summary)
        reason_tags_list.append(reason_tags)
        reason_texts_list.append(reason_texts)
        basis_items_list.append(basis_items)
        risk_texts_list.append(risk_texts)

    explained["reason_summary"] = reason_summaries
    explained["reason_tags"] = reason_tags_list
    explained["reason_texts"] = reason_texts_list
    explained["basis_items"] = basis_items_list
    explained["risk_texts"] = risk_texts_list
    return explained


def train_model(feature_df: pd.DataFrame, output_path: Path) -> dict:
    ordered = feature_df.sort_values("date").reset_index(drop=True)
    cutoff_index = int(len(ordered) * 0.8)
    train_df = ordered.iloc[:cutoff_index]
    test_df = ordered.iloc[cutoff_index:]

    model = LGBMRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=4,
        num_leaves=31,
        min_child_samples=20,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
    )
    model.fit(train_df[FEATURE_COLUMNS], train_df["future_return_5"])

    train_score = float(model.score(train_df[FEATURE_COLUMNS], train_df["future_return_5"]))
    test_score = float(model.score(test_df[FEATURE_COLUMNS], test_df["future_return_5"])) if not test_df.empty else train_score

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as fh:
        pickle.dump(model, fh)

    return {
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "train_r2": train_score,
        "test_r2": test_score,
    }


def load_model(model_path: Path) -> LGBMRegressor:
    with model_path.open("rb") as fh:
        return pickle.load(fh)


def score_snapshot(model: LGBMRegressor, snapshot_df: pd.DataFrame) -> pd.DataFrame:
    ranked = snapshot_df.copy()
    ranked["predicted_return_5"] = model.predict(ranked[FEATURE_COLUMNS])
    ranked["score"] = ranked["predicted_return_5"].rank(ascending=False, method="first")
    ranked = ranked.sort_values("predicted_return_5", ascending=False).reset_index(drop=True)
    return ranked
