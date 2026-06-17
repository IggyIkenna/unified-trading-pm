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


# ── Version-surface semver-max (2026-06-17 follow-up) ────────────────────────
# `versions.<repo>` + `repositories.<name>.version` are a MONOTONIC released-version
# cache (semver-agent only bumps up; "AHEAD is fine, only BEHIND is bad"). A
# both-bumped version scalar resolves to semver-max — never "take main" (would
# regress a repo whose LDR copy is ahead, the real 2026-06-17 jam), never escalate.


def test_versions_both_bumped_resolve_to_semver_max_ldr_higher() -> None:
    # The live jam: base 0.10.0, ours(LDR) 0.12.0, theirs(main) 0.11.0 → max 0.12.0.
    base = {"versions": {"unified-trading-library": "0.10.0"}}
    ours = {"versions": {"unified-trading-library": "0.12.0"}}
    theirs = {"versions": {"unified-trading-library": "0.11.0"}}
    merged, conflicts = reconcile_mod.reconcile(base, ours, theirs)
    assert conflicts == []
    assert merged["versions"]["unified-trading-library"] == "0.12.0"


def test_versions_both_bumped_main_higher() -> None:
    base = {"versions": {"x": "1.0.0"}}
    ours = {"versions": {"x": "1.1.0"}}
    theirs = {"versions": {"x": "1.3.0"}}
    merged, conflicts = reconcile_mod.reconcile(base, ours, theirs)
    assert conflicts == []
    assert merged["versions"]["x"] == "1.3.0"


def test_versions_only_theirs_changed_takes_main_pm_case() -> None:
    # PM: base==ours → existing 3-way takes theirs (main higher) → fixes the version-align gate.
    base = {"versions": {"unified-trading-pm": "1.2.128"}}
    ours = {"versions": {"unified-trading-pm": "1.2.128"}}
    theirs = {"versions": {"unified-trading-pm": "1.2.145"}}
    merged, conflicts = reconcile_mod.reconcile(base, ours, theirs)
    assert conflicts == []
    assert merged["versions"]["unified-trading-pm"] == "1.2.145"


def test_repo_display_version_both_bumped_semver_max() -> None:
    base = {"repositories": {"x": {"version": "0.5.0"}}}
    ours = {"repositories": {"x": {"version": "0.7.0"}}}
    theirs = {"repositories": {"x": {"version": "0.6.0"}}}
    merged, conflicts = reconcile_mod.reconcile(base, ours, theirs)
    assert conflicts == []
    assert merged["repositories"]["x"]["version"] == "0.7.0"


def test_ldr_only_versions_key_preserved() -> None:
    base = {"versions": {"a": "1.0.0"}}
    ours = {"versions": {"a": "1.0.0", "newrepo": "0.1.0"}}
    theirs = {"versions": {"a": "1.0.0"}}
    merged, conflicts = reconcile_mod.reconcile(base, ours, theirs)
    assert conflicts == []
    assert merged["versions"]["newrepo"] == "0.1.0"


def test_unparseable_version_both_changed_still_escalates() -> None:
    # Never guess on a non-semver value — fall through to genuine conflict.
    base = {"versions": {"x": "1.0.0"}}
    ours = {"versions": {"x": "abc"}}
    theirs = {"versions": {"x": "1.1.0"}}
    _merged, conflicts = reconcile_mod.reconcile(base, ours, theirs)
    assert ("versions", "x") in conflicts


def test_dep_edge_floors_both_changed_still_escalate() -> None:
    # Dep-edge range-pin floors are INTENTIONAL — must NOT auto-resolve (not a version field).
    base = {"repositories": {"x": {"dependencies": [{"name": "uac", "version": ">=0.1,<1.0"}]}}}
    ours = {"repositories": {"x": {"dependencies": [{"name": "uac", "version": ">=0.2,<1.0"}]}}}
    theirs = {"repositories": {"x": {"dependencies": [{"name": "uac", "version": ">=0.3,<1.0"}]}}}
    _merged, conflicts = reconcile_mod.reconcile(base, ours, theirs)
    assert ("repositories", "x", "dependencies") in conflicts


def test_version_helpers() -> None:
    assert reconcile_mod._semver_tuple("1.2.145") == (1, 2, 145)
    assert reconcile_mod._semver_tuple("0.12") == (0, 12, 0)
    assert reconcile_mod._semver_tuple("abc") is None
    assert reconcile_mod._semver_tuple(123) is None
    assert reconcile_mod._is_version_field(("versions", "utl")) is True
    assert reconcile_mod._is_version_field(("repositories", "utl", "version")) is True
    assert reconcile_mod._is_version_field(("repositories", "utl", "dependencies")) is False
    assert reconcile_mod._is_version_field(("versions",)) is False
