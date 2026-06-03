---
title:
  "Central orchestrator API host (i-0c9b283b31d6b5ca7) chronic StatusCheckFailed_Instance — intermittent impairment all
  day 2026-05-29; reboot is workaround"
created: 2026-05-29
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
priority: P2
status: active
parent_epic: orchestrator_master
estimate_calibrated_ai_days: 0.8
estimate_class: infra
---

> **🔄 VERIFICATION 2026-06-01 (harsh) — KEEP OPEN; plan covered the defensive layer only.** The
> `api_host_chronic_impairment_2026_05_29` plan (16/16) shipped the workarounds: MemoryMax=56G cgroup cap
> (agent-orchestrator@057f860), auto-reboot Lambda + ceiling (deployment-service@c8fc73d), httpx usage-poller
> (agent-orchestrator@ad28879), watchdog. **4 root-cause items from this issue are NOT in that plan and remain open:**
> (1) identify + fix the memory-exploding pytest test (the actual 32–57 GB OOM source); (2) add ≥16 GB swap; (3) move
> QG/pytest off the central host onto dedicated VMs; (4) SQLite `PRAGMA busy_timeout=30000` 2-line fix. Host no longer
> wedges the OS, but the underlying pytest blow-up is untouched. (Ikenna-owned doc — flagging, not rewriting.)

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

**Key observation**: Memory usage is LOW — only 2.6 GB of 63 GB used (4%). Swap is NOT configured. If usage climbs over
63 GB, OOM killer fires immediately (no swap buffer). This is the critical risk path.

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

No swap activity. IO mostly idle after initial boot. CPU 95-97% idle. Context switches 13k-15k/s (moderate for 16 vCPUs
running 8 worker slots).

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

Top memory consumers: python3 orchestrator (570 MB RSS / 0.9%), each claude worker slot ~330-570 MB RSS (0.5%). Load
average 5.72/8.07/3.84 on 16 vCPUs = 36-50% saturation. No zombie processes.

### `journalctl -u orchestrator --since "10 min ago" | wc -l`

```
763
```

~76 log lines/min. Moderate volume; not alarming in absolute terms but worth watching under load.

### `pgrep -af claude | wc -l`

```
7
```

Active at snapshot time: 4 claude worker processes (slot 4) + 3 bash helper processes. VIRT shows 70.4 GB per claude
process (maps shared node/electron libs) but RSS is only ~330-570 MB each — actual memory is fine.

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

This is a **fresh post-reboot baseline** (41 min uptime). Memory, FDs, disk, and TCP sockets are all healthy. The
impairments occur hours into uptime, not immediately — consistent with a gradual accumulation problem.

**Revised hypothesis ranking** (post Phase 1 data):

| #   | Hypothesis                                                            | Assessment                                                                                                               |
| --- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| 1   | Claude-spawn-based usage poller accumulating processes/RSS over hours | **STILL PRIME SUSPECT** — 4 visible claude processes even at 41 min; at 6h uptime with ~24 spawns/min that's ~86k spawns |
| 2   | No swap — OOM kill is immediate when memory fills                     | **Risk amplifier** — not root cause, but means even brief spike is fatal                                                 |
| 3   | Kernel/network-stack wedge under I/O load                             | Less likely given low wa% baseline, but can't rule out                                                                   |
| 4   | Disk fill                                                             | **Unlikely** — 127 GB free                                                                                               |

**Recommended next steps**: Implement Phase 2 watchdog to capture state during next impairment event, and Phase 3 poller
replacement to eliminate subprocess churn.

---

## Phase 2 Evidence — EC2 Console Output Forensics

**Captured**: 2026-05-29T15:31Z by slot-10 (agent) **Command**:
`aws ec2 get-console-output --instance-id i-0c9b283b31d6b5ca7 --latest --region ap-northeast-1`

### Key findings

- **Captured boot**: `2026-05-29T14:49:58Z` — the reboot initiated at 14:28Z, instance up by 14:49Z (~21s kernel boot).
- **No OOM-killer entries**: no `Out of memory: Killed process` messages anywhere in the console output.
- **No kernel panics**: no `Kernel panic`, `BUG:`, `OOPS:`, or `general protection fault` messages.
- **No hardware faults**: RAS collector initialized normally (`RAS: Correctable Errors collector initialized`), no MCE
  (Machine Check Exceptions), no NVMe errors, no ECC corrections.
