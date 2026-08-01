---
doc_type: issue
title: >-
  code-tarball-refresh Cloud Run Job has silently failed to update ANY tarball for at least 2 days — ModuleNotFoundError
  in the upload helper, masked because the job reports success
summary: >-
  The scheduled `code-tarball-refresh` Cloud Run Job (`*/30 * * * *`, `terraform/gcp/code_tarball_refresh_scheduler.tf`)
  has updated ZERO tarballs on every run since at least 2026-07-30T13:02Z (confirmed via Cloud Logging, ~90+ consecutive
  runs) — every repo's `gcs_upload_via_adc.py` upload step crashes with `ModuleNotFoundError: No module named
  'deployment_service'`, so `refresh_code_tarballs.sh` logs `Refresh PARTIAL — 0/N updated` and the job execution still
  reports `succeededCount=1` (the container's own exit(1) is not surfacing as a job failure). VM launchers only WARN
  (not block) on a stale tarball (`LC_TARBALL_FRESHNESS` defaults to `warn`), so every batch VM launched during this
  window may have silently run on code older than what was actually shipped to `live-defi-rollout` — discovered because
  a just-shipped features-service fix (source-bucket override,
  `features_sports_env_staging_reads_empty_staging_reference_data_2026_08_01.md`) did not take effect on a real
  verification VM even though it was confirmed on `origin/live-defi-rollout`.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [vm-tarball-deployment, cloud-run-job, silent-failure, code-freshness, cross-cutting]
related:
  [
    plans/active/issues/features_sports_env_staging_reads_empty_staging_reference_data_2026_08_01.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
  ]
created: "2026-08-01"
parent_epic: infrastructure_master
priority: P0
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [features_sports_env_staging_reads_empty_staging_reference_data_2026_08_01-worker]
resolved_by:
locked_by:
context_scope:
  [
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /plans/active/issues/features_sports_env_staging_reads_empty_staging_reference_data_2026_08_01.md,
    deployment-service/scripts/vm/create-code-tarballs.sh,
    deployment-service/scripts/vm/gcs_upload_via_adc.py,
  ]
depends_on: []
---

# code-tarball-refresh Cloud Run Job silently failing since at least 2026-07-30

## What I found

While verifying a features-service fix on a real e2e-check VM
(`features_sports_env_staging_reads_empty_staging_reference_data_2026_08_01.md`), a force-leg run against a VM launched
at `2026-08-01T12:32:15Z` — well AFTER the fix (`features-service@72393fbf`) was confirmed as an ancestor of
`origin/live-defi-rollout` — still exhibited the pre-fix broken behaviour (reads hit the stale
`instruments-store-sports-stg-...` bucket). Root-caused to the VM having pulled a STALE `features-service-code.tar.gz`
from `gs://deployment-scripts-central-element-323112/code/`.

Checked the scheduled `code-tarball-refresh` Cloud Run Job (`*/30 * * * *`) directly via Cloud Logging:

```
2026-08-01T12:31:13Z [refresh-tarballs] Refresh PARTIAL — 0/10 updated; FAILED: batch-live-reconciliation-service
  deployment-service execution-service features-service instruments-service market-data-processing-service
  market-tick-data-service ml-service strategy-service unified-api-contracts
...
Traceback (most recent call last):
  File "/tmp/ds/scripts/vm/gcs_upload_via_adc.py", line 20, in <module>
    from deployment_service.vm.gcs_upload_cli import main
ModuleNotFoundError: No module named 'deployment_service'
Container called exit(1).
```

Every single run in the queried window (2026-07-30T13:02Z through 2026-08-01T12:31Z — the full extent I checked, likely
longer) shows the identical `Refresh PARTIAL — 0/N updated` failure. `gcloud run jobs executions list` nonetheless
reports `succeededCount=1, failedCount=0` for these executions — the container's own `exit(1)` on
`Container called exit(1).` is not propagating as a Cloud Run Job execution failure, so the standard job-health surface
(whatever alerting/dashboard reads `executions list`) reads GREEN the entire time.

