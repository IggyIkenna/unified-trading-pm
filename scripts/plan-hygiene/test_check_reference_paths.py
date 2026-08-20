# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_reference_paths.py's --only defects
(check_reference_paths_silent_skip_and_quiet_hides_violation_2026_08_12.md).

Defect 1: an unresolvable --only path was silently `continue`d, then reported
"0 violation(s)" / exit 0 -- a false-clean result for a file never actually checked.
Defect 2: `--quiet` suppressed the per-violation FORMAT/DANGLING lines even on
FAILURE, so a precommit failure said "N violation(s)" and never which reference.

Cost seven failed safe-doc-push attempts and six wrong diagnoses on one real
one-line violation before these were found (see the issue doc).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Lives beside its script, matching scripts/quality_gates|cicd|docs. That only
# WORKS because scripts/plan-hygiene/ is listed in PYTEST_UNIT_DIR in
# scripts/quality-gates.sh — the gate passes explicit path args, which override
# pyproject's `testpaths`, so a directory absent from that list is silently never
# collected. This file spent its first day exactly there: present, plausible, and
# never executed. If you add a test dir, add it to PYTEST_UNIT_DIR too.
sys.path.insert(0, str(Path(__file__).parent))

import check_reference_paths as checker


def test_unresolvable_only_path_is_a_hard_error(capsys, tmp_path: Path) -> None:
    """A path that does not resolve to a file must exit non-zero, never be
    silently skipped and reported as '0 violation(s)'."""
    missing = tmp_path / "does_not_exist.md"

    exit_code = checker._run_only([str(missing)], quiet=False)

    assert exit_code != 0
    out = capsys.readouterr().out
    assert "UNRESOLVED" in out
    assert str(missing) in out


def test_unresolvable_only_path_reported_even_under_quiet(capsys, tmp_path: Path) -> None:
    """The whole point of the fix: --quiet must not hide WHY --only failed."""
    missing = tmp_path / "does_not_exist.md"

    exit_code = checker._run_only([str(missing)], quiet=True)

    assert exit_code != 0
    out = capsys.readouterr().out
    assert "UNRESOLVED" in out


def test_existing_clean_file_still_passes(capsys, tmp_path: Path) -> None:
    """A real file with no violations must still exit 0 (no regression from the fix)."""
    clean = tmp_path / "clean.md"
    clean.write_text("Nothing but plain prose here.\n")

    exit_code = checker._run_only([str(clean)], quiet=False)

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "UNRESOLVED" not in out


def test_violation_in_real_file_prints_evidence_even_under_quiet(capsys, tmp_path: Path) -> None:
    """Defect 2: a genuine violation's FORMAT/DANGLING line must print on failure
    regardless of --quiet -- quiet only suppresses noise on SUCCESS."""
    bad = tmp_path / "bad.md"
    # A bare codex/... reference (missing leading slash) is a FORMAT violation.
    bad.write_text("See codex/06-coding-standards/quality-gates.md for details.\n")

    exit_code = checker._run_only([str(bad)], quiet=True)

    assert exit_code != 0
    out = capsys.readouterr().out
    assert "FORMAT" in out
