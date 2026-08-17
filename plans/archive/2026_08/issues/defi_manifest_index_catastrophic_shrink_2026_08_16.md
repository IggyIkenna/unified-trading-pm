---
doc_type: issue
title:
  URGENT — defi consolidated manifest `_index/availability_index.parquet` shrank from ~159M rows/~6.8GiB to 138,612
  rows/3.9MB (measured live) — suspected active data-loss on the defi asset_group's SSOT manifest
summary: >-
  Side-finding while working DP-FETCH-009 escalation `agt-d2c3cc` (asset_group=defi, data_type=dex_pool_swaps —
  already resolved, see `/plans/active/issues/dp_fetch_009_defi_dex_pool_swaps_uniswap_v3_ethereum_stale_schema_validation_failed_2026_08_16.md`,
  filed by a duplicate dispatch of this SAME escalation on slot-26 a few hours earlier today). That prior issue doc's
  own "Recommended decision" section states the consolidated defi index is "~159M rows / ~6.8GiB" — consistent with
  `/codex/05-infrastructure/data-pipeline-alerts.md`'s "measured 2026-08-14" figure and with
  `deployment-service/deployment_service/data_pipeline_monitors/_attempted_failed_index.py`'s own module docstring
  (also citing 159M rows for the defi index, same OOM incident). Both were written using **live measurements taken
  earlier TODAY (2026-08-16)** — slot-26's doc reports isolating 7,841,388 raw `dex_pool_swaps` `attempted_failed`
  rows ALONE from that same index.

  Independently re-measuring the SAME object just now (this session, ~few hours after slot-26's investigation):
  `gcs_describe_object("gs://instruments-store-defi-prd-central-element-323112/_index/availability_index.parquet")`
  returns `size=3,905,306 bytes` (3.9 MiB), `last_modified=2026-08-16T16:01:12.252000+00:00`. A second, independent
  read via `pyarrow.fs.GcsFileSystem().open_input_file(...)` + `pq.ParquetFile(...).metadata.num_rows` confirms
  **138,612 total rows across ALL data_types in the defi bucket's consolidated index** — not just dex_pool_swaps,
  the WHOLE index. This is a ~99.9% row-count collapse (159M → 138,612) and a ~1750x size collapse (6.8GiB → 3.9MiB)
  on the SAME object, in the same day, after two independent sources (codex + a same-session sibling issue doc) both
  measured the large figure. `_index/per_vm/` for the same bucket currently holds exactly 1 shard, 3.77MB — closely
  matching the new total, consistent with the consolidator's last merge cycle having written out ONLY the per-VM
  delta as the new canonical index instead of merging it against the prior ~159M-row canonical baseline (a
  read-existing-canonical-first bug, not a delete).

  **Not yet root-caused** (out of scope for this one-shot dex_pool_swaps escalation worker to fix inline — filing per
  the "big finding: data-correctness / cross-repo / SSOT contradiction → NOTIFY OPERATOR + issue doc" HARD RULE
  rather than attempting a live fix against a not-yet-understood failure mode on a shared prod bucket).
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [deployment-service, unified-trading-library, market-tick-data-service]
scope: [engineer, admin]
tags:
  [
    defi,
    manifest,
    consolidator,
    data-loss,
    urgent,
    dp-manifest-001,
    availability-index,
    ssot,
  ]
related:
  [
    /plans/active/issues/dp_fetch_009_defi_dex_pool_swaps_uniswap_v3_ethereum_stale_schema_validation_failed_2026_08_16.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
source: data_pipeline_failure escalation agt-d2c3cc (side-finding, not the escalation's own scope)
resolved_by:
  slot-32 (2026-08-16, root-cause investigation — bucket-confusion false alarm, no data loss); independently
  re-confirmed 2026-08-17 (operator-approved P0 on stale BLK-46f447dc, unrelated slot) — same verdict, fresh
  live measurement
locked_by: ""
created: "2026-08-16"
author: slot-32
last_updated: "2026-08-17"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    unified-trading-library/unified_trading_library/manifest_consolidator.py,
    deployment-service/deployment_service/data_pipeline_monitors/_attempted_failed_index.py,
  ]
---

> **🟢 RETRACTED (2026-08-16, slot-32) — NOT a data-loss incident. Root cause: bucket confusion in the original
> investigation, not a consolidator failure.** The "~159M rows / ~6.8GiB" figure every other source cited belongs to
> `gs://market-data-tick-defi-prd-central-element-323112` (the MTDS tick-data manifest — confirmed still intact:
> `size=7,147,986,304 bytes`, `last_modified=2026-08-16T18:03:12Z`, live-verified via `gcs_describe_object`). This
> doc's own measured object, `gs://instruments-store-defi-prd-central-element-323112/_index/availability_index.parquet`
> (the SEPARATE instruments-service DeFi reference-data manifest), is a genuinely different bucket that has been stably
> at ~138,468-138,612 rows for at least the prior 40 hours of Cloud Run execution logs (2026-08-15T00:00Z through
> 2026-08-16T16:01Z) — every hourly cycle in that window shows either a no-op touch (`rows_in=0 rows_out=0`) or a small
> incremental merge (`rows_out` in the 138k range), never anything close to 159M. There was no "consolidator's last
> merge cycle" that shrank anything — this bucket was never large. See "Root cause investigation" below for full
> evidence. All 4 todos below are resolved/moot as a result.

## What I found

Live measurement of `gs://instruments-store-defi-prd-central-element-323112/_index/availability_index.parquet`
right now: 3,905,306 bytes / 138,612 rows / `last_modified=2026-08-16T16:01:12Z`. Every other source that touched
this SAME object earlier TODAY (a sibling issue doc from a duplicate dispatch of my own escalation, filed by
slot-26; `data-pipeline-alerts.md`'s own registry doc; `_attempted_failed_index.py`'s module docstring) reports
~159M rows / ~6.8GiB. `_index/per_vm/` for the same bucket now holds exactly 1 shard (3.77MB) — its size is close
enough to the new canonical total that the most likely mechanism is: the consolidator's last merge run wrote out
ONLY the per-VM shard delta as the new canonical index, discarding (not merging against) the prior ~159M-row
canonical baseline. This is the DP-MANIFEST-001 failure class (`consolidator not running / stale _index while
per-VM shards exist`) but INVERTED — here the consolidator evidently DID run (the blob is fresh, minutes old at
investigation time) but produced a catastrophically smaller output, a failure mode not currently in the DP-* alert
registry (`/codex/05-infrastructure/data-pipeline-alerts.md`).

## Why it matters

The consolidated `_index/availability_index.parquet` is the SSOT every reader (freshness checks, backfill
skip-decisions, DP-FETCH-009/007 alerting, coverage/data-status dashboards, honest-absence reasoning) consults for
"has this defi shard already been captured." If ~159M rows of `captured`/`attempted_failed` history genuinely
vanished from the canonical read path, every consumer now sees the defi asset_group as almost entirely
un-attempted — this would drive a MASSIVE re-attempt wave across every defi data_type (not just dex_pool_swaps),
each re-attempt racing real upstream rate limits / bad-indexer conditions, plausibly explaining today's DP-FETCH-009
spike as a SYMPTOM rather than the root cause slot-26's issue doc identified (that doc's "stale row" diagnosis may
itself need revisiting once this is understood — it read the SAME index at a point when it apparently still had the
larger row count, so its numbers were likely accurate AT THE TIME, but the ground has since shifted under it).

## Root cause investigation (2026-08-16, slot-32)

Pulled the Cloud Run Job execution history + logs for `uts-prod-manifest-consolidator-instruments-defi` (the job that
owns `instruments-store-defi-prd-central-element-323112`) via `gcloud logging read` over
`2026-08-15T00:00:00Z`–`2026-08-16T16:10:00Z` (40+ hours, well before this doc's `last_modified` measurement). Every
one of the ~40 hourly cycles in that window is either a no-op touch (`rows_in=0 rows_out=0`, mtime-only refresh) or a
real merge with `rows_out` in the 138,468–138,612 range (e.g. `2026-08-15T01:01:17Z rows_out=138468`,
`2026-08-15T13:50:43Z rows_out=138612`, `2026-08-16T00:35:57Z rows_out=138609`, `2026-08-16T13:50:41Z rows_out=138612`,
`2026-08-16T16:01:12Z rows_in=0 rows_out=0` — the exact cycle this doc's `last_modified=16:01:12.252Z` measurement
landed inside, which only touched mtime metadata, not row count). **The row count was never anywhere near 159M for
this bucket at any point in the pulled history** — there is no cycle where it drops from a large number to 138k; it
was always ~138k. No `WARNING`/`ERROR` severity log lines appear for this job in the window except one unrelated
transient `Application exec likely failed` blip at `2026-08-16T11:00:17Z` that self-recovered on the very next
scheduled tick (`11:01:04Z`, normal report line, no data impact).

Cross-checked `unified_trading_library/manifest_consolidator.py`'s merge logic for a path that skips the prior
canonical: the only way `consolidate()` full-rebuilds from shards alone (excluding the canonical) is
`canonical_mtime is None` in `_get_canonical_mtime()` — and that function was hardened 2026-07-12
(`tradfi_manifest_row_loss_regression_2026_07_12.md`) to RE-RAISE on any non-404 read failure instead of silently
returning `None`, specifically to prevent this exact failure class. No such full-rebuild-from-shards-only event
appears anywhere in the pulled logs for this bucket (every real-merge cycle's `shards=2` line implies the canonical
WAS read as a merge input — an incremental anti-join, not a cold full rebuild).

**The actual mechanism**: this doc's own live measurement (`gcs_describe_object` on
`instruments-store-defi-prd-central-element-323112`) is CORRECT for that bucket — 138,612 rows / 3.9MB is that
bucket's genuine, long-stable size. The "~159M rows / ~6.8GiB" figure every other source (the sibling DP-FETCH-009
issue doc, `data-pipeline-alerts.md`, `_attempted_failed_index.py`'s docstring) cites belongs to a DIFFERENT bucket —
`market-data-tick-defi-prd-central-element-323112` (the MTDS tick-data manifest, not the instruments-service
reference-data manifest) — confirmed by re-reading the sibling issue doc's own body (`dex_pool_swaps` rows written
"to `gs://market-data-tick-defi-prd-central-element-323112`") and by a live `gcs_describe_object` call against that
bucket right now: `size=7,147,986,304 bytes` (~6.66 GiB), `last_modified=2026-08-16T18:03:12Z`, generation
`1786903392731903` — fully intact and actively being written to, consistent with ~159M rows. **Two different
buckets, two different consolidator jobs, two different legitimate sizes — the original investigation session
(also slot-32) read the small IS-reference-data bucket and compared its row count against the large MTDS
tick-data bucket's cited figure, concluding a shrink that never happened.**

