# Screen B — term premium (lockup) test

Snapshots analyzed: **26,242**. NO-side maker economics, carry 3.25%.

## Identification: support by category x horizon (n snapshots)
| category | 90 | 180 | 7 | 30 | 365 |
|---|---|---|---|---|---|
| Climate and Weather | 191 | 90 | 1190 | 862 | 3 |
| Commodities | 11 | 11 | 338 | 16 | 2 |
| Companies | 38 | 23 | 59 | 49 | 4 |
| Economics | 829 | 462 | 2908 | 2323 | 184 |
| Elections | 828 | 317 | 1509 | 1879 | 70 |
| Financials | 457 | 221 | 781 | 689 | 104 |
| Health | 56 | 37 | 116 | 89 | 19 |
| Politics | 1393 | 665 | 2869 | 2435 | 176 |
| Science and Technology | 244 | 159 | 730 | 534 | 42 |
| World | 43 | 22 | 93 | 59 | 13 |

## 1. Raw annualized NO return by horizon (confounded)
| horizon_days | n | n_events | ann_no_mean | ann_no_se | with_carry |
|---|---|---|---|---|---|
| 7 | 10593 | 3681 | -6.3068 | 1.2886 | -6.2743 |
| 30 | 8935 | 3106 | 0.6505 | 0.6625 | 0.6830 |
| 90 | 4090 | 1530 | 0.2148 | 0.1876 | 0.2473 |
| 180 | 2007 | 851 | 0.3251 | 0.1324 | 0.3576 |
| 365 | 617 | 248 | 0.2678 | 0.0945 | 0.3003 |

## 2. Controlled: residualized within category x bucket (slope only)
| horizon_days | n | n_events | resid_mean | resid_se |
|---|---|---|---|---|
| 7 | 10497 | 3680 | -3.2321 | 1.2818 |
| 30 | 8935 | 3106 | 2.6863 | 0.6705 |
| 90 | 4090 | 1530 | 1.5965 | 0.2163 |
| 180 | 2007 | 851 | 1.3980 | 0.2016 |
| 365 | 617 | 248 | 0.9543 | 0.2241 |

## 3. Within-market: residualized within ticker (strongest)
| horizon_days | n | n_events | resid_mean | resid_se |
|---|---|---|---|---|
| 7 | 5632 | 2297 | -5.9787 | 0.8624 |
| 30 | 6704 | 2625 | 3.1003 | 0.5907 |
| 90 | 3580 | 1461 | 2.2619 | 0.6238 |
| 180 | 1900 | 830 | 2.0588 | 0.2605 |
| 365 | 607 | 248 | 1.4465 | 0.3263 |

## 4. Carry natural experiment (controlled slope, by regime)
### pre-interest
| horizon_days | n | n_events | resid_mean | resid_se |
|---|---|---|---|---|
| 7 | 3332 | 1462 | -4.5553 | 2.1014 |
| 30 | 3266 | 1320 | 2.6617 | 1.4304 |
| 90 | 1629 | 639 | 2.5385 | 0.4722 |
| 180 | 1525 | 698 | 1.2536 | 0.1878 |
| 365 | 617 | 248 | 0.7098 | 0.2099 |

### post-interest
| horizon_days | n | n_events | resid_mean | resid_se |
|---|---|---|---|---|
| 7 | 7102 | 2240 | -2.5739 | 1.6031 |
| 30 | 5666 | 1823 | 2.6052 | 0.6588 |
| 90 | 2455 | 922 | 1.0384 | 0.2074 |
| 180 | 479 | 162 | 2.0243 | 0.6515 |

### Overall NO edge by regime (raw, >=30d horizons)
| carry_regime | n | n_events | ann_no_mean | ann_no_se |
|---|---|---|---|---|
| post-interest | 8607 | 1944 | 0.5067 | 0.4365 |
| pre-interest | 7042 | 1847 | 0.4470 | 0.6716 |