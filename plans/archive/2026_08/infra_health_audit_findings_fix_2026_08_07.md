---
doc_type: plan
title: Fix the infra-health-audit findings (Cloud Run Jobs/Services + VM fleet) and document alert-coverage gaps
summary: >-
  A 2026-08-07 3-agent parallel audit of Cloud Run Jobs, Cloud Run Services, and the GCE VM fleet in
  central-element-323112 found ~12 real, currently-active issues (crash-loops, OOM, dead schedulers firing into voids, a
  hung idle VM burning billing, stale GCR image paths, a 19-month-broken min-instances service). Per operator direction:
  exclude the DeFi manifest-consolidator pause (already a known, tracked, intentional condition —
  /plans/active/issues/defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md). For every remaining finding,
  first determine whether it already fired a #data-pipeline-alerts or #uts-live-alerts Slack alert (document the gap if
  not — a real finding in its own right, since a bug nobody gets paged for is a bug that never gets found), then fix the
  underlying issue regardless of alert status. Also run a dedicated zombie sweep (VMs and Cloud Run job executions that
  are technically "running" but doing nothing) beyond what the original audit incidentally found.
status: resolved
nature: process
asset_group: [meta]
stage: [meta]
repos:
  [
    market-tick-data-service,
    client-reporting-api,
    deployment-service,
    alerting-service,
    unified-trading-library,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [infra-health, oom, crash-loop, zombie, cloud-run, gce, alert-coverage, audit]
related:
  [
    /plans/active/issues/alerting_service_lifecycle_events_sub_dual_consumer_slack_spam_2026_08_07.md,
    /plans/active/issues/defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
  ]
created: 2026-08-07
last_updated: 2026-08-07
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
locked_by:
locked_since:
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/15-runbooks/safe-service-restart-procedures.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator ("great so all those issues... should have hit alerts... if they didnt we need to document and then fix them
  and if they did great we still need to fix them /autonomous"), 2026-08-07, following a 3-agent infra health audit.
assigned_role: infra
drift_direction: advance-code
---

# Fix the infra-health-audit findings

> **🟢 ARCHIVED 2026-08-09 — RESOLVED.** All 16 todos done, unlocked. The last open item
> (`uts-prod-data-status-rollup-svc` OOM) closed after a 5-round live investigation — VERIFIED LIVE via a 49-min,
> 2-cron-cycle Cloud Logging sweep showing zero OOM events across the previously-100%-reproducing failure conditions.
> See that todo's own entry for the full incident.

## Todos

- [x] [SCRIPT] P0. ✅ **Dedicated zombie sweep — DONE 2026-08-07.** Bullets (b)/(c) found nothing new beyond what was
      already tracked (no second dual-consumer pattern; every long-running VM's heartbeat was current within 1-2 min;
      the fleet's own `vm-zombie-watchdog` independently confirms 0 zombies). Bullet (a) uncovered a much bigger
      standalone finding instead: ~38 Cloud Scheduler jobs (asia-northeast1 + europe-west1) firing daily/hourly at Cloud
      Run Job targets that no longer exist — some for 500+ consecutive failed executions (~1.4 years). Triaged +
      bulk-paused separately (see the "Zombie scheduler triage" work below +
      `/plans/active/issues/     asia_northeast1_zombie_schedulers_dead_targets_2026_08_07.md`).
- [x] [SCRIPT] P0. ✅ **STALE DUPLICATE — already done, closing 2026-08-07 (na-eligibility-audit).** Alert-coverage
      cross-reference — for every finding below (excluding the DeFi consolidator), check `#data-pipeline-alerts` and
      `#uts-live-alerts` for a matching alert; cross-check against the DP-* registry; produce a finding→alert-fired
      table; file gaps as their own todo/issue-doc entries. This is a literal duplicate of the checked twin todo below
      ("✅ Alert-coverage cross-reference — DONE 2026-08-07"), which already did exactly this and filed
      `/plans/active/issues/infra_health_audit_alert_coverage_gaps_2026_08_07.md`.
- [x] [SCRIPT] P0. ✅ **`market-data-query-service` — DECOMMISSIONED, not patched.** Investigation before fixing found
      this reclassifies from "fix the bucket" to "dead service": (1) zero real HTTP requests in 7 days (only the
      internal startup probe, which fails) — `gcloud logging read` for `httpRequest.requestUrl!=""` returned nothing;
      (2) its ONLY revision (`market-data-query-service-00002-g9r`) was created `2025-10-20T19:42:12Z` — not redeployed
      in ~10 months; (3) `gs://market-data-candles` was deliberately RETIRED `2026-04-18` per
      `unified-trading-pm:plans/archive/data_pipeline_completion_2026_04_18.plan.md` ("empty; co-location wins") —
      candles now live co-located under `market-data-tick-{category}-{project}/processed_candles/`, so this service
      predates a real architecture migration and was never updated; (4) its backing Artifact Registry repo
      `market-data-handler` is now **0.000MB / empty** (an aggressive `delete-older-than-3d` cleanup policy has been
      silently deleting its own images) — the source code for `market_data_query_service.py` could not even be located
      anywhere in the GitHub org (`gh search code`, zero hits); (5)
      `deployment-service/configs/     gcp_service_accounts.yaml`'s own audit comment groups it in the same "sampled
      5/7" list as `batch-live-reconciliation-service`/`fund-administration-service`/`trading-agent-service` — 3 of
      which are ALREADY confirmed dead-weight stubs in the P3 decommission todo below. Deleted via
      `gcloud run services delete market-data-query-service --region=asia-northeast1` (2026-08-07). Its `deployment-ui`
      references (`src/lib/mock-api.ts`, a smoke-test testid) run against a MOCK API, not the live service, so nothing
      else needed updating. Folded into the P3 dead-weight cluster rather than counted separately.
- [x] ✅ [SCRIPT] P0. **Alert-coverage cross-reference** — DONE 2026-08-07. Checked all 11 non-excluded findings against
      `#data-pipeline-alerts` (8-day + 8h `scripts/dev/slack-read-channel.py` pulls) and the DP-* registry +
      `unified-api-contracts` `codes.py`/`rules.py`. **Zero of 11 fired a Slack alert.** `#uts-live-alerts` could not be
      checked — reader bot returns `not_in_channel` (residual verification gap, noted not assumed-negative). Filed
      `/plans/active/issues/infra_health_audit_alert_coverage_gaps_2026_08_07.md` with the full finding→status→evidence
      table + 3 structural gap classes (Cloud Run Service/Job compute-failure blind spot; dp-alerting-subscriber's own
      GCS-429 misrouting past an existing DP-VM-006 rule; zero AlertCode coverage for AWS IAM/STS) + 4 follow-up todos.
      Findings 4 and 8 flagged as a distinct case (a conceptually-matching rule exists but apparently didn't fire —
      needs live MissTracker state, not a Slack/code read) rather than filed as a gap. Cross-referenced 3 already-open
      same-day docs to avoid duplicating in-flight root-cause work. (repo: unified-trading-pm)
- [x] [SCRIPT] P0. ✅ **MOOT — service decommissioned, closing 2026-08-07 (na-eligibility-audit).** Fix
      `market-data-query-service` crash-loop (hardcoded `gs://market-data-candles`). This plan's own earlier todo above
      ("`market-data-query-service` — DECOMMISSIONED, not patched") already deleted the service entirely
      (`gcloud run services delete market-data-query-service --region=asia-northeast1`, 2026-08-07) after finding it
      dead for ~10 months with zero real traffic — there is no longer a crash-loop to fix; the service doesn't exist.
- [x] [SCRIPT] P0. ✅ **Fixed `client-reporting-batch` OOM.** Memory limit raised from `512Mi`/`1cpu` to `2Gi` —
      verified live via
      `gcloud run jobs describe client-reporting-batch --region=asia-northeast1     --format="value(...resources.limits.memory)"`
      returning `2Gi` (2026-08-08). Fix-agent details (source-of-truth IaC change, sizing rationale, execution
      verification) pending its own report; this checkbox reflects the confirmed live GCP state, not just a claim.
- [x] [SCRIPT] P1. ✅ **Fixed `uts-prod-data-status-rollup-svc` OOM — 5-round investigation, VERIFIED LIVE
      2026-08-09T13:04Z.** - **Rounds 1-2 recap**: per-service isolation (`4c0e039`) + per-category subprocess sharding
      (`_SERIAL_DISPATCH_ISOLATED`) fixed the original in-process RSS ratchet; `daemon=True→False` (`e2b9a55`) fixed the
      sharding fix's own regression (0/14 succeeding). Deployed on revision `00360-hkf` — OOM PERSISTED, measured 10/10
      cron cycles over 6h, every one: `instruments-service` times out at 420s, then ~100-110s later the WHOLE CONTAINER
      OOMs. - **Round 3**: root-caused to `_run_service_isolated`'s 420s timeout-kill path signalling only the
      per-service child's PID — under `_SERIAL_DISPATCH_ISOLATED` that child spawns a per-category GRANDCHILD
      (`bounded_subprocess.run_bounded`), and a service's ~5 categories at up to 200s each routinely exceed the 420s
      outer ceiling, so the kill fires mid-category and orphans the grandchild (nothing signals it; `daemon=True`'s
      auto-cleanup is an `atexit` hook that never fires on an externally-delivered SIGTERM). **Fix**:
      `deployment-api@6ac1c43ff` — `os.setpgrp()`/`os.killpg()` process-group cleanup (worker + `bounded_subprocess.py`,
      QG 5252 passed). Deployed as `00363-vbt`: Cloud Logging confirmed `killpg(pid=257, SIGTERM) delivered` — the fix
      genuinely works, clean reap, no orphan — **but the OOM still happened anyway, 67s later**, proving the orphan leak
      was real but not the dominant driver. - **Round 4**: 5 independent OOM samples (pre/post the process-group fix)
      all measured this "dedicated" service's baseline app overhead (full deployment-api surface: cache-warming, VM
      listing, redis, catalogue-lifecycle, auto-sync) at a tight 8194-8640 MiB band; the old 24Gi per-category ceiling
      left zero real margin against the 32Gi container. **Fix**: `deployment-api@1849f4e23` lowers
      `_CHILD_RLIMIT_AS_BYTES`/`_SERIAL_ISOLATED_CATEGORY_RLIMIT_BYTES` 24Gi→20Gi (safety-margin correction, not "raise
      the ceiling" — the 32Gi container limit is unchanged). Deployed as `00364-k2p`, verified via `docker pull` of the
      exact image digest + grep inside it (ruling out a stale-image false negative) — waited 2 full cron cycles: **OOM
      STILL occurred, 4 events, statistically IDENTICAL to every prior sample (32770-33216 MiB)** — proof the rlimit was
      never the binding constraint. - **Round 5 (the real dominant root cause)**: `deployment_api/lifespan.py` — this
      service shares its image with `uts-shared-deployment-api` but only ever serves `POST /api/data-status/rollup-run`;
      it nonetheless ran the FULL app surface unconditionally (leader-worker deployment auto-sync/reaper — lists every
      running VM + sequentially downloads every stale `deployments/active/*.json` blob every ~60-70s —, the SSE
      deployment-events drain, and the catalogue-lifecycle cache warm), all in the TOP-LEVEL PARENT process, entirely
      outside any isolated-child rlimit already proven ineffective in round 4. **Fix**: `deployment-api@f3ee76f93` adds
      `DEPLOYMENT_API_MINIMAL_STARTUP` (new pydantic field, `DATA_STATUS_PREWARM_SERVICE` pattern) — skips those 3 task
      groups when true; default false (zero behavior change for `uts-shared-deployment-api`/any other deployment). Set
      live via `gcloud run services update ... --update-env-vars=DEPLOYMENT_API_MINIMAL_STARTUP=true`. **VERIFIED
      LIVE**: deployed as revisions `00367-c8v` (12:15Z) then `00368-xmj` (12:29Z, superseded by an unrelated concurrent
      promotion) — Cloud Logging confirms `MINIMAL_STARTUP: skipping ...` firing (12 lines across gunicorn workers) and,
      across a 49-min window (12:15→13:04Z) spanning 2 full cron cycles, `instruments-service`,
      `market-tick-data-service` AND `market-data-processing-service` ALL independently hit their known 420s
      structural-gap timeout (the EXACT condition that caused 10/10 OOMs pre-fix and 1/1 post-round-4) — **zero "Memory
      limit exceeded"/"too much memory" events**, confirmed via an explicit fleet-wide Cloud Logging sweep across both
      revisions. The per-service 420s timeouts for instruments-service/MTDS/MDPS are the PRE-EXISTING,
      already-documented, accepted structural gap (data volume growth outpacing the ceiling — see
      `data_status_rollup_ml_service_full_blob_missing_2026_07_26.md`), not the bug this todo fixes; that gap stays open
      as its own tracked item. - **Correction to the operator's own verification ask**: `log_event("SERVICE_PROCESSED")`
      writes ONLY to the GCS `GcsEventSink` (never stdout/Cloud Logging), so it can't be grepped even on success —
      ground truth used Cloud Logging OOM-absence + live diagnostic log lines instead. - **`--hotfix-to-main` explicitly
      NOT used** (requires operator env `QUICKMERGE_HOTFIX_TO_MAIN_OK=1`, "agents cannot self-authorize"); the normal
      `*/15` fleet promotion carried every round. - **2 shared-infra side-incidents found + fixed this session**: (1)
      `base-service.sh`'s non-portable `grep -oP` (GNU-only PCRE) silently aborted `quality-gates.sh` host-wide under
      `set -e` (macOS BSD grep has no `-P`) — fixed via `rg --pcre2` (already a hard QG dependency). (2) shipping that
      fix raced a concurrent session's independent fix for the same bug — an autostash reconciliation committed+pushed
      literal `<<<<<<</=======/>>>>>>>` conflict markers to `live-defi-rollout` (`eb50e13cc`), breaking every slot's QG
      the same way — caught via a direct `bash -n` check against the ACTUAL pushed content (never trust a reported "✅
      Pushed" alone) and corrected (`d6495e760`).
- [x] [SCRIPT] P1. ✅ **Killed the hung idle `mtds-dex-swaps-backfill-2` VM.** Re-confirmed before deleting: no
      `PROGRESS.json` at its GCS log path (404), `run.log` tail (15:15-15:20Z) showed only RESOURCE_SAMPLE/
      PIPELINE_HEARTBEAT lines at ~0-1.4% CPU, no processing activity since the `process_final=True` shard-complete line
      at 07:50:33Z (7.5h idle). Deleted via
      `gcloud compute instances delete mtds-dex-swaps-backfill-2     --zone=asia-northeast1-c` (2026-08-07T15:2xZ) —
      justification: confirmed-finished worker VM, non-preemptible on-demand billing with zero further useful work
      possible, not a data-delete (no GCS/manifest content touched).
- [x] [SCRIPT] P1. ✅ **Fixed `vm-serial-capture-prd`** — still a genuinely needed function (no successor found; it's
      the periodic GCE serial-console capture for `LONG_LIVED_LIVE`/`SCHEDULED_RECURRING` VMs, distinct from the
      already-working `vm-log-archival-prd` cron — live in `cloud_run_job_registry.py`'s `_SINGLETON_JOBS`, UTL helper
      `vm_serial_rolling_uri` actively tested; unlike `market-data-query-service` this one has NO co-location/successor
      migration). Root cause: `deployment-service/terraform/gcp/vm_serial_capture_scheduler.tf`'s `image:` field pointed
      at Artifact Registry repo `unified-trading-library/deployment-service:latest` — that repo has **zero**
      `deployment-service` images (confirmed via `gcloud artifacts docker images list`), a copy-paste bug (confusing the
      source-repo name for an AR docker-repo path). The correct, actively-published repo is `unified-trading-system`
      (confirmed via the working sibling `vm-log-archival-prd`, which uses that path). Fixed the `image:` line +
      documented the gotcha inline; `ENV=prod tofu.sh apply -target=google_cloud_run_v2_job.vm_serial_capture` applied
      the 1-line diff (plan showed exactly 0 add/1 change/0 destroy). **Verified live**: `gcloud run jobs describe`
      shows `Ready: True` (ContainerMissing cleared); manually triggered execution `vm-serial-capture-prd-mjghx`
      **succeeded** — 5 VMs captured, 0 errors, exit(0), real objects written to
      `gs://deployment-scripts-central-element-323112/log-archive/serial-rolling/20260807/...`. Shipped
      `deployment-service@a1936e72` via quickmerge (QG green: `ALL QUALITY GATES PASSED`, sentinel
      `22f35fa32c7bbcd45429482a1818af53900ad5cb` == HEAD at push).
- [x] [SCRIPT] P1. **Fix the 3 dead `europe-west1` jobs** (`tardis-data-loader`, `check-missing-cloud-storage`,
      `gen-inst-defs`) — 100% failure for 50 days on a stale `gcr.io/...` path orphaned by the AR migration. ✅ All 3
      verdicted OBSOLETE (superseded, not fixed) — zero references to any of the 3 job/image/pubsub-trigger names in any
      of the ~30 current source repos (`rg` full-workspace + `_archived`/`archive`, 0 hits outside unified-trading-pm
      planning docs); each already has a live current successor: `tardis-data-loader` → the VM-based sharded Tardis
      backfill pipeline (`deployment-service/scripts/vm/tardis-concurrency-guard.sh` +
      `mtds-backfill-cefi-*`/`cefi-queue-*` VMs, capped at 1 concurrent per
      `/codex/05-infrastructure/vm-launcher-runbook.md` § Tardis Concurrent-VM Cap) — matches this doc's own May-2026
      snapshot already flagging it "legacy 2024; likely zero traffic"
      (`/codex/05-infrastructure/aws-migration-cost-snapshot-2026-05-07.md:187`); `gen-inst-defs` →
      instruments-service's live per-venue `reference_data/adapters/*` instrument-definition generation (IS is the
      CLAUDE.md-declared SSOT for reference data); its trigger topic `gen-inst-defs-job-trigger` is independently
      flagged "Legacy infrastructure (likely stale)" in `/codex/05-infrastructure/pubsub-topic-inventory.md:103`;
      `check-missing-cloud-storage` → superseded by the current
      manifest/availability-manifest/`data-pipeline-reconciliation` system, the present SSOT for "what's missing from
      GCS." Action taken per the obsolete-path: paused all 3 Cloud Scheduler triggers rather than deleting
      (`tardis-data-loader-scheduler`, `check-missing-cloud-storage-scheduler`, `gen-inst-defs-scheduler`, all
      `europe-west1`) — verified `state: PAUSED` post-pause via `gcloud scheduler jobs list`. No code/config fix needed
      (no repo owns these jobs). Flagging for a follow-up deletion todo (Cloud Run Job resources + schedulers) once
      confirmed stable with the pause — same disposition as this doc's existing `central-market-data-tardis-loader`
      decommission todo above. Evidence:
      `gcloud run jobs executions list --job=<job> --region=europe-west1     --project=central-element-323112` showed
      `Image '...' not found` on all 5 most-recent executions per job (2026-08-03 through 2026-08-07);
      `gcloud scheduler jobs list --location=europe-west1 --project=central-element-323112` showed all 3 `state: PAUSED`
      post-fix. (repo: unified-trading-pm, no code repo — infra-only)
- [x] ✅ [SCRIPT] P1. **Fix `live-event-log-compactor` daily OOM** — DONE (multi-slot effort 2026-08-07/08, re-verified
      live 2026-08-09). Root cause was two compounding bugs, not simple undersizing: (1) warm GCS objects are NDJSON
      (multiple `CanonicalPersistEnvelope` per file) but the compactor parsed each file as a single JSON document —
      every envelope failed validation, so cold compaction had silently written ZERO cefi cold data since inception,
      masking the shard's true memory requirement; (2) once NDJSON parsing was fixed, `(cefi, book_snapshot_5)` proved
      to be genuinely large (~204GiB/day) — real organic growth, not a leak. Fix: NDJSON per-line parsing
      (deployment-service@d5f850f1), schema-drift + column-order handling (@5281cb0a0, @d304c0ba), per-file batching to
      cut Arrow overhead (@e57441c0), memory raised in verified steps 512Mi(implicit default; never actually
      4Gi)→4Gi→16Gi + CPU 2→4 (@5e23a7b0, @454cccd9c), task timeout extended 3600s→28800s(8h) to match real compaction
      time (@6edec6b9, @e584b559, @4648b5ea), plus a COMPACTION_DATE backfill mechanism (@9e1ab495) — this already gives
      per-date chunking (one execution per day, not the whole log at once) on top of the per-file streaming write path.
      Backfill: all 7 missed dates (2026-08-01→2026-08-07) × 4 cefi data_types backfilled — 28 cold parquet objects
      confirmed via `gcloud storage ls gs://central-element-323112-events/live-events/cold/cefi/**`. Live verification:
      the next scheduled 02:00 UTC run (`live-event-log-compactor-9z2tv`, 2026-08-08T02:00:04Z) completed successfully
      in 2h49m35s with zero OOM — first clean scheduled run after the 7-day OOM streak (2026-08-01 through 2026-08-07,
      all `The configured memory limit was reached`). Full incident:
      `/plans/archive/issues/cefi_live_event_cold_compactor_oom_and_legacy_path_check_2026_08_07.md` (status: resolved).
      (repo: deployment-service)
- [x] [SCRIPT] P2. **Reduce `mtds-backfill-odds-401-retry` memory footprint** ✅ — root cause: `CHUNK_SIZE` (days per
      subprocess-per-league in `mtds_chunk_loop.sh`) defaulted to 250 in
      `deployment-service/scripts/vm/launch-mtds-sports-odds-backfill-vm.sh`, vs. `CHUNK_SIZE=5` on the working
      `mtds-backfill-odds-smallchunk-20260807` sibling (`LAUNCH_PARAMS.json` diff confirmed — both share the same
      launcher). A wide chunk lets one subprocess accumulate many real-fetch days' worth of RSS before it exits (the
      root cause already diagnosed in `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`); live re-check same day:
      401-retry hit 15 `OOM_KILLED` in ~80min vs. the smallchunk sibling's 2 over the same window. Fix: launcher default
      changed 250→5 (deployment-service@22f35fa32c7bbcd45429482a1818af53900ad5cb, QG green — `IGNORE_TIMEOUT=true`,
      sanctioned host-contention override, all substantive gates incl. 3151 tests + 71.76% coverage passed; shipped via
      quickmerge, landed on `live-defi-rollout`). This is a mitigation, not the confirmed root-cause fix — the
      underlying native-memory leak investigation stays open in that issue doc. Live-VM check:
      `mtds-backfill-odds-401-retry` itself is no longer running — it was SPOT-preempted (`compute.instances.preempted`,
      2026-08-07T16:55Z) and auto-deleted per its own `--instance-termination-action=DELETE`, not OOM-killed into
      oblivion; no hot-apply path exists (`VM_CHUNK_DAYS` is baked into the boot-time-generated `mtds_chunk_loop.sh`,
      not re-read from metadata), so no live intervention was needed or attempted. A separate
      `mtds-backfill-odds-     smallchunk9` VM (started 2026-08-08) is already continuing the backfill with the
      small-chunk approach.
- [x] [SCRIPT] P2. **Fix the `dp-alerting-subscriber` GCS 429 retry storm** ✅ on `write_config_snapshot`'s
      `routing_rules.yaml` writes (479 occurrences in one day, separate from the already-fixed `mirror_live` bug) —
      confirmed root cause: `router.route_event()` calls `_persist_config_snapshot()` on every routed event, but
      `AlertingSystemConfig.routing_rules` is process-lifetime-static (byte-for-byte render of the UAC
      `LIVE_ALERT_RULES` SSOT), so every write re-uploaded byte-identical content to the same blob. Fix: in-memory
      SHA-256 content-hash cache keyed by snapshot `name` in `AlertStorageStore.write_config_snapshot` — skips the GCS
      upload when unchanged since the last successful write, still writes immediately on genuine change (preserves audit
      intent). 5 regression tests added. Evidence: `alerting-service@066a1bcad8e6c17edcdc4bbefc2cc872fcb1408a`, QG green
      (`ALL QUALITY GATES PASSED`, sentinel `58824f38b0dd41a6421812cb8d28424f1e6f1f8b`), landed on LDR
      (`live-defi-rollout`) via quickmerge 2026-08-09. LDR→main fleet promotion was stalled at the time (see
      `plans/active/issues/strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md` Progress Log
      2026-08-07 recurrence entry) — deploy propagation to Cloud Run not verified as part of this todo.
- [x] [SCRIPT] P3. **Fix the AWS cost-snapshot IAM failure** ✅ — root cause: OIDC identity drift, not a permissions
      bug. AWS IAM role `gcp-cloudrun-athena-cost-reader` (trust policy `Federated: accounts.google.com`, condition
      `accounts.google.com:sub == 104881302737822972808`) was provisioned 2026-07-14 trusting
      `unified-trading-sa@central-element-323112.iam.gserviceaccount.com`'s OIDC subject, but the LIVE
      `uts-shared-deployment-api` Cloud Run revision actually runs as
      `uts-prd-sa@central-element-323112.iam.gserviceaccount.com` (uniqueId `108768985147151736276`, verified via
      `gcloud run services describe ... spec.template.spec.serviceAccountName`) — a different SA, different `sub` claim,
      hence the deployed service's minted OIDC token was never trusted by the role and every
      `sts:AssumeRoleWithWebIdentity` in `deployment_api/scripts/cost_snapshot_worker.py`'s
      `_load_cloud(CLOUD_AWS, ...)` → `aws_facts` → `get_athena_analytics_client` path (used by both the Cloud
      Scheduler-driven `/api/costs/snapshot-run` endpoint AND the standalone worker entrypoint) hit AccessDenied. Fixed
      by widening the AWS-side trust policy condition to
      `StringEquals accounts.google.com:sub: [104881302737822972808,     108768985147151736276]`
      (`aws iam update-assume-role-policy --role-name gcp-cloudrun-athena-cost-reader`) — trusts both the
      originally-provisioned SA and the actual runtime SA, non-destructive. Verified end-to-end LIVE: minted a real OIDC
      id-token as `uts-prd-sa`
      (`gcloud auth print-identity-token --impersonate-service-account=uts-prd-sa@...     --audiences=arn:aws:iam::427895769566:role/gcp-cloudrun-athena-cost-reader`)
      and called `aws sts assume-role-with-web-identity` with it — succeeded, returning
      `arn:aws:sts::427895769566:assumed-role/gcp-cloudrun-athena-cost-reader/verify-fix-test3`. No GCP-side code/config
      change needed — AWS IAM change only.
- [x] [SCRIPT] P3. **Decommission dead-weight services** ✅ — verified each independently (not just trusting the
      original audit) via
      `gcloud run services describe <svc> --region=<r> --format="table(status.traffic,status.conditions)"` +
      region-scoped Cloud Logging (`resource.labels.service_name=... AND resource.labels.location=...`) for any real
      request traffic, then deleted via `gcloud run services delete <svc> --region=<r> --quiet`. All 6 confirmed: single
      revision `00001` (or equivalent), `HealthCheckContainerError`, `status.traffic` empty/absent (never routed),
      near-zero log volume (3 lines = just the startup-failure event; 0 httpRequest entries in 30-90d). Deleted:
      `batch-live-reconciliation-service` (asia-northeast1, created 2026-07-22), `deployment-service` (asia-northeast1,
      created 2026-07-22 — confirmed this is the STUB, image `.../unified-trading-system/deployment-service:latest`,
      zero relation to the real, live `uts-shared-deployment-api` service which was independently confirmed still
      serving post-delete), `fund-administration-service` (asia-northeast1, created 2026-07-22), `trading-agent-service`
      (asia-northeast1, created 2026-07-22), `odum-portal-staging` (us-central1, created 2026-04-24, 0 logs/0 requests
      in 90d region-scoped), `central-market-data-tardis-loader` (europe-west1, created 2024-06-29, broken since
      2024-12-16, 0 logs in 7d; `minScale` annotation not actually present at delete-time, defaults to 0 — the
      "continuously retrying" framing was stale, but dead-since-2024/zero-traffic independently confirmed regardless).
      **Caught a near-miss**: an UN-region-scoped log query for `odum-portal-staging` initially returned 6173 log lines
      incl. live 200-status `/health` + `/wizard` traffic — turned out to be a SEPARATE, live `odum-portal-staging`
      service in **europe-west4** (183 revisions, 100% traffic, unrelated to the dead us-central1 stub the task named)
      whose logs share the same `service_name` label; re-scoped the query with `resource.labels.location="us-central1"`
      and got 0 logs/0 requests, confirming ONLY the us-central1 instance was dead. The europe-west4 live instance and
      the real `uts-shared-deployment-api` were both verified untouched post-deletion.
- [x] [SCRIPT] P1. ✅ **Recheck `mdps-backfill-cefi-20260807-130321` preemption** — preempted 2026-08-07T14:49:27Z; the
      same launcher left a sibling VM un-relaunched for ~33h on 2026-08-04. Verify it actually got relaunched this time
      (per the PROGRESS-checkpoint contract) — if not, this is the exact class of bug the launcher-registry
      preemption-recovery contract is supposed to prevent, and needs the same fix applied fleet-wide, not just a one-off
      relaunch. **(a) VM-specific: did NOT recover — worse than the 2026-08-04 precedent.** No successor
      instance/vm-logs dir was ever created (`gcloud compute operations list` shows only
      `insert`+`compute.instances.preempted` for this exact name, nothing after); the VM was instead silently REAPED as
      `vm_not_running` at 14:55:49Z (`reap_stale: archived ... reason=vm_not_running`) with zero relaunch attempt — no
      PROGRESS.json checkpoint ever existed either (`mdps-backfill` is a single-shot `_launch_with_tee` VM_TASK in
      `setup-data-pipeline-vm.sh`, not one of the chunked launcher families with the shell-level `[[VM_PROGRESS]]`
      marker per `/codex/05-infrastructure/spot-vms-for-backfill.md`), so even a relaunch would have replayed
      `START_DATE=2023-06-01` verbatim. This VM's specific relaunch-or-confirm action is already tracked separately at
      `/plans/active/cefi_satellite_ao_dispatch_batch10_2026_08_08.md` todo (line ~135) — not duplicated here. **(b)
      General DP-VM-008/009/011 mechanism: found GENUINELY BROKEN at the root, now FIXED.** The exit-code fleet monitor
      (`uts-prod-dp-exit-code-monitor`, Cloud Run Job, cron healthy — ran on schedule every 5 min straight through the
      incident, confirmed via `gcloud run jobs executions list`) DID see the VM terminate (14:51:03Z: "1 terminated ...
      0 preempted") but its Operations-API preemption fallback (`was_instance_preempted` in
      `unified-trading-library/.../gcp_compute.py`, consulted whenever the in-guest GCS `PREEMPTED` marker is absent —
      exactly this VM's case, killed too abruptly for its shutdown-script to write one) returned `False` for a VM that
      was provably preempted (`compute.instances.preempted` op confirmed live via `gcloud compute operations list`).
      Root-caused by reproducing the exact call live against GCP (`.venv/bin/python` +
      `unified_trading_library.cloud_interface.get_compute_engine_client(...).was_instance_preempted(...)` returned
      `False`): the server-side GCE Operations `aggregatedList` filter's compound clause
      `(operationType="compute.instances.preempted") AND (targetLink:"<vm_name>")` silently returns ZERO results — the
      `:` "has" operator does not do substring/contains matching on URL-typed fields like `targetLink` at all (tested
      every wildcard variant, all 0 hits; only a full-URL EXACT match works, which needs the zone ahead of time). Never
      raised — `_compute_ops.py`'s inner `try/except: return False` swallows it silently, so this failure mode had ZERO
      diagnostic trace anywhere (no WARNING logged, confirmed via `gcloud logging read`). Net effect: `DP_VM_PREEMPTED`
      never fired for this class of VM (abrupt-kill, no in-guest marker) since the fallback was added — not just this
      incident — so `DP_VM_PREEMPTED_NO_RELAUNCH` (DP-VM-009) never had a chance to fire either, since its own
      precondition (a detected-but-unrelaunchable preemption) was never reached. The primary GCS-marker signal path and
      the actuator/relaunch layer itself are NOT broken (same-day `DP_VM_PREEMPTED`+`DP_VM_PREEMPTED_RECOVERED` fired
      correctly for `cefi-fwd-20260807-100050` at 10:25Z via that path) — this was specifically the abrupt-kill
      fallback. **Fix**: dropped the dead `targetLink` clause from the server-side filter (kept `operationType`-only,
      still bounded — ~750 ops fleet-wide, not an unbounded scan) and rely entirely on the already-present client-side
      exact trailing-path-segment match. Re-verified live post-fix: same call now returns `True`. Added a regression
      test (`test_server_side_filter_has_no_dead_target_link_clause`) pinning the filter string so a future re-add of a
      targetLink clause fails loudly. Shipped `unified-trading-library@dc5fc16a6` (quality-gates.sh green,
      `--agent --files`). **Residual**: this fix is live on LDR; propagating to the actually-deployed
      `uts-prod-dp-exit-code-monitor` Cloud Run image requires the standard LDR→main promotion + wheel publish +
      deployment-service picking up the new pin and rebuilding/redeploying — not yet confirmed live in the deployed cron
      job as of this writing (a separate downstream step, not "next 5-min tick").

## Progress Log

- 2026-08-07: Plan created following a 3-agent parallel infra health audit (Cloud Run Jobs, Cloud Run Services, GCE
  VMs). Excluding the DeFi manifest-consolidator finding per operator direction (already tracked as a known, intentional
  condition). Proceeding under `/autonomous`.
- 2026-08-07: Todo 2 (alert-coverage cross-reference) DONE — see the todo's own entry for the full summary. Filed
  `/plans/active/issues/infra_health_audit_alert_coverage_gaps_2026_08_07.md`.
- 2026-08-07: Todo 1 (dedicated zombie sweep), Cloud-Scheduler-dead-target class — re-derived the full
  scheduler↔Cloud-Run-Job cross-reference for `asia-northeast1` (158 schedulers) + the 1 in-scope `europe-west1` job
  (`central-market-data-service-scheduler-trigger`; the other 3 europe-west1 zombies were already fixed above in this
  same todo). Found 38 schedulers targeting a Cloud Run Job that no longer exists (32 `ENABLED` + 6 already `PAUSED`);
  bulk-paused all 32, verified 38/38 now `PAUSED`; flagged 4 with an obvious live successor as repoint candidates (not
  auto-repointed). Filed `/plans/active/issues/asia_northeast1_zombie_schedulers_dead_targets_2026_08_07.md` with the
  full list + repoint candidates + a `[OPERATOR]` follow-up todo.
- **na-eligibility-audit 2026-08-07 (ui tranche)**: KEEP-NA, stale items closed (2) — a literal duplicate
  "Alert-coverage cross-reference" todo (its checked twin already did the work) and a now-moot "fix
  market-data-query-service crash-loop" todo (the service was deleted entirely by an earlier todo in this same doc). Doc
  otherwise stays NA — genuinely live, currently-being-executed `/autonomous` infra remediation work created today (P0),
  8 remaining open items are real unblocked ops-fix work, not defaulted/unassessed.
- **na-eligibility-audit 2026-08-08 (ui tranche)**: KEEP-NA, valid — re-confirmed; a same-day `/autonomous` session
  closed the `client-reporting-batch` OOM item (live-verified `2Gi` limit) since yesterday's marker, so 7 items remain
  open (was 8). Every remaining item still requires investigate-then-decide judgment before a fix is even choosable
  (zombie-sweep classification; shard-vs-resize on the rollup OOM; keep-vs-decommission on `vm-serial-capture-prd`;
  root-cause-before-raising-the-ceiling on the compactor OOM; a coalescing/backoff design for the 429 storm;
  verify-then- maybe-fleet-wide-fix on the preemption recheck) — none is a pre-decided, deterministic-outcome todo. One
  exception worth flagging for a future look: the `mtds-backfill-odds-401-retry` memory-footprint item has a direct
  working precedent to copy (`mtds-backfill-odds-smallchunk-20260807`'s chunk-size mitigation) and reads more bounded
  than its siblings — not promoted to RECLASSIFY this run since the doc's other 6 items don't clear the bar and a
  whole-doc flip would dispatch those too, but worth a second look if it's still open next pass. Doc stays NA as a
  whole; still genuinely live `/autonomous` work, not defaulted/unassessed.
- **2026-08-09**: Confirmed the "tracked elsewhere" `mdps-backfill-cefi-20260807-130321` action (todo above, line ~225)
  was actually executed, not just referenced. Independently re-verified the old VM is genuinely gone (404 on
  `gcloud compute instances describe`, only `insert`+`compute.instances.preempted` ops, no successor — matches this
  todo's own finding) and relaunched it (`mdps-backfill-cefi-20260808-095136`, SPOT e2-standard-8, launched
  2026-08-08T08:56:57Z, confirmed STARTED + still RUNNING, actively progressing, no preemption op). While verifying,
  found concurrent slot-16/slot-7/slot-26 work had already landed on the SAME VM + the same underlying bug: `--force`
  was silently dropped in MDPS's per-date subprocess spawner (root-caused + fixed,
  `market-data-processing-service@e9f9819`; writeup `issues/mdps_force_flag_dropped_subprocess_per_date_2026_08_08.md`)
  — this pre-fix VM will not itself fix the BYBIT bundles even at completion; a per-day-scoped relaunch is already
  queued in `issues/cefi_track7_candle_bundle_regeneration_vm_2026_08_04.md` for once it reaches terminal state. No
  duplicate relaunch performed. Full detail: `cefi_satellite_ao_dispatch_batch10_2026_08_08.md` todo 3 (already flipped
  `[x]`) and the Track-7 issue doc's "2026-08-08 84-cell audit" section.
- **na-eligibility-audit 2026-08-09 (ui tranche, dispatch agt-eee16e)**: KEEP-NA, valid — re-confirmed; only 1 open item
  remains (`uts-prod-data-status-rollup-svc` OOM), down from 7 at the 2026-08-08 marker as the other 6 closed out since.
  Content shift worth flagging: this item has moved from open-ended investigate-then-decide judgment (its 2026-08-08
  framing) to a bounded, deterministic verify-then-flip — the fix (`deployment-api@e2b9a55`) is already shipped to LDR,
  and the only remaining step is (a) wait for the external ~hourly LDR→main promotion to land it, (b) check Cloud
  Logging for `SERVICE_PROCESSED` events on MTDS/instruments-service, (c) flip the checkbox with that evidence. That
  shape would normally clear the RECLASSIFY bar, but this doc is under continuous active hands-on iteration right now
  (Progress Log entries at 2026-08-09T01:52Z and T01:58Z, within the hour of this audit) — reclassifying mid-flight
  risks a duplicate/competing dispatch racing whichever session is already driving it live. Tagging
  MISCLASSIFIED_LIKELY_AO_ELIGIBLE rather than promoting to a clean RECLASSIFY this pass; re-assess next run against the
  primary RECLASSIFY bar if this item is still open and the doc has gone quiet (no Progress Log edit in the interim).
- **2026-08-09T07:43Z (round 3)**: the daemon=False hotfix (`e2b9a55`) deployed live 2026-08-09T03:43Z but the OOM
  PERSISTED — measured 10/10 cron cycles over the following 6h, every single one, via the full Cloud Logging history for
  revision `uts-prod-data-status-rollup-svc-00360-hkf`. Root-caused to a genuinely different bug: the per-service
  timeout-kill path (`_run_service_isolated`, unchanged since before per-category sharding existed) only signals the
  per-service child's own PID, orphaning the per-category grandchild it spawns under `_SERIAL_DISPATCH_ISOLATED` when
  the (routine, not rare) 420s outer timeout fires mid-category — the orphan keeps consuming memory, uncapped by
  anything tracking it, until the container tips over 32Gi. Fixed via process-group isolation
  (`os.setpgrp()`/`os.killpg()`) in `deployment-api@6ac1c43ff66cbeff4903c6559cbbac70fb1299ec`, applied to both the
  concrete caller (`data_status_rollup_worker.py`) and the shared `bounded_subprocess.run_bounded` utility. QG green,
  shipped via normal quickmerge (no carve-out), landed on LDR. Live verification pipeline armed and in progress
  (LDR→main promotion → Cloud Build → new revision → ≥2 rollup cron cycles → Cloud Logging/GCS blob-freshness checks);
  will update this entry with a definitive verdict once it completes.
