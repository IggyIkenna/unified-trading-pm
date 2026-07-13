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
    plans/active/sports_manifest_canonicalisation_2026_06_01.md,
    codex/02-data/availability-manifest-and-data-status.md,
    codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-07-13
parent_epic: mtds_mdps_master
priority: P0
source: sports_manifest_canonicalisation-004 dispatch, slot 3, 2026-07-13
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-13
locked_by:
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
  EMPTY_CONFIRMED reason strings (`EXPECTED_NO_FIXTURE__truthset_*` variants) that don't match the current closed-set
  `EmptyConfirmedReason` enum exactly — **independently found + already filed** by slot 6 (this same plan's
  twenty-seventh touch) as `plans/active/issues/sports_rebuild_v9_free_text_reason_taxonomy_rejection_2026_07_13.md`
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
- [ ] [INFRA] P1. Once root-caused and fixed, re-attempt the full-corpus CF-8 `available_at` backfill on both sports
      surfaces (IS still at 62.9%, MDPS still at ~0%) — coordinate the maintenance window with the operator first to
      avoid a repeat of the cron-collision (Finding 1). (repo: market-tick-data-service) — **STILL BLOCKED on the P0
      above; NOT re-attempted this touch** (see Progress Log).
- [ ] [INFRA] P2. Fix the `write_projected_index`/`SportsProjectionCollector` FetchEvidence-serialization crash so
      `--beta-manifest-out` dry-run previews work again. (repo: market-tick-data-service)
- [x] ✅ [DATA] P2. Decide disposition for the 12,407 legacy `source='instruments_service'` rows (VENUES/LEAGUES) —
      backfill a real vendor source or accept as a known residual. (The 35,361 free-text-reason rows are tracked
      separately in `sports_rebuild_v9_free_text_reason_taxonomy_rejection_2026_07_13.md`.) (repo:
      market-tick-data-service, unified-api-contracts) — **DECIDED, slot 8, 2026-07-13**:
  - **Root cause confirmed historical, not a live bug.** UAC `SOURCE_PRIORITY` (`_source_priority_data.py`) registers
    `("sports", "VENUES")` and `("sports", "LEAGUES")` under `["api_football"]` — `instruments_service` (the writing
    SERVICE's own name) was never a valid vendor for these data_types. Traced the CURRENT active capture code
    (`instruments-service/instruments_service/engine/orchestrator/sports_fixtures.py::_sports_ref_source()`): it derives
    the manifest `source` from the entity's pipeline_mode (batch_-stripped), which correctly resolves to `api_football`
    for VENUES/LEAGUES today, and `record_captured()` itself **fail-fasts** (`MissingSourceError`) on any source not in
    `SOURCE_PRIORITY` — so the current write path CANNOT reproduce this mislabeling; it's guarded. The 12,407 rows are
    therefore genuinely **legacy** (written before this source-derivation/validation existed), not an active, recurring
    defect.
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
      corruption. (repo: unified-trading-library) — `unified-trading-library@<pending-commit>`, see Progress Log.
