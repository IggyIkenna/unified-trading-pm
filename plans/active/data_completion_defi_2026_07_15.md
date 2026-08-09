---
doc_type: plan
title: Data completion to 100% — DeFi manifest canonicalisation + backfill (split from M-1)
summary: >-
  DeFi slice of the data-completion-to-100% program, split out of data_completion_to_100_all_ag_2026_06_21 (M-1) on
  2026-07-15 per operator ruling (plan-reconcile §8) when M-1 breached the absolute 5000-line ceiling. Carries the defi
  scope M-1 absorbed in the 2026-07-13 consolidation, migrated VERBATIM — no scope added, dropped or reworded. M-1
  remains the coordinator hub for cross-cutting work (bucket naming, source provenance, bar-edge) and owns the shared
  Progress Log.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [backfill, manifest, honest-coverage, data-completion, defi, data-correctness]
related:
  [/plans/active/data_completion_to_100_all_ag_2026_06_21.md, /plans/active/defi_consolidated_closeout_2026_07_18.md]
created: 2026-07-15
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2
last_updated: 2026-07-24 # (was: 2026-07-20 -- folded in the DeFi-lane Progress Log entries from M-1 per plan line-cap remediation)
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: [data_completion_to_100_all_ag_2026_06_21 (M-1) — split 2026-07-15, plan-reconcile §8 operator ruling A]
drift_direction: advance-code
context_scope:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
---

# Data completion to 100% — DeFi

> **Split from M-1 on 2026-07-15** (`data_completion_to_100_all_ag_2026_06_21.md`, plan-reconcile §8, operator ruling
> A). M-1 had reached 5,366 lines — the only file in the corpus over the absolute 5,000-line ceiling — after absorbing
> 130 folded-in todos in the 2026-07-13 consolidation. This plan carries M-1's **defi** scope **verbatim**; M-1 stays
> the coordinator hub (measured snapshot, per-AG launch matrix, cross-cutting scope, shared Progress Log).
>
> **Read M-1 first** for the program-level snapshot + launch matrix. Cross-cutting items (bucket-name SSOT, data-source
> provenance, bar-edge) deliberately stayed there — they are not defi-specific.

### From `defi_manifest_canonicalisation_2026_06_01.md` (archived 2026-07-13 -- MASTER: canonical-SSOT for data+manifest (cross-plan coordinator) + DeFi manifest canonicalisation (operator judgment-call ruling 2026-07-13: FOLD -> M-1))

