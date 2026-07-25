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
status: open
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
resolved_by:
source:
  "Found while launching an INJURIES enrichment backfill VM, sports_satellite_ao_dispatch_batch2-005, slot 4, 2026-07-25"
depends_on: []
---

# VM tarball upload fails under an expired WIF token in an interactive AO slot (2026-07-25)

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

- [ ] 1. [INFRA] P2. Fix the PATH issue for interactive AO slots — either document it in the slot bootstrap docs
      (`/codex/05-infrastructure/per-tab-worktrees.md` or the slot setup script) so every worker knows to prepend
      `/home/ubuntu/google-cloud-sdk/bin`, or symlink/alias the non-snap `gcloud` ahead of the snap one in the default
      `PATH` at slot-clone-setup time. (repo: unified-trading-pm docs, or the slot-setup script wherever it lives.)
- [ ] 2. [INFRA] P2. Fix the WIF-token-expiry auth gap for `create-code-tarballs.sh`'s upload step — either configure a
      non-expiring ADC-backed active gcloud account for interactive slots, or change the upload step to use the UTL GCS
      client (or `gcloud storage` with explicit ADC impersonation) instead of bare `gsutil cp` against the active CLI
      account. Verify with a full `create-code-tarballs.sh` run from a fresh interactive slot session with the
      `github-actions-deploy@...` account still active (reproduce first, then confirm the fix resolves it).
