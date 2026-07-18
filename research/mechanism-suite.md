# Multi-mechanism alpha suite v1

Registry SHA-256: `a7edf1eb3b33cd7d3216430e972039d24f1317da239ae747de68fe94f4718e67`

Every result is retrospective. Qualification requires three chronological folds, 50 independent events per fold, mean minus two clustered standard errors above 7%, family FDR, and suite-wide FDR. Historical qualification is not deployment.

## Search funnel by mechanism

| family | cells | fold survivors | family-FDR survivors | suite survivors |
|---|---:|---:|---:|---:|
| aggressor-imbalance | 320 | 0 | 0 | 0 |
| calendar-month | 576 | 0 | 0 | 0 |
| calendar-weekday | 448 | 0 | 0 | 0 |
| conditional-maker-selection | 798 | 4 | 1 | 0 |
| early-close-risk | 96 | 0 | 0 | 0 |
| event-structure | 192 | 0 | 0 | 0 |
| listing-lifecycle | 470 | 1 | 0 | 0 |
| price-path-dependence | 288 | 1 | 1 | 1 |
| price-staleness | 256 | 0 | 0 | 0 |
| recent-activity | 256 | 0 | 0 | 0 |
| recurring-series-residual | 30918 | 0 | 0 | 0 |
| rule-objectivity | 192 | 0 | 0 | 0 |
| settlement-source | 144 | 0 | 0 | 0 |
| sibling-lead-lag | 160 | 0 | 0 | 0 |
| two-sided-close-calibration | 1358 | 1 | 0 | 0 |

## Best surviving evidence per family

### aggressor-imbalance

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| T-30d|0.2:0.4|01-05|no | False | 3 | 0.2761 | 0.02002 | 1.000000 | 1.000000 |
| T-7d|0.8:1|41-60|yes | False | 28 | 0.2394 | -6.911578 | 1.000000 | 1.000000 |
| T-30d|0.4:0.6|01-05|no | False | 2 | 0.2027 | -0.046253 | 1.000000 | 1.000000 |
| T-30d|0.8:1|01-05|no | False | 24 | 0.1530 | -0.07738 | 1.000000 | 1.000000 |
| T-30d|0.6:0.8|01-05|no | False | 2 | 0.0595 | -0.246782 | 1.000000 | 1.000000 |

### calendar-month

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| T-30d|12|01-05|no | False | 59 | 0.1243 | -0.025732 | 0.016704 | 0.264422 |
| T-30d|7|06-10|no | False | 7 | 0.8642 | 0.180028 | 1.000000 | 1.000000 |
| T-30d|12|11-20|no | False | 20 | 0.8207 | 0.320085 | 1.000000 | 1.000000 |
| T-7d|5|96-99|yes | False | 7 | 0.4540 | 0.263946 | 1.000000 | 1.000000 |
| T-30d|12|06-10|no | False | 24 | 0.4446 | -0.109392 | 1.000000 | 1.000000 |

### calendar-weekday

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| T-1d|4|11-20|no | False | 521 | 5.3729 | -2.987701 | 0.021056 | 0.285697 |
| T-3d|4|96-99|yes | False | 3 | 0.5758 | -0.552346 | 1.000000 | 1.000000 |
| T-7d|7|01-05|no | False | 22 | 0.5373 | -0.172416 | 1.000000 | 1.000000 |
| T-3d|2|11-20|no | False | 265 | 0.2965 | -4.298776 | 1.000000 | 1.000000 |
| T-1d|4|01-05|no | False | 593 | 0.2920 | -1.500193 | 1.000000 | 1.000000 |

### conditional-maker-selection

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| Politics|7-30d|01-05|no | True | 87 | 0.3485 |  | 0.036708 | 0.285697 |
| Climate and Weather|0-7d|96-99|no | True | 372 | 126.2523 |  | 1.000000 | 1.000000 |
| Financials|0-7d|96-99|no | True | 117 | 14.1139 |  | 1.000000 | 1.000000 |
| Economics|7-30d|11-20|no | True | 202 | 0.4739 |  | 1.000000 | 1.000000 |
| Commodities|7-30d|96-99|no | False | 55 | 38.4131 |  | 1.000000 | 1.000000 |

