---
doc_type: plan
title: Instruments + MTDS/MDPS plan consolidation — 3 active survivors + 1 deferred
summary:
status: active
nature: process
stage: [meta]
repos: [instruments-service]
scope: [engineer, admin]
tags: []
related: [../epics/instruments_master.md, ../epics/mtds_mdps_master.md]
created: 2026-06-26
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope:
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
last_updated: 2026-06-26
locked_by: live-defi-rollout
locked_since: 2026-06-26
supersedes:
superseded_by:
depends_on:
source:
---

# Instruments + MTDS/MDPS plan consolidation — 2026-06-26

> **Operator directive 2026-06-26**: "amalgamate everything to do with instruments and MTDS into groups of plans —
> archive/supersede every plan that is done or largely-done, and fold remaining todos into another plan." Scope =
> **strict core** (instruments-service + MTDS/MDPS only; tangential sports/predictions/cefi-perps/strategy plans stay
> under their home epics, cross-linked only). Shape = **themed survivors** (2 per domain). Archival **authorised**
> (`[unlock-plan]` granted for the locked candidates).

## End state — 3 active survivors + 1 deferred + 3 retained issue docs

| Group                                                     | Survivor (stays active)                                                 | Absorbs (archived after fold)                                                                                                                                |
| --------------------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **I-1 · Instruments Foundation & Catalogue Completeness** | `instruments_foundation_completeness_2026_06_24`                        | `proper_instrument_catalogue_lifecycle_rollup` (9) · `tradfi_databento_subscription_universe_lockdown` (7) · `defi_venue_name_canonicalisation_and_reth` (1) |
| **I-2 · IS↔MTDS Canonicalisation & Consistency**          | `instruments_mtds_subset_consistency_remediation_2026_06_17`            | `instruments_manifest_canonicalisation` (8) · `issues/instruments_service_audit_findings` (14)                                                               |
| **M-1 · MTDS Backfill-to-100% & Capture**                 | `path_to_100pct_backfill_mtds_is_2026_06_17`                            | `defi_instrument_catalogue_and_capture_pipeline` (11) · `defi_mtds_subgraph_and_adapter_fixes` (2) · `mtds_honest_absence_swallow_remediation` (3)           |
| **M-2 · MTDS/MDPS Tech-Debt & Coverage** ⏸️ **DEFERRED**  | `mtds_file_size_refactor_2026_06_08` (retitled; `status: deferred`, P3) | `mdps_adapter_protocol_pandas_to_polars` (2) · `mtds_coverage_75_and_codex_zero` (3) · `mdps_coverage_85pct` (1)                                             |

**Pure archivals** (DONE/SUPERSEDED — banner + move only): `instruments_backfill_phase3` · `mtds_backfill_phase3` ·
`mdps_backfill_phase3`.

**Retained live issue docs** (referenced by survivors, not folded): `features_delta_one_tradfi_mdps_dependency_gap`
(operator-decision architectural gap) · `fleet_mtds_qg_red_hardcoded_url_record_empty_ratchet` ·
`mtds_cefi_mvp_gate_and_thegraph_shard_test_fleet_red`.

**Stale epic-link fixes**: `instruments_master` still links `d1_is_hardening`, `expected_universe_v2_design`,
`trigger_based_reference_data` as active — all 3 are already in `archive/2026_05/` and 100% done; repoint + mark DONE.

## Execution todos

- [x] [PLAN] P1. **Batch 1 — pure archivals + stale epic-link fixes.** ✅ 3 DONE/SUPERSEDED backfill plans archived to
      `archive/2026_06/`; the 3 stale `instruments_master` related_plans links repointed to `archive/2026_05/`.
- [x] [PLAN] P1. **Batch 2 — I-1 fold.** ✅ 17 todos from the 3 I-1 sources migrated into the "Folded-in (I-1)" section
      of `instruments_foundation_completeness` (now 52 open); 3 sources archived.
- [x] [PLAN] P1. **Batch 3 — I-2 fold.** ✅ `instruments_manifest_canonicalisation` (8) +
      `issues/instruments_service_audit_findings` (14) migrated into `instruments_mtds_subset_consistency_remediation`
      (now 60 open); both sources archived (issue → `archive/issues/`).
- [x] [PLAN] P1. **Batch 4 — M-1 fold.** ✅ 16 todos from the 3 M-1 sources migrated into
      `path_to_100pct_backfill_mtds_is` (now 24 open); 3 sources archived. BLOCKED-OPERATOR-DECISION (CLOB asset_group
      classification) preserved.
- [x] [PLAN] P1. **Batch 5 — M-2 fold + retitle.** ✅ `mtds_file_size_refactor` retitled "MTDS/MDPS tech-debt &
      coverage"; 6 todos from the 3 M-2 sources migrated (now 9 open); 2 QG/test issue docs referenced; 3 sources
      archived.
- [x] [PLAN] P2. **Epic refresh.** ✅ `instruments_master` + `mtds_mdps_master` carry consolidation banners pointing at
      the 4 survivors; `last_updated` → 2026-06-26; instruments assigned-plans section repointed; MTDS migration phases
      marked HISTORICAL.
- [x] [PLAN] P2. **Inventory + codex alignment.** ✅ `regenerate_active_plan_inventory.py` re-run (111 plans, 0
      orphans); 3 codex provenance pointers + `defi_master` epic links repointed from `active/` to the archived paths
      (no codex doc cites an archived plan as SSOT — they were "see plan" pointers).
