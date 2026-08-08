---
doc_type: issue
title:
  docs-reconcile 2026-08-08 — 3 authoritative_for content-duplication pairs (no contradiction, but a systemic pattern)
summary: >-
  Three `authoritative_for` doc-pairs found by the 2026-08-08 docs-reconcile sweep's collision hunter where content is
  CONSISTENT (not contradicting, so not an operator-decision park) but genuinely duplicated across two docs that both
  self-declare authority over the same narrow fact, rather than one deferring to the other. All 3 share one shape: a
  broad "consolidated target SSOT" doc restates a fact a narrower sibling doc already owns, instead of cross-referencing
  it -- a real drift risk on the next edit to either side, and one instance (cross-asset-canonical-target-ssot.md)
  directly violates that same doc's own stated "reference, don't duplicate" design principle.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [docs-reconcile, authoritative-for, retrieval-layer, content-duplication]
related:
  [
    /plans/active/issues/docs_reconcile_operator_decisions_2026_08_02.md,
    /plans/active/issues/docs_reconcile_autonomous_sweep_2026_07_30.md,
  ]
created: 2026-08-08
author: unknown
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /codex/02-data/schema-governance.md,
    /codex/04-architecture/schema-placement.md,
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/prediction-schema-paths.md,
    /codex/04-architecture/prediction-batch-live.md,
  ]
supersedes:
superseded_by:
depends_on:
source: [docs-reconcile autonomous sweep, dispatch agt-bb1c67, 2026-08-08]
assigned_role: infra
drift_direction: none
---

# docs-reconcile 2026-08-08 — authoritative_for content duplication (not contradiction)

Found by this run's Phase 1 `authoritative_for` collision hunter (scanned 879 codex docs, 744 declaring
`authoritative_for`, ~156 fuzzy-matched candidate pairs, ~10 highest-value pairs read in full). Of 4 confirmed
collisions, 3 are this class — content-consistent duplication, not contradiction (the 4th, a genuine numeric
contradiction on Fireblocks credential rotation cadence, is parked separately as BLOCKED-OPERATOR-DECISION 4 in
`docs_reconcile_operator_decisions_2026_08_02.md`). Per this skill's own severity guidance, a same-content overlap is
NOT an authority question (no ruling needed on "who's right" when both sides already agree) — but it's also not a
one-line mechanical fix, since resolving it means picking which doc keeps the full prose and which becomes a pointer, a
content-editing judgment call. Filing as a tracked, non-operator-gated finding rather than leaving it as sweep-report
prose only, per the workspace's "every follow-up is a todo, never prose" rule.

## Findings

- [ ] [DOCS] P2. **`/codex/02-data/schema-governance.md` vs `/codex/04-architecture/schema-placement.md`** — both
      independently maintain a "which repo/location owns this type" matrix (schema-governance.md's copy is nested inside
      a broader parquet/GCS-write doc; schema-placement.md is dedicated solely to this question). Neither
      cross-references the other despite covering the same 3-way split (service-local vs UAC-internal cross-service vs
      UAC-external). Fix: pick the dedicated doc (`schema-placement.md`) as the sole owner of the matrix itself, have
      `schema-governance.md` cross-reference it instead of restating it.
- [ ] [DOCS] P2. **`/codex/02-data/cross-asset-canonical-target-ssot.md` §6 vs
      `/codex/02-data/defi-canonical-naming-ssot.md`** — both restate the identical CLOB-vs-DEX-pool perp cefi/defi
      asset_group boundary fact near-verbatim (same 4 venues, same GMX-removal history, same DRIFT/PACIFICA culled
      history). Notably, `cross-asset-canonical-target-ssot.md`'s own intro states its design principle is to "REFERENCE
      the detailed per-domain SSOTs rather than duplicating them" — §6 violates that stated principle by fully restating
      rather than deferring to `defi-canonical-naming-ssot.md` (already `related:`-linked, just not deferred to in body
      prose). Fix: trim §6 down to a pointer, per the doc's own stated design.
- [ ] [DOCS] P3. **`/codex/02-data/prediction-schema-paths.md` vs `/codex/04-architecture/prediction-batch-live.md`** —
      both independently state the identical `canonical_question_group` shard-atom 5-tuple with near-identical wording.
      Both actually attribute the true "banner-canonical" source to a THIRD doc
      (`availability-manifest-and-data-status.md`'s Multi-axis correction banner) yet both still self-declare
      `authoritative_for` on it — a 3-way duplication. Fix: have both defer to the manifest doc's banner as the single
      source, or to each other, rather than each independently restating it.

## Progress Log

- 2026-08-08 (docs_reconciler, dispatch agt-bb1c67): filed. Not fixed this run — each fix is a real content-editing
  judgment call (which doc keeps the prose, which becomes the pointer) rather than a mechanical repoint, and the Phase-1
  hunter's own coverage was explicitly a precision-first sample (~10 of 156 candidate pairs read in full), so there may
  be more instances of this same pattern not yet surfaced. Recommend a future docs-reconcile run's Phase 1
  authoritative_for hunter explicitly widen its read-coverage of the remaining ~146 candidate pairs, prioritizing
  `cross-asset-canonical-target-ssot.md`-adjacent pairs (the hunter flagged it as the common thread in 2 of 4 findings
  here, i.e. a broad consolidated-SSOT doc is the recurring offender shape).
