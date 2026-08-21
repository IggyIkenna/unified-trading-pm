---
doc_type: plan
title: Platform-external-API walkthrough — 2026-08-21 operator feedback remediation
summary: >-
  Executes the operator's 2026-08-21 feedback on platform-external-api-walkthrough.html. Carries the verified
  registry (T1), execution/transfer (T4) and presentation (T5) feedback clusters that could not be appended to the
  over-line-cap tranche plans, plus the ready-to-paste local worktree dispatch prompts. The refdata (T2) and
  strategy (T3) clusters live directly in their tranche plans. Every claim here was re-verified against repo HEAD
  2026-08-21 before being turned into a todo.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, execution-service, strategy-service, unified-trading-pm]
scope: [engineer]
tags: [code-readiness, walkthrough, client-artefact, feedback, registry, execution, presentation]
related:
  [
    /plans/active/code_readiness_t1_contracts_library_externalapi_2026_08_19.md,
    /plans/active/code_readiness_t2_refdata_marketdata_2026_08_19.md,
    /plans/active/code_readiness_t3_features_ml_strategy_2026_08_19.md,
    /plans/active/code_readiness_t4_execution_settlement_2026_08_19.md,
    /plans/active/code_readiness_t5_readiness_observability_presentations_2026_08_19.md,
  ]
created: 2026-08-21
last_updated: 2026-08-21
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 5
locked_by:
locked_since:
context_scope:
  [
    /plans/active/code_readiness_five_agent_coordinator_2026_08_19.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/06-coding-standards/quality-gates.md,
    unified-api-contracts/unified_api_contracts/registry/,
    execution-service/execution_service/,
  ]
supersedes:
superseded_by:
depends_on: [code_readiness_t1_contracts_library_externalapi_2026_08_19]
source: >-
  Operator feedback session 2026-08-21 on
  codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html — claims re-verified against
  repo HEAD by three parallel investigation agents before todo conversion.
assigned_role: backend_engineer
effort: high
drift_direction: advance-code
---

# Walkthrough feedback remediation — 2026-08-21

> Execution order: registry cluster (T1 scope) and execution cluster (T4 scope) and strategy/refdata clusters
> (in-plan on T3/T2) run CONCURRENTLY in separate worktrees — different repos, no shared files. The presentation
> cluster (T5 scope) runs LAST, after the others land, so the artefact shows fixed reality. Then the re-audit.
> Operator rulings recorded 2026-08-21: (1) ALCHEMY-ONCHAIN is NOT a venue — it is a protocol/data-source (e.g.
> on-chain gas fees); (2) where multiple code paths exist, consolidate onto the SSOT/better version — the more
> configurable, higher-functionality, strategy/venue-AGNOSTIC one.

## Todos — registry cluster (T1 scope: unified-api-contracts)

- [ ] [BACKEND] P0. Bucket the 23 real declared-but-unbucketed venues into `VENUES_BY_ASSET_GROUP["defi"]`
      (AAVE_V3-SCROLL, AAVE_V3-ZKSYNC, COMPOUND-ETHEREUM, COMPOUND_V3-POLYGON, COMPOUND_V3-SCROLL,
      EULER_V2-ARBITRUM, MORPHO-{ARBITRUM,OPTIMISM,POLYGON}, MORPHOVAULTS-ETHEREUM, FRAX-ETHEREUM,
      IDLE-{ARBITRUM,POLYGON}, YEARN_V3-OPTIMISM, BEEFY-POLYGON, UNISWAP-ETHEREUM, PANCAKESWAP_V3-ARBITRUM,
      STARGATE-ETHEREUM, ACROSS-ETHEREUM, FLASHBOTS-ETHEREUM, LIFINITY-SOLANA, METEORA-SOLANA, PHOENIX-SOLANA).
      ALCHEMY-ONCHAIN — operator ruling 2026-08-21: NOT a venue, it is a protocol/data-source (e.g. on-chain gas
      fees) — remove it from `VENUE_DATA_TYPE_CAPABILITIES` as a venue token and re-home its capability under a
      data-source registry, do NOT bucket it. Closes the declared(201)-vs-bucketed(177) gap the walkthrough
      discloses as 192-vs-177 (count drifted +9 since its 2026-08-19 measurement). Source:
      `market_data_categories.py:2644` (dict), `:387` (buckets).
- [ ] [BACKEND] P1. Converge the three DeFi venue sets to one coherent story: dedup `ALL_DEFI_VENUES`
      (`defi_venues.py:32` — 174 entries, 35 exact duplicates, 139 unique) and prune-or-capability the 18
      identities with no capability row (incl. the deliberately-cefi-reclassified CLOBs — annotate as
      cross-referenced, not missing). Target: 139/121/103 becomes explainable in one sentence per set, or the
      sets converge.