- [ ] [PLAN] P3. **Self-archive.** Gated on operator review + commit of this consolidation. Once landed, archive THIS
      plan (its end-state map is the durable record).

## Provenance log (5-step ritual — migrate → banner → codex-align → epic update → lock-clear)

**Archived to `archive/2026_06/` (lock cleared, ARCHIVED-2026-06-26 banner, status→archived):**

| Plan                                                                       | Done/folded           | → Survivor                       |
| -------------------------------------------------------------------------- | --------------------- | -------------------------------- |
| `instruments_backfill_phase3_2026_05_22`                                   | 26/26 DONE+SUPERSEDED | (none — I-1/I-2 cover live work) |
| `mtds_backfill_phase3_2026_05_22`                                          | 42/42 DONE+SUPERSEDED | (none — M-1 covers live work)    |
| `mdps_backfill_phase3_2026_05_22`                                          | 46/46 DONE+SUPERSEDED | (none — M-1/M-2 cover live work) |
| `proper_instrument_catalogue_lifecycle_rollup_2026_06_04`                  | 16/25 · 9 folded      | I-1                              |
| `tradfi_databento_subscription_universe_lockdown_2026_06_18`               | 26/33 · 7 folded      | I-1                              |
| `defi_venue_name_canonicalisation_and_reth_2026_06_17`                     | 4/5 · 1 folded        | I-1                              |
| `instruments_manifest_canonicalisation_2026_06_01`                         | 5/13 · 8 folded       | I-2                              |
| `issues/instruments_service_audit_findings_2026_06_08` → `archive/issues/` | 2/16 · 14 folded      | I-2                              |
| `defi_instrument_catalogue_and_capture_pipeline_2026_06_23`                | 11/22 · 11 folded     | M-1                              |
| `defi_mtds_subgraph_and_adapter_fixes_2026_06_20`                          | 3/5 · 2 folded        | M-1                              |
| `mtds_honest_absence_swallow_remediation_2026_06_10`                       | 14/17 · 3 folded      | M-1                              |
| `mtds_coverage_75_and_codex_zero_2026_06_11`                               | 5/8 · 3 folded        | M-2                              |
| `mdps_adapter_protocol_pandas_to_polars_2026_06_21`                        | 0/2 · 2 folded        | M-2                              |
| `mdps_coverage_85pct_2026_06_10`                                           | 9/10 · 1 folded       | M-2                              |

**14 plans archived → 3 active survivors (I-1, I-2, M-1) + 1 deferred (M-2, non-essential tech-debt) + 3 retained issue
docs.** No commit/push yet — changes staged for operator review (`git mv` renames + survivor/epic edits visible in
`git status`).

> **Deferral 2026-06-26 (operator):** M-2 (`mtds_file_size_refactor` / "MTDS/MDPS tech-debt & coverage") set to
> `status: deferred`, P3 — pure tech-debt, not needed to get the data pipeline started; the live MTDS-ship blocker is
> the separate issue `fleet_mtds_qg_red_…`, which stays active. Also non-essential and downgraded to P3: the DeFi
> catalogue **discontinuous-availability-ranges** producer enhancement (the `(→ I-1)` bullet in M-1) — the single-window
> rollup is fine to start; only build discontinuous ranges if drop-then-recover modelling later proves necessary.

## Post-fold conflict audit (2026-06-26) — cross-survivor overlaps found + reconciled

Folding 14 plans into 4 surfaced overlapping/contradictory todos. Audited all 4 survivors; resolved:

1. **DeFi catalogue — two plans each claimed to build "the catalogue MTDS reads."** Code-checked
   (`build_instrument_catalogue.py` + MTDS `_catalogue_filter.py`): there is **ONE** catalogue — the lifecycle-rollup
   `{env}/catalog.parquet`, **no TVL ranking at build time**; TVL is reconciled at MTDS **capture** time via
   `EXPECTED_NOT_ENOUGH_TVL` (shipped @3b901087/c4c5f15). I-1 owns catalogue PRODUCTION; M-1's three "IS build per-day
   TVL snapshot/aggregation/single catalogue file" P0s are SUPERSEDED (RECONCILED note in M-1); the one genuine producer
   gap — discontinuous availability ranges — is cross-linked to I-1.
2. **TradFi/CME backfill fragmented across I-1, I-2, M-1 + the tradfi-domain plan.** Ownership rule applied: IS-side
   catalog/definition backfill = I-1/I-2; MTDS market-data OHLCV backfill = M-1; CME EC\* event-contract slice =
   `tradfi_cme_event_contract_backfill_2026_06_20` (tradfi_master). I-1:"MTDS tradfi backfill" → "(→ M-1)"; I-2 CME EC\*
   → "v9-certification dependency only, defer to plan-of-record."
3. **M-1 sequencing gap.** M-1 backfill needs a FRESH IS catalog (frozen ~2026-05-21 + dead producer per I-1); added a
   SECOND-GATE banner to M-1 so per-AG backfill gates on I-1's catalog/producer rebuild, not only I-2's v9 `--apply`.
4. **False alarm — `engine/orchestrator.py` split in both M-2 and I-2.** Different repos (MTDS 4,219L vs
   instruments-service 8,192L); added "do not conflate" NB to both todos.
