# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_adapter_contract_regression.py (QG STEP 5.83).

Pure-Python — no GCS/AWS/network. Run via pytest from a venv with pyyaml
(the workspace `.venv-workspace` satisfies this), or via the workspace-root
pytest invocation base-service.sh wires up.

Covers the 2026-07-27 fix for `market_tick_data_service_ci_qg_ratchet_absent_repo_false_fail`:
the baseline spans ~13 repos captured on a full local workspace scan, but a per-repo CI
checkout only clones the target repo + its declared `dep_repos` — every baseline entry for
an absent sibling repo must be SKIPPED, never counted as a "file missing" regression.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from check_adapter_contract_regression import (  # type: ignore[import-not-found]
    Baseline,
    count_contract_calls_in_file,
    load_baseline,
    main,
    present_repo_names,
)


def _write(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


# ── Single-file counting ─────────────────────────────────────────────────────


def test_count_matches_each_contract_pattern(tmp_path: Path) -> None:
    f = _write(
        tmp_path / "handler.py",
        """
        def f():
            classify_venue_error("v", "t")
            log_event(ADAPTER_FETCH_FAILED)
            recorder.record_captured()
            recorder.record_empty()
            recorder.record_failed()
        """,
    )
    assert count_contract_calls_in_file(f) == 5


def test_count_zero_when_no_contract_calls(tmp_path: Path) -> None:
    f = _write(tmp_path / "clean.py", "x = 1\n")
    assert count_contract_calls_in_file(f) == 0


# ── present_repo_names ───────────────────────────────────────────────────────


def test_present_repo_names_only_git_dirs(tmp_path: Path) -> None:
    for r in ("repoA", "repoB"):
        (tmp_path / r / ".git").mkdir(parents=True)
    (tmp_path / "not-a-repo").mkdir()  # no .git → excluded
    (tmp_path / ".hidden").mkdir()  # dot-dir → excluded
    (tmp_path / "scripts").mkdir()  # excluded dir name
    names = present_repo_names(tmp_path)
    assert names == {"repoA", "repoB"}


# ── Baseline loading ─────────────────────────────────────────────────────────


def test_load_baseline_real_file_present() -> None:
    # The committed baseline must parse and be non-empty (seeded 2026-05-20).
    bl = load_baseline()
    assert isinstance(bl.counts, dict)
    assert bl.required("a-file-that-definitely-is-not-listed.py") == 0


# ── main() end-to-end: the absent-repo-skip fix ──────────────────────────────


def test_main_skips_baseline_entries_for_repos_absent_from_checkout(tmp_path: Path) -> None:
    """The real bug: a single-repo CI checkout (here: only `market-tick-data-service`
    present) must NOT fail on baseline entries belonging to sibling repos
    (`execution-service`, `features-service`, ...) that simply aren't cloned here."""
    bl = load_baseline()
    real_mtds_entries = {k: v for k, v in bl.counts.items() if k.startswith("market-tick-data-service/")}
    assert real_mtds_entries, "expected at least one real market-tick-data-service baseline entry"

    repo = tmp_path / "market-tick-data-service"
    (repo / ".git").mkdir(parents=True)
    for file_key, required in real_mtds_entries.items():
        rel = Path(file_key).relative_to("market-tick-data-service")
        body = "\n".join("classify_venue_error()" for _ in range(required))
        _write(repo / rel, body + "\n")

    # No other sibling repo directories exist under tmp_path at all — exactly the
    # single-repo CI checkout shape. Every baseline entry for execution-service /
    # features-service / etc. must be skipped, not flagged as "file missing".
    rc = main(["--workspace-root", str(tmp_path)])
    assert rc == 0


def test_main_still_fails_on_genuine_regression_in_present_repo(tmp_path: Path) -> None:
    """A present repo whose file drops below its baseline count must still FAIL —
    the absent-repo skip must not neuter the ratchet for the repo actually being checked."""
    repo = tmp_path / "synthetic-regressed-repo"
    (repo / ".git").mkdir(parents=True)
    pkg = repo / "pkg"
    _write(pkg / "handler.py", "classify_venue_error()\n")  # 1 call

    baseline = Baseline(counts={"synthetic-regressed-repo/pkg/handler.py": 2})  # requires 2

    import check_adapter_contract_regression as m

    original_load_baseline = m.load_baseline
    m.load_baseline = lambda: baseline
    try:
        rc = m.main(["--workspace-root", str(tmp_path)])
    finally:
        m.load_baseline = original_load_baseline
    assert rc == 1


def test_main_check_path_never_walks_full_workspace(tmp_path: Path) -> None:
    """Regression test for the 2026-07-27 QG STEP 5.83 timeout incident: the ratchet
    check must read only the baseline's own files (`read_baseline_files`), never do a
    full-workspace `.py` walk (`scan_workspace`) — that full walk was measured
    exceeding the 60s CI `run_timeout` on a 25-repo workspace (>120s standalone, worse
    under host I/O contention), hard-failing the gate with no actual regression
    present. Locks in the targeted-read fix so this can't silently regress back."""
    repo = tmp_path / "synthetic-repo-3"
    (repo / ".git").mkdir(parents=True)
    _write(repo / "pkg" / "handler.py", "classify_venue_error()\n")
    # Files a full workspace walk WOULD visit but the targeted read must never touch.
    for i in range(50):
        _write(repo / "pkg" / f"unrelated_{i}.py", "x = 1\n")

    baseline = Baseline(counts={"synthetic-repo-3/pkg/handler.py": 1})

    import check_adapter_contract_regression as m

    def _boom(*_args: object, **_kwargs: object) -> list[object]:
        raise AssertionError("scan_workspace must not run on the non-regenerate check path")

    original_load_baseline = m.load_baseline
    original_scan_workspace = m.scan_workspace
    m.load_baseline = lambda: baseline
    m.scan_workspace = _boom  # type: ignore[assignment]
    try:
        rc = m.main(["--workspace-root", str(tmp_path)])
    finally:
        m.load_baseline = original_load_baseline
        m.scan_workspace = original_scan_workspace
    assert rc == 0


def test_main_fails_on_missing_file_in_present_repo(tmp_path: Path) -> None:
    """A baseline-listed file whose repo IS present but the file itself was deleted/renamed
    without a --regenerate-baseline run is a genuine regression → FAIL, distinct from the
    absent-repo case."""
    repo = tmp_path / "synthetic-repo-2"
    (repo / ".git").mkdir(parents=True)
    _write(repo / "pkg" / "other.py", "x = 1\n")  # unrelated file present

    baseline = Baseline(counts={"synthetic-repo-2/pkg/deleted_handler.py": 1})

    import check_adapter_contract_regression as m

    original_load_baseline = m.load_baseline
    m.load_baseline = lambda: baseline
    try:
        rc = m.main(["--workspace-root", str(tmp_path)])
    finally:
        m.load_baseline = original_load_baseline
    assert rc == 1
