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
author: unknown
last_updated: "2026-08-10"
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
context_scope:
  [
    /codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md,
    /plans/archive/issues/defi_base_adapter_success_key_ignored_by_failure_accounting_2026_07_27.md,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/live/governance_params_event_poller.py,
    instruments-service/instruments_service/reference_data/adapters/defi/jupiter.py,
    instruments-service/instruments_service/reference_data/factory.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/onchain/helius_solana.py,
  ]
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

### 2.3 RESOLVED 2026-07-27 (slot-11) — **CONFIRMED MASKING**, `curve_adapter.py::_download_liquidity`'s broad except IS

indistinguishable from a genuine empty-result day, quoting the full caller chain

`defi/curve_adapter.py::_download_liquidity` (~line 682) catches broad `Exception`, logs, and `return []` on failure —
traced the full caller chain end to end; it is **NOT distinguishable** from a genuine zero-liquidity-snapshot day
anywhere in the accounting, and the masking is worse than the original lead suspected — it also swallows a **whole-day
setup failure** (e.g. `_ensure_alchemy_client()`/`w3.eth.contract()` raising), not just per-block RPC misses.

**The chain, each hop quoted:**

1. `curve_adapter.py::_download_liquidity` (:682-684): `except Exception as e: logger.error(...); return []` — catches
   EVERYTHING from the whole try block (client setup, contract binding, `BlockResolver.get_sample_blocks()`, the
   sampling loop itself), not just per-block queries. Per-block RPC failures never even reach this except — they're
   already caught individually one level down in `_query_curve_pool_at_block` (:639,
   `except (OSError, ValueError, RuntimeError, Exception)`, returns `None` per block) — so if EVERY sample in the day
   fails, `liquidity_snapshots` ends up `[]` via the NORMAL return path (:680), not even via the except block.
2. `curve_adapter.py::_fetch_curve_data_type` (:469-470):
   `data = await self._download_liquidity(...); return data if data else []` — an empty list from EITHER cause (failure
   or genuine) returns `[]` here, uniformly.
3. `curve_adapter.py::download_market_data` (:451-453):
   `fetched = await self._fetch_curve_data_type(...); if fetched is not None: results[data_type] = fetched` — `fetched`
   is `[]`, which `is not None`, so `results["dex_pool_state"] = []` IS added to the dict. `results` (returned as
   `result` to the caller) is therefore `{"dex_pool_state": []}` — a **non-empty dict** — regardless of whether the day
   genuinely had zero snapshots or the whole fetch failed.
4. `base_defi_adapter.py::_download_all_instruments` (:290-295):
   `result = await self.download_market_data(...); if not result: continue` — `result = {"dex_pool_state": []}` is
   truthy (a dict with one key, even if its value is an empty list, is never falsy in Python), so this `continue`
   **never fires** for this cause. Execution falls through to `_flatten_instrument_result(result, ...)` (contributes 0
   rows, since iterating an empty list appends nothing) and `succeeded += 1` (:295) — the SAME counter path as a real
   success. The `failed` counter (:288, :299, :303) is never incremented; the per-day shard-summary log line (:305-313)
   never surfaces this instrument at all.

**Verdict: masking is real, not "may already be covered by the shard-isolation convention."** Unlike the file's OTHER
broad-except usages (§0's narrow per-field parse guards, and `curve.py:224`'s per-record skip-and-log inside a listing
loop — both legitimate record-level isolation per `/codex/04-architecture/shard-level-failure-isolation.md`), this one
collapses an entire INSTRUMENT-day's outcome (not a single record) into the exact same shape as "nothing to report,"
with zero signal surviving to the caller's failure-accounting.

