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
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch9_2026_08_09.md,
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

- [x] ✅ [CODE] P1. **DONE (code) 2026-08-09 (slot 15) — columns= restriction shipped, but this ALONE does NOT clear the
      OOM; see the follow-up todo below.** Added an explicit `columns=` restriction to
      `reprobe_new_empty_confirmed.py`'s `read_manifest_index()` call (line 419), mirroring `daily_digest.py`'s
      already-shipped fix (e2e-testing@5d7f53a/edd12c6) —
      `_MANIFEST_COLUMNS = [capture_status, venue, data_type,     chain, *_REASON_COLUMNS, *_DATE_COLUMNS]`, the exact
      minimal set `_select_new_empties()` (the only consumer of the returned `df`) reads. Unit test added asserting the
      call is made with this restricted set, not `columns=None` (mirrors `test_digest_requests_column_restricted_read`).
      QG green, shipped e2e-testing@507717c. **Verified via BOTH a local bounded reproduction AND a live manual trigger
      that the fix, while correct and necessary, is NOT SUFFICIENT — the real `defi` manifest has grown to 2.79GiB
      compressed (vs the ~130MB figure cited when daily_digest.py's own fix was validated 8 days ago), and even the
      column-restricted read now exceeds the 16Gi ceiling.** Full evidence in the Progress Log below. Repo: e2e-testing.
- [x] ✅ [INFRA] P1. **DONE (mechanical bump shipped + applied + verified live) 2026-08-09 (slot 13) — CONFIRMED
      INSUFFICIENT: even Cloud Run's platform ceiling (32Gi/8vCPU — no larger instance exists, per
      `manifest-consolidator-ssot.md` line 778) does not clear the OOM.** Bumped `dp_reprobe_empty_job` from
      `cpu="4"     memory="16Gi"` to `cpu="8" memory="32Gi"` in
      `deployment-service/terraform/gcp/data_pipeline_audit_scheduler.tf:280-281` (NOTE: `cpu=4`/`memory=32Gi` is
      REJECTED by the Cloud Run API — "For 4.0 CPU, memory must be between 2Gi and 16Gi inclusive" — the todo's original
      "cpu=4 up to memory=32Gi" claim was wrong; 32Gi requires cpu=8, confirmed against every other `memory="32Gi"` job
      in this repo's terraform, which all already pair it with `cpu="8"`). Applied via `tofu apply -target` (this repo
      uses OpenTofu, not HashiCorp Terraform — running the wrong `terraform` binary silently rewrote
      `.terraform.lock.hcl` to the `registry.terraform.io` namespace; reverted before shipping), verified live via
      `gcloud run jobs describe` (`cpu: '8', memory: 32Gi`). **Manually re-triggered (`uts-prod-dp-reprobe-empty-xrxzx`)
      — STILL OOM-failed**
      (`"Task ...-task0 failed with exit code: 0 and message:     The configured memory limit was reached."`,
      `Container terminated on signal 9` at 19:13:51Z). Timeline: started 19:11:53Z, `cefi` cleared at 19:13:00 (0 new
      empties, ~67s in), OOM-killed ~51s into `defi` at 19:13:51 — i.e. doubling RAM 16Gi→32Gi bought the run
      essentially ZERO extra runway before the kill (same "cefi ok, dies early into defi" shape as the 16Gi run). This
      is strong evidence the read is not just large but effectively unbounded in this process (consistent with the
      diagnosed antipattern: full-blob download + count-EXPANDS into per-row Python lists) — a bigger ceiling was never
      going to hold. **The mechanical-bump path is now exhausted: 32Gi/8vCPU is Cloud Run's actual maximum, confirmed
      both by this rejection and by every other job in the codebase topping out there.** The CODE P2 structural fix
      below is no longer a hedge against "if 32Gi isn't enough" — that condition is now live and confirmed; escalated
      its priority to P1 accordingly. Repo: deployment-service.
