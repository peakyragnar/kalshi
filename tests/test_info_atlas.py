import json

from kalshi_data.analysis.info_atlas import (
    UNKNOWN_FLOOR,
    geometric_mean,
    host_scores,
    tail_gap_score,
)


def _sources(*urls):
    return json.dumps([{"url": u} for u in urls])


def test_host_scores_catalog_hit_and_subdomains():
    up, pit, note = host_scores(_sources("https://www.weather.gov/nyc"))
    assert (up, pit) == (1.0, 1.0)
    up, pit, _ = host_scores(_sources("https://efts.sec.gov/search"))
    assert (up, pit) == (0.9, 1.0)


def test_host_scores_unknown_floor_not_zero():
    up, pit, note = host_scores(_sources("https://example-blog.com/post"))
    assert (up, pit) == (UNKNOWN_FLOOR, UNKNOWN_FLOOR)
    assert "judgment pass" in note
    assert host_scores(None)[0] == UNKNOWN_FLOOR


def test_host_scores_takes_best_of_multiple_sources():
    up, pit, _ = host_scores(_sources("https://cnn.com/x", "https://noaa.gov/y"))
    assert (up, pit) == (1.0, 1.0)


def test_fed_is_cataloged_as_professionals_game():
    up, _, note = host_scores(_sources("https://www.federalreserve.gov/press"))
    assert up == 0.3
    assert "professionals" in note


def test_tail_gap_score_floors_caps_and_thin_evidence():
    assert tail_gap_score(0.03, 500) == 0.6          # 0.03 / 0.05 cap
    assert tail_gap_score(0.20, 500) == 1.0          # capped
    assert tail_gap_score(-0.02, 500) == 0.0         # underpriced tails: no maker wage
    assert tail_gap_score(0.03, 50) == UNKNOWN_FLOOR  # thin evidence is not a verdict
    assert tail_gap_score(None, 500) == UNKNOWN_FLOOR


def test_geometric_mean_zero_gates():
    assert geometric_mean([1.0, 1.0, 0.0]) == 0.0
    assert abs(geometric_mean([0.5, 0.5, 0.5]) - 0.5) < 1e-12
