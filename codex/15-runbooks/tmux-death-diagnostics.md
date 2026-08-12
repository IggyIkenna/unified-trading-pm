---
doc_type: codex-runbook
title: Reading a tmux_session_lost event's diagnostic payload (+ core-dump forensics setup)
summary:
  "SSOT for what's actually captured, automatically, on every worker/slot tmux death, and how to pull it live. Built
  2026-08-12 out of ao_tmux_session_loss_mid_task_root_cause_2026_08_10's 2-day investigation: every catch up to this
  point needed a manually-launched capture script running IN ADVANCE of a death to get any context beyond an empty
  pane_death_info. server/tmux_pruner.py's tmux_session_lost logging now attaches host/account/pane/spawn-concurrency
  state to every future death with zero operator action, and a live check-ao-recent-deaths.sh script reads it back
  without hand-rolling SSM+sqlite3 each time. Also documents the root cause of why NO death (however it died) ever left
  a real crash artifact: `ulimit -c` measured 0 for the whole orchestrator.service tree despite kernel.core_pattern
  already being configured — fixed via a systemd drop-in (LimitCORE=infinity), NOT by editing the live installed unit
  file directly (it's install-script-substituted per-VM, User=ubuntu here vs the repo template's User=hk — overwriting
  it would have broken the live service)."
