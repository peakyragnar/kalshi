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
CHECKPOINTS = STATE / "checkpoints"
CANDIDATES = STATE / "candidates_today.json"
SHADOW_BOOK = STATE / "shadow_book.json"
EDGE_HISTORY = STATE / "edge_health_history.jsonl"

TAIL_SIGNALS = STATE / "tail_signals.json"
FEATURES = CAPTURE / "external_features"

OPS = ROOT / "ops"
RULEBOOK_VERDICTS = OPS / "rulebook-verdicts.json"

RESEARCH = ROOT / "research"
REPORTS = ROOT / "reports"
DASHBOARD = ROOT / "dashboard"
LOGS = ROOT / "logs"
