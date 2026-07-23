---
doc_type: plan
title: Manifest cross-asset rescan — design (2026-05-08, Tab 3 separate scope)
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, instruments-service]
scope: [engineer, admin]
tags: []
related:
  [
    manifest_migration_SUPERSEDED_2026_05_21,
    gcs_migration_bundle_pipeline_mode_2026_05_08,
    writegate_honest_coverage_endtoend_2026_05_06,
  ]
created: 2026-05-08
priority: P1
last_updated: 2026-05-12
parent: manifest_migration_SUPERSEDED_2026_05_21
locked_by: live-defi-rollout
locked_since: 2026-05-08
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
estimate_calibration_note: "Dominant work: infra (VM launches, reconciler runs, log analysis) + design (drift-axis
  extensions). Using infra class (0.8×).

  Baseline 3 AI-days covers: axis 7-8-9 extension (0.5d), 5-VM dry-runs + log analysis (1.0d), apply-flips per AG
  (1.0d), codex updates (0.5d).

  Updated 2026-05-13 (slot 6 substantive touch).

  "
parent_epic: manifest_master
---

> **✅ Dry-run COMPLETE.** **✅ cefi/defi/tradfi apply-flips COMPLETE 2026-05-13** (cefi Scripts 1+2 done ~08:39 UTC;
> defi/tradfi ~08:34 UTC). **✅ Script 3 classifier fix RESOLVED 2026-05-14** — tarball refresh + UAC merge; re-run
> confirmed 0 upgrades for all groups (TypeError gone; default reasons already most specific; issue CLOSED).
> Sports/prediction Scripts 1+2 apply-flips deferred (separate authorized slot needed; 99,620 sports + 50 prediction
> phantoms).

> **🟡 FOLDED INTO UMBRELLA — `manifest_evolution_SUPERSEDED_2026_05_21`** (codified 2026-05-08)
>
> This plan's manifest-touching scope MUST execute as part of the umbrella's gate sequence — NOT in isolation. Operator
> direction: "manifest, code, and data migrate in the same group plan to avoid collision risk; force batch execution;
> don't allow execution in isolation." Three-axis invariant: schema (UAC) + writer code (UTL + adapter callsites) + GCS
> data layout co-evolve.
>
> Child of:
> [`plans/epics/manifest_evolution_SUPERSEDED_2026_05_21.md`](../epics/manifest_evolution_SUPERSEDED_2026_05_21.md)
>
> This plan's phases land in gate(s): **G5** (rescan --apply-flips against full v8 manifest)

# Manifest cross-asset rescan — design (2026-05-08, Tab 3 separate scope)

> Item 5 of Tab 3 in [`work_split_2026_05_08_ikenna.md`](../archive/work_split_2026_05_08_ikenna.md). Tab 3 (Ikenna)
> designs the rescan flip schema; Harsh Tab 4 runs the rescan VM (mechanical execution). The actual rescan Python script
> (`cross_asset_rescan.py`) is Harsh Tab 4's scope; this doc + the launcher are Tab 3's scope. Launcher script
> (`deployment-service/scripts/vm/launch-cross-asset-rescan-vm.sh`) is queued as a follow-up; not shipped in this
> session due to rate-limit cap on the launcher sub-agent.

## Why

`manifest_migration_SUPERSEDED_2026_05_21` Stage 4 needs a cross-asset rescan post-CeFi VM drain. The rescan walks every
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
2. instrument_type casing, 4. schema-4 empty instrument_type, 5. chain-bundle equivalence,
3. DeFi protocol underscore (AAVE_V3 ↔ AAVE_V3). **Added 2026-05-13 (instruments-service@1a62547)**:
4. TradFi Databento per-schema-bundle (trades ↔ tbbo), 8. cross-asset venue=UNKNOWN skip,
5. Sports pre-coverage + known-gap UAC clips. All 9 auto-fix via class A above; any residual goes to class C triage.

## Cross-plan coordination (banner)

Per CLAUDE.md "Cross-Plan Coordination Banners":

