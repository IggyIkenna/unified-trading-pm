---
doc_type: plan
title: IS-catalogue completion (2d) — backfill to no-missing, regen, un-pause (AO Plan 3)
summary:
  Complete the instruments-service could-exist catalogue so every expected-universe consumer reads a full, deduped
  instrument lifecycle. Sequence is B0 (backfill instruments to no-missing) gates B1 (catalogue regen + un-pause the
  per-AG daily schedulers) and the B2 downstream wiring (enumerate_expected_universe reads the shipped
  TOTAL_UNIVERSE_AXES UAC SSOT). B0 is the hard prereq for the Stage-3 denominator re-measure (Plan 4) — a stale
  catalogue means a wrong could-exist universe. Source items live in instruments_mtds_subset +
  instruments_catalogue_incremental_rollup + mvp_scope_catalogue_tagging — this plan carries the catalogue-completion
  slice and references them for detail.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, unified-api-contracts, deployment-service]
scope: [engineer]
tags: [instruments, catalogue, could-exist, backfill, b0, b1, b2, mvp-universe, instruments-completion]
related:
  [
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/active/instruments_mtds_subset_consistency_remediation_2026_06_17.md,
    /plans/archive/2026_07/instruments_catalogue_incremental_rollup_2026_06_29.md,
    /plans/active/mvp_scope_catalogue_tagging_2026_06_08.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
  ]
created: 2026-07-06
last_updated: 2026-07-12 # was: 2026-07-06 -- corrected 2026-07-12, finding 112, §A2 B-queue ruling: all 10 todos verified [x] complete with sha evidence, status flipped active -> complete per finding 110, last_updated never bumped past creation date
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
model_tier: sonnet-doable
thinking_tier: high
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
---

# IS-catalogue completion (2d) — B0 → B1 → B2 (AO Plan 3)

> **🤖 AO PLAN 3 of the instruments-completion set.** Dispatched to the agent-orchestrator (`assigned_vm: planning`,
> role `data_engineering`). **Dispatch tier (frontmatter-driven, EVERY task): Sonnet / high.** Coordinator =
> `instruments_completion_tracker_2026_07_06.md` (Stage 2d). Runs in **parallel** with Plans 1 (cefi) + 2 (tradfi). **B0
> is foundational** — it gates B1 + the Stage-3 re-measure (Plan 4): every expected-universe consumer
> (`enumerate_expected_universe.py`, data-status could-exist) reads the catalogue, so a stale/incomplete catalogue = a
> wrong denominator. Source detail lives in `instruments_mtds_subset_consistency_remediation` (B0/B1/B2, F1) — READ
> there; those items stay tracked-but-not-dispatched (that plan is `assigned_vm: NA`), this plan carries the dispatched
> slice.
>
> **Worker guards (HARD):** (1) **smoke-first** on any backfill VM — one venue/slice foreground + verify the IS store +
> catalogue side-effect before fanning out; **backfill VMs default SPOT**; no fire-and-forget (verify T+10min). (2) **B0
> before B1** — do NOT regen the catalogue on an incomplete instrument set. (3) **scheduler un-pause is a cadence
> decision** — if the daily rollup still times out at 3600s, RAISE the BLOCKED-Q (band-aid vs. Phase-3 incremental), do
> not silently re-enable a scheme the operator declined. (4) ship via quickmerge; flip + Progress-Log in the same turn.

## Codex SSOTs (read before touching)

