---
doc_type: issue
title: DeFi venue phase readiness ruling — 20 pipeline-phase venues, per-venue IS-producibility verdict
summary: >-
  Resolves the walkthrough_feedback_remediation_2026_08_21.md "Bucket the 23 real declared-but-unbucketed
  venues" todo, which was BLOCKED on discovering `VENUES_BY_ASSET_GROUP["defi"]` is DERIVED from
  `_DEFI_VENUE_PHASE` (market_data_categories.py ~line 537), not a literal list — so "bucketing" a venue means
  flipping `DEFI_VENUE_PHASE` "pipeline"→"live", a real IS-producibility/readiness claim, not a registry-hygiene
  fix. Operator authorized this ruling explicitly, real per-venue, evidence-based, 2026-08-21. Per-venue verdict
  requires an adapter check (instruments-service/market-tick-data-service) AND a manifest-capture check AND a
  live-mainnet-protocol check (secondary, confirming) — all three independently, never code-existence or
  web-research alone. Result: 0 of 20 flip to live this pass. 19 are NOT READY with fresh, dated, code-level
  evidence. 1 (MORPHO-ARBITRUM) is UNCERTAIN — real partial evidence, but this session could not independently
  confirm manifest capture (GCS access from the working environment timed out repeatedly) — left `pipeline`,
  tracked as its own follow-up todo below rather than guessed either way.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, instruments-service, market-tick-data-service]
