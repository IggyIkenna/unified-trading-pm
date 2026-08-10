#!/usr/bin/env python3
# Epic: observability_master
# Lifecycle: permanent
# Delete-when: NA
"""Driver: assert_version_coherence.py --json -> verdict_store CAS writes (one Firestore doc per
repo, collection ``version_coherence_verdicts``).

Wired into ``.github/workflows/version-coherence-check.yml`` (scheduled, every 30 min). Kept as a
real, importable, unit-testable module rather than an inline ``python3 -c`` block in the workflow
YAML (SSOT: `/codex/06-coding-standards/script-homes.md`).

SSOT design: plans/active/monitoring_control_plane_master_2026_06_10.md (version-coherence panel),
operator decision 2026-07-27 (build the real Firestore verdict-store generalisation, not a
faithful-port workaround). The deployment-api panel READS these docs — it never re-derives
VERSION_SPLIT / VESTIGIAL_SCALAR_DRIFT / DEP_FLOOR_UNSATISFIABLE itself (the do-NOT-reimplement
trap: CLAUDE.md § "Manifest version-surface semantics").
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

# Python only adds the script's own dir to sys.path for file-based runs, not for stdin/module runs
# (same rationale check_ci_status_bot_only.py documents) — make the sibling import explicit.
sys.path.insert(0, str(Path(__file__).parent))
import verdict_store


def run_checker(*, warn_only: bool = True, python_executable: str = sys.executable) -> dict[str, dict[str, object]]:
    """Invoke ``assert_version_coherence.py --json`` as a subprocess and parse its per-repo
    verdicts. A subprocess (not an import) so this driver never inherits the checker's argparse
    exit-code semantics or its (fleet-sized) ``gh api`` call graph at import time."""
    checker = Path(__file__).with_name("assert_version_coherence.py")
    args = [python_executable, str(checker), "--json"]
    if warn_only:
        args.append("--warn-only")
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode not in (0, 1):
        raise RuntimeError(
            f"assert_version_coherence.py --json exited {result.returncode} unexpectedly: {result.stderr}"
        )
    payload = json.loads(result.stdout)
    # Fail fast on a malformed/schema-drifted checker output rather than silently writing zero
    # verdicts (an empty-dict fallback here would mask a real bug in the checker's --json contract
    # as "no repos to report" — the exact trap the workspace's empty-fallback ban exists to catch).
    repos = payload.get("repos")
    if not isinstance(repos, dict):
        raise RuntimeError(f"assert_version_coherence.py --json emitted no 'repos' object: {result.stdout[:500]!r}")
    return repos


def write_verdicts(
    repos: dict[str, dict[str, object]],
    *,
    checked_at: str,
    project_id: str | None = None,
) -> tuple[int, int]:
    """CAS-write every repo's verdict doc. A single repo's write failure is logged and counted, not
    fatal — shard-level isolation (the same principle every per-repo loop in this workspace follows;
    one Firestore hiccup on one repo must never blank the other 24)."""
    written = 0
    errors = 0
    for repo, entry in sorted(repos.items()):
        verdict = str(entry.get("verdict", "OK"))
        reasons_raw = entry.get("reasons", [])  # noqa: qg-empty-fallback — "no reasons" is a real, meaningful state
        reasons = [str(r) for r in reasons_raw] if isinstance(reasons_raw, list) else []
        try:
            verdict_store.set_verdict(
                verdict_store.VERSION_COHERENCE_COLLECTION,
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
    repos = run_checker()
    written, errors = write_verdicts(repos, checked_at=checked_at, project_id=args.project_id)
    print(f"version-coherence verdict-store: wrote {written} doc(s), {errors} failure(s), checked_at={checked_at}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
