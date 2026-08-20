---
doc_type: plan
title: tradfi satellite AO dispatch batch 15 — 2026-08-17
summary: >-
  Extraction batch from the tradfi tranche's 2026-08-17 /na-eligibility-audit sweep — 8 conflict-cleared,
  bounded/deterministic items pulled from 6 source docs (RECLASSIFY per-todo-split candidates from the NA audit).
  Two items (T2) were narrowed/consolidated across sibling source docs after this audit found their original
  4-VM scope included 2 VMs already root-caused as billing-blocked elsewhere; two items (T4, T5) were reworded
  from their source docs' literal text to avoid re-testing an already-disproven hypothesis / repeating a
  documented incident. Each todo cites its exact source doc; the source docs themselves are NOT touched by this
  batch (checkbox reconciliation back into each source doc happens in the paired finalize plan, except for the
  citation-only checkbox flips already applied directly by the audit at extraction time). Conflict-checked against
  every existing active batch/finalize plan for this tranche (grep sweep for account_delinquent/billing_blocked,
  resume_after_maintenance/scheduler_maintenance, asyncio.wait_for, check_reference_paths baseline, and the
  archival target's filename) plus the infra tranche's batch18 (SchedulerMaintenance-adjacent work, confirmed
  different mechanism/already shipped) before drafting — no item here duplicates ground an existing dispatched
  todo already claims.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm, market-data-processing-service, market-tick-data-service, deployment-service, instruments-service]
scope: [engineer]
tags: [tradfi, ao-dispatch, satellite-batch, na-eligibility-audit]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
    /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_btc_2020_exit137_stall_relaunch_bound_page_2026_08_16.md,
    /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_es_2020_exit137_stall_relaunch_bound_page_2026_08_15.md,
    /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_20260816_220209_databento_cme_billing_rootcause_2026_08_17.md,
    /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2021_exit137_stall_relaunch_bound_page_2026_08_16.md,
    /plans/active/issues/tradfi_catalogue_regen_scheduler_silently_not_paused_2026_08_08.md,
    /plans/active/issues/plan_reconciler_findings_tradfi_2026_08_16.md,
    /plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-20"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
assigned_role: data_engineering
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
sequential: true
context_scope:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    deployment-service/deployment_service/data_pipeline_monitors/scheduler_maintenance.py,
    instruments-service/scripts/build_instrument_catalogue.py,
  ]
source: >-
  Drafted by the 2026-08-17 /na-eligibility-audit tradfi-tranche scheduled dispatch (dispatch agt-d99b5c). Authored
  status: active directly per the skill's Phase 3 "the parent skill's own verdict IS the operator decision that
  flips the draft gate" rule (na-eligibility-audit, unlike ag-closeout-audit, is authorized to apply).
---

# tradfi satellite AO dispatch batch 15 — 2026-08-17

