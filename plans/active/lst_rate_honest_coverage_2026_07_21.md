---
doc_type: plan
title:
  LST rate honest coverage — wire the four exchange-rate surfaces into the pipeline (denominator → collectors →
  canonical → manifest → daily → sample-verified)
summary: >-
  Operator-directed (2026-07-21) build to bring the four LST exchange-rate surfaces to HONEST COVERAGE end-to-end so the
  DeFi interest PnL can sit on real data. #1 CEX spot = a Tardis backfill (denominator already complete — adding pairs
  is a phantom-minting anti-pattern). #3 Aave oracle = the real code build (plumbing: the getAssetPrice RPC exists but
  is dormant — wire a collection branch + venue registration + Chainlink feed adds, verified on-chain first). #2 DEX
  pool = a collector/endpoint fix (dead Graph subgraphs) + reserve→mid derivation. #4 protocol redemption = a features
  backfill + a Solana/LRT join fix. Denominator-first: register verified feeds/venues so gaps read expected_unattempted
  RED before any fill. Then the interest PnL A2 staking leg (#4) + the recursive borrow leg (unblocks on #3).
status: active
nature: process
asset_group: [defi]
stage: [data, strategy]
repos:
  [
    market-tick-data-service,
    instruments-service,
    unified-api-contracts,
    features-service,
    strategy-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [lst, exchange-rate, oracle, dex, honest-coverage, pnl-correctness, defi, data-pipeline]
related:
  [
    lst_exchange_rate_data_availability_2026_07_21.md,
    pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md,
    onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md,
  ]
created: "2026-07-21"
last_updated: "2026-07-21"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 4.8
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source: ["operator dispatch 2026-07-21: build honest LST-rate coverage then wire interest PnL"]
locked_by:
locked_since:
supersedes:
superseded_by:
---

# LST rate honest coverage — plan of record

**Codex SSOT:** `codex/02-data/lst-exchange-rate-surfaces.md` (the four surfaces, canonical homes, honest-coverage
contract). **Audit:** `plans/active/issues/lst_exchange_rate_data_availability_2026_07_21.md`.

**Sequencing invariant (denominator-first):** register a verified feed/venue in the catalogue + expected registries so
every un-captured LST rate renders `expected_unattempted` (honest RED) BEFORE any backfill. Verify on-chain reality
FIRST so no permanent-false-RED cell is seeded. Shard atom identical writer→manifest→IS→gate→UI.

## Phase 0 — Reality verification (read-only / on-chain; no ship) — pins the TRUE denominator

- [x] [ONCHAIN] P0. ✅ **AAVE reserve oracle reality** — `eth_call getAssetPrice` VERIFIED (wf_f629fbb4-7da, real
      returns): **REGISTER 6** — wstETH `0x7f39C581…`=$2393.27, weETH `0xCd5fE23C…`=$2122.85, rETH
      `0xae78736C…`=$2254.42,
      cbETH `0xBe989514…`=$2191.60, rsETH
      `0xA1290d69…`=$2077.76 (AAVE-path-only), ezETH via `0xbf5495Efe5DB9ce00f80364C8B423567e58d2110` ONLY=$2088.92.
      **EXCLUDE** osETH (`getAssetPrice` REVERTS, aToken=0x0 — not a reserve) and ezETH@`0x2416092f…` (REVERTS) → would
      seed permanent-false-RED.
- [x] [EXTERNAL] P0. ✅ **Chainlink aggregator reality** — VERIFIED: add exactly **2 RefPrice feeds** — weETH/ETH
      `0x5c9C449BbC9a6075A2c061dF312a35fd1E05fF22` (dec 18, live 1.0995) + ezETH/ETH
      `0x636A000262F6aA9e1F094ABF0aD8f645C44f641C` (dec 18, live 1.0796). **Do NOT add** rsETH (`0x9d2F2f…` is ExRate,
      not price) or wstETH (only a _Calculated_ USD feed exists — operator decision; wstETH is fully AAVE-covered).
- [x] [MTDS] P0. ✅ **CEX listing reality** — confirmed **NO catalogue edit** (the LST bases are already in
      `CEFI_BASE_ASSET_UNIVERSE`+`STAKING_SPOT_EXCEPTION`; catalogue-add is the documented phantom-mint anti-pattern).
      #1 is a Tardis backfill only. (The per-venue listing sub-check didn't fully complete — verify exact listed
      (LST,venue) cells at backfill time, Phase 5.)
- [x] [MTDS] P0. ✅ **DEX endpoint reality — WORKS TODAY, NOT blocked.** Live-probed 2026-07-21: Curve stETH/ETH pool
      `0xDC24316b9AE028F1497c275EB9192a3Ea0f67022` + Balancer via the EXISTING `thegraph-api-key` secret + shipped
      `dex_swaps_handler` cascade + UAC `SUBGRAPH_IDS` — HTTP 200, hasIndexingErrors:false, at-head, real swaps. The
      codex "decommissioned subgraphs" claim is STALE for these ETH LST endpoints → #2 is a normal collector/backfill
      task, NOT `BLOCKED-CREDENTIALS`. Curve REST (`api.curve.finance`, no key) is a live direct-alternative.

## Phase 1 — Denominator registration (smallest first-shippable; makes gaps HONEST)

- [ ] [UAC][IS] P1. **Chainlink LST feed-map add** (smallest increment) — add the Phase-0-verified feeds to BOTH the
      MTDS `_oracle_prices_constants.py` (dict shape) and IS `chainlink.py` (tuple shape); the mirror-invariant test
      must pass. Auto-mints `(CHAINLINK-ETHEREUM, SPOT_PAIR, oracle_prices)` catalogue rows on the next build. One
      quickmerge per repo.
- [x] [UAC] P1. **AAVE oracle venue registration** — `expected_coverage.py` `AAVE` += `oracle_prices` +
      `AAVE-ETHEREUM: [oracle_prices]`; `defi_venues.py` flip `AAVE-ETHEREUM` phase `pipeline`→`live`;
      `venue_adapter_keys.py` add `AAVE-ETHEREUM: aave_oracle`; `capability_declarations/_defi_oracle_coverage.py`
      coverage-start. Add `aave` to UAC `pipeline_mode_for_source` if absent. — `unified-api-contracts@6bdbc31d`, landed
      on `live-defi-rollout` 2026-07-21; full suite 11,739 passed (0 failures).
- [x] [IS] P1. **AaveOracle reference-data adapter** — `adapters/defi/aave_oracle.py` (clone `chainlink.py`; venue
      `AAVE-ETHEREUM`; enumerate the Phase-0-verified reserves as `spot_asset`); register `aave_oracle` in
      `factory._ADAPTERS` + add `AAVE-ETHEREUM` to `orchestrator/defi.py`. Keep IS phase in lockstep with UAC. —
      `instruments-service@d13fb68d`+`@02e5215b` (2 commits, local, `quality-gates.sh` fully green, sentinel matches
      HEAD) — **quickmerge BLOCKED**, not by anything IS-side: the dirty-deps pre-flight guard refuses because IS's
      path-dependency `unified-trading-library` currently has genuinely LIVE uncommitted WIP (8 files, identical mtime
      ~27s old at check time — well inside the 120s liveness threshold, correctly PROTECTED, not isolated). That same
      WIP also blocks shipping this plan's own already-tested `unified-trading-library` fix (the
      `_VENUE_OVERRIDES["AAVE"]` provenance bug from the Phase-2 entry above) — ship both together the next time UTL's
      working tree is genuinely clear, then retry `instruments-service`'s quickmerge. See "the DEFI dedup count 98→99 is
      UAC-registry-driven, not IS-adapter-driven" note below for why this ship, while blocked, is not itself the long
      pole — Phase 4's daily-download gate is the actual next dependency.
