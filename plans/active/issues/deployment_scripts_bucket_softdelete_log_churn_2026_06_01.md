---
title: deployment-scripts bucket — 57 TiB (99.9% soft-deleted) from VM run.log re-upload churn + 7-day soft-delete
created: 2026-06-01
author: harsh
parent_epic: infrastructure_master
source:
  - unified-trading-library/unified_trading_library/lifecycle/uploader.py
  - deployment-service/deployment_service/vm/heartbeat_cli.py
  - deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh
  - deployment-service/scripts/vm/cleanup_old_tarballs.py
  - deployment-service/cloud-build/refresh-tarballs.cloudbuild.yaml
  - deployment-service/scripts/vm/create-code-tarballs.sh
locked_by: live-defi-rollout
---

## What I found

`gs://deployment-scripts-central-element-323112` was **57.5 TiB on 2026-06-01**, up from 207 GiB on 2026-05-20. **99.9%
(56 TiB) was soft-deleted shadow copies**; only ~66 GiB is live. Diagnosed by sampling (no full walk — bucket has 1.56M
objects):

- **The 56 TiB of soft-deleted BYTES = VM `run.log` re-upload churn.** `LogUploader.upload_once()`
  ([uploader.py:77-96](../../../unified-trading-library/unified_trading_library/lifecycle/uploader.py#L77-L96)) does
  `self.local_log.read_bytes()` → `upload_bytes(blob_path=key, ...)` to the **same** GCS key every `interval_sec`
  (default **30s**, env `UPLOAD_INTERVAL_SEC`), skipping only when file size is unchanged. An active VM's log always
  grows, so it re-uploads the **entire** 3–16 MiB log every cycle, each upload overwriting → (with soft-delete on)
  retaining a full copy for 7 days. Sample evidence: `vm-logs/cefi-bitget-spot-2025-heavy-.../run.log` overwritten 4× in
  49 s, each 16.5 MiB. A 90 s listing slice of `vm-logs/` alone = 61,499 soft-deleted objects / 263 GiB.
- **The 1.54M soft-deleted OBJECT COUNT = deployment heartbeat JSONs.** `deployments/active/<uuid>.json` (≈608 bytes)
  overwritten ~every 60 s. Dominates the count, ~0 bytes.
- **Tarballs are NOT the problem.** Live tarballs are only 1.17 GiB (394 files: 366 `@sha` + 28 mutable). The bucket's
  66 GiB of live data is mostly logs (`log-archive` 14.75 GiB + `logs` 3.5 GiB + `vm-logs` live, so large `du` times
  out). Tarballs are written by `create-code-tarballs.sh` (operator) + `refresh-tarballs.cloudbuild.yaml` (auto, fires
  when an asset_group tarball is older than latest `live-defi-rollout` commit), each writing both a mutable
  `{repo}-code.tar.gz` (overwrite) and `{repo}-code@{sha}.tar.gz` (per-commit).
- **The reaper is dead.** `cleanup_old_tarballs.py` exists (keep-N per service) but has **0 schedule references**
  (grepped terraform/cloud-build/cron). Its docstring is stale: claims "single-file-per-service naming … No cleanup is
  needed today" — wrong, `@sha` naming is live. `@sha` tarballs accumulate unbounded (72 for unified-api-contracts).
- **No lifecycle rules** on the bucket at all (`lifecycle_config` empty); `log-archive/` "persists indefinitely".
- Nothing in the bucket benefits from soft-delete: tarballs reproducible from git/`@sha`; logs superseded/archived;
  `operator_capital_overrides/` (1.25 KiB) + `pre-migration-snapshots/` (0.18 GiB) are write-once/append-only so
  soft-delete (delete/overwrite protection) never engages for them.

## Why it matters

56 TiB of soft-deleted STANDARD storage in `asia-northeast1` ≈ **~$1.3k/month and was growing ~8 TiB/day** — a silent
cost leak, and the bucket would have kept climbing. Violates the cost-discipline spirit of "no fire-and-forget VM
launches". The whole-file re-upload also burns redundant egress + Class-A write ops on every running VM independent of
the storage bloat.

## Action taken (2026-06-01)

- ✅ **Soft-delete disabled bucket-wide** (`gcloud storage buckets update <bucket> --clear-soft-delete`; was 604800 s /
  7 d → `retentionDurationSeconds: 0`). Stops new shadow copies immediately; the existing 56 TiB ages out by
  **~2026-06-08**. Reversal: `gcloud storage buckets update <bucket> --soft-delete-duration=7d`. Operator-confirmed: no
  file in this bucket needs soft-delete retention.

## Recommended decision / tracked follow-ups

- [x] ✅ [INFRA] P1. **DONE 2026-06-01 (slot 7) — VM `run.log` re-upload churn fixed.** `LogUploader.upload_once()` now
      re-uploads only when the log grew by ≥ `min_growth_bytes` (default 256 KiB) instead of byte-for-byte-changed, and
      the default interval is 30 s → 120 s; idle-skip + shrink/rotation re-sync preserved; `final_upload()` still flushes
      the full tail on exit; +5 unit tests bound upload cadence/volume. **unified-trading-library@`2bfb6a16`** (uploader
      + tests) + **deployment-service@`130c85c`** (heartbeat_cli upload-interval default 30→120). Both QG-green for the
      touched files (deployment-service has 1 pre-existing foreign failure — see flake note below).
- [x] ✅ [INFRA] P1. **DONE 2026-06-02 (slot 1) — tarball reaper LIVE + verified.** `tarball_cleanup_scheduler.tf`
      (deployment-service@`840c9a5`, slot 7) `terraform apply -target`'d against the real prod state (`terraform/state/prod`,
      NOT `shared-infrastructure` — see landmine item) → `uts-prod-tarball-cleanup` Cloud Run Job + `uts-prod-tarball-cleanup-cron`
      (daily `0 2 * * *` UTC). Image repointed to `unified-trading-system/deployment-service:latest` (the MTDS image had no
      deployment-service source → exit 2); arg path fixed `deployment-service/scripts/...` → `scripts/...` (WORKDIR /app).
      **`gcloud run jobs execute` → succeeded=1; cron ENABLED.** deployment-service@`2ab4cce` (TF + Dockerfile). Runbook
      block still TODO (P3 below).
- [x] ✅ [INFRA] P0. **DONE 2026-06-02 (slot 1) — `deployment-service` jobs image built + published.** There was **no
      `deployment-service` image in Artifact Registry**. Added Dockerfile `maintenance-jobs` stage (api stage + `scripts/`
      + the 3 PyPI deps the eager backends import needs but the `--no-deps` UTL base lacks: `jinja2` (vm_config),
      `flask`+`functions-framework` (cloud-functions backend); could NOT `uv pip install -e .` WITH deps because the
      lockfile pins workspace path-deps like `file:///unified-trading-library` absent in the image). New
      `cloud-build/deployment-service-jobs-image.cloudbuild.yaml` publishes
      `unified-trading-system/deployment-service:latest` (one GCP project serves all envs). Both jobs repointed; both
      verified (`uts-prod-tarball-cleanup` succeeded; `vm-log-archival-prd` t8j2d **succeeded** after the deps fix —
      was exit(1) on import before). `vm_log_archival` given `deletion_protection=false`. deployment-service@`2ab4cce`
      (slot `46eacdf`).
- [x] ✅ [INFRA] P2. **DONE 2026-06-02 (slot 1)** Fixed `bootstrap_gcp.sh` stale backend prefix —
      `prefix=shared-infrastructure` (EMPTY, 0 resources) → `prefix=terraform/state/${ENV}` (the real per-env state; prod
      has 198 resources). Old value would 409 on every SA/scheduler. (`main.tf`'s backend comment was already correct —
      `terraform/state/<env>` — so only the script needed fixing.) deployment-service@`e38524a`.
- [x] ✅ [TEST] P2. **(fixed 2026-06-02, slot 1)** deployment-service date-window flake fixed —
      `test_fixture_within_window_returned` built kickoff via `now.replace(hour=(now.hour+2)%24)`, which wraps to the
      early morning of the SAME day at ≥22:00 UTC → lands in the past, outside the 48h window. Now uses
      `now + timedelta(hours=2)` (time-of-day independent) + dropped a duplicate `get_storage_client` patch.
      **deployment-service@`79a40f6`** | QG-green (212s, 4/4 in file pass). (Was R3 in `issue_docs_remediation_sweep_2026_06_02.md`,
      left for pickup "if their fix does not land" — it had not landed; 0 incoming on the file.)
- [ ] [INFRA] P2. Add prefix-scoped lifecycle rules to `gs://deployment-scripts-<pid>` (zero rules today). Delete
      `vm-logs/` live objects > 14 d and `log-archive/` > 90 d (currently indefinite). **STATUS 2026-06-02 (slot 1):
      now UNBLOCKED — `vm-log-archival-prd` cron is ENABLED + verified (snapshot-before-delete is satisfied). Safe to add
      the `vm-logs/`>14d + `log-archive/`>90d rules now; recommend letting the daily archival run ≥1 prod cycle first,
      then add via `--lifecycle-file`/terraform.** (Note: the bucket-wide soft-delete clear from 2026-06-01 already drains
      the 56 TiB by ~06-08 independently of this.)
- [x] ✅ [INFRA] P2. **(audit RAN 2026-06-02, slot 1)** Cross-bucket soft-delete + versioning audit complete —
      `gcs_bucket_stats.py --out /tmp/gcs_bucket_bloat_audit_20260602.csv` walked 295 buckets (95 non-empty, 120.4 TiB).
      **Findings:** `deployment-scripts` 58,511 GiB @ 99.9% is **all soft-deleted** (58.4 TiB; the known churn, still
      present, ages out ~2026-06-08 — fix stopped *new* growth). TF-state buckets (`uts-terraform-state` 96%,
      `terraform-state` 31.5%) + `strategy-store-*` (100% but ≪1 GiB) are intentional versioning — no action. Three real
      secondary offenders (~1.2 TiB) → tracked in the new P1 below.
- [x] ✅ [INFRA] P1. **DONE 2026-06-02 (slot 1) — secondary bloat buckets (~1.2 TiB) remediated.** **(a) soft-delete
      churn** — `instruments-store-sports` (296 GiB) + `instruments-store-sports-prd` (300 GiB) were ~96% soft-deleted:
      `gcloud storage buckets update --clear-soft-delete` on both (retention 604800→0; mass ages out). **(b) noncurrent
      versioning** — `client-reporting-data` (471 GiB) given a conservative lifecycle (delete noncurrent `daysSinceNoncurrentTime=90`
      AND `numNewerVersions=5` — keeps recent client history); `instruments-store-defi` (96 GiB) given
      `daysSinceNoncurrentTime=7` (reference data). Applied via gcloud (immediate); evidence CSV:
      `/tmp/gcs_bucket_bloat_audit_20260602.csv`.
- [ ] [INFRA] P2. **(follow-ups from the bloat remediation)** (1) Find + fix the `instruments-store-sports` overwrite
      *writer* (a fixtures/odds re-write loop) so it stops churning — clearing soft-delete stopped the retention bloat
      but not the redundant writes. Repo: instruments-service. (2) Codify the gcloud-applied lifecycle/soft-delete
      settings (sports clear; defi 7d; client 90d/keep-5) into the owning repo's bucket terraform so they survive a
      bucket re-apply and apply in every env. Repo: deployment-service/terraform (or instruments-service bucket TF).
- [ ] [INFRA] P3. **(discovered 2026-06-02, slot 1)** Declare `jinja2`, `flask`, `functions-framework` in
      deployment-service `pyproject.toml [project.dependencies]` (they're imported by the backends chain but undeclared —
      currently installed explicitly in the Dockerfile `maintenance-jobs` stage as a workaround). Also add a
      `owner/cadence/verifier/last_executed` runbook block for the tarball-cleanup + vm-log-archival jobs, and a
      cloud-build trigger so `deployment-service:latest` refreshes automatically. Repo: deployment-service.

## Verification

- `python3 unified-trading-pm/scripts/migration/gcs_bucket_stats.py` — `deployment-scripts` `total_GiB` should fall from
  57,516 toward ~66 GiB by ~2026-06-08 (soft-deleted ages out) and `bloat_pct` toward ~0.
- `gcloud storage buckets describe <bucket> --format='value(softDeletePolicy.retentionDurationSeconds)'` → `0`.
