---
doc_type: issue
title: >-
  manifest_hygiene_daily.py's auto-filed issue doc has malformed, apparently
  actively-regenerating frontmatter — blocks quickmerge repo-wide in unified-trading-pm
summary: >-
  plans/active/issues/manifest_hygiene_red_all_2026_08_19.md (auto-filed by the daily
  data-pipeline audit manifest_hygiene_daily.py) has frontmatter that fails
  check_frontmatter_schema (wrong doc_type, invalid status/asset_group, empty tags — later
  observed with most required keys missing entirely). This is already on
  origin/live-defi-rollout, so it fails quality-gates.sh / quickmerge.sh for EVERY session in
  this repo, not just the one that found it. Observed 3 distinct frontmatter states across
  ~10 minutes without editing the file, strongly suggesting an active process (most plausibly
  the generator script itself) is still writing to it.
status: resolved
resolved_by: unified-trading-pm@94e9bf8f4c
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quickmerge, quality-gates, frontmatter-schema, data-pipeline-alerts, blocking]
related:
  [
    /plans/active/issues/worker_slot_account_exhaustion_no_rotation_2026_08_19.md,
    /plans/archive/2026_08/issues/alerting_service_basedpyright_regression_blocks_all_ships_2026_08_12.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-19"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.25
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/manifest_hygiene_red_all_2026_08_19.md,
    e2e-testing/scripts/audit/manifest_hygiene_daily.py,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  Interactive session 2026-08-19 (slot 3) — surfaced as a side effect of shipping an
  unrelated fix (worker_slot_account_exhaustion_no_rotation_2026_08_19); not this session's
  primary subject.
assigned_role: infra
drift_direction: correct-codex
---

> **🟢 ARCHIVED 2026-08-20 — RESOLVED** (status: resolved, 6/6 todos `[x]`, unlocked). Root cause (a
> `fix_frontmatter.py` auto-fixer seeding plan-shaped defaults onto issue docs) fixed at
> `unified-trading-pm@94e9bf8f4c`; the blocked doc-schema work and downstream dependent shipped at
> `unified-trading-pm@314abf445b` / `cc38229b57`.

# manifest_hygiene_daily.py's auto-filed doc blocks quickmerge repo-wide

## What was measured

`bash scripts/quality-gates.sh` (and `quickmerge.sh --isolated`, which re-gates against a fresh
worktree built from `origin/HEAD`) both fail `check_frontmatter_schema` against
`plans/active/issues/manifest_hygiene_red_all_2026_08_19.md`. Confirmed via
`git show origin/live-defi-rollout:<path>` that the malformed frontmatter is already ON origin —
this is not a scoping artifact of any one session's working tree, it fails for everyone.

First observed state (missing/invalid fields):

```
doc_type: plan          # contradicts path-derived 'issue'
status: active           # not a valid issue status
asset_group: cross-asset # not in the valid enum
tags: []                 # required, empty
(resolved_by: absent)
```

A minimal frontmatter-only fix was attempted (correct `doc_type`/`status`/`asset_group`/`tags`,
add `resolved_by:`) and verified clean standalone (`check_frontmatter_schema.py` → 0 violations).
Between that fix landing in the working tree and the next `git status` check (a few minutes,
mid-way through an unrelated quickmerge attempt), the file's on-disk content had changed again —
to a THIRD, more degraded state with most required keys missing entirely:

```
nature, asset_group, stage, repos, scope, tags, related, priority: all missing
```

Three distinct frontmatter states were observed across roughly 10 minutes without this session
editing the file after the first attempt. This is the signature of an external process (most
plausibly `manifest_hygiene_daily.py` itself, mid-run or mid-debug) actively rewriting the file,
not a one-time authoring mistake.

## Why this wasn't fixed in place

Editing a file under active, unexplained, concurrent contention risks colliding with whatever
process is rewriting it, or producing a nonsensical merged result — multi-agent-safety default is
to stop, not keep re-applying a fix that visibly isn't sticking. This session's own edit was
cleanly discarded by the failed quickmerge's recovery path (confirmed via `git status` +
`git stash show -p` — nothing of this session's was lost or stranded).

## Impact

Every `bash scripts/quality-gates.sh` and every `quickmerge.sh` invocation in unified-trading-pm
currently fails on this one file, regardless of what the invoking session is actually trying to
ship — matching the precedent in the archived
`alerting_service_basedpyright_regression_blocks_all_ships_2026_08_12` issue doc (pre-existing
debt anywhere in the repo blocks the whole-tree gate, not just a scoped diff). At least one other
session's shippable work (this issue's own `related:` doc, todo 3's doc-schema changes) is
currently sitting uncommitted, blocked on this.

## Follow-up

- [x] [INFRA] P1. **DONE — the generator was `fix_frontmatter.py`'s auto-fixer, not `manifest_hygiene_daily.py`**
      (correcting this doc's own premise per CLAUDE.md "a doc that misled you is a finding"). Root-caused: its
      `_apply_field_defaults()` was unconditionally stamping plan-shaped defaults (`doc_type=plan`, `status=active`,
      `nature=process`, `asset_group=cross-asset`) onto issue docs regardless of path. Fixed at
      `unified-trading-pm@94e9bf8f4c` ("stop auto-fixer seeding plan-shaped defaults onto issue docs") — corpus-wide
      `check_frontmatter_schema` now reports 2167 docs, zero violations; full `quality-gates.sh` passes.
- [x] ✅ [INFRA] P1. **DONE — answered by the correction immediately above (same doc).** The
      generator was `fix_frontmatter.py`'s auto-fixer, not `manifest_hygiene_daily.py` —
      root-caused and fixed at `unified-trading-pm@94e9bf8f4c` ("stop auto-fixer seeding
      plan-shaped defaults onto issue docs"). Diagnose-the-generator premise is moot.
- [x] [INFRA] P1. **DONE — confirmed stable.** `manifest_hygiene_red_all_2026_08_19.md`'s current frontmatter read
      directly: `doc_type: issue` ✓, `status: open` (valid) ✓, `asset_group: [cross-cutting]` (valid enum) ✓,
      non-empty `tags:` ✓, `resolved_by: slot-7 (e2e-testing@e8c41f618c)` present ✓ — satisfies this todo's
      done-condition verbatim. Fixed at `unified-trading-pm@94e9bf8f4c` + `314abf445b` ("correct issue-doc frontmatter
      schema... unblocks ldr-docs-gate + promote-PR checks slice"), both verified ancestors of
      `origin/live-defi-rollout`.
- [x] ✅ [INFRA] P1. **DONE — satisfied by the sibling todo directly above (same doc).** Fixed
      at `unified-trading-pm@94e9bf8f4c` + `314abf445b`; current frontmatter confirmed valid
      (`doc_type: issue`, `status: open`, valid `asset_group`, non-empty `tags`, `resolved_by:`
      present).
- [x] [SCRIPT] P2. **DONE — shipped.** `worker_slot_account_exhaustion_no_rotation_2026_08_19.md`'s own Progress Log
      states "todo 3's `unified-trading-pm` half shipped cleanly at `cc38229b57` on the first retry" and "the
      generator issue itself is unrelated to this doc and remains tracked only in its own issue doc above."
      `unified-trading-pm@cc38229b57` verified ancestor of `origin/live-defi-rollout`.
- [x] ✅ [SCRIPT] P2. **DONE — already shipped, per the sibling todo directly above (same
      doc).** `worker_slot_account_exhaustion_no_rotation_2026_08_19.md`'s own Progress Log
      confirms the unified-trading-pm half shipped at `unified-trading-pm@cc38229b57`, verified
      ancestor of `origin/live-defi-rollout`.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
