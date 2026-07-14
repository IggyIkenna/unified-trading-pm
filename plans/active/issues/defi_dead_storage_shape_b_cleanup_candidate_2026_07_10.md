---
doc_type: issue
title:
  "🔴 REVERSED 2026-07-14: DeFi shape-B is NOT dead — actively preferred by production DeFi instrument loading, and 45%
  of sampled pairs DIVERGE in content from the flat shape (was: ~104K dead-storage duplicate objects, safe-to-delete
  candidate)"
summary:
  The DeFi legacy-naming audit (2026-07-09) found a fully distinct duplicate write path
  (`day={D}/pipeline_mode=batch_instruments_service/asset_group=defi/venue={V}/...`) mirroring ~104K real objects in the
  `-prd-` bucket. Two spot-checked samples (oldest 2020-01-20, recent 2026-06-10, CRC32C+MD5 hash-verified) were
  byte-for-byte identical to their flat-shape sibling, and every real consumer confirmed to read only the flat shape.
  Recommended as its own dedicated SAFE-TO-DELETE audit — not executed, and not a full-corpus reconciliation (only 2
  samples checked).
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [instruments-service]
scope: [engineer, admin]
tags: [dead-storage, cleanup, gcs, cost, defi]
related: [instrument_id_format_canonicalization_2026_07_08.md]
created: 2026-07-10
parent_epic: instruments_master
assigned_vm:
resolved_by:
source:
  "Real finding from the DeFi legacy-naming audit agent (wf_9e5f13e3-962, 2026-07-09), the same session that found and
  fixed the ghost-venue-merge + its data-contamination bug."
priority: P1
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

## What I found

Real narrow-prefix GCS listing across `instruments-store-defi-prd-central-element-323112` found a second, fully distinct
real duplicate write path: `day={D}/pipeline_mode=batch_instruments_service/asset_group=defi/venue={V}/...` mirroring
~104K real objects (2,353 of 2,363 real day-partitions) of the flat-shape tree. Real writes to this shape stopped
~2026-06-30 (confirmed dead going forward, not an actively-growing duplicate).

**Confirmed real, not assumed**:

- 2 spot-checked samples (oldest real date `day=2020-01-20`, a recent `day=2026-06-10`), CRC32C+MD5 hash-verified —
  byte-for-byte identical to the flat-shape sibling.
- Confirmed **unread by every real consumer** — grepped `unified_trading_library`'s `instrument_lifecycle_loader.py`,
  `domain/instruments_client.py`, `domain_client/clients/instruments.py`, `options_cluster_lookup.py`,
  `core/cloud_data_provider.py` — all read the flat shape only.

**Important caveat, stated honestly by the finding agent**: this is only 2 spot-checked samples out of 2,353 real
day-partitions, not a full reconciliation — treat as a real-but-narrow finding, not a proven full-corpus guarantee,
until a dedicated audit checks more broadly (or all) of the 2,353 partitions.

This mirrors the exact same shape-B pattern the CeFi legacy-naming audit found for OKX in the same session — but unlike
OKX's shape B (which DID carry stale/buggy unmigrated content and needed a real fix), this DeFi shape B appears to be
genuinely redundant dead storage, not a coverage gap.

## Why it matters

~104K real objects of confirmed-dead, confirmed-duplicate storage is a real, quantifiable GCS cost with zero functional
value if the full-corpus check confirms the 2-sample finding holds broadly. Not urgent (no correctness risk — nothing
reads it), but a legitimate cleanup opportunity once verified safe at scale.

## Recommended next step

A dedicated SAFE-TO-DELETE audit, same pattern as
`market-tick-data-service/e2e-testing/scripts/defi/ audit_legacy_gcs_dup_delete_list.py` and the exact shape-B pattern
the CeFi audit already used:

1. Real full (or much larger sample) reconciliation across all 2,353 real day-partitions — confirm byte-identical
   duplication holds broadly, not just for 2 samples.
2. Re-confirm zero real consumers read this shape (broader grep + a runtime check if feasible, e.g. log-based access
   auditing over a real time window).
3. Only then: a real, backup-first (or GCS-versioning-based) deletion pass, with the same rigor as every other migration
   this session (dry-run first, verify, then real delete).

## 🔴 2026-07-14 — fuller reconciliation REVERSES both premises of this doc: NO-GO on any deletion

Ran the recommended next step above (both parts) for real. Result: **the "dead storage" premise does not hold.**

**Part 1 — byte-comparison at scale (100 day-partitions, not 2).** Stratified sample across the full corpus +
oldest/newest, 2,911 venue-day pairs where both shapes had a comparable file (CRC32C + MD5 + size):

- **1,596 (54.8%) byte-identical** — matches the original finding's direction, just not its universality.
- **1,315 (45.2%) MISMATCH** — different size, different CRC32C, different MD5. Spread across every year (2020: 10,
  2021: 34, 2022: 124, 2023: 248, 2024: 382, 2025: 413, **2026: 104** — not an old-data-only artifact; e.g.
  `day=2026-02-28`, venues `AAVE_V3-{ARBITRUM,AVALANCHE,BASE,BSC,ETHEREUM}` all mismatch).
