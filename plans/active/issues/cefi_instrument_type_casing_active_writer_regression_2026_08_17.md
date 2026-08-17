---
doc_type: issue
title: CeFi instrument_type casing residual is an ACTIVE writer regression, not stale debt
summary: >-
  Re-verifying the instrument_type casing residual cited in cefi_consolidated_closeout_2026_07_18.md
  line 523 (2,982 rows) found it has grown 13x to 39,286 — an active writer regression, not stale
  historical debt. Traces a plausible root cause in market-tick-data-service's partitioned_writer.py
  (GCS-path lowercasing leaking into the manifest row-key), fixes 3 safety defects in the existing
  --apply script, and finds the apply itself is genuinely VM-scale (166k+ per-VM shard objects, a
  29.9M-row consolidated index) rather than safe to run on the shared host.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [cefi, instrument-type, casing, manifest, writer-regression]
related:
  [
    /plans/archive/2026_08/cefi_casing_residual_ao_dispatch_2026_08_16.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md,
  ]
created: 2026-08-17
author: slot-14 (data_engineering)
parent_epic: cefi_master
source: [/plans/archive/2026_08/cefi_casing_residual_ao_dispatch_2026_08_16.md]
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by:
resolved_by:
drift_direction: advance-code
depends_on: []
---

## What I found

