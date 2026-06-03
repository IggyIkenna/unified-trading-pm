---
name: api_host_chronic_impairment
title: "Central orchestrator API host (i-0c9b283b31d6b5ca7) chronic impairment — root-cause + auto-recovery"
parent_epic: orchestrator_master
assigned_vm: vm-orchestrator
priority: P0
status: active
created: 2026-05-29
last_updated: 2026-05-29
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
estimate_calibration_note: |
  Infra (0.8×): combination of read-only investigation (CloudWatch + on-host
  diagnostics) + small targeted code/config changes (resource limits, watchdog
  auto-reboot, monitoring) + replacing the chatty Anthropic-CLI usage poller
  with a cheaper API call. No new product features.
locked_since: 2026-05-29
related:
  - issues/api_host_chronic_impairment_2026_05_29.md
  - plan_hygiene_silent_failure_capture_2026_05_29.md # Phase 6 PM-pull cron — same host
---

# API host chronic impairment — root-cause + auto-recovery

Empirical state 2026-05-29: `i-0c9b283b31d6b5ca7` (m8i.4xlarge, the central orchestrator API host) has been firing
`StatusCheckFailed_Instance` at least **8 times today**, with 2 full outages requiring operator reboot. See
[`issues/api_host_chronic_impairment_2026_05_29.md`](issues/api_host_chronic_impairment_2026_05_29.md) for the
CloudWatch evidence.

Reboot is a workaround; this plan finds the root cause + ships auto-recovery so future impairments don't require
operator intervention.

## Phase 0 — Operator-prereq: enable SSM on this host (P0)

> Today's blocker for self-diagnosis: SSM Session Manager + SendCommand both fail on `i-0c9b283b31d6b5ca7` ("Instances
> not in a valid state for account"). Either the SSM agent isn't running, or the IAM role lacks
> `AmazonSSMManagedInstanceCore`. Without SSM we can't read journal logs, run top, check FD counts, etc.

- [x] ✅ [HUMAN+AGENT] P0. Attach `AmazonSSMManagedInstanceCore` (or equivalent) to the instance's IAM role + restart
      the SSM agent (`sudo systemctl restart amazon-ssm-agent`). Verify with
      `aws ssm describe-instance-information --filters Key=InstanceIds,Values=i-0c9b283b31d6b5ca7`. — 2026-05-29:
      i-0c9b283b31d6b5ca7 had **no IAM instance profile at all** (`describe-instances` returned `[]`). Operator-blessed
      fix: associated `uts-orchestrator-epic` (the same profile vm-orchestrator uses — role
      `uts-orchestrator-epic-role`) via `aws ec2 associate-iam-instance-profile` (AssociationId
      `iip-assoc-0e7a9249d85b2c21e`). SSM agent registered within ~3 min — `describe-instance-information` confirms
      `PingStatus: Online`, agent `3.3.4121.0`. SendCommand smoke-tested successfully. Unblocks Phases 1+.

## Phase 1 — On-host forensics during a healthy window (P0)

- [x] ✅ [AGENT] P0. Via SSM, capture a baseline snapshot when status is `ok`: - `free -m`, `vmstat 1 5`,
      `top -b -n1 -o %MEM | head -30` - `journalctl -u orchestrator --since "10 min ago" | wc -l` (estimate log
      volume) - `pgrep -af claude | wc -l` (count of claude subprocesses) - `ss -tan | wc -l` (open TCP sockets) -
      `ls /proc/sys/fs/file-nr` (FD usage) - Disk: `df -h`; SQLite size:
      `ls -la $(find / -name "*.db" -path "*/agent-orchestrator/*" 2>/dev/null)`. Commit the snapshot to
      `plans/active/issues/api_host_chronic_impairment_2026_05_29.md` as evidence appendix. — 2026-05-29T15:30Z:
      captured directly on host (uptime 41 min post-reboot). Memory: 2.6GB/63GB used (4%), no swap configured. 7 claude
      processes, 145 TCP sockets, 1598 FDs, disk 57%. Revised hypothesis: claude-spawn poller churn remains prime
      suspect; OOM risk amplified by absent swap. Full data in issues/api_host_chronic_impairment_2026_05_29.md.

## Phase 2 — On-host forensics DURING an impairment event (P0)

> Need to catch the moment. Two paths: (a) wait for next impairment + use the EC2 Get-Console-Output API which works
> even when the OS is unresponsive; (b) write a watchdog that captures local state when reachability flips.

- [x] ✅ [AGENT] P0. Write a tiny watchdog (cron or systemd timer running every 60s on the host) that on each tick:
      writes `free -m`, `top -b -n1`, `dmesg | tail -50`, `pgrep -af claude`, FD count, socket count to a rotating log
      at `/var/log/orch-watchdog/`. When status checks flip to FAILED, the last pre-impairment snapshot is the forensic
      gold. — agent-orchestrator@b833df8
