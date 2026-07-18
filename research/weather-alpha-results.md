# Weather external-alpha suite v1

Registry SHA-256: `10e376d56a9eea5003ae6b87a6b088944da2442dec98dafe562dc3c23032b93b`

This is a retrospective calibration test, not a historical fill claim. Forecasts are joined by conservative availability time; entries use last print plus a 2¢ spread reserve and taker fee. Every conditional rule must beat a matched market-only baseline.

## Coverage

- Forecast-qualified strategy rows (YES and NO sides): **220,320**
- Independent weather events: **9,784**
- Settlement stations: **20**
- Kalshi contracts: **56,370**

## Probability benchmark

Lower Brier score is better. This is a diagnostic, not a trading return.

| horizon | contract observations | GFS model | Kalshi price |
|---|---:|---:|---:|
| T-6h | 56,239 | 0.140421 | 0.020802 |
| T-1d | 53,921 | 0.148054 | 0.112153 |

## Search funnel

| stage | cells |
|---|---:|
| registered external-data tests | 268 |
| passed all three folds | 0 |
| survived family FDR | 0 |
| survived combined structural + external suite FDR | 0 |

## Families

| family | cells | fold passes | family FDR | final |
|---|---:|---:|---:|---:|
| weather-city-disagreement | 160 | 0 | 0 | 0 |
| weather-level-disagreement | 32 | 0 | 0 | 0 |
| weather-price-disagreement | 40 | 0 | 0 | 0 |
| weather-revision-underreaction | 12 | 0 | 0 | 0 |
| weather-staleness-disagreement | 24 | 0 | 0 | 0 |

## Best evidence per family

### weather-city-disagreement

| cell | folds | min events | annual lower | hold lower | uplift lower | family q | combined q | fold pass | final |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| miami-international|T-1d|low|no | 1 | 190 | -1.204768 | 0.002576 | 1.532293 | 1.000000 | 1.000000 | False | False |
| denver-international|T-1d|low|no | 1 | 166 | -7.799904 | -0.017671 | -8.882682 | 1.000000 | 1.000000 | False | False |
| seattle-tacoma|T-1d|low|no | 1 | 98 | -16.671731 | -0.057834 | -9.473430 | 1.000000 | 1.000000 | False | False |
| oklahoma-city-will-rogers|T-1d|low|no | 1 | 87 | -16.830209 | -0.058612 | -12.174625 | 1.000000 | 1.000000 | False | False |
| houston-hobby|T-1d|low|no | 1 | 97 | -20.619983 | -0.068387 | -11.245357 | 1.000000 | 1.000000 | False | False |

### weather-level-disagreement

| cell | folds | min events | annual lower | hold lower | uplift lower | family q | combined q | fold pass | final |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| T-1d|edge>=10|low|no | 1 | 1946 | 9.118832 | 0.033128 | -5.838052 | 1.000000 | 1.000000 | False | False |
| T-1d|edge>=5|low|no | 1 | 2206 | 1.095191 | 0.005240 | -7.815074 | 1.000000 | 1.000000 | False | False |
| T-1d|edge>=3|low|no | 1 | 2267 | -1.195268 | -0.002786 | -8.224124 | 1.000000 | 1.000000 | False | False |
| T-1d|edge>=0|low|no | 1 | 2343 | -3.910505 | -0.012117 | -8.932977 | 1.000000 | 1.000000 | False | False |
| T-1d|edge>=0|high|no | 3 | 1056 | -25.679968 | -0.089470 | -8.125580 | 1.000000 | 1.000000 | False | False |

### weather-price-disagreement

| cell | folds | min events | annual lower | hold lower | uplift lower | family q | combined q | fold pass | final |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| T-6h|61-80|low|yes | 1 | 1 | 319.020271 | 0.420290 | 414.186425 | 1.000000 | 1.000000 | False | False |
| T-1d|01-20|low|no | 1 | 145 | 144.848753 | 0.526162 | -272.288523 | 1.000000 | 1.000000 | False | False |
| T-6h|81-99|high|yes | 1 | 2 | 69.308702 | 0.119582 | 90.221974 | 1.000000 | 1.000000 | False | False |
| T-1d|81-99|low|yes | 1 | 1 | 66.772441 | 0.209877 | 101.198784 | 1.000000 | 1.000000 | False | False |
| T-6h|41-60|low|no | 1 | 214 | 32.926292 | 0.047702 | -67.115528 | 1.000000 | 1.000000 | False | False |

### weather-revision-underreaction

| cell | folds | min events | annual lower | hold lower | uplift lower | family q | combined q | fold pass | final |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| T-1d->T-6h|update>=3|low|no | 1 | 2261 | -556.982121 | -0.748384 | -106.253962 | 1.000000 | 1.000000 | False | False |
| T-1d->T-6h|update>=5|low|no | 1 | 2239 | -566.778400 | -0.760726 | -107.253547 | 1.000000 | 1.000000 | False | False |
| T-1d->T-6h|update>=10|low|no | 1 | 2184 | -596.638954 | -0.800277 | -120.883703 | 1.000000 | 1.000000 | False | False |
| T-1d->T-6h|update>=10|low|yes | 1 | 2074 | -810.087776 | -1.111581 | 8.889876 | 1.000000 | 1.000000 | False | False |
| T-1d->T-6h|update>=5|low|yes | 1 | 2219 | -828.462604 | -1.132428 | -9.133134 | 1.000000 | 1.000000 | False | False |

### weather-staleness-disagreement

| cell | folds | min events | annual lower | hold lower | uplift lower | family q | combined q | fold pass | final |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| T-1d|stale|low|no | 1 | 100 | 203.054087 | 0.714054 | 169.608165 | 1.000000 | 1.000000 | False | False |
| T-1d|aging|low|no | 1 | 627 | -11.256424 | -0.035543 | -19.718335 | 1.000000 | 1.000000 | False | False |
| T-1d|fresh|low|no | 1 | 1810 | -16.798497 | -0.057456 | -24.807952 | 1.000000 | 1.000000 | False | False |
| T-1d|stale|high|no | 3 | 9 | -17.330835 | -0.056938 | -15.434325 | 1.000000 | 1.000000 | False | False |
| T-1d|fresh|high|no | 3 | 424 | -34.945582 | -0.149290 | -28.765899 | 1.000000 | 1.000000 | False | False |

## Interpretation boundary

The forecast archive is a third-party point extraction of NOAA GFS operational runs. NOAA NCEI Daily Summaries provide settlement-station observations for expanding error calibration. No current or future observation is allowed into a forecast probability. A historical survivor would still require live simultaneous books, forward shadow evidence, capacity, and operator approval.