- **Clean systemd boot**: `orchestrator.service` and `nginx.service` both reached `[OK]` state.
- **SSM Agent auth error at boot** (`14:50:00Z`): "no valid credentials could be retrieved for ec2 identity" — expected,
  because the IAM instance profile was not yet attached at boot time. SSM Agent registered successfully at `15:15:15Z`
  once the IAM profile propagated.
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

The console output covers the last reboot (14:49Z) through 15:31Z with no anomalies. **No kernel-level root cause is
evident.** The `StatusCheckFailed_Instance` failures are NOT caused by OOM-killer, kernel panic, or hardware errors.
This confirms a **userspace soft-hang**: the process table / FD / memory pressure accumulates until the kernel network
stack becomes unresponsive to EC2 ARP/ICMP health checks — but the kernel itself never panics or invokes the OOM-killer.
The damage threshold is below the kernel-kill threshold.

This is the expected pattern for Hypothesis #1 (claude-spawn-based usage poller churn): gradual accumulation over hours,
not an acute event that leaves a kernel breadcrumb. Console output will never catch it — only the Phase 2 watchdog
(capturing `pgrep`, `free`, FD counts every 60s) will show the accumulation curve in real time.

**Combined Phase 1 + Phase 2 conclusion**: Both independent forensic sources point to the same root cause. Phase 3
(replace claude-spawn poller with direct Anthropic API call) is the correct fix.

---

## Phase 1 Amendment — Kernel Journal OOM Evidence (CRITICAL: root cause correction)

**Captured**: 2026-05-29T15:32Z by slot-5 (agent) — reading systemd journal directly on-host **Source**:
`journalctl --since "today" 2>/dev/null | grep -E "oom|OOM|Killed process|memory peak"`

### OOM killer events confirmed in kernel journal

All four StatusCheckFailed_Instance impairment windows correspond to OOM-killer events in the kernel journal:

| Time (UTC) | Trigger | Killed process      | anon-RSS    | cgroup               |
| ---------- | ------- | ------------------- | ----------- | -------------------- |
| 03:27:12   | cron    | pytest (PID 595124) | **32.3 GB** | orchestrator.service |
| 03:38:00   | apport  | pytest (PID 595782) | **57.6 GB** | orchestrator.service |
| 09:14:00   | python  | python (PID 129050) | **36.1 GB** | orchestrator.service |
| 12:19:09   | git     | pytest (PID 130766) | **38.6 GB** | orchestrator.service |

Raw kernel messages (examples):

```
03:27:13 kernel: Out of memory: Killed process 595124 (pytest) total-vm:36800608kB, anon-rss:33841248kB, ...
03:38:00 kernel: Out of memory: Killed process 595782 (pytest) total-vm:63368744kB, anon-rss:57641324kB, ...
09:14:00 kernel: Out of memory: Killed process 129050 (python) total-vm:38593612kB, anon-rss:36084188kB, ...
12:19:09 kernel: Out of memory: Killed process 130766 (pytest) total-vm:42510856kB, anon-rss:38607828kB, ...
```

Systemd service accounting at each shutdown:

```
03:27:21 orchestrator.service: Consumed 7h 7min 58.884s CPU time, 59.5G memory peak
03:38:04 orchestrator.service: Consumed 7min 51.030s CPU time, 59.6G memory peak
09:14:04 orchestrator.service: Consumed 52min 28.858s CPU time, 60.5G memory peak
12:19:17 orchestrator.service: Consumed 24min 5.366s CPU time, 60.5G memory peak
```

The killed processes are in `task_memcg=/system.slice/orchestrator.service` because worker-slot tmux sessions are
children of processes in the orchestrator service cgroup.

### Usage poller: hypothesis INCORRECT

The usage poller actually runs at **interval=1800s (30 minutes)**, not every 10 seconds. Per journal:

```
14:33:22 UsagePoller started (interval=1800s)
14:33:52 usage refresh: spawning claude in ... (render_floor=3.0s)
14:34:05 usage refresh: captured 17836 raw chars → parsed session=23% weekly=12%
14:34:05 usage refresh: spawning claude (account 2)
14:34:18 captured → spawning claude (account 3)
14:34:31 captured → spawning claude (account 4)
```

