---
doc_type: epic
title: Instruments Live — Master Activation Plan
summary:
  L1 epic owning instruments-service reference-data activation — catalogue completeness, IS↔MTDS canonical-form
  single-walk (CF-1…CF-12), tradfi/DeFi-LST universe lockdown, incremental catalogue rollup, and the
  INSTRUMENT_CACHE_REFRESH_TRIGGER publish side; live work runs through survivors I-1/I-2 (I-3 complete 2026-07-10, was
  listed as an open survivor -- annotated 2026-07-12, finding 125, §A2 B-queue ruling).
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    alerting-service,
    deployment-service,
    features-service,
    instruments-service,
    unified-api-contracts,
    unified-trading-library,
  ]
scope: [engineer, admin]
tags: [instruments, catalogue, mtds, single-walk, canonicalisation, tradfi, defi, registry]
related:
  [
    ../archive/2026_07/mvp_catalogue_finalization_v10_2026_06_27.md,
    ../archive/2026_05/d1_is_hardening_2026_05_20.md,
    ../archive/2026_05/expected_universe_v2_design_2026_05_08.md,
    ../archive/2026_05/trigger_based_reference_data_2026_04_13.md,
    ../active/global_ledger_pnl_attribution_discovery_2026_05_21.md,
  ]
created: 2026-05-08
name: instruments_master
tier: L1
priority: P0
assigned_vm: vm-cefi # epic-level ownership label (legacy per-VM convention, retained workspace-wide across ALL epics/*.md as of 2026-07-12; distinct from PLAN `assigned_vm` which is {planning, NA}-only post-2026-06-27 -- annotated 2026-07-12, finding 123, §A2 B-queue ruling, no value change -- workspace-wide epic-schema migration is out of scope here)
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans:
  - ../active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md
  - ../active/instrument_record_schema_completeness_extra_forbid_2026_07_18.md
  - ../active/instruments_cefi_g1_g5_gate_execution_2026_07_24.md
  - ../active/instruments_completion_tracker_2026_07_06.md
  - ../active/instruments_foundation_completeness_2026_06_24.md
  - ../active/instruments_foundation_phase0_cross_cutting_2026_07_24.md
  - ../active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md
  - ../active/instruments_mtds_consistency_remediation_residuals_2026_07_24_finalize.md
  - ../active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md
  - ../active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md
  - ../active/mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md
  - ../active/mvp_could_exist_rollup_dual_scope_2026_08_12.md
  - ../active/prediction_capture_incident_remediation_2026_07_06.md
  - ../active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md
  - ../active/tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md
  - ../active/tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16_finalize.md
  - ../active/tradfi_satellite_ao_dispatch_batch9_2026_08_09.md
  - ../active/tradfi_satellite_ao_dispatch_batch9_2026_08_09_finalize.md
last_updated: 2026-08-19 # bumped 2026-07-14 (was: 2026-07-08, unchanged despite the 2026-07-12 body edits below; finding 125 verify-rerun-2, doc-reconciliation sync)
locked_by: live-defi-rollout
locked_since: 2026-05-08
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

<!-- 2026-07-12 doc-reconciliation sync (findings 96/101/106/111/117/123/125, §A2 B-queue ruling): epic-body staleness
     annotated in place below (was: unannotated) — see body markers for each finding's correction. -->

<!-- 2026-07-14 doc-reconciliation sync (verify-rerun-2 pass, distinct finding-id space from the 07-12 pass above —
     that pass's "123"/"125" covered unrelated topics; this pass's own findings 123/146/150 are body markers below,
     125 is the frontmatter last_updated bump above). -->

# Instruments Live — Master Activation Plan

## Report

Live HTML ledger: https://claude.ai/code/artifact/f4b0545a-b1be-4554-94b5-8e99e5948798 (generated 2026-08-19,
`/plan-reconcile instruments_master`)

