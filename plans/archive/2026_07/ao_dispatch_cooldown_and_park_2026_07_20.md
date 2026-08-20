---
doc_type: plan
title: AO dispatch cooldown + durable park — ONE fleet-scoped store, three consumers
summary:
  A worker that declines a task as blocked only blocks its own slot, so any other idle slot re-claims it within minutes
  — 117 skips a day and the same verdict re-derived three times in 35 minutes. Build exactly one fleet-scoped cooldown
  store with change-triggered re-eligibility, then express durable auto-park as its N-skip escalation. The escalator
  backoff consumes the same store; three separate engines would diverge.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, dispatch, cooldown, auto-park, policy]
related:
  [
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/archive/2026_07/ao_backlog_regen_integrity_2026_07_20.md,
    /plans/archive/2026_07/ao_fleet_observability_kpis_2026_07_20.md,
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
depends_on: []
source:
---

# AO dispatch cooldown + durable park

> **🟢 COMPLETE 2026-07-20 — ARCHIVED.** All 5 todos landed and were independently re-verified 2026-07-20 (read-only
> agent): `agent-orchestrator@cfb211c` exists, is an ancestor of `origin/live-defi-rollout`, and is LIVE on the VM
> (confirmed by SSM earlier this session — ancestor of the deployed HEAD). The headline architectural claim holds —
> **ONE generic opaque-key store** (`server/state_store/cooldown.py`); a tree-wide grep found no second
> dispatch-cooldown engine, and the named future consumer (AF-1b's escalator backoff) correctly defers to this store
> rather than building its own. The store is dispatch-wired (`server/dispatch.py` `_FILTERS` SSOT, `FilterScope.FLEET`),
> not dead code; every cited test exists by name with substantive assertions. Codex alignment done in-plan:
> `agent-orchestrator-single-vm- architecture.md` § "Skip / cooldown / park" carries the full contract + `code_refs`.
>
> **Two todos closed with transparent PARTIAL gates, both with tracked follow-up (not the false-progress pattern)**:
> todo 4's generic "no park without a named LIVE flipper" mechanism-enforcement is deferred to issue doc
> `auto_park_no_flipper_rule_not_mechanism_enforced_2026_07_20.md` (P3, well-formed); todo 5's "AF-1's owner confirms"
> half is inherently cross-session and is now AF-1b's concern, tracked live in
> `ao_fleet_observability_kpis_2026_07_20.md`. No residual for the master tracker — this plan is fully closed.
>
> **Test-count note for the record**: the "QG green / ~1490 tests" figure is report-backed (the verifier could not run
> pytest read-only; a rough `grep -c 'def test_'` of ~1477 is consistent). The code claims themselves were confirmed by
> reading the diffs.

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

## ⚠️ Dependency — RESOLVED 2026-07-20, `depends_on` cleared

Was `depends_on: ao_backlog_regen_integrity_2026_07_20.md` (its preserve-by-`brief` todo). That plan's todo 2
re-verified the concern directly: the RC-1 brief-keyed reconcile (`agent-orchestrator@ff6100a`, 2026-07-07) already
prevents hand-tuned-field loss on a sibling-completion id shift — no code change was needed, and the real mvp-defi park
has held live for 3+ days across ~140 regen ticks. **Todo 3 (auto-park) is unblocked** — build on
`priority_override`/`prereqs.prerequisites` as-is. That plan is now archived:
`plans/archive/2026_07/ao_backlog_regen_integrity_2026_07_20.md`.

## The measured problem

A skip-as-blocked today blocks only the SKIPPING slot (24h slot-scoped TTL). Any other idle same-role slot re-claims the
task within ~minutes: **117 `slot_task_skipped` per 24h**, and the mvp thrash doc recorded the same verdict being
re-derived **3 times in ~35 minutes**. Every re-derivation is a full worker boot that reads the plan and reaches the
identical conclusion.

## Todos

- [x] ✅ [BACKEND] P1. **Build the ONE fleet-scoped cooldown store.** — `agent-orchestrator@cfb211c` (QG green: ruff +
      basedpyright 0/0/0 + 1490 tests). Keyed by an OPAQUE `key` string (not `task_id` alone — operator decision
      2026-07-20, so AF-1's escalator backoff can namespace `f"escalation:{escalation_id}"` onto the SAME store without
      a second engine), fleet-scoped (`server/state_store/cooldown.py`, `CooldownRow`), wired as a new FLEET
      `fleet_cooldown` dispatch filter (`server/dispatch.py`). Policy implemented verbatim: (1) a BLOCKED/PARKED/GATED
      decline arms a base cooldown (`tuning.dispatch_cooldown_base_minutes`, default 12min, in the 10-15min range),
      un-dispatchable to every slot; (2) `dispatch._cooldown_snapshot` fingerprints prerequisites/completed_tasks/
      priority/priority_override/brief — a mismatch at check time grants immediate re-eligibility regardless of the
      window (change-triggered re-eligibility); (3) a repeat decline with no detected change arms the extended window
      instead (`tuning.dispatch_cooldown_extended_minutes`, default 60min) — computed at ARM time (`register_cooldown`),
      keeping the dispatch-side filter a pure read. **Gate MET**: regression tests in
      `tests/test_dispatch_fleet_cooldown_filter.py` — skip-blocked → no cross-slot redispatch inside the base cooldown;
      prereq flip → immediate re-eligibility; no change → extended window, pinned via `skip_count`.
- [x] ✅ [BACKEND] P1. **Worker-supplied ETA overrides the default cooldown.** — `agent-orchestrator@cfb211c`.
      `SkipCurrentTaskRequest.estimated_unblock_minutes` (`server/models/slots.py`); `register_cooldown` uses
      `eta_minutes + tuning.dispatch_cooldown_eta_buffer_minutes` when
      `0 < eta <= tuning.dispatch_cooldown_max_eta_minutes` (plausible), else falls back to the base/extended default
      entirely (not clamped — a bad guess is discarded, not partially trusted). **Gate MET**:
      `test_dispatch_cooldown_store.py::test_plausible_eta_overrides_the_default_window` +
      `test_implausible_eta_falls_back_to_policy_defaults` + `test_absent_eta_falls_back_to_policy_defaults`.
- [x] ✅ [BACKEND] P2. **Durable auto-park as the N-skip escalation of the SAME store.** — `agent-orchestrator@cfb211c`.
      `server/auto_park.py::maybe_auto_park` — `>= tuning.dispatch_cooldown_auto_park_skip_threshold` (default 3)
      distinct BLOCKED/PARKED/GATED arms within `tuning.dispatch_cooldown_park_window_hours` (default 24h) parks via the
      durable `priority_override`/false-prereq recipe (RULES.md §4), applied programmatically (synthetic condition
      `auto_unpark__<task_id>`). **Unpark path**: condition-driven, not blocker-detection — `AutoParkReconciler`
      (`server/auto_park_reconcile.py`, `tuning.auto_park_reconcile_interval_seconds` default 300s) notices once the
      synthetic condition is set true (via the existing `POST /api/prerequisites/{name}`) and reverts
      `priority_override` (letting the next `PlanRegenLoop` tick restore the plan-derived `priority` — never guesses the
      pre-park value); a manual override, `POST /api/backlog/{task_id}/unpark`, is also live. **Operator-visible
      surface**: `task_auto_parked`/`task_auto_unparked` activity events + `/api/state` `backlog_summary.auto_parked`
      dashboard count (same class as `needs_operator_count`). **Gate MET**: `tests/test_auto_park.py` +
      `tests/test_auto_park_reconcile.py` + `tests/test_skip_endpoint_cooldown_and_park.py` — a fleet-skipped task
      auto-parks with a visible reason at the Nth skip, not before; clearing the condition unparks it; idempotent (never
      double-parks once already parked).
- [x] ✅ [ADMIN] P2. **Wire the mvp-defi unpark — re-pointed to the live owner.** — this commit.
      `defi_consolidated_closeout_2026_07_18.md` Track 5 now carries the flip instruction (a new callout block + updated
      todo text): flip `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` true once R1→R3 have landed and Track
      5's backfill shows real progress on the per-instrument shard key — honestly still gated (Track 5 is C-GREEN-gated
      on T1→T3, R3 is `RUNNING, partial` as of this writing), not stale. `data_completion_defi_2026_07_15.md` B0 gets a
      pointer redirecting readers to the new home (its seed-chain framing is dead under the per-instrument
      re-architecture) instead of silently drifting. **Gate MET**: the owning plan carries the flip instruction; the
      condition is documented; the note itself is the named live flipper (with an explicit instruction to migrate it if
      Track 5 is ever archived/superseded) — the "no park exists without a named LIVE flipper" rule is asserted in prose
      here, enforcing it IN the auto-park mechanism itself is future work if a second silent-park incident recurs (not
      done — a mechanism-level enforcement would need every future manual park to register through this same store,
      which the manual RULES.md recipe does not currently do).
- [x] ✅ [BACKEND] P2. **Publish the store's contract for its other consumer.** — this commit. SSOT:
      `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "2. Task lifecycle" ("Skip / cooldown /
      park") — key namespacing, window semantics, change-triggered re-eligibility, and the full auto-park/unpark
      contract, `code_refs` updated. Notified `ao_fleet_observability_kpis_2026_07_20.md` directly (Progress Log entry +
      AF-1b todo text updated to "Unblocked 2026-07-20"). **Gate PARTIALLY MET**: the interface is documented and
      AF-1b's todo now points at it — "AF-1's owner has confirmed" cannot be satisfied by this same session (no live
      confirmation channel back); flagged as the one open half of this gate for whoever picks up AF-1b next.

## Safeguards

- Never `git reset --hard` / `git clean -fd` / `git checkout` a dirty tree — other agents share this repo.
- Commit only from a `quality-gates.sh`-green tree.
- **A cooldown that is too aggressive starves the fleet; one too lax restores the thrash.** Both failure directions are
  real — prefer the measured policy above over your own tuning instinct, and if you think a value is wrong, say so
  rather than quietly changing it.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — dispatch/skip/park model.
- `/codex/06-coding-standards/config-reloader-pattern.md` + the 2026-07-18 config split — why new tunables are env-free.
- `/codex/04-architecture/agent-orchestrator-alerting.md` — the park's operator-visible surface must be actionable-only.

## Progress Log

- **2026-07-20 — ALL FIVE TODOS SHIPPED.** Code: `agent-orchestrator@cfb211c` (QG green: ruff/format clean, basedpyright
  0/0/0, 1490 tests incl. 47 new — `server/state_store/cooldown.py` + `server/auto_park.py` +
  `server/auto_park_reconcile.py` + the `fleet_cooldown` FLEET dispatch filter + skip-endpoint/dashboard wiring). Design
  decisions taken per operator input at plan-start: the store's key is a generic opaque string (not `task_id`-only)
  specifically so AF-1's escalator backoff can reuse it without a second engine; the mvp-defi unpark flip instruction
  was written directly into `defi_consolidated_closeout_2026_07_18.md` Track 5 (not just re-pointed); the skip payload
  got a structured `reason_code` enum rather than free-text parsing. **Landed mid-session**: a sibling AO plan
  (`ao_fleet_observability_kpis_2026_07_20` AF-2, `agent-orchestrator@d098970`) merged into `live-defi-rollout` while
  this work was in flight — quickmerge's STAGE 0.4 autostash-rebase reconciled it cleanly (verified: no conflict
  markers, full quality gate + 1490 tests re-run green post-rebase before shipping). **One gate left half-open**: todo
  5's "AF-1's owner has confirmed" — the interface is published + AF-1b's todo text updated to "Unblocked", but no live
  confirmation loop exists back to this session; whoever picks up AF-1b next closes that half. **Not done, deliberately
  out of scope**: mechanism-level enforcement of "no park exists without a named LIVE flipper" (todo 4's closing
  sentence) — asserted in prose on the mvp-defi park specifically, not built into `auto_park.py` generically, since a
  manual RULES.md §4 park doesn't register through this store at all today. Tracked, not dropped:
  `plans/archive/issues/auto_park_no_flipper_rule_not_mechanism_enforced_2026_07_20.md`.
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
