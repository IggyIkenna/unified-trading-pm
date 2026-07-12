---
doc_type: issue
title: TradFi manifest — 1.02M distinct rows disappeared from _index between 2026-07-10 and 2026-07-12 (unexplained)
summary:
  The tradfi-prd `_index/availability_index.parquet` lost 1,017,024 distinct manifest rows (by natural key) between the
  2026-07-10T11:33Z snapshot (6,107,337 rows) and a fresh read on 2026-07-12T03:34Z (5,088,405 rows). Root cause NOT yet
  identified — ruled out `cleanup_legacy_twins.py` (reads manifest, never writes it) and ruled out a benign natural-key
  dedup (distinct-key count also dropped by ~1.02M, not just raw row count). This blocks `tradfi_v9_stage1_finish` task
  4 (manifest rebuild) and calls into question every downstream gate that reads this manifest (task 2 orphan-sweep E=0,
  task 7 EU-seed, task 8 IS catalogue) since all were certified against a manifest that has since silently lost
  coverage.
status: open
resolved_by:
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [tradfi, manifest, data-correctness, regression, row-loss, big-finding]
related:
  [
    tradfi_v9_stage1_finish_2026_07_06.md,
    tradfi_manifest_canonicalisation_2026_06_01.md,
    migration_verification_orphan_safety_2026_06_10.md,
  ]
created: 2026-07-12
source:
  - tradfi_v9_stage1_finish_2026_07_06.md task 4 dispatch (slot-8 sonnet/high)
assigned_vm: planning
assigned_role: data_engineering
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.5
drift_direction: advance-code
parent_epic: instruments_master
execution_scope: orchestrator-agent
depends_on: []
last_updated: 2026-07-12
locked_by:
locked_since:
---

# TradFi manifest — 1.02M-row disappearance between 2026-07-10 and 2026-07-12

> **🔴 BIG FINDING — data-correctness regression, NOT fixed this session.** Filed by slot-8 (sonnet/high) while
> dispatched to `tradfi_v9_stage1_finish` task 4 (E5 manifest rebuild). Re-verifying task 4's gate surfaced this instead
> of the expected "same 13,971-row v4 tail, still waiting on fleet-drain" state from the prior 3 sessions. **This
> FREEZES confident progress on task 4/task 11/task 2-dependent work for tradfi** until root-caused — every downstream
> gate this plan certified GREEN (orphan-sweep E=0, EU-seed 0-unseeded, IS catalogue freshness) was certified against a
> manifest state that has since silently shrunk by ~1M rows, so those certifications can no longer be trusted without a
> re-check.

## What I found

Dispatched to `tradfi_v9_stage1_finish_2026_07_06.md` task 4 ("Rebuild the tradfi manifest"). Per the plan's own
history, the E5 rebuild tool already ran to completion 2026-07-07 and the only known-remaining gap was a static
13,971-row `schema_version=4` tail gated on task 10 (fleet-drain). Re-verified fleet-drain state first (still FALSE —
see below), then re-read the manifest to confirm the tail count was unchanged, as the last 3 sessions had done. It was
NOT unchanged — the corpus itself had shrunk.

**Fleet-drain state (re-confirmed, 2026-07-12T03:3x UTC, via direct Compute API — `gcloud` is broken in this slot per
the documented snap-confine issue, same as every prior session)**: 8 `tradfi-bf-*` VMs still `RUNNING` in
`asia-northeast1-c` (`tradfi-bf-cboe-ohlcv-1m-vx-2026-*`, `tradfi-bf-cme-ohlcv-1m-{cl,es,gc,hg,ng,nq,si}-2025-*`, launch
timestamps 2026-07-11/07-12 — i.e. the fleet has been cycling, not draining). Task 10 remains correctly
BLOCKED-PREREQUISITES; unchanged from the 2026-07-10 finding.

**Manifest row-count comparison** (`market-data-tick-tradfi-prd-central-element-323112`, read via UTL
`StorageClient.download_bytes` — `gcloud`/`gsutil` both broken in-slot):

| Snapshot                                                                                                                                  | Read at           | Total rows     | `schema_version=9` | `schema_version=4` (v4 tail) |
| ----------------------------------------------------------------------------------------------------------------------------------------- | ----------------- | -------------- | ------------------ | ---------------------------- |
| `_index/snapshots/pre_tradfi_source_restamp_20260710T113305Z.parquet` (last verified-fresh snapshot, used for the 2026-07-10 E7 re-audit) | 2026-07-10T11:33Z | 6,107,337      | 6,093,366          | 13,971                       |
| `_index/availability_index.parquet` (live, fresh — `get_blob_metadata` confirms `last_modified=2026-07-12T03:34:03Z`, not stale/cached)   | 2026-07-12T03:34Z | 5,088,405      | 5,074,434          | 13,971                       |
| **Delta**                                                                                                                                 |                   | **-1,018,932** | **-1,018,932**     | **0 (unchanged)**            |