**Root cause**: `scripts/vm/create-code-tarballs.sh`'s upload step resolves its Python interpreter as
`GCS_UPLOAD_PY="${DS_ROOT}/.venv/bin/python"`, falling back to bare `python3` only if that path is missing
(`create-code-tarballs.sh:513-514`). Inside the Cloud Run Job's container, `DS_ROOT` resolves to `/tmp/ds` (per the
traceback's `File "/tmp/ds/scripts/vm/gcs_upload_via_adc.py"`) — and that path has no `.venv/bin/python`, so it falls
back to bare `python3`, which does not have the `deployment_service` package importable (`gcs_upload_via_adc.py` imports
`from deployment_service.vm.gcs_upload_cli import main`). The actual tarball BUILD step succeeds
(`Created: execution-service-code.tar.gz (3.2M)` etc. — confirmed in the same logs); only the final
`gcloud storage`-equivalent upload via `gcs_upload_via_adc.py` crashes, for every changed repo, every run.

I also reproduced the identical failure interactively on this shared host: `.tabs/2/deployment-service` had no `.venv`
at all (same missing-venv class as `RULES.md`'s "stale sibling .venv's → uv sync" note) — after `uv sync`, the SAME
bare-`create-code-tarballs.sh --include features-service` upload succeeded cleanly. That confirms the fix class (a
working `.venv` with `deployment_service` importable resolves it) but the **production Cloud Run Job's own container
image** is the thing that needs fixing — it's not a "stale sibling venv on a dev host" instance, it's the job's own
deployed image lacking (or losing) its own venv at `/tmp/ds`.

## Why it matters

- **Cross-cutting, active, multi-day production gap**: every batch/backfill VM across every service+asset_group that
  launches via the tarball-deployment path (`launch-*.sh` scripts calling `lc_verify_tarball_freshness`) has been
  running on whatever code was tarball-current as of before 2026-07-30T13:02Z, regardless of what has shipped to
  `live-defi-rollout` since — for at least ~2 days and counting.
- **The staleness gate does not block** — `LC_TARBALL_FRESHNESS` defaults to `warn`, so launches proceed silently on
  stale code; nothing in the normal launch path would have surfaced this without someone specifically diffing real-VM
  behaviour against a just-shipped fix, as happened here.
- **The job's own health signal is false-green** — `succeededCount=1` even though the container logs its own `exit(1)`,
  so whatever monitors `code-tarball-refresh` executions for health (if anything does) would not have caught this
  either.
- Directly caused a false-negative on an UNRELATED task's verification (the sports source-bucket fix genuinely works —
  confirmed once the tarball was manually rebuilt via a direct `create-code-tarballs.sh --include features-service`
  invocation from a fixed local venv — see
  `features_sports_env_staging_reads_empty_staging_reference_data_2026_08_01.md`).

## Todos

