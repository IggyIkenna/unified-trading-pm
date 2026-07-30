---
doc_type: issue
title:
  "MTDS CeFi Cloud Run jobs' shared image `market-data-tick-handler:latest` has not been rebuilt since 2026-02-11 -- 5.5
  months of source drift, missing every fix since including the 2026-07-28 book_snapshot_5 schema-contract fix"
summary: >-
  While investigating a DP_RUN_MOSTLY_EMPTY (DP-FETCH-009) re-page for cefi/book_snapshot_5 (see
  cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md), traced a small fresh
  schema-contract-violation tail (39 rows, 2026-07-30T16:21-18:45Z) to check whether a stale-code Cloud Run job was the
  producer. Found: the Cloud Run jobs `market-tick-cefi-binance-futures`, `market-tick-cefi-okx`,
  `market-tick-cefi-daily-download` (and likely siblings `market-tick-cefi-binance-spot`/`-bybit`/`-coinbase`/`-upbit`,
  not individually checked) all reference
  `asia-northeast1-docker.pkg.dev/central-element-323112/market-data-tick-handler/market-tick-data-handler:latest`.
  `gcloud artifacts docker images list ... --include-tags` shows only 6 images total, the newest push (including the
  `:latest` tag) timestamped `2026-02-11T11:05:09Z` -- **5.5 months stale relative to today (2026-07-30)**, meaning any
  execution of these jobs would run code missing every commit since mid-February, including the 2026-07-28
  schema-contract fix (`market-tick-data-service@339ca767` + `unified-api-contracts@8db188fe`) and everything else
  shipped in between. **Not confirmed as the cause of the 39-row tail** -- `gcloud logging read` found ZERO invocations
  of `market-tick-cefi-binance-futures` in the last 7 days, so this specific job set appears dormant, not the active
  source of that tail (which remains unattributed). This is filed as an independent staleness/blast-radius risk: if any
  of these dormant Cloud Run jobs is ever re-triggered (manually, by a forgotten scheduler, or by a future automation
  change), it will silently run 5.5-month-stale code with no warning. Read-only investigation -- no image rebuilt, no
  job triggered, no code changed.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [data-pipeline, docker-image, stale-image, cloud-run, cefi, dp-fetch-009, deploy-drift]
related:
  [
    /plans/active/issues/cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: 2026-07-30
parent_epic: cefi_master
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
execution_scope: local-only
resolved_by:
source:
  "Found during data_pipeline_failure escalation agt-c271de (dp-fleet-monitor -> agent-orchestrator, slot-10,
  2026-07-30) while investigating a fresh tail on the DP_RUN_MOSTLY_EMPTY (DP-FETCH-009) cefi/book_snapshot_5 alert."
last_updated: 2026-07-30
---

# MTDS CeFi Cloud Run jobs' `market-data-tick-handler:latest` image is 5.5 months stale

## What was found

Investigating a small (39-row) fresh `"schema contract violated"` tail on `(cefi, book_snapshot_5)` (`attempted_at`
2026-07-30T16:21:25Z-18:45:24Z, all targeting `date` in 2020-01/02), I checked whether a Cloud Run job with stale code
could be the producer, since the exact same bug shape (schema-contract violation on book_snapshot_5) was root-caused and
fixed 2026-07-28 in `market-tick-data-service@339ca767` + `unified-api-contracts@8db188fe`.

```
$ gcloud run jobs describe market-tick-cefi-binance-futures --region=asia-northeast1 \
    --format="value(spec.template.spec.template.spec.containers[0].image)"
asia-northeast1-docker.pkg.dev/central-element-323112/market-data-tick-handler/market-tick-data-handler:latest

$ gcloud artifacts docker images list \
    asia-northeast1-docker.pkg.dev/central-element-323112/market-data-tick-handler/market-tick-data-handler \
    --include-tags --format="value(tags,updateTime)"
a9c9bc4                2026-02-11T11:05:09
45effcd,latest          2026-02-11T11:05:09
44dbe65                2026-02-11T09:53:01
e5a587e                2026-02-11T08:26:48
664f056                2026-02-10T17:38:19
b8ca7b8                2026-02-10T10:37:34
```

