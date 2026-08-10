---
doc_type: plan
title: CeFi satellite AO batch 17 — Tardis-cap watchdog relaunch + unit test, ASTER book_snapshot_5 recurrence check
summary: >-
  Seventeenth AO-dispatch batch for cefi. Extracted from 2 docs found `orphaned_never_touched` + AO-eligible by the
  2026-08-10 `/ag-closeout-audit cefi` run's Phase 1 (both were `status: open`, never cited by any of the 20 discovered
  cefi covering docs). Item 1-2 close `tardis_concurrency_gate_hardening_2026_08_09.md`'s two remaining todos (relaunch
  the fleet watchdog so its new Tardis-cap self-check goes live; add regression coverage for the new code path). Item 3
  closes `cefi_aster_book_snapshot5_batch_stale_code_attempted_failed_burst_2026_08_09.md`'s standing recurrence-watch
  condition (a stale-tarball incident that had already self-resolved by the time it was filed, pending one future
  audit-pass check).
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [deployment-service]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-17, satellite-docs, tardis, zombie-watchdog, ag-closeout-audit]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch17_finalize_2026_08_10.md,
    /plans/archive/issues/tardis_concurrency_gate_hardening_2026_08_09.md,
    /plans/archive/2026_08/issues/cefi_aster_book_snapshot5_batch_stale_code_attempted_failed_burst_2026_08_09.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
effort: medium
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  `/ag-closeout-audit cefi` run 2026-08-10 (ag_closeout_auditor scheduled worker, slot 23, one-shot, `$TRANCHE=cefi`).
  Phase 0 pre-filter (`generate_ag_closeout_audit_candidates.py --tranche cefi`) narrowed 78 AG-primary candidates to 9
  never-cited; Phase 1 (Workflow, 7 agents over the non-trivially-multi-AG-tagged subset) confirmed these 2 as genuine,
  AO-eligible, cefi-exclusive orphans despite one carrying a `cross-cutting` co-tag.
context_scope:
  [
    /plans/archive/issues/tardis_concurrency_gate_hardening_2026_08_09.md,
    /plans/archive/2026_08/issues/cefi_aster_book_snapshot5_batch_stale_code_attempted_failed_burst_2026_08_09.md,
    /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
  ]
---

# CeFi satellite AO batch 17 — item-level extraction (2026-08-10 ag-closeout-audit)

> **Status: DRAFT — awaiting operator review before dispatch** (per `/ag-closeout-audit`'s autonomous-mode safety rail;
> CLAUDE.md "Plan destination — ASK BEFORE CREATING"). **Conflict-checked 2026-08-10**: grepped all 20 discovered cefi
> covering docs (consolidated closeout + batch9/10/13/16 + finalizes + 4surface/chain-drop/deribit-binance/track2/
> onchain-perp-allowlist docs) plus a corpus-wide grep for each source doc's basename, escalation id, and specific new
> code symbols (`_is_tardis_consumer`, `_enforce_tardis_cap`, `vm-zombie-watchdog-20260807-075242`, `agt-e488d1`,
> `DP-FETCH-009`) — zero genuine overlap found. One archived doc (`infra_vm_zombie_watchdog_relaunch_2026_08_07.md`)
> relaunched the same watchdog VM but for an unrelated, already-shipped 2026-08-07 fix, predating and disjoint from this
> batch's Tardis-cap code (landed 2026-08-09). **Cross-todo file-collision check**: todo 1 is a VM ops action (no repo
> file); todo 2 edits `deployment-service/tests/unit/test_vm_zombie_watchdog.py`; todo 3 is a read-only manifest query
> with no repo file touch. No overlap — safe to run concurrently.

## Todos

- [x] ✅ [OPS] P1. **Relaunch the `vm-zombie-watchdog-20260807-075242` fleet daemon** (kill the running instance, then
      `bash launch-vm-zombie-watchdog.sh`) so the already-shipped `_enforce_tardis_cap` post-launch self-check
      (`deployment-service@58af2ab1303e4d91093f4f5371fc2d9c4667622f`) actually goes live — the running instance does not
      re-fetch its script mid-loop, so the code change is merged but not yet enforced. Repo: deployment-service. Source:
      `issues/tardis_concurrency_gate_hardening_2026_08_09.md` todo 1 (line 180). **Done when**: the new instance is
      confirmed `RUNNING` (`gcloud compute instances describe`) and its log shows the dry-run self-check line
      ("Tardis-cap self-check: N Tardis-consuming VM(s) found, cap=1, 0 excess") within one 5-min cycle of relaunch;
      flip the source doc's todo 1 checkbox citing the relaunch timestamp + confirmed log line. — **DONE 2026-08-10
      (`deployment-service@3d545372`, VM `vm-zombie-watchdog-20260810-124145` relaunched 12:41:45Z)**: self-check line
      `Tardis-cap self-check: 1 Tardis-consuming VM(s) found, cap=1, 0 excess` logged 12:51:45Z (first sweep, within one
      5-min cycle). Source doc todo 1 flipped. **Finding + fix folded in**: two pre-existing watchdog crashes aborted
      every prior sweep before pass 3 — `_persist_zombie_alert` except missed `GoogleAPIError` (Forbidden on
      `unified-trading-cicd-events`; `uts-prd-sa` lacked `storage.objectCreator`) and `_vm_age_minutes` had no 404
      tolerance. Fixed in `deployment-service@3d545372` (except→`Exception`, skip+log on per-VM eval failure) + IAM
      grant to `uts-prd-sa`; QG green; verified the relaunched watchdog's first sweep runs pass 1→2→3 cleanly.
