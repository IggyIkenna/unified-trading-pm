---
doc_type: issue
title:
  "DeFi adapter dead-code / runtime-fallback / duplicate-implementation audit — jupiter.py orphan, MTDS
  adapters/defi/{live,defi_live}/ entirely unreached (incl. the governance-params-refresh Phase 1 poller), Helius
  duplicate, execution-service dead execute_swap/lend/stake removed"
summary: >-
  Per-module audit of the three named DeFi adapter surfaces (instruments-service reference-data adapters, MTDS
  market-interface adapters, execution-service's defi_adapter.py) against
  `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md`. Methodology: cross-referenced every adapter class
  against its service's live dispatch table (IS `reference_data/factory.py::_ADAPTERS`, MTDS
  `market_interface/factory.py::VENUE_REGISTRY`), grepped every remaining file's class name for real non-test, non-self
  callers repo-wide, and swept every file for broad-except runtime-fallback patterns. Findings: IS
  `adapters/defi/jupiter.py::JupiterReferenceDataAdapter` is fully built + tested but registered nowhere (FLAGGED). MTDS
  `adapters/defi/live/` (3 files) and `adapters/defi_live/` (2 files) are fully built, exported, tested, and completely
  unreached by the real live-connector registry (`live/connectors/`) — most significantly,
  `governance_params_event_poller.py` is the plan-marked-complete Phase 1 of the cross-repo
  governance-parameters-refresh feature, never actually instantiated in production, which means Phase 2's
  `governance_params` parquet is never populated and Phase 3/4 (features-service APR calc, strategy-service sizing)
  silently run on hardcoded fallback constants forever (FLAGGED, big finding, cross-repo). MTDS
  `onchain/helius_solana.py::HeliusSolanaAdapter` sits unused while `native_staking_handler.py` hand-rolls the same
  Helius RPC calls itself — undocumented duplicate (FLAGGED). `onchain/__init__.py`'s docstring is stale (documented,
  not shipped — see § 6). execution-service `adapters/defi_adapter.py` had three dead public methods
  (`execute_swap`/`execute_lend`/`execute_stake`) duplicating the live `execute_instruction()` path without its
  retry/classify/Tenderly-simulation safety machinery — REMOVED and shipped this session. All other modules across both
  services (IS: 50/51 files; MTDS: all `onchain_perps/` + all registered `defi/` protocol adapters) are KEPT — correctly
  registered, reachable, and free of silent fallback masking.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, market-tick-data-service, execution-service, unified-trading-pm]
scope: [engineer]
tags:
  [
    dead-code,
    fallback,
    duplicate-adapter,
    adapters,
    defi,
    quality-gates,
    live-connectors,
    governance-params,
    operator-notify,
  ]
related:
  [
    defi_consolidated_closeout_2026_07_18,
    defi_governance_params_refresh_2026_06_20,
    wsfeedconnector_phase35_gap_2026_07_06,
  ]
created: "2026-07-24"
priority: P1
parent_epic: infrastructure_master
source:
  "Dispatched todo from plans/active/defi_consolidated_closeout_2026_07_18.md (gate-audit §1, 2026-07-24): 'Audit defi
  adapters for dead code, runtime-fallback masking, and duplicate implementations' across instruments-service
  .../adapters/defi/, MTDS market_interface/adapters/{defi,defi_live,onchain,onchain_perps}/, and execution-service
  adapters/defi_adapter.py, per /codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md."
execution_scope: local-only
drift_direction: advance-docs
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
resolved_by:
last_reviewed:
---

# DeFi adapter dead-code / runtime-fallback / duplicate-implementation audit (2026-07-24)

> **🔴 OPERATOR-NOTIFY — cross-repo / data-correctness-adjacent class (§ 3).** The governance-parameters-refresh
> feature's plan (`plans/archive/2026_06/defi_governance_params_refresh_2026_06_20.md`, `status: complete`) marks Phase
> 1 "✅ DONE" on the strength of a class existing and its own unit tests passing. Measured in this session: that class
> (`GovernanceParamsEventPoller`) has **zero production callers** — nothing ever instantiates it, so the Phase 2 parquet
> it's supposed to feed is never written, and Phase 3/4's documented "graceful fallback" to hardcoded
> LTV/liquidation-threshold constants is not a fallback for an edge case — it is the **only thing that has ever run** in
> production. This is not re-verified against features-service/strategy-service in this session (out of this audit's
> repo scope); it is reported here as measured MTDS-side evidence that the claim needs re-checking.

