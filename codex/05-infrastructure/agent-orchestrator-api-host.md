---
doc_type: codex-ssot
title: agent-orchestrator — central API host architecture
summary:
  Central API host architecture for agent-orchestrator (EC2 i-0c9b283b31d6b5ca7, 13.113.200.22) — nginx :443 to uvicorn
  :8765 (in-process tmux slots on this same VM — no per-VM fleet backends), systemd resource limits, the orch-watchdog
  forensic snapshots, the resource-watchdog kill-guardian + resource-history-sampler historical RAM/CPU/disk trend log
  (with exact "how far back does our RAM history go / who caused a spike" query recipes — this host is NOT covered by
  the fleet-wide `deployment_operational_data.resource_samples` BigQuery table, which is deployment-service-launched VMs
  only), EventBridge+Lambda auto-reboot with a sliding-24h reboot ceiling, and the httpx (no-subprocess) usage poller.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, deployment-service]
scope: [engineer]
tags:
  [orchestrator, infrastructure, aws, ec2, monitoring, self-healing, nginx, resource-history, resource-watchdog, oom]
related:
  [
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/05-infrastructure/agent-orchestrator-deploy.md,
    /codex/05-infrastructure/deployment-observability.md,
    /plans/archive/2026_08/watchdog_kill_events_deployment_observability_2026_08_05.md,
  ]
created: 2026-05-30
authoritative_for:
  [
    agent-orchestrator central API host (systemd limits + watchdog + auto-reboot),
    where to find this host's historical RAM/CPU/disk data and how far back it goes,
  ]
referenced_by:
  [
    /codex/05-infrastructure/agent-orchestrator-deploy.md,
    /codex/05-infrastructure/agent-orchestrator-slack-notifications.md,
  ]
owner:
last_reviewed: 2026-08-05
code_refs:
author: ikenna-claude-subagent
---

# agent-orchestrator — central API host architecture

> **SSOT**: this document. Related: `/codex/04-architecture/agent-orchestrator-overview.md` § "Deployment shape" + §
> "Connectivity model".

---

## Host identity

| Field           | Value                                                       |
| --------------- | ----------------------------------------------------------- |
| Instance ID     | `i-0c9b283b31d6b5ca7`                                       |
| Instance type   | `m8i.4xlarge` (16 vCPU, 64 GB RAM)                          |
| Region          | AWS `ap-northeast-1`                                        |
| Public IP       | `13.113.200.22`                                             |
| Public hostname | `api.agent-orchestrator.odum-research.com`                  |
| IAM profile     | `uts-orchestrator-epic` (role `uts-orchestrator-epic-role`) |
| SSM status      | Online, agent `3.3.4121.0` (registered 2026-05-29)          |

---

## Port layout

```
Client (browser)
        │ HTTPS :443
        ▼
nginx (TLS termination) — 13.113.200.22
        │ HTTP :8765
        ▼
orchestrator FastAPI backend (uvicorn, listens 127.0.0.1:8765)
        │  in-process
        ▼
N slot workers (tmux orch-slot-N) on the same VM
```

- **:443** — public HTTPS; nginx terminates TLS, proxies to backend at :8765.
- **:8765** — orchestrator uvicorn, loopback-only (`127.0.0.1`); not reachable from outside.

Slots are in-process tmux sessions on this same VM, not separate hosts (no epic VMs — retired 2026-06-27). Only the
central host has a public TLS endpoint. The `/api/vms/<id>/*` proxy endpoints remain as a single-node degenerate case of
the former multi-VM router.

---

## Systemd service

```
/etc/systemd/system/orchestrator.service
/etc/systemd/system/orchestrator.service.d/resource-limits.conf  ← added 2026-05-30
```

### Resource limits (m8i.4xlarge — 64 GB)

| Directive    | Value  | Rationale                                                 |
| ------------ | ------ | --------------------------------------------------------- |
| `MemoryHigh` | `48G`  | 75 % ceiling — kernel starts reclaiming pages above this  |
| `MemoryMax`  | `56G`  | 87.5 % hard cap — OOM-killer fires on service, not host   |
| `TasksMax`   | 10 000 | Prevents thread/FD exhaustion from unbounded worker churn |

