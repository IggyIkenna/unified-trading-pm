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
last_updated: "2026-08-21"
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

- [ ] [SCRIPT] P3. DEFERRED-BY-DESIGN — per D54 ruling (ADOPTED-REC 2026-08-21, "Wait — the docs are already
      resolved and will most likely archive on their own"): no liveness check or context_scope backfill scheduled
      now. Re-check only if the 4 docs (`empty_reprobe_disagreement_all_2026_08_18.md`, `_2026_08_19.md`,
      `manifest_hygiene_red_all_2026_08_18.md`, `manifest_hygiene_red_cefi_2026_08_16.md`) are still present,
      locked, and unarchived at a future sweep well past today. Repo: unified-trading-pm.

## Progress Log

- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
- **na-eligibility-audit 2026-08-21 (ao tranche batch 2/3)**: KEEP-NA, valid — sole remaining item requires either the 4 named docs' own resolution path to naturally archive them, or an operator-approved unlock before any `context_scope` backfill — the todo's own text explicitly forbids autonomous action on a locked doc. Re-verified live: all 4 docs (`empty_reprobe_disagreement_all_2026_08_18`, `_2026_08_19`, `manifest_hygiene_red_all_2026_08_18`, `manifest_hygiene_red_cefi_2026_08_16`) still present at `plans/active/issues/`, still `status: resolved` + `locked_by: live-defi-rollout`, unarchived since 2026-08-20 — no change to the underlying ask.

- **2026-08-21 — ruling D54 (Locked-doc context_scope backfill)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch
  authority, AUTONOMOUS_AGENT_RULES rule 2): Wait — the docs are already resolved and will most likely archive on
  their own. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