The v4 tail is byte-identical in count to the 2026-07-08/07-10 readings — that specific population is untouched. The
loss is entirely within rows that WERE `schema_version=9` (`captured`/`empty_confirmed` rows), i.e. rows the plan had
already certified as canonical and correctly captured.

**`capture_status` breakdown of the loss** (old → new):

| `capture_status`       | 2026-07-10 | 2026-07-12 | delta    |
| ---------------------- | ---------- | ---------- | -------- |
| `empty_confirmed`      | 3,352,487  | 3,037,867  | -314,620 |
| `captured`             | 2,326,685  | 1,620,804  | -705,881 |
| `attempted_failed`     | 343,079    | 342,211    | -868     |
| `expected_unattempted` | 85,086     | 87,523     | +2,437   |

Real `captured` rows (actual object-backed manifest entries) account for the majority of the loss (705,881 of 1,018,932)
— this is not a cosmetic honest-absence-bookkeeping change.

**Ruled out — natural-key duplicate collapse (benign explanation)**: computed a natural key
(`date, venue, asset_group, data_type, instrument_type, underlying, instrument_id, pipeline_mode`) on both snapshots.
Distinct-key count ALSO dropped by the same order of magnitude (5,723,660 → 4,711,672, a drop of 1,011,988) — if this
were merely deduplication of previously-duplicated rows, the distinct-key count would be unchanged or would have
INCREASED as a share of total rows, not dropped by nearly the same amount as the raw row count. **Direct key-set diff
confirms it definitively**: 1,017,024 keys present in the 2026-07-10 snapshot are absent from the 2026-07-12 read (only
5,036 new keys were added in the same window — consistent with the ~97K rows whose `written_at` falls after 2026-07-10,
the expected live-writer trickle, not a rebuild). Sample of missing keys spans multiple venues (CME, NYSE confirmed in a
random sample), multiple `data_type`s (`ohlcv_1s`, `ohlcv_1m`), and a wide date range (2021-01 through 2026-03) — this
is a broad, corpus-wide loss, not an isolated shard or a single bad write.

**Ruled out — `cleanup_legacy_twins.py --apply` (the operator-gated bucket-delete this plan explicitly HARD-STOPs on)**:
found a NEW, previously-undocumented artifact `_index/audit/legacy_dup_delete_list_tradfi.parquet` (1,706,332 rows,
`SAFE-TO-DELETE` classification) — this is `cleanup_legacy_twins.py --dry-run`'s own report output (task 11's sanctioned
prep step, never `--apply`). Read the script source directly (`instruments-service/scripts/cleanup_legacy_twins.py`): it
only calls `client.delete_blob()` on GCS objects and `client.download_bytes()` to READ the manifest for twin
verification — **it has no code path that writes to `_index/availability_index.parquet`**, so even an (unauthorized)
`--apply` run of this specific tool cannot explain manifest rows disappearing. Confirmed via `grep` for
`upload_bytes`/`ManifestWriter`/`to_parquet` in the file — zero hits.

**`written_at` distribution of the surviving 5,088,405 rows**: the bulk (3.37M rows) still carries `written_at` from
2026-07-07 (the original E5 rebuild day); only ~96,924 rows carry a `written_at` after 2026-07-10. This rules out "a
fresh full rebuild overwrote the index with a smaller correct result" — a full rebuild would stamp a fresh `written_at`
on every row it (re-)emits. Instead, the OLD rows (with their original `written_at` preserved) are simply gone from the
new file — consistent with some process reading the main index, dropping ~1M rows via an incorrect
filter/anti-join/merge, and writing the result back over the same object path, rather than a legitimate full-corpus
rebuild.

**Venue/data_type/date breakdown of a 200K-row sample of the missing keys** (confirms broad corpus-wide scope, not one
bad shard): venues
`CME=114,023 · NYSE=56,788 · NASDAQ=26,990 · CBOE=1,419 · KRX=316 · YAHOO_FINANCE=237 · ICE=136 · FX=91`; `data_type`
`ohlcv_1s=114,625 · ohlcv_1m=84,777 · ohlcv_24h=354 · ohlcv_15m=237 · trades=7`; date range `2019-01-05` through
`2026-07-02`. Sample `capture_status`: `captured=138,099 · empty_confirmed=61,737 · attempted_failed=164` (proportions
consistent with the full-corpus delta table above). Every major venue and a 6-year date span is represented — this rules
out a single misconfigured shard or a narrow-range bad write.

**Not yet identified**: which script/job actually performed the write. This slot has no `gcloud`/`gsutil` access
(snap-confine) and therefore no Cloud Logging / Cloud Run job history visibility to identify the writer process or
another slot's in-flight session. This needs either (a) an operator/main-agent check of Cloud Logging for writes to
`gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` around
2026-07-10T11:33Z–2026-07-12T03:34Z, or (b) checking other active slots' sessions/commits for any manifest-editing
script run against tradfi in that window.

