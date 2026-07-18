# Main-loop review of the overnight timing correction + atlas (2026-07-18)

Independent recomputation from raw markets/trades, not the executor's panel
code. Both cells rebuilt under both anchorings; phantom (post-close) snapshots
counted directly.

## Confirmed
1. **Timing bug is real and material.** 36.7% of settled Politics markets have
   expiration >30d after close. Old anchoring created post-close "phantom"
   snapshots (untradeable entries priced off final pre-close prints): 14% of
   the old Financials T-90 cell, 2% of old Politics T-30 by my construction
   (worse with the latest_expiration ingest fallback). Close-anchoring is
   correct. CONFIRMED.
2. **Financials T-90 withdrawal.** Under corrected timing and the ORIGINAL
   pre-committed 2-period gate, my numbers: disc +17.4% ± 6.9 (bound 3.6% <
   7% hurdle -> FAILS), conf +22.9% ± 1.7. Discovery fails at 2SE.
   Withdrawal CONFIRMED by an independent path.

## Disputed
3. **"Zero qualified" as applied to Politics T-30.** My corrected-timing
   recomputation under the ORIGINAL pre-committed gate (2 periods, 2 clustered
   SE, 7% hurdle): disc +24.5% ± 1.0, conf +25.0% ± 4.0 - BOTH periods clear
   the hurdle by wide margins. The atlas's disqualification comes from a NEW
   3-fold early-support requirement, which pre-2024-thin categories cannot
   satisfy regardless of economics. That is a standards change, not a
   mathematical refutation. Which standard governs is an OPERATOR decision
   (phase0 amendment-log material), and it should not be changed retroactively
   by an executor lane without that sign-off.

## Caveats on this review
Single-pass recomputation with simplified resolve convention
(coalesce(settled, close)); old-anchor reruns on the rebuilt corpus are
outlier-noisy and do not reproduce the original screens (the corpus itself
changed overnight: settlement_ts normalization + short-duration backfill).
A full three-way reconciliation (original screens vs executor panel vs this
review) is the right next research task before any standard is finalized.
