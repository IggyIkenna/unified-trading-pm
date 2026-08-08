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
status: resolved
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
resolved_by: docs_reconciler (second same-day dispatch, 2026-08-08)
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

> **🟢 ARCHIVED 2026-08-08 (docs_reconciler, second same-day dispatch).** All 3 todos fixed: todo 1
> (schema-governance.md ↔ schema-placement.md) and todo 2 (cross-asset-canonical-target-ssot.md §6 ↔
> defi-canonical-naming-ssot.md) trimmed to pointers + `authoritative_for` corrected, `unified-trading-pm@36c2335aa`;
> todo 3 (prediction-schema-paths.md ↔ prediction-batch-live.md) — added the missing manifest-doc-banner citation to
> prediction-batch-live.md § 4. Zero referrers to this doc's path found corpus-wide (grep, pre-archive) — no step-5
> referrer updates needed. Codex-alignment check: the fixes themselves ARE the codex updates (the 3 collision pairs), no
> separate codex doc needed.

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

- [x] ✅ [DOCS] P2. **`/codex/02-data/schema-governance.md` vs `/codex/04-architecture/schema-placement.md`** — both
      independently maintain a "which repo/location owns this type" matrix (schema-governance.md's copy is nested inside
      a broader parquet/GCS-write doc; schema-placement.md is dedicated solely to this question). Neither
      cross-references the other despite covering the same 3-way split (service-local vs UAC-internal cross-service vs
      UAC-external). Fix: pick the dedicated doc (`schema-placement.md`) as the sole owner of the matrix itself, have
      `schema-governance.md` cross-reference it instead of restating it. **Fixed 2026-08-08 (docs_reconciler)**: trimmed
      schema-governance.md's 5-row matrix down to a pointer at schema-placement.md + the one non-duplicated fact
      (SchemaDefinition/ColumnSchema stays service-local); removed `schema type ownership placement matrix` from
      schema-governance.md's own `authoritative_for` (kept `parquet SchemaDefinition vs UAC data-contract split`, its
      genuinely unique content); added bidirectional `related:`/`referenced_by:` links between the two docs.
- [x] ✅ [DOCS] P2. **`/codex/02-data/cross-asset-canonical-target-ssot.md` §6 vs
      `/codex/02-data/defi-canonical-naming-ssot.md`** — both restate the identical CLOB-vs-DEX-pool perp cefi/defi
      asset_group boundary fact near-verbatim (same 4 venues, same GMX-removal history, same DRIFT/PACIFICA culled
      history). Notably, `cross-asset-canonical-target-ssot.md`'s own intro states its design principle is to "REFERENCE
      the detailed per-domain SSOTs rather than duplicating them" — §6 violates that stated principle by fully restating
      rather than deferring to `defi-canonical-naming-ssot.md` (already `related:`-linked, just not deferred to in body
      prose). Fix: trim §6 down to a pointer, per the doc's own stated design. **Fixed 2026-08-08 (docs_reconciler)**:
      §6 now points at defi-canonical-naming-ssot.md's two named sections instead of restating them; moved
      `CLOB-vs-DEX-pool perp asset_group classification` + `defi two-id model` off
      cross-asset-canonical-target-ssot.md's `authoritative_for` (the two-id-model topic was previously undeclared on
      either doc — added it to defi-canonical-naming-ssot.md, the doc that actually carries the content, alongside its
      existing CLOB-boundary claim).
- [x] ✅ [DOCS] P3. **`/codex/02-data/prediction-schema-paths.md` vs `/codex/04-architecture/prediction-batch-live.md`**
      — both independently state the identical `canonical_question_group` shard-atom 5-tuple with near-identical
      wording. Both actually attribute the true "banner-canonical" source to a THIRD doc
      (`availability-manifest-and-data-status.md`'s Multi-axis correction banner) yet both still self-declare
      `authoritative_for` on it — a 3-way duplication. Fix: have both defer to the manifest doc's banner as the single
      source, or to each other, rather than each independently restating it. **Fixed 2026-08-08 (docs_reconciler)**:
      re-read both docs — `prediction-schema-paths.md` already cited the manifest-doc banner correctly (its own
      `<!-- MULTI_AXIS_CORRECTION_2026_05_06 -->` banner + a "banner-canonical per..." citation right before its
      restatement); `prediction-batch-live.md` § 4 was the actual gap — it restated the identical 5-tuple with ZERO
      attribution, presenting it as this doc's own fact. Added the same "banner-canonical per
      availability-manifest-and-data-status.md § Multi-axis correction banner" citation to § 4, resolving the 3-way
      duplication by making both docs explicitly defer to the third doc rather than each independently asserting it.
      Neither doc's `authoritative_for` declared this narrow fact (both are broad: "prediction GCS schema paths" /
      "prediction asset-group batch/live architecture"), so no frontmatter change was needed here — this was purely a
      missing-citation gap in body prose, unlike todos 1/2.

## Progress Log

- 2026-08-08 (docs_reconciler, dispatch agt-bb1c67): filed. Not fixed this run — each fix is a real content-editing
  judgment call (which doc keeps the prose, which becomes the pointer) rather than a mechanical repoint, and the Phase-1
  hunter's own coverage was explicitly a precision-first sample (~10 of 156 candidate pairs read in full), so there may
  be more instances of this same pattern not yet surfaced. Recommend a future docs-reconcile run's Phase 1
  authoritative_for hunter explicitly widen its read-coverage of the remaining ~146 candidate pairs, prioritizing
  `cross-asset-canonical-target-ssot.md`-adjacent pairs (the hunter flagged it as the common thread in 2 of 4 findings
  here, i.e. a broad consolidated-SSOT doc is the recurring offender shape).
- **na-eligibility-audit 2026-08-08** (ao tranche): KEEP-NA, valid — deferring to the authoring docs_reconciler's own
  explicit judgment-call framing (it read the actual content in both docs of each pair before filing). Closer read on
  this pass: todo 1 and todo 2 each already have a fully-determined fix stated in their own text (todo 1: "pick the
  dedicated doc as sole owner" — schema-placement.md over the nested copy in schema-governance.md; todo 2: "trim §6 down
  to a pointer, per the doc's own stated design" — cross-asset-canonical-target-ssot.md's own intro already commits to
  deferring, not restating) — tagging both MISCLASSIFIED_LIKELY_AO_ELIGIBLE for a closer look next pass rather than
  overriding today's filing verdict unilaterally. Todo 3 genuinely still needs a defer-direction call ("or to each
  other" leaves which-doc-defers-to-which open even though the third-doc-banner option is the likelier fix) —
  GENUINE_WORK. Not re-litigated beyond that.
- 2026-08-08 (docs_reconciler, second same-day dispatch, one-off boot): re-verified this doc's own state fresh before
  acting (grepped for a same-day duplicate docs-reconcile run first, per the workspace's pre-task plan/issue conflict
  check) — found this issue + the na-eligibility-audit's MISCLASSIFIED_LIKELY_AO_ELIGIBLE tag on todos 1/2, agreed with
  that read after independently re-reading both doc pairs in full, and applied both fixes (see checkbox notes above).
  Todo 3 still open — deferred (see below), not a mechanical fix the way 1/2 were.
