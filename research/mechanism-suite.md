# Multi-mechanism alpha suite v1

Registry SHA-256: `4d8b1598c5dda54d2fbd18b2f652da782bd7bb74c45ed15112f41aab93f55bc3`

Every result is retrospective. Qualification requires three chronological folds, 50 independent events per fold, mean minus two clustered standard errors above 7%, family FDR, and suite-wide FDR. Historical qualification is not deployment.

## Search funnel by mechanism

| family | cells | fold survivors | family-FDR survivors | suite survivors |
|---|---:|---:|---:|---:|
| aggressor-imbalance | 320 | 0 | 0 | 0 |
| calendar-month | 576 | 0 | 0 | 0 |
| calendar-weekday | 448 | 0 | 0 | 0 |
| conditional-maker-selection | 1076 | 4 | 1 | 0 |
| early-close-risk | 96 | 0 | 0 | 0 |
| event-structure | 192 | 0 | 0 | 0 |
| listing-lifecycle | 656 | 1 | 0 | 0 |
| price-path-dependence | 288 | 0 | 0 | 0 |
| price-staleness | 256 | 0 | 0 | 0 |
| recent-activity | 256 | 0 | 0 | 0 |
| recurring-series-residual | 48814 | 0 | 0 | 0 |
| rule-objectivity | 192 | 0 | 0 | 0 |
| settlement-source | 144 | 0 | 0 | 0 |
| sibling-lead-lag | 160 | 0 | 0 | 0 |
| two-sided-close-calibration | 1762 | 1 | 0 | 0 |

## Best surviving evidence per family

### aggressor-imbalance

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| T-1d|0:0.2|21-40|no | False | 454 | 4.1898 | -8.40523 | 1.000000 | 1.000000 |
| T-1d|0.6:0.8|06-10|no | False | 148 | 0.6432 | -4.676802 | 1.000000 | 1.000000 |
| T-30d|0.8:1|01-05|no | False | 30 | 0.1307 | -0.074023 | 1.000000 | 1.000000 |
| T-30d|0.6:0.8|01-05|no | False | 2 | 0.0595 | -0.246782 | 1.000000 | 1.000000 |
| T-30d|0.4:0.6|96-99|yes | False | 5 | -0.0255 | -0.10546 | 1.000000 | 1.000000 |

### calendar-month

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| T-30d|12|01-05|no | False | 63 | 0.1364 | -0.024793 | 0.001152 | 0.027618 |
| T-30d|12|11-20|no | False | 24 | 0.6710 | 0.171304 | 1.000000 | 1.000000 |
| T-90d|8|81-95|yes | False | 8 | 0.3671 | 0.102741 | 1.000000 | 1.000000 |
| T-90d|1|06-10|no | False | 7 | 0.3472 | 0.059589 | 1.000000 | 1.000000 |
| T-30d|12|06-10|no | False | 30 | 0.3097 | -0.206378 | 1.000000 | 1.000000 |

### calendar-weekday

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| T-1d|4|11-20|no | False | 522 | 5.4028 | -2.513892 | 0.020160 | 0.317607 |
| T-3d|2|11-20|no | False | 322 | 1.6968 | -3.058284 | 0.090048 | 1.000000 |
| T-3d|5|06-10|no | False | 85 | 0.8637 | -2.074516 | 0.318416 | 1.000000 |
| T-1d|4|01-05|no | False | 596 | 0.7520 | -1.211904 | 0.212352 | 1.000000 |
| T-3d|4|01-05|no | False | 30 | 0.6238 | -0.644861 | 1.000000 | 1.000000 |

### conditional-maker-selection

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| Politics|7-30d|01-05|no | True | 87 | 0.3485 |  | 0.049496 | 0.317607 |
| Climate and Weather|0-7d|96-99|no | True | 372 | 126.2523 |  | 1.000000 | 1.000000 |
| Financials|0-7d|96-99|no | True | 117 | 14.1139 |  | 1.000000 | 1.000000 |
| Economics|7-30d|11-20|no | True | 202 | 0.4739 |  | 1.000000 | 1.000000 |
| Transportation|30-90d|96-99|no | False | 1 | 294.0603 |  | 1.000000 | 1.000000 |

