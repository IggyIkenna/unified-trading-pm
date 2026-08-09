---
doc_type: issue
title: >-
  DP-FETCH-009 escalation (agt-e488d1) — cefi book_snapshot_5 fresh attempted_failed traced to a since-stopped process
  running pre-2026-07-16 code that batch-attempted ASTER book_snapshot_5 (current HEAD already excludes it; no
  recurrence in 14h+)
summary: >-
  Escalation agt-e488d1 (data_pipeline_failure worker, slot 6) fired on DP-FETCH-009 (asset_group=cefi,
  data_type=book_snapshot_5, 9,883 attempted_failed of 935,767 attempted, "Fresh — 2193 attempted_failed row(s) in the
  last 1d"). Bounded manifest read (read_availability_index_safe, filters=data_type/capture_status/venue, no
  whole-corpus walk) found the fresh slice dominated by venue=ASTER, error_reason=UpstreamTimestampBiasError,
  pipeline_mode=batch_aster, source=aster — 2,000 of the 2,625 fresh (>=2026-08-08) rows, spread over ~40 historical
  dates (2026-07-01..2026-07-20ish), all written 2026-08-08T21:34Z.. 2026-08-09T01:24Z, then STOPPED (zero activity
  since, ~14h+ quiet at investigation time). Root-caused via direct code read + a live functional check against this
  slot's HEAD-of-branch clone: ASTER book_snapshot_5 has been excluded from the batch fetch universe since
  unified-api-contracts@7754661a (2026-07-15) / market-tick-data-service@2e674d1f (2026-07-16)
  (`VENUE_DATA_TYPE_NO_BATCH_SOURCE["ASTER"]` + `batch_data_types_for_venue()` in `_onchain_perp_batch_live_only.py`) —
  confirmed live: `batch_data_types_for_venue("ASTER", ["trades","book_snapshot_5","derivative_ticker"])` returns
  `["trades","derivative_ticker"]` on this HEAD checkout, book_snapshot_5 filtered out before any fetch is attempted.
  The 2026-08-08/09 burst is therefore NOT reproducible on current code — whatever process wrote these rows
  (pipeline_mode=batch_aster, i.e. OnchainPerpBatchHandler) was running a tarball build predating the July fix by ~3-4
  weeks, hit ASTER's current-snapshot-only depth endpoint for a HISTORICAL target_day, got back a "now"-timestamped
  snapshot, and PartitionedTickWriter's validate_day_partition_alignment correctly rejected the day-misaligned chunk as
  UpstreamTimestampBiasError on every one of the ~50 symbols/day it touched. Same systemic risk class as the
  already-tracked tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md (a VM/process running code older
  than its last redeploy), a DIFFERENT specific incident/window/bug than that doc's (that doc's ASTER book_snapshot_5
  finding was the LIVE subscribe-frame-size cliff, pipeline_mode=live_aster, empty_confirmed — not this BATCH
  day-alignment failure). No code fix required (current code already correct); could not identify the specific offending
  VM within this one-shot's scope (no currently-running instance name-matches an onchain-perp/ASTER backfill launcher;
  nothing to kill or relaunch).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags:
  [
    dp-fetch-009,
    aster,
    book_snapshot_5,
    upstream-timestamp-bias,
    tarball-staleness,
    attempted-failed,
    data-pipeline-alerts,
  ]
related:
  [
    /plans/active/issues/tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md,
    /plans/active/issues/cefi_window_scoped_coverage_gap_okx_binance_bybit_2024_2026_2026_08_09.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
  ]
created: "2026-08-09"
author: slot-6 (data_pipeline_failure escalation agt-e488d1)
parent_epic: cefi_master
priority: P2
assigned_vm: NA
execution_scope: local-only
drift_direction: fix
estimate_class: research
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
resolved_by:
locked_by:
depends_on: []
source: [DP_RUN_MOSTLY_EMPTY escalation agt-e488d1, wall_type=data_pipeline_failure]
---

# DP-FETCH-009 cefi/book_snapshot_5 fresh-attempted_failed burst — ASTER stale-tarball, self-resolved

## What I found

Escalation `agt-e488d1` context: CRITICAL DP_RUN_MOSTLY_EMPTY (DP-FETCH-009), asset_group=cefi
data_type=book_snapshot_5, 9,883 attempted_failed of 935,767 attempted (1.1%, abs>=500 triggers the alert), "Fresh —
2193 attempted_failed row(s) in the last 1d." No issue was pre-filed (the alert carried the details); this doc is the
findings-closure filing.

Read the manifest bounded (`read_availability_index_safe`, bucket `market-data-tick-cefi-prd-central-element-323112`,
`filters=[data_type=book_snapshot_5, capture_status=attempted_failed]`, no whole-corpus walk):