- [ ] [CODE] P1 _(escalated from P2 2026-08-09 — the memory-ceiling path is now confirmed exhausted, not hypothetical;
      see the INFRA P1 entry above)_. **NEW, filed 2026-08-09 (slot 15) — the only remaining fix: read via
      row-group/column pushdown instead of downloading the full blob.** The root cause underneath both this doc and
      `daily_digest.py`'s original fix is the same: `_dp_common.read_manifest_index()` downloads the ENTIRE compressed
      parquet blob into memory (`client.download_bytes(...)`) before doing a column-restricted decode — the column
      restriction only bounds the DECODE step, not the download/buffer-retention step, so as the underlying manifest
      grows without bound, every caller's memory floor grows with it regardless of how few columns each caller actually
      needs. A genuinely durable fix would read via row-group/column pushdown directly against GCS (DuckDB's
      `read_parquet` over an `httpfs`/GCS URL, or a range-read of only the needed row-groups) instead of materializing
      the full compressed file — the same DuckDB-over-pandas precedent already used elsewhere per
      `/codex/05-infrastructure/manifest-consolidator-ssot.md`. DP-FETCH-006's self-healing reclassify is NOT running to
      completion on `defi` (and likely `tradfi`/`sports`/`prediction`, not yet reached in any run) until this lands —
      the 32Gi/8vCPU ceiling bump is not a viable stopgap (see evidence above: it bought ~0 extra runway). Repo:
      e2e-testing.
- [ ] [INFRA] P3. Check whether `uts-prod-dp-manifest-hygiene-changed` and `uts-prod-dp-manifest-hygiene-full` have the
      same unrestricted-columns gap in their own manifest-read call sites — not checked this session. Repo: e2e-testing.

## Progress Log

- **2026-08-09 (infra worker, slot 18)**: Filed while verifying the e2e-audit:latest rebuild's done-when. Confirmed the
  OOM is pre-existing (3 consecutive prior days) and unrelated to the rebuild (both old and new image share the same
  unfixed script); confirmed the job is provisioned at the already-bumped 16Gi/4cpu ceiling, so this is a fresh
  regression, not the original under-provisioning bug; root-caused to a specific, unfixed call site via direct code
  read, cross-referenced against the already-proven sibling fix in daily_digest.py. Not fixing inline — outside this
  session's assigned todo (image rebuild, INFRA craft) and this fix needs its own measurement + test cycle (CODE craft).
