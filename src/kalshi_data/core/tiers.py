"""Universe tier classification, per phase0-assumptions.md section 4.

Tiers:
  excluded        - KXMVE* parlay markets; never ingested beyond a volume tally
  instrumentation - sports and crypto; measured for microstructure, never traded
  deployment      - econ / climate / financials / politics / companies / science
  review          - category not yet mapped; surfaced by the coverage report
"""

from __future__ import annotations

EXCLUDED_TICKER_PREFIXES = ("KXMVE",)

INSTRUMENTATION_KEYWORDS = ("sport", "crypto")

DEPLOYMENT_KEYWORDS = (
    "econ",
    "climate",
    "weather",
    "financ",
    "politic",
    "election",
    "world",
    "compan",
    "science",
    "tech",
    "commodit",
    "health",
)


def classify(ticker: str, category: str | None) -> str:
    t = (ticker or "").upper()
    if any(t.startswith(p) for p in EXCLUDED_TICKER_PREFIXES):
        return "excluded"
    c = (category or "").lower()
    if any(k in c for k in INSTRUMENTATION_KEYWORDS):
        return "instrumentation"
    if any(k in c for k in DEPLOYMENT_KEYWORDS):
        return "deployment"
    return "review"
