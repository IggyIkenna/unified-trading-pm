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
    plans/active/bucket_estate_fold_design_2026_07_13.md,
    plans/active/bucket_estate_consolidation_to_sub100_2026_07_13.md,
    plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
    plans/active/bucket_fold_closeout_2026_07_17.md,
    codex/05-infrastructure/bucket-isolation-model.md,
    codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
    codex/02-data/pipeline-mode-partition.md,
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

- `codex/05-infrastructure/bucket-isolation-model.md` — Group B naming → folded portfolio-state shape (closeout).
- `codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` — pnl-attribution semantics (do not corrupt on
  migrate).
- `codex/02-data/pipeline-mode-partition.md` — reader-fallback discipline; `_KIND_ALIASES` soft-window.
- Design cross-cutting: [[bucket_estate_fold_design_2026_07_13]] §2.A/C/D/E.

## Todos — DeFi-playbook order, but delete + reader-cutover OPERATOR-GATED

- [ ] [DATA] P2. **Provision + yaml/registry scaffold** — add the folded `portfolio-state` key to `cloud-providers.yaml`
      (all 3 copies), env-tiered; the PATH_REGISTRY flat trio needs its tier expressed via the UTL `DataSetSpec`
      `bucket_template` (their SSOT — not yaml). Add `_KIND_ALIASES` mapping the retired kinds → `portfolio-state`
      (§2.D). Provision `portfolio-state-{prd,test}` on GCP + AWS. Verify `terraform plan` shows only the new folded
      buckets as creates. UTL QG green.
- [ ] [DATA] P2. **Parity migrate all 6 sources** — server-side copy each source → its per-domain prefix under
      `portfolio-state-{env}-{pid}/`; byte-count parity per domain. Re-measure object counts at execution (design counts
      are 2026-07-13). Assert-empty + skip any 0-object source, recording the assertion.
- [ ] [CODE] P2. **Cutover — OPERATOR-GATED** — repoint UTL PATH_REGISTRY (`registry.py` positions/pnl-attribution/
      risk-metrics rows) + the `pnl-attribution-output` bare default (`pnl/config.py`) + the two yaml kinds
      (archetype-state, position-store-sports) → `kind="portfolio-state"` + per-domain prefixes. Ship per-repo QG-green:
      UTL, strategy-service, deployment-service, UAC. **Reader cutover requires operator sign-off** — this changes where
      live position/pnl/risk state is read from.
- [ ] [INFRA] P2. **Redeploy + verify-exercised END-TO-END (do NOT rush)** — redeploy the real writers (strategy-service
      pnl + position modules); verify a live position/pnl/risk snapshot lands under the correct
      `portfolio-state/{domain}/` prefix AND is read back correctly — diff real output against the pre-migration source,
      not just "deployed". Cite `Evidence: cloudbuild=<id>` SUCCESS. Retarget the portfolio-state consolidator 6→1.
- [ ] [INFRA] P2. **Delete sources + TF/yaml removal (SAME change) — OPERATOR-GATED, LAST OF ALL FOLDS** — only after
      verify-exercised + a passive read-audit window + operator sign-off, delete the 6 source buckets (GCP + AWS) and
      remove their TF/yaml keys same change; `terraform plan` green. This is the final destructive step of the entire
      Wave-3 fold — nothing is more live-trading-sensitive.
- [ ] [INFRA] P2. **IAM + lifecycle** — join `portfolio-state-prd` to
      [[bucket_iam_write_protection_per_tier_2026_06_09]] Phase-2 Group-B; `-test-` twin gets test-tier. **CONFIRM
      retention before COLDLINE** — live-trading snapshots may need STANDARD longer than 60d (design §2.E flags
      portfolio-state as a confirm-before-COLDLINE case); do not blanket-apply the 60d rule without operator
      confirmation.
- [ ] [CODE] P3. **Alias sunset** — after the fallback window closes + retired kinds grep-clean, hard-remove
      `_KIND_ALIASES` entries + retired yaml keys; `terraform plan` green. (May defer to closeout.)

## Progress Log

- **2026-07-17, authored** as the portfolio-state successor of [[bucket_estate_fold_design_2026_07_13]] §3 todo 1.
  Live-trading-adjacent — reader cutover + delete operator-gated, retention confirm required before COLDLINE. Object
  counts NOT re-measured this session — executor re-measures per domain. Nothing executed yet.
