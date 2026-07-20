---
doc_type: plan
title: AO dispatch cooldown + durable park — ONE fleet-scoped store, three consumers
summary:
  A worker that declines a task as blocked only blocks its own slot, so any other idle slot re-claims it within minutes
  — 117 skips a day and the same verdict re-derived three times in 35 minutes. Build exactly one fleet-scoped cooldown
  store with change-triggered re-eligibility, then express durable auto-park as its N-skip escalation. The escalator
  backoff consumes the same store; three separate engines would diverge.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, dispatch, cooldown, auto-park, policy]
related:
  [
    ao_open_issues_consolidated_close_out_2026_07_17.md,
    ao_backlog_regen_integrity_2026_07_20.md,
    ao_fleet_observability_kpis_2026_07_20.md,
  ]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: orchestrator_master
assigned_vm: NA # LOCAL execution — operator-assigned agents on this host, NOT AO-dispatched (2026-07-20)
execution_scope: local-only
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 3.0
assigned_role: backend_engineer
model_tier: sonnet-doable # single-repo mechanism build; policy is specified verbatim below
thinking_tier: high # a shared store with three consumers and change-listeners — the design must hold
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_backlog_regen_integrity_2026_07_20.md]
source:
---

# AO dispatch cooldown + durable park

> **Provenance**: Phase 6 (blocked-task cooldown) + Phase 3 (auto-park, mvp-defi unpark) of
> `ao_open_issues_consolidated_close_out_2026_07_17.md`. That plan keeps the audit record; this plan holds the work.

## ⚠️ Two hard constraints — these are the whole point of the plan

**1. Build exactly ONE fleet-scoped cooldown store.** It is keyed by `task_id`, carries change-listeners on prerequisite
/ regen / park events, and is REUSED by (a) blocked-task cooldown, (b) Phase-3 auto-park as its N-skip escalation, and
(c) the escalator backoff in `ao_fleet_observability_kpis_2026_07_20.md` (AF-1). **Do NOT ship three separate
cooldown/backoff engines — they will diverge**, and the divergence is precisely the failure mode the master plan called
out. If AF-1's owner needs the store before it exists, they wait on this plan; say so rather than letting them build a
second one.

**2. New tunables go on the env-free `config.tuning` / `TuningDefaults`, NOT a new `ORCHESTRATOR_*` env alias** (per the
2026-07-18 config split). Reuse existing knobs where they fit: `slot_skip_ttl_hours`,
`orphaned_task_reclaim_grace_seconds`, `dispatch_ack_timeout_seconds`.

## ⚠️ Dependency

`depends_on: ao_backlog_regen_integrity_2026_07_20.md` — specifically its **preserve-by-`brief`** todo. An id-keyed park
is silently dropped on the next id-shift regen (measured: the mvp-defi park was lost exactly this way on 2026-07-17), so
**auto-park is NOT durable until that lands**. Todo 1 (the store) can start immediately; **todo 3 (auto-park) must
wait.**

## The measured problem

A skip-as-blocked today blocks only the SKIPPING slot (24h slot-scoped TTL). Any other idle same-role slot re-claims the
task within ~minutes: **117 `slot_task_skipped` per 24h**, and the mvp thrash doc recorded the same verdict being
re-derived **3 times in ~35 minutes**. Every re-derivation is a full worker boot that reads the plan and reaches the
identical conclusion.

## Todos

- [ ] [BACKEND] P1. **Build the ONE fleet-scoped cooldown store.** Keyed by `task_id`, fleet-scoped (not slot-scoped),
      with the operator policy implemented verbatim: (1) when a worker declines a task as BLOCKED after reading the
      plan, the task is not re-dispatchable to **ANY** slot for a base cooldown of **10-15 min**; (2) within/after that
      window, re-dispatch EARLY only if something RELEVANT changed — a prerequisite flip, a plan-todo/regen change on
      that task, or a park/priority change (**change-triggered re-eligibility**); (3) no change → next attempt no sooner
      than **1h**. **Gate**: regression tests — skip-blocked → no cross-slot redispatch inside the base cooldown; prereq
      flip → immediate re-eligibility; no change → 1h.
- [ ] [BACKEND] P1. **Worker-supplied ETA overrides the default cooldown.** Extend the `/skip-current-task` payload with
      `estimated_unblock_minutes` — a worker often knows ("the VM finishes in ~15 min"). When supplied, the cooldown
      becomes that estimate plus a small buffer instead of the defaults. **Gate**: a test asserting the ETA is honoured,
      and that an absent/implausible ETA falls back to the policy defaults rather than trusting the worker blindly.
