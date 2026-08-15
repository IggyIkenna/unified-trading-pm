---
doc_type: issue
title: >-
  DP_CLOUD_RUN_JOB_FAILED (DP-WATCHER-006) — uts-prod-dp-daily-digest OOM at 16Gi, then again at 32Gi (defi crossed the
  documented headroom estimate); resolved via 32Gi bump + a DuckDB GROUP-BY-pushdown rewrite, both verified live
summary: >-
  `uts-prod-dp-daily-digest` (the daily per-AG completion digest, `0 7 * * *` UTC) OOM-killed on its 2026-08-14T07:00
  UTC run ("The configured memory limit was reached", `failed_count=1`), triggering `DP_CLOUD_RUN_JOB_FAILED`/
  DP-WATCHER-006 (PAGE_OPERATOR, no auto-recover tier for a generic job failure) ~1233 minutes later. This was the exact
  scenario `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md`'s P3 todo predicted and pre-approved a response
  for: that todo measured the digest's peak RSS at ~11.8GiB after two rounds of memory-antipattern fixes, ruled 11.8GiB
  "the acceptable steady state" under the 16Gi ceiling, and explicitly recommended a DuckDB migration once defi crosses
  the ~16Gi headroom estimate. Bumping to 32Gi (Cloud Run gen2's hard ceiling) was NOT sufficient on its own — a
  re-execution still OOM'd, dying specifically on defi (confirmed via execution logs: cefi completed, defi never
  finished). Since 32Gi is the platform's ceiling (no further infra lever), the DuckDB `GROUP BY`-pushdown rewrite was
  implemented in this same escalation rather than left deferred. Both fixes are live and verified: a manual re-execution
  completed all 5 AGs (including defi, 99.4% over 3560 cells) and emitted the digest cleanly.
status: resolved
nature: issue
asset_group: [cross-cutting, defi]
stage: [meta]
repos: [deployment-service, e2e-testing]
scope: [engineer, admin]
tags:
  [
    data-pipeline-monitors,
    dp-watcher-006,
    dp-cloud-run-job-failed,
    dp-daily-digest,
    oom,
    duckdb-aggregation,
    cloud-run-job,
  ]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md,
    /plans/archive/2026_07/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/archive/2026_08/issues/dp_reprobe_empty_oom_regression_unbounded_manifest_read_2026_08_09.md,
    /plans/archive/2026_08/read_availability_index_slim_read_oom_at_defi_scale_2026_08_01.md,
  ]
created: 2026-08-15
author: data_pipeline_failure escalation agent (agt-8a1647, slot-31)
parent_epic: infrastructure_master
priority: P2
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
assigned_role:
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by: data_pipeline_failure escalation agent (agt-8a1647, slot-31)
last_updated: 2026-08-15
locked_since:
context_scope:
source: >-
  DP_CLOUD_RUN_JOB_FAILED (DP-WATCHER-006) escalation, dispatched by the self-monitoring substrate
  (`cloud_run_job_failure_watcher.py`) via `POST /api/escalate` with `wall_type=data_pipeline_failure` — no pre-filed
  issue doc, the alert itself carried the full detail (job name + failed_count + completion age).
---

# DP_CLOUD_RUN_JOB_FAILED — `uts-prod-dp-daily-digest` OOM at the documented 16Gi ceiling

## What I found

`gcloud run jobs executions describe uts-prod-dp-daily-digest-5hsbp` (region `asia-northeast1`, project
`central-element-323112`):

```yaml
status:
  completionTime: "2026-08-14T07:01:51.438858Z"
  conditions:
    - message:
        "Task uts-prod-dp-daily-digest-5hsbp-task0 failed with exit code: 0 and message: The configured memory limit was
        reached."
      status: "False"
      type: Completed
  failedCount: 1
  startTime: "2026-08-14T07:00:11.346033Z"
```

Live job spec at diagnosis time: `cpu=4`, `memory=16Gi` — matching the 2026-07-26 bump
(`data_pipeline_self_healing_completion_residual_2026_07_24.md`), which itself followed the 2026-08-05 decision that
measured peak RSS at ~11.8GiB and called 16Gi "safely under" that — with an explicit escape hatch for when defi grows
further. That escape hatch is what fired here.

## Why it matters

