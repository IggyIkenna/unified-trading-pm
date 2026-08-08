#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Shrinking-ratchet gate: disk-vs-backlog todo dispatchability delta, per AO-dispatched doc.

SSOT: plans/active/issues/ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md

``regen_backlog_from_plan.py``'s ``_parse_open_todos`` deliberately drops a todo whose
continuation block asserts a live ``BLOCKED-<token>`` state or a permanent
stretch/deferred marker — correct on its own terms (a worker can't work something waiting
on a human), but nothing previously reported the delta: a plan can render 5 open
checkboxes while the backlog only ever sees 3, and no gate, hygiene sweep, or dashboard
said so. Four separate incidents (2026-07-28, 07-29, 08-02, 08-08) each found a DIFFERENT
trigger shape for the same underlying problem and "fixed" it by widening the exclusion
regex — that has not converged, because the actual defect is that exclusion goes
UNREPORTED, not that the regex is too narrow. **This gate does not touch the regex.** It
is a pure visibility + ratchet mechanism: growth in the invisible-exclusion count is a
loud, blocking signal; a genuine new exclusion (an operator adds a real BLOCKED-CREDENTIALS
todo) is fine and gets absorbed via ``--update-baseline``, same convention as
``check_na_corpus_ratchet.py``.

Never a re-implemented regex: the actual classification comes from
``agent-orchestrator/server/regen_backlog_from_plan.py``'s REAL ``_parse_open_todos`` /
``_is_non_dispatchable`` — the parser IS the oracle. Since that module needs
agent-orchestrator's own dependencies (pydantic / pydantic-settings / unified_trading_library
config plumbing) that this lean, pure-stdlib PM repo does not install, this script does NOT
import it directly. Instead it subprocess-invokes
``agent-orchestrator/scripts/orchestrator/dump_plan_dispatch_visibility.py`` (the "parser
import path" half of the fix, living in agent-orchestrator) via THAT repo's own ``.venv``,
and applies the ratchet/baseline arithmetic here in pure stdlib.

Degrades to a NO-OP when the sibling ``agent-orchestrator`` checkout or its ``.venv`` is
absent (e.g. a single-repo CI runner) — same convention as ``check_repo_docs_ssot.py`` /
``detect_template_drift.py`` (see ``quality-gates.sh``'s ``WORKSPACE_ROOT``-gated post-gate
block): this is the LOCAL / full-workspace gate, not something CI can enforce standalone.

Tracks two numbers, both shrinking ratchets:
  * ``max_excluded_todos``       — total todos, across every ``assigned_vm: planning`` doc,
                                    that ``_parse_open_todos`` excludes (raw_open - dispatchable
                                    summed corpus-wide).
  * ``max_zero_dispatchable_docs`` — count of currently-in-force (``status`` in
                                    ``{active, open}``) ``assigned_vm: planning`` docs whose
                                    dispatchable count is ZERO despite having open todos on
                                    disk — the acute case: an apparently-tracked plan AO will
                                    never touch at all.

Usage: check_ao_dispatch_visibility_gate.py [--workspace-root DIR] [--update-baseline] [--quiet] [--report]
  --update-baseline   regenerate the baseline YAML from the CURRENT corpus state. Run this
                       ONLY after triaging/fixing genuine accidental exclusions (see --report) —
                       never to silence a run that just found the invisible set grew. If the
                       new numbers are HIGHER than the old ones a loud warning prints (still
                       written — a deliberate raise is a real, visible signal, not a block).
  --report            print the full per-doc excluded-todo breakdown, with a heuristic
                       declared-intentional vs likely-accidental split (negation-phrasing
                       near the marker, e.g. "do NOT mark this BLOCKED-X", is the tell the
                       current regex can't see — see the module docstring's incident list).
Exit 0 = current excluded/zero-dispatchable counts <= baseline on both axes (or the AO
sibling/venv is absent — degrades to a no-op). Exit 1 = either axis grew beyond baseline.
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
BASELINE = Path(__file__).resolve().parent / "ao_dispatch_visibility_baseline.yaml"

_BASELINE_HEADER = """\
# Shrinking-ratchet baseline for the disk-vs-backlog todo dispatchability delta
# (check_ao_dispatch_visibility_gate.py).
#
# Tracks two numbers over the LIVE `assigned_vm: planning` population (plans/active/*.md +
# plans/active/issues/*.md), computed by agent-orchestrator's REAL `_parse_open_todos` /
# `_is_non_dispatchable` (never a re-implemented regex). SHRINKING ratchet, same convention
# as na_corpus_baseline.yaml: a run that finds the CURRENT corpus WORSE than this baseline on
# EITHER axis fails. The goal is not "zero exclusions" -- a genuine BLOCKED-CREDENTIALS todo
# SHOULD be excluded from the backlog -- the goal is that invisible exclusion cannot grow
# unattended: a new one is fine when it's genuinely deliberate, but it must be reviewed
# (--report) before --update-baseline absorbs it.
#
# NEVER hand-raise these numbers to silence a run that just found the invisible set grew --
# only --update-baseline after reviewing the new exclusions via --report. A deliberate raise
# (a real batch of new BLOCKED-* todos) is a real signal -- make it visible with why in the
# commit message, same convention as any other ratchet exception in this corpus.
#
# Do NOT "fix" a growth by widening agent-orchestrator's _BLOCKED_TOKEN_RE /
# _STALE_MARKER_PREFIX_RE / _STALE_MARKER_SUFFIX_RE again -- four widenings (2026-07-28,
# 07-29, 08-02, 08-08) already failed to converge on that approach. This ratchet is the fix:
# make growth in the invisible set a hard, visible signal instead of trying to perfectly
# regex-classify intent.
"""

# Heuristic-only (see --report docstring): a negation cue within this many characters
# BEFORE a BLOCKED-<token> match that the real parser's own _STALE_MARKER_PREFIX_RE does
# NOT recognise (that one only recognises past-tense resolution language: "was" / "no
# longer" / "retagged from" / "previously" -- see regen_backlog_from_plan.py). A todo
# whose own prose argues AGAINST the marker applying (the sports Betfair trigger shape:
# "Do NOT mark this BLOCKED-CREDENTIALS") reads as a likely accidental exclusion to a
# human, but is invisible to the parser's prefix check because it isn't PAST-tense
# resolution language, it's a present-tense instruction. This is a REPORTING aid only --
# it does not change what the gate blocks on, and it is not a stealth fifth regex widening
# (nothing here feeds back into the real parser).
_NEGATION_CUE_RE = re.compile(
    r"\b(?:do\s+not|don't|never|should\s+not|must\s+not)\b\s*(?:mark|tag|treat|flag|use)?",
    re.IGNORECASE,
)
_NEGATION_LOOKBACK_CHARS = 40


def _find_ao_dump_script(workspace_root: Path) -> tuple[Path, Path] | None:
    """Locate agent-orchestrator's venv python + the dump script, or None if absent.

    Both must exist: the sibling repo checkout AND its synced .venv (agent-orchestrator's
    OWN dependencies -- pydantic/pydantic-settings/unified_trading_library -- are what
    regen_backlog_from_plan.py needs; this lean PM repo does not install them).
    """
    ao_root = workspace_root / "agent-orchestrator"
    dump_script = ao_root / "scripts" / "orchestrator" / "dump_plan_dispatch_visibility.py"
    venv_python = ao_root / ".venv" / "bin" / "python3"
    if not dump_script.is_file() or not venv_python.is_file():
        return None
    return venv_python, dump_script


def _run_dump(venv_python: Path, dump_script: Path, pm_root: Path) -> list[dict[str, object]]:
    proc = subprocess.run(
        [str(venv_python), str(dump_script), "--pm-root", str(pm_root)],
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    result = json.loads(proc.stdout)
    if not isinstance(result, list):
        raise ValueError(f"dump_plan_dispatch_visibility.py returned non-list JSON: {type(result)}")
    return result


def _current_counts(docs: list[dict[str, object]]) -> tuple[int, int]:
    """(total_excluded_todos, zero_dispatchable_doc_count) over the live corpus."""
    total_excluded = sum(int(d["excluded"]) for d in docs)  # pyright: ignore[reportArgumentType]
    zero_dispatchable = sum(
        1
        for d in docs
        if d.get("status") in ("active", "open") and int(d["dispatchable"]) == 0 and int(d["raw_open"]) > 0  # pyright: ignore[reportArgumentType]
    )
    return total_excluded, zero_dispatchable


def _looks_accidental(description: str) -> bool:
    """Heuristic-only flag — see the module-level ``_NEGATION_CUE_RE`` docstring above."""
    m = _NEGATION_CUE_RE.search(description)
    if not m:
        return False
    # Only a hit is meaningful; the lookback window bounds false matches on a negation
    # cue that's unrelated prose far from any BLOCKED-* marker in a long continuation block.
    return bool(re.search(r"BLOCKED-[A-Z-]+", description[m.end() : m.end() + _NEGATION_LOOKBACK_CHARS]))


def _print_report(docs: list[dict[str, object]]) -> None:
    excluded_docs = [d for d in docs if d["excluded"]]
    print(f"\n{len(excluded_docs)} doc(s) carry at least one excluded (invisible-to-backlog) todo:\n")
    accidental_total = 0
    declared_total = 0
    for d in excluded_docs:
        print(f"  {d['path']}  (assigned_vm={d['assigned_vm']} status={d['status']})")
        for todo in d["excluded_todos"]:  # pyright: ignore[reportGeneralTypeIssues]
            desc = todo["description"]  # pyright: ignore[reportIndexIssue]
            suspect = _looks_accidental(desc)
            if suspect:
                accidental_total += 1
                label = "LIKELY-ACCIDENTAL (negation cue near marker)"
            else:
                declared_total += 1
                label = "declared"
            print(f"    [{label}] {desc[:140]}")
    print(f"\nSplit: {declared_total} declared-by-parser-logic, {accidental_total} likely-accidental (heuristic).")
    print(
        "Likely-accidental entries are a REPORTING aid, not a hard gate -- read the doc, fix the phrasing\n"
        "(or file a follow-up todo) the same way the sports Betfair example was fixed, then\n"
        "--update-baseline once the fleet-visible count reflects the fix."
    )


def _load_baseline() -> dict[str, object]:
    if not BASELINE.is_file():
        return {}
    return yaml.safe_load(BASELINE.read_text()) or {}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace-root", type=Path, default=PM.parent, help="Workspace root (default: PM parent)")
    ap.add_argument("--update-baseline", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--report", action="store_true", help="print the full per-doc excluded-todo breakdown")
    args = ap.parse_args(argv)

    located = _find_ao_dump_script(args.workspace_root.resolve())
    if located is None:
        if not args.quiet:
            print(
                "check_ao_dispatch_visibility_gate: sibling agent-orchestrator checkout or its "
                ".venv is absent under this workspace root -- degrading to a no-op (this is the "
                "LOCAL / full-workspace gate; CI with a single-repo checkout can't run it). "
                "Run `cd agent-orchestrator && uv sync` to enable it locally."
            )
        return 0
    venv_python, dump_script = located

    try:
        docs = _run_dump(venv_python, dump_script, PM)
    except (subprocess.SubprocessError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"❌ check_ao_dispatch_visibility_gate: dump script failed: {exc}", file=sys.stderr)
        return 1

    excluded, zero_dispatchable = _current_counts(docs)
    baseline = _load_baseline()
    max_excluded = baseline.get("max_excluded_todos")
    max_zero = baseline.get("max_zero_dispatchable_docs")

    if args.report:
        _print_report(docs)

    if args.update_baseline:
        warnings = []
        if isinstance(max_excluded, int) and excluded > max_excluded:
            warnings.append(f"max_excluded_todos RAISED {max_excluded} -> {excluded}")
        if isinstance(max_zero, int) and zero_dispatchable > max_zero:
            warnings.append(f"max_zero_dispatchable_docs RAISED {max_zero} -> {zero_dispatchable}")
        BASELINE.write_text(
            _BASELINE_HEADER
            + f"max_excluded_todos: {excluded}\n"
            + f"max_zero_dispatchable_docs: {zero_dispatchable}\n"
            + f'last_updated: "{datetime.now(UTC).date().isoformat()}"\n'
        )
        print(
            f"ao_dispatch_visibility_baseline.yaml regenerated: "
            f"max_excluded_todos={excluded}, max_zero_dispatchable_docs={zero_dispatchable}"
        )
        for w in warnings:
            print(f"⚠️  {w} -- verify this is a reviewed, justified raise, not a silenced failure", file=sys.stderr)
        return 0

    problems = []
    if isinstance(max_excluded, int) and excluded > max_excluded:
        problems.append(f"excluded (invisible-to-backlog) todo count grew: {excluded} > baseline {max_excluded}")
    if isinstance(max_zero, int) and zero_dispatchable > max_zero:
        problems.append(f"zero-dispatchable doc count grew: {zero_dispatchable} > baseline {max_zero}")

    if problems:
        print(
            "❌ check_ao_dispatch_visibility_gate: invisible-exclusion backlog grew beyond baseline:",
            file=sys.stderr,
        )
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print(
            "  Remedy: re-run with --report to see which docs/todos are new, fix genuine accidental\n"
            "  exclusions (reword the todo -- see the sports Betfair precedent), then re-run this check.\n"
            "  If this growth is a reviewed, justified exception (real new BLOCKED-* todos), re-run with\n"
            "  --update-baseline and explain why in the commit message -- never hand-edit the YAML.",
            file=sys.stderr,
        )
        return 1

    if not args.quiet:
        print(
            f"✅ check_ao_dispatch_visibility_gate: {excluded} excluded todos / {zero_dispatchable} "
            f"zero-dispatchable docs (baseline: {max_excluded}/{max_zero})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
