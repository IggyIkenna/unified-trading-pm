---
doc_type: plan
title: Cross-cutting satellite AO batch 4 — 4 conflict-cleared todos from the DATA_EPICS membership-gap fix
summary: >-
  Fourth AO-dispatch batch for the cross-cutting tranche, produced by re-invoking `/ag-closeout-audit cross-cutting`
  (autonomous, scheduled `ag_closeout_auditor` dispatch `agt-b09d86`, slot 10). Phase 0 found `total_members=89,
  never_cited=0` via `generate_ag_closeout_audit_candidates.py` — but cross-checking against
  `check_ag_closeout_linkage.py`'s stricter (main-closeout-doc-only) linkage signal surfaced a real gap: the generator's
  `DATA_EPICS` set (used to gate cross-cutting membership for docs not yet cited anywhere) was missing
  `batch_live_symmetry_master` (the batch=live determinism/event-log spine epic — genuinely cross-cutting per
  CLAUDE.md's own "Live = batch" section), silently excluding 5 real cross-cutting docs from membership entirely — not
  even reaching the never-cited bucket. Fixed the script (`generate_ag_closeout_audit_candidates.py@<this-run>`);
  corrected numbers: 93 members, 2 never-cited. A Phase-1 `Workflow` (3 agents: the 2 newly-surfaced never-cited docs +
  a 3rd doc retagged in from a stale `[meta]` tag during the same gap-hunt) classified: 2 `orphaned_never_touched`, 1
  `orphaned_partial_coverage` (cited in the closeout's Track-19 Sources digest, which is explicitly non-dispatch, not a
  real todo). This batch drafts 4 conflict-cleared todos across all 3 docs; the 2 remaining docs' larger/gated items are
  Deferred (see below) rather than force-fit into a batch todo.
status: draft
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm, deployment-service, batch-live-reconciliation-service]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-4, data-epics-gap-fix]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch3_2026_08_01.md,
    /plans/active/issues/ag_closeout_audit_cross_cutting_parked_2026_08_02.md,
    /plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md,
    /plans/active/issues/batch_live_recon_cloud_run_job_stage0_never_succeeded_2026_07_30.md,
    /plans/active/issues/pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-02"
last_updated: "2026-08-02"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.64
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit cross-cutting re-invocation 2026-08-02 (autonomous, dispatch agt-b09d86, slot 10) — discovered
  while cross-verifying Phase 0's generator-script output against check_ag_closeout_linkage.py's independent orphan
  signal, which surfaced a real DATA_EPICS whitelist gap in generate_ag_closeout_audit_candidates.py.
---

# Cross-cutting satellite AO batch 4

> **Status: draft** — this batch is `status: draft` pending explicit operator review + approval to dispatch (flip to
> `status: active`), per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE and this skill's own
> Autonomous-mode Phase 3 contract (a skill-drafted plan is never auto-shipped). Every todo below is independently
> conflict-cleared (grepped against all 8 prior cross-cutting covering docs — consolidated closeout + batch1/1b/2/3 +
> their finalizes — zero real-todo hits found for any of the 4 items below) and file-disjoint from every other todo
> here — safe to dispatch as-is once approved.

## Todos

- [ ] [SCRIPT] P3. **Determine whether the batch-live-recon VM launcher and the live Cloud Run job are duplicate
      deployment mechanisms for the same reconciliation.** Source:
      `issues/batch_live_recon_cloud_run_job_stage0_never_succeeded_2026_07_30.md` todo 3. Confirm whether
      `deployment-service/scripts/vm/launch-batch-live-recon-cron-vm.sh` and the live Cloud Run job
      `uts-prod-batch-live-reconciliation-service` are the SAME reconciliation running via two different deployment
      mechanisms (making the VM launcher dead/redundant code) or genuinely different use cases (VM = manual/backfill
      re-run; Cloud Run = live nightly). If the former, apply a lifecycle marker
      (`# Epic:`/`# Lifecycle:`/`# Delete-when:`) to the VM launcher per `/codex/06-coding-standards/script-homes.md`
      and note it in `deployment-service`'s own dispatch-branch docs; if the latter, document the use-case split inline
      in both scripts. **Done when**: the duplication question is answered with cited evidence (code read, not
      inference), the appropriate follow-up (lifecycle marker or documented split) is applied, and the source doc's
      todo 3 checkbox is flipped. (repo: deployment-service, unified-trading-pm)