- [ ] [BACKEND] P2. `VENUE_CHAIN_MAP` (`venue_constants.py:907`) — verified 2026-08-21: zero consumers outside
      UAC itself (wallet-grouping only, derives `SHARED_WALLET_GROUPS`). Either complete it for every DeFi venue
      with a shared-wallet chain or rename/docstring it so it can never be mistaken for chain-coverage truth.
- [ ] [BACKEND] P1. Delete the deprecated third prediction grouping axis: migrate `PredictionMarketCategory`
      consumers (`_mvp_scope_rules.py`, `predictions/cross_venue_mapping.py`,
      `internal/schemas/_prediction_market_taxonomy.py`) onto `CanonicalQuestionGroup` +
      `two_axis.PredictionUnderlying`, then delete the legacy singular `canonical/domain/prediction/` package
      and its re-exports. Manifest supersession flagged to T2 (no-migration scope here).
- [ ] [BACKEND] P0. Resolve ALL 12 unresolved (venue, data_type) pairs from `venue_instrument_type_triples()`
      (enumerated live 2026-08-21; 678 triples total now, walkthrough says 660/12): AAVE-PLASMA/lending_indices,
      BINANCE-FUTURES/futures_chain, BYBIT/futures_chain, COINBASE-ETHEREUM/oracle_prices,
      DERIBIT/futures_chain, DERIBIT/options_chain, FRAX-ETHEREUM/vault_share_price, FRED/ohlcv_1d,
      FRED/yield_curve, JUPITER-SOLANA/dex_pool_swaps, MORPHOVAULTS-ETHEREUM/vault_share_price,
      SOLANA-NATIVE-SOLANA/lst_rates. Fix pattern per pair: venue-specific roster override where the capability
      is real (Era-B: chains are instrument_types whose data_type is `trades`), or relabel/retire the stale
      pre-Era-B RAW-dict key — BINANCE-FUTURES's dated quarterlies map to leaf `future`, not a chain bundle.
      Then the walkthrough's "12 unresolved, disclosed" line is deleted, not softened.
- [ ] [BACKEND] P1. Fix the CeFi instrument_type roster over-fan: ASTER (perp-only per the registry's own
      comment at `market_data_categories.py:2114`) shows Futures-chain/Options-chain buckets in the artefact
      because `venue_instrument_type_axis.py`'s CeFi path probes the full asset-group roster with no venue-level
      chain exclusion (the module docstring names exactly this failure mode; DeFi/sports already have the
      narrowing). Add the chain-instrument_type gate restricting futures_chain/options_chain candidacy to real
      chain-bundle venues (DERIBIT for cefi; CME/ICE/CBOE for tradfi).
- [ ] [BACKEND] P0. Fix `unified_api_contracts.execution.get_venue_asset_group()` silently returning "cefi" for
      every venue its lookup misses (P0 issue filed 2026-08-19) — fail loud or resolve via
      `VENUES_BY_ASSET_GROUP`.
- [ ] [DOC→T5 handoff] P1. Stale-claims note for the artefact re-derive: Plasma IS a `ChainKind` member since
      unified-api-contracts@27ebc544b (2026-08-19) and PACIFICA-SOLANA has a full capability row since
      @88cd9f912 (2026-08-20, cefi bucket per 2026-08-14 operator ruling); `ChainKind.BITCOIN` exists with
      non-EVM sentinel chain-id 0 in `MAINNET_CHAIN_IDS`. Replace the walkthrough's "registry gap" callouts for
      these with the fixed reality.

## Todos — execution/transfer cluster (T4 scope: execution-service)

- [ ] [BACKEND] P0. Converge the two transfer dispatch paths. `transfer_coordinator.py` (legacy: only
      SUBACCOUNT_MOVE wired, Binance/OKX only, CEX_WITHDRAW docstring says NOT WIRED) vs
      `engine/handlers/transfer_handler.py` (real path: all 5 BusTransferTypes wired — SUBACCOUNT_MOVE,
      CEX_WITHDRAW via live CCXT `withdraw()`, ON_CHAIN, CUSTODY_TRANSFER via Copper/Ceffu/CloudKMS; BRIDGE is
      a fail-loud stub). Operator ruling 2026-08-21: consolidate onto the SSOT/better version — the more
      configurable, higher-functionality, strategy/venue-AGNOSTIC one (here: `TransferHandler`); delete the
      legacy coordinator per no-shims and migrate its callers. Extend SUBACCOUNT_MOVE beyond Binance/OKX where
      venue support exists. The walkthrough's "Wired versus specified" table then collapses to reality.
