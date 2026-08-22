#!/usr/bin/env python3
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
"""Driver: verify_branch_protection_check_names.py --json -> verdict_store CAS writes (one
Firestore doc per repo, collection ``ruleset_drift_verdicts``).

Wired into ``.github/workflows/ruleset-drift-alert.yml`` (Mondays 06:00 UTC + workflow_dispatch),
ADDITIVE alongside that workflow's existing Slack-paging notify job (which stays — this only gives
deployment-api a persisted per-repo verdict to read instead of the workflow's run-only Slack
alert). ``verify_branch_protection_check_names.py`` reads via ``GH_TOKEN``/``gh api`` (no local
sibling-repo checkout needed) — unlike ``detect_template_drift.py`` /
``write_template_drift_verdicts.py``, this driver ships as a normal GH Actions job, mirroring
``write_version_coherence_verdicts.py``'s pattern exactly. Kept as a real, importable,
unit-testable module rather than an inline shell block (SSOT:
`/codex/06-coding-standards/script-homes.md`).

SSOT design: plans/active/monitoring_control_plane_master_2026_06_10.md (rollout-ratchet panel),
plans/active/issues/rollout_ratchet_panel_ui_only_mis_scoped_needs_backend_2026_08_17.md. The
deployment-api route (a separate, not-yet-built follow-up todo on that issue doc) READS this
collection — it never re-derives the ruleset-drift check itself (the same do-NOT-reimplement
discipline as the version-coherence panel).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

# Python only adds the script's own dir to sys.path for file-based runs, not for stdin/module runs
# (same rationale check_ci_status_bot_only.py / write_version_coherence_verdicts.py document) —
# make the sibling import explicit.
sys.path.insert(0, str(Path(__file__).parent))
import verdict_store


def run_checker(*, python_executable: str = sys.executable) -> list[dict[str, object]]:
    """Invoke ``verify_branch_protection_check_names.py --json`` as a subprocess and parse its
    per-repo ruleset-drift reports. A subprocess (not an import) so this driver never inherits the
    checker's argparse exit-code semantics or its (fleet-sized) ``gh api`` call graph at import
    time."""
    checker = Path(__file__).parent.parent / "repo-management" / "verify_branch_protection_check_names.py"
    args = [python_executable, str(checker), "--json"]
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode not in (0, 1):
        raise RuntimeError(
            f"verify_branch_protection_check_names.py --json exited {result.returncode} unexpectedly: {result.stderr}"
        )
    payload = json.loads(result.stdout)
    # Fail fast on a malformed/schema-drifted checker output rather than silently writing zero
    # verdicts (an empty-list fallback here would mask a real bug in the checker's --json contract
    # as "no repos to report" — the exact trap the workspace's empty-fallback ban exists to catch).
    if not isinstance(payload, list):
        raise RuntimeError(
            f"verify_branch_protection_check_names.py --json did not emit a JSON list: {result.stdout[:500]!r}"
        )
    return payload


def derive_verdict(report: dict[str, object]) -> tuple[str, list[str]]:
    """One repo's ruleset-drift report -> (verdict, reasons). Mirrors the checker's own drift
    ordering (default-branch drift called out first, since it's the fleet-wide assertion)."""
    reasons: list[str] = []
    if not report.get("default_branch_ok", True):
        reasons.append(f"default_branch={report.get('default_branch')!r} != 'main'")
    if not report.get("main_ok", True):
        reasons.append(f"main required-contexts drifted: {report.get('main_required')!r}")
    if not report.get("staging_ok", True):
        reasons.append(f"staging required-contexts drifted: {report.get('staging_required')!r}")
    verdict = "DRIFT" if report.get("drift") else "CLEAN"
    return verdict, reasons


def write_verdicts(
    reports: list[dict[str, object]],
    *,
    checked_at: str,
    project_id: str | None = None,
) -> tuple[int, int]:
    """CAS-write every repo's verdict doc. A single repo's write failure is logged and counted, not
    fatal — shard-level isolation (one Firestore hiccup on one repo must never blank the others)."""
    written = 0
    errors = 0
    for report in sorted(reports, key=lambda r: str(r.get("repo", ""))):
        repo = str(report.get("repo", ""))
        if not repo:
            continue
        verdict, reasons = derive_verdict(report)
        try:
            verdict_store.set_verdict(
                verdict_store.RULESET_DRIFT_COLLECTION,
                repo,
                verdict,
                reasons=reasons,
                checked_at=checked_at,
                project_id=project_id,
            )
            written += 1
        except Exception as err:  # noqa: broad-except — shard-level isolation: one repo's Firestore
            # write failure is logged and counted, not fatal — must never blank the other repos
            print(f"  FAILED to write verdict for {repo}: {type(err).__name__}: {err}", file=sys.stderr)
            errors += 1
    return written, errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-id", default=None)
    args = ap.parse_args()
    checked_at = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    reports = run_checker()
    written, errors = write_verdicts(reports, checked_at=checked_at, project_id=args.project_id)
    print(f"ruleset-drift verdict-store: wrote {written} doc(s), {errors} failure(s), checked_at={checked_at}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
