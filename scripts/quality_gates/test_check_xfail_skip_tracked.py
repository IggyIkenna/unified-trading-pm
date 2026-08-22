# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_xfail_skip_tracked.py (QG STEP 5.107 service / 5.102 library).

The rule: every ``pytest.xfail`` / unconditional ``@pytest.mark.skip`` reason
must cite a tracked plan/issue slug — an xfail with a good reason and no
remediation todo is indistinguishable, six months later, from coverage that was
never written (operator finding 2026-08-08). ``@pytest.mark.skipif`` (has a
condition) and reason-bearing ``pytest.skip("<reason>")`` calls (environmental
gating) are exempt by design; a zero-justification ``pytest.skip()`` is not.

Run via pytest from a venv that has pyyaml installed (the workspace
.venv-workspace satisfies this), or via the workspace-root pytest invocation
that base-service.sh wires up. Pure-Python — no GCS/AWS/network.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from check_xfail_skip_tracked import (  # type: ignore[import-not-found]
    _TRACKED_SLUG_RE,
    BaselineEntry,
    Finding,
    _cites_tracking,
    _iter_repo_test_files,
    _resolve_scopes,
    _scan_file,
    load_baseline,
    main,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _write(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


# ── Slug predicate ───────────────────────────────────────────────────────────


def test_tracked_slug_predicate() -> None:
    """The predicate accepts dated slugs, doc paths, and plans/issues paths."""

    assert _cites_tracking("tracked in plans/active/issues/foo_2026_07_20.md")
    assert _cites_tracking("tracked in issues/foo_2026_07_20.md")
    assert _cites_tracking("see codex/04-architecture/solana-defi-coverage.md")
    assert _cites_tracking("restore at tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01")
    assert _cites_tracking("tracked in defi_consolidated_closeout_2026_07_18.md Track 1")
    assert _cites_tracking("deferred to predictions_master.md")
    assert _cites_tracking("uac@502ef57e widened _ID_FORM_CHECKED_ASSET_GROUPS ... 2026_07_20.md")


def test_tracked_slug_predicate_rejects_bare_prose() -> None:
    """A good-sounding reason with NO tracking reference must NOT pass."""

    assert not _cites_tracking("Cassette stubs not yet recorded — future providers")
    assert not _cites_tracking("Cleanup deferred to a future false-positive-guard plan")
    assert not _cites_tracking("Pre-existing UTL import cascade error; tracking as a follow-up")
    assert not _cites_tracking("requires live API key")
    assert not _cites_tracking(None)
    assert not _cites_tracking("")


def test_tracked_slug_regex_shape() -> None:
    assert _TRACKED_SLUG_RE.pattern  # non-empty, importable


# ── Baseline loading ─────────────────────────────────────────────────────────


def test_load_baseline_real_workspace_baseline() -> None:
    """The real workspace baseline must parse cleanly + be all pending_removal."""

    here = Path(__file__).resolve().parent
    real = here / "xfail_skip_tracked_baseline.yaml"
    if not real.is_file():  # pragma: no cover — defensive
        pytest.skip("real baseline not yet shipped")
    baseline, default_successor = load_baseline()
    assert isinstance(baseline, dict)
    assert all(e.status == "pending_removal" for e in baseline.values())
    assert default_successor  # non-empty
    for key in baseline:
        assert len(key) == 4  # (repo, file, kind, line)


# ── Single-file scanning: xfail ──────────────────────────────────────────────


def test_scan_xfail_without_slug_is_flagged(tmp_path: Path) -> None:
    src = _write(
        tmp_path / "tests" / "test_x.py",
        'import pytest\n\n@pytest.mark.xfail(reason="Known drift — fix later")\ndef test_x():\n    assert True\n',
    )
    findings = _scan_file(src)
    assert len(findings) == 1
    assert findings[0].kind == "xfail"
    assert findings[0].line == 3


def test_scan_xfail_with_slug_not_flagged(tmp_path: Path) -> None:
    src = _write(
        tmp_path / "tests" / "test_x.py",
        "import pytest\n\n"
        '@pytest.mark.xfail(reason="tracked in plans/active/issues/foo_2026_07_20.md")\n'
        "def test_x():\n    assert True\n",
    )
    assert _scan_file(src) == []


def test_scan_xfail_slug_in_reason_comment_not_flagged(tmp_path: Path) -> None:
    """A slug in the same-line ``# reason:`` comment satisfies the rule."""

    src = _write(
        tmp_path / "tests" / "test_x.py",
        "import pytest\n\n"
        "# reason: restore at tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01\n"
        "@pytest.mark.xfail(strict=False)\ndef test_x():\n    assert True\n",
    )
    assert _scan_file(src) == []


def test_scan_pytest_xfail_call_flagged(tmp_path: Path) -> None:
    src = _write(
        tmp_path / "tests" / "test_x.py",
        'import pytest\n\ndef test_x():\n    pytest.xfail("may be expected, no tracking")\n',
    )
    findings = _scan_file(src)
    assert len(findings) == 1 and findings[0].kind == "xfail"


# ── Single-file scanning: skip ───────────────────────────────────────────────


def test_scan_unconditional_skip_without_slug_flagged(tmp_path: Path) -> None:
    src = _write(
        tmp_path / "tests" / "test_x.py",
        'import pytest\n\n@pytest.mark.skip(reason="deferred work")\ndef test_x():\n    assert True\n',
    )
    findings = _scan_file(src)
    assert len(findings) == 1 and findings[0].kind == "skip"


def test_scan_unconditional_skip_bare_flagged(tmp_path: Path) -> None:
    src = _write(
        tmp_path / "tests" / "test_x.py",
        "import pytest\n\n@pytest.mark.skip\ndef test_x():\n    assert True\n",
    )
    findings = _scan_file(src)
    assert len(findings) == 1 and findings[0].kind == "skip"


def test_scan_unconditional_skip_with_slug_not_flagged(tmp_path: Path) -> None:
    src = _write(
        tmp_path / "tests" / "test_x.py",
        'import pytest\n\n@pytest.mark.skip(reason="restore at foo_2026_08_01")\ndef test_x():\n    assert True\n',
    )
    assert _scan_file(src) == []


def test_scan_skipif_never_flagged(tmp_path: Path) -> None:
    """skipif carries a condition — environment-gated, exempt by design."""

    src = _write(
        tmp_path / "tests" / "test_x.py",
        "import pytest\n\n"
        '@pytest.mark.skipif(not HAS_KEY, reason="requires live API key")\ndef test_x():\n    assert True\n',
    )
    assert _scan_file(src) == []


def test_scan_reason_bearing_pytest_skip_call_not_flagged(tmp_path: Path) -> None:
    src = _write(
        tmp_path / "tests" / "test_x.py",
        'import pytest\n\ndef test_x():\n    pytest.skip("Live network call — run manually")\n',
    )
    assert _scan_file(src) == []


def test_scan_bare_pytest_skip_call_flagged(tmp_path: Path) -> None:
    src = _write(
        tmp_path / "tests" / "test_x.py",
        "import pytest\n\ndef test_x():\n    pytest.skip()\n",
    )
    findings = _scan_file(src)
    assert len(findings) == 1 and findings[0].kind == "skip_call"


def test_scan_skip_reason_via_module_constant(tmp_path: Path) -> None:
    """A reason held in a module-level constant that cites a slug must pass."""

    src = _write(
        tmp_path / "tests" / "test_x.py",
        "import pytest\n\n"
        '_REASON = "tracked in plans/active/issues/foo_2026_05_14.md"\n'
        "@pytest.mark.skip(reason=_REASON)\ndef test_x():\n    assert True\n",
    )
    assert _scan_file(src) == []


# ── Single-file scanning: clean / unparseable ────────────────────────────────


def test_scan_clean_file_no_findings(tmp_path: Path) -> None:
    src = _write(
        tmp_path / "tests" / "test_x.py",
        'import pytest\n\ndef test_x():\n    assert pytest.mark.skipif(True, reason="x")\n',
    )
    assert _scan_file(src) == []


def test_scan_handles_unparseable_file(tmp_path: Path) -> None:
    src = _write(tmp_path / "tests" / "broken.py", "def f(:\n    pass\n")
    assert _scan_file(src) == []


# ── File walker ──────────────────────────────────────────────────────────────


def test_iter_repo_test_files_scans_tests_excludes_scripts(tmp_path: Path) -> None:
    test_file = _write(tmp_path / "tests" / "unit" / "test_x.py", "import pytest\n")
    tests_helper = _write(tmp_path / "tests" / "helper.py", "import pytest\n")
    src_noise = _write(tmp_path / "mypkg" / "helper.py", "x = 1\n")
    scripts_noise = _write(tmp_path / "scripts" / "tool_test.py", "import pytest\n")
    found = set(_iter_repo_test_files(tmp_path))
    assert test_file in found
    assert tests_helper in found  # any .py under tests/ is scanned
    assert src_noise not in found  # not under tests/ and not test-named
    assert scripts_noise not in found  # scripts/ excluded from strict checks


def test_iter_repo_test_files_excludes_stale_clones(tmp_path: Path) -> None:
    real = _write(tmp_path / "tests" / "test_x.py", "import pytest\n")
    stale = _write(
        tmp_path / "mypkg.stale-pre-history-rewrite-20260805T112618Z" / "tests" / "test_old.py",
        "import pytest\n",
    )
    found = set(_iter_repo_test_files(tmp_path))
    assert real in found
    assert stale not in found


# ── Scope resolution ─────────────────────────────────────────────────────────


def test_resolve_scopes_scope_only(tmp_path: Path) -> None:
    (tmp_path / "myrepo").mkdir()
    assert _resolve_scopes(tmp_path, "myrepo") == [tmp_path / "myrepo"]


def test_resolve_scopes_missing_scope_returns_empty(tmp_path: Path) -> None:
    assert _resolve_scopes(tmp_path, "no_such_repo") == []


def test_resolve_scopes_workspace_wide_excludes_hidden_and_stale(tmp_path: Path) -> None:
    (tmp_path / "repo_a").mkdir()
    (tmp_path / ".venv").mkdir()
    (tmp_path / "repo_b.stale-pre-history-rewrite-20260805T112618Z").mkdir()
    names = {d.name for d in _resolve_scopes(tmp_path, None)}
    assert "repo_a" in names
    assert ".venv" not in names
    assert not any("stale-pre-history-rewrite" in n for n in names)


# ── main() end-to-end ────────────────────────────────────────────────────────


def _seed_baseline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, entries_yaml: str) -> None:
    body = 'default_successor: "cite a tracked slug"\nentries:\n' + textwrap.indent(textwrap.dedent(entries_yaml), "  ")
    f = _write(tmp_path / "_baseline.yaml", body)
    monkeypatch.setattr("check_xfail_skip_tracked._baseline_path", lambda: f)


def test_main_new_untracked_xfail_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _seed_baseline(monkeypatch, tmp_path, "[]\n")
    repo = tmp_path / "fakerepo"
    _write(repo / "tests" / "test_x.py", 'import pytest\n\n@pytest.mark.xfail(reason="no slug")\ndef t():\n    pass\n')
    assert main(["--workspace-root", str(tmp_path), "--scope", "fakerepo"]) == 1


def test_main_baselined_violation_passes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = tmp_path / "fakerepo"
    _write(repo / "tests" / "test_x.py", 'import pytest\n\n@pytest.mark.xfail(reason="no slug")\ndef t():\n    pass\n')
    _seed_baseline(
        monkeypatch,
        tmp_path,
        """
        - repo: fakerepo
          file: tests/test_x.py
          kind: xfail
          line: 3
          status: pending_removal
          successor: "cite a tracked slug"
        """,
    )
    assert main(["--workspace-root", str(tmp_path), "--scope", "fakerepo"]) == 0


def test_main_clean_repo_passes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _seed_baseline(monkeypatch, tmp_path, "[]\n")
    repo = tmp_path / "fakerepo"
    _write(
        repo / "tests" / "test_x.py", 'import pytest\n\n@pytest.mark.skipif(True, reason="env")\ndef t():\n    pass\n'
    )
    assert main(["--workspace-root", str(tmp_path), "--scope", "fakerepo"]) == 0


def test_main_absent_scope_is_clean_skip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _seed_baseline(monkeypatch, tmp_path, "[]\n")
    assert main(["--workspace-root", str(tmp_path), "--scope", "no_such_repo"]) == 0


# ── Dataclasses ──────────────────────────────────────────────────────────────


def test_finding_is_frozen() -> None:
    f = Finding(repo="r", file="f.py", line=1, kind="xfail", snippet="x")
    with pytest.raises(AttributeError):
        f.line = 99  # type: ignore[misc]


def test_finding_baseline_key() -> None:
    f = Finding(repo="r", file="f.py", line=1, kind="skip", snippet="x")
    assert f.baseline_key == ("r", "f.py", "skip", 1)


def test_baseline_entry_is_frozen() -> None:
    e = BaselineEntry(repo="r", file="f.py", kind="skip", line=1, status="pending_removal", successor="x")
    with pytest.raises(AttributeError):
        e.status = "changed"  # type: ignore[misc]
