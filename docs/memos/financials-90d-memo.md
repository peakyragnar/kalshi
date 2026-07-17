# Structure memo — Financials · enter T−90d · YES 1–10¢ (rest NO), ex-ticket

> **Superseded 2026-07-17.** This memo used the old
> `max(close_time, expiration_time)` horizon. The corrected close-anchored atlas
> finds a middle-fold lower bound of −13.1%; this cell is RED and its prior
> qualification is withdrawn. The text below is retained as an audit trail.

**Cell qualification:** original merged cell +17.9%/+14.8%/yr. **Re-run excluding
ticket-price series** (KXNBAFINALSPRICE, KXWCPRICE, KXNHLPRICE, KXRTICKET,
KXDTICKET — sports-adjacent, recommend permanent exclusion per the no-sports
decision): discovery +17.9%/yr (SE 1.8), confirmation **+16.8%/yr (SE 2.8)**,
conservative bound +11.1% — qualification *improved* without them.
Confirmation ex-ticket: 183 snapshots, 71 events, 61 series. Mean position:
NO at ~96¢, ~90d hold, +3.9¢ per winning contract.

## 0. Tail risk — thinner cushion, and correlated

Observed tail: **1/183 = 0.55%** (the loss: `KXINXHIGH-25-AUG01-6144.15` — a 9¢
market that the S&P would set an all-time high by Aug 2025; the rally made it).

- 95% Poisson upper bound on true tail rate: **~2.6% per position-quarter**
- Return at that bound: **~+8%/yr with carry — barely above the 7% hurdle**
- Hurdle-breakeven tail: ~2.9%

Worse than the raw math: the observed loss is **index-linked**. A strong equity
rally (or crash) settles many "will index reach X" strikes YES *simultaneously* —
this cell's tails cluster by construction in a way the Politics cell's do not.
The IPO-timing and company-ops series are more idiosyncratic; the index-range
series are the correlated block. Consider capping index-linked series as a
sub-limit within the cell.

## 1. Who sets the marginal price

Mixed. IPO-timing and company-ops markets: retail flow (Screen D economics
apply). Index yearly ranges: professionally quotable (options-hedgeable), but
the deep tails 90d out are patrolled loosely — the 16.8% suggests real residual.
Durability is weaker than Politics: these markets are exactly where an
institutional MM could eventually tighten.

## 2. Rulebook risk

Cleaner than Politics: settlement sources are quantitative (index closes,
official company reports, exchange listings). Residual wording risk in IPO
markets ("announce" vs "file" vs "list") — read those rulebooks specifically.

## 3. Regulatory exposure

Low. Economic/financial event contracts are squarely inside the CFTC remit;
no litigation overhang comparable to politics/sports.

## 4. Liquidity profile

Restable depth in the merged category-bucket ≈ $12.4M across 1,258 open markets,
but concentrated in index strikes (the sub-family with correlated tails and the
strongest professional presence). Fills in IPO/company-ops series are thinner
and news-driven.

## 5. Dataset requirement (layer 2)

Two concrete pipelines, both automatable in the existing stack:
1. **EDGAR filings feed** (free, structured): S-1/F-1 filings and amendments
   give hard early signal on IPO-timing markets — likely the single highest
   edge-per-effort dataset in either cell.
2. **Options-implied distributions** (CBOE): for index-range markets, the SPX
   options smile prices the same tail — divergence between Kalshi and options
   pricing is a direct signal for both entry selection and detecting when the
   Kalshi discount has been arbed away.

## Verdict (analysis, not advice)

Secondary cell. Qualified and cleaner on rulebook/regulatory risk, but the tail
cushion is thin at pessimistic bounds and the worst tails are mutually
correlated through the index. If deployed: smaller allocation than Politics,
sub-cap on index-linked series, and the EDGAR pipeline built first.
