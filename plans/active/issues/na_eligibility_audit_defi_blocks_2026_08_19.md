---
doc_type: issue
title: na-eligibility-audit defi tranche 2026-08-19 — consolidated operator questions and carry-forward MISCLASSIFIED_LIKELY_AO_ELIGIBLE list
summary: >-
  Phase 1b consolidation artifact for the 2026-08-19 /na-eligibility-audit defi run (11 docs classified: 8
  defi-owned in-scope, 3 report-only from cefi/cross-cutting/ao tranches). Not a work item itself — a batchable
  index of the DISTINCT operator-decision asks found across the tranche, plus the MISCLASSIFIED_LIKELY_AO_ELIGIBLE
  items still genuinely unresolved after this run's own RECLASSIFY pass. Supersedes
  na_eligibility_audit_defi_blocks_2026_08_18.md.
status: open
nature: issue
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [defi, na-eligibility-audit, operator-questions, credential-ask, misclassified-carry-forward]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/na_eligibility_audit_defi_blocks_2026_08_18.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: 2026-08-19
last_updated: 2026-08-19
# was: defi_master (epic-assignment audit 2026-08-19) -- same as its 2026-08-16/17/18
parent_epic: plan_hygiene_master
  # predecessors: a na-eligibility-audit Phase 1b consolidation run report over the defi tranche, not defi
  # asset-group content itself
assigned_vm: NA
execution_scope: local-only
priority: P3
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
context_scope:
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
supersedes: na_eligibility_audit_defi_blocks_2026_08_18
source: >-
  /na-eligibility-audit defi (2026-08-19, dispatch agt-88e4bb, slot 29) — Phase 1b consolidation across all 11
  classified docs (8 defi-owned + 3 report-only from cefi/cross-cutting/ao tranches).
---

# na-eligibility-audit defi tranche 2026-08-19 — blocks + carry-forward index

## Resolved this run (closed-by-citation or narrowed with live evidence, all additive edits)

1. **`defi_migration_audit_log_2026_07_24.md`** — closed the "VERIFY-then-MIGRATE the unique orphan gaps" checkbox
   by citation (every sub-item's action already lives on `defi_orphan_bucket_delete_list_includes_canonical_bucket_2026_08_15.md`'s
   own `[OPERATOR]` todo, or is resolved-as-moot). Narrowed the DeFi-collection-gaps retag item per its own
   2026-08-16 "next hands-on pass" ask — split into a bounded scheduler-wiring residual (see MISCLASSIFIED list
   below) and a `CREDENTIAL_BLOCKED` sub-feature (see Credential asks below). 7 → 6 open todos.
2. **`plan_reconciler_findings_defi_2026_08_17.md`** — closed its remaining "AO-dispatch-readiness tagging gaps"
   pointer by citation: the same underlying gap is already tracked in more detail (with a `[WORKER REC]`) in
   `plan_reconciler_findings_defi_master_epic_2026_08_18.md`'s Parked item 4 — this journal's own copy was pure
   duplication. 1 → 0 open todos; this run-journal's own remaining work is now fully closed (stays `assigned_vm: NA`,
   not archived, per prior precedent for run-journal docs).
3. **`mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md`** — live-verified the per-slot RSS-ceiling
   question from a slot on the same host: `ORCHESTRATOR_WORKER_MEMORY_MAX` is confirmed NOT armed (empty env var;
   `/proc/self/cgroup` shows the shared `orchestrator.service` scope, not an individual worker scope), and
   architecturally WOULD cover an ad-hoc script subprocess if armed (cgroup-scope inheritance). The investigative
   half of this todo is now answered with certainty; what remains is a live production-safety sizing decision
   (arm it, at what per-worker cap), genuinely operator-gated — stays `KEEP-NA`, 2 open todos unchanged (annotation
   only, nothing extracted).

## Operator questions (deduped by distinct ask, not one row per doc)

1. **Elysium delivery decisions (9 distinct asks, unchanged since 2026-08-16/17/18, one doc)** —
   `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`. Not in this run's in-scope set
   (incremental_skip=true) — carried forward unverified against fresh state, exactly as the 2026-08-18 run left it.