- [ ] [INFRA] P3. **Grant `uts-test-sa` write access on the `central-element-323112-events` bucket to fix the residual
      non-fatal 403 on `-test-`-tier event-log uploads.** Source:
      `issues/pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md`'s final open todo. The doc's other 5
      items already shipped (IS/MTDS/MDPS `--env staging` fixes + 2 downstream `-stg-`/`-test-` bucket-tier bugs, all
      QG-green + verified on `origin/live-defi-rollout`); this is the one remaining residual. Mirror the
      `deployment-scripts` grant already made in that doc's "What I actually shipped" section:
      `gcloud storage buckets add-iam-policy-binding gs://central-element-323112-events --member="serviceAccount:uts-test-sa@central-element-323112.iam.gserviceaccount.com" --role="roles/storage.objectAdmin"`
      (verify the bucket's IAM-Condition/UBLA shape first — the `deployment-scripts` grant needed to be unconditional
      because that bucket lacks Uniform Bucket-Level Access; confirm whether the same applies here before choosing
      conditional vs. unconditional). Then run a fresh `-test-`-tier VM (any of the 4 `pipeline_e2e_check.py` drivers)
      and confirm its event-log objects actually land in the bucket. **Done when**: the grant is live-verified via
      `gcloud storage buckets get-iam-policy`, a fresh `-test-` run's event-log objects are confirmed present, and both
      the source doc's todo and its own "residual non-fatal 403... still unfixed" note are updated to reflect closure.
      (repo: deployment-service or infra config, wherever the events-bucket IAM lives; unified-trading-pm for the doc
      update)