These limits ensure that a rogue process (e.g. runaway pytest) OOM-kills the orchestrator process — a fast restart —
rather than wedging the entire EC2 instance and triggering a StatusCheckFailed reboot cycle.

Apply (idempotent): `bash scripts/orchestrator/apply_resource_limits.sh` via SSM.

---

## Watchdog service (`orch-watchdog`)

A systemd timer running every 60 s on the host captures a forensic snapshot to `/var/log/orch-watchdog/`:

- `free -m`, `top -b -n1`, `dmesg | tail -50`
- `pgrep -af claude` (subprocess count)
- FD count (`/proc/sys/fs/file-nr`), TCP socket count (`ss -tan`)

When a StatusCheckFailed event fires, the last pre-impairment log entry is the forensic gold — available even if the OS
hangs and the normal journal becomes unreadable.

| Watchdog resource limit | Value  |
| ----------------------- | ------ |
| `MemoryMax`             | `512M` |
| `TasksMax`              | `50`   |

Service unit: `scripts/orch-watchdog.service`. Install: `bash scripts/install-watchdog.sh` via SSM.

> **NoNewPrivs constraint**: the watchdog's `NoNewPrivileges=true` drops `sudo`/`suid` — this means `dmesg` may return
> `Operation not permitted` on kernels with `kernel.dmesg_restrict=1`. The snapshot is still valuable for the
> application-level metrics. Operator must install the service manually (SSM SendCommand) because systemd unit
> installation requires root and the orchestrator process itself runs as a non-root user.

---

## Resource watchdog (`resource-watchdog`)

Cross-process resource guardian deployed 2026-08-05 after two back-to-back OOM incidents where agent-spawned
`exec(eval(sys.stdin.readline()))` Python processes ballooned to 26 GB + 27.7 GB RSS, consuming the entire orchestrator
cgroup (`MemoryMax=56G` — see § "Resource limits" above) and causing a 3× crash-loop. Implementation history:
`/plans/archive/2026_08/resource_watchdog_host_guardian_2026_08_05.md` (archived 2026-08-06, all todos shipped).

A systemd service (`resource-watchdog.service`, `After=orchestrator.service`) polls every 10 seconds and kills
non-allowlisted processes exceeding per-resource thresholds:

| Dimension | Normal pressure (cgroup < 80%)       | High pressure (cgroup ≥ 80%)   |
| --------- | ------------------------------------ | ------------------------------ |
| RSS       | 10 GB                                | 4 GB                           |
| CPU       | >95 % of one core, sustained 10+ min | _(same — not pressure-scaled)_ |
| Swap      | >4 GB per process                    | _(same — not pressure-scaled)_ |

**Allowlist**: Processes matching `orchestrator`, `uvicorn`, `resource-watchdog`, `pytest`, `prek`, `ruff`,
`basedpyright`, `mypy`, `npm`, `vitest`, `tsc` are never killed (quality-gates + infrastructure).

**Kill feedback loop**: Before killing, the watchdog writes a marker file to
`/dev/shm/resource-watchdog/kills/{pid}.json` (tmpfs) and POSTs to the orchestrator's internal API
(`POST /api/resource-watchdog/kill`). The orchestrator relays the kill event to the owning slot via its next
`/heartbeat` response so the agent knows NOT to re-spawn the killed workload — "offload to a spot VM."

