#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Stale-blocker reaper for the agent-orchestrator backlog.

Finds tasks that have been queued for >STALE_DAYS (default 3) with at least
one unmet prereq. Classifies each case:

  DEADLOCK      — both the blocked task and its blocker are queued with
                  unmet prereqs (circular or mutually-stuck dependency).
  ORPHAN        — a prereq task_id appears in prereqs.completed_tasks but is
                  NOT in the backlog at all (removed from plan without being
                  marked done; task will never be dispatchable).
  PHANTOM_DONE  — prereq task_id IS in the DB with status=done but the
                  dispatcher somehow hasn't picked up the dependent. Rare;
                  usually resolves itself on the next /boot cycle.

Output:
  stdout       — one line per finding (CSV-friendly)
  daily summary file — appended to $SUMMARY_DIR/reap_<YYYY-MM-DD>.log
  Slack        — DEADLOCK + ORPHAN emit alerts; PHANTOM_DONE is info-only

Usage:
    python3 scripts/orchestrator/reap_stale_blockers.py \\
        [--backlog PATH]   # default: auto-detect from orch repo
        [--db PATH]        # default: auto-detect from orch data/state/state.db
        [--stale-days N]   # default: 3
        [--summary-dir D]  # default: /tmp
        [--dry-run]        # print findings but skip Slack + summary write
        [--quiet]          # suppress stdout

Environment variables read:
    AGENT_ORCHESTRATOR_SLACK_WEBHOOK  — for Slack alerts
    ORCH_BACKLOG_YAML                 — override backlog path
    ORCH_STATE_DB                     — override DB path
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Config + defaults
# ---------------------------------------------------------------------------

_WORKSPACE = Path(os.environ.get("WORKSPACE_ROOT", "/home/ubuntu/unified-trading-system-repos"))
_DEFAULT_BACKLOG = _WORKSPACE / "agent-orchestrator" / "data" / "config" / "backlog.yaml"
_DEFAULT_DB = _WORKSPACE / "agent-orchestrator" / "data" / "state" / "state.db"
_DEFAULT_STALE_DAYS = 3

_SLACK_WEBHOOK = os.environ.get("AGENT_ORCHESTRATOR_SLACK_WEBHOOK", "")  # noqa: qg-empty-fallback
_DASHBOARD_URL = os.environ.get("ORCHESTRATOR_DASHBOARD_URL", "https://agent-orchestrator.odum-research.com")


# ---------------------------------------------------------------------------
# Minimal YAML loader (no external dep; parses only the tasks list shape)
# ---------------------------------------------------------------------------


def _load_backlog_yaml(path: Path) -> list[dict]:
    """Parse backlog.yaml tasks without PyYAML. Returns list of task dicts.

    Falls back to yaml module if available (much more robust for multi-line
    strings); uses a line-by-line approach only as last resort.
    """
    try:
        import yaml  # type: ignore[import-untyped]  # noqa: imports-inside-functions

        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("tasks", []) if isinstance(data, dict) else []  # noqa: qg-empty-fallback
    except ImportError:
        pass

    # Fallback: use json alternative embedded in the server if reachable
    try:
        # Try to import the server's backlog module via sys.path manipulation
        srv = _WORKSPACE / "agent-orchestrator"
        if str(srv) not in sys.path:
            sys.path.insert(0, str(srv))
        from server.backlog import load_backlog  # type: ignore[import-not-found]  # noqa: imports-inside-functions

        tasks = load_backlog(path)
        return [t.model_dump() for t in tasks]
    except (ImportError, OSError, ValueError, AttributeError):
        pass

    print(
        f"WARNING: cannot parse {path} — install PyYAML or run from the agent-orchestrator venv",
        file=sys.stderr,
    )
    return []


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


def _load_task_statuses(db_path: Path) -> dict[str, dict]:
    """Return {task_id: {status, queued_at}} from the SQLite tasks table."""
    rows: dict[str, dict] = {}
    if not db_path.exists():
        print(f"WARNING: DB not found at {db_path}", file=sys.stderr)
        return rows
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT task_id, status, queued_at FROM tasks")
        for row in cur.fetchall():
            rows[row["task_id"]] = {
                "status": row["status"] or "queued",
                "queued_at": row["queued_at"],
            }
    return rows


# ---------------------------------------------------------------------------
# Slack
# ---------------------------------------------------------------------------