## Recommended decision (RETRACTED — see banner above; all 4 items resolved as moot / already covered)

- [x] [OPERATOR] P0. ~~Do not run any further defi manifest consolidator cycles…~~ **RESOLVED 2026-08-16, no data
      loss found** — `instruments-store-defi-prd-central-element-323112` was never at 159M rows; nothing needs
      pausing or recovering. `market-data-tick-defi-prd-central-element-323112` (the bucket the 159M figure actually
      describes) is independently confirmed intact and actively growing. Repo: deployment-service / infra — N/A.
- [x] [SCRIPT] P0. **Root-cause the consolidator's last merge cycle** — DONE. See "Root cause investigation" above:
      pulled Cloud Run Job execution history + logs for `uts-prod-manifest-consolidator-instruments-defi` around
      `2026-08-16T16:01:12Z` (and the prior 40h); confirmed every real-merge cycle reads the canonical as a merge
      input (no cold full-rebuild-from-shards-only event occurred); the row count was never larger than ~138k for
      this bucket. Root cause of the APPARENT shrink is a bucket-identification mix-up in the original
      investigation, not a consolidator defect. Repo: unified-trading-library, deployment-service — no code change
      needed (the merge logic behaved correctly throughout).
- [x] [SCRIPT] P1. ~~Append a new DP-* registry entry for this failure mode~~ **NOT NEEDED — already covered.** No
      catastrophic-shrink failure mode occurred to register, and the general shape (a consolidator/writer producing
      a much-smaller-than-expected index) is already defended in depth per
      `/codex/05-infrastructure/manifest-consolidator-ssot.md` § "Writers: per-VM shard mode…": the legacy-CAS
      writer path REFUSES any write whose merged output is >2% smaller than the base it just read
      (`_INDEX_SHRINK_GUARD_PCT` / `ManifestIndexShrinkRefusedError`, UTL `unified-trading-library@45a43438`), and
      the consolidator's own `_ROW_COUNT_REGRESSION_ALERT_THRESHOLD` (0.1%, observability-only) is the sibling check
      on the merge side. Repo: deployment-service — no new todo filed.
