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
status: resolved
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
resolved_by: deployment-service@aa146bc
locked_by:
context_scope:
  [
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /plans/archive/issues/features_sports_env_staging_reads_empty_staging_reference_data_2026_08_01.md,
    deployment-service/scripts/vm/create-code-tarballs.sh,
    deployment-service/scripts/vm/gcs_upload_via_adc.py,
  ]
depends_on: []
---

# code-tarball-refresh Cloud Run Job silently failing since at least 2026-07-30

> **🟢 RESOLVED 2026-08-01 — `deployment-service@aa146bc`.** All 3 todos done; fix verified live (execution
> `code-tarball-refresh-9zfmf`, `Refresh complete — 6/6 tarball(s) updated`). Archived per the plan-completion
> discipline. See the Todos section below for the full attempt history and the final resolution.

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

- [x] ✅ [INFRA] P0. **RESOLVED 2026-08-01 — `deployment-service@aa146bc`, verified live.** Fix the Cloud Run Job's
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

                      **Attempt 2 (2026-08-01, same session, NOT deployed to the live job — validated locally only)**: rather than
                      re-deploy blind, tried a candidate fix (c) in a throwaway local clone first — broaden
                      `refresh_code_tarballs.sh`'s sparse-checkout of `deployment-service@LDR` (currently `scripts/vm` only) to
                      also pull `deployment_service/` + `pyproject.toml`, then `pip install` from that local clone directly instead
                      of by name from AR (no publish-pipeline dependency at all). Validated the sparse-checkout expansion itself
                      works cleanly (`git sparse-checkout set --no-cone 'scripts/vm/*' 'deployment_service/*' 'pyproject.toml'`),
                      but the subsequent `pip install .` from that clone ALSO fails, for two separate structural reasons — both
                      worth knowing before anyone else tries this path again:
                      1. **Python version mismatch**: `deployment-service`'s own `pyproject.toml` declares
                         `requires-python = ">=3.13,<3.14"`. The shared host's `python3` (and near-certainly the Cloud Run Job's
                         `google-cloud-cli:latest` image's bundled `python3`, a Debian-stable build) is `3.12.3` — every recent
                         `unified-trading-library` version on the AR index explicitly gates on `>=3.13,<3.14`, so pip refuses ALL of
                         them ("Ignored the following versions that require a different python version"). This blocks option (c)
                         even for the AR-hosted transitive deps, independent of the `deployment-service` publish gap above.
                      2. ~~**`unified-api-contracts` is stale on this same AR index**: only `0.2.38` is published there~~ —
                         **CORRECTION, same session, minutes later: this claim was WRONG, self-caught before it misled anyone.**
                         `pip`'s own error text (`ERROR: Ignored the following versions that require a different python
                         version: ... 0.86.0 Requires-Python <3.14,>=3.13 ...`) already showed `0.86.0` right there in the
                         ignored-versions list — I misread "ignored because of the Python-version filter" as "doesn't exist at
                         all" instead of reading the message's own stated reason. Direct verification via
                         `gcloud artifacts versions list --package=unified-api-contracts --repository=unified-libraries
                         --location=asia-northeast1 --project=central-element-323112` shows the AR index is fully current —
                         `0.86.1.dev1+gdcfe9ce5d` published `2026-08-01T10:54:10`, `0.86.0` at `2026-08-01T02:55:22`, matching
                         the repo's own `git describe` tag exactly — and `gh run list --workflow=publish-package.yml` on
                         `unified-api-contracts` shows the publish pipeline running successfully multiple times a day, as
                         recently as hours before this correction. **There is only ONE real blocker, not two**: the Python
                         3.12-vs-3.13 mismatch from point 1 above. Once that's satisfied, both `unified-trading-library` AND
                         `unified-api-contracts` resolve fine from this exact AR index — no separate publish-pipeline problem
                         exists, and no further audit of it is needed.

                      **Resolution shipped (2026-08-01, same session) — deployment-service@aa146bc**: rather than build a NEW
                      custom image (which the mid-session revised recommendation below originally called for), found an
                      EXISTING one that already solves the single real blocker: `deployment-service:latest` (the
                      `maintenance-jobs` Docker stage, built off the `unified-trading-library` base image) already has Python
                      3.13.14 + `deployment_service` + git/bash/tar/gcloud all verified present — the same image
                      `tarball_cleanup_scheduler.tf` and `vm_log_archival_scheduler.tf` already run their own maintenance jobs
                      from. Switched `code_tarball_refresh_scheduler.tf`'s job to that image, dropped the old sparse-checkout
                      bootstrap entirely (the script + package are baked in), and ran `scripts/vm/refresh_code_tarballs.sh`
                      directly — mirroring `tarball_cleanup_scheduler.tf`'s exact `command`/`args` pattern. Also added
                      `code-tarball-refresh` to `deployment-service-jobs-image.cloudbuild.yaml`'s `redeploy-jobs` list so future
                      image rebuilds keep it in sync like the other 3 maintenance jobs. Deployed imperatively via
                      `gcloud run jobs update` (this job's terraform file has carried a "Created imperatively... this file is
                      the IaC SSOT" note since 2026-06-17; a stale/incompatible terraform backend on this shared host — `Error:
                      Failed to decode current backend config... unsupported attribute "universe_domain"` — made `terraform
                      apply` unsafe to attempt, matching the file's own established deployment path). **This ended up
                      MATCHING the original `est_hours: 1.0` after all** — the "genuinely bigger unit of work" framing below
                      was written before finding that a suitable image already existed; left uncorrected below as an honest
                      record of the mid-investigation reasoning, not deleted.

                      ~~**Revised recommendation**: publishing `deployment-service` as a wheel (option a) and this local-clone
                      install (option c) are BOTH now proven blocked by real infra gaps (missing publish + stale publish +
                      python-version mismatch), not just untried. **Option (b) — a custom Cloud Run
                      container image with a properly-built `.venv` (matching `deployment-service`'s actual Python 3.13 +
                      real dependency versions, built via a normal `uv sync` in a Dockerfile build step, same pattern every OTHER
                      service in this repo already uses) — is now the only validated-viable path**, not just the least-invasive
                      guess. This is a genuinely bigger unit of work than the original `est_hours: 1.0` assumed (new Dockerfile +
                      Cloud Build trigger + terraform image reference, mirroring an existing service's `Dockerfile` pattern) —
                      scope it as such rather than another quick-fix attempt. Do NOT re-attempt (a) or (c) without first fixing
                      their respective blockers (publish `deployment-service`+bump `unified-api-contracts` on the AR index, and
                      resolve the Python 3.12-vs-3.13 mismatch) — both are real, separate, and non-trivial.

                      Re-verify any future fix the SAME way both these attempts did: `gcloud run jobs execute
                      code-tarball-refresh --project=central-element-323112 --region=asia-northeast1`, then
                      `gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="code-tarball-refresh" AND
                      labels."run.googleapis.com/execution_name"="<new-execution-id>"' --project=central-element-323112` for
                      `Refresh COMPLETE` / `N/N updated`, not a fast exit-1 or `PARTIAL`.

                      **VERIFIED LIVE (2026-08-01T15:04-15:10Z, execution `code-tarball-refresh-9zfmf`)**: fresh manual
                      execution against the redeployed job — `succeededCount: 1`, `Completed True`, "Execution completed
                      successfully in 6m28.58s." Logs confirm the FULL real pipeline ran correctly: SHA-skip scanned all 11
                      repos, correctly identified 6 CHANGED (deployment-service, market-data-processing-service,
                      features-service, ml-service, execution-service, batch-live-reconciliation-service) vs 5 already
                      up-to-date, rebuilt + uploaded all 6 (including real tarball + manifest + launcher-script uploads to
                      `gs://deployment-scripts-central-element-323112/code/...`, individually confirmed in the logs), and
                      closed with **`Refresh complete — 6/6 tarball(s) updated to live-defi-rollout tip.`** — the exact
                      done-when criterion this todo asked for. The scheduled cron will now keep tarballs current going
                      forward without operator intervention. `gcs_upload_via_adc.py`'s `ModuleNotFoundError` class is fully
                      closed for this job.

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
