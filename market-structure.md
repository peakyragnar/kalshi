# Kalshi Market Structure — Findings Book

**What this is.** The accumulated, validated findings of the market-structure project,
maintained as the single reference for any real-money decision. Every claim cites the
screen that produced it; every number is reproducible from the repo. Updated as new
evidence lands (forward settlements, recorder depth, live scans). This document
records what the data supports — the deployment decision itself belongs to the
operator and is gated by the Phase 3 map and the pre-committed kill rule.

**Data basis (as of 2026-07-16):** 2.73M settled deployment-tier markets (2021→2026),
46.3M fills with aggressor side, 430k price/outcome snapshots, order-book depth
recorder live since 2026-07-15. Full reports: `reports/screen_a.md`, `screen_d.md`,
`screen_b.md`, `coverage.md`.

---

## Part 1 — Validated findings

### F1. Long-dated YES is overpriced across the board; holding NO collects the gap
At horizons ≥30d, realized settlement frequency sits below implied probability in
every price bucket (e.g. 24¢ implied → 19.6% realized; 54¢ → 48.7%). The mirror:
resting NO positions earn a positive gross spread everywhere. At T−7d the pattern
is the classic S (longshots overpriced, favorites slightly underpriced); at ≥30d
even favorites stop being cheap. *(Screen A)*

### F2. The published anomaly is dead; the structural one survived
The academic "buy high-priced favorites" edge exists in pre-2025 data and is gone
(slightly reversed) in the last 12 months. The longshot-side overpricing persists
in the confirmation period with clustered errors well clear of zero. Easily
harvested edges decay after publication; capital-intensive ones survive. *(Screen A,
discovery/confirmation split)*

### F3. The bias is an average with sign flips — selection is mandatory
Series where professional forecasters concentrate price the OTHER way: Fed
decisions (+4.6pp), Payrolls (+7.5pp), GDP (+1.4pp) — fading YES there loses.
Elections are arbed nearly flat (+2.9%/yr fill-weighted). The richest maker
returns: Economics (+38%), Science/Tech (+34%), Politics (+21%) fill-weighted
with carry. A discovery-period exclusion rule ("drop series that lost") improved
confirmation-period returns — the selection idea survived out-of-sample. *(Screens
A + D; series dot-plot)*

### F4. Makers beat takers everywhere — adverse selection favors the resting side
Across 46.3M fills, the resting side out-returns the crossing side in every
horizon bucket, both periods, by +8 to +31pp per fill. Kalshi's crossing flow in
deployment categories is uninformed retail, not sharp flow. Maker fee is zero on
98.9% of series (130 series charge; pull per-series). Getting filled is good
news on this exchange. *(Screen D)*

### F5. There is NO term premium — the edge peaks at 30–90 days
Annualized NO edge by entry horizon: ~+63%/yr pooled at T−30, roughly halved at
T−90, ~zero at T−365. Confirmed at three identification levels including
within-market (same contract entered earlier vs later). Duration is a cost, not
a source: the per-hold discount grows too slowly with horizon to pay for the
extra lockup. **Hold 30–90d, recycle capital; never extend past ~90d for yield.**
*(Screen B)*

### F6. Returns are insurance-shaped; the edge is a portfolio property
Target cell (resting NO vs YES at 1–20¢, ≥30d): ~90% of positions win small
(≈ +5–6%/hold), ~10% lose everything. Mean +4.7%/hold on real maker fills.
Losses cluster by event and by news cycle. No single position ever earns "the
average" — only a diversified book held through the losers does. *(Screens A + D)*

### F7. Capacity, not edge, is the open constraint
Per dollar of flow actually absorbed, the target cell earned **+20.9%/yr with
carry** (confirmation period, clears the 7%-at-2SE rule). Per *event* equal-
weighted, **+5.4%/yr** — below the hurdle. Flow concentrates in liquid political/
economic events (top-10 events ≈ 19% of fills). A real book lives between the
two numbers, positioned by per-market depth — the recorder + map resolve this.
*(Screen D robustness)*

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

