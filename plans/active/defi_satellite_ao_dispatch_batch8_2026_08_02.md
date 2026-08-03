---
doc_type: plan
title: DeFi satellite AO batch 8 — na-eligibility-audit reclassification (scheduled na_eligibility_auditor)
summary: >-
  Eighth AO-dispatch batch for defi, produced by the scheduled `na_eligibility_auditor` running `/na-eligibility-audit
  defi` (2026-08-02). Phase 0 found 34 defi-OWNED `assigned_vm: NA` docs (48 in the tranche's candidate set, 14 owned by
  other tranches and therefore read-and-reported only); 15 were in scope after the incremental-diff filter. Phase 1
  classified all 15 end to end and surfaced exactly ONE conflict-cleared RECLASSIFY item, extracted verbatim below: the
  `-test-`-bucket force/skip sample-download proof from `lst_rate_honest_coverage_2026_07_21.md` Phase 3, whose stated
  `BLOCKED-CREDENTIALS` blocker was retired 2026-07-29 (bucket exists since 2025-11-12, `unified-trading-sa` holds
  `roles/storage.admin`) leaving a bounded, worker-determinable runtime-verification task. The source plan stays
  `assigned_vm: NA` — its other 5 open todos are real-infra multi-year backfills blocked on a separate P0 OOM bug, an
  in-flight VM run, and two strategy money-path legs, none whole-doc-flippable. Shape (a) fresh carve-out per
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 1, mirroring batch1-7.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, na-eligibility-audit, reclassification, batch-8, satellite-docs, honest-coverage]
related:
  [
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    /plans/active/defi_satellite_ao_dispatch_batch8_2026_08_02_finalize.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-02"
last_updated: "2026-08-02"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    /codex/02-data/lst-exchange-rate-surfaces.md,
    /cursor-configs/skills/data-pipeline-check-mtds/SKILL.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
depends_on: []
source: >-
  `/na-eligibility-audit defi` run 2026-08-02 (autonomous, scheduled na_eligibility_auditor, tranche=defi) — Phase 1
  classified 15 in-scope `assigned_vm: NA` docs end to end; Phase 2 conflict-checked the single candidate RECLASSIFY
  item against every active `assigned_vm: planning` plan in `parent_epic` `defi_master` (32 plans) and
  `infrastructure_master` (96 plans) plus the tranche's own `defi_consolidated_closeout_2026_07_18.md`, and cleared it.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# DeFi satellite AO batch 8 — 2026-08-02

**status: active — conflict-cleared, dispatching.** Drafted autonomously by the scheduled `na_eligibility_auditor`
running `/na-eligibility-audit defi`. The single todo below cleared the shared conflict-check
([`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`](/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md)
§ 3) against the live `defi_master` + `infrastructure_master` backlogs before being drafted here.

## Todos

- [ ] [DATA] P3. **Prove force + skip for the LST-rate surfaces against the `-test-` bucket** — extracted verbatim from
      [`/plans/active/lst_rate_honest_coverage_2026_07_21.md`](/plans/active/lst_rate_honest_coverage_2026_07_21.md)
      Phase 3 (that plan stays `assigned_vm: NA`; only this item was conflict-cleared). Run a sample download for the
      **AAVE oracle surface** (`--operation collect-oracle-prices`, the operation the AAVE/Chainlink code actually lives
      under — NOT `collect-evm-defi`, see the source plan's Phase-5 misdirected-launch finding) against
      `gs://market-data-tick-defi-test-central-element-323112`, then repeat for the **DEX surface** (`dex_pool_swaps`)
      only if its endpoint is confirmed live at dispatch time — re-verify, do not trust the source plan's 2026-07-21
      probe stale. **Done when**: the force-leg is shown to write the canonical parquet **and** a manifest `captured`
      row, and the skip-leg is shown to fire the freshness skip, for the AAVE-oracle surface at minimum — with the VM
      `run.log` read as ground truth (per the source plan's own wording), not a launcher exit code. Report the DEX leg's
      verdict either way (proved / endpoint-unavailable), never silently drop it. Repos: market-tick-data-service,
      deployment-service. - **Safe-idempotent justification (why no `[OPERATOR]` tag is required for the VM launch)**:
      this writes ONLY to the `-test-` bucket, performs **no deletes**, **no `--apply`**, and **no prod-bucket or
      prod-manifest write**; a re-run is idempotent by construction (the force leg overwrites its own test-bucket
      object; the skip leg is read-only). This is the standard `/data-pipeline-check-mtds` shape, not a migration. -
      **Precondition already verified, do not re-litigate it**: the source todo's original
      `BLOCKED-CREDENTIALS (2026-07-22)` framing was retired 2026-07-29 — the `-test-` bucket exists (created
      2025-11-12, actively used) and `unified-trading-sa` already holds `roles/storage.admin` +
      `roles/storage.objectAdmin`, both confirmed via live `gcloud`. The operator separately approved `--auto-day`, so
      the day does **not** need to come from an operator ask for this run. - **Known execution hazards, budget for
      them** (each has burned a prior pipeline-check run, all already filed): driver timeouts orphaning duplicate VMs
      ([`/plans/archive/issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md`](/plans/archive/issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md)),
      worker-session teardown killing a long-running check
      ([`/plans/active/issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`](/plans/active/issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md)),
      and a missing env flag producing a `-test-` bucket 403
      ([`/plans/active/issues/pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md`](/plans/active/issues/pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md)).
      Do not report a stall as a failure without checking these three first.

## Deferred — classified but NOT extracted (no operator ruling needed; each is unambiguous)

- **`issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md:202`** (the 5,332-object composite-venue
  fold) — the conflict-check found it **already executed to completion**, not outstanding:
  `defi_satellite_ao_dispatch_batch6_2026_07_30.md`'s matching `[DATA] P1` shipped it 2026-08-01
  (`market-tick-data-service@13f14b78`, 5,332/5,332 shards, 0 errors, 324,867 objects + manifest rows). Handled as a
  stale-checkbox correction on the source doc (conflict-check protocol § 3 step 4), not drafted here.
- **`issues/defi_catalog_dp_catalog_001_shrink_blocked_2026_08_02.md:157`** (`[DATA] P2`, root-cause why the R3
  migration VM vanished with zero operation history) — genuinely bounded and independent of that doc's undecided A/B/C
  operator question, BUT the doc carries a live standing hold from main ("hold, apply nothing, await operator go on R3",
  standing escalation #1, 3 CRITICAL pages). Extracting a todo out from under an explicit hold instruction on a
  P0-escalation doc is the redirect-banner class the skill's Phase 1 says not to override. Left in place; re-assess once
  the R3 decision lands.

## Progress Log

- 2026-08-02 (scheduled `na_eligibility_auditor`, tranche=defi, autonomous): Drafted alongside its finalize twin, both
  `status: active` (dispatching immediately — na-eligibility-audit's autonomous mode applies auto-fixable classes
  without pausing; this todo cleared its own conflict-check, so there was no genuine ambiguity to park). The source plan
  `lst_rate_honest_coverage_2026_07_21.md` stays `assigned_vm: NA` — only this one item was extracted.
- **⚠️ 2026-08-02 — the source doc could NOT be annotated to cite this batch, and that is a known blocker, not an
  oversight.** `lst_rate_honest_coverage_2026_07_21.md` is **1001L, already over `check_line_caps.sh`'s 1000L HARD cap**
  with 6 open todos, so the gate's staged-file mode ("a file THIS commit touches must not be over its tier's cap, full
  stop") refuses every edit to it — including the one-line extraction annotation and this skill's own verdict marker.
  Verified empirically this run (exit 1 at 1019L), then reverted. Filed as
  [`/plans/active/issues/over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md`](/plans/active/issues/over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md)
  (`[OPERATOR]`-gated policy call; the 2026-07-30 cap exception covers only ZERO-open-todo docs). **Consequence to be
  aware of if you are a future auditor**: the source's Phase-3 checkbox still reads plainly open with no citation, so it
  can look un-dispatched. It is NOT — it is this batch's todo. Do not re-extract it; check this doc first. The deferred
  annotation text is preserved verbatim in that issue doc for whoever unblocks the cap.
- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries).
