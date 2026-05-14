---
title: Solana DeFi venue naming reconciliation — canonicalize to PROTOCOL-SOLANA pattern
type: plan
status: active
created: 2026-05-14
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

# Solana DeFi venue naming reconciliation — Plan D

Successor to the Solana coverage gap issue doc
(`plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md`). The operator decision on canonical naming
is now **settled** (see § "Decision" below). This plan migrates legacy bare-name manifest rows
(`MARINADE`, `DRIFT`, `JITO`, `ORCA`, `RAYDIUM`, `KAMINO`, `SOLEND`, `MARGINFI`) to the canonical
`{PROTOCOL}-SOLANA` naming convention.

**Issue doc**: `plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md`

---

## Decision — canonical naming is `{PROTOCOL}-SOLANA`

**Settled by code, not by operator vote.** Two sources confirm:

1. **UAC `_defi.py:687`** (comment): `venue: Canonical venue name (e.g. "AAVEV3-ETHEREUM", "DRIFT-SOLANA")`
2. **`instruments-service/instruments_service/reference_data/adapters/defi/drift.py:69`**:
   `return f"DRIFT-{self._chain}"` — all Solana adapters already produce `PROTOCOL-SOLANA` venue names.

**Conclusion**: bare-name rows (`MARINADE`, `DRIFT`, etc.) are legacy artifacts from an earlier adapter
version that predated the `{PROTOCOL}-{CHAIN}` pattern. The `{PROTOCOL}-SOLANA` rows pre-populated by the
enumerator are correct canonical targets.

---

## Scope of migration

### What exists (per 2026-05-13 audit)

| Bare-name venue | Captured rows | Data_types | Status |
| --------------- | ------------- | ---------- | ------ |
| MARINADE        | 30            | `lst_rates` | Legacy captured — real data under wrong name |
| DRIFT           | 0 of 29       | —          | Empty; adapter already writes to DRIFT-SOLANA |
| JITO            | 0 of 30       | —          | Empty; adapter already writes to JITO-SOLANA |
| RAYDIUM         | 31            | `dex_pools` | Legacy captured — real data under wrong name |
| ORCA            | 31            | `dex_pools` | Legacy captured — real data under wrong name |
| KAMINO          | 32            | `lending_indices` | Legacy captured — 50% coverage |
| SOLEND          | 29            | `lending_indices` | Legacy captured — real data |
| MARGINFI        | 16            | `lending_indices` | Legacy captured — partial coverage |

The `{PROTOCOL}-SOLANA` rows (0% captured, `EXPECTED_PRE_VENUE_LAUNCH`) are waiting for the adapter to
write to them — they already exist in the manifest under correct naming.

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

- [ ] [SCRIPT] P0. Create `instruments-service/scripts/migrate_solana_bare_name_venues.py` — reads defi
      manifest rows where `venue ∈ {MARINADE, RAYDIUM, ORCA, KAMINO, SOLEND, MARGINFI}` and
      `capture_status = captured`, copies parquet to `{PROTOCOL}-SOLANA` path, writes updated manifest
      rows, marks bare-name rows as `attempted_failed` (phantom). Script structure:
      1. Load manifest for `asset_group=defi`
      2. Filter: `venue IN BARE_NAMES AND capture_status = 'captured'`
      3. For each row: `new_venue = f"{row.venue}-SOLANA"`; read parquet at old path; rewrite with
         `venue` column set to `new_venue`; upload to canonical path (via `resolve_bucket_name`);
         update manifest row to `captured` at `new_venue`; mark old row `attempted_failed`
      4. Category B (DRIFT, JITO): just mark bare-name rows `attempted_failed` (no data to move)
      5. Per-VM shard isolation: `VM_NAME` + `MANIFEST_PER_VM_SHARDS=true`
      6. `--dry-run` flag (default): print what would change; `--apply` to execute
      Script location: `instruments-service/scripts/migrate_solana_bare_name_venues.py`
      Uses `resolve_bucket_name` per bucket-name SSOT — no hardcoded bucket strings.

