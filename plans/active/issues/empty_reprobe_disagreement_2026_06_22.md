---
title: "Empty re-probe disagreements — today's new empties may be C1 bugs (2026_06_22)"
created: 2026-06-22
source:
  - reprobe_new_empty_confirmed.py
  - data_pipeline_hardening_self_monitoring_2026_06_22.md
locked_by: live-defi-rollout
priority: P2
status: active
---

# Empty re-probe disagreements — today's new empties may be C1 bugs (2026_06_22)

> Auto-filed by the daily data-pipeline audit `reprobe_new_empty_confirmed.py` (Wave 4b, Phase 5
> scripted→LLM escalation hop). A deterministic candidate list was non-empty — the
> verdicts below need a planning-VM slot's judgment (real gap vs code bug, straggler
> vs intentional new venue). See `codex/05-infrastructure/data-pipeline-alerts.md`.

## What I found

The daily empty re-probe found cells that became empty_confirmed+SOURCE_RETURNED_ZERO today where the UAC coverage oracle SHOULD_HAVE_DATA (or a wired re-fetch returned rows), plus ambiguous cells. AGs: defi.

Candidate list(s) (deterministic, machine-written):

- `/home/ubuntu/unified-trading-system-repos/unified-trading-pm/plans/audit/results/empty_reprobe_defi_2026_06_22.csv`

## Why it matters

This is the operator's #1 failure class (C1): a real-empty misclassified as honest-absence. An ORACLE_EXPECTS_DATA / REPROBE_RETURNED_ROWS verdict means the data exists but we recorded empty — a code bug, not a true gap. AMBIGUOUS verdicts need judgment (oracle silent + no re-fetch hook).

## Recommended decision

For each disagreement: trace the adapter path that recorded the empty and route it to record_failed (thread fetch_evidence per Phase 1). For ambiguous: decide real-gap vs new-venue, extend the oracle. Per data_pipeline_hardening_self_monitoring_2026_06_22.md Phase 1/5.