- [x] [IS] P1. **Regenerate catalogue + expected universe** — `build_instrument_catalogue.py` +
      `enumerate_expected_universe.py` (v2); confirm the new `(CHAINLINK-ETHEREUM, SPOT_PAIR, oracle_prices)` +
      `(AAVE, spot_asset, oracle_prices)` cells appear as `expected_unattempted` (honest RED). Verify #1 (CEX) needs no
      edit (no-op). — covered by the adapter registration above
      (`instruments_service_aave_oracle_adapter_registration_test_drift_2026_07_21.md`'s own invariant tests confirm the
      enumeration); same quickmerge-blocked state.

## Phase 2 — Collectors ready to fetch

- [x] [MTDS] P2. **AAVE oracle collection branch** — `_AAVE_ORACLE_ASSETS` in `_oracle_prices_constants.py` +
      `_collect_aave_rows`/`_emit_aave_manifest` in `OraclePricesHandler` (lifts `AavePositionsMixin._ORACLE_ABI` +
      `AAVE_ORACLE_ADDRESS`, does not re-implement; rows carry `source='aave'`, `chain='ETHEREUM'`, `symbol`/`feed`;
      `record_captured/empty/failed`, `instrument_type=spot_asset`; STRICT write contract confirmed). BUILT + 15 new
      unit tests green + adversarially reviewed 2026-07-21 — **held staged, not shipped** (MTDS quality-gates.sh is
      still blocked on the peer-owned `mtds_rule11_shard_count_stale_baseline_2026_07_21.md`, unrelated to this work).
      Review found 2 real bugs, both fixed in the same pass: (1) `_emit_aave_manifest` unconditionally called
      `pipeline_mode_for_source("aave", Mode.LIVE)`, which raises (aave is BATCH-only, no `LIVE_AAVE` member) — the
      already-scheduled 5-min live oracle-prices cron would have crashed the WHOLE handler incl. Chainlink/Pyth; fixed
      by gating the AAVE branch to skip cleanly (never crash) when `_run_tag == "live"`. (2) `write_defi_rows` had no
      `"AAVE"` entry in `unified-trading-library`'s `pipeline_mode_resolver._VENUE_OVERRIDES`, so the actual parquet
      write path mislabeled every AAVE row as `pipeline_mode=batch_pyth_hermes` (SOURCE_PRIORITY's top pick) while the
      manifest correctly said `batch_aave` — fixed by adding the override (mirrors CHAINLINK/PYTH); **this UTL fix is
      itself correct + tested (2 new tests, full 55-test suite green) but ALSO held unshipped** — UTL's working tree has
      heavy unrelated foreign WIP right now and this fix has zero current blast radius (the AAVE collector it protects
      hasn't shipped anywhere yet), so it wasn't worth a risky whole-tree gate for a non-urgent fix; ship alongside the
      MTDS piece once MTDS unblocks. **Deliberate simplification vs the original todo**: no IS-first filter
      (`load_oracle_feeds_for_date('AAVE','ETHEREUM',…)`) — `_AAVE_ORACLE_ASSETS` is a static 6-entry dict, verified
      byte-identical to IS's `aave_oracle.py` `_AAVE_ORACLE_RESERVES["ETHEREUM"]` today but with nothing enforcing that
      going forward; add the IS-first filter (mirroring `_resolve_chainlink_feeds`) if/when the two registries need to
      diverge safely. **Known gap deferred to Phase 5** (documented in code at `_record_aave_empty`): pre-listing days
      for rsETH/ezETH will aggregate to `SOURCE_RETURNED_ZERO` rather than an honest pre-listing reason — needs a
      verified per-reserve listing-date registry before the full-history backfill, analogous to Chainlink's
      `get_chain_genesis_date` gate.
- [ ] [MTDS] P2. **DEX collector/endpoint** — point `dex_pool_swaps` at the Phase-0 replacement endpoint (or a
      direct-RPC pool-state reader), deepen UniV3, add a reserve→per-interval-mid derivation. If no endpoint/key →
      scaffold + `BLOCKED-CREDENTIALS`, never silently drop.

## Phase 3 — Sample-download test on the `-test-` bucket (runtime verification, no prod write)

- [ ] [MTDS] P3. **Prove force + skip per surface** — sample download for the AAVE oracle (and DEX where endpoint
      available) against the `-test-` bucket: force-leg writes the canonical parquet + manifest `captured`; skip-leg
      fires the freshness skip. Read the VM `run.log` as ground truth. This is the "tested for sample data downloads"
      requirement.

## Phase 4 — Daily-download / MVP gate

- [ ] [IS] P3. **Daily-download inclusion** — confirm the new feeds/venue are `is_mvp`-tagged and land in the daily
      instrument-download universe so they are fetched on the standing cadence, not only on a one-off backfill.

## Phase 5 — Fill on real infra (SPOT VMs; manifest-verified; monitored by TARGET-shard count, not log activity)

- [ ] [MTDS] P2. **#3 oracle backfill** — SPOT-VM RPC backfill (getAssetPrice + Chainlink) over history; monitor by
      manifest count of `(AAVE, spot_asset, oracle_prices)` shards created (`time_created`), not log lines.
- [ ] [MTDS] P2. **#1 CEX-spot contiguity backfill** — full-history Tardis backfill over `*-SPOT` LST venues; SPOT VM,
      `tardis-concurrency-guard` cap-1 (dominant constraint), non-1st-of-month dates use the paid academic key.
- [ ] [FEATURES] P2. **#4 lst_yields backfill** — run the `lst_yields` feature over the full `lst_rates` source
      history + fix the today-vs-prior inner-join/vocab that drops Solana + LRTs (ezETH/rsETH) from the feature output.
- [ ] [MTDS] P3. **#2 DEX fill** — deep-backfill `dex_pool_swaps` once the endpoint lands (else remains
      `BLOCKED-CREDENTIALS`).

## Phase 6 — Interest PnL on honest data (the payoff; see pnl_interest_accrual doc)

- [ ] [STRATEGY] P2. **A2 staking leg** — wire `carry_staked_basis` `STAKING_REWARD`/`CARRY` to the `lst_yields`
      `exchange_rate/prev_rate` index ratio keyed off `cfg['lst_asset']`; explicit-zero the Aave-lending mismodel;
      honest-absence visible; real passive-parity test; 3-lens money-path review; ship to LDR. Prod-NAV recompute stays
      operator-gated.
- [ ] [STRATEGY] P3. **Recursive-staking borrow leg** — unblocks once #3 Aave oracle (collateral) lands; wire the
      `aave_borrow_index` cost leg + the archetype's drivability. Depends on Phase 5 #3.

## Progress Log

- **2026-07-21** — Plan authored from the pipeline-add understand sweep. Codex SSOT `lst-exchange-rate-surfaces.md`
  authored alongside. Key reframes captured: #1 CEX = backfill-not-build (catalogue already complete; list edits are
  phantom-minting); #3 Aave oracle = plumbing (dormant RPC, not missing); #2 DEX = collector/endpoint problem;
  denominator-first honest-coverage invariant. Executing Phase 0 (reality verification) next.
