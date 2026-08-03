---
doc_type: issue
title:
  Legacy-CAS write invisibility to the shard-fallback manifest read — confirmed, and independently remediated twice
  since 2026-07-19
summary: >-
  Closes the open question from the 2026-07-19 sports P2 investigation
  (sports_p2_history_apifootball_2015_to_present_2026_06_27.md, archived) — does the shard-fallback aggregate read
  structurally never fold in a prior legacy-CAS write? CONFIRMED TRUE of `_read_and_merge_per_vm_shards()`'s own design
  (it lists+reads only `_index/per_vm/*.parquet`, never the canonical blob). Two independent fixes since have closed the
  practical failure mode without changing that underlying fact: the 2026-06-01 liveness-health change made the fallback
  opt-in (loud-fail by default) instead of silent, and a 2026-08-02 fleet-wide sweep gave the specific closer script
  that caused the original incident `per_vm_shards=True`, so it no longer produces a legacy-CAS write.
status: resolved
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-library, instruments-service]
scope: [engineer]
tags: [sports, manifest, legacy-cas, shard-fallback, consolidator, investigation]
related:
  [
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/archive/2026_07/sports_p2_history_apifootball_2015_to_present_2026_06_27.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: "2026-08-03"
parent_epic: sports_master
priority: P2
assigned_vm: planning
resolved_by: "read-only investigation, no code change needed — findings below"
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
source: [sports_consolidated_native_ao_extract_2026_07_25.md Track S2 legacy-CAS-question todo]
last_updated: "2026-08-03"
---

# Legacy-CAS write invisibility to the shard-fallback manifest read

## What I found

**Hypothesis under test** (from the 2026-07-19 investigation): "the aggregate shard-fallback gate structurally never
sees a legacy-CAS write, by design, until/unless a corpus-wide reconciliation happens."

**(1) Confirmed TRUE of the code's actual design.** The relevant merge-source module is
`unified_trading_library/manifest_writer/_read_index.py` (not `manifest_consolidator.py`, which only handles the
consolidator's own write cycle — the 2026-07-19 investigation hit the READER's fallback path, a separate mechanism).
`_read_and_merge_per_vm_shards()` (`_read_index.py:1133`) lists + reads ONLY blobs under `_index/per_vm/*.parquet` —
direct read of the function body confirms it never downloads or reads the canonical `_index/availability_index.parquet`
at all. A write that lands only in the canonical (legacy CAS, i.e. a bare `ManifestWriter(...)` with no
`per_vm_shards=True`) is therefore structurally 100% invisible to this function, regardless of how much time passes.

**(2) Fix #1 — the fallback is no longer silent-by-default (2026-06-01, predates this investigation but wasn't yet
reflected in the 2026-07-19 doc's own recommendation).** `_read_and_merge_per_vm_shards()` is reached via
`_read_slow_path()` (`_read_index.py:207`), the stale-consolidated-blob fallback inside the public
`read_availability_index()`. Per `_resolve_allow_stale_fallback()`
(`unified_trading_library/manifest_writer/_state.py:320-332`, `manifest_consolidator_liveness_health_2026_06_01`), the
DEFAULT behavior (env `MANIFEST_ALLOW_STALE_FALLBACK` unset) is now to raise `ManifestConsolidatorStaleError` instead of
silently falling back to the per-VM-only read. So the exact silent-wrong-answer shape observed 2026-07-19 (a stale read
quietly returning an incomplete shard-only view, permanently missing the CAS write) can only recur today if a caller
explicitly sets that env var. `instruments-service/scripts/query_api_football_pending_clusters_2026_07_18.py` (the gate
script the original investigation used) does not set it — confirmed by direct read of its source, which calls the bare
`read_availability_index(bucket, columns=[...])`.

**(3) Fix #2 — the specific closer script that caused the 2026-07-19 incident no longer writes via legacy CAS
(2026-08-02, one day before this dispatch).** The root cause of the original incident wasn't the reader alone — it was
that `close_stale_enrichment_expected_unattempted_cells_2026_07_19.py`'s `_apply()` constructed a bare
`ManifestWriter(service_name=..., catalogue_bucket=bucket)` with no `per_vm_shards=True`, which is what routed its
5,288-cell write through the legacy CAS path in the first place. `instruments-service@d0e4e5a3` ("fix(scripts): add
per_vm_shards=True to bare ManifestWriter sites (sports/prediction buckets)", a 17-script fleet-wide sweep triggered by
the unrelated `migrate_legacy_gas_fees_venue_2026_07_30.py` OOM incident) added `per_vm_shards=True` to this closer's
`_apply()` among the 17. Confirmed via
`git show d0e4e5a3 -- scripts/close_stale_enrichment_expected_unattempted_cells_2026_07_19.py`. A fresh `--apply` of
this script today writes to a per-VM shard, which `_read_and_merge_per_vm_shards()` (fix #1's opt-in fallback) DOES see,
and which the ordinary consolidator cycle folds into the canonical shortly after.

**Contrast — a function that DOES get this right**: `merge_canonical_with_outstanding_shards()` (`_read_index.py:1441`)
reads the canonical blob AND merges outstanding per-VM shards on top — a legacy-CAS write already in the canonical IS
visible through this path. It's used by write-back reconcilers (e.g. a phantom-row correction that must re-read
canonical immediately before writing back), never by the standard hot-path reader.

## Why it matters

The underlying reader-side gap (`_read_and_merge_per_vm_shards()` never reading the canonical) is still real and
unchanged in the code today — it just requires 2 independent, now-true preconditions to be silently hit (a caller that
reads a stale index AND opts into `MANIFEST_ALLOW_STALE_FALLBACK=true`), so the 2026-07-19 incident's specific trigger
(this closer's own bare `ManifestWriter`) is closed, but a DIFFERENT bare-`ManifestWriter` script hitting a
stale-and-opted-in read could still reproduce the same class of silent gap.

## Recommended decision

No new code change needed for THIS finding — both practical remediations already shipped independently before this
investigation started. Leaving open only as a documentation/awareness note:

- [x] ✅ [DOC] P3. Add a one-line pointer to this doc's finding (2) + (3) in
      `/codex/05-infrastructure/manifest-consolidator-ssot.md`'s "Liveness + health contract" section, so a future
      reader of that section knows the opt-in stale-fallback gap was traced to a concrete, now-fixed incident rather
      than staying a purely theoretical caveat. (repo: unified-trading-pm) — unified-trading-pm@pending
