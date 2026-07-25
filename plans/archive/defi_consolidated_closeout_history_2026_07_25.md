---
doc_type: plan
title:
  DeFi consolidated close-out — Track 6/7 + Tracks 2/3/4/8 closed-item + session history (forked from the defi
  consolidated close-out plan)
summary:
  Archive-bound history extracted verbatim from defi_consolidated_closeout_2026_07_18.md across two same-day extraction
  passes. 1st pass (2026-07-25, parent was 1039 lines against the 1000-line hard cap) -- Track 6 (RENDER -- data-status
  surface four + restore the enumeration view) and Track 7 (CULL -- purge the removed venues everywhere), both 100%
  closed (2/2 done in Track 6, 1/1 done in Track 7). 2nd pass (2026-07-25, an AO-readiness pass, parent had drifted back
  to 984 lines) -- every remaining CLOSED item in Tracks 2/3/4/8 + "Open follow-ups" that no open parent todo depends
  on, the 2026-07-24 in-flight VM banner (superseded by the 8h-mark interim report below it), and the full 2026-07-24
  session-3 through 2026-07-25 8h-mark-checkpoint Progress Log tail. Record-only; not intended for further action. Zero
  open todos anywhere in this doc. Track 6's close-out CRITERION (not a todo) is not yet fully met per the parent's own
  text (a fresh distinct-values census must return zero `is_canonical=false` entries) — that residual drive-to-0 work is
  tracked in `defi_track01_per_instrument_and_canon_id_2026_07_24.md`, not as a todo here or in the parent.
status: complete
nature: record
asset_group: [defi]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    deployment-api,
    deployment-ui,
    deployment-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [
    defi,
    close-out,
    consolidation,
    canonicalisation,
    manifest,
    enumeration,
    venue-purge,
    history,
    plan-split,
    archive-bound,
  ]
