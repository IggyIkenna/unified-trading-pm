---
doc_type: issue
title: Prod VM launches from the shared compute SA 403 on the new per-tier runtime SA (missing iam.serviceAccountUser)
summary: >-
  deployment-service's DP-VM-002 fix (2026-08-01, lc_tier_service_account) made every prod-env VM launch attach
  `uts-prd-sa@central-element-323112.iam.gserviceaccount.com` as the runtime service account. The shared
  `1060025368044-compute@developer.gserviceaccount.com` identity (the default for every local/interactive dev session
  across all slots, per this session's own established knowledge) lacks `iam.serviceAccountUser` on `uts-prd-sa` and
  cannot even read its IAM policy — every prod launcher invocation from a local session now 403s with "Ask a project
  owner to grant you the iam.serviceAccountUser role". Workaround found + used this session:
  `LC_RUNTIME_SA=<the-launching-identity's-own-email>` (attaching a VM to the SAME identity you already run as needs no
  delegation grant) restores launch success. Durable fix needs an operator or the `unified-trading-sa` self-service
  identity (/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md) to grant `iam.serviceAccountUser` on
  `uts-prd-sa` to the shared compute SA.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [iam, gcp, vm-launcher, service-account, prod-env, self-service-gap]
related:
  [
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/issues/sports_fixture_events_refetch_progress_2026_07_25.md,
    /plans/active/issues/bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md,
  ]
created: 2026-08-02
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
source: ["sports_satellite_ao_dispatch_batch2, autonomous continuation, 2026-08-02"]
drift_direction: advance-code
context_scope:
  [
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/issues/bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md,
    deployment-service/scripts/vm/lib/launcher_common.sh,
  ]
---

## What happened

Relaunching the FIXTURE_EVENTS recovery-pass VM (`launch-api-football-backfill-vm.sh --entity FIXTURE_EVENTS ...`,
routine after a SPOT preemption) failed with:

```
ERROR: (gcloud.compute.instances.create) Could not fetch resource:
 - The user does not have access to service account 'uts-prd-sa@central-element-323112.iam.gserviceaccount.com'.
   User: '1060025368044-compute@developer.gserviceaccount.com'. Ask a project owner to grant you the
   iam.serviceAccountUser role on the service account.
```

This is a NEW failure mode — the exact same command, same identity, same launcher succeeded twice earlier in this same
session (`af-backfill-20260731-094047`, `af-backfill-20260731-123439`) before this point. Root cause:
`deployment-service/scripts/vm/lib/launcher_common.sh`'s `lc_tier_service_account()` (added 2026-08-01, comment cites
"fix for DP-VM-002" — a bug where `--test-run` launches were writing to prod buckets because the launcher never attached
a tier-scoped runtime SA at all) now makes **every** `DEPLOYMENT_ENV=prod` VM launch attach
`uts-prd-sa@central-element-323112.iam.gserviceaccount.com` as its `--service-account`. Attaching a VM to a different SA
than the one you're currently authenticated as requires `roles/iam.serviceAccountUser` (or equivalent) on that target SA
— a grant that was evidently never extended to `1060025368044-compute@developer.gserviceaccount.com`, the shared
identity every local/interactive dev session uses by default in this workspace.

**Confirmed via `gcloud iam service-accounts get-iam-policy uts-prd-sa@... --account=1060025368044-compute@...`**:
`PERMISSION_DENIED: iam.serviceAccounts.getIamPolicy` — the compute SA can't even READ the policy on `uts-prd-sa`,
confirming the grant genuinely doesn't exist (not just a caching/propagation delay).

## Why this isn't an isolated one-off

`lc_tier_service_account()` is called by every launcher that adopted the DP-VM-002 fix pattern (grep the codebase for
`lc_tier_service_account` to enumerate current callers as they grow) — any DEFAULT-env (`prod`) launch from a
local/interactive session hits this identically. This is a workspace-wide gap introduced by a well-intentioned fix that
closed one bug (`--test-run` writing to prod buckets) and opened another (every ordinary prod launch from a
non-privileged identity now 403s).

## Self-service check (per /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md)

That SSOT's self-service identity is `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` — NOT the
`1060025368044-compute@...` identity used in this session. `unified-trading-sa`'s credentials are ambient only on the AO
orchestrator / human-planning VMs (`GOOGLE_APPLICATION_CREDENTIALS` exported in `.profile`/`.bashrc`), not on a local
interactive laptop session (confirmed: `GOOGLE_APPLICATION_CREDENTIALS` unset here, no key file found, no
`gcloud auth list` entry for it). The operator's own personal `gcloud` account (`ikenna@odum-research.com`) has an
expired token that cannot reauth non-interactively. **Net result: from THIS session, there is no reachable identity with
`iam.serviceAccountAdmin`/`resourcemanager.projectIamAdmin` to close this gap directly** — it genuinely needs either (a)
the operator to run the one-line grant below from an authenticated session, or (b) a future AO-orchestrator worker
session (which DOES have `unified-trading-sa` ambiently) to self-grant it per that SSOT's documented rule.

