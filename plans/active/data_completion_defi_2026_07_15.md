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
last_updated: 2026-08-16 # was 2026-08-15 -- corrected 2026-08-19 (/plan-reconcile manifest_master), matched to the latest dated Progress Log entry (na-eligibility-audit 2026-08-16). (prior: was 2026-07-24 -- folded in the DeFi-lane Progress Log entries from M-1 per plan line-cap remediation)
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
    market-tick-data-service/market_tick_data_service/scripts/migrate_defi_full_v9_canonical.py,
    instruments-service/scripts/build_instrument_catalogue.py,
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

- [x] ✅ [DATA] P0. C0 **path + bucket canonicalisation (the foundational migration) — RUN ON A VM (operator-confirmed
      2026-06-01)**. **FLIPPED 2026-08-16 (plan_reconciler, defi tranche, dispatch agt-1a88e0)**: by this todo's own
      stated definition ("Remaining = the C0a–C0f VM-cutover sub-todos below"), every one of C0-PROVISION/C0a/C0b/C0c/
      C0d/C0e/C0f is `[x]` — verified by direct read, not inference. **Two-tool lineage (system-first)**: Phase-1.8
      `migrate_defi_canonical.py` already did
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
        and `lending-indices-prd-central-element-323112` succeeded, "STATUS: COMPLETE 2026-07-15", both confirmed 404
        via `buckets describe`; that doc also found the Morpho VM referenced here wrote to the unrelated canonical
        shared bucket, so its completion was never actually a gate on this specific deletion. All 14 of 14 kinds now
        confirmed deleted — nothing left open on C0f. See `gcs_bucket_estate_cleanup_2026_07_10.md` §5f + §5i for the
        original re-verification and execution log. **(MIGRATED FROM: `defi_manifest_canonicalisation_2026_06_01.md`,
        2026-07-13 per MTDS consolidation ruling.)**

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
      **na-eligibility-audit 2026-08-18**: "dedicated DeFi buckets" is now-stale scoping — dedicated buckets were
      RETIRED 2026-08-14 (`defi_migration_dedicated_bucket_architecture_retired_2026_08_14.md`); every DeFi
      data_type now shares the canonical `market-data`/`defi` bucket. When this walk executes, its scope must
      explicitly include `vault_share_price`/`risk_params`/`utilization` (the former "orphan-bucket" data_types,
      now confirmed on the same shared bucket per
      `/plans/active/defi_migration_audit_log_2026_07_24.md` line ~406) — those 3 have real pre-2026-06-16 rows of
      unconfirmed schema_version and are this walk's most likely remaining legacy-shaped content, not an edge case
      to skip because they were never "dedicated".

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