DP-WATCHER-006 has no `auto_recover` tier for a generic Cloud Run Job failure (by design — "the root cause is unknown
and job-specific," per `cloud_run_job_failure_watcher.py`'s own docstring) — every occurrence pages
`PAGE_OPERATOR`/CRITICAL with no self-heal. Left unfixed, the daily digest (the primary per-AG completion visibility
into `#data-pipeline-alerts`) silently stops posting, and the page keeps firing (or worse, degrades to a p95-not-yet
gated re-alert per the MissTracker's `min_consecutive` gate) every day defi's index keeps growing.

## Resolution

Both the immediate mitigation (32Gi terraform bump) and the real root-cause fix (DuckDB `GROUP BY` pushdown) were
implemented in this escalation and are live/verified — see the Progress Log for the full sequence and evidence. The
originally-considered options ("author a dedicated plan, AO-dispatched vs human, for the DuckDB rewrite") are
superseded: the 32Gi-alone mitigation was confirmed insufficient (still OOM'd on defi), which removed any further
infra-only backstop to defer to, so the rewrite was done directly rather than left open.

## Progress Log

- 2026-08-15 (slot-31, escalation agt-8a1647): Root-caused via `gcloud run jobs executions describe`. Bumped
  `dp_daily_digest_job` to `cpu="8"/memory="32Gi"` in
  `deployment-service/terraform/gcp/data_pipeline_audit_scheduler.tf`, applied live
  (`ENV=prod ./tofu.sh apply -target=module.dp_daily_digest_job`, plan was `0/1/0`), confirmed via
  `gcloud run jobs describe` (`cpu: '8', memory: 32Gi`).

- 2026-08-15 (same session, continued): **32Gi alone was NOT sufficient** — manually re-executed the job
  (`gcloud run jobs execute uts-prod-dp-daily-digest --wait`) to verify the terraform fix; execution
  `uts-prod-dp-daily-digest-kzdnk` still OOM'd ("The configured memory limit was reached"). Cloud Logging for that
  execution shows `cefi` completed successfully at 04:46:05Z, then the container was `terminated on signal 9` at
  04:48:02Z while processing the NEXT asset group in `ASSET_GROUPS` order (`defi`) — confirming defi specifically has
  grown past even the 32Gi ceiling. Since 32Gi is Cloud Run gen2's hard memory ceiling (no further infra lever
  available), **implemented the DuckDB `GROUP BY`-pushdown rewrite in this same escalation** rather than leaving it
  deferred.
  - `e2e-testing@f27cf30748` (verified ancestor of `origin/live-defi-rollout`): added `_dp_common.ManifestDuckDB` +
    `open_manifest_duckdb()` (one GCS download, N `GROUP BY` queries against the same local file) and
    `schema_version_readiness_from_dist()` (kept in lockstep with the existing per-row `schema_version_readiness()` —
    parity proven by a dedicated unit test). Rewrote `data_pipeline_daily_digest.py::_digest_for_ag` to push the
    per-cell union-across-sources tally and the schema_version distribution into DuckDB SQL, so `.df()` only ever
    materialises the AGGREGATED result (bounded by distinct-cell-count, not row-count) — never the raw multi-million-row
    index. `read_manifest_index` and its other 2 callers (`manifest_hygiene_daily.py`, `reprobe_new_empty_confirmed.py`)
    are untouched. `quality-gates.sh` green (201 tests passed, sentinel-verified) before shipping.
  - `deployment-service@13c4d47595` (verified ancestor of `origin/live-defi-rollout`): the 32Gi terraform bump above.
  - Rebuilt the `e2e-audit:latest` runner image from clean LDR (both commits included) —
    `gcloud builds submit --config=cloudbuild-e2e-audit.yaml`, build `638f74cf-1088-42bd-b36f-fbedb15995d5` SUCCESS.
  - **Re-executed and confirmed live**: `gcloud run jobs execute uts-prod-dp-daily-digest --wait` → execution
    `uts-prod-dp-daily-digest-gbvnb` completed successfully in 2m55.7s. Logs show all 5 AGs completed, including the
    previously-fatal `defi` (99.4% complete over 3560 cells, ~1m43s), and a single unioned `DP_DAILY_DIGEST` event
    emitted. `Container called exit(0)`.
  - **Resolution**: both the immediate mitigation (32Gi) and the real root-cause fix (DuckDB pushdown) are live and
    verified. Marking this issue `resolved`.
