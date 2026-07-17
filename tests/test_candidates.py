import json

import polars as pl

from kalshi_data.operations import candidates


class EmptyClient:
    def __init__(self, *args, **kwargs):
        pass

    def paginate(self, *args, **kwargs):
        return iter(())


def test_zero_candidate_day_writes_valid_empty_outputs(tmp_path, monkeypatch):
    series_path = tmp_path / "series.parquet"
    pl.DataFrame(
        [
            {
                "ticker": "KXEMPTY",
                "title": "No open markets today",
                "category": "Politics",
                "tier": "deployment",
            }
        ]
    ).write_parquet(series_path)

    report_dir = tmp_path / "reports"
    state_path = tmp_path / "state" / "candidates_today.json"
    state_path.parent.mkdir()
    monkeypatch.setattr(candidates, "SERIES", series_path)
    monkeypatch.setattr(candidates, "REPORTS_DIR", report_dir)
    monkeypatch.setattr(candidates, "CANDIDATES", state_path)
    monkeypatch.setattr(candidates, "KalshiClient", EmptyClient)

    result = candidates.run()

    assert result.is_empty()
    assert result.columns == [
        "category",
        "series",
        "ticker",
        "title",
        "days_to_close",
        "yes_ask_c",
        "rest_no_at_c",
        "volume",
        "rulebook",
    ]
    assert json.loads(state_path.read_text()) == []
    assert "0 candidates" in (report_dir / "candidates_today.md").read_text()