- **2026-07-21 (Phase 1, partial)** — UAC's AAVE oracle venue registration landed: `unified-api-contracts@6bdbc31d` on
  `live-defi-rollout` (11,739 tests passed, 0 failures; two pre-existing test gaps fixed in the same commit rather than
  left red). Took 7 ship attempts, all blocked by the sentinel-race under heavy concurrent PM/UAC push traffic on this
  shared host, not by any real content problem — see
  `plans/active/issues/quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md` for the pattern
  (a peer's commit or a same-repo commit invalidates the QG sentinel between gate-pass and quickmerge; fix is
  re-gate-then-immediately-quickmerge, never re-gate-then-wait). **MTDS and IS legs of Phase 1 remain BUILT-BUT-NOT-
  SHIPPED**: both repos have their Phase-1 file changes staged/committed locally (MTDS `_oracle_prices_constants.py`
  weETH/ezETH Chainlink feeds; IS `chainlink.py` mirror + `aave_oracle.py` adapter + `factory.py`/`orchestrator/defi.py`
  registration) but their `quality-gates.sh` is blocked by pre-existing, unrelated, already-filed test-baseline drift
  from an earlier OKX-FUTURES/OKX-SWAP venue registration + DERIBIT-COMBO deregistration (root cause
  `unified-api-contracts@11adf279`) — not caused by this plan's work, and not this plan's to fix:
  `plans/active/issues/mtds_rule11_shard_count_stale_baseline_2026_07_21.md` (MTDS) and
  `plans/active/issues/instruments_service_deribit_combo_purge_test_drift_2026_07_21.md` (IS, already operator-assigned
  `assigned_vm: planning`). Do not re-attempt those ships until the respective issue is resolved; do not duplicate
  either issue doc. The remaining Phase 1 UAC todo (Chainlink feed-map, tagged `[UAC][IS]` above — body describes
  MTDS+IS work) stays unchecked for the same reason.
