# Information-Edge Program — Work Plan (Phase 3 of the project)

Successor to 02-edge-program-plan.md. Ratified context (2026-07-18, expanded
corpus, commit `38d4c70` + main-loop review): Kalshi is efficient for
price-takers; no risk-free arbitrage exists; the one residual structural
phenomenon is the maker wage at extreme prices (unqualified, one forward test
pending); the historical search is exhausted as a discovery tool.

**Thesis of this phase:** remaining edge, if any, comes from *information* —
modeling the settlement variable from public upstream data before the market
prices it — and cashes out through the one structural channel the data
validated: patient maker orders at extreme prices, held to settlement.
Structure is the delivery mechanism, not the thesis.

The operator makes all deployment decisions. Nothing in this plan places or
modifies orders.

---

## Track A — The Information-Edge Atlas (the search engine)

**Question it answers:** "which data should we acquire and model, in what
order?" — as a measured ranking, not taste.

**Principle:** we do not search the world's information. We search Kalshi's
*settlement variables*. Every market family settles on an enumerable fact;
each family is scored on six axes:

| # | Axis | Meaning | Source | Method |
|---|---|---|---|---|
| 1 | Mechanicalness | does it settle on a published measurement? | settlement-source classes (government / exchange-data / media), rulebook verdicts | automated |
| 2 | Upstream signal | does public data lead the settlement variable? | settlement-source URL hostnames + per-family enumeration | automated proposal + judgment pass |
| 3 | Point-in-time availability | can we know what was knowable at decision time (archives exist / capture required)? | source catalog | judgment pass, documented per family |
| 4 | Dumb-flow depth | maker-side contracts at extreme prices (01–05, 96–99) | trade tape (fills machinery from screen D) | automated |
| 5 | Incumbent sharpness | mid-bucket calibration vs tail calibration per family | settled corpus | automated |
| 6 | Verification speed | settlements per month; median market lifetime | settled corpus | automated |

**Scoring: pre-committed before the first ranked run.** Axes 1, 4, 5, 6
computed from the corpus; axes 2–3 filled as a structured judgment column
(with named sources) for the top ~30 families by axis 4. Composite rank =
product of normalized axis scores (a zero on any of axes 1–3 zeroes the
family: un-modelable is un-modelable). Weights and normalization are fixed in
the module docstring before the first run; changes go through the amendment
log like every registry.

**Deliverables:**
- `src/kalshi_data/analysis/info_atlas.py` + tests
- `research/information-edge-atlas.md` (ranked table, shortlist of top 3
  targets with their upstream-source dossiers) + parquet
- Refresh cadence: quarterly, or on universe change.

**Expected outcome (to be confirmed, not assumed):** weather daily ranges at
#1. The atlas exists to *derive* this and to surface targets #2–#3 we have
not thought of, plus explicit skip-verdicts for adversarial domains (Fed,
payrolls) where the upstream information is the professionals' own game.

Effort: ~2 days automated axes + 1 judgment pass.

## Track B — Point-in-time capture (the unbackfillable layer)

Two standing rules: **point-in-time or it doesn't count**, and **capture
starts before modeling** — every uncaptured day is training data lost
forever. Per atlas target:

1. **Weather (presumptive #1, start immediately):** daily archive of
   government forecast ensembles + station observations for the stations
   Kalshi settles on, stamped with retrieval time. Historical model-archive
   backfill where public archives exist (they do for the major ensembles) —
   backfill is legitimate *only* because the archives are themselves
   point-in-time records.
2. **Final-hours order books (serves all maker-channel deployment):** retarget
   the book recorder at markets entering extreme-price / near-settlement
   windows. This is simultaneously the executability gate (fill rates, queue
   depth) and the decay early-warning system (fill starvation precedes return
   decay).
3. Targets #2–#3: capture pipelines specced after the atlas names them.

Existing watchers (congressional calendar, EDGAR) continue as-is: they are
the point-in-time layer for Politics/Financials event families and now write
to the feature store.

Effort: recorder retargeting ~1 day; weather capture ~2 days.

## Track C — Models (one target at a time)

Per atlas target, in order, never more than two concurrently:

1. **Target model:** calibrated probability distribution for the settlement
   variable (for weather: per-station, per-season bias/spread-corrected
   ensemble → P(settle in bracket) for every listed bracket).
2. **Edge computation:** model probability vs market price, *net of the
   maker-channel cost model* (fees, carry, 7% hurdle) — output is a per-market
   fair-value band and edge estimate, joined to the daily candidate list.
3. **Use both directions:** sell tails the model says are dead (offense);
   veto/exit when the model says the tail is live (defense — the
   synchronized-day early warning).

## Track D — Validation and deployment (the provenance rules)

Pre-committed, they close the loopholes that killed the two structural
mirages:

1. **Provenance decides what history is worth.** A model whose inputs and
   form are chosen *without reference to Kalshi outcomes* may be validated
   against the full settled corpus — that backtest is legitimate evidence
   (multiplicity = number of model variants tried, which is logged in a
   model registry with a change-log, like the mechanism suite).
2. **Anything tuned on market P&L spends history.** Tuning split: fit on
   pre-2025-07-01, evaluate on 2025-07-01→2026-07-16, confirm on the sealed
   period (≥ 2026-07-17, still untouched).
3. **Economic gate unchanged:** annualized net edge, with carry, minus two
   event-clustered SEs, above 7%, at ≥50 independent events; day-clustered
   robustness check alongside.
4. **Deployment is a ladder, not a cliff:** paper → tiny → half → full, each
   rung unlocked by pre-committed evidence thresholds; shadow execution runs
   from registration day (fills, queue, realized-vs-modeled).
5. **Retirement rules written at deployment:** AMBER/RED edge lights, plus
   the two leading indicators — fill starvation and retail-flow composition —
   monitored weekly. RED = stop entries, run off, findings-book entry.
6. **Concentration caps precede capital:** same-day / same-category exposure
   cap in the memo before any rung above paper (the synchronized-loss-day
   lesson; F6 at high frequency).

## Standing items carried from the alpha-exploration review

- **Politics forward test** (`Politics|7-30d|01-05|no`, maker): m=1
  pre-registration awaiting operator go. Independent of this plan's tracks;
  cheapest possible qualified-edge shot (~6 weeks of accrual).
- Weekly mechanism suite continues as drift monitoring, not discovery.
  Re-slicing ban stands.
- Base-rate/trap labels continue to annotate the candidate list.

## Sequencing

| Week | Track A | Track B | Track C | Track D |
|---|---|---|---|---|
| 1 | atlas automated axes | recorder retargeting; weather capture live | — | forward pre-registration (if approved) |
| 2 | judgment pass + ranked atlas | weather archive backfill | weather model v0 (climatology baseline) | — |
| 3–4 | — | capture for target #2 (per atlas) | weather model v1 (calibrated ensemble); corpus backtest | model registry + gates doc |
| 5–8 | — | — | iterate v1; target #2 model v0 | shadow ladder for anything passing backtest |
| ~10 | **program checkpoint:** forward-test verdict + weather backtest verdict → venue decision (pre-committed) | | | |

The week-10 checkpoint is the operator's pre-committed venue evaluation: if
the forward test fails AND no model clears its backtest gate, the findings
book records a venue verdict and the factory's next hunting ground becomes
the agenda. This checkpoint exists to prevent both premature abandonment and
indefinite drift.
