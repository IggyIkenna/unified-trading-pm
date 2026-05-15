---
name: manifest-schema-final-gate-2026-05-09
overview: |
  One-shot maximalist plan that lands the BEST manifest (v8 with all designed columns) on real GCS infra by
  2026-05-23 — no partial state, no deferred items, every plan checkbox flipped `[x]` before cutover. Bundled
  Phase 3 parquet walk does FIVE migrations in ONE pass to fit the 14-day window: (1) `pipeline_mode=` hive
  partition, (2) `category=` → `asset_group=` rekey, (3) 5 drift axes from 2026-05-04 phantom audit, (4) v8
  NULL-column backfill (`service_emission_state` + `last_emission_decision_at` +
  `expected_window_completeness_fraction`), (5) cross-asset rescan class-A auto-fixes. Closed-set
  `ServiceEmissionStateEnum` ratified inline (4 values: `PUBLISHED_OK` / `PUBLISHED_DEGRADED` /
  `STALE_DATA_HEARTBEAT_ONLY` / `BLOCKED`) — slice b spec landed as part of this plan. Workspace-wide Phase 4
  consumer sweep across 8 repos is critical-path. Two-stage MTDS bounce-sweep: drain May 12, full launch May 16.
  E3 7-item launcher checklist ratified verbatim by operator 2026-05-09. Hard-stop: no schema additions between
  2026-05-09 and 2026-05-23 — every new column proposal defers to post-cutover.
type: infra
epic: epic-infra
status: active
asset_group: cross-cutting
priority: P0
deadline: 2026-05-23
parent: master_to_live_defi_2026_05_23
spawned_from: plans/questions/backfill_manifest_schema_freeze_gate_2026_05_08.md
locked_by: live-defi-rollout
locked_since: 2026-05-09
created: 2026-05-09
last_updated: 2026-05-09

completion_gates:
  code: C5
  deployment: D3
  business: F17+F18+G23

repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: market-tick-data-service
    code: C0
    deployment: none
    business: none
  - repo: market-data-processing-service
    code: C0
    deployment: none
    business: none
  - repo: instruments-service
    code: C0
    deployment: none
    business: none
  - repo: features-service
    code: C0
    deployment: none
    business: none
  - repo: deployment-api
    code: C0
    deployment: none
    business: none
  - repo: deployment-service
    code: C0
    deployment: none
    business: none
  - repo: e2e-testing
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none

depends_on:
  - manifest-v7-schema-migration-design-2026-05-08
  - gcs-migration-bundle-pipeline-mode-2026-05-08
  - manifest-cross-asset-rescan-design-2026-05-08
  - writegate-honest-coverage-endtoend-2026-05-06
  - live-pipeline-mtds-mdps-features-2026-05-08
  - features-repo-consolidation-2026-05-08

related_plans:
  - plans/questions/backfill_manifest_schema_freeze_gate_2026_05_08.md
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/epics/manifest_migration_master_2026_05_07.md
estimate_class: design
estimate_baseline_ai_days: 3.5
estimate_calibrated_ai_days: 2.1
estimate_calibration_note: |
  Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~3-4). Class inferred from filename (design, multiplier 0.6×).
  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be double-counted. Owner agent: verify baseline, refine class per codex/08-workflows/estimation-calibration.md, recompute calibrated if either changes.
---

# Manifest schema final gate — best v8 by 2026-05-23 (no partials, all items done)

> **🟡 IN-FLIGHT REFACTOR — batch_live_symmetry 2026-05-14** (BE-AWARE) `BatchExecutionMode` enum +
> `RECON_GREEN_THRESHOLDS` shipped at UAC@01c1b59. Re-verify any archetype-keyed batch/live routing code before touching
> pipeline_mode / reconciler threshold / mode-routing logic.