## 0. Rule applied + methodology

Per `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md`, three questions per module:

1. **Dead code** — registered somewhere (factory/dispatch table) but never reached by a live code path.
2. **Runtime fallback masking** — an adapter-level error silently caught and replaced with degraded/stale/legacy
   behavior instead of surfacing loudly.
3. **Duplicate implementation** — two files implementing the same venue/chain with no stated reason for both.

**Methodology used** (stated honestly — this is a reachability + pattern audit, not a full line-by-line business-logic
review of all ~100 files):

- For every adapter class in each of the three named directories, grepped the owning service's live dispatch table (IS:
  `instruments_service/reference_data/factory.py::_ADAPTERS`, reached via `get_adapter_for_canonical_venue()` /
  `create_reference_data_adapter()`, consumed by `engine/urdi_reference_provider.py`; MTDS:
  `market_tick_data_service/market_interface/factory.py::VENUE_REGISTRY` + its documented `PLANNED_VENUES` carve-out) to
  establish registration + reachability status for every file.
- For files not in the live registry, grepped the class name (not just the filename — filename greps produced two false
  positives during this audit, see § 2.2) repo-wide for any real caller (CLI handler, script, live-connector
  registration) outside its own module/tests.
- Swept every file in scope for broad `except Exception` / bare `except:` patterns and read each in context to classify
  as (a) legitimate per-instrument/per-record shard-isolation (log + continue, matches
  `/codex/04-architecture/shard-level-failure-isolation.md`), (b) a named + logged intentional degrade, or (c) a silent
  mask.
- Cross-checked every registry entry for a class mapped to two files (duplicate registration) and, separately, grepped
  for known-duplicate-pattern candidates (multiple files implementing calls to the same external API).

## 1. instruments-service — `instruments_service/reference_data/adapters/defi/` (51 files)

**Registry**: `reference_data/factory.py::_ADAPTERS` (the live path — reached via `get_adapter_for_canonical_venue()` /
`create_reference_data_adapter()`, called from `engine/urdi_reference_provider.py`). A second resolver exists,
`reference_data/router.py::create_reference_data_adapter_for_source()`, re-exported from `reference_data/__init__.py` as
`get_reference_adapter_for_source` — grepping its only callers repo-wide surfaces **only its own tests**
(`tests/unit/test_router.py`, `tests/unit/test_factory_comprehensive.py`) and the package re-export itself; nothing in
`instruments_service/` or `scripts/` calls it. `router.py` imports the exact same `adapters/defi/*` set as `factory.py`
(verified: `comm` diff of both files' `adapters.defi.*` import lists is empty in both directions), so this doesn't
orphan any additional file beyond the one below — but it is itself a second, apparently-unreached implementation of
"resolve a venue+source to an adapter," which is why jupiter.py's story is ambiguous (it's registered in neither).

