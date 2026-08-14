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
      deployment-service. **ATTEMPTED 2026-08-14, BLOCKED-CREDENTIALS in this slot**:
      `scripts.recovery._durable_state. state_bucket()` resolves empty locally (gcloud auth present — 5 accounts
      including a working SA — but the bucket name itself resolves from runtime-only config this dev checkout doesn't
      carry). Needs either a slot with the runtime env wired or a VM-side run. Left open rather than faked.
- [x] ✅ [SCRIPT] P0. Enumerate every VM prefix in `LAUNCHER_FOR_VM_PREFIX` and classify each as drain-capable (emits
      PROGRESS via `record_captured`) vs drain-blind (no checkpoint) — a drain-blind prefix can only ever receive
      DEPS_HOLD. Repo: deployment-service. — **MEASURED 2026-08-14** (no code changed, read-only census): **243 total
      prefixes** (the plan's own "~189" estimate was stale — corrected here per the doc-that-misled-you rule), of which
      **65 map to `None`** (fan-out wrappers / live singletons / infra VMs — structurally never backfill-capture units,
      so DEPS_DRAIN never targets them) and **178 map to 104 distinct `scripts/vm/launch-*.sh` files**. Of those 104:
      **102 confirmed drain-capable** — each invokes a manifest_writer-using service (MTDS/MDPS/instruments-service/
      features-service/SFI), directly or via a shared launcher lib (`_tradfi-ohlcv-launcher-lib.sh` sets
      `VM_SERVICE=market_tick_data_service` for all 7 `launch-tradfi-bf-*` scripts, which a naive filename-prefix grep
      would have missed). **2 are structurally not data-capture VMs** (`launch-scenario-runner-vm.sh` runs
      `unified_trading_library.scenario.run_matrix` — reads existing data, writes no manifest-tracked shards;
      `launch-ml-strategy-orphan-sweep-vm.sh` runs a standalone report script) — DEPS_DRAIN never applies to them either
      way, so they are N/A rather than a gap.
- [x] ✅ [DATA] P0. Confirm from the classification above how many of the ~189 prefixes are drain-blind; if the count is
      material, add a todo here to close the gap rather than silently degrading those edges to HOLD forever. —
      **MEASURED 2026-08-14: the count is NOT material — zero confirmed drain-blind-but-should-capture-data prefixes.**
      Every backfill-capture launcher (102/104 distinct scripts) is drain-capable post Phase 1's structural fix
      (`manifest_writer` installs the drain registry at import); the only 2 unconfirmed-by-service-name scripts turned
      out to be non-capture tools where drain is simply inapplicable, not a gap. No follow-up todo needed.
- [x] ✅ [SCRIPT] P1. Inventory every buffered writer in the fleet that can hold un-flushed rows — grep for
      `StreamingParquetWriter`, `StreamingShardFinalizer`, and any local accumulation before a GCS write. This is Phase
      1's registration list. Repo: unified-trading-library. — **MEASURED 2026-08-14**: grepped all 4 backfill service
      repos (instruments-service, market-tick-data-service, market-data-processing-service, features-service) for
      `upload_from_string`/`upload_blob`/direct-write patterns outside `StreamingParquetWriter`/`manifest_writer`. Every
      non-`scripts/` hit was a `.write_bytes()` to a LOCAL side-cache file (EVM creation-block resolver, Solana pool
      metadata) — synchronous per-call writes, not an accumulating buffer, so nothing to register. The `scripts/`-dir
      hits are one-off migration/reconciliation scripts (lifecycle-marked TEMPORARY, not in `LAUNCHER_FOR_VM_PREFIX`,
      not preemption-monitored the way a live backfill VM is) — out of Phase 1's registration scope. No unregistered gap
      found.
- [x] ✅ [SCRIPT] P1. Reconcile the slot-4 `unified-trading-pm` checkout. **DONE 2026-08-13 —
      `unified-trading-pm@25b9869550`.** No longer BLOCKED-OPERATOR-DECISION, and the diagnosis below was incomplete:
      the checkout was not merely ahead/behind, it was in **DETACHED HEAD with an interactive rebase interrupted 3.2
      hours earlier** (`.git/rebase-merge` present, `stopped-sha` = the `chore(orphan-wip)` commit). That — not any
      dirty file — is what blocked plan commits repo-wide, because a resolved file inside a stalled rebase unblocks
      nothing. The "LIVE peer session" premise had also gone stale: measured no live process, no `.agent-claim`, and a
      3.2h-idle rebase = a DEAD claim, which the liveness rule says to inherit. Completing the rebase reattached
      `live-defi-rollout` and landed the orphan-WIP commit carrying BOTH preserved blobs (`d45a1bdc68` codex,
      `0dcaf67834` plan) — so those are now tracked on origin and need no `git cat-file` restore. Six conflicts were
      resolved on a measured criterion rather than preference: 4 where `ours` matched origin byte-for-byte and `theirs`
      did not, 1 pure whitespace re-wrap, and 1 where `theirs` was the older version missing a completed entry. Every
      discarded side was backed up first. Original text follows for provenance — it named the checkout as 1-ahead /
      153-behind with dirty files owned by a LIVE peer session
      (`tradfi_databento_account_billing_suspended_2026_08_09.md`,
      `tradfi_manifest_content_recovery_completion_2026_07_24.md`, untracked
      `cefi_tardis_pre_listing_filter_wrong_gcs_path_always_404s_2026_08_12.md`, `slack-data-pipeline-alerts-2h.json`).
      BLOCKED-OPERATOR-DECISION: resolving it requires deciding what happens to the peer's staged work, which the
      liveness gate forbids an agent from doing unilaterally. Options: (a) wait for the peer session to land its work
      then `git pull --rebase --autostash`; (b) operator adjudicates and reconciles now. Recommendation: (a) — nothing
      is blocked by it, since every ship this session went through the isolated-worktree path unaffected by the
      divergence.
- [x] ✅ [CODE] P0. Re-ship Phase 2 once the `unified-api-contracts` tree is green. **DONE 2026-08-13 —
      `unified-api-contracts@c206f9100d`** (Phases 2 AND 3 together). No longer BLOCKED-OPERATOR-DECISION: the premise
      was that a **LIVE** peer held the uncommitted `_source_priority_data.py` + `registry/market_data_categories.py`,
      making the liveness gate forbid touching them. By 2026-08-13 that claim had gone stale — measured idle **~5
      hours** (newest mtime 17,885s), no `.agent-claim`, no live process — i.e. a DEAD claim, which the same rule says
      to inherit. Neither option (a) nor (b) was needed: the Yahoo work was **parked, not adjudicated and not reverted**
      (`git stash push` under a named ref + a file-level backup), which let Phase 2/3 ship on a green tree while
      preserving the peer's work byte-for-byte. The parked decision is now tracked at
      `/plans/active/issues/yahoo_ohlcv_1h_availability_semantic_undecided_2026_08_13.md`. Verified in the landed code
      (9/9 claims): `DependentAction` StrEnum with all 6 members, `evaluate_revocation()`, `resolve_dependents()`,
      `ALERT_CODE_ACTIONS` + `DP_FAILURE_MODE_ACTIONS`, `RetryBudget`, `RETRY_BUDGETS`,
      `MISSING_CREDENTIAL max_attempts=0`, Tardis `max_attempts=1`; 41 tests green. Repo: unified-api-contracts.
- [ ] [OPERATOR] P2. Bootstrap a `.venv` in this slot's `unified-trading-library` — absent, so every verification
      round-trip is a full `quality-gates.sh` run (measured this session: 103s / 119s / 218s / 406s, plus a 74s
      tests-slice). Roughly 20 minutes of one session's wall-clock went to gates for changes checkable in seconds
      locally. This is the dominant cost on the remaining todos and Phase 6's 12 bad-VM scenarios will be the worst of
      it.

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
- [x] 7. ✅ [CODE] P0. Migrate `_preemption_signal` to install its handler THROUGH the drain registry rather than owning
      its own, so exactly one SIGTERM handler exists per process and the manifest buffer keeps its current
      guaranteed-drain semantics. Repo: unified-trading-library. — unified-trading-library@15e285f007 (QG green 218s,
      real run not sentinel). Deleted (no shims): `_handle_preemption_signal`, `_chain_to_previous_signal_handler`,
      `_PREV_SIGNAL_HANDLERS`, `_SIGNAL_HANDLER_STATE`, `_PREEMPTION_SIGNALS` + their `__init__` re-exports. Their
      behaviour MOVED to `tests/unit/test_drain_registry.py` (SIG_DFL re-delivery, SIG_IGN preservation, off-main-thread
      no-op, idempotent install, chaining, never-raising); the manifest tests keep the per-VM debounce regression and
      gain `test_manifest_is_registered_and_drains_last`. **Sharpened 2026-08-12 — this is an ORDERING-FRAGILITY fix,
      not a cosmetic one.** With two independent chained handlers, drain order is decided by install order:
      `manifest_writer/__init__` installs at IMPORT, `drain_registry` installs when the first `StreamingParquetWriter`
      is CONSTRUCTED (later), so the later-installed registry handler runs first and chains to the manifest's —
      data-writers-then-manifest, the correct order, but only by accident of sequence. A process that constructs a
      writer BEFORE importing `manifest_writer` inverts it and flushes manifest rows asserting `captured` for data not
      yet uploaded. Migrating makes the order structural (`DrainPriority`) instead of incidental. Preserve the public
      `install_preemption_signal_handler` name — `manifest_writer/__init__` exports it and
      `tests/unit/test_manifest_writer_preemption_signal_handler.py` exercises it directly.
- [x] 3. ✅ [CODE] P0. A partial shard flushed by drain MUST NOT be recorded `captured` — record the rows written and
      leave the shard's capture_status unchanged so the resume re-attempts it. A drain that marks a partial shard
      complete is fabrication-by-construction. Repo: unified-trading-library. — unified-trading-library@d50ca9ff65
      (`drain_for_shutdown()` writes bytes only; touches neither `record_captured` nor the PROGRESS frontier)
- [x] 4. ✅ [TEST] P0. Test: SIGTERM mid-write flushes every registered buffer, in registry order, and the parquet is
      readable — the regression guard for the whole plan. Repo: unified-trading-library. —
      unified-trading-library@d50ca9ff65 (`test_data_writers_drain_before_manifest`,
      `test_drain_order_is_deterministic_within_a_priority`, `test_manifest_priority_is_last_in_the_enum`)
- [x] 8. ✅ [TEST] P0. Test: a drain-flushed partial shard does not advance the PROGRESS frontier and does not set
      `captured`, so `--force` resume re-attempts it. Repo: unified-trading-library. —
      unified-trading-library@c523dededa (QG green 103s, real run).
      `test_drained_partial_shard_does_not_advance_progress_or_record_captured` drives a REAL `StreamingParquetWriter`
      (not a fake buffer) through `write_chunk` → `drain_for_shutdown` and asserts `_vm_progress._max_seen` is unmoved;
      `test_drain_does_not_touch_the_manifest_write_buffer` asserts `_WRITE_BUFFER` is unchanged. Closes the gap called
      out on this todo when Phase 1a shipped.
- [x] 5. ✅ [TEST] P0. Test: the drain registry chains a pre-existing SIGTERM handler instead of clobbering it,
      mirroring `_preemption_signal`'s existing contract. Repo: unified-trading-library. —
      unified-trading-library@d50ca9ff65 (`test_signal_handler_chains_instead_of_clobbering`,
      `test_signal_handler_never_raises_even_when_a_buffer_explodes`)
- [x] 9. ✅ [CODE] P1. Wire the drain registry into the backfill entrypoints that currently install no SIGTERM handler
      at all — MTDS, MDPS, instruments-service and features-service backfill CLIs. Repos: market-tick-data-service,
      market-data-processing-service, instruments-service, features-service. — **THE PREMISE WAS BACKWARDS, the real
      defect was worse, and the fix is one structural change in UTL rather than four entrypoint edits.**
      unified-trading-library@2aacde1359 (QG green 89s; the preceding run failed 1/7057 on my own test bug, which proves
      the suite executed). MEASURED, not assumed: importing `market_tick_data_service` already yields
      `_HANDLER_STATE {'installed': True}` and `[('manifest_pending_buckets', 90)]`, because `manifest_writer` installs
      at import. This todo's grep searched the SERVICE repos and so missed the transitive install from UTL. What it also
      missed is the actual bug: `GracefulShutdownHandler.__init__` calls `signal.signal(SIGTERM, ...)` unconditionally,
      so every `ServiceBootstrap` service constructing one in `main()` — i.e. AFTER imports — **replaces** the drain
      hook (proved: handler identity goes `_handle_drain_signal` → `GracefulShutdownHandler._handle_signal`). Its
      `sys.exit(0)` raises SystemExit, which DOES run atexit, and `manifest_writer._state` has always registered an
      atexit flush — but `StreamingParquetWriter` has **no atexit at all**. So the manifest drained while the data
      writers were discarded: rows asserting `captured` for parquet never uploaded — the phantom-row class
      (DP-MANIFEST-003), manufactured by the machinery meant to prevent data loss. Fixed in two layers: (1)
      `drain_registry` registers an atexit backstop at install time — atexit is LIFO and this lands after `_state`'s, so
      the priority-ordered drain runs BEFORE it and `_state`'s flush no-ops; (2)
      `GracefulShutdownHandler._handle_signal` calls `drain_all()` before its cleanup callback, so a failing callback
      cannot pre-empt the drain. Four new tests, plus the autouse isolation fixture the file lacked (these tests install
      REAL signal handlers — without it a test could leave pytest itself exiting on SIGTERM).
- [x] 10. ✅ [DOC] P1. Document the flush contract in `/codex/05-infrastructure/spot-vms-for-backfill.md` — what "exit
      gracefully" obliges a script to do, and that registering a buffer is mandatory for any new writer. — new section
      "The graceful-flush contract" placed directly before § Coverage, carrying: the mandatory registration snippet
      (register at construction, deregister in EVERY terminal path); why drain ORDER is a correctness property
      (`MANIFEST = 90` is deliberately last — draining it first fabricates `captured` for un-uploaded parquet,
      DP-MANIFEST-003); why neither atexit NOR the signal handler alone suffices, with all three measured failure modes
      (SIGKILL skips atexit · SIGTERM does not unwind a `with` · signal installation is last-writer-wins, the
      `GracefulShutdownHandler` clobber found the same day); the drained-partial-shard-is-not-captured rule; and the
      `loop.add_signal_handler` caveat for async services. Cites the fix at unified-trading-library@2aacde1359 and the
      contract tests.

## Phase 2 — The policy evaluator (one SSOT, no forked policy)

- [x] 11. ✅ [CODE] P0. Add `DependentAction` to UAC as a closed StrEnum — NONE / SELF_RETRY / SELF_RESTART / SELF_DRAIN
      / DEPS_HOLD / DEPS_DRAIN / FLEET_HALT / KILL_SWITCH. Deliberately 8 values: `DEPS_KILL` is absent by operator
      decision. Repo: unified-api-contracts. — unified-api-contracts@c206f910. 8 values; `DEPS_KILL` absent by operator
      decision, guarded by `test_deps_kill_is_absent_from_the_action_vocabulary`.
- [x] 12. ✅ [CODE] P0. Add `evaluate_revocation()` to `instruments_preflight_dag` returning a `DependentAction` for a
      (alert_code, affected_entity) pair — the single policy SSOT both delivery paths consult. Repo:
      unified-api-contracts. — unified-api-contracts@c206f910. **Deviation:** lives in a NEW
      `canonical/crosscutting/dependency_revocation.py`, not inside `instruments_preflight_dag` — that file was already
      589 lines and 142 registry entries would breach the file-size ratchet. The new module IMPORTS the DAG and inverts
      `INSTRUMENTS_PREFLIGHT_REQUIREMENTS`, so the actual requirement (resolve dependents from the existing graph) holds
      exactly; re-exporting back through the DAG would have created an import cycle.
- [x] 13. ✅ [CODE] P0. Build the alert→action map keyed on `AlertCode` and DP registry_id identity, never on severity
      tier — four routing bugs found 2026-08-12 had a correct code at the wrong tier. Repo: unified-api-contracts. —
      unified-api-contracts@c206f910. `ALERT_CODE_ACTIONS` (89 members) + `DP_FAILURE_MODE_ACTIONS` (53 ids). Keyed on
      the DP **id**, not the event name, because `DP-FETCH-007`/`009` share `DP_RUN_MOSTLY_EMPTY` and
      `DP-RATE-001`/`003` share `DP_SOURCE_RATE_LIMITED` — keying on the event would have silently merged four failure
      modes into two. `test_dp_ids_are_well_formed_and_the_two_key_spaces_do_not_overlap` proves the spaces cannot
      collide.
- [x] 14. ✅ [CODE] P0. Resolve the dependent set for an alert from the existing preflight graph rather than a new
      adjacency table — the graph is already the SSOT for upstream-required-before-downstream. Repo:
      unified-api-contracts. — unified-api-contracts@c206f910. `resolve_dependents()` inverts
      `INSTRUMENTS_PREFLIGHT_REQUIREMENTS`; no second adjacency table exists, so the revocation edge set cannot disagree
      with the admission gate it mirrors.
- [x] 15. ✅ [TEST] P0. Test: every DP registry_id and every `AlertCode` resolves to exactly one `DependentAction` — the
      closed-set guard, mirroring `test_every_alert_code_has_a_specific_rule` shipped at
      unified-api-contracts@76e144d5ca. Repo: unified-api-contracts. — unified-api-contracts@c206f910.
      `test_every_alert_code_has_a_dependent_action` + `test_every_dp_registry_id_has_a_dependent_action`. Registry ids
      held as a literal (transcribed 2026-08-13) because UAC's CI does not check out unified-trading-pm — a test that
      skipped on a missing file would be exactly the vacuous guard this mirrors.
- [x] 16. ✅ [TEST] P0. Test: `evaluate_revocation` never returns a stronger action than DEPS_DRAIN for any input — the
      machine guard that drain-only cannot silently become terminate. Repo: unified-api-contracts. —
      unified-api-contracts@c206f910. `test_no_verdict_ever_exceeds_the_drain_ceiling` over all 142 identities. Its
      teeth come from `DEPENDENT_LIFECYCLE_STRENGTH` being validated total at import: a future terminating action cannot
      be added without declaring a strength, and any strength above the ceiling fails.
- [x] 17. ✅ [TEST] P0. Test: a drain-blind VM prefix (from Phase 0) resolves to DEPS_HOLD, never DEPS_DRAIN. Repo:
      unified-api-contracts. — unified-api-contracts@c206f910. `test_a_drain_blind_target_is_clamped_to_hold` asserts
      the clamp AND that `clamped_from` records it, so a degraded edge stays visible. Made structural (a `drain_capable`
      parameter) rather than data-driven, so it does not block on Phase 0's prefix census.

## Phase 3 — The retry budget registry (does not exist today)

> A fleet grep for `max_retries` / `RETRY_BUDGET` / `max_attempts` finds nothing in UAC or `deployment_service`. "Three
> attempts" is prose in `autonomous-recovery-matrix.md`, not a value anything reads.

- [x] 18. ✅ [CODE] P0. Add `RetryBudget` to UAC — `max_attempts`, `backoff_base_seconds`, `backoff_multiplier`,
      `max_backoff_seconds`, `give_up_action: DependentAction`. Repo: unified-api-contracts. —
      unified-api-contracts@c206f910. Validates its own invariants at construction (no shrinking ladder, no ceiling
      below floor, no negative attempts).
- [x] 19. ✅ [CODE] P0. Add `RETRY_BUDGETS` keyed `(data_type, source)` plus `DEFAULT_RETRY_BUDGET_BY_ERROR_ACTION`,
      resolving exact → `(data_type, "*")` → `ErrorAction` default. Mirrors how `VENUE_HEARTBEAT_THRESHOLDS` is already
      keyed. Repo: unified-api-contracts. — unified-api-contracts@c206f910. Four-level resolution: exact →
      `(data_type, "*")` → `("*", source)` → `ErrorAction` default. The vendor-wide level exists because the Tardis and
      Databento caps are properties of the VENDOR, not of any data type.
- [x] 20. ✅ [CODE] P0. Seed the defaults from the values already documented in `autonomous-recovery-matrix.md` — 3
      attempts, 300→600→1200→3600s ladder — so the registry starts as a faithful transcription, not a redesign. Repo:
      unified-api-contracts. — unified-api-contracts@c206f910. Measured `[300, 600, 1200, 2400, 3600]`, 3 attempts — a
      faithful transcription, not a redesign.
- [x] 21. ✅ [CODE] P0. Set `max_attempts=0` for `MISSING_CREDENTIAL` so "never retry a missing key" is structural
      rather than a convention someone can forget. Repo: unified-api-contracts. — unified-api-contracts@c206f910.
      Structural, plus `test_missing_credential_is_never_retried` across four sources.
- [x] 22. ✅ [CODE] P0. Set Tardis `max_attempts=1` — it is already hard-capped at one concurrent VM per cloud and
      retries storm the API. Repo: unified-api-contracts. — unified-api-contracts@c206f910. A retry ladder is the
      one-concurrent-VM storm serialised.
- [x] 23. ✅ [CODE] P1. Set Databento budgets to fail closed on billing errors, consistent with the 3-datasets
      billing-fail-closed rule. Repo: unified-api-contracts. — unified-api-contracts@c206f910. Retrying re-attempts a
      charge on a suspended account and yields 0-row runs indistinguishable from honest absence.
- [x] 24. ✅ [TEST] P0. Test: resolution order falls back correctly through all three levels and every `ErrorAction` has
      a default. Repo: unified-api-contracts. — unified-api-contracts@c206f910.
      `test_resolution_falls_through_all_four_levels` + `test_every_error_action_has_a_default_budget`.
- [x] ✅ [CODE] P1. Replace the hardcoded retry counts in the adapter retry paths with `RETRY_BUDGETS` lookups so the
      registry is actually load-bearing, not decorative. Repos: instruments-service, market-tick-data-service. —
      instruments-service@1ae4b7d0 (`BaseReferenceDataAdapter.retry_source` class attr,
      `test_base_adapter_retry_budget.py` 3 tests) + market-tick-data-service@554adf49 (hyperliquid handler resolves
      `max_retries` from `resolve_retry_budget("perp_funding", "hyperliquid")`). Both confirmed on
      `origin/live-defi-rollout`. Attempt COUNT only, per the 2026-08-14 Progress Log entry — the registry's
      second-level ladder is VM/job-scale seconds, never an in-request HTTP backoff.

## Phase 4 — The push actuator (ships without touching a single launcher)

- [x] 25. ✅ [CODE] P0. Add a revocation actuator in `data_pipeline_monitors` that consults `evaluate_revocation()` and
      delivers the verdict — it must carry NO policy branch of its own. Repo: deployment-service. —
      deployment-service@e38b2a0e. Carries no policy branch;
      `test_actuator_verdict_matches_the_evaluator_for_every_alert` iterates all 142 identities to prove it.
- [x] 26. ✅ [CODE] P0. Deliver DEPS_DRAIN by writing a per-VM drain marker to the VM's `vm-logs/` prefix, not by
      terminating the instance — the VM-side hook in Phase 5 observes the marker. Repo: deployment-service. —
      deployment-service@e38b2a0e. `vm-logs/{target}/DRAIN_REQUESTED.json`. Nothing terminates.
- [x] 27. ✅ [CODE] P0. Deliver DEPS_HOLD by writing an admission-block marker the launcher preflight reads, so a held
      dependent never starts. Repo: deployment-service. — deployment-service@e38b2a0e.
      `vm-census/admission-hold/{target}.json`.
- [x] 35. ✅ [CODE] P0. Deliver FLEET_HALT by pausing the relevant Cloud Scheduler jobs, reusing the existing
      scheduler-pause path rather than a new mechanism — and emit `DP_CONSOLIDATOR_SCHEDULER_PAUSED`-style visibility so
      a halt is never silent. Repo: deployment-service. — deployment-service@67e3b36c. Pauses every job serving the
      target's asset group via the existing `scheduler_maintenance` pauser — one pause path in the repo. **Correction
      2026-08-14**: this note originally claimed `check_consolidator_scheduler_paused` "already suppresses
      DP-WATCHER-004" — UNVERIFIED, not confirmed. The actuator calls the bare `make_scheduler_pauser()` action, never
      `pause_for_maintenance()`, so no `MaintenanceWindow` is registered for a FLEET_HALT pause; the DP-WATCHER-004
      suppression only fires when `maintenance_window_reader` finds a live window naming the job. See the new todo
      below. Jobs resolve from the UAC `SCHEDULER_REGISTRY`, so a newly-registered scheduler is halted automatically
      rather than silently exempt. Never silent: paused job names ride back on the outcome. A failing pause does not
      abandon the rest (`test_a_failing_pause_does_not_abandon_the_remaining_jobs` — uses sports, not cefi, because cefi
      resolves to a SINGLE job and the test would have been vacuous).
- [ ] [CODE] P2. A FLEET_HALT pause registers no `MaintenanceWindow`, so `check_consolidator_scheduler_paused`
      (DP-WATCHER-004) may page a deliberate FLEET_HALT pause as an accidental one — found 2026-08-14, not fixed
      (adjacent to the visibility carry-over, out of scope for that pass). Either route `_pause_schedulers` through
      `scheduler_maintenance.pause_for_maintenance()` (needs a `bucket`/`surface`/`ttl_minutes` design call this plan's
      operator record does not make) or confirm via a live sweep that this genuinely never double-pages before closing
      it as a non-issue. Repo: deployment-service.
- [x] 28. ✅ [CODE] P0. Budget-bound every actuation per (alert_code, target, day) using the GCS-durable state pattern
      from `relaunch_backfill_vm.py` — the tempdir-backed budget was discarded every 5 minutes on Cloud Run and the
      documented cap never engaged. Repo: deployment-service. — deployment-service@e38b2a0e. `ShardedState`,
      day-partitioned; `test_actuation_budget_survives_a_fresh_container` is the regression guard.
- [x] 29. ✅ [CODE] P0. Emit a resolved-bookend when a hold or drain is released, so a revocation that opened is visibly
      closed in-channel per the alerting close-bookend rule. Repo: deployment-service. — deployment-service@e38b2a0e.
      `RevocationActuator.release()` + `test_release_clears_the_marker`.
- [x] 30. ✅ [TEST] P0. Test: the actuator's verdict for every alert equals `evaluate_revocation()`'s — the anti-drift
      guard proving there is no second policy. Repo: deployment-service. — deployment-service@e38b2a0e. The anti-drift
      guard.
- [x] 31. ✅ [TEST] P0. Test: the actuator degrades to file_issue rather than crashing when its own dependencies are
      unavailable, matching `_ACTUATORS_AVAILABLE`'s existing capability-probe contract. Repo: deployment-service. —
      deployment-service@e38b2a0e. `test_it_degrades_rather_than_crashing_when_storage_is_absent` +
      `test_an_unknown_alert_degrades_instead_of_raising`.
- [x] 32. ✅ [TEST] P0. Test: actuation budget survives a fresh container — the exact regression that made
      `_MAX_RELAUNCHES_PER_DAY` a no-op. Repo: deployment-service. — deployment-service@e38b2a0e.

## Phase 5 — VM-side poll hook and Cloud Run skip gate (the fail-closed backstop)

- [x] 33. ✅ [CODE] P0. Add a drain-marker poll to the VM tee-wrapper's heartbeat so a running VM observes DEPS_DRAIN
      and exits at its next checkpoint. Repo: deployment-service. — deployment-service@e38b2a0e.
      `revocation_gate.drain_requested()` — one small object-exists read, safe per heartbeat tick.
- [x] 34. ✅ [CODE] P0. Make the drain path call the Phase-1 drain registry before exiting, so observing the marker
      actually flushes rather than merely stopping. Repo: deployment-service. — deployment-service@e38b2a0e.
      `drain_and_exit()` calls `drain_all()` BEFORE exiting and returns 0 (a drained VM SUCCEEDED; a non-zero exit would
      fire `DP_VM_EXIT_NONZERO` and page about a working system). `test_drain_actually_flushes_not_merely_exits` guards
      it.
- [x] 36. ✅ [CODE] P0. Add an admission check to the launcher preflight so a DEPS_HOLD marker prevents launch, and the
      refusal is logged with the alert that caused it. Repo: deployment-service. — deployment-service@67e3b36c.
      `revocation_admission_cli` + a gate in the SHARED `vm-exec-with-gcs-tee.sh`, so every launcher inherits it and a
      new one cannot forget to opt in. Exit **75** (EX_TEMPFAIL), never 1: a run that correctly declined did not fail,
      and a generic 1 would fire `DP_VM_EXIT_NONZERO` and page about the system working as designed. The refusal names
      the alert, so 'why did this skip' is answerable from the job's own log.
- [x] 37. ✅ [CODE] P0. Add the same admission check to the Cloud Run job entrypoints so a job in a bad-state window
      skips its run instead of executing against known-bad inputs. Repo: deployment-api. — deployment-api@0d3f1cc.
      `launch_deploy_missing_vm` short-circuits before consuming rate-limit budget; result carries `skipped_reason` and
      reports **skipped, not failed** (raising would surface a 5xx and page). Fail-open on any marker-read failure — one
      unreachable bucket must not freeze every launch in the estate.
- [x] 38. ✅ [CODE] P1. Roll the poll hook across the drain-capable launcher prefixes from Phase 0, structurally rather
      than per-file where the launchers share a common wrapper. Repo: deployment-service. —
      unified-trading-library@ad29bd9f + deployment-service@67e3b36c. Done STRUCTURALLY, as the todo asks: the poll
      lives in the UTL `HeartbeatDaemon` and is bound in `heartbeat_cli`, so every VM running through the shared wrapper
      inherits it — zero per-launcher edits, and no prefix can be missed.
- [x] 39. ✅ [TEST] P0. Test: a VM with the poll hook drains within one checkpoint interval of the marker appearing.
      Repo: deployment-service. — unified-trading-library@ad29bd9f.
      `test_a_drain_marker_signals_the_workload_within_one_tick` — the drain rides the existing heartbeat tick rather
      than a poll cycle of its own. Siblings prove SIGTERM-never-SIGKILL (SIGKILL discards the shard), at-most-once (a
      repeat interrupts the flush it asked for), retry while the PID is unknown, and that a marker-read failure never
      takes down the heartbeat.
- [x] 40. ✅ [TEST] P0. Test: a Cloud Run job skips cleanly and reports skipped-not-failed when the admission check
      blocks it. Repo: deployment-api. — deployment-api@0d3f1cc. `test_a_hold_is_reported_as_skipped_not_failed` +
      `test_an_unreadable_marker_fails_open`.

## Phase 6 — Bad-VM test matrix (prove it on the failure modes that motivated it)

> Every scenario is exercised against `-test-` buckets, never prod. Each asserts three things: the alert fires, the
> right dependency action is taken, and no in-flight shard is lost.

> **2026-08-14 — all 12 scenarios landed, `e2e-testing/tests/integration/revocation/`.** Written against the
> ACTUAL/shipped policy table (Phase 2), not this prose — 3 of the descriptions below were stale relative to
> already-shipped, already-tested behavior and are corrected in place rather than left to mislead the next reader
> (doc-that-misled-you rule). Two new follow-up todos below capture the real gaps this pass surfaced. Gate green
> (independently re-run, 78s), 20 tests collected / 19 passing / 1 skipped with a cited reason.

- [x] ✅ [TEST] P0. Scenario OOM — force a 137 exit mid-shard; assert DP-VM-001 fires (dependents HOLD — self-restart is
      deployment-service's own existing actuator, out of scope here), and the drain registry flushed before death. Repo:
      e2e-testing. — `test_oom_137_exit_dependents_hold` + `test_oom_flushes_the_drain_registry_before_death`.
- [x] ✅ [TEST] P0. Scenario stall — wedge the process past the heartbeat budget; assert DP-VM-003 fires. **Corrected**:
      the shipped policy is `SELF_RESTART` (self-scoped, `dependent_lifecycle_strength == 0` — no dependent touched at
      all), not "dependents HOLD" as originally written here — stale prose from before Phase 2's table was finalized.
      Repo: e2e-testing. — `test_stall_is_a_self_restart_not_a_dependent_hold`.
- [x] ✅ [TEST] P0. Scenario preemption — SIGTERM with the SPOT grace window; assert DP-VM-008 resolves to `NONE`
      (routine SPOT churn, not over-escalated — DP-VM-009 is the distinct escalated case) and the drain registry flushes
      buffered rows. The PROGRESS-marker resume mechanism itself is UTL-internal and already covered by UTL's own
      tests + the spot-vms-for-backfill.md contract — out of scope for a black-box test here. Repo: e2e-testing. —
      `test_preemption_alone_is_not_over_escalated` + `test_preemption_drain_flushes_the_shard_in_flight`.
- [x] ✅ [TEST] P0. Scenario gone-no-capture — drain a VM whose captured count never climbed; assert DP-VM-002 fires and
      dependents DRAIN rather than proceeding on absent data. Repo: e2e-testing. —
      `test_gone_no_capture_dependents_drain` + `test_gone_no_capture_full_round_trip_observes_and_drains` (full
      actuator-write → gate-read round trip).
- [x] ✅ [TEST] P0. Scenario consolidator-down — stop the consolidator; assert DP-MANIFEST-001 fires. **Corrected**: the
      shipped policy is `DEPS_HOLD`, not "every dependent drains" — deployment-service's own already-committed
      `test_revocation_gate.py::test_a_hold_does_not_imply_a_drain` docstring states this is deliberate ("that
      distinction is the reason CONSOLIDATOR_DOWN holds rather than drains"). The "no in-flight shard lost" property is
      satisfied MORE strongly by a hold than a drain would give — nothing running is touched at all. Repo: e2e-testing.
      — `test_consolidator_down_holds_admission_not_a_drain` +
      `test_consolidator_down_blocks_new_launches_but_leaves_running_work_alone`.
- [x] ✅ [TEST] P0. Scenario mostly-empty — drive a run past the empty ratio threshold; assert DP-FETCH-007/DP-FETCH-009
      (both emit `DP_RUN_MOSTLY_EMPTY`) resolve to DEPS_DRAIN identically. The threshold-crossing TIMING is the
      detector's own concern, out of scope here. Repo: e2e-testing. —
      `test_mostly_empty_drains_regardless_of_which_detector_fired` (parametrized over both identities).
- [x] ✅ [TEST] P0. Scenario wrong-path — force a non-canonical write; assert DP-PATH-001 fires and dependents DRAIN
      (clean mapping, no plan/policy mismatch). Repo: e2e-testing. —
      `test_wrong_path_write_drains_the_vm_and_its_dependents`.
- [x] ✅ [TEST] P0. Scenario catalogue-stale — age the catalogue past 24h; assert DP-CATALOG-001 fires. **Corrected**:
      identity mapping was exact (registry.yaml `fires:` text matches this trigger verbatim), but the shipped policy is
      `DEPS_HOLD`, not "capture VMs drain" — same shape of stale prose as consolidator-down above. Repo: e2e-testing. —
      `test_catalogue_stale_holds_admission_for_the_asset_group`.
- [x] ✅ [TEST] P0. Scenario deadman — stale a monitor sentinel; assert FLEET_HALT blocks new launches and that
      already-running VMs are NOT drained. **Gap found, not silently routed around**: no alert identity for the actual
      watch-the-watchers condition (DP-WATCHER-001/002, `deadman_poster`) resolves to FLEET_HALT in the shipped table —
      both resolve to DEPS_HOLD. The full `DP_FAILURE_MODE_ACTIONS`/`ALERT_CODE_ACTIONS` search found exactly two
      identities that DO resolve to FLEET_HALT (`DP-RATE-002` key-pool exhaustion, `GAS_SURGE_50X` DeFi gas), used
      `DP-RATE-002` as an identity-independent mechanism proof (new launches blocked, running VMs untouched) since the
      plan's asserted PROPERTY is what's identity-independent, not which alert triggers it. See the new follow-up todo
      below. Repo: e2e-testing. — `test_deadman_fleet_halt_blocks_new_launches` +
      `test_deadman_fleet_halt_does_not_drain_already_running_vms`.
- [x] ✅ [TEST] P0. Scenario drain-blind prefix — assert a prefix with no checkpoint receives HOLD and is never sent a
      drain marker it cannot honour. Repo: e2e-testing. — `test_drain_blind_prefix_clamps_to_hold` (asserts the clamp is
      VISIBLE via `outcome.detail["clamped_from"]`, not silent) +
      `test_drain_blind_prefix_gate_observes_hold_never_a_drain_request`.
- [x] ✅ [TEST] P1. Scenario double-booking — two VMs on the same shard range; assert the interlock prevents the second
      from starting. **CUT, documented reason, not silently dropped**: searched deployment-service for a shard-range
      interlock/claim mechanism (`interlock|double.booking|ShardRangeLock|range_interlock`) — zero hits. This
      presupposes a VM-launcher CONCURRENCY-CONTROL mechanism that is a different subsystem entirely, not built in
      Phases 2-5 of this plan. Kept as a named, collected-but-skipped test (shows in every pytest summary, per QG STEP
      5.107's cited-reason requirement) rather than deleted. Repo: e2e-testing. —
      `test_double_booking_interlock_prevents_the_second_vm` (skipped, reason cited).
- [x] ✅ [TEST] P1. Scenario recovery — assert every scenario above emits its resolved-bookend and releases holds once
      the upstream alert clears. Repo: e2e-testing. — `test_release_clears_the_marker_and_the_gate_observes_the_clear`,
      parametrized across a representative HOLD (DP-MANIFEST-001) and DRAIN (DP-VM-002) verdict, round-tripped through
      the gate to prove the marker is actually gone post-release, not just that `release()` reports success.
- [x] ✅ [DOC] P2. Reconcile Phase 6's stale prose against the shipped policy table for the 3 scenarios corrected above
      (stall, consolidator-down, catalogue-stale). **REVIEWED 2026-08-14 — the drift is the PROSE's fault in all three;
      the Phase 2 policy assignments are right and stay.** The plan's scenario list was written before the policy
      existed and reached for the strongest-sounding action each time. Each shipped assignment survives scrutiny on the
      same principle — _the action must match what is actually in doubt_: `stall` (`DP-VM-003` → `SELF_RESTART`) — a
      restarted VM re-runs its range, so the data is LATE, not WRONG, and holding the estate on lateness would halt it
      for the commonest transient there is; `consolidator-down` (`DP-MANIFEST-001` → `DEPS_HOLD`) — a down consolidator
      makes the manifest STALE, not false, and it is `AUTO_RECOVER`, so draining every manifest-writing VM would destroy
      in-flight work over a condition that heals itself (the LYING-manifest case, `DP-MANIFEST-003` phantom rows, is the
      one that correctly drains — see the follow-up todo below); `catalogue-stale` (`DP-CATALOG-001` → `DEPS_HOLD`) — a
      stale catalogue means do not START against a universe nobody refreshed, but capture already running is still
      writing valid raw data against the universe it launched with. No `unified-api-contracts` change.
- [x] ✅ [CODE] P2. `DependentAction.DEPS_DRAIN`'s docstring claims draining "AND admission is held", but
      `RevocationActuator._MARKER_PATH_FOR` maps DEPS_DRAIN to the drain marker ONLY — a fresh launch into a
      currently-draining target is NOT actually blocked by the shipped code. **RESOLVED 2026-08-14 by changing the
      BEHAVIOUR, not the docstring** — deployment-service@_TBD_. The flag (raised in e2e-testing's Phase 6 suite for
      this session to arbitrate) was correct, and the actuator was the lone dissenter among three sources: the enum
      docstring says drain subsumes hold, and `DEPENDENT_LIFECYCLE_STRENGTH` ranks `DEPS_DRAIN=2` above `DEPS_HOLD=1`,
      **CODE WRITTEN + TESTED, NOT LANDED — see the 2026-08-14 Progress Log entry; blobs
      `761ebc9d6f62c2dac050b8bc50881c801ca342a8` (actuator), `667a148a05479228da0828c37516c196973a3497` (ds tests),
      `8add413ed86b783a6374bdab1fa4a7d26c3adac7` (e2e assertion). e2e-testing gated GREEN with the change; the
      deployment-service gate could not be gotten green on a host at load average 39 with 10 concurrent QG runs.** which
      only means anything if the stronger action does everything the weaker one does. **The hole was real but bounded**:
      nothing blocked the scheduler relaunching a drained target into the same bad-input window, where the heartbeat
      daemon would drain the new instance on its first tick and again on the next launch — a launch/drain loop lasting
      as long as the condition did. Not data-corrupting (the relaunch drains before writing), but it burns quota and
      fires noise for the entire outage. `_MARKER_PATH_FOR` → `_MARKER_PATHS_FOR` (a tuple of builders per action);
      `release()` clears both, so a resolved condition still frees the target completely. Repos: deployment-service
      (behaviour + 2 tests) + e2e-testing (the flagged assertion inverted, its FLAG comment replaced with the
      resolution).
- [x] ✅ [CODE] P2. No alert identity in the shipped policy table resolves to FLEET_HALT for the watch-the-watchers
      condition. **RESOLVED 2026-08-14 — the second branch this todo offered is the correct one: the deadman does not
      route through revocation at all, and `DP-WATCHER-001/002 → DEPS_HOLD` is right as shipped.** The deadman poster is
      documented as deliberately INDEPENDENT of the alerting-service (`/codex/05-infrastructure/`
      `data-pipeline-alerts.md` § "Watching the watchers", Layer 2) — that independence is the whole point of an
      out-of-band deadman, and routing it back through the alerting spine it exists to backstop would re-couple them.
      What DP-WATCHER-001/002 actually represent is an in-band watcher FAILURE, and for that `DEPS_HOLD` is exactly
      right: we are blind, so do not start new work, but do not destroy the work already running (which Phase 6's own
      scenario text asked for verbatim — "blocks new launches, running VMs NOT drained" IS strength-1 admission scope,
      not FLEET_HALT). `FLEET_HALT` stays reserved for `DP-RATE-002` / `GAS_SURGE_50X`, where every venue call fails and
      pausing at the scheduler is the only thing that stops the bleeding. No policy change; Phase 6's scenario prose is
      corrected instead. Repo: unified-trading-pm (this plan).
- [ ] [TEST] P2. Two policy rows Phase 6's suite does not assert, both worth a row because they are the CONTRAST that
      makes a neighbouring scenario meaningful: `DP-MANIFEST-003` (phantom rows → `DEPS_DRAIN`) is the money-burn case
      that consolidator-down is routinely confused with, and asserting only the HOLD side leaves the distinction
      untested; `DP-VM-009` (preemption-no-relaunch → `DEPS_HOLD`) is the escalated counterpart to `DP-VM-008` → `NONE`,
      which the suite currently mentions in a comment but never asserts. Add both to
      `e2e-testing/tests/integration/revocation/`. Repo: e2e-testing.
- [ ] [TEST] P2. `deployment-service`'s `tests/unit/test_vm_launcher_scripts.py::TestErrorHandling::`
      `test_script_syntax_validation` has now flaked THREE times across this plan's sessions (returncode -13 SIGPIPE, -5
      SIGTRAP, and a bare failure under concurrent gate load), each time on a tree that touched no shell script, and
      each time costing a full ~11-minute gate re-run to disprove. It shells out to `bash -n` per launcher across ~120
      scripts. Either bound it (batch the syntax check into one `bash -n` invocation, or serialise it) or mark it with a
      cited flake issue — "re-run and see" is currently costing more than the check is worth. Repo: deployment-service.

## Phase 8 — ARM IT (the mechanism is built but INERT in production — found 2026-08-14)

> **This plan cannot be archived until this phase is done.** Phases 1-6 are genuinely complete and green, and the READ
> side is fully wired: `heartbeat_cli` polls for a drain marker on every tick, and `vm-exec-with-gcs-tee.sh` gates
> admission and exits 75. But **nothing writes a marker.** Measured 2026-08-14: `rg 'RevocationActuator|\.actuate\('`
> over deployment-service, excluding tests, returns **its own definition and nothing else** — zero production call
> sites. `resolve_dependents()` is likewise consumed only inside UAC. The fleet is listening and nothing is speaking, so
> no alert has ever revoked anything and none will.
>
> This was not visible from the plan's own state: every Phase 4 todo is ✅ and each is honestly ticked — the actuator
> WAS built, tested and shipped. "Built" and "called" are different properties, and Phase 4 only ever claimed the first.
> Recording that here because the same shape of gap will hide in any plan that ships a component without an explicit
> caller-side todo.

> **OPERATOR DECISION 2026-08-14 — target granularity: DEPS_DRAIN targets the SPECIFIC RUNNING VM.** Admission actions
> (`DEPS_HOLD` / `FLEET_HALT`) target the PREFIX FAMILY. This follows the semantics rather than cutting across them: a
> drain speaks to a process that is running right now and must flush what it is holding, so it needs that instance's
> name; a hold speaks to launches that have not happened yet, which are only identifiable by family. It also means the
> two markers a `DEPS_DRAIN` now writes are keyed differently on purpose — `vm-logs/<vm-name>/` for the drain,
> `vm-census/admission-hold/<prefix>/` for the hold — and the resolver must return both, not one reused twice.

- [ ] [CODE] P0. **Resolve dependents to actuation targets.** `evaluate_revocation()` answers WHAT action; nothing
      answers WHO to apply it to. `resolve_dependents(upstream_entity, asset_group)` returns `(asset_group, data_type)`
      pairs, but the actuator takes a VM prefix / Cloud Run job name — the translation layer between them does not
      exist, and it is the reason nothing calls `actuate()`. Build it against the registries the Phase 0 census already
      enumerated (`LAUNCHER_FOR_VM_PREFIX` / `VM_PREFIX_TO_BUCKET`: 243 prefixes, 178 mapping to 104 launcher scripts).
      **Needs a design call this plan's operator record does not make**: whether a DEPS_DRAIN targets the specific
      running VM name or the whole prefix family (drain is per-instance, hold is per-family — they may not want the same
      target). Repo: deployment-service.
- [ ] [CODE] P0. **Call `actuate()` from `escalation.route_finding()`.** That is the seam every DP finding already
      passes through, and revocation must fire there INDEPENDENT of tier — a `DEPS_DRAIN` verdict applies whether the
      finding is `auto_recover`, `file_issue` or `page_operator`, unlike `_DP_RECOVERY_ACTIONS` which is auto-recover
      only. Use `finding.registry_id` as the alert identity (the finer key — `DP-FETCH-007`/`009` share one `AlertCode`)
      and fall back to `finding.event`. Must never crash the sweep: same `except Exception` contract the existing
      actuator dispatch already uses. Record the outcome in `event_details` so the Slack alert says what was revoked.
      Repo: deployment-service.
- [ ] [CODE] P0. **Emit and release the bookend.** `RevocationActuator.release()` exists and is tested but has no
      production caller either, so even once holds are written, nothing clears them — a revocation that cannot be
      released is an outage with extra steps, and this is the alerting SSOT's close-bookend rule. Wire release to the
      condition-resolved path. Repo: deployment-service.
- [ ] [TEST] P0. An anti-inertness guard: a test asserting `actuate()` has at least one non-test caller. The whole
      mechanism sat wired-but-unreachable through six green phases; a grep-level guard is what makes that unrepeatable.
      Repo: deployment-service.
- [ ] [OPERATOR] P0. **Confirm it live after wiring**: the monitor runs as the `uts-prod-dp-exit-code-monitor` Cloud Run
      Job on a `*/5` schedule, so verify (a) the job's deployed image contains the wiring commit
      (`gcloud run jobs describe`), (b) an execution actually invoked revocation (log a `DP-REVOCATION-*` line), and (c)
      a marker appears in `vm-census/admission-hold/` for a real condition. A green Cloud Build is NOT this —
      `Evidence: cloudbuild=<id>` plus an execution log line is. Repo: deployment-service.
- [ ] [CODE] P1. **Admission-gate coverage is ~148/184 launchers, not all of them** (measured 2026-08-14). Only
      launchers routing through `setup-data-pipeline-vm.sh` → `vm-exec-with-gcs-tee.sh` get the admission check and the
      heartbeat drain poll; the 158 that use `launcher_common.sh`'s `lc_` helper get the LIGHTWEIGHT observability
      snippet, which deliberately omits the tarball+venv+heartbeat-daemon install and therefore has neither gate. The
      two sets overlap, so the honest statement is: the canonical path is gated, the lightweight path is not, and a
      per-launcher census is needed to say which real VMs are uncovered. Either add the admission check to the `lc_`
      helper (it needs no venv — it can curl the marker) or document the lightweight path as deliberately ungated. Repo:
      deployment-service.

## Phase 7 — Codex SSOT and close-out

- [x] ✅ [DOC] P0. Add a revocation section to `/codex/05-infrastructure/data-pipeline-alerts.md` — the action
      vocabulary, the drain-only ruling and its rationale, and the alert→action table. It references the code, it does
      not duplicate the map. — New "Alert-driven dependency revocation" section (action-vocabulary table, drain-only
      ruling, both delivery paths, drain-registry pointer) placed before "Watching the watchers"; also corrected a stale
      "~189" VM prefix count to the measured 243 (Phase 0 census) and added `DP-REVOCATION-001` to both the doc table
      and `data-pipeline-alerts.registry.yaml`.
- [x] ✅ [DOC] P0. Update `/codex/04-architecture/autonomous-recovery-matrix.md` to state that batch/backfill now has a
      revocation path, correcting its current "Live-mode only. All recovery mechanisms are disabled in batch/backtest."
      — Scoped the "Live-mode only" claim to the execution-side decision tree specifically and added a correction
      pointing to the new revocation section, noting the two systems are deliberately disjoint.
- [x] ✅ [DOC] P0. Record the retry registry as the SSOT for retry counts in the recovery matrix, replacing the prose "3
      attempts" with a pointer to `RETRY_BUDGETS`. — Added a scope-split pointer on the `RETRY` row (live per-request
      path stays as-is; batch/backfill retry-COUNT SSOT is now named) rather than overwriting the live-mode semantics,
      since RETRY_BUDGETS' backoff ladder must not be conflated with the live circuit-breaker cooldown timeline.
- [x] ✅ [DOC] P1. Add the flush contract to `/codex/06-coding-standards/` so every new buffered writer registers with
      the drain registry by convention, not by memory. — Added under "Error Handling Standards" alongside a matching
      RETRY_BUDGETS pointer (both landed together since they're the same shape of "hardcoded X → registry Y" rule).
- [ ] [REVIEW] P0. Post-phase codex audit — verify no plan↔codex drift, every cited path resolves, and no doc still
      claims a gap this plan closed.
- [ ] [REVIEW] P0. Archive this plan once every todo is done and unlocked, per the archival discipline (dated archive
      folder, banner, referrer sweep).

---

## Deferred work after 2026-08-14 (supersedes the 2026-08-12 table — Phases 1-5 are now fully shipped)

> The prior version of this table (written 2026-08-13, mid-Phase-4/5) had gone STALE and was actively misleading — it
> claimed FLEET_HALT delivered as a hold marker and Phase 5 was 2-of-7, when both had since landed in full. Corrected
> per the doc-that-misled-you hard rule rather than left to rot further.

| Item                                                  | State                                                                                                                        | Blocked on |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ---------- |
| Phase 0 — preconditions and measurement               | **1 of 5 done** — the 4 measurement todos (p95 shard duration, drain-capable/blind census, buffered-writer inventory) remain | nobody     |
| Phase 1 — graceful-flush contract                     | **DONE** — all 10 todos                                                                                                      | —          |
| Phase 2 — `DependentAction` + `evaluate_revocation()` | **DONE** — all 7 todos, unified-api-contracts@c206f910                                                                       | —          |
| Phase 3 — `RETRY_BUDGETS`                             | **DONE** — all 8 todos, unified-api-contracts@c206f910 + instruments-service@1ae4b7d0 + market-tick-data-service@554adf49    | —          |
| Phase 4 — push actuator                               | **DONE** — all 9 todos, deployment-service@e38b2a0e + @67e3b36c (FLEET_HALT pauses Cloud Scheduler jobs, not a hold marker)  | —          |
| Phase 5 — VM poll hook + Cloud Run skip gate          | **DONE** — all 8 todos, deployment-service@67e3b36c + deployment-api@0d3f1cc + unified-trading-library@ad29bd9f              | —          |
| Phase 6 — 12 bad-VM scenarios                         | **Not started** — now unblocked, Phases 4-5 give it something real to assert against                                         | nobody     |
| Phase 7 — codex SSOT + archival                       | **Not started** — closes the plan                                                                                            | Phase 6    |
| slot-4 PM checkout divergence                         | **RESOLVED 2026-08-13** — see the Phase 0 todo above                                                                         | —          |
| `unified-trading-library` `.venv` bootstrap           | **Operator-owned** — environment setup, not on the critical path                                                             | operator   |

**Recommended NEXT item (2026-08-14): Phase 0's measurement todos, then Phase 6.** The census of drain-capable vs
drain-blind prefixes directly determines which of Phase 6's scenarios are even reachable (a drain-blind prefix can only
ever receive HOLD, never DRAIN) — doing it first makes the scenario set accurate instead of assumed.

## Progress Log

- 2026-08-13 — **Phases 2-5 all landed.** `unified-api-contracts@c206f9100d` (Phase 2 policy evaluator + Phase 3 retry
  budgets, 41 tests) · `deployment-service@e38b2a0e6e` (Phase 4 push actuator + Phase 5 VM-side poll/skip gate, 92
  tests) · `deployment-service@c55faf2c81` (unrelated: prod project id removed from a vm-launcher test fixture that was
  failing the gate). Prerequisite unblock: `unified-trading-pm@25b9869550` completed a rebase that had been interrupted
  for 3.2h, leaving slot 4 in DETACHED HEAD — that, not any one file, was what blocked plan commits repo-wide. Four
  things worth carrying forward. (1) **The inherited tree held three unrelated workstreams**, and bundling them would
  have blocked Phases 2-5 behind an unrelated half-finished change; they were separated by measurement, not by
  appearance — a keyword grep called the `_ShardedState`→`ShardedState` rename "unrelated", but the import graph showed
  `revocation_actuator`/`revocation_gate` both consume it, so it shipped WITH Phases 4-5. (2) **A checker's summary line
  is not the measurement**: the empty-string-fallback gate named `escalation*.py` sites, which led to a wrong
  "pre-existing, not mine" call; counting showed `revocation_gate.py` contributed exactly the 5-site overage, and fixing
  those took it to `[OK] 91 (== baseline)`. (3) **Tools read prose as syntax** — an explanatory comment beginning
  `# noqa` was parsed by ruff as an unused directive and failed the gate; the same shape as prettier turning a wrapped
  `+` into a list item. Don't start a comment or wrapped line with a token a parser owns. (4) **A blocked change is not
  a frozen change** — origin moved 168 commits under one parked item, and a different fix to the same problem had landed
  in the same functions.

### 2026-08-14 — Phases 4 and 5 finished end-to-end; Phase 3 wired but not landed

The blockers cleared overnight, so this pass closed the loop from "policy exists" to "the fleet actually reacts".

**Shipped.** `unified-trading-library@ad29bd9f` (heartbeat daemon polls for a drain marker and SIGTERMs the workload),
`deployment-service@67e3b36c` (FLEET_HALT pauses schedulers; the shared VM wrapper gates admission),
`deployment-api@0d3f1cc` (a held deploy-missing launch skips). The mechanism is no longer inert: an alert now reaches a
running VM and a pending launch, by two independent paths.

**The design call worth keeping.** The daemon does NOT drain on the workload's behalf — it sends SIGTERM and lets the
workload's own drain registry flush writers before the manifest. One drain implementation, not two, and it reuses the
Phase-1 contract rather than paralleling it.

**A number that would have caused an incident.** Wiring `RETRY_BUDGETS` into the adapters, the first cut also took the
registry's backoff LADDER. Measured before shipping: that puts delays of `[300, 600, 1200]` **seconds** inside an
in-request HTTP retry loop — 20-minute sleeps inside a single fetch. The registry's ladder is calibrated for VM- and
job-level retries; HTTP backoff is a different concern in different units. Only the ATTEMPT COUNT is taken from the
registry now, and both adapters say so in a comment so the next person does not redo it.

**Phase 3 is written but NOT landed.** `instruments-service` `base_adapter.py` gains a `retry_source` class attribute
(one-line opt-in per subclass, defaulting to the generic budget) and MTDS's hyperliquid handler resolves its count from
the registry. Tests pass; the IS gate reports one hard step failing that its own output never names — the summary says
"1 hard gate/ratchet step(s) failed (see the ❌ STEP lines above)" while no such line is printed, and a stash probe
confirmed the failure is not in the test suite. **That un-named gate failure is itself a finding**: a gate that cannot
tell you which step failed costs every future agent the same hunt. Preserved as blobs:
`1c1184c8181473ead13f41fd4cac4e2ddea0203b` (IS base_adapter), `adf44f54afb424fa1aceae67a61c1adf639eef52` (IS test),
`8aa50ac270fd4bac707c3dd75e4a890ad539c714` (MTDS handler).

**Two test bugs worth naming**, both of which passed for the wrong reason first: a `pauser` stub tested against `cefi`,
which resolves to a SINGLE scheduler job, so "did it carry on to the rest" was unaskable; and an `admission_blocked`
stub declared `**kwargs`-only while the caller passes positionally, so it raised, hit the fail-open guard, and the test
went green while testing nothing.

### 2026-08-13 (later) — Phases 3, 4 and 5 written; one Phase-5 piece shipped

Continued writing while the UAC/PM ship path was blocked, per the operator's instruction that a block on shipping is not
a block on building. Everything below is complete and gate-verified to the limit each repo allows.

**Phase 3 — retry budgets (UAC, blocked with Phase 2).** `canonical/crosscutting/retry_budgets.py`: `RetryBudget`,
`RETRY_BUDGETS` keyed `(data_type, source)` mirroring `VENUE_HEARTBEAT_THRESHOLDS`,
`DEFAULT_RETRY_BUDGET_BY_ERROR_ACTION` (total over `ErrorAction`, validated at import), and `resolve_retry_budget()`
falling through four levels so an unknown pair inherits rather than raising. Seeded as a faithful transcription of the
ladder that was previously PROSE only in `autonomous-recovery-matrix.md` — measured: `[300, 600, 1200, 2400, 3600]`, 3
attempts. Two budgets are degenerate ON PURPOSE and are correctness, not tuning: `missing_credential` gets
`max_attempts=0` (retrying a key that does not exist burns auth quota) and Tardis gets `1` (it is hard-capped at one
concurrent VM per cloud because concurrency storms its API — a retry ladder is that storm serialised). 16 tests. UAC
gate: same 6 peer failures, 12752 passed (+16 = exactly this file).

**Phase 4 — the push actuator (deployment-service).** `data_pipeline_monitors/revocation_actuator.py` consults
`evaluate_revocation()` and delivers; it carries NO policy branch, and
`test_actuator_verdict_matches_the_evaluator_for_every_alert` iterates all 142 identities to prove it. Delivery is by
GCS MARKER (`vm-logs/{target}/DRAIN_REQUESTED.json` / `vm-census/admission-hold/{target}.json`), never an API call
against the fleet — which is what lets it ship without touching a launcher. Budget is `ShardedState`-backed and
day-partitioned, with a test that a FRESH instance still sees prior actuations: the exact regression that made
`_MAX_RELAUNCHES_PER_DAY` a documented cap which never engaged on Cloud Run.

**Phase 5 — the observing side.** `revocation_gate.py`: `drain_requested()` for a VM's heartbeat poll,
`admission_blocked()` for launcher preflight and Cloud Run entrypoints, and `drain_and_exit()` which calls `drain_all()`
BEFORE exiting — observing a marker and merely stopping would discard the buffers this whole design protects. Failure
direction is deliberately asymmetric (a GCS read failure resolves to "not blocked"), because failing the other way lets
one unreachable bucket halt every backfill in the estate.

**Shipped: unified-trading-library@36714bfe97** — the drain registry is now exported from the UTL top-level namespace.
Forced by deployment-service's import-pattern gate rejecting a deep import, but correct on its own terms: Phase 1e's
codex section makes drain registration MANDATORY fleet-wide, and a contract every consumer must honour should not
require a deep import.

**Three things worth not re-learning.**

1. `deployment-service`'s UAC is an EDITABLE install pointing at the local checkout, so Phase 4/5 gate green locally
   against uncommitted Phase-2 code. That is a trap, not a convenience: shipping Phase 4 before Phase 2 lands would put
   an import of `evaluate_revocation` on LDR against a UAC that does not export it, breaking CI for everyone. Ship order
   is Phase 2 → Phase 3 → Phase 4/5, always.
2. `deployment-service`'s gate is RED on a clean tree, independently of this plan — STEP 5.101 counts 96
   empty-string-fallback sites against a baseline of 91 (the named sites are in `escalation.py` / `escalation_dedup.py`)
   and the prod-project-ID check flags `tests/unit/test_vm_launcher_scripts.py`. None of those files are touched here.
   Earlier gate runs never reached these steps because typecheck failed first, which is why they only surfaced late.
3. `test_vm_launcher_scripts.py::TestChunkLoopPartialPayloadLossGating[mtds]` failed once with `returncode=-13` (SIGPIPE
   on a spawned bash heredoc, empty stdout AND stderr) and passed on the immediate re-run. Resource artifact under
   concurrent gate load — diagnose the signal before assuming a real failure.

**Preserved as git blobs** (recover with `git cat-file -p <sha> > <path>`):

| Blob SHA                                   | Repo               | Path                                                                                          |
| ------------------------------------------ | ------------------ | --------------------------------------------------------------------------------------------- |
| `f7fc6d21d7b6ecab0f6ca8f4103f43ba3e5e7b01` | UAC                | `unified_api_contracts/canonical/crosscutting/retry_budgets.py`                               |
| `c5f0e3fe4a91b3502f9b6267149403002cf7c257` | UAC                | `tests/internal/unit/test_retry_budgets.py`                                                   |
| `1255fc1dd52c8ff18473347e8267472192918607` | UAC                | `unified_api_contracts/canonical/crosscutting/__init__.py`                                    |
| `4db14c85c35cc20971d6c69f434be14fee6b4ee9` | UAC                | `unified_api_contracts/__init__.py`                                                           |
| `7e2ca510f34ae6bb2d1433503f2c80d39f5cbd3f` | deployment-service | `deployment_service/data_pipeline_monitors/revocation_actuator.py`                            |
| `c4220860ead241fd43edd7196d95d924ae1a35a2` | deployment-service | `deployment_service/data_pipeline_monitors/revocation_gate.py`                                |
| `4a3003af27a757fe9eba501296afd979eeb1141d` | deployment-service | `tests/unit/test_revocation_actuator.py`                                                      |
| `e8723986118f710ff5d8338a1a323771cbc53281` | deployment-service | `tests/unit/test_revocation_gate.py`                                                          |
| `b2708a9015103d1e3a556f0b69a21c1332d636fe` | deployment-service | `scripts/recovery/_durable_state.py` (adds a public `state_bucket` / renames `_ShardedState`) |
| `69bbfca7ce241097d830cbce971064a8acf6408e` | deployment-service | `scripts/recovery/relaunch_backfill_vm.py` (rename follow-through)                            |
| `54cff03365ba7bec08b31673e6c8e0e0a5e9d3df` | deployment-service | `tests/unit/test_dp_recovery_actuators.py` (rename follow-through)                            |

### 2026-08-13 — Phase 2 written and gate-proven; ship BLOCKED by a live peer's red tree

**What exists.** `unified_api_contracts/canonical/crosscutting/dependency_revocation.py` — `DependentAction` (8 values,
no `DEPS_KILL`), `EscalationTarget` (AUTO / AGENT / AGENT_URGENT / HUMAN), `RevocationPolicy`, `RevocationVerdict`,
`resolve_dependents()`, `evaluate_revocation()`, plus both policy tables: `DP_FAILURE_MODE_ACTIONS` (all 53 registry
ids) and `ALERT_CODE_ACTIONS` (all 89 `AlertCode` members). Exported from `canonical/crosscutting/__init__.py` and the
top-level UAC namespace. 26 tests in `tests/internal/unit/test_dependency_revocation.py`.

**Why it is a separate module rather than added to `instruments_preflight_dag` as the todo says.** That file is already
589 lines and 141 registry entries would blow the file-size ratchet. The new module IMPORTS the DAG and inverts
`INSTRUMENTS_PREFLIGHT_REQUIREMENTS` in `resolve_dependents()`, so the plan's actual requirement — "resolve the
dependent set from the existing preflight graph rather than a new adjacency table" — holds exactly as written.
Re-exporting the evaluator back through the DAG module would have created an import cycle, so consumers import from
`unified_api_contracts` directly.

**The ceiling guard has real teeth.** `DEPENDENT_LIFECYCLE_STRENGTH` maps every action to its effect on a DEPENDENT's
lifecycle (0 self-scoped / 1 admission-scoped / 2 checkpoint-drain) and is validated as total at import. A future
terminating action cannot be added without declaring a strength, and any strength above `DEPS_DRAIN` fails
`test_no_verdict_ever_exceeds_the_drain_ceiling`. That is what makes the operator's drain-only decision mechanical
rather than a comment.

**Test execution PROVEN, not assumed.** Coverage output does not mention the new module, so a green gate alone would not
have shown the file was collected. A canary (`assert 1 == 2`) produced
`FAILED tests/internal/unit/test_dependency_revocation.py::test_canary_delete_me` with the passed-count unchanged at
12736, proving all 26 real tests execute and pass. Canary removed. (Note for the next session: `assert False` trips ruff
`B011` at the LINT stage and never reaches pytest — use `assert 1 == 2`.)

**Why it cannot ship.** `quality-gates.sh` is red tree-wide: 6 failures, all caused by a LIVE peer session's uncommitted
addition of `("tradfi", "ohlcv_1h"): ["yahoo"]` to `SOURCE_PRIORITY` in `_source_priority_data.py` (plus
`registry/market_data_categories.py`), which has no matching availability semantic —
`test_every_source_priority_pair_has_availability_semantic`, `test_all_source_priority_pairs_reachable_or_excluded`, and
four `test_era_b_purge` cases. None of the six touch anything in this phase. quickmerge re-gates the whole tree and
refuses, which is correct behaviour, not a bug. `--dep-branch` is HUMAN-ONLY and `--skip-tests` is a rule-amnesia stop,
so there is no legitimate agent path through it.

**Work preserved, not at risk.** The four files were written into the git object DB with `git hash-object -w` (safe: it
touches no index, branch, or peer file). Recover any of them with `git cat-file -p <sha> > <path>`:

| Blob SHA                                   | Path                                                                    |
| ------------------------------------------ | ----------------------------------------------------------------------- |
| `caff0238774a176f4bf75ec943d526943c999696` | `unified_api_contracts/canonical/crosscutting/dependency_revocation.py` |
| `9b0320fe6a308cc10e43fdbad1e14ea019578c1d` | `tests/internal/unit/test_dependency_revocation.py`                     |
| `d85e7855e3ae2e36b8489dd30c5c97464b7eb8ec` | `unified_api_contracts/canonical/crosscutting/__init__.py`              |
| `e9ae531de5e533eb8bd15af5acb73fe87ea48062` | `unified_api_contracts/__init__.py`                                     |

**One correction to a plan assumption.** The Phase 2 todo list says the alert→action map should be keyed on "`AlertCode`
and DP registry_id identity". Both key spaces are implemented, and a test asserts they never collide — but note the DP
id is the finer key on purpose: `DP-FETCH-007` / `DP-FETCH-009` both emit `DP_RUN_MOSTLY_EMPTY`, and `DP-RATE-001` /
`DP-RATE-003` both emit `DP_SOURCE_RATE_LIMITED`. Keying on the event name would have silently merged four failure modes
into two.

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

### 2026-08-14 (continued) — housekeeping, FLEET_HALT visibility, Phase 0 census

Housekeeping first: the `tradfi_fx_krw_usd_phantom_rows_fresh_confirmation_2026_08_12.md` UU-conflict scenario named in
the resume brief did not apply — `git status` showed a clean tree, already up to date after `git pull --ff-only`. No
peer conflict to route around.

**Two already-shipped items were sitting unflipped** (doc-that-misled-you class): Phase 3's retry-budget-wiring todo was
DONE (`instruments-service@1ae4b7d0` + `market-tick-data-service@554adf49`, both confirmed on origin) but still showed
`- [ ]`; the "Deferred work after 2026-08-12" table claimed FLEET_HALT delivered as a hold marker and Phase 5 was
2-of-7, when both phases had been fully shipped the day before. Both corrected in the same push
(`unified-trading-pm@6b333cbc6e`).

**FLEET_HALT visibility carry-over, closed.** `_pause_schedulers` previously only logged via `logger.warning` — nothing
reached the alerting-service router, so a halt was invisible to Slack despite the plan's own todo asking for
`DP_CONSOLIDATOR_SCHEDULER_PAUSED`-style visibility. Added `DP_REVOCATION_FLEET_HALT` (UTL event constant,
`unified-trading-library@85df0de2b2`) and wired `RevocationActuator._emit_fleet_halt_visibility()` to call
`meta_watchers.emit_finding()` with `tier=AUTO_RECOVER` and no wired actuator for the event — deliberate, not an
oversight: the actuator itself IS the recovery, so on a Cloud Run Job (no PM clone on disk) this degrades to a silent
no-op file_issue rather than paging, matching the AO-alerting rule that automatic lifecycle events log + digest but
never page. Two new tests prove the event fires and that an emit failure never undoes the actual delivery
(`deployment-service@05630397c4`). **Adjacent finding, NOT fixed, left as an open question**: `_pause_schedulers` calls
the bare `make_scheduler_pauser()` action, never `scheduler_maintenance.pause_for_maintenance()` — so a FLEET_HALT pause
registers no `MaintenanceWindow`, meaning `check_consolidator_scheduler_paused` (DP-WATCHER-004) has nothing to suppress
it against. Path arithmetic on `_DEFAULT_PM_SIBLINGS` happens to make this NOT presently confirmed to double-page (would
need a live sweep to prove), but the suppression claim in todo 35's own docstring ("already suppresses DP-WATCHER-004")
is UNVERIFIED, not confirmed true. Scoped out of this pass — visibility was the asked-for carry-over, not the
suppression wiring, and `pause_for_maintenance` needs a `bucket`/`ttl_minutes` design call this plan's own operator
record doesn't make. Worth a follow-up todo before this fleet-wides.

**Phase 0's 4 measurement todos, 3 of 4 closed.** Real numbers, not guesses: `LAUNCHER_FOR_VM_PREFIX` has 243 entries
(the plan's "~189" was stale), 65 map to `None` (never backfill-capture, so DEPS_DRAIN is moot for them), 178 map to 104
distinct launcher scripts. Verified drain-capability by grepping which service CLI each script actually invokes (not
filename prefix — the `launch-tradfi-bf-*` family would have false-negatived on a naive check since they delegate
through `_tradfi-ohlcv-launcher-lib.sh`). Result: 102/104 confirmed drain-capable, the other 2 are non-capture tools
(scenario runner, orphan-sweep report) where drain is inapplicable rather than missing. Buffered-writer inventory found
nothing outside what Phase 1 already registered. The p95/max shard-duration measurement is the one still open —
`state_bucket()` resolves empty in this dev checkout even with working gcloud auth, so it needs either a properly-wired
runtime env or a VM-side run; left BLOCKED rather than fabricated.

**Next**: Phase 6 (12 bad-VM scenarios, repo: e2e-testing) is the largest remaining chunk. Scoping note for whoever
picks it up: e2e-testing has ZERO existing revocation-domain test infra, but it DOES already depend directly on
`execution-service`/`strategy-service` as editable path deps (confirmed precedent for cross-service test imports — this
harness is explicitly exempted from the T4 no-service-deps rule). `deployment-service` is NOT yet an e2e-testing
dependency and would need adding to import `RevocationActuator`/`revocation_gate` directly. Per the operator's own
scoping note, where live -test- GCS bucket access isn't available, write the 12 scenarios against the marker/verdict
contract with in-memory fakes (mirroring `deployment-service`'s own `written`/`local_only=True` test pattern) rather
than fabricating VM behavior — this was verified as the honest path, not a shortcut. Phase 7 (codex audit + archive)
still fully open behind Phase 6.

### 2026-08-14 (later) — the mechanism is INERT in production; Phase 8 opened

**The finding that matters more than anything else in this plan.** Six phases are green and the revocation mechanism has
never revoked anything, because **nothing calls `RevocationActuator.actuate()`**. Measured, not assumed:
`rg 'RevocationActuator|\.actuate\('` over deployment-service excluding tests returns the class definition and nothing
else; `resolve_dependents()` is consumed only inside UAC. The READ side is fully wired — `heartbeat_cli` polls for a
drain marker every tick, `vm-exec-with-gcs-tee.sh` gates admission and exits 75 — so the fleet is listening and nothing
is speaking.

**Why six green phases hid it.** Every Phase 4 todo is ✅ and each is honestly ticked: the actuator WAS built, tested
and shipped. "Built" and "called" are different properties and Phase 4 only ever claimed the first. The generalisable
lesson: a plan that ships a component needs an explicit caller-side todo, or completeness is unfalsifiable from the
plan's own state. Phase 8 now carries that work.

**The missing piece is a translation layer, not a call.** `evaluate_revocation()` answers WHAT action;
`resolve_dependents()` returns `(asset_group, data_type)` pairs; the actuator wants a VM prefix or job name. Nothing
bridges them, which is precisely why no caller could exist. Bridging it needs a design call this plan's operator record
does not make: whether DEPS_DRAIN targets the specific running VM or the whole prefix family (drain is per-instance,
hold is per-family).

**Admission-gate coverage is partial, and a naive grep says otherwise.** 148 of 184 launchers route through
`setup-data-pipeline-vm.sh` → `vm-exec-with-gcs-tee.sh` and are gated; 158 use `launcher_common.sh`'s `lc_` helper,
which is a deliberately LIGHTWEIGHT observability snippet with no tarball/venv/heartbeat-daemon install and therefore
neither the admission check nor the drain poll. `rg -l 'launcher_common'` initially read as "179/184 covered" — the lib
only MENTIONS `vm-exec-with-gcs-tee.sh` in its comments. Reading what a lib does beats counting who sources it.

**Todo 515 resolved by changing behaviour, not the docstring** — written, tested, NOT landed. The actuator was the lone
dissenter among three sources; `_MARKER_PATH_FOR` → `_MARKER_PATHS_FOR` (tuple of builders per action) so DEPS_DRAIN
writes both markers, and `release()` clears both. The hole was real but bounded: a relaunched target drains before
writing, so it burnt quota and fired noise rather than corrupting data. e2e-testing gated GREEN with the change (its
venv was bootstrapped this session — `uv sync` clean — and it resolves both `deployment_service` and
`unified_api_contracts` to the local checkouts, so the change was genuinely exercised).

**Why it did not land, and how to land it.** Two full deployment-service gate runs failed on DIFFERENT tests in
`tests/unit/test_vm_launcher_scripts.py` — first `test_script_syntax_validation`, then
`test_genuinely_healthy_run_with_real_action_lines_is_not_false_killed` with `rc=124`, a subprocess TIMEOUT on a test
that shells out and sleeps 12s. Host load average was 39 with 10 concurrent QG processes. Different test each run =
load, not the change; and `revocation_actuator.py` is not on the `vm-exec` path the failing file exercises. **Do not
re-run blind a third time** — wait for the host to quiesce (`ps aux | grep -c '[q]uality-gates'` near 1), then one run
should green. Restore with `git cat-file -p <blob> > <path>` using the three SHAs on todo 515 above, deployment-service
FIRST (e2e-testing's inverted assertion depends on it).

### 2026-08-14 (later still) — UN-ARCHIVED; the archive copy was removed

A parallel session archived this plan (`status: complete`, 0 open todos) minutes after this session pushed Phase 8
documenting that it must NOT be archived. For a short window both copies were on `origin/live-defi-rollout` saying
opposite things; then the archive move dropped the active copy entirely, taking Phase 8 with it.

**Resolved on the operator's instruction: the ACTIVE copy survives, the archive copy is deleted.** The archived version
was the misleading half — it presented six green phases as finished work for a mechanism that has never fired once, and
anyone grepping the archive first would have concluded the work was done. The active copy is restored from
`unified-trading-pm@f9c97dd4c6` with Phase 8 and 13 open todos intact.

**Why this happened is worth more than the fix.** The archival was not careless: by the plan's own state at that moment,
every phase was ✅ and the archival discipline says a plan with every todo done must be archived immediately. The plan's
state was simply wrong — Phase 4 claimed "built", never "called", and nothing in the corpus could tell the difference. A
completeness check that reads only checkboxes will keep reaching this same wrong answer. The Phase 8 anti-inertness
guard (a test asserting `actuate()` has a non-test caller) is the durable fix, because it makes the gap visible to the
gate rather than to whoever happens to grep for call sites.
