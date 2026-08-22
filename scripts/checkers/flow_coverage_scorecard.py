#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Flow coverage scorecard — tracks UI/API flow coverage trends over time.

Runs check_ui_api_flow_coverage.py --format=json, appends the result to a
JSONL history file, and prints a trend summary (current vs previous score).

Usage
-----
    python flow_coverage_scorecard.py                           # default
    python flow_coverage_scorecard.py --workspace-root /path    # custom workspace root
    python flow_coverage_scorecard.py --history-file /path      # custom history file

Exit codes
----------
    0  Always (informational tool)
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def _resolve_paths(
    workspace_root: Path | None,
    history_file: Path | None,
) -> tuple[Path, Path, Path]:
    """Resolve workspace root, checker script path, and history file path."""
    if workspace_root is not None:
        ws = workspace_root.resolve()
    else:
        # Default: grandparent of this script's grandparent
        # scripts/checkers/ -> scripts/ -> unified-trading-pm/ -> workspace
        ws = Path(__file__).resolve().parent.parent.parent.parent

    pm_root = ws / "unified-trading-pm"
    checker = pm_root / "scripts" / "checkers" / "check_ui_api_flow_coverage.py"

    hist = history_file.resolve() if history_file is not None else pm_root / "docs" / "flow-coverage-history.jsonl"

    return ws, checker, hist


def _run_checker(checker_path: Path, workspace_root: Path) -> dict[str, object]:
    """Run the flow coverage checker and return parsed JSON output."""
    result = subprocess.run(
        [
            sys.executable,
            str(checker_path),
            "--format",
            "json",
            "--warning-only",
            "--workspace-root",
            str(workspace_root),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode == 2:
        print(f"ERROR: Checker configuration error:\n{result.stderr}", file=sys.stderr)
        sys.exit(0)

    if not result.stdout.strip():
        print("ERROR: Checker produced no output", file=sys.stderr)
        sys.exit(0)

    parsed: dict[str, object] = json.loads(result.stdout)
    return parsed


def _load_previous_entry(history_path: Path) -> dict[str, object] | None:
    """Load the last entry from the JSONL history file, if it exists."""
    if not history_path.is_file():
        return None

    last_line = ""
    with open(history_path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                last_line = stripped

    if not last_line:
        return None

    parsed: dict[str, object] = json.loads(last_line)
    return parsed


def _append_entry(history_path: Path, entry: dict[str, object]) -> None:
    """Append a JSON entry as a new line in the JSONL history file."""
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with open(history_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")


def _print_trend(
    current: dict[str, object],
    previous: dict[str, object] | None,
) -> None:
    """Print a human-readable trend summary."""
    summary = current.get("summary", {})  # noqa: qg-empty-fallback
    if not isinstance(summary, dict):
        print("WARNING: Unexpected summary format", file=sys.stderr)
        return

    total = summary.get("total_journeys", 0)
    covered = summary.get("covered_journeys", 0)
    pct = summary.get("coverage_pct", 0.0)
    critical_uncovered = summary.get("critical_uncovered_count", 0)

    print("=" * 60)
    print("Flow Coverage Scorecard")
    print("=" * 60)
    print(f"  Timestamp:  {current.get('timestamp', 'unknown')}")
    print(f"  Journeys:   {covered}/{total} covered ({pct}%)")
    print(f"  Critical uncovered: {critical_uncovered}")

    if previous is not None:
        prev_summary = previous.get("summary", {})  # noqa: qg-empty-fallback
        if isinstance(prev_summary, dict):
            prev_pct = prev_summary.get("coverage_pct", 0.0)
            prev_covered = prev_summary.get("covered_journeys", 0)
            prev_critical = prev_summary.get("critical_uncovered_count", 0)
            prev_ts = previous.get("timestamp", "unknown")

            if isinstance(pct, (int, float)) and isinstance(prev_pct, (int, float)):
                delta_pct = float(pct) - float(prev_pct)
                sign = "+" if delta_pct >= 0 else ""
                print("")
                print(
                    f"  Previous:   {prev_covered}/{prev_summary.get('total_journeys', '?')} ({prev_pct}%) @ {prev_ts}"
                )
                print(f"  Delta:      {sign}{delta_pct:.1f}pp coverage")

            if isinstance(critical_uncovered, int) and isinstance(prev_critical, int):
                crit_delta = critical_uncovered - prev_critical
                if crit_delta < 0:
                    print(f"  Critical:   {abs(crit_delta)} fewer critical gaps")
                elif crit_delta > 0:
                    print(f"  Critical:   {crit_delta} more critical gaps")
                else:
                    print("  Critical:   unchanged")
    else:
        print("")
        print("  (No previous data — first scorecard entry)")

    print("=" * 60)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the flow coverage scorecard."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Flow coverage scorecard — track UI/API flow coverage trends.",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="Workspace root directory (default: auto-detect)",
    )
    parser.add_argument(
        "--history-file",
        type=Path,
        default=None,
        help="Path to JSONL history file (default: docs/flow-coverage-history.jsonl)",
    )

    args = parser.parse_args(argv)

    workspace_root, checker_path, history_path = _resolve_paths(
        args.workspace_root,
        args.history_file,
    )

    if not checker_path.is_file():
        print(f"ERROR: Checker not found: {checker_path}", file=sys.stderr)
        return 0

    # Run the checker
    checker_output = _run_checker(checker_path, workspace_root)

    # Build history entry with timestamp
    entry: dict[str, object] = {
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "summary": checker_output.get("summary", {}),  # noqa: qg-empty-fallback
    }

    # Load previous for trend comparison
    previous = _load_previous_entry(history_path)

    # Append to history
    _append_entry(history_path, entry)

    # Print trend
    _print_trend(entry, previous)

    return 0


if __name__ == "__main__":
    sys.exit(main())
