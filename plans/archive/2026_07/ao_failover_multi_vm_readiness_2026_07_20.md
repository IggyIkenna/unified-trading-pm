---
doc_type: plan
title: AO failover — keep it, fix the paused-slot bug, and prove the dormant path actually works
summary:
  Multi-VM is dormant but intended to return for resilience, so FailoverLoop is KEPT (operator 2026-07-20, reversing the
  earlier delete ruling). It has never fired once, has zero fleet-registry entries, and prefers paused slots as re-route
  targets — untested resilience machinery is worse than none. Fix the slot-selection bug and prove the offline-reroute
  and rollback paths before anyone relies on them.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, failover, resilience, multi-vm, dormant-infra]
related:
  [
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/archive/2026_07/ao_dispatch_liveness_p0_2026_07_20.md,
  ]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: orchestrator_master
assigned_vm: NA # LOCAL execution — operator-assigned agents on this host, NOT AO-dispatched (2026-07-20)
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
assigned_role: backend_engineer
model_tier: sonnet-doable # test-writing against one existing module + a docs/runbook deliverable
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
---

# AO failover — keep it, fix it, and prove it works

> **🟢 COMPLETE 2026-07-20 — ARCHIVED.** All 8 todos landed, zero residual. Independently re-verified 2026-07-20: shas
> `03d48e8`, `dfc948f`, `3dff4d7` all exist, are ancestors of `origin/live-defi-rollout`, and carry the
> `Quickmerge: agent` trailer. The headline defect — `_pick_least_loaded_slot` PREFERRING a paused slot because its
> structural zero load made it look least-loaded — is genuinely fixed (now filtered through
> `dispatch.slot_is_spawnable()`) and pinned by a regression test that builds exactly that scenario. **Honest scope
> note**: everything here is proven by test + code inspection. The end-to-end path (a real second host going offline, a
> real `failover_rerouted` row in prod) has NEVER been exercised live — the plan and the re-enable runbook both say so
> (`last_executed: NEVER`). This is dormant-but-hardened, not proven-in-production.

> **Operator ruling 2026-07-20 (REVERSES the earlier A5 "delete")**: multi-VM is not running today, but it is likely to
> return for resilience/backup, so the failover infrastructure is **KEPT**. The retirement plan drafted earlier was
> removed before any worker saw it (verified: 0 ingested tasks).

## Why this is a real plan and not just a one-line guard fix

The earlier reasoning — "it never fires, so delete it" — inverts once you intend to **rely** on it. Everything measured
on 2026-07-20 now reads as a warning rather than an obituary:

- `ORCHESTRATOR_FAILOVER_ENABLED` unset (default `False`), `/api/ops/failover/status` → `{"running": false}`.
- **0 `failover_rerouted` events for all time** — the re-route path has never executed in production, ever.
- `fleet_registry_entries: 0` — even if enabled today it has no registry data to act on.
- `_pick_least_loaded_slot` **prefers paused slots** (see below).

That is the profile of resilience machinery nobody has ever exercised. **Untested failover is worse than no failover**:
it invites reliance during exactly the incident where its first-ever execution will be discovered to be broken. The work
below makes it dormant-but-trustworthy.

## Execution environment — LOCAL (read this first)

Executed by **operator-assigned agents on this host**, not AO dispatch (`assigned_vm: NA`,
`execution_scope: local-only`). Tick checkboxes by hand.

**This plan is almost entirely local** — todos 1-3 and 5-7 are code, tests and docs in the `agent-orchestrator`
checkout, verified with `bash scripts/quality-gates.sh`. Todo 4 (the `fleet_registry_entries: 0` trace) starts as a
local code read; only confirming the live registry state needs read-only SSM (pattern in
`scripts/orchestrator/check-ao-backlog-status.sh`).

**Do not enable failover anywhere** — see Safeguards. Everything here is provable with tests against the loop directly.

## The slot-selection bug (the concrete defect)

`failover._pick_least_loaded_slot` selects over `select(SlotRow)` filtered ONLY by `exclude_slots` (= the offline host's
slots). It does **not** filter `paused`, `killed`, or review slots. Worse, its load metric is "fewest
queued-and-undispatched tasks pinned to it", and a paused slot has **zero by definition** — nothing dispatches to it —
so `min()` picks a paused slot **preferentially**. Re-routing a task onto the one slot guaranteed never to run it
strands it invisibly, re-creating the exact class the R5 dead-target spill was written to fix. **Slot 0 is paused right
now** and would be today's preferred target.