Only 6 images exist in this repository, all pushed 2026-02-10/11. `:latest` is the same digest as `45effcd`, pushed
`2026-02-11T11:05:09Z`. Same shared image referenced by `market-tick-cefi-okx` and `market-tick-cefi-daily-download`
(checked directly); `market-tick-cefi-binance-spot`/`-bybit`/`-coinbase`/`-upbit` were not individually re-checked but
are the same job family and plausibly share the same image (not confirmed).

## Not confirmed as the book_snapshot_5 tail's cause

```
$ gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="market-tick-cefi-binance-futures"' \
    --freshness=7d --limit=10
(no results)
```

Zero invocations in the last 7 days. This job set is currently dormant, not the active source of the 2026-07-30 tail
(which self-resolved before this session's second manifest check and remains unattributed to a specific compute unit —
see the parent doc's Progress Log entry for the fuller trace, including the running-VM-fleet check that also came up
empty).

## Why this is still worth tracking

A dormant Cloud Run job with a 5.5-month-stale image is a silent landmine: nothing pages on image staleness itself, and
the next time this job set is triggered (manual operator run, a forgotten/re-enabled scheduler, or a future automation
wiring it back in) it will silently execute code missing every fix shipped since 2026-02-11 -- including, ironically,
the exact schema-contract regression class this investigation started from. This is the same "IMAGE GAP" failure shape
already named in `/codex/05-infrastructure/data-pipeline-alerts.md` (the e2e-audit runner image gap, closed 2026-06-22)
-- a different instance of the same anti-pattern (deploy artifact silently diverging from source).

## What was NOT done (out of this one-shot escalation's scope)

- Did not determine whether this job family is truly dead/superseded (e.g. by the VM-based Tardis backfill launchers
  that are the documented primary CeFi capture path per CLAUDE.md's "Backfill VMs default to SPOT" section) or merely
  dormant-but-still-wired-in via some trigger not checked here (a Cloud Scheduler entry naming it differently, a manual
  runbook, a dependency from another service).
- Did not check the other 4 job siblings (`market-tick-cefi-binance-spot`/`-bybit`/`-coinbase`/`-upbit`) individually.
- Did not rebuild the image or trigger a fresh Cloud Build.
- Did not identify the actual producer of the 39-row tail this investigation started from.

## Recommendation

If this job family is confirmed still-relevant (not a dead/superseded legacy path): rebuild + push a fresh
`market-data-tick-handler` image before the job is next triggered, and consider wiring image-staleness into the existing
"watch-the-watchers" deployment-observability surface (a dormant-job-with-stale-image class is exactly the kind of
silent-until-triggered risk that surface already exists to catch for other mechanisms). If this job family is confirmed
dead/superseded by the VM-based launchers: delete the Cloud Run jobs (removes the landmine entirely) rather than rebuild
an image for something that should not run again.

## Todos

- [ ] [OPS] P2. Determine whether `market-tick-cefi-binance-futures`/`-okx`/`-daily-download`/`-binance-spot`/`-bybit`/
      `-coinbase`/`-upbit` are still-relevant (rebuild the image) or dead/superseded by the VM-based launcher path
      (delete the jobs) -- a scoping/judgment call, not determinable by this investigation alone.
- [ ] [OPS] P3. If kept: rebuild + push a fresh `market-data-tick-handler` image so a future trigger doesn't silently
      run 5.5-month-stale code.

## Progress Log

- **2026-07-30 (data_pipeline_failure escalation worker, slot-10, task agt-c271de):** Filed this doc after finding the
  stale image while investigating an unrelated fresh tail on the cefi/book_snapshot_5 DP-FETCH-009 alert (see
  `cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md`'s Progress Log for the full context).
  Read-only investigation only; no image rebuilt, no job triggered, no code changed.