- [ ] [INFRA] P0. **Attempt 1 shipped + verified NOT sufficient — real fix still needed.** Fix the Cloud Run Job's
      `code-tarball-refresh` container image so `gcs_upload_via_adc.py` can import `deployment_service` — either bake a
      working `.venv` at the `DS_ROOT` the container resolves (`/tmp/ds`), install `deployment_service` into the
      container's system/base Python, or make `create-code-tarballs.sh`'s `GCS_UPLOAD_PY` resolution robust to a missing
      venv (e.g. fall back to a `PYTHONPATH`-aware invocation instead of silently falling back to a bare interpreter
      that can't import the package). Verify by triggering a manual job execution and confirming `Refresh COMPLETE` /
      `N/N updated` in the logs, not `PARTIAL`. (repo: deployment-service)

      **Attempt 1 (2026-08-01, na_eligibility_auditor slot 2, `agent-orchestrator` dispatch agt-8e95ca, shipped
          `deployment-service@dbd9e72`)**: added `ensure_deployment_service_importable()` to `refresh_code_tarballs.sh` —
          gated on `CHANGED` non-empty, installs `deployment-service` via `python3 -m pip install --target=/tmp/ds-pydeps`
          from the internal AR wheel index (`asia-northeast1-python.pkg.dev/central-element-323112/unified-libraries`,
          same index every service `Dockerfile` already uses) authenticated via the job's own ambient
          `gcloud auth print-access-token`, then exports `PYTHONPATH` before the upload subshell runs. **Manually triggered
          a real job execution to verify** (`gcloud run jobs execute code-tarball-refresh`, execution
          `code-tarball-refresh-8j8ql`, 2026-08-01T14:36Z) — **FAILED**, exit code 1, in ~25s (before even reaching the
          upload step): `pip install deployment-service` returned `ERROR: Could not find a version that satisfies the
          requirement deployment-service (from versions: none)` / `No matching distribution found`. The request DID reach
          the AR index successfully (a real "no versions" answer, not an auth/404 error) — **`deployment-service` is very
          likely never published as an installable wheel to that index at all**: `deployment-service`'s own
          `.github/workflows/semver-agent.yml` has zero references to `publish-package`/`workflow_call` (grepped directly),
          unlike `unified-trading-library`/`unified-api-contracts`, which the release pipeline DOES publish (they're
          consumed as dependencies by every service; `deployment-service` is itself a deployable
          orchestration-engine/service, not a library other repos `pip install`). **My attempt-1 approach's core assumption
          was wrong** — confirmed the mechanism (gate on CHANGED, PYTHONPATH-inject) is sound, but the wheel-index source
          doesn't have this specific package. Left the code shipped (harmless — it correctly fails fast+loud now instead of
          silently, an improvement over the original silent crash even though the underlying job is still broken) rather
          than reverting, since reverting would restore the WORSE silent-`ModuleNotFoundError` behavior.

          **Next step for whoever picks this up** (NOT yet attempted — genuinely blocked on a design choice, not a
          mechanical retry): pick one of (a) publish `deployment-service` as a wheel too (extends the release pipeline —
          bigger, cross-cutting CI change, touches every future `deployment-service` release); (b) bake a custom Cloud Run
          container image for this job with a pre-built `.venv` (the terraform's own comments show this job deliberately
          avoids a custom image today, using the stock `google-cloud-cli` image — a real design reversal, needs sign-off);
          or (c) broaden `refresh_code_tarballs.sh`'s existing sparse-checkout of `deployment-service@LDR` (currently
          `scripts/vm` only) to also pull `deployment_service/` + `pyproject.toml`/`uv.lock`, then `uv pip install -e .` or
          `pip install .` from that fresh clone directly (no AR index needed at all — trades a slightly bigger
          sparse-checkout for zero publish-pipeline dependency). (c) is probably the least invasive given (a) and (b) both
          touch shared release/image infrastructure. Re-verify the SAME way this attempt did: `gcloud run jobs execute
          code-tarball-refresh --project=central-element-323112 --region=asia-northeast1`, then
          `gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="code-tarball-refresh" AND
          labels."run.googleapis.com/execution_name"="<new-execution-id>"' --project=central-element-323112` for
          `Refresh COMPLETE` / `N/N updated`, not a fast exit-1 or `PARTIAL`.

