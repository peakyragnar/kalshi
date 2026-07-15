# Kalshi Market Structure Analysis — Work Plan

**Objective.** Produce a calibration map of the Kalshi exchange: which market families misprice, at which horizons, in which direction, by how much — net of fees and carry. The map decides (a) whether to deploy capital at all, (b) into which two or three market families, and (c) which fundamental datasets to build afterward. No forecasting model is built during this plan; structure locates the discount before fundamentals confirm it.

**Governing principle.** Every screen outputs one number — annualized net return — and is judged against a pre-committed kill threshold. If nothing survives, the project ends at Phase 3 at a cost of ~3 weeks. That outcome is a success, not a failure.

---

## Phase 0 — Definitions and benchmarks (half a day)

Fix these before touching data so results can't be rationalized afterward.

- **Hurdle rate:** 3-month T-bill (~3.8%) + platform/regulatory risk premium + effort. Kill threshold: **7% annualized net**, and edge must exceed 2 standard errors of the estimate.
- **Fee model:** taker = 0.07 × P × (1−P) per contract, rounded up to the cent per fill; settlement is free. **Do not assume a maker fee** — most Kalshi series charge zero maker fees; a minority of designated series charge them. Pull the actual fee schedule per series from the API into the `markets` table and apply the true fee per market. Pessimism belongs in the fill/spread assumptions (set by Screen D), not in a fee that isn't charged. Note the ceil-to-cent rounding is a step function that dominates economics below ~10¢ — model it exactly, per fill, not as a rate.
- **Carry model (assumption to verify, not assert):** Kalshi APY (3.25% at last check, variable). Before committing the assumptions sheet, verify against Kalshi's current terms exactly what accrues on what — cash vs. resting orders vs. marked open positions — and what changed in August 2025. Screen B's pre/post design depends on this. Then: model carry as APY on the verified base, and charge the ~55bps spread between APY and bills as opportunity cost.
- **Universe rules:** exclude markets with fewer than a minimum trade count (set after seeing distributions, e.g. 25 trades). Voided/cancelled markets are **not silently excluded**: track void frequency by category/series and charge it as a cost to the cells where it occurs — a real strategy eats the void, and voids concentrate exactly where rulebook drafting is worst.
- **Statistical protocol (pre-committed):**
  - *Clustered errors.* Settled markets are not independent — brackets of one event settle together, series share drivers. All standard errors are clustered by event at minimum; check sensitivity to clustering by series × settlement week. Unclustered SEs are fictional and are not reported.
  - *Discovery/confirmation split.* The map has hundreds of cells; at 2 SE, ~5% qualify by chance on noise alone. Split the sample in time: **discover** candidate cells on the older period, **confirm** on a held-out recent period (e.g. trailing 12 months). A cell qualifies only if it clears the hurdle in both, with the confirmation period's (clustered) SE. This also directly measures anomaly decay.

**Deliverable:** a one-page assumptions sheet committed before Phase 1 begins.

---

## Phase 1 — Data foundation (days 1–5)

**Source:** Kalshi's official API (free). Live endpoints for current/recent data; `GET /historical/...` endpoints for settled markets, trades, and candlesticks past the cutoff (`GET /historical/cutoff`). Cursor pagination throughout.

**Raw tables:**

1. `markets` — ticker, event, series, category, open/close/expiration timestamps, settlement outcome, status, **the series fee schedule (maker fee yes/no and rate)**, and the rulebook's settlement source where retrievable.
2. `trades` — price, size, timestamp, taker side, per market.
3. `candles` — daily OHLC per market.
4. `book_snapshots` — **live order-book recorder, started on day 1 of this phase**: top 3 levels both sides, all active markets, several times daily. The API has no historical book, so this recorder is the only source of real depth for the Phase 3 capacity estimates and for Screen C — every day it isn't running is depth data lost. It's a small script; write it before the historical backfill.

**Core derived table** (the object every screen runs on): one row per settled market per snapshot horizon at **T−7d, T−30d, T−90d, T−180d, T−365d** before expiration, joined to the settlement outcome, category, and exact fee at that price. Per snapshot, record **three price fields**, not one: the last traded price, **the timestamp of the trade that supplied it** (staleness — on thin long-dated markets the "last trade" can be weeks old, and staleness correlates with exactly the markets the lockup thesis targets), and the daily candle close as a cross-check. Screens filter or downweight by staleness; results are reported with the staleness cut disclosed.

**QA gate:** coverage counts by category × year; distribution of time-to-expiry at listing; share of markets excluded and why. If sports dominates row counts (likely — it is most of exchange activity), keep it but report all results with and without sports, since it carries the regulatory overhang.

**Deliverable:** one parquet dataset + a coverage report + the book recorder running.

---

## Phase 2 — Structural screens (days 6–10)

Four screens, run on the same derived table. Each answers one question.

**Screen A — Calibration and favorite–longshot bias.**
Bucket snapshot prices (1–5¢, 5–10¢, …, 95–99¢). For each bucket: realized settlement frequency vs. implied probability, and net return of buying-and-holding to settlement after maker and after taker fees. Cut by category and by horizon. *Purpose:* replicate the published finding (high-priced contracts win more often than priced; makers outperform) on the current data and locate where the bias is fattest — and whether it has decayed since publication.

