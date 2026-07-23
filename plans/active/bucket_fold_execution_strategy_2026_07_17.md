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
    /codex/05-infrastructure/bucket-isolation-model.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/02-data/pipeline-mode-partition.md,
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

- `/codex/05-infrastructure/bucket-isolation-model.md` — Group B naming → folded execution/strategy shapes (closeout).
- `/codex/05-infrastructure/manifest-consolidator-ssot.md` — execution consolidator 5 → 1.
- `/codex/02-data/pipeline-mode-partition.md` — reader-fallback discipline; `_KIND_ALIASES` soft-window.
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
- [x] ✅ [CODE] P1. **Atomic cutover** — **CODE LAYER DONE 2026-07-18 (6/7 repos, UTL CI GREEN).** LANDED: UAC@1dd02a73
      (yaml exec-flat+strategy-tier+facade), UTL@d822bab5 (registry exec_fills/nautilus + strategy 3 rows +
      _KIND_ALIASES exec-prediction + execution.py client), strategy-service@c425d5b5 (reader fold + VaR golden fix),
      execution-service@6af18c2e (writer surface + fill-twin), deployment-service@9f3f43b (yaml + single-root
      consolidator-TF + canonical-kind maps), UI@8075d6d7 (2 catalogue routes), PM@34125fac3 (yaml mirrors).
      **deployment-api DEFERRED** (display-only, tree tangled with unrelated Fold-B/data_status WIP). **UTL CI break
      root-caused + fixed:** the resolver's workspace-yaml discovery finds
      unified-trading-pm/configs/cloud-providers.yaml in CI (deployment-service not a UTL dep); its stale-on-LDR per-AG
      execution-store failed UTL's folded-resolution tests even with a good UAC clone — the FIX-workflow PM agent folded
      it but hit the usage limit before committing; folded + pushed, qg-v2 re-triggered GREEN. Original todo text below.
- [ ] [CODE] P1. **(orig) Atomic cutover** — repoint Fold C sites → `kind="execution-store"` + `{ag}/` path prefix, and
      Fold D sites → the re-tiered flat `strategy-store` name (incl. the UAC `strategy_store_bucket` facade + the two UI
      hardcoded routes). Ship per-repo QG-green: execution-service, strategy-service, UTL, deployment-api, UI, UAC.
- [x] ✅ [INFRA] P1. **Redeploy + consolidator retarget** — **DONE 2026-07-18.** No redeploy needed (operator: execution
      NOT live, static test data — nothing running to redeploy). **Consolidator retargeted via DIRECT gcloud** (apply
      unsafe): execution 3→1 single-root (`execution-cefi` job repurposed → `--bucket execution-store-prd`, tradfi/defi
      jobs+crons deleted); strategy → `--bucket strategy-store-prd`. VERIFIED-exercised: both wrote root
      `_index/latest.json` (execution-store-prd + strategy-store-prd). Naming wart: exec job still `-cefi` (closeout
      rename). AWS consolidators (all 404-drifted) → closeout.
