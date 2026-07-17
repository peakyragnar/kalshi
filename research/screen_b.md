# Screen B — term premium (lockup) test

Snapshots analyzed: **129,261**. NO-side maker economics, carry 3.25%.

## Identification: support by category x horizon (n snapshots)
| category | 180 | 365 | 30 | 90 | 7 |
|---|---|---|---|---|---|
| Climate and Weather | 97 | 19 | 1044 | 355 | 60388 |
| Commodities | 16 | 2 | 258 | 12 | 9879 |
| Companies | 28 | 8 | 57 | 45 | 41 |
| Economics | 666 | 245 | 2721 | 1534 | 5286 |
| Elections | 292 | 1844 | 203 | 232 | 156 |
| Financials | 353 | 173 | 531 | 650 | 32432 |
| Health | 29 | 24 | 93 | 47 | 116 |
| Politics | 922 | 803 | 1651 | 1626 | 2284 |
| Science and Technology | 173 | 101 | 783 | 229 | 555 |
| World | 25 | 15 | 53 | 48 | 117 |

## 1. Raw annualized NO return by horizon (confounded)
| horizon_days | n | n_events | ann_no_mean | ann_no_se | with_carry |
|---|---|---|---|---|---|
| 7 | 111254 | 24867 | -4.0668 | 0.4767 | -4.0343 |
| 30 | 7394 | 2353 | 0.6289 | 0.5000 | 0.6614 |
| 90 | 4778 | 1531 | 0.4977 | 0.4023 | 0.5302 |
| 180 | 2601 | 1012 | 0.1093 | 0.1307 | 0.1418 |
| 365 | 3234 | 1005 | -0.0263 | 0.0424 | 0.0062 |

## 2. Controlled: residualized within category x bucket (slope only)
| horizon_days | n | n_events | resid_mean | resid_se |
|---|---|---|---|---|
| 7 | 111254 | 24867 | 0.1459 | 0.4641 |
| 30 | 7394 | 2353 | -1.0100 | 0.5460 |
| 90 | 4778 | 1531 | -1.0915 | 0.4402 |
| 180 | 2601 | 1012 | -0.4838 | 0.3207 |
| 365 | 3234 | 1005 | -0.7089 | 0.1784 |

## 3. Within-market: residualized within ticker (strongest)
| horizon_days | n | n_events | resid_mean | resid_se |
|---|---|---|---|---|
| 7 | 3966 | 1368 | -3.7298 | 1.4008 |
| 30 | 4847 | 1760 | 2.0695 | 1.0879 |
| 90 | 2597 | 1073 | 1.2528 | 0.3722 |
| 180 | 1820 | 777 | 0.4106 | 0.4051 |
| 365 | 655 | 298 | 1.1616 | 0.1935 |

## 4. Carry natural experiment (controlled slope, by regime)
### pre-interest
| horizon_days | n | n_events | resid_mean | resid_se |
|---|---|---|---|---|
| 7 | 38783 | 10782 | 0.0478 | 0.7237 |
| 30 | 2688 | 1008 | -0.7224 | 0.5106 |
| 90 | 1374 | 530 | -0.1368 | 0.4738 |
| 180 | 1872 | 782 | 0.4205 | 0.2477 |
| 365 | 1295 | 522 | -0.3934 | 0.1874 |

### post-interest
| horizon_days | n | n_events | resid_mean | resid_se |
|---|---|---|---|---|
| 7 | 72400 | 14079 | 0.1964 | 0.5977 |
| 30 | 4703 | 1362 | -0.8414 | 0.9467 |
| 90 | 3394 | 1011 | -2.6981 | 0.6634 |
| 180 | 726 | 240 | -1.3043 | 1.0764 |
| 365 | 1936 | 485 | -0.0802 | 0.2484 |

### Overall NO edge by regime (raw, >=30d horizons)
| carry_regime | n | n_events | ann_no_mean | ann_no_se |
|---|---|---|---|---|
| post-interest | 10772 | 2343 | 0.8469 | 0.3650 |
| pre-interest | 7235 | 2025 | -0.2620 | 0.2105 |