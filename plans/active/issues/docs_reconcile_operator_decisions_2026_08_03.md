---
doc_type: issue
title: "docs-reconcile 2026-08-03 — 1 genuine operator-decision park (prediction shard-atom authoritative_for overlap)"
summary: >-
  One finding from the 2026-08-03 docs-reconcile autonomous sweep parked per the skill's own contract: two current
  codex-ssot docs (prediction-schema-paths.md, prediction-batch-live.md) both list "shard atom" phrasing in their own
  `authoritative_for:` field for the identical prediction canonical_question_group tuple, even though both docs' BODY
  text already agrees the real owner is a third hub doc (availability-manifest-and-data-status.md). Adversarial
  verification split (one reviewer UPHELD it as a genuine collision, one found it NOT CONFIRMED as a hub-and-spoke
  false-positive) — parked rather than unilaterally resolved either way, since `authoritative_for` topic ownership is an
  authority call this skill never auto-decides, in any mode.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [docs-reconcile, operator-decision, authoritative_for, retrieval-layer, prediction]
related: [docs_reconcile_operator_decisions_2026_08_02]
created: 2026-08-03
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days:
estimate_calibrated_ai_days:
resolved_by:
locked_by:
locked_since:
context_scope:
supersedes:
superseded_by:
depends_on:
source: [docs-reconcile autonomous sweep, dispatch agt-fd4e6d, 2026-08-03]
assigned_role: infra
drift_direction: advance-docs
---

# docs-reconcile 2026-08-03 — 1 operator-decision park

Per the skill's own autonomous-mode contract, a genuine `authoritative_for` authority call is parked here rather than
decided unilaterally, even though (unusually) the underlying investigation already narrowed this down to a
near-mechanical choice — see "Why this needed a human anyway" below.

## 🚧 BLOCKED-OPERATOR-DECISION 1 — prediction shard-atom `authoritative_for` overlap

- [ ] [DOCS] P2. **Should `prediction-schema-paths.md` and `prediction-batch-live.md` keep "shard atom" phrasing in
      their own `authoritative_for:` field, given both already defer to a third hub doc in their body text?**

  Verified facts (not in question):
  - `/codex/02-data/prediction-schema-paths.md` (`status: current`) declares
    `authoritative_for: [prediction GCS schema paths, canonical_question_group shard atom and taxonomy]`.
  - `/codex/04-architecture/prediction-batch-live.md` (`status: current`) declares
    `authoritative_for: [prediction asset-group batch/live architecture, prediction canonical-question-group shard atom]`.
  - Both restate the identical tuple
    `(asset_group=prediction, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)`
    verbatim, and both bodies explicitly cite `/codex/02-data/availability-manifest-and-data-status.md` as the real
    owner ("banner-canonical" / "Shard-atom + empty-reason SSOT" respectively) — that hub doc itself self-declares
    "**This document is the single source of truth** for: ... shard dimensions per service ...". Both spoke docs'
    frontmatter `related:` lists now cross-reference each other and the hub (the missing hub link on the
    `prediction-batch-live.md` side was added by this sweep — a mechanical precision fix, not the authority question
    itself).
  - The hub doc's OWN `authoritative_for:` field does not contain the phrase "shard atom" (only "availability manifest
    schema + capture_status 4-state ledger").

  **Why this needed a human anyway**: two independent adversarial reviewers split on whether this counts as a genuine
  retrieval-layer collision. Reviewer A (refuter, tried to disprove it): UPHELD — an agent literally grepping
  `authoritative_for:.*shard atom` lands on the two SPOKE docs, never the hub that both actually defer to, so the
  grep-to-one-doc guarantee this field exists for is still broken in practice regardless of body-text agreement.
  Reviewer B (confirmer, tried to independently verify it): NOT CONFIRMED — called this a hub-and-spoke pattern that
  already resolves "who governs" via consistent cross-referencing, not an unresolved peer dispute, and rated the
  frontmatter overlap a "trivial precision gap." Both readings are defensible; picking between them is exactly the kind
  of authority call this skill's contract reserves for the operator, in every mode, even when (as here) the mechanical
  fix itself is small and low-risk either way.

  **A: Trim "shard atom" phrasing from BOTH spoke docs' `authoritative_for:`, and add matching phrasing to the hub doc's
  `authoritative_for:`** — makes the grep-to-one-doc guarantee hold literally, matches what both spoke docs' bodies
  already assert. [RECOMMENDED — lowest future-drift risk: if the atom definition ever changes, there is exactly one doc
  whose frontmatter says so, matching where the body-level cross-references already point] B: **Leave as-is** — the
  body-level cross-references already make the hub-and-spoke structure clear to anyone who opens either spoke doc, and
  the practical risk of drift is low since both spokes currently agree word-for-word with the hub. Other: operator can
  type a custom answer (e.g. trim only one spoke, or word the hub's `authoritative_for` differently rather than adding
  literal "shard atom").

## Progress Log

- 2026-08-03 (docs_reconciler, dispatch agt-fd4e6d): filed after a split adversarial-verification vote (refuter UPHELD
  high-confidence, confirmer NOT CONFIRMED medium-confidence) on the sole P0/P1-tier `authoritative_for` candidate this
  sweep's collision-hunter surfaced across 831 codex-ssot docs carrying the field (0 exact-string collisions
  corpus-wide; ~35+ fuzzy-match candidates individually read and ruled out as intentional parent/child splits or
  shared-vocabulary false positives — see this sweep's Phase 5 report for the full breakdown). Two smaller,
  non-authority findings from the same collision-hunt pass were auto-fixed directly rather than parked here: a missing
  mutual `related:` cross-reference between `execution-modes-and-chain-resolution.md` and
  `paper-vs-live-execution-seam.md`, and the missing hub-doc `related:` link on `prediction-batch-live.md` mentioned
  above.
