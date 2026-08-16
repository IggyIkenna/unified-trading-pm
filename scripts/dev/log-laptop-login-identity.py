#!/usr/bin/env python3
# Epic: orchestrator_master
# Lifecycle: permanent
# Delete-when: NA
"""LAPTOP-ONLY. Appends (timestamp, accountUuid, emailAddress) from ~/.claude.json's
oauthAccount to a local log, only when the identity changes since the last recorded
entry. Evidence that this laptop never logged into an AO-reserved account
(sub-a-ikenna, sub-e-odum3default) during a calibration window.

Source: plans/active/anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md
(LAPTOP-ONLY [OPERATOR] P2 todo).

Usage: run manually before/after a calibration window, or on a cron/launchd schedule:
    python3 scripts/dev/log-laptop-login-identity.py
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

CLAUDE_JSON = Path.home() / ".claude.json"
LOG_PATH = Path.home() / ".claude" / "laptop_login_identity_log.jsonl"


def main() -> int:
    if not CLAUDE_JSON.exists():
        print(f"no {CLAUDE_JSON} found — nothing to log")
        return 1

    data = json.loads(CLAUDE_JSON.read_text())
    oauth = data.get("oauthAccount") or {}
    account_uuid = oauth.get("accountUuid")
    email = oauth.get("emailAddress")
    if not account_uuid:
        print("no oauthAccount.accountUuid in ~/.claude.json — not logged in?")
        return 1

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    last_entry = None
    if LOG_PATH.exists():
        lines = [ln for ln in LOG_PATH.read_text().splitlines() if ln.strip()]
        if lines:
            last_entry = json.loads(lines[-1])

    if last_entry and last_entry.get("accountUuid") == account_uuid and last_entry.get("emailAddress") == email:
        print(f"identity unchanged ({email}) — not appending a duplicate entry")
        return 0

    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "accountUuid": account_uuid,
        "emailAddress": email,
    }
    with LOG_PATH.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"logged identity change: {email} ({account_uuid}) -> {LOG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
