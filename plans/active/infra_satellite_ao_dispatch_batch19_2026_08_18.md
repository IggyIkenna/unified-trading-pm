---
doc_type: plan
title: Infra satellite — na-eligibility-audit RECLASSIFY_SPLIT extraction batch (batch 19, single-todo)
summary: >-
  Single-todo extraction from the infra tranche's 2026-08-18 `/na-eligibility-audit` run — the bounded, mechanical
  half of `issues/archival_referrer_codex_redirect_bulk_cleanup_2026_08_17.md`'s todo 1 (work the
  `check_active_refs_archived_plans.py` corpus-wide baseline down from 925 toward 0, per that doc's own
  already-written, self-sufficient "Dispatch prompt" section). The source doc's own todo 2 (a P3 "consider adding
  --diff-base mode later" forward-looking design question) is NOT extracted — stays `assigned_vm: NA` on the source
  doc. Conflict-checked: grepped every active plan for `check_active_refs_archived_plans` — only the source doc
  itself references the mechanism (it was only created 2026-08-17, ratchet baseline seeded same day); this is its
  first dispatch. No finalize twin, per the established single-todo carve-out precedent
  (`infra_satellite_ao_dispatch_batch4_2026_07_31.md` / `batch5_2026_08_01.md`).
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

# Infra satellite — archived-plan referrer cleanup (batch 19, single-todo)

> **Fresh carve-out, single-todo, no finalize twin** (same pattern as batch4/batch5). Extracted from
> `issues/archival_referrer_codex_redirect_bulk_cleanup_2026_08_17.md` todo 1 — that doc's own body already carries
> a complete, self-sufficient dispatch prompt (§ "Dispatch prompt"). The todo below is a pointer to it plus
> extraction provenance, not a re-derivation — read the source doc's "Dispatch prompt" section in full before
> starting; it is the authoritative step-by-step procedure.

## Todo

- [ ] [SCRIPT] P2. **Work `check_active_refs_archived_plans.py`'s baseline down from 925 toward 0** — follow
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

## Progress Log

- **na-eligibility-audit 2026-08-18** (infra tranche, dispatch agt-6a3d46): drafted. RECLASSIFY_SPLIT of
  `issues/archival_referrer_codex_redirect_bulk_cleanup_2026_08_17.md` todo 1 — conflict-check clear (grepped every
  active plan for `check_active_refs_archived_plans`; only the source doc itself references it; mechanism created
  2026-08-17, never previously dispatched). Todo 2 on the source doc (P3, "consider `--diff-base` mode later") is
  explicitly NOT extracted — it is a small forward-looking design question gated on "once the baseline reaches 0",
  not independently bounded today; stays `assigned_vm: NA` on the source doc.
