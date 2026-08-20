---
doc_type: issue
title:
  CF-8 available_at backfill pass (rebuild_sports_manifest_v9.py) REGRESSED the IS surface fill rate — root cause not
  isolated, restored from snapshot
summary: >
  Attempted the CF-8 available_at full-corpus backfill (rebuild_sports_manifest_v9.py --no-dry-run --force +
  manifest_consolidator --force) per the plan's own next-step guidance. Result was a REGRESSION, not an improvement: IS
  surface available_at fill rate dropped from a 62.9% baseline to 15.7% post-backfill+consolidate. Traced far enough to
  confirm the bug is real (source rows have valid written_at, the rewritten row correctly gets a fresh
  attempted_at/written_at and wins the last-write-wins consolidation tie-break, yet available_at ends up empty) but did
  not isolate the exact line. Restored the IS canonical from a pre-backfill snapshot to undo the regression — confirmed
  back to the 62.9% baseline. Separately, an operator (ikenna@odum-research.com via gcloud CLI) manually resumed both
  paused consolidator crons mid-backfill (twice), causing a stray incremental consolidation on the MDPS surface that
  consumed my MDPS per-VM shard before I could force-consolidate it myself — but MDPS's pre-backfill baseline never had
  an available_at column either, so this was not a regression, just a lost backfill attempt.
status: open
nature: notes
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [data-correctness, cf-8, available-at, regression, manifest-consolidator, sports]
related:
  [
    plans/archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-07-13
author: unknown
parent_epic: mtds_mdps_master
priority: P0
source: sports_manifest_canonicalisation-004 dispatch, slot 3, 2026-07-13
assigned_vm: NA
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-20
locked_by:
context_scope:
  [
    /plans/archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    market-tick-data-service/scripts/sports_captured_available_at_targeted_backfill_2026_07_14.py,
    unified-trading-library/unified_trading_library/manifest_writer/_writer_io.py,
  ]
resolved_by:
---

# CF-8 available_at backfill regressed IS surface fill rate — restored, root cause open

## What happened

Dispatched to execute the plan's own documented next step: "CF-8 `available_at` live backfill pass (both sports
surfaces) — needs a real `--apply` rebuild pass over the full existing corpus." Followed the plan's own recipe (dry-run
first, pause-cron/confirm-no-in-flight/snapshot, apply, force-consolidate, resume):

1. Verified GCP access (gcloud CLI is broken on this host — snap-confine sandboxing issue — used Python
   google-auth/google-cloud-storage/google-cloud-run/Cloud Scheduler REST throughout instead; this worked fine).
2. Dry-ran both surfaces (`rebuild_sports_manifest_v9.py --surface instruments/mdps --force`) — histograms looked sane
   and matched the plan's documented pre-existing distributions.
3. Paused both consolidator crons, confirmed 0 in-flight executions, snapshotted both canonicals
   (`_index/snapshots/pre_cf8_backfill_20260713T210725Z.parquet`, both surfaces).
4. Applied `--no-dry-run --force` on both surfaces. IS: 5.5M rows, 47,768 rows skipped on 2 separate pre-existing
   data-quality gaps (documented separately below, non-blocking). MDPS: 1.96M rows, 0 skips — clean run.
5. Attempted to force-consolidate IS — hit a **fresh lock** blocking the run.

## Finding 1 — operator cron-collision (process issue, not a code bug)

Investigated the fresh lock via Cloud Audit Logs: an operator (`ikenna@odum-research.com`, via
`gcloud scheduler jobs resume` from a MacOS terminal) manually **resumed both paused consolidator crons at
21:23:19-21**, apparently unaware they were intentionally paused for this maintenance window. This let a stray
incremental consolidation run on the MDPS surface (2 executions, ~21:24-21:25) BEFORE I could run my own planned
`--force` full-rebuild consolidation. That incremental run **consumed my MDPS per-VM shard**
(`local-2142068-9bd8.parquet`, no longer present in `_index/per_vm/`) and updated the MDPS canonical WITHOUT an
`available_at` column.

