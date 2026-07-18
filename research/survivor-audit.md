# Survivor execution audit

Registered survivor: `T-1d->T-6h|-2:2|01-05|no`.

The candidate matched **30,252 recorded prints / 5,465,854 contracts** by exact ticker, timestamp, and price. Of those, **23,030 prints / 4,612,698 contracts** had a YES aggressor, which means the desired NO side was the historical maker fill.

Recorded contract count is evidence of traded scale, not a claim that our counterfactual order would have received every contract. Historical top-of-book depth is unavailable.

The T-6h decision price was last printed a median **2.88 hours** earlier (90th percentile **12.09 hours**). Execution returns therefore start at the actual print timestamp, not the nominal T-6h decision time.

Largest event share of maker-side matched contracts: **1.95%**.

## Fold evidence by executable role

| role | fold | fills | events | markets | contracts | mean hold | loss rate | ann. mean | ann. 2-SE lower |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| maker_no | early | 923 | 560 | 702 | 113,886 | 1.467% | 0.325% | 6.295 | 3.793 |
| maker_no | middle | 2,942 | 1,421 | 2,169 | 1,165,320 | 1.250% | 0.102% | 6.339 | 5.400 |
| maker_no | recent | 19,165 | 7,365 | 14,046 | 3,333,492 | 1.036% | 0.183% | 5.747 | 4.588 |
| taker_no | early | 981 | 671 | 866 | 203,093 | 0.201% | 0.612% | 0.543 | -2.349 |
| taker_no | middle | 1,376 | 849 | 1,121 | 234,071 | 0.256% | 0.291% | 0.962 | -0.960 |
| taker_no | recent | 4,865 | 2,159 | 2,908 | 415,993 | -0.031% | 0.473% | -0.176 | -1.749 |

## Maker-side category distribution

| category | events | markets | contracts | mean hold | loss rate |
|---|---:|---:|---:|---:|---:|
| Climate and Weather | 7,263 | 12,425 | 2,947,915 | 1.091% | 0.075% |
| Politics | 644 | 1,307 | 541,316 | 1.332% | 0.173% |
| Economics | 432 | 955 | 363,691 | 1.132% | 0.355% |
| Science and Technology | 175 | 622 | 267,910 | 0.720% | 0.140% |
| Elections | 212 | 429 | 245,214 | -0.371% | 1.795% |
| Financials | 397 | 688 | 159,763 | 1.220% | 0.695% |
| Commodities | 165 | 411 | 65,419 | 1.447% | 0.424% |
| Health | 35 | 42 | 11,197 | 1.999% | 0.000% |
| World | 13 | 25 | 8,423 | -1.360% | 3.571% |
| Companies | 8 | 13 | 1,849 | 2.593% | 0.000% |

## Maker-side category stability by fold

This breakdown is diagnostic and post-selection; it does not create separately qualified category cells.

| category | fold | fills | events | contracts | mean hold | loss rate | ann. 2-SE lower |
|---|---|---:|---:|---:|---:|---:|---:|
| Climate and Weather | early | 288 | 204 | 27,349 | 1.233% | 0.347% | 1.286 |
| Climate and Weather | middle | 2,025 | 1,020 | 752,645 | 1.251% | 0.000% | 5.843 |
| Climate and Weather | recent | 14,915 | 6,040 | 2,167,921 | 1.067% | 0.080% | 5.193 |
| Commodities | early | 6 | 5 | 86 | 3.465% | 0.000% | 8.906 |
| Commodities | middle | 1 | 1 | 25 | 5.263% | 0.000% | 15.696 |
| Commodities | recent | 701 | 159 | 65,308 | 1.424% | 0.428% | 3.878 |
| Companies | early | 1 | 1 | 46 | 2.041% | 0.000% | 5.723 |
| Companies | recent | 13 | 7 | 1,803 | 2.636% | 0.000% | 5.970 |
| Economics | early | 144 | 86 | 37,352 | 1.418% | 0.000% | 4.078 |
| Economics | middle | 149 | 86 | 88,688 | 1.498% | 0.000% | 6.917 |
| Economics | recent | 835 | 260 | 237,651 | 1.017% | 0.479% | -0.467 |
| Elections | middle | 91 | 22 | 94,362 | 0.083% | 1.099% | -10.937 |
| Elections | recent | 466 | 190 | 150,852 | -0.459% | 1.931% | -33.159 |
| Financials | early | 299 | 153 | 29,660 | 1.777% | 0.334% | 3.937 |
| Financials | middle | 93 | 59 | 42,731 | 1.252% | 1.075% | -10.426 |
| Financials | recent | 471 | 185 | 87,372 | 0.861% | 0.849% | -19.445 |
| Health | early | 32 | 24 | 7,284 | 2.121% | 0.000% | 3.790 |
| Health | middle | 2 | 2 | 12 | 2.051% | 0.000% | 6.634 |
| Health | recent | 21 | 9 | 3,901 | 1.810% | 0.000% | 0.097 |
| Politics | early | 148 | 83 | 11,979 | 1.097% | 0.676% | -3.868 |
| Politics | middle | 520 | 207 | 161,246 | 1.559% | 0.000% | 8.163 |
| Politics | recent | 1,066 | 355 | 368,091 | 1.254% | 0.188% | 5.799 |
| Science and Technology | early | 1 | 1 | 25 | 1.010% | 0.000% | 0.393 |
| Science and Technology | middle | 50 | 21 | 24,462 | 0.958% | 0.000% | 3.119 |
| Science and Technology | recent | 664 | 153 | 243,423 | 0.701% | 0.151% | -0.464 |
| World | early | 4 | 3 | 105 | 2.309% | 0.000% | 2.081 |
| World | middle | 11 | 3 | 1,149 | -6.546% | 9.091% | -237.299 |
| World | recent | 13 | 7 | 7,169 | 1.899% | 0.000% | 6.060 |
