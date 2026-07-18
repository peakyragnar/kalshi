import plistlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "ops"


def command(name: str) -> str:
    with (OPS / name).open("rb") as f:
        plist = plistlib.load(f)
    args = plist["ProgramArguments"]
    return args[-1] if args[-2:-1] == ["-c"] else " ".join(args)


def modules(cmd: str) -> list[str]:
    return re.findall(r"python -m ([\w.]+)", cmd)


def test_daily_launchd_chain_has_each_module_once_in_order():
    cmd = command("com.exascale.kalshi-daily.plist")
    assert modules(cmd) == [
        "kalshi_data.ingest.incremental",
        "kalshi_data.operations.candidates",
        "kalshi_data.watchers.congressional",
        "kalshi_data.features.edgar",
        "kalshi_data.operations.shadow_book",
        "kalshi_data.operations.portfolio",
        "kalshi_data.operations.dashboard",
    ]
    prefix = f"/opt/homebrew/bin/uv run --directory {ROOT}"
    assert f"{prefix} {prefix}" not in cmd


def test_recurring_launchd_chains_cover_recorder_shadow_and_edge_health():
    assert modules(command("com.exascale.kalshi-recorder.plist")) == [
        "kalshi_data.ingest.recorder"
    ]
    assert modules(command("com.exascale.kalshi-shadow.plist")) == [
        "kalshi_data.operations.shadow_book",
        "kalshi_data.operations.portfolio",
        "kalshi_data.operations.dashboard",
    ]
    assert modules(command("com.exascale.kalshi-weekly.plist")) == [
        "kalshi_data.ingest.market_metadata",
        "kalshi_data.analysis.full_suite",
        "kalshi_data.analysis.edge_health",
        "kalshi_data.operations.dashboard",
    ]
