---
doc_type: issue
title: Empty re-probe disagreements — today's new empties may be C1 bugs (2026_06_22)
summary:
  The daily empty re-probe found cells that became empty_confirmed+SOURCE_RETURNED_ZERO today where the UAC coverage
  oracle SHOULD_HAVE_DATA (or a wired re-fetch returned rows), plus ambiguous cells....
status: archived
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [manifest, data-quality, data-correctness, honest-coverage, defi, audit, data-status]
related: [data_pipeline_hardening_self_monitoring_2026_06_22]
created: 2026-06-22
parent_epic: infrastructure_master
priority: P2
source: [reprobe_new_empty_confirmed.py, data_pipeline_hardening_self_monitoring_2026_06_22.md]
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
---

# Empty re-probe disagreements — today's new empties may be C1 bugs (2026_06_22)

> **✅ ARCHIVED as stale (archived 2026-07-27)** — a single dated snapshot (4 defi cells, `ORACLE_EXPECTS_DATA`: ALCHEMY
> gas_fees, CHAINLINK oracle_prices, CURVE dex_pool_state, PANCAKESWAP_V3 dex_pool_state) with no recurring instance
> found in the original `/plan-vintage-audit` pass. The reprobe mechanism has since industrialized into a scheduled
> auto-flip system, but that system never auto-flips `ORACLE_EXPECTS_DATA` verdicts specifically — so these 4 cells were
> never mechanically re-resolved. Archived as a known, accepted gap (not a false-positive, not re-probed this session)
> rather than re-litigated — operator-directed default disposition per
> `/plans/active/june_2026_vintage_audit_findings_2026_07_27.md` §2 (also cross-referenced in that doc's §6 as
> "unclear," resolved to this same disposition in the same session). Per
> `/plans/active/june_2026_vintage_audit_findings_2026_07_27.md` §2.

> Auto-filed by the daily data-pipeline audit `reprobe_new_empty_confirmed.py` (Wave 4b, Phase 5 scripted→LLM escalation
> hop). A deterministic candidate list was non-empty — the verdicts below need a planning-VM slot's judgment (real gap
> vs code bug, straggler vs intentional new venue). See `/codex/05-infrastructure/data-pipeline-alerts.md`.

## What I found

The daily empty re-probe found cells that became empty_confirmed+SOURCE_RETURNED_ZERO today where the UAC coverage
oracle SHOULD_HAVE_DATA (or a wired re-fetch returned rows), plus ambiguous cells. AGs: defi.

Candidate list(s) (deterministic, machine-written):

- `/home/ubuntu/unified-trading-system-repos/unified-trading-pm/plans/audit/results/empty_reprobe_defi_2026_06_22.csv`

## Why it matters

This is the operator's #1 failure class (C1): a real-empty misclassified as honest-absence. An ORACLE_EXPECTS_DATA /
REPROBE_RETURNED_ROWS verdict means the data exists but we recorded empty — a code bug, not a true gap. AMBIGUOUS
verdicts need judgment (oracle silent + no re-fetch hook).

## Recommended decision

For each disagreement: trace the adapter path that recorded the empty and route it to record_failed (thread
fetch_evidence per Phase 1). For ambiguous: decide real-gap vs new-venue, extend the oracle. Per
data_pipeline_hardening_self_monitoring_2026_06_22.md Phase 1/5.