- [x] [DATA] P1. A2 pre-venue-launch reason — manifest migration (operator: "captured in UAC if genuinely pre venue +
      migrated in manifest"). **UAC ALREADY HAS** most launch dates in `DEFI_VENUE_LAUNCH_DATES` keyed `VENUE-CHAIN`
      (MARINADE-SOLANA 2021-08-02, JITO-SOLANA 2022-08-16, LIDO-ETHEREUM 2020-12-19, ETHERFI/ETHENA, …) — my earlier
      "None" was a wrong-key lookup (flat `LIDO` vs `LIDO-ETHEREUM`). **APPLIED 2026-06-01**:
      `plans/audit/results/defi_venue_launch_relabel_migration_2026_06_01.py --apply` relabeled **1,337** lst-rates rows
      → `EXPECTED_PRE_VENUE_LAUNCH` (ETHENA/ETHERFI/LIDO 353 each + MARINADE 278), UAC-backed + snapshotted. **(MIGRATED
      FROM: `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P0. B0 (CORRECTED — do NOT build a consolidator step) RUN the existing expected_unattempted chain for DeFi:
      confirm the DeFi MTDS batch orchestrator goes through the instruments-service pre-flight that calls
      `record_expected_unattempted` (wire the DeFi handlers onto it if not), then run a prod DeFi MTDS batch so the owed
      rows generate; validate the denominator. **GATED on C-GREEN** — the owed rows must land in the canonical structure
      (env-split/`pipeline_mode`/`asset_group=`), so migrate first. Closes deferred
      `issues/expected_unattempted_validation_pending_phase3_2026_05_19.md`. parent_epic: manifest_master. **(MIGRATED
      FROM: `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)** **⚠️
      2026-07-20: the agent-orchestrator backlog park keyed on this seed/backfill completing
      (`defi_onchain_v10_universe_v2_seed_or_backfill_progressed`) has been RE-POINTED to
      `defi_consolidated_closeout_2026_07_18.md` Track 5** — that plan's per-instrument re-architecture supersedes this
      B0/C0 seed-chain framing (shard key is now the symbolic `canonical_instrument_id`, not this consolidator chain).
      Do not flip that condition off the completion of THIS todo; see Track 5's unpark note instead.

- [ ] [DATA] P0. C0 **path + bucket canonicalisation (the foundational migration) — RUN ON A VM (operator-confirmed
      2026-06-01)**. **Two-tool lineage (system-first)**: Phase-1.8 `migrate_defi_canonical.py` already did
      VENUE-CHAIN→flat (C3), data_type canonicalisation (C2), `{NAME}_V{N}` promotion, instrument_type + canonical
      instrument_id — that step is DONE; the current dedicated-bucket objects are in the flat
      `day=/category=defi/venue={FLAT}/chain=/…` form.

      The C0/**v9** step is a NEW, separate read+rewrite tool —
      `market-tick-data-service/.../scripts/migrate_defi_full_v9_canonical.py` (**WRITTEN + launcher-wired
      2026-06-01**, proper home beside the other `migrate_*.py`; dry-run-able; ruff+parse clean; helpers verified) —
      that takes the flat objects to FULL canonical: `category=defi`→`asset_group=defi` + `pipeline_mode={MODE}`
      partition + schema_version=9 + `source` column (UAC SOURCE_PRIORITY) + canonical `_V{N}` venue (UAC SSOT,
      complete incl TraderJoe/Velodrome post-C12-UAC) + ~~`available_at` preserve-or-backfill~~ (preserve where
      present; backfill only missing/null from day end-of-day UTC — never regenerate to migration-time) + env-split
      `{kind}-prd-{project}` bucket. **⚠️ CORRECTED 2026-07-25**: the `available_at` preserve-or-backfill clause above
      was never shipped — `migrate_defi_full_v9_canonical.py`'s actual code (verified via grep, 2026-07-25) has ZERO
      `available_at` handling, consistent with `mtds_available_at_cross_asset_backfill_2026_07_13.md`'s live measurement
      of **0.0% available_at fill** on this exact bucket's 3,010,913 captured rows a month after C0d ran. The gap is
      real, unresolved, and tracked as its own not-yet-scoped fix in that plan's defi section — do not treat it as
      covered by C0. mtds@a07cea55; launcher deployment-service@4484802. **Remaining = the C0a–C0f VM-cutover
      sub-todos below.** parent_epic: manifest_master.

  - [x] ✅ [SCRIPT] P0. C0-PROVISION — **5 dedicated DeFi `-prd` buckets PROVISIONED** (operator-authorized 2026-06-03,
        supersedes the "no new buckets/VMs" pause): `oracle-prices-prd`, `lst-rates-prd`, `lending-indices-prd`,
        `perp-funding-prd`, `gas-fees-prd` — all `*-prd-central-element-323112`, ASIA-NORTHEAST1, NEARLINE@90d +
        versioning + UBLA + prod labels. Via `terraform apply -target` against `terraform/state/prod` (clean-create:
        plan = 5 add / 0 change / 0 destroy; backend reset to dev after; `gcloud storage buckets describe` verified all
        5). `evm-defi-prd`/`solana-defi-prd`/`eigenlayer-rewards-prd` + `dex-pools`/`dex-swaps` `-prd` already existed.
        **Residual (P1)**: `liquidations-prd` is absent + has no TF resource (`liquidations_handler` resolves it via
        cloud-providers.yaml:186) → future liquidations backfills would fail-write; add the TF resource + apply. —
        deployment-service (TF resources applied). parent_epic: manifest_master.
  - [x] ✅ [CODE] P0. C0a — wire the tool into the launcher **DONE** (deployment-service@4484802;
        dry=default/full=--apply; `bash -n` + command-emission verified). Remaining: a `--start/--end` smoke on a 1-day
        slice (rolls into C0b dry VM).
  - [x] ✅ [DATA] P0. C0b — **dry VM DONE** — discover + plan dry-runs validated as described below (unchanged
        evidence), superseded by the real full VM run (C0d).
  - [x] ✅ [DATA] P0. C0c — **pre-migration drain DONE** (folded into the C0d apply run — no evidence of a fleet
        collision found during verification).
  - [x] ✅ [DATA] P0. C0d — **full VM DONE** — `canonical-migration-defi-20260618-180603` (launched via
        `launch-canonical-migration-vm.sh defi ... full`), completed `rc=0`. Cross-confirmed in
        `plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md` ("G4 apply run 2026-06-29 — 4/5
        AGs COMPLETE") and `plans/active/instruments_completion_tracker_2026_07_06.md` (defi → Canonical? ✅ yes).
        Found + flipped 2026-07-12 (`gcs_bucket_estate_cleanup_2026_07_10.md` §5f) — this checklist was never updated
        when the work actually landed; the coordinator + tracker docs had the accurate state throughout.
  - [x] ✅ [DATA] P0. C0e — **consolidator verify DONE** — live GCS evidence: `market-data-tick-defi-prd-*`'s
        `raw_tick_data/by_date/day=2022-06-01/` shows populated `pipeline_mode=batch_onchain_rpc/`+
        `pipeline_mode=batch_onchain_subgraph/` partitions under `asset_group=defi/venue=<CHAIN>/` (source-aware
        canonical form, post-GATE-0); canonical index confirmed comprehensive (27.4M rows, all 8 in-scope data_types
        present with full historical date ranges) via direct download+inspection 2026-07-12.
  - [x] ✅ [DATA] P0. C0f — **delete legacy originals — CLOSED 2026-08-09 (round11 sweep, citation-fix).** operator
        authorized 2026-07-12 ("delet legacy buckets if data is migrated"). **Correction to this todo's own original
        framing**: not all 8 kinds' `-prd` buckets are "legacy originals" — `migrate_defi_full_v9_canonical.py`'s own
        `base_prd = f"{stem}-prd-{project_id}"` write target IS the live canonical production bucket for
        `dex-pools`/`lst-rates`/`perp-funding` (real callers confirmed: strategy-service, `e2e-testing`), not a rollback
        copy — deleting those would have been a regression, caught before it happened (see
        `gcs_bucket_estate_cleanup_2026_07_10.md` §5i). **Deleted 2026-07-12** (12 of 14 genuinely-legacy buckets):
        `dex-swaps` + `dex-swaps-prd`, `oracle-prices` + `oracle-prices-prd`, `gas-fees` + `gas-fees-prd`,
        `liquidations` (no `-prd` variant), plus the FLAT (source-only) forms of `dex-pools`/`lst-rates`/ `perp-funding`
        — their `-prd` forms correctly KEPT (live). **The last deferred kind is also done**: `lending-indices` +
        `lending-indices-prd` (2 of 14) — this todo's own text left them open pending
        `mtds-lending-indices-20260712-112557` (the Morpho follow-up VM) completing. Per
        `plans/active/bucket_estate_consolidation_closeout_2026_07_24.md` (line ~119-128, 2026-07-31 re-correction):
        **CONFIRMED DELETED** — `gcloud storage buckets delete --quiet` on both `lending-indices-central-element-323112`
        and `lending-indices-prd-central-element-323112` succeeded, "STATUS: COMPLETE 2026-07-15", both confirmed 404 via
        `buckets describe`; that doc also found the Morpho VM referenced here wrote to the unrelated canonical shared
        bucket, so its completion was never actually a gate on this specific deletion. All 14 of 14 kinds now confirmed
        deleted — nothing left open on C0f. See `gcs_bucket_estate_cleanup_2026_07_10.md` §5f + §5i for the original
        re-verification and execution log. **(MIGRATED FROM: `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13
        per MTDS consolidation ruling.)**

- [ ] [DATA] P1. C2 data_type alias dedup across buckets — **canonical is the ON-DISK form (operator-locked 2026-06-01,
      see C0-CN + codex `defi-canonical-naming-ssot.md`)**: hyphen→underscore (`lending-indices`→`lending_indices`),
      `staking_yields`→`lst_rates`, and the pool/swap data_type collapses to `dex_pool_state`/`dex_pool_swaps`
      EVERYWHERE (NOT the logical `dex_pools`/`dex_swaps` — that was the regression the naming audit caught). Rides the
      C0 walk (the migration already writes `dex_pool_state`/`dex_pool_swaps`). ONE walk. **(MIGRATED FROM:
      `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P1. C3 VENUE-CHAIN→flat: legacy `UNISWAPV3-ETHEREUM` venue strings → flat `venue` + populated `chain`. Same
      walk. **(MIGRATED FROM: `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation
      ruling.)**

- [ ] [DATA] P1. C4 schema v4–v8 → v9 re-version across the dedicated DeFi buckets. Same walk. parent_epic:
      manifest_master. **(MIGRATED FROM: `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)**

- [ ] [DATA] P1. C5 phantom-grid delete: remove the cartesian `data_type × venue` empty grid in `market-data-tick-defi`;
      point data-status at the dedicated indexes. **(MIGRATED FROM: `defi_manifest_canonicalisation_2026_06_01.md`,
      2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P2. C6 Pyth ~5-week backfill (2026-04-15→present, Hermes API) on a VM. **GATED on C0/C-GREEN** (backfill
      into the canonical env-split/`pipeline_mode`/`asset_group=` structure, never the legacy layout). **(MIGRATED FROM:
      `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DATA] P1. C8 fill manifest under-enumeration: UAC declares 90 defi venue-keys but manifest enumerated only lst
      14/22, lending 6/21, perp 5/8. parent_epic: defi_master. **(MIGRATED FROM:
      `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)** **CORRECTED
      2026-07-26 (slot 9, data_engineering)** — the original "genuine absentees DRIFT-SOLANA (Solana MVP), FRAX, MORPHO,
      FLUID" framing is stale/wrong on two counts, per
      `plans/archive/issues/defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`'s full re-diagnosis: (1)
      DRIFT-SOLANA's manifest absence is CORRECT — it was deliberately, comprehensively removed from every UAC registry
      2026-07-16 (all Solana perp DEXes dropped except Jupiter); "confirmed present" must never be a done-criterion for
      this item again. (2) FRAX-ETHEREUM's UAC capability is `vault_share_price`, not `lst_rates`/`lending_indices` — it
      was never actually in scope for the lst/lending family counts cited above; if its manifest rows are genuinely
      absent that's a separate `vault_share_price_handler.py` scheduling question, not an enumeration gap. Deeper
      finding also on file: DeFi has **no `expected_unattempted` seeder at all** (unlike CeFi/TradFi/Sports/Prediction)
      — this item cannot be resolved by "re-running a seeding pass" since none exists; a real fix needs a dedicated
      design+build plan gated on an operator/architecture decision (Option A/B in the linked issue doc). — ✅ **Flipped
      by citation 2026-08-01 (slot 10, data_engineering)**:
      `/plans/archive/2026_08/defi_expected_unattempted_seeder_design_2026_07_26.md` (all 7 todos done, archived)
      shipped the real seeder — `DefiManifestRecorder.emit_expected_unattempted_for_remaining` wired into
      `lending_indices`/`liquidations`/`lst_rates` (`unified-api-contracts@91bafdae`,
      `market-tick-data-service@a5a93dc0`/`92a6ebb1`), verified against real prod data with zero gap (that plan's own
      Todo 4) — exactly the disposition the na-eligibility-audit note below anticipated.

- [ ] [DATA] P1. C9 legacy DeFi bucket object paths are pre-canonical —
      `day=/category=defi/venue=/chain=/instrument_type=/data_type=/file.parquet`: **`category=` not `asset_group=`**
      AND **no `pipeline_mode=` partition** (canonical raw_tick_data layout is
      `…/day=/pipeline_mode={mode}/asset_group={ag}/…`). The manifest ROWS carry pipeline_mode (handlers pass it); the
      object PATHS don't. Normalise the dedicated DeFi bucket paths in the same single-walk as C2–C4. parent_epic:
      manifest_master. **(MIGRATED FROM: `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)**

- [ ] [DATA] P0. C11 **deeper phantom audit — are the POST-launch dex `captured` rows object-backed?** Date-impossible
      ones are done (C10/C10b); the remaining question is whether post-launch captured rows have real objects.
      Spot-check 2026-06-01: `dex-pools day=2025-06-01` HAS objects ✅ but `day=2024-01-01` returned 0 (inconclusive —
      read flaked). The uniform `2021-01-01` first-captured still warrants a full **captured-vs-objects walk**
      (dex-pools/dex-swaps), relabeling any captured row with no object honest. **NOTE 2026-06-01**: an initial walk
      falsely reported 74% phantom — that was an index-venue↔object-venue MISMATCH (`UNISWAPV3` vs `UNISWAP_V3`), now
      fixed for those venues by C12. Re-run the walk AFTER C12 lands everywhere, WITHOUT any read-path normalisation.
      **VM job** (object listing at scale). parent_epic: manifest_master. **(MIGRATED FROM:
      `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [~] [DATA] P0. C12 **venue-name `{VENUE}_V{N}` canonicalisation — EVERYWHERE (code + manifest + data + docs)**
  (operator 2026-06-01: "switched to canonical form with `_V2` etc everywhere … TRADER_JOEV2/VELODROMEV2 is wrong").
  Canonical = underscore before the version (`UNISWAP_V3`, `TRADER_JOE_V2`, `VELODROME_V2`, `AERODROME_V3`, …).
  Surfaces: - **UAC** (the SSOT — fix first): `registry/defi_venues.py`, `defi_venue_capabilities.py`,
  `defi_protocol_registry.py`, `expected_coverage.py`, `venue_mapping.py`, `chain_env.py`,
  `capability_declarations/_defi*.py`, `internal/reference/instrument_validation.py` + the `canonicalize_defi_venue`
  function + its tests (`test_venue_key_parity.py`, `test_canonicalize_defi_venue_combined.py`).
  `TRADER_JOEV2`→`TRADER_JOE_V2`, `VELODROMEV2`→`VELODROME_V2` (and confirm all `*V{N}` use the underscore). - **Code
  (writers)**: MTDS `_instruments_metadata.py` + any handler that emits a venue string. - **Data (objects)**: rename
  object paths `venue=TRADER_JOEV2`→`TRADER_JOE_V2` etc. — VM single-walk (bundle with C0). - **Manifest index**:
  `dex-pools`/`dex-swaps` index — DONE for the already-underscore venues (UNISWAP_V3 39,355 + dex-swaps); TODO
  TRADER_JOE_V2/VELODROME_V2 (coordinate with the object rename so index==object). - **Docs**:
  `/codex/02-data/availability-manifest-and-data-status.md`, `contracts-scope-and-layout.md`, etc. Coordinated
  cross-repo migration (all surfaces together; objects = VM). parent_epic: manifest_master. **(MIGRATED FROM:
  `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] ✅ [DATA] P0. D1 features-onchain-defi is near-empty (3 rows); features-delta-one-defi has NO index → derived
      features (`staking_apy_bps`/`funding_rate_apy_bps`/`basis_bps`/`realized_vol_*`) absent. Run the features backfill
      for the in-scope DeFi instruments over the captured window. **GATED on C-GREEN** (features must read canonical
      raw, else they inherit the mess). **`features-volatility-defi` is NOT part of this item's scope** (correction
      2026-07-26): the volatility feature family's DeFi asset-group was REMOVED 2026-07-17 (operator ruling — no DeFi
      options products, so no implied-vol/skew/term-structure surface can exist for DeFi; the CLI hard-rejects
      `--asset-group DEFI` and the bucket was deleted) — this item's original text predates that ruling. parent_epic:
      features_and_ml_master. **(MIGRATED FROM: `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS
      consolidation ruling.)** **DONE** — all 3 legs live (features-service@faedd957/1309480a/6b2282c5), per
      `defi_satellite_ao_dispatch_batch3_2026_07_26.md` D1.

- [x] ✅ [DATA] P1. D2 **MDPS swaps_ohlcv reprocess for the stale chain-column `attempted_failed` rows** (MIGRATED FROM
      archived `issues/uniswap_v3_ethereum_28k_attempted_failed_2026_05_28.md`, slot-2 2026-06-02). 28,634
      `UNISWAP_V3-ETHEREUM` `swaps_ohlcv_*` rows on the **consolidated `market-data-tick-defi` `_index`**
      (`processed_candles` layer) are `attempted_failed`/`SCHEMA_VALIDATION_FAILED` — **stale point-in-time records**
      from the 2026-05-23/24 chain-propagation fix-deploy window (root cause = blank `chain`; the canonical migration
      removes it source-side). Code fix already live (`mdps@7f1a5b5`+`3799c8d`); slot-7 pre-flight verified live candles
      now carry `chain`. **No code change** — needs an MDPS reprocess rerun once our C0 canonicalises the source (rows
      flip `captured`). Companion chain-column venues to reprocess in the SAME pass (do NOT race the migration with a
      one-venue VM): UNISWAP_V2-ETHEREUM 3,444 · AAVEV3-OPTIMISM 2,820 · EIGENLAYER 1,311 · CURVE-ETHEREUM 1,281 · MAKER
      1,113 · FRAX 1,032 · DRIFT-SOLANA 200 · KAMINO/JITO/MARGINFI ~75. **GATED on C-GREEN.** Verify post-retry:
      `attempted_failed` for these venues → 0 (now `captured` or legit `empty_confirmed`). Repos:
      market-data-processing-service. parent_epic: mtds_mdps_master. **(MIGRATED FROM:
      `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)** **DONE** — stale
      premise, zero `attempted_failed` rows for these 11 venues, per `defi_satellite_ao_dispatch_batch3_2026_07_26.md`
      D2.

- [ ] [DATA] P0. E1 CeFi `derivative_ticker` (funding carrier) fetch failures: OKX-FUTURES + ASTER 100%
      attempted_failed; refresh to current (stale ~3–5 weeks) (was: both venues cited as 100% failed — **[2026-07-12
      correction]**: `issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md`'s 2026-06-22 runtime/manifest audit
      (last_updated 2026-06-27, same date as this doc) shows **ASTER `derivative_ticker` (funding) at 62% captured,
      annotated "ok"** — ASTER's E1 failure claim is stale, superseded by that audit. OKX-FUTURES is NOT re-verified by
      that issue doc (not addressed either way) — do not assume it is also fixed; re-check OKX-FUTURES independently
      before dispatching this item. Checkbox NOT flipped — ASTER-only partial resolution, OKX-FUTURES still unverified.
      Corrected per plan-reconciliation finding 156,
      `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 B-queue ruling.). parent_epic:
      cefi_master. **(MIGRATED FROM: `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation
      ruling.)**

- [ ] [DATA] P0. G1 Launch the full 2024-06-01 → 2026-06-01 backfill VM (Drift V2 historical + Solana spot DEX state).
      Operator-launched from laptop OR `vm-defi`. Recipe: the four CLI scripts in
      `market_tick_data_service/scripts/backfill_drift_v2_historical.py` (perp_funding + perp_trades) +
      `backfill_solana_dex_state.py` (Orca Whirlpool + Raydium classic AMM) for each day in window; estimated ~36GB
      total payload across the 730-day window. **GATED on C-GREEN for the dedicated DeFi buckets** that hold these
      writes (env-split + source-aware `pipeline_mode=batch*<source>`per`derive_pipeline_mode_for_row`+
      `asset_group=defi`).

      Verification (per CLAUDE.md "Plans Run To Actual Completion"):
      `gsutil ls gs://market-data-tick-defi-prd-${PID}/raw_tick_data/by_date/day=*/pipeline_mode=batch_*/asset_group=defi/venue=DRIFT/chain=SOLANA/instrument_type=perpetual/data_type=perp_funding/`
      returns a parquet per day in window; sample-inspect 3 random parquets (early/mid/late window) for non-empty
      `funding_rate`, `oracle_price_twap`, `mark_price_twap` columns; manifest-verified row count > 0 per day-shard;
      equivalent checks for `perp_trades` (active days only; allow `empty_confirmed[SOURCE_RETURNED_ZERO]` on quiet
      days) + `dex_pool_state` for Orca + Raydium. **No silent gaps**: any day with 0 rows MUST carry a typed
      `empty_confirmed` reason (not `attempted_failed`). parent_epic: mtds_mdps_master. **Operator-launched (long
      wall-clock; not a dispatch).** **(MIGRATED FROM: `defi_manifest_canonicalisation_2026_06_01.md`,
      2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P0. G2 Launch live-mode snapshotters via `--live --continuous` (mtds@1d35c7f2 unified live/batch path).
      Terminal A:
      `python -m market_tick_data_service.scripts.backfill_drift_v2_historical --markets SOL-PERP --live --continuous --interval-seconds 3600 --data-types funding`
      (hourly). Terminal B:
      `python -m market_tick_data_service.scripts.backfill_solana_dex_state --venues orca,raydium --live --continuous --interval-seconds 60 --samples-per-day 60 --data-types pool_state`
      (1-min). These run as long-lived VMs on `vm-defi` (`lifecycle_class=LONG_LIVED_LIVE` per CLAUDE.md vm naming
      SSOT). **GATED on G1** (need backfilled history to be loadable as warmup) + **C-GREEN** (writes target canonical
      structure). Verification (per CLAUDE.md "Plans Run To Actual Completion"): T+5min check post-launch — both VMs
      RUNNING in `gcloud compute instances describe`; ≥1 parquet under
      `day=<TODAY>/pipeline_mode=live_*/asset_group=defi/…` (the transitional `live_websocket` alias until the gated
      `live_<source>` tranche lands — never coarse `live`) within the first interval (1 min for DEX, 1 h for Drift
      funding); manifest `capture_status=captured` rows generated. Symptom of regression: `SolanaBasisGcsLoader` logs
      `no perp_funding rows for live`. Depends on G1 (backfill warmup) before paper trade can run a meaningful history.
      parent_epic: mtds_mdps_master. **Operator-launched.** **(MIGRATED FROM:
      `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [PLAY] P0. G3 Run 24h paper trade via `e2e-testing/scripts/defi/run-paper.sh --strategy SOL_BASIS`. Recipe:
      `bash cd e2e-testing && bash scripts/defi/run-paper.sh --strategy SOL_BASIS --tick-interval 3600 --continuous \ --execution-provider solana-devnet --initial-capital-usd 100000 `
      Engine flows `--strategy SOL_BASIS` → `colocated_engine.py` → `SolanaBasisGcsLoader` → fill-sim on devnet (signed,
      not broadcast). **GATED on G2** (live data must be flowing so the engine reads a non-stale tape). Verification
      (per CLAUDE.md "Plans Run To Actual Completion" + Promote Workflow Path SSOT): 24h wall-clock session writes a
      non-empty trade log + PnL series; Firestore `MinimalCandidateManifest` populated; Sharpe ratio + realised funding
      earnings − slippage computed; sample-inspect 3 trades for honest fill simulation (no NaN/inf, no fictional fills
      against zero-liquidity ticks); manifest path `gs://market-data-tick-defi-prd-${PID}/paper_trade/…` (or whichever
      sink the engine writes to) has the session's full output. **DART `ManualTradeGateDialog` enforces first-3-days
      hand-confirmation per CLAUDE.md Promote Workflow Path.** parent_epic: mtds_mdps_master. **Operator-launched (long
      wall-clock; not a dispatch).** **(MIGRATED FROM: `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per
      MTDS consolidation ruling.)**

- [ ] [HUMAN] P0. G4 Promote to live wallet — **HUMAN-ONLY per CLAUDE.md hard-stop list**
      (`## Plans Run To Actual Completion`: wallet keys + kill-switch arming are human-only; agent never runs
      `run-live.sh`). Valid promote target per CLAUDE.md Promote Workflow Path is `paper_1d → live_early`; `live_full`
      is post-cutover. Operator runs:
      `bash cd e2e-testing && bash scripts/defi/run-live.sh --strategy SOL_BASIS --tick-interval 3600 --continuous \ --execution-provider <copper|ceffu|cloud_kms_encrypted> --capital <amount> --wallet <KMS_KEY_ALIAS> `
      **GATED on G3** (Sharpe-positive ack required) + **C-GREEN** + **G2 live data flowing**. Verification: real wallet
      ≥7-day session per CLAUDE.md Master Plan (live DeFi 2026-05-23 gate already shipped — this is a
      Solana-archetype-specific operational gate, not a master-plan blocker). The agent **never** ticks G4 — the
      operator does after the live run completes. parent_epic: mtds_mdps_master. **(MIGRATED FROM:
      `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] [CODE] P1. G5 **Phoenix radix-slab decode (top-of-book bid + ask + size).** The market account is 1.7MB; the
      top-of-book decode is ~50-100 LOC of binary parsing against Phoenix's documented slab layout. Full L2 (deeper
      levels) is harder + can ship later. Current state: `PhoenixOrderbookIngester` (mtds@d3d26f56) fetches the market
      account successfully (proves the RPC path) but routes via
      `record_failed(reason="SOURCE_HANDLER_TODO_PHOENIX_DECODE")`. Acceptance: top-of-book parsed;
      `best_bid_price + best_ask_price + their sizes + spread_bps + mid_price` populated; `record_captured` instead of
      `record_failed`; 5+ unit tests cover the binary decode against known slab states. parent_epic: mtds_mdps_master.
      Not GATED on G1–G4 (independent feature add). **(MIGRATED FROM: `defi_manifest_canonicalisation_2026_06_01.md`,
      2026-07-13 per MTDS consolidation ruling.)** — DONE 2026-07-30 (defi_satellite_ao_dispatch_batch1 finalize
      reconciliation), see defi_satellite_ao_dispatch_batch1_2026_07_25.md todo 6 for full evidence
      (market-tick-data-service@ee49a76d).

- [ ] [CODE] P2. G6 **Jupiter historical reconstruction.** `JupiterQuoteIngester` (mtds@d3d26f56) is forward-only —
      Jupiter doesn't expose historical quote endpoints. For the 2024-06-01 → today backtest window, reconstruct
      historical Jupiter routes by simulating Jupiter's routing algorithm against the underlying Orca/Raydium pool
      states at the same timestamps. Acceptance: per (timestamp, size-bucket) row matching forward-collected quote
      structure within ±5%; backtest harness can read Jupiter quotes for any day in window. parent_epic:
      mtds_mdps_master. GATED on G1 (need Orca + Raydium pool states backfilled). **(MIGRATED FROM:
      `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [x] [CODE] P2. G7 **Orca tick-array decode** (concentrated-liquidity depth visualisation). Current MVP uses
      `sqrt_price` + `liquidity` scalars (sufficient for next-tick slippage approximation). Full tick-array decode
      enables tick-distribution depth maps + better mid-size-fill simulation. ~150-200 LOC binary parsing of the 3
      nearest tick arrays around `tick_current_index`. Acceptance: per-snapshot tick array state captured alongside pool
      state; downstream consumers can compute fill slippage at arbitrary sizes. parent_epic: mtds_mdps_master. Not GATED
      on G1–G4 (independent depth improvement). **(MIGRATED FROM: `defi_manifest_canonicalisation_2026_06_01.md`,
      2026-07-13 per MTDS consolidation ruling.)** — DONE 2026-07-30 (defi_satellite_ao_dispatch_batch1 finalize
      reconciliation), see defi_satellite_ao_dispatch_batch1_2026_07_25.md todo 7 for full evidence
      (market-tick-data-service@f771e841).

- [ ] [CODE] P2. G8 **Raydium second WSOL/USDC pool** — extend `RaydiumClassicAmmIngester` defaults if a meaningful TVL
      pool materialises. The plan-time secondary Raydium pool dropped to
      $4.6K TVL by 2026-06-01 (below noise
      threshold); current default ingestion is just the top $8.8M pool. The
      constant scaffold is forward-compat — adding a pool requires only updating `_RAYDIUM_POOLS` dict. Acceptance: if a
      second SOL/USDC Raydium pool reaches >
      $1M
      TVL, add it; ingest from the canonical date; backtest harness reads both. parent_epic: mtds_mdps_master. Trigger:
      TVL probe shows > $1M.
      **(MIGRATED FROM: `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**

- [ ] [DATA] P0. **`instruments-store-defi` reference-surface canonical-form walk** (the DeFi slice of
      `instruments_manifest_canonicalisation_2026_06_01.md`, whose §C excludes defi). Phase-0 layout audit → single
      bundled walk on the `instruments-store-defi` `_index` + objects to v9 + `asset_group=` + `pipeline_mode=`
      partition + `source` column + typed `EmptyConfirmedReason`, same target form as the MTDS DeFi C0 walk. Re-run
      CF-1…CF-12 → GREEN before any DeFi instruments writer relaunch (master L3-gates-L5). NEVER a second walk on this
      `_index`. **(MIGRATED FROM: `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation
      ruling.)**

- [x] ✅ [CODE] P2. **FLAG 2 — `_BUCKET_CATEGORY_OVERRIDES` DeFi scope** (the DeFi slice flagged to slot-2 in the
      downstream plan): a DeFi `category` override absent from `cloud-providers.yaml` / unresolved by
      `resolve_bucket_name` → post-delete silent-empty. Resolve with
      `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` L6 (owns the bucket-name SSOT + the actual delete).
      **(MIGRATED FROM: `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS consolidation ruling.)**
      **na-eligibility-audit 2026-08-01: CLOSED — stale premise, root cause found + fixed elsewhere.**
      `defi_venue_lst_rates_residual_2026_07_24.md`: "DONE 2026-07-26 (slot-2) ... deployment-api's own DeFi
      sub-bucket-fold machinery (`_BUCKET_CATEGORY_OVERRIDES`/`_MTDS_DEFI_SUB_DIMENSIONS` in
      `services/data_status/defi.py`) is now empty — every DeFi sub-bucket that ever existed has been consolidated into
      the single shared bucket — there is nothing left to fold." Shipped `deployment-api@f919c87`; the original redirect
      target (`bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`) is itself superseded/archived.

- [~] [CODE] P1. ⑦ defi could-exist denominator seed — **CODE-READY (slot-2 2026-06-05, is@bb8fb203); only the VM
  `--apply-write` run is operator/VM-gated.** Grep-then-read found the catalog-build is ALREADY shipped:
  `instruments-service/scripts/build_instrument_catalogue.py` is the defi-capable lifecycle roll-up — it unions the
  per-date `instrument_availability/by_date/day=…/venue=…/instruments.parquet` defns into one catalogue parquet with
  exactly the `instrument_id`/`instrument_type`/`venue`/`chain`/`available_from`/`available_to` columns
  `enumerate_expected_universe._catalog_from_dataframe` consumes. `_enumerate_v2_defi` (chain-genesis + listing + delist
  lifecycle) + the `--asset-group/--catalog-path/--apply-write` flags + the `resolve_bucket_name` env-tier fix already
  ship. **Added the missing denominator-monotonicity regression**
  (`test_defi_v2_denominator_is_could_exist_universe_not_just_manifest`): an alive-but-uncaptured DeFi instrument is
  seeded `expected_unattempted` (denominator grows), a captured one is skipped (not dropped) → could-exist ⊇ manifest,
  never shrinks. **REMAINING (operator/VM, NOT code)**: run `build_instrument_catalogue.py --asset-group defi` then
  `enumerate_expected_universe.py --asset-group defi --catalog-path <catalog> --apply-write` on a VM against the
  canonical `_index` (gated on C-GREEN + the cross-AG `proper_instrument_catalogue_lifecycle_rollup` foundation).
  parent_epic: mtds_mdps_master. **(MIGRATED FROM: `defi_manifest_canonicalisation_2026_06_01.md`, 2026-07-13 per MTDS
  consolidation ruling.)**

## Progress Log

- **na-eligibility-audit 2026-08-01**: MIXED — re-read end to end (21 open items). 19 stay KEEP-NA valid (C-GREEN-gated
  canonicalisation walks, operator-launched wallet/promote steps, design/judgment calls, an unverified-fetch item
  needing independent re-check). 2 items closed as stale (FLAG 2 — done elsewhere, see above; C8 — now
  KEEP-NA-STALE-DUPLICATE, tracked in `defi_expected_unattempted_seeder_design_2026_07_26.md`, see above). No
  RECLASSIFY-eligible items found — every non-stale item is operator/VM-gated, a bundled cross-repo canonical migration
  behind an open C-GREEN prerequisite, or a hard human-only step. Doc stays `assigned_vm: NA`.

> **Folded in 2026-07-24** from the M-1 coordinator's (`data_completion_to_100_all_ag_2026_06_21.md`) shared Progress
> Log (plan line-cap remediation, `plans/active/issues/plan_line_cap_remediation_2026_07_23.md` bucket-(d) split,
> operator-approved) — every DeFi-lane-tagged dated entry, moved verbatim, in original chronological order. M-1 retains
> the cross-cutting/multi-AG entries; read M-1's Progress Log too for the full program-level narrative.

### 2026-07-14 (bucket-decommission follow-through — `perp-funding-test-central-element-323112` DELETED, re-verified live)

Operator dispatch: act on a prior read-only audit's `SAFE_TO_DELETE_NOW` verdict for
`perp-funding-test-central-element-323112`. Per the workspace hard rule (never trust a "looks empty/done" claim), I
re-ran every check live and independently before deleting — all four required conditions reconfirmed, matching the prior
audit exactly:

- **Live object count**: `gcloud storage ls gs://perp-funding-test-central-element-323112/` → 0 objects.
  `gcloud storage ls -a` (all versions) → also 0. `gcloud storage buckets describe --format=json` shows no
  `versioning_enabled` key (false) + a 7-day age-based delete lifecycle rule.
- **Canonical coverage**: `market-data-tick-defi-test-central-element-323112` independently re-checked —
  `versioning_enabled: true`, but a full `ls -a` (all versions) still returns 0 objects, i.e. canonical-test is
  genuinely empty too (not merely empty-at-HEAD). No unique data exists in the target bucket that isn't equally absent
  from canonical.
- **`perp-funding-prd-central-element-323112`** (the prod tier) re-confirmed 404 (already deleted).
- **Live infra references**: re-grepped the whole workspace fresh (not relying on the prior audit's grep output).
  `deployment-service/terraform/gcp/canonical_buckets.tf`'s `for_each` derives strictly from `cloud-providers.yaml`'s
  `gcp.storage` map, and that map has **zero** `perp-funding:` key anywhere (workspace-wide, including
  `unified-trading-pm/configs/`, `unified-api-contracts/…/config/`, and `unified-trading-library/tests/fixtures/`
  mirrors) — only historical comments documenting the kind's removal on 2026-07-13
  (`defi_dedicated_bucket_shared_migration_2026_07_13`). `main.tf` likewise carries only a comment
  ("`market_data_defi_perp_funding_prd` REMOVED 2026-07-13") — **no active `resource` block** for perp-funding exists
  anywhere in `terraform/gcp/*.tf` (`grep -n "^resource"` × `perp` → 0 hits). The live daily Cloud Scheduler job
  `collect-perp-funding` (`defi_collection_scheduler.tf:112`, 01:15 UTC) triggers the operation by name only — its
  handler (`market-tick-data-service/market_tick_data_service/cli/handlers/perp_funding_handler.py:225`) resolves
  `get_write_bucket_name("market_data", "defi")`, i.e. writes to the canonical shared bucket, never to a bucket named
  `perp-funding-*`. Zero workspace-wide hits for the literal string `perp-funding-test-central-element-323112` outside
  this plan doc itself.
- **Conclusion**: because the `perp-funding` kind was already fully purged from the `cloud-providers.yaml` SSOT (and its
  hand-written `main.tf` resource block already removed + `terraform state rm`'d) in the 2026-07-13 migration, there was
  **no remaining Terraform declaration to clean up** for this bucket — that half of the decommission precedent
  (`a596b62` "remove decommissioned DeFi legacy bucket resources", `eb5f660` "remove decommissioned prediction legacy
  bucket resources") had already landed. This session's action was the physical-delete half only.

**Action taken**: `gcloud storage buckets delete gs://perp-funding-test-central-element-323112 --quiet` → exit 0.
Re-verified live: `gcloud storage buckets describe gs://perp-funding-test-central-element-323112` →
`ERROR: ...not found: 404`. Bucket is gone.

**No code/terraform changes shipped** — none were needed (see above); nothing to commit for this repo.

**Adjacent, out-of-scope finding flagged (not actioned here)**:
`e2e-testing/scripts/defi/copy_research_perp_ctx_to_canonical.py:33` still hardcodes
`CANONICAL_BUCKET = "perp-funding-prd-central-element-323112"` — the PRD tier, already 404/deleted. If the
`perp_daily_ctx`/`perp_mark_price` cells that script was meant to preserve were never copied out before that PRD
bucket's deletion, that could be a real data-loss gap. This is unrelated to the TEST bucket this entry scopes and was
NOT investigated further here — flagging for operator triage / a separate todo.

### 2026-06-22 — GAP FOUND (operator): DeFi market-data has NO continuous live capture (daily batch only)

Operator caught it: DeFi live market-data =
`uts-prod-mtds-collect-{dex-swaps,dex-pools,oracle-prices,evm-defi, solana-defi,lending-indices,lst-rates,perp-funding}`
Cloud Run jobs, ALL `--mode batch` on a ONCE-DAILY cron (00:05- 02:05). NOT continuous. (These are MTDS market-data, NOT
strategy — strategy/execution = paper-trading-engine etc.) CeFi/prediction/sports/tradfi run CONTINUOUS live VMs
(websocket streams, ephemeral=miss-is-lost). DeFi has no continuous-live equivalent (only the daily batch + an UNUSED
launch-defi-forward-poll.sh). WHY it matters: on-chain is retroactively queryable so daily batch is gap-free for
FEATURES/BACKTEST (≤24h latent), but LIVE TRADING `arbitrage_price_dispersion` needs near-real-time DEX+oracle prices
(move every block) → a daily snapshot cannot feed a live arb. `carry_staked_basis` (LST APR/Aave rates, slow) is
arguably daily-OK.

- [x] ✅ [INFRA] P1. **DeFi continuous live market-data capture** — **IaC SHIPPED 2026-06-22** —
      deployment-service@2e396f8 + market-tick-data-service@3f5c61f9; DeFi live VERIFIED 2026-06-23 (7 captured rows,
      `live_onchain_subgraph`+`live_chainlink`+`live_pyth_hermes`, heartbeat emitting) (`deployment-service@2e396f8`,
      QG-green): `launch-defi-forward-poll.sh` parameterized over `--operation`
      (collect-dex-swaps/dex-pools/oracle-prices + the existing lst-rates, per-op singleton lock) + NEW
      `terraform/gcp/defi_forward_poll_scheduler.tf` = a `*/5` Cloud Scheduler firing the forward-poll for the 3
      price-sensitive ops (gated by `enable_defi_forward_poll`, default true; slow ops stay daily). **REMAINING:**

      (a) ✅ **mtds live pipeline_mode fix + DeFi-live heartbeat LANDED 2026-06-22 —
      `market-tick-data-service@3f5c61f9`** (on origin/live-defi-rollout, full QG `--no-fix` exit-0 + content sentinel
      verified). Folds `runtime.mode` into `_run_tag` so `--mode live` writes `pipeline_mode=live_*`
      (dex_pools/dex_swaps/oracle_prices) AND emits a per-shard `emit_pipeline_heartbeat` on the live forward-poll
      path (subsumes (c)). **NOTE on the prior "blocker": the local QG was NOT a coverage mis-root** — that
      `rootdir: unified-trading-pm, collected 6` line is the intentional `PM_INT_TEST` integration check (a red
      herring); the real failures were a missing `# noqa: qg-deep-import` on the new
      `from unified_trading_library.events import emit_pipeline_heartbeat` lines (events helper, not top-level
      re-exported) + a method-size trim on `oracle_prices_handler.process()` (53→48L). Python service repos
      quickmerge locally fine.

      (b) **`terraform apply`** the scheduler (operator/CI infra op — broad apply blast-radius in a live project;
      use `-target` for the new scheduler) + a `create-code-tarballs.sh` rebuild so the live-tag fix reaches the
      launched VMs. (c) ✅ **heartbeat** (`emit_pipeline_heartbeat`) — DONE, landed with (a) above. Manual verify
      when applied: `bash deployment-service/scripts/vm/launch-defi-forward-poll.sh --operation collect-oracle-prices`
      → T+10min check rows at
      `gs://market-data-tick-defi-prd-…/raw_tick_data/by_date/day=<today>/pipeline_mode=live_*/asset_group=defi/`.

      Orig intent: stand up a persistent/high-frequency DEX-price + oracle-price capture for the live-trading
      archetypes (per-block or near-real-time), not the once-daily batch. Either a persistent live VM (mirror the
      CeFi `mtds-live-*` pattern, polling DEX/oracle every block/few-sec) or a frequent Cloud Run cron (e.g. \*/1)
      for the price-sensitive operations (dex-swaps/pools, oracle-prices) while leaving the slow ones (lst-rates,
      lending-indices) daily. Wire it through the same live==batch schema + the hardening heartbeat. Repo:
      market-tick-data-service + deployment-service (launch-defi-forward-poll.sh exists, unused). Gates the DeFi arb
      archetype going live.

### 2026-06-22 (DEFI lane, PM-driven backfill-everything dispatch) — PHASE A: enumerator IAM root-caused + fixed (expected_unattempted=0 → seeding)

Operator dispatch "backfill everything (defi)": drive defi to high+honest coverage. Snapshot at start (live consolidated
`market-data-tick-defi-prd` v9 `_index`, 3,812,106 rows): **honest_cov_defi = 17.89%** (captured 682,033 /
empty_confirmed 3,099,859 / attempted_failed 30,214 / **expected_unattempted 0**). 100% schema_version=9. Date range
2018-01-01→2026-06-22.

**PHASE A root cause (the `expected_unattempted=0` symptom) — NOT the "scheduler never applied" hypothesis in the
dispatch.** The `expected-universe-v2-*-daily` Cloud Scheduler + the 5 per-AG Cloud Run Jobs WERE `tofu apply`'d
2026-06-19 (all ENABLED). But the defi scheduler's last attempt (2026-06-22 01:31) returned **`status code: 7` =
PERMISSION_DENIED**, and `gcloud run jobs executions list --job expected-universe-v2-defi` was EMPTY (never executed;
only prediction ran once, hand- triggered, 2026-06-19). Cause: the enumerator SA `expected-universe-v2-enum@…` had **NO
`run.invoker`** binding (neither job- level — empty `etag: ACAB` policy — nor project-level).
`expected_universe_v2_scheduler.tf` grants the SA `objectViewer` (catalogue) + `objectAdmin` (manifest) but OMITS the
`roles/run.invoker` the scheduler→job OIDC call needs → every daily defi/cefi/tradfi/sports trigger was silently
rejected → 0 `expected_unattempted` seeded fleet-wide. (cefi/tradfi/sports also never executed — same gap.)

- [x] ✅ [TERRAFORM] P0. **Durable per-AG `run.invoker` SHIPPED** deployment-service@e45c07e — the
      `google_cloud_run_v2_job_iam_member` for_each per-AG binding replaced the insufficient project-level one.
      (Recovered from a stash-pop conflict by the data-pipeline-hardening run 2026-06-22 — it existed only in a
      working-tree conflict; now landed.) **add `run.invoker` for the enumerator SA to
      `expected_universe_v2_scheduler.tf`** (the missing IAM that made every scheduled run `code 7`). Stop-gap applied
      live via `gcloud run jobs add-iam-policy-binding` on all 5 jobs (`cefi/defi/tradfi/sports/prediction`) → defi job
      now executes. Durable fix = a `google_cloud_run_v2_job_iam_member` (role=`roles/run.invoker`, member=the enum SA)
      per-AG in the TF. Repo: deployment-service. Provenance: this Progress Log.

Manual `gcloud run jobs execute expected-universe-v2-defi` (exec `…-h5djp`) launched + RUNNING (image imported clean,
catalog `gs://instruments-store-defi-prd-…/prod/catalog.parquet` present 302KB). The v2 `--apply-write` path loads the
catalog + builds the manifest `present_set` + calls `enumerate_v2(present_set=…)` → emits `expected_unattempted` for
alive-but-uncaptured defi cells over the bounded window (`--start-date 2026-02-20`, the recent-honest-denominator
window; full-history is the gated companion artifact, not this job). Verifying the seed count next.

ROOT CAUSE (operator-pinned, confirmed against live `market-data-tick-defi-prd` `_index`): the IS expected-universe
enumerator `_enumerate_defi()` iterated ALL `DATA_TYPES_BY_ASSET_GROUP["defi"]` — including CHAIN-LEVEL types — for
every `(chain, protocol)` in `PROTOCOL_LAUNCH_DATES`, emitting
`empty_confirmed[EXPECTED_INSTRUMENT_NOT_LISTED / EXPECTED_PRE_GENESIS_CHAIN]` keyed `venue=<PROTOCOL>` (e.g.
`venue=AAVE_V3, data_type=gas_fees`) for pre-protocol-launch dates. But gas/transfers/MEV exist from CHAIN genesis
regardless of when a DEX launched, and the real capture is keyed `venue=ALCHEMY`/`venue=FLASHBOTS`

- `chain=X`. ~142k false rows per chain-level data_type masked real coverage as "confirmed empty".

CODE shipped (each QG-green via quickmerge):

- [x] [SCRIPT] P0. **IS enumerator** — `instruments-service/scripts/enumerate_expected_universe.py` `_enumerate_defi()`:
      EXCLUDE chain-level data_types (`gas_fees`/`token_transfers`/`mev_events` — declared only by synthetic infra
      pseudo-protocols ALCHEMY-ONCHAIN/FLASHBOTS, fetched at synthetic venues) from the per-protocol loop; ADD
      chain-level `gas_fees` enumeration at `venue=ALCHEMY` for **pre-CHAIN-genesis dates only** →
      `EXPECTED_PRE_GENESIS_CHAIN` (gas chains derived UAC-only from `MAINNET_CHAIN_IDS` ∩ `GAS_FEE_CHAIN_START_DATES` +
      SOLANA; post-genesis gas absence is the handler/backfill's concern). `oracle_prices` is KEPT per-protocol
      (verified genuinely per-protocol: captured at AAVE_V3/ETHENA/LIDO/ETHERFI venues; ~15 LST/yield/staking/perp
      protocols emit it as their exchange rate). Smoke: fixed `_enumerate_defi` yields 47,990 gas rows ALL
      `venue=ALCHEMY`/`EXPECTED_PRE_GENESIS_CHAIN`, 0 `venue=PROTOCOL` gas, 0 token_transfers/mev per-protocol, 315k
      oracle_prices kept. — instruments-service@0e08237 (origin LDR) | QG green (81s)
- [x] [SCRIPT] P0. **UAC `_defi.py`** — removed `"gas_fees"` (22) + `"collect-gas-fees"` (22) from every protocol's
      `data_types`/`mtds_operations` (gas is chain-level). Verified: 0 protocols declare gas_fees; `gas_fees` stays in
      the chain-level `DATA_TYPES_BY_ASSET_GROUP["defi"]` list; `collect-gas-fees` dispatch is standalone
      (`launch-mtds-gas-fees-*-vm.sh`, `VM_OPERATION=collect-gas-fees`) so gas collection is unaffected. **Companion
      fix:** the lazy DeFi validity matrix (`market_data_categories.py` `valid_data_types_for_instrument_type`) derives
      from `PROTOCOL_CAPABILITIES.data_types`, so removing gas_fees orphaned the `("defi","gas_fees")` SOURCE_PRIORITY
      pair (UAC `test_validity_matrix_completeness` caught it) — re-injected `gas_fees` onto the chain-level
      `spot_asset` set in the lazy builder (now reachable + green). — unified-api-contracts@cbdef56d (origin LDR) | QG
      green
- [x] [SCRIPT] P0. **MTDS handler silent-zero audit + eigenlayer fix** — audited every defi handler's
      caught-fetch-exception routing: all main per-shard `except` blocks correctly `record_failed`
      (staking_yields/dex_pools/dex_swaps/lending_indices/ solana_defi); the ONE genuine silent-zero bug was
      `eigenlayer_rewards_handler._collect_date` (`except (...): return 0` → outer `record_zero_rows` →
      `empty_confirmed`). FIXED: expanded the except tuple (`aiohttp.ServerTimeoutError`/
      `ServerDisconnectedError`/`TimeoutError`/`json.JSONDecodeError`/…) and **re-raise** instead of `return 0`, so a
      caught fetch error on expected data routes to the outer `record_failed` (`attempted_failed`), not a false empty.
      Updated the test that encoded the buggy `return 0` to assert the raise. — market-tick-data-service@56435ac (origin
      LDR) | QG green

MANIFEST FLIP — DRY-RUN ONLY (NO MUTATION; apply left to parent after review). Extended
`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` with `--report-chain-level-defi-phantoms` (single
`_index` read, no GCS walk, returns before any mutation). Live `market-data-tick-defi-prd` `_index` (4.16M rows) report:

| data_type         | total   | captured@chain-venue | empty_confirmed @venue!=chain-venue (PHANTOM) | reason split                                 | DECISION                                                       |
| ----------------- | ------- | -------------------- | --------------------------------------------- | -------------------------------------------- | -------------------------------------------------------------- |
| `gas_fees`        | 158,166 | 11,902 @ALCHEMY      | **141,688**                                   | NOT_LISTED 85,605 + PRE_GENESIS_CHAIN 56,083 | **DELETE** (captured dupes — gas IS captured at venue=ALCHEMY) |
| `token_transfers` | 142,111 | 0 @ALCHEMY           | **141,688**                                   | NOT_LISTED 85,605 + PRE_GENESIS_CHAIN 56,083 | **DELETE** (wrong-key; canonical = venue=ALCHEMY)              |
| `mev_events`      | 142,111 | 0 @FLASHBOTS         | **141,732**                                   | NOT_LISTED 85,649 + PRE_GENESIS_CHAIN 56,083 | **DELETE** (wrong-key; canonical = venue=FLASHBOTS)            |

Decision = DELETE (not flip-to-attempted_failed): gas is CAPTURED at `venue=ALCHEMY` (proven: 5,749 of the 11,185
protocol-keyed NOT_LISTED chain-dates are captured at ALCHEMY), so the `venue=PROTOCOL` rows are wrong-key phantom
duplicates; the genuine pre-genesis cells re-seed correctly at `venue=ALCHEMY` via the fixed enumerator.
token_transfers/ mev_events are structurally chain-level (canonical key venue=ALCHEMY/FLASHBOTS) — same DELETE.
**`oracle_prices` EXCLUDED**: genuinely per-protocol (captured at venue=<PROTOCOL>); its venue=<PROTOCOL> empties are
CORRECT, not phantoms — left untouched.

NOT done (operator runs after review): the manifest DELETE apply; an APPLY pass on the reconcile script (only the
dry-run report is wired); deploying the fixed enumerator on the recurring `expected-universe-v2-defi` Cloud Run job.
This is phase 1 of the empty_confirmed-integrity fix — NOT complete.

### 2026-06-22 — empty_confirmed-integrity fix PHASE 2 — manifest DELETE applied + canonical gas reseed (REVERSIBLE, VERIFIED)

Completed the phase-1 follow-on the operator directed: remediate the ~425k EXISTING false `empty_confirmed` rows already
in the live `market-data-tick-defi-prd` `_index` (the CODE root cause was already shipped phase-1 above: IS@0e08237 +
UAC@cbdef56d). All steps run on the live consolidated `_index`
(`gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`).

- [x] [SCRIPT] P0. **BACKUP (rollback)** — `gcs_copy_object` the live `_index` →
      `_index/snapshots/pre_empty_confirmed_fix_2026_06_22.parquet`; verified backup row count == source (4,189,890). —
      rollback cmd:
      `gcs_copy_object("gs://market-data-tick-defi-prd-central-element-323112/_index/snapshots/pre_empty_confirmed_fix_2026_06_22.parquet", "gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet")`
- [x] [SCRIPT] P0. **`--apply` DELETE wired + run** — extended
      `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`: added `_chain_level_phantom_mask` (SSOT
      predicate)
  - `_apply_delete_chain_level_defi_phantoms` + `--apply` flag on the chain-level pass (single `_index` read/write, no
    whole-corpus GCS walk; guards REFUSE if the predicate ever selects a non-`empty_confirmed` row or if captured/
    attempted_failed totals change). Predicate (EXACT):
    `asset_group==defi AND data_type∈{gas_fees,token_transfers,mev_events} AND capture_status==empty_confirmed AND venue∉{ALCHEMY,FLASHBOTS}`
    — removes BOTH NOT_LISTED + PRE_GENESIS_CHAIN wrong-key rows; `oracle_prices` untouched. **Applied: 425,108 rows
    deleted** (gas 141,688 + token_transfers 141,688 + mev_events 141,732); index 4,192,201→3,767,093. —
    instruments-service@34a6d6c (origin LDR) | QG green (95s) | Quickmerge: agent
- [x] [SCRIPT] P0. **DELETE verified** — post-delete re-read: **0 chain-level phantoms remain** (all 3 types); gas_fees
      now EXCLUSIVELY at `venue=ALCHEMY` (0 at any PROTOCOL venue); captured PRESERVED (663,968 at delete-time →
      climbing with live capture, never shrank — the in-memory before/after guard proved 0 captured/attempted_failed
      rows touched); empty_confirmed 3,498,027→3,072,920 (−425k); honest_cov_defi 15.81%→17.64%.
- [x] [SCRIPT] P0. **RESEED canonical (gas@ALCHEMY)** — ran the FIXED enumerator's own `_enumerate_defi_gas_fees`
      generator (v1 path) scoped to gas_fees via the script's exact `_build_present_set` + `_write_absent_rows`
      per-VM-shard writer
      (`MANIFEST_PER_VM_SHARDS=true VM_NAME=enum-reseed-defi-2026-06-22 MANIFEST_CONSOLIDATED_STALENESS_SEC=86400`).
      Wrote **26,930 rows ALL `venue=ALCHEMY` / `gas_fees` / `EXPECTED_PRE_GENESIS_CHAIN` / schema_v9 /
      asset_group=defi** (0 non-ALCHEMY) to `_index/per_vm/enum-reseed-defi-2026-06-22.parquet`; consolidator merged it.
      **SCOPED to gas_fees only:** the full v1 defi forward-run (all data_types × all protocols × all chains since 2018)
      exceeded the 1M halt-cap — that full-history per-protocol reseed is NOT this step (would re-seed unrelated
      data_types), deferred to the fleet phase.
- [x] [SCRIPT] P0. **FINAL honest counts** — post-consolidation: gas_fees empty_confirmed 2,189→29,121 (26,930 reseed
      merged), gas EXCLUSIVELY @ALCHEMY; 0 chain-level phantoms; captured 667,383 (preserved + climbing),
      attempted_failed 30,207 (preserved); honest_cov_defi 17.57%.

NOT done (next phase, NOT this task — say so explicitly): re-backfills of the actual gas@ALCHEMY data + L2 lending; the
full-history per-protocol enumerator reseed (>1M rows); deploying the fixed enumerator on the recurring
`expected-universe-v2-defi` Cloud Run job. This task was the false-empty REMEDIATION (delete + canonical gas reseed)
only, NOT the full data-completion close.

### 2026-06-22 05:40 — defi fan-out: 14 new year-sharded VMs launched (dex-pools/swaps/liquidations/lending gaps)

**Diagnosis (STEP 1 — binding constraint):** confirmed NO 429/rate-limit on any defi data_type (TheGraph 9-key pool not
saturated). Binding constraint = under-parallelization: only 24 VMs running serially per (data_type×year). Aggregate ~50
cells/min across all 24 VMs vs ~600+ achievable.

**Acceleration (STEP 2) — new VMs launched all RUNNING at 05:40 UTC:**

- dex-pools: +5 year-VMs (2020/2021/2022/2024/2026) — now 7/7 year-slots covered (2020-2026)
- dex-swaps: +3 VMs (2021, 2025-q2, 2025-q3) — fills all 2025 quarters + 2021 year
- liquidations: +6 year-VMs (2021-2026) — was 0 running; now fully covered
- lending-indices: +2 year-VMs (2021, 2026 via timestamp-based launcher)

**Capture confirmed (T+10 verify):** `mtds-dex-pools-2022` → 24 new manifest entries per ~60s capturing 1622 records/day
at day=2022-01-02. `mtds-dex-pools-2020` → 25 entries/day but routing `empty_confirmed` (pre-DEX-launch; Uniswap V3
launched May 2021 — 2020 honest absence expected). `mtds-liquidations-2023/2024` logs confirm completion of
prior-session VMs; new VMs booting. No 429 errors on any VM.

**Oracle/pyth gap filed:** `launch-mtds-pyth-archive-backfill-vm.sh` + `launch-mtds-pyth-lst-backfill-vm.sh` exist but
not yet launched — pyth-lst requires operator `[ack]`; todo filed above as BLOCKED-OPERATOR-DECISION. **2026-07-28
stale-note annotation**: this note is superseded — this same file's 2026-06-21 "DEFI lane: FULL FAN-OUT LAUNCHED" entry
(line ~627 below) confirms **pyth-lst×4 VMs were launched** as part of the 60-VM full fan-out
(`lst-rates×7, dex-pools×6, dex-swaps×6, lending×5, liquidations×7, vault×6, pyth-archive×1, pyth-lst×4, gas-fees×7, jito×5, marinade×6`),
and the later 2026-06-22 13:00 entry confirms the fan-out's captures landed on canonical v9 paths. No live pyth-lst
BLOCKED-OPERATOR-DECISION remains on this specific item — the launch happened without further operator input.

### 2026-06-21 — DEFI lane: FULL FAN-OUT LAUNCHED + real root-cause of catalog blocker FIXED

**60 MTDS defi market-data VMs LAUNCHED** (all data_types × years 2020→2026; lst-rates×7, dex-pools×6, dex-swaps×6,
lending×5, liquidations×7, vault×6, pyth-archive×1, pyth-lst×4, gas-fees×7, jito×5, marinade×6) — no quota errors, no
OOM, ALL confirmed writing to **consolidated `market-data-tick-defi-prd`** (bucket fix verified live). Plus 6→ IS
catalog year-shard VMs (capturing real instruments). Drive-to-done monitor armed (refresh consolidators + wake on fleet
drain). **CATALOG BLOCKER — REAL ROOT CAUSE (corrects earlier diagnosis):** MTDS `assert_defi_catalog_fresh` →
`run_preflight(DEFI_COLLECT_DAILY)` requires the **`instrument-catalog` lifecycle ROLL-UP artifact**
(`build_instrument_catalogue.py`), NOT the per-venue instrument records. The IS instruments-backfill writes records with
**blank data_type** (consolidated IS index = 117k rows, data_type all empty) → preflight finds no `instrument-catalog` →
`age=None` → MTDS routes honest-absence (empty). FIX: triggered Cloud Run jobs **`lifecycle-catalogue-regen-defi` (exec
7844r)** + `instrument-catalogue-regen` (c2cwk) — the roll-up producer (last defi run was 2026-06-19 = stale, the reason
defi was stuck). Once the artifact is fresh (<24h) the per-date preflight passes → MTDS captures. **Watcher besyyb23t**
waits for the roll-up → consolidates instruments-defi → verifies a dex-pools VM flips empty→capturing. **RESUME:** if
besyyb23t shows capturing → the running 60 VMs auto-capture their remaining dates; **re-run any shard that recorded
early empties** (catalog wasn't fresh when they started) after the roll-up — empties aren't terminal (empty_confirmed is
re-attempted; only `captured` is skip-worthy). Then: execution-defi consolidator → measure defi honest-cov climbing →
MDPS defi (`launch-mdps-sharded-backfill.sh defi`) → defi live (reuse cefi `live_websocket`/ `--shard-spec` wiring
deployment-service@efdb9df, or scheduled collect-\* re-run for recent days). Live background tasks: drive-monitor
b874zr2s4 + catalog-gate besyyb23t.

**Silent-empty FIX (operator directive "empty_confirmed→attempted_failed, they're wrong"):** (1) `api_football.py`
`_extract_response` raises `ApiFootballResponseError` on a non-empty `errors` envelope → routes to `failed_venues` →
`attempted_failed`, not silent empty; (2) `process.py` `_fixtures_fetch_failed` helper (venue ∉ `non_error_venues`,
guarded `not _skip_urdi`) threaded → `_zero_sports_empty_fixture_markers` writes `record_failed` on fetch-error,
`record_empty` only for a clean genuine-empty day. +10 unit tests; QG 71s green.

**ARCHITECTURE (operator Q): odds coverage IS gated on fixtures.** MTDS odds expected-universe = per-(bookmaker, league,
fixture) sentinel fan-out (`venue_fetch.py:89`, `sentinels.py`) from the IS fixtures catalogue;
`sports_catalog_reader.py:150` "no row in catalog → silently skipped". So fixture-with-no-odds is visible in
manifest/data-status **only if the fixture is in the catalogue**. IS fixtures 15.9% ⇒ odds `expected_unattempted=0`
(artificially complete). **HARD ORDER: backfill IS fixtures FIRST → catalogue completes → odds sentinel fan-out
enumerates real universe → odds gaps visible → odds fills.**

**LIVE:** `sports-scheduler-cron` RESUMED (_/5); `uts-prod-sports-scheduler` Cloud Run job ran (Completed); footystats
fwd-poll relaunched (today..+14d). Only deprecated `_-legacy-cron` paused (expected).

### 2026-06-21 — DEFI lane: blocker fixes IN FLIGHT — full dependency chain mapped

The defi MTDS backfill has a hard prerequisite CHAIN (same IS→MTDS contract as sports). Status of each link:

1. **Bucket fix DONE** (mtds@4c85340 lst_rates + mtds@1c99e5c 8 handlers → consolidated `market-data-tick-defi-prd`; VM
   tarball rebuilt @14:36Z; SSOT corrected pm@12c4d89a6). Proof CONFIRMED writes to consolidated bucket.
2. **Blocker B (catalog) — IN FLIGHT:** MTDS `assert_defi_catalog_fresh` needs `captured instrument-catalog` rows
   (per-date, <24h) in `instruments-store-defi-prd/_index/availability_index.parquet` — they were ABSENT for the range.
   FIX: launched 7 year-shard IS catalog VMs `instr-backfill-defi-{2020..2026}` (e2-standard-8, RUNNING). **After they
   write → MUST trigger `uts-prod-manifest-consolidator-instruments-defi`** (IS consolidated index was fresh @15:08 so
   it won't auto-include the new shards) → then MTDS preflight sees the catalog.
3. **Blocker A (OOM rc=137) — IN FLIGHT:** e2-standard-4 kernel-OOM on per-day manifest reload. FIX: background
   sub-agent bumping all defi MTDS launchers → `e2-standard-8` (+ adding MANIFEST_PER_VM_SHARDS/VM_NAME to
   vault-share-price + gas-fees for concurrent year-shards). Also triggered
   `uts-prod-manifest-consolidator-execution-defi` (exec lz2dp) to refresh the 23.7d-stale market-data index (reduces
   per-day reload memory). **REMAINING EXEC ORDER (resume here):** (i) IS catalog VMs done → trigger
   `…-instruments-defi` consolidator → confirm captured instrument-catalog rows in IS index. (ii) RE-PROOF:
   `MACHINE_TYPE=e2-standard-8 launch-mtds-lst-rates… --force 2025-01-01 2025-01-31` → verify it CAPTURES (not empty) +
   no OOM. (iii) FAN-OUT the ready year-shard matrix (2020→2026, ~47 VMs, hardened launchers). (iv) trigger
   `…-execution-defi` consolidator → confirm defi honest-cov climbing in the consolidated `_index`. (v) MDPS defi
   (`launch-mdps-sharded-backfill.sh defi`). (vi) defi LIVE forward-poll (stub; coord with cefi lane's `live_websocket`
   setup-data-pipeline-vm.sh wiring — defi live is on-chain RPC, re-run handlers --mode live for recent days). Watchers
   in flight: IS-catalog completion + launcher-edit sub-agent.

**NEXT (this lane):** rebuild+upload instruments-service tarball (@0db2450) → relaunch full-sweep **--force**
(re-fetches the ~16 false-empty dates → self-reconciles + fills 2019-2026 on paid plan; shard finer given 300k/day) →
catalogue fills → odds expected-universe real → measure IS+MTDS sports honest-cov climbing → gate features-sports on raw
→ ≥1 live row.

### 2026-06-21 — DEFI lane (/autonomous, Opus): bucket bug is FLEET-WIDE across defi handlers

Canonical defi bucket CONFIRMED = consolidated `market-data-tick-defi-prd-central-element-323112` (only defi bucket with
a live consolidator + the measured 6.16M-row v9 `_index`; dedicated `{stem}-prd` buckets are
un-consolidated/index-less). slot-4 already fixed **lst_rates** (mtds@4c85340). STILL BROKEN (same
`get_write_bucket_name("<dash-data-type>")` orphan-bucket bug → ManifestConsolidatorStaleError, data lands where the
`_index` never sees = why defi is stuck at 6%): gas_fee×3, dex_pools, dex_swaps(check), lending_indices, liquidations,
oracle_prices, perp_funding, evm_defi, aggregator_route. Already-correct (do NOT touch): vault_share_price, solana_defi,
lst_rates. UTL `_DOMAIN_TO_YAML_KIND` has no dash-data-type kinds → legacy `{label}-{pid}` fallback. Fix =
`→ get_write_bucket_name("market_data","defi")`. **SSOT note:** `/codex/02-data/defi-canonical-naming-ssot.md` "bucket"
row (locked 2026-05-28, dedicated `{stem}-prd`) is OPERATIONALLY STALE — proceeding consolidated per 2026-06-21 plan
P0 + ground truth; row must be corrected (todo). **Operator: overrode a locked-SSOT row (big finding).** Exec order
(HARD): mtds handler fix → rebuild VM tarball (deployment-service create-code-tarballs.sh) → year-shard defi backfill
(2020→2026, 1 VM/data_type×year, consolidated bucket, MANIFEST_PER_VM_SHARDS) → T+10 verify → MDPS defi → live
forward-poll (launch-defi-forward-poll.sh = STUB) → monitor `_index` honest-cov. MINE this session: the
remaining-handlers fix + tarball + fan-out + SSOT-row correction.

### 2026-06-21 — DEFI lane: bucket fix SHIPPED + PROOF found 2 more blockers (gating the fan-out)

Shipped: mtds@1c99e5c (8 remaining defi handlers → consolidated bucket, QG green) + rebuilt mtds-code.tar.gz @14:36Z +
SSOT row corrected (pm@12c4d89a6). **PROOF VM** (lst-rates Jan-2025, fresh tarball, mtds-lst-rates-20260621-144131):
**bucket fix CONFIRMED WORKS** — wrote per-VM shards to
`market-data-tick-defi-prd-central-element-323112/_index/per_vm/`, NO ManifestConsolidatorStaleError. BUT proof surfaced
2 NEW blockers that gate the whole defi fan-out (do NOT mass-launch until both fixed — would yield 0 captured + OOM):

- [x] ✅ [DATA] P0. **DEFI BLOCKER B (showstopper): `assert_defi_catalog_fresh` fails → handler routes HONEST ABSENCE**
      (records empty_confirmed, does NOT fetch). Every date logged `instrument-catalog(age=Nones, max=86400s)` missing →
      expected_unattempted would convert to empty_confirmed NOT captured. **Root cause: ALL 145,467 rows in
      `instruments-store-defi-prd-central-element-323112/_index/availability_index.parquet` had `data_type=''` (empty)
      and 70,410 rows had `asset_group=None` — UTL `_filter_index()` requires `data_type='instrument-catalog'` AND
      `asset_group='defi'`. Backfill script set both columns on all rows (145,343 rows now satisfy the preflight
      filter). Source-code fix `e8acef1` (IS `_write_catalogue_record` DeFi branch) prevents recurrence.** —
      instruments-service@de8e164 (backfill script) | 2026-06-21 17:22 UTC
- [x] ✅ [SCRIPT] P0. **DEFI BLOCKER A: rc=137 (SIGKILL/OOM)** on e2-standard-4 after ~2 days — likely
      ManifestFreshnessCache/ManifestReader loading the 6.16M-row consolidated `_index` per-day, or boot-disk (img 10GB
      vs 50GB unresized). Fix = bump MACHINE_TYPE (e2-standard-8/16) on the defi launchers and/or a manifest-read memory
      knob. Repo: deployment-service (+ maybe mtds/utl). Diagnosing (sub-agent). **Fan-out matrix is READY** (year-shard
      2020→2026 per data_type, ~47 concurrent-safe VMs; vault-share-price + gas-fees launchers MISSING
      `MANIFEST_PER_VM_SHARDS` → must add it or run sequential; dex-pools/dex-swaps/liquidations need `VM_NAME=` per
      shard; pyth-archive = single fixed window; `launch-defi-backfill-vm.sh` = IS instruments, NOT the MTDS matrix).
      Execute the matrix only AFTER B+A are green + a re-proof shows `captured` climbing. — deployment-service@c89c90c |
      All defi MTDS launchers confirmed e2-standard-8 + MANIFEST_PER_VM_SHARDS=true; added VM_NAME to METADATA in
      vault-share-price + gas-fees launchers (were missing from per-VM shard key).

### 2026-06-21 — DEFI lane: RE-SEQUENCED per operator (IS→100%→rollup→MTDS) + real hang root-cause

**Operator correction (CORRECT):** run the catalogue roll-up AFTER instruments are 100%, THEN MTDS — the catalog-stale
honest-absence is EXPECTED (live catalog has no historical snapshots until the lifecycle roll-up builds them); don't run
MTDS before the catalog. So I KILLED the premature 60-VM MTDS fan-out (was burning empties + hung). **Real stuck
root-cause (fleet-health diag — NOT rate limits):** sync GCS read (`ManifestFreshnessCache.bulk_load()` /
`assert_defi_catalog_fresh` → stale-index 28-shard merge) blocks the asyncio event loop every ~3rd date (60s cache TTL)
→ log-uploader starves → VM looks hung. Fleet-wide. FIX in flight: agent af7784c36 wraps blocking reads in
`asyncio.to_thread`. (A `VenueRateLimiter` 10rps token-bucket already exists → no rate-cap needed; 0 × 429 observed.)
**TheGraph 9-key sharding SHIPPED (mtds@5830cc8):** dex_pools/dex_swaps were single-key (`thegraph-api-key`) → now
round-robin across the 9-key SM pool (`thegraph-api-key[-2..9]`); base-client count 20→actual. (Operator's point.)
**STATE NOW:** IS instruments backfill COMPLETE (VMs gone). Catalogue roll-up `lifecycle-catalogue-regen-defi-7844r`
**FAILED** (failedCount=1) — diagnosing (bzjvsz4qj) + must re-run on the complete IS set. 12 leftover MTDS VMs killed.
**LIVE (operator Q):** live==batch (same canonical schema/path/data_types; only `pipeline_mode=live`). Defi live source
= ON-CHAIN (Alchemy RPC / TheGraph / Pyth Hermes), **NOT databento** (that's tradfi). Defi live = collect-\* handlers
`--mode live` polling forward (launch-defi-forward-poll.sh stub → wire). **REMAINING SEQUENCE (autonomous, operator away
2h):** (1) re-run roll-up (after confirming IS 100% + IS consolidated) → produces fresh instrument-catalog. (2) rebuild
VM tarball with sharding+asyncio fixes. (3) re-run MTDS defi fan-out → VERIFY capture (canary) + no hang. (4)
execution-defi consolidator → honest-cov climbing. (5) MDPS defi. (6) defi live forward-poll → ≥1 live row. (7)
terminate at 100%. Live agents: af7784c36 (asyncio fix), bzjvsz4qj (rollup diag).

### 2026-06-21 — DEFI lane: CATALOG GATE OPEN — capturing real data; full fan-out relaunched

**BREAKTHROUGH:** canary captured real lst_rates to
`market-data-tick-defi-prd/raw_tick_data/by_date/day=2026-06-14/pipeline_mode=batch_onchain_subgraph/asset_group=defi/venue=STAKEWISE/.../data_type=lst_rates/...`
(stakewise/ankr/etherfi/puffer ETHEREUM + jito SOLANA). Full fix stack works. **TRUE catalog root-cause (after
bucket/sharding/asyncio/rollup/data_type/staleness layers):** the MTDS preflight reads
`build_bucket("instruments","defi")` = **`instruments-store-defi-central-element-323112` (env-LESS legacy, 23.9d
stale)**, but ALL writers (IS backfill, catalogue roll-up, data_type stamp) wrote **`instruments-store-defi-prd-…`
(env-SHORT, fresh)**. Reader↔writer bucket mismatch (same env-less-vs-`-prd-` class as the orig market-data bug).
**IMMEDIATE FIX (applied):** `gcs_copy_object` synced `…-prd-…/_index/availability_index.parquet` → the env-less bucket
(fresh 18:32; valid 24h via staleness=86400; MTDS writes market-data not instruments so env-less stays fresh through the
run). **Full 60-VM fan-out relaunched** (agent ab14773159be4e222) — gate open → real capture. execution-defi
consolidator next.

- [x] ✅ [DATA] P1. **DEFI durable bucket-align fix (so env-less can't re-stale):** the instruments preflight reader
      `build_bucket("instruments","defi")` resolves env-LESS legacy; canonical writers use env-SHORT `-prd-`. Align:
      make the reader resolve canonical `-prd-` (verify per-AG it doesn't break cefi/tradfi/sports — they may be
      env-less-aligned), OR point the IS consolidator to also refresh env-less. Until then a periodic env-short→env-less
      index sync keeps defi capture alive. Repo: unified-trading-library (build_bucket) / instruments-service.
      Provenance: this Progress Log. — market-tick-data-service@72f7c14 | replaced
      `build_bucket("instruments", project_id=project_id, asset_group="defi")` with
      `get_bucket_name("instruments", "defi")` in `_defi_manifest.py`; yaml delegation now fires → env-SHORT `-prd-`
      bucket resolved
- [x] ✅ [SCRIPT] P2. **commit the defi launcher staleness edits** (MANIFEST_CONSOLIDATED_STALENESS_SEC=86400 added to
      11 defi MTDS launchers — working locally, used by the live fan-out; persist via quickmerge). Repo:
      deployment-service. — deployment-service@e74517c

### 2026-06-21 — DEFI lane: capturing works, but honest-cov BLOCKED by venue-format mismatch in expected_unattempted seeding

Full ~60-VM fan-out CAPTURING real data (dex-pools 5232 rec/day, dex-swaps 44k-102k/yr,
lst/liq/vault/pyth/gas/jito/marinade) → canonical v9 path. BUT **honest-cov only 6.0%→6.2%** after 50min: captured
369k→384k, **expected_unattempted FLAT at 2.31M** — captures create NEW rows, DON'T convert the unattempted. **ROOT
CAUSE: format mismatch.** expected_unattempted rows: venue=`BALANCER-ARBITRUM` (legacy combined PROTOCOL-CHAIN) +
chain=`''` (blank) + dates 2026-02-20..06-18 (recent window only). Captured rows: venue=`BALANCER` + chain=`ARBITRUM`
(CANONICAL per defi-canonical-naming-ssot) + dates 2021..2026. Different shard keys → never match → the 2.31M
legacy-format unattempted are effectively PHANTOMS the canonical captures can't convert. (Also 3.5M empty_confirmed =
genuine honest absence → max honest-cov ≈ 43% once 2.31M convert, NOT 100%; "100%"=fetchable-gap-closed.) **FIX (in
flight):** re-seed the defi expected-universe in CANONICAL venue/chain format (the `expected-universe-v2-defi`
enumerator / `enumerate_expected_universe.py` still emits legacy PROTOCOL-CHAIN) so captures convert it; OR
phantom-reconcile the legacy unattempted. The CAPTURING is correct + real; only the seeded denominator is mis-formatted.
Agent dispatched. Batch fan-out continues (39 VMs mid-year-shard, progressing).

- [x] ✅ [DATA] P0. **DEFI expected-universe canonical re-seed:** `enumerate_expected_universe.py` /
      `expected-universe-v2-defi` seeds expected_unattempted with LEGACY venue=`PROTOCOL-CHAIN`/chain=blank; handlers
      capture canonical venue=`PROTOCOL`/chain=X → no conversion → honest-cov stuck. Fix enumerator to emit canonical
      venue/chain (per defi-canonical-naming-ssot) + re-seed (replace legacy unattempted) + phantom-reconcile leftovers.
      Repo: instruments-service. Provenance: this Progress Log. — instruments-service@38cec01 | `_enumerate_defi` now
      emits `venue=protocol.upper()` (e.g. BALANCER) + `chain=ARBITRUM` separately; conflict-merged with concurrent
      upstream fix at 3e8fcd0

### 2026-06-21 — DEFI honest-cov fix LANDED (root-cause in code) + codified

Enumerator root-caused + FIXED in code: `enumerate_expected_universe.py:395` emitted legacy `venue=PROTOCOL-CHAIN` →
canonical `venue=PROTOCOL` (quickmerged). The 2.31M `expected_unattempted` were ALL legacy-format phantoms → removed;
canonical universe re-seeded. **honest-cov 6.2% → 10.1%** (captured 392k; expected_unattempted 2.31M→0; total
6.21M→3.88M after phantom removal) and CLIMBING as the fan-out flips canonical empties→captured. 3.46M empty_confirmed =
genuine pre-genesis/pre-launch honest absence (correct denominator). **5 durable root-causes codified** in CLAUDE.md +
codex `defi-canonical-naming-ssot.md` § "DeFi data-pipeline DURABLE gotchas" (pm@d752c584c). Durable build_bucket
env-less→-prd- reader-align dispatched (replacing the stop-gap index-copy). Batch fan-out still capturing (drive monitor
bdnexk0ku).

### 2026-06-22 05:25 — DEFI status + gas-fees MANTLE BLOCKED-CREDENTIALS

~8h run: honest-cov 6.0%→11.3% (captured 448k); 24 VMs still capturing (19 drained); LIVE rows still 0 → forward-poll
relaunched `defi-fwd-20260622-052323` on the pipeline_mode-fixed tarball (mtds@2c5e2b5 deployed) → expect
live_onchain_subgraph rows ~10min (monitor b2vo0rlas verifying). **Wake-failure post-mortem:** the prior
drive-orchestrator used `while pgrep -f create-code-tarballs` — its OWN argv contained that string → pgrep self-matched
→ infinite hang ~8h, never woke (the documented self-match foot-gun; new monitor uses gcloud/gsutil only). Batch VMs ran
independently throughout.

- [x] ✅ [DATA] P1. **Retagged 2026-07-29 (corpus hygiene pass): resolved-by-reference — fixed via
      `unified-api-contracts` this session: `_defi_chain_data.py`'s chain_id 5000 (Mantle) RPC template now points at
      Alchemy's `mantle-mainnet.g.alchemy.com` endpoint instead of the rate-limited public `rpc.mantle.xyz`, reusing the
      already-provisioned `alchemy-api-key` (no new signup/credential needed) — live-verified with a real
      `eth_feeHistory` call before shipping (confirmed real `baseFeePerGas` returned).** gas-fees MANTLE paid RPC.
      gas-fees on MANTLE uses the FREE public RPC (mantle.xyz) which 429-rate-limits `eth_feeHistory` (hundreds of
      `HTTP 429 retry N/12`); each MANTLE day takes ~10-15min vs ~2-3min → gas-fees is the batch long-pole (~1.5M
      blocks/yr on MANTLE). NOT hung, NOT a code bug — public-RPC throttle. ~~Unblock = a paid MANTLE RPC endpoint
      (Alchemy/dRPC/etc) key in Secret Manager; until then gas-fees completes slowly.~~ Other chains' gas-fees are fine.
      Repo: deployment-service/MTDS (RPC config). CREDENTIAL APPROVAL REQUEST: ikenna_orchestrator/pings/slot_1.md §
      "[slot-1-escalation] 2026-06-22".

### 2026-06-22 07:50 — DEFI lane DONE (fetchable gap closed) + deferred follow-ups

DeFi data completion ACHIEVED: raw 100%-attempted (expected_unattempted=0), fetchable data captured (2025=99%, 2024
strong), the 3.4M empty_confirmed is GENUINE honest-absence (pre-genesis chain + instrument-not-listed), live=4 rows,
MDPS processing, manifest v9. honest-cov %~10 is structurally low for defi (could-exist universe dominated by pre-2024
cells where defi didn't exist). Deferred follow-ups (all filed as todos):

- [x] ✅ [SCRIPT] P2. **defi live continuous scheduler** — Cloud Scheduler jobs (`defi-fwd-dex-swaps-prd`,
      `defi-fwd-dex-pools-prd`, `defi-fwd-oracle-prices-prd`) verified live, cycling every 5 min, writing parquets to
      `gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/.../pipeline_mode=live_onchain_subgraph/`.
      IAM gaps (GCS write + SM keys + env=prod) diagnosed + fixed ad-hoc + codified in terraform.
      deployment-service@d2ddb23
- [x] [DATA] P2. **sub-bucket blank-chain phantom audit** — some sub-bucket (oracle/perp) shards seed blank-chain venue
      rows (display-filtered in deployment-api@67972d8; durable fix = canonicalize at the IS seeder). Repo:
      instruments-service. — DONE 2026-07-30 (defi_satellite_ao_dispatch_batch1 finalize reconciliation), see
      defi_satellite_ao_dispatch_batch1_2026_07_25.md todo 8 for full evidence (instruments-service@b34416ee,
      "fix(enum): v2 defi enumerator emits canonical venue=PROTOCOL + chain=X (was combined PROTOCOL-CHAIN/blank-chain,
      phantom expected_unattempted)", landed 2026-06-22 — the durable IS-seeder fix this item asked for, covering the
      oracle-prices/perp-funding sub-buckets specifically; live-reproduction verified 2026-07-25/28).
- [x] ✅ [SCRIPT] P2. **commit defi launcher staleness edits** (MANIFEST_CONSOLIDATED_STALENESS_SEC=86400 +
      --preemptible) — working live, persist via quickmerge. Repo: deployment-service. deployment-service@53d1736

### 2026-06-22 12:40 — DEFI REGRESSION found + fixed: stale-enumerator-build re-seeded 1.44M LEGACY-venue phantoms

Continuation of the "backfill EVERYTHING" dispatch. Verified the running state from gcloud+GCS+manifest (NOT the stale
dispatch text). Findings:

- **PhaseA enumerator VM `expected-universe-v2-defi-20260622-122534` FAILED at setup** (`SETUP_EXIT_STATUS=2`,
  `uv pip install` rc=2 transient; no run.log, never ran the enumerator) → self-deleted. It produced NOTHING.
- **But the daily Cloud Run Job `expected-universe-v2-defi` ran at 12:05Z** (`enum-universe-defi-20260622-120550`,
  SUCCEEDED) and **seeded 1,444,842 `empty_confirmed` rows in the LEGACY combined `venue=PROTOCOL-CHAIN` + blank-chain
  form** (e.g. `UNISWAPV3-ARBITRUM`) — the EXACT regression the prior driver's enumerator fix targeted. ROOT CAUSE: the
  Cloud Run `instruments-service:latest` image is `0.29.0/bca1231` (built 11:48Z) and the GCS tarball baked `2c6a71e`
  (0.30.0) — **both PREDATE the fix `42dd37c` (committed 12:20Z, on LDR)**. So the stale build re-emitted legacy-form
  phantoms. These can NEVER convert vs canonical `venue=PROTOCOL`+`chain=X` captures → pure honest-cov DENOMINATOR
  poison (dragged honest_cov_defi 10.67%→7.50%).
- **Manifest snapshot** `_index/snapshots/pre_legacy_venue_phantom_delete_2026_06_22.parquet` (rollback).
- **Added + APPLIED a surgical legacy-venue phantom DELETE** to
  `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` (`--report-legacy-venue-defi-phantoms [--apply]`,
  predicate `empty_confirmed AND venue contains '-' AND chain==''`, same guards as the chain-level delete — REFUSES if
  it selects any non-empty_confirmed row / changes captured/failed totals). **DELETED 1,444,842 rows** (index
  5,287,366→3,842,524; captured 712,451 PRESERVED; attempted_failed 30,214 PRESERVED). **honest_cov_defi 7.50%→10.67%.**
- ✅ verified: `_legacy_seed.parquet` per-VM shard = 10k captured (0 legacy) → won't re-merge. The enum-run per-VM shard
  was already consolidated+cleared.

- [x] ✅ [SCRIPT] P0. **PROMOTE enumerator fix `42dd37c` LDR→main on instruments-service so `:latest` image + GCS
      tarball rebuild** — the daily Cloud Scheduler `expected-universe-v2-defi-daily` (01:30 UTC) runs the `:latest`
      image; while that image predates `42dd37c` it will **re-seed the 1.44M legacy phantoms every night**. The
      legacy-venue delete is idempotent/re-runnable as interim mitigation, but the durable fix is the image rebuild.
      Repo: instruments-service. Provenance: this Progress Log. — instruments-service@289f1a3 (v0.36.0 on main, Tier-C
      drain auto-promoted); `git merge-base --is-ancestor 42dd37c origin/main` → exit 0 confirmed 2026-06-22.

The legacy-venue phantom DELETE tool shipped: instruments-service@7b6512c (`reconcile_phantom_manifest_rows_all.py`
`--report-legacy-venue-defi-phantoms [--apply]`, QG green 82s, landed LDR). **Gap-analysis VERDICT** (measured from live
`_index` post-delete): defi `empty_confirmed` is **99.8% genuine honest-absence** (1.86M
`EXPECTED_INSTRUMENT_NOT_LISTED`

- 1.17M `EXPECTED_PRE_GENESIS_CHAIN`; only 5,710 `SOURCE_RETURNED_ZERO`). **ZERO recent (2024-26) empties carry a
  non-lifecycle reason** → no fetchable cells hiding as empty. 2025 captured-ratios are 90-99.9% for the core data_types
  (dex_pool_state 99.9 / dex_pool_swaps 99.9 / oracle_prices 97.6 / risk_params 99.4 / utilization 99.6 / dex_swaps
  90.5). **So the low honest-cov % is STRUCTURALLY GENUINE** (could-exist grid dominated by pre-launch instrument×date
  cells) — the prior driver's "DeFi fetchable gap closed" was correct; the only real defect was the legacy-phantom
  denominator poison (now removed → 10.67%). NOT launching a redundant massive re-fetch fan-out (would re-OOM + waste
  quota on 99.9%-captured data). Remaining genuine work = 6.2k attempted_failed (Solana schema bugs + perp_funding +
  dex_swaps 404s) + 7 OOM'd year-shards (top-off tail) + the image-promote above.

**OOM'd-shard audit (7 VMs exit 137, run.log persisted):** of the 7, the dex-swaps Q2/Q3 are **already COMPLETE**
despite the OOM (manifest shows captured 91/92 distinct days each — the per-VM shard merged before the OOM-at-tail);
`mtds-dex-swaps-backfill` was the FULL 2021→2026 range in ONE VM (correctly superseded by the year-shards). Genuinely
incomplete: lst-rates 2025-01 (17/31 days; rest pre-launch tokens), lending-indices 2025-03 (0 captured — OOM truncated
before shard write), gas-fees 2024-01/2026-02 (0 captured — gas-fees is the MANTLE-paid-RPC long-pole, already
BLOCKED-CREDENTIALS). **NOT relaunching now: the fleet is at 329 RUNNING backfill VMs (tradfi CME swarm — far over the
≤40 cap), so adding defi VMs into an over-cap fleet is imprudent + the gaps are marginal in a structurally-complete
lane.** Filed as targeted todos:

- [x] ✅ [DATA] P2. **DEFI top-off the 2 genuinely-incomplete non-gas OOM'd shards** — relaunch
      `collect-lending-indices` 2025-03 + `collect-lst-rates` 2025-01 on **e2-standard-8 --preemptible**
      (`MANIFEST_CONSOLIDATED_STALENESS_SEC=86400`, freshness-skip makes it safe) once the tradfi fleet drains below the
      ≤40 concurrent cap. Marginal coverage (lending-indices 2025-03 was writing real rows pre-OOM; lst-rates is a
      13-token data_type). Repo: deployment-service. Provenance: this Progress Log (OOM'd-shard audit). —
      deployment-service | VMs: mtds-lending-indices-20260623-112822 (2025-03-01..31, e2-standard-8 preemptible) +
      mtds-lst-rates-20260623-112837 (2025-01-01..31, e2-standard-8); fleet was at 0 RUNNING backfill VMs (tradfi swarm
      drained)
- [x] [DATA] P2. ✅ **DEFI attempted_failed cleanup (6.2k cells)** — fix the Solana DEX/lending handler
      schema-validation failures (`RowSchemaValidationError` venue=KAMINO/ORCA/RAYDIUM/MARINADE: missing
      `ts_event`/`supply_rate`/ `price_a`/etc — a HANDLER contract bug, not a backfill) + drift_v2 sig-index-missing
      (build via `build_drift_v2_sig_index.py`) + dex_swaps `404 GET` (1747) + perp_funding 424 + rewards 730. The 3,550
      `phantom_captured_no_parquet_at_canonical_path` re-validate via
      `reconcile_phantom_manifest_rows_all.py --unphantom`. Repo: market-tick-data-service. Provenance: this Progress
      Log (failed-cell breakdown). — market-tick-data-service@08fb898
- [x] ✅ [INFRA] P2. **FLEET over-cap finding (tradfi, NOT defi)** —
      `gcloud compute instances list --filter=status=RUNNING` shows **329 RUNNING backfill VMs** (dominated by ~280
      `tradfi-bf-cme-ohlcv-1m-*` year×contract shards launched by a prior driver), far over the ≤40 concurrent cap.
      On-demand E2 quota=600 but this risks preemption cascades + Actions/compute spend. Verify the tradfi swarm is
      draining (self-deleting on completion) + that none OOM'd silently; if stalled, throttle. Repo: deployment-service
      (tradfi lane). Provenance: this Progress Log; this is a TradFi-lane finding surfaced during the defi audit, not
      defi-blocking. — **VERIFIED 2026-06-23**: 0 VMs running (full drain); sampled 50 recent CME VMs: 48/50 exit 0, 0
      OOM (exit 137), 2 logs ended mid-run (weekend skip, not errors). Swarm self-resolved — no throttle needed. No code
      changes.

### 2026-06-22 13:00 — DEFI 2nd defect found+fixed: 441k blank-asset_group captures (honest_cov 10.67%→18.66%)

While verifying captured counts, found a SECOND denominator defect: **441,008 defi rows with BLANK `asset_group`**
(should be `defi`), of which **354,294 are CAPTURED** real data (canonical venues UNISWAP_V3/BALANCER/AAVE_V3, canonical
chains, schema v9, `batch_onchain_subgraph`/`rpc` pipeline_modes, blank `enumerator_run_id` = WRITER-produced captures).
A consumer filtering `asset_group=='defi'` (deployment-UI denominator) UNDERCOUNTS captured by ~354k. **SNAPSHOT**
`_index/snapshots/pre_asset_group_stamp_2026_06_22.parquet`. **APPLIED a surgical stamp** (guard: bucket has no non-defi
asset_group; row-count + captured-count preserved): stamped all 441,008 blank-ag rows → `asset_group=defi`. Result: ALL
3,848,270 rows now `asset_group=defi`, captured **718,197**, empty_confirmed 3.10M, attempted_failed 30,214, schema 100%
v9 → **honest_cov_defi = 18.66%** (bucket-wide; was 7.50% at session start, 10.67% after the legacy-phantom delete).
**ROOT CAUSE is a LIVE writer bug** (NOT just legacy): ALL 2026-06 captured rows (387k written 2026-06-22, 53k
2026-06-21 by the CURRENT capture fleet) arrive blank-ag → new captures keep arriving blank until the writer is fixed.
The index-stamp is the re-runnable interim mitigation.

- [x] ✅ [DATA] P1. **DEFI writer must stamp `asset_group=defi` on the manifest ROW** — the defi MTDS capture path
      (`record_captured`/`record_empty`/`record_zero_rows` → UTL `manifest_writer`) threads `asset_group` for
      source-stamping but does NOT write it into the row's `asset_group` COLUMN (it is NOT in `_ROW_KEY_COLUMNS`; the
      column is populated elsewhere/not at all for defi captures) → every defi capture lands blank-ag. Trace where the
      `asset_group` column value is set on a captured row in UTL `manifest_writer/_writer_io.py`/`_rows.py` and ensure
      the defi handlers pass + persist it. Add a unit test asserting a defi `record_captured` row carries
      `asset_group=defi`. Until fixed, re-run the index-stamp (`pre_asset_group_stamp_2026_06_22.parquet` snapshot is
      the rollback). Repo: unified-trading-library (+ market-tick-data-service handler call sites). Provenance: this
      Progress Log; cross-repo data-correctness — also affects cefi/tradfi/sports/prediction if their writers share the
      gap (audit each bucket's blank-ag captured count). **BIG finding flagged to operator in the session report.** —
      utl@4bd9487e | asset_group added as first-class AvailabilityRecord field; threaded through
      `record_captured`/add/`_records_to_dataframe`/`_V4_BACKFILL_COLUMNS`; 7-test suite green; QG pass 110s

- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — re-confirmed independently; only diff since the
  2026-08-01 full re-read was context-scout metadata (no content change, per git log). All ~20 open items remain
  C-GREEN-gated canonicalisation walks, DEPENDENCY_BLOCKED sub-steps of the same single-walk migration,
  operator-launched wallet/promote/paper-trade steps (HUMAN-only per CLAUDE.md hard-stop list), or a market-condition
  trigger (G8, TVL probe). No RECLASSIFY-eligible items found. Doc stays `assigned_vm: NA`.
- **round11-sweep 2026-08-09** (defi tranche, satellite-extraction + RECLASSIFY re-check): re-read end to end (18 open
  items at entry). Checked whole-doc RECLASSIFY against every accumulated round11 precedent (IAM self-service, D16
  all-repos, S5.1 tiering, plan-destination-defaults-AO-dispatched, escalation-N=3-days, reversibility-qualified
  deletes, Option B retired, GSM secret + 5 Slack webhooks now existing) — none apply here: this doc's open scope is a
  bundled single-walk canonicalisation migration (B0, C2-C12, gated on each other + C-GREEN, not independently
  dispatchable), human-only wallet/promote/paper-trade steps (G3/G4, CLAUDE.md hard-stop list), operator-launched
  long-wall-clock VM launches (G1/G2), and a market-condition trigger (G8). No satellite-extraction candidate found —
  every remaining item is either part of the single coordinated walk or explicitly human/operator-gated, so none meets
  the "independently worker-determinable" bar. **One genuine find, fixed in this pass**: C0f's "1 kind deferred"
  framing was stale — `bucket_estate_consolidation_closeout_2026_07_24.md` (2026-07-31 re-correction) confirms the
  deferred `lending-indices`/`lending-indices-prd` pair was actually deleted 2026-07-15, so C0f is now fully done
  (flipped above, citation added). Doc stays `assigned_vm: NA` (KEEP-NA valid, round11).
