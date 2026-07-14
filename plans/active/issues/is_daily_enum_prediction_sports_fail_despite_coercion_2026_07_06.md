---
doc_type: issue
title:
  is-daily-enum-{prediction,sports} still exit(1) in the cloud despite the fixed UTL (coercion) being in the deployed
  image — real error hidden by the Cloud-Run observability gap
summary:
  "Root-cause-#1 (capture-path dtype) is NOT fully closed. The daily instruments-enumeration Cloud Run jobs
  is-daily-enum-prediction (failing 07-01→) and is-daily-enum-sports (failing 06-28→, longer + previously undetected)
  BOTH still exit(1) after a full ~37-min enumeration, EVEN THOUGH the deployed image now carries the UTL write-side
  coercion that fixes the ArrowTypeError merge crash (confirmed by docker-inspecting the image). So the coercion was
  necessary but is NOT the (whole) cause — there is a SECOND, different failure at the end of the run. It cannot be
  diagnosed from Cloud Logging (which shows ONLY 'Container called exit(1)' — the shard-isolation catch swallows the
  traceback without exc_info). A local .venv run of the same command on the same UTL 1.6.0 SUCCEEDS, so the failure is
  cloud-image/environment-specific. This doc is a HANDOFF: it records everything the slot-2 perp-correction agent tried
  (it was out of that agent's assigned scope — perp correction — so it is being handed to the capture-hardening owner
  rather than debugged further)."
status: resolved
nature: issue
asset_group: [prediction, sports]
stage: [data]
repos: [instruments-service, unified-trading-library, deployment-service]
scope: [engineer, admin]
tags:
  [manifest, consolidator, capture, dtype, arrow, coercion, is-daily-enum, cloud-run, observability, exc-info, handoff]
related:
  [
    plans/active/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md,
    plans/active/prediction_capture_incident_remediation_2026_07_06.md,
  ]
created: 2026-07-06
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P0
source:
  [
    slot-2 perp-correction agent — found while auditing the sports double-consolidator (a Workstream-A residual) that
    both prediction+sports cloud enum jobs still fail even after the coercion reached the image 2026-07-06,
  ]
resolved_by:
  [
    "OOM root cause (exit -9) fixed by memory bumps: prediction 16Gi green 2026-07-13T23:54Z (wrbsm); sports 32Gi green
    2026-07-14T15:02:44Z (5vchf, the 13:30Z scheduled cron run) — both daily enum jobs verified green end-to-end",
  ]
locked_by:
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

# is-daily-enum-{prediction,sports} still fail despite the coercion (handoff 2026-07-06)

