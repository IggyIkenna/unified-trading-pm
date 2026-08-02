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
    /plans/active/issues/bucket_iam_per_tier_dev_stg_retired_ssot_contradiction_2026_07_27.md,
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
    /plans/active/issues/bucket_iam_per_tier_dev_stg_retired_ssot_contradiction_2026_07_27.md,
    /plans/active/issues/bucket_iam_p2_god_sa_removal_before_runtime_rewire_2026_07_30.md,
    /plans/active/issues/bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md,
    /plans/active/issues/deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md,
    /plans/active/issues/unified_trading_sa_live_iam_drift_vs_terraform_2026_07_31.md,
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
- [ ] [TERRAFORM] P1.3. Verify dev/stg workloads read everything, write their own tier, and are **IAM-denied** a `-prd-`
      write (negative test). No prod write-grant removal until P2.

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
- [ ] [TERRAFORM][OPERATOR] P2.1b. **Remove the god-SA `objectAdmin`** (`unified_trading_storage_admin` in
      `main.tf:598-602`); verify live/batch prod workloads retain `-prd-` write (now via `uts-prd-sa`, not the god-SA);
      verify a dev/stg credential is **denied** a `-prd-` write (IAM-level, not just name-resolver). **HARD-GATED on
      P2.2e AND P2.2d (below) both completing + being live-verified first** — do not remove the god-SA grant while any
      runtime still authenticates as `unified-trading-sa` OR the GCP default compute SA for writes. **P2.2c alone
      (2026-07-31) is NOT sufficient for this gate** — it wires the identity into `deploy-shared.sh` and live-verifies
      `uts-prd-sa`'s grants, but deployment-api's actual LIVE runtime is still `unified-trading-sa` (traffic cutover
      split out as the new P2.2e, currently blocked on a cold-start reliability issue) — do not misread P2.2c's ✅ as
      satisfying this gate. **Group B buckets join here only after the consolidation plan's Wave-3 folds provision their
      `-{env}-` form (re-gated 2026-07-13; env-split plan archived).** **`[OPERATOR]`-tagged 2026-07-30 (slot-13)**:
      this checkbox has no structured `depends_on`/`gate_on_depends` link to P2.2 (same-plan todos can't express a
      per-todo prereq — CLAUDE.md), so the backlog regenerator has auto-dispatched this fleet-wide-blast-radius IAM
      removal to a worker TWICE in one day despite the HARD-GATED note above (slot-11 earlier today, slot-13 this pass)
      — both independently declined per `issues/bucket_iam_p2_god_sa_removal_before_runtime_rewire_2026_07_30.md`.
      `[OPERATOR]` routes this to the operator's blocked-queue instead of re-offering it to workers who can only
      re-derive the same "not yet" verdict. **Retag back to plain `[TERRAFORM]`** once P2.2e and P2.2d are both done +
      live-verified (every write-path runtime confirmed running as its tier SA, not `unified-trading-sa` or the default
      compute SA) — do not leave this tag stale per CLAUDE.md's retag-on-resolve rule.

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

