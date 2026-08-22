# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_no_empty_string_fallback.py (QG STEP 5.101).

Covers `_has_empty_fallback_noqa()`'s three documented noqa shapes: a
single-code comment, a multi-code comment packed into ONE cluster, and two
SEPARATE `# noqa: ...` clusters on the same line
(qg_empty_string_fallback_checker_misses_stacked_noqa_2026_07_13.md).

Also covers the git-diff-based over-baseline reporting added for
`instruments_service_empty_string_fallback_baseline_breach_2026_07_14.md`:
`Baseline.commit_for()` round-tripping through `load_baseline`/`write_baseline`,
and `_resolve_over_baseline_sites()` preferring a real git diff over the old
positional tail-slice, with a graceful fallback when no commit is on record.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from check_no_empty_string_fallback import (  # type: ignore[import-not-found]
    Baseline,
    RepoScan,
    _diff_added_empty_string_sites,
    _has_empty_fallback_noqa,
    _resolve_over_baseline_sites,
    load_baseline,
    write_baseline,
)


def test_single_code_cluster() -> None:
    assert _has_empty_fallback_noqa('x = d.get("k", "")  # noqa: qg-empty-fallback')


def test_multi_code_one_cluster_space_separated() -> None:
    assert _has_empty_fallback_noqa('x = d.get("k", "")  # noqa: qg-os-environ qg-empty-fallback')


def test_multi_code_one_cluster_comma_separated() -> None:
    assert _has_empty_fallback_noqa('x = d.get("k", "")  # noqa: qg-os-environ, qg-empty-fallback')


def test_two_separate_clusters_second_cluster_carries_the_code() -> None:
    """Regression: dev_paths.py:27's exact shape — two independent `# noqa: ...`
    clusters on one line, with `qg-empty-fallback` in the SECOND, not the first.
    """
    assert _has_empty_fallback_noqa('x = d.get("k", "")  # noqa: qg-os-env  # noqa: qg-empty-fallback')


def test_two_separate_clusters_first_cluster_carries_the_code() -> None:
    assert _has_empty_fallback_noqa('x = d.get("k", "")  # noqa: qg-empty-fallback  # noqa: qg-os-env')


def test_no_noqa_comment() -> None:
    assert not _has_empty_fallback_noqa('x = d.get("k", "")')


def test_noqa_present_but_wrong_code() -> None:
    assert not _has_empty_fallback_noqa('x = d.get("k", "")  # noqa: qg-os-environ')


def test_two_separate_clusters_neither_carries_the_code() -> None:
    assert not _has_empty_fallback_noqa('x = d.get("k", "")  # noqa: qg-os-env  # noqa: qg-empty-string')


# ── Git-diff-based over-baseline reporting ──────────────────────────────────


def _run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True)


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(repo, "init", "-q")
    _run_git(repo, "config", "user.email", "qg-test@example.invalid")
    _run_git(repo, "config", "user.name", "QG Test")
    _run_git(repo, "config", "commit.gpgsign", "false")
    return repo


def _commit_all(repo: Path, message: str) -> str:
    _run_git(repo, "add", "-A")
    _run_git(repo, "commit", "-q", "-m", message)
    return _run_git(repo, "rev-parse", "HEAD").stdout.strip()


