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
- [ ] [INFRA] P1. Schedule `cleanup_old_tarballs.py` (deployment-service/scripts/vm/) — currently never run (0 cron/TF/
      cloud-build references); 366 live `@sha` tarballs accumulate unbounded. Wire a daily Cloud Scheduler + Cloud Run
      Job (or fold into an existing maintenance cron) running `--keep 5`. (**Docstring fix DONE** deployment-service@`130c85c`
      — `@sha` naming IS adopted, cleanup IS needed; only the TF scheduling remains.) Terraform SSOT:
      deployment-service/terraform/gcp/. Add a `owner/cadence/verifier/last_executed` runbook block. QG deployment-service.
- [ ] [TEST] P2. **(discovered 2026-06-01, slot 7)** deployment-service QG has a pre-existing foreign date-window flake:
      `tests/unit/test_sports_tier3_fixture_diagnostic.py::TestFixtureCalendarDiagnostic::test_fixture_within_window_returned`
      fails (current date moved outside a hardcoded fixture window). Unrelated to VM-infra. Fix the test to use a
      relative/frozen window. Repo: deployment-service.
- [ ] [INFRA] P2. Add prefix-scoped lifecycle rules to `gs://deployment-scripts-<pid>` (zero rules today). Delete
      `vm-logs/` live objects > 14 d and `log-archive/` > 90 d (currently indefinite). Verify the daily
      `vm_log_archival_cron` snapshots `run.log` → `log-archive/rolling/` before the vm-logs deletion window. Set via
      `--lifecycle-file` or terraform. This is the correct per-folder retention mechanism (soft-delete is bucket-wide).
- [ ] [INFRA] P2. Audit soft-delete + versioning policy across ALL project buckets using the new
      `unified-trading-pm/scripts/migration/gcs_bucket_stats.py` `bloat_pct` column. The 2026-05-20 snapshot shows other
      high-bloat buckets (client-reporting-data 99.9%, central-element-323112-data-status-rollups 100%,
      instruments-store-\* 90%+) — confirm each is intentional noncurrent-versioning vs. another accidental churn ×
      retention leak.

## Verification

- `python3 unified-trading-pm/scripts/migration/gcs_bucket_stats.py` — `deployment-scripts` `total_GiB` should fall from
  57,516 toward ~66 GiB by ~2026-06-08 (soft-deleted ages out) and `bloat_pct` toward ~0.
- `gcloud storage buckets describe <bucket> --format='value(softDeletePolicy.retentionDurationSeconds)'` → `0`.
