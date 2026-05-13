---
name: manifest-cross-asset-rescan-design-2026-05-08
type: plan
plan_type: design
asset_group: cross-cutting
owner: ikenna
status: active
priority: P1
created: 2026-05-08
last_updated: 2026-05-12
parent: manifest_migration_master_2026_05_07
related_plans:
  - manifest_migration_master_2026_05_07
  - gcs_migration_bundle_pipeline_mode_2026_05_08
  - writegate_honest_coverage_endtoend_2026_05_06
locked_by: live-defi-rollout
locked_since: 2026-05-08
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
estimate_calibration_note: |
  Dominant work: infra (VM launches, reconciler runs, log analysis) + design (drift-axis extensions). Using infra class (0.8×).
  Baseline 3 AI-days covers: axis 7-8-9 extension (0.5d), 5-VM dry-runs + log analysis (1.0d), apply-flips per AG (1.0d), codex updates (0.5d).
  Updated 2026-05-13 (slot 6 substantive touch).
---

> **✅ VMs COMPLETE 2026-05-13 ~09:00 UTC (run 2)** — All 5 manifest-recon-all VMs completed successfully. Logs at `gs://deployment-scripts-central-element-323112/vm-logs/manifest-recon-{ag}-20260513-074{716,736}/run.log`. Gate 3 results populated below. Apply-flips blocked on Gate 1 (slot 2 ping).

> **🟡 FOLDED INTO UMBRELLA — `manifest_evolution_master_2026_05_08`** (codified 2026-05-08)
>
> This plan's manifest-touching scope MUST execute as part of the umbrella's gate sequence — NOT in isolation. Operator
> direction: "manifest, code, and data migrate in the same group plan to avoid collision risk; force batch execution;
> don't allow execution in isolation." Three-axis invariant: schema (UAC) + writer code (UTL + adapter callsites) + GCS
> data layout co-evolve.
>
> Child of: [`plans/epics/manifest_evolution_master_2026_05_08.md`](../epics/manifest_evolution_master_2026_05_08.md)
>
> This plan's phases land in gate(s): **G5** (rescan --apply-flips against full v8 manifest)

# Manifest cross-asset rescan — design (2026-05-08, Tab 3 separate scope)

> Item 5 of Tab 3 in [`work_split_2026_05_08_ikenna.md`](work_split_2026_05_08_ikenna.md). Tab 3 (Ikenna) designs the
> rescan flip schema; Harsh Tab 4 runs the rescan VM (mechanical execution). The actual rescan Python script
> (`cross_asset_rescan.py`) is Harsh Tab 4's scope; this doc + the launcher are Tab 3's scope. Launcher script
> (`deployment-service/scripts/vm/launch-cross-asset-rescan-vm.sh`) is queued as a follow-up; not shipped in this
> session due to rate-limit cap on the launcher sub-agent.

## Why

`manifest_migration_master_2026_05_07` Stage 4 needs a cross-asset rescan post-CeFi VM drain. The rescan walks every
parquet on disk + cross-checks vs the canonical manifest; flips disagreements vs immutable; routes triage cases to
operator. This is a superset of the 2026-05-04 phantom audit (which produced 354 residual phantoms after auto-fixing
130k); the rescan should drop residual phantom count to 0 across all 5 asset_groups.

## Rescan flip schema (closed-set)

Three classes per (manifest_row, on-disk parquet) disagreement:

### A — Mutable (rescan auto-flips to match disk)

| Field            | Reason it's mutable                                                                    |
| ---------------- | -------------------------------------------------------------------------------------- |
| `capture_status` | Disk parquet existence vs manifest row state — reconcile to disk reality.              |
| `error_reason`   | Backfilled when reconciler classifies via UAC `EMPTY_CONFIRMED_REASONS` / typed-error. |
| `attempted_at`   | Stamped at rescan time when missing on legacy rows.                                    |
| `path` column    | Path-template drift between manifest's stamped path and disk's canonical path.         |

### B — Immutable (rescan must respect, NOT flip)

| Field                    | Reason it's immutable                                                          |
| ------------------------ | ------------------------------------------------------------------------------ |
| `pipeline_mode`          | Write-time fact set by writer per UAC `PipelineMode` SSOT. Rescan can't infer. |
| `available_at` (per-row) | Per-row column on parquet; respects `LookaheadBiasError` invariants.           |
| `service_emission_state` | Set by emission-policy hook at write-and-publish boundary, not by rescan walk. |

