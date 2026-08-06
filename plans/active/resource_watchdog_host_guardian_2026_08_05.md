---
doc_type: plan
title: Resource Watchdog — Host Guardian for Planning VM
summary:
  A persistent daemon that monitors CPU, RAM, and swap for every process in the orchestrator cgroup and kills
  non-allowlisted processes that exceed per-resource thresholds. Addresses the 2026-08-05 OOM incident (two
  exec(eval(stdin)) processes at 26+27 GB RSS each, cgroup hit MemoryMax=54G, orchestrator crash-looped 3 times in 3
  minutes). The QG host governor already handles QG concurrency and self-abort — this watchdog fills the gap for non-QG
  runaway processes spawned by agents.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [watchdog, oom, memory, cpu, swap, planning-vm, host-guardian]
related:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /plans/active/quality_gates_resource_contention_speedup_2026_06_02.md,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
    /plans/active/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md,
    /codex/05-infrastructure/agent-orchestrator-api-host.md,
    /plans/archive/2026_08/watchdog_kill_events_deployment_observability_2026_08_05.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-05"
last_updated: "2026-08-05"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
context_scope:
  [
    scripts/infra/resource-watchdog/resource-watchdog.sh,
    agent-orchestrator/server/routes/resource_watchdog.py,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
  ]
---

# Resource Watchdog — Host Guardian

## Context

**Incident 2026-08-05**: AO backend OOM-killed at 00:40 UTC. Two
`python -c "import sys;exec(eval(sys.stdin.readline()))"` processes at 26 GB + 27.7 GB RSS consumed the entire
orchestrator cgroup (MemoryMax=54G). Orchestrator crash-looped 3 times in 3 minutes. Root cause: agents running
unbounded compute (data loading, feature calculation stubs) on the planning VM instead of a dedicated spot VM.

**QG governor exists but is self-scoped**: `qg-host-governor.sh` handles QG concurrency (token bucket) and self-abort (a
QG run can abort ITSELF when host RAM >80%). It cannot kill OTHER processes — that gap is what this plan fills.

**Design decided in-session** (2026-08-05 interactive session, operator present):

- Two pressure levels gated on cgroup memory
- Allowlist for QG + infrastructure processes
- Multi-resource tracking: RSS, CPU (% of one core, sustained), swap
- Bash implementation (no venv dependency, runs even when Python is broken)
- Standalone systemd service in orchestrator cgroup slice

Codex SSOTs: `/codex/05-infrastructure/vm-launcher-runbook.md` (heavy-I/O rule),
`/codex/05-infrastructure/spot-vms-for-backfill.md` (backfill → spot VM principle).

---

## Design summary

### Pressure-level model

| Level  | Trigger                         | Per-process RSS limit |
| ------ | ------------------------------- | --------------------- |
| Normal | cgroup < 80% MemoryMax (~43 GB) | 10 GB                 |
| High   | cgroup ≥ 80% MemoryMax          | 4 GB                  |

At normal pressure, agents can load a few Parquet files to inspect schema (legitimate). At high pressure, even moderate
processes get clamped.

### Resource thresholds

| Dimension           | Threshold        | Window                       | Source                                                  |
| ------------------- | ---------------- | ---------------------------- | ------------------------------------------------------- |
| RSS (normal)        | 10 GB            | immediate (>30s process age) | `/proc/[pid]/status` VmRSS                              |
| RSS (high pressure) | 4 GB             | immediate (>30s process age) | same                                                    |
| CPU                 | >95% of one core | 10 min sustained             | `/proc/[pid]/stat` utime+stime delta / wall delta × 100 |
| Swap                | >4 GB            | immediate                    | `/proc/[pid]/status` VmSwap                             |
| Disk I/O            | track only       | —                            | `/proc/[pid]/io` read_bytes/write_bytes                 |

Any one dimension trips the kill.

### Allowlist

These processes are NEVER killed: `orchestrator`, `uvicorn`, `resource-watchdog`, `pytest`, `prek`, `ruff`,
`basedpyright`, `mypy`, `npm`, `vitest`, `tsc`.

### Safeguards

- Min process age 30s before enforcement
- Max 1 kill per 60s (rate-limit)
- Snapshot `/proc/[pid]/smaps` + process tree to log before killing
- Never kills PID 1, self, or allowlisted processes

### Kill → Agent feedback loop

Killing a process without telling the agent that spawned it is futile — the agent will just re-spawn it. Three layers of
communication, each a fallback for the next:

