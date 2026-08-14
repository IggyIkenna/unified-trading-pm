---
doc_type: codex-ssot
title: Ratchet taxonomy — correctness ratchets vs hygiene ratchets
summary: >-
  Classifies every QG/plan-hygiene ratchet into two kinds with different re-baseline authority: a correctness ratchet
  asserts a claim about the code/world is TRUE and must never be re-baselined by a passer-by, while a hygiene ratchet
  (freshness, link-prose, cosmetic) may be absorbed mid-ship as long as the debt is named in the commit. Formalizes
  reasoning that previously existed only in scattered commit messages.
status: current
nature: guideline
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quality-gates, ratchet, ship-blocker, plan-hygiene, taxonomy, baseline]
related:
  [
    /codex/06-coding-standards/quality-gates.md,
    /codex/11-project-management/plan-hygiene.md,
    /plans/active/issues/qg_ratchets_block_unrelated_ships_2026_08_12.md,
  ]
created: 2026-08-14
authoritative_for: [correctness-ratchet vs hygiene-ratchet classification, who may re-baseline a ratchet and when]
referenced_by: []
owner:
last_reviewed: 2026-08-14
code_refs:
  [
    unified-trading-pm/scripts/quality_gates/check_codex_doc_freshness.py,
    unified-trading-pm/scripts/quality_gates/check_adapter_contract_regression.py,
    unified-trading-pm/scripts/quality_gates/check_evidence_backed_completion.py,
  ]
---

# Ratchet taxonomy: correctness ratchets vs hygiene ratchets

The workspace runs dozens of shrinking-ratchet QG/plan-hygiene gates (`/codex/06-coding-standards/quality-gates.md`
enumerates the STEP 5.x family; `/codex/11-project-management/plan-hygiene.md` the plan-corpus family). They all look
the same mechanically — a baseline file, a count that must not go up, a `--baseline-write`/`--update-baseline` escape
hatch for when the count legitimately needs to move. But two structurally different things get enforced through that one
mechanism, and the escape hatch is safe for only one of them.

## The two kinds

**Correctness ratchet** — the gate asserts a specific claim about the code or the world is **TRUE**: a cited commit SHA
actually landed and its build succeeded, an adapter still calls its required contract methods, a lint-codex violation
count reflects the real current state of the tree, a manifest write is actually stamped. Re-baselining a correctness
ratchet without fixing (or independently re-verifying) the underlying condition makes a **false claim look true** — it
doesn't just defer work, it corrupts the record the gate exists to protect.

**Hygiene ratchet** — the gate tracks review/freshness/cosmetic debt that decays on the calendar or on prose drift, not
on any specific author's change: a codex doc's `last_reviewed` aging past its window, a `codex/`-prefixed CLAUDE.md
shorthand read as a broken path, prosewrap padding. Absorbing this into the baseline mid-ship asserts nothing false — it
just defers a review that was never about correctness in the first place. As long as the debt is named in the commit (so
it stays visible, not hidden), a passer-by absorbing it is the sanctioned remedy, not a violation.

## The test

Ask one question before touching a ratchet's baseline: **would re-baselining this make a false claim look true?**

- Yes → correctness ratchet. Do not `--baseline-write`/`--update-baseline` it to unblock an unrelated ship. Either fix
  the underlying condition, or if you can independently verify the claim is still true, say so explicitly in the commit
  with the verification evidence (not a bare re-baseline). If you can do neither, this is a genuine ship blocker — use
  the repo-blocker / `/blocked` escalation path (`unified-trading-pm/agents/worker.md` § 4b), not the baseline.
- No → hygiene ratchet. Absorbing it mid-ship is fine; name what was absorbed and why in the commit message (the pattern
  already used for `codex_doc_freshness` and `cross-reference-path-convention` absorptions).

## Worked examples

| Ratchet                                                                                       | Kind        | Why                                                                                                                                                                     |
| --------------------------------------------------------------------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `check_evidence_backed_completion.py` (Cloud Build SHA evidence, `plans/PLAN_FORMAT.md` § 8b) | correctness | Asserts a specific `cloudbuild=<id>` actually resolved SUCCESS — re-baselining without checking would let a fabricated/failed deploy read as done.                      |
| STEP 5.83 adapter contract-call regression (`check_adapter_contract_regression.py`)           | correctness | Asserts an adapter still calls `classify_venue_error`/`record_captured`/etc. — the exact contract a hygiene sweep can silently strip.                                   |
| `CODEX_MAX_VIOLATIONS` per-repo ceiling (`quality-gates.md` § "ratchet-down, ≤5 ceiling")     | correctness | The count is a direct measurement of the current tree; a bump not tied to a fix is explicitly review-blocking (2026-06-11 incident: deployment-api 24→25→24, reverted). |
| commit-SHA-reachable-on-origin checks (worker `/done` M3, quickmerge Stage-5 regate guard)    | correctness | Asserts the cited SHA is actually an ancestor of `origin/live-defi-rollout` — a false positive here is exactly "claiming shipped work that wasn't".                     |
| `check_codex_doc_freshness.py`'s `stale` reason (post-2026-08-12 warn-with-digest split)      | hygiene     | Fires purely because a calendar threshold passed with zero content change — asserts nothing about the doc's correctness, only that a re-read is due.                    |
| `cross-reference-path-convention` / dangling-doc-link checks                                  | hygiene     | A broken prose pointer is a navigation defect, not a claim about code behavior.                                                                                         |
| `check_prosewrap_padding.sh`                                                                  | hygiene     | Pure formatting; re-baselining changes nothing about what the doc asserts.                                                                                              |

The same script can straddle both kinds. `check_codex_doc_freshness.py`'s own 2026-08-12 fix
(`unified-trading-pm@9498b9f3a5`) is the concrete precedent: `partition_by_agency()` splits its four violation reasons
by a **different but related** axis — clock-driven (`stale`, hygiene, non-blocking) vs authoring-defect-in-this-diff
(`no-frontmatter`/`no-last_reviewed-field`/`invalid-last_reviewed-format`, which stay blocking because the author's own
change caused them). That split is about _who caused the violation_; this doc's split is about _what the violation
asserts_. They compose rather than collide — a reason can be both "caused by this diff" and a correctness matter, or
"calendar-driven" and still hygiene — but neither axis substitutes for the other, and a gate design should check both
before deciding whether an absorb-path is safe to offer at all.

## Why this wasn't written down until now

Both kinds were hit in one 2026-08-11/12 shipping session
(`plans/active/issues/qg_ratchets_block_unrelated_ships_2026_08_12.md`): a commit-SHA evidence gate correctly blocked
because a peer's commit hadn't actually reached origin (correctness, left blocking), and a codex-freshness gate blocked
because two unrelated docs aged past 90 days with zero edits (hygiene, later converted to warn-with-digest). Both were
handled correctly in the moment, but the reasoning for treating them differently lived only in the shipping commit
messages — this doc is that reasoning, promoted to a citable SSOT so the next gate design (or the next passer-by
deciding whether to `--baseline-write`) doesn't have to re-derive it from git log.
