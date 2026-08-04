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
  `codex/11-project-management/doc-frontmatter-schema.md` (issue required-fields table, ~line 101:
  parent_epic/priority/source only) AND `scripts/docs/docspec.py` PER_TYPE["issue"] (7 fields, verified directly) omit
  `author` entirely — not required, not optional. Confirmed NOT an active QG breakage (validate_frontmatter() only
  iterates known specs and never flags unrecognized extra keys, so author-bearing issue docs do not fail docspec) — it
  is a documentation-completeness / SSOT-contradiction gap per CLAUDE.md's definition, low-urgency (no data loss, no
  broken gate). Filed by main agt-1756f6 on review's routing request; review pinged no worker slot (all shipped fixes
  functionally correct).
status: open
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
locked_by:
source: ["review sweep msg #3671 (2026-08-04), ebc2075b9 slot-8 fix_frontmatter follow-up"]
drift_direction: advance-process
estimate_class: refactor
depends_on: []
---

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
  - `codex/11-project-management/doc-frontmatter-schema.md` — the issue required-fields table (~line 101) lists only
    `parent_epic`/`priority`/`source`; `author` appears nowhere (not required, not optional).
  - `scripts/docs/docspec.py` — `PER_TYPE["issue"]` carries 7 fields (verified directly); `author` is absent. So the
    schema SSOT and worker.md's HARD RULE disagree on whether issue docs need `author`. **Not an active QG failure**
    (`validate_frontmatter()` only iterates known specs and never rejects unrecognized extra keys, so author-bearing
    issue docs pass docspec today) — a documentation-completeness gap, per CLAUDE.md's SSOT-contradiction definition.

## Todos

- [ ] [DOC] P3. **Fix the mis-cited source** in the 2 mutable places `ebc2075b9` landed (the commit message is
      immutable, leave it): the code comment in `scripts/docs/fix_frontmatter.py` and the regression-test docstring,
      changing "RULES.md §4.5 (Findings Closure)" → "worker.md §4.5 (FINDINGS CLOSURE, HARD RULE 2026-06-10)". Grep the
      repo for the literal `RULES.md §4.5` / `RULES.md 4.5` / `Findings Closure` strings to catch every landing site;
      done-when: no code/test/comment cites a non-existent RULES.md §4.5 for the author rule. Repo: unified-trading-pm.
- [ ] [SCRIPT] P3. **Reconcile the SSOT to match worker.md §4.5's existing HARD RULE (default = option a, the
      correctness-preserving path).** Add `author` to the issue spec so the schema enforces what worker.md already
      mandates: (i) add `author` to `scripts/docs/docspec.py` `PER_TYPE["issue"]` (required, matching worker.md §4.5 —
      or elective/Req.O if a same-file precedent for other doc types shows author is conventionally elective, worker's
      judgement on the exact tier), and (ii) add the corresponding `author` row to the issue required/optional-fields
      table in `codex/11-project-management/doc-frontmatter-schema.md` (~line 101). Run `bash scripts/quality-gates.sh`
      for the PM repo and confirm existing issue docs (which do NOT all currently carry `author`) do not newly fail — if
      making it _required_ would red the tree against the existing corpus, land it as elective/Req.O and note the
      backfill as a P3 follow-up todo rather than reflex-breaking the gate. **Only pick option (b) — narrowing worker.md
      §4.5's wording to not require author — if you find positive evidence `author` was deliberately excluded from the
      schema** (e.g. a codex/plan note); absent that, worker.md's HARD RULE is authoritative and the schema is simply
      stale. done-when: docspec.py + the schema doc + worker.md §4.5 agree on whether issue docs carry `author`, QG
      green. Repo: unified-trading-pm.

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
