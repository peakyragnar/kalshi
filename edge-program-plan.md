# Edge Program — Work Plan (Phase 2 of the project)

Successor to kalshi-market-structure-plan.md, which completed 2026-07-16 (GO: 2
cells). Three tracks. Same disciplines as Phase 1: pre-committed hurdles,
discovery/confirmation splits, clustered errors, findings-book updates, and the
operator makes all deployment decisions.

---

## Track 1 — Continuous edge measurement (the living core)

**Goal.** The measured edge is a decaying asset. Its current value — not July's —
must drive every decision. "Continuous" here means *daily batch*, deliberately:
holds are 30–90 days and entries are daily, so no intraday number changes any
decision; real-time infrastructure would add cost and fragility, not information.

**Build:**
1. `ingest_incremental` (daily, scheduled): pull markets newly settled since the
   last high-water mark + their trades; append to the store; rebuild derived
   snapshots incrementally. High-water cursor in checkpoint.
2. `edge_health` (weekly, scheduled): recompute per qualifying cell on trailing
   windows (90d / 365d):
   - cell edge (ann, with carry, clustered SE) vs the qualification baseline
   - calibration gap (F1 metric)
   - maker–taker gap (F4 metric)
   - observed tail-loss rate vs the memo bounds
3. **Pre-committed traffic lights** (set now, before any drift is observed):
   - AMBER — trailing-90d cell edge − 1·SE < 7% hurdle → halve new-entry size
   - RED — trailing-90d cell edge − 1·SE < carry (~3.5%) → stop new entries;
     positions run off naturally
4. Dashboard: "edge health" section — current vs baseline per cell, trend, light.
5. When live (Stage 2 of execution plan): fill-rate and realized-vs-modeled P&L
   join the same section from the read-only portfolio feed.

**Deliverable:** two scheduled jobs + dashboard section + traffic-light rules
committed. Effort ~2 days.

## Track 2 — Systematic edge discovery (the pipeline of next edges)

**Goal.** The map found what the lockup thesis was shaped to find. Other
structures exist that our snapshot grid couldn't see. Run one new screen per
week against the same kill discipline; survivors join the map.

**Hypothesis backlog (initial, ranked):**
1. **Ladder-monotonicity violations** — within multi-strike ladders, implied
   P(>X) must decrease in X; the tape shows violations. Are they persistent and
   harvestable at maker prices? (Uses existing data.)
2. **Resolution drift** — do prices systematically drift the final N days
   (favorites grinding to 99 = late-entry variant with faster recycling)?
   (Existing data; new snapshot grid anchored to close.)
3. **New-listing mispricing** — first-week prices vs settlement; retail anchors
   badly on fresh markets? (Existing data; snapshots anchored to open_time.)
4. **Flow-shock reaction** — after a taker-YES volume surge, do prices
   overshoot? (Tape only.)
5. **Instrumentation-tier baselines** — ingest sampled sports/crypto tape;
   re-run A/D there. Not for deployment: sharpens the cost model and tests
   whether deployment-tier findings are exchange-wide or category-specific.
6. **Cross-venue gaps** — Kalshi vs Polymarket same-event pricing (new data
   source; free API). Discipline note: cross-venue "arbs" are usually rulebook
   differences — the sweep methodology applies before any claim.

**Data additions:** instrumentation trades sample (background backfill);
listing-anchored snapshot grid; ladder-relationship table; Polymarket feed
(later).

**Deliverable cadence:** one screen/week, written up in the findings book,
RED/GREEN verdict against the pre-committed hurdle. Most will die; that is the
system working.

## Track 3 — Edge from data itself (layer 2: the fundamental layer)

**Goal.** Until now every edge is structural — prices vs outcomes, no knowledge
of the world. Layer 2 brings outside data. **Reframe from the original thesis:**
in the qualifying cells we do not need to out-forecast the market broadly; we
need (a) **selection** — skip candidates whose tail is hotter than the base rate
(the veto lesson), and (b) **pricing** — size up candidates whose true tail is
colder. Selection is cheaper than prophecy and compounds with the existing edge.

**Pipelines, ranked by edge-per-effort (first two serve live candidates today):**
1. **Congressional calendar watcher** (Politics cell): Senate executive
   calendar, scheduled cloture/confirmation votes, Library of Congress bill
   status. Today's candidate list is full of confirmation markets — whether a
   vote is *scheduled* is public, mechanical, and is the tail. Skip/size signal
   per candidate, surfaced on the dashboard row.
2. **EDGAR filings watcher** (Financials cell): S-1/F-1 and amendments are the
   mechanical precursor of "confirms an IPO." A filing = the tail is live.
   Free, structured, automatable.
3. **Base-rate library** (Politics): historical frequencies per proposition
   family (pardons, vetoes, foreign trips, Mar-a-Lago weekends) from public
   records + our own settled-market corpus → prior per candidate vs market
   price → flags both elevated-tail (skip) and overpriced-tail (size up).
4. **Options-implied densities** (Financials): CBOE SPX/NDX smiles vs Kalshi
   yearly-range prices → independent fair value for index cells; also detects
   when that pocket gets arbed.
5. **Weather/climate** (bench): Climate cells near-missed the map; if forward
   data qualifies them, NOAA/CPC pipelines slot in — infrastructure the
   operator's data business already runs.

**Deliverable:** pipeline 1 and 2 as scheduled jobs annotating the daily
candidate list (a `tail_signal` column: CLEAR / WARM / HOT / UNKNOWN); base-rate
library as a background build.

## Sequencing (proposed)

| Week | Track 1 | Track 2 | Track 3 |
|---|---|---|---|
| 1 | incremental ingest + edge_health + lights | UNSWEPT sweep pipeline (rolling daily) | congressional calendar watcher |
| 2 | dashboard edge-health section | screen: ladder monotonicity | EDGAR watcher |
| 3 | (running) | screen: resolution drift | base-rate library v1 |
| 4+ | (running) | one screen/week from backlog | options-implied v1 |

Standing rule: discovery screens and data pipelines never touch deployment
rules directly — anything they find passes through the map's qualification
gate and a findings-book entry first.
