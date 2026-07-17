"""Shadow book: the paper-trading experiment that measures fill rates.

Places simulated resting NO orders on every GREEN candidate per the playbook
sizing rules, fills them against the REAL trade tape (50% of contracts printed
at or through our price after placement - queue position unknown, so half the
prints are assumed ahead of us), and realizes P&L at REAL settlements.

Purpose: (1) visual book on the dashboard; (2) the deployment-ratio / fill-rate
data the return model lacks; (3) the control group once real money runs.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .client import KalshiClient
from .parse import cents

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
BOOK_FILE = DATA_DIR / "shadow_book.json"

BOOK_USD = 10_000.0
UNIT_USD = 250.0
CELL_MULT = {"Politics": 1.0, "Financials": 0.5}
FILL_SHARE = 0.5


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _event(ticker: str) -> str:
    return ticker.rsplit("-", 1)[0]


def load_book() -> dict:
    if BOOK_FILE.exists():
        return json.loads(BOOK_FILE.read_text())
    return {"book_usd": BOOK_USD, "created": _now().isoformat(), "orders": []}


def place_from_candidates(book: dict) -> int:
    cands = json.loads((DATA_DIR / "candidates_today.json").read_text())
    have_events = {_event(o["ticker"]) for o in book["orders"]}
    placed = 0
    for c in cands:
        if c["rulebook"] != "GREEN":
            continue
        ev = _event(c["ticker"])
        if ev in have_events:
            continue
        dollars = UNIT_USD * CELL_MULT[c["category"]]
        price_c = int(c["rest_no_at_c"])
        qty = int(dollars / (price_c / 100))
        book["orders"].append(
            {
                "ticker": c["ticker"],
                "event": ev,
                "category": c["category"],
                "title": c["title"],
                "price_c": price_c,
                "qty": qty,
                "placed_ts": _now().isoformat(timespec="seconds"),
                "filled_qty": 0,
                "state": "resting",
                "result": None,
                "realized_usd": 0.0,
                "mark_c": None,
            }
        )
        have_events.add(ev)
        placed += 1
    return placed


def update_fills_and_settlements(book: dict, client: KalshiClient) -> None:
    for o in book["orders"]:
        if o["state"] in ("settled", "cancelled"):
            continue
        placed = dt.datetime.fromisoformat(o["placed_ts"])
        max_yes = 100 - o["price_c"]

        printed = 0.0
        for page in client.paginate(
            "/markets/trades", "trades", ticker=o["ticker"], min_ts=int(placed.timestamp())
        ):
            for t in page:
                p = cents(t, "yes_price")
                if p is not None and p <= max_yes:
                    printed += float(t.get("count") or t.get("count_fp") or 0)
        fillable = int(printed * FILL_SHARE)
        o["filled_qty"] = min(o["qty"], fillable)
        if o["filled_qty"] > 0 and o["state"] == "resting":
            o["state"] = "partial" if o["filled_qty"] < o["qty"] else "filled"

        m = client.get(f"/markets/{o['ticker']}").get("market", {})
        status = m.get("status")
        if status in ("settled", "finalized") and m.get("result") in ("yes", "no"):
            o["result"] = m["result"]
            payout = 100 if m["result"] == "no" else 0
            o["realized_usd"] = round(o["filled_qty"] * (payout - o["price_c"]) / 100, 2)
            o["state"] = "settled"
        elif status not in ("active", "open"):
            if o["filled_qty"] == 0:
                o["state"] = "cancelled"
        else:
            bid = cents(m, "no_bid")
            o["mark_c"] = bid if bid else o["price_c"]


def stats(book: dict) -> dict:
    orders = book["orders"]
    deployed = sum(o["filled_qty"] * o["price_c"] / 100 for o in orders if o["state"] in ("partial", "filled"))
    resting = sum((o["qty"] - o["filled_qty"]) * o["price_c"] / 100 for o in orders if o["state"] in ("resting", "partial"))
    realized = sum(o["realized_usd"] for o in orders)
    unreal = sum(
        o["filled_qty"] * ((o["mark_c"] or o["price_c"]) - o["price_c"]) / 100
        for o in orders
        if o["state"] in ("partial", "filled")
    )
    return {
        "n_orders": len(orders),
        "n_open_positions": sum(1 for o in orders if o["state"] in ("partial", "filled")),
        "deployed_usd": round(deployed, 2),
        "resting_usd": round(resting, 2),
        "cash_usd": round(book["book_usd"] - deployed, 2),
        "deployed_pct": round(deployed / book["book_usd"] * 100, 1),
        "realized_usd": round(realized, 2),
        "unrealized_usd": round(unreal, 2),
    }


def run() -> None:
    book = load_book()
    placed = place_from_candidates(book)
    client = KalshiClient(rps=5)
    update_fills_and_settlements(book, client)
    book["stats"] = stats(book)
    book["updated"] = _now().isoformat(timespec="seconds")
    BOOK_FILE.write_text(json.dumps(book, indent=1))
    s = book["stats"]
    print(
        f"shadow book: +{placed} new orders | {s['n_orders']} total | "
        f"deployed ${s['deployed_usd']:,.0f} ({s['deployed_pct']}%) | "
        f"realized ${s['realized_usd']:,.2f}"
    )


if __name__ == "__main__":
    run()