### early-close-risk

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| T-90d|false|61-80|no | False | 3 | 7.8197 | 4.597447 | 1.000000 | 1.000000 |
| T-7d|false|06-10|no | False | 3 | 2.5974 | 0.166664 | 1.000000 | 1.000000 |
| T-90d|false|21-40|no | False | 1 | 1.2355 | -0.738586 | 1.000000 | 1.000000 |
| T-30d|false|06-10|no | False | 1 | 0.9476 | -0.111506 | 1.000000 | 1.000000 |
| T-7d|false|01-05|no | False | 6 | 0.7483 | 0.204434 | 1.000000 | 1.000000 |

### event-structure

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| T-90d|1:2|81-95|yes | False | 4 | 0.4081 | -0.122311 | 1.000000 | 1.000000 |
| T-30d|2:4|01-05|no | False | 17 | 0.2051 | 0.041165 | 1.000000 | 1.000000 |
| T-90d|1:2|01-05|no | False | 24 | 0.1364 | 0.043989 | 1.000000 | 1.000000 |
| T-90d|2:4|06-10|no | False | 11 | 0.1260 | -0.132173 | 1.000000 | 1.000000 |
| T-30d|1:2|96-99|yes | False | 4 | 0.1257 | -0.204664 | 1.000000 | 1.000000 |

### listing-lifecycle

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| Economics|L+30d|01-05|no | True | 50 | 0.1319 |  | 1.000000 | 1.000000 |
| Commodities|L+30d|81-95|no | False | 1 | 8.4577 |  | 1.000000 | 1.000000 |
| Health|L+7d|01-05|no | False | 25 | 4.9854 |  | 1.000000 | 1.000000 |
| Health|L+7d|96-99|yes | False | 31 | 4.4914 |  | 1.000000 | 1.000000 |
| Commodities|L+7d|11-20|no | False | 21 | 2.7824 |  | 1.000000 | 1.000000 |

### price-path-dependence

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| T-1d->T-6h|-2:2|01-05|no | True | 1079 | 4.0127 | 0.009667 | 0.000096 | 0.012157 |
| T-1d->T-6h|-100:-10|01-05|no | False | 1804 | 2.7792 | -3.592536 | 0.000000 | 0.000000 |
| T-1d->T-6h|3:9|96-99|yes | False | 131 | 6.9700 | -0.026216 | 0.000096 | 0.012157 |
| T-1d->T-6h|3:9|01-05|no | False | 43 | 6.4366 | -1.240952 | 1.000000 | 1.000000 |
| T-7d->T-3d|3:9|01-05|no | False | 1 | 2.0002 | 0.72642 | 1.000000 | 1.000000 |

### price-staleness

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| T-1d|0.2:1|06-10|no | False | 557 | 1.1829 | -2.488061 | 1.000000 | 1.000000 |
| T-7d|0.01:0.05|81-95|yes | False | 9 | 0.1268 | -2.572156 | 1.000000 | 1.000000 |
| T-30d|0:0.01|96-99|yes | False | 13 | 0.0121 | -0.072434 | 1.000000 | 1.000000 |
| T-30d|0.01:0.05|01-05|no | False | 67 | 0.0039 | -0.089522 | 1.000000 | 1.000000 |
| T-30d|0.2:1|01-05|no | False | 78 | -0.0485 | -0.149573 | 1.000000 | 1.000000 |

### recent-activity

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| T-1d|0:10|01-05|no | False | 1146 | 1.1566 | -0.551953 | 0.017920 | 0.364720 |
| T-1d|100:1000|06-10|no | False | 805 | 2.1157 | -3.597622 | 0.175360 | 1.000000 |
| T-1d|0:10|81-95|yes | False | 147 | 1.7645 | -0.470497 | 0.592192 | 1.000000 |
| T-1d|0:10|11-20|no | False | 429 | 0.8991 | -5.668956 | 0.642731 | 1.000000 |
| T-3d|0:10|11-20|no | False | 286 | 0.8132 | -2.048867 | 0.592192 | 1.000000 |