Total per cycle: 4 sequential claude spawns over ~52 seconds every 30 minutes. Each claude process uses ~340 MB RSS.
Peak during poll cycle: ~1.4 GB additional RSS for 52 seconds. This is **not** the root cause.

### Actual root cause: quality-gate pytest on worker slots consuming 32-57 GB

Worker slots (tmux sessions, children of orchestrator cgroup) run quality-gate scripts that invoke `pytest`. Some test
suite (likely loading large financial data fixtures or accumulating data in memory during a long test run) grows to
32-57 GB RSS before the OOM killer fires.

The causal chain:

1. Worker agent runs `bash scripts/quality-gates.sh` → pytest invoked
2. pytest loads large test data / has a memory leak in a test fixture
3. pytest RSS reaches 32-57 GB → OS OOM threshold
4. OOM killer fires; during page-table teardown of 57 GB process, kernel stalls briefly
5. EC2 hypervisor ARP/ICMP health check times out → `StatusCheckFailed_Instance`
6. `orchestrator.service: Failed with result 'oom-kill'` (collateral — pytest was in the cgroup)
7. systemd restarts orchestrator → usage poller runs 4 claude spawns → 1.4 GB spike → second OOM minutes later (03:27 →
   03:38)

### Phase 3 recommendation: AMEND

Phase 3 (replace usage poller) is **still worth doing** (reduces subprocess count, cleaner code), but it will NOT fix
the impairment. The OOM root cause is pytest test memory usage, not the usage poller.

**Required fixes**:

1. **Phase 5 (MemoryMax)** — priority must be elevated from P1 to P0. Setting `MemoryMax=56G` on orchestrator.service
   caps the entire cgroup (all worker slots + pytest included) at 56 GB. OOM kills the service cleanly rather than
   wedging the OS network stack. This alone prevents StatusCheckFailed_Instance.
2. **Identify the memory-exploding pytest tests** — find which test file loads 32-57 GB and fix the fixture or mock the
   large data dependency. Check test files loading parquet/GCS data without streaming.
3. **Add swap (at minimum 16 GB)** — gives the OOM killer a buffer before firing. A 57 GB pytest run on a 63 GB machine
   with 0 swap has no margin. Even 16 GB swap buys time for the watchdog to detect and `systemctl stop`.
4. **Worker slots should run QG on dedicated VMs** — the central orchestrator host is not designed to absorb 60 GB
   pytest runs alongside the dispatch service. Worker slots for code-heavy repos should run on vm-cross-cutting or
   vm-cefi, not the central API host.

---

## Phase 2 Supplement — SQLite Lock Contention as Secondary Failure Indicator

**Captured**: 2026-05-29T15:40Z by slot-5 (agent) — `journalctl --boot -2` analysis **Context**: Boot -2 ran
08:48Z-13:07Z and had OOM events at 09:14Z and 12:19Z (see Phase 1 Amendment above).

### Boot History (complete)

```
IDX  FIRST ENTRY              LAST ENTRY               Duration
 -4  2026-05-19T15:56Z  →  2026-05-22T14:38Z           ~3 days
 -3  2026-05-22T14:38Z  →  2026-05-29T08:48Z           ~7 days (OOM x2: 03:27Z, 03:38Z)
 -2  2026-05-29T08:48Z  →  2026-05-29T13:07Z           ~4.3 h  (OOM x2: 09:14Z, 12:19Z)
 -1  2026-05-29T14:33Z  →  2026-05-29T14:48Z           15 min  (clean, operator rebooted again)
  0  2026-05-29T14:49Z  →  running                     ~47 min (healthy baseline)
```

### SQLite DB Lock (boot -2, 12:55Z-13:07Z)

After the 12:19Z OOM event (pytest), the boot -2 boot continued running. At 12:55Z (journal time, actual error
~12:46-47Z) a secondary failure appeared:

```
python3[243726]: ERROR: TmuxPruner tick failed (continuing)
  server/tmux_pruner.py:198 prune_once() → session.scalars()
  → conn.exec_driver_sql("BEGIN IMMEDIATE")
  → sqlite3.OperationalError: database is locked
```

