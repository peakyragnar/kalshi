# Weather alpha v2.0 — maker channel + out-of-fold recalibration

Registry: `weather-alpha-v2.json` (v2). Scope: T-1d only; T-6h cells await the intraday running-max capture (running them without it would repeat v1's handicap). Early fold is in-fit for the recalibration and is reported but the kill condition reads middle/recent only.

Walk-forward recalibration tables (per pre-committed bin):

- middle (fit on early): 0.0159, 0.0354, 0.0812, 0.0812, 0.1126, 0.1393, 0.2307, 0.2492, 0.2492, 0.2500, 0.2983, 0.3452, 0.4333, 0.5312, 0.5312
- recent (fit on early+middle): 0.0289, 0.0394, 0.0490, 0.0657, 0.0808, 0.1233, 0.1984, 0.2406, 0.2406, 0.2406, 0.2919, 0.3976, 0.5000, 0.5645, 0.5645

## Kill-condition check — out-of-fold separation (middle+recent, T-1d, <=5c)

| band | n | events | market_implied | realized |
|---|---|---|---|---|
| (0.01, 0.02] | 157 | 122 | 0.0201 | 0.0127 |
| (0.02, 1.0] | 16960 | 7552 | 0.0237 | 0.0129 |

## Cells

| family_id | cell_id | n_periods | minimum_fold_events | worst_lower_bound | worst_incremental_lower_bound | family_fdr_q | combined_suite_q | passes_all_folds | historically_qualified |
|---|---|---|---|---|---|---|---|---|---|
| tail-veto-no | T-1d|p<=0.02|01-05|no | 2 | 26 | -2.7686 | -6.2817 | 1.0000 | 1.0000 | False | False |
| favorite-fragility-no | T-1d|doubt>=0.02|96-99|no | 3 | 3 | 1118.1410 | -13266.7025 | 1.0000 | 1.0000 | False | False |
| favorite-fragility-no | T-1d|doubt>=0.05|96-99|no | 3 | 3 | 1118.1410 | -13266.7025 | 1.0000 | 1.0000 | False | False |
| favorite-fragility-no | T-1d|doubt>=0.1|96-99|no | 3 | 3 | 1118.1410 | -13266.7025 | 1.0000 | 1.0000 | False | False |

**Suite survivors: 0**

Maker economics primary per contract; historical qualification is not deployment; forward confirmation on sealed data and the deployment ladder still apply.
