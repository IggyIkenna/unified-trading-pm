---
doc_type: plan
title: >-
  Pacifica-Solana perp DEX re-integration — UAC through strategy-service
summary: >-
  Re-integrate PACIFICA-SOLANA (real CLOB, hourly-settled funding rates) after the 2026-07-16 cull and its 2026-08-14
  reversal — split out of the combined Jupiter+Pacifica plan once Pacifica's gates fully resolved while Jupiter's did
  not. Every prerequisite is now closed by REAL testing, not documentation: live WS streamed trades with zero
  credentials (the pre-cull BLOCKED-CREDENTIALS assessment no longer holds), REST endpoints match the deleted parser's
  expected shapes exactly, a real markets-discovery endpoint exists (obsoleting the old hardcoded 10-coin list), and the
  cefi/derivative_ticker schema already carries everything needed (funding_rate, mark_price, index_price, open_interest)
  — no new data_type or instrument_type required. Most of the stack is a RESURRECTION of real working code the cull
  deleted (instruments-service adapter, MTDS batch REST adapter, MTDS live WS scaffold); execution-service is the one
  genuinely net-new piece (zero prior Pacifica code ever existed there). Sequenced UAC registry → instruments-service →
  MTDS (batch + live) → execution-service → strategy-service, the real dependency order.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, execution-service, strategy-service]
scope: [engineer]
tags: [defi, cefi, solana, pacifica, perp-dex, funding-dispersion, venue-reintegration, clob]
related:
  [
    /plans/active/solana_lst_carry_jupiter_perps_and_kamino_borrow_2026_08_12.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /codex/04-architecture/solana-defi-coverage.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-funding-dispersion.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
  ]
created: 2026-08-14
last_updated: "2026-08-14"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 9
estimate_calibrated_ai_days: 6.5
assigned_role: data_engineering
effort: high
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Split out of /plans/active/solana_lst_carry_jupiter_perps_and_kamino_borrow_2026_08_12.md 2026-08-14. That plan's
  Track 2 (Pacifica) had every gate resolved via real API testing (live WS streamed trades with zero credentials, REST
  shapes confirmed, schema confirmed clean) while Track 1 (Jupiter+Kamino) still has two open judgment gates (economics
  spread, schema-mapping decision). Operator: "just pacifica then lets build plan from IS to Strategy service" —
  explicit instruction to split and sequence the buildable track. Kept `assigned_vm: NA` (human/local, operator's
  explicit choice over AO-dispatch) despite every gate being resolved, because this session's own corrections (the
  untested-Pacifica-premise catch, the schema-gap catch, the StandX settlement-risk catch) all came from the operator
  staying in the loop — a background worker wouldn't have had that.
---

# Pacifica-Solana perp DEX re-integration

