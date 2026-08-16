---
doc_type: plan
title: defi venue e2e wiring batch 1 — 2026-08-16
summary: >-
  Fresh carve-out from venue_e2e_wiring_2026_08_16.md's "Fork per-asset-group dispatch batches" P0 todo — walks
  contract steps 1-9 across every defi (venue, data_type) row from `unified-api-contracts/scripts/
  generate_venue_work_list.py` (200 rows, measured 2026-08-16; re-run the script, this count is not a constant).
  Not an extraction from another source doc — no operator-gated item mixed in, per task_template.md §3 finding Y.
status: active
nature: process
asset_group: [defi]
stage: [data, features, strategy, execution]
repos:
  [
    unified-api-contracts,
    unified-trading-library,
    instruments-service,
    market-tick-data-service,
    features-service,
    strategy-service,
    execution-service,
  ]
scope: [engineer]
tags: [venue-readiness, e2e-wiring, defi, ao-dispatch, satellite-batch]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
drift_direction: advance-code
depends_on: []
estimate_class: infra
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 4.8
assigned_role: backend_engineer
effort: medium
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /codex/06-coding-standards/integration-testing-layers.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    unified-api-contracts/scripts/generate_venue_work_list.py,
  ]
source: >-
  Forked from `venue_e2e_wiring_2026_08_16.md`'s "Fork per-asset-group dispatch batches" P0 todo, 2026-08-16
  interactive session, per the operator-selected "per contract-step-group" decomposition.
---

# defi venue e2e wiring batch 1 — 2026-08-16

> **Parent**: [`/plans/active/venue_e2e_wiring_2026_08_16.md`](/plans/active/venue_e2e_wiring_2026_08_16.md) (W4).
> The contract steps this plan walks, and the hard rules it must not violate, live in the parent — not restated here.
> Row list: `unified-api-contracts/scripts/generate_venue_work_list.py --csv PATH` filtered to `asset_group=defi`.

## Todos

- [x] ✅ [BACKEND] P0. **Steps 1-5 per unit — done 2026-08-16.** SHIPPED — `unified-trading-pm@285cefec7a`.
      4 parallel research passes, scoped by shared architecture (135 real defi venues, not 192 — see the
      correction below) since exhaustive per-venue checking isn't tractable at this scale.
      **Scope correction**: defi's real venue universe is `ALL_DEFI_VENUES` = **135** unique protocol-chain venues
      (measured), not the 192 cross-AG total this batch's own frontmatter cited — that 192 figure was always the
      whole-corpus denominator across every asset_group, not defi-specific; fixing the mislabel here rather than
      letting it propagate further.
      **Step 2 (instrument resolution) — 105/135 (≈78%) have a real `VENUE_TO_ADAPTER_KEY` entry**, stricter than
      the 127/135 capability-declaration figure already tracked. Beyond the already-tracked 8-venue gap, **22 NEW
      venues** are capability-declared but have no resolvable adapter mapping at all — new gap todo below.
      **Steps 3-4 (batch/live) — batch is broad** (50 protocol×chain subgraph deployments + RPC/REST for
      oracle_prices, ~121 venue keys via shared per-data-type handlers). **Live coverage is only ~13%** (16 real
      connectors vs. ~121 batch-covered venues; `oracle_prices`, the biggest data_type at 49 venues, has ZERO live
      connectors) — architecturally honest (`NotImplementedError` scaffolds, not faked), and **already tracked**
      in `defi_live_poller_phased_build_2026_08_15.md`/`cross_ag_live_capture_parity_2026_08_14.md`, cited not
      duplicated.
      **Step 5 (feature consumption, checked for the 6 biggest data_types = 170/200 rows) — only 2/6 clean PASS**
      (`lending_indices`, `lst_rates` — the archetype family defi was originally built around). Found a genuinely
      new structural bug: features-service's onchain dispatch (`FEATURE_GROUPS`, a closed 13-name enumeration in
      `onchain/cli/parser.py`) is NARROWER than its calculator registry — `oracle_prices` and `dex_pool_state` each
      have a real, implemented calculator that's simply unreachable (not wired into the dispatch if/elif chain).
      `dex_pool_swaps`/`staking_yields` have no consumer implementation at all — genuinely unimplemented, not just
      unwired. 2 new gap todos below (dispatch-table gap; missing-implementation gap).
