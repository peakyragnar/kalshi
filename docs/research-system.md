# Research system contract

The system exists to identify repeatable, executable Kalshi edges without
turning a large search space into a false-positive machine. It does not place
orders or change deployment rules.

## Decision anchor

- **Goal:** find structural cells that beat 7% annualized net with uncertainty,
  concentration, fees, carry, and independent-event support included.
- **Evidence:** settled deployment markets, public trade tape, capture-only live
  books, and point-in-time external observations.
- **Constraints:** sports-themed series, Crypto, `KXMVE*` parlays, and versioned RED rulebooks
  are out of scope; historical books do not exist; Michael alone approves deployment.
- **Falsifier:** failure to replicate across early, middle, recent, and then
  sealed-forward periods, or failure to support executable size.

## Data boundary

`close_time` is the final tradable instant in a finalized Kalshi market.
`expiration_time` can be a later rescheduling ceiling and must not anchor a
historical entry. Current payloads expose actual settlement as `settlement_ts`,
which is normalized to `settled_time` at ingest.

The canonical derived stores are deliberately separated:

| Artifact | Grain | May contain outcomes? |
|---|---|---:|
| `decision_points.parquet` | market × registered decision timestamp | No |
| `outcomes.parquet` | settled market | Yes |
| `market_relations.parquet` | market membership in an event | No |
| `corpus_coverage.parquet` | coverage cell | No |
| `external_features/*.parquet` | point-in-time external observation | No |

Decision points include close-anchored T−1h/6h/1d/3d/7d/30d/90d/180d/365d
and listing-anchored L+1d/7d/30d observations. Price, cumulative volume, recent
24-hour aggressor flow, staleness, and listing age are calculated strictly as
of the decision timestamp.

## Claim ladder

1. **Calibration:** historical price differed from outcome frequency.
2. **Fill-conditioned execution:** observed trades support maker/taker economics.
3. **Live execution:** captured books and real fills support spread and capacity.

No report may collapse these into one claim. Historical midpoint depth cannot
be reconstructed.

## Registry and atlas

`research/hypotheses.yaml` and `research/mechanism-suite-v1.yaml` are deterministic
JSON-compatible YAML. Every screen
declares mechanism, universe, signal, entry, exit, fees, spread, carry,
benchmark, clustering, temporal validation, capacity, tail risk, exact filters,
economic hurdle, minimum independent events, error multiplier, status, and
whether it was registered retroactively. The loader rejects incomplete economic
contracts.
Grid screens expand only dimensions written in the registry.

The atlas uses three historical robustness folds:

- early: before 2024-01-01
- middle: 2024-01-01 through 2025-06-30
- recent: 2025-07-01 through 2026-07-16

Dates from 2026-07-17 are sealed forward observations. A historical candidate
must pass the economic lower-bound gate in every historical fold and survive a
Benjamini–Hochberg false-discovery correction across the registered search.
Historical qualification permits shadow research only; deployment still needs
forward evidence, live execution, a findings-book entry, and operator approval.

The multi-mechanism suite executes the close-price grid plus listing lifecycle,
own-price path, sibling-contract lead/lag, aggressor flow, activity, staleness,
recurring-series, calendar, early-close, event structure, settlement-source,
fill-conditioned maker selection, and rule-objectivity families. Conditional
families must beat a matched category × decision-label × price × side baseline,
not merely inherit a pooled low-price effect. Unsupported registered cells enter
false-discovery correction with p=1, so tiny zero-variance cells cannot improve a
supported candidate's rank.

Historical market metadata is backfilled per series into
`data/raw/market_metadata/`. It supplies actual settlement timestamps, titles,
choice labels, numeric strikes, and rule text. Ladder monotonicity and mutually
exclusive event sums are explicitly reported as asynchronous calibration
comparisons: all legs still need simultaneous live book prices before either can
be called executable.

## External feature contract

Every observation records:

```text
source, entity, metric, effective_at, available_at, retrieved_at,
value, revision, evidence
```

An as-of join uses `available_at <= decision_time`; `effective_at` alone is never
enough. The Senate watcher now writes confirmation signals to this store. The
EDGAR adapter writes S-1/F-1 registration observations and deliberately labels
an empty exact-name search `NO_MATCH`, not `CLEAR`.

The first complete external-data suite covers daily high/low temperature
contracts at 20 settlement stations. `features.weather` reconstructs fixed
one-to-seven-day NOAA GFS runs through the Open-Meteo Previous Runs archive and
downloads exact-station NOAA NCEI Daily Summaries. Expanding bias and uncertainty
are estimated separately by station, high/low statistic, and lead using only
observations available before each forecast. `analysis.weather_alpha` converts
those distributions to contract probabilities and tests level, city, price,
staleness, and forecast-revision mechanisms at feasible T−1d and T−6h entries.
Each selected side pays a 2¢ spread reserve and taker fee, must beat a matched
market-only baseline in all three folds, and enters both family and combined
structural-plus-external FDR correction. A historical pass permits shadow
monitoring only.

## Rebuild

```bash
uv run python -m kalshi_data.ingest.trades --tier deployment --min-lifetime-days 0
uv run python -m kalshi_data.ingest.market_metadata --tier deployment
uv run python -m kalshi_data.analysis.corpus_audit
uv run python -m kalshi_data.analysis.research_panel
uv run python -m kalshi_data.analysis.atlas
uv run python -m kalshi_data.analysis.mechanism_suite
uv run python -m kalshi_data.analysis.metadata_suite
uv run python -m kalshi_data.analysis.survivor_audit
uv run python -m kalshi_data.features.edgar
uv run python -m kalshi_data.features.weather
uv run python -m kalshi_data.analysis.weather_alpha
```

Derived data stays gitignored. Registry, methodology, generated Markdown
reports, and tests are versioned.
