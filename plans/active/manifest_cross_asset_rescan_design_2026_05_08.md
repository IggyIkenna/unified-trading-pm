---
name: manifest-cross-asset-rescan-design-2026-05-08
type: plan
plan_type: design
asset_group: cross-cutting
owner: ikenna
status: draft
priority: P1
created: 2026-05-08
last_updated: 2026-05-08
parent: manifest_migration_master_2026_05_07
related_plans:
  - manifest_migration_master_2026_05_07
  - gcs_migration_bundle_pipeline_mode_2026_05_08
  - writegate_honest_coverage_endtoend_2026_05_06
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

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

| Field            | Reason it's mutable                                                                       |
| ---------------- | ----------------------------------------------------------------------------------------- |
| `capture_status` | Disk parquet existence vs manifest row state — reconcile to disk reality.                 |
| `error_reason`   | Backfilled when reconciler classifies via UAC `EMPTY_CONFIRMED_REASONS` / typed-error.    |
| `attempted_at`   | Stamped at rescan time when missing on legacy rows.                                       |
| `path` column    | Path-template drift between manifest's stamped path and disk's canonical path.            |

### B — Immutable (rescan must respect, NOT flip)

| Field                    | Reason it's immutable                                                              |
| ------------------------ | ---------------------------------------------------------------------------------- |
| `pipeline_mode`          | Write-time fact set by writer per UAC `PipelineMode` SSOT. Rescan can't infer.     |
| `available_at` (per-row) | Per-row column on parquet; respects `LookaheadBiasError` invariants.               |
| `service_emission_state` | Set by emission-policy hook at write-and-publish boundary, not by rescan walk.     |

### C — Triage (rescan flags disagreement, operator decides)

| Field         | Reason it goes to triage                                                                                                |
| ------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `asset_group` | Hive-vocab disagreement (`category=` vs `asset_group=` in path) — auto-fix per drift axis 1, not triage.                |
| `venue` / `data_type` / `instrument_type` / `instrument_id` | Row-key column drift between manifest and disk path — operator decides which is authoritative. |
| `chain`                                                     | DeFi-specific row_key axis; mismatch between manifest and disk is structural.                  |

Triage rows go to `gs://{pid}-rescan-triage/{run_id}/triage.jsonl` with shape:
`{manifest_row_key, disk_path, disagreement_class, rescan_recommendation}`. Operator reviews + signs off in the
rescan plan body via a follow-up `## Rescan triage decisions` section.

## Per-asset-group rules

Rescan applies per-asset-group rules per CLAUDE.md "Per-asset-group shard-key matrix":

- **cefi**: per-instrument shard atom — rescan checks each instrument's parquet; auto-fixes instrument_type casing
  drift (PERPETUAL → perpetual per drift axis 2).
- **cefi options/futures**: per-root bundle — rescan checks chain-bundle equivalence (option ↔ options_chain per drift
  axis 5) — auto-fix.
- **tradfi**: rescan respects `venue_trading_calendar` pre-skips; non-trading days stay `empty_confirmed` with
  `error_reason=EXPECTED_HOLIDAY` / `EXPECTED_WEEKEND`.
- **defi**: per-chain shard atom — rescan respects `PROTOCOL_LAUNCH_DATES` + chain-genesis dates; pre-launch days stay
  `empty_confirmed` with `error_reason=EXPECTED_PRE_GENESIS_CHAIN` / `EXPECTED_PRE_VENUE_LAUNCH`.
- **sports**: per-fixture shard — rescan respects `SOURCE_COVERAGE_START` + `KNOWN_COVERAGE_GAPS`; pre-cutoff days stay
  `empty_confirmed` with `error_reason=EXPECTED_PRE_SOURCE_COVERAGE_START` / `EXPECTED_PAUSED_LEAGUE`.
- **prediction**: per-canonical_question_group — rescan respects market lifecycle (`market_created_at` / `settlement_time`).

## Concurrency safety

Rescan VM uses `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=cross-asset-rescan-{RUN_TS}` per CLAUDE.md "Per-VM shard
isolation for concurrent backfills". Per-VM shard at `_index/per_vm/cross-asset-rescan-{RUN_TS}.parquet`; manifest
consolidator merges into canonical via last-writer-wins on identical row_key. No race with other in-flight VMs that
follow the same protocol.

## Phantom audit integration

The rescan IS a superset of the existing phantom audit
(`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`). Pre-rescan baseline: 354 residual phantom rows
from 2026-05-04 audit. Post-rescan target: **0 phantoms across all 5 asset_groups**. The 5 drift axes (hive-vocab,
path-prefix, instrument_type casing, schema-4 empty instrument_type, chain-bundle equivalence) auto-fix via class A
above; any residual goes to class C triage.

## Cross-plan coordination (banner)

Per CLAUDE.md "Cross-Plan Coordination Banners":

- During the rescan window, banner the following plans with
  `🟡 IN-FLIGHT REFACTOR — cross-asset rescan running 2026-05-XX → 2026-05-YY`:
  - `gcs_migration_bundle_pipeline_mode_2026_05_08`
  - `manifest_migration_master_2026_05_07`
  - `writegate_honest_coverage_endtoend_2026_05_06`
- Other agents pause new VM launches in the affected asset_groups until the banner is removed.

## Launcher script (queued; not shipped this session)

The rescan VM launcher (`deployment-service/scripts/vm/launch-cross-asset-rescan-vm.sh`) is required per CLAUDE.md
"VM launcher script SSOT". Spec for the launcher (for the follow-up sub-agent):

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

## Open questions

- Q1 — operator-approval edge cases for class C triage: bundle all class-C rows into one weekly review, or per-rescan-run
  signoff? Default: per-run signoff in this plan body's `## Rescan triage decisions` section.
- Q2 — runtime cost estimate per asset_group: depends on bucket sizes from gcs_migration Phase 0 audit. Defer to that
  audit run.
- Q3 — coordination with in-flight gcs_migration Phase 3 VM execution: the rescan must run AFTER gcs_migration Phase 3
  + Phase 6 phantom cleanup, not before. Otherwise we'd rescan pre-migration paths and produce false triage cases.

## Cross-plan coordination

- `gcs_migration_bundle_pipeline_mode_2026_05_08` — STRICT BLOCKER: rescan runs AFTER Phase 3 + Phase 6 of that plan.
- `manifest_migration_master_2026_05_07` — parent. Stage 4 includes this rescan.
- `writegate_honest_coverage_endtoend_2026_05_06` Phase 4 (typed-error rendering) — consumes `error_reason` populated
  by class A flips during the rescan.
- `manifest_v7_schema_migration_design_2026_05_08` (sibling Tab 3 design) — rescan must respect new v8 immutable
  columns (`service_emission_state`).