- [x] ✅ [SCRIPT] P3. **Add a focused unit test for `_is_tardis_consumer`/`_enforce_tardis_cap`** in
      `deployment-service/tests/unit/test_vm_zombie_watchdog.py`, using the fixtures already present in that file
      (`_FakeComputeClient`/`_FakeComputeInstance`), covering: (a) name-pattern match, (b) metadata-stamp match, (c)
      neither (correctly not counted), (d) a 3-VM-over-cap-1 scenario asserting the 2 newest are killed and the oldest
      is kept. Repo: deployment-service. Source: `issues/tardis_concurrency_gate_hardening_2026_08_09.md` todo 2 (line
      184). — **DONE 2026-08-10 (`deployment-service@0c14f54050`)**: 21 new tests (13 `_is_tardis_consumer` + 8
      `_enforce_tardis_cap`), QG green (3282 passed), quickmerge landed.
- [x] ✅ [DATA] P3. **ASTER/book_snapshot_5 stale-tarball recurrence check.** Query the cefi manifest
      (`read_availability_index_safe`, bucket `market-data-tick-cefi-prd-central-element-323112`,
      `filters=[data_type=book_snapshot_5, venue=ASTER, capture_status=attempted_failed, error_reason=UpstreamTimestampBiasError]`)
      for any row with `attempted_at` strictly newer than `2026-08-09T01:24:28.273974+00:00` (the doc's own
      microsecond-precision cutoff — do not truncate to seconds, a prior same-day check over-matched on a truncated
      comparison). Repo: market-tick-data-service (read-only query, no code change expected). Source:
      `issues/cefi_aster_book_snapshot5_batch_stale_code_attempted_failed_burst_2026_08_09.md` todo 2 (line 160). **Done
      when**: EITHER no newer row is found — flip the source doc's todo 2 checkbox citing "confirmed non-recurring as of
      <today's date>, 0 rows newer than the cutoff" — OR a newer row is found, in which case do NOT close the source
      doc's todo; instead file a fresh P0 tarball-staleness escalation per that todo's own stated procedure (cite this
      doc + `tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md`) and leave the source todo open with
      a note pointing at the new escalation. **DONE (2026-08-10, slot 22)** — bounded cefi manifest query returned 2,000
      matching rows, **0 with `attempted_at` strictly newer than the microsecond-precision cutoff
      `2026-08-09T01:24:28.273974+00:00`** (max attempted_at == cutoff exactly). Confirmed non-recurring as of
      2026-08-10 — source doc `cefi_aster_book_snapshot5_batch_stale_code_attempted_failed_burst_2026_08_09.md` todo 2
      flipped. Read-only query, no code change (doc-only flip).

## Deferred — operator-gated (not drafted; genuine cefi-specific work, but design/sign-off gated)

