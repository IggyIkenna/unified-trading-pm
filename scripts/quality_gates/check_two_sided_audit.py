#!/usr/bin/env python3
"""Phase 6B QG post-gate: two-sided prospectus vs codex audit (baselined ratchet).

Runs ``audit_prospectus_vs_codex.py``'s ``run_audit()`` directly and compares
each finding-category count against a committed baseline YAML.  NEW findings
(count > baseline) -> non-zero exit (gate FAIL).  Existing findings at or below
baseline -> exit 0.

Baseline categories tracked:
  - ``contradictions``    : venue-category contradictions (c)
  - ``orphan_docs``       : codex docs without enum entry (b)
  - ``legs_in_prose``     : legs-in-prose drift (d)

SSOT: plans/active/capability_wizard_and_manifest_2026_06_11.md section 6B parity quality gates.

Exit-code semantics: 0 = at/below baseline (green); 1 = regression (new findings); 2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import cast

import yaml

DEFAULT_BASELINE_PATH = Path(__file__).parent / "two_sided_audit_baseline.yaml"

_SCRIPT_DIR = Path(__file__).resolve().parent
_PM_ROOT = _SCRIPT_DIR.parent.parent
_OPENAPI_DIR = _PM_ROOT / "scripts" / "openapi"


def _load_baseline(path: Path) -> dict[str, int]:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {
        "contradictions": int(data.get("baseline_contradictions", 0)),
        "orphan_docs": int(data.get("baseline_orphan_docs", 0)),
        "legs_in_prose": int(data.get("baseline_legs_in_prose", 0)),
    }


def _write_baseline(path: Path, counts: dict[str, int]) -> None:
    data = {
        "rule": "two-sided-prospectus-codex-audit",
        "source": "capability_wizard_and_manifest_2026_06_11.md section 6B",
        "baseline_contradictions": counts["contradictions"],
        "baseline_orphan_docs": counts["orphan_docs"],
        "baseline_legs_in_prose": counts["legs_in_prose"],
    }
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def _run_audit() -> dict[str, int]:
    """Import and run the audit (no subprocess -- keeps the check fast + testable)."""
    if str(_OPENAPI_DIR) not in sys.path:
        sys.path.insert(0, str(_OPENAPI_DIR))

    os.environ.setdefault("CLOUD_PROVIDER", "local")
    os.environ.setdefault("CLOUD_MOCK_MODE", "true")
    os.environ.setdefault("DISABLE_AUTH", "true")
    os.environ.setdefault("MOCK_STATE_MODE", "deterministic")
    os.environ.setdefault("GCP_PROJECT_ID", "mock-project")
    os.environ.setdefault("PUBSUB_EMULATOR_HOST", "localhost:8085")
    os.environ.setdefault("STORAGE_EMULATOR_HOST", "http://localhost:4443")
    os.environ.setdefault("BIGQUERY_EMULATOR_HOST", "localhost:9050")
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "mock-project")
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("API_KEY", "mock-api-key-for-openapi-gen")

    from audit_prospectus_vs_codex import run_audit  # type: ignore[import-not-found]

    result = run_audit()
    return {
        "contradictions": len(cast(list, result["contradictions"])),
        "orphan_docs": len(cast(list, result["doc_without_enum"])),
        "legs_in_prose": len(cast(list, result["legs_in_prose_drift"])),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Two-sided prospectus vs codex audit (baselined ratchet gate)"
    )
    parser.add_argument(
        "--baseline-path",
        type=Path,
        default=DEFAULT_BASELINE_PATH,
        help="Path to the YAML baseline file (default: two_sided_audit_baseline.yaml)",
    )
    parser.add_argument(
        "--baseline-write",
        action="store_true",
        help="Write current counts as new baseline (used to re-baseline after intentional changes)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if ANY findings exist (ignores baseline)",
    )
    return parser.parse_args()


def main() -> int:
    ns = _parse_args()
    baseline_path: Path = cast(Path, ns.baseline_path)
    baseline_write: bool = cast(bool, ns.baseline_write)
    strict: bool = cast(bool, ns.strict)

    print("Running two-sided prospectus vs codex audit...")
    try:
        counts = _run_audit()
    except Exception as exc:  # pylint: disable=broad-except
        print(f"ERROR: audit failed -- {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2

    total = sum(counts.values())
    print(
        f"  (c) venue-category contradictions : {counts['contradictions']}\n"
        f"  (b) orphan codex docs             : {counts['orphan_docs']}\n"
        f"  (d) legs-in-prose drift           : {counts['legs_in_prose']}\n"
        f"  Total findings                    : {total}"
    )

    if baseline_write:
        _write_baseline(baseline_path, counts)
        print(f"Wrote baseline to {baseline_path}")
        return 0

    if strict:
        if total > 0:
            print(f"\nSTRICT: {total} finding(s) -- all categories must be zero.")
            return 1
        print("\nSTRICT: no findings.")
        return 0

    baseline = _load_baseline(baseline_path)

    regressions: list[str] = []
    for key, label in (
        ("contradictions", "venue-category contradictions"),
        ("orphan_docs", "orphan codex docs"),
        ("legs_in_prose", "legs-in-prose drift"),
    ):
        current = counts[key]
        base = baseline[key]
        if current > base:
            regressions.append(
                f"  {label}: {current} > baseline {base} (+{current - base} new)"
            )
        elif current < base:
            print(
                f"  improvement: {label}: {current} < baseline {base} -- "
                "re-baseline with --baseline-write to codify."
            )

    if regressions:
        print("\nNew audit findings (regression vs baseline):")
        for r in regressions:
            print(r)
        print(
            "\nTo resolve: fix the new findings, OR re-baseline with --baseline-write "
            "(only when findings are accepted debt)."
        )
        return 1

    print(
        f"\nTwo-sided audit at/below baseline (contradictions={baseline['contradictions']}, "
        f"orphan_docs={baseline['orphan_docs']}, legs_in_prose={baseline['legs_in_prose']})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
