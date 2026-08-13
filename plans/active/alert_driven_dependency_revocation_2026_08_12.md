---
doc_type: plan
title:
  Alert-driven dependency revocation — drain dependent VMs and Cloud Run jobs when the alert that invalidates their
  inputs fires
summary: >-
  Today an alert fires and nothing downstream reacts. A dead manifest consolidator, a catalogue 24h stale, or a VM that
  drained without capturing anything all leave dependent VMs downloading into a pipeline whose inputs are already known
  bad — the measured money-burn the operator named. This plan wires every alert across the three channels to a
  dependency action, keyed on AlertCode identity rather than severity tier (four separate routing bugs found 2026-08-12
  had a correct code routed at the wrong tier, so anything keyed on tier inherits all four). Revocation is
  drain-at-checkpoint ONLY — never terminate — which removes the per-prefix checkpoint-resume audit as a prerequisite
  and makes the 71 launcher prefixes bound to None a non-special case. Policy lives in one evaluator
  (instruments_preflight_dag, already the admission-gate SSOT); two delivery paths consume it — a push actuator that
  ships without touching any launcher, and a VM-side poll hook that lands incrementally as a fail-closed backstop. Phase
  1 is a hard prerequisite — a graceful-flush contract that every buffered writer honours, because drain-only is only
  safe if a drained unit writes out the shards it is holding.
status: active
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos:
  [unified-trading-library, unified-api-contracts, deployment-service, deployment-api, alerting-service, e2e-testing]
scope: [engineer, admin]
tags: [alerting, self-healing, vm-lifecycle, cost-control, drain, dependency-dag, escalation]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/recovery-defence-in-depth-layers.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md,
    /plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md,
  ]
created: "2026-08-12"
last_updated: 2026-08-12
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 9
estimate_calibrated_ai_days: 7.2
assigned_role: infra
effort: xhigh # 63 todos across 6 repos; data-correctness stakes (a wrong drain edge destroys in-flight shards)
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/data-pipeline-alerts.registry.yaml,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    unified-trading-library/unified_trading_library/manifest_writer/_preemption_signal.py,
    unified-trading-library/unified_trading_library/io/streaming_writer.py,
    unified-trading-library/unified_trading_library/manifest_writer/_vm_progress.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/instruments_preflight_dag.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/circuit_breaker/_enums.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/dependency/health_policy.py,
    deployment-service/deployment_service/data_pipeline_monitors/escalation.py,
    deployment-service/scripts/recovery/relaunch_backfill_vm.py,
  ]
supersedes:
superseded_by:
depends_on:
source:
---

# Alert-driven dependency revocation

> **Operator decisions (2026-08-12, recorded before authoring).** (1) Enforcement point: **both** — the DAG owns policy,
> the actuator executes, VM polling lands incrementally as a fail-closed backstop. (2) `DEPS_KILL` semantics:
> **drain-at-checkpoint only, never terminate.** Both were chosen over the alternatives explicitly; do not re-litigate
> them on a later pass without the operator.

## Why this exists

An alert firing changes nothing downstream today. The measured cases:

- `CONSOLIDATOR_DOWN` restarts the consolidator and takes **no dependent action** — VMs keep downloading into a manifest
  that is not updating, then re-download because it still has not updated.
- Two VMs can hold the same shard range simultaneously with no cross-VM interlock.
- `DP_VM_GONE_NO_CAPTURE` means downstream is about to read data that does not exist, and nothing stops it.

The primitives already exist and are NOT to be reinvented: `ErrorAction` (RETRY/RECONNECT/SKIP/FAIL), `BreakerAction` ×
`BreakerRecoveryMode` + `BREAKER_RECOVERY_DEFAULTS` (the agent-vs-human matrix), `DependencyClass` with
`expected_recovery_time_seconds` / `hard_escalation_seconds` (the time-based escalation ladder),
`VENUE_HEARTBEAT_THRESHOLDS` (the per-`(venue, data_type)` tuning precedent), and `instruments_preflight_dag` (the
upstream→downstream graph). What is missing is revocation, a retry budget registry, and a fleet-wide flush contract.