> Every todo below was classified bounded/deterministic (worker-determinable outcome, no open design/judgment call)
> by the 2026-08-17 `/na-eligibility-audit tradfi` sweep and conflict-checked against every existing active
> batch/finalize plan for this tranche (plus the infra tranche's batch18) before being drafted here.
>
> **`sequential: true`** — several todos here plausibly touch the SAME shared files (T6/T7/T8 all edit PM-repo
> docs and T6's ~43-referrer sweep may overlap T7's 2 target docs; T2/T4 may converge on the same launcher/adapter
> code if the root cause turns out to be shared across `tradfi-bf-cme-ohlcv-1m-` years) — serialized to avoid a
> concurrent-edit collision per this workspace's "concurrent todos MUST touch different files" rule, since that
> can't be guaranteed here.

## Todos

- [ ] [SCRIPT] P2. **Live re-verification sweep**, deferred from the archived
      `/plans/archive/2026_08/issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md` issue doc. Confirm
      3 already-shipped fixes hold on a fresh live run: (1) `ohlcv_24h` SchemaContract alias for
      future/equity/options_chain/index (`unified-api-contracts@079d48ff`) — confirm `--data-types ohlcv_24h` no
      longer crashes for those instrument_types; (2) ETF `ohlcv_1m`/`trades` SchemaContract registration
      (`unified-api-contracts@0228afe52a`) — confirm a fresh request for those data_types on ETF instruments writes
      successfully; (3) `instrument_type=option` leaf exclusion from `ohlcv_15m`/`ohlcv_24h` orchestration scans
      (`market-data-processing-service@2b2cc58ef3`) — confirm the 34 `instrument_type='OPTION'` "No SchemaContract
      registered" crash lines no longer appear. Fold all 3 into ONE
      `--data-types "ohlcv_15m ohlcv_24h ohlcv_1m trades"` verification run over CME/NASDAQ/NYSE (repo:
      market-data-processing-service). ALSO include `ohlcv_1m`/`ohlcv_1s` against a CME OPTION instrument
      specifically per the 2026-08-16 addendum finding (a pre-fix VM showed the same OPTION SchemaContract crash on
      those two fine timeframes too — 109,853 occurrences on one VM — not yet independently re-verified post-fix).
      Done when: the run completes and each of the 4 patterns is confirmed absent, or documented as a fresh finding
      if still present. Source: `/plans/active/data_completion_tradfi_2026_07_15.md` item 15 (L995).

- [ ] [BACKEND] P1. **Pull + read `run.log` for `tradfi-bf-cme-ohlcv-1m-es-2020-20260815-030216`** — the ONE
      remaining `tradfi-bf-cme-ohlcv-1m-` DP-VM-001 stall not yet explained by the tracked Databento CME billing
      block. **`btc-2020` resolved 2026-08-17** (data_pipeline_failure escalation agt-dfccf4, slot 12): pulled
      `run.log` for both `tradfi-bf-cme-ohlcv-1m-btc-2020-20260816-180410` and a fresh `...-20260817-060542`
      recurrence — both confirmed the identical Databento CME billing-block signature (402/account_delinquent) from
      the shard's first CME date onward; do not re-dispatch `btc-2020`, see
      `dp_vm_001_tradfi_bf_cme_ohlcv_1m_btc_2020_exit137_stall_relaunch_bound_page_2026_08_16.md`'s 2026-08-17
      Progress Log entry. Use `deployment_service.data_pipeline_monitors._gcs.read_text`/`read_terminal_exit_code`
      (SDK, never subprocess `gsutil`/`gcloud storage`). es-2020's log was already partially pulled (1561 lines,
      confirmed genuine `WORKER_STALLED`, but the stack trace identifies only the `tee`-wrapper process, not the
      actual worker — the hung call is still unidentified). Given 3 of 4 same-family incidents this week turned out
      billing-caused, FIRST check whether es-2020 also matches the 402/account_delinquent signature before assuming
      a genuine code defect. If billing-caused: no code fix needed, redirect to the billing doc, done. If genuinely
      a different cause: fix at the root — shared code defect → bound the offending call with `asyncio.wait_for` at
      the per-shard level per the shard-isolation SSOT; shard-specific → isolate + skip the poison instrument-date.
      Done when: the VM's `run.log` is read, a failure signature is identified (or documented as inconclusive), and
      either a code fix ships or it's confirmed billing-caused or shard-specific poison data. Sources:
      `/plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_btc_2020_exit137_stall_relaunch_bound_page_2026_08_16.md`
      item 2 (originally 4-VM scope, then narrowed to 2, now narrowed to 1 — btc-2020 resolved 2026-08-17),
      `/plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_es_2020_exit137_stall_relaunch_bound_page_2026_08_15.md`
      item 2 (absorbed — do not double-dispatch).