> **🔵 CONSOLIDATION 2026-06-26 — live instruments work now runs through 2 themed survivors.** Per the operator's
> instruments/MTDS amalgamation (`../active/instruments_mtds_plan_consolidation_2026_06_26.md`), all done/largely-done
> instruments plans were archived and their residual todos folded into:
>
> - **I-1 ·
>   [`instruments_foundation_completeness_2026_06_24`](../active/instruments_foundation_completeness_2026_06_24.md)** —
>   foundation + catalogue completeness + tradfi-universe-lockdown + DeFi-LST universe (absorbed
>   `proper_instrument_catalogue_lifecycle_rollup`, `tradfi_databento_subscription_universe_lockdown`,
>   `defi_venue_name_canonicalisation_and_reth`).
> - **I-2 ·
>   [`instruments_mtds_subset_consistency_remediation_2026_06_17`](../archive/2026_07/instruments_mtds_subset_consistency_remediation_2026_06_17.md)**
>   — ARCHIVED 2026-07-26 (trimmed 2026-07-24 to a pure entry-point index, 0 todos of its own; the substantive scope
>   this bullet used to describe was 3-way split into 3 live children): IS↔MTDS canonical-form single-walk (CF-1…CF-12)
>   →
>   [`instruments_store_cf_canonicalization_single_walk_2026_07_24`](../active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md);
>   core F1-F7/N1-N9 audit-remediation residuals →
>   [`instruments_mtds_consistency_remediation_residuals_2026_07_24`](../active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md);
>   venue-onboarding + ops-hardening →
>   [`mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24`](../active/mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md)
>   (absorbed `instruments_manifest_canonicalisation`, `issues/instruments_service_audit_findings`).
> - **I-3 ·
>   [`instruments_catalogue_incremental_rollup_2026_06_29`](../archive/2026_07/instruments_catalogue_incremental_rollup_2026_06_29.md)**
>   — incremental (trailing-window + frozen-tail) catalogue rollup replacing the full-history re-aggregation that now
>   exceeds the Cloud-Run 3600s task timeout (2026-06-29 `DP_CATALOG_NOT_RUNNING`); prototype-measured ~0.9 min vs 137
>   min. Successor to `proper_instrument_catalogue_lifecycle_rollup` (the full-rebuild originator). **2026-07-12
>   correction (was: presented below as a live/open survivor; finding 125, §A2 B-queue ruling): I-3 flipped
>   `status: active` → `complete` on 2026-07-10 (27 of 28 todos confirmed `[x]` with cited runtime evidence, per its own
>   Progress Log) — no longer an open workstream; retained here only as historical routing context for pre-2026-07-10
>   work.**
>
> Newly archived under `../archive/2026_06/`: the 3 above sources + `instruments_backfill_phase3` (DONE/SUPERSEDED). The
> Phase A-Z activation content below is retained as historical design intent.

> **🟢 SIBLING — Live-pipeline activation 2026-05-08**
>
> [`live_pipeline_mtds_mdps_features_2026_05_08`](../active/live_pipeline_mtds_mdps_features_2026_05_08.md) Phase 10
> consumes the `INSTRUMENT_CACHE_REFRESH_TRIGGER` event this plan publishes, via the new UTL
> `InstrumentCacheDeltaReloader` helper (cache-delta hot-reload pattern). **This plan owns the publish-side** (verify or
> add the event publication in instruments-service); **the live-pipeline plan owns the consume-side** (UTL helper +
> per-service wiring in MTDS/MDPS/features-service). Codex pattern doc:
> [`/codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md`](/codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md).

## Why this plan exists

The unified-trading-system already has the **architecture** for live-mode instruments — the codex SSOTs
(`batch-live-architecture.md`, `backfill-and-live-startup.md`, `live-deployment-monitoring.md`,
`alerting-batch-live.md`, `sports-live-odds-connectivity.md`, `deployment-clusters-live-vs-batch.md`,
`runtime-tiers-and-deployment.md`, the per-asset-group instruments-service docs in `instruments-service/docs/`)
collectively express the target state already. What's MISSING is the **activation surface**: which scheduler fires which
trigger, which adapter is the live-source, which UI surfaces let an operator monitor it, and which audit job proves
live=batch after the fact. This plan owns the activation surface, references the SSOTs for design intent, and references
the active issues for data-correctness sub-deltas.

## Principles (not new — restating from codex SSOTs for plan-anchored visibility)

1. **Live writes to the SAME GCS path as batch.** No `live=` partition, no `live_` prefix, no parallel hierarchy.
   Downstream consumers (MTDS catalog load, features-\* preflight, strategy preflight) read one path regardless of how
   the row got there. SSOT: `/codex/04-architecture/batch-live-architecture.md`.

2. **T+1 is an audit/comparison job, NOT a backfill.** Live writes are authoritative; batch is the truth-checker.
   Discrepancies are alerted; they do NOT trigger automatic re-write of live rows. SSOT: same doc § T+1 Scheduling.

3. **Live-mode CLI = batch CLI + a `--mode live --trigger <name>` flag.** Same code path, same orchestrator, same
   `record_captured/record_empty/record_failed` semantics. The seam is the source-adapter pick. SSOT:
   `/codex/06-coding-standards/cli-convention.md`.

4. **`available_at` is per-row write-time, equal to live-pipeline-arrival.** Already enforced workspace-wide (CLAUDE.md
   `available_at` rule); live-mode writes inherit this without new code.

5. **No fire-and-forget Cloud Scheduler invocations.** Every scheduled run must emit `STARTED` + per-entity progress
   events + `STOPPED` or `FAILED` per CLAUDE.md "no fire-and-forget VM launches" rule. Phase F.2 dry-fire validates this
   before any schedule is promoted to prod.