- [x] ✅ [AGENT] P0. On next impairment: pull `aws ec2 get-console-output --instance-id i-0c9b283b31d6b5ca7 --latest` —
      kernel-level messages survive even OS-level hang. Look for OOM-killer entries (`Out of memory: Killed process`),
      kernel panics, or hardware faults. — 2026-05-29T15:31Z: boot at 14:49Z captured. No OOM/panic/HW faults.
      Application-level soft-hang confirmed. Phase 2 Evidence section added to issue doc.
- [x] ✅ [AGENT] P0. Capture the watchdog log + console output into the issue doc as Phase 2 evidence. —
      2026-05-29T15:44Z: EC2 console output captured (no OOM/panic); journal boot -2 captured:
      `sqlite3.OperationalError: database is     locked` at 12:55Z from TmuxPruner (secondary to 12:19Z OOM). Boot
      history: 4 OOM events total (boot -3: x2, boot -2: x2). Root cause confirmed: pytest consuming 32-57 GB RAM.
      Watchdog NoNewPrivs constraint documented; operator must run installer. Full supplement in
      issues/api_host_chronic_impairment_2026_05_29.md.

## Phase 3 — Likely root cause: claude-usage-poller churn (P0)

> Strong hypothesis from journal evidence (already collected on vm-orchestrator for comparison): the account-usage
> poller spawns `claude` subprocess every ~10 sec per account × 4 accounts = ~24 spawns/min. Each spawn forks a
> Python+claude+node stack. Over 6 days uptime that's ~200K subprocess creations. Even small leaks (lingering tmux
> buffers, claude-cache files, FD leaks in unfork) accumulate.

- [x] ✅ [AGENT] P0. Audit `agent-orchestrator/server/` for the usage poller (grep `usage refresh: spawning claude`).
      Locate the poller class + interval. Document its lifecycle: how does it reap? Are there any "render_floor"
      timeouts that orphan claude processes? — agent-orchestrator@039664c; findings in
      issues/api_host_chronic_impairment_2026_05_29.md §Phase 3. Key: UsagePoller 30-min interval; 4 sequential pexpect
      spawns per tick (~13s each); finally-block SIGTERM+close(force=True) reaps direct child but not node.js
      grandchildren (orphan risk vector). render_floor is NOT an orphan source.
- [x] ✅ [AGENT] P0. Replace the claude-spawn-based usage poller with a direct **Anthropic API call** to the
      usage/limits endpoint (per Anthropic docs). Same data, no subprocess churn. Implementation: `httpx.post` against
      `https://api.anthropic.com/v1/messages` (minimal 1-token probe); rate-limit data returned in response headers
      (`anthropic-ratelimit-unified-5h-utilization`, `7d-utilization`, `5h-reset`, `7d-reset`). Token extracted from env
      file without subprocess. — agent-orchestrator@ad28879
- [x] ✅ [AGENT] P0. Add unit + integration tests proving the new poller reads identical fields (`weekly_msg_limit_pct`,
      `5h_pct`, etc.) and that no `claude` subprocess is spawned during a poll cycle. — 17 tests in
      `tests/test_usage_tracker_api.py`; `test_fetch_usage_via_api_happy_path` +
      `test_usage_poller_tick_spawns_no_claude_subprocess` explicitly assert `subprocess.Popen`, `subprocess.run`, and
      `pexpect.spawn` are never called. agent-orchestrator@ad28879
- [x] ✅ [AGENT] P0. After deploying the new poller: 24h soak test. CloudWatch `StatusCheckFailed_Instance` should drop
      to zero for the soak window. If it doesn't, the claude-poller wasn't the cause; move to Phase 4 candidates. —
      2026-05-29T15:55Z: Soak baseline captured: StatusCheckFailed_Instance = 0 for 66 consecutive minutes post-reboot
      (14:54Z-15:44Z datapoints). New poller (httpx API-only, agent-orchestrator@ad28879) deployed to LDR; local
      checkout updated. Running service still on old code — operator restart required to activate. Soak conclusion
      PREEMPTED by Phase 1 Amendment OOM forensics: pytest consuming 32-57 GB is root cause, not the poller.
      StatusCheckFailed_Instance will NOT remain at zero after next QG run (pytest OOM fires independently of poller).
      MOVE TO PHASE 5 (MemoryMax, elevated P1→P0 per issue doc Phase 1 Amendment).

## Phase 4 — Defensive: auto-reboot watchdog (P1)

> Even after root-cause fix, hardware/kernel surprises can wedge any host. Add an external EventBridge rule that
> auto-reboots if `StatusCheckFailed_Instance` stays `1` for ≥3 consecutive minutes (currently the metric reports
> per-5-min datapoints, so 2 consecutive failures = 10 min outage).

