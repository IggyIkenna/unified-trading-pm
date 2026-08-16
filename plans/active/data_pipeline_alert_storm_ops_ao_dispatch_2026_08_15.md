---
doc_type: plan
title: AO VM cross-cloud WIF + chain-relabel part 2 dispatch + combo_chain expiration ruling
summary: >-
  Operator-ruled 2026-08-16 (na-eligibility-audit follow-up Q&A, round 2) — three items from
  data_pipeline_alert_storm_root_cause_batch_2026_08_10.md: stand up cross-cloud Workload
  Identity Federation for the AO VM, re-verify then dispatch the chain relabel migration part
  2 execution plan, and record the combo_chain expiration ruling (each leg's own instrument_id
  already carries expiration, matching the options_chain/futures_chain precedent — no separate
  chain-level field needed).
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta, data]
repos: [agent-orchestrator, instruments-service, unified-api-contracts]
scope: [engineer]
tags: [ao, observability, wif, canonicalization, combo_chain]
related:
  [
    /plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: infra
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 2, 2026-08-16"
locked_by:
context_scope:
  [
    /plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md,
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
    unified-api-contracts/unified_api_contracts/canonical/_partition_path_canonicality.py,
  ]
locked_since:
resolved_by:
---

# AO VM cross-cloud WIF + chain-relabel part 2 dispatch + combo_chain expiration ruling

## Todos

- [ ] [INFRA] P1. Stand up cross-cloud Workload Identity Federation for the AO VM (per
      `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md` line 307) — replaces whatever long-lived static
      cross-cloud credential the AO VM currently holds. Operator approved 2026-08-16. (repo: agent-orchestrator)
- [ ] [DATA] P1. Re-verify the chain relabel migration part 2 execution plan is still current against live state
      (per line 332 — direction already approved), then dispatch execution. Given how much has landed on this
      branch recently, do not trust a stale citation — re-measure before executing. (repo: instruments-service)
- [ ] [DOCS] P3. Record the combo_chain expiration ruling: `combo_chain` is a chain-type shard (same
      `CEFI_CHAIN_INSTRUMENT_TYPES`/`TRADFI_CHAIN_INSTRUMENT_TYPES` frozenset as `options_chain`/`futures_chain` in
      `unified_api_contracts/canonical/_partition_path_canonicality.py`) — each leg-row carries its own full
      `instrument_id` with its own embedded expiration, matching the established sibling-type precedent. No separate
      chain-level expiration field is needed. Update the combo_chain schema doc/docstring to state this explicitly so
      the question (line 804) doesn't get re-asked. (repo: unified-api-contracts)

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 2, operator ruling)**: extracted from
  `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`. Combo_chain ruling was verified live against
  `unified_api_contracts/canonical/_partition_path_canonicality.py` before being recorded — not taken on the
  operator's framing alone.
- **context-scout 2026-08-16**: populated context_scope (3 entries).
