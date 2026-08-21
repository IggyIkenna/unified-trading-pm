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
      **BLOCKED — premise stale, needs operator ruling 2026-08-21**: `VENUES_BY_ASSET_GROUP["defi"]` is not a
      literal list to append to — it's DERIVED (`list(dict.fromkeys(v for v in _ALL_DEFI_VENUES if
      _DEFI_VENUE_PHASE.get(v) == "live"))`, `market_data_categories.py` ~line 528). All 20 of the 23 named
      venues checked (AAVE_V3-SCROLL, AAVE_V3-ZKSYNC, COMPOUND-ETHEREUM, COMPOUND_V3-POLYGON,
      COMPOUND_V3-SCROLL, EULER_V2-ARBITRUM, MORPHO-ARBITRUM, MORPHOVAULTS-ETHEREUM, FRAX-ETHEREUM,
      IDLE-ARBITRUM, YEARN_V3-OPTIMISM, BEEFY-POLYGON, UNISWAP-ETHEREUM, PANCAKESWAP_V3-ARBITRUM,
      STARGATE-ETHEREUM, ACROSS-ETHEREUM, FLASHBOTS-ETHEREUM, LIFINITY-SOLANA, METEORA-SOLANA,
      PHOENIX-SOLANA — `defi_venues.py`) are already declared with `_DEFI_VENUE_PHASE == "pipeline"`, i.e.
      deliberately NOT counted "live"/IS-producible yet. "Bucketing" them means flipping pipeline→live, which is
      an IS-producibility/readiness call on 20 real venues, not a registry-hygiene fix — needs an explicit
      operator ruling on which of the 20 are actually ready, or this todo is mis-scoped and should be re-pointed
      at the honest-coverage denominator story instead. Left unflipped pending that ruling. The ALCHEMY-ONCHAIN
      re-home sub-item is separately scoped and equally not started in this pass (same blocker: budget).
- [ ] [BACKEND] P1. Converge the three DeFi venue sets to one coherent story: dedup `ALL_DEFI_VENUES`
      (`defi_venues.py:32` — 174 entries, 35 exact duplicates, 139 unique) and prune-or-capability the 18
      identities with no capability row (incl. the deliberately-cefi-reclassified CLOBs — annotate as
      cross-referenced, not missing). Target: 139/121/103 becomes explainable in one sentence per set, or the
      sets converge.
      **DEFERRED — not attempted this pass**: budget did not extend to a safe multi-file dedup + capability
      audit across `ALL_DEFI_VENUES`/`VENUE_DATA_TYPE_CAPABILITIES`/capability declarations; needs its own
      focused pass.
- [x] [BACKEND] P2. `VENUE_CHAIN_MAP` (`venue_constants.py:907`) — verified 2026-08-21: zero consumers outside
      UAC itself (wallet-grouping only, derives `SHARED_WALLET_GROUPS`). Either complete it for every DeFi venue
      with a shared-wallet chain or rename/docstring it so it can never be mistaken for chain-coverage truth. —
      unified-api-contracts@<PENDING-SHA> + evidence: took the low-risk rename+docstring option — added a
      docstring to `VENUE_CHAIN_MAP` and `SHARED_WALLET_GROUPS` in `venue_constants.py` stating it is a
      deliberately-curated wallet-grouping subset, NOT a chain-coverage inventory, and pointing consumers at
      `ALL_DEFI_VENUES`/`ChainKind` instead. No behavior change (dict contents untouched); QG-gated.
- [ ] [BACKEND] P1. Delete the deprecated third prediction grouping axis: migrate `PredictionMarketCategory`
      consumers (`_mvp_scope_rules.py`, `predictions/cross_venue_mapping.py`,
      `internal/schemas/_prediction_market_taxonomy.py`) onto `CanonicalQuestionGroup` +
      `two_axis.PredictionUnderlying`, then delete the legacy singular `canonical/domain/prediction/` package
      and its re-exports. Manifest supersession flagged to T2 (no-migration scope here).
      **DEFERRED — not attempted this pass**: 3-consumer migration + legacy package deletion + whole-repo grep
      for other consumers needs its own focused pass; budget did not extend to it.
- [ ] [BACKEND] P0. Resolve ALL 12 unresolved (venue, data_type) pairs from `venue_instrument_type_triples()`
      (enumerated live 2026-08-21; 678 triples total now, walkthrough says 660/12): AAVE-PLASMA/lending_indices,
      BINANCE-FUTURES/futures_chain, BYBIT/futures_chain, COINBASE-ETHEREUM/oracle_prices,
      DERIBIT/futures_chain, DERIBIT/options_chain, FRAX-ETHEREUM/vault_share_price, FRED/ohlcv_1d,
      FRED/yield_curve, JUPITER-SOLANA/dex_pool_swaps, MORPHOVAULTS-ETHEREUM/vault_share_price,
      SOLANA-NATIVE-SOLANA/lst_rates. Fix pattern per pair: venue-specific roster override where the capability
      is real (Era-B: chains are instrument_types whose data_type is `trades`), or relabel/retire the stale
      pre-Era-B RAW-dict key — BINANCE-FUTURES's dated quarterlies map to leaf `future`, not a chain bundle.
      Then the walkthrough's "12 unresolved, disclosed" line is deleted, not softened.
      **DEFERRED — not attempted this pass**: needs a per-pair fix decision (venue-specific roster override vs.
      relabel/retire stale RAW-dict key) across 12 pairs plus a measured re-run; budget did not extend to it.
- [ ] [BACKEND] P1. Fix the CeFi instrument_type roster over-fan: ASTER (perp-only per the registry's own
      comment at `market_data_categories.py:2114`) shows Futures-chain/Options-chain buckets in the artefact
      because `venue_instrument_type_axis.py`'s CeFi path probes the full asset-group roster with no venue-level
      chain exclusion (the module docstring names exactly this failure mode; DeFi/sports already have the
      narrowing). Add the chain-instrument_type gate restricting futures_chain/options_chain candidacy to real
      chain-bundle venues (DERIBIT for cefi; CME/ICE/CBOE for tradfi).
      **DEFERRED — not attempted this pass**: needs the DeFi/sports narrowing pattern located and mirrored in
      `venue_instrument_type_axis.py`'s CeFi path; budget did not extend to it.
- [x] [BACKEND] P0. Fix `unified_api_contracts.execution.get_venue_asset_group()` silently returning "cefi" for
      every venue its lookup misses (P0 issue filed 2026-08-19) — fail loud or resolve via
      `VENUES_BY_ASSET_GROUP`. — unified-api-contracts@HEAD (no code change needed) + evidence: already fixed.
      `unified_api_contracts/execution.py::get_venue_asset_group()` (lines 57-87) resolves via
      `classify_venue_asset_group()` then the capability-source table, and raises `UnknownVenueAssetGroupError`
      on a genuine miss — it does not default to "cefi". The originating P0 issue doc
      (`uac_get_venue_asset_group_silently_returns_cefi_for_all_venues_2026_08_19.md`) is already archived under
      `plans/archive/2026_08/issues/`, confirming this was resolved before this pass; the walkthrough plan's
      todo text is stale.
- [x] [DOC→T5 handoff] P1. Stale-claims note for the artefact re-derive: Plasma IS a `ChainKind` member since
      unified-api-contracts@27ebc544b (2026-08-19) and PACIFICA-SOLANA has a full capability row since
      @88cd9f912 (2026-08-20, cefi bucket per 2026-08-14 operator ruling, see
      /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md); `ChainKind.BITCOIN` exists with
      non-EVM sentinel chain-id 0 in `MAINNET_CHAIN_IDS`. Replace the walkthrough's "registry gap" callouts for
      these with the fixed reality. — unified-api-contracts@HEAD (verification only, no code change) + evidence:
      all three facts confirmed true 2026-08-21: `git log --oneline --all | grep 27ebc544` →
      `27ebc544 fix(registry): declare ChainKind the chain SSOT and recognise SCROLL/PLASMA venues`;
      `git log --oneline --all | grep 88cd9f91` → `88cd9f91 fix(uac): declare PACIFICA-SOLANA in
      VENUE_DATA_TYPE_CAPABILITIES (readiness/coverage gap)`; `rg -n "BITCOIN" venue_constants.py`... resolved
      via `unified_api_contracts/registry/chain_env.py:33` — `"BITCOIN": 0,  # Not EVM -- handled separately` in
      `MAINNET_CHAIN_IDS`. Facts still hold against repo HEAD — T5 can replace the artefact's "registry gap"
      callouts for these three with the fixed reality.

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

