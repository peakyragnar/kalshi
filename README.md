# Kalshi Market Structure Project

Research and operations for a validated structural edge on the Kalshi exchange:
resting NO-side maker orders against retail longshot flow in two qualified
cells (Politics ~30d, Financials ~90d). Status: **diligence phase — no live
positions.** All deployment decisions belong to the operator.

## Reading order

1. **`market-structure.md`** — the findings book. The document of record; when
   documents disagree, this one wins. Nine validated findings, the strategy as
   tested, open gates, falsification criteria.
2. `memos/` — per-cell deployment memos (tail-risk math first).
3. `edge-program-plan.md` — the current work plan (continuous measurement,
   edge discovery, layer-2 data).
4. `phase0-assumptions.md` — the pre-committed rules and amendment log.
5. `kalshi-market-structure-plan.md` — the completed Phase 0–4 plan (history).
6. `reports/` — generated evidence (screens, map, sweep, daily candidates).

## Operating the machine

```bash
uv run pytest                                  # 34 tests
uv run python -m kalshi_data.candidates        # refresh today's candidate list (~5 min)
uv run python -m kalshi_data.dashboard         # regenerate dashboard/index.html
uv run python -m kalshi_data.phase3_map        # re-run the go/no-go map
uv run python -m kalshi_data.screen_a          # (b, d) re-run any screen
```

Data (`data/`, ~3GB) is gitignored and fully reproducible:
`ingest_series` → `ingest_markets --tier deployment` → `ingest_trades --tier
deployment` → `derive`. Backfills are checkpointed and resumable.

## Automation (launchd, plists versioned in `ops/`)

| Agent | Schedule | Does |
|---|---|---|
| `com.exascale.kalshi-recorder` | 06:10 / 12:10 / 18:10 / 23:50 | order-book depth snapshots (~24k markets) |
| `com.exascale.kalshi-daily` | 13:15 | candidate scan → dashboard regenerate |

Install: `cp ops/*.plist ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/com.exascale.kalshi-*.plist`
Remove: `launchctl unload ~/Library/LaunchAgents/com.exascale.kalshi-*.plist`
Logs: `logs/recorder.log`, `logs/daily.log`.

## Standing rules

- Maker-only, hold to settlement, 30–90d entry windows, UNSWEPT = untouchable.
- Nothing changes deployment rules without passing the map's qualification gate
  and a findings-book entry.
- Claude builds analysis and tooling; order execution and API credentials stay
  with the operator, permanently.
