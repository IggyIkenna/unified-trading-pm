#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""QG gate: disk-vs-backlog todo delta for every AO-dispatched plan.

SSOT: plans/active/issues/ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md

Problem: ``_parse_open_todos`` in agent-orchestrator deliberately excludes todos that
contain a live BLOCKED-<TOKEN> or stretch/DEFERRED-BY-DESIGN marker — correct in intent,
but nothing REPORTS the gap.  Measured 2026-08-08: 551 open todos on disk, 504 in the
backlog, **47 silently dropped across 37 docs** (14 with ZERO dispatchable todos).

This gate:
  1. Walks every ``assigned_vm: planning`` plan in ``plans/active/`` + ``plans/active/issues/``
  2. Compares, per doc, the raw unchecked-checkbox count against the dispatchable count
     produced by the parser's own logic (verbatim copy of ``_parse_open_todos`` below —
     NOT a re-implemented regex; see the "VERBATIM COPY" block comment).
  3. Ratchets the TOTAL excluded-todo count DOWN from the measured baseline (47).
  4. Emits a LOUDER finding for any doc that is ``assigned_vm: planning`` yet has ZERO
     dispatchable todos — those are the acutest case (an active AO plan AO will never touch).

Ratchet direction: DOWN only.  To accept new intentional debt use ``--baseline-write``.

Exit codes: 0 = at/below baseline; 1 = regression (gate failed); 2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

import yaml

logger = logging.getLogger("check_ao_dispatchable_todo_delta")

DEFAULT_BASELINE_PATH = Path(__file__).parent / "ao_dispatchable_todo_delta_baseline.yaml"

# ---------------------------------------------------------------------------
# VERBATIM COPY of the parsing constants and functions from
# agent-orchestrator/server/regen_backlog_from_plan.py.
#
# This is deliberately NOT a reimplemented regex — it is the same code so
# this gate uses EXACTLY the same oracle as the dispatcher.  When you update
# agent-orchestrator/server/regen_backlog_from_plan.py's parsing logic, update
# the corresponding block here too (search for "VERBATIM COPY END").
# ---------------------------------------------------------------------------
_UNCHECKED_RE = re.compile(r"^\s*-\s+\[ \]\s+(.+)$")
_FRONTMATTER_DELIM = "---"
_FENCE_RE = re.compile(r"^\s*```")
_STRIKETHROUGH_RE = re.compile(r"^\s*~~.*~~\s*$")
_TODO_BLOCK_BOUNDARY_RE = re.compile(r"^\s*-\s+\[|^\s*#")

_BLOCKED_TOKEN_RE = re.compile(
    r"BLOCKED-(CREDENTIALS|OPERATOR(-DECISION)?|BILLING|UPSTREAM-(OUTAGE|DESIGN)|PLAYWRIGHT|JURISDICTION)\b"
)
_STALE_MARKER_PREFIX_RE = re.compile(
    r"(?:\bwas\b|\bno longer\b|\bretagged\s+(?:from|away\s+from)\b|\bpreviously\b)"
    r"(?:\s*[`\[]{1,2}[\w\s\-]{0,24}[`\]]{1,2})?"
    r"\s*[:`\[]?\s*$",
    re.IGNORECASE,
)
_STALE_MARKER_SUFFIX_RE = re.compile(
    r"^[\s`\]]{0,3}"
    r"(?:\([^()]{0,24}\)[\s`\]]{0,3})?"
    r"(?:[\w.'-]+\s+){0,3}?"
    r"(?:was|is|were|has\s+been|have\s+been)\s+"
    r"(?:retired|resolved|lifted|cleared|closed|superseded|dropped|ruled)\b"
    r"|^\s*no\s+longer\s+appli(?:es|cable)\b",
    re.IGNORECASE,
)
_PERMANENT_NON_DISPATCHABLE_RE = re.compile(
    r"DEFERRED-BY-DESIGN\b"
    r"|_\(\s*[Ss]tretch"
    r"|\b[Ss]tretch,\s*optional\b"
    r"|\*\*[Ss]tretch\*\*"
)