> **🟡 IN-FLIGHT REFACTOR — code-freeze sequencing 2026-05-10** (BLOCK)
>
> [`plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md)
> sequences this plan's **Phase 1 (v8 schema-bump)** as a Phase 1 freeze-gate item and **Phase 7 (gcs bundled walk May
> 13-15)** as Phase 2.1 + 2.2 of the cutover window. Per operator decision 2026-05-11 commit `39ab61e5` (resolving
> codex_audit F3 ambiguity), THIS plan is the canonical v8 column owner; writegate slice (b) Phase 5.2 ("UAC manifest
> schema columns") is SUPERSEDED. Phase 4.MTDS 🟡 BLOCKED 2026-05-12 on 3 PipelineMode operator findings
> (PM@`237d00b7` + `a5e5aa4d` + `6ede1e01`) — Phase 4.DEFAULT-REMOVAL chains. Reader contract: scan top-of-file banners
> before touching manifest v8 columns / writer / reader / `pipeline_mode` / `service_emission_state` / cross-asset
> rescan code paths.

> **Operator direction (verbatim, 2026-05-09).** _"i want the best manifest before may 23rd not a partial one all the
> items done."_ + _"yeah do all this v8 should not be deferred should be done"_ + ratification of the 7-item E3 launcher
> checklist verbatim.
>
> **What this plan is.** The maximalist successor to
> [`plans/questions/backfill_manifest_schema_freeze_gate_2026_05_08.md`](../questions/backfill_manifest_schema_freeze_gate_2026_05_08.md).
> Codifies the closed-set decisions ratified 2026-05-09 + lands every designed-but-not-shipped manifest item on real GCS
> infra by May 23 cutover. No "deferred-post-cutover" — that path was rejected.
>
> **Hard-stop.** Between 2026-05-09 and 2026-05-23, ANY proposal to add a new manifest column / row-key axis / hive
> partition is REJECTED → defer to post-cutover. The "best manifest" is v8 = v7 + 3 emission columns; the closed set is
> locked.

## Pre-audit manifest (Citadel § 1)

Full impact surface enumerated upfront. Every change MUST land within the 14-day window; any "deferred to later" is a
hard-stop violation per the maximalist directive.

### Repos touched

| Repo                                    | Scope                                                                                                                                                                                 | Key files                                                                                                                                                         |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `unified-api-contracts`                 | v8 schema-bump (3 columns + slice b enum) + `PipelineMode` already shipped                                                                                                            | `canonical/crosscutting/service_emission_policy.py` (extend), NEW `canonical/crosscutting/service_emission_state.py`, `canonical/crosscutting/manifest_schema.py` |
| `unified-trading-library`               | `ManifestWriter` 3 new columns + emission-policy hooks at write-and-publish boundary                                                                                                  | `manifest_writer.py`, `emission_publisher.py`, `manifest_reader_fallback.py`, NEW `manifest_migrations/v7_to_v8.py`                                               |
| `market-tick-data-service`              | Phase 4 sweep — explicit `pipeline_mode=` kwarg per adapter (Databento / Tardis / CCXT / Barchart / Yahoo / Sports / DeFi / Prediction) + emission-policy wire-in at publish boundary | `adapters/*.py`, `engine/orchestrator.py`                                                                                                                         |
| `market-data-processing-service`        | Phase 4 sweep + bundle-pipeline-mode propagation from input parquet                                                                                                                   | `engine/orchestrator.py`, `adapters/*.py`                                                                                                                         |
| `instruments-service`                   | Phase 4 sweep — catalog refresh writes + reconcile_phantom_manifest_rows_all.py update for v8 row shape                                                                               | `scripts/reconcile_phantom_manifest_rows_all.py`, `scripts/cross_asset_rescan.py` (NEW)                                                                           |
| `features-service` (post-consolidation) | Phase 4 sweep + emission-policy hooks; **GATED on features_repo_consolidation completing by May 16**                                                                                  | per-feature-group writers                                                                                                                                         |
| `deployment-api`                        | Manifest read endpoints handle v8 columns; data-status drilldown surfaces `service_emission_state`                                                                                    | `services/data_status.py`                                                                                                                                         |
| `deployment-service`                    | Cross-asset rescan launcher (`launch-cross-asset-rescan-vm.sh`) + watchdog dict prefix                                                                                                | `scripts/vm/launch-cross-asset-rescan-vm.sh` (NEW), `scripts/vm/vm_zombie_watchdog.py`                                                                            |
| `e2e-testing`                           | Phase 4 sweep — synthetic-fixture writers pass explicit pipeline_mode                                                                                                                 | `scripts/sports/`, `scripts/defi/`, `scripts/prediction/`                                                                                                         |
| `unified-trading-pm`                    | This plan + bundled v8 migration script + banner sweep across active plans                                                                                                            | `scripts/migration/manifest_v7_to_v8_2026_05_11.py` (NEW), `scripts/migration/gcs_migration_bundle_2026_05_08.py` (extend)                                        |

### Codex SSOTs touched (Post-Plan-Phase Codex Audit HARD RULE)

- **UPDATE** `codex/02-data/availability-manifest-and-data-status.md` — add v8 section + 4-state emission enum + reader
  migration window.
- **NEW** `codex/04-architecture/service-emission-policy.md` — full expansion of the slice-a stub; describe 4-state
  lifecycle + hook insertion points + consumer behaviour.
- **UPDATE** `codex/00-SSOT-INDEX.md` — register the new emission-policy doc.
- **CROSS-LINK** `codex/02-data/pipeline-mode-partition.md` — point at v8 design.
- **UPDATE** `codex/05-infrastructure/launcher-script-ssot.md` — register the rescan launcher prefix.

### UAC enums frozen for the window (A3 audit complete 2026-05-09 — FREEZE-CLEAN)

A3 audit verdict: **FREEZE-CLEAN.** Workspace-wide grep over 319 `(StrEnum|IntEnum|Enum)` classes in UAC

- closed-set constants + recent 14-day git activity + active-plan body grep for "add value / extend enum" proposals
  returned **zero at-risk enums** beyond the 5 listed below. No additional freeze additions needed.

The following closed sets are frozen 2026-05-09 → 2026-05-23. ANY proposal to add a value during the window is rejected;
defer to post-cutover.

- **`PipelineMode`** (`canonical/crosscutting/pipeline_mode.py:44`) — **18 values** verified (13 BATCH\_\* + 1
  LIVE_WEBSOCKET + 4 deferred batch sources). Freeze.
- **`ServiceEmissionStateEnum`** — **greenfield, not yet created.** Phase 1.A creates it at
  `canonical/crosscutting/service_emission_state.py` with 4 values: `PUBLISHED_OK` / `PUBLISHED_DEGRADED` /
  `STALE_DATA_HEARTBEAT_ONLY` / `BLOCKED`. Freeze at creation time.
- **`EmptyConfirmedReason`** / **`EMPTY_CONFIRMED_REASONS`** (`canonical/crosscutting/honest_coverage.py:68`) — **17
  values** verified (Wave 3.X added 8 new reasons 2026-05-07 pre-freeze including `EXPECTED_PARTIAL_HALF_DAY` /
  `EXPECTED_OUTSIDE_TRADING_HOURS` / `EXPECTED_OUTSIDE_TRANSFER_WINDOW` / `EXPECTED_PRE_SEASON` / `EXPECTED_POST_SEASON`
  / `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE` / `EXPECTED_DEPRECATED_DATA_TYPE` / `EXPECTED_REFDATA_CADENCE_CHANGE`).
  Freeze. Plan-body initial claim of "9 values" was stale — corrected.
- **`ServiceEmissionPolicy`** (`canonical/crosscutting/service_emission_policy.py:46`) — **4 values** verified:
  `STRICT_FAIL` / `PARTIAL_OK` / `NAN_FILL` / `BLOCK_CRITICAL`. Freeze. Plan-body initial claim cited stale value names
  (`PUBLISH_OK` / `PUBLISH_DEGRADED`) — corrected.
- **`capture_status`** — closed-set string literal (NOT a formal Enum; enforced at writer + UAC schema boundary):
  `captured` / `empty_confirmed` / `attempted_failed` / `expected_unattempted` (4 values). Freeze.

A3 audit also confirmed:

- Zero pending-plan proposals to add values to any of the 5 frozen enums in the May 9-23 window.
- Zero recent (last 14 days) git commits to the 5 frozen enum files beyond the writegate Wave 3.X work (already
  pre-freeze).
- Two unrelated `MarketState` definitions exist (`domain/market/__init__.py:11` +
  `internal/domain/market_data_processing/candle_schema.py:18`) — **not in row_key**, not at-risk, out-of-scope for this
  freeze. Capture as a post-cutover SSOT-consolidation finding (per CLAUDE.md Findings Triage Discipline case 4 → file a
  `plans/active/issues/<slug>.md` doc post-May-23).

## Phased execution DAG (Citadel § 2 + § 4)

```
                      Phase 0 (operator) — pre-audit run + ratchet baseline (May 9-10)
                                                  │
                ┌─────────────────────────────────┼─────────────────────────────────┐
                │                                 │                                 │
   Phase 1 (UAC v8 schema-bump)        Phase 2 (UTL v8 columns)      Phase 3 (rescan launcher)
   May 9-11 PARALLEL                   May 10-12 PARALLEL              May 9-11 PARALLEL
                │                                 │                                 │
                └─────────────────────────────────┼─────────────────────────────────┘
                                                  │
                            Phase 4 (workspace consumer sweep)
                            May 10-12 PARALLEL across 8 repos
                                                  │
                            Phase 5 (v8 migration script + bundled into gcs Phase 2)
                            May 11-12 SEQUENTIAL
                                                  │
                            Phase 6 (Bounce-sweep #1 — drain stale VMs)
                            May 12 SEQUENTIAL
                                                  │
                            Phase 7 (gcs Phase 3 BUNDLED WALK — operator-gated)
                            May 13-15 SEQUENTIAL
                                                  │
                            Phase 8 (Cross-asset rescan triage review)
                            May 15 SEQUENTIAL
                                                  │
                            Phase 9 (Bounce-sweep #2 — full launch)
                            May 16 SEQUENTIAL
                                                  │
                            Phase 10 (MTDS backfill execution)
                            May 16-20 PARALLEL by asset_group
                                                  │
                            Phase 11 (MDPS reprocess + features compute)
                            May 20-21 SEQUENTIAL (gated on features-consolidation)
                                                  │
                            Phase 12 (Paper-trade smoke + batch-vs-live recon + ratchet lock-in)
                            May 21-22 PARALLEL
                                                  │
                            Phase 13 (Live cutover)
                            May 23 — operator
```

QG gates between every phase boundary. No phase starts until the prior phase's QG + done-definition green.

## Phases

### Phase 0 — Operator pre-audit (May 9-10)

- [ ] [HUMAN] P0. Phase 0.A — Run gcs_migration Phase 0 pre-audit on a same-region `asia-northeast1-c` GCE VM.
      Calibrates Phase 7 wall-clock + per-bucket parquet count + drift histogram. Output: append
      `## Run results — 2026-05-09` to `plans/archive/issues/gcs_migration_bundle_preaudit_2026_05_08.md`. Gates Phase 7
      launch.
- [ ] [HUMAN] P0. Phase 0.B — Run `measure-honest-coverage.py` on production manifests for writegate Phase 5
      PRE-baseline. Output: per-data_type coverage % cells in `codex/02-data/honest_coverage_baseline_2026_05.md`. Gates
      Phase 12 ratchet POST-baseline comparison.

### Phase 1 — UAC v8 schema-bump (May 9-11, PARALLEL with Phase 2/3)

- [x] [AGENT] P0. Phase 1.A — Ratify slice b spec inline. NEW
      `unified-api-contracts/unified_api_contracts/canonical/crosscutting/service_emission_state.py` with
      `ServiceEmissionStateEnum` (4 values verbatim: `PUBLISHED_OK` / `PUBLISHED_DEGRADED` / `STALE_DATA_HEARTBEAT_ONLY`
      / `BLOCKED`) + manifest-read protocol (BLOCKED rows = consumer-skip + raise `ManifestRowBlockedError`; STALE_DATA
      = consumer-skip + log; PUBLISHED_DEGRADED = consume with degraded flag). 12 unit tests covering: closed-set
      enforcement; round-trip via JSON; consumer skip semantics; default-None back-compat for v7 rows. **SHIPPED
      2026-05-11** — UAC@174f401 (slot 6 ikenna-v8-schema-tab). 12 tests in `tests/unit/test_service_emission_state.py`
      cover all four contract bullets. `ServiceEmissionStateEnum` + `ManifestRowBlockedError` +
      `SERVICE_EMISSION_STATES` re-exported from `unified_api_contracts` root facade.
- [x] [AGENT] P0. Phase 1.B — Extend `service_emission_policy.py` to surface a `next_state(...)` resolver that maps
      `(ServiceEmissionPolicy, EmissionDecision)` → `ServiceEmissionStateEnum`. Pure function, no I/O. Tests: every
      (policy, decision) pair has a deterministic next_state. **SHIPPED 2026-05-11** — UAC@174f401.
      `next_state(*, policy, event)` is the resolver; signature uses `EmissionLifecycleEvent` (the structured
      `EmissionDecision.event_emitted` field) since that's UTL's `publish_with_policy` output surface. 8 new tests in
      `test_service_emission_policy.py` cover every (policy, event) pair + kwargs-only enforcement + pure-function
      determinism. Mapping: `STALE_DATA` → `STALE_DATA_HEARTBEAT_ONLY`; other three lifecycle events map 1:1 to state
      values.
- [x] [AGENT] P0. Phase 1.C — Manifest schema column declaration in `canonical/crosscutting/manifest_schema.py` (NEW or
      extend existing). 3 new columns: `service_emission_state` (str | None, ServiceEmissionStateEnum value);
      `last_emission_decision_at` (timestamp | None, ISO-8601 ms UTC); `expected_window_completeness_fraction` (float |
      None, 0.0-1.0). All nullable; v7 rows back-compat. **SHIPPED 2026-05-11** — UAC@174f401 with NEW
      `unified_api_contracts/canonical/crosscutting/manifest_schema.py` declaring all 3 column-name constants +
      `MANIFEST_SCHEMA_VERSION_V8 = 8` + `V8_NEW_COLUMNS` tuple + back-compat `V8_COLUMN_DEFAULTS` dict (all `None`) +
      `READER_FALLBACK_WINDOW_DAYS = 30`. 6 tests in `test_manifest_schema.py`. All 7 symbols re-exported from root
      facade. `__all__` alpha-sort drift from rebase caught by RUF022 + fixed in follow-up UAC@d938a69.
- QG: UAC quality-gates.sh clean (lint pass on my files; foreign lint errors from concurrent circuit-breaker / risk-rule
  rebase resolved by another agent's UAC@dc4c9f0; tests pass; basedpyright 0/0; codex compliance pass).
  **Done-definition**: `unified-api-contracts@174f401` + `@d938a69` shipped + 27 new tests added (12 emission_state + 8
  next_state + 6 manifest_schema + 1 EXPECTED_KNOWN_SOURCE_GAP). **2026-05-11 RENAME** — third v8 column renamed from
  `expected_window_completeness_pct` → `expected_window_completeness_fraction` at UAC@`76f950a` per operator-approved
  option (a) from
  [`plans/active/issues/expected_window_completeness_pct_range_drift_2026_05_11.md`](issues/expected_window_completeness_pct_range_drift_2026_05_11.md).
  Three-way SSOT drift on range convention (UAC said 0-1; codex said "0-100 fraction" oxymoron; column name `_pct`
  implied percentage; UTL `completeness_fraction` arg canonical 0-1). Rename free because zero on-disk writes had
  shipped. `_pct` constant name banned post-`76f950a`.

### Phase 2 — UTL v8 ManifestWriter (May 10-12, PARALLEL with Phase 1/3)

- [x] [AGENT] P0. Phase 2.A — `unified_trading_library/manifest_writer.py`: extend `record_captured` / `record_empty` /
      `record_failed` / `record_expected_empty` / `record_expected_unattempted` with 3 new kwargs
      (`service_emission_state` / `last_emission_decision_at` / `expected_window_completeness_fraction`) all defaulting
      to `None` for back-compat with existing callsites. Phase 4 sweeps the callsites; the default is REMOVED at end of
      Phase 4 (explicit-or-fail per the writegate Phase 4 P0 P0 contract). **SHIPPED 2026-05-12 slot 6 @UTL@0adea1c6** —
      12 unit tests landed in `tests/unit/test_manifest_writer_emission_state.py`.
- [x] [AGENT] P0. Phase 2.B — `emission_publisher.py` integration: extend `publish_with_policy` to compute
      `service_emission_state` via Phase 1.B `next_state(...)` and pass to ManifestWriter. Wired at the same publish
      boundary as the existing `EmissionDecision` flow. **SHIPPED 2026-05-12 slot 6 @UTL@001e8892** — `EmissionDecision`
      extended with `service_emission_state` + `last_emission_decision_at`; mirrored into event metadata for stream-grep
      observability. 6 new tests under `tests/events/test_emission_publisher.py`.
- [x] [AGENT] P0. Phase 2.C — Reader fallback: `manifest_reader_fallback.py` tolerates v7 (3 columns missing) for ≤30d
      post-Phase-7. Emit `READER_BACKFILLED_V8_COLUMNS_AS_NULL` event per row. After 30d zero-event window, fallback
      deleted (workspace "no double SSOT" rule). **SHIPPED 2026-05-12 slot 6 @UTL@5f2aacd6** — implemented inline in
      `manifest_writer.read_availability_index()` via `_V8_COLUMNS` + `_backfill()` (no separate module needed; reader
      lives next to writer). 30d cutover counter starts at Phase 7 ship date.
- [x] [AGENT] P0. Phase 2.D — NEW `manifest_migrations/v7_to_v8.py` helper: walks canonical
      `_index/availability_index.parquet` per bucket, adds 3 NULL columns to every existing row, writes per-VM shard at
      `_index/per_vm/v7_to_v8_migrate_{VM_NAME}.parquet`. Per-VM shard isolation MANDATORY. **SHIPPED 2026-05-12 slot 6
      @UTL@bae1ecb9** — `migrate_v7_to_v8()` + `migrate_v7_to_v8_buckets()` + `V7ToV8MigrationResult` +
      `MissingVMShardIsolationError` guard. 12 unit tests under `tests/unit/test_manifest_migrations_v7_to_v8.py`.
- QG: UTL quality-gates.sh clean. **Done-definition**: `unified-trading-library@<sha>` shipped + 11+ unit tests +
  back-compat with v7 rows. **STATUS — 4/4 sub-items ✅; UTL refs above; 30+ unit tests landed total.**
- [x] [AGENT] P2. **Phase 2 follow-up — `MANIFEST_SCHEMA_VERSION` vs codex doc drift (slot-6 audit finding
      2026-05-11).** **RESOLVED 2026-05-12 (option b) — `ikenna-v8-manifestwriter-tab` (slot 2) @PM@`6efbfced`:** chose
      option (b) per Phase-2 done-definition's own framing ("back-compat with v7 rows... bumps to 8 at end of Phase 4").
      Codex doc
      [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
      lines 258-262 + 265 reconciled: prose now says "`MANIFEST_SCHEMA_VERSION = 7` (transitional; bumps to 8 at end of
      Phase 4.DEFAULT-REMOVAL)" matching the embedded code snippet at line 265. The "Schema v8 (current; ratified)"
      header is preserved because the column-shape contract IS final + ratified — only the version-constant lags one
      phase behind, by design. Plan body Phase 4.DEFAULT-REMOVAL extended below to include the bump-to-8 + remove all 3
      v8-emission-column `None` defaults at the same time as `pipeline_mode=` removal. No code change needed; the
      manifest*writer.py constant value of `7` was correct all along. `manifest_writer.py:131` is still
      `MANIFEST_SCHEMA_VERSION = 7` while the v8 emission columns (`service_emission_state` /
      `last_emission_decision_at` / `expected_window_completeness_fraction`) ARE present in the `AvailabilityRecord`
      dataclass + the 5 `record**` method sigs (Phase 2.A @UTL@`0adea1c6`). That looks *intentional* per the Phase-2
      done-definition ("back-compat with v7 rows" — v7-labeled rows carry nullable v8 columns until Phase 4 makes the
      kwargs required, THEN bump to 8) — but the codex doc `codex/02-data/availability-manifest-and-data-status.md`
      overstates it: line 261 prose says "`MANIFEST_SCHEMA_VERSION = 8` ... in `manifest_writer.py`" while the embedded
      code snippet (line 265) correctly says `MANIFEST_SCHEMA_VERSION = 7` — internal inconsistency in the doc +
      doc-prose-vs-code drift. Nothing branches on `schema_version == 8` (grepped
      UTL/deployment-api/MTDS/MDPS/instruments-service — zero hits), so no current reader-logic breakage. **Decision
      needed (ikenna-slot-6 / this plan owner)**: either (a) the code should bump to 8 now (and the codex snippet at
      line 265 updates to 8), OR (b) the code stays at 7 transitionally and the codex prose at line 261 + the "Schema v8
      (current; ratified)" header soften to "transitionally writing v7-labeled rows with nullable v8 columns; bumps to 8
      at end of Phase 4". Pick one + reconcile the doc. Source: slot-6 codex-audit pass 2026-05-11, prompted by the
      13:30 `[main → slot 6]` ping ("verify the v8 ManifestWriter is *shipped\* not just UAC-declared"). No urgency —
      additive, back-compat, no reader breakage; but it's a "docs are the intent" drift.

### Phase 3 — Cross-asset rescan launcher (May 9-11, PARALLEL with Phase 1/2)

- [x] [AGENT] P0. Phase 3.A — NEW `deployment-service/scripts/vm/launch-cross-asset-rescan-vm.sh` per the spec at
      `manifest_cross_asset_rescan_design_2026_05_08.md` lines 113-127 (singleton-lock, same-region zone, per-VM shard
      isolation envvars, `WORKERS=64` + `HTTP_POOL_SIZE=128`, tarball-default + tarball-from-local flag). Mirrors
      `launch-sfi-forward-poll.sh` precedent. **SHIPPED 2026-05-12 slot 6 @deployment-service@19fad8c** — 184-line
      launcher with singleton-lock + `--apply` toggle + `cefi|defi|tradfi|sports|prediction|cross_asset_all` dispatch.
- [x] [AGENT] P0. Phase 3.B — Add `cross-asset-rescan-` prefix to `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` dict.
      Relaunch watchdog VM after dict update (running watchdog only fetches Python at boot per CLAUDE.md "VM Naming
      Convention" rule). **SHIPPED 2026-05-12 slot 6 @deployment-service@19fad8c** (same commit as 3.A) — prefix
      registered as `None` (heartbeat-only; rescan VM writes to canonical per-asset-group manifest, not a dedicated
      shard bucket). **DEFERRED — operator runs watchdog VM relaunch**
      (`gcloud compute instances delete     vm-zombie-watchdog-* --zone=asia-northeast1-c --quiet` then
      `bash deployment-service/scripts/vm/launch-vm-zombie-watchdog.sh`) before the first rescan VM launch — running
      watchdog only fetches Python at boot.
- [x] [AGENT] P0. Phase 3.C — Register launcher in deployment-api `_SERVICE_LAUNCHER_SCRIPTS` registry so Deploy-Missing
      UI can surface it. **SHIPPED 2026-05-12 slot 6 @deployment-api@c8a1cd4** — `cross-asset-rescan` slug added.
- [x] [AGENT] P0. Phase 3.D — NEW `instruments-service/scripts/cross_asset_rescan.py` (Harsh Tab 4 scope per rescan
      design line 22, but if Harsh's queue can't fit it by May 11 a fresh sub-agent picks it up). Implements class A
      auto-flips + class C triage routing per rescan design § "Rescan flip schema". **SHIPPED 2026-05-12 slot 6
      @instruments-service@a264f21** — 333-line orchestrator on top of existing `reconcile_phantom_manifest_rows_all.py`
      (handles 5 drift axes). Adds `cross_asset_all` dispatch + per-VM shard tag from `VM_NAME` + `VM_APPLY_FLIPS`
      gate + triage JSONL streaming to `gs://{pid}-rescan-triage/{run_id}/triage.jsonl` + lifecycle events
      (RESCAN_RUN_STARTED / RESCAN_SHARD_STARTED / RESCAN_SHARD_COMPLETED / RESCAN_SHARD_FAILED / RESCAN_RUN_STOPPED /
      RESCAN_RUN_FAILED).
- QG: deployment-service + instruments-service quality-gates.sh clean. **Done-definition**: launcher script + Python
  script + watchdog registration shipped. **STATUS — 4/4 sub-items ✅ (3.B watchdog relaunch is operator's standard
  follow-up; not a code item).**

### Phase 4 — Workspace-wide consumer sweep (May 10-12, PARALLEL across 8 repos)

> Citadel § 6 extension: workspace-wide grep + per-adapter wire-in. NOT just MTDS. Per CLAUDE.md "Citadel- Grade
> Planning Standards § 6 Downstream Consumer Updates."

Spawn 8 parallel sub-agents (one per repo) per CLAUDE.md "Sub-Agents & Autonomous Agents: Full Rules Required" rule —
paste `SUB_AGENT_MANDATORY_RULES.md` at the top of each Task prompt.

- [x] [AGENT] P0. Phase 4.MTDS — Each adapter (Databento / Tardis / CCXT / Barchart / Yahoo / Sports / DeFi /
      Prediction) explicitly passes `pipeline_mode=PipelineMode.BATCH_<source>` per UAC SOURCE_PRIORITY
  - emission-policy hooks via `publish_with_policy`. **Per E3 ratified item.** **✅ SHIPPED 2026-05-12 by Ikenna slot 3
    (`ikenna-codefreeze-audit-tab`)**: 3-sub-agent fan-out (MTDS + MDPS + instruments-service) executed in parallel
    after operator-relayed Q1+Q2 approval at PM@`4c573302`.
    - **Q1 = (α)**: `DefiManifestRecorder` migrated to v8 record\_\* path at MTDS@`3da3f43` (record_empty +
      record_failed fully migrated; record_captured retains `add()`-path wrapper with explicit `pipeline_mode=` forward
      via \*\*kwargs — bounded interpretation; full df-flow propagation through every DeFi handler tracked as Phase
      4.DEFAULT-REMOVAL successor scope).
    - **Q2 = (A)**: UAC@`52d289c` shipped 6 new PipelineMode batch values + 14 DeFi SOURCE_PRIORITY gap entries;
      UAC@`7d7ea4c` added 7 additive per-member round-trip tests pinning (enum value, source string) pairs.
    - **MTDS sweep**: 97 callsites in 26 files at MTDS@`3da3f43` (20 DeFi handlers + DefiManifestRecorder +
      MTDSShardManifestRecorder + websocket_runner + orchestrator sentinel helper
      `_resolve_pipeline_mode_for_sentinel`). PM baseline shrunk 114 → 17 at PM@`88226bdb`.
    - **UTL sweep**: 11 internal record\_\* callsites at UTL@`12d5e621` (4 streaming/candle_writer LIVE_WEBSOCKET + 1
      streaming/parallel_per_symbol_runner threaded kwarg + 1 streaming/live_aggregator whitelist marker for Protocol
      method + 3 manifest_writer_normalising delegating-wrapper signatures + 1 per_leaf_failure dataclass field + 1
      manifest_writer.py:1919 internal plumbing). PM baseline shrunk 17 → 6 at PM@`ea50eddc` (only Phase 4.FEATURES
      entries remain).
    - **Q3-Q5**: orchestrator dispatch strategy / reconciler preservation / test fixture updates addressed inline. See
      `plans/active/issues/mtds_pipeline_mode_sweep_ambiguities_2026_05_12.md` (flipped ✅ RESOLVED at PM@`4c573302`).
    - **AST-walk QG STEP 5.70**: `OK — 6 baselined occurrences; 0 new occurrences` workspace-wide (6 remaining are Phase
      4.FEATURES scope, separate slot).
    - **DefiManifestRecorder record_captured full-v8 migration**: deferred to Phase 4.DEFAULT-REMOVAL (df-flow
      propagation through every DeFi handler needs separate plan or successor).
- [x] [AGENT] P0. Phase 4.MDPS — candle writer + reprocess engine propagate `pipeline_mode` from input parquet's column.
      Emission-policy hooks at publish boundary. **SHIPPED 2026-05-12 slot 2 spawned `ikenna-v8-mw-mdps-sweep` sub-agent
      @MDPS@`a3c7198`** — 22 callsites across 16 files (8 source + 2 scripts + 6 tests). New helper
      `resolve_pipeline_mode_from_source(blob_path)` parses `pipeline_mode=<value>` hive partition segment from GCS blob
      path; legacy pre-v8 paths fall back to `BATCH_DATABENTO`. Threaded through `write_candle_parquet` /
      `candle_write_mixin._write_candles` / `live_workers._process_instrument_file` /
      `batch_workers._handle_empty_tick_data` / `orchestration_writer` VIX 15m gap path /
      `live_aggregator._MDPSManifestRecorder` (LIVE_WEBSOCKET) / `io/writer.CandleWriter`. Emission-policy hooks already
      in `canonical_writer.write_candle_parquet` from prior Phase 6.2 ship @MDPS@`311614a`. QG: 1174 tests passing, 1
      pre-existing foreign failure (`test_cli_main::test_cli_help`); basedpyright clean on edited files. Finding filed:
      [`mdps_vix_15m_yahoo_barchart_pipeline_mode_gap_2026_05_12.md`](../archive/issues/mdps_vix_15m_yahoo_barchart_pipeline_mode_gap_2026_05_12.md).
- [x] [AGENT] P0. Phase 4.INSTRUMENTS — catalog refresh writes pass `pipeline_mode` per source. Update
      `reconcile_phantom_manifest_rows_all.py` to handle v8 row shape. **SHIPPED 2026-05-12 slot 2 spawned
      `ikenna-v8-mw-instruments-sweep` sub-agent @instruments-service@`e530906`** — ~50 callsites across 9 files.
      Per-source mapping table decided (api_football → BATCH_API_FOOTBALL, transfermarkt → BATCH_TRANSFERMARKT,
      understat → BATCH_UNDERSTAT, soccer_football_info → BATCH_SOCCER_FOOTBALL_INFO, open_meteo → BATCH_OPEN_METEO,
      polymarket gamma → BATCH_POLYMARKET_GAMMA_API, footystats → BATCH_API_FOOTBALL workaround pending enum extension,
      CME options → BATCH_DATABENTO, CeFi options → BATCH_TARDIS, self-published catalog rows →
      BATCH_INSTRUMENTS_SERVICE). New SSOT mapping `_SPORTS_DATA_TYPE_TO_PIPELINE_MODE` in orchestrator. Reconciler
      `reconcile_phantom_manifest_rows_all.py` v8-aware (read-tolerant + write-preserving for all 4 new v8 columns —
      pandas round-trip is naturally column-preserving; added docstring banner + inline comment for future readers, no
      behaviour change needed). QG: identical pre-sweep baseline (zero new errors). Finding filed:
      [`footystats_pipeline_mode_gap_2026_05_12.md`](../archive/issues/footystats_pipeline_mode_gap_2026_05_12.md).
- [x] [AGENT] P0. Phase 4.FEATURES — features-service (post-consolidation) + remaining features-\* repos pass propagated
      `pipeline_mode` + emission-policy hooks. **✅ SHIPPED 2026-05-12 by harsh slot 3** (features-consolidation Phase 7
      already shipped 2026-05-11 per code_freeze freeze-gate item 6; gate was effectively lifted Day 2). 6 callsites in
      2 files cleared: - `features-service@842ff741` (sports/batch_handler 4 callsites lines 474+487+538+547) — adds
      module-level SSOT `_FEATURE_GROUP_TO_PIPELINE_MODE` dict + `_resolve_pipeline_mode(name)` helper. Mapping per slot
      2's Phase 4.INSTRUMENTS `_SPORTS_DATA_TYPE_TO_PIPELINE_MODE` precedent: fixture_features → `BATCH_API_FOOTBALL`,
      odds_features → `BATCH_ODDS_API`, derived_features → `BATCH_FOOTYSTATS`; 14 reference-table TABLE_TO_EXPORT
      catalog exports fall-through to `BATCH_API_FOOTBALL` default. - `features-service@229a0963` (calendar_orchestrator
      2 callsites lines 241+264) — adds module-level SSOT `_FEATURE_GROUP_TO_PIPELINE_MODE` for `time_features` +
      `economic_events`. Both tagged `BATCH_INSTRUMENTS_SERVICE` as a documented closed-set workaround pending UAC enum
      extension (`BATCH_FRED` for economic_events FRED-sourced + `BATCH_FEATURES_CALENDAR_SERVICE` for time_features
      pure-derived) — full finding + operator-decision menu at
      [`issues/features_calendar_pipeline_mode_gap_2026_05_12.md`](issues/features_calendar_pipeline_mode_gap_2026_05_12.md).
      Same logical-unit adjacent fix: `record_empty(...)` at line 264 now also passes `reason="SOURCE_RETURNED_ZERO"` —
      original code would have crashed `LegacyBlankErrorReasonError` at runtime (UTL Wave-2 writegate blank-reason
      guard, hardened 2026-05-07). - PM baseline `pipeline_mode_explicit_baseline.yaml` shrunk **6 → 0** at
      PM@`<this-flip>` (full workspace baseline now empty). STEP 5.70 `check_pipeline_mode_explicit_at_record_calls.py`
      workspace-wide: `OK — 0       baselined occurrences, 0 new occurrences`. Phase 4.DEFAULT-REMOVAL now UNBLOCKED on
      the FEATURES half.
- [x] [AGENT] P0. Phase 4.DEPLOYMENT-API — manifest read endpoints surface v8 columns; data-status drilldown renders
      `service_emission_state` badges (4 states). **SHIPPED 2026-05-12 slot 2 spawned `ikenna-v8-mw-deployment-api-ui`
      sub-agent**: - **deployment-api@`2f833a7`** — `ShardGcsMetadata` extended with 4 v8 fields (`pipeline_mode`,
      `service_emission_state`, `last_emission_decision_at`, `expected_window_completeness_fraction`) all
      `None`-defaulting for forward-compat; new `ServiceEmissionStateLiteral` Literal[...] type mirroring UAC
      `ServiceEmissionStateEnum`; `_gcs_metadata` populator threads v8 columns from manifest-row dict with closed-set
      frozenset guard (off-set values silently drop to `None`) + unparseable-float warning fallback. 6 new tests in
      `TestShardGcsMetadataV8Columns`; 49/49 shard_detail tests pass. - **deployment-ui@`ab06bfe`** — NEW
      `ServiceEmissionStateBadge.tsx` (128 lines) — 4-state colour-coded badge (green / amber / orange / red) + muted
      `—` placeholder for null/undefined; `compact` prop; ARIA `role=status` + accessible-label + closed-set tooltip;
      `serviceEmissionStatePalette` helper for testability. `ShardDetailModal` wired with the new badge + conditional
      `pipeline_mode` label. `ShardDetailGcs` TS interface extended with 4 nullable v8 fields. 9 new vitest tests (4
      states + null + undefined + compact + ARIA + palette-uniqueness); 466/466 full suite passes;
      `VITE_MOCK_API=true npx vite build` clean. - **Forward-compat verified**: pre-v8 manifest rows render muted `—`
      placeholder + omit pipeline_mode label; no regressions; no double-SSOT (closed-set lives in UAC; deployment-api
      uses Literal alias; deployment-ui uses TS union — all three name the same closed set, drift would be
      review-blocking).
- [x] [AGENT] P0. Phase 4.E2E — synthetic-fixture writers pass synthetic-source `pipeline_mode`. **N/A 2026-05-12 slot
      2** — grep-then-read audit (per CLAUDE.md "Grep-Then-Read") found ZERO actual `record_*(` method calls in
      `system-integration-tests/`. The only grep hit (`tests/smoke/test_coverage_matrix_smoke.py:209`) was an
      error-message format-string referencing the method names, not an actual invocation. No work needed.
- [x] [AGENT] P0. Phase 4.PM-SCRIPTS — any `unified-trading-pm/scripts/` Python that calls `record_*` passes explicit
      kwargs. **N/A 2026-05-12 slot 2** — grep-then-read audit found ZERO actual record\_\* method calls in PM scripts.
      The 3 grep hits were: (a) `test_check_removed_symbols.py:45` test-fixture string
      `successor="ManifestWriter.record_captured"` (literal in test data dict); (b)
      `test_check_banned_placeholder_methods.py:158/168/308` synthetic test code defining `def record_empty_for_shard()`
      inside string literals to feed the AST-walk QG check; (c) `check_banned_placeholder_methods.py` docstring +
      error-message strings. None are actual invocations. No work needed.
- [x] [AGENT] P0. Phase 4.GREP-VERIFY — workspace-wide AST-walk (not naive grep). **SHIPPED 2026-05-12 slot 8** at
      `pm@<this-flip-commit>` — new AST-walk QG check
      [`scripts/quality_gates/check_pipeline_mode_explicit_at_record_calls.py`](../../scripts/quality_gates/check_pipeline_mode_explicit_at_record_calls.py)
      (266 lines mirroring `check_banned_placeholder_methods.py` shape) + 11-test unit suite at
      [`scripts/quality_gates/test_check_pipeline_mode_explicit_at_record_calls.py`](../../scripts/quality_gates/test_check_pipeline_mode_explicit_at_record_calls.py) +
      bootstrap baseline at
      [`scripts/quality_gates/pipeline_mode_explicit_baseline.yaml`](../../scripts/quality_gates/pipeline_mode_explicit_baseline.yaml)
      (114 entries: 97 market-tick-data-service `pending_phase_4_mtds` + 6 features-service `pending_phase_4_features` +
      11 unified-trading-library `pending_phase_4_features` Phase 4.DEFAULT-REMOVAL successor). Workspace-wide
      invocation: `OK — 114 baselined occurrence(s); 0 new occurrences`. Whitelist marker
      `# QG-allow: pipeline-mode-not-applicable` supports the rare legitimate exception (e.g. `**kwargs` plumbing).
      Reviewer enforcement: ANY new `record_*(...)` call without explicit `pipeline_mode=` kwarg + not baselined + not
      whitelisted → ERROR, exit 1. Baseline entries get DELETED (not re-statused) as slot 3 ships Phase 4.MTDS sweep +
      features-consolidation ships Phase 4.FEATURES sweep. **2026-05-12 slot 2 audit finding** confirmed: naive grep
      `grep -rln "record_captured" --include="*.py" | xargs grep -L "pipeline_mode="` returned 7 false positives for
      docstring/comment/dict-key/string-literal references; AST-walk authoritatively counts only actual `Call` nodes.
      **✅ Phase 4.GREP-VERIFY P1 SHIPPED 2026-05-12 slot 6 (Harsh) @pm@`93459749`** — QG check wired into the per-repo
      QG body via `scripts/quality-gates-base/base-service.sh` **STEP 5.70** (5.6x range was exhausted — 5.65/5.67/5.69
      in use, 5.66/5.68 reserved — so the ratchet takes 5.70; same baseline-aware shrinking-ratchet shape as STEP 5.67 /
      5.69: `--workspace-root <ws> --scope <repo> --source-dir <pkg>`; baselined occurrences → `log_warn` exit-clean,
      NEW occurrence → `log_fail` + `V++`; checker-absent → skip clean). Every service repo sources `base-service.sh` so
      the ratchet is workspace-wide on next push. Codex doc
      [`codex/06-coding-standards/quality-gates.md`](../../codex/06-coding-standards/quality-gates.md) documents STEP
      5.70 (table row + full How-it-works / Adding-a-new-occurrence / Composes-with sections) + backfills the missing
      STEP 5.69 table row. **TODO Phase 4.GREP-VERIFY P2** [optional, low-pri]: `base-library.sh` does NOT carry STEP
      5.65/5.67/5.69 either (library repos skip the workspace AST-walk ratchets by current precedent) — UTL's 11
      baselined `record_*` callsites are cleared by Phase 4.DEFAULT-REMOVAL regardless + caught by any workspace-wide
      sweep, so per-library enforcement is optional follow-up, not a gap. **NICE-TO-HAVE**: also add STEP 5.70
      invocation to PM's own `quality-gates.sh` (Phase 4.PM-SCRIPTS confirmed N/A — zero real `record_*` calls in PM
      scripts — so it'd be a vacuous pass; defer).
- [x] [AGENT] P0. Phase 4.DEFAULT-REMOVAL — `pipeline_mode=` default removed (explicit-or-fail) from all 6 public
      `record_*` methods + `MANIFEST_SCHEMA_VERSION` bumped `7 → 8` at `manifest_writer.py:131` + codex doc
      `availability-manifest-and-data-status.md` "transitional" prose updated to reflect v8 live. (utl@`547ff3c`
      2026-05-12 — Phase 4.DEFAULT-REMOVAL shipped) **DEFERRED**: 3 v8 emission kwargs (`service_emission_state=` /
      `last_emission_decision_at=` / `expected_window_completeness_fraction=`) still accept `= None` — removing their
      defaults requires a full emission-policy callsite sweep across MTDS + instruments-service + any raw-tick adapters.
      Those callsites were NOT swept in Phase 4 (only `pipeline_mode=` was). Tracked as follow-up deferred item below.
- [ ] [AGENT] P0. Phase 4.DEFAULT-REMOVAL-v8kwargs — **DEFERRED** — remove `= None` defaults from 3 v8 emission kwargs
      (`service_emission_state=` / `last_emission_decision_at=` / `expected_window_completeness_fraction=`) in all
      public `record_*` methods once MTDS + instruments-service + raw-tick adapter callsites are swept to pass these
      explicitly. Predecessor: Phase 4.DEFAULT-REMOVAL (done, utl@`547ff3c`). Blocked by: callsite sweep not yet done
      (emission-policy adapters only partially updated — only writegate slice (b) MDPS POC callsites pass v8 kwargs;
      remaining 8 services pending Phase 6.3-6.9 rollout per writegate plan).
- QG: every affected repo quality-gates.sh clean. **Done-definition**: zero grep hits + every repo's QG green + Phase
  4.DEFAULT-REMOVAL committed.

### Phase 5 — Bundled migration script (May 11-12, SEQUENTIAL after Phase 1+2)

- [x] [AGENT] P0. Phase 5.A — Extend `unified-trading-pm/scripts/migration/gcs_migration_bundle_2026_05_08.py` to
      include the v8 NULL-column backfill in the same parquet walk. Single walk does FIVE migrations: (1)
      `pipeline_mode=` partition insertion, (2) `category=` → `asset_group=` rekey, (3) 5 drift axes (path-prefix /
      instrument*type casing / schema-4 empty / chain-bundle equivalence / hive-vocab), (4) v8 NULL columns via Phase
      2.D helper, (5) cross-asset rescan class-A auto-fixes via Phase 3.D `cross_asset_rescan.py` helper. **SHIPPED
      2026-05-12 slot 2 spawned `ikenna-v8-mw-gcs-migration-bundle` sub-agent @PM@`d9a4fa9b`** — `DriftClass` StrEnum
      extended with `V8_NULL_COLUMNS_MISSING` + `CROSS_ASSET_RESCAN_CLASS_A`; `MigrationMetrics` extended with 4 new
      counters + 2 record*\* methods; new helpers `run_v8_column_backfill` + `run_cross_asset_rescan` +
      `_parse_rescan_output`; new dataclass `CrossAssetRescanResult`; `run_migration` extended with 5 new kwargs
      (`v8_backfill_fn`, `rescan_fn`, `rescan_asset_group`, `skip_v8_backfill`, `skip_rescan`); new CLI flags
      `--skip-v8-backfill` / `--skip-rescan` / `--rescan-asset-group`. Imports UTL Phase 2.D helper via facade (enabled
      by UTL@`d76203a2` Citadel § 7 facade re-export). Rescan invoked via subprocess (process-isolation; Phase 3.D
      helper is a standalone CLI). Defence-in-depth per-VM-shard-isolation guard fires BEFORE UTL helper invocation.
- [x] [AGENT] P0. Phase 5.B — Extend tests in `tests/test_gcs_migration_bundle.py` with v8-column + rescan-auto-fix
      coverage. Maintain dry-run-by-default + per-VM shard isolation guard. **SHIPPED 2026-05-12 slot 2 @PM@`06076383`**
      — 14 new tests (target 8+): 4 v8 backfill + 7 rescan + 3 bundled/skip/isolation. Coverage: legacy v7 parquet → 4
      NULL columns backfilled + non-zero `v8_columns_backfilled_rows`; pre-migrated v8 parquet →
      `v8_columns_already_present_rows == row_count` + zero backfilled; class-A drift case →
      `rescan_class_a_auto_fixes >= 1`; class-C ambiguous case → row in triage JSONL +
      `rescan_class_c_triage_count >= 1`; per-VM-isolation guard fires before UTL helper; dry-run omits `--apply` flag
      from rescan subprocess. All 37 tests pass locally in 16s (23 original + 14 new).
- QG: PM quality-gates.sh clean. **Done-definition**: bundled script + 30+ unit tests covering all 5 migration axes ✅
  (37 tests total post-Phase-5.B; covers 7 axes — original 5 + v8-backfill + rescan-class-A).

### Phase 6 — Bounce-sweep #1 — drain stale VMs (May 12)

- [x] [HUMAN+AGENT] P0. Phase 6.A — Identify all in-flight MTDS / MDPS / instruments / features VMs via
      `gcloud compute instances list --filter="status=RUNNING"`. Cross-reference against `vm_zombie_watchdog.py`
      `VM_PREFIX_TO_BUCKET` registered prefixes. **DONE 2026-05-15**: 1 zombie found — `mtds-gas-fees-20260508-010121`
      (VM_END_DATE=2026-05-08, idle since 2026-05-10). All other registered prefixes: no RUNNING instances.
- [x] [HUMAN+AGENT] P0. Phase 6.B — Drain VMs gracefully — wait for in-flight `record_captured` calls to flush per-VM
      shard, then `gcloud compute instances delete <vm-name> --zone=<zone> --quiet`. Verify manifest consolidator drains
      per-VM shards into canonical before next phase. **DONE 2026-05-15**: `mtds-gas-fees-20260508-010121` stopped via
      `gcloud compute instances stop`. No manifest consolidator drain needed (VM was already idle with no in-flight
      records).
- [x] [AGENT] P0. Phase 6.C — Tarball refresh: `bash deployment-service/scripts/vm/create-code-tarballs.sh --all` to
      capture Phase 4 sweep into all flavors. **Per E3 ratified item.** **DONE 2026-05-15**: 16 tarballs refreshed and
      uploaded to `gs://deployment-scripts-central-element-323112/code/` via `/opt/homebrew/bin/bash` (bash 5.3.9
      required for associative arrays). All 16 service repos confirmed uploaded.
- **Done-definition**: zero RUNNING MTDS / MDPS / instruments / features VMs + manifest consolidator drained + fresh
  tarballs in `gs://deployment-scripts-${PID}/code/`.

### Phase 7 — gcs Phase 3 bundled walk (May 13-15, operator-gated)

- [ ] [HUMAN+AGENT] P0. Phase 7.A — Pre-flight: Phase 0.A artifact still current; Phase 1+2+3+4+5 all shipped + QG
      green; Phase 6 drain confirmed.
- [ ] [HUMAN+AGENT] P0. Phase 7.B — Snapshot critical state: per-bucket
      `gcloud storage cp -r gs://{pid}-raw-tick/_index/ gs://{pid}-pre-migration-snapshot/raw-tick-2026-05-13/_index/`.
      Covers manifest pre-bundled-walk; restore path if any drift class breaks the manifest in-flight.
- [ ] [HUMAN+AGENT] P0. Phase 7.C — Launch migration VM fleet per gcs_migration plan Phase 3 spec — per-bucket
      parallelism (4-8 VMs per bucket); same-region `asia-northeast1-c`; HTTP pool `2*workers`;
      `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=migration-${asset_group}-${slice}-${RUN_TS}`.
- [ ] [HUMAN+AGENT] P0. Phase 7.D — Watch event stream — `MIGRATION_VM_STARTED` + per-parquet progress + `STOPPED`. Per
      CLAUDE.md "no fire-and-forget VM launches" — verify each VM emits STARTED within 60s
  - per-hour progress.
- [ ] [HUMAN+AGENT] P0. Phase 7.E — Manifest consolidator runs continuously during walk; per-VM shards merge via
      last-writer-wins.
- [ ] [HUMAN+AGENT] P0. Phase 7.F — Per-asset-group QA gate: re-run
      `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group <ag>` per asset_group; phantom
      count MUST be 0 (was 354 residual pre-bundle).
- [ ] [HUMAN] P0. Phase 7.G — Operator sign-off per asset_group recorded inline below this todo (5 sub-checkboxes, one
      per asset_group: cefi / defi / tradfi / sports / prediction) once Phase 7.F gate green.
  - [ ] cefi signed off — date: \_**\_ — operator: \_\_**
  - [ ] defi signed off — date: \_**\_ — operator: \_\_**
  - [ ] tradfi signed off — date: \_**\_ — operator: \_\_**
  - [ ] sports signed off — date: \_**\_ — operator: \_\_**
  - [ ] prediction signed off — date: \_**\_ — operator: \_\_**
- **Done-definition**: 5/5 asset_groups signed off + zero phantoms + bundled walk metrics emitted (5 drift-class
  histograms + bytes-moved + wall-clock per asset_group).

### Phase 8 — Cross-asset rescan triage review (May 15)

- [ ] [HUMAN] P0. Phase 8.A — Review class-C triage rows at `gs://{pid}-rescan-triage/{run_id}/triage.jsonl`. Operator
      decides per row: (a) flip the disagreement per disk reality, (b) flip per manifest, (c) leave as-is (legitimate
      dual-shape — currently no known cases).
- [ ] [HUMAN] P0. Phase 8.B — Sign-off section appended to `manifest_cross_asset_rescan_design_2026_05_08.md` § "Rescan
      triage decisions" per its line 67 contract.
- **Done-definition**: every class-C row resolved + sign-off recorded.

### Phase 9 — Bounce-sweep #2 — full MTDS launch (May 16)

- [ ] [AGENT] P0. Phase 9.A — Verify E3 7-item launcher checklist passes for every MTDS adapter (Phase 4 shipped +
      grep-clean):
  1. UTL `manifest_writer.py` `pipeline_mode=` kwarg shipped + default REMOVED post-Phase-4.
  2. Each MTDS adapter explicitly passes `pipeline_mode=PipelineMode.BATCH_<source>`.
  3. Manifest concurrency principle (`_TTL_SECONDS=60` + `_refresh_captured_cache` + `_is_now_captured`) in every MTDS
     launcher.
  4. Per-VM shard isolation envvars (`MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=<unique-tag>`).
  5. Event-stream STARTED + per-instrument progress + STOPPED.
  6. Tarballs refreshed (Phase 6.C).
  7. Watchdog dict registers every prefix used.
- [ ] [HUMAN+AGENT] P0. Phase 9.B — Launch MTDS VM fleet per asset_group. Parallel by zone where dependency-free
      (cefi/defi/tradfi/sports/prediction can run concurrently per per-VM shard isolation rule).
- **Done-definition**: every MTDS VM emits STARTED within 60s + watchdog dict has zero unregistered RUNNING prefixes.

### Phase 10 — MTDS backfill execution (May 16-20, PARALLEL by asset_group)

- [ ] [HUMAN+AGENT] P0. Phase 10.A — Backfill runs to natural completion per asset_group. Manifest concurrency principle
      ensures restart-on-already-captured = no-op.
- [ ] [AGENT] P0. Phase 10.B — Per-asset-group sample-parquet inspection per CLAUDE.md "Plans Run To Actual
      Completion" + "Honest absence vs fake placeholders" — read sample row, assert OHLC populated, assert no
      1440-NaN-bar pattern, assert at least one instrument-shard per (venue, data_type), assert `available_at`
      populated, assert `pipeline_mode` populated, assert `service_emission_state` populated for any row where the
      policy hook fired.
- [ ] [AGENT] P0. Phase 10.C — Coverage % per drilldown level:
      `captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)` matches Phase 0.B PRE-baseline
      within ±0.5pp tolerance per writegate Phase 5 ratchet.
- **Done-definition**: 5/5 asset_groups complete + coverage % matches baseline + zero NaN-placeholder rows in sample
  inspection.

### Phase 11 — MDPS reprocess + features compute (May 20-21, SEQUENTIAL)

- [ ] [HUMAN+AGENT] P0. Phase 11.A — MDPS reprocess against MTDS Phase 10 output. Same-shape v8 manifest reads + writes;
      emission-policy hooks at publish boundary.
- [ ] [HUMAN+AGENT] P0. Phase 11.B — features-service compute against MDPS output. **Cross-plan blocker on
      `features_repo_consolidation_2026_05_08` having merged by May 16.** If consolidation slips, MDPS output reads
      against old per-repo features layout — re-run features compute post-cutover.
- [ ] [AGENT] P0. Phase 11.C — `LookaheadBiasError` strict-mode enforcement at every features compute per
      `available_at_lookahead_bias_completion_2026_05_08`. No warn-mode; raise on any
      `input.available_at > target_ts - horizon` violation.
- **Done-definition**: MDPS + features-service both have post-Phase-11 manifest with `service_emission_state` populated
  for every shard + zero LookaheadBiasError raises.

### Phase 12 — Paper-trade smoke + batch-vs-live recon + ratchet lock-in (May 21-22, PARALLEL)

- [ ] [HUMAN+AGENT] P0. Phase 12.A — Paper-trade smoke per master plan F17. `carry_staked_basis` +
      `leveraged_funding_arb` archetypes run on testnet against post-Phase-11 features. Strategy / risk / position /
      alerting / reconciliation wired identically to live shape.
- [ ] [HUMAN+AGENT] P0. Phase 12.B — Batch-vs-live recon per master plan F18. Run the `batch_live_reconciler`
      (UTL@908b1647) helper; compare batch P&L vs live P&L over the same window; delta < 5bps tolerance.
- [ ] [HUMAN] P0. Phase 12.C — writegate Phase 5 ratchet POST-baseline measurement; `measure-honest-coverage.py` re-runs
      against post-backfill manifest. Lock ratchet in `codex/02-data/honest_coverage_baseline_2026_05.md` with ±0.5pp
      tolerance + monthly cadence + 99% floor.
- **Done-definition**: paper-trade smoke green + recon delta <5bps + ratchet locked.

### Phase 13 — Live cutover (May 23)

- [ ] [HUMAN] P0. Phase 13.A — Operator triggers live wallet enable; carry_staked_basis + leveraged_funding_arb run on
      real wallet for ≥7 continuous days per master plan G23 DART manual-trade gate.
- [ ] [AGENT] P0. Phase 13.B — Banner removal across all `plans/active/*.md` plans bannered Phase 0; status flip on this
      plan from `active` → `complete` once 7-day continuous run validates.
- **Done-definition**: live wallet active + 7-day continuous run started + this plan archived after the 7-day window
  completes.

## Cross-plan coordination banners (Citadel § 4 + CLAUDE.md "Cross-Plan Coordination Banners")

This plan banners every `plans/active/*.md` whose work touches MTDS / MDPS / features / manifest:

```markdown
> **🟡 IN-FLIGHT REFACTOR — manifest v8 FINAL by 2026-05-23 (manifest_schema_final_gate_2026_05_09). Bundled gcs Phase 3
> walk May 13-15. MTDS bounce-sweep launch May 16. NO schema additions accepted 2026-05-09 → 2026-05-23 — defer to
> post-cutover. Reader contract: scan top-of-file before touching manifest / writer / reader / pipeline_mode /
> asset_group hive vocab / emission-policy code paths.**
```

Plans to banner (closed list, sweep on Phase 0 launch):

- `live_pipeline_mtds_mdps_features_2026_05_08.md`
- `gcs_migration_bundle_pipeline_mode_2026_05_08.md`
- `manifest_cross_asset_rescan_design_2026_05_08.md` (sibling design doc; v7 predecessor
  `manifest_v7_schema_migration_design_2026_05_08.md` archived 2026-05-09 as this v8 plan supersedes it)
- `writegate_honest_coverage_endtoend_2026_05_06.md`
- `features_repo_consolidation_2026_05_08.md`
- `available_at_lookahead_bias_completion_2026_05_08.md`
- `hard_schema_enforcement_2026_05_08.md`
- `wave3x_residual_ssots_2026_05_08.md`
- `master_to_live_defi_2026_05_23.md` (master)

## Done-definition (Citadel § 5 + CLAUDE.md "Plans Run To Actual Completion")

This plan is done IFF every bullet below is verified on real GCS infra (not dry-run):

- ✅ UAC + UTL + every consumer repo at v8-final commit shipped + QG green per `repo_gates`.
- ✅ Bundled gcs Phase 3 walk completed across all 5 asset_groups (cefi / defi / tradfi / sports / prediction) —
  per-asset-group sign-off recorded inline at Phase 7.G sub-checkboxes above.
- ✅ Cross-asset rescan triage review complete — every class-C row resolved.
- ✅ MTDS backfill ran to natural completion per asset_group; sample-parquet inspection passes per CLAUDE.md "Honest
  absence vs fake placeholders" rule.
- ✅ MDPS reprocess + features-service compute ran against post-backfill manifest; zero LookaheadBiasError raises.
- ✅ Paper-trade smoke green for both DeFi archetypes; batch-vs-live recon delta <5bps; writegate Phase 5 ratchet
  POST-baseline locked.
- ✅ Live cutover triggered May 23; ≥7-day continuous run validates.

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE):

- Every phase has explicit verification commands run on real infra. No dry-run-only completions.
- Coverage % per asset_group matches Phase 0.B PRE-baseline within ±0.5pp.
- Zero phantom rows post-Phase-7.
- Zero NaN-placeholder rows in MTDS sample inspection (per CLAUDE.md 2026-05-05 incident reference).
- Zero unregistered RUNNING VM prefixes in watchdog dict at any point in Phase 9-10.

**Handoff exception(s)**: none. This plan does not hand off to a downstream plan; the May 23 cutover IS the terminal
milestone. Any item that can't ship by May 23 violates the maximalist directive — escalate to operator immediately, do
not silently defer.

## Codex SSOT updates (Post-Plan-Phase Codex Audit HARD RULE)

Each phase boundary triggers the codex audit per CLAUDE.md "Post-Plan-Phase Codex Audit HARD RULE":

- Phase 1 boundary → UPDATE `codex/04-architecture/service-emission-policy.md` with the 4-state enum + read protocol.
  **✅ SHIPPED — `service-emission-policy.md` LANDED (134 L, stub-appropriate)** (verified slot-6 codex-audit
  2026-05-11).
- Phase 2 boundary → UPDATE `codex/02-data/availability-manifest-and-data-status.md` with v8 columns + reader migration
  window. **Mostly done; ⚠ doc drift** — the v8 columns + reader-migration window are in the doc, but line 261 prose
  says "`MANIFEST_SCHEMA_VERSION = 8` ... in `manifest_writer.py`" while `manifest_writer.py:131` is still `= 7` (the
  embedded code snippet at :265 correctly says `= 7`). See the Phase 2 follow-up todo above. (slot-6 codex-audit
  2026-05-11.)
- Phase 3 boundary → CREATE `codex/02-data/cross-asset-rescan-protocol.md` stub documenting the cross-asset rescan
  workflow (launcher VM + per-VM shard isolation + `VM_APPLY_FLIPS` gate + class-C triage JSONL →
  `gs://{pid}-rescan-triage/`). **❌ NOT YET SHIPPED** — Phase 3 code shipped 2026-05-11 (`deployment-service@19fad8c` +
  `deployment-api@c8a1cd4` + `instruments-service@a264f21`) but the codex stub is absent; OWNER ikenna-slot-6. Per the
  "Post-Plan-Phase Codex Audit" HARD RULE the stub should ride with the Phase-3 ship. (slot-6 codex-audit finding
  2026-05-11; was missing from this section entirely — added by slot 6.)
- Phase 4 boundary → UPDATE `codex/06-coding-standards/quality-gates.md` with the new workspace-wide grep verification
  step.
- Phase 7 boundary → UPDATE `codex/02-data/availability-manifest-and-data-status.md` § "Phantom audit" with bundled-walk
  recipe + 5-drift-axis closed-set fixed.
- Phase 13 boundary → UPDATE `codex/00-SSOT-INDEX.md` registering all v8-related codex docs; CLAUDE.md "Master Plan"
  updated with v8-shipped state.

## Risk register

| Risk                                                               | Probability | Impact                                 | Mitigation                                                                                                                                                        |
| ------------------------------------------------------------------ | ----------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| features-consolidation slips past May 16                           | Medium      | High (blocks Phase 11)                 | Spawn parallel work-split tab focused on consolidation; daily check-in                                                                                            |
| Phase 7 bundled walk wall-clock exceeds 36h                        | Low         | High (compresses MTDS window)          | Phase 0.A calibration; if exceeded, drop drift axes 4+5 (cleanup-only) to post-cutover                                                                            |
| Slice b 4-value enum proves insufficient at consumer-wire-in time  | Low         | Medium (would need v9)                 | 4 values cover all known use cases; if insufficient at Phase 4, defer policy hook to post-cutover (degrades gracefully — emission_state stays None for new shard) |
| Manifest concurrency principle not actually wired in MTDS adapters | Medium      | High (full quota burn on bounce-sweep) | Phase 9.A item #3 explicitly verifies; Phase 6.A pre-drain confirms behavior                                                                                      |
| Operator unavailable for Phase 7.G sign-off                        | Low         | High (blocks phase progression)        | Pre-arrange daily 30-min sign-off windows May 13-15; deputize ops if operator OOO                                                                                 |
| 30-day reader fallback window incurs technical debt past cutover   | Low         | Low                                    | Calendar reminder for 2026-06-23 fallback removal; QG event count check                                                                                           |

## Open items still needing operator input

### A3 → CLOSED 2026-05-09 (FREEZE-CLEAN)

A3 grep sweep complete; results folded into "UAC enums frozen for the window" section above. No additional enums need
freeze-window protection. 5-enum closed set is comprehensive.

### D1 → Databento + Tardis quota burn estimate (operator-fillable; needs Phase 0.A inputs)

The double bounce-sweep (Phase 6 drain May 12 + Phase 9 full launch May 16) re-fetches data ONLY for shards where the
manifest concurrency principle (per-shard freshness check at fetch time, TTL=60s) returns "not-captured". Wired
correctly, the only re-fetch cost is shards captured AFTER the drain and BEFORE the launch — i.e. ~4 days of incremental
coverage that should be near-zero since VMs were drained May 12.

**Estimation methodology** (operator fills in cells from Phase 0.A pre-audit + Databento/Tardis billing):

| Source                                                                | Per-fetch cost (USD)             | Shard scope (cefi+tradfi)                | Days re-fetched (drain→launch window) | Estimated burn (USD)                         |
| --------------------------------------------------------------------- | -------------------------------- | ---------------------------------------- | ------------------------------------- | -------------------------------------------- |
| Databento — TradFi futures + ETFs + options                           | _<operator: $/req from billing>_ | _<operator: shard count from Phase 0.A>_ | 4 (May 12-16)                         | _<calc>_                                     |
| Databento — CeFi historical (Coinbase/Bitfinex/etc.)                  | _<operator>_                     | _<operator>_                             | 4                                     | _<calc>_                                     |
| Tardis — CeFi perp + spot (Bybit/Binance/OKX/etc.)                    | _<operator: $/symbol-day>_       | _<operator: symbol count × 4 days>_      | 4                                     | _<calc>_                                     |
| **Sub-total — incremental re-fetch under correct concurrency wiring** |                                  |                                          |                                       | **_<sum>_**                                  |
| **Worst-case — concurrency NOT wired, full date-range re-fetch**      | _<operator>_                     | _<operator: full backfill window>_       | _N/A — full range_                    | **_<sum × N where N = full-window-days/4>_** |

**Decision the estimate enables:**

- If sub-total < $X (operator's threshold), proceed with Phase 6 drain May 12 as planned.
- If worst-case >> sub-total + concurrency NOT verified, gate Phase 6 drain on Phase D2/D3 verification (manifest
  concurrency principle audit) — see Phase 6.A pre-flight + add an explicit `_TTL_SECONDS=60` +
  `_refresh_captured_cache` + per-VM shard isolation grep verification to Phase 6.A before drain.

**Owner**: operator runs billing query + fills the table; Tab 2 main agent verifies concurrency wiring (D2/D3) per the
next subsection.

### Daily check-in ownership — DECIDED 2026-05-10

Per CLAUDE.md "Daily Work-Split Process" Model B (1-main + dynamic spawned tabs), Ikenna's main orchestrator agent (the
side's Tab 1, no implementation; only direction-setting + ledger-curation + ping triage) owns the daily check-in for
this plan.

**Cadence + scope:**

- **09:00 UTC daily reset** (per CLAUDE.md "Daily reset" recipe): main orchestrator runs the standard `git fetch` +
  `git log --oneline -25 origin/live-defi-rollout` + ping ledger triage, THEN appends a manifest-schema-final-gate
  progress sweep to its summary report.
- **Per-phase boundary check-in** (when a phase flips a checkbox, not on calendar cadence): main orchestrator dispatches
  the cross-plan banner sweep + codex audit per Post-Plan-Phase Codex Audit HARD RULE; spawned implementer tab does the
  actual ship.
- **Operator escalation gates** (mandatory escalation, not autonomous): Phase 0 sign-off, Phase 7.G per-asset-group
  sign-off, Phase 8.B class-C triage decisions, Phase 13.A live cutover. Per the Plans-Run-To-Actual-Completion HARD
  RULE only the explicit hard-stops escalate; implementation defers to spawned tabs.

**What main orchestrator reports to operator daily:**

1. Phase status table (which phases shipped, which are in-flight, which are blocked).
2. Cross-plan handshakes that fired (e.g. features-consolidation Phase 2 GitHub repo creation = operator dependency).
3. CI/QG state on the underlying repos for shipped phases.
4. Open ping-ledger entries blocked >30 min on the main orchestrator's response.
5. Risk-register tripwires (e.g. features-consolidation Phase 11.B blocker if consolidation slips past May 16).

This is the standard Model B dispatcher pattern; codifying here so the responsibility is unambiguous across multi-tab
parallel sessions on this plan.

## DONE-2026-05-12 — slot 6 Phase 2 + Phase 3 ship-out

Slot 6 (Ikenna `tab/ikennaigboaka/6`) shipped both **Phase 2 (UTL v8 ManifestWriter)** + **Phase 3 (cross-asset rescan
launcher + script + watchdog + deployment-api registry)** end-to-end across 4 repos. Phase 1 (UAC v8 schema-bump +
`next_state()` resolver + EXPECTED_KNOWN_SOURCE_GAP) had been shipped by slot 8 earlier the same day (UAC@`7be6bd5`);
slot 6 absorbed via rebase + moved forward.

| Phase | Repo                    | Commit       | Highlights                                                                                                                                                                     |
| ----- | ----------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 2.A   | unified-trading-library | [`0adea1c6`] | `AvailabilityRecord` + 3 new fields + 5 `record_*` methods extended + 12 unit tests.                                                                                           |
| 2.B   | unified-trading-library | [`001e8892`] | `EmissionDecision` extended + `publish_with_policy()` stamps v8 state via Phase 1.B `next_state()` + 6 new tests.                                                              |
| 2.C   | unified-trading-library | [`5f2aacd6`] | `read_availability_index()._backfill()` adds v8 cols as NULL when missing + emits `READER_BACKFILLED_V8_COLUMNS_AS_NULL` event.                                                |
| 2.D   | unified-trading-library | [`bae1ecb9`] | `manifest_migrations/v7_to_v8.py` — per-VM shard isolation guard + `MissingVMShardIsolationError` + `V7ToV8MigrationResult` + 12 unit tests.                                   |
| 3.A/B | deployment-service      | [`19fad8c`]  | `launch-cross-asset-rescan-vm.sh` — singleton-lock, `WORKERS=64`, `HTTP_POOL_SIZE=128`, asia-northeast1-c, `--apply` toggle. Watchdog dict registered (`cross-asset-rescan-`). |
| 3.C   | deployment-api          | [`c8a1cd4`]  | `_SERVICE_LAUNCHER_SCRIPTS["cross-asset-rescan"]` slug for Deploy-Missing UI.                                                                                                  |
| 3.D   | instruments-service     | [`a264f21`]  | `scripts/cross_asset_rescan.py` — 333-line orchestrator on top of existing reconciler + `cross_asset_all` dispatch + triage JSONL + lifecycle events.                          |

**Operator follow-up:**

- Phase 3.B watchdog relaunch (standard
  `gcloud compute instances delete vm-zombie-watchdog-* --zone=asia-northeast1-c --quiet` +
  `bash deployment-service/scripts/vm/launch-vm-zombie-watchdog.sh` to pick up the new prefix) before the first
  cross-asset-rescan VM launch.
- Tarball refresh (`bash deployment-service/scripts/vm/create-code-tarballs.sh --all`) so the rescan VM at boot reads
  the new instruments-service `cross_asset_rescan.py` + the new launcher.
- Phase 8 (cross-asset rescan triage review May 15) consumes the `gs://{pid}-rescan-triage/{run_id}/triage.jsonl` output
  once the first rescan VM run completes.

**Scoreboard — Phase 4-13 status post slot-6 ship:** unchanged; Phase 4 (workspace-wide consumer sweep) still
DEFERRED-AFTER Phase 2 (now unblocked since 2.A's `None` defaults preserve back-compat for the gradual callsite sweep);
Phase 5 (bundled migration script) and Phase 7 (gcs Phase 3 bundled walk) remain operator-gated per the plan body.

### features-consolidation parallel tab — DRAFTED (paste-ready spawn prompt below)

Per the risk register, features-consolidation is the highest-impact medium-prob risk: its plan deadline is 2026-05-13,
and Phase 11.B of THIS plan is blocked until consolidation merges by May 16. Plan status 2026-05-10:

- Phase 0 + 1A + 1B + 5 + 8A + 8B + 9 → ✅ shipped.
- Phase 2 (create features-service repo) → ⏸️ `blocked` (HUMAN-gated GitHub repo creation).
- Phase 3 (8× git subtree merges with history) → ⏸️ `blocked` (depends on Phase 2).
- Phase 4 (fix internal imports + CLI + config — 11 external Python lines + 51 string refs per pre-audit) → 🔵 `todo`.
- Phase 6 (regression parity test) → 🔵 `todo`.
- Phase 7 (archive 8 source repos) → 🔵 `todo`.
- Phase 10 (workspace QG sweep) → 🟡 `helper-shipped`.

Critical path = unblock Phase 2 (operator action) → ship Phase 3 → Phase 4 → Phase 6 → Phase 7. Tight: 6 calendar days
to merge by May 16.

**Tab N — features-consolidation completion (DRAFT for incorporation into today's `work_split_2026_05_10_ikenna.md`).**
Identity: `features-consolidation-tab`. Plan-of-record:
[`features_repo_consolidation_2026_05_08.md`](features_repo_consolidation_2026_05_08.md). Read-first list:
features_repo_consolidation_2026_05_08.md + its preaudit issue doc + this plan
(manifest_schema_final_gate_2026_05_09.md) for the Phase 11.B blocker context. Repos owned (collision boundary): the 8
source `features-*-service` repos + the new `features-service` repo + UAC + UTL + deployment-{api,ui,service} +
e2e-testing. Estimated AI-budget: ~3-4 AI-days (mostly Phase 3 subtree merges + Phase 4 11-line import sweep, both
highly parallelizable). Sub-agent fan-out: 8 parallel sub-agents for Phase 3 (one per source repo), 1 main for Phase 4 +
6 + 7. Collision risk: HIGH with any agent touching the soon-to-be-archived 8 features-\* repos; banner those repos with
`🟡 IN-FLIGHT REFACTOR — features-consolidation merging into features-service; archive imminent` per CLAUDE.md
"Cross-Plan Coordination Banners" rule.

**Done-definition:**

- features-service repo created on GitHub + workspace cloned + Phase 2 checkbox flipped `[x]`.
- 8× git subtree merge complete with full history preserved + Phase 3 checkbox `[x]`.
- 11 external Python imports rewritten + 51 string refs case-by-case fixed + workspace-wide grep for
  `features_<family>_service` returns zero hits in non-archived repos + Phase 4 checkbox `[x]`.
- Regression parity test green: same MTDS-input → same features-output before vs after consolidation, hash-equal output
  parquets per family + Phase 6 checkbox `[x]`.
- 8 source repos archived + GitHub UI shows `archived` label + Phase 7 checkbox `[x]`.
- features_repo_consolidation_2026_05_08 plan flips status `active` → `complete` + spawns banner-removal in all plans
  bannered Phase 0 of this plan.
- **Hard deadline: 2026-05-16 EOD UTC** (Phase 11.B of manifest_schema_final_gate gating).

**Spawn prompt (paste-ready, per CLAUDE.md "Spawn prompt template (Model B)"):**

```text
You are the features-consolidation tab — a sub-agent spawned by Ikenna's main orchestrator agent (Tab 1,
a separate Claude Code session on the SAME PC, sharing the SAME .git/ + working tree as you).

BEFORE doing anything else, read in order:
  1. unified-trading-pm/plans/active/work_split_2026_05_10_ikenna.md § "Bootstrap — read first if you're a
     spawned tab" (if exists; otherwise see CLAUDE.md "Daily Work-Split Process").
  2. unified-trading-pm/cursor-configs/CLAUDE.md — workspace coding standards + "Daily Work-Split Process"
     section.
  3. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md — sub-agent inheritance.
  4. unified-trading-pm/plans/active/features_repo_consolidation_2026_05_08.md — your plan-of-record.
  5. unified-trading-pm/plans/archive/issues/features_repo_consolidation_preaudit_2026_05_08.md — the 1286-
     line audit artifact with the 11 external import lines + 51 string refs + 6 lift candidates.
  6. unified-trading-pm/plans/active/manifest_schema_final_gate_2026_05_09.md § "Phase 11" — the May-16
     hard-deadline blocker that depends on you finishing.

Your agent-tag for ping-ledger entries: features-consolidation-tab.
Your tab number: TBD (operator assigns when adding to today's work-split).

ORCHESTRATION RULES (per CLAUDE.md "Daily Work-Split Process"):
  1. Shared working tree — no `git pull` needed between tabs; pre-commit check
     (git status + git diff --cached --stat NO PATH ARG) mandatory before EVERY commit.
     Use `git add -p` for shared files; never `git add -A` / `git add <whole-shared-file>`.
  2. Plan-doc Q&A flow — write blockers into features_repo_consolidation_2026_05_08.md's
     `## Open questions` (status 🟡 BLOCKED), append ping in _agent_pings.md, continue with what you CAN do.
  3. Conditional push — per shippable unit: commit locally, fetch + check incoming, zero incoming → push,
     any incoming → flag + escalate.
  4. Plan-flip in same logical unit as code — checkbox flip + `<repo>@<sha>` evidence stamped in body.
  5. Foot-gun #4 (prek auto-revert race) — bundle Edit→add→commit→push into ONE Bash call when working
     on plan files in PM repo.

YOUR TASK:

Critical-path: ship the features-consolidation completion by 2026-05-16 EOD UTC. This is a HARD blocker
for manifest_schema_final_gate Phase 11.B (May 23 cutover gating). Phases 2, 3, 4, 6, 7 remaining; 0 + 1A +
1B + 5 + 8A + 8B + 9 + 10 already shipped.

Sequence:

1. **Phase 2 — features-service repo creation (HUMAN-GATED).** Operator creates the GitHub repo
   `IggyIkenna/features-service` + workspace clones it as a sibling. Wait for operator confirmation in
   ping ledger; until then, focus on Phase 4 prep work that doesn't need the repo (audit the 11 external
   imports + 51 string refs against current sibling state to confirm pre-audit is still accurate).

2. **Phase 3 — 8× git subtree merge with history preserved (PARALLEL FAN-OUT).** Once Phase 2 unblocks,
   spawn 8 parallel sub-agents (one per source repo), each running:
     `cd features-service && git subtree merge --squash=false ../features-<family>-service main`
   Conflict resolution: each sub-agent owns its source-repo's sub-package directory (`features_service/<family>/`);
   no cross-family conflicts expected since each family lands in a distinct sub-package. Collision boundary:
   any sub-agent that touches another family's directory — STOP, ping main, surface the conflict.

3. **Phase 4 — fix imports + CLI + config (SEQUENTIAL after Phase 3).** Per pre-audit:
   - 11 external Python import lines (lift to `features_service.<family>.*` namespace).
   - 51 string references (test params + openapi catalogues + .gitignore) — case-by-case manual fixup.
   - Lift 6 cross-family helpers to UTL per Phase 5 already shipped — verify the lift is consumed
     correctly.
   - Workspace-wide grep verification: `grep -rln "features_<family>_service" --include="*.py" --include="*.yaml"
     --include="*.json" --include="*.md"` returns zero hits in non-archived repos.

4. **Phase 6 — regression parity test (SEQUENTIAL after Phase 4).** Pick a representative MTDS-input
   parquet per family; compute the family's features pre-consolidation (against the soon-archived source
   repo) + post-consolidation (against features-service) + hash-compare output parquets. Hash-equal =
   parity green. Any divergence = regression; investigate before proceeding.

5. **Phase 7 — archive the 8 source repos (HUMAN+AGENT).** Once Phase 6 green, operator archives the 8
   `features-*-service` repos via GitHub UI + workspace removes the sibling clones + workspace-manifest
   updated. Update `unified-trading-pm/plans/PLAN_FORMAT.md` + relevant codex docs to remove pointers to
   the archived repos.

6. **Banner sweep + plan flip.** Once Phase 7 done, status of features_repo_consolidation_2026_05_08 flips
   `active` → `complete`. Banner-removal sweep across plans bannered Phase 0 of manifest_schema_final_gate
   (the 10 plans listed there). Status flip on this tab in today's work-split.

REPORT-BACK: per shippable unit, code commit + plan-flip commit, conditional push. Final: append a
"DONE-2026-05-<DD>" block at the bottom of features_repo_consolidation_2026_05_08.md body listing every
code + plan-flip commit sha across the 8 source repos + features-service + UAC + UTL + deployment-\* +
e2e-testing. EOD-audit (per CLAUDE.md "Capture Discoveries As Plan Todos Immediately" § "End-of-cycle audit
clause"): every deferral in your final summary MUST already be a `- [ ]` plan todo or a `**DEFERRED**`
annotation in plans/active/. Run grep checks per the EOD-audit recipe. Then go quiet — don't pick up new
work autonomously. If consolidation slips past May 16 EOD UTC, escalate to operator IMMEDIATELY (chat
ping + main-orchestrator alert) — Phase 11.B of manifest_schema_final_gate is blocked + the May 23 cutover
schedule compresses by 1 day per slip-day.
```

The tab is ready to drop into today's `work_split_2026_05_10_ikenna.md` once operator decides the working model (Model A
6-tab vs Model B dynamic spawned). Recommend Model B for today since the consolidation has HUMAN-gated Phase 2
unblocking + 8 parallel Phase 3 sub-agents — dynamic spawning fits the shape better than fixed thematic tabs.

## DONE-2026-05-12 — slot 2 `ikenna-v8-manifestwriter-tab` — Phase 2 P2 + Phase 4 partial + Phase 5.A+B

Tab: `ikenna-v8-manifestwriter-tab` (slot 2 worktree at `.tabs/2/`). Session scope: re-task from writegate slice (c)
Phase 6.2 close-out (prior session) → manifest_schema_final_gate Phase 2 (UTL v8 ManifestWriter) per operator re-task
brief. Pre-audit discovery: RE-TASK BRIEF #2 primary scope (Step 0 Q2 Bug 1 + Step 1-4 Phase 2.A/B/C/D) ALL already
shipped (slot 6 finished today). Surfaced finding to operator → operator directed "do all these: Phase 2 P2 + Phase 4 +
Phase 5.A/B".

### Commits

| Commit                        | Repo                           | Summary                                                                                                                |
| ----------------------------- | ------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| `PM@59d761a4`                 | unified-trading-pm             | Phase 2 P2 — MANIFEST_SCHEMA_VERSION decision (option b) + codex softened + Phase 4.DEFAULT-REMOVAL extended           |
| `MDPS@a3c7198`                | market-data-processing-service | Phase 4.MDPS — 22 callsites + `resolve_pipeline_mode_from_source` helper                                               |
| `instruments-service@e530906` | instruments-service            | Phase 4.INSTRUMENTS — ~50 callsites + per-source map + v8-aware reconciler                                             |
| `PM@237d00b7`                 | unified-trading-pm             | Phase 4.MTDS — 🟡 finding doc (5 Q's pending operator triage)                                                          |
| `PM@a5e5aa4d`                 | unified-trading-pm             | Finding doc: VIX 15m Yahoo/Barchart `PipelineMode` enum gap                                                            |
| `PM@6ede1e01`                 | unified-trading-pm             | Finding doc: footystats `PipelineMode` enum gap                                                                        |
| `PM@42348eba`                 | unified-trading-pm             | Phase 4 partial plan-flip — MDPS [x] + INSTRUMENTS [x] + small-repos N/A + MTDS blocked + GREP-VERIFY AST-walk upgrade |
| `deployment-api@2f833a7`      | deployment-api                 | Phase 4.DEPLOYMENT-API — 4 v8 fields in `ShardGcsMetadata` + 6 tests                                                   |
| `deployment-ui@ab06bfe`       | deployment-ui                  | Phase 4.UI — `ServiceEmissionStateBadge` + 9 vitest                                                                    |
| `PM@d9a4fa9b`                 | unified-trading-pm             | Phase 5.A — gcs_migration_bundle v8 backfill + cross-asset-rescan class-A                                              |
| `PM@06076383`                 | unified-trading-pm             | Phase 5.B — 14 new tests (37 total)                                                                                    |
| `UTL@d76203a2`                | unified-trading-library        | UTL `manifest_migrations` facade re-exports (enables Phase 5.A imports per Citadel § 7)                                |
| `PM@<this-flip>`              | unified-trading-pm             | Plan-flip + DONE block                                                                                                 |

### What shipped (operationally)

- **Phase 2 P2** — closed-set design call (option b): codex prose softened to match `manifest_writer.py:131` constant
  value `MANIFEST_SCHEMA_VERSION = 7` (transitional); bump-to-8 + remove all 4 transitional `None` defaults consolidated
  into Phase 4.DEFAULT-REMOVAL.
- **Phase 4.MDPS** — pipeline_mode propagated through `write_candle_parquet` / `candle_write_mixin` / `live_workers` /
  `batch_workers` / `orchestration_writer` / `live_aggregator` / `io/writer`. Helper `resolve_pipeline_mode_from_source`
  parses `pipeline_mode=<value>` hive partition segment from GCS blob path; legacy pre-v8 paths fall back to
  `BATCH_DATABENTO`. 22 callsites in 16 files (8 source + 2 scripts + 6 tests).
- **Phase 4.INSTRUMENTS** — per-source pipeline_mode mapping table decided (api_football → BATCH_API_FOOTBALL,
  transfermarkt → BATCH_TRANSFERMARKT, etc.); reconciler v8-aware (pandas read-tolerant + write-preserving — no
  behaviour change needed). ~50 callsites in 9 files.
- **Phase 4.DEPLOYMENT-API + UI** — `ShardGcsMetadata` response surfaces 4 v8 fields; `ServiceEmissionStateBadge`
  4-state colour-coded badge wired into `ShardDetailModal`. 15 new tests (6 Python + 9 TS); 466/466 UI suite passes.
- **Phase 5.A** — single-walk migration script extended with 2 new drift axes (`V8_NULL_COLUMNS_MISSING` +
  `CROSS_ASSET_RESCAN_CLASS_A`); 4 new metrics counters; 3 new CLI flags; UTL facade enables clean import.
- **Phase 5.B** — 14 new tests covering v8 backfill + rescan auto-fix + per-VM isolation defence-in-depth.

### Findings filed (3 — pending operator triage)

| Finding doc                                                                                                                                    | Scope                                                                                                                                                                                                    | Severity |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| [`mtds_pipeline_mode_sweep_ambiguities_2026_05_12.md`](issues/mtds_pipeline_mode_sweep_ambiguities_2026_05_12.md)                              | 102 MTDS callsites blocked on 5 design ambiguities (DefiManifestRecorder legacy `add()` path + 3 DeFi PipelineMode enum gaps + orchestrator dispatch strategy + reconciler preservation + test fixtures) | P0       |
| [`mdps_vix_15m_yahoo_barchart_pipeline_mode_gap_2026_05_12.md`](../archive/issues/mdps_vix_15m_yahoo_barchart_pipeline_mode_gap_2026_05_12.md) | VIX 15m route (Yahoo / Barchart) lacks `BATCH_YAHOO` / `BATCH_BARCHART` enum values; workaround `BATCH_DATABENTO` per SOURCE_PRIORITY top-entry                                                          | P1       |
| [`footystats_pipeline_mode_gap_2026_05_12.md`](../archive/issues/footystats_pipeline_mode_gap_2026_05_12.md)                                   | footystats source lacks `BATCH_FOOTYSTATS` enum value; workaround `BATCH_API_FOOTBALL` stamped on instruments-service catalog rows                                                                       | P1       |

**Operator triage decision needed** (consolidated): extend UAC `PipelineMode` enum + `SOURCE_PRIORITY` to add 6 missing
values (`BATCH_YAHOO` / `BATCH_BARCHART` / `BATCH_FOOTYSTATS` / `BATCH_HYPERLIQUID_REST` / `BATCH_PYTH_HERMES` /
`BATCH_CHAINLINK`), OR ratify the workaround pattern (stamp closest SOURCE_PRIORITY top-entry value when no exact
match). Plus: migrate `DefiManifestRecorder.record_captured` from legacy `ManifestWriter.add()` path to v8
`record_captured()` path (no-double-SSOT per workspace contract).

### Deferred work after 2026-05-12 ikenna-v8-manifestwriter-tab session

| Phase / item                                  | Status as of 2026-05-12                                       | Successor / blocker                                                                                                                            |
| --------------------------------------------- | ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 2 P2 — MANIFEST_SCHEMA_VERSION decision | `done` (PM@`59d761a4`)                                        | —                                                                                                                                              |
| Phase 4.MDPS                                  | `done` (MDPS@`a3c7198`)                                       | —                                                                                                                                              |
| Phase 4.INSTRUMENTS                           | `done` (instruments-service@`e530906`)                        | —                                                                                                                                              |
| Phase 4.DEPLOYMENT-API + UI                   | `done` (deployment-api@`2f833a7` + deployment-ui@`ab06bfe`)   | —                                                                                                                                              |
| Phase 4.E2E + Phase 4.PM-SCRIPTS              | `done` (N/A — no real callsites; verified via grep-then-read) | —                                                                                                                                              |
| Phase 4.MTDS                                  | `blocked`                                                     | Operator triage of 3 findings (6 PipelineMode enum gaps + DefiManifestRecorder add()-path)                                                     |
| Phase 4.FEATURES                              | `deferred-after-may-16`                                       | features-consolidation merge gate per plan body                                                                                                |
| Phase 4.GREP-VERIFY                           | `todo` (`- [ ]`)                                              | NEW QG STEP `check_pipeline_mode_explicit_at_record_calls.py` AST-walk; ~80-100 lines mirroring `check_banned_placeholder_methods.py` shape    |
| Phase 4.DEFAULT-REMOVAL                       | `blocked-after-mtds`                                          | Blocked on Phase 4.MTDS unblock; once 4.MTDS + 4.FEATURES land, removes 4 None defaults + bumps MANIFEST_SCHEMA_VERSION 7→8 + reconciles codex |
| Phase 5.A                                     | `done` (PM@`d9a4fa9b`)                                        | —                                                                                                                                              |
| Phase 5.B                                     | `done` (PM@`06076383`)                                        | —                                                                                                                                              |

Cross-plan items NOT addressed this session (still open in their own plans-of-record):

- **Per-service slice (c) Phase 6.3-6.9** — writegate plan body: features-volatility / cross-instrument / ml-training /
  ml-inference / strategy / execution / position-balance / risk / instruments-service rollouts.
- **Phase 6-8 (manifest_schema_final_gate)** — HUMAN+AGENT operational steps (drain stale VMs / tarball refresh / gcs
  Phase 3 walk / class-C triage). Out of agent scope; operator-runnable per plan body.

### EOD-audit (per CLAUDE.md "Capture Discoveries As Plan Todos Immediately" § "End-of-cycle audit clause")

Every deferral in this DONE block is grep-verified as a `- [ ]` plan todo or `**DEFERRED**`/`**BLOCKED**` annotation in
`plans/active/`:

- "Phase 4.MTDS blocked" — annotated in plan body Phase 4.MTDS section +
  `plans/active/issues/mtds_pipeline_mode_sweep_ambiguities_2026_05_12.md`.
- "Phase 4.FEATURES gated on May-16" — explicit annotation in plan body Phase 4.FEATURES.
- "Phase 4.GREP-VERIFY AST-walk upgrade" — explicit `- [ ]` in plan body with implementation site
  (`unified-trading-pm/scripts/quality_gates/check_pipeline_mode_explicit_at_record_calls.py`) named.
- "Phase 4.DEFAULT-REMOVAL blocked on MTDS" — annotated in plan body + extended scope (4 None defaults + bump
  MANIFEST_SCHEMA_VERSION + reconcile codex) per Phase 2 P2 resolution.
- "Per-service slice (c) Phase 6.3-6.9" — open in `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 6.3-6.9.

No deferral lives only in chat or in the commit message. Three findings filed for operator triage.

### Foreign findings flagged (NOT my code, NOT blocking)

- Per-tree prettier auto-reflow (foot-gun #4) — ~130 codex docs + plans show line-wrapping diffs vs HEAD after sub-agent
  rebases. Files have IDENTICAL semantic content; only whitespace differs. Stashed under
  `slot-2: foreign-prettier-reflows-foot-gun-4` to keep the slot 2 working tree clean for plan-flip commits. Foreign
  agents will reconcile in their own commits per CLAUDE.md "Two teammates × multiple parallel agents" rule.

---

## DONE-2026-05-12 — slot 8 Phase 4.GREP-VERIFY closure + Phase 4.FEATURES pre-audit

Slot 8 (`tab/ikennaigboaka/8`, agent-tag `ikenna-manifest-phase3-tab`) shipped two consumer-sweep items today inside the
manifest_schema_final_gate Phase 4 cluster:

| Phase               | Repo               | Commit       | Highlights                                                                                                                                                                                                                                                                                            |
| ------------------- | ------------------ | ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 4.GREP-VERIFY | unified-trading-pm | [`4159b7ae`] | NEW AST-walk QG check `scripts/quality_gates/check_pipeline_mode_explicit_at_record_calls.py` (266 LOC) + 11-test unit suite + 706-LOC bootstrap baseline. Detects every `record_*(...)` call missing explicit `pipeline_mode=` kwarg. Workspace invocation: `OK — 114 baselined; 0 new occurrences`. |
| Phase 4.FEATURES P0 | unified-trading-pm | [`c1414ed7`] | Pre-audit enumerated 6 features-service callsites concentrated in 2 files (calendar orchestrator + sports batch handler). Pipeline-mode mapping per existing UAC SOURCE_PRIORITY documented inline. Mechanical sweep ~30min once features-consolidation merge lifts the gate (target 2026-05-16).     |

**Phase 4 cluster scoreboard post-slot-8 ship:**

| Sub-phase               | Status as of 2026-05-12                                                                            | Owner / Successor / Blocker                                                                                                  |
| ----------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Phase 4.MDPS            | ✅ shipped slot 2 (`mdps@a3c7198`)                                                                 | Done                                                                                                                         |
| Phase 4.INSTRUMENTS     | ✅ shipped slot 2 (`instruments-service@e530906`)                                                  | Done                                                                                                                         |
| Phase 4.DEPLOYMENT-API  | ✅ shipped slot 2 (`deployment-api@2f833a7` + `deployment-ui@ab06bfe`)                             | Done                                                                                                                         |
| Phase 4.E2E             | ✅ N/A (slot 2 audit; zero actual record\_\* calls)                                                | Done                                                                                                                         |
| Phase 4.PM-SCRIPTS      | ✅ N/A (slot 2 audit; zero actual record\_\* calls)                                                | Done                                                                                                                         |
| Phase 4.GREP-VERIFY     | ✅ checker shipped slot 8 (PM@`4159b7ae`) + P1 QG-wiring shipped slot 6 (PM@`93459749`, STEP 5.70) | Done — ratchet live in every service repo's QG; see DONE blocks below                                                        |
| Phase 4.FEATURES        | ⚪ pre-audit shipped slot 8 today; sweep deferred-after-may-16                                     | Successor: features-consolidation merge gate; 6 callsites enumerated above                                                   |
| Phase 4.MTDS            | 🟡 pre-audit shipped slot 2 (26 files / 102 callsites); sweep BLOCKED on operator triage of Q1-Q5  | Successor: slot 3 (code_freeze Phase 1.E audit) per `plans/active/issues/mtds_pipeline_mode_sweep_ambiguities_2026_05_12.md` |
| Phase 4.DEFAULT-REMOVAL | ⚪ blocked transitively on Phase 4.MTDS                                                            | Successor: same as Phase 4.MTDS                                                                                              |

**Phase 4.GREP-VERIFY ratchet** is now LIVE **and wired into every service repo's QG** — `Phase 4.GREP-VERIFY P1`
shipped 2026-05-12 slot 6 (Harsh) @pm@`93459749`: `scripts/quality-gates-base/base-service.sh` **STEP 5.70** invokes
`check_pipeline_mode_explicit_at_record_calls.py` scoped to the calling repo (every service repo `source`s
`base-service.sh`, so the per-PR ratchet is workspace-wide on next push). Any new `record_*(...)` call missing explicit
`pipeline_mode=` kwarg + not in `pipeline_mode_explicit_baseline.yaml` + no `# QG-allow: pipeline-mode-not-applicable`
inline marker → `log_fail` + non-zero exit, blocking the PR. Baseline entries get DELETED (not re-statused) as Phase
4.MTDS sweep + Phase 4.FEATURES sweep + Phase 4.DEFAULT-REMOVAL land. Codex doc
`codex/06-coding-standards/quality-gates.md` documents STEP 5.70 in full. P2 (library-repo enforcement / PM-repo
invocation) noted as optional follow-up in the Phase 4.GREP-VERIFY checkbox above — not a gap (library callsites are
cleared by Phase 4.DEFAULT-REMOVAL + caught by workspace-wide sweep; PM has zero real `record_*` calls).

## Decision log

- **2026-05-09** — Plan created from `plans/questions/backfill_manifest_schema_freeze_gate_2026_05_08.md` decision-log
  ratifications: E2=(a), A1=NO, A1-sub=ratify-now, B2=workspace-wide, B3=bundled-into-Phase-3, E1=v8-final,
  E3=ratified-as-listed-7-item-checklist. Operator direction verbatim: _"i want the best manifest before may 23rd not a
  partial one all the items done"_ + _"yeah do all this v8 should not be deferred should be done"_.
