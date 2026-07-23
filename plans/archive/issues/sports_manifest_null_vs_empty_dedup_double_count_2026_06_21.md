---
doc_type: issue
title: Sports IS manifest double-count is caused by NULL-vs-empty-string in optional dedup columns, not pipeline_mode
summary:
  While implementing the one-off `canonicalize_sports_legacy_pipeline_mode_2026_06_21.py` (re-stamp legacy
  `batch_instruments_service` sports rows → `batch_<source>` + fill blank `empty_confirmed` re...
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags:
  [sports, manifest, data-correctness, consolidation, canonicalisation, pipeline-mode, data-quality, honest-coverage]
related:
  [
    plans/active/issues/sports_league_id_out_of_universe_overcapture_2026_06_24.md,
    plans/active/issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md,
  ]
created: 2026-06-21
parent_epic: sports_master
priority: P1
source:
  [
    instruments-store-sports-prd/_index/availability_index.parquet (live read 2026-06-21,
    re-verified 2026-07-08,
    re-verified 2026-07-13),
    unified_trading_library/manifest_consolidator.py (_resolve_dedup_cols / _DEDUP_NULL_SENTINEL),
    unified_trading_library/manifest_writer/_read_index.py (_merge_shard_frames,
    2026-07-08 fix),
    instruments-service/scripts/canonicalize_sports_legacy_pipeline_mode_2026_06_21.py,
  ]
assigned_vm: planning
resolved_by: sports_master_closeout_2026_07_21 investigation (2026-07-21)
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-21
---

## What I found

While implementing the one-off `canonicalize_sports_legacy_pipeline_mode_2026_06_21.py` (re-stamp legacy
`batch_instruments_service` sports rows → `batch_<source>` + fill blank `empty_confirmed` reasons), the dry-run verified
the stated double-count mechanism is **incorrect**:

- The task diagnosis said: `pipeline_mode` is part of the consolidator dedup key, so the same cell exists under both
  `batch_instruments_service` (old) and `batch_<source>` (new), and re-stamping the legacy `pipeline_mode` makes the
  rows share the key → the consolidator collapses them.
- **Verified against the live index + the consolidator source**: `pipeline_mode` is **NOT** in the dedup key. The key is
  `_BASE_DEDUP_COLS = (date, venue, data_type, service_name)` + the present `_OPTIONAL_DEDUP_COLS`
  (`timeframe, league_id, chain, instrument_type, underlying, feature_group, model_family, training_period, strategy_id, client_id, instruction_type, instrument_id`).
  Re-stamping `pipeline_mode` alone collapses **0 rows**.
- The **real splitter** is a **NULL-vs-empty-string mismatch in the OPTIONAL dedup columns**: legacy rows carry parquet
  `NULL` where the newer/canonical rows carry `""`. The consolidator coalesces `NULL` to a distinct sentinel
  (`__UTL_CONSOLIDATOR_NULL_4e8a2__`) and leaves `""` as `""`, so `NULL != ""` → the twins never merge. Example:
  FIXTURES `date=2020-07-01, league=EPL` exists as a legacy `captured` row (instrument_count=4, all optional dims NULL)
  AND a newer `empty_confirmed` row (count=0, optional dims `""`).
- Normalising the **legacy** rows' NULL optional dims → `""` collapses the duplicate twins (consolidated index
  `4,127,195 → 4,107,758` distinct dedup-keys; FIXTURES captured `76,087 → 76,006` distinct). This is now done by the
  one-off (step 1b), scoped to legacy rows only and convergent with the canonical `""` convention.

## Why it matters

1. The double-count fix shipped by the one-off relies on the **NULL→"" normalisation**, not the pipeline_mode rename.
   Anyone reading the original task diagnosis would conclude the rename fixes it — it does not.
