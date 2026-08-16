---
doc_type: issue
title:
  "ml-service predictions + strategy-service strategy_instructions have ZERO manifest coverage in prod — real
  strategy_instructions objects genuinely orphaned"
summary: >-
  First real-GCS-data run of ml_orphan_sweep.py + strategy_orphan_sweep.py (todo 3b of
  mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md), executed via 2 Tier-2 SPOT VMs. Both corpora's
  availability manifests are completely absent in prod (`_index/availability_index.parquet` not found in either bucket,
  0 captured cells) — not a sweep-tool bug, confirmed via a real `gcloud storage ls` of both buckets. ml-service
  `ml_predictions`: 0 real prediction objects exist yet (0/0/0/0 across A/D/E, F_other_corpus=236 for the real
  ml_models/ml_training_artifacts objects sharing the bucket) — genuinely unused so far, not a gap. strategy-service
  `strategy_instructions`: 7 REAL objects exist in prod with zero manifest coverage — all 7 classify E_orphan_real
  (there is no manifest row to compare against). The real objects also confirmed the `client_id=` path segment the
  todo-3b PATH_REGISTRY fix added is genuinely present in prod paths, though populated EMPTY for all 7
  (`client_id=/strategy_id=.../day=.../instructions.parquet`).
status: resolved
nature: issue
asset_group: [defi, cefi]
stage: [data]
repos: [ml-service, strategy-service, unified-trading-pm]
scope: [engineer, admin]
tags: [data-correctness, ml, strategy, manifest-completeness, orphan-real, honest-absence, big-finding]
related:
  [
    /plans/archive/issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md,
    /plans/archive/2026_08/issues/features_service_manifest_coverage_gap_2026_08_03.md,
    /codex/02-data/orphan-object-detection.md,
  ]
created: "2026-08-03"
author: unknown
last_updated: "2026-08-03"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.7
assigned_role: data_engineering
drift_direction: advance-code
source: >-
  Surfaced 2026-08-03 (slot 3) running the first real-GCS-data validation of ml_orphan_sweep.py (ml-service@b6c87d0c) +
  strategy_orphan_sweep.py (strategy-service@a353a570) via 2 real Tier-2 SPOT VMs, launched through the new
  launch-ml-strategy-orphan-sweep-vm.sh (deployment-service@fb29a8d).
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /codex/02-data/orphan-object-detection.md,
    ml-service/ml_service/inference/cli/main.py,
    strategy-service/scripts/backfill_strategy_instructions_orphan_class_e.py,
    strategy-service/scripts/strategy_orphan_sweep.py,
  ]
depends_on: []
---

> **🟢 ARCHIVED 2026-08-06** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. All 4 todos [x]: the 7 strategy_instructions orphans backfilled + verified (recorded_cells=7,
> record_errors=0, per-VM shard direct read), ml_predictions confirmed intentionally unwired (discarded
> prediction_writer), sample_verify fix shipped (strategy-service@1c20712b) — context-scout 2026-08-06 confirms 'All 4
> todos are now closed.'. Moved by the 2026-08-06 AO issue-doc archive sweep.

# ml_predictions + strategy_instructions manifest coverage gap

## What I found

Ran the newly-wired `ml_orphan_sweep.py` / `strategy_orphan_sweep.py` on real prod data via 2 Tier-2 SPOT VMs
(`ml-orph-*` / `strat-orph-*`, `e2-standard-4`, both completed in under 2 minutes, no preemption). Real, measured
results:

| corpus                | bucket                                    | manifest cells | A   | C   | D   | E (orphan_real) | F (other-corpus) |
| --------------------- | ----------------------------------------- | -------------- | --- | --- | --- | --------------- | ---------------- |
| ml_predictions        | ml-store-prd-central-element-323112       | 0 (absent)     | 0   | 2   | 0   | 0               | 236              |
| strategy_instructions | strategy-store-prd-central-element-323112 | 0 (absent)     | 0   | 0   | 0   | 7               | n/a              |

