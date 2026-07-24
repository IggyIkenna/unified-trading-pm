---
doc_type: plan
title: Per-client isolation + venue fanout topology (May-23 cutover gate)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, execution-service, strategy-service]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/archive/2026_07/master_to_live_defi_2026_05_23.md,
    /plans/archive/2026_05/strategy_repo_consolidation_2026_05_19.md,
    /plans/archive/2026_05/promote_workflow_may23_cli_path_2026_05_10.md,
    /plans/archive/2026_05/api_keys_wallets_accounts_readiness_2026_05_10.md,
  ]
created: "2026-05-20"
parent_epic: client_isolation_and_governance_master
priority: P0
estimate_class: brand-new
estimate_baseline_ai_days: 5.0
estimate_calibrated_ai_days: 5.0
locked_by: live-defi-rollout
locked_since: 2026-05-20
---

# Per-Client Isolation + Venue Fanout Topology

Multi-client subprocess isolation under `StrategySupervisor`: each client runs as an isolated OS subprocess
(`ClientWorker`), crash-isolated, with hot credential reload via KMS. `MarkPriceAggregator` computes MTM once per symbol
per tick in supervisor and broadcasts via shared memory to all workers. `ClientLifecycleEvent` bus supports
REGISTER/DEREGISTER/QUARANTINE/CREDENTIAL_ROTATED. HARD RULE codified: funds NEVER move between different clients;
`CrossClientTransferForbiddenError` raised at 2 defensive layers.

Codex SSOTs: `/codex/04-architecture/per-client-isolation-architecture.md` -
`/codex/04-architecture/client-funds-isolation.md` - `/codex/05-infrastructure/strategy-shard-vm-topology.md`

---

## Phase 0 -- UAC schema base

- [x] ✅ [AGENT] P0. UAC `ClientRecord` + `ClientsYamlSchema` + `ClientLifecycleEvent` schemas;
      `CrossClientTransferForbiddenError`; `assert_client_allowed()` guard. (uac@`d0f72fd`)

## Phase 1 -- UTL base classes

- [x] ✅ [AGENT] P0. UTL `BaseModeHandler` + `BaseClientWorker` + `BaseStrategySupervisor` base classes; shared-memory
      IPC helpers; `classify_venue_error()` error surface. (utl@`cae77ad9`)

## Phase 2 -- StrategySupervisor

- [x] ✅ [AGENT] P0. `strategy_service/supervisor/strategy_supervisor.py` -- process lifecycle, CLIENT_READY/QUARANTINE
      FSM, ShardCapacitySensor, `MarkPriceAggregator` single-compute pattern. (strategy-service@`4fb14035`)

## Phase 3 -- ClientWorker + IPC

- [x] ✅ [AGENT] P0. `strategy_service/supervisor/client_worker.py` -- per-client subprocess; shared-memory ring-buffer
      read; venue fanout per ClientRecord; crash/restart loop (max 5 before QUARANTINE). (strategy-service@`4fb14035`)

## Phase 4 -- Preflight + hot-credential reload

- [x] ✅ [AGENT] P0. `strategy_service/supervisor/preflight.py` -- per-client venue-connectivity + IS preflight; KMS
      poll-based credential rotation (pull) + event-bus push (CREDENTIAL_ROTATED); `hot_reload_credentials()` wired.
      (strategy-service@`6506f868`)

## Phase 5 -- Execution-service doc + TransferCoordinator

- [x] ✅ [AGENT] P0. Codex docs for OMS protocol + multi-venue routing + execution per-client isolation. (PM@`b1664fe8`)
- [x] ✅ [AGENT] P0. `execution_service/transfer_coordinator.py` `TransferCoordinator` -- single entry point for
      TransferIntent events; thread-safe idempotency cache; HARD RULE cross-client rejection at 2 layers;
      SUBACCOUNT_MOVE for Binance + OKX only. (execution-service@`35c15f60`)

## Phase 6 -- E2E + unit test bundle

- [x] ✅ [AGENT] P0. 2-client May-23 e2e: StrategySupervisor with us + defi-client-1; crash isolation (kill -9 ->
      restart <16s, peer unaffected); QUARANTINE after 5 failures; capacity simulation; shared-memory p99 < 100us. 64/64
      per_client_isolation tests green; 20+ transfer_coordinator tests green. (strategy-service@`6817cf7c`,
      execution-service@`35c15f60`)

## Phase 7 -- Deployment-service wiring

- [x] ✅ [AGENT] P0. `launch-strategy-paper-vm.sh` + `launch-strategy-live-vm.sh` accept `--shard N` +
      `--clients-yaml-path`; VM name pattern `strategy-{mode}-{archetype}-shard{N}-{ts}`; `VM_PREFIX_TO_BUCKET` updated;
      `POST /api/strategy/shard/spawn` + `drain` endpoints; per-archetype `clients.yaml` configs; `ClientsYamlSchema` in
      UAC. (uac@`816d1aa`, deployment-service@`8efb315`, deployment-api@`5a5b07d`)

## Phase 8 -- Codex SSOT

- [x] ✅ [AGENT] P1. 8 codex docs shipped: per-client-isolation-architecture.md,
      execution-service-per-client-isolation.md, oms-protocol-and-state-machine.md, multi-venue-concurrent-routing.md,
      transfer-coordinator.md, client-lifecycle-event-bus.md, strategy-shard-vm-topology.md,
      promote-workflow-architecture.md updated. (PM@`32d1929d`, PM@`b1664fe8`)

## Deferred work — migrated to: `plans/epics/client_isolation_and_governance_master.md` § Deferred

See `client_isolation_and_governance_master.md` § "Deferred from per_client_isolation_and_venue_fanout_topology".

## ⚠️ ARCHIVED 2026-05-22 — all Phases 0-8 shipped; deferred items migrated to epic body

## Post-cutover deferred

- [x] ✅ **POST-MAY-23** [AGENT] P1. Phase E.2 -- Auto-shard supervisor signal: deployment-service consumes
      `ShardCapacityEvent.SPAWN_NEW_SHARD` + auto-launches next shard VM. Target: 2026-05-28. **[DEFERRED-POST-CUTOVER
      2026-05-23 slot 6]** POST-MAY-23 item targeting 2026-05-28+. Gated on deployment-service (not in slot 6 worktree)
      and DeFi cutover. Operator-driven post-cutover.
- [x] ✅ **POST-MAY-23** [AGENT] P2. Phase E.3 -- Intra-client RebalanceCoordinator (intra-client multi-portfolio +
      intra-client multi-wallet ONLY; cross-client fund movement is NEVER in scope -- HARD RULE). Target: 2026-06-01.
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** POST-MAY-23 item targeting 2026-05-28+. Gated on deployment-service
      (not in slot 6 worktree) and DeFi cutover. Operator-driven post-cutover.

## Temporary states + canonical follow-up plans

- Auto-shard end-to-end: Phase E.2 (this plan), 2026-05-28.
- Intra-client rebalancing: Phase E.3 (this plan), 2026-06-01. Cross-client fund movement is PERMANENTLY out of scope.
- Sub-account transfers for non-Binance/OKX venues: `subaccount_transfers_phase_2_2026_06_01.md` (to be created).
