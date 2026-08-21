---
doc_type: issue
title: >-
  codex-bridge.service missing `tiktoken` in its venv caused every Codex turn to 500 and leak an
  orphaned `codex app-server` child — 241 orphans, up to 26GB swap, host load 50-60/8 cores,
  starving every slot's quality-gates.sh (including 13/17's ~1hr stuck ship attempts)
summary: >-
  Operator reported slots 13 and 17 unable to ship for ~1 hour, quality-gates.sh appearing stuck.
  Live investigation (2026-08-21, slot 15) ruled out the qg-host-governor resource-reservation
  mechanism first — its ledger showed 0MB reserved / 0 running heavy phases / 0/6 total-instance
  tokens held, i.e. admitting freely, not queueing anyone. Root cause was a separate, unrelated
  leak: `codex-bridge.service` (server/codex_bridge_server.py, the Anthropic-format facade for
  OpenAI Codex/Luna on 127.0.0.1:8769 — used by both slot 13 and slot 17, both on the `codex-pro`
  account) was 500ing on every single request with `ModuleNotFoundError: No module named
  'tiktoken'`. `tiktoken>=0.8.0` was already correctly declared in pyproject.toml/uv.lock — this
  was a pure venv-sync drift in the shared top-level `agent-orchestrator/.venv` the service runs
  from (WorkingDirectory=/home/ubuntu/unified-trading-system-repos/agent-orchestrator), not a code
  defect. Each failed turn appears to leak its spawned `codex app-server` subprocess without
  reaping it: `pgrep -P <bridge-pid>` found 241 orphaned children (6,358 total tasks in the
  service's cgroup per `systemctl status`), all started in a ~24min window ~20h before discovery.
  `systemctl status` showed current memory 11.1G, peak 24.6G, swap 7.5G, peak swap 26.3G — up to
  87% of this 30GB host's RAM from one leaking service. Host-wide: load average 49.7/55.9/58.7 on
  8 physical cores, ~16GB actively swapped (not just low `MemAvailable`), iowait spiking to 62% in
  one vmstat sample. This explains why quality-gates.sh runs that the governor DID admit still
  crawled: they kept losing the CPU scheduler and hitting swapped-out pages, which looks identical
  to "QG is stuck" from the outside but is real execution slowness, not admission queueing. Also
  notable: the governor's own runtime abort-watchdog (built for exactly this) only checks
  `MemAvailable %` (currently ~50%, under its 75% abort trip point) — it doesn't look at
  swap-in-use or load average, so it did not and would not have self-detected this. Confirmed via
  AO API that slots 13/17 were both `status: paused, task_id: None` (operator-driven interactive
  sessions, not AO dispatch) — so this was never an AO dispatch/orchestration bug.
  **Fix applied and verified live**: (1) `cd agent-orchestrator && uv sync` — installed the
  already-declared-but-missing tiktoken (0.14.0) into the shared venv, confirmed importable.
  (2) `sudo systemctl restart codex-bridge.service` — cleared all 241 orphans (cgroup Tasks
  6358→18, Memory 11.1G→195.8M immediately). Post-restart journal shows clean 200s, no more
  tiktoken errors. Host memory: used 15Gi→6.5Gi, available 15Gi→24Gi, swap 16Gi→7.3Gi within
  ~20s of the restart and continuing to drain. Load average (a trailing EWMA) had not yet caught
  up within the observation window — expected, not a sign the fix didn't work, since the
  underlying process tree was confirmed gone via `ps`/`pgrep`.
status: resolved
resolved_by: >-
  agent-orchestrator venv `uv sync` (installed tiktoken==0.14.0) + `systemctl restart
  codex-bridge.service`, both run live on the shared host 2026-08-21 ~07:48 UTC by slot 15,
  operator-approved. No code change — pure environment-sync + service restart.
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    codex,
    codex-bridge,
    tiktoken,
    process-leak,
    host-resource-exhaustion,
    quality-gates,
    qg-governor,
    swap-thrashing,
  ]
related:
  [
    /plans/active/issues/codex_luna_heartbeat_sandbox_network_stuck_loop_2026_08_20.md,
    /plans/active/issues/nvidia_codex_exhaustion_observability_gap_2026_08_19.md,
    /plans/active/issues/codex_native_cli_vs_bridge_architecture_decision_2026_08_20.md,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    agent-orchestrator/server/codex_bridge_server.py,
    unified-trading-pm/scripts/quality-gates-base/qg-host-governor.sh,
  ]
source: >-
  Operator, interactive session, 2026-08-21: "please check the issue and slowness of the
  quality-gates, why the quality-gates are taking so long to complete? i was working with agents in
  slot 13 and 17 and they are trying to ship their work for 1 hour now but they are not able to ship
  because qg are taking so long. please check the issue with governer or any other mechanism that is
  slowing down the AO." Investigated live via slot 15.
---

## What was reported