- [ ] [BACKEND] P3. **Optional hardening — DP-VM-001 stall-watchdog billing classification.** The in-VM stall
      watchdog currently can't distinguish "hung call" from "correctly-fast-failing on a known billing/entitlement
      error" — both surface as generic `exit_code=137`/`WORKER_STALLED`. Special-case a `402`/`account_delinquent`
      response into a distinct terminal state (e.g. `DEPLOYMENT_FAILED cause=billing_blocked`) so the fleet monitor
      and future escalations don't need to manually re-pull `run.log` to tell the two apart — 3 same-day/same-week
      DP-VM-001 incidents already required this exact manual read. Done when: the watchdog script classifies a
      402/account_delinquent response into the distinct terminal state, with a test proving the classification.
      Source:
      `/plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_20260816_220209_databento_cme_billing_rootcause_2026_08_17.md`
      item 2 (P3, optional hardening).

- [ ] [BACKEND] P2. **Pull + read `run.log` for `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2021-20260816-200155`** via
      `deployment_service.data_pipeline_monitors._gcs.read_text`/`read_terminal_exit_code` (SDK, never subprocess).
      FIRST check whether this shard's failure signature matches the confirmed Databento CME billing-block pattern
      (402/account_delinquent — see
      `dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_20260816_220209_databento_cme_billing_rootcause_2026_08_17.md`)
      before assuming a code-defect/poison-instrument cause — the sibling 2020-shard g01-6a-6l stalls both turned
      out to be billing-caused, not code defects, so check that hypothesis first rather than re-testing the two
      branches below from scratch. If billing-caused: no code fix needed, redirect to the billing doc, done. If
      genuinely a different cause: compare against the `btc-2020`/`es-2020` stall signatures (see this batch's
      Todo 2) and fix at the root — shared code defect → bound with `asyncio.wait_for` at the per-shard level;
      shard-specific → isolate + skip the poison instrument-date. Done when: the billing-vs-code-defect branch is
      determined and, if code-defect, either fixed or the two failures are confirmed to share/not-share a
      signature. Source:
      `/plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2021_exit137_stall_relaunch_bound_page_2026_08_16.md`
      item 2 (reworded per this audit — original 2-branch hypothesis didn't account for the now-confirmed billing
      block third outcome).

