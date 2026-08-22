# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for the shared standing-condition alert-recovery diff helper.

Pins the transition table (recovered fires ONLY on true->false) and the state-file
round-trip (missing/corrupt file -> no false recovery; the file always ends up holding
the current tick's value for the next run's diff).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from alert_recovery import compute_recovery, read_prev_alert, write_state


@pytest.mark.parametrize(
    ("prev_alert", "current_alert", "expected"),
    [
        (True, False, True),  # was alerting, now clear -> genuine recovery
        (False, False, False),  # steady-state healthy -> no recovery
        (True, True, False),  # still alerting -> no recovery (the existing notify job re-nags)
        (False, True, False),  # a fresh alert firing -> not a recovery
    ],
)
def test_compute_recovery_transition_table(prev_alert: bool, current_alert: bool, expected: bool) -> None:
    assert compute_recovery(prev_alert, current_alert) is expected


def test_read_prev_alert_missing_file_is_false(tmp_path: Path) -> None:
    assert read_prev_alert(tmp_path / "does-not-exist.json") is False


def test_read_prev_alert_corrupt_file_is_false(tmp_path: Path) -> None:
    state_file = tmp_path / "state.json"
    state_file.write_text("not json", encoding="utf-8")
    assert read_prev_alert(state_file) is False


def test_write_state_then_read_round_trips(tmp_path: Path) -> None:
    state_file = tmp_path / "state.json"
    write_state(state_file, True)
    assert read_prev_alert(state_file) is True
    write_state(state_file, False)
    assert read_prev_alert(state_file) is False


def test_cli_recovered_case(tmp_path: Path) -> None:
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"alert": True}), encoding="utf-8")
    script = Path(__file__).parent / "alert_recovery.py"
    result = subprocess.run(
        [sys.executable, str(script), "--state-file", str(state_file), "--current", "false"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "recovered=true"
    assert json.loads(state_file.read_text(encoding="utf-8")) == {"alert": False}


def test_cli_no_prior_state_never_recovers(tmp_path: Path) -> None:
    state_file = tmp_path / "state.json"  # does not exist yet — first-ever tick
    script = Path(__file__).parent / "alert_recovery.py"
    result = subprocess.run(
        [sys.executable, str(script), "--state-file", str(state_file), "--current", "false"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "recovered=false"
    assert json.loads(state_file.read_text(encoding="utf-8")) == {"alert": False}


def test_cli_still_alerting_stays_silent(tmp_path: Path) -> None:
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"alert": True}), encoding="utf-8")
    script = Path(__file__).parent / "alert_recovery.py"
    result = subprocess.run(
        [sys.executable, str(script), "--state-file", str(state_file), "--current", "true"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "recovered=false"