status: current
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
owner: operator (ad-hoc — whenever a tmux/worker death needs live diagnosis, not just this doc's own upkeep)
cadence: on-demand (incident-triggered — not periodic)
verifier:
  "check-ao-recent-deaths.sh returns real, non-null host_snapshot/account_snapshot/tmux_server_alive for the most recent
  slot-scope tmux_session_lost row — confirms the automatic capture is still live on whatever build the VM is currently
  running"
last_executed: "2026-08-12"
tags: [runbook, agent-orchestrator, tmux, crash-forensics, core-dump, monitoring, root-cause]
related:
  [
    /plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md,
    /codex/15-runbooks/isolated-deepseek-crash-debug-sandbox.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
code_refs:
  [
    agent-orchestrator/server/tmux_pruner.py,
    agent-orchestrator/server/tmux_spawn.py,
    agent-orchestrator/server/host_resources.py,
    agent-orchestrator/scripts/orchestrator.service,
    agent-orchestrator/scripts/orchestrator/check-ao-recent-deaths.sh,
  ]
created: "2026-08-12"
author: agent
---

# Reading a `tmux_session_lost` event's diagnostic payload

## Quick start — how to check

```bash
bash agent-orchestrator/scripts/orchestrator/check-ao-recent-deaths.sh                # last 10, any slot
bash agent-orchestrator/scripts/orchestrator/check-ao-recent-deaths.sh --slot 2       # last 10 for slot 2
bash agent-orchestrator/scripts/orchestrator/check-ao-recent-deaths.sh --limit 30
```

Same read-only SSM access pattern as `check-ao-backlog-status.sh` (see
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` for why SSM instead of hitting the API directly)
— reads `state.db`'s `activity_log` table via `sqlite3 -readonly` rather than the HTTP API, since `/api/activity` has no
`task_id` filter and a wide-enough `limit` to reliably catch an older death is expensive.

## What's captured on every death, automatically (agent-orchestrator@d825c415c6 / @007995b3bd)

Every SLOT-scope `tmux_session_lost` event (agent-scope deaths — persistent `main`/`review`/custom agents — do NOT carry
these fields, only the pane-level `pane_death_info`) now logs:

| Field                             | What it tells you                                                                                                                                                                                                                                                                                                                                                                                      |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `burst_size`                      | How many OTHER slots died in the SAME tick. `1` = isolated. `>1` = a tmux-SERVER-wide crash took every hosted session with it — the dominant historical pattern (18-29-slot bursts).                                                                                                                                                                                                                   |
| `tmux_server_alive`               | Was the tmux SERVER process itself confirmed up or down at detection (`tmux_server_running()`) — distinguishes "this one pane died" from "the whole server crashed and every death this tick reads identically."                                                                                                                                                                                       |
| `host_snapshot`                   | `load_avg_1m/5m/15m`, `ram_percent`, `swap_percent` at the moment of death. Stateless-only (no `cpu_percent`/`iowait_percent` — those mutate module-global delta state the externalized resource-history sampler owns; see `host_resources.stateless_snapshot()`'s own docstring).                                                                                                                     |
| `account_id` / `account_snapshot` | The dying slot's own account (`account_status`, `rate_limited_until`, `overage_status`, `overage_disabled_reason`, `auth_failed_at`) — tests the standing account-level rate-limit/quota hypothesis automatically, no manual DB join.                                                                                                                                                                  |
| `pane_death_info`                 | tmux's own `#{pane_dead_status}`/`signal`/`time`/`pane`/`pane_pid` + cgroup OOM counters, if the pane object survived long enough to be read. **Usually `null`** (session itself already fully gone) — see below.                                                                                                                                                                                      |
| `pane_tail`                       | Scrollback off the dying pane, if it survived. Empty in the same cases `pane_death_info` is null. `rate_limit_in_tail` runs the existing rate-limit regex against it automatically.                                                                                                                                                                                                                    |
| `concurrent_recent_spawns`        | Count of `SlotRow.last_spawned_at` within the last 60s, DB-only (no subprocess) — death #1's historical mechanism (a burst of ~27 near-simultaneous new-pane-creation calls crashing the server) was only ever measurable via a manually-launched `pgrep` script; this is the same signal, automatic. **Not a perfect proxy** — escalation/watchdog spawns bypass AutoSpawn's own respawn counter too. |
| `core_dumps_found`                | Any `/tmp/core-*` file from the last 120s (broad glob, not pid-matched — most deaths have no known pid either). Empty unless the process was spawned AFTER the `LimitCORE=infinity` fix landed (see below) AND the death was a self-inflicted signal.                                                                                                                                                  |
| `checkout_sha`                    | The running build at the moment of death — ties a `tmux_session_lost` row to the exact code that saw it.                                                                                                                                                                                                                                                                                               |

**Why `pane_death_info`/`pane_tail` are usually empty, still**: this is the harshest, most common death signature in the
whole investigation — the tmux SESSION itself vanished (not just the process inside it), so there is no pane object left
anywhere to query by the time the pruner's next tick runs. This is a genuinely different case from "the process exited
and `remain-on-exit` kept a dead pane around" (that case DOES leave `pane_death_info` populated, just usually with blank
status/signal/time fields — see `capture_pane_death_info()`'s own docstring for the two known gradations).

## Core dumps — root cause of "no forensic trace, ever" (fixed 2026-08-12)

Measured live: `ulimit -c` = **0** for the entire `orchestrator.service` process tree, even though `kernel.core_pattern`
was already correctly set to `/tmp/core-%e-%p-%t`. No death — however it died, including a self-inflicted
SIGABRT/SIGSEGV that absolutely would have produced a core if allowed — ever had a real crash artifact available.
`fs.suid_dumpable=2` and `ProtectSystem=strict`'s `ReadWritePaths=/tmp` were already fine; the ONE missing piece was the
per-process resource limit.

**Fix**: `LimitCORE=infinity` added to `scripts/orchestrator.service` (the repo template) — but applied LIVE via a
**systemd drop-in** (`/etc/systemd/system/orchestrator.service.d/override.conf`), never a raw file overwrite. The live
installed unit differs from the tracked template (`install-orchestrator-service.sh --operator ubuntu` substitutes
`User=hk`/`WorkingDirectory=/home/hk/...` in the template to `User=ubuntu`/`/home/ubuntu/...` on this VM) — `cp`-ing the
template over it would revert those substitutions and break the live service. **Always diff the live unit against the
template before touching it** (`cat /etc/systemd/system/orchestrator.service` on the VM) — a drop-in is the safe way to
add one directive without risking the rest.

Limits are inherited down the process tree at fork/exec, so this covers every tmux session + every `claude` worker this
service spawns, not just uvicorn itself — but **only processes spawned AFTER the restart**; an already-running worker
keeps its old (disabled) limit until its own next respawn.

**What a core dump can and can't prove**: only a **self-inflicted** signal (SIGABRT, SIGSEGV, SIGBUS, SIGILL, SIGFPE —
the process crashing itself) produces a core. An **external** `SIGKILL` (OOM-killer, `kill -9`, a cgroup limit
enforcement) never does — the kernel doesn't get a chance to dump before the process is gone. So `core_dumps_found`
being empty for a given death does NOT rule out a kill; it only means "if this was a crash, it wasn't the core-producing
kind, or the fix wasn't live yet for this process."

## Applying a live change to `orchestrator.service` safely

1. `cat /etc/systemd/system/orchestrator.service` on the VM FIRST — confirm what's actually installed differs from the
   repo template (it will, per the operator-substitution above).
2. Prefer a drop-in: `mkdir -p /etc/systemd/system/orchestrator.service.d && cat > .../override.conf <<'EOF' ... EOF`.
3. `sudo systemctl daemon-reload && sudo systemctl restart orchestrator`.
4. Verify: `systemctl show orchestrator -p <TheDirective>`, `systemctl is-active orchestrator`,
   `curl -s localhost:8765/api/healthz`, and check the journal for real request traffic resuming
   (`journalctl -u orchestrator --since -1min`).
5. `KillMode=process` (already set, do not change) means this restart does NOT touch worker tmux sessions — confirm
   post-restart that in-flight slots kept posting (`/api/slots/N/progress` calls in the journal) rather than assuming it
   from the unit file comment alone.

## See also

- `/codex/15-runbooks/isolated-deepseek-crash-debug-sandbox.md` — the MANUAL live-catch methodology (a fully-isolated
  sandbox instance, process-level instrumentation) used before this automatic capture existed. Still the right tool for
  questions this automatic capture can't answer (e.g. attaching a live debugger before the next death).
- `/plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md` — the full investigation history this
  doc's fields were built to close gaps in. Root cause of the tmux-SERVER-death class itself is still open as of this
  doc's creation.