- During the rescan window, banner the following plans with
  `🟡 IN-FLIGHT REFACTOR — cross-asset rescan running 2026-05-XX → 2026-05-YY`:
  - `gcs_migration_bundle_pipeline_mode_2026_05_08`
  - `manifest_migration_SUPERSEDED_2026_05_21`
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

- **UPDATE** `/codex/02-data/availability-manifest-and-data-status.md` § "Phantom audit — re-runnable recipe" — add
  rescan flip schema reference + class A/B/C closed sets above.
- **NEW STUB** `/codex/02-data/cross-asset-rescan-protocol.md` — entry-point doc cross-referencing this plan + the
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
      false-positive phantoms identified in the 2026-05-11 dry-run (instruments-service@1a62547 2026-05-13): - **Axis
      7** (TradFi Databento per-schema-bundle): `trades` and `tbbo` paired schemas share the same prefix; accept either
      data_type needle as capture evidence. Eliminates ~1,017 per-data_type false positives. - **Axis 8** (cross-asset
      venue=UNKNOWN): UNKNOWN sentinel has no resolvable path; skip the venue needle. Eliminates ~565 TradFi + ~2k
      cross-asset false positives. - **Axis 9** (Sports pre-coverage + known-gap): rows before source launch date or in
      registered gaps excluded from phantom check via `is_pre_launch_date` + `is_in_known_gap`. Eliminates bulk of 16.8%
      sports false-positive rate.

- [x] [DESIGN] P1. Add `## Reconciliation execution order` section to this plan documenting the pass sequence with exact
      `--data-types` values per pass, derived from authoritative scan of each service's `record_captured()` callsites.
      **DONE 2026-05-18 (slot 10)** — section added below before "Dry-run command set"; expands the 4-pass table above
      with inputs/outputs/failure-mode/recovery semantics per pass + shard-atom alignment cite. Cross-references
      `data_status_drilldown_shard_atom_alignment_2026_05_07.md` +
      `/codex/02-data/availability-manifest-and-data-status.md`. Done-def cite: PM@<this commit>.
- [x] [SCRIPT] P0. Add execution order enforcement to the rescan launcher
      (`deployment-service/scripts/vm/launch-cross-asset-rescan-vm.sh`) — pass 1 completes before pass 2 starts.
      Implement as sequential VM invocations or as a sequenced CLI flag `--pass 1|2|3|4` that the launcher orchestrates.
      **DONE 2026-05-19 (slot 2)** — deployment-service@880bc3a + instruments-service@5a0b115. Added
      `--pass 1|2|3|4|all` flag, `wait_for_vm_stopped()` helper (polls TERMINATED, max 8h), sequential 4-pass
      orchestration when `--apply` used without `--pass` (dry-run single-VM unchanged). `RESCAN_PASS` env var propagated
      to VM metadata; Python side reads it to pass `--data-types` to reconciler. Stale "Blocker: launcher not yet
      shipped" note was false — launcher existed; only ordering was missing.
- [x] [SCRIPT] P1. Dry-run all 5 asset_groups NOW (no ordering needed for audit pass) to get baseline phantom count
      before `--apply-flips`. (deployment-service@b5f25cc + @2ca80d5 2026-05-13): 5 VMs completed — Gate 3 results
      section populated. Run 1 failed silently (python path doubled by setup-script substitution); fixed in
      deployment-service@2ca80d5. Run 2 (07:47 UTC) all completed ~09:00 UTC. Log root:
      `gs://deployment-scripts-central-element-323112/vm-logs/manifest-recon-{ag}-20260513-074{716,736}/run.log`