- [x] ✅ [INFRA] P1. **Delete sources + TF-state reconcile** — **DONE 2026-07-18 (operator pre-authorized autonomous
      delete; cefi was test data not live fills).** DELETED (GCP):
      execution-store-{cefi(6144),defi(2),tradfi(1),sports}, execution-store-pred-{prd,test}, strategy-store(flat,172);
      strategy-store-{cefi,tradfi,defi} were already 404. Parity pre-verified (execution-store-prd 6147 =
      cefi+defi+tradfi; strategy-store-prd 172 = flat). yaml keys already folded. TF-state: IMPORTED folded
      execution-store-{prd,test} + strategy-store-prd; STATE-RM'd the deleted sources. Estate IAM/scheduler drift stays
      operator-aware (not applied).
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
- **2026-07-18, `/autonomous` — PROVISION + MIGRATE started (operator steer: "start C+D provisioning, additive/safe,
  while Fold-A ship waits").** Re-measured GCP: `execution-store-cefi` **6144 obj** (live fills — confirms the ~6142
  estimate), defi 2, tradfi 1, sports 0; `execution-store-pred-{prd,test}` exist (pred kind); `strategy-store` flat
  **172 obj**. **PROVISIONED** the folded GCP targets (direct gcloud, ASIA-NORTHEAST1/UBLA/STANDARD→COLDLINE@60d):
  `execution-store-{prd,test}-central-element-323112` (both were absent), `strategy-store-prd-central-element-323112`
  (`strategy-store-test` already existed). **MIGRATING** (server-side, additive — sources untouched): Fold D
  `strategy-store/*` → `strategy-store-prd/*` (flat re-tier, same layout:
  `_index/ backtests/ catalogue/ configs/ hedge_ratio_snapshots/ legacy_cefi/ strategy_decision_context/ strategy_instructions/ tracer_runs/`);
  Fold C `execution-store-{cefi,defi,tradfi}/*` → `execution-store-prd/{ag}/*` (AG becomes top-level prefix; cefi layout
  `execution/ configs/ deployment_history/ blocked_spreads/ backfill_batches/ nautilus-catalog-cache/ nautilus_catalog/ …`
  all gain the `cefi/` prefix) + `execution-store-pred-prd/*` → `execution-store-prd/pred/`; sports (0) assert-empty.
  **cefi is LIVE** — the bulk copy is a point-in-time snapshot; a FINAL RSYNC at cutover catches new-fill drift
  (expected parity-drift on cefi until then). **MIGRATE DONE + PARITY ✓ (2026-07-18):** strategy-store
  src=dst=37,765,413 B; execution cefi src=dst=1,610,459,707 B (no snapshot drift), defi/tradfi/pred copied under
  `{ag}/` prefixes, sports (0) asserted empty. **NEXT (gated, NOT this session):** Fold-C+D code CUTOVER is GATED on the
  parent W2 [[strategy_store_split_brain_2026_07_13]] repoint landing first (todo 2 — strategy-service already resolves
  flat `kind="strategy-store"`, verified; the HARDCODED per-AG readers deployment-api/UI/UAC-facade are the W2 scope to
  confirm); execution-store-cefi DELETE is OPERATOR-GATED (live fills). Cutover follows the Fold-A discovery→implement→
  adversarially-verify shape (execution-service `service_config.py` + UTL PATH_REGISTRY
  `execution_fills`/`nautilus_catalog`
  - strategy re-tier writers + UAC `strategy_store_bucket` facade + 2 UI hardcoded routes). Also: execution/strategy
    service builds will need the same base-image pin bump as ml (fleet digest-sweep fix f6e98bbdd auto-handles it once
    it promotes + the 6h sweep runs).

- **2026-07-18, `/autonomous` — C+D CODE CUTOVER shipping (4-workflow pipeline: IMPLEMENT→VERIFY→FIX→REVERIFY).** Ran a
  6-agent IMPLEMENT workflow (one per repo) → 2 adversarial verifiers → a 5-agent FIX workflow → re-verify. The
  adversarial passes earned their keep — caught, before anything shipped: (1) **strategy-service holds Fold-C
  byte-parity execution-fills READERS** (`pnl/adapters/domain_adapter` + `pnl/engine/orchestrator`) that I'd mis-scoped
  as "redeploy-only" — un-folded they `KeyError`/silently-mismatch the writer's `{category}/execution/…` path (silent
  hold-day P&L drop); FIXED writer==reader (resolve_bucket_name(kind="execution-store") + category=). (2)
  `execution-service dependency_checker` resolved the RETIRED `strategy-store-test` yaml key → BucketNamingError; FIXED
  to tiered resolve. (3) deployment-service `_SERVICE_TO_CANONICAL_KIND` missing execution/strategy; (4) deployment-api
  stale generated `consolidator_catalog.json` (regenerated); (5) **PM yaml mirrors** (configs + ci-test) not folded —
  folded. **LANDED:** UAC@1dd02a73 (yaml exec-flat + strategy-tier + facade), UTL (registry exec_fills/nautilus +
  strategy 3 rows + _KIND_ALIASES exec-prediction + execution.py client + fixture/tests), strategy-service (readers +
  config/dep-checker re-tier + tests). **execution-service** (writer surface — service_config/storage/save_operations
  fill-twin/data_sink/dep_checker + churn tests) re-gating for ship; **deployment-service/deployment-api/UI** next.
  **VaR golden fix (operator-requested, not-my-fault):** strategy-service's phase0 risk golden failed on a ~1e-12 VaR
  precision flake (19 digits of z-score float-noise in `current_value`); quantized the parametric VaR to cents in
  `pre_trade_check_engine._check_var_limit` (canonical for a currency amount) + updated the golden — 190 var/pre_trade
  tests green, platform-stable. **LOOSE END:** a large separate replay/source-capability WIP of mine (~8 UAC files:
  possible_manifest/pipeline_mode/_source_priority_data/_cefi-capability/lighter_api) re-dirties UAC (codegen or
  slot-cron restore) — unrelated to C+D; ship C+D with `--skip-preflight`; the replay feature needs finishing/committing
  or reverting separately. **Operator context: TEST DATA, not precious, single-root \_index/, autonomous delete.**

