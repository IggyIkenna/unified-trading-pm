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
- [ ] [INFRA] P1. Schedule `cleanup_old_tarballs.py` (deployment-service/scripts/vm/) — 366 live `@sha` tarballs
      accumulate unbounded. **STATUS 2026-06-02 (slot 1): TF applied to prod but jobs DO NOT RUN — `BLOCKED` on the
      image fix below.** `tarball_cleanup_scheduler.tf` (deployment-service@`840c9a5`, slot 7) authored the job+cron; I
      `terraform apply -target`'d it against the real prod state (`terraform/state/prod`, NOT `shared-infrastructure` —
      see landmine note) → `uts-prod-tarball-cleanup` Cloud Run Job + `uts-prod-tarball-cleanup-cron` created. **A
      one-shot `gcloud run jobs execute` FAILED with container exit(2)** — the job's image is
      `unified-trading-system/market-tick-data-service:latest`, whose Dockerfile is `COPY . .` (MTDS source only;
      `deployment_service` is not a dep), so the `python deployment-service/scripts/vm/cleanup_old_tarballs.py` file path
      does not exist in the image. **Cron PAUSED** (`gcloud scheduler jobs pause uts-prod-tarball-cleanup-cron`) to stop
      daily exit-2 failures until the image is fixed. Add an `owner/cadence/verifier/last_executed` runbook block once
      it actually runs. QG deployment-service.
- [ ] [INFRA] P0. **(discovered 2026-06-02, slot 1)** Build + publish a `deployment-service` container image and point
      the deployment-service-script Cloud Run Jobs at it. ROOT CAUSE of the two broken jobs above: there is **no
      `deployment-service` image in Artifact Registry** (only `unified-trading-system/<service>:latest` per-service
      images + `unified-trading-library/unified-trading-library:latest`). `tarball_cleanup_scheduler.tf` and
      `vm_log_archival_scheduler.tf` both reference images that cannot run their commands — tarball uses the MTDS image
      (no deployment-service source); `vm_log_archival_scheduler.tf` references
      `unified-trading-library/deployment-service:latest` which **does not exist at all** (its job creation errored
      `Image ... not found` so the job + its cron were never created). Fix: (a) `deployment-service/Dockerfile` exists —
      build + push `…/unified-trading-system/deployment-service:latest` (add a cloud-build trigger like the other
      services), (b) repoint both TF files' `image =` to it, (c) re-`terraform apply -target`, (d) un-pause
      `uts-prod-tarball-cleanup-cron`, (e) verify both jobs with a one-shot `gcloud run jobs execute … --wait` exit 0.
      Alternative if a deployment-service image is unwanted: move `cleanup_old_tarballs.py` + `vm_log_archival_cron.py`
      into UTL and invoke as `python -m unified_trading_library…` (the pattern `consolidator_liveness` uses on the MTDS
      image). Repos: deployment-service (TF + Dockerfile/cloud-build). Terraform state: `terraform/state/prod`.
- [ ] [INFRA] P2. **(discovered 2026-06-02, slot 1)** Fix `bootstrap_gcp.sh` stale backend prefix — it inits with
      `-backend-config="prefix=shared-infrastructure"`, but that state is **EMPTY (0 resources)** while the live prod
      resources (198) are under `prefix=terraform/state/prod`. Anyone running `bootstrap_gcp.sh` against prod would try
      to recreate every resource (SAs, schedulers) → 409 conflicts + a bogus parallel state. Align the script (and the
      misleading `main.tf` backend comment, which says `terraform/state/<env>`) to the actual prod prefix. Repo:
      deployment-service.
- [x] ✅ [TEST] P2. **(fixed 2026-06-02, slot 1)** deployment-service date-window flake fixed —
      `test_fixture_within_window_returned` built kickoff via `now.replace(hour=(now.hour+2)%24)`, which wraps to the
      early morning of the SAME day at ≥22:00 UTC → lands in the past, outside the 48h window. Now uses
      `now + timedelta(hours=2)` (time-of-day independent) + dropped a duplicate `get_storage_client` patch.
      **deployment-service@`79a40f6`** | QG-green (212s, 4/4 in file pass). (Was R3 in `issue_docs_remediation_sweep_2026_06_02.md`,
      left for pickup "if their fix does not land" — it had not landed; 0 incoming on the file.)
- [ ] [INFRA] P2. Add prefix-scoped lifecycle rules to `gs://deployment-scripts-<pid>` (zero rules today). Delete
      `vm-logs/` live objects > 14 d and `log-archive/` > 90 d (currently indefinite). **STATUS 2026-06-02 (slot 1):
      `BLOCKED` on the P0 image fix — `vm-logs/`>14d deletion is only safe once `vm_log_archival_cron` actually runs
      (snapshot-before-delete), and that job can't be created/run until the deployment-service image exists. Do NOT add
      the vm-logs deletion rule until archival is live + verified.** Set via `--lifecycle-file` or terraform.
- [x] ✅ [INFRA] P2. **(audit RAN 2026-06-02, slot 1)** Cross-bucket soft-delete + versioning audit complete —
      `gcs_bucket_stats.py --out /tmp/gcs_bucket_bloat_audit_20260602.csv` walked 295 buckets (95 non-empty, 120.4 TiB).
      **Findings:** `deployment-scripts` 58,511 GiB @ 99.9% is **all soft-deleted** (58.4 TiB; the known churn, still
      present, ages out ~2026-06-08 — fix stopped *new* growth). TF-state buckets (`uts-terraform-state` 96%,
      `terraform-state` 31.5%) + `strategy-store-*` (100% but ≪1 GiB) are intentional versioning — no action. Three real
      secondary offenders (~1.2 TiB) → tracked in the new P1 below.
- [ ] [INFRA] P1. **(discovered 2026-06-02, slot 1 — from the cross-bucket audit)** Triage + fix the secondary bloat
      buckets (~1.2 TiB). Two leak classes: **(a) soft-delete churn** — `instruments-store-sports` (296 GiB) +
      `instruments-store-sports-prd` (300 GiB) are ~96% **soft-deleted** (same pattern as deployment-scripts: a writer
      overwrites objects with soft-delete on). Find the writer (likely a fixtures/odds re-write loop), then
      `--clear-soft-delete` if nothing needs 7-day retention. **(b) noncurrent versioning** — `client-reporting-data`
      (471 GiB, 100% noncurrent) + `instruments-store-defi` (96 GiB noncurrent): versioning on, old versions accumulate
      unbounded; add a `num_newer_versions`/`noncurrent_time_before` lifecycle rule if unintentional. Evidence:
      `/tmp/gcs_bucket_bloat_audit_20260602.csv`. Repos: instruments-service (writers) + deployment-service/terraform
      (lifecycle). Per *Data Pipeline Correctness Is The Heartbeat* — every accidental leak fixed in full.

## Verification

- `python3 unified-trading-pm/scripts/migration/gcs_bucket_stats.py` — `deployment-scripts` `total_GiB` should fall from
  57,516 toward ~66 GiB by ~2026-06-08 (soft-deleted ages out) and `bloat_pct` toward ~0.
- `gcloud storage buckets describe <bucket> --format='value(softDeletePolicy.retentionDurationSeconds)'` → `0`.
