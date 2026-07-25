---
doc_type: issue
title:
  "data_manifest_handler.py's availability-index collision risk — CORRECTED + RESOLVED: eigenlayer never wrote to the
  canonical index (initial write-up was factually wrong on this point); real risk was only in code being proposed for
  gas-fees/lst-rates, never shipped that way; a new, separate finding (consolidator reporting stale for this bucket)
  surfaced during verification and needs ops attention"
summary:
  'Originally filed claiming market-tick-data-service''s data_manifest_handler.py::_scan_eigenlayer() writes to the
  shared tick-data/defi bucket''s canonical _index/availability_index.parquet (the same path UTL ManifestWriter''s
  per-VM-shard consolidator owns), risking clobbering it. Re-verified 2026-07-12 and that claim was WRONG:
  _scan_eigenlayer() only READS (via _list_dates_with_venue) — it never calls _write_availability_index() at all. Direct
  inspection of the real file confirmed it healthy: 27.4M rows, dozens of real venues/data_types, matching what the real
  ManifestWriter/per-VM-shard consolidator produces — no corruption, no clobbering, ever. The actual risk was narrower
  than first framed: it only would have existed if gas-fees/lst-rates scanners were pointed at the shared bucket AND
  made to call _write_availability_index() there too — which was exactly the fix under consideration when this was
  filed. Implemented instead: _scan_via_availability_index(), which READS the canonical index (via
  unified_trading_library.read_availability_index()) and filters by the real data_type column — no write, so no
  collision risk, ever, by construction. Shipped market-tick-data-service@8b730664. This resolves the collision-risk
  question. A SEPARATE finding surfaced during live verification of that fix: read_availability_index() raised
  ManifestConsolidatorStaleError for this exact bucket ("stale or missing (older than
  MANIFEST_CONSOLIDATED_STALENESS_SEC=120s) while per-VM shards exist") — the shared code handles this gracefully (falls
  back to an honestly-empty result with a logged reason, doesn''t crash), but WHY the consolidator is reporting stale
  for this bucket (genuinely down/behind, vs. a 120s default threshold that''s simply tighter than this consolidator''s
  real schedule) is unresolved and needs an operator/ops look — see the new ''Open sub-finding'' section below.'
status: resolved
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [gcs, manifest, data-status, availability-index, data-pipeline-correctness, manifest-writer, defi]
related:
  [
    /plans/archive/2026_07/gcs_bucket_estate_cleanup_2026_07_10.md,
    /plans/archive/issues/gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md,
  ]
created: "2026-07-12"
parent_epic: infrastructure_master
priority: P1
source:
  "Discovered while fixing a crash in data_manifest_handler.py's _build_operations_dict() (4 operations calling
  resolve_bucket_name() for cloud-providers.yaml kinds deleted in gcs_bucket_estate_cleanup_2026_07_10). While deciding
  whether to also point the gas-fees/lst-rates scanners at the shared tick-data/defi bucket, misread _scan_eigenlayer()
  as ALSO writing to that bucket's availability index (it doesn't) and filed this issue on that incorrect premise.
  Re-verified by re-reading the actual function body + downloading and inspecting the real 27.4M-row index file directly
  — corrected below."
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm:
resolved_by: market-tick-data-service@8b730664
---

# data_manifest_handler.py's availability-index collision risk — corrected + resolved

## Correction (read this first)

The original write-up claimed `_scan_eigenlayer()` calls `_write_availability_index()` against the shared bucket. **This
was a factual error** — re-checked the actual function body:

```python
def _scan_eigenlayer(storage: _StorageClient) -> dict[str, object]:
    bucket = resolve_bucket_name(cloud="gcp", kind="tick-data", asset_group="defi")
    prefix = "raw_tick_data/by_date/"
    venue = "EIGENLAYER-ETHEREUM"
    dates = _list_dates_with_venue(storage, bucket, prefix, venue)   # READ only
    ...
    return {...}   # no _write_availability_index() call anywhere in this function
```

Grepping every call site of `_write_availability_index(` in the pre-fix file confirmed it was called only by
`_scan_gas_fees`, `_scan_protocol_chain_bucket`, `_scan_flat_date_bucket`, and `_scan_protocol_only_bucket` — each
against **their own dedicated** resolved bucket (gas-fees/dex-pools/dex-swaps/lst-rates/etc.), never the shared
`tick-data`/`defi` bucket. `_scan_eigenlayer` is the only function resolving the shared bucket, and it's read-only.

