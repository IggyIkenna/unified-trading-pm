#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
rollup_resolved_pings.py — Read-time rollup for per-slot ping files.

Rolls up entries that are both (a) ✅ DONE / ✅ RESOLVED and (b) older than
24 hours into a `## Prior context (rolled)` collapsed section at the bottom of
the file.  Keeps the active (recent or unresolved) entries in the main body.

Usage:
    python3 scripts/agents/rollup_resolved_pings.py <ping_file> [--dry-run]

Trigger: called from a slot main's boot sequence when the ping file grows
large.  NOT called from setup-tab-worktrees.sh (avoids racing with append-writes
from sub-agents).  The `--reset-slot` truncate step is the hard reset; this
helper provides bounded-growth within a same-theme multi-day run (R1).

Per-tab-worktrees.md SSOT:
    codex/05-infrastructure/per-tab-worktrees.md § "Slot-reset discipline"
Plan:
    plans/active/per_agent_worktrees_2026_05_10.md Phase 4.5 P1
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# A ping line is resolved if it contains one of these markers.
_RESOLVED_MARKERS = ("✅ DONE", "✅ RESOLVED", "✅ ACK", "✅ done", "✅ resolved")

# ISO-ish timestamp embedded in ping lines: [YYYY-MM-DD HH:MM UTC]
_TS_RE = re.compile(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC\]")


def _parse_ts(line: str) -> datetime | None:
    m = _TS_RE.search(line)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M").replace(tzinfo=UTC)
    except ValueError:
        return None


def _is_stale_resolved(line: str, cutoff: datetime) -> bool:
    if not any(marker in line for marker in _RESOLVED_MARKERS):
        return False
    ts = _parse_ts(line)
    return ts is not None and ts < cutoff


def rollup(ping_path: Path, dry_run: bool = False) -> int:
    """Roll up stale resolved entries into ## Prior context (rolled) section.

    Returns the number of lines rolled up.
    """
    text = ping_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    cutoff = datetime.now(tz=UTC) - timedelta(hours=24)

    # Split out the existing "## Prior context (rolled)" block if present.
    prior_header = "## Prior context (rolled)\n"
    if prior_header in lines:
        idx = lines.index(prior_header)
        active_lines = lines[:idx]
        prior_lines = lines[idx + 1 :]
    else:
        active_lines = lines
        prior_lines = []

    to_roll: list[str] = []
    keep: list[str] = []
    for line in active_lines:
        if _is_stale_resolved(line, cutoff):
            to_roll.append(line)
        else:
            keep.append(line)

    if not to_roll:
        return 0

    rolled_block: list[str] = [prior_header, *prior_lines, *to_roll]
    new_text = "".join(keep) + "\n" + "".join(rolled_block)

    if not dry_run:
        ping_path.write_text(new_text, encoding="utf-8")

    return len(to_roll)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ping_file", type=Path, help="Path to slot_N.md ping file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print count of lines that would be rolled up without writing",
    )
    args = parser.parse_args()

    if not args.ping_file.exists():
        print(f"ERROR: ping file not found: {args.ping_file}", file=sys.stderr)
        sys.exit(1)

    n = rollup(args.ping_file, dry_run=args.dry_run)
    if args.dry_run:
        print(f"[dry-run] would roll up {n} stale resolved line(s)")
    else:
        print(f"Rolled up {n} stale resolved line(s) into '## Prior context (rolled)'")


if __name__ == "__main__":
    main()