6. **Preflight chain is live=batch — same dependency rules, same UTL helper, same typed events.** Downstream triggers
   (sports lineups / weather / injuries / fixture-stats; cefi+tradfi 15-min OHLCV when instrument-catalog is stale;
   prediction-discovery on empty UAC registry) MUST run preflight against the upstream entity-set BEFORE making any
   source call. Preflight uses the SAME UTL helper batch uses (Phase A.10) reading the SAME UAC SSOT (Phase A.9) probing
   the SAME manifest with the SAME freshness helpers. Live differs ONLY in invocation cadence. Preflight failure
   short-circuits the trigger AND emits a typed `INSTRUMENTS_LIVE_PREFLIGHT_FAILED` event whose payload names the
   specific missing upstream — Phase H.1 alerting routes this to Telegram with the missing-dep detail in the message
   body, so the operator can act in seconds. An independent upstream-staleness monitor (Phase A.11) emits
   `INSTRUMENTS_LIVE_UPSTREAM_STALE` proactively before any downstream trigger fires-and-fails — early-warning surface.
   Why this matters: silent upstream-staleness is the single most common cause of "live pipeline degraded but nobody
   noticed for 4 hours" — typed preflight events turn it into a sub-minute Telegram alert.

## Asset-group routing matrix (cadence + trigger + source per entity-type)

This is a SUMMARY for plan-anchored navigation. The authoritative version is the new
`/codex/04-architecture/instruments-live-architecture.md` (Phase A.1).

| Asset group | Entity type        | Cadence / trigger                | Live source           | Batch source      | Phase |
| ----------- | ------------------ | -------------------------------- | --------------------- | ----------------- | ----- |
| sports      | Fixtures           | Daily re-poll [today, today+8d]  | api_football REST     | api_football REST | B.1   |
| sports      | Fixture end_time   | Status-flip cascade              | api_football REST     | api_football REST | B.2   |
| sports      | Leagues + teams    | Per-league season-roll (2 fires) | api_football + FS     | same              | B.3   |
| sports      | Player values      | Transfer-window open + close     | Transfermarkt         | same              | B.4   |
| sports      | Weather            | 8 fires per fixture pre-kickoff  | open-meteo            | same              | B.5   |
| sports      | Lineups + injuries | kickoff-60min + event-time       | api_football          | same              | B.6   |
| tradfi      | OHLCV 15m          | Wall-clock 15-min                | Polygon (TBD per C.1) | Databento         | C.1-2 |
| tradfi      | VIX OHLCV 15m      | Wall-clock 15-min                | Yahoo Finance (live)  | Barchart preload  | C.3   |
| cefi        | OHLCV 15m          | Wall-clock 15-min                | CCXT                  | Tardis (T+1)      | D.1-2 |
| prediction  | Market discovery   | Wall-clock 15-min                | Polymarket / Kalshi   | same              | E.1   |
| prediction  | CLOB ticks         | Continuous (already MTDS scope)  | Polymarket CLOB       | same              | E.2   |

## Dependencies + sibling plan references

