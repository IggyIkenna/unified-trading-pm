#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Codex doc freshness QG check (gap-G-12 / D-18 codification).

Walks cutover-critical codex surfaces and asserts every `*.md` file declares
`last_reviewed: YYYY-MM-DD` in YAML frontmatter, and that the date is no older
than the configured staleness window (default 90 days).

Cutover-critical surfaces (per governance_qg_automation_gaps_post_cutover_2026_05_12.md
§ Group B):
  - codex/02-data/        — data contracts, manifests, honest-absence
  - codex/04-architecture/ — service architecture + DeFi execution
  - codex/05-infrastructure/ — VM launchers, runbooks, deployment
  - codex/11-project-management/ — orchestration + planning SSOTs

Baseline mode (`--baseline-write`) writes the current violation count to
`scripts/quality_gates/codex_doc_freshness_baseline.yaml`. Ratchet mode
(default) fails if violations exceed baseline.

Exit-code semantics:
  0 — at-or-below baseline (clean)
  1 — regression / missing-frontmatter / stale-doc
  2 — argument / IO / yaml-parse error

SSOT: CLAUDE.md § "Post-Plan-Phase Codex Audit (HARD RULE)" — codex docs
must reflect shipped contracts; `last_reviewed:` is the codified review-stamp.

Origin: plans/active/governance_qg_automation_gaps_post_cutover_2026_05_12.md
        § "Group B — Codex freshness ratchet (G-12 + D-18)".
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path
from typing import cast

import yaml

CUTOVER_CRITICAL_DIRS = (
    "codex/02-data",
    "codex/04-architecture",
    "codex/05-infrastructure",
    "codex/11-project-management",
)
DEFAULT_STALENESS_DAYS = 90
DEFAULT_BASELINE_PATH = Path(__file__).parent / "codex_doc_freshness_baseline.yaml"


class FreshnessViolation:
    """A codex doc failing the freshness SSOT."""

    def __init__(self, path: Path, reason: str, detail: str = "") -> None:
        self.path = path
        self.reason = reason
        self.detail = detail

    def __str__(self) -> str:
        if self.detail:
            return f"{self.path}: {self.reason} ({self.detail})"
        return f"{self.path}: {self.reason}"


def _iter_codex_md(workspace_root: Path) -> list[Path]:
    """Walk cutover-critical codex surfaces for *.md files."""
    candidates: list[Path] = []
    for d in CUTOVER_CRITICAL_DIRS:
        root = workspace_root / "unified-trading-pm" / d
        if not root.is_dir():
            continue
        for p in root.rglob("*.md"):
            candidates.append(p)
    return sorted(candidates)


def _parse_frontmatter(path: Path) -> dict[str, object] | None:
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


def _parse_last_reviewed(value: object) -> datetime.date | None:
    """Accept date or YYYY-MM-DD string."""
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        try:
            return datetime.date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def _check_doc(path: Path, staleness_days: int, today: datetime.date) -> FreshnessViolation | None:
    fm = _parse_frontmatter(path)
    if fm is None:
        return FreshnessViolation(path, "no-frontmatter")
    last_reviewed_raw = fm.get("last_reviewed")
    if last_reviewed_raw is None:
        return FreshnessViolation(path, "no-last_reviewed-field")
    last_reviewed = _parse_last_reviewed(last_reviewed_raw)
    if last_reviewed is None:
        return FreshnessViolation(path, "invalid-last_reviewed-format", str(last_reviewed_raw)[:40])
    age = (today - last_reviewed).days
    if age > staleness_days:
        return FreshnessViolation(path, "stale", f"{age}d old (limit {staleness_days}d; last_reviewed={last_reviewed})")
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


def _write_baseline(baseline_path: Path, count: int, violations: list[FreshnessViolation]) -> None:
    payload: dict[str, object] = {
        "violation_count": count,
        "rule": "codex-doc-freshness",
        "source": (
            "CLAUDE.md § 'Post-Plan-Phase Codex Audit (HARD RULE)' + "
            "governance_qg_automation_gaps_post_cutover_2026_05_12.md § Group B"
        ),
        "baseline_files": [{"path": str(v.path), "reason": v.reason} for v in violations],
    }
    baseline_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check codex docs declare last_reviewed: + are no older than N days.")
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path(__file__).resolve().parents[2].parent,
        help="Workspace root to scan",
    )
    parser.add_argument(
        "--staleness-days",
        type=int,
        default=DEFAULT_STALENESS_DAYS,
        help=f"Max age in days (default: {DEFAULT_STALENESS_DAYS})",
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
    parser.add_argument("--strict", action="store_true", help="Fail on ANY violation (ignore baseline)")
    return parser.parse_args()


def main() -> int:
    ns = _parse_args()
    workspace_root: Path = cast(Path, ns.workspace_root).resolve()
    staleness_days: int = cast(int, ns.staleness_days)
    baseline_path: Path = cast(Path, ns.baseline_path)
    baseline_write: bool = cast(bool, ns.baseline_write)
    strict: bool = cast(bool, ns.strict)

    if not workspace_root.exists():
        print(f"ERROR: workspace-root does not exist: {workspace_root}", file=sys.stderr)
        return 2

    today = datetime.date.today()
    docs = _iter_codex_md(workspace_root)
    violations: list[FreshnessViolation] = []
    for doc in docs:
        v = _check_doc(doc, staleness_days, today)
        if v is not None:
            violations.append(v)

    print(
        f"Scanned {len(docs)} codex doc(s) across {len(CUTOVER_CRITICAL_DIRS)} cutover-critical "
        f"surface(s); {len(violations)} violation(s) (staleness limit: {staleness_days}d)."
    )

    if baseline_write:
        _write_baseline(baseline_path, len(violations), violations)
        print(f"✅ Wrote baseline ({len(violations)} violations) to {baseline_path}")
        return 0

    if violations:
        print("\nViolations (first 20 shown):")
        for v in violations[:20]:
            try:
                rel = v.path.relative_to(workspace_root)
            except ValueError:
                rel = v.path
            print(f"  - {rel}: {v.reason}{(' (' + v.detail + ')') if v.detail else ''}")
        if len(violations) > 20:
            print(f"  ... + {len(violations) - 20} more")

    if strict:
        if violations:
            print(f"\n❌ STRICT mode: {len(violations)} violation(s).")
            return 1
        print("\n✅ STRICT mode: 0 violations.")
        return 0

    baseline = _load_baseline(baseline_path)
    if len(violations) > baseline:
        print(
            f"\n❌ Regression: {len(violations)} > baseline {baseline}. "
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
