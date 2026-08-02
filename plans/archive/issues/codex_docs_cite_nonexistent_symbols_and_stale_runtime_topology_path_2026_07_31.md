---
doc_type: issue
title:
  "Codex docs cite symbols that exist in no repo (phantom API surface) + `runtime-topology.yaml` SSOT path is stale in 4
  docs outside the freshness-c shard"
summary: >-
  Surfaced during the staggered codex freshness re-review (shard offset-2 of the 113 docs still stamped `last_reviewed:
  2026-05-17`). Two residual classes were verified but deliberately NOT fixed in that shard's commit because they land
  in docs owned by other shards or outside the 05-17 set entirely — fixing them there would have collided with two
  sibling agents editing the same corpus concurrently. (A) Thirteen backticked identifiers are cited by codex docs as
  real API surface but return ZERO hits across every cloned repo — verified individually with `rg -F` after discovering
  that a bulk `rg -o -f patternfile` scan silently hides longer symbols behind shorter prefixes (`ClientOnboardingState`
  masked `ClientOnboardingStateMachine`), so any future sweep must verify per-symbol, not in bulk. (B)
  `deployment-service/configs/runtime-topology.yaml` no longer exists — the SSOT moved to
  `unified-trading-pm/configs/runtime-topology.yaml` (`owner: unified-trading-pm`, `version: 7`) and deployment-service
  now SYNCS it via `scripts/sync/sync-configs.py` — but 4 codex docs still cite the dead deployment-service path.
status: resolved
nature: issue
asset_group: [infrastructure] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [codex, docs, freshness, ssot-drift, phantom-symbols, runtime-topology]
related:
  [
    /codex/04-architecture/TOPOLOGY-DAG.md,
    /codex/04-architecture/client-lifecycle-state-machine.md,
    /codex/04-architecture/kill-switch-circuit-breaker.md,
  ]
created: 2026-07-31
priority: P3
parent_epic: infrastructure_master
source:
  [
    "Surfaced during staggered codex freshness re-review shard offset-2 (freshness-c, 2026-07-31) — re-reviewing the 37
    docs assigned to that shard out of the 113 still carrying last_reviewed: 2026-05-17.",
  ]
