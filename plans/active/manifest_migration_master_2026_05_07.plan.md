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

## Anti-patterns (DO NOT)

- Do NOT add a "fallback reader" to read both old and new manifest shapes — workspace rule "Manifest migration NOT
  fallback".
- Do NOT run Stage 2.C strict-mode flip before Stage 1 Phase 3 atomic rename ships.
- Do NOT delete old parquets in Stage 3 migrations before hand-verification + operator approval.
- Do NOT run multi-worker migrations without per-VM shard isolation.
- Do NOT touch `unified-trading-library/tests/unit/test_availability_stamping.py` (dirty with another agent's WIP per
  Stage 1 Phase 3 constraint).
- Do NOT add this plan's todos here. They belong in the parent plans. This plan is coordination-only.