- 1,525 venue-day slots exist in only ONE shape (157 shape-B-only, 1,368 flat-only) — a meaningful chunk traces to an
  unfixed venue-naming divergence between the two paths (flat `AAVE_V3-ARBITRUM` vs shape-B `AAVEV3-ARBITRUM`, flat
  `UNISWAP_V2-ETHEREUM` vs shape-B `UNISWAPV2-ETHEREUM`) — the same ghost-venue-naming bug class the 2026-07-09 session
  already found + fixed for `dexpool`, just left unfixed here.

The original "byte-for-byte identical" claim was real for its 2 samples, but those samples happened to land on days
where content matched — it does not generalize. Under half the corpus is verified-identical.

**Part 2 — broader consumer grep found a REAL, CURRENT, ACTIVE consumer.**
`market_tick_data_service/ instrument_availability_paths.py` (added 2026-07-13 — i.e. AFTER this issue doc was filed, so
the original grep could not have caught it) — `match_instruments_blob()`:

```python
hive = [n for n in candidates if "/pipeline_mode=" in n]
return (hive or candidates)[0]   # shape-B (hive) wins whenever both layouts exist
```

Called from `base_defi_adapter.py::_load_instruments_for_venue` (~line 390), the shared instrument-loading method
inherited by essentially every real DeFi protocol adapter (`uniswap_v3_adapter.py`, `uniswapv4_adapter.py`,
`aave_adapter.py`, `balancer_adapter.py`, `morpho_adapter.py`, `defillama_adapter.py`, several vault/LST/restaking
adapters — wired through `market_interface/factory.py`). **This reads and PREFERS shape-B, right now, in production,
whenever a shape-B object exists for that (day, venue)** — the exact opposite of "confirmed unread."

**Combined implication — this is now a live data-correctness concern, not a cleanup candidate.** Given shape-B is
preferentially consumed AND diverges from the flat shape in 45% of sampled cases, DeFi instrument loading may be
silently using stale or wrong data for a real fraction of (day, venue) pairs _right now_, independent of any cleanup
question. **Do not run any deletion pass, dry-run or otherwise — status is NOT resolved, priority raised P3→P1.**

**New real next step** (supersedes the old "safe-to-delete audit" recommendation): a fresh, separate investigation into
which shape is actually authoritative per (day, venue) — this needs an explicit operator decision (does
`match_instruments_blob`'s hive-wins policy reflect real intent, or is it itself the bug?), not a cleanup script. Also
needs the same venue-naming-divergence fix (`AAVEV3-*` → `AAVE_V3-*` etc.) already applied to `dexpool` in the
2026-07-09 session, extended to this path.

Investigation script (read-only, nothing written to GCS): scratchpad `defi_shape_b_reconcile.py`, raw results
`run5.json`/`run100.json` (session-local, not committed).

## 🔵 2026-07-14 — "dex-pool second-writer-path" is this SAME population, not a separate issue; root cause identified

A separate scoping pass (started to size a suspected distinct ~100K-400K-object "second-writer-path" migration) found
fresh real numbers that corroborate this doc almost exactly and confirm it is **the same population, not a different
one**: hive shape `day={D}/pipeline_mode=batch_instruments_service/asset_group=defi/venue={V}/instruments.parquet` =
**103,944 objects / 2,353 distinct days, frozen 2020-01-20→2026-06-29**; flat shape = **74,947 objects / 2,368 days,
still live through today**. Matches this doc's "~104K" / "2,353 days" figures exactly — no separate migration item
exists, and no VM-scale migration/deletion job should be scoped for it.

**Root cause, now identified**: the hive tree is not an accidental duplicate writer — it's a **frozen, partially-run
snapshot of the v9 canonicalization migration** (`instruments-service/scripts/migrate_instruments_store_v9.py`,
`# Lifecycle: oneoff`). That migration's ownership moved from the archived
`instruments_manifest_canonicalisation_2026_06_01.md` (status: complete, folded 2026-06-26) to the currently **active**
`plans/active/instruments_mtds_subset_consistency_remediation_2026_06_17.md`, whose "reader cutover DONE" covers
`raw_tick_data`/deployment-api drilldown only — **not** `instrument_availability/defi`. The live daily writer
(`instruments_service/engine/orchestrator/writers.py::_write_venue`, confirmed single-write, no dual-write) only ever
wrote the flat shape; the hive copy simply stopped advancing when the v9 migration run stalled at day=2026-06-29.

**This reframes the fix**: not a bounded copy/backup/delete job, but (a) a **reader-preference bug/decision** in
`market_tick_data_service/instrument_availability_paths.py::match_instruments_blob` (hive-wins is very likely wrong
given hive is stale-and-frozen while flat is live — strong evidence now, still an explicit operator call per this doc's
existing NO-GO/operator-decision stance, not unilaterally changed here), and (b) either finishing the v9 migration's
real cutover for this specific tree under `instruments_mtds_subset_consistency_remediation_2026_06_17.md`, or
abandoning/deleting the stale hive snapshot once (a) is resolved and flat is confirmed the sole reader target. No new
plan needed for this — it folds into the already-active v9-remediation plan once the operator decision lands.
