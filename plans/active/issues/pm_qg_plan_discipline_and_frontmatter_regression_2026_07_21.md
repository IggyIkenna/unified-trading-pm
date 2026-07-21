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

- [ ] [DOCS] P2. Fix `codex/02-data/sports-2020-06-data-floor.md` frontmatter — add the missing `referenced_by` key
      (present-but-empty is enough to pass `scripts/docs/seed_frontmatter.py --apply`). (repo: unified-trading-pm)
- [ ] [DOCS] P2. Triage the 121 plan-discipline violations (42 `A-deferred-no-banner` + 79 `C-archive-no-successor`)
      against baseline 120 in `scripts/quality_gates/plan_discipline_baseline.yaml` — add banners/successor-refs for
      genuine new offenders, or re-baseline with `--baseline-write` + an operator-approved note if this is accumulated
      fleet-wide debt rather than one bad commit. (repo: unified-trading-pm)
