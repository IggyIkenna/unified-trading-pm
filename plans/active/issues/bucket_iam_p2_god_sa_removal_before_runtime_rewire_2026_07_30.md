---
doc_type: issue
title:
  "bucket_iam_write_protection_per_tier_2026_06_09.md P2.1 as written removes the project-wide god-SA objectAdmin BEFORE
  any runtime is wired to the new per-tier SAs — would 403 every live/batch prod GCS write fleet-wide"
summary: >-
  Dispatched task bucket_iam_write_protection_per_tier-004 (assigned_role: infra) asked me to execute P2.1 literally:
  "Apply -prd- write-scope; remove the god-SA objectAdmin. Verify live/batch prod workloads retain -prd- write."
  Investigation (read-only, no state mutated) shows the "-prd- write-scope apply" half is ALREADY done — P1.2b's
  uts_prd_objectadmin_group_a/group_b bindings in bucket_iam_per_tier_sa.tf were confirmed LIVE via `tofu state list` +
  a clean `tofu plan` on 2026-07-29. The "remove the god-SA objectAdmin" half is NOT safe to do yet: main.tf:651's own
  comment confirms `unified-trading-sa` is "deployment-api's actual runtime identity", and a live grep of the whole
  deployment-service repo (`grep -rn "uts-prd-sa\|uts_prd\|uts-test-sa" --include=*.py --include=*.yaml --include=*.sh
  .`) returns ZERO hits outside terraform/ — nothing anywhere in the codebase authenticates as uts-prd-sa yet, and only
  5 of 165 scripts/vm/launch-*.sh scripts even pass --service-account= at all (the rest fall back to the default compute
  SA or unified-trading-sa). P2.2 ("wire each runtime to its tier SA") is still fully unchecked in the plan. Removing
  unified_trading_storage_admin (main.tf:598-602, the project-wide roles/storage.objectAdmin grant on unified-trading-sa
  — the literal "god-SA objectAdmin" P2.1 names) right now would immediately 403 every live + batch GCS write across the
  entire fleet (MTDS/MDPS/instruments-service/features/ execution/strategy stores — everything currently running as
  unified-trading-sa), which is both a direct violation of the data-pipeline-correctness-is-the-heartbeat HARD RULE and
  would ALSO fail P2.1's own stated verification step ("verify live/batch prod workloads retain -prd- write") since they
  would in fact lose write access entirely. I did NOT apply any terraform change. Instead I split P2.1 into P2.1a (done
  — the write-scope-apply half, already live via P1.2b) and P2.1b (open, explicitly gated on P2.2 completing + being
  live-verified first), mirroring this same plan's own P1.2→P1.2a/P1.2b precedent for "a single checkbox covering both a
  genuinely-complete slice and a still-blocked slice."
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [iam, terraform, sequencing-hazard, production-safety, gcp, bucket-tiers]
related:
  [
    /plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
    /plans/active/issues/bucket_iam_per_tier_dev_stg_retired_ssot_contradiction_2026_07_27.md,
    /codex/05-infrastructure/bucket-isolation-model.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: infra
drift_direction: correct-plan
source: >-
  Surfaced 2026-07-30 (slot-11, infra) while executing bucket_iam_write_protection_per_tier_2026_06_09.md todo P2.1,
  dispatched as backlog task bucket_iam_write_protection_per_tier-004.
resolved_by:
locked_by:
locked_since:
depends_on: []
---

# P2.1's literal "remove the god-SA objectAdmin" step would break every live/batch prod GCS write, fleet-wide

## What I found

`bucket_iam_write_protection_per_tier_2026_06_09.md`'s Phase 2 todo P2.1 bundles two very different actions in one
checkbox: (1) "apply `-prd-` write-scope" and (2) "remove the god-SA `objectAdmin`." Investigating before touching
anything (per the infra craft's own north-star — "never launch blind, everything observable and reversible"):

1. **(1) is already done.** P1.2b (completed 2026-07-29) applied `uts_prd_objectadmin_group_a` and
   `uts_prd_objectadmin_group_b` — `roles/storage.objectAdmin` on `uts-prd-sa`, scoped to `-prd-` Group A/B buckets via
   IAM Conditions. Confirmed live via `tofu state list` + a clean, no-diff `tofu plan` at the time. Nothing new needed
   here.
2. **(2) is NOT safe yet.** `unified-trading-sa` is the actual runtime identity essentially everything in the fleet
   authenticates as today — `deployment-service/terraform/gcp/main.tf:651`'s own comment says so explicitly
   ("unified-trading-sa, deployment-api's actual runtime identity"). Its `roles/storage.objectAdmin` project-wide grant
   is `unified_trading_storage_admin` at `main.tf:598-602`. I grepped the entire `deployment-service` repo for any
   reference to the new per-tier SAs outside terraform:

   ```
   grep -rn "uts-prd-sa\|uts_prd\|uts-test-sa" --include="*.py" --include="*.yaml" --include="*.yml" --include="*.sh" .
   → 0 hits (outside terraform/)
   ```

   and checked how many VM launchers even specify a service account at all:

   ```
   grep -l "service-account=" scripts/vm/launch-*.sh | wc -l   → 5
   ls scripts/vm/launch-*.sh | wc -l                            → 165
   ```

   So P2.2 ("wire each runtime to its tier SA") — still an unchecked `[ ]` in the plan — has not happened at all.
   Nothing anywhere authenticates as `uts-prd-sa`. If `unified_trading_storage_admin` were removed right now, every
   write path that currently runs as `unified-trading-sa` (which is nearly everything — deployment-api, Cloud Run
   services, VM backfill launchers) would immediately start 403ing on every GCS write: MTDS, MDPS, instruments-service,
   features-service, execution-service, strategy-service — the entire live + batch data pipeline, simultaneously.

## Why it matters

This is exactly the class of action the workspace's `data-pipeline-correctness-is-the-heartbeat` HARD RULE exists to
prevent — a single terraform apply that halts live trading data capture AND batch writes fleet-wide, with no rollback
faster than a second `tofu apply` to re-add the grant (during which window every write is silently dropped or
hard-failing, not merely degraded). It is also self-defeating on the plan's own terms: P2.1's own success criterion is
"verify live/batch prod workloads retain `-prd-` write" — executing the removal step first makes that verification fail
by construction, since those workloads would in fact lose write access (they're not using `uts-prd-sa` yet).

## Recommended decision

**Do NOT execute P2.1's god-SA-removal half until P2.2 is done and live-verified** (every deployment-service Cloud Run
service + VM launcher confirmed running as `uts-prd-sa`/the relevant tier SA, not `unified-trading-sa`, for all write
paths). I split P2.1 in the plan itself into:

- `P2.1a` (flipped done) — the write-scope-apply half, already satisfied by P1.2b.
- `P2.1b` (left open, explicitly gated on P2.2) — the god-SA-removal + negative-test-verification half.

This mirrors the plan's own already-established P1.2→P1.2a/P1.2b precedent for exactly this shape of problem ("a single
checkbox covering both a genuinely-complete slice and a still-blocked slice left nothing honestly flippable"). P2.2
should be picked up next by an infra/backend worker; P2.1b should not be dispatched again until P2.2's own checkbox is
flipped with live verification evidence.

## Addendum (2026-07-30, slot-13)

Same-day recurrence: backlog task `bucket_iam_write_protection_per_tier-008` (this plan's P2.1b) was dispatched to
slot-13 hours after this issue was filed. Re-verified the gate is still live (P2.2 still 0 hits for
`uts-prd-sa|uts_prd|uts-test-sa` outside `terraform/`, still only 5/165 launchers pass `--service-account=`) — did NOT
apply any terraform change. Root cause confirmed: P2.1b's checkbox carries no structured `depends_on`/ `gate_on_depends`
link to P2.2 (this workspace has no per-todo prereq syntax within a single plan — CLAUDE.md), so the backlog regenerator
re-offers it to any idle worker regardless of the plan's own prose gate. Fixed by tagging P2.1b `[OPERATOR]` in the plan
(`_OPERATOR_TAG_PREFIX_RE`-recognized — routes it to the operator's blocked-queue instead of worker dispatch) —
mechanical, not just documentation, so a third same-day re-dispatch shouldn't recur. Retag back to plain `[TERRAFORM]`
once P2.2 lands per the plan's own note.

## Todos

- [x] ✅ [CODE] P1. **Investigated 2026-07-30 (slot-12) — mechanical completion is NOT safe today.** Attempting P2.2
      literally surfaced 3 independently-blocking, live-verified findings (tier SAs are storage-only; VM launchers
      actually run as the GCP default compute SA, not `unified-trading-sa`, and that SA is itself a bigger live security
      exposure; a second, already-partially-live per-service SA scheme exists unreconciled with this plan). Filed
      `issues/bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md` with full evidence + a
      corrected, properly-gated todo breakdown, and split `bucket_iam_write_protection_per_tier_2026_06_09.md`'s P2.2
      into P2.2a-P2.2d (mirroring this plan's own P1.2/P2.1 split precedent) — unified-trading-pm@HEAD. No terraform/IAM
      state mutated.
- [ ] [TERRAFORM] P2. Once P1 above is live-verified (every write-path runtime confirmed running as its tier SA, not
      `unified-trading-sa`), execute `bucket_iam_write_protection_per_tier_2026_06_09.md` P2.1b: remove
      `unified_trading_storage_admin` (`main.tf:598-602`), then verify live/batch prod workloads retain `-prd-` write
      (now via the tier SA) and a dev/stg credential is IAM-denied a `-prd-` write. (repo: deployment-service)
