---
doc_type: issue
title: PM quality-gates.sh RED — plan-discipline ratchet (121 > baseline 120) + frontmatter-schema violation
summary: >-
  unified-trading-pm's quality-gates.sh fails repo-wide on 2 pre-existing, unrelated checks (plan-discipline ratchet 121
  > baseline 120; a frontmatter-schema gap on sports-2020-06-data-floor.md), blocking the green-tree ship gate for any
  non-docs(plans) PM commit.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, plan-discipline, frontmatter-schema, governance]
related: []
created: "2026-07-21"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: planning
resolved_by:
locked_by:
source: [deployment_ui_vm_log_viewer_2026_07_20.md]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# What I found

Running `bash scripts/quality-gates.sh` in `unified-trading-pm` (needed to ship an unrelated 1-line
`configs/cloud-providers.yaml` sync fix) fails on 2 pre-existing, unrelated checks:

1. **Plan discipline regression** — `scripts/quality_gates/check_plan_discipline.py` reports 121 violations vs the
   committed baseline of 120 (`scripts/quality_gates/plan_discipline_baseline.yaml`). Breakdown:
   42×`A-deferred-no-banner` (a plan contains `DEFERRED` but no `## Deferred work — migrated to:` banner), 79×
   `C-archive-no-successor`. This is off-by-one over baseline — some plan committed since the baseline was last written
   tipped it over (fleet-wide plan churn, not attributable to any single commit I can find without a full `git bisect`
   across dozens of concurrent slots).
2. **Frontmatter schema violation** — `codex/02-data/sports-2020-06-data-floor.md`: `referenced_by` optional key is
   absent (schema requires present-but-empty, not fully absent).

Verified pre-existing: my only staged change was `configs/cloud-providers.yaml` (a data-only sync, see
`unified-api-contracts@83506de0` / `unified-trading-library@e22e40f1` for the same fix in the other 2 copies of this
file). Neither failing check references that file.

# Why it matters

`unified-trading-pm`'s `quality-gates.sh` gates EVERY quickmerge ship through this repo (plan authoring, cross-repo
`docs(plans):` flips land via raw push and are unaffected, but any non-plan PM commit — like this config sync — needs
the full gate green to get a quickmerge sentinel). With ~50+ backlog tasks draining concurrently across slots, this repo
is high-churn; a ratchet regression here silently blocks anyone who needs a non-`docs(plans):` PM commit to ship
normally.

# Recommended decision

- Re-run `scripts/quality_gates/check_plan_discipline.py` to enumerate the 121 current violations, diff against
  `plan_discipline_baseline.yaml`, and either (a) add the missing `## Deferred work — migrated to:` banners / archive
  successor refs for the 1 (or more) new offenders, or (b) if the regression is legitimate accumulated debt from many
  small plan edits fleet-wide, re-baseline with `--baseline-write` per the check's own remedy text, with an operator
  sign-off note on why the ratchet moved.
- Add the missing `referenced_by: []` (or equivalent empty-but-present key) to
  `codex/02-data/sports-2020-06-data-floor.md` frontmatter.

## Todos

- [x] [DOCS] P2. ✅ Fix `codex/02-data/sports-2020-06-data-floor.md` frontmatter — add the missing `referenced_by` key
      (present-but-empty is enough to pass `scripts/docs/seed_frontmatter.py --apply`) — unified-trading-pm@3122de370.
      Ran the remedy tool as-instructed; it also seeded the elective `implementation_status` key.
      `check_frontmatter_schema.py` now reports zero violations across all 1739 docs; full `quality-gates.sh` for this
      repo now passes clean end-to-end (both todos in this issue doc closed — plan-discipline ratchet fix landed
      @522dcdf92). (repo: unified-trading-pm)
- [x] [DOCS] P2. ✅ Triage the 121 plan-discipline violations (42 `A-deferred-no-banner` + 79 `C-archive-no-successor`)
      against baseline 120 in `scripts/quality_gates/plan_discipline_baseline.yaml` — unified-trading-pm@522dcdf92. Real
      fix, not a blind re-baseline: enumerated all 121, classified each by whether an honest templated banner applies.
      19/79 archived `C-archive-no-successor` plans had **zero open `- [ ]` items** (100%-closed) — applied the
      established `## Deferred work — migrated to: **None** — successor: not applicable` banner (same template as
      precedent commit `835ef6114`). This is the ONLY subset a scripted fix can honestly close — everything else needs
      real per-plan judgment: 60/79 archived plans still have open items (1–139 each) and 42/42 active
      `A-deferred-no-banner` plans have un-qualified DEFERRED mentions, both requiring a human/plan-owner call on the
      actual successor, not a generic banner. Net: 121 → 102 violations, comfortably clears baseline 120 without gaming
      it (an improvement, not just a ratchet raise) — re-baselined 120 → 102 via `--baseline-write` to codify. Remaining
      102 (42 A + 60 C) is genuine accumulated fleet-wide plan-corpus debt, not attributable to one commit; tracked as a
      fresh P3 follow-up todo below rather than force-fit into this P2 task's scope. (repo: unified-trading-pm)
- [ ] [DOCS] P3. Remaining plan-discipline debt (baseline now 102, down from 120): 42 active plans with unqualified
      `DEFERRED` mentions need per-plan judgment on whether to add inline `DEFERRED-<QUALIFIER>` annotations (see
      precedent `f6df716e7`) or a real `## Deferred work — migrated to:` banner naming an actual successor; 60 archived
      plans with 1–139 open `- [ ]` items each need a real successor plan identified (or a decision that the open items
      are abandoned) before a `C-archive-no-successor` banner can be added honestly — do NOT blanket-apply the "no
      successor needed" template to these, it would be false for plans with real open work. Split across multiple P3
      tasks by plan-owner/asset_group if picked up; not a single sitting. (repo: unified-trading-pm)
