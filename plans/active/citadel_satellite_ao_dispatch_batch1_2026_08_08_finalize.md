---
doc_type: plan
title: Citadel satellite AO batch 1 — finalize (reconcile source doc + re-check the held-back conflict + archive)
summary: >-
  Gated closeout for citadel_satellite_ao_dispatch_batch1_2026_08_08.md — machine-held via depends_on + gate_on_depends:
  true until that plan's 7 todos are done. Mirrors the prediction/cefi/defi/sports satellite-batch finalize pattern
  (reconcile the source doc's checkboxes/register, re-check the deferred/held-back population for cleared gates, then
  archive). Authored `status: active` (not draft) per the 2026-07-30 no-double-gate finding — `gate_on_depends` alone
  already machine-holds every task here until batch1's own todos land, regardless of batch1's own draft/active status; a
  finalize plan carries no independent judgment call.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [reconciliation, paper-trading, ao-dispatch, close-out, batch-1, citadel, archival]
related:
  [
    /plans/active/citadel_satellite_ao_dispatch_batch1_2026_08_08.md,
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /plans/active/crypto_alpha_research_2026_07_24.md,
    /plans/epics/batch_live_symmetry_master.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: batch_live_symmetry_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [citadel_satellite_ao_dispatch_batch1_2026_08_08]
gate_on_depends: true
source: >-
  Drafted alongside citadel_satellite_ao_dispatch_batch1_2026_08_08.md, per task_template.md §4's finalize-plan-
  coverage rule — every AO-dispatched plan needs a companion gated finalize plan.
assigned_role: backend_engineer
effort: medium
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/citadel_satellite_ao_dispatch_batch1_2026_08_08.md,
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /plans/active/crypto_alpha_research_2026_07_24.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Citadel satellite AO batch 1 — finalize

> **Machine-gated on `citadel_satellite_ao_dispatch_batch1_2026_08_08.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 7 tasks of that plan are `done`. `sequential: true` because
> todo 2 (archival) must run after todo 1 (reconciliation).

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile the source doc.** batch1's 7 todos each cite
      `citadel_paper_batch_live_reconciliation_2026_06_19.md` Phase 2 / Phase 11 items P2.1, P2.2, P1.6, P2.11.16,
      P2.11.20, P2.11.18, P2.14 as their `Source:`. For each of the 7, confirm the corresponding `- [ ]` checkbox in the
      source doc is flipped `- [x] ✅` with a commit citation (or, if the corpus convention by then prefers a pointer
      instead of a flip, confirm a pointer to this batch's own commit exists) — do not trust batch1's own copy of the
      evidence line, re-verify the cited `<repo>@<sha>` actually exists and resolves. Also confirm the source doc's
      register § A (the "Agent-shippable infra/code" list) no longer lists these 7 items as open, and that the 4 stale
      register bullets this batch's Progress Log flagged (already-migrated-to-`crypto_alpha_research` items) were
      corrected in the source doc per this batch's Progress Log note. **Done when**: all 7 source-doc checkboxes are
      confirmed flipped with resolving commit citations, the register is confirmed corrected, and this plan's own
      Progress Log records the exact commit citation for each.

- [x] ✅ [REVIEW] P2. **Re-check the held-back conflict (P2.11.15) for a cleared gate.** batch1's `## Deferred` section
      held back "cs-leg longer-horizon TARGET retrain in `_panel.py`" (P2.11.15) because it near-verbatim-duplicated
      `crypto_alpha_research_2026_07_24.md`'s own open `[RESEARCH] P2` todo (line ~536 as of 2026-08-08 — re-locate by
      content, not line number, since it may have shifted). Check whether that `crypto_alpha_research` todo has since
      been executed (retrain done, cs Sharpe / 2026-drag verdict recorded) — if so, confirm
      `citadel_paper_batch_live_reconciliation_2026_06_19.md`'s own P2.11.15 checkbox should now also flip (citing the
      SAME evidence, not a duplicate re-run) and do so; if still open, leave both as-is (no action needed, this is not a
      failure state). Also re-check whether P2.11.18's scope-trimmed retrain sub-step (deferred in batch1 for the same
      reason) has become executable now that the P2.11.15 gate's status is known — if the retrain has landed, note
      whether P2.11.18's full original scope (including the retrain) should be considered complete too, or whether a
      follow-up todo is still needed; file a new tracked `- [ ]` todo (never prose) in the appropriate plan if one is.
      **Done when**: this plan's own Progress Log records the checked status of both the P2.11.15 gate and any resulting
      follow-up action (checkbox flip, new todo filed, or explicitly "still open, no action").