- [x] [DOC] P0. Sticky left-hand TOC sidebar: contents pinned left, scroll-spy highlighting the current
      section, click-to-jump. Wide content keeps its own overflow scroll. — unified-trading-pm@<shipping-sha>.
      Fixed `.toc-sidebar` panel (min-width:1680px) built from the existing in-flow `nav.contents` anchors,
      `IntersectionObserver` scroll-spy, `body{overflow-x:hidden}` guard; existing wide tables/diagrams already
      carry their own `.scroll-x`/`overflow-x` containers (unchanged).
- [ ] [DOC] P0. Voice pass — remove internal-audit framing: every "Verified directly:" → "Source:"; delete
      correction narratives (16-chain grep-artefact story, one-day-fresher re-run block, "TWO DIFFERENT
      HOW-MANY QUESTIONS" block, "DEFI REFRESHED — why the split moved" block, "12 unresolved, disclosed",
      VENUE_CHAIN_MAP defect callout, Unattributed tree section) once their underlying fixes land; replace with
      the single clean number/story. Client-facing "not ready" → "coming soon" (KALSHI perp: "Coming Soon",
      application-gated; market perp: "Coming Soon", API in beta, not officially launched). Remove the plan-doc
      reference in the reference-position/credit section (describe capability, cite no plan files).
      - 2026-08-21 (wave-2-prep lane) — completed the mechanical half only: all 3 literal
        `"Verified directly:"` occurrences → `"Source:"` (lines carrying the exact colon form; the 9
        `"Verified directly against"` citations were left as-is, out of this mechanical pass's scope).
        Correction-narrative blocks, "not ready"→"coming soon", and the plan-doc-reference removal are
        content/wave-1-dependent and were NOT touched — unified-trading-pm@<shipping-sha>.
- [ ] [DOC] P0. Request/response examples for EVERY named endpoint: external instruction API (REST
      `POST /external/instructions` with a real `StrategyInstructionV2` payload + response, and the Pub/Sub
      EventTransport variant), cancel path, strategy wizard endpoint (once T3 ships it), hot-config-reload
      pattern, coverage/data retrieval, transfers. Strategy instruction envelope re-formatted as a bunched
      endpoint-call example, not prose. Protocols + parameters explicit throughout.
      - 2026-08-21 (wave-2-prep lane) — completed only the format-only sub-item: §08 "The instruction
        envelope" now renders as a `POST /external/instructions` JSON-body example (fields unchanged —
        action, instrument, quantity, reference_price, execution_policy_ref, urgency, eligible_venues,
        venue_constraints, reference_position, credit, position_adjustment_bps_per_unit_risk — no fields
        invented). The per-endpoint request/response examples (external instruction API real payload,
        cancel path, wizard endpoint, hot-config-reload, coverage/data retrieval, transfers) are content
        work gated on wave-1 landing and were NOT done — unified-trading-pm@<shipping-sha>.
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
      - 2026-08-21 (wave-2-prep lane) — completed 3 format-only sub-items: (1) §06 "Getting the data" gained a
        "Why parquet" callout (typed + compressed; open to other compression codecs or flat CSV on request);
        (2) §07 "Shard schemas" got a CSS class pass (`.fld` spans + `#s7 .code i`) colour-distinguishing
        column tokens from type tokens on the 4 already-documented schemas (trades/book/candles/funding) — no
        schema content added or removed, the "list ALL data types" half (on-chain/sports/prediction/TradFi) is
        data work, NOT done; (3) header legend gained the "Declared since: not declared" note. Every other
        sub-item in this bundle (execution 4th path, PnL dimensions, readiness promote line, collateral
        reframe, manual-trade reframe, security expansion, fees/gas exposure, measured-vs-projected,
        venue-error extension, strategy-instructions completion, §25/§27 completion) is content work gated on
        wave-1 landing and was NOT done — unified-trading-pm@<shipping-sha>.
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
- 2026-08-21 — T1 registry-cluster pass (unified-api-contracts): flipped 3/8 todos. Shipped VENUE_CHAIN_MAP
  docstring fix (low-risk rename+docstring option, no behavior change). Verified-only, no code needed:
  `get_venue_asset_group()` already fails loud (the cited P0 issue was already resolved and archived before
  this pass — todo text was stale); the T5-handoff stale-claims note (Plasma/PACIFICA-SOLANA/BITCOIN facts all
  confirmed true against HEAD). Todo 1 (venue bucketing) found premise-stale on investigation:
  `VENUES_BY_ASSET_GROUP["defi"]` is DERIVED from `_DEFI_VENUE_PHASE`, not a literal list — all 20 checked
  venues are already declared but deliberately phase="pipeline" (non-live); "bucketing" them is an
  IS-producibility/readiness ruling on 20 real venues, not a registry-hygiene edit, so left BLOCKED pending
  operator input rather than flipped unsafely. Todos 2 (venue-set convergence), 4 (PredictionMarketCategory
  deletion), 5 (12 unresolved triples), 6 (ASTER roster over-fan) each need their own focused multi-file pass —
  left DEFERRED, not silently skipped; see inline blocker notes under each todo.

