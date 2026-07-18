# Weather-alpha v1 — main-loop review and v2 specification (2026-07-18)

Independent review of `research/weather-alpha-results.md` (registry SHA
`10e376d5…`). Numbers recomputed from `data/derived/` artifacts, not read
from the report. Section 3 is a post-hoc diagnostic and qualifies nothing.

## 1. Verification

- Funnel reproduced: 268 registered external-data cells → 0 three-fold
  passes → 0 survivors. Brier scores recomputed exactly (T-6h model 0.140421
  vs market 0.020802; T-1d 0.148054 vs 0.112153). Panel: 220,320 strategy
  rows, 9,784 events, 20 stations. The pipeline runs what it registered.

## 2. The negative result is overdetermined — two design handicaps

1. **Taker economics only.** `add_strategy_economics` prices every strategy
   as a taker: last print + 2¢ spread reserve + full taker fee. The
   program's central structural finding is that identical signals die as
   taker and live as maker. v1 tested the model exclusively through the
   execution channel known to kill everything; zero survivors was decided
   before model quality entered.
2. **Unfair information set at T-6h.** The model is yesterday's GFS run
   (leads 1–7d, +6h publication lag) with no intraday observations. At T-6h
   a daily-high market's settlement variable is partially *realized* — the
   market is watching the thermometer; the model cannot. The market's
   0.0208 Brier at T-6h measures access to realized data, not forecasting
   genius. T-1d (target day not yet begun) is the fair horizon, and there
   the gap is far smaller (0.148 vs 0.112) despite GFS being the weakest
   major model and the absolute calibration being visibly off.

Conclusion: v1 disproves "beat the market with a stale global model priced
as a taker." It does not test the program's actual hypothesis.

## 3. Post-hoc diagnostic: the model ranks tails even though its levels are wrong

(Thresholds chosen after seeing v1; labeled diagnostic, drives v2's
registration, proves nothing by itself.)

T-1d, market-priced ≤5¢ tails, split by raw model view:

| model view | n | events | market implied | realized YES | model mean |
|---|---:|---:|---:|---:|---:|
| model agrees dead (≤1%) | 1,723 | 1,360 | 1.95% | **0.58%** | 0.4% |
| model lukewarm (1–5%) | 3,427 | 2,904 | 2.12% | **1.02%** | 2.9% |
| model says alive (>5%) | 12,934 | 7,083 | 2.51% | **1.62%** | 18.5% |

The market prices these three groups nearly identically; realized outcomes
separate monotonically 3×. The model's *levels* are badly calibrated (18.5%
claimed vs 1.6% realized in the "alive" group — GFS sigma far too wide) but
its *ranking* carries real tail information the market has not priced.

Favorites mirror, T-1d, market ≥95¢: in 51 rows where the model doubted
(<95%), the market implied 97.2% and only **72.5%** settled YES. Small
sample — but it names the mechanism behind the structural suite's
unexplained `Climate and Weather|0-7d|96-99|no` maker cell: the model can
identify *which* favorite-lockers are overpaying.

Same monotone separation holds at T-6h (0.03% / 0.15% / 0.33%), where the
market is sharper overall.

## 4. v2 specification (register before running; this section is the contract)

1. **Maker-channel economics as primary.** Rest at last print (no reserve),
   maker fees only, hold to settlement — the validated collection channel.
   Taker economics reported as a secondary robustness column, never a gate.
2. **Recalibration layer.** Map raw model probability → calibrated
   probability with a monotone fit trained *only on the discovery fold*;
   applied out-of-fold. The ranking information is real; the levels are the
   broken part — fix the levels, keep the ranking.
3. **Intraday state for T-6h.** New capture: hourly station observations →
   point-in-time running daily max/min. At T-6h the model must condition on
   the day so far, as the market does. (Capture-first rule applies: archive
   from now; historical hourly obs backfill where NCEI archives allow.)
4. **Better forecast source where point-in-time archives exist** (higher-
   skill ensembles via the same previous-runs mechanism); GFS retained as
   the fallback and for continuity.
5. **Registered families (tail-focused, maker-channel):**
   - *Tail-veto NO*: rest NO on ≤5¢ tails where calibrated model P(YES) is
     below a registered threshold ladder.
   - *Favorite-fragility NO*: rest NO at 96–99¢ where the calibrated model
     doubts the favorite by a registered margin (the mirror trade).
   - Both: three chronological folds, ≥50 events per fold, economic gate
     with carry and clustered SEs, matched market-only baselines
     (the condition must beat "rest NO on every tail"), family + combined
     suite FDR, day-clustered robustness reported alongside.
6. **Kill condition, pre-committed:** if the *calibrated* model shows no
   out-of-fold monotone separation of realized tail rates, weather modeling
   closes; the atlas's #2 target (CPI/ALFRED complex) moves up.

## 5. What this changes

v1's "the market wins" headline is replaced by: *the market wins at levels;
the model wins at ranking tails; v2 tests whether ranked tails plus the
maker channel clear the economic gate.* The synchronized-day defense also
becomes concrete: "model says alive" days are the step-aside signal the
correlated-loss cap needs.
