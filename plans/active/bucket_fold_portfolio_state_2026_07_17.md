---
doc_type: plan
title: Bucket fold — portfolio-state 6 stores → 1 (portfolio-state-{env}-{pid}) — LAST
summary:
  "Executes Fold E of the Wave-3 fold design — the LAST fold, live-trading-adjacent. Collapses six position/pnl/risk
  stores (positions-store, pnl-attribution-store, risk-metrics-store, pnl-attribution-output, archetype-state,
  position-store-sports) into ONE portfolio-state-{env}-{pid} with per-domain path prefixes. Heterogeneous sources with
  THREE drivers: the UTL PATH_REGISTRY flat trio (positions/pnl-attribution/risk-metrics) gains its -{env}- tier for the
  FIRST time here; pnl-attribution-output is a bare default not in yaml OR registry; archetype-state +
  position-store-sports are already env-tiered (name+prefix move only). The named writer services
  (risk-and-exposure/pnl-attribution/ position-balance-monitor) DO NOT exist as repos — the real writers reach these via
  UTL DataSetSpec, consumed by strategy-service pnl/position modules; redeploy THOSE. Because a wrong-path write or
  premature source delete is a live-trading data-integrity hazard, the reader cutover + source delete are OPERATOR-GATED
  (design §5 Q2 [WORKER REC]). HUMAN plan — do NOT rush; diff real position/pnl/risk output end-to-end before deleting
  anything."
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, meta]
repos: [unified-trading-library, strategy-service, deployment-service, unified-api-contracts]
scope: [engineer, admin]
tags:
  [
    gcs,
    buckets,
    consolidation,
    fold,
    portfolio-state,
    positions,
    pnl,
    risk,
    migration,
    env-split,
    lifecycle,
    infrastructure,
  ]
related:
  [
    plans/archive/2026_07/bucket_estate_fold_design_2026_07_13.md,
    plans/active/bucket_estate_consolidation_to_sub100_2026_07_13.md,
    plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
    plans/active/bucket_fold_closeout_2026_07_17.md,
    /codex/05-infrastructure/bucket-isolation-model.md,
    /codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
    /codex/02-data/pipeline-mode-partition.md,
  ]
created: "2026-07-17"
last_updated: "2026-07-17"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: infra
drift_direction: advance-code
depends_on: [bucket_estate_fold_design_2026_07_13]
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "Successor execution plan of bucket_estate_fold_design_2026_07_13 §3 todo 1. Operator ruling 2026-07-17: all 5 folds
  as HUMAN plans. This is Fold E (portfolio-state — LAST per the design's risk order, live-trading-adjacent,
  operator-gated reader-cutover + delete)."
context_scope:
  [
    /codex/05-infrastructure/bucket-isolation-model.md,
    /plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
    unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py,
  ]
---

# Bucket fold — portfolio-state 6 stores → 1 (`portfolio-state-{env}-{pid}`) — LAST

> **🔴 LIVE-TRADING-ADJACENT — execute LAST, after the other four folds.** Touches live position/pnl/risk snapshots. A
> wrong-path write or premature source delete is a data-integrity hazard. The reader cutover + source delete are
> OPERATOR-GATED (design §5 Q2). Cross-plan banner on [[bucket_estate_consolidation_to_sub100_2026_07_13]] W3 +
> [[bucket_estate_fold_design_2026_07_13]] Fold E.

**What / why**: Fold E of [[bucket_estate_fold_design_2026_07_13]] — 6 stores → 1 `portfolio-state-{env}-{pid}` with
per-domain path prefixes:
`portfolio-state-{env}-{pid}/{positions,pnl-attribution,risk-metrics,pnl-attribution-output,archetype-state,position-sports}/…`.

**Heterogeneous sources — three drivers (SSOT = design §1 Fold E)**:

| Source bucket (prd)      | Driver / SSOT                                                             | Tiered today? | Target prefix                 |
| ------------------------ | ------------------------------------------------------------------------- | ------------- | ----------------------------- |
| `positions-store`        | UTL PATH_REGISTRY `registry.py` (`positions-store-{project_id}`, no-AG)   | NO (flat)     | `.../positions/`              |
| `pnl-attribution-store`  | UTL PATH_REGISTRY `registry.py`                                           | NO (flat)     | `.../pnl-attribution/`        |
| `risk-metrics-store`     | UTL PATH_REGISTRY `registry.py`                                           | NO (flat)     | `.../risk-metrics/`           |
| `pnl-attribution-output` | bare default `strategy-service/.../pnl/config.py` (NOT in yaml/registry)  | NO            | `.../pnl-attribution-output/` |
| `archetype-state`        | `cloud-providers.yaml` (`archetype-state-${DEPLOYMENT_ENV_SHORT}-${pid}`) | **YES**       | `.../archetype-state/`        |
| `position-store-sports`  | `cloud-providers.yaml` + `venue_balance_tracker.py`                       | **YES**       | `.../position-sports/`        |

> The PATH_REGISTRY flat trio gains its `-{env}-` tier for the FIRST time in this fold — the SSOT is the UTL
> `DataSetSpec.bucket_template`, not yaml. `archetype-state` + `position-store-sports` already carry `-{env}-`
> (name+prefix move only). **The yaml-named writer services `risk-and-exposure-service` / `pnl-attribution-service` /
> `position-balance-monitor-service` DO NOT exist as repos** — the real writers reach these via UTL `DataSetSpec`,
> consumed by strategy-service's pnl/position modules. Redeploy strategy-service, NOT phantom services.

## Codex SSOTs (read before touching — plan↔codex drift is review-blocking)

- `/codex/05-infrastructure/bucket-isolation-model.md` — Group B naming → folded portfolio-state shape (closeout).
- `/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` — pnl-attribution semantics (do not corrupt on
  migrate).
- `/codex/02-data/pipeline-mode-partition.md` — reader-fallback discipline; `_KIND_ALIASES` soft-window.
- Design cross-cutting: [[bucket_estate_fold_design_2026_07_13]] §2.A/C/D/E.

## Todos — DeFi-playbook order, but delete + reader-cutover OPERATOR-GATED

- [x] ✅ [DATA] P2. **Provision + yaml/registry scaffold** — **DONE 2026-07-18/19** (flipped 2026-07-31 corpus-sweep
      against this doc's own Progress Log + the `[x]` Cutover item below; the 2026-07-17 operator-ownership hold on
      bucket-fold checkboxes is RESCINDED for hard-evidenced items, and the 2026-07-30 na-eligibility-audit had already
      flagged this exact todo as reading STALE). **Provisioned** (2026-07-18, direct gcloud,
      ASIA-NORTHEAST1/UBLA/STANDARD→COLDLINE@60d): `portfolio-state-{prd,test}-central-element-323112`. **yaml key
      folded across all 3 copies**: PM mirrors `unified-trading-pm@a1c500097` (_"fix(config): fold portfolio-state key
      into PM cloud-providers.yaml mirrors (Fold-E, unblock UTL CI)"_ — folded FIRST, applying the C+D PM-yaml-in-CI
      lesson), plus the UAC yaml and deployment-service yaml landed in the same Cutover wave. **PATH_REGISTRY
      `DataSetSpec` tier + `_KIND_ALIASES`**: UTL repointed `positions`/`pnl_attribution`/`risk_metrics` →
      `portfolio-state-prd` with the literal domain prefix and `_KIND_ALIASES` for all 6 retired kinds. **UTL CI GREEN**
      (recorded on the Cutover item). **GCP leg only** — the AWS leg + the `terraform plan` creates-only drift assert
      this todo also asked for are NOT done, and (checked 2026-07-31) were NOT in fact covered by the IAM-and-lifecycle
      or Alias-sunset todos below; they are now split out as their own open todo. The GCP TF reconcile that DID happen
      (`import` of `portfolio-state-{prd,test}` + source `state rm`) is recorded on the Delete-sources item.