- [x] ✅ [INFRA] P0. Make a genuine upload failure inside `refresh_code_tarballs.sh` propagate as a Cloud Run Job
      execution FAILURE, not a silently-successful exit — VERIFIED ALREADY CORRECT, no code change needed. This todo's
      own premise (`succeededCount=1, failedCount=0`) does not hold:
      `gcloud run jobs executions list --job=code-tarball-refresh     --project=central-element-323112 --region=asia-northeast1 --format=json`
      over 30 consecutive real executions spanning `2026-07-31T23:30Z`→`2026-08-01T14:00Z` (~15h, the same
      ongoing-broken window this doc documents) shows **30/30 with `failedCount=1`, 0/30 with `succeededCount≥1`**.
      `gcloud run jobs executions describe     code-tarball-refresh-66w77` confirms the `Completed` condition
      `status=False, reason="NonZeroExitCode",     message="Task ... failed with exit code: 1..."`. The default
      (non-JSON) CLI table also renders this unambiguously — a leading `X` failure glyph + `COMPLETE: 0 / 1`. Root cause
      of the correct behavior: `refresh_code_tarballs.sh` already `exit 1`s on any non-empty `failed_repos` (line ~174,
      shipped 2026-06-17 commit `bba8096`), the `code_tarball_refresh_scheduler.tf` bootstrap `exec`s straight into it
      (so the container's own exit code IS the script's), and the deployed job has `max_retries=0` (confirmed live via
      `gcloud run jobs describe` matches terraform) — so a genuine failure is never masked by a retry. **Correction to
      this doc's original claim**: the `succeededCount=1, failedCount=0` reading was very likely a misread of the CLI
      table (a `None`/blank `succeededCount` column next to a populated `failedCount=1` column is easy to misalign when
      eyeballing — confirmed by directly reproducing that exact misreading before catching it with `--format=json`).
      **The real false-green surface, if any, is Cloud Scheduler's OWN job status, not the Cloud Run Job's**:
      `gcloud scheduler     jobs describe uts-prod-code-tarball-refresh-cron` shows `status: {}` (no error) because
      Cloud Scheduler only checks the synchronous HTTP 200 from the `:run` trigger API (job-accepted), not the
      downstream execution outcome — that's GCP's own async-trigger design for Cloud Run Job schedulers, not a bug in
      this repo's exit-code handling, and out of scope for this todo (which is specifically about the Cloud Run Job's
      own execution status). Evidence: verified 2026-08-01 via live `gcloud` queries against `central-element-323112`,
      no commit — the existing shipped code already satisfies the acceptance criterion. (repo: deployment-service)
- [x] ✅ [INFRA] P1. Audit whether any VM launched since 2026-07-30T13:02Z under `LC_TARBALL_FRESHNESS=warn` (the
      default) ran on materially stale code for a repo with a real bugfix shipped in that window. Established the
      per-repo staleness windows (each tarball's `.manifest.json` `created_at`) and cross-referenced each against its
      repo's real (non-ci/deps) `live-defi-rollout` fix commits in that window — MTDS is highest-risk: floating for
      ~47.5h (`2026-07-30T13:02Z`→`2026-08-01T12:42:24Z`), during which ~30 real fixes landed, including two explicitly
      self-described as fixing "100% empty live capture" (Binance-Futures/ASTER wire-shape `4f244845`, OKX-FUTURES
      canonical-id/channel `8a6bbc97`) plus a same-day cefi perp_funding manifest-write data-loss regression+revert
      (`fb32fb65`). Traced `vm-logs/*/TARBALL_PINS.json` for real VM launches inside the window (~1050 fleet-wide by
      date); the one concrete lead (`cefi-queue-heavy-binancefutu-x17`, launched twice post-fix with zero tarball pins
      recorded) turned out to run the Tardis HISTORICAL-file backfill path, not the live-WS path the fixes target — so
      likely unaffected. Could not, within this audit's scope, locate a genuine PRODUCTION live-capture VM launch inside
      the window to confirm/rule out actual impact. Per the "file the resulting gap as its own P0/P1 issue — do not
      silently accept it" instruction: filed
      `plans/active/issues/tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md` (P1) with 2 concrete
      AO-dispatchable follow-up todos (identify the actual live-capture deployment mechanism; check MTDS manifest
      capture_status/row-counts for the named venues over the window — escalate to confirmed P0 if any zero-row stretch
      is found). batch-live-reconciliation-service (stale since 2026-07-27, predating the outage) had exactly 1 real fix
      in-window and it's perf-only (column projection), not correctness — no issue needed there. (repo:
      unified-trading-pm)

## Codex SSOTs

`/codex/05-infrastructure/vm-tarball-deployment.md`.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
