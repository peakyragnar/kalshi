import json

from kalshi_data.operations import dashboard


def test_dashboard_reports_real_resting_orders_and_omits_stale_open_items(tmp_path, monkeypatch):
    state = tmp_path / "state"
    state.mkdir()
    candidates_path = state / "candidates.json"
    candidates_path.write_text("[]")
    portfolio = {
        "available": True,
        "ts": "2026-07-17T17:00:00+00:00",
        "cash_usd": 3030.05,
        "exposure_usd": 0.0,
        "equity_usd": 3030.05,
        "baseline_usd": 3030.05,
        "since": "2026-07-17",
        "pnl_usd": 0.0,
        "sizing": {"politics_unit_usd": 75.75, "financials_unit_usd": 37.88},
        "positions": [],
        "resting_orders": [
            {"ticker": f"KXTEST-{i}", "side": "no", "price_c": 95, "resting": 10}
            for i in range(11)
        ],
        "recent_settlements": [],
    }
    (state / "portfolio.json").write_text(json.dumps(portfolio))

    books = tmp_path / "books"
    books.mkdir()
    logs = tmp_path / "logs"
    logs.mkdir()
    checkpoints = state / "checkpoints"
    checkpoints.mkdir()
    verdicts = tmp_path / "rulebooks.json"
    verdicts.write_text("{}")
    out = tmp_path / "dashboard"

    monkeypatch.setattr(dashboard, "STATE", state)
    monkeypatch.setattr(dashboard, "CANDIDATES", candidates_path)
    monkeypatch.setattr(dashboard, "BOOKS", books)
    monkeypatch.setattr(dashboard, "LOGS", logs)
    monkeypatch.setattr(dashboard, "CHECKPOINTS", checkpoints)
    monkeypatch.setattr(dashboard, "EDGE_HISTORY", state / "edge.jsonl")
    monkeypatch.setattr(dashboard, "RULEBOOK_VERDICTS", verdicts)
    monkeypatch.setattr(dashboard, "SHADOW_BOOK", state / "shadow.json")
    monkeypatch.setattr(dashboard, "TAIL_SIGNALS", state / "tails.json")
    monkeypatch.setattr(dashboard, "OUT", out)

    path = dashboard.run()
    html = path.read_text()

    assert "11 live orders resting — no filled positions" in html
    assert "deployment status: <b>diligence phase — no live positions</b>" not in html
    assert "Escrow-carry support ticket" not in html
    assert "Forward-validation weekly job" not in html