**Directly verified the file's actual current content** (downloaded + read
`gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`, 482MB): 27,446,015 rows,
dozens of real venues (UNISWAP_V3, BALANCER, MORPHO, AAVE_V3, ...) and real data_types (dex_pool_state, dex_pool_swaps,
lending_indices, liquidations, oracle_prices, lst_rates: 222,836 rows spanning 2018-01-01 to 2026-07-10, gas_fees:
49,575 rows, eigenlayer_rewards: 201,402 rows, ...). This is unambiguously the real, comprehensive, healthy consolidator
output — never corrupted, never at risk from `_scan_eigenlayer`.

## What the real (narrower) risk was, and how it was resolved

The genuine risk only existed in the fix I was about to make: pointing `_scan_gas_fees`/the lst-rates scanner at the
shared bucket (to fix their under-reporting — see [[gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10]]) while
leaving their existing `_write_availability_index()` calls intact would have made THEM write raw overwrites into the
shared bucket's canonical index — a risk that didn't exist before that specific change and never shipped.

**Resolution**: implemented `_scan_via_availability_index(data_type, description)` instead of reusing the raw
blob-listing scanners. It calls `unified_trading_library.read_availability_index(bucket, columns=[...])` — a read-only
call into the canonical index — and filters by the real `data_type` column. No write, anywhere, ever. This was also the
CORRECT fix on its own merits, independent of the collision question: gas-fees/lst-rates captures span multiple venues
per data_type (gas_fees: ALCHEMY/LIDO/ETHERFI; lst_rates: AAVE_V3/COMPOUND_V3/BALANCER/LIDO/...) with `data_type` living
only as a parquet column, never as a GCS path segment — raw blob-path listing (what the old scanners did, against a
`gas_fees/`/`lst_rates/` flat prefix that turns out to never have existed in this bucket) could never have worked,
collision risk or not. Shipped `market-tick-data-service@8b730664`, full `quality-gates.sh` green, 49 tests passing.

## Open sub-finding: consolidator reports stale for this bucket

Live-verifying the fix against real production data, `read_availability_index()` raised
`ManifestConsolidatorStaleError`:

```
Consolidated availability_index for bucket='market-data-tick-defi-prd-central-element-323112' is stale or missing
(older than MANIFEST_CONSOLIDATED_STALENESS_SEC=120s) while per-VM shards exist — the manifest consolidator is
behind or DOWN.
```

The shared code's designed behavior here is correct and safe (loud-fail rather than silently reading possibly-wrong
data, or OOMing on a 12+ GB per-VM merge) — `_scan_via_availability_index()` catches this specific exception and falls
back to an honest "empty" result with the reason logged, which is exactly right for a coverage-reporting handler. **Not
fixed or investigated further**: whether this means the real consolidator Cloud Run Job/Scheduler for this bucket is
actually behind/down (an active ops issue — matches the codex note that "GCS manifest consolidator ... loud-fails on
stale index"), or whether `MANIFEST_CONSOLIDATED_STALENESS_SEC`'s 120-second default is simply tighter than this
bucket's real consolidator cadence (a threshold-tuning non-issue). Either way, do NOT set
`MANIFEST_ALLOW_STALE_FALLBACK=true` to force through a read without checking which case this is first — the
per-VM-shard recovery merge this triggers can OOM (12+ GB pandas heap on large buckets, per `ManifestWriter`'s own
docstring), and this bucket is 482MB+ / 27M+ rows, squarely in that risk zone.

**Recommended next step**: check the DeFi tick-data bucket's manifest-consolidator Cloud Run Job + Scheduler health
directly (`/codex/05-infrastructure/manifest-consolidator-ssot.md` has the runbook) — confirm whether it's actually
behind schedule or just running on a slower cadence than 120s tolerates.

## Status

Resolved 2026-07-12 (same session that filed it) — the collision risk this issue was filed about never existed in
shipped code and the underlying gas-fees/lst-rates fix now uses a read-only approach that can't introduce it. One new,
narrower, separate finding (consolidator staleness for this specific bucket) is flagged above for ops follow-up — not
blocking, not urgent by itself, but worth a real answer rather than silently living with "empty" gas-fees/ lst-rates
coverage on the deployment-UI status page whenever the consolidator is in this state.
