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

> **🟡 PROCESS NOTE (Ikenna 2026-06-02) — `deployment-service #15` is the wrong delivery vehicle for this work.** PR #15
> (`tab/hkm/3 → staging`) is **756 commits ahead / 2 behind** staging — a slot-branch wholesale-merge, not the focused
> terraform-codify change its title describes. It's been `DIRTY`/stuck for 4h+. A `tab/*` slot branch must NOT PR to
> staging; its work reaches integration via `tab-mirror → LDR` then LDR→staging per-unit. **Recommended: close #15 and
> re-land the bucket-codify change as a small per-unit quickmerge.** Note: **disabling auto-merge on #15 is pointless**
> — it's `DIRTY` so it can't merge anyway, and the required `quality-gates-v2` check (not the toggle) is the gate. The
> underlying bucket work below is still valid; only the PR shape is wrong. Pinged harsh in `_agent_pings.md`.

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
      the default interval is 30 s → 120 s; idle-skip + shrink/rotation re-sync preserved; `final_upload()` still
      flushes the full tail on exit; +5 unit tests bound upload cadence/volume. **unified-trading-library@`2bfb6a16`**
      (uploader + tests) + **deployment-service@`130c85c`** (heartbeat_cli upload-interval default 30→120). Both
      QG-green for the touched files (deployment-service has 1 pre-existing foreign failure — see flake note below).
- [x] ✅ [INFRA] P1. **DONE 2026-06-02 (slot 1) — tarball reaper LIVE + verified.** `tarball_cleanup_scheduler.tf`
      (deployment-service@`840c9a5`, slot 7) `terraform apply -target`'d against the real prod state
      (`terraform/state/prod`, NOT `shared-infrastructure` — see landmine item) → `uts-prod-tarball-cleanup` Cloud Run
      Job + `uts-prod-tarball-cleanup-cron` (daily `0 2 * * *` UTC). Image repointed to
      `unified-trading-system/deployment-service:latest` (the MTDS image had no deployment-service source → exit 2); arg
      path fixed `deployment-service/scripts/...` → `scripts/...` (WORKDIR /app). **`gcloud run jobs execute` →
      succeeded=1; cron ENABLED.** deployment-service@`2ab4cce` (TF + Dockerfile). Runbook block still TODO (P3 below).
- [x] ✅ [INFRA] P0. **DONE 2026-06-02 (slot 1) — `deployment-service` jobs image built + published.** There was **no
      `deployment-service` image in Artifact Registry**. Added Dockerfile `maintenance-jobs` stage (api stage +
      `scripts/` + the 3 PyPI deps the eager backends import needs but the `--no-deps` UTL base lacks: `jinja2`
      (vm_config), `flask`+`functions-framework` (cloud-functions backend); could NOT `uv pip install -e .` WITH deps
      because the lockfile pins workspace path-deps like `file:///unified-trading-library` absent in the image). New
      `cloud-build/deployment-service-jobs-image.cloudbuild.yaml` publishes
      `unified-trading-system/deployment-service:latest` (one GCP project serves all envs). Both jobs repointed; both
      verified (`uts-prod-tarball-cleanup` succeeded; `vm-log-archival-prd` t8j2d **succeeded** after the deps fix — was
      exit(1) on import before). `vm_log_archival` given `deletion_protection=false`. deployment-service@`2ab4cce` (slot
      `46eacdf`).
- [x] ✅ [INFRA] P2. **DONE 2026-06-02 (slot 1)** Fixed `bootstrap_gcp.sh` stale backend prefix —
      `prefix=shared-infrastructure` (EMPTY, 0 resources) → `prefix=terraform/state/${ENV}` (the real per-env state;
      prod has 198 resources). Old value would 409 on every SA/scheduler. (`main.tf`'s backend comment was already
      correct — `terraform/state/<env>` — so only the script needed fixing.) deployment-service@`e38524a`.