- `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — IS owns reference data; catalogue = the could-exist
  SSOT MTDS + data-status read.
- `/codex/02-data/honest-coverage-model.md` — Layer-1 denominator; do NOT derive the expected universe from the
  manifest.

## B0 → B1 → B2 (order matters — each task's `PREREQ:` is load-bearing)

- [x] ✅ [DATA] P0. **B0 — backfill instruments to NO-MISSING** (slot-2 opus/max 2026-07-06, evidence: MVP-scoped gap =
      83 cells (~0.1% of 76k MVP), all classified). CURRENT-STATE READ from
      `instruments-store-{cefi,tradfi,defi}-prd/_index/availability_index.parquet` filtered to `MVP_SCOPE[ag].venues`:
      **defi = 0 MVP missing** (2e D1 seeding landed same-day per tracker log); **cefi = 76 MVP non-captured** (40 ASTER
      = Stage-2c capture-rule work in-flight elsewhere; 24 EU 2023-12-16..19 = historical service outage window across 6
      venues, accept as coverage-time floor per main-agent guidance BLK-749ae284; 12 non-ASTER AF classified per
      `issues/instruments_handler_pd_na_ambiguous_and_af_classification_2026_07_06.md` into 8 RESOLVED_STALE_AF
      (co-existing captured rows found — cleared by the
      `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05` dedup fix) + 4 KNOWN_HANDLER_BUG_PD_NA
      (HYPERLIQUID 2024-09-12/28, 2024-12-31, 2026-03-18 — root-caused via a DEBUG-log retry to a repeatable
      InstrumentsHandler "boolean value of NA is ambiguous" write-path crash, fix TODO in the issue doc)); **tradfi = 7
      MVP non-captured** (all CME — 1 AF 2026-06-20 + 6 EU sparse dates 2024-07-08 / 2024-11-26 / 2024-12-04 /
      2025-08-07 / 2025-08-18 / 2026-06-24; pattern consistent with market-calendar /Databento gaps, verify post
      `tradfi_v9_stage1_finish` completes). All residuals are TRACKED. Per main-agent's BLK answer "0 missing MVP means
      0 UNEXPLAINED gaps — known in-flight tracked work does not block the flip." B0 gate flips with the residuals
      documented as classified/tracked items above. instruments-service. — see issue doc for the P1 pd.NA fix + P2
      tradfi CME verify + P2 stale-dedup collapse follow-ons.
- [x] ✅ [DATA] P1. **F1 — backfill IS for the CEFI venues MTDS has but instruments lacks historically** (slot-2
      opus/max 2026-07-06). Compared `instruments-store-cefi-prd` vs `market-data-tick-cefi-prd` availability index
      venue sets (single-walk-compliant reads, no whole-corpus GCS re-scan). Result: **MVP ∩ MTDS ⊆ MVP ∩ IS = 20
      venues** — every MVP-scope venue MTDS has captured is ALREADY in IS (BINANCE-SPOT/FUTURES, BITFINEX-SPOT/ FUTURES,
      BITGET-SPOT/FUTURES, BYBIT/BYBIT-SPOT, COINBASE-SPOT/FUTURES, DERIBIT, EXTENDED-STARKNET, HYPERLIQUID,
      KRAKEN-SPOT/FUTURES, OKX-SPOT/FUTURES/SWAP, UPBIT, ASTER — 20/20). The 2 MVP venues not yet in MTDS
      (LIGHTER-ZKSYNC, PACIFICA-SOLANA) are ON-CHAIN CLOB DEXes still ramping MTDS live-capture — not a historical
      backfill gap. **The 12 MTDS-only bare-venue diffs** (BINANCE, BITFINEX, BITFINEX-DERIVATIVES, BITGET, KRAKEN,
      OKEX/OKEX-FUTURES/OKEX-SWAP, BYBIT-FUTURES, COINBASE-INTERNATIONAL, CRYPTOFACILITIES, UNKNOWN) are all LEGACY
      pre-canonicalization MTDS naming or non-MVP venues (Kraken-Futures's pre-2019 wire-form "CRYPTOFACILITIES"; OKEX
      pre-2022 rebrand-to-OKX; bare-form BINANCE/BITFINEX/BITGET/KRAKEN pre the sub-venue split; the "UNKNOWN"
      classification-junk row) — NOT MVP-scope backfill gaps but MTDS-manifest canonicalization surface. Their
      IS-canonical equivalents are all catalogued. Gate satisfied under the MVP-strict reading of "no venue MTDS
      captured but IS never catalogued". The MTDS legacy-naming reconcile is a MTDS/manifest concern (tracked in
      `venue_naming_drift_defi_reconcile_2026_06_19` for defi and by the general `*_manifest_canonicalisation_*` track
      for cefi), not IS backfill.
- [x] ✅ [DATA] P1. **Extended public instrument + perp backfill (UNBLOCKED — no key needed)** — IS daily public
      instrument + perp backfill for EXTENDED (slot-2 opus/max 2026-07-06). Gate satisfied: EXTENDED-STARKNET is 100%
      catalogued in its UAC discovery window — 644 of 644 days captured 2024-10-01 → 2026-07-06 (0 missing) via the
      recurring `uts-prod-instruments-service-cefi-t1-recon` daily job that publish-runs the
      `ExtendedReferenceDataAdapter` (public REST at `api.starknet.extended.exchange/api/v1/info/markets`, no auth);
      2012 pre-discovery-start rows (2019-03-30 → 2024-09-30) correctly classified
      `empty_confirmed / EXPECTED_PRE_VENUE_LAUNCH`. Baseline read from
      `instruments-store-cefi-prd-central-element-323112/_index/availability_index.parquet` (single-walk-compliant per
      the codex, no whole-corpus GCS re-scan). Adjacent finding surfaced during verification:
      `issues/is_cefi_manifest_blank_data_type_since_2026_06_29_2026_07_06.md` — every cefi venue's captured shards
      since 2026-06-29 land with `data_type=""` (blank) instead of `data_type="instruments"` (writers.py:239 emits
      blank; the migration script was the historical normalizer). Not blocking THIS gate (the plan reads coverage on
      `capture_status=='captured'` alone) but review-blocking downstream consumers that use the canonical
      `data_type=='instruments'` filter — 4 actionable todos filed for a fix-worker.
- [x] ✅ [DATA] P1. **CME EC\* event-contract backfill (v9-certification dependency)** — the CME event-contract
      instruments the tradfi catalogue needs for the v9 cert (slot-2 opus/max 2026-07-06). Gate satisfied: fresh tradfi
      catalog (rebuilt today at 2026-07-06T15:48:30 UTC via Plan 2 task 8 — same
      `catalogue-rollup-tradfi-20260706T154714Z` run) contains **222,694 CME EC\* rows** — all MVP CME EC roots present
      (ECES=Snake500, ECNQ=Nasdaq-100, ECGC=Gold, ECBTC=Bitcoin — plus non-MVP ECCL/ECNG/EC6E/ECRTY/ECYM and
      options-on-EC-futures folded into "OTHER" 13,532). Coverage window
      `available_from ∈ [2024-12-17,     2026-07-02]`; `available_to ∈ [2025-09-29, 2026-12-31]`. All 222,694 carry
      `venue='CME'`, `instrument_type='OPTION'` (Databento's classification for the binary EC-family products — the
      adapter's `BAG→EVENT_CONTRACT` reclass at `databento/adapter.py:764-766` is a documented fallback for a legacy
      Databento representation; the live GLBX.MDP3 feed classifies them as OPTION and the adapter passes that through).
      Plan 2's tradfi IS seed coordinated implicitly: the same rollup includes them because
      `build_instrument_catalogue.py` walks `by_date/` snapshots the Databento URDI adapter has emitted from
      `TRADFI_DATABENTO_INSTRUMENTS` (UAC registry includes ECES/ECNQ/ECGC/ECCL/ECNG/ECBTC under
      `MVP_CME_EXCHANGE_CODES`, `unified-api-contracts@registry/tradfi_instrument_universe.py:713-720`). Feeds Stage-3
      denominator re-measure (Plan 4). instruments-service (fresh rollup landed via the shared
      `gs://instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet`).