- **Full history**: 295,848 attempted_failed rows for cefi/book_snapshot_5 (much larger than the alert's 9,883 — the
  alert's denominator/window differs from a full-history count; not investigated further here, out of this escalation's
  scope). Dominant error_reasons: `UNCLASSIFIED:Tardis HTTP 403` (112,597), `VENUE_FETCH_FAILED` (93,169),
  `Tardis HTTP 403` (64,195) — the known, already-tracked Tardis concurrent-IP-lockout class
  (`cefi_high_attempted_failed_batch_cluster_2026_07_23.md`, `tardis_concurrent_ip_lockout_2026_07_12`, both
  archived/ongoing-by-design per `cefi_window_scoped_coverage_gap_okx_binance_bybit_2024_2026_2026_08_09.md`'s cause 2)
  — NOT this doc's finding, still real and still ongoing, just not the "fresh" slice.
- **Fresh slice** (attempted_at >= 2026-08-08): 2,625 rows. Of these, **2,000 are venue=ASTER,
  error_reason=UpstreamTimestampBiasError** (76% of the fresh slice). Detail query (venue=ASTER filter added) confirms:
  `service_name=market-tick-data-service`, `pipeline_mode=batch_aster`, `source=aster` — i.e.
  `OnchainPerpBatchHandler`'s batch path, not the live WS connector. `date` values are historical (2026-07-01 through
  ~2026-07-20+, ~50 rows/day = one per ASTER perpetual symbol), while `attempted_at`/`written_at` cluster
  2026-08-08T21:34:22Z .. 2026-08-09T01:24:28Z — a single (or handful of) run(s) walking historical dates attempting to
  (re)capture ASTER book_snapshot_5, each date's ~50-symbol batch failing identically. **Zero activity since
  2026-08-09T01:24:28Z** (checked at investigation time, several hours later — no recurrence).

Root cause, confirmed by code read + a live functional check on this slot's HEAD-of-branch `market-tick-data-service`
checkout (`live-defi-rollout`):

- `unified-api-contracts` `VENUE_DATA_TYPE_NO_BATCH_SOURCE["ASTER"]` includes `book_snapshot_5` (ASTER's depth endpoint
  is current-snapshot-only, no historical range param) — landed `unified-api-contracts@7754661a` (2026-07-15T18:14:29Z).
- `market_tick_data_service/cli/handlers/_onchain_perp_batch_live_only.py`'s `batch_data_types_for_venue()` consults it
  and drops `book_snapshot_5` from the batch fetch list BEFORE any HTTP call — landed
  `market-tick-data-service@2e674d1f` (2026-07-16T15:13:06Z).
- **Verified live** (this session):
  `batch_data_types_for_venue("ASTER", ["trades","book_snapshot_5","derivative_ticker"])` →
  `["trades","derivative_ticker"]` on current HEAD — `book_snapshot_5` is filtered out, logged
  `"OnchainPerpBatch: excluding ASTER/book_snapshot_5 from batch universe (live-only, no batch source) — not attempted"`.
- Therefore the 2026-08-08/09 burst is **not reproducible on current code**. The process that wrote these 2,000 rows
  must have been running a tarball build from BEFORE 2026-07-16 — nearly a month stale at the time it ran — which still
  routed ASTER `book_snapshot_5` into `_fetch_aster`'s snapshot-only path for a historical `target_day`; the snapshot
  came back timestamped "now" (2026-08-08/09), `PartitionedTickWriter`'s `validate_day_partition_alignment` (in
  `raw_tick_hive.py`) correctly rejected every day-misaligned chunk as `UpstreamTimestampBiasError`, and
  `OnchainPerpBatchHandler` correctly routed that to `record_failed` (shard-isolated, no data corruption — the honest-
  absence contract held; this is the guard working as designed against a stale-code caller).

**Could not identify the specific offending VM/process** within this one-shot escalation's scope — no currently-running
GCE instance name-matches an onchain-perp/ASTER/HYPERLIQUID backfill launcher (`gcloud compute instances list` at
investigation time shows no `*aster*`/`*onchain*`/`*hyperliquid*` instance running), and the activity already stopped
14h+ before investigation — nothing to kill, relaunch, or redeploy. This is the same STALE-TARBALL risk class as
`tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md` (a process running code older than its last
intended redeploy) but a **different specific incident** — that doc's own ASTER book_snapshot_5 finding (its P0 todo,
fixed `market-tick-data-service@593bd425`) was the LIVE WS subscribe-frame-size cliff (`pipeline_mode=live_aster`,
`empty_confirmed`, zero captured rows) — a distinct bug, distinct pipeline_mode, distinct manifest signature from this
doc's BATCH day-alignment failure.

## Why it matters

- The DP-FETCH-009 alert is technically correct (a real, fresh burst of attempted_failed rows existed) but the root
  cause is already fixed in code and the burst has already stopped — no further data-correctness action is needed for
  THIS specific burst. Filing this doc (rather than silently closing) per CLAUDE.md's "every follow-up is a todo/issue,
  never silent" rule and because a stale-tarball-executes-pre-fix-code incident is itself worth a paper trail even when
  self-resolved — it's evidence the tarball-staleness risk class (already flagged P0-open in the sibling doc) can and
  does recur in different code paths weeks after a specific incident window closes, not just during the
  originally-diagnosed 2026-07-30→08-01 outage.