### recurring-series-residual

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| KXWINDSORWEST|T-7d|01-05|yes | False | 1 | 5146.8320 | 5174.548894 | 1.000000 | 1.000000 |
| KXVRASCOTUSVOTE|T-7d|96-99|no | False | 1 | 5146.8320 | 5199.316217 | 1.000000 | 1.000000 |
| KXVOTEPERCENTPVV|T-7d|96-99|no | False | 1 | 5146.8320 | 5175.469867 | 1.000000 | 1.000000 |
| KXTARIFFCAN|T-7d|01-05|yes | False | 1 | 5146.8150 | 5174.531925 | 1.000000 | 1.000000 |
| KXH100MAX|T-7d|01-05|yes | False | 1 | 5146.8150 | 5171.540912 | 1.000000 | 1.000000 |

### rule-objectivity

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| unclassified|T-7d|81-95|yes | False | 1 | 2.3346 | -0.4228488367844403 | 1.000000 | 1.000000 |
| unclassified|T-7d|61-80|yes | False | 1 | 1.6006 | -3.002687209188071 | 1.000000 | 1.000000 |
| official_act|T-30d|06-10|no | False | 1 | 0.8133 | 0.6455661418511931 | 1.000000 | 1.000000 |
| unclassified|T-30d|06-10|no | False | 7 | 0.5028 | -0.07848093028446276 | 1.000000 | 1.000000 |
| official_act|T-90d|06-10|no | False | 1 | 0.3029 | 0.12868777252464592 | 1.000000 | 1.000000 |

### settlement-source

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| T-30d|exchange_or_data|06-10|no | False | 2 | 0.7936 | -0.184248 | 1.000000 | 1.000000 |
| T-90d|exchange_or_data|06-10|no | False | 3 | 0.2958 | -0.081459 | 1.000000 | 1.000000 |
| T-30d|exchange_or_data|96-99|yes | False | 4 | 0.1712 | -0.151889 | 1.000000 | 1.000000 |
| T-90d|exchange_or_data|96-99|yes | False | 1 | 0.0734 | 0.030228 | 1.000000 | 1.000000 |
| T-90d|media_or_other|11-20|no | False | 10 | 0.0356 | -0.234403 | 1.000000 | 1.000000 |

### sibling-lead-lag

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| T-7d->T-1d|-100:-10|11-20|no | False | 1 | 4.9488 | -8.673164 | 1.000000 | 1.000000 |
| T-3d->T-1d|10:100|01-05|no | False | 35 | 4.1801 | 1.10814 | 1.000000 | 1.000000 |
| T-7d->T-1d|10:100|01-05|no | False | 15 | 2.9249 | -1.168802 | 1.000000 | 1.000000 |
| T-7d->T-1d|3:9|01-05|no | False | 25 | 1.3655 | -1.546109 | 1.000000 | 1.000000 |
| T-3d->T-1d|3:9|96-99|yes | False | 28 | 0.6717 | -0.812315 | 1.000000 | 1.000000 |

### two-sided-close-calibration

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| Economics|T-30d|11-20|no | True | 57 | 0.3419 |  | 1.000000 | 1.000000 |
| World|T-1h|41-60|no | False | 2 | 5211.3036 |  | 1.000000 | 1.000000 |
| Companies|T-1h|41-60|yes | False | 1 | 4395.0659 |  | 1.000000 | 1.000000 |
| Elections|T-1h|41-60|yes | False | 3 | 4128.7004 |  | 1.000000 | 1.000000 |
| Companies|T-1h|61-80|yes | False | 2 | 1906.6477 |  | 1.000000 | 1.000000 |

## Metadata-dependent registered tests

Rule objectivity, ladder monotonicity, and mutually exclusive event sums are reported by `research/metadata-suite.md` after the historical metadata backfill. Rule cells join the complete suite-wide correction; multi-leg structures remain descriptive until simultaneous historical or live books exist.

Full machine-readable evidence: `data/derived/mechanism_results.parquet` and `data/derived/mechanism_periods.parquet`.
