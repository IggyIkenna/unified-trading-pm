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

- [ ] [SCRIPT] P1. **QG step: no coarse `pipeline_mode = "batch"` / blank stamp** — grep migrators/rebuilds/writers for
      a coarse default; baseline-ratchet (0 today, must stay 0). Catches the DeFi `DEFAULT_PIPELINE_MODE="batch"` class
      reappearing. Repo: PM QG template → all repos. (Extends STEP 5.70 which only checks _presence_.)
- [ ] [SCRIPT] P1. **QG step: no exact-coarse reader probe** — grep readers for `pipeline_mode=batch/` / `=live/` exact
      (not prefix `batch_*`); 0 hits (the C-PATH READ fix must not regress). features + mdps + mtds.
- [ ] [SCRIPT] P1. **QG step: no Era-A `data_type=options_chain`/`futures_chain` WRITE** — grep writers/migrators;
      chains must write `instrument_type=…` + `data_type=trades` (the `tardis_shared._LEGAL_DATA_TYPES` raise is the
      runtime guard; the QG step is the static one).
- [ ] [SCRIPT] P2. **QG step: validity-matrix completeness** — a UAC test asserting every `(instrument_type, data_type)`
      in `SOURCE_PRIORITY`/the matrix is either valid or explicitly excluded; no impossible pair enumerable.
- [ ] [SCRIPT] P1. **QG step: no pre-aggregated open-edge bar ingestion** — extend `check_mdps_bar_boundary_compliance.py`
      beyond the MDPS write path to reference-data + pre-agg ingestion adapters; flag a vendor bar-START field
      (`t`/`periodStartUnix`/`bar[0]`/DataFrame index) stamped without a `compute_bar_close_boundary`/explicit-close-field
      conversion (baseline the known latent sites → NEW open-edge ingestion fails the commit). Owned by
      `bar_edge_left_vs_right_remediation_2026_06_08.md` Phase 0; tracked here as the Tier-2 entry.
- [ ] [SCRIPT] P2. Wire all of these into `base-service.sh` / `base-library.sh` (STEP 5.9x) + the PM template; baseline
      any pre-existing hits (ratchet), so NEW regressions fail the commit for ALL repos/AGs.

## Phase 2 — Tier-3 data-state audit: extend + cross-AG + schedule (the continuous-verification cron)

- [ ] [CODE] P1. **Extend `cf_manifest_audit` to CF-1…CF-14**: add CF-13 (pipeline*mode matches
      `batch*<source>`    source-aware FORM, not just populated;`source_string_for(pm)==source`), CF-14 (`build_instrument_catalogue`⊇     manifest present-set), Era-B (chains as instrument_type +`data_type=trades`, count `data_type=(options_chain|
      futures_chain)`==0), CF-6 (expected_unattempted present for IS-listed-not-backfilled), CF-10 (object-backed
      captured only). Emit per-CF GREEN/RED with evidence + a machine-readable summary (JSON) for alerting.
- [ ] [CODE] P1. **Cross-AG wrapper** — one invocation runs all 5 AGs × {market-data-tick, instruments-store} buckets
      (the 10 buckets), per-AG GREEN/RED rollup.
- [ ] [INFRA] P1. **Schedule it** — a daily Cloud Run Job + Scheduler (per the consolidator pattern) that runs the
      cross-AG audit and **alerts on any RED** (the master plan's "Continuous Verification" column, finally wired). NOT
      fire-and-forget; emits a CF-status artifact.
- [ ] [DATA] P2. **Wire into QG-smoke where feasible** — a fast subset (schema_version/source/pipeline_mode-form
      distribution on a sampled day) as a peripheral-script QG so a per-repo gate catches the grossest data-state drift
      too.

## Success criterion

Re-running the per-AG ①–⑫ / CF-1…CF-14 audit by hand surfaces NOTHING the automation didn't already flag: every code
criterion is a QG step (commit-time, all repos) and every data-state criterion is a scheduled alert (daily, all AG
buckets). The agentic audit is then reserved for genuinely-new findings, not recurring verification.
