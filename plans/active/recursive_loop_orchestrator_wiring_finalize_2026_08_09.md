---
doc_type: plan
title: Finalize — RecursiveLoopOrchestrator wiring plan reconciliation + archival
summary: >-
  Gated finalize companion to recursive_loop_orchestrator_wiring_2026_08_09.md. Reconciles every completed todo's
  evidence back into the source issue doc's [DESIGN] todo, re-checks the Family-2 hedge-poller audit's deferred outcome,
  and runs the 6-step archival ritual on the now-complete parent plan.
status: active
nature: process
asset_group: [defi]
stage: [strategy]
repos: [strategy-service, execution-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [defi, carry, recursive-loop, finalize, archival]
related:
  [
    /plans/archive/2026_08/recursive_loop_orchestrator_wiring_2026_08_09.md,
    /plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
depends_on: [recursive_loop_orchestrator_wiring_2026_08_09]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  Companion finalize plan, authored alongside recursive_loop_orchestrator_wiring_2026_08_09.md per the workspace's
  mandatory finalize-plan-for-every-AO-plan rule.
context_scope:
  [
    /plans/archive/2026_08/recursive_loop_orchestrator_wiring_2026_08_09.md,
    /plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md,
  ]
---

# Finalize — RecursiveLoopOrchestrator wiring

## Todos

- [x] ✅ [REVIEW] P1. Re-verify each of `recursive_loop_orchestrator_wiring_2026_08_09.md`'s 8 todos: confirm the cited
      commit(s) actually exist and the cited test(s) actually pass green (re-run, don't trust the recorded evidence line
      alone). Reconcile the evidence into
      `plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md`'s `[DESIGN]`
      `RecursiveLoopOrchestrator` translation-layer todo — flip it `[x]` done, citing every repo@sha this plan produced.
      Repo: unified-trading-pm. Done-when: the source doc's todo is flipped with a full evidence trail, and re-running
      each cited test independently still passes.
- [x] ✅ [REVIEW] P2. Re-check the Family-2 hedge-poller audit todo's outcome (recursive_loop_orchestrator_wiring's 6th
      todo): if it found no suitable poller existed and filed a follow-up `[DESIGN]` todo, confirm that follow-up was
      actually filed (not just mentioned in prose) as a real `- [ ]` item somewhere trackable — file it now if it was
      described but never actually written as a checkbox. Repo: unified-trading-pm. Done-when: the follow-up either
      doesn't apply (a poller was found and wired) or exists as a real tracked `- [ ]` todo. — unified-trading-pm.
      Independently re-verified 2026-08-09 (slot 29, review): the parent plan's todo 6 outcome is
      `(b) no suitable     poller exists` (confirmed via the parent plan's own Progress Log + Todos section —
      `HealthFactorMonitor` has zero production callers, no Cloud-Scheduler endpoint exists); the required follow-up
      `[DESIGN]` todo IS a real trackable `- [ ]` checkbox in this same file (todo 4 below, "Decide + scope the RIGHT
      mechanism..."), not prose-only — confirmed via direct grep of the live file content, not a trust of the prior
      session's claim.
- [x] ✅ [DOC] P1. Run the standard 6-step archival ritual on `recursive_loop_orchestrator_wiring_2026_08_09.md` once
      every one of its todos is `[x]` and unlocked: move it to `plans/archive/2026_08/`, fix every corpus referrer path
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`), and confirm `run_hygiene_sweep.sh` stays
      green. Repo: unified-trading-pm. Done-when: the file is under `plans/archive/2026_08/`, `status: complete`, 0
      broken referrer links, hygiene sweep green.
- [x] ✅ [DESIGN] P2. Decide + scope the RIGHT mechanism to make `PerpHedgeSizer.compute_rebalance()`/
      `.compute_margin_topup()` (Family-2 `CARRY_BASIS_PERP_INV`) live-reachable on its documented 5-min poll cadence
      (`perp_hedge_sizer.py:60-63`). The parent plan's todo 7 audit (2026-08-09, slot 8) confirmed execution-service has
      **no suitable existing poller**: `HealthFactorMonitor` (`defi_execution/monitors/health_factor_monitor.py`) is a
      real asyncio poll-loop primitive but itself has zero production callers (not started in `api/app.py`'s
      `@app.on_event("startup")` or `cli/main.py`); `start_domain_config_reloaders()` (the one live-reachable
      scheduling-adjacent mechanism, `api/app.py:149-152`) wraps UTL's pub/sub event-driven `DomainConfigReloader` —
      wrong shape for a fixed-cadence business-logic tick; no Cloud-Scheduler-triggered HTTP endpoint exists anywhere in
      the service. Candidate shapes weighed (operator/main judgment call, not a worker's to freehand): (1) a new
      `HealthFactorMonitor`-pattern in-process asyncio poll loop wired at `api/app.py` startup, one instance per open
      Family-2 position; (2) a Cloud-Scheduler-triggered admin HTTP endpoint (5-min cron hitting execution-service,
      mirroring how other periodic jobs in the workspace are wired — see
      `/codex/05-infrastructure/vm-launcher-runbook.md`-adjacent scheduled-job patterns); (3) piggybacking on
      strategy-service's existing `V2EngineOrchestrator.on_tick()` cadence via the same `leg_controller_runner.py`
      bridge `recursive_loop_runner.py` already uses, rather than adding a second independent scheduler to
      execution-service. Repo: execution-service (+ possibly infra, if Cloud Scheduler is the ruled shape). Done-when:
      the operator/main rules on the mechanism, and a properly-scoped implementation todo (with exact done-when + test
      plan) is filed against that ruling.

      **RULED 2026-08-09 (main, via BLK-b0af53e2, slot 4)**: option (1) — clone the `HealthFactorMonitor` pattern into a
                  new in-process asyncio poll loop in execution-service, wired at `api/app.py` startup, one instance per open
                  Family-2 position, 5-min interval. Rationale: reuses a proven, already-shipped primitive in the SAME service
                  (lowest implementation risk, no new operational surface to build/debug); keeps `PerpHedgeSizer` + on-chain/
                  perp-venue reads colocated in execution-service, matching the T4 no-service-to-service-dependency tier-import rule
                  (`/codex/04-architecture/tier-and-import-architecture.md`) rather than introducing new coupling. Option (2)
                  rejected — needs new Cloud Scheduler infra plus an admin HTTP auth surface not yet proven for this shape in this
                  service, disproportionate blast radius for what an in-process timer already satisfies. Option (3) rejected — per
                  code evidence gathered for the blocked-question (`recursive_staked.py`'s `_on_tick_family2_basis_perp_inv()` only
                  opens the Family-2 position ONCE, guarded by `if self.current_position_units != 0: return []`, and its own
                  docstring already frames live rebalancing as "a separate, not-yet-wired poll-cycle concern" — reusing on_tick
                  would require reworking that one-shot-open guard and conflates market-tick-driven cadence with a fixed 5-min poll
                  requirement). Properly-scoped implementation todo filed as todo 5 below, same-turn.

- [x] ✅ [BACKEND] P2. Implement the `HealthFactorMonitor`-pattern asyncio poller CLASS for `PerpHedgeSizer` (Family-2
      `CARRY_BASIS_PERP_INV`), per todo 4's 2026-08-09 ruling (option A). Build a new `PerpHedgeMonitor` class in
      `execution-service/execution_service/defi_execution/monitors/` (sibling to `health_factor_monitor.py`, same
      asyncio poll-loop shape: `run()`/`stop()`/`_poll_loop()`, default interval 300s per `perp_hedge_sizer.py:60-63`'s
      documented 5-min cadence). Each instance owns ONE open Family-2 position (perp_venue + perp_pair + wallet), reads
      on-chain Aave data + LST exchange rate (via injected `fetch_*` callables), calls
      `PerpHedgeSizer.read_e_from_aave_data()` then `.compute_rebalance()`/`.compute_margin_topup()` each tick, and on a
      non-NOOP rebalance action or a non-null margin-topup instruction, calls caller-injected `dispatch_rebalance`/
      `dispatch_margin_topup` callables (the actual execution-path wiring is scoped OUT to todo 7 below, per the
      2026-08-09 BLK-7f4d33db ruling). Repo: execution-service. Done-when: (1) unit tests cover `PerpHedgeMonitor`'s
      NOOP/SHORT/COVER rebalance branches + margin-topup triggered/not-triggered, using injected fake `fetch_*`
      callables (mirrors `HealthFactorMonitor`'s existing test pattern — no live network calls); (2) `quality-gates.sh`
      green on execution-service. Codex SSOTs: `/codex/04-architecture/tier-and-import-architecture.md`,
      `/codex/04-architecture/defi-execution-overview.md`. — execution-service@7e4e6b8c. Unit tests: 7 tests (NOOP,
      SHORT, COVER, margin-topup triggered, margin-topup not-triggered, poll-error-no-crash, stop-terminates), all
      green. `quality-gates.sh` full run green (199s) on the committed HEAD (re-ran after commit per the
      commit-before-QG ordering rule — the first QG pass ran on the dirty pre-commit tree and its sentinel didn't carry
      forward). App.py startup/shutdown wiring + the "same execution path as `recursive_loop_runner.py`" integration
      test are OUT of this todo's scope now — see todo 7.

- [x] ✅ [DESIGN][BACKEND] P2. Build the open-Family-2-position registry `PerpHedgeMonitor` needs to source genuine
      currently-open positions from, per main's 2026-08-09 ruling on BLK-7f4d33db (option C — overriding the worker's
      recommended option B of an honest-empty interim source): shipping `PerpHedgeMonitor` wired to a permanently-empty
      position source would satisfy the letter of "wired at startup" while providing ZERO actual margin/liquidation risk
      coverage — the smoke-test-green-not-operationally-shipped anti-pattern CLAUDE.md's "Plans run to actual
      completion" rule rules out. Also resolve the cross-repo premise gap the ruling surfaced: Family-2 positions are
      actually opened by strategy-service's `recursive_staked.py._on_tick_family2_basis_perp_inv()`, NOT via
      execution-service's `RecursiveLoopOrchestrator`/`recursive_loop_runner.py` (that bridge module has zero production
      callers per todo 4's grep evidence) — so a zero-callers grep on the execution-service side alone does NOT
      establish there are zero live on-chain Family-2 positions today; it only establishes the execution-service
      tracking bridge was never wired. Design + build the registry (its exact shape — e.g. what
      recursive-loop-open/unwind call sites register into, and how it learns about positions opened via the
      strategy-service path today — is this todo's own scope to resolve, not pre-decided here). Repo: execution-service
      (+ read-only investigation of strategy-service's `recursive_staked.py` to confirm the open/close call sites).
      Done-when: a registry component exists that can enumerate currently-open Family-2 positions (perp_venue +
      perp_pair + wallet + `HedgeSizerConfig` per position) genuinely reflecting live on-chain state (or an honest,
      explicitly-flagged interim source with a filed follow-up if live on-chain enumeration needs infra this todo can't
      reach), with unit test coverage; `quality-gates.sh` green on every touched repo. Codex SSOTs:
      `/codex/04-architecture/defi-execution-overview.md`, `/codex/04-architecture/tier-and-import-architecture.md`. —
      execution-service@8a76e2f1. Investigated `recursive_staked.py` (read-only, strategy-service): confirmed Family-2
      positions ARE opened there via `_on_tick_family2_basis_perp_inv()`, which publishes an `AtomicInstruction`
      (`instrument_type=RECURSIVE_LENDING_LOOP_PERP_HEDGED`) onto the same published `atomic_instruction` event-log
      shard `atomic_instruction_router.py` already subscribes to (the live=batch `EventTransport` spine every
      strategy->execution hand-off on this workspace uses) — so `Family2PositionRegistry` reads that SAME log rather
      than inventing a parallel source or shipping a permanently-empty stub. Two genuine, explicitly-flagged interim
      gaps surfaced (both filed as real tracked todos below, not left as prose, per the done-when's own escape hatch):
      (1) `_on_tick_family2_basis_perp_inv()` never emits a close/unwind instruction for Family 2 today, so the registry
      correctly treats every observed open as currently-open — filed as todo 8 for when a real unwind path ships; (2)
      neither `AtomicInstruction` nor its attestations carry a wallet identifier anywhere in the pipeline (confirmed via
      direct inspection of `_build_family2_instruction`) — the registry emits a caller-supplied `default_wallet` label
      instead of fabricating one, filed as todo 9. 6 unit tests (enumerate-one, skip-family1, skip-non-strategy-source,
      skip-unknown-perp-venue, skip-malformed-payload, enumerate-multiple-with-shared-wallet), all green.
      `quality-gates.sh` full green (169s) on the committed HEAD (commit-before-QG ordering rule followed — first pass
      ran pre-commit on the dirty tree and its sentinel didn't carry forward, re-ran post-commit).

- [ ] [BACKEND] P3. Add unwind/close consumption to `Family2PositionRegistry` (todo 6) once strategy-service's
      `recursive_staked.py` ships a real Family-2 close/unwind emission path — today `_on_tick_family2_basis_perp_inv()`
      never emits one (confirmed via todo 6's own investigation), so every observed Family-2 open event is, correctly
      for now, treated as currently-open; that assumption goes stale the moment a real unwind path exists unless this
      follow-up ships alongside it. Repo: execution-service. Done-when: the registry also consumes a Family-2
      close/unwind event (correlating on `correlation_id`/`instruction_id`) and retires the matching open position from
      `enumerate_open_positions()`'s output; unit test covers the retire path.

- [ ] [DESIGN][BACKEND] P3. Add a genuine per-position wallet attestation to the Family-2 `AtomicInstruction` pipeline —
      today neither the instruction nor its attestations carry a wallet identifier anywhere (confirmed via todo 6's
      direct inspection of `recursive_staked.py::_build_family2_instruction`), so `Family2PositionRegistry` emits a
      caller-supplied `default_wallet` placeholder for every position instead of the real per-position wallet. Repo:
      strategy-service (emit the attestation) + execution-service (`Family2PositionRegistry` reads it instead of the
      placeholder). Done-when: `OpenFamily2Position.wallet` reflects the real per-position wallet sourced from the
      instruction, not a shared default; unit test covers a multi-wallet scenario.

- [ ] [BACKEND] P2. Wire `PerpHedgeMonitor` lifecycle at `execution-service/execution_service/api/app.py`'s
      `@app.on_event("startup")`/`@app.on_event("shutdown")`, sourcing the currently-open Family-2 position set from
      todo 6's registry (one `PerpHedgeMonitor` instance per open position, matching shutdown stop-all), and route each
      instance's `dispatch_rebalance`/`dispatch_margin_topup` callables through the SAME instruction-execution path
      `recursive_loop_runner.py` already uses — do NOT invent a second dispatch path. Repo: execution-service.
      Done-when: (1) an integration/wiring test confirms `app.py` startup creates one monitor instance per open Family-2
      position (per todo 6's registry) and shutdown stops them cleanly; (2) `quality-gates.sh` green on
      execution-service; (3) confirms the emitted rebalance/topup instructions reach the same execution path as
      `recursive_loop_runner.py`'s outputs (no second, divergent instruction sink). Codex SSOTs:
      `/codex/04-architecture/tier-and-import-architecture.md`, `/codex/04-architecture/defi-execution-overview.md`.

## Progress Log

- **2026-08-09**: authored alongside the parent plan as `status: active` — held purely via
  `depends_on: [recursive_loop_orchestrator_wiring_2026_08_09]` + `gate_on_depends: true` (dispatch stays
  machine-blocked until the parent's todos complete), not the draft-gated phase-chain pattern — the hygiene gate flagged
  `status: draft` here as redundant once `gate_on_depends` already holds it (`task_template.md` §4).
- **2026-08-09 (slot 8, backend_engineer)**: Added the `[DESIGN]` follow-up todo above per the parent plan's todo 7
  audit outcome (no suitable existing poller for `PerpHedgeSizer` — full grep evidence in the parent plan's Progress
  Log). This satisfies todo 2 above's "confirm the follow-up was actually filed as a real `- [ ]` item" check in advance
  — filed now rather than left as prose.
- **2026-08-09 (slot 25, review)**: Todo 1 shipped — independently re-verified all 8 of the parent plan's todos.
  Confirmed all 6 distinct cited commits exist AND are ancestors of `origin/live-defi-rollout`
  (`unified-api-contracts@547b1d1b`, `strategy-service@b98f74fb`/`817bb4e0`/`f2ac7fdf`/`d6c86f44`,
  `execution-service@2352a17e`). Re-ran full `quality-gates.sh --no-fix` (not just the cited unit tests — the full
  suite, per RULES.md's "never run pytest directly") on all 3 touched repos, all green: unified-api-contracts (396s,
  includes `resolve_ltv_mode` 0.93/0.945/0.86 assertions), strategy-service (5836 passed, 199s, includes the
  `n_loops`/`ltv_per_loop` catalog tests + both Family-1/2 `on_tick()` test files), execution-service (7895 passed,
  226s, includes `test_recursive_loop_runner.py`). Confirmed both archetypes are genuinely absent from
  `_ALLOWED_EMPTY_ARCHETYPES` (todo 8) via direct dict-content inspection, not just a checkbox read. Re-ran todo 7's
  audit greps verbatim — findings match exactly (no suitable poller exists; `HealthFactorMonitor` has zero production
  callers; no Cloud-Scheduler endpoint). Flipped the source issue doc's `[DESIGN]` `RecursiveLoopOrchestrator`
  translation-layer todo (`defi_catalog_engine_config_key_contract_drift_2026_07_23.md`) to `[x]` with the full evidence
  trail. Found + recorded (non-blocking) two minor evidence-line inaccuracies in the parent plan's Progress Log: the
  Family-1 `on_tick()` test file has 5 tests not the claimed 6; `test_recursive_loop_runner.py` has 11 tests not the
  claimed 13 — both files are correct and complete, only the narrated counts were off; not worth a follow-up todo.
- **2026-08-09 (slot 29, review)**: Todo 2 shipped — independently re-checked the parent plan's todo 6 (Family-2
  hedge-poller audit) outcome and confirmed the required follow-up `[DESIGN]` todo (todo 4 in this file) is a genuine
  tracked `- [ ]` checkbox, not prose-only. No new todo needed — slot 8 already filed it correctly on 2026-08-09.
- **2026-08-09 (slot 10, backend_engineer)**: Todo 3 shipped — ran the standard 6-step archival ritual on
  `recursive_loop_orchestrator_wiring_2026_08_09.md`. (1) Deferral migration: already satisfied — todo 7's poller-audit
  finding was already tracked as this file's own todo 4 (`[DESIGN]`), no new todo needed. (2) Added the
  `✅ ARCHIVED 2026-08-09` banner + flipped `status: complete` +
  `superseded_by: recursive_loop_orchestrator_wiring_finalize_2026_08_09` in the parent plan's frontmatter. (3)+(4)
  Codex-alignment: both archetype SSOTs
  (`/codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-lending-only.md`,
  `.../carry-basis-perp-inv.md`) had `implementation_status: design`, now stale given this plan shipped the real
  translation layer + `RecursiveLoopOrchestrator`'s first production caller — bumped both to `code-shipped` with a new
  "Translation-layer status" section citing the exact shipped commits (`strategy-service@817bb4e0`/`f2ac7fdf`,
  `execution-service@2352a17e`) and noting the still-open perp-hedge-poller gap (this file's todo 4). No CLAUDE.md
  change needed — no new cross-cutting HARD RULE, just a domain implementation-status update already covered by the
  existing Strategy domain-index pointer. (5) Corpus-wide referrer sweep
- **2026-08-09 (slot 4, backend_engineer)**: Todo 4 shipped — this was an explicit operator/main judgment call per its
  own text ("not a worker's to freehand"), so read the actual code
  (`perp_hedge_sizer.py`/`recursive_staked.py`/`health_factor_monitor.py`, confirming `PerpHedgeSizer` has zero callers
  anywhere and Family-2's `on_tick()` only ever opens the position once) and escalated via `/blocked` (BLK-b0af53e2)
  with 3 options + an evidence-based recommendation (option A). Main ruled A. Recorded the full ruling + rationale
  inline on todo 4 and flipped it `[x]`; filed the properly-scoped implementation todo (with exact done-when + test
  plan) as this file's new todo 5, per todo 4's own done-when requirement. Did not implement the poller itself — that is
  todo 5's own scope, not this todo's.

  (`grep -rl 'recursive_loop_orchestrator_wiring_2026_08_09'`) found 5 referrers besides the plan+finalize pair itself:
  `plans/active/INDEX.md` (auto-generated, regenerated via `scripts/plans/regenerate_active_plan_index.py` rather than
  hand-edited), `plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md` (2 prose citations,
  repointed `/plans/active/...` → `/plans/archive/2026_08/...`), and this file's own `related:`/`context_scope:` entries
  (repointed the same way; `depends_on:` left as the bare slug `recursive_loop_orchestrator_wiring_2026_08_09` per
  convention — that field is machine-parsed and location-independent). The 2 codex docs' new citations already point at
  the archive path from authoring. (6) `git mv` to
  `plans/archive/2026_08/recursive_loop_orchestrator_wiring_2026_08_09.md` as a commit separate from this checkbox
  flip + the content edits (never combine a checkbox flip with a `git mv` in one commit, per the ritual's own SSOT) — no
  lock existed to clear. `run_hygiene_sweep.sh` re-run green after the move (see commit evidence below).

- **2026-08-09 (slot 5, backend_engineer)**: Started todo 5 (`PerpHedgeMonitor` implementation). Read
  `RecursiveLoopOrchestrator` (stateless, no position registry), `recursive_loop_runner.py` (zero production callers —
  confirmed by grep, only its own unit test references it), and `UnifiedPositionTracker`
  (`execution_service/engine/live/positions.py`, a generic venue qty/PnL cache with no Family-2 identity fields) and
  found todo 5's own done-when premise — "source the open-position set from the same place `RecursiveLoopOrchestrator`/
  its callers already track open loops... don't invent a new registry" — false: no such registry exists anywhere in
  execution-service. Escalated via `/blocked` (BLK-7f4d33db) with 3 options + recommendation B (ship the class fully
  tested with an honest-empty interim position source). **Main overrode with option C**: pause the wiring, file a new
  prerequisite registry-building todo first (also surfacing that Family-2 positions are actually opened via
  strategy-service's `recursive_staked.py._on_tick_family2_basis_perp_inv()`, not execution-service's
  `RecursiveLoopOrchestrator` — so the "zero callers" grep only proves the execution-service bridge is unwired, not that
  zero live positions exist). Split former todo 5 into three: todo 5 (this session's actual scope — ship the
  `PerpHedgeMonitor` class + full unit tests, DONE, `execution-service@7e4e6b8c`), todo 6 (new prerequisite — build the
  open-Family-2-position registry), todo 7 (rescoped — wire `PerpHedgeMonitor` at `app.py` startup/shutdown against todo
  6's registry + the execution-path integration test). `quality-gates.sh` green on execution-service (both the
  dirty-tree pre-commit run and the correct post-commit re-run, per the commit-before-QG ordering rule).
- **2026-08-09 (slot 10, backend_engineer)**: Todo 6 shipped — `Family2PositionRegistry`
  (`execution_service/defi_execution/monitors/family2_position_registry.py`), `execution-service@8a76e2f1`. Read the
  actual `atomic_instruction` publish/subscribe contract (`strategy_service.engine.strategies.v2.live_routing` publish
  side + `execution_service.v2.atomic_instruction_router` read side) rather than inventing a new mechanism — the
  registry reuses that module's own `ATOMIC_INSTRUCTION_DATA_TYPE`/`ATOMIC_INSTRUCTION_SOURCE` constants and reads the
  same shard via the UTL `EventTransport` facade. Filed the two honest interim-source gaps as real todos (8, 9) per the
  done-when's own escape hatch, rather than leaving them as docstring prose.