### C — Triage (rescan flags disagreement, operator decides)

| Field                                                       | Reason it goes to triage                                                                                 |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `asset_group`                                               | Hive-vocab disagreement (`category=` vs `asset_group=` in path) — auto-fix per drift axis 1, not triage. |
| `venue` / `data_type` / `instrument_type` / `instrument_id` | Row-key column drift between manifest and disk path — operator decides which is authoritative.           |
| `chain`                                                     | DeFi-specific row_key axis; mismatch between manifest and disk is structural.                            |

Triage rows go to `gs://{pid}-rescan-triage/{run_id}/triage.jsonl` with shape:
`{manifest_row_key, disk_path, disagreement_class, rescan_recommendation}`. Operator reviews + signs off in the rescan
plan body via a follow-up `## Rescan triage decisions` section.

## Per-asset-group rules

Rescan applies per-asset-group rules per CLAUDE.md "Per-asset-group shard-key matrix":

- **cefi**: per-instrument shard atom — rescan checks each instrument's parquet; auto-fixes instrument_type casing drift
  (PERPETUAL → perpetual per drift axis 2).
- **cefi options/futures**: per-root bundle — rescan checks chain-bundle equivalence (option ↔ options_chain per drift
  axis 5) — auto-fix.
- **tradfi**: rescan respects `venue_trading_calendar` pre-skips; non-trading days stay `empty_confirmed` with
  `error_reason=EXPECTED_HOLIDAY` / `EXPECTED_WEEKEND`.
- **defi**: per-chain shard atom — rescan respects `PROTOCOL_LAUNCH_DATES` + chain-genesis dates; pre-launch days stay
  `empty_confirmed` with `error_reason=EXPECTED_PRE_GENESIS_CHAIN` / `EXPECTED_PRE_VENUE_LAUNCH`.
- **sports**: per-fixture shard — rescan respects `SOURCE_COVERAGE_START` + `KNOWN_COVERAGE_GAPS`; pre-cutoff days stay
  `empty_confirmed` with `error_reason=EXPECTED_PRE_SOURCE_COVERAGE_START` / `EXPECTED_PAUSED_LEAGUE`.
- **prediction**: per-canonical_question_group — rescan respects market lifecycle (`market_created_at` /
  `settlement_time`).

## Concurrency safety

Rescan VM uses `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=cross-asset-rescan-{RUN_TS}` per CLAUDE.md "Per-VM shard
isolation for concurrent backfills". Per-VM shard at `_index/per_vm/cross-asset-rescan-{RUN_TS}.parquet`; manifest
consolidator merges into canonical via last-writer-wins on identical row_key. No race with other in-flight VMs that
follow the same protocol.

## Phantom audit integration

The rescan IS a superset of the existing phantom audit
(`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`). Pre-rescan baseline: 354 residual phantom rows
from 2026-05-04 audit. Post-rescan target: **0 phantoms across all 5 asset_groups**. **9 drift axes** now handled:
1. Hive-key vocab (category= vs asset_group=), 2. Path-prefix drift (raw_tick_data/by_date/ vs top-level),
3. instrument_type casing, 4. schema-4 empty instrument_type, 5. chain-bundle equivalence,
6. DeFi protocol underscore (AAVEV3 ↔ AAVE_V3). **Added 2026-05-13 (instruments-service@1a62547)**:
7. TradFi Databento per-schema-bundle (trades ↔ tbbo), 8. cross-asset venue=UNKNOWN skip,
9. Sports pre-coverage + known-gap UAC clips.
All 9 auto-fix via class A above; any residual goes to class C triage.

## Cross-plan coordination (banner)

Per CLAUDE.md "Cross-Plan Coordination Banners":

- During the rescan window, banner the following plans with
  `🟡 IN-FLIGHT REFACTOR — cross-asset rescan running 2026-05-XX → 2026-05-YY`:
  - `gcs_migration_bundle_pipeline_mode_2026_05_08`
  - `manifest_migration_master_2026_05_07`
  - `writegate_honest_coverage_endtoend_2026_05_06`
- Other agents pause new VM launches in the affected asset_groups until the banner is removed.

## Launcher script (queued; not shipped this session)