Operator: slots 13 and 17 had been trying to ship their work for ~1 hour, blocked on
quality-gates.sh appearing to take far too long. Asked whether the qg-host-governor (or "any other
mechanism") was slowing down the AO.

## Investigation path

1. **Ruled out the qg-host-governor first** (`scripts/quality-gates-base/qg-host-governor.sh`,
   reservation mode). Live `--status` against the correct shared ledger
   (`/home/ubuntu/unified-trading-system-repos/.benchmarks/qg-governor/`, `WORKSPACE_ROOT` must
   match `*/.tabs/*` for `_qg_shared_root()` to resolve correctly — a bare invocation without it
   silently falls back to `/tmp` and reads the WRONG ledger, a footgun worth knowing about when
   re-running this check) showed `reserved: 0MB`, `running heavy phases: 0`,
   `total-instance gate: 0/6 tokens held`. The governor was admitting freely, not queueing anyone.
2. Checked raw host state: `uptime` → load average 49.7/55.9/58.7 on 8 physical cores. `free -h`
   → ~16GB swap in active use. `vmstat 1 3` → run queue (`r`) of 86/39/11, iowait (`wa`) up to 62%
   in one sample. This is real oversubscription, not a governor artifact.
3. `ps` census: 690 total processes, 264 matching `codex app-server|claude --dangerously`. Broke
   this down by parent PID + cwd: the large majority were children of a single PID (later
   identified as `codex-bridge.service`'s main uvicorn process), not the legitimate one-per-slot
   worker processes (those are children of a different, expected parent and map 1:1 to real
   `.tabs/<N>` slots).
4. `systemctl status codex-bridge.service` confirmed: 241 direct children, 6,358 total cgroup
   tasks, current memory 11.1G (peak 24.6G, swap peak 26.3G). `journalctl -u codex-bridge.service`
   showed continuous, currently-ongoing `ModuleNotFoundError: No module named 'tiktoken'` 500
   errors on every request, plus `TransportClosedError: Codex process closed stdout` /
   `failed to initialize sqlite state runtime under /home/ubuntu/.codex` — consistent with sqlite
   lock contention from hundreds of concurrent orphaned Codex processes hammering the same state
   file.
5. Confirmed `tiktoken>=0.8.0` was already correctly declared in `agent-orchestrator/pyproject.toml`
   and `uv.lock` — this was a venv-sync drift on the shared top-level `agent-orchestrator/.venv`
   the systemd unit runs from, not a missing/incorrect dependency declaration.
6. Confirmed via `GET /api/state` that slots 13 and 17 were both `status: paused, task_id: None` —
   operator-driven interactive sessions, not AO-dispatched tasks. Not an AO orchestration bug.

## Fix

```bash
cd /home/ubuntu/unified-trading-system-repos/agent-orchestrator
uv sync                                  # installs tiktoken==0.14.0 (already declared, just missing)
sudo systemctl restart codex-bridge.service
```

Verified: cgroup `Tasks` 6358→18, `Memory` 11.1G→195.8M immediately after restart. Fresh journal
showed clean 200/307 responses, no more tiktoken errors. Host `free -h`: used 15Gi→6.5Gi, available
15Gi→24Gi, swap 16Gi→7.3Gi and draining within ~20s. `ps`/`pgrep` confirmed the old orphaned
process tree (241 children under the old PID) was fully gone post-restart.

## Why this masqueraded as "the QG governor is slow"

Any quality-gates.sh run the governor DID admit was still real work competing for the same 8
physical cores and 30GB of RAM as codex-bridge's 241 orphaned, actively-erroring children — so an
admitted run kept losing the CPU scheduler and touching swapped-out pages. From the outside that is
indistinguishable from "quality-gates.sh is stuck," but the governor's own admission math was
correct throughout; it has zero visibility into a completely separate systemd service's leak.

## Gap surfaced, not yet fixed

The governor's runtime abort-watchdog (`_qg_watchdog_pressure_hit` in `qg-host-governor.sh`) only
checks `MemAvailable` percentage against `QG_HOST_RAM_ABORT_PCT` (default 75%). At the time of
this incident `MemAvailable` was ~50% of total — comfortably under the trip point — despite ~16GB
already parked in swap and a load average 6-7x the physical core count. The watchdog would not
have self-detected or self-aborted under this exact failure shape (real degradation via swap
thrashing + CPU steal from a process the governor doesn't track, with nominal `MemAvailable`
looking fine). Not fixed as part of this incident — flagging for whoever next touches
`qg_host_adaptive_resource_governor_2026_07_14.md`.

## Not yet investigated

`codex-bridge.service`'s exception-handling path that leaks the spawned `codex app-server` child
on a failed turn instead of reaping it — the `uv sync` + restart clears the SYMPTOM (the missing
dependency that was triggering every turn to fail, and the accumulated orphans), but if any other
turn-failure mode exists that also skips child cleanup, the same leak class could recur without a
missing-tiktoken-style trigger. Worth a follow-up read of `server/codex_bridge_server.py`'s spawn/
cleanup path by whoever owns that service next, to confirm child processes are unconditionally
reaped (e.g. in a `finally`) rather than only on the happy path.

## Separate finding, same investigation: 592-commit-stale slot-15 checkout

While shipping this doc, `safe-doc-push.sh` refused on a pre-existing unmerged (conflicted) index
state in this checkout, unrelated to this incident. Investigating found the checkout was 592
commits behind `origin/live-defi-rollout` with ~30 unrelated dirty files, 2 live git-stash-pop
conflicts, and 63 accumulated stash entries (several literally named
`safety-snapshot: pre-reconcile quarantine`, indicating this is a recurring, previously-tooled-for
class of problem — see `scripts/dev/audit-stash-pile.sh`). Every sampled piece of dirty content
(both conflicts + a spot-checked plain diff) was confirmed to be STALE: the working tree was
reverting already-corrected, already-evidence-cited content back to older pre-correction versions
(e.g. a todo's `Evidence:` citation line, a plan's `Flipped to active 2026-08-20` dated ruling —
both present in HEAD, both missing from the locally-stashed side). Resolved by keeping the HEAD
side for the 2 conflicts (`git checkout --ours`), snapshotting the remaining dirty tree into one
new, clearly-labeled stash (`slot15 pre-590-commit-resync safety snapshot 2026-08-21 (claude)` —
nothing destroyed, fully recoverable) rather than individually verifying all ~30 files, then
`git pull --ff-only` to catch up. The other 62 pre-existing stash entries were left untouched —
cleaning the historical stash pile is `audit-stash-pile.sh`'s job and a separate decision from
unblocking this one ship.