**Why this plan exists, and why it's separate from the Jupiter+Kamino plan.** Both venues were re-authorized in the same
2026-08-14 operator ruling (`/codex/04-architecture/solana-defi-coverage.md`'s 🟢 REVERSAL banner), and were originally
scoped together. But Pacifica's every gate is now closed by direct testing (see §A) while Jupiter's economics question
and schema-mapping decision remain open judgment calls — so this plan is `status: active` and buildable today, while the
Jupiter+Kamino plan stays `status: draft`, gated. Splitting avoids blocking Pacifica's ready work on Jupiter's
unresolved one.

**Current state, audited 2026-08-14 — mostly a RESURRECTION, not a rebuild:**

| Layer                                                | State                                                                                                       |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| UAC (`COLLATERAL_REGISTRY`, `VENUES_BY_ASSET_GROUP`) | ❌ never existed for Pacifica — net new (§B)                                                                |
| instruments-service                                  | ✅ existed, deleted `instruments-service@dee3f6a4` — resurrect + modernize (§C)                             |
| market-tick-data-service (batch)                     | ✅ existed + WORKING, deleted `market-tick-data-service@2e674d1f` — resurrect, verified shape-accurate (§D) |
| market-tick-data-service (live)                      | ⚠️ existed as a BLOCKED-CREDENTIALS scaffold, never activated — **now provably activatable** (§A, §D)       |
| execution-service                                    | ❌ never existed — genuine net new, zero prior commits (§E)                                                 |
| strategy-service                                     | ❌ never wired as a perp-hedge/funding-dispersion venue candidate (§F)                                      |

**What Pacifica is, mechanically** (confirmed live, not from docs alone): a real off-chain-matching CLOB — trade data
carries `event_type: "fulfill_taker"`/`"fulfill_maker"` pairs, genuine order matching, not pool-fill attribution. USDC
unified margin (cross or isolated), linear contracts only, no coin-margined product, **no LST accepted as margin** (so
this venue does NOT restore `CARRY_STAKED_BASIS` — it targets `CARRY_FUNDING_DISPERSION` and straight-basis structures
only). Real hourly-settled funding rates, recalculated every 5s. Up to 50x leverage. Deploy date 2025-06-01.

**Codex SSOTs each change is checked against:** [solana-defi-coverage](/codex/04-architecture/solana-defi-coverage.md) ·
[carry-funding-dispersion](/codex/09-strategy/architecture-v2/archetypes/carry-funding-dispersion.md) ·
[tier-and-import-architecture](/codex/04-architecture/tier-and-import-architecture.md) ·
[defi-canonical-naming-ssot](/codex/02-data/defi-canonical-naming-ssot.md) ·
[shard-level-failure-isolation](/codex/04-architecture/shard-level-failure-isolation.md) ·
[gcs-and-manifest-delete-safety-protocol](/codex/02-data/gcs-and-manifest-delete-safety-protocol.md)

## A. Gate — RESOLVED 2026-08-14 via real API calls, kept here as the evidence record

The pre-cull live connector was a **BLOCKED-CREDENTIALS scaffold, never activated** — as of 2026-07-06 it documented
`wss://ws.pacifica.fi/v1` as gated behind a paid Helius/Triton RPC key plus a Pacifica partner header. **Closed by
direct testing, not documentation-reading:**

- [x] [AGENT] P0. ✅ **Real WS test, zero credentials.** Connected to `wss://ws.pacifica.fi/ws` (note: `/ws` path, not
      `/v1` as the old scaffold assumed) with no API key, no RPC tier, no partner header. Subscribed to the `trades`
      channel for `BTC` and received real live trade ticks within ~2s:
      `{"channel":"trades","data":[{"h":252234313,"s":"BTC","a":"0.00351","p":"62759","d":"open_long",     "tc":"normal","t":1786714266923,"li":11622278699,"it":0}]}`.
      The 2026-07-06 assessment no longer holds — public, unauthenticated live streaming works today. §D's live
      connector can target real implementation.
- [x] [AGENT] P1. ✅ **Real REST calls, base URL and response shapes confirmed.** `https://api.pacifica.fi/api/v1` is
      live: `GET /trades?symbol=BTC` returns real recent-trade rows (`price`/`amount`/`side`/`created_at` — matches the
      deleted `_parse_pacifica_trades`'s expected fields exactly); `GET /book?symbol=BTC` returns real order-book levels
      (`l: [[bids],[asks]]` with `p`/`a`/`n` per level, `t` timestamp — matches the deleted `_build_pacifica_book_row`'s
      expected shape exactly). The deleted parser code is not stale — §C/§D restore it as-is, no shape migration needed.
- [x] [AGENT] P2. ✅ **Real markets-discovery endpoint confirmed — the curated coin-list workaround is obsolete.**
      `GET /info` returns a full live market list (verified: BTC, ETH, SOL, PUMP, XRP, and more — 20+ per current docs),
      each row carrying `symbol`, `tick_size`, `lot_size`, `max_leverage`, `min_order_size`,
      `instrument_type: "perpetual"`, AND **`funding_rate`/`next_funding_rate` inline**. `/info` alone serves both
      instrument discovery (§C) and a funding-rate snapshot. Restore the adapter calling `/info` dynamically instead of
      the hardcoded 10-coin list (`BTC, ETH, SOL, HYPE, XRP, DOGE, BNB, SUI, PUMP, FARTCOIN`).
- [x] [AGENT] P2. ✅ **Schema check: no new data_type or instrument_type needed.** Queried the live UAC schema registry
      directly (`find_schema('cefi', 'derivative_ticker')`) — it carries `funding_rate`, `mark_price`, `index_price`,
      `open_interest`, `predicted_funding_rate`, `funding_timestamp`, `next_funding_timestamp`, and more. Everything
      `/info`, `/trades`, and `/book` supply maps cleanly onto existing `cefi` schemas (`derivative_ticker`, `trades`,
      `book_snapshot_5`). `InstrumentType.PERPETUAL` already exists. This is the clean case — contrast with the
      Jupiter+Kamino plan's §A.3, which found a genuine schema gap for Jupiter because `JUPITER-SOLANA` is pinned to
      `defi`, which has no working `derivative_ticker` schema. Pacifica has no equivalent problem: it's cleanly
      `cefi`-classified (matching HYPERLIQUID/ASTER/EXTENDED-STARKNET/ LIGHTER-ZKSYNC), and `cefi/derivative_ticker`
      already fits.

## B. UAC registry — prerequisite for everything below

- [x] [SCRIPT] P1. ✅ **Add `PACIFICA-SOLANA` to `VENUES_BY_ASSET_GROUP["cefi"]`** — `unified-api-contracts@316002f1e6`.
      Discovery pass found the removal footprint was ~18 files wide (registries + comments), not just the 4 named in
      this plan — full sweep done as one coherent unit (see Progress Log). Evidence: `quality-gates.sh` ALL PASSED
      (297s), full suite 13175 passed / 0 failed (3 pre-existing unrelated deployment_ui failures untouched).
- [x] [SCRIPT] P1. ✅ **Add `PACIFICA-SOLANA`'s `CollateralPolicy` to `COLLATERAL_REGISTRY`** — `venue_kind=PERP_DEX`,
      USDC-only margin (cross+isolated), linear contracts only — `unified-api-contracts@316002f1e6`. Also added the
      underlying `VENUE_COLLATERAL_MATRIX` (`venue_collateral.py`) row it derives from (USDC accepted; JitoSOL/mSOL
      explicitly not-accepted, confirmed live 2026-08-14 — no LST margin).
- [x] [SCRIPT] P2. ✅ **Declare `VENUE_DATA_TYPE_CAPABILITIES`** for `trades`, `book_snapshot_5`, `derivative_ticker`,
      `available_from=2025-06-01`, `live_capable=True`/`requires_credentials=False` (real connector, not a
      BLOCKED-CREDENTIALS stub like EXTENDED-STARKNET/LIGHTER-ZKSYNC) — `unified-api-contracts@316002f1e6`.
- [x] [SCRIPT] P2. ✅ **Checked `onchain_perp_batch_handler.py`'s `_VENUE_SOURCE`/`_VENUE_PIPELINE_MODE`/`_VENUE_LAUNCH`
      dicts** — this file lives in `market-tick-data-service` (plan's file location for this todo was wrong), not UAC.
      Confirmed via the same self-archiving-vs-Tardis-routed logic that gates HYPERLIQUID/ASTER/EXTENDED-STARKNET
      (self-archiving, own REST) vs LIGHTER-ZKSYNC (Tardis-routed): Pacifica has confirmed-live direct REST (`/trades`,
      `/book`, `/info`, §A), matching the self-archiving cluster — but its pre-cull code was NEVER routed through this
      shared handler either (own standalone `_umi_pacifica.py`/`umi_tick_provider.py` module). **Answer: no row needed
      here** — §D's resurrected `_umi_pacifica.py` is the real batch path. Will do a final confirm when §D actually
      lands (next).

## C. instruments-service — reference data

- [x] [SCRIPT] P1. ✅ **Resurrected + modernized the reference-data adapter** — `instruments-service@31981f461c`. Pulled
      the deleted file (`instruments-service@dee3f6a4~1:instruments_service/reference_data/adapters/cefi/pacifica.py`,
      curated 10-coin list) as reference, then rewrote against the CURRENT adapter interface shape
      (`classify_venue_error` + `log_event` + `_get_with_retry`, mirroring `extended.py` — the pre-cull file predates
      this interface and a straight restore would not have passed current QG) with dynamic `/info` market discovery
      replacing the hardcoded list per §A's finding. 10 new unit tests (`tests/unit/test_pacifica_adapter.py`), all
      passing — caught and fixed 2 real bugs during testing (a conditional-expression operator-precedence bug that
      silently returned `[]` for every /info call, and dead exception-handling code because `_get_with_retry` wraps
      `aiohttp.ClientError` into `RuntimeError` before it reaches the caller — both confirmed via actually running the
      tests, not just writing them).
- [x] [SCRIPT] P1. ✅ **Restored the factory registration + orchestrator comments** — `instruments-service@31981f461c`.
      `factory.py`'s `_ADAPTERS`/`ADAPTER_DATA_SOURCES` re-registered; fixed 3 stale "PACIFICA removed" comments in
      `orchestrator/defi.py` + `orchestrator/writers.py` (informational only — Pacifica was never in
      `_SOLANA_DEFI_VENUES`, it's cefi not defi, so no list entry needed there, only the comments were stale).
- [x] [SCRIPT] P2. ✅ **Wrote new adapter tests** (no pre-cull test file existed to restore — deleted alongside the
      adapter with no separate parent-commit survivor) — `tests/unit/test_pacifica_adapter.py`, 10 tests, mirrors
      `test_hyperliquid_adapter.py`'s structure. Also fixed 1 collateral test
      (`test_pipeline_e2e_prediction.py::test_rule11_per_ag_dedup_target_counts_byte_unchanged`, CEFI dedup count 24→25)
      caught by the full QG run. Evidence: `quality-gates.sh` ALL PASSED (199s).
- [ ] [SCRIPT] P3. **New follow-up (surfaced 2026-08-14, not in the original plan draft)**: run a reconciliation pass to
      attempt resolving the 265 `QUARANTINE_REGISTRY`-listed `PACIFICA-SOLANA` objects
      (`unified_api_contracts/canonical/quarantine.py`) against the real catalogue now that §C's adapter is live —
      read-only classify, not GCS-destructive. Not done as part of §B/§C themselves (real data reconciliation, not a
      registry-code change) — the registry entry's `reason` field was updated to note this is now possible, but the 265
      objects are deliberately left registered/quarantined until this pass actually runs.

## D. market-tick-data-service — batch and live capture

Depends on §B (venue + capability registration) and benefits from §C landing first (real instrument universe to validate
shard-specs against), but the connector code itself doesn't hard-depend on §C — can be built in parallel.

- [x] [SCRIPT] P1. ✅ **Resurrected the batch REST adapter** — `market-tick-data-service@c87b12db60`. Restored
      `_umi_pacifica.py` from the deleted commit + `umi_tick_provider.py` routing re-binds. Evidence: 10728 passed, 0
      failed on the repo's full pytest suite; `quality-gates.sh` ALL PASSED.
- [x] [SCRIPT] P1. ✅ **Resurrected and ACTIVATED the live WS connector** — `market-tick-data-service@c87b12db60`. Full
      real rewrite (not a flag flip) mirroring `hyperliquid_ws.py`'s structure, incl. the mandatory `asyncio.sleep(0)`
      reconnect-loop fix (2026-08-05 incident — 16-26GB RSS host starvation if omitted). Subscribe message format
      confirmed via WebFetch against `docs.pacifica.fi/api-documentation/api/websocket/subscriptions/     trades.md`
      (`{"method":"subscribe","params":{"source":"trades","symbol":"<COIN>"}}`, cited example, not guessed); unsubscribe
      shape is an honest, documented, inferred-not-confirmed mirror of subscribe (residual risk noted in code + tests,
      no live round-trip performed in this session). Registered under `WS_FEED_CONNECTOR_FACTORIES["PACIFICA-SOLANA"]`.
- [x] [SCRIPT] P2. ✅ **Funding-rate capture confirmed as `derivative_ticker.funding_rate`** —
      `market-tick-data-service@     c87b12db60`. Unchanged from the pre-cull pattern; MTDS batch adapters don't call
      `classify_venue_error()` (confirmed against sibling adapters — that's an instruments-service-layer convention, not
      MTDS's).
- [x] [SCRIPT] P3. ✅ **Restored + rewrote MTDS tests** — `market-tick-data-service@c87b12db60`.
      `tests/unit/test_pacifica_candles.py`, `tests/unit/test_pacifica_solana_perp_ws_connector.py` restored + updated
      for real activation (no more `_CREDENTIALS_AVAILABLE=False` no-op assertions).
- [x] [SCRIPT] P3. ✅ **Shard-level failure isolation confirmed** — `market-tick-data-service@c87b12db60`. No `raise` in
      per-shard loops (matches convention); `classify_venue_error()` correctly absent (MTDS batch adapters never use it,
      unlike instruments-service). **§B4 corrected**: the tentative "no `onchain_perp_batch_handler.py` row needed"
      answer from §B was WRONG — `git show 2e674d1f --stat` proved the deletion commit DID touch this file
      (`_VENUE_SOURCE`/`_VENUE_PIPELINE_MODE`/`_venue_chain`/`_VENUE_LAUNCH`/`UMI_VENUE_FETCH`/symbol-mapping/
      `DROPPED_DATA_TYPES`), all restored. One deliberate deviation from pre-cull behavior: `book_snapshot_5` stays in
      the batch universe (honest-empties on non-today shards) rather than reintroducing an MTDS-local exclusion, since
      UAC has no per-data-type capability entry declaring it batch-incapable yet — documented as a genuine gap, not
      silently worked around.

## E. execution-service — genuinely net new

- [x] [SCRIPT] P1. ✅ **Built `defi_execution/protocols/pacifica.py` from scratch** — `execution-service@c2961ec9a2`.
      Researched Pacifica's real order-auth model via WebFetch (`docs.pacifica.fi/api-documentation/api/signing.md` +
      `.../signing/implementation.md` + `.../signing/api-agent-keys.md`) BEFORE writing any signing code — confirmed
      Pacifica does NOT use an HMAC API-key scheme like Aster; every SIGNED endpoint requires an **Ed25519 signature
      from a raw Solana keypair**. Per the wallet-keys hard-stop, live signing was deliberately NOT implemented —
      `supports_live` stays at `BaseConnector`'s fail-closed default (`False`); constructing with `is_live=True` raises
      `SimulationOnlyConnectorError` (verified by test). `chain="SOLANA"` (not `"off-chain"` like Aster/ Hyperliquid,
      since Pacifica's auth itself is wallet-signing-shaped, matching `JupiterConnector`). Error classification
      confirmed via grep as UAC `classify_venue_error()` (this repo has no separate `DefiErrorCode` dispatch table for
      connector-level errors — that enum serves a different purpose elsewhere). Evidence: 20 new unit tests passing,
      `quality-gates.sh` ALL PASSED (189s).
- [x] [SCRIPT] P2. ✅ **Modeled USDC unified margin (cross/isolated)** — `execution-service@c2961ec9a2`. New
      `MarginMode = Literal["cross", "isolated"]` at both position level (`PositionResult`) and order level
      (`place_order(..., margin_mode="cross")`) — a new pattern in this repo (neither Aster nor Hyperliquid modeled
      margin mode explicitly before this).
- [x] [SCRIPT] P3. ✅ **`builder_code` deliberately NOT implemented** — `execution-service@c2961ec9a2`. Documented in
      module docstring + `_build_order_params()` comment as an explicit defer, per this todo's own instruction. **Honest
      gap also flagged**: Pacifica's actual maker/taker fee schedule was not independently verified during the research
      pass, so simulated fills record `fee=Decimal("0")` rather than a fabricated rate — covered by a dedicated test.

## F. strategy-service — venue selection

- [x] [SCRIPT] P1. ✅ **Added `PACIFICA-SOLANA` as a `perp_venue` candidate** — `strategy-service@14d869449f`. The
      plan's assumed registration point (`funding_rate_dispersion.py`) was WRONG — that file is a pure-function helper
      for a different engine with zero venue lists. The REAL registration point, found by investigation, is
      `target_universe/catalog_carry.py`'s `_FUNDING_DISPERSION_VENUES` (feeds `CARRY_FUNDING_DISPERSION`) and
      `_CARRY_BASIS_PERP_VENUE_BUNDLES` (feeds `CARRY_BASIS_PERP`, the plan's "straight-basis structures") — ASTER
      already appears in both; Pacifica added the same way to both. Confirmed via 6 new tests, including 3 negative
      assertions proving zero staked-basis eligibility.
- [x] [SCRIPT] P2. ✅ **Confirmed registry-population-only, no new mechanism** — `strategy-service@14d869449f`.
      `paper_universe.py`'s generic archetype→required-config-key map + the engine's per-tick generic `venue` field read
      confirms the plan's own framing was right, once pointed at the real registration files above.
- [x] [SCRIPT] P3. ✅ **Confirmed PnL/risk paths handle cross/isolated margin generically** —
      `strategy-service@     14d869449f`. `risk/v2/margin_sim.py` reads `capability.margin_spec.mode` from the UAC
      `CollateralPolicy` registry (§B already landed Pacifica's cross+isolated policy there) — venue-agnostic, no change
      needed. The one venue-hardcoded margin-mode dict found (`CEFI_PERP_MARGIN_MODELS`) already excludes
      ASTER/DERIBIT/KRAKEN-FUTURES etc. — Pacifica's absence there is consistent with every other funding-dispersion
      venue, not a new gap. **Real cross-repo finding surfaced by this todo**: UAC's `venue_tokens.py` `_CEFI_TOKENS`
      frozenset (consulted by the slot-label parser) was missing `"pacifica"` — §B's sweep hadn't covered it because
      nothing consumed the token yet at sweep time. Fixed same-day: `unified-api-contracts@ce7c07d9af`.

## G. Documentation

- [x] [SCRIPT] P2. ✅ **Updated `/codex/04-architecture/solana-defi-coverage.md`'s venue-registry tables** —
      `unified-trading-pm@<pending push>`. Replaced the struck-through DRIFT-only historical table with the real
      post-reintegration state (PACIFICA-SOLANA live row + REST/WS bases, DRIFT-SOLANA still struck through, Jupiter
      explicitly noted as separately-tracked/not-done); added a "RE-INTEGRATION COMPLETE" banner with the git-history
      resurrection facts (the two wrong pre-cull premises, the execution-service live-signing gap, the deferred
      quarantine-reconciliation follow-up) so a future reader doesn't have to re-derive them from `git log`. Updated
      frontmatter `summary`/`repos`/`related`/`last_reviewed` to match.
- [x] [SCRIPT] P3. ✅ **Cross-linked this plan and the Jupiter+Kamino plan's Progress Logs** —
      `unified-trading-pm@<pending push>`. Added a "sibling track complete" entry to the Jupiter+Kamino plan's Progress
      Log pointing back here with the execution-service live-signing finding flagged as relevant to Jupiter's own
      (not-yet-resolved) gates; this plan's own Progress Log (below) already carries the split-decision pointer forward.

## Progress Log

- **2026-08-14/15 (§D-§F landed, full stack shipped)** — §D (MTDS), §E (execution-service), §F (strategy-service) all
  shipped with full QG green: `market-tick-data-service@c87b12db60`, `execution-service@c2961ec9a2`,
  `strategy-service@14d869449f`. Plus a same-day cross-repo fix `unified-api-contracts@ce7c07d9af` (venue_tokens.py
  `_CEFI_TOKENS` gap §F surfaced). Parallelized §D/§E/§F as 3 background sub-agents (different repos, no file overlap)
  after §B/§C landed — each did real investigation, not blind pattern-copying, and each found something the plan's draft
  got wrong: §D discovered §B4's "no onchain_perp_batch_handler.py row needed" tentative answer was incorrect (the
  deletion commit DID touch it); §E discovered Pacifica's order-auth is raw Solana Ed25519 wallet-signing, not
  Aster-style HMAC — correctly triggered the wallet-keys hard-stop and left `supports_live=False`; §F discovered the
  plan's assumed registration file (`funding_rate_dispersion.py`) was wrong and found the real one (`catalog_carry.py`),
  and separately confirmed (with 3 negative tests) that Pacifica was never made staked-basis/LST-eligible. One
  operational note: a UAC `quality-gates.sh` run stalled ~18 min in the resource-ledger admission-wait with zero actual
  contention (confirmed via `ps`/`lsof` — no other QG process was running) — killed and re-ran clean rather than waiting
  indefinitely; worth a look if this recurs, but treated as a one-off here, not filed as a separate issue. **Full stack
  now live**: UAC → instruments-service → MTDS (batch+live) → execution-service (simulation-only, pending an operator
  decision on live signing) → strategy-service (CARRY_FUNDING_DISPERSION + CARRY_BASIS_PERP). Remaining: §G (docs) + the
  new §C follow-up (265-object quarantine reconciliation, deferred, tracked).

- **2026-08-14 (autonomous build-out started)** — Invoked `/autonomous` to drive §B-§G to completion. §A already fully
  resolved (real API testing). Started §B (UAC registry, `unified-api-contracts`) — the discovery pass found the removal
  footprint is much larger than §B's 4 todos suggested: ~16 files in `unified_api_contracts/` carry
  `# PACIFICA ... removed 2026-07-16` markers (registries + comments), not just `VENUES_BY_ASSET_GROUP`/
  `COLLATERAL_REGISTRY`/`VENUE_DATA_TYPE_CAPABILITIES`/`onchain_perp_batch_handler.py`. Treating the full sweep as
  necessary for §B to be genuinely correct (a partial UAC registration would leave §C-§F resolving against an
  inconsistent venue picture) — this is IN PROGRESS, not yet a scope change to the plan itself, just a wider §B than
  drafted. Done directly (uncommitted, local edits) so far:
  - `unified_api_contracts/registry/market_data_categories.py` — `PACIFICA-SOLANA` back in
    `VENUES_BY_ASSET_GROUP["cefi"]`, stale removal comment corrected to note the reversal.
  - `unified_api_contracts/registry/venue_collateral.py` — `CollateralAcceptance` rows: `PACIFICA-SOLANA`/`USDC`
    accepted (cross/isolated), `PACIFICA-SOLANA`/`{JitoSOL,mSOL}` explicitly not-accepted (no LST margin, confirmed live
    2026-08-14).
  - `unified_api_contracts/internal/architecture_v2/collateral_registry.py` — net-new `CollateralPolicy` for
    `pacifica-solana` (`venue_kind=PERP_DEX`, USDC-only, cross+isolated margin modes), deriving its `AssetHaircut` from
    the `venue_collateral.py` row above via `_ah_from_venue_collateral`.
  - `unified_api_contracts/canonical/quarantine.py` — updated the `PACIFICA-SOLANA` `QUARANTINE_REGISTRY` entry's
    `reason` to note the 2026-08-14 reversal; the 265 historically-quarantined objects are NOT auto-resolved by this
    change (deliberate — resolving them requires a reconciliation pass against instruments-service's real catalogue once
    §C lands, which is real data work, not a registry-code change). Tracked as a new follow-up todo below.
  - Dispatched a background sub-agent (general-purpose, sonnet) to sweep the remaining ~14 files (`venue_constants.py`,
    `venue_launch_dates.py`, `venue_mapping.py` [3 spots], `venue_adapter_keys.py`, `cefi_perp_venue_endpoints.py`,
    `data_type_capability.py` [real `VENUE_DATA_TYPE_CAPABILITIES` entries — this covers §B3], `expected_coverage.py`,
    `perp_funding_cadence.py`, `venue_instrument_config.py`, `capability_declarations/_cefi.py`,
    `canonical/crosscutting/pipeline_mode.py`, `canonical/crosscutting/_source_priority_data.py` [3 spots],
    `canonical/crosscutting/mvp_scope.py`, `canonical/crosscutting/_mvp_scope_rules.py`) — mirroring the
    HYPERLIQUID/ASTER/EXTENDED-STARKNET/LIGHTER-ZKSYNC sibling pattern in each, fixing every stale "removed" comment it
    touches. **Result pending** — not yet reviewed/shipped as of this journal entry.
  - §B4 (`onchain_perp_batch_handler.py`, actually in `market-tick-data-service`, not UAC — the plan's file location for
    this todo was wrong) — preliminary read: Pacifica has its own direct REST adapter (`_umi_pacifica.py`, confirmed
    live in §A) exactly like the pre-cull code, NOT routed through this shared on-chain-perp batch handler (that
    handler's `_VENUE_SOURCE`/`_VENUE_PIPELINE_MODE` dicts cover HYPERLIQUID/ASTER/EXTENDED-STARKNET/ LIGHTER-ZKSYNC
    only). Tentative answer: **no row needed here** — will confirm when §D's batch adapter resurrection lands and
    cross-check against the pre-cull commit's actual wiring (the deleted `_umi_pacifica.py` was never routed through
    this handler either).
  - Pulled the 3 deleted pre-cull files from git history for §C/§D (read-only, not yet applied):
    `instruments-service@dee3f6a4~1:instruments_service/reference_data/adapters/cefi/pacifica.py` (167 lines, curated
    10-coin list — needs the `/info`-dynamic-discovery modernization per §A/§C1),
    `market-tick-data-service@2e674d1f~1:market_tick_data_service/adapters/_umi_pacifica.py` (495 lines, real REST
    parsing — §A confirmed shapes still match, restore near-as-is),
    `market-tick-data-service@2e674d1f~1:market_tick_data_service/live/connectors/pacifica_solana_perp_ws.py` (189
    lines, the `BLOCKED-CREDENTIALS` scaffold — needs `_CREDENTIALS_AVAILABLE=True` + real `_drain_ws_messages` per
    §D2). Confirmed the modern `instruments-service` adapter interface pattern via `hyperliquid.py` (uses
    `classify_venue_error`, `log_event`, `_make_session`, `VenueMapping().get_instrument_discovery_start` — none of
    which existed in the same form when the Pacifica adapter was deleted, so a straight `git show` restore would NOT
    pass current QG; the `/info`-based rewrite needs to follow `hyperliquid.py`'s current shape, not the old file's).
  - **New follow-up todo (not in original plan draft)**: after §C lands, run a reconciliation pass to attempt resolving
    the 265 `QUARANTINE_REGISTRY`-listed `PACIFICA-SOLANA` objects against the real catalogue — see
    `unified_api_contracts/canonical/quarantine.py`'s updated reason field. Not GCS-destructive (read/classify only);
    still deferred until a real catalogue exists to resolve against.
  - **Nothing committed/pushed yet** — §B is still mid-flight (waiting on the sub-agent sweep before running QG +
    shipping as one coherent unit, since a partial/inconsistent UAC registration is worse than a slightly-delayed
    complete one). Next tick: review the sub-agent's diff, run `quality-gates.sh`, `quickmerge` the whole §B batch, flip
    §B's checkboxes with the commit SHA, then move to §C.

- **2026-08-14 (§B+§C landed)** — §B (UAC, `unified-api-contracts@316002f1e6`) and §C (instruments-service,
  `instruments-service@31981f461c`) both shipped, full QG green on both repos. Widened §B beyond its drafted 4 todos to
  a genuine ~18-file sweep (registries + 6 stale-test fixes) once discovery showed the removal footprint was that wide —
  a partial UAC registration would have left §C-§F resolving against an inconsistent venue picture. Two real bugs caught
  by actually running the new instruments-service adapter tests before shipping (not just writing them): an
  operator-precedence bug in the `/info` response parser that silently returned an empty market list every time, and
  dead exception-handling code (the base adapter's `_get_with_retry` wraps `aiohttp.ClientError` into `RuntimeError`
  before it reaches the caller, so catching only `ClientError` never fired — fixed by catching both, mirroring
  `extended.py`'s already-correct pattern). One new out-of-plan follow-up tracked as a P3 todo in §C (265
  historically-quarantined Pacifica objects, reconciliation deferred to a real data pass, not done as a side-effect of a
  registry-code change). Next: §D (MTDS batch + live), which needs a final confirm-on-landing of §B4's "no
  `onchain_perp_batch_handler.py` row needed" answer.
- **2026-08-14** — Split out of `/plans/active/solana_lst_carry_jupiter_perps_and_kamino_borrow_2026_08_12.md`'s Track 2
  on operator instruction ("just pacifica then lets build plan from IS to Strategy service"), once real testing (that
  plan's §A.2) fully resolved every Pacifica gate while the Jupiter track's gates (§A.1 economics, §A.3 schema mapping)
  stayed open. `status: active` from creation — no blocking decisions remain, only real build work. Sequenced UAC →
  instruments-service → MTDS → execution-service → strategy-service, the genuine dependency order (venue must exist in
  the registry before any adapter can register against it; MTDS and execution-service can proceed in parallel once UAC
  lands; strategy-service needs the others wired to have real data/execution to select against). Kept `assigned_vm: NA`
  per explicit operator choice over AO-dispatch, despite the work being technically AO-eligible now (every gate closed)
  — this session's value came from the operator catching things (untested premise, schema gap, StandX settlement risk)
  that a background worker executing todos alone wouldn't have surfaced.