---

## Part 2 — The strategy the findings support (as tested, not as advised)

The single strategy every screen converges on:

- **Position:** rest NO-side maker orders (never cross the spread) in markets
  where YES trades at 1–20¢.
- **Horizon:** enter 30–90 days before settlement. Recycle proceeds on
  settlement. No positions past ~90d (F5).
- **Universe:** deployment categories (econ, climate, politics, world, companies,
  sci-tech, commodities, health) **minus** an exclusion list of professionally
  priced series (Fed, Payrolls, GDP class — formalized per-cell by the map) and
  minus Elections (arbed). No sports, no parlays, no crypto ladders (decision,
  Phase 0).
- **Diversification:** many small positions across unrelated events; losses
  cluster (F6), so event concentration is the primary portfolio risk.
- **Expected shape if history repeats:** high win rate, occasional −100%
  positions, net between ~5% and ~21%/yr including carry depending entirely on
  how much size the flow supports (F7). The honest planning number until the
  map says otherwise: low double digits at small size.

**What would falsify it going forward:** the calibration gap closing in newly
settled markets; maker-taker gap compressing (professionalizing flow); fill
rates collapsing. All three are tracked automatically (below).

---

## Part 3 — Gates still closed before real money

1. **The Phase 3 map — PASSED 2026-07-16: GO, 2 qualifying cells** (`reports/phase3_map.md`):
   - **Politics · enter T−30d · YES 1–5¢** (rest NO at 95–99¢): discovery +30.4%/yr
     (SE 1.6), confirmation +28.7%/yr (SE 3.5) — clears the 7%/2SE rule in both
     periods by wide margins. ~$5.0M restable now across 617 open markets.
   - **Financials · enter T−90d · YES 1–10¢**: +17.9% / +14.8%/yr, clears both
     periods. ~$12.4M restable across 1,258 open markets.
   - 15 near-misses (mostly Economics 30d mid-buckets, confirmation-positive but
     discovery-negative per F2's favorite flip) — re-evaluate as forward data accrues.
   - Remaining before deployment: Phase 4 memos on the two families.
2. **Capacity estimates** — recorder has days, wants weeks. Improves automatically.
3. **Escrowed-order carry** — one support ticket (F9).
4. **Void charging** — void frequency by series charged into cell edges at map
   time.
5. **Forward validation** — ~24k open markets settle over coming months and
   re-grade every finding on unseen data, cost-free.

## Part 4 — Standing infrastructure

- Recorder: launchd `com.exascale.kalshi-recorder`, 4×/day, ~24k books/run.
- Rebuild anything: `uv run python -m kalshi_data.{ingest_series,ingest_markets,
  ingest_trades,derive,coverage,screen_a,screen_b,screen_d}`.
- Tests: `uv run pytest` (29). Data: `data/` (gitignored, reproducible).

## Change log
- 2026-07-16: created after Screens A, B, D. Screen C production scan and the
  Phase 3 map are the open work items.
- 2026-07-16 (later): Phase 3 map PASSED — GO with 2 qualifying cells
  (Politics 30d 1–5¢; Financials 90d 1–10¢). Phase 4 memos are the open item.
- 2026-07-16 (later still): Phase 4 memos written (`memos/`). Financials cell
  re-qualified ex-ticket-price series (+16.8%/yr conf, bound +11.1%). Both
  cells' single observed tail losses identified and analyzed (Trump vetoes;
  S&P all-time-high — the latter index-correlated). Politics = primary cell,
  Financials = secondary with index sub-cap recommendation. Open before
  deployment: rulebook reads, regulatory status check, escrow-carry answer.
- 2026-07-16: Rulebook sweep complete (`reports/rulebook-sweep.md`): 36 series
  read, 22 GREEN / 12 YELLOW / 2 RED (KXCRYPTOSTRUCTURE, KXTARIFFCHECKS —
  categorical/attribution judgment conditions, excluded). No discretionary
  settlement language found anywhere. New selection rule: prefer act-conditions
  over announcement/attribution triggers.
