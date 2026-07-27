---
doc_type: issue
title:
  "bucket_iam_write_protection_per_tier_2026_06_09.md's per-tier SA design (uts-dev-sa/uts-stg-sa) is built on a premise
  a LATER operator ruling retired — dev/stg tiers do not exist and never will"
summary: >-
  Found while scoping P1.2 (per-suffix IAM bindings for the 4 per-tier SAs P1.1 already created live in GCP).
  bucket_iam_write_protection_per_tier_2026_06_09.md's "Open design decisions" section (resolved 2026-06-12) commits to
  4 SAs: uts-dev-sa, uts-stg-sa, uts-prd-sa, uts-migration-sa — one per tier including dev and staging. But
  deployment-service/terraform/gcp/canonical_buckets.tf:44-46 states plainly: "prd + test are the only provisioned tiers
  (dev/stg retired per the 2026-07-13 operator ruling — bucket_estate_consolidation_to_sub100_2026_07_13.md Wave 1)" —
  confirmed by that archived plan's own todo (line 153): "[OPERATOR] P1. RULED 2026-07-13 — retire BOTH dev/stg tiers
  (operator answer to the audit question set; 20 of 21 canonical dev/stg buckets empty)," with all 20 empty dev/stg
  buckets subsequently deleted. This operator ruling is dated 2026-07-13 — ONE MONTH AFTER the IAM plan's SA design was
  resolved (2026-06-12) — so the IAM plan's design predates, and is now contradicted by, the authoritative later ruling.
  The IAM plan's own 2026-07-25 update independently re-discovered the SYMPTOM (Group A real buckets are
  "-test-"/"-prd-" only) but framed it as "not yet provisioned, needs re-derivation" rather than tracing it to this ROOT
  CAUSE (dev/stg were deliberately, permanently retired workspace-wide, not just absent from Group A). P1.1 has ALREADY
  created uts-dev-sa and uts-stg-sa as live GCP service accounts based on the stale premise — no role bindings yet
  (that's P1.2, not done), so nothing is broken, but the plan is one dispatch away from someone binding those 2 SAs to a
  suffix (`*-dev-*`/`*-stg-*`) that will never match any bucket, forever, silently building dead infrastructure on a
  stale design.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [iam, terraform, ssot-contradiction, bucket-tiers, dev-stg-retirement, gcp]
related:
  [
    /plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
    /plans/archive/2026_07/bucket_estate_consolidation_to_sub100_2026_07_13.md,
    /codex/05-infrastructure/bucket-isolation-model.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: design
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role: infra
drift_direction: correct-plan
source: >-
  Surfaced 2026-07-27 (slot-12, infra) while scoping bucket_iam_write_protection_per_tier_2026_06_09.md todo P1.2
  (per-suffix IAM bindings), dispatched as backlog task bucket_iam_write_protection_per_tier-002.
resolved_by:
locked_by:
locked_since:
depends_on: []
---

# The IAM-per-tier plan's dev/stg SA design predates and contradicts the dev/stg tier retirement

> **🟢 DESIGN DECISION RESOLVED 2026-07-27 — READ THIS BEFORE RE-ASKING.** This exact question ("how to reconcile the
> dev/stg SA design with the retirement") was raised independently by three slots this session (slot-12 → BLK-4b104acc,
> slot-8 → BLK-6cb40a54, slot-6 → BLK-f1620233) and main ruled identically all three times: **option (a) "rename" is
> impossible** (GCP SA `account_id`s are immutable) — the end state is **create `uts-test-sa`; leave
> `uts-dev-sa`/`uts-stg-sa` permanently UNBOUND + documented as historical, never destroyed** (retiring an already-dead
> tier via a live destroy is a separate, [OPERATOR]-gated step per delete-safety, not this decision). **This is DONE and
> live-verified** (`gcloud iam service-accounts list` re-confirmed 2026-07-27 slot-6: `uts-test-sa` exists;
> `uts-dev-sa`/`uts-stg-sa` display names read "(HISTORICAL — permanently unbound)") — see the flipped `[DESIGN] P0`
> checkbox below for the full citation. **Do not re-open this design question** — if you land on this doc next, your job
> is one of the 3 still-open mechanical todos below (credential-blocked `tofu apply`, `related:` cross-referencing,
> CI/CD-identity scoping), not the architecture decision.

## What I found

- **The retirement (root cause)**: `deployment-service/terraform/gcp/canonical_buckets.tf:44-46` — "prd + test are the
  only provisioned tiers (dev/stg retired per the 2026-07-13 operator ruling —
  bucket_estate_consolidation_to_sub100_2026_07_13.md Wave 1)." Confirmed in the source plan itself
  (`plans/archive/2026_07/bucket_estate_consolidation_to_sub100_2026_07_13.md:153`): "[x] ✅ [OPERATOR] P1. RULED
  2026-07-13 — retire BOTH dev/stg tiers (operator answer to the audit question set; 20 of 21 canonical dev/stg buckets
  empty)" — the 20 empty dev/stg buckets were subsequently deleted (line 688-692 lists them by name). This is a
  workspace-wide, permanent retirement — not scoped to Group A, not "not yet provisioned."
- **The stale design**: `bucket_iam_write_protection_per_tier_2026_06_09.md`'s "Open design decisions" §, resolved
  2026-06-12 (**one month before** the retirement ruling): "Final SA set: `uts-dev-sa` (rw `-dev-*`...), `uts-stg-sa`
  (rw `-stg-*`...), `uts-prd-sa` (rw `-prd-*`...), `uts-migration-sa`." This 4-tier design has no way to reflect a
  ruling that postdates it.
- **The symptom, independently re-discovered but not traced to root cause**: the same plan's own 2026-07-25 finding
  (Phase 1 scoping note) says "Group A's real bucket names are TWO-TIER, `-test-`/`-prd-` only, no `-dev-`/`-stg-`
  suffix anywhere in this family" and correctly flags that "a `uts-dev-sa`/`uts-stg-sa` split may not even apply to
  Group A if there is no `-dev-`/`-stg-` tier for it to bind to" — but frames this as a Group-A-specific naming gap
  needing "re-derivation," not as "the entire dev/stg tier concept was killed workspace-wide a month after this SA
  design was written." The two docs were never cross-referenced.
- **Already-live consequence**: P1.1 (`deployment-service@72c78a8`, shipped 2026-07-27 by a different slot) already
  created `uts-dev-sa` and `uts-stg-sa` as real GCP service accounts (`terraform/gcp/bucket_iam_per_tier_sa.tf`) — with
  **no IAM role bindings yet** (P1.1's own commit message: "deliberately out of this todo"). So nothing is broken in
  production today. But P1.2 (the very next todo, what I was dispatched to do) is specified as "dev SA → objectAdmin on
  `*-dev-*`; stg SA → `*-stg-*`" — binding two live SAs to a bucket-name pattern that, per the retirement ruling, will
  **never match anything, ever**. Implementing P1.2 literally would ship a permanently-dead, misleading IAM binding on
  the project's actual production identity fabric.

## Why it matters

This is a real-infra, cross-plan SSOT contradiction on a **locked, active P1 plan** (`locked_by: live-defi-rollout`)
that is mid-execution against a **live production GCP project**. Two consequences if not corrected before P1.2 ships:

1. **Dead infrastructure**: `uts-dev-sa`/`uts-stg-sa` bound to conditions matching zero buckets forever — technically
   harmless (an empty grant), but permanently misleading to anyone reading the IAM policy later ("why does this SA exist
   and have a scoped grant that matches nothing?").
2. **Missed the real 2-tier requirement**: the plan never asks "who writes `-test-`?" — P1.2's literal text only covers
   dev/stg/prd, entirely omitting the tier that (per the retirement) is actually the ONE non-prod tier that exists.
   `-test-` buckets are the CI/E2E write target real workloads need — that's arguably the more urgent gap than the
   dev/stg bindings the plan currently specifies.

## Recommended decision

- [x] ✅ [DESIGN] P0. **RESOLVED 2026-07-27 — operator approval via BLK-4b104acc.** Chose option (b) WITHOUT a destroy:
      create a correctly-named `uts-test-sa` (GCP SA `account_id`s are immutable, so (a)'s "rename" was never really
      possible — it would have left a permanently-misnamed resource); leave `uts-dev-sa`/`uts-stg-sa` PERMANENTLY
      UNBOUND (zero IAM role bindings) and documented as historical, never destroyed (retiring a bucket TIER that's
      already gone is implementing an existing operator SSOT, not a new architecture decision; leaving the SAs
      undestroyed is zero-risk and trivially reversible). Shipped `deployment-service@0dbc9ae`: `uts-test-sa` created +
      `uts-dev-sa`/`uts-stg-sa` descriptions updated, live-verified via `gcloud iam service-accounts list`.
- [x] ✅ [DOCS] P1. **DONE 2026-07-27** — `bucket_iam_write_protection_per_tier_2026_06_09.md`'s "Open design decisions"
      § now carries a dated correction banner citing this issue doc + the retirement ruling (the stale 2026-06-12
      resolution is preserved below the banner, not silently edited).
- [x] ✅ [TERRAFORM] P1. **PARTIAL 2026-07-27** — `uts-prd-sa` → `objectAdmin` on `*-prd-*` + `uts-test-sa` →
      `objectAdmin` on `*-test-*` (both scoped to Group A: `market-data-tick-*`/`instruments-store-*`/
      `features-calendar-*`) + broad `objectViewer` for all 5 SAs are DECLARED in
      `deployment-service/terraform/gcp/bucket_iam_per_tier_sa.tf` (`tofu validate` clean, targeted `tofu plan` showed 8
      adds/2 changes/0 destroys) but **NOT YET APPLIED** — see new todo below (credential blocker).
- [ ] [TERRAFORM] P0. **NEW 2026-07-27 — BLOCKED-CREDENTIALS.** `tofu apply` of the 8 declared IAM-binding resources
      failed: this session's active credential (`github-actions-deploy@central-element-323112.iam.gserviceaccount.com`)
      lacks `resourcemanager.projects.getIamPolicy`/`setIamPolicy` on `central-element-323112` entirely — confirmed
      directly, `gcloud projects get-iam-policy central-element-323112` 403s outright for this identity (not scoped to
      my new resources; the SAME error class hit ~15 unrelated pre-existing `google_project_iam_member`/
      `google_secret_manager_secret_iam_member` resources in a full untargeted `tofu plan`, confirming this is a
      whole-project IAM-policy permission gap, not something wrong with the new resources). **Done when**: someone with
      a credential holding `resourcemanager.projects.setIamPolicy` on `central-element-323112` (e.g.
      `unified-trading-sa`, or an operator's own ADC — matches how P1.1's SA-creation step and other project-level
      grants in this terraform were evidently applied historically) runs
      `ENV=prod TMPDIR=<short-path> TF_DATA_DIR=<short-path>/.terraform ./tofu.sh apply` from
      `deployment-service/terraform/gcp/` (a short `TMPDIR` avoids a known unix-socket-handshake break on the plugin
      install step with long paths — see P1.1's own note above) and confirms
      `Plan: 8 to add, 2 to change, 0 to     destroy` before applying (re-run `tofu plan` fresh first — the docs above
      are not a substitute for a live re-check).
- [ ] [DOCS] P2. Cross-reference `bucket_iam_write_protection_per_tier_2026_06_09.md` and the (now-archived)
      `bucket_estate_consolidation_to_sub100_2026_07_13.md` in each other's `related:` frontmatter so this class of
      drift (two plans quietly deciding contradictory things about the same tier model, a month apart, never
      cross-checked) is easier to catch next time — add to `related:` on both plan docs (the source plan is archived, so
      only add on this side + this issue doc; do not un-archive it just to edit frontmatter).
- [ ] [SCOPE] P2. **NEW 2026-07-27.** The original P1.2 text's "all SAs + CI/CD + developer identities → objectViewer
      broadly" was only partially addressed — the 5 per-tier SAs got objectViewer, but no CI/CD or developer identity is
      terraform-managed anywhere in this repo today (grepped: only task-specific SAs like `t1_batch`, `catalogue_regen`
      exist, no generic "CI/CD SA" or "developer SA" resource), so that half of the original ask has no concrete
      terraform target yet. Scope this properly (does a CI/CD SA need to be created? are "developer identities" human
      GCP IAM users, handled outside terraform entirely?) before assuming it's done.