**Architectural constraint that shapes everything below**: `autonomous-recovery-matrix.md` states "Live-mode only. All
recovery mechanisms are disabled in batch/backtest." Live and batch are two disjoint recovery systems today. This plan
bridges them; it does not extend one over the other.

## Codex SSOTs

`/codex/05-infrastructure/data-pipeline-alerts.md` (failure-mode registry + emit→route→escalate),
`/codex/04-architecture/autonomous-recovery-matrix.md` (ErrorAction decision tree, agent-vs-human scope),
`/codex/05-infrastructure/spot-vms-for-backfill.md` (PROGRESS-resume contract),
`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` (nothing here deletes; cited so that stays true).

---

## Phase 0 — Preconditions and measurement (nothing is armed until these land)

- [ ] [SCRIPT] P0. Measure p95 and max shard duration per launcher family from `vm-logs/` run.log PROGRESS markers —
      this is the drain-budget denominator, since worst-case waste is longest-shard-duration × dependent-count. Repo:
      deployment-service.
- [ ] [SCRIPT] P0. Enumerate every VM prefix in `LAUNCHER_FOR_VM_PREFIX` and classify each as drain-capable (emits
      PROGRESS via `record_captured`) vs drain-blind (no checkpoint) — a drain-blind prefix can only ever receive
      DEPS_HOLD. Repo: deployment-service.
- [ ] [DATA] P0. Confirm from the classification above how many of the ~189 prefixes are drain-blind; if the count is
      material, add a todo here to close the gap rather than silently degrading those edges to HOLD forever.
- [ ] [SCRIPT] P1. Inventory every buffered writer in the fleet that can hold un-flushed rows — grep for
      `StreamingParquetWriter`, `StreamingShardFinalizer`, and any local accumulation before a GCS write. This is Phase
      1's registration list. Repo: unified-trading-library.

## Phase 1 — The graceful-flush contract (HARD PREREQUISITE — no DEPS_DRAIN edge is armed before this)

> Drain-only is safe **only** if a drained unit writes out the shards it is holding. Today exactly one buffer does:
> `manifest_writer/_preemption_signal.py` hooks SIGTERM+SIGINT, drains the per-VM shard debounce buffer, and chains the
> previous handler (shipped 2026-08-10 after preempted `mdps-cefi-2019-*` VMs logged thousands of real aggregations with
> nothing in the manifest). `StreamingParquetWriter` flushes only via `close()` / `__exit__` / atexit — and SIGTERM does
> not unwind a `with` block while atexit does not run on SIGKILL, which is the reasoning already written into
> `_preemption_signal`'s own docstring. The fix is to generalise that module, not to invent a new mechanism.

- [x] 1. ✅ [CODE] P0. Add a UTL drain registry — a process-wide registry of drainable buffers with a deterministic
      drain order, lifted from `manifest_writer/_preemption_signal.py` so the signal-chaining and re-entrancy behaviour
      is inherited rather than re-derived. Repo: unified-trading-library. — unified-trading-library@d50ca9ff65
      (`lifecycle/drain_registry.py`; QG green, canary-proven that the 7048-test unit suite executes it)
- [x] 2. ✅ [CODE] P0. Register `StreamingParquetWriter` with the drain registry on construction and deregister on
      `close()`, so a SIGTERM mid-shard flushes and uploads the partial parquet instead of discarding the buffer. Repo:
      unified-trading-library. — unified-trading-library@d50ca9ff65 (registers at construction, not first write, so a
      writer dying before its first flush is covered; deregisters in BOTH `close()` and `finalize_local()`)
- [x] 6. ✅ [CODE] P0. Register `StreamingShardFinalizer`'s writer pool with the drain registry — its per-shard writers
      are the same exposure with a wider blast radius (one row-group can span many shard keys). Repo:
      unified-trading-library. — **PLAN ASSUMPTION WAS WRONG; no pool code needed.** The pool is built out of
      `StreamingParquetWriter` instances (`streaming_shard_finalizer.py` constructs them in `_route_row_groups`), and
      those self-register at construction as of d50ca9ff65 — so every pooled shard writer is drainable already.
      Registering the pool as well would be a redundant second layer and a double-drain risk. Closed with the proving
      test instead: unified-trading-library@3378696710 (`test_streaming_parquet_writer_self_registers_and_deregisters`,
      `test_empty_writer_drain_is_a_noop`)
