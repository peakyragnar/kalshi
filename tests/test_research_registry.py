import json

import polars as pl
import pytest

from kalshi_data.analysis.atlas import evaluate_hypothesis, false_discovery_adjust
from kalshi_data.analysis.registry import load_registry


def test_registry_rejects_missing_precommit_fields(tmp_path):
    path = tmp_path / "hypotheses.yaml"
    path.write_text(json.dumps({"version": 1, "hypotheses": [{"id": "bad"}]}))
    with pytest.raises(ValueError, match="mechanism"):
        load_registry(path)


def test_registry_rejects_duplicate_ids(tmp_path):
    h = {
        "id": "same",
        "mechanism": "test",
        "kind": "cell_no_maker",
        "status": "registered",
        "retroactive": False,
        "filters": {},
        "contract": {
            "universe": "test", "signal": "test", "entry": "test", "exit": "test",
            "fees": "test", "spread": "test", "carry": "test", "benchmark": "test",
            "cluster_by": "event", "validation": "test", "capacity": "test",
            "tail_risk": "test",
        },
        "gate": {"hurdle": 0.07, "minimum_events": 2, "z": 2.0},
    }
    path = tmp_path / "hypotheses.yaml"
    path.write_text(json.dumps({"version": 1, "hypotheses": [h, h]}))
    with pytest.raises(ValueError, match="duplicate"):
        load_registry(path)


def test_registry_rejects_incomplete_economic_contract(tmp_path):
    h = {
        "id": "incomplete", "mechanism": "test", "kind": "documented",
        "status": "untested", "retroactive": False, "filters": {},
        "contract": {"universe": "deployment"},
        "gate": {"hurdle": 0.07, "minimum_events": 2, "z": 2.0},
    }
    path = tmp_path / "hypotheses.yaml"
    path.write_text(json.dumps({"version": 1, "hypotheses": [h]}))
    with pytest.raises(ValueError, match="contract missing"):
        load_registry(path)


def _joined(period, event, price, result_yes, category="Politics", label="T-30d"):
    return {
        "period": period,
        "event_ticker": event,
        "ticker": f"{event}-{price}",
        "category": category,
        "decision_label": label,
        "yes_price_cents": price,
        "fee_type": "quadratic",
        "result_yes": result_yes,
        "hold_seconds": 30 * 86400,
        "decision_time_trustworthy": True,
    }


def test_atlas_gate_requires_every_period_and_independent_events():
    rows = []
    for p in ("early", "middle", "recent"):
        rows += [_joined(p, f"{p}-{i}", 5, 0) for i in range(4)]
    spec = {
        "id": "edge",
        "kind": "cell_no_maker",
        "filters": {"categories": ["Politics"], "decision_labels": ["T-30d"], "yes_price_min": 1, "yes_price_max": 5},
        "gate": {"hurdle": 0.07, "minimum_events": 4, "z": 2.0},
    }
    result, periods = evaluate_hypothesis(pl.DataFrame(rows), spec)
    assert result["historically_qualified"] is True
    assert len(periods) == 3

    weak = pl.DataFrame(rows).with_columns(
        pl.when(pl.col("period") == "recent").then(pl.lit(1)).otherwise(pl.col("result_yes")).alias("result_yes")
    )
    result, _ = evaluate_hypothesis(weak, spec)
    assert result["historically_qualified"] is False


def test_benjamini_hochberg_is_monotone_and_penalizes_search_count():
    out = false_discovery_adjust([0.001, 0.02, 0.03, 0.9])
    assert out == pytest.approx([0.004, 0.04, 0.04, 0.9])
    assert out == sorted(out)
