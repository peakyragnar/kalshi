# Family base rates in legacy candidate cells — 2026-07-17

**Status.** Financials T−90 is withdrawn and Politics T−30 has insufficient early-fold support. These labels are descriptive only.

**Honesty note.** Thresholds were written into the module before the first full run, but an exploratory preview on 2026-07-17 (looser filters) had already surfaced two trap suspects. Thresholds were set on statistical grounds, not tuned to those names; the per-period persistence table is the guard.

## Tier 1 — strict, as-traded (in-cell proof)
1022 snapshots, 451 families. Verdicts: 0 (THIN 451, NEUTRAL 0).

*No family clears the evidence floor inside the strict cell — the trade's edge rests on the cell average, exactly what the map validated. This tier accumulates as history grows.*

## Tier 2 — neighborhood outcomes (advisory prior)
4452 settled longshot markets (<=15c, unfiltered prices, one row per market), 1164 families. TRAP 3, THIN 1157, NEUTRAL 4. FAT is impossible at this tier by construction.

### TRAP families (proposed skip-list)
| category | series_ticker | n | n_markets | n_events | implied | tail_rate | q_lo | q_hi | firing_events | label |
|---|---|---|---|---|---|---|---|---|---|---|
| Politics | KXTRUMPMEET | 81 | 81 | 11 | 0.0720 | 0.1111 | 0.0372 | 0.1850 | 6 | TRAP |
| Politics | KXTRUMPPARDON | 50 | 50 | 2 | 0.0386 | 0.0600 | 0.0356 | 0.0844 | 2 | TRAP |
| Politics | KXSWENCOUNTERS | 39 | 39 | 9 | 0.0605 | 0.1026 | 0.0000 | 0.2067 | 4 | TRAP |

### Persistence by period (discovery = resolved pre-2025-07-01)
| category | series_ticker | period | n | n_events | implied | tail_rate |
|---|---|---|---|---|---|---|
| Politics | KXSWENCOUNTERS | confirmation | 38 | 8 | 0.0603 | 0.0789 |
| Politics | KXSWENCOUNTERS | discovery | 1 | 1 | 0.0700 | 1.0000 |
| Politics | KXTRUMPMEET | confirmation | 81 | 11 | 0.0720 | 0.1111 |
| Politics | KXTRUMPPARDON | confirmation | 26 | 1 | 0.0431 | 0.0769 |
| Politics | KXTRUMPPARDON | discovery | 24 | 1 | 0.0338 | 0.0417 |

## Today's candidates in verdicted families
*(none on today's list)*

## Tier 2 full table (families with >= 8 events)
| category | series_ticker | n | n_markets | n_events | implied | tail_rate | q_lo | q_hi | firing_events | label |
|---|---|---|---|---|---|---|---|---|---|---|
| Politics | KXTRUMPMEET | 81 | 81 | 11 | 0.0720 | 0.1111 | 0.0372 | 0.1850 | 6 | TRAP |
| Politics | KXSWENCOUNTERS | 39 | 39 | 9 | 0.0605 | 0.1026 | 0.0000 | 0.2067 | 4 | TRAP |
| Politics | KXGOVSHUT | 13 | 13 | 13 | 0.0785 | 0.0769 | 0.0000 | 0.2218 | 1 | NEUTRAL |
| Politics | KXBILLSCOUNT | 50 | 50 | 8 | 0.0528 | 0.0400 | 0.0000 | 0.0883 | 2 | NEUTRAL |
| Politics | KXASYLUMCASES | 25 | 25 | 10 | 0.0572 | 0.0400 | 0.0000 | 0.1211 | 1 | NEUTRAL |
| Politics | KX538APPROVEMAX | 52 | 52 | 22 | 0.0527 | 0.0192 | 0.0000 | 0.0558 | 1 | NEUTRAL |
| Politics | KXLAGODAYS | 74 | 74 | 16 | 0.0270 | 0.0000 | 0.0000 | 0.1875 | 0 | THIN |
| Politics | KX538APPROVEMIN | 47 | 47 | 22 | 0.0545 | 0.0000 | 0.0000 | 0.1364 | 0 | THIN |
| Politics | KXEOWEEK | 21 | 21 | 10 | 0.0224 | 0.0000 | 0.0000 | 0.3000 | 0 | THIN |
| Politics | KXAPRPOTUS | 12 | 12 | 8 | 0.0858 | 0.0000 | 0.0000 | 0.3750 | 0 | THIN |

Labels are analysis, not rules: wiring TRAP vetoes into the candidate list requires a findings-book entry and operator sign-off. Tier-2 implied prices are indicative (unfiltered snapshots).