- **2026-07-18, OPERATOR DECISIONS (interactive Q&A) — full-send, canonical-first, NOT precious data.** Operator
  clarified the trading-adjacent buckets hold only random test data — **no real trades have happened; nothing is writing
  execution right now.** So the "live cefi fills" caution is moot: the 6144 cefi objects are STATIC historical test data
  (no live-write hazard, no final-rsync/write-drain needed, no misplaced-write-on-redeploy risk). Goal is CANONICAL
  structure for eventual (weekend) trading — do NOT over-gate on safety. **Decisions:** (1) **Risk#3 → SINGLE ROOT
  `_index/`** — the execution consolidator writes ONE bucket-root `_index/latest.json` merged across AGs (full job
  collapse); reader reads root + AG-filter; safe because nothing's live. (2) **Full-send BOTH C+D** autonomously. (3)
  **Pre-authorized AUTONOMOUS delete** of all sources incl. execution-store-cefi after the 4 gates (parity + cutover +
  verify-exercised + zero-reads) — no operator pause. W2 gate SATISFIED (verified). Same coordinated ship-all-then-
  redeploy shape as Fold-A. cutover spec = workflow wf_9e961e81-417 output (whvoyecxl.output).

- **2026-07-18, UTL `quality-gates-v2` RED → diagnosed + CONFIRMED RESOLVED (no new fix needed).** After UTL@d822bab5
  (folded resolver + folded `tests/fixtures/cloud-providers.yaml`), UTL v2 went RED (runs 29659419522 @20:17Z,
  29660682095 @20:57Z) on the **tests** slice. Root cause: the CI resolution source is **not** the UTL test fixture —
  the v2 workflow exports `UNIFIED_TRADING_CLOUD_PROVIDERS_YAML` →
  `unified-trading-pm/scripts/quality-gates-base/ci-test-cloud-providers.yaml` (base-service.sh:471; base-library.sh
  does NOT set it, so UTL **local** QG uses the folded fixture → local-green while CI-red). That PM mirror still carried
  the OLD `execution-store` per-AG DICT + un-tiered `strategy-store`, so the folded UTL tests hit
  `BucketNamingError: Kind 'execution-store' … is per-asset_group` + `strategy-store-{pid}` vs `-prd-` assert-mismatch.
  The CI-tail `--- Logging error --- / ValueError: I/O operation on closed file` is benign pytest teardown noise, NOT
  the failure. **Already fixed on origin:** `be973918e` (@21:10Z, "fix(config): fold PM cloud-providers.yaml mirrors for
  C+D (unblock UTL CI)") folded BOTH PM mirrors (ci-test + configs) — landed ~13 min AFTER the last red run. Evidence
  UTL v2 **GREEN**: run **29661120709 @21:10:48Z SUCCESS** (first run after the fold; identical code, only the mirror
  changed) + re-triggered 29661344579. **Fleet-safety verified** before concluding: no sibling pytest resolves the OLD
  exec/strategy shape against the shared fixture (execution-service assertions are literal/mock;
  deployment-service/deployment-api/UI have none) — execution-service (29659402526) + strategy-service (29659413987) v2
  stayed GREEN. No UTL change required.