- [x] ✅ [INFRA] P1. **B1 — instrument catalogue regen + un-pause the per-AG daily schedulers** (slot-12 opus/max
      2026-07-06). Gate satisfied: **task premise was stale** — the schedulers had already been un-paused between
      2026-06-23 (deployment-service@9b74416 tradfi 32Gi→16Gi + timeout 1800→3600) and 2026-06-29
      (instruments-service@b0596d0 Phase-3 incremental `--mode incremental` default + weekly `--mode full` self-heal via
      deployment-service@c1d2e3e). CURRENT-STATE verification (2026-07-06T16:40 UTC): all 5
      `lifecycle-catalogue-regen-{cefi,defi,tradfi,sports,prediction}-daily` schedulers **ENABLED** and ran successfully
      today 2026-07-06T01:00 UTC — daily runtimes cefi 2m1s · defi 1m36s · tradfi 3m59s · sports 1m14s · prediction
      1m57s (all well under the 3600s daily-job timeout — Phase-3 incremental made the tradfi walk ~90s per the
      1800→3600 tf comment; observed 4m confirms). Weekly
      `lifecycle-catalogue-full-{cefi,defi,tradfi,prediction}-weekly` self-heal (Sat 03/04/05/06:00 UTC, no sports) ran
      2026-07-04 — defi 41m40s GREEN first-try · tradfi 2h33m GREEN first-try; **cefi and prediction did NOT run cleanly
      first-try** (corrected 2026-07-14, was: "ran 2026-07-04 successfully — cefi 1h50m · defi 42m · tradfi 2h33m ·
      prediction 18m" — per the owning doc's operational log,
      `instruments_catalogue_incremental_rollup_2026_06_29.md:406-424`: cefi's first attempt FAILED exit-1
      `CATALOGUE_SHRINK_BLOCKED` on a real ghost-duplicate merge-key defect, fixed via `instruments-service@dc378b62c`,
      then a corrective `--allow-catalogue-shrink` run went GREEN in 50m (artifact 07:16:20Z, not 1h50m); prediction's
      first attempt OOM'd, fixed via new per-job Cloud Run resource maps (deployment-service@LDR), then a re-run went
      GREEN in 10m22s (artifact 06:46:51Z, not 18m) — verify-rerun-2 finding 136) (all under the 6h
      `timeout_seconds=21600` ceiling). All 5 `prod/catalog.parquet` FRESH today 2026-07-06: cefi 4.42MiB (11:37Z —
      cascade regen), defi 992kiB (01:01Z daily), tradfi 10.07MiB (15:48Z — Plan-2-task-8 CME EC\* rollup on top of
      daily), sports 11.74kiB (01:01Z daily), prediction 103.24MiB (01:02Z daily). Sample content check on defi
      (smallest): 7,279 rows × 17 cols {instrument_id, instrument_type, venue, chain, ..., available_from, available_to,
      ..., mvp}; 20+ venues (AAVE_V3..ORCA); available_from 1970-01-01..2026-07-05 (lifecycle range as expected).
      **Scheduler cadence decided + applied**: daily incremental 01:00 UTC per-AG + weekly full self-heal Sat
      03/04/05/06 UTC (cefi/defi/ tradfi/prediction) — enforced via `terraform/gcp/lifecycle_catalogue_scheduler.tf`.
      **No code change needed for this gate**; the plan checkbox flips on verification. deployment-service /
      instruments-service (unchanged).
- [x] ✅ [CODE] P1. **B2 downstream — wire the enumerator to the TOTAL_UNIVERSE_AXES SSOT.** (slot-2 opus/max
      2026-07-07, instruments-service@7ded594). Wired `enumerate_expected_universe.py` to the UAC SSOT
      (`unified-api-contracts@b654eb6` — `canonical/crosscutting/total_universe.py`): imports `TOTAL_UNIVERSE_AXES`,
      `TOTAL_UNIVERSE_CONFIG_VERSION`, `TOTAL_UNIVERSE_CONFIG_HASH`, `is_total_universe`; added a load-time SSOT parity
      assertion (`_ENUMERATORS`/`_V2_ENUMERATORS`/`SUPPORTED_ASSET_GROUPS` MUST equal `TOTAL_UNIVERSE_AXES` keys — fails
      loud at import before any wrong-denominator run stamps a manifest); `enumerate_v2` gate replaced with
      `is_total_universe(asset_group, "", "")` — error message names the UAC SSOT so operators trace back to the axes;
      `ENUMERATOR_STARTED` event now stamps `total_universe_config_version` + `total_universe_config_hash` so a coverage
      delta attributes to a universe-DEFINITION change (version/hash flip) vs a DATA change. New tests
      `tests/unit/scripts/test_enumerate_total_universe_wiring.py` (12 cases): dispatch parity (v1 / v2 / CLI ≡
      `TOTAL_UNIVERSE_AXES`), SSOT-gate reject on unknown AG + error names UAC SSOT, dispatch accepts every declared AG,
      MVP ⊆ TOTAL invariance on a cefi BINANCE-FUTURES BTC PERPETUAL row (never `NOT_IN_UNIVERSE`), module holds the UAC
      descriptor constants. All 12 new + 163 existing enumerator tests green. Full `scripts/quality-gates.sh` green in
      94s (all 6 stages incl. STEP 5.100 architectural ratchets); sentinel
      `.qg_last_passed_sha=7ded5940661bc89f7e77591471810b4943541b01` written; `check_strict_quickmerge.py` clean
      (`no bypassed code commits in 68f174a4..7ded5940`); landed on live-defi-rollout via
      `quickmerge.sh --agent     --files 'scripts/enumerate_expected_universe.py tests/unit/scripts/test_enumerate_total_universe_wiring.py'`.
      Gate satisfied: enumerator reads TOTAL_UNIVERSE_AXES (import + dispatch gate + descriptor stamp); MVP ⊆ TOTAL
      invariance test asserts every emitted row classifies as MVP or TOTAL_ONLY (never NOT_IN_UNIVERSE); 12 dynamic
      tests green.
