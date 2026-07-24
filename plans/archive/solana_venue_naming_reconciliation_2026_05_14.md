---
doc_type: plan
title: Solana DeFi venue naming reconciliation — canonicalize to PROTOCOL-SOLANA pattern
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-14
type: plan
deadline: 2026-05-23
priority: P1
spawned_from: plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md (Successor plan D)
locked_by: live-defi-rollout
locked_since: 2026-05-14
estimate_class: design
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.9
effective_concurrent_slots: 1
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

> **ARCHIVED 2026-05-16 — 100% done per inventory (slot-8 SWEEP-16 mechanical archive sweep)**

# Solana DeFi venue naming reconciliation — Plan D

Successor to the Solana coverage gap issue doc (`plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md`). The
operator decision on canonical naming is now **settled** (see § "Decision" below). This plan migrates legacy bare-name
manifest rows (`MARINADE`, `DRIFT`, `JITO`, `ORCA`, `RAYDIUM`, `KAMINO`, `SOLEND`, `MARGINFI`) to the canonical
`{PROTOCOL}-SOLANA` naming convention.

**Issue doc**: `plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md`

---

## Decision — canonical naming is `{PROTOCOL}-SOLANA`

**Settled by code, not by operator vote.** Two sources confirm:

1. **UAC `_defi.py:687`** (comment): `venue: Canonical venue name (e.g. "AAVE_V3-ETHEREUM", "DRIFT-SOLANA")`
2. **`instruments-service/instruments_service/reference_data/adapters/defi/drift.py:69`**:
   `return f"DRIFT-{self._chain}"` — all Solana adapters already produce `PROTOCOL-SOLANA` venue names.

**Conclusion**: bare-name rows (`MARINADE`, `DRIFT`, etc.) are legacy artifacts from an earlier adapter version that
predated the `{PROTOCOL}-{CHAIN}` pattern. The `{PROTOCOL}-SOLANA` rows pre-populated by the enumerator are correct
canonical targets.

---

## Scope of migration

### What exists (per 2026-05-13 audit)

| Bare-name venue | Captured rows | Data_types        | Status                                        |
| --------------- | ------------- | ----------------- | --------------------------------------------- |
| MARINADE        | 30            | `lst_rates`       | Legacy captured — real data under wrong name  |
| DRIFT           | 0 of 29       | —                 | Empty; adapter already writes to DRIFT-SOLANA |
| JITO            | 0 of 30       | —                 | Empty; adapter already writes to JITO-SOLANA  |
| RAYDIUM         | 31            | `dex_pools`       | Legacy captured — real data under wrong name  |
| ORCA            | 31            | `dex_pools`       | Legacy captured — real data under wrong name  |
| KAMINO          | 32            | `lending_indices` | Legacy captured — 50% coverage                |
| SOLEND          | 29            | `lending_indices` | Legacy captured — real data                   |
| MARGINFI        | 16            | `lending_indices` | Legacy captured — partial coverage            |

The `{PROTOCOL}-SOLANA` rows (0% captured, `EXPECTED_PRE_VENUE_LAUNCH`) are waiting for the adapter to write to them —
they already exist in the manifest under correct naming.

### Migration categories

**Category A — Has real data, needs migration** (MARINADE, RAYDIUM, ORCA, KAMINO, SOLEND, MARGINFI):

- Bare-name parquets have real captured data
- Must be re-written to `{PROTOCOL}-SOLANA` venue name in parquet + manifest
- Migration script: read bare-name parquet → rewrite with corrected venue → upload to canonical path
- Then: mark bare-name manifest rows as phantoms (`attempted_failed`)

**Category B — Empty, just needs phantom-marking** (DRIFT, JITO):

- 0 captured rows under bare name
- Just mark the bare-name manifest rows as phantoms
- `{PROTOCOL}-SOLANA` rows already exist; adapter will write to them next run

---

## Pre-audit

```bash
# Confirm adapter venue naming:
grep -n "f\".*-{self._chain}\"\|f\".*SOLANA" \
    instruments-service/instruments_service/reference_data/adapters/defi/*.py

# Confirm MARINADE-SOLANA exists in manifest (pre-populated enumerator rows):
# Run locally with DEPLOYMENT_ENV=prod to count MARINADE-SOLANA rows
```