- [ ] [BACKEND] P2. **Durable auto-park as the N-skip escalation of the SAME store** (blocked on the dependency above).
      At ≥N distinct within-TTL skips carrying a `BLOCKED|PARKED|GATED` reason, park via the durable
      `priority_override`/false-prereq recipe (`ao@8dd5763`) — **with an unpark path when the condition clears**, and an
      operator-visible surface (activity event + dashboard flag, same class as `needs_operator_count`). R1 made
      fleet-skipped tasks count 0 toward the spawn budget, which silenced the churn **but also the signal** — nothing
      currently tells anyone a task is stuck. This restores the signal without the churn. **Gate**: a fleet-skipped task
      auto-parks with a visible reason; clearing the condition unparks it; test-pinned. Closes doc #1's last todo and
      doc #5's auto-park design todo in one mechanism.
- [ ] [ADMIN] P2. **Wire the mvp-defi unpark — RULED 2026-07-20: re-point it to the live owner.**
      `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` is still `false` and its named flipper plan
      (`data_completion_defi_2026_07_15`) was flagged by plan_health as CONTRADICTED/superseded by
      `defi_consolidated_closeout_2026_07_18` — which declares DeFi capture STOPPED and backfill GATED on T1-T3
      canonicalisation. If the named flipper never progresses, **this park outlives its reason forever** — a permanent
      silent park. Operator ruling (A3): re-point the unpark to the `defi_consolidated_closeout_2026_07_18` owner, or
      park it EXPLICITLY (documented) until the DeFi re-architecture resumes. **Gate**: the owning plan (whichever it
      now is) carries the flip instruction; the condition is documented; **no park exists without a named LIVE flipper**
      — make that last clause a rule the auto-park mechanism enforces, not just a one-off cleanup.
- [ ] [BACKEND] P2. **Publish the store's contract for its other consumer.** AF-1's escalator backoff
      (`ao_fleet_observability_kpis_2026_07_20.md`) must sit on this store. Write down the interface — how to register a
      cooldown, how to signal a relevant change, how to query re-eligibility — somewhere its owner will find it, and
      tell them when it lands. **Gate**: the interface is documented and AF-1's owner has confirmed they can build on it
      without a second engine.

## Safeguards

- Never `git reset --hard` / `git clean -fd` / `git checkout` a dirty tree — other agents share this repo.
- Commit only from a `quality-gates.sh`-green tree.
- **A cooldown that is too aggressive starves the fleet; one too lax restores the thrash.** Both failure directions are
  real — prefer the measured policy above over your own tuning instinct, and if you think a value is wrong, say so
  rather than quietly changing it.

## Codex SSOTs

- `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — dispatch/skip/park model.
- `codex/06-coding-standards/config-reloader-pattern.md` + the 2026-07-18 config split — why new tunables are env-free.
- `codex/04-architecture/agent-orchestrator-alerting.md` — the park's operator-visible surface must be actionable-only.

## Progress Log

- **🟢 2026-07-20 — KEYSTONE DEPENDENCY UNBLOCKED (notification from `ao_backlog_regen_integrity_2026_07_20.md` todo
  2).** Your durable auto-park's preserve-by-`brief` prerequisite is resolved — and it turns out no production code
  change was needed: the RC-1 brief-keyed reconcile (`agent-orchestrator@ff6100a`, 2026-07-07) already predates and
  prevents the "id shift silently drops a park" mechanism the master plan flagged. Verified two ways: (1) a new
  regression test, `test_regen_park_survives_sibling_completion_and_id_shift` (`agent-orchestrator@a650ee4`) — parks the
  middle of 3 todos, removes the last, regens twice with `prune_stale=True` — park survives unchanged; (2) live re-check
  via read-only SSM: the real mvp-defi park (`mvp_backfill_defi_onchain_v10-001`) still holds `priority: 999` +
  `prereqs.prerequisites: [defi_onchain_v10_universe_v2_seed_or_backfill_progressed]`, unchanged 3 days / ~140
  `PlanRegenLoop` ticks since its 2026-07-17 re-application. Full detail + corrected root-cause on that plan's todo 2.
  **You can build durable auto-park on `priority_override`/`prereqs.prerequisites` as-is — no additional preservation
  work is a prerequisite.**
- **2026-07-20 — plan created** from Phases 3+6. Deliberately scoped around the ONE-store constraint rather than by
  phase, because the master plan's own risk note is that three consumers each build their own backoff and drift apart.