- [x] ✅ [TEST] P2. **(fixed 2026-06-02, slot 1)** deployment-service date-window flake fixed —
      `test_fixture_within_window_returned` built kickoff via `now.replace(hour=(now.hour+2)%24)`, which wraps to the
      early morning of the SAME day at ≥22:00 UTC → lands in the past, outside the 48h window. Now uses
      `now + timedelta(hours=2)` (time-of-day independent) + dropped a duplicate `get_storage_client` patch.
      **deployment-service@`79a40f6`** | QG-green (212s, 4/4 in file pass). (Was R3 in
      `issue_docs_remediation_sweep_2026_06_02.md`, left for pickup "if their fix does not land" — it had not landed; 0
      incoming on the file.)
- [x] ✅ [INFRA] P2. **DONE 2026-06-02 — prefix-scoped lifecycle rules APPLIED to
      `gs://deployment-scripts-central-element-323112`** (was zero rules). **Operator decision: 30-day cap on everything
      we retain** (more aggressive than the original `vm-logs/`>14d + `log-archive/`>90d sketch — "if no one reads logs
      in 14d, no reason to keep 180d; increase later if needed"). Applied via
      `gcloud storage buckets update --lifecycle-file`; hard-delete, **no soft-delete** (bucket
      `retentionDurationSeconds=0`, verified). Rules: - `age 14d` → `vm-logs/` (live run-log stream; archival cron
      copies to `log-archive/` before then) - `age 15d` → `vm-heartbeat/` (liveness signal; watchdog only cares about
      freshness) - `age 30d` → `logs/`, `recon-logs/`, `audit-results/`, `migration-bundle/staging/`, `log-archive/`,
      `deployments/archive/` **Deliberately NOT lifecycled** (live operational state / working copies the running system
      reads back — a timer would break it): `deployments/active/` (live VM state, self-deletes on `complete()`),
      `operator_capital_overrides/` (runtime config the DeFi engine reads back), `code/` + `code-packages/` (tarballs a
      relaunched VM pulls — reaper keeps-N), `vm/` + `scripts/` + `audit-scripts/` (launch-time working copies),
      `pre-migration-snapshots/` (DR safety). **Writer audit (2026-06-02)** confirming the above — every prefix traced
      to its producer: `vm-logs/`←UTL `LogUploader.upload_once()`; `log-archive/`←`vm_log_archival_cron.py` (Cloud Run
      `vm-log-archival-prd`, copies to escape the 14d TTL) + `vm_serial_capture_cron.py`; `logs/`←MTDS migration scripts
      (`migrate_cefi_v2.py`, `migrate_defi_canonical.py`, `migrate_tradfi_canonical.py`);
      `recon-logs/`←`launch-manifest-recon-{apply,all}-vm.sh`; `vm-heartbeat/`←`setup-data-pipeline-vm.sh` sidecar;
      `audit-results/`←`post-tier3-fanout-audit.sh`;
      `deployments/{active,archive}/`←`DeploymentsRegistry.{register,heartbeat,complete}()` (`deployments_registry.py`;
      archive read only last 7d via `list_recent_archive(days=7)`);
      `migration-bundle/staging/`←`launch-gcs-migration-bundle-vm.sh`;
      `operator_capital_overrides/`←`colocated_engine.py`. **PENDING: terraform codification** of these imperative
      settings → tracked in the bloat-follow-ups item below (2b). (Soft-delete clear from 2026-06-01 still drains the 56
      TiB by ~06-08 independently; lifecycle acts on live objects only, so the two don't interact.)
- [x] ✅ [INFRA] P2. **(audit RAN 2026-06-02, slot 1)** Cross-bucket soft-delete + versioning audit complete —
      `gcs_bucket_stats.py --out /tmp/gcs_bucket_bloat_audit_20260602.csv` walked 295 buckets (95 non-empty, 120.4 TiB).
      **Findings:** `deployment-scripts` 58,511 GiB @ 99.9% is **all soft-deleted** (58.4 TiB; the known churn, still
      present, ages out ~2026-06-08 — fix stopped _new_ growth). TF-state buckets (`uts-terraform-state` 96%,
      `terraform-state` 31.5%) + `strategy-store-*` (100% but ≪1 GiB) are intentional versioning — no action. Three real
      secondary offenders (~1.2 TiB) → tracked in the new P1 below.
- [x] ✅ [INFRA] P1. **DONE 2026-06-02 (slot 1) — secondary bloat buckets (~1.2 TiB) remediated.** **(a) soft-delete
      churn** — `instruments-store-sports` (296 GiB) + `instruments-store-sports-prd` (300 GiB) were ~96% soft-deleted:
      `gcloud storage buckets update --clear-soft-delete` on both (retention 604800→0; mass ages out). **(b) noncurrent
      versioning** — `client-reporting-data` (471 GiB) given a conservative lifecycle (delete noncurrent
      `daysSinceNoncurrentTime=90` AND `numNewerVersions=5` — keeps recent client history); `instruments-store-defi` (96
      GiB) given `daysSinceNoncurrentTime=7` (reference data). Applied via gcloud (immediate); evidence CSV:
      `/tmp/gcs_bucket_bloat_audit_20260602.csv`.
- [x] ✅ [INFRA] P2. **(follow-ups from the bloat remediation — all 3 sub-parts done; box flipped slot-3 2026-06-02; one
      residual extracted to its own P3 todo below)** **(1) ✅ DONE 2026-06-02 (slot 1) — sports writer characterized:**
      the churn writer is the daily fixtures re-poll `instruments_service/triggers/sports_fixtures_daily_repoll.py` →
      `_write_fixtures_per_league` (per-league GCS sink), which overwrites each day's fixtures parquet on every poll.
      This is _expected_ (fixtures/odds update daily) — not a writer bug; the bloat was soft-delete _retention_ of those
      overwrites, fixed at the bucket level (see (2)). **Write-skip optimization SHIPPED 2026-06-02 (slot 1, operator
      requested):** added `_per_league_fixtures_data_unchanged` (reads on-disk parquet, compares DATA excluding the
      re-stamped `available_at`, round-trip-normalised dtypes); `_write_fixtures_per_league` skips the gated re-write
      when unchanged — opt-in (`bucket=` + `skip_if_unchanged=True`), only the daily re-poll opts in (batch/recovery
      paths untouched). Safety bias: any doubt → write (never skips a real change); skipping also preserves the
      earliest/correct `available_at`. +7 unit tests. instruments-service@`016cc248`. (Also FIXED the 2 pre-existing
      foreign QG failures that this surfaced — both stale test assertions vs canonical behavior: venus available*from
      2020-09-22→2020-10-08 (UAC PROTOCOL_LAUNCH_DATES SSOT) + canonicalize_league_id passthrough example
      EPL_99999→EPL_88 (5-digit now strips via UAC Step 3a; 1-2 digit passthrough intact).
      instruments-service@`aeebb8cb`; **instruments-service QG now fully GREEN**.) **(2) ✅ DONE 2026-06-02 (slot 1) —
      instruments-store bucket settings codified + applied:** `terraform/gcp/main.tf` now sets
      `soft_delete_policy{retention_duration_seconds=0}` + a noncurrent Delete lifecycle
      (`days_since_noncurrent_time=30, num_newer_versions=3`) on all 5 instruments-store buckets
      (cefi/tradfi/defi/sports/prediction); `terraform import`'d sports+prediction (were live but untracked in
      `terraform/state/prod`) + applied in-place; all 5 verified `soft_delete=0` live. deployment-service@`be6df48`.
      **Remaining → extracted + investigated as the dedicated P3 todo below (slot-3 2026-06-02):**
      `instruments-store-sports-prd` + `client-reporting-data` are NOT in workspace TF (created out-of-band) — their
      gcloud settings stand (live protection in place); codify per the P3 todo. (3) **Codify the `deployment-scripts`
      bucket lifecycle into terraform** (the 30d-cap rules applied 2026-06-02 are imperative-only). **BLOCKER / design
      note (slot-3 2026-06-02):** the `deployment-scripts-<pid>` bucket is **not in TF at all** + is a **singleton**
      (one physical bucket in the central project) while `terraform/gcp` applies per-env (dev/staging/prod state
      prefixes), so a naïve `google_storage_bucket` resource would (a) try to \_create* an existing bucket → 409 on the
      next apply, and (b) be claimed by 3 separate state files. Recipe for a **TF-capable host** (this slot has neither
      `terraform` nor `tofu`): add `resource "google_storage_bucket" "deployment_scripts"` to `terraform/gcp/main.tf`
      matching live settings (location `ASIA-NORTHEAST1`, STANDARD, **UBLA off** / fine-grained ACLs, no versioning,
      `force_destroy=false`, `soft_delete_policy { retention_duration_seconds = 0 }`, the three `lifecycle_rule` blocks
      = 14d `vm-logs/`, 15d `vm-heartbeat/`, 30d
      `logs/`+`recon-logs/`+`audit-results/`+`migration-bundle/staging/`+`log-archive/`+`deployments/archive/`)
      **guarded to the central project only** (e.g. `count = var.project_id == "central-element-323112" ? 1 : 0`) + a TF
      1.5 `import {}` block (`id =     "deployment-scripts-central-element-323112"`) so the prod-state apply _adopts_
      rather than creates; then `terraform plan` against `prefix=terraform/state/prod` MUST show **no changes** before
      commit. Until then the live lifecycle is safe (no TF resource exists that could overwrite it). **✅ DONE
      2026-06-02 (slot 1 — had terraform):** added the central-project-guarded
      `google_storage_bucket.deployment_scripts` (count) to `terraform/gcp/main.tf` matching live exactly (UBLA off, no
      versioning, soft_delete=0, the 3 prefix Delete rules); `terraform import`'d into `terraform/state/prod` + applied
      (labels-only diff; lifecycle + soft-delete confirmed unchanged: 3 rules, soft_delete=0).
      deployment-service@`75012d3`. Future prod-state applies now preserve the lifecycle.
- [x] ✅ [INFRA] P3. **DONE 2026-06-02 (slot 1)** Declared `jinja2` in deployment-service `pyproject.toml` (`flask` +
      `functions-framework` were already declared) AND regenerated `uv.lock` — which also finished the `deployment-api`
      circular-dep removal's lockfile cleanup (`63bd807` changed pyproject but never re-locked, leaving 6 stale
      deployment-api transitive refs: `yfinance`/`websocket-client`/`ujson`/`u-msgpack-python`/`zope-interface`).
      Result: jinja2 present, 0 stale refs, `uv lock --check` passes (220 packages, was out-of-sync before).
      deployment-service@`479a3e2`. (The Dockerfile `maintenance-jobs` explicit install of all 3 stays — required
      because the api stage installs deployment_service with `--no-deps`.)