**Layer 1 — Orchestrator API relay (primary path):** After killing a process, the watchdog determines which slot owns it
(see slot detection below), then POSTs to the orchestrator's internal API:

```
POST localhost:8765/api/resource-watchdog/kill
{ "pid": 12345, "slot_id": 8, "command": "python -u -c ...",
  "rss_mb": 22400, "limit_mb": 10000, "pressure_level": "normal",
  "reason": "rss", "timestamp": "2026-08-05T07:15:00Z" }
```

The orchestrator stores the event and includes it in the slot's next `/api/slots/{N}/poll` or heartbeat response. The
agent's Claude session reads the kill message and knows: "don't re-spawn this — offload to a spot VM."

**Layer 2 — Marker file (fallback if orchestrator is unreachable):** Before killing, the watchdog writes
`/dev/shm/resource-watchdog/kills/{pid}.json` (tmpfs — no disk I/O, fast). When the agent's subprocess dies
unexpectedly, the agent (or its harness) can check for the marker to discover why. This works even when the orchestrator
is too memory-starved to respond to API calls.

**Layer 3 — Slot detection via `/proc/[pid]/cwd`:** The watchdog determines which slot a PID belongs to by reading
`/proc/[pid]/cwd` and matching `.tabs/(\d+)/`. If the immediate process doesn't match, it walks up the parent chain.
Every process an agent spawns inside its slot tmux session inherits the working directory. No cooperation needed from
the orchestrator or tmux.

### Integration

- **Service**: `resource-watchdog.service` in `system.slice/orchestrator.service/` cgroup
- **Config**: `/etc/resource-watchdog/config.yaml`, version-controlled in
  `unified-trading-pm/scripts/infra/resource-watchdog/`
- **Logs**: journald (`journalctl -u resource-watchdog`) + `/var/log/resource-watchdog.log`
- **Kill markers**: `/dev/shm/resource-watchdog/kills/` (tmpfs, survives no disk I/O)
- **Coexists with** QG governor (different scope: cross-process vs self-abort)

---

## Implementation plan

### Phase 1: Watchdog script + config

- [x] [SCRIPT] P1. Create `unified-trading-pm/scripts/infra/resource-watchdog/resource-watchdog.sh` — the daemon script
      — PM@d1ffdf6b3 + deployed on planning VM
  - Allowlist matching against process command lines (config-driven)
  - RSS reading from `/proc/[pid]/status` VmRSS
  - CPU% computation from `/proc/[pid]/stat` utime+stime delta (as % of one core)
  - Swap reading from `/proc/[pid]/status` VmSwap
  - Disk I/O tracking from `/proc/[pid]/io` (diagnostic only)
  - Cgroup memory pressure reading from `/sys/fs/cgroup/system.slice/orchestrator.service/memory.current`
  - Kill decision logic with two pressure levels (normal: 10 GB, high: 4 GB)
  - Slot detection from `/proc/[pid]/cwd` (match `.tabs/(\d+)/`, walk parent chain)
  - Pre-kill: write marker JSON to `/dev/shm/resource-watchdog/kills/{pid}.json`
  - Pre-kill: snapshot smaps + process tree → log file
  - Post-kill: POST to orchestrator `localhost:8765/api/resource-watchdog/kill`
  - Rate-limit (max 1 kill/60s)
  - SIGTERM → 5s wait → SIGKILL escalation
  - journald integration (log to stderr → captured by systemd)
  - Dry-run mode (`--dry-run`) for testing
  - Self-daemonizing with configurable poll interval (`--interval`, default 10s)

- [x] [SCRIPT] P1. Create `unified-trading-pm/scripts/infra/resource-watchdog/config.yaml` — default config —
      PM@d1ffdf6b3
  - Allowlist patterns, pressure thresholds, resource limits, safeguards, marker dir

- [x] [SCRIPT] P1. Create `unified-trading-pm/scripts/infra/resource-watchdog/resource-watchdog.service` — systemd unit
      — PM@d1ffdf6b3, live on planning VM
  - Same cgroup slice as orchestrator. `Restart=always`. `ExecStart` points at the script.

### Phase 2: Orchestrator kill-relay endpoint