- **2026-08-15 (slot 24, data_engineering)**: Closed the 2026-07-14 entry's flagged finding below
  (`copy_research_perp_ctx_to_canonical.py:33` hardcoding the already-deleted PRD tier). Confirmed live via
  `get_storage_client().bucket(<name>).exists()`: both `perp-funding-central-element-323112` (LEGACY_BUCKET) and
  `perp-funding-prd-central-element-323112` (CANONICAL_BUCKET) are 404/deleted, so the script cannot run either way. No
  data-loss gap: `defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md` fact #3 confirms the
  `perp_daily_ctx`/`perp_mark_price` cells this script was meant to preserve were already migrated into the shared
  canonical bucket by a different script (HL `perp_daily_ctx` 1,109 objects + a 6,941-object residual-gap closure,
  verified counts in that doc's Progress Log) — this script was superseded, not needed. Deleted the dead script:
  `e2e-testing@f0978fa469`. Closed by citation per `defi_satellite_ao_dispatch_batch9_2026_08_06.md` todo (`[DIAG] P3`
  dead-code disposition).
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

> **History extracted 2026-08-15 (context_scope_backfill line-cap remediation, follow-up batch).** The entire folded-in-from-M-1 chronological block of 2026-06-21/2026-06-22 dated Progress Log entries (DeFi lane launch through the 2 regression-fix write-ups) was moved VERBATIM to `/plans/archive/2026_08/data_completion_defi_progress_log_history_2026_08_15.md` — zero open todos lived in this range (this plan's 17 open items all live in the `## Todos` section above, none in the Progress Log). The 2026-07-14 entry and the 2026-08-15 entry above stay live. Read the archive file for the full record.

- **context-scout 2026-08-15**: line-cap remediation (extracted the folded-in-from-M-1 chronological block to
  `/plans/archive/2026_08/data_completion_defi_progress_log_history_2026_08_15.md`, 1033L→469L); re-verified
  context_scope (3 entries), unchanged.
**context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)

## Extracted items index (2026-08-15)

> **Mechanical todo-conservation index — not live work.** `check_todo_regression.sh` counts total `- [ ]`/`- [x]` lines
> and fails a staged plan whose total shrinks vs `origin/live-defi-rollout`, with no exemption yet for a Finding-J
> archival extraction (same root cause as
> `/plans/active/issues/todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md`). The 24 lines
> below are the already-`[x]`-closed checkbox items this extraction moved verbatim to
> `/plans/archive/2026_08/data_completion_defi_progress_log_history_2026_08_15.md` — kept here as one-line stubs
> purely so the mechanical count is conserved; the full original text lives only in the archive, not duplicated here.

- [x] [INFRA] P1. DeFi continuous live market-data capture — IaC SHIPPED 2026-06-22 — see archive.
- [x] [TERRAFORM] P0. Durable per-AG `run.invoker` SHIPPED — see archive.
- [x] [SCRIPT] P0. IS enumerator — `enumerate_expected_universe.py` `_enumerate_defi()` — see archive.
- [x] [SCRIPT] P0. UAC `_defi.py` — removed `gas_fees`/`collect-gas-fees` from every protocol — see archive.
- [x] [SCRIPT] P0. MTDS handler silent-zero audit + eigenlayer fix — see archive.
- [x] [SCRIPT] P0. BACKUP (rollback) — `gcs_copy_object` the live `_index` — see archive.
- [x] [SCRIPT] P0. `--apply` DELETE wired + run — see archive.
- [x] [SCRIPT] P0. DELETE verified — 0 chain-level phantoms remain — see archive.
- [x] [SCRIPT] P0. RESEED canonical (gas@ALCHEMY) — see archive.
- [x] [SCRIPT] P0. FINAL honest counts — post-consolidation gas_fees numbers — see archive.
- [x] [DATA] P0. DEFI BLOCKER B: `assert_defi_catalog_fresh` fails → handler routes honest absence — see archive.
- [x] [SCRIPT] P0. DEFI BLOCKER A: rc=137 (SIGKILL/OOM) on e2-standard-4 — see archive.
- [x] [DATA] P1. DEFI durable bucket-align fix (env-less can't re-stale) — see archive.
- [x] [SCRIPT] P2. commit the defi launcher staleness edits — see archive.
- [x] [DATA] P0. DEFI expected-universe canonical re-seed — see archive.
- [x] [DATA] P1. Retagged 2026-07-29 (corpus hygiene pass) — resolved-by-reference — see archive.
- [x] [SCRIPT] P2. defi live continuous scheduler — Cloud Scheduler jobs — see archive.
- [x] [DATA] P2. sub-bucket blank-chain phantom audit — see archive.
- [x] [SCRIPT] P2. commit defi launcher staleness edits (`MANIFEST_CONSOLIDATED_STALENESS_SEC`) — see archive.
- [x] [SCRIPT] P0. PROMOTE enumerator fix `42dd37c` LDR→main on instruments-service — see archive.
- [x] [DATA] P2. DEFI top-off 2 genuinely-incomplete non-gas OOM'd shards — see archive.
- [x] [DATA] P2. DEFI attempted_failed cleanup (6.2k cells) — see archive.
- [x] [INFRA] P2. FLEET over-cap finding (tradfi, NOT defi) — see archive.
- [x] [DATA] P1. DEFI writer must stamp `asset_group=defi` on the manifest ROW — see archive.
- **na-eligibility-audit 2026-08-16** [body-hash:388f83d440eb6e71]: KEEP-NA, stale items (citation-fix flagged, not applied this run) -- 511-line doc read end to end, 16 open todos grep-confirmed matching Phase-0. C0 foundational migration flipped [x] TODAY (plan_reconciler, defi tranche) -- C-GREEN-dependent items (B0, C6) warrant a fresh gate-read next run. C2/C3/C4/C9/C11 (5 items, tagged MIGRATED FROM defi_manifest_canonicalisation_2026_06_01.md) are very likely a duplicate of the SAME residual canon-walk items independently tracked at defi_track01_per_instrument_and_canon_id_2026_07_24.md:310 -- confirmed via this runs own Phase-0 inventory that defi_track01 IS assigned_vm:NA (still active, KEEP-NA-valid this run), so this is a genuine 3-way tracking overlap (this doc + defi_consolidated_closeout_2026_07_18.md + defi_track01), not a dispatch-duplication risk -- citation-fix (not a checkbox close) deferred to a dedicated hands-on pass given 3 docs are involved. C5 phantom-grid-delete item may also be stale per this docs own C0f finding (dedicated-to-shared bucket consolidation complete) -- flagged, not applied. Remaining items (B0, E1, G1-G4, G6, G8, instruments-store-defi walk) are genuinely C-GREEN/operator/judgment-gated, G4 a HUMAN-ONLY live-wallet promote hard-stop. Doc stays NA.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-21** (defi tranche, wave 2): KEEP-NA, valid — re-read end to end; 16 open todos unchanged since the 2026-08-18 verdict (context-scout-only touch on 2026-08-20). All remain C-GREEN/operator/VM-gated canonicalisation walks, a bundled cross-repo migration, or a hard human-only wallet/promote step. No new RECLASSIFY-eligible items found. Doc stays `assigned_vm: NA`.