- [ ] [SCRIPT] P0. Write unit tests at
      `instruments-service/tests/unit/scripts/test_migrate_solana_bare_name_venues.py`:
      - Mock manifest with MARINADE captured rows → verify MARINADE-SOLANA rows created, old rows marked
        attempted_failed
      - Mock DRIFT empty rows → verify just phantom-marked (no parquet copy)
      - Dry-run mode: verify no writes
      - `MANIFEST_PER_VM_SHARDS=true` assertion

## Phase 2 — QG + dry-run verification

- [ ] [SCRIPT] P0. Run `cd instruments-service && bash scripts/quality-gates.sh` — confirm ruff +
      basedpyright green on migration script.

- [ ] [SCRIPT] P0. Run migration script in dry-run mode (local, DEPLOYMENT_ENV=prod):
      `CLOUD_PROVIDER=gcp DEPLOYMENT_ENV=prod WORKSPACE_ROOT=... python scripts/migrate_solana_bare_name_venues.py --dry-run`
      Verify:
      - Category A venues: X parquet paths would be copied; X manifest rows would be updated
      - Category B venues (DRIFT, JITO): X manifest rows would be phantom-marked
      - No errors

## Phase 3 — VM migration + verification

- [ ] [SCRIPT] P1. **OPERATOR-AUTHORIZED**: Launch migration VM (asia-northeast1-c, same region as
      manifest). Command:
      ```bash
      bash deployment-service/scripts/vm/launch-manifest-migration-vm.sh \
          --script migrate_solana_bare_name_venues \
          --apply \
          --asset-group defi
      ```
      Expected: Category A parquets migrated; Category B rows phantom-marked. Verify via event stream
      (STARTED + progress + STOPPED events at `gs://{pid}-events/events/instruments-service/...`).

- [ ] [SCRIPT] P1. Post-migration verification:
      - `grep MARINADE manifest | capture_status = captured` → count should be 0 (migrated)
      - `grep MARINADE-SOLANA manifest | capture_status = captured` → count should be 30+
      - Sample read: load one MARINADE-SOLANA parquet → verify `venue = "MARINADE-SOLANA"` column

## Phase 4 — Codex update

- [ ] [SCRIPT] P1. Update `codex/04-architecture/solana-defi-coverage.md` § "Venue naming convention":
      add note that canonical naming is `{PROTOCOL}-SOLANA` per UAC `_defi.py:687` + adapter code;
      bare-name rows are legacy migration artifacts (this plan resolves them).

---

## Temporary states + their canonical follow-up plans

- **Before Phase 3**: bare-name captured rows still exist under `MARINADE`/`RAYDIUM`/`ORCA`/`KAMINO`/`SOLEND`/`MARGINFI`. MTDS may read the wrong venue name for these rows. Duration: until VM migration runs (Phase 3).
- **After Phase 3**: `{PROTOCOL}-SOLANA` rows contain all data. Adapters will continue writing to `{PROTOCOL}-SOLANA` names on next run.

No downstream plan needed — this plan is self-contained.

---

## Full-execution criterion

- ✅ Migration script ships + QG passes.
  - **What ran**: `bash scripts/quality-gates.sh` in instruments-service.
  - **Verification**: 0 ruff/basedpyright errors on migration script.

- ✅ VM migration completes (Phase 3) — OPERATOR-AUTHORIZED.
  - **What ran**: `launch-manifest-migration-vm.sh --apply` on GCE asia-northeast1-c.
  - **Verification**: MARINADE/RAYDIUM/ORCA captured rows = 0; MARINADE-SOLANA/RAYDIUM-SOLANA/ORCA-SOLANA captured rows ≥ 30/31/31; sample parquet `venue` column = `{PROTOCOL}-SOLANA`.

**Handoff exception**: Phase 3 VM migration deferred to next authorized backfill slot. Phase 1-2 ship now.
