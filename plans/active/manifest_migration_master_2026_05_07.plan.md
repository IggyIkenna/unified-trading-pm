---
name: manifest-migration-master
slug: manifest_migration_master_2026_05_07
date: 2026-05-07
owner: claude-code
status: active
priority: P0
phase: pending_approval
domain: cross-cutting
type: coordination
locked_by: live-defi-rollout
locked_since: 2026-05-07
references:
  - sports_master_2026_05_07
  - predictions_master_2026_05_07
  - defi_master_2026_05_07
  - infrastructure_master_2026_05_07
  - writegate_honest_coverage_endtoend_2026_05_06
  - master_to_live_defi_2026_05_23
related_plans:
  - master_to_live_defi_2026_05_23
  - writegate_honest_coverage_endtoend_2026_05_06
---

# Manifest Migration Master — cross-plan dependency sequencer

## Why this exists

Manifest re-build / schema-migration work is scattered across **5 active plans + 1 master plan** because each piece
naturally lives next to its asset_group / write-side / infrastructure scope. But these pieces have **hard sequencing
dependencies** — running them out-of-order produces silent data corruption (writegate Phase 2.C strict-mode flip
hard-fails sports `record_captured` if sports rename Phase 2 hasn't run; Phase 3 reconcilers can't flip 1440-NaN until
the placeholder methods are deleted; per-base_asset → canonical_question_group rewrite must happen before post-Phase-3
manifest rescan).

This plan does **not own any todos** — every piece of work lives in its parent plan. This plan owns:

1. **Sequencing diagram** — the cross-plan dependency chain in one place.
2. **Operator gate tracker** — which phases need operator action (GCE migration / VM pause-resume) and when.
3. **Status rollup** — current state of each piece, refreshed as parents flip checkboxes.
4. **Risk register** — what breaks if we run pieces out-of-order.

If you're an executing agent: **work in the parent plan**, not here. This plan exists so the operator + future agents
can see the manifest-migration shape at a glance.

## Sequencing DAG

```
                                                                                                        ┌───────────────────────┐
                                                                                                        │  v6 → v7 schema bump  │
                                                                                                        │  (additive: job_id)   │
                                                                                                        │  UTL @ed658e9b SHIPPED│
                                                                                                        └───────────────────────┘
Stage 1 (sports rename — operator-gated)              Stage 2 (writegate 2.A/2.B/2.C — code)              Stage 3 (reconcilers + parquet migrations)
─────────────────────────────────────────             ──────────────────────────────────                  ────────────────────────────────────────
[A1 Phase 1] migrate_sports_*.py                      [Phase 2.A] delete                                  [Phase 3.A] 1440-NaN flip
  SHIPPED instruments-service@8050477                   _create_empty_output                                + partial-bundle reflip
                                                        + _create_full_day_empty_output                     (`record_captured` → `record_failed`)
       ↓                                                + _create_closed_market_candle                            ↓
                                                        + v3-shape _write_manifest_records                  [Phase 3.B] one-time GCS
[A1 Phase 2] OPERATOR runs GCE migration                  ↓                                                  available_at per-row backfill
  - pause sports FWD/BACKFILL VMs                      [Phase 2.B] PartitionedTickWriter                          ↓
  - launch in asia-northeast1-c                          partition-validation guard (LIVE)                  [Phase 3.C] pre-v6 manifest cleanup
  - --dry-run first, spot-check 20 parquets               ↓                                                       ↓
       ↓                                               [Phase 2.C] LookaheadBiasError strict          [Predictions Phase 3] Polymarket
                                                         flip — REQUIRES sports rename done            per-base_asset → canonical_question_group
[A1 Phase 3] AGENT atomic 4-repo source rename                                                          GCS rewrite + manifest reflip
  - UAC → UTL → instruments-service → features-sports                                                            ↓
       ↓                                                                                                ┌──────────────────────────────────────┐
                                                                                                        │ [defi_master mtds-s4-10] FINAL       │
[A1 Phase 4] verify writegate Phase 2.C unblocked       (Phase 2 unblocks Phase 3)                      │ rescan ALL availability indexes      │
                                                                                                        │ (sweeps every per-service manifest)  │
                                                                                                        └──────────────────────────────────────┘
                                                                                                                          ↓
                                                                                                        [infrastructure_master raw-tables]
                                                                                                          14 entries in TABLE_TO_EXPORT —
                                                                                                          per-table canonical shape decision +
                                                                                                          _ensure_timestamp shim DELETE
```

Stage 1 unblocks Stage 2.C. Stage 2 (especially 2.A + 2.B) precedes Stage 3 reconcilers. Stage 3.A→3.B→3.C + Predictions
Phase 3 happen in parallel within Stage 3 (no inter-dependency among them). After Stage 3 completes, the final
`mtds-s4-10-rescan-all-manifests` sweep + raw-tables migration close out.

