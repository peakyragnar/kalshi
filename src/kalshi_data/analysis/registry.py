"""Strict, dependency-free hypothesis registry loader.

The .yaml file is intentionally a JSON document, which is valid YAML 1.2. This
keeps the registry human-readable while avoiding a runtime parser dependency.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


REQUIRED = {
    "id", "mechanism", "kind", "status", "retroactive", "filters", "gate", "contract"
}
CONTRACT_REQUIRED = {
    "universe", "signal", "entry", "exit", "fees", "spread", "carry",
    "benchmark", "cluster_by", "validation", "capacity", "tail_risk",
}
KINDS = {"cell_no_maker", "cell_grid_no_maker", "documented"}
STATUSES = {
    "registered", "red", "historically_qualified", "shadow", "live_monitored", "untested"
}


def load_registry(path: Path) -> dict:
    raw = path.read_bytes()
    try:
        registry = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"registry must use deterministic JSON-compatible YAML: {exc}") from exc
    if registry.get("version") != 1 or not isinstance(registry.get("hypotheses"), list):
        raise ValueError("registry requires version=1 and a hypotheses list")
    ids = []
    for i, hypothesis in enumerate(registry["hypotheses"]):
        missing = sorted(REQUIRED - set(hypothesis))
        if missing:
            raise ValueError(f"hypothesis {i} missing {', '.join(missing)}")
        if hypothesis["kind"] not in KINDS:
            raise ValueError(f"hypothesis {hypothesis['id']} has unsupported kind")
        if hypothesis["status"] not in STATUSES:
            raise ValueError(f"hypothesis {hypothesis['id']} has unsupported status")
        missing_contract = sorted(CONTRACT_REQUIRED - set(hypothesis["contract"]))
        if missing_contract:
            raise ValueError(
                f"hypothesis {hypothesis['id']} contract missing "
                f"{', '.join(missing_contract)}"
            )
        gate = hypothesis["gate"]
        for field in ("hurdle", "minimum_events", "z"):
            if field not in gate:
                raise ValueError(f"hypothesis {hypothesis['id']} gate missing {field}")
        if hypothesis["kind"] == "cell_grid_no_maker":
            dimensions = hypothesis.get("dimensions") or {}
            for field in ("categories", "decision_labels", "price_buckets"):
                if not dimensions.get(field):
                    raise ValueError(f"hypothesis {hypothesis['id']} dimensions missing {field}")
        ids.append(hypothesis["id"])
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate hypothesis id")
    registry["sha256"] = hashlib.sha256(raw).hexdigest()
    return registry
