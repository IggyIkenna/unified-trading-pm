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
- [x] ✅ [TERRAFORM] P0. **DONE 2026-07-29 (operator's own ADC, `ikenna@odum-research.com` — confirmed
      `resourcemanager.projects.getIamPolicy` works for this identity, unlike the prior session's
      `github-actions-deploy` SA).** Applied via
      `ENV=prod TMPDIR=/tmp/tf-short TF_DATA_DIR=/tmp/tf-short/.terraform     ./tofu.sh apply` — but a scoped,
      `-target`-ed plan was required first: an untargeted `tofu plan` showed **19 to add / 70 to change / 2 to destroy**
      (unrelated live-state drift accumulated since 2026-07-27, not this todo's resources), a materially different shape
      than the doc's stated 8/2/0 expectation, so the full plan was NOT applied blind. Targeting exactly this file's 14
      resources (5 SAs + 9 `google_project_iam_member` bindings) gave a clean, additive-only plan (9 to add, 0 to
      change, 0 to destroy — the 5 SAs already existed unchanged). Applying that surfaced a **real, independent,
      pre-existing bug**: the 4 conditional `objectAdmin` bindings (group_a/group_b × prd/test) used
      `resource.name.contains("-prd-")` in their IAM Condition CEL expression — `contains` is NOT a declared function in
      GCP's IAM Condition CEL environment (confirmed live:
      `400 Condition expression compilation     failed... undeclared reference to 'contains'`), never caught by
      `tofu validate`/`plan` since GCP only compiles CEL server-side at `apply`. Tried `matches()` (regex) next — ALSO
      undeclared; GCP's `resource.name` condition attribute supports only `startsWith`/`endsWith`. Fixed by
      restructuring to a single `startsWith("projects/_/buckets/{prefix}{tier}-")` per bucket-name prefix (exact, not an
      approximation — confirmed live that `{tier}` immediately follows the group prefix in every real bucket name, e.g.
      `features-cefi-prd-central-element-323112`), eliminating the second function entirely. All 9 bindings now live and
      verified via `gcloud projects get-iam-policy central-element-323112` (4 conditional objectAdmin + 5 unconditioned
      objectViewer, all present with the expected condition titles). Shipped via quickmerge:
      `deployment-service@44002342`.
- [ ] [DOCS] P3. **Document GCP IAM Condition CEL's real function support** — confirmed live 2026-07-29: `resource.name`
      conditions support only `startsWith`/`endsWith`; both `contains()` and `matches()` are undeclared references,
      rejected only at real `apply` time (never caught by `tofu validate`/`plan`, which don't compile CEL server-side).
      Not documented anywhere in this workspace yet. Add to `/codex/05-infrastructure/bucket-isolation-model.md` or a
      dedicated IAM-conditions note, so the next per-tier/ per-env condition doesn't rediscover this the hard way.
- [x] ✅ [DOCS] P2. **DONE 2026-07-28** — Cross-referenced `bucket_iam_write_protection_per_tier_2026_06_09.md` and the
      (now-archived) `bucket_estate_consolidation_to_sub100_2026_07_13.md`: this issue doc's own `related:` already
      carried both (added 2026-07-27); fixed `bucket_iam_write_protection_per_tier_2026_06_09.md`'s `related:` entry for
      the archived plan (was pointing at the stale pre-archive `plans/active/...` path — corrected to
      `/plans/archive/2026_07/bucket_estate_consolidation_to_sub100_2026_07_13.md`) and added this issue doc
      (`/plans/active/issues/bucket_iam_per_tier_dev_stg_retired_ssot_contradiction_2026_07_27.md`) to the same list —
      `unified-trading-pm@c9eed9822`. Did not un-archive the source plan. `check_reference_paths.py` confirms no new
      format/existence violations introduced by this edit (verified against a stash/pop diff — an unrelated +4
      existence-count drift on `live-defi-rollout` HEAD predates this change).
- [x] ✅ [SCOPE] P2. **RESOLVED 2026-07-28** — Scoped both halves of "all SAs + CI/CD + developer identities →
      objectViewer broadly." (1) **CI/CD SA**: no new SA needs creating — the real CI/CD identity
      (`github-actions-deploy@central-element-323112.iam.gserviceaccount.com`) already exists and is live (it's the
      credential P1.2b's `tofu apply` ran under); exhaustive grep of `deployment-service/terraform/gcp/*.tf` for
      `google_service_account` confirms it is NOT terraform-managed anywhere in this repo (every declared SA —
      `unified_trading`, `t1_batch`, `catalogue_regen`, `is_daily_enum`, `defi_removal_probe`,
      `expected_universe_v2_enum`, `instrument_catalogue_regen`, `lifecycle_catalogue_regen`, `secret_rotator`, the 5
      per-tier SAs — is task-specific; none is `github-actions-deploy`). If broad CI read-access to the tier buckets is
      ever wanted, the correct terraform shape is a literal-email `google_storage_bucket_iam_member` /
      `google_project_iam_member` referencing `github-actions-deploy`'s existing address — never a new
      `google_service_account` resource, which would create a conflicting duplicate of a real, already-provisioned
      identity. (2) **Developer identities**: confirmed to be human GCP IAM users, handled entirely outside terraform by
      design — grepped `deployment-service/terraform/gcp/*.tf` for `"user:` IAM-member bindings: zero hits anywhere in
      the file set (consistent with this session's own use of personal ADC, e.g. `ikenna@odum-research.com`, for
      out-of-terraform GCP operations). **Conclusion**: neither half has a missing terraform target to build — the
      original P1.2 ask's "CI/CD + developer identities" clause described access that either already exists (CI/CD SA,
      external to this repo) or is intentionally out-of-terraform (developer/human accounts). No code change required to
      close this todo; see the new optional follow-up below for the one genuine, narrowly-scoped remaining option.
- [ ] [TERRAFORM] P3. **NEW 2026-07-28 (optional, not blocking).** If the operator wants CI to read the 5 tier-scoped
      buckets (matching bucket-isolation-model.md §8's "CI/CD SA read-only on prod"), add a literal-email
      `google_storage_bucket_iam_member` (`objectViewer`, scoped to Group A's `-test-`/`-prd-` bucket families) for
      `github-actions-deploy@central-element-323112.iam.gserviceaccount.com` in
      `deployment-service/terraform/gcp/bucket_iam_per_tier_sa.tf` — do NOT declare a `google_service_account` resource
      for it (it already exists; a new resource would either error on import-collision or create a stray duplicate
      identity). No current consumer is blocked on this — CI's `tofu apply`/`plan` steps use project-level IAM-policy
      permissions (P1.2b's gap), not bucket object access.
