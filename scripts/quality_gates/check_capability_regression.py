"""Capability-regression gate (Wave-2 #5) — FAIL on a lost capability without a plan ack.

A capability edge that was ``available`` in the committed baseline
(``scripts/openapi/capability-edge-status-baseline.json``) and is now
``not_available`` / ``not_registered`` is a REGRESSION — the system stopped being
able to do something it could do. This gate fails the build on any such
regression UNLESS the edge is acked in ``capability_regression_acks.yaml`` with a
plan reference (intentional, reviewed removal).

Improvements (``not_registered`` -> ``available`` etc.) never fail. Run
``generate_capability_changelog.py --update-baseline`` to accept the new state
after an intentional capability change.

Self-contained (no cross-dir import) so it type-checks cleanly under the
``scripts/`` basedpyright ratchet. The diff semantics mirror
``generate_capability_changelog.diff_statuses`` (kept trivially in sync via the
shared baseline file + the test suite).

SSOT: ``plans/active/capability_wizard_and_manifest_2026_06_11.md`` Wave-2 #5.
Mirrors the baselined-ratchet pattern of ``check_two_sided_audit.py``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import cast

import yaml

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
_OPENAPI_DIR = _REPO_ROOT / "scripts" / "openapi"
_ACKS_PATH = _SCRIPT_DIR / "capability_regression_acks.yaml"
_BASELINE_PATH = _OPENAPI_DIR / "capability-edge-status-baseline.json"

_AVAILABLE = "available"
_LOST = {"not_available", "not_registered"}
_RANK = {"available": 0, "partial": 1, "not_registered": 2, "not_available": 3}


def _manifest_path() -> Path:
    return _REPO_ROOT.parent / "unified-api-contracts" / "openapi" / "capability-manifest.json"


def load_edge_statuses(manifest_path: Path) -> dict[str, str]:
    """edge_key -> best (most-available) status, from the committed manifest."""
    raw = cast("dict[str, object]", json.loads(manifest_path.read_text()))
    # Fail-fast: a manifest with no "edges" is malformed (KeyError loud), never silently empty.
    edges = cast("list[dict[str, str]]", raw["edges"])
    out: dict[str, str] = {}
    for e in edges:
        key = f"{e['from_node_id']}|{e['relation']}|{e['to_node_id']}"
        status = e.get("status", "not_registered")
        prev = out.get(key)
        if prev is None or _RANK.get(status, 9) < _RANK.get(prev, 9):
            out[key] = status
    return out


def load_baseline(baseline_path: Path) -> dict[str, str]:
    if not baseline_path.exists():
        return {}
    return cast("dict[str, str]", json.loads(baseline_path.read_text()))


def find_regressions(baseline: dict[str, str], current: dict[str, str]) -> list[tuple[str, str, str]]:
    """(key, old, new) for edges that went available -> not_available/not_registered."""
    out: list[tuple[str, str, str]] = []
    for key in sorted(current):
        old = baseline.get(key)
        if old == _AVAILABLE and current[key] in _LOST:
            out.append((key, old, current[key]))
    return out


def load_acks() -> dict[str, str]:
    """edge_key -> plan reference for intentionally-removed capabilities."""
    if not _ACKS_PATH.exists():
        return {}
    data = cast("dict[str, object]", yaml.safe_load(_ACKS_PATH.read_text()) or {})
    acks = data.get("acked_regressions", {})  # noqa: qg-empty-fallback — no acks is a legitimate empty state
    if not isinstance(acks, dict):
        return {}
    acks_typed = cast("dict[object, object]", acks)
    return {str(k): str(v) for k, v in acks_typed.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Capability-regression gate")
    parser.add_argument("--manifest", default=None, help="Path to capability-manifest.json (default: sibling UAC)")
    args = parser.parse_args()
    manifest_arg = cast("str | None", args.manifest)

    manifest_path = Path(manifest_arg) if manifest_arg else _manifest_path()

    if not manifest_path.exists():
        print(f"SKIP capability-regression gate: manifest not found at {manifest_path}")
        return 0
    if not _BASELINE_PATH.exists():
        print(f"SKIP capability-regression gate: no baseline yet at {_BASELINE_PATH}")
        return 0

    current = load_edge_statuses(manifest_path)
    baseline = load_baseline(_BASELINE_PATH)
    regressed = find_regressions(baseline, current)
    acks = load_acks()

    if not regressed:
        print("PASS capability-regression gate: no edge lost capability vs baseline.")
        return 0

    acked = [(k, o, n) for (k, o, n) in regressed if k in acks]
    unacked = [(k, o, n) for (k, o, n) in regressed if k not in acks]

    for k, o, n in acked:
        print(f"NOTE: acked regression {k}  ({o} -> {n})  ack: {acks[k]}")

    if unacked:
        print(f"FAIL capability-regression gate: {len(unacked)} edge(s) LOST capability without a plan ack:")
        for k, o, n in unacked:
            print(f"    {k}  ({o} -> {n})")
        print(f"   Restore the capability, OR ack it in {_ACKS_PATH}")
        print("   (acked_regressions: {<edge_key>: <plan-ref>}), OR accept the new state:")
        print("   python3 scripts/openapi/generate_capability_changelog.py --update-baseline")
        return 1

    print("PASS capability-regression gate: all regressions acked with a plan reference.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
