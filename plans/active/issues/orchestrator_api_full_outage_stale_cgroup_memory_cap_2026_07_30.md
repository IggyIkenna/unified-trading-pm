---
doc_type: issue
title: >-
  orchestrator.service's entire HTTP API was unresponsive (every endpoint HTTP:000) because its systemd cgroup memory
  cap was never rescaled after the 2026-07-29 32GB→64GB VM resize — fixed live, zero downtime
summary: >-
  While investigating an unrelated sports-satellite backlog question, `/api/backlog` hung indefinitely (curl HTTP:000 at
  60s from localhost on the VM itself). Broadened the check: EVERY orchestrator endpoint (`/api/mode`, `/api/activity`,
  `/api/backlog`) was unresponsive, though `systemctl is-active orchestrator` reported the process alive and CPU load
  was unremarkable. `systemctl status orchestrator` showed the smoking gun: `Memory: 23.0G (high: 23.0G max: 26.0G ...
  available: 0B)` — the orchestrator.service cgroup (which holds the API process AND every slot's tmux+claude children)
  had hit its configured `MemoryHigh` and was sitting at zero available headroom, even though the HOST had 36.5GB free
  system-wide. Root cause: `memory-cap.conf` (`/etc/systemd/system/orchestrator.service.d/`) is auto-computed by
  `bootstrap_vm.sh` Step 5.7 as a fraction of `/proc/meminfo`'s MemTotal AT THE TIME THAT STEP LAST RAN — its file
  timestamp (2026-07-28 09:07) predates `orchestrator_vm_swap_exhaustion_masked_as_cpu_2026_07_29.md`'s instance resize
  (2026-07-29, ~31GB→64GB RAM), and nobody re-ran Step 5.7 (or any bootstrap step) afterward, so the cap stayed
  calibrated to the OLD ~31GB RAM (MemoryHigh=23G/MemoryMax=26G, exactly matching 31GB×75%/87.5%) — an almost EXACT
  mirror-image of the 2026-07-28 incident Step 5.7's own comment already documents (a downsize leaving a cap ABOVE
  actual RAM); this time an UPSIZE left a cap BELOW actual RAM, which is the more dangerous direction since the cap
  actually binds. Fixed live with ZERO service restart: recomputed the same ratios against current `/proc/meminfo`
  (64GB→ MemoryHigh=46G/MemoryMax=54G/MemorySwapMax=16G), applied instantly via `systemctl set-property ... --runtime`
  (no restart, no worker disruption), then wrote the matching persistent drop-in + `daemon-reload` so it survives
  reboot. All 3 endpoints returned to HTTP:200 (0.04s-3.6s) within the same command sequence, no restart needed.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, incident, cgroup, memory-cap, systemd, api-outage, instance-resize, bootstrap_vm]
