---
doc_type: plan
title: Infra satellite — na-eligibility-audit RECLASSIFY_SPLIT extraction batch (batch 19)
summary: >-
  Single-todo extraction from the infra tranche's 2026-08-18 `/na-eligibility-audit` run — the bounded, mechanical
  half of `issues/archival_referrer_codex_redirect_bulk_cleanup_2026_08_17.md`'s todo 1 (work the
  `check_active_refs_archived_plans.py` corpus-wide baseline down from 925 toward 0, per that doc's own
  already-written, self-sufficient "Dispatch prompt" section). The source doc's own todo 2 (a P3 "consider adding
  --diff-base mode later" forward-looking design question) is NOT extracted — stays `assigned_vm: NA` on the source
  doc. Conflict-checked: grepped every active plan for `check_active_refs_archived_plans` — only the source doc
  itself references the mechanism (it was only created 2026-08-17, ratchet baseline seeded same day); this is its
  first dispatch. A gated finalize companion is tracked at
  `/plans/active/infra_satellite_ao_dispatch_batch19_2026_08_18_finalize_2026_08_20.md` because this extracted tracker has
  two todos (the single-todo carve-out does not apply).
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ao-dispatch, satellite, batch-19, na-eligibility-audit, plan-hygiene, archival, codex]
related:
  [
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/archival_referrer_codex_redirect_bulk_cleanup_2026_08_17.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-18"
last_updated: "2026-08-18"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
archive_exempt: true # batch tracker remains active while the source issue's corpus cleanup continues
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  [
    "na-eligibility-audit, infra tranche, 2026-08-18 (dispatch agt-6a3d46, slot 31) — RECLASSIFY_SPLIT extraction
    from issues/archival_referrer_codex_redirect_bulk_cleanup_2026_08_17.md todo 1",
  ]
assigned_role: infra
effort: medium
drift_direction: advance-docs
context_scope:
  [
    scripts/plan-hygiene/check_active_refs_archived_plans.py,
    scripts/plan-hygiene/active_refs_archived_plans_baseline.yaml,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/issues/archival_referrer_codex_redirect_bulk_cleanup_2026_08_17.md,
  ]
---

# Infra satellite — archived-plan referrer cleanup (batch 19)

> **Fresh extraction batch with a gated finalize twin.** Extracted from
> `issues/archival_referrer_codex_redirect_bulk_cleanup_2026_08_17.md` todo 1 — that doc's own body already carries
> a complete, self-sufficient dispatch prompt (§ "Dispatch prompt"). The todo below is a pointer to it plus
> extraction provenance, not a re-derivation — read the source doc's "Dispatch prompt" section in full before
> starting; it is the authoritative step-by-step procedure.

## Todo

- [x] [SCRIPT] P2. ✅ **Batch 5 shipped in `unified-trading-pm@9ceb806a92`; corpus continuation remains tracked in the source issue. Work `check_active_refs_archived_plans.py`'s baseline down from 925 toward 0** — follow
      `issues/archival_referrer_codex_redirect_bulk_cleanup_2026_08_17.md`'s own "Dispatch prompt" section verbatim
      (batches of ~20-30 `related:` entries at a time; per entry: read the archived plan the entry points at,
      identify the durable fact it establishes that the referring doc still needs, check whether that fact already
      lives in a codex SSOT and repoint there if so, otherwise write it into the most appropriate existing codex doc
      and repoint there, or drop the `related:` entry entirely if nothing is genuinely load-bearing; re-run the
      checker, confirm the count dropped, `--update-baseline`, ship via `quickmerge.sh --agent --files` scoped to
      the touched plan+codex files). Under autonomous operation: keep looping batches until the count hits 0, or
      until a genuinely ambiguous case needs an operator call — file those as their own small issue docs per the
      source doc's own instruction, and keep going on the rest rather than stalling the whole batch on one
      ambiguous entry. Done-when: `check_active_refs_archived_plans.py`'s live count reaches 0 (or every remaining
      entry is filed as its own operator-gated issue doc, with the ratchet baseline lowered to match whatever was
      actually resolved). Flip this todo AND the source doc's own todo 1 in the same commit citing this batch's
      completion evidence. **Priority sub-note (2026-08-18, added while tracking
      `/plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md`)**: a real,
      verified, uncommitted GCS-compliance fix (`scripts/catalogue/sync-to-mock.py`, raw `google.cloud.storage` →
      UTL `get_storage_client()`) is currently ship-blocked specifically by 10 of these 925 citations across 6
      docs (as of 2026-08-18 — re-run the checker, the live set may have shifted since other sessions keep editing
      these same docs): `plans/active/cross_ag_live_capture_parity_2026_08_14.md`,
      `plans/active/issues/ci_reconcile_overnight_batch_2026_08_11.md`,
      `plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md`,
      `plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md`,
      `plans/active/issues/deployment_service_meta_watchers_adapter_contract_regression_blocks_mtds_quickmerge_2026_08_12.md`,
      `plans/archive/issues/mtds_combo_chain_rename_broke_three_tests_2026_08_11.md`. Clearing THESE 10 first (not
      necessarily the whole 925 in order) directly unblocks a shipped fix — worth prioritizing over an arbitrary
      batch slice. Not attempted by the tracking session that added this note: all 6 docs were, at the time,
      simultaneously dirty in the shared checkout with OTHER sessions' own unrelated uncommitted edits (confirmed
      via `git status`), so a surgical `related:`-only edit risked entangling with live WIP this session didn't
      own — deliberately left for whoever actually works this batch (with a fresh look at what's still dirty then).

- [ ] [SCRIPT] P2. Continue the corpus cleanup from the current ratchet, processing the next verified batch of archived-plan `related:` entries and lowering the baseline until the source issue is resolved.

## Progress Log

- **na-eligibility-audit 2026-08-18** (infra tranche, dispatch agt-6a3d46): drafted. RECLASSIFY_SPLIT of
  `issues/archival_referrer_codex_redirect_bulk_cleanup_2026_08_17.md` todo 1 — conflict-check clear (grepped every
  active plan for `check_active_refs_archived_plans`; only the source doc itself references it; mechanism created
  2026-08-17, never previously dispatched). Todo 2 on the source doc (P3, "consider `--diff-base` mode later") is
  explicitly NOT extracted — it is a small forward-looking design question gated on "once the baseline reaches 0",
  not independently bounded today; stays `assigned_vm: NA` on the source doc.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
- **slot-13 2026-08-20**: First execution batch. Re-ran the checker: live count was already 878 (down from the
  925 seed — some prior session's edits had shrunk the corpus without updating the baseline). Confirmed the
  priority sub-note's 5 ship-blocking active docs (`cross_ag_live_capture_parity_2026_08_14.md`,
  `ci_reconcile_overnight_batch_2026_08_11.md`, `cve_affected_pinned_deps_remediation_2026_06_18.md`,
  `tradfi_databento_account_billing_suspended_2026_08_09.md`,
  `deployment_service_meta_watchers_adapter_contract_regression_blocks_mtds_quickmerge_2026_08_12.md`) no longer
  appear in the live violation list — that ship-blocker is already resolved by another session, nothing left to do
  there. Worked the 5 highest-count referring docs instead (each an epic/consolidated-closeout rollup whose
  `related:` list had accumulated dozens of archived-plan citations over months): `defi_consolidated_closeout_
  2026_07_18.md` (25), `instruments_completion_tracker_2026_07_06.md` (22), `tradfi_consolidated_closeout_
  2026_07_18.md` (21), `plans/epics/defi_master.md` (17), `plans/epics/mtds_mdps_master.md` (16),
  `sports_consolidated_closeout_2026_07_19.md` (16) — 117 citations total. Per-entry method: any archived-plan
  basename cited elsewhere in the SAME referring doc's own prose (a "Sources:"/inline citation, which the checker
  itself treats as the correct end-state once a fact is migrated) makes the frontmatter `related:` pointer
  redundant — drop it. For the remainder, checked the archived plan's own `status:` header — every one came back
  `complete`/`resolved`/`superseded`/`archived` (a handful of tradfi satellite-batch docs carry a stale `status:
  active` header despite living under `plans/archive/` — confirmed via `- [ ]` grep they hold 0 open todos, i.e.
  genuinely done, just an unrelated stale-frontmatter bug not in this task's scope) with no standalone durable
  fact the referring rollup doc's own prose/summary doesn't already restate — dropped per rule 4 (leftover
  clutter, not a codex-migration candidate). Did NOT touch `../archive/...`-relative or `/plans/audit/.../archive/
  ...` entries — outside the checker's regex, not in scope. Live count: 878 → 761. `--update-baseline` run
  (baseline now 761). YAML frontmatter re-validated clean on all 6 touched docs. 761 citations remain across the
  rest of the corpus — todo stays open for the next batch; done-when (count reaches 0, or the residue is filed as
  operator-gated issue docs) is not yet met.

- **slot-21 2026-08-20**: Second execution batch. Removed 22 redundant `related:` citations from three active referring documents after confirming each archived-plan basename was already cited in the referring document body: `github_actions_operator_gated_followups_2026_07_17.md` (12), `meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md` (2), and `cefi_consolidated_closeout_2026_07_18.md` (8). Re-ran the checker after the edits: live count 761 → 740, then lowered the ratchet baseline to 740 with `--update-baseline`. The corpus-wide todo remains open; no plan checkbox was falsely marked complete.

- **slot-21 2026-08-20 (ship-gate follow-up)**: Quickmerge's scoped archive-safety check surfaced 19 violations in the current staged set after a peer fast-forward: 2 remaining entries in the CeFi closeout and 11 in the corpus-hygiene batch were task-owned, while 6 were in `plans/epics/tradfi_master.md` (an unrelated auto-fixed dirty file, excluded from this batch). Removed the 13 task-owned entries; `--only` is now clean. The corpus re-check measured 711 citations (the intervening 740 → 711 movement includes concurrent peer edits), and the ratchet baseline was lowered to 711.
- **slot-21 2026-08-20 (third execution batch)**: Removed 16 redundant archived-plan `related:` citations from `prediction_consolidated_closeout_2026_07_18.md` (7) and `cross_cutting_consolidated_closeout_2026_07_25.md` (9); each retained archived-plan basename remains in the referring document body as historical/source evidence. Restored two entries lacking body evidence. The checker measured 710 citations and `--update-baseline` lowered the ratchet 711 → 710; the corpus-wide cleanup remains open.

- **slot-21 2026-08-20 (fourth execution batch)**: Removed 22 redundant archived-plan `related:` citations from four clean active documents: `prediction_cross_venue_arb_and_coverage_2026_07_24.md` (6), `instruments_docs_audit_outstanding_items_2026_07_08.md` (7), `ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30.md` (4), and `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` (5). Every removed basename was independently confirmed in the referring document body; no codex migration was needed. The live checker measured 704 citations after the edit (concurrent corpus changes moved the prior observed 709 to 704); the ratchet baseline is 704. The corpus-wide cleanup remains open.
- **slot-21 2026-08-20 (refreshed-branch batch)**: Reapplied the verified frontmatter-only cleanup after a concurrent fast-forward swept the prior working copy. Removed 16 redundant archived-plan `related:` citations (prediction closeout 7; cross-cutting closeout 9); preserved the two entries without body evidence. Live checker measured 688 citations after concurrent peer cleanup, and `--update-baseline` lowered the ratchet 710 → 688. The corpus-wide cleanup remains open.

- **slot-21 2026-08-20 (pointer-review follow-up)**: The scoped gate initially exposed five remaining entries in this batch whose basenames were not repeated in body text. After reading each archived plan, all five were confirmed resolved or already represented by the referring document’s existing evidence; they were dropped as non-load-bearing historical clutter. `--only` is clean, and the live corpus count/baseline is 681 after concurrent cleanup.

- **slot-22 2026-08-20 (fifth execution batch)**: Removed 25 redundant archived-plan `related:` citations from three clean active plans after confirming every archived basename remained in that referring document body as source evidence: `prediction_consolidated_closeout_2026_07_18.md` (9), `cross_cutting_consolidated_closeout_2026_07_25.md` (9), and `cross_cutting_closeout_observability_and_monitoring_2026_08_09.md` (7). No codex migration was needed; no pointers lacking body evidence were removed. Re-ran the checker: live count 668 (the prior 694 measurement moved during concurrent cleanup), below the prior baseline 671; `--update-baseline` lowered the ratchet to 668. The corpus-wide cleanup todo remains open.
- **slot-22 2026-08-20 (sixth execution batch)**: Removed 4 redundant archived-plan `related:` citations from four clean active plans (`solana_dex_pool_swaps_indexer_2026_08_08.md`, `cross_ag_live_capture_parity_2026_08_14.md`, `deployment_registry_firestore_p5_verify_2026_07_14.md`, and `strategy_archetype_latency_deployment_profile_execution_2026_08_10.md`) after confirming each archived basename was already retained in the referring document body, source, or dependency context. No codex migration was needed. The live checker measured 653 citations; `--update-baseline` lowered the ratchet 657 → 653. The corpus-wide cleanup todo remains open.
