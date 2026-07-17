# Phase 0 — Assumptions Sheet

Committed 2026-07-15, before any screen is run. Every value here is fixed now so results
cannot be rationalized later. Changes after Phase 1 begins are permitted only as a logged
amendment at the bottom of this file, with a reason. Silent edits void the analysis.

## 1. Hurdle and kill threshold

| Item | Value | Source |
|---|---|---|
| 3-month T-bill | 3.76% | FRED DTB3, 2026-07-13 |
| Kalshi APY | 3.25% (variable) | user-confirmed 2026-07-15; accrues on cash and open positions |
| Carry drag vs. bills | ~51 bps | difference of the above; charged to every strategy |
| **Kill threshold** | **7.0% annualized net** | pre-committed; ~3.2 points over bills for platform risk, illiquidity, effort |

A cell qualifies only if annualized net edge > 7.0% **and** > 2 clustered standard errors,
**in both the discovery and confirmation periods** (§5). No exceptions, no "almost."

- Return definition: net profit ÷ capital committed, annualized as simple 365/days-held.
  For the T−7d horizon, per-horizon return is reported alongside annualized (annualization
  multiplies fee-rounding noise ~52×).
- Open positions earn APY, so capital committed is charged only the ~51 bps drag plus fees
  and spread — not the full time value.

## 2. Fee model

- Taker: `ceil_to_cent(0.07 × C × P × (1−P))` per fill. Modeled exactly per fill — the
  ceiling is a step function that dominates economics below ~10¢. Settlement free.
- Maker: per-series from the API, never assumed. Measured 2026-07-15 across 11,486 series:
  11,343 `quadratic` (zero maker fee), 130 `quadratic_with_maker_fees`, 13 zero-fee.
  No maker rebates exist on the exchange.
- Entry-price convention: maker entry = snapshot price haircut by Screen D's realized-spread
  estimate for that price bucket × horizon (until Screen D reports, placeholder = 2¢, flagged
  provisional). Pessimistic bound = taker at snapshot price + taker fee.

## 3. Carry

- APY accrues on cash and open positions (user-confirmed). Charge: ~51 bps drag vs. bills
  on all committed capital.
- **Open sub-item (non-blocking):** whether cash escrowed behind unfilled resting orders
  accrues APY. Prices the cost of waiting-to-be-filled; resolve with Kalshi support before
  deployment. Analysis proceeds assuming it does NOT accrue (pessimistic).

## 4. Universe

Two tiers. Measured 2026-07-15: ~99% of daily settled markets are `KXMVE*` parlays;
crypto ladders dominate the remainder; ~800–1,000 real markets/day clear a 25-trade filter.

- **Deployment tier** (capital candidates): Economics, Climate & Weather, Financials
  (long-dated only — daily/hourly crypto ladders excluded), Politics & World Events,
  Companies, Science & Tech. Full settled history ingested.
- **Instrumentation tier** (measured, never traded): sports, crypto ladders. Feeds
  Screens A and D only (calibration baseline, spread/adverse-selection estimates).
- Excluded everywhere: `KXMVE*` parlay markets (ticker-prefix filter at ingest; volume
  tallied separately as a flow datum).
- Minimum activity filter: ≥25 lifetime trades (provisional; finalized from Phase 1 QA
  distributions — the *procedure* is what's pre-committed: one threshold, chosen from the
  distribution before any screen runs, applied uniformly).
- Voids: voided/cancelled markets are charged as a cost to the cells where they occur,
  at observed void frequency by series. Never silently dropped.

## 5. Statistical protocol

- **Clustering:** all standard errors clustered by event (minimum); sensitivity check at
  series × settlement-week. Unclustered SEs are not reported.
- **Discovery/confirmation split:** discovery = markets settled before 2025-07-01;
  confirmation = settled 2025-07-01 through 2026-07-15. Cells qualify only in both (§1).
  The split also directly measures anomaly decay and brackets the Aug-2025 carry change.
- **Snapshot horizons:** T−7d, T−30d, T−90d, T−180d, T−365d before expiration.
- **Price buckets:** 1–5¢, 5–10¢, 10–20¢, …, 80–90¢, 90–95¢, 95–99¢ (symmetric tails).
- **Staleness:** each snapshot carries the timestamp of the trade supplying its price.
  Default filter: price must be ≤ 20% of the remaining time-to-expiry old (e.g. at T−30d,
  trade within the last 6 days). Reported with and without the filter.
- **Pooling (pre-committed order):** any deployment-tier cell with < 50 settled markets in
  discovery pools: (1) merge with adjacent price bucket; (2) if still < 50, pool categories
  at the same horizon. Pooling stops the moment n ≥ 50. No other pooling permitted.

## 6. Capacity

Capacity per cell ≈ median top-of-book depth (from the `book_snapshots` recorder, running
from Phase 1 day 1) × observed turnover at that cell. Cells ranked by edge × capacity.

## Amendment log

- **2026-07-15 (Phase 1, day 1):** Kalshi's category taxonomy is finer than §4 anticipated.
  Added to deployment tier: **Elections** (Politics under another label), **Commodities**
  (EIA/USDA-data-driven — squarely the layer-2 thesis), **Health** (CDC/govt data).
  Explicitly left in review (not analyzed, not traded): Entertainment, Mentions, Social,
  Education. Reason: mapping decision forced by observed category strings, made before
  any screen was run.
- **2026-07-15 (Phase 1, day 1):** §5's "candle close as cross-check" is unavailable for
  markets settled before the 2026-05-16 historical cutoff — the candlesticks endpoint
  404s for them (probed directly). The trade tape (`/historical/trades`) covers all eras
  and becomes the sole snapshot source; the staleness field already carries the burden
  the cross-check was for. Candle cross-checks may still be run on post-cutoff markets
  as a one-sided validation.
- **2026-07-17:** APY corrected in prose from ~3.5% to **3.25%** (user correction);
  carry drag vs bills restated 26bps → ~51bps. All computed results were always
  produced with CARRY_APY = 0.0325 in code — prose-only correction, no numbers change.