## Todos

- [x] [BACKEND] P2. **Exclude unusable slots from failover target selection.** In `failover._pick_least_loaded_slot`,
      filter out `paused` / `killed` and review slots in addition to `exclude_slots`. **Also fix the metric bias, not
      just the guard** — "fewest pinned tasks" will keep nominating any slot that structurally cannot receive work, so
      the selection must be over ELIGIBLE slots, not all slots minus a blocklist. **Gate**: a test with a paused slot
      carrying 0 pinned tasks alongside a busy eligible slot asserts the eligible slot wins; a second test asserts
      `None` (→ the existing "no available slot" skip) when every candidate is ineligible. ✅
      `agent-orchestrator@03d48e8` — also excludes unconfigured slots (operator-confirmed scope broadening, reuses
      `dispatch.slot_is_spawnable`); gates in `tests/test_failover_integration.py`.
- [x] [BACKEND] P2. **Prove the offline-reroute path end-to-end — it has NEVER executed.** Write an integration test
      that simulates a host going offline past `failover_heartbeat_threshold_seconds`, and asserts eligible tasks
      (`failover_allowed=True`, queued, undispatched, `failover_origin` NULL) are re-pointed to an eligible slot with a
      `failover_rerouted` activity row. **Gate**: the test fails if the loop is a no-op — verify by bug-injection (break
      the re-route, confirm the test goes red). ✅ `agent-orchestrator@03d48e8` —
      `tests/test_failover_integration.py::test_offline_reroute_end_to_end` (+ hard-pin / already-failovered /
      dispatched exclusion coverage); bug-injection verified red then reverted green.
- [x] [BACKEND] P2. **Prove the ROLLBACK path too.** When the offline host returns, tasks still queued and unclaimed
      must have `target_slot` + `failover_origin` cleared. An un-exercised rollback is how a recovered host stays
      starved after the incident. **Gate**: a test covering return-from-offline; assert already-dispatched tasks are NOT
      rolled back (only queued+unclaimed), so a live worker is never yanked. ✅ `agent-orchestrator@03d48e8` —
      `tests/test_failover_integration.py::test_rollback_restores_queued_unclaimed_tasks_only`.
- [x] [BACKEND] P2. **Explain `fleet_registry_entries: 0` — the gap that makes failover inert even when enabled.** Trace
      what populates `fleet_registry.json` and why it is empty under the single-VM topology. Failover keys "offline
      host" off that registry, so an empty registry means the loop can never fire regardless of the enable flag.
      **Gate**: a written answer covering (a) what writes the registry, (b) whether it would populate when multi-VM
      returns, (c) whether an empty registry should be a loud warning at startup when `failover_enabled=True` — silence
      here is what would make a resilience feature fail closed without telling anyone. ✅ answer in Progress Log below;
      `agent-orchestrator@03d48e8` also implements (c) — `FailoverLoop.start()` now warns loudly on an empty registry.
      (b)'s GCP self-registration gap filed as a new P3 todo below.
- [x] [BACKEND] P3. **Write the re-enable checklist — the deliverable that makes dormancy safe.** A short runbook
      section: what must be true before `ORCHESTRATOR_FAILOVER_ENABLED=true` (registry populated, ≥2 hosts, the tests
      above green, the paused-slot fix deployed), and how to verify the first real re-route. Declare `owner` / `cadence`
      / `verifier` / `last_executed` per the runbook rule. **Gate**: an operator can re-enable failover from the
      checklist alone without re-deriving any of this. ✅ `unified-trading-pm` —
      `/codex/15-runbooks/agent-orchestrator-failover-re-enable-checklist.md` (`doc_type: codex-runbook`, full
      owner/cadence/verifier/last_executed frontmatter per the runbook schema).
