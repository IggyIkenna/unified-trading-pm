---
doc_type: plan
title: Solana dex_pool_swaps indexer — finalize
summary: >-
  Gated finalize companion for solana_dex_pool_swaps_indexer_2026_08_08.md — reconcile evidence back into the source
  scoping doc, re-check any deferred follow-up, then archive both docs per the standard 6-step ritual.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, solana, dex-pool-swaps, indexer, finalize]
related:
  [
    /plans/active/solana_dex_pool_swaps_indexer_2026_08_08.md,
    /plans/active/issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-20"
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
assigned_role: data_engineering
effort: high
drift_direction: none
depends_on: [solana_dex_pool_swaps_indexer_2026_08_08]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Authored alongside solana_dex_pool_swaps_indexer_2026_08_08.md per task_template.md's "Every AO-dispatched plan needs
  a gated finalize plan" rule (2026-07-24 operator ruling) — this plan is multi-todo, not the single-todo exemption.
context_scope:
  [
    /plans/active/solana_dex_pool_swaps_indexer_2026_08_08.md,
    /plans/active/issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md,
  ]
---

# Solana dex_pool_swaps indexer — finalize

> Gated on `solana_dex_pool_swaps_indexer_2026_08_08.md` (`depends_on` + `gate_on_depends: true`) — every task in THIS
> plan waits until every task in the named plan is done.

## Todos

- [ ] [REVIEW] P2. **Reconcile evidence into `/plans/active/issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md`** — re-verify every commit cited by `solana_dex_pool_swaps_indexer_2026_08_08.md`'s completed todos actually exists (`git show <sha>` / `git merge-base --is-ancestor`, never trust the plan's own citation blind), then update that scoping doc's "Open actions" todo + Progress Log to
      point at the finished implementation plan, closing that doc's own sole open item by citation. Repo:
      unified-trading-pm.
- [ ] [DOC] P2. **Run the standard 6-step archival ritual on `/plans/active/solana_dex_pool_swaps_indexer_2026_08_08.md`** once it is fully done (all 5 todos `[x]`, unlocked) and the reconciliation todo above has landed — and separately confirm whether
      `/plans/active/issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md` (the source scoping issue doc) now has zero open todos after
      the reconciliation above; if so, archive it too via the same ritual (task_template.md §4's rule 4: "for a
      batch-style extraction plan, also check each SOURCE doc"). Fix every corpus referrer path in the same pass. Repo:
      unified-trading-pm.

## Progress Log

- **2026-08-08**: authored alongside the main plan (`solana_dex_pool_swaps_indexer_2026_08_08.md`), `status: draft`
  until that plan's todos complete (per its own `gate_on_depends: true` — this is belt-and-suspenders with the draft
  status, since the plan is genuinely new and untouched).
- **2026-08-08**: flipped `status: draft` → `active` — `gate_on_depends: true` already holds actual dispatch until the
  parent plan's todos are done, so the extra `draft` gate was redundant (flagged by `check_finalize_plan_coverage.py`'s
  "finalize plan stuck at draft" ratchet). Per task_template.md §4 / ag-closeout-audit SKILL.md's 2026-07-30 fix: a
  gated finalize plan should be `active` from authorship.
- **context-scout 2026-08-17**: populated/refreshed context_scope (2 entries).
- **plan-reconcile 2026-08-19 (mtds_mdps_master batch A)**: fixed a line-1 completeness defect (task_template.md §3) on
  both open todos — each todo's raw first physical line trailed off mid-sentence ("Re-verify every commit cited by" /
  "...unlocked) and the") with the target doc path(s) and archival condition pushed onto continuation lines the AO
  dispatcher's `_parse_open_todos` never parses. Rewrote both so the target doc, method, and hard constraint are on
  line 1. No content/scope change, no evidence flip — both todos remain correctly gated by `gate_on_depends: true`
  (parent plan still 2/5 todos done as of this pass).
- **context-scout 2026-08-20**: populated/refreshed context_scope (2 entries)
