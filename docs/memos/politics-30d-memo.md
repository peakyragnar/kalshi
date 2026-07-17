# Structure memo — Politics · enter T−30d · YES 1–5¢ (rest NO)

> **Status update 2026-07-17.** Correct close-time anchoring preserves the
> economics in all three historical folds, but the early fold has only 26
> independent events versus the registered 50-event minimum. Status is
> INSUFFICIENT SUPPORT / live monitored, not newly qualified. The original memo
> remains below as an audit trail.

**Cell qualification (Phase 3 map):** discovery +30.4%/yr (SE 1.6), confirmation
+28.7%/yr (SE 3.5), both clear 7% at 2 clustered SE. Confirmation composition:
366 snapshots, 216 events, **208 distinct series** — max single-series share 4%.
Mean position: NO at ~97.9¢, ~30d hold, +2.3¢ premium per winning contract.

## 0. Tail risk — the binding risk of this cell

The cell sells ~2.3% insurance against "the dramatic thing happens." Observed
tail rate in confirmation: **1/366 = 0.27%** (the loss: `KXVETOCOUNT-26-1`,
a 2¢ market on Trump vetoes that settled YES). Because one observed event is a
thin basis for a tail estimate:

- 95% Poisson upper bound on the true tail rate: **~1.3% per position-month**
- Return at that pessimistic bound: ~+15%/yr with carry — **still above hurdle**
- Hurdle-breakeven tail rate: **~1.9%** — 7× the observed rate, 1.5× the
  pessimistic bound

The cell survives even a deliberately pessimistic tail reading. Tail *clustering*
is the residual worry (one news shock hitting several propositions at once), but
the propositions are unusually idiosyncratic — vetoes, foreign trips, tariff
thresholds share no common trigger the way index strikes do. Diversification
across all ~200 series is mandatory, not optional.

## 1. Who sets the marginal price — and why it should persist

Screen D: crossing flow in these markets is uninformed retail buying "it could
happen" lottery tickets; resting side wins in every horizon bucket. Why no
professional competition: hundreds of tiny novelty markets, each needing its own
rulebook read, with ~$8k average restable depth — **below any institutional cost
structure**. The edge persists precisely because it doesn't scale; a patient
individual operator with automation is the right-sized predator.

## 2. Rulebook risk — the main diligence item

Settlement sources are news/official records; propositions hinge on verbs
("meet," "visit," "pardon," "impose") and deadline wording. Void frequency is
unmeasurable from the settled feed (voids never reach it) — treat drafting risk
as real. **Before deployment: read the rulebooks of the top ~20 series by
intended exposure; skip any with ambiguous verbs or discretionary sources.**

## 3. Regulatory exposure

Political event contracts carry the deployment universe's highest regulatory
attention short of sports. A mid-hold adverse ruling could suspend or unwind
markets. Mitigants: 30-day holds limit exposure windows; positions are NO-side
(unwind at mark likely favorable). **Verify current litigation/regulatory status
of political event contracts before first dollars** — not asserted here.

## 4. Liquidity profile

~$5.0M restable (top-3 NO levels) across 617 open markets now; ≈$8k/market.
Strategy holds to settlement, so exit cost applies only if the thesis breaks.
Fills arrive with news-driven retail bursts; expect lumpy, not steady, deployment.
Realistic initial book: low tens of thousands of dollars without moving books —
consistent with the plan's $5–10k first tranche.

## 5. Dataset requirement (layer 2)

The forecasting edge for this family is a **base-rate library for political
actions**: DOJ pardon statistics, POTUS travel/schedule records, Federal
Register/USTR tariff actions, veto history — all public, all automatable with
the existing OSINT/govt-data stack. Use: not to out-forecast each market, but to
**skip propositions whose true tail rate is elevated** (the veto loss was
plausibly predictable from veto-threat news flow). Selection, not prediction.

## Verdict (analysis, not advice)

Primary cell. Robust to pessimistic tail math, maximally diversified, durable
counterparty story, capacity adequate for planned size. Open items before
dollars: rulebook read (§2), regulatory status check (§3), escrow-carry answer.
