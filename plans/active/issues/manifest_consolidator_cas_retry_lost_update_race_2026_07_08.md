---
doc_type: issue
title:
  manifest consolidator's CAS-retry loop re-uploads a STALE already-computed merge on PreconditionFailed instead of
  recomputing — a lost-update race that leaves dedup-key-colliding rows coexisting in the canonical index
summary:
  "Escalated from plans/active/issues/manifest_record_expected_empty_blank_source_2026_07_08.md's 'Open question — dedup
  non-collision'. Confirmed via a direct read of the RAW canonical `_index/availability_index.parquet` (not a read-time
  per-VM-shard overlay artifact — the reader's `_merge_shard_frames` only overlays the CALLING process's own self-shard,
  and this read used a plain pd.read_parquet against the persisted blob) that two rows sharing an IDENTICAL,
  byte-verified dedup key (date, venue='', data_type, service_name='instruments-service', league_id) coexist: an OLD row
  (source='understat', capture_status=expected_unattempted, error_reason='', attempted_at=2026-06-28T21:31:49Z) and a
  NEW row written by today's understat-eu-residual-closer v2 run (capture_status=empty_confirmed,
  error_reason='EXPECTED_NO_FIXTURE', attempted_at=2026-07-08T22:2x-22:4xZ — ~10 days newer). Per the documented
  last-write-wins semantics (ORDER BY attempted_at DESC, written_at DESC) the newer row should have superseded the older
  one during consolidation; instead 9/15 sampled cells show both rows persisted. Root-caused to `_write_consolidated()`
  (unified_trading_library/manifest_consolidator.py): on GCS `PreconditionFailed` (generation conflict — another
  consolidation cycle wrote first), the retry loop only re-fetches the blob generation and re-uploads the SAME
  already-computed `payload` bytes — it never re-runs `_duckdb_consolidate_and_write`'s merge against the fresh
  canonical. This is a classic lost-update race: a losing cycle's stale merge (computed before a concurrent winning
  cycle's write) can overwrite the winner's freshly-deduped canonical with content that never saw the winner's changes,
  silently resurrecting rows the winner had already correctly collapsed. The module docstring's safety claim ('the
  existing 15-retry backoff in ManifestWriter._write_with_generation_match covers it') is itself WRONG — that function
  lives in manifest_writer/_writer_io.py and is unrelated to the consolidator's write path; it is never called by
  `_write_consolidated`. Ironically, `_write_with_generation_match`'s own retry helper (`_try_conditional_write`) IS a
  correct 'one read-merge-write cycle per attempt' — exactly the pattern `_write_consolidated` is missing.
  Cross-cutting: this is a bucket-level race in the shared consolidator, not specific to sports/understat — any
  asset_group bucket with overlapping consolidation cycles (busy multi-slot / multi-VM write days) is exposed."
status: open
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library]
scope: [engineer, admin]
tags: [manifest, manifest-consolidator, data-correctness, dedup, race-condition, cas, honest-absence, sports, understat]
related:
  [
    plans/active/issues/manifest_record_expected_empty_blank_source_2026_07_08.md,
    plans/active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md,
  ]
created: 2026-07-08
parent_epic: sports_master
priority: P0
source: [plans/active/issues/manifest_record_expected_empty_blank_source_2026_07_08.md]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-08
---

## What I found

Dispatched to close the "Open question — dedup non-collision" left by
`manifest_record_expected_empty_blank_source_2026_07_08.md`'s last todo: "if the v2 closer re-run (this session) shows
the old blank-reason rows STILL coexisting alongside new correctly-sourced rows, escalate as its own P0 issue targeting
`unified_trading_library/manifest_consolidator.py`'s DuckDB incremental anti-join."

