from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.config import PAPER_PORTFOLIO_PATH
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


def default_portfolio_state() -> dict[str, Any]:
    return {
        "updated_at": None,
        "initial_cash": 1_000_000.0,
        "cash": 1_000_000.0,
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
    if not isinstance(base.get("settings"), dict):
        base["settings"] = dict(DEFAULT_SETTINGS)
    else:
        settings = dict(DEFAULT_SETTINGS)
        settings.update(base["settings"])
        base["settings"] = settings
    return base


def write_portfolio_state(payload: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(payload)
    enriched["updated_at"] = _now_iso()
    return write_json_file(PAPER_PORTFOLIO_PATH, enriched)


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
    if price is not None:
        return round(float(price), 2)

    quotes = merge_live_and_close([symbol])
    if not quotes:
        raise ValueError("unable to resolve trade price")
    quote = quotes[0]
    candidate = quote.get("price") if (price_mode or "live") == "live" else quote.get("fallback_close") or quote.get("price")
    if candidate is None:
        raise ValueError("trade price unavailable")
    return round(float(candidate), 2)


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
                "current_price": round(current_price, 2),
                "market_value": position_value,
                "unrealized_pnl": pnl,
                "quote": quote,
            }
        )

    realized_pnl = round(sum(_safe_float(item.get("realized_pnl")) for item in state.get("trades", [])), 2)
    cash = round(_safe_float(state.get("cash")), 2)
    equity = round(cash + market_value, 2)

    return {
        "updated_at": state.get("updated_at"),
        "initial_cash": round(_safe_float(state.get("initial_cash")), 2),
        "cash": cash,
        "market_value": round(market_value, 2),
        "equity": equity,
        "realized_pnl": realized_pnl,
        "unrealized_pnl": round(unrealized_pnl, 2),
        "positions": sorted(snapshot_positions, key=lambda item: item.get("symbol", "")),
        "recent_trades": list(reversed(state.get("trades", [])[-20:])),
        "trade_count": len(state.get("trades", [])),
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
    trade_price = _resolve_trade_price(normalized_symbol, price=price, price_mode=price_mode)
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
        "quantity": normalized_quantity,
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