def test_diff_added_empty_string_sites_detects_new_site(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    pkg = repo / "pkg"
    pkg.mkdir()
    (pkg / "old_site.py").write_text('x = d.get("legacy_key", "")\n', encoding="utf-8")
    baseline_sha = _commit_all(repo, "seed: one pre-existing site")

    (pkg / "new_site.py").write_text('y = d.get("new_key", "")\n', encoding="utf-8")
    _commit_all(repo, "add: one new site")

    added = _diff_added_empty_string_sites(repo, baseline_sha)

    assert added == {("pkg/new_site.py", 'y = d.get("new_key", "")')}


def test_diff_added_empty_string_sites_excludes_noqa_marked_new_lines(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "a.py").write_text("z = 1\n", encoding="utf-8")
    baseline_sha = _commit_all(repo, "seed")

    (repo / "a.py").write_text('z = d.get("k", "")  # noqa: qg-empty-fallback\n', encoding="utf-8")
    _commit_all(repo, "add noqa'd site")

    assert _diff_added_empty_string_sites(repo, baseline_sha) == set()


def test_diff_added_empty_string_sites_returns_none_for_unreachable_commit(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "a.py").write_text("z = 1\n", encoding="utf-8")
    _commit_all(repo, "seed")

    assert _diff_added_empty_string_sites(repo, "0" * 40) is None


def test_diff_added_empty_string_sites_returns_none_when_not_a_git_repo(tmp_path: Path) -> None:
    not_repo = tmp_path / "not_a_repo"
    not_repo.mkdir()

    assert _diff_added_empty_string_sites(not_repo, "deadbeef") is None


def test_resolve_over_baseline_sites_falls_back_without_baseline_commit(tmp_path: Path) -> None:
    scan = RepoScan(
        repo="demo",
        count=3,
        sites=[
            ("a.py", 1, 'a = d.get("k1", "")'),
            ("b.py", 2, 'b = d.get("k2", "")'),
            ("c.py", 3, 'c = d.get("k3", "")'),
        ],
    )

    over, note = _resolve_over_baseline_sites(scan, allowed=2, repo_root=tmp_path, baseline_commit=None)

    assert over == scan.sites[2:]
    assert "no baseline commit on record" in note


def test_resolve_over_baseline_sites_falls_back_when_diff_unreachable(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "a.py").write_text('a = d.get("k", "")\n', encoding="utf-8")
    _commit_all(repo, "seed")
    scan = RepoScan(repo="demo", count=1, sites=[("a.py", 1, 'a = d.get("k", "")')])

    over, note = _resolve_over_baseline_sites(scan, allowed=0, repo_root=repo, baseline_commit="0" * 40)

    assert over == scan.sites
    assert "git-diff against the baseline commit failed" in note


def test_resolve_over_baseline_sites_prefers_diff_detection_over_positional_slice(tmp_path: Path) -> None:
    """Reproduces the exact failure mode from
    instruments_service_empty_string_fallback_baseline_breach_2026_07_14.md: the
    positional tail-slice picks whichever site sorts alphabetically last
    (`zzz_old.py`, 2 months stale), while the real new site (`mmm_new.py`) sorts
    in the middle and would never be reported by the old code."""
    repo = _init_repo(tmp_path)
    (repo / "aaa_old.py").write_text('a = d.get("old", "")\n', encoding="utf-8")
    (repo / "zzz_old.py").write_text('z = d.get("also_old", "")\n', encoding="utf-8")
    baseline_sha = _commit_all(repo, "seed: two pre-existing sites, baseline=2")

    (repo / "mmm_new.py").write_text('m = d.get("new", "")\n', encoding="utf-8")
    _commit_all(repo, "add: one genuinely new site")

    scan = RepoScan(
        repo="demo",
        count=3,
        sites=sorted(
            [
                ("aaa_old.py", 1, 'a = d.get("old", "")'),
                ("mmm_new.py", 1, 'm = d.get("new", "")'),
                ("zzz_old.py", 1, 'z = d.get("also_old", "")'),
            ]
        ),
    )
    assert scan.sites[2:] == [("zzz_old.py", 1, 'z = d.get("also_old", "")')]  # old bug's pick

    over, note = _resolve_over_baseline_sites(scan, allowed=2, repo_root=repo, baseline_commit=baseline_sha)

    assert over == [("mmm_new.py", 1, 'm = d.get("new", "")')]
    assert note == ""


def test_baseline_commit_round_trip_via_write_and_load(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "a.py").write_text("x = 1\n", encoding="utf-8")
    sha = _commit_all(repo, "seed")

    baseline_file = tmp_path / "baseline.yaml"
    write_baseline({"demo": 5}, Baseline(), path=baseline_file, repo_roots={"demo": repo})

    loaded = load_baseline(baseline_file)

    assert loaded.allowed("demo") == 5
    assert loaded.commit_for("demo") == sha


def test_baseline_commit_preserved_for_unscanned_repo(tmp_path: Path) -> None:
    baseline_file = tmp_path / "baseline.yaml"
    existing = Baseline(counts={"other-repo": 3}, commits={"other-repo": "abc123"})

    write_baseline({}, existing, path=baseline_file, repo_roots={})

    loaded = load_baseline(baseline_file)
    assert loaded.allowed("other-repo") == 3
    assert loaded.commit_for("other-repo") == "abc123"
