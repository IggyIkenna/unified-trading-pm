---
doc_type: plan
title:
  Cross-cutting satellite AO batch 4 — infrastructure_master bounded residuals extracted from the 2026-08-09
  satellite-batch-extraction sweep
summary: >-
  Fourth AO-dispatch batch for the cross-cutting tranche, produced by the same 2026-08-09 satellite-batch-extraction
  pass as batches 2-3 — this one pulls 3 bounded items out of `infrastructure_master` source docs:
  `issues/ag_closeout_audit_cross_cutting_parked_2026_08_08.md` (2 self-contained tooling/hygiene items — the other 13
  open items in that doc, and every open item in its 4 sibling dated-parked docs, are cross-tranche `asset_group` retag
  handoffs left untouched per this workspace's own concurrent-sharded-worker routing convention) and
  `issues/shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md` (1 documentation item — its 2 code-fix
  items stay behind on a confirmed cross-doc overlap with
  `orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md`, both touching the same shared mutable gcloud config
  state). `bucket_estate_consolidation_closeout_2026_07_24.md` and
  `cross_cutting_strategy_execution_determinism_2026_07_26.md` (also `infrastructure_master`) yielded zero extractable
  items — see the Progress Log below.
status: complete # archived 2026-08-09 — every todo done; close-out verified by finalize plan
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-4, satellite-docs, infrastructure-master]
related:
  [
    /plans/active/issues/ag_closeout_audit_cross_cutting_parked_2026_08_08.md,
    /plans/active/issues/shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch4_2026_08_09_finalize.md,
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
locked_by:
locked_since:
supersedes:
superseded_by: cross_cutting_satellite_ao_dispatch_batch4_2026_08_09_finalize
depends_on: []
context_scope:
  [
    /plans/active/issues/ag_closeout_audit_cross_cutting_parked_2026_08_08.md,
    /plans/active/issues/shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
source: >-
  Satellite-batch-extraction sweep 2026-08-09 (8 parallel classification agents over the cross-cutting tranche's 27
  RECLASSIFY-non-qualifying NA docs), mirroring `/ag-closeout-audit`'s satellite-batch pattern.
assigned_role: infra
effort: medium
sequential: false
drift_direction: advance-code
---

# Cross-cutting satellite AO batch 4 (infrastructure_master) — bounded-item extraction

> **Status: active.** All 3 todos below are same-priority-independent and touch distinct files — no
> `sequential`/`gate_on_depends` needed.

## Todos

- [x] ✅ [SCRIPT] P3. Widen `generate_ag_closeout_audit_candidates.py`'s cross-cutting tranche membership test
      (currently `parent_epic in DATA_EPICS or basename in cited`) so it no longer silently excludes never-cited docs
      carrying a non-data `parent_epic` from the candidate pool — the doc's own Process finding 2 diagnosed this exact
      class of previously-invisible candidate. Repo: unified-trading-pm. Source:
      `issues/ag_closeout_audit_cross_cutting_parked_2026_08_08.md` (membership-test-widening item). Done when: the
      generator's membership test captures the diagnosed class (docs `check_ag_closeout_linkage.py`'s reachability check
      flags as members but today's narrower test misses), verified by re-running Phase 0 and confirming those
      previously-invisible candidates now appear in the member list. — unified-trading-pm@3829eea18. Membership test for
      `t == "cross-cutting"` is now plain `"cross-cutting" in asset_group` (matching every other tranche), dropping the
      `parent_epic in DATA_EPICS` gate + the now-unused `DATA_EPICS` constant; citation status still drives the
      cited/never-cited split via `cited_in_covering_doc`, not membership. Verified: `--tranche cross-cutting --json`
      `total_members` 103→130, `never_cited_count` 19→34 on the live corpus (27 newly-visible docs, e.g.
      `plans/active/ag_closeout_audit_rollout_2026_07_25.md`). New regression test
      `test_cross_cutting_membership_not_gated_on_data_epic_or_citation` added; all 9 tests in
      `tests/unit/test_generate_ag_closeout_audit_candidates.py` pass; full `quality-gates.sh` green.
- [x] ✅ [DOC] P2. Line-cap-split `cross_cutting_consolidated_closeout_2026_07_25.md` (999/1000 lines, 1 line of margin
      after its latest addition) — fork a Track/phase-named child doc with `depends_on` pointing back, mirroring how the
      other 5 asset-group consolidated-closeout docs were already split. Repo: unified-trading-pm. Source:
      `issues/ag_closeout_audit_cross_cutting_parked_2026_08_08.md` (line-cap-split item). Done when: the parent doc is
      back under ~700 lines with a forked child covering the trimmed content, and the parent's `depends_on`/child
      pointer is wired per `task_template.md` finding I. — unified-trading-pm@28d6b07a4. Parent trimmed 1007→716 lines
      (had grown past the 1000L hard cap since this todo was authored). Forked Tracks 14/18-22 (still-open,
      observability/self-monitoring-themed) to `cross_cutting_closeout_observability_and_monitoring_2026_08_09.md`;
      forked Track 15 (closed) + the full Progress Log through 2026-08-08 to
      `plans/archive/2026_08/cross_cutting_consolidated_closeout_history_2026_08_09.md` (status: complete, per
      `check_terminal_status_archived.py` — a terminal-status doc belongs in plans/archive/, not plans/active/).
      `depends_on`/`related`/Split-notice wired on the parent per finding I. Verified: `check_line_caps.sh`,
      `check_frontmatter_yaml.py`, `check_reference_paths.py`, `check_na_corpus_ratchet.py`,
      `check_terminal_status_archived.py` all clean on the 3 touched files (2 pre-existing unrelated corpus failures —
      `check_archive_candidates`, `check_prosewrap_padding` — confirmed not caused by this change).
- [x] ✅ [DOC] P3. Document the `gcloud config set account` host-wide-mutation hazard in
      `/codex/05-infrastructure/per-tab-worktrees.md` § "Multi-agent safety" (or a new subsection), regardless of which
      code-fix direction eventually lands for the underlying clobbering bug: state that `gcloud config set     account`
      mutates shared host state (not session-scoped), that a worker switching identity should prefer a per-invocation
      `--account=`/`CLOUDSDK_CORE_ACCOUNT` override where tooling allows it, and that any other concurrent slot may
      change the ambient identity at any time. Repo: unified-trading-pm. Source:
      `issues/shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md` (hazard-documentation item). Done
      when: the codex doc's "Multi-agent safety" section (or a new subsection) states the hazard and the
      per-invocation-override recommendation in the terms above. — unified-trading-pm@de70cd5aa. Added item 5 to
      `per-tab-worktrees.md` § "What worktree isolation does NOT cover" (the doc's existing multi-agent-safety-gap
      catalogue, items 1-4) stating the host-wide `core/account` mutation hazard, the confirmed 2026-08-04 incident, the
      per-invocation `--account=`/`CLOUDSDK_CORE_ACCOUNT` override recommendation, and the
      any-concurrent-slot-can-flip-it-at-any-time caveat, per the terms specified in this todo.

## Codex SSOTs

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility",
`/codex/05-infrastructure/per-tab-worktrees.md`.

## Progress Log

- **2026-08-09**: Batch authored via the satellite-batch-extraction sweep. 3 items extracted from 2
  `infrastructure_master` issue docs. **Zero-yield docs in this parent_epic, confirmed via full end-to-end read**:
  `bucket_estate_consolidation_closeout_2026_07_24.md` (both open items gated — an unscoped multi-repo
  observability-chain item, and a human-only whole-bucket delete);
  `cross_cutting_strategy_execution_determinism_2026_07_26.md` (sole open item is itself "author a new AO dispatch
  batch," gated by CLAUDE.md's plan-destination HARD RULE);
  `issues/ag_closeout_audit_cross_cutting_parked_2026_08_01.md`/`_08_02.md`/`_08_06.md`/`_08_07.md` (every open item is
  a cross-tranche `asset_group` retag handoff, correctly left for the owning tranche's own audit per this workspace's
  concurrent-sharded-worker routing convention — dispatching a retag from the wrong tranche would write into another
  tranche's namespace). One item flagged by the classifying agent but NOT actioned anywhere in this batch, since it
  needs an operator decision, not dispatch: `issues/ag_closeout_audit_cross_cutting_parked_2026_08_07.md` and
  `_08_08.md` both flag `issues/deployment_api_prod_disable_auth_true_2026_08_06.md` (a live unauthenticated production
  Cloud Run exposure) as unretagged for 3+ consecutive days — this is a pre-existing, already-tracked finding this sweep
  did not originate; surfacing it here only because it recurred across 2 of this batch's source docs and appears
  un-escalated as of this sweep.
- **2026-08-09**: Shipped the P3 `[SCRIPT]` membership-widening todo — unified-trading-pm@3829eea18. Full details on the
  flipped checkbox above; QG green, 9/9 unit tests pass.

> **ARCHIVED 2026-08-09** — all 3 todos done, `locked_by` empty. Archived via the standard 6-step ritual per
> `/plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch4_2026_08_09_finalize.md`. superseded_by:
> `cross_cutting_satellite_ao_dispatch_batch4_2026_08_09_finalize`.
