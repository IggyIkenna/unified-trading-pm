---
doc_type: plan
title:
  TradFi satellite AO batch 10 — 2 bounded items from the round-9 RECLASSIFY sweep (MVP-of-MVP backfill verify + a
  scheduler-history diagnostic)
summary: >-
  Satellite-batch extraction from the round-9 combined RECLASSIFY + satellite-extraction sweep (2026-08-09), tradfi
  tranche. Two items qualified: (1) the manual-launch FRED/CBOE-Treasury-INDEX/KRW/DXY backfill verify+launch step from
  `tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md` — all 4 cells are Yahoo/FRED-sourced (NOT gated by the
  open Databento billing-suspension issue) and every named launcher either already exists or shipped same-day; (2) a
  read-only `gcloud logging read` diagnostic from `tradfi_catalogue_regen_scheduler_silently_not_paused_2026_08_08.md`
  to determine whether `lifecycle-catalogue-regen-tradfi-daily`'s 2026-06-25 pause claim ever actually took effect via
  the Scheduler API — flagged as a clean MISCLASSIFIED_LIKELY_AO_ELIGIBLE candidate by that same doc's own 2026-08-09
  na-eligibility-audit pass but not promoted that run. Both source docs stay `assigned_vm: NA` overall (each carries
  other genuinely operator/design-gated content) — only these 2 items extracted. Conflict-checked against
  tradfi_satellite batches 6-9 (all active/complete) and `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` —
  zero collisions.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service, unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, satellite-extraction, batch-10, mvp-of-mvp, scheduler-diagnostic]
