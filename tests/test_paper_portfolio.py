from __future__ import annotations

from pathlib import Path

import pytest

from app.services import paper_portfolio


@pytest.fixture()
def temp_portfolio_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "paper_portfolio.json"
    monkeypatch.setattr(paper_portfolio, "PAPER_PORTFOLIO_PATH", target)
    return target


def test_reset_portfolio_uses_default_cash(temp_portfolio_path: Path) -> None:
    snapshot = paper_portfolio.reset_portfolio()
    assert snapshot["initial_cash"] > 0
    assert snapshot["cash"] == snapshot["initial_cash"]
    assert snapshot["positions"] == []


def test_update_portfolio_settings(temp_portfolio_path: Path) -> None:
    paper_portfolio.reset_portfolio(initial_cash=500000)
    snapshot = paper_portfolio.update_portfolio_settings(
        {
            "commission_rate": 0.0005,
            "min_commission": 3,
            "stamp_duty_rate": 0.001,
            "slippage_bps": 5,
        }
    )
    assert snapshot["settings"]["commission_rate"] == 0.0005
    assert snapshot["settings"]["slippage_bps"] == 5


def test_import_export_roundtrip(temp_portfolio_path: Path) -> None:
    paper_portfolio.reset_portfolio(initial_cash=321000)
    exported = paper_portfolio.export_portfolio_state()
    snapshot = paper_portfolio.import_portfolio_state(exported)
    assert snapshot["initial_cash"] == 321000
    assert exported["schema_version"] == "1.1"


def test_manual_price_requires_price(temp_portfolio_path: Path) -> None:
    with pytest.raises(ValueError):
        paper_portfolio._resolve_trade_price("600519", price=None, price_mode="manual")
