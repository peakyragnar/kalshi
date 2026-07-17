# Kalshi Market Structure Project

Research and operations for a validated structural edge on the Kalshi exchange:
resting NO-side maker orders against retail longshot flow in two qualified
cells (Politics ~30d, Financials ~90d). Status: **diligence phase — shadow book
running, no live positions.** All deployment decisions belong to the operator.

## Repository map

| Path | Contents |
|---|---|
| `market-structure.md` | **The findings book — document of record.** Read first; wins all conflicts. |
| `docs/plans/` | Work plans: 01 market-structure (completed), 02 edge-program (active) |
| `docs/phase0-assumptions.md` | Pre-committed rules + amendment log |
| `docs/data-set-description.md` | Data census, scope, backfillable vs capture-only |
| `docs/memos/` | Per-cell deployment memos (tail-risk math first) |
| `research/` | One-time evidence: screens A/B/D, coverage, map, rulebook sweeps |
| `reports/` | Recurring outputs: daily candidates, weekly edge health |
| `src/kalshi_data/core/` | client, field parsing, tier rules, **paths.py (single source of path truth)** |
| `src/kalshi_data/ingest/` | series, markets, trades, daily incremental, book recorder |
| `src/kalshi_data/analysis/` | screens, derived table, map, edge health |
| `src/kalshi_data/operations/` | candidate list, shadow book, dashboard |
| `src/kalshi_data/watchers/` | external-data tail watchers (congressional calendar, EDGAR) |
| `ops/` | launchd plists (versioned; installed copies in ~/Library/LaunchAgents) |
| `dashboard/index.html` | The operations dashboard (generated; bookmark it) |

## Data layout (`data/`, gitignored)

| Tier | Path | Replaceability |
|---|---|---|
| Raw | `data/raw/` (series, markets, trades) | re-downloadable from the API |
| Capture | `data/capture/books/` | **impossible to backfill — guard it** |
| Derived | `data/derived/` | rebuilt from raw via `analysis.derive` |
| State | `data/state/` (checkpoints, candidates, shadow book, edge history) | operational |

## Operating the machine

```bash
uv run pytest                                        # 41 tests
uv run python -m kalshi_data.operations.candidates   # refresh candidate list (~5 min)
uv run python -m kalshi_data.operations.shadow_book  # update paper book
uv run python -m kalshi_data.operations.dashboard    # regenerate dashboard
uv run python -m kalshi_data.analysis.edge_health    # weekly grading (also scheduled)
uv run python -m kalshi_data.analysis.phase3_map     # re-run the go/no-go map
```

Full rebuild from nothing: `ingest.series` → `ingest.markets --tier deployment`
→ `ingest.trades --tier deployment` → `analysis.derive`. Checkpointed, resumable.

## Automation (launchd)

| Agent | Schedule | Chain |
|---|---|---|
| `com.exascale.kalshi-recorder` | 06:10 / 12:10 / 18:10 / 23:50 | book depth snapshots |
| `com.exascale.kalshi-daily` | 13:15 | incremental ingest → candidates → shadow book → dashboard |
| `com.exascale.kalshi-weekly` | Mon 14:00 | edge health → dashboard |
| `com.exascale.kalshi-shadow` | every 4h (02:20…22:20) | shadow book fill check → dashboard |

Install: `cp ops/*.plist ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/com.exascale.kalshi-*.plist`

## Standing rules

- Maker-only, hold to settlement, 30–90d entry windows, UNSWEPT = untouchable,
  RED rulebooks never trade.
- Sizing: $250/position Politics, ×½ per AMBER cell light, ×½ per YELLOW
  rulebook, one position per event.
- Nothing changes deployment rules without passing the map's qualification gate
  and a findings-book entry.
- Claude builds analysis and tooling; order execution and API credentials stay
  with the operator, permanently. All orders placed in Kalshi Pro, limit only.

## The operations system (who does what, on what clock)

| Layer | Actor | Trigger |
|---|---|---|
| Mechanical: ingest, candidates, watcher, shadow book, dashboard | launchd agents | 13:15 daily + recorder 4×/day + weekly Mon 14:00 |
| Judgment: rulebook sweeps, signal review, anomaly triage, ops journal | **headless Claude via launchd** (`com.exascale.kalshi-ops`, brief in `ops/daily-ops-brief.md`; run manually any time: `ops/run-ops.sh`) | 14:11 daily |
| Decisions: deployment rules, sizing, go/no-go, real orders | **Michael only** | on alerts or choice |

The ops pass runs headless (no app needed), reads this README + the findings
book fresh each run, journals to `reports/ops-journal.md`, writes
`data/state/ops_status.json`, and its results surface ON THE DASHBOARD: an
'ops pass' check in the Step 0 strip, and a red OPERATOR ALERTS banner at the
top only when something genuinely needs a human — a HOT signal on a held
market, a new RED rulebook, an edge-health light change, or an unfixable
pipeline failure. If it's not on the dashboard, it didn't happen.
Permissions for the headless session: minimal allowlist in `.claude/settings.json`.

## Real portfolio setup (operator-only, one time)

1. Kalshi → account settings → API → create key. You get a key ID (text) and a
   downloaded private key file.
2. Put the downloaded key file in this folder named `kalshi.pem`, and create
   `.env` in this folder containing one line: `KALSHI_KEY_ID=<your key id>`.
   Both are gitignored and never leave this machine. (`~/.kalshi/` also works.)
3. Never paste key material into chat, the repo, or logs. The sync
   (`operations/portfolio.py`) is read-only by construction — the client has no
   order methods. Returns baseline is recorded at first successful sync in
   `data/state/portfolio_baseline.json`; sizing units on the dashboard derive
   from live equity (2.5% Politics, ×½ AMBER).