- [x] [SCRIPT] P1. Apply-flips: cefi/defi/tradfi Scripts 1+2 — COMPLETE 2026-05-13
      (deployment-service@1a714ec+@574c168). Run 1 (08:19) failed rc=2 — `--apply` not recognized; fixed to
      `--unphantom` (deployment-service@574c168). VMs: `manifest-recon-apply-{cefi,defi,tradfi}-20260513-082713`. All 3
      self-deleted after completion. **cefi**: 2,223 phantom flips + 3,146 null-reason stamps (SOURCE_RETURNED_ZERO)
      ~08:29–08:39 UTC. **defi**: 1,298 phantom flips (rewards) + 0 stamps ~08:27–08:34 UTC. **tradfi**: 3,976 phantom
      flips (trades+tbbo+ohlcv_1m) + 0 stamps ~08:27–08:34 UTC. Sports/prediction apply-flips deferred — needs separate
      authorized slot (99,620 sports phantoms). **DEFERRED**: Script 3 apply-flips for defi/sports/prediction blocked on
      classifier fix (P1 issue filed).
- [x] ✅ **DEFERRED** [SCRIPT] P1. **PRE_CUTOVER — switch all 3 reconciliation scripts to `resolve_bucket_name`**
      (blocked on physical bucket migration landing). Currently all 3 scripts hardcode legacy non-env-tiered bucket
      names (e.g. `market-data-tick-cefi-{PROJECT_ID}`) violating the bucket-name SSOT (b+) codified 2026-05-11.
      `cloud-providers.yaml` lines 124-132 already define the canonical env-tiered templates
      (`market-data-tick-cefi-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}`). Scripts must NOT adopt `resolve_bucket_name`
      until the physical GCS buckets are renamed/created — adopting early would point to non-existent buckets and fail
      all manifest reads. **MIGRATED TO**: `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 2.6 (create
      env-tiered buckets + copy data + cutover). After Phase 2.6 gate, update the 3 scripts: replace
      `ASSET_GROUP_CONFIG` hardcoded bucket strings with
      `resolve_bucket_name(cloud=Cloud.GCP, kind="market-data-tick", asset_group=ag)` (and `kind="instruments-store"`
      for sports). Remove hardcoded `PROJECT_ID` constant. Deferred 2026-05-19 slot-8.

## Reconciliation execution order

> Expands the "Reconciliation dependency ordering" 4-pass table above with per-pass inputs/outputs, failure-mode +
> recovery semantics, and the shard-atom alignment rule. The SERIAL gate (pass 1 → 2) and read-after-write barrier (pass
> 2 → 3) are correctness-load-bearing — dry-run reads commute, but `--apply-flips` requires strict ordering.

### Pass 1 — instruments-service reference rows (SERIAL, root)

- **Scope**: `--data-types instruments,venue_trading_calendar` for every asset_group sequentially.
- **Inputs**: `instruments-store-<ag>-<env>-<pid>/instrument_availability/by_date/day=…/venue=…/instruments.parquet`;
  the manifest's `captured/empty_confirmed/attempted_failed/expected_unattempted` state per (ag, day, venue).
- **Outputs**: phantom `captured` → `attempted_failed` flips and null-reason → `SOURCE_RETURNED_ZERO` stamps on
  reference rows only. These flips define what instruments WERE listable per (day, venue) and therefore drive every
  downstream service's "expected vs missing" classification.
- **Failure mode**: a phantom in instruments-service silently mutates every downstream `empty_confirmed` reason for the
  same shard from `EXPECTED_INSTRUMENT_NOT_LISTED` to `EXPECTED_UPSTREAM_GAP` (or vice-versa) — a Class-A correctness
  bug that only surfaces in `data_status_drilldown` if reference rows are flipped first.
- **Recovery**: idempotent (`--unphantom` re-runs are no-ops on flipped rows); on partial failure re-launch the same
  `VM_NAME` so `MANIFEST_PER_VM_SHARDS=true` per-VM shards converge without double-write. SERIAL gate: pass 2 must NOT
  start until pass 1 reports `STOPPED` on the deployment-service VM ledger.

### Pass 2 — MTDS raw market data (PARALLEL across asset_groups, serial after pass 1)

- **Scope**: every MTDS-owned `--data-types` (ohlcv, trades, tbbo, book_snapshot, lending_rates, lst_yields, dex_pools,
  perp_funding, oracle_prices, etc. — full list at line ~181) across all 5 asset_groups simultaneously.
- **Inputs**: pass-1-flipped reference manifest (read-after-write barrier); per-venue/per-shard parquets in
  `market-data-tick-<ag>-<env>-<pid>/raw_tick_data/by_date/day=…/venue=…/`.
- **Outputs**: market-data manifest flips + typed-reason stamps; per-VM shard parquets under
  `_index/per_vm/<vm>.parquet` that the consolidator merges into canonical `_index/availability_index.parquet` within ~5
  min of VM completion.
- **Failure mode**: a venue/shard with `data_type=trades` flipped but a paired `tbbo` row still claimed `captured` by
  phantom produces inconsistent honest-coverage in `data_status_drilldown`. Axis-7 paired-schema handling in
  [`reconcile_phantom_manifest_rows_all.py:507`](../instruments-service/scripts/reconcile_phantom_manifest_rows_all.py#L507)
  guards against this within pass 2.
- **Recovery**: each (ag, data_type) is its own VM job — failed jobs can be re-launched without affecting parallel jobs.
  Per-VM shard isolation prevents cross-VM write races; if the consolidator misses a per-VM parquet it stays in
  `_index/per_vm/` until the next consolidator tick — no data loss.

### Pass 3 — MDPS processed outputs (PARALLEL, serial after pass 2)

- **Scope**: `--data-types ohlcv_1h` (or whichever MDPS-owned pipeline_mode outputs are present per asset_group; varies
  between cefi/defi/tradfi/sports/prediction).
- **Inputs**: MTDS-flipped raw manifest from pass 2; MDPS-written processed parquets in
  `market-data-tick-<ag>-<env>-<pid>/processed/by_date/…` (path varies per asset_group).
- **Outputs**: MDPS manifest flips; MDPS rows refer to the same shard atom as MTDS but at the processed-output
  granularity (per `data_status_drilldown_shard_atom_alignment_2026_05_07.md`).
- **Failure mode**: MDPS phantom flipped before MTDS pass completes can mis-classify the empty_confirmed reason (e.g.,
  `EXPECTED_NO_OHLCV_FOR_INSTRUMENT` when the underlying tick rows were phantoms now flipped to `attempted_failed`). The
  serial gate prevents this.
- **Recovery**: identical to pass 2 — per-VM-shard isolation, re-launch failed jobs.

### Pass 4 — features services (PARALLEL, serial after pass 3)

- **Scope**: features-specific data_types per family (delta_one, volatility, onchain, calendar, sports, multi-timeframe,
  cross-instrument, prediction). **Inputs**: pass-3-flipped MDPS manifest +
  `features-<family>-<ag>-<env>-<pid>/by_date/…`.
- **Outputs**: features manifest flips with feature-specific `empty_confirmed` reasons.
- **Failure mode**: flipping features before passes 1-3 complete can stamp `EXPECTED_NO_FEATURE_INPUT` on rows whose
  input WAS captured but a phantom in pass 2/3 hid it. **Recovery**: identical to passes 2-3.

### Shard atom alignment (cite CLAUDE.md "Shard-granularity SSOT")

All four passes flip rows at the **same shard atom** the writer used, the manifest consolidator emits, the deployment-UI
drilldown reads, and downstream pre-flight gates check. Atoms: `(asset_group, day, venue, data_type)` for MTDS + MDPS;
`(asset_group, day, family, feature_key)` for features; `(asset_group, day, venue)` for instruments-service. Drift
between writer atom + manifest atom + reconciliation flip atom is a silent correctness bug per CLAUDE.md
"Shard-granularity SSOT (CRITICAL)" + `plans/epics/infrastructure_master.md` 4-pillar validation. Reconcilers derive the
atom from the manifest schema at runtime; do NOT introduce reconciler-specific shard partitioning.

### Cross-references

- **`plans/active/data_status_drilldown_shard_atom_alignment_2026_05_07.md`** — per-service shard atom contract; the
  4-pass order above assumes those atoms match between writer + reconciler + drilldown.
- **`/codex/02-data/availability-manifest-and-data-status.md`** § "Phantom audit — re-runnable recipe" + § "Per-Service
  Shard Dimension Matrix" — canonical recipe + dimension table the rescan scripts implement against.
- **`plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md`** Phase 2.6 — bucket-rename window unblocking the
  `PRE_CUTOVER` todo at line ~222 (switch reconcilers to `resolve_bucket_name`).
- **CLAUDE.md** "Shard-granularity SSOT (CRITICAL)" + "Live = batch (CRITICAL)" — workspace contracts these passes
  preserve.

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
> `Phantom audit` recipe in `/codex/02-data/availability-manifest-and-data-status.md`.

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

Run 2 (07:47 UTC), deployment-service@2ca80d5. All 5 VMs completed ~09:00 UTC. VM names:
`manifest-recon-{defi,cefi,tradfi,sports,prediction}-20260513-074{716,736}`.

### Script 1 — Phantom captures (manifest `captured`, parquet missing)

| asset_group | Captured rows scanned | Real captures | **Phantom captures** | Top phantom data_types                                                                       |
| ----------- | --------------------: | ------------: | -------------------: | -------------------------------------------------------------------------------------------- |
| defi        |               312,900 |       311,602 |            **1,298** | rewards (1,298)                                                                              |
| cefi        |             1,292,929 |     1,290,706 |            **2,223** | options_chain 435, futures_chain 401, trades 381, derivative_ticker 367, book_snapshot_5 363 |
| tradfi      |                96,101 |        92,125 |            **3,976** | trades 1,017, tbbo 1,017, ohlcv_1m 904                                                       |
| sports      |               686,086 |       586,466 |           **99,620** | TRANSFERMARKT_LEAGUES 75,960, SFI_LEAGUES 12,777, INJURIES 9,843                             |
| prediction  |                14,474 |        14,424 |               **50** | trades 50                                                                                    |
| **TOTAL**   |         **2,402,490** | **2,295,323** |          **107,167** |                                                                                              |

> **Notable**: sports 99,620 phantoms (TRANSFERMARKT_LEAGUES dominant at 75,960) vs 354 in 2026-05-04 audit — scope
> difference (all manifest rows vs partial prior audit) or accumulated debt. cefi has 1,453 phantoms with blank venue
> (likely schema_v4 vestigial rows not fully filtered) + 136 at DERIBIT + 111 at UNKNOWN. tradfi trades+tbbo = 2,034 of
> 3,976 (Databento paired-schema artifact; axis 7 eliminates false positives here but real phantoms remain).

### Script 2 — `empty_confirmed` with NULL `error_reason`

| asset_group | Total manifest rows | Null-reason rows | Distribution                                      |
| ----------- | ------------------: | ---------------: | ------------------------------------------------- |
| defi        |           1,606,190 |                0 | —                                                 |
| cefi        |           2,632,931 |        **3,146** | all `SOURCE_RETURNED_ZERO` — ready for apply-flip |
| tradfi      |             141,401 |                0 | —                                                 |
| sports      |           2,675,696 |                0 | —                                                 |
| prediction  |              16,812 |                0 | —                                                 |

### Script 3 — Legacy-blank upgradeable to typed `EXPECTED_*` reason

> **✅ RESOLVED 2026-05-14 (slot-8-ikenna)** — `fixture_manifest` TypeError fixed by tarball refresh (UTL +
> instruments-service + UAC with `refdata_cadence.py` from LDR merge). Re-run locally (DEPLOYMENT_ENV=prod): 0 upgrades
> for all groups — existing default reasons are the most specific classification possible. Apply-flips would produce 0
> changes; HOLD per Ikenna direction remains. Issue doc:
> `plans/active/issues/classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md` (CLOSED).

| asset_group | Candidates (% of manifest) | Upgrades | Notes                                                                                   |
| ----------- | -------------------------: | -------: | --------------------------------------------------------------------------------------- |
| defi        |                          0 |        0 | no legacy-blank candidates (run 2026-05-14)                                             |
| cefi        |                          0 |        0 | clean — no legacy-blank candidates                                                      |
| tradfi      |                          0 |        0 | clean — no legacy-blank candidates                                                      |
| sports      |         1,829,839 (69.66%) |        0 | classifier ran clean (no TypeError); 0 upgrades = default reasons already most specific |
| prediction  |                 41 (0.24%) |        0 | classifier ran clean (no TypeError); 0 upgrades = default reasons already most specific |

### Gate 3 → Gate 4 gate status

| Gate                      | Condition                                                              | Status                                                                                    |
| ------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Gate 1                    | Slot 2 `expected_unattempted_propagation_chain` Phase 3+4+2.A complete | ✅ FIRED 07:30 UTC (\_agent_pings.md)                                                     |
| Script 3 classifier       | `classify_blank_reason_row()` `fixture_manifest` kwarg fix             | ✅ RESOLVED 2026-05-14 (tarball refresh + UAC merge)                                      |
| cefi Script 2 apply       | 3,146 null-reason → `SOURCE_RETURNED_ZERO` stamp                       | ✅ COMPLETE (08:39 UTC)                                                                   |
| defi/tradfi phantom apply | Scripts 1+2 `--unphantom`/`--apply-flips`                              | ✅ COMPLETE (08:34 UTC)                                                                   |
| cefi phantom apply        | Script 1 `--unphantom` (2,223 flips)                                   | ✅ COMPLETE (08:39 UTC)                                                                   |
| Script 3 apply-flips      | defi/sports/prediction legacy-blank upgrades                           | ✅ N/A — 0 upgrades; all default reasons already most specific; HOLD per Ikenna direction |

## Phantom audit Gate 4 results — 2026-05-13 apply-flips (cefi/defi/tradfi COMPLETE)

Run 2, deployment-service@574c168 (--unphantom fix). VMs: `manifest-recon-apply-{cefi,defi,tradfi}-20260513-082713`. All
3 VMs self-deleted on completion (`VM_SHUTDOWN_ON_COMPLETION=true`).

### Script 1 — phantom rows flipped to `attempted_failed`

| asset_group | Manifest rows uploaded | Phantoms flipped | Script 2 stamped | Notes                                                                       |
| ----------- | ---------------------: | ---------------: | ---------------: | --------------------------------------------------------------------------- |
| defi        |              1,606,190 |        **1,298** |                0 | All `rewards` — complete ~08:34 UTC                                         |
| cefi        |              2,632,931 |        **2,223** |        **3,146** | Scripts 1+2 both ran — complete ~08:39 UTC                                  |
| tradfi      |                141,401 |        **3,976** |                0 | Trades+tbbo+ohlcv_1m — complete ~08:34 UTC                                  |
| sports      |                      — |                — |                — | Deferred (out of slot scope; 99,620 phantoms need separate authorized slot) |
| prediction  |                      — |                — |                — | Deferred (out of slot scope; 50 phantoms)                                   |
| **TOTAL**   |                        |        **7,497** |        **3,146** | cefi/defi/tradfi only                                                       |

> cefi Script 2 `SOURCE_RETURNED_ZERO` reason distribution: all 3,146 stamped rows → `SOURCE_RETURNED_ZERO`. Per-VM
> shard at
> `gs://market-data-tick-cefi-central-element-323112/_index/per_vm/manifest-recon-apply-cefi-20260513-082713.parquet`;
> consolidator merges within ~5 min.