related:
  [
    /plans/active/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md,
    /plans/active/issues/tradfi_catalogue_regen_scheduler_silently_not_paused_2026_08_08.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch9_2026_08_09.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch10_2026_08_09_finalize.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.64
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md,
    /plans/active/issues/tradfi_catalogue_regen_scheduler_silently_not_paused_2026_08_08.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
depends_on: []
source: >-
  Round-9 combined RECLASSIFY + satellite-extraction sweep (2026-08-09), tradfi tranche. Both source docs read end to
  end; items conflict-checked against every active tradfi satellite batch (6-9) plus
  `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`.
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
---

# TradFi satellite AO batch 10 — 2026-08-09

Only 2 items qualified from the 2 candidate docs this sweep read in full — both source docs remain genuine mixes with
other operator/design-gated content untouched. Yield is deliberately thin; reported honestly rather than padded.

## Todos

- [ ] [DATA] P1. **Verify FRED manifest coverage, then launch/verify the CBOE Treasury yield-curve INDEX + KRW/USD +
      DXY backfills.** Per `tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`'s in-scope list, these 4 cells are
      ALL Yahoo Finance / FRED sourced — **not gated by the open Databento account-billing-suspension issue**
      (`tradfi_databento_account_billing_suspended_2026_08_09.md`, which only affects Databento-sourced fetches).
      First, check the live manifest for actual FRED macro-series coverage — `macro_micro_econ_data_capture_audit_2026_06_05.md`
      records the FRED backfill launched+verified 2026-07-30 (`tradfi-bf-fred-full-*`), so this step may resolve to
      "already covered, verify only." Then launch/verify full-history backfills for: (a) the CBOE Treasury
      yield-curve INDEX (US3M/US2Y/US5Y/US10Y/US30Y, Yahoo `ohlcv_24h`) — existing launcher, manual invocation (not
      `wave_launcher.py`-auto-dispatched, FX/ICE/`ohlcv_24h` excluded by design); (b) KRW/USD spot FX (Yahoo
      `ohlcv_24h`) — existing launcher, manual invocation, same reason; (c) DXY (US Dollar Index, Yahoo `ohlcv_24h`) —
      launcher shipped same-day (`deployment-service@bd561d917`,
      `scripts/vm/launch-tradfi-bf-ice-ohlcv-24h.sh`, `VM_VENUE=ICE`, no `--source` flag needed since Yahoo is the
      only source). Per the vm-launcher-runbook, verify each launch STARTED + reaches a terminal manifest state (no
      fire-and-forget). **Done when**: the manifest shows non-empty `captured` coverage for all 4 cells across their
      full stated history windows (CBOE-Treasury/KRW full history; DXY full history), with the FRED-coverage
      verify-vs-backfill disposition stated explicitly. Repos: market-tick-data-service, instruments-service. Source:
      `issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md` (the "NEW (2026-08-09) — before launching
      anything: check the manifest..." todo).
- [ ] [DIAG] P2. **Determine WHEN `lifecycle-catalogue-regen-tradfi-daily` actually got re-enabled** (was it ever
      truly paused via the Cloud Scheduler API on 2026-06-25 as two plan docs claimed, or did that session pause it
      manually out-of-band via a mechanism that didn't persist — e.g. a `gcloud` command that failed silently, or a
      subsequent Terraform apply/redeploy that reset it to its Terraform-declared default state). Run
      `gcloud logging read 'resource.type="cloud_scheduler_job" resource.labels.job_id="lifecycle-catalogue-regen-tradfi-daily"' --project=central-element-323112 --freshness=90d`
      (Cloud Audit Logs retention permitting) to pull the actual pause/resume history. This is read-only (no delete,
      no `--apply`, no VM launch) — a bounded, worker-determinable diagnostic. **Done when**: the doc's own DIAG
      todo (`issues/tradfi_catalogue_regen_scheduler_silently_not_paused_2026_08_08.md` todo 4) is answered with cited
      log evidence — either "the pause never took" (script/API-call bug) or "something later silently re-enabled it"
      (a deploy-time reset gap) — and that doc's checkbox is flipped `[x]` citing the finding. Repo:
      unified-trading-pm (finding write-up) + whichever repo the root cause points to (fix itself is NOT in scope for
      this todo — diagnosis only). Source:
      `issues/tradfi_catalogue_regen_scheduler_silently_not_paused_2026_08_08.md` (todo 4, DIAG P2), flagged
      MISCLASSIFIED_LIKELY_AO_ELIGIBLE by that doc's own 2026-08-09 na-eligibility-audit entry but not promoted that
      run.

## Not extracted this batch — items that stay behind

- `tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`'s `wave_launcher.py` CME dedup fix — found ALREADY SHIPPED
  during this sweep's conflict-check (`deployment-service@bcf55c781f98f3834298252c443ed5ffa6f42a35`, confirmed
  ancestor of `origin/live-defi-rollout`); flipped `[x]` directly on the source doc in this same sweep, not extracted
  here.
- `tradfi_catalogue_regen_scheduler_silently_not_paused_2026_08_08.md`'s build-time exclusion filter (item 1) —
  already tracked verbatim in `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` (KEEP-NA-STALE duplicate,
  citation already present); its scheduler re-enable item (item 2) is DEPENDENCY_BLOCKED on that filter shipping; its
  standing-health-check item (item 4) is a genuine open design/scoping question, not yet a committed bounded task.
- `data_completion_tradfi_2026_07_15.md` — read this same sweep; its 15 open items are overwhelmingly
  operator/credential/design-gated (Databento billing suspension, `altdata` AG-home wiring scoping, a cefi-owned
  QG-RED item, a permanent R1 data-loss record) per 8 prior na-eligibility-audit passes, independently confirmed here.
  One citation fix applied directly (November-2026 scope-gate note on the NASDAQ/NYSE equities coverage-gap item) —
  no bounded, conflict-clear extraction candidate found.

## Progress Log

- 2026-08-09 (round-9 combined RECLASSIFY + satellite-extraction sweep, tradfi tranche): drafted alongside its
  finalize twin. 2 conflict-clear todos extracted from 2 source docs; 1 additional item (wave_launcher.py dedup fix)
  found already-shipped and flipped directly on its source doc rather than extracted. Conflict-check run against
  tradfi_satellite batches 6-9 (all active/complete) and `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` —
  zero collisions on the 2 extracted items.
