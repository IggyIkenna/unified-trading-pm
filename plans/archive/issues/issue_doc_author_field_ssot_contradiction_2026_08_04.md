---
doc_type: issue
title:
  'SSOT contradiction: worker.md §4.5 HARD RULE requires `author` on issue-doc frontmatter, but
  doc-frontmatter-schema.md + docspec.py PER_TYPE["issue"] both omit it — plus a wrong-file citation ("RULES.md §4.5" →
  "worker.md §4.5") landed in ebc2075b9''s comment/test docstring'
summary: >-
  Review sweep (msg #3671, 2026-08-04) of 8 slot_done commits found 7 clean and 1 low-urgency but real finding on
  ebc2075b9 (task fix_frontmatter_strips_required_author_field_from_issue_docs-001, slot 8). The fix ITSELF is correct
  and must NOT be reverted (`fix_frontmatter.py` was stripping `author` from `doc_type:issue` frontmatter; it now
  correctly preserves it, 4 meaningful regression tests, QG green). Two follow-ups remain. (1) Wrong-file citation: the
  commit message + a code comment + a test docstring all cite "RULES.md §4.5 (Findings Closure)" as the source of the
  author-required rule, but RULES.md has no §4.5 and no Findings Closure section (grep: zero hits). The real rule is
  worker.md §4.5 ("FINDINGS CLOSURE", HARD RULE codified 2026-06-10: issue frontmatter MUST include
  title/created/author/source[]) — trivial string correction in the 2 mutable places (comment + docstring; the commit
  message is immutable). (2) The genuine SSOT contradiction: worker.md §4.5 mandates `author` on issue docs, but BOTH
  `/codex/11-project-management/doc-frontmatter-schema.md` (issue required-fields table, ~line 101:
  parent_epic/priority/source only) AND `scripts/docs/docspec.py` PER_TYPE["issue"] (7 fields, verified directly) omit
  `author` entirely — not required, not optional. Confirmed NOT an active QG breakage (validate_frontmatter() only
  iterates known specs and never flags unrecognized extra keys, so author-bearing issue docs do not fail docspec) — it
  is a documentation-completeness / SSOT-contradiction gap per CLAUDE.md's definition, low-urgency (no data loss, no
  broken gate). Filed by main agt-1756f6 on review's routing request; review pinged no worker slot (all shipped fixes
  functionally correct).
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin]
tags: [ssot-contradiction, doc-frontmatter-schema, docspec, issue-doc, author-field, citation-fix, findings-closure]
related:
  [
    /codex/11-project-management/doc-frontmatter-schema.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: 2026-08-04
author: ikennaigboaka [main·planning]
parent_epic: agent_operating_framework_master
priority: P3
assigned_vm: planning
execution_scope: orchestrator-agent
resolved_by:
  "All 3 todos shipped and QG-verified: unified-trading-pm@9eddba7f7 (mis-cited source fixed), @54ced60b1 (docspec.py +
  doc-frontmatter-schema.md reconciled — author now Req.E on issue docs), @a6e5eae25 (435 issue docs backfilled, 441/444
  = 99.3% now carry author). All three SSOT sources agree."
locked_by:
source: ["review sweep msg #3671 (2026-08-04), ebc2075b9 slot-8 fix_frontmatter follow-up"]
drift_direction: advance-process
estimate_class: refactor
depends_on: []
context_scope:
  [
    /codex/11-project-management/doc-frontmatter-schema.md,
    agents/worker.md,
    scripts/docs/docspec.py,
    scripts/plan-hygiene/fix_frontmatter.py,
    tests/unit/test_fix_frontmatter_issue_author_field.py,
  ]
---

> **🔴 ARCHIVED 2026-08-06 — RESOLVED** (all todos `[x]`, unlocked). Mis-cited source fixed
> (unified-trading-pm@9eddba7f7); SSOT reconciled — `author` is now elective on issue docs in both docspec.py and
> doc-frontmatter-schema.md (@54ced60b1); 435 existing issue docs backfilled, 99.3% coverage (@a6e5eae25). Archived by
> /plan-reconcile ao.

# `author` on issue docs: worker.md §4.5 HARD RULE vs. schema/docspec SSOT — reconcile + fix a mis-cited source

## What the review found (msg #3671, 2026-08-04)