2. **`strategy_service_centralization_fixes_2026_08_16.md`'s `sequential: true` scope** — unchanged since
   2026-08-17/18, not in today's in-scope set — carried forward unverified.
3. **Non-defi-owned, reported only** (this run's own reads, primary-owner rule — infra/cefi/cross-cutting/ao own
   these, no writes made):
   - `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` (cefi-owned) — read in full this run;
     KEEP-NA valid, matches cefi's own last verdict (2026-08-16 RECLASSIFY-SPLIT, 7 items remain genuinely NA,
     unchanged since).
   - `instruments_remaining_work_audit_2026_07_10.md` (cross-cutting-owned) — read in full this run; KEEP-NA valid,
     matches FOUR independent prior tranche confirmations (2026-07-30 sports, 2026-08-06, 2026-08-07 cross-cutting,
     2026-08-17 cross-cutting with body-hash marker) — a single-todo umbrella over 6 independently-scoped,
     partly-operator-gated workstreams, not one determinable outcome. A strong never-relitigate candidate.
   - `operator_action_items_consolidated_2026_08_08.md` (ao-owned) — read in full this run; KEEP-NA valid, matches
     the SAME-DAY 2026-08-19 ao-tranche marker already present in the doc itself (27 open items, all
     credential/GH-UI/git-stash-drop/judgment-fork calls).
   - Carried forward unchanged from 2026-08-18 (not in today's in-scope set, not independently re-verified):
     `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md` (cefi-owned), `defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md`
     (infra-owned), `estate_orphan_assessment_2026_07_21.md` (cefi-owned, todo 6 still contested).

## Credential/access asks

- **`helius-api-key`** (free-tier self-signup) — unblocks the per-validator `native_staking_rates` sub-feature in
  `defi_migration_audit_log_2026_07_24.md` (the aggregate feature is already code-complete and only needs the
  scheduler-wiring todo below, no credential). Not a paid ask — a quick operator self-signup.

## MISCLASSIFIED_LIKELY_AO_ELIGIBLE — carry-forward for the NEXT defi run only

Per the skill's close-the-loop rule, every item below is a mandatory Phase-1 input for the next
`/na-eligibility-audit defi` run.

**New this run**: `defi_migration_audit_log_2026_07_24.md`'s native_staking_rates (aggregate) Cloud Scheduler cron —
wire a `defi_collection_scheduler.tf` entry mirroring the existing `collect-eigenlayer-rewards` cron. Bounded,
mechanical, matches an established terraform pattern in the same file. Not extracted this run (a single-item
satellite-batch extraction felt like more process overhead than the item warranted given this run's remaining
scope; also genuinely low-risk to leave one more cycle given the source doc's own history of caution on this exact
paragraph) — a future run or an operator can extract it directly.

**Unchanged, not re-touched this run** (primary-owner rule — not defi's job, or not in today's in-scope set):

- `defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md` (infra-owned) todo 1 — still infra tranche's
  job to promote via a per-todo split.
- `estate_orphan_assessment_2026_07_21.md` (cefi-owned) todo 6 — not in today's defi Phase-0 in-scope set; still
  cefi tranche's job, still contested.

## Progress Log

- **2026-08-19 (na-eligibility-audit, defi tranche, dispatch agt-88e4bb, slot 29)**: Phase 0 found 11 of 62
  defi-tranche-candidate docs in scope (51 already-verdicted-and-unchanged). Of the 11: 8 defi-owned (4 with real
  open-todo content — see Resolved-this-run above for 3 of them; the 4th, `plan_reconciler_findings_defi_master_epic_2026_08_18.md`,
  got a KEEP-NA marker citing established splitting-a-plan-is-operator-gated precedent; 4 more were 0-open-todo
  report/run-journal artifacts, outside the verdict rubric's population, no action per established precedent) + 3
  report-only docs from cefi/cross-cutting/ao (read in full, no writes, primary-owner rule — see Operator questions
  above). Zero conflicts required operator escalation this run. Ratchet checked at run end (see this run's `/done`
  evidence).
- **context-scout 2026-08-20**: refreshed context_scope (2 entries)
