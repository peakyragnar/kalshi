from kalshi_data.edge_health import CARRY, HURDLE, MIN_N, light


def test_green_when_bound_clears_hurdle():
    assert light(0.20, 0.05, 100) == "GREEN"  # 0.15 >= 0.07


def test_amber_when_bound_between_carry_and_hurdle():
    assert light(0.10, 0.05, 100) == "AMBER"  # 0.05 in [0.0325, 0.07)


def test_red_when_bound_below_carry():
    assert light(0.05, 0.04, 100) == "RED"  # 0.01 < 0.0325


def test_thin_when_sample_too_small_or_missing():
    assert light(0.50, 0.01, MIN_N - 1) == "THIN"
    assert light(None, None, 0) == "THIN"


def test_boundaries_are_exact():
    assert light(HURDLE + 0.01, 0.01, 100) == "GREEN"   # bound == hurdle exactly
    assert light(CARRY + 0.01, 0.01, 100) == "AMBER"    # bound == carry exactly