- [ ] [BACKEND] P1. Build the two genuinely-missing rails: REBALANCE as a real transfer rail (new UAC
      `BusTransferType` member + handler — today only an IntentType/OrderPriority in unrelated modules) and gas
      top-up / gas-floor maintenance (zero hits in execution-service; new handler + UAC schema field).
- [ ] [BACKEND] P1. Manual trade — second booking path. Operator ruling 2026-08-21: manual trading gets TWO
      options — (a) book into the system as normal; (b) book a trade that is persisted + FCA-audited
      (`ManualInstructionAuditLog` already exists) but flagged EXCLUDED from standard reconciliation (exchange
      outages, OTC/not-yet-cleared trades). No recon-exclusion flag exists today in `manual_schemas.py` or
      batch-live-reconciliation-service — add the flag end to end (schema → handler → recon ledger-matching
      skip + audit trail). Then T5 rewrites "WHY RECONCILIATION PAUSES BEFORE A MANUAL ENTRY" around the two
      paths.
- [ ] [BACKEND] P2. ICEBERG has no `ExecAlgorithm` implementation class (manual-menu-only,
      `manual_instruction_helpers.py:74`); ghost algos SEQUENTIAL_LEGS/SPREAD_ROLL/BEST_PRICE/KELLY_STAKE are
      declared with no impl (fail-loud). Implement or explicitly present as in-development — decide per algo,
      make selector and docs agree. Real registry for T5: TWAP, VWAP, ADAPTIVE_TWAP, ALMGREN_CHRISS,
      POV_DYNAMIC, HYBRID_OPTIMAL, PASSIVE_AGGRESSIVE_HYBRID, BENCHMARK_FILL + SOR/SOR_TWAP/SWAP_TWAP.
- [ ] [DOC→T5 handoff] P1. Corrections for the artefact re-derive: custody is NOT "genuinely absent" —
      `execution_service/custody/` is a full provider-protocol module (Copper production MPC, CloudKMS default,
      Ceffu stub pending Binance institutional API spec) with per-venue withdrawal eligibility via
      `get_venue_wallet_capabilities()`; the external execution API exists both ways (REST
      `POST /external/instructions` taking `StrategyInstructionV2`, and Pub/Sub via the UTL EventTransport
      facade with the same UAC envelope) — author real request/response examples from these;
      `execution_service/readiness/instruction_path.py` is real and runnable.

## Todos — presentation cluster (T5 scope: the artefact itself; run AFTER the clusters above land)

- [ ] [DOC] P0. Sticky left-hand TOC sidebar: contents pinned left, scroll-spy highlighting the current
      section, click-to-jump. Wide content keeps its own overflow scroll.
- [ ] [DOC] P0. Voice pass — remove internal-audit framing: every "Verified directly:" → "Source:"; delete
      correction narratives (16-chain grep-artefact story, one-day-fresher re-run block, "TWO DIFFERENT
      HOW-MANY QUESTIONS" block, "DEFI REFRESHED — why the split moved" block, "12 unresolved, disclosed",
      VENUE_CHAIN_MAP defect callout, Unattributed tree section) once their underlying fixes land; replace with
      the single clean number/story. Client-facing "not ready" → "coming soon" (KALSHI perp: "Coming Soon",
      application-gated; market perp: "Coming Soon", API in beta, not officially launched). Remove the plan-doc
      reference in the reference-position/credit section (describe capability, cite no plan files).
- [ ] [DOC] P0. Request/response examples for EVERY named endpoint: external instruction API (REST
      `POST /external/instructions` with a real `StrategyInstructionV2` payload + response, and the Pub/Sub
      EventTransport variant), cancel path, strategy wizard endpoint (once T3 ships it), hot-config-reload
      pattern, coverage/data retrieval, transfers. Strategy instruction envelope re-formatted as a bunched
      endpoint-call example, not prose. Protocols + parameters explicit throughout.
- [ ] [DOC] P1. Content additions: parquet rationale (typed + compressed; open to other formats/flat CSV);
      shard schemas list ALL data types' schemas plainly (no "pending"), colour distinction type vs column;
      "declared since: not declared" legend note (live-only capability, no batch start date — not "not real");
      execution section adds a 4th path (treasury management: wallet transfers, settlements, DeFi
      lend/borrow/stake) + full algo list from the T4 handoff + "and select proprietary algos to capture alpha
      vs basic execution"; PnL attribution enumerates real dimensions (delta/gamma/theta/vega/rho, funding,
      basis, interest_rate, carry, fx, staking once T3 lands it, residual); readiness section adds the
      batch→paper→live promote line, same code paths/real symmetry; collateral/cross-margining reframed as a
      feature (automated in-strategy OR full external-interface control, limited only by on-chain capability);
      manual trade reframed as two booking options (standard vs audited recon-excluded, per T4); security
      section expanded (custody providers Copper/Ceffu/CloudKMS, wallet signing, GCP service accounts, external
      auth); fees & gas by component states HOW it is exposed (parameter / API request / reference data);
      measured-vs-projected uses smoke-test results for obtainable coverage; venue-error-handling specificity
      extended to every section; strategy-instructions section completed + linked to per-instrument breakdowns
      of venues/instrument types/shared dimensions; complete "The external execution API — two ways to run it"
      and the shard-level coverage drilldown.
