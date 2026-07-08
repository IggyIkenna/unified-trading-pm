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
- [x] ✅ [DATA] P1. Correct the misleading module docstring (`unified_trading_library/manifest_consolidator.py:38-40`) —
      it cites `ManifestWriter._write_with_generation_match`, which the consolidator never calls; replace with an
      accurate description of `_write_consolidated`'s actual (buggy, pending the P0 fix above) retry behavior, updated
      again once the fix lands (repo: unified-trading-library). — unified-trading-library@84528344 (slot-4 sonnet/high).
      Docstring now accurately states the CAS retry re-uploads the same stale payload without re-merging (a lost-update
      race, linked to this issue doc) and corrects the wrong function citation; will need a follow-up edit once the P0
      fix above ships.
- [ ] [DATA] P1. Once the P0 fix ships, re-run this doc's reproduction (15-cell sample query against
      `instruments-store-sports-prd-central-element-323112`'s canonical index) to confirm the specific understat
      XG/XG_SHOTS duplicate cells collapse to one row each, then re-verify item #4's gate in
      `plans/active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md` (repo: unified-trading-pm, plan
      file).
- [x] ✅ [DATA] P2. **Audit other high-write-concurrency buckets — COMPLETE 2026-07-08 (slot-3 sonnet/high).** Audited
      the 3 named `market-data-tick-{ag}-prd-central-element-323112` canonical indices directly (ONE bounded
      `_index/availability_index.parquet` object read per bucket via UTL `get_storage_client().download_bytes` — not a
      corpus walk; single-walk discipline held; PyArrow column-pruned to the dedup-key + status columns, held in memory
      only, no disk write, to avoid the shared host's small `/tmp` tmpfs which hit ENOSPC mid-run from other slots'
      concurrent activity). Grouped by the CONSOLIDATOR'S OWN dedup key (`_BASE_DEDUP_COLS` + `_OPTIONAL_DEDUP_COLS`
      present in the schema, `coalesce(nullif(cast(col AS VARCHAR), ''), sentinel)` — mirrors `_dedup_key_sql` exactly,
      both NULL and `''` collapse to the same sentinel) via memory-bounded DuckDB (`memory_limit=6GB`, spill directory
      pointed at `/home` — the large disk-backed partition — not the tiny `/tmp` tmpfs). - **cefi**
      (`market-data-tick-cefi-prd-...`, 7,219,598 rows): **0 duplicate dedup-key groups. CLEAN.** - **defi**
      (`market-data-tick-defi-prd-...`, 13,766,590 rows): **0 duplicate dedup-key groups. CLEAN.** - **tradfi**
      (`market-data-tick-tradfi-prd-...`, 6,022,040 rows): **1,023,968 duplicate dedup-key groups, spanning 2,047,936
      rows — 34.0% of the entire canonical index.** This is a MUCH larger instance of the same bug than the sports
      diagnosis (which found 9/15 sampled cells affected) — confirmed via full-population GROUP BY, not sampling.
      Verified the row-level fingerprint on 3 concrete sample dup-keys matches the sports root cause exactly (an OLDER
      row's `capture_status`/`error_reason` persisting alongside a NEWER row for the identical dedup key, instead of the
      newer row correctly superseding it per last-write-wins): - `(2026-06-01, NASDAQ, ohlcv_1s, AXTI)`:
      `empty_confirmed/SOURCE_RETURNED_ZERO` written 2026-06-28T00:46Z COEXISTS with
      `attempted_failed/WithinBoundsTradfiSourceZero` written 2026-07-07T07:28Z (9 days newer). -
      `(2023-09-18, NASDAQ, ohlcv_1m, BAC)`: same pattern — `empty_confirmed/SOURCE_RETURNED_ZERO` (06-28) coexists with
      `attempted_failed/WithinBoundsTradfiSourceZero` (07-07). - `(2024-12-10, NASDAQ, ohlcv_1s, KLAC)`: BOTH rows are
      `captured` (blank error_reason) from two SEPARATE write events (06-28 and 07-07) — the older `captured` row should
      have been collapsed by the newer cycle's merge but wasn't, so the dedup violation isn't limited to status-flip
      cells; even same-status re-writes duplicate. - **Why tradfi and not cefi/defi (plausible, not proven)**: tradfi
      has had exceptionally dense overlapping consolidation-cycle activity today and over the past ~10 days — the 7-VM
      v9 canonical migration (this plan's task 1), the E5 `rebuild_tradfi_manifest.py` full-corpus rebuild (task 4, ran
      2026-07-07 for 785s writing 1.52M+ additions), the CF-4 source-restamp `--apply` (2026-07-08), and multiple
      straggler re-run VMs — all writing shards to the SAME bucket in tight, overlapping windows, which is exactly the
      race's precondition (cycle A reads canonical, cycle B writes first, cycle A's CAS retry re-uploads its now-stale
      merge). cefi/defi did not have comparably dense overlapping-cycle activity in this snapshot, so their absence of
      duplicates is consistent with the race being probabilistic (requires two cycles racing), not a bucket-specific
      immunity — it does NOT mean cefi/defi are structurally safe from this bug once they see similarly dense concurrent
      activity (e.g. a future multi-VM cefi/defi backfill or manifest rebuild). - **Not audited this pass (explicit
      scope note, not a silent cap)**: the sibling `instruments-store-{ag}-prd-...` buckets (IS catalogue /
      enumerate-seed side, same consolidator code path, same race is structurally possible) were not checked — this pass
      covered the 3 named `market-data-tick-{ag}-prd-...` buckets per the task's literal scope. Flagging as a candidate
      follow-up, not filing a separate todo for it (P2 audit, already over its 1h estimate; the P0 fix in item #1 is the
      actual remediation regardless of which buckets are affected). - **Escalation**: this is a "big finding" per the
      data-correctness HARD RULE (quantified data-correctness bug, cross-repo, changes the scale understanding of item
      #1's urgency) — surfacing here rather than a new issue doc since item #1 (the P0 fix) already exists and is the
      correct remediation target; this entry supplies the quantified evidence that tradfi specifically needs
      re-verification (task 4/6 in `tradfi_v9_stage1_finish_2026_07_06.md`, both already unflipped/RED) once item #1
      ships — the 34% duplicate-row rate materially affects any row-count-based percentage those tasks compute (e.g.
      CF-1's 99.77% v9 figure, CF-4's blank-source counts) since duplicated cells double-count in a naive `COUNT(*)`.
      unified-trading-pm@(this commit).
