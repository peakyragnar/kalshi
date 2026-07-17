# Flow-shock overshoot — RED

Pre-committed definition: `research/flow-shock-precommit.md`. This screen excludes sports, crypto instrumentation, parlays and block trades.

Signals found: **3,217** across 1,594 events.

## Support and matching
| period | signals | matched | events | follow_7d | top10_event_share |
|---|---|---|---|---|---|
| discovery | 1036 | 291 | 196 | 0.9931 | 0.1924 |
| confirmation | 2181 | 1601 | 812 | 0.9944 | 0.0731 |

## Gate results
| period | n | events | 7d_change | 7d_se | ann_no | ann_se | uplift | uplift_se | follow_7d |
|---|---|---|---|---|---|---|---|---|---|
| discovery | 291 | 196 | -0.8660 | 0.6459 | 0.0469 | 0.4509 | 0.5535 | 0.6760 | 0.9931 |
| confirmation | 1601 | 812 | -1.4497 | 0.3429 | 0.8550 | 0.1548 | 1.0426 | 0.3186 | 0.9944 |

### Failed conditions
- discovery seven-day reversion does not clear 2SE
- discovery absolute NO return does not clear 7% at 2SE
- discovery uplift does not clear zero at 2SE

## Distribution check
| period | mean_7d | median_7d | p10 | p90 | share_down |
|---|---|---|---|---|---|
| discovery | -0.8660 | -3.0000 | -9.0000 | 5.0000 | 0.7526 |
| confirmation | -1.4497 | -3.0000 | -12.0000 | 5.0000 | 0.7277 |

Median seven-day changes are -3.0¢ in discovery and -3.0¢ in confirmation. The gate uses event-clustered means rather than win rate or median because rare continuations can dominate settlement economics.

## Exploratory category breakdown (not a qualification gate)
| period | category | n | events | shock_price | change_7d | ann_no | uplift | tail_rate |
|---|---|---|---|---|---|---|---|---|
| confirmation | Politics | 662 | 314 | 11.8200 | -1.6090 | 0.7140 | 1.0970 | 0.0680 |
| confirmation | Elections | 452 | 218 | 11.4200 | -1.4000 | 0.5100 | 0.5200 | 0.1018 |
| confirmation | Economics | 331 | 164 | 10.7500 | -0.6130 | 1.0000 | 1.2420 | 0.0544 |
| confirmation | Climate and Weather | 125 | 91 | 11.8000 | -3.0560 | 2.4800 | 2.2580 | 0.0720 |
| discovery | Politics | 177 | 111 | 7.4800 | -0.9720 | -0.5090 | 0.4110 | 0.0678 |
| discovery | Economics | 111 | 82 | 12.0300 | -0.6670 | 0.8930 | 0.7600 | 0.0901 |

Category rows are exploratory only. None is promoted without a separately registered cross-period category gate.

Settlement returns are conditional economics at the shock-hour anchor, not a claim that a newly placed resting order would have filled. No deployment rule changes automatically.