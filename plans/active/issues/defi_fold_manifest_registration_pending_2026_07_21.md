---
doc_type: issue
title: DeFi fold (2026-07-21) — 648 canonical twins written but manifest rows not yet registered
summary:
  The 2026-07-21 defi dex_pools/lending_indices fold wrote 648 canonical OBJECTS (verified) but did not register
  availability-manifest rows for them. The consolidator merges record_captured per-VM shards — it does NOT re-derive
  rows from raw GCS objects — so the folded twins do not yet appear as captured in the coverage manifest. A standalone
  register pass via DefiManifestRecorder did not flush cleanly in a script context (no partial write occurred). This is
  a coverage-reporting gap, not data loss — the objects exist and the depth-provider reads them directly.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [defi, fold, manifest, record-captured, consolidator, honest-coverage, dex-pools, solana]
related:
  [
    defi_dex_pools_delete_order_stale_2026_07_20.md,
    data_pipeline_reconciliation_skill_2026_07_20.md,
    ../../codex/05-infrastructure/manifest-consolidator-ssot.md,
    ../../codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-21
last_updated: 2026-07-21
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: found while executing the D3 fold + manifest step, 2026-07-21
depends_on: []
---

# DeFi fold (2026-07-21) — canonical objects written, manifest rows pending

> **State:** the DATA migration is COMPLETE and verified (648 legacy-only twins written; KAMINO-vault 0→513, SOLEND
> 0→59, KAMINO-lending 0→44, RAYDIUM 100→132). The legacy `dex_pools/`+`lending_indices/` prefixes now have canonical
> twins for every cell → the delete is SAFE (human-only). What remains is registering the manifest rows so the folded
> twins show `captured` in the coverage surface. **No data is at risk; no partial manifest write occurred.**

## The mechanism finding (corrects a stale assumption)

The fold script's docstring claimed "the manifest is re-derived from GCS by the standard consolidator." **That is
wrong.** `unified_trading_library.manifest_consolidator.consolidate(bucket)` lists + merges the
`_index/per_vm/*.parquet` shards written by `record_captured` — it does **not** scan raw `raw_tick_data/` objects (that
would be the banned whole-corpus walk). So an objects-only fold leaves **no** manifest representation.

## The correct registration recipe (verified in dry-run: 714 rows)

Register one `record_captured` row per folded instrument at the per-pool grain (bare address, lowercased — the grain the
live `dex_pools_handler` and the address-keyed enumerator both use), then consolidate:

- `DefiManifestRecorder(catalogue_bucket=<market-data-tick-defi bucket>, target_day=date(2026,4,14), handler_label="dex_pools")`
- per instrument:
  `recorder.record_captured(venue=<PROTO>, chain="SOLANA", data_type="dex_pool_state"|"lending_indices", row_count=<n>, pipeline_mode=derive_pipeline_mode_for_row(<PROTO>,"defi",<dt>), instrument_type="solana_amm_pool"|"solana_vault"|"solana_lending", instrument_id=<address>.lower(), attempted_at=datetime(2026,4,14,tzinfo=UTC), source="onchain_subgraph")`
- `recorder.close()`, then `python -m unified_trading_library.manifest_consolidator --bucket <bucket>`.
- Scope: the 4 subsets with new writes (KAMINO-vault 513, KAMINO-lending 44, SOLEND 59, RAYDIUM 98 = 66 idempotent
  refresh + 32 new). SKIP ORCA (0 new — all 14,094 pre-existing, already registered by the live writer). Dry-run
  confirmed **714** rows.

## The blocker (why it is not done inline)

A standalone `DefiManifestRecorder`/`ManifestWriter(batch_size=1)` register pass did not flush a `_index/per_vm/` shard
in a plain-script context (the process reached storage/validation init, then exited without persisting — no output, no
shard, **no partial write**). The recorder is coupled to the live handler's async flush discipline. It was **not** worth
risking a flaky prod manifest write at the tail of the migration, so it is filed here as a bounded follow-up rather than
forced.

## Todos

- [x] 1. [DATA] P1. Diagnose why the standalone `DefiManifestRecorder`/`ManifestWriter(batch_size=1)` register pass does
      not flush a `_index/per_vm/` shard from a plain script (buffer/flush/async-context coupling); either fix the
      standalone path or run the registration through the live handler flush discipline. —
      **unified-trading-library@b9534230** (landed via an inherited-stale-WIP commit; diff verified byte-identical,
      evidence below). Root cause reproduced directly: `ManifestWriter._write_to_gcs()` calls `get_storage_client()`
      with no explicit `project_id`, which falls through to `get_project_id()` — this raises a bare
      `ValueError: GCP_PROJECT_ID or AWS_ACCOUNT_ID must be set in     environment` when the env var is unset (the
      normal condition for a bare script; a bootstrapped service always sets it, and the fold script itself only worked
      because it resolves its OWN separate storage client with an explicit `project_id=`). That `ValueError` escaped
      `_write_to_gcs`'s except clause (`ImportError, ConnectionError,     OSError, RuntimeError` only) uncaught, and
      `DefiManifestRecorder`'s blanket `except Exception: logger.warning(...)` swallowed it with zero row-loss
      accounting — exactly "reached storage/validation init, then exited without persisting, no output". Fixed: (a) the
      `ValueError` is now re-raised as `RuntimeError` so it routes through the SAME caught-exception +
      `MANIFEST_ATEXIT_DRAIN_INCOMPLETE` accounting path already proven for the atexit/asyncio race; (b) a write failure
      no longer permanently discards the records `_mark_flushed` already popped off the module buffer — `_drain()` now
      re-stages them so the next `write()`/`flush()`/`close()` call gets another chance. SECOND compounding factor found
      (operational, not a code bug): this bucket's canonical index is ~1.9 GB / ~52M rows — without
      `MANIFEST_PER_VM_SHARDS=true` the writer defaults to the legacy single-blob generation-match CAS path, which on a
      bucket this hot spins through all 15 retries (full read-merge-reupload of the whole blob each time) and
      empirically never completed for even 1 row within 170s; with per-VM-shard mode it completed in <1s. Both env vars
      are required for any future standalone script against this bucket.
- [x] 2. [DATA] P1. Register the 714 rows per the recipe above (dry-run first — it prints the per-cell counts), then run
      the consolidator over the defi market-data bucket; verify the folded cells show `captured` for `day=2026-04-14`
      (KAMINO/SOLEND/32-Raydium flip from `expected_unattempted` → `captured`). — **748 rows registered (not 714)**,
      scoped one-off script (`register_defi_fold_manifest.py`, per-recipe, `logging.basicConfig` +
      `setup_events(mode="local")` + `GCP_PROJECT_ID` + `MANIFEST_PER_VM_SHARDS=true` + explicit `recorder.close()`),
      run against the REAL GCS objects for all 4 subsets on `day=2026-04-14`: KAMINO/solana_vault/dex_pool_state=513,
      KAMINO/solana_lending/lending_indices=44, SOLEND/solana_lending/ lending_indices=59,
      RAYDIUM/solana_amm_pool/dex_pool_state=132 (513+44+59+132=748). A live pre-check (`ManifestWriter.lookup()`
      against the current index) showed ZERO existing rows for `day=2026-04-14` across all 4 subsets before this run, so
      every one of the 748 real, GCS-verified canonical objects needed registration — not just the delta the original
      dry-run's 714 estimate assumed (which appears to have pre-supposed ~34 RAYDIUM cells were already correctly
      registered; empirically none were). **Verified via live manifest read**
      (`read_availability_index(bucket, filters=[("date","==","2026-04-14")])`): all 748 rows show
      `capture_status=captured` with correct
      `row_count`/`pipeline_mode=batch_onchain_subgraph`/`source=onchain_subgraph`, split exactly as above. Consolidator
      run:
      `python -m unified_trading_library.manifest_consolidator --bucket     market-data-tick-defi-prd-central-element-323112`
      (incremental; canonical index is ~52.3M rows so a full incremental merge cycle over the whole 2018–2026 range
      takes several minutes — a first attempt timed out mid-merge at 280s, re-run with no artificial timeout to let it
      finish; see Progress Log for final status if still running at handoff).