- [x] ✅ [OPERATOR] P2.2a. **RESOLVED 2026-07-31** — operator ruling on BLK-0c84ceac: **"C: hybrid" — per-tier SAs
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
      `deployment-service@8a8125e`/`c518cda` + `118ad9e`.** Wired `deploy-shared.sh`'s default `--service-account` for
      `uts-shared-deployment-api`/deployment-api from `unified-trading-sa` to `uts-prd-sa` (env-overridable via
      `RUNTIME_SA=` for an instant revert), and live-verified access: Secret Manager `versions.access`, Pub/Sub
      `topics.list`, BigQuery `datasets.list`, Storage `objects.list` (Group A `-prd-`) all confirmed working directly
      via an impersonated `uts-prd-sa` token. Concurrently, slot-7 found + fixed 2 grant gaps this check didn't cover
      (`roles/bigquery.jobUser`, bucket-level write on `unified-deployment-state-*`/`deployment-scripts-*`),
      live-verified via real endpoints — see
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
      cross-bucket, flat→tiered — same migration-SA-blocked class as the 2 migration launchers, folded into P2.2d2c
      below) + 6 confirmed OUT OF SCOPE via the authoritative registry (`deployment_service/vm_prefix_registry.py`
      `VM_PREFIX_TO_BUCKET`, all map to `bucket=None`): `launch-dashboard-vm.sh`, `launch-disaster-drill-cron-vm.sh`,
      `launch-dr-drill-cutover-vm.sh`, `launch-sports-scheduler-vm.sh`, `launch-vm-zombie-watchdog.sh` (control-plane /
      heartbeat-only, confirms the plan's own "not a data writer" suspicion for each) +
      `launch-features-onchain-backfill-vm.sh` (resolved above, pure delegator). The 17 execution/strategy/ml-service +
      9 AWS launchers remain correctly out of scope (unchanged from P2.2d2a's disposition — per-service SA /
      different-cloud, not this helper). Evidence: `bash -n` + shellcheck clean on all 10 touched files;
      `quality-gates.sh` green; CI verified.
- [ ] [TERRAFORM][OPERATOR] P2.2f. **NEW finding, opened 2026-08-01 (slot-7) during P2.2d2b.** `uts-migration-sa` — this
      plan's own § Open design decisions designates it "the sanctioned cross-tier writer" for migration scripts —
      currently holds ONLY `roles/storage.objectViewer` project-wide (`bucket_iam_per_tier_sa.tf`'s
      `uts_migration_objectviewer` resource); it has ZERO write grant (no `objectAdmin`, conditioned or otherwise).
      Confirmed by reading the terraform source (not yet re-confirmed against live GCP — do that before granting). It
      cannot actually write anything, contradicting its stated purpose and blocking every launcher that needs it
      (`launch-legacy-bucket-migration-sharded.sh`, `launch-gcs-migration-bundle-vm.sh`, `launch-bucket-rsync-vm.sh` —
      see P2.2d2c below). **`[OPERATOR]`**: the exact grant scope is a judgment call, not mechanically determinable —
      options are (a) an unconditioned project-wide `storage.objectAdmin` (simplest, but re-creates a mini god-SA for
      exactly these 3 migration-purpose launchers), (b) a CEL condition scoped to the specific legacy bucket name
      patterns these 3 launchers actually touch (`market-data-tick-{ag}-{project}` flat legacy shape confirmed for
      `launch-gcs-migration-bundle-vm.sh`; the other 2 need their own enumeration), or (c) extend
      `lc_tier_service_account` with a migration mode AND scope the grant narrowly to match. Recommend (b) — mirrors
      this plan's own least-privilege design intent for the tier SAs. Once ruled + granted, live-verify via a real write
      (not just `get-iam-policy`) before unblocking P2.2d2c.
- [ ] [CODE] P2.2d2c. **NEW, split from P2.2d2b 2026-08-01 (slot-7).** Wire the 3 launchers blocked on the migration-SA
      write-grant gap (P2.2f above): `launch-legacy-bucket-migration-sharded.sh`, `launch-gcs-migration-bundle-vm.sh`,
      `launch-bucket-rsync-vm.sh` — all three read/write a LEGACY (non-env-tiered, flat) bucket name that no tier SA's
      `startsWith` IAM condition matches. Gated on P2.2f (still open — `[OPERATOR]` grant not yet made); **remaining
      scope is now JUST these 3**. **DONE 2026-08-02 (slot-13) — `deployment-service@24e0878`, the 2 independently-
      investigable launchers**: `launch-canonical-migration-vm.sh` — confirmed via
      `terraform/gcp/bucket_iam_per_tier_sa.tf` +
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
      shellcheck clean; `quality-gates.sh` green; CI verified. Gated on P2.2a (met) + P2.2d1 (met) + P2.2d2a (met) +
      P2.2d2b (met, this split).
- [ ] [INFRA] P2.2e. **NEW, opened 2026-07-31 (slot-5).** Cut `uts-shared-deployment-api`'s live traffic
      (`spec.traffic`) over to a `uts-prd-sa` revision (P2.2c wired the identity + resource sizing; this is the separate
      step of actually promoting it). **Currently BLOCKED**: every fresh cold-start of a new/tagged revision fails
      reproducibly (`Container called exit(0)` + STARTUP-TCP-probe-failed, ~30-32s in — independent of SA and of the
      `16Gi/4cpu` resource fix, both confirmed via direct testing), a failure signature that looks like the same
      mechanism as the open `issues/deployment_api_sigabrt_crash_loop_2026_07_24.md` investigation. Once that
      investigation (or this specific cold-start angle) resolves: tag + curl-verify a fresh instance 3-5× for
      confidence, then cut `spec.traffic` over (or ramp via the existing tagged-canary pattern — see
      `e8ce86a-verify`/`00389-d9d`). Full writeup:
      `issues/deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md`. Gated on P2.2c
      (met) + the cold-start blocker resolving.
- [ ] [TEST] P2.3. Negative tests: `ENVIRONMENT=staging` write to a `*-prod-*` bucket → `403` at IAM; migration SA →
      allowed. Add as a deployment-service QG check.

### Phase 3 — Codex alignment

- [ ] [DOCS] P3.1. Update [bucket-isolation-model.md §8](/codex/05-infrastructure/bucket-isolation-model.md) from
      "designed" to "enforced", documenting the SA names + the migration-SA exception. Update CLAUDE.md one-liner.

## Success criteria

- IAM (not code) denies a dev/staging credential a prod-bucket write (negative test passes).
- Live/batch prod + dev workloads unaffected (read-anything preserved; tier writes preserved).
- Migration SA is the single sanctioned cross-tier writer; no remaining project-wide `objectAdmin`.
- Codex §8 reflects enforced reality.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (6 entries).
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
