# Dataset Description

What we hold from Kalshi, how it grows, and which parts cannot be rebuilt.
Census as of 2026-07-18; sizes grow daily. Everything under `data/` is
gitignored.

## Stores

| Store | Size | Rows | Purpose |
|---|---:|---:|---|
| `raw/series.parquet` | <1MB | 11,999 catalog rows | exchange catalog and current universe tier |
| `raw/markets/` | 52MB | 2,888,361 settled raw markets | outcomes, timing, event/series, fees |
| `raw/trades/` | 2.2GB | 67,289,825 fills in 465,472 raw market tickers | price, size, timestamp, aggressor side |
| `raw/market_metadata/` | 109MB | 2,885,843 unique tickers | titles, strikes, rules, settlement timestamps |
| `derived/snapshots.parquet` | 2MB | 84,148 | legacy T−7/30/90/180/365d screen grid |
| `derived/decision_points.parquet` | derived | 1,106,075 | outcome-free close/listing anchored research panel |
| `derived/outcomes.parquet` | derived | 2,866,040 | isolated in-scope YES/NO resolutions after RED filtering |
| `derived/market_relations.parquet` | derived | 2,866,040 | event membership for linked-contract analysis |
| `capture/books/` | 52MB | growing | capture-only live depth; recorder began 2026-07-15 |
| `capture/external_features/` | growing | point-in-time observations | Senate and EDGAR data with availability timestamps |
| `raw/external/weather-gfs-previous-runs.parquet` | <1MB | 133,798 | fixed-lead daily high/low GFS point forecasts for Kalshi settlement stations |
| `raw/external/weather-ncei-daily-summaries.parquet` | <1MB | 19,254 | exact-station daily high/low observations used for point-in-time calibration |
| `derived/weather_alpha_panel.parquet` | 23MB | 220,320 | costed YES/NO weather strategies joined as of each decision timestamp |

The current deployment boundary contains 2,866,367 settled market tickers
before the three versioned RED series are removed. See
`research/corpus-audit.md` for the category × year × duration census.

## Timing correction and short-duration coverage

`close_time` is the actual end of trading. `expiration_time` may be a later
rescheduling ceiling and must not be used as the tradable boundary. Current API
payloads provide actual settlement as `settlement_ts`, normalized at ingest to
`settled_time`.

The historical market parser previously discarded `settlement_ts`; the metadata
backfill repaired this where Kalshi exposes it. Only 68 raw markets still lack
actual settlement time. Close-anchored decision times remain trustworthy, and
the remaining carry limitation is explicit rather than silently filled.

The trade backfill now includes every volume-positive deployment-tier market,
including markets shorter than seven days. Coverage is complete for the target
boundary: **378,597 / 378,597 volume-positive deployment markets shorter than
six days have tape**.
The old claim that short tape could not contribute to research is withdrawn.

## Deliberate scope boundaries

- Deployment research covers every exchange category except Crypto and
  sports-themed series, including sports contracts mislabeled under Mentions,
  Entertainment, Politics, or other categories. `KXMVE*` parlays remain
  excluded. Versioned RED rulebooks are retained in raw
  storage for auditability but filtered from the research panel and live candidates.
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
- Weekly: series refresh, incremental historical backfill, metadata refresh,
  complete structural suite, weather source refresh and external-alpha suite,
  legacy-cell health diagnostics, dashboard.

No websocket stream is needed for the current daily-entry, multi-day holding
style. If an explicitly registered intraday hypothesis requires it, that would
be a separate capture system and evidence boundary.
