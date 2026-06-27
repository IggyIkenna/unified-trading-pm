---
doc_type: plan
title: Sports Pipeline to 100% — Golden-Window-First (coordinator)
summary:
status: draft
nature: process
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-06-27
parent_epic: sports_master
assigned_vm: vm-sports
execution_scope:
priority:
estimate_class: infra
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 10
last_updated:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
---

# Sports Pipeline to 100% — Golden-Window-First

**Status: DRAFT — operator must flip to `active` and confirm `assigned_vm: vm-sports` before agents dispatch.**

**Context (re-homed 2026-06-27):** The sports G1→G5 foundation / golden-window / history-expansion work was re-homed
from `instruments_foundation_completeness_2026_06_24.md` (vm-cefi plan) to this vm-sports coordinator. The cefi plan's
sports section is now audit/context only; all sports dispatch runs here.

**Coordinator for children `sports_p0_*` … `sports_p2_*`** — create child plans as needed for each gate.

**Codex SSOTs:**
- `codex/02-data/availability-manifest-and-data-status.md`
- `codex/02-data/data-pipeline-correctness-hard-rule.md`

---

## Scope (from 2026-06-24 audit in `instruments_foundation_completeness_2026_06_24.md`)

**G1 — Non-canonical-league noise wipe:** api_football FIXTURES span 1,531 leagues vs the ~101 canonical
(1,437 non-canonical = ~106k noise rows). Wipe rows outside the canonical universe.

**G2 — Foundation holes diagnosis + re-run:** 2015–2017 = 0 captured (35,889 all-`empty_confirmed` across 76 MVP
leagues that played) + 40,041 `attempted_failed` (2018/2021/2023 clusters). Diagnose root cause, re-run backfill.

**G3 — Catalogue all-AG producer-crash fix:** all-AG producer crashed; diagnose + fix.

**G4 — Manifest-correctness fixes #2/#5/#6:** remaining correctness items from the 2026-06-24 audit.

**G5 — 100% golden-window coverage:** achieve 100% coverage for the canonical golden-window universe.

**Pre-staged work (already shipped in instruments_foundation_completeness_2026_06_24.md session):**
- #1 phantom-reconcile pipeline_mode fix (IS@c01bb1c)
- #2 understat per-league 404 2-way (IS@18398c8)
- #3 api_football MTDS wrong-source odds wipe (1.4M rows + 231,532 objects)
- #4 `DP_HIGH_ATTEMPTED_FAILED` alert (deployment-service@cb330f7)

Cross-reference audit context: `sports_golden_window_attempted_failed_remediation_2026_06_24.md` +
`sports_fixture_completeness_oracle_2026_06_24.md`.

---

## Gates (operator sign-off required at each)

- [ ] [INFRA] P0. G1 — Non-canonical noise wipe complete; verify no canonical-league rows dropped
- [ ] [INFRA] P0. G2 — 2015-17 zero-captured root-cause diagnosed; re-run backfill with honest 4-state reasons
- [ ] [INFRA] P1. G3 — All-AG catalogue producer crash fixed; catalogue rebuild green
- [ ] [INFRA] P1. G4 — Manifest-correctness fixes #2/#5/#6 applied and verified
- [ ] [INFRA] P1. G5 — Golden-window coverage reaches 100% for canonical universe

---

## Temporary states + their canonical follow-up plans

*(none yet — operator to add as work progresses)*
