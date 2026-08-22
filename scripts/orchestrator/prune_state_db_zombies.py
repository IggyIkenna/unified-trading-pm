#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Prune zombie rows from agent-orchestrator state.db.

Zombies are state.db `tasks` rows where ALL of:
  - status = 'queued'
  - dispatched_to IS NULL  (not actively held by a worker)
  - task_id NOT IN current backlog.yaml

Done-rows (status='done') and dispatched-rows are NEVER touched — they are
audit history and may belong to active workers respectively.

Default mode: DRY-RUN — prints counts but makes no changes.
Pass --exec to actually DELETE.

Usage (run from any directory):
  python3 scripts/orchestrator/prune_state_db_zombies.py
  python3 scripts/orchestrator/prune_state_db_zombies.py --exec
  python3 scripts/orchestrator/prune_state_db_zombies.py \\
      --db /path/to/state.db --backlog /path/to/backlog.yaml
  python3 scripts/orchestrator/prune_state_db_zombies.py --exec \\
      --db /opt/orchestrator/data/state/state.db \\
      --backlog /opt/orchestrator/data/config/backlog.yaml
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path


def _default_ao_root() -> Path:
    """agent-orchestrator sits next to unified-trading-pm in the workspace root."""
    pm_root = Path(__file__).resolve().parent.parent.parent
    return pm_root.parent / "agent-orchestrator"


def _default_db_path() -> Path:
    return _default_ao_root() / "data" / "state" / "state.db"


def _default_backlog_path() -> Path:
    return _default_ao_root() / "data" / "config" / "backlog.yaml"


def _load_backlog_ids(backlog_path: Path) -> set[str]:
    """Return the set of task IDs in backlog.yaml (empty set if file absent)."""
    if not backlog_path.exists():
        return set()
    try:
        import yaml  # pyyaml — available on all orchestrator VMs

        with backlog_path.open() as fh:
            data = yaml.safe_load(fh) or {}
    except ImportError:
        # Fallback: regex scan for `  id: <value>` lines inside tasks list.
        import re

        text = backlog_path.read_text()
        return set(re.findall(r"^\s+id:\s+(\S+)", text, re.MULTILINE))
    tasks = data.get("tasks") or []
    return {str(t["id"]) for t in tasks if isinstance(t, dict) and "id" in t}


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        metavar="PATH",
        help="Path to state.db (default: <ao-root>/data/state/state.db)",
    )
    parser.add_argument(
        "--backlog",
        type=Path,
        default=None,
        metavar="PATH",
        help="Path to backlog.yaml (default: <ao-root>/data/config/backlog.yaml)",
    )
    parser.add_argument(
        "--exec",
        action="store_true",
        dest="execute",
        help="Actually delete zombie rows — default is DRY-RUN (print only)",
    )
    args = parser.parse_args()

    db_path = args.db or _default_db_path()
    backlog_path = args.backlog or _default_backlog_path()

    if not db_path.exists():
        print(f"ERROR: state.db not found: {db_path}", file=sys.stderr)
        print("  Use --db /path/to/state.db to override.", file=sys.stderr)
        return 1

    print(f"db      : {db_path}")
    print(f"backlog : {backlog_path}")

    backlog_ids = _load_backlog_ids(backlog_path)
    print(f"backlog : {len(backlog_ids)} task IDs loaded")
    print()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM tasks")
    total: int = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM tasks WHERE status = 'done'")
    done_count: int = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM tasks WHERE status = 'dispatched'")
    dispatched_count: int = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM tasks WHERE status = 'queued' AND dispatched_to IS NOT NULL")
    queued_dispatched: int = cur.fetchone()[0]

    cur.execute("SELECT task_id FROM tasks WHERE status = 'queued' AND dispatched_to IS NULL")
    queued_undispatched_ids: set[str] = {row[0] for row in cur.fetchall()}
    queued_undispatched: int = len(queued_undispatched_ids)

    zombies: set[str] = queued_undispatched_ids - backlog_ids
    safe_to_delete: int = len(zombies)
    still_valid: int = queued_undispatched - safe_to_delete

    other_count: int = total - done_count - dispatched_count - queued_dispatched - queued_undispatched

    print("=" * 62)
    print("  state.db breakdown")
    print(f"  {'Total rows':<38} {total:>8}")
    print(f"  {'  done':<38} {done_count:>8}")
    print(f"  {'  dispatched':<38} {dispatched_count:>8}")
    print(f"  {'  queued (worker holding slot)':<38} {queued_dispatched:>8}")
    print(f"  {'  queued (undispatched)':<38} {queued_undispatched:>8}")
    print(f"  {'    ↳ in current backlog (live)':<38} {still_valid:>8}")
    print(f"  {'    ↳ ZOMBIE (safe to delete)':<38} {safe_to_delete:>8}")
    if other_count:
        print(f"  {'  other status':<38} {other_count:>8}")
    print("=" * 62)

    if safe_to_delete == 0:
        print("\nNo zombies — state.db is clean.")
        conn.close()
        return 0

    if not args.execute:
        print(f"\nDRY-RUN: {safe_to_delete} zombies would be deleted.")
        print("Re-run with --exec to delete them.")
        sample = sorted(zombies)[:8]
        suffix = f" … (+{safe_to_delete - len(sample)} more)" if safe_to_delete > len(sample) else ""
        print(f"Sample : {sample}{suffix}")
        conn.close()
        return 0

    # --exec path: DELETE in chunks of 500 to stay under SQLite's 999-variable limit.
    zombie_list = sorted(zombies)
    chunk_size = 500
    deleted = 0
    for i in range(0, len(zombie_list), chunk_size):
        chunk = zombie_list[i : i + chunk_size]
        placeholders = ",".join("?" * len(chunk))
        cur.execute(
            f"DELETE FROM tasks"  # nosec B608 — placeholders is only `?,?,...`; values bound via params
            f" WHERE task_id IN ({placeholders})"
            f"   AND status = 'queued'"
            f"   AND dispatched_to IS NULL",
            chunk,
        )
        deleted += cur.rowcount
    conn.commit()
    conn.close()

    print(f"\nDELETED {deleted} zombie rows.")
    print(f"Remaining total: {total - deleted}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
