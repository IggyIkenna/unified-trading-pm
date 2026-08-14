---
doc_type: issue
title:
  Untriaged CI backlog carried forward from the 2026-08-10 alert audit — release-tag stall (7 repos), UTL prod trigger,
  glue-runner 228 restarts
summary: >-
  Three CI conditions were named in a 2026-08-10 alert audit's Deferred-work table ("untouched CI groups from the alert
  audit") but never converted into a tracked todo, and the audit's parent issue doc is now being archived (all its own
  todos done) — migrating the prose deferral into a real todo here per the archival-discipline HARD RULE ("never let a
  deferral evaporate with the archived plan") rather than investigating from scratch, since none of the three conditions
  has been re-verified as still-live since 2026-08-10.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-ci]
scope: [engineer]
tags: [ci, release-tags, glue-runner, backlog, migrated-deferral]
related:
  [
    /plans/archive/2026_08/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-14
last_updated: "2026-08-14"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: infra
effort: medium
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Migrated from `pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md`'s "Deferred work after 2026-08-10"
  table (row: "Release-tag stall (7 repos), UTL prod trigger, glue runner 228 restarts — Not done — untouched CI groups
  from the alert audit — nobody; pick it up") while archiving that doc 2026-08-14 (every one of its own todos done; a
  bare prose deferral cannot be left to evaporate with the archive per
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § 2).
depends_on: []
context_scope: []
---

# Untriaged CI backlog: release-tag stall, UTL prod trigger, glue-runner restarts

## What I found

The 2026-08-10 alert audit (folded into `pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md`'s "CI
audit + QG-timing findings" section) named three CI conditions as untouched backlog, with no further detail recorded
beyond the row itself:

1. A release-tag stall affecting 7 repos.
2. A UTL (unified-trading-library) production trigger issue.
3. A glue-runner with 228 restarts.

None of these has a root-cause investigation on record. `reconcile_release_tags.py` is documented elsewhere (CLAUDE.md)
as "a stall detector, not minter" — item 1 may already be self-flagging via that mechanism, or may already be stale (4+
days old at time of migration); this has not been re-checked.

## Why it matters

Untriaged is not the same as resolved — this could be live, ongoing CI cost/noise, or it could already be moot. Nobody
has looked since 2026-08-10.

## Recommended decision

Re-verify each condition is still live (via `gh run list`/`reconcile_release_tags.py`/the glue-runner's own restart
count) before doing any deeper fix — do not assume any of the three is still accurate 4 days later.

## Todos

- [ ] [INFRA] P3. Re-verify whether the 7-repo release-tag stall is still live (re-run
      `scripts/cicd/reconcile_release_tags.py` or equivalent check); if stale/self-resolved, close this item; if live,
      root-cause and fix — repo: unified-trading-ci.
- [ ] [INFRA] P3. Re-verify the UTL production trigger issue is still live and root-cause it if so — repo:
      unified-trading-library.
- [ ] [INFRA] P3. Re-verify the glue-runner's restart count; if still elevated, root-cause the restart loop — repo:
      unified-trading-ci.

## Progress Log

- **2026-08-14 (slot-20, infra)**: filed as a migration of an unowned prose deferral row while archiving its parent doc.
  No investigation performed here — see Todos for the re-verify-first approach.
