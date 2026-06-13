"""Versioned capability manifest changelog + regression baseline (Wave-2 #5).

Reads the committed capability manifest (``unified-api-contracts/openapi/
capability-manifest.json``), compares every edge's status against a committed
baseline (``capability-edge-status-baseline.json``, next to this script), and
emits a human-readable changelog (``openapi/capability-changelog.md``):

  - **Newly available** — edges the system *learned to do* since the baseline
    (investor-update material: "what the system learned this month").
  - **Regressed** — edges that lost a capability (``available`` → ``not_available``
    / ``not_registered``). These are what the regression GATE
    (``scripts/quality_gates/check_capability_regression.py``) blocks unless
    acked with a plan reference.
  - **New / removed edges** and softer status changes.

This script is INTENTIONALLY decoupled from the registry walk: it reads the
already-generated manifest JSON, so it runs anywhere (no ``.venv-workspace``)
and is deterministic. ``--update-baseline`` rewrites the baseline from the
current manifest (run after an intentional, reviewed capability change).

SSOT: ``plans/active/capability_wizard_and_manifest_2026_06_11.md`` Wave-2 #5.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import cast

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

_SCRIPT_DIR = Path(__file__).resolve().parent
_BASELINE_PATH = _SCRIPT_DIR / "capability-edge-status-baseline.json"

#: Statuses that count as "the system can do this".
_AVAILABLE = "available"
#: Statuses that count as a lost capability when regressed FROM ``available``.
_LOST = {"not_available", "not_registered"}


def edge_key(from_node: str, relation: str, to_node: str) -> str:
    """Stable identity for an edge (independent of status)."""
    return f"{from_node}|{relation}|{to_node}"


def load_edge_statuses(manifest_path: Path) -> dict[str, str]:
    """Map every manifest edge to its status, keyed by stable edge identity.

    On a duplicate (from, relation, to) the BEST (most-available) status wins,
    so a single available edge is never masked by a sibling not_available.
    """
    raw = cast("dict[str, object]", json.loads(manifest_path.read_text()))
    # Fail-fast: a manifest with no "edges" is malformed (KeyError loud), never silently empty.
    edges = cast("list[dict[str, str]]", raw["edges"])
    rank = {"available": 0, "partial": 1, "not_registered": 2, "not_available": 3}
    out: dict[str, str] = {}
    for e in edges:
        key = edge_key(e["from_node_id"], e["relation"], e["to_node_id"])
        status = e.get("status", "not_registered")
        prev = out.get(key)
        if prev is None or rank.get(status, 9) < rank.get(prev, 9):
            out[key] = status
    return out


def load_baseline(baseline_path: Path) -> dict[str, str]:
    if not baseline_path.exists():
        return {}
    return cast("dict[str, str]", json.loads(baseline_path.read_text()))


def diff_statuses(
    baseline: dict[str, str], current: dict[str, str]
) -> tuple[list[str], list[tuple[str, str, str]], list[tuple[str, str]], list[str], list[str]]:
    """Return (newly_available, regressed, soft_changes, new_edges, removed_edges).

    - newly_available: edge became ``available`` (from a non-available baseline state).
    - regressed: (key, old, new) where old==available and new in _LOST — the hard gate.
    - soft_changes: (key, old→new) status changes that are neither of the above.
    - new_edges: present now, absent in baseline.
    - removed_edges: present in baseline, absent now.
    """
    newly_available: list[str] = []
    regressed: list[tuple[str, str, str]] = []
    soft_changes: list[tuple[str, str]] = []
    new_edges: list[str] = []
    removed_edges: list[str] = []

    for key in sorted(current):
        cur = current[key]
        if key not in baseline:
            new_edges.append(key)
            if cur == _AVAILABLE:
                newly_available.append(key)
            continue
        old = baseline[key]
        if old == cur:
            continue
        if old != _AVAILABLE and cur == _AVAILABLE:
            newly_available.append(key)
        elif old == _AVAILABLE and cur in _LOST:
            regressed.append((key, old, cur))
        else:
            soft_changes.append((key, f"{old}→{cur}"))

    for key in sorted(baseline):
        if key not in current:
            removed_edges.append(key)

    return newly_available, regressed, soft_changes, new_edges, removed_edges


def _section(title: str, lines: list[str]) -> list[str]:
    out = [f"## {title} ({len(lines)})", ""]
    if not lines:
        out.append("_none_")
    else:
        out.extend(f"- `{line}`" for line in lines)
    out.append("")
    return out


def render_changelog(
    manifest_commit: str,
    newly_available: list[str],
    regressed: list[tuple[str, str, str]],
    soft_changes: list[tuple[str, str]],
    new_edges: list[str],
    removed_edges: list[str],
) -> str:
    out: list[str] = [
        "# Capability changelog",
        "",
        "Diff of the committed capability manifest vs the last reviewed baseline",
        "(`scripts/openapi/capability-edge-status-baseline.json`). Regenerated by",
        "`scripts/openapi/generate_capability_changelog.py`. **Newly available** =",
        "what the system learned to do since the baseline. **Regressed** = lost",
        "capability — blocked by the regression gate unless acked.",
        "",
        f"Manifest commit: `{manifest_commit}`",
        "",
    ]
    out.extend(_section("Newly available — system learned to do", newly_available))
    out.extend(
        _section(
            "Regressed — lost capability (gate-blocked unless acked)", [f"{k}  ({o}→{n})" for k, o, n in regressed]
        )
    )
    out.extend(_section("New edges (added to the manifest)", new_edges))
    out.extend(_section("Removed edges (dropped from the manifest)", removed_edges))
    out.extend(_section("Other status changes", [f"{k}  ({d})" for k, d in soft_changes]))
    return "\n".join(out) + "\n"


def _resolve_manifest(manifest_arg: str | None, workspace_arg: str | None) -> Path:
    if manifest_arg:
        return Path(manifest_arg)
    workspace_root = Path(workspace_arg) if workspace_arg else _SCRIPT_DIR.parent.parent.parent
    return workspace_root / "unified-api-contracts" / "openapi" / "capability-manifest.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Capability manifest changelog + regression baseline")
    parser.add_argument("--manifest", default=None, help="Path to capability-manifest.json (default: sibling UAC)")
    parser.add_argument("--workspace-root", default=None, help="Workspace root (default: PM's parent)")
    parser.add_argument(
        "--output-dir", default=None, help="Where to write capability-changelog.md (default: UAC openapi/)"
    )
    parser.add_argument("--update-baseline", action="store_true", help="Rewrite the baseline from the current manifest")
    args = parser.parse_args()
    manifest_arg = cast("str | None", args.manifest)
    workspace_arg = cast("str | None", args.workspace_root)
    output_arg = cast("str | None", args.output_dir)
    update_baseline = bool(cast("object", args.update_baseline))

    manifest_path = _resolve_manifest(manifest_arg, workspace_arg)
    if not manifest_path.exists():
        logger.error("Manifest not found: %s (run generate_capability_manifest.py first)", manifest_path)
        return 1

    raw = cast("dict[str, object]", json.loads(manifest_path.read_text()))
    manifest_commit = str(raw.get("generated_from_commit", "unknown"))
    current = load_edge_statuses(manifest_path)
    baseline = load_baseline(_BASELINE_PATH)

    newly_available, regressed, soft_changes, new_edges, removed_edges = diff_statuses(baseline, current)

    output_dir = Path(output_arg) if output_arg else manifest_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    changelog_path = output_dir / "capability-changelog.md"
    changelog_path.write_text(
        render_changelog(manifest_commit, newly_available, regressed, soft_changes, new_edges, removed_edges)
    )
    logger.info(
        "Wrote %s (newly_available=%d regressed=%d new=%d removed=%d soft=%d)",
        changelog_path,
        len(newly_available),
        len(regressed),
        len(new_edges),
        len(removed_edges),
        len(soft_changes),
    )

    if update_baseline:
        _BASELINE_PATH.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
        logger.info("Updated baseline: %s (%d edges)", _BASELINE_PATH, len(current))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
