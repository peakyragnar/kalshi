from kalshi_data.operations.shadow_book import update_fills_and_settlements


class FakeClient:
    def paginate(self, *args, **kwargs):
        return iter(
            [
                [
                    {"yes_price": 5, "count": 4, "taker_side": "yes"},
                    {"yes_price": 5, "count": 8, "taker_side": "no"},
                ]
            ]
        )

    def get(self, *args, **kwargs):
        return {"market": {"status": "open", "no_bid": 95}}


class NoAggressorClient(FakeClient):
    def paginate(self, *args, **kwargs):
        return iter([[{"yes_price": 5, "count": 8, "taker_side": "no"}]])


def test_resting_no_fill_counts_only_yes_aggressor_volume():
    order = {
        "ticker": "KXTEST-26-A",
        "price_c": 95,
        "qty": 10,
        "placed_ts": "2026-07-17T12:00:00+00:00",
        "filled_qty": 0,
        "state": "resting",
        "result": None,
        "realized_usd": 0.0,
        "mark_c": None,
    }
    book = {"orders": [order]}

    update_fills_and_settlements(book, FakeClient())

    # Half of the four YES-aggressor contracts are assumed ahead of us.
    # NO-aggressor prints filled a resting YES maker and cannot fill this order.
    assert order["filled_qty"] == 2
    assert order["state"] == "partial"


def test_corrected_fill_reverts_stale_partial_order_to_resting():
    order = {
        "ticker": "KXTEST-26-B",
        "price_c": 95,
        "qty": 10,
        "placed_ts": "2026-07-17T12:00:00+00:00",
        "filled_qty": 4,
        "state": "partial",
        "result": None,
        "realized_usd": 0.0,
        "mark_c": None,
    }

    update_fills_and_settlements({"orders": [order]}, NoAggressorClient())

    assert order["filled_qty"] == 0
    assert order["state"] == "resting"
