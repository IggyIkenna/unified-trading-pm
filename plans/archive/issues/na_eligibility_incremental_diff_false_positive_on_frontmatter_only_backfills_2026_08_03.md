---
doc_type: issue
title:
  "/na-eligibility-audit's Phase-0 incremental diff treats a context_scope-only (or other frontmatter-only) backfill
  commit as 'doc changed since verdict' — forces a needless re-verify on every future run, forever, unless hand-caught"
summary: >-
  Phase 0's incremental-skip rule (`cursor-configs/skills/na-eligibility-audit/SKILL.md`) compares a doc's latest
  `na-eligibility-audit YYYY-MM-DD` verdict-marker date against its `last_updated` frontmatter, or — since this corpus
  does not consistently populate `last_updated` — its git last-commit date as a fallback. That fallback has no concept
  of WHICH fields changed: any commit touching the file at all (even a same-day metadata-only backfill) reads as
  "changed since verdict" and forces a fresh Phase-1 read. Measured live during the 2026-08-03 infra-tranche run
  (dispatch agt-a41abf): 5 of 8 docs Phase 0 flagged as "in scope" were false positives — `git show` on each doc's
  actual post-marker commit(s) confirmed the ONLY diff was a `context_scope:` frontmatter backfill (the `/context-scout`
  skill's own unrelated maintenance sweep, batches 3/5 and 4/5 plus a `context_scout backfill — 66 NEVER_SCOUTED docs`
  run, all same-day 2026-08-03) or, in one case, a pure leading-whitespace reflow inside an existing markdown table with
  zero textual change. None of the 5 had any todo/status/body content change. Caught only because this run manually `git
  show`'d every "in scope" doc before trusting the flag rather than re-classifying blind — the skill's own Phase-0 text
  does not currently instruct that verification step, so a less careful run would burn a full Phase-1 re-read (or worse,
  a sub-agent dispatch) on all 5 for no reason. Since context-scout backfills run corpus-wide and this skill runs on a
  2-hour cadence across up to 9 concurrent tranches, this false-positive class recurs on EVERY future run for EVERY doc
  a metadata-only backfill has ever touched, compounding as more maintenance skills (context-scout, docs-reconciler,
  etc.) touch frontmatter fields unrelated to NA-eligibility content.
status: resolved
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    plan-hygiene,
    na-eligibility-audit,
    context-scout,
    incremental-diff,
    false-positive,
    measurement-correctness,
    frontmatter,
  ]
related:
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/issues/na_inventory_counts_fenced_code_block_checkboxes_as_open_todos_2026_08_02.md,
    /plans/active/issues/na_doc_tranche_inventory_stale_citation_membership_cross_contamination_2026_07_29.md,
  ]
created: "2026-08-03"
author: unknown
last_updated: "2026-08-03"
parent_epic: plan_hygiene_master
priority: P3
source:
  "/na-eligibility-audit tranche=infra, autonomous scheduled run 2026-08-03 (dispatch agt-a41abf) — found while manually
  `git show`-verifying every Phase-0 'in scope' doc's actual diff before trusting the git-commit-date fallback"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: infra
drift_direction: advance-code
resolved_by: "operator ruling 2026-08-07 — citation-closed into infra_satellite_ao_dispatch_batch7_2026_08_04.md"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [/cursor-configs/skills/na-eligibility-audit/SKILL.md, scripts/plan-hygiene/generate_na_doc_tranche_inventory.py]
---

> ## ✅ RESOLVED 2026-08-07 — archived (ACKED-INTO-PLAN)
>
> Operator ruling 2026-08-07 ("less work and edits, still correct"): both todos citation-closed — the identical
> content-hash/frontmatter-blind-diff fix is already tracked verbatim in
> `plans/archive/2026_08/infra_satellite_ao_dispatch_batch7_2026_08_04.md` (status: active). No work duplicated here;
> the parent plan owns the fix from here.

# na-eligibility-audit's incremental diff false-positives on frontmatter-only backfill commits

## What I found

