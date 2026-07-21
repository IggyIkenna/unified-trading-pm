---
doc_type: plan
title: sports-data-available-at-rename
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service]
scope: [engineer, admin]
tags: []
related:
  [
    writegate_honest_coverage_endtoend_2026_05_06,
    master_to_live_defi_2026_05_23,
    sports_fixtures_legacy_schema_migration_2026_04_28,
  ]
created: "2026-05-07"
slug: sports_data_available_at_rename_2026_05_07
date: 2026-05-07
owner: claude-code
priority: P1
phase: pending_approval
domain: data-pipeline
locked_by: live-defi-rollout
locked_since: 2026-05-07
---

## Deferred work — migrated to: `plans/epics/sports_master.md` — successor: sports_master (Phase 2 GCS migration +

Phase 3 4-repo rename + Phase 4 writegate verify/unlock all shipped per that epic, incl. `instruments-service@fc7b306`,
`features-service@9847b350`. **GENUINELY ORPHANED REGRESSION FOUND**: the UTL half of the Phase-3 rename
(`instruments_write_gate.py::DEFAULT_AS_OF_COLUMNS`, `point_in_time.py` default `timestamp_col`) was silently reverted
back to the legacy `data_available_at` name by an unrelated commit (`988ab287`, 2026-05-23) — the no-lookahead scan on
sports data has been silently a no-op ever since. Filed as
`plans/active/issues/unified_trading_library_data_available_at_rename_silently_reverted_2026_07_21.md` (P1). NOTE:
`locked_by: live-defi-rollout` was never cleared at archival — flagged for operator `[unlock-plan]` cleanup.)

# Sports `data_available_at` → `available_at` rename + GCS column migration

## Background

