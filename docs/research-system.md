# Research system contract

The system exists to identify repeatable, executable Kalshi edges without
turning a large search space into a false-positive machine. It does not place
orders or change deployment rules.

## Decision anchor

- **Goal:** find structural cells that beat 7% annualized net with uncertainty,
  concentration, fees, carry, and independent-event support included.
- **Evidence:** settled deployment markets, public trade tape, capture-only live
  books, and point-in-time external observations.
- **Constraints:** sports, parlays, and crypto are out of scope; historical books
  do not exist; Michael alone approves deployment.
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

`research/hypotheses.yaml` is deterministic JSON-compatible YAML. Every screen
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

Atlas v1 executes only the predeclared category × close-horizon × price grid
and two legacy cells. Listing-age effects, recurring-series residuals, ladder
monotonicity, linked-contract lead/lag, activity/staleness/flow interactions,
and resolution objectivity are registered as **untested**. Some can use the
current panel; ladders, linked semantics, and rule objectivity require historical
metadata not retained in the raw store. The atlas report lists these gaps so an
untested mechanism cannot be read as a RED result.

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

## Rebuild

```bash
uv run python -m kalshi_data.ingest.trades --tier deployment --min-lifetime-days 0
uv run python -m kalshi_data.analysis.corpus_audit
uv run python -m kalshi_data.analysis.research_panel
uv run python -m kalshi_data.analysis.atlas
uv run python -m kalshi_data.features.edgar
```

Derived data stays gitignored. Registry, methodology, generated Markdown
reports, and tests are versioned.