scope: [engineer]
assigned_vm: NA
execution_scope: local-only
tags: [defi, venue-phase, honest-coverage, readiness, registry]
priority: P1
source: operator-request-2026-08-21
parent_epic: system_readiness_master
related:
  [
    /plans/active/walkthrough_feedback_remediation_2026_08_21.md,
    /plans/active/code_readiness_t1_contracts_library_externalapi_2026_08_19.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-22
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
context_scope:
  [
    unified-api-contracts/unified_api_contracts/registry/defi_venues.py,
    unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py,
    instruments-service/instruments_service/engine/orchestrator/defi.py,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
---

# DeFi venue phase readiness ruling — 2026-08-22

## Verdict table

`_build_defi_venues()` (`instruments-service/instruments_service/engine/orchestrator/defi.py`) is the
authoritative enumeration IS actually queries: a protocol/chain pair is IS-producible only if it appears via
(a) `_SUBGRAPH_PROTOCOL_TO_VENUE_PREFIX` × `get_supported_chains_for_protocol()` (reads UAC's `SUBGRAPH_IDS`,
`capability_declarations/_defi.py`), or (b) the hand-curated `_STATIC_DEFI_VENUES` / `_SOLANA_DEFI_VENUES` lists.
Every NOT READY verdict below traces to one of these two enumeration paths genuinely excluding the venue today.

| Venue | Verdict | Evidence |
|---|---|---|
| AAVE_V3-SCROLL | NOT READY | `aave_v3` `SUBGRAPH_IDS` has no SCROLL entry (ETHEREUM/ARBITRUM/OPTIMISM/POLYGON/AVALANCHE/BASE/LINEA/BSC only) — `_build_defi_venues()` can never enumerate this chain. |
| AAVE_V3-ZKSYNC | NOT READY | Same `aave_v3` `SUBGRAPH_IDS` gap — no ZKSYNC entry. |
| COMPOUND-ETHEREUM | NOT READY | Bare `compound` (governance/analytics) has no subgraph mapping and isn't in `_STATIC_DEFI_VENUES`; its declared capability is `governance_events` only (`defi_venue_capabilities.py`), not a lending market — not IS-producible. |
| COMPOUND_V3-POLYGON | NOT READY | `compound_v3` `SUBGRAPH_IDS` explicitly notes POLYGON "removed: subgraph returns 0 markets (Compound V3 not active on Polygon)" — the protocol itself isn't deployed there. |
| COMPOUND_V3-SCROLL | NOT READY | `compound_v3` `SUBGRAPH_IDS` has no SCROLL entry. |
| EULER_V2-ARBITRUM | NOT READY | `euler_v2` is deliberately excluded from `_SUBGRAPH_PROTOCOL_TO_VENUE_PREFIX` ("removed from universe — not needed yet") and not in `_STATIC_DEFI_VENUES`; `euler_v2.py`'s reference-data adapter is Ethereum-only regardless of the `SUBGRAPH_IDS` declaration existing. |
| **MORPHO-ARBITRUM** | **UNCERTAIN** | Real adapter chain support confirmed (`morpho.py::_MORPHO_CHAIN_IDS` includes `"ARBITRUM": 42161`); real dated capability declared (`DEFI_VENUE_DATA_TYPE_CAPABILITIES["MORPHO-ARBITRUM"] = {"lending_indices": "2024-06-01", "oracle_prices": "2024-06-01"}`); currently computes as a `batch_capable_venues()` member (present in `tests/data/mtds_batch_live_coverage_baseline.json` as a live-*connector* gap, not a batch-capture gap — i.e. today's code already treats it as batch-capable); protocol independently re-verified live mainnet 2026-07-26 (~$3.0B supplied/borrowed on the USDC/K market, per the `SUBGRAPH_IDS["morpho"]` comment in `capability_declarations/_defi.py`). Against this: `DEFI_VENUE_PHASE`'s own comment for it ("not in IS-producible set despite having rows (not in `_build_defi_venues()`)") lacks the measured N-rows/date citation this file's other flips carry, and this session could not independently confirm non-empty manifest `capture_status` — direct `gcloud storage` subprocess calls are hard-blocked by a workspace guardrail (UTL-only), and the UTL `cloud_interface.get_storage_client()` GCS read of `gs://central-element-323112-honest-coverage/{date}/coverage.json` (the SSOT path per `/codex/02-data/honest-coverage-model.md`) timed out repeatedly (~120s+, twice) from this session's environment with no diagnostic output — a real tooling gap, not evidence either way. Per `/codex/02-data/honest-absence-downstream-handling.md` and `/codex/02-data/data-pipeline-correctness-hard-rule.md`: do not flip on partial/code-only evidence. Left `pipeline`. Follow-up todo below. |
| MORPHOVAULTS-ETHEREUM | NOT READY | Not in the subgraph map or `_STATIC_DEFI_VENUES` — vault/analytics identity, no adapter enumeration route at all. |
| FRAX-ETHEREUM | NOT READY | Same as above, plus explicit history: real data existed but stopped dead 2026-06-21 with no scheduler (`DEFI_VENUE_MTDS_ADAPTER_VERIFIED_NOT_YET_SCHEDULED` docstring, `defi_venues.py`) — never qualified for promotion (UNVERIFIED-CLAIM class). |
| IDLE-ARBITRUM | NOT READY | `idle.py` has zero Arbitrum entries in `_IDLE_VAULTS_BY_CHAIN` — would enumerate 0 rows, deliberately left un-enumerated (comment in `defi.py`). |
| YEARN_V3-OPTIMISM | NOT READY | YEARN_V3-ETHEREUM/ARBITRUM are `_STATIC_DEFI_VENUES`-live; OPTIMISM explicitly excluded ("chains whose adapter registry is empty for that chain... deliberately NOT enumerated", `defi.py`). |
| BEEFY-POLYGON | NOT READY | Same class — BEEFY live on ETHEREUM/ARBITRUM/BASE/AVALANCHE/BSC; POLYGON's curated registry is empty, same `defi.py` exclusion comment. |
| UNISWAP-ETHEREUM | NOT READY | Bare `uniswap` (governance analytics, declared capability = `governance_events` only) is not in the subgraph map or `_STATIC_DEFI_VENUES` — distinct from the real, live UNISWAP_V2/V3/V4 venues. |
| PANCAKESWAP_V3-ARBITRUM | NOT READY | `pancakeswap_v3` `SUBGRAPH_IDS` has only BSC/ETHEREUM/BASE — no ARBITRUM entry. |
| STARGATE-ETHEREUM | NOT READY | `bridge_events` protocol, not in the subgraph map or `_STATIC_DEFI_VENUES`; among the "STILL-BROKEN: crash-looping cron or never scheduled at all" set per `DEFI_VENUE_MTDS_ADAPTER_VERIFIED_NOT_YET_SCHEDULED`'s docstring. |
| ACROSS-ETHEREUM | NOT READY | Same `bridge_events`/STILL-BROKEN class as STARGATE-ETHEREUM. |
| FLASHBOTS-ETHEREUM | NOT READY | Same STILL-BROKEN class (MEV analytics); separately still an open, undecided "infra-not-venue?" question per `mtds_batch_live_coverage_baseline.json`'s own description — **no operator ruling on this name** (only ALCHEMY-ONCHAIN was ruled on 2026-08-21) — left untouched. |
| LIFINITY-SOLANA | NOT READY | Adapter wired in IS `factory._ADAPTERS` but upstream measurably dead — re-verified fresh 2026-08-22 (this session, WebFetch): `api.lifinity.io/pools` → HTTP 522, same failure as the 2026-07-22 in-code finding, over a month later. |
| METEORA-SOLANA | NOT READY | Re-verified fresh 2026-08-22: `app.meteora.ag/api/pools` → HTTP 404, unchanged since 2026-07-22. |
| PHOENIX-SOLANA | NOT READY | Re-verified fresh 2026-08-22: `api.phoenix.trade` → NXDOMAIN, unchanged since 2026-07-22. |

**Net effect**: `_DEFI_VENUE_PHASE` unchanged for all 20 venues this pass. `VENUES_BY_ASSET_GROUP["defi"]`'s
derived count is unaffected — this is deliberate, not an oversight: a `pipeline`→`live` flip is an
IS-producibility claim, not a count-reconciliation move, and none of the 20 cleared the bar.

## ALCHEMY-ONCHAIN re-home (separate, resolved sub-item)

Operator ruling 2026-08-21: ALCHEMY-ONCHAIN is NOT a venue — it's the RPC-based token-transfer analytics data
source (top 20 DeFi tokens, cross-chain via ALCHEMY RPC), a protocol/infrastructure identity. Applied 2026-08-22:

- Removed `"ALCHEMY-ONCHAIN": {"token_transfers": "2020-01-01"}` from `DEFI_VENUE_DATA_TYPE_CAPABILITIES`
  (`unified-api-contracts/unified_api_contracts/registry/defi_venue_capabilities.py`).
- Re-homed the same entry to a new, deliberately-separate `DEFI_DATA_SOURCE_CAPABILITIES` dict in the same file
  (not wired into any venue-shaped consumer — `batch_capable_venues()`, `VENUES_BY_ASSET_GROUP`, position-read
  checks, etc. — by construction).
- This resolves the "may be RPC/MEV infrastructure... unconfirmed... kept in this baseline conservatively
  pending an operator call" note both `tests/data/mtds_batch_live_coverage_baseline.json` and
  `tests/data/strategy_position_read_mode_baseline.json` carried for it. Removed ALCHEMY-ONCHAIN from both
  baselines' gap lists in the same change (it no longer computes as a `batch_capable_venues()` member at all —
  a registry-shape correction, not a live-connector or position-reader win) and appended a dated `UPDATE
  2026-08-22:` note to each description, matching this corpus's established pattern.
- ALCHEMY-ONCHAIN stays a member of `ALL_DEFI_VENUES`/`DEFI_VENUE_PHASE` (phase="pipeline", `defi_venues.py`)
  and of `capability_declarations/_defi.py`'s `PROTOCOL_CAPABILITIES["alchemy_onchain"]` (venue_prefix="ALCHEMY",
  already `protocol_class=INFRASTRUCTURE`) and `venue_granularity_seed.py`'s seed tuple — those three registries
  are OUT of this ruling's explicit scope (the operator's wording was "remove it from `VENUE_DATA_TYPE_CAPABILITIES`
  as a venue token and re-home its capability... do NOT bucket it", not a full de-venue-ification everywhere the
  string appears). **Flagged as a genuine, wider entanglement for a future explicit-scope pass** if the operator
  wants ALCHEMY-ONCHAIN fully un-venued: it's still venue-shaped in those three places today.
