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
    plans/active/bucket_estate_consolidation_to_sub100_2026_07_13.md,
  ]
created: 2026-06-09
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
last_updated: 2026-06-27
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
  > remains unchecked → Group A IAM (Phase 1/2) remains blocked. Re-verify after G4 applies complete. **[2026-07-14
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

- [ ] [TERRAFORM] P1.1. Define per-tier SAs (`uts-dev-sa`, `uts-stg-sa`, `uts-prd-sa`) + a dedicated **migration SA**
      (`uts-migration-sa`, cross-tier write — the sanctioned exception, used only by
      `*_service/scripts/migration_*.py`).
- [ ] [TERRAFORM] P1.2. Replace the project-wide `roles/storage.objectAdmin` with **per-suffix bindings**: dev SA →
      `objectAdmin` on `*-dev-*`; stg SA → `*-stg-*`; prd SA → `*-prd-*`; all SAs + CI/CD + developer identities →
      `objectViewer` broadly (read-anything) but **read-only on `*-prd-*`**. Apply to **Group A buckets first** (they
      carry the suffix today).
- [ ] [TERRAFORM] P1.3. Verify dev/stg workloads read everything, write their own tier, and are **IAM-denied** a `-prd-`
      write (negative test). No prod write-grant removal until P2.

### Phase 2 — Prod cutover + wiring

- [ ] [TERRAFORM] P2.1. Apply `-prd-` write-scope; remove the god-SA `objectAdmin`. Verify live/batch prod workloads
      retain `-prd-` write; verify a dev/stg credential is **denied** a `-prd-` write (IAM-level, not just
      name-resolver). **Group B buckets join here only after the consolidation plan's Wave-3 folds provision their
      `-{env}-` form (re-gated 2026-07-13; env-split plan archived).**
- [ ] [CODE] P2.2. Wire each runtime to its tier SA (deployment-service launchers / Cloud Run service identities);
      migration scripts opt into `uts-migration-sa` explicitly.
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
