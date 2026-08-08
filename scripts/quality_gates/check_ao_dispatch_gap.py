#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Shrinking-ratchet gate on silently non-dispatchable todos in assigned_vm:planning docs.

SSOT / why this exists:
plans/active/issues/ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md.
MEASURED 2026-08-08: 551 open todos on disk across every `assigned_vm: planning` doc, 504 parsed
into the backlog by regen's own `_parse_open_todos` -- 47 silently dropped across 37 docs, 14 of
those docs parsing to ZERO dispatchable todos. A todo can be silently dropped either DELIBERATELY
(a live BLOCKED-<token> / stretch-optional marker -- correct, a worker can't act on it) or
ACCIDENTALLY (a regex-exclusion bug -- four of those have been fixed by widening
`_STALE_MARKER_PREFIX_RE`/friends since 2026-07-28 and the class keeps recurring, because the
defect is that exclusion is UNREPORTED, not that the regex is too narrow).

This gate never re-implements the parser -- see the four-widenings history above -- it calls
agent-orchestrator's REAL `_parse_open_todos` (the actual dispatch oracle) via a subprocess into
that repo's own `.venv` (server/regen_backlog_from_plan.py pulls fastapi/sqlalchemy/
unified-trading-library/pydantic-settings, none of which PM's own .venv carries, so a same-process
import isn't viable -- see scripts/plan_hygiene/dump_dispatchable_todos.py in agent-orchestrator).
Each on-disk open todo (`^- \\[ \\]` line) not present in the dispatchable set is classified
DECLARED (its own continuation block states a live BLOCKED-<token> / [OPERATOR] tag / explicit
"blocked on" line) or ACCIDENTAL (no such declaration -- the todo's own text asserts it's
workable, exactly the sports-Betfair trigger shape). Ratchets on two counts, same shape as
na_corpus_baseline.yaml: `max_accidental_exclusions` (undeclared drops) and
`max_zero_dispatchable_docs` (an active assigned_vm:planning doc AO will never touch at all).

Needs WORKSPACE_ROOT (the sibling agent-orchestrator clone + its `.venv`) -- degrades to a no-op
when either is absent (same shape as check_repo_docs_ssot.py: CI / a clone without every sibling
present skips silently; this is the LOCAL / full-workspace gate).

Usage: check_ao_dispatch_gap.py --workspace-root <path> [--quiet] [--update-baseline]
Exit 0 = current accidental/zero-dispatchable counts <= baseline (or gate skipped, no workspace).
Exit 1 = either count grew beyond baseline.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

PM = Path(__file__).resolve().parents[2]
PLAN_DIRS = [PM / "plans" / "active", PM / "plans" / "active" / "issues"]
BASELINE = Path(__file__).resolve().parent / "ao_dispatch_gap_baseline.yaml"

sys.path.insert(0, str(PM / "scripts" / "docs"))
import docspec

# A todo is DECLARED non-dispatchable (deliberate, not a parser bug) when its own text states
# one of these. Mirrors what a human/`- [ ]` reader would recognise as "this waits on something",
# deliberately looser than regen's own live-token detector (regen's job is precision -- don't
# dispatch a resolved marker; this gate's job is recall -- don't let an undeclared drop hide).
# Non-marker-token declare signals -- these don't need proximity/negation checking, unlike
# BLOCKED-<TOKEN> below (see _is_declared).
_DECLARED_RE = re.compile(
    r"\[OPERATOR\]"
    r"|\bblocked[- ]on\b"
    r"|DEFERRED-BY-DESIGN\b"
    r"|\bstretch,?\s*optional\b",
    re.IGNORECASE,
)

_MARKER_RE = re.compile(r"BLOCKED-[A-Z][A-Z-]*", re.IGNORECASE)

# The sports-Betfair trigger shape (2026-08-08): "Do NOT mark this BLOCKED-CREDENTIALS" contains
# the marker text but explicitly DISCLAIMS it -- a bare marker-presence check would misclassify
# this as a deliberate hold, exactly the false-positive this gate exists to catch.
_NEGATED_DECLARE_RE = re.compile(
    r"do\s+not\s+mark|must\s+not\s+(?:gate|block)|should\s+not\s+(?:be\s+)?(?:mark|block)|"
    r"no\s+longer\s+block|not\s+block(?:ed|ing)\b",
    re.IGNORECASE,
)
# How far back (chars) to look for a negation phrase before a marker match. Windowed rather than
# whole-block, same shape as regen's own _STALE_MARKER_PREFIX_RE lookback -- a whole-block search
# false-positived on an UNRELATED "not blocking" phrase elsewhere in a real corpus doc
# (prediction_satellite_ao_dispatch_batch6_2026_07_29.md: a genuinely-blocked Betfair todo whose
# block also happens to quote an unrelated source doc's "not blocking paper" phrase).
_NEGATION_WINDOW = 80


def _is_declared(block: str) -> bool:
    if _DECLARED_RE.search(block):
        return True
    for m in _MARKER_RE.finditer(block):
        prefix = block[max(0, m.start() - _NEGATION_WINDOW) : m.start()]
        if not _NEGATED_DECLARE_RE.search(prefix):
            return True  # a genuine, undisclaimed marker
    return False


# Mirrors regen's own `_UNCHECKED_RE` (server/regen_backlog_from_plan.py) exactly so the
# extracted description text lines up character-for-character with what the AO wrapper reports.
_OPEN_TODO_RE = re.compile(r"^\s*-\s+\[ \]\s+(.+)$")
_ANY_CHECKBOX_OR_HEADER_RE = re.compile(r"^\s*-\s+\[|^\s*#")

_BASELINE_HEADER = """\
# Shrinking-ratchet baseline for check_ao_dispatch_gap.py.
#
# Tracks two numbers over the live `assigned_vm: planning`, status in {active, open} corpus
# (plans/active/*.md + plans/active/issues/*.md): the count of ACCIDENTAL (undeclared) silently
# non-dispatchable todos, and the count of docs that parse to ZERO dispatchable todos. Shrinking
# ratchet, same convention as na_corpus_baseline.yaml -- a run that finds either number HIGHER
# than this baseline fails. NEVER hand-raise these numbers to silence a run that just found new
# accidental exclusions -- only --update-baseline after actually fixing/filing the new ones.
#
# See plans/active/issues/ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md.
"""


def _iter_disk_open_todos(text: str) -> list[tuple[str, str]]:
    """Return [(description, continuation_block), ...] for every on-disk `- [ ]` line.

    continuation_block is the checkbox line plus every following line up to the next
    checkbox item / header -- same boundary regen's own `_is_non_dispatchable` scans
    (blocked_marker_continuation_line_not_scanned_2026_07_26.md: a BLOCKED-* marker is
    commonly annotated in prose below the checkbox, not on it).
    """
    lines = text.splitlines()
    out: list[tuple[str, str]] = []
    in_frontmatter = False
    frontmatter_opened = False
    in_code_block = False
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if i == 0 and stripped == "---":
            in_frontmatter = True
            frontmatter_opened = True
            i += 1
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            i += 1
            continue
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            i += 1
            continue
        if in_code_block:
            i += 1
            continue
        m = _OPEN_TODO_RE.match(line)
        if m:
            desc = m.group(1).strip()
            block_lines = [line]
            j = i + 1
            while j < n and not _ANY_CHECKBOX_OR_HEADER_RE.match(lines[j]):
                block_lines.append(lines[j])
                j += 1
            out.append((desc, "\n".join(block_lines)))
        i += 1
    _ = frontmatter_opened
    return out


def _eligible_docs() -> list[Path]:
    docs: list[Path] = []
    for d in PLAN_DIRS:
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.md")):
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            fm, _body = docspec.parse_frontmatter(text)
            if not fm:
                continue
            if fm.get("assigned_vm") != "planning":
                continue
            if fm.get("status") not in ("active", "open"):
                continue
            docs.append(p)
    return docs


def _dispatchable_data(ao_dir: Path, docs: list[Path]) -> dict[str, set[str]] | None:
    """Batch-call agent-orchestrator's real _parse_open_todos via its own .venv.

    Returns {str(doc_path): {dispatchable_description, ...}}, or None if the AO venv/wrapper
    isn't available (gate degrades to a no-op rather than a hard failure — see module docstring).
    """
    venv_python = ao_dir / ".venv" / "bin" / "python3"
    wrapper = ao_dir / "scripts" / "plan_hygiene" / "dump_dispatchable_todos.py"
    if not venv_python.is_file() or not wrapper.is_file():
        return None
    proc = subprocess.run(
        [str(venv_python), str(wrapper), *[str(p) for p in docs]],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(f"⚠️  dump_dispatchable_todos.py failed (rc={proc.returncode}): {proc.stderr.strip()}", file=sys.stderr)
        return None
    parsed = json.loads(proc.stdout)
    return {path: set(info["todos"]) for path, info in parsed.items()}


def classify(disk_desc: str, disk_block: str, dispatchable_descs: set[str]) -> str | None:
    """Return 'declared', 'accidental', or None if this disk todo IS in the dispatchable set.

    Per-todo (not gap-arithmetic) classification: exact description-text match against
    regen's own dispatchable set — both sides derive the description the same way (the
    checkbox line's own text, stripped), so this is a direct membership check, not a guess.
    """
    if disk_desc in dispatchable_descs:
        return None
    return "declared" if _is_declared(disk_block) else "accidental"


def _load_baseline() -> dict[str, object]:
    if not BASELINE.is_file():
        return {}
    return yaml.safe_load(BASELINE.read_text()) or {}


def run(workspace_root: Path | None) -> dict[str, object]:
    """Compute the current corpus state. Returns a report dict; 'skipped': True when the
    AO sibling/.venv isn't available."""
    if workspace_root is None:
        return {"skipped": True}
    ao_dir = workspace_root / "agent-orchestrator"
    if not ao_dir.is_dir():
        return {"skipped": True}

    docs = _eligible_docs()
    dispatchable = _dispatchable_data(ao_dir, docs)
    if dispatchable is None:
        return {"skipped": True}

    accidental_items: list[str] = []
    declared_items: list[str] = []
    zero_dispatchable_docs: list[str] = []

    for doc in docs:
        text = doc.read_text(encoding="utf-8", errors="replace")
        disk_todos = _iter_disk_open_todos(text)
        rel = str(doc)
        disp_descs = dispatchable.get(rel, set())
        if disk_todos and not disp_descs:
            zero_dispatchable_docs.append(rel)
        for desc, block in disk_todos:
            verdict = classify(desc, block, disp_descs)
            if verdict == "accidental":
                accidental_items.append(f"{rel}: {desc}")
            elif verdict == "declared":
                declared_items.append(f"{rel}: {desc}")

    return {
        "skipped": False,
        "docs_checked": len(docs),
        "accidental_count": len(accidental_items),
        "accidental_items": accidental_items,
        "declared_count": len(declared_items),
        "zero_dispatchable_docs": zero_dispatchable_docs,
        "zero_dispatchable_count": len(zero_dispatchable_docs),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", type=Path, default=None)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--update-baseline", action="store_true")
    args = parser.parse_args(argv)

    workspace_root = args.workspace_root
    report = run(workspace_root)

    if report.get("skipped"):
        if not args.quiet:
            print("check_ao_dispatch_gap: skipped (no --workspace-root / agent-orchestrator .venv found)")
        return 0

    accidental = report["accidental_count"]
    zero_dispatchable = report["zero_dispatchable_count"]

    if args.update_baseline:
        baseline = _load_baseline()
        old_acc = baseline.get("max_accidental_exclusions")
        old_zero = baseline.get("max_zero_dispatchable_docs")
        warnings = []
        if isinstance(old_acc, int) and accidental > old_acc:
            warnings.append(f"max_accidental_exclusions RAISED {old_acc} -> {accidental}")
        if isinstance(old_zero, int) and zero_dispatchable > old_zero:
            warnings.append(f"max_zero_dispatchable_docs RAISED {old_zero} -> {zero_dispatchable}")
        BASELINE.write_text(
            _BASELINE_HEADER
            + f"max_accidental_exclusions: {accidental}\n"
            + f"max_zero_dispatchable_docs: {zero_dispatchable}\n"
            + f'last_updated: "{datetime.now(UTC).date().isoformat()}"\n'
        )
        print(
            f"ao_dispatch_gap_baseline.yaml regenerated: "
            f"max_accidental_exclusions={accidental}, max_zero_dispatchable_docs={zero_dispatchable}"
        )
        for w in warnings:
            print(f"⚠️  {w} -- verify this is reviewed, not a silenced failure", file=sys.stderr)
        return 0

    baseline = _load_baseline()
    max_acc = baseline.get("max_accidental_exclusions")
    max_zero = baseline.get("max_zero_dispatchable_docs")

    problems = []
    if isinstance(max_acc, int) and accidental > max_acc:
        problems.append(f"accidental (undeclared) non-dispatchable todos grew: {accidental} > baseline {max_acc}")
    if isinstance(max_zero, int) and zero_dispatchable > max_zero:
        problems.append(f"zero-dispatchable docs grew: {zero_dispatchable} > baseline {max_zero}")

    if problems:
        print("❌ check_ao_dispatch_gap: silently non-dispatchable todos grew beyond baseline:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        for item in report["accidental_items"]:
            print(f"    accidental: {item}", file=sys.stderr)
        for doc in report["zero_dispatchable_docs"]:
            print(f"    zero-dispatchable doc: {doc}", file=sys.stderr)
        print(
            "  Remedy: for each accidental item, either add a declared BLOCKED-<token>/[OPERATOR]\n"
            "  marker (if it genuinely waits on something) or fix the doc so it's dispatchable, then\n"
            "  re-run with --update-baseline. Never widen the parser's own marker regex as the fix.",
            file=sys.stderr,
        )
        return 1

    if not args.quiet:
        print(
            f"✅ check_ao_dispatch_gap: {accidental} accidental / {zero_dispatchable} zero-dispatchable "
            f"(baseline: {max_acc}/{max_zero}, {report['docs_checked']} docs checked)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