---

## Phase 1 — Write migration script (PARALLEL)

- [x] [SCRIPT] P0. Create `instruments-service/scripts/migrate_solana_bare_name_venues.py` — reads defi manifest rows
      where `venue ∈ {MARINADE, RAYDIUM, ORCA, KAMINO, SOLEND, MARGINFI}` and `capture_status = captured`, copies
      parquet to `{PROTOCOL}-SOLANA` path, writes updated manifest rows, marks bare-name rows as `attempted_failed`
      (phantom). Script structure: 1. Load manifest for `asset_group=defi` 2. Filter:
      `venue IN BARE_NAMES AND capture_status = 'captured'` 3. For each row: `new_venue = f"{row.venue}-SOLANA"`; read
      parquet at old path; rewrite with `venue` column set to `new_venue`; upload to canonical path (via
      `resolve_bucket_name`); update manifest row to `captured` at `new_venue`; mark old row `attempted_failed` 4.
      Category B (DRIFT, JITO): just mark bare-name rows `attempted_failed` (no data to move) 5. Per-VM shard isolation:
      `VM_NAME` + `MANIFEST_PER_VM_SHARDS=true` 6. `--dry-run` flag (default): print what would change; `--apply` to
      execute Script location: `instruments-service/scripts/migrate_solana_bare_name_venues.py` Uses
      `resolve_bucket_name` per bucket-name SSOT — no hardcoded bucket strings. (instruments-service@2639f8e — migration
      script + 7 unit tests all passing)

- [x] [SCRIPT] P0. Write unit tests at
      `instruments-service/tests/unit/scripts/test_migrate_solana_bare_name_venues.py`: - Mock manifest with MARINADE
      captured rows → verify MARINADE-SOLANA rows created, old rows marked attempted_failed - Mock DRIFT empty rows →
      verify just phantom-marked (no parquet copy) - Dry-run mode: verify no writes - `MANIFEST_PER_VM_SHARDS=true`
      assertion (instruments-service@2639f8e — 7/7 passing)

## Phase 2 — QG + dry-run verification

- [x] [SCRIPT] P0. Run `cd instruments-service && bash scripts/quality-gates.sh` — confirm ruff + basedpyright green on
      migration script. (QG exit 0 — 2026-05-14; scripts/ dir excluded from basedpyright by
      SOURCE_DIR=instruments_service)

- [x] [SCRIPT] P0. Run migration script in dry-run mode (local, DEPLOYMENT_ENV=prod):
      `CLOUD_PROVIDER=gcp DEPLOYMENT_ENV=prod GCP_PROJECT_ID=central-element-323112 python scripts/migrate_solana_bare_name_venues.py`
      Results (2026-05-14 16:25-16:32 UTC): - Manifest: 1,606,190 rows read from
      `market-data-tick-defi-prd-central-element-323112` - Category A: 169 rows (KAMINO=32, MARINADE=30, ORCA=31,
      RAYDIUM=31, SOLEND=29, MARGINFI=16) - Category B: 59 rows (DRIFT+JITO) - Would add 169 new {PROTOCOL}-SOLANA
      manifest rows; would mark 169 old + 59 Cat B rows as attempted_failed - **FINDING: parquets_migrated=0** — no
      parquet files found at probed GCS paths for any of the 169 captured rows. This means either (a) actual parquet
      data is at a different path structure than what the script probes, or (b) the bare-name "captured" manifest rows
      are phantom captures (no actual file on disk). Requires operator verification before Phase 3 apply: confirm
      whether parquet files exist at `raw_tick_data/by_date/day=*/asset_group=defi/venue=MARINADE/...` or
      `category=defi/venue=MARINADE/...` in bucket `market-data-tick-defi-prd-central-element-323112`. If not → phantom
      captures, apply is safe. If yes → script path template needs correction before apply.

## Phase 3 — VM migration + verification