2. **The NULL/"" inconsistency is NOT legacy-only.** The same dry-run shows NON-legacy rows ALSO carry a mix of NULL and
   `""` across optional dims (e.g. `timeframe`: non-legacy 1,365,481 NULL / 565,606 `""`; `underlying`/`feature_group`/
   `…`: non-legacy 1,365,481 NULL / 565,606 `""`). So there may be additional `NULL`-vs-`""` duplicate twins among
   non-legacy rows (and across other asset_groups' IS/MTDS indices) that this one-off does NOT touch (it is scoped to
   legacy `batch_instruments_service` rows). A full-corpus NULL→"" canonicalisation of optional dedup columns is a
   larger, separate operation.
3. Root-cause options (operator decision): (a) make the **consolidator** treat `NULL` and `""` as equal in the dedup key
   (coalesce both to the same sentinel) — a single SSOT fix that retroactively de-dupes every bucket; OR (b) a
   full-corpus writer-side normalisation so every optional dedup column is `""`-not-NULL. Option (a) is the cleaner
   single-point fix and avoids re-walking every parquet.

## Recommended decision

- The sports legacy one-off (`canonicalize_sports_legacy_pipeline_mode_2026_06_21.py`) is correct and shipped — it
  delivers the task's three goals (pipeline_mode canonical, typed reasons, double-count collapsed) via the corrected
  mechanism, scoped to legacy rows.
- **Operator: pick the systemic fix** for the NULL-vs-`""` dedup-key mismatch (consolidator coalesce-both vs full-corpus
  normalisation). If (a), a small change to `_duckdb_consolidate_and_write` (coalesce `NULL` AND `''` to one sentinel)
  fixes it fleet-wide with no whole-corpus walk. Until then, non-legacy NULL/"" twins in sports (and likely cefi/defi/
  tradfi/prediction IS + MTDS indices) remain a latent double-count.

## Update 2026-07-08 (slot-7, data_engineering) — option (a) WAS shipped, but two gaps left the twins live

Confirms this doc's option (a) is no longer hypothetical —
`unified_trading_library.manifest_consolidator._dedup_key_sql` already coalesces NULL and `""` to one sentinel (shipped
as `unified-trading-library@f5ec2291f`, §9.2b, referenced from
`plans/archive/2026_07/understat_local_backfill_completion_2026_07_06.md`). Verified the SQL is _correct_ by feeding it
the exact duplicate pair directly (DuckDB `PARTITION BY` on the normalized key correctly picks 1 survivor). Yet the LIVE
sports canonical index still carried the twins. Two independent gaps, both now closed:

1. **Reader-side gap (different code path, same bug class)** —
   `unified_trading_library/manifest_writer/_read_index.py ::_merge_shard_frames` (the pandas dedup
   `read_availability_index` uses to layer a caller's just-written per-VM shard on top of the consolidated blob) never
   got the equivalent NULL/`""` normalization; it deduped on raw values, so a caller's own fresh read could see the same
   NULL-vs-`""` twin the consolidator was designed to prevent. Fixed + shipped: `unified-trading-library@d64563da`
   (`fix(manifest): dedup NULL vs empty-string optional dims in reader shard merge`), with a regression test
   (`test_reader_dedups_optional_dim_null_vs_empty_string`).
2. **Consolidator staleness/operational gap** — even after the SQL fix (#1 above notwithstanding), the LIVE sports
   canonical still held ~297 un-collapsed `(date, league_id, data_type)` keys with an `attempted_failed` row coexisting
   with a newer valid-status row (discovered while driving `understat_local_backfill_completion-001`'s retry-verify
   loop, which never reached 0 `attempted_failed` because of these twins). This means the DEPLOYED Cloud Run
   consolidator job's incremental cycles were NOT applying the `_dedup_key_sql` fix continuously in production — either
   a stale image (never rebuilt post-`f5ec2291f`) or the incremental anti-join is missing some contested-key cases the
   isolated SQL test doesn't reproduce. **Not root-caused further here** — out of this session's scope (infra/deploy
   craft, not data_engineering) and already tracked as
   `plans/archive/2026_07/understat_local_backfill_completion_2026_07_06.md` task -003 ("confirm §9.2b consolidator
   deployed"). **Mitigated for sports only**: ran
   `python -m unified_trading_library.manifest_consolidator --bucket instruments-store-sports-prd-central-element-323112 --force`
   (one-off full rebuild, sanctioned per the tool's own docstring: "one-off seed after backfill"). Result:
   `rows_in=5,175,040 rows_out=4,901,461 dedup_dropped=273,579` — a FAR larger cleanup than the 297 keys I could see
   from the narrow attempted_failed/XG_SHOTS angle, confirming this NULL/`""` twin pattern is broad across the whole
   sports manifest, not just understat. Cross-check needed for cefi/defi/tradfi/prediction buckets — task -003 (or a new
   dedicated audit) should verify whether their Cloud Run consolidator jobs are running the fixed image, and if not, run
   the equivalent one-off `--force` rebuild per bucket (each is a quick, self-contained, locked operation — no
   whole-corpus GCS walk, just the existing canonical + shards).

## Update 2026-07-13 (slot-3, interactive session) — the "not root-caused further" gap is CONFIRMED still open and recurring

Cross-referencing this doc's "Update 2026-07-08" section (the deployed Cloud Run consolidator's incremental cycles NOT
applying the dedup fix continuously in production — "either a stale image ... or the incremental anti-join is missing
some contested-key cases", explicitly "Not root-caused further here"): a fresh live-manifest re-verify today found the
sibling doc `sports_xg_shots_instrument_type_dedup_key_instability_2026_07_09.md`'s fix — independently verified clean
("0 duplicate groups remain system-wide") on 2026-07-09 — has a fresh recurrence 4 days later (same 2024-12-14 big-5
cells, plus a new instance on XG itself). This is consistent with — and likely the same root mechanism as — this doc's
still-open gap: something about the consolidator's incremental/per-VM-shard merge path is not durably retiring
corrective/dedup fixes, so a previously-collapsed duplicate can reappear without any new "bad" write. This raises the
priority of actually root-causing item 2 above (rather than continuing to rely on periodic manual `--force` rebuilds as
the only mitigation) — tracked as a todo in `plans/archive/2026_07/understat_local_backfill_completion_2026_07_06.md`
(2026-07-13 entry) scoped to the sports bucket; the cross-bucket check this doc already calls out
(cefi/defi/tradfi/prediction) remains a separate, not-yet-scheduled follow-up.

**CORRECTION (same session, later 2026-07-13): the "recurrence" above was a misdiagnosis — it was NOT this doc's
consolidator gap.** Root-caused fully: the fresh 2026-07-13T06:21Z duplicates were collateral damage from an unrelated
bug in `market-tick-data-service`'s sports manifest rebuild script, run as part of
`sports_manifest_canonicalisation_2026_06_01.md`'s E4 migration apply-pass the SAME morning (a hardcoded `service_name`

- missing `asset_group` re-emitted 684,158 rows fleet-wide under the wrong service_name at `06:16:51Z`–`06:23:04Z` — see
  that plan's E3/E4 entry for full detail, the fix at `market-tick-data-service@55f9e961`, and the cleanup at
  `instruments-service@2f56038e`). The sibling doc's 2026-07-09 fix DID hold; this doc's own "incremental cycle not
  applying the fix continuously" gap (Update 2026-07-08) is therefore **NOT re-confirmed by this event** — it remains
  exactly as before (a real, still-open, still-unexplained gap worth root-causing on its own merits, but the 2026-07-13
  "recurrence" is not fresh evidence for it). Correcting the record so a future reader doesn't over-weight this data
  point.

## Update 2026-07-21 (sports_master_closeout investigation) — ROOT-CAUSED, FIXED, AND LIVE-VERIFIED CLOSED

Dispatched to close the "Update 2026-07-08" item 2 / "Update 2026-07-13" gap ("Not root-caused further here … either a
stale image … or the incremental anti-join is missing some contested-key cases the isolated SQL test doesn't
reproduce"). Findings, in order:

**1. Deployed Cloud Run image staleness check — NOT stale today (with evidence, not just ancestor-checking).**

- The two sports consolidator jobs (`uts-prod-manifest-consolidator-instruments-sports`,
  `uts-prod-manifest-consolidator-market-data-sports`,
  `deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf`) both run
  `asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/market-tick-data-service:latest`. The
  live execution resolved that tag to digest `sha256:5ea4fc9c3d83588a1d6aa62619de9aad6b6ad6db5c921739ed0b532485aadbc5`,
  pushed **2026-07-21T13:33:29Z (same day, ~2h before this check)** —
  `gcloud artifacts docker images list … --include-tags`.
- **Content-verified, not just date-inferred**: `docker pull`ed that exact digest and ran
  `python -c "import unified_trading_library; ..."` inside it. The installed package (`unified-trading-library==0.55.0`,
  editable at `.deps/unified-trading-library`, staged from LDR tip at build time per the 2026-07-20 DEP-SKEW-GUARD
  structural fix in `market-tick-data-service/Dockerfile`) contains: the
  `_DEDUP_NULL_SENTINEL = "__UTL_CONSOLIDATOR_NULL_4e8a2__"` coalesce fix (`f5ec2291f`, 2026-07-06) in
  `manifest_consolidator.py`, the reader-side `_merge_shard_frames` optional-dim normalization (`d64563da`, 2026-07-08)
  in `manifest_writer/_read_index.py`, AND a marker from a later 2026-07-19 fix
  (`read_availability_index_column_selection_dependent_merge_2026_07_19`) — proving the image tracks near-current LDR
  tip, not a stale pin.
- **Every other GCP manifest-consolidator Cloud Run job shares the exact same image string**
  (`gcloud run jobs describe … --format="value(spec.template.spec.template.spec.containers[0].image)"` on
  `instruments-{cefi,defi,tradfi,prediction}`, `market-data-{cefi,defi,tradfi,prediction}`, `features-cefi`,
  `execution`, `ml-training-artifacts`, `strategy`) — all `market-tick-data-service:latest`. One current image = all of
  them current; there is no per-bucket staleness to find on GCP.
- **AWS side** (Batch Fargate, ECR `market-tick-data-service:latest`): last pushed **2026-07-17T04:29:43Z** (4 days
  behind GCP but still 9-11 days after both fix commits). Content-verified the same way (`docker pull` by digest +
  grep): carries the `_DEDUP_NULL_SENTINEL` fix and the reader-side `_merge_shard_frames` function.
  (`batch:Describe JobDefinitions` was access-denied from this session's role, so individual AWS job definitions weren't
  enumerable, but per the manifest-consolidator SSOT every AWS consolidator job references this same ECR `:latest` tag,
  so the ECR push check covers all of them by the same logic used for GCP.)

**2. The deeper "incremental anti-join misses contested-key cases" bug — ALREADY independently root-caused + fixed
2026-07-10, 2 days after this doc's own Update-2026-07-08 entry, but never cross-referenced here.**

`plans/active/issues/defi_manifest_consolidator_duplicate_race_2026_07_10.md` (found during an unrelated DeFi backlog
session) root-caused the EXACT mechanism this doc's item 2 speculated about: the incremental merge path
(`_duckdb_merge_payload`) splits the canonical into `contested` rows (keys touched by the current cycle's incoming
shards — correctly window-deduped) and `survivors` (all other rows — streamed through **completely unchanged, zero
self-dedup**). Consequence: **any duplicate that ever lands in the canonical, by ANY mechanism — including a NULL/""
twin created before the `f5ec2291f` SQL fix shipped — persists forever**, because incremental cycles only ever
re-examine keys the _current_ cycle's shards touch, never re-verify the untouched 99%+ of the canonical against itself.
This is precisely why the SQL fix tested correct in isolation (§ Update 2026-07-08: "fed it the exact duplicate pair
directly … correctly picks 1 survivor") yet pre-existing duplicate twins already resident in the live canonical kept
surviving cycle after cycle — they were never in anyone's `contested` set again.

- **Fix**: `unified-trading-library@0de04b6e` (2026-07-10) — apply the same window-dedup already used for `contested`
  rows to `survivors` too (later split into `survivors_clean`/`survivors_deduped` in `@800af156` the same day, for an
  OOM regression at defi's 27M-row scale — irrelevant to sports' much smaller canonical). New regression test
  `test_consolidate_incremental_self_dedups_untouched_canonical_duplicates`, verified fail-before/pass-after via a
  stash-based check, not inline reasoning.
- **That doc's own P2 todo (2026-07-10) already scanned all 5 asset groups** with the correct per-schema grain and found
  **sports already clean (0 genuine duplicates)** post-fix, alongside cefi 0, defi 0, tradfi (346 rows/173 groups,
  cleaned), prediction (6,284 rows/3,142 groups, cleaned). The fix + cleanup predates this doc's own "Update 2026-07-13"
  entry by 3 days — this doc's remaining "not root-caused further" framing was simply not updated to reflect it.
- This also explains the stale-image half of the 2026-07-08 finding: that same closure doc records the MTDS image
  independently found stale on 2026-07-10 (pinned `BASE_IMAGE_DIGEST` predating the fix) and rebuilt/redeployed same
  day, with the local `market-tick-data-service` Dockerfile git history confirming an **urgent** digest-pin bump
  (`72fa3f42`, 2026-07-10T16:28 +01:00: _"Fleet-wide fan-out … to pick up unified-trading-library@0de04b6e (the
  manifest-consolidator duplicate-row fix) — urgent, the consolidator running via this service's Cloud Run job needs
  this deployed ASAP"_). So: **yes, the deployed image was genuinely stale in the narrow 2026-07-08 → 2026-07-10
  window** — both halves of this doc's open hypothesis were partially right (a real stale-image gap AND a real deeper
  bug), and both are now closed.

**3. Live re-verification today (2026-07-21), against the CURRENT production canonical, using the exact production
dedup-key SQL (`_BASE_DEDUP_COLS` + `_OPTIONAL_DEDUP_COLS` + `_dedup_key_sql` NULL/"" coalesce), not a narrow
attempted_failed/XG_SHOTS angle:**

| Bucket                         | Rows      | Duplicate dedup-key groups |
| ------------------------------ | --------- | -------------------------- |
| `instruments-store-sports-prd` | 5,384,397 | **0**                      |
| `market-data-tick-sports-prd`  | 1,974,679 | **0**                      |
| `instruments-store-cefi-prd`   | 84,266    | **0**                      |
| `instruments-store-defi-prd`   | 118,809   | **0**                      |
| `instruments-store-tradfi-prd` | 27,203    | **0**                      |
| `instruments-store-pred-prd`   | 27,115    | **0**                      |

(`market-data-tick-{cefi,defi,tradfi,pred}-prd` were not downloaded for a full duplicate scan — defi alone is 1.87 GB —
but each shows a healthy `success:true` cycle in `_index/latest.json` within the last minute of this check, consistent
with a live, functioning consolidator, and their consolidator jobs share the identical verified-current image.)

**Conclusion — CLOSED.** Both halves of this doc's open question are answered: the deployed image WAS stale for a ~2-day
window ending 2026-07-10, and there WAS a deeper incremental-merge bug (survivors never self-deduped) — both are now
fixed, the fix is deployed and content-verified current on every consolidator bucket (same shared image), and the live
production sports manifests show zero NULL-vs-empty-string (or any other) duplicate dedup-key groups today. No code
change was needed from this session. `sports_master_closeout_2026_07_21.md` §2-C / §7 item 4 updated to reflect this is
resolved, not a pending blocker for the post-floor recompute.

## Non-FIXTURES blank-reason residue (left untouched, by design)

The same one-off leaves **612,682** consolidated-index `empty_confirmed` blank `error_reason` rows untouched
(non-FIXTURES sports data_types:
FIXTURE_STATS/FIXTURE_LINEUPS/FIXTURE_EVENTS/PREDICTIONS/ODDS/PLAYER_STATS/XG/WEATHER/INJURIES/…). Reason: their
non-blank twins use a MIX of `EXPECTED_NO_FIXTURE` / `EXPECTED_INSTRUMENT_NOT_LISTED` / `SOURCE_RETURNED_ZERO` — no
single canonical reason is derivable per data_type, so filling one would be a guess. A follow-up that re-derives the
correct reason per (data_type, date, league) from the fixture-presence + source-coverage SSOT (rather than a blanket
fill) is needed to close these. Tracked here for the sports/manifest epic.
