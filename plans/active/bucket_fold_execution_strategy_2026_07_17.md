---
doc_type: plan
title: Bucket fold — execution-store 4+pred → 1 & strategy-store flat → tiered
summary:
  "Executes Folds C + D of the Wave-3 fold design in ONE plan (same services, same cutover window). Fold C collapses the
  per-AG execution-store buckets (cefi/defi/tradfi/sports + the execution-store-prediction kind) into a single
  execution-store-{env}-{pid} with the asset-group axis moved into the path (incl. the nautilus-catalog-cache/ prefix
  that shares the per-AG bucket today) — cefi is the heavy one (~6142 objects:
  fills/configs/deployment_history/spreads). Fold D is name-tier-only: strategy-store is ALREADY unified-flat, so this
  fold just adds its -{env}- tier — and it DEPENDS_ON the parent plan's Wave-2 strategy_store_split_brain repoint
  (per-AG readers → flat kind) landing FIRST. DeFi playbook per fold: provision + soft _KIND_ALIASES → dual-verify
  parity → atomic cutover → redeploy + verify-exercised → delete sources + TF/yaml. HUMAN plan — execution-store cefi
  holds live fills, so the delete step is operator-gated."
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, meta]
repos:
  [
    execution-service,
    strategy-service,
    unified-trading-library,
    deployment-api,
    unified-trading-system-ui,
    unified-api-contracts,
    deployment-service,
  ]
scope: [engineer, admin]
tags:
  [gcs, buckets, consolidation, fold, execution-store, strategy-store, migration, env-split, lifecycle, infrastructure]
related:
  [
    plans/active/bucket_estate_fold_design_2026_07_13.md,
    plans/active/bucket_estate_consolidation_to_sub100_2026_07_13.md,
    plans/active/issues/strategy_store_split_brain_2026_07_13.md,
    plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
    plans/active/bucket_fold_closeout_2026_07_17.md,
    codex/05-infrastructure/bucket-isolation-model.md,
    codex/05-infrastructure/manifest-consolidator-ssot.md,
    codex/02-data/pipeline-mode-partition.md,
  ]
created: "2026-07-17"
last_updated: "2026-07-17"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: infra
drift_direction: advance-code
depends_on: [bucket_estate_fold_design_2026_07_13, strategy_store_split_brain_2026_07_13]
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "Successor execution plan of bucket_estate_fold_design_2026_07_13 §3 todo 1. Operator ruling 2026-07-17: all 5 folds
  as HUMAN plans. This bundles Folds C (execution-store) + D (strategy-store) — same services, one cutover window
  (design §3 groups them)."
---

# Bucket fold — execution-store 4+pred → 1 & strategy-store flat → tiered

> **🟡 MIGRATION IN FLIGHT (started 2026-07-17).** Provisions `execution-store-{prd,test}-{pid}` + re-tiers
> `strategy-store` → `strategy-store-{env}-{pid}`; deletes the per-AG execution-store buckets (cefi holds LIVE fills —
> delete is operator-gated). Cross-plan banner on [[bucket_estate_consolidation_to_sub100_2026_07_13]] W3 +
> [[bucket_estate_fold_design_2026_07_13]] Folds C/D.

**What / why**: Folds C + D of [[bucket_estate_fold_design_2026_07_13]], bundled because they touch the same services
(execution-service + strategy-service) in one cutover window.

- **Fold C — execution-store**: `execution-store-{cefi,defi,tradfi,sports}` + the `execution-store-prediction` kind →
  one `execution-store-{env}-{pid}`, AG moves into the path:
  `execution-store-{env}-{pid}/{cefi,defi,tradfi,sports,pred}/execution/by_date/…`, and the `nautilus-catalog-cache/`
  prefix folds in too. cefi ≈ 6142 objects (fills/configs/deployment_history/spreads); the rest sparse — re-measure at
  execution.
- **Fold D — strategy-store**: ALREADY unified-flat (operator decision 2026-05-20); this fold ONLY adds the `-{env}-`
  tier. **DEPENDS_ON** the parent plan's Wave-2 [[strategy_store_split_brain_2026_07_13]] repoint (per-AG readers → flat
  `kind="strategy-store"`) landing FIRST — this fold is the "gains its tier in the same move" follow-on.

**Cutover sites (SSOT = design §1 Folds C & D, file:line there).** Fold C: execution-service `service_config.py`
(`kind="execution-store-prediction"`); UTL PATH_REGISTRY `execution_fills` and `nautilus_catalog`
(`bucket_template="execution-store-{category}-{project_id}"`); `deployment-api_config.py`, `routes/services.py`,
`routes/service_status_execution.py`. Fold D: strategy-service writers (`gcs_storage_service.py`,
`venue_balance_tracker.py`, `hedge_ratio_writer.py`, `decision_context_writer.py`, `pnl/adapters/domain_adapter.py` —
already resolve flat `kind="strategy-store"`, only re-tier); readers fixed by W2 but re-tiered here:
`deployment-api_config.py`, `routes/services.py`, the UI hardcoded `strategy-store-cefi-…` in
`app/api/catalogue/envelope/route.ts` + `catalogue/instrument/route.ts`, the three UAC `enumerate_*.py` scripts, and the
UAC facade `canonical/gcs_paths.py::strategy_store_bucket` (must return the flat tiered name).

