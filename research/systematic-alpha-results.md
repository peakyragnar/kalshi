# Systematic alpha suite — final historical results

## Bottom line

The registered suite searched the market structure rather than testing only the
term-premium thesis. It evaluated **36,472 cells across 15 statistically
executable mechanism families**, plus two descriptive multi-leg mechanisms.
Seven cells passed all three chronological folds, two survived correction within
their family, and one survived correction across the entire suite.

That survivor is not a duration effect. It is a short-horizon price-path and
execution-role effect:

`T-1d->T-6h|-2:2|01-05|no`

At T−6h, the last YES trade is 1–5¢ and the price has changed by at least −2¢
but less than +2¢ since T−1d, with a new trade required after the earlier
decision. The trade being evaluated is NO. Historical reconstruction supports
only a resting NO order; crossing the spread does not survive.

## Search funnel

| Stage | Cells | Meaning |
|---|---:|---|
| Registered statistical tests | 36,472 | All generated cells enter the suite correction; unsupported cells receive p=1 |
| Passed all three folds | 7 | Economic lower bound and at least 50 independent events in early, middle, and recent |
| Survived family FDR | 2 | Benjamini–Hochberg correction inside the mechanism family |
| Survived suite FDR | 1 | Correction across the complete registered statistical search |

The 15 statistical families cover two-sided close calibration, listing
lifecycle, own-price path, sibling lead/lag, aggressor imbalance, recent
activity, staleness, recurring series, month, weekday, early-close risk, event
structure, settlement source, conditional maker selection, and rule
objectivity. Threshold-ladder monotonicity and mutually exclusive event sums are
reported separately because asynchronous historical last trades cannot prove
simultaneous execution.

## Survivor evidence

| Measure | Result |
|---|---:|
| Decisions | 21,812 |
| Minimum independent events in any fold | 1,079 |
| Family FDR q | 0.000096 |
| Suite FDR q | 0.012157 |
| Weakest absolute annualized 2-SE lower bound | 401.27% |
| Weakest matched-baseline annualized uplift lower bound | 0.97% |

The very large annualized number is a scaling artifact of a position held for
hours or days; it is not a claim that capital can compound at 401% with unlimited
capacity. The economically interpretable quantities are the realized return per
hold, loss rate, historical contract count, concentration, and forward fill
rate. The 0.97% weakest uplift lower bound also shows that the early-fold
incremental advantage over comparable category × horizon × price × side trades
is thin.

## Execution reconstruction

The survivor matched 30,252 historical prints by exact ticker, timestamp, and
price, representing 5,465,854 contracts. In
23,030 prints / 4,612,698 contracts, a YES aggressor hit a resting NO order—the
role the candidate needs. Recorded volume is evidence that trades occurred, not
a claim that a counterfactual order would have received all volume.

| Role | Fold | Fills | Events | Contracts | Mean return per hold | Loss rate | Annualized 2-SE lower |
|---|---|---:|---:|---:|---:|---:|---:|
| maker NO | early | 923 | 560 | 113,886 | 1.467% | 0.325% | 379.3% |
| maker NO | middle | 2,942 | 1,421 | 1,165,320 | 1.250% | 0.102% | 540.0% |
| maker NO | recent | 19,165 | 7,365 | 3,333,492 | 1.036% | 0.183% | 458.8% |
| taker NO | early | 981 | 671 | 203,093 | 0.201% | 0.612% | −234.9% |
| taker NO | middle | 1,376 | 849 | 234,071 | 0.256% | 0.291% | −96.0% |
| taker NO | recent | 4,865 | 2,159 | 415,993 | −0.031% | 0.473% | −174.9% |

The T−6h decision price was already 2.88 hours old at the median and 12.09 hours
old at the 90th percentile. Returns in the execution audit therefore begin at
the actual print time, not the nominal T−6h timestamp. The largest event was
1.95% of maker-side matched contracts.

Climate and Weather supplied 2,947,915 maker-side contracts, or 63.9% of the
matched maker volume. That is why point-in-time NOAA weather forecasts are the
next external-data priority. This category split is post-selection and does not
qualify a weather-only cell.

## What did not survive

- Conditional maker selection produced four three-fold passes and one
  family-FDR pass, but no suite-wide survivor.
- Listing lifecycle and two-sided close calibration each produced one
  three-fold pass, then failed FDR.
- Sibling lead/lag, aggressor imbalance, activity, staleness, recurring-series,
  calendar, early-close, event structure, settlement source, and rule
  objectivity produced no qualified cell.
- The original long-duration thesis did not produce a monotonic term premium.
  Carry remains part of the hurdle, not the source of the surviving edge.

## Multi-leg scans

The metadata suite found 36,416 adjacent threshold pairs. For above-threshold
ladders, 6.57%–13.26% of asynchronous pairs showed a signed gap of at least 2¢,
but only 12.15%–23.50% of pairs were printed within five minutes. Restricting to
those closer timestamps reduced the apparent gap rate to 1.29%–5.47%.
Below-threshold ladders were sparse, and none of their within-five-minute pairs
had a 2¢ violation.

It also found 125 complete mutually exclusive event observations. Most apparent
2¢ gaps used legs printed more than five minutes apart. These are leads for the
live book recorder, not historical arbitrage claims.

## Promotion boundary

The survivor is **historically qualified / shadow only**. It cannot become a
live rule until sealed-forward observations and captured books establish order
placement, fill probability, available depth, fees, event concentration, and
capacity. The research pipeline does not place or modify orders.
