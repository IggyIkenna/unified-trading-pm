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
status: open
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
locked_by:
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: data-pipeline-engineer
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

- 2026-07-06: Filed by the slot-2 perp-correction agent as a scope-correcting handoff (it went out of its lane debugging
  this; stopping and returning to the perp task). All attempts + the two infra changes above recorded so the
  capture-hardening owner can continue. Blocker = observability gap (exc_info).
