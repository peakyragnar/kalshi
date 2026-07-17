import math

import polars as pl

from kalshi_data.analysis.screens import bucket_label, cluster_se, maker_fee_cents, taker_fee_cents


def test_taker_fee_matches_published_examples():
    assert taker_fee_cents(50) == 2  # 0.07*0.5*0.5 = $0.0175 -> ceil $0.02
    assert taker_fee_cents(1) == 1  # 0.000693 -> ceil to 1 cent
    assert taker_fee_cents(99) == 1
    assert taker_fee_cents(30) == 2  # 0.07*0.3*0.7 = $0.0147 -> 2 cents


def test_maker_fee_zero_unless_series_charges():
    assert maker_fee_cents(50, "quadratic") == 0
    assert maker_fee_cents(50, "") == 0
    assert maker_fee_cents(50, "quadratic_with_maker_fees") == 1  # 25% of taker


def test_bucket_edges():
    assert bucket_label(1) == "01-5"
    assert bucket_label(4) == "01-5"
    assert bucket_label(5) == "05-10"
    assert bucket_label(94) == "90-95"
    assert bucket_label(95) == "95-99"
    assert bucket_label(99) == "95-99"


def test_cluster_se_collapses_to_iid_when_clusters_are_singletons():
    x = pl.Series([1.0, 2.0, 3.0, 4.0])
    c = pl.Series(["a", "b", "c", "d"])
    # CR0 with singleton clusters = sqrt(sum resid^2)/n = population sd / sqrt(n)
    expected = math.sqrt(sum((v - 2.5) ** 2 for v in [1, 2, 3, 4])) / 4
    assert abs(cluster_se(x, c) - expected) < 1e-12


def test_cluster_se_grows_with_within_cluster_correlation():
    # same values, but perfectly correlated pairs share a cluster
    x = pl.Series([1.0, 1.0, 4.0, 4.0])
    iid = cluster_se(x, pl.Series(["a", "b", "c", "d"]))
    clustered = cluster_se(x, pl.Series(["a", "a", "b", "b"]))
    assert clustered > iid