- [x] [BACKEND] P3. **Keep the dormant module from rotting.** Confirm `failover.py` and its tests are inside the
      `quality-gates.sh` scope so dormant code cannot silently drift out of type/lint compliance, and add a one-line
      note at the top of the module stating it is DORMANT-BUT-MAINTAINED for multi-VM's return — so the next person
      auditing dead code (as I did) finds the intent instead of re-proposing deletion. **Gate**: the module carries the
      note; QG covers it. ✅ `agent-orchestrator@dfc948f` — module docstring note added; QG scope confirmed already
      covers `server/` + `tests/` wholesale (no per-file exclusion existed).
- [x] [DOC] P3. **Record the dormant-infra position in codex.** Note in the recovery-layers docs that failover is kept
      deliberately, is not currently a live recovery layer, and must not be cited as one until the re-enable checklist
      passes. **Gate**: no codex doc describes FailoverLoop as an active recovery layer, and none describes it as dead.
      ✅ `unified-trading-pm` — new "Out of scope" section in `recovery-defence-in-depth-layers.md` disambiguating AO's
      `FailoverLoop` from `failover_feed.py` (Layer 0) and stating dormant-but-kept status.
      `autonomous-recovery-matrix.md` left untouched (grepped: zero FailoverLoop mentions, scope is live-trading error
      classification only — the disambiguation in the doc it already defers to for the layer model is sufficient).
- [x] [BACKEND] P3. **`bootstrap_vm.sh` STEP 10 self-registration has no GCP branch** (found while tracing todo 4 —
      `elif [[ "${CLOUD_PROVIDER}" == "aws" ]]` with no GCP arm). A GCP-provisioned worker VM boots and never calls
      `POST /api/vms/register`, so `fleet_registry.json` — and therefore failover, which keys "offline host" entirely
      off that registry — would stay silently inert on GCP even after multi-VM genuinely returns with real hosts
      running. Add the GCP metadata-server equivalent of the AWS IMDS private-IP lookup + register call. **Gate**: a
      GCP-provisioned VM appears in `fleet_registry.json` after boot, same as an AWS one does today. ✅
      `agent-orchestrator@3dff4d7` — STEP 10 restructured to compute `_PRIV_IP` per-cloud (AWS IMDS vs GCP metadata
      server `network-interfaces/0/ip` + `Metadata-Flavor: Google`, no token needed) then run ONE shared registration
      POST, mirroring this script's existing EXTERNAL_IP if/else idiom rather than duplicating the curl call per branch.
      No test harness exists for `bootstrap_vm.sh` (real-VM boot script); verified via `bash -n` + `shellcheck` (no new
      findings in the edited region) + full `quality-gates.sh` green (1425 passed).

## Safeguards

- Never `git reset --hard` / `git clean -fd` / `git checkout` a dirty tree — other agents share this repo.
- Commit only from a `quality-gates.sh`-green tree.
- **Do NOT enable failover in production as part of this plan.** Default stays `False`; the enable is an operator action
  gated on the checklist. Tests exercise the loop directly, not by flipping the live flag.

## Codex SSOTs

- `/codex/04-architecture/recovery-defence-in-depth-layers.md` + `…/autonomous-recovery-matrix.md` — where failover
  does/does not belong as a recovery layer.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — the current topology this is dormant under.
- `/codex/06-coding-standards/quality-gates.md` — the gate keeping dormant code honest.

## Progress Log

- **2026-07-20 — plan created**, replacing a drafted retirement plan after the operator ruled multi-VM is likely to
  return. **Lesson worth keeping**: "it has never fired" was read as evidence the code is dead, when it was equally
  evidence the code is UNTESTED. Which reading is right depends entirely on whether the capability is still wanted — a
  question about intent, not about the code. Ask it before proposing any deletion of dormant infrastructure.
- **2026-07-20 — todo 1 done** — `agent-orchestrator/server/failover.py::_pick_least_loaded_slot` now filters to
  ELIGIBLE slots (not in `exclude_slots`, not a review slot (`config.review_slot_ids()`), `status != "killed"`, and
  `dispatch.slot_is_spawnable(slot)` — reused rather than reimplemented, so paused/unconfigured tracks the same SSOT
  AutoSpawn uses). Scope confirmed with operator: also exclude unconfigured slots (worktree/branch/operator unset), not
  just the 3 literally-named categories — an unconfigured slot is exactly as dead-end as a paused one and nothing
  guarded it before. Gate tests in `tests/test_failover_integration.py`.