Sports adapters + schemas are the only place in the workspace that uses the prefixed column name `data_available_at`.
Every other service uses the canonical `available_at` (per CLAUDE.md "`available_at` is per-row, write-time, equal to
live-pipeline-arrival" SSOT). UTL `assert_available_at_present` (called inside `ManifestWriter.record_captured`) checks
for canonical `available_at` and raises `LookaheadBiasError` when missing.

**Why this matters now**: writegate plan Phase 2.C flips `LookaheadBiasError` to strict-mode workspace-wide. The flip
hard-fails every sports `record_captured` call as long as sports parquets and writers stamp `data_available_at`
(canonical-name absent → bias check fails). This rename is the prerequisite for Phase 2.C strict-mode flip.

**Decision recorded**: master plan Q&A 14 (HIGH-2) 2026-05-06; resolution shape = full rename + one-time GCS column
migration (per workspace "manifest migration not fallback" rule). No reader fallback path is acceptable.

**Headline**: 4-repo coordinated change + 1 operator action (GCE VM run) + atomic ship to retire the prefixed column
name. Required before writegate Phase 2.C strict-mode flip.

## Pre-audit manifest

Confirmed via workspace grep 2026-05-07. **Every callsite is listed** — agent does not need to re-scan.

### UAC — sports schema declarations

| File                                                                  | Lines              | Action                                                                                         |
| --------------------------------------------------------------------- | ------------------ | ---------------------------------------------------------------------------------------------- |
| `unified_api_contracts/internal/schemas/_sports_shared.py`            | 13                 | Rename column declaration `name="data_available_at"` → `name="available_at"`.                  |
| `unified_api_contracts/internal/schemas/_sports_contracts.py`         | 188, 280, 373, 628 | 4 column declarations + 1 description string. Rename all `data_available_at` → `available_at`. |
| `unified_api_contracts/internal/schemas/_sports_match_contracts.py`   | 21, 338            | 2 docstring/comment references. Rename to canonical.                                           |
| `unified_api_contracts/internal/schemas/_sports_derived_contracts.py` | 230                | 1 description string. Rename.                                                                  |

### UTL — instruments write-gate + PIT

| File                                                | Lines              | Action                                                                                                                          |
| --------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| `unified_trading_library/instruments_write_gate.py` | 60–63, 185, 398    | `DEFAULT_AS_OF_COLUMNS` tuple includes `"data_available_at"`. Replace with `"available_at"`. Update `__all__` reference at 398. |
| `unified_trading_library/point_in_time.py`          | 201                | Comment reference `Mirrors instruments-service's own data_available_at for fixtures`. Update comment to `available_at`.         |
| `tests/unit/test_instruments_write_gate.py`         | (multiple)         | Update test fixtures + assertions to use `available_at`.                                                                        |
| `tests/unit/test_point_in_time.py`                  | (multiple)         | Same.                                                                                                                           |
| `tests/unit/test_availability_stamping.py`          | (DIRTY — not mine) | **DO NOT TOUCH** in initial pass — currently has uncommitted edits by another agent (Harsh). Coordinate before final ship.      |

### instruments-service — orchestrator + scripts

| File                                                | Lines                                                                       | Action                                                                                                                                              |
| --------------------------------------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `instruments_service/engine/orchestrator.py`        | 253, 3338, 3474, 3528, 3678, 4169, 4458, 4628, 4848, 5548, 6046, 6048, 6050 | 13 callsites — sports + weather paths. Each writes `df["data_available_at"] = ...` based on per-source stamping rule. Rename all to `available_at`. |
| `scripts/recover_fixtures_from_truthset.py`         | 144, 172, 173, 180, 184, 188, 200                                           | 7 callsites — `_post_fill_data_available_at` helper + caller. Rename function + callsites + docstring.                                              |
| `scripts/migrate_local_sfi_to_canonical.py`         | 21, 299, 365                                                                | 3 callsites — comment + `_id_cols` set + post-fill block. Rename.                                                                                   |
| `tests/unit/test_orchestrator_write_gate.py`        | (multiple)                                                                  | Update test fixtures + assertions.                                                                                                                  |
| `tests/unit/test_orchestrator_fixture_flattener.py` | (multiple)                                                                  | Same.                                                                                                                                               |

### features-sports-service

| File                                                    | Lines                                         | Action                                                                                                 |
| ------------------------------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `features_sports_service/cli/handlers/batch_handler.py` | (TBD — confirmed present 2026-05-07 via grep) | Update reader-side reference. Likely intersects writegate Phase 2.C `_ensure_timestamp` deletion work. |

### GCS parquet files (on-disk)

All sports parquets under `gs://instruments-store-sports-{pid}/sports_reference/by_date/day=*/entity=*/` whose schema
includes a `data_available_at` column. Written across multiple years (~2018-onward per sports source coverage).
Migration must rename the column in-place without rewriting unrelated cells.

## Execution DAG

```
Phase 0 (audit)            Phase 1 (script)         Phase 2 (operator)        Phase 3 (atomic rename)         Phase 4 (verify)
─────────────────          ─────────────────        ────────────────────       ────────────────────────         ──────────────
[shipped 2026-05-07]   →   [SCRIPT] migration  →   [OPERATOR] same-region  →  [SCRIPT/AGENT] coordinated  →  [QG] writegate
this plan = audit          + tests + dry-run        GCE VM runs migration      4-repo source rename            Phase 2.C unblocks
```

Phase 2 gates Phase 3. Phase 3 is atomic across the 4 repos (commit each, push together) — readers must not see new
`available_at` writes while old `data_available_at` parquets exist OR vice versa.

## Phase 0 — Pre-audit (shipped 2026-05-07)

- [x] [AUDIT] P1. Workspace-wide grep for `data_available_at` write sites + `DEFAULT_AS_OF_COLUMNS` references.
      Confirmed callsites in UAC (4 schema files) + UTL (write-gate + PIT + tests) + instruments-service (orchestrator +
      2 scripts + tests) + features-sports-service (batch_handler). Manifest above is exhaustive.
- [x] [AUDIT] P1. Confirm UTL `assert_available_at_present` (called inside `ManifestWriter.record_captured`) raises
      `LookaheadBiasError` when only prefixed `data_available_at` is present — confirmed via reading
      `unified_trading_library/availability_stamping.py` + UTL `manifest_writer.py` `record_captured`.
- [x] [AUDIT] P1. Confirm writegate Phase 2.C strict-mode flip is the downstream gate this rename unblocks. See
      writegate plan § Phase 2.C.
- [x] [AUDIT] P1. Confirm rename does NOT conflict with sports-fixtures-legacy-schema-migration plan (it is independent
      — that plan covers nested-struct → flat schema; `data_available_at` is in BOTH legacy + new sports schemas).

## Phase 1 — Migration script (THIS PLAN'S PRIMARY DELIVERABLE)

**Goal**: Write `instruments-service/scripts/migrate_sports_available_at_column.py` that renames the column in-place
across all sports parquets without rewriting unrelated cells. Idempotent, dry-run-capable, manifest-safe.

- [x] [SCRIPT] P0. Create `instruments-service/scripts/migrate_sports_available_at_column.py`. Inputs:
      `--bucket gs://instruments-store-sports-{pid}` `--prefix sports_reference/by_date/` `--workers <N>` `--dry-run`
      `--vm-name <tag>` (per-VM shard isolation if multi-worker). Behaviour: enumerate parquets via `list_blobs()` with
      HTTP pool tuned to `2*workers`; for each parquet: (a) read schema via `pyarrow.parquet.read_schema()` (cheap, no
      row read); (b) if column `data_available_at` present AND `available_at` absent → rename column atomically +
      re-write parquet; (c) if both columns present (mid-migration restart) → drop the legacy `data_available_at`
      column, keep `available_at`; (d) if only `available_at` present → skip (already migrated); (e) if neither present
      → log + skip (parquet is older schema; outside this migration's scope). Idempotent: rerun does no work on
      already-migrated files. Per-file emit `MIGRATION_PROGRESS` event with
      `{path, action, n_rows, schema_before, schema_after}`.
- [x] [SCRIPT] P0. Add unit tests at `instruments-service/tests/unit/test_migrate_sports_available_at_column.py`.
      Synthetic parquets covering the 4 cases (a/b/c/d). 11 tests pass. Multi-worker concurrency is handled via per-blob
      CAS (`if_generation_match`) — operator pauses concurrent FWD/BACKFILL VMs per Phase 2 anyway.
- [x] [SCRIPT] P0. Quality-gate the script: ruff clean. basedpyright argparse-`Any` errors are out-of-scope (scripts/
      not in `tool.basedpyright.include`). No `os.getenv()` — uses `--project-id` arg + GCS client.
- [x] [QG] P1. PM master plan Q&A 14 cross-link to this plan landed via commit `8759f59e` (PM) + `8050477`
      (instruments-service).
- [ ] [DEFERRED] P2. Add dry-run integration test that lists ~10 real GCS files. Deferred — operator will run the
      `--dry-run --limit 10` smoke directly on the same-region VM in Phase 2; integration test against real GCS adds
      complexity (ADC + cross-region) for marginal value over operator-driven smoke.

**Phase 1 success criteria**:

- Script ships in instruments-service.
- Tests pass on `cd instruments-service && bash scripts/quality-gates.sh`.
- Dry-run output sample saved at `instruments-service/scripts/migrate_sports_available_at_column.dryrun.md` for operator
  to inspect before running.

## Phase 2 — Operator runs migration (sequenced after Phase 1)

This phase is **operator-driven** (not agent-shipped). VM runs cross-region are 18× slower than same-region
(`asia-northeast1-c`); migration MUST run on a same-region VM.

- [ ] [OPERATOR] P0. Pause sports forward-poll VMs (`af-fwd-*`, `fs-fwd-*`, `tm-fwd-*`, `sfi-fwd-*`, `us-fwd-*`,
      `openmeteo-fwd-*`) — they're writing to the bucket the migration is rewriting.
- [ ] [OPERATOR] P0. Pause sports backfill VMs (`af-backfill-*`, `fs-backfill-*`, etc.) for same reason.
- [ ] [OPERATOR] P0. Launch migration VM in `asia-northeast1-c` per CLAUDE.md "Always run on a same-region GCE VM". VM
      name `sports-migrate-available-at-{ts}` (add to `VM_PREFIX_TO_BUCKET` in `vm_zombie_watchdog.py` first). Run with
      `--dry-run` first, review output, then full run.
- [ ] [OPERATOR] P0. Verify migration completion: spot-check ~20 parquets across years 2018–2026 to confirm column
      rename. `pq.read_schema(uri).names` includes `available_at` and not `data_available_at`.
- [ ] [OPERATOR] P0. Resume forward-poll + backfill VMs ONLY AFTER Phase 3 atomic source rename ships.

## Phase 3 — Atomic source rename across 4 repos (sequenced after Phase 2 completes)

This phase is the agent-driven coordinated source-code change. Each repo commits separately; pushes are coordinated so
no reader sees new writes against pre-migration parquets.

- [ ] [SCRIPT] P0. UAC — rename in 4 schema files. 1 commit. Push to `live-defi-rollout`.
- [ ] [SCRIPT] P0. UTL — rename `DEFAULT_AS_OF_COLUMNS` + `point_in_time.py` comment + tests. 1 commit. Push.
- [ ] [SCRIPT] P0. instruments-service — rename 13 orchestrator callsites + 2 scripts + tests. 1 commit. Push.
- [ ] [SCRIPT] P0. features-sports-service — rename batch_handler reference. **Coordinate with writegate Phase 2.C**
      (`_ensure_timestamp` deletion + per-source stamping happens in same file region; if Phase 2.C is mid-flight, fold
      this rename into that work instead of separate commit).
- [ ] [QG] P0. Run quality-gates.sh on all 4 repos sequentially (UAC → UTL → instruments-service → features-sports).
      Each repo's QG must pass before pushing the next.
- [ ] [SCRIPT] P0. Workspace-wide ripgrep for stragglers: `rg -n 'data_available_at' --type py --glob '!.venv*'` returns
      ZERO non-test, non-archived results. Test references that mock raw on-disk legacy data may keep
      `data_available_at` with explicit `# legacy migrated 2026-05-XX` comment.

**Phase 3 success criteria**:

- All 4 repos shipped to `live-defi-rollout` with rename complete.
- No workspace-wide source references to `data_available_at` remain (excluding migrated-from comments + archived plans).
- All 4 repos' quality gates pass.

## Phase 4 — Writegate Phase 2.C unblock + verification

- [ ] [SCRIPT] P0. Re-run `instruments-service/scripts/quality-gates.sh` end-to-end on a sports backfill smoke run.
      Confirm `record_captured` no longer raises `LookaheadBiasError` on sports.
- [ ] [VERIFY] P0. Update writegate plan Phase 2.C "prerequisites" section to mark sports `available_at` rename as
      shipped + reference this plan's commits.
- [ ] [VERIFY] P0. Update master plan Q&A 14 to mark HIGH-2 as SHIPPED + record commit SHAs.
- [ ] [VERIFY] P0. Resume forward-poll + backfill VMs (operator action).
- [ ] [UNLOCK] P0. Once all phases complete, request `[unlock-plan]` to archive this plan.

**Phase 4 success criteria**:

- Sports backfill smoke writes `available_at` to GCS.
- Sports forward-poll writes `available_at` to GCS.
- writegate Phase 2.C is unblocked for sports.
- Master plan + writegate plan updated with shipped status.

## Risk register

| Risk                                                                     | Likelihood | Impact                                                                                                           | Mitigation                                                                                                                                                                                             |
| ------------------------------------------------------------------------ | ---------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Forward-poll VMs write new `data_available_at` parquets DURING migration | High       | Migration completes but new writes diverge → mixed state                                                         | Phase 2 explicitly pauses forward-poll + backfill VMs before migration starts. Resume only after Phase 3 atomic rename ships.                                                                          |
| Phase 3 commits land out-of-order (e.g. UTL pushes before UAC)           | Medium     | Brief window where readers expect canonical column but UAC schema declarations still say prefixed                | Sequence is UAC → UTL → instruments-service → features-sports. Each push gates the next. If push order breaks, revert + redo.                                                                          |
| writegate Phase 2.C ships in parallel and modifies same files            | Medium     | Conflict on `features-sports/cli/handlers/batch_handler.py` + `unified_trading_library/availability_stamping.py` | Phase 3 features-sports todo flags coordination. If 2.C is mid-flight, fold this rename into 2.C's batch_handler work. Branch `live-defi-rollout` is shared so latest pull wins.                       |
| Migration script bug rewrites cells incorrectly                          | Medium     | Data corruption                                                                                                  | Phase 1 ships dry-run + unit tests covering 4 cases. Operator runs `--dry-run` first + spot-checks 20 parquets across years before full run.                                                           |
| GCS migration takes longer than expected (wall-clock)                    | Low        | Window of paused VMs > acceptable                                                                                | Same-region VM (per workspace rule, 18× faster). Estimate: ~10⁵ parquets × 200ms each ≈ 5–6h on 1 worker; multi-worker shards in 1–2h.                                                                 |
| Sports tests file `test_availability_stamping.py` has someone else's WIP | Low        | Phase 3 UTL commit absorbs unrelated edits                                                                       | Phase 3 UTL commit explicitly excludes `tests/unit/test_availability_stamping.py` until coordinated; left dirty for owner to commit separately. Workspace rule "don't touch unfamiliar files" applies. |

## Cross-references

- **Master plan Q&A 14** (HIGH-2): [`master_to_live_defi_2026_05_23.md`](./master_to_live_defi_2026_05_23.md) — original
  decision.
- **Writegate Phase 2.C** (the consumer of this rename):
  [`writegate_honest_coverage_endtoend_2026_05_06.md`](./writegate_honest_coverage_endtoend_2026_05_06.md).
- **Honest absence downstream SSOT** (companion principle): `codex/02-data/honest-absence-downstream-handling.md`.
- **Migration precedent** (idempotent column-level migration):
  `instruments-service/scripts/migrate_local_sfi_to_canonical.py`.
- **Workspace rule** ("manifest migration not fallback"): `cursor-configs/CLAUDE.md` § Shard-granularity SSOT.
- **CLAUDE.md `available_at` semantics** (the canonical column name + per-source stamping): `cursor-configs/CLAUDE.md` §
  "`available_at` is per-row, write-time, equal to live-pipeline-arrival".

## Temporary states + their canonical follow-up plans

None — this plan retires a temporary state (sports prefixed `data_available_at`) rather than introducing one. After
Phase 4 completes, the only `data_available_at` references that remain are in archived plans and in test fixtures that
mock raw legacy on-disk data (each marked with `# legacy migrated YYYY-MM-DD` comment).
