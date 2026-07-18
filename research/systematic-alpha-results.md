# Systematic alpha suite — expanded-universe historical results

## Bottom line

The registered suite searched market structure rather than only the original
term-premium thesis. It evaluated **55,236 cells across 15 statistical
families**, plus descriptive threshold-ladder and mutually exclusive-event
scans. Six cells passed all three chronological folds, one survived correction
inside its family, and **none survived the full suite-wide gate**.

There is therefore no new historically qualified alpha cell and no suite
candidate to promote to shadow or live trading. This is a negative result, not
proof that Kalshi is efficient: it means no tested rule cleared the registered
economic, support, matched-baseline, family-FDR, and suite-FDR requirements over
the expanded corpus.

## Search funnel

| Stage | Cells | Meaning |
|---|---:|---|
| Registered statistical tests | 55,236 | All generated cells enter correction; unsupported cells receive p=1 |
| Passed all three folds | 6 | Four maker-selection, one listing-lifecycle, one close-calibration cell |
| Survived family FDR | 1 | Politics, 7–30d, 1–5¢ YES / NO maker selection |
| Survived suite FDR and all gates | 0 | No historical qualifier |

The families cover close calibration, listing lifecycle, own-price path,
sibling lead/lag, aggressor imbalance, recent activity, staleness, recurring
series, month, weekday, early-close risk, event structure, settlement source,
conditional maker selection, and rule objectivity.

## Why the old candidate disappeared

The previous candidate was:

`T-1d->T-6h|-2:2|01-05|no`

It still has large absolute historical NO returns and at least **1,119 events in
its weakest fold**, but it no longer passes every matched-baseline economic
gate. Its weakest incremental annualized two-standard-error lower bound is
**−0.030996**, so the observed return cannot be distinguished robustly from
comparable category × horizon × price × side trades in every fold. Its tiny
p-value and q-value do not override a failed pre-committed economic gate.

The execution audit is consequently suppressed and now states that no
registered survivor exists. Historical prints from the previously selected cell
remain useful diagnostics, but calling it a survivor after the larger search
would be selection leakage.

## Near misses

- Conditional maker selection produced four three-fold passes. The best was
  `Politics|7-30d|01-05|no`: minimum 87 events, weakest annualized lower bound
  0.3485, family q=0.049496, but suite q=0.317607.
- Listing lifecycle produced one three-fold pass:
  `Economics|L+30d|01-05|no`, with exactly 50 events in its weakest fold. It did
  not survive family correction.
- Two-sided close calibration produced one three-fold pass:
  `Economics|T-30d|11-20|no`, minimum 57 events. It did not survive family
  correction.
- The price-path family has very small corrected q-values for several cells,
  including the old candidate, but none passes all registered fold/economic
  requirements.
- The other eleven statistical families produced no all-fold qualifier.

## Multi-leg scans

The metadata suite found **46,254 adjacent threshold pairs**. Above-threshold
asynchronous gaps of at least 2¢ occur in several folds, but only about
12%–23% of pairs were printed within five minutes; synchronized-gap rates are
materially lower. Below-threshold pairs are sparse and show no 2¢ gap among
the reported within-five-minute subsets.

It also found **125 mutually exclusive event observations**. Many apparent
gaps use legs printed more than five minutes apart. These remain leads for live
simultaneous book capture, not historical arbitrage claims.

## Research boundary

The corpus contains all current categories except crypto- and sports-themed
series, with `KXMVE*` parlays and versioned RED rulebooks excluded from the
research panel. Raw excluded records are retained for auditability. No orders
are placed or modified by this pipeline.

Future alpha work must either register a genuinely new mechanism or add
point-in-time external information—weather, company filings, government data,
or politics—before observing outcomes. Re-slicing these 55,236 results after
the fact is not a valid new test.