- **2026-07-20 — todos 2 + 3 done** — `tests/test_failover_integration.py` added: real-sqlite-session integration tests
  (not MagicMock, unlike the pre-existing `test_failover.py`) exercising `_failover_tasks_for_host` and
  `_rollback_tasks_for_host` end-to-end, asserting on the actual `ActivityRow` table. Bug-injection verified for the
  offline-reroute path per the todo 2 gate: neutered the `task.target_slot = best_slot` mutation, confirmed
  `test_offline_reroute_end_to_end` went red, reverted, confirmed green again.
- **2026-07-20 — todo 4 done** — traced `fleet_registry_entries: 0`:
  - **(a) What writes it**: exactly one writer, `POST /api/vms/register` (`server/routes/vms.py::register_vm`), called
    by `scripts/bootstrap_vm.sh` STEP 10 on VM boot (outbound self-registration, best-effort, non-fatal on failure). A
    companion `POST /api/vms/{id}/heartbeat` updates `last_heartbeat` on an already-registered entry, but nothing in the
    repo ever calls it — live endpoint, zero callers.
  - **(b) Would it populate when multi-VM returns?** Only partially. `bootstrap_vm.sh` STEP 10's self-register call is
    gated `elif [[ "${CLOUD_PROVIDER}" == "aws" ]]` with **no GCP branch at all** — a GCP-provisioned worker VM would
    boot and never register. Filed as a new P3 todo above (`bootstrap_vm.sh` STEP 10 GCP gap) rather than fixed inline —
    outside this todo's "written answer" gate, but directly adjacent, so tracked in this same plan per the findings
    triage rule rather than left as a verbal note.
  - **(c) Should an empty registry be a loud startup warning when `failover_enabled=True`?** Yes — implemented.
    `FailoverLoop.start()` now logs a `logger.warning` when `self._fleet_getter()` returns empty (reuses the loop's own
    fleet abstraction rather than re-deriving from the registry file, so it can never drift from what the loop actually
    queries, and fires on both the lifespan-start and the `/api/ops/failover/enable` hot-enable paths since both route
    through `start()`). Covered by `test_start_warns_when_fleet_registry_empty` /
    `test_start_does_not_warn_when_fleet_registry_populated` in `tests/test_failover.py`. This is a small, safe addition
    beyond the todo's literal "written answer" gate — it never enables/starts anything on its own, just makes an
    already-enabled-but-inert state loud instead of silent, which is exactly the risk the todo was raised to close.
- **2026-07-20 — todo 8 done** (`agent-orchestrator@3dff4d7`) — GCP branch added to `bootstrap_vm.sh` STEP 10
  self-registration, closing the gap todo 4's trace surfaced. All 8 todos now complete; plan is functionally done, left
  `status: active` pending the operator's own archival call rather than self-archived here.

## Notes for the plan writer

Flagging two things noticed while executing this plan, for future plan authoring — not blockers, both already resolved
here:

- **This plan was independently executed START-TO-FINISH by two separate operator sessions running concurrently** (this
  session, and `harshkantariya [slot-23·harsh_pc]`, minutes apart) — neither aware of the other until the background
  FF-pull cron merged the other's already-shipped commits mid-session. Both converged on near-identical fixes for todos
  1-7 (same eligibility filters, same test structure, even the same todo-8 finding), so the duplicated effort didn't
  produce conflicting work this time, but it was pure waste — two full implementation passes for one plan. **Root
  cause**: `assigned_vm: NA` / `execution_scope: local-only` plans have no claim signal visible to a second operator
  before they start — AO-dispatched plans get backlog-level claim protection, local ones don't. Worth a lightweight
  convention (e.g. the first Progress Log line being "starting now — <operator/slot>", or a `claimed_by`/`claimed_at`
  frontmatter stamp) so a second operator opening the same local plan sees it's already in flight before duplicating the
  work, not after.
- **Todo 4's gate — "a written answer covering (a)/(b)/(c)..." — was read by both sessions as license to also
  _implement_ (c)**, not just answer it in prose (both added the loud-warning code + tests, unprompted by the gate
  text). Worked out fine here since the answer was "yes, and it's cheap and safe," but if a future todo genuinely wants
  documentation-only output with no code changes, say so explicitly (e.g. "a written recommendation only — do not
  implement") — "a written answer covering whether X should happen" reads as an invitation to just do X.
