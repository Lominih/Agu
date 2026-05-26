from __future__ import annotations

from datetime import datetime
import json
from typing import Any

from app.core.config import PAPER_PORTFOLIO_PATH, PORTFOLIO_DEFAULT_CASH
from app.services.market_watch import merge_live_and_close, normalize_symbol
from app.services.state_store import read_json_file, write_json_file


DEFAULT_SETTINGS = {
    "commission_rate": 0.0003,
    "min_commission": 5.0,
    "stamp_duty_rate": 0.001,
    "slippage_bps": 0.0,
}


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _normalize_settings(settings: dict[str, Any] | None) -> dict[str, float]:
    normalized = dict(DEFAULT_SETTINGS)
    if isinstance(settings, dict):
        for key, default in DEFAULT_SETTINGS.items():
            if settings.get(key) is None:
                continue
            normalized[key] = max(0.0, _safe_float(settings.get(key), default))
    return normalized


def default_portfolio_state() -> dict[str, Any]:
    return {
        "updated_at": None,
        "initial_cash": PORTFOLIO_DEFAULT_CASH,
        "cash": PORTFOLIO_DEFAULT_CASH,
        "positions": [],
        "trades": [],
        "settings": dict(DEFAULT_SETTINGS),
    }


def read_portfolio_state() -> dict[str, Any]:
    payload = read_json_file(PAPER_PORTFOLIO_PATH, default_factory=default_portfolio_state)
    base = default_portfolio_state()
    if isinstance(payload, dict):
        base.update(payload)
    if not isinstance(base.get("positions"), list):
        base["positions"] = []
    if not isinstance(base.get("trades"), list):
        base["trades"] = []
    base["settings"] = _normalize_settings(base.get("settings"))
    return base


