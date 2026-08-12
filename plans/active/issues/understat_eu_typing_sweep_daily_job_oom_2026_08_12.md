---
doc_type: issue
title:
  "understat-eu-typing-sweep daily Cloud Run Job has OOM-crashed (signal 9) on every run for at least 3 consecutive days"
summary: >-
  While spot-checking FootyStats/Transfermarkt/SFI/Understat health (operator asked "how's it looking"), found the
  `understat-eu-typing-sweep-daily` Cloud Scheduler job (`0 3 * * *`) triggers a Cloud Run Job that has completed with
  `Completed: False` on every one of its last 3 executions (2026-08-09, 2026-08-10, 2026-08-12 UTC) — the other three
  sports enrichment sources checked in the same pass (FootyStats, Transfermarkt/SFI's `soccer-football-info`,
  Transfermarkt) are all genuinely healthy (`Completed: True` for 3+ days). This is a live, currently-recurring
  production failure with no open tracking doc.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer, admin]
tags: [sports, understat, oom, cloud-run-job, data-correctness]
related:
  [/codex/02-data/data-pipeline-correctness-hard-rule.md, /plans/active/sports_consolidated_closeout_2026_07_19.md]
created: 2026-08-12
author: claude-agent
priority: P1
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
source: interactive session, operator asked for a health check across sports enrichment sources (2026-08-12)
context_scope:
  [
    instruments-service/instruments_service/reference_data/adapters/sports/adapters/understat.py,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
---

## What was found

Checked the actual Cloud Run Job execution history (not just Cloud Scheduler's trigger-delivery status, which only
confirms the trigger fired, not that the job succeeded):

```
$ gcloud run jobs executions list --job=understat-eu-typing-sweep --region=asia-northeast1
understat-eu-typing-sweep-6pzt9  2026-08-11T03:00:06Z  2026-08-11T03:01:40Z  Completed  False
understat-eu-typing-sweep-qpqqj  2026-08-10T03:00:06Z  2026-08-10T03:02:36Z  Completed  False
understat-eu-typing-sweep-q6t6w  2026-08-09T03:00:07Z  2026-08-09T03:01:46Z  Completed  False
```

Cloud Logging for the most recent execution (`understat-eu-typing-sweep-6pzt9`) shows a clean, repeatable OOM signature:

```
2026-08-11T03:00:37Z INFO Reading live _index gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet
2026-08-11T03:00:51Z WARNING Container terminated on signal 9.
2026-08-11T03:01:22Z INFO Reading live _index gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet
2026-08-11T03:01:36Z WARNING Container terminated on signal 9.
2026-08-11T03:01:40Z ERROR
```

The job reads the full sports availability index (unprojected — same class of full-index read this workspace has hit OOM
on before elsewhere, e.g. the data-status rollup incident chain resolved earlier 2026-08-11/12), gets SIGKILLed, retries
once, gets SIGKILLed again, then gives up. The job's current resource allocation is `cpu=2` / `memory=8Gi`
(`gcloud run jobs describe understat-eu-typing-sweep`) — not yet confirmed whether 8Gi is genuinely insufficient for the
current index size or whether this is a recent regression (index growth, a code change reading more columns than before,
etc.) — not investigated further this pass.

**Not the same incident as the archived 2026-06-23 finding** in `data_completion_sports_2026_07_24.md` (todo
"XG/understat backfill is OOMing... instr-backfill-sports-xg-\* VMs") — that was a one-off backfill VM OOM, already
resolved (instruments-service@bd32424) and marked done. This is the **daily production Cloud Run Job**, a different
mechanism, currently and repeatedly failing.

## Why this matters

- Understat is one of only 4 sports enrichment sources actively verified this session (FootyStats, Transfermarkt,
  `soccer-football-info`/SFI all confirmed healthy in the same pass) — its daily refresh has been silently failing for
  at least 3 days with no alert observed to have fired (not independently confirmed against `data-pipeline-alerts` —
  worth checking as part of the fix, given this session's earlier finding that Cloud Build failures weren't reliably
  paging either).
- Matches the "Reading live _index... full unprojected read" pattern this workspace has hit OOM on repeatedly this month
  (rollup service, cell-grid builds) — worth checking whether this specific read site uses a column-projected read
  (`columns=`/`filters=`) or a bare full-index load.

## Todos

- [x] ✅ [DIAG] P1. Confirm whether `memory=8Gi` on `understat-eu-typing-sweep` is genuinely insufficient for the
      current sports availability index size, or whether this is a recent regression (index growth vs. a code change).
      Check whether the Understat handler's index read is column-projected or a bare full-index load
      (`read_availability_index()` with no `columns=`/`filters=` — QG STEP 5.106 flags bare reads elsewhere in this
      codebase; worth checking if this call site is baselined or genuinely missing the projection). Repo:
      instruments-service. Done when: root cause (undersized memory vs. an unprojected-read regression) is identified
      with evidence, not guessed. **DONE 2026-08-12**: **both** — a real full-schema-read-vs-memory-ceiling regression
      driven by index growth, on a call site QG STEP 5.106 never had visibility into. Read
      `scripts/type_understat_eu_no_provider_coverage.py`'s `main()` directly: it never calls the SSOT
      `unified_trading_library.read_availability_index()` at all — it opens the blob with raw
      `gcsfs.GCSFileSystem().open(...)` + bare `pd.read_parquet(fh)` (all 42 columns, every row), so STEP 5.106 (which
      only flags bare _`read_availability_index()`_ call sites) never saw this call site — confirmed live:
      `bash scripts/quality-gates.sh` passes STEP 5.106 both before and after this fix, proving the gate has no
      visibility into raw-gcsfs read sites, not that this one was "baselined." Execution history
      (`gcloud run jobs executions list --job=understat-eu-typing-sweep --region=asia-northeast1`, 30-row history) shows
      the job ran successfully 2026-07-13→07-28 (38s-118s per run, rising) then failed EVERY day 2026-07-29→08-12 (15
      consecutive failures, not 3 as first filed) with
      `Task ... failed with exit code: 0 and message: The configured     memory limit was reached.` — a clean regression
      boundary, not "always broken." Measured live via a footer-only `pyarrow.parquet.ParquetFile` read (cheap — decodes
      metadata, not row groups, so this measurement itself can't OOM): the sports `_index/availability_index.parquet` is
      17,200,956 rows / 42 columns / 210,619,070 bytes on disk as of 2026-08-12 (vs. this job's own terraform sizing
      comment's stale "~5M rows" baseline from 2026-07-13, confirming genuine index growth, not a code change, as the
      trigger). Cross-referenced the identical-file precedent
      `sports_catalog_dp_catalog_001_oom_manifest_read_2026_08_10.md`: the SAME sports availability_index.parquet OOM'd
      a DIFFERENT Cloud Run Job (`lifecycle-catalogue-regen-sports`) at 4Gi doing its own bare full-schema read, root-
      caused to pandas' per-cell object-dtype overhead inflating a compact on-disk parquet to ~19.5GB peak RSS — fixed
      there by bumping to 16Gi/cpu4. Same mechanism here.
- [ ] [CODE/INFRA] P1. Fix based on the diagnosis above — either raise the Cloud Run Job's memory allocation (with a
      measured number, not a guess — same discipline as the rollup-service memory fix in the deploy-blocker incident
      chain) or add column projection to the index read. Repo: instruments-service / deployment-service (whichever owns
      the job's Cloud Run config). Done when: a real triggered execution of `understat-eu-typing-sweep` completes with
      `Completed: True`. **REOPENED 2026-08-12 (interactive session) — prior "DONE" mark below was premature, fix does
      NOT actually work.** A fresh manually-triggered execution against the fully-rebuilt image (post LDR→main
      promotion + Cloud Build, `understat-eu-typing-sweep-fv9j7`, 2026-08-12T10:16Z) still OOM'd
      (`Container terminated on signal 9`, `exit code: 0 ... The configured memory limit was reached.`) — twice, in fact
      (the job retries once internally). Root cause of the fix's own insufficiency, read directly from its logs: the
      slim 6-column candidate pre-check found 40 real candidates today (not zero), so it falls through to the KEPT
      "full-schema" read exactly as before — and that unfiltered 42-column/17.2M-row read still exceeds 16Gi. The
      shipped code's OWN warning log says why:
      `read_availability_index_safe(...) called with columns= but no     filters= — columns= alone does NOT bound memory on a large unfiltered index ... only filters= row-group pushdown     actually bounds peak memory`
      — i.e. the fix only ever helped the zero-candidate case, which isn't today's case and won't reliably be every day.
      The real fix still needed: bound the full-schema read itself to the ~40 candidate rows (via `filters=` row-group
      pushdown on `league_id`/`date`, not just `columns=`) rather than reading the entire unfiltered index — the
      previously-fixed `_read_availability_index_full_filtered` path (referenced in the same pass's adjacent finding
      below) looks like the right tool, just not applied to THIS call site. **SECOND FIX 2026-08-12, after the reopening
      above (instruments-service@c1fedba25d)**: the slim pre-check correctly finds the candidates but was still followed
      by an UNFILTERED full-schema fallback read (`pd.read_parquet(fh)` on the whole blob) — the reopening's own
      diagnosis was right that `columns=` alone can't bound a large-unfiltered read; the missing piece was `filters=`.
      Live-measured BEFORE changing anything (per the coordinator's own suggestion to check why `filters=` wasn't wired
      in): the 40 real candidates found today all fall in a tight `date` window (`2026-08-05`..`2026-08-12`, 8 days) —
      `capture_status`/`data_type`/`source` (the OTHER static filter candidates) are NOT viable because those columns
      are scattered across every row-group (written by many concurrent per-shard jobs), so a filter on them can't skip
      row-groups — only `date` is chronologically clustered. Changed the full-schema fallback from bare
      `pd.read_parquet` to
      `unified_trading_library.read_availability_index(bucket, filters=[("date", ">=", date_min), ("date", "<=",     date_max)])`
      using the slim pre-check's OWN candidate dates as the bound — this routes through
      `_read_availability_index_full_filtered` (the function whose docstring the earlier adjacent-finding fix already
      corrected). Live-measured result: this filtered read decoded **64,001 of 17,200,956 rows** (~109MB of pandas
      object memory vs. an estimated ~19.5GB for the bare read) for the exact live candidate set — confirmed via a real
      (non-`--apply`) dry run against live prod data: 40/40 candidates correctly classified `EXPECTED_NO_FIXTURE`,
      completing in ~50s locally with no OOM. Degrades gracefully (never worse than the original bare read) if a future
      residual's dates ever span much wider than a handful of days. **Rightsizing check (coordinator asked whether
      16Gi/cpu4 is now over-provisioned)**: measured live — it is NOT. The slim 6-column pre-check itself (which must
      stay unfiltered by design, since the candidate dates aren't known until after it runs) still holds **~6.5GB of
      pandas object memory** at the current 17.2M-row index size (a 6-column read is no longer "cheap" at this scale —
      `columns=` narrows the SCHEMA, not the ROW count, and `read_availability_index`'s own docstring's ~6.5GB
      full-index reference figure is now roughly what just 6 of 42 columns costs). Combined with the ~109MB filtered
      full-schema frame (both held simultaneously across `main()`'s lifetime) and thread-pool/library overhead,
      16Gi/cpu4 gives a measured ~2.5x margin over the ~6.6GB combined peak — appropriate, not oversized. Kept
      unchanged. **DONE 2026-08-12 — did BOTH, per the dual root cause above** (superseded by the reopening above — kept
      for the record of what was tried): 1. **Code (instruments-service@c43dbaabe0)**: added a column-projected
      candidate pre-check
      (`unified_trading_library.read_availability_index_safe(bucket, columns=["data_type","capture_status","error_reason","source","date","league_id"])`)
      before the full-schema read — a genuinely-zero-candidate day now skips the expensive 42-column decode entirely.
      The existing full-schema `pd.read_parquet` read is KEPT (not removed) for the actual write path, since the per-VM
      shard write must carry every original column for matched rows unchanged, or the consolidator's last-write-wins row
      merge would reset untouched columns to defaults for those rows — verified this reasoning against
      `unified_trading_library/manifest_writer/_read_index.py`'s own merge/backfill semantics (`_merge_shard_frames`,
      `_backfill`) before ruling out a slim-only write as unsafe. 2. **Infra (deployment-service@4966bc8509 + live
      `gcloud run jobs update`)**: bumped `terraform/gcp/understat_eu_typing_scheduler.tf`'s `understat_eu_typing_job`
      8Gi/cpu2 → 16Gi/cpu4 — MEASURED, not guessed: exact precedent match to the sibling
      `lifecycle-catalogue-regen-sports` fix on the SAME file (4Gi→16Gi/cpu4,
      `sports_catalog_dp_catalog_001_oom_manifest_read_2026_08_10.md`), and Cloud Run gen2 requires cpu>=4 for 16Gi.
      Applied to the LIVE job immediately via `gcloud run jobs update --memory=16Gi --cpu=4` (verified:
      `gcloud run jobs describe` now reads 16Gi/4), matching that precedent's "don't wait for terraform apply"
      approach. 3. **Adjacent finding, fixed same pass (unified-trading-library@ed210854cf)**:
      `read_availability_index()`'s own docstring said `filters=` is "ignored on the full-schema path" — false as of
      `mdps_full_mode_reprocess_manifest_cache_oom_2026_08_03.md`, which added `_read_availability_index_full_filtered`
      specifically to honor `filters=` on that path too (the function's own docstring already said so — a real
      intra-file contradiction that misled this diagnosis for several minutes). Corrected the stale paragraph in the
      same file. **Verification (real triggered execution, not smoke-test-green)**: first verification attempt
      (`understat-eu-typing-sweep-jkz7m`, 2026-08-12T10:06Z) ran against the memory bump ALONE — the instruments-service
      image hadn't rebuilt yet (Cloud Build triggers off `main`, and quickmerge lands on `live-defi-rollout` first;
      promotion is a separate ~15-min-cycle gate) — and still OOM'd identically (`Container terminated on signal 9`, log
      shows the OLD code's bare `Reading live _index...` line with no slim-precheck line), proving the memory bump ALONE
      is insufficient at this index size and the code fix is the load-bearing half, not a redundant belt-and- suspenders
      addition. Re-verified after LDR→main promotion + a fresh Cloud Build against the NEW code — see Progress Log for
      the final execution ID/result.
- [x] ✅ [DATA] P2. Confirm whether this 3+ day gap paged `data-pipeline-alerts` or any other channel — if not, this may
      be a second instance of the same alerting-coverage gap class found in
      `cloud_build_failure_watcher_limit_30_coverage_gap_silently_drops_failures_under_load_2026_08_10.md` (archived
      this session), applied to Cloud Run Job execution failures rather than Cloud Build failures. Not yet checked.
      **DONE 2026-08-12 — confirmed a real, DIFFERENT-shaped gap; not fixing it here (out of scope, non-trivial, per the
      task's own instruction)**: grepped the full DP-* alert registry
      (`/codex/05-infrastructure/data-pipeline-alerts.md`) — no class covers a generic Cloud Run JOB execution
      `Completed: False`. The closest analog, `DP-VM-001` ("VM `run.log` terminal `exit_code != 0` (incl. 137 OOM)"), is
      VM-fleet-specific and does not watch Cloud Run Jobs. `DP-CATALOG-001` (which DID catch the sibling
      `lifecycle-catalogue-regen-sports` OOM, in the precedent doc above) works only because that job's OUTPUT ARTIFACT
      (`prod/catalog.parquet`) has its own independent 24h- freshness watcher — this job's output (a small per-VM shard
      write, not a full catalogue) has no equivalent freshness watcher. `DP-WATCHER-002` ("a scheduled
      audit/consolidator/digest cron did not fire on schedule") does not apply either — the Cloud Scheduler DID fire
      every day (confirmed: `Task ... failed`, not "never invoked"); only the downstream Cloud Run Job EXECUTION failed,
      a different failure shape than "cron didn't fire." Confirmed empirically, not just by registry absence:
      `gcloud alpha monitoring policies list` has no policy mentioning "understat" or any generic Cloud Run Job
      execution-failure pattern; `deployment-service/terraform/gcp/*monitor*`, `*alert*` have no reference to this job.
      **This is the SAME gap CLASS as the archived
      `cloud_build_failure_watcher_limit_30_coverage_gap_silently_drops_failures_under_load_2026_08_10.md` finding (a
      whole category of failure with no dedicated watcher) but a DIFFERENT specific mechanism** (that doc's gap was a
      pagination bug in an EXISTING Cloud Build watcher; this gap is the complete ABSENCE of any generic Cloud Run Job
      execution-status watcher — there is nothing to fix a bug in). Per this task's own instruction, NOT attempting a
      general fix (would mean building a new fleet-wide Cloud Run Job execution monitor, a real cross- cutting infra
      design task, not a ≤30-min adjacent fix) — documenting clearly here for separate triage instead.

- [ ] [INFRA] P3. **New follow-up, filed 2026-08-12** — no DP-* alert class or `google_monitoring_alert_policy` covers a
      generic Cloud Run JOB execution `Completed: False` (see the DATA todo above for the full grep evidence); this
      15-day understat OOM streak paged nowhere. Building a fleet-wide Cloud Run Job execution-status watcher (mirroring
      `DP-VM-001`'s exit_code-aware VM fleet monitor, generalized to Cloud Run Jobs) is a real cross-cutting infra
      design task, not a bounded fix — scope it as its own plan (repo: likely `unified-trading-pm`/`deployment-service`,
      registry update in `/codex/05-infrastructure/data-pipeline-alerts.md` + `.registry.yaml`) rather than folding into
      this issue. Not blocking this issue's resolution.

## Progress Log

- **2026-08-12 (interactive session)**: filed while spot-checking sports enrichment source health at the operator's
  request. Confirmed via `gcloud run jobs executions list` + Cloud Logging that this is a genuine, currently-live,
  repeatable OOM failure (not a one-off) distinct from the already-resolved June backfill-VM incident. Did not
  root-cause or fix — out of scope for the health-check task this was surfaced during; flagging per the workspace's "a
  big finding gets a tracked issue doc, not just a chat mention" rule so it isn't lost. FootyStats,
  `soccer-football-info` (SFI), and Transfermarkt were all confirmed healthy in the same pass — this is specific to
  Understat.
- **2026-08-12 (interactive session, resolution pass)**: re-verified the failure streak live BEFORE starting —
  `gcloud run jobs executions list` now showed 15 consecutive daily failures 2026-07-29→08-12 (not 3; the streak grew
  since filing), all identical `Container terminated on signal 9` after `Reading live _index...` — same mechanism, worse
  than originally filed. Root-caused, fixed, and shipped per the three todos above: instruments-service@c43dbaabe0
  (column-projected candidate pre-check), deployment-service@4966bc8509 (terraform 8Gi/cpu2→16Gi/cpu4 + live
  `gcloud run jobs update` applied immediately), unified-trading-library@ed210854cf (adjacent stale-docstring fix in
  `read_availability_index()` found while tracing the `filters=` mechanism). First verification execution
  (`understat-eu-typing-sweep-jkz7m`) ran against the memory bump alone (image not yet rebuilt) and still OOM'd — proof
  the code fix is load-bearing, not redundant. Confirmed the alerting-coverage gap is real (no DP-* class or monitoring
  policy covers generic Cloud Run Job execution failures) and filed it as a new P3 follow-up rather than fixing it
  inline, per the task's own scoping instruction. Waiting on the LDR→main promotion cycle + fresh Cloud Build to
  re-verify against the actual code fix — final execution evidence appended below once that completes (never triggering
  `ldr-to-main-promote-fleet.yml` manually, per the shared-slot starvation rule; polling `origin/main` on a 60s cadence
  via a backgrounded watchdog instead).
- **2026-08-12 (interactive session, reopened by coordinator)**: coordinator manually re-verified the first fix live
  (`understat-eu-typing-sweep-fv9j7`, 2026-08-12T10:16Z, against the fully-rebuilt image) and it still OOM'd — the slim
  pre-check correctly found 40 real (non-zero) candidates and fell through to the KEPT unfiltered full-schema read
  exactly as before, so the fix only ever helped the zero-candidate day. Reopened [CODE/INFRA] P1 with the failure
  evidence. Re-diagnosed live rather than guessing: measured the 40 candidates' actual `date` values first (tight 8-day
  window, 2026-08-05..08-12) to confirm a `date`-based `filters=` would genuinely give row-group pushdown before wiring
  anything — confirmed (64,001/17.2M rows, ~109MB). Shipped the real fix (instruments-service@c1fedba25d): full-schema
  fallback now uses `read_availability_index(bucket, filters=[("date", ">=", date_min), ("date", "<=", date_max)])`
  bounded to the slim pre-check's own candidate date range, instead of a bare `pd.read_parquet`. Verified logically +
  against live prod data via a dry run (no `--apply`) before shipping: 40/40 candidates correctly classified, ~50s wall
  time, no OOM. Also answered the coordinator's rightsizing question with a live measurement (not a guess): 16Gi/cpu4 is
  appropriate, NOT over-provisioned — the slim pre-check alone still holds ~6.5GB of pandas object memory at the current
  17.2M-row/6-column scale (unavoidable without knowing candidate dates in advance), leaving a real but not excessive
  ~2.5x margin at 16Gi. QG green (`quality-gates.sh --no-fix`, instruments-service). Re-triggered the
  LDR→main→Cloud-Build→execute verification chain via a backgrounded watchdog (never manually dispatching the shared
  promote workflow) — final execution ID/result appended below once it lands; the todo above stays UNCHECKED until that
  lands, per the coordinator's explicit instruction not to mark it done again without a fresh
  `gcloud run jobs execute --wait` against the rebuilt image.
