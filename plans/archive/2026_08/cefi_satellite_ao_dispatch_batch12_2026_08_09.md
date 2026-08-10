---
doc_type: plan
title: CeFi satellite AO batch 12 — item-level extraction from 19 non-qualifying NA docs (infrastructure_master group)
summary: >-
  Twelfth AO-dispatch batch for cefi, sibling of `cefi_satellite_ao_dispatch_batch11_2026_08_09.md` (same
  item-level-extraction run, same 19-doc candidate list — see that doc for the full methodology). This batch is the
  `parent_epic: infrastructure_master` group (3 items, 3 source docs). Item 1 (mdps dead-launcher deletion) was
  independently re-verified against the SOURCE doc's own round5-cefi-question-resolution (2026-08-08) Progress Log
  entry, which explicitly declassified it from `[OPERATOR]` per `task_template.md` finding U and stated "todos 1-3 are
  ready for dispatch the moment todo 8 is resolved or split out" — this batch performs exactly that split for todo 1
  only (todos 2/3 stayed behind on their own per-item merits, see batch11's sibling research pass and the Progress Log
  below). Item 3 (shard24 relaunch) resolves a same-day conflict flagged by that source doc's own round7 RECLASSIFY
  sweep (batch10's operator-gated characterization was stale, predating the doc's own round5 resolution of its blocking
  item).