## Deferred work after 2026-05-13 slot-6 session

| Phase / item                                                     | Status as of 2026-05-13                                                                                                     | Successor / blocker                                                                                               |
| ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Script 1+2 apply-flips cefi/defi/tradfi                          | ✅ COMPLETE (all 3 VMs done, 7,497 phantoms flipped, 3,146 stamps)                                                          | —                                                                                                                 |
| Script 3 apply-flips (defi/sports/prediction)                    | ✅ CLOSED — 0 upgrades (TypeError resolved 2026-05-14; apply-flips would produce 0 changes; HOLD per Ikenna direction moot) | Issue `classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md` CLOSED                                         |
| Sports/prediction apply-flips Scripts 1+2                        | ⏸ DEFERRED — not in slot 6 scope                                                                                            | Needs separate authorized slot; sports has 99,620 phantoms, prediction 50                                         |
| `--data-types` pass-ordering for apply-flips                     | ⏸ DEFERRED — `launch-manifest-recon-apply-vm.sh` does not implement pass 1→2 ordering                                       | Todo in plan: `[SCRIPT] P0. Add execution order enforcement to rescan launcher`. Needs launcher (not yet shipped) |
| Cross-asset rescan launcher (`launch-cross-asset-rescan-vm.sh`)  | ⏸ DEFERRED — spec written in plan; script not yet shipped                                                                   | Blocker: reconciliation pass ordering must be settled first                                                       |
| `resolve_bucket_name` migration for 3 reconciler scripts         | ⏸ DEFERRED — blocked on physical bucket rename (bucket_name_ssot Phase 2.6)                                                 | `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 2.6 must land first                                       |
| Codex SSOT updates (phantom audit doc + cross-asset-rescan stub) | ⏸ DEFERRED — no new patterns established this session; existing plan stub stands                                            | Ship with cross-asset-rescan launcher                                                                             |

## Open questions

- Q1 — operator-approval edge cases for class C triage: bundle all class-C rows into one weekly review, or
  per-rescan-run signoff? Default: per-run signoff in this plan body's `## Rescan triage decisions` section.
