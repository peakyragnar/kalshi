# Metadata-dependent mechanism results

Canonical historical metadata coverage: **2,867,025 / 2,888,361 markets**. The API returned **18,818** additional settled tickers, which are retained but do not enter the canonical universe without a join.

## Rule-language mechanism

Tested **192** rule-class cells; **0** survived three folds, event support, economic gates, matched-baseline uplift, family FDR, and suite FDR.

## Threshold-ladder dislocations

These are asynchronous last-trade calibration comparisons, not executable arbitrages. A live candidate still requires both legs to be offered simultaneously at the observed prices.

| direction | horizon | fold | pairs | events | gaps >=2c | rate | mean signed gap | within 5m | sync gap rate |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| above | T-1d | early | 1,268 | 309 | 137 | 10.80% | -14.920c | 12.15% | 3.25% |
| above | T-1d | middle | 4,291 | 704 | 342 | 7.97% | -11.822c | 17.04% | 1.50% |
| above | T-1d | recent | 25,135 | 2,212 | 3,187 | 12.68% | -5.985c | 23.31% | 5.22% |
| above | T-30d | early | 576 | 105 | 76 | 13.19% | -8.311c | 20.49% | 4.24% |
| above | T-30d | middle | 1,195 | 306 | 98 | 8.20% | -14.854c | 12.22% | 2.74% |
| above | T-30d | recent | 2,435 | 455 | 182 | 7.47% | -10.640c | 16.06% | 3.58% |
| above | T-7d | early | 860 | 155 | 111 | 12.91% | -9.602c | 13.26% | 4.39% |
| above | T-7d | middle | 2,558 | 523 | 195 | 7.62% | -14.346c | 11.88% | 1.64% |
| above | T-7d | recent | 7,675 | 1,026 | 779 | 10.15% | -8.724c | 16.13% | 3.96% |
| below | T-1d | early | 22 | 14 | 4 | 18.18% | -1.227c | 4.55% | 0.00% |
| below | T-1d | middle | 42 | 20 | 7 | 16.67% | -1.905c | 11.90% | 0.00% |
| below | T-1d | recent | 48 | 11 | 5 | 10.42% | -4.646c | 12.50% | 0.00% |
| below | T-30d | early | 10 | 6 | 1 | 10.00% | -5.400c | 0.00% | n/a |
| below | T-30d | middle | 24 | 12 | 1 | 4.17% | -10.083c | 12.50% | 0.00% |
| below | T-30d | recent | 21 | 8 | 5 | 23.81% | -7.667c | 9.52% | 0.00% |
| below | T-7d | early | 20 | 12 | 2 | 10.00% | -5.850c | 15.00% | 0.00% |
| below | T-7d | middle | 39 | 19 | 4 | 10.26% | -3.538c | 10.26% | 0.00% |
| below | T-7d | recent | 35 | 10 | 5 | 14.29% | -4.514c | 5.71% | 0.00% |

## Mutually exclusive event price sums

Candidate-style groups are identified from shared titles and distinct non-numeric choice labels. Final outcomes validate classification only; they are not used as a decision-time feature. Like ladders, the historical prices are asynchronous and do not prove all legs were executable together.

| horizon | fold | events | gaps >=2c | rate | mean gap | within 5m | exact-one outcome |
|---|---|---:|---:|---:|---:|---:|---:|
| T-1d | middle | 2 | 2 | 100.00% | 14.000c | 0.00% | 100.00% |
| T-1d | recent | 48 | 28 | 58.33% | 5.167c | 6.25% | 100.00% |
| T-30d | middle | 2 | 2 | 100.00% | 3.000c | 0.00% | 100.00% |
| T-30d | recent | 26 | 20 | 76.92% | 8.462c | 3.85% | 100.00% |
| T-7d | middle | 2 | 2 | 100.00% | 56.000c | 0.00% | 100.00% |
| T-7d | recent | 45 | 29 | 64.44% | 8.644c | 8.89% | 100.00% |
