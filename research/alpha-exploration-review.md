# Alpha exploration review — expanded universe (main-loop, 2026-07-18)

Independent review of the expanded-universe suite run committed at `38d4c70`.
Every number below was recomputed from the artifacts, not read from the report.
Sections 4–5 are descriptive diagnostics over already-searched results; under
the registry's re-slicing rule they qualify nothing and are marked as such.

## 1. Verification

- Funnel reproduced exactly: 55,236 cells → 6 three-fold passes → 1 family-FDR
  survivor → 0 suite-wide qualifiers. Independent Benjamini–Hochberg recompute
  matches every q-value (max diff 0.0). 144 tests pass; tree clean at review.
- The suite's negative headline is **correct as registered**: no historically
  qualified alpha cell exists on the expanded corpus.

## 2. Post-mortem of the former survivor `T-1d->T-6h|-2:2|01-05|no`

- Death certificate confirmed: it still passes support and absolute-economics
  everywhere (weakest fold 1,119 events; absolute lower bound 4.15; search
  p ≈ 0, suite q ≈ 0 — statistically still the strongest cell in the suite),
  but the **matched-baseline incremental gate** now fails in early
  (−0.0075) and middle (−0.0310) folds. A pre-committed gate failed; the
  pipeline refused to grandfather it. Right call, correctly administered.
- Category decomposition of the uplift shows why: the stability condition's
  incremental value is pocket-specific — strong in Politics (+5.4 middle) and
  Financials (+5.2), weak-to-negative in the newly added mass (Entertainment
  +0.6 on 1,079 middle-fold rows; Economics −1.1). The expansion did not
  reveal the base structure to be false; it revealed the *condition* to be
  non-robust. The lesson: the money was always the base structure (maker NO
  at extreme prices), never the −2:2 path refinement.

## 3. The family-FDR survivor: `Politics|7-30d|01-05|no` (maker fills)

The original program thesis — resting NO against retail YES longshot flow in
Politics around the 30-day window — re-emerged from the blind search as the
single family-FDR survivor, measured on 122,249 real maker fills:

| fold | fills | events | days | day-clustered 2-SE lower (ann) | loss fills | loss events | mean hold ret |
|---|---:|---:|---:|---:|---:|---:|---:|
| early | 1,119 | 87 | 230 | 0.719 | 1 | 1 | 2.72% |
| middle | 20,468 | 341 | 320 | 0.473 | 199 | 15 | 2.01% |
| recent | 100,662 | 512 | 360 | 0.566 | 455 | 23 | 2.67% |

- Survives my calendar-day clustering stress (the check event clustering
  cannot do) in all folds, 7–10× above the 7% hurdle.
- Loss anatomy is F6-shaped: losses bunch within events (recent: 455 loss
  fills across only 23 events); the event-clustered statistics already price
  this in. Volume concentrates in single mega-events (KXFEDCHAIRNOM: 14,363
  fills, one event) — the stats correctly count these as one observation each.
- Its only failure is the suite-wide multiplicity tax (family q 0.0495,
  suite q 0.318). That tax is a property of the 55,236-cell search, not of
  the cell.

## 4. Energy map (descriptive; qualifies nothing)

Of 55,236 cells, 87 pass the economic gate in ≥2 folds. They concentrate in:
maker-selection NO (33), close-calibration NO (16), listing-lifecycle NO (10);
YES-side cells are scarce everywhere. 53% of the 87 sit at extreme prices
(01–05 or 96–99). The residual structure of this exchange, wherever it exists,
has one signature: **NO side, maker role, extreme prices** — retail buys
longshot YES and locks in favorites; makers are paid on the other side.

Notable unqualified three-fold passes, leads only:
- `Climate and Weather|0-7d|96-99|no` and `Financials|0-7d|96-99|no` (maker):
  the mirror trade — makers buying the 1–4¢ NO tail from favorite-lockers.
  Enormous bounds, lottery-profile variance, failed FDR.
- `Economics|~30d|11-20|no` appears independently in two families.

## 5. Strategic read

1. **Historical search is exhausted as a discovery tool.** Two full passes
   over the corpus have been run; the registry itself bans re-slicing. More
   searching of the same past cannot qualify anything — by construction, the
   multiplicity tax now exceeds what any single historical cell can pay.
2. **The exit is forward, not backward.** Sealed-forward data (untouched since
   2026-07-17) accrues ~41 qualifying Politics events/month at recent pace: a
   pre-registered forward test of ONE named hypothesis carries m=1
   multiplicity and reaches the registered 50-event floor in ~6 weeks.
3. **The model track is immune to the multiplicity problem.** Edges from
   point-in-time external data (weather forecasts, filings, calendars) are
   informational, not search-derived; they do not pay the 55,236-cell tax.
   The energy map says where they cash out: maker NO at extreme prices.

## 6. Recommended actions (operator decides; nothing here changes rules)

1. Pre-register a sealed-forward test of `Politics|7-30d|01-05|no` (maker):
   gates, evaluation date, and sizing caps written before looking. Optional
   second registrant: the 96–99 weather mirror, as a mechanism probe.
2. Start the two unbackfillable captures now: final-hours book snapshots on
   candidate markets, and point-in-time NOAA forecasts.
3. Weekly suite continues as monitoring (drift detection), not discovery.
4. Same-day/same-category exposure caps go into any memo before any
   forward-validated cell is considered for capital.