def _slack_post(text: str, blocks: list[dict] | None = None) -> None:
    if not _SLACK_WEBHOOK:
        return
    try:
        import urllib.request  # noqa: imports-inside-functions

        payload: dict = {"text": text}
        if blocks:
            payload["blocks"] = blocks
        req = urllib.request.Request(
            _SLACK_WEBHOOK,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)  # nosec: B310 — HTTPS webhook URL from env var, not user input
    except Exception as e:  # noqa: broad-except — best-effort Slack notify, must never crash the reaper
        print(f"Slack notify failed: {e}", file=sys.stderr)


def _alert_deadlock(task_id: str, blocker_id: str, stale_days: int) -> None:
    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    backlog_link = f"{_DASHBOARD_URL}/#backlog"
    _slack_post(
        f":rotating_light: DEADLOCK in backlog: `{task_id}` ← `{blocker_id}` "
        f"(both queued >{stale_days}d) [{ts}] — <{backlog_link}|Open Backlog>",
        blocks=[
            {
                "type": "header",
                "text": {"type": "plain_text", "text": ":rotating_light: Backlog deadlock detected"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Blocked task:*\n`{task_id}`"},
                    {"type": "mrkdwn", "text": f"*Blocking task:*\n`{blocker_id}`"},
                    {"type": "mrkdwn", "text": f"*Stale for:*\n>{stale_days} days"},
                    {"type": "mrkdwn", "text": f"*Time:*\n{ts}"},
                ],
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            "Both tasks are queued with unmet prereqs — manual resolution required. "
                            f"<{backlog_link}|Open orchestrator backlog>"
                        ),
                    }
                ],
            },
        ],
    )