- [ ] [DOC] P3. **Archive batch1 + this finalize plan.** Once the source doc is confirmed reconciled (todo 1) and the
      held-back conflict is re-checked (todo 2), archive both `citadel_satellite_ao_dispatch_batch1_2026_08_08.md` and
      this finalize doc to `plans/archive/2026_08/` per the 6-step archival ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) — update every referrer (this doc's own
      `related:`, `citadel_paper_batch_live_reconciliation_2026_06_19.md`'s `related:` if it names batch1,
      `plans/epics/batch_live_symmetry_master.md` if it enumerates satellite batches). **Done when**: both files are in
      `plans/archive/2026_08/`, `regenerate_active_plan_inventory.py` shows 0 orphaned referrers, and
      `run_hygiene_sweep.sh` is green.

## Progress Log

- 2026-08-08 (interactive session): drafted alongside batch1, per the finalize-plan-coverage rule. `status: active` from
  the start (not draft) — `gate_on_depends: true` already fully holds every todo above until batch1's own 7 todos are
  `done`, so no second manual flip is needed later (2026-07-30 no-double-gate finding,
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`).
- **2026-08-11 (slot 27, P1 — Reconcile the source doc)**: independently re-verified all 7 batch1 todos against the
  source doc `citadel_paper_batch_live_reconciliation_2026_06_19.md`. Findings:
  1. **P2.1** (trade_key + fill fields) — ✅ batch1 checkbox flipped. Source doc Phase 2: correctly converted to
     non-ingestable pointer line `→ moved to citadel_satellite_ao_dispatch_batch1_2026_08_08.md` (not a checkbox — per
     `task_template.md` finding H). SHA `execution-service@08808415` verified ancestor of `origin/live-defi-rollout`.
  2. **P2.2** (colocated_engine fill records) — ✅ batch1 checkbox flipped. Source doc Phase 2: pointer line (same
     pattern). SHA `strategy-service@f1a98416` verified on origin.
  3. **P1.6** (GroupC smart-fill handoff) — ✅ batch1 checkbox flipped. Source doc Phase 11: pointer line
     `→ moved verbatim to citadel_satellite_ao_dispatch_batch1_2026_08_08.md`. SHA `execution-service@b2b41038` verified
     on origin.
  4. **P2.11.16** (BTC trend feature corpus recompute) — ✅ batch1 checkbox flipped (GCS-verified 2026-08-11, slot 9:
     `btc_trailing_return_{1m,3m,6m,12m}` + `btc_realized_vol` non-null in prod GCS; availability-index rows
     `capture_status=captured`). Source doc Phase 11: pointer line.
  5. **P2.11.20** (TSMOM_BTC_CTA capability wiring) — ✅ batch1 checkbox flipped. Source doc Phase 11: pointer line. SHA
     `unified-trading-pm@bbaf01e17` verified on origin.
  6. **P2.11.18** (intraday BTC mean-reversion cs-ML feature corpus recompute, scope-trimmed) — ✅ batch1 checkbox
     flipped (GCS-verified 2026-08-10, slot 7: `reversion_zscore_60m`/`240m` non-null in prod GCS; drift-check QG
     green). Source doc Phase 11: pointer line noting scope-trimmed extraction.
  7. **P2.14** (UI selector 145-strategy run) — ✅ batch1 checkbox flipped. Source doc Phase 11: pointer line. SHA
     `unified-trading-system-ui@a7140a9a` verified on origin. **Register § A**: confirmed corrected — "EXTRACTED
     2026-08-08" header with pointer text; all 7 items listed as extracted (not as open `- [ ]` checkboxes); the 4 stale
     bullets (`_mom_tb.py` bug, combined-book vol-norm bug, cs ensemble `alt_*`/`altfull_*` gap, HYPE+post-2024-cohort
     gap) are explicitly removed with a dated correction note. **Verdict**: all 7 items reconciled. Source doc uses
     pointer-line convention (correct per corpus rule); batch1 checkboxes are the live dispatchable todos and all 7 are
     flipped with verified evidence.
- **2026-08-11 (slot 27, P2 — Re-check the held-back conflict P2.11.15)**: checked `crypto_alpha_research_2026_07_24.md`
  for the `[RESEARCH] P2` todo that P2.11.15 duplicates. The todo ("Apply the cs denoise + tsmom-long-only to the
  production legs — cs: `ewm(span≈7)` on the ML book **(or a longer-horizon target retrain in `_panel.py`)**") is still
  open (`- [ ]`), located at the "leg-quality audit 2026-06-21" follow-up block (moved from its 2026-08-08 position at
  line ~536 — repoint by content not line number confirmed). **Gate NOT cleared — retrain not yet executed.** Source
  doc's P2.11.15 remains correctly `- [ ]` (open, not extracted, still `assigned_vm: NA`). No action needed — this is
  not a failure state per the plan's own done-when. **P2.11.18 retrain sub-step**: also remains not executable (still
  coupled to P2.11.15's gate; `crypto_alpha_research` P2 line still open). No new follow-up todo needed — the existing
  `crypto_alpha_research` todo already covers both. **Verdict**: still open, no action.