**Confirmed the coexistence directly against the persisted canonical blob** (not a read-time per-VM-shard-overlay
artifact — `read_availability_index()`'s fast path only merges the CALLING process's own self-shard on top of the cached
consolidated frame per `unified_trading_library/manifest_writer/_read_index.py:318-333`; this check bypassed that
entirely with a plain `pandas.read_parquet("gs://.../_index/availability_index.parquet")`, so what it sees is exactly
the DuckDB consolidator's own persisted output):

```
--- date=2020-05-13 data_type=XG_SHOTS league_id=EPL : 2 row(s) sharing this cell ---
capture_status         error_reason          source  venue  service_name          attempted_at                        written_at
expected_unattempted   ''                    understat  ''  instruments-service   2026-06-28T21:31:49.534565+00:00    2026-06-28T21:31:49.534565+00:00
empty_confirmed        EXPECTED_NO_FIXTURE   ''         ''  instruments-service   2026-07-08T22:29:50.416070+00:00    2026-07-08T22:29:55.926942+00:00
```

Verified byte-for-byte that every `_BASE_DEDUP_COLS` + the populated `_OPTIONAL_DEDUP_COLS` value (`date`, `venue`,
`data_type`, `service_name`, `league_id`) is IDENTICAL between the two rows (`repr()`-checked, not a print-formatting
illusion). Sampled 15 (date, data_type, league_id) cells straight from the still-blank residual set: **9/15 have exactly
this 2-row coexistence** (old blank-reason `expected_unattempted` + a newer, correctly-typed `empty_confirmed`); the
other 6/15 are still single-row (the closer hasn't reached that cell's league/date combination with a typed write yet —
a different, unrelated gap). The newer row is unambiguously from TODAY's `understat-eu-residual-closer-20260708-v2` run
(`attempted_at` in its 22:2x-22:4x UTC run window; `/tmp/understat_eu_residual_closer_v2.log` confirms
`[MAIN] processed=1169 ... raised=0` at 22:47:21 UTC, consolidator merge confirmed by GCS blob size growth 84.7MB →
89.4MB in the same window).

**Root cause — read `_write_consolidated()` (`unified_trading_library/manifest_consolidator.py:1490-1565`)**:

```python
if generation is not None:
    blob.upload_from_string(payload, ..., if_generation_match=generation)
else:
    blob.upload_from_string(payload, ..., if_generation_match=0)
...
except Exception as exc:
    if exc_name == "PreconditionFailed" and attempt < attempts - 1:
        _time.sleep(0.5 * (attempt + 1))
        continue  # <-- retries the SAME `payload` bytes with a fresh generation number
```

`payload` is computed ONCE by `_duckdb_consolidate_and_write()` (the DuckDB merge — canon + changed shards, incremental
anti-join or full window-dedup) BEFORE `_write_consolidated` is even called. When the CAS write hits
`PreconditionFailed` (another consolidation cycle for the SAME bucket wrote a newer generation in between), the retry
loop re-fetches only the blob's current `generation` number via `blob.reload()` and re-uploads the IDENTICAL,
already-stale `payload` — it never re-runs the DuckDB merge against the canonical the winning cycle just wrote. This is
a **lost-update race**: if cycle A (started first, saw an older canonical + a smaller changed-shard set) loses the CAS
race to cycle B (which correctly merged the SAME changed shard and dropped the old duplicate), A's retry does not know
about B's write — it simply re-uploads A's own stale merge onto the NOW-current generation, silently overwriting B's
correct dedup with A's outdated one. The dedup key that B correctly collapsed reappears duplicated because A's stale
`payload` still carries the ORIGINAL (pre-collapse) canonical row for that key.

**The module docstring's safety claim is itself inaccurate** (lines 38-40): "if two cycles race, only one CAS write wins
and the other retries (the existing 15-retry backoff in `ManifestWriter._write_with_generation_match` covers it)."
`_write_with_generation_match` lives in `unified_trading_library/manifest_writer/_writer_io.py` — a DIFFERENT write path
used by the legacy single-blob `ManifestWriter.write()`, not by the consolidator at all
(`grep -rn "_write_with_generation_match"` shows zero callers in `manifest_consolidator.py`). Worth noting: that OTHER
function's own retry helper, `_try_conditional_write` (`_writer_io.py:688-709`), IS implemented correctly — its
docstring says "one read-merge-write cycle" and it genuinely re-reads (`_read_with_generation`) + re-merges
(`_merge_dataframes`) on EVERY attempt before writing. That is exactly the pattern `_write_consolidated` needs and does
not have.

## Why it matters

1. **Cross-cutting data-correctness bug, not sports-specific.** The manifest consolidator
   (`unified_trading_library/manifest_consolidator.py`) is the single canonical-index writer for EVERY asset_group
   bucket (`codex/05-infrastructure/manifest-consolidator-ssot.md`). Any bucket where two consolidation cycles overlap
   in time — plausible whenever multiple VMs/backfills/scripts write per-VM shards to the same bucket close together,
   which is routine on a busy multi-slot day like today — is exposed to this lost-update race, not just
   `instruments-store-sports-prd`.
2. **Silently defeats honest-absence resolution.** The entire point of the source-fix + residual-closer (this plan's
   item #4) was to convert blank-reason `expected_unattempted` seeds into correctly-typed terminal states. This race
   means a fix that DID land correctly at write time can still show up as unresolved in the canonical index — any
   downstream gate query (`pending_fetch == 0`, coverage %, ML NaN-fill denominators) reading the canonical directly
   (not through the self-shard-overlay reader path) can undercount resolution indefinitely, since nothing re-triggers a
   correct merge once a stale one has won the CAS race.
3. **The docstring's safety claim is misleading and should not be trusted going forward** — the "handled, 15-retry
   backoff covers it" note pointed the wrong function; anyone reading the module docstring (as I nearly did) would
   wrongly conclude concurrent-cycle safety is already proven.

## Recommended decision

- [ ] [DATA] P0. Fix the lost-update race in `_write_consolidated()`
      (`unified_trading_library/manifest_consolidator.py:1490-1565`, repo: unified-trading-library): on
      `PreconditionFailed`, RE-RUN the full merge (`_duckdb_consolidate_and_write`, re-reading the canonical at its NEW
      generation + the same changed-shard set) before re-attempting the CAS write — do not re-upload the stale
      `payload`. Mirror the correct pattern already used by `ManifestWriter._try_conditional_write`
      (`unified_trading_library/manifest_writer/_writer_io.py:688-709`, "one read-merge-write cycle" per attempt). Add a
      regression test that simulates two overlapping `consolidate()` calls against the same bucket (mock GCS generation
      bump mid-cycle) and asserts the canonical after both completes contains exactly ONE row per dedup key, not two.
- [ ] [DATA] P1. Correct the misleading module docstring (`unified_trading_library/manifest_consolidator.py:38-40`) — it
      cites `ManifestWriter._write_with_generation_match`, which the consolidator never calls; replace with an accurate
      description of `_write_consolidated`'s actual (buggy, pending the P0 fix above) retry behavior, updated again once
      the fix lands (repo: unified-trading-library).
- [ ] [DATA] P1. Once the P0 fix ships, re-run this doc's reproduction (15-cell sample query against
      `instruments-store-sports-prd-central-element-323112`'s canonical index) to confirm the specific understat
      XG/XG_SHOTS duplicate cells collapse to one row each, then re-verify item #4's gate in
      `plans/active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md` (repo: unified-trading-pm, plan
      file).
- [ ] [DATA] P2. Audit other high-write-concurrency buckets (cefi/defi/tradfi backfills that run many parallel VMs
      against one bucket) for symptoms of the same duplicate-row pattern — this bug is not sports-specific, only
      diagnosed here first (repo: unified-trading-library / instruments-service, scope: cross-asset-group audit).
