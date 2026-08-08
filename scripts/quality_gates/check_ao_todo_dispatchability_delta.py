#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Shrinking-ratchet gate: disk-open vs backlog-dispatchable todo delta per AO-dispatched doc.

WHAT IT MEASURES
----------------
For every `assigned_vm: planning` doc in plans/active/ (and issues/), runs two counts:
  - disk_open: raw `^- [ ]` lines
  - dispatchable: result of regen's real `_parse_open_todos` (the parser IS the oracle)
  delta = disk_open - dispatchable

Todos in the delta are excluded by `_is_non_dispatchable` — they have a BLOCKED-*/DEFERRED-BY-
DESIGN/stretch marker somewhere in their text block. The defect this gate catches: an *accidental*
exclusion where a todo mentions a BLOCKED token in prose (e.g. "Do NOT mark this BLOCKED-
CREDENTIALS") rather than asserting it as its own block state, silently dropping the todo from
the dispatch queue with no warning.

TWO RATCHETS
------------
1. TOTAL non-dispatchable open todos across the whole corpus (baseline 47, shrinks over time).
2. ZERO-dispatchable docs: an `assigned_vm: planning` active doc with disk_open > 0 but
   dispatchable == 0 is an AO plan AO will never touch — either mis-tagged or finished, never
   correct as-is. Louder finding, separate ratchet (baseline 14).

DECLARATION REQUIREMENT
-----------------------
A non-dispatchable todo must be "declared" — it must carry an obvious intentional marker that a
reader can verify. Undeclared todos fail the gate immediately (no ratchet tolerance) because they
represent the exact accidental-exclusion failure mode this gate was built to catch:

Declared (passes):
  - Todo's *first line* matches `_PERMANENT_NON_DISPATCHABLE_RE` (DEFERRED-BY-DESIGN / stretch)
  - Todo's *first line* contains a live BLOCKED-* token (the first line IS the declaration)
  - Todo has `[BLOCKED]` or `[DEFERRED]` in its leading tag cluster

Undeclared (fails immediately):
  - Non-dispatchable due to BLOCKED-* token in *continuation block only* (not the first line) AND
    the first line has no `[BLOCKED]`/`[DEFERRED]` tag → potentially accidental.

Authors of intentionally-blocked todos must put the marker in the description line itself
(e.g. `[BACKEND] P1. Add X BLOCKED-CREDENTIALS — waiting for vendor`) or tag the todo `[BLOCKED]`.

HOW TO FIX A FAILING RUN
-------------------------
  a) Undeclared non-dispatchable todo → move the BLOCKED-* marker to the description line, or
     add a `[BLOCKED]` tag in the leading tag cluster.
  b) Ratchet exceeded (total count grew) → find and fix the new non-dispatchable todo(s).
  c) Re-baseline after a genuine corpus shrink: `--baseline-write` writes the new counts.