## Codex SSOTs (read before touching — plan↔codex drift is review-blocking)

- `codex/05-infrastructure/bucket-isolation-model.md` — Group B naming → folded execution/strategy shapes (closeout).
- `codex/05-infrastructure/manifest-consolidator-ssot.md` — execution consolidator 5 → 1.
- `codex/02-data/pipeline-mode-partition.md` — reader-fallback discipline; `_KIND_ALIASES` soft-window.
- Design cross-cutting: [[bucket_estate_fold_design_2026_07_13]] §2.A/C/D/E.

## Todos — DeFi-playbook order (Fold C + Fold D interleaved by phase)

- [ ] [DATA] P1. **Provision + yaml scaffold** — add folded `execution-store` key + `${DEPLOYMENT_ENV_SHORT}-` to the
      existing `strategy-store` flat key in `cloud-providers.yaml` (all 3 copies); add `_KIND_ALIASES` mapping the 4
      per-AG execution kinds + `execution-store-prediction` → `execution-store` (§2.D). Provision
      `execution-store-{prd,test}` on GCP + AWS via derived-from-yaml `for_each`. Verify `terraform plan` shows only the
      new folded buckets as creates. UTL QG green.
- [ ] [CODE] P1. **GATE — confirm W2 strategy_store_split_brain repoint landed** — Fold D cutover cannot ship until the
      parent plan's Wave-2 [[strategy_store_split_brain_2026_07_13]] per-AG→flat reader repoint is done. Verify (grep
      the readers resolve flat `kind="strategy-store"`, not per-AG). If not landed, this plan BLOCKS here — do NOT
      re-tier over a split-brain reader set.
- [ ] [DATA] P1. **Parity migrate** — server-side copy `execution-store-{ag}/*` →
      `execution-store-{env}-{pid}/{ag}/execution/…` (incl. `nautilus-catalog-cache/`) and the prediction kind →
      `.../pred/…`; byte-count parity per AG (cefi ≈ 6142 obj — re-measure). strategy-store is a name re-tier, not a
      data move — copy the flat bucket contents to the tiered name, parity-verify.
- [ ] [CODE] P1. **Atomic cutover** — repoint Fold C sites → `kind="execution-store"` + `{ag}/` path prefix, and Fold D
      sites → the re-tiered flat `strategy-store` name (incl. the UAC `strategy_store_bucket` facade + the two UI
      hardcoded routes). Ship per-repo QG-green: execution-service, strategy-service, UTL, deployment-api, UI, UAC.
- [ ] [INFRA] P1. **Redeploy + verify-exercised** — redeploy execution-service + strategy-service; verify a live fill
      write lands under `execution-store/{ag}/…` and the UI catalogue routes resolve the re-tiered strategy-store (diff
      real output). Cite `Evidence: cloudbuild=<id>` SUCCESS. Retarget the execution consolidator job(s) 5→1.
- [ ] [INFRA] P1. **Delete sources + TF/yaml removal (SAME change) — OPERATOR-GATED for execution-store-cefi** — after
      verify-exercised + a passive read-audit window, delete the per-AG execution-store buckets + retire the split-brain
      per-AG strategy-store readers' buckets, remove TF/yaml keys same change. **`execution-store-cefi` holds live fills
      — its delete needs operator sign-off** (design §5 Q2 flags Fold C delete as a candidate human gate); do not delete
      cefi autonomously.
- [ ] [INFRA] P2. **IAM + lifecycle** — join `execution-store-prd` + `strategy-store-prd` to
      [[bucket_iam_write_protection_per_tier_2026_06_09]] Phase-2 Group-B; `-test-` twins get test-tier.
      STANDARD→COLDLINE@60d whole-bucket, with a prefix-scoped STANDARD exception for `strategy-store/catalogue/`
      (UI-served daily).
- [ ] [CODE] P3. **Alias sunset** — after the fallback window closes + retired kinds grep-clean, hard-remove
      `_KIND_ALIASES` entries + retired yaml keys; `terraform plan` green. (May defer to closeout.)

## Progress Log

- **2026-07-17, authored** as the execution+strategy successor of [[bucket_estate_fold_design_2026_07_13]] §3 todo 1.
  Object counts NOT re-measured this session — executor re-measures per AG at provision time. Fold D gated on the parent
  W2 split-brain repoint (todo 2). Nothing executed yet.