Repeated 3 times with growing gaps (12:55Z → 12:59Z → 13:07Z journal time). The python3 log messages show a ~9-minute
buffer delay (python3 logged at 12:46Z, journald received at 12:55Z) — consistent with the python3 event loop being
blocked/hung for 9 minutes.

**Preceding entry (12:44Z)**: `CredsEnvPoller: download failed ... TimeoutExpired(['aws', 's3', 'cp', ...], 60)`

### Interpretation

The SQLite "database is locked" errors are a **secondary consequence** of the OOM event at 12:19Z:

- After the 12:19Z OOM kill, systemd restarted orchestrator
- During restart, some transaction was left in an inconsistent state (RESERVED lock not released)
- OR a long-running async task (CredsEnvPoller S3 download, 60s timeout) was mid-transaction
- `TmuxPruner.prune_once()` and other callers fail with `BEGIN IMMEDIATE` → "database is locked"
- The Python asyncio event loop backs up; journald buffer fills (9-minute delay)
- Last journal entry at 13:07:46Z → boot ended

**Root note**: `server/db.py` does NOT set `PRAGMA busy_timeout`. Default SQLite busy timeout is 5s. After an
OOM-induced restart with a stuck lock, 5s is insufficient. **Adding `PRAGMA busy_timeout=30000` is a 2-line fix that
prevents cascading DB failures after a partial restart**.

### EC2 Console Output (confirmed by slot-10 + slot-5)

Both slots verified: no OOM-killer entries in EC2 console output (console only shows current healthy boot). Journal is
the authoritative source for OOM evidence (see Phase 1 Amendment above).

**Watchdog installation status**: `NoNewPrivs=1` prevents `sudo` in Claude Code workers. Operator must run:
`bash scripts/install-orch-watchdog.sh --operator ubuntu --start` directly on the host.

---

## Phase 2 Watchdog — Healthy-Window Manual Snapshot

**Captured**: 2026-05-29T15:40:43Z by slot-5 — uptime 50 min post-reboot, status `ok` **Note**: Timer not yet installed
(requires operator sudo). Manual run via modified LOG_DIR=/tmp/orch-watchdog.

```
=== free -m ===
               total        used        free      shared  buff/cache   available
Mem:           63255        2817       53949           3        7214       60438
Swap:              0           0           0

=== vmstat 1 3 ===
 r  b   swpd     free   buff  cache  si so   bi   bo    in     cs us sy id wa
 0  0      0 55213484 3922816 3465056  0  0 1793  315  2260      4  1  1 95  3
 0  0      0 55226684 3922824 3465056  0  0    0   56  4926  19912  5  1 95  0
 1  0      0 55247400 3922824 3465060  0  0    0    0  3953  16463  4  1 95  0

=== top (top 5 by %MEM) ===
  PID  RSS      %MEM  COMMAND
56101  582 MB   0.9%  python3 (orchestrator)
65983  379 MB   0.6%  claude  (slot worker)
65779  376 MB   0.6%  claude  (slot worker)
66151  373 MB   0.6%  claude  (slot worker)
66336  372 MB   0.6%  claude  (slot worker)

=== pgrep -af claude ===
4 active claude workers; 0 zombie processes

=== /proc/sys/fs/file-nr ===
1529   0   9223372036854775807   (1529 FDs open — healthy)

=== ss -tan | wc -l ===
57   (healthy)

=== df -h ===
/dev/root   290G  163G  127G  57%  /
```

**Key observation**: At 50 min into the current healthy boot, total RSS = ~2.8 GB (orchestrator 582 MB + 4 claude
workers ~375 MB each = ~2.1 GB). All metrics healthy. Memory growth of ~40 MB/slot over 50 min extrapolates to only ~288
MB/slot over 6 hours — not the OOM driver. Root cause remains the pytest fixture (Phase 1 Amendment).

---

## Phase 3 Evidence Appendix — Usage Poller Code Audit (2026-05-29T15:35Z)

**Captured by**: slot-9 (task api_host_chronic_impairment-006) **Note**: Slot-5's OOM evidence above corrects the
primary root cause. Phase 3 replacement is still worthwhile (cleaner code, eliminates pexpect PTY overhead), but will
not alone fix impairments.

### Files audited