> **Scope note / why this is a handoff.** The slot-2 agent was assigned the **KALSHI/POLYMARKET-PERP adapter
> correction** (Workstream B of `prediction_capture_incident_remediation_2026_07_06.md`). While doing the "audit sports
> for the same double-consolidator condition" residual, it found the sports+prediction cloud enum jobs are still dead —
> an unrelated **capture-hardening (root-cause-#1)** problem. Per findings-triage it should have been written up and
> left for the capture-hardening owner; instead it went several layers deep (below). This doc captures ALL of that so
> the right owner can continue without re-deriving it. **The slot-2 agent has STOPPED debugging this and returned to the
> perp correction.**

## The symptom (measured, explicit)

- **`is-daily-enum-sports`**: `failedCount=1` every day **06-28 → 07-06** (verified `gcloud run jobs executions list`).
  Sports instruments capture has been DEAD ~8 days, previously undetected. Sports availability index
  (`instruments-store-sports-prd-…/_index/availability_index.parquet`) is string-poisoned: `instrument_count` /
  `row_count` / `expected` / `available` all `object`/str across 4,999,446 rows.
- **`is-daily-enum-prediction`**: `failedCount=1` **07-01 → 07-06** (its index string-poisoned too, ≈24,994 rows).
- Both jobs run `instruments-service:latest`; runtime is ~31–51 min then exit(1) (i.e. it **enumerates fully, then dies
  at the end** — consistent with a write/merge step, not an import/startup error).
- cefi / defi / tradfi enum jobs SUCCEED (their indexes are not poisoned) — the failure is isolated to the two
  string-poisoned AGs.

## What is NOT the cause (ruled out with evidence)

- **NOT "the image lacks the coercion."** The image was rebuilt with the coercion (see "what I tried" #1–2) and I
  **docker-inspected it**: `instruments-service@sha256:f36f3bba…` has `_writer_io.py` with the `Int64` coercion + the
  `expected_window_completeness_fraction` float coercion, UTL version **1.6.0**. Yet the enum still fails. So the
  coercion is present and is NOT what's still breaking.
- **NOT the UTL version.** Local `.venv` and the image both run UTL **1.6.0**. A local `.venv` run of the EXACT cloud
  command healed prediction successfully in a prior session. So the code+UTL work locally; the cloud run does not.
- **Therefore the remaining failure is cloud-image/environment-specific** (candidates below), and it is a DIFFERENT
  error from the original `ArrowTypeError` (which the coercion does fix — verified on the exact poisoned 24,994-row prod
  frame in the prior session).

## The blocker: total observability gap

Cloud Logging for these executions contains ONLY `Container called exit(1).` — no traceback, no app logs. Two reasons
(both are open residuals in the remediation plan):

1. The UTL shard-isolation catch (`service_framework/_adapter.py`, "Handler %s failed on payload") logs **without
   `exc_info=True`** → the real exception is swallowed.
2. Cloud Run job stdout/stderr does not reach Cloud Logging for these jobs.

**This is why the failure can't be diagnosed remotely — fixing (1) first (add `exc_info=True` + redeploy) would very
likely surface the real error on the next run and unblock everything else here.**

## What I tried (chronological — so you don't repeat it)

1. **(mis-step) Assumed the deployed image lacked the coercion** and bumped the UTL base-image pin. instruments-service
   `Dockerfile` `ARG BASE_IMAGE_DIGEST` was `sha256:a0359e03…` (a UTL base predating the coercion); bumped it to
   `sha256:9f01cf8e…` (= UTL base `:latest`, the coercion build `7c6e2437`/`0e85227`, UTL 1.6.0). **Shipped:
   instruments-service@1098731c4** (QG green incl. STEP 5.79 base-pin gate), promoted to main, image rebuilt to
   `:latest` = `sha256:f36f3bba…`. **This is a legitimate, correct change** (the image SHOULD track the coercion base) —
   leave it in place — but it did **not** fix the enum failure.
2. **docker-inspected `f36f3bba`** → confirmed the coercion IS present (UTL 1.6.0). See "what is NOT the cause".
3. **Re-ran `is-daily-enum-prediction` on `f36f3bba`** (exec `hpmlr`) → **still `failedCount=1`** after ~37 min.
   (Earlier exec `n2kc9` on the pre-pin image also failed; a first watchdog wrongly reported these as "succeeded" — a
   bug in a hand-rolled `awk` status poller that misread gcloud's tab output when `succeededCount` is empty. Always read
   `gcloud run jobs executions describe` fields explicitly, one at a time.)
4. **Started a local `.venv` repro** of the exact cloud command (below) with visible stdout/stderr to capture the real
   traceback the cloud swallows. It was still enumerating (~30 min in) when I stopped it to hand this off. **This is the
   most promising next step** — let it run to the failure and read the traceback.

### The exact cloud command + env (for a faithful local/docker repro)

```
python scripts/daily_is_enumeration.py --asset-group prediction --days-back 3 --force --log-level INFO
# env: MANIFEST_PER_VM_SHARDS=true PROJECT_ID=central-element-323112 VM_NAME=is-daily-enum-prediction
#      DEPLOYMENT_ENV=prod GCP_PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp CLOUD_MOCK_MODE=false
# resources: cpu=4 memory=8Gi timeoutSeconds=7200 maxRetries=1
# (sports: same, --asset-group sports; sports index is 4.99M rows → watch for OOM at 8Gi)
```

Use a NON-prod `VM_NAME` (e.g. `…-localrepro`) so the local repro writes an isolated per-VM manifest shard, not the real
one.

## Candidate causes to check next (unordered)

- **OOM at 8Gi** on the merge/write of the large index (sports index is 4.99M rows; prediction is small, so if
  prediction ALSO OOMs that argues against OOM — but check the exit signal; a true OOM-kill is 137/SIGKILL, whereas
  these show exit code **1**, which points AWAY from OOM and toward an app-level exception).
- **A second dtype/schema mismatch** the coercion doesn't cover (the coercion handles
  `instrument_count`/`schema_version`/`row_count`/`expected`/`available`/`expected_window_completeness_fraction`; if the
  poisoned index has ANOTHER column with a mixed dtype, `to_parquet` would still raise a different `ArrowTypeError`).
- **A cloud-only env/config difference** vs the successful local run (service account perms, a config-reloader, a per-VM
  shard path, `MANIFEST_PER_VM_SHARDS` interaction).

## Infra changes I made that you should know about (do NOT be surprised by these)

- **SHIPPED — instruments-service@1098731c4**: Dockerfile UTL base pin `a0359e03 → 9f01cf8e` (coercion base). On main;
  `:latest` = `f36f3bba` (UTL 1.6.0). Correct change; keep it.
- **PAUSED — `uts-prod-manifest-consolidator-instruments-sports-legacy-cron`** (Cloud Scheduler, asia-northeast1).
  Sports had BOTH the legacy and non-legacy instruments consolidators enabled `*/1` (racing co-writers on one index) —
  the same condition that was fixed for prediction/cefi/defi/tradfi. Pausing the legacy one brings sports in line.
  **Reversible:**
  `gcloud scheduler jobs resume uts-prod-manifest-consolidator-instruments-sports-legacy-cron --location=asia-northeast1`.
- **No other infra touched** for this issue. (The cefi KALSHI-PERP guard + purge are a SEPARATE, in-scope perp fix — see
  `prediction_capture_incident_remediation_2026_07_06.md`.)

## Suggested fix order

1. Add `exc_info=True` to the UTL shard-isolation catch + redeploy (closes the observability gap) — OR run the local
   repro above to read the traceback now.
2. From the real traceback, fix the second failure (dtype / OOM / env).
3. Re-run `is-daily-enum-{prediction,sports}` on the fixed image; verify `succeededCount=1` via
   `gcloud run jobs executions describe` (read each field explicitly).
4. Backfill the missed windows (prediction 07-01→, sports 06-28→) once the daily job is green.

## Progress log

- **2026-07-13 ~23:16Z (sink amendment EXECUTED per operator ruling, logsink-enum-diagnosis leg)** — **Observability gap
  CLOSED.** Operator ruled (2026-07-13 interactive Q&A) to amend the `_Default` sink exclusion. Pre-delete/before state:
  exclusion `debug-filter` filter = `severity <= "DEBUG"` (sink updateTime 2023-01-31T10:50:51Z). After:
  `severity <= "DEBUG" AND NOT resource.type="cloud_run_job"` (sink updateTime 2026-07-13T23:15:53Z). Execution note:
  `unified-trading-sa` (the only local credential) LACKS `logging.sinks.update` (verified via `testIamPermissions`;
  Cloud Build default SA `1060025368044@cloudbuild` and compute default SA also lack it) — executed via **Cloud Build
  running as `logging@central-element-323112.iam.gserviceaccount.com`**
  (`gcloud builds submit --no-source --service-account=…/logging@…` — build `9a838983-464c-4f45-b703-c436e8ad058e`
  SUCCESS; two failed permission-probe builds `21d51648…`/`6749d15f…` precede it). VERIFIED WORKING: a fresh
  `is-daily-enum-prediction` execution launched 23:16Z now streams full app stdout to Cloud Logging
  (`resource.type="cloud_run_job"`, INFO lines visible 23:20Z). Also: 22:22Z verification executions terminal states —
  `is-daily-enum-prediction-djjm7` FAILED (failedCount=1, retriedCount=1, completed 22:48:30Z);
  `is-daily-enum-sports-6dnq9` still running at 23:16Z. Canonical prediction `_index/availability_index.parquet`
  dtype-dumped 23:19Z: **no longer string-poisoned** (numerics int64/float64, expected/available bool) and NO per-VM
  shard exists for `vm=is-daily-enum-prediction` (only `_legacy_seed.parquet`), so the "second poisoned column in the
  job's own shard" lead is stale for prediction.
- **2026-07-13 (fresh-image verification + observability root cause, is-daily-enum leg sub-agent)** — **STILL OPEN: the
  2026-07-13 double rebuild does NOT fix it.** (a) Today's 13:30Z scheduled runs failed on the pre-rebuild image
  `sha256:01507aee…` (`is-daily-enum-sports-jqrjc` failedCount=1, completion 16:00:59Z; `…-prediction-tbkj7`
  failedCount=1 — both jobs pin `:latest`, which Cloud Run resolves at execution-creation, so the 13:30Z runs predate
  the 20:28Z/21:22Z rebuilds). (b) Manual verification executions were triggered 22:22Z on `:latest` =
  `sha256:8b6cb429…` (pushed 21:22Z, the second rebuild — NEWER than `a699bab0`, includes instruments-service@6e1f7972
  base-pin refresh to UTL base `b7e391f8`): **`is-daily-enum-prediction-djjm7` attempt-1 exited 1 at 22:37:40Z after ~15
  min** (`varlog/system` "Container called exit(1)") — same signature, ON the fully-fixed image. Retry attempt was in
  flight at handoff; `is-daily-enum-sports-6dnq9` attempt-1 still running (historically fails ~80 min in). **The
  base/UTL-staleness class is ruled out as the root cause.** (c) **Observability-gap root cause FOUND (supersedes both
  prior hypotheses)**: the project `_Default` logging sink carries exclusion `debug-filter: severity <= "DEBUG"` —
  unstructured Cloud Run job stdout gets severity `DEFAULT` (rank 0, BELOW `DEBUG`=100), so **ALL cloud_run_job stdout
  is dropped project-wide** (verified: zero stdout entries for ANY cloud_run_job since 07-12, including the SUCCEEDING
  is-daily-enum-cefi — so this is not crash-related log loss, and the UTL `exc_info` fix alone will surface NOTHING).
  Fix requires a sink-exclusion carve-out, e.g. `severity <= "DEBUG" AND NOT resource.type="cloud_run_job"` —
  project-level infra + log-cost decision → OPERATOR ruling requested (decision packet filed by the 2026-07-13 leg). (d)
  **OOM ruled out for the current failures**: `varlog/system` shows a clean app-level `Container called exit(1)` (a
  memory kill logs a distinct memory-limit message; none present for jqrjc/djjm7). (e) **Sharpened lead — the job's own
  per-VM manifest shard** (`MANIFEST_PER_VM_SHARDS=true`, `VM_NAME=is-daily-enum-{prediction,sports}`): the write-side
  coercion in `unified_trading_library/manifest_writer/_writer_io.py` covers
  `instrument_count`/`schema_version`/`row_count`/`expected`/`available`/`expected_window_completeness_fraction` only;
  if the job's own shard parquet (or the canonical index it read-merges) carries ANOTHER string-poisoned column,
  `to_parquet` still dies — and a local repro under a DIFFERENT `VM_NAME` (per this doc's own advice) would NEVER load
  the poisoned prod shard, exactly matching the local-succeeds/cloud-fails split. NEXT: dump dtypes of
  `vm=is-daily-enum-prediction` shard + canonical `_index` for both AGs, diff against the coercion column list; note
  `manifest_consolidator_dtype_at_source_fix_2026_07_07.md` is still `status: draft` (poisoning not yet fixed at
  source).

- **2026-07-10 (re-verification, sub-agent, instruments-completion-tracker sweep)** — **CONFIRMED still genuinely open,
  failing daily through 2026-07-09** (`gcloud run jobs executions list` for both `is-daily-enum-prediction` and
  `is-daily-enum-sports`: `failedCount=1` on every execution 07-06→07-09 inclusive; the 07-10 13:30 UTC run had not yet
  fired at verification time). **New diagnostic detail that sharpens (does not replace) the "observability gap"
  framing**: pulled the FULL Cloud Logging record for one execution's entire runtime window
  (`is-daily-enum-prediction-85tst`, started 13:30:14 UTC, exit(1) at 13:45:46 UTC — ran **15 minutes**, not an instant
  crash) via `gcloud logging read` with no severity filter, across every `logName` under that
  `resource.labels.job_name`. Result: **zero application-level log lines of any kind** — not even the wrapper script's
  own very first line (`"IS daily enumeration START ..."`, which `main()` logs via
  `logging.basicConfig(stream=sys.stdout, ...)` before doing anything else, and the job sets `PYTHONUNBUFFERED=1`). Only
  2 system-level log entries exist: `Container called exit(1)` at the two retry attempts. This is a STRONGER finding
  than "the shard-isolation catch swallows exc_info" (that hypothesis implies SOME log lines exist, just without a
  traceback) — the total absence of even the wrapper's trivial startup log line, after 15 real minutes of runtime,
  points to either (a) a Cloud Logging delivery gap specific to this job's log driver (the container's stdout/stderr
  genuinely isn't reaching the sink), or (b) a hard kill (SIGKILL/OOM) that occurs after logs are buffered but before
  Cloud Run's log agent flushes them — the job runs on an 8Gi/4cpu Cloud Run Job
  (`gcloud run jobs describe is-daily-enum-prediction`), and the wrapper invokes `python -m instruments_service ...` as
  an inherited-stdio subprocess (`subprocess.run(cmd, check=False)`, no `stdout=`/`stderr=` capture), so a hard kill of
  either the parent or child would silently drop everything not yet flushed to the log sink. **New candidate root cause
  worth investigating before the exc_info fix**: the still-open
  `manifest_consolidator_dtype_at_source_fix_2026_07_07.md` finding (numeric columns persisted as `utf8` instead of a
  compact dtype in the canonical `_index`) would inflate in-memory footprint significantly for a multi-million-row
  prediction/sports index once loaded into pandas — directly relevant here since these are exactly the two poisoned
  indexes (sports 4.99M rows, prediction ~25K). Did NOT find an explicit "memory limit exceeded" system log line (only
  checked this execution; not exhaustive), so OOM is a plausible-not-confirmed lead, same epistemic status as the
  `cefi_monotonicity_guard` doc's `t1-recon` OOM hypothesis — same pattern, different job. No code changed this pass —
  read-only `gcloud logging read` / `gcloud run jobs executions describe` / `gcloud run jobs describe` investigation
  only. Suggested fix order updated: try the local `.venv` repro (item 4 in "what I tried") or add `exc_info=True` AND
  memory-profile the run locally before assuming either fix alone will surface the real error.
- 2026-07-06: Filed by the slot-2 perp-correction agent as a scope-correcting handoff (it went out of its lane debugging
  this; stopping and returning to the perp task). All attempts + the two infra changes above recorded so the
  capture-hardening owner can continue. Blocker = observability gap (exc_info).
- 2026-07-13 23:35Z: ROOT CAUSE CAPTURED (first log lines ever, post sink carve-out):
  `IS enum FAILED asset_group=prediction exit_code=-9` at 23:28:14Z — **SIGKILL = OOM kill** at 8Gi/4CPU while the CLOB
  scan was past "page 1000, 1,001,000 markets total". No traceback ever existed to capture (SIGKILL is uncatchable) —
  explains why every prior diagnosis path came up empty even before the stdout suppression was found. Mitigation applied
  (operator's standing fix-now mandate): `is-daily-enum-prediction` memory 8Gi → **16Gi** (config-only, reversible);
  verification execution launched 23:35Z on the new limit — resolution flip awaits its green completion. Durable fix
  todo: chunk/stream the prediction CLOB universe scan so memory is bounded regardless of market count (the 1M+ market
  universe will keep growing past any fixed limit). is-daily-enum-sports-6dnq9 still running at 23:33Z (~71 min in); if
  it also exits -9, apply the same bump + the same durable-fix analysis for the sports index path.
- [ ] [CODE] P2. Durable fix: bound memory in the prediction CLOB universe scan (chunked pagination → incremental
      manifest writes, no full-universe accumulation); same review for the sports enum path. Until then the 16Gi limit
      is a ceiling race against universe growth.
- 2026-07-14 00:05Z: **PREDICTION RESOLVED — first green run in 5+ days**: is-daily-enum-prediction-wrbsm
  succeededCount=1, completed 2026-07-13T23:54:52Z on 16Gi (the OOM diagnosis verified end-to-end: 8Gi OOM at -9 → 16Gi
  green). SPORTS confirmed same class: 6dnq9 logged `exit_code=-9` at 23:37:23Z on 8Gi — doomed 8Gi retry cancelled, job
  bumped to 16Gi, verification execution launched 00:04Z (in flight). The durable chunked-scan todo stands for both
  (16Gi is a ceiling race against universe growth). Doc flips to resolved when the sports verification lands green.
- 2026-07-14 02:05Z: SPORTS memory class is DEEPER than prediction's. is-daily-enum-sports OOM'd (-9) even at 16Gi
  (executions 01:10 + 01:53); bumped to 32Gi/8cpu (13:30Z cron verifies). SEPARATELY the nightly
  expected-universe-v2-sports run (01:30Z, execution -p8f9v) — previously green nightly at 8Gi — was SIGKILLed in ~90s
  at the manifest `pd.concat` (enumerate_expected_universe.py:2722) on its FIRST run with the new image. Prime suspect:
  the oscillation guard's `_build_captured_set` (instruments-service@ba306543) materializing ~5.5M Python row-key tuples
  over the sports index (prediction at 26K rows unaffected — its 16Gi run was green). Mitigation: job bumped 8Gi/2cpu →
  16Gi/4cpu, tonight's seeding re-executed (in flight). QUEUED CODE FIX (P1, joins the chunked-scan P2): memory-frugal
  captured-set (asset-group-filtered semi-join / pd.Index instead of tuple set) + audit the concat path; owner:
  follow-up to the staleness-trio ship (same file, sequenced to avoid same-file collision).
- 2026-07-14 03:16Z: **P1 CODE FIX SHIPPED — instruments-service@633d7af4**
  (`fix(enum): memory-frugal manifest load path — column-project index reads`). Root cause of the
  expected-universe-v2-sports 8Gi OOM measured on the REAL 5.75M-row sports index (profiled locally,
  `/usr/bin/time -v`): the enumerator loaded the index FULL-WIDTH — 42 object columns ≈ **5.6GB** in pandas — then the
  per-VM-shard `pd.concat` copy peaked ≈6GB; `_build_captured_set` added a full-width copy of the ~captured rows on top.
  Only 4 columns are ever consumed (sports present-set grain `data_type, league_id, date` + `capture_status`). Fix: (1)
  every manifest parquet read (cache / canonical / per-VM shards) column-projects at READ time via new
  `_needed_manifest_columns` + `_read_manifest_parquet_projected` (schema read first; full-width fallback only for a
  degenerate parquet with zero key columns); (2) `_build_captured_set` filters+projects in one `df.loc[mask, cols]`
  select (no full-width captured-rows copy); (3) `main()` releases the manifest frame before the enumeration loop.
  **Measured peak RSS (real script, scan-only, frozen 2026-07-14 index snapshot, identical inputs): 6,746MB before →
  1,619MB after (−76%, 4.2x)**; stage-level profile 5,967MB → 1,590MB with the concat-stage peak 5,967MB → 1,140MB.
  **Semantics proven byte-identical**: present-set (4,816,144) + captured-set (757,476 — exactly the -v97dj green run's
  logged size) sha256-identical old-vs-new on the real index; guard dropped the same 35 rows; the 44,386-row candidate
  CSVs byte-identical across before/after runs. Unit tests:
  `tests/unit/scripts/test_enumerate_manifest_memory_frugal.py` (55 tests — old-vs-new equivalence oracle on edge-case
  fixtures incl. NaN/dup/numeric keys + end-to-end guard-drop equivalence + a memory-shape pin that sports projection
  reads EXACTLY 4 of the 42 index columns). QG green, quickmerged to LDR. **Bump-back evaluation (recommendation, NOT
  executed)**: once the next instruments-service image rebuild carries 633d7af4, expected-universe-v2-sports can very
  likely return to 8Gi/2cpu — the fixed load path peaks ~1.6GB on today's index and scales per-row far shallower
  (retained cost is now the key-tuple sets, not the full-width frame). Leave the 16Gi mitigation until one green nightly
  run on the fixed image, then downsize. NOTE: is-daily-enum-sports (32Gi mitigation) is the SAME memory family but a
  DIFFERENT binary path (`daily_is_enumeration.py` universe scan, not this loader) — its 13:30Z 32Gi verdict + the
  chunked-scan P2 remain open and are NOT addressed by this ship.
- 2026-07-14 15:05Z: **SPORTS RESOLVED — the 13:30Z scheduled cron run on 32Gi is GREEN.** Execution
  `is-daily-enum-sports-5vchf` (created 13:30:03Z, the exact verification run this doc was waiting on): completed
  2026-07-14T15:02:44Z, `succeededCount=1`, `failedCount` empty, `retriedCount` empty (fields read explicitly, one at a
  time per this doc's own advice). Cloud Logging confirms the full app-level success path (sink carve-out working):
  `"IS enum OK asset_group=sports"` + `"IS daily enumeration DONE OK — all 1 AG(s) succeeded"` +
  `"Container called exit(0)"` at 15:02:41Z; per-VM shard updated (`_index/per_vm/is-daily-enum-sports.parquet`, 485
  entries, 93 new). Runtime ~92.7 min at 32Gi/8cpu — no OOM. **Both jobs now green → doc flipped `status: resolved` per
  its own criterion** ("flips to resolved when the sports verification lands green"; prediction went green
  2026-07-13T23:54Z on 16Gi). **Standing follow-ups that survive this resolution (owners noted, do not lose):** (1) the
  P2 durable chunked-scan fix above (both AGs — 16Gi/32Gi are ceiling races against universe growth); (2) bump-back
  evaluation — sports 32Gi→lower + prediction 16Gi→lower after a few green scheduled runs, and
  expected-universe-v2-sports 16Gi→8Gi once a nightly runs green on an image carrying instruments-service@633d7af4; (3)
  backfill the missed windows (prediction 07-01→07-13, sports 06-28→07-13) now that the daily jobs are green —
  coordinate with the sports GW/enrichment work in
  `sports_gw_enrichment_false_empty_manifest_and_dropped_rows_2026_07_14.md` (same index, avoid double-writing).