IMPORT NOTE
-----------
Uses `_parse_open_todos` and `_is_non_dispatchable` from
`agent-orchestrator/server/regen_backlog_from_plan.py` via controlled sys.modules injection.
The AO module has internal dependencies (pydantic, UTL) that are not available in the PM QG
context. We stub them so the pure-Python parser functions can be loaded without executing
the full import chain. If the import fails (AO not checked out alongside PM), the gate skips
with a warning — it does NOT fail the QG when AO is absent.
"""

from __future__ import annotations

import argparse
import importlib.util
import logging
import re
import sys
import types
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_BASELINE_PATH = Path(__file__).parent / "ao_todo_dispatchability_baseline.yaml"

_BASELINE_HEADER = """\
# Shrinking-ratchet baseline for the AO todo dispatchability delta
# (check_ao_todo_dispatchability_delta.py).
#
# MEASURES (per assigned_vm:planning doc):
#   total_non_dispatchable:    sum of (disk_open - dispatchable) across all AO docs.
#   zero_dispatchable_docs:    count of AO docs with disk_open > 0 but dispatchable == 0.
#   undeclared_non_dispatchable: todos excluded by regen's parser but with no BLOCKED-*/
#                              [BLOCKED]/[DEFERRED]/permanent-marker declaration on the
#                              todo's first line — likely accidental exclusions.
#
# NEVER hand-raise these numbers to silence a run that found the corpus grew.
# Only --baseline-write after a genuine corpus shrink (confirmed fixes to the accidental
# exclusions or intentional retirements of blocked todos).
#
# See: plans/active/issues/ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md
"""

# Regex to find raw open todos (disk count) — same as regen's _UNCHECKED_RE
_RAW_OPEN_RE = re.compile(r"^\s*-\s+\[ \]\s+(.+)$")
# Frontmatter delimiter
_FM_DELIM = "---"
# Fenced code block
_FENCE_RE = re.compile(r"^\s*```")
# Leading tag-cluster prefix (e.g. "[BLOCKED]", "[DEFERRED]", "[OPERATOR]")
_LEADING_TAG_RE = re.compile(r"^\s*(?:\d+[a-z]?\.\s+)?(?:(?:\[[A-Z][A-Z_-]*\]|P[0-3]\.)\s*)+")
# Tags that mark intentional non-dispatch at the leading position
_INTENTIONAL_NONDISP_TAG_RE = re.compile(r"\[(?:BLOCKED|DEFERRED)\]")
# PERMANENT non-dispatchable markers (DEFERRED-BY-DESIGN / stretch) — mirrors the AO module
_PERMANENT_NONDISP_RE = re.compile(
    r"DEFERRED-BY-DESIGN\b"
    r"|_\(\s*[Ss]tretch"
    r"|\b[Ss]tretch,\s*optional\b"
    r"|\*\*[Ss]tretch\*\*"
)
# BLOCKED-* token (AO's specific list) — used by AO to classify non-dispatchable
_BLOCKED_TOKEN_RE = re.compile(
    r"BLOCKED-(CREDENTIALS|OPERATOR(-DECISION)?|BILLING|UPSTREAM-(OUTAGE|DESIGN)|PLAYWRIGHT|JURISDICTION)\b"
)
# Broader BLOCKED-<UPPERCASE-WORD> pattern: covers BLOCKED-PREREQUISITES and other non-AO tokens
# that plan authors use to declare intentional holds on the DESCRIPTION LINE.
# Requires an uppercase letter after the hyphen to exclude prose compounds like "BLOCKED-marker".
_BROAD_BLOCKED_IN_DESC_RE = re.compile(r"\bBLOCKED-[A-Z][A-Z0-9_-]*\b")


# ---------------------------------------------------------------------------
# Frontmatter parsing (minimal, stdlib-only)
# ---------------------------------------------------------------------------


def _parse_fm(text: str) -> dict[str, str]:
    """Return flat {key: value} for the leading YAML frontmatter block."""
    if not text.startswith("---"):
        return {}
    out: dict[str, str] = {}
    for line in text.splitlines()[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if m:
            val = re.sub(r"\s+#.*$", "", m.group(2)).strip().strip("'\"")
            out[m.group(1)] = val
    return out


def _is_ao_dispatched(fm: dict[str, str]) -> bool:
    """True if this doc is AO-dispatched (mirrors regen's _plan_contributes_briefs gate)."""
    vm = fm.get("assigned_vm", "").lower().strip()
    if vm not in ("planning",):
        return False
    status = fm.get("status", "").lower().strip()
    if status in ("draft", "superseded", "complete", "cancelled", "resolved"):
        return False
    scope = fm.get("execution_scope", "").lower().strip()
    if scope == "local-only":
        return False
    return True


# ---------------------------------------------------------------------------
# AO parser import (with stubbing)
# ---------------------------------------------------------------------------


def _make_stub(name: str, **attrs: object) -> types.ModuleType:
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


def _load_ao_parser(ao_dir: Path) -> types.ModuleType | None:
    """Load _parse_open_todos / _is_non_dispatchable from agent-orchestrator.

    Injects minimal stubs for the AO package's internal imports so the pure-Python
    parser functions can execute without pydantic / UTL / etc. being installed.
    Returns None and logs a warning if the AO directory is not found.
    """
    regen_src = ao_dir / "server" / "regen_backlog_from_plan.py"
    if not regen_src.is_file():
        logger.warning(
            "AO parser not found at %s — dispatchability check skipped (AO not checked out?)",
            regen_src,
        )
        return None

    # Build stub modules for every AO-internal import the regen module needs at module level.
    # None of the stubbed names are used by _parse_open_todos / _is_non_dispatchable.
    sentinel = object()
    server_pkg = _make_stub(
        "server",
        __path__=[str(ao_dir / "server")],
        __package__="server",
    )
    config_stub = _make_stub(
        "server.config",
        get_config=lambda: types.SimpleNamespace(
            tuning=types.SimpleNamespace(pm_repo_path=None),
            plan_regen_interval_seconds=600,
        ),
        REPO_ROOT=ao_dir,
    )

    stub_map: dict[str, types.ModuleType] = {
        "server": server_pkg,
        "server.config": config_stub,
        "server.role_registry": _make_stub("server.role_registry"),
        "server.backlog": _make_stub(
            "server.backlog",
            Backlog=sentinel,
            BacklogTask=sentinel,
            load_backlog=None,
            save_backlog=None,
        ),
        "server.model_tier": _make_stub(
            "server.model_tier",
            EFFORT_LADDER=[],
            LARGE_PLAN_TODO_THRESHOLD=100,
        ),
        "server.models": _make_stub("server.models", ModelTier=sentinel),
        "server.ruling_task_brief": _make_stub(
            "server.ruling_task_brief",
            ORIGINAL_TODO_TEXT_MARKER="",
        ),
    }

    spec = importlib.util.spec_from_file_location(
        "server.regen_backlog_from_plan",
        regen_src,
    )
    if spec is None or spec.loader is None:
        logger.warning("Could not create spec for %s", regen_src)
        return None
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "server"  # type: ignore[assignment]

    # Must pre-register the module in sys.modules BEFORE exec_module so that
    # @dataclass can resolve cls.__module__ (dataclasses.py:_is_type looks up
    # sys.modules[cls.__module__].__dict__ — returns None if not yet registered).
    stub_map["server.regen_backlog_from_plan"] = mod  # type: ignore[assignment]
    saved: dict[str, types.ModuleType | None] = {name: sys.modules.get(name) for name in stub_map}  # type: ignore[assignment]
    try:
        sys.modules.update(stub_map)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod
    except Exception as exc:
        logger.warning("Failed to load AO parser from %s: %s", regen_src, exc)
        return None
    finally:
        for name, old_val in saved.items():
            if old_val is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old_val


# ---------------------------------------------------------------------------
# Per-doc counting
# ---------------------------------------------------------------------------


@dataclass
class TodoEntry:
    description: str
    is_non_dispatchable: bool
    is_declared: bool


@dataclass
class DocResult:
    path: Path
    disk_open: int
    dispatchable: int
    undeclared_todos: list[str] = field(default_factory=list)

    @property
    def delta(self) -> int:
        return self.disk_open - self.dispatchable

    @property
    def is_zero_dispatchable(self) -> bool:
        return self.disk_open > 0 and self.dispatchable == 0


def _is_todo_declared(description: str, continuation: str) -> bool:
    """True if a non-dispatchable todo has an explicit intentional marker on its FIRST LINE.

    A todo that is non-dispatchable ONLY because its continuation block mentions a BLOCKED-*
    token (not the description line) is classified as undeclared — likely accidental.
    """
    # Permanent markers in description → declared (DEFERRED-BY-DESIGN, stretch, etc.)
    if _PERMANENT_NONDISP_RE.search(description):
        return True
    # [BLOCKED] or [DEFERRED] tag in leading tag cluster of description → declared
    prefix_m = _LEADING_TAG_RE.match(description)
    if prefix_m and _INTENTIONAL_NONDISP_TAG_RE.search(prefix_m.group()):
        return True
    # Any BLOCKED-<UPPERCASE> token in the DESCRIPTION LINE → declared.
    # Uses the broad pattern (not just AO's specific token list) so that BLOCKED-PREREQUISITES
    # and similar non-AO tokens are recognised.  Requires uppercase after the hyphen so that
    # prose compounds like "BLOCKED-marker" (lowercase 'm') don't falsely suppress a real bug.
    if _BROAD_BLOCKED_IN_DESC_RE.search(description):
        return True
    # Non-dispatchable only through continuation block text → undeclared
    return False


def _count_doc(
    path: Path,
    parse_open_todos_fn: object,
    is_non_dispatchable_fn: object,
) -> DocResult:
    """Count disk-open vs dispatchable todos for one doc."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return DocResult(path=path, disk_open=0, dispatchable=0)

    lines = text.splitlines()
    # Dispatchable count from regen's oracle
    dispatchable = len(cast("list[tuple[str, object]]", cast(object, parse_open_todos_fn)(path)))  # type: ignore[call-arg]

    # Disk open count: raw `- [ ]` scan (mirrors regen's own loop, frontmatter/fence aware)
    in_fm = False
    fm_opened = False
    in_code = False
    disk_open = 0
    undeclared: list[str] = []
    todo_boundary_re = re.compile(r"^\s*-\s+\[|^\s*#")
    strikethrough_re = re.compile(r"^\s*~~.*~~\s*$")

    for i, raw_line in enumerate(lines):
        line = raw_line.rstrip()
        # Frontmatter
        if i == 0 and line.strip() == _FM_DELIM:
            in_fm = True
            fm_opened = True
            continue
        if in_fm:
            if line.strip() == _FM_DELIM and fm_opened:
                in_fm = False
            continue
        # Code fence
        if _FENCE_RE.match(line):
            in_code = not in_code
            continue
        if in_code:
            continue
        # Strikethrough
        if strikethrough_re.match(line):
            continue

        m = _RAW_OPEN_RE.match(line)
        if not m:
            continue
        description = m.group(1).strip()
        if not description:
            continue

        disk_open += 1

        # Gather continuation block for dispatchability check
        continuation_lines: list[str] = []
        peek = i + 1
        while peek < len(lines) and not todo_boundary_re.match(lines[peek]):
            continuation_lines.append(lines[peek])
            peek += 1
        todo_block = "\n".join([description, *continuation_lines])

        # Check if this todo is non-dispatchable (would be filtered by the oracle)
        if cast(bool, cast(object, is_non_dispatchable_fn)(todo_block)):  # type: ignore[call-arg]
            if not _is_todo_declared(description, "\n".join(continuation_lines)):
                undeclared.append(description[:120])

    return DocResult(path=path, disk_open=disk_open, dispatchable=dispatchable, undeclared_todos=undeclared)


# ---------------------------------------------------------------------------
# Corpus scan
# ---------------------------------------------------------------------------


def scan_corpus(pm_root: Path, ao_dir: Path) -> tuple[list[DocResult], bool]:
    """Scan all AO-dispatched docs. Returns (results, ao_available).

    ao_available=False means AO was not found and dispatchable counts are 0 (skipped).
    """
    parser_mod = _load_ao_parser(ao_dir)
    ao_available = parser_mod is not None

    if ao_available:
        parse_open_todos_fn = getattr(parser_mod, "_parse_open_todos")
        is_non_dispatchable_fn = getattr(parser_mod, "_is_non_dispatchable")
    else:
        # Fallback: can't measure dispatchable, skip (return disk counts only)
        parse_open_todos_fn = lambda p: []  # noqa: E731
        is_non_dispatchable_fn = lambda b: False  # noqa: E731

    results: list[DocResult] = []
    for subdir in [pm_root / "plans" / "active", pm_root / "plans" / "active" / "issues"]:
        if not subdir.is_dir():
            continue
        for p in sorted(subdir.glob("*.md")):
            if p.name.startswith("_") or p.name == "INDEX.md":
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            fm = _parse_fm(text)
            if not _is_ao_dispatched(fm):
                continue
            results.append(_count_doc(p, parse_open_todos_fn, is_non_dispatchable_fn))

    return results, ao_available


# ---------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------


def _read_baseline(baseline_path: Path) -> dict[str, int]:
    if not baseline_path.is_file():
        return {"total_non_dispatchable": 0, "zero_dispatchable_docs": 0}
    try:
        raw = yaml.safe_load(baseline_path.read_text())
    except Exception:
        return {"total_non_dispatchable": 0, "zero_dispatchable_docs": 0}
    if not isinstance(raw, dict):
        return {"total_non_dispatchable": 0, "zero_dispatchable_docs": 0}
    return {
        "total_non_dispatchable": int(raw.get("total_non_dispatchable", 0)),
        "zero_dispatchable_docs": int(raw.get("zero_dispatchable_docs", 0)),
        "undeclared_non_dispatchable": int(raw.get("undeclared_non_dispatchable", 0)),
    }


def _write_baseline(baseline_path: Path, results: list[DocResult]) -> None:
    total_nd = sum(r.delta for r in results)
    zero_docs = sum(1 for r in results if r.is_zero_dispatchable)
    undeclared = sum(len(r.undeclared_todos) for r in results)
    content = _BASELINE_HEADER + yaml.dump(
        {
            "total_non_dispatchable": total_nd,
            "zero_dispatchable_docs": zero_docs,
            "undeclared_non_dispatchable": undeclared,
        },
        default_flow_style=False,
    )
    baseline_path.write_text(content, encoding="utf-8")
    print(
        f"Baseline written: total_non_dispatchable={total_nd}, "
        f"zero_dispatchable_docs={zero_docs}, undeclared_non_dispatchable={undeclared}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    default_pm = Path(__file__).resolve().parents[2]
    default_ws = default_pm.parent
    ap.add_argument("--workspace-root", type=Path, default=default_ws)
    ap.add_argument("--pm-root", type=Path, default=None, help="PM repo root (default: inferred)")
    ap.add_argument("--ao-root", type=Path, default=None, help="AO repo root (default: inferred)")
    ap.add_argument("--baseline-path", type=Path, default=DEFAULT_BASELINE_PATH)
    ap.add_argument("--baseline-write", action="store_true", help="Write new baseline and exit 0")
    ap.add_argument("--report", action="store_true", help="Emit per-doc report to stdout")
    ns = ap.parse_args()

    ws = cast(Path, ns.workspace_root).resolve()
    pm_root: Path = (cast(Path, ns.pm_root) or ws / "unified-trading-pm").resolve()
    ao_dir: Path = (cast(Path, ns.ao_root) or ws / "agent-orchestrator").resolve()

    if not (pm_root / "plans" / "active").is_dir():
        print(f"error: plans/active not found under {pm_root}", file=sys.stderr)
        return 2

    results, ao_available = scan_corpus(pm_root, ao_dir)

    if not ao_available:
        print(
            "WARNING: agent-orchestrator not found — dispatchability delta not measurable. "
            "Gate skipped (exit 0).",
            file=sys.stderr,
        )
        return 0

    if ns.baseline_write:
        _write_baseline(ns.baseline_path, results)
        return 0

    total_nd = sum(r.delta for r in results)
    zero_docs = [r for r in results if r.is_zero_dispatchable]
    docs_with_undeclared = [r for r in results if r.undeclared_todos]

    if ns.report or docs_with_undeclared or True:
        print("AO todo dispatchability delta report")
        print(f"  AO-dispatched docs scanned: {len(results)}")
        print(f"  Total non-dispatchable open todos: {total_nd}")
        print(f"  Zero-dispatchable docs: {len(zero_docs)}")
        if zero_docs:
            print("  ZERO-DISPATCHABLE (active AO plan that AO will never touch):")
            for r in zero_docs:
                rel = r.path.relative_to(pm_root) if r.path.is_relative_to(pm_root) else r.path
                print(f"    [{r.disk_open} open, 0 dispatchable] {rel}")
        if docs_with_undeclared:
            print("  UNDECLARED non-dispatchable todos (fail gate — must be fixed):")
            for r in docs_with_undeclared:
                rel = r.path.relative_to(pm_root) if r.path.is_relative_to(pm_root) else r.path
                print(f"    {rel}:")
                for td in r.undeclared_todos:
                    print(f"      - {td[:100]}")
        if ns.report:
            print("\n  Per-doc delta (only docs with delta > 0):")
            for r in sorted(results, key=lambda x: -x.delta):
                if r.delta == 0:
                    continue
                rel = r.path.relative_to(pm_root) if r.path.is_relative_to(pm_root) else r.path
                print(f"    delta={r.delta:>3} (disk={r.disk_open}, disp={r.dispatchable}) {rel}")

    # --- Gates 0/1/2: all ratchets (read baseline once) ---
    baseline = _read_baseline(ns.baseline_path)
    baseline_nd = baseline["total_non_dispatchable"]
    baseline_zero = baseline["zero_dispatchable_docs"]
    baseline_undeclared = baseline.get("undeclared_non_dispatchable", 0)
    total_undeclared = sum(len(r.undeclared_todos) for r in docs_with_undeclared)
    failed = False

    # --- Gate 0: undeclared non-dispatchable ratchet ---
    if total_undeclared > baseline_undeclared:
        print(
            f"\nFAIL (ratchet): undeclared non-dispatchable todos {total_undeclared} > baseline {baseline_undeclared}.",
            file=sys.stderr,
        )
        print(
            "  A non-dispatchable todo has no BLOCKED-*/[BLOCKED]/[DEFERRED] declaration on its first line.",
            file=sys.stderr,
        )
        print(
            "  Fix: add the marker to the todo's first line, or run --baseline-write after a genuine corpus shrink.",
            file=sys.stderr,
        )
        failed = True

    if total_nd > baseline_nd:
        print(
            f"\nFAIL (ratchet): total non-dispatchable todos {total_nd} > baseline {baseline_nd}.",
            file=sys.stderr,
        )
        print(
            "  New non-dispatchable todo(s) added. Fix them or mark as declared before committing.",
            file=sys.stderr,
        )
        print(
            f"  Re-baseline after fixing: python3 {Path(__file__).name} --baseline-write",
            file=sys.stderr,
        )
        failed = True

    # --- Gate 2: zero-dispatchable docs ratchet ---
    if len(zero_docs) > baseline_zero:
        print(
            f"\nFAIL (ratchet): zero-dispatchable AO docs {len(zero_docs)} > baseline {baseline_zero}.",
            file=sys.stderr,
        )
        print(
            "  An active `assigned_vm: planning` doc has disk_open > 0 but dispatchable == 0.",
            file=sys.stderr,
        )
        print(
            "  Fix: reclassify the doc (assigned_vm: NA), archive it, or fix the blocked todos.",
            file=sys.stderr,
        )
        failed = True

    if not failed:
        print(
            f"PASS: total_non_dispatchable={total_nd}/{baseline_nd} "
            f"zero_dispatchable_docs={len(zero_docs)}/{baseline_zero} "
            f"undeclared={total_undeclared}/{baseline_undeclared}",
        )
    return 1 if failed else 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    raise SystemExit(main())
