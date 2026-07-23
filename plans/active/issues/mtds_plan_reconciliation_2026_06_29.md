---
doc_type: issue
title: MTDS Plan Reconciliation — open plans vs SSOT (UAC + MTDS code + 3 new plans + fresh codex)
summary:
  "Find-first reconciliation for market-tick-data-service (MTDS), the service after instruments-service. Score every
  open plan that touches MTDS against the SSOT (live UAC + market-tick-data-service code + fresh codex + the 3 new
  plans) to surface task-item CONTRADICTIONS for a later alignment pass. Read-only: finds + classifies, does NOT edit
  subject plans. Companion to instruments_service_plan_reconciliation_2026_06_29.md. Section A = the MTDS assertion
  ledger (M-series). Section B = triage. Section C = deep-read findings. Section D = synthesis + resolutions."
status: open
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service, unified-api-contracts]
scope: [admin]
tags: [reconciliation, ssot-audit, plan-hygiene, mtds, market-data, pipeline-mode, honest-coverage, shard-isolation]
related:
  [
    /plans/active/issues/instruments_service_plan_reconciliation_2026_06_29.md,
    ../honest_coverage_v2_instrument_denominator_2026_06_28.md,
    ../honest_coverage_v2_opus_checkpoints_2026_06_28.md,
    /codex/02-data/pipeline-mode-partition.md,
    /codex/02-data/live-data-persistence-and-event-log.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
  ]
created: 2026-06-29
parent_epic: mtds_mdps_master
priority: P1
source: [operator request 2026-06-29]
assigned_vm: NA
resolved_by:
locked_by: live-defi-rollout
last_updated: 2026-06-29
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_since: 2026-05-21
---

# MTDS Plan Reconciliation (2026-06-29)

> **Read-only FIND pass.** Companion to the instruments-service reconciliation. Same trust model: **no plan is SSOT;
> SSOT = live UAC + market-tick-data-service code + fresh codex.** A plan item is a contradiction wherever it misaligns
> with that truth; no date-based trust exemption. `last_updated` is junk (bulk-stamped) — use `created` for ordering
> only. The 3 new plans + the honest-coverage-v2 pair are the aligned reference, not a privileged tier.

## Codex freshness (git last-modified) — MTDS-relevant docs

| Codex doc                                                 | git date   | verdict                                                         |
| --------------------------------------------------------- | ---------- | --------------------------------------------------------------- |
| `02-data/honest-coverage-model.md`                        | 2026-06-29 | ✅ FRESH (Tier-1 v2 model)                                      |
| `02-data/availability-manifest-and-data-status.md`        | 2026-06-27 | ✅ fresh                                                        |
| `02-data/tradfi-databento-sourcing-ssot.md`               | 2026-06-27 | ✅ fresh (one deploy-gated caveat — M30.4)                      |
| `02-data/live-data-persistence-and-event-log.md`          | 2026-06-26 | ✅ fresh                                                        |
| `02-data/pipeline-mode-partition.md`                      | 2026-06-25 | 🟡 fresh-ish; Phase-8 reader-fallback removal past date (M30.3) |
| `06-coding-standards/config-reloader-pattern.md`          | 2026-06-25 | ✅ fresh-ish                                                    |
| `04-architecture/tier-and-import-architecture.md`         | 2026-06-25 | ✅ fresh-ish                                                    |
| `04-architecture/instruments-service-as-ssot-for-mtds.md` | 2026-06-16 | 🟡 core contract OK; "current-state" stale (M30.1)              |
| `04-architecture/shard-level-failure-isolation.md`        | 2026-05-17 | 🟡 rule OK; classify-call signature stale (M30.2)               |

---

## Section A — MTDS SSOT assertion ledger (the yardstick)

`LANDED` = shipped ground truth (contradiction = now-conflict); `IN-FLIGHT` = target end-state (contradiction =
alignment-needed). Citations verified against live `market-tick-data-service` + UAC code by the contract-extraction
pass.

### Domain 1 — IS-owns-universe / MTDS-is-market-data-only

- **M1 `LANDED`** — MTDS must NOT hardcode venue URLs, universe lists, or coverage windows in handlers; all derived at
  runtime from the IS catalogue (`InstrumentRecord.source_archive_url_template` / `source_record_types` /
  `source_coverage_start/end`). 3 QG gates enforce (`no_hardcoded_venue_urls/universe/silent_absence`,
  quality-gates.sh:144-155). **Conflicts:** plans adding hardcoded venue URLs/universe/windows to MTDS, or treating MTDS
  as the universe owner.
- **M2 `LANDED`** — on missing IS data for a (venue,date) with no `--instrument-ids`, MTDS honest-skips (records
  `skipped_shards`) by DEFAULT; `MTDS_ALLOW_HARDCODED_UNIVERSE_FALLBACK=true` is an opt-in for batch bootstrap ONLY
  (venue_fetch.py:415-441, service_config.py:187-196). **Conflicts:** plans making the hardcoded fallback the default.
- **M3 `LANDED`** — MTDS must NOT `import instruments_service`; IS data via UAC helpers (`list_instruments`,
  `load_pool_metadata_for_date`, `get_solana_protocol_url`) or GCS reads, never service↔service Python import.
  **Conflicts:** plans wiring a direct IS package import.
- **M4 `LANDED`** — every handler/`collect_*`/`backfill_*` emits exactly one manifest call per shard outcome
  (`record_captured` / `record_empty(reason)` / `record_failed(error)` / `record_expected_unattempted`); silent returns
  banned (QG `no_silent_absence_handlers.sh`). **Conflicts:** plans introducing a silent-return / no-manifest path.

### Domain 2 — pipeline_mode / source partition

- **M5 `LANDED`** — every MTDS parquet carries a `pipeline_mode` hive partition `{mode}_{source}[_{transport}]`
  (`mode ∈ {batch,live,replay}`, `source`=VENDOR), LEFT of `asset_group=` (pipeline-mode-partition.md;
  manifest_finalize.py:348-349). **Conflicts:** plans writing mode-only `pipeline_mode` or omitting source from the key.
- **M6 `LANDED`** — `source` (v9) is write-stamped by the FETCHING adapter's vendor, NEVER `SOURCE_PRIORITY[0]` at
  write; TradFi OHLCV CLI requires explicit `--source databento|massive` (manifest_finalize.py:288-290,348-349).
  **Conflicts:** plans deriving write-time `source` from `SOURCE_PRIORITY[0]`, or tradfi writes without `--source`.
- **M7 `IN-FLIGHT`** — live writer uses the transitional `live_websocket` alias until the gated `M1-BREAKING` tranche
  renames to `live_<source>`; readers PREFIX-match `batch_*/live_*/replay_*` (pipeline-mode-partition.md § M1 GATED).
  **Alignment-needed:** plans assuming `live_<source>` is already live, or readers exact-matching coarse literals.
- **M8 `LANDED`** — no new `pipeline_mode` without a matching UAC `SOURCE_PRIORITY` entry (round-trip enforced by UAC
  `test_pipeline_mode.py`; closed-set `PipelineMode` StrEnum). **Conflicts:** plans inventing a free-text pipeline_mode.

### Domain 3 — shard-level failure isolation

- **M9 `LANDED`** — a failed shard must NOT kill others: per-shard loop catches all, classifies, `record_failed` (no
  silent swallow), logs with shard-atom fields, continues. `raise` inside a per-shard loop is banned
  (shard-level-failure-isolation.md; venue_fetch.py:572-575). **Conflicts:** plans adding a `raise`/fail-fast in a
  per-shard loop.
- **M10 `LANDED`** — opaque `VENUE_FETCH_FAILED` is RETIRED; unknown errors → `classify_venue_error()`, else
  `f"UNCLASSIFIED:{code_token}"` (sentinels.py:267-269,639-641,717-720). **Conflicts:** plans treating
  `VENUE_FETCH_FAILED` as the live model.
- **M11 `LANDED`** — per-VM batch clusters set `VM_NAME=<unique>` + `MANIFEST_PER_VM_SHARDS=true` (UTL raises
  `MultiWorkerWithoutShardIsolationError` otherwise; QG STEP 5.66). **Conflicts:** plans launching multi-worker
  backfills without per-VM shard isolation.

