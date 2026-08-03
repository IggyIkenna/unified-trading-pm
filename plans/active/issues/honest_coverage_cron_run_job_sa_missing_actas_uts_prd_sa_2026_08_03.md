---
doc_type: issue
title:
  honest-coverage-daily-launcher Cloud Run Job's own SA lacks iam.serviceAccountUser on uts-prd-sa — nightly cron has
  been silently failing since ~2026-08-01
summary: >-
  Live-verified via a manual `gcloud run jobs execute honest-coverage-daily-launcher --wait` (run to confirm the
  launcher-SSOT-cleanup repoint in defi_consolidated_native_ao_extract_2026_07_25.md landed correctly): the launcher
  fetch itself now succeeds (confirms that fix), but the job then fails at `gcloud compute instances create` with `The
  user does not have access to service account 'uts-prd-sa@central-element-323112.iam.gserviceaccount.com'. User:
  'instruments-service-cloud-run@central-element-323112.iam.gserviceaccount.com'`. Root cause is the SAME DP-VM-002
  `lc_tier_service_account()` rollout (2026-08-01) already tracked in
  `prod_vm_launch_missing_service_account_user_grant_2026_08_02.md` and
  `bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md` — but a DIFFERENT caller identity
  neither doc enumerates: the Cloud Run Job's own dedicated SA (`instruments-service-cloud-run@...`), not a local dev
  session's shared default compute SA. `gs://central-element-323112-honest-coverage/` has ZERO objects for 2026-08-02
  (and, per this session's own two manual trigger attempts, 2026-08-03) — the honest-coverage data-status panel has been
  silently stale for at least 2 days.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [iam, gcp, vm-launcher, service-account, prod-env, cron, honest-coverage, data-status]
related:
  [
    /plans/active/issues/prod_vm_launch_missing_service_account_user_grant_2026_08_02.md,
    /plans/active/issues/bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md,
    /plans/active/defi_consolidated_native_ao_extract_2026_07_25.md,
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
  ]
created: 2026-08-03
priority: P1
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  [
    "defi_consolidated_native_ao_extract_2026_07_25.md INFRA P3 (honest-coverage launcher SSOT cleanup), slot-7,
    2026-08-03",
  ]
drift_direction: advance-code
context_scope:
  [
    /plans/active/issues/prod_vm_launch_missing_service_account_user_grant_2026_08_02.md,
    /plans/active/issues/bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md,
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
    deployment-service/scripts/vm/lib/launcher_common.sh,
    deployment-service/terraform/gcp/honest_coverage_scheduler.tf,
  ]
---

## What happened

While shipping `defi_consolidated_native_ao_extract_2026_07_25.md`'s honest-coverage launcher SSOT cleanup todo (repoint
`honest_coverage_scheduler.tf`'s Cloud Run Job fetch command from the special-cased bucket-root `vm/` GCS path to the
`code/deployment-service/scripts/vm/` path `create-code-tarballs.sh`'s bare-launcher loop auto-publishes), I manually
triggered the live Cloud Run Job to verify the repoint end-to-end
(`gcloud run jobs execute honest-coverage-daily-launcher --region=asia-northeast1 --project=central-element-323112 --wait`),
per this craft's "never launch blind" north-star.

Two consecutive executions both **confirmed the launcher-SSOT fix is correct** — both cleanly fetched
`launch-measure-honest-coverage-vm.sh` + `lib/*.sh` from the new `code/deployment-service/scripts/vm/` path
(`lc_verify_tarball_freshness: all 4 tarball(s) current`) — but both then failed identically at VM creation:

```
ERROR: (gcloud.compute.instances.create) Could not fetch resource:
 - The user does not have access to service account 'uts-prd-sa@central-element-323112.iam.gserviceaccount.com'.
   User: 'instruments-service-cloud-run@central-element-323112.iam.gserviceaccount.com'. Ask a project owner to grant
   you the iam.serviceAccountUser role on the service account.
```

`gs://central-element-323112-honest-coverage/` currently has date-prefixed folders through `2026-08-02` but the
2026-08-02 folder is EMPTY (0 objects) — the nightly 00:30 UTC cron has been failing silently since at least that date
(the deployment-api `GET /api/data-status/honest-coverage` endpoint 404s or serves stale data for any date without a
`coverage.json`).

## Root cause — same bug class as two already-tracked docs, one new caller identity

`launch-measure-honest-coverage-vm.sh` calls `lc_tier_service_account("${DEPLOYMENT_ENV}" "$PROJECT")`
(`deployment-service/scripts/vm/lib/launcher_common.sh`), added 2026-08-01 for the DP-VM-002 fix (prevent `--test-run`
launches from writing to prod buckets). For `DEPLOYMENT_ENV=prod` (the Cloud Scheduler's only invocation mode for this
job) this resolves to `--service-account=uts-prd-sa@...`. Attaching a VM to a service account OTHER than the one you're
currently authenticated as requires `roles/iam.serviceAccountUser` (or equivalent) on that TARGET SA — a grant that was
never extended to the honest-coverage-daily-launcher Cloud Run Job's own SA
(`instruments-service-cloud-run@central-element-323112.iam.gserviceaccount.com`).

This is the exact same failure shape as `prod_vm_launch_missing_service_account_user_grant_2026_08_02.md` (which covers
the shared `1060025368044-compute@developer.gserviceaccount.com` default compute SA, used by local/interactive dev
sessions) — but that doc's `related:` grep and "why this isn't an isolated one-off" section did not enumerate Cloud Run
Job SAs as a distinct affected-caller class, only local sessions. `instruments-service-cloud-run@...` is a scoped,
single-purpose SA already carrying `compute.instanceAdmin.v1` (per `honest_coverage_scheduler.tf`'s existing
`google_service_account_iam_member.honest_coverage_launcher_actas_default_compute` resource, which grants it actAs on
the DEFAULT compute SA only) — the DP-VM-002 rollout changed which SA the VM attaches to but nobody updated this
specific actAs binding to match.

## Why I am NOT self-fixing this here

The mechanically obvious fix — add a `google_service_account_iam_member` binding granting
`instruments-service-cloud-run@...` `roles/iam.serviceAccountUser` on `uts-prd-sa` specifically (narrow, single-target,
NOT the broad project-wide grant `prod_vm_launch_missing_service_account_user_grant_2026_08_02.md` flagged as
conflicting with active de-privileging work) — looks safe in isolation. But
`bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md` is an ACTIVE, `sequential: true`,
`assigned_vm: planning`, P0 plan whose explicit open scope is "wire every deployment-service Cloud Run service + VM
launcher to its tier SA" and which found the current VM-launcher SA topology (155/156 launchers on the over-privileged
default compute SA, a competing per-service SA scheme, tier SAs missing non-storage roles) unsafe to touch mechanically
without first resolving those three findings. Adding a NEW actAs binding for one more caller-SA pair, on the exact
identity pair that plan is actively re-architecting, risks contradicting whatever direction it lands on (e.g. if the
"right" fix is a dedicated per-cron-job SA rather than actAs delegation onto the shared tier SA). Per the same
conflict-check precedent `prod_vm_launch_missing_service_account_user_grant_2026_08_02.md`'s own Progress Log already
established for the sibling case: do NOT flip, do NOT silently apply a fix that overlaps actively-claimed ground —
file + cross-reference instead.

