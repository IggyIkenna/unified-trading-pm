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

- [ ] [INFRA] P1. Determine why no Cloud Build has fired for `market-tick-data-service` since
      `2026-08-21T10:18:11Z` despite the `49a8dd80` digest-bump commit landing on `live-defi-rollout` at
      `16:07:59Z` and passing `quality-gates-v2`. Check the Cloud Build trigger config
      (`gcloud builds triggers list --region=asia-northeast1`, filtered to this repo) for what event it fires
      on (push to LDR vs. promotion to `main` vs. something else) and whether it's genuinely stalled or simply
      hasn't been reached yet by the promotion pipeline. If stalled, trigger it via the sanctioned path (not
      an ad-hoc `gcloud builds submit`) and cite `Evidence: cloudbuild=<id>` resolving SUCCESS per
      `plans/PLAN_FORMAT.md` § 8b. Repo: deployment-service (owns the build triggers) /
      market-tick-data-service.
- [ ] [DATA] P1. Once the new image is confirmed deployed (`gcloud run jobs executions list` shows a fresh
      execution with real merge activity — `shards>0`/`rows_in>0`, not `error=locked`), verify the defi
      canonical `market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` blob's
      `generation`/`last_modified` has advanced past `2026-08-21T06:38:39Z`. If the guard fix causes the cron
      to loud-fail instead of self-healing (i.e. defi's full corpus also exceeds
      `CONSOLIDATOR_UNPROVABLE_MERGE_MAX_SHARDS`), the SAME manual marker-restore recovery
      `manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md`'s Progress Log documents step-by-step
      (pause cron -> confirm holder dead -> clear orphaned lock -> metadata-only restamp
      `consolidator_content_write_at` to the last genuine merge's listing time, NOT `now` -> resume -> execute)
      applies here too — do not attempt without first determining the correct restamp timestamp from Cloud
      Logging, per that doc's own explicit data-loss warning. Repo: unified-trading-library /
      market-tick-data-service (execution only, no new code expected).
- [ ] [DATA] P2. Cross-link this doc's confirmed mechanism into
      `mdps_defi_captured_days_stale_consolidated_index_despite_healthy_consolidator_2026_08_21.md`'s open
      "hypothesis 2" — done in the same edit as this filing (see that doc's Progress Log).

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