## Per-stage status rollup (refresh as parents flip)

### Stage 1 — Sports `data_available_at` → `available_at`

**Owner plan**: `sports_master_2026_05_07` (Sports `data_available_at` → `available_at` rename section). **Folded plan
in archive**: `plans/archive/sports_data_available_at_rename_2026_05_07.plan.md`.

| Phase | Item                                                                                                                              | Status                                               | Owner    |
| ----- | --------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | -------- |
| 1     | `instruments-service/scripts/migrate_sports_available_at_column.py` (idempotent 4-case GCS rename + 11 unit tests + per-blob CAS) | **SHIPPED 2026-05-07** `instruments-service@8050477` | agent    |
| 2     | Pause sports FWD VMs (`af-fwd-*`, `fs-fwd-*`, `tm-fwd-*`, `sfi-fwd-*`, `us-fwd-*`, `openmeteo-fwd-*`)                             | PENDING                                              | operator |
| 2     | Pause sports BACKFILL VMs (`af-backfill-*`, `fs-backfill-*`, etc.)                                                                | PENDING                                              | operator |
| 2     | Launch migration VM `sports-migrate-available-at-{ts}` in `asia-northeast1-c` (add prefix to `vm_zombie_watchdog.py` first)       | PENDING                                              | operator |
| 2     | `--dry-run` first; review; then full run                                                                                          | PENDING                                              | operator |
| 2     | Spot-check 20 parquets across 2018-2026 — `pq.read_schema(uri).names` includes `available_at`, not `data_available_at`            | PENDING                                              | operator |
| 3     | Atomic 4-repo source rename: UAC → UTL → instruments-service → features-sports (each repo's QG passes before next push)           | PENDING                                              | agent    |
| 3     | DO NOT touch `unified-trading-library/tests/unit/test_availability_stamping.py` (other-agent dirty)                               | constraint                                           | agent    |
| 3     | `rg -n 'data_available_at' --type py --glob '!.venv*'` returns ZERO non-test, non-archived results                                | PENDING                                              | agent    |
| 4     | Smoke-run sports backfill — `record_captured` no longer raises `LookaheadBiasError`                                               | PENDING                                              | agent    |
| 4     | Resume FWD + BACKFILL VMs                                                                                                         | PENDING                                              | operator |

### Stage 2 — Writegate Phase 2.A + 2.B + 2.C

**Owner plan**: `writegate_honest_coverage_endtoend_2026_05_06`. (Note: this plan was the master-plan-audit umbrella
target; not folded into infrastructure_master because writegate covers write-side correctness, not deployment infra.)

| Phase | Item                                                                                                                                                                                                       | Status                                              |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| 2.A   | Delete `_create_empty_output` from `app/adapters/base_adapter.py` + 37 callsite migration to A/B/C                                                                                                         | partial                                             |
| 2.A   | Delete sibling `_create_full_day_empty_output` (MDPS `tradfi/ohlcv_passthrough.py:266`) + `_create_closed_market_candle` (`orchestration_writer.py:65`) per master-plan-audit A2 ruling 2026-05-07         | added to scope; PENDING                             |
| 2.A   | Delete v3-shape `_write_manifest_records`; consolidate three write-paths (`candle_write_mixin._write_candles` + `data_sink.SyncGCSDataSink.write` + `orchestration_writer._write_candles_to_gcs`) into one | PENDING                                             |
| 2.A   | Fix prediction empty path (`live_workers.py:268-271`) — add `record_empty(row_key)` call (currently silent `success=True, candles_generated=0`)                                                            | PENDING                                             |
| 2.B   | `PartitionedTickWriter` partition-validation guard at MTDS `raw_tick_hive.py`                                                                                                                              | LIVE (MTDS@ae2be64 + 0fc8ba2)                       |
| 2.C   | Sports `_ensure_timestamp` shim deletion + per-source `available_at` stamping migration                                                                                                                    | partial; **GATED on Stage 1 Phase 3 atomic rename** |
| 2.C   | `LookaheadBiasError` strict-mode flip workspace-wide                                                                                                                                                       | PENDING; **GATED on Stage 1 + 2.A + 2.B done**      |

### Stage 3 — Reconcilers + parquet migrations (parallel)

| Stream                               | Owner                                           | Items                                                                                                                                                                                                                                                                                                                                                  | Status  |
| ------------------------------------ | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------- |
| **Writegate Phase 3.A**              | `writegate_honest_coverage_endtoend_2026_05_06` | 1440-NaN flip + partial-bundle reflip (ES.OPT 18-date single-parent fills) — `record_captured` → `record_failed` for malformed bundles                                                                                                                                                                                                                 | scoped  |
| **Writegate Phase 3.B**              | `writegate_honest_coverage_endtoend_2026_05_06` | One-time GCS `available_at` per-row backfill across all asset_groups                                                                                                                                                                                                                                                                                   | scoped  |
| **Writegate Phase 3.C**              | `writegate_honest_coverage_endtoend_2026_05_06` | Pre-v6 manifest cleanup — delete v3-shape rows after Phase 2.A v3-path delete                                                                                                                                                                                                                                                                          | scoped  |
| **Predictions migration**            | `predictions_master_2026_05_07`                 | `mtds_migrate_polymarket_per_base_asset_to_canonical_group.py` parquet rewrite + `mtds_reflip_polymarket_per_base_asset.py` manifest reflip (with `run_lifecycle` + `--max-flips-per-run=10000` halt safety + CSV audit) + old parquet deletion + `migrate_polymarket_canonical.py` confirmation + delete `category=prediction` legacy fallback reader | scoped  |
| **Sports ODDS_API legacy migration** | `sports_master_2026_05_07`                      | 288M legacy `venue=ODDS_API` rows → canonical `(asset_group=sports, source=odds_api, data_type, league_id, day)` re-key + MDPS `SportsBucketAssignmentAdapter` 8-horizon bucketing on migrated rows                                                                                                                                                    | scoped  |
| **Sports fixture truthset recovery** | `sports_master_2026_05_07`                      | Phase 4 drift audit + manifest rescan post-recovery; SFI_STANDINGS 100% phantom triage; api-football + understat UAC `SOURCE_COVERAGE_START` reconcile                                                                                                                                                                                                 | partial |

### Stage 4 — Final sweeps (sequenced after Stage 3)

| Item                                                                                  | Owner                              | Notes                                                                                                                          |
| ------------------------------------------------------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `mtds-s4-10-rescan-all-manifests` — re-scan ALL availability indexes after migrations | `defi_master_2026_05_07`           | P0; sweeps every per-service manifest (CeFi / DeFi / TradFi / Sports / Predictions / instruments / MTDS / MDPS / features-\*). |
| Raw tables migration — 14 entries in `TABLE_TO_EXPORT` per canonical shape            | `infrastructure_master_2026_05_07` | Source-of-truth gap; needs design per table.                                                                                   |
| `_ensure_timestamp` shim DELETE                                                       | `infrastructure_master_2026_05_07` | Gated on raw-tables migration.                                                                                                 |
| Conditional `feature_group` column backfill                                           | `infrastructure_master_2026_05_07` | Only if per-service writer never populated; check via Phase 1A audit.                                                          |

### Already-shipped (historical schema migrations)

These are **DONE** but recorded here as the migration trail for future reference:

- **v3 → v4**: legacy → first availability_index format with venue/data_type axis. Pre-2026-04.
- **v4 → v5**: honest-coverage — added `capture_status` (`captured` / `empty_confirmed` / `attempted_failed`) +
  `error_reason` + `attempted_at` columns. Per CLAUDE.md "Availability manifest v5".
- **v5 → v6**: `quote_margin_combo` for spreads + per-asset-group axis additions. Plan
  `manifest_schema_v6_quote_margin_combo_2026_04_23` (archived).
- **v6 → v7**: additive `job_id` axis for ML / strategy / execution shards. UTL `MANIFEST_SCHEMA_VERSION 6→7` SHIPPED
  via `UTL@ed658e9b` 2026-05-06. Reader supports `_V7_COLUMNS` superset; old readers tolerate v7-extra columns.

## Operator action gates (sequenced)

This is the operator-visible view — what the human needs to do, when, in what order.

| #   | Action                                                                                                                                            | Triggered by           | Approx duration                        | VM zone                                                                                                       |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| 1   | Pause sports FWD + BACKFILL VMs                                                                                                                   | Stage 1 Phase 1 done   | 5 min                                  | `asia-northeast1-c`                                                                                           |
| 2   | Launch `sports-migrate-available-at-{ts}` VM with `--dry-run`                                                                                     | After (1)              | 10-20 min wall-clock                   | `asia-northeast1-c` (same-region per CLAUDE.md "always run on a same-region GCE VM"; cross-region 18× slower) |
| 3   | Review dry-run output, spot-check 20 parquets                                                                                                     | After (2)              | 30 min                                 | local                                                                                                         |
| 4   | Re-launch migration VM for full run                                                                                                               | After (3)              | ~5-6h on 1 worker / ~1-2h multi-worker | `asia-northeast1-c`                                                                                           |
| 5   | DO NOT resume sports VMs yet (Stage 1 Phase 3 must ship first)                                                                                    | After (4)              | wait                                   | n/a                                                                                                           |
| 6   | After agent ships Stage 1 Phase 3 atomic rename, resume sports VMs                                                                                | After Phase 3 done     | 5 min                                  | n/a                                                                                                           |
| 7   | After agent verifies Stage 1 Phase 4, agent proceeds to Stage 2.C strict-mode flip                                                                | After Phase 4 verified | n/a                                    | agent-only                                                                                                    |
| 8   | Stage 3 parquet migrations (predictions + ODDS_API) — operator approves first 10k flips per `--max-flips-per-run=10000` halt safety per migration | per script             | 1-2h supervised, then unattended       | n/a                                                                                                           |
| 9   | Final `mtds-s4-10-rescan-all-manifests` sweep                                                                                                     | After Stage 3 done     | 4-8h cross-asset_group                 | mix                                                                                                           |

## Risk register

| Risk                                                                                                                                     | Likelihood                        | Impact                                                                                             | Mitigation                                                                                                                                                                   |
| ---------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Stage 1 Phase 2 runs while FWD/BACKFILL VMs still write → mixed-state parquets (some with `available_at`, some with `data_available_at`) | High if operator skips pause step | Migration script is idempotent + per-blob CAS, so re-runs are safe; but mid-run new writes diverge | Operator pause step is explicit Phase 2 prerequisite                                                                                                                         |
| Stage 1 Phase 3 atomic rename ships out-of-order (e.g. UTL pushes before UAC)                                                            | Medium                            | Brief reader/writer schema mismatch                                                                | Sequence is UAC → UTL → instruments-service → features-sports; each repo's QG passes before next push                                                                        |
| Stage 2.C strict-mode flip ships before Stage 1 Phase 3 done                                                                             | Medium-high                       | Sports `record_captured` hard-fails workspace-wide (LookaheadBiasError on every sports write)      | This plan's gating diagram is the SSOT for the dependency; agents read this before flipping 2.C                                                                              |
| Stage 3 reconcilers run while writegate Phase 2.A `_create_*_empty_output` deletions still in flight                                     | Medium                            | Reconciler may flip rows that 2.A would have deleted via record-failure                            | Phase 2.A precedes Stage 3.A in the DAG; writegate plan tracks the order                                                                                                     |
| Predictions Polymarket parquet rewrite deletes old parquets before new ones are verified                                                 | Low                               | Data loss                                                                                          | Plan requires (a) hand-inspection of 10 random groups × random days, (b) downstream features compute clean, (c) operator approval before old-parquet deletion                |
| Final `mtds-s4-10` sweep runs while any agent is mid-flight on a per-asset_group migration                                               | Low                               | Sweep returns inconsistent state                                                                   | Coordinate via deployment-ui data-status panel + this plan's status rollup                                                                                                   |
| Per-VM shard isolation forgotten on multi-worker migration                                                                               | Medium                            | Concurrent CAS race + manifest clobber per CLAUDE.md `§ Per-VM shard isolation`                    | Migration scripts MUST set `VM_NAME=<unique>` + `MANIFEST_PER_VM_SHARDS=true` per worker; UTL runtime guard in ManifestWriter raises `MultiWorkerWithoutShardIsolationError` |

## Cross-references

- Master plan: [`master_to_live_defi_2026_05_23.plan.md`](./master_to_live_defi_2026_05_23.plan.md).
- Write-gate (Stage 2 + 3):
  [`writegate_honest_coverage_endtoend_2026_05_06.plan.md`](./writegate_honest_coverage_endtoend_2026_05_06.plan.md).
- Sports rename (Stage 1): [`sports_master_2026_05_07.plan.md`](./sports_master_2026_05_07.plan.md) § Sports
  `data_available_at` → `available_at` rename.
- Predictions Phase 3 migration: [`predictions_master_2026_05_07.plan.md`](./predictions_master_2026_05_07.plan.md).
- Final rescan: [`defi_master_2026_05_07.plan.md`](./defi_master_2026_05_07.plan.md) § mtds-s4-10.
- Raw tables + `_ensure_timestamp` deletion:
  [`infrastructure_master_2026_05_07.plan.md`](./infrastructure_master_2026_05_07.plan.md).
- Workspace rule: CLAUDE.md `§ Manifest migration, NOT fallback` — when manifest drifts from canonical shape, write a
  one-time migration script and **remove** the fallback reader. No compat shims.
- Workspace rule: CLAUDE.md `§ Per-VM shard isolation for concurrent backfills`.
- Workspace rule: CLAUDE.md `§ VIX 15m source layering` — Barchart preload + Yahoo rolling + honest gap; example of how
  layered sources interact with manifest writes.
- Codex SSOT (write side): `codex/02-data/availability-manifest-and-data-status.md`.
- Codex SSOT (read side): `codex/02-data/honest-absence-downstream-handling.md` (shipped 2026-05-06).

## Conflicts + sequencing constraints (added 2026-05-07)

### File-overlap conflicts (same file edited in two stages)

1. **UTL `unified_trading_library/instruments_write_gate.py`** — Stage 1 Phase 3 renames `DEFAULT_AS_OF_COLUMNS` tuple
   `data_available_at` → `available_at`; Stage 2.C deletes `_ensure_timestamp` shim. Resolution: Stage 1 ships first per
   DAG; Stage 2.C agent rebases on top and confirms no merge conflict.
2. **features-sports `cli/handlers/batch_handler.py`** — Stage 1 Phase 3 reader-side rename + Stage 2.C
   `_ensure_timestamp` shim deletion + per-source `stamp_available_at_*` migration BOTH touch this file. **Resolution:
   DEFER Stage 1 Phase 3's features-sports rename and ship it in the SAME commit as Stage 2.C's batch_handler refactor**
   — avoids two-commit churn on the same lines. Sports rename plan + sports_master already flag this; cross-referenced
   here for visibility.
3. **Sports ODDS_API rows location** — **OPEN QUESTION**: where exactly do legacy `venue=ODDS_API` 288M rows live?
   - If under `gs://instruments-store-sports-{pid}/sports_reference/by_date/.../entity=odds/`: Stage 1 Phase 2 GCS
     migration picks them up via column-rename automatically (no separate Stage 3 work).
   - If under `gs://market-tick-data-sports-{pid}/...` or another bucket: Stage 1 misses them; Stage 3 sports ODDS_API
     re-key handles them as an independent migration.
   - **Action**: next agent must grep existing migration scripts (`instruments-service/scripts/`,
     `market-tick-data-service/scripts/`) + check operator's earlier ODDS_API migration commits to confirm path layout
     BEFORE starting Stage 3 Sports ODDS_API migration.
4. **Stage 1 Phase 2 sports parquet rewrite** vs **Stage 3.B GCS `available_at` per-row backfill** — **redundancy +
   value-drift risk**: Phase 2 preserves cell values (column-rename only); Stage 3.B may re-derive `available_at`
   per-row using stamping rules. **Resolution**: Stage 3.B script MUST `pq.read_schema(uri).names` check first; if
   `available_at` is present + non-null, skip. Saves duplicate GCS write cost AND preserves Phase 2's
   preserved-cell-value invariant.

### Sequencing dependencies (already in DAG, pinned explicitly here)

5. **Stage 3.A** (1440-NaN flip + partial-bundle reflip) MUST run AFTER Stage 2.A placeholder-method deletions + v3-path
   deletion completes — otherwise reconciler must handle multiple writer-output shapes simultaneously (extra
   complexity + race surface).
6. **Stage 4 `mtds-s4-10` rescan** MUST run AFTER all Stage 3 streams complete (not in parallel) — rescan during
   reconciler-in-flight gives inconsistent state across services.
7. **Stage 4 `_ensure_timestamp` shim DELETE** is gated on Stage 4 raw-tables migration completion (per
   `infrastructure_master`) — premature delete breaks readers for tables not yet stamped.
8. **Stage 3.C pre-v6 manifest cleanup** must filter on `schema_version` column to avoid touching v7 rows. Concurrent
   writers writing v7 rows during cleanup must NOT be deleted.

## VM impact matrix (added 2026-05-07)

Per-stage impact on currently-running VMs + required operator action.

| Stage                                                                            | VMs affected                                                                                                                                                | Action required                                                                                                                                                     | Risk if no action                                                                                                                              |
| -------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| **Stage 1 Phase 2** sports GCS column rename                                     | Sports FWD-poll (`af-fwd-*`, `fs-fwd-*`, `tm-fwd-*`, `sfi-fwd-*`, `us-fwd-*`, `openmeteo-fwd-*`) + sports BACKFILL (`af-backfill-*`, `fs-backfill-*`, etc.) | **PAUSE before; RESUME after Phase 4** (post-source-rename). Already P0 operator gate in plan.                                                                      | Mid-run new writes diverge → mixed-schema parquets (`data_available_at` from old tarball coexisting with `available_at` from migrated bucket). |
| **Stage 1 Phase 3** atomic 4-repo source rename                                  | All sports VMs needing the new code (paused state)                                                                                                          | After source rename ships: refresh tarball `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group SPORTS` BEFORE resuming.                       | Resumed VM uses pre-rename tarball → still writes legacy column → undoes Phase 2's migration.                                                  |
| **Stage 2.A** delete placeholders + v3 writer path                               | Currently-running MDPS / TradFi / CeFi / DeFi / sports backfill VMs                                                                                         | **NO active pause** — old VMs drain with old code; new VMs after rebuild use new code. Stage 3.A reconciler cleans legacy 1440-NaN / partial-bundle rows post-fact. | None if drained.                                                                                                                               |
| **Stage 2.B** partition-validation guard                                         | All MDPS VMs                                                                                                                                                | **ALREADY LIVE** (MTDS@ae2be64 + 0fc8ba2). New VMs picked it up at last tarball refresh.                                                                            | n/a                                                                                                                                            |
| **Stage 2.C** `_ensure_timestamp` shim delete + `LookaheadBiasError` strict flip | Sports + features-\* + ML/strategy/execution VMs                                                                                                            | **NO pause needed** if sequenced correctly (Stage 1 + 2.A + 3.B done first). Strict-mode flip catches paths missing `available_at` — fail-loud is the design.       | Premature flip (before Stage 1 done) → sports `record_captured` hard-fails workspace-wide.                                                     |
| **Stage 3.A** 1440-NaN + partial-bundle reflip                                   | Currently-writing MDPS VMs                                                                                                                                  | **NO pause** — reconciler flips manifest rows; per-VM shard isolation + consolidator + `check_shard_freshness(retry_failed=True)` re-attempts flipped rows.         | Race tolerated: flipped row may get re-captured by VM next cycle (correct behaviour).                                                          |
| **Stage 3.B** GCS `available_at` per-row backfill                                | All asset_group writer VMs                                                                                                                                  | **NO pause** — per-blob CAS via `if_generation_match` + skip-if-stamped check (preserves Stage 1 Phase 2 sports values).                                            | Race → CAS rejects, retry loop.                                                                                                                |
| **Stage 3.C** pre-v6 manifest cleanup                                            | Concurrent manifest writers                                                                                                                                 | **NO pause** — cleanup filters on `schema_version` to avoid touching v7 rows.                                                                                       | Cleanup deletes v7 rows if filter wrong → manifest corruption.                                                                                 |
| **Stage 3 Predictions** Polymarket parquet rewrite + reflip                      | `mtds-prediction-*` VMs (per-base_asset writers)                                                                                                            | **PAUSE during rewrite**; resume only after MTDS Polymarket adapter migration ships (so resumed VMs write canonical_question_group shape).                          | Mid-run new ticks land in legacy per-base_asset path.                                                                                          |
| **Stage 3 Sports ODDS_API** 288M row re-key                                      | Sports VMs (already paused for Stage 1)                                                                                                                     | **COMBINE pause window with Stage 1 Phase 2** to amortise downtime.                                                                                                 | Same class as Stage 1.                                                                                                                         |
| **Stage 4 `mtds-s4-10`** workspace-wide manifest rescan                          | All asset_group VMs writing manifest                                                                                                                        | **NO pause** — rescan reads availability indexes; consolidator handles concurrent writes per CLAUDE.md `§ Manifest concurrency principle`.                          | Concurrent flips during rescan → next rescan picks them up; eventual-consistent.                                                               |
| **Stage 4 raw-tables migration** (14 entries)                                    | Sports forward-poll VMs (raw tables are sports reference)                                                                                                   | **PAUSE per-table** during rewrite (mini-window per table, NOT workspace-wide).                                                                                     | Sports FWD writes to raw table during rewrite → race.                                                                                          |
| **Stage 4 `_ensure_timestamp` shim DELETE**                                      | All readers of raw tables                                                                                                                                   | **NO pause** — gated on raw-tables migration completion; readers tolerate deletion because every raw table now stamps `available_at` per-row.                       | Premature delete → reader breakage.                                                                                                            |

**Currently-running VM families to coordinate (per session memory 2026-05-07):**

- Sports FWD-poll + multiple sports BACKFILL (paused during Stage 1 + Stage 3 sports ODDS_API).
- `mtds-prediction-*` (paused during Stage 3 Predictions).
- ~82 cefi-\* venue backfill VMs — NOT directly affected by Stage 1 (sports-specific). Stage 3.B touches CeFi parquets
  but skip-if-stamped + per-blob CAS handles concurrency.
- TradFi MTDS backfill fleet (`mtds-*` prefixes) — same as CeFi.
- `features-onchain-defi-backfill-*` — Stage 3.B may touch DeFi parquets — same skip-if-stamped logic.
- Manifest consolidator (singleton) — runs throughout. Reconcilers + migrations write to per-VM shards which
  consolidator merges.
- VM zombie watchdog — singleton, unaffected.

**Net summary** — pause windows:

- **Window 1**: Stage 1 Phase 2 + Stage 3 Sports ODDS_API (sports VMs only; combined into one window).
- **Window 2**: Stage 3 Predictions Polymarket migration (prediction VMs only).
- **Window 3** (mini-windows): Stage 4 raw-tables migration (per-table; sports VMs only).

CeFi / DeFi / TradFi MTDS backfill fleet keeps running through nearly all migrations.

## VM operational guidance during the migration window

The migration spans days-to-weeks across multiple stages. While stages execute (and between stages), VMs continue
running. This section codifies what to do with VMs in the meantime so we don't accidentally regress the migration or
build up new bad-shape data.

### Pre-migration period (today 2026-05-07 → Stage 1 Phase 2 launch)

- **Sports FWD-poll + BACKFILL VMs**: keep running normally with current code. They write `data_available_at` (legacy) —
  fine because nothing's migrated yet. Final pre-migration data drift is acceptable; Stage 1 Phase 2 picks it up.
- **CeFi / DeFi / TradFi / Predictions VMs**: keep running. They're not affected by Stage 1.
- **MDPS / TradFi VMs writing 1440-NaN placeholders**: keep running. Stage 2.A code-side deletion + Stage 3.A reconciler
  will clean up post-fact. **DO NOT** pre-emptively kill these — drain is fine.
- **New backfill VM launches**: use the **latest tarball**
  (`bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group <X>`) so the launched VM picks up Stage 2.B
  partition-validation guard (already LIVE) + any other shipped writegate fixes. Don't launch a new VM with stale
  tarball if a fresh one is available.
- **Stuck / zombie VMs**: let `vm_zombie_watchdog` handle. Reference: CLAUDE.md `§ VM Naming Convention`. If a new VM
  prefix is being used, **add it to `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` BEFORE launch** (per reference
  incident 2026-05-05 — 5 prefixes silently zombied).
- **Manifest consolidator** (singleton): keep running. It's the merge point for per-VM shards under
  `_index/per_vm/{vm_name}.parquet` → canonical `_index/availability_index.parquet` (last-writer-wins on identical
  row_key per CLAUDE.md `§ Per-VM shard isolation`).
- **Multi-agent coordination**: per CLAUDE.md `§ Two teammates × multiple parallel agents`, Harsh + Ikenna
  - their respective parallel agents may launch VMs unaware of this migration window. Operator should periodically
    `gcloud compute instances list --format='value(name)'` filter by sports / prediction prefixes to verify state before
    triggering Stage 1 / Stage 3 windows.

### During Stage 1 Phase 2 (sports GCS migration ~5-6h on 1 worker / ~1-2h multi-worker)

- **Sports FWD-poll**: PAUSED.
- **Sports BACKFILL**: PAUSED.
- **All other VMs** (CeFi / DeFi / TradFi / Predictions / MTDS / features-\*): keep running. Different buckets.
- **Migration VM** (`sports-migrate-available-at-{ts}`): single VM in `asia-northeast1-c` with per-VM shard isolation if
  multi-worker. Reads via cheap `pyarrow.parquet.read_schema()` first; rewrites via `if_generation_match` CAS.
- **NEW VM launches during this window**: NO sports VMs (they'd race the migration). CeFi / DeFi / TradFi / Predictions
  launches OK.

### Between Stage 1 Phase 2 done and Stage 1 Phase 3 atomic source rename ships

- **Sports VMs**: STAY PAUSED. Do NOT resume yet — VMs would use pre-rename tarball + write `data_available_at`,
  re-introducing legacy column into migrated bucket.
- **CeFi / DeFi / TradFi / Predictions VMs**: keep running.

### During Stage 1 Phase 3 (atomic 4-repo source rename, agent-driven, ~30-60 min)

- **Sports VMs**: STAY PAUSED.
- **Tarball refresh**: after each repo push (UAC / UTL / instruments-service / features-sports), DO NOT trigger a
  tarball rebuild yet — wait until all 4 repos shipped. Tarball rebuilds individually mid-rename create inconsistent
  code-state.
- **After all 4 repos pushed**: refresh sports tarball
  (`bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group SPORTS`).

### Stage 1 Phase 4 (verify + resume)

- Smoke-run sports backfill VM (single VM, fresh tarball) for one date → confirm `record_captured` no longer raises
  `LookaheadBiasError`.
- After smoke green, **RESUME paused sports VMs** with fresh tarball.
- Verify deployment-ui data-status panel for sports — should show `available_at` populated, no legacy
  `data_available_at` column.

### During Stage 2.A code rollout (delete placeholders + v3 writer path)

- **NO active pause needed**. Currently-running MDPS VMs use pre-2.A tarball — they continue writing 1440-NaN
  placeholders + partial bundles + v3-shape manifest rows. Drain naturally.
- **NEW MDPS VM launches**: refresh tarball post-2.A so new VMs use new code (record_empty + record_failed paths).
- **Stage 3.A reconciler** later flips legacy 1440-NaN / partial-bundle / v3-shape rows from `captured` →
  `attempted_failed`. Orchestrator pre-flight uses `check_shard_freshness(retry_failed=True)` (UTL@ba83a6f1) to
  re-attempt flipped rows with new code.

### Between Stage 2.A done and Stage 3 reconcilers run

- **All VMs continue running**. New writes use new code. Old rows still legacy-shape on disk. Reconciler will clean up.
- **Operator check**: monitor manifest consolidator output. If consolidator is ever down for >24h, Stage 3 reconcilers
  may produce stale per-VM shards that don't merge cleanly. Verify `manifest-consolidator-{ts}` prefix VM RUNNING state
  daily.

### During Stage 3 reconcilers + parquet migrations

- **Stage 3.A / 3.B / 3.C reconcilers**: NO VM pause. Per-blob CAS + per-VM shard isolation handle concurrency. Active
  writers may flip rows that the reconciler is reading; consolidator merges last-writer-wins on row_key; next reconciler
  sweep cleans up any remaining legacy rows.
- **Stage 3 Predictions Polymarket migration**: PAUSE `mtds-prediction-*` VMs for the rewrite window. Resume ONLY after
  MTDS Polymarket adapter migration ships (so resumed VMs write `canonical_question_group` shape).
- **Stage 3 Sports ODDS_API 288M row re-key**: combine pause window with Stage 1 Phase 2 / Phase 3 (same sports VMs
  already paused). If ODDS_API path is in `sports_reference/` bucket: the Stage 1 Phase 2 GCS migration already covered
  this (column rename); Stage 3 work is just MDPS adapter writing canonical key onwards. Resolve the OPEN QUESTION about
  path layout BEFORE this stage starts.
- **Other VMs** (CeFi / DeFi / TradFi / MTDS perp-funding / lending-indices / lst-rates): keep running.

### Stage 4 `mtds-s4-10` workspace-wide rescan + raw-tables migration

- **`mtds-s4-10` rescan**: NO VM pause. Rescan reads ALL availability indexes; concurrent writes handled per
  consolidator. Run when all Stage 3 streams complete.
- **Raw-tables migration** (14 entries in `TABLE_TO_EXPORT`): per-table mini-pause window. Pause sports FWD briefly
  (~5-10 min per table), run rewrite, resume. Don't try to migrate all 14 in one window — incremental is safer.
- **`_ensure_timestamp` shim DELETE**: code-only change. Refresh tarballs after delete; new VMs use new code
  immediately. Old VMs drain.

### Post-migration (Stage 4 done)

- Verify deployment-ui data-status panel: every asset_group's `available_at` populated; no legacy columns; no 1440-NaN
  placeholder rows; partial-bundle rows show as `attempted_failed`.
- Re-run smoke backfills per asset_group to confirm `LookaheadBiasError` strict-mode is healthy.
- Resume normal VM operation. Fleet should be writing exclusively v7-canonical shape with per-row `available_at`.

### Coordination with other agents (workspace-wide rule reminder)

Per CLAUDE.md `§ Two teammates × multiple parallel agents`:

- Other agents (Harsh's + Ikenna's parallel sessions) may push code touching the same surfaces (UTL
  `instruments_write_gate.py`, MDPS adapters, features-sports) DURING this migration window. **Watch for stash
  conflicts** when committing migration changes.
- Don't run `git checkout origin/<branch> -- .` as a recovery move — it dumps remote changes into the working tree. Mass
  resets pull in 20+ files of noise from old stashes.
- If a per-agent migration commit conflicts with another agent's WIP, resolve by editing surgically not by mass-reset.
- The DIRTY-FILE EXCLUSION on `unified-trading-library/tests/unit/test_availability_stamping.py` (Stage 1 Phase 3
  constraint) is the canonical example — still flagged as do-not-touch until owner commits.

## Anti-patterns (DO NOT)

- Do NOT add a "fallback reader" to read both old and new manifest shapes — workspace rule "Manifest migration NOT
  fallback".
- Do NOT run Stage 2.C strict-mode flip before Stage 1 Phase 3 atomic rename ships.
- Do NOT delete old parquets in Stage 3 migrations before hand-verification + operator approval.
- Do NOT run multi-worker migrations without per-VM shard isolation.
- Do NOT touch `unified-trading-library/tests/unit/test_availability_stamping.py` (dirty with another agent's WIP per
  Stage 1 Phase 3 constraint).
- Do NOT add this plan's todos here. They belong in the parent plans. This plan is coordination-only.