- [x] ✅ [DATA] P2. **Parity migrate** — **DONE 2026-07-19.** Only 1 real object existed (pnl-attribution-store, an
      ARBITRAGE_PRICE_DISPERSION funding-rate parquet) → server-side copied to `portfolio-state-prd/pnl-attribution/`,
      parity verified. positions-store(0)/archetype-state-{prd,test}(0)/position-store-sports-{prd,test}(0)
      asserted-empty; risk-metrics-store + pnl-attribution-output ABSENT. No real portfolio state written (test/dev,
      nothing traded).
- [x] ✅ [CODE] P2. **Cutover** — **DONE 2026-07-19 (operator full-send, test data).** Driven via IMPLEMENT→adversarial-
      verify workflow (woq29kqa8, GO all 5 repos). LANDED: PM yaml mirrors@a1c500097 (folded FIRST — the C+D
      PM-yaml-in-CI lesson), UAC yaml, UTL@(registry positions/pnl_attribution/risk_metrics → portfolio-state-prd +
      literal domain prefix + \_KIND_ALIASES 6 retired kinds), strategy-service (pnl/config resolved_output_bucket + 4
      pnl writers + venue_balance_tracker position-sports/ prefix), deployment-service yaml. UTL CI GREEN. X-repo loose
      end: execution-service `tenderly_budget.py` writes archetype-state at bucket root (internally symmetric, empty
      bucket → no data loss) — **CLOSEOUT PREFIX FIX DONE 2026-07-19: execution-service@9a1f4f1d** (added
      `_BUDGET_DOMAIN_PREFIX="archetype-state"` → blob path now
      `archetype-state/tenderly_budget/{archetype}/day=….json`; docstring updated to the folded portfolio-state bucket;
      6 unit tests green, QG green; LDR→staging via Tier-C drain).
- [x] ✅ [INFRA] P2. **Redeploy/consolidator** — **N/A / DONE 2026-07-19.** No redeploy (nothing writing
      portfolio-state, test/dev). No portfolio-state consolidator exists (plan-noted — the flat trio never had one);
      skipped.
- [x] ✅ [INFRA] P2. **Delete sources + TF-reconcile** — **DONE 2026-07-19 (operator pre-authorized autonomous delete;
      test data, not live).** DELETED the 6 source buckets (positions-store, pnl-attribution-store, archetype-state-
      {prd,test}, position-store-sports-{prd,test}). TF: imported portfolio-state-{prd,test}; state-rm'd the 4
      TF-tracked sources (positions/pnl-attribution not TF-managed). yaml keys folded
      (archetype-state/position-store-sports kept for soft-window → closeout). This was the LAST destructive step of
      Wave-3 — ALL 5 FOLDS NOW COMPLETE.
- [ ] [INFRA] P2. **AWS leg + `terraform plan` drift assert** — the residual of the (now `[x]`) Provision todo, split
      out 2026-07-31 (corpus-sweep) after confirming no other open todo here covered it. Provision folded
      `portfolio-state-{prd,test}` on **AWS** via the derived-from-yaml `for_each`, then run `terraform plan` and assert
      the only creates are the new folded buckets. (GCP provisioning + GCP TF import/state-rm are already done — see the
      Provision and Delete-sources items.)
- [ ] [INFRA] P2. **IAM + lifecycle** — join `portfolio-state-prd` to
      [[bucket_iam_write_protection_per_tier_2026_06_09]] Phase-2 Group-B; `-test-` twin gets test-tier. Retention
      CONFIRMED by operator 2026-08-08 — ship the default STANDARD→COLDLINE@60d as-is, no longer-than-60d exception
      needed for live-trading snapshots.
- [ ] [CODE] P3. **Alias sunset** — after the fallback window closes + retired kinds grep-clean, hard-remove
      `_KIND_ALIASES` entries + retired yaml keys; `terraform plan` green. (May defer to closeout.)

## Progress Log

- **2026-07-17, authored** as the portfolio-state successor of [[bucket_estate_fold_design_2026_07_13]] §3 todo 1.
  Live-trading-adjacent — reader cutover + delete operator-gated, retention confirm required before COLDLINE. Object
  counts NOT re-measured this session — executor re-measures per domain. Nothing executed yet.