- [ ] [INFRA] P2. **Re-enable the tradfi catalogue schedulers via the guarded resume path.** The durable build-time
      exclusion filter has shipped and been reference-verified (`instruments-service@22a5f197`, cite-verified
      2026-08-17). Dry-run a manual `build_instrument_catalogue.py` regen to confirm the 4 previously-excluded legs
      (venue=ICE; venue=CBOE AND instrument_type IN (OPTION, SPOT_PAIR); the 2 VIX-cash INDEX ids) stay excluded.
      THEN re-enable both Cloud Scheduler jobs (`lifecycle-catalogue-regen-tradfi-daily` + the paired
      manifest-consolidator cron) using `deployment_service/data_pipeline_monitors/scheduler_maintenance.py`'s
      `resume_after_maintenance()` helper — do **NOT** use a raw `gcloud scheduler jobs resume` call. This exact job
      has a confirmed incident on record (source doc's own Progress Log): a 2026-06-27 raw `gcloud scheduler jobs
      resume` by an untargeted agent session silently undid an intentional protective pause with no safety check,
      causing 6+ weeks of silent catalogue pollution before detection. `scheduler_maintenance.py`'s guarded resume
      path (built 2026-07-13, specifically to prevent a repeat of this failure mode) is why this todo must not
      repeat the raw-gcloud pattern. Done when: the dry-run confirms the 4 legs excluded, both jobs are resumed via
      the guarded helper (not raw gcloud), and a live scheduler-state check confirms both jobs are RUNNING. Source:
      `/plans/active/issues/tradfi_catalogue_regen_scheduler_silently_not_paused_2026_08_08.md` item at L120
      (reworded per this audit to mandate the guarded helper, per this doc's own tracked incident history).

- [ ] [DOC] P2. **BLOCKED — premise stale, do NOT archive yet (corrected 2026-08-19, plan_reconciler epic-scoped
      tradfi_master pass).** ~~Archive `tradfi_canonical_path_migration_design_2026_07_19.md`. Run the standard
      6-step archival ritual. All todos already `[x]`~~ — **this is no longer true**: the 2026-08-18 pass converted
      2 prose-only "Deferred work" items into real tracked `- [ ] [DATA] P2.` todos (lines ~603, ~609 of that doc —
      a 207,438-object short-code→display-name migration and a broader orphaned-`combo` scoping item), both still
      open as of 2026-08-19. Its `archive_exempt: true` bridge comment has been corrected in place to flag this.
      **Revised done-when**: first resolve or explicitly re-scope those 2 open todos (real DATA migration work, not
      mechanical), THEN run the standard 6-step archival ritual (`codex/11-project-management/`) — `locked_by:` is
      currently empty, re-verify before starting. This doc has ~43 corpus referrers (confirmed 2026-08-17) — the
      referrer-path fixup remains the substantial part of the eventual archival task; budget for it. Source:
      `/plans/active/issues/plan_reconciler_findings_tradfi_2026_08_16.md` item 1 (L77) — archival half only; the
      text-correction half was already done 2026-08-16; this precondition-staleness correction is new 2026-08-19.

- [x] ✅ [DOCS] P3. **DONE 2026-08-19 (plan_reconciler, epic-scoped tradfi_master pass).** Fix the residual
      reference-path ratchet regression from the 2026-08-16 plan_reconciler pass's own archivals (baseline 34, was
      38 at filing — 2 of the original 6 were fixed same-run). Verified live this pass: `grep -n
      'batch7_2026_08_06' plans/active/tradfi_consolidated_closeout_2026_07_18.md` → both refs (L64-65) already
      point to `/plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch7_2026_08_06.md`(+`_finalize`) — already
      fixed by the 2026-08-18 pass (see `plan_reconciler_findings_tradfi_2026_08_18.md` item 7), just never flipped
      here because this doc was itself inside its own 12h grace window at that time.
      `tradfi_satellite_ao_dispatch_batch8_2026_08_08.md` is itself now archived (confirmed via `ls
      plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch8_2026_08_08.md`) — its internal refs are historical,
      no longer live-corpus. Source: `/plans/active/issues/plan_reconciler_findings_tradfi_2026_08_16.md` item 3
      (L100).

- [x] ✅ [DOCS] P3. **DONE 2026-08-19 (plan_reconciler, epic-scoped tradfi_master pass) — 4/4 complete.** Bump stale
      `last_updated` frontmatter on the 4 tradfi-tranche docs from the 2026-08-16 plan_reconciler pass's finding.
      3/4 were already fixed 2026-08-18 (`ag_closeout_audit_rollout_2026_07_25.md`,
      `estate_orphan_assessment_2026_07_21.md`, `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`, all
      bumped to `2026-08-17`). The 4th, `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`, was still
      inside its own 12h grace window as of the 2026-08-18 pass — bumped this pass, `last_updated: 2026-06-27` →
      `2026-08-17` (real git last-touch date, `git log -1 --format=%ad --date=short`). Source:
      `/plans/active/issues/plan_reconciler_findings_tradfi_2026_08_16.md` item 4 (L109).

## Progress Log

- **na-eligibility-audit 2026-08-17** (tradfi tranche, dispatch agt-d99b5c): drafted this batch from 6 source docs'
  conflict-cleared RECLASSIFY-per-todo-split candidates. Todo 2 narrowed from its source docs' original combined
  4-VM scope after cross-referencing the sibling billing-rootcause doc found 2 of those 4 VMs (`g01-6a-6l-2020`
  pair) already root-caused as billing-blocked — dispatching the original 4-VM wording would have had a worker
  re-discover that finding from scratch. Todo 4 and Todo 5 reworded from their source docs' literal text for the
  same reason (avoid re-testing an already-disproven hypothesis / repeating a documented incident).
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
