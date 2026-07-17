---
doc_type: issue
title: Orchestrator concurrent-QG box saturation → backend up-but-slow + dispatch-status divergence
summary:
  Many QG-heavy sports tasks were dispatched concurrently and all hit ship-verify full-quality-gates.sh at once,
  exceeding the shared-host "≤2 full QG" cap; combined with a 10-VM fleet launch this saturated the planning-VM CPU,
  making the uvicorn backend slow-to-respond (request timeouts / transient 5xx, "not reachable") and contributing to
  worker recycles. Dead workers' tasks still showed status=dispatched (reconciliation lag), so backlog read "3
  dispatched" while only 1 worker was genuinely alive.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [orchestrator, dispatch, quality-gates, shared-host-saturation, backlog-divergence, backend-availability]
related:
  - backlog_task_done_status_diverges_from_plan_checkbox
created: 2026-07-17
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: platform_engineer
drift_direction: neutral
depends_on: []
source: >-
  main·planning session 2026-07-17 — filed after the concurrent-QG saturation incident; frontmatter repaired
  (doc_type/status/nature enums + missing keys) by slot main·harsh_pc to unblock the PM lint-codex gate, content
  untouched
resolved_by:
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

> **🟢 EXECUTION CONSOLIDATED 2026-07-17** — this doc's open items are now tracked and executed via
> [`ao_open_issues_consolidated_close_out_2026_07_17`](../ao_open_issues_consolidated_close_out_2026_07_17.md)
> (operator-session local plan; verified-live classification table there). Do NOT start work from this doc alone — flip
> items in the plan and mirror them here. This doc stays the detail/evidence record.

# Orchestrator concurrent-QG box saturation → backend up-but-slow + dispatch-status divergence

> **Filed by main orchestrator (agt-46dce4) at operator request, 2026-07-17 ~14:07Z.** Diagnostic doc — two related
> symptoms with one root cause (shared-host CPU saturation). The immediate incident self-recovered; this doc captures
> the systemic fix so it does not recur.

## Symptoms observed (operator-reported + main-verified)

1. **"3 tasks dispatched but only 1 active worker."** `backlog_summary.dispatched=3` (slots 2, 3, 5) but only slot-5 had
   `worker_alive=true` + `tmux_alive=true`. Slots 2 and 3 had **`worker_alive=false` AND `tmux_alive=false`** — their
   worker processes and tmux sessions were both gone (dead), yet their tasks (`sports_manifest_canonicalisation-010`,
   `-002`) still showed `status=dispatched` pointing at those dead slots.
2. **Backend "not reachable" hiccup.** For ~2 poll ticks, `GET /api/state` returned `TimeoutError` then a transient
   `HTTPError` (5xx). Port `8765` remained **LISTENING the whole time** (two uvicorn workers bound, pids 1913716
   / 1896217) — the server never crashed. Requests recovered once load eased.

## Root cause (one cause, two symptoms)

**Shared-host CPU saturation on the planning VM.** The sports epic fanned out ~8 tasks
(`sports_manifest_canonicalisation-*`, `sports_*_gap_fill`, travel/elo fixes) that all reached the ship-verify stage at
roughly the same time and each launched a **full `quality-gates.sh` (single-worker `pytest -n 0` over the entire
features-service/UAC/MTDS suite)**. Observed **4-6 concurrent full-QG pytest processes** at 80-98% CPU each. This
exceeds the documented shared-host budget **"≤2 full QGs at once — `max(2, floor(cores/4))`"** (CLAUDE.md § Git
discipline). Layered on top: a 10-VM gap-fill fleet launch (tarball build/upload + gcloud control calls) running from
slot-6.

Consequences of the saturation:

- **Backend up-but-slow (symptom 2):** uvicorn is CPU-starved → request handling stalls → client-side `TimeoutError` /
  transient 5xx. NOT a crash (correctly handled by waiting, per the "empty/000/timeout = wait, don't nohup" rule).
- **Worker recycles → dispatch divergence (symptom 1):** CPU-starved / context-heavy workers (slot-6 was at ~95k tokens)
  exited or were recycled. When a worker dies mid-task, the task's `status` stays `dispatched` until the backend
  failover/reconciler flips it back to `queued` (governed by `target_slot_timeout_seconds`, default 600s). During that
  reconciliation lag, `dispatched` count over-reports live work. This is the same class as the in-flight
  `backlog_task_done_status_diverges_from_plan_checkbox` work + slot-10's repeat-dispatch (BLOCKED-\* marker) fix.

## Why it self-recovered

Spot fleet VMs run **independently** of the orchestrator workers, so no compute was lost. Once the concurrent QG runs
finished, CPU freed, the backend responded normally, and the dead slots' tasks are `failover_allowed=true` (they
re-queue on the target-slot timeout). At filing time the incident had already cleared (state queries succeeded again).

## Fix directions (systemic — pick during triage)

1. **Throttle concurrent QG-heavy dispatch (primary).** The dispatcher should cap simultaneously-_shipping_ (full-QG)
   tasks to the shared-host budget `max(2, floor(cores/4))`, queueing the rest. Today nothing enforces this at dispatch
   time — the fan-out let ~all sports tasks hit QG together. Options: (a) a dispatch-time semaphore keyed on "task is in
   ship/QG phase"; (b) a `qg_slot` lease workers acquire before running full `quality-gates.sh`; (c) stagger ship-verify
   dispatch for same-epic fan-outs.
2. **Tighten dispatch-status reconciliation latency.** 600s target-slot timeout means up to 10 min of over-reported
   `dispatched`. Consider a faster dead-worker detector (worker_alive=false AND tmux_alive=false for >N s → immediate
   re-queue) so `backlog_summary.dispatched` reflects live workers. Coordinate with the in-flight
   `backlog_task_done_status_diverges_from_plan_checkbox` work to avoid duplicate mechanisms.
3. **Backend resilience under load (secondary).** uvicorn on the shared planning VM competes with worker QG for CPU.
   Consider nice/cgroup-isolating the orchestrator API process, or a small request queue with fast-fail, so a QG storm
   degrades gracefully instead of timing out polls.

## Not doing / non-goals

- Not a crash — do NOT add uvicorn auto-restart/nohup logic (server was up throughout; that would mask the real cause).
- The dispatch-divergence half overlaps existing `backlog_task_done_status_diverges_from_plan_checkbox` work — fold into
  that rather than building a parallel fix.

## Evidence (2026-07-17 ~14:05-14:07Z)

- `backlog_summary`: `{queued:16, dispatched:3, done:65}`; slots 2 & 3 `worker_alive=false, tmux_alive=false`; slot-5
  `worker_alive=true`.
- `ss -tlnp` : `0.0.0.0:8765 LISTEN` (uvicorn pids 1913716, 1896217) during the "not reachable" window.
- Concurrent `python -m pytest ... -n 0 --cov` processes observed at 80-98% CPU across multiple `.tabs/*` worktrees
  during the preceding ticks.