Dispatched to re-verify the `instrument_type` casing residual cited in
`cefi_consolidated_closeout_2026_07_18.md` line 523 (2,982 non-canonical rows, "dominated by
already-ruled lowercase-casing variants") before running the `--apply` casing fix. A fresh live
re-count against the current cefi manifest (independently measured twice: once by a research
fork, once by myself, both via
`market-tick-data-service/scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py`,
run 2026-08-17 05:44 UTC) found the residual has **grown 13x, not shrunk**:

- Manifest size: 29,938,146 rows (was 8,880,557 in July — 3.4x growth from real capture volume).
- Genuine casing-variant residual (lowercase of a canonical `InstrumentType`): **39,286** rows
  (`perpetual`=38,083, `future`=1,191, `spot_pair`=12) — up from the cited 2,982.
- **NOT part of the casing residual, and NOT a new finding**: `instrument_type` also carries
  `futures_chain`=173,043 and `options_chain`=36,329 rows (up from 307/1,100 in the 2026-07-27
  snapshots below). This was already investigated and RESOLVED 2026-07-27 as an intentional,
  workspace-wide "bundled chain shard" writer convention, not a bug — see
  `issues/cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md`
  Finding 1. Correctly excluded from this doc's casing-fix scope; noted here only so the raw
  counts in the Evidence section below aren't mistaken for a new open defect. Also present and
  likewise excluded: `None`=162,190, blank=157,337, `index`=3,910 (unclassified, not casing
  variants).

**Plausible root cause of the active regrowth** (repo: market-tick-data-service — flagged as a
candidate, not confirmed with the same rigor as the 2026-07-27 doc's RESOLVED sections; a fix
should re-verify against the actual single-instrument `record_captured` call sites before
shipping):
`market_tick_data_service/engine/orchestrator/partitioned_writer.py::_resolve_instrument_type_column`
(line 401-414) deliberately lowercases the `instrument_type` column
(`df["instrument_type"].astype(str).str.lower()`) so it matches the GCS hive-partition-path
convention (`CHAIN_INSTRUMENT_TYPES`/`SINGLE_INSTRUMENT_TYPES` are lowercase by convention for
`build_*_partition_path`). The sibling function
`market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py:565` does the identical
lowercase-for-path-building. This is correct/by-design for path construction. The open question:
whether that same lowercased column also feeds the manifest `record_captured` row-key for
SINGLE-instrument (non-bundle) shards (`manifest_finalize.py`'s `itype_key`, e.g. line 264/488) —
the 2026-07-27 doc's RESOLVED trace only examined the BUNDLE-shard write path
(`_write_bundle_shard_row`) for the `futures_chain`/`options_chain` question, not this one. If
confirmed, the fix is to re-map to canonical uppercase specifically at the manifest-write call
site, keeping the lowercase value only for `build_*_partition_path`. Whatever the exact mechanism,
the residual's 13x growth since 2026-07-18 is itself solid evidence (independently measured
twice) that SOME live write path is still minting lowercase-cased manifest rows — the
`canonicalize_cefi_instrument_type_legacy_lowercase_2026_07_16.py` script's claim that the writer
was "already fixed" is stale/wrong for the MTDS manifest, though apparently still accurate for
the separate, much smaller instruments-service `_index/availability_index.parquet` surface (0
legacy rows there, independently re-verified this session).

**Existing `--apply` fix tooling had three separate safety defects** (found + fixed in this
session, `market-tick-data-service/scripts/normalize_instrument_type_casing.py`):
1. Mask over-reach: `itype.ne(itype.str.upper())` would have also uppercased the unrelated
   `futures_chain`/`options_chain`/`None`/`index` categories into `FUTURES_CHAIN`/`OPTIONS_CHAIN`/
   etc — still non-canonical, actively wrong (and would have fought the 2026-07-27-ruled-intentional
   convention). Fixed: mask now requires the uppercased form to be in
   `CANONICAL_ITYPES = {PERPETUAL, FUTURE, OPTION, SPOT_PAIR, COMBO}`.
2. No collision-dedup: `instrument_type` is part of the manifest's composite row-identity key
   (`unified_trading_library.manifest_writer._ROW_KEY_COLUMNS`) — uppercasing in place with no
   dedup could silently DUPLICATE a manifest row wherever an already-canonical-cased row exists for
   the same real shard atom. Fixed: dedups on the real composite key, keeping the
   latest-`attempted_at` survivor, mirroring the instruments-service sibling script's mechanics.
3. No backup: the original script overwrote the live PROD blob in place with zero backup. Fixed:
   backs up every touched blob to a timestamped sibling key before overwriting.

**The `--apply` run itself could not be safely completed in this interactive slot session** — this
is genuinely VM-scale work, not shared-host-scale:
- The per-VM shard scan is **166,686 individual GCS objects** (`_index/per_vm/*.parquet`) — a
  sequential download-modify-upload loop over that many objects timed out at 480s having barely
  started (per-object HTTP round-trips at that count are hours of wall-clock, not minutes).
- Even an `--index-only` run (added this session — skips the per-VM scan, touches only the single
  consolidated `_index/availability_index.parquet`, which is what `read_availability_index()`
  actually serves to readers/audits) was OOM-killed (exit 137) reading + building the composite
  row-key across the full 29.9M-row frame.

## Why it matters

- The plan's stated done-when ("re-count live; if a real residual exists, apply the fix") cannot be
  honestly closed by a quick apply — the residual is real, larger than believed, AND actively
  regenerating. A one-time apply without the writer fix would decay back toward today's 39,286
  within weeks, matching the exact growth pattern already observed since the 2026-07-18 baseline.
- `cefi_consolidated_closeout_2026_07_18.md`'s "Enumeration-audit terminal checkpoint" claim
  (2,982 residual, "dominated by already-ruled lowercase-casing variants") is now stale by an order
  of magnitude and should not be cited as current state.
- The task's own plan (`cefi_casing_residual_ao_dispatch_2026_08_16.md`) declared
  `repos: [instruments-service]`, but every script involved (the audit, the writer, the apply fix)
  lives in `market-tick-data-service` — corrected in that plan's own frontmatter as part of this
  session's flip.

## Recommended decision

- [x] ✅ [BACKEND] P1. **DONE 2026-08-17 (slot-11, backend_engineer craft)** — Confirmed and fixed the
      writer-side root cause. `market-tick-data-service@c07cc70e93`.

      **Confirmed**: `venue_fetch.py`'s `_record_venue_shard_counts` derives `manifest_itype` (the
      value that becomes `manifest_finalize.py`'s `itype_key`) via
      `fallback_itype = _tms._tradfi_manifest_itype(venue, itype)` (line ~410), where `itype` comes
      from `writer.underlying_counts` — keyed on the SAME lowercased `instrument_type` column
      `partitioned_writer.py::_resolve_instrument_type_column` stamps for GCS-path-building.
      `_tradfi_manifest_shard.py::_tradfi_manifest_itype` (pre-fix) hardcoded
      `if VENUE_TO_ASSET_GROUP.get(venue) != "tradfi": return itype` — so every CeFi venue (asset_group
      `cefi`, not `tradfi`) fell through this gate and the lowercase value was passed straight into
      the manifest row-key, unchanged. The shared UTL canon
      (`unified_trading_library.canonical.canonicalize_manifest_instrument_type`) already ships a
      `cefi` mapping table (`perpetual`/`spot_pair`/`spot`/`option`/`future` → canonical
      `InstrumentType`) — it was simply never reached for cefi.

      **Fix**: `_tradfi_manifest_itype` now calls
      `canonicalize_manifest_instrument_type(VENUE_TO_ASSET_GROUP.get(venue, ""), itype)`
      unconditionally, letting the shared canon's own asset_group gating (only `tradfi`/`cefi` have
      mapping tables; every other asset_group + the bundle-grain exclusion set — `futures_chain`/
      `options_chain`/`combo`/`combo_chain`/`continuous_future` — pass through unchanged) do the work,
      instead of re-gating on `== "tradfi"` in this file. The lowercase value is still used verbatim
      for `build_*_partition_path` (`partitioned_writer.py`/`tardis_shared.py` untouched) — only the
      MANIFEST-column casing changes, per the plan's own scoping.

      **Tests**: added `test_tradfi_manifest_itype_upgrades_cefi_venue` (BINANCE-SPOT/BYBIT/DERIBIT
      lowercase → canonical uppercase) and `test_tradfi_manifest_itype_bundle_grain_axis_still_unchanged_for_cefi`
      (Deribit `futures_chain`/`options_chain` stay lowercase, confirming the bundle-grain exclusion is
      asset-group-agnostic). Full `tests/unit/engine/test_tradfi_manifest_shard.py` +
      `tests/unit/test_venue_fetch_cefi_manifest_canonicalization.py` +
      `tests/unit/engine/test_sentinels_coverage.py` (111 tests) green — no pre-existing test assumed
      the buggy cefi-passthrough behavior as correct. Full `quality-gates.sh` green on `c07cc70e93`
      (sentinel-verified).

      This does NOT itself shrink the existing 39,286-row residual (that's todo 2's `--apply` VM
      dispatch, gated behind this fix per the plan) — it stops new lowercase-cased rows from being
      minted going forward, which is this todo's own done-when.