- [x] [DATA] P1. ~~Re-verify DP-FETCH-009's dex_pool_swaps diagnosis~~ **MOOT — baseline was never compromised.**
      `market-data-tick-defi-prd-central-element-323112` (the bucket DP-FETCH-009's diagnosis actually reads) is
      confirmed intact (see Root cause investigation above); slot-26's original diagnosis in the sibling issue doc
      stands unchanged. Repo: market-tick-data-service, deployment-service — no re-verification needed.

## Progress Log

- **2026-08-16 (data_pipeline_failure escalation agt-d2c3cc, slot-32)**: Assigned escalation (DP-FETCH-009,
  defi/dex_pool_swaps) turned out to already be resolved by a duplicate dispatch of the SAME escalation ID on
  slot-26 earlier today (see the sibling issue doc linked above) — diagnosis + live remediation already applied,
  nothing further needed for that specific finding. While independently re-deriving the same manifest data (bounded
  pyarrow row-group streaming read, mirroring `_make_streaming_index_reader`'s OOM-safe pattern, to sanity-check the
  dex_pool_swaps attempted_failed breakdown), found the consolidated defi index total row count is 138,612 — not
  the ~159M cited by every other source that touched this object earlier today, including the sibling issue doc
  itself. Cross-verified via an independent API path (`gcs_describe_object`, not pyarrow) — confirmed via object
  `size`/`last_modified` directly against GCS, ruling out a client-side caching artifact. Checked `_index/per_vm/`
  (1 shard, 3.77MB — consistent with "consolidator wrote out only the delta" as the leading hypothesis). Did not
  attempt any fix — this is a shared-prod-bucket, not-yet-understood failure mode, squarely the "big finding, notify
  operator" case, not a one-shot worker's unilateral-fix scope. Filed this doc + will ping main agent directly given
  the severity (possible active data loss on the defi asset_group's SSOT manifest).
- **2026-08-16 (root-cause investigation, slot-32, task `defi_manifest_index_catastrophic_shrink-a4d9f031deba`)**:
  Pulled `uts-prod-manifest-consolidator-instruments-defi`'s Cloud Run Job execution history + logs
  (`gcloud logging read`) over the 40 hours preceding this doc's filing — every cycle shows `instruments-store-defi`'s
  canonical index stably at 138,468-138,612 rows; no cycle anywhere in that window shows a shrink FROM a large row
  count. Cross-checked `manifest_consolidator.py`'s merge logic: the only cold-full-rebuild-skips-canonical path
  (`canonical_mtime is None`) was hardened 2026-07-12 to re-raise rather than silently proceed, and no such event
  fired in the logs regardless. Live-verified via `gcs_describe_object` (UTL `cloud_interface`, per the workspace's
  no-subprocess-gcloud-object-ops rule) that `market-data-tick-defi-prd-central-element-323112` — the bucket the
  cited "~159M rows / ~6.8GiB" figure actually belongs to, per the sibling DP-FETCH-009 issue doc's own body — is
  fully intact (7,147,986,304 bytes, actively growing, last written 2026-08-16T18:03Z). **Root cause: the original
  investigation session (also slot-32) compared two DIFFERENT buckets' row counts** — `instruments-store-defi-...`
  (this doc's live measurement, genuinely ~138k rows, always has been) against a figure that belongs to
  `market-data-tick-defi-...` (a separate consolidator, separate bucket, genuinely ~159M rows, never touched). No
  data loss occurred anywhere. Retracted the doc's premise, resolved all 4 recommended-decision todos as moot/covered,
  flipped `status: resolved`. No code changes needed — the consolidator behaved correctly throughout; this was purely
  a same-session bucket-identification error, not an infrastructure defect.
- **2026-08-17 (independent re-verification, prompted by the operator approving a P0 on the STALE `BLK-46f447dc`
  blocked question, unrelated slot)**: The operator approved a P0 ("freeze consolidator writes, check reversibility,
  root-cause the merge bug") on 2026-08-17 in response to `BLK-46f447dc` — a blocked question filed 2026-08-16 by a
  worker on an unrelated task, escalating the ORIGINAL (pre-retraction) finding above. That blocked question was
  apparently never re-visited after slot-32's same-day retraction landed (`unified-trading-pm@64eed6c4e0`,
  2026-08-16T18:34Z, ~2h20m after the original P0 filing) — the operator was very likely answering a stale question
  about an incident already diagnosed as a false alarm before their approval landed. Searched the live AO backlog
  (`check-ao-backlog-status.sh "46f447dc"`) for the blocked-question id itself: 0 matches (blocked-question ids are
  not task ids/plan_refs/titles, so this doesn't confirm answered/open either way; the AO dashboard's `/api/blocked/*`
  routes are `AUTHED_DEPS`-gated and this session has no dashboard JWT, so its live state could not be directly
  confirmed from here — flagging for the operator/a session with dashboard access to close explicitly if still open).
  Independently re-measured BOTH buckets fresh, live, via UTL `gcs_describe_object` +
  `gcs_bucket_soft_delete_retention_seconds` (`unified_trading_library.cloud_interface`) — no subprocess
  gcloud/gsutil:
  - `gs://instruments-store-defi-prd-central-element-323112/_index/availability_index.parquet`: size=3,914,854 bytes,
    last_modified=2026-08-17T15:01:29.661Z, generation=1786978889651629. A second, independent read via
    `pyarrow.fs.GcsFileSystem` + `pq.ParquetFile(...).metadata.num_rows` (footer-only, no full-file scan) confirms
    **138,753 total rows** — up only +141 rows from the 2026-08-16 measurement (138,612) over ~23 hours, i.e. normal
    small incremental growth, not a shrink and not a jump toward 159M. This bucket has never been anywhere near 159M
    rows.
  - `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` (the bucket the
    original "~159M rows/~6.8GiB" figure actually describes): size=7,265,426,420 bytes (~6.77 GiB),
    last_modified=2026-08-17T15:49:47.473Z, generation=1786981787460717 — grown from the ~6.66 GiB measured
    2026-08-16, confirming it is intact and still actively being written, not frozen or shrunk.
  - **Reversibility, both buckets**: `gcs_bucket_soft_delete_retention_seconds()` returns **604800** (7 days) for
    both `instruments-store-defi-prd-central-element-323112` and `market-data-tick-defi-prd-central-element-323112`
    — matches the 2026-07-27 fleet-wide sweep baseline in
    `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a. Even in a genuine-shrink counterfactual, a prior
    generation would have been recoverable within a 7-day window — moot here since no shrink occurred.
  - **Write path**: confirmed healthy and NOT frozen — freezing was never warranted and would have been actively
    harmful (blocks real captures from merging, triggers false staleness alerts). Both consolidator Cloud Scheduler
    crons are `ENABLED` on their documented cadence: `uts-prod-manifest-consolidator-instruments-defi-cron`
    (`0 * * * *`, hourly, matches the `AG_STALENESS_BUDGET_SEC["defi"]=3600` override in
    `manifest-consolidator-ssot.md`) and `uts-prod-manifest-consolidator-market-data-defi-cron` (`*/1 * * * *`).
  - **Root-cause corroboration**: re-confirmed the shrink-guard defense-in-depth the retraction cited is real code,
    not an asserted claim — `_INDEX_SHRINK_GUARD_PCT` / `ManifestIndexShrinkRefusedError` live in
    `unified-trading-library/unified_trading_library/manifest_writer/_writer.py` (the legacy-CAS writer path), and
    `_ROW_COUNT_REGRESSION_ALERT_THRESHOLD = 0.001` (0.1%, observability-only) is real in
    `unified_trading_library/manifest_consolidator.py:2145`.
  - **Verdict**: the 2026-08-16 retraction stands, now independently corroborated by a second, later,
    differently-tooled measurement (fresh `gcs_describe_object` + a second independent pyarrow footer read, vs. the
    retraction's own `gcs_describe_object` re-check) — no data loss occurred, no code changes needed, no restore
    action is warranted (there is nothing to restore from), and no freeze was applied (none was needed). The only
    open loose end is confirming `BLK-46f447dc` itself shows answered/resolved in the AO dashboard — not this doc's
    substance — left for the operator or a session with dashboard JWT access.
