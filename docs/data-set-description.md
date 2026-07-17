# Dataset Description

What we hold from Kalshi, how it grows, and which parts could never be rebuilt.
Census as of 2026-07-17; sizes grow daily. Everything lives in `data/`
(gitignored); every table except the order books is fully reproducible from
Kalshi's free public API via the commands in README.md.

## The stores

| Store | Size | Rows | Span | Grows |
|---|---|---|---|---|
| `raw/series.parquet` | <1MB | 11,486 series — the full exchange catalog, tiered (deployment / instrumentation / excluded / review) | all-time | on re-run |
| `raw/markets/` | 47MB | 2,731,998 settled deployment-tier markets: outcome, timestamps, per-series fees | Jul 2021 → present | **static — daily incremental ingest is Track 1 of edge-program-plan.md (not yet built)** |
| `raw/trades/` | 1.5GB | 46,892,108 trades with price, size, timestamp, **aggressor side**, for the 376,557 markets that lived ≥7d and traded | Jun 2021 → Jul 2026 | same as markets |
| `derived/snapshots.parquet` | 8MB | 429,761 rows: last price + staleness + cumulative volume + outcome at T−7/30/90/180/365d | same | rebuilt from the above |
| `capture/books/` | 40MB | 169,282 order-book depth snapshots (top 5 levels, both sides, ~24k open markets) | **2026-07-15 → now** | **live: 4×/day via launchd** |
| `state/candidates_today.json` | — | daily qualifying-market list with rulebook stamps | daily | **live: 13:15 daily** |

Scale reference: the markets table represents ~6.17 billion contracts of
lifetime volume — the full five-year economic history of every category in the
deployment universe.

## Deliberate scope boundaries

- **Deployment tier only** for markets/trades (econ, politics, climate,
  financials, world, companies, sci-tech, commodities, health). Sports and
  crypto-ladder tape not pulled (planned as a *sampled* instrumentation
  backfill); `KXMVE*` parlays excluded at ingest (~500k junk rows/day avoided).
- **Trades only where they can matter**: markets that lived <7 days can never
  contribute a snapshot at the shortest horizon, so their tape buys nothing.
- Voided markets never appear under `status=settled` and are therefore absent —
  void risk is a rulebook diligence item, not a data column.

## The two kinds of data (the distinction that matters)

**Backfillable** — markets, trades, candles-era prices. Kalshi serves the full
history (`/historical/*` before the rolling cutoff, live endpoints after).
Losing these costs a re-download, nothing more. Anyone can build this table;
it is a commodity.

**Capture-only** — order-book depth. Kalshi serves only the *current* book;
there is no historical endpoint. A book state not recorded when it existed is
gone permanently. Our archive starts 2026-07-15 and is proprietary by
construction: it exists only because we were recording when the moment passed.
The same will be true of the candidate-list and edge-health time series.

## Cadence today, and what "real time" would mean

Current cadence is **batch, matched to decision speed**: books 4×/day,
candidates 1×/day, settled-market corpus static pending the Track 1 build
(daily incremental ingest + weekly edge recomputation). Nothing is streamed.

True real time is available if ever needed: Kalshi exposes websocket feeds
(order-book deltas, trade prints). We deliberately don't consume them — the
strategy enters once a day and holds for weeks, so intraday resolution changes
no decision while adding an always-on process to babysit. The one future
consumer would be a discovery screen that needs intraday microstructure (e.g.
flow-shock reaction); the recorder's REST cadence can also simply be increased
(launchd edit) long before websockets are justified.

## Growth plan (from edge-program-plan.md Track 1)

1. `ingest_incremental` daily: markets settled since the high-water mark + their
   tape → corpus becomes append-only current.
2. `edge_health` weekly: rolling edge per qualifying cell, calibration and
   maker-taker drift, against pre-committed amber/red thresholds.
3. Instrumentation-tier sampled tape (background) for cost-model precision.