- Q2 — runtime cost estimate per asset_group: depends on bucket sizes from gcs_migration Phase 0 audit. Defer to that
  audit run.
- Q3 — coordination with in-flight gcs_migration Phase 3 VM execution: the rescan must run AFTER gcs_migration Phase 3
  - Phase 6 phantom cleanup, not before. Otherwise we'd rescan pre-migration paths and produce false triage cases.

## Cross-plan coordination

- `gcs_migration_bundle_pipeline_mode_2026_05_08` — STRICT BLOCKER: rescan runs AFTER Phase 3 + Phase 6 of that plan.
- `manifest_migration_SUPERSEDED_2026_05_21` — parent. Stage 4 includes this rescan.
- `writegate_honest_coverage_endtoend_2026_05_06` Phase 4 (typed-error rendering) — consumes `error_reason` populated by
  class A flips during the rescan.
- `manifest_schema_final_gate_2026_05_09` (consolidated v8 SSOT — supersedes archived
  `manifest_v7_schema_migration_design_2026_05_08`) — rescan must respect new v8 immutable columns
  (`service_emission_state`). Note: v8 plan's Phase 3 bundles cross-asset rescan class-A auto-fixes into the same
  parquet walk; this design doc is the SSOT for the rescan semantics.

## Deferred work — migrated to successor plans