- [ ] [CODE] P0. Migrate `_preemption_signal` to install its handler THROUGH the drain registry rather than owning its
      own, so exactly one SIGTERM handler exists per process and the manifest buffer keeps its current guaranteed-drain
      semantics. Repo: unified-trading-library.
- [x] 3. ✅ [CODE] P0. A partial shard flushed by drain MUST NOT be recorded `captured` — record the rows written and
      leave the shard's capture_status unchanged so the resume re-attempts it. A drain that marks a partial shard
      complete is fabrication-by-construction. Repo: unified-trading-library. — unified-trading-library@d50ca9ff65
      (`drain_for_shutdown()` writes bytes only; touches neither `record_captured` nor the PROGRESS frontier)
- [x] 4. ✅ [TEST] P0. Test: SIGTERM mid-write flushes every registered buffer, in registry order, and the parquet is
      readable — the regression guard for the whole plan. Repo: unified-trading-library. —
      unified-trading-library@d50ca9ff65 (`test_data_writers_drain_before_manifest`,
      `test_drain_order_is_deterministic_within_a_priority`, `test_manifest_priority_is_last_in_the_enum`)
- [ ] [TEST] P0. Test: a drain-flushed partial shard does not advance the PROGRESS frontier and does not set `captured`,
      so `--force` resume re-attempts it. Repo: unified-trading-library. NOT covered by the shipped tests — those use
      fake buffers; this one needs a real ManifestWriter+PROGRESS integration test.
- [x] 5. ✅ [TEST] P0. Test: the drain registry chains a pre-existing SIGTERM handler instead of clobbering it,
      mirroring `_preemption_signal`'s existing contract. Repo: unified-trading-library. —
      unified-trading-library@d50ca9ff65 (`test_signal_handler_chains_instead_of_clobbering`,
      `test_signal_handler_never_raises_even_when_a_buffer_explodes`)
- [ ] [CODE] P1. Wire the drain registry into the backfill entrypoints that currently install no SIGTERM handler at all
      — MTDS, MDPS, instruments-service and features-service backfill CLIs. A fleet grep for `signal.SIGTERM` finds
      handlers in long-running services but not in these. Repos: market-tick-data-service,
      market-data-processing-service, instruments-service, features-service.
- [ ] [DOC] P1. Document the flush contract in `/codex/05-infrastructure/spot-vms-for-backfill.md` — what "exit
      gracefully" obliges a script to do, and that registering a buffer is mandatory for any new writer.

## Phase 2 — The policy evaluator (one SSOT, no forked policy)

- [ ] [CODE] P0. Add `DependentAction` to UAC as a closed StrEnum — NONE / SELF_RETRY / SELF_RESTART / SELF_DRAIN /
      DEPS_HOLD / DEPS_DRAIN / FLEET_HALT / KILL_SWITCH. Deliberately 8 values: `DEPS_KILL` is absent by operator
      decision. Repo: unified-api-contracts.
- [ ] [CODE] P0. Add `evaluate_revocation()` to `instruments_preflight_dag` returning a `DependentAction` for a
      (alert_code, affected_entity) pair — the single policy SSOT both delivery paths consult. Repo:
      unified-api-contracts.
- [ ] [CODE] P0. Build the alert→action map keyed on `AlertCode` and DP registry_id identity, never on severity tier —
      four routing bugs found 2026-08-12 had a correct code at the wrong tier. Repo: unified-api-contracts.
- [ ] [CODE] P0. Resolve the dependent set for an alert from the existing preflight graph rather than a new adjacency
      table — the graph is already the SSOT for upstream-required-before-downstream. Repo: unified-api-contracts.
- [ ] [TEST] P0. Test: every DP registry_id and every `AlertCode` resolves to exactly one `DependentAction` — the
      closed-set guard, mirroring `test_every_alert_code_has_a_specific_rule` shipped at
      unified-api-contracts@76e144d5ca. Repo: unified-api-contracts.