## Recommended decision

One of:

(a) When `bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md`'s P3.1/P3.2 (VM launcher
SA rewiring) executes, fold this specific caller (`instruments-service-cloud-run@` → the honest-coverage cron) into its
scope rather than granting a standalone actAs binding now.

(b) If restoring the honest-coverage data-status panel is more urgent than waiting on that P0 plan's sequencing, an
operator (or a future AO-orchestrator-identity session per
`/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`) can apply the narrow, single-target grant
directly:

```bash
gcloud iam service-accounts add-iam-policy-binding uts-prd-sa@central-element-323112.iam.gserviceaccount.com \
  --member="serviceAccount:instruments-service-cloud-run@central-element-323112.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser" \
  --project=central-element-323112
```

then mirror it into `honest_coverage_scheduler.tf` (a new `google_service_account_iam_member` resource, same pattern as
the existing default-compute-SA binding in that file) so it's IaC-tracked, not an out-of-band grant.

## Status

Not applying either option here — outside this session's assigned todo (launcher SSOT file cleanup, already shipped and
verified: the fetch-path repoint itself works correctly) and directly overlaps an active P0's claimed scope. Filing so
(a) the data-pipeline-correctness gap (honest-coverage stale since ~2026-08-01/08-02) is tracked and visible, and (b)
whoever next works either the P0 SA-rewiring plan or this doc sees the honest-coverage caller as a third affected
identity alongside the two already documented.

## Todos

- [ ] [OPERATOR] P1. **Decide (a) vs (b) above.** (a) fold the `instruments-service-cloud-run@` caller into
      `bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md`'s P3.1/P3.2 scope when that
      still-open P0 plan (`status: open`, `assigned_vm: planning`, confirmed live 2026-08-03) executes its VM-launcher
      SA rewiring; or (b) apply the narrow `iam.serviceAccountUser` grant on `uts-prd-sa` for
      `instruments-service-cloud-run@` directly now (exact command above) + mirror into `honest_coverage_scheduler.tf`,
      if restoring the honest-coverage data-status panel is more urgent than waiting on the P0 plan's sequencing. This
      is a genuine urgency-vs-scope-overlap tradeoff, not a mechanical fix — a worker should not guess which side wins.
      Until decided, the honest-coverage data-status panel stays silently stale (failing since ~2026-08-01/08-02).

## Progress Log

- **context-scout 2026-08-03**: populated context_scope (5 entries).
- **na-eligibility-audit 2026-08-03** (infra tranche, dispatch agt-a41abf): **KEEP-NA, valid.** First verdict for this
  doc. Read end-to-end. On arrival the doc's only actionable content was prose under "## Recommended decision" / "##
  Status" — no `- [ ]` checkbox anywhere, so `open_todos` read 0 in this run's Phase 0 inventory. Per CLAUDE.md's HARD
  RULE ("every follow-up is a `- [ ]` todo, never prose"), added an explicit `## Todos` section above capturing the
  doc's own already-well-reasoned (a)/(b) decision as one `[OPERATOR] P1` item — no new judgment introduced, the two
  options and their tradeoff are exactly as this doc's author already stated them. Verdict is KEEP-NA (not RECLASSIFY):
  the choice between (a) fold into the active P0's scope vs (b) apply a narrow grant now is an urgency/scope-overlap
  tradeoff a worker cannot resolve alone, and the doc's own "Why I am NOT self-fixing this here" section already
  explains why applying (b) unilaterally risks contradicting the active P0 plan's direction. Confirmed
  `bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md` is still `status: open`,
  `assigned_vm: planning`, `priority: P0` (live check, not stale citation). No conflict-check needed (KEEP-NA, not a
  RECLASSIFY).