The rescan VM launcher (`deployment-service/scripts/vm/launch-cross-asset-rescan-vm.sh`) is required per CLAUDE.md "VM
launcher script SSOT". Spec for the launcher (for the follow-up sub-agent):

- VM name: `cross-asset-rescan-{RUN_TS}` (per CLAUDE.md "VM Naming Convention").
- Default zone: `asia-northeast1-c` (same-region per CLAUDE.md phantom-audit recipe — 18× faster).
- Singleton-lock pattern (per CLAUDE.md "Singleton-locked launchers"): refuses launch if a same-prefix VM is RUNNING in
  the zone unless `--force` passed. Mirror precedent `launch-sfi-forward-poll.sh`.
- Env vars: `MANIFEST_PER_VM_SHARDS=true`, `VM_NAME=cross-asset-rescan-{RUN_TS}`, `RESCAN_ASSET_GROUP=cross_asset_all`,
  `WORKERS=64`, `HTTP_POOL_SIZE=128` (`2*workers`).
- Tarball mode default; `--tarball-from-local` flag for developer path per CLAUDE.md "VM launcher script SSOT" 4-mode
  spec.
- Invokes `instruments-service/scripts/cross_asset_rescan.py` (Harsh Tab 4 ships the Python).
- VM_PREFIX_TO_BUCKET registration: add `cross-asset-rescan-` prefix to
  `deployment-service/scripts/vm/vm_zombie_watchdog.py` per CLAUDE.md.
- Watchdog VM relaunch after the dict update.

## Codex SSOT updates needed (when rescan ships)

Per CLAUDE.md "Post-Plan-Phase Codex Audit HARD RULE":

- **UPDATE** `codex/02-data/availability-manifest-and-data-status.md` § "Phantom audit — re-runnable recipe" — add
  rescan flip schema reference + class A/B/C closed sets above.
- **NEW STUB** `codex/02-data/cross-asset-rescan-protocol.md` — entry-point doc cross-referencing this plan + the
  launcher + the rescan Python script.
- **UPDATE** `codex/00-SSOT-INDEX.md` — register the new cross-asset-rescan-protocol.md doc.

## Reconciliation dependency ordering (HARD RULE — codified 2026-05-12)

**Finding (2026-05-12 operator direction)**: reconciliation scripts currently scan ALL data_types in each asset_group
bucket without service ordering. instruments-service is the reference-data root — its rows (`data_type=instruments`,
`data_type=venue_trading_calendar`) define WHAT should exist for every downstream service (MTDS → MDPS → features).
Flipping downstream phantom rows before instruments-service state is clean produces incorrect `empty_confirmed` reasons
(e.g., `EXPECTED_INSTRUMENT_NOT_LISTED` for an instrument that WAS listed but had a phantom in the reference bucket).

