#!/bin/zsh
# Daily judgment pass: headless Claude working the ops brief.
# Run by launchd (com.exascale.kalshi-ops, 14:11) or manually: ops/run-ops.sh
cd /Users/michael/Kalshi || exit 1
echo "=== ops run $(date '+%Y-%m-%d %H:%M') ===" >> logs/ops.log
/Users/michael/.local/bin/claude -p "$(cat ops/daily-ops-brief.md)" >> logs/ops.log 2>&1
echo "=== ops run exit $? ===" >> logs/ops.log