- [ ] [TEST] P0. Test: `evaluate_revocation` never returns a stronger action than DEPS_DRAIN for any input — the machine
      guard that drain-only cannot silently become terminate. Repo: unified-api-contracts.
- [ ] [TEST] P0. Test: a drain-blind VM prefix (from Phase 0) resolves to DEPS_HOLD, never DEPS_DRAIN. Repo:
      unified-api-contracts.

## Phase 3 — The retry budget registry (does not exist today)

> A fleet grep for `max_retries` / `RETRY_BUDGET` / `max_attempts` finds nothing in UAC or `deployment_service`. "Three
> attempts" is prose in `autonomous-recovery-matrix.md`, not a value anything reads.

- [ ] [CODE] P0. Add `RetryBudget` to UAC — `max_attempts`, `backoff_base_seconds`, `backoff_multiplier`,
      `max_backoff_seconds`, `give_up_action: DependentAction`. Repo: unified-api-contracts.
- [ ] [CODE] P0. Add `RETRY_BUDGETS` keyed `(data_type, source)` plus `DEFAULT_RETRY_BUDGET_BY_ERROR_ACTION`, resolving
      exact → `(data_type, "*")` → `ErrorAction` default. Mirrors how `VENUE_HEARTBEAT_THRESHOLDS` is already keyed.
      Repo: unified-api-contracts.
- [ ] [CODE] P0. Seed the defaults from the values already documented in `autonomous-recovery-matrix.md` — 3 attempts,
      300→600→1200→3600s ladder — so the registry starts as a faithful transcription, not a redesign. Repo:
      unified-api-contracts.
- [ ] [CODE] P0. Set `max_attempts=0` for `MISSING_CREDENTIAL` so "never retry a missing key" is structural rather than
      a convention someone can forget. Repo: unified-api-contracts.
- [ ] [CODE] P0. Set Tardis `max_attempts=1` — it is already hard-capped at one concurrent VM per cloud and retries
      storm the API. Repo: unified-api-contracts.
- [ ] [CODE] P1. Set Databento budgets to fail closed on billing errors, consistent with the 3-datasets
      billing-fail-closed rule. Repo: unified-api-contracts.
- [ ] [TEST] P0. Test: resolution order falls back correctly through all three levels and every `ErrorAction` has a
      default. Repo: unified-api-contracts.
- [ ] [CODE] P1. Replace the hardcoded retry counts in the adapter retry paths with `RETRY_BUDGETS` lookups so the
      registry is actually load-bearing, not decorative. Repos: instruments-service, market-tick-data-service.

## Phase 4 — The push actuator (ships without touching a single launcher)

- [ ] [CODE] P0. Add a revocation actuator in `data_pipeline_monitors` that consults `evaluate_revocation()` and
      delivers the verdict — it must carry NO policy branch of its own. Repo: deployment-service.
- [ ] [CODE] P0. Deliver DEPS_DRAIN by writing a per-VM drain marker to the VM's `vm-logs/` prefix, not by terminating
      the instance — the VM-side hook in Phase 5 observes the marker. Repo: deployment-service.
- [ ] [CODE] P0. Deliver DEPS_HOLD by writing an admission-block marker the launcher preflight reads, so a held
      dependent never starts. Repo: deployment-service.
- [ ] [CODE] P0. Deliver FLEET_HALT by pausing the relevant Cloud Scheduler jobs, reusing the existing scheduler-pause
      path rather than a new mechanism — and emit `DP_CONSOLIDATOR_SCHEDULER_PAUSED`-style visibility so a halt is never
      silent. Repo: deployment-service.
- [ ] [CODE] P0. Budget-bound every actuation per (alert_code, target, day) using the GCS-durable state pattern from
      `relaunch_backfill_vm.py` — the tempdir-backed budget was discarded every 5 minutes on Cloud Run and the
      documented cap never engaged. Repo: deployment-service.