- [ ] [DATA] P2. Dispatch `scripts/normalize_instrument_type_casing.py --all-buckets --apply` (the
      corrected, safety-fixed version shipped this session — mask restricted to genuine casing
      variants, collision-dedup, timestamped backup) to a dedicated one-off VM per
      `/codex/05-infrastructure/vm-launcher-runbook.md` (this is corpus-scale: 166,686 per-VM
      shard objects + a 29.9M-row consolidated index — confirmed too large for the shared host,
      both the full per-VM scan and even an index-only run failed/OOM'd here). Safe-idempotent
      justification: dry-run first (now supported), backs up every blob before overwrite, dedups on
      the real manifest row-key so no row can be silently duplicated, and a second run against an
      already-normalized index is a clean no-op (changed=0). After apply, trigger the manifest
      consolidator to rebuild the merged index (per the script's own docstring) and re-run the
      enumeration audit to confirm 0 residual. Do this AFTER the P1 writer fix lands, or the count
      will already be climbing again by the time the VM run starts.

## Evidence

- Live re-count (2026-08-17 05:44 UTC, exit 0): manifest rows=29,938,146; casing residual=39,286
  (perpetual=38,083 + future=1,191 + spot_pair=12); bundle-shard-type (2026-07-27-resolved,
  intentional)=209,372 (futures_chain=173,043 + options_chain=36,329); other-non-canonical=323,437
  (None=162,190 + blank=157,337 + index=3,910).
- Code fix: `market-tick-data-service/scripts/normalize_instrument_type_casing.py` (mask fix +
  collision-dedup + backup + `--index-only` flag) — `market-tick-data-service@07861cf6`.
- Root-cause candidate code refs: `partitioned_writer.py:401-414`, `tardis_shared.py:565`,
  `manifest_finalize.py:259-269` (`itype_key` in `base_row_key`).
