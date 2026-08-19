---
doc_type: issue
title: "manifest_hygiene_daily.py / reprobe_new_empty_confirmed.py auto-file issue docs with plan-shaped frontmatter — recurring daily QG break"
created: 2026-08-19
parent_epic: observability_master
assigned_vm: planning
resolved_by:
source:
  - e2e-testing/scripts/audit/manifest_hygiene_daily.py
  - e2e-testing/scripts/audit/reprobe_new_empty_confirmed.py
locked_by:
summary: >-
  The two daily data-pipeline auto-filers write their findings docs into
  unified-trading-pm/plans/active/issues/ with `doc_type: plan`, `status: active`, and
  `asset_group: cross-asset` (not a valid frontmatter enum value) instead of the required
  `doc_type: issue` / `status: open` / `asset_group: [cross-cutting]` shape — every fresh
  doc they file trips `check_frontmatter_schema` and reds the next quality-gates-v2 run
  until a human/agent manually patches the frontmatter after the fact.
status: open
nature: issue
asset_group: [cross-cutting, ci]
stage: [data, meta]
repos: [e2e-testing, unified-trading-pm]
scope: [engineer, admin]
tags: [frontmatter, doc-governance, quality-gates, manifest-hygiene, auto-filer, recurring]
related: [manifest_hygiene_red_all_2026_08_19, empty_reprobe_disagreement_all_2026_08_19]
priority: P2
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# manifest_hygiene_daily.py / reprobe_new_empty_confirmed.py auto-file issue docs with plan-shaped frontmatter — recurring daily QG break

## What I found

Resolving escalation `agt-064a24` (promote_qg_failure, unified-trading-pm PR #3492, continuously red 51min)
traced the failure to `check_frontmatter_schema` rejecting
`plans/active/issues/manifest_hygiene_red_all_2026_08_19.md`: `doc_type: plan` (path-derived
type is `issue`), `status: active` (not a valid issue status), `asset_group: cross-asset` (not
in the enum), `tags: []`, `resolved_by` absent. The full local `quality-gates.sh` run then
surfaced a second, freshly-filed doc with the exact same defect shape:
`plans/active/issues/empty_reprobe_disagreement_all_2026_08_19.md`. Both are auto-filed by
scripts in `e2e-testing/scripts/audit/` (`manifest_hygiene_daily.py`,
`reprobe_new_empty_confirmed.py`) — "Wave 4b, Phase 5 scripted→LLM escalation hop" per their own
doc preamble.

Checking the equivalent 2026-08-18 docs (`manifest_hygiene_red_all_2026_08_18.md`,
`empty_reprobe_disagreement_all_2026_08_18.md`) shows they now carry correct
`doc_type: issue` / `status: open|resolved` / `asset_group: [cross-cutting]` frontmatter — but
that correction was applied by hand after filing (visible in their status trailing comments),
not by the filer itself. This is a recurring pattern, not a one-off: every day's fresh
auto-filed doc ships broken and needs a human/agent to notice and hand-patch it before the next
promote PR's QG run, and on 2026-08-19 nobody had yet, which is what produced the 51-minute red
wall this escalation was dispatched for.

## Why it matters

This is silent, recurring toil that directly causes fleet-wide promote-PR QG failures — the
exact wall type `quality_gate_resolution` exists to firefight. Fixing the filer template once
(in `e2e-testing/scripts/audit/`) removes the daily manual-patch step and prevents the next
occurrence, rather than firefighting it fresh each day.

## Recommended decision

In `e2e-testing/scripts/audit/manifest_hygiene_daily.py` and `reprobe_new_empty_confirmed.py`
(or a shared frontmatter-template helper they both call, not yet located in this pass — search
`e2e-testing/scripts/audit/` and any shared `scripts/` helper it imports), fix the emitted
frontmatter block to the issue-doc schema (`/codex/11-project-management/doc-frontmatter-schema.md`
§3 `issue` row): `doc_type: issue`, `status: open`, `asset_group: [cross-cutting]` (or the
correct domain enum value(s) for the finding), non-empty `tags:`, and a present-but-empty
`resolved_by:`. Verify against `scripts/plan-hygiene/check_frontmatter_schema.py` before
declaring done.

## Todos

- [ ] [CODE] P2. Fix `manifest_hygiene_daily.py` + `reprobe_new_empty_confirmed.py` (and any
      shared filer helper) in `e2e-testing` to emit schema-valid issue-doc frontmatter
      (`doc_type: issue`, valid `status`, valid `asset_group` enum value(s), non-empty `tags`,
      present-but-empty `resolved_by`) so future auto-filed docs pass
      `check_frontmatter_schema` on first write instead of needing daily manual correction.