- [x] ✅ [INFRA] P2. **DONE 2026-06-02 (slot 1)** deployment-service QG was **pre-existing RED** (codex 9>8) on a
      foreign cloud-SDK import: `deployment_service/vm/gcp_instance_lister.py` did `from google.cloud import compute_v1`
      directly (STEP 5.10). **Fixed by routing through UTL** — `get_compute_engine_client().aggregated_list_instances()`
      (the `compute_v1` call lives properly inside `unified_trading_library.cloud_interface/providers/gcp_compute.py`;
      note `unified-cloud-interface` was merged INTO UTL, so the canonical path is
      `unified_trading_library.cloud_interface`; `get_compute_engine_client` isn't re-exported at UTL top level so the
      deep import carries the sanctioned `# noqa: qg-deep-import`, matching `cleanup_old_tarballs.py`). Same
      read-only/failure-isolated behavior; tests updated to mock the UTL client. **QG now GREEN** (155s, codex 7<8, STEP
      5.10 clean, 3/3 lister tests pass). deployment-service@`80de01c`.
- [x] ✅ [INFRA] P3. **DONE 2026-06-02 (slot 1)** Runbooks + auto-refresh trigger.
      `runbooks/tarball_cleanup_maintenance.md` updated (last_executed=2026-06-02 verified, cron ENABLED, fixed stale
      dry-run path) + `runbooks/vm_log_archival_maintenance.md` created — both carry the 4 mandatory fields
      (owner/cadence/verifier/last_executed). Cloud Build trigger `deployment-service-jobs-image-build` created
      (`iggyikenna-github` connection, push `^main$`, `includedFiles` scoped to
      Dockerfile/cloudbuild-config/`scripts/vm/**`/ pyproject/uv.lock) → `deployment-service:latest` auto-rebuilds on
      main. deployment-service@`0916b35`. **Residuals RESOLVED 2026-06-02 (slot 1):** (a) trigger codified in TF —
      standalone `google_cloudbuild_trigger.deployment_service_jobs_image` in `terraform/cloud-build/gcp/main.tf`
      pinning the live `iggyikenna-github` connection (NOT the module's stale `ln` default); `terraform import`'d → plan
      shows no changes. (b) digest auto-resolve — the jobs-image cloudbuild now has an explicit push step + a
      `redeploy-jobs` step that `gcloud run jobs update`s both maintenance jobs to the fresh `:latest` after each push
      (Cloud Build SA granted `roles/run.developer` + `iam.serviceAccountUser` on `unified-trading-sa`); verified
      end-to-end (build `1c684ffc` re-resolved both jobs). deployment-service@`c1c56cd`. **Pre-existing note (not
      introduced here):** the 13 module-based service triggers in that state still default to the dead `ln` connection —
      a separate foreign drift, left untouched.
- [x] ✅ [INFRA] P3. **DONE 2026-06-02 (slot-3) — both out-of-band buckets codified in `terraform/state/prod`.**
      (Blocker resolved by installing terraform 1.9.8 locally.) Added central-project-guarded `google_storage_bucket`
      resources to `deployment-service/terraform/gcp/main.tf` matching live exactly, `terraform import`'d both into
      `terraform/state/prod`, and applied — **plan: 0 add, 2 change (labels-only), 0 destroy**; live settings verified
      unchanged post-apply. **`client-reporting-data`**: `soft_delete=604800` (7d KEPT) + noncurrent lifecycle
      (`daysSinceNoncurrentTime=90, numNewerVersions=5`). **`instruments-store-sports-prd`** (NEW canonical sports
      bucket — NOT a duplicate): `soft_delete=0`, no lifecycle, matched live. **deployment-service@`b012ea5`** → staging
      PR [#15](https://github.com/IggyIkenna/deployment-service/pull/15) (auto-merge enabled; QG green 70s). Future
      prod-state applies now preserve both buckets' settings. (Note: `instruments-store-sports-prd` codified at its
      current live shape — versioning off / no lifecycle; if the new canonical bucket should later match the other 5
      instruments-store buckets' versioning+noncurrent-lifecycle, that's a separate migration-config decision, not this
      durability codification.)

## Verification

- `python3 unified-trading-pm/scripts/migration/gcs_bucket_stats.py` — `deployment-scripts` `total_GiB` should fall from
  57,516 toward ~66 GiB by ~2026-06-08 (soft-deleted ages out) and `bloat_pct` toward ~0.
- `gcloud storage buckets describe <bucket> --format='value(softDeletePolicy.retentionDurationSeconds)'` → `0`.