- [ ] [CODE] P0. Emit a resolved-bookend when a hold or drain is released, so a revocation that opened is visibly closed
      in-channel per the alerting close-bookend rule. Repo: deployment-service.
- [ ] [TEST] P0. Test: the actuator's verdict for every alert equals `evaluate_revocation()`'s — the anti-drift guard
      proving there is no second policy. Repo: deployment-service.
- [ ] [TEST] P0. Test: the actuator degrades to file_issue rather than crashing when its own dependencies are
      unavailable, matching `_ACTUATORS_AVAILABLE`'s existing capability-probe contract. Repo: deployment-service.
- [ ] [TEST] P0. Test: actuation budget survives a fresh container — the exact regression that made
      `_MAX_RELAUNCHES_PER_DAY` a no-op. Repo: deployment-service.

## Phase 5 — VM-side poll hook and Cloud Run skip gate (the fail-closed backstop)

- [ ] [CODE] P0. Add a drain-marker poll to the VM tee-wrapper's heartbeat so a running VM observes DEPS_DRAIN and exits
      at its next checkpoint. Repo: deployment-service.
- [ ] [CODE] P0. Make the drain path call the Phase-1 drain registry before exiting, so observing the marker actually
      flushes rather than merely stopping. Repo: deployment-service.
- [ ] [CODE] P0. Add an admission check to the launcher preflight so a DEPS_HOLD marker prevents launch, and the refusal
      is logged with the alert that caused it. Repo: deployment-service.
- [ ] [CODE] P0. Add the same admission check to the Cloud Run job entrypoints so a job in a bad-state window skips its
      run instead of executing against known-bad inputs. Repo: deployment-api.
- [ ] [CODE] P1. Roll the poll hook across the drain-capable launcher prefixes from Phase 0, structurally rather than
      per-file where the launchers share a common wrapper. Repo: deployment-service.
- [ ] [TEST] P0. Test: a VM with the poll hook drains within one checkpoint interval of the marker appearing. Repo:
      deployment-service.
- [ ] [TEST] P0. Test: a Cloud Run job skips cleanly and reports skipped-not-failed when the admission check blocks it.
      Repo: deployment-api.

## Phase 6 — Bad-VM test matrix (prove it on the failure modes that motivated it)

> Every scenario is exercised against `-test-` buckets, never prod. Each asserts three things: the alert fires, the
> right dependency action is taken, and no in-flight shard is lost.

- [ ] [TEST] P0. Scenario OOM — force a 137 exit mid-shard; assert DP-VM-001 fires, self restarts resize-up, dependents
      HOLD, and the drain registry flushed before death. Repo: e2e-testing.
- [ ] [TEST] P0. Scenario stall — wedge the process past the heartbeat budget; assert DP-VM-003 fires, the stall-kill
      path (not the drain path) handles it, and dependents HOLD. Repo: e2e-testing.
- [ ] [TEST] P0. Scenario preemption — SIGTERM with the SPOT grace window; assert the drain registry flushes, PROGRESS
      does not advance past the flushed shard, and relaunch resumes from PROGRESS rather than START_DATE. Repo:
      e2e-testing.
- [ ] [TEST] P0. Scenario gone-no-capture — drain a VM whose captured count never climbed; assert DP-VM-002 fires and
      dependents DRAIN rather than proceeding on absent data. Repo: e2e-testing.
- [ ] [TEST] P0. Scenario consolidator-down — stop the consolidator; assert MANIFEST-001 fires and every
      manifest-writing dependent drains, the headline money-burn case. Repo: e2e-testing.
- [ ] [TEST] P0. Scenario mostly-empty — drive a run past the empty ratio threshold; assert it drains AT the threshold
      crossing rather than at run end. Repo: e2e-testing.
- [ ] [TEST] P0. Scenario wrong-path — force a non-canonical write; assert the write is blocked, the VM drains, and
      dependents drain. Repo: e2e-testing.
- [ ] [TEST] P0. Scenario catalogue-stale — age the catalogue past 24h; assert DP-CATALOG-001 fires and that asset
      group's capture VMs drain. Repo: e2e-testing.
