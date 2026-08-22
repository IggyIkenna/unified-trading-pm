#!/usr/bin/env python3
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
"""Driver: detect_template_drift.py --json -> verdict_store CAS writes (one Firestore doc per
repo, collection ``template_drift_verdicts``).

Wired into ``scripts/orchestrator/template-drift-daily-check.{sh,service,timer}`` (a daily systemd
timer on the `planning` orchestrator VM — NOT a GitHub Actions workflow: detect_template_drift.py
reads local sibling-repo files (``_qg_path(workspace_root, repo_name).read_text()``) with no
``gh api`` fallback, so it can only run where the full multi-repo workspace exists on disk, unlike
``assert_version_coherence.py`` / ``write_version_coherence_verdicts.py`` (this driver's sibling),
which does have a ``gh api`` fallback and so ships as a normal GH Actions workflow instead). Kept
as a real, importable, unit-testable module rather than an inline shell block (SSOT:
`/codex/06-coding-standards/script-homes.md`).

SSOT design: plans/active/monitoring_control_plane_master_2026_06_10.md (rollout-ratchet panel),
plans/active/issues/rollout_ratchet_panel_ui_only_mis_scoped_needs_backend_2026_08_17.md. The
deployment-api panel (a separate, not-yet-built follow-up) READS these docs — it never re-derives
the drift checks itself (the same do-NOT-reimplement discipline as the version-coherence panel).
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
    """Invoke ``detect_template_drift.py --json`` as a subprocess and parse its per-repo drift
    reports. A subprocess (not an import) so this driver never inherits the checker's argparse
    exit-code semantics or its (fleet-sized) per-repo file-read graph at import time."""
    checker = Path(__file__).parent.parent / "quality_gates" / "detect_template_drift.py"
    args = [python_executable, str(checker), "--json"]
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode not in (0, 1):
        raise RuntimeError(f"detect_template_drift.py --json exited {result.returncode} unexpectedly: {result.stderr}")
    payload = json.loads(result.stdout)
    # Fail fast on a malformed/schema-drifted checker output rather than silently writing zero
    # verdicts (an empty-list fallback here would mask a real bug in the checker's --json contract
    # as "no repos to report" — the exact trap the workspace's empty-fallback ban exists to catch).
    if not isinstance(payload, list):
        raise RuntimeError(f"detect_template_drift.py --json did not emit a JSON list: {result.stdout[:500]!r}")
    return payload


def derive_verdict(report: dict[str, object]) -> tuple[str, list[str]]:
    """One repo's drift report -> (verdict, reasons). Errors outrank warnings; a clean report has
    neither, matching the checker's own severity ordering (``run()``'s human-readable summary)."""
    items_raw = report.get("items", [])  # noqa: qg-empty-fallback — "no drift items" is a real, meaningful state
    items = items_raw if isinstance(items_raw, list) else []
    has_error = any(isinstance(item, dict) and item.get("severity") == "error" for item in items)
    reasons = [f"[{item.get('check', '?')}] {item.get('message', '')}" for item in items if isinstance(item, dict)]
    if has_error:
        return "ERROR", reasons
    if reasons:
        return "WARN", reasons
    return "CLEAN", reasons


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
                verdict_store.TEMPLATE_DRIFT_COLLECTION,
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
    print(f"template-drift verdict-store: wrote {written} doc(s), {errors} failure(s), checked_at={checked_at}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