1. **Neither bucket has an `_index/availability_index.parquet` at all** — confirmed via the sweep's own manifest-load
   warning (`no _index/availability_index.parquet in <bucket>`) AND independently via
   `gcloud storage ls gs://ml-store-prd-central-element-323112/_index/` (empty) and the equivalent for strategy-store.
   This is a genuine absence, not a sweep-tool bucket-resolution bug (the same pattern that caught todo 1's real sports
   bucket bug would have caught this too — both buckets resolved correctly and returned real listings).
2. **`ml_predictions` has ZERO real prediction objects in prod today** (A=0, D=0, E=0). The 236 `F_other_corpus` objects
   are real `ml_models`/`ml_training_artifacts` data sharing the bucket (see the sibling
   `mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md` todo-3b fix — this sweep run is what surfaced and
   fixed the sibling-corpus misclassification bug in the same dispatch). This reads as **genuinely unused, not a gap** —
   `ml-service/ml_service/inference/cli/main.py`'s `MLInferenceBatchModeHandler.run()` constructs a `prediction_writer`
   and then discards it (`_ = prediction_writer`) rather than wiring it into the actual inference flow, consistent with
   zero real writes ever having happened.
3. **`strategy_instructions` has 7 REAL objects in prod with zero manifest coverage** — all classify `E_orphan_real` (no
   manifest row exists to compare against, since the manifest itself is absent). Real object paths (from the run log):
   - `strategy_instructions/client_id=/strategy_id=DEFI_ETH_BASIS_MULTI_HUF_1H_V1/day=2025-06-15/instructions.parquet`
   - `strategy_instructions/client_id=/strategy_id=DEFI_ETH_BASIS_MULTI_HUF_1H_V1/day=2025-06-16/instructions.parquet`
   - `strategy_instructions/client_id=/strategy_id=DEFI_ETH_RECURSIVE_HEDGED_ALL_HYPERLIQUID_HUF_1H/day=2025-06-15/instructions.parquet`
   - `strategy_instructions/client_id=/strategy_id=DEFI_ETH_STAKED_BASIS_HYPERLIQUID_SCE_1H/day=2025-06-15/instructions.parquet`
   - `strategy_instructions/client_id=/strategy_id=DEFI_ETH_STAKED_BASIS_HYPERLIQUID_SCE_1H/day=2025-06-16/instructions.parquet`
   - `strategy_instructions/client_id=/strategy_id=DEFI_ETH_YLD_AAVE_USDC_HUF_1H_V1/day=2025-06-15/instructions.parquet`
   - `strategy_instructions/client_id=/strategy_id=DEFI_ETH_YLD_AAVE_USDC_HUF_1H_V1/day=2025-06-16/instructions.parquet`

   These are real strategy backtest/paper artifacts from 2025-06-15/16 — genuinely captured by
   `gcs_storage_service.py::write_instructions` at some point, but never registered via `strategy_manifest.py`'s
   `StrategyManifestRecorder`. Confirms the todo-3b PATH_REGISTRY fix's `client_id=` segment is real (the sweep's
   grain-tolerant `is_covered()` blank-`client_id`-as-wildcard match — already built for exactly this case — worked
   correctly against real data), just populated EMPTY for these particular 7 objects (an early/pre-multi-client-era
   write, plausibly).

## Why this is a big finding, not backfill-in-this-session scope

Per this repo's data-pipeline-correctness HARD RULE, an absent manifest for a corpus with real backing data is a
correctness gap (not an operational choice) — `strategy_instructions` objects exist that no downstream consumer using
the manifest (completion-checking, coverage reporting) can see. But root-causing WHY the manifest was never populated (a
`StrategyManifestRecorder` wiring gap? an env/bucket mismatch between the writer and where `record_captured` calls
landed?) is a genuine investigation, not a mechanical fix — exactly the class of judgment call this doc's own "Why this
needs a split" section (parent issue) argues should be its own todo, not folded into "validate the tool" scope.