- **2026-07-21 (IS Phase 1 completed + shipped-BLOCKED)** — the UAC Phase 1 landing itself (surfacing
  `AAVE-ETHEREUM: aave_oracle` in `VENUE_TO_ADAPTER_KEY`) generated a NEW, separate instruments-service test-drift issue
  for other slots pulling UAC without this plan's IS adapter yet:
  `plans/active/issues/instruments_service_aave_oracle_adapter_registration_test_drift_2026_07_21.md` (filed by a
  different slot, `assigned_vm: planning`; correctly noted the fix as "already this plan's own next todo" and did not
  duplicate/rebuild it). That issue doc's predecessor
  (`instruments_service_deribit_combo_purge_test_drift_2026_07_21.md`) had already been resolved upstream by its owner —
  pulled cleanly via `git pull --ff-only` (6 commits, none touching this plan's files). With that in, this plan's
  already-built `aave_oracle.py`/`chainlink.py`/`factory.py`/`defi.py` resolved 3 of the new issue doc's 4 failing
  invariant tests immediately; the 4th (`DEFI dedup target count 98≠99`) was verified via `git stash` isolation (adapter
  file both present AND fully absent → identical 99 either way) to be driven purely by UAC's already-landed venue-phase
  flip, not by IS's own adapter — bumped the frozen count with provenance, matching that issue doc's own todo #2
  guidance. Also fixed en route: a PRE-EXISTING (verified via isolation, unrelated to this plan) address-citation gate
  failure in `_dex_factory_registry.py` (12 well-documented but uncited addresses from the just-landed
  DERIBIT-COMBO/dex-factory-resolver fix) that was blocking ALL instruments-service ships, not just this one — added the
  citation gate's required per-line `# DERIVED` marker (small, mechanical, ≤30min fix per the findings-triage rule,
  since it blocked everyone). `instruments-service` reached fully-green `quality-gates.sh` (sentinel matching HEAD)
  twice, but **quickmerge itself is blocked by the dirty-deps pre-flight guard** — `unified-trading-library` (a path
  dependency) has genuinely LIVE uncommitted WIP (8 files sharing an mtime ~27s old at check time) that must NOT be
  isolated/touched per the liveness-gating rule. IS's 2 commits sit safely local (ahead of origin, clean tree) pending
  UTL's WIP clearing; ship it + this plan's own UTL fix (the `_VENUE_OVERRIDES["AAVE"]` provenance bug, see Phase 2
  above) together the next time that tree is genuinely clear.

