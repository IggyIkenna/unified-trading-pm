---
doc_type: issue
title: MTDS DefiCatalogReader still reads the dead static-snapshot path — mirrors CeFi BUG #4 / TradFi G4 FIX
summary: |
  Discovered while shipping `is_catalogue_completion_2d-009` (P3 delete-orphaned-static-snapshot-catalogue-path).
  The IS CatalogueBuilder writer is orphan CODE (no CLI/TF/test caller — audit-confirmed), so nobody writes to
  `reference_data/instruments/asset_group=defi/written_at=<ISO>/all.parquet`. But `MTDS/engine/defi_catalog_reader.py`
  still probes exactly that prefix (`_CATALOG_PREFIX = "reference_data/instruments/asset_group=defi/"`) and is
  registered live at `orchestrator/__init__.py:456`. If the prefix is empty (or stale) the reader returns None
  from `_load_latest_catalog()` and the MTDS DeFi enum silently falls back to the UAC static seed — the SAME
  silent-fallback failure mode the CeFi reader had before its 2026-06-22 fix (BUG #4) and the TradFi reader
  before its 2026-06-25 fix (G4). Both peers were migrated to read the lifecycle-regen output
  `{env}/catalog.parquet` (freshly written by `build_instrument_catalogue.py` daily).
status: resolved
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, mtds, catalog-reader, silent-fallback, honest-coverage, data-correctness]
related:
  [
    /plans/archive/2026_07/is_catalogue_completion_2d_2026_07_06.md,
    ../cefi_hl_aster_batch_data_gaps_2026_06_22.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-06
last_updated: 2026-07-06
source:
  - instruments-service audit finding (unified-trading-pm/plans/audit/results/instruments_master_audit_2026_06_08.md §
    "Dead duplicate catalogue path")
  - live trace during task is_catalogue_completion_2d-009 (P3 delete-orphan)
assigned_vm: planning
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: data_engineering
drift_direction: advance-code
execution_scope: orchestrator-agent
parent_epic: mtds_mdps_master
depends_on: []
resolved_by: market-tick-data-service@f4dab8f9 (reader migration) + @af1800f7 (test port)
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# MTDS DefiCatalogReader silent-fallback — mirrors CeFi BUG #4 / TradFi G4 FIX

> **Status-flip note (2026-07-10)**: both todos confirmed `[x]` with cited evidence (reader migration + test port, QG
> green). Flipped `status: open` → `resolved`.

## What I found

While shipping `is_catalogue_completion_2d-009` (delete the orphan
`instruments_service/reference_data/catalogue/catalogue_builder.py` + `orchestrator.refresh_catalogue`), I traced every
consumer of the static-snapshot GCS path `reference_data/instruments/asset_group=<ag>/written_at=<ISO>/all.parquet` that
`CatalogueBuilder.write_to_gcs` used to write.

- **CeFi**: `market-tick-data-service/market_tick_data_service/engine/cefi_catalog_reader.py` was MIGRATED 2026-06-22
  (BUG #4 fix, `plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md`). Reader now probes
  `{prod,staging,dev}/catalog.parquet` — the lifecycle-regen output written by
  `instruments-service/scripts/build_instrument_catalogue.py`.
- **TradFi**: `tradfi_catalog_reader.py` was MIGRATED 2026-06-25 (G4 FIX). Same probe candidates, same lifecycle-regen
  SSOT.
- **DeFi**: `defi_catalog_reader.py` is **NOT migrated** — it still hardcodes
  `_CATALOG_PREFIX = "reference_data/instruments/asset_group=defi/"` (line 36) and probes for `all.parquet` under that
  prefix (`_download_latest_catalog`, lines 207–246). It is registered live at `orchestrator/__init__.py:456`:
  ```python
  register_catalog_reader("defi", DefiCatalogReader(get_storage_client(), _defi_instr_bucket))
  ```

Since the IS-side `refresh_catalogue`/`CatalogueBuilder` writer has NO CLI/TF/scheduler caller (audit-confirmed
"parallel old+new, no CLI/TF/test caller" — instruments_master_audit § "Dead duplicate catalogue path", and the IS CLI
`main.py` never invokes `refresh_catalogue`), the static-snapshot DeFi path either doesn't exist in the bucket or is
stale from a long-past ad-hoc run.

## Why it matters

This is the **exact same silent-fallback failure mode** BUG #4 documented for CeFi:

> BUG #4 (2026-06-22) — the prior prefix `reference_data/instruments/asset_group=cefi/` did NOT exist in the bucket (it
> was the OTHER, never-populated CatalogueBuilder output), so `_load_latest_catalog()` returned None and the
> orchestrator silently fell back to the UAC static ~9-coin seed, capping the cefi attempt universe at 9.

For DeFi, the same mechanism means:

1. `DefiCatalogReader._load_latest_catalog()` returns None (empty prefix) OR loads stale data (last ad-hoc
   `refresh_catalogue` run — possibly months old).
2. MTDS DeFi sentinel fan-out / expected-universe enumeration silently falls back to the UAC static DeFi seed (a small
   hardcoded venue list, NOT the ~7,279-row lifecycle catalogue currently sitting fresh at
   `gs://instruments-store-defi-prd-<pid>/prod/catalog.parquet`, per `is_catalogue_completion_2d` Progress Log
   2026-07-06 B1-FLIPPED entry).
3. Honest-coverage denominator for DeFi is **understated** — the expected-universe never converts to fully-captured
   because the reader is looking at the wrong path. This is a **RED data-correctness finding under the "no silent
   placeholders / correctness is the heartbeat" hard-rule**.

Reader-side is thin — the migration pattern is already documented in the CeFi/TradFi peers (`cefi_catalog_reader.py`,
`tradfi_catalog_reader.py`). Roughly:

- Replace `_CATALOG_PREFIX = "reference_data/instruments/asset_group=defi/"` with
  `_CATALOG_OBJECT_CANDIDATES = ("prod/catalog.parquet", "staging/catalog.parquet", "dev/catalog.parquet")`.
- Replace `_download_latest_catalog()`'s list-blobs-and-take-lexmax logic with a candidate-probe: first-that-exists wins
  (same as `cefi_catalog_reader._download_latest_catalog`).
- Update docstring header (drop the "written by CatalogueBuilder" line — CatalogueBuilder is deleted by task
  `is_catalogue_completion_2d-009` shipping alongside this issue doc).
- Column-name fallbacks: the peers accept BOTH the canonical `build_instrument_catalogue.py` schema (dropped `_datetime`
  suffix, adds `mvp`) AND the legacy CatalogueBuilder schema (`available_from_datetime`, etc.). The DeFi catalogue
  schema is currently `{instrument_id, instrument_type, venue, chain, ..., available_from, available_to, ..., mvp}` per
  the `is_catalogue_completion_2d` Progress Log defi sample (17 cols) — verify the reader's column-access uses the
  canonical names, add fallbacks if needed.
- Existing tests: `market-tick-data-service/tests/unit/test_catalogue_filter.py` mocks
  `storage.download_bytes.return_value = _catalogue_bytes()` — the migration probably needs the probe-order stub updated
  to the new candidate list.

## Recommended decision

**Do the migration**: `defi_catalog_reader.py` → `prod/catalog.parquet` reads. This is a straight port of the pattern
already applied to CeFi + TradFi. Small change (a P2 refactor at ~0.08 calibrated AI-days) with meaningful
data-correctness impact (fixes silent-fallback for DeFi denominator).

## Actionable todos

- [x] ✅ [MTDS] P2. **Migrate `market_tick_data_service/engine/defi_catalog_reader.py` to read the lifecycle-regen
      catalogue** — replace the `_CATALOG_PREFIX = "reference_data/instruments/asset_group=defi/"` static-snapshot probe
      with the `_CATALOG_OBJECT_CANDIDATES = ("prod/catalog.parquet", "staging/catalog.parquet", "dev/catalog.parquet")`
      first-that-exists probe used by `cefi_catalog_reader.py` and `tradfi_catalog_reader.py`. Update the file docstring
      (drop "written by instruments-service CatalogueBuilder" — the writer was deleted). Handle column-name fallbacks
      between the canonical `build_instrument_catalogue.py` schema (`available_from`, `available_to`, `mvp`) and the
      legacy CatalogueBuilder schema (`available_from_datetime`, `available_to_datetime`, `status`). Regression test:
      verify DeFi expected-universe honest-coverage numerator/denominator no longer stalls at the UAC static seed size.
      (repo: market-tick-data-service) — market-tick-data-service@f4dab8f9 — replaced the list-blobs + lex-max scan with
      the first-that-exists probe of `_CATALOG_OBJECT_CANDIDATES`; canonical `instrument_id` column used verbatim when
      present (falls back to `_canonical_defi_id` derivation); prefers explicit `chain` column with venue-chain
      extraction as fallback; canonical `available_from`/`available_to` accepted first, legacy `*_datetime` names as
      fallback; added `tests/unit/engine/test_defi_catalog_reader.py` with 6 regression tests pinning the canonical
      `prod/catalog.parquet` probe (regression guard mirroring CeFi BUG #4 / TradFi G4 pattern), canonical + legacy
      column filtering, `instrument_id` verbatim usage, missing-catalogue empty-iterator behaviour, and per-process
      caching. Full `bash scripts/quality-gates.sh` exit 0.
- [x] ✅ [MTDS] P3. **Update `tests/unit/test_catalogue_filter.py`** — the current test mocks the
      list-blobs-and-take-lexmax flow; port the mock to the first-that-exists probe (mirror the CeFi/TradFi reader
      tests). (repo: market-tick-data-service) — market-tick-data-service@af1800f7 — replaced the `MagicMock` +
      `download_bytes.return_value` stub with a `_Storage` class that only returns bytes for the canonical
      `_CATALOGUE_BLOB` (`prod/catalog.parquet`) and tracks `keys_probed`; every test now pins that the canonical blob
      is probed (regression guard mirroring the CeFi BUG #4 / TradFi G4 pattern). Added `_MissingCatalogueStorage` for
      the absent-catalogue case + explicit-empty assertions for the no-project-id early-return path. 6/6 tests green
      (`.venv/bin/python -m pytest tests/unit/test_catalogue_filter.py -v`); repo `quality-gates.sh` exit 0.
