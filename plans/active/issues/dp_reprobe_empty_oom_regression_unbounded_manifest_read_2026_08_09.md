---
doc_type: issue
title:
  "uts-prod-dp-reprobe-empty Cloud Run Job has regressed to OOM-failing daily (16Gi/4cpu ceiling) since at least
  2026-08-07 — reprobe_new_empty_confirmed.py never got the columns= restriction daily_digest.py already shipped"
summary: >-
  Discovered while verifying the e2e-audit:latest rebuild (cross_cutting_satellite_ao_dispatch_batch9_2026_08_09.md todo
  2): the daily uts-prod-dp-reprobe-empty execution has failed with "The configured memory limit was reached" on every
  run 2026-08-07, 08-08, 08-09 (confirmed via gcloud run jobs executions list) plus a manual trigger run today
  (uts-prod-dp-reprobe-empty-r2gsn, same failure) — this is a REGRESSION from the 2026-08-05 state
  (cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md's own P3 entry: "All 4 dp-audit Cloud Run jobs run green
  daily at 16Gi/4cpu"). The job is still provisioned at the bumped cpu=4/memory=16Gi (confirmed live), so this is not
  the original 4Gi under-provisioning bug recurring — it's the SAME manifest-read memory antipattern
  (data_pipeline_self_healing_completion_residual_2026_07_24.md's already-diagnosed "reads the FULL per-AG _index with
  columns=None then count-EXPANDS into per-row Python lists") but on a DIFFERENT script:
  read_manifest_index()/read_availability_index() already gained a columns= restriction parameter for daily_digest.py's
  fix (e2e-testing@5d7f53a/edd12c6, ~11.8GiB peak RSS, safely under 16Gi), but reprobe_new_empty_confirmed.py's own
  read_manifest_index(ag, storage_client=storage_client) call at line 419 was never updated to pass it — still a full
  columns=None read. Since this OOM prevents reprobe from completing, its proof-gated empty_confirmed ->
  attempted_failed auto-heal (DP-FETCH-006, "LIVE in prod" per consolidator_throughput_backlog_monitor_2026_07_09.md)
  has not actually run to completion on any of the last 3+ days.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing]
scope: [engineer]
tags: [e2e-testing, data-pipeline, oom, memory-antipattern, reprobe, self-healing, cloud-run-jobs, regression]
related:
  [
    /plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md,
    /plans/archive/2026_07/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch9_2026_08_09.md,
    /plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md,
    e2e-testing/scripts/audit/reprobe_new_empty_confirmed.py,
    e2e-testing/scripts/audit/_dp_common.py,
  ]
created: "2026-08-09"
author: infra-worker-slot18
parent_epic: observability_master
resolved_by:
locked_by:
locked_since:
source: >-
  infra worker, slot 18, dispatched on cross_cutting_satellite_ao_dispatch_batch9_2026_08_09.md's e2e-audit:latest
  rebuild todo — discovered while manually triggering uts-prod-dp-reprobe-empty to verify the new image was picked up
  (which it was; the OOM is a pre-existing, unrelated, currently-active regression, not caused by the rebuild).
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
drift_direction: advance-code
depends_on: []
---

# uts-prod-dp-reprobe-empty OOM regression — reprobe never got the column-restriction fix daily_digest.py shipped

## What I found

Verifying `cross_cutting_satellite_ao_dispatch_batch9_2026_08_09.md`'s "Rebuild `e2e-audit:latest`" todo (done-when part
3: confirm the daily reprobe cron's next run picks up the new image), I checked recent `uts-prod-dp-reprobe-empty`
executions:

```
uts-prod-dp-reprobe-empty-v2hjb  2026-08-09T09:00  FAILED — "The configured memory limit was reached"
uts-prod-dp-reprobe-empty-lqllc  2026-08-08T09:00  FAILED — "The configured memory limit was reached"
uts-prod-dp-reprobe-empty-r8t5k  2026-08-07T09:00  FAILED — "The configured memory limit was reached"
```

Manually triggered a fresh execution to verify the new image
(`gcloud run jobs execute uts-prod-dp-reprobe-empty --region=asia-northeast1 --wait`) — it correctly resolved to the
freshly-pushed digest (`e2e-audit@sha256:0fc05321d5790b35875d1330424348abc0abc4be873b17a449b44b909458e3ce`, confirming
the image-rebuild todo's own done-when), but **still OOM-failed with the identical message** (execution
`uts-prod-dp-reprobe-empty-r2gsn`). The image rebuild is unrelated to this regression — both the old and new image share
the same unfixed script.

**Confirmed still provisioned at the bumped ceiling**
(`gcloud run jobs describe uts-prod-dp-reprobe-empty --region=asia-northeast1` → `cpu=4;memory=16Gi`), so this is NOT
the original 2026-06-22 under-provisioning bug recurring — the job has enough headroom per the 2026-07-26 fix and was
confirmed green as of 2026-08-05 (`cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md`'s own P3 entry: "All 4
dp-audit Cloud Run jobs run green daily at 16Gi/4cpu"). Something changed between 2026-08-05 and 2026-08-07 to push
reprobe's memory footprint back over 16Gi.

**Root cause located** — `e2e-testing/scripts/audit/reprobe_new_empty_confirmed.py:419`:

```python
df = read_manifest_index(ag, storage_client=storage_client)
```

`read_manifest_index()` (`_dp_common.py:155-159`) already supports a `columns: list[str] | None = None` parameter —
added specifically for `daily_digest.py`'s OOM fix (e2e-testing@5d7f53a/edd12c6, "restrict daily-digest manifest read to
needed columns", peak RSS dropped from OOM-killing at 4Gi to ~11.8GiB safely under 16Gi). **Reprobe's own call site was
never updated to pass it** — still a full `columns=None` read of the entire per-AG manifest index, the exact antipattern
`data_pipeline_self_healing_completion_residual_2026_07_24.md` diagnosed as "the actual OOM driver (16Gi is a
band-aid)". `_select_new_empties()` (the only consumer of `df`, line 186-211) only ever reads `capture_status`, one of
`_REASON_COLUMNS`, one of `_DATE_COLUMNS`, `venue`, `data_type`, `chain` — the same shape of minimal column set
`daily_digest.py`'s fix already restricts to.

This is plausible as the actual 2026-08-05→08-07 trigger: as the manifest index has grown (more captured shards across
more days), reprobe's unrestricted full-index read grew past the 16Gi ceiling exactly the way `daily_digest.py`'s did
before its own fix — reprobe was simply smaller and slower to hit the wall.

## Why it matters

Reprobe's proof-gated `empty_confirmed → attempted_failed` auto-heal (DP-FETCH-006, described as "LIVE in prod" in
`consolidator_throughput_backlog_monitor_2026_07_09.md`) has not run to completion on any of the last 3+ days — the
self-healing mechanism this whole `observability_master` epic exists to keep running is silently not running. Per
CLAUDE.md's data-pipeline-correctness HARD RULE, a broken self-healing/audit job is exactly the class of finding that
should not sit un-triaged.

