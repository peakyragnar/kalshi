# Kalshi Market Structure — Findings Book

**What this is.** The accumulated, validated findings of the market-structure project,
maintained as the single reference for any real-money decision. Every claim cites the
screen that produced it; every number is reproducible from the repo. Updated as new
evidence lands (forward settlements, recorder depth, live scans). This document
records what the data supports — the deployment decision itself belongs to the
operator and is gated by the Phase 3 map and the pre-committed kill rule.

**Data basis (as of 2026-07-18):** 2.888M settled raw markets (2021→2026),
67.290M fills with aggressor side, 1,106,075 leakage-resistant decision points,
complete deployment title/strike/rule metadata, actual settlement timestamps missing for
only 68 raw markets, and order-book depth recorder live since
2026-07-15. Full reports: `research/screen_a.md`, `screen_d.md`, `screen_b.md`,
`corpus-audit.md`, `edge-atlas.md`, `mechanism-suite.md`, `metadata-suite.md`,
and `survivor-audit.md`.

**Material timing correction, 2026-07-17.** Earlier screens anchored horizons to
`max(close_time, expiration_time)`. Kalshi uses `close_time` for the actual end
of trading; `expiration_time` may be a rescheduling ceiling a week later. All
screens below were rebuilt on `close_time`. The Politics T−30 cell survives the
economic correction but has insufficient early-fold support under the new atlas;
the Financials T−90 qualification does not survive and is withdrawn. No live
orders were changed automatically.

---

## Part 1 — Validated findings

### F1. Low-probability YES overpricing survives, but it is not universal
At T−30d the 1–20¢ YES buckets settle below their implied probability in both
periods (for example, confirmation 1–5¢: 2.09¢ implied versus 1.30% realized;
10–20¢: 14.01¢ versus 12.61%). Other buckets and longer horizons flip sign.
Holding NO therefore needs explicit category × horizon × price selection; there
is no exchange-wide "buy NO" rule. *(Corrected Screen A)*

### F2. Apparent anomalies decay and must replicate through time
The academic "buy high-priced favorites" edge exists in pre-2025 data and is gone
(slightly reversed) in the last 12 months. Some longshot overpricing persists in
aggregate, but the registered category × horizon × price search produced no
FDR-qualified cell. Neither side is a universal rule; temporal replication and
search correction are mandatory. *(Corrected Screen A; Edge atlas v1)*

### F3. The bias has large sign flips — selection is mandatory
The original atlas tested 722 category × horizon × price cells and produced zero
FDR qualifiers. The expanded suite now executes the previously missing
mechanisms: listing lifecycle, own-price path, sibling lead/lag, aggressor flow,
recent activity, staleness, recurring series, calendar, early close, event
structure, settlement source, maker selection, and rule language. Across 55,236
statistical cells, six passed all three folds, one survived family FDR, and none
survived every gate plus suite-wide FDR. This is direct evidence that isolated high-return cells
are easy to manufacture from the corpus and must be judged against the entire
search. *(Edge atlas v1; Multi-mechanism suite v1)*

### F4. Makers beat takers everywhere — but that alone does not make maker returns positive
Across 20.1M eligible fills, the resting side out-returns the crossing side in every
horizon bucket and both periods, by roughly +1 to +26pp per fill. The gap is
consistent with adverse selection against the crossing side, but it does not by
itself identify who trades or why. Maker fee is zero on
98.9% of series (130 series charge; pull per-series). However, broad longshot
maker returns are negative in several horizons: better than taker is not the
same as profitable. *(Corrected Screen D)*

### F5. There is NO term premium — the edge peaks at 30–90 days
Corrected pooled annualized NO return is largest at T−30 (~65% before carry) and
does not rise monotonically: ~21% at T−90, ~33% at T−180, ~27% at T−365, all
with wide event-clustered uncertainty. Within-market residuals tell the same
directional story. Duration is not the source of edge; 3.25% carry only reduces
the cost of waiting. *(Corrected Screen B)*