- **2026-07-18, `/autonomous` — PROVISION only (additive/safe; the sensitive live migration + cutover DEFERRED to the
  careful gated pass per this plan's operator-gated design).** Provisioned the folded target
  `portfolio-state-{prd,test}-central-element-323112` (direct gcloud, ASIA-NORTHEAST1/UBLA/STANDARD→COLDLINE@60d). NOTE
  the design flags **retention-confirm-before-COLDLINE** for live-trading snapshots — the 60d lifecycle is applied as
  the canonical default but the operator must confirm live position/pnl/risk retention doesn't need STANDARD longer than
  60d (if so, adjust before it bites). **Sources measured:** `positions-store` (flat), `pnl-attribution-store` (flat),
  `pnl-attribution-output` (bare, no-pid), `archetype-state-{prd,test}` (env-tiered), `position-store-sports-{prd,test}`
  (env-tiered); **`risk-metrics-store` NOT present** on GCP (likely empty / PATH_REGISTRY-`DataSetSpec`-only — assert at
  migration). **DEFERRED (this is the LAST + most sensitive fold — do NOT rush):** the 6-source migration + the
  OPERATOR-GATED reader cutover (UTL PATH_REGISTRY flat trio gains its `-{env}-` tier here for the first time +
  `pnl/config.py` bare default + the 2 yaml kinds → `portfolio-state` + per-domain prefixes) + redeploy + end-to-end
  verify (diff real position/pnl/risk vs pre-migration) + the operator-gated delete. Follows the Fold-A discovery→
  implement→adversarially-verify shape; strategy-service pnl/position modules are the real writers (the yaml-named
  risk-and-exposure/pnl-attribution/position-balance-monitor services do NOT exist as repos — redeploy
  strategy-service).

- **na-eligibility-audit 2026-08-02** (re-confirms 2026-07-30; re-read after intervening edits, verdict unchanged):
  KEEP-NA, valid — operator ruling 2026-07-17 (HUMAN plans); the IAM+lifecycle todo explicitly needs operator
  confirmation on live-trading retention before COLDLINE. NOTE the 'Provision + yaml/registry scaffold' todo reads STALE
  against the 2026-07-18/19 Progress Log (targets provisioned; yaml/registry/\_KIND_ALIASES landed with the `[x]`
  cutover).
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — swapped in registry.py + strategy-service
  pnl/config.py source paths (the real driver files) for bucket_iam_write_protection + pipeline-mode-partition.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — reaffirms 2026-08-02 (unchanged): governed by the 2026-07-17
  operator ruling (HUMAN plans); live-trading-adjacent, IAM+lifecycle item still needs operator retention confirmation.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — reaffirms 2026-08-06 (unchanged, 3 open todos): 2026-07-17
  operator ruling (HUMAN plans, this is the LAST/live-trading-adjacent fold) governs the AWS-leg/alias-sunset residuals;
  IAM+lifecycle remains OPERATOR_QUESTION-gated (explicit "CONFIRM retention before COLDLINE... do not blanket-apply
  without operator confirmation").
- **operator ruling 2026-08-08** (NA-corpus blocker digest, cross-cutting round 5, id=45): 60 days is fine — ship the
  default STANDARD→COLDLINE@60d for `portfolio-state-prd` live-trading snapshots, no exception needed. IAM+lifecycle
  todo updated to drop the retention-confirm gate; still open pending the actual IAM-join + lifecycle-policy execution.

- **context-scout 2026-08-15**: refreshed context_scope (3 entries, trimmed from 5) — cutover/parity-migrate/redeploy
  are all DONE; remaining opens are the AWS-leg provision, the IAM+lifecycle Group-B join, and alias sunset, so swapped
  the (now-closed) registry.py/pnl-config.py cutover source paths for the Phase-2 Group-B IAM plan this fold joins +
  `bucket_naming.py` (the alias-sunset target).