### early-close-risk

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| T-90d|false|61-80|no | False | 3 | 7.8197 | 4.597447 | 1.000000 | 1.000000 |
| T-7d|false|06-10|no | False | 3 | 2.5974 | 0.354048 | 1.000000 | 1.000000 |
| T-90d|false|21-40|no | False | 1 | 1.2355 | -0.738586 | 1.000000 | 1.000000 |
| T-30d|false|06-10|no | False | 1 | 0.9570 | -0.069719 | 1.000000 | 1.000000 |
| T-7d|false|01-05|no | False | 6 | 0.7522 | 0.209984 | 1.000000 | 1.000000 |

### event-structure

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| T-90d|1:2|81-95|yes | False | 4 | 0.4081 | -0.122311 | 1.000000 | 1.000000 |
| T-30d|1:2|81-95|yes | False | 16 | 0.2722 | -0.159189 | 1.000000 | 1.000000 |
| T-30d|2:4|01-05|no | False | 17 | 0.2062 | 0.039411 | 1.000000 | 1.000000 |
| T-30d|2:4|06-10|no | False | 11 | 0.1438 | -0.268126 | 1.000000 | 1.000000 |
| T-90d|4:11|11-20|no | False | 37 | 0.1419 | -0.312352 | 1.000000 | 1.000000 |

### listing-lifecycle

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| Economics|L+30d|01-05|no | True | 50 | 0.1319 |  | 1.000000 | 1.000000 |
| Mentions|L+1d|61-80|no | False | 41 | 48.1039 |  | 1.000000 | 1.000000 |
| Social|L+7d|06-10|no | False | 1 | 32.9554 |  | 1.000000 | 1.000000 |
| Social|L+1d|61-80|no | False | 3 | 18.0285 |  | 1.000000 | 1.000000 |
| Social|L+1d|41-60|yes | False | 1 | 14.9625 |  | 1.000000 | 1.000000 |

### price-path-dependence

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| T-1d->T-6h|-2:2|01-05|no | False | 1119 | 4.1453 | -0.030996 | 0.000000 | 0.000000 |
| T-1d->T-6h|-100:-10|01-05|no | False | 1825 | 3.5452 | -3.168814 | 0.000000 | 0.000000 |
| T-1d->T-6h|3:9|96-99|yes | False | 153 | 6.1831 | -0.47901 | 0.000096 | 0.018412 |
| T-1d->T-6h|-2:2|96-99|yes | False | 246 | 5.5549 | -0.090152 | 0.001800 | 0.276180 |
| T-1d->T-6h|3:9|01-05|no | False | 47 | 11.7515 | 3.086917 | 1.000000 | 1.000000 |

### price-staleness

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| T-1d|0.2:1|41-60|no | False | 248 | 5.9046 | -16.915747 | 0.808448 | 1.000000 |
| T-1d|0.2:1|06-10|no | False | 570 | 1.4718 | -2.456778 | 0.808448 | 1.000000 |
| T-30d|0.05:0.2|11-20|no | False | 42 | 0.1339 | -0.756986 | 1.000000 | 1.000000 |
| T-30d|0.01:0.05|01-05|no | False | 77 | 0.0916 | -0.05389 | 0.808448 | 1.000000 |
| T-30d|0.2:1|01-05|no | False | 87 | -0.0040 | -0.098657 | 1.000000 | 1.000000 |

### recent-activity

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| T-1d|0:10|01-05|no | False | 1206 | 1.1855 | -0.545401 | 0.010240 | 0.317607 |
| T-1d|100:1000|06-10|no | False | 815 | 2.2894 | -3.152215 | 0.063744 | 1.000000 |
| T-3d|0:10|11-20|no | False | 322 | 2.1224 | -2.350701 | 0.041216 | 1.000000 |
| T-1d|0:10|11-20|no | False | 451 | 1.2894 | -5.478855 | 0.495718 | 1.000000 |
| T-30d|0:10|11-20|no | False | 77 | 0.3951 | -0.25024 | 0.041216 | 1.000000 |

