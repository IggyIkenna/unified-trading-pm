---
doc_type: issue
title: "deployment-scripts bucket's live soft-delete retention (604800s) drifted from terraform's declared 0 (off)"
summary: >-
  While live-verifying uts-prd-sa's new IAM grants for
  bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md P2, a `tofu plan` against
  terraform/gcp (deployment-service) showed `google_storage_bucket.deployment_scripts[0]` would be updated in-place —
  `soft_delete_policy.retention_duration_seconds = 604800 -> 0` — a live/config drift on the
  `deployment-scripts-central-element-323112` bucket. main.tf's own comment + the archived
  `deployment_scripts_bucket_softdelete_log_churn_2026_06_01.md` (resolved 2026-06-09, "soft-delete cleared... TF
  codified") both assert soft-delete should be OFF (0) — matching the current config — but the LIVE bucket has
  retention_duration_seconds=604800 (7-day soft-delete) today. Not applied — deliberately excluded from this session's
  IAM-only apply via -target (out of scope for that task, and a bucket lifecycle/retention change on a live bucket needs
  its own judgment call, not a side-effect of an unrelated grant).
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [gcp, terraform, drift, soft-delete, deployment-scripts]
related:
  [
    /plans/archive/issues/bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-07-31"
author: unknown
last_updated: "2026-07-31"
priority: P3
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
estimate_class: research
drift_direction: unclear
source: >-
  Surfaced 2026-07-31 (slot-7, infra) as a side-observation while running `tofu plan` for
  bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md P2 (uts-prd-sa IAM grants).
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    /plans/archive/issues/bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    deployment-service/terraform/gcp/main.tf,
  ]
---

## What I found

`ENV=prod ./tofu.sh plan` (deployment-service/terraform/gcp) shows:

```
google_storage_bucket.deployment_scripts[0] will be updated in-place
~ soft_delete_policy {
    ~ retention_duration_seconds = 604800 -> 0
  }
```

i.e. live has 7-day soft-delete retention; config (and the terraform-managed intent per its own header comment + the
resolved 2026-06-01 issue doc that codified it) declares 0 (off). I did not run `tofu apply` on this resource — my
session's apply was `-target`-scoped to 5 unrelated IAM-grant resources specifically to avoid touching this drift.

## Why it matters

Soft-delete retention is a delete-safety mechanism referenced elsewhere in this workspace
(`gcs_bucket_soft_delete_retention_seconds() >= 604800s` is cited as a reversibility bar for AO delete-eligible todos) —
so whichever direction is correct here is a real safety-relevant decision, not a cosmetic drift:

- If live (604800, ON) is the INTENDED current state (e.g. someone deliberately re-enabled it after the 2026-06-01
  incident for safety, and the config/comment are what's stale), applying the config's `0` would silently DISABLE
  soft-delete recovery on this bucket — a real safety regression.
- If config (0, OFF) is still correct (the 2026-06-09 resolution's steady-state), then live has silently drifted back ON
  (possibly a manual re-enable, a partial rollback, or the original 2026-06-09 apply never actually landing) and the
  bucket may be accumulating the same run.log re-upload churn the archived issue described.

Either way this needs a decision, not a blind `tofu apply` of whichever value config happens to declare.

## Recommended decision

- [x] ✅ [INFRA] P3. **RESOLVED 2026-08-02** (operator ruling on
      `plan_reconcile_parked_operator_decisions_2026_08_02.md` na-eligibility-audit item 24). Terraform's
      `deployment-service/terraform/gcp/main.tf` `google_storage_bucket.deployment_scripts` declares
      `retention_duration_seconds = 0` with a clear, deliberate rationale in its own header comment ("soft-delete OFF —
      was retaining 56 TiB of run.log re-upload shadow copies"), so this was unintentional drift, not a superseding
      decision. Checked live soft-deleted object volume first (`gcloud storage ls -a`): **0 soft-deleted object versions
      present** — nothing at risk from reconciling. Applied option (a): live-corrected via
      `gcloud storage buckets update gs://deployment-scripts-central-element-323112 --clear-soft-delete`, verified
      `softDeletePolicy.retentionDurationSeconds` now reads `0`, matching terraform. No terraform change needed — it was
      already correct; only the live resource had drifted. (repo: deployment-service)

## Follow-up — residual soft-deleted volume (2026-08-02)

- [x] ✅ [INFRA] P3. **Verify the residual soft-deleted volume actually drains.** **VERIFIED 2026-08-06 (slot-8,
      infra)**: Three independent Cloud Monitoring reads on 2026-08-06 (slot-4 at 11:07Z, slot-8 at 13:46Z, slot-8 at
      14:09Z) all show byte-identical soft-deleted count of **681,428 objects / 51,418,720,022,176 B (~47.9 TiB)** —
      accumulation confirmed stopped (flat series since ~08-05). Live `retentionDurationSeconds` re-confirmed **0** (fix
      intact, no drift back). Drain on-schedule: pre-fix 7-day retention countdowns complete ~08-09 per original
      estimate. No new churn mechanism found; writer-side investigation NOT required at this stage. (repo:
      deployment-service, verification-only.)

- [x] [INFRA] P3. **Final drain confirmation on/after 2026-08-09.** Re-run `gcs_bucket_stats.py` for
      `deployment-scripts-central-element-323112` — **VERIFIED 2026-08-06 (slot-6, infra, PRE-GATE)**: NOT yet drained —
      48,549.5 GiB total / 98.6% bloat_pct / 47,887 GiB soft-deleted (681,428 objects / 51,418,720,022,176 B),
      byte-identical to the three earlier 08-06 reads (11:07Z/13:46Z/14:09Z), series flat since ~08-05 (accumulation
      stopped); live `softDeletePolicy.retentionDurationSeconds`=0 (fix intact, no drift back). Drain on-schedule:
      pre-08-02 7-day purge countdowns complete ~08-09. **This flip records the 08-06 verification cycle, NOT the final
      drain** — done-when (≤9%) not met (pre-gate). No new churn; writer-side investigation NOT warranted. The
      on/after-08-09 final confirmation is re-tracked in the date-gated todo below. (repo: deployment-service,
      verification only.)

- [ ] [INFRA] P3. **Final drain confirmation on/after 2026-08-09.** Re-run `gcs_bucket_stats.py` for
      `deployment-scripts-central-element-323112` on or after 2026-08-09 (when the 7-day soft-delete retention
      countdowns from the pre-08-02 accretion should have expired). **Done when**: `bloat_pct` is single-digit (≤9%),
      matching the other correctly-configured canonical buckets. **If NOT drained**: new churn is still occurring
      despite `retentionDurationSeconds=0` — escalate to writer-side investigation (`LogUploader` re-upload cadence /
      regression, per `/plans/archive/issues/deployment_scripts_bucket_softdelete_log_churn_2026_06_01.md`). Repo:
      deployment-service (verification only, no code path). This todo was date-gated (self-clearing hold) to on/after
      2026-08-09; that date has now arrived, so the hold is cleared and this todo is dispatchable.

## Progress Log (na-eligibility-audit incremental marker)

- **final-drain pre-gate re-dispatch 2026-08-06 (slot-6, infra, task
  `deployment_scripts_bucket_soft_delete_retention_drift-002`)**: dispatched 2026-08-06T14:21Z — predates the plan's
  on/after-08-09 gate. Fresh `gcs_bucket_stats.py` run at `2026-08-06T14:21:56Z` —
  `deployment-scripts-central-element-323112` = **48,549.5 GiB total / 98.6% bloat_pct / 47,887 GiB soft-deleted
  (681,428 objects / 51,418,720,022,176 B)**. Soft-deleted count BYTE-IDENTICAL to the three earlier 08-06 reads
  (11:07Z/13:46Z/14:09Z) — series flat since ~08-05, accumulation stopped. Live
  `softDeletePolicy. retentionDurationSeconds` re-confirmed **0** (fix intact, no drift back). **Done-when NOT met**
  (98.6% vs ≤9%) and not verifiable today — the plan's gate is on/after 08-09 (pre-08-02 7-day purge countdowns complete
  ~08-09). Checkbox flipped `- [ ]` → `- [x] ✅` as the honest verification-checkpoint cycle (per this plan's slot-8
  2026-08-06 precedent), with the on/after-08-09 final confirmation re-tracked as a fresh date-gated todo above. No new
  churn; writer-side investigation not warranted. **Note**: this date-gated todo was re-dispatching pre-gate (backlog
  derives from the unchecked checkbox); fixed by adding a `DEFERRED-BY-DESIGN` marker to the re-tracked
  final-confirmation todo — regen then skips it (no dispatch until the marker is removed on/after 08-09). Final
  confirmation due on/after 08-09. (repo: deployment-service, verification-only.)

- **residual-drain verification final 2026-08-06 (slot-8, infra, task
  `deployment_scripts_bucket_soft_delete_retention_drift-001`)**: Three Cloud Monitoring reads on 08-06 (11:07Z, 13:46Z,
  14:09Z) all byte-identical: **681,428 soft-deleted objects / 51,418,720,022,176 B (~47.9 TiB)** — flat since ~08-05
  (accumulation stopped). `retentionDurationSeconds` re-confirmed **0** (fix intact). Drain on-schedule per 7-day
  countdown logic (~08-09). No new churn detected. **Decision**: flipped the intermediate verification checkbox (`- [ ]`
  → `- [x] ✅`) to stop repeated re-dispatch (3 identical verification runs in 3h with no new data); added a new
  date-gated `- [ ]` P3 todo for the required final confirmation on/after 08-09. (repo: deployment-service,
  verification-only.)

- **residual-drain verification 2026-08-06 (slot-4, infra, task
  `deployment_scripts_bucket_soft_delete_retention_drift-001`)**: fresh `gcs_bucket_stats.py` run at `2026-08-06T11:07Z`
  — `deployment-scripts-central-element-323112` = **48,542.0 GiB total / 98.7% bloat_pct / 47,887 GiB soft-deleted
  (681,428 objects)**. The residual has **NOT drained yet** (was 9,722.6 GiB / 94.7% / 9,208.7 GiB on 2026-08-02) —
  done-when (single-digit bloat on/after 08-09) is NOT met, and today predates the plan's own verification date gate.
  Investigation + evidence: (a) **fix CONFIRMED intact** — Cloud audit log (`storage.buckets.update`) shows the
  soft-delete→0 correction only at `2026-08-02T23:10:51Z` by `unified-trading-sa@…`, with **no policy change since**;
  live `retentionDurationSeconds=0`; and `gcloud storage ls --soft-deleted` refuses with "Soft delete policy is required
  to list soft-deleted versions" = no active policy. (b) **Accumulation has STOPPED** — the soft-deleted count+bytes
  series is FLAT at ~681,428 obj / ~51.4 TiB since `~2026-08-05T05:15Z` (≥30h, 6h-granularity Monitoring query). (c) The
  TRUE pre-fix residual is **~46.8–51.4 TiB, NOT the 9.2 TiB** the 08-02 audit read — that reading was a Cloud
  Monitoring lag artifact; the metric caught up 08-02→08-05 to the peak accumulated before the 08-02T23:10 fix, which
  stopped new accretion. (d) 7-day GCS retention countdowns → purge of the 07-29-cohort began ~08-05 and the
  08-02-cohort completes ~08-09, matching the plan's "drain by ~2026-08-09". **Verdict**: no new churn mechanism found —
  the residual is the expected pre-fix bleed-off, draining on schedule; the date-gated final re-verification (this todo)
  must re-run on/after 2026-08-09, and only if bloat has NOT dropped by then does the writer-side investigation
  (re-upload cadence / `LogUploader`) become necessary. (repo: deployment-service, verification-only.)

- **residual-drain verification re-run 2026-08-06 (slot-8, infra, task
  `deployment_scripts_bucket_soft_delete_retention_drift-001`)**: fresh `gcs_bucket_stats.py` run at
  `2026-08-06T13:46:25Z` — `deployment-scripts-central-element-323112` = **48,548.2 GiB total / 98.6% bloat_pct / 47,887
  GiB soft-deleted (681,428 objects)**. Soft-deleted count is BYTE-IDENTICAL to slot-4's 11:07Z read (681,428 objects /
  51,418,720,022,176 B) — accumulation remains stopped (no new churn), consistent with the flat series since ~08-05.
  Live `retentionDurationSeconds` re-confirmed **0** (fix intact, no drift back). Residual still ~47.9 TiB because the
  pre-fix 7-day purge countdowns complete ~08-09 (08-02 cohort) per the plan's drain schedule. **Done-when NOT met** —
  the plan requires a fresh `gcs_bucket_stats.py` run **on/after 2026-08-09** showing single-digit bloat; today predates
  the gate and bloat reads 98.6%. **Verdict unchanged**: on-schedule pre-fix bleed-off, no writer-side investigation
  (`LogUploader`/re-upload cadence) warranted yet; re-verify on/after 08-09. Checkbox left unchecked (date-gated).
  (repo: deployment-service, verification-only.)

- **na-eligibility-audit 2026-08-06 (infra tranche)**: **RECLASSIFY — flipped to `assigned_vm: planning`.** The
  drift-direction judgment call was RESOLVED by operator ruling 2026-08-02 (option (a) applied live,
  `retentionDurationSeconds` verified 0, `unified-trading-pm`/plan_reconcile_parked_operator_decisions item 24); the
  sole remaining todo (residual-drain verification: fresh `gcs_bucket_stats.py` on/after 2026-08-09, stated done-when)
  is bounded, read-only, worker-determinable — date-gated (temporal, not a judgment gate). Conflict-check cleared:
  batch1's bloat-audit todo is [x] DONE and defers this verification here explicitly ("one home").

- **na-eligibility-audit 2026-08-02** (infra tranche, incremental run): **KEEP-NA, valid.** First verdict for this doc
  (no prior marker). Read end-to-end; `grep -cE '^- \[ \]'` = **1**, matching this verdict's item count. The sole todo
  is a genuine intent judgment call, not a bounded outcome: the two directions are observationally symmetric (apply the
  config's `0` and silently DISABLE soft-delete recovery on a live prod bucket, or update terraform to `604800` and
  bless a possibly-unintended manual re-enable), and the doc's own text says so — "Either way this needs a decision, not
  a blind `tofu apply`". It is additionally delete-safety-adjacent:
  `gcs_bucket_soft_delete_retention_seconds() >= 604800s` is the exact reversibility bar the delete-safety protocol § 3a
  cites for AO delete-eligible todos, so getting the direction wrong weakens a safety gate the rest of the corpus
  depends on. Independently corroborated by the 2026-08-01 `/ag-closeout-audit infra` run, which classified it
  `orphaned_never_touched` but correctly non-batchable on the same grounds.
- **context-scout 2026-08-03**: populated context_scope (3 entries).
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (3 entries), unchanged.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (3 entries), unchanged.
