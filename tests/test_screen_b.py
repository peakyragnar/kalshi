import polars as pl

from kalshi_data.screen_b import residualize


def _df(rows):
    return pl.DataFrame(rows)


def test_residualize_recovers_planted_term_premium():
    # two groups with different levels, same +2.0 step from horizon 30 to 90
    rows = []
    for g, base in (("a", 1.0), ("b", 10.0)):
        for h, v in ((30, base), (90, base + 2.0)):
            rows.append({"category": g, "bucket": "x", "horizon_days": h, "ann_no": v})
    out = residualize(_df(rows), ["category", "bucket"])
    prof = out.group_by("horizon_days").agg(pl.col("resid").mean()).sort("horizon_days")
    r30, r90 = prof["resid"].to_list()
    assert abs((r90 - r30) - 2.0) < 1e-12  # slope survives, levels are gone


def test_residualize_drops_single_horizon_groups():
    rows = [
        {"category": "a", "bucket": "x", "horizon_days": 30, "ann_no": 5.0},
        {"category": "a", "bucket": "x", "horizon_days": 90, "ann_no": 7.0},
        {"category": "lonely", "bucket": "x", "horizon_days": 30, "ann_no": 99.0},
    ]
    out = residualize(_df(rows), ["category", "bucket"])
    assert "lonely" not in out["category"].to_list()


def test_residual_means_are_zero_within_group():
    rows = [
        {"category": "a", "bucket": "x", "horizon_days": 30, "ann_no": 3.0},
        {"category": "a", "bucket": "x", "horizon_days": 90, "ann_no": 9.0},
    ]
    out = residualize(_df(rows), ["category", "bucket"])
    assert abs(float(out["resid"].sum())) < 1e-12
