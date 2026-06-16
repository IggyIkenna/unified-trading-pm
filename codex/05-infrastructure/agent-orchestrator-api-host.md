---
title: agent-orchestrator — central API host architecture
created: 2026-05-30
author: ikenna-claude-subagent
scope: [engineer]
status: active
last_reviewed: 2026-05-30
---

# agent-orchestrator — central API host architecture

> **SSOT**: this document. Related: `codex/04-architecture/agent-orchestrator-overview.md` § "Deployment shape" + §
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
Client (browser / worker VM)
        │ HTTPS :443
        ▼
nginx (TLS termination) — 13.113.200.22
        │ HTTP :8765
        ▼
orchestrator FastAPI backend (uvicorn, listens 127.0.0.1:8765)
        │ private VPC (172.31.x.x, ORCHESTRATOR_USE_PRIVATE_URLS=true)
        ▼
Fleet VMs — :8026 (no TLS, private only)
```

- **:443** — public HTTPS; nginx terminates TLS, proxies to backend at :8765.
- **:8765** — orchestrator uvicorn, loopback-only (`127.0.0.1`); not reachable from outside.
- **:8026** — fleet worker VMs only; not open on the central API host.

The API host is a **router, not a worker** — it proxies dashboard requests to per-VM backends over the private VPC.
Workers never have public IPs; only the central host has a public TLS endpoint.

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
  --parameters 'commands=["bash /home/ubuntu/agent-orchestrator/scripts/orchestrator/apply_resource_limits.sh"]'
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

| System                                                          | Interaction                                                 |
| --------------------------------------------------------------- | ----------------------------------------------------------- |
| `nginx`                                                         | TLS termination, :443 → :8765 proxy; config on the host     |
| `orch-watchdog.service`                                         | 60 s timer; forensic snapshots to `/var/log/orch-watchdog/` |
| `orchestrator.service`                                          | Main FastAPI backend; uvicorn on :8765                      |
| `deployment-service/terraform/aws/api_host_auto_reboot.tf`      | CloudWatch alarm + EventBridge + Lambda                     |
| `server/usage_tracker.py`                                       | httpx-based usage poller (no subprocess)                    |
| `tests/test_usage_tracker_api.py`                               | 17-test coverage for new poller                             |
| `codex/04-architecture/agent-orchestrator-overview.md`          | High-level deployment shape + connectivity model            |
| `codex/05-infrastructure/agent-orchestrator-deploy.md`          | Historical Cloud Run shape; systemd install script          |
| `codex/05-infrastructure/agent-orchestrator-worker-topology.md` | Per-VM IP table + fleet topology                            |
| `plans/active/issues/api_host_chronic_impairment_2026_05_29.md` | Full forensic evidence for 2026-05-29 incident              |