**`--data-types` flag already exists**
([`reconcile_phantom_manifest_rows_all.py:507`](../instruments-service/scripts/reconcile_phantom_manifest_rows_all.py#L507))
— use it to enforce ordering.

**Required execution order for `--apply-flips` pass** (SERIAL gates between passes):

| Pass | Scope                              | `--data-types` flag                                                                                                                                                                                                                                                                                                                                                                                                                  | Parallelism                                 |
| ---- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------- |
| 1    | instruments-service reference rows | `--data-types instruments,venue_trading_calendar`                                                                                                                                                                                                                                                                                                                                                                                    | SERIAL (root — must complete before pass 2) |
| 2    | MTDS raw market data               | `--data-types ohlcv_1h,ohlcv_1m,ohlcv_24h,ohlcv_15m,trades,tbbo,book_snapshot_5,book_snapshot,lending_rates,lst_yields,lending_indices,dex_pools,dex_pool_swaps,perp_funding,oracle_prices,staking_yields,risk_params,rewards,flash_loan_events,governance_events,liquidation_events,bridge_events,position_data,token_transfers,vault_share_price,options_chain,futures_chain,prediction_canonical_question_group,MARKET_LIFECYCLE` | PARALLEL across all 5 asset_groups          |
| 3    | MDPS processed outputs             | `--data-types ohlcv_1h` (where written by MDPS pipeline_mode)                                                                                                                                                                                                                                                                                                                                                                        | PARALLEL across asset_groups, AFTER pass 2  |
| 4    | features services                  | features-specific data_types                                                                                                                                                                                                                                                                                                                                                                                                         | PARALLEL, AFTER pass 3                      |

**For dry-run (audit-only, no flips)**: ordering is not critical — phantoms from all passes can be discovered in
parallel. Only the `--apply-flips` run requires strict ordering.

**Action items** (todos below):

- [x] [SCRIPT] P0. Extend `reconcile_phantom_manifest_rows_all.py` with 3 Databento-aware drift axes to eliminate
      false-positive phantoms identified in the 2026-05-11 dry-run (instruments-service@1a62547 2026-05-13):
      - **Axis 7** (TradFi Databento per-schema-bundle): `trades` and `tbbo` paired schemas share the same prefix;
        accept either data_type needle as capture evidence. Eliminates ~1,017 per-data_type false positives.
      - **Axis 8** (cross-asset venue=UNKNOWN): UNKNOWN sentinel has no resolvable path; skip the venue needle.
        Eliminates ~565 TradFi + ~2k cross-asset false positives.
      - **Axis 9** (Sports pre-coverage + known-gap): rows before source launch date or in registered gaps excluded
        from phantom check via `is_pre_launch_date` + `is_in_known_gap`. Eliminates bulk of 16.8% sports false-positive rate.

- [ ] [DESIGN] P1. Add `## Reconciliation execution order` section to this plan documenting the pass sequence with exact
      `--data-types` values per pass, derived from authoritative scan of each service's `record_captured()` callsites.
      **DEFERRED**: needs per-service data_type ownership audit (1 AI-day).
- [ ] [SCRIPT] P0. Add execution order enforcement to the rescan launcher
      (`deployment-service/scripts/vm/launch-cross-asset-rescan-vm.sh`) — pass 1 completes before pass 2 starts.
      Implement as sequential VM invocations or as a sequenced CLI flag `--pass 1|2|3|4` that the launcher orchestrates.
      **Blocker**: launcher not yet shipped (see "Launcher script" section above).
- [x] [SCRIPT] P1. Dry-run all 5 asset_groups NOW (no ordering needed for audit pass) to get baseline phantom count
      before `--apply-flips`. (deployment-service@b5f25cc + @2ca80d5 2026-05-13): 5 VMs completed — Gate 3 results
      section populated. Run 1 failed silently (python path doubled by setup-script substitution); fixed in
      deployment-service@2ca80d5. Run 2 (07:47 UTC) all completed ~09:00 UTC.
      Log root: `gs://deployment-scripts-central-element-323112/vm-logs/manifest-recon-{ag}-20260513-074{716,736}/run.log`
- [ ] [SCRIPT] P1. **PRE_CUTOVER — switch all 3 reconciliation scripts to `resolve_bucket_name`** (blocked on physical
      bucket migration landing). Currently all 3 scripts hardcode legacy non-env-tiered bucket names (e.g.
      `market-data-tick-cefi-{PROJECT_ID}`) violating the bucket-name SSOT (b+) codified 2026-05-11.
      `cloud-providers.yaml` lines 124-132 already define the canonical env-tiered templates
      (`market-data-tick-cefi-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}`). Scripts must NOT adopt `resolve_bucket_name`
      until the physical GCS buckets are renamed/created — adopting early would point to non-existent buckets and fail
      all manifest reads. **Blocker**: `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 2.6 (create env-tiered
      buckets + copy data + cutover). After that plan's Phase 2.6 gate, update the 3 scripts: replace
      `ASSET_GROUP_CONFIG` hardcoded bucket strings with
      `resolve_bucket_name(cloud=Cloud.GCP, kind="market-data-tick", asset_group=ag)` (and `kind="instruments-store"`
      for sports). Remove hardcoded `PROJECT_ID` constant.

## Dry-run command set — all 5 asset_groups (run on same-region GCE VM, asia-northeast1-c)

> **CLI syntax note (2026-05-12 correction)**: `reconcile_phantom_manifest_rows_all.py` has a `--dry-run` flag.
> `reconcile_expected_absence_reasons.py` and `reconcile_legacy_blank_to_typed_reason.py` do NOT — their default
> (omitting `--apply-flips`) IS scan-only mode. Passing `--dry-run` to the latter two raises an error.

```bash
# Scan-only (dry-run) — ordering does not matter for audit pass (read-only)

# Script 1: reconcile_phantom_manifest_rows_all — HAS --dry-run flag
python instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group cefi --dry-run
python instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi --dry-run
python instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group tradfi --dry-run
python instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group sports --dry-run
python instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group prediction --dry-run

# Script 2: reconcile_expected_absence_reasons — scan-only = omit --apply-flips (NO --dry-run flag)
python instruments-service/scripts/reconcile_expected_absence_reasons.py --asset-group cefi
python instruments-service/scripts/reconcile_expected_absence_reasons.py --asset-group defi
python instruments-service/scripts/reconcile_expected_absence_reasons.py --asset-group tradfi
python instruments-service/scripts/reconcile_expected_absence_reasons.py --asset-group sports
python instruments-service/scripts/reconcile_expected_absence_reasons.py --asset-group prediction

# Script 3: reconcile_legacy_blank_to_typed_reason — scan-only = omit --apply-flips (NO --dry-run flag)
python instruments-service/scripts/reconcile_legacy_blank_to_typed_reason.py --asset-group cefi
python instruments-service/scripts/reconcile_legacy_blank_to_typed_reason.py --asset-group defi
python instruments-service/scripts/reconcile_legacy_blank_to_typed_reason.py --asset-group tradfi
python instruments-service/scripts/reconcile_legacy_blank_to_typed_reason.py --asset-group sports
python instruments-service/scripts/reconcile_legacy_blank_to_typed_reason.py --asset-group prediction
```

## Apply-flips command set (production — run on GCE VM, NOT locally)

> Per CLAUDE.md "Plans Run To Actual Completion": `--apply-flips` must run with `MANIFEST_PER_VM_SHARDS=true` and a
> unique `VM_NAME` to prevent concurrent write races. Run on same-region GCE VM (asia-northeast1-c) per the
> `Phantom audit` recipe in `codex/02-data/availability-manifest-and-data-status.md`.

```bash
# Execution order: pass 1 (reference rows) → pass 2-4 (market data services). See "Reconciliation dependency
# ordering" section above.

# Pass 1 — instruments-service reference rows first (SERIAL gate)
MANIFEST_PER_VM_SHARDS=true VM_NAME=recon-phantom-cefi-$(date +%Y%m%d) \
  python instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group cefi --unphantom
MANIFEST_PER_VM_SHARDS=true VM_NAME=recon-phantom-defi-$(date +%Y%m%d) \
  python instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi --unphantom
# ... (tradfi / sports / prediction — parallel after cefi + defi complete)

# Expected-absence reconciler (--apply-flips; PARALLEL across asset_groups within same pass)
MANIFEST_PER_VM_SHARDS=true VM_NAME=recon-reasons-cefi-$(date +%Y%m%d) \
  python instruments-service/scripts/reconcile_expected_absence_reasons.py --asset-group cefi --apply-flips
# ... (defi / tradfi / sports / prediction)

# Legacy-blank reconciler (--apply-flips; PARALLEL)
MANIFEST_PER_VM_SHARDS=true VM_NAME=recon-legacy-cefi-$(date +%Y%m%d) \
  python instruments-service/scripts/reconcile_legacy_blank_to_typed_reason.py --asset-group cefi --apply-flips
# ... (defi / tradfi / sports / prediction)
```

## Phantom audit Gate 3 results — 2026-05-13

Run 2 (07:47 UTC), deployment-service@2ca80d5. All 5 VMs completed ~09:00 UTC.
VM names: `manifest-recon-{defi,cefi,tradfi,sports,prediction}-20260513-074{716,736}`.

### Script 1 — Phantom captures (manifest `captured`, parquet missing)

| asset_group | Captured rows scanned | Real captures | **Phantom captures** | Top phantom data_types |
| ----------- | --------------------: | ------------: | -------------------: | ---------------------- |
| defi        | 312,900               | 311,602       | **1,298**            | rewards (1,298) |
| cefi        | 1,292,929             | 1,290,706     | **2,223**            | options_chain 435, futures_chain 401, trades 381, derivative_ticker 367, book_snapshot_5 363 |
| tradfi      | 96,101                | 92,125        | **3,976**            | trades 1,017, tbbo 1,017, ohlcv_1m 904 |
| sports      | 686,086               | 586,466       | **99,620**           | TRANSFERMARKT_LEAGUES 75,960, SFI_LEAGUES 12,777, INJURIES 9,843 |
| prediction  | 14,474                | 14,424        | **50**               | trades 50 |
| **TOTAL**   | **2,402,490**         | **2,295,323** | **107,167**          | |

> **Notable**: sports 99,620 phantoms (TRANSFERMARKT_LEAGUES dominant at 75,960) vs 354 in 2026-05-04 audit — scope
> difference (all manifest rows vs partial prior audit) or accumulated debt. cefi has 1,453 phantoms with blank venue
> (likely schema_v4 vestigial rows not fully filtered) + 136 at DERIBIT + 111 at UNKNOWN. tradfi trades+tbbo = 2,034
> of 3,976 (Databento paired-schema artifact; axis 7 eliminates false positives here but real phantoms remain).

### Script 2 — `empty_confirmed` with NULL `error_reason`

| asset_group | Total manifest rows | Null-reason rows | Distribution |
| ----------- | ------------------: | ---------------: | ------------ |
| defi        | 1,606,190           | 0                | — |
| cefi        | 2,632,931           | **3,146**        | all `SOURCE_RETURNED_ZERO` — ready for apply-flip |
| tradfi      | 141,401             | 0                | — |
| sports      | 2,675,696           | 0                | — |
| prediction  | 16,812              | 0                | — |

### Script 3 — Legacy-blank upgradeable to typed `EXPECTED_*` reason

> **⚠️ Classifier broken**: `classify_blank_reason_row() got an unexpected keyword argument 'fixture_manifest'` —
> per-row failure for all candidate rows in defi/sports/prediction. Script continues (non-fatal), result is 0 upgrades.
> Filed as issue: `plans/active/issues/classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md` (P1).

| asset_group | Candidates (% of manifest) | Upgrades | Notes |
| ----------- | -------------------------: | -------: | ----- |
| defi        | 604,951 (37.66%)           | 0        | classifier `fixture_manifest` kwarg error — all rows fail |
| cefi        | 0                          | 0        | clean — no legacy-blank candidates |
| tradfi      | 0                          | 0        | clean — no legacy-blank candidates |
| sports      | 1,868,285 (69.82%)         | 0        | classifier `fixture_manifest` kwarg error — all rows fail |
| prediction  | 41 (0.24%)                 | 0        | classifier `fixture_manifest` kwarg error — all rows fail |

### Gate 3 → Gate 4 gate status

| Gate | Condition | Status |
| ---- | --------- | ------ |
| Gate 1 | Slot 2 `expected_unattempted_propagation_chain` Phase 3+4+2.A complete | 🔴 NOT FIRED — waiting on slot 2 ping |
| Script 3 classifier | `classify_blank_reason_row()` `fixture_manifest` kwarg fix | 🔴 BLOCKED — issue filed P1 |
| cefi Script 2 apply | 3,146 null-reason → `SOURCE_RETURNED_ZERO` stamp | 🟡 READY (no Gate 1 dependency for Script 2) |
| phantom apply-flips | Scripts 1+3 `--apply-flips` per AG | 🔴 BLOCKED on Gate 1 + Script 3 fix |

## Open questions

- Q1 — operator-approval edge cases for class C triage: bundle all class-C rows into one weekly review, or
  per-rescan-run signoff? Default: per-run signoff in this plan body's `## Rescan triage decisions` section.
- Q2 — runtime cost estimate per asset_group: depends on bucket sizes from gcs_migration Phase 0 audit. Defer to that
  audit run.
- Q3 — coordination with in-flight gcs_migration Phase 3 VM execution: the rescan must run AFTER gcs_migration Phase 3
  - Phase 6 phantom cleanup, not before. Otherwise we'd rescan pre-migration paths and produce false triage cases.

## Cross-plan coordination

- `gcs_migration_bundle_pipeline_mode_2026_05_08` — STRICT BLOCKER: rescan runs AFTER Phase 3 + Phase 6 of that plan.
- `manifest_migration_master_2026_05_07` — parent. Stage 4 includes this rescan.
- `writegate_honest_coverage_endtoend_2026_05_06` Phase 4 (typed-error rendering) — consumes `error_reason` populated by
  class A flips during the rescan.
- `manifest_schema_final_gate_2026_05_09` (consolidated v8 SSOT — supersedes archived
  `manifest_v7_schema_migration_design_2026_05_08`) — rescan must respect new v8 immutable columns
  (`service_emission_state`). Note: v8 plan's Phase 3 bundles cross-asset rescan class-A auto-fixes into the same
  parquet walk; this design doc is the SSOT for the rescan semantics.
