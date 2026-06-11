#!/usr/bin/env python3
"""Runbook Execution-Owner SSOT QG check.

Enforces the CLAUDE.md HARD RULE:

    Every runbook MUST declare 4 fields: `owner` / `cadence` / `verifier` /
    `last_executed`. No exceptions — missing fields = review-blocking.

The check walks the workspace for files matching `*runbook*.md` (excluding
`plans/archive/`), parses YAML frontmatter, and asserts the canonical
`execution:` block is present with all 4 sub-fields populated.

Canonical exemplar (current SSOT — only runbook in compliance as of 2026-05-15):
    plans/active/gate_3_phantom_audit_runbook_2026_05_13.md::
        execution:
          owner: "..."
          cadence: "..."
          verifier: "..."
          last_executed: "..."

Baseline mode (`--baseline-write`): writes the current violation count to
`scripts/quality_gates/runbook_execution_owner_baseline.yaml`. Ratchet mode
(default): fails if violations exceed the baseline (ratchets down toward zero).

This QG step codifies the rule from:
  - CLAUDE.md § "Runbook Execution-Owner SSOT (HARD RULE)"
  - plans/archive/issues/runbook_execution_governance_gaps_2026_05_08.md (origin)
  - plans/active/governance_qg_automation_gaps_post_cutover_2026_05_12.md (codification plan)

Exit-code semantics: 0 = clean (≤ baseline); 1 = regression / missing fields;
2 = arg / IO error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import cast

import yaml

REQUIRED_FIELDS = ("owner", "cadence", "verifier", "last_executed")
# `context/codex/` = vendored codex MIRRORS that non-PM repos sync for their
# in-repo AI context (e.g. unified-trading-system-ui/context/codex/...). The
# canonical codex SSOT — and therefore the only authoritative runbooks — lives in
# `unified-trading-pm/codex/`, which IS enforced here. Excluding the read-only
# mirrors prevents a stale copy (e.g. a pre-frontmatter sit-runbook.md) from
# failing the gate in full-workspace checkouts while the canonical is compliant.
# `.extra/` = local-only archived/scratch trees (e.g. .extra/unified-trading-codex/ — an
# archived codex mirror) that are NOT a tracked repo; same stale-mirror class as context/codex/.
EXCLUDED_DIRS = (
    "plans/archive/",
    # workspace-level archived mirrors (e.g. archive/unified-trading-codex/) — same stale-mirror class as .extra/
    "archive/",
    ".venv",
    ".venv-workspace",
    "build/",
    "dist/",
    "node_modules/",
    "context/codex/",
    ".extra/",
)
DEFAULT_BASELINE_PATH = Path(__file__).parent / "runbook_execution_owner_baseline.yaml"


class RunbookViolation:
    """A runbook file failing the Execution-Owner SSOT check."""

    def __init__(self, path: Path, missing_fields: list[str], reason: str = "missing-fields") -> None:
        self.path = path
        self.missing_fields = missing_fields
        self.reason = reason

    def __str__(self) -> str:
        if self.reason == "no-frontmatter":
            return f"{self.path}: NO YAML frontmatter — runbook must have one"
        if self.reason == "no-execution-block":
            return f"{self.path}: missing top-level `execution:` block in frontmatter"
        return f"{self.path}: execution.{{{','.join(self.missing_fields)}}} missing or empty"


def _iter_runbook_files(workspace_root: Path) -> list[Path]:
    """Walk workspace for files matching *runbook*.md, excluding archive + build dirs."""
    candidates: list[Path] = []
    for p in workspace_root.rglob("*runbook*.md"):
        rel = p.relative_to(workspace_root).as_posix()
        if any(rel.startswith(ex) or f"/{ex}" in f"/{rel}" for ex in EXCLUDED_DIRS):
            continue
        candidates.append(p)
    return sorted(candidates)


def _parse_frontmatter(path: Path) -> dict[str, object] | None:
    """Extract YAML frontmatter from a markdown file; returns None if missing."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    raw = text[4:end]
    try:
        loaded = cast(object, yaml.safe_load(raw))
    except yaml.YAMLError:
        return None
    if not isinstance(loaded, dict):
        return None
    return cast(dict[str, object], loaded)


