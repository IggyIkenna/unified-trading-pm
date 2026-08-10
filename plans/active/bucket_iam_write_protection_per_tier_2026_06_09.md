---
doc_type: plan
title: Bucket IAM write-protection — per-tier/per-domain SAs replace the project-wide god-SA (§8 implementation)
summary: >-
  Implements bucket-isolation-model §8 credential-level write-protection: replaces the project-wide god-SA
  (unified-trading-sa holds roles/storage.objectAdmin over all buckets) with per-tier/per-domain service accounts
  (batch/live SAs write only their domain; CI/CD + dev SAs read-only on prod) plus a dedicated migration SA. Keys off
  the actual -dev-/-stg-/-prd- suffix from resolve_bucket_name; Group B phase blocked on the env-split rollout plan.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [infrastructure, ssot-audit, migration, data-correctness, canonicalisation, quality-gates]
related:
  [
    plans/active/cicd_contract_hardening_2026_06_01.md,
    plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    plans/archive/2026_07/bucket_env_split_rollout_2026_06.md,
    /plans/archive/2026_07/bucket_estate_consolidation_to_sub100_2026_07_13.md,
    /plans/archive/issues/bucket_iam_per_tier_dev_stg_retired_ssot_contradiction_2026_07_27.md,
  ]
created: 2026-06-09
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
last_updated: 2026-07-31
locked_by: live-defi-rollout
locked_since: 2026-06-09
supersedes:
superseded_by:
depends_on:
assigned_role: infra
source:
Codex SSOTs:
  [/codex/05-infrastructure/bucket-isolation-model.md, /codex/16-strategy-playbooks/infra-spec/stage-3e-g2-env-split.md]
drift_direction: advance-code
context_scope:
  [
    /codex/05-infrastructure/bucket-isolation-model.md,
    /plans/archive/issues/bucket_iam_per_tier_dev_stg_retired_ssot_contradiction_2026_07_27.md,
    /plans/archive/issues/bucket_iam_p2_god_sa_removal_before_runtime_rewire_2026_07_30.md,
    /plans/archive/issues/unified_trading_sa_live_iam_drift_vs_terraform_2026_07_31.md,
    deployment-service/terraform/gcp/bucket_iam_per_tier_sa.tf,
    deployment-service/terraform/gcp/main.tf,
  ]
---

# Bucket IAM write-protection — per-tier/per-domain SAs (§8 implementation)

## What I found

The bucket isolation model is **designed but only half-implemented**.

- **Designed** ([bucket-isolation-model.md §8](/codex/05-infrastructure/bucket-isolation-model.md)): batch/live SAs
  read+write **scoped to their domain**; CI/CD + developer SAs **read-only on prod, read+write on mock/dev**; env tier
  lives in the bucket name (Group B: `…-{mock|dev|prod}-{project}`).
- **Implemented**: bucket **naming/tier** (`unified-cloud-interface` `get_bucket_name`/`get_bucket_environment`) + the
  runtime guard that makes `CLOUD_MOCK_MODE=true` / `ENVIRONMENT=dev` never resolve to a prod bucket name. This is a
  **code-level** safety net only.
- **NOT implemented (the gap)**: the live service account
  [`unified-trading-sa`](../../../deployment-service/terraform/gcp/main.tf#L1833) holds **`roles/storage.objectAdmin`
  project-wide** — so it can write **every** bucket in the project, including prod-tier. The §8 IAM write-protection is
  not enforced. The only thing stopping a staging/dev process (or a migration script, or a bug) writing a prod bucket is
  the code-level name resolver — credential-level isolation does not exist yet.
- There is **no dedicated migration SA**, so the documented "exceptions for migration scripts" has nothing to except
  from — everything already runs as the one god-SA.

### Bucket-name target (sync with in-flight migrations — do NOT invent)

The IAM model keys off the **actual** bucket env suffix produced by the mandated SSOT
[`resolve_bucket_name`](../../../unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py)
(`_DEPLOYMENT_ENV_SHORT_FORM`), **not** a new scheme:

| Workspace env           | Bucket suffix |
| ----------------------- | ------------- |
| dev / development       | `-dev-`       |
| **staging / stg**       | **`-stg-`**   |
| prod / prd / production | `-prd-`       |
| (E2E) test              | `-test-`      |

- **4 effective name tiers (`dev`/`stg`/`prd` + ephemeral `test`); staging is DISTINCT (`-stg-`), not folded into dev.**
- **`mock` is NOT a name suffix** — it is `CLOUD_MOCK_MODE` + scenario prefixes _inside_ buckets.
- **Two drift facts blocking clean sync:**
  - **Codex stale**: [bucket-isolation-model.md](/codex/05-infrastructure/bucket-isolation-model.md) §4 claims "staging
    shares the dev tier" (3-tier via `get_bucket_environment`) — **contradicts** `resolve_bucket_name`. Resolver is the
    mandated SSOT → doc must be corrected (P3 below).
  - **Group A vs B differ TODAY**: Group A (raw — `market-data-tick`, `instruments-store`) is **env-tiered live**
    (canonicalisation migrations already run on `…-prd-central-element-323112`); Group B (derived — `features-*`,
    `strategy-store`, `execution-store`, `ml-*`) is **env-split ROLLED BACK** (non-env-split today), and its named
    successor `plans/active/bucket_env_split_rollout_2026_06.md` **does not exist** (dangling reference in
    `deployment-service/configs/cloud-providers.yaml`). Group B IAM cannot key on a tier suffix the buckets don't carry.

## Why it matters

Operator intent (2026-06-09): "read from anything but only WRITE to the bucket with our SA credentials (exceptions for
migration scripts) … lock services from accidentally editing prod whilst working on staging." Today a single credential
can write all tiers, so the lock is advisory (code), not enforced (IAM). Composes with the same isolation goal behind
the cloud-build-router fix (deploy-time isolation) — this plan covers the **runtime data-bucket** half.

## Sequencing gate (HARD)

Two independent gates because Group A and Group B are at different stages:

1. **Group A (raw, already env-tiered)**: do NOT scope IAM until the in-flight canonicalisation walks complete
   (`master_data_canonicalisation_migration_catalogue_2026_06_07.md` + the per-AG
   `*_manifest_canonicalisation_2026_06_01` plans) — they do cross-tier whole-corpus writes on the `-prd-` buckets with
   the current broad-grant SA; scoping mid-migration breaks them. Gate = P0.1.
2. **Group B (derived, env-split rolled back)**: BLOCKED on Group B gaining tier suffixes — the buckets do not carry one
   today, so there is nothing to scope by. **RE-GATED 2026-07-13**: `bucket_env_split_rollout_2026_06.md` was unlocked +
   archived (superseded); Group B becomes env-tiered via the Wave-3 folds of
   [`bucket_estate_consolidation_to_sub100_2026_07_13.md`](bucket_estate_consolidation_to_sub100_2026_07_13.md)
   (consolidated buckets env-tiered from birth, operator ruling) — this plan's Group B IAM follows those folds.

## Open design decisions (resolve before terraform)

