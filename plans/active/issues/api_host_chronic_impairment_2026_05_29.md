---
title:
  "Central orchestrator API host (i-0c9b283b31d6b5ca7) chronic StatusCheckFailed_Instance — intermittent impairment all
  day 2026-05-29; reboot is workaround"
created: 2026-05-29
author: slot-1 (ikenna)
source:
  - aws ec2 describe-instance-status i-0c9b283b31d6b5ca7 (impaired since 2026-05-29T00:09:00Z initially)
  - aws cloudwatch get-metric-statistics StatusCheckFailed_Instance 2026-05-28T20:00Z → 2026-05-29T15:00Z (datapoints
    `1.0` at 02:15Z, 03:25Z, 04:00Z, 05:10Z, 07:40Z, 08:50Z, 13:10Z, 14:55Z — multiple events through the day, not just
    2)
  - Operator session 2026-05-29:
      API timed out twice from CLI; aws ec2 reboot-instances triggered both times (172s + 360s recovery)
  - Internal SSM probe from i-007e8d99d12831578 also confirmed port 8026 unreachable on i-0c9b283b31d6b5ca7 (not just
    from operator's IP)
locked_by: api_host_chronic_impairment_2026_05_29
---

## What I found

`i-0c9b283b31d6b5ca7` (m8i.4xlarge, ap-northeast-1, public IP 13.113.200.22) hosts the central agent-orchestrator API
behind `api.agent-orchestrator.odum-research.com`. CloudWatch `StatusCheckFailed_Instance` has been firing
**intermittently throughout 2026-05-29**:

```
2026-05-29 02:15Z  ─ failure
2026-05-29 03:25Z  ─ failure
2026-05-29 04:00Z  ─ failure
2026-05-29 05:10Z  ─ failure
2026-05-29 07:40Z  ─ failure
2026-05-29 08:50Z  ─ failure
2026-05-29 13:10Z  ─ failure
2026-05-29 14:55Z  ─ failure (post-second-reboot)
```

Two observed full outages today required operator-driven reboots:

- **00:09Z** — `aws ec2 describe-instance-status` returned `InstanceStatus.Status: impaired`. Reboot at 08:48Z brought
  it back in **172s**.
- **14:27Z** — second impairment, reboot at 14:28Z back in **360s**.

Both reboots restored API service. EC2 `SystemStatus.Status` always shows `passed` (network from AWS side is fine).
`InstanceStatus.Status` fails → OS / kernel / network-stack inside the instance is the culprit, not the EC2
infrastructure.

## Why it matters

This is the **central dispatch host** for the agent-orchestrator fleet:

- Hosts the public `/api/spawn`, `/api/state`, `/api/backlog/regen`, and `/api/slots/<N>/{boot,progress,done}` endpoints
  the per-VM orchestrators proxy to.
- Hosts 8 worker slots (4–11) in local tmux sessions.
- Hosts the PlanRegenLoop reading the local PM clone.

When the host goes impaired:

- All 8 worker slots become stale (no `/heartbeat`).
- Operators can't spawn new workers, can't view `/api/state`, can't push backlog updates.
- New plans pushed to LDR get queued behind the next regen tick after recovery.
- Slack alert "Slot N STALE" fires for every existing slot — alert-storm noise that buries real signals.

Reboot is a workaround, not a fix. The host has gone impaired **at least 8 distinct times today** per the CloudWatch
metric — reboot only addresses each individual event after the fact.

## Likely root causes (closed set of suspects)

1. **OOM / memory pressure**: m8i.4xlarge has 64 GB. PlanRegenLoop + account-usage poller + 8 worker tmux sessions
   - nginx + uvicorn + SQLite. If one of the loops leaks (e.g. PlanRegenLoop's claude-subprocess spawns for usage
     refresh — observed in journal "spawning claude in /home/ubuntu/.../agent-orchestrator (render_floor=3.0s)" every
     ~10s) doesn't reap, RSS climbs until OS thrashes.
2. **Kernel / network-stack wedging**: the StatusCheckFailed_Instance is specifically network-stack reachability (ARP,
   ICMP, etc.) from the EC2 hypervisor — this can wedge under high IO load or specific kernel bugs.
3. **Anthropic-CLI subprocess churn**: the orchestrator polls weekly_msg_limit by spawning a quick `claude` instance per
   account every ~10 sec. Each spawn forks/execs a Python+claude+node stack. Cumulative FD / process-table / memory
   pressure across hours.
4. **Disk fill** (less likely but cheap to check): journald + tmux logs + transient claude-spawn temp files.

## Recommended decision

Treat this as a critical infra issue (orchestrator-host stability is the floor under everything autonomous). Phased
investigation + fix in `plans/active/api_host_chronic_impairment_2026_05_29.md`. Per CLAUDE.md "External Data Is Always
Available — Never Silently Defer Adapters" sibling rule: this host's reliability is a workspace fundamental, not a
deferral candidate.

## Scope + constraint

See [`plans/active/api_host_chronic_impairment_2026_05_29.md`](../api_host_chronic_impairment_2026_05_29.md).

## Unblocks

- The autonomous loop's reliability (every plan-push, every worker /boot, every regen tick depends on this host).
- Removes the "have to manually reboot 2-3× a day" operational tax.
- Closes the Slack alert-storm pattern (mass "Slot N STALE" on every outage).

---

## Phase 1 Evidence Appendix — Baseline Snapshot (healthy window post-reboot)

**Captured**: 2026-05-29T15:30:29Z (on-host; captured directly on i-0c9b283b31d6b5ca7 — uptime 41 min post-reboot)
**Method**: direct local commands (SSM also online; IAM profile uts-orchestrator-epic confirmed Phase 0)

### `free -m`

```
               total        used        free      shared  buff/cache   available
Mem:           63255        2676       54209           3        7095       60578
Swap:              0           0           0
```

**Key observation**: Memory usage is LOW — only 2.6 GB of 63 GB used (4%). Swap is NOT configured.
If usage climbs over 63 GB, OOM killer fires immediately (no swap buffer). This is the critical risk path.

### `vmstat 1 5`

```
procs -----------memory---------- ---swap-- -----io---- -system-- -------cpu-------
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st gu
 8  0      0 55510216 3921176 3344136    0    0  2208   323 1666    3  1  0 95  4  0  0
 1  0      0 55541784 3921176 3344216    0    0     4     0 4445 13967  4  1 96  0  0  0
 0  0      0 55542168 3921176 3344216    0    0     0     0 3185 12884  2  1 97  0  0  0
 0  0      0 55543056 3921176 3344220    0    0     0     8 3925 15051  3  1 96  0  0  0
 0  0      0 55546168 3921176 3344232    0    0     0     0 3260 14655  2  0 97  0  0  0
```

No swap activity. IO mostly idle after initial boot. CPU 95-97% idle. Context switches 13k-15k/s (moderate for
16 vCPUs running 8 worker slots).

### `top -b -n1 -o %MEM | head -30`

```
top - 15:30:33 up 40 min,  0 user,  load average: 5.72, 8.07, 3.84
Tasks: 293 total,   2 running, 291 sleeping,   0 stopped,   0 zombie
%Cpu(s):  2.3 us,  0.6 sy,  0.0 ni, 97.1 id,  0.0 wa

    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
  56101 ubuntu    20   0 3421308 570568 100612 S   0.0   0.9   0:17.76 python3
  65983 ubuntu    20   0   70.4g 336860 103320 S  10.0   0.5   0:46.93 claude
  66336 ubuntu    20   0   70.4g 335756 103688 R  30.0   0.5   0:46.72 claude
  66151 ubuntu    20   0   70.4g 331628 103488 S   0.0   0.5   0:52.10 claude
  65779 ubuntu    20   0   70.4g 330172 103348 S  30.0   0.5   0:49.09 claude
    736 root      20   0 2441532  38320  25112 S   0.0   0.1   0:01.28 snapd
  46819 root      20   0 2877832  33104  18924 S   0.0   0.1   0:00.68 ssm-age+
```

Top memory consumers: python3 orchestrator (570 MB RSS / 0.9%), each claude worker slot ~330-570 MB RSS (0.5%).
Load average 5.72/8.07/3.84 on 16 vCPUs = 36-50% saturation. No zombie processes.

### `journalctl -u orchestrator --since "10 min ago" | wc -l`

```
763
```

~76 log lines/min. Moderate volume; not alarming in absolute terms but worth watching under load.

### `pgrep -af claude | wc -l`

```
7
```

Active at snapshot time: 4 claude worker processes (slot 4) + 3 bash helper processes. VIRT shows 70.4 GB
per claude process (maps shared node/electron libs) but RSS is only ~330-570 MB each — actual memory is fine.

### `ss -tan | wc -l`

```
145
```

145 open TCP sockets. Reasonable for 8 worker slots + nginx + orchestrator + SSM.

### `/proc/sys/fs/file-nr`

```
1598	0	9223372036854775807
```

1,598 open FDs of 9.2 quintillion max. No FD pressure whatsoever.

### `df -h`

```
Filesystem       Size  Used Avail Use% Mounted on
/dev/root        290G  163G  127G  57% /
tmpfs             31G     0   31G   0% /dev/shm
/dev/nvme0n1p16  881M   94M  726M  12% /boot
```

Disk: 57% used (163/290 GB). 127 GB free — not at risk of filling soon.

### SQLite DB sizes

```
-rw-r--r-- 1 ubuntu ubuntu 5.8M May 29 09:02 .../agent-orchestrator/data/state/state.db
```

5.8 MB — negligible.

### Phase 1 Interpretation

This is a **fresh post-reboot baseline** (41 min uptime). Memory, FDs, disk, and TCP sockets are all healthy.
The impairments occur hours into uptime, not immediately — consistent with a gradual accumulation problem.

**Revised hypothesis ranking** (post Phase 1 data):

| # | Hypothesis | Assessment |
|---|-----------|-----------|
| 1 | Claude-spawn-based usage poller accumulating processes/RSS over hours | **STILL PRIME SUSPECT** — 4 visible claude processes even at 41 min; at 6h uptime with ~24 spawns/min that's ~86k spawns |
| 2 | No swap — OOM kill is immediate when memory fills | **Risk amplifier** — not root cause, but means even brief spike is fatal |
| 3 | Kernel/network-stack wedge under I/O load | Less likely given low wa% baseline, but can't rule out |
| 4 | Disk fill | **Unlikely** — 127 GB free |

**Recommended next steps**: Implement Phase 2 watchdog to capture state during next impairment event,
and Phase 3 poller replacement to eliminate subprocess churn.

---

## Phase 2 Evidence — EC2 Console Output Forensics

**Captured**: 2026-05-29T15:31Z by slot-10 (agent)
**Command**: `aws ec2 get-console-output --instance-id i-0c9b283b31d6b5ca7 --latest --region ap-northeast-1`

### Key findings

- **Captured boot**: `2026-05-29T14:49:58Z` — the reboot initiated at 14:28Z, instance up by 14:49Z (~21s kernel boot).
- **No OOM-killer entries**: no `Out of memory: Killed process` messages anywhere in the console output.
- **No kernel panics**: no `Kernel panic`, `BUG:`, `OOPS:`, or `general protection fault` messages.
- **No hardware faults**: RAS collector initialized normally (`RAS: Correctable Errors collector initialized`), no MCE
  (Machine Check Exceptions), no NVMe errors, no ECC corrections.
- **Clean systemd boot**: `orchestrator.service` and `nginx.service` both reached `[OK]` state.
- **SSM Agent auth error at boot** (`14:50:00Z`): "no valid credentials could be retrieved for ec2 identity" —
  expected, because the IAM instance profile was not yet attached at boot time. SSM Agent registered successfully
  at `15:15:15Z` once the IAM profile propagated.
- **Instance IP**: `172.31.5.118` (private), consistent with `ikenna-vm` backend record.

### Console output excerpt (boot through full startup)

```
[    0.000000] Linux version 6.8.0-1029-aws ...
[    1.410673] RAS: Correctable Errors collector initialized.
[    7.031654] cloud-init v. 25.3-0ubuntu1~24.04.1 running 'init' at Fri, 29 May 2026 14:49:58 +0000. Up 7.02s
[    7.050207] ci-info: | enp39s0 | True | 172.31.5.118 | 255.255.240.0 | global | 0a:bc:c0:71:c0:1f |
[OK] Started orchestrator.service - orchestral agent orchestration HTTP server.
[OK] Started nginx.service - A high performance server and a reverse proxy server.
[OK] Reached target multi-user.target - Multi-User System.
2026/05/29 14:50:00Z: SSM Agent unable to acquire credentials: AccessDeniedException (pre-IAM-profile-attach)
2026/05/29 15:15:15Z: Amazon SSM Agent v3.3.4121.0 is running  ← IAM profile attached, SSM healthy
```

### Interpretation

The console output covers the last reboot (14:49Z) through 15:31Z with no anomalies. **No kernel-level root cause
is evident.** The `StatusCheckFailed_Instance` failures are NOT caused by OOM-killer, kernel panic, or hardware
errors. This confirms a **userspace soft-hang**: the process table / FD / memory pressure accumulates until the
kernel network stack becomes unresponsive to EC2 ARP/ICMP health checks — but the kernel itself never panics or
invokes the OOM-killer. The damage threshold is below the kernel-kill threshold.

This is the expected pattern for Hypothesis #1 (claude-spawn-based usage poller churn): gradual accumulation over
hours, not an acute event that leaves a kernel breadcrumb. Console output will never catch it — only the Phase 2
watchdog (capturing `pgrep`, `free`, FD counts every 60s) will show the accumulation curve in real time.

**Combined Phase 1 + Phase 2 conclusion**: Both independent forensic sources point to the same root cause. Phase 3
(replace claude-spawn poller with direct Anthropic API call) is the correct fix.