status: complete
nature: process
asset_group: [cefi]
stage: [meta]
repos: [unified-trading-pm, deployment-service, strategy-service, market-tick-data-service, features-service]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-12, satellite-docs, item-level-extraction, na-audit]
related:
  [
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch11_2026_08_09.md,
    /plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md,
    /plans/active/aster_and_cefi_rolling_adv_feature_2026_07_21.md,
    /plans/archive/2026_08/issues/cefi_content_migration_shard24_early_preemption_false_page_2026_07_31.md,
    /plans/active/cefi_satellite_ao_dispatch_batch10_2026_08_08.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.9
estimate_calibrated_ai_days: 0.72
assigned_role: infra
effort: medium
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Item-level satellite-extraction pass 2026-08-09, sibling of batch11 (same run, same methodology — see that doc's
  frontmatter `source` field for the full research-pass description).
context_scope:
  [
    /plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch11_2026_08_09.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
---

# CeFi satellite AO batch 12 — item-level extraction (infrastructure_master group)

> **🟢 ARCHIVED 2026-08-09 — COMPLETE.** All 3 todos shipped/measured with real evidence (see Progress Log), reconciled
> against their 3 source docs (`issues/mdps_features_deadcode_consolidation_2026_07_20.md`,
> `aster_and_cefi_rolling_adv_feature_2026_07_21.md`,
> `issues/cefi_content_migration_shard24_early_preemption_false_page_2026_07_31.md`) and independently re-verified by
> finalize-plan todos 1-2. Archived per the 6-step ritual
> (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`); a codex staleness found in the process — 2
> refs to the now-deleted `launch-prediction-features-vm.sh` (todo 1, `deployment-service@4150c6c2`) — was corrected in
> `/codex/05-infrastructure/vm-launcher-runbook.md` + `/codex/05-infrastructure/vm-tarball-deployment.md`. Finalize plan
> `cefi_satellite_ao_dispatch_batch12_2026_08_09_finalize.md` (source-doc reconciliation + this archival) completed and
> archived alongside this doc. No new deferred item migrated — the two forward-pointers in this doc's own Progress Log
> (the `features-cross-instrument-service` cleanup, the S1-b citation-reconciliation) were already real tracked `- [ ]`
> todos in their source docs. Successor: none.
>
> **Status: ACTIVE (historical).** Conflict-checked 2026-08-09 — see Progress Log for the per-todo verification (each
> todo's target file/mechanism grepped against the full active-plan corpus; the one genuine near-miss, a sibling doc
> `ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md` referencing the SAME "pending
> operator A/B/C" framing for todo 1's target, was confirmed stale — it predates the 2026-08-08 round5 declassification
> and names a DIFFERENT pair of launchers, not this todo's target). **Cross-todo file-collision check**: todo 1 edits
> `deployment-service/scripts/vm/` +
> `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py`; todo 2 edits
> `strategy-service/strategy_service/allocation_sizer.py`; todo 3 launches a VM via
> `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` (no source edit unless the audit finds a bug). No
> file is edited by more than one todo.

## Todos

- [x] ✅ [SCRIPT] P2. **Delete `deployment-service/scripts/vm/launch-prediction-features-vm.sh`** (confirmed still
      broken as of 2026-08-09: packages the removed `features-cross-instrument-service` repo — no such checkout exists
      in the workspace — and the script's own import-verify step under `set -e` imports
      `features_cross_instrument_service.cli.main`, guaranteeing `ModuleNotFoundError` on every run; also lacks
      `--provisioning-model=SPOT`, uses a 50GB boot disk that escapes the disk QG, and has no live-collision guard) and
      repoint `launcher_registry.py`'s `"prediction-features-"` self-heal binding (currently line 191) from
      `launch-prediction-features-vm.sh` to
      `launch-features-vm.sh --feature-family cross_instrument --asset-group     PREDICTION` (confirmed live/working:
      `launch-features-vm.sh` supports `--provisioning-model=SPOT` and both `cross_instrument`/`PREDICTION` are valid
      enum values per its own usage text). **Safe-idempotent, no `[OPERATOR]` tag needed**: the current launcher cannot
      succeed under any input today, so deleting it and repointing self-heal to a working launcher strictly reduces
      blast radius — the source doc's own round5-cefi-question-resolution (2026-08-08) already applied
      `task_template.md` finding U's positive test and declassified this exact item from `[OPERATOR]`. Repo:
      deployment-service. Source: `issues/mdps_features_deadcode_consolidation_2026_07_20.md` todo 1 (S1-a, line 87).
      **Done when**: `launch-prediction-features-vm.sh` no longer exists in the repo, `launcher_registry.py`'s
      `"prediction-features-"` key maps to `launch-features-vm.sh` with the stated flags, `quality-gates.sh` is green,
      and a grep for `features-cross-instrument-service` under `deployment-service/scripts/vm/` returns zero hits.
      **DONE** — `deployment-service@4150c6c2`. `launch-prediction-features-vm.sh` deleted; the registry's
      `"prediction-features-": "launch-features-vm.sh"` row carries a comment documenting the
      `--feature-family cross_instrument --asset-group PREDICTION` invocation (the registry's value type is a bare
      `launch-*.sh` filename only — every other multi-flag entry, e.g. the sibling `"features-"` row, follows the same
      documented-comment convention, not literal embedded flags — confirmed via `tests/unit/test_launcher_registry.py`
      lines 76-81, which asserts every non-None value `.startswith("launch-") and .endswith(".sh")`).
      `test_launcher_registry.py` (9/9) + full `quality-gates.sh` both green on the shipped SHA. The done_definition's
      "zero hits" grep is scoped to this script's own references — `features-cross-instrument-service` still appears in
      2 pre-existing, separately-tracked files (`launch-prediction-pipeline-vm.sh`, `backfill-cluster.sh`; see
      `issues/ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md`), out of this todo's
      stated single-file scope (Repo: deployment-service, S1-a only).
- [x] ✅ [BACKEND] P2. **Implement the 10%-of-ADV position-size cap at order-sizing time** (per the 2026-08-08 operator
      ruling — see `aster_and_cefi_rolling_adv_feature_2026_07_21.md` Phase 3): in
      `strategy-service/strategy_service/allocation_sizer.py`, clamp `AllocationSizer.size_signal()`'s
      `PerClientSignal.allocation_amount_usd` to `min(computed_size, 0.10 * adv_usd)`, using
      `RollingAdvReader.compute_rolling_adv()`
      (`features-service/features_service/cross_instrument/app/calculators/adv.py`, `features-service@8608ea5d`) for
      `adv_usd`. Fail closed (not tradeable) when `AdvStatus` is `INSUFFICIENT_HISTORY` or `NO_DATA`. Repo:
      strategy-service. Source: `aster_and_cefi_rolling_adv_feature_2026_07_21.md` Phase 3 (line 215). **Done when**:
      `AllocationSizer.size_signal()` enforces the clamp + fail-closed behavior, covered by unit tests,
      `quality-gates.sh` green. — `strategy-service@73aa792f`: implemented via a T4-local
      `strategy_service/engine/core/rolling_adv_reader.py` rather than importing features-service's `adv.py` directly —
      cross-service imports are banned by `/codex/04-architecture/tier-and-import-architecture.md` (T4 services have no
      service-to-service import path), and this repo already has the identical precedent
      (`canonical_adv_ranked_universe_provider.py`) solving the same features-service-adv-can't-be-imported problem by
      mirroring the calculator's verified-correct logic locally instead. Clamp + fail-closed (missing instrument
      context, `INSUFFICIENT_HISTORY`, `NO_DATA`) covered by 8 new/updated unit tests; `quality-gates.sh` green
      (sentinel-verified, sha=73aa792fb5a68429f08783b2e69910376f20e6fb).
- [x] ✅ [SCRIPT] P3. **Check canonical-migration-cefi-content-24's current manifest `capture_status` and `vm-logs/` GCS
      prefix for any launch since `-065001` (2026-07-31)**; if shard 24 is still incomplete and hasn't already been
      relaunched by another agent, launch its checkpoint-resumed 3rd attempt:
      `launch-canonical-migration-vm.sh cefi-content-apply 2026-01-07 2026-01-15 full` (the exact window `-065001` was
      using). **Conflict-checked 2026-08-09**: shard 24 is NOT among the 8 shards (16,17,18,19,21,23,41,42) tracked by
      the still-active `cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed_2026_07_31.md` round8
      launch — it split off into its own dedicated escalation doc (this source doc) precisely because of its distinct
      false-positive-preemption complication, so no double-claim on the relaunch action itself. The source doc's own
      item 1 (deployment-api redeploy gate) was independently live-verified RESOLVED 2026-08-08 (`deployment-api`
      rebuilt repeatedly since the fix commit, Cloud Run resolves `:latest` fresh per execution) —
      `cefi_satellite_ao_dispatch_batch10_2026_08_08.md`'s "item 1 is `[OPERATOR]`-tagged" characterization predates or
      is otherwise inconsistent with this later resolution; that doc's own round7 RECLASSIFY sweep flagged this exact
      inconsistency and deferred reconciling it to "the next pass" — this todo IS that reconciliation. Repos:
      deployment-service (launch), market-tick-data-service (verify). Source:
      `issues/cefi_content_migration_shard24_early_preemption_false_page_2026_07_31.md` (line 169, § "Recommended
      decision" item 2). **Done when**: shard 24's `canonical-migration-cefi-content-24-*` vm-logs show a completed or
      actively-progressing 3rd-attempt run (`PROGRESS.json` advancing past `last_completed_date=2026-01-07`), OR the
      check confirms shard 24 already completed via another path, in which case the todo closes as verified-complete
      with no relaunch needed. — **CLOSED 2026-08-09 (slot-8, infra) per the todo's own precondition, not the done-when
      disjunction**: the checkpoint-resumed 3rd attempt was ALREADY launched by another agent before this check
      (`canonical-migration-cefi-content-24-relaunch20260731-133746`, inserted 13:37Z,
      `RESUME_START_DATE=2026-01-06     RESUME_END_DATE=2026-01-15`) — so "hasn't already been relaunched by another
      agent" is false and no launch was due from this todo. That 3rd attempt itself did NOT reach either done-when
      disjunct (not complete, not actively progressing — it wedged at 33,800/108,441 files, `last_completed_date` frozen
      at `2026-01-07`, VM self-deleted 2026-07-31 with no clean exit marker) — full evidence + the
      correctly-checkpointed 4th-attempt follow-up filed at
      `issues/cefi_content_migration_shard24_recurring_wedge_needs_diagnosis_2026_08_09.md`.

## Codex SSOTs

- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the shared conflict-check protocol.
- `/codex/05-infrastructure/vm-launcher-runbook.md` — SPOT-default, verify-started/progress/terminal-state pattern
  applied to todo 3.
- `/plans/active/task_template.md` §3 finding U — the `[OPERATOR]`-tag positive test applied to todo 1.

## Progress Log

- **2026-08-09** — drafted from the same 4-agent item-level classification pass as batch11 (see that doc's Progress Log
  for the full methodology). This doc carries the 3 extractable items whose source doc's
  `parent_epic: infrastructure_master`. All 3 confirmed as literal open checkboxes at drafting time:
  `issues/mdps_features_deadcode_consolidation_2026_07_20.md` line 87 (todo 1 of that doc, item 1 above),
  `aster_and_cefi_rolling_adv_feature_2026_07_21.md` line 215 (Phase 3, item 2 above),
  `issues/cefi_content_migration_shard24_early_preemption_false_page_2026_07_31.md` line 169 (item 3 above). **Item 1
  additional verification**: read `issues/mdps_features_deadcode_consolidation_2026_07_20.md` in full — confirmed its
  "Big findings" annotation (added round5-cefi-question-resolution 2026-08-08) explicitly declassifies todos 1-3
  (S1-a/b/c) from `[OPERATOR]`, and its round7 RECLASSIFY sweep entry explicitly states "todos 1-3 are ready for
  dispatch... that split is not performed here" — this batch performs that split for S1-a (item 1) only; S1-b (that
  doc's todo 2) stays behind because real successor work has landed toward "finish it" rather than "delete it" (2
  archived successor docs show a working dispatcher branch + fixed dependency-install already shipped, contradicting the
  stale delete-framing); S1-c (that doc's todo 3) stays behind because it's already fixed
  (`deployment-service@c79f984c`, confirmed via direct code read of `launcher_registry.py:153` +
  `vm_prefix_registry.py:364`) — its checkbox is simply stale, a doc-hygiene fix not new AO work, left for batch12's
  finalize twin or a future hygiene pass, not drafted as a todo here. **Item 1 also cross-checked against
  `issues/ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md`**, which references "the
  same A/B/C decision already pending for S1-a" — confirmed this reference predates the 2026-08-08 declassification
  (that doc was filed 2026-08-04) and its own content targets two DIFFERENT launchers (`launch-ml-training-vm.sh`,
  `launch-prediction-pipeline-vm.sh`), not this todo's target — no real conflict, just a stale cross-reference in a
  sibling doc (flagging for whoever next touches that doc, out of scope here). **Item 3 additional verification**: read
  `issues/cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed_2026_07_31.md` directly, confirmed its
  round8 launch list (16,17,18,19,21,23,41,42) does not include shard 24 — no double-claim.
- **2026-08-09** — item 2 (the 10%-of-ADV position-size cap) shipped, `strategy-service@73aa792f`. **Deviation from the
  todo's literal wording**: the todo names `features-service/features_service/cross_instrument/app/calculators/adv.py`
  as the `RollingAdvReader` source, but strategy-service and features-service are both T4 services with NO
  service-to-service import path (`/codex/04-architecture/tier-and-import-architecture.md`) — importing it directly
  would violate that HARD RULE (and doesn't even resolve: features-service isn't a declared strategy-service
  dependency). This repo already carries the identical precedent for this exact problem —
  `strategy_service/engine/core/canonical_adv_ranked_universe_provider.py`'s docstring documents building a T4-local
  reader instead of importing `adv.py`, for the same reason. Implemented the same way: a new
  `strategy_service/engine/core/rolling_adv_reader.py` mirrors `adv.py`'s verified-correct (2026-07-29-fixed) logic
  locally, with one intentional correction carried over from `canonical_adv_ranked_universe_provider.py`'s own finding —
  defaults `data_type="trades"` instead of `adv.py`'s own `"derivative_ticker"` default, since real CeFi
  `derivative_ticker` candles carry hardcoded-zero volume (verified against prod GCS by that sibling module, not
  re-verified here). Intent (10%-of-ADV clamp + fail-closed on `INSUFFICIENT_HISTORY`/`NO_DATA`) matches the todo
  exactly; only the low-level "which file provides `RollingAdvReader`" detail changed.