> **🟥 STALE 2026-07-27 (slot-12) — the tier-set + SA-design resolutions below predate a LATER, contradicting operator
> ruling.** `deployment-service/terraform/gcp/canonical_buckets.tf:44-46`: "prd + test are the only provisioned tiers
> (dev/stg retired per the 2026-07-13 operator ruling — `bucket_estate_consolidation_to_sub100_2026_07_13.md` Wave 1)."
> That ruling is dated 2026-07-13 — ONE MONTH AFTER this section's 2026-06-12 resolution — and is a WORKSPACE-WIDE,
> PERMANENT retirement of the dev/stg tier concept (20 empty dev/stg canonical buckets deleted), not a Group-A-specific
> gap. P1.1 already created `uts-dev-sa`/`uts-stg-sa` as live GCP SAs on this now-stale premise (no bindings yet — P1.2
> is un-shipped). Full analysis + recommended resolution paths:
> `issues/bucket_iam_per_tier_dev_stg_retired_ssot_contradiction_2026_07_27.md` (new, P0, operator-decision pending).
> **Do not implement P1.2's literal dev-SA/stg-SA bindings** until that decision lands — do the `-prd-` binding only
> (unambiguous, doesn't depend on the dev/stg naming question) or wait for the full re-derivation.

- [x] ✅ **Tier set — RESOLVED**: `dev` / `stg` / `prd` (+ ephemeral `test`) per `resolve_bucket_name`; **staging is a
      distinct `-stg-` tier** (the codex 3-tier "staging≡dev" framing is stale). `mock` is mode-based, not a name
      suffix. — provenance: UTL `_DEPLOYMENT_ENV_SHORT_FORM` (mandated SSOT) + operator 2026-06-09.
- [x] ✅ [DESIGN] P0. **Per-tier only vs per-domain×tier SAs.** Decision: **(a) one SA per tier**. Per-domain×tier (b)
      deferred — blast-radius benefit doesn't justify the binding-count cost before full tier isolation is in place.
      Final SA set: `uts-dev-sa` (rw `-dev-*`, r `-stg-*`/`-prd-*`), `uts-stg-sa` (rw `-stg-*`, r `-dev-*`/`-prd-*`),
      `uts-prd-sa` (rw `-prd-*`, r `-dev-*`/`-stg-*`), `uts-migration-sa` (cross-tier rw, sanctioned exception). —
      unified-trading-pm@HEAD 2026-06-12

## Phased execution

### Phase 0 — Gates + design

- [x] ✅ P0.0. **`bucket_env_split_rollout_2026_06.md` created** (2026-06-09) — env-split everywhere (Group A confirm +
      Group B un-rollback). Group B IAM (Phase 2) depends on its Phase 1/2 (provision + migrate + legacy delete).
- [x] ✅ [INFRA] P0.1. **Group A migration-completion gate**: confirm the master canonicalisation catalogue + per-AG
      `*_manifest_canonicalisation_2026_06_01` plans are DONE and no whole-corpus walk is scheduled. Blocks Group A IAM.

  > **Gate check 2026-06-12 (slot-2)**: NOT MET. G4 applies (whole-corpus walks) pending for all 5 AGs
  > (`master_data_canonicalisation_migration_catalogue_2026_06_07.md` §"Dispatch checklist" — 5× `[ ]` DATA P0 slots
  > 2–6). Blocking pre-conditions: R2-schema `[ ]` (UAC schema extensions), R3-verdicts `[ ]` (V5 dev renders + verdict
  > packs), R8-prediction `[ ]` (dry-run regen pending), 5 R5 smoke-test bugs (cefi tardis datetime64 P0, tradfi FX
  > yahoo writer P1, footystats ODDS source label P1, kalshi IS 400 P1, manifest consolidator restore P1). G4 applies
  > are operator-fired (HARD-STOP); no whole-corpus walk has completed and several are still scheduled. P0.1 checkbox
  > remains unchecked → Group A IAM (Phase 1/2) remains blocked. Re-verify after G4 applies complete. **[2026-07-14 >
  > update, verify-rerun-2 finding 205]**: the G4-whole-corpus-walk blocking premise above is now STALE —
  > `master_data_canonicalisation_migration_catalogue_2026_06_07.md`'s own status grid confirms **"G4 🟢 all 5 AGs
  > (updated 2026-07-12)"**: defi/cefi/sports/prediction `--apply` complete 2026-06-29, and TradFi `--apply` DONE
  > 2020-2026 span (7 VMs, exit_code=0 fatal=0, completed 2026-07-06, GCS re-verified 2026-07-12) — the last of the 5
  > AGs. **P0.1 checkbox left OPEN, not flipped**: the G4-walk sub-condition is now met, but this gate-check's OTHER
  > cited blocking pre-conditions (R8-prediction dry-run regen, the 5 R5 smoke-test bugs) were not re-verified in this
  > pass — re-check those specifically before flipping P0.1 to done.

  > **🟢 GATE MET — flipped 2026-07-22 (plan-reconcile "fix these issues" follow-up).** Re-checked the two remaining
  > sub-conditions directly against `master_data_canonicalisation_migration_catalogue_2026_06_07.md`: **R8-prediction**:
  > dry-plan regenerated on HEAD 2026-06-17 — `migrate_prediction_to_pred_prd_v9.py --dry-run` TOTAL planned=1,897,691,
  > 0 errors; doc's own words: "prediction GREEN, clear for G4." **5 R5 smoke-test bugs**: fix-1 (cefi tardis
  > datetime64) DONE `mtds@657f615`; fix-2 (tradfi FX yahoo writer) DONE `mtds@ed23954`; fix-3 (footystats ODDS source
  > label) DONE `instruments-service@b475ae8`; fix-4 (kalshi instruments 400) DONE `instruments-service@4562dad`; fix-5
  > (restore manifest consolidator scheduler for `instruments-store-*`) is the ONE still-open item (`[ ]` INFRA P1, line
  > 763 of that plan) — but it's a consolidator-scheduling health item with its own interim mitigation
  > (`MANIFEST_ALLOW_STALE_FALLBACK=true`), not an in-flight whole-corpus WRITE that would conflict with IAM scoping
  > (the actual thing this gate exists to protect against). No whole-corpus walk is scheduled or running. **Gate
  > genuinely met — Group A IAM (Phase 1) may proceed.**

- [x] ✅ [DESIGN] P0.2. Resolved in P0 above: option (a) per-tier SAs. Final SA list: `uts-dev-sa`, `uts-stg-sa`,
      `uts-prd-sa`, `uts-migration-sa` (cross-tier exception). — unified-trading-pm@HEAD 2026-06-12

### Phase 1 — IAM model in terraform (Group A + dev/stg first, no prod write-removal)

> **Scoping note (2026-07-22, plan-reconcile "fix these issues" follow-up).** P0.1 is now genuinely unblocked (above),
> so this phase is ready to start — but I stopped short of authoring/applying it this pass, for two concrete reasons
> rather than a vague caution:
>
> 1. **Bucket enumeration is currently blind.** `gcloud storage buckets list` under this session's active credential
>    (`unified-trading-sa`) returns effectively nothing (0-1 results) — it lacks project-level `storage.buckets.list`.
>    P1.2's per-suffix bindings are implementable via **IAM Conditions** (`resource.name.startsWith(...)` on a
>    project-level binding) rather than per-bucket enumeration, which sidesteps the listing gap in principle — but I
>    have no way to verify the condition's CEL expression matches real Group-A bucket names without being able to list
>    them, and shipping an unverified IAM condition is exactly the "confident inference is not a proof" trap.
> 2. **Blast radius**: this SA is the project's current single write identity for essentially all live data capture.
>    Even Phase 1's "no prod write-removal" framing only bounds ONE of the two ways this could go wrong — a mis-scoped
>    CEL condition on the NEW dev/stg grants (not the existing prod grant) could still misfire in ways that are hard to
>    predict without being able to enumerate + test against real bucket names first.
>
> **Concrete next step**: get a credential with `storage.buckets.list` (or run this from a session that has one),
> enumerate the actual Group A bucket names, verify the proposed `*-dev-*`/`*-stg-*`/`*-prd-*` CEL conditions match them
> exactly, then author + apply P1.1-P1.3 with that verification in hand. Not done here to avoid shipping an unverified
> IAM change to the project's primary write identity.
>
> **🟢 Bucket enumeration RESOLVED 2026-07-25** — operator ran
> `gcloud storage buckets list --project=central-element- 323112` personally (ADC, `ikenna@odum-research.com`). **The
> `*-dev-*`/`*-stg-*`/`*-prd-*` three-tier assumption above is WRONG for Group A** — real bucket names are TWO-TIER,
> `-test-`/`-prd-` only, no `-dev-`/`-stg-` suffix anywhere in this family:
>
> - `market-data-tick-{cefi,defi,pred,sports,tradfi}-{prd,test}-central-element-323112` (10 buckets)
> - `instruments-store-{cefi,defi,pred,sports,tradfi}-{prd,test}-central-element-323112` (10 buckets)
> - `features-calendar-{prd,test}-central-element-323112` (2 buckets, not per-AG)
>
> The only buckets using spelled-out `dev`/`staging`/`prod` naming are a DIFFERENT family entirely —
> `uts-{dev,staging,prod}-deployment-state` — not in scope for Group A's per-tier SA bindings. **P1.1-P1.3's CEL
> conditions must target `-test-`/`-prd-` for the market-data-tick/instruments-store/features-calendar families, NOT
> `-dev-`/`-stg-`, or the conditions will silently match zero buckets.** This corrects, not just unblocks, the Phase-1
> premise — re-derive the per-tier SA design (§ Open design decisions above) against this real naming before authoring
> terraform: a `uts-dev-sa`/`uts-stg-sa` split may not even apply to Group A if there is no `-dev-`/`-stg-` tier for it
> to bind to; the real distinction here is `-test-` (ephemeral/CI) vs `-prd-` (live). Terraform authoring (P1.1-P1.3) is
> now genuinely unblocked on the listing gap, but still needs this re-derivation pass before it's ready to apply — not
> done in this update.

- [x] ✅ [TERRAFORM] P1.1. **SHIPPED 2026-07-27 (slot-8) — `deployment-service@72c78a8`.** Defined + applied all 4 SAs
      in `terraform/gcp/bucket_iam_per_tier_sa.tf`: `uts-dev-sa`, `uts-stg-sa`, `uts-prd-sa`, `uts-migration-sa`
      (cross-tier write, the sanctioned exception for `*_service/scripts/migration_*.py`). Targeted `tofu apply` against
      the real `terraform/state/prod` backend (confirmed authoritative — it already holds the live
      `google_service_account.unified_trading` resource main.tf declares); plan showed exactly 4 adds, 0
      changes/destroys. Live-verified via `gcloud iam service-accounts list`: all 4 emails exist
      (`uts-{dev,stg,prd,migration}-sa@central-element-323112.iam.gserviceaccount.com`). **No IAM role bindings
      granted** — these are P1.2's scope, deliberately out of this todo (the 2026-07-25 finding above that Group A's
      real buckets are `-test-/-prd-` only, not `-dev-/-stg-`, affects which suffixes P1.2 binds each SA to, not whether
      the SA resources themselves should exist — an empty, unbound SA grants zero access either way). Tooling note: this
      session's environment needed `tofu` (OpenTofu, matches the pre-existing `registry.opentofu.org` lock-file entries)
      rather than the repo's much older pinned `terraform` v1.5.7 binary (protocol-incompatible with the resolved
      `google` provider v7.41.0), and a short `TMPDIR`/`TF_DATA_DIR` (a long scratchpad path broke the provider plugin's
      unix-socket handshake — `Unrecognized remote plugin message`/ "Failed to read any lines from plugin's stdout").
- **[TERRAFORM] P1.2.** Replace the project-wide `roles/storage.objectAdmin` with per-suffix bindings. **Non-checkbox
  rollup header — split 2026-07-27 (slot-12) per the M3 done-gate** (a single checkbox covering both the
  genuinely-complete SA-level slice and the still-blocked IAM-binding-apply slice left nothing honestly flippable, the
  same shape already fixed once this session for the mdps-features plan's todo 11). See P1.2a (done) and P1.2b (open,
  credential-blocked) immediately below.
