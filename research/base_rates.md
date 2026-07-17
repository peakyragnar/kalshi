# Family base rates in the qualified cells — 2026-07-17

**Honesty note.** Thresholds were written into the module before the first full run, but an exploratory preview on 2026-07-17 (looser filters) had already surfaced two trap suspects. Thresholds were set on statistical grounds, not tuned to those names; the per-period persistence table is the guard.

## Tier 1 — strict, as-traded (in-cell proof)
906 snapshots, 364 families. Verdicts: 0 (THIN 364, NEUTRAL 0).

*No family clears the evidence floor inside the strict cell — the trade's edge rests on the cell average, exactly what the map validated. This tier accumulates as history grows.*

## Tier 2 — neighborhood outcomes (advisory prior)
6832 settled longshot markets (<=15c, unfiltered prices, one row per market), 1310 families. TRAP 3, THIN 1300, NEUTRAL 7. FAT is impossible at this tier by construction.

### TRAP families (proposed skip-list)
| category | series_ticker | n | n_markets | n_events | implied | tail_rate | q_lo | q_hi | firing_events | label |
|---|---|---|---|---|---|---|---|---|---|---|
| Politics | KXTRUMPMEET | 114 | 114 | 11 | 0.0489 | 0.0526 | 0.0103 | 0.0949 | 5 | TRAP |
| Financials | KXINX | 45 | 45 | 6 | 0.0456 | 0.0889 | 0.0286 | 0.1491 | 4 | TRAP |
| Financials | KXNASDAQ100 | 31 | 31 | 5 | 0.0394 | 0.0645 | 0.0081 | 0.1210 | 2 | TRAP |

### Persistence by period (discovery = resolved pre-2025-07-01)
| category | series_ticker | period | n | n_events | implied | tail_rate |
|---|---|---|---|---|---|---|
| Financials | KXINX | discovery | 45 | 6 | 0.0456 | 0.0889 |
| Financials | KXNASDAQ100 | discovery | 31 | 5 | 0.0394 | 0.0645 |
| Politics | KXTRUMPMEET | confirmation | 114 | 11 | 0.0489 | 0.0526 |

## Today's candidates in verdicted families
*(none on today's list)*

## Tier 2 full table (families with >= 8 events)
| category | series_ticker | n | n_markets | n_events | implied | tail_rate | q_lo | q_hi | firing_events | label |
|---|---|---|---|---|---|---|---|---|---|---|
| Politics | KXGOVSHUT | 13 | 13 | 13 | 0.0815 | 0.0769 | 0.0000 | 0.2218 | 1 | NEUTRAL |
| Politics | KXTRUMPMEET | 114 | 114 | 11 | 0.0489 | 0.0526 | 0.0103 | 0.0949 | 5 | TRAP |
| Politics | KXBILLSCOUNT | 54 | 54 | 8 | 0.0469 | 0.0370 | 0.0000 | 0.0793 | 2 | NEUTRAL |
| Politics | KXSWENCOUNTERS | 37 | 37 | 8 | 0.0341 | 0.0270 | 0.0000 | 0.0796 | 1 | NEUTRAL |
| Politics | KX538APPROVE | 864 | 864 | 143 | 0.0397 | 0.0243 | 0.0147 | 0.0339 | 21 | NEUTRAL |
| Politics | KXPARDONSTRUMP | 45 | 45 | 8 | 0.0560 | 0.0222 | 0.0000 | 0.0618 | 1 | NEUTRAL |
| Politics | KXPOTUSTWEETS | 75 | 75 | 9 | 0.0228 | 0.0133 | 0.0000 | 0.0378 | 1 | NEUTRAL |
| Politics | KXTRUTHSOCIAL | 172 | 172 | 22 | 0.0121 | 0.0000 | 0.0000 | 0.1364 | 0 | THIN |
| Politics | KXELONTWEETS | 99 | 99 | 9 | 0.0151 | 0.0000 | 0.0000 | 0.3333 | 0 | THIN |
| Politics | KXLAGODAYS | 74 | 74 | 16 | 0.0272 | 0.0000 | 0.0000 | 0.1875 | 0 | THIN |
| Politics | KXTRUMPACT | 73 | 73 | 19 | 0.0214 | 0.0000 | 0.0000 | 0.1579 | 0 | THIN |
| Politics | KX538APPROVEMAX | 60 | 60 | 22 | 0.0503 | 0.0000 | 0.0000 | 0.1364 | 0 | THIN |
| Politics | KXHORMUZWEEKLY | 52 | 52 | 11 | 0.0235 | 0.0000 | 0.0000 | 0.2727 | 0 | THIN |
| Politics | KX538APPROVEMIN | 52 | 52 | 23 | 0.0612 | 0.0000 | 0.0000 | 0.1304 | 0 | THIN |
| Financials | KXTESLA | 42 | 42 | 9 | 0.0317 | 0.0000 | 0.0000 | 0.3333 | 0 | THIN |
| Politics | KXASYLUMCASES | 30 | 30 | 10 | 0.0373 | 0.0000 | 0.0000 | 0.3000 | 0 | THIN |
| Politics | KXEOWEEK | 25 | 25 | 13 | 0.0216 | 0.0000 | 0.0000 | 0.2308 | 0 | THIN |
| Politics | KXVOTEHUBTRUMPUPDOWN | 19 | 19 | 19 | 0.0889 | 0.0000 | 0.0000 | 0.1579 | 0 | NEUTRAL |
| Politics | KXMAMDANIEO | 13 | 13 | 13 | 0.0200 | 0.0000 | 0.0000 | 0.2308 | 0 | THIN |

Labels are analysis, not rules: wiring TRAP vetoes into the candidate list requires a findings-book entry and operator sign-off. Tier-2 implied prices are indicative (unfiltered snapshots).