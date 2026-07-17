import polars as pl

from kalshi_data.analysis.phase3_map import build_map


def _snaps(cat, bucket, horizon, period, n, ret, ev_prefix):
    return [
        {
            "category": cat,
            "bucket": bucket,
            "horizon_days": horizon,
            "period": period,
            "ann_no_carry": ret,
            "event_ticker": f"{ev_prefix}{i}",
        }
        for i in range(n)
    ]


def test_fat_cell_with_real_edge_qualifies():
    rows = (
        _snaps("Econ", "10-20", 30, "discovery", 80, 0.20, "d")
        + _snaps("Econ", "10-20", 30, "confirmation", 80, 0.20, "c")
    )
    out = build_map(pl.DataFrame(rows))
    cell = out.filter((pl.col("category") == "Econ") & (pl.col("bucket_label") == "10-20"))
    assert cell.row(0, named=True)["level"] == "fine"
    # zero variance -> SE 0 -> 0.20 - 0 > 0.07 in both periods
    assert cell.row(0, named=True)["qualified"] is True


def test_edge_below_hurdle_does_not_qualify():
    rows = (
        _snaps("Econ", "10-20", 30, "discovery", 80, 0.05, "d")
        + _snaps("Econ", "10-20", 30, "confirmation", 80, 0.05, "c")
    )
    out = build_map(pl.DataFrame(rows))
    assert out.filter(pl.col("qualified"))["qualified"].len() == 0


def test_thin_cell_merges_into_adjacent_bucket():
    # 30 snapshots in each of two adjacent fine buckets -> neither reaches 50
    # alone; together they clear it at the merged level
    rows = (
        _snaps("Econ", "10-20", 30, "discovery", 30, 0.2, "a")
        + _snaps("Econ", "20-30", 30, "discovery", 30, 0.2, "b")
        + _snaps("Econ", "10-20", 30, "confirmation", 20, 0.2, "c")
    )
    out = build_map(pl.DataFrame(rows))
    assert "fine" not in out["level"].to_list()
    merged = out.filter(pl.col("level") == "merged")
    assert len(merged) == 1
    assert merged.row(0, named=True)["bucket_label"] == "10-30"
    assert merged.row(0, named=True)["n_disc"] == 60


def test_still_thin_pools_across_categories():
    rows = (
        _snaps("Econ", "10-20", 30, "discovery", 30, 0.2, "a")
        + _snaps("Politics", "20-30", 30, "discovery", 30, 0.2, "b")
    )
    out = build_map(pl.DataFrame(rows))
    pooled = out.filter(pl.col("level") == "pooled")
    assert len(pooled) == 1
    assert pooled.row(0, named=True)["category"] == "(all)"
    assert pooled.row(0, named=True)["n_disc"] == 60


def test_confirmation_failure_blocks_qualification():
    rows = (
        _snaps("Econ", "10-20", 30, "discovery", 80, 0.30, "d")
        + _snaps("Econ", "10-20", 30, "confirmation", 80, 0.02, "c")
    )
    out = build_map(pl.DataFrame(rows))
    assert out.filter(pl.col("qualified"))["qualified"].len() == 0


def test_thin_confirmation_period_cannot_qualify_on_zero_variance():
    rows = (
        _snaps("Econ", "10-20", 30, "discovery", 80, 0.30, "d")
        + _snaps("Econ", "10-20", 30, "confirmation", 1, 0.30, "c")
    )
    out = build_map(pl.DataFrame(rows))
    assert out.filter(pl.col("qualified"))["qualified"].len() == 0
