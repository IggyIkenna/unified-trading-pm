---
doc_type: issue
title: SSOT contradiction — empty-output decision tree is 3-category in one codex doc, 4-category in another
summary:
  /codex/04-architecture/shard-level-failure-isolation.md claims a "three-category empty-output decision tree" while
  /codex/06-coding-standards/validation-and-errors.md (newer, operator directive 2026-05-07) documents FOUR categories
  (adds path D zero-activity-bar). Same decision, conflicting category counts — one doc must be corrected or scoped.
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ssot-contradiction, frontmatter, data-correctness, empty-output, codex-drift]
related:
  [
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/06-coding-standards/validation-and-errors.md,
    ../../archive/2026_07/frontmatter_content_pass_and_gate_consolidation_2026_06_30.md,
  ]
created: 2026-07-03
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: NA
resolved_by: unified-trading-pm@4d42f50c2 (codex option A applied 2026-07-12) — verified 2026-07-16
locked_by:
source:
  [
    P3.2 frontmatter content-pass lane 18 (Opus lane agent) surfaced the contradiction while writing authoritative_for
    claims — the two docs claim adjacent phrases ("three-category empty-output decision tree" vs "four-category
    empty-output decision") for what appears to be the SAME decision at different revisions,
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# SSOT contradiction: 3-vs-4-category empty-output decision

## Finding

Two live codex SSOTs describe the per-shard empty-output classification decision with different category counts:

- [`/codex/04-architecture/shard-level-failure-isolation.md`](/codex/04-architecture/shard-level-failure-isolation.md) —
  claims `authoritative_for: [... three-category empty-output decision tree]`; body documents 3 categories.
- [`/codex/06-coding-standards/validation-and-errors.md`](/codex/06-coding-standards/validation-and-errors.md) — the
  newer merged write-side SSOT; documents a **four-category** decision (adds path D: zero-activity-bar), citing an
  operator directive of 2026-05-07.

If the 2026-05-07 directive added path D, the shard-level doc's 3-category tree (and its `authoritative_for` claim) is
stale and should be updated or narrowed to defer to validation-and-errors.md. If path D is scoped only to the
write-side, both docs should state the scoping explicitly so the counts stop reading as a contradiction.

## Resolution options (operator or dispatched agent)

- A **[REC]**: update shard-level-failure-isolation.md to 4 categories (or explicitly defer the empty-output decision to
  validation-and-errors.md and drop its claim), citing the 2026-05-07 directive.
- B: document the scoping difference in both docs (shard-loop-side vs write-gate-side) if genuinely different decisions.

## Verification note (2026-07-12)

Re-verified directly against both docs' frontmatter: `validation-and-errors.md` has `created: 2026-05-08`,
`authoritative_for` includes "four-category empty-output decision"; `shard-level-failure-isolation.md` has
`created: 2026-03-27`, `last_reviewed: 2026-05-17` (nine days AFTER validation-and-errors.md already existed as the
newer merged SSOT) yet still carries `authoritative_for: [... three-category empty-output decision tree]` — confirms
option A **[REC]** above is the correct read (shard-level-failure-isolation.md is the stale side, never updated after
the 2026-05-08 merge). **NOT auto-applied**: the actual fix requires editing
`/codex/04-architecture/shard-level-failure-isolation.md`, which is out of scope for this doc-reconciliation pass
(codex/ files are never edited here). Status stays `open` pending a codex-authorized edit; the `- [ ]` todo below is
unchanged. Finding #346, plan-reconciliation `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md`
§A2 "50 reclassified" blanket ruling.

## Todos

- [x] [AGENT] P2. ✅ **ALREADY DONE 2026-07-12 — verified 2026-07-16.** Option A was applied by
      `unified-trading-pm@4d42f50c2`; this checkbox simply never got flipped. Read both docs in full + the 2026-05-07
      directive provenance; determine whether path D applies to the shard-loop decision; apply option A or B; update the
      loser's `authoritative_for` accordingly. **Gate**: the two docs agree on the category count or explicitly scope
      their difference; no duplicate authoritative_for phrases.

## Reconciliation 2026-07-16 — the fix shipped the same day this doc said it hadn't

Verified against codex during the AO issue-doc reconciliation sweep. The remedy this doc recommends (**option A**) was
**already applied on 2026-07-12** by `unified-trading-pm@4d42f50c2` (_"docs(plans): leftover queue closed — codex
taxonomy/URDI/consolidator/ao-self-pull synced"_):

- `/codex/04-architecture/shard-level-failure-isolation.md` now carries an
  `<!-- EMPTY_OUTPUT_CATEGORY_CORRECTION_2026_07_12 -->` banner, documents **4** categories (not 3), and its
  `authoritative_for:` **no longer claims the empty-output decision-tree count at all**.
- `/codex/06-coding-standards/validation-and-errors.md:23-24` holds the sole
  `authoritative_for: [..., four-category empty-output decision, ...]` claim.
- **Gate satisfied**: the two docs agree on the category count (A honest-absence / B upstream-timestamp-bias / C
  malformed-fields / D zero-activity-bar) and there is no duplicate `authoritative_for` phrase.

**Why it stayed open**: this doc's own _"Verification note (2026-07-12)"_ says the fix was "NOT auto-applied … out of
scope for this doc-reconciliation pass" and that status should stay `open`. That note was **wrong on the day it was
written** — the codex edit landed the same day. An `open` doc guarding an already-shipped fix costs the next agent a
full re-derivation. Flipped to `resolved` and archived; no code or codex change was needed.