### F6. Returns are insurance-shaped; the edge is a portfolio property
The surviving Politics T−30d 1–5¢ cell earns roughly 1.8–2.2% per historical
hold, with observed tail-loss rates from 0% to 0.6% by fold. One YES settlement
can still erase many small NO wins, and losses cluster by event. No single
position earns the historical average; diversification remains essential.
*(Edge atlas v1)*

### F7. Statistical support now precedes capacity
The new atlas promotes no cell, so it correctly does not run a capacity gate.
For the live-monitored Politics cell, current economics are consistent but the
early fold has only 26 independent events versus the registered minimum of 50.
Capacity remains relevant only after a candidate clears that support and FDR
gate. *(Edge atlas v1)*

### F8. Bracket "free money" is almost always a trap; genuine arbs are a
side-dish at best
Live scan (193 open multi-outcome events): most flagged sub-$1 completions are
missing-outcome traps (non-exhaustive candidate lists — verified live on two
examples, both failed rulebook or depth). Even a genuine completion must beat
bills after annualization: 5¢ over 13 months ≈ 4.5%/yr = worse than a T-bill.
Only short-dated dislocations matter; two-week daily scan measures their
frequency. *(Screen C demo, 2026-07-16)*

### F9. Cost & carry facts (verified)
Taker fee = ceil(0.07·P·(1−P)) per contract per fill — a step function that
dominates below ~10¢. Maker fee zero except 130 designated series. Settlement
free. APY (3.25%, variable) accrues on cash AND open positions
(user-confirmed 2026-07-15); 3-mo T-bill 3.76% (FRED, 2026-07-13) → carry drag
~51bps. **Open question: does cash escrowed behind unfilled resting orders
accrue?** (Assume no until Kalshi confirms — prices the cost of waiting for fills.)

### F10. The expanded suite has no historical survivor
The previously reported path cell `T-1d->T-6h|-2:2|01-05|no` still shows large
absolute NO returns and at least 1,119 independent events in its weakest fold,
but it fails the matched-baseline economic gate: its weakest incremental
annualized two-standard-error lower bound is −0.030996. Small corrected q-values
do not override a failed pre-committed economic condition. The expanded suite
therefore has **zero historical qualifiers**, and the execution audit is
suppressed rather than continuing to label the old cell a survivor.
*(Multi-mechanism suite v1; Survivor execution audit)*

### F11. The first external-data suite finds no GFS weather edge
The point-in-time weather panel contains 220,320 costed YES/NO strategy rows
across 9,784 events, 56,370 contracts, and 20 exact settlement stations. The
registered suite tested 268 level, city, price, staleness, and revision cells.
None passed the economic and matched-baseline gate in all three folds, and none
survived family or combined structural-plus-external FDR. Kalshi prices also
beat the station-calibrated GFS probability model on Brier score at T−1d
(0.112 versus 0.148) and T−6h (0.021 versus 0.140). This rejects the current
GFS-only specification; it does not reject all weather data or future ensembles.
*(Weather external-alpha suite v1)*

---

## Part 2 — Current deployment interpretation (not an automatic instruction)

After the timing correction, the evidence supports only this narrow posture:

- **Position:** the only legacy cell still worth monitoring is Politics T−30d,
  with YES at 1–5¢; use resting NO-side maker orders and never infer a broader
  1–20¢ rule from pooled results.
- **Horizon:** the existing Politics cell is T−30d. Duration itself is not an
  edge and no blanket 30–90d rule survives the systematic atlas.
- **Universe:** every exchange category is eligible for structural research
  except crypto- and sports-themed series, including contracts Kalshi labels in
  other categories. `KXMVE*` parlays and versioned RED rulebooks are
  excluded. Fed, payroll, GDP, Elections, Transportation, Entertainment,
  Mentions, Social, Education, and presidential-ticket series are included; no
  market is excluded merely because it is presumed professionally priced.