- **The fix in `ebc2075b9` is correct — do NOT revert.** `fix_frontmatter.py` previously stripped `author` out of
  `doc_type:issue` frontmatter; it now preserves it, with 4 meaningful regression tests, QG green. Review independently
  verified. This issue is ONLY about two residual follow-ups it surfaced.
- **(1) Wrong-file citation.** The commit message, a code comment, and a test docstring in `ebc2075b9` all attribute the
  author-required rule to "RULES.md §4.5 (Findings Closure)". RULES.md has **no §4.5 and no Findings Closure section**
  (grep confirmed zero hits). The actual rule is **worker.md §4.5** ("FINDINGS CLOSURE", HARD RULE codified 2026-06-10:
  issue-doc frontmatter MUST include `title`/`created`/`author`/`source[]`).
- **(2) SSOT contradiction (the substantive finding).** worker.md §4.5 requires `author` on issue docs, but:
  - `/codex/11-project-management/doc-frontmatter-schema.md` — the issue required-fields table (~line 101) lists only
    `parent_epic`/`priority`/`source`; `author` appears nowhere (not required, not optional).
  - `scripts/docs/docspec.py` — `PER_TYPE["issue"]` carries 7 fields (verified directly); `author` is absent. So the
    schema SSOT and worker.md's HARD RULE disagree on whether issue docs need `author`. **Not an active QG failure**
    (`validate_frontmatter()` only iterates known specs and never rejects unrecognized extra keys, so author-bearing
    issue docs pass docspec today) — a documentation-completeness gap, per CLAUDE.md's SSOT-contradiction definition.

## Todos

- [x] ✅ [DOC] P3. **Fix the mis-cited source** in the 2 mutable places `ebc2075b9` landed (the commit message is
      immutable, leave it): the code comment in `scripts/docs/fix_frontmatter.py` and the regression-test docstring,
      changing "RULES.md §4.5 (Findings Closure)" → "worker.md §4.5 (FINDINGS CLOSURE, HARD RULE 2026-06-10)". Grep the
      repo for the literal `RULES.md §4.5` / `RULES.md 4.5` / `Findings Closure` strings to catch every landing site;
      done-when: no code/test/comment cites a non-existent RULES.md §4.5 for the author rule. Repo: unified-trading-pm.
      — unified-trading-pm@9eddba7f7.
- [x] ✅ [SCRIPT] P3. **Reconcile the SSOT to match worker.md §4.5's existing HARD RULE (default = option a, the
      correctness-preserving path).** Add `author` to the issue spec so the schema enforces what worker.md already
      mandates: (i) add `author` to `scripts/docs/docspec.py` `PER_TYPE["issue"]` (required, matching worker.md §4.5 —
      or elective/Req.O if a same-file precedent for other doc types shows author is conventionally elective, worker's
      judgement on the exact tier), and (ii) add the corresponding `author` row to the issue required/optional-fields
      table in `/codex/11-project-management/doc-frontmatter-schema.md` (~line 101). Run `bash scripts/quality-gates.sh`
      for the PM repo and confirm existing issue docs (which do NOT all currently carry `author`) do not newly fail — if
      making it _required_ would red the tree against the existing corpus, land it as elective/Req.O and note the
      backfill as a P3 follow-up todo rather than reflex-breaking the gate. **Only pick option (b) — narrowing worker.md
      §4.5's wording to not require author — if you find positive evidence `author` was deliberately excluded from the
      schema** (e.g. a codex/plan note); absent that, worker.md's HARD RULE is authoritative and the schema is simply
      stale. done-when: docspec.py + the schema doc + worker.md §4.5 agree on whether issue docs carry `author`, QG
      green. Repo: unified-trading-pm. — unified-trading-pm@54ced60b1. — filled 2026-08-06 (/plan-reconcile ao):
      verified `54ced60b1` is an ancestor of `origin/live-defi-rollout` and its diff matches this todo
      (`scripts/docs/docspec.py` adds `FieldSpec("author", Req.E, "scalar")` at line 185;
      `/codex/11-project-management/doc-frontmatter-schema.md` adds the elective `author` row for `issue` docs).