- **2026-08-09T18:36Z-19:00Z (slot 15, data_engineering, task `-95d84d2e8008`): shipped the columns= fix exactly as
  scoped, then discovered via real measurement that it alone does not clear the OOM — manifest growth outpaced the
  fix.** Sequence:
  1. **Code fix**: added `_MANIFEST_COLUMNS` (the minimal set `_select_new_empties()` reads) and passed it to the
     `read_manifest_index()` call at line 419, mirroring `daily_digest.py`'s proven pattern exactly. Added a unit test
     (`test_reprobe_requests_column_restricted_read`) asserting the restricted columns list is what's actually
     requested, not `None`. QG green (`quality-gates.sh` full pass). Shipped via quickmerge:
     `e2e-testing@507717c63c746ef77bd029d5b752817a9f2c9e99`, verified ancestor-of-origin.
  2. **Local RSS verification (per the todo's own step 2), bounded via `run-bounded-analysis.sh`'s RSS-poll fallback (no
     systemd-run on this host)**: a real read of `defi`'s manifest index (the largest AG) with the new
     `_MANIFEST_COLUMNS` restriction — first run capped at 16G, KILLED after exceeding cap
     (`RSS 16807108K exceeded cap 16777216K`, ~16.03GiB and still rising, not yet plateaued); second run capped at 20G,
     still climbing (~15.7GB at the 49s mark, RSS% 50.9 of host) before the harness's own 5-minute tool timeout cut it
     off (exit 143 / SIGTERM, not the cap watchdog — confirmed via `ps`, not a `run-bounded-analysis.sh` kill message).
     Both runs are consistent: the column-restricted read genuinely needs MORE than 16GiB for `defi` today.
  3. **Root cause of the growth**: checked the REAL bucket `read_manifest_index()` actually resolves to for defi via
     `resolve_bucket_name(kind="market-data", asset_group="defi")` — `market-data-tick-defi-prd-central-element-323112`
     (NOT `instruments-store-defi-prd-...`, an easy wrong-bucket trap). `gcloud storage du --readable-sizes` on its
     `_index/availability_index.parquet`: **2.79GiB compressed** — vs. the `~130MB` figure `daily_digest.py`'s own fix
     comment cites from its 2026-08-01 validation, roughly a **20x** growth in 8 days. This is a genuine, organic
     manifest-growth problem, not a fix-design flaw: `read_manifest_index()` downloads the FULL compressed blob into
     memory (`client.download_bytes`) before doing any column-restricted decode, so the download/buffer-retention floor
     scales with total manifest size regardless of how few columns a caller requests — see the new P2 structural todo
     above.
  4. **Live authoritative check (per the todo's own step 3)**: manually triggered a fresh execution,
     `uts-prod-dp-reprobe-empty-sztdh` (confirmed running the just-shipped fix — the image digest is unchanged since the
     2026-08-07 rebuild, and the fix landed in the SAME image via the script source, not a rebuild). `cefi` processed
     cleanly (`0 new SOURCE_RETURNED_ZERO empties`, logged at 18:54:24Z, ~40s after boot — confirms the fix works
     correctly for a small AG). Then went silent (matches the local repro's silent-during-read behavior) and **the
     execution reached a definitive terminal FAILURE at 18:55:16Z**: `status.conditions[type=Completed, status=False]`,
     message
     `"Task uts-prod-dp-reprobe-empty-sztdh-task0 failed with exit code: 0 and message: The configured memory limit was reached."`
     — the IDENTICAL failure this whole issue doc is about, still happening with the fix live, ~2 minutes into the
     `defi` AG (the second of 5 in `ASSET_GROUPS` order). (Note: a `--format value(status.conditions[0].type,...)` query
     kept returning a stale-looking "Waiting for execution to complete" — `gcloud`'s condition-list ordering isn't
     stable; use `--format=json` and read `status.completionTime` + `failedCount` for an authoritative terminal check,
     not `conditions[0]` positionally.)
  5. **Verdict**: the columns= fix is real, correct, necessary progress (mirrors the proven pattern exactly as scoped,
     ships a genuine memory reduction vs. the prior fully-unrestricted read, and unblocks `cefi` at minimum) — but is
     **NOT sufficient alone** to clear this OOM anymore, because the underlying `defi` manifest has outgrown the 16Gi
     ceiling even with column restriction. Flipping the P1 checkbox to reflect the code work shipped (todo's own
     `[CODE]` scope is done), but the OOM itself is NOT resolved — filed two new follow-up todos: `[INFRA] P1` (the
     fast, mechanical fix — bump the Cloud Run memory ceiling, same remediation class as the 2026-07-26 4Gi→16Gi bump)
     and `[CODE] P2` (the structural fix if the ceiling bump proves to be a recurring treadmill — read via
     row-group/column pushdown instead of downloading the full blob). DP-FETCH-006's self-healing reclassify is still
     NOT running to completion on `defi`/`tradfi`/`sports`/`prediction` (whichever haven't been reached yet — `cefi`
     confirmed OK) until one of those lands.
- **2026-08-09T~19:05Z-19:15Z (slot 13, infra, task
  `dp_reprobe_empty_oom_regression_unbounded_manifest_read-78a38cba365a`): shipped + applied the INFRA P1 ceiling bump,
  live-verified it does NOT clear the OOM — the mechanical path is exhausted.**
  1. **Corrected the todo's own premise**: `cpu=4`/`memory=32Gi` is REJECTED by the Cloud Run API
     (`"For 4.0 CPU, memory must be between 2Gi and 16Gi inclusive"`) — 32Gi requires `cpu=8`. Confirmed against every
     other `memory="32Gi"` job already in this repo's terraform (`cf_manifest_audit_scheduler.tf`,
     `data_pipeline_fleet_monitor_scheduler.tf`, `mdps_odds_horizon_scheduler.tf`,
     `sports_enrichment_provider_scheduler.tf`) — all pair it with `cpu="8"`, none go higher; codex
     (`manifest-consolidator-ssot.md:778`) independently confirms "hard ceiling of 32 Gi RAM / 8 vCPU — there is no
     larger instance" for this Cloud Run job class.
  2. **Tooling gotcha**: this repo's terraform is OpenTofu (lock file header: "maintained automatically by tofu init"),
     not HashiCorp Terraform — the host has both binaries (`/home/ubuntu/.local/bin/tofu` vs `/usr/local/bin/terraform`)
     and running plain `terraform init` silently rewrote `.terraform.lock.hcl` to the `registry.terraform.io` provider
     namespace (vs the repo's `registry.opentofu.org`) plus bumped `hashicorp/google` 7.37.0→7.43.0 — reverted
     (`git checkout --`) before shipping anything. Used `tofu` for all subsequent init/plan/apply.
  3. **Applied**: `cpu="4" memory="16Gi"` → `cpu="8" memory="32Gi"` at
     `deployment-service/terraform/gcp/data_pipeline_audit_scheduler.tf:280-281`, via
     `tofu apply -target=module.dp_reprobe_empty_job` (scoped plan showed exactly the intended 1-resource diff, nothing
     else). Live-verified via `gcloud run jobs describe --format="yaml(...resources)"` → `cpu: '8', memory: 32Gi`.
     Shipped deployment-service (terraform-only change; quickmerge Pass-1/Pass-2 — see /done evidence for SHA).
  4. **Manually re-triggered** (`gcloud run jobs execute uts-prod-dp-reprobe-empty --wait` →
     `uts-prod-dp-reprobe-empty-xrxzx`) to test the todo's own done-when (non-OOM completion across all 5 AGs). **STILL
     OOM-failed**: `status.conditions[type=Completed,status=False]` message
     `"Task uts-prod-dp-reprobe-empty-xrxzx-task0 failed with exit code: 0 and message: The configured memory limit was reached."`,
     log line `Container terminated on signal 9` at 19:13:51Z. Execution timeline from logs: started 19:11:53Z, `cefi`
     cleared cleanly at 19:13:00 (`0 new SOURCE_RETURNED_ZERO empties`, ~67s in), OOM-killed ~51s into `defi` at
     19:13:51 — **doubling RAM 16Gi→32Gi bought essentially zero extra runway** before the kill (same "cefi-ok,
     dies-early-into-defi" shape as the pre-bump 16Gi run reported in the entry above). This is live evidence the read
     is not merely large but effectively unbounded in-process for this manifest size, consistent with the
     originally-diagnosed antipattern (full-blob download + count-EXPANDS into per-row Python lists) — a bigger ceiling
     alone was never going to hold, and 32Gi/8vCPU is the actual platform max, so there is no bigger ceiling left to
     try.
  5. **Verdict**: flipped INFRA P1 to done (the mechanical bump was correctly shipped and IS a real, live, verified
     terraform change) but the underlying OOM is still NOT resolved. Escalated `[CODE] P2` (the
     row-group/column-pushdown structural fix) to **P1** — the "if 32Gi still isn't enough" condition it was filed as a
     hedge against is now confirmed live, not hypothetical, and there is no further mechanical lever (ceiling bump) left
     to pull. DP-FETCH-006 self-healing remains broken on `defi` (and un-reached AGs `tradfi`/`sports`/`prediction`)
     until the CODE P1 lands.
