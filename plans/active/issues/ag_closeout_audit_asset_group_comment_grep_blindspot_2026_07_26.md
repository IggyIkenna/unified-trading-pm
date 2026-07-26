---
doc_type: issue
title:
  The ag-closeout-audit orthogonality retag comment style makes a doc invisible to asset_group discovery — the fix
  reintroduces the failure class it exists to prevent
summary: >-
  `/ag-closeout-audit`'s Orthogonality HARD CHECK prescribes retagging a mistagged doc and "never silently leaving it
  dual-tagged" — in practice that has been done with an inline YAML comment that QUOTES the old value, e.g.
  `asset_group:\n  [prediction] # corrected 2026-07-25 ... -- was [cross-cutting], a genuine mistag`. That shape defeats
  tag discovery in BOTH directions: a single-line `rg '^asset_group:.*<ag>'` misses the doc entirely (the value sits on
  a continuation line), while a naive whole-block tokenizer reads the quoted old value as a LIVE second tag and excludes
  the doc as a peer-AG candidate. Either way the doc drops out of the candidate set — the exact invisible-orphan class
  the check exists to catch. Measured consequence: `prediction_cqg_residual_2026_07_24.md` (2 open todos, one of them
  P1) was invisible to BOTH same-day prediction audits (batch3's 17-doc set and batch4's 26-doc set) despite having been
  correctly retagged the day before, and was found only by a frontmatter-block-aware parse that strips comments before
  tokenising.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, ag-closeout-audit, frontmatter, asset-group, discovery, orphan-detection, skill-defect]
related:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/prediction_cqg_residual_2026_07_24.md,
    /plans/active/prediction_satellite_ao_dispatch_batch5_2026_07_26.md,
    /plans/active/ag_closeout_audit_rollout_2026_07_25.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
  ]
created: 2026-07-26
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
drift_direction: advance-code
depends_on: []
source:
  [
    "Found 2026-07-26 by the second /ag-closeout-audit prediction run (autonomous) while reconciling why
    prediction_cqg_residual_2026_07_24.md had ZERO coverage in any batch/native/phase plan despite being correctly
    asset_group-tagged.",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
---

# ag-closeout-audit: the orthogonality-retag comment style is a discovery blindspot

## What I found

`prediction_cqg_residual_2026_07_24.md` carries this frontmatter:

```yaml
asset_group:
  [prediction] # corrected 2026-07-25 (ag-closeout-audit orthogonality fix) -- was [cross-cutting], a genuine
  # mistag: cqg-classifier coverage is prediction-market-specific, inherited the parent harness's cross-cutting
  # tag on fork instead of being corrected to its real single-AG scope
```

The retag itself is correct and the audit trail is genuinely valuable. The problem is purely mechanical, and it cuts
both ways:

1. **Single-line grep misses it.** `rg -l '^asset_group:.*prediction' plans/active/*.md plans/active/issues/*.md`
   returns 63 docs and this is not one of them — the key line ends at the colon, and the value is on the next line. The
   skill's own Phase 0.3 wording ("enumerate every `plans/active/*.md` ... whose frontmatter `asset_group` list contains
   `<ag>`") is naturally implemented as exactly this grep; the closeout-linkage helper and the ad-hoc greps quoted
   inside several closeout docs use that form too.
2. **Naive block-aware parsing ALSO misses it, for the opposite reason.** Collapse the continuation lines and tokenise
   without stripping `#` comments, and the quoted `[cross-cutting]` reads as a live second tag → the doc looks like
   `[prediction, cross-cutting]` → the Phase 0.3 peer-AG exclusion drops it as a "deterministic cross-cutting
   candidate", AND `cross-cutting`'s own audit drops it for carrying a specific AG. That is verbatim the
   fall-through-both-audits failure the Orthogonality HARD CHECK section describes as "an invisible orphan the discovery
   step itself creates".

I hit failure mode (2) first in this session — my initial parser reported 63 members and classified cqg_residual as an
excluded peer-AG doc; only after adding comment-stripping did it appear as the 64th member.

## Measured consequence

- `prediction_cqg_residual_2026_07_24.md`: 2 open todos (`[DATA] P1` + `[DATA] P2`), `status: active`, `priority: P0`.
- Coverage: ZERO hits in `prediction_satellite_ao_dispatch_batch1/2/4` (+ their finalizes),
  `prediction_consolidated_native_ao_extract` (+ finalize), the archived `batch3` pair, or any of the 4
  `prediction_phase_*` children. Its only corpus mentions are two entries in
  `prediction_consolidated_closeout_2026_07_18.md`'s "Aggregated source docs" digest — which that section's own header
  declares is "referenced, not duplicated", i.e. not dispatch.
- Both same-day prediction audits missed it: batch3 states it triaged "all 17 prediction AG-primary docs", batch4 "all
  26 prediction AG-primary candidate docs". A comment-stripping block parse over the same corpus finds 64
  prediction-tagged docs / 32 strict candidates.
- Worse, the doc's blocking gate (operator decision 338) had already been ruled and implemented in UAC on 2026-06-16 —
  so the invisibility hid work that was not merely open but _unblocked and ready_.

Note the retag that created this shape was itself the CORRECT action, taken by a prior run of this same skill. This is
not a criticism of that fix; it is that the prescribed fix has an unintended discovery cost nobody measured.

## Why it matters beyond this one doc

The corpus has 17 docs whose `asset_group` is a multi-line block (`rg -c '^asset_group:\s*$'`), and the
orthogonality-retag pass explicitly created several of them (the SKILL's own § lists 6 forks retagged 2026-07-25 plus 3
earlier ones). Every future orthogonality fix that follows the documented "never silently left dual-tagged" instruction
with a value-quoting comment adds another doc that single-line discovery cannot see. The failure is silent in the worst
way: the audit reports a clean orphan count and a plausible-looking doc total, so nothing looks wrong.

## Suggested next steps (not actioned here — this is a skill/tooling change, scoped for its own pass)

1. Amend `/cursor-configs/skills/ag-closeout-audit/SKILL.md` Phase 0.3 to require a **frontmatter-block-aware parse that
   strips YAML comments before tokenising**, and to state explicitly that a single-line `rg '^asset_group:.*<ag>'` is
   NOT sufficient. Same for the membership greps quoted inside the closeout docs.
2. Prefer recording a retag's history in the doc's **Progress Log** (or a `# corrected …` comment that does NOT restate
   the old bracketed value) rather than inline in the `asset_group` block — keeps the audit trail without putting a dead
   value where a tokenizer will read it.
3. Add a cheap guard to `scripts/plan-hygiene/` that cross-checks the single-line-grep membership count against a
   block-aware count per asset group and fails on divergence — that turns this whole class from silent to loud.
4. Re-run the discovery step for the OTHER 8 tranches with a comment-stripping parse before their next closeout gate;
   this session only proved the miss for `prediction`, and the same shape exists across the corpus (the sports, defi and
   cefi forks named in the SKILL's own orthogonality section are the obvious first places to look).

## Provenance

Second `/ag-closeout-audit prediction` run, 2026-07-26 (autonomous). The prediction-side consequence is tracked as
`/plans/active/prediction_satellite_ao_dispatch_batch5_2026_07_26.md` todos 1-2 (`status: draft`); this doc tracks the
skill/tooling defect itself so it stops recurring.
