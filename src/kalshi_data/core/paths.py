"""Single source of truth for every filesystem location in the project.

Data tiers by replaceability:
  RAW      - re-downloadable from Kalshi's API (markets, trades, series)
  CAPTURE  - impossible to backfill (order books); guard accordingly
  DERIVED  - rebuilt from RAW by analysis.derive
  STATE    - operational state (checkpoints, candidate list, shadow book)
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

DATA = ROOT / "data"
RAW = DATA / "raw"
CAPTURE = DATA / "capture"
DERIVED = DATA / "derived"
STATE = DATA / "state"

SERIES = RAW / "series.parquet"
MARKETS = RAW / "markets"
TRADES = RAW / "trades"
BOOKS = CAPTURE / "books"
SNAPSHOTS = DERIVED / "snapshots.parquet"
DECISION_POINTS = DERIVED / "decision_points.parquet"
OUTCOMES = DERIVED / "outcomes.parquet"
MARKET_RELATIONS = DERIVED / "market_relations.parquet"
CORPUS_COVERAGE = DERIVED / "corpus_coverage.parquet"
ATLAS_RESULTS = DERIVED / "atlas_results.parquet"
MECHANISM_RESULTS = DERIVED / "mechanism_results.parquet"
MECHANISM_PERIODS = DERIVED / "mechanism_periods.parquet"
LADDER_RESULTS = DERIVED / "ladder_results.parquet"
LADDER_SUMMARY = DERIVED / "ladder_summary.parquet"
EVENT_COHERENCE = DERIVED / "event_coherence.parquet"
EVENT_COHERENCE_SUMMARY = DERIVED / "event_coherence_summary.parquet"
SURVIVOR_AUDIT = DERIVED / "survivor_audit.parquet"
MARKET_METADATA = RAW / "market_metadata"
CHECKPOINTS = STATE / "checkpoints"
CANDIDATES = STATE / "candidates_today.json"
SHADOW_BOOK = STATE / "shadow_book.json"
EDGE_HISTORY = STATE / "edge_health_history.jsonl"

TAIL_SIGNALS = STATE / "tail_signals.json"
FEATURES = CAPTURE / "external_features"
EXTERNAL_RAW = RAW / "external"
WEATHER_FORECASTS = EXTERNAL_RAW / "weather-gfs-previous-runs.parquet"
WEATHER_OBSERVATIONS = EXTERNAL_RAW / "weather-ncei-daily-summaries.parquet"
WEATHER_PANEL = DERIVED / "weather_alpha_panel.parquet"
WEATHER_RESULTS = DERIVED / "weather_alpha_results.parquet"
WEATHER_PERIODS = DERIVED / "weather_alpha_periods.parquet"
WEATHER_HOURLY_OBS = EXTERNAL_RAW / "weather-ncei-global-hourly.parquet"
WEATHER_V2_CELLS = DERIVED / "weather_alpha_v2_cells.parquet"
WEATHER_V2_PERIODS = DERIVED / "weather_alpha_v2_periods.parquet"

OPS = ROOT / "ops"
RULEBOOK_VERDICTS = OPS / "rulebook-verdicts.json"

RESEARCH = ROOT / "research"
REPORTS = ROOT / "reports"
DASHBOARD = ROOT / "dashboard"
LOGS = ROOT / "logs"