- [ ] [TEST] P0. Scenario deadman — stale a monitor sentinel; assert FLEET_HALT blocks new launches and that
      already-running VMs are NOT drained (fail-closed on admission, not on running work). Repo: e2e-testing.
- [ ] [TEST] P0. Scenario drain-blind prefix — assert a prefix with no checkpoint receives HOLD and is never sent a
      drain marker it cannot honour. Repo: e2e-testing.
- [ ] [TEST] P1. Scenario double-booking — two VMs on the same shard range; assert the interlock prevents the second
      from starting. Repo: e2e-testing.
- [ ] [TEST] P1. Scenario recovery — assert every scenario above emits its resolved-bookend and releases holds once the
      upstream alert clears. Repo: e2e-testing.

## Phase 7 — Codex SSOT and close-out

- [ ] [DOC] P0. Add a revocation section to `/codex/05-infrastructure/data-pipeline-alerts.md` — the action vocabulary,
      the drain-only ruling and its rationale, and the alert→action table. It references the code, it does not duplicate
      the map.
- [ ] [DOC] P0. Update `/codex/04-architecture/autonomous-recovery-matrix.md` to state that batch/backfill now has a
      revocation path, correcting its current "Live-mode only. All recovery mechanisms are disabled in batch/backtest."
- [ ] [DOC] P0. Record the retry registry as the SSOT for retry counts in the recovery matrix, replacing the prose "3
      attempts" with a pointer to `RETRY_BUDGETS`.
- [ ] [DOC] P1. Add the flush contract to `/codex/06-coding-standards/` so every new buffered writer registers with the
      drain registry by convention, not by memory.
- [ ] [REVIEW] P0. Post-phase codex audit — verify no plan↔codex drift, every cited path resolves, and no doc still
      claims a gap this plan closed.
- [ ] [REVIEW] P0. Archive this plan once every todo is done and unlocked, per the archival discipline (dated archive
      folder, banner, referrer sweep).

---

## Progress Log

### 2026-08-12 — plan authored

Context that produced it: an audit of the three alert channels for the operator's question "which alerts should kill
which VMs". Findings shipped separately at **unified-api-contracts@76e144d5ca** before this plan was written:

- `RECON_DEGRADED` never matched its own rule (`RECON_DEGRADED_*` requires the underscore; the bare code fell to the
  catch-all and routed INFO/Telegram instead of HIGH/PagerDuty). Live production routing bug.
- `CHAOS_DRILL_FAILED` and `DAILY_LEDGER_DIGEST` had no rule at all — same catch-all fallthrough class as the documented
  2026-07-27 `DP_FLEET_MONITOR_*` and 2026-07-31 `DP_CONSOLIDATOR_SCHEDULER_PAUSED` incidents.
- Root cause of all three: `test_live_alert_rules_patterns_match_at_least_one_code` only checked rule→code. The reverse
  direction existed as per-family spot-checks that matched the catch-all and therefore passed vacuously, while
  `codes.py` claimed bidirectional enforcement. Fixed by `test_every_alert_code_has_a_specific_rule`.

Codex corrections shipped in the same pass: the DP-VM table in `data-pipeline-alerts.md` was drifted against
`registry.yaml` (md's 007/008 were the registry's 008/010; 007/009/011 missing), `DP-CATALOG-002` was registry-only, and
the actuator-packaging "OPEN GAP (P1)" was stale — closed at `deployment-api@a01e2a5b`, where the real story was worse
than documented: an earlier fix turned `_ACTUATORS_AVAILABLE` green while the relaunch actuators stayed dead, because
they exec `scripts/vm/launch-*.sh` at actuation time and only one file had been COPYed. Every relaunch hit a caught
`FileNotFoundError` and degraded to `file_issue` — silent for weeks. That is the failure mode this plan's anti-drift and
capability-probe tests exist to prevent repeating.

Operator decisions recorded at the top of this doc. Phase 1 is the hard prerequisite: drain-only is only safe once every
buffered writer flushes on signal, and today only the manifest debounce buffer does.

### 2026-08-12 — Phase 1 implementation (in flight, gate pending)

