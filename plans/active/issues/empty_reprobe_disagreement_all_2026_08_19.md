---
doc_type: issue
title: "Empty re-probe disagreements — today's new empties may be C1 bugs (2026_08_19)"
created: 2026-08-19
author: "reprobe_new_empty_confirmed.py (data-pipeline daily audit)"
parent_epic: observability_master
assigned_vm: planning
source:
  - reprobe_new_empty_confirmed.py
  - data_pipeline_hardening_self_monitoring_2026_06_22.md
locked_by: live-defi-rollout
summary: "The daily empty re-probe found cells that became empty_confirmed+SOURCE_RETURNED_ZERO today where the UAC coverage oracle SHOULD_HAVE_DATA (or a wired re-fetch returned rows), plus ambiguous ..."
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [manifest-hygiene, data-pipeline, honest-coverage, empty-reprobe]
related: [/plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md]
resolved_by:
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
---

# Empty re-probe disagreements — today's new empties may be C1 bugs (2026_08_19)

> Auto-filed by the daily data-pipeline audit `reprobe_new_empty_confirmed.py` (Wave 4b, Phase 5
> scripted→LLM escalation hop). A deterministic candidate list was non-empty — the
> verdicts below need a worker's judgment (real gap vs code bug, straggler
> vs intentional new venue). See `/codex/05-infrastructure/data-pipeline-alerts.md`.

## What I found

The daily empty re-probe found cells that became empty_confirmed+SOURCE_RETURNED_ZERO today where the UAC coverage oracle SHOULD_HAVE_DATA (or a wired re-fetch returned rows), plus ambiguous cells. AGs: cefi, defi, prediction, sports, tradfi.

Candidate list(s) (deterministic, machine-written):

- `/app/unified-trading-pm/plans/audit/results/empty_reprobe_tradfi_2026_08_19.csv`

## Why it matters

This is the operator's #1 failure class (C1): a real-empty misclassified as honest-absence. An ORACLE_EXPECTS_DATA / REPROBE_RETURNED_ROWS verdict means the data exists but we recorded empty — a code bug, not a true gap. AMBIGUOUS verdicts need judgment (oracle silent + no re-fetch hook).

## Recommended decision

For each disagreement: trace the adapter path that recorded the empty and route it to record_failed (thread fetch_evidence per Phase 1). For ambiguous: decide real-gap vs new-venue, extend the oracle. Per data_pipeline_hardening_self_monitoring_2026_06_22.md Phase 1/5.

Cold-start context: read `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
in full + `/codex/05-infrastructure/data-pipeline-alerts.md` + the candidate CSV(s)
above before acting.

## Todos

- [ ] [CODE] P1. Empty re-probe disagreements — today's new empties may be C1 bugs (2026_08_19) — diagnose + fix the root cause (misclassified-empty vs real gap, not-v9 schema row, or oracle-expects-but-empty divergence) in `market-tick-data-service`. Read `SUB_AGENT_MANDATORY_RULES.md` + the data-pipeline codex SSOT + the candidate CSV(s) above first (source `reprobe_new_empty_confirmed.py`).