### Domain 4 — live = batch event-log spine

- **M12 `LANDED`** — MTDS publishes live ticks via the UTL `EventTransport` facade (`event_facade`) wrapping
  `CanonicalPersistEnvelope`; `InMemoryTransport` (paper) / `PubSubTransport` (live) → `paper(W)==batch-rerun(W)` ε=0
  (live-data-persistence-and-event-log.md; event_facade_sink.py:18-90). **Conflicts:** plans adding a live-only
  persistence path bypassing the facade.
- **M13 `LANDED`** — MTDS must NOT write live ticks directly to GCS on the hot path; facade → Pub/Sub → warm GCS via
  Cloud-Storage subscription (live/**init**.py:17; websocket_runner.py:48). **Conflicts:** plans reintroducing direct
  hot-path GCS writes.
- **M14 `LANDED`** — `SINK_MATRIX` governs all 52 `(asset_group,data_type)` shards; `sinks_for()` raises `KeyError` on
  unknown (no silent default); all market-data shards `REPRODUCIBLE`. **Conflicts:** plans adding a shard without a
  SINK_MATRIX entry or assuming a silent default.

### Domain 5 — writer-side honest-coverage contracts (shared with the IS/honest-coverage-v2 audit)

- **M15 `LANDED`** — `instrument_type` normalized to canonical **lowercase** at write (`PartitionedTickWriter`
  `.str.lower()`, partitioned_writer.py:255-258; derives from venue/symbol when absent). **Conflicts:** plans assuming
  uppercase/blank instrument_type.
- **M16 `LANDED`** — `empty_confirmed` carries a typed UAC `EmptyConfirmedReason`; `SOURCE_RETURNED_ZERO` requires a
  `FetchEvidence` proof (`UnprovenHonestAbsenceError` otherwise) (sentinels.py:493-498,746-769). **Conflicts:** plans
  emitting blank-reason empties / unproven zero.
- **M17 `LANDED`** — `pipeline_mode` + `source` stamped on EVERY captured row via
  `_resolve_pipeline_mode_for_sentinel(venue,dt,source=_run_source)` (manifest_finalize.py:325-370). (= M5/M6 at row
  grain.)
- **M18 `LANDED`** — 4-state `capture_status` is canonical; `attempted_failed` needs a typed reason;
  `expected_unattempted` is WRITER-materialised (MTDS pre-flight + IS enumerator), never re-derived downstream.
  **Conflicts:** plans re-deriving `expected_unattempted` in a consumer, or adding a 5th state.
- **M19 `LANDED`** — per cefi/defi/tradfi, `empty_confirmed` is legitimate only at VENUE level
  (holiday/weekend/pre-genesis); per-instrument-day `empty_confirmed` indicates a writer bug. **Conflicts:** plans
  treating per-instrument-day empties as normal.
- **M20 `LANDED`** — 4-pillar write-gate on `record_captured` (rows>0 · NaN<thresh · schema matches UAC ·
  cluster-coverage≥expected for bundles); failures route to `record_failed`, no partial parquets land
  (manifest_finalize.py:166-265). **Conflicts:** plans landing partial/ungated parquets.

### Domain 6 — Databento / TradFi sourcing

- **M21 `LANDED`** — exactly 3 Databento datasets (`GLBX.MDP3` CME / `DBEQ.BASIC` US-equities / `XCBF.PITCH` CFE-VX);
  all requests via `assert_databento_request_allowed(...)` (off-allowlist → `DatabentoDatasetNotAllowedError`);
  `batch.submit_job` hard-blocked. **Conflicts:** plans adding a 4th Databento dataset or a batch.submit_job path.
- **M22 `LANDED`** — Barchart as a LIVE source is RETIRED; VIX 15m is a one-time GCS preload, no live Barchart adapter
  (tradfi/**init**.py:11-13). **Conflicts:** plans wiring a live Barchart adapter.
- **M23 `LANDED`** — TradFi `SOURCE_PRIORITY` is databento-first (`[databento, massive]`; `ohlcv_1s` databento-only);
  KRX + ICE(DXY) are Yahoo Finance, NOT Databento, NOT operator-blocked. **Conflicts:** plans making massive primary, or
  routing KRX/ICE through Databento.
- **M24 `LANDED`** — CME OHLCV from `GLBX.MDP3` uses `stype_out=instrument_id` (not raw_symbol) with `stype_in=parent`,
  paginates `symbology.resolve` in 2000s, classifies space-containing CME short options. **Conflicts:** plans using
  raw_symbol or unpaginated resolve.

### Domain 7 — service infra + tier/import

- **M25 `LANDED`** — MTDS instantiates UTL `ServiceBootstrap` (STARTED/STOPPED/FAILED; QG 5.61; cli/main.py:19,530).
- **M26 `LANDED`** — MTDS HTTP API wires `make_health_router` + `data_freshness` callback (QG 5.62; api/main.py:25,107).
- **M27 `LANDED`** — MTDS uses `ApiKeyReloader` (sync initial fetch, daemon refresh), not a frozen key dict
  (tick_data_handler.py:30,71,139). **Conflicts (M25-M27):** plans bypassing
  ServiceBootstrap/health-router/ApiKeyReloader.
- **M28 `LANDED`** — MTDS must NOT import another service repo (T4→T4 banned); depends only on
  UTL/UAC/`unified-*-interface`. Known tracked violation: UMI(T2)→UDC(T3) `cohesion-umi-udc-dep-violation`.
  **Conflicts:** plans adding a service↔service import.
- **M29 `LANDED`** — domain schema types from `unified_api_contracts.{domain}` / `.internal`; local equivalents banned
  (event_facade_sink.py:14-17; sentinels.py:12-19). **Conflicts:** plans defining local manifest/event/config
  dataclasses.

### Domain 8 — stale-source flags (codex docs that are the stale side)

- **M30.1** — `instruments-service-as-ssot-for-mtds.md` (06-16): core IS→MTDS contract ACCURATE, but its "current state"
  (writers "0% of 7.4M rows at v8", mid-v8-migration) is STALE — manifest is now v9. Plans leaning on its state numbers
  cite stale.
- **M30.2** — `shard-level-failure-isolation.md` (05-17): no-raise rule + classify-or-UNCLASSIFIED intent CORRECT, but
  the `classify_venue_error(e)` call-signature illustration is stale (live = venue-aware token-based + `UNCLASSIFIED:`
  fallback).
- **M30.3** ⚖️ — `pipeline-mode-partition.md` Phase-8 (reader legacy-fallback removal) target 2026-06-15 has PASSED
  (today 06-29); gated on `READER_FELL_BACK_TO_LEGACY_PATH`=0/7d, `last_executed: NEVER`. **Operator-attention.**
- **M30.4** ⚖️ — `tradfi-databento-sourcing-ssot.md`: the `live_massive` source-stamp fix is code-landed (UAC@1205ae44)
  but DEPLOY-gated (tarball rebuild); live rows written pre-rebuild are still mis-stamped `live_massive`.
  **Operator-attention.**

---

## Section B — Triage (MTDS-specific contested-token signal across 74 plans)

Signal = grep across 7 token-groups (venue-universe · pipeline_mode · shard · event-spine · writer · databento · infra).
~37 MTDS-material plans deep-read across 15 cluster-agents (M-C1…M-C15). Domain-5 honest-coverage findings that already
appear in the IS audit are cross-referenced, not duplicated; MTDS focus = Domains 1-4, 6-7.

| Cluster | Plans                                                                                                                                  |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| M-C1    | cefi_manifest_canonicalisation · tradfi_manifest_canonicalisation                                                                      |
| M-C2    | defi_manifest_canonicalisation · prediction_manifest_canonicalisation                                                                  |
| M-C3    | sports_manifest_canonicalisation · downstream_services_manifest_canonicalisation                                                       |
| M-C4    | master_data_canonicalisation_migration_catalogue                                                                                       |
| M-C5    | pipeline_mode_source_batch_live_replay_standardisation · bucket_name_ssot_legacy_dual_write_remediation                                |
| M-C6    | data_completion_to_100_all_ag · path_to_100pct_backfill_mtds_is · data_pipeline_hardening_self_monitoring                              |
| M-C7    | instruments_mtds_subset_consistency_remediation · instruments_foundation_completeness · migration_verif_orphan                         |
| M-C8    | data_source_provenance_all_asset_groups · tradfi_massive_dual_source · tradfi_multisource_backfill                                     |
| M-C9    | mvp_backfill_tradfi_ohlcv1m_v10 · tradfi_cme_event_contract_backfill · cryptovenue_equity_perps_and_tokenized                          |
| M-C10   | citadel_paper_batch_live_reconciliation · features_service_e2e_pipeline_test · sports_p2_features_history_to_ml                        |
| M-C11   | prediction_venue_perps_and_live_clob_depth · carry_staked_basis_funding_scan_experiment                                                |
| M-C12   | solana_defi_legacy_migration · master_to_live_defi · v2_engine_venue_buildout                                                          |
| M-C13   | cross_ag_shard_4pillar_validation_harness · macro_econ_adapter_scaffolds · tradfi_mdps_passthrough_dependency                          |
| M-C14   | sports_p1_golden_window_mtds_odds · honest_coverage_smoke_harness · audit_criteria_automation · bar_edge_l_v_r                         |
| M-C15   | data_feed_sla_registry · monitoring_control_plane_master · data_status_tab_downloads · unified_deploy_health · mtds_file_size_refactor |

**Set aside (low/zero MTDS-specific signal — honest-coverage-only overlaps already scored in the IS audit, or
CI/gov/org):** the v10 MVP plans (mvp*backfill_defi_onchain / cefi_tick / mvp_catalogue_finalization /
mvp_reconciliation_closeout — their MTDS signal is writer-side honest-coverage, covered by the IS audit's D-clusters),
capability_wizard, the sports P1/P2 family (A4-clean), defi_onchain_derivable_values, tradfi_sp500_ml,
predictions_other_bucket, sports_odds_bookmaker_coverage_enumeration, + cicd/scripts/governance/org plans (cicd*_,
repo*scripts_governance, scripts_lifecycle_marker_rollout, org_migration, codex*_, work_split, harsh_day_master,
test_fleet_image_builds).

## Section C — Deep-read findings (15 cluster-agents, 41 plans)

**Tally: 0 MAJOR-CONFLICT · 0 SUPERSEDED · 26 MINOR-DRIFT · 15 ALIGNED.** Markedly cleaner than the IS audit — the
MTDS-specific axes (pipeline_mode/source, shard isolation, event spine) are mature and the writer-side migrations
already shipped. No plan instructs an action that contradicts a LANDED M# on an open item with material risk. All
findings are MED-or-below and sit inside MINOR-DRIFT plans. `*` = open `[ ]` item.

### Plans carrying a MED finding (watch-items, no MAJOR)

| Plan                                               | MED finding                                                                                                                                                                                                                                                               |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `instruments_foundation_completeness`              | **M4/M1\*** EXTENDED cefi adapter falls back to a HARDCODED market list on fetch-failure → records `captured` (stale) not `record_failed` — the "false-complete" pattern (open P1, IS-side adapter, self-diagnosed).                                                      |
| `tradfi_massive_dual_source`                       | **M22** Operator-decision #3 (L53) + L180 still list **Barchart** in the `ohlcv_15m` SOURCE_PRIORITY — Barchart was RETIRED 2026-06-24 (VIX 15m now via Databento XCBF.PITCH). Stale-premise on a removed source.                                                         |
| `prediction_venue_perps_and_live_clob_depth`       | **M12/M13** interim deviation — live book_snapshot_5 reverts to a direct-GCS `LiveWebsocketTickSink`; the facade→Pub/Sub→warm-GCS path is **BLOCKED-CREDENTIALS** (documented). Plus M14 — verify SINK_MATRIX entries exist for the new cefi perp `book_snapshot` shards. |
| `carry_staked_basis_funding_scan_experiment`       | **M4/M14\*** `perp_daily_ctx` is a research-grade, **manifest-invisible** data_type written to GCS — must canonicalize to `derivative_ticker` + register before any production pipeline consumes it (self-flagged).                                                       |
| `master_data_canonicalisation_migration_catalogue` | **M21** R5 smoke ledger probed **`XNAS.ITCH`** as a Databento dataset alongside the allowlisted `GLBX.MDP3`/`DBEQ.BASIC` — verify `assert_databento_request_allowed` blocked it or it's a probe mislabel (US-equities → `DBEQ.BASIC`).                                    |
| `bucket_name_ssot_legacy_dual_write_remediation`   | **M1\*** open+DEFERRED fix for env-LESS instruments-store readers in the MTDS orchestrator (`engine/orchestrator/__init__.py:445-451`, `_instruments_metadata.py`) — risks silently reading the non-prd IS index. Don't strand.                                           |
| `path_to_100pct_backfill_mtds_is`                  | **M10\*** open re-fetch task names the retired `VENUE_FETCH_FAILED` label (relabel, not a new emission — see IS audit). **M16\*** pre-gate DeFi `[~]` continuation VMs must run on a post-`fbac3a9` tarball so `SOURCE_RETURNED_ZERO` carries FetchEvidence.              |
| `instruments_mtds_subset_consistency_remediation`  | **M16\*** `_af_record_empty(reason='')` blank-reason at IS orchestrator:4271 needs a typed `EmptyConfirmedReason` (open P2). (Its `_CEFI_VENUES` dedup item is correctly IS-side here, not an MTDS M1 hit.)                                                               |
| `tradfi_mdps_passthrough_dependency_gap`           | **M28** (MDPS-scoped) verify the new passthrough adapter imports only UAC/UTL types, not `market_tick_data_service.*`.                                                                                                                                                    |
| `mtds_file_size_refactor`                          | **M9/M13/M25** execution-risk: the behavior-preserving split of `live/websocket_runner.py` must keep facade+ServiceBootstrap; `engine/orchestrator.py` split must not reintroduce a `raise` at shard grain. (status=deferred.)                                            |

### MINOR-DRIFT (low only)

`tradfi_manifest_canonicalisation` (M5 table omits `batch_eia`) · `defi_manifest_canonicalisation` (self-annotated
superseded `pipeline_mode=batch` refs) · `prediction_manifest_canonicalisation` (deep-import QG hygiene, not an M28
boundary) · `pipeline_mode_source_batch_live_replay_standardisation` (stale work-unit checkboxes vs shipped progress log
— flip them) · `data_completion_to_100_all_ag` (M10 legacy label; M7 progress-log refs) · `cryptovenue_equity_perps`
(M23 progress-log order; KRX backfill should pass explicit `--source yahoo`) · `data_source_provenance_all_asset_groups`
(Overview self-corrected; shared consolidator todo) · `tradfi_multisource_backfill` (M21 ICE re-add phrasing) ·
`features_service_e2e_pipeline_test` (v8-only assertion stale vs v9) · `solana_defi_legacy_migration` (`dex_pools` vs
`dex_pool_state` body labels below a correction banner) · `v2_engine_venue_buildout` (`live_deribit` ahead of M7 gate) ·
`macro_econ_adapter_scaffolds` (verify `ADAPTER_FETCH_FAILED` distinct from retired `VENUE_FETCH_FAILED`) ·
`monitoring_control_plane_master` · `unified_deployment_health_cockpit` · `honest_coverage_smoke_harness` ·
`audit_criteria_automation`.

### ALIGNED (15)

`cefi_manifest_canonicalisation` · `sports_manifest_canonicalisation` · `downstream_services_manifest_canonicalisation`
(1 tracked E5/M16 watch-item, verdict ALIGNED) · `data_pipeline_hardening_self_monitoring` ·
`migration_verification_orphan_safety` · `mvp_backfill_tradfi_ohlcv1m_v10` · `tradfi_cme_event_contract_backfill` ·
`citadel_paper_batch_live_reconciliation` (its ε=0 paper==batch contract IS the M12 end-state) ·
`sports_p2_features_history_to_ml_ready` · `master_to_live_defi` · `cross_ag_shard_4pillar_validation_harness` ·
`sports_p1_golden_window_mtds_odds` · `bar_edge_left_vs_right_remediation` ·
`data_feed_sla_registry_and_active_self_healing` · `data_status_tab_and_downloads_remediation`.

## Section D — Synthesis: cross-plan clusters + proposed resolutions

⚖️ = operator decision; 🔧 = mechanical. Findings collapse into 10 clusters (MD1–MD10).

### MD1 ⚖️ — The ledger may be stale: M7 is probably LANDED, not IN-FLIGHT (the headline outcome)

Multiple live writers already emit the post-gate `live_<source>` form — `live_kalshi_perp` (`prediction_venue_perps`),
`live_deribit` (`v2_engine_venue_buildout`), `live_odds_api` (`sports_manifest`) — and
`pipeline_mode_source_batch_live_replay_standardisation` reports **M1-BREAKING COMPLETE + `LIVE_WEBSOCKET` deleted
fleet-wide** (`rg live_websocket --type py` = 0). That means the **M7 "IN-FLIGHT / `live_websocket` transitional"
framing in the ledger + codex `pipeline-mode-partition.md`, and the M30.3 "reader legacy-fallback removal NEVER (target
06-15 passed)" flag, are likely the STALE side** — not the plans. **Proposed resolution:** (1) verify the M1-BREAKING
tranche is deployed to all live writers at runtime (not just code), then **flip M7 LANDED** in the codex + this ledger;
(2) execute or formally close the **M30.3** reader-legacy-fallback removal (it's gated on
`READER_FELL_BACK_TO_LEGACY_PATH`=0/7d). This single reconciliation reclassifies ~4 "alignment-needed" plan findings
(perps/deribit/odds/master-catalogue) to aligned.

### MD2 ⚖️ — Databento allowlist hygiene (M21)

`master_data…catalogue` R5 smoke ledger probed `XNAS.ITCH` (not on the 3-dataset allowlist). **Resolution:** verify the
smoke log shows `assert_databento_request_allowed` raised `DatabentoDatasetNotAllowedError` _before_ the network call
(in which case the guard works and it's just a noisy probe label → 🔧 fix the probe to `DBEQ.BASIC`); if it reached the
vendor, that's a real allowlist-bypass to fix. Operator confirm which.

### MD3 🔧 — Barchart-retired stale references (M22)

`tradfi_massive_dual_source` Operator-decision #3 (L53) + L180 + L386 still list Barchart in the `ohlcv_15m`
SOURCE_PRIORITY / valid-source set. → update to `[databento, massive, yahoo]`; VIX 15m is Databento XCBF.PITCH now.

### MD4 ⚖️ — Live-persistence interim deviation from the facade spine (M12/M13)

`prediction_venue_perps` runs live book_snapshot_5 through a **direct-GCS `LiveWebsocketTickSink`** because the
facade→Pub/Sub→warm-GCS subscription is **BLOCKED-CREDENTIALS**. Documented, but it's a standing deviation from the
M12/M13 end-state. **Operator:** provision the Cloud-Storage subscription (un-block credentials) or accept + explicitly
track the interim. Also 🔧 verify SINK_MATRIX has the new cefi perp `book_snapshot` shards (M14) before any live launch.

### MD5 🔧 — Silent-capture / manifest-invisible risks (M4/M14/M16) — all self-tracked, close before trusting the data

`instruments_foundation` EXTENDED hardcoded-fallback→false-`captured` (P1) · `carry` `perp_daily_ctx` manifest-invisible
data_type · `instruments_mtds_subset` blank-reason `_af_record_empty` (P2) · `downstream_services` E5 CF-11 3-way logic
must be canonical before the cefi/tradfi/prediction rebuild scripts run. Each is correctly open in its plan; resolution
= land the fix before that plan's data is treated as honest-coverage ground truth.

### MD6 🔧 — Retired VENUE_FETCH_FAILED label in open re-fetch tasks (M10)

`path_to_100pct` + `data_completion` open CeFi re-fetch tasks name `VENUE_FETCH_FAILED` as the scoping label. It's
legacy-cell _identification_, not a new emission (no M10 writer violation). → relabel to "cells whose legacy
`error_reason` was `VENUE_FETCH_FAILED`". (Same item as IS-audit D4 — fix once, reference from both.)

### MD7 🔧 — Quick verify-asks (M28/M10)

`tradfi_mdps_passthrough` adapter imports UAC/UTL only (not `market_tick_data_service.*`) · `macro_econ_adapter`
`ADAPTER_FETCH_FAILED` is a live distinct sentinel, not an echo of retired `VENUE_FETCH_FAILED` · macro adapter's
deferred write-path wiring must later satisfy M4/M14/M20.

### MD8 🔧 — Plan-hygiene: stale checkboxes & labels (no SSOT conflict)

`pipeline_mode_source_batch_live_replay_standardisation` un-flipped work-unit boxes (shipped per progress log) ·
`solana_defi_legacy_migration` `dex_pools`→`dex_pool_state` body labels · `tradfi_manifest` `batch_eia` table omission ·
`bucket_name_ssot` stale prerequisite list · `audit_criteria_automation` reversed Era-A `options_chain` table row ·
`features_e2e` v8→v9 assertion. → doc-accuracy flips, low priority.

### MD9 🔧 — Shared todo, priority drift (M5/M6)

`data_source_provenance` (P1) and `tradfi_massive_dual_source` (P0) both own the `manifest_consolidator.py`
`_OPTIONAL_DEDUP_COLS` omits-`source` fix. → assign one owner, align to P0.

### MD10 🔧 — mtds_file_size_refactor execution guards (M9/M13/M25)

When the deferred split runs: `live/websocket_runner.py` must preserve the `event_facade_sink` import + ServiceBootstrap
(M13/M25); `engine/orchestrator.py` must keep the per-shard catch/classify/continue intact (no `raise` at shard grain,
M9). → annotate these as hard execution constraints on the refactor todos.

### Headline for the operator (MTDS)

1. **MD1 ⚖️ (most important):** the audit's biggest finding is that **the codex/ledger is likely the stale side on M7 /
   M30.3** — live writers already emit `live_<source>`. Verify M1-BREAKING is deployed → flip M7 to LANDED + close the
   M30.3 reader-fallback removal. This is a codex/ledger update, not a plan fix.
2. **MD2 ⚖️:** confirm the `XNAS.ITCH` Databento probe was guard-blocked (allowlist integrity).
3. **MD4 ⚖️:** un-block the Pub/Sub Cloud-Storage subscription for live book_snapshot_5, or accept the documented
   direct-GCS interim.

Everything else (MD3, MD5–MD10) is mechanical and folds into the alignment pass alongside the IS edits.

## Section E — Pass 2 (adversarial verification + ledger-completeness critique)

Second pass (Opus ledger critic + code-grounded skeptics) tested the find-pass conclusions. Where E conflicts with C/D,
**E wins**. Key caution from the critic: **the "0 MAJOR / cleaner than IS" verdict is partly an artifact of MISSING
ledger axes** — where there's no assertion, there's no contradiction to find. Several ALIGNED plans sit on un-asserted
axes.

### E.1 — Corrections to Section C/D findings (verified vs code)

- **MD1 / M7 — PARTIAL, do NOT flip straight to LANDED.** Code IS migrated (`LIVE_WEBSOCKET` deleted from the
  `PipelineMode` enum, 0 fleet-wide `.py` hits; live writers emit `live_<source>` via `websocket_runner.py:206` →
  `live_pipeline_mode_for_venue`). BUT (a) the **reader legacy-fallback is still live in code** (`reader.py:295-296`
  unconditionally appends non-`pipeline_mode=` bases; M30.3 `last_executed: NEVER`) and (b) **no runtime-redeploy
  evidence** — recent tarball rebuilds were _batch_ VMs, not the live producer, so per M30.4 the running producer may
  still emit `live_massive`. **Corrected resolution:** (1) fix the codex text (code is migrated); (2) rebuild+relaunch
  the live-producer tarball → closes M30.4; (3) sample live manifest rows for `live_<source>`; (4) then execute M30.3
  reader-fallback removal. Restate M7 as "code-landed; runtime+reader pending." The ~4 plans emitting `live_<source>`
  (perps/deribit/odds/master) are **aligned at code level** — the ledger was the contradicting side, not the plans.
- **MD2 (XNAS.ITCH allowlist) — REFUTED, drop from operator list.** Allowlist = frozenset
  `{GLBX.MDP3, DBEQ.BASIC, XCBF.PITCH}`; `assert_databento_request_allowed` raises _first_, before any network call,
  with a unit test on exactly `XNAS.ITCH`. The smoke `XNAS.ITCH` was a noisy probe label (`smoke_matrix.py`), not a
  bypass. At most: clean up the probe.
- **MD3 (Barchart in SOURCE_PRIORITY) — CONFIRMED.** Already removed from `('tradfi','ohlcv_15m')` (now
  `[databento, massive, yahoo]`, retired 2026-06-24) + from capability/latency tables; no live adapter. Plan text stale
  → mechanical fix.
- **MD5 EXTENDED false-complete — REFUTED (as characterized).** The hardcoded `_EXTENDED_FALLBACK_SYMBOLS` is real but
  the adapter never emits `record_captured`; per-symbol failures route to `PerLeafFailureRouter.record()` honestly.
  Residual = one candle-path that logs-debug-without-recording-failure + a documented bootstrap fallback. Downgrade from
  MED. (File ambiguity: verifier checked MTDS `_umi_extended.py`; the IS plan's text pointed at IS
  `adapters/cefi/extended.py`.)
- **MD5 `perp_daily_ctx` manifest-invisible — CONFIRMED.** Backfill writes it via raw `gcsfs`, zero manifest calls;
  absent from `DATA_TYPES_BY_ASSET_GROUP`, `SINK_MATRIX`, all UAC registries. Stands (carry plan's self-flag is
  correct).

### E.2 — M-ledger gaps (WRONG/MISSING)

- **WRONG: M7** → flip to "code-landed; runtime+reader pending" (E.1). **M14** over-states "KeyError on unknown" — there
  is a wildcard `("*", data_type)` fallback for ~30 cross-cutting shards (`sink_matrix.py:156`); KeyError fires only
  when neither exact nor wildcard matches. **M30.3** is SPLIT, not "NEVER": MTDS emission removed, but UTL
  `manifest_reader_fallback.py` chain still exists. **New stale flag M30.5:** `pipeline-mode-partition.md` is the
  _primary_ stale teaching doc — it still teaches `live_websocket` in normative prose (`:84,:124,:167-180`), not just a
  checkbox.
- **MISSING (high-leverage, each a scored-ALIGNED plan sits on it):**
  - **M31** — Bar-boundary RIGHT-edge (`t_close`) write contract; ingesting a vendor OPEN/left edge = look-ahead (QG
    STEP 5.92 `check_bar_edge_open_ingestion.py`). `bar_edge…` was ALIGNED but never scored against an M#.
  - **M32** — Bucket resolution via `resolve_bucket_name(...)`, no inline `gs://`, GCS object ops via UTL helpers (QG
    5.69). The whole `bucket_name_ssot…` cluster was scored against an axis the ledger never stated.
  - **M33** — `BUNDLED_DATA_TYPES` closed-set + cluster-validation grain + registry-seeding
    (`_honest_coverage_clusters.py`). `carry`/perps `perp_daily_ctx` + `book_snapshot` shards live here.
  - **M34** — Cadence axis is ORTHOGONAL to `pipeline_mode` (a manifest column, never a path key).
  - **M35** — `--operation/--mode/--asset-group` 3-axis CLI convention (`--run-mode` is the anti-pattern).
  - **M36** — Consolidator is Cloud Run / Batch-Fargate (not a VM), loud-fails on stale index, `_OPTIONAL_DEDUP_COLS`
    must include `source` (the MD9 bug sits here).
  - **HOLES:** replay mode (`replay_<source>`) absent; transport axis (vendor≠transport, transport always a column);
    reader precedence is mode-CONTEXTUAL (`select_for_mode`), not flat prefix-match; **honest-coverage-v2 two-layer
    model** not reflected (Domain-5 is the v1 writer model; honest-coverage-model.md 06-29 is newer than every M#).

### E.3 — Pass 3: re-score on the new axes (did any plan EXPLOIT the gaps?)

Re-scored the plans sitting on each new M31–M36 / HOLE axis. **3 axes exploited (new findings), the rest latent-clean.**
The critic's caution was right: the "0 MAJOR / cleaner than IS" verdict was partly an artifact of missing axes — pass 3
recovers the findings those axes would have caught.

**EXPLOITED — new contradictions:**

- **M32 (bucket resolution via `resolve_bucket_name`, no inline `gs://`, UTL gcs ops):**
  - `bucket_name_ssot_legacy_dual_write` — **HIGH**: 4 MTDS orchestrator callsites still read the env-LESS (non-prd)
    instruments-store bucket via legacy `get_bucket_name` (`engine/orchestrator/__init__.py:445-451`). (Elevates the
    earlier MD8 deferred item.)
  - `carry_staked_basis_funding_scan_experiment` — **HIGH**: current harness premise reads env-LESS legacy
    `lst-rates-central-…` / `lending-indices-central-…` buckets (not `-prd`).
  - `defi_manifest_canonicalisation` — **MED**: an OPEN G1 verification step prescribes `gsutil ls gs://…` (subprocess
    CLI banned by QG 5.69).
- **M33 (BUNDLED_DATA_TYPES cluster-registry seeding):**
  - `prediction_venue_perps_and_live_clob_depth` — **HIGH**: adds Kalshi as a source for
    `prediction_canonical_question_group` (a BUNDLED type) with no cluster-registry seeding tracked → `record_captured`
    may raise `MissingClusterValidationError`.
- **M36 (consolidator dedup `_OPTIONAL_DEDUP_COLS` must include `source`) — DATA-CORRECTNESS, ⚠️ NOTIFY-OPERATOR:**
  - `data_source_provenance` (open P1) + `tradfi_massive_dual_source` (open P0) + `pipeline_mode_source…` (open P2
    residue) — **HIGH**: all ship dual-source write paths while the consolidator dedup key omits `source`, so
    `batch_databento` vs `batch_massive` rows for one cell **collapse last-write-wins, silently dropping a source**.
    Open at **inconsistent priorities (P0/P1/P2) across 3 plans** with no single owner → the per-heartbeat-rule
    operator-flag item. Resolution: one UTL `manifest_consolidator.py` fix (add `source` to `_OPTIONAL_DEDUP_COLS`, with
    the read-path resolver) BEFORE any dual-source AG consolidation runs; assign one owner + align to P0.

**ALIGNMENT-NEEDED (systematic, not hard conflicts):**

- **HC-V2 two-layer** — 5 MTDS coverage/manifest plans (`downstream_services`, `honest_coverage_smoke_harness`,
  `data_status_tab`, `cefi_manifest`, `defi_manifest`) frame coverage as a single v1 number `captured/(c+e+f+eu)` with
  no Layer-1 gate / `schema_version 2`. Predate hc-v2; need a v2 consumer update (owned by the honest-coverage-v2
  plans).
- **REPLAY** — `defi_manifest`'s `mtds_canonical_reader` uses a flat `batch>bare>live>replay` ranking, not
  mode-contextual `select_for_mode` (harmless for batch consumers today, wrong if a live consumer is routed through it).

**LATENT-CLEAN (verified aligned on the new axis):** M31 bar-edge (the `bar_edge…` plan owns it; no other plan ingests
open-edge candles in open items) · M34 cadence (the pipeline_mode plan explicitly affirms column-not-path-key) ·
TRANSPORT (no glued `source_transport`; `batch_hyperliquid_rest` correctly retired everywhere). M35 (CLI 3-axis) not
separately re-scored — live `cli/main.py` already uses `--operation/--mode/--asset-group` per the critic.

**Net pass-3:** the M-ledger's "0 MAJOR" was partly latent-axis artifact — pass 3 surfaces **5 new contradictions (4
HIGH/MED bucket+bundle + the M36 data-correctness cluster)** + 5 HC-V2 alignment-needed; the other axes confirmed clean.

## Section F — Contradiction review log (per-item; FRESH live verification 2026-06-30)

> Walking the MTDS contradictions one at a time with live code + manifest checks (the same method that corrected the IS
> doc's C1/C5). Each entry: contradiction, ground-truth, verdict, decision. **Kept LOCAL/unpushed per operator; Harsh
> decided the clear ones, flagged operator-only items.** Index: M-C1 live_source migration · M-C2 consolidator
> source-drop · M-C3 env-less buckets · M-C4 BUNDLED cluster seeding · M-C5 Barchart · M-C6 XNAS.ITCH · M-C7 live-book5
> credentials · M-C8 silent-capture · M-C9 VENUE_FETCH_FAILED · M-C10 HC-v2 two-layer.

### M-C1 — codex/ledger say `live_websocket` IN-FLIGHT (M7); live writers emit `live_<source>` — CHECKED vs code + RUNTIME manifest; verdict: CODEX IS STALE → flip M7 LANDED

**Contradiction:** M7 + codex `pipeline-mode-partition.md` frame `live_websocket` as the transitional live mode
(IN-FLIGHT); ~4 plans (perps/deribit/odds/master) emit `live_<source>`. Pass-2 hedged ("code migrated, but runtime
pending — do NOT flip").

**Ground-truth (2026-06-30):** (1) **Code:** `rg LIVE_WEBSOCKET --type py` (MTDS+UTL, excl tests) = **0 hits** — deleted
from the `PipelineMode` enum. (2) **RUNTIME** — live cefi manifest `pipeline_mode` distribution: `live_deribit` 6,518 ·
`live_binance` 4,080 · `live_kraken` 2,972 · `live_hyperliquid` 1,620 · `live_okx` 756 · `live_bybit` 47 = **15,993
`live_<source>` rows, `live_websocket` = 0.** So runtime IS migrated (cefi), **refuting pass-2's "runtime pending"
caution.** (3) **Residual:** reader legacy fallback still live (`reader.py:294-296` appends a `None`-mode base; UTL
`manifest_reader_fallback.py`) — M30.3 not executed.

**Verdict — codex/ledger is the stale side; M7 → LANDED.** Decision (Harsh): (a) **flip M7 IN-FLIGHT→LANDED** in
ledger + fix codex `pipeline-mode-partition.md` normative prose (the M30.5 stale-teaching flag); (b) spot-check
**tradfi** runtime for any `live_massive` (cefi is clean); (c) M30.3 reader-fallback removal is the only residual —
harmless belt-and-suspenders, execute as cleanup (gated on `READER_FELL_BACK_TO_LEGACY_PATH`=0/7d). The ~4
`live_<source>` plans are ALIGNED.

### M-C2 — consolidator collapse is recency- not status-aware (M36) — CHECKED vs UTL code + operator context; DOWNGRADED to latent (idempotent backfill prevents the divergence)

**Operator context (Harsh 2026-06-30):** `databento`/`massive` are **data VENDORS (providers), not venues** — they
supply tradfi venue data. `source` is **provenance** (track where data came from); for coverage ("do we HAVE the cell?")
the source is irrelevant — having it from EITHER vendor = covered. So **collapsing the two vendor rows into one is
CORRECT**, and the doc's original fix ("add `source` to the dedup key") is **WRONG** — it would keep two rows per cell
and double-count / defer the collapse.

**The REAL bug (verified):** the collapse is **recency-ordered, not status-aware.** `manifest_consolidator.py:1347`:
`order_by = "attempted_at DESC NULLS LAST, written_at DESC NULLS LAST"` — keeps the most-recently-**attempted** row. The
only pre-filter (`_stale_drop_predicate`, :1375) drops blank/below-schema rows; **`captured` does NOT beat
`attempted_failed`.** So when two vendors diverge on one cell:

> databento **captures** cell X (Mon) + massive **fails** cell X (Tue) → collapse keeps Tuesday's `attempted_failed` row
> → the cell would read FAILED though we have it → coverage undercount. **BUT this requires massive to ATTEMPT a cell
> databento already captured.**

**Operator follow-up + verification (Harsh 2026-06-30) — DOWNGRADES the finding:** we **don't re-fetch already-captured
cells** — a vendor only fetches what's missing; we re-fetch a captured cell ONLY if its data is wrong/corrupted (then
the new attempt is the truth, and recency-collapse is CORRECT). **Verified in code — the backfill is idempotent:**
handlers skip already-captured cells, including the concurrent case — `lst_rates_handler.py:380/411`
(`already_captured_by_concurrent_worker`), `perp_funding_handler.py:367`, `liquidation_events_handler.py:239`,
`solana_lst_archival.py:597`, `risk_params_handler.py:568`, `gas_fee_handler.py:249`, `lending_indices_handler.py:715` —
all _"skip … already captured"_. So a vendor never re-attempts a cell another vendor captured → **the
`(captured → later failed)` divergence cannot arise in normal operation.**

**Verdict — LATENT fragility, well-mitigated by the idempotent-backfill design; NOT an active data-correctness bug.**
The recency-collapse is benign because: (1) idempotent skip prevents the divergent pair; (2) in the corruption-refetch
case recency is correct. Residual: only a true concurrent race (two workers both pass the skip-check before either
captures) could seed a divergent pair, and the next backfill cycle self-heals it. Decision: **optional defensive
hardening** — make the collapse status-aware (`captured` wins) as belt-and-suspenders for the race edge; **LOW priority,
not NOTIFY.** _(The doc's original "add source to dedup / silent data-drop / P0" framing is WITHDRAWN: source-in-key is
wrong for coverage (vendors≠venues), and the undercount is prevented by idempotent backfill. Good example of operator
domain context correcting an audit finding.)_

### M-C3 — env-less (non-prd) bucket reads (M32) — CHECKED vs code; orchestrator RESOLVED, residuals minor

**Contradiction (pass-3 HIGH):** 4 MTDS orchestrator callsites read the env-LESS instruments-store via legacy
`get_bucket_name` (`engine/orchestrator/__init__.py:445-451`) → stale/absent bucket → honest-cov flat.

**Ground-truth:** the flagged callsites (`__init__.py:445-457`) **already use
`resolve_bucket_name(kind="instruments-store", asset_group=…)`** with an inline comment crediting the "C6 fix";
`get_bucket_name` survives only as an import/`__all__` re-export, **no live call** in the orchestrator. → **The HIGH
part LANDED since the doc was written (06-29).** Residuals (separate, CONFIRMED, minor): `carry` harness reads env-LESS
`lst-rates`/`lending-indices` buckets; `defi_manifest` G1 step prescribes banned `gsutil ls` (`:1518`, QG 5.69).

**Verdict — orchestrator RESOLVED; 2 mechanical residuals.** Decision (Harsh): close the orchestrator finding; fix
`carry` buckets → `resolve_bucket_name` and `defi_manifest` `gsutil ls` → UTL gcs helper when those plans are next
touched.

### M-C4 — BUNDLED data_type written without cluster-registry seeding raises (M33) — CHECKED vs code; CONFIRMED latent trap

**Contradiction:** `prediction_venue_perps` adds KALSHI as a source for `prediction_canonical_question_group` (a BUNDLED
type) with no cluster-registry seeding tracked.

**Ground-truth:** `manifest_writer/_writer_captured.py:288-289` —
`if data_type in BUNDLED_DATA_TYPES and (expected_root_clusters is None or cluster_extractor is None): raise MissingClusterValidationError`.
`expected_coverage.py:375` lists `prediction_canonical_question_group` for **POLYMARKET only** (not KALSHI). So writing
a Kalshi CQG bundle without seeding **would raise at write time.** CONFIRMED latent trap (fires only when that open item
runs).

**Verdict — forward-looking sequencing risk.** Decision (Harsh): seed the cluster registry for Kalshi CQG (or confirm
the `cluster_extractor`/`expected_root_clusters` kwargs are passed) **before** the `prediction_venue_perps` Kalshi item
runs. Annotate that todo. Not a current data bug.

### M-C5 — Barchart still in `ohlcv_15m` SOURCE_PRIORITY (M22/MD3) — CHECKED vs code; UAC FIXED, plan text stale

**Ground-truth:** UAC `_source_priority_data.py:290` notes _"ohlcv_15m: barchart RETIRED 2026-06-24 (VIX 15m now from VX
futures via Databento XCBF.PITCH)"_; the live priority is `[databento, massive, yahoo]`; no live Barchart adapter (only
a retained `BARCHART_OHLCV_15M_SCHEMA` for historical-preload provenance). **UAC code already correct.** Only the
`tradfi_massive_dual_source` plan text (L53/L180/L386) still lists Barchart.

**Verdict — plan-text stale (like IS C3).** Decision (Harsh): mechanical — update the plan's SOURCE_PRIORITY references
to `[databento, massive, yahoo]` when next touched. No code change.

### M-C6 — `XNAS.ITCH` Databento allowlist bypass? (M21/MD2) — CHECKED vs code; REFUTED (non-issue)

**Ground-truth:** `databento_subscription_allowlist.py` — allowlist frozenset = `{GLBX.MDP3, DBEQ.BASIC, XCBF.PITCH}`
(:46-48); `assert_databento_request_allowed` (:228) raises `DatabentoDatasetNotAllowedError` (:156) **before** any
network call; `XNAS.ITCH` is not in the set. The `master_catalogue` R5 smoke `XNAS.ITCH` was a **noisy probe label**,
not a bypass.

**Verdict — REFUTED, non-issue.** Decision (Harsh): drop from the operator list; optionally clean the probe label to
`DBEQ.BASIC`. No action required.

### M-C7 — live persistence: fix the root (`LiveEventFacadeSink` warm-GCS-parts), not the `LiveWebsocketTickSink` interim (MD4/M12/M13) — operator directive + corrected root-cause

**What it is — the live tick PERSISTENCE SINK.** Two implementations: **`LiveEventFacadeSink`** (the intended end-state
— publishes each tick to the UTL EventTransport facade → Pub/Sub (hot) → Cloud-Storage subscription → GCS hive (warm) →
cold compaction; the **"live = batch" event-log spine** that gives `paper(W)==batch-rerun(W)` ε=0 determinism) vs
**`LiveWebsocketTickSink`** (a **direct-GCS writer** — the old coupled path the spine was built to replace, which per
codex `live-data-persistence-and-event-log.md` _"broke paper==batch determinism, GCS contents could change between write
and read"_).

**The deviation:** Plan-04 cut over to `LiveEventFacadeSink` (MTDS@3b956b70) then **REVERTED to `LiveWebsocketTickSink`
(direct-GCS) as `_make_default_sink()` default** (MTDS@3043f2dc) because the facade path isn't fully provisioned: (1)
the `features-service-events` **Pub/Sub topic IAM was missing** (ServiceBootstrap `STARTED` crashed rc=1; partly fixed
via terraform), and (2) the **Warm tier — Pub/Sub → Cloud-Storage subscription → GCS hive — is `BLOCKED-CREDENTIALS`.**
So live prediction-perp book5 DOES land in GCS (works), but bypasses the event-log spine → no batch=live determinism
guarantee for that data until it flows through the facade.

**ROOT-CAUSE UPDATE (fresh live-code check 2026-06-30) — corrects the plan narrative + the operator directive:**

Operator (Harsh) directive: **`LiveEventFacadeSink` is the correct path — fix the root, do NOT settle for
`LiveWebsocketTickSink`.** Rationale: prod = **1000s of ticks/sec** across live feeds → cannot write per-tick/per-window
to GCS. Correct architecture = **batch in memory → append to parquet parts → flush to GCS periodically (current day, in
parts) → a daily cron aggregates the parts into canonical (batch-equivalent) data.** (That is precisely the warm+cold
tiers of the event-log spine.)

What the live code actually shows (corrects the plan):

- **`_make_default_sink()` already returns `LiveEventFacadeSink`** (`websocket_runner.py:242`) — the plan's "reverted to
  `LiveWebsocketTickSink`" is **STALE**; the correct sink is the live default.
- **In-memory batching EXISTS** — `LiveEventFacadeSink` buffers ticks per shard and flushes the window-batch
  (`event_facade_sink.py:58-90`); it publishes one `CanonicalPersistEnvelope` per window, not per tick. ✓ (the "batch in
  memory" you want is done).
- **`PubSubTransport.publish()` is IMPLEMENTED, not a no-op** (`event_facade.py:283-295` — serialises envelope →
  publishes to topic `persist-{ag}-{dt}`). The "STUB / Plan-03-pending" label is the **INFRA** (topics + subscriptions +
  IAM), not the code.
- **Cold-tier daily compactor EXISTS as a scaffold** — `deployment-service/.../jobs/live_event_log_compactor.py`
  (`run_union` over SINK_MATRIX shards, warm-bucket → cold-bucket; terraform `union_job.tf`).
- **The ONE missing link = the WARM tier durable-write:** `flush()` publishes to `get_transport("pubsub")` → Pub/Sub,
  and the **Pub/Sub → Cloud-Storage subscription → GCS** materialisation is `BLOCKED-CREDENTIALS`. So window-batches
  reach Pub/Sub but aren't durably written to warm GCS.

**Decision (Harsh) — fix the root via the warm-GCS-parts path (the unblock):** implement the warm tier as a **direct
periodic GCS part-write** — `LiveEventFacadeSink` already batches in memory → add a warm-GCS sink/transport that appends
the buffered window-batch to a **per-(day,shard) parquet part in GCS** on the flush cadence → the **existing compactor**
unions the day's parts into the canonical cold parquet (= batch-equivalent). This **side-steps the blocked Pub/Sub →
Cloud-Storage subscription entirely** (no credential needed for persistence). Pub/Sub stays the HOT real-time transport
for when live strategy needs it (or `RedisStreamTransport`); persistence no longer depends on it.

**Build checklist (when greenlit):** (1) warm-GCS part-writer (append parquet parts, `resolve_bucket_name` warm bucket,
no inline `gs://`); (2) wire `LiveEventFacadeSink.flush` to it (tee or replace the pubsub publish for the persist path);
(3) complete the `live_event_log_compactor` IO (scaffold → real); (4) determinism test (`paper(W)==batch-rerun(W)` ε=0
still holds reading the compacted cold parquet); (5) verify SINK_MATRIX has the cefi perp `book_snapshot` shards (M14).
**Status: decided (fix root, warm-GCS-parts); NOT yet built — awaiting greenlight to implement (real code, not a doc
edit).**

### M-C8 — silent-capture / manifest-invisible data_types (MD5/M4/M14/M16) — CHECKED; CONFIRMED, self-tracked

**Ground-truth (3 sub-items):** (1) `carry` **`perp_daily_ctx`** written via raw `gcsfs`, zero manifest calls, absent
from `DATA_TYPES_BY_ASSET_GROUP`/`SINK_MATRIX`/UAC — **manifest-invisible, CONFIRMED** (canonicalize to
`derivative_ticker` + register before any pipeline consumes it). (2) EXTENDED `_fetch_extended_candles_for_symbol`
logs-debug-without-recording on HTTP-error/empty — **same finding as IS C9** (confirmed code bug, low MVP urgency, ohlcv
non-MVP). (3) `instruments_mtds_subset` `_af_record_empty(reason='')` blank-reason needs a typed `EmptyConfirmedReason`
(M16, open P2).

**Verdict — data-correctness, each self-tracked in its plan.** Decision (Harsh): land each fix **before** that plan's
data is trusted as honest-coverage ground truth; perp_daily_ctx registration is the highest-leverage (currently
invisible).

### M-C9 — open re-fetch tasks name retired `VENUE_FETCH_FAILED` (M10/MD6) — same as IS C6

**Verdict — MINOR relabel-only** (verified in the IS pass: emission retired in `sentinels.py`, but 482,518 historical
rows still carry the label in the live cefi manifest → the task selects real cells; only the wording implies a live
model). Decision (Harsh): relabel to "cells whose legacy `error_reason` was `VENUE_FETCH_FAILED`" — **fix once**,
reference from both the IS (C6/D4) and MTDS (MD6) docs.

### M-C10 — 5 MTDS coverage plans frame coverage as v1 single-number (no Layer-1 gate) — alignment-needed

**Status:** `downstream_services`, `honest_coverage_smoke_harness`, `data_status_tab`, `cefi_manifest`, `defi_manifest`
compute coverage as v1 `captured/(c+e+f+eu)` with no Layer-1 gate / `schema_version 2`. They predate honest-coverage-v2
(codex 06-29, newer than every M#). Same family as IS C4 (the two-layer gate).

**Verdict — systematic alignment, not a hard conflict.** Decision (Harsh): owned by the honest-coverage-v2 plans — these
5 consumers update to the v2 two-layer model (Layer-1 gates Layer-2 trust). Couples to the IS-side `build_expected`/C2
work.

### MTDS review-log summary (10 items)

| #     | item                                                     | verdict                                                                                                                                                                | who decides                           |
| ----- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| M-C1  | live_source migration (M7)                               | codex STALE; runtime LANDED (15,993 live\_<source>, 0 live_websocket) → flip M7                                                                                        | Harsh ✅ (flip) + tradfi spot-check   |
| M-C2  | consolidator collapse is recency- not status-aware (M36) | **DOWNGRADED → latent** — idempotent backfill (skip-captured) prevents the divergence; recency correct for corruption-refetch                                          | Harsh ✅ (optional low-pri hardening) |
| M-C3  | env-less buckets (M32)                                   | orchestrator RESOLVED; 2 mechanical residuals                                                                                                                          | Harsh ✅                              |
| M-C4  | BUNDLED cluster seeding (M33)                            | CONFIRMED latent trap (would raise)                                                                                                                                    | Harsh ✅ (seed before run)            |
| M-C5  | Barchart SOURCE_PRIORITY (M22)                           | UAC fixed; plan text stale                                                                                                                                             | Harsh ✅ (mechanical)                 |
| M-C6  | XNAS.ITCH allowlist (M21)                                | REFUTED, non-issue                                                                                                                                                     | Harsh ✅ (drop)                       |
| M-C7  | live persistence root (MD4)                              | **DECIDED: fix root** — default already `LiveEventFacadeSink`; build warm-GCS-parts write (batch→parts→daily compaction) to side-step the blocked Pub/Sub subscription | Harsh ✅ (build when greenlit)        |
| M-C8  | silent-capture (MD5)                                     | CONFIRMED, self-tracked                                                                                                                                                | Harsh ✅ (land before trust)          |
| M-C9  | VENUE_FETCH_FAILED (M10)                                 | MINOR relabel (= IS C6)                                                                                                                                                | Harsh ✅                              |
| M-C10 | HC-v2 two-layer (5 plans)                                | alignment-needed                                                                                                                                                       | honest-cov-v2 plans                   |

**Headline (revised):** **M-C2 DOWNGRADED to latent** — operator context (vendors≠venues; we don't re-fetch
already-captured cells) + verified idempotent backfill (handlers skip-captured) mean the recency-collapse divergence
can't arise in normal operation; optional low-priority hardening only. So the MTDS audit has **no active
data-correctness emergency**. The biggest real _finding_ is **M-C1 corrected** — fresh runtime evidence shows the
live*source migration IS landed (cefi: 15,993 `live*<source>`, 0 `live_websocket`), so flip M7 LANDED (the doc's pass-2
was over-cautious). The remaining operator item is **M-C7** (live-book5 Cloud-Storage-subscription credential).
Everything else is mechanical/alignment.

## Progress Log

- **2026-06-29** — Doc created. Trust model carried from the IS reconciliation. Codex freshness checked (2 old docs:
  IS↔MTDS boundary 06-16, shard-isolation 05-17 — both pattern-stable, current-state drift flagged M30). **Section A
  M-ledger (M1–M29 + M30 stale flags) written** — contract-extraction verified every assertion against live
  market-tick-data-service + UAC code. 74 plans reference MTDS. Next: Section B triage + deep-read fan-out.
- **2026-06-29** — Section B triage + 15 cluster-agents deep-read **41 plans** against M1–M30. **Sections C + D
  written.** **Tally: 0 MAJOR-CONFLICT · 26 MINOR-DRIFT · 15 ALIGNED** — far cleaner than IS (the MTDS-specific axes are
  mature; the v10-MVP MAJORs were IS-side / honest-coverage overlap set-aside here). Findings collapse into 10 clusters
  (MD1–MD10). **Headline (MD1): the ledger/codex is probably the stale side on M7 + M30.3** — live writers already emit
  `live_<source>` (live_kalshi_perp / live_deribit / live_odds_api) and M1-BREAKING reports complete + `LIVE_WEBSOCKET`
  deleted fleet-wide, so M7 should likely flip IN-FLIGHT→LANDED and M30.3 reader-fallback removal should be
  executed/closed. **3 operator items** (MD1 M7/M30.3 flip · MD2 XNAS.ITCH allowlist verify · MD4 live book_snapshot_5
  Pub/Sub subscription). Read-only pass; no subject plans edited. Companion to the IS reconciliation (committed
  `2ad201e18`).
- **2026-06-30** — **Section F contradiction review log (M-C1…M-C10) — FRESH live verification.** Walked all MTDS
  contradictions with live code + manifest checks (same method that corrected the IS C1/C5). Corrections to the doc's
  own pass-2/3: **M-C1 (M7)** — runtime CONFIRMED landed (live cefi manifest = 15,993 `live_<source>` rows:
  deribit/binance/ kraken/hyperliquid/okx/bybit; `live_websocket`=0), so pass-2's "runtime pending, don't flip" was
  over-cautious → flip M7 LANDED. **M-C3 (M32)** — orchestrator bucket callsites ALREADY migrated to
  `resolve_bucket_name` (C6 fix landed since 06-29) → HIGH part resolved; carry/defi_manifest residuals minor.
  ~~CONFIRMED unchanged: **M-C2 (M36)** consolidator `_BASE/_OPTIONAL_DEDUP_COLS` both omit `source` → silent
  dual-source drop (⚠️ NOTIFY, the headline)~~ (was: this framing — see CORRECTED note below); **M-C4 (M33)**
  `_writer_captured.py:288` raises on unseeded BUNDLED Kalshi CQG (latent trap); **M-C8** perp_daily_ctx
  manifest-invisible. REFUTED: **M-C6** XNAS.ITCH (allowlist guard raises first). Mechanical: M-C5 Barchart (UAC fixed,
  plan text stale), M-C9 VENUE_FETCH_FAILED relabel (=IS C6). ~~Operator-only: M-C2 owner/P0~~ (was: M-C2 owner/P0 — see
  CORRECTED note below), M-C7 live-book5 credentials, M-C10 hc-v2 alignment. Kept LOCAL/unpushed per operator.
- **CORRECTED 2026-07-12 per operator ruling (plan-reconciliation finding 171):** the Section-F DOWNGRADE verdict stands
  — M-C2 is LATENT/LOW-priority optional hardening, NOT an active bug and NOT a NOTIFY headline. This entry's "CONFIRMED
  unchanged" framing was written without acknowledging the same-day downgrade (Section F's M-C2 write-up at ~L458 and
  the MTDS review-log summary table's M-C2 row, both already dated 2026-06-30, correctly show "DOWNGRADED → latent";
  this Progress Log line alone regressed to the withdrawn pre-downgrade framing). No dual-source silent-drop bug is
  active and no operator NOTIFY is warranted; the only surviving action is the optional defensive hardening tracked
  below. Ruling recorded in `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 (finding
  171).
- [x] [CODE] P3. LOW-priority — `manifest_consolidator.py` optional defensive hardening: make the dual-source collapse
      status-aware (`captured` wins over `attempted_failed` in `_stale_drop_predicate`/`order_by`) as
      belt-and-suspenders for the narrow concurrent-race edge case (two workers both pass the skip-already-captured
      check before either writes). Not required for correctness today — idempotent skip-if-captured already prevents the
      divergence in normal operation (Section F, M-C2). No owner assigned; pick up opportunistically. —
      **unified-trading-library@a05d69c7** (2026-07-13): implemented per the M-C2 design (status-aware tie-break on
      collapse, NOT source-in-dedup-key) as a leading ORDER BY CASE in the window-dedup `order_by` —
      `capture_status='captured'` outranks any non-captured status in the same dedup-key group regardless of recency;
      no-op tie for all-captured / all-non-captured groups so the cf2e196b cross-source row_count tie-break, the
      bb17638e TRY_CAST guard, and plain recency engage exactly as before. Evidence: new regression test
      `test_consolidate_captured_survives_later_non_captured_duplicate` (verified fails pre-fix on recency keeping the
      later `attempted_failed` row, passes post-fix); cf2e196b/2ba20527/bb17638e regression tests re-run green
      (test_manifest_consolidator.py 59/59, +test_factory.py 82/82); full `quality-gates.sh --no-fix` green at
      utl@22885e3f before ship (`ALL QUALITY GATES PASSED (137s)`).
