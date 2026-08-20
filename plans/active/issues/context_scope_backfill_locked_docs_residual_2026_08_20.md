---
doc_type: issue
title: context_scope backfill — 4 locked docs are the only residual after docspec.py's Req.E -> Req.R flip
summary: >-
  The corpus-wide context_scope backfill (ao_satellite_ao_dispatch_batch3_2026_07_31.md todo 1) reached 888/888
  UP_TO_DATE via generate_context_scope_inventory.py and docspec.py's context_scope FieldSpec was hardened from Req.E to
  Req.R for both plan and issue doc_types. Re-running check_frontmatter_schema.py corpus-wide (which, unlike the
  inventory script, does not exclude locked/draft docs from its scope) surfaced 12 docs missing the now-required field;
  8 were status:draft-but-unlocked and were scouted directly this session. The remaining 4 are all locked_by:
  live-defi-rollout and status: resolved — per this corpus's own rule (never edit a locked doc's frontmatter without
  operator sign-off), they were left untouched.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [context-scout, context_scope, frontmatter-schema, locked-doc]
related:
  [
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch3_2026_07_31.md,
    /plans/archive/2026_07/context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
  ]
created: "2026-08-20"
last_updated: "2026-08-20"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P3
resolved_by:
locked_by:
context_scope:
  [
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch3_2026_07_31.md,
    scripts/docs/docspec.py,
    scripts/plan-hygiene/check_frontmatter_schema.py,
  ]
source: >-
  Interactive session, 2026-08-20 — surfaced while finishing ao_satellite_ao_dispatch_batch3_2026_07_31.md's todo 1
  (corpus-wide context_scope backfill + FieldSpec hardening).
---

# context_scope backfill — 4 locked docs residual

## The 4 docs

All `status: resolved`, `locked_by: live-defi-rollout` — a live lock, not a stale one (not independently verified for
liveness this session):

- `plans/active/issues/empty_reprobe_disagreement_all_2026_08_18.md`
- `plans/active/issues/empty_reprobe_disagreement_all_2026_08_19.md`
- `plans/active/issues/manifest_hygiene_red_all_2026_08_18.md`
- `plans/active/issues/manifest_hygiene_red_cefi_2026_08_16.md`

All 4 are already `status: resolved` — the most likely path to resolution is that whatever process holds the lock
archives them (a `doc_type: issue` archive move goes to flat `plans/archive/issues/`, out of `check_frontmatter_schema.py`'s
active-corpus scope entirely, per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` step 6). If
that doesn't happen on its own, this needs either an operator-approved unlock to backfill `context_scope` directly, or
confirmation the lock is stale.

## Follow-up

- [ ] [SCRIPT] P3. Check whether these 4 docs' `locked_by: live-defi-rollout` lock is still live or stale (per this
      workspace's liveness-gated inherited-dirty-WIP convention), and either archive them (if the lock naturally clears
      via their own resolution path) or backfill `context_scope` on them directly (only after an operator-approved
      unlock, never autonomously). Repo: unified-trading-pm.

## Progress Log

- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
