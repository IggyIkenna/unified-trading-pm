#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""AO dispatch-visibility gate — per-AO-dispatched-doc disk-vs-backlog open-todo
delta, baselined ratchet.

SSOT: ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md.
`_parse_open_todos` (agent-orchestrator/server/regen_backlog_from_plan.py)
deliberately excludes a todo whose continuation block asserts a live
BLOCKED-<token>/DEFERRED-BY-DESIGN/stretch marker — correct on its own terms, but
nothing reported the delta: a plan renders a live `- [ ]`, the inventory counts it,
the operator sees tracked work, and AO never dispatches it. MEASURED 2026-08-08: 47
of 551 open todos across 37 `assigned_vm: planning` docs silently dropped, 14 of
those docs reduced to ZERO dispatchable todos.

Delegates the actual parse to agent-orchestrator's `server.dispatch_visibility_report`
(a thin reporting wrapper added alongside this gate — imports the REAL
`_parse_open_todos`/`_plan_contributes_briefs`, no parser change) via subprocess,
run under agent-orchestrator's OWN venv — this repo's environment does not carry
agent-orchestrator's dependencies (pydantic et al.), so a direct import would fail
here. Same "the parser IS the oracle, never a re-implemented regex" reasoning as
count_operator_blocking_todos.py's docstring, just crossing the repo boundary via a
subprocess call instead of a copy-pasted regex.

Two ratcheted axes (ao_dispatch_visibility_baseline.yaml), same shrinking-ratchet
convention as na_corpus_baseline.yaml / repo_docs_ssot_baseline.yaml:
  - max_accidental_exclusions: excluded todos whose marker does NOT declare itself
    (does not open its own line) — the bug class this gate exists to catch. Goal is
    zero; the baseline seeds the CURRENT measured count so pre-existing debt doesn't
    fail every run, only NEW accidental exclusions do.
  - max_zero_dispatchable_docs: assigned_vm:planning docs with open todos on disk
    but ZERO dispatchable ones — the acute "active plan AO will never touch at all"
    case, reported as its own louder finding per the issue's ask.

A DECLARED exclusion (a live marker that DOES open its own line — the deliberate,
correctly-authored hold) never counts against either axis; it is the parser working
exactly as intended.

Usage: check_ao_dispatch_visibility_gate.py [--workspace-root DIR] [--vm-id ID]
                                             [--json] [--update-baseline] [--quiet]
Exit 0 = at-or-below baseline on both axes, OR the sibling agent-orchestrator
         repo/venv is unavailable (degrades to a no-op — same convention as the
         other workspace-wide PM gates; CI without sibling clones is unaffected).
Exit 1 = either axis grew beyond baseline.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

PM = Path(__file__).resolve().parents[2]
BASELINE = Path(__file__).resolve().parent / "ao_dispatch_visibility_baseline.yaml"

_BASELINE_HEADER = """\
# Shrinking-ratchet baseline for the AO dispatch-visibility gate
# (check_ao_dispatch_visibility_gate.py).
#
# See ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md for the
# full incident history (four prior _STALE_MARKER_*_RE widenings that did not
# converge). Two tracked axes:
#   max_accidental_exclusions  -- excluded todos whose marker does not declare itself
#     (does not open its own line). This is the regex-widening bug class; goal is
#     zero, baseline seeds current debt so it doesn't fail every run.
#   max_zero_dispatchable_docs -- assigned_vm:planning docs with open todos on disk
#     but zero reach the backlog (an active plan AO never touches at all).
#
# NEVER hand-raise these numbers to silence a run that just found new drift -- only
# --update-baseline after fixing or filing (issue-doc todo) the newly-found
# accidental exclusions. A genuine spike is a real signal -- make it visible in the
# commit message, same convention as every other ratchet in this corpus.
"""


def _ao_repo(workspace_root: Path) -> Path:
    return workspace_root / "agent-orchestrator"


def _ao_python(workspace_root: Path) -> Path | None:
    candidate = _ao_repo(workspace_root) / ".venv" / "bin" / "python3"
    return candidate if candidate.is_file() else None


def _run_report(workspace_root: Path, vm_id: str) -> list[dict[str, object]] | None:
    """Returns None (never raises) when the sibling repo/venv/module isn't available
    — the caller degrades that to a no-op, mirroring check_repo_docs_ssot.py's own
    "CI without siblings is unaffected" convention."""
    ao_repo = _ao_repo(workspace_root)
    ao_python = _ao_python(workspace_root)
    if ao_python is None or not (ao_repo / "server" / "dispatch_visibility_report.py").is_file():
        return None
    proc = subprocess.run(
        [str(ao_python), "-m", "server.dispatch_visibility_report", "--pm-path", str(PM), "--vm-id", vm_id, "--json"],
        capture_output=True,
        text=True,
        cwd=ao_repo,
        check=False,
    )
    if proc.returncode != 0:
        print(
            f"check_ao_dispatch_visibility_gate: report subprocess failed (exit {proc.returncode}):\n{proc.stderr}",
            file=sys.stderr,
        )
        return None
    result: list[dict[str, object]] = json.loads(proc.stdout)
    # Fail LOUDLY on a sibling checkout predating the `ineffective` field rather than
    # defaulting it to zero: a silent zero would report "no ineffective declarations"
    # for a corpus nobody actually measured, which is the same silent-false-negative
    # class this whole gate exists to eliminate. No compat shim — say what's wrong.
    for entry in result:
        if "ineffective" not in entry:
            print(
                "check_ao_dispatch_visibility_gate: the sibling agent-orchestrator checkout predates the\n"
                "  `ineffective` finding (added 2026-08-09, server/dispatch_visibility_report.py). Pull it —\n"
                "  refusing to report a measurement this checkout cannot make.",
                file=sys.stderr,
            )
            return None
    return result