Phase 0's skip rule is: skip a doc from Phase 1 when it carries a dated `na-eligibility-audit YYYY-MM-DD` marker AND the
doc's `last_updated` frontmatter (or, absent that, its git last-commit date) is NOT newer than the marker. This corpus
does not consistently populate `last_updated` (checked all 39 infra-tranche docs this run: zero had it), so in practice
the check is almost always **git last-commit date vs. marker date** — a file-level granularity with no awareness of
which fields actually changed.

`/context-scout` (a separate, unrelated scheduled skill) backfills the `context_scope:` frontmatter field across the
whole active corpus in batches, and its commits touch the SAME files this skill verdicts, on the SAME cadence timescale.
When a context-scout commit lands the day after (or the same day as) a na-eligibility-audit verdict marker, Phase 0's
date comparison reads "file changed since verdict" even though nothing verdict-relevant changed.

## Measurement (live, 2026-08-03, infra tranche)

Of 39 infra-tranche docs, Phase 0 flagged 8 as "in scope" (3 genuinely never-verdicted, 5 flagged only by the
date-fallback). Manually `git show`-ing each of the 5's actual post-marker commit(s) before trusting the flag:

| Doc                                                                             | Marker date | Last-commit date | Actual diff since marker                                                        |
| ------------------------------------------------------------------------------- | ----------- | ---------------- | ------------------------------------------------------------------------------- |
| `gitignore_sync_script_destructive_due_to_stale_central_template_2026_07_27.md` | 2026-07-30  | 2026-08-03       | `context_scope:` added + pure line-wrap reflow of an `[x]` item's text          |
| `plan_reconcile_autonomous_sweep_2026_07_30.md`                                 | 2026-08-02  | 2026-08-03       | `context_scope:` added + pure leading-whitespace reflow inside a markdown table |
| `prod_vm_launch_missing_service_account_user_grant_2026_08_02.md`               | 2026-08-02  | 2026-08-03       | `context_scope:` added, nothing else                                            |
| `shared_host_home_filesystem_full_2026_07_26.md`                                | 2026-08-02  | 2026-08-03       | `context_scope:` added, nothing else                                            |
| `stale_agentwork_scratch_clone_not_deletable_unpushed_stashes_2026_07_30.md`    | 2026-08-02  | 2026-08-03       | 2 more entries appended to an existing `context_scope:` list                    |

All 5 verified via `git blame` on the marker line vs. `git log -1` on the file: the marker-adding commit was NOT the
file's HEAD commit, confirming a genuine post-marker touch — but every one of those touches was frontmatter-only. 5 of 8
(62%) of this run's "in scope" set was therefore false-positive busywork, caught only by manual verification this run
happened to do, not by anything the skill's own Phase-0 text requires.

## Why it matters

- **Compounds every future run, on both axes.** Context-scout runs on its own cadence and eventually touches every doc
  in the corpus at least once (it explicitly targets `NEVER_SCOUTED`/`STALE` docs); na-eligibility-audit runs every 2
  hours across up to 9 concurrent tranches. Every doc a metadata backfill has ever touched will misreport as "changed"
  on its very next na-eligibility-audit pass, forever, unless that pass happens to do the same manual `git show`
  diligence this run did (which the skill file does not currently instruct).
- **Directly undermines the stated purpose of Phase 0.** The skill's own incremental-mode rationale is explicitly "do
  not re-read all ~390 docs every time" — a false-positive class this systematic (this run alone: 5/8, 62%) erodes a
  meaningful fraction of that savings, and grows as more maintenance skills (context-scout, docs-reconciler, future
  ones) touch shared frontmatter fields on their own independent cadences.
- **Risk of a worse outcome than wasted effort.** A less careful run — or a sub-agent Phase-1 dispatch that trusts Phase
  0's flag without independently re-verifying — would burn real agent-hours re-classifying unchanged docs, and in the
  worst case could produce a DIFFERENT verdict on a re-read of unchanged content (classifier variance is not zero),
  silently overwriting a previously-correct, deliberately-reasoned verdict for no reason.

## Recommended fix

Teach the Phase-0 diff to distinguish verdict-relevant content from frontmatter noise, rather than trusting file-level
git-commit-date alone. Two independent angles, either sufficient alone, stronger together:

1. **Content-hash comparison, not date comparison.** At verdict-write time, also record a hash of the doc's body
   (frontmatter stripped, or at minimum with known-orthogonal fields like `context_scope` excluded) alongside the dated
   marker. On the next run, skip when the CURRENT hash matches the recorded hash, regardless of intervening commits —
   this is exact and immune to any future frontmatter-only maintenance skill, not just context-scout specifically.
2. **Cheaper partial fix**: teach `generate_na_doc_tranche_inventory.py` (or the skill's own Phase-0 instructions) to
   diff the two commits' content directly (`git show <marker-commit>..HEAD -- <path>` or equivalent) and check whether
   the diff touches anything OTHER than the `context_scope:` frontmatter block before flagging "in scope" — narrower
   than (1) but requires no new state to persist.

Prefer (1): it is the only version that generalizes to future frontmatter-only maintenance skills without needing a
second named exclusion added every time a new one ships.

## Todos

- [x] ✅ [SCRIPT] P3. **RULED 2026-08-07 (operator, "less work and edits, still correct") — Option A: citation-closed,
      tracked in `infra_satellite_ao_dispatch_batch7_2026_08_04.md` (already `status: active`, not draft as last
      believed) — same content-hash/frontmatter-blind-diff fix verbatim, its own todo there.** Not duplicated here.
- [x] ✅ [DOCS] P3. **Same ruling — Option A, citation-closed.** `infra_satellite_ao_dispatch_batch7_2026_08_04.md`
      already carries the identical SKILL.md Phase-0-update todo verbatim. Not duplicated here.

## Plan-destination note

Filed `assigned_vm: NA` per the ask-before-creating HARD RULE's default (this run is autonomous, no operator present to
answer). Both todos are bounded and worker-determinable — named files/script, stated done-when, fix approach already
decided in "Recommended fix" above — so this is a clean candidate for a future `/na-eligibility-audit` pass to
independently evaluate and potentially flip to `assigned_vm: planning`, mirroring the precedent this doc's own
`related:` list cites (`na_inventory_counts_fenced_code_block_checkboxes_as_open_todos_2026_08_02.md`: filed NA by one
dispatch, reclassified by a later, separate dispatch after its own conflict-check). Deliberately not self-reclassified
in the same breath it was authored — the two-step precedent gives the reclassification decision an independent pass
rather than the filer marking their own work ready-to-dispatch in one unbroken action.

## Progress Log

- **na-eligibility-audit 2026-08-06 (infra tranche)**: **KEEP-NA — RECLASSIFY-signal CONFLICT, parked
  BLOCKED-OPERATOR-DECISION, NOT flipped.** Both todos are bounded (content-hash/frontmatter-blind diff verification in
  `generate_na_doc_tranche_inventory.py`; SKILL.md Phase 0 update), but
  `infra_satellite_ao_dispatch_batch7_2026_08_04.md` (assigned_vm: planning, status: draft, drafted 2026-08-04 by
  /ag-closeout-audit) already holds BOTH claims verbatim and its finalize twin plans to flip this doc's checkboxes on
  ship — flipping now would create a duplicate dispatch vehicle for the same two items. Conflict-check §3 CONFLICT: do
  not prefer one side. Operator ruling needed: (A) activate batch7 + citation-close this doc's two todos; (B) keep
  batch7 draft, flip this doc, strip batch7's two overlapping todos; (C) leave both.

- **2026-08-03** — Filed by `/na-eligibility-audit` (tranche `infra`, autonomous scheduled run, dispatch agt-a41abf).
  Found while manually `git show`/`git blame`-verifying every Phase-0 "in scope" doc in the infra tranche's 39-doc
  population before trusting the date-fallback flag, per this run's own "grep-then-READ, not grep-then-conclude"
  discipline — not a hypothetical, all 5 false positives in the measurement table were independently confirmed via
  direct commit inspection, and the correct KEEP-NA-unchanged verdicts were still written for those 5 docs (this finding
  did not block or delay this run's own Phase 1/3 work).
- **context-scout 2026-08-03**: refreshed context_scope (2 entries, unchanged) — both entries already map 1:1 onto this
  doc's two todos (the SCRIPT todo touches `generate_na_doc_tranche_inventory.py`, the DOCS todo touches the SKILL.md
  Phase-0 section); genuinely minimal and correct, no expansion needed.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (2 entries), unchanged.