**Diagnosing a silent kill from inside an interactive per-slot sandbox (found 2026-08-10)**: a slot's own container
cannot `sudo grep /var/log/syslog` (blocked by the container's "no new privileges" flag) and `dmesg`/`journalctl -k`
return genuinely empty (no host-kernel visibility at all from inside the container, not just a permissions gap) — both
are dead ends for kill diagnosis from an interactive session, as opposed to an AO-dispatched worker loop that receives
the relay via its own `/heartbeat`. The reliable channel from inside the sandbox is reading
`/dev/shm/resource-watchdog/kills/<pid>.json` directly (world-readable) — it is also more complete than a syslog line
(structured `rss_mb`/`limit_mb`/`pressure_level`/`reason` fields). The absence of a traceback in a crashed process's
captured stdout/stderr (vs. a genuine Python exception, which always prints one) is the tell that a silent exit was a
kill, not a code bug, and is worth checking for the marker before assuming either.

**Dual-write to deployment-api (additive, 2026-08-05)**: In addition to the existing AO-internal POST above, the
watchdog also POSTs each kill event to deployment-api's `POST /api/fleet/watchdog/kill-events` ingest route
(`_rw_notify_deployment_api()` in `resource-watchdog.sh`, opt-in via `RW_DEPLOYMENT_API_URL` env var). This second write
is fire-and-forget (does not block the enforcement loop) and streams into BigQuery
`deployment_operational_data.watchdog_kill_events` — the same durable-operational-data surface as `reap_events` and
`idle_spend`. This **supersedes** the Phase-4 AO-UI-only scope for kill events specifically: the AO dashboard's own
kill-status panel stays, but kill events are now ALSO visible in deployment-ui's per-VM resource-comparison page
(`VmResourceComparison.tsx` expandable-row panel) via `GET /api/watchdog/kill-events`. Table schema:
`ts TIMESTAMP, vm_name STRING, pid INT64, slot_id STRING, command STRING, reason STRING, rss_mb INT64, limit_mb INT64, pressure_level STRING, killed BOOL`.
Full design: `/plans/archive/2026_08/watchdog_kill_events_deployment_observability_2026_08_05.md`; read path:
`/codex/05-infrastructure/deployment-observability.md` § "Durable operational data — watchdog_kill_events".

**Installation**: Bootstrap step 4.8 in `agent-orchestrator/scripts/bootstrap_vm.sh`. Self-healing liveness check in
`ao-self-pull.sh` (every ~15 min). Service unit:
`unified-trading-pm/scripts/infra/resource-watchdog/resource-watchdog.service`. Script:
`/usr/local/bin/resource-watchdog.sh` (deployed from PM repo).

**Logs**: `journalctl -u resource-watchdog` or the raw file `/var/log/resource-watchdog.log` (one line per poll tick +
one `VIOLATION`/`KILL` line per event — this is the per-incident "which exact process, what threshold, was it killed"
audit trail). Kill snapshots (full `ps`/cmdline capture at kill time) at `/var/log/snapshots/kill_*.txt`.

> **Gap found 2026-08-05, fixed same day**: this service was deployed 2026-08-05, so `/var/log/resource-watchdog.log`
> and the kill snapshots by construction had no history before that date, and — unlike the resource-history sampler
> below — neither was mirrored off-VM nor logrotated, on a host already at ~80% local disk. Fixed via
> `gcs_sync.upload_resource_watchdog_log_to_gcs/_to_s3` + `upload_resource_watchdog_snapshots_to_gcs/_to_s3` (rides the
> existing `resource-history-backup.timer`, no new systemd unit) + `resource-watchdog.logrotate` (14d local rotation)
>
> - `resource-watchdog-snapshots.tmpfiles.conf` (14d age-out) + standalone `install-resource-watchdog-retention.sh`
>   (applies to an already-running VM; `bootstrap_vm.sh` Step 4.8 covers future VM builds).

---

## Resource history sampler — this host's RAM/CPU/disk/swap trend log

Answers "how has this host's RAM/CPU/disk actually trended over the last N days" — **NOT** the same question the
resource watchdog above answers (which single process got killed and why, right now). Do not confuse the two, and do not
confuse either with `deployment-observability.md`'s `deployment_operational_data.resource_samples` BigQuery table — that
table is fleet-wide but **scoped to deployment-service-launched VMs only** (backfill/live-data workers launched via
`deployment-service/scripts/vm/`); it has **zero rows for this central API host**, confirmed live via `bq query`
2026-08-05 (`vm_name`/`service` filtered for this instance and for `%orchestrator%` returned empty, while the same query
against the fleet's own VM names returns thousands of rows/day). If you need this host's history, the three sources
below are the only ones that have it.

**Primary source — `resource-history-sampler.service`** (`ao_resource_history_externalize_2026_07_30`): standalone
systemd unit (deliberately NOT an in-process orchestrator thread — survives `ao-self-pull.sh`'s restart of
`orchestrator.service` on every upstream commit landing on `live-defi-rollout`, observed every ~15-25 min while the
fleet is shipping, and survives a genuine OOM-kill of the orchestrator itself). Samples CPU/RAM/disk/swap/iowait every 5
seconds via `server/resource_history.py`'s `ResourceHistoryLoop`, appending to one JSONL file per day:
`agent-orchestrator/data/state/resource_history/YYYY-MM-DD.jsonl` (~9 MB/day). Running continuously since 2026-07-31 —
as of 2026-08-05 that's already 6 days of local history and growing; no pruning cron found for the data dir, so old
daily files are not deleted automatically (at ~9 MB/day this is not an urgent disk concern, unlike the resource-watchdog
log above). Also mirrored off-VM to GCS/S3 every 10 minutes by the sibling `resource-history-backup.timer`
(`OnBootSec=180`, `OnUnitActiveSec=600`) — durable even if the VM is replaced. Install/redeploy both units together:
`bash scripts/install-resource-history-sampler.sh --operator ubuntu --start`.

**Legacy/superseded — `resource-monitor.sh` bridge cron**: `*/5 * * * * /opt/resource-monitor/resource-monitor.sh`,
appends to `/var/log/resource-monitor/resource-monitor.jsonl` (load/cpu-jiffies/mem/swap + top-8-by-%CPU processes),
self-trims to the last 8640 lines (~30 days at 5-min cadence). Its own header comment says it is explicitly "a bridge
until the AO-integrated version lands" — that version (`resource-history-sampler.service` above) landed 2026-07-31 and
has been stable for 6+ days as of this writing, so this cron is now a retirement candidate (not yet removed as of
2026-08-05; `deployment-observability.md` § "Known gaps" still references it as the safety net for a different,
unrelated timer that failed to autostart — check that note is still current before deleting this cron).

**Query recipes** (read-only; no dashboard JWT needed — same SSM Session Manager pattern as
`check-ao-backlog-status.sh`, see that script's header for the auth rationale):

```bash
# RAM/CPU/disk trend for the last week, from this host's own sampler (primary source):
aws ssm send-command --instance-ids i-0c9b283b31d6b5ca7 --region ap-northeast-1 \
  --document-name AWS-RunShellScript --parameters commands='[
    "cd /home/ubuntu/unified-trading-system-repos/agent-orchestrator/data/state/resource_history && \
     for f in $(ls *.jsonl | tail -7); do echo \"== $f ==\"; \
     python3 -c \"import json,sys; [print(l.strip()) for i,l in enumerate(open(sys.argv[1])) if i%720==0]\" \"$f\"; done"
  ]' --query 'Command.CommandId' --output text
# (samples every 720th line ~= hourly points from the 5s-cadence file; drop the %720 filter for full-resolution)

# What got killed in the last N hours and why (resource-watchdog audit trail):
aws ssm send-command --instance-ids i-0c9b283b31d6b5ca7 --region ap-northeast-1 \
  --document-name AWS-RunShellScript --parameters commands='[
    "sudo grep -E \"VIOLATION|KILL\" /var/log/resource-watchdog.log | tail -100"
  ]' --query 'Command.CommandId' --output text

# Current + historic-peak cgroup memory for orchestrator.service (56 GiB hard cap):
aws ssm send-command --instance-ids i-0c9b283b31d6b5ca7 --region ap-northeast-1 \
  --document-name AWS-RunShellScript --parameters commands='[
    "cat /sys/fs/cgroup/system.slice/orchestrator.service/memory.current /sys/fs/cgroup/system.slice/orchestrator.service/memory.peak"
  ]' --query 'Command.CommandId' --output text
```

Then poll
`aws ssm get-command-invocation --command-id <id> --instance-id i-0c9b283b31d6b5ca7 --region ap-northeast-1 --query StandardOutputContent --output text`
until `Status` is `Success` (same pattern as `check-ao-backlog-status.sh`).

---

## Auto-reboot: EventBridge + Lambda

Shipped at `deployment-service@c8fc73d` under `deployment-service/terraform/aws/api_host_auto_reboot.tf`.

### CloudWatch alarm

```
aws_cloudwatch_metric_alarm.api_host_impaired
  Metric: StatusCheckFailed_Instance
  Instance: i-0c9b283b31d6b5ca7
  Threshold: ≥ 1
  Period: 300 s (5 min)
  Evaluation periods: 3 / 3
  → triggers at 15 min of continuous impairment
```

### EventBridge rule

Matches CloudWatch Alarm state-change events for `api-host-impaired` entering `ALARM` state, triggers the Lambda.

### Lambda (`aws_lambda_function.api_host_auto_reboot`)

- Runtime: Python 3.12, timeout 30 s
- Action: `ec2:RebootInstances` on `i-0c9b283b31d6b5ca7`
- Alerts: Slack webhook (`/uts/alerts/slack-webhook-url`) + Telegram bot (`/uts/alerts/telegram-bot-token`,
  `/uts/alerts/telegram-chat-id`); SSM SecureString at runtime.
- Alert format:
  `🔄 Auto-rebooted <id> at <ts> — impaired for ≥15 min (StatusCheckFailed_Instance 3/3 datapoints). Reboot N/3 in current 24h window.`

### Reboot ceiling (prevents infinite-reboot loop)

The Lambda tracks a **sliding 24 h window** via SSM parameters:

| SSM parameter                               | Value stored                       |
| ------------------------------------------- | ---------------------------------- |
| `/uts/api-host/reboot-ceiling/count`        | Number of auto-reboots in window   |
| `/uts/api-host/reboot-ceiling/window-start` | ISO-8601 timestamp of window start |

On the **4th alarm within 24 h**: Lambda self-disables the EventBridge rule (`events:DisableRule`) and sends
`🚨 Auto-reboot CEILING HIT` alert. Operator re-enables manually:

```bash
aws events enable-rule --name uts-api-host-auto-reboot-<env>
```

---

## Usage poller — httpx API replacement

Previously: `UsagePoller` in `server/usage_tracker.py` spawned a `claude` subprocess (via `pexpect`) every 30 min per
account to read usage stats. On a host with 4 accounts that's 4 sequential pexpect spawns per tick (~13 s each). The
direct child was SIGTERM'd in a `finally` block, but Node.js grandchildren could orphan.

**Replacement** (`agent-orchestrator@ad28879`): `UsagePoller` now calls the Anthropic API directly via `httpx`:

- `httpx.post("https://api.anthropic.com/v1/messages", ...)` — minimal 1-token probe
- Rate-limit data from response headers: `anthropic-ratelimit-unified-5h-utilization`,
  `anthropic-ratelimit-unified-7d-utilization`, `5h-reset`, `7d-reset`
- API key extracted from the account's env file — no subprocess required
- Same output fields: `weekly_msg_limit_pct`, `5h_pct`, `7d_pct`, `reset_ts`

**No claude subprocess is spawned during a poll cycle.** `subprocess.Popen`, `subprocess.run`, and `pexpect.spawn` are
all absent from the new poll path — explicitly asserted in
`tests/test_usage_tracker_api.py::test_usage_poller_tick_spawns_no_claude_subprocess`.

Test coverage: 17 unit tests in `tests/test_usage_tracker_api.py`.

---

## Root-cause history (2026-05-29 incident)

The host was firing `StatusCheckFailed_Instance` ≥ 8 times on 2026-05-29 with 2 operator-initiated reboots.

| Phase                      | Finding                                                                                                                                   |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 1 (healthy baseline) | 2.6 GB / 63 GB used (4%), 7 claude processes, 145 TCP sockets, 1598 FDs, disk 57%. No obvious pressure.                                   |
| Phase 2 (boot -2 journal)  | `sqlite3.OperationalError: database is locked` at 12:55Z (secondary to OOM). 4 OOM events across last 3 boots (boot -3: ×2, boot -2: ×2). |
| Console output             | No kernel OOM-killer entries, no panics, no hardware faults. Application-level soft-hang.                                                 |
| Root cause                 | **pytest consuming 32–57 GB RAM** — QG runs during plan regen or CI triggered on this host exhaust memory.                                |
| claude-spawn poller        | Originally suspected; poller replaced (Phase 3) but StatusCheckFailed was confirmed as pytest-OOM, not poller-churn.                      |

Evidence archive: `plans/active/issues/api_host_chronic_impairment_2026_05_29.md`.

---

## Operator runbook (quick reference)

### Apply resource limits (first-time or after service reinstall)

```bash
# Via SSM SendCommand on i-0c9b283b31d6b5ca7
aws ssm send-command \
  --instance-ids i-0c9b283b31d6b5ca7 \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["bash /home/ubuntu/unified-trading-system-repos/agent-orchestrator/scripts/orchestrator/apply_resource_limits.sh"]'
```

### Check auto-reboot ceiling state

```bash
aws ssm get-parameters-by-path --path /uts/api-host/reboot-ceiling/ --with-decryption
```

### Re-enable auto-reboot after ceiling hit

```bash
aws events enable-rule --name uts-api-host-auto-reboot-prod   # adjust env suffix
# Also reset the ceiling counter:
aws ssm put-parameter --name /uts/api-host/reboot-ceiling/count --value "0" --overwrite
aws ssm put-parameter --name /uts/api-host/reboot-ceiling/window-start --value "" --overwrite
```

### Verify SSM reachability

```bash
aws ssm describe-instance-information \
  --filters Key=InstanceIds,Values=i-0c9b283b31d6b5ca7 \
  --query 'InstanceInformationList[0].{Status:PingStatus,Agent:AgentVersion}'
```

---

## SSM parameters required (operator must provision)

| Parameter path                   | Type         | Value                      |
| -------------------------------- | ------------ | -------------------------- |
| `/uts/alerts/slack-webhook-url`  | SecureString | Slack incoming webhook URL |
| `/uts/alerts/telegram-bot-token` | SecureString | Telegram bot token         |
| `/uts/alerts/telegram-chat-id`   | SecureString | Telegram chat ID           |

---

## Related systems

| System                                                                  | Interaction                                                                                                                                  |
| ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `nginx`                                                                 | TLS termination, :443 → :8765 proxy; config on the host                                                                                      |
| `orch-watchdog.service`                                                 | 60 s timer; forensic snapshots to `/var/log/orch-watchdog/`                                                                                  |
| `resource-watchdog.service`                                             | 10 s poll; kills non-allowlisted processes exceeding RSS/CPU/swap limits. Relays kills to agents via orchestrator API so they don't re-spawn |
| `orchestrator.service`                                                  | Main FastAPI backend; uvicorn on :8765                                                                                                       |
| `deployment-service/terraform/aws/api_host_auto_reboot.tf`              | CloudWatch alarm + EventBridge + Lambda                                                                                                      |
| `server/usage_tracker.py`                                               | httpx-based usage poller (no subprocess)                                                                                                     |
| `tests/test_usage_tracker_api.py`                                       | 17-test coverage for new poller                                                                                                              |
| `/codex/04-architecture/agent-orchestrator-overview.md`                 | High-level deployment shape + connectivity model                                                                                             |
| `/codex/05-infrastructure/agent-orchestrator-deploy.md`                 | Historical Cloud Run shape; systemd install script                                                                                           |
| `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` | Topology + dispatch SSOT (single central VM)                                                                                                 |
| `plans/active/issues/api_host_chronic_impairment_2026_05_29.md`         | Full forensic evidence for 2026-05-29 incident                                                                                               |
