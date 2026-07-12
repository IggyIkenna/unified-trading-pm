---
doc_type: issue
title:
  "data_manifest_handler.py writes DIRECTLY to the canonical _index/availability_index.parquet path of the shared
  market-data-tick-defi bucket, bypassing ManifestWriter/ManifestConsolidator's CAS+per-VM-shard protocol entirely —
  risk of clobbering the real DeFi tick-data availability index with a near-empty stub"
summary:
  "Surfaced while investigating the gas-fees/lst-rates bucket-kind fix
  ([[gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10]]) for [[gcs_bucket_estate_cleanup_2026_07_10]]:
  market-tick-data-service's data_manifest_handler.py::_scan_eigenlayer() resolves kind='tick-data', asset_group='defi'
  (the SAME shared bucket real DeFi tick-data writers use) and calls _write_availability_index(), which does a raw
  storage.upload_bytes(bucket, '_index/availability_index.parquet', ...) — a full, non-atomic overwrite. That literal
  path (_index/availability_index.parquet) is also UTL ManifestWriter's _INDEX_PATH — the canonical, consolidated
  availability index that real DeFi tick-data writers populate via MANIFEST_PER_VM_SHARDS=true + an async consolidator
  daemon (consolidate_per_vm_shards), specifically to avoid racing direct writes to that exact path. If
  data_manifest_handler.py's 'data-manifest' CLI operation is ever invoked against a project where the shared defi
  tick-data bucket has a live per-VM-shard consolidation cycle running, its write would overwrite the canonical index
  (built from ALL real defi captures) with a stub containing only EigenLayer-rewards dates — or vice versa, depending on
  write ordering. Not fixed here — root-caused and documented only, pending a decision on the correct fix (route via
  ManifestWriter instead of raw upload_bytes; write to a differently-named path; or confirm this operation is safe
  because it's never actually invoked against a live per-VM-shard bucket) plus operator confirmation the risk is real
  before touching production write logic."
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [gcs, manifest, data-status, availability-index, data-pipeline-correctness, manifest-writer, defi]
related: [gcs_bucket_estate_cleanup_2026_07_10.md, gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md]
created: "2026-07-12"
parent_epic: infrastructure_master
priority: P1
source:
  "Discovered while fixing a crash in data_manifest_handler.py's _build_operations_dict() (4 operations calling
  resolve_bucket_name() for cloud-providers.yaml kinds deleted in gcs_bucket_estate_cleanup_2026_07_10). While deciding
  whether to also point the gas-fees/lst-rates scanners at the shared tick-data/defi bucket (matching _scan_eigenlayer's
  existing pattern), tracing _write_availability_index()'s output path led to UTL ManifestWriter._INDEX_PATH — same
  literal string, same bucket family. Declined to compound the risk by adding 2 more direct-overwrite callers; left
  gas-fees/lst-rates bucket resolution untouched pending this issue's resolution."
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm:
resolved_by:
---

# data_manifest_handler.py's availability-index write may collide with the real ManifestWriter/Consolidator

## What was found

`market-tick-data-service/market_tick_data_service/cli/handlers/data_manifest_handler.py::_scan_eigenlayer()` (this
predates the current session — NOT something introduced by the 2026-07-10/07-12 bucket-estate cleanup work) resolves:

```python
bucket = resolve_bucket_name(cloud="gcp", kind="tick-data", asset_group="defi")
```

— the SAME shared `market-data-tick-defi-{env}-{project_id}` bucket that real DeFi market-tick-data writers use for raw
tick capture. It then calls `_write_availability_index(storage, bucket, index_rows)`, whose body is:

```python
storage.upload_bytes(bucket, _AVAILABILITY_INDEX_PATH, buf.getvalue())
```

where `_AVAILABILITY_INDEX_PATH = "_index/availability_index.parquet"`.

That literal path is **also** `unified_trading_library.manifest_writer._writer.ManifestWriter._INDEX_PATH` — the
canonical, consolidated availability index for the bucket. Per `ManifestWriter`'s own docstring, real writes to this
path are supposed to go through either:

1. A direct `ManifestWriter.write()` call (CAS-protected merge), or
2. `MANIFEST_PER_VM_SHARDS=true` mode — each VM writes to `_index/per_vm/{instance}.parquet`, and a separate
   **consolidator daemon** (`consolidate_per_vm_shards`) asynchronously merges those shards into the canonical
   `_index/availability_index.parquet` — specifically so individual writers never race the consolidator on that path.

`deployment-service/terraform/gcp/lst_seasonal_rewards_scheduler.tf` and `audit03_cron_provisioning.tf` both set
`MANIFEST_PER_VM_SHARDS=true`, confirming the shared DeFi tick-data bucket is under active per-VM-shard consolidation in
production.

`data_manifest_handler.py`'s `_write_availability_index()` does **none of this** — it's a raw, one-shot, full-bucket
overwrite via `storage.upload_bytes()`, containing only the rows for whichever operation called it (in the current code,
only `_scan_eigenlayer`'s EigenLayer-rewards dates — one row per date, nothing else). If this write lands after the
consolidator's own write, the canonical index — built from every real DeFi tick-data capture — would be replaced by a
near-empty stub until the next consolidator cycle overwrites it back (or does it get further corrupted by racing writes
— not analyzed here).

## Why this wasn't fixed here

This was found as a side effect of deciding how to fix `data_manifest_handler.py`'s gas-fees/lst-rates operations (see
[[gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10]]) — pointing those two scanners at the same shared
`tick-data`/`defi` bucket (to fix their under-reporting) would have added 2 more direct-overwrite callers on top of
eigenlayer's existing one, compounding an already-serious-looking collision risk. That fix was deliberately **not**
applied; gas-fees/lst-rates bucket resolution in this handler is unchanged.

Fixing the underlying collision properly requires either:

1. Routing `_write_availability_index()` through `ManifestWriter.write()` (adds real per-VM-shard/CAS semantics — the
   "correct" fix, larger blast radius, needs to be tested against a live per-VM-shard cycle), or
2. Writing to a **different, namespaced path** so this handler's coverage-report index never collides with the canonical
   one (smaller blast radius, but check whether `deployment-api`'s `read_availability_index()` consumer for this
   specific report expects the canonical path — if so this alone doesn't fully fix the reporting use case), or
3. Confirming `data-manifest` (the CLI operation name, `market-tick-data-service/.../cli/main.py:583`) is **not**
   actually scheduled anywhere (no Terraform Cloud Scheduler entry was found referencing it — grepped workspace-wide)
   and is genuinely dead/manual-only, in which case the risk is latent rather than active — still worth fixing before
   anyone runs it, but not an emergency.

None of these is safe to guess at without operator input on which downstream consumer(s) actually depend on the current
(possibly-already-broken, unverified) state of the canonical index in the shared DeFi tick-data bucket.

## Recommended next step

1. Confirm whether `data-manifest` has ever actually been run against `central-element-323112`'s
   `market-data-tick-defi-*` bucket (check GCS object version history / audit logs for
   `_index/availability_index.parquet` in that bucket — multiple distinct writers would show up as alternating content
   sizes/row-counts across versions).
2. If it has run: assess whether the current canonical index is already corrupted (row count / date range sanity check
   against known real DeFi tick-data coverage) — if so, this becomes the same class of "big finding — data-correctness"
   as the gas-fees/lst-rates mismatch and should be triaged the same way.
3. Decide fix direction (route through `ManifestWriter`, or namespace the path) and implement + test against a non-prod
   bucket before touching the real one.

## Status

Not investigated further as of 2026-07-12 (found while fixing a crash in the same handler, deliberately not compounded —
see "Why this wasn't fixed here"). Per findings-triage this is a "big finding — data-correctness / cross-repo" needing
operator visibility, not something to guess-fix without confirming actual current-state severity first.