def _check_runbook(path: Path) -> RunbookViolation | None:
    """Return a RunbookViolation if the file fails the 4-field SSOT, else None."""
    fm = _parse_frontmatter(path)
    if fm is None:
        return RunbookViolation(path, missing_fields=[], reason="no-frontmatter")
    execution = fm.get("execution")
    if not isinstance(execution, dict):
        return RunbookViolation(path, missing_fields=[], reason="no-execution-block")
    missing: list[str] = []
    for field in REQUIRED_FIELDS:
        value = execution.get(field)
        if not isinstance(value, str) or not value.strip():
            missing.append(field)
    if missing:
        return RunbookViolation(path, missing_fields=missing, reason="missing-fields")
    return None


def _load_baseline(baseline_path: Path) -> int:
    if not baseline_path.exists():
        return 0
    try:
        loaded = cast(object, yaml.safe_load(baseline_path.read_text(encoding="utf-8")))
    except yaml.YAMLError:
        return 0
    if isinstance(loaded, dict):
        count: object = cast(dict[str, object], loaded).get("violation_count")
        if isinstance(count, int):
            return count
    return 0


def _write_baseline(baseline_path: Path, count: int, violation_paths: list[Path]) -> None:
    payload: dict[str, object] = {
        "violation_count": count,
        "rule": "runbook-execution-owner-ssot",
        "source": "CLAUDE.md § 'Runbook Execution-Owner SSOT (HARD RULE)'",
        "baseline_files": [p.as_posix() for p in violation_paths],
    }
    baseline_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check runbook *.md files declare execution.{owner,cadence,verifier,last_executed}."
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Workspace root to scan (default: parent of unified-trading-pm)",
    )
    parser.add_argument(
        "--baseline-path",
        type=Path,
        default=DEFAULT_BASELINE_PATH,
        help=f"Baseline YAML path (default: {DEFAULT_BASELINE_PATH})",
    )
    parser.add_argument(
        "--baseline-write",
        action="store_true",
        help="Write current violation count to baseline file (bootstrap mode)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on ANY violation (ignore baseline) — use post-cleanup",
    )
    ns = parser.parse_args()
    workspace_root: Path = cast(Path, ns.workspace_root).resolve()
    baseline_path: Path = cast(Path, ns.baseline_path)
    baseline_write: bool = cast(bool, ns.baseline_write)
    strict: bool = cast(bool, ns.strict)
    if not workspace_root.exists():
        print(f"ERROR: workspace-root does not exist: {workspace_root}", file=sys.stderr)
        return 2

    runbooks = _iter_runbook_files(workspace_root)
    violations: list[RunbookViolation] = []
    for rb in runbooks:
        v = _check_runbook(rb)
        if v is not None:
            violations.append(v)

    print(f"Scanned {len(runbooks)} runbook file(s) under {workspace_root}; {len(violations)} violation(s).")

    if baseline_write:
        _write_baseline(baseline_path, len(violations), [v.path.relative_to(workspace_root) for v in violations])
        print(f"✅ Wrote baseline ({len(violations)} violations) to {baseline_path}")
        return 0

    if violations:
        print("\nViolations:")
        for v in violations:
            try:
                rel = v.path.relative_to(workspace_root)
            except ValueError:
                rel = v.path
            print(f"  - {rel}: {v.reason} {v.missing_fields if v.missing_fields else ''}")

    if strict:
        if violations:
            print(f"\n❌ STRICT mode: {len(violations)} violation(s) — every runbook MUST comply.")
            return 1
        print("\n✅ STRICT mode: 0 violations.")
        return 0

    baseline = _load_baseline(baseline_path)
    if len(violations) > baseline:
        print(
            f"\n❌ Regression: {len(violations)} violations exceed baseline {baseline}. "
            f"Either fix new violations OR re-run with --baseline-write after intentional debt."
        )
        return 1
    if len(violations) < baseline:
        print(
            f"\n⚠️  Improvement: {len(violations)} < baseline {baseline}. "
            f"Run --baseline-write to ratchet down (codifies the win)."
        )
        return 0
    print(f"\n✅ At baseline ({baseline}). Codify a fix to ratchet down.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
