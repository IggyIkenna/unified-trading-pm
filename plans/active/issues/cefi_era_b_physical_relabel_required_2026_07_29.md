---
doc_type: issue
title:
  "cefi Era-B (options_chain/futures_chain data_type) requires a physical GCS relabel, mirroring the sports E3+E4 / defi
  G4 precedent — not a manifest-only fix"
summary: >-
  cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md's cefi CF-1/CF-4/CF-5/Era-B todo left an open question on
  whether cefi's ~491,146 `data_type=options_chain/futures_chain` manifest rows are a manifest-`_index`-only artifact or
  reflect the actual on-disk GCS object path. Answered by reading the emission chain (deribit_options_chain_handler →
  partitioned_writer's `_resolve_partition_data_type()` → UAC's `build_cefi_partition_path()`): one variable flows
  unchanged from capture to the physical path, so the manifest faithfully mirrors what's on disk — a genuine physical
  relabel is required (chain distinction moves to `instrument_type`, `data_type` becomes `trades`), same shape as the
  already-shipped sports E3+E4 and defi G4 fleet migrations. This is VM-scale heavy I/O, out of a single dispatched
  todo's safe scope — this issue doc scopes the dedicated follow-up.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [cefi, era-b, manifest, canonicalisation, gcs-relabel, backfill, cf-audit]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/active/issues/cross_cutting_manifest_canonicalisation_findings_2026_07_11.md,
    /plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md,
  ]
created: 2026-07-29
priority: P1
parent_epic: manifest_master
source: ["cross_cutting_satellite_ao_dispatch_batch1-016, slot 4, 2026-07-29"]
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
---

# cefi Era-B requires a physical GCS relabel, not a manifest-only fix

## What I found

`cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s cefi CF-audit todo (line 428) left one open design question
before a fix could be built: is the CF-audit's `data_type=options_chain/futures_chain` count (491,146 rows, "Era-B" in
this codebase's convention) a manifest-`_index`-only labeling artifact, or does it reflect the actual on-disk GCS object
path?

Traced the emission chain in `market-tick-data-service`:

1. **Capture time**: `cli/handlers/deribit_options_chain_handler.py` stamps `data_type="options_chain"` on every
   captured row (the literal value later present in both the manifest and the write call).
2. **The writer path**: `engine/orchestrator/partitioned_writer.py`'s `_resolve_partition_data_type()`
   (`symbol_rules.py`'s `_MERGED_DATA_TYPE_MAP = {"futures_chain": "options_chain"}`) takes that same value and passes
   it straight into `_build_partition_path_for_asset_group()`, which for cefi calls UAC's
   `build_cefi_partition_path(data_type=...)`.
3. **UAC's own docstring** (`unified_api_contracts/canonical/partition_paths.py`) confirms the emitted path literally
   embeds a `data_type={DT}/` path segment.

One variable flows unchanged from capture → writer → the physical GCS object path. The manifest is not a stale index
artifact — it faithfully mirrors what is physically on disk today.

**Sister-AG precedent confirms the same shape elsewhere**:
`master_data_canonicalisation_migration_catalogue_2026_06_07.md`'s G4-apply note states defi's "Era-B relabel rides the
migrator's final step" (a genuine physical on-disk move, part of the same VM-scale fleet run already executed for sports
— "E3+E4 fleet 2026-07-12" — and defi — "G4 apply 2026-07-12"). By contrast, cefi's own G4-apply line in that same doc
reports only "already canonical on-disk" with **no** Era-B relabel step recorded — cefi never got the physical fix
sports/defi received, which matches today's live audit (491,146 residual Era-B rows). tradfi's own Era-B rows were
separately adjudicated a non-issue (bundle-grain design, not a relabel candidate) — tradfi is not a "same fix already
done" precedent here, only sports/defi are.

`migrate_cefi_flat_to_v9_canonical.py`'s `_ONDISK_DATA_TYPE_MERGE`/`_CHAIN_BUNDLE_DTYPES` (built for the v6→v9
physical-path migration) already mirror the live writer's on-disk convention for chain-type path segments — further
confirming the path genuinely carries `options_chain`/`futures_chain` today, not `trades`.

**Reversibility check (fresh, 2026-07-29)**: `gcs_bucket_soft_delete_retention_seconds()` against
`market-data-tick-cefi-prd-central-element-323112` returns **604800 seconds (exactly 7 days)** — qualifies (`>= 604800`)
for the safe-idempotent reversibility carve-out under
`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a path (c), though it sits exactly at the
boundary, not comfortably above it. This means a same-run fresh check is required before every apply (do not reuse this
session's number without re-verifying), but the apply todo below does not need an `[OPERATOR]` tag given a passing fresh
check.

## Why it matters

CF-1/CF-3/CF-4/CF-5 are already GREEN + live-verified for cefi (slot 14, 2026-07-29). Era-B is the one remaining CF gap
keeping cefi out of parity with prediction/sports/tradfi/defi's already-confirmed manifest-correctness state. This is
genuine production data-correctness debt (data-pipeline correctness is the workspace heartbeat), not cosmetic — a
manifest reader trusting `data_type=options_chain/futures_chain` as a real trades-adjacent value (rather than the
canonical `data_type=trades` + `instrument_type=options_chain/futures_chain` split already used by the other 4 AGs) will
misclassify ~491k rows.

## Recommended decision

Build the physical relabel mirroring the already-shipped sports E3+E4 / defi G4 fleet pattern (server-side GCS copy,
verify-before-delete, manifest `_index` rewritten in lockstep), following the same dry-run/snapshot/pause-cron/
apply/resume-cron protocol this workspace already uses for cross-AG manifest backfills (per the sports CF-8 regression
HARD constraint). No design ambiguity remains — proceed directly to implementation.

## Todos

- [ ] [DATA] P1. Design + build the physical relabel migration for cefi's Era-B rows: server-side GCS copy
      (`gcs_copy_object`, never delete the source until the copy is verified) moving each affected object from its
      `data_type=options_chain|futures_chain` path segment to `data_type=trades`, threading the chain distinction into
      `instrument_type` on the copied object, mirroring the already-shipped sports E3+E4 / defi G4 fleet scripts'
      structure (reuse, don't reinvent). Update the manifest `_index` rows in lockstep. Unit-test the path-rewrite +
      `instrument_type` derivation logic. (repo: market-tick-data-service)
- [ ] [DATA] P1. Dry-run against a bounded date-range/venue sample of the ~491,146 affected rows; hand-verify a handful
      of previewed relabels before any live write. (repo: market-tick-data-service)
- [ ] [DATA] P1. Snapshot the cefi canonical manifest index and pause its consolidator cron (per the sports CF-8
      regression HARD constraint — snapshot-first, verify `PAUSED` state; the 2026-07-28 operator ruling means no
      scheduling round-trip is needed pre-live-trading). (repo: market-tick-data-service)
- [ ] [DATA] P1. Apply the relabel for real across the full 491,146-row Era-B corpus on a SPOT VM (heavy-I/O HARD RULE —
      this is far past the few-hundred-object local-execution ceiling). Re-verify
      `gcs_bucket_soft_delete_retention_seconds() >= 604800` fresh in this same run before any delete (do not reuse this
      doc's 2026-07-29 number) — if it no longer qualifies, escalate to `[OPERATOR]` instead of proceeding. Verify each
      copy (row/byte-count match) before deleting the source object. (repo: market-tick-data-service)
- [ ] [DATA] P1. Re-run `cf_manifest_audit.py` to confirm Era-B GREEN (0 residual `options_chain`/`futures_chain`
      `data_type` rows on captured cefi rows) and resume the consolidator cron; verify `MANIFEST_COLUMN_FILL_REGRESSION`
      did not trip and total row count is unchanged. Record before/after evidence in this issue doc's Progress Log.
      (repo: market-tick-data-service)
- [ ] [VERIFY] P2. Once Era-B is confirmed GREEN, add a short confirming note to
      `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s cefi CF todo (already flipped `[x]` on the
      documented-residual clause) citing this issue doc's resolution, and flip this issue doc's `status` to `resolved`.
      (repo: unified-trading-pm)

## Progress Log

- 2026-07-29 (data_engineering slot-4): filed. Answered the open manifest-vs-physical question left by slot 14's
  in-progress work on the parent todo (physical relabel confirmed required, full code-path evidence above). No
  production writes made by this touch — investigation + scoping only.
