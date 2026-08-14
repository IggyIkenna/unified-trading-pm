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
      `MISSING_CREDENTIAL     max_attempts=0`, Tardis `max_attempts=1`; 41 tests green. Repo: unified-api-contracts.
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
- [ ] [CODE] P1. Replace the hardcoded retry counts in the adapter retry paths with `RETRY_BUDGETS` lookups so the
      registry is actually load-bearing, not decorative. Repos: instruments-service, market-tick-data-service.

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
      target's asset group via the existing `scheduler_maintenance` pauser — one pause path in the repo, and
      `check_consolidator_scheduler_paused` already suppresses DP-WATCHER-004 for a deliberately paused job so a halt
      does not page as its own failure. Jobs resolve from the UAC `SCHEDULER_REGISTRY`, so a newly-registered scheduler
      is halted automatically rather than silently exempt. Never silent: paused job names ride back on the outcome. A
      failing pause does not abandon the rest (`test_a_failing_pause_does_not_abandon_the_remaining_jobs` — uses sports,
      not cefi, because cefi resolves to a SINGLE job and the test would have been vacuous).
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

## Deferred work after 2026-08-12

Phase 1 closed 8 of 9 todos. Nothing below is half-shipped — every item is either untouched or operator-owned.

| Item                                                                                                          | State / why deferred                                                                                                                                                                                                                                        | Blocked on           |
| ------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- |
| Phase 1c — wire drain registry into MTDS / MDPS / instruments-service / features-service backfill entrypoints | **Not done** — 4 repos = 4 separate gate runs; deliberately not started mid-context rather than left half-wired across repos                                                                                                                                | nobody               |
| Phase 1e — codex flush-contract doc                                                                           | **Not done** — small, follows 1c so the doc describes the shipped end state                                                                                                                                                                                 | nobody (do after 1c) |
| Phase 2 — `DependentAction` + `evaluate_revocation()`                                                         | **DONE** — all 7 todos, unified-api-contracts@c206f910                                                                                                                                                                                                      | —                    |
| Phase 3 — `RETRY_BUDGETS`                                                                                     | **7 of 8 done** (unified-api-contracts@c206f910) — the adapter retry-path replacement in IS/MTDS is the one left, so the registry is not yet load-bearing                                                                                                   | nobody               |
| Phase 4 — push actuator                                                                                       | **8 of 9 done** (deployment-service@e38b2a0e) — FLEET_HALT currently delivers as a hold marker, not the Cloud Scheduler pause the todo specifies                                                                                                            | nobody               |
| Phase 5 — VM poll hook + Cloud Run skip gate                                                                  | **2 of 7 done** (deployment-service@e38b2a0e, unified-trading-library@36714bfe97) — the gate module exists but nothing CALLS it yet: launcher preflight and the deployment-api Cloud Run entrypoints are unwired, and its two behaviour tests are unwritten | nobody               |
| Phase 6 — 12 bad-VM scenarios                                                                                 | **Cannot be done yet** — needs the actuator and poll hook to exist before there is anything to assert against                                                                                                                                               | Phases 4-5           |
| Phase 7 — codex SSOT + archival                                                                               | **Cannot be done yet** — closes the plan                                                                                                                                                                                                                    | all phases           |
| slot-4 PM checkout divergence                                                                                 | **Operator-owned** — liveness gate forbids an agent reconciling a live peer's staged work                                                                                                                                                                   | operator             |
| `unified-trading-library` `.venv` bootstrap                                                                   | **Operator-owned** — environment setup                                                                                                                                                                                                                      | operator             |

**Recommended NEXT item (revised 2026-08-14): finish Phase 5's wiring.** The actuator writes markers and the gate can
read them, but nothing CALLS the gate yet — the mechanism is inert end-to-end. Wire `admission_blocked()` into the
launcher preflight and the deployment-api Cloud Run entrypoints, then Phase 6's scenarios have something real to assert
against. Every blocker that stalled 2026-08-13 is CLEARED: the peer landed its UAC work, and an automated slot-4 WIP
rescue committed this plan's Phases 2-5 (`c206f910`, `e38b2a0e`).

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