## Why it matters

- This is the SAME manifest every other checkbox in `tradfi_v9_stage1_finish_2026_07_06.md` certified against: task 2's
  orphan-sweep `E=0` (certified 2026-07-10T17:17Z, i.e. BEFORE this loss — may no longer hold if the missing rows
  correspond to canonical objects that now have no manifest row, which is exactly the orphan-sweep's Class-E
  definition), task 7's EU-seed "0 unseeded candidates" (certified against a manifest that has since lost ~1M rows), and
  task 8's IS catalogue freshness (built from `by_date/` snapshots, likely also affected).
- Per workspace HARD RULE ("Data pipeline correctness is the heartbeat" — a RED data audit FREEZES layer-N+1 work): this
  is exactly that class of finding. Task 4 cannot be meaningfully progressed (rebuilding on top of a manifest that is
  actively losing rows for an unknown reason risks compounding the problem or masking it).
- Task 11 (legacy-twin bucket deletes) is especially sensitive here — its own `--dry-run` safety check (`is_deletable`
  requiring "canonical twin captured in manifest") depends on manifest completeness; if the MANIFEST itself is silently
  losing captured rows, a future dry-run could misclassify a legacy object as safe-to-delete when its canonical twin's
  manifest row has been (incorrectly) dropped — even though task 11 stays operator-gated for the actual delete, its prep
  evidence quality depends on this being fixed first.

## Recommended decision

1. **Operator/main-agent: identify the writer.** Check Cloud Logging / Cloud Run revision history for
   `market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` writes in the window
   2026-07-10T11:33Z–2026-07-12T03:34Z (this slot cannot — `gcloud` broken). Cross-check whether another slot ran a
   manifest-editing script against tradfi in that window (dedup attempt, consolidator code change, etc).
2. **Do NOT run task 4 (E5 rebuild) again until root-caused** — re-running the rebuild on top of an already-lossy index
   could either mask the bug (re-adding the missing rows and hiding the regression) or compound it if the same bug is
   triggered by the rebuild itself.
3. **Do NOT proceed with task 11's `--dry-run` prep** using the current manifest state until this is resolved — its
   evidence quality depends on manifest completeness.
4. Once root-caused: if recoverable from a snapshot (the 2026-07-10T11:33Z snapshot pre-dates the loss and is still in
   `_index/snapshots/`), consider restoring the missing 1,017,024 rows via a targeted re-add rather than a full re-scan,
   to avoid another multi-hour full-corpus operation.

## Todos

- [ ] [DATA] P0. Identify the exact script/job/commit that wrote `_index/availability_index.parquet` for
      `market-data-tick-tradfi-prd-central-element-323112` between 2026-07-10T11:33Z and 2026-07-12T03:34Z (repo:
      unified-trading-pm / operator — needs Cloud Logging access this slot lacks).
- [ ] [DATA] P0. Once the writer is identified, root-cause why it dropped 1,017,024 distinct manifest rows
      (`captured`=-705,881, `empty_confirmed`=-314,620) while leaving the 13,971-row v4 tail untouched, and fix the
      underlying script/consolidator bug (repo: market-tick-data-service or instruments-service, whichever owns the
      identified writer).
- [ ] [DATA] P0. Restore the 1,017,024 missing rows — either replay them from
      `_index/snapshots/pre_tradfi_source_restamp_20260710T113305Z.parquet` (targeted re-add of exactly the missing
      keys, verified via the same key-set diff this issue doc used) or via a fresh full E5 rebuild once the root cause
      is fixed and confirmed non-recurring (repo: market-tick-data-service).
- [ ] [DATA] P1. Re-run task 2's orphan-sweep (`migration_orphan_sweep.py --asset-group tradfi`) after the restoration
      to re-confirm `orphan_class_E=0` still holds — the 2026-07-10T17:17Z GREEN certification may not survive against
      the current (or restored) manifest state (repo: instruments-service).
- [ ] [DATA] P2. Add a row-count sanity check (delta vs. the last known-good snapshot, alert on any drop >0.1%) to
      whichever job writes `_index/availability_index.parquet`, so a future regression of this class is caught
      immediately rather than 2 days later by an unrelated task's re-verification (repo: market-tick-data-service or
      unified-trading-library, wherever the writer/consolidator lives).

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-12** — Filed by slot-8 (sonnet/high), dispatched to `tradfi_v9_stage1_finish` task 4. Full characterization
  above; root cause NOT yet identified (needs Cloud Logging access this slot lacks). No code change — this is a
  data-state finding, no repo commit for this entry (issue doc itself ships via the PM `docs(plans):` carve-out).