related:
  [
    /plans/archive/issues/orchestrator_vm_swap_exhaustion_masked_as_cpu_2026_07_29.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-07-30"
author: unknown
last_updated: "2026-07-30"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source: >-
  Discovered incidentally while investigating a stale "52 tasks blocked on sports_satellite_ao_dispatch_batch2" claim
  from yesterday's session — `/api/backlog` hung, which turned out to be a symptom of the whole API being down, not a
  backlog-specific bug.
resolved_by:
locked_by:
context_scope:
  [
    agent-orchestrator/scripts/rescale-memory-cap.sh,
    agent-orchestrator/scripts/bootstrap_vm.sh,
    /plans/archive/issues/orchestrator_vm_swap_exhaustion_masked_as_cpu_2026_07_29.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
locked_since:
---

# Orchestrator API full outage — stale cgroup memory cap after yesterday's VM resize

## What's confirmed

1. **Symptom, live-measured 2026-07-30T08:0x-08:1xZ**: every orchestrator HTTP endpoint timed out from **localhost on
   the VM itself** (not a network/firewall issue) — `curl --max-time 60 http://localhost:8765/api/backlog` → `HTTP:000`
   after the full 60s; `/api/mode` and `/api/activity` likewise timed out at 10s. `systemctl is-active orchestrator` →
   `active`; `NRestarts` implied 0 (no crash/respawn) — the process was alive but not servicing requests.
2. **Root cause, confirmed via `systemctl status orchestrator`**: the cgroup was pinned at its configured ceiling —
   `Memory: 23.0G (high: 23.0G max: 26.0G swap max: 15.0G available: 0B peak: 23.8G swap: 14.9G swap peak: 15.0G)`.
   `available: 0B` with `swap: 14.9G` of a `15.0G` swap-max is the smoking gun: the cgroup was in sustained `MemoryHigh`
   reclaim/throttle, causing every thread in the process (including request-handling ones) to stall on allocation/swap
   I/O — while the HOST overall was healthy (`free -m`: 63255MB total / 26686MB used / 5505MB free / **36568MB
   available** system-wide) — the constraint was entirely internal to this ONE cgroup's budget, not host-wide pressure.
3. **Why the cap was stale**: `scripts/bootstrap_vm.sh` Step 5.7 ("Guard the MemoryMax cgroup cap on
   orchestrator.service") computes `MemoryHigh`/`MemoryMax`/`MemorySwapMax` as 75%/87.5%/min(actual-swap,16G) of
   **`/proc/meminfo` read at the time the step runs** — it is idempotent and self-correcting, but only on a bootstrap
   re-run, not continuously. `/etc/systemd/system/orchestrator.service.d/memory-cap.conf`'s file timestamp was
   **2026-07-28 09:07** — the file's own values (`MemoryHigh=23G`/`MemoryMax=26G`) exactly match 75%/87.5% of the OLD
   `c7i.4xlarge` RAM (~31GB, confirmed against the earlier session's own `free -m` reading of `31551MB` total).
   `orchestrator_vm_swap_exhaustion_masked_as_cpu_2026_07_29.md`'s instance resize to `m8i.4xlarge` (64GB) happened the
   NEXT DAY (2026-07-29) via a graceful stop/modify-instance-attribute/start — which does NOT re-run `bootstrap_vm.sh`,
   so the stale ~31GB-calibrated cap silently carried forward onto the new 64GB box. This is the **mirror image** of the
   exact incident Step 5.7's own code comment documents (`m8i.4xlarge[64G] -> c7i.4xlarge[32G]` DOWNSIZE leaving a cap
   ABOVE actual RAM, which is harmless since it never binds) — this time an UPSIZE left a cap BELOW actual RAM, which is
   the dangerous direction because the cap actively constrains the cgroup well before the host itself would ever feel
   pressure.
4. **This cgroup is the WHOLE fleet, not just the API process**: `systemctl status`'s `CGroup:` tree shows the
   orchestrator.service cgroup contains the uvicorn process AND every slot's `tmux new-session` + spawned `claude` child
   processes (20+ concurrent Claude sessions observed) — so this cap silently constrains the combined memory footprint
   of the ENTIRE fleet, not a narrow API budget. A stale-low cap here throttles everything: task dispatch, activity
   logging, scheduled-job dispatch, the dashboard, and (per point 1) the worker sessions' own resource competition, all
   at once.

## Fix applied (2026-07-30, this session, zero downtime)

Recomputed the exact same ratios Step 5.7 uses, against **current** `/proc/meminfo` (`MemTotal=64773408kB`,
`SwapTotal=50331640kB`): `MemoryHigh=46G` / `MemoryMax=54G` / `MemorySwapMax=16G` (swap capped at the original 16G
constant since actual swap, 48G, exceeds it — matches Step 5.7's own swap-cap logic).

1. **Immediate, non-disruptive relief**:
   `systemctl set-property orchestrator.service MemoryHigh=46G MemoryMax=54G MemorySwapMax=16G --runtime` — applies to
   the ALREADY-RUNNING cgroup instantly, no restart, no worker disruption. `MemoryAvailable` went `0` → `24668487680`
   (~23GB) in the same command.
2. **Persistent**: wrote `/etc/systemd/system/orchestrator.service.d/memory-cap.conf` with the same values +
   `systemctl daemon-reload`, so the fix survives a future reboot/restart (matches exactly what re-running Step 5.7
   would have written).
3. **Verified recovered**: `/api/mode` HTTP:200 (0.04s), `/api/activity?limit=5` HTTP:200 (3.6s), `/api/backlog`
   HTTP:200 (2.0s) — all three endpoints that were HTTP:000 moments earlier. Re-checked ~15 min later: still healthy
   (`MemoryAvailable=26.7GB`, `/api/mode` 1.9ms, host-wide `free -m` shows 51.7GB available, swap usage actually DROPPED
   from 17.7GB→11.1GB used as the kernel stopped fighting the tight cap).

## What is NOT yet done

The **process-level fix** (re-running `bootstrap_vm.sh`'s Step 5.7, or an equivalent standalone script) was deliberately
NOT invoked here — I hand-computed and applied the same ratios via `systemctl set-property` + a hand-written drop-in for
speed (this was a live production outage), rather than running the full `bootstrap_vm.sh` (which does many OTHER
provisioning steps not needed / not safe to blindly re-run against an already-configured, already-running VM). The
**durable gap** this incident exposes: Step 5.7 is a good self-correcting mechanism, but it is only INVOKED at bootstrap
time — an EC2 stop/modify/start resize (the sanctioned, lower-friction resize path used yesterday, and likely to be used
again) never triggers it. Nothing currently reminds an operator/agent to re-run this step after a resize.

## Todos

- [x] [BACKEND] P1. Diagnose the full API outage and restore service without a restart. — **Done 2026-07-30**: see "Fix
      applied" above. `agent-orchestrator@f2b6d73` (yesterday's session, unrelated) already live; this fix is
      config-only, no code shipped, no commit needed for the immediate relief.
- [x] [BACKEND] P2. Close the durable gap: make the post-resize memory-cap rescale automatic instead of relying on
      someone remembering to re-run `bootstrap_vm.sh` Step 5.7. Two viable directions (pick one, don't just flag both):
      (a) extract Step 5.7 into its own standalone idempotent script (e.g. `scripts/rescale-memory-cap.sh`) and call it
      from `ao-self-pull.sh`'s existing ~15-min cron loop (cheap, already-polling, already root) so any future RAM
      change self-heals within 15 minutes without a human remembering; (b) add an explicit manual step to whatever
      runbook governs EC2 instance-type changes. (a) is strictly better (self-healing, no runbook-discipline dependency)
      unless there's a reason a cron shouldn't be touching systemd drop-ins found during implementation. — **Done
      2026-07-30, direction (a): `agent-orchestrator@a916694`.** New `scripts/rescale-memory-cap.sh` — idempotent,
      no-ops (one log line) when already correctly scaled, applies live via `systemctl set-property --runtime` (zero
      restart) + writes the persistent drop-in + `daemon-reload`. Wired into `ao-self-pull.sh`'s existing ~15-min cron
      (best-effort, independent of the git-pull logic) AND `bootstrap_vm.sh`'s own Step 5.7 (now delegates to the same
      script instead of a second, divergence-prone copy of the ratio logic). Smoke-tested live against the orchestrator
      VM both paths (no-op detection + `--dry-run`), both exit 0 as expected. Full `quality-gates.sh` green (bash -n +
      shellcheck clean on the new script; no Python touched).
- [ ] [REVIEW] P3. This is the SECOND stale-cgroup-cap incident this class has produced (2026-07-28 downsize-left-
      cap-too-high; 2026-07-30 upsize-left-cap-too-low) — both times found by accident while investigating something
      else, not by any monitor. Consider whether `agent-orchestrator`'s existing host-resource dashboard/alerting (the
      same Swap tile shipped 2026-07-29, `orchestrator_vm_swap_exhaustion_masked_as_cpu_2026_07_29.md`) should also
      surface `MemoryAvailable`/cgroup-vs-host RAM mismatch directly, so a repeat doesn't again require someone to
      stumble into `systemctl status` manually.

## Codex SSOTs

- None directly own cgroup resource-control drop-ins. If todo 2 ships, consider whether
  `/codex/05-infrastructure/vm-launcher-runbook.md` or a runtime-topology doc should note the self-healing rescale
  mechanism, so a future EC2 instance-type change doesn't need tribal-knowledge re-discovery.

## Progress Log

- **2026-07-30 (plans-corpus-reduction-marathon wave 4)**: re-triaged, no action taken. The remaining `[REVIEW] P3` todo
  ("consider whether... dashboard/alerting should also surface MemoryAvailable/cgroup-vs-host RAM mismatch") is phrased
  as an open judgment call, not a bounded fix, and the concrete implementation would cross both agent-orchestrator's
  backend (a new cgroup-v2 memory-stat reader in `host_resources.py`, extending the `/ws/vm-resources` push contract)
  and deployment-ui's frontend (a new dashboard tile, which per this workspace's `[UI]` gate needs a `pw:L2 ✓`
  regression spec) — real feature-sized, cross-repo work, not a 20-minute follow-up. Correctly skipped.
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): KEEP-NA, valid — the sole
  open `[REVIEW] P3` remains an open design/judgment call (new cgroup-v2 memory-stat reader + a new deployment-ui
  dashboard tile), correctly left NA/unbuilt per the 2026-07-30 self-assessment. No change.
- **context-scout 2026-08-03**: refreshed context_scope (4 entries, unchanged — still accurate).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.

- **na-eligibility-audit 2026-08-09 (round11)**: KEEP-NA, valid — re-read end-to-end; sole open item (`[REVIEW] P3`)
  remains real feature-sized, cross-repo work (new agent-orchestrator cgroup-v2 memory-stat reader AND a new
  deployment-ui dashboard tile needing its own `pw:L2` regression spec per the `[UI]` gate) — self-assessed "correctly
  skipped" 2026-07-30, unchanged. Checked against the round7-10 precedent set — none apply. Corroborated same-day:
  `/ag-closeout-audit ao` batch12 independently lists this doc under genuinely-human-only (4).

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3)**: KEEP-NA, valid — full re-read of the sole open
  item (dashboard/alerting surface for `MemoryAvailable`/cgroup-vs-host RAM mismatch). Self-assessed 2026-07-30 as real
  feature-sized, cross-repo work (new agent-orchestrator cgroup-v2 memory-stat reader AND a new deployment-ui dashboard
  tile needing its own `pw:L2` regression spec) — 4 prior audits plus `ao_satellite_ao_dispatch_batch3_2026_07_31.md`'s
  own Deferred section agree. No new facts found.