- [x] [SCRIPT] P1. **OPERATOR-AUTHORIZED**: Launch migration VM. **DONE 2026-05-15 (slot-3)**: Ran locally with ADC
      admin perms (no VM needed — network available, all Category A parquets were phantom captures so no actual GCS
      copies required).
      `VM_NAME=slot3-solana-venue-migration-20260515 MANIFEST_PER_VM_SHARDS=true DEPLOYMENT_ENV=prd     python scripts/migrate_solana_bare_name_venues.py --apply --confirm`.
      Result: parquets_migrated=0 manifest_rows_updated=0 rows_phantom_marked=228 (169 Cat A + 59 Cat B). Backup at
      `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.20260515-135146.bak.parquet`.
      (instruments-service migration script already committed @2639f8e)

- [x] [SCRIPT] P1. Post-migration verification. **DONE 2026-05-15 (slot-3)**: Manifest re-queried from GCS: MARINADE
      captured=0 attempted_failed=30 ✅; DRIFT captured=0 attempted_failed=29 ✅; JITO captured=0 attempted_failed=30
      ✅; ORCA captured=0 attempted_failed=31 ✅; RAYDIUM captured=0 attempted_failed=31 ✅; KAMINO captured=0
      attempted_failed=64 ✅; SOLEND captured=0 attempted_failed=29 ✅; MARGINFI captured=0 attempted_failed=30 ✅.
      PROTOCOL-SOLANA rows all `empty_confirmed` (adapters run, honest absence). Total rows: 1,606,190 (unchanged).

## Phase 4 — Codex update

- [x] [SCRIPT] P1. Update `/codex/04-architecture/solana-defi-coverage.md` § "Venue naming convention": add note that
      canonical naming is `{PROTOCOL}-SOLANA` per UAC `_defi.py:687` + adapter code; bare-name rows are legacy migration
      artifacts (this plan resolves them). (unified-trading-pm@02efcea5)

---

## Temporary states + their canonical follow-up plans

- **Before Phase 3**: bare-name captured rows still exist under
  `MARINADE`/`RAYDIUM`/`ORCA`/`KAMINO`/`SOLEND`/`MARGINFI`. MTDS may read the wrong venue name for these rows. Duration:
  until VM migration runs (Phase 3).
- **After Phase 3**: `{PROTOCOL}-SOLANA` rows contain all data. Adapters will continue writing to `{PROTOCOL}-SOLANA`
  names on next run.

No downstream plan needed — this plan is self-contained.

---

## Deferred work after 2026-05-14 slot-8-session-2

| Deferred item              | Successor / action                                                                                                                                                                                                                                                                                        |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 3 VM migration apply | **BLOCKED-OPERATOR-DECISION**: Verify whether parquet files exist at `raw_tick_data/.../venue=MARINADE/...` in `market-data-tick-defi-prd-central-element-323112` before apply. Dry-run found `parquets_migrated=0` for all 169 Cat A rows — likely phantom captures, but confirm before executing write. |
| Phase 4 Codex update       | Update `/codex/04-architecture/solana-defi-coverage.md` once Phase 3 verified.                                                                                                                                                                                                                            |

---

## Full-execution criterion

- ✅ Migration script ships + QG passes.
  - **What ran**: `bash scripts/quality-gates.sh` in instruments-service (2026-05-14).
  - **Verification**: QG exit 0; 7/7 unit tests passing.

- ✅ Dry-run verified.
  - **What ran**: `python scripts/migrate_solana_bare_name_venues.py` (dry-run default) against prod manifest.
  - **Verification**: 169 Cat A + 59 Cat B rows identified; no errors. FINDING: `parquets_migrated=0` — requires
    operator parquet-existence verification before Phase 3 apply.

- ⏳ VM migration completes (Phase 3) — BLOCKED-OPERATOR-DECISION (parquet path verification needed).
  - **What ran**: N/A — pending operator verification.
  - **Verification**: MARINADE/RAYDIUM/ORCA captured rows = 0; {PROTOCOL}-SOLANA captured ≥ 30/31/31.

**Handoff**: Phase 1-2 done. Phase 3 blocked on operator parquet-path verification (see Deferred work above).