execution_scope: orchestrator-agent
drift_direction: none
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
  slot-3, 2026-07-31 — all 4 todos (A's per-symbol fix pass, A's offset-0/1 re-run, B's two repoints) done; no open
  todos remain, no locked_by, no referrers found workspace-wide.
---

# Codex docs cite phantom symbols; `runtime-topology.yaml` path stale outside the freshness-c shard

## Why this is an issue doc and not a fix

Three agents were re-reviewing disjoint thirds of the same 113-doc corpus concurrently against the same PM checkout.
Everything below is either (a) in a doc owned by a **sibling shard** or outside the 05-17 set, or (b) a phantom-symbol
finding whose correct resolution is a judgment call (delete the claim vs. implement the symbol) rather than a mechanical
doc fix. Both are captured here rather than silently edited across shard boundaries.

## A — Identifiers cited by codex docs that exist in NO cloned repo

Each verified individually with `rg -F '<symbol>' --glob '!*.venv*' --glob '!unified-trading-pm/**'` (zero files).
Caveat recorded honestly: the `unified-cloud-interface` and the `unified-*-interface` (UTEI/UDEI/UMI/USEI) repos are
**not cloned in this slot**, so a symbol below could in principle live there. The ones marked ✅ are safe calls because
a sibling symbol from the same module _was_ found, proving the owning module is present.

| Doc                                                     | Phantom symbol(s)                                                                                                             | Confidence                                       |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| `/codex/02-data/chart-candle-delivery-flow.md`          | `BarStore`                                                                                                                    | medium (candle readers are cloned)               |
| `/codex/04-architecture/capital-efficiency-patterns.md` | `allocated_usd`                                                                                                               | ✅ `AllocationDecisionEvent` found in UTL        |
| `/codex/04-architecture/concentrated-liquidity.md`      | `PoolKey`, `exttload`                                                                                                         | low — Uniswap V4 types may live in UDEI          |
| `/codex/04-architecture/share-class-architecture.md`    | `strategy_pnl_usd`                                                                                                            | medium                                           |
| `/codex/04-architecture/treasury-custody-flow.md`       | `CEFFUEnvironment`, `CopperEnvironment`, `amount_threshold_usd`, `force_single_approve`, `quorum_required`, `total_approvers` | ✅ `CEFFUEndpoint` found in client-reporting-api |
| `/codex/05-infrastructure/per-venue-paper-policy.md`    | `fork_url`, `live_rpc_url`                                                                                                    | medium                                           |

- [x] ✅ [DOCS] P3. Per-symbol, decide **delete-the-claim vs. implement-the-symbol** for each row above, then either fix
      the doc or open a build todo. Do NOT bulk-delete — `CEFFUEndpoint` proves some of this surface is real and
      partially shipped, so each row needs its own call. Verify with `rg -F` per symbol (never a bulk `rg -f`
      patternfile — see the prefix-shadowing trap below). — unified-trading-pm. Per-row verdicts: `BarStore` (false
      positive — doc already frames it as Phase-3 future work); `allocated_usd` (fix — real type is UTL
      `AllocationDecision.allocation_amount_usd`, not UAC `allocated_usd`); `PoolKey`/`exttload` (false positive —
      external Uniswap V4 protocol identifiers, not repo symbols); `strategy_pnl_usd` (fix — real field is
      `total_pnl_usd` in `strategy-service/.../settlement_service.py`); `CEFFUEnvironment`/`CopperEnvironment`/
      `amount_threshold_usd`/`force_single_approve`/`quorum_required`/`total_approvers` (fix — real
      `CopperEndpoint`/`CEFFUEndpoint` use `is_live: bool` not an environment enum; real `WithdrawalApprovalRule` fields
      are `threshold_amount_usd`/`required_approvers`/`approver_pool`; `force_single_approve` has zero hits anywhere in
      code — corrected the anti-pattern claim to state no bypass exists rather than implement one);
      `fork_url`/`live_rpc_url` (fix — `CHAIN_RPC_TEMPLATES` only carries `rpc_url_template`; fork RPC resolution is a
      separate `FORK_MODE` switch in `get_defi_rpc_url()` using one global `tenderly-fork-rpc-url` secret, not a
      per-chain field).
- [x] ✅ [DOCS] P3. Re-run the same per-symbol check over the other two freshness shards' docs (offsets 0 and 1) — this
      sweep only covered offset-2's 37 docs, so the same phantom-symbol class is very likely present in the other 76. —
      unified-trading-pm. Reconstructed the exact offset-0/offset-1 doc sets by replaying the sorted-path-index-mod-3
      split against the 113-doc pre-fix snapshot (verified byte-identical to the real `44aecd1dc`/`ff8b38f70` commit
      file lists). Extracted every backticked candidate-symbol token from all 76 docs (2152 raw tokens → 1165
      code-symbol-shaped after filtering paths/extensions/prose), then verified each of the 1067 unique root symbols
      **individually** via `rg -F` (not a bulk patternfile — the same prefix-shadowing trap flagged above), yielding 95
      zero-hit candidates. Triaged all 95 by reading each doc's actual context (not just the grep hit): - **Already
      fixed by shard offset-0's own commit** (`FixtureStatusReport`/`CrossSourceFixtureVerifier`, `DeFiFillRecord`,
      `KillSwitchAuditLogPersistenceError`, `MatchingEngineConfig`, `InstrumentProcessingConfig`, `_paper_positions`,
      `BreakerArmed`): all already carry "verified absent 2026-07-31" banners — no new action. - **False positives**
      (external protocol/vendor identifiers, illustrative examples, or plan-file slugs, not claimed repo symbols): the
      entire ~30-symbol `amm-slippage-simulation.md` cluster (Uniswap V4 hook ABI names, Aave/Compound governance
      contracts, Solana RPC methods, ETH slashing-condition enum values — all framed as external on-chain/subgraph
      references, and the doc already discloses NOT-YET-shipped pool classes via ❌/Phase markers); the ~9-symbol
      `sports-scheduling-and-sharding.md` cluster (all are plan-filename slugs with working markdown links to real
      archived plans, e.g. `utl_manifest_migration_primitives`); illustrative field-rename examples in
      `schema-versioning.md`; example client IDs in `client-isolation-sla-and-runtime-profiles.md`; external Ethereum
      JSON-RPC (`eth_sign`) and heuristic prose terms in `mev-protection.md`; `active-plan-inventory-tracker.md`'s
      `cal_left`/`estimate_calibrated_ai_days` (real generator fields, not phantom); already-disclosed future-work items
      in `backtest-groups.md`, `scenario-injection-architecture.md`, `live-strategy-config-hot-reload.md` (superseded by
      the fresher, more detailed `strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md` issue doc — not duplicated
      here), `fireblocks-integration-spec.md` (whole doc is an explicit "no code shipped yet" spec),
      `execution-policy.md` (already banner-corrected). - **Genuine fixes applied** (verified against the real code,
      corrected in place): `amm-slippage-simulation.md` — `hooks.py`'s real shipped interface is `IUniswapV4Hook` + 6
      named hook classes via `HookRegistry`, not a `BeforeSwapHook`/`AfterSwapHook` Protocol pair.
      `defi-phase3-infrastructure.md` — `TreasuryMonitor` moved 2026-05-20 to
      `strategy-service/strategy_service/position/core/treasury_monitor.py`; real thresholds are
      `TreasuryConfig.min_threshold_pct`/`max_threshold_pct` (percent-of-AUM per share class), not the fixed-ETH
      `min_treasury_balance_eth`/`min_trading_balance_eth`/`max_pending_withdrawal_pct` the doc claimed (all three
      absent from every repo). `slow-fast-routing-split.md` — the envelope class is `StrategyInstructionEnvelope`
      (`unified_api_contracts.internal.architecture_v2`), not the older `StrategyInstruction`; `eligible_venues` /
      `venue_constraints` / `venue_routing_mode` / `target_venue` all check out as real fields, but `fallback_venues`
      and `unity_child_books_eligible`/`unity_child_book_preferences` are absent from the workspace — corrected with
      NOT-SHIPPED banners rather than deleted, since the routing-mode design intent is real.
      `interface-credential-convention.md` — `ApiKeyReloader`'s real param is `refresh_interval`
      (`DEFAULT_REFRESH_INTERVAL` = 300s), not `reload_interval_seconds` (default 60s, also wrong).
      `live-pipeline-architecture.md` — the real symbol is `market_data_processing_service...live_aggregator`'s
      `parent_fanout(parent: str) -> int` method (counts themselves were correct), not a `parent_timeframe_fanout`
      field. - **Left as-is, low-confidence** (plausible external/infra names, not worth further digging at P3):
      `market_tick_asia` (illustrative BQ dataset name), `vault_account_id`/`sub_status`/`freezeVaultAccount`
      (Fireblocks' own vendor API field/method names, doc already marked no-code-shipped), `usdt_to_usdc_swap_cost`
      (descriptive, not a literal claimed field).

### Methodology trap worth keeping

A bulk `rg -o --no-filename -f /tmp/allsyms.txt` scan reported 38 "absent" symbols; individual `rg -F` re-verification
cut that to 19 real ones. Cause: with an alternation of patterns, `rg -o` emits the **leftmost/shortest** match, so a
symbol that is a strict prefix of another (`ClientOnboardingState` vs `ClientOnboardingStateMachine`) hides the longer
one, which then looks absent. Any future doc-vs-code symbol audit must verify per-symbol.

## B — `runtime-topology.yaml` SSOT path is stale in 4 docs outside this shard

Ground truth: the file is `unified-trading-pm/configs/runtime-topology.yaml` (`version: 7`, `owner: unified-trading-pm`,
`paired_code_ssot: unified-trading-pm/workspace-manifest.json`). `deployment-service/configs/` has **no**
`runtime-topology.yaml`; `deployment-service/scripts/sync/sync-configs.py` pulls it from PM.
`/codex/04-architecture/TOPOLOGY-DAG.md` was corrected in the freshness-c commit; these four were not:

- [x] ✅ [DOCS] P3. Repoint `deployment-service/configs/runtime-topology.yaml` →
      `unified-trading-pm/configs/runtime-topology.yaml` in `/codex/08-workflows/service-pair-flows.md`,
      `/codex/04-architecture/tier-and-import-architecture.md` (line ~317), `/codex/07-security/audit-logging.md`. —
      unified-trading-pm.
- [x] ✅ [DOCS] P3. Same repoint in `/codex/05-infrastructure/runtime-tiers-and-deployment.md` — **owned by freshness
      shard offset-1**; confirm that shard did not already fix it before editing, to avoid a duplicate/conflicting edit.
      — unified-trading-pm. Confirmed via grep that the stale path was still present (not yet fixed by shard offset-1)
      before editing; also corrected the doc's "(symlink from PM)" claim — verified there is no symlink, only the
      `sync-configs.py` sync script.