def _has_live_blocked_token(todo_block: str) -> bool:
    """Verbatim copy from regen_backlog_from_plan._has_live_blocked_token."""
    for match in _BLOCKED_TOKEN_RE.finditer(todo_block):
        prefix = todo_block[max(0, match.start() - 60) : match.start()]
        if _STALE_MARKER_PREFIX_RE.search(prefix):
            continue
        suffix = todo_block[match.end() : match.end() + 60]
        if _STALE_MARKER_SUFFIX_RE.search(suffix):
            continue
        return True
    return False


def _is_non_dispatchable(todo_block: str) -> bool:
    """Verbatim copy from regen_backlog_from_plan._is_non_dispatchable."""
    return bool(_PERMANENT_NON_DISPATCHABLE_RE.search(todo_block)) or _has_live_blocked_token(todo_block)


def _parse_open_todos(plan_path: Path) -> list[str]:
    """Verbatim copy of regen_backlog_from_plan._parse_open_todos (description-only variant).

    Returns descriptions of dispatchable open todos only (identical filtering to the
    real parser — skips frontmatter, code blocks, strikethrough, done checkboxes,
    non-dispatchable todos).  The description is the checkbox-line text, matching the
    regen key used for brief-matching / orphan detection.
    """
    try:
        text = plan_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        logger.warning("Could not read plan %s: %s", plan_path, exc)
        return []

    lines = text.splitlines()
    results: list[str] = []
    in_frontmatter = False
    frontmatter_opened = False
    in_code_block = False
    line_num = 0
    idx = 0
    total_lines = len(lines)

    while idx < total_lines:
        raw_line = lines[idx]
        line_num += 1
        idx += 1
        line = raw_line.rstrip()

        if line_num == 1 and line.strip() == _FRONTMATTER_DELIM:
            in_frontmatter = True
            frontmatter_opened = True
            continue
        if in_frontmatter:
            if line.strip() == _FRONTMATTER_DELIM and frontmatter_opened:
                in_frontmatter = False
            continue

        if _FENCE_RE.match(line):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        if _STRIKETHROUGH_RE.match(line):
            continue

        m = _UNCHECKED_RE.match(line)
        if not m:
            continue

        description = m.group(1).strip()
        if not description:
            continue

        continuation_lines: list[str] = []
        peek = idx
        while peek < total_lines and not _TODO_BLOCK_BOUNDARY_RE.match(lines[peek]):
            continuation_lines.append(lines[peek])
            peek += 1

        todo_block = "\n".join([description, *continuation_lines])
        if _is_non_dispatchable(todo_block):
            continue

        results.append(description)

    return results


def _count_raw_open_todos(plan_path: Path) -> int:
    """Count ALL unchecked checkboxes (outside frontmatter and code blocks).

    This is the disk-level count: the number a reader of the plan would see as
    open work.  The delta vs _parse_open_todos is the 'silently excluded' count.
    """
    try:
        text = plan_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0

    lines = text.splitlines()
    count = 0
    in_frontmatter = False
    frontmatter_opened = False
    in_code_block = False
    line_num = 0

    for line in lines:
        line_num += 1
        stripped = line.rstrip()
        if line_num == 1 and stripped.strip() == _FRONTMATTER_DELIM:
            in_frontmatter = True
            frontmatter_opened = True
            continue
        if in_frontmatter:
            if stripped.strip() == _FRONTMATTER_DELIM and frontmatter_opened:
                in_frontmatter = False
            continue
        if _FENCE_RE.match(stripped):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if _UNCHECKED_RE.match(stripped):
            count += 1

    return count


# ---------------------------------------------------------------------------
# VERBATIM COPY END
# ---------------------------------------------------------------------------

# Frontmatter parsing helpers (local — PM-only context, no AO dep needed)
_FM_DELIM = "---"
_ASSIGNED_VM_RE = re.compile(r"^assigned_vm\s*:\s*(.+)$")
_STATUS_RE = re.compile(r"^status\s*:\s*(.+)$")
_EXECUTION_SCOPE_RE = re.compile(r"^execution_scope\s*:\s*(.+)$")
_UNASSIGNED_SENTINELS = frozenset({"na", "n/a"})
_SKIP_STATUSES = frozenset({"draft", "superseded", "resolved", "complete", "cancelled"})
_SKIP_NAMES = {"index.md", "_agent_pings.md"}