Written, not yet shipped (UTL `quality-gates.sh` running at time of writing — nothing below is claimed done until it is
green and the checkboxes are flipped):

- `unified_trading_library/lifecycle/drain_registry.py` — new. Weakref-held registry, `DrainPriority` IntEnum,
  `drain_all()` that never raises, and a SIGTERM/SIGINT handler that CHAINS the previous handler (pattern lifted from
  `manifest_writer/_preemption_signal.py` rather than re-derived, so the install-once / rollback / re-deliver semantics
  are inherited).
- `io/streaming_writer.py` — `StreamingParquetWriter` now installs the handler and registers itself at construction (not
  at first write, so a writer that dies before its first flush is still covered), implements `drain_for_shutdown()`, and
  deregisters in both `close()` and `finalize_local()`.
- `tests/unit/test_drain_registry.py` — 10 tests.

**Design decision worth not re-deriving: drain ORDER is a correctness property.** Data writers drain BEFORE manifest
buffers, because the manifest records what the data writers wrote — draining the manifest first can record rows as
`captured` that the writer then fails to upload, manufacturing the phantom-row class (DP-MANIFEST-003) out of the
mechanism meant to prevent data loss. `DrainPriority.MANIFEST` is deliberately the max value and
`test_manifest_priority_is_last_in_the_enum` is the machine guard on that.

**Environment note for the next tick**: this slot's `unified-trading-library` checkout has NO `.venv`, so targeted
`python -c` verification is not available there — go through `scripts/quality-gates.sh`, which owns env setup.

### 2026-08-12 — Phase 1 partially SHIPPED at `unified-trading-library@d50ca9ff65`

5 of 9 Phase-1 todos flipped. Still open: `StreamingShardFinalizer` pool registration, migrating `_preemption_signal` to
install THROUGH the registry, the backfill-entrypoint wiring, the codex flush-contract doc, and the PROGRESS-frontier
integration test (the shipped tests use fake buffers and do not cover it — called out inline on that todo rather than
flipped).

**Verification trap worth not repeating.** The gate suppresses unit-test output on success and separately echoes only
the PM integration session (`6 passed, 2 deselected`). Reading that log I twice concluded the unit suite was not running
and nearly filed a fabricated `base-library.sh` gate bug. It was wrong: a deliberately-failing canary test returned
`1 failed, 7048 passed`, proving the suite runs and executes `tests/unit/test_drain_registry.py`. **Silence in the gate
log is not evidence of non-execution** — if you need to know whether a test file runs, add a failing canary and read the
exit code, don't read the log. `QG_SLICE=tests` does NOT make unit output visible either.

**Green in 12s is the sentinel fast path**, not a full run — legitimate only when the tree is byte-identical to the last
full green (removing the canary restored exactly that state). Do not accept a 12s green after a real edit.

**Ship note**: quickmerge pre-flight refused (`unified-api-contracts: HAS UNCOMMITTED CHANGES`) because a LIVE peer
session holds uncommitted UAC work in this shared slot. Used `--skip-preflight` (documented as a multi-agent safety
check, explicitly NOT a quality gate) after confirming neither dirty UAC file is imported by this change —
`drain_registry` imports no UAC at all. `--dep-branch` is HUMAN-ONLY and was not used. The peer's files were never
touched.

**Slot state (unresolved, operator-gated)**: the shared slot-4 `unified-trading-pm` checkout is 1-ahead / 153-behind
`origin/live-defi-rollout`. The 1 ahead is an automated `chore(orphan-wip)` inherit commit. Four dirty files belong to a
LIVE peer session (`tradfi_databento_account_billing_suspended_2026_08_09.md`,
`tradfi_manifest_content_recovery_completion_2026_07_24.md`, an untracked
`cefi_tardis_pre_listing_filter_wrong_gcs_path_always_404s_2026_08_12.md`, and `slack-data-pipeline-alerts-2h.json`).
Per the liveness gate a live claim is PROTECT, so they were left untouched and every ship this session went through
`safe-doc-push`/`quickmerge`'s isolated worktree, which reconciles against origin and is unaffected by the local
divergence. Do NOT reconcile that checkout without the operator while the peer is live.