| Item                                                            | Successor plan                                                                                  |
| --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Cross-asset rescan launcher (`launch-cross-asset-rescan-vm.sh`) | ✅ SHIPPED in `manifest_schema_final_gate_2026_05_09.md` Phase 3.A (deployment-service@c8a1cd4) |
| `cross_asset_rescan.py` script + 5-axis drift fix               | ✅ SHIPPED in `manifest_schema_final_gate_2026_05_09.md` Phase 3.D                              |
| Sports/prediction apply-flips (99,620 sports phantoms)          | `sports_master.md` § "Phantom recon + failure triage"                                           |
| `resolve_bucket_name` migration for 3 reconciler scripts        | `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 2.6                                     |
| Operator sign-off (class-C triage + sign-off section)           | `manifest_schema_final_gate_2026_05_09.md` Phase 8.A + 8.B                                      |
| Codex SSOT updates (phantom audit doc + rescan stub)            | `manifest_schema_final_gate_2026_05_09.md` Phase codex items                                    |

## Closure note (2026-05-19 slot 4)

Design plan complete. All AI-executable checkboxes are `[x]`. Cross-asset rescan launcher + script shipped in
`manifest_schema_final_gate_2026_05_09.md`. Remaining deferred items tracked in successor plans above. Operator sign-off
(Phase 8.A+8.B) is a HUMAN-only gate in manifest_schema_final_gate. Status: active → done.