- [x] 3. [REVIEW] P1. Correct the fold script's MANIFEST docstring (it wrongly says the consolidator re-derives from
      objects) — or delete the one-off script once the legacy prefixes are deleted (human-only) and this is resolved. —
      Code fix complete and verified locally (docstring + closing log line now correctly state the consolidator does NOT
      re-derive rows from raw objects, and point at this issue doc's recipe); **not yet pushed** — every
      `quickmerge --agent` in market-tick-data-service is currently blocked by an unrelated, pre-existing, deterministic
      3-test regression on HEAD (canonical-stem / leaf-byte-match / catalog-decompose — nothing to do with this fold or
      this docstring). Filed as `mtds_canonical_stem_leaf_qg_regression_blocks_quickmerge_2026_07_21.md`; the docstring
      diff is safe to ship the moment that regression is fixed and the sentinel goes green.

## Progress Log (2026-07-21)

- Root-caused + fixed the flush gap in `unified-trading-library` (see todo 1). Fix landed on `live-defi-rollout` via
  commit `b9534230` (another agent inherited this session's stale-but-verified dirty WIP per the LIVENESS-gated
  inherit-dead-claim rule while unblocking an unrelated instruments-service quickmerge; diff confirmed byte-identical to
  what this session authored). 42 pre-existing `manifest_writer` tests + this session's own full
  `unified-trading-library` quality-gates run (6670 passed; only 2 unrelated `cloud-providers.yaml` sibling-parity
  failures, pre-existing/out of scope) both green.
- Registered all 748 real folded rows for `day=2026-04-14` and verified `capture_status=captured` via a live manifest
  read (see todo 2). Consolidator run in progress/completed against the canonical `_index/availability_index.parquet`
  (52.3M rows) — see whichever of this session's final report / a follow-up session's check confirms the canonical blob
  itself now reflects these rows (the per-VM-shard-merge fallback the reader already performs means the rows are visible
  to ANY caller today regardless of consolidator completion, since the canonical blob is currently >120s stale and the
  reader always falls back to a live per-VM-shard merge).
- Fixed the fold script's MANIFEST docstring (todo 3) in market-tick-data-service; ship blocked on an UNRELATED
  pre-existing regression, filed separately (see todo 3 note + the new issue doc).

## Alternative

Re-running the DeFi capture for `day=2026-04-14` (KAMINO/SOLEND/RAYDIUM) through the **live handler** would register the
manifest correctly (the handler's `record_captured` path works) — but defi capture is currently STOPPED, and the fold
already created the objects, so the register-pass path above is cheaper.