## Workaround used this session (works from any identity, no extra grant needed)

Attaching a VM to the SAME identity you're already authenticated as does not require the delegation grant (no
impersonation is happening). Set the launcher's own escape-hatch env var to your own identity's email:

```bash
CLOUDSDK_CORE_ACCOUNT=1060025368044-compute@developer.gserviceaccount.com \
LC_RUNTIME_SA="1060025368044-compute@developer.gserviceaccount.com" \
bash deployment-service/scripts/vm/launch-api-football-backfill-vm.sh ...
```

Confirmed working: `af-backfill-20260802-152210` launched cleanly with this override immediately after the bare
invocation 403'd. **Caveat**: this reverts the VM to running as the plain default compute SA, i.e. exactly the
pre-DP-VM-002 behavior — fine for FIXTURE_EVENTS/FIXTURE_STATS/FIXTURE_LINEUPS prod backfills (they were writing
correctly under this SA before 2026-08-01), but do NOT use this workaround for a `--test-run` launch, since reverting to
the default compute SA is exactly the behavior DP-VM-002 was fixing (it would silently write real prod-bucket data
during what's meant to be a test-bucket smoke check). Test-mode launches should keep going through
`lc_tier_service_account(..., test_run=true)` unmodified.

## Recommended durable fix (not applied — needs operator or an AO-orchestrator-identity session)

```bash
gcloud iam service-accounts add-iam-policy-binding uts-prd-sa@central-element-323112.iam.gserviceaccount.com \
  --member="serviceAccount:1060025368044-compute@developer.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

Once granted, drop the `LC_RUNTIME_SA=<self>` workaround from any active runbooks/monitoring-loop instructions that
adopted it as a stopgap (grep for `LC_RUNTIME_SA=` in `plans/active/issues/` once this is closed).

## Status

Not escalating as `BLOCKED-OPERATOR` on the FIXTURE_EVENTS/FIXTURE_STATS/FIXTURE_LINEUPS campaign itself — the
workaround unblocks all in-flight and planned launches for this campaign immediately. Filing this doc so (a) the
underlying grant gap gets closed durably rather than every future session rediscovering the same 403, and (b) the
workaround is written down for whoever hits it next before the grant lands.

## Progress Log

- **na-eligibility-audit 2026-08-02 (infra tranche, dispatch agt-fe5e17)**: KEEP-NA, valid (parked, conflict found) —
  this doc's "Recommended durable fix" (grant `iam.serviceAccountUser` on `uts-prd-sa` to the shared default compute SA
  `1060025368044-compute@developer.gserviceaccount.com`) reads as bounded/worker-determinable in isolation (exact
  command + verification given), so it was evaluated as a RECLASSIFY candidate. Conflict-check
  (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3) against active
  `assigned_vm: planning` docs in the same `parent_epic: infrastructure_master` surfaced a genuine conflict:
  `/plans/active/issues/bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md` (P0,
  `sequential: true`, actively dispatched) is mid-flight on the SAME two identities (`uts-prd-sa` and the default
  compute SA) and explicitly frames the default compute SA's broad, unconditional, project-wide grant set (incl.
  `roles/storage.admin` + `roles/iam.serviceAccountTokenCreator`) as "a bigger live exposure than the original god-SA
  grant" — its own open P3.1/P3.2 todos are heading toward SCOPING DOWN / migrating launchers OFF the default compute SA
  entirely, not granting it further reach. Applying this doc's recommended fix (granting the default compute SA MORE
  impersonation reach — the ability to act as `uts-prd-sa` too) would extend exactly the identity that sibling doc's
  active P0 effort is working to de-privilege, and duplicates ground already claimed by its P3.1/P3.2 (VM launcher SA
  rewiring, "Do not attempt as a single mechanical bulk edit"). Per the conflict-check protocol: do NOT flip, do NOT
  silently prefer one side — stays `assigned_vm: NA`, cross-referenced (see `related:` above) for reconciliation when
  P3.1/P3.2 execute (the "right" durable fix may be wiring this specific launcher onto a properly-scoped identity per
  that plan's Recommended-decision option (a), rather than this doc's proposed direct grant to the over-privileged
  default compute SA). Not parked as `BLOCKED-OPERATOR-DECISION` (this doc's own workaround already unblocks the
  campaign, no urgency), but flagged here so whoever next works either doc sees the connection before executing either
  fix.

- **context-scout 2026-08-03**: populated context_scope (4 entries).
- **na-eligibility-audit 2026-08-03** (infra tranche, incremental run, dispatch agt-a41abf): **KEEP-NA, valid —
  unchanged from the 2026-08-02 verdict.** In scope only because the context-scout backfill above touched the file;
  `git show` confirms zero content/todo/status change from that commit. 0 open checkboxes (a diagnostic/workaround doc,
  not a checkbox-tracked one), matching Phase 0's inventory. Re-verified live: the conflicting sibling plan
  (`bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md`) is still `status: open`,
  `assigned_vm: planning`, `priority: P0` — the 2026-08-02 conflict-check's basis for staying parked still holds. No
  action needed.
