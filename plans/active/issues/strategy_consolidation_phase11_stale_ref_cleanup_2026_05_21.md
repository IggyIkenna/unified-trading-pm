---
title: "Strategy consolidation Phase 11 — workspace stale-ref cleanup (slots 5/6/8/3)"
created: 2026-05-21
author: slot-2
source:
  - plans/active/strategy_repo_consolidation_2026_05_19.md
locked_by: live-defi-rollout
parent_epic: strategy_master
---

## What I found

`strategy_repo_consolidation_2026_05_19.md` Phase 11 (reopened 2026-05-20 per operator) identified **~206 live-code
references** to the 3 now-GitHub-archived services (`risk-and-exposure-service`, `position-balance-monitor-service`,
`pnl-attribution-service`) across 7 consumer repos. Phase 11a (deployment-service) and Phase 11g (strategy-service own)
are **done**. The remaining 6 sub-phases are open and assigned to specific slots.

### Open sub-phases

| Phase | Scope                                                                                                                                        | Slot   | Priority | Est.             |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------ | -------- | ---------------- |
| 11b   | unified-api-contracts: ~75 live refs (risk_rule.py, kill_switch.py, service_emission_policy.py, circuit_breaker.py, registry/)               | slot 5 | P0       | 0.75 cal-AI-days |
| 11c   | unified-trading-library: ~33 live refs (test fixtures in test_emission_publisher.py, test_topology_reader.py, test_auth_entitlements.py)     | slot 5 | P0       | 0.25 cal-AI-days |
| 11d   | unified-trading-system-ui: ~50 live refs (data-flow-manifest.json, workspace-manifest.json, dashboard service cards, monitoring panels)      | slot 6 | P0       | 0.5 cal-AI-days  |
| 11e   | execution-service: ~18 live refs (preflight.py:28 hardcoded risk-service URL — HIGH, live runtime ref)                                       | slot 8 | P1       | 0.25 cal-AI-days |
| 11f   | alerting-service + system-integration-tests + e2e-testing + trading-agent-service: ~30 live refs                                             | slot 3 | P1       | 0.5 cal-AI-days  |
| 11h   | DEPRECATION_NOTICE audit: verify each of 3 archived repos has correct DEPRECATION_NOTICE.md pointing to strategy_service/{risk,position,pnl} | slot 6 | P0       | 0.1 cal-AI-days  |

**Total remaining**: ~206 refs, ~2.35 cal-AI-days.

### High-severity item

Phase 11e `execution-service/execution_service/preflight.py:28` contains a **hardcoded runtime URL** pointing to
`risk-and-exposure-service`. This is a live execution path — it will silently fail if the risk service is fully
decommissioned. Slot 8 owns this cleanup and it composes with `strategy_execution_contract_remediation_2026_05_20.md`
Phase 4a/4b work.

## Why it matters

The 3 GitHub-archived services are no longer deployable. Any hardcoded URL, service-name enum, or topology-map entry
pointing at them is dead code at best and a silent failure at worst (execution preflight, alert aggregator health
checks). The cleanup is mechanical grep+sed but must be verified with per-repo QG green.

## Recommended decision

Assign Phase 11b/c to slot 5, Phase 11d/11h to slot 6, Phase 11e to slot 8, Phase 11f to slot 3. Each slot picks up
their phase, runs the repo-specific QG, flips the checkbox here when done.

Done when all 6 sub-phases have green QG evidence + checkbox flipped.

## Todos

- [x] ✅ [AGENT slot 3] P0. Phase 11b — unified-api-contracts stale-ref cleanup (~75 live refs). Gate: UAC QG green +
      cassette parity green. — unified-api-contracts@23e2b58 (3560 passed; service_emission_policy, event_topics, service_contract_map, nav_snapshot, allowlist fix; 2026-05-23)
- [ ] [AGENT slot 5] P0. Phase 11c — unified-trading-library stale-ref cleanup (~33 live refs). Gate: UTL QG green.
- [ ] [AGENT slot 6] P0. Phase 11d — unified-trading-system-ui stale-ref cleanup (~50 live refs). Gate: UI QG green +
      dev-tier 0 boot test.
- [ ] [AGENT slot 6] P0. Phase 11h — DEPRECATION_NOTICE audit: verify 3 archived repos. Gate: ack in audit trail +
      checkbox flip.
- [ ] [AGENT slot 8] P1. Phase 11e — execution-service stale-ref cleanup (~18 live refs, includes live runtime URL in
      preflight.py:28). Gate: ES QG green.
- [ ] [AGENT slot 3] P1. Phase 11f — tail consumer cleanup: alerting + sys-int-tests + e2e + trading-agent (~30 live
      refs). Gate: per-repo QG green.

Full scope per sub-phase documented in
[`strategy_repo_consolidation_2026_05_19.md`](../archive/2026_05/strategy_repo_consolidation_2026_05_19.md) Phase 11
body.
