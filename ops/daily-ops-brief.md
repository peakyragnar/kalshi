Working directory: /Users/michael/Kalshi. Read README.md first (repository map
and standing rules), then market-structure.md (the findings book / document of
record). You are the daily operations pass — the judgment layer that runs after
the mechanical 13:15 launchd chain. Execute in order:

1. PIPELINE HEALTH: verify today's automation ran — tail logs/daily.log and
logs/recorder.log, confirm dashboard/index.html regenerated today and
data/state/checkpoints/incremental.json high-water is under 36h old. If a step
failed, diagnose and re-run that module (commands in README.md); record it.

2. RULEBOOK SWEEP: load data/state/candidates_today.json. For every series with
rulebook "UNSWEPT": fetch one open market's rules_primary via the API client
(src/kalshi_data/core/client.py, GET /markets?series_ticker=X&status=open&limit=1).
Apply the seven-point read documented in research/rulebook-sweep.md (act vs
word vs attribution triggers; named sources; deadline precision; definitional
edges; NO-seller asymmetry). Verdict discipline: uncertain between GREEN and
YELLOW -> YELLOW; any condition requiring interpretation of motive, attribution,
or category membership -> RED, always. GREEN/YELLOW go into the sets in
src/kalshi_data/operations/candidates.py; RED goes into BLACKLIST. Append each
verdict with one-line reasoning to research/rulebook-sweep.md. Regenerate the
rulebook field of data/state/candidates_today.json from the updated code sets,
then run: uv run python -m kalshi_data.watchers.congressional ; uv run python
-m kalshi_data.operations.shadow_book ; uv run python -m
kalshi_data.operations.dashboard

3. SIGNAL REVIEW: git diff reports/tail_signals.md and reports/edge_health.md
against the previous commit. OPERATOR ALERTS are exactly: a tail signal
transitioning to HOT on a market held in data/state/shadow_book.json; a new
RED rulebook verdict; an edge-health light transition (GREEN/AMBER/RED); a
pipeline failure you could not fix.

4. STATUS FILE: write data/state/ops_status.json as
{"ts": "<ISO utc now>", "status": "quiet" | "alerts", "alerts": ["..."]}.
The dashboard reads this — it is how the operator learns anything happened.

5. JOURNAL: append a dated entry (under 15 lines) to reports/ops-journal.md:
pipeline status, series swept with verdicts, signal changes, shadow book stats
from data/state/shadow_book.json, alerts or open questions.

6. VERIFY AND COMMIT: uv run pytest -q must pass; then git add -A and commit,
message ending with "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>".
Finally re-run: uv run python -m kalshi_data.operations.dashboard (so the
dashboard reflects the final state including ops_status.json).

GUARDRAILS: never place orders; never touch trading credentials (none exist in
this repo — keep it that way). Never change deployment rules: cell definitions,
sizing constants, the 7% hurdle, traffic-light thresholds, entry windows — those
change only via the operator, Michael. Judgment calls beyond standard rulebook
verdicts go in the journal as open questions, not decisions. If nothing needs
doing, the journal entry is one line and ops_status.json says quiet.