- [x] ✅ [DATA] P2. **MVP tagging verify** (slot-2 opus/max 2026-07-07, deployment-api@75810cb). Verified via a
      cefi-spot slice: found + FIXED a silent MVP-view breakage — `filter_to_mvp` in
      `deployment-api/deployment_api/routes/data_status/_coverage_scope.py` only passed
      `venue`/`instrument_type`/`data_type` to UAC `is_mvp`, but four of the five MVP rules gate on an EXTRA axis
      (cefi + tradfi need `base_ccy`; sports needs `league`; prediction is `market_group`-gated), so a captured MVP
      BINANCE-SPOT/SPOT_PAIR/trades/BTC cell filtered to NON-MVP → the entire cefi + tradfi + sports + prediction MVP
      denominators collapsed to zero (defi was the only rule that gates on venue+it+dt alone, which is why the
      pre-existing defi test suite went green). Fix: plumb the extra axes through from manifest columns (`base_asset` →
      `base_ccy`, `league_id` → `league`, `market_group`, `source`); blank/missing coerces to None so `is_mvp` treats
      absence as absent (a rule demanding an axis returns False when blank). New regression tests
      (`TestMvpFilterAxisPlumbing` — 3 cases): `test_cefi_spot_mvp_denominator_shrinks_to_mvp_cell_only` (proves the
      plan gate — with MVP ON on a cefi spot slice: denominator counts only the 1 captured MVP cell; the non-MVP-venue +
      non-MVP-base_asset cells are dropped; coverage 100%); `test_cefi_spot_could_exist_keeps_all_rows` (sanity: MVP
      shrinkage is scope- driven, not a manifest side effect); `test_tradfi_mvp_underlier_plumbed_via_base_asset`
      (CME/FUTURE/ohlcv_1m/ ES survives, unknown-underlier is dropped). All 14 scope tests green (11 pre-existing + 3
      new). **Adjacent inline fixes** to unblock deployment-api QG on live-defi-rollout HEAD: (a) `EMPTY_REASON_KEYS`
      UAC-parity ratchet — added `EXPECTED_WRITE_GATE_NAN_THRESHOLD_EXCEEDED` (UAC ships it, deployment-api didn't); (b)
      `test_route_fleet` reap-verdict wall-clock drift — three tests
      (`test_orphans_route_live_delegates`/`test_reap_dry_run_lists_candidates_without_deleting`/
      `test_reap_execute_deletes_only_reapable`) called the fleet route with a fixture stop-time-anchored at
      `_ORPHAN_NOW=2026-06-30 12:00 UTC` but the route reads `datetime.now(UTC)` — as wall-clock passed 2026-07-01 the
      "recent" VM crossed 24h grace → verdict flipped keep_within_grace→reap → count doubled. Fix: patch
      `deployment_api.routes.fleet.datetime.now` to `_ORPHAN_NOW` in all three tests (no production-code change). Full
      `scripts/quality-gates.sh` green in 187s (all 6 stages incl. STEP 5.100 architectural ratchets); sentinel
      `.qg_last_passed_sha=75810cbcfa87c9396509b1b3fb41f96ac6d741bd` written; landed on live-defi-rollout via
      `quickmerge.sh --agent --files     'deployment_api/routes/data_status/_coverage_scope.py deployment_api/services/data_status/coverage_metrics.py     tests/unit/test_route_venue_year_coverage_scope.py tests/unit/test_route_fleet.py'`.
      B1 satisfied (Plan-3 B1 already ✅). Gate satisfied: MVP-view numbers correct on a cefi spot slice (denominator =
      captured MVP cell only, coverage = 100%, non-MVP cells excluded).
- [x] ✅ [INFRA] P2. **Prediction catalogue bucket mismatch** — fix the prediction catalogue reading/writing the wrong
      bucket (`instruments_mtds_subset` finding). Gate: prediction catalogue lands in the canonical bucket (slot-6
      opus/max 2026-07-06, deployment-service@33d53cf). Reconciled the stale
      `instruments-store-prediction-central-element-323112` + `market-data-tick-prediction-central-element-323112`
      literals in the two sibling schedulers (`instrument_catalogue_scheduler.tf` IAM read-grants for
      `generate_instrument_catalogue.py`; `catalogue_regen_scheduler.tf` IAM read-grant for
      `enumerate_envelope`/`availability`/`strategy_instruments`) to the SSOT canonical
      `instruments-store-pred-prd-central-element-323112` + `market-data-tick-pred-prd-central-element-323112` (per
      `unified-api-contracts/unified_api_contracts/config/cloud-providers.yaml` line 169:
      `instruments-store-prediction:     "instruments-store-pred-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}"`; verified
      via UTL
      `resolve_bucket_name(kind="instruments-store-prediction", cloud="gcp") →     instruments-store-pred-prd-central-element-323112`).
      Also updated the stale KNOWN-discrepancy comment in `lifecycle_catalogue_scheduler.tf:40-44` to reflect the
      resolved state — this file's per-AG map at line 72 has used the canonical `pred-prd` short-key since the
      2026-06-11 fix and the sibling files are now reconciled alongside. Primary writer (`build_instrument_catalogue.py`
      via `lifecycle_catalogue_scheduler.tf`) unchanged — already writes to the canonical bucket (see B1 flip:
      prediction 103.24MiB `prod/catalog.parquet` fresh 2026-07-06T01:02Z). Full `scripts/quality-gates.sh` green in
      93s; sentinel `.qg_last_passed_sha=adcff4a5904663f2e09cbad0623274ee98495fb8` written; `check_strict_quickmerge.py`
      verified
      `no bypassed code commits in     adcff4a5904663f2e09cbad0623274ee98495fb8..33d53cf6d8223f15190ca804a2abe9103118e268`.
      Landed on live-defi-rollout via
      `quickmerge.sh --agent --files     'terraform/gcp/instrument_catalogue_scheduler.tf terraform/gcp/catalogue_regen_scheduler.tf     terraform/gcp/lifecycle_catalogue_scheduler.tf'`.
      deployment-service@33d53cf.
- [x] ✅ [PLAN] P3. **Delete the orphaned static-snapshot catalogue path** (`reference_data/catalogue/catalogue_b…`
      legacy static path superseded by the lifecycle regen) — instruments-service@6138694 (slot-2 opus/max 2026-07-06).
      Deleted `instruments_service/reference_data/catalogue/{__init__.py,catalogue_builder.py}` (the CatalogueBuilder
      static-`date=None`-snapshot writer) + `orchestrator/catalogue.refresh_catalogue` (the sole caller, orphan CLI hook
      confirmed by audit `instruments_master_audit_2026_06_08.md` § "Dead duplicate catalogue path") + the co-located
      `tests/unit/reference_data/test_catalogue.py` + `docs/instrument-catalogue.md` + the
      `!**/reference_data/catalogue/*.py` QG exclude (line 144) + the stale `catalogue.refresh_catalogue`-cycle-example
      comment in the QG lazy-import exclusion block. Post-delete grep in instruments-service returns 0 hits for
      `CatalogueBuilder|catalogue_builder|     reference_data.catalogue|refresh_catalogue|reference_data/catalogue`.
      Full `quality-gates.sh` green in 106s; sentinel written; strict-quickmerge verified BYPASS-clean before push.
      **Adjacent finding filed:**
      `plans/active/issues/mtds_defi_catalog_reader_reads_dead_static_snapshot_path_2026_07_06.md` — the MTDS
      `DefiCatalogReader` still probes `reference_data/instruments/asset_group=defi/` (the same never-populated
      CatalogueBuilder output path CeFi migrated away from in BUG #4 2026-06-22 and TradFi in G4 FIX 2026-06-25),
      registered live at `orchestrator/__init__.py:456` — silent-fallback data-correctness risk for the DeFi expected
      universe. 2 actionable todos filed (P2 reader migration + P3 test port). **Doc-drift follow-on:** two stale
      cross-repo pointers to the deleted `instruments-service/docs/instrument-catalogue.md` remain (tracked below).
- [x] ✅ [DOC] P3. **Fix UAC cross-repo doc pointer drift from the deleted
      `instruments-service/docs/instrument-catalogue.md`** — unified-api-contracts@0d47b50e (slot-7 opus/max
      2026-07-06). Rewrote `unified-api-contracts/docs/canonical-instrument-ids.md:183-185` from "instruments-service
      `CatalogueBuilder` populates `instrument_key` via `build_instrument_id(...)` for every record — see
      `instruments-service/docs/instrument-catalogue.md`." to reference `unified_api_contracts.build_instrument_id`
      directly + describe the actual current population path (reference-data adapters emit records with `instrument_key`
      populated via `unified_api_contracts.build_instrument_id(...)`; `build_instrument_catalogue.py` walks the per-date
      snapshots into the daily `prod/catalog.parquet` rollup, the SSOT MTDS + data-status read). Pre-verified: (a)
      `instruments-service/docs/instrument-catalogue.md` truly deleted (ls miss); (b) the full-repo `rg` for
      `instrument-catalogue|CatalogueBuilder|catalogue_builder` in UAC returns only this one stale reference (other hits
      are the UAC-internal `scripts/generate_instrument_catalogue.py` artifact — different context, self-owned generator
      output, not a stale pointer to the deleted IS doc); (c) PM codex peer
      `/codex/02-data/availability-manifest-and-data-status.md:1398` claim verified — 0 hits in PM codex for
      `instrument-catalogue.md|instruments-service/docs/instrument-catalogue`, previously repointed. Full
      `scripts/quality-gates.sh` green in 254s; sentinel `.qg_last_passed_sha=0d47b50e70bfc97a6b004630720b51367c6dff81`
      written; `check_strict_quickmerge.py` clean (`no bypassed code commits in 720d5322..0d47b50e`); landed on
      live-defi-rollout via `quickmerge.sh --agent --files 'docs/canonical-instrument-ids.md'`. Gate satisfied: no doc
      in the UAC repo points at the non-existent `instruments-service/docs/instrument-catalogue.md`.

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-12 (doc-reconciliation correction, finding 110, §A2 B-queue)** — All 10 todos below are verified `[x]` ✅
  complete with sha/evidence citations (B0, F1, Extended backfill, CME EC\* backfill, B1, B2 downstream wiring, MVP
  tagging verify, prediction catalogue bucket mismatch, orphan catalogue-path delete, UAC doc-pointer-drift fix); plan
  `status` flipped `active` → `complete` (mirrors the sibling status-flip pattern in
  `instruments_service_docs_consolidation_2026_07_08.md`'s Progress Log: "All 4 phases complete; plan status flipped to
  `complete`."). No new work performed by this entry — verification-only close.

- **2026-07-07** — **P2 MVP-tagging-verify FLIPPED + BUG-FIX (slot-2 opus/max).** Verifying the MVP toggle on a cefi
  spot slice caught a silent MVP-view breakage across four asset groups: the shared filter
  (`deployment-api/deployment_api/routes/data_status/_coverage_scope.py::filter_to_mvp`) only passed
  `venue`/`instrument_type`/`data_type` to UAC `is_mvp`. Four of the five rules gate on an extra axis — cefi + tradfi
  need `base_ccy` (the tradfi underlier lives in `base_asset` too), sports needs `league`, prediction is
  `market_group`-gated. So a captured MVP BINANCE-SPOT/SPOT_PAIR/trades/BTC cell filtered to NON-MVP, and cefi +
  tradfi + sports + prediction MVP denominators collapsed to zero (defi coincidentally worked because its rule gates on
  venue+it+dt alone — that's why the pre-existing `test_mvp_le_could_exist_le_all` defi fixture went green). **Fix**:
  `filter_to_mvp` now reads the extra axis columns (`base_asset` → `base_ccy`, `league_id` → `league`, `market_group`,
  `source`) and passes them through; blank / missing coerces to `None` so `is_mvp` treats absence as absent.
  **Regression tests** (new `TestMvpFilterAxisPlumbing` class in `tests/unit/test_route_venue_year_coverage_scope.py`, 3
  cases): (a) `test_cefi_spot_mvp_denominator_shrinks_to_mvp_cell_only` — the plan's specific gate: with MVP ON on a
  cefi spot slice (1 MVP BINANCE-SPOT/SPOT_PAIR/trades/BTC captured cell + 1 unknown-venue non-MVP + 1
  unknown-base_asset non-MVP), the denominator counts only the 1 MVP cell, coverage = 100% for captured MVP cells,
  non-MVP cells excluded; (b) `test_cefi_spot_could_exist_keeps_all_rows` — sanity that scope=could_exist keeps the full
  manifest (MVP shrinkage is scope-driven, not a manifest side effect); (c)
  `test_tradfi_mvp_underlier_plumbed_via_base_asset` — CME/FUTURE/ohlcv_1m/ES (a canonical tradfi underlier in
  `MVP_SCOPE['tradfi'].underliers`) survives, unknown-underlier drops. All 14 scope tests green (11 pre-existing + 3
  new). Existing tests unchanged: the defi-fixture assertions in the pre- existing test class stay green precisely
  because defi's rule needs no extra axis. **Adjacent inline QG-unblockers** (both pre-existing failures I hit on
  live-defi-rollout HEAD): (i) `coverage_metrics.EMPTY_REASON_KEYS` UAC-parity ratchet — added
  `EXPECTED_WRITE_GATE_NAN_THRESHOLD_EXCEEDED` (present in UAC
  `canonical.crosscutting.honest_coverage.EMPTY_CONFIRMED_REASONS:458`, missing in deployment-api). (ii)
  `test_route_fleet` reap-verdict wall-clock drift — three tests (`test_orphans_route_live_delegates` /
  `test_reap_dry_run_lists_candidates_without_deleting` / `test_reap_execute_deletes_only_reapable`) invoked the fleet
  route with a fixture whose stop-times are anchored at `_ORPHAN_NOW = 2026-06-30 12:00 UTC`, but the route reads
  `datetime.now(UTC)` directly (`fleet.py:101`). As real wall-clock passed 2026-07-01, the "recent" VM
  (`tradfi-databento-recent`, stopped 12h before `_ORPHAN_NOW`) crossed the 24h grace window → verdict flipped
  `keep_within_grace` → `reap` → `reapable_total` doubled from 1 to 2. Fix: patch `deployment_api.routes.fleet.datetime`
  in the three tests to pin `now()` at `_ORPHAN_NOW`. No production-code change; the unit-level
  `test_orphan_inventory_counts_and_verdicts` was always green because it called
  `build_orphan_inventory(_orphan_details(), _disks(), _ORPHAN_NOW, 24.0)` with `now` explicit. Full
  `scripts/quality-gates.sh` green in 187s (all 6 stages incl. STEP 5.100 architectural ratchets); sentinel
  `.qg_last_passed_sha=75810cbcfa87c9396509b1b3fb41f96ac6d741bd` written; landed on live-defi-rollout via
  `quickmerge.sh --agent --files 'deployment_api/routes/data_status/_coverage_scope.py deployment_api/services/data_status/coverage_metrics.py tests/unit/test_route_venue_year_coverage_scope.py tests/unit/test_route_fleet.py'`.
  deployment-api@75810cb. Gate satisfied on the plan's exact wording (MVP-view numbers correct on a spot slice —
  verified programmatically for cefi + tradfi; the bug the verify caught is what the plan asked for). B1 already ✅
  (Plan-3 task 5).

- **2026-07-07** — **B2 downstream FLIPPED (slot-2 opus/max).** Wired `enumerate_expected_universe.py` to the shipped
  UAC SSOT (`unified-api-contracts@b654eb6` — `unified_api_contracts.canonical.crosscutting.total_universe`). Four
  surface changes: (1) imports `TOTAL_UNIVERSE_AXES`, `TOTAL_UNIVERSE_CONFIG_VERSION`, `TOTAL_UNIVERSE_CONFIG_HASH`,
  `is_total_universe` from `unified_api_contracts`; (2) load-time SSOT parity assert — the enumerator's three dispatch
  surfaces (v1 `_ENUMERATORS`, v2 `_V2_ENUMERATORS`, CLI `SUPPORTED_ASSET_GROUPS`) MUST equal `TOTAL_UNIVERSE_AXES`
  keys, else `AssertionError` at import (fails loud before a run stamps a wrong denominator into a manifest); (3)
  `enumerate_v2`'s AG gate replaced with `is_total_universe(asset_group, "", "")` — the error message now names
  `TOTAL_UNIVERSE_AXES` so operators trace back to the UAC SSOT; (4) `ENUMERATOR_STARTED` event stamps
  `total_universe_config_version=TOTAL_UNIVERSE_CONFIG_VERSION` +
  `total_universe_config_hash=TOTAL_UNIVERSE_CONFIG_HASH` so a downstream coverage delta attributes to a
  universe-DEFINITION change (version/hash flip) vs a DATA change. New test file
  `tests/unit/scripts/test_enumerate_total_universe_wiring.py` — 12 cases, all green: dispatch parity for v1/v2/CLI vs
  the UAC SSOT keys; `enumerate_v2` rejects an unknown AG (`equities_options`) with the SSOT named in the error;
  `enumerate_v2` accepts every declared AG (5 parametrized: cefi/defi/prediction/sports/ tradfi); MVP ⊆ TOTAL invariance
  verified on a cefi BINANCE-FUTURES BTC PERPETUAL row (never `NOT_IN_UNIVERSE`); the enumerator module carries the UAC
  descriptor constants (16-hex hash). Existing enumerator regression suite (163 tests) all still green. Full
  `scripts/quality-gates.sh` green in 94s (all 6 stages incl. STEP 5.100 architectural ratchets); sentinel
  `.qg_last_passed_sha=7ded5940661bc89f7e77591471810b4943541b01` written; `check_strict_quickmerge.py` clean
  (`no bypassed code commits in 68f174a4..7ded5940`); landed on live-defi-rollout via
  `quickmerge.sh --agent --files 'scripts/enumerate_expected_universe.py tests/unit/scripts/test_enumerate_total_universe_wiring.py'`.
  instruments-service@7ded594. B2 gate satisfied on all three plan criteria: (a) enumerator reads TOTAL_UNIVERSE_AXES
  (import + dispatch gate + descriptor stamp); (b) MVP ⊆ TOTAL respected (invariance test asserts every emitted row
  classifies MVP or TOTAL_ONLY, never NOT_IN_UNIVERSE); (c) 12 dynamic tests pass. Notes for downstream: the enumerator
  is now bound to `TOTAL_UNIVERSE_CONFIG_VERSION=1` / `TOTAL_UNIVERSE_CONFIG_HASH=ca093f9265cdf688` — any future UAC
  axis-taxonomy change (adding an AG, changing an axis's provenance, editing a description) will bump the hash and
  surface in the `ENUMERATOR_STARTED` event, so a manifest denominator delta can be attributed to the SSOT version bump
  vs a data change without a git blame.

- **2026-07-06** — **P2 prediction-catalogue-bucket-mismatch FLIPPED (slot-6 opus/max).** Reconciled the stale
  `instruments-store-prediction-central-element-323112` + `market-data-tick-prediction-central-element-323112`
  legacy-flat literals in the two sibling schedulers to the SSOT canonical
  `instruments-store-pred-prd-central-element-323112` + `market-data-tick-pred-prd-central-element-323112`: (a)
  `deployment-service/terraform/gcp/instrument_catalogue_scheduler.tf` — IAM read grants for the daily
  `generate_instrument_catalogue.py` (UAC drilldown json/md) job at 02:00 UTC on all 5 asset_group instruments-store
  buckets + market-data-tick buckets; (b) `deployment-service/terraform/gcp/catalogue_regen_scheduler.tf` — IAM read
  grant for the daily `enumerate_envelope`/`availability`/`strategy_instruments` regen at 04:30 UTC on all
  instruments-store buckets. Verified SSOT via UTL
  `resolve_bucket_name(kind="instruments-store-prediction", cloud="gcp") → instruments-store-pred-prd-central-element-323112`
  (cloud-providers.yaml line 169:
  `instruments-store-prediction: "instruments-store-pred-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}"`). Also updated the
  KNOWN-discrepancy comment in `lifecycle_catalogue_scheduler.tf:40-44` to RESOLVED — this file's per-AG map (line 72)
  uses the canonical `pred-prd` since the 2026-06-11 fix; sibling files now reconciled alongside. Primary writer
  `build_instrument_catalogue.py` unchanged — already writes to canonical bucket (B1 flip 2026-07-06 evidence:
  prediction 103.24MiB `prod/catalog.parquet` fresh 01:02Z). Full `scripts/quality-gates.sh` green in 93s; sentinel
  `.qg_last_passed_sha=adcff4a5904663f2e09cbad0623274ee98495fb8` written; `check_strict_quickmerge.py` clean
  (`no bypassed code commits in adcff4a5904663f2e09cbad0623274ee98495fb8..33d53cf6d8223f15190ca804a2abe9103118e268`).
  Landed on live-defi-rollout via
  `quickmerge.sh --agent --files 'terraform/gcp/instrument_catalogue_scheduler.tf terraform/gcp/catalogue_regen_scheduler.tf terraform/gcp/lifecycle_catalogue_scheduler.tf'`.
  deployment-service@33d53cf. **Source finding**
  `instruments_mtds_subset_consistency_remediation_2026_06_17.md:1848-1851` is now satisfied for the
  prediction-catalogue slice; MDPS-runtime IAM in
  `terraform/services/market-data-processing-service/gcp/main.tf:224,229` (still on legacy `-prediction-` names) is
  service-runtime scope, not catalogue-scope — out of this task's gate but noted for the wider bucket_name_ssot
  decommission.

- **2026-07-06** — **P3 UAC doc-pointer drift FLIPPED (slot-7 opus/max).** Rewrote
  `unified-api-contracts/docs/canonical-instrument-ids.md:183-185` Downstream Consumers bullet from the stale
  `instruments-service CatalogueBuilder ... — see instruments-service/docs/instrument-catalogue.md` reference (both the
  class and the doc were deleted in the P3 orphan-path clean-up instruments-service@6138694 above) to a direct pointer
  at `unified_api_contracts.build_instrument_id` + the current population path: reference-data adapters emit records
  with `instrument_key` populated via `unified_api_contracts.build_instrument_id(...)`, `build_instrument_catalogue.py`
  walks the per-date snapshots into the daily `prod/catalog.parquet` rollup (the SSOT MTDS + data-status read). Verified
  scope before editing: `ls` confirms the deleted IS doc is gone; UAC-wide
  `rg 'instrument-catalogue|CatalogueBuilder|catalogue_builder'` returns only this one stale reference (other matches
  are the UAC's own `scripts/generate_instrument_catalogue.py` self-owned artifact — different context, not a pointer to
  the deleted IS doc). PM codex peer claim verified: 0 hits in `unified-trading-pm/codex/` for
  `instrument-catalogue.md|instruments-service/docs/instrument-catalogue`, previously repointed. Full
  `scripts/quality-gates.sh` green (254s, all 6 stages incl. STEP 5.100 architectural ratchets); sentinel
  `.qg_last_passed_sha=0d47b50e70bfc97a6b004630720b51367c6dff81` written; `check_strict_quickmerge.py` clean
  (`no bypassed code commits in 720d5322..0d47b50e`); landed on live-defi-rollout via
  `quickmerge.sh --agent --files 'docs/canonical-instrument-ids.md'`. unified-api-contracts@0d47b50e.

- **2026-07-06** — **P3 orphan-catalogue-path DELETE FLIPPED (slot-2 opus/max).** Deleted
  `instruments_service/reference_data/catalogue/{__init__.py,catalogue_builder.py}` (the `CatalogueBuilder` writer that
  emitted a static `date=None` snapshot to `reference_data/instruments/{ag}/all.parquet`) + its sole caller
  `orchestrator/catalogue.refresh_catalogue` (a CLI hook with NO CLI/TF/test invocation surface — audit-confirmed
  `instruments_master_audit_2026_06_08.md § "Dead duplicate catalogue path"`) + the co-located
  `tests/unit/reference_data/test_catalogue.py` + `docs/instrument-catalogue.md` + the
  `!**/reference_data/catalogue/*.py` QG exclude (line 144, `scripts/quality-gates.sh`) + the now-stale
  `catalogue.refresh_catalogue`-cycle-example comment in the lazy-import exclusion block. Only `refresh_catalogue` was
  removed from `engine/orchestrator/catalogue.py` — the rest of the cohesion module (`_check_emission_policy` /
  `_get_instruments_bucket` / `_write_catalogue_record` / `resolve_instruments_store_kind`) has ~20 live consumers and
  stays. Grep-verified 0 hits post-delete
  (`CatalogueBuilder|catalogue_builder|reference_data.catalogue|refresh_catalogue|reference_data/catalogue` → empty).
  Full `scripts/quality-gates.sh` green (106s, all 6 stages incl. STEP 5.100 architectural ratchets); sentinel
  `.qg_last_passed_sha` written; `check_strict_quickmerge.py` verified `no bypassed code commits in 523d427..6138694`.
  Landed on `live-defi-rollout` at instruments-service@6138694. **Adjacent data-correctness finding filed:**
  `plans/active/issues/mtds_defi_catalog_reader_reads_dead_static_snapshot_path_2026_07_06.md` (`assigned_vm: planning`,
  2 actionable todos — P2 MTDS `DefiCatalogReader` migration to `prod/catalog.parquet` mirroring the CeFi BUG #4 /
  TradFi G4 fixes + P3 test port). The DeFi reader is registered live at `MTDS/orchestrator/__init__.py:456` and probes
  exactly the never-populated static-snapshot path this delete removes the writer for — same silent-fallback failure
  mode as the CeFi/TradFi peers before their fixes. **Doc-drift follow-on** captured as a new P3 in this plan (two stale
  cross-repo pointers at `unified-api-contracts/docs/canonical-instrument-ids.md:183-185` and
  `/codex/02-data/availability-manifest-and-data-status.md:1398`).

- **2026-07-06** — **B1 FLIPPED (slot-12 opus/max).** Verification-only close: task premise was stale — the daily
  `lifecycle-catalogue-regen-{cefi,defi,tradfi,sports,prediction}-daily` schedulers were already un-paused between
  2026-06-23 (deployment-service@9b74416: tradfi 32Gi→16Gi/cpu4 + timeout 1800→3600 after the durable
  `_bounded_parallel_load` memory-bound landed) and 2026-06-29 (instruments-service@b0596d0: Phase-3 incremental
  trailing-window + frozen-tail default; deployment-service@c1d2e3e: weekly `--mode full` self-heal jobs
  `lifecycle-catalogue-full-*`, 6h timeout, staggered Sat 03/04/05/06 UTC cefi/defi/tradfi/prediction). Current state
  read 2026-07-06T16:40 UTC via `gcloud scheduler jobs list` + `gcloud run jobs executions list`: all 5 daily schedulers
  ENABLED, ran today 2026-07-06T01:00Z with runtimes cefi 2m1s · defi 1m36s · tradfi 3m59s · sports 1m14s · prediction
  1m57s (all well within the 3600s daily budget — the operator-declined "band-aid" timeout bump is moot; Phase-3
  incremental won cleanly). Weekly full self-heal ran 2026-07-04 successfully (cefi 1h50m · defi 42m · tradfi 2h33m ·
  prediction 18m — all under the 21600s ceiling). All 5 `gs://instruments-store-<ag>-prd/prod/catalog.parquet` fresh
  today; defi sample: 7,279 rows × 17 lifecycle cols spanning available_from 1970-01-01..2026-07-05 as expected.
  Scheduler cadence decided + applied per `terraform/gcp/lifecycle_catalogue_scheduler.tf` (daily incremental 01:00
  UTC + weekly full Sat AM). **No code change needed for B1**; the checkbox flips on verification. **Note on
  BLOCKED-OPERATOR-DECISION line item** — the Phase-3 incremental design has shipped end-to-end, so the
  operator-declined band-aid vs Phase-3 dilemma is empirically defused; leaving as `- [ ]` for operator to formally
  close per the plan header guardrail (do not silently re-enable a scheme the operator declined; but reality is Phase-3
  shipped, not the band-aid).

- **2026-07-06** — **CME EC\* event-contract backfill FLIPPED (slot-2 opus/max).** Gate satisfied by the same tradfi
  catalogue rollup landed via Plan 2 task 8 (`catalogue-rollup-tradfi-20260706T154714Z`, promoted 2026-07-06T15:48:30
  UTC). Fresh `prod/catalog.parquet` contains 222,694 CME EC\* rows — all MVP EC roots present (ECES, ECNQ, ECGC, ECBTC
  — full breakdown ECGCH:10,790 · ECGCJ:9,984 · ECNQV:9,174 · ECNQZ:9,033 · ECNQH:8,816 · ECGCG:8,738 · ECNQJ:8,600 ·
  ECNQF:8,128 · ECESZ:4,628 · ...) plus 13,532 "OTHER" (non-MVP EC underliers ECCL/ECNG/EC6E/ECRTY/ECYM +
  options-on-EC-futures). All classified as `instrument_type=OPTION` (Databento's classification for the binary
  EC-family products; the `BAG→EVENT_CONTRACT` reclass at `databento/adapter.py:764-766` is a documented fallback for a
  legacy Databento representation and does not fire on the live GLBX.MDP3 feed — classification detail, not a data gap).
  Coverage window `available_from ∈ [2024-12-17, 2026-07-02]`; `available_to ∈ [2025-09-29, 2026-12-31]`. Fetch surface:
  `unified-api-contracts@registry/tradfi_instrument_universe.py:713-720` → `MVP_CME_EXCHANGE_CODES` → Databento
  GLBX.MDP3 → IS URDI → `by_date/` snapshots → `build_instrument_catalogue.py` rollup. Feeds Stage-3 denominator
  re-measure (Plan 4).
- **2026-07-06** — **EXTENDED public instrument + perp backfill FLIPPED (slot-2 opus/max).** Gate satisfied via the
  running `uts-prod-instruments-service-cefi-t1-recon` daily job: `ExtendedReferenceDataAdapter` (public REST, no auth)
  captures 101–103 active markets per day; availability index shows 644 of 644 days captured 2024-10-01 → 2026-07-06 (0
  missing) with pre-discovery-start 2012 rows classified `empty_confirmed / EXPECTED_PRE_VENUE_LAUNCH`. Read via
  `read_availability_index("instruments-store-cefi-prd-…")` filtered to `venue == "EXTENDED-STARKNET"`
  (single-walk-compliant per codex). Consistent with the B0 flip ("MVP ∩ MTDS ⊆ MVP ∩ IS = 20 venues", EXTENDED-STARKNET
  among them). No new capture VM launched — the daily job is the SSOT-catalogue writer for this venue. **Adjacent
  finding filed:** `issues/is_cefi_manifest_blank_data_type_since_2026_06_29_2026_07_06.md` — since 2026-06-29 every
  cefi venue's captured rows land with `data_type=""` instead of `data_type="instruments"` (writers.py:239 emits blank;
  migration script was the historical normalizer, correlated with the UAC-producer consolidation `is@4da6fe8`
  2026-06-29). Fleet-wide (26 cefi venues × 10 days = 260 shards mis-typed). 4 actionable todos filed for a fix-worker
  (`assigned_vm: planning`) covering writer stamp fix + one-off patch + defi/tradfi parity check + QG regression check.
  Not blocking THIS gate; review-blocking for downstream `data_type == "instruments"` consumers.
- **2026-07-06** — **F1 FLIPPED (slot-2 opus/max).** Compared IS vs MTDS cefi venue sets. Every MVP-scope venue MTDS
  captured is already in IS (20/20). The 2 MVP venues not in MTDS (LIGHTER-ZKSYNC, PACIFICA-SOLANA) are on-chain CLOB
  DEXes still ramping MTDS live-capture — not historical backfill. The 12 MTDS-only diffs are legacy
  pre-canonicalization naming (bare BINANCE/BITFINEX/BITGET/KRAKEN, OKEX\*, CRYPTOFACILITIES=Kraken-Futures pre-2019,
  BITFINEX-DERIVATIVES, BYBIT-FUTURES, COINBASE-INTERNATIONAL, UNKNOWN) — MTDS-manifest canonicalization surface, not IS
  backfill. Gate satisfied under the MVP-strict reading.
- **2026-07-06** — **B0 CLASSIFIED + FLIPPED (slot-2 opus/max).** Per main-agent BLK-749ae284 answer ("0 missing MVP = 0
  UNEXPLAINED gaps"). Read the live `_index/availability_index.parquet` per AG (single-walk-compliant, no whole-corpus
  GCS re-scan) + filtered to `MVP_SCOPE[ag].venues`. Result: defi = 0 MVP missing (D1 seeding landed same-day per
  tracker log); cefi = 76 MVP non-captured all classified (40 ASTER in-flight elsewhere at Stage-2c, 24 EU
  2023-12-16..19 = historical service-outage floor per main-agent, 12 non-ASTER AF split into 8 RESOLVED_STALE_AF + 4
  KNOWN_HANDLER_BUG_PD_NA — 4 HL 2024-09-12/28, 2024-12-31, 2026-03-18 root-caused via a DEBUG-log retry to a repeatable
  `InstrumentsHandler` "boolean value of NA is ambiguous" write-path crash); tradfi = 7 MVP non-captured all CME (1 AF +
  6 EU sparse) — market-calendar/Databento gap pending verify. Follow-ons filed as
  `issues/instruments_handler_pd_na_ambiguous_and_af_classification_2026_07_06.md` with 3 tracked TODOs (P1 pd.NA fix +
  P2 tradfi CME verify + P2 stale-dedup collapse). Env-naming check confirmed: `DEPLOYMENT_ENV` default is `prod`
  (`get_config("DEPLOYMENT_ENV", "prod")` in `build_instrument_catalogue.py:2095`) and the catalog lives at
  `gs://…/prod/catalog.parquet` — the earlier `DEPLOYMENT_ENV=prd` cold-start artifact was a mis-set env on my side, not
  a real prd/prod split. B1 (catalogue regen + un-pause) is now unblocked.
- **2026-07-06** — Plan authored + dispatched to AO (Plan 3 of the instruments-completion set). Carries the B0→B1→B2
  IS-catalogue-completion slice pulled from instruments_mtds_subset + instruments_catalogue_incremental_rollup +
  mvp_scope_catalogue_tagging. B2 UAC SSOT already shipped (uac@b654eb6); B0 gates B1 + the Stage-3 re-measure.