- `server/usage_poller.py` — `UsagePoller` class (background thread)
- `server/usage_tracker.py` — `fetch_usage_via_claude()` (pexpect spawn logic)
- `server/server.py:179` — instantiation + interval config

### Findings

**1. Class + interval**

`UsagePoller` (daemon thread, serialized via `_USAGE_REFRESH_LOCK`). Interval controlled by
`ORCHESTRATOR_USAGE_POLL_INTERVAL_MINUTES` env var; default **30 minutes**. NOT set in `.env.local` on this host →
default 30 min applies. Startup settle delay: min(interval_seconds, 30) = **30 seconds**.

**2. Spawn mechanism**

`fetch_usage_via_claude()` calls `pexpect.spawn("bash", ["-c", f"source {env_file}; exec claude"])`. Key points:

- New PTY session (`setsid` implicit via pexpect) — child gets its own process group.
- 4 accounts, sequential (one at a time, serialized). Three have `oauth_token_env_file`; `ikenna-backup` is skipped (no
  env file). Per-spawn wall time: ~13 s. Full tick: ~39–52 s.
- Actual confirmed from journal at 15:20:13Z startup: 4 probes ran at 15:20:13, 15:20:27, 15:20:40, 15:20:53 — gaps of
  13–14s (intra-cycle sequential spacing). The "every ~10s" in the issue doc referred to this intra-cycle spacing, NOT a
  standalone short poll interval. Full tick rate: 4 spawns per 30 min = **0.13 spawns/min**.

**3. Reaping lifecycle**

```python
finally:
    with contextlib.suppress(Exception):
        child.send("\x1b")    # ESC — dismiss any modal
        time.sleep(0.2)
        child.kill(15)         # SIGTERM to direct child (bash exec'd to claude)
    with contextlib.suppress(Exception):
        child.close(force=True)  # closes PTY master → SIGHUP to session group
                                  # + os.waitpid() on direct child
```

The `finally` block ALWAYS runs (even on exception). The `contextlib.suppress(Exception)` on each step is defensive —
failures are silenced. `close(force=True)` calls `os.waitpid()` on the **direct** child (claude) but NOT on
grandchildren.

**4. Orphan risk vector — node.js grandchildren**

`exec claude` replaces bash with the Claude CLI (Python). The CLI spawns node.js for its TUI. When `child.kill(15)`
sends SIGTERM to claude:

- Claude (Python) exits promptly → repaped by pexpect's `os.waitpid()` → no zombie.
- Node.js grandchild: receives SIGHUP when PTY master closes (pexpect's `close(force=True)`). If node.js handles or
  ignores SIGHUP, it becomes an orphan reparented to PID 1.
- `close(force=True)` does NOT wait for node.js — only for claude (the direct child).

**Risk assessment**: At 0.13 spawns/min (4 per 30-min cycle), any node.js orphan accumulates at most 0.13/min. Over 6 h
uptime = ~48 potential orphans. Each node.js process is ~80–120 MB RSS. 48 × 100 MB = ~4.8 GB potential leak — secondary
contributor, not the primary cause per OOM evidence above (which shows pytest consuming 32-57 GB as the primary driver).

**5. "render_floor" is NOT an orphan source**

`render_floor` in the log message corresponds to `render_seconds=3.0` — the minimum drain time after sending `/usage\r`
before the code starts scanning for "Resets" markers. It is NOT a hard timeout that cuts off cleanup. The `finally`
block always runs regardless of `render_seconds`.

**6. No evidence of premature SIGKILL**

pexpect's `close(force=True)` sends SIGKILL only if the child is still running after a timeout (default 5s). Given each
probe exits in ~13s and SIGTERM is sent at the end, the child is almost certainly already dead by `close(force=True)`.
No SIGKILL evidence in logs.

### Conclusion for Phase 3

Replacing `fetch_usage_via_claude` with a direct HTTP call eliminates all pexpect PTY spawns. The replacement (task
api_host_chronic_impairment-007) should:

- Use `httpx` (already in requirements) to call the Anthropic usage/limits API directly.
- Verify the same fields (`weekly_pct`, `session_pct`) are recoverable from the API response.
- Add a test that no `pexpect` / subprocess is invoked during a poll cycle. Primary fix remains Phase 5 (MemoryMax) per
  OOM evidence.