- `attempted_failed_staleness.py`'s own module docstring (meta_watchers.py sibling) predicts exactly this shape: "a cell
  whose newest attempted_failed row is at least 1 day old is STATIC BACKLOG... a decaying trickle... not a fresh
  regression" — by the time a future re-run of the DP-FETCH-009 detector fires, this ASTER slice should already read as
  static backlog (no new activity), which is the expected/correct outcome here, not a masked ongoing issue.
- The REMAINING (non-ASTER) attempted_failed volume in this same cefi/book_snapshot_5 cell is real, large, and NOT
  resolved by this doc (Tardis concurrent-IP-lockout class, ~short of 200k+ rows historically) — already tracked
  elsewhere (see `related:`); this doc is scoped ONLY to the ASTER/UpstreamTimestampBiasError fresh slice the
  DP-FETCH-009 escalation's own "Fresh" label pointed at.

## Recommended decision

No code fix required — current code is already correct (verified above). No further action needed unless this recurs
(would indicate a currently-live VM/service is running the same pre-2026-07-16 tarball, worth escalating as its own P0
tarball-staleness finding if confirmed).

## Action items

- [x] ✅ [DATA] P2. Root-cause the DP-FETCH-009 fresh attempted_failed burst for cefi/book_snapshot_5 and confirm
      whether current code needs a fix. **Done — confirmed current HEAD (market-tick-data-service@live-defi-rollout,
      this slot's checkout) already excludes ASTER book_snapshot_5 from the batch fetch universe; the burst is a
      non-reproducible historical artifact of a stale-tarball run that already stopped.** No code shipped (none needed).
      — unified-trading-pm (doc-only, 2026-08-09).
- [ ] [DATA] P3. If this specific signature (venue=ASTER, data_type=book_snapshot_5, pipeline_mode=batch_aster,
      error_reason=UpstreamTimestampBiasError) recurs with a NEW `attempted_at` after 2026-08-09, escalate as a P0
      tarball-staleness finding (a currently-live process is running code >=3 weeks stale) rather than re-filing this
      doc — cite this doc + `tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md`. **Done when**:
      either confirmed non-recurring at a future audit pass, or a fresh recurrence is escalated per this note.

## Codex SSOTs

- `/codex/05-infrastructure/data-pipeline-alerts.md` — DP-FETCH-009 registry entry (`check_high_attempted_failed`, page
  escalation).
- `/codex/05-infrastructure/vm-tarball-deployment.md` — tarball freshness / staleness risk model this finding's root
  cause instantiates.
- `/codex/02-data/honest-absence-downstream-handling.md` §6A Class 1 — the `UpstreamTimestampBiasError` guard is the
  CORRECT behavior here (rejecting a day-misaligned chunk rather than writing a mislabeled parquet), not a bug to relax.

## Progress Log

- **2026-08-09** — Escalation `agt-e488d1` (data_pipeline_failure, slot 6) investigated, root-caused via bounded
  manifest reads (`read_availability_index_safe`, filtered, no whole-corpus walk) + a live functional check of
  `batch_data_types_for_venue()` on this slot's HEAD checkout. Confirmed current code correct, burst self-resolved
  (~14h+ no recurrence at investigation time), no code change shipped. Filed this doc per the findings-triage "outside
  every plan" rule since no pre-existing issue doc named this exact ASTER-batch/UpstreamTimestampBiasError signature
  (the sibling tarball doc's ASTER finding is a different bug/pipeline_mode). Escalation closes without a code ship.
- **2026-08-09** — Same escalation id `agt-e488d1` redispatched a second time (data_pipeline_failure, slot 4) — a
  duplicate dispatch of the already-closed finding above, not a new occurrence (context payload identical: cefi/
  book_snapshot_5, 9,883 attempted_failed of 935,767 attempted, "2193 attempted_failed row(s) in the last 1d").
  Independently re-ran the same bounded manifest query (`read_availability_index_safe`,
  `bucket=market-data-tick-cefi- prd-central-element-323112`,
  `filters=[data_type=book_snapshot_5, venue=ASTER, capture_status=attempted_failed]`): 2,003 rows, latest
  `attempted_at=2026-08-09T01:24:28.273974+00:00` — identical to the first investigation's finding, zero rows with a
  genuinely newer `attempted_at` (the naive `>` string-prefix check against the earlier doc's truncated-to-seconds
  cutoff initially over-matched 50 same-second microsecond-precision rows from that SAME final batch; re-checked against
  the full microsecond timestamp and confirmed no new write). Confirms the P3 follow-up condition above ("no
  recurrence") as of this second check, several hours after the first. No code change needed; closing this dispatch of
  the escalation without a ship, same conclusion as the first.
