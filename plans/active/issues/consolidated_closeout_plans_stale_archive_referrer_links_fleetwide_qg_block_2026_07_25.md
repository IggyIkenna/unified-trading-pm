---
doc_type: issue
title:
  "4 consolidated-closeout plans held 14 stale `/plans/active/issues/...` links to docs archived to
  `/plans/archive/...`, failing run_validators.py fleet-wide and blocking every repo's quickmerge sentinel"
summary: >-
  Discovered while shipping the parked cloudbuild.yaml substitution-escape fix for market-tick-data-service (its own
  repo's quality-gates.sh Step 6/6 "PRODUCTION READINESS VALIDATORS" failed on `python3
  unified-trading-pm/scripts/run_validators.py --scope all`, not on anything in market-tick-data-service itself). Root
  cause: 14 markdown links in 4 consolidated-closeout plans still pointed at `/plans/active/issues/<doc>.md` paths for
  docs that had already been archived to `/plans/archive/issues/<doc>.md`. Every repo's quality-gates.sh invokes this
  same PM-corpus validator, so this was a fleet-wide QG-red blocker (no repo could pass the quickmerge --agent sentinel
  check) until fixed. This is the exact bug class CLAUDE.md's plan-archival ritual step "update every referrer's path
  corpus-wide" (added 2026-07-23) exists to prevent — it recurred anyway.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plans, links, validators, qg, fleet-wide, p0]
related: []
created: 2026-07-25
parent_epic: infrastructure_master
priority: P0
source:
  "Found 2026-07-25 (slot 3, infra) while shipping cloudbuild_yaml_unescaped_substitution_comments_fleet_wide-001 (the
  parked market-tick-data-service todo)."
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by: slot-3
---

# consolidated-closeout plans — stale archive-referrer links, fleet-wide QG block

## What I found

`python3 unified-trading-pm/scripts/run_validators.py --scope all` failed with 14 `BROKEN:` link reports, all of the
shape `active/<consolidated_closeout_plan>.md -> /plans/active/issues/<doc>.md` where `<doc>.md` had actually been moved
to `/plans/archive/issues/<doc>.md` (or `/plans/archive/<doc>.md` for 2 non-issue docs). Every one of the 14 targets was
confirmed to exist, unchanged, at its `plans/archive/...` location — this was a referrer-path staleness bug, not a
deleted/missing doc.

Affected files (all in `plans/active/`):

- `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md` — 3 stale links
- `tradfi_consolidated_closeout_2026_07_18.md` — 2 stale links (3 occurrences incl. a frontmatter `related` list entry)
- `defi_consolidated_closeout_aggregated_sources_2026_07_24.md` — 2 stale links
- `sports_consolidated_closeout_aggregated_sources_2026_07_24.md` — 7 stale links

Because this validator (`STEP 6/6: PRODUCTION READINESS VALIDATORS` in every repo's `quality-gates.sh`) is shared across
the whole fleet, **this blocked the `quality-gates.sh`-green sentinel for every repo**, not just unified-trading-pm — no
repo could reach the `quickmerge --agent` gate while this was red. Other slots' recent `quality-gates.sh green` evidence
entries earlier in the session (2026-07-25, ~13:00-14:00) predate this regression, so it was introduced sometime after
those runs — likely by the same archival pass that moved the 14 target docs to `plans/archive/` without updating these 4
referring plans (the exact gap CLAUDE.md's 2026-07-23 archival-ritual addendum "update every referrer's path
corpus-wide" was written to close).

## Why this wasn't independently confirmed as a standing/known issue

Not investigated: which specific archival operation(s) moved the 14 target docs, or whether other (non-closeout) active
plans hold similar stale links to other archived docs — this fix was scoped to the 14 links the validator actually
flagged as broken at the time of discovery. If `run_validators.py --scope all` goes red again with a similar `BROKEN:`
pattern, treat it as a recurrence of this same gap, not a new bug class.

## Recommended fix

Applied directly (small, mechanical, safe — confirmed via `find` that every target existed under `plans/archive/` before
editing): updated all 14 links' display text + href from `plans/active/...` to `plans/archive/...`, matching each doc's
actual current location. Re-ran `run_validators.py --scope all` → `OK: No broken links in plans/active/*.md`.

## Todos

- [x] ✅ [DOCS] P0. Fix the 3 stale links in `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`. (repo:
      unified-trading-pm)
- [x] ✅ [DOCS] P0. Fix the 2 stale links (3 occurrences) in `tradfi_consolidated_closeout_2026_07_18.md`. (repo:
      unified-trading-pm)
- [x] ✅ [DOCS] P0. Fix the 2 stale links in `defi_consolidated_closeout_aggregated_sources_2026_07_24.md`. (repo:
      unified-trading-pm)
- [x] ✅ [DOCS] P0. Fix the 7 stale links in `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`. (repo:
      unified-trading-pm)
- [x] ✅ [SCRIPT] P2. Consider whether the archival ritual's step 5 ("update every referrer's path corpus-wide") should
      be backed by an automated check (e.g. `run_validators.py` or a QG step run at archive-time rather than only
      surfacing fleet-wide at next quickmerge) so this recurs as a fast local failure for the archiving agent, not a
      fleet-wide QG-red discovered by an unrelated worker days later. (repo: unified-trading-pm) — Wired
      `validate_plan_links.py` into `run_hygiene_sweep.sh`'s `--precommit` fast path (and the full sweep), gated on any
      staged `plans/` change including renames (the existing staged-file scan used `--diff-filter=ACM`, which excludes
      git's default rename detection — a pure archival `git mv` commit would otherwise skip the whole precommit gate).
      Verified in isolated scratch repos: a stale-referrer archival commit now fails locally with exit 1 pointing at
      this ritual step; a correctly-repointed referrer passes; unrelated commits still no-op. —
      unified-trading-pm@701437723

## Codex SSOTs

No dedicated SSOT for this specific validator; the archival ritual itself is in workspace `CLAUDE.md` § "Plans —
format + authoring discipline" (the corpus-wide-referrer-update step, added 2026-07-23).