- **FLAGGED — `jupiter.py::JupiterReferenceDataAdapter`** (Jupiter DEX aggregator token-pair discovery, Solana). Fully
  implemented (real API calls, canonical `instrument_key` construction, `classify_venue_error` usage) and fully
  unit-tested (`tests/unit/reference_data/adapters/defi/test_jupiter_metadata.py`, 165 lines +
  `tests/unit/test_defi_adapters_boost.py`). NOT imported by `factory.py` (confirmed: it is the **only** file in the
  directory absent from `factory.py`'s `adapters.defi.*` import list), NOT in `_ADAPTERS`, NOT imported by `router.py`,
  no dynamic/`importlib` lookup exists in either resolver. Zero production callers. This is dead code per rule #1 — and
  a stricter case than the rule's own worked example, since it isn't even referenced in a factory/dispatch table, just
  orphaned. **Not fixed in this pass**: registering a new live DeFi venue (Jupiter) has downstream effects (UAC venue
  lists / `VENUE_TO_ADAPTER_KEY`, manifest schema, backfill scope, billing) that are a product decision, not a safe
  unilateral code fix. Follow-up choice is binary: (a) add `"jupiter": JupiterReferenceDataAdapter` to `_ADAPTERS` and
  take on Jupiter as a live-routed venue, or (b) delete the class + its tests as abandoned scaffolding. Either is a
  real, scoped follow-up todo.
- **KEPT — all other 50 files.** Every other `adapters/defi/*.py` module maps 1:1 to a `factory.py::_ADAPTERS` key
  (verified via full import-list diff, not sampling). No duplicate registration found (no `factory.py` value/class is
  mapped under two different keys). `_dex_factory_registry.py` (factory-contract-address → DEX-version registry) carries
  its own `# Epic:` / `# Lifecycle: permanent` / `# Delete-when: NA` markers per
  `/codex/06-coding-standards/script-homes.md` and is deliberately consumed by exactly one caller
  (`scripts/canonicalize_defi_manifest_venue_2026_06_14.py`) — that's its designed usage, not orphaning.
  `_solana_utils.py` is actively imported by 10 sibling adapters + `engine/orchestrator/__init__.py`.
- **Exception-pattern sweep**: narrow per-field parse guards (`curve.py:70`, `balancer.py:89,110`, `uniswap_v2.py:66`,
  `uniswap_v4.py:66,78`, `uniswap_v3.py:658,670`, `meteora.py:186`, `lifinity.py:189`, `phoenix.py:198,206` — all
  `except (TypeError, ValueError): return None` on a single decoded value) and one per-record skip-and-log inside a
  pool-listing loop (`curve.py:224`, `except Exception as exc: logger.warning(...)`, continues to the next pool) are
  legitimate record-level isolation, not adapter-level failure masking. No instance found of an adapter catching a real
  upstream/venue error and silently substituting degraded data for the whole request.

## 2. market-tick-data-service — `market_interface/adapters/{defi,defi_live,onchain,onchain_perps}/`

**Registry**: `market_interface/factory.py::VENUE_REGISTRY` (get_adapter() dispatch) + `PLANNED_VENUES` (documented,
intentionally-not-yet-wired — the codex rule's own carve-out: "document why it's intentionally kept... with a stated
activation path"). Separately, the workspace's actual **live-streaming** registration mechanism is
`market_tick_data_service/live/connectors/` (`register_all()` → `WS_FEED_CONNECTOR_FACTORIES`, the "Phase 3.5" per-venue
WSFeedConnector rollout, plan `plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md` Phase 3.5) — distinct from
`market_interface/factory.py`'s batch/direct `get_adapter()`.

### 2.1 `onchain_perps/` (3 files) — KEPT, clean

`AsterAdapter` and `HyperliquidAdapter` are both in `VENUE_REGISTRY` (`"aster"`, `"hyperliquid"` →
`("onchain_perps", ...)`); `base_onchain_perp_adapter.py::BaseOnchainPerpAdapter` is their shared base class, imported
by both plus `factory.py`. No duplication, no dead code.

### 2.2 `defi/` (44 files incl. `live/` subpackage) — mostly KEPT, one big FLAGGED, one FLAGGED

All protocol adapters that map to a `VENUE_REGISTRY` key are **KEPT**: `aave_adapter.py`, `balancer_adapter.py`,
`curve_adapter.py`, `defillama_adapter.py`, `ethena_adapter.py`, `fluid_adapter.py`, `instadapp_adapter.py`,
`morpho_adapter.py`, `uniswap_v3_adapter.py` / `uniswapv2_adapter.py` / `uniswapv4_adapter.py`,
`restaking_jito_adapter.py` / `restaking_karak_adapter.py` / `restaking_symbiotic_adapter.py`, `vault_beefy_adapter.py`
/ `vault_convex_adapter.py` / `vault_idle_adapter.py` / `vault_pendle_adapter.py` / `vault_yearn_adapter.py`, and the
`lst_*_adapter.py` set (`lst_etherfi_adapter.py`, `lst_kelpdao_adapter.py`, `lst_lido_adapter.py`,
`lst_puffer_adapter.py`, `lst_renzo_adapter.py`, `lst_rocket_pool_adapter.py`, `lst_solblaze_adapter.py` — note these
files hold the actual `EtherFiAdapter`/`LidoAdapter`/etc. classes that `factory.py` imports; there is no
separately-named `etherfi_adapter.py`). Shared utilities are all genuinely consumed:
`aave_lending.py`/`aave_positions.py`/`aave_utils.py` (mixins used by `aave_adapter.py` + `ethena_adapter.py`

- a CLI handler), `block_utils.py`, `canonical_write.py` (used by `scripts/migrate_defi_batch_to_per_instrument.py` +
  `cli/handlers/dex_pools_handler.py`), `fluid_liquidity_resolver.py`, `governance_adapter.py` +
  `snapshot_space_monitor.py` (consumed by `cli/handlers/governance_proposals_handler.py` /
  `snapshot_governance_handler.py`), `protocol_outage_adapter.py` (consumed by
  `cli/handlers/protocol_outage_detector_handler.py`), `lst_adapters.py` (documented re-export shim, not dead),
  `_async_utils.py` / `_defi_graph_models.py` / `_lst_utils.py` / `_pool_key.py` / `utils.py` (all with real consumers,
  confirmed individually).

* **FLAGGED — `defi/live/` sub-package (3 files), significant, cross-repo.** `hyperliquid_ws.py::HyperliquidWSFeed`,
  `onchain_event_poller.py::OnChainEventPoller`, and `governance_params_event_poller.py::GovernanceParamsEventPoller`
  are each fully implemented and covered by `tests/market_interface/unit/test_defi_live_feeds.py`, but **none has a
  production caller**. `HyperliquidWSFeed` and `OnChainEventPoller` are exported via `live/__init__.py.__all__`
  (satisfying rule #1's "referenced somewhere" but not "reached"); `GovernanceParamsEventPoller` isn't even exported
  there. A filename-only grep for "hyperliquid_ws" is actively misleading here: it also matches an unrelated,
  genuinely-live class of the same theme, `HyperliquidWSFeedConnector`, in a **different** file
  (`market_tick_data_service/live/connectors/hyperliquid_ws.py`) that IS registered via `live/connectors/register_all()`
  — two same-named-in-spirit but structurally distinct implementations of "stream Hyperliquid over WS," one dead, one
  live, which is itself a duplicate-implementation instance (rule #3) if anyone maintaining this later assumes
  "hyperliquid_ws.py" is one file.
  - **The `GovernanceParamsEventPoller` case is the headline finding.** It is the shipped artifact for
    `plans/archive/2026_06/defi_governance_params_refresh_2026_06_20.md` Phase 1 (checkbox marked ✅ complete, citing
    `market-tick-data-service@fc3df1c`). Measured in this session: `GovernanceParamsEventPoller` has no caller anywhere
    in the repo outside its own file and tests; `GOVERNANCE_PARAMS_CHANGED` is only ever mentioned inside the class's
    own docstring `Usage:` example (`async for change in poller.stream(): emit_lifecycle_event(...)`), never as an
    actual call; `cli/main.py`'s only "governance_params" hit is a comment
    (`# defi_governance_params_refresh Phase 5 — Snapshot space monitor`) pointing at the _unrelated_
    `snapshot_space_monitor.py` governance-proposals tracker, not this poller. Per the Phase 2 plan text,
    `read_governance_params_asof()` "returns `{}` on missing/unreadable parquet (graceful pre-Phase-1 fallback)" — since
    Phase 1 never runs, that parquet is never populated, so Phase 3 (features-service `aave_risk_calculator.py`) and
    Phase 4 (strategy-service sizing) — both documented as catching this and falling back to hardcoded constants — have
    been running on the fallback path unconditionally since the plan was marked complete. This is dead code (rule #1)
    whose downstream consequence is exactly rule #2's runtime-fallback-masking pattern, three repos removed from the
    dead module itself. **Not re-verified against features-service/strategy-service in this session** (outside this
    audit's three named directories) — flagged per the workspace's "big finding" rule (data-correctness-adjacent,
    cross-repo, a plan's own completion claim contradicted by measured reachability). Fixing it is real engineering
    (wire the poller into a live entrypoint or the `live/connectors/` registry, or re-scope Phases 3/4's fallback), not
    a same-pass fix.
* **FLAGGED — `defi_live/` sub-package (2 files), same shape, no successor exists.**
  `alchemy_adapter.py::AlchemyLiveAdapter` and `thegraph_ws_adapter.py::TheGraphWsAdapter` are exported via
  `market_interface/__init__.py`'s public surface but have zero downstream consumers (no CLI handler, no
  `live/connectors/` registration). Unlike `hyperliquid_ws.py` above, there is **no** Alchemy- or TheGraph-named
  connector anywhere in `live/connectors/` either — this pair isn't superseded by a newer implementation, it was simply
  never wired into either generation of the live-adapter pattern. Lower urgency than the governance poller (no plan
  claims it shipped a risk-relevant feature), but the same disposition choice applies: wire it in, or delete it.
* **FLAGGED — duplicate implementation, `onchain/helius_solana.py::HeliusSolanaAdapter` vs.
  `cli/handlers/native_staking_handler.py`.** `HeliusSolanaAdapter` is a real, documented, tested adapter exposing
  `native_staking_rates` / `token_balances` / `epoch_info` via the Helius enhanced Solana RPC — with zero callers
  anywhere in the repo. `native_staking_handler.py` (the actual live producer of Solana native-staking data)
  independently hand-rolls the identical capability from scratch: its own `_get_helius_api_key()` /
  `_get_solana_rpc_url()` / `_fetch_live_rates()` / `_fetch_vote_accounts()` / `_fetch_jito_mev_apy()`, raw `aiohttp`
  calls to `https://mainnet.helius-rpc.com/?api-key=...`, with no import of `HeliusSolanaAdapter` at all. No file states
  which is authoritative or why both exist — per rule #3, that silence is itself the violation. (This is distinct from
  the `defi/live/` case above: `HeliusSolanaAdapter` isn't unreachable-because-unwired, it's unreachable because a
  completely separate implementation does its job. `native_staking_handler.py`'s own graceful degrade — falling back to
  `_schedule_rate()` when the live RPC call fails, logged as `"RPC unavailable — using schedule rate for epoch %d"` — is
  a properly-named, logged, intentional fallback and is NOT itself a violation.) Follow-up (not made here): decide
  whether to consolidate `native_staking_handler.py` onto `HeliusSolanaAdapter`, or delete the adapter as superseded.
* **FLAGGED, minor, documented but NOT shipped — `onchain/__init__.py` stale docstring.** The module docstring reads:
  _"On-chain data adapters (placeholder). All adapters previously here (Glassnode, MEV) were blacklisted dead stubs and
  deleted during the UMI → MTDS merge (2026-04-11)."_ That was true in 2026-04 but is now stale: `glassnode.py` (added
  2026-05-21) and `helius_solana.py` (added 2026-05-20) were both re-added since, with real implementations. Neither is
  dead-by-accident, though — `glassnode.py::GlassnodeAdapter` is explicitly listed in
  `factory.py::PLANNED_VENUES["glassnode"] = "analytics"` with a stated activation path, and
  `helius_solana.py::HeliusSolanaAdapter` carries an explicit `BLOCKED-CREDENTIALS` docstring pending operator paid-tier
  approval (`ikenna_orchestrator/pings/slot_8.md`) — both satisfy rule #1's "document why it's intentionally kept"
  carve-out on their own terms, so this is a **documentation accuracy issue, not a dead-code violation**. I drafted and
  verified a corrected docstring in this session but did **not** ship it: at audit time the MTDS checkout had live,
  actively-mtimed (<10 min old) uncommitted foreign work in two unrelated CLI handler files (`lst_rates_handler.py`,
  `staking_yields_handler.py`) plus a staged new script, from what is evidently a concurrent agent session in the same
  shared per-slot worktree (a second `quality-gates.sh` process for this repo was observed running mid-audit, started by
  a process this session did not launch). Per the multi-agent safety rules, I chose not to run a full-tree
  `quality-gates.sh` against a checkout with another session's genuinely in-flight WIP, and reverted my own edit rather
  than leave a second uncommitted change sitting in a shared tree. This is a trivial, zero-risk follow-up for whoever
  next touches that file — corrected text is quoted in full below for direct reuse:

  ```
  """On-chain data adapters.

  The original Glassnode/MEV stubs referenced below were deleted during the UMI → MTDS
  merge (2026-04-11); this docstring is corrected 2026-07-24 because both were since
  re-added and this note had gone stale:

  - ``GlassnodeAdapter`` (glassnode.py, added 2026-05-21) — real implementation, listed
    in ``market_interface/factory.py::PLANNED_VENUES`` ("glassnode": "analytics") as an
    intentionally-not-yet-wired venue; promoting it requires adding it to
    ``VENUE_REGISTRY`` and dispatch in ``get_adapter()``.
  - ``HeliusSolanaAdapter`` (helius_solana.py, added 2026-05-20) — real implementation,
    gated ``BLOCKED-CREDENTIALS`` per its own module docstring (paid Helius RPC tier
    pending operator approval); also not yet in ``VENUE_REGISTRY``.

  Neither class is exported from this package's ``__all__`` or reachable via
  ``get_adapter()`` today — both are intentionally-parked, not accidentally-orphaned
  (tracked: ``plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md``).
  """
  ```

### 2.3 Lower-confidence, not separately traced

`defi/curve_adapter.py::_download_liquidity` (~line 682) catches broad `Exception`, logs, and `return []` on failure —
the same return shape as "this pool genuinely has zero liquidity snapshots today." I did not trace whether the outer
`base_defi_adapter.py` per-instrument loop's `if not result: continue` distinguishes this from a real per-shard failure
(i.e., whether an RPC outage here silently reads as "no data" instead of incrementing the loop's `failed` counter).
Noting this as an unconfirmed lead rather than a proven violation — it may already be covered by the same
shard-isolation convention that makes the rest of the file's broad-except usage legitimate.

## 3. execution-service — `execution_service/adapters/defi_adapter.py`

- **FIXED, SHIPPED THIS SESSION.** `DeFiAdapter.execute_swap()` / `.execute_lend()` / `.execute_stake()` (public
  methods, previously lines 368-397) were dead: the file also implements a completely parallel, hardened path —
  `execute_instruction()` → `_parse_defi_instruction()` → `_execute_with_retries()` → `_dispatch_defi_operation()` →
  `_execute_swap`/`_execute_lending`/`_execute_staking` — which is the **only** path any production caller uses
  (`cli/handlers/live_execution_handler.py:659`, the sole constructor+caller site, calls `execute_instruction()`
  exclusively). The three deleted methods called the identical underlying connectors
  (`UniswapConnector.swap_exact_input` / `AAVEConnector.supply`+`.borrow` / `LidoConnector.stake`) but with **none** of
  `execute_instruction()`'s retry/backoff, `classify_venue_error`-based error classification, or Tenderly pre-simulation
  — i.e. if anything had ever called them, it would have silently bypassed every safety mechanism the rest of the class
  exists to provide. Confirmed zero callers repo-wide (only match: the three `tests/unit/test_defi_adapter.py` tests
  literally named `test_execute_swap`/`test_execute_lend`/`test_execute_stake` — each already calls
  `execute_instruction()`, not the deleted method, per their own docstrings ("Test swap execution via
  execute_instruction") — so **no test changes were required**). Also removed the two now-unused imports
  `DeFiSwapResult as SwapResult` / `DeFiTxResult as TxResult` (used only as return-type annotations on the deleted
  methods). This is dead code (rule #1) with a duplicate-implementation flavor (rule #3): two parallel code paths for
  the same three operations, one live+hardened, one dead+unsafe, with nothing stating which is authoritative — small and
  unambiguous enough to fix directly rather than flag. **Evidence**: `execution-service@<sha>` (see commit list below);
  full `quality-gates.sh` green (7883 passed / 21 skipped / 1 pre-existing documented xdist flake unrelated to this file
  — see next paragraph).
  - **QG note**: the first full run hit 2 failures in
    `tests/unit/sports_execution/adapters/unity/test_mock_feed_connector_e2e.py::TestSidecarLifecycleAgainstMock`
    (sports/Unity mock feed connector sidecar lifecycle — unrelated to DeFi). A sibling test in the same file already
    carries an inline comment documenting this exact class of failure ("Pre-existing flake under pytest-xdist parallel
    execution: passes in isolation, fails when run alongside the rest of the suite... not a regression"). Verified:
    running that test file alone (no xdist) passes cleanly (9 passed, 1 xpassed). Not a regression from this change.
- **KEPT — the rest of the file.** `_simulate_transaction()`'s Tenderly-unavailable path
  (`except httpx.HTTPError: logger.warning(...); return True # proceeding without simulation`) is a named, logged,
  intentional degrade — Tenderly is a pre-execution safety check, not the execution itself, and its unavailability is
  explicitly surfaced in the log line, matching rule #2's "genuine, intentional fallback... named as such and logged"
  carve-out, not a silent mask. `_execute_with_retries()` re-raises `ValueError` immediately, raises unconditionally on
  `ErrorAction.FAIL` (from `classify_venue_error`), and only retries genuinely classified-retryable errors with
  exponential backoff — correct fail-loud behavior, no masking found.

## 4. Summary table

| module / file                                                                         | disposition        | reason                                                                                                  |
| ------------------------------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------- |
| IS `adapters/defi/jupiter.py`                                                         | FLAGGED            | fully built + tested, registered nowhere; needs a wire-in-or-delete decision                            |
| IS `adapters/defi/` (other 50 files)                                                  | KEPT               | all registered in `factory.py::_ADAPTERS`, reachable, no duplication                                    |
| IS `reference_data/router.py` (context, not a `defi/` file)                           | noted              | second resolver, apparently unreached outside its own tests                                             |
| MTDS `onchain_perps/` (3 files)                                                       | KEPT               | both concrete adapters in `VENUE_REGISTRY`                                                              |
| MTDS `adapters/defi/` registered protocol adapters + shared utils                     | KEPT               | all in `VENUE_REGISTRY` or confirmed real consumers                                                     |
| MTDS `adapters/defi/live/` (`hyperliquid_ws.py`, `onchain_event_poller.py`)           | FLAGGED            | exported, tested, zero production callers                                                               |
| MTDS `adapters/defi/live/governance_params_event_poller.py`                           | FLAGGED — big      | plan-marked-complete Phase 1, never actually runs; masks a live-trading fallback three repos downstream |
| MTDS `adapters/defi_live/` (both files)                                               | FLAGGED            | exported, tested, zero callers, no successor exists either                                              |
| MTDS `onchain/glassnode.py`, `onchain/helius_solana.py`                               | KEPT               | both intentionally-parked with a stated reason (`PLANNED_VENUES` / `BLOCKED-CREDENTIALS`)               |
| MTDS `onchain/helius_solana.py` vs `native_staking_handler.py`                        | FLAGGED            | undocumented duplicate implementation of the same Helius RPC capability                                 |
| MTDS `onchain/__init__.py` docstring                                                  | FLAGGED, minor     | stale text; corrected version drafted, not shipped (shared-checkout risk)                               |
| MTDS `adapters/defi/curve_adapter.py::_download_liquidity`                            | noted, unconfirmed | broad except → `[]`; not traced against the outer loop's failure accounting                             |
| execution-service `adapters/defi_adapter.py::execute_swap/execute_lend/execute_stake` | REMOVED, shipped   | zero callers, bypassed all of `execute_instruction()`'s safety machinery                                |
| execution-service `adapters/defi_adapter.py` (rest of file)                           | KEPT               | fail-loud retry/classify path; Tenderly fallback is named + logged                                      |

## 5. Scope not covered

This audit stayed inside the three directories named in the dispatching todo. It does **not** re-verify
features-service's `aave_risk_calculator.py` / `lending_features.py` or strategy-service's sizing logic referenced in §
2.2's governance-params finding — that would require its own pass in those repos. It also does not cover
`execution_service/defi_execution/` (the UDEI connector package `defi_adapter.py` delegates to) or
`execution_service/trade_execution/adapters/` beyond the single named file, per the dispatching todo's explicit scope.

## 6. Follow-up todos (not made in this pass — each is a real, scoped decision)

- [ ] [SERVICE] P2. instruments-service: decide `jupiter.py::JupiterReferenceDataAdapter`'s fate — register as a live
      DeFi venue (`factory.py::_ADAPTERS["jupiter"]`) or delete the class + its two test files.
- [ ] [SERVICE] P1. market-tick-data-service: re-verify the governance-parameters-refresh feature end-to-end
      (features-service `aave_risk_calculator.py` asof reads, strategy-service sizing) against the measured fact that
      `GovernanceParamsEventPoller` never runs in production; either wire the poller into a real entrypoint (a
      `live/connectors/`-style registration, or a scheduled batch job) or update the plan/codex record to state plainly
      that this feature has never been live.
- [ ] [SERVICE] P2. market-tick-data-service: decide disposition for `adapters/defi/live/onchain_event_poller.py`,
      `adapters/defi_live/{alchemy_adapter.py,thegraph_ws_adapter.py}` — wire in or delete.
- [ ] [SERVICE] P2. market-tick-data-service: consolidate `onchain/helius_solana.py::HeliusSolanaAdapter` and
      `cli/handlers/native_staking_handler.py`'s hand-rolled Helius calls onto one implementation.
- [ ] [SERVICE] P3. market-tick-data-service: land the corrected `onchain/__init__.py` docstring quoted in § 2.2 once
      the shared checkout is clean.
- [ ] [SERVICE] P3. market-tick-data-service: trace whether `curve_adapter.py::_download_liquidity`'s broad-except
      `return []` is distinguishable from a genuine zero-snapshot day in the caller's success/failure accounting.
