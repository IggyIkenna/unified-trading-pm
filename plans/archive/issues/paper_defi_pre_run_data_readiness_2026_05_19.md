---
doc_type: issue
title: Paper-DeFi VM launches without verifying features-onchain data prerequisites
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, e2e-testing, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-19
author: ikenna-main (flagged from ~15:15 UTC Slack discussion)
source:
  [
    "Ikenna ↔ Harsh Slack thread 2026-05-19 ~15:11-15:15 UTC",
    paper defi was ambitious it didnt even chekc it has features data it needed. backfill last 30 days hasnt run etc and
    needs live streaming of the data pipeline,
  ]
locked_by: live-defi-rollout
---

> **🟡 COVERED BY**
> [../phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md](../phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md) +
> [../promote_workflow_may23_cli_path_2026_05_10.md](../promote_workflow_may23_cli_path_2026_05_10.md) —
> `PaperRunDataReadinessCheck` is a feature of `e2e-testing/scripts/defi/run-paper.sh` owned by the May-23 CLI promote
> plan (slot-1 triage 2026-05-20). Will also leverage mega-audit Phase A2 `expected_coverage()` once it lands. Archive
> when parent plans close.

# Paper-DeFi pre-run data-readiness gap

## What I found

The DeFi paper-trading runbook (e2e-testing/scripts/defi/run-paper.sh → strategy-service paper VM launchers in
`deployment-service/scripts/vm/`) launches the VM and starts the colocated_engine WITHOUT first verifying that:

1. **Features-onchain backfill** has run for the last 30 days for the archetype's required clusters (e.g. `lst_yields`,
   `lending_rates`, `paired_price_dispersion`)
2. **Live streaming** of the data pipeline (MTDS → MDPS → features-onchain → strategy) is healthy and emitting fresh
   data
3. **Cluster validation** at the strategy reader confirms all required clusters have non-empty parquets for the run
   window

Result: a paper VM launched 2026-05-18 (B-015 / pvl-p18a, mentioned in harsh-main 2026-05-19 ping ledger) ran through
the gate but the underlying strategy was effectively no-op'd by missing-data short-circuits internally. "2 days wasted"
per harsh-main's reflection.

## Why it matters

- **Live-DeFi 2026-05-23 cutover gate** depends on ≥1 paper run + ≥1 live early run reaching their respective success
  criteria. A paper run that silently produces nothing is worse than no run — it gives a false signal that the gate is
  met.
- **Operator trust in pre-run gates** — every paper/live launch should fail loud on data prerequisites, not silently.
  This is the spirit of the workspace's "Manifest + honest absence" HARD RULE applied to the strategy-runner entry
  point.
- **Master plan Group F readiness items** count paper-run successes; an unverified-data success is a phantom F-row.

## Recommended decision

Add a **PaperRunDataReadinessCheck** gate to `e2e-testing/scripts/defi/run-paper.sh` (and the underlying
`colocated_engine.py` startup) that:

1. Reads the archetype's required clusters from UAC (already in
   `unified_api_contracts.registry.capability_declarations._defi`).
2. For each cluster: probe `features-onchain` manifest for last-30-day row count + check `available_at` mtime < 60min
   (live-streaming proxy).
3. If ANY required cluster fails: exit 2 BEFORE launching the paper VM with a clear error message listing missing
   clusters + recommended fix (backfill command, MTDS stream status).
4. Document the gate in `/codex/09-strategy/operational/cli-promote-paths.md`
   - add a runbook checkbox `paper_run_data_readiness_check_landed`.

**Estimated work**: ~1-2 AI-days. `infra` class (0.8× multiplier) → ~0.8-1.6 calibrated AI-days.

## Routing

Owner: **harsh-side** (strategy-service + e2e-testing are harsh-side surfaces per CLAUDE.md Daily Work-Split Process).
ikenna-side flags this issue here; harsh-side decides when to land (suggested: BEFORE the next paper-VM relaunch).

## Cross-link

This is adjacent to but NOT part of `agent_orchestrator_cloud_run_deployment_2026_05_19.md` (that plan is
orchestrator-only). It's a strategy-service hardening task that belongs in the live-defi master plan's Group F.