def write_portfolio_state(payload: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(payload)
    enriched["updated_at"] = _now_iso()
    return write_json_file(PAPER_PORTFOLIO_PATH, enriched)


def update_portfolio_settings(settings_patch: dict[str, Any]) -> dict[str, Any]:
    state = read_portfolio_state()
    settings = dict(state.get("settings") or DEFAULT_SETTINGS)
    for key in DEFAULT_SETTINGS:
        if key in settings_patch and settings_patch[key] is not None:
            settings[key] = settings_patch[key]
    state["settings"] = _normalize_settings(settings)
    write_portfolio_state(state)
    return get_portfolio_snapshot()


def export_portfolio_state() -> dict[str, Any]:
    state = read_portfolio_state()
    return {
        "exported_at": _now_iso(),
        "schema_version": "1.1",
        "portfolio": state,
    }


def import_portfolio_state(payload: dict[str, Any]) -> dict[str, Any]:
    portfolio = payload.get("portfolio") if isinstance(payload, dict) and "portfolio" in payload else payload.get("state") if isinstance(payload, dict) and "state" in payload else payload
    if not isinstance(portfolio, dict):
        raise ValueError("invalid portfolio payload")
    merged = default_portfolio_state()
    merged.update(portfolio)
    if not isinstance(merged.get("positions"), list):
        raise ValueError("positions must be a list")
    if not isinstance(merged.get("trades"), list):
        raise ValueError("trades must be a list")
    merged["initial_cash"] = round(_safe_float(merged.get("initial_cash"), 1_000_000.0), 2)
    merged["cash"] = round(_safe_float(merged.get("cash"), merged["initial_cash"]), 2)
    merged["settings"] = _normalize_settings(merged.get("settings"))
    normalized_positions = []
    for item in merged.get("positions", []):
        if not isinstance(item, dict):
            continue
        symbol = normalize_symbol(item.get("symbol"))
        quantity = int(_safe_float(item.get("quantity"), 0))
        if not symbol or quantity <= 0:
            continue
        normalized_positions.append(
            {
                **item,
                "symbol": symbol,
                "name": item.get("name") or symbol,
                "quantity": quantity,
                "avg_cost": round(_safe_float(item.get("avg_cost")), 4),
                "opened_at": item.get("opened_at") or _now_iso(),
            }
        )
    normalized_trades = []
    for item in merged.get("trades", []):
        if not isinstance(item, dict):
            continue
        symbol = normalize_symbol(item.get("symbol"))
        quantity = int(_safe_float(item.get("quantity"), 0))
        if not symbol or quantity <= 0:
            continue
        side = str(item.get("side") or "buy").strip().lower()
        if side not in {"buy", "sell"}:
            side = "buy"
        price = round(_safe_float(item.get("price")), 2)
        requested_price = round(_safe_float(item.get("requested_price"), price), 2)
        gross_amount = round(_safe_float(item.get("gross_amount"), price * quantity), 2)
        commission = round(_safe_float(item.get("commission")), 2)
        stamp_duty = round(_safe_float(item.get("stamp_duty")), 2)
        fees = round(_safe_float(item.get("fees"), commission + stamp_duty), 2)
        realized_pnl = round(_safe_float(item.get("realized_pnl")), 2)
        normalized_trades.append(
            {
                **item,
                "executed_at": item.get("executed_at") or _now_iso(),
                "symbol": symbol,
                "name": item.get("name") or symbol,
                "side": side,
                "status": item.get("status") or "filled",
                "quantity": quantity,
                "requested_price": requested_price,
                "price": price,
                "gross_amount": gross_amount,
                "commission": commission,
                "stamp_duty": stamp_duty,
                "fees": fees,
                "net_amount": round(_safe_float(item.get("net_amount"), gross_amount + fees if side == "buy" else gross_amount - fees), 2),
                "realized_pnl": realized_pnl,
                "price_mode": item.get("price_mode") or "live",
            }
        )
    merged["positions"] = normalized_positions
    merged["trades"] = normalized_trades
    write_portfolio_state(merged)
    return get_portfolio_snapshot()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _calculate_commission(amount: float, settings: dict[str, Any]) -> float:
    commission = amount * _safe_float(settings.get("commission_rate"))
    return max(_safe_float(settings.get("min_commission"), 5.0), round(commission, 2))


def _calculate_stamp_duty(amount: float, side: str, settings: dict[str, Any]) -> float:
    if side != "sell":
        return 0.0
    return round(amount * _safe_float(settings.get("stamp_duty_rate")), 2)


def _resolve_trade_price(symbol: str, price: float | None, price_mode: str | None) -> float:
    normalized_mode = (price_mode or "live").strip().lower()
    if normalized_mode == "manual":
        if price is None:
            raise ValueError("manual price mode requires price")
        return round(float(price), 2)
    if price is not None:
        return round(float(price), 2)

    quotes = merge_live_and_close([symbol])
    if not quotes:
        raise ValueError("unable to resolve trade price")
    quote = quotes[0]
    candidate = quote.get("price") if normalized_mode == "live" else quote.get("fallback_close") or quote.get("price")
    if candidate is None:
        raise ValueError("trade price unavailable")
    return round(float(candidate), 2)


def _apply_slippage(price: float, side: str, settings: dict[str, Any]) -> float:
    slippage_bps = _safe_float(settings.get("slippage_bps"))
    if slippage_bps <= 0:
        return round(price, 2)
    factor = 1 + slippage_bps / 10000 if side == "buy" else 1 - slippage_bps / 10000
    return round(price * factor, 2)


def _find_position(positions: list[dict[str, Any]], symbol: str) -> dict[str, Any] | None:
    normalized = normalize_symbol(symbol)
    return next((item for item in positions if normalize_symbol(item.get("symbol")) == normalized), None)


def get_portfolio_snapshot() -> dict[str, Any]:
    state = read_portfolio_state()
    positions = state.get("positions", [])
    symbols = [normalize_symbol(item.get("symbol")) for item in positions if item.get("symbol")]
    quote_map = {item["symbol"]: item for item in merge_live_and_close(symbols)} if symbols else {}

    snapshot_positions: list[dict[str, Any]] = []
    market_value = 0.0
    unrealized_pnl = 0.0

    for item in positions:
        symbol = normalize_symbol(item.get("symbol"))
        quantity = int(item.get("quantity") or 0)
        if quantity <= 0:
            continue
        avg_cost = round(_safe_float(item.get("avg_cost")), 2)
        cost_amount = round(avg_cost * quantity, 2)
        quote = quote_map.get(symbol, {})
        current_price = _safe_float(quote.get("price") or quote.get("fallback_close"), avg_cost)
        position_value = round(current_price * quantity, 2)
        pnl = round((current_price - avg_cost) * quantity, 2)
        market_value += position_value
        unrealized_pnl += pnl
        snapshot_positions.append(
            {
                **item,
                "symbol": symbol,
                "avg_cost": avg_cost,
                "cost_amount": cost_amount,
                "current_price": round(current_price, 2),
                "market_value": position_value,
                "unrealized_pnl": pnl,
                "weight_pct": 0.0,
                "quote": quote,
            }
        )

    trades = list(state.get("trades", []))
    realized_pnl = round(sum(_safe_float(item.get("realized_pnl")) for item in trades), 2)
    cash = round(_safe_float(state.get("cash")), 2)
    equity = round(cash + market_value, 2)
    buy_count = sum(1 for item in trades if str(item.get("side") or "").strip().lower() == "buy")
    sell_count = sum(1 for item in trades if str(item.get("side") or "").strip().lower() == "sell")
    closed_trades = [item for item in trades if str(item.get("side") or "").strip().lower() == "sell"]
    winning_trade_count = sum(1 for item in closed_trades if _safe_float(item.get("realized_pnl")) > 0)
    losing_trade_count = sum(1 for item in closed_trades if _safe_float(item.get("realized_pnl")) < 0)
    win_rate_pct = round(winning_trade_count / len(closed_trades) * 100, 2) if closed_trades else 0.0
    avg_fee_per_trade = round(sum(_safe_float(item.get("fees")) for item in trades) / len(trades), 2) if trades else 0.0

    for item in snapshot_positions:
        item["weight_pct"] = round(item["market_value"] / equity * 100, 2) if equity else 0.0

    return {
        "updated_at": state.get("updated_at"),
        "initial_cash": round(_safe_float(state.get("initial_cash")), 2),
        "cash": cash,
        "market_value": round(market_value, 2),
        "equity": equity,
        "realized_pnl": realized_pnl,
        "unrealized_pnl": round(unrealized_pnl, 2),
        "position_count": len(snapshot_positions),
        "cash_ratio": round(cash / equity, 4) if equity else 0.0,
        "position_ratio": round(market_value / equity, 4) if equity else 0.0,
        "cash_ratio_pct": round(cash / equity * 100, 2) if equity else 0.0,
        "position_ratio_pct": round(market_value / equity * 100, 2) if equity else 0.0,
        "total_fees": round(sum(_safe_float(item.get("fees")) for item in trades), 2),
        "average_fee_per_trade": avg_fee_per_trade,
        "trade_count": len(trades),
        "buy_count": buy_count,
        "sell_count": sell_count,
        "winning_trade_count": winning_trade_count,
        "losing_trade_count": losing_trade_count,
        "win_rate_pct": win_rate_pct,
        "positions": sorted(snapshot_positions, key=lambda item: item.get("symbol", "")),
        "recent_trades": list(reversed(trades[-20:])),
        "settings": state.get("settings", dict(DEFAULT_SETTINGS)),
    }


def place_order(
    *,
    symbol: str,
    side: str,
    quantity: int,
    price: float | None = None,
    price_mode: str | None = "live",
    name: str | None = None,
) -> dict[str, Any]:
    normalized_symbol = normalize_symbol(symbol)
    normalized_side = (side or "").strip().lower()
    if normalized_side not in {"buy", "sell"}:
        raise ValueError("side must be buy or sell")
    normalized_quantity = int(quantity or 0)
    if normalized_quantity <= 0:
        raise ValueError("quantity must be positive")
    if normalized_quantity % 100 != 0:
        raise ValueError("quantity must be a board lot of 100 shares")

    state = read_portfolio_state()
    settings = state.get("settings", dict(DEFAULT_SETTINGS))
    requested_price = _resolve_trade_price(normalized_symbol, price=price, price_mode=price_mode)
    trade_price = _apply_slippage(requested_price, normalized_side, settings)
    gross_amount = round(trade_price * normalized_quantity, 2)
    commission = _calculate_commission(gross_amount, settings)
    stamp_duty = _calculate_stamp_duty(gross_amount, normalized_side, settings)
    total_fees = round(commission + stamp_duty, 2)
    positions = list(state.get("positions", []))
    cash = round(_safe_float(state.get("cash")), 2)
    position = _find_position(positions, normalized_symbol)

    realized_pnl = 0.0
    if normalized_side == "buy":
        total_cost = round(gross_amount + total_fees, 2)
        if cash < total_cost:
            raise ValueError("insufficient cash")
        cash = round(cash - total_cost, 2)
        if position is None:
            position = {
                "symbol": normalized_symbol,
                "name": name or normalized_symbol,
                "quantity": normalized_quantity,
                "avg_cost": round(total_cost / normalized_quantity, 4),
                "opened_at": _now_iso(),
            }
            positions.append(position)
        else:
            old_qty = int(position.get("quantity") or 0)
            old_cost = _safe_float(position.get("avg_cost")) * old_qty
            new_qty = old_qty + normalized_quantity
            position["quantity"] = new_qty
            position["name"] = name or position.get("name") or normalized_symbol
            position["avg_cost"] = round((old_cost + total_cost) / max(new_qty, 1), 4)
    else:
        if position is None or int(position.get("quantity") or 0) < normalized_quantity:
            raise ValueError("insufficient position")
        proceeds = round(gross_amount - total_fees, 2)
        cash = round(cash + proceeds, 2)
        avg_cost = _safe_float(position.get("avg_cost"))
        realized_pnl = round((trade_price - avg_cost) * normalized_quantity - total_fees, 2)
        remaining = int(position.get("quantity") or 0) - normalized_quantity
        if remaining <= 0:
            positions = [item for item in positions if normalize_symbol(item.get("symbol")) != normalized_symbol]
        else:
            position["quantity"] = remaining

    trade_record = {
        "executed_at": _now_iso(),
        "symbol": normalized_symbol,
        "name": name or (position.get("name") if position else normalized_symbol) or normalized_symbol,
        "side": normalized_side,
        "status": "filled",
        "quantity": normalized_quantity,
        "requested_price": requested_price,
        "price": trade_price,
        "gross_amount": gross_amount,
        "commission": commission,
        "stamp_duty": stamp_duty,
        "fees": total_fees,
        "net_amount": round(gross_amount + total_fees, 2) if normalized_side == "buy" else round(gross_amount - total_fees, 2),
        "realized_pnl": realized_pnl,
        "price_mode": price_mode or "live",
    }

    updated_state = {
        **state,
        "cash": cash,
        "positions": positions,
        "trades": [*state.get("trades", []), trade_record],
    }
    write_portfolio_state(updated_state)
    return {
        "message": f"{normalized_symbol} {normalized_side} order filled",
        "trade": trade_record,
        "snapshot": get_portfolio_snapshot(),
    }


def reset_portfolio(initial_cash: float | None = None) -> dict[str, Any]:
    state = default_portfolio_state()
    if initial_cash is not None:
        state["initial_cash"] = round(float(initial_cash), 2)
        state["cash"] = round(float(initial_cash), 2)
    write_portfolio_state(state)
    return get_portfolio_snapshot()