def _is_frontmatter_key_line(raw: str) -> bool:
    return bool(raw) and not raw[0].isspace()


def _get_frontmatter_value(plan_path: Path, field_re: re.Pattern[str]) -> str | None:
    try:
        text = plan_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    lines = text.splitlines()
    if not lines or lines[0].strip() != _FM_DELIM:
        return None
    for raw in lines[1:]:
        line = raw.strip()
        if line == _FM_DELIM:
            break
        if not _is_frontmatter_key_line(raw):
            continue
        m = field_re.match(line)
        if m:
            return m.group(1).split("#")[0].strip().lower()
    return None


def _is_ao_dispatched_plan(plan_path: Path) -> bool:
    """True iff this plan is assigned_vm: planning and status: active (ingestible)."""
    if plan_path.name.lower() in _SKIP_NAMES or plan_path.name.startswith("_"):
        return False
    assigned_vm = _get_frontmatter_value(plan_path, _ASSIGNED_VM_RE)
    if assigned_vm is None or assigned_vm in _UNASSIGNED_SENTINELS:
        return False
    if assigned_vm != "planning":
        return False
    status = _get_frontmatter_value(plan_path, _STATUS_RE)
    if status in _SKIP_STATUSES:
        return False
    scope = _get_frontmatter_value(plan_path, _EXECUTION_SCOPE_RE)
    if scope == "local-only":
        return False
    return True


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DocDelta:
    path: Path
    raw_open: int
    dispatchable: int

    @property
    def delta(self) -> int:
        return self.raw_open - self.dispatchable

    @property
    def is_zero_dispatchable(self) -> bool:
        return self.raw_open > 0 and self.dispatchable == 0


@dataclass
class DeltaReport:
    docs: list[DocDelta] = field(default_factory=list)

    @property
    def total_delta(self) -> int:
        return sum(d.delta for d in self.docs)

    @property
    def zero_dispatchable_docs(self) -> list[DocDelta]:
        return [d for d in self.docs if d.is_zero_dispatchable]

    @property
    def docs_with_delta(self) -> list[DocDelta]:
        return [d for d in self.docs if d.delta > 0]


def build_report(plans_dirs: list[Path]) -> DeltaReport:
    report = DeltaReport()
    for plans_dir in plans_dirs:
        for plan_path in sorted(plans_dir.glob("*.md")):
            if not _is_ao_dispatched_plan(plan_path):
                continue
            raw_open = _count_raw_open_todos(plan_path)
            dispatchable = len(_parse_open_todos(plan_path))
            report.docs.append(DocDelta(path=plan_path, raw_open=raw_open, dispatchable=dispatchable))
        issues_dir = plans_dir / "issues"
        if issues_dir.is_dir():
            for plan_path in sorted(issues_dir.glob("*.md")):
                if not _is_ao_dispatched_plan(plan_path):
                    continue
                raw_open = _count_raw_open_todos(plan_path)
                dispatchable = len(_parse_open_todos(plan_path))
                report.docs.append(DocDelta(path=plan_path, raw_open=raw_open, dispatchable=dispatchable))
    return report


# ---------------------------------------------------------------------------
# Baseline read/write
# ---------------------------------------------------------------------------


def _load_baseline(path: Path) -> dict[str, int]:
    try:
        with open(path, encoding="utf-8") as f:
            loaded = cast(object, yaml.safe_load(f))
    except (OSError, yaml.YAMLError):
        return {"total_excluded": 0, "zero_dispatchable_docs": 0}
    if not isinstance(loaded, dict):
        return {"total_excluded": 0, "zero_dispatchable_docs": 0}
    return {
        "total_excluded": int(loaded.get("total_excluded", 0)),
        "zero_dispatchable_docs": int(loaded.get("zero_dispatchable_docs", 0)),
    }