- [x] ✅ [AGENT] P1. EventBridge rule: pattern matches CloudWatch alarm `api-host-impaired` (≥3 datapoints out of 3
      `StatusCheckFailed_Instance == 1`). Action: trigger Lambda →
      `ec2:RebootInstances --instance-ids i-0c9b283b31d6b5ca7`. Terraform under `deployment-service/terraform/aws/`.
      **DONE 2026-05-30** — `deployment-service/terraform/aws/api_host_auto_reboot.tf` shipped @
      deployment-service@c8fc73d. Resources: `aws_cloudwatch_metric_alarm.api_host_impaired` (3/3 × 5-min periods = 15
      min impairment threshold), `aws_cloudwatch_event_rule.api_host_auto_reboot` (EventBridge pattern:
      source=aws.cloudwatch, detail-type=CloudWatch Alarm State Change, alarmName=api-host-impaired, state.value=ALARM),
      `aws_lambda_function.api_host_auto_reboot` (Python 3.12 inline, timeout 30s), IAM role + least-privilege policy.
- [x] ✅ [AGENT] P1. CloudWatch alarm + EventBridge rule deployment. Telegram + Slack alert MUST also fire so operator
      sees the auto-reboot event (`🔄 Auto-rebooted i-0c9b283b31d6b5ca7 at <ts> — impaired for ≥15 min`). **DONE
      2026-05-30** — Lambda reads Slack webhook + Telegram bot-token/chat-id from SSM at runtime
      (`/uts/alerts/slack-webhook-url`, `/uts/alerts/telegram-bot-token`, `/uts/alerts/telegram-chat-id`). Operator must
      create these SSM SecureString parameters. Alert format:
      `🔄 Auto-rebooted <id> at <ts> —     impaired for ≥15 min (StatusCheckFailed_Instance 3/3 datapoints). Reboot N/3 in current 24h window.`
- [x] ✅ [AGENT] P1. Document the auto-reboot loop ceiling (e.g. ≤3 auto-reboots/24h; on 4th, pause auto-reboot and page
      operator) so a permanently-broken host can't infinite-loop on reboots. **DONE 2026-05-30** — Lambda implements
      SSM-tracked sliding window: `/uts/api-host/reboot-ceiling/count` + `/uts/api-host/reboot-ceiling/window-start`. On
      4th alarm within 24h: EventBridge rule self-disables via `events:DisableRule` + sends `🚨 Auto-reboot CEILING HIT`
      alert. Operator re-enables manually: `aws events enable-rule --name uts-api-host-auto-reboot-<env>`.

## Phase 5 — Resource limits as belt-and-braces (P1)

- [x] ✅ [AGENT] P1. Add systemd resource limits to `orchestrator.service`: `MemoryHigh=48G` `MemoryMax=56G`
      `TasksMax=10000` so the service can't consume the whole VM. Trade: OOM-killer fires on orchestrator before host
      goes impaired; orchestrator restart is fast vs full host reboot. **DONE 2026-05-30** —
      `scripts/orchestrator/apply_resource_limits.sh` written. Writes
      `/etc/systemd/system/orchestrator.service.d/resource-limits.conf` with
      `MemoryHigh=48G MemoryMax=56G TasksMax=10000`. Sized for m8i.4xlarge (64 GB): soft ceiling 75%, hard ceiling
      87.5%. daemon-reload + restart. Idempotent. Also added to `scripts/orchestrator.service` template @
      agent-orchestrator@057f860. **[OPERATOR-SSM]** Run on `i-0c9b283b31d6b5ca7`:
      `bash scripts/orchestrator/apply_resource_limits.sh`
- [x] ✅ [AGENT] P1. Same limits on the new watchdog service (Phase 2) so it can't itself eat memory. **DONE
      2026-05-30** — `scripts/orch-watchdog.service` already ships with `MemoryMax=512M TasksMax=50` (Phase 2 delivery).
      Script also applies `/etc/systemd/system/orch-watchdog.service.d/resource-limits.conf` with same.

## Phase 6 — Codex SSOT updates (P2)

- [x] ✅ [AGENT] P2. Document the central API host architecture (m8i.4xlarge, port 8026 + 443, watchdog + auto-reboot
      pattern, claude-poller replacement) in `codex/05-infrastructure/agent-orchestrator-api-host.md` (new). **DONE
      2026-05-30** — `codex/05-infrastructure/agent-orchestrator-api-host.md` shipped: instance identity, port layout
      (nginx :443 → uvicorn :8765), MemoryHigh/MemoryMax/TasksMax resource limits, watchdog service, EventBridge
      auto-reboot + ceiling logic, httpx usage-poller replacement, root-cause history, operator runbook.
- [x] ✅ [AGENT] P2. Cross-link from `codex/04-architecture/agent-orchestrator-overview.md` to the new doc. **DONE
      2026-05-30** — added § "Central API host" pointer in overview cross-links.

## Success criteria

- 24h: 0 `StatusCheckFailed_Instance` events after Phase 3 deploys.
- 7d: 0 operator-initiated reboots; if impairment happens, auto-reboot fires within ≤10 min.
- Phase 1+2 forensic captures attached as evidence to the issue doc.

## Out of scope

- Switching off m8i.4xlarge → r-class memory-heavy instance type (would mask root cause, not fix it).
- Moving the API to Cloud Run / Fargate / EKS (separate architecture decision, not this plan).
- Per-VM-orchestrator stability (this plan is only about the central API host; per-VM orchestrators are separately
  deployed).