- **`master_to_live_defi_2026_05_23.md`** — sibling. DeFi-live (the master plan's headline goal) does NOT depend on most
  of this plan, but the DeFi instruments-live triggers (cefi 15-min CCXT for hedge legs on Bybit/Deribit/
  Binance/OKX/Hyperliquid/Aster, plus DeFi-onchain instruments triggers covered separately by `defi_master`) ARE in the
  master critical path. Phase D + the AWS-mirror in F.3 are the parts of THIS plan that the master needs by 2026-05-23;
  everything else (sports / tradfi / prediction live) is post-2026-05-23.
- **`writegate_honest_coverage_endtoend_2026_05_06.md`** — depends_on. Live-mode `record_captured` / `record_empty`
  semantics inherit from writegate Phase 2.D; this plan does NOT re-derive write-gate rules.
- **`alerting_service_live_rules_2026_05_07.md`** — depends_on. Owns the rule engine; THIS plan adds the
  instruments-live entries (Phase H.1).
- **`deployment_api_work_stream_a_2026_05_07.md`** — depends_on. Owns programmatic VM launch + event-tail endpoints;
  THIS plan reuses event-tail logic for the Scheduled Jobs tab (Phase G.1).
- **`launcher_scripts_consolidation_into_deployment_service_2026_05_07.md`** — depends_on. Owns launcher SSOT migration;
  THIS plan's Phase F.1 adds Cloud Scheduler config under the same `deployment-service/scripts/` root.
- [`trigger_based_reference_data_2026_04_13.md`](../active/trigger_based_reference_data_2026_04_13.md) — **active
  sibling** (promoted from `plans/ai/` to `plans/active/` on 2026-05-14 per operator decision = option b). Owns the
  sports trigger calendar design; THIS plan's Phase B references it and completes in parallel (no fold). Phase B.0
  unlock-request RESOLVED.

## Active issues this plan references (does NOT duplicate)

- `plans/archive/issues/instruments_lifecycle_and_fixtures_endtime_cascade_2026_05_08.md` — schema requirements for
  futures expiry, options expiry, fixtures end_time. Phase B.2 references; issue owns the cascade rules.
- `plans/archive/issues/fixtures_postponed_cancelled_lifecycle_2026_05_08.md` — fixture lifecycle column shape. Phase
  B.1 references; issue owns the column shape.
- `plans/archive/issues/fixtures_lookahead_bias_post_match_scores_2026_05_08.md` — `available_at` for post-match scores.
  Phase B.1 + B.2 references; issue owns the bias rule.
- `plans/archive/issues/manifest_cleanup_on_entity_add_remove_2026_05_08.md` — manifest reconciliation when entities are
  added/removed (e.g. promotion/relegation, new market_id). Phase B.3 + E.1 reference; issue owns the cleanup rules.
- `plans/archive/issues/predictions_completeness_hierarchy_lifecycle_drilldown_2026_05_08.md` — lifecycle drilldown for
  predictions. Phase E.1 references; issue owns the lifecycle taxonomy.
- `plans/archive/issues/sports_per_fixture_anchored_cascade_2026_05_08.md` — fixture-anchored cascade for sports. Phase
  B.5 + B.6 reference.
- `plans/archive/issues/mtds_live_data_recovery_self_detect_2026_05_08.md` — self-recovery for missed live fires. Phase
  D.1 references; issue owns the recovery pattern.
- `plans/archive/issues/databento_tradfi_session_type_awareness_2026_05_08.md` — TradFi session-type schema fix. Phase
  C.4 references.

## Codex doc updates this plan owns

| Codex doc                                                    | Update                                                                                     | Phase |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------ | ----- |
| `04-architecture/instruments-live-architecture.md` (NEW)     | Single entry-point + routing matrix + cadence/trigger/source per (asset_group, entity)     | A.1   |
| `04-architecture/batch-live-architecture.md`                 | Add "Instruments are reference data" section explicit on same-path + T+1-as-audit          | A.2   |
| `04-architecture/instruments-preflight-chain.md` (NEW)       | Preflight DAG SSOT + live=batch invariant + UTL helper contract                            | A.9   |
| `05-infrastructure/runtime-tiers-and-deployment.md`          | Add "Instruments-live Cloud Scheduler topology" section listing all scheduled entries      | A.3   |
| `04-architecture/alerting-batch-live.md`                     | Add "Instruments-live failure rules" section (7 typed failure modes including 2 preflight) | A.4   |
| `02-data/pipeline-coverage-matrix.md`                        | Add live-source row per (asset_group, data_type)                                           | C.1   |
| `00-SSOT-INDEX.md`                                           | Add row pointing to `instruments-live-architecture.md`                                     | A.1   |
| `15-runbooks/instruments-live/t1-audit-discrepancy.md` (NEW) | Operator playbook for T+1 audit discrepancies                                              | I.3   |
| `instruments-service/docs/ADAPTER_ARCHITECTURE.md`           | Add live-mode CLI invocation matrix table                                                  | A.7   |

## Architectural conflicts found in instruments-service repo

**None.** Reviewed `instruments-service/docs/ADAPTER_ARCHITECTURE.md` and the per-asset-group docs (CEFI/DEFI/TRADFI/
SPORTS/PREDICTION) plus `instrument-catalogue.md`. The repo's documented architecture already aligns with live=batch
symmetry: no statement that "live mode has different schema" or "live writes to a separate path" was found. The existing
CLI is single-codepath; adding `--trigger` as a new axis is additive (Phase A.7).

## Out of scope (referenced but owned elsewhere)

- DeFi onchain instruments live triggers (governance params, RPC discovery, contract-event indexing) → owned by
  `defi_master.md`. This plan's matrix above does NOT include defi rows because the asset_group's live triggers are
  intrinsically onchain-event-driven, not wall-clock; they ride a different architecture surface.
- Per-shard market-tick capture (MTDS market data, NOT instruments) — owned by per-asset-group MTDS plans
  (`cefi_master`, `tradfi_master`, `sports_master`, `predictions_master`). Phases C.2, D.1, E.2 above touch MTDS only
  because tradfi/cefi/prediction "instruments" 15-min OHLCV cadence sits inside MTDS adapters, not instruments-service.
- Telegram bot infra and the alerting-service rule engine — owned by `alerting_service_live_rules_2026_05_07`.

> **Routing gap flagged 2026-07-14 (finding 126, unresolved — needs an operator ruling, not fixed here)**: despite the
> two disclaimers above, `archive/issues/wsfeedconnector_phase35_gap_2026_07_06.md` carries
> `parent_epic: instruments_master` (repos: `market-tick-data-service`) yet its content is precisely per-venue MTDS
> `WSFeedConnector` live-tick capture wiring across cefi/tradfi/sports/defi — including a "### DeFi — 49 venues" section
> building onchain-protocol connectors (Uniswap/Aave/Compound/Morpho/Lido/GMX etc.) — i.e. exactly both disclaimed
> categories. Neither doc reconciles this; annotated in place only, not resolved.

## Parallelisation strategy

```
Phase A (foundation, all PARALLEL within phase)
  ├─ A.1 codex SSOT entry-point             ─┐
  ├─ A.2 batch-live-symmetry instruments    ─┤
  ├─ A.3 runtime-tiers cron topology        ─┤
  ├─ A.4 alerting failure rules taxonomy    ─┤  ← all completable independently
  ├─ A.5 UAC LifecycleEventType extension   ─┤
  ├─ A.6 UAC trigger calendar               ─┤
  ├─ A.7 instruments-service CLI axis       ─┤
  ├─ A.8 UTL ManifestWriter live-mode test  ─┤
  ├─ A.9 preflight DAG SSOT (UAC + codex)   ─┤  ← gates all asset-group preflight wiring
  ├─ A.10 UTL preflight validator helper    ─┤  ← gates all asset-group preflight wiring
  └─ A.11 upstream-staleness monitor        ─┘  ← can ship after A.10 (Phase F deploys)
            │
            ▼  QG gate
Phase B / C / D / E (asset-group adapters, all PARALLEL)
  ├─ B (sports)   — B.0a preflight wiring → B.1-B.6 triggers (depends on A.10)
  ├─ C (tradfi)   — C.0 preflight wiring  → C.1 (source decision) → C.2 (adapter)
  ├─ D (cefi)     — D.0 preflight wiring  → D.1 (CCXT adapter) → D.2 (router)
  └─ E (prediction) — E.0 preflight wiring → E.1 (discovery) → E.2 (CLOB confirm)
            │
            ▼  QG gate
Phase F (Cloud Scheduler activation)
            │
            ▼  QG gate
Phase G (deployment-UI tab)  ║  Phase H (alerting + circuit breakers, parallel to G)
            │                                       │
            └───────────────────┬───────────────────┘
                                ▼
            Phase I (T+1 audit, depends on ≥1 day of live data)
                                │
                                ▼
            Phase Z (workspace QG + D3 staging + B4 batch-vs-live recon)
```

## Success criteria

- **C5**: every repo in `repo_gates` reaches C5 (quickmerged).
- **D3**: all Cloud Scheduler entries deployed to staging, dry-fire passes, Telegram alerts fire on injected fault.
- **B4**: 7 days of live data audited via Phase I.2, discrepancy rate within per-asset-group tolerance documented in the
  `instruments-live-architecture.md` doc.
- **B6**: operator approves Scheduled Jobs tab UX + audit-discrepancy playbook.

## SSOT references

- `/codex/04-architecture/batch-live-architecture.md` — live=batch, same path, T+1 is audit (single SSOT — replaces
  former batch-live-pipeline.md + batch-live-symmetry.md)
- `/codex/04-architecture/backfill-and-live-startup.md` — live startup pattern
- `/codex/04-architecture/alerting-batch-live.md` — alerting rules
- `/codex/04-architecture/sports-live-odds-connectivity.md` — sports live ingest reference
- `/codex/04-architecture/runtime-deployment-topology.md` — operational modes
- `/codex/05-infrastructure/runtime-tiers-and-deployment.md` — deployment tiers
- `/codex/05-infrastructure/live-deployment-monitoring.md` — monitoring pattern
- `/codex/05-infrastructure/deployment-clusters-live-vs-batch.md` — cluster topology
- `/codex/05-infrastructure/launcher-script-ssot.md` — VM launcher SSOT (referenced by Cloud Scheduler config)
- `/codex/06-coding-standards/cli-convention.md` — CLI axis SSOT
- `/codex/02-data/availability-manifest-and-data-status.md` — manifest schema, available_at
- `/codex/02-data/pipeline-coverage-matrix.md` — per-source coverage matrix
- `instruments-service/docs/ADAPTER_ARCHITECTURE.md` + per-asset-group docs — service-internal entry-points

## Plan-format compliance

This plan follows `unified-trading-pm/plans/PLAN_FORMAT.md`:

- 3-tier readiness model declared: code C5, deployment D3, business B4.
- Per-repo gate progress in YAML frontmatter.
- Cursor checkboxes on every todo.
- Pre-audit complete: `_AUDIT_2026_05_07_dependency_graph.md` and the codex-coverage agent run that produced this plan
  inventoried all existing plans + issues + codex docs; no duplicate work surfaced.
- Phased execution DAG with QG gates between phases.
- Parallelisation explicit (block above).
- No technical debt: source-switch is one routing point per asset_group, not a parallel codepath.
- Downstream consumer audits scoped per phase.
- Single source of truth: codex doc updates listed in the table above; plan REFERENCES the docs, does NOT duplicate.

## DONE-2026-05-09 — Phase A.7 (Tab F1)

Tab F1 (agent-tag `instruments-cli-trigger-tab`, spawn from `work_split_2026_05_08_ikenna.md`) shipped Phase A.7's
`--trigger` axis on the instruments-service CLI:

- **instruments-service@5d511e6** — `feat(cli): add --trigger live-mode flag to instruments-service CLI`. 3 files / 283
  insertions: `instruments_service/cli/main.py` (argparse arg via `_add_instruments_extra_args`),
  `instruments_service/cli/instruments_handler.py` (`handler._trigger_name` field + `_wire_cli_filters_from_args` wire),
  `tests/unit/cli/test_trigger_axis.py` (9 unit tests — 5x parametrised parser asserts across canonical trigger names +
  default-None batch + preflight wire-through + absent-trigger None + legacy-Namespace getattr-fallback).

Verification:

- Local pytest: 17/17 CLI tests pass (including 9 new + 8 pre-existing rolling-window).
- Local ruff: 3/3 files clean (lint + format).
- Local basedpyright: pre-existing 1329-error workspace state on origin (per CLAUDE.md QG-cleanup window 2026-05-07 →
  ~2026-05-09); my changes add 5 errors all identical-pattern to existing `getattr(self.args, ...)` callsites at
  handler.py:85-117. Sweep absorbs them.
- Conditional push: `git rev-list --left-right --count HEAD...origin/live-defi-rollout` = `0 0` post-push.

Items deferred from this Phase A.7 ship and tracked above in the per-todo body annotation:

- ARCHITECTURE.md "live-mode CLI invocation matrix" table — DEFERRED to Phase B.1's first trigger-handler ship.
  Justification: doc is busy + foreign-agent touch-risk; matrix needs stable Phase A.6 UAC enum + Phase B.1+ dispatcher
  inputs.
- UAC closed-set trigger enum — separate todo (Phase A.6); flag is free-form string until that lands.
- Actual trigger handlers — explicitly out-of-scope per spawn prompt, deferred to Phase B.1 / C / D / E.

## DONE-2026-05-09 — Phase A.9 + A.10 (instruments-preflight-gate-tab F0)

Master gate sub-agent F0 shipped the UAC SSOT + UTL runtime helper that unblock Tab F2 (cefi-available-at-stamping-tab)
and every downstream Phase B/C/D/E trigger handler. Both ride the live=batch invariant — same module, same call
signature, both modes.

Code commits:

- `unified-api-contracts@8f89ec4` — `instruments_preflight_dag.py` 554L module body (PreflightTrigger enum × 9 members,
  INSTRUMENTS_PREFLIGHT_REQUIREMENTS DAG, PreflightRequirement, PreflightOK / PreflightFailed / PreflightResult,
  ManifestReader Protocol, get_preflight_requirements, get_trigger_definition, validate_preflight_for_trigger). Foot-gun
  #1: semver-rollout[bot] swept the file body into its commit during parallel-agent staging; content correct,
  attribution mixed.
- `unified-api-contracts@a07711d` — `canonical/crosscutting/__init__.py` facade re-exports (11 symbols) +
  `tests/unit/test_instruments_preflight_dag.py` (22 unit tests, all green: trigger taxonomy / DAG-shape integrity /
  per-asset-group dependency-rule shape / validator success / failure / aggregation / static-SSOT short-circuit /
  naive-datetime coercion / frozen-dataclass invariant).
- `unified-trading-library@db0f4364` — `unified_trading_library/instruments_preflight/{__init__.py, runner.py}`
  (UTLManifestReader, run_preflight, PreflightFailedError) + `tests/unit/test_instruments_preflight.py` (13 unit tests,
  all green: 3 success / 4 failure with event-emission / OK-no-emission / arg-validation / 5 UTLManifestReader paths).

Plan flips:

- A.9: `- [ ]` → `- [x]` with UAC@8f89ec4 + UAC@a07711d evidence (this plan, Phase A § a9 entry).
- A.10: `- [ ]` → `- [x]` with UTL@db0f4364 evidence (this plan, Phase A § a10 entry).

Codex doc:

- `/codex/04-architecture/instruments-preflight-chain.md` — shipped by parallel agent (~same scope, different
  narrative). Left intact per "Two teammates × multiple parallel agents — don't edit unfamiliar files" rule. My drafted
  version was discarded once parallel agent's file detected.

Full-execution criterion (per CLAUDE.md "Plans Run To Actual Completion" HARD RULE):

- ✅ In-process invocation of `run_preflight` against ALL 9 PreflightTriggers with a fresh in-memory ManifestReader seed
  → 9/9 returned `PreflightOK`. No mocked CI smoke; real Python invocation through the full call stack (UTL helper → UAC
  validator → UAC DAG SSOT → PreflightOK construction).
  - **What ran**: in-line Python smoke at the workstation invoking `run_preflight` for every `PreflightTrigger` enum
    member with `manifest_reader=_SmokeReader(seed)`, `now=datetime.now(timezone.utc)`, `today=date.today()`. Duration
    <100ms.
  - **Verification**: stdout output `9/9 triggers preflight OK against fresh manifest seed.` All 9 triggers enumerated
    and PASSED.
- ✅ All 35 unit tests across UAC + UTL pass locally (22 UAC + 13 UTL).

Handoff to Tab F2:

- F2 (cefi-available-at-stamping-tab) was queued as 🟡 BLOCKED on the UTL helper from A.10. Helper now ships at
  `unified_trading_library/instruments_preflight/{__init__.py, runner.py}`. Import surface for F2:

  ```python
  from unified_trading_library.instruments_preflight import (
      run_preflight,
      PreflightFailedError,
      UTLManifestReader,
  )
  ```

  Ping posted to `ikenna_orchestrator/_agent_pings.md` announcing UNBLOCK.

Pending follow-ups (NOT shipped this session, captured as plan items elsewhere):

- A.5 codex audit — A.5 events SSOT + Phase A.4 alerting taxonomy already shipped per upstream. No edits needed this
  session.
- A.11 upstream-staleness monitor — separate todo (P1); reuses `validate_preflight_for_trigger` + UTLManifestReader.
- Phase B.1+ trigger handlers wire `run_preflight` as the gating preflight call before source fetch (pre-existing
  todos).

## DONE-2026-05-09 — sports-fixtures-repoll-tab (Tab F4)

Tab F4 of `plans/active/work_split_2026_05_08_ikenna.md` shipped two scope items. Code commits:

- `unified-trading-library@1f115bc6` — A.8 live-mode `available_at` confirmation (4 unit tests, all green).
- `unified-trading-pm@7496a8a9` — A.8 plan-flip + provenance citation.
- `instruments-service@c53ec64` — B.1 `sports.fixtures.daily_repoll` trigger handler + 8 unit tests.

Full-execution verification (per "Plans Run To Actual Completion" HARD RULE):

- A.8 — 4 unit tests pass under `pytest tests/unit/test_manifest_writer_live_mode_available_at.py`. No new functionality
  required (existing `assert_available_at_present` gate at `unified_trading_library/manifest_writer.py:2153` already
  enforces presence under live invocation).
- B.1 — trigger ran end-to-end against live api-football API + real GCS write 2026-05-08 23:22 UTC for
  `today=2026-05-09 league=BRASILEIRAO lookahead_days=0 VM_NAME=tab-f4-laptop-2026-05-09 MANIFEST_PER_VM_SHARDS=true`.
  Result: `{"2026-05-09/BRAZIL_SERIE_A": 2}`. On-disk parquet at
  `gs://instruments-store-sports-central-element-323112/sports_reference/by_date/day=2026-05-09/entity=fixtures/league=BRAZIL_SERIE_A/fixtures.parquet`
  contains 2 rows with `available_at` populated and `kickoff_utc - 7d` semantics verified (e.g. Coritiba vs
  Internacional kickoff `2026-05-09T19:00:00+00:00` → `available_at = 2026-05-02 19:00:00+00:00`). Manifest per-VM shard
  row at `_index/per_vm/tab-f4-laptop-2026-05-09.parquet`: `capture_status=captured`, `data_type=FIXTURES`,
  `league_id=BRAZIL_SERIE_A`, `instrument_count=2`.

## Assigned active plans

_18 active plans declare `parent_epic: instruments_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`. Regenerated 2026-08-19 via
`/plan-reconcile instruments_master` — the prior roster (`last_updated: 2026-07-14`) had gone stale: it still listed 2
plans since archived (`mvp_scope_catalogue_tagging_2026_06_08`,
`defi_expected_unattempted_backlog_1m_2026_07_03_finalize_2026_08_08`) as if active, and was missing 3 plans that now
declare this epic (`mvp_could_exist_rollup_dual_scope_2026_08_12`,
`tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16` + its finalize)._

## P0 — must complete before next foundation gate

### [`instruments_cefi_g1_g5_gate_execution_2026_07_24`](../active/instruments_cefi_g1_g5_gate_execution_2026_07_24.md)

**status**: active · **estimate**: 6 cal AI-days (class: design) **title**: Instruments Foundation — cefi G1→G5 gate
execution

### [`instruments_completion_tracker_2026_07_06`](../active/instruments_completion_tracker_2026_07_06.md)

**status**: active · **estimate**: 1 cal AI-days (class: infra) **title**: Instruments Completion Tracker — denominator
→ numerator (cefi-first, operator-driven)

### [`instruments_foundation_completeness_2026_06_24`](../active/instruments_foundation_completeness_2026_06_24.md)

**status**: active · **estimate**: 3 cal AI-days (class: design) **title**: Instruments Foundation & Catalogue
Completeness — gated rebuild, every asset group

### [`instruments_foundation_phase0_cross_cutting_2026_07_24`](../active/instruments_foundation_phase0_cross_cutting_2026_07_24.md)

**status**: active · **estimate**: 5 cal AI-days (class: design)

### [`instruments_tradfi_g1_g5_gate_execution_2026_07_24`](../active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md)

**status**: active · **estimate**: 5 cal AI-days (class: design) **title**: Instruments Foundation — tradfi G1→G5 gate
execution

### [`mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24`](../active/mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md)

**status**: active · **estimate**: 2.4 cal AI-days (class: infra) **title**: MTDS venue onboarding + ops-hardening
residuals

### [`prediction_capture_incident_remediation_2026_07_06`](../active/prediction_capture_incident_remediation_2026_07_06.md)

**status**: active · **estimate**: 3.2 cal AI-days (class: infra)

## P1 — important; post-current-gate

### [`instruments_mtds_consistency_remediation_residuals_2026_07_24`](../active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md)

**status**: active · **estimate**: 1.6 cal AI-days (class: infra) **title**: Instruments <-> MTDS F1-N9 consistency
remediation -- residual continuation

### [`instruments_store_cf_canonicalization_single_walk_2026_07_24`](../active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md)

**status**: active · **estimate**: 2.4 cal AI-days (class: infra) **title**: Instruments-store CF canonicalisation —
inherited single-walk lineage

### [`mvp_could_exist_rollup_dual_scope_2026_08_12`](../active/mvp_could_exist_rollup_dual_scope_2026_08_12.md)

**status**: active · **estimate**: 3.0 cal AI-days (class: design)

## P2 — useful; opportunistic

### [`canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08`](../active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md)

**status**: active · **estimate**: 0.8 cal AI-days (class: refactor)

### [`instruments_mtds_consistency_remediation_residuals_2026_07_24_finalize`](../active/instruments_mtds_consistency_remediation_residuals_2026_07_24_finalize.md)

**status**: active · **estimate**: 0.1 cal AI-days (class: refactor) **title**: Instruments <-> MTDS F1-N9 consistency
remediation residuals — finalize

### [`tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24`](../active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md)

**status**: active · **estimate**: 0.24 cal AI-days (class: infra) **title**: TradFi legacy-twin bucket deletes — Ikenna
sign-off gate

### [`tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16`](../active/tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md)

**status**: active · **estimate**: 1.6 cal AI-days (class: infra) **title**: TradFi residual catalogue-leg purge
extension + twin-delete lookup-bug fix

### [`tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16_finalize`](../active/tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16_finalize.md)

**status**: active · **estimate**: 0.15 cal AI-days (class: infra) **title**: Finalize — TradFi purge extension +
twin-delete lookup-bug fix

### [`tradfi_satellite_ao_dispatch_batch9_2026_08_09`](../active/tradfi_satellite_ao_dispatch_batch9_2026_08_09.md)

**status**: active · **estimate**: 0.96 cal AI-days (class: infra)

### [`tradfi_satellite_ao_dispatch_batch9_2026_08_09_finalize`](../active/tradfi_satellite_ao_dispatch_batch9_2026_08_09_finalize.md)

**status**: active · **estimate**: 0.32 cal AI-days (class: infra) **title**: TradFi satellite AO batch 9 — finalize
(reconcile 2 source docs + archive)

## P3 — backlog; revisit quarterly

### [`instrument_record_schema_completeness_extra_forbid_2026_07_18`](../active/instrument_record_schema_completeness_extra_forbid_2026_07_18.md)

**status**: active · **estimate**: 1.0 cal AI-days (class: refactor) **title**: InstrumentRecord schema-completeness +
extra='forbid' — stop silently dropping adapter kwargs

## Archived plans

### [`instruments_backfill_phase3_2026_05_22`](../archive/2026_05/instruments_backfill_phase3_2026_05_22.md)

**status**: ✅ ARCHIVED 2026-05-23 — 22 items shipped (CeFi/DeFi/TradFi/Pred backfills + catalogue builds); 3 items
DEFERRED-OPERATOR-DECISION. · **estimate**: 1.6 cal AI-days (class: infra)

**Deferred (MIGRATED FROM archived plan)** — post-cutover backlog:

- **IS-3.1.Sports-V verification (P0, DEFERRED-OPERATOR-DECISION)**: Gate: `instr-backfill-sports` completes; track in
  `predictions_master`.
- **IS-3.1.TradFi-Databento (P0, BLOCKED-CREDENTIALS)**: Gate: operator reactivates Databento account.
- **IS-3.1.Pred-Kalshi (P0, BLOCKED-CREDENTIALS)**: Kalshi account registration + API key required to backfill Kalshi
  prediction markets. Polymarket writes OK; Kalshi adapter dormant until credentials land. (**MIGRATED FROM:**
  `instruments_backfill_phase3_2026_05_22`)
- **IS bucket canonicalisation (P2)**: Migrated to: `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 2.6.

## Folded-in scope 2026-07-15 (plan-reconcile §6)

- [ ] [BACKEND] P3. Post-phase codex audit — check whether `/codex/02-data/defi-canonical-naming-ssot.md` or
      `/codex/04-architecture/instrument-universe-registry-consolidation.md` document the (now-corrected) glued_pair_id
      polarity or canonical_instrument_id's CeFi/DeFi scope; update/SUPERSEDED-banner if they assert the old (wrong)
      state. (FOLDED IN from canonical_instrument_id_cefi_defi_backfill_2026_07_14, 2026-07-15, plan-reconcile §6
      operator ruling)