**Screen B — Term premium (the lockup thesis).**
Same hold-to-settlement trade, cut by time-to-expiry bucket, returns annualized. *Test:* does net annualized return rise with lockup duration, controlling for price bucket and category? Split the sample pre/post August 2025 (launch of interest on open positions) to measure whether the APY change already compressed the discount. *This screen is the direct test of the core thesis: patient capital being paid for warehousing what impatient or non-interest-earning holders won't.*
*Identification check (run first):* horizon correlates strongly with category — long-dated skews elections/climate, short-dated skews sports. Before interpreting anything as a term premium, tabulate sample support per category × horizon cell; a category with markets at only one horizon cannot separate term premium from category effect, and the conclusion is stated only for categories with multi-horizon support. The pre/post-Aug-2025 split cuts the sample again — expect wide error bars on the post period and say so rather than over-reading it. For the T−7d bucket, report the per-horizon return alongside the annualized figure: annualizing a 7-day hold multiplies fee-rounding noise ~52×.

**Screen C — Bracket completion (live scan, no backtest).**
For every currently listed multi-outcome event with mutually exclusive brackets: sum the best asks across all brackets. Two variants, reported separately because they are different trades:
- *Taker-cross (the riskless one):* lifting the best asks is taker flow — flag events where sum of asks < $1 minus **taker** fees on every leg, each rounded up to the cent (the rounding bites hard on many-bracket events with cheap tails). This is the true arbitrage bound.
- *Maker-leg (cheaper, not riskless):* resting bids across brackets avoids taker fees but reintroduces legging risk — some legs fill, others don't, and the unfilled legs are the informative ones. Quantify fill risk from the daily re-runs rather than assuming completion.
Annualize the locked profit over time-to-settlement; record executable depth at the flagged prices (feed the `book_snapshots` recorder). Verify exhaustiveness against the event rulebook (open-ended tail brackets, void language) before counting any event as riskless. *Purpose:* measure whether the view-free, outcome-independent trade exists today, at what size, and in which event families. Re-run daily for two weeks to estimate how often opportunities appear and how fast they close.

**Screen D — Maker vs. taker economics and adverse selection.**
From the trade tape, estimate the realized return gap between resting and crossing sides by **price bucket × horizon**. *Purpose:* this is the exchange's realized spread + adverse-selection cost, and it replaces the naive one-tick entry haircut everywhere — long-dated thin books run 5–15¢ wide, and one tick is fantasy there. Screen D's estimate is the entry-cost assumption applied to every maker-entry number in Screens A–C. If adverse selection eats the maker advantage in long-dated books, every result gets restated with the worse number.

**Deliverable:** four screen reports, each ending in annualized net return with standard errors, by category × horizon × price bucket.

---

## Phase 3 — The calibration map (days 11–12)

Assemble the matrix: **category × horizon × price bucket → {annualized net edge, clustered standard error, sample size, capacity estimate}**, where capacity ≈ median top-of-book depth × observed turnover at that cell, with depth taken from the `book_snapshots` recorder (by Phase 3 it has ~2 weeks of real books; the recorder keeps running regardless).

- **Qualification rule (pre-committed in Phase 0):** a cell qualifies only if it clears edge > 7% and > 2 clustered SE **in the discovery period and again in the held-out confirmation period**. A single-period 2-SE pass across hundreds of cells is noise by construction and does not qualify.
- Rank qualifying cells by edge × capacity.
- Apply the stop rule: **no qualifying cell → project stops here.** Document the negative result; it is reusable (it also tells you which markets are efficient enough to trust as forecasts).
- Otherwise: select the top 2–3 market families for Phase 4.

**Deliverable:** the map (one table + one heatmap) and a go/no-go decision.

---

## Phase 4 — Structure memos for surviving families (days 13–15)

One page per surviving family, answering five questions in order:

1. **Who sets the marginal price?** Retail app flow, FCM-routed flow that earns no APY, or professional quotes — and therefore *why* the mispricing exists and whether the reason is durable.
2. **Rulebook risk.** Settlement source, deadline wording, void/ambiguity language, precedent for disputed settlements. Read like a credit doc; a discount caused by bad drafting is not a term premium.
3. **Regulatory exposure.** Econ/weather/policy vs. sports/elections; current litigation touching the category; consequence of a mid-hold adverse ruling.
4. **Liquidity profile.** Fill time for maker orders, exit cost if forced, realistic book size.
5. **Dataset requirement.** What fundamental data pipeline would deepen the edge in this family — this section is the requirements document for the next workstream, and the only place forecasting enters the plan.

**Deliverable:** 2–3 memos + a ranked recommendation for where the first live dollars go ($5–10k, maker-only — this is the *master plan's* deployment phase, a separate document; the phase numbers there do not correspond to the phases here).

---

## Timeline and outputs summary

| Phase | Duration | Output |
|---|---|---|
| 0 — Definitions | 0.5 day | Assumptions sheet, kill threshold, statistical protocol |
| 1 — Data foundation | 5 days | Settled-market dataset + coverage report + book recorder |
| 2 — Four screens | 5 days | Edge estimates by category/horizon/price |
| 3 — Calibration map | 2 days | Ranked map + go/no-go |
| 4 — Structure memos | 3 days | 2–3 memos + deployment recommendation |

Total: ~3 weeks part-time. Total spend: $0 (all data free).

---

## Known limitations (stated up front)

- **No historical order book** in the official API — maker fills are approximated from trade prices, haircut by Screen D's realized-spread estimate per price bucket × horizon (not a flat one tick, which understates thin long-dated books). The day-1 recorder closes this gap prospectively but cannot recover the past.
- **Snapshot staleness:** last-trade prices at long horizons can be weeks old on thin markets; the derived table carries the supplying trade's timestamp, and every screen discloses its staleness filter.
- **Anomaly decay:** the favorite–longshot findings are now published; the discovery/confirmation time split measures how much has already been competed away — decay shows up directly as discovery-period cells failing confirmation.
- **Regime shifts:** institutional volume grew ~800% in six months and institutional tooling is arriving; edges measured on 2021–2024 data may overstate what remains. Weight recent periods accordingly.
- **Sports category:** largest sample, largest regulatory overhang. Report everything with and without it; default deployment excludes it.
