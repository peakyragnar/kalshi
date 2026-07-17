# Dataset Description

What we hold from Kalshi, how it grows, and which parts cannot be rebuilt.
Census as of 2026-07-17; sizes grow daily. Everything under `data/` is
gitignored.

## Stores

| Store | Size | Rows | Purpose |
|---|---:|---:|---|
| `raw/series.parquet` | <1MB | 11,486 catalog rows | exchange catalog and deployment tier |
| `raw/markets/` | 47MB | 2,733,070 settled deployment-tier markets | outcomes, timing, event/series, fees |
| `raw/trades/` | 1.6GB | 47,342,026 fills in 380,660 traded markets | price, size, timestamp, aggressor side |
| `derived/snapshots.parquet` | 2MB | 50,941 | legacy T−7/30/90/180/365d screen grid |
| `derived/decision_points.parquet` | 21MB | 758,479 | outcome-free close/listing anchored research panel |
| `derived/outcomes.parquet` | 3.8MB | 2,732,916 | isolated YES/NO resolutions |
| `derived/market_relations.parquet` | derived | 2,732,916 | event membership for linked-contract analysis |
| `capture/books/` | 52MB | growing | capture-only live depth; recorder began 2026-07-15 |
| `capture/external_features/` | growing | point-in-time observations | Senate and EDGAR data with availability timestamps |

The settled corpus covers 51,587 events, 3,579 series represented in the
deployment market table, and about 6.17 billion contracts of lifetime volume.
See `research/corpus-audit.md` for the category × year × duration census.

## Timing correction and short-duration coverage

`close_time` is the actual end of trading. `expiration_time` may be a later
rescheduling ceiling and must not be used as the tradable boundary. Current API
payloads provide actual settlement as `settlement_ts`, normalized at ingest to
`settled_time`.

The historical market parser previously discarded `settlement_ts`, so actual
settlement is absent for the existing 2,733,070-market backfill. Close-anchored
decision times remain trustworthy; exact post-close carry duration does not.
This limitation is explicit in the audit and panel rather than silently filled.

The trade backfill now includes every volume-positive deployment-tier market,
including markets shorter than seven days. Coverage is complete for the target
boundary: **332,515 / 332,515 traded markets shorter than six days have tape**.
The old claim that short tape could not contribute to research is withdrawn.

## Deliberate scope boundaries

- Deployment categories are economics, climate/weather, politics, world,
  companies, science/technology, commodities, health, financials, and the
  existing elections corpus. Sports, parlays, and crypto remain excluded from
  this build by decision.
- The current relationship table proves shared-event membership. Historical
  strike/title fields were not stored, so ordered ladder monotonicity needs a
  metadata backfill before it can be tested honestly.
- Voided or cancelled markets are absent from the settled-only history. They
  must be captured prospectively; a settled-only feed cannot measure void risk.
- Historical order books do not exist. Tape can support calibration and
  fill-conditioned maker/taker claims, but only captured books and real fills
  can support live spread and capacity claims.

## Backfillable versus capture-only

Markets and trades are backfillable from Kalshi's public historical/live API
boundary. Losing them costs download time. Decision points, outcomes, relations,
coverage, and atlas outputs are deterministic derivatives.

Order-book states are capture-only: an unrecorded historical book is gone.
External observations are stored with `effective_at`, `available_at`, and
`retrieved_at`; research joins on `available_at <= decision_time` to prevent
look-ahead. A current public filing may be backfillable, but the exact point-in-
time result of a changing search generally is not.

## Cadence

- Daily: incremental markets/tape, candidates, Senate/EDGAR observations,
  shadow book, portfolio read, dashboard.
- Four times daily: current order-book capture.
- Weekly: corpus audit, canonical research panel, registered atlas, legacy-cell
  health diagnostics, dashboard.

No websocket stream is needed for the current daily-entry, multi-day holding
style. If an explicitly registered intraday hypothesis requires it, that would
be a separate capture system and evidence boundary.
