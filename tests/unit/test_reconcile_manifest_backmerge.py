"""Guard 2 — tests for the back-merge manifest reconciler.

Verifies the ``main → live-defi-rollout`` 3-way reconcile: CI-automation fields
resolve to main (``theirs``) and never conflict; LDR-side non-CI edits survive;
main-side non-CI additions arrive; a genuine non-CI divergence is reported as a
conflict (exit 2) so the human-PR escalation still fires.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "cicd" / "reconcile_manifest_backmerge.py"
_spec = importlib.util.spec_from_file_location("reconcile_manifest_backmerge", _MODULE_PATH)
assert _spec is not None and _spec.loader is not None
reconcile_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(reconcile_mod)


def _manifest(ci_status: str, *, desc: str = "base", staging_locked: bool = False) -> dict[str, object]:
    return {
        "title": "workspace",
        "repositories": {
            "alerting-service": {
                "ci_status": ci_status,
                "coverage_pct": 80,
                "description": desc,
            }
        },
        "staging_status": {"locked": staging_locked},
    }


def test_ci_status_drift_takes_main_no_conflict() -> None:
    base = _manifest("FEATURE_GREEN")
    ours = _manifest("FAILING")  # LDR stale snapshot
    theirs = _manifest("STAGING_GREEN")  # main authoritative (fresh)
    merged, conflicts = reconcile_mod.reconcile(base, ours, theirs)
    assert conflicts == []
    repos = merged["repositories"]
    assert isinstance(repos, dict)
    assert repos["alerting-service"]["ci_status"] == "STAGING_GREEN"  # main wins


def test_staging_status_drift_takes_main() -> None:
    base = _manifest("FEATURE_GREEN", staging_locked=False)
    ours = _manifest("FEATURE_GREEN", staging_locked=True)
    theirs = _manifest("FEATURE_GREEN", staging_locked=False)
    merged, conflicts = reconcile_mod.reconcile(base, ours, theirs)
    assert conflicts == []
    assert merged["staging_status"] == {"locked": False}  # main wins


def test_ldr_noncic_edit_preserved() -> None:
    base = _manifest("FEATURE_GREEN", desc="base")
    ours = _manifest("FAILING", desc="ldr-edited-description")  # LDR edited a non-CI field
    theirs = _manifest("STAGING_GREEN", desc="base")  # main only flipped ci_status
    merged, conflicts = reconcile_mod.reconcile(base, ours, theirs)
    assert conflicts == []
    repos = merged["repositories"]
    assert repos["alerting-service"]["description"] == "ldr-edited-description"  # LDR edit kept
    assert repos["alerting-service"]["ci_status"] == "STAGING_GREEN"  # main ci_status kept


def test_main_new_repo_arrives() -> None:
    base = _manifest("FEATURE_GREEN")
    ours = _manifest("FEATURE_GREEN")
    theirs = _manifest("STAGING_GREEN")
    theirs_repos = theirs["repositories"]
    assert isinstance(theirs_repos, dict)
    theirs_repos["new-service"] = {"ci_status": "FEATURE_GREEN", "description": "added on main"}
    merged, conflicts = reconcile_mod.reconcile(base, ours, theirs)
    assert conflicts == []
    repos = merged["repositories"]
    assert isinstance(repos, dict)
    assert "new-service" in repos  # main-side addition arrives in LDR


def test_genuine_noncic_conflict_reported() -> None:
    base = _manifest("FEATURE_GREEN", desc="base")
    ours = _manifest("FEATURE_GREEN", desc="ldr-edit")  # both changed description differently
    theirs = _manifest("FEATURE_GREEN", desc="main-edit")
    _merged, conflicts = reconcile_mod.reconcile(base, ours, theirs)
    assert conflicts == [("repositories", "alerting-service", "description")]


def test_main_function_writes_and_exits(tmp_path: Path) -> None:
    import json

    base_p = tmp_path / "base.json"
    ours_p = tmp_path / "ours.json"
    theirs_p = tmp_path / "theirs.json"
    out_p = tmp_path / "out.json"
    base_p.write_text(json.dumps(_manifest("FEATURE_GREEN")), encoding="utf-8")
    ours_p.write_text(json.dumps(_manifest("FAILING")), encoding="utf-8")
    theirs_p.write_text(json.dumps(_manifest("MAIN_GREEN")), encoding="utf-8")
    rc = reconcile_mod.main(
        ["--base", str(base_p), "--ours", str(ours_p), "--theirs", str(theirs_p), "--out", str(out_p)]
    )
    assert rc == 0
    written = json.loads(out_p.read_text(encoding="utf-8"))
    assert written["repositories"]["alerting-service"]["ci_status"] == "MAIN_GREEN"


def test_main_function_conflict_exit_2(tmp_path: Path) -> None:
    import json

    base_p = tmp_path / "base.json"
    ours_p = tmp_path / "ours.json"
    theirs_p = tmp_path / "theirs.json"
    out_p = tmp_path / "out.json"
    base_p.write_text(json.dumps(_manifest("FEATURE_GREEN", desc="base")), encoding="utf-8")
    ours_p.write_text(json.dumps(_manifest("FEATURE_GREEN", desc="ldr")), encoding="utf-8")
    theirs_p.write_text(json.dumps(_manifest("FEATURE_GREEN", desc="main")), encoding="utf-8")
    rc = reconcile_mod.main(
        ["--base", str(base_p), "--ours", str(ours_p), "--theirs", str(theirs_p), "--out", str(out_p)]
    )
    assert rc == 2
    assert not out_p.exists()  # no write on conflict