## RESUME POINT (pre-compact 2026-07-21) — a fresh session starts HERE

- **Phase 0 is DONE (verified denominator below).** Phase 1 is the next executable step, and it is ready NOW.
- **The VERIFIED denominator to register in Phase 1 (ETHEREUM, conservative — only real-eth_call/probe YES items):**
  - **AAVE `(AAVE, spot_asset, oracle_prices)` — 6 reserves:** wstETH `0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0`,
    weETH `0xCd5fE23C85820F7B72D0926FC9b05b43E359b7ee`, rETH `0xae78736Cd615f374D3085123A210448E74Fc6393`, cbETH
    `0xBe9895146f7AF43049ca1c1AE358B0541Ea49704`, rsETH `0xA1290d69c65A6Fe4DF752f95823fAe25cB99e5A7`, ezETH
    `0xbf5495Efe5DB9ce00f80364C8B423567e58d2110` (this address ONLY; `0x2416092f…` REVERTS).
    `instrument_id=<symbol_lower>`. EXCLUDE osETH (not a reserve).
  - **Chainlink feed-map (mirror BOTH MTDS dict + IS tuple) — 2 RefPrice feeds:** weETH/ETH
    `0x5c9C449BbC9a6075A2c061dF312a35fd1E05fF22` (dec 18), ezETH/ETH `0x636A000262F6aA9e1F094ABF0aD8f645C44f641C` (dec
    18). NOT rsETH (ExRate), NOT wstETH (Calculated-USD only — operator decision).
  - **CEX (#1): NO catalogue edit.** **DEX (#2): endpoints work today — normal collector task, NOT blocked.**
- **Phase 1 execution** (smallest shippable first): add the 2 Chainlink feeds to BOTH mirrored maps (MTDS
  `_oracle_prices_constants.py` dict + IS `chainlink.py` tuple; the mirror-invariant test must pass) → one quickmerge
  per repo; then the AAVE oracle venue registration (UAC `expected_coverage`/`defi_venues` phase
  flip/`venue_adapter_keys`/ `capability_declarations`) + IS `aave_oracle` adapter enumerating the 6 reserves; regen
  catalogue; confirm the new `(CHAINLINK-ETHEREUM, SPOT_PAIR, oracle_prices)` + `(AAVE, spot_asset, oracle_prices)`
  cells render `expected_unattempted` (honest RED).
- **Deferred to operator/scope (do NOT register without a ruling):** wstETH Chainlink (Calculated-USD feed — is that
  shape allowed in the RefPrice map?); L2 (Arbitrum/Base/…) LST feeds + AAVE reserves (Ethereum-only Phase 0). Full
  evidence: `wf_f629fbb4-7da` journal.
- **Held artifacts (on-disk, survive compaction, NOT shipped):**
  `strategy-service/strategy_service/engine/backtest/ index_ratio_accrual.py` + its test (the correct pure
  staking/borrow accrual helper for Phase 6, held until the leg wiring). Two labeled stashes: `strategy-service`
  (superseded blocked fix — droppable) and `features-service` (deferred safe-survivor fixes — recover with
  `git stash apply`, reconcile against peer `features-service@9ce1f4ab`).

## Lessons (avoid re-learning)

- **CEX catalogue-add is a PHANTOM-MINTING anti-pattern** — the LST bases are already in `CEFI_BASE_ASSET_UNIVERSE` +
  `STAKING_SPOT_EXCEPTION`; #1 is a Tardis BACKFILL, never a list edit. (Codex §#1.)
- **Plan todos use P0–P3, NOT the phase number** — `P4/P5/P6` fail `check_todo_format` ("missing P-priority"); priority
  is importance, conveyed separately from the phase header.
- **A new codex-ssot doc needs** `referenced_by`/`owner`/`last_reviewed`/`code_refs` present-but-empty; a plan's
  `assigned_role` must be from `agents/*.md` (e.g. `backend_engineer`, not `backend`); run
  `scripts/plan-hygiene/fix_frontmatter.py` + `fix_todo_format.sh` then the pre-commit passes.
- **PM has heavy peer commit traffic** — a tight `pull→add→commit→push` retry loop (up to ~5) lands past the
  branch-drift hook; doc-only PM commits may also go direct-push under the `docs(plans):` carve-out.
- **The `getAssetPrice` RPC is DORMANT, not missing** — lift it from
`market-tick-data-service aave_positions.py:: _fetch_rpc_oracle_prices`, never re-implement.
</content>