## Todo 1 investigation findings (2026-08-03)

**Answer: wired in, DOES fire on every real write, but the exception it raises on failure is silently swallowed.** This
is an ACTIVE ongoing gap, not a pre-instrumentation historical artifact.

1. **Two write call sites for `strategy_instructions`, both confirmed via grep of every `.py` file in `strategy-service`
   (prod + tests):**
   - `strategy_service/engine/core/gcs_storage_service.py::CloudStorageService.write_instructions` — correctly wraps the
     GCS write in a `StrategyManifestRecorder` context manager (`record_captured`/`record_empty`/`record_failed`). But
     it has **zero callers anywhere in the current tree** (confirmed:
     `grep -rn "\.write_instructions(" --include="*.py" .` excluding tests returns nothing, and the tests dir has none
     either) — it is dead code, not the production path.
   - `strategy_service/cli/handlers/batch_results.py::write_instructions_to_gcs` — the ACTUAL live call site, invoked
     from `batch_handler.py::_generate_and_write_signals` (line 672), itself part of the continuous batch=live
     signal-generation flow ("Always write instructions — even empty. This is the heartbeat from strategy to
     execution."). This function DOES call `ManifestWriter.record_captured()` + `.write()` on every real write.
2. **Root cause**: `write_instructions_to_gcs` wraps the entire manifest-recording block in a blanket
   `except Exception: logger.warning(...)` (pre-fix). The GCS parquet write happens BEFORE this block and always
   succeeds regardless — so any exception inside `record_captured()`/`.write()` is silently absorbed into one
   WARNING-level log line with no traceback, no `gs://` path, no alert, no retry. A real object lands in prod while its
   manifest row silently never exists.
3. **Confirmed ACTIVE, not historical**: pulled real GCS object metadata (`gcloud storage objects describe`) for all 7
   orphaned objects — all 7 share the exact same creation window, **2026-07-18T15:35:27Z – 15:35:28Z** (one batch run).
   That is ~2 months AFTER manifest emission first landed for this writer (`cd617891`, 2026-05-20) and ~2 weeks before
   this investigation (2026-08-03) — this rules out the "early/pre-multi-client-era write, before instrumentation
   existed" hypothesis floated above. The gap is live.
4. **Walked every documented raise-point inside `ManifestWriter.record_captured()`** (unified-trading-library) against
   this exact call shape (`asset_group=<category>`, `instrument_type=""`, `data_type="strategy_instructions"`, no
   `venue`, no `feature_group`, not a bundled data_type) and ruled out each as the cause: the `feature_family` sibling
   gate (N/A, no `feature_group`), the source-required gate (N/A — `source_required()` is only True for >1-external-
   source cells, and `strategy_instructions` is computed/service-emitted), the cluster-coverage gate (N/A, not in
   `BUNDLED_DATA_TYPES`), the `available_at` presence gate (satisfied — the caller's `manifest_df` always populates it),
   the write-time canonical-path assert (a no-op for any row with a blank `venue`, per `_resolve_candidate_write_path`),
   and `_resolve_asset_group` (exempt/no-raise for venue-less rows). None of the _known_ validation gates explain a
   raise for this shape, which points at either a real GCS I/O failure in `writer.write()`'s manifest-index upload
   (permissions / transient network / concurrent-write conflict) or `MANIFEST_STRICT_SCHEMA_VALIDATION=true` if set in
   this deployment's env (not the default). Attempted to pull the exact swallowed warning from Cloud Logging for the
   2026-07-18T15:35Z window; the queries returned no matches / timed out inside this todo's time budget — pinpointing
   the literal exception text is a good next step but wasn't required to answer this todo's core question.
5. **Fix shipped this todo (mechanical, in-scope)**: hardened `write_instructions_to_gcs`'s except block from
   `logger.warning(str(e))` to `logger.exception(...)` with the `gs://` path included, so the NEXT occurrence of this
   failure is diagnosable (full traceback + correlatable path, ERROR severity) instead of repeating an unattributable
   silent gap. Deliberately kept non-blocking (does not re-raise) — the actual instructions write must still land even
   if manifest recording fails, per the function's own "heartbeat" design intent; only the _visibility_ of the failure
   changed.

## Todo 2 investigation findings (2026-08-03)

**The row shape this todo's own wording assumed (`capture_status="captured"`) is WRONG — footer-verified all 7 real
objects and every one is a genuine 0-row write, not a row_count>0 capture.**

1. Downloaded all 7 real objects (`gcloud storage cp` + `pyarrow.parquet.ParquetFile.metadata.num_rows`, each ~135
   bytes) — every single one reads `rows=0`. This matches `batch_results.py::write_instructions_to_gcs`'s own documented
   design intent ("Always write instructions — even empty. This is the heartbeat from strategy to execution") — these
   are hold-day signals (the strategy ran and chose not to trade), not junk and not real row_count>0 captures.
2. `StrategyManifestRecorder.record_captured` (the correctly-wired-but-zero-caller dead-code path) already encodes the
   correct terminal state for this: it routes `row_count<=0` straight to `record_empty`, never `record_captured`.
   Stamping `capture_status="captured"` here would itself be a silent-placeholder / dishonest-absence violation
   (data_engineering.md craft north-star #1) — so the honest backfill target is `record_empty`
   (`capture_status="empty_confirmed"`), not what this todo originally asked for.
3. **Blocker**: `record_empty(reason=SOURCE_RETURNED_ZERO)` — the closest-named existing `EmptyConfirmedReason` — is
   semantically wrong here. Its own docstring + the writer's Phase-1-KEYSTONE gate
   (`FetchEvidence.proves_honest_absence()`, REQUIRED for this reason or the writer HARD-RAISES
   `UnprovenHonestAbsenceError`) are explicitly HTTP-fetch-shaped ("Threaded from the adapter HTTP layer" —
   `http_status`/`source`-vendor-token/`endpoint`-URL fields). `strategy_instructions` has no upstream fetch at all —
   "the strategy engine IS the source" (`strategy_manifest.py`'s own comment) — so constructing a synthetic
   `FetchEvidence` to satisfy the gate would itself be fabricated evidence, not a fix. No other closed-set
   `EmptyConfirmedReason` member fits "an internal computation legitimately produced zero rows" either — every
   `EXPECTED_*` member is a calendar/coverage-window primitive (holiday, pre-launch, TVL-floor, etc.), none of which
   describe a strategy engine's own hold-day decision.
4. Adding a new `EmptyConfirmedReason` taxonomy member is the semantically correct fix, but per its own governance
   ("Adding a new code = adding it here AND to `/codex/02-data/honest-absence-downstream-handling.md` AND to the
   per-service consumer-class audit table") it's a real closed-set design decision requiring a `unified-api-contracts`
   change — outside this todo's declared repos (`ml-service`, `strategy-service`, `unified-trading-pm`) and exactly the
   kind of judgment call `task_template.md`'s dispatch-scope-eligibility rule reserves for a human decision, not a
   mechanical worker.
5. **Companion fix shipped this todo** (in scope, correct regardless of the reason-code decision):
   `strategy_orphan_sweep.py`'s `build_covered_index()` only recognised `capture_status=="captured"` as coverage — an
   honest `empty_confirmed` backfill would therefore NEVER have converged `orphan_class_E` to 0 on re-sweep, directly
   defeating this todo's purpose. Widened to treat `{"captured", "empty_confirmed"}` as covered (a cell the manifest
   system has terminal knowledge of, either shape) + added a locking unit test.
6. **Backfill tool shipped this todo, functional but not yet applied**:
   `backfill_strategy_instructions_orphan_class_e.py` — footer-reverifies each of the 7 known cells is still genuinely
   0-row, re-checks the LIVE manifest index (never double-records), calls
   `ManifestWriter.record_empty(reason=<operator-supplied>)`, sample-verifies its own per-VM shard post-write. Requires
   an explicit `--reason` (refuses `SOURCE_RETURNED_ZERO` and any non-closed-set value) — proven end-to-end in
   `--dry-run` against real prod GCS (all 7 cells still genuinely 0-row, none yet covered). 9 new unit tests (all
   passing). The actual `--apply` run is deferred pending the operator's reason-code decision (posted as a `/blocked`
   question).

## Open work

- [x] 1. ✅ [SCRIPT] P2. **Investigate why `strategy_instructions` has zero manifest rows in prod** — grep
      `StrategyManifestRecorder`/`record_captured` call sites in `strategy-service`, confirm whether they're wired into
      the live paper/backtest write path at all, or exist but never fire (env mismatch, exception swallowed, etc.).
      Repo: strategy-service. — strategy-service@788dfa08 (see "Todo 1 investigation findings" above).
- [x] 2. ✅ [OPERATOR] P2. **Decide the `EmptyConfirmedReason` for the 7 real `strategy_instructions` orphans, then run
      the backfill.** Operator ruling on BLK-4a063e0f: option A (new taxonomy member). Added
      `EmptyConfirmedReason.STRATEGY_ENGINE_RETURNED_ZERO` — `unified-api-contracts@06dee218`. Exhaustive-consumer audit
      found + fixed 2 real hand-maintained-mirror drift risks — `deployment-api@e922a72b`, `deployment-ui@01cb9b6c`
      (also backfilled 2 unrelated pre-existing gaps found during the audit). Ran
      `backfill_strategy_instructions_orphan_class_e.py --apply --reason STRATEGY_ENGINE_RETURNED_ZERO`
      (strategy-service@faddf680) for real: **recorded_cells=7, record_errors=0**. Independently verified by downloading
      the per-VM shard parquet directly
      (`gs://strategy-store-prd-central-element-323112/_index/per_vm/     local-2848562-4fb7.parquet`) and reading its
      content — all 7 rows carry `capture_status=empty_confirmed`/`error_reason=STRATEGY_ENGINE_RETURNED_ZERO` for the
      exact 7 known cells. The manifest consolidator merge into the canonical index is async (not yet observed at time
      of writing) — the per-VM-shard direct read is the authoritative proof of the write per the tool's own design (does
      not wait on the consolidator). Done.
- [x] 3. ✅ [DOC] P3. **Confirm `ml_predictions` is genuinely intentionally unwired** (not a silently-broken feature) —
      check with the operator or a design doc whether ml-service inference was ever meant to persist predictions in prod
      yet, or if `MLInferenceBatchModeHandler`'s discarded `prediction_writer` is itself a gap worth its own todo. If
      genuinely not-yet-built, no action needed beyond this note. Repo: ml-service.
- [x] 4. ✅ [SCRIPT] P3. **Fix `backfill_strategy_instructions_orphan_class_e.py`'s `sample_verify` step — it checks the
      wrong per-VM shard filename.** — strategy-service@1c20712b `main()` re-instantiates a fresh `ManifestWriter()` to
      resolve `_per_vm_path` for the post-write verify read, but each `ManifestWriter()` instantiation picks a NEW
      random per-VM shard name — so the verify step reads a file that was never written (`does not exist after close()`)
      even when the actual write (via the `record_cells()`-owned writer instance) succeeded. Confirmed live during the
      real `--apply` run for todo 2: `recorded_cells=7 record_errors=0` but `verify_failed=1` — the write itself was
      independently confirmed correct via a direct GCS read (see todo 2's evidence above), so this is a verify-step bug,
      not a data bug. Fix: have `record_cells()` return the writer's own `_per_vm_path` (captured before `.close()`)
      instead of the caller re-resolving a second instance's path — `main()` should thread that value into
      `sample_verify()` directly. (A fix was drafted + QG-green this session but reverted uncommitted when this dispatch
      was cancelled mid-turn by an unrelated backlog-regen artifact — this todo re-derives it fresh rather than assuming
      stale context.) Repo: strategy-service.

## Progress Log

- **2026-08-03** (AO dispatch, slot 3) — Filed after running the real-GCS-data validation VMs for todo 3b of
  `mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md`. Both sweeps ran cleanly against real prod buckets
  (correct bucket resolution, no crashes); the manifest-absence + real-orphan findings above are genuine data gaps this
  validation run surfaced, out of that todo's own "validate the tool" scope.
- **2026-08-03** (AO dispatch, slot 16) — Todo 1 done. Confirmed via grep + code read that the live write path
  (`batch_handler.py` → `batch_results.py::write_instructions_to_gcs`) DOES call `ManifestWriter.record_captured()` on
  every real write, but the call was wrapped in a blanket `except Exception: logger.warning(str(e))` — silently
  swallowing whatever raised, with no traceback. Confirmed via `gcloud storage objects describe` on all 7 orphan objects
  that they were written in one batch run at 2026-07-18T15:35:27Z-15:35:28Z — ~2 months after manifest emission first
  landed (2026-05-20) — so this is an ACTIVE ongoing silent-failure bug, not a pre-instrumentation historical gap as
  speculated above. Walked every documented raise-point inside `ManifestWriter.record_captured()` against this call's
  exact shape and ruled out all of them (feature_family/source-required/cluster-coverage/
  available_at/canonical-path/asset_group-resolution gates all no-op or pass for this venue-less, non-bundled,
  single-source shape) — the actual exception is most likely a `writer.write()` GCS I/O failure, not caught by any Cloud
  Logging query I could get to return a match inside this todo's time budget. Shipped a minimal, non-blocking hardening
  fix (strategy-service@788dfa08): `logger.exception()` with the `gs://` path instead of a bare warning, so the next
  occurrence is diagnosable. `CloudStorageService.write_instructions` (the OTHER write site, with its own correct
  `StrategyManifestRecorder` wiring) has zero callers anywhere in the current tree — confirmed dead code, not the
  production path. Root-causing the exact swallowed exception (Cloud Logging archaeology) is a good next step but not
  required to answer this todo's question and is left for whoever picks up todo 2 (backfill).
- **2026-08-03** (AO dispatch, slot 2) — Started todo 2 (backfill). Footer-verified via `gcloud storage cp` +
  `pyarrow.parquet.ParquetFile.metadata.num_rows` that all 7 real orphan objects are genuine 0-row writes — the todo's
  own `capture_status="captured"` assumption was wrong (see "Todo 2 investigation findings" above). Built + unit-tested
  (9 new tests) + dry-run-proved against real prod GCS `backfill_strategy_instructions_orphan_class_e.py`, and widened
  `strategy_orphan_sweep.py`'s `build_covered_index()` to recognise `capture_status="empty_confirmed"` as coverage (else
  an honest backfill could never converge `orphan_class_E` to 0). Discovered `SOURCE_RETURNED_ZERO`'s `FetchEvidence`
  proof gate is HTTP-fetch-shaped and does not apply to strategy-service's internally-computed instructions, and no
  other closed-set `EmptyConfirmedReason` fits — retagged the todo `[OPERATOR]` and posted BLK-4a063e0f with 3 options
  (recommend A: add a new taxonomy member).
- **2026-08-03** (AO dispatch, slot 2) — Operator ruling on BLK-4a063e0f: option A. Added
  `EmptyConfirmedReason.STRATEGY_ENGINE_RETURNED_ZERO` (sibling of `SOURCE_RETURNED_ZERO`, exempt from the FetchEvidence
  gate) — `unified-api-contracts@06dee218`. Ran the operator-mandated exhaustive-consumer audit (an Explore sub-agent
  surveyed every repo for hand-maintained mirrors of the closed set) and found + fixed 2 real drift risks that would
  have silently misclassified the new reason as legacy `empty_unclassified`: `deployment-api@e922a72b`
  (`EMPTY_REASON_KEYS` tuple) and `deployment-ui@01cb9b6c` (`EMPTY_REASON_KEYS` + `EMPTY_REASON_META` + its pinned test
  snapshot — also backfilled 2 pre-existing gaps, `EXPECTED_ACQUISITION_PENDING`
  - `EXPECTED_SUBGRAPH_DEINDEXED`, found during the same audit but predating this change). Updated
    `/codex/02-data/honest-absence-downstream-handling.md`'s reason taxonomy + consumer-policy tables and
    `scripts/quality_gates/check_record_empty_reason_closed_set.py`'s `KNOWN_REASONS` (also backfilled the same 2
    pre-existing gaps there). Shipped `strategy-service@faddf680`: the backfill tool + sweep coverage fix (see prior
    entry), now runnable with `--reason STRATEGY_ENGINE_RETURNED_ZERO`. All 5 repos QG-green before shipping.
- **2026-08-03** (AO dispatch, slot 2) — Ran the real `--apply` backfill: `recorded_cells=7 record_errors=0`.
  Independently verified via a direct GCS read of the per-VM shard parquet (bypassing the async manifest consolidator) —
  all 7 cells correct. Todo 2 flipped done. While verifying, found + drafted a fix for a real bug in the backfill tool's
  own `sample_verify` step (checks a mismatched, never-written per-VM shard path — see new todo 4); QG-validated the fix
  but it landed uncommitted when this dispatch was cancelled mid-session by a backlog-regen artifact (my own rewrite of
  todo 2's checkbox text no longer line-matched the originally-dispatched task, so the server's next heartbeat reported
  `dispatch_reason: cancelled`) — reverted the uncommitted fix per worker.md protocol rather than ship further work
  under an invalidated task identity, and captured it as todo 4 instead of losing the diagnosis. **This todo's actual
  goal (backfill the 7 real orphans) is complete and verified**; todo 4 is the only loose end, and is a pure
  code-quality fix with no data-correctness impact (the write itself was already independently proven correct).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — todos 1-2 are done; swapped the archived
  parent-issue link for the two live source files the still-open todos 3-4 actually touch.
- **2026-08-05** (AO dispatch, slot 8, data_engineering) — Todo 3 done. Confirmed `ml_predictions` is genuinely
  intentionally unwired. Code evidence: `ml_service/inference/cli/main.py:327-339` —
  `prediction_writer = get_writer("ml_predictions", storage)` is constructed but then explicitly discarded via
  `_ = prediction_writer` (Python's standard throwaway-variable idiom). The `InferHandler.handle()` runs inference and
  returns results inline but never persists through the writer. Zero real `ml_predictions` objects exist in the prod
  bucket (confirmed by the 2026-08-03 Tier-2 SPOT VM sweep). The 236 `F_other_corpus` objects in the bucket are
  `ml_models`/`ml_training_artifacts` sharing the same bucket — unrelated to prediction persistence. The ML
  implementation design doc (`deployment-service/docs/ML_IMPLEMENTATION.md`) shows architectural intent for
  `ml-predictions-store/` as the prediction sink, but the code is deliberately not yet wired — this is a pre-production
  validation phase, not a silently-broken feature. No TODO/FIXME in code suggests accidental breakage. Verdict:
  genuinely not-yet-built — no action needed beyond this note. If/when ml-service graduates to persisting predictions,
  the `get_writer("ml_predictions", ...)` scaffold is already in place and just needs to be passed into the handler
  instead of discarded.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged. All 4 todos are now closed
  (0 open checkboxes) — a completion-candidate for a future archival pass, not this skill's scope.
