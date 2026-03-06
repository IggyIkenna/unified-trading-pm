# Audit Reflog — Scheduled Job & Alerts

Weekly check for unintended `git reset --hard` or `reset to origin/main` across all workspace repos. Alerts via macOS notification when high-risk resets are found.

## Script locations

| Item                       | Path                                                                               |
| -------------------------- | ---------------------------------------------------------------------------------- |
| **Audit script**           | `unified-trading-pm/scripts/repo-management/audit-reflog-resets.sh`                |
| **Wrapper (with alert)**   | `unified-trading-pm/scripts/repo-management/run-audit-reflog-with-alert.sh`        |
| **Launchd plist**          | `~/Library/LaunchAgents/com.unified-trading.audit-reflog.plist`                    |
| **Install script**         | `unified-trading-pm/scripts/repo-management/launchd/install-audit-reflog.sh`       |
| **Log**                    | `/tmp/audit-reflog.log`                                                            |
| **Ignore list**            | `unified-trading-pm/scripts/repo-management/audit-reflog-ignore.txt`               |
| **Watch script (fswatch)** | `unified-trading-pm/scripts/repo-management/watch-and-audit-reflog.sh`             |
| **Watch plist**            | `~/Library/LaunchAgents/com.unified-trading.audit-reflog-watch.plist`              |
| **Watch install**          | `unified-trading-pm/scripts/repo-management/launchd/install-audit-reflog-watch.sh` |
| **Watch log**              | `/tmp/audit-reflog-watch.log`                                                      |

## Run manually

```bash
cd /path/to/unified-trading-system-repos
bash unified-trading-pm/scripts/repo-management/run-audit-reflog-with-alert.sh
```

Or audit only (no notification):

```bash
bash unified-trading-pm/scripts/repo-management/audit-reflog-resets.sh
```

## Test notification

```bash
terminal-notifier -title "Audit Reflog" -message "Test: Click to open log" -sound default -execute "open /tmp/audit-reflog.log"
```

## Start the scheduled job

```bash
cd /path/to/unified-trading-system-repos
bash unified-trading-pm/scripts/repo-management/launchd/install-audit-reflog.sh
launchctl load ~/Library/LaunchAgents/com.unified-trading.audit-reflog.plist
```

Runs **every 10 min**.

## Event-based watch (fswatch)

Runs the audit whenever `.git/logs` changes in any workspace repo (commit, reset, checkout, etc.). Uses `fswatch`; install via `brew install fswatch` if needed.

```bash
cd /path/to/unified-trading-system-repos
bash unified-trading-pm/scripts/repo-management/launchd/install-audit-reflog-watch.sh
launchctl load ~/Library/LaunchAgents/com.unified-trading.audit-reflog-watch.plist
```

The watch job runs in the background with `KeepAlive`; it triggers the same wrapper (audit + notification on high-risk). Log: `/tmp/audit-reflog-watch.log`.

**Stop watch job:**

```bash
launchctl unload ~/Library/LaunchAgents/com.unified-trading.audit-reflog-watch.plist
```

## Cancel / stop the job

```bash
launchctl unload ~/Library/LaunchAgents/com.unified-trading.audit-reflog.plist
```

## Check job status

```bash
launchctl list | grep audit-reflog
```

## Solved vs ignore list

**Solved (automatic):** A reset is considered solved if the "lost" commit is now in `origin/main` — either the exact commit was recovered, or the same patch was committed (e.g. cherry-pick). No ignore entry needed.

**Per-commit ignore (intentional discard):** When you intentionally reset and discard work, add the specific commit to `audit-reflog-ignore.txt` as `repo:hash` (e.g. `deployment-api:b103671`). The audit output shows the exact line to add. This keeps the ignore scoped to that commit — future genuine breaches in the same repo will still be detected.

**Legacy:** `repo` only (no colon) = ignore whole repo. Prefer per-commit when possible.

## Implementation notes (for similar notification scripts)

When creating or copying scripts that run audits and show macOS notifications:

| Gotcha                                                                      | Fix                                                                                         |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| **set -e** exits before notification when audit returns 1                   | Use `cmd \|\| exit_code=$?` and `exit_code=0` before; don't let set -e trigger on the audit |
| **launchd** has minimal PATH; `command -v terminal-notifier` fails          | Use full paths: `/opt/homebrew/bin/terminal-notifier` or `/usr/local/bin/terminal-notifier` |
| **Cursor/agent** runs may deliver notifications; user terminal runs may not | Same script works in both; if user sees no alert, check set -e and PATH                     |

Wrapper script: `run-audit-reflog-with-alert.sh` — reference when building similar alert scripts.

## Alert behavior

- **No high-risk resets:** Script exits 0, no notification.
- **High-risk resets found:** Script exits 1, macOS notification with sound. Click to open log.

**Stay until acknowledged:** System Settings → Notifications → terminal-notifier → set delivery style to **Alerts** (not Banners). Alerts stay on screen until dismissed.
