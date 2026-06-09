---
title:
  "Audit-criteria automation — convert recurring agentic audits into QG steps (code) + a scheduled data-state audit
  (GCS), all asset groups"
created: 2026-06-08
parent_epic: epics/manifest_master.md
assigned_vm: vm-cross-cutting
status: active
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
locked_by: live-defi-rollout
locked_since: 2026-06-08
source:
  - operator 2026-06-08 ("do all audit criteria have tests so QG catches issues vs constant agentic audits? — automate
    it across all AGs")
  - canonical_form_cross_service_audit_checklist.md (CF-1…CF-14)
  - master_data_canonicalisation_migration_catalogue_2026_06_07.md (the ①–⑫ pre-apply audit)
---

# Audit-criteria automation — kill the recurring agentic-audit dependence

> **Goal (operator 2026-06-08): every audit criterion is enforced automatically — a QG step (code, commit-time) or a
> scheduled data-state job (GCS, alert-on-drift) — so the agentic audit becomes a rare new-finding triage, not a
> chore.** Three tiers (see the coverage map below). Tier-1 is largely done; Tiers 2 + 3 are the work.

## Coverage map — what's automated TODAY vs the gaps (all AGs; QG runs per-repo → all-AG by construction)

| Tier                             | Criterion class                                                                                                                                                                                       | Today                                                                                                       | Gap                                                 |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| **1 — code LOGIC**               | validity-matrix / bundle-grain / C-#6 cross-check / Era-B enum round-trip                                                                                                                             | ✅ unit tests (QG test phase) — agents pinned them (`df15dba2`, C-#6, enum⟺capability)                      | keep adding a test per new contract                 |
| **1 — code PATTERN (existing)**  | bucket SSOT (5.69) · pipeline*mode-explicit (5.70) · cluster (5.64) · per-VM (5.66) · IS→MTDS (`no_hardcoded_venue*\*`/`no_silent_absence`) · swallow/CF-11 · adapter-contract ratchet                | ✅ QG STEPS, all repos/AGs                                                                                  | —                                                   |
| **2 — code PATTERN (NEW model)** | coarse `pipeline_mode="batch"` creep · exact-coarse reader probe · Era-A `data_type=options_chain` WRITE · validity/impossible-cell                                                                   | ❌ **agentic grep only**                                                                                    | **add QG steps** (greppable → static gates)         |
| **3 — DATA-STATE (GCS)**         | CF-1 v9-in-rows · CF-4 source-in-rows · CF-13 source-aware FORM on disk · CF-14 catalogue ⊇ present-set · CF-6 expected_unattempted · CF-10 phantom · Era-B on-disk byte-probe · 4-state distribution | ⚠️ **`cf_manifest_audit` is MANUAL, per-bucket, CF-1…CF-9/12 only — missing the new model + not scheduled** | **extend + cross-AG-loop + schedule with alerting** |

## `cf_manifest_audit_2026_06_01.py` audit (2026-06-08) — the Tier-3 foundation, partial

- **Cross-asset**: AG-AGNOSTIC (point at any bucket) but NOT a single all-AG run — needs a per-AG loop wrapper.
- **Covers** (GCS data-state of one `_index`): CF-1/2/3(populated)/4/5/7/8/9/12 + shallow object-path probe.
- **MISSING**: CF-13 (source-aware FORM — it checks pipeline*mode *populated*, not
  `batch*<source>`), CF-14 (catalogue ⊇ present-set), Era-B (`options_chain`/`futures_chain`= instrument_type +`data_type=trades`, 0 `data_type=options_chain`),
  CF-6 (expected_unattempted materialised), CF-10 (phantom). **new-model hits = 0.**
- **Codebase-blind** by design (data-state only) — the code-pattern checks are Tier-2 QG steps, NOT this script.

## Phase 1 — Tier-2 QG steps (code patterns; cheap, high-leverage; catch the exact regressions we just fixed)

- [x] ✅ [SCRIPT] P1. **QG step: no coarse `pipeline_mode = "batch"` stamp** — **unified-trading-pm@b4245a7dd**
      `check_canonical_model_regressions.py` (STEP 5.93) `coarse-pipeline-mode` pattern (AST Assign/AnnAssign/kwarg =
      `"batch"`/`"live"`; blank `""` deliberately NOT flagged — it is the canonical v9 sentinel, covered by UTL
      auto-derive + STEP 5.70). 0 new fleet-wide. Catches the `DEFAULT_PIPELINE_MODE="batch"` class.
- [x] ✅ [SCRIPT] P1. **QG step: no exact-coarse reader probe** — same checker, `exact-coarse-reader` pattern (string
      literal `pipeline_mode=batch/`/`=live/`; docstrings excluded). 0 new fleet-wide (the C-PATH READ fix holds).
- [x] ✅ [SCRIPT] P1. **QG step: no Era-A `data_type=options_chain`/`futures_chain` WRITE** — same checker,
      `era-a-chain-write` pattern (UAC registry/declaration trees excluded; 3 legacy write sites baselined →
      per-AG-migrator-owned Era-B relabel). The `_LEGAL_DATA_TYPES` raise stays the runtime guard.
- [x] ✅ [SCRIPT] P2. **QG step: validity-matrix completeness** — **unified-api-contracts@d087a468**:
      `tests/test_validity_matrix_completeness.py` (27 tests / 4 classes) asserts every `(instrument_type, data_type)`
      in `SOURCE_PRIORITY`/the matrix is valid or explicitly excluded, no impossible pair enumerable, Era-B chain
      bundles = trades-only, and **no silent all-data_types fallback** (unknown instrument_type → None, leaf bundles →
      empty frozenset). QG exit 0. **Surfaced REAL GAPS (pinned in the test exclusion list, not weakened) — see finding
      below.**
- [x] ✅ [FINDING] P2. **Validity-matrix / SOURCE_PRIORITY orphans RESOLVED into a typed closed-set** —
      **unified-api-contracts@fec77f5d**: the ad-hoc exclusion list became `_SOURCE_PRIORITY_EXCLUSION_REASONS` (every
      orphan → one of 7 closed-set reason constants) + a new `test_every_exclusion_has_typed_reason` (no anonymous skip
      possible; 28 tests green). Per-orphan decisions (evidence-based, conservative — wiring a capability with no real
      producer would re-seed false `expected_unattempted`, so genuine gaps stay NAMED, not guessed). **Operator-directed
      follow-through 2026-06-09 (unified-api-contracts@f5e6b0c2 + @fec77f5d):** (1) `(cefi, ohlcv_15m)` → **RETIRED**
      (operator confirmed cefi has no 15m candles — removed from SOURCE_PRIORITY + AVAILABILITY_AT_SEMANTICS); (2) the
      Era-A name-collision was a checker bug — `data_type=options_chain` is a LEGIT Era-B SNAPSHOT data_type, so STEP
      5.93's `era-a-chain-write` pattern was REMOVED (pm@361e548e1) and `(cefi/tradfi, options_chain/futures_chain)` →
      **`PENDING_SNAPSHOT_SLICE`** (the snapshot slice slot-3 widens), not legacy-retained; (3) **9 of 11 DeFi data_types
      WIRED** into PROTOCOL_CAPABILITIES from `defi_venue_capabilities.py` producer evidence (+18 protocols, 37→55) —
      `native_staking_rates`/`vault_share_price` honestly stay `BLOCKED_UPSTREAM_CAPABILITY` (no producer in venue_caps);
      (4) 11 sports → `REFERENCE_NOT_INSTRUMENT_GRAIN`. Plus `COMPUTED_SERVICE_OUTPUT`/`CEFI_LEGACY_KEY`/
      `REFERENCE_AG_NO_MATRIX`. Matrix complete-or-typed-excluded; 28 tests green. **→ slot-2 re-verify enumerate before
      G4** (the DeFi could-exist universe grew — B0-PRE todo in `defi_manifest_canonicalisation_2026_06_01.md`).
- [x] ✅ [SCRIPT] P1. **QG step: no pre-aggregated open-edge bar ingestion** — **unified-trading-pm@b4245a7dd**
      `check_bar_edge_open_ingestion.py` (STEP 5.92); built as a dedicated AST checker (not folded into
      check_mdps_bar_boundary) — see `bar_edge_left_vs_right_remediation_2026_06_08.md` Phase 0. 2 latent sites
      baselined; planted-regression proven.
- [x] ✅ [SCRIPT] P2. Wired both into `base-service.sh` + `base-library.sh` (STEP 5.92/5.93) — **@b4245a7dd**. Service
      repos SOURCE base-service.sh from the workspace PM checkout (no per-repo copy → no template rollout needed; gate
      activates fleet-wide the instant PM lands on the CI-cloned ref). Pre-existing hits baselined (ratchet); verified
      green on 5 representative consumer repos per-scope (mtds/IS/UTL/UAC/deployment-api).

## Phase 2 — Tier-3 data-state audit: extend + cross-AG + schedule (the continuous-verification cron)

- [x] ✅ [CODE] P1. **`cf_manifest_audit` extended to CF-1…CF-14 + Era-B** — **unified-trading-pm@2fe982eb1**: `audit()`
      now returns a structured per-CF results dict + JSON-able; added CF-13 (pipeline_mode SOURCE-AWARE prefix form
      `batch_*`/`live_*`/`replay_*`, not just populated), Era-B (`data_type in {options_chain,futures_chain}` count == 0),
      CF-6 (4-state/expected_unattempted vocabulary present + canonical), and CF-10 + CF-14 as honest SKIP-with-reason
      (CF-10 → reconcile_phantom_manifest_rows_all.py; CF-14 → catalogue artifact when materialised, else SKIP since the
      G1 build_instrument_catalogue roll-up is pending). per-CF GREEN/RED with evidence; ruff-clean.
- [x] ✅ [CODE] P1. **Cross-AG wrapper** — **unified-trading-pm@2fe982eb1** `cf_manifest_audit_all.py`: one invocation
      runs all 5 AGs × {market-data-tick, instruments-store} = 10 buckets, per-AG GREEN/RED rollup + a machine-readable
      JSON summary, exits non-zero on any RED (the `cf-manifest-audit-all --all-ags --json-out` cron entrypoint).
- [x] ✅ [INFRA] P1. **Scheduled** — **deployment-service@eaff3a7**: `terraform/gcp/cf_manifest_audit_scheduler.tf`
      (Cloud Run Job `uts-prod-cf-manifest-audit` + Scheduler `0 6 * * *` UTC, after the consolidator; GCS output bucket
      90-day lifecycle; `google_monitoring_alert_policy` log-based **alert-on-RED** = severity=ERROR for the job) +
      `terraform/aws/cf_manifest_audit_scheduler.tf` (Batch-Fargate + EventBridge `cron(0 6 * * ? *)` + `FailedJobCount
      >= 1` CloudWatch alarm). Emits the CF-status JSON artifact; alerts on any RED. **NOT applied** (operator applies).
- [ ] [DATA] P2. **Wire into QG-smoke where feasible** — a fast subset (schema_version/source/pipeline_mode-form
      distribution on a sampled day) as a peripheral-script QG so a per-repo gate catches the grossest data-state drift
      too.

## Success criterion

Re-running the per-AG ①–⑫ / CF-1…CF-14 audit by hand surfaces NOTHING the automation didn't already flag: every code
criterion is a QG step (commit-time, all repos) and every data-state criterion is a scheduled alert (daily, all AG
buckets). The agentic audit is then reserved for genuinely-new findings, not recurring verification.