- **`issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`** — 5 of its 8 open items are
  genuinely cefi-specific (DERIBIT-COMBO venue-key retirement, phantom OPTION removal on bare OKX/OKX_FUTURES,
  BINANCE-DELIVERY tooltip copy, CEFI instrument-definition parquet resharding design, CeFi/TradFi historical manifest
  backfill) and are never cited in any cefi covering doc — a genuine orphan by this audit's own definition. Not drafted
  here: every one of the 5 is explicitly self-described as deferred pending an operator go-ahead, a design sign-off on
  the doc's own mockup, or (for the backfill item) a not-yet-confirmed prerequisite utility
  (`manifest_reprocessing_generic_utility_2026_07_07.md`) — none is a bounded, worker-determinable outcome today. Needs
  the operator to review the doc's mockup/design questions directly; once ruled, a future batch can extract the
  now-bounded items.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility"
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`
- `/codex/05-infrastructure/vm-launcher-runbook.md` (ordinary fleet-daemon restarts are AO-dispatchable by default)

## Progress Log

- **2026-08-10 (slot 24, data_engineering, todo 2)**: Added 21 focused unit tests for `_is_tardis_consumer` (13 tests:
  name-pattern match 4, metadata-stamp 3, neither/not-counted 3, edge cases 3) and `_enforce_tardis_cap` (8 tests:
  empty/at-cap/over-cap 3-VM-cap-1 oldest-kept-newest-killed/dry-run/persist-per-kill/kill-failure). Uses existing
  `_FakeComputeClient`/`_FakeComputeInstance` pattern plus a new `_FakeTardisMetadataItem` helper. QG green (3282
  passed), quickmerge landed `deployment-service@0c14f54050`. Source issue doc
  (`tardis_concurrency_gate_hardening_2026_08_09.md`) archived — both todos now resolved.
- **2026-08-10 (slot 18, data_engineering, todo 1)**: Relaunched the watchdog per todo 1. First launch
  (`vm-zombie-watchdog-20260810-120624`) stayed RUNNING but every sweep crashed before pass 3 — the Tardis self-check
  never ran. Root-caused TWO pre-existing watchdog defects (both in
  `deployment-service/scripts/vm/vm_zombie_watchdog.py`): (1) `_persist_zombie_alert`'s
  `except (BucketNamingError, OSError, ValueError, RuntimeError)` missed `google.api_core.exceptions.GoogleAPIError` —
  the alert-ledger write to `unified-trading-cicd-events` failed with a 403 (`uts-prd-sa` lacked
  `storage.objects.create`) and the exception propagated, aborting the whole sweep in direct violation of the function's
  own "best-effort, never raises" contract; (2) `_vm_age_minutes`'s `compute_client.get` had no 404 tolerance, so a VM
  deleted between the fleet list and its per-VM evaluation also aborted the sweep. Fixed both in
  `deployment-service@3d545372` (widen to `except Exception` + skip-and-log on per-VM eval failure in the `as_completed`
  loop), granted `uts-prd-sa` `roles/storage.objectCreator` on `unified-trading-cicd-events` (verified binding), QG
  green, quickmerge landed. Deleted the pre-fix VM, relaunched as `vm-zombie-watchdog-20260810-124145` (12:41:45Z).
  First sweep completed cleanly pass 1→2→3: `Watchdog summary: 728 alive / 0 zombie / 79 too_young` →
  `terminated-reaper complete: reaped 0/0` → `Tardis-cap self-check: 1 Tardis-consuming VM(s) found, cap=1, 0 excess`
  (12:51:45Z, within one 5-min cycle). Both todo-1 checkboxes (this plan + source issue doc) flipped. Todo 2 (unit test)
  still open.
- **2026-08-10** — Drafted by `/ag-closeout-audit cefi` (ag_closeout_auditor, slot 23, autonomous one-shot). Phase 0:
  `generate_ag_closeout_audit_candidates.py --tranche cefi` → 78 candidates, 20 covering docs, 9 never-cited. Phase 1:
  Workflow (7 agents) classified the 9 minus 2 already-resolved directly (the audit-rollout meta-doc, confirmed
  legitimate multi-AG; this run's own prior same-day parked-findings doc, self-referential) — 4 confirmed genuinely
  cross-cutting (excluded), 1 genuine cefi orphan but operator-gated (deferred above), 2 genuine AO-eligible cefi
  orphans (extracted above). `status: draft` per the skill's autonomous-mode safety rail — awaiting operator review to
  flip to `active`.
- **2026-08-10 (slot 22, data_engineering, todo 3)**: ran the ASTER/book_snapshot_5 stale-tarball recurrence check per
  the todo's done-when. Bounded cefi manifest query (`read_availability_index_safe`, bucket
  `market-data-tick-cefi-prd-central-element-323112`,
  `columns=[date, venue, data_type, capture_status, error_reason, attempted_at, pipeline_mode, source, service_name]`,
  `filters=[data_type=book_snapshot_5, venue=ASTER, capture_status=attempted_failed, error_reason=UpstreamTimestampBiasError]`)
  → 2,000 matching rows; **0 have `attempted_at` strictly newer than the microsecond-precision cutoff
  `2026-08-09T01:24:28.273974+00:00`** (max attempted_at == cutoff exactly). Confirmed non-recurring as of 2026-08-10 —
  flipped the source doc (`cefi_aster_book_snapshot5_batch_stale_code_attempted_failed_burst_2026_08_09.md`) todo 2
  checkbox + this plan's todo 3. Read-only query, no code change (doc-only flip).
