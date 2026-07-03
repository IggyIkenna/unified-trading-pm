---
doc_type: issue
title: SSOT contradiction — empty-output decision tree is 3-category in one codex doc, 4-category in another
summary:
  codex/04-architecture/shard-level-failure-isolation.md claims a "three-category empty-output decision tree" while
  codex/06-coding-standards/validation-and-errors.md (newer, operator directive 2026-05-07) documents FOUR categories
  (adds path D zero-activity-bar). Same decision, conflicting category counts — one doc must be corrected or scoped.
status: open
nature: record
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ssot-contradiction, frontmatter, data-correctness, empty-output, codex-drift]
related:
  [
    ../../../codex/04-architecture/shard-level-failure-isolation.md,
    ../../../codex/06-coding-standards/validation-and-errors.md,
    ../frontmatter_content_pass_and_gate_consolidation_2026_06_30.md,
  ]
created: 2026-07-03
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: NA
resolved_by:
locked_by: NA
source:
  [
    P3.2 frontmatter content-pass lane 18 (Opus lane agent) surfaced the contradiction while writing
    authoritative_for claims — the two docs claim adjacent phrases ("three-category empty-output decision tree" vs
    "four-category empty-output decision") for what appears to be the SAME decision at different revisions,
  ]
---

# SSOT contradiction: 3-vs-4-category empty-output decision

## Finding

Two live codex SSOTs describe the per-shard empty-output classification decision with different category counts:

- [`codex/04-architecture/shard-level-failure-isolation.md`](../../../codex/04-architecture/shard-level-failure-isolation.md)
  — claims `authoritative_for: [... three-category empty-output decision tree]`; body documents 3 categories.
- [`codex/06-coding-standards/validation-and-errors.md`](../../../codex/06-coding-standards/validation-and-errors.md)
  — the newer merged write-side SSOT; documents a **four-category** decision (adds path D: zero-activity-bar), citing
  an operator directive of 2026-05-07.

If the 2026-05-07 directive added path D, the shard-level doc's 3-category tree (and its `authoritative_for` claim)
is stale and should be updated or narrowed to defer to validation-and-errors.md. If path D is scoped only to the
write-side, both docs should state the scoping explicitly so the counts stop reading as a contradiction.

## Resolution options (operator or dispatched agent)

- A **[REC]**: update shard-level-failure-isolation.md to 4 categories (or explicitly defer the empty-output decision
  to validation-and-errors.md and drop its claim), citing the 2026-05-07 directive.
- B: document the scoping difference in both docs (shard-loop-side vs write-gate-side) if genuinely different
  decisions.

## Todos

- [ ] [AGENT] P2. Read both docs in full + the 2026-05-07 directive provenance; determine whether path D applies to
      the shard-loop decision; apply option A or B; update the loser's `authoritative_for` accordingly. **Gate**: the
      two docs agree on the category count or explicitly scope their difference; no duplicate authoritative_for
      phrases.