related: [/plans/active/defi_consolidated_closeout_2026_07_18.md]
created: "2026-07-25"
last_updated: "2026-07-25" # 2nd same-day extraction pass, see source: below
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: docs_reconciler
drift_direction: advance-code
supersedes:
superseded_by:
depends_on:
source:
  [
    "Forked 2026-07-25 from defi_consolidated_closeout_2026_07_18.md's Track 6 + Track 7 sections during the line-cap
    trim (parent was 1039 lines against the 1000-line cap; both tracks are fully-closed with zero open todos, the
    cleanest extraction candidates per the extract-to-archive-bound-history-child pattern in
    plans/archive/issues/plan_line_cap_remediation_2026_07_23.md's FINAL RESOLUTION section).",
    "2nd extraction pass, same day 2026-07-25: an AO-readiness pass on the parent (which had drifted back to 984 lines)
    extended this doc in place -- per the operator's resolved-ambiguity ruling to extend the existing 2026-07-25 history
    doc rather than create a near-duplicate -- with every Tracks-2/3/4/8 + Open-follow-ups closed item the parent's open
    todos do not directly depend on, plus the full 2026-07-24 session-3 to 2026-07-25 8h-mark Progress Log tail.",
  ]
locked_by:
locked_since:
---

# DeFi consolidated close-out — Track 6/7 + Tracks 2/3/4/8 closed-item + session history

> **Archived 2026-07-25** — status was already complete.

> **Record-only.** This doc is the archive-bound verbatim extraction of closed work from
> [`defi_consolidated_closeout_2026_07_18.md`](/plans/active/defi_consolidated_closeout_2026_07_18.md), across two
> same-day extraction passes. Nothing here is summarized, rewritten, or condensed — every section below is copied
> byte-for-byte from the parent as of its respective extraction. Zero open todos anywhere in this doc.
>
> **1st pass (immediately below — Track 6 + Track 7)**: both fully-closed tracks (2 done in Track 6, 1 done in Track 7).
> **2nd pass (further down this doc)**: every remaining closed item in Tracks 2/3/4/8 + "Open follow-ups" that no open
> parent todo depends on, the superseded in-flight VM banner, and the full 2026-07-24→2026-07-25 Progress Log tail (both
> dated session write-ups, the deferred-work table, lessons, and the 8h-mark interim report).

## Track 6 — RENDER: data-status surface #4 + RESTORE the enumeration view · P1

- **Sources**: `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md` (HYPERLIQUID/ASTER 3.77M/1.07M invisible),
  `issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`, the removed-feature archaeology
  (`deployment-api@47a7f67`/`953fa81`/`512180be` gated/suppressed/canonicalised-away the distinct-values view
  2026-07-16→18).
- **Close-out criterion**: data-status renders the canonical DeFi ids; the raw distinct-values audit view is live again;
  **AND** a fresh re-run of that census (`GET /api/data-status/distinct-values/defi`) returns **zero**
  `is_canonical=false` entries — not just the view being live (gate-audit §2, 2026-07-24; the Wave-D worklist it
  surfaced 2026-07-18 must be driven to 0 first — that drive-to-0 work is tracked in
  `defi_track01_per_instrument_and_canon_id_2026_07_24.md`, not as its own todo here).

- [x] ✅ [BACKEND] P1. **SHIPPED + LIVE (operator ask 2026-07-18): `instruments-service@64a58cc1` (by_chain projection +
      `chain` read-col) + `deployment-api@0d2f6e6` (endpoint) + `deployment-ui@4afcfd8` (panel, `pw:L2 ✓`
      `data-status-distinct-values.spec.ts`).** `GET /api/data-status/distinct-values/{asset_group}` returns per-axis
      distinct values (venues/instrument_types/data_types/**chains**) each with `is_canonical` (exact UAC-SSOT-set
      membership: `VENUES_BY_ASSET_GROUP`/`InstrumentType`/`DATA_TYPES_BY_ASSET_GROUP`/`MAINNET_CHAIN_IDS`), sourced
      from the nightly `coverage.json` rollup keys (single bounded blob read — NO new corpus walk), values NOT
      collapsed. **It immediately surfaces the Wave-D worklist** (real defi drift measured: 76 venues incl.
      AAVE/AAVEV3/AAVE_V3 + COMPOUND/COMPOUND_V3 dupes; 17 itypes, 11 non-canonical case/alias drift; 36 dtypes, 10
      non-canonical incl. `dex_pools`→`dex_pool_state`; 24 chains, 3 non-canonical: HYPERLIQUID→HYPERLIQUID_L1 +
      KALSHI_PERP/POLYMARKET_PERP leaking). **Process findings (see Progress Log)**: (a) `@0d2f6e6` was DIRECT-PUSHED
      (no `Quickmerge:` trailer) via the REMOVED git-commit skill — a git-discipline violation; code is green (6 unit
      tests + lint) so accepted, flagged for operator; (b) it also fixed a pre-existing cross-repo drift
      `deployment-api@593327a` (R2c's new `EXPECTED_ACQUISITION_PENDING` hadn't been mirrored into
      `coverage_metrics.py::EMPTY_REASON_KEYS` → tree-break on LDR — via quickmerge). (repos: deployment-api,
      deployment-ui, instruments-service)
- [x] ✅ [BACKEND] P2. **SHIPPED 2026-07-21: `deployment-api@427ede5` (turbo-API fix) + `deployment-ui@83ec561`
      (capability-bundle DRIFT residue prune).** **Root cause (turbo-API)**: `_read_defi_merged_index`'s DEFI-venue
      whitelist (`_allowed_defi_venue_chain_pairs`) is sourced purely from UAC `ALL_DEFI_VENUES` +
      `LEGACY_DEFI_VENUE_ALIASES`; HYPERLIQUID and ASTER are CEFI-registered hybrid on-chain-CLOB venues never declared
      in UAC's DEFI registry, so their real, currently-captured chain-side rows under `asset_group=defi` (confirmed live
      2026-07-10: 3.77M `(HYPERLIQUID, HYPERLIQUID)` rows 2023-11-01→2026-05-31, 1.07M `(ASTER, BSC)` rows
      2024-04-03→2026-05-31) were silently dropped BEFORE the aggregator ever saw them — not a stale cache, not a naming
      mismatch, a pure registry-completeness gap in the whitelist filter. **Fix**: added a deployment-api-local
      supplemental whitelist (`_CEFI_DEFI_HYBRID_VENUE_CHAIN_PAIRS`, `defi.py`) admitting these two confirmed
      `(venue, chain)` pairs — NOT a double-counting risk since this whitelist only gates DEFI-category bucket reads,
      completely separate from CEFI's own coverage computation (matches the operator-confirmed hybrid architecture,
      `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` Update §3: CEFI holds instrument
      definitions, DEFI holds chain-level settlement data). Traced the downstream `dates_expected`/`venue_start`
      resolution (`venue_resolution.py`) to confirm it gracefully falls back to observed-date-range for undeclared
      venues (no crash, no stale-cache dependency). Durable fix still belongs in UAC's `ALL_DEFI_VENUES` (out of this
      dispatch's deployment-api/deployment-ui scope) — this is the documented stopgap, flagged in the code comment +
      `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md`. 2 new regression tests
      (`TestCefiDefiHybridVenueWhitelist`, `test_data_status_service.py`), full `quality-gates.sh` green. Shipped via
      the **dirty-deps carve-out** (direct push, `Quickmerge: agent` trailer) — quickmerge's pre-flight audit was
      blocked by foreign concurrent-agent WIP in unified-trading-library (`defi/` module) and deployment-service
      (`launch-canonical-migration-vm.sh`), neither touched. **Live re-verification attempt**: inconclusive — the real
      GCS DEFI manifest (`_index/availability_index.parquet`, ~1.9GB) is being actively rewritten by the manifest
      consolidator several times per minute right now (confirmed generation churn across repeated read attempts, all
      raced to 404), so a fresh full-file read couldn't complete; the fix rests on the 2026-07-10 live-verified evidence
      above + the code-path trace + passing regression tests, not a fresh live pull. **Capability bundle (Track 6 + the
      sibling issue doc's DRIFT-residue finding)**: no generator for
      `capability-manifest.json`/`capability-verdict-matrix.json` exists anywhere in this workspace (confirmed — no
      committed script in deployment-ui or UAC; the verdict-matrix's own reasons cite a `config_space_fuzzer` module
      that doesn't exist either), so per the issue doc's own fallback guidance this was a surgical,
      referential-integrity-verified prune rather than a blind full regen: removed the `venue:drift`/`collateral:drift`
      nodes + their 21 edges from the manifest (574→572 nodes, 2433→2412 edges; zero NEW dangling edge references — the
      pre-existing `venue:ibkr` dangling ref and the pre-existing duplicate `EVENT_DRIVEN` node are untouched, out of
      scope), one stale free-text "Kamino + Drift" mention fixed in a `CARRY_STAKED_BASIS` edge reason, and removed the
      66 `venue=drift` cells from the verdict-matrix with recomputed per-archetype + top-level summary counts (verified
      formula: `available_count=Σlen(available_algos)`, `blocked_count=Σlen(blocked_algos)`, `cell_count`=their sum; new
      summary total=20,544, available=12,122, blocked=7,974, not_registered=448 unchanged). `generated_from_commit` left
      unchanged (still 1000+ commits stale) since this is a documented delta on top of the stale base, not a full regen
      — the durable fix is still recovering/ building the real generator, tracked in the sibling issue doc.
      **Verification**: `tsc`/`eslint`/`vitest` (1038 passed) all clean; updated the 2 hardcoded stale-count assertions
      in `tests/smoke/capability_tab.spec.ts` (574/2433 → 572/2412; summary 21,600/12,977/8,175 → 20,544/12,122/7,974)
      and re-ran — **`pw:L2 ✓` all 9 tests green**, incl. a real browser render of the Capability tab confirming DRIFT
      no longer shown. (repos: deployment-api, deployment-ui)

## Track 7 — CULL: purge the removed venues everywhere (dead-only, snapshot-first) · P1

> **Operator ruling 2026-07-18**: remove the CULLED venues ENTIRELY — UAC + manifest + GCS data + MVP catalogue + docs —
> to avoid confusion. **KEEP** `KALSHI-PERP`/`POLYMARKET-PERP` (roadmap — will be added), `LIGHTER-ZKSYNC`
> (blocked-credentials MVP scaffold — external-data-always-available rule), `EXTENDED-STARKNET` (live MVP). **All
> GCS-data deletes are snapshot-first** (irreversible). NOTE: LIGHTER/EXTENDED/(culled) PACIFICA are CeFi-classified —
> the cefi purge is passed to `cefi_consolidated_closeout_2026_07_18.md`; this track owns the DeFi-side residue.

- **Sources**: `issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md`,
  `issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`,
  `issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`, `/codex/02-data/mvp-scope-canonical.md`
  (STALE — still bolds `PACIFICA-SOLANA` as MVP; code culled it).
- **Close-out criterion**: zero references to culled venues in UAC / manifest / GCS / catalogue / docs; a snapshot
  exists before any delete.

- [x] ✅ [DATA] P1. **Purge the culled Solana-perp venues' DeFi-side residue — checklist item was itself stale; nearly
      all of it was ALREADY DONE (verified 2026-07-21).** Fresh live case-insensitive grep of unified-api-contracts +
      market-tick-data-service for DRIFT/PACIFICA/MANGO/ZETA/FLASH/SOLAYER/PICASSO/CAMBRIAN, with every hit read in
      context (not grep-and-conclude): - **architecture_v2 leg specs — already dropped, NOT ~20 files still pending.**
      The `d996e4fe` UAC commit (2026-07-16, cited in
      `issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`'s own "UPDATE" section) already
      removed every live DRIFT reference from `archetype_capability_manifest.json`, `archetype_leg_spec.py`,
      `archetype_leg_spec_seeds.py`, `collateral_registry.py`, `jurisdiction_overlay.py`, `order_semantics.py`,
      `simulation_assumptions.py`, `venue_tokens.py` (+5 test files) — re-verified live: the ONLY residual "Drift"
      mention in `architecture_v2/` is one properly-formatted historical note in `archetype_capability_manifest.json`
      line 692 ("...CeFi-perp hedge leg (Drift) removed 2026-07-16, operator ruling..."), matching this cull's own
      comment-marker convention. Zero MANGO/ZETA/PACIFICA hits in `architecture_v2/` at all. **Nothing left to drop.** -
      **`mvp-scope-canonical.md` — already fixed**, `unified-trading-pm@709274a5c` (2026-07-18): grepped the live file,
      zero PACIFICA/DRIFT hits remain; DeFi section now reads "MVP-tag-all today" with no per-venue bolding. **No doc
      edit needed.** - **SOLAYER/PICASSO/CAMBRIAN — record-correction, not part of this ruling.** These were removed
      **2026-06-02** (a DIFFERENT, EARLIER, unrelated operator decision — "no usable/decodable data source" per
      `issues/issue_docs_remediation_sweep_2026_06_02.md`), NOT the 2026-07-16 Solana-perp-DEX-onto-Jupiter ruling this
      todo's own wording implied. Confirmed live: only historical comment markers remain in
      `unified_api_contracts/{testing/vcr_endpoints.py, registry/venue_adapter_keys.py,       registry/capability_declarations/{_defi.py,_defi_chain_data.py}}`
      — no live registry entries, nothing to purge, already at the correct end-state. - **market-tick-data-service — one
      genuine residue item found + removed**:
      `market_tick_data_service/scripts/purge_drift_pacifica_solana_perp_2026_07_16.py`, the (already-executed)
      DATA/STATE purge script itself, which carried its own lifecycle marker ("DELETE this file once the kill is
      verified + journaled"). The kill IS fully verified + journaled
      (`issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md` COMPLETION RECORD: 0 residual across
      manifest/catalogue/GCS/per-VM-shards, both asset groups, 3+ post-resume consolidator cycles watched clean). No
      other lingering MTDS handler branches found (`drift_v2_historical_handler.py` / `drift_v2_onchain_decoder.py` /
      any pacifica-named handler were already deleted in `market-tick-data-service@2e674d1f`, "55 files, -11,178
      lines"). Deleted: **`market-tick-data-service@f6176e8b`** (dirty-deps carve-out direct push — quickmerge's
      pre-flight blocked on foreign concurrent WIP in unified-trading-library + unified-api-contracts, confirmed
      unrelated canonical-id/fail-hard-enforcement work, neither touched; `quality-gates.sh --no-fix` green,
      `.qg_last_passed_sha` sentinel matched HEAD before the commit). **unified-api-contracts required NO commit**
      (nothing dead left to remove — see below). - **Confirmed LOAD-BEARING, deliberately left alone (not residue)**:
      (a) `unified_api_contracts/registry/venue_adapter_keys.py::DECOMMISSIONED_VENUE_BASES` — an ACTIVE frozenset
      (`{"DRIFT","PACIFICA","MANGO","ZETA","FLASH"}`) that deployment-api's data-status drilldown reads to
      base-prefix-exclude legacy manifest rows; removing it would REGRESS that filter. (b)
      `unified_api_contracts/canonical/quarantine.py::QUARANTINE_REGISTRY` — a NEW (2026-07-20/21,
      `fail_hard_canonical_enforcement_design_2026_07_20.md`) fail-hard-enforcement mechanism whose ONE seed member is
      `PACIFICA-SOLANA` (265 permanently-honest-raw objects, evidenced, expires 2027-07-21) — deliberately references
      the culled venue so these legacy rows verdict `quarantined` (PASS) instead of `non_canonical` (FAIL) once Stage-3
      read-enforcement wires in; NOT dead code. (c) `DRIFT` as a TOKEN TICKER (not venue) in
      `unified_api_contracts/registry/{defi_major_assets.py,cefi_instrument_universe.py}` — the Drift-protocol
      governance token trades live on non-culled venues (Binance/Bybit/etc, ~40,693 manifest rows per the original
      cull's own scope-guard); this is a different entity from the culled DEX venue and must stay. (d) a
      `_PERP_DEFAULT_CHAIN` DRIFT/PACIFICA chain-default mapping in MTDS's `scripts/migrate_defi_full_v9_canonical.py`
      and a `_RENAMED_VENUES = {"PACIFICA": "PACIFICA-SOLANA"}` mapping in
      `scripts/migrate_lst_perp_shared_bucket_gap_2026_07_13.py` — both are historical-data migration utilities (the
      latter has its own `Delete-when:` gated on a DIFFERENT plan's Todo 9, unrelated to this cull) whose correctness
      for any future re-run of already-written legacy rows depends on these mappings; left untouched as
      out-of-scope-for-this-cull rather than risk miscategorising historical data. - **instruments-service +
      deployment-service** were explicitly OUT of this dispatch's repo scope (narrowed to avoid a live file-collision
      with two other concurrently-running agents in those exact repos) — per
      `issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md`'s own COMPLETION RECORD these already shipped
      (`instruments-service@4d65d468`+`b37e9d82`+`ee19f6f3`, `deployment-service@9b13679`+`194deeb`, all confirmed on
      `origin` as of the 2026-07-18 closing pass) — not re-verified this session, cited as already-closed evidence
      rather than re-audited. (repos: market-tick-data-service, unified-api-contracts, unified-trading-pm —
      instruments-service/deployment-service closed by a prior session, cited above)

## Track 2 — STORE: closed items (extracted 2026-07-25, 2nd extraction pass)

> Both items below are done, extracted verbatim (line-cap remediation, 2nd pass) from Track 2 of
> [`defi_consolidated_closeout_2026_07_18.md`](/plans/active/defi_consolidated_closeout_2026_07_18.md). The parent keeps
> Track 2's remaining open todos + the ⛔ 2026-07-20 fold-not-delete correction banner they depend on.

- [x] ✅ [DATA] P0. **Pin the flat canonical path shape (code portion) + kill the second dexpool writer path.** ~~DELETE
      the dead top-level Solana `dex_pools/`+`lending_indices/` prefixes (frozen 2026-04-14, "Shape-B")~~ **← DELETE
      CLAUSE SUPERSEDED — see the ⛔ correction banner directly above.**

      **2026-07-22 findings + fix.** The historical bare-`0x<address>.parquet` batch writer suspected by
                                                                                                                                      `issues/defi_dexpool_second_writer_path_and_zero_capture_2026_07_10.md` was already fixed 2026-07-09
                                                                                                                                      (`mtds@0713c01a`/`0ce28623`) — confirmed dead via a narrow live-GCS read (`day=2026-07-18` CURVE
                                                                                                                                      `dex_pool_state` objects are real `TOKEN0-TOKEN1.parquet` symbol names, not addresses). The ACTUAL live
                                                                                                                                      second writer: `market_tick_data_service.live.websocket_runner.live_tick_blob_path` (`mtds@3043f2dc1`,
                                                                                                                                      2026-06-26) spliced `chain=` BEFORE `venue=` for every non-cefi asset_group — the reverse of the canonical
                                                                                                                                      batch order (`unified_api_contracts.build_defi_partition_path`: `venue={V}/chain={C}/...`) — for the SAME
                                                                                                                                      (asset_group=defi, venue, chain, data_type, day) shard. Undetected for ~1 month because
                                                                                                                                      `canonical_path_violations` parsed partition segments into a `key→value` dict and never validated ORDER
                                                                                                                                      (only presence/values) — proven empirically (a hand-built reversed-order path returned the identical
                                                                                                                                      violation list as the correct order).

                                                                                                                                      **Shipped**: `market-tick-data-service@0fcfa803` — reordered `live_tick_blob_path` to venue-before-chain +
                                                                                                                                      pinned the `_PER_AG_SHARD_COUNTS["DEFI"]` regression test (2673→2592, drifted by the unrelated concurrent
                                                                                                                                      METEORA/LIFINITY/PHOENIX phase-downgrade commit `uac@9a047a31`) + a new live/batch path-order regression
                                                                                                                                      test. Full `quality-gates.sh` green (6814 passed), pushed to `live-defi-rollout`.

                                                                                                                                      **UAC half SHIPPED `unified-api-contracts@1cd27478` (2026-07-23)**: the paired defi-scoped structural check
                                                                                                                                      added to `unified_api_contracts.canonical_path_violations` (venue-before-chain, lowercase
                                                                                                                                      `instrument_type`, `pipeline_mode=` position) so this drift class fails loud going forward — proven safe
                                                                                                                                      against the real writer (its template is unconditional/fixed; verified zero violations across every
                                                                                                                                      pipeline_mode × instrument_type × data_type combination + the fixed live path) and covered by 4 new
                                                                                                                                      regression tests (126 total passing). The blocking pre-existing defect
                                                                                                                                      (`tests/internal/unit/test_archetype_capability_manifest_parity.py`, 3 false failures) was ALREADY
                                                                                                                                      resolved by unrelated concurrent work by the time this shipped — `uac@68c4c371` fixed the parity test's
                                                                                                                                      root-cause path resolution (it resolved via ancestor walk before `UNIFIED_TRADING_WORKSPACE_ROOT`,
                                                                                                                                      which had been reading a stale outer-root PM checkout — the codex markdown sections were never
                                                                                                                                      actually missing, the test was just looking in the wrong place); no codex-doc content edit was needed.
                                                                                                                                      Verified: `bash scripts/quality-gates.sh --no-fix` full green (`.qg_last_passed_sha` == HEAD
                                                                                                                                      `824b1b7d` pre-ship), all 17 archetype-parity tests + all 89 `test_partition_path_is_canonical.py`
                                                                                                                                      tests passing, shipped via `quickmerge.sh --agent --files 'unified_api_contracts/canonical/partition_paths.py
                                                                                                                                      tests/unit/test_partition_path_is_canonical.py'`. (repos: market-tick-data-service, unified-api-contracts)

- [x] ✅ [INFRA] P1. **Correct the STALE codex path docs — checklist item was itself stale; both docs were ALREADY fixed
      (verified 2026-07-21).** Re-read both target docs in full + re-derived from this plan's own "Path template
      (operator-locked...)" section + a fresh live GCS listing
      (`gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=2026-04-14/pipeline_mode=batch_onchain_subgraph/asset_group=defi/venue=AAVE_V3/chain=ARBITRUM/`
      — venue segment confirmed BEFORE chain). **Finding: both docs already state venue-before-chain + carry
      `pipeline_mode=` left of `asset_group=`, and neither contains any "Shape-B" text** — grepped
      `market-tick-data-service/docs/` for `Shape-B` (0 hits). The underlying fix landed same-day this bullet was
      authored (`58a6a54edb` @ 2026-07-18 14:14), just ~2.5h before the checklist text could reflect it:
      **`unified-trading-pm@709274a5c`** (2026-07-18 16:50, "…venue-before-chain…", corrected the DEFI row in
      `per-asset-group-bucket-layouts.md` to `venue={v}/chain={chain}` + added `pipeline_mode={mode}_{source}` left of
      `asset_group=`) and **`market-tick-data-service@5f498858`+`@e9764b38`** (2026-07-18 16:46 / 2026-07-19 05:02, same
      "venue-before-chain path" DEFI-align pass to `docs/GCS_PATHS.md`, which already showed
      `venue={PROTOCOL}/chain={CHAIN}` with an explicit "(venue BEFORE chain)" comment and never referenced Shape-B).
      **No further doc edit required** — this bullet was simply never flipped after the fix shipped; flipping it now
      closes the gap. (repos: unified-trading-pm, market-tick-data-service)

## Track 3 — DENOM: closed items (extracted 2026-07-25, 2nd extraction pass)

> Both items below are done, extracted verbatim from Track 3 of
> [`defi_consolidated_closeout_2026_07_18.md`](/plans/active/defi_consolidated_closeout_2026_07_18.md). The parent keeps
> Track 3's remaining open todos (the PURGE-then-seed P0, the EXPECTED_SUBGRAPH_DEINDEXED `--apply` P1, the launcher-bug
> P2).

- [x] ✅ [DATA] P1. **DeFi catalogue `available_to` false-delisting — DONE (2026-07-20).** Root fix SHIPPED + VERIFIED
      `instruments-service@13c4f68a` (Option A: defi drop-outs never last-seen-delist, gated `asset_group=="defi"`, both
      full + incremental paths; truth-gate `delisted_at`/`expiry` preserved for a future probe) — PROVEN on real prod
      data: 947 clustered false-delistings (06-26/07-06/07-08 across TRADER_JOE_V2/PANCAKESWAP_V3/AAVE_V3/MORPHO) → 0.
      **(a) prod catalogue CORRECTED + VERIFIED**: `--mode full` regen (monotonic guard ACCEPT, `CATALOGUE_PROMOTED`) +
      a targeted frozen-tail purge (`purge_defi_false_available_to_2026_07_20.py`) — non-blank `available_to` 2,349 →
      **105**, **0** on the 3 false-cluster dates. **(b) historical manifest un-delist DONE + VERIFIED**
      (`undelist_defi_false_postdelist_eu_2026_07_20.py`, instrument_type-agnostic, the inverse of
      `reclassify_defi_postdelist_eu_2026_06_24.py`) — `EXPECTED_INSTRUMENT_DELISTED` **219,738 → 3,874** across 45.8M
      manifest rows. **(c) Option B (on-chain removal probe) SHIPPED** `instruments-service@13c4f68a` +
      `deployment-service@9a36478` (daily Cloud Run job, `defi-removal-probe`, 00:30 UTC) — conservative by
      construction, runtime-verified against prod (0/30 live targets confirmed gone — correct for a healthy universe).
      CI green both repos. SSOT + full evidence: `issues/defi_catalogue_available_to_false_delisting_2026_07_20.md`.
      **Residual, tracked separately**: the 215,864 un-delisted cells are honest-pending, not yet terminal — see the
      next item. (repos: instruments-service, deployment-service)

- [x] ✅ [DECISION] P1. **DeFi non-POOL per-instrument EU has NO reconciliation path — DECISION resolved + shipped
      (2026-07-21), generalization work still open.** (surfaced by the un-delist above). The catalogue-residual →
      typed-empty machinery is DEX-POOL-ONLY at all three layers, and SPOT_ASSET/A_TOKEN/DEBT_TOKEN are reference-only
      holdings with no per-day capture path. **Resolved: Option B — a NEW in-denominator terminal reason** (never
      `EXPECTED_NOT_ENOUGH_TVL`, which would reproduce the `EXPECTED_INSTRUMENT_DELISTED` clipped-from-denominator
      exclusion), decided via `AskUserQuestion` 2026-07-20/21. **Shipped**: `unified-api-contracts@d4d85854`
      (`EmptyConfirmedReason.EXPECTED_REFERENCE_ONLY_NO_CAPTURE_PATH`, deliberately NOT in
      `OUT_OF_COVERAGE_WINDOW_REASONS`), `instruments-service@a516bd01` (prospective enumerator seeding,
      `_enumerate_v2_defi`), `instruments-service@2967cf5f` (retroactive reconciliation script),
      `deployment-api@8691f29`/`@ea56fff` + `deployment-ui@183cfc3` (dashboard parity). **Measured 2026-07-21**: the
      215,864-cell instrument-level estimate did NOT hold at cell grain by measurement time (3 independent pyarrow
      queries against the live `_index`, 52.3M rows: zero EU cells carry a reference-only `instrument_type`; 166,641
      reference-only rows exist but are 100% already `captured`) — the retroactive script is a correct no-op today and
      stays as a self-cleaning safety net. Full evidence:
      `issues/defi_nonpool_per_instrument_eu_has_no_reconciliation_path_2026_07_20.md`. **Still open** (real capability
      work, not a decision gap): generalise `catalogue_pool_ids_for_shard` beyond `instrument_type=='pool'` + add a
      per-instrument residual emitter to the capturable non-POOL handlers (lending_indices/risk_params/lst_rates/
      evm_defi) — tracked as that issue doc's own `[ ]` follow-on items. (repos: market-tick-data-service,
      instruments-service, unified-api-contracts)

## Track 4 — CAP: closed items (extracted 2026-07-25, 2nd extraction pass)

> Both items below are done, extracted verbatim from Track 4 of
> [`defi_consolidated_closeout_2026_07_18.md`](/plans/active/defi_consolidated_closeout_2026_07_18.md). The parent keeps
> Track 4's one remaining open todo (wire Morpho + the Solana ORCA/RAYDIUM swap indexer).

- [x] ✅ [DATA] P2. **Verified 2026-07-24 (GCS object-existence probe, 160 venue×data_type×sample-date combos + VM
      run.log/deployment-registry evidence — manifest download infeasible this session, ~100KB/s sandbox network).** OOM
      crash-loop did NOT recur post-fix — every VM that ran after `a5b07ff7e` ran clean (no `Killed`/`rc=137`) until
      independently TERMINATED by an explicit `v1.compute.instances.delete` (confirmed via audit log; not OOM, not SPOT
      preemption). Mixed result: `dex_pool_state` has real substantive coverage for all 4 protocols 2023→2026-03
      (UNISWAP_V4 correctly absent pre-2025-01-31 launch) but a real, patchy gap ~2026-03→today (the healthy
      `mtds-dex-pools-backfill` run was killed 2026-07-18 mid-backfill, never relaunched until this session).
      `dex_pool_swaps`: UNISWAP_V2/V4 partial-but-improving (currently-running sharded fleet
      `mtds-dex-swaps-backfill-{1,2,3}` actively filling recent dates); **TRADER_JOE_V2 = 0% ever captured** (persistent
      TheGraph subgraph schema-cascade failure, a code bug, NOT OOM-related); **VELODROME_V2 = near-zero (2/20 sampled
      dates)**. Found + fixed a real launcher bug along the way (`--protocols` comma-lists broke gcloud `--metadata`
      parsing — deployment-service commit, both dex-pools + dex-swaps launchers) and relaunched a scoped
      `mtds-dex-pools-backfill` (4 protocols, 2023-01-01→today) to close the pool_state gap — T+10min health-verified
      RUNNING + writing real rows. Full evidence + verdict table + 5 follow-up todos (trader_joe_v2 code fix,
      velodrome/trader_joe swaps historical backfill, lending-indices launcher preemptive fix, re-check, manifest
      cross-check): `issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md`. (repos: market-tick-data-service,
      deployment-service)

- [x] ✅ [BACKEND] P3. **Post-phase codex audit for the dex_pools/dex_swaps protocol dispatch list** — check whether
      `/codex/02-data/defi-canonical-naming-ssot.md` documents the MTDS `_DEFAULT_PROTOCOLS`/fallbacks dispatch set; it
      currently does not (only data_type/venue/bucket path-naming rules) — add it if the audit confirms no stale list
      exists elsewhere. (repos: unified-trading-pm) — audit confirmed `defi-canonical-naming-ssot.md` genuinely lacks
      it, but a STALE, incomplete version already existed in `/codex/02-data/defi-data-types-catalog.md` §1/§2
      ("Sources" fields, missing the 2026-07-14 zero-capture-fix protocols + the Solana route) — corrected in place
      rather than duplicated, verified against `market-tick-data-service` code (`dex_pools_handler._DEFAULT_PROTOCOLS`
      17 protocols, `_dex_swaps_queries._DEFAULT_PROTOCOLS` 12 protocols) 2026-07-24.

## Track 8 / Open follow-ups — closed items + superseded VM-status narrative (extracted 2026-07-25, 2nd extraction pass)

> All items below are done (or, for the in-flight VM banner, superseded by the 8h-mark interim report further down this
> doc), extracted verbatim from Track 8 / "Open follow-ups" of
> [`defi_consolidated_closeout_2026_07_18.md`](/plans/active/defi_consolidated_closeout_2026_07_18.md). The parent keeps
> every genuinely-open Track 8 / Open-follow-ups todo, the correction banner on the paused-cron count, and two closed
> items that stayed IN the parent because open todos there directly point at them (the FLAGGED-marker remediation
> decision record — origin story for `defi_gmx_venue_removal_2026_07_25.md` +
> `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` — and the Solana AMM symbol-collision fix, which the
> resume-crons todo cites directly).

**In-flight VM banner (2026-07-24 ~18:22 UTC), superseded by the 8h-mark interim report below:**

> **🟢 IN-FLIGHT (2026-07-24, ~18:22 UTC onward) — a fresh dry-run report for this exact script is ALREADY RUNNING on VM
> `canonical-migration-defi-marker-cleanup-20260724-182226` (SPOT, `asia-northeast1-c`, launched via the new
> `defi-marker-cleanup` category on `launch-canonical-migration-vm.sh`, `deployment-service@b4d2305`). Full
> 2020-01-01..2026-07-24 corpus (356,391 markers); log streams to
> `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-defi-marker-cleanup-20260724-182226/run.log`;
> resume-log checkpoints every 2 min to
> `gs://deployment-scripts-central-element-323112/canonical-migration-defi-marker-cleanup/resume-seed/delete_migrated_defi_markers_2026_07_23.resume.jsonl`
> (safe to resume from if the VM is preempted). Steady-state ~5-6 markers/sec once past the cheap early-corpus portion →
> ETA ~15-16h from launch. **Do NOT launch another dry-run (local or VM) for this script while this is in flight** —
> check the VM/GCS log above for current status first. `--apply` stays human-executed-only regardless (see below) — this
> banner only concerns not duplicating the DRY-RUN. Remove this banner once the report is delivered to the operator and
> either superseded by a fresh run or acted on.**

- [x] ✅ [BACKEND] P2. **Stale duplicate — RESOLVED elsewhere 2026-07-24, synced here.** Already answered in
      `defi_track01_per_instrument_and_canon_id_2026_07_24.md`'s "Second Solana writer" item:
      `_dex_pools_subgraph.py::_collect_solana_dex` keys its manifest row AND leaf filename off the pool **ADDRESS**,
      never a derived symbol — structurally immune to the token-pair collision this item worried about (addresses are
      inherently unique). No fix/retire decision needed on collision grounds; only gap is optional readability. (repo:
      market-tick-data-service)

- [x] ✅ [BACKEND] P2. **`is_defi_force_include_pool` wiring** — `instruments-service@4e97a82e`. Cherry-picked ONLY the
      `filter_defi_instruments_by_relevance`/`_add_force_include`/orchestrator-namespace-import hunks out of `stash@{0}`
      (re-diff-confirmed against current HEAD, not just the 2026-07-22 claim): wired
      `is_defi_force_include_pool`/`DEFI_FORCE_INCLUDE_POOLS` into the IS DEX relevance filter (pool_address carve-out,
      `instruments_service/engine/orchestrator/defi.py`) and the catalogue `_add_force_include` column
      (`scripts/build_instrument_catalogue.py`), plus the orchestrator-package export
      (`instruments_service/engine/orchestrator/__init__.py`) so `_orch.is_defi_force_include_pool` resolves at runtime
      — so the 32 legacy-only high-TVL Raydium pools (incl. XMR/USDC ~$47M, BNB/USDC ~$18M) survive both the relevance
      filter and the catalogue force_include stamp. The REST of `stash@{0}` (Chainlink oracle + Solana-DEX
      venue/factory-adapter WIP, goldens, per-AG target counts) diff-confirmed fully superseded/redundant at HEAD —
      `git apply --check` fails on every remaining hunk, and HEAD's golden `defi.json` tuple_count (234, captured
      2026-07-22) and `_PER_AG_TARGET_COUNTS["DEFI"]` (96) are already strictly ahead of the stash's stale 227/93 — so
      only the 3 force-include hunks moved, nothing else cherry-picked. Added unit test coverage: 3 new tests in
      `tests/unit/test_new_orchestrator.py` (force-include keeps a high-TVL minor-asset pool, case- insensitive match,
      non-allowlisted minor-asset pool still rejected) + 1 new test in
      `tests/unit/scripts/test_build_instrument_catalogue.py` (`_add_force_include` flags a force-include pool by
      address, control pool stays False). `quality-gates.sh` green (sentinel `.qg_last_passed_sha` == HEAD `31d662e1`
      pre-ship), shipped via `quickmerge.sh --agent --files`. Stash cleanup: `stash@{0}` is now fully
      consumed/superseded (post-ship re-diff also fails to apply on every hunk) but `git stash drop` is BLOCKED by the
      orchestrator's destructive-command guardrail for autonomous workers — needs an operator/interactive-session
      `git stash drop stash@{0}` in `instruments-service` to actually clear it. `stash@{1}`
      (`stale-e527a0d7-dockerfile-wip-do-not-ship`) is unrelated/out-of-scope and was left untouched.

- [x] ✅ [DATA] P3. **Orphan-sweep VM monitoring** — `orphan-sweep-defi-20260723-043605` (6th attempt) reached
      ACCEPTANCE 2026-07-23 21:04:37 UTC: `orphan_class_E=15,865,384, unknown_prefixes=8` (full 24,890,959-object walk,
      16h25m). The 8 unknown-prefix objects were fully triaged (test-artifact leak, negligible scale, fixed with a
      general safety net) and the backfill is now in progress — see
      `plans/active/issues/estate_orphan_assessment_2026_07_21.md` todo 3c and
      `plans/active/issues/defi_orphan_sweep_test_artifact_prod_leak_2026_07_24.md` for full detail (the latter also
      documents a related cefi manifest row_count-inflation finding from the same defect class).

- [x] ✅ [DATA] P1. **Fake-history relabel-forward migration script** — checkbox was STALE, work already shipped +
      verified complete. `market-tick-data-service/scripts/relabel_solana_dex_pools_fake_history.py`
      (`market-tick-data-service@67524cbb`, 429-crash fix `@b48a0a4d`, sharding fix `@b9a8b76e`) relabels each of the
      241,281 legacy `data_type=dex_pools` rows (17 days x 2 venues: ORCA + RAYDIUM, 2025-01-01..17) forward to its TRUE
      date (from the row's own `timestamp`, not `available_at`) under canonical `data_type=dex_pool_state` +
      `pipeline_mode=live_onchain_subgraph`, `record_captured`s only the new path, and leaves the old object
      un-recorded + logged to `_index/audit/dex_pools_fake_history_pending_delete.parquet` for human delete review.
      **Full-scale run VERIFIED COMPLETE 2026-07-24 ~12:09 UTC** per
      `issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` todo 3 (all 4 ON_DEMAND VMs exited
      rc=0, sum of objects-processed = 241,281 exactly matching the measured population) — **independently re-confirmed
      2026-07-24** via a fresh `gcloud storage ls` count against the live `-prd-` bucket: `day=2026-05-04` = 14,104
      ORCA + 119 RAYDIUM, `day=2026-05-05` = 14,099 ORCA + 113 RAYDIUM, sum = 28,435, exactly matching the issue doc's
      cited final count. Pending-delete audit parquet confirmed present in GCS. No new script needed — this todo and the
      mirrored verification todo in `defi_track01_per_instrument_and_canon_id_2026_07_24.md` are both being flipped in
      this pass.
- [x] ✅ [DATA] P2. **Get TRUE final fake-history scope** — DONE 2026-07-23 per the issue doc todo 2, superseded by a
      faster independent targeted walk (not the `--source final` path) — proved 17 days x 2 venues (ORCA, RAYDIUM),
      2025-01-01..17, no gaps, nothing beyond this window. See
      `issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` "Scope" section.

- [x] ✅ [DATA] P2. **cefi/prediction timestamp-provenance audit — DONE 2026-07-24.** Sampled prediction's core adapters
      (`kalshi_adapter.py`/`polymarket_adapter.py` — already correct, `available_at = max(tick_ts, market_created_at)`)
      and cefi's primary path (`ccxt_adapter.py` — already correct, derives from `compute_bar_close_boundary`) plus 3
      smaller cefi batch handlers for the exact DeFi-fix defect shape. Found 2 real gaps
      (`deribit_volatility_index_handler.py`, `book_microstructure_handler.py` — wall-clock `available_at` despite an
      already-computed deterministic timestamp in the same function) + 1 weaker dead-code candidate
      (`deribit_options_chain_handler.py`). Filed
      [`issues/cefi_available_at_wallclock_despite_deterministic_row_timestamp_2026_07_24.md`](/plans/active/issues/cefi_available_at_wallclock_despite_deterministic_row_timestamp_2026_07_24.md)
      and routed the code-fix work into `cefi_consolidated_closeout_2026_07_18.md` Track 6 (owning plan — out of scope
      for this defi-plan audit todo). No code changed by this touch.

- [x] ✅ [BACKEND] P3. **`dex_pools_handler.py`'s parallel Solana writer (`_collect_solana_dex`, CLI op
      `collect-dex-pools`) — RESOLVED 2026-07-25, evidence-cited.** Registered + live: `main.py:554`
      (`"collect-dex-pools": DexPoolsHandler`), routed to `_dex_pools_subgraph.py::_collect_solana_dex` for
      kamino/orca/raydium/phoenix on `chain=SOLANA` (`_dex_pools_subgraph.py:312-392`, `:420-421`); confirmed
      structurally cruder than `solana_defi_handler.py` — `row.setdefault("symbol", pool_id_str)` (the raw pool/vault
      address, `:350-354`) vs `solana_defi_handler.py::_solana_row_symbol()`'s real
      `{token_a}-{token_b}-{discriminator}` build (`:390-404`). Scheduler declarations exist in
      `deployment-service/terraform/gcp/` (`defi_collection_scheduler.tf:91-97,154-160` — daily
      `mtds-collect-dex-pools-cron`; `defi_forward_poll_scheduler.tf:67-71` + `variables.tf:38-42` — `*/5` forward-poll,
      `enable_defi_forward_poll` default `true`), but the LIVE production jobs (`uts-prod-mtds-collect-dex-pools-cron`,
      `defi-fwd-dex-pools-poll`/`defi-fwd-dex-swaps-poll`) are currently **PAUSED**, part of the deliberate
      operator-approved "All DeFi capture STOPPED" halt (2026-07-18, re-armed) pending the in-flight per-instrument
      re-architecture — not dead code, not retired, temporarily paused; Terraform still declares both ON by default so
      an unguarded `terraform apply` could silently re-enable them. Structurally immune to the symbol-collision bug this
      todo's sibling worried about (keys by pool ADDRESS, not a derived symbol) — matches the already-closed "Second
      Solana writer" finding in `defi_track01_per_instrument_and_canon_id_2026_07_24.md:658-680`, which this todo failed
      to cross-reference (the real gap, not missing information). No fix required before resume; re-verify PAUSED state
      at resume-time since Terraform's default is ON.

## Progress Log tail — session 3 (2026-07-24) through the 8h-mark checkpoint (2026-07-25) (extracted 2026-07-25, 2nd extraction pass)

> Extracted verbatim from the parent's "Progress Log — condensed" section and its trailing "Deferred work after
> 2026-07-25"/"Lessons from this session"/"8h-mark interim report" sub-sections. The parent's own condensed
> one-line-per-date Progress Log entries (2026-07-18 through 2026-07-24, plus new one-line summaries of the two sessions
> below) are UNCHANGED and stay in the parent — this is the FULL prose those summaries condense, plus the deferred-work
> table, lessons, and interim report that followed them.

- **2026-07-24 (session 3, `/autonomous`, orchestration pass)** — pulled latest across all repos, re-read this plan +
  `defi_track01_per_instrument_and_canon_id_2026_07_24.md` + `defi_lending_writer_retire_prerequisite_2026_07_20.md` in
  full, triaged all ~50 open todos across the three docs into actionable-now / launchable / genuinely-gated. Flipped 4
  stale checkboxes found DONE-but-never-flipped (verified via `git merge-base`/archived-issue-doc checks, not assumed):
  dex_pools/lending_indices legacy fold, Solana AMM symbol-collision fix (`mtds@0d83a8a9`), delete-marker script ship
  (`mtds@a65117eb`), legacy composite-venue investigation (issue filed). Fanned out 9 parallel background agents on
  independent actionable items; 3 hit transient ECONNRESET/network-stall failures mid-task and were resumed via
  SendMessage (2 of those 3 confirmed shipped: `unified-api-contracts@e893e5c9` EXPECTED_SUBGRAPH_DEINDEXED,
  `instruments-service@4e97a82e` is_defi_force_include_pool wiring). **Big finding**: the long-running defi orphan-sweep
  (`estate_orphan_assessment_2026_07_21.md` todo 3, 6th VM attempt) completed with **15,865,384 orphan_class_E rows** —
  larger than cefi+prediction+sports combined — with a caution flag that some fraction is likely leaked test-artifact
  data (`agent-sample-test-jupiter/` prefix sampled), not genuine production gaps; delegated scoped investigation +
  backfill to a background agent, full detail in that issue doc's 2026-07-24 update. **Session interrupted mid-flight**:
  operator is migrating this session to different infrastructure (bandwidth constraints) while 4-5 of the 9 background
  agents were still actively running (line-445 backfill-VM verification, line-761 cefi/prediction audit, the Solana
  symbol-collision closeout naming-doc/second-writer sub-items, the 9-cell ORCA glued-id retry, and the 15.87M-row
  orphan backfill) — their in-flight edits may or may not land depending on whether those background tasks survive the
  migration. Anyone resuming this plan should first `git fetch` + check each repo's recent log for commits past this
  entry's timestamp before assuming any of those 5 items are still open — they may have completed independently after
  this entry was written. If genuinely still open, re-check `gcloud compute instances list` for any
  `backfill-orphan-e-defi-*` / `canonical-migration-defi-pi-range-*` VMs before re-launching anything (avoid a duplicate
  concurrent run). The prod-bucket `_migrated_*` marker delete (`delete_migrated_defi_markers_2026_07_23.py --apply`,
  line ~708) was handed to the operator directly (human-planning VM) this session — check with them before assuming it's
  still pending.

- **2026-07-25 (`/autonomous`, operator stepped away for ~8h)** — continuing the
  `delete_migrated_defi_markers_2026_07_23.py` dry-run (banner above): VM
  `canonical-migration-defi-marker-cleanup-20260724-182226` now runs TWO independent verification processes (shard-a,
  the original supervised run; shard-b, launched separately once SSH confirmed the VM had ~85% idle CPU headroom) to
  roughly double throughput. Each discovers the full 356,391-marker corpus independently and skips whatever is already
  in its OWN resume-log — they do NOT coordinate, so there is bounded, harmless duplicate verification between them;
  both logs get merged+deduped by marker name before the final report. **Honest ETA**: combined rate is ~6/marker-sec
  but each shard's OWN remaining backlog (~230-250k markers each) would take ~20-21h to fully exhaust independently at
  current rate — **this will very likely still be running past the 8-hour window**, not finished. Plan for this session:
  keep both shards running (safe, resumable, SPOT + 2-min GCS resume-log sync on each), do read-only sampling of the
  growing FLAGGED population to characterize root cause per the todo above, and merge+report whatever is done at the 8h
  mark or true completion, whichever comes first. **Queued operator decisions (you were away, so these are queued rather
  than blocking)**:
  1. **`--apply` for the marker delete** — unchanged, still human-only, still queued for you regardless of how clean the
     report looks. Nothing to decide until the report is ready; I will not run it.
  2. **FLAGGED remediation — UPDATE: investigated, decision needed, NOT auto-remediating.** Sampled ~268k processed
     markers via direct parquet inspection (not guessing from counts alone) — full writeup in
     `issues/defi_migrated_marker_flagged_root_cause_clusters_2026_07_25.md`, todo above updated. My earlier plan ("if
     the pattern is unambiguous, re-run migration myself") turned out to be the wrong call once I actually looked at the
     data: it is NOT one simple pattern. GMX perp_funding (~1,896 markers) is 1-row daily aggregates with no
     needs_attribution backup — a design question (should these even split per-instrument?), not a migration bug.
     TRADER_JOE_V2/AVALANCHE dex_pool_state (~944 markers) verified to have a real distinct `pool_id` per row (not
     unattributable) but no symbol resolution — re-running the split migration would NOT fix this, the gap is upstream
     (symbol/pool metadata), confirmed by checking the migration tool doesn't do symbol resolution at all. lst_rates
     (~678 markers) flagged by volume, not yet root-caused. **I am not re-running any `--apply` for any FLAGGED
     cluster** — each needs its own scoped decision from you (see the issue doc's Recommendation section: per cluster,
     accept-as-orphaned vs. backfill symbol metadata vs. further investigation). This replaces my earlier, more
     optimistic framing below (kept for the record, not current guidance):
     - ~~I will characterize a sample (read-only) but will NOT re-run `migrate_defi_batch_to_per_instrument.py --apply`
       against `FLAGGED_ROWCOUNT_SHORTFALL` cells without your sign-off~~ — confirmed: don't, for any cluster, it's not
       a migration-tool problem.
     - ~~If `FLAGGED_NO_SIBLINGS_NO_BACKUP` investigation shows an unambiguous interrupted-run pattern, I'll re-run
       migration for those cells myself~~ — investigated; the pattern is NOT unambiguous/simple, so per my own stated
       bar this stays queued for you rather than auto-remediated.

## Deferred work after 2026-07-25 (`/pre-compact` checkpoint, session context ~67%)

| Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | State / why deferred                                                                                                                                                                                                                                                           | Blocked on                                                                                                              |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| Both dry-run shards finishing their own full backlog                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Cannot be done yet — **updated 2026-07-25 ~10:40 UTC**: 68.2% of the corpus processed (243,111/356,391 deduped, 113,280 remaining), rate steady, VM still healthy. Genuinely time-bound, not blocked on anyone                                                                 | Elapsed time. VM `canonical-migration-defi-marker-cleanup-20260724-182226`, SPOT, still `RUNNING` as of this checkpoint |
| **RESUME-HERE (2026-07-25, operator explicitly asked for this checkpoint): watch for a NEW orphan/venue cluster as the dry-run finishes the remaining ~32%.** Through 68.2% coverage, EVERY FLAGGED marker still falls into the same 12 already-known venues (GMX, TRADER_JOE_V2, VELODROME_V2, CURVE, COINBASE, MAKER, SWELL, ETHENA, HYPERLIQUID, SUSHISWAP, AURORA, UNISWAP_V3) — zero new venues have appeared. To resume: pull both resume-logs (`gs://deployment-scripts-central-element-323112/canonical-migration-defi-marker-cleanup/resume-seed/delete_migrated_defi_markers_2026_07_23.resume{,-b}.jsonl`), dedupe by `marker` key (last-write-wins is fine, disposition is deterministic), tally `disposition` + extract `venue=` from each FLAGGED marker's path, and diff against the 12-venue list above. If still just those 12 (likely, given the pattern held steady from 65.8%→68.2%) — no new investigation needed, the two decided plans already cover it, just update their counts. If a genuinely NEW venue appears — root-cause it the same way this session did (download the marker + a sibling, inspect columns directly with pyarrow, check for a needs_attribution twin) before assuming it needs the same fix as an existing cluster. | Elapsed time (VM still running) — not blocked on anyone, purely a "check again once further along" item                                                                                                                                                                        |
| Merge shard-a/shard-b resume-logs + final SAFE/FLAGGED report                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | Not done — trivial once inputs exist (dedupe by marker name, tally dispositions); the same script as the RESUME-HERE row above produces this                                                                                                                                   | The item above (or true shard completion, whichever comes first)                                                        |
| **NEW (2026-07-25, found by an AO worker, not this session)**: `agent-orchestrator`'s `gate_on_depends` wiring has a THIRD confirmed occurrence of failing to hold — `defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25.md` (a "finalize" companion plan for `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` that this session did NOT author) dispatched a reconciliation todo despite its upstream plan being 0/5 done. The worker correctly refused to fabricate a false-completion claim and filed `issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md` + `/blocked` BLK-0d30dec1 — no harm done, but the platform-level bug is real and recurring (2 prior archived incidents). Not this plan's work to fix (agent-orchestrator repo, `assigned_role: backend_engineer`/orchestrator maintainers) — just flagging so nobody re-discovers it fresh.                                                                                                                                                                                                                                                                                                                                                                       | Operator-owned / agent-orchestrator-team-owned — a platform dispatch-logic bug, not a defi-plan action item                                                                                                                                                                    | See the issue doc's "Recommended decision" section                                                                      |
| `delete_migrated_defi_markers_2026_07_23.py --apply`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Operator-owned — always human-executed, never blocking, nothing to do until the report above exists                                                                                                                                                                            | You, whenever you review the finished report                                                                            |
| GMX perp_funding cluster (~1,896 markers) — should 1-row daily aggregates even go through per-instrument splitting?                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | **RESOLVED 2026-07-25 — moot**: operator decided to remove GMX entirely (synthetic OI-imbalance data, not real funding); see `defi_gmx_venue_removal_2026_07_25.md`. No per-instrument splitting decision needed.                                                              | Closed — see removal plan                                                                                               |
| TRADER_JOE_V2/AVALANCHE symbol/pool-metadata backfill (~944 markers)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Operator-owned — likely instruments-service/URDI territory, real design decision on whether/how to backfill                                                                                                                                                                    | Your call, same issue doc                                                                                               |
| lst_rates cluster root-cause (~678 markers, COINBASE/MAKER/SWELL)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Not done — genuinely open investigative work, time-boxed out this session in favor of the two bigger clusters. NOT blocked on anyone — whoever picks this plan back up can just do it (same method: sample the resume-logs, download a marker + its siblings, inspect columns) | Nobody — pick it up anytime                                                                                             |
| `market-tick-data-service/.gitignore` missing a `*.resume.jsonl` pattern (this exact script's own scratch resume-log dirties the tree and blocked one attempted tarball auto-republish this session — worked around, not fixed)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Not done — small, clear, ~2min fix, deliberately not shipped this checkpoint to avoid a QG+quickmerge cycle while compacting                                                                                                                                                   | Nobody — pick it up anytime, low priority hygiene only                                                                  |

**Recommended next item when this plan is picked back up**: check whether both shards have finished
(`gcloud compute instances describe canonical-migration-defi-marker-cleanup-20260724-182226 --zone=asia-northeast1-c` —
SPOT + `VM_SHUTDOWN_ON_COMPLETION=true` means a `TERMINATED`/absent instance likely means it finished; the resume-logs
at `gs://deployment-scripts-central-element-323112/canonical-migration-defi-marker-cleanup/resume-seed/` are the proof
either way, they don't need the VM alive to read). If done: merge + write the final report + present it, still without
running `--apply`. If still running: it's fine to just keep waiting, nothing else is blocked on it.

### Lessons from this session (would otherwise be relearned)

- **Initial-burst rate is not steady-state.** A fresh dry-run measured ~14 markers/sec in its first 500-batch, but
  settled to ~3-6/sec once past the cheap early-corpus (mostly-zero-row) portion. Don't project an ETA from the first
  few checkpoints.
- **`needs_attribution` fallback objects are often simply ABSENT, not just occasionally missing** — checked several
  specific `day=`/`data_type=` combos directly; the object didn't exist for any of them. Don't assume "SAFE via
  needs_attribution" is a reliably-available path; it's the exception.
- **"Unattributable" (per this tool's definition) ≠ "the data has no identity."** TRADER_JOE_V2 rows had `symbol`/
  `pool_address` NULL but a 100%-populated, genuinely distinct `pool_id` per row. Always check for an alternate
  identifying column before concluding data is truly orphaned.
- **My own earlier optimism was wrong and worth naming**: I initially planned to autonomously re-run the split migration
  for `FLAGGED_NO_SIBLINGS_NO_BACKUP` cells "if the pattern looked unambiguous." Actual sampling showed 3+ distinct root
  causes, none fixable by a blind rerun. Investigate before committing to a remediation plan, even when the operator has
  pre-authorized the general direction.
- **A partial per-slot clone (`.tabs/1`, PM-repo-only) gives a false `disk_absent` dependency-alignment failure** in
  quickmerge's STAGE 1.5 (it expects every sibling repo checked out alongside it) — environmental, not a real problem;
  the docs(plans) direct-push carve-out (path-based, see `check_strict_quickmerge.py`) is the correct route for a
  docs-only change from a partial clone, not a reason to force the full pipeline.
- **YAML frontmatter plain multi-line scalars break on a literal `": "` inside the text** (parsed as a new mapping key)
  — use `" -- "` or rephrase instead of a colon-space when writing issue-doc summaries by hand.

### 8h-mark interim report (2026-07-25 ~09:25 UTC — real elapsed time verified against commit timestamps, not guessed)

Neither shard reached its own full backlog by the 8h mark (each independently needs ~15-20h total at steady rate) — per
the deferred-work table above, produced an INTERIM merged report instead of waiting further, per the operator's "8 hours
or until done" instruction. **Both VM processes are left running unattended** (safe, resumable, SPOT + periodic GCS
resume-log sync) — this is not a stopping point for the actual dry-run, only for this reporting tick.

**Deduped combined progress**: 234,441 of 356,391 markers processed (65.8%), 121,950 remaining.

| Disposition                    | Count     | % of processed |
| ------------------------------ | --------- | -------------- |
| SAFE                           | 230,895   | 98.49%         |
| FLAGGED_NO_SIBLINGS_NO_BACKUP  | 1,935     | 0.83%          |
| FLAGGED_ROWCOUNT_SHORTFALL     | 903       | 0.39%          |
| SAFE_NEEDS_ATTRIBUTION_COVERED | 708       | 0.30%          |
| **Total FLAGGED**              | **2,838** | **1.21%**      |

**Updated cluster breakdown** (refines the counts in
`issues/defi_migrated_marker_flagged_root_cause_clusters_2026_07_25.md` — root causes unchanged, just bigger/cleaner
sample now): GMX perp_funding 952 (476 ARBITRUM + 476 AVALANCHE), TRADER_JOE_V2/AVALANCHE dex_pool_state 784 (610
NO_SIBLINGS + 174 SHORTFALL), VELODROME_V2/OPTIMISM dex_pool_state 586 (SHORTFALL), lst_rates 346 (COINBASE 202 + MAKER
132 + ETHENA 7 + SWELL 5), UNISWAP_V3/ETHEREUM dex_pool_swaps 73 (new cluster, not yet root-caused — small, flagging for
completeness), CURVE/ETHEREUM dex_pool_state 66, HYPERLIQUID perp_funding 27, SUSHISWAP/AURORA misc 4.

**Full FLAGGED list (all 2,838, not just the table above)**: staged to
`gs://deployment-scripts-central-element-323112/canonical-migration-defi-marker-cleanup/reports/flagged_markers_interim_2026_07_25.jsonl`
(one JSON record per marker — path, row counts, sibling info, disposition). This is INTERIM (65.8% of corpus) — the
final report once both shards finish will supersede it; re-running the merge script against the same GCS resume-log
paths produces an updated version at any time, no need to wait for a human to re-request it.
