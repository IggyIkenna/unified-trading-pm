---
doc_type: issue
title:
  "create-code-tarballs.sh's gsutil upload step fails under an expired Identity-Pool (WIF) token when run from an
  interactive AO slot session — the active gcloud account is CI-oriented, not slot-oriented"
summary:
  "bash scripts/vm/create-code-tarballs.sh --include instruments-service --include deployment-service (run from
  .tabs/4/deployment-service, slot 4, 2026-07-25) built all 5 tarballs locally but failed 10/10 gsutil uploads with
  repeated 'Unable to retrieve Identity Pool subject token ... token has invalid claims: token is expired'. The active
  gcloud CLI account in this slot's config is github-actions-deploy@central-element-323112.iam.gserviceaccount.com (a
  Workload-Identity-Federation service account meant for short-lived CI runner sessions), not an account backed by the
  slot's own long-lived Application Default Credentials (~/.config/gcloud/application_default_credentials.json, which
  DOES work fine for direct google-cloud-storage/compute Python SDK calls — confirmed working throughout this session).
  gsutil/gcloud storage commands route through the ACTIVE ACCOUNT's credential, not ADC, so they hit the expired WIF
  token while direct Python SDK calls (via unified_trading_library.get_storage_client()) succeed. A secondary human
  account (ikenna@odum-research.com) is also configured but requires interactive reauth ('Reauthentication failed.
  cannot prompt during non-interactive execution'), unusable from an unattended worker. Net effect: any interactive AO
  worker slot that needs to rebuild+upload VM code tarballs via the sanctioned create-code-tarballs.sh launcher will hit
  this same failure until the active account is switched to one with a valid non-interactive credential, or the
  script/launcher tooling is changed to route gsutil calls through ADC directly. This did NOT block the specific task in
  progress (sports_satellite_ao_dispatch_batch2-005, INJURIES enrichment backfill) because the tarballs already existed
  fresh (rebuilt by another process ~35 minutes earlier), but it WILL block the next slot/session that needs a genuinely
  fresh tarball rebuild+upload from an interactive session with no other recent rebuild to fall back on."
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags:
  [vm-tarball-deployment, gcloud-auth, workload-identity-federation, gsutil, interactive-slot, spot-vms-for-backfill]
related:
  [
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /plans/active/issues/tarball_rotation_breaks_vm_recovery_2026_07_20.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
  ]
created: 2026-07-25
last_updated: 2026-07-25
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: "deployment-service@74f22b9 -- all 4 todos done, wider sweep complete, quality-gates.sh green"
source:
  "Found while launching an INJURIES enrichment backfill VM, sports_satellite_ao_dispatch_batch2-005, slot 4, 2026-07-25"
depends_on: []
---

# VM tarball upload fails under an expired WIF token in an interactive AO slot (2026-07-25)

> **🟢 RESOLVED 2026-07-25** — all 4 todos done, including the wider ~150-launcher/gsutil-call-site sweep todo 4 had
> flagged as out-of-scope. Every genuinely host-side `gsutil` call in `deployment-service/scripts/` now routes through
> `gcloud storage` (ADC-backed); every VM-side (heredoc/`VM_BACKFILL_CMD`-embedded) `gsutil` call was deliberately left
> untouched (different, unaffected auth domain). deployment-service@74f22b9, `quality-gates.sh` green.

## What I found

Running `bash scripts/vm/create-code-tarballs.sh --include instruments-service --include deployment-service` from an
interactive AO worker slot (`.tabs/4/deployment-service`) built the 5 requested tarballs locally without error, then
failed all 10 `gsutil cp` uploads (tarball + SHA-pinned copy × 5 repos) with:

```
('Unable to retrieve Identity Pool subject token', '{"source":"actions-run-service","statusCode":401,"errorMessage":"token has invalid claims: token is expired"}')
CommandException: 10 files/objects could not be transferred.
```

`gcloud auth list` shows the ACTIVE account is `github-actions-deploy@central-element-323112.iam.gserviceaccount.com` —
a Workload Identity Federation service account whose token source (`actions-run-service`) is a GitHub-Actions-runner
credential broker, not something a long-lived interactive slot session can refresh on its own. A secondary human
account, `ikenna@odum-research.com`, is also configured but switching to it and calling `gcloud auth print-access-token`
fails with `Reauthentication failed. cannot prompt during non-interactive execution` — also unusable unattended.

Critically, this does NOT affect direct `google-cloud-storage`/`google-cloud-compute` Python SDK calls
(`unified_trading_library.get_storage_client()`, `google.cloud.compute_v1.InstancesClient()`) — those use
`GOOGLE_APPLICATION_CREDENTIALS` (`~/.config/gcloud/application_default_credentials.json`) directly and worked correctly
throughout this session (GCS reads/writes, instance listing). The failure is specific to `gsutil`/`gcloud storage`
shelling out through the CLI's configured ACTIVE ACCOUNT rather than ADC.

Separately, the snap-packaged `gcloud` at `/snap/bin/gcloud` (the one on `PATH` by default in this slot) cannot even run
at all (`snap-confine is packaged without necessary permissions ... cap_dac_override not found`) — a second, independent
environment issue. A working non-snap install exists at `/home/ubuntu/google-cloud-sdk/bin/gcloud` and must be prepended
to `PATH` for any `launch-*.sh` / `create-code-tarballs.sh` script to run at all in this slot.

## Why it matters

Every `deployment-service/scripts/vm/launch-*.sh` launcher and `create-code-tarballs.sh` depends on a working `gcloud`
CLI. Any interactive AO worker slot that needs a genuinely fresh tarball rebuild (not falling back on one recently built
by another process) will hit this exact failure and be unable to complete it — silently degrading every VM launch to
running on stale code until someone notices and works around it by hand (as this session did, by relying on a tarball
another process had _just_ rebuilt minutes earlier — a lucky coincidence, not a fix).

## Recommended decision

Two independent, additive fixes, neither mutually exclusive:

1. **PATH fix (cheap, mechanical)**: document (or wire into slot bootstrap / `.bashrc`) that
   `/home/ubuntu/google-cloud-sdk/bin` must be prepended to `PATH` before invoking any
   `deployment-service/scripts/vm/*.sh` launcher from an interactive slot — the default `/snap/bin/gcloud` cannot run in
   this sandbox at all.
2. **Auth fix (needs an infra decision)**: either (a) provision the slot's gcloud CLI config with a _non-expiring_,
   ADC-backed account as the default ACTIVE account (so `gsutil`/`gcloud storage` route through the same credential that
   already works for direct SDK calls), or (b) patch `create-code-tarballs.sh`'s upload step to use
   `unified_trading_library`'s GCS client (or `gcloud storage cp` with `--impersonate-service-account` pointed at ADC)
   instead of bare `gsutil cp`, which is the CLI's default active-account path.

## Todos

- [x] 1. [INFRA] P2. Fix the PATH issue for interactive AO slots — either document it in the slot bootstrap docs
      (`/codex/05-infrastructure/per-tab-worktrees.md` or the slot setup script) so every worker knows to prepend
      `/home/ubuntu/google-cloud-sdk/bin`, or symlink/alias the non-snap `gcloud` ahead of the snap one in the default
      `PATH` at slot-clone-setup time. (repo: unified-trading-pm docs, or the slot-setup script wherever it lives.) ✅ —
      unified-trading-pm@7b4a3f662. Root cause: `~/.bashrc` already prepends the real SDK's `bin/` via `path.bash.inc`,
      but that only fires in an interactive login shell — a non-interactive shell (an agent's sandboxed Bash tool, cron,
      `claude -p`) never sources `.bashrc` and still resolves the broken snap `gcloud`. Fix: new
      `scripts/dev/install-gcloud-sdk-path-symlinks.sh` symlinks the real SDK's
      `gcloud`/`gsutil`/`bq`/`docker-credential-gcloud` into `~/.local/bin` (already first on `PATH` in every shell
      type, no shell-startup file required); wired into `setup-tab-worktrees.sh --init`; documented in
      `/codex/05-infrastructure/per-tab-worktrees.md` § "gcloud SDK PATH symlinks". Verified live on this host: ran the
      script, then confirmed `command -v gcloud` → `~/.local/bin/gcloud` and `gcloud --version` succeeds in this exact
      sandboxed non-interactive shell (previously resolved to the broken `/snap/bin/gcloud`).
- [x] 2. [INFRA] P2. Fix the WIF-token-expiry auth gap for `create-code-tarballs.sh`'s upload step — either configure a
      non-expiring ADC-backed active gcloud account for interactive slots, or change the upload step to use the UTL GCS
      client (or `gcloud storage` with explicit ADC impersonation) instead of bare `gsutil cp` against the active CLI
      account. Verify with a full `create-code-tarballs.sh` run from a fresh interactive slot session with the
      `github-actions-deploy@...` account still active (reproduce first, then confirm the fix resolves it). ✅ —
      deployment-service@3ba14ff9. Chose the UTL-GCS-client path: added `StorageClient.upload_file()` to
      `deployment_service/cloud/storage_client.py` (delegates to UTL's ADC-backed client) plus a
      `gcs_upload_cli.py`/`gcs_upload_via_adc.py` thin-shim pair (mirrors `heartbeat_daemon.py`'s package-delegation
      pattern); `create-code-tarballs.sh`'s GCP branch now routes every tarball/manifest/launcher upload through this
      helper instead of bare `gsutil cp`. Reproduced first: confirmed `gsutil ls`/`cp` against
      `deployment-scripts-central-element-323112` both fail with "Your credentials are invalid" on this exact host with
      `github-actions-deploy@...` still the active gcloud account. Then verified the fix: uploaded a real object to that
      bucket via the new helper (`gs://deployment-scripts-central-element-323112/tmp/agent-smoketest/`, confirmed
      present + correct size via the UTL client's `list_files_with_metadata`) while `gsutil` itself was still broken on
      the same host in the same session — proves the upload path no longer depends on the CLI's active-account
      credential. `GCP_PROJECT_ID`/`PROJECT_ID` env resolution gap (DeploymentConfig didn't have either set in this
      slot) worked around via an explicit `--project` flag the caller resolves from
      `gcloud     config get-value project` (a local config read, not a live-auth call). Also fixed pre-existing
      pip-audit failure blocking the quality gate (`pyasn1` 0.6.3→0.6.4, PYSEC-2026-3455/3456/3457) — verified the pin
      predated this task's commits, unrelated debt on the shared branch.
- [x] 3. [INFRA] P2. Fixed a 2nd occurrence of the same bug class: `create-code-tarballs.sh`'s own trailing "Uploaded
      files:" verification listing (GCS branch) still called raw `gsutil ls`, so under this exact WIF-token gap the
      LISTING failed and (via `set -e`) took the whole script down non-zero even though every real upload above it had
      already succeeded — a false-failure signal, not a real one. Reproduced live 2026-07-25 (slot 10,
      `sports_satellite_ao_dispatch_batch2-004`): a fresh `--asset-group SPORTS` rebuild uploaded all tarballs +
      manifests + 156 launcher scripts correctly (`gcloud storage ls -l` confirmed fresh timestamps), then exited 127
      when the trailing `gsutil ls` hit the expired token. Fixed by swapping to `gcloud storage ls` (same fix pattern as
      todo 2). ✅ — deployment-service@a12c84a.
- [x] 4. [INFRA] P3. A 3RD occurrence — FIXED. `scripts/vm/lib/launcher_common.sh`'s `lc_verify_tarball_freshness()`
      (pre-launch guard, called by every `launch-*.sh`) and its sibling `lc_resolve_tarball_sha()` both called
      `gsutil -q cp <manifest> ...` / `gsutil -q stat ...` to read a tarball's manifest — under this same WIF-token gap
      the read failed, and `lc_verify_tarball_freshness` treated that as `WARNING: tarball manifest MISSING for <repo>`
      (a FALSE staleness signal) for every repo, every launch, in any interactive slot with the broken active account.
      ✅ — deployment-service@8f996db. Swapped both functions' `gsutil -q cp`/`gsutil -q stat` calls to
      `gcloud storage cp --quiet`/`gcloud storage objects describe` (mirrors todos 2-3's fix; also swapped their
      `command -v gsutil` tooling-precondition checks to `command -v gcloud`). Reproduced first, then verified live on
      this host with the same broken `github-actions-deploy@...` WIF account still active: `gsutil ls` against the code
      bucket failed with "Your credentials are invalid" while `gcloud storage ls` succeeded (ADC); called both fixed
      functions directly — `lc_resolve_tarball_sha` returned a real commit_sha (no false-empty), and
      `lc_verify_tarball_freshness` correctly reported genuine staleness (not a false MISSING) in both `warn` (exit 0,
      non-blocking) and `enforce` (exit 1, blocking) modes for 2 different repos. Updated the 2 unit tests
      (`TestTarballFreshnessGuard::test_fresh_tarball_passes`, `::test_stale_tarball_warn_does_not_block`) plus
      `::test_missing_manifest_enforce_blocks`'s mock from a `gsutil` shell-function stub to a `gcloud` one (they were
      asserting against the old codepath and failed post-fix until updated); `quality-gates.sh` green (12/12
      `TestTarballFreshnessGuard` tests pass). **The wider sweep this todo flagged as out-of-scope — now COMPLETE,
      deployment-service@74f22b9.** Audited every `gsutil` reference across the entire `deployment-service/scripts/`
      tree (145 files) with a heredoc/VM_BACKFILL_CMD- boundary-aware classifier distinguishing genuinely host-side
      (interactive-slot) calls from calls that only ever run ON a VM under its own instance credential (a different,
      unaffected auth domain) or pure echo/comment hint text. Found + fixed 3 more genuinely host-side functions in
      `launcher_common.sh` itself (`lc_write_launch_params`, `lc_write_tarball_pin_record` — both `gsutil -q cp -`
      stdin-pipe writes called by 15+ launchers before `gcloud compute instances create`;
      `lc_verify_setup_script_freshness` — `gsutil hash -m`/ `gsutil stat`/`gsutil cp`, called automatically by
      `lc_gcloud_create` on EVERY Pattern-A launch, the single highest-blast-radius remaining call site) plus
      `lc_gcs_object_age_seconds` (the `lc_refuse_if_vm_alive` VM-name- collision safety guard's staleness check). Fixed
      9 more launch-*.sh/utility scripts with their own direct call sites outside `launcher_common.sh`
      (`launch-qg-snapshot-vm.sh`'s pre-flight gate, `launch-vm-zombie-     watchdog.sh`,
      `launch-mtds-live-{cefi,prediction}-consolidated.sh`, `launch-features-sports-parallel-backfill-     vm.sh`,
      `launch-prediction-{features,pipeline}-vm.sh`, `reap-zombies.sh`'s zombie-reaper staleness check,
      `refresh-tarballs-for-shard-key.sh`, `run-sports-phantom-downstream-chain.sh`, plus the Python utilities
      `analyze_vm_costs.py`/`cleanup_old_tarballs.py`'s `gsutil ls -l` shard-outs) and 4 one-time bootstrap/infra
      scripts (`verify-test-bucket-lifecycle.sh`, `setup-cloud-build-triggers.sh`,
      `configure_audit_bucket_versioning.sh`, `bootstrap_gcp.sh`). Re-ran the classifier after every fix; final sweep
      confirms **zero remaining genuinely host-side `gsutil` call sites** in the whole tree — the only 2 residual
      classifier hits (`launch-funding-ensemble-paper-cron-vm.sh`, `launch-rate-calibration-probe-vm.sh`) were verified
      by reading each file's context to be `VM_BACKFILL_CMD` string content that runs on the VM, not the slot. Updated
      the matching unit-test `gsutil` shell-function/fake-binary mocks to `gcloud` across `test_vm_launcher_scripts.py`
      (`TestSetupScriptFreshnessGuard`, `TestCanonicalMigrationVmRelaunch`, `TestDefiLaunchersSpotPreemptionContract`,
      the qg-snapshot preflight tests) and `test_tarball_pins.py` (`TestRealLauncherOutputShape`'s real-bash-helper
      fixture). Full `quality-gates.sh` green (2675+ passed, 0 failed) before shipping. (repo: deployment-service, 19
      files — `scripts/vm/lib/launcher_common.sh` + the 13 scripts named above +
      `tests/unit/test_vm_launcher_scripts.py` + `tests/unit/test_tarball_pins.py`.)