- [ ] [DATA] P2. **File the dead-`mode=`-kwarg bug as its own issue doc.** Source:
      `daily_trading_analyst_llm_job_design_2026_07_29.md` §5. `execution_fills`/`positions`/`strategy_instructions`/
      `pnl_attribution` silently drop their `mode=` kwarg, so batch/paper/live collide on one object path instead of
      being kept distinct. Read the source doc's §5 description of this bug (cites the specific classes/call sites),
      verify it reproduces against current code, and file
      `plans/active/issues/execution_fills_mode_kwarg_silently_dropped_<date>.md` (or the current date at file-time)
      with full repro evidence, in `unified_trading_library`. This todo is filing-only — do not attempt the actual fix
      here (that's a separate, not-yet-scoped `unified-trading-library` code change). **Done when**: the new issue doc
      exists with cited repro evidence, and `daily_trading_analyst_llm_job_design_2026_07_29.md`'s §5 corresponding
      checkbox is flipped citing the new doc. (repo: unified-trading-pm for the issue doc; read-only verification in
      unified-trading-library)
- [ ] [DOC] P2. **Fix the stale scheduled-jobs table in the AO single-VM architecture SSOT.**
      Source: `daily_trading_analyst_llm_job_design_2026_07_29.md` §5. `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`'s
      scheduled-jobs table currently says "opus / 01:00 UTC daily" for at least one live job whose actual current
      config is "sonnet / hourly-retry" (per this source doc's own finding — verify the exact row(s) affected by
      reading the table against each job's live `install-*-timer.sh`/systemd-timer config before editing, don't just
      trust the source doc's paraphrase). Correct the stale row(s) to match live reality. **Done when**: every row in
      the table is cross-checked against its live timer config and corrected where stale, and the source doc's §5
      corresponding checkbox is flipped. (repo: unified-trading-pm)

## Deferred — too-large-for-a-batch-todo (needs its own dedicated design/build plan)

- **`daily_trading_analyst_llm_job_design_2026_07_29.md`**'s 3 remaining §5 items form an internally-sequential
  multi-day, multi-repo build chain: (1) build the trading-analyst skill itself (per-category data adapters reusing
  BLRS's stage readers + a prompt/dedup contract), (2) wire the AO scheduling mechanics (new `agents/trading_analyst.md`
  role file, a new `plan_health.py` mode, a new `install-trading-analyst-timer.sh`), (3) retire BLRS Stage 4's
  `_write_agent_report()` write path once (1)+(2) are confirmed live in production. Per the skill's own non-batchable
  taxonomy ("too-large-or-risky-for-a-batch-todo"), cramming a from-scratch new recurring-agent-job build spanning
  `batch-live-reconciliation-service`/`trading-agent-service`/`agent-orchestrator`/`unified-trading-pm` into one batch
  todo (or racing 3 fanned-out todos across a genuinely sequential chain) risks under-scoping a build this size without
  a dedicated read of the full design doc + explicit operator sign-off on the approach. Recommend: promote to its own
  standalone plan once an operator/design-owning agent has read `daily_trading_analyst_llm_job_design_2026_07_29.md` in
  full and confirmed the design is ready to build as-specified.

## Deferred — operator decision needed (BLOCKED-OPERATOR-DECISION)

- **`daily_trading_analyst_llm_job_design_2026_07_29.md`** §5's `[OPERATOR] P2` item — decide the exact escalation-N
  (days a condition must recur before severity escalates) and the initial `assigned_vm` default (`planning` vs `NA`)
  for issue docs this future job would file. Explicitly operator-gated per the source doc's own tagging, not
  code-derivable. Re-check once the "too-large" build item above is actually picked up (this decision likely wants to
  be made alongside that build, not in isolation).

## Codex SSOTs

`/codex/02-data/live-data-persistence-and-event-log.md`, `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`,
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`, `/codex/06-coding-standards/script-homes.md`.

## Progress Log

- **2026-08-02** — Drafted (`/ag-closeout-audit cross-cutting`, autonomous, dispatch `agt-b09d86`, slot 10). Phase 0
  discovered + fixed a real `DATA_EPICS` whitelist gap in `generate_ag_closeout_audit_candidates.py` (missing
  `batch_live_symmetry_master`), corrected via cross-verification against `check_ag_closeout_linkage.py`'s independent
  (stricter, main-closeout-doc-only) orphan signal. Corrected Phase 0 numbers: 93 members (was 89), 2 never-cited (was
  0). A 3rd doc (`pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md`) was separately retagged in from a
  stale `[meta]` tag during the same gap-hunt (genuine cross-cutting content: IS/MTDS/MDPS/features `-test--bucket
  VM-launcher IAM gap) and included in the same Phase-1 pass. Orthogonality HARD CHECK re-run with the FULL peer-marker
  set (previous runs only checked the 5 AGs as peers — this run added `ao`/`ci`/`infrastructure`/`ui`): found 2 new
  single-peer+cross-cutting dual-tag mistags (both `[ao, cross-cutting]`), parked for the `ao` tranche (see the parked-
  findings issue doc). Phase 1 (`Workflow`, 3 agents): 2 `orphaned_never_touched`
  (`daily_trading_analyst_llm_job_design_2026_07_29.md`, `batch_live_recon_cloud_run_job_stage0_never_succeeded_2026_07_30.md`)
  + 1 `orphaned_partial_coverage` (`pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md` — cited in the
  closeout's Track-19 Sources digest, which is explicitly non-dispatch). Phase 3 conflict-check: all 4 drafted todos
  independently grepped clean against all 8 covering docs (consolidated closeout + batch1/1b/2/3 + finalizes) — zero
  real-todo hits for any. 3 items deferred as too-large-for-a-batch-todo (a multi-day multi-repo build chain); 1 item
  deferred as operator-gated. `status: draft` pending operator review.