def _alert_orphan(task_id: str, missing_blocker_id: str, stale_days: int) -> None:
    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    backlog_link = f"{_DASHBOARD_URL}/#backlog"
    _slack_post(
        f":warning: ORPHAN-BLOCKED: `{task_id}` waiting on `{missing_blocker_id}` "
        f"which is not in backlog (>{stale_days}d) [{ts}] — <{backlog_link}|Open Backlog>",
        blocks=[
            {
                "type": "header",
                "text": {"type": "plain_text", "text": ":warning: Orphan-blocked task"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Blocked task:*\n`{task_id}`"},
                    {"type": "mrkdwn", "text": f"*Missing prereq:*\n`{missing_blocker_id}`"},
                    {"type": "mrkdwn", "text": f"*Stale for:*\n>{stale_days} days"},
                    {"type": "mrkdwn", "text": f"*Time:*\n{ts}"},
                ],
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            "Prereq task was removed from the backlog without being marked done. "
                            "Remove it from prereqs.completed_tasks or re-add the task. "
                            f"<{backlog_link}|Open orchestrator backlog>"
                        ),
                    }
                ],
            },
        ],
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run(
    backlog_path: Path,
    db_path: Path,
    stale_days: int,
    summary_dir: Path,
    dry_run: bool,
    quiet: bool,
) -> int:
    now = datetime.now(UTC)
    stale_cutoff = now - timedelta(days=stale_days)

    tasks_def = _load_backlog_yaml(backlog_path)
    if not tasks_def:
        if not quiet:
            print("No tasks loaded from backlog — nothing to reap.")
        return 0

    task_map: dict[str, dict] = {t["id"]: t for t in tasks_def}
    statuses = _load_task_statuses(db_path)

    findings: list[dict] = []

    for task in tasks_def:
        tid = task["id"]
        db_row = statuses.get(tid)
        if not db_row:
            continue  # not in DB yet — skip

        status = db_row["status"]
        if status != "queued":
            continue  # only care about queued tasks

        queued_at_raw = db_row.get("queued_at")
        if not queued_at_raw:
            continue
        try:
            queued_at = datetime.fromisoformat(str(queued_at_raw).replace("Z", "+00:00"))
            # Ensure tz-aware for comparison with now (UTC)
            if queued_at.tzinfo is None:
                queued_at = queued_at.replace(tzinfo=UTC)
        except (ValueError, TypeError):
            continue

        if queued_at >= stale_cutoff:
            continue  # not stale yet

        # Check prereqs
        prereqs = task.get("prereqs") or {}
        blocker_ids = prereqs.get("completed_tasks") or []
        unmet_blockers: list[str] = []
        for bid in blocker_ids:
            b_status = statuses.get(bid, {}).get("status")
            if b_status != "done":
                unmet_blockers.append(bid)

        if not unmet_blockers:
            continue  # all prereqs met — dispatcher will pick this up

        stale_for_days = int((now - queued_at).total_seconds() / 86400)

        for bid in unmet_blockers:
            if bid not in task_map and bid not in statuses:
                # ORPHAN: blocker not in backlog at all
                category = "ORPHAN"
                msg = f"{category}  {tid!r:50s} ← {bid!r:50s}  stale={stale_for_days}d  (blocker missing from backlog)"
                findings.append(
                    {
                        "category": category,
                        "task_id": tid,
                        "blocker_id": bid,
                        "stale_days": stale_for_days,
                    }
                )
                if not quiet:
                    print(msg)
                if not dry_run:
                    _alert_orphan(tid, bid, stale_days)

            elif statuses.get(bid, {}).get("status") == "done":
                # PHANTOM_DONE: blocker is done but dispatcher hasn't picked up
                category = "PHANTOM_DONE"
                msg = (
                    f"{category}  {tid!r:50s} ← {bid!r:50s}  "
                    f"stale={stale_for_days}d  "
                    f"(blocker is done; dispatcher should pick up on next /boot)"
                )
                findings.append(
                    {
                        "category": category,
                        "task_id": tid,
                        "blocker_id": bid,
                        "stale_days": stale_for_days,
                    }
                )
                if not quiet:
                    print(msg)
                # PHANTOM_DONE is info-only — no Slack alert, dispatcher handles it

            else:
                # DEADLOCK: both tasks are queued with unmet prereqs
                category = "DEADLOCK"
                msg = (
                    f"{category}    {tid!r:50s} ← {bid!r:50s}  "
                    f"stale={stale_for_days}d  "
                    f"(both queued, mutual or chain block)"
                )
                findings.append(
                    {
                        "category": category,
                        "task_id": tid,
                        "blocker_id": bid,
                        "stale_days": stale_for_days,
                    }
                )
                if not quiet:
                    print(msg)
                if not dry_run:
                    _alert_deadlock(tid, bid, stale_days)

    # Write daily summary
    if not dry_run and findings:
        date_str = now.strftime("%Y-%m-%d")
        summary_path = summary_dir / f"reap_{date_str}.log"
        with summary_path.open("a", encoding="utf-8") as f:
            f.write(f"\n=== reap_stale_blockers run {now.isoformat()} ===\n")
            for finding in findings:
                f.write(
                    f"{finding['category']}  {finding['task_id']}  "
                    f"<- {finding['blocker_id']}  stale={finding['stale_days']}d\n"
                )

    if not quiet:
        n = len(findings)
        cats = {}
        for f in findings:
            cats[f["category"]] = cats.get(f["category"], 0) + 1
        cat_str = "  ".join(f"{k}={v}" for k, v in sorted(cats.items()))
        print(
            f"\nreap_stale_blockers: {n} finding(s) across {len(task_map)} tasks  "
            f"{cat_str if cat_str else '(all clean)'}"
        )

    return 1 if any(f["category"] in ("DEADLOCK", "ORPHAN") for f in findings) else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backlog",
        type=Path,
        default=Path(os.environ.get("ORCH_BACKLOG_YAML", str(_DEFAULT_BACKLOG))),
        help=f"Path to backlog.yaml (default: {_DEFAULT_BACKLOG})",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path(os.environ.get("ORCH_STATE_DB", str(_DEFAULT_DB))),
        help=f"Path to SQLite state.db (default: {_DEFAULT_DB})",
    )
    parser.add_argument(
        "--stale-days",
        type=int,
        default=int(os.environ.get("REAP_STALE_DAYS", str(_DEFAULT_STALE_DAYS))),
        help=f"Days before a queued task with unmet prereqs is considered stale (default: {_DEFAULT_STALE_DAYS})",
    )
    parser.add_argument(
        "--summary-dir",
        type=Path,
        default=Path(tempfile.gettempdir()),
        help="Directory for daily summary log (default: system temp dir)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print findings; skip Slack + summary write")
    parser.add_argument("--quiet", action="store_true", help="Suppress stdout output")
    args = parser.parse_args(argv)

    return run(
        backlog_path=args.backlog,
        db_path=args.db,
        stale_days=args.stale_days,
        summary_dir=args.summary_dir,
        dry_run=args.dry_run,
        quiet=args.quiet,
    )


if __name__ == "__main__":
    sys.exit(main())