- **Diversification:** many small positions across unrelated events; losses
  cluster (F6), so event concentration is the primary portfolio risk.
- **Financials T−90:** withdrawn as a qualified cell after the timing correction;
  no new entry should be inferred from the old memo. Existing orders/positions
  require an operator decision and were not changed by research code.
- **New discovery:** no cell is historically qualified after the expanded
  universe and full suite correction. No new shadow or live rule is created.

**What would falsify it going forward:** the calibration gap closing in newly
settled markets; maker-taker gap compressing (professionalizing flow); fill
rates collapsing. All three are tracked automatically (below).

---

## Part 3 — Current gates

1. **Politics T−30d YES 1–5¢:** economic lower bounds clear 7% in early,
   middle, and recent folds, but early support is 26 events versus the registered
   50-event minimum. Status: **INSUFFICIENT SUPPORT / live monitored**, not a new
   systematic qualification.
2. **Financials T−90d YES 1–10¢ ex-ticket:** middle-fold lower bound is −13.1%
   and the corrected legacy map also fails. Status: **RED / qualification withdrawn**.
3. **Complete mechanism suite:** 55,236 cells across 15 statistical families;
   six pass all folds, one survives family FDR, and none clears the full
   suite-wide gate. Status: **ZERO HISTORICAL QUALIFIERS**.
4. **Forward validation:** observations from 2026-07-17 onward are sealed and
   cannot be reused to invent gates.
5. **Execution:** historical books remain unavailable; only captured books and
   real fills can graduate a historically qualified edge to live execution.

## Part 4 — Standing infrastructure

- Recorder: launchd `com.exascale.kalshi-recorder`, 4×/day, ~24k books/run.
- Rebuild anything: `uv run python -m kalshi_data.{ingest_series,ingest_markets,
  ingest_trades,derive,coverage,screen_a,screen_b,screen_d}`; discovery screens
  live under `kalshi_data.analysis` (for example `flow_shock`).
- Tests: `uv run pytest`. Data: `data/` (gitignored, reproducible).

## Part 5 — Systematic discovery ledger

| Screen | Verdict | Evidence | Consequence |
|---|---|---|---|
| Structural atlas v1 (`research/edge-atlas.md`) | **ZERO QUALIFIERS** | 1,082 registered cells; one passed all folds pre-FDR (Economics T−30d YES 11–20¢), then failed q=0.163. | No new cell; begin external-data work only as a selection layer or newly registered test. |
| Multi-mechanism suite v1 (`research/mechanism-suite.md`) | **ZERO HISTORICAL QUALIFIERS** | 55,236 cells across 15 statistical families; six three-fold passes, one family-FDR pass, zero full-suite passes. | Do not preserve the old path cell as a survivor; new mechanisms require registration or point-in-time external data. |
| Metadata structure (`research/metadata-suite.md`) | **DESCRIPTIVE ONLY** | 46,254 adjacent ladder pairs and 125 complete exclusive-event observations; synchronous-price coverage is sparse. | Use live books to test simultaneous leg execution; do not label asynchronous last-print gaps arbitrage. |
| Flow-shock overshoot (`research/flow_shock.md`) | **RED** | Corrected timing: 3,217 shocks, median seven-day YES change −3¢ in both periods. Discovery reversion, absolute return, and uplift all fail the 2SE gate. | Do not add a pooled post-shock entry rule. |
| Weather GFS external alpha (`research/weather-alpha-results.md`) | **ZERO QUALIFIERS** | 268 registered cells; zero three-fold passes. Market Brier error is lower than the calibrated GFS model at T−1d and T−6h. | Keep the unchanged weekly monitor; do not create a GFS-only shadow or live rule. |

## Change log
- 2026-07-16: created after Screens A, B, D. Screen C production scan and the
  Phase 3 map are the open work items.
- 2026-07-16 (later): Phase 3 map PASSED — GO with 2 qualifying cells
  (Politics 30d 1–5¢; Financials 90d 1–10¢). Phase 4 memos are the open item.