- FLASHBOTS-ETHEREUM is a separate, still-undecided name from the same "infra-not-venue" baseline note — **not
  touched**, no ruling given.
- Verified: 7/7 targeted tests green (`test_mtds_venue_coverage_cascade_invariant.py`,
  `test_strategy_position_read_mode_cascade_invariant.py`); `quality-gates.sh --no-fix` green.

## Todos

- [ ] [BACKEND] P2. MORPHO-ARBITRUM manifest-capture follow-up: get a working GCS/manifest read path (this
      session's UTL `cloud_interface.get_storage_client()` reads of
      `gs://central-element-323112-honest-coverage/{date}/coverage.json` timed out repeatedly with no
      diagnostic output from a laptop-slot environment — investigate the network/ADC path, or use a VM/
      deployment-api route instead) and confirm whether MORPHO-ARBITRUM has real, non-empty `capture_status`
      recently. If yes: flip `DEFI_VENUE_PHASE["MORPHO-ARBITRUM"]` `"pipeline"`→`"live"` in
      `unified-api-contracts/unified_api_contracts/registry/defi_venues.py` in the SAME commit that also adds it
      to `instruments-service`'s `_build_defi_venues()` enumeration (denominator drift guard:
      `set(_build_defi_venues()) == VENUES_BY_ASSET_GROUP["defi"]` — either via extending `morpho`'s chain
      discovery or adding `MORPHO-ARBITRUM` to `_STATIC_DEFI_VENUES`, whichever matches how the adapter is
      actually invoked). If no: document the gap the same way `IDLE-ARBITRUM`/`YEARN_V3-OPTIMISM` are documented
      in the verdict table above, close this todo without flipping, and archive this issue.
- [ ] [OPERATOR] P3. If a full ALCHEMY-ONCHAIN de-venue-ification is wanted (removing it from
      `ALL_DEFI_VENUES`/`DEFI_VENUE_PHASE`, `PROTOCOL_CAPABILITIES["alchemy_onchain"]`'s venue_prefix shape, and
      `venue_granularity_seed.py`), scope that explicitly — the 2026-08-21 ruling only covered
      `VENUE_DATA_TYPE_CAPABILITIES`. Otherwise close this todo as "ruling was intentionally narrow, no further
      action" and archive this issue once the MORPHO-ARBITRUM todo above also resolves.
