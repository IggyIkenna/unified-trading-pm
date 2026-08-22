---
doc_type: issue
title: >-
  DP-WATCHER-002: `uts-prod-manifest-consolidator-market-data-defi` is wedged on the SAME
  full-merge-timeout/orphaned-lock loop the cefi consolidator hit 2026-08-19 — fix already shipped
  in UTL, deploy-chain gap (MTDS image rebuild) still confirmed open
summary: >-
  CRITICAL `DP_CRON_DID_NOT_FIRE` (DP-WATCHER-002, `check_cron_fired`) fired for `manifest-consolidator-defi`
  at 2026-08-21T16:04:51Z (`last output 566m ago`). Live diagnosis (`gcloud run jobs executions list` +
  `gcloud logging read` against `uts-prod-manifest-consolidator-market-data-defi`'s own execution logs) found
  the job IS running on schedule and reporting `Completed`/`success=True` every ~1min — but every single cycle
  logs `"skipping cycle for bucket=... — fresh lock present (sibling cron still running)"` followed by its own
  `CRITICAL "SILENT STALL ... streak=N cycles ... needs consolidate(bucket, force=True)"`, with `N` climbing
  monotonically (206 at 15:53Z -> 239 at 16:25Z, still climbing as of filing). This is bit-for-bit the SAME
  symptom `/plans/active/issues/manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md` root-caused
  and fixed for the cefi bucket: a missing `consolidator_content_write_at` marker forces a fail-closed FULL
  corpus merge, which exceeds the Cloud Run 7200s task timeout, gets SIGKILLed (bypassing
  `finally: _release_lock`), orphans the lock, and every cycle thereafter re-arms the identical doomed merge
  once the lock's TTL (9000s for the defi/cefi heavy buckets) expires — a perpetual wedge, not a single
  zombie. The fix (`unified-trading-library@af783d92e4` — `_UNPROVABLE_MERGE_MAX_SHARDS` cap, refuses the
  doomed merge instead of attempting it; `unified-trading-library@53abdf72f3` — excludes locked no-op cycles
  from the liveness watchdog's heartbeat) already shipped 2026-08-19, but that doc's own still-open P2 todo
  ("Rebuild the market-tick-data-service:latest image so BOTH shipped fixes reach their running Cloud Run
  jobs") was confirmed STILL OPEN by a 2026-08-20 reconciler sweep. A Dockerfile `BASE_IMAGE_DIGEST` bump
  landed on `live-defi-rollout` TODAY (`market-tick-data-service@49a8dd80`, 2026-08-21T16:07:59Z — likely the
  standing automated digest-drift-sweep, not specifically triggered by this incident) and its
  `quality-gates-v2` GH check passed (16:09Z->16:28Z), but `gcloud builds list` shows NO Cloud Build has fired
  for this repo since `2026-08-21T10:18:11Z` — over 2 hours before this filing, and ~20+ minutes after the
  digest-bump commit landed — so the fix has NOT yet reached the running `market-tick-data-service:latest`
  image (Cloud Run resolves `:latest` -> digest at execution-creation time, so no manual job repin would be
  needed once a build actually completes). This is the DIRECT explanation for the already-open
  `mdps_defi_captured_days_stale_consolidated_index_despite_healthy_consolidator_2026_08_21.md`'s unresolved
  "hypothesis 2" (a genuine consolidator incremental-merge correctness gap) — confirmed here with a precise
  mechanism, not a guess.
status: open
nature: issue
asset_group: [defi]
stage: [meta, data]
repos: [unified-trading-library, market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags:
  [
    data-pipeline-alerts,
    dp-watcher-002,
    manifest-consolidator,
    stuck-lock,
    defi,
    deploy-chain-gap,
    cron-did-not-fire,
  ]
related:
  [
    /plans/active/issues/manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md,
    /plans/active/issues/mdps_defi_captured_days_stale_consolidated_index_despite_healthy_consolidator_2026_08_21.md,
    /plans/active/issues/dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: "2026-08-21"
author: data_pipeline_failure escalation worker (slot 22, agt-6ea9c3)
source: [DP-WATCHER-002, escalation agt-6ea9c3]
parent_epic: mtds_mdps_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
last_updated: "2026-08-21"
context_scope:
  [
    /plans/active/issues/manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    unified-trading-library/unified_trading_library/manifest_consolidator.py,
    market-tick-data-service/Dockerfile,
    market-tick-data-service/cloudbuild.yaml,
  ]
---

# DP-WATCHER-002: defi market-data consolidator wedged on the same lock-orphan loop as cefi (2026-08-19)

## What I found

Escalation `agt-6ea9c3` (DP-WATCHER-002, `wall_type=data_pipeline_failure`) fired with no pre-filed issue slug
— alert carried the details directly: `cron 'manifest-consolidator-defi' did not fire on schedule (last
output 566m ago)`.

**Live evidence gathered (2026-08-21T16:1x-16:3xZ):**

1. `gcloud scheduler jobs list` — `uts-prod-manifest-consolidator-market-data-defi-cron` `ENABLED`, `*/1 * * * *`.
2. `gcloud run jobs executions list --job=uts-prod-manifest-consolidator-market-data-defi` — every recent
   execution `Completed=True`, firing every ~1 min. **The job is not down** — this is the same
   "healthy-execution-signal, frozen-output" shape the cefi doc already named.
3. `gcloud logging read` against the job's own stdout (not Slack, not a downstream watcher) — every cycle from
   at least 15:53Z through 16:25Z logs:
   ```
   INFO  ManifestConsolidator: skipping cycle for bucket=market-data-tick-defi-prd-central-element-323112 — fresh lock present (sibling cron still running)
   CRITICAL ManifestConsolidator: SILENT STALL bucket=market-data-tick-defi-prd-central-element-323112 streak=N cycles shards_scanned=3 baseline_shards=2 — shards keep landing but no cycle has merged them; likely a bulk shard drop whose mtimes predate the incremental cutoff, needs consolidate(bucket, force=True)
   manifest-consolidator bucket=market-data-tick-defi-prd-central-element-323112 success=True shards=0 rows_in=0 rows_out=0 dedup_dropped=0 legacy_seeded=False pruned_shards=0 latency_ms=... error=locked
   ```
   `streak` climbed 206 (15:53Z) -> 215 (16:01Z) -> 234-239 (16:20-16:25Z) — a live, ongoing, worsening
   condition, not a one-off blip.
4. The alert's own `age_min=566` (16:04:51Z) matches, almost to the minute, the canonical blob staleness a
   SEPARATE same-day investigation already measured independently:
   `mdps_defi_captured_days_stale_consolidated_index_despite_healthy_consolidator_2026_08_21.md` recorded
   `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`
   `last_modified='2026-08-21T06:38:39Z'` at its own 10:47Z check (~4h9m stale then) — `16:04:51Z - 06:38:39Z
   = 566.2 min`, i.e. the canonical has not genuinely advanced since 06:38:39Z, confirmed independently by two
   different detection paths (a manifest-freshness read AND this DP-WATCHER-002 cron-alive probe).
5. **Root cause match, not a guess**: this exact three-line log signature (`fresh lock present` /
   `SILENT STALL ... needs consolidate(bucket, force=True)` / `success=True ... error=locked`) is the same
   signature `manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md` root-caused end-to-end for the
   cefi bucket: a missing `consolidator_content_write_at` marker forces a fail-closed FULL corpus merge that
   exceeds the Cloud Run 7200s task timeout, SIGKILL bypasses `finally: _release_lock`, the lock orphans, and
   every cycle thereafter (once the TTL — `CONSOLIDATOR_LOCK_TTL_SECONDS`, 9000s override for the
   defi/cefi heavy-merge buckets — expires) reclaims and re-runs the identical doomed merge. That doc's own
   fix, `unified-trading-library@af783d92e4` (`_UNPROVABLE_MERGE_MAX_SHARDS` cap — refuses an oversized
   unprovable-cutoff merge instead of attempting it, loud-fails with `MANIFEST_CONSOLIDATION_FAILED` instead
   of wedging) + `unified-trading-library@53abdf72f3` (excludes locked no-op cycles from the liveness
   watchdog's heartbeat, closing the reason zero `CONSOLIDATOR_DOWN` alerts fired during the 41.6h cefi
   outage), already shipped 2026-08-19 — but its own todo `[INFRA] P2` ("Rebuild the
   `market-tick-data-service:latest` image … so BOTH shipped fixes reach their running Cloud Run jobs") is
   **still unchecked**, and a 2026-08-20T08:04Z reconciler sweep independently reconfirmed it: "The MTDS image
   rebuild in P2 remains the unresolved deploy-chain step." Since ALL manifest-consolidator Cloud Run jobs
   (every asset_group, both `instruments` and `market-data` kinds) share the ONE
   `market-tick-data-service:latest` image (`manifest-consolidator-ssot.md`), this deploy gap explains why the
   SAME wedge bug is now surfacing on `defi` too — not a second, independent occurrence of the underlying
   merge-timeout bug, but the SAME still-undeployed-fix gap manifesting on a second bucket.
6. **Deploy-chain status, checked this session**: `market-tick-data-service`'s `Dockerfile` `ARG
   BASE_IMAGE_DIGEST` was bumped TODAY (`market-tick-data-service@49a8dd80`, `2026-08-21T16:07:59Z`) — a
   repeating `chore(deps): refresh base-image digest pin` pattern (5 prior instances in `git log`), most
   likely the standing automated digest-drift-sweep rather than a fix specifically targeting this incident.
   Its `quality-gates-v2` GH Actions check passed (`32501434496`, `2026-08-21T16:09:09Z` -> `16:28:08Z`,
   18m59s). **But `gcloud builds list` (fleet-wide, no filter, most recent 6 shown) has NO entry newer than
   `2026-08-21T10:18:11Z`** — i.e. no Cloud Build has actually run for this repo in the >2h before this
   filing, including the >20 minutes since the digest-bump commit landed and passed CI. The running Cloud Run
   job resolves `:latest` -> digest at execution-creation time (per the SSOT, no manual job repin needed once
   a build lands) — so the fix genuinely has NOT yet reached the deployed image as of this filing. **Did NOT
   determine why the build hasn't fired** (a stalled/misconfigured push-trigger vs. simply not-yet-queued vs.
   this repo's build trigger firing on a DIFFERENT event than a plain LDR push, e.g. only on promotion to
   `main`) — flagged as the precise next step below rather than guessed at.

## Why I did not attempt a code fix or a manual Cloud Build trigger this session

Per role contract (`does_not: guess at an ambiguous fix`): the actual code fix already exists, is already
proven safe (successfully broke the identical wedge on cefi, canonical advanced, verified end-to-end), and is
already tracked as an open P2 todo on the cefi doc — duplicating it here would violate findings-triage ("fits
another plan → annotate it, don't fix"). Manually invoking `gcloud builds submit` without first confirming
the correct trigger/config for this repo's actual CI/CD wiring risked either duplicating an in-flight
automated process or using an incorrect ad-hoc command outside the sanctioned pipeline — the SSOT's own
"Image deploy-hygiene" note says a UTL fix reaches the base image automatically via the
`unified-trading-library-live-defi-rollout` trigger on LDR pushes, with the MTDS `BASE_IMAGE_DIGEST` bump +
rebuild as "the only manual link in the chain" — but does not specify what re-triggers the MTDS-side build
itself, which is exactly the gap observed here (bump landed, no build followed).

## Recommended decision

- [x] [INFRA] P1. ✅ **CORRECTED — this was a measurement artifact, not a real deploy-chain gap.** `gcloud builds
      list` (no `--region` flag) silently omits regional builds — it does NOT error, it just returns fewer rows,
      so the earlier "no Cloud Build has fired" claim looked confirmed when it was actually querying the wrong
      scope. Re-checked WITH `--region=asia-northeast1`: `market-tick-data-service-live-defi-rollout` trigger
      (id `46d60bf7-4880-4b38-8ed4-87e1249ee4ed`, push-on-`^live-defi-rollout$`) fired 6 SUCCESS builds between
      `17:22:59Z` and `18:17:34Z`. The `18:17:34Z→18:27:39Z` build (`079dfe0d-fc07-4f1b-8854-ed5602235a83`) built
      commit `ed967279` (`git merge-base --is-ancestor 49a8dd80 ed967279` confirms it descends from the
      digest-bump commit) and pushed `:latest` — `Evidence: cloudbuild=079dfe0d-fc07-4f1b-8854-ed5602235a83`
      (SUCCESS). The Cloud Run Job's image ref is the mutable
      `.../unified-trading-system/market-tick-data-service:latest` tag (confirmed via `gcloud run jobs
      describe`), so it resolves the new digest automatically on the next execution — no manual repin needed,
      exactly per this doc's own original assumption. **The deploy gap is closed.** Correcting this doc's own
      misdiagnosis per CLAUDE.md "a doc/comment/pointer that MISLED you is a finding — fix it in the same turn":
      a future worker re-running the same fleet-wide `gcloud builds list` sanity check without `--region` will
      hit the identical false-negative — flagged as a new follow-up todo below rather than silently left to
      recur.
- [ ] [DATA] P1. **IN PROGRESS as of 19:16Z, not yet done-when-satisfied.** New image confirmed deployed and
      picked up: execution `uts-prod-manifest-consolidator-market-data-defi-p6hrc` (started `18:57:05Z`, after
      the `18:27:39Z` build) cleared the prior holder's stale orphaned lock (age 9048.7s > 9000s TTL),
      reacquired, hit the same missing-`consolidator_content_write_at`-marker "cutoff UNPROVABLE" warning, but
      — unlike the cefi incident — its `shards=2`/`shards=3` count is far under `_UNPROVABLE_MERGE_MAX_SHARDS`
      (default 50000), so the guard did NOT fast-fail it; instead it proceeded into a genuine
      `phase=duckdb_merge_start mode=incremental memory_limit=24GB threads=4 chunk_days=30 chunks=106
      date_range=2018-01-01..2026-08-21` — a chunked full-history incremental merge (`canon_rows=161,763,519`
      downloaded first), still running as of this edit. **This asset_group's "unprovable merge" shape is
      chunked, not a single doomed pass** — genuinely different code path than cefi's, so whether it completes
      inside the 7200s Cloud Run task timeout is not yet known; a background monitor is tracking it to a
      terminal state this session. Once terminal: if SUCCESS, verify canonical `generation`/`last_modified`
      advanced past `2026-08-21T06:38:39Z` (done-when met, close this todo). If SIGKILLed by the 7200s timeout,
      the SAME manual marker-restore recovery
      `manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md`'s Progress Log documents (pause cron ->
      confirm holder dead -> clear orphaned lock -> metadata-only restamp `consolidator_content_write_at` to the
      last genuine merge's listing time, NOT `now` -> resume -> execute) applies here too — do not attempt
      without first determining the correct restamp timestamp from Cloud Logging, per that doc's own explicit
      data-loss warning. Repo: unified-trading-library / market-tick-data-service (execution only, no new code
      expected).
      **CORRECTION (2026-08-22T05:2xZ, slot 31, agt-2ad90c) — "IN PROGRESS" / "still running as of this edit" was
      a misread and this todo's own hedged framing understated it: `p6hrc` did NOT succeed. Live-traced its full
      log: `phase=duckdb_merge_start` at `18:59:37Z`, then `2026-08-21T20:57:18.002728Z ERROR "Terminating task
      because it has reached the maximum timeout of 7200 seconds"` — SIGKILLed mid-merge, never reached
      `_write_consolidated`. The Cloud Run *execution* still reported `Completed=True`/"successfully in 2h1m0s"
      because that status reflects the JOB-level exit code of the RETRY task Cloud Run auto-spawned after the
      kill (a fresh process at `20:57:51Z` that found the orphaned lock still fresh, logged `SILENT STALL`, and
      exited 0 having done zero work) — not that the merge completed. See the corrected timeline below; this is
      now confirmed an ONGOING wedge, not a one-off pending SIGKILL.**
- [ ] [DATA] P2. Cross-link this doc's confirmed mechanism into
      `mdps_defi_captured_days_stale_consolidated_index_despite_healthy_consolidator_2026_08_21.md`'s open
      "hypothesis 2" — done in the same edit as this filing (see that doc's Progress Log).
- [ ] [INFRA] P3. Add a `--region=asia-northeast1` reminder (or a wrapper script) for the "check whether a Cloud
      Build fired" pattern — `gcloud builds list` with no region flag silently under-reports (returns fewer
      rows, not an error), which produced a false "deploy gap" diagnosis in this doc's own first pass (see todo
      1's correction above). Worth a one-line callout in `/codex/05-infrastructure/dual-cloud-image-builds.md`
      or `/codex/12-agent-workflow/measurement-claims-discipline.md` so a future worker doesn't repeat the same
      false-negative. Repo: unified-trading-pm (docs-only).

## Codex SSOTs

- `/codex/05-infrastructure/manifest-consolidator-ssot.md` § "Liveness + health contract", § "Recovery when a
  deployed consolidator is on a bad image".
- `/codex/05-infrastructure/data-pipeline-alerts.md` § DP-WATCHER-002.

## Progress Log

- **2026-08-21 (data_pipeline_failure escalation worker, slot 22, agt-6ea9c3)**: filed after live diagnosis
  (see "What I found" above). Confirmed this is a RECURRENCE of the already-root-caused, already-fixed-in-
  source `manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md` incident, blocked purely on that
  doc's own still-open P2 image-rebuild todo. Found the digest bump landed today but no Cloud Build has yet
  followed it — the precise, actionable next step, added as todo 1 above. Did not attempt a code fix (none
  needed — the fix already exists and is proven) or a manual Cloud Build trigger (outside confident, sanctioned
  scope for a one-shot escalation — `does_not: guess at an ambiguous fix`). No code shipped this session; this
  doc-only filing ships via `safe-doc-push.sh`. `AUTHORING_SLOT` (`dp-fleet-monitor`) is not a numeric slot id,
  so skipped the authoring-slot ping per the boot-prompt's skip rule — the dispatch-time Slack alert already
  covered the FYI.
- **2026-08-21T19:1xZ (data_pipeline_failure escalation worker, slot 31, agt-401353)**: dispatched off a
  RE-FIRE of the same DP-WATCHER-002 alert (`age_min≈732` this time, vs. 566 at the prior filing — same cron,
  same bucket, no new slug given, alert carried the details directly). Found this open doc immediately via the
  pre-task issue-conflict grep and continued it rather than re-diagnosing or filing a duplicate.
  **CORRECTED todo 1's "no Cloud Build fired" claim — it was a measurement artifact**: re-ran the same
  `gcloud builds list` check WITH `--region=asia-northeast1` (the prior pass omitted it) and found 6 SUCCESS
  builds for this repo between `17:22:59Z`-`18:17:34Z`, including one (`079dfe0d`) building commit `ed967279`
  (confirmed via `git merge-base --is-ancestor 49a8dd80 ed967279` to descend from the digest-bump commit) and
  pushing `:latest`. The Cloud Run Job's image ref is the mutable `:latest` tag, so it auto-picked up the fix —
  **the deploy gap this doc opened with is closed, no manual action was needed.** Live-traced the CURRENT lock
  holder: execution `p6hrc` (started `18:57:05Z`, i.e. with the new image already live) cleared a stale
  orphaned lock and is running a genuine `mode=incremental` chunked merge (106 chunks, full `2018-01-01..
  2026-08-21` date range) — **not** hitting the `_UNPROVABLE_MERGE_MAX_SHARDS` guard (its `shards=2`/`3` count
  is far under the 50000 threshold), so this asset_group's "unprovable merge" shape is a chunked pass, not a
  single doomed one like cefi's. Armed a bounded background monitor (Monitor task `bbtyf60sj`, ~18min cap,
  heartbeating this session's liveness every ~3min) to catch p6hrc's terminal state and, if SUCCESS, confirm the
  canonical index advanced past `06:38:39Z`. Todo 1 flipped done (corrected); todo 2 updated in-place with this
  finding rather than duplicated; added todo 3 (P3, docs-only) so the `gcloud builds list`-needs-`--region`
  false-negative doesn't recur for the next worker who runs the same sanity check.
- **2026-08-21T19:35Z (data_pipeline_failure escalation worker, slot 31, agt-401353) — session-end handoff**:
  the bounded background monitor (18min cap, 36×30s polls) expired with `p6hrc` STILL running (`Unknown /
  Waiting for execution to complete`) — no terminal state reached this session. **No destructive action was
  taken**; nothing here needs a restamp yet since the merge may still complete on its own (this asset_group's
  chunked-incremental unprovable-merge path is unproven either way, so a premature marker-restore would be a
  guess, not a confirmed fix — out of scope per this role's `does_not: guess at an ambiguous fix`). Per
  `p6hrc`'s `startTime=2026-08-21T18:57:05Z` and the Cloud Run Job's 7200s task timeout, its terminal state
  (success or SIGKILL) will land by **~2026-08-21T20:57:05Z** at the latest. **Next responder** (whether a fresh
  DP-WATCHER-002 fire, a scheduled reconciler sweep, or an operator check): first check
  `gcloud run jobs executions describe uts-prod-manifest-consolidator-market-data-defi-p6hrc --region=
  asia-northeast1 --project=central-element-323112` (note: always pass `--region` — see todo 3) for a terminal
  `status.conditions[0].status`. If `True`/succeeded, verify the canonical
  `market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` blob's
  `generation`/`last_modified` advanced past `2026-08-21T06:38:39Z` and close todo 1. If it was SIGKILLed
  (7200s timeout), todo 1's documented cefi-mirrored marker-restore recovery applies — determine the correct
  restamp timestamp from Cloud Logging `phase=shards_listed` lines before touching anything, per that
  recovery's own data-loss warning. This session did not babysit the remaining ~1h22m to the timeout boundary
  (one-shot escalation contract; the cefi doc's own precedent is "do not babysit hourly"). No code shipped this
  session — doc-only, via `safe-doc-push.sh` (commit `f2c25abb51`, verified on origin).
- **2026-08-22T05:1x-05:2xZ (data_pipeline_failure escalation worker, slot 31, agt-2ad90c)**: dispatched off a
  THIRD fire of the same DP-WATCHER-002 alert (`age_min≈272`). Found this open doc via the pre-task grep, read
  the full handoff, and **disproved the prior session's "p6hrc succeeded" conclusion** — see the correction
  inserted into todo 2 above. Full live re-diagnosis this session:
  - `gcloud run jobs executions list` (current, `region=asia-northeast1`): the job fires every ~1 min as
    scheduled (cron itself is healthy — this is NOT a literal "cron did not fire", it's DP-WATCHER-002's
    canonical-staleness detection tripping on a wedged merge, same shape the doc title already names) but every
    cycle logs `skipping cycle ... fresh lock present` + `CRITICAL SILENT STALL ... streak=N` (N=763-764 at
    05:10-05:11Z) + `success=True shards=0 ... error=locked`.
  - The CURRENT lock holder, execution `xtn66` (started `05:09:39Z`): `clearing stale lock ... age=9060.0s >
    TTL=9000.0s`, re-acquired, hit the same `WARNING ... has NO consolidator_content_write_at marker ... cutoff
    UNPROVABLE`, and at `05:11:36Z` started the same `phase=duckdb_merge_start mode=incremental chunks=106
    date_range=2018-01-01..2026-08-22` full-history merge that has doomed every prior cycle.
  - **24h Cloud Logging sweep (`textPayload:"wrote consolidated index" OR "Terminating task" OR "clearing stale
    lock" OR "phase=lock_acquired"`, 2026-08-20T06:00Z→2026-08-21T23:30Z) gives the FULL, unambiguous timeline**:
    genuine successful `wrote consolidated index` cycles ran roughly hourly from `2026-08-20T06:17Z` through
    **`2026-08-21T06:21:55Z` (canon_rows=161,809,819 — the LAST genuine merge)**. The very next cycle
    (`phase=lock_acquired` `06:22:40Z`, `phase=shards_listed` `06:22:40.583662Z`, `shards=2`) is the FIRST to
    never complete — it ran into the 7200s timeout and was killed at `08:22:15Z`. Every cycle since has repeated
    the identical acquire→run 7200s→SIGKILL→orphan→9000s-TTL-wait→clear-stale-lock→re-acquire→repeat loop,
    confirmed via 7 more `Terminating task` timestamps through `2026-08-21T23:27:26Z` plus this session's own
    live observation of the `xtn66` cycle — **a continuous, unbroken wedge since 2026-08-21T06:22:40Z, now
    ~23h and counting**, burning a full 7200s Cloud Run task on every ~2.6h cycle for zero forward progress.
  - **Root-cause note on the marker loss itself** (new information, not established by the cefi doc): the gap
    between the last genuine write (`06:21:55Z`) and the next cycle's lock acquisition (`06:22:40Z`) is only
    ~45s — too tight to comfortably attribute to an external "out-of-band rewrite" tool (the cefi incident's
    working theory) coincidentally landing in that exact window. Did NOT dig further into the GCS client upload
    path (`_write_consolidated`, `unified_trading_library/manifest_consolidator.py:3465-3598`) to confirm
    whether the CAS `upload_from_string(..., if_generation_match=...)` call can silently drop a
    just-set `blob.metadata` under some condition — flagging as an open code-level question for whoever picks up
    the fix, since if that's the real mechanism it will keep re-triggering after every future restamp too.
  - **Recommended recovery — same shape as the proven cefi fix, exact parameters determined this session**:
    pause the `manifest-consolidator-defi` Cloud Scheduler job → confirm the current lock holder is genuinely
    dead (not `xtn66` mid-merge — cancel/wait it out first) → clear the orphaned `_index/consolidator.lock` →
    metadata-only restamp `_index/availability_index.parquet`: `consolidator_content_write_at =
    2026-08-21T05:11:44Z` (the last genuine cycle's `phase=shards_listed` time — NOT `06:22:40Z`, which is the
    FIRST BAD cycle's listing time and would silently drop everything that cycle should have merged),
    `consolidator_run_at = now()`, content bytes untouched → resume the scheduler → verify the next cycle merges
    incrementally (small shard count, fits well inside 7200s) and the canonical `generation`/`last_modified`
    advances past `2026-08-21T06:21:55Z`.
  - **Did not execute this recovery myself this session** — per role contract (`does_not: guess at an ambiguous
    fix`) and the cefi precedent (`manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md` required an
    explicit operator "A" answer via `/blocked` before its own metadata-only restamp, given the doc's own
    data-loss warning that a wrong timestamp prunes unmerged shards). Posted a bounded `/blocked` question with
    this exact recommendation to the main agent; see its answer (or the 2-min timeout) noted below or in a
    follow-up entry. **No code shipped this session** — doc-only, via `safe-doc-push.sh`.
