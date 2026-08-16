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
status: open
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
resolved_by: ""
locked_by: ""
created: "2026-08-16"
author: slot-32
last_updated: "2026-08-16"
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

## Recommended decision — needs operator/main-agent triage, not a unilateral fix from a one-shot worker

- [ ] [OPERATOR] P0. **Do not run any further defi manifest consolidator cycles, reclassification, or purge scripts
      against `instruments-store-defi-prd-central-element-323112` until this is understood** — including the
      reclassification-script todo already filed by
      `/plans/active/issues/dp_fetch_009_defi_dex_pool_swaps_uniswap_v3_ethereum_stale_schema_validation_failed_2026_08_16.md`
      todo 2, which was sized against the ~159M-row assumption and could behave unpredictably (or further
      overwrite recoverable state) against the current 138,612-row reality. Check whether GCS object versioning /
      `softDeletePolicy.retentionDurationSeconds` is enabled on this bucket (per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a reversibility check) BEFORE anything else
      writes to this object again — if a prior generation of `_index/availability_index.parquet` is still
      recoverable, that is the fastest path back to a correct baseline. Repo: deployment-service / infra.
- [ ] [SCRIPT] P0. **Root-cause the consolidator's last merge cycle** — pull the Cloud Run Job execution history +
      logs for the defi manifest consolidator around `2026-08-16T16:01:12Z` (mirrors the read-execution-history
      pattern already used elsewhere in `deployment_service/data_pipeline_monitors/cli.py`) and confirm whether it
      read the existing consolidated blob as a merge input before writing, or wrote directly from an (apparently
      near-empty) per-VM shard set. Cross-check `unified_trading_library/manifest_consolidator.py`'s merge logic for
      any path that can skip loading the prior canonical blob. Repo: unified-trading-library, deployment-service.
- [ ] [SCRIPT] P1. **Once root cause + recoverability are known, append a new DP-* registry entry** for this failure
      mode (consolidator produces a valid-but-catastrophically-smaller index) to
      `/codex/05-infrastructure/data-pipeline-alerts.md` + `.registry.yaml`, and add a detector: a consolidator
      write whose new row count drops by more than some large fraction (e.g. >50%) vs. the immediately prior
      canonical row count should page CRITICAL before the smaller file becomes "the new normal" that other
      checkers silently accept. Mirrors `DP-CATALOG-002`'s existing monotonic-guard pattern
      (`promote_catalogue/evaluate_monotonic_guard`) — this is the same shape of bug for the manifest consolidator
      instead of the catalogue promoter. Repo: deployment-service.
- [ ] [DATA] P1. **Re-verify DP-FETCH-009's dex_pool_swaps diagnosis** once the manifest state is understood — if
      the 159M-row baseline is recovered intact, slot-26's "13 stale dates, current code works" diagnosis in the
      sibling issue doc likely still stands unchanged (it was measured before this shrink). If the baseline is
      NOT recoverable, the whole defi capture-status history needs a fresh audit before trusting any DP-FETCH-009
      candidate list going forward. Repo: market-tick-data-service, deployment-service.

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
