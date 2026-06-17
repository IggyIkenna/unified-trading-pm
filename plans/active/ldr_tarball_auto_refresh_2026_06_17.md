---
title: LDR → VM-deployment tarball auto-refresh (Cloud Run Job + cron)
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
status: active
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
priority: P2
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# LDR → VM-deployment tarball auto-refresh

## What + why

VM-deployment **tarballs** (`gs://deployment-scripts-{project}/code/*-code.tar.gz`, fetched by
`setup-data-pipeline-vm.sh`) are the **rapid-dev** delivery path — they must track
`live-defi-rollout`. Re-running `create-code-tarballs.sh` manually on every ship was a treadmill,
and it tars the **working tree**, so a dirty foreign-WIP clone blocks it. **Prod is unaffected** —
prod runs Docker **images off `main`** (stable); this is only the dev/tarball path. Operator
decision 2026-06-17: tarballs should self-refresh from LDR on a cron, across the board.

## Design (shipped)

A Cloud Scheduler cron (`*/30`) fires a Cloud Run Job (`code-tarball-refresh`) that runs
`deployment-service/scripts/vm/refresh_code_tarballs.sh`:

- **SHA-skip** — `git ls-remote` each repo's LDR tip vs its uploaded `{tarball}.manifest.json`
  `commit_sha`; only **changed** repos are rebuilt. Idle ticks are cheap (ls-remote only).
- **Clean-by-construction** — clones each changed repo **fresh at `origin/live-defi-rollout`**
  (a dirty host working tree is irrelevant; sidesteps the dirty-tree block).
- **Reuses the builder** — `create-code-tarballs.sh` SKIPs any repo absent from the workspace,
  so cloning only the changed repos into a temp workspace and running `--all` rebuilds exactly
  the changed set — no fork of the tar/manifest/naming logic.
- **Bounded parallel** (`MAX_PAR=4`) — serial (~3-4 min/repo, clone-bound) can't keep up with
  LDR churn (~9-11 repos change between runs); 4-at-a-time is ~5.5× faster (10 repos in ~7 min)
  so a `*/30` run finishes well inside the window (no overlap). MAX_PAR bounds the Cloud Run Job's
  memory-backed `/tmp` to ~4 repos at once. One retry per repo absorbs transient concurrent-clone
  timeouts.
- **Observability** — Cloud Run Jobs don't reliably surface container stdout/stderr in Cloud
  Logging, so the script writes `gs://{bucket}/code/_refresh_status.json`
  (`{ts, changed, rebuilt_ok, failed}`) every run — the auditable cron status.
- **Self-healing** — SHA-skip + idempotent overwrite-by-name: a partial/timed-out run just
  rebuilds fewer; the next tick converges. Job: cloud-sdk image, `unified_trading` SA
  (secretAccessor on GH_PAT + storage.objectAdmin), sparse-checkout bootstrap (only `scripts/vm/`
  from deployment-service@LDR — not the full 1.9 GiB), 16Gi, 3600s timeout, max-retries 0.

## Pitfall captured (do not regress)

The imperative `gcloud run jobs ... --args=^|^...` deploy uses `|` as the list delimiter, so a
`||` in the bootstrap **fragments the command** (incident 2026-06-17: the job silently ran only
`command -v git` → no-op exit 0, no rebuild, no logs). Use `if/fi`, never `||`, in the bootstrap.

## Status

- [x] ✅ [SCRIPT] P1. `refresh_code_tarballs.sh` — SHA-skip + clean-from-LDR + reuse-builder.
      deployment-service (shipped); initial full refresh of all 11 stale tarballs succeeded.
- [x] ✅ [SCRIPT] P1. Bounded-parallel + `_refresh_status.json` + per-repo retry — locally tested
      (9/10 in 6m49s; status object correct), **landed deployment-service@bba8096** (through the
      churn race via a stash→FF-pull→pop→QG→quickmerge loop). The job clones LDR's script at
      run-time so the cron auto-adopts it.
- [x] ✅ [INFRA] P1. Cloud Run Job `code-tarball-refresh` created + verified (rebuilds tarballs;
      mtimes advance). Bootstrap-fragmentation bug found + fixed.
- [x] ✅ [INFRA] P1. Cloud Scheduler `uts-prod-code-tarball-refresh-cron` (`*/30`) created +
      verified (force-run triggered a job execution).
- [x] ✅ [INFRA] P2. TF SSOT `deployment-service/terraform/gcp/code_tarball_refresh_scheduler.tf`
      (job + scheduler) — **landed deployment-service@bba8096**, so a `terraform apply` won't drop
      the imperatively-created resources (documents the no-`||`-in-bootstrap pitfall).
- [ ] [INFRA] P3. **Perf follow-up (NICE-TO-HAVE)** — if churn outpaces even parallel rebuilds,
      replace per-repo `git clone` with the GitHub codeload tree tarball (no `.git`, faster
      transfer) — needs `create-code-tarballs.sh` to accept an explicit SHA (no `git rev-parse`).
- [ ] [INFRA] P3. **AWS parity** — the refresh currently targets GCP only; mirror for the AWS
      tarball bucket if/when the AWS VM fleet is reactivated.

## Codex SSOT updates

- `codex/05-infrastructure/vm-tarball-deployment.md` — add the "auto-refresh from LDR" section
  (cron + SHA-skip + the no-`||`-in-bootstrap pitfall + the `_refresh_status.json` audit object).
