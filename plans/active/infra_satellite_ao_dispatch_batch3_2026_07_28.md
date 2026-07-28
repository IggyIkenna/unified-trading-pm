---
doc_type: plan
title:
  Infra satellite docs — AO dispatch batch 3 (6 conflict-cleared AO-eligible todos extracted from 6 satellite docs)
summary: >-
  `/ag-closeout-audit infra` re-run 2026-07-28 (Autonomous/AO-dispatched mode, operator away). Phase 0 found batch1
  (27 todos, ~5 done) and batch2 (9 todos) both still `status: active` and in-flight; none of batch1's 10
  conflict-gated Deferred items have cleared enough to convert yet (re-checked all against their named competing
  claims — see this plan's Progress Log). Phase 1 classified 13 new/unaccounted infra-tranche docs discovered since
  batch1/batch2 were drafted (created 2026-07-16 through 2026-07-27, mostly `assigned_vm: NA`): 2 are
  `archivable_now` (fully shipped, frontmatter simply never flipped — reported, not touched here, that's
  `/plan-reconcile` territory), 4 are orphaned but NOT AO-eligible (2 operator-decision-gated, 1 human-judgment-gated,
  1 mistagged single-AG doc), 1 is orphaned + AO-eligible but CONFLICT-GATED against batch1's own still-open todo 8
  (same file, `launcher_common.sh`), and 6 are orphaned, AO-eligible, and conflict-clear — extracted here.
status: draft
nature: process
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    alerting-service,
    deployment-service,
    trading-agent-service,
    agent-orchestrator,
    unified-trading-pm,
    unified-trading-library,
    features-service,
    execution-service,
    ml-service,
    deployment-api,
  ]
scope: [engineer, admin]
tags: [infra, ao-dispatch, satellite-docs, batch-3, plan-hygiene, close-out]
related:
  [
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/active/infra_satellite_ao_dispatch_batch2_2026_07_27.md,
    /plans/active/infra_satellite_ao_dispatch_batch2_finalize_2026_07_27.md,
    /plans/active/infra_satellite_ao_dispatch_batch3_finalize_2026_07_28.md,
    /plans/active/e2e_coverage_gaps_alerting_deployment_trading_agent_2026_07_27.md,
    /plans/active/issues/git_health_not_clean_since_pinned_constant_2026_07_27.md,
    /plans/active/issues/legacy_bucket_template_literals_2026_07_16.md,
    /plans/active/issues/heartbeat_stall_watcher_autokill_never_works_in_production_2026_07_27.md,
    /plans/active/issues/migration_vm_hung_detection_monitoring_gap_2026_07_27.md,
    /plans/active/issues/relaunch_stalled_vm_no_checkpoint_resume_gap_2026_07_27.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-28"
last_updated: "2026-07-28"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.4
estimate_calibrated_ai_days: 1.9
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  `/ag-closeout-audit infra` run 2026-07-28 (Autonomous/AO-dispatched mode, operator away). Phase 0 confirmed batch1 +
  batch2 both still active/in-flight and re-checked batch1's 10 conflict-gated Deferred items against their named
  competing claims (none cleared). Phase 1 ran a 13-agent Workflow classifying every infra-tranche doc created since
  batch1/batch2 (`plans/active/*.md` + `plans/active/issues/*.md` with `asset_group` containing `infrastructure`, not
  already cited by a covering plan). Phase 3 applied the dispatch-scope eligibility test + the HARD conflict check
  (grepped batch1 + batch2 + the hub for file/mechanism overlap) before drafting anything here.
---

# Infra satellite docs — AO dispatch batch 3

> **`status: draft` — NOT ingested, NOT dispatched.** Flipping this to `active` is the operator's call (CLAUDE.md §
> "Plan destination — ASK BEFORE CREATING"). Drafted autonomously 2026-07-28 while the operator was away.

## Why this plan exists