- [x] ✅ [TERRAFORM] P1.2a. **DONE 2026-07-27 (slot-12) — `deployment-service@0dbc9ae`.** Re-scoped per the operator
      resolution of `issues/bucket_iam_per_tier_dev_stg_retired_ssot_contradiction_2026_07_27.md` (BLK-4b104acc): the
      dev/stg suffix bindings in the original P1.2 text are DROPPED (those tiers were permanently retired 2026-07-13,
      nothing to bind to) — `uts-test-sa` (new) is the correctly-named replacement for the actual non-prod tier
      (`-test-`). **SA-level changes LIVE-VERIFIED** (`gcloud iam service-accounts list`): `uts-test-sa` created;
      `uts-dev-sa`/`uts-stg-sa` display names updated to "(HISTORICAL — permanently unbound)", zero role bindings. "All
      SAs + CI/CD + developer identities → objectViewer broadly" from the original text: the CI/CD + developer-identity
      half is NOT addressed (no such identity is terraform-managed in this repo today — out of scope for a mechanical
      implementation, flagged as its own todo in the SSOT-contradiction issue doc).
- [x] ✅ [TERRAFORM] P1.2b. **DONE — self-serviced 2026-07-29 (interactive session, credential re-triage pass).** The
      credential gap this todo cited is resolved: this session's ADC identity (`ikenna@odum-research.com`) holds
      `resourcemanager.projects.setIamPolicy` on `central-element-323112` (live-confirmed via
      `cloudresourcemanager.projects.testIamPermissions`), and all 9 declared resources — `uts_prd_objectadmin_group_a`,
      `uts_test_objectadmin_group_a`, `uts_prd_objectadmin_group_b`, `uts_test_objectadmin_group_b`,
      `uts_dev_objectviewer`, `uts_stg_objectviewer`, `uts_prd_objectviewer`, `uts_test_objectviewer`,
      `uts_migration_objectviewer` — are confirmed LIVE in terraform state (`tofu state list`) and a scoped
      `tofu plan -target=...` across all 9 returns **"No changes. Your infrastructure matches the configuration."**
      (verified 2026-07-29). This was actually applied earlier the same session as part of the
      `bucket_iam_per_tier_dev_stg_retired_ssot_contradiction_2026_07_27.md` fix (which found and fixed the 4 broken GCP
      IAM Condition CEL expressions — `contains()`/`matches()` are undeclared references, only `startsWith`/ `endsWith`
      work — blocking `deployment-service@44002342`'s original apply); this doc's own copy of the ask just never got the
      matching retag. Ping `ikenna_orchestrator/pings/slot_5.md` can be closed as resolved. ~~BLOCKED-CREDENTIALS
      2026-07-27 (slot-12). Ping filed: `ikenna_orchestrator/pings/slot_5.md` (2026-07-27, slot-5, CREDENTIAL APPROVAL
      REQUEST). `objectAdmin` on `*-prd-*`/`*-test-*` for `uts-prd-sa`/`uts-test-sa` + `objectViewer` broadly for all 5
      SAs are DECLARED in `deployment-service/terraform/gcp/bucket_iam_per_tier_sa.tf` (`tofu validate` + `tofu fmt`
      clean, targeted `tofu plan` showed exactly 8 adds/2 changes/0 destroys) but NOT YET APPLIED — this session's
      active credential (`github-actions-deploy` SA) lacks `resourcemanager.projects.getIamPolicy`/`setIamPolicy`
      entirely (confirmed: `gcloud projects get-iam-policy central-element-323112` 403s outright for this identity; the
      same error class hit ~15 unrelated pre-existing resources in a full untargeted plan too, confirming a
      whole-project permission gap, not something wrong with the new resources).~~
- [x] ✅ [TERRAFORM] P1.3. ~~Verify dev/stg workloads read everything, write their own tier, and are **IAM-denied** a
      `-prd-` write (negative test).~~ **MOOT, closed via P2.3 — verified by plan_reconciler 2026-08-10.** As literally
      worded this tests a tier pair (`dev`/`stg`) that P1.2a (above, DONE 2026-07-27) already confirms was permanently
      retired 2026-07-13 — `uts-dev-sa`/`uts-stg-sa` are "(HISTORICAL — permanently unbound)" with zero role bindings,
      so there is no live dev/stg workload left to test. P2.3 (below, DONE 2026-08-02) already performed the equivalent
      negative test on the REAL current tier pair: live-verified `uts-prd-sa` can write `-prd-`/denied `-test-`;
      `uts-test-sa` can write `-test-`/denied `-prd-` — the actual IAM-level cross-tier-write-403 proof this todo was
      asking for, just against the tier names that replaced dev/stg rather than the retired ones. No prod write-grant
      removal needed here either way (P2 handles that separately, unaffected by this closure).

### Phase 2 — Prod cutover + wiring

> **🟥 SEQUENCING HAZARD found 2026-07-30 (slot-11) — P2.1 as originally written is UNSAFE to execute before P2.2.**
> `unified-trading-sa` is the ACTUAL LIVE runtime identity for essentially the entire fleet today (deployment-api, Cloud
> Run services, VM backfill launchers — `main.tf:651` comment: "unified-trading-sa, deployment-api's actual runtime
> identity"). Live-verified 2026-07-30: zero references to `uts-prd-sa`/`uts_prd`/`uts-test-sa` anywhere in
> deployment-service outside `terraform/`
> (`grep -rn "uts-prd-sa\|uts_prd\|uts-test-sa" --include=*.py --include=*.yaml --include=*.sh .` → 0 hits), and only 5
> of 165 `scripts/vm/launch-*.sh` even pass `--service-account=` at all. P2.2 ("wire each runtime to its tier SA") is
> still fully unchecked — **nothing anywhere in the codebase authenticates as `uts-prd-sa` yet.** Removing
> `unified_trading_storage_admin` (`main.tf:598-602`, the project-wide `roles/storage.objectAdmin` grant — the literal
> "god-SA objectAdmin" this todo names) BEFORE P2.2 rewires runtimes would immediately 403 every live + batch GCS write
> across the whole fleet (MTDS/MDPS/IS/features/execution/strategy stores, everything) — a direct violation of the
> data-pipeline-correctness-is-the-heartbeat HARD RULE, and it would ALSO fail P2.1's own stated verification ("verify
> live/batch prod workloads retain `-prd-` write") since they would in fact LOSE write access. **Split below mirrors
> this plan's own precedent** (P1.2 → P1.2a/P1.2b: "a single checkbox covering both a genuinely-complete slice and a
> still-blocked slice left nothing honestly flippable"). Full evidence + recommendation:
> `issues/bucket_iam_p2_god_sa_removal_before_runtime_rewire_2026_07_30.md`.

- [x] ✅ [TERRAFORM] P2.1a. **`-prd-` write-scope is already live** — P1.2b's `uts_prd_objectadmin_group_a` /
      `uts_prd_objectadmin_group_b` bindings (`bucket_iam_per_tier_sa.tf`) were confirmed LIVE via `tofu state list` + a
      clean `tofu plan` on 2026-07-29 (P1.2b's own evidence trail). No new terraform state change made this pass —
      re-verified by reading `bucket_iam_per_tier_sa.tf` against that evidence. — slot-11, 2026-07-30.
- [x] ✅ [TERRAFORM] P2.1b. **DONE 2026-08-08 (slot-4) — deployment-service@f514b6a0.** Removed
      `unified_trading_storage_admin` (god-SA `roles/storage.objectAdmin` project-wide on `unified-trading-sa`) via
      targeted `tofu apply -target=google_project_iam_member.unified_trading_storage_admin` (1 destroyed).
      Live-verified: SA no longer holds `objectAdmin` (note: `roles/storage.admin` undeclared drift still present —
      tracked in `issues/unified_trading_sa_live_iam_drift_vs_terraform_2026_07_31.md`, out of P2.1b scope). P2.3 re-run
      post-removal: all 5 PASSED (`uts-prd-sa` writes `-prd-`/denied `-test-`; `uts-test-sa` writes `-test-`/denied
      `-prd-`; `uts-migration-sa` writes `-prd-` via unconditioned `objectAdmin` per P2.2f). Migration SA test assertion
      updated False→True (P2.2f DONE 2026-08-03). tokenCreator grants self-granted + immediately revoked post-test.
      **RULED 2026-08-06 (operator): APPROVED, AO-dispatchable — `[OPERATOR]` tag removed.** Both hard gates are
      satisfied with live evidence, not just checkbox claims: P2.2e is DONE 2026-08-04 with multi-endpoint live 200s
      confirming deployment-api runs on `uts-prd-sa`; P2.3's integration test (`test_bucket_iam_tier_isolation.py`) was
      live-RUN 2026-08-02 and all 5 PASSED, directly proving the IAM-level cross-tier-write-403 behavior this todo's own
      "verify" clause asks for (`uts-prd-sa` writes `-prd-`/denied `-test-`; `uts-test-sa` writes `-test-`/denied
      `-prd-`). **Operator's standing policy (2026-08-06): plan-scoped GCS/IAM CRUD operations already covered by this
      corpus's delete-safety and reversibility safeguards should be ruled and dispatched, not re-asked interactively
      each time** — this todo's own text already specifies the exact execution + verification procedure (remove binding,
      confirm prd retained, confirm dev/stg denied), which is itself the safeguard. Re-run P2.3's live test immediately
      after the removal (not just before) to close the loop. **Remove the god-SA `objectAdmin`**
      (`unified_trading_storage_admin` in `main.tf:598-602`); verify live/batch prod workloads retain `-prd-` write (now
      via `uts-prd-sa`, not the god-SA); verify a dev/stg credential is **denied** a `-prd-` write (IAM-level, not just
      name-resolver). **HARD-GATED on P2.2e AND P2.2d (below) both completing + being live-verified first** — do not
      remove the god-SA grant while any runtime still authenticates as `unified-trading-sa` OR the GCP default compute
      SA for writes. **P2.2c alone (2026-07-31) is NOT sufficient for this gate** — it wires the identity into
      `deploy-shared.sh` and live-verifies `uts-prd-sa`'s grants, but deployment-api's actual LIVE runtime is still
      `unified-trading-sa` (traffic cutover split out as the new P2.2e, currently blocked on a cold-start reliability
      issue) — do not misread P2.2c's ✅ as satisfying this gate. **Group B buckets join here only after the
      consolidation plan's Wave-3 folds provision their `-{env}-` form (re-gated 2026-07-13; env-split plan archived).**
      **`[OPERATOR]`-tagged 2026-07-30 (slot-13)**: this checkbox has no structured `depends_on`/`gate_on_depends` link
      to P2.2 (same-plan todos can't express a per-todo prereq — CLAUDE.md), so the backlog regenerator has
      auto-dispatched this fleet-wide-blast-radius IAM removal to a worker TWICE in one day despite the HARD-GATED note
      above (slot-11 earlier today, slot-13 this pass) — both independently declined per
      `issues/bucket_iam_p2_god_sa_removal_before_runtime_rewire_2026_07_30.md`. `[OPERATOR]` routes this to the
      operator's blocked-queue instead of re-offering it to workers who can only re-derive the same "not yet" verdict.
      **Retag back to plain `[TERRAFORM]`** once P2.2e and P2.2d are both done + live-verified (every write-path runtime
      confirmed running as its tier SA, not `unified-trading-sa` or the default compute SA) — do not leave this tag
      stale per CLAUDE.md's retag-on-resolve rule.

      > **🟥 Note (2026-07-31, slot-14)**: even once this todo removes `unified-trading-sa`'s `storage.objectAdmin`,
                                                                                                                                                                                                                                                                                                                                                                                                                              > that SA still live-holds `roles/resourcemanager.projectIamAdmin` + `roles/iam.serviceAccountAdmin` (undeclared
                                                                                                                                                                                                                                                                                                                                                                                                                              > in any terraform in this repo) — both self-escalation-capable, i.e. it could re-grant itself storage access
                                                                                                                                                                                                                                                                                                                                                                                                                              > (or any other role) without going through terraform at all. See
                                                                                                                                                                                                                                                                                                                                                                                                                              > `issues/unified_trading_sa_live_iam_drift_vs_terraform_2026_07_31.md` — a full de-privilege of this SA is not
                                                                                                                                                                                                                                                                                                                                                                                                                              > actually complete until that doc's P1/P2 also land.

> **🟥 P2.2 SCOPE GAP found 2026-07-30 (slot-12) — "wire each runtime to its tier SA" is not mechanically executable
> today.** Investigation (live GCP IAM queries + static analysis, no state mutated) found 3 independently-blocking
> findings: (1) `uts-prd-sa`/`uts-test-sa`/`uts-migration-sa` hold ONLY storage roles (live-verified via
> `gcloud projects get-iam-policy` — zero secretmanager/pubsub/bigquery/run.invoker) — wiring any real runtime to them
> today breaks its Secret Manager / Pub/Sub / BigQuery access immediately; (2) the "instead of `unified-trading-sa`"
> framing above is itself wrong for VM launchers — 155/165 `launch-*.sh` scripts actually run as the GCP **default
> compute SA** (`main.tf`'s own comment + a live IAM query confirm this), which live-verified holds 28 UNCONDITIONAL
> project-wide roles incl. `roles/storage.admin` and `roles/iam.serviceAccountTokenCreator` — a BIGGER live security
> exposure than the god-SA grant this plan exists to close; (3) a second, already-partially-live per-service SA scheme
> (`deployment-service/configs/gcp_service_accounts.yaml`, `features-prod`/etc.) coexists unreconciled with this plan's
> per-tier design. Full evidence + recommendation:
> `issues/bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md`. Split below mirrors this
> plan's own P1.2→P1.2a/P1.2b precedent.

- [x] ✅ [OPERATOR] P2.2a. **RESOLVED 2026-07-31** — operator ruling on BLK-0c84ceac (recorded in
      `/plans/archive/issues/bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md` §
      "Hybrid (C) boundary proposal — operator decision surface (2026-07-31)"): **"C: hybrid" — per-tier SAs
      (`uts-prd-sa`/`uts-test-sa`/`uts-migration-sa`) stay the write-owner for the Group A/B raw-data buckets this plan
      already covers; per-service SAs (`deployment-service/configs/gcp_service_accounts.yaml`) own already-migrated
      domain services (`features-prod` etc.); reconcile the undocumented ad-hoc SA family (`uts-*-batch-sa`,
      `t1-batch-sa`, ...) into whichever bucket it structurally belongs.** Full boundary table (bucket→scheme mapping +
      ad-hoc-family disposition) already drafted in the linked issue doc's "Hybrid (C) boundary proposal" section — that
      table is the ratified answer, not just a proposal, as of this ruling. Unblocks P2.2b-P2.2d. — slot-14, 2026-07-31.
- [x] ✅ [TERRAFORM] P2.2b. **DONE 2026-07-31 (slot-14) — `deployment-service@e8684fe`.** Retagged back to plain
      `[TERRAFORM]` (P2.2a resolved above). Granted the 7 non-storage roles `unified-trading-sa` currently holds
      (`bigquery.dataEditor`, `secretmanager.secretAccessor`, `run.invoker`, `pubsub.editor`,
      `compute.instanceAdmin.v1`, `iam.serviceAccountUser`, `artifactregistry.reader` — `main.tf`'s `unified_trading_*`
      project members) to `uts-prd-sa`/`uts-test-sa`/`uts-migration-sa`, project-wide, mirroring `unified-trading-sa`'s
      own (unconditioned) grant scope. Applied via `tofu apply` against the real `terraform/state/prod` backend (21
      adds, 0 changes/destroys); live-verified via `gcloud projects get-iam-policy` — all 3 SAs now hold all 7 roles; a
      follow-up `tofu plan` shows 0 changes (config/state/live in sync). INERT until P2.2c/P2.2d actually wire a runtime
      to one of these SAs — no live runtime identity changed as a result.
- [x] ✅ [CODE] P2.2c. **DONE 2026-07-31 (slot-5, reconciled with a concurrent slot-7 session on the same file) —
      `deployment-service@a2b90f9e7351f23c9ce48130e1926acff066f5ae`/`c518cda` + `118ad9e`.** Wired `deploy-shared.sh`'s
      default `--service-account` for `uts-shared-deployment-api`/deployment-api from `unified-trading-sa` to
      `uts-prd-sa` (env-overridable via `RUNTIME_SA=` for an instant revert), and live-verified access: Secret Manager
      `versions.access`, Pub/Sub `topics.list`, BigQuery `datasets.list`, Storage `objects.list` (Group A `-prd-`) all
      confirmed working directly via an impersonated `uts-prd-sa` token. Concurrently, slot-7 found + fixed 2 grant gaps
      this check didn't cover (`roles/bigquery.jobUser`, bucket-level write on
      `unified-deployment-state-*`/`deployment-scripts-*`), live-verified via real endpoints — see
      `issues/bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md` P2 (flipped ✅ there).
      Also fixed an unrelated drift bug found along the way: `deploy-shared.sh` had a stale `--memory=4Gi --cpu=2`
      predating `cloudbuild.yaml`'s documented 2026-07-17 8Gi→16Gi OOM fix for this service — now `16Gi/4cpu` to match.
      **`uts-prd-sa`'s functional readiness for deployment-api is thoroughly confirmed** — the remaining live-traffic
      cutover is split out below as P2.2e (new finding, blocked on a separate reliability issue, not on anything this
      checkbox covers).
- [x] ✅ [CODE] P2.2d1. **DONE 2026-07-31 (slot-7) — `deployment-service@0ff5bc8`.** Split out of P2.2d (single checkbox
      covering both a genuinely-complete slice and a large still-open one — mirrors this plan's own P1.2a/P1.2b,
      P2.1a/P2.1b, P2.2a-e precedent). Added `lc_tier_service_account <env> <project>` to
      `scripts/vm/lib/launcher_common.sh` (env→`uts-prd-sa`/`uts-test-sa` resolver, `LC_RUNTIME_SA=` override for an
      instant revert — mirrors `deploy-shared.sh`'s `RUNTIME_SA=` pattern from P2.2c) and an optional 8th
      `service_account` arg to `lc_gcloud_create()` (omitted/empty preserves prior default-compute-SA behavior — fully
      backward-compatible). Wired all 3 real `lc_gcloud_create()` callers whose target buckets are unambiguously Group
      A/B raw-data per the ratified bucket→scheme table (`launch-canonical-smoke-vm.sh`,
      `launch-instruments-smoke-vm.sh`, `launch-deribit-options-chain-daily.sh`) — dry-run verified
      `--env prod/staging/dev` each resolve to the correct tier SA email. `launch-qg-snapshot-vm.sh` (the 4th
      `lc_gcloud_create()` caller) deliberately left UNWIRED — its write target (`${PROJECT}-deployment-events`) doesn't
      match the ratified table's Group A/B raw-data definition; folded into P2.2d2 below rather than guessed.
- [x] ✅ [CODE] P2.2d2a. **DONE 2026-08-01 (slot-7) — `deployment-service@7538587`/`01edfe8`/`ef891c1`.** Split out of
      P2.2d2 (single checkbox covering both a genuinely-classifiable-and-safe slice and a large still-ambiguous one —
      mirrors this plan's own P1.2a/P1.2b, P2.1a/P2.1b, P2.2a-e, P2.2d1 precedent). Ran the per-launcher tier
      classification pass P2.2d2 called for: of 134 direct-`gcloud`-calling launchers (133 found via
      `grep -L 'lc_gcloud_create\|--service-account='`, +1 `launch-api-football-backfill-vm.sh` recovered after its own
      comment — "rather than the `lc_gcloud_create` wrapper" — produced a grep false-positive that had excluded it),
      cross-referenced each against the target service tarball it pulls (`lc_verify_tarball_freshness`/tarball-name
      grep) and, for `market-data-processing-service`, against its actual `resolve_bucket_name(kind=...)` call sites
      (confirmed MDPS candles land in `kind="market-data"` — the SAME `market-data-tick-*` family as raw MTDS ticks, not
      a separate bucket kind). **95 launchers** write EXCLUSIVELY into Group A raw-data
      (`market-data-tick-*`/`instruments-store-*`) with no `features-service` co-dependency — unambiguously covered by
      `uts-prd-sa`/`uts-test-sa`'s IAM condition, so wired via
      `--service-account="$(lc_tier_service_account "$DEPLOYMENT_ENV" "$PROJECT")"` on their real
      `gcloud compute instances create` invocation (87 via a scripted transform targeting the `--project=` line +
      dry-run/shellcheck/`bash -n` verified across all 95; 8 hand-edited for non-standard formatting — arrays, same-line
      flags, no-backslash-continuation — 3 of those also needed `lib/launcher_common.sh` sourced in for the first time).
      Full per-file list + rationale in the 3 commits above. `launch-cefi-week-test.sh` needed no edit (pure delegator
      to the now-wired `launch-cefi-forward-poll.sh`, fixed transitively).
- [x] ✅ [CODE] P2.2d2b. **DONE 2026-08-01 (slot-7) — `deployment-service@3dc37d6`.** Per-script bucket-name verify (as
      required) + wire for the 12 features-service launchers P2.2d2a deliberately skipped. **10 wired** via
      `--service-account="$(lc_tier_service_account "${DEPLOYMENT_ENV}" "$PROJECT")"`: `launch-features-backfill-vm.sh`,
      `launch-features-sharded-backfill.sh`, `launch-features-sports-backfill-vm.sh`, `launch-features-vm.sh` (all
      confirmed via `features_service/common/__init__.py`'s shared `resolve_bucket(kind="features", asset_group=...)`
      wrapper → canonical `features-{ag}-`), `launch-mdps-features-live.sh` + `launch-mtds-live.sh` (per-asset_group
      `market-data`/`features` kinds, Group A/B), `launch-prediction-arb-detector.sh` (confirmed via
      `features_service/cross_instrument/config.py:142` — resolves to canonical `features-pred-`, NOT the legacy
      `features-cross-instrument-prediction-*` bucket the plan warned about for its sibling
      `launch-prediction-features-vm.sh`), `launch-prediction-live.sh` (`VM_SERVICE=market_tick_data_service` →
      `market-data-tick-pred-`, Group A), `launch-sports-derived-features-census-vm.sh` (env-aware via VM metadata; the
      shell `$SPORTS_BUCKET` var is echo-only, not the real write path).
      `launch-sfi-progressive-features-backfill-vm.sh` wired with a HARDCODED `"prod"` tier (not `${DEPLOYMENT_ENV}`)
      because its `--bucket` arg is hardcoded `features-sports-prd-*` regardless of `--env` — a dynamic lookup would
      carry `uts-test-sa` into a run that still writes the prd bucket and 403. `launch-features-onchain-backfill-vm.sh`
      needed no edit — it `exec`s into the now-wired `launch-features-vm.sh` (pure delegator, resolves transitively,
      same pattern as P2.2d2a's `launch-cefi-week-test.sh`). **2 deliberately left unwired** (split out below, not
      silently dropped): `launch-canonical-migration-vm.sh` (multi-category dispatcher writing BOTH Group A/B raw-data
      AND the `deployment-scripts` control-plane bucket in the same run — the tier SA's IAM condition is prefix-scoped
      to Group A/B only, wiring would break its staging-output writes) and `launch-features-cross-cutting.sh` (genuinely
      cross-asset_group; no `resolve_bucket_name` call found anywhere in its live runner code —
      `features_service/cross_instrument/live/` + `features_service/calendar/live/`; its own header comments describe
      bucket names — `features-cross-instrument-{env}-{pid}` / `features-multi-timeframe-{env}-{pid}` — that don't exist
      anywhere in the current `cloud-providers.yaml`, i.e. stale documentation of a pre-Fold-A shape). The **~11
      ambiguous/control-plane launchers are now fully dispositioned**: `launch-bucket-rsync-vm.sh` (explicitly
      cross-bucket, flat→tiered — same migration-SA-blocked class as the 2 migration launchers, folded into P2.2d2c2
      below) + 6 confirmed OUT OF SCOPE via the authoritative registry (`deployment_service/vm_prefix_registry.py`
      `VM_PREFIX_TO_BUCKET`, all map to `bucket=None`): `launch-dashboard-vm.sh`, `launch-disaster-drill-cron-vm.sh`,
      `launch-dr-drill-cutover-vm.sh`, `launch-sports-scheduler-vm.sh`, `launch-vm-zombie-watchdog.sh` (control-plane /
      heartbeat-only, confirms the plan's own "not a data writer" suspicion for each) +
      `launch-features-onchain-backfill-vm.sh` (resolved above, pure delegator). The 17 execution/strategy/ml-service +
      9 AWS launchers remain correctly out of scope (unchanged from P2.2d2a's disposition — per-service SA /
      different-cloud, not this helper). Evidence: `bash -n` + shellcheck clean on all 10 touched files;
      `quality-gates.sh` green; CI verified.
- [x] ✅ [TERRAFORM] P2.2f. **NEW finding, opened 2026-08-01 (slot-7) during P2.2d2b.** `uts-migration-sa` — this plan's
      own § Open design decisions designates it "the sanctioned cross-tier writer" for migration scripts — currently
      holds ONLY `roles/storage.objectViewer` project-wide (`bucket_iam_per_tier_sa.tf`'s `uts_migration_objectviewer`
      resource); it has ZERO write grant (no `objectAdmin`, conditioned or otherwise). Confirmed by reading the
      terraform source (not yet re-confirmed against live GCP — do that before granting). It cannot actually write
      anything, contradicting its stated purpose and blocking every launcher that needs it
      (`launch-legacy-bucket-migration-sharded.sh`, `launch-gcs-migration-bundle-vm.sh`, `launch-bucket-rsync-vm.sh` —
      see P2.2d2c2 below). **DONE 2026-08-03 (interactive session) — RESOLVED with a corrected finding, not option (b)
      as originally recommended.** P2.2g's investigation (below) found 2 of the 3 launchers this todo named are DEAD
      CODE, not live blockers: `launch-legacy-bucket-migration-sharded.sh`'s target script
      (`migrate_legacy_tick_buckets_to_canonical.py`) was deliberately deleted
      `market-tick-data-service@4d235caf`/`f8276e22` (2026-07-25) — its own `Delete-when` OR-clause ("after prod-run
      verified + GCS orphan-sweep=0") was satisfied by E8's confirmed deletion of the legacy source bucket
      `market-data-tick-sports-central-element-323112`; `launch-gcs-migration-bundle-vm.sh`'s target script
      (`gcs_migration_bundle_2026_05_08.py`) was deleted even earlier, `unified-trading-pm@075f64279` (2026-05-20,
      "Phase 9 complete", plan archived to `plans/archive/2026_05/gcs_migration_bundle_pipeline_mode_2026_05_08.md`).
      Neither needs any IAM grant — they are not runnable. Only `launch-bucket-rsync-vm.sh` (`Lifecycle: permanent`) is
      live, and per P2.2g's finding, it is a GENERIC cross-family migration tool whose `--dest-bucket` varies per
      invocation — GCP IAM Conditions support only `startsWith`/`endsWith` on `resource.name` (confirmed live
      2026-07-29, see `group-a-prd-tier-only`'s comment in the .tf), and neither can express "any tiered bucket
      regardless of family" without an enumerable fixed prefix, which this generic tool doesn't have. Option (b) is
      therefore NOT ACHIEVABLE for this launcher (unlike the fixed-family Group A/B lists uts-prd-sa/uts-test-sa use) —
      option (a), an unconditioned `storage.objectAdmin`, is the correct design here, matching uts-migration-sa's own
      declared purpose ("sanctioned cross-tier write exception... used only by migration scripts") rather than a
      shortcut around scoping it. **Applied + live-verified**:
      `deployment-service/terraform/gcp/bucket_iam_per_tier_sa.tf` `google_project_iam_member.uts_migration_objectadmin`
      (full rationale in its own comment block),
      `ENV=prod     ./tofu.sh apply -target=google_project_iam_member.uts_migration_objectadmin` — scoped apply (did NOT
      touch the ~24 unrelated pending changes already sitting in this shared prod state;
      `Plan: 1 to add, 0 to change, 0 to     destroy` before applying). Live-verified via a real IAM policy read (ADC
      token + `cloudresourcemanager.googleapis.com:getIamPolicy`, not just `tofu` state): `uts-migration-sa` now holds
      `roles/storage.objectAdmin` in addition to its existing `objectViewer` + P2.2b's 7 non-storage roles. **INERT
      today** — `launch-bucket-rsync-vm.sh` does not pass `--service-account` at all (confirmed by reading the launcher
      source), so its VMs currently run under the project default compute SA, not `uts-migration-sa`; wiring it is
      tracked as P2.2d2c2 below (a code change, not gated on this todo anymore).
- [x] ✅ [DATA] P2.2g. **NEW 2026-08-03 — resolve the staleness/scope question the P2.2f finding above raised, per
      operator direction: "naming conventions should match reality and script should exist else docs update."** (1)
      Confirm whether `launch-legacy-bucket-migration-sharded.sh`'s Phase-5 migration is actually complete (check the
      referenced `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` plan's own status/todos, and whether
      `migrate_legacy_tick_buckets_to_canonical.py` was deleted post-completion vs. never committed/misnamed). If
      complete: delete the launcher (its own `Lifecycle: oneoff` header already says so) and drop it from P2.2f/
      P2.2d2c2's scope — it needs no IAM grant. If genuinely still needed: restore or correctly re-reference the script
      so the launcher is actually runnable, and keep it in scope. Either way, fix every doc (this plan +
      `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`) so the launcher's documented state matches
      reality. (2) For `launch-bucket-rsync-vm.sh`: since it's generically parameterized across multiple flat bucket
      families rather than one fixed name, decide the CEL condition shape for P2.2f option (b) that covers "any
      flat/legacy-named bucket" (e.g. absence of the `-{env}-` tier suffix) rather than trying to enumerate a
      per-launcher prefix list. **Done when**: P2.2f's "the other 2 need their own enumeration" is either resolved with
      a concrete condition/decision for both, or one is confirmed out of scope with docs updated to match. **DONE
      2026-08-03 (interactive session).** (1) Confirmed COMPLETE via git history, not just the launcher's own header
      claim: `migrate_legacy_tick_buckets_to_canonical.py` was deleted `market-tick-data-service@4d235caf` 2026-07-25,
      commit message states its `Delete-when` OR-clause was satisfied by E8's confirmed deletion of
      `market-data-tick-sports-central-element-323112` (the migration's legacy source, gone) — this predates and is
      independent of this plan's own investigation, i.e. a genuinely separate team/session already closed this migration
      out. **Widened the check beyond what this todo asked** and found `launch-gcs-migration-bundle-vm.sh` is ALSO dead
      by the same pattern (`gcs_migration_bundle_2026_05_08.py` deleted `unified-trading-pm@075f64279`, 2026-05-20,
      "Phase 9 complete" — its whole plan is archived), which P2.2f's own 2026-08-03 Progress-Log entry had incorrectly
      treated as merely "already usable" (only the bucket-family naming PATTERN was checked, not whether the script
      itself still existed). **Deleting the 2 dead launcher scripts + their
      `vm_prefix_registry.py`/`launcher_registry.py`/`tarball_pins.py` registrations is real, separate code work** (one
      of the two, `launch-gcs-migration-bundle-vm.sh`, is also referenced by the live
      `issues/vm_launcher_class_b_no_stall_kill_gap_2026_07_27.md` P2 todo's launcher list — that reference needs
      updating in the same change) — NOT done in this pass to keep this todo's scope to the docs/IAM question it was
      actually gating; tracked as new P2.2i below. (2) For `launch-bucket-rsync-vm.sh`: confirmed via the file's own
      existing `group-a-prd-tier-only` comment that GCP IAM CEL supports only `startsWith`/`endsWith` on
      `resource.name`, and neither can express "any tiered bucket regardless of family" for a tool whose bucket family
      varies per invocation (an open/growing set across future cutover waves) — `startsWith` needs a fixed family prefix
      (which doesn't exist here) and `endsWith` can't reach the bucket-name segment for an Object-level condition (the
      unbounded object key sits at the true end of `resource.name`, not the bucket name). **Ruled: option (b) is not
      achievable for this launcher; option (a) (unconditioned) is correct**, since this SA exists specifically to be the
      cross-tier exception — see P2.2f's DONE entry for the applied grant.
- [x] ✅ [CODE] P2.2d2c. **NEW, split from P2.2d2b 2026-08-01 (slot-7).** Wire the 3 launchers blocked on the
      migration-SA write-grant gap (P2.2f above): `launch-legacy-bucket-migration-sharded.sh`,
      `launch-gcs-migration-bundle-vm.sh`, `launch-bucket-rsync-vm.sh` — all three read/write a LEGACY (non-env-tiered,
      flat) bucket name that no tier SA's `startsWith` IAM condition matches. **DONE 2026-08-02 (slot-13) —
      `deployment-service@24e0878`, the 2 launchers this todo flagged as independently investigable (not gated on
      P2.2f)**: `launch-canonical-migration-vm.sh` — confirmed via `terraform/gcp/bucket_iam_per_tier_sa.tf` +
      `issues/pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md` that BOTH `uts-prd-sa` (already
      terraform-declared) and `uts-test-sa` (live-granted 2026-08-01, was terraform-UNdeclared — now added in this same
      commit, closing that drift) already hold a non-tier-conditioned `storage.objectAdmin` grant on
      `deployment-scripts-<project>` — so a single
      `--service-account="$(lc_tier_service_account "$DEPLOYMENT_ENV"     "$PROJECT")"` covers BOTH its env-tiered Group
      A/B migration-target writes AND its `CODE_BUCKET` (mapping-TSV + standard VM observability) writes; no second
      `--service-account` needed. Wired. `launch-features-cross-cutting.sh` — read
      `unified_trading_library/feature_service_base/live_aggregator.py`'s `CrossCuttingFeaturesRunner` in full: it is
      EVENT-ONLY (Redis Streams in, `FeaturesComputedEvent` out via an injected `emission_publisher`), no
      GCS/`resolve_bucket_name` call anywhere — confirms the header comment's
      `features-cross-instrument-{env}-{pid}`/`features-multi-timeframe-{env}-{pid}` bucket names are stale (corrected
      in this commit, matching P2.2d2b's own suspicion). So this launcher needs only the standard tier SA for its
      observability writes, same as every other launcher — wired via `lc_tier_service_account`. Both `bash -n` +
      shellcheck clean; `quality-gates.sh` green; CI verified. **The 3 migration-SA-blocked launchers remain undone,
      split out below as P2.2d2c2** (not silently dropped — mirrors P2.2d2b's own split precedent).
- [x] ✅ [CODE] P2.2d2c2. **NEW, split from P2.2d2c 2026-08-02 (slot-13).** Wire the 3 launchers still blocked on the
      migration-SA write-grant gap: `launch-legacy-bucket-migration-sharded.sh`, `launch-gcs-migration-bundle-vm.sh`,
      `launch-bucket-rsync-vm.sh` — all three read/write a LEGACY (non-env-tiered, flat) bucket name that no tier SA's
      `startsWith` IAM condition matches. Gated on P2.2f (still open — `[OPERATOR]` grant not yet made).
      **`[OPERATOR]`-tagged 2026-08-02 (slot-12)**: re-verified independently before touching code — live GCP
      (`gcloud projects get-iam-policy central-element-323112 --filter="bindings.members:uts-migration-sa@..."`)
      confirms `uts-migration-sa` still holds ONLY `roles/storage.objectViewer` project-wide, zero write grant, matching
      terraform source (`bucket_iam_per_tier_sa.tf`'s `uts_migration_objectviewer` resource — no `objectAdmin` block for
      this SA). Wiring any of these 3 launchers to it today would 403 on every write; wiring them to a tier SA instead
      would be wrong too (P2.2f's own text: none of the 3's legacy flat bucket names match any tier SA's `startsWith`
      condition). **NARROWED + retagged 2026-08-03 (interactive session, P2.2f/g now DONE)**: the gate is cleared —
      `uts-migration-sa` holds `roles/storage.objectAdmin` live (see P2.2f's DONE entry) — but 2 of the 3 launchers
      named above no longer need wiring at all: `launch-legacy-bucket-migration-sharded.sh` and
      `launch-gcs-migration-bundle-vm.sh` are dead code (their target scripts are deleted, per P2.2g's finding) — they
      belong in P2.2i's deletion scope below, not here. This todo now scopes to ONLY `launch-bucket-rsync-vm.sh`: add
      `--service-account="uts-migration-sa@${PROJECT}.iam.gserviceaccount.com"` to its `gcloud compute instances create`
      call (it currently passes no `--service-account` at all, so its VMs run under the project default compute SA —
      confirmed by reading the launcher source). Retagged back to plain `[CODE]` per CLAUDE.md's retag-on-resolve rule —
      do not leave `[OPERATOR]` stale now that the grant is live. Same structural gap as P2.1b above — this checkbox has
      no structured `depends_on`/`gate_on_depends` link to P2.2f (same-plan todos can't express a per-todo prereq —
      CLAUDE.md), so the backlog regenerator will keep re-offering it to workers who can only re-derive the same "not
      yet" verdict. **DONE 2026-08-03 (slot-9) — `deployment-service@3c5acfb`.** Added
      `--service-account="uts-migration-sa@${PROJECT}.iam.gserviceaccount.com"` to `launch-bucket-rsync-vm.sh`'s
      `gcloud compute instances create` call, exactly as scoped above. `bash -n` clean, `shellcheck` clean (only the
      pre-existing SC1091 info-level note every launcher carries for its `lib/launcher_common.sh` source line).
      `quality-gates.sh` green (219s); SHA verified reachable on `origin/live-defi-rollout` via
      `git merge-base --is-ancestor`.
- [x] ✅ [CODE] P2.2i. **NEW 2026-08-03 (interactive session), split from P2.2g.** Delete the 2 confirmed-dead migration
      launchers found by P2.2g: `deployment-service/scripts/vm/launch-legacy-bucket-migration-sharded.sh` and
      `launch-gcs-migration-bundle-vm.sh` (both target scripts long deleted — see P2.2f/g's DONE entries for the exact
      commits). Mirrors the precedent `market-tick-data-service@4d235caf`/`f8276e22` already set for the script side.
      Remove each launcher's entries from `deployment_service/vm_prefix_registry.py`,
      `deployment_service/vm/tarball_pins.py` (the `launch-legacy-bucket-migration-sharded.sh` mention in its
      pin-eligible-launchers list) and `deployment_service/data_pipeline_monitors/launcher_registry.py` (both
      `VM_PREFIX_TO_LAUNCHER` entries + the `canonical-migration-legacy-*`/`gcs-migration-bundle-*` prefix families in
      `vm_prefix_registry.py`'s `VM_PREFIX_TO_BUCKET`). Update `tests/unit/test_tarball_pins.py`'s reference to
      `launch-legacy-bucket-migration-sharded.sh`. **Also update**
      `issues/vm_launcher_class_b_no_stall_kill_gap_2026_07_27.md` — its P2 `[HUMAN]` todo lists
      `launch-gcs-migration-bundle-vm.sh` among "6 doubly-unprotected launchers" needing a stall-kill fix; remove it
      from that list (a deleted launcher has no VMs to protect) rather than leaving a stale reference. **Done when**:
      both scripts + all registry/test/doc references are gone, `deployment-service`'s `quality-gates.sh` is green, and
      a grep for either launcher's filename across both repos returns only this plan's own historical Progress Log
      entries. **DONE 2026-08-03 (slot-7)** — `deployment-service@d407b8b` (deleted both scripts),
      `deployment-service@244f494` (registry/test refs in `vm_prefix_registry.py`, `launcher_registry.py`,
      `tarball_pins.py`, `test_tarball_pins.py`), `deployment-service@b2ed2ca` (2 more stray refs the first QG run
      surfaced: a leftover generic `"gcs-migration-bundle-": None` key in `launcher_registry.py`'s
      `VM_PREFIX_TO_LAUNCHER` — a separate dict section from the per-AG entries, caught by
      `test_no_extra_registry_prefixes` — and a now-unreferenced `canonical-migration-legacy-` entry in
      `test_vm_zombie_watchdog.py`'s `_TEMPLATE_FAMILY_PREFIXES` exemption set). Also updated
      `issues/vm_launcher_class_b_no_stall_kill_gap_2026_07_27.md` (removed `gcs-migration-bundle-*` from the P2
      6-launcher list), `plans/epics/infrastructure_master.md` (closed the now-moot `launch-gcs-migration-bundle-vm.sh`
      GCS-script-staging P3 todo as MOOT — the launcher no longer exists) and
      `/codex/05-infrastructure/vm-tarball-deployment.md` (dropped its stale Pattern-B-exception table row) — all
      adjacent stale references to the deleted launcher, found while verifying scope. `deployment-service`'s
      `quality-gates.sh` green (224s, `.qg_last_passed_sha=557247c`); all 3 commits verified reachable on
      `origin/live-defi-rollout` via `git merge-base --is-ancestor`. Repo-wide grep for both launcher filenames in
      `deployment-service` now returns zero hits; the `scripts/vm/launch-ec2-vm.sh` AWS-side
      `_register     "gcs-migration-bundle"` entry was investigated and deliberately left alone — it is a separate AWS
      EC2 task-name→instance-profile registry with no test coupling to either deleted GCP launcher's filename, so
      removing it was out of this todo's verified scope (not proven dead).
- [x] ✅ [INFRA] P2.2e. **DONE 2026-08-04 (operator-forced cutover; slot-13 infra closeout).** The operator forced the
      live-traffic cutover on 2026-08-04 under time pressure (pipeline stuck ~4 days on the cold-start bug). Production
      `uts-shared-deployment-api` is NOW confirmed on `uts-prd-sa` (revision `00430-dcr`, 16Gi/4cpu, image
      `sha256:e805764...`), verified via multiple live 200s across `/api/health`,
      `/api/data-status/distinct-values/sports`, `/api/data-status/distinct-values/defi` — see
      `issues/deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md` Progress Log
      2026-08-04 entry for full evidence. The SIGABRT root cause (`deployment_api_sigabrt_crash_loop_2026_07_24.md`)
      remains open and the cold-start `exit(0)` bug still reproduces on automatic deploys, but a reliable workaround
      exists: manual `gcloud run services update-traffic --to-revisions=...=100` retry after the automatic deploy
      silently no-ops. The cold-start doc's P3 todo is now also closed (same session). **Retagged `[INFRA][OPERATOR]` →
      `[INFRA]`** — operator action completed; SIGABRT root cause tracked separately.
- [x] ✅ [TEST] P2.3. **DONE 2026-08-02 (slot-4, infra) — live-verified, `deployment-service@4b86feb`/`b85aa53`
      (authored + shipped by an earlier session; this pass live-verified + closed it out).**
      `tests/integration/test_bucket_iam_tier_isolation.py` already existed (docstring corrects the plan's original
      `ENVIRONMENT=staging`-vs-`*-prod-*` wording to the REAL tier pair — `-test-`/`-prd-` — since dev/stg were
      permanently retired 2026-07-13; `uts-test-sa` is the ratified non-prod-tier subject). Uses
      `Bucket.test_iam_permissions()` (no real writes) via impersonation of each tier SA from the ambient identity.
      **Live-ran it this session**
      (`RUN_INTEGRATION=true GCP_PROJECT_ID=central-element-323112 pytest     tests/integration/test_bucket_iam_tier_isolation.py -v`):
      all 5 tests initially SKIPPED (ambient `unified-trading-sa` lacked `roles/iam.serviceAccountTokenCreator` on the 3
      target SAs) — self-granted that role narrowly on `uts-prd-sa`/`uts-test-sa`/`uts-migration-sa` per the
      self-service ambient-identity rule (same pattern as the P2.2c/coldstart-doc precedent), re-ran after IAM
      propagation (~30s), **all 5 PASSED**, then **revoked the 3 grants immediately after** (verified removed via
      `get-iam-policy`) — no standing credential left behind. Confirmed LIVE: `uts-prd-sa` can write `-prd-`/denied
      `-test-`; `uts-test-sa` can write `-test-`/denied `-prd-` (this is the actual IAM-level cross-tier-write-403 proof
      P2.3 asks for); `uts-migration-sa` still denied `-prd-` write (honest current-state assertion — P2.2f's
      write-grant is still open, tracked separately, not a test bug). **"Add as a deployment-service QG check" — scoped,
      not blanket-wired**: `RUN_INTEGRATION` stays `false` (this repo's existing default, predating this plan) rather
      than flipping it globally — `RUN_INTEGRATION=true` would ALSO activate the pre-existing
      `tests/integration/test_gcp_services.py`, which constructs `google.cloud.logging.Client()` uncaught (no
      `DefaultCredentialsError` guard), and this repo's `quality-gates-v2.yml` CI has no GCP-credential step anywhere in
      the pipeline — flipping the flag would 500 every future CI run for the whole repo, not just skip. That gap
      predates this plan and isn't scoped to P2.3; filed as its own new todo below (P2.3b) rather than silently
      absorbing or blindly flipping it. This test IS the deployment-service "QG check" in the sense this repo already
      uses for every credentialed integration test (the `RUN_INTEGRATION=true` + `tests/integration/` convention,
      identical to `test_gcp_services.py`'s own established pattern) — it runs on-demand via the documented command in
      its own docstring, self-skips safely without the impersonation grant, and asserts real IAM state when run with it.
      (repo: deployment-service)
- [x] ✅ [INFRA] P2.3b. **DONE 2026-08-02 (slot-9) — `deployment-service@4b776f0`.** Implemented option (b) exactly as
      scoped (option (a) — provisioning real CI GCP credentials — stays untouched, a separate operator-judgment call,
      not attempted here): added a shared `_gcp_client(factory)` helper to `tests/integration/test_gcp_services.py` that
      catches `google.auth.exceptions.DefaultCredentialsError` around every GCP client-construction call site (Cloud
      Logging ×4, Compute Engine ×4, Cloud Build ×3, Cloud Run Jobs/Executions ×6, Artifact Registry
      `google.auth.default()` ×2 — 19 sites total across the file) and `pytest.skip()`s with the exact
      `"No GCP credentials — skipping integration test: …"` phrasing `base-service.sh`'s STEP-5 credential-skip QG check
      (`BAD_AUTH_SKIP` regex) already allowlists — mirrors `test_bucket_iam_tier_isolation.py`'s existing
      skip-on-credential-gap convention. `RUN_INTEGRATION` is left `false` (unchanged) — this todo only makes flipping
      it locally/interactively safe, per its own scoping; the CI-credential decision (option a) is not this todo's to
      make. Live-verified: `bash scripts/quality-gates.sh` green (3018 passed, 5 skipped, "No credential-file skip
      patterns in tests" ✅) on the committed HEAD; SHA confirmed on `origin/live-defi-rollout` via
      `git merge-base --is-ancestor`. **Note for a future pass on option (a)**: `tests/conftest.py`'s existing autouse
      `_skip_integration_without_creds` fixture (shipped 2026-07-13, `deployment-service@cad9416`, predates this
      finding) already unconditionally skips every `@pytest.mark.integration` test whenever pytest-socket's
      `--allow-hosts` is set — which `quality-gates.sh`'s TESTS phase always passes — so in practice CI already never
      reaches this file's client-construction code today even with `RUN_INTEGRATION=true`; this todo's fix is
      independent defense-in-depth (the direct, non-quality-gates.sh `pytest tests/integration/…` invocation path, and
      any future change to that conftest fixture) rather than evidence the CI-breakage risk was empirically reproduced
      this pass.

### Phase 3 — Codex alignment

- [x] ✅ [DOCS] P3.1. Update [bucket-isolation-model.md §8](/codex/05-infrastructure/bucket-isolation-model.md) from
      "designed" to "enforced", documenting the SA names + the migration-SA exception. Update CLAUDE.md one-liner. —
      unified-trading-pm@495c66ec1

## Success criteria

- IAM (not code) denies a dev/staging credential a prod-bucket write (negative test passes).
- Live/batch prod + dev workloads unaffected (read-anything preserved; tier writes preserved).
- Migration SA is the single sanctioned cross-tier writer; no remaining project-wide `objectAdmin`.
- Codex §8 reflects enforced reality.

## Progress Log

- **2026-08-03 (interactive session)**: operator asked to apply P2.2f's recommended (b) grant for the 3 launchers.
  Confirmed `launch-gcs-migration-bundle-vm.sh`'s pattern was already usable, but the other 2 needed real research, not
  a lookup — found `launch-legacy-bucket-migration-sharded.sh`'s script is missing entirely (likely a completed,
  deletable one-off) and `launch-bucket-rsync-vm.sh` is generically parameterized across multiple bucket families (no
  single prefix to condition on). Did NOT apply a guessed/overly-broad IAM grant given this is a live GCP security
  change — filed P2.2g above instead of forcing it through. Separately, ruled
  `unified_trading_sa_live_iam_drift_vs_ terraform_2026_07_31.md`'s P1 (keep both self-escalation-capable roles for now,
  insufficient evidence to safely revoke either) and dispatched its P2 (terraform-import all 24 as-is) via the live
  blocked-queue.
- **context-scout 2026-08-01**: populated/refreshed context_scope (6 entries).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — swapped the tier_sa_scope_gap issue (its P2
  already flipped) for the `bucket_iam_per_tier_sa.tf` source path (the terraform declaring the actual SAs).
- **slot-6 2026-08-02**: dispatched task `bucket_iam_write_protection_per_tier-018` (P2.2e, the
  `uts-shared- deployment-api` live-traffic cutover). Did NOT proceed — confirmed both gating docs are still
  `status: open` and the explicit downstream gate from `deployment_api_sigabrt_crash_loop_2026_07_24.md`'s
  `2026-08-01T00:06Z (main-orchestrator agt-26fe12)` entry is still in force verbatim: "any live-traffic cutover to a
  fresh revision (e.g. `bucket_iam_write_protection_per_tier-018` P2.2e) MUST NOT proceed on a 'resolved' reading of
  this doc — the cold-start path is demonstrably still flaky; hold 100% traffic on the warm instance until finding-6's
  durable-close bar is met." Checked the companion tracker
  (`deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md`) — no `durable-close` language
  present, i.e. the raised bar (N-consecutive fresh cold-starts over a multi-hour window spanning quiet periods, zero
  `exit(0)` failures) has not been met. Also confirmed the related `BLK-a14e9de5` (Google Cloud Support case question on
  `deployment_api_sigabrt_crash_loop-028`) is still unanswered. This is a live-production service traffic cutover
  explicitly gated by main-orchestrator's own instruction — not proceeding without that gate clearing is not optional
  caution, it's compliance with a standing directive. No action taken; releasing via `/skip-current-task`.
- **slot-12 2026-08-02**: dispatched task `bucket_iam_write_protection_per_tier-023` (P2.2d2c2, the 3
  migration-SA-blocked launchers). Independently re-verified P2.2f's gate before touching code: live GCP
  `get-iam-policy` confirms `uts-migration-sa` still holds only `roles/storage.objectViewer` (zero write grant),
  matching terraform source — the gate is genuinely still unmet, not just stale-looking. Wiring the 3 launchers now
  would either 403 (migration SA) or silently mismatch (tier SA's `startsWith` condition doesn't cover their legacy flat
  bucket names). Retagged P2.2d2c2 `[OPERATOR]` (mirrors this plan's own P2.1b precedent — same-plan todos can't express
  a structured prereq, so the backlog regenerator will keep re-offering this to workers otherwise). No code changed;
  releasing via `/skip-current-task`.
- **slot-7 2026-08-02T18:55Z**: dispatched task `bucket_iam_write_protection_per_tier-018` (P2.2e, the
  `uts-shared-deployment-api` live-traffic cutover) — the same task slot-6 declined earlier today. Between slot-6's
  decline and this dispatch, slot-5 actually PERFORMED the gate test the companion tracker's own P3 recommends (tag
  - curl-verify a fresh `uts-prd-sa`+`16Gi/4cpu` cold start) at **2026-08-02T18:12Z** — only 43 minutes before this
    dispatch — and it **failed on the first attempt** (`update-traffic --set-tags` on `00417-7fh`, identical
    `Container called exit(0)`/STARTUP-TCP-probe-failed signature), despite `revisions list` + a log sweep showing an
    apparent 38.5h clean streak beforehand — full detail in
    `deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md`'s own Progress Log. That is the
    most recent, most rigorous (an actual live cold-start attempt, not just a log-sweep) evidence available, and it
    directly re-confirms the durable-close bar (N-consecutive fresh cold-starts over a multi-hour window, zero `exit(0)`
    failures) is still unmet — main-orchestrator's standing hold-until-durable-close directive
    (`deployment_api_sigabrt_crash_loop_2026_07_24.md`, `2026-08-01T00:06Z`) still applies verbatim. Re-attempting the
    same cold-start test myself 43 minutes later would not add information and risks compounding the investigation-churn
    hypothesis multiple sessions have flagged as a possible contributor. Not proceeding; no code shipped; releasing via
    `/skip-current-task`.
- **slot-11 2026-08-02**: dispatched task `bucket_iam_write_protection_per_tier-018` (P2.2e) a 3rd time in one day.
  Re-verified both gating docs (`deployment_api_sigabrt_crash_loop_2026_07_24.md`,
  `deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md`) are still `status: open`, no new
  evidence since slot-5's 18:12Z live cold-start failure. Rather than re-attempt the identical test a 4th time, retagged
  P2.2e `[OPERATOR]` (same fix pattern as P2.2d2c2 above) so the backlog stops re-offering a task no worker can
  currently clear. No code changed; releasing via `/skip-current-task`.
- **slot-9 2026-08-02**: dispatched task `bucket_iam_write_protection_per_tier-024` (P2.3b). Implemented option (b) from
  the todo's own text — see P2.3b's checkbox above for the full evidence trail (`deployment-service@4b776f0`,
  quality-gates.sh green, SHA verified on origin). Left `RUN_INTEGRATION` and the CI-credential decision (option a)
  untouched, as scoped.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **context-scout 2026-08-07**: refreshed context_scope (6 entries) — dropped
  `deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md` (dangling: archived since the
  last scout pass, its P2.2e gate is now DONE per P2.1b's 2026-08-06 operator approval, so it's resolved history, not a
  live blocker); added `deployment-service/terraform/gcp/main.tf` (the actual `unified_trading_storage_admin`
  god-SA-grant resource at `main.tf:598`, P2.1b's real removal target — `bucket_iam_per_tier_sa.tf` alone only covers
  the replacement per-tier bindings, not the grant being removed). Locked doc (`locked_by: live-defi-rollout`) — per
  `plans/PLAN_FORMAT.md` a lock blocks archival only, not this additive frontmatter edit.
- **slot-4 2026-08-08**: dispatched task `bucket_iam_write_protection_per_tier-009` (P2.1b). Verified both hard gates:
  P2.2e DONE 2026-08-04 (deployment-api live on `uts-prd-sa`, multi-endpoint 200s), P2.3 PASSED 2026-08-02 (all 5
  assertions). Updated `test_bucket_iam_tier_isolation.py` migration SA assertion False→True (P2.2f DONE 2026-08-03:
  `uts-migration-sa` now holds `roles/storage.objectAdmin` project-wide unconditioned). Self-granted
  `roles/iam.serviceAccountTokenCreator` on 3 SAs for P2.3 re-run; polled for propagation; all 5 PASSED post-removal;
  immediately revoked all 3 grants (confirmed removed).
  `tofu apply -target=google_project_iam_member.unified_trading_storage_admin` (ENV=prod, `tofu init` required first due
  to provider v7.37.0 upgrade) — 1 destroyed, 0 added. Live `get-iam-policy` confirms `unified-trading-sa` no longer
  holds `roles/storage.objectAdmin`; however `roles/storage.admin` (broader) is still present as undeclared drift — out
  of P2.1b scope, tracked in `issues/unified_trading_sa_live_iam_drift_vs_terraform_2026_07_31.md`. Shipped
  `deployment-service@f514b6a0` (`terraform/gcp/main.tf` god-SA block removed +
  `tests/integration/test_bucket_iam_tier_isolation.py` assertion flipped) via quality-gates.sh green + quickmerge.
- **plan_reconciler 2026-08-10 (cross-cutting tranche, dispatch `agt-33a6ec`)**: closed P1.3 as MOOT/superseded by P2.3
  (see the flipped checkbox above for the evidence chain — both halves of the argument, dev/stg's permanent retirement
  and P2.3's equivalent test on the real tier pair, are already recorded in this same doc). **This was the LAST open
  todo — the doc is now 100% `[x]` done.** Not archiving: `locked_by: live-defi-rollout` blocks archival without an
  explicit `[unlock-plan]` grant (HARD RULE) — flagging as an archive-ready-once-unlocked candidate in this run's
  findings doc instead. The gated finalize plan
  (`bucket_iam_write_protection_per_tier_2026_06_09_finalize_2026_07_27.md`, `depends_on`+`gate_on_depends: true`) can
  now dispatch once someone flips it `active` — its own gate condition (source plan fully done) is met.