- [x] [SERVICE] P2. Add `POST /api/resource-watchdog/kill` endpoint to `agent-orchestrator/server/server.py` —
      AO@4b696fe (quickmerged), deployed + tested on planning VM
  - Internal-only (localhost or JWT-authenticated)
  - Validates payload, stores kill event in state.db
  - On next slot poll/heartbeat, includes `watchdog_kills` array in response
  - Each entry: `{pid, command, rss_mb, limit_mb, reason, message}` where message is the human-readable instruction ("Do
    not re-spawn. Offload to a spot VM.")

### Phase 3: Deploy + verify

- [x] [INFRA] P3. Deploy to planning VM (`i-0c9b283b31d6b5ca7`) — watchdog running, orchestrator endpoint live, systemd
      service active
  - Copy script + config + unit to VM, `systemctl daemon-reload && systemctl enable --now resource-watchdog`
  - Verify cgroup placement and service status
  - Deploy updated orchestrator with kill-relay endpoint

- [x] [INFRA] P3. Dry-run smoke test — found + flagged PID 2958199 (slot 12, 11.5 GB RSS), allowlist working, slot
      detection working
  - Run with `--dry-run` to confirm process discovery + classification + slot detection
  - Verify allowlisted processes are skipped, non-allowlisted are correctly identified
  - Spawn a memory-hog and confirm it would be flagged + marker would be written + API would be called

- [x] [INFRA] P3. Live verification — killed first violator (slot 12, 13.2 GB RSS), cgroup stable at 13-23 GB, marker +
      snapshot written
  - Switch to live mode, confirm journald output
  - Wait for actual agent workload, confirm no false positives
  - Verify kill → marker → API → agent relay end-to-end

### Phase 4: Hardening (follow-up)

- [x] [SCRIPT] P3. Add Slack alerting for kills (dedup-keyed, cooldown-gated) — AO@quickmerged (slack.py +
      resource_watchdog.py)
- [x] [SCRIPT] P3. Wire watchdog status into AO UI dashboard panel (not deployment-api — operator directed AO UI surface
      only) — AO@quickmerged (ResourceWatchdog.tsx + api.ts + types.ts + App.tsx)
- [x] [SCRIPT] P3. Add status JSON file to watchdog script + `GET /api/resource-watchdog/status` endpoint + `--status`
      flag (already shipped in Phase 1) wired for AO UI consumption — AO@quickmerged + PM@5d23e2779

---

## Design decisions (ruled in-session)

1. **Bash, not Python** — no venv dependency, runs when Python is broken, consistent with QG governor
2. **Separate service, not QG governor extension** — different scope (cross-process vs self-abort), simpler to reason
   about
3. **Configurable allowlist** — version-controlled config file (changes go through PR), validated on startup
4. **CPU measured as % of one core** — process using 200% (2 full cores) also trips the 95% single-core threshold
5. **Swap limit 4 GB** — cgroup has MemorySwapMax=16G; 4 GB per process = 25% of budget, pathological for any single
   process
6. **Disk I/O track-only** — no kill on I/O alone; correlates with RSS growth for post-mortem analysis
7. **Feedback loop via orchestrator API** — watchdog POSTs kill events to the orchestrator, which relays them to the
   agent's slot on next poll/heartbeat, so the agent knows NOT to re-spawn the killed process
8. **Marker files as fallback** — `/dev/shm/resource-watchdog/kills/{pid}.json` survives orchestrator API outages during
   memory pressure
9. **Slot detection via `/proc/[pid]/cwd`** — matches `.tabs/(\d+)/`, walks parent chain; no cooperation needed from
   tmux or the orchestrator

---

## Progress Log

### 2026-08-05 (later session) — RAM-spike investigation, backup/logrotate gap fix, AO-UI-only ruling partially reversed

An interactive-session RAM-spike investigation (operator noticed host RAM at 75%) traced it to this exact watchdog doing
its job: slot 15 ran a bare (unprojected) `read_availability_index()` call twice within a minute (known, still-open
issue `read_availability_index_bare_defi_callers_2026_07_27.md`), RSS hit ~40-42GB each time, the watchdog SIGTERM'd
both — confirming the watchdog IS catching runaway processes live, closing the loop on
`orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md`'s still-unruled `[OPERATOR] P1` mechanical-
enforcement decision (this watchdog is a live instance of that doc's option 1, "bake the bound into the tooling" — the
two docs were never cross-linked until now; not asserting the 4th-recurrence issue's OPERATOR todo is formally resolved,
that's still the operator's call, just noting the concrete evidence for whoever picks it up next).

Two follow-ups from that investigation:

1. **Gap found + fixed**: `/var/log/resource-watchdog.log` and its kill snapshots had zero local rotation and zero
   off-VM backup (deployed same-day, so no history existed before the incident). Fixed via
   `gcs_sync.upload_resource_watchdog_log_to_gcs/_to_s3` + `upload_resource_watchdog_snapshots_to_gcs/_to_s3` (rides the
   existing `resource-history-backup.timer`) + `resource-watchdog.logrotate` (14d local) +
   `resource-watchdog-snapshots.tmpfiles.conf` (14d age-out) + standalone `install-resource-watchdog-retention.sh`.
2. **Phase 4's AO-UI-only ruling (line ~208 below) is being partially reversed, same day, by direct operator instruction
   in the follow-up session**: kill/violation events should ALSO surface through deployment-api/ deployment-ui's
   existing resource-monitoring surfaces, not live only in AO's own world — tracked in
   `/plans/archive/2026_08/watchdog_kill_events_deployment_observability_2026_08_05.md` (+ gated finalize). This doc's
   own Phase-4 checkbox text is left as-is (it accurately records what was decided AT THAT TIME) — this entry is the
   pointer for a future reader who greps that line and would otherwise think AO-UI-only is still the standing decision.

### 2026-08-05 (later session) — Phase 4 hardening

Completed all three hardening items:

- **Slack alerting**: Added `notify_resource_watchdog_kill()` to `server/notifications/slack.py` following existing
  state-transition-dedup pattern. Dedup-keyed by `(slot_id, reason_category)` with 4h cooldown between re-reminds. First
  kill per category pages immediately; subsequent same-category kills within cooldown are suppressed. GCS alert ledger
  persisted. Fired from `receive_kill_event()` in `resource_watchdog.py`.

- **AO UI panel**: Created `ResourceWatchdog.tsx` dashboard component (top-row panel, 30s poll). Shows: service health
  (live/stale/dead), pressure level (normal/high), cgroup memory % and GB, kill count with last-kill timestamp, and
  uptime. Uses self-contained fetch+setInterval pattern (Pattern B). Wired into both DesktopLayout top-row sections in
  App.tsx.

- **Status endpoint + status file**: Watchdog writes `/dev/shm/resource-watchdog/status.json` each poll tick via
  `_rw_write_status_file()`. Orchestrator `GET /api/resource-watchdog/status` reads it + checks systemd active state.
  `--status` CLI flag was already functional from Phase 1.

### 2026-08-05 — Initial implementation + deploy (interactive session)

Completed Phases 1–3. Watchdog is live on planning VM, killed its first violator within the first tick. Cgroup memory
stable at 13-23 GB. Orchestrator kill-relay endpoint deployed and tested. Bootstrap + ao-self-pull integration shipped.

- **context-scout 2026-08-06**: populated context_scope (5 entries).

---

## Deferred work after 2026-08-05

All Phase 4 hardening items completed. No deferred work remaining. Plan is ready for archival once deploy is verified.

---

## Lessons learned

1. **`exec(eval(sys.stdin.readline()))` is the orchestrator's Python execution harness** — agents spawn this in service
   venvs to run arbitrary Python. It is NOT quality-gates.sh. The 26 GB was from agent-spawned Python, not pytest.
2. **Quality-gates.sh is stable at ~440 MB** — confirmed by local run (10,000 tests, 4.5 min, flat memory).
3. **The OOM crash-loop is a systemd artifact**: cgroup hits MemoryHigh → systemd tries to stop the service → service is
   too starved to exit → SIGKILL after StopTimeout → orphaned child processes survive → restart inherits same pressure →
   loop repeats. The watchdog prevents this by killing the runaway BEFORE the cgroup hits MemoryHigh.
4. **SSM has a ~97 KB document size limit** — large files (like `slots_worker.py` at 94 KB → 125 KB base64) need chunked
   deployment.
5. **pip-audit CVEs block quickmerge** — pre-existing locked-dependency vulnerabilities need `PIP_AUDIT_EXTRA_ARGS` to
   bypass. Not caused by our changes; clean otherwise (2,349 tests, lint, format all green).
6. **Slot detection via `/proc/[pid]/cwd` works** — the `.tabs/N/` pattern in the working directory reliably maps any
   process to its slot, no cooperation needed from tmux or the orchestrator.
7. **Feedback loop via orchestrator API** — watchdog POSTs kill events to the orchestrator, which relays them to the
   agent's slot on next poll/heartbeat, so the agent knows NOT to re-spawn the killed process
8. **Marker files as fallback** — `/dev/shm/resource-watchdog/kills/{pid}.json` survives orchestrator API outages during
   memory pressure
9. **Slot detection via `/proc/[pid]/cwd`** — matches `.tabs/(\d+)/`, walks parent chain; no cooperation needed from
   tmux or the orchestrator
