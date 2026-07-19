# Weather alpha v2 — verdict: kill condition fired (2026-07-18)

Registry: `weather-alpha-v2.json`. Run history and the decision, recorded in
full because the sequence is the point.

## Run history

- **v2.0** (early-fold-only calibration): sub-1% ladder rungs structurally
  unreachable — the thin early fold floored the lowest bin at ~1.6%
  (Jeffreys smoothing on ~30 samples). Amendment 2 registered walk-forward
  fitting (middle←early, recent←early+middle); no thresholds or gates
  changed.
- **v2.1** (walk-forward): the reachable bands show **no out-of-fold
  separation** — realized 1.27% vs 1.29% across the calibrated split
  (middle+recent, T-1d, ≤5¢). The lowest rungs remain unreachable, and this
  time not as an artifact: the calibrator floors near 3% because that is
  what the model's confident tails actually do.
- **Defect theory tested and refuted.** Before accepting the kill, one
  candidate defect was checked: label contamination (pooling T-6h rows,
  where the model lacks intraday state, into the fit). The split says
  otherwise — among raw model p ≤ 0.5% in the fit folds, T-1d rows fired
  **4.73%** (444 rows) vs T-6h 2.44%. The model's confidence is unreliable
  at the fair horizon *unconditionally*. No third amendment is available on
  the evidence.

## Correction to the v1 review's diagnostic

The v1 review reported that the raw model separates market-priced ≤5¢ tails
0.58% / 1.02% / 1.62%. That conditioning (market cheap AND model view) let
the market's information masquerade as model skill: unconditionally, the
model's "dead" calls fire at ~4.7% at T-1d. Where model and market
disagree, the market is right. The within-band ordering was real but
mostly market-supplied; the calibrated families built on model probability
alone could never recover it. The review's optimism is corrected here.

## Verdict and consequence (per the pre-committed contract)

**Kill condition fired.** The GFS-previous-runs weather model, honestly
calibrated, carries no deployable tail information beyond the market at the
fair horizon. Per the registry: weather modeling closes; the atlas #2
target — the **CPI/ALFRED complex** — moves up as the model program's next
target.

What would reopen weather: a NEW registered program on materially better
information (higher-skill ensemble archives, intraday running max at T-6h),
at lower priority than CPI. The `features/hourly_obs.py` capture module is
committed as infrastructure for that eventuality; its backfill is not run —
no spend on a closed track.

Unaffected by this verdict: the structural maker wage (never depended on
the model), the Politics forward pre-registration (still the cheapest
qualified-edge path, still awaiting operator go), the near-close book
capture, and the synchronized-day risk cap (which loses its hoped-for
model-based early warning and therefore matters MORE, not less, if the
structural trade ever deploys).
