---
doc_type: plan
title:
  DeFi consolidated close-out — Track 6 (RENDER) + Track 7 (CULL) closed history (forked from the defi consolidated
  close-out plan)
summary:
  Archive-bound history extracted verbatim from defi_consolidated_closeout_2026_07_18.md's 2026-07-25 line-cap
  remediation (parent was 1039 lines against the 1000-line hard cap). Covers Track 6 (RENDER -- data-status surface four
  + restore the enumeration view) and Track 7 (CULL -- purge the removed venues everywhere) in full — both tracks' todos
  are 100% closed (2/2 done in Track 6, 1/1 done in Track 7; 0 open todos across both). Record-only; not intended for
  further action. Track 6's close-out CRITERION (not a todo) is not yet fully met per the parent's own text (a fresh
  distinct-values census must return zero `is_canonical=false` entries) — that residual drive-to-0 work is tracked in
  `defi_track01_per_instrument_and_canon_id_2026_07_24.md`, not as a todo here or in the parent.
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
last_updated: "2026-07-25"
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
    plans/active/issues/plan_line_cap_remediation_2026_07_23.md's FINAL RESOLUTION section).",
  ]
locked_by:
locked_since:
---

# DeFi consolidated close-out — Track 6 + Track 7 closed history

> **Record-only.** This doc is the archive-bound verbatim extraction of two fully-closed tracks from
> [`defi_consolidated_closeout_2026_07_18.md`](/plans/active/defi_consolidated_closeout_2026_07_18.md). Nothing here is
> summarized, rewritten, or condensed — both sections are copied byte-for-byte from the parent as of the 2026-07-25
> extraction. Zero open todos in either track (2 done in Track 6, 1 done in Track 7).

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