def _write_baseline(path: Path, report: DeltaReport) -> None:
    data = {
        "rule": "ao-dispatchable-todo-delta",
        "source": "plans/active/issues/ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md",
        "total_excluded": report.total_delta,
        "zero_dispatchable_docs": len(report.zero_dispatchable_docs),
        "docs_with_delta": [
            {"path": str(d.path.name), "raw": d.raw_open, "dispatchable": d.dispatchable, "delta": d.delta}
            for d in sorted(report.docs_with_delta, key=lambda x: -x.delta)
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:  # noqa: C901
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", default=None, help="Workspace root (default: auto-detect from git)")
    parser.add_argument("--baseline-path", default=str(DEFAULT_BASELINE_PATH))
    parser.add_argument(
        "--baseline-write",
        action="store_true",
        help="Write current counts as the new baseline (ratchet reset — use for accepted intentional debt).",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress per-doc output on pass")
    args = parser.parse_args(argv)

    # Resolve PM repo root
    if args.workspace_root:
        pm_root = Path(args.workspace_root) / "unified-trading-pm"
    else:
        here = Path(__file__).resolve()
        # scripts/quality_gates/ -> scripts/ -> repo root
        pm_root = here.parent.parent.parent
    plans_dirs = [pm_root / "plans" / "active"]

    report = build_report(plans_dirs)
    baseline_path = Path(args.baseline_path)

    if args.baseline_write:
        _write_baseline(baseline_path, report)
        print(
            f"✅ Baseline written: total_excluded={report.total_delta}, "
            f"zero_dispatchable_docs={len(report.zero_dispatchable_docs)}"
        )
        return 0

    baseline = _load_baseline(baseline_path)
    baseline_total = baseline["total_excluded"]
    baseline_zero = baseline["zero_dispatchable_docs"]

    failures: list[str] = []

    # Zero-dispatchable docs: loudest finding
    zero_docs = report.zero_dispatchable_docs
    if len(zero_docs) > baseline_zero:
        failures.append(
            f"zero-dispatchable-docs: {len(zero_docs)} docs have assigned_vm: planning but ZERO "
            f"dispatchable todos (baseline={baseline_zero}, regression={len(zero_docs) - baseline_zero})"
        )
    if zero_docs and not args.quiet:
        print(f"\n⚠  ZERO-DISPATCHABLE DOCS ({len(zero_docs)} — these active AO plans will never dispatch):")
        for d in sorted(zero_docs, key=lambda x: x.path.name):
            print(f"   {d.path.name}: {d.raw_open} open todos on disk, 0 dispatchable")

    # Total excluded count ratchet
    if report.total_delta > baseline_total:
        failures.append(
            f"total-excluded-todos: {report.total_delta} todos excluded from backlog "
            f"(baseline={baseline_total}, regression={report.total_delta - baseline_total})"
        )

    docs_with_delta = report.docs_with_delta
    if docs_with_delta and not args.quiet:
        print(f"\nDelta report ({len(docs_with_delta)} docs with excluded todos):")
        for d in sorted(docs_with_delta, key=lambda x: -x.delta):
            print(f"  {d.path.name}: {d.raw_open} raw, {d.dispatchable} dispatchable, {d.delta} excluded")
        print(f"\nTotal: {report.total_delta} excluded across {len(docs_with_delta)} docs (baseline={baseline_total})")

    if failures:
        print("\n❌ ao-dispatchable-todo-delta regressions:", file=sys.stderr)
        for f in failures:
            print(f"   • {f}", file=sys.stderr)
        print(
            f"\n   To accept new intentional debt (excluded todos with genuine BLOCKED-* markers):",
            file=sys.stderr,
        )
        print(f"   python3 {__file__} --baseline-write", file=sys.stderr)
        print(
            "   But first confirm the excluded todos are genuinely blocked — not false positives from the parser.",
            file=sys.stderr,
        )
        return 1

    if not args.quiet:
        print(
            f"✅ ao-dispatchable-todo-delta: total_excluded={report.total_delta}/{baseline_total}, "
            f"zero_dispatchable_docs={len(zero_docs)}/{baseline_zero} (at/below baseline)"
        )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    sys.exit(main())