## Recommended decision

Mechanical, bounded fix — mirror the already-proven `daily_digest.py` pattern:

1. Pass an explicit `columns=` list to `read_manifest_index()` at `reprobe_new_empty_confirmed.py:419` — the minimal set
   `_select_new_empties()` actually reads (`capture_status`, `_REASON_COLUMNS`, `_DATE_COLUMNS`, `venue`, `data_type`,
   `chain`; check `_crosscheck()` at line 429 for any additional columns it needs from the same `df` before finalizing
   the list).
2. Verify locally (measure peak RSS on a real per-AG index, same methodology as the digest fix) before shipping.
3. Re-run `uts-prod-dp-reprobe-empty` (manual trigger, same as this issue's own verification) to confirm it completes
   without OOM.
4. Consider whether the OTHER 2 dp-audit jobs (`dp-manifest-hygiene-changed`, `dp-manifest-hygiene-full`) have the same
   gap — not checked this session (outside this todo's scope), flagging as a possible sibling issue.

## Todos

- [ ] [CODE] P1. Add an explicit `columns=` restriction to `reprobe_new_empty_confirmed.py`'s `read_manifest_index()`
      call (line 419) mirroring `daily_digest.py`'s already-shipped fix (e2e-testing@5d7f53a/edd12c6). Verify peak RSS
      drops safely under the 16Gi ceiling on a real per-AG index, then manually trigger `uts-prod-dp-reprobe-empty` to
      confirm a completed (non-OOM) execution. Repo: e2e-testing.
- [ ] [INFRA] P2. Check whether `uts-prod-dp-manifest-hygiene-changed` and `uts-prod-dp-manifest-hygiene-full` have the
      same unrestricted-columns gap in their own manifest-read call sites — not checked this session. Repo: e2e-testing.

## Progress Log

- **2026-08-09 (infra worker, slot 18)**: Filed while verifying the e2e-audit:latest rebuild's done-when. Confirmed the
  OOM is pre-existing (3 consecutive prior days) and unrelated to the rebuild (both old and new image share the same
  unfixed script); confirmed the job is provisioned at the already-bumped 16Gi/4cpu ceiling, so this is a fresh
  regression, not the original under-provisioning bug; root-caused to a specific, unfixed call site via direct code
  read, cross-referenced against the already-proven sibling fix in daily_digest.py. Not fixing inline — outside this
  session's assigned todo (image rebuild, INFRA craft) and this fix needs its own measurement + test cycle (CODE craft).
