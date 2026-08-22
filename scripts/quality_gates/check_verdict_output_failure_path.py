#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""QG meta-assertion: a job's `verdict` output consumed by another job must survive the failure path.

WHY (2026-08-10 incident — plans/active/issues/ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10.md):
``ldr-docs-gate.yml``'s gate step ran under GitHub Actions' default shell
(``bash --noprofile --norc -e -o pipefail``). Its own ``set -uo pipefail`` does NOT clear the inherited
``-e``, so when the checker it ran exited non-zero, the step died AT the ``OUT="$(...)"`` capture — before
the ``{ echo "verdict=..."; ... } >> "$GITHUB_OUTPUT"`` block ever ran. Every downstream job gated on
``needs.<job>.outputs.verdict`` (notify / escalate / RESOLVED-bookend) then silently skipped: the gate was
RED and the channel was SILENT for 10+ hours before a manual sweep caught it.

This is a general trap, not a one-off: **any** job that publishes a `verdict` output another job consumes
via `needs.<job>.outputs.verdict` must guarantee that output gets written even when the step's own checker
command fails — via `set +e` before the capture, a `trap ... EXIT` handler, or a dedicated `if: always()`
step — never bare inline in a step that can die under the shell's inherited `-e` before reaching the write.
Only literal `verdict` outputs are in scope (the exact failure class this incident produced); this is
deliberately narrower than "every job output" to avoid false positives on unrelated outputs.

Usage::

    python scripts/quality_gates/check_verdict_output_failure_path.py

Exit codes:
  0 — every verdict-output job consumed elsewhere has a failure-path guarantee (or none exist)
  1 — a verdict-output job consumed elsewhere has NO failure-path guarantee
  2 — argument / IO error

SSOT: plans/active/issues/ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10.md,
codex/04-architecture/ci-alerting.md (dedup/read-back contract this closes a gap upstream of).
"""

from __future__ import annotations

import glob
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_STEP_OUTPUT_VERDICT_RE = re.compile(r"steps\.([\w.-]+)\.outputs\.verdict")
_ALWAYS_RE = re.compile(r"\balways\(\s*\)")
_SET_PLUS_E_RE = re.compile(r"(^|[;&\n])\s*set\s+(?:[a-zA-Z]*\+e[a-zA-Z]*|\+o\s+errexit)\b", re.MULTILINE)
_TRAP_EXIT_RE = re.compile(r"\btrap\b[^\n]*\bEXIT\b")
_VERDICT_WRITE_RE = re.compile(r"\bverdict\s*=")


@dataclass(frozen=True)
class Finding:
    file: str
    job_id: str
    step_id: str
    output_key: str
    reason: str


def _needs_verdict_ref(raw: str, job_id: str) -> bool:
    return re.search(rf"needs\.{re.escape(job_id)}\.outputs\.verdict\b", raw) is not None


def _find_step(job: dict[str, Any], step_id: str) -> dict[str, Any] | None:
    for step in job.get("steps") or []:
        if isinstance(step, dict) and step.get("id") == step_id:
            return step
    return None


def _has_failure_path_guarantee(job: dict[str, Any], step_id: str) -> tuple[bool, str]:
    step = _find_step(job, step_id)
    if step is None:
        # Can't locate the producing step (e.g. a composite `uses:` action, or a
        # malformed `id:`) — nothing to statically verify, don't false-flag.
        return True, "producing step not a scannable run: block (skipped, cannot verify)"

    step_if = str(step.get("if") or "")
    if _ALWAYS_RE.search(step_if):
        return True, "producing step itself has if: always()"

    run_text = str(step.get("run") or "")
    if _SET_PLUS_E_RE.search(run_text):
        return True, "script disables inherited -e via set +e before the write"
    if _TRAP_EXIT_RE.search(run_text):
        return True, "script uses a trap ... EXIT handler"

    # A separate step in the same job, guarded if: always(), that itself writes verdict=.
    for other in job.get("steps") or []:
        if not isinstance(other, dict) or other is step:
            continue
        other_if = str(other.get("if") or "")
        other_run = str(other.get("run") or "")
        if _ALWAYS_RE.search(other_if) and _VERDICT_WRITE_RE.search(other_run):
            return True, "a separate if: always() step writes verdict="

    return False, (
        "no failure-path guarantee found — the producing step can die under GH Actions' inherited "
        "-e before writing verdict= to GITHUB_OUTPUT; add `set +e` before the capture, a `trap ... EXIT` "
        "handler, or a dedicated `if: always()` step that writes verdict="
    )


def _scan_workflow(path: Path) -> list[Finding]:
    raw = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        # Unparseable workflows are check_workflow_yaml_valid.py's concern, not this
        # checker's — skip rather than double-report.
        return []
    if not isinstance(data, dict):
        return []
    jobs = data.get("jobs")
    if not isinstance(jobs, dict):
        return []

    findings: list[Finding] = []
    for job_id, job in jobs.items():
        if not isinstance(job, dict):
            continue
        outputs = job.get("outputs")
        if not isinstance(outputs, dict):
            continue
        for out_key, expr in outputs.items():
            if out_key != "verdict" or not isinstance(expr, str):
                continue
            m = _STEP_OUTPUT_VERDICT_RE.search(expr)
            if not m:
                continue
            step_id = m.group(1)
            if not _needs_verdict_ref(raw, job_id):
                continue  # published but never consumed elsewhere — not the incident's shape
            ok, reason = _has_failure_path_guarantee(job, step_id)
            if not ok:
                findings.append(
                    Finding(file=str(path), job_id=job_id, step_id=step_id, output_key=out_key, reason=reason)
                )
    return findings


def main() -> int:
    workflows = sorted(glob.glob(".github/workflows/*.yml") + glob.glob(".github/workflows/*.yaml"))
    if not workflows:
        print("✅ verdict-output-failure-path: no .github/workflows to check")
        return 0

    all_findings: list[Finding] = []
    for wf in workflows:
        all_findings.extend(_scan_workflow(Path(wf)))

    if all_findings:
        print(
            "❌ verdict-output-failure-path: a job's `verdict` output is consumed by another job "
            "(needs.<job>.outputs.verdict) but has no guarantee it survives the producing step's failure path:"
        )
        for f in all_findings:
            print(f"   {f.file}: job '{f.job_id}' step '{f.step_id}' output '{f.output_key}' — {f.reason}")
        print(
            "   See plans/active/issues/ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10.md — "
            "a monitor whose failure path cannot page is a coverage hole, not just a bug."
        )
        return 1

    print(f"✅ verdict-output-failure-path: {len(workflows)} workflow(s) checked, no unguarded verdict producers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