def _summarize(reports: list[dict[str, object]]) -> dict[str, int]:
    accidental = 0
    declared = 0
    zero_dispatchable = 0
    ineffective = 0
    for r in reports:
        excluded = r["excluded"]
        assert isinstance(excluded, list)
        if r["disk_open"] > 0 and r["backlog_open"] == 0:  # type: ignore[operator]
            zero_dispatchable += 1
        for e in excluded:
            if e["declared"]:
                declared += 1
            else:
                accidental += 1
        ineffective_list = r["ineffective"]
        assert isinstance(ineffective_list, list)
        ineffective += len(ineffective_list)
    return {
        "docs": len(reports),
        "accidental_exclusions": accidental,
        "declared_exclusions": declared,
        "zero_dispatchable_docs": zero_dispatchable,
        "ineffective_declarations": ineffective,
    }


def _load_baseline() -> dict[str, object]:
    if not BASELINE.is_file():
        return {}
    return yaml.safe_load(BASELINE.read_text()) or {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AO dispatch-visibility gate (disk-vs-backlog todo delta).")
    parser.add_argument("--workspace-root", type=Path, default=PM.parent, help="Workspace root (default: PM parent)")
    parser.add_argument("--vm-id", default="planning", help="VM id to scope ingestion to (default: planning).")
    parser.add_argument("--json", action="store_true", help="Emit the summary + full per-doc report as JSON.")
    parser.add_argument("--update-baseline", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    workspace_root: Path = args.workspace_root.resolve()
    reports = _run_report(workspace_root, args.vm_id)
    if reports is None:
        if not args.quiet:
            print(
                "check_ao_dispatch_visibility_gate: agent-orchestrator repo/.venv not found under "
                f"{workspace_root} -- skipping (no-op; CI without sibling clones degrades the same way)"
            )
        return 0

    summary = _summarize(reports)

    if args.json:
        print(json.dumps({"summary": summary, "docs": reports}))
        return 0

    baseline = _load_baseline()
    max_accidental = baseline.get("max_accidental_exclusions")
    max_zero = baseline.get("max_zero_dispatchable_docs")
    max_ineffective = baseline.get("max_ineffective_declarations")

    if args.update_baseline:
        warnings = []
        if isinstance(max_accidental, int) and summary["accidental_exclusions"] > max_accidental:
            warnings.append(f"max_accidental_exclusions RAISED {max_accidental} -> {summary['accidental_exclusions']}")
        if isinstance(max_zero, int) and summary["zero_dispatchable_docs"] > max_zero:
            warnings.append(f"max_zero_dispatchable_docs RAISED {max_zero} -> {summary['zero_dispatchable_docs']}")
        if isinstance(max_ineffective, int) and summary["ineffective_declarations"] > max_ineffective:
            warnings.append(
                f"max_ineffective_declarations RAISED {max_ineffective} -> {summary['ineffective_declarations']}"
            )
        BASELINE.write_text(
            _BASELINE_HEADER
            + f"max_accidental_exclusions: {summary['accidental_exclusions']}\n"
            + f"max_zero_dispatchable_docs: {summary['zero_dispatchable_docs']}\n"
            + f"max_ineffective_declarations: {summary['ineffective_declarations']}\n"
            + f'last_updated: "{datetime.now(UTC).date().isoformat()}"\n'
        )
        print(
            "ao_dispatch_visibility_baseline.yaml regenerated: "
            f"max_accidental_exclusions={summary['accidental_exclusions']} "
            f"max_zero_dispatchable_docs={summary['zero_dispatchable_docs']} "
            f"max_ineffective_declarations={summary['ineffective_declarations']}"
        )
        for w in warnings:
            print(f"WARNING: {w} -- verify this is a reviewed, justified raise, not silenced", file=sys.stderr)
        return 0

    problems = []
    if isinstance(max_accidental, int) and summary["accidental_exclusions"] > max_accidental:
        problems.append(
            f"accidental (undeclared) exclusions grew: {summary['accidental_exclusions']} > baseline {max_accidental}"
        )
    if isinstance(max_zero, int) and summary["zero_dispatchable_docs"] > max_zero:
        problems.append(f"zero-dispatchable docs grew: {summary['zero_dispatchable_docs']} > baseline {max_zero}")
    if isinstance(max_ineffective, int) and summary["ineffective_declarations"] > max_ineffective:
        problems.append(
            f"ineffective declarations grew: {summary['ineffective_declarations']} > baseline {max_ineffective} "
            "(a todo declares BLOCKED-<TOKEN> in a token the dispatcher does not know, so it DISPATCHES "
            "while reading as held)"
        )

    if problems:
        print("check_ao_dispatch_visibility_gate: FAILED", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print(
            "  Remedy: re-run with --json to see the doc/description list. For each newly-accidental\n"
            "  exclusion, either DECLARE it (put the BLOCKED-<token>/DEFERRED-BY-DESIGN/stretch marker at\n"
            "  the start of its own line) or rewrite the todo so it no longer trips the marker. If this is\n"
            "  a reviewed, justified exception, re-run with --update-baseline and explain why in the commit\n"
            "  message -- never hand-edit the YAML.",
            file=sys.stderr,
        )
        return 1

    if not args.quiet:
        print(
            f"check_ao_dispatch_visibility_gate: {summary['docs']} AO-dispatched docs, "
            f"{summary['accidental_exclusions']} accidental exclusions (baseline {max_accidental}), "
            f"{summary['zero_dispatchable_docs']} zero-dispatchable docs (baseline {max_zero}), "
            f"{summary['ineffective_declarations']} ineffective declarations (baseline {max_ineffective})"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