### recurring-series-residual

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| KXWINDSORWEST|T-7d|01-05|yes | False | 1 | 5146.8320 | 5174.512381 | 1.000000 | 1.000000 |
| KXVOTEPERCENTPVV|T-7d|96-99|no | False | 1 | 5146.8320 | 5175.469867 | 1.000000 | 1.000000 |
| KXTOPALBUMTHIRDUSA|T-7d|01-05|yes | False | 1 | 5146.8320 | 5180.822667 | 1.000000 | 1.000000 |
| KXVRASCOTUSVOTE|T-7d|96-99|no | False | 1 | 5146.8320 | 5199.322441 | 1.000000 | 1.000000 |
| KXH100MAX|T-7d|01-05|yes | False | 1 | 5146.8150 | 5171.540912 | 1.000000 | 1.000000 |

### rule-objectivity

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| unclassified|T-7d|11-20|no | False | 7 | 1.0570 | -1.2637407149573903 | 1.000000 | 1.000000 |
| official_act|T-30d|06-10|no | False | 1 | 0.8133 | 0.6455661418511931 | 1.000000 | 1.000000 |
| unclassified|T-7d|06-10|no | False | 11 | 0.6196 | -0.7286146525181717 | 1.000000 | 1.000000 |
| unclassified|T-7d|01-05|no | False | 32 | 0.4701 | -0.07675943105457783 | 1.000000 | 1.000000 |
| unclassified|T-30d|11-20|no | False | 10 | 0.3962 | -0.3719943405797591 | 1.000000 | 1.000000 |

### settlement-source

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| T-7d|media_or_other|06-10|no | False | 45 | 0.6909 | -1.081068 | 1.000000 | 1.000000 |
| T-90d|exchange_or_data|06-10|no | False | 3 | 0.2958 | -0.081459 | 1.000000 | 1.000000 |
| T-90d|exchange_or_data|96-99|yes | False | 1 | 0.0734 | 0.030228 | 1.000000 | 1.000000 |
| T-90d|media_or_other|06-10|no | False | 24 | 0.0409 | -0.143066 | 1.000000 | 1.000000 |
| T-90d|media_or_other|01-05|no | False | 23 | 0.0178 | -0.077392 | 1.000000 | 1.000000 |

### sibling-lead-lag

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| T-7d->T-1d|-100:-10|11-20|no | False | 1 | 16.2272 | -9.549199 | 1.000000 | 1.000000 |
| T-7d->T-1d|-100:-10|06-10|no | False | 4 | 4.1798 | -7.785994 | 1.000000 | 1.000000 |
| T-3d->T-1d|3:9|21-40|no | False | 40 | 1.3022 | -28.223552 | 1.000000 | 1.000000 |
| T-3d->T-1d|-2:2|01-05|no | False | 347 | 0.6048 | -2.056294 | 0.834880 | 1.000000 |
| T-7d->T-1d|10:100|01-05|no | False | 15 | -0.8548 | -4.063793 | 1.000000 | 1.000000 |

### two-sided-close-calibration

| cell | folds pass | min events | worst lower | worst uplift lower | family q | suite q |
|---|---:|---:|---:|---:|---:|---:|
| Economics|T-30d|11-20|no | True | 57 | 0.3419 |  | 1.000000 | 1.000000 |
| Companies|T-3d|96-99|no | False | 1 | 11248.0789 |  | 1.000000 | 1.000000 |
| World|T-1h|81-95|no | False | 1 | 5604.7718 |  | 1.000000 | 1.000000 |
| World|T-1h|41-60|no | False | 2 | 5211.3036 |  | 1.000000 | 1.000000 |
| Elections|T-1h|41-60|yes | False | 3 | 4128.7004 |  | 1.000000 | 1.000000 |

## Metadata-dependent registered tests

Rule objectivity, ladder monotonicity, and mutually exclusive event sums are reported by `research/metadata-suite.md` after the historical metadata backfill. Rule cells join the complete suite-wide correction; multi-leg structures remain descriptive until simultaneous historical or live books exist.

Full machine-readable evidence: `data/derived/mechanism_results.parquet` and `data/derived/mechanism_periods.parquet`.
