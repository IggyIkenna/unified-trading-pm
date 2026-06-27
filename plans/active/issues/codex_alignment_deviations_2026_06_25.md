---
doc_type: plan
title: Codex Alignment Deviation Scan — 2026-06-25
created: 2026-06-25
source: [plan_hygiene_master]
parent_epic: plan_hygiene_master
assigned_vm: vm-cross-cutting
priority: P2
status: active
locked_by: live-defi-rollout
locked_since: 2026-05-21
summary: Produced by `[AGENT] P1` in `plans/epics/plan_hygiene_master.md` Phase 4.
nature: process
asset_group: cross-asset
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
---

# Codex Alignment Deviation Scan — 2026-06-25

Produced by `[AGENT] P1` in `plans/epics/plan_hygiene_master.md` Phase 4.

**Scope**: all 42 active plans with `## Codex SSOTs` sections; 8 had open todos + codex refs (semantic risk surface).

---

## Broken refs (file doesn't exist)

| Plan                                                                          | Ref                                                     | Status                                                                 |
| ----------------------------------------------------------------------------- | ------------------------------------------------------- | ---------------------------------------------------------------------- |
| `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` | `codex/02-data/sports-canonical-league-cup-registry.md` | NOT_YET_CREATED — marked "New:" in plan; acceptable for in-flight work |

**Action**: no action needed. The plan itself will create this doc when it ships.

---

## Semantic deviations (file exists but content contradicts plan todos)

**None detected.**

All sampled open todos align with cited codex docs:

- `downstream_services_manifest_canonicalisation_2026_06_01.md` — todos require `EmptyConfirmedReason` typed enums +
  `attempted_failed` states → codex confirms 4-state ledger ✓
- `tradfi_manifest_canonicalisation_2026_06_01.md` — todos mandate v9 schema + `pipeline_mode` partition → codex
  outlines matching multi-axis shard atoms ✓
- `instruments_manifest_canonicalisation_2026_06_01.md` — todos add `instrument_type` column + v9 canonicalisation →
  codex registers `instrument_type` as display-only (not shard axis) per multi-axis correction ✓
- `orchestrator_strict_vm_matching_and_plan_frontmatter_governance_2026_06_24.md` — codex dirs + files all exist with
  appropriate content ✓
- `prediction_venue_perps_and_live_clob_depth_2026_06_20.md`, `sports_manifest_canonicalisation_2026_06_01.md`,
  `capability_wizard_and_manifest_2026_06_11.md` — all codex refs exist and align ✓

---

## Verdict

**CLEAN.** The active plan corpus is well-aligned with codex SSOTs. The sole broken ref is a planned future doc (not a
regression).

---

## Methodology note

This scan covers the **mechanical** subset (do cited files exist?) + a **targeted semantic** check on plans with open
todos (do todos assume patterns the codex doc contradicts?). It does NOT replace an exhaustive paragraph-by-paragraph
audit of all 114 plans — that would require deeper agent reads. The targeted sample covers the highest-risk surface
(open todos × cited codex docs).

Next sweep recommended: after the next major codex refactor or plan corpus addition.