- **na-eligibility-audit 2026-08-21** (cross-cutting tranche, batch 3/3): KEEP-NA, valid — re-read against current
  HEAD (16 open todos, down from 19 at plan creation via the T1 registry-cluster pass above). Consistent with its
  entire family: all 5 sibling `code_readiness_t1-t5` tranche plans it overflows from are ALSO `assigned_vm: NA`,
  and this doc explicitly carries "Dispatch prompts — local worktrees (paste one per Claude session)" — the
  designed consumption model is an operator pasting per-cluster prompts into manually-launched local interactive
  sessions (the `code_readiness_five_agent_coordinator_2026_08_19.md` pattern), not AO backlog dispatch.
  Reclassifying this one doc out of its whole family would break that choreography (wave 1a-1d parallel / wave 2
  gated after) without a corresponding change to its 5 siblings, which is out of this doc's own scope to decide
  alone. **Note on this pass's own process**: this doc is under heavy concurrent editing (a real T1 pass landed
  between this audit's first read and its ship attempt); the ship script's autostash/quarantine replay briefly
  reverted this file to its pre-audit-session content mid-push (self-inflicted corruption, not a content defect)
  — caught before shipping by re-diffing against a fresh `origin/live-defi-rollout` fetch rather than trusting the
  script's own recovery output, and rebuilt from the current origin content plus only this note appended.