- [ ] [DOC] P0. Full naming-consistency audit across the artefact: everything named anywhere appears everywhere
      relevant (venues, instrument types, data types, dimensions cross-referenced); every number re-derived
      same-day at one stated grain after the upstream fixes; TradFi "90% coverage but drill-down not-ready"
      contradiction resolved by explaining/fixing the strict all-or-nothing venue verdict vs volume-weighted
      percentage; prediction markets split by canonical groupings (CanonicalQuestionGroup, post-registry
      cleanup).
- [ ] [BACKEND] P1. Build the archetype-readiness capability audit (operator feedback: "READINESS APPLIES TO
      ARCHETYPES AS WELL AS VENUES" — specified, not built). Derive per-(archetype, venue, mode) readiness from
      each archetype's declared FEATURE_REQUIRED_INPUTS against the venue's satisfiable inputs, across batch/
      paper/live, so that axis stops reporting blanket unverified. Reuses the readiness-dump strategy-leg check;
      output joins the per-venue 8-leg model.
- [ ] [AGENT] P0. Re-audit: after all clusters land, re-run `venue_instrument_type_triples()`,
      `derive_readiness.py` and the coverage dump; confirm 0 unresolved pairs, 0 unbucketed venues, and refresh
      every number in the artefact from those runs. Get some venues to genuinely ready so the readiness tree is
      not all "coming soon". The re-audit is GATED on the two active data-side degraders the artefact names:
      the path-canonicalisation CASING writer regression (grew 13x — T2 owns the canonicalisation code) and the
      prediction-capture outage — confirm both fixed (or explicitly carve them out with a dated note) before
      republishing coverage numbers.

## Sibling clusters (in-plan on their tranches — do not duplicate here)

- Refdata cluster (Kalshi perp scaffold, sports bookmaker classification, unattributed-token attribution code,
  bitcoin-chain connectors): `/plans/active/code_readiness_t2_refdata_marketdata_2026_08_19.md`
  § "Walkthrough feedback 2026-08-21".
- Strategy cluster (wizard external endpoint P0, staking_pnl dimension):
  `/plans/active/code_readiness_t3_features_ml_strategy_2026_08_19.md` § "Walkthrough feedback 2026-08-21".

## Dispatch prompts — local worktrees (paste one per Claude session)

Each prompt targets a different repo, so all of wave 1 can run concurrently (≤5 agents; gate+ship stay serial per
host-concurrency rules). Presentation prompt runs only after wave 1 lands.

**Wave 1a — registry (unified-api-contracts):**
"Work /plans/active/walkthrough_feedback_remediation_2026_08_21.md § 'Todos — registry cluster' in
unified-api-contracts. Read the plan section in full first, then each cited source file. Standard workspace rules:
QG-green before commit via `bash scripts/quality-gates.sh`, ship via quickmerge with --files, flip each checkbox
with repo@sha evidence in the same turn."

**Wave 1b — execution (execution-service):**
"Work /plans/active/walkthrough_feedback_remediation_2026_08_21.md § 'Todos — execution/transfer cluster' in
execution-service. The transfer-path consolidation ruling is in the plan header. Same ship rules as above."

**Wave 1c — strategy (strategy-service + deployment-api):**
"Work /plans/active/code_readiness_t3_features_ml_strategy_2026_08_19.md § 'Walkthrough feedback 2026-08-21 —
strategy cluster'. Same ship rules."

**Wave 1d — refdata (market-tick-data-service + instruments-service):**
"Work /plans/active/code_readiness_t2_refdata_marketdata_2026_08_19.md § 'Walkthrough feedback 2026-08-21 —
refdata/coverage cluster'. Same ship rules."

**Wave 2 — presentation (unified-trading-pm, after wave 1):**
"Work /plans/active/walkthrough_feedback_remediation_2026_08_21.md § 'Todos — presentation cluster' on
codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html. Re-derive every number from a
fresh same-day run; then the re-audit todo."

## Progress Log

- 2026-08-21 — Plan created from operator feedback session; every claim re-verified against repo HEAD by three
  parallel investigation agents (registry, venue-cell, execution clusters) before todo conversion. T1/T4/T5
  tranche plans are over the 1000-line hard cap, so their clusters live here with pointer todos there.
