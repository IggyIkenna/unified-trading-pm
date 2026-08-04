---
doc_type: issue
title: fix_frontmatter.py's DEPRECATED_PLAN_FIELDS strips the author field REQUIRED on issue docs
summary:
  "scripts/plan-hygiene/fix_frontmatter.py's DEPRECATED_PLAN_FIELDS set includes `author`, and
  `remove_deprecated_fields()` is applied blanket to every doc under plans/active/ (including plans/active/issues/) with
  no doc_type gate — so any hygiene sweep or quality-gates.sh plan-hygiene step silently strips `author:` from issue
  docs too, even though RULES.md § 4.5 (Findings Closure) explicitly REQUIRES `title` / `created` / `author` /
  `source[]` on every issue doc. Confirmed live, reproduced twice in one session: this repo's own
  qg_editable_sibling_install_regresses_override_only_cve_fixes_2026_08_04.md lost its `author: slot-9` line on two
  separate quality-gates.sh / quickmerge runs."
status: open
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, frontmatter, docspec, issue-docs, fixer-bug]
related: [/plans/active/issues/qg_editable_sibling_install_regresses_override_only_cve_fixes_2026_08_04.md]
created: 2026-08-04
author: slot-12
parent_epic: infrastructure_master
priority: P3
source:
  [
    "2026-08-04 (slot-12) — discovered as a side effect while validating a LOCAL_DEPS uv fix: running `bash
    scripts/quality-gates.sh` in unified-trading-pm twice silently stripped `author: slot-9` from an unrelated issue
    doc's frontmatter both times, confirmed by `git diff` immediately after each run.",
  ]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-04
context_scope: [scripts/plan-hygiene/fix_frontmatter.py, scripts/docs/docspec.py, unified-trading-pm/agents/RULES.md]
---

# fix_frontmatter.py strips the author field required on issue docs

## What I found

`scripts/plan-hygiene/fix_frontmatter.py` defines:

```python
DEPRECATED_PLAN_FIELDS = {
    "slug", "deadline", "owner", "horizon", "operator", "companion_to", "companion_plans",
    "spawned_from", "parent_plan", "related_codex", "overview", "date", "type", "author", "plan_type",
}
```

and its `fix_active_plan()` (or equivalent) walks every doc under `plans/active/` — including `plans/active/issues/*.md`
— calling `remove_deprecated_fields(new_fm, DEPRECATED_PLAN_FIELDS)` unconditionally, with no `doc_type` gate. `author`
is a legitimate DEPRECATED field for `doc_type: plan` docs (per PLAN_FORMAT.md's canonical schema, which has no `author`
field), but `unified-trading-pm/agents/RULES.md` § 4.5 "FINDINGS CLOSURE" explicitly requires every `doc_type: issue`
doc to carry `author` in its frontmatter: "Frontmatter MUST include `assigned_vm` ... plus `title` / `created` /
`author` / `source[]`."

**Confirmed reproduction**:
`plans/active/issues/qg_editable_sibling_install_regresses_override_only_cve_fixes_2026_08_04.md` declared
`author: slot-9` (correctly, per RULES.md § 4.5). Running `bash scripts/quality-gates.sh` in unified-trading-pm (which
invokes the plan-hygiene fixer/sweep as one of its steps) removed that line from the working tree — reproduced TWICE
independently in the same session (once via a direct QG run, once via `quickmerge.sh`'s own internal sweep steps), both
times restorable via `git restore` (the mutation lands in the working tree, not committed, so nothing shipped broken —
but any agent who doesn't `git status`/`git diff` before their next commit risks silently shipping the field's removal).

## Why it matters

- Directly contradicts a HARD RULE in `RULES.md` § 4.5 — every issue doc this fixer touches is at risk of losing its
  required `author` field on the next hygiene sweep.
- Silent + easy to miss: the mutation happens in the working tree with no log line calling out _which_ field was removed
  from _which_ file in an issue-doc-specific way (the fixer's own changes-list probably just says "removed deprecated" —
  verified generically true from the code, not confirmed per-run since this doc's own run output wasn't captured
  verbatim).
- Any agent who runs `git add -A`/stages broadly without checking `git diff` first could ship this regression into a
  doc's committed history, silently violating the findings-closure contract for that issue doc going forward.

## Recommended decision

Scope `DEPRECATED_PLAN_FIELDS`'s `author`-removal (and any other plan-only-deprecated field that overlaps with a
REQUIRED issue-doc field) to `doc_type: plan` specifically — e.g. read the doc's own `doc_type:` frontmatter value
before calling `remove_deprecated_fields()` and skip `author` from the deprecated-set when `doc_type == "issue"`.
Alternatively, split `DEPRECATED_PLAN_FIELDS` into a doc_type-keyed mapping so this class of collision can't recur for
any other field either.

## Todos

- [ ] [SCRIPT] P3. In `scripts/plan-hygiene/fix_frontmatter.py`, gate the `author` removal (and any other field in
      `DEPRECATED_PLAN_FIELDS` that collides with an issue-doc-required field) on `doc_type != "issue"` before calling
      `remove_deprecated_fields()`, so hygiene sweeps stop silently stripping the RULES.md § 4.5-required `author` field
      from issue docs. Add/extend `scripts/docs/test_docspec.py` or a fixer-specific test to cover an issue doc
      round-trip (author field must survive a fix pass). (repo: unified-trading-pm)

## Progress Log

- 2026-08-04 (slot-12): filed after reproducing the strip twice while shipping an unrelated LOCAL_DEPS `uv` fix
  (`qg_editable_sibling_install_regresses_override_only_cve_fixes_2026_08_04.md`); both times recovered via
  `git restore` before committing, so nothing shipped broken from this session.