batch1 (2026-07-26) and batch2 (2026-07-27) are both still `status: active` and in-flight (batch1 ~5/27 todos done;
batch2's 9 todos not yet verified this pass). This is NOT a re-derivation of their content — it's the **next slice**:
13 infra-tranche docs were created (or last substantively touched) AFTER batch1/batch2 were drafted and were never
run through Phase 1 classification. This plan extracts the conflict-clear, AO-eligible subset of that new slice.

## Phase 0 re-check: batch1's Deferred conflict-gated items — none cleared

Re-checked all 10 of batch1's `## Deferred` conflict-gated items (per the iterative-drain methodology, step 1) against
their named competing claims before doing any fresh Phase 1 triage:

- **Item 1** (`PYTEST_UNIT_DIR` vs `issues/mtds_ungated_test_families_2026_07_17.md`): that doc is still
  `status: open` — not re-verified further; treated as still-conflicting.
- **Items 2/3** (`base-service.sh`/`base-library.sh` bundle): PARTIALLY cleared. The `base-library.sh` side
  (`tradfi_satellite_ao_dispatch_batch4_2026_07_26.md`'s item) is `[x] ✅` DONE (2026-07-27, slot-5) — verified
  directly in that plan's text. The `base-service.sh` side
  (`cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`'s MTDS retry_safe-convention item, which touches
  `base-service.sh`) is still `[ ]` open. Per the operator's "one owning plan at a time" ruling
  (`autonomous_session_operator_decisions_2026_07_25.md` #36), this item stays conflict-gated until that other plan's
  item lands too.
- **Item 4** (`DataStatusTab.tsx` vs `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` item B): still `[ ]`
  open in that plan — still conflicting.
- **Item 6** (repo_scripts DEPRECATE vs `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` item k, the
  ~60-script cloud-agnostic sweep): still `[ ]` open — still conflicting.
- **Items 5, 7, 8, 9, 10**: not independently re-verified this pass (no new evidence found or sought) — carried
  forward as still-conflicting per their last recorded state. A future batch4 should re-check these explicitly.

**Conclusion**: zero of batch1's 10 Deferred conflict-gated items convert to a batch3 todo this round.

## Rules this plan follows

- Every todo ends with `Source: <doc>.md` and a **Done when** clause.
- Checked pairwise across all 6 todos and against every open todo in `infra_satellite_ao_dispatch_batch1_2026_07_26.md`
  (27 todos) and `infra_satellite_ao_dispatch_batch2_2026_07_27.md` (9 todos) for file-level collision — zero found
  among these 6 (one candidate, `vm_launcher_class_b_no_stall_kill_gap_2026_07_27.md`, DID collide with batch1's
  still-open todo 8 on `deployment-service/scripts/vm/lib/launcher_common.sh` and was deferred instead — see
  `## Deferred` below).
- `sequential:` deliberately unset — these 6 touch disjoint files/repos and are independently dispatchable.

## Todos

- [ ] [TEST] P1. **Build real E2E coverage for alerting-service, deployment-service, and trading-agent-service (3
      independent repo-scoped builds, combined into one todo since they share one source doc).** (a) **alerting-service**
      (P1): add a real end-to-end test exercising the live alert pipeline (ingest → classify → dispatch/suppress),
      not just unit-level mocks. (b) **deployment-service** (P1): add a real E2E test driving an actual VM-launcher
      dry-run path end-to-end. (c) **trading-agent-service** (P2): create a net-new `tests/e2e/` directory (none
      exists today) with at least one real end-to-end scenario. Each harness must exercise real code paths, not just
      re-mock what unit tests already cover. **Done when**: all three repos have a passing E2E test file exercising a
      real cross-component path, each repo's `quality-gates.sh` is green, and the source doc's three checkboxes are
      flippable with the new test file paths cited. Repos: alerting-service, deployment-service,
      trading-agent-service. Source: `e2e_coverage_gaps_alerting_deployment_trading_agent_2026_07_27.md`.

- [ ] [BACKEND] P2. **Fix the fleet git-health `not_clean_since` staleness gap (3-step chain, combined).** (1) Trace
      `scripts/dev/slot-git-status-report.sh` to confirm whether the `not_clean_since`/dirty-transition timestamp it
      posts is captured fresh each run or is a fixed/stale value carried forward. (2) Audit agent-orchestrator's
      `GET /api/fleet/git-health` aggregation to confirm it surfaces a per-(host, slot, repo) `not_clean_since`
      rather than a collapsed global value. (3) Based on (1)+(2)'s findings, fix the upstream timestamp source, or
      add a new "last observed dirty transition" field alongside the existing hysteresis-gated `not_clean_since` —
      whichever the findings indicate is the real gap. **Done when**: the trace + audit findings are recorded with
      evidence, the fix (or the added field) is shipped, and a test proves the per-(host,slot,repo) value is
      genuinely fresh, not fixed. Repo: agent-orchestrator. Source:
      `issues/git_health_not_clean_since_pinned_constant_2026_07_27.md`.

- [ ] [CODE] P2. **Pay down the 15 baselined legacy bucket-template literals (21 occurrences, 6 repos).** Route each
      literal through `resolve_bucket_name(...)` and delete its corresponding entry from
      `check_no_explicit_project_id_bucket_baseline.json`, working asset-group by asset-group as the source doc's own
      Disposition section names (features-onchain, features-calendar, features-store, features-sports,
      instruments-store-tradfi legacy-bucket decommission order) — do NOT wait for a separate "decommission" event if
      the literal can be safely routed through `resolve_bucket_name` today; only genuinely-still-legacy buckets stay
      baselined. **Done when**: `check_no_explicit_project_id_bucket_baseline.json` has 0 remaining entries for
      literals that were safely routable, each touched repo's QG is green, and any literal that must stay baselined
      (genuine legacy bucket, not yet decommissioned) is explicitly named with why. Repos: unified-trading-pm,
      unified-trading-library, deployment-service, features-service, execution-service, ml-service. Source:
      `issues/legacy_bucket_template_literals_2026_07_16.md`.

- [ ] [REVIEW] P2. **Close the deployment-api zombie-watchdog Dockerfile fix's verification gap (evidence-only, no
      new code expected).** The production-stage `COPY vm_zombie_watchdog.py` + `scripts/recovery/` fix already
      shipped (commit `fa54159`), but the todo isn't closeable yet: (1) confirm deployment-api's
      `live-defi-rollout`→`main` promotion (PR 410) has actually gone green — cite a resolving `cloudbuild=<id>`
      evidence per the runtime-verification HARD RULE, not just a re-read of the PR; (2) live-confirm the
      auto-kill/auto-relaunch actuators actually fire post-deploy (a real triggered stall/kill event, not just "the
      file is present in the image"). **Do NOT touch `heartbeat_stall_watcher.py`'s matching logic** — a sibling
      todo below owns that file. **Done when**: a resolving `cloudbuild=<id>` is cited for the PR 410 promotion, and
      a live-triggered actuator firing is confirmed with evidence, and the source doc's Todo 1 is flippable citing
      both. Repos: deployment-api, deployment-service. Source:
      `issues/heartbeat_stall_watcher_autokill_never_works_in_production_2026_07_27.md` (Todo 1 only — Todo 4 stays
      `[OPERATOR]`-gated on a VM machine-sizing decision, not drafted here).

- [ ] [BACKEND] P2. **Close the migration-VM hung-detection monitoring gap's residual todo 7 (2-part, combined).**
      (a) Individually verify each of the ~35 unverified one-off/recon/audit-named launcher scripts for Class-A
      stall-kill coverage and safe inclusion in `heartbeat_stall_watcher.py`'s `_is_backfill_vm()` naming match —
      check each for fleet-naming collision risk before adding it. (b) Fix the confirmed active mis-route in
      `launch-batch-live-recon-cron-vm.sh`: its `VM_NAME` contains the literal `-live-` substring, tripping
      `_is_backfill_vm()`'s early-out to `False` despite being a batch cron, not a live-capture VM — narrow the
      early-out condition or add an explicit carve-out. **Scope guard**: this is the only todo in this batch touching
      `heartbeat_stall_watcher.py` — no other todo here edits it. **Done when**: all ~35 named launchers carry an
      explicit stall-kill-coverage verdict (included / excluded-with-reason), `launch-batch-live-recon-cron-vm.sh` is
      correctly classified as a batch cron (not live), and a regression test covers the corrected early-out
      condition. Repos: deployment-api, deployment-service. Source:
      `issues/migration_vm_hung_detection_monitoring_gap_2026_07_27.md` (Todo 7 only — Todos 1-6 already shipped).

- [ ] [BACKEND] P2. **Give `RelaunchStalledVm.relaunch()` a checkpoint-read/`START_DATE`-override step, mirroring
      `RelaunchPreemptedVm.relaunch()`'s existing logic.** Today every stall-triggered relaunch replays blind from
      the original launch params with zero checkpoint/resume logic (confirmed: full-file read of
      `deployment-service/scripts/recovery/relaunch_stalled_vm.py`, `RelaunchStalledVm.relaunch()` lines 106-227).
      Add the same `PROGRESS.json`-checkpoint read + monotonic-gated `START_DATE` override that
      `RelaunchPreemptedVm.relaunch()` already has (a **different file**, `relaunch_backfill_vm.py` — no overlap
      with this todo's target file). **Done when**: a unit test exercises both actuators against the same synthetic
      checkpoint fixture and confirms parity, with no regression to the existing no-checkpoint budget/paging
      behavior. Repo: deployment-service. Source:
      `issues/relaunch_stalled_vm_no_checkpoint_resume_gap_2026_07_27.md`.

## Deferred — held back, with the reason

**CONFLICT-GATED** (a competing live claim on the same file — re-checkable once the other side clears):

1. **`vm_launcher_class_b_no_stall_kill_gap_2026_07_27.md`** (3 open `[HUMAN]` todos: add stall-timeout auto-kill to
   `lc_log_upload_trap_block` or migrate 8 Class-B launchers to the Class-A route; extend
   `heartbeat_stall_watcher.py`'s naming heuristic for 6 doubly-unprotected launchers; re-prioritize 2 daily-cron
   launchers). Its primary fix target is `deployment-service/scripts/vm/lib/launcher_common.sh`'s
   `lc_log_upload_trap_block()` (line 1028) — the SAME FILE `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s own
   still-open todo 8 ("the launcher's two best-effort GCS writes") already claims. Drafting this now would race
   batch1's own in-flight work on the identical file. Re-check once batch1's todo 8 lands.

**ORPHANED BUT NOT AO-ELIGIBLE** (real remaining work, but a human/operator judgment call, not a worker-bounded
outcome — reported, not drafted):

2. **`issues/codex_ssot_audit_phase3_hold_vs_reclassify_contradiction_2026_07_27.md`** — one `[OPERATOR-DECISION] P1`
   todo: rule on whether the 2026-06-01 FIX-STALE-only hold on `codex_vs_repo_docs_ssot_audit_2026_06_01`'s Phase-3/4
   REDIRECT/DELETE apply is lifted, still in force, or lift-and-redispatch-to-opus. Genuine standing governance call.
3. **`issues/deployment_api_inventory_alert_gate_ondemand_only_2026_07_27.md`** — one `[HUMAN] P2` todo posing an open
   design tradeoff (reuse the existing inventory endpoint vs build a narrower alert-check-only path for a dedicated
   Cloud Scheduler cadence). The doc's own text frames this as a judgment call, not a determinable spec.
4. **`issues/gitignore_sync_script_destructive_due_to_stale_central_template_2026_07_27.md`** — 3 open todos; the
   middle one (reconcile `scripts/templates/.gitignore.central` against PM's live `.gitignore`) is real per-line
   judgment/merge work gating the other two, per the classifying agent's read — not drafted as a bounded todo.
5. **`issues/per_venue_scope_key_provisioning_incomplete_2026_07_23.md`** — 3 open `[HUMAN]` todos (a literal GCP
   secret-creation action, plus two open venue-scope-separation design calls). ALSO a likely mistag: content is
   entirely CeFi-execution-specific (Binance/Deribit/Bybit/OKX/Hyperliquid/Aster credential provisioning,
   `parent_epic: execution_master`) despite carrying `asset_group: [cefi, infrastructure]` — flagging for a retag
   check (drop `infrastructure`) rather than fixing it in this plan (out of scope for a dispatch-batch doc).

**ARCHIVABLE NOW** (fully shipped, frontmatter simply never flipped — `/plan-reconcile`'s territory, not touched
here):

6. **`issues/rotate_exchange_keys_stale_venue_registry_2026_07_23.md`** — all 3 tracked todos are genuinely done
   (full 34/34 live GCP verification 2026-07-27, a definitive dead/unwired invocation-path verdict, and the venue-list
   code fix shipped `deployment-service@6eed099`). Only `status`/`resolved_by` frontmatter is stale.
7. **`issues/capability_manifest_ml_models_probe_stale_import_2026_07_26.md`** — its one todo is `[x]` with a full
   shipped-and-verified completion narrative (3 repos, commit shas cited, green QG). Only `status`/`resolved_by`
   frontmatter is stale.

## Codex SSOTs

`/codex/06-coding-standards/quality-gates.md` · `/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md`
· `/codex/05-infrastructure/vm-launcher-runbook.md` · `/codex/11-project-management/plan-hygiene.md` ·
`plans/active/task_template.md` §4

## Progress Log

- **2026-07-28** — Drafted by `/ag-closeout-audit infra` (Autonomous/AO-dispatched mode, ag_closeout_auditor role,
  operator away). Phase 0 confirmed batch1 (27 todos, ~5 done) and batch2 (9 todos) both still active; re-checked all
  10 of batch1's conflict-gated Deferred items — none cleared enough to convert (2/3 partially cleared on the
  `base-library.sh` side only). Phase 1 ran a 13-agent Workflow classifying every infra-tranche doc created since
  batch1/batch2 (2026-07-16 through 2026-07-27): 2 archivable_now, 4 orphaned-not-AO-eligible, 1 orphaned-AO-eligible-
  but-conflict-gated, 6 orphaned-AO-eligible-and-conflict-clear. Drafted the 6 conflict-clear items here. Left
  `status: draft` deliberately — the flip to `active` is the operator's call.
