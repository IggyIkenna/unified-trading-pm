---
doc_type: issue
title: >-
  VM startup/helper scripts have NO auto-rollout to GCS — shipped fixes silently do not reach VMs until
  create-code-tarballs.sh is run by hand
summary: >-
  VMs boot their startup script and heartbeat helpers by pulling them directly from
  gs://deployment-scripts-<project>/vm/ at boot. Nothing auto-uploads those files on commit — not quickmerge, not a git
  hook, not CI. They only reach GCS when someone runs create-code-tarballs.sh (which cp-s them at lines ~445-447). So
  git and GCS drift: a change committed and pushed to LDR keeps running the OLD version on every VM until a manual
  rollout. Found 2026-07-19 when a freshly-shipped multi-process fan-out did NOT activate (the VM booted the stale GCS
  startup script), and the audit then found deployment_heartbeat.py was 68 lines behind git in GCS too. The CODE
  tarballs do NOT have this problem — they self-heal via lc_verify_tarball_freshness at launch.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [vm-launcher, gcs, rollout, deployment-correctness, did-we-reload-the-code]
related:
  [
    /plans/archive/issues/backfill_vm_disk_starvation_misdiagnosed_as_tardis_quota_2026_07_18.md,
    /plans/archive/issues/launcher_gcloud_continuation_broken_by_disk_sweep_2026_07_18.md,
  ]
created: 2026-07-19
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: devops
drift_direction: advance-code
depends_on: []
source:
  [
    "discovered 2026-07-19 when a shipped multi-process fan-out did not activate — the VM booted a stale GCS copy of
    setup-data-pipeline-vm.sh",
  ]
resolved_by:
locked_by:
---

# VM startup/helper scripts have no auto-rollout to GCS

## What happens

The cefi backfill launcher (and every launcher that uses the shared data-pipeline startup script) sets
`startup-script-url=gs://deployment-scripts-<project>/vm/setup-data-pipeline-vm.sh`. The VM downloads that object at
boot and runs it; the startup script in turn `gsutil cp`-s its helpers (`vm-exec-with-gcs-tee.sh`,
`deployment_heartbeat.py`, `heartbeat_daemon.py`, `vm_heartbeat_sidecar.sh`) from the same `gs://.../vm/` prefix.

**Nothing keeps `gs://.../vm/` in sync with git.** `quickmerge` lands code on the integration branch; it does not upload
these files. There is no git hook and no GitHub Actions job that uploads them. The only thing that writes them is a
manual `bash scripts/vm/create-code-tarballs.sh` run (it cp-s them at roughly lines 445-447). If that is not run after a
change, every VM keeps booting the old version.

This is the concrete mechanism behind the recurring "did we reload the code?" question.

## Evidence (2026-07-19)

- A multi-process fan-out was committed to LDR, QG-green, verified on the remote — but the first test VM booted with
  `workers=0` and single-process throughput. The GCS copy of `setup-data-pipeline-vm.sh` had `0` occurrences of the new
  `_FANOUT` code. Manually uploading it made the feature activate on the next launch.
- The follow-up audit (git HEAD vs the GCS copy, per file) found `deployment_heartbeat.py` **68 diff lines behind git**
  — a peer's committed change (`0676ba1 re-land the UTL relocation so VMs reach the dual-write registry`) that had never
  been re-uploaded, so VMs were emitting deployment events through the old registry path. Synced it to git HEAD as part
  of the audit.

## What is NOT affected

The per-service **code tarballs** (the pip-installed packages: MTDS, UTL, etc.) DO self-heal:
`lc_verify_tarball_freshness` checks/rebuilds them at launch, so this session's MTDS code fixes (event-loop off-loop,
fetch/parse decoupling, connection pool) were verified live on the VM. The gap is specific to the `vm/` startup + helper
scripts, which have no equivalent freshness check.

## Fix options (for operator decision)

1. **Add the `vm/` upload to the ship path.** Make quickmerge (or a dedicated post-merge CI job) run the `gsutil cp` of
   every `deployment-service/scripts/vm/*.sh` + `*.py` that is GCS-hosted whenever one of them changes on the
   integration branch. Smallest blast radius: a CI job triggered on changes under `deployment-service/scripts/vm/`.
2. **Give the startup scripts a freshness check like the code tarballs.** Have each launcher verify the GCS copy's hash
   against the committed file before launch and re-upload if stale (mirrors `lc_verify_tarball_freshness`). More robust
   but more code.
3. **Interim / always-safe:** document as a HARD step that any change to a `vm/` startup or helper script MUST be
   followed by `bash scripts/vm/create-code-tarballs.sh` (or the targeted upload), and add it to the ship checklist for
   those paths. This is the minimum until (1) or (2) lands.

## Immediate state

All GCS-hosted `vm/` scripts were re-synced to git HEAD on 2026-07-19 during the audit (`setup-data-pipeline-vm.sh`,
`vm-exec-with-gcs-tee.sh`, `deployment_heartbeat.py`, `heartbeat_daemon.py`, `setup-cefi-live-consolidated-vm.sh` all
verified FRESH). So the fleet is currently in sync; the open work is the DURABLE fix so it stays in sync automatically.

## Todos

> Added 2026-07-26 by `/plan-reconcile` (infra shard). This doc was `priority: P1`, `status: open`, with **zero
> checkboxes** — its work existed only as prose under "Fix options (for operator decision)", so nothing here was visible
> to the hygiene/dispatch surface (the sweep class is
> `/plans/active/issues/issue_docs_zero_checkbox_sweep_2026_07_24.md` todo 3). **No option was chosen** — picking
> between the doc's own three fix shapes is an authority call with real blast-radius differences (ship-path change vs
> per-launcher freshness check vs process-only), so it is captured below as an `[OPERATOR]`-gated decision exactly per
> `task_template.md`'s bounded-outcome rule, and raised as a `/plan-reconcile` operator question in the same pass.

- [ ] [OPERATOR] P1. **Rule on which durable fix shape to build** for "a committed change to a GCS-hosted
      `deployment-service/scripts/vm/` startup/helper script must reach `gs://deployment-scripts-<project>/vm/`
      automatically". The three options are stated verbatim in § "Fix options (for operator decision)" above: **(1)** a
      CI job triggered on changes under `deployment-service/scripts/vm/` that `gsutil cp`s the changed files (smallest
      blast radius); **(2)** a per-launcher freshness check mirroring `lc_verify_tarball_freshness` (more robust, more
      code); **(3)** interim/process-only — document the manual `bash scripts/vm/create-code-tarballs.sh` step as a HARD
      post-change requirement in the ship checklist (the doc itself calls this "the minimum until (1) or (2) lands", not
      a substitute for them). **Done when**: one option is recorded in this doc with a dated operator line, and the
      chosen option is written up as its own bounded implementation todo here. Repo: deployment-service (+
      unified-trading-pm if (3) adds a checklist/codex step).