- 2026-07-16 (later still): Phase 4 memos written (`docs/memos/`). Financials cell
  re-qualified ex-ticket-price series (+16.8%/yr conf, bound +11.1%). Both
  cells' single observed tail losses identified and analyzed (Trump vetoes;
  S&P all-time-high — the latter index-correlated). Politics = primary cell,
  Financials = secondary with index sub-cap recommendation. Open before
  deployment: rulebook reads, regulatory status check, escrow-carry answer.
- 2026-07-16: Rulebook sweep complete (`research/rulebook-sweep.md`): 36 series
  read, 22 GREEN / 12 YELLOW / 2 RED (KXCRYPTOSTRUCTURE, KXTARIFFCHECKS —
  categorical/attribution judgment conditions, excluded). No discretionary
  settlement language found anywhere. New selection rule: prefer act-conditions
  over announcement/attribution triggers.
- 2026-07-17: Settled corpus now self-updating (daily incremental ingest);
  edge_health live on weekly schedule with pre-committed lights. First grading:
  politics_30d GREEN (+28.0% t90), financials_90d AMBER (bound 6.6% < 7% on
  n=70 — halved-entry rule applies). APY prose corrected to 3.25% (code was
  always 0.0325). Falsification metrics tracked: calibration gap −1.0pp,
  maker−taker gap +26.8pp (both alive).
- 2026-07-17: Regulatory brief delivered (docs/regulatory-brief.md): political
  contracts federally permitted (CFTC dropped appeal May 2025); June 2026
  proposed rule classifies elections as contests not gaming; no retroactive
  voiding proposed; residual risk = enumerated-activity edge cases (war-adjacent
  markets like Hormuz) and future listing supply. Operator's comfort call
  remains the gate. First real orders placed today: 11 resting, $603 committed.
- 2026-07-17: Interest-program eligibility confirmed by operator (SSN on file,
  qualifies). The escrow sub-question (does order-reserved cash accrue?) now
  resolves empirically: ~$603 sits behind resting orders; the first monthly
  interest credit's accrual base answers it. Models stay pessimistic until then.
  No support ticket needed.
- 2026-07-17: First Track-2 discovery screen completed. Flow-shock overshoot is
  RED under its pre-committed cross-period gate: high median mean-reversion did
  not translate into stable average or incremental NO returns. No deployment
  rule changes. Definition and full result: `research/flow-shock-precommit.md`,
  `research/flow_shock.md`.
- 2026-07-17: Research-system audit corrected the tradable horizon from
  `max(close_time, expiration_time)` to `close_time` and normalized
  `settlement_ts`. Full short-duration tape now covers 332,515/332,515 traded
  sub-six-day markets. Corrected corpus: 47,342,026 trades; 50,941 snapshots;
  758,479 decision points.
- 2026-07-17: Atlas v1 tested 722 registered cells across three historical
  folds with event clustering and FDR. Zero qualified. Politics T−30 retains
  strong economics but lacks early-fold support; Financials T−90 is RED and its
  prior qualification is withdrawn. No live order was changed automatically.
- 2026-07-18: Expanded the corpus to every category except semantically
  classified sports and crypto series; restored macro, elections,
  entertainment, mentions, social, education, and transportation. Final corpus:
  67,289,825 trades and 1,106,075 decision points. Of 55,236 statistical cells,
  six passed all folds, one survived family FDR, and none cleared the complete
  suite-wide gate. The prior near-flat path label is withdrawn because its
  weakest matched-baseline lower bound is negative. Ladder and event-sum scans
  remain descriptive because historical last prints are asynchronous.
- 2026-07-18: Completed the first point-in-time external-data suite. Backfilled
  fixed-lead GFS forecasts and exact-station NOAA observations for 20 weather
  stations, tested 268 registered cells across five mechanisms, and found zero
  three-fold or FDR survivor. The weekly job now refreshes and reruns the sealed
  weather test automatically; no deployment rule was added.