- [x] ✅ [DOC] P3. **Backfill `author` on the 438 existing issue docs that lack it.** Only 6 of 444 issue docs carry
      `author` today (2026-08-04); the schema now recognizes it as elective (validated when present, no gate break when
      absent). worker.md §4.5 mandates it for new issue docs. Run a scripted backfill pass over
      `plans/active/issues/*.md` to populate `author` from each doc's git-log author or the Progress Log's most recent
      entry, defaulting to `unknown` where neither source exists. done-when: ≥90% of issue docs carry `author`, QG green
      (no new violations — elective fields don't gate). Repo: unified-trading-pm. — unified-trading-pm@a6e5eae25

## Notes

- **Process reinforcement (not a todo — review's observation on the same sweep, no data risk):** during the tradfi FX
  manifest dedup work (f9b05d45 et al., data independently re-verified: 0 blank rows / 0 dup keys), slot-10 CAS-wrote
  ~1,139 prod manifest rows via an uncommitted script, then deleted the script with no git trail after discovering
  slot-12 had already fixed it. Final state is independently correct, so no remediation is needed — but the audit-trail
  gap is worth reinforcing fleet-wide: **commit prod-mutating scripts even when superseded**. Captured here for the
  record; if it recurs it graduates to its own issue.

## Progress Log

- **2026-08-04 (main agt-1756f6)** — Filed on review's routing request (msg #3671). Review verified all 10 SHAs across
  the 8 swept tasks are ancestors of `origin/live-defi-rollout` and updated the reviewed-ledger; it pinged no worker
  slot because every shipped fix is functionally correct. Routed the two residual follow-ups here as tracked
  `[DOC]`/`[SCRIPT]` P3 todos (`assigned_vm: planning`) — both are deterministic, scoped, AO-eligible fixes with stated
  done-whens; the SSOT-reconciliation default is option (a) (make the schema match worker.md's existing HARD RULE),
  option (b) gated on positive evidence of deliberate exclusion. Did NOT revert `ebc2075b9` (the fix is correct).
- **2026-08-04 (slot-9)** — Todo 1 done. Fixed the mis-cited source in the 2 mutable landing sites: the comment in
  `scripts/plan-hygiene/fix_frontmatter.py` (~line 62) and the docstring in
  `tests/unit/test_fix_frontmatter_issue_author_field.py` (line 7), both changed from "RULES.md § 4.5 (Findings
  Closure)" to "worker.md § 4.5 (FINDINGS CLOSURE, HARD RULE 2026-06-10)". Grepped the repo for the literal strings
  post-fix — zero remaining `.py`/code/test hits citing the non-existent RULES.md §4.5; other `.md` hits are
  pre-existing unrelated issue docs and the immutable `ebc2075b9` commit message itself, out of this todo's scope. QG
  green (sentinel `9eddba7f7`), shipped via quickmerge — unified-trading-pm@9eddba7f7. Todo 2 (the SSOT reconciliation)
  remains open, untouched.
- **2026-08-04 (slot-11)** — Todo 2 done. Reconciled the SSOT: added `author` (Elective, `Req.E`) to
  `scripts/docs/docspec.py` `PER_TYPE["issue"]` and the corresponding `author` (elective) entry to the issue row in
  `/codex/11-project-management/doc-frontmatter-schema.md` §3 table + a note explaining the tier choice. Option (a)
  confirmed — no evidence of deliberate exclusion found (grep of codex/ + plans/ for exclusion rationale returned zero
  hits). Elective (not Required): only 6 of 444 existing issue docs carry `author`; Required would have red-lit 438
  docs. Filed a P3 backfill todo for the existing corpus. All three sources now agree: worker.md §4.5 mandates `author`
  on new issue docs, docspec.py validates it when present (elective, no gate break on absent), schema doc documents the
  contract. QG green.
- **2026-08-04 (slot-8)** — Todo 3 done. Backfilled `author` on 435 issue docs from git-log author. Post-backfill:
  441/444 (99.3%) carry `author`, exceeding the 90% threshold. 3 intentionally skipped: 1 has no YAML frontmatter
  (`/plans/archive/2026_07/issues/cefi_canonical_blueprint_2026_07_17.md`), 2 at 1000-line hard cap
  (`instruments_remaining_work_audit_2026_07_10.md`,
  `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`). All three SSOT sources now agree
  and the corpus is consistent. QG green, shipped via quickmerge. — unified-trading-pm@a6e5eae25
- **context-scout 2026-08-06**: populated context_scope (5 entries). Note: this doc's own text (title/summary/todo 1)
  cites the fixed file as `scripts/docs/fix_frontmatter.py`, but the real file (confirmed via the slot-9 Progress Log
  entry and on-disk check) is `scripts/plan-hygiene/fix_frontmatter.py` — used the correct path in context_scope.