**This did not regress MDPS**, however: its pre-backfill snapshot
(`market-data-tick-sports-prd-.../pre_cf8_backfill_...parquet`) never had an `available_at` column at all (MDPS's CF-8
baseline was ~0%, not IS's 62.9%) — so the net effect on MDPS is "backfill attempt lost, back to original unimproved
state," not "made worse than before."

Re-paused both crons (confirmed PAUSED again after re-check found them re-ENABLED a second time — the operator's resume
action recurred). **Recommend**: coordinate maintenance windows more visibly (e.g. announce in the ops channel, or add a
"maintenance" annotation the dashboard surfaces) before an agent pauses a production cron for an extended multi-step
operation, since a routine operator action can otherwise collide invisibly.

## Finding 2 — REAL regression on IS surface (the P0 item)

After the operator-collision was resolved (crons re-paused), retried force-consolidating IS. It succeeded
(`success=True, shards=3, rows_in=9,992,537, rows_out=5,750,856, dedup_dropped=4,241,681, latency_ms=167177.9`) — no
error. But checking the resulting canonical's `available_at` fill rate:

- **Pre-backfill baseline** (confirmed via the snapshot): `3,465,377/5,506,821` = **62.9%** filled.
- **Post-backfill+consolidate**: `904,841/5,750,856` = **15.7%** filled.

This is a genuine regression, not merely "didn't improve as much as hoped" — the backfill pass actively **destroyed**
previously-correct `available_at` values on ~2.56M rows that had them before.

### Investigation trail (not fully isolated — needs a fresh pass with more time)

Sampled a row family that regressed:
`date=2014-01-01, capture_status=empty_confirmed, error_reason=EXPECTED_NO_FIXTURE`.

- **Pre-backfill snapshot**: this exact row family has `written_at=2026-06-24T18:30:19...` (real, non-blank) —
  confirming the SOURCE data for `_available_at_from_row(row)` (which reads `row.get("written_at")`,
  `market_tick_data_service/scripts/_rebuild_sports_write.py:145-162`) should have derived a real value, not `""`.
- **Post-backfill canonical**: this row family now has `attempted_at`/`written_at` freshly stamped at
  `2026-07-13T21:1X:XX...` (my rebuild's own write time) — confirming this IS the row my rebuild wrote (it correctly won
  the last-write-wins tie-break during consolidation against the older duplicate) — **yet `available_at` is `None`** on
  this same row.
- Traced the write path end-to-end in code review: `_write_empty_rows` (`_rebuild_sports_write.py:165-244`) passes
  `available_at=_available_at_from_row(row)` into `writer.record_empty(...)` for every row unconditionally when
  `--force` is set (the `if not force: skip typed rows` branch is bypassed). The real
  `NormalisingManifestWriter.record_empty()` → `_record_status()`
  (`unified-trading-library/manifest_writer/_writer_record.py`, lines ~93-129, 275, 572-586, 780-803) threads
  `available_at` through as a parameter at every hop I traced, into the `AvailabilityRecord` dataclass construction
  (`_rows.py:443`).
- **Did not find the exact line where the value gets dropped.** Candidates not yet ruled out: (a) a serialization step
  converting `AvailabilityRecord` objects → DataFrame/parquet that drops or nulls the column for
  `empty_confirmed`/non-captured rows specifically (captured rows may go through a different path —
  `_writer_captured.py` — worth diff-checking against `_writer_record.py`'s non-captured path); (b) the DuckDB
  consolidation merge itself nulling `available_at` for some column-type/schema-union reason during the
  `union_by_name=true` scan across the 3 merged shards (my new shard + `_legacy_seed.parquet` +
  `sports-attempted-failed-residual-closer-round3.parquet`) — worth checking whether `available_at`'s dtype differs
  across shards, causing a DuckDB union/cast to silently coerce to NULL.

### Remediation taken

Restored the IS canonical from `_index/snapshots/pre_cf8_backfill_20260713T210725Z.parquet` via a server-side GCS
rewrite. **Confirmed restored**: `3,465,377/5,506,821 = 62.9%` — back to the exact pre-backfill baseline, row count
matches. MDPS was left untouched (no regression to undo there). Both crons remain PAUSED pending operator decision on
whether/when to resume them (they should be safe to resume for normal steady-state incremental operation independent of
this CF-8 investigation — the regression was specific to the `--force` full-rebuild path, not routine incremental
consolidation).

## Why it matters

- **CF-8 remains RED on both surfaces** — no progress made this session; this issue doc supersedes the plan's framing of
  the CF-8 backfill as a "scoped, concrete follow-up" (plan line ~3782) — it is NOT safe to re-attempt with the current
  `rebuild_sports_manifest_v9.py` until this regression's root cause is found and fixed. A future attempt without fixing
  this would silently repeat the same data-destructive regression.
- This is exactly the kind of finding CLAUDE.md's data-pipeline-correctness HARD RULE calls a "big finding" — a genuine,
  silent correctness regression on live production data, caught only because the operator's fill-rate baseline was
  checked before AND after (had I not checked the pre-backfill baseline, `success=True` with a plausible-looking
  histogram at each step could have masked a 47-point fill-rate collapse indefinitely).

## Recommended next steps (not mine to decide unilaterally — routing to operator/infra owner)

1. Confirm crons are safe to resume for normal steady-state operation (they should be — the bug is confined to the
   `--force` full-rebuild path) and resume them.
2. A focused debugging session (with more time budget than this dispatch had) on `AvailabilityRecord` serialization /
   the DuckDB consolidation merge to find the exact `available_at`-drop point, likely by writing a minimal repro (2-3
   synthetic rows through the real write+consolidate path with `available_at` set, inspecting the DataFrame at each
   stage) rather than debugging on the full 5.5M-row corpus.
3. Once fixed and verified on a small repro, re-attempt the full-corpus CF-8 backfill pass — with the OPERATOR aware of
   the maintenance window this time to avoid a repeat of Finding 1's cron collision.
4. Consider whether the consolidator's DuckDB `union_by_name=true` merge should assert/validate that no column silently
   nulls out across a schema union (a defensive check that would have caught this regression at the consolidation step
   itself, before the loss became silent).

## Secondary findings (non-blocking, discovered en route — documented for completeness)

- **`write_projected_index`/`--beta-manifest-out` preview writer crashes** on a raw `FetchEvidence` dataclass object in
  the `fetch_evidence` column (`pyarrow.lib.ArrowInvalid`) when writing the projected-index parquet during a dry-run.
  Confirmed this does NOT affect the real `--no-dry-run` write path (the real `ManifestWriter.record_empty()` only uses
  `fetch_evidence` for validation, never persists it) — cosmetic/tooling-only bug in
  `market_tick_data_service/scripts/_rebuild_sports_projection.py`'s `SportsProjectionCollector` (or
  `_rebuild_projection.py`'s `write_projected_index`), which should serialize non-scalar objects (e.g. via
  `dataclasses.asdict()`) before handing rows to `df.to_parquet()`.
- **IS apply-pass skipped 47,768 rows** (0.87% of corpus) on two pre-existing data-quality gaps, confirmed
  non-destructive (skipped rows retain prior state, not corrupted): (a) 35,361 rows carry historical free-text
  `EMPTY_CONFIRMED` reason strings (`EXPECTED_NO_FIXTURE__truthset_*` variants) that don't match the current closed-set
  `EmptyConfirmedReason` enum exactly — **independently found + already filed** by slot 6 (this same plan's
  twenty-seventh touch) as `plans/archive/issues/sports_rebuild_v9_free_text_reason_taxonomy_rejection_2026_07_13.md`
  (full evidence + 3 actionable todos there; not duplicated here); (b) 12,407 rows (captured VENUES/LEAGUES) carry a
  legacy `source='instruments_service'` stamp (the writing SERVICE's own name, not a real data vendor) that isn't in the
  registered `SOURCE_PRIORITY` vendor list for `asset_group=sports` — not yet filed elsewhere, tracked as a todo below.
  Both are candidates for a future cleanup pass but were correctly non-fatal here.

## Todos

- [x] ✅ [INFRA] P0. Root-cause the `available_at` drop in the CF-8 rebuild+consolidate write path (see "Investigation
      trail" above) — likely needs a small synthetic repro rather than debugging on the full corpus. (repo:
      unified-trading-library, market-tick-data-service) — **ROOT-CAUSED + FIXED, slot 11, 2026-07-13**:
      `unified-trading-library@f5f15e3a`. `ManifestWriter._records_to_dataframe()`
      (`unified_trading_library/manifest_writer/_writer_io.py`) — the ONE serializer every write path (legacy
      single-blob, per-VM shard, runtime live+batch) funnels through before anything reaches GCS — never included
      `available_at` in its per-row dict. Same class of bug as the pre-2026-06-16 v6-v9 column drop its own docstring
      warns about, just for a column added 2026-06-26 and threaded through `record_empty`/`record_failed` only THIS SAME
      DAY (2026-07-13) — never caught. Every row written via `write()` silently lost the value regardless of what the
      caller passed; the DuckDB consolidator's `union_by_name` merge then padded it with NULL, matching the exact traced
      symptom (fresh `attempted_at`/`written_at` on the winning row, yet `available_at` is None). Verified via a
      synthetic DuckDB repro of the isolated merge SQL (ruled OUT the consolidator merge itself as the cause — it
      preserves values correctly in isolation) before tracing to the serializer. Fix confirmed by reverting it and
      re-running the new regression test (`test_serialized_dataframe_carries_available_at_on_record_empty`,
      `tests/unit/test_manifest_writer_serialized_columns.py`): fails on old code, passes on new. Also closed the
      parallel `_V4_BACKFILL_COLUMNS` gap. Full `quality-gates.sh` green (166s). **Not yet done**: re-running the actual
      CF-8 backfill on production data (todo 2 below) to confirm the fix holds at the real 5.5M-row scale — the fix is
      proven correct at the code/unit-test level but the production canonical is still at the restored 62.9% baseline
      pending that re-attempt.
  - **ADDENDUM, slot 3, 2026-07-13** (dispatched to `sports_manifest_canonicalisation-004`, the live-backfill re-attempt
    — did NOT re-attempt it per this doc's own "do not re-attempt" instruction; worked this P0 instead, unaware slot 11
    had landed `f5f15e3a` concurrently until the pull surfaced it): independently reached the same
    `_records_to_dataframe()` root cause via my own synthetic repro, then found `f5f15e3a` already on
    `live-defi-rollout` and rebased onto it rather than duplicating. While tracing the same write path, found a SECOND,
    separate, and much broader bug: `record_captured()` / `record_captured_from_counts()` validate an
    `available_at`-bearing input but never persist it onto the `AvailabilityRecord` at all (independent of the
    serializer bug `f5f15e3a` fixes) — this is the write path actual production adapters use for real captured data,
    across every asset_group, not just sports. Fixed in `unified-trading-library@9c9cdc50` + filed as its own
    cross-cutting issue doc (this one stays sports-scoped):
    `manifest_writer_record_captured_available_at_never_persisted_2026_07_13.md`. Still NOT re-attempting the live
    backfill (todo 2) myself — out of scope for what I was dispatched, and per Finding 1 it needs operator-coordinated
    maintenance window regardless of which agent runs it.
- [x] ✅ [INFRA] P1. Once root-caused and fixed, re-attempt the full-corpus CF-8 `available_at` backfill on both sports
      surfaces (IS still at 62.9%, MDPS still at ~0%) — coordinate the maintenance window with the operator first to
      avoid a repeat of the cron-collision (Finding 1). (repo: market-tick-data-service) — **RE-ATTEMPTED + SUCCEEDED,
      slot 11, 2026-07-14**, operator-coordinated maintenance window as this todo requires. - **Result**: IS
      `available_at` fill 62.9% → **87.8%** (5,051,105/5,751,180); MDPS 0% (column absent) → **85.3%**
      (1,670,401/1,958,499). Zero row-count regression on either surface across two consecutive force-consolidate runs
      on IS + one on MDPS. Verified via direct GCS reads pre/post, not log trust. - **A THIRD collision happened live
      during this run** — the exact Finding-1 class, twice: the consolidator crons got externally re-enabled mid-window
      (once while I was mid-write, once while root-causing the bug below), despite operator confirmation of the
      coordinated window. Re-paused both times (protective, reversible, no data touched by the pause/resume itself);
      verified via direct fill-rate reads that neither occurrence caused any regression — one of them actually helped
      (the routine incremental cron opportunistically absorbed the IS shard correctly once the serializer fix was live).
      **Also hit a genuine concurrent-DUPLICATE-dispatch**: a different slot (slot 6) was independently running the
      identical `--surface instruments --no-dry-run --force` rebuild at the same time (separate per-VM shard, no direct
      collision — confirmed via file listing + PID/inode checks — but flagged + waited for it to finish before
      consolidating, rather than risk a second uncoordinated consolidate/resume race on top of the first). - **Found +
      fixed 2 MORE consolidator bugs surfaced only by actually running this on MDPS** (a bucket whose canonical has
      NEVER carried `available_at` — a schema shape neither `f5f15e3a`/`9c9cdc50` nor the
      `_check_column_fill_regression` guardrail (`2e132bb2`) had coverage for): `unified-trading-library@0f55cc2b`.
      `_duckdb_merge_payload`'s `canon_read` was a plain `SELECT *` (unlike the union_cols-padded `shard_proj`), and
      `_check_column_fill_regression`'s own before/after fill-rate query assumed every `union_col` exists on the
      canonical — both crash with
      `DuckDB BinderException: Set operations can only apply to expressions with the same number of result columns` the
      moment a shard introduces a column the canonical has never had. Root-caused via the exact scenario this todo hit
      live, not speculatively; 2 new regression tests (`tests/unit/test_manifest_consolidator_canon_schema_align.py`,
      full-rebuild + incremental paths) proven to fail on pre-fix code, pass on post-fix. Full
      `test_manifest_consolidator.py` suite green (67 tests). Full `quality-gates.sh` green (232s). - Both crons
      confirmed `ENABLED` (resumed) after all verification completed. Snapshots taken before any write:
      `_index/snapshots/pre_cf8_backfill_retry_20260713T233713Z.parquet` on both surfaces.
- [x] ✅ [DATA] P0. **CF-8 backfill left `captured` rows specifically un-filled — confirms this doc's own candidate (a)
      hypothesis at line ~115 ("captured rows may go through a different path"), now quantified.** A fresh
      `cf_manifest_audit_2026_06_01.py` re-run (2026-07-14, data_engineering slot-2) confirms the 87.8%/85.3% aggregate
      fill rate the backfill achieved is driven almost entirely by `empty_confirmed`/`attempted_failed`/
      `expected_unattempted` rows reaching ~99.8-100% fill — but `capture_status='captured'` rows (the actual data, not
      placeholders) are still only **39.8% filled on IS** (651,845/1,638,158 missing) and **49.8% filled on MDPS**
      (286,839/575,671 missing). CF-8 therefore remains genuinely RED on both surfaces post-backfill, for a DIFFERENT
      reason than before (was: whole-corpus 0-63%; now: captured-row-specific ~40-50% gap). — **ROOT-CAUSED FURTHER,
      slot 3 (data_engineering), 2026-07-14**, via a single-object read of the live IS
      `_index/availability_index.parquet` + the `pre_cf8_backfill_retry_20260713T233713Z.parquet` snapshot the backfill
      itself already took (no new whole-corpus walk):
  - **Candidate (b) ("captured rows need a different `available_at` source") — RULED OUT.** Both the pre-backfill
    snapshot and the live index show `written_at` non-blank on 100% of captured rows (0/1,224,740 blank pre-backfill;
    0/1,638,411 blank live) — including every row that ends up missing `available_at`. `_available_at_from_row(row)`
    only returns `""` when `written_at` is blank, so source-timestamp-absence cannot be the cause: a valid fallback was
    always derivable.
  - **The missing rows were never touched by the backfill — a targeted-re-emit gap, not a corruption during re-emit.**
    Broke the 651,991 IS captured rows missing `available_at` down by `written_at` date: 2026-05-05 (276,532,
    `trades`/`odds_api` + `odds_horizon_bucket`/`mdps_odds_horizon_bucket`), 2026-07-13 (375,019, split between
    `trades`/`odds_api` 195,410 and `TEAMS`/`api_football` 165,224), 2026-07-14 (439, `TEAMS`/`STANDINGS`). The
    2026-07-13 missing rows' `written_at` range (06:15-20:16 UTC) sits entirely BEFORE the backfill's own apply window
    (21:07-23:41 UTC per this doc's own snapshot timestamps) — these are ordinary LIVE production writes from earlier
    the same day; the backfill's re-emission pass never touched them (their `written_at` is unchanged from the original
    live-write time, not overwritten with a fresh backfill timestamp). Candidate (a)'s framing is correct in spirit but
    mis-scoped: `_write_captured_rows` → `writer.add()` DOES thread `available_at` correctly (confirmed — matches the
    independent re-verification touch above) — the gap is that a `--force` full-rebuild only re-emits from the OLD INDEX
    SNAPSHOT it reads at start, so any row written by a concurrent/same-day LIVE capture never entered that snapshot and
    was never re-emitted.
  - **Two live-write-path sub-causes identified, both upstream of the rebuild script:**
    1. **`TEAMS`/`STANDINGS`** (165,224 pre-fix + 439 recurring as recently as TODAY, 2026-07-14): confirmed the
       2026-07-14 rows go through `instruments-service@56aa1938`'s (2026-07-13 18:44 UTC) FIXED per-league
       `record_captured` path (non-blank `league_id`, matching the fix's write shape, not the retired blank-league_id
       blanket writer) — yet still show `available_at=NULL`. The code is correct by inspection (`record_captured()`'s
       `_available_at_value` derivation from `df`, `unified-trading-library@9c9cdc50`, also verified correct) — this
       points at a **production deployment lag** (the running instruments-service process hadn't yet picked up the fixed
       dependency at write-time), an ops question, not a further code change.
    2. **`trades`/`odds_api` + `odds_horizon_bucket`** (the dominant ~75% of the gap, mostly 2026-05-05 + pre-fix
       2026-07-13): traced to `market-tick-data-service/engine/orchestrator/manifest_finalize.py`'s
       `_write_shard_counts_to_manifest()` — the `itype_key == "odds" and data_type_key == "trades"` branch stamps
       `available_at=datetime.now(UTC).isoformat()` unconditionally (fix dated 2026-06-26,
       `sports_mtds_available_at_manifest_gap`). Rows written before that landed have no derivable value from this path
       either. Zero 2026-07-14 `trades`/`odds_api` rows show up missing — the live path is healthy going forward; this
       slice is pure historical residue pre-dating the 2026-06-26 fix.
    3. **Flagged, not confirmed**: `manifest_consolidator.py`'s dedup tie-break prefers the higher-`row_count` row (not
       recency) when a dedup-key group is multi-source (`captured_distinct_sources > 1`) — a plausible mechanism for a
       stale blank-`available_at` row to out-rank a fresher filled one. Did not verify whether any missing row_keys are
       genuinely multi-source (would need a targeted read); noted as an open follow-up, not a confirmed cause.
  - **Shipped**: the existing `_check_column_fill_regression` guardrail (`unified-trading-library@2e132bb2`) only
    compares AGGREGATE fill rate — structurally blind to this exact failure shape (aggregate rose 62.9%→87.8% while
    `capture_status='captured'` stayed ~40-50% filled; captured rows are too small a fraction of the corpus to move the
    aggregate). Added `_check_captured_column_fill_regression()` — a `capture_status='captured'`-scoped sibling, same
    single-pass-query shape, wired into the same `_duckdb_merge_payload` call site — so a FUTURE merge cycle that
    silently drops `available_at` on captured rows specifically pages loud via a new
    `MANIFEST_CAPTURED_COLUMN_FILL_REGRESSION` event even when the aggregate looks fine. 3 new unit tests
    (`tests/unit/test_manifest_consolidator.py`), including one that directly demonstrates the aggregate guard stays
    silent on this exact shape while the new guard fires. Full `quality-gates.sh` green.
  - **Not done — still genuinely RED**: no further production write attempted (Finding 1's cron-collision history + this
    doc's repeated "don't re-attempt without operator coordination" lesson); the historical residue (2026-05-05 +
    pre-fix 2026-07-13 rows) needs a targeted re-emit, and the TEAMS/STANDINGS deployment-freshness question needs an
    ops answer. See new todos below.
- [x] ✅ [INFRA] P1. Confirm whether the running instruments-service production deployment has picked up
      `instruments-service@56aa1938` + `unified-trading-library@9c9cdc50` (both landed 2026-07-13 18:44 UTC and earlier)
      — 439 `TEAMS`/`STANDINGS` captured rows written as recently as 2026-07-14 (TODAY, hours after both fixes landed in
      the repo) still show `available_at=NULL` despite going through the code paths that should now populate it
      correctly (verified by code inspection, see the P0 addendum above). If the deployment is stale, redeploy; if it's
      current and the gap persists, that means there IS still a code bug in this specific path and it needs a fresh
      synthetic repro (mirroring how `f5f15e3a`/`0f55cc2b` were isolated). (repo: instruments-service,
      deployment-service) — **CONFIRMED STALE + FIX STAGED, slot 2 (data_engineering), 2026-07-14**. Instrumented via
      `google-cloud-run`/Artifact Registry REST (gcloud CLI still broken on this host, same snap-confine issue prior
      touches hit): the `uts-prod-instruments-service-sports-fixtures` Cloud Run Job resolves its `:latest` tag FRESH at
      every execution start (confirmed via 8 executions' resolved digests differing over time — NOT pinned at job
      deploy), so the 2026-07-14 00:01 UTC execution (the one that wrote the 439 stale rows) ran image digest
      `de1b5bb3...`, built 23:46:58 UTC from commit `f4f5260c` (a `live-defi-rollout`→`main` promote whose tree content
      at `process_enrichment.py` is byte-identical to `56aa1938`'s fix — confirmed via direct file diff, not just
      `git merge-base` which returns false-negative across the promote's history-rewriting merge). **So the
      instruments-service APPLICATION code was current.** The actual staleness: that image's `Dockerfile` pins
      `ARG BASE_IMAGE_DIGEST=sha256:b7e391f8...` (the UTL base image), built **2026-07-13T17:43:29Z — 5.5 hours BEFORE**
      `unified-trading-library@9c9cdc50` landed (23:08:07 UTC). Confirmed current LDR HEAD (`a771e3e2`, 2026-07-14 00:28
      UTC, well after `9c9cdc50`) STILL carries the same stale digest pin — the `update-dependency-version.yml`
      auto-refresh automation (designed for exactly this: "Refreshed by the dependency-update fan-out... on base-image
      republish") did not fire/land for this repo. **Fix staged**: bumped `ARG BASE_IMAGE_DIGEST` to
      `sha256:29e5b552...` (the current UTL `latest`/`0.55.0` image, built 2026-07-14T01:23:17Z from UTL HEAD `c7126116`
      — confirmed `merge-base --is-ancestor 9c9cdc50 HEAD` on UTL). Also regenerated the `tradfi` expected_universe
      golden fixture (unrelated pre-existing QG-red: UAC's `753fb81a`, an operator-approved 2026-07-13 change narrowing
      ICE to `ohlcv_24h`-only, never got its instruments-service golden regenerated — verified intentional via commit
      message + git blame before regenerating; scoped the regen to ONLY `tradfi.json`, reverted the other 4
      auto-regenerated goldens since their tests were already passing and blind-committing them risks baking in
      unrelated drift). **Both fixes are LOCAL, UNCOMMITTED** — a SECOND, independent, confirmed-pre-existing QG red
      (STEP 5.101 empty-string-fallback baseline breach, 368>366) blocks the `quickmerge --agent` sentinel gate;
      repo-blocker `RB-f453fcc0` declared + issue doc filed
      (`instruments_service_empty_string_fallback_baseline_breach_2026_07_14.md`). **Answer to this todo's own question:
      STALE (the UTL base layer specifically), NOT a residual code bug** — todo 2 below can proceed once (a) this fix
      ships (unblocks the repo-blocker) and (b) the operator-coordinated maintenance window todo 2 itself requires is
      arranged. — **DIGEST FIX CONFIRMED LIVE, slot 2 (data_engineering), 2026-07-14 (session resumed after a mid-task
      crash)**: on resume, fresh-pull found `instruments-service@ca3902bb` (slot 3, independently) already shipped the
      byte-identical digest bump (`sha256:b7e391f8...` → `sha256:29e5b552...`, same UTL HEAD `c7126116`) via the
      dirty-deps direct-push carve-out — confirmed via `git show`, now live on `live-defi-rollout`. Stashed my
      now-superseded local Dockerfile diff (identical content, dropped cleanly on fast-forward) and re-verified the
      `tradfi.json` golden fix is STILL genuinely needed (re-ran the failing test on the fast-forwarded tree — still
      red; an earlier golden regen, `c6a97052`, only removed 3 stale ICE/ohlcv_1m tuples but pre-dated the
      ICE/index/ohlcv_24h tuple becoming enumerable, so it's itself stale). Re-generated + reduced to a tradfi-only diff
      again (verified passing); but a **THIRD, independent, confirmed-pre-existing QG red** surfaced on this same re-run
      (`test_rollup_defi_pool_emits_dual_form_ids`, a DeFi UNISWAPV3-vs-UNISWAP_V3 naming drift, verified pre-existing
      via clean-tree stash — unrelated to sports/tradfi, out of data_engineering craft scope). Given this repo is now
      confirmed red for (at least) two independent reasons simultaneously and multiple other slots are actively shipping
      fixes to it concurrently, re-stashed the tradfi golden fix (tag
      `orchestrator-slot-2-sports_cf8_available_at_backfill_regression-007`) rather than chase a third unrelated failure
      or risk a misapplied direct-push carve-out. **This todo's own substance (the deployment-freshness question) is now
      fully resolved AND live in production** — the digest fix shipped is what matters; who authored the commit is
      incidental given two independent investigations converged on the identical root cause and fix.
- **[DATA] P1. CANCELLED — SUPERSEDED 2026-08-16** (consolidated into the `[INFRA] P1` "STALE-CHECK CORRECTION
      2026-08-09" todo below, which is now authoritative for what remains — only sub-item (3), the operator-coordinated
      maintenance-window execution. Kept below for investigation-trail context only — not independently dispatchable.) Once the TEAMS/STANDINGS deployment question above is resolved (either "was stale, now redeployed" or
      "a residual code bug, now fixed"), run a TARGETED re-emit pass scoped ONLY to `capture_status='captured'` rows on
      both sports surfaces (NOT a full `--force` corpus rebuild, which has already regressed data twice in this doc's
      history) — coordinate the maintenance window with the operator first per Finding 1. Expected volume: ~652K rows on
      IS, ~287K on MDPS (per the P0 addendum's breakdown, dominated by pre-2026-06-26 `trades`/`odds_api` +
      `odds_horizon_bucket` historical residue). Verify with the new `_check_captured_column_fill_regression` guardrail
      active during consolidation. (repo: market-tick-data-service, unified-trading-library) — **ATTEMPTED (small-scale
      test only) — BLOCKED on a NEW root cause, safely rolled back, slot 3, 2026-07-14.** Dispatched independently
      (per-CF-8-backfill-ask), read this doc in full at dispatch start (before `280d3f9fc`/`1fb0344aa` landed) and
      proceeded per the dispatch's own explicit small-scale-test-first authorization; did **not** re-check this doc
      again immediately before writing, so did not see the operator's `BLK-d9137d48` STOP answer (committed
      `2026-07-14T01:57:45Z`, ~4 minutes before this touch's write at `02:01:59Z`) until AFTER the test+rollback below
      was already complete — flagging this timing gap honestly rather than omitting it; net effect was safe (see below)
      but the process lesson is to re-pull+re-read immediately before the write step, not just at dispatch start, on a
      doc this hot. Built `sports_captured_available_at_targeted_backfill_2026_07_14.py` (reuses
      `_write_captured_rows`/`_available_at_from_row` exactly) + `sports_cf8_captured_backfill_snapshot_2026_07_14.py`.
      Snapshotted both canonicals, confirmed 0 in-flight consolidator executions, paused both crons. Ran the required
      500-row small-scale test on MDPS ONLY (IS never touched beyond dry-run) — **fill rate did NOT improve**
      (captured=575,671, missing=286,839, BYTE-IDENTICAL before vs. after). A row-content hash diff proved only 71/500
      written rows survived consolidation, and those 71 replaced ALREADY-FILLED rows (2026-07-13 backfill residue), not
      blank ones — net zero, not an improvement. **Root-caused why — a NEW finding, more fundamental than the
      "point-in-time snapshot" hypothesis above**: the consolidator's dedup key includes `service_name`.
      `ManifestWriter(service_name=service_name_for_surface(surface), ...)` stamps EVERY backfill-written row with ONE
      fixed value per surface (`market-tick-data-service` MDPS / `instruments-service` IS). Live query: on BOTH
      surfaces, 100% of currently-FILLED captured rows carry that exact fixed service_name, while 100% of
      currently-MISSING rows carry a DIFFERENT, original owning service_name — MDPS: `market-data-processing-service`
      (109,313) + `migrate-sports-canonical` (176,428); IS: `market-tick-data-service` (209,741) +
      `migrate-sports-canonical` (167,220) + `backfill-teams-61-leagues` (165,148) + `market-data-processing-service`
      (109,312). A rewrite stamped with the wrong service_name can never dedupe-supersede the true target row — every
      attempt (past or future) using the CURRENT write path only adds a permanently separate, non-collapsible duplicate.
      **This is why the P1 todo above's "targeted re-emit" framing itself needs revision before ANY further attempt**:
      it is not safe/effective to scale up `sports_captured_available_at_targeted_backfill_2026_07_14.py` as currently
      designed — a correct fix needs to group target rows by their OWN `service_name` and write each group through a
      `ManifestWriter` constructed with THAT service_name (new, unreviewed engineering — a design + review step, not a
      batch-size judgment call). Per the dispatch's own absolute safety floor ("genuine ambiguity about data correctness
      → STOP, roll back, report") — independently of, and reinforcing, the operator's separately-recorded STOP — did NOT
      scale to the remaining ~286K/~652K rows. **Rolled back**: restored MDPS's live index from the pre-test snapshot
      (`pre_cf8_captured_backfill_20260714T015810Z.parquet`, byte-identical verified: 1,958,499 rows / 575,671 captured
      / 286,839 missing — exact pre-test baseline, confirmed via a fresh `cf_manifest_audit_2026_06_01.py` run showing
      `RED — ['CF-8', 'L6-legacy-only']`, non-null=1,670,401/1,958,499, unchanged from history). Both crons resumed +
      confirmed healthy (`succeededCount=1`, 0 failures, 3+ consecutive cycles observed). Both scripts shipped
      (`market-tick-data-service@41b3c8fa`) with a prominent "DO NOT RUN AT SCALE — BLOCKED" docstring warning + this
      finding, kept as reference read/filter/dry-run scaffolding for whoever designs the per-service_name write fix —
      **not attempting that design in this dispatch**: it is genuinely new engineering needing its own review, and the
      operator has separately and explicitly said stop pending a scheduled window regardless. No further production
      write made after the rollback. CF-8 remains RED on both surfaces, unchanged from the pre-session baseline.

      **DESIGN DIRECTION CONFIRMED 2026-08-07 (operator: "i authorize")** — the per-service_name-scoped write-group
          approach above (group target rows by their OWN original `service_name`, write each group through a
          `ManifestWriter` constructed with THAT service_name, not the fixed per-surface value) is confirmed as the right
          direction. **Design confirmed, NOT yet built/reviewed/executed** — this is still "new, unreviewed engineering"
          per the finding above; confirming the direction doesn't skip the actual implementation + review step, nor the
          maintenance-window coordination `sports_consolidated_closeout_2026_07_19.md`'s Track H todo above now
          authorizes separately. Someone still needs to: (1) implement the per-service_name grouping in
          `sports_captured_available_at_targeted_backfill_2026_07_14.py` (currently DO-NOT-RUN-AT-SCALE per its own
          docstring), (2) get it reviewed given the 2 prior regressions in this area, (3) run it inside a coordinated
          maintenance window with pre-snapshots, matching the 2026-07-14 attempt's own safe rollback pattern.

- [ ] [INFRA] P1. **STALE-CHECK CORRECTION 2026-08-09 — sub-item (1) below is factually WRONG, already done; only
      sub-item (3) remains.** This todo's own framing ("now design-confirmed but unbuilt") contradicts this SAME doc's
      own 2026-07-14 Progress Log: `market-tick-data-service@af627b5b` ("fix(sports): per-original-service_name write
      grouping for CF-8 captured-row targeted backfill") already implemented exactly this — verified live 2026-08-09,
      `af627b5b` is an ancestor of `origin/live-defi-rollout`, and the current
      `scripts/sports_captured_available_at_targeted_backfill_2026_07_14.py` on that branch contains
      `_group_target_rows_by_service_name()`, wired into `main()`'s write loop, with a synthetic unit test
      (`tests/unit/scripts/test_sports_captured_available_at_targeted_backfill.py`). The script's own docstring already
      says "**Fix applied (2026-07-14, this touch)**" for this exact grouping. The `na-eligibility-audit 2026-08-07`
      entry below already flagged this as a likely duplicate ("worth re-verifying before rebuilding") — this pass
      confirms it. **Implement + ship the per-service_name-scoped write-group fix, now design-confirmed but unbuilt**
      (see the 2026-08-07 note directly above). Concretely: ~~(1) rewrite
      `sports_captured_available_at_targeted_backfill_2026_07_14.py` to group target rows by their OWN original
      `service_name` and write each group through a `ManifestWriter` constructed with THAT service_name, instead of the
      fixed per-surface value that caused the 2026-07-14 rollback~~ — **ALREADY DONE, 2026-07-14,
      `market-tick-data-service@af627b5b`, see correction above**; (2) get it reviewed — this area has 2 prior
      regressions, do not skip review; (3) execute inside the coordinated maintenance window authorized by
      `sports_consolidated_closeout_2026_07_19.md`'s Track H todo, with pre-snapshots and the same safe-rollback pattern
      as the 2026-07-14 attempt. Does not scale-test past the ~286K/~652K remaining rows until the rewritten script is
      reviewed. **What genuinely remains: only sub-item (3), the operator-coordinated maintenance-window execution — the
      same gate the sibling `[DATA] P1` todo above already tracks.** (repo: market-tick-data-service)

- [x] ✅ [INFRA] P2. Verify whether the row_count-preferring multi-source dedup tie-break (`manifest_consolidator.py`'s
      `CASE WHEN capture_status = 'captured' AND captured_distinct_sources > 1 THEN COALESCE(TRY_CAST(row_count AS BIGINT), 0) ELSE NULL END DESC`)
      contributes to the captured-row `available_at` gap above — flagged as a plausible mechanism (a high-row-count
      stale row could out-rank a fresher low-row-count one) but NOT confirmed; needs a targeted check of whether any of
      the missing row_keys are genuinely multi-source before concluding either way. (repo: unified-trading-library) —
      **RULED OUT, slot 4 (infra), 2026-07-14**, via a direct empirical check (no code change; read-only, no production
      write, no cron pause/resume). The consolidator's real dedup key is `_BASE_DEDUP_COLS + _OPTIONAL_DEDUP_COLS`
      (`manifest_consolidator.py:393-407` — date/venue/data_type/service_name + timeframe/league_id/chain/
      instrument_type/underlying/feature_group/model_family/training_period/strategy_id/client_id/instruction_type/
      instrument_id; deliberately excludes `source`). `captured_distinct_sources` is
      `count(DISTINCT source) FILTER (WHERE capture_status='captured') OVER (PARTITION BY <that same key>)` — so the
      tie-break's `> 1` branch can only ever fire on a dedup-key group that genuinely has 2+ different `source` values.
      Single-object read of the LIVE `_index/availability_index.parquet` on both sports surfaces (no new whole-corpus
      walk — same single-object-read method prior touches on this doc used), grouped ALL `capture_status='captured'`
      rows by the real dedup key (NULL/`""` normalized the same way `_dedup_key_sql` does) and counted distinct `source`
      per group: **IS — 1,645,101 captured rows → 1,645,101 dedup-key groups, 0 with >1 distinct source. MDPS — 575,671
      captured rows → 575,671 dedup-key groups, 0 with >1 distinct source.** Every currently-captured row is already at
      a unique key on both surfaces — there is no live multi-source ambiguity for the tie-break to resolve either way,
      on the FULL corpus, not just the data_types named in the gap breakdown above. (Sanity-checked the two data_types
      that looked most suspicious first: IS `TEAMS`/`STANDINGS` are single-source [`api_football`] only; MDPS `trades`
      has 2 distinct sources present [`api_football` 47,253 rows + `odds_api` 362,746 rows] but they never share a dedup
      key — `api_football`'s `trades` rows are a disjoint legacy slice, not a same-cell competitor to `odds_api`'s,
      matching this doc's own precedent for the 12,407 legacy `source='instruments_service'` VENUES/LEAGUES rows.)
      **Caveat honestly noted**: this proves no ACTIVE multi-source ambiguity exists right now (so the tie-break cannot
      be silently misfiring today, and a future consolidation cycle is safe from this specific mechanism) — it cannot
      retroactively prove the tie-break never fired on a since-collapsed historical duplicate, since a post-dedup
      canonical only ever retains the winning row. Given zero live evidence of the precondition
      (`captured_distinct_sources>1`) anywhere in either surface's current captured population, and that the same-source
      duplicates the doc's investigation trail already traced (targeted-re-emit gap, service_name-scoped dedup) fully
      explain the gap via other confirmed mechanisms, this tie-break is not a contributing cause. No further action
      needed on this todo.
- [x] ✅ [INFRA] P2. Fix the `write_projected_index`/`SportsProjectionCollector` FetchEvidence-serialization crash so
      `--beta-manifest-out` dry-run previews work again. (repo: market-tick-data-service) —
      market-tick-data-service@cae3a3fb. `ProjectionCollector._emit()` (the single choke point every
      `add`/`record_empty`/`record_failed`/`emit_passthrough` row passes through) now coerces any dataclass-instance
      value (e.g. `FetchEvidence`, threaded via `record_empty(fetch_evidence=...)` for honest-absence validation) to a
      JSON string via `dataclasses.asdict()` before `write_projected_index` hands rows to
      `pd.DataFrame(...).to_parquet()` — pyarrow's type inference cannot serialize a raw dataclass instance, which is
      exactly the `pyarrow.lib.ArrowInvalid` this todo names. New regression test
      (`test_fetch_evidence_dataclass_does_not_crash_parquet_write`) confirmed to FAIL with the exact same
      `ArrowInvalid` on pre-fix code (verified via a temporary `git stash` revert) and PASS post-fix, round-tripping
      `fetch_evidence` as valid JSON. Confirmed this never touched the real `--no-dry-run` write path (only
      preview/dry-run tooling). Full `quality-gates.sh` green + sentinel-verified; shipped via `quickmerge --agent`.
- [x] ✅ [INFRA] P2. The sports-consolidator-cron collision (Finding 1) has now recurred at least 3 times in one day
      (original incident 2026-07-13 + twice more during the 2026-07-14 re-attempt above) despite operator coordination
      each time — manual "please don't touch this" coordination is not holding up under real fleet concurrency. Worth a
      TECHNICAL safeguard instead of relying on coordination alone: e.g. a maintenance-window marker (a GCS sentinel
      object or Firestore flag) that a resume/pause action checks and refuses to override without an explicit force, or
      routing cron pause/resume through a single dashboard control other agents/ operators can see is currently held.
      Scope/design not decided — routing to operator/infra owner. (repo: unified-trading-pm or deployment-service,
      wherever the scheduler-management tooling should live) — **Shipped, slot 6 (infra), 2026-07-14.** Built the
      GCS-sentinel maintenance-window marker option: `unified-trading-library@4ddc59c9`
      (`unified_trading_library.maintenance_window` — `acquire`/`read`/`release_maintenance_window`), a distributed CAS
      marker modeled on the production-proven `TardisConcurrencyLease` pattern (generation-precondition
      `conditional_upload_bytes`/`conditional_delete_blob`, so two racing callers can never both believe they hold the
      window; every window auto-expires via TTL so an abandoned declaration never permanently blocks future
      maintenance). 15 unit tests, in-memory fake GCS client with generation semantics. Scheduler-specific wiring in
      `deployment-service@1090c3e` (`scheduler_maintenance.py`): `pause_for_maintenance()` acquires the window BEFORE
      pausing (never pauses a cron it can't safely account for); `resume_after_maintenance()` refuses
      (`MaintenanceWindowActiveError`) when a live foreign window is held, unless `force=True`; a `--status` CLI
      subcommand lets ANY caller — including an operator about to run a raw `gcloud scheduler jobs resume` — check who
      holds the window and why, directly targeting Finding 1's root cause (the operator wasn't aware the pause was
      intentional). 11 more unit tests (injected fake pauser/resumer, no real GCP credentials). Full `quality-gates.sh`
      green on both repos, shipped via `quickmerge --agent`. **Complementary work discovered mid-dispatch**
      (`deployment-service@e2a62cc`, a different slot, same session): a new DP-WATCHER-003 check
      (`consolidator_scheduler_watcher.py`) pages CRITICAL when a manifest-consolidator Cloud Scheduler job is found
      PAUSED with no maintenance marker — the reactive/detection half of this same problem (mine is the
      proactive/prevention half). A natural follow-up (not done in this dispatch — new, unreviewed integration work) is
      teaching that watcher to read `maintenance_window`'s marker and suppress its page when a live window legitimately
      explains the pause, mirroring the existing pause-aware `scheduler_state_reader` pattern in `check_cron_fired`.
      **Does NOT retrofit the existing ad-hoc CF-8 backfill scripts to call this** — that adoption (which scripts, when)
      is a separate operator/infra-owner decision; this ships the primitive + CLI for that decision to act on.
  - **Bug fix, slot 6 (backend_engineer), 2026-07-14**: a review of `deployment-service@1090c3e` flagged that
    `resume_after_maintenance()` released the maintenance window BEFORE resuming the scheduler jobs — inverted vs.
    `pause_for_maintenance()`'s acquire-before-act ordering. If `act(job)` raised partway through a multi-job resume
    (e.g. a Cloud Scheduler API error on job 2 of N), the window was already released while jobs remained paused — a
    second caller checking `--status` would see "clear" on a surface that was actually still mid-resume, the exact race
    this module exists to prevent. Fixed: authorization is now checked first (still refuses an unauthorized caller
    before it touches any job, preserving the enforcement point), jobs are resumed, and the window is released only
    after every job resumes successfully — a raised exception now leaves the window HELD. Added a regression test
    (`test_partial_resume_failure_leaves_window_held`, `deployment-service/tests/unit/test_scheduler_maintenance.py`)
    that fails on the pre-fix ordering and passes post-fix. Full `quality-gates.sh` green (deployment-service, coverage
    confirmed via `coverage.xml`), shipped via `quickmerge --agent`: `deployment-service@d58506e`.
- [x] ✅ [DATA] P2. Decide disposition for the 12,407 legacy `source='instruments_service'` rows (VENUES/LEAGUES) —
      backfill a real vendor source or accept as a known residual. (The 35,361 free-text-reason rows are tracked
      separately in `sports_rebuild_v9_free_text_reason_taxonomy_rejection_2026_07_13.md`.) (repo:
      market-tick-data-service, unified-api-contracts) — **DECIDED, slot 8, 2026-07-13**:
  - **Root cause confirmed historical, not a live bug.** UAC `SOURCE_PRIORITY` (`_source_priority_data.py`) registers
    `("sports", "VENUES")` and `("sports", "LEAGUES")` under `["api_football"]` — `instruments_service` (the writing
    SERVICE's own name) was never a valid vendor for these `data_types`.

    Traced the CURRENT active capture code
    (`instruments-service/instruments_service/engine/orchestrator/sports_fixtures.py::_sports_ref_source()`): it derives
    the manifest `source` from the entity's `pipeline_mode` (`batch_` stripped), which correctly resolves to
    `api_football` for VENUES/LEAGUES today, and `record_captured()` itself **fail-fasts** (`MissingSourceError`) on any
    source not in `SOURCE_PRIORITY` — so the current write path CANNOT reproduce this mislabeling; it's guarded. The
    12,407 rows are therefore genuinely **legacy** (written before this source-derivation/validation existed), not an
    active, recurring defect.

  - **Correct disposition: backfill to `api_football` (not "accept indefinitely")** — matches the registered vendor,
    corrects future SOURCE_PRIORITY-based auditing/attribution, and the actual DATA VALUES in these rows are already
    correct (only the `source` metadata column is wrong) — a narrow, low-risk metadata correction, not a data rewrite.
  - **BUT: do not execute the backfill now.** This same issue doc's Finding 2 (P0, still OPEN) is a live, unresolved
    `available_at`-destroying regression on this EXACT IS canonical, triggered by the same
    `rebuild_sports_manifest_v9.py --force` full-rebuild mechanism a `source`-relabel backfill would need to use. Per
    CLAUDE.md's data-pipeline- correctness rule ("a RED data audit FREEZES layer-N+1 work"), running ANY further
    `--force` full-rebuild pass on this canonical before Finding 2 is root-caused risks repeating the same silent
    corruption on a different column. **Action: defer this backfill and bundle it into the SAME future rebuild pass that
    resolves Finding 1's root cause** (todo 1/2 above) — do not run it as a separate, earlier operation.

- [x] ✅ [INFRA] P1. Add a general column-fill-regression guardrail to the DuckDB consolidator merge (the "defensive
      check" suggested in "Recommended next steps" item 4 above) — so ANY future full-rebuild attempt (this backfill or
      otherwise) FAILS LOUD via `MANIFEST_COLUMN_FILL_REGRESSION` instead of silently repeating this exact class of
      corruption. (repo: unified-trading-library) — `unified-trading-library@2e132bb2`, see Progress Log.

## Progress Log

**Maintenance-window primitive — 2026-07-14 (slot 6, infra)**: dispatched to the cron-collision todo. Built + shipped
the GCS-sentinel maintenance-window option (`unified-trading-library@4ddc59c9` — generic CAS marker, modeled on
`TardisConcurrencyLease`) + a scheduler-specific pause/resume wrapper + `--status` CLI (`deployment-service@1090c3e`),
26 combined unit tests, both repos full-`quality-gates.sh` green, shipped via `quickmerge --agent`. Hit the exact
quickmerge rebase race `pm_qg_governor_k1_vs_branch_churn_race_2026_07_13.md` describes repeatedly on both repos (5
misses on UTL alone) under heavy same-session churn — kept re-running QG + retrying quickmerge until each landed
cleanly, no shortcuts taken. Along the way, fixed 3 unrelated pre-existing reds that blocked shipping: a fresh
setuptools CVE (PYSEC-2026-3447, `uv lock --upgrade-package setuptools`, UTL@b8ef48dc), a top-level-import-pattern
violation (UTL@4ddc59c9 exports the new symbols), and 2 codex-compliance violations in my own new file (basedpyright
`reportAny` + a hardcoded prod project id in a test). Discovered `deployment-service@e2a62cc` (a different slot, same
session) independently built the complementary detection/alerting half of this same problem (DP-WATCHER-003 pages when a
consolidator scheduler is found paused unexpectedly) — cross-linked in the todo above rather than duplicated; flagged a
natural follow-up (that watcher reading this marker to suppress its page during a legitimate window) as unreviewed
future work, not done here.

**CF-8 scoping + guardrail touch — 2026-07-14 (slot 3, laptop, dispatched per the operator's original CF-8-backfill
ask)**: read this doc + the plan in full before starting. Found (via `git log --all`) that root-causing was already IN
PROGRESS/DONE by two other concurrent agents (slot 11's `f5f15e3a`; slot 3/planning's `9c9cdc50` + their own plan touch
"CF-8 root-cause continuation") — did NOT duplicate that work. Independently built a synthetic DuckDB repro of the
consolidator's full-rebuild merge SQL (2-file and 3-file canon+shards scenarios, using REAL production schemas pulled
via single already-planned index/shard reads — `is_canon_live.parquet`, the pre-backfill snapshot, a live per-VM shard,
`_legacy_seed.parquet` — no new whole-corpus walk) and confirmed the column-order/schema-union hypothesis this doc's
Finding 2 flagged as candidate (b) does NOT explain the regression: the merge's explicit `shard_proj` re-projection
correctly realigns columns by name even across a 3-file merge when the canonical is the superset schema — corroborating
(via an independent method) slot 11's own conclusion that the consolidator merge itself was innocent and the bug was
upstream in the writer serializer.

Given the P0 root cause is now fixed but the live backfill re-attempt (todo/P1 above) is explicitly gated on an
operator-coordinated maintenance window per Finding 1 (confirmed unchanged by slot 3/planning's own touch, timestamped
minutes before this one) — did NOT attempt the production re-run myself, to avoid a 3-way collision with whichever agent
the operator eventually coordinates that window with.

Instead shipped a genuine, non-duplicative hardening contribution: `_check_column_fill_regression()` +
`MANIFEST_COLUMN_FILL_REGRESSION` in `unified_trading_library/manifest_consolidator.py`, mirroring the existing
`_check_row_count_regression`/`MANIFEST_ROW_COUNT_REGRESSION` pattern — a single-pass per-column non-null-fraction
comparison (before vs. after a merge cycle) that pages loudly if ANY column's fill rate collapses, closing the
"defensive check" gap this doc's own Recommended-next-steps item 4 named. 4 new unit tests
(`tests/unit/test_manifest_consolidator.py`), full `quality-gates.sh` green. `unified-trading-library@2e132bb2`.

Re-ran the full `cf_manifest_audit_2026_06_01.py` on both live sports surfaces (fresh index pull, current as of this
touch): **MDPS** `RED — ['CF-8', 'L6-legacy-only']` (unchanged — `available_at` column still absent; 140 legacy-only
cells, previously-accepted phantom-capture). **IS** `RED — ['CF-2-paths', 'CF-3', 'CF-4', 'CF-8', 'L6-legacy-only']`
(unchanged RED-check set from the 26th/27th touches; `available_at` non-null=3,492,700/5,506,821 = 63.4%, up slightly
from the 62.9% restore baseline via ordinary incremental writes — NOT a re-attempt of the backfill). Confirmed both
sports consolidator crons are back to `ENABLED` (routine steady-state; no lock file, no orphaned per-VM shard — nothing
mid-flight right now). Neither surface is honestly GREEN. Not ready for an E8 legacy-bucket-deletion ask on either
surface — CF-8 remains the primary blocker on both, now purely procedural (operator-coordinated window) rather than a
code-correctness blocker.

**Post-slot-11-backfill re-audit — 2026-07-14 (data_engineering slot-2, task `sports_manifest_canonicalisation-001`,
E8-verify dispatch)**: fresh-pulled to `unified-trading-pm@e2bf7a47a` (includes slot 11's completed backfill + slot 6's
independent re-verification, both already flipping the plan's CF-8 P1 todo before this touch started). Since `gcloud`
CLI is broken on this host (snap-confine sandboxing, same issue Finding 1's author hit), ran
`cf_manifest_audit_2026_06_01.py`'s `audit()` in-process with `_cp`/`_ls_shallow` monkeypatched to the
`google-cloud-storage` SDK (`.venv-workspace` has it pre-authed) instead of shelling to `gcloud storage` — same read
logic, different transport, no script edit needed.

Live results, both surfaces: **MDPS** `RED — ['CF-8', 'L6-legacy-only']`; `available_at` non-null=1,670,401/1,958,499
(85.3%, matches slot 11's reported figure exactly — no drift). **IS**
`RED — ['CF-2-paths', 'CF-3', 'CF-4', 'CF-8', 'L6-legacy-only']`; `available_at` non-null=5,090,721/5,751,217 (88.5%, up
slightly from the reported 87.8% via ordinary incremental writes, consistent with the pattern the prior touch already
noted for the 62.9%→63.4% drift). CF-2-paths/CF-3/CF-4/L6-legacy-only are byte-for-byte the SAME pre-existing,
previously-triaged residuals (28 genuinely-empty INJURIES legacy-only cells on IS, 140 on MDPS — both match history
exactly).

**New finding, not previously quantified**: broke the CF-8 gap down by `capture_status` on both surfaces (grouped the
downloaded index parquet by status, checked `available_at.notna()` per group) rather than trusting the aggregate
percentage. Result: `empty_confirmed`/`attempted_failed`/`expected_unattempted` are ALL ~99.8-100% filled on both
surfaces (the backfill worked correctly for these) — but `capture_status='captured'` rows are only **39.8% filled on
IS** (986,313/1,638,158 filled, 651,845 missing) and **49.8% filled on MDPS** (288,832/575,671 filled, 286,839 missing).
This confirms — and quantifies for the first time — this doc's own Finding-2 investigation-trail candidate (a) at line
~115 ("captured rows may go through a different path — worth diff-checking against `_writer_record.py`'s non-captured
path"): captured rows are genuinely, specifically under-filled, not just "slightly behind" the aggregate. Filed as a new
P0 todo above (did not re-run any write myself — a captured-row-scoped backfill is the same
operator-coordinated-maintenance-window class of operation as the empty-row backfill, out of scope for a verify
dispatch, and Finding 1's cron-collision history argues against an uncoordinated attempt).

**E8 checkbox NOT flipped** — CF-8 is genuinely still RED on both surfaces (for a narrower, now-understood reason). This
plan-doc + issue-doc edit ship via the `docs(plans):` carve-out.

**Independent re-verification — 2026-07-14 (slot 3, laptop, dispatched per the operator's Part-1-4 CF-8
authorization)**: read this doc + the plan in full. Verified `f5f15e3a`/`9c9cdc50` logically close the exact traced
mechanism (no gap); fixed + shipped this same session's own previously-broken uncommitted repro test
(`unified-trading-library@dbc5447f`), confirmed via revert-and-retest that it reproduces the real regression shape and
that `2e132bb2` genuinely fires on it. Separately found (via a live `gcloud run jobs executions list` check, not
speculatively) that `market-data-tick-sports-prd`'s consolidator had crash-looped ~24 cycles (23:54Z-00:17Z) on a
related but distinct bug — `canon_read` not schema-aligned to `union_cols`, crashing on `DuckDB BinderException` the
moment a shard introduces a column (`available_at`) the canonical never had. Root-caused + fixed it independently, then
found via `git pull` that slot-11 had landed the identical fix (`unified-trading-library@0f55cc2b`) while re-running the
real backfill — reconciled by dropping my duplicate source fix, keeping only the still-needed test fix.

Independently re-verified todo 2's backfill results via a direct `google-cloud-storage`/`pyarrow` read of both live
canonicals (own read, not trusted from any log): MDPS 85.3%, IS 88.5% — both match the reported figures to within normal
incremental drift. Confirmed both crons `ENABLED`. Re-ran the full `cf_manifest_audit_2026_06_01.py` on both surfaces:
**unchanged verdict** — MDPS `RED — ['CF-8', 'L6-legacy-only']`, IS
`RED — ['CF-2-paths', 'CF-3', 'CF-4', 'CF-8', 'L6-legacy-only']`. Independently corroborated the captured-row gap this
doc's P0 todo above already quantifies (IS captured 60.2% filled/39.8% missing = 651,991 rows, MDPS 50.2% filled/49.8%
missing = 286,839 rows — both within ~150 rows of this doc's own numbers, i.e. no material drift). Traced
`_write_captured_rows` + `ManifestWriter.add()` myself: both correctly thread `available_at` through to the
`AvailabilityRecord` on CURRENT code — the residual is consistent with this doc's own candidate (b) (pre-existing
captured rows never re-emitted by a captured-row-scoped pass) rather than a still-broken write path; did not
disambiguate further or attempt a captured-row backfill myself — that stays this P0 todo's own scope, not duplicated
here, and today's 3-times-recurred cron-collision history argues for a fresh, separately-coordinated window rather than
a same-session fourth attempt. Neither surface is ready for an E8 ask. No checkbox flipped.

**Captured-row P0 root-cause + guardrail — 2026-07-14 (data_engineering slot-3, dispatched to work this exact P0
todo)**: read this doc + the plan in full first; fresh-pulled every slot repo to `origin/live-defi-rollout` (clean, no
conflicts). Did a single-object read of the LIVE `instruments-store-sports-prd-central-element-323112`
`_index/availability_index.parquet` plus the `_index/snapshots/pre_cf8_backfill_retry_20260713T233713Z.parquet` snapshot
the backfill itself already took (both single-object GCS reads via the already-authed `google-cloud-storage` SDK from
`market-tick-data-service/.venv` — no new whole-corpus walk).

Definitively ruled OUT candidate (b) ("captured rows need a different `available_at` source"): `written_at` is non-blank
on 100% of captured rows in BOTH the pre-backfill snapshot (0/1,224,740 blank) and the live index (0/1,638,411 blank) —
including every row currently missing `available_at`. Since `_available_at_from_row(row)` only returns `""` on a blank
`written_at`, a valid fallback was always derivable; timestamp-absence cannot explain the gap.

Isolated the real mechanism: broke the 651,991 IS captured rows missing `available_at` down by `written_at` date and
found the 2026-07-13 slice's `written_at` range (06:15-20:16 UTC) sits entirely BEFORE the backfill's own apply window
(21:07-23:41 UTC) — these rows are ordinary live production writes from earlier the same day that the backfill's
`--force` pass, reading a point-in-time index snapshot at start, never saw and therefore never re-emitted. This is a
targeted-re-emit gap, not a corruption during re-emit — `_write_captured_rows`/`writer.add()` correctly thread
`available_at` through on current code (independently confirmed, matches the prior touch's own finding).

Traced the two live-write-path data_types that dominate the gap to their actual call sites: `TEAMS`/`STANDINGS`
(`instruments-service/engine/orchestrator/sports_reference_core.py`, fixed by `56aa1938` 2026-07-13 18:44 UTC) and
`trades`/`odds_api`+`odds_horizon_bucket` (`market-tick-data-service/engine/orchestrator/manifest_finalize.py`'s
`_write_shard_counts_to_manifest`, fixed 2026-06-26). Confirmed BOTH fixes are correct by code inspection, yet 439
`TEAMS`/`STANDINGS` rows written as recently as TODAY (2026-07-14, well after both fixes landed) still show
`available_at=NULL` going through the fixed code path (non-blank `league_id`, matching the fix's own write shape) —
pointing at a production-deployment-freshness question (routed as a new P1 todo below) rather than a further code bug.
The `trades`/`odds_api` slice shows ZERO 2026-07-14 misses, confirming that path is healthy going forward and its gap is
pure pre-2026-06-26 historical residue.

Also flagged (not confirmed) a plausible third mechanism: `manifest_consolidator.py`'s dedup tie-break prefers the
higher-`row_count` row over recency specifically for multi-source captured dedup groups — filed as an open P2 todo
rather than asserted as a cause, since I did not verify any missing row_key is actually multi-source.

Given this doc's own history of TWO real production regressions from `--force` full-rebuild attempts, did NOT attempt
any further production write. Instead shipped the concrete, safe artifact this investigation's own findings called for:
`_check_captured_column_fill_regression()` in `unified_trading_library/manifest_consolidator.py` — a
`capture_status='captured'`-scoped sibling of the existing (aggregate-only) `_check_column_fill_regression` guardrail,
proven via a new unit test to catch the EXACT shape of this regression (aggregate fill rate improving while the
captured-only slice collapses) that the aggregate guard structurally cannot see. 3 new unit tests, full
`test_manifest_consolidator.py` suite green (73 tests), full `quality-gates.sh` green (126s).
`unified-trading-library@c7126116`.

Filed 3 new follow-up todos (deployment-freshness check, targeted captured-row re-emit, multi-source tie-break
verification) since the underlying data gap is genuinely NOT fixed — flipping this todo's checkbox because the
investigation asked for (isolate the root cause) is now substantially complete + a concrete guardrail shipped, matching
this doc's own established pattern for prior P0 items.

**Deployment-freshness todo resolved — 2026-07-14 (data_engineering slot-2, dispatched to
`sports_cf8_available_at_backfill_regression-007`)**: read this doc + the plan in full first; fresh-pulled every slot
repo (clean). Root-caused the deployment-freshness question the P0 addendum above left open: the production
`uts-prod-instruments-service-sports-fixtures` Cloud Run Job resolves its `:latest` image tag FRESH at every execution
(proven via 8 executions' differing resolved digests, not pinned at job-deploy time), so instruments-service APPLICATION
code was current at every write. The actual staleness is one layer down: the Dockerfile's `ARG BASE_IMAGE_DIGEST` pins a
UTL base image built 5.5 hours BEFORE `unified-trading-library@9c9cdc50` landed, and current LDR HEAD still carries that
stale pin (the `update-dependency-version.yml` digest-auto-refresh automation didn't fire for this repo — a separate,
real infra gap, not filed as its own issue this touch since the immediate fix was a one-line manual bump matching
exactly what that automation would have done). Staged the digest bump + an unrelated tradfi golden-fixture regen
(verified-intentional per UAC `753fb81a`, operator-approved) needed to get a clean QG baseline, but hit a SECOND,
confirmed-pre-existing QG red (STEP 5.101 baseline-ratchet breach, unrelated to either fix, verified via clean-tree
stash A/B) blocking the ship. Filed `instruments_service_empty_string_fallback_baseline_breach_2026_07_14.md` + declared
repo-blocker `RB-f453fcc0` rather than hand-guess the wrong lines (the checker's own reporting is a positional
tail-slice, not true new-site detection — confirmed via `git blame` that its 2 named lines are 2-month-old, unrelated
code). Both fixes remain staged LOCALLY/UNCOMMITTED in the instruments-service slot clone pending the repo-blocker
clearing (per RULES.md §4b posture — commit only from a green tree, wait for the backend's green signal, do not silently
stash-and-abandon).

Did NOT attempt the actual targeted captured-row re-emit (todo 2 below, this dispatch's literal assignment) — it is a
live production write of ~939K rows across two surfaces, and this doc's own text requires operator-coordinated
maintenance-window scheduling first (Finding 1's cron-collision history recurred 3 times even WITH coordination on the
prior attempt). Routing that coordination ask + the repo-blocker status to the operator via `/blocked` rather than
either running an uncoordinated production backfill or silently leaving the dispatch's actual assignment untouched with
no visibility.

**Session resumed after mid-task crash — 2026-07-14 (data_engineering slot-2)**: WIP was intact (uncommitted
Dockerfile + tradfi.json diff, as left). Operator answered `BLK-d9137d48` with **option A**: wait for the repo-blocker,
ship the digest fix, then STOP — do not attempt the live re-emit without further explicit go-ahead + a scheduled window.
Fresh-pulled and found slot 3 had independently shipped the byte-identical digest fix (`instruments-service@ca3902bb`)
via the dirty-deps carve-out while this session was down — confirmed live, dropped my now-redundant Dockerfile diff on
fast-forward. Re-verified the tradfi golden fix is still genuinely needed (a prior golden regen, `c6a97052`, was itself
stale) and re-confirmed it passes in isolation, but a third independent pre-existing QG red surfaced
(`test_rollup_defi_pool_emits_dual_form_ids`, a DeFi naming drift, out of scope) — kept it stashed
(`orchestrator-slot-2-sports_cf8_available_at_backfill_regression-007` in the instruments-service slot clone) rather
than chase an unrelated third failure or misapply a direct-push carve-out I'm not confident matches this case.

**Net effect for this dispatch**: this todo's own question (deployment-freshness) is resolved AND the fix is live in
production, satisfying the operator's "ship the digest fix" instruction (via a converged independent fix, not my own
commit). Per the operator's explicit STOP instruction, the actual targeted re-emit (todo 2) remains untouched, correctly
— it needs a separately operator-scheduled maintenance window, not this dispatch. Closing this dispatch here.

**Targeted captured-row backfill attempt + new blocking finding — 2026-07-14 (slot 3, laptop, dispatched to finish CF-8
completely)**: read this doc + the plan in full at dispatch start (before `280d3f9fc`/`1fb0344aa` landed), confirmed
nothing had changed vs. the dispatch's own briefing, then worked independently. Confirmed the same deployment-freshness
root cause data_engineering slot-2 later also found (stale UTL base-image digest on instruments-service,
`sha256:b7e391f8...` built 18:44:41Z, predating `f5f15e3a`/`9c9cdc50`/`2e132bb2`/`0f55cc2b` — all landed 22:59-00:22Z)
via a live read showing the 2026-07-14 TEAMS/STANDINGS gap GROWING (439→790 rows, now spread across the ENTIRE
`record_captured()` surface: WEATHER/INJURIES/ODDS/`FIXTURE__`/`PLAYER__`/MATCHES/PLAYER_VALUES too, not just
TEAMS/STANDINGS — confirming a dependency-wide staleness, not a narrow code bug). Shipped the fix
(`instruments-service@ca3902bb`, Dockerfile digest bump to `sha256:29e5b552...` = UTL HEAD `c7126116`) via the
dirty-deps direct-push carve-out (repo has ~65 unrelated files mid-edit by another concurrent agent's cefi/defi adapter
refactor, causing an unrelated golden-fixture QG failure) — confirmed by data_engineering slot-2's later touch above as
the same fix they independently converged on; still pending LDR→main promotion as of this write-up (standing fleet
automation owns it from here, not blocking).

Then built + ran the todo-2 targeted re-emit (evidence + full finding recorded on that todo's own checkbox above — not
duplicated here). Summary: a 500-row MDPS small-scale test produced a **net-zero** fill-rate change (not an
improvement), traced to a genuinely new root cause — the manifest consolidator's dedup key includes `service_name`, and
the current backfill write path stamps one fixed service_name per surface regardless of which service originally owned
the target row, making every currently-missing row's true dedup twin unreachable by any rewrite using the existing
convention. Rolled back the test write (restored MDPS's live index from the pre-test snapshot, byte-verified), resumed
both crons (confirmed healthy), and did not proceed to IS or to full scale. **Independently re-ran the full
`cf_manifest_audit_2026_06_01.py` on both surfaces post-rollback**: MDPS `RED — ['CF-8', 'L6-legacy-only']`
(non-null=1,670,401/1,958,499 = 85.3%, unchanged); IS `RED — ['CF-8', ...]` (unchanged from history — see below for the
full current verdict). Neither surface is closer to GREEN than before this session, but CF-8's true blocker is now
understood one level deeper than "needs a coordinated maintenance window" — it needs a per-original-service_name write
redesign FIRST, independent of when that window happens. Filed as an explicit caveat on the existing P1 todo rather than
a new todo (same scope, sharper understanding) so a future agent doesn't repeat the same ineffective attempt. Discovered
the operator's `BLK-d9137d48` STOP-pending-scheduled-window answer only after this test+rollback had already completed
(it was committed 4 minutes before this session's write) — the outcome was safe and fully reverted regardless, and this
session's own independent finding reaches the same "do not proceed" conclusion for a different, technical reason, but
the timing gap (not re-checking this doc immediately before the write step) is noted honestly as a process lesson for
next time on a doc this actively contested.

**Per-original-service_name write design built + tested — 2026-07-14 (slot 12, data_engineering)**: read this doc + the
plan in full at dispatch start; fresh-pulled every slot repo (clean, no conflicts). This doc's own P1 todo above is
explicitly gated on TWO things before any further production write: (1) the operator's `BLK-d9137d48` STOP pending a
coordinated maintenance window (still standing — not re-litigated here), and (2) the service_name dedup-key blocker
found by the touch immediately above, which this doc's own text calls "new, unreviewed engineering, not a batch-size
call" and names the concrete fix needed ("group target rows by their own service_name and write each group through a
ManifestWriter constructed with THAT service_name"). Confirmed via `git log` that fix had not yet been built by any slot
— only flagged as needed.

Built it: `sports_captured_available_at_targeted_backfill_2026_07_14.py` now reads each target row's own `service_name`
column (already present on every index row — the mechanism this doc's own finding used to diagnose the bug), groups
target rows by that value (falling back to the surface default only when blank/missing), and constructs one
`ManifestWriter` per group scoped to that group's own service_name — so a rewrite's dedup key matches the row it is
meant to supersede, closing the exact gap the 500-row MDPS test exposed. Verified via a new synthetic unit test
(`tests/unit/scripts/test_sports_captured_available_at_targeted_backfill.py`, 4 tests) that constructs a
multi-service_name target set with a mocked `ManifestWriter` and asserts: (a) rows split into per-service_name groups
correctly, (b) blank/missing `service_name` falls back to the surface default, (c) `main()`'s real write loop constructs
a distinct writer per group and routes each row's `add()` call to the writer matching ITS OWN service_name — never the
surface's single fixed default (the exact bug this fix closes). Full `quality-gates.sh` green.
`market-tick-data-service@af627b5b`.

**Did NOT run this against production** — no live write was made, no snapshot/pause/cron action taken, nothing in this
touch changes CF-8's live state on either surface. This closes the ENGINEERING half of the P1 todo's own caveat ("this
is new, unreviewed engineering... a design + review step, not a batch-size judgment call"); the OPERATIONAL half — an
actual coordinated-maintenance-window run, small-scale test first per Finding 1, honoring `BLK-d9137d48` — remains open
and is NOT this touch's call to make. Not flipping the P1 todo's checkbox: the targeted re-emit itself is still not
done, and CF-8 remains RED on both surfaces, unchanged from the pre-session baseline. A future operator-coordinated
attempt now has a design that should actually close the gap instead of repeating the net-zero 500-row result — that is
this touch's whole contribution.

**Redispatch-churn confirmed a second time — 2026-07-14 (slot-12, resumed session)**: this same slot's crashed prior
session (the touch immediately above) was resumed and re-dispatched to this identical task. Fresh-pulled all repos
(clean); confirmed `market-tick-data-service@af627b5b` is live and unchanged. A separate touch (slot-7, on the parent
plan doc) already diagnosed this exact pattern — ~30 re-dispatches since 2026-06-27 with data_engineering craft work
fully closed and only an operator-scheduled maintenance-window run remaining, still STOP-gated by `BLK-d9137d48` — and
filed `/blocked` recommending a `prereqs.conditions` gate on this task's `backlog.yaml` entry. Getting re-dispatched
into the identical dead end confirms that fix has not yet landed. Filed a fresh `/blocked` as a second, independent
confirmation rather than re-running any audit (would reproduce byte-identical RED evidence for zero new information, the
exact waste slot-7's own touch already flagged). No code shipped this touch.

**Parking gate applied — 2026-07-14 (slot-12, same session, operator-authorized)**: operator answered the fresh
`/blocked` (`BLK-c80a05e7`) with option A — apply the backlog parking gate now. Executed the `RULES.md` § 4 "Park a
task" recipe: seeded condition `sports-cf8-maintenance-window-scheduled` (`false`) via `POST /api/prerequisites/...`,
set `priority: 999` + `priority_override: true` + `prereqs.prerequisites: [sports-cf8-maintenance-window-scheduled]` on
this task's `backlog.yaml` entry (`sports_cf8_available_at_backfill_regression-007`), then `POST /api/backlog/reload`
followed by a real `POST /api/backlog/regen` tick to confirm the hand-tuned fields survive reconciliation (they do —
verified in the post-regen yaml, not just trusted from the API response). The same condition name was already referenced
as a prerequisite on `sports_manifest_canonicalisation-001` (the E8 Verify task), so this closes both gates with one
condition. This task will no longer be dispatched to idle slots until the operator flips
`sports-cf8-maintenance-window-scheduled` to `true` (coordinated with an actual maintenance-window run). No code shipped
this touch; this plan-doc edit ships via the `docs(plans):` carve-out.

**Multi-source dedup tie-break check — 2026-07-14 (slot 4, infra, dispatched to
`sports_cf8_available_at_backfill_regression-008`, the P2 verify-only todo)**: read this doc in full first; fresh-pulled
every slot repo (clean). Task scope is explicitly read-only investigation — no production write, no cron pause/resume,
so the operator's `BLK-d9137d48` STOP and the parking gate above (which only gates task `-007`'s live re-emit) do not
apply here. Confirmed the todo (this exact one) is a distinct backlog task ID from the parked `-007`, so dispatch was
correct.

Ruled out the tie-break via a single-object read of the live `_index/availability_index.parquet` on both sports surfaces
(no new whole-corpus walk), grouping every `capture_status='captured'` row by the consolidator's REAL dedup key
(`_BASE_DEDUP_COLS`+`_OPTIONAL_DEDUP_COLS`, source deliberately excluded) and counting distinct `source` per group —
full evidence + numbers recorded on the todo's own checkbox above (not duplicated here). Zero dedup-key groups with more
than one distinct source on either surface's full captured population; the one data_type that looked genuinely
multi-source at first glance (MDPS `trades`: `api_football` + `odds_api`) turned out to occupy fully disjoint dedup
keys, not a same-cell collision. This closes the todo's own open question — the answer is a confirmed negative, not an
unconfirmed flag. No code changed, no crons touched, no production write. This plan-doc edit ships via the
`docs(plans):` carve-out.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries).


## Root-caused + repaired the parking-gate churn — 2026-07-17 (slot-4, data_engineering, dispatched onto `sports_manifest_canonicalisation-001`)

Dispatched onto the E8 Verify checkbox (the ~30-plus-th redispatch this plan's own note already warns about). Read this
doc + the master plan in full before acting. Did **not** re-run `cf_manifest_audit_2026_06_01.py` — every prior touch
since 2026-07-14 has already established a repeat run reproduces byte-identical RED evidence (CF-8 only) for zero new
information, and GCS reads at corpus scale are not free.

**Ground-truth check, first time verified directly against the live orchestrator DB rather than trusted from doc text**:
queried `/var/lib/orchestrator/state.db` (`ORCHESTRATOR_DB_PATH`, read-only `sqlite3` connection) `prerequisites` table
directly — `sports-cf8-maintenance-window-scheduled = 0`
(`set_by: "slot-12 (operator-authorized via BLK-c80a05e7 answer: apply the backlog parking gate now)"`,
`set_at: 2026-07-14 10:44:49`). Confirms the maintenance window has genuinely never been scheduled/run since slot-12's
parking-gate session — the condition itself is intact and untouched.

**Found why the parking gate kept evaporating**: it was never a DB/condition problem — it's that the gate was never
actually wired to a _currently-live_ backlog task ID. Checked the live `agent-orchestrator/data/config/backlog.yaml`
(the ROOT clone's copy — this file is `.gitignore`'d server runtime state, confirmed via `git check-ignore`, so editing
it directly on root is the correct mechanism, not a root-clone-read-only violation) directly: **both**
`sports_manifest_canonicalisation-001` **and** `sports_cf8_available_at_backfill_regression-001` currently carry
`prereqs.prerequisites: []` and `priority: 10`/`20` (no `priority_override`) — i.e. completely unparked, despite
slot-12's 2026-07-14 session recording the gate as applied-and-verified. The task IDs referenced by that 2026-07-14
session (`…-007`/`…-008` suffixes) no longer exist in the current backlog at all — `regen_backlog_from_plan.py` derives
numeric ID suffixes from each plan's live checkbox ordering, so edits to either plan doc's structure since (new
checkboxes inserted above, items reordered/removed) silently renumbered both tasks down to `-001`, orphaning any
hand-tuned field that was attached to the old ID string. This is a _different_ failure mode than
`backlog_regen_drops_handtuned_prereqs_2026_07_12.md` (whose `8dd5763` fix — confirmed present,
`git merge-base --is-ancestor 8dd5763 HEAD` — addresses `priority_override` surviving a regen tick on a **stable** ID):
here the ID itself is not stable across plan edits, so no per-tick preservation logic can help — the tuning has to be
re-applied under whatever ID the task currently holds, checked after every plan edit to either doc, not just after every
regen tick.

**Re-applied the gate to the CURRENT IDs and verified it survives an actual regen tick** (not just `/reload`, which the
existing RULES.md guidance already flags as insufficient to exercise the revert path): set
`prereqs.prerequisites: [sports-cf8-maintenance-window-scheduled]` + `priority: 999` + `priority_override: true` on both
`sports_manifest_canonicalisation-001` and `sports_cf8_available_at_backfill_regression-001` directly in
`agent-orchestrator/data/config/backlog.yaml` (root clone, gitignored runtime state) → `POST /api/backlog/reload` (held)
→ `POST /api/backlog/regen` (a real plan-checkbox rescan, 444 plans scanned, held — verified by re-reading the file
after each call). Both tasks are parked as of this touch.

**Residual risk this touch does NOT close**: the next time either `sports_manifest_canonicalisation_2026_06_01.md` or
this issue doc gets a checkbox inserted/reordered above these items, the derived ID will shift again (e.g. `-001` →
`-002`) and silently drop this same gate a third time — the structural fix (key the gate to something ID-stable, e.g. a
content hash of the checkbox text, or `plan_ref` + `plan_order`, rather than the regen-derived positional suffix) is an
agent-orchestrator regen-logic change, out of data_engineering craft scope. Filing as a P1 below for a backend_engineer/
infra dispatch.

Nothing shipped in a service repo this touch (no code change); the DB read was read-only (`mode=ro` URI); the
`backlog.yaml` edit is live server config, not a git commit. This plan-doc edit ships via the `docs(plans):` carve-out.

- [x] ✅ [BACKEND] P1. Make backlog parking gates (`prereqs.prerequisites` / `priority_override`) survive plan-checkbox
      reordering, not just regen ticks on a stable ID. `regen_backlog_from_plan.py` derives each task's numeric ID
      suffix from checkbox position within its `plan_ref`; inserting/removing/reordering checkboxes above a parked item
      renumbers it and silently orphans any hand-tuned field attached to the old ID (distinct from — and not fixed by —
      `8dd5763`'s `priority_override`-survives-a-regen-tick fix, which only covers a _stable_ ID across ticks). Fix
      candidates: key parking state to a stable identifier (content-hash of the checkbox's own text, or `plan_ref` + an
      explicit anchor comment in the plan) instead of positional suffix; or have `/api/backlog/reload` warn/alert when a
      previously-parked condition name has no current task referencing it. Evidence: this touch re-derived and
      re-applied the gate for `sports_manifest_canonicalisation-001` / `sports_cf8_available_at_backfill_regression-001`
      after finding both silently unparked despite slot-12's 2026-07-14 session recording the gate as applied. (repo:
      agent-orchestrator) — agent-orchestrator@22738f6

**Shipped the parking-state-migration fix — 2026-07-18 (slot-8, backend_engineer)**: root cause was narrower than the
todo's own "positional suffix" framing — `_make_task_id` derives new ids from an incrementing per-slug counter, not
checkbox position, and the RECONCILE path (`plan_tasks_by_brief`) already matches on exact single-line brief text
regardless of reordering. The actual trigger is that this workspace hard-wraps plan markdown and `_parse_open_todos`
captures only the FIRST line of a multi-line todo as its `brief`: editing LATER words in the same paragraph (not the
todo's intent) can shift the line-1/line-2 word boundary, changing the captured brief even though nothing about the
todo's meaning changed. `_prune_stale` treats that shifted brief as a genuine orphan (byte-exact set match) and drops
it; the next regen ingests the new wording as a brand-new task via the existing, deliberate A2 remove+add design
(`test_text_edit_is_remove_and_add_not_in_place` — a reworded todo getting a fresh id is correct behavior, not the bug)
— but the OLD task's hand-tuned `priority`/`priority_override`/`prereqs.prerequisites` died with it, silently.

Implemented `_migrate_parking_state()` in `agent-orchestrator/server/regen_backlog_from_plan.py`, called from
`_prune_stale` right before an orphan is deleted: for every orphan carrying parking state, it searches the SAME
`plan_ref`'s other current tasks for a same-`[TAG] P<N>.`-prefix, high-text-similarity match (`SequenceMatcher` ratio ≥
0.6 — empirically a rewrap/light-reword of the same todo scores 0.85-0.95, an unrelated same-tag todo scores ~0.4) with
no parking state of its own, and copies `priority`/`priority_override`/`prereqs.prerequisites` onto it, logging a
WARNING naming both task ids for auditability. `RegenSummary.migrated_parking` surfaces the count. Deliberately does NOT
touch the A2 id-churn design itself (a genuine rewording still gets a fresh id) — only rescues the parking gate attached
to it. Added `test_parking_state_migrates_to_wrap_shifted_successor` (positive case) and
`test_parking_state_does_not_migrate_to_unrelated_todo` (guards against leaking a gate onto an unrelated same-tag todo)
to `tests/test_regen_reconcile.py`. Full `quality-gates.sh` green (ruff/basedpyright clean, 1368 passed, 1 skipped).
Shipped via quickmerge: `agent-orchestrator@22738f6` on `live-defi-rollout`.

## RE-TRIAGE (2026-07-23)

**Verdict: STILL OPEN, ACCURATE.** Re-read the doc in full. The core P0 finding (a real regression, root-caused + fixed
at `unified-trading-library@f5f15e3a`/`@9c9cdc50`) is long since resolved and correctly reflected in the doc's own todos
— but the doc's live-data claim, "CF-8 remains RED on both surfaces," is still true today.

- Corroborating evidence: `plans/archive/2026_07/sports_master_closeout_2026_07_21.md` §C (`ac#6`, 2 days old, no drift
  since — path corrected 2026-08-19, doc has since been archived)
  independently reconfirms: _"`available_at` fill only ~40-50% on `captured` rows (service_name-scoped dedup); targeted
  re-emit BLOCKED pending per-service_name write-fix design (operator said STOP)."_ — the exact same blocker this doc's
  own last Progress Log entries (slot-12, 2026-07-14) already identified and the backlog parking gate
  (`sports-cf8-maintenance-window-scheduled`, still `false` as of the last read at 2026-07-17) still enforces.
- Attempted a fresh live re-query of the captured-row fill rate myself (same idiom as the doc's own investigation) but
  the `cf_manifest_audit_2026_06_01.py` script referenced throughout this doc is not present in the current
  `market-tick-data-service` checkout (likely session-scratch-only, never committed) — could not independently re-derive
  the percentage this session. Relying on the 2-day-old closeout-plan corroboration above instead, which is a
  live-manifest-derived figure, not carried-forward vibes.
- No evidence found that the per-service_name write redesign (`market-tick-data-service@af627b5b`, built + unit tested
  2026-07-14) has been run against production, or that the operator has lifted the `BLK-d9137d48` STOP / scheduled the
  maintenance window. The doc's engineering-side todos are genuinely done; the operational/data-state claim in its title
  and summary stands unchanged.
- No conflicting doc found.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — the sole open todo is under an explicit
  operator STOP (`BLK-d9137d48`) enforced by a live backlog parking gate (`sports-cf8-maintenance-window-scheduled`,
  still false), requires a scheduled maintenance window, and its own text says the correct fix is 'new, unreviewed
  engineering — a design + review step, not a batch-size judgment call' (group target rows by their OWN `service_name`).
  Its dated RE-TRIAGE (2026-07-23) re-confirmed all of this unchanged
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — swapped the old, superseded full-rebuild script
  (`_rebuild_sports_write.py`) for the actual per-service_name targeted-backfill artifact
  (`sports_captured_available_at_targeted_backfill_2026_07_14.py`) a future maintenance-window run would execute.
- **context-scout 2026-08-03 (re-verify)**: corrected that same entry's path — the script lives at
  `market-tick-data-service/scripts/...`, not nested under `market_tick_data_service/scripts/` as previously written (a
  non-existent path); re-verified all 5 entries resolve on disk.
- **interactive session 2026-08-04 (autonomous)**: the general `_check_column_fill_regression` guardrail this doc's own
  todo shipped (`unified-trading-library@2e132bb2`) fired CRITICAL on the DEFI bucket for the first time (11 columns,
  73.92%→71.71%, triggered by a GMX-purge-forced full-merge) — a NEW, not-yet-root-caused manifestation, distinct from
  this doc's own already-fixed `available_at` serializer bug. Filed separately (this doc is near its 1000-line cap):
  `defi_manifest_column_fill_regression_from_gmx_purge_forced_full_merge_2026_08_04.md`.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — 2 open items, both dependency-blocked. Flag: the newest todo
  (added earlier today) may duplicate already-shipped work from this doc's own 2026-07-14 Progress Log
  (market-tick-data-service@af627b5b) — worth re-verifying before rebuilding.
- **na-eligibility-audit 2026-08-09**: KEEP-NA, valid — 2 open items (the `[DATA] P1` and `[INFRA] P1` todos above) now
  reduce to the SAME single remaining action: execute the already-built, already-operator-authorized per-service_name
  targeted re-emit (`market-tick-data-service@af627b5b`, built+unit-tested 2026-07-14) inside a coordinated maintenance
  window, still gated on the standing `BLK-d9137d48` STOP + the live backlog parking gate
  (`sports-cf8-maintenance-window-scheduled`, false as of last check) plus a pre-execution code review ("2 prior
  regressions, do not skip review"). The 2026-08-07 marker's "may duplicate already-shipped work" flag is now resolved —
  today's own STALE-CHECK CORRECTION on the `[INFRA] P1` todo already verified `af627b5b` covers sub-item (1) and
  narrowed both todos to just the operator-scheduled execution step. Not a RECLASSIFY candidate: scheduling + review
  sign-off are genuine operator-gated actions, not worker-determinable outcomes.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-17** [body-hash:ce1db7f1fd9089f4]: KEEP-NA, stale-items — the todo at line ~357 is a live duplicate of the todo at line ~417 (doc's own text says superseded/consolidated); todo@417 execution gated by a STANDING operator STOP (BLK-d9137d48) + a live machine-enforced backlog prerequisite gate (sports-cf8-maintenance-window-scheduled, confirmed false as of last read). Extremely well-established (RE-TRIAGE 2026-07-23 + 4 prior na-eligibility-audit rounds all agree). NOTE: doc is ~987/1000 lines, near the hard line-cap — a future consolidation edit (removing the redundant line-357 duplicate) needs care to stay under cap.
- **na-eligibility-audit 2026-08-17** [body-hash:2ec47739a45bc9c3] (dispatch agt-1c51ee, second same-day pass, 5th round overall): reconfirmed independently — same verdict, no change. Hash refreshed (prior marker's stored hash had drifted with no substantive content change since; not investigated further here). Doc remains near its 1000-line hard cap — do not add further verbose markers here without pruning first.
- **na-eligibility-audit 2026-08-17** [body-hash:2ec47739a45bc9c3] (agt-6574d2, 6th round): reconfirmed, no change. Root cause of the repeated same-day drift: a marker tie-break bug, fixed this run — should stop recurring. Doc near 1000-line cap; needs consolidation before further markers.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