- [x] ✅ [BACKEND] P1. **Gap: 22 defi venues are capability-declared but have no resolvable
      `VENUE_TO_ADAPTER_KEY` entry — done 2026-08-16, all 22 already carry a cited reason, no code needed.**
      This todo's own premise was checked against the wrong file: the earlier steps-1-5 sweep read only
      `venue_adapter_keys.py` (the resolved-adapter registry) and never cross-referenced
      `unified-api-contracts/unified_api_contracts/registry/defi_venues.py`'s `DEFI_VENUE_PHASE` dict, where
      every one of the 22 already carries an explicit `"pipeline"` classification under a section-header
      comment naming the reason — verified by reading each entry's surrounding comment directly, not inferred:
      - `ACROSS-ETHEREUM`/`STARGATE-ETHEREUM`/`FLASHBOTS-ETHEREUM`/`ALCHEMY-ONCHAIN`/`COMPOUND-ETHEREUM`/
        `UNISWAP-ETHEREUM` — NOT "zero adapter class" or "legacy aliases" as originally characterized; they're
        governance/MEV/bridge/gas-oracle analytics venues under "Pipeline (Ethereum analytics / governance /
        MEV — NOT IS-producible)" / "Pipeline (Alchemy multi-chain gas-fee oracles — NOT IS-producible)".
        `defi_venues.py`'s own `DEFI_VENUE_MTDS_ADAPTER_VERIFIED_NOT_YET_SCHEDULED` docstring additionally cites
        per-venue MTDS-side evidence for `ALCHEMY`/`FLASHBOTS`/`ACROSS`/`STARGATE`: "STILL-BROKEN: crash-looping
        cron or never scheduled at all, two with no SchemaContract registered" (2026-07-22 design doc).
      - `METEORA-SOLANA`/`LIFINITY-SOLANA`/`PHOENIX-SOLANA` — already cited in `venue_adapter_keys.py` itself
        (measurably dead upstreams, 404/522/NXDOMAIN, re-verified 2026-07-22).
      - `AAVE_V3-{SCROLL,ZKSYNC}`, `COMPOUND_V3-SCROLL` — "Pipeline (Scroll / zkSync — NOT IS-producible)".
      - `COMPOUND_V3-POLYGON` — "Pipeline (Polygon — NOT IS-producible)"; `venue_adapter_keys.py`'s own
        `SUBGRAPH_IDS["compound_v3"]` additionally notes "subgraph returns 0 markets (Compound V3 not active on
        Polygon)".
      - `MORPHO-ARBITRUM` — checked most carefully since `venue_adapter_keys.py`'s own comment reads as if this
        should be live ("ARBITRUM now has real major-asset liquidity... wired into morpho_adapter.py's
        `_CHAIN_ID_BY_CHAIN`"); `defi_venues.py` has the newer, more specific ruling: "not in IS-producible set
        despite having rows (not in `_build_defi_venues()`)" — deliberately still pipeline. Did NOT add an
        explicit key entry here on the strength of the older comment alone; the newer citation governs.
      - `MORPHO-OPTIMISM`/`MORPHO-POLYGON`, `YEARN_V3-OPTIMISM`, `PANCAKESWAP_V3-ARBITRUM` — each under its own
        "Pipeline (... — NOT IS-producible)" section header.
      - `MORPHOVAULTS-ETHEREUM`/`FRAX-ETHEREUM` — "Pipeline (Ethereum vaults / analytics — NOT IS-producible)";
        `FRAX` additionally has the same MTDS-side "stopped dead 2026-06-21, no scheduler" citation as the
        analytics group above.
      - `BEEFY-POLYGON`/`IDLE-POLYGON` — "Pipeline (Polygon catalogue Phase 1A, slot 5 2026-05-11)".
      No `VENUE_TO_ADAPTER_KEY` / `DEFI_VENUE_PHASE` edits made — every branch of the done-when ("real entry OR
      confirmed intentionally excluded with a cited reason") already resolves to the second branch, and writing
      speculative adapter code or forcing a phase flip against these citations would contradict already-ruled
      decisions, not close a gap.
- [ ] [BACKEND] P1. **Gap: features-service's onchain dispatch table is narrower than its calculator registry** —
      `oracle_prices` (`chainlink_peg_deviation_calculator.py`) and `dex_pool_state`
      (`concentrated_liquidity_il_realised_calculator.py`, `pool_invariant_drift_calculator.py`) all have real,
      registered implementations that are simply absent from `onchain/cli/parser.py`'s `FEATURE_GROUPS`/
      `engine/orchestrator.py`'s dispatch if/elif chain — a mechanical wiring gap, not missing engineering work.
      Done-when: all 3 calculators are reachable via the dispatch path and produce real output for at least one
      defi venue.
- [ ] [BACKEND] P2. **Gap: `dex_pool_swaps` and `staking_yields` have no feature_group consumer at all** — unlike
      the dispatch-table gap above, these are genuinely unimplemented (no calculator reads `dex_pool_swaps`
      anywhere; `staking_yields`'s only near-match, `lst_staking_calculator.py`, is an unrelated live DefiLlama
      pull that bypasses the manifest and also isn't dispatched). Done-when: a real implementation exists and is
      wired, or the gap is confirmed intentional with a cited reason.
- [ ] [BACKEND] P0. **Steps 6-8 per unit — strategy and execution**, across the same 200 rows. **Gated by the
      step-5 result above**: only `lending_indices`/`lst_rates` rows (the archetype family defi was originally
      built around) have real feature output today; `oracle_prices`/`dex_pool_state` rows stay `BLOCKED-ON` the
      dispatch-table gap todo above, `dex_pool_swaps`/`staking_yields` rows stay `BLOCKED-ON` the missing-
      implementation gap todo above. Scope this todo to the `lending_indices`/`lst_rates` rows first: does a
      position adapter resolve in batch/live/paper; are these venues declared in the archetype/slot catalogues
      for `CARRY_STAKED_BASIS`/`CARRY_STAKED_BASIS_DATED`/`CARRY_RECURSIVE_STAKED`/`YIELD_STAKING_SIMPLE`/
      `YIELD_ROTATION_LENDING`; does an execution adaptor handle every `InstructionActionV2` those archetypes
      emit — verify real routing per the prediction/tradfi batches' methodology, not just a declared mapping.
      Done-when: a real per-row verdict for those rows, plus `BLOCKED-ON` markers for the rest.
- [x] ✅ [BACKEND] P0. **Step 9 per unit — done 2026-08-16, 1 major finding escalated as MORE urgent than the
      cefi sibling.** SHIPPED — `unified-trading-pm@285cefec7a`. Transfer routing is generic/chain-scoped, not
      per-protocol — `classify_transfer_type` routes purely on wallet type + custody_provider, the specific
      protocol (Aave/Uniswap/Lido/...) never enters the transfer path.
      **Major finding, escalated to a dedicated P0 issue doc + the operator directly**:
      [defi_cloud_kms_silent_wrong_chain_id_fallback_2026_08_16](/plans/active/issues/defi_cloud_kms_silent_wrong_chain_id_fallback_2026_08_16.md)
      — `CloudKmsCustodyProvider._resolve_chain_id()` (the real, provisioned May-23-cutover default custody
      surface) silently resolves an unmapped chain (LINEA/PLASMA/SCROLL/ZKSYNC) to `chain_id=1` (Ethereum)
      instead of failing loud like UAC's own canonical resolver does. **Confirmed REACHABLE-BUT-GATED, not dead
      code** — unlike the cefi CCXT-withdraw stub: the custody provider is genuinely constructed with real
      HSM-backed keys, and `AAVE_V3-LINEA` is already wired end-to-end elsewhere in execution-service and marked
      `"live"`. Zero fail-loud guard exists upstream. The only remaining gates (system-wide pre-live-trading
      status, live `wallet_provisioning.json` content) are not fully verifiable from a repo checkout — the issue
      doc's first todo is checking that live config, since it determines real urgency.
      **Copper custody path confirmed clean** — chain-agnostic by design (passes `chain` as an opaque string),
      real non-stub `create_transfer` calls, covers ASTER/HYPERLIQUID/LIGHTER-ZKSYNC/POLYMARKET-PERP already
      confirmed in the cefi batch.
- [x] ✅ [BACKEND] P1. **Record every gap found — done 2026-08-16.** 6 genuinely new gaps tracked across steps
      1-5 and 9 (22 unresolved venues, the dispatch-table-narrower bug, the 2 unimplemented data_types, and the
      cloud_kms chain-id issue doc); 2 apparent gaps (the ~13% live-connector coverage, the already-tracked
      8-venue capability gap) confirmed already tracked elsewhere, not duplicated.
- [x] ✅ [BACKEND] P0. **Confirm the parent plan's hard rules held — done 2026-08-16, trivially satisfied.** This
      batch's steps 1-5 and step 9 sweep was investigation/documentation only — zero code was changed in any
      touched repo (the 2 new issue docs are plan-corpus docs, not code changes).

## Progress Log

**2026-08-16 — full contract sweep done, 1 escalated finding MORE urgent than cefi's, 6 new gaps total.**
SHIPPED — `unified-trading-pm@285cefec7a`. 4 parallel research passes plus a dedicated reachability check.
Scope-corrected the batch's own denominator (135 real defi venues, not the 192 cross-AG total this doc originally
cited). Instrument resolution: 105/135 real (22 new gap venues beyond the already-tracked 8). Live capture is
only ~13% of batch coverage — large but already tracked elsewhere, not duplicated. Feature consumption: only
`lending_indices`/`lst_rates` (the original archetype family) are genuinely wired; found a real dispatch-table-
narrower-than-registry bug affecting `oracle_prices`/`dex_pool_state`, and confirmed `dex_pool_swaps`/
`staking_yields` have no implementation at all. The most serious finding: `CloudKmsCustodyProvider` silently
resolves an unmapped chain to `chain_id=1` instead of failing loud — confirmed REACHABLE-BUT-GATED (not dead
code, unlike the cefi sibling), with a real provisioned custody path and `AAVE_V3-LINEA` already live-wired
elsewhere in execution-service. Escalated to a dedicated P0 issue doc + the operator directly.

**2026-08-16 — slot 12: dispatched onto this same "Steps 1-5" scope after it had already landed; shipped a
complementary structural cross-check instead of duplicating.** SHIPPED — `unified-api-contracts@5770b51a72`
(`scripts/verify_defi_venue_e2e_steps1_5.py`, permanent/re-runnable). By the time this session's `/boot` resolved,
todo #1 above (`unified-trading-pm@285cefec7a`) had already shipped a more thorough, registry-grounded sweep — not
duplicating it. The new script instead runs a different, cheaper, FILE-PRESENCE-based structural check per defi
row (200 rows, reused verbatim from `generate_venue_work_list.py`): does an `instruments-service` adapter file
exist matching the venue (step 2), does an MTDS handler file reference both the venue and data_type tokens (step
3, manifest reconciliation explicitly NOT live-checked), does a `live/connectors/*_ws.py` file match the venue
(step 4, distinguishing real adapters from declared `_scaffold_ws.py` stubs), does any UAC
`FEATURE_REQUIRED_INPUTS` entry declare the data_type for a defi feature_group (step 5). Measured this run: step2
170/200 PASS; step3 54 PASS / 29 PARTIAL / 117 FAIL; step4 19 PASS / 181 FAIL; step5 59 PASS / 141 NONE. Broadly
consistent with the peer sweep's headline numbers (adapter/live-coverage gaps large, feature consumption narrow)
via an independent method (filename/text presence vs. `VENUE_TO_ADAPTER_KEY` registry lookup) — a useful standing
cross-check for future re-runs of this batch, not a substitute for the registry-grounded analysis already landed.
No new gap todos added from this run: its FAIL/NONE counts are structurally consistent with the already-tracked
gaps above (the 22-venue adapter gap, the ~13% live coverage, the narrow feature dispatch) rather than revealing a
distinct defect class.

**2026-08-16 — 22-venue adapter gap resolved, all already cited, zero code changes needed.** Investigated the
"22 defi venues... no resolvable `VENUE_TO_ADAPTER_KEY` entry" P1 gap todo by reading `defi_venues.py`'s
`DEFI_VENUE_PHASE` dict (not just `venue_adapter_keys.py`, which is what the originating sweep checked). Every
one of the 22 already carries an explicit `"pipeline"` classification under a section-comment reason there —
governance/MEV/bridge/gas-oracle analytics (not IS-producible by architecture), dead/low-liquidity/inactive
subgraphs, or staged Phase-1A rollout. Full per-venue citation list in the flipped todo below. One near-miss
worth flagging for future readers: `MORPHO-ARBITRUM`'s comment in `venue_adapter_keys.py` reads as if it should
already be live (real liquidity, wired into the adapter's chain map) — `defi_venues.py` carries the newer,
overriding citation ("not in IS-producible set despite having rows"). Deferred to the newer source rather than
adding a key on the older comment's strength alone. No code shipped (correctly — the gap resolves via the
already-cited-reason branch of the done-when, not a code fix); this batch's own hard-rule confirmation todo above
already established zero code changes for steps 1-5/9, and this todo continues that pattern.