**Broader than Curve alone — filed separately**: tracing the caller chain surfaced that
`base_defi_adapter.py::_download_all_instruments`'s `if not result: continue` check ALSO never inspects the
`"success": bool` key that ~12 OTHER DeFi adapters already return (`lst_puffer_adapter.py`, `lst_lido_adapter.py`,
`lst_renzo_adapter.py`, `lst_rocket_pool_adapter.py`, `lst_solblaze_adapter.py`, `restaking_jito_adapter.py`,
`restaking_karak_adapter.py`, `vault_pendle_adapter.py`, `lst_coinbase_adapter.py`, `lst_etherfi_adapter.py`,
`lst_kelpdao_adapter.py`, `aave_positions.py` — all return `{"success": False, "error": "..."}` on failure) —
`_flatten_instrument_result` (:50) only uses the `"success"` key to SKIP it during row-flattening, never to route a
`False` value into the `failed` counter. So the masking pattern found here for Curve is a SYSTEMIC gap in the shared
caller, not a Curve-specific bug — filed as its own issue doc since it's a bigger, cross-adapter finding than this
todo's Curve-only scope: `issues/defi_base_adapter_success_key_ignored_by_failure_accounting_2026_07_27.md`.

**Not traced further** (staying honest about scope, matching this doc's own § 5 convention): whether/how a
zero-row-but-`succeeded` DataFrame propagates into manifest `capture_status` (i.e., whether it lands as
`empty_confirmed` vs `attempted_failed` at the GCS-write layer) — that's downstream of `download_batch`'s return value,
outside `base_defi_adapter.py`, and DeFi's actual collection path is CLI operations
(`collect-evm-defi`/`collect-dex-swaps`/etc., not `download_batch` via `umi_tick_provider.py` — confirmed via grep, DeFi
doesn't route through that file at all) that weren't in this todo's scope.

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

| module / file                                                                         | disposition         | reason                                                                                                  |
| ------------------------------------------------------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------- |
| IS `adapters/defi/jupiter.py`                                                         | FLAGGED             | fully built + tested, registered nowhere; needs a wire-in-or-delete decision                            |
| IS `adapters/defi/` (other 50 files)                                                  | KEPT                | all registered in `factory.py::_ADAPTERS`, reachable, no duplication                                    |
| IS `reference_data/router.py` (context, not a `defi/` file)                           | noted               | second resolver, apparently unreached outside its own tests                                             |
| MTDS `onchain_perps/` (3 files)                                                       | KEPT                | both concrete adapters in `VENUE_REGISTRY`                                                              |
| MTDS `adapters/defi/` registered protocol adapters + shared utils                     | KEPT                | all in `VENUE_REGISTRY` or confirmed real consumers                                                     |
| MTDS `adapters/defi/live/` (`hyperliquid_ws.py`, `onchain_event_poller.py`)           | FLAGGED             | exported, tested, zero production callers                                                               |
| MTDS `adapters/defi/live/governance_params_event_poller.py`                           | FLAGGED — big       | plan-marked-complete Phase 1, never actually runs; masks a live-trading fallback three repos downstream |
| MTDS `adapters/defi_live/` (both files)                                               | FLAGGED             | exported, tested, zero callers, no successor exists either                                              |
| MTDS `onchain/glassnode.py`, `onchain/helius_solana.py`                               | KEPT                | both intentionally-parked with a stated reason (`PLANNED_VENUES` / `BLOCKED-CREDENTIALS`)               |
| MTDS `onchain/helius_solana.py` vs `native_staking_handler.py`                        | FLAGGED             | undocumented duplicate implementation of the same Helius RPC capability                                 |
| MTDS `onchain/__init__.py` docstring                                                  | FLAGGED, minor      | stale text; corrected version drafted, not shipped (shared-checkout risk)                               |
| MTDS `adapters/defi/curve_adapter.py::_download_liquidity`                            | FLAGGED — confirmed | broad except → `[]`, CONFIRMED indistinguishable from a genuine empty day at every caller hop (§2.3)    |
| execution-service `adapters/defi_adapter.py::execute_swap/execute_lend/execute_stake` | REMOVED, shipped    | zero callers, bypassed all of `execute_instruction()`'s safety machinery                                |
| execution-service `adapters/defi_adapter.py` (rest of file)                           | KEPT                | fail-loud retry/classify path; Tenderly fallback is named + logged                                      |

## 5. Scope not covered

This audit stayed inside the three directories named in the dispatching todo. It does **not** re-verify
features-service's `aave_risk_calculator.py` / `lending_features.py` or strategy-service's sizing logic referenced in §
2.2's governance-params finding — that would require its own pass in those repos. It also does not cover
`execution_service/defi_execution/` (the UDEI connector package `defi_adapter.py` delegates to) or
`execution_service/trade_execution/adapters/` beyond the single named file, per the dispatching todo's explicit scope.

## 6. Follow-up todos (not made in this pass — each is a real, scoped decision)

- [x] ✅ [SERVICE] P1. **RULED 2026-08-07 (operator) — register Jupiter as a live DeFi venue, full-stack.** Jupiter is a
      major Solana DEX aggregator; scope is NOT just `factory.py::_ADAPTERS["jupiter"]` — it needs: (a) UAC venue
      registration (`VENUE_TO_ADAPTER_KEY` + manifest schema so captured rows get a canonical path), (b)
      instruments-service catalogue/reference-data entry (wire `JupiterReferenceDataAdapter` into `_ADAPTERS`, the
      class + its 2 test files are already built and passing), (c) MVP-venues list inclusion, (d) an MTDS
      market-tick-data-service adapter (does not exist yet — `jupiter.py` today is IS-side reference-data only, no MTDS
      capture-side adapter), (e) execution-service support so Jupiter routes are actually tradable. This is real,
      multi-repo build-out, not a same-pass fix — needs its own scoped plan (LOCAL vs AO-dispatch TBD, see this doc's
      Progress Log). **Tracked as of 2026-08-07**: AO-dispatched plan
      `/plans/archive/2026_08/defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07.md` now covers this (todos
      1-4 + close-out todo 6, which flips this checkbox) — that plan's investigation also found (c) is automatic (no
      separate list) and (e) already exists unwired (`JupiterConnector`), narrowing the real remaining scope; see its
      "Scope corrections vs the operator's framing" section. ✅ **DONE 2026-08-10 — that plan's todos 1-5 all shipped**:
      unified-api-contracts@ad003d03 (UAC venue registration — `DEFI_VENUE_PHASE["JUPITER-SOLANA"]="live"` +
      `VENUE_TO_ADAPTER_KEY["JUPITER-SOLANA"]="jupiter"`), instruments-service@06c6f2dd (`JupiterReferenceDataAdapter`
      wired into `_ADAPTERS` + `_SOLANA_DEFI_VENUES`), market-tick-data-service@9e9c9817 (JUPITER-SOLANA live
      `WSFeedConnector`, `data_type=dex_pool_swaps`), execution-service@507093de (`JupiterConnector` wired into
      `DeFiAdapter`), + market-tick-data-service@73abd655 (Aave-liquidation connector, that plan's todo 5). This
      checkbox flipped by that plan's todo 6 (close-out).
- [ ] [SERVICE] P1. market-tick-data-service: re-verify the governance-parameters-refresh feature end-to-end
      (features-service `aave_risk_calculator.py` asof reads, strategy-service sizing) against the measured fact that
      `GovernanceParamsEventPoller` never runs in production; either wire the poller into a real entrypoint (a
      `live/connectors/`-style registration, or a scheduled batch job) or update the plan/codex record to state plainly
      that this feature has never been live.
- [ ] [DOC] P3. market-tick-data-service: repoint the now-dangling `/plans/active/` plan-reference in
      `market_tick_data_service/live/connectors/aave_liquidations_ethereum_ws.py`'s module docstring (line ~10 — "Plan:
      /plans/active/defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07.md todo 5") to
      `/plans/archive/2026_08/defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07.md` (build plan
      archived 2026-08-11 by the finalize ritual). The sibling `jupiter_solana_ws.py` docstring's bare-filename
      reference (line 22) still resolves and can be repointed in the same pass if editing that file.
- [x] ✅ [SERVICE] P2. **RULED 2026-08-07 (operator) — wire in, do not delete.** market-tick-data-service:
      `adapters/defi/live/onchain_event_poller.py` and `adapters/defi_live/{alchemy_adapter.py,thegraph_ws_adapter.py}`
      register into the real `live/connectors/` registration mechanism (`register_all()` /
      `WS_FEED_CONNECTOR_FACTORIES`) — the code is already built + tested per § 2.2, this is wiring, not new
      implementation. **Tracked as of 2026-08-07**: AO-dispatched plan
      `/plans/archive/2026_08/defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07.md` todo 5 covers
      `onchain_event_poller.py` (Aave-liquidation path only — its own investigation found none of the 3 named classes is
      a `WSFeedConnector`-conforming self-registering class, so real new wrapper code is needed, not a one-line
      `register_all()` addition; the Uniswap-Swap-topic half is deliberately excluded as a duplicate of the already-live
      `dex_swap_uniswap_v3_ws.py`). **`alchemy_adapter.py`/`thegraph_ws_adapter.py` — the "further operator/design
      decision" landed 2026-08-08** (live interactive session): confirmed `onchain_event_poller.py` (already shipped)
      does not import either file, and the actual live-streaming pattern this codebase uses is the completed
      `batch_live_symmetry_master` epic's ~20 dedicated per-venue `WSFeedConnector`s, which neither file is part of —
      operator ruled DELETE. Blocked once by an unrelated repo-wide empty-string-fallback ratchet violation (fixed by a
      concurrent session, `market-tick-data-service@505959b0`) and once by a false-positive "confirmed live" claim from
      a transient clean working-tree read (corrected below) — actually shipped `market-tick-data-service@4e5d8b475`,
      verified via `git show origin/live-defi-rollout:market_tick_data_service/market_interface/__init__.py` (0 refs)
      and `git cat-file -e` on the deleted file (confirmed absent), not `git status` on a shared clone. Wire-in leg of
      this item (that plan's todo 5) shipped `market-tick-data-service@73abd655` — the `OnChainEventPoller` Aave-
      liquidation path is now registered as `live/connectors/aave_liquidations_ethereum_ws.py` under `AAVE_V3-ETHEREUM`,
      `data_type="liquidations"`.
- **[SERVICE] P2. EXTRACTED 2026-08-09 → `defi_satellite_ao_dispatch_batch11_2026_08_09.md`.** RULED 2026-08-08
  (operator): consolidate onto `HeliusSolanaAdapter`, delete `native_staking_handler.py`'s hand-rolled implementation.**
  market-tick-data-service. **2026-08-07 note (unchanged)**: the `BLOCKED-CREDENTIALS` framing in § 2.2 is STALE —
  `helius-api-key` was approved + provisioned 2026-05-15 (confirmed live in
  `/codex/05-infrastructure/credentials-matrix.md`); not credential-blocked. **2026-08-08 scoping (NOT a clean 1:1 swap
  — read both implementations before touching either)**: `HeliusSolanaAdapter` (`onchain/helius_solana.py`) today only
  implements `get_inflation_rate()` / `get_epoch_info()` / `get_token_balances()` / `get_native_balance()` /
  `get_enhanced_transactions()`, with a real retry+backoff contract (3 attempts, exponential backoff, honours
  `Retry-After` on 429, `classify_venue_error` integration) and requires a Helius key (no fallback to another RPC
  provider). `native_staking_handler.py` additionally needs, and the adapter does NOT yet provide: (1) a
  `getVoteAccounts` call (`_fetch_vote_accounts`, per-validator breakdown, top-200 by stake) — must be ADDED to
  `HeliusSolanaAdapter` as a new public method before the handler can consolidate; (2) a 3-tier RPC-URL fallback (Helius
  → Alchemy → public `api.mainnet-beta.solana.com`, `_get_solana_rpc_url`) — the adapter is Helius-only, so the
  handler's graceful degrade to free public RPC when no Helius key is configured has no equivalent in the adapter today
  and must be preserved (either inside the adapter or as a thin wrapper the handler keeps); (3) the deterministic
  historical inflation-SCHEDULE fallback (`_schedule_rate`, on-chain taper constants) for epochs before the current one
  — this is NOT a Helius RPC call at all and stays in `native_staking_handler.py` regardless of the consolidation; (4)
  the Jito MEV-rewards fetch (`_fetch_jito_mev_apy`) — a completely separate public Kobe API, also unrelated to Helius
  and stays as-is. **Consolidation scope**: (a) add `get_vote_accounts()` to `HeliusSolanaAdapter` mirroring
  `_fetch_vote_accounts`'s shape/limit; (b) either extend the adapter with the Helius→Alchemy→public fallback tier, or
  have `NativeStakingHandler` construct `HeliusSolanaAdapter` only when a Helius key is present and keep its own
  lightweight fallback path when absent (avoids over-generalizing the adapter for a fallback need this is currently its
  only caller for); (c) swap `NativeStakingHandler._collect_staking_rows`'s raw
  `_rpc_call`/`_fetch_live_rates`/`_fetch_vote_accounts` for
  `HeliusSolanaAdapter.get_inflation_rate()`/`get_epoch_info()`/`get_vote_accounts()` calls, keeping the schedule-
  rate + Jito MEV logic unchanged; (d) delete the now-dead hand-rolled RPC plumbing
  (`_rpc_call`/`_helius_rpc_attempt`-equivalent/`_fetch_vote_accounts`/`_fetch_live_rates`'s raw-HTTP body,
  `_get_helius_api_key`/`_get_solana_rpc_url`) from `native_staking_handler.py`, keeping only the
  epoch/schedule/Jito-MEV/row-building logic that has no adapter equivalent. Unit tests: assert the adapter's real
  retry/backoff contract now covers the staking-rate live path (previously untested — the handler's own `_rpc_call` had
  zero retry logic), and that the fallback tier + schedule-rate + Jito MEV behavior are unchanged (regression, not new
  behavior). Repo: market-tick-data-service. Done-when: `native_staking_handler.py` imports `HeliusSolanaAdapter` for
  its live RPC path with no duplicate hand-rolled JSON-RPC POST/retry code remaining, and the existing staking-rate unit
  tests (mocked) still pass green.
- [x] [SERVICE] P3. market-tick-data-service: land the corrected `onchain/__init__.py` docstring quoted in § 2.2 once
      the shared checkout is clean. — DONE 2026-07-30 (defi_satellite_ao_dispatch_batch1 finalize reconciliation), see
      defi_satellite_ao_dispatch_batch1_2026_07_25.md todo 12 for full evidence (market-tick-data-service@0cd76b93).
- [x] ✅ [DIAG] P3. **DONE 2026-07-27 (slot-11) — no code shipped (diagnostic-only todo).** Traced whether
      `curve_adapter.py::_download_liquidity`'s broad-except `return []` is distinguishable from a genuine zero-snapshot
      day in the caller's success/failure accounting — **CONFIRMED MASKING**, full caller-chain evidence in § 2.3. Also
      surfaced a broader, systemic version of the same gap affecting ~12 other adapters, filed separately:
      `issues/defi_base_adapter_success_key_ignored_by_failure_accounting_2026_07_27.md`.

## 7. Addendum 2026-08-01 (slot-6, `plans/archive/2026_08/defi_satellite_ao_dispatch_batch7_2026_08_01.md` todo 1) — incremental re-check

Re-dispatch of the SAME source todo (`defi_consolidated_closeout_2026_07_18.md:548`) landed via the scheduled
`na-eligibility-audit` (the closeout plan's checkbox was never flipped after § 1-6 above shipped, since several findings
stayed FLAGGED/open rather than fully resolved — the auditor correctly read the unchecked box but had no way to know a
full audit artifact already existed here). Rather than re-run the full ~100-file audit, diffed the three scoped
directories against this doc's original file list (`git log --since=2026-07-24 --name-only`) to find only what's new:

- **instruments-service `adapters/defi/`**: 7 new files since 2026-07-24 — `ankr.py`, `maker.py`, `mantle.py`,
  `stader.py`, `stakewise.py`, `swell.py`, `aave_v3_plasma_rpc.py`. No deletions.
- **market-tick-data-service** (`adapters/{defi,defi_live,onchain,onchain_perps}/`): no additions or deletions.
- **execution-service `adapters/defi_adapter.py`**: only change is this doc's own § 3 fix (`execution-service@489b78b8`,
  the `execute_swap`/`execute_lend`/`execute_stake` removal) — no regression, methods confirmed still absent.

**New-file findings (instruments-service, all 7 — KEPT, clean):**

- `ankr.py`, `maker.py`, `mantle.py`, `stader.py`, `stakewise.py`, `swell.py` — each 1:1 registered in
  `factory.py::_ADAPTERS` (import + dict entry verified per file) exactly like the other 50 KEPT files in § 1. Zero
  `except` clauses in any of the six — no fallback-masking surface at all.
- `aave_v3_plasma_rpc.py` — NOT a standalone adapter (correctly absent from `_ADAPTERS`): a helper module split out of
  `aave_v3.py` for a basedpyright dynamic-typing boundary (own docstring states the rationale, same pattern as
  `_dex_factory_registry.py`/`_solana_utils.py` in § 1), exporting `discover_plasma_reserves_sync` +
  `resolve_plasma_alchemy_key` — both confirmed imported AND called from `aave_v3.py` (lines 264, 274). Not dead code.
  Two `except` blocks: a narrow per-reserve `except (ConnectionError, TimeoutError, ValueError, RuntimeError): continue`
  inside the discovery loop (record-level skip-and-log, same legitimate shape as `curve.py:224` in § 1) and a broad
  `except Exception:` in the Secret-Manager key lookup — logged, returns `None`, and the code comment explicitly cites
  the SAME audited precedent as `evm_creation_resolver._resolve_rpc_url` for why the broad catch is intentional (ADC/GCP
  credential exception surface isn't a safely-enumerable closed set). Matches rule #2's "genuine, intentional
  fallback... named as such and logged" carve-out — not masking.

**Still-open findings spot-checked for regression (none found — all confirmed unchanged):** `jupiter.py` still absent
from `factory.py`/`router.py` (dead, unresolved); `GovernanceParamsEventPoller` still has zero callers outside its own
file/tests; `HeliusSolanaAdapter` / `AlchemyLiveAdapter` / `TheGraphWsAdapter` / `OnChainEventPoller` /
`HyperliquidWSFeed` (the `defi/live/` class) all still zero-caller outside tests/re-exports.

**Disposition**: this doc's existing artifact (§ 1-6) plus this addendum together satisfy batch7 todo 1's
done_definition ("a written finding per module (kept/fixed/removed + reason) is recorded") for the full current file set
across all three repos. No new fix needed (all 7 new files are clean). The 4 still-open follow-up todos in § 6 remain
open, unaffected by this pass — they were already tracked there before this addendum and are unrelated to the 7 new
files.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - doc's own section-6 header calls each residual 'a real, scoped
  decision'; 4 of 5 are wire-in-or-delete product calls with registry/billing blast radius
- **2026-08-01 (slot-6, defi_satellite_ao_dispatch_batch7-001)**: added § 7 addendum re-verifying the 7 instruments-
  service adapter files added since this doc's original audit — all clean/KEPT, no regression on prior findings. Closes
  batch7 todo 1 by citation; see that plan + the parent `defi_consolidated_closeout_2026_07_18.md:548` checkbox for the
  cross-reference.
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-02** (tranche=defi, autonomous, scheduled): KEEP-NA valid (2026-07-30 verdict re-
  affirmed after the § 7 addendum) — re-read end to end, 4 open items, all in § 6 whose own header calls each "a real,
  scoped decision". Every one is a wire-in-or-delete product call with registry/billing blast radius (jupiter.py's fate;
  the governance-params poller's cross-repo re-verify + wire-or-restate; `defi_live/` disposition; helius_solana vs
  native_staking_handler consolidation) — none worker-determinable. The 2026-08-01 § 7 addendum changed nothing here: it
  explicitly records that "the 4 still-open follow-up todos in § 6 remain open, unaffected by this pass". Doc stays
  `assigned_vm: NA`.
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — dropped the archived
  `defi_governance_params_refresh_2026_06_20.md` plan reference (already fully quoted inline in this doc's own headline
  finding) to stay within the 2-6 entry budget; kept the 6 live-code targets for the 4 still-open section-6 decisions.
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA valid (prior verdicts re-affirmed) —
  re-read end to end, all 4 open items unchanged: wire-in-or-delete/consolidation product decisions with named
  registry/billing/cross-repo blast radius, none worker-determinable. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — all 4 open items remain scoped
  product/architecture disposition decisions (jupiter.py venue registration, governance-params poller OPERATOR-NOTIFY,
  +2 more), none worker-determinable.
- **Operator ruling 2026-08-07 (interactive session, via consolidated NA-blocker-digest audit)**: two of the four §6
  decisions are now RULED (see §6 for full text): (1) Jupiter — register as a live DeFi venue, full cross-repo build-out
  (UAC venue registration, IS catalogue, MVP-venues list, a new MTDS adapter that does not exist yet, execution-service
  routing) — this is materially bigger than the original todo's "add one line to `_ADAPTERS`" framing, now needs its own
  scoped plan. (2) `onchain_event_poller.py` + `defi_live/{alchemy_adapter,thegraph_ws_adapter}` — wire in via
  `live/connectors/register_all()`, not delete. Also corrected: the Helius consolidation item's `BLOCKED-CREDENTIALS`
  framing (§2.2) is stale — `helius-api-key` was approved + provisioned 2026-05-15
  (`/codex/05-infrastructure/credentials-matrix.md`), so that item is a pure consolidation call, not credential-gated.
  Governance-params poller re-verify (item 2 of 4) remains unruled. **Doc stays `assigned_vm: NA`** — the two ruled
  items are now real scoped engineering work that needs its own plan (dispatch destination TBD), not something this
  issue doc itself executes.
- **2026-08-07 (interactive session)**: authored the AO-dispatched plan pair
  `/plans/archive/2026_08/defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07.md` +
  `/plans/archive/2026_08/defi_jupiter_venue_registration_and_live_connector_wireup_finalize_2026_08_07.md`
  covering both 2026-08-07 rulings, per full cross-repo investigation (UAC/
  instruments-service/market-tick-data-service/execution-service). Both this doc's §6 checkboxes updated with pointers
  to that plan (not flipped — work not yet shipped). Key findings that change the operator's own framing: Jupiter's
  "MVP-venues list inclusion" is automatic (no separate list — `_mvp_defi_venues()` derives from `DEFI_VENUE_PHASE`);
  Jupiter's "execution-service support... does not exist" is wrong —
  `execution_service/defi_execution/protocols/jupiter.py::JupiterConnector` already exists, fully built, just unwired
  (same pattern as the IS-side `jupiter.py` this doc already flagged); the wire-in item narrows from 3 files to 1
  (`onchain_event_poller.py` only — `alchemy_adapter.py`/`thegraph_ws_adapter.py` lack a determinable single-venue
  target, flagged as an open question in the new plan rather than forced into a todo).
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — re-read §6 end to end (4 open items).
  Items 1 (Jupiter) and 3 (onchain_event_poller wiring) are deliberately-open citation-trackers only — both explicitly
  say "leave this checkbox open until that plan's todo N lands," with the REAL execution already `assigned_vm: planning`
  in `/plans/archive/2026_08/defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07.md`; flipping this
  doc's own `assigned_vm`
  would risk a worker picking these up as fresh, redundant work. Item 4 (Helius/native_staking_handler consolidation)
  gained a full operator ruling + detailed scoping TODAY (2026-08-08) and is now genuinely bounded — a strong RECLASSIFY
  candidate on its own, flagged for a future round or a dedicated extraction. Item 2 (governance-params-poller
  cross-repo re-verify, the OPERATOR-NOTIFY big finding) remains unruled and cross-repo. Net: whole-doc flip is not
  clean this round. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA valid -- 579-line audit doc, 6 prior na-eligibility-audit
  rounds all landed KEEP-NA valid, re-confirmed today. 2 open checkboxes: a deliberate citation-tracker held open until
  `/plans/archive/2026_08/defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07.md` todo 6 lands
  (verified active/planning, real citation), plus one other gated item. Doc stays `assigned_vm: NA`.
- **2026-08-10 (slot-18, `/plans/archive/2026_08/defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07.md` todo 6)**: closed out
  this doc's §6. Jupiter checkbox (item 1) flipped ✅ citing the plan's shipped SHAs (unified-api-contracts@ad003d03,
  instruments-service@06c6f2dd, market-tick-data-service@9e9c9817, execution-service@507093de,
  market-tick-data-service@73abd655). The wire-in item (item 3) was already flipped by the 2026-08-08 alchemy/thegraph
  DELETE session; appended the todo-5 wire-in SHA (`market-tick-data-service@73abd655`, AAVE_V3- ETHEREUM liquidations
  connector). Wire-in scope was narrowed to `onchain_event_poller.py` only — `alchemy_adapter.py`/
  `thegraph_ws_adapter.py` had no determinable single-venue target and the operator ruled DELETE (see that plan's "Scope
  corrections" + "Open questions"). Also refreshed `/codex/04-architecture/solana-defi-coverage.md` (JUPITER MTDS line +
  `spot_trades` → `dex_pool_swaps`).
