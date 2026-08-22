#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""check_qg_slice_completeness — machine-enforce the QG_SLICE "zero lost coverage" claim.

CI (python-quality-gates-v2.yml) runs the local gate as three parallel legs
(QG_SLICE = tests | typecheck | lint-codex). base-service.sh documents that the
slices "PARTITION the gate with ZERO overlap + ZERO lost coverage" — but until
2026-07-02 that was PROSE, not enforced: a slice-flag edit could silently drop a
phase from every CI leg while the local full run still executed it (local-green
would stop predicting v2-green in the worst direction: CI false-green).

This guard parses the slice case-block in base-service.sh and asserts the
partition property over the four phase-controlling flags:

    RUN_LINT / RUN_TESTS / (not SKIP_TYPECHECK) / _QG_RUN_CODEX

each must be ENABLED in EXACTLY ONE slice (zero overlap, zero loss), and the
slice set must be exactly {tests, typecheck, lint-codex} on BOTH sides
(base-service.sh case block AND the CI workflow matrix), so a slice added to one
side without the other fails here instead of silently no-op'ing.

Provenance: cicd_mvp_ldr_to_main_pipeline_2026_06_30 Phase-2 local<->CI parity;
the 2026-06-10 "typecheck leg silent no-op false green" incident is the class
this prevents (see the _qg_slice_done BUG FIX comment in base-service.sh).
"""

from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

PM_ROOT = Path(__file__).resolve().parents[2]
BASE_SERVICE = PM_ROOT / "scripts" / "quality-gates-base" / "base-service.sh"
# The reusable python-quality-gates-v2.yml moved to unified-trading-ci on 2026-08-06
# (shared_ci_workflow_repo_extraction_2026_08_06.md) — PM no longer hosts a local copy.
# Prefer the sibling checkout (fast, no network, what every local slot has); fall back to
# a live GitHub fetch of the public repo's main branch for environments without the
# sibling cloned (e.g. a GHA runner that only checks out the calling repo + dep_repos).
CI_WORKFLOW_SIBLING = PM_ROOT.parent / "unified-trading-ci" / ".github" / "workflows" / "python-quality-gates-v2.yml"
CI_WORKFLOW_RAW_URL = (
    "https://raw.githubusercontent.com/IggyIkenna/unified-trading-ci/main/.github/workflows/python-quality-gates-v2.yml"
)


def read_ci_workflow() -> str:
    if CI_WORKFLOW_SIBLING.is_file():
        return CI_WORKFLOW_SIBLING.read_text(encoding="utf-8")
    with urllib.request.urlopen(CI_WORKFLOW_RAW_URL, timeout=15) as resp:  # nosec B310 — hardcoded raw.githubusercontent.com https URL, not user input
        return resp.read().decode("utf-8")


EXPECTED_SLICES = {"tests", "typecheck", "lint-codex"}
# flag name -> the value that means "this phase RUNS"
PHASE_FLAGS = {
    "RUN_LINT": "true",
    "RUN_TESTS": "true",
    "SKIP_TYPECHECK": "false",  # inverted: false == typecheck runs
    "_QG_RUN_CODEX": "true",
}

_CASE_ARM = re.compile(
    r"^\s*(?P<slice>[a-z-]+)\)\s*"
    r"RUN_LINT=(?P<RUN_LINT>\w+);\s*"
    r"RUN_TESTS=(?P<RUN_TESTS>\w+);\s*"
    r"SKIP_TYPECHECK=(?P<SKIP_TYPECHECK>\w+);\s*"
    r"_QG_RUN_CODEX=(?P<_QG_RUN_CODEX>\w+)",
    re.MULTILINE,
)


def parse_slice_matrix(text: str) -> dict[str, dict[str, str]]:
    """slice -> {flag: value} parsed from the base-service.sh case block."""
    return {m.group("slice"): {f: m.group(f) for f in PHASE_FLAGS} for m in _CASE_ARM.finditer(text)}


def parse_ci_matrix(text: str) -> set[str]:
    """The slice list from the CI workflow's `slice: [a, b, c]` matrix line."""
    m = re.search(r"^\s*slice:\s*\[([^\]]+)\]", text, re.MULTILINE)
    if not m:
        return set()
    return {s.strip() for s in m.group(1).split(",") if s.strip()}


def main() -> int:
    failures: list[str] = []

    base_text = BASE_SERVICE.read_text(encoding="utf-8")
    matrix = parse_slice_matrix(base_text)
    if set(matrix) != EXPECTED_SLICES:
        failures.append(
            f"base-service.sh slice case-block parsed as {sorted(matrix)} — expected "
            f"{sorted(EXPECTED_SLICES)} (parser drift or a slice was added/renamed; "
            "update BOTH this guard and the CI workflow matrix together)"
        )
    else:
        for flag, run_value in PHASE_FLAGS.items():
            enabled_in = [s for s, flags in matrix.items() if flags[flag] == run_value]
            if len(enabled_in) != 1:
                failures.append(
                    f"phase flag {flag} is enabled in {enabled_in or 'NO slice'} — the "
                    "partition property requires EXACTLY ONE slice per phase (zero "
                    "overlap, zero lost CI coverage)"
                )

    # A5 (2026-07-17): the CI matrix runs TWO legs — `tests` plus a merged `checks` leg that
    # invokes the typecheck + lint-codex SELECTORS sequentially (one runner, one setup, one
    # fewer billed job minimum; measured fleet-wide: merged stays under the tests leg on every
    # slow repo). The base-service.sh selector partition is UNCHANGED, so completeness is now:
    #   (a) base selectors still partition all 4 phases (checked above),
    #   (b) CI matrix is exactly {tests, checks},
    #   (c) the workflow's checks leg literally invokes BOTH non-tests selectors — verified
    #       against the SELECTORS line so a selector dropped from the merged leg fails HERE
    #       instead of silently losing typecheck or lint-codex coverage fleet-wide.
    ci_text = read_ci_workflow()
    ci_slices = parse_ci_matrix(ci_text)
    expected_ci = {"tests", "checks"}
    if ci_slices != expected_ci:
        failures.append(
            f"CI workflow matrix slices {sorted(ci_slices)} != expected {sorted(expected_ci)} "
            "— a leg exists on one side only (silent coverage loss or a permanently-missing "
            "matrix job)"
        )
    if not re.search(r"^\s*SELECTORS=\(typecheck lint-codex\)", ci_text, re.MULTILINE):
        failures.append(
            "CI workflow's merged `checks` leg no longer invokes `SELECTORS=(typecheck "
            "lint-codex)` — the leg merge lost a selector (typecheck or lint-codex would "
            "silently stop running in CI)"
        )

    if failures:
        print("❌ qg-slice-completeness:", file=sys.stderr)
        for f in failures:
            print(f"   - {f}", file=sys.stderr)
        return 1
    print(
        "✅ qg-slice-completeness: 3 base selectors partition all 4 phases; CI matrix "
        "{tests, checks} with the checks leg invoking both merged selectors"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
