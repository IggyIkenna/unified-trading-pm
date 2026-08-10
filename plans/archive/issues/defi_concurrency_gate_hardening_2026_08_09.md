---
doc_type: issue
title:
  "DeFi per-data-source concurrency gating audit — 4 handlers hand-rolled TheGraph key #1 (fixed); Alchemy has no
  cross-launcher cap (documented gap, not yet an incident)"
summary: >-
  Audited every DeFi VM-based data source (TheGraph 9-key subgraph pool, Alchemy single-key EVM+Solana RPC, Pyth
  Hermes/Pythnet per-IP REST — none use Tardis) against the `tardis-concurrency-guard.sh` pattern. Found and FIXED a
  real, live bug: `liquidation_events_handler.py` / `flash_loan_events_handler.py` / `position_data_handler.py` /
  `governance_events_handler.py` all called `load_thegraph_key_pool()` but only ever consumed `pool[0]` — the exact
  hand-rolled-single-key bug already fixed once in `dex_pools_handler`/`dex_swaps_handler`
  (`/codex/02-data/defi-canonical-naming-ssot.md` DURABLE gotcha #5) but never propagated to these 4 siblings, with ZERO
  retry-on-429 as a second-order effect. Fixed via a new shared `post_subgraph_query_with_rotation()` helper in
  `market_tick_data_service/cli/handlers/_lending_grain.py`. Separately: unlike Tardis (hard 1-VM fleet-wide cap,
  `tardis-concurrency-guard.sh`) and The Odds API (`odds-api-concurrency-guard.sh`), the single shared `alchemy-api-key`
  (~7 DeFi launchers: gas-fees/lst-rates/vault-share-price/solana-gas/jito-solana/marinade-solana/defi-forward-poll) has
  NO cross-launcher concurrency guard — only per-launcher/per-operation singleton locks that explicitly ALLOW different
  Alchemy-consuming launchers to run concurrently. This is a real structural gap but, unlike Tardis/Odds-API (both built
  reactively after a MEASURED incident), there is no recorded Alchemy 429/rate-limit incident in this corpus, and a
  historical ~47-VM concurrent DeFi fan-out (2026-06-21/23, `data_completion_defi_2026_07_15.md`) ran without one — so a
  speculative hard-cap guard is NOT built here (no empirical number to calibrate against, unlike Tardis's measured N=1).
  Live GCS-only DeFi VMs (canonical-migration rebuild, MDPS candle derivation x2, MDPS live features) currently running
  touch NEITHER TheGraph NOR Alchemy, so there is no live cap violation right now.
status: resolved
nature: issue
asset_group: [defi, meta]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [defi, concurrency, thegraph, alchemy, rate-limit, vm-launcher, data-correctness, P2]
created: 2026-08-09
author: unknown
priority: P2
parent_epic: infrastructure_master
source: >-
  Operator-directed audit session, 2026-08-09 — "per data source defi vms same logic, most already in there just check
  for deviants and harden scripts", modeled on the cefi-side `tardis-concurrency-guard.sh` audit running concurrently in
  a sibling session.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
supersedes:
superseded_by:
resolved_by: "market-tick-data-service@ee5751f1b"
context_scope:
  [
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    deployment-service/scripts/vm/tardis-concurrency-guard.sh,
    deployment-service/scripts/vm/odds-api-concurrency-guard.sh,
    market-tick-data-service/market_tick_data_service/cli/handlers/_lending_grain.py,
    market-tick-data-service/market_tick_data_service/market_interface/clients/thegraph_base_client.py,
  ]
related: []
---

> **🟢 ARCHIVED 2026-08-10** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule (`ACKED-INTO-CODE`). Resolution evidence carried in `resolved_by:`
> (market-tick-data-service@ee5751f1b). Never previously shipped — archived directly at first ship, no flip-then-mv
> bridge needed since no external tracker was watching this path.

## Task

Operator hypothesis: DeFi VM launchers likely already have per-data-source concurrency gating (possibly reusing
`tardis-concurrency-guard.sh`, since Tardis serves some DeFi data too), and the ask was to audit for gaps/deviants and
harden what exists — not build from scratch. This doc records what was found.

## 1. Does any DeFi data source use `tardis-concurrency-guard.sh`?

**No.** `tardis-concurrency-guard.sh`'s own header scopes it explicitly: "TARDIS_VM_NAME_PATTERN=
`'^(cefi|tradfi)-.*-(heavy|light)-|^cefi-queue-|^mtds-backfill-cefi-'`" and its `TARDIS_CAP_EXEMPT_VENUES` list is
CeFi/on-chain-perp venues only (HYPERLIQUID / ASTER / EXTENDED-STARKNET / COINBASE-CDE). Confirmed by code:
`grep -rln tardis market_tick_data_service/market_interface/adapters/defi/*.py` → zero hits. Every DeFi adapter
(`aave_lending.py`, `curve_adapter.py`, `uniswapv2/v3/v4_adapter.py`, `morpho_adapter.py`, `balancer_adapter.py`, the 5
`lst_*_adapter.py` files) is a subgraph/RPC/REST client, not a `datasets.tardis.dev` consumer. No `launch-*defi*` or
`launch-mtds-*` DeFi launcher sources `tardis-concurrency-guard.sh` or `odds-api-concurrency-guard.sh` — grepped every
`launch-{defi,mtds-dex,mtds-lending,mtds-liquidation,mtds-flash-loan,mtds-position,mtds-risk-params,mtds-lst-rates, mtds-vault-share-price,mtds-gas-fees,mtds-bridge-events,mtds-eigenlayer-rewards,mtds-solana-gas,jito-solana, marinade-solana,mtds-pyth-*}-*.sh`
for `guard.sh` sourcing — zero matches.

## 2. What DeFi data sources actually exist, and how is each one's concurrency risk mitigated?

| Source                                      | Consumers (launcher/handler)                                                                                                                                                                                                                                                                                      | Shared resource                                            | Existing mitigation                                                                                                                                                                                                                                                                                                  |
| ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **TheGraph** (subgraph gateway)             | `dex_pools_handler`, `dex_swaps_handler`, `lending_indices_handler`, `risk_params_handler`, `liquidations_handler`, `evm_defi_handler`, + the 4 fixed-this-session handlers below                                                                                                                                 | 9-key pool (`thegraph-api-key` + `-2..-9`, Secret Manager) | **Key-pool SHARDING + 429-aware rotation** (`thegraph_base_client.py::next_thegraph_key_from_pool` / `ThegraphKeyPoolRotator`) — a fundamentally different, adequate strategy vs. Tardis's single-IP hard cap (TheGraph has NO single-IP lock; sharding across 9 keys is the correct mitigation, not a VM-count cap) |
| **Alchemy** (EVM archival RPC + Solana RPC) | `launch-mtds-gas-fees-backfill-vm.sh` (8 chains), `launch-mtds-lst-rates-backfill-vm.sh`, `launch-mtds-vault-share-price-backfill-vm.sh`, `launch-mtds-solana-gas-backfill-vm.sh`, `launch-jito-solana-backfill-vm.sh`, `launch-marinade-solana-backfill-vm.sh`, `launch-defi-forward-poll.sh` (oracle-prices op) | **ONE** `alchemy-api-key` secret (no pool)                 | Per-launcher/per-operation singleton lock ONLY (self-duplicate refusal) — **no cross-launcher cap** (§3)                                                                                                                                                                                                             |
| **Pyth** (Hermes REST / Pythnet RPC pool)   | `launch-mtds-pyth-lst-backfill-vm.sh`, `launch-mtds-pyth-archive-backfill-vm.sh`                                                                                                                                                                                                                                  | Per-IP rate limit (100 req/min), not a shared credential   | Per-launcher singleton lock; per-IP means concurrent VMs on DIFFERENT external IPs don't actually contend the same way Tardis's single authenticated IP does — lower-risk by construction                                                                                                                            |

## 3. The real bug: 4 handlers hand-rolled TheGraph key #1, never rotated, never retried — FIXED

`/codex/02-data/defi-canonical-naming-ssot.md` DURABLE gotcha #5 already documents this exact bug class: "DeX subgraph
handlers MUST shard across the 9-key TheGraph pool... `dex_pools_handler`/`dex_swaps_handler` hand-rolled a SINGLE key
-> all DEX VMs collided on key #1" — fixed once. Auditing the SIBLING handlers the SSOT names as sharing the
`market_count_map` grain helper (`_lending_grain.py`: "the four lending/liquidation handlers (lending_indices /
liquidations / liquidation_events / flash_loan_events / position_data)") plus `governance_events_handler.py` found the
fix was NEVER propagated to 4 of them:

- `liquidation_events_handler.py::_fetch_liquidation_events` → `_fetch_aave_liquidations`/`_fetch_morpho_liquidations`
- `flash_loan_events_handler.py::_fetch_aave_flash_loans`
- `position_data_handler.py::_fetch_aave_positions`/`_fetch_uniswap_positions`
- `governance_events_handler.py::_fetch_governance_events`

Each `preflight()` called `load_thegraph_key_pool()` (loading all 9 keys) but then did
`self._graph_api_key = pool[0] if pool else None` and passed ONLY that fixed string down through a single-shot
`session.post()` with **no retry on 429/5xx at all**. Every VM running any of these 4 data_types therefore (a) always
hit key #1 — colliding with every OTHER pool[0]-only caller AND with the FIRST key in every properly-rotating caller's
round-robin — and (b) hard-failed the whole shard (`record_failed`) on the first transient rate-limit instead of backing
off, unlike the correctly-wired siblings (`lending_indices_handler`/`risk_params_handler`/
`liquidations_handler`/`dex_pools_handler`/`dex_swaps_handler`/`evm_defi_handler`, all confirmed via
`next_thegraph_key_from_pool` usage in their request path, not just the `preflight()` pool[0] compat assignment).

**Fix**: added `post_subgraph_query_with_rotation(session, api_key_pool, subgraph_id, query)` to
`market_tick_data_service/cli/handlers/_lending_grain.py` — rotates one key per call via `next_thegraph_key_from_pool`
and retries that key up to 3x with exponential backoff on 429/500/502/503/504 (mirrors the proven pattern in
`lending_indices_subgraph.py::_execute_subgraph_query`). All 4 handlers' `__init__`/ `preflight()`/fetch functions now
thread `_api_key_pool: list[str]` through instead of a single fixed string; `_graph_api_key` is kept only as a
presence-check/logging convenience. Updated call sites + every affected unit test
(`tests/unit/test_{flash_loan_events,position_data,liquidation_events,governance_events}_handler.py`,
`tests/market_interface/unit/test_defi_handlers.py`) from single-string to list-of-keys signatures.

Files changed (market-tick-data-service): `market_tick_data_service/cli/handlers/_lending_grain.py`,
`flash_loan_events_handler.py`, `position_data_handler.py`, `liquidation_events_handler.py`,
`governance_events_handler.py`, + the 5 test files above.

## 4. Alchemy: real structural gap, deliberately NOT built out this session

Multiple Alchemy-consuming launcher headers already document AWARENESS of shared-CU-budget contention in prose
(`launch-mtds-gas-fees-backfill-vm.sh` "ALCHEMY SHARED-CU CAVEAT", `launch-mtds-lst-rates-backfill-vm.sh` "Alchemy
compute-units are shared per-key", `launch-jito-solana-backfill-vm.sh`/`launch-marinade-solana-backfill-vm.sh` "prevent
Alchemy compute-unit budget burn", `launch-defi-forward-poll.sh` "Alchemy + The Graph share per-key compute-unit
budgets") — but every one of them enforces this ONLY via a per-launcher-name or per-operation singleton lock (refuses a
duplicate of ITSELF), never a cross-launcher cap on the total Alchemy-consuming fleet. `defi-fwd-*`'s own Cloud
Scheduler (`terraform/gcp/defi_forward_poll_scheduler.tf`) explicitly staggers its 3 price-sensitive ops by 1-2 min
"keys off the shared TheGraph/Alchemy quota" — a real mitigation, but scoped to the 3 scheduled live-poll ops only, not
to the ~6 manually/AO-launched Alchemy backfill launchers, which can all be launched concurrently with zero gate.

This mirrors the shape of the Tardis/Odds-API bugs (documented risk, no enforcement) but is **NOT** built out into a new
`alchemy-concurrency-guard.sh` here, for a load-bearing reason: both existing guards were built REACTIVELY from a
MEASURED incident with real numbers to calibrate against (Tardis: N=1 vs N=3 vs N=6 403-storm data; Odds-API: the
5,000,000-credit exhaustion). No Alchemy 429/rate-limit incident exists in `plans/`/`codex/` (grepped
`alchemy.*(rate|429|compute unit)` — zero hits), and a historical ~47-concurrent-VM DeFi fan-out
(`data_completion_defi_2026_07_15.md`, 2026-06-21/23, ~6-7 of those 47 VMs would have been Alchemy-consuming) ran to
completion without a reported Alchemy throttle incident — the OOM/manifest-write issues that DID occur there were
unrelated (memory + manifest-shard-key bugs). Building a speculative hard cap with an invented number risks the exact
overcorrection Tardis's own history warns about (an under-calibrated cap starves legitimate parallel work; an
over-generous one does nothing). **Recommendation, not built**: if/when a 429 from Alchemy is observed in a DeFi
launcher's `run.log`, build `alchemy-concurrency-guard.sh` mirroring `odds-api-concurrency-guard.sh`'s shape
(FAIL-CLOSED fleet enumeration + explicit override var) with a cap calibrated from that measurement.

## 5. Live state check (2026-08-09, ~17:15 PT)

`gcloud compute instances list --filter="name~defi" --project=central-element-323112`:

| VM                                                 | Started    | What it does                                                            | Touches TheGraph/Alchemy/Pyth?               |
| -------------------------------------------------- | ---------- | ----------------------------------------------------------------------- | -------------------------------------------- |
| `canonical-migration-defi-rebuild-20260809-163511` | 2026-08-09 | `rebuild_defi_manifest.py`, `VM_START_DATE=2024-09-06`                  | No — GCS manifest rewrite only               |
| `mdps-defi-2025-20260807-203541`                   | 2026-08-07 | MDPS candle derivation, `--start-date 2025-01-01 --end-date 2025-12-31` | No — reads raw ticks from GCS, no vendor API |
| `mdps-defi-2026-20260807-203541`                   | 2026-08-07 | MDPS candle derivation, 2026 shard                                      | No                                           |
| `mdps-features-live-defi-20260807-032721`          | 2026-08-06 | Live features computation                                               | No                                           |

`canonical-migration-defi-rebuild-20260809-163511` is **verified NOT a duplicate** of the known-tracked
`canonical-migration-defi-rebuild-20260806-223130` (`defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md`,
explicitly out of scope for this audit): its metadata shows `VM_START_DATE=2024-09-06`, consistent with a legitimate
resume from the earlier VM's last measured checkpoint (that issue doc recorded `date=2023-01-30` as of 2026-08-07,
climbing) — matches the workspace's "preemption recovery resumes from measured PROGRESS, never replays START_DATE" rule,
not a second concurrent rebuild.

**No live cap violation of any kind right now** — none of the 4 running DeFi VMs call TheGraph, Alchemy, or Pyth.

## 6. Plans/issues scan for in-flight risk

Grepped `plans/active/` + `plans/active/issues/` for any currently-active plan proposing a NEW mass-concurrent DeFi VM
launch. The only historical precedent (~47 concurrent DeFi VMs, `data_completion_defi_2026_07_15.md`) is long closed out
(2026-06-21/23). No active plan currently proposes re-running that shape or a new large-scale DeFi VM fan-out.

## Resolution

- [x] Real bug (4 handlers, hand-rolled TheGraph key #1, no retry) — **FIXED**, market-tick-data-service, this session
      (Evidence: `market-tick-data-service@ee5751f1b`).
- [x] Alchemy cross-launcher gap — **documented, deliberately not built** (§4); no measured incident to calibrate a cap
      against. Re-open / fold into a proper plan if a 429 is ever observed.
- [x] Live-state + plans scan — no current violation, no in-flight risk found.
