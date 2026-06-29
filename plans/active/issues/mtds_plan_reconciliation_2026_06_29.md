---
doc_type: issue
title: "MTDS Plan Reconciliation — open plans vs SSOT (UAC + MTDS code + 3 new plans + fresh codex)"
summary:
  "Find-first reconciliation for market-tick-data-service (MTDS), the service after instruments-service. Score every
  open plan that touches MTDS against the SSOT (live UAC + market-tick-data-service code + fresh codex + the 3 new
  plans) to surface task-item CONTRADICTIONS for a later alignment pass. Read-only: finds + classifies, does NOT edit
  subject plans. Companion to instruments_service_plan_reconciliation_2026_06_29.md. Section A = the MTDS assertion
  ledger (M-series). Section B = triage. Section C = deep-read findings. Section D = synthesis + resolutions."
status: active
nature: audit
asset_group: cross-asset
stage: [meta]
repos: [market-tick-data-service, unified-api-contracts]
scope: [admin]
tags: [reconciliation, ssot-audit, plan-hygiene, mtds, market-data, pipeline-mode, honest-coverage, shard-isolation]
related:
  [
    instruments_service_plan_reconciliation_2026_06_29.md,
    ../honest_coverage_v2_instrument_denominator_2026_06_28.md,
    ../honest_coverage_v2_opus_checkpoints_2026_06_28.md,
    ../../../codex/02-data/pipeline-mode-partition.md,
    ../../../codex/02-data/live-data-persistence-and-event-log.md,
    ../../../codex/04-architecture/shard-level-failure-isolation.md,
    ../../../codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
  ]
created: 2026-06-29
last_updated: 2026-06-29
assigned_vm: NA
execution_scope: local-only
priority: P1
source: [operator request 2026-06-29]
drift_direction: advance-code
depends_on: []
---

# MTDS Plan Reconciliation (2026-06-29)

> **Read-only FIND pass.** Companion to the instruments-service reconciliation. Same trust model: **no plan is SSOT;
> SSOT = live UAC + market-tick-data-service code + fresh codex.** A plan item is a contradiction wherever it misaligns
> with that truth; no date-based trust exemption. `last_updated` is junk (bulk-stamped) — use `created` for ordering
> only. The 3 new plans + the honest-coverage-v2 pair are the aligned reference, not a privileged tier.

## Codex freshness (git last-modified) — MTDS-relevant docs

| Codex doc                                          | git date   | verdict                                                        |
| -------------------------------------------------- | ---------- | -------------------------------------------------------------- |
| `02-data/honest-coverage-model.md`                 | 2026-06-29 | ✅ FRESH (Tier-1 v2 model)                                     |
| `02-data/availability-manifest-and-data-status.md` | 2026-06-27 | ✅ fresh                                                       |
| `02-data/tradfi-databento-sourcing-ssot.md`        | 2026-06-27 | ✅ fresh (one deploy-gated caveat — M30.4)                     |
| `02-data/live-data-persistence-and-event-log.md`   | 2026-06-26 | ✅ fresh                                                       |
| `02-data/pipeline-mode-partition.md`               | 2026-06-25 | 🟡 fresh-ish; Phase-8 reader-fallback removal past date (M30.3)|
| `06-coding-standards/config-reloader-pattern.md`   | 2026-06-25 | ✅ fresh-ish                                                   |
| `04-architecture/tier-and-import-architecture.md`  | 2026-06-25 | ✅ fresh-ish                                                   |
| `04-architecture/instruments-service-as-ssot-for-mtds.md` | 2026-06-16 | 🟡 core contract OK; "current-state" stale (M30.1)      |
| `04-architecture/shard-level-failure-isolation.md` | 2026-05-17 | 🟡 rule OK; classify-call signature stale (M30.2)             |

---

## Section A — MTDS SSOT assertion ledger (the yardstick)

`LANDED` = shipped ground truth (contradiction = now-conflict); `IN-FLIGHT` = target end-state (contradiction =
alignment-needed). Citations verified against live `market-tick-data-service` + UAC code by the contract-extraction pass.

### Domain 1 — IS-owns-universe / MTDS-is-market-data-only

- **M1 `LANDED`** — MTDS must NOT hardcode venue URLs, universe lists, or coverage windows in handlers; all derived at
  runtime from the IS catalogue (`InstrumentRecord.source_archive_url_template` / `source_record_types` /
  `source_coverage_start/end`). 3 QG gates enforce (`no_hardcoded_venue_urls/universe/silent_absence`, quality-gates.sh:144-155).
  **Conflicts:** plans adding hardcoded venue URLs/universe/windows to MTDS, or treating MTDS as the universe owner.
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

- **M9 `LANDED`** — a failed shard must NOT kill others: per-shard loop catches all, classifies, `record_failed`
  (no silent swallow), logs with shard-atom fields, continues. `raise` inside a per-shard loop is banned
  (shard-level-failure-isolation.md; venue_fetch.py:572-575). **Conflicts:** plans adding a `raise`/fail-fast in a per-shard loop.
- **M10 `LANDED`** — opaque `VENUE_FETCH_FAILED` is RETIRED; unknown errors → `classify_venue_error()`, else
  `f"UNCLASSIFIED:{code_token}"` (sentinels.py:267-269,639-641,717-720). **Conflicts:** plans treating `VENUE_FETCH_FAILED` as the live model.
- **M11 `LANDED`** — per-VM batch clusters set `VM_NAME=<unique>` + `MANIFEST_PER_VM_SHARDS=true` (UTL raises
  `MultiWorkerWithoutShardIsolationError` otherwise; QG STEP 5.66). **Conflicts:** plans launching multi-worker backfills without per-VM shard isolation.

### Domain 4 — live = batch event-log spine

- **M12 `LANDED`** — MTDS publishes live ticks via the UTL `EventTransport` facade (`event_facade`) wrapping
  `CanonicalPersistEnvelope`; `InMemoryTransport` (paper) / `PubSubTransport` (live) → `paper(W)==batch-rerun(W)` ε=0
  (live-data-persistence-and-event-log.md; event_facade_sink.py:18-90). **Conflicts:** plans adding a live-only persistence path bypassing the facade.
- **M13 `LANDED`** — MTDS must NOT write live ticks directly to GCS on the hot path; facade → Pub/Sub → warm GCS via
  Cloud-Storage subscription (live/__init__.py:17; websocket_runner.py:48). **Conflicts:** plans reintroducing direct hot-path GCS writes.
- **M14 `LANDED`** — `SINK_MATRIX` governs all 52 `(asset_group,data_type)` shards; `sinks_for()` raises `KeyError` on
  unknown (no silent default); all market-data shards `REPRODUCIBLE`. **Conflicts:** plans adding a shard without a SINK_MATRIX entry or assuming a silent default.

### Domain 5 — writer-side honest-coverage contracts (shared with the IS/honest-coverage-v2 audit)

- **M15 `LANDED`** — `instrument_type` normalized to canonical **lowercase** at write (`PartitionedTickWriter`
  `.str.lower()`, partitioned_writer.py:255-258; derives from venue/symbol when absent). **Conflicts:** plans assuming uppercase/blank instrument_type.
- **M16 `LANDED`** — `empty_confirmed` carries a typed UAC `EmptyConfirmedReason`; `SOURCE_RETURNED_ZERO` requires a
  `FetchEvidence` proof (`UnprovenHonestAbsenceError` otherwise) (sentinels.py:493-498,746-769). **Conflicts:** plans emitting blank-reason empties / unproven zero.
- **M17 `LANDED`** — `pipeline_mode` + `source` stamped on EVERY captured row via
  `_resolve_pipeline_mode_for_sentinel(venue,dt,source=_run_source)` (manifest_finalize.py:325-370). (= M5/M6 at row grain.)
- **M18 `LANDED`** — 4-state `capture_status` is canonical; `attempted_failed` needs a typed reason;
  `expected_unattempted` is WRITER-materialised (MTDS pre-flight + IS enumerator), never re-derived downstream.
  **Conflicts:** plans re-deriving `expected_unattempted` in a consumer, or adding a 5th state.
- **M19 `LANDED`** — per cefi/defi/tradfi, `empty_confirmed` is legitimate only at VENUE level (holiday/weekend/pre-genesis);
  per-instrument-day `empty_confirmed` indicates a writer bug. **Conflicts:** plans treating per-instrument-day empties as normal.
- **M20 `LANDED`** — 4-pillar write-gate on `record_captured` (rows>0 · NaN<thresh · schema matches UAC · cluster-coverage≥expected
  for bundles); failures route to `record_failed`, no partial parquets land (manifest_finalize.py:166-265). **Conflicts:** plans landing partial/ungated parquets.

### Domain 6 — Databento / TradFi sourcing

- **M21 `LANDED`** — exactly 3 Databento datasets (`GLBX.MDP3` CME / `DBEQ.BASIC` US-equities / `XCBF.PITCH` CFE-VX); all
  requests via `assert_databento_request_allowed(...)` (off-allowlist → `DatabentoDatasetNotAllowedError`); `batch.submit_job`
  hard-blocked. **Conflicts:** plans adding a 4th Databento dataset or a batch.submit_job path.
- **M22 `LANDED`** — Barchart as a LIVE source is RETIRED; VIX 15m is a one-time GCS preload, no live Barchart adapter
  (tradfi/__init__.py:11-13). **Conflicts:** plans wiring a live Barchart adapter.
- **M23 `LANDED`** — TradFi `SOURCE_PRIORITY` is databento-first (`[databento, massive]`; `ohlcv_1s` databento-only); KRX +
  ICE(DXY) are Yahoo Finance, NOT Databento, NOT operator-blocked. **Conflicts:** plans making massive primary, or routing KRX/ICE through Databento.
- **M24 `LANDED`** — CME OHLCV from `GLBX.MDP3` uses `stype_out=instrument_id` (not raw_symbol) with `stype_in=parent`,
  paginates `symbology.resolve` in 2000s, classifies space-containing CME short options. **Conflicts:** plans using raw_symbol or unpaginated resolve.

### Domain 7 — service infra + tier/import

- **M25 `LANDED`** — MTDS instantiates UTL `ServiceBootstrap` (STARTED/STOPPED/FAILED; QG 5.61; cli/main.py:19,530).
- **M26 `LANDED`** — MTDS HTTP API wires `make_health_router` + `data_freshness` callback (QG 5.62; api/main.py:25,107).
- **M27 `LANDED`** — MTDS uses `ApiKeyReloader` (sync initial fetch, daemon refresh), not a frozen key dict
  (tick_data_handler.py:30,71,139). **Conflicts (M25-M27):** plans bypassing ServiceBootstrap/health-router/ApiKeyReloader.
- **M28 `LANDED`** — MTDS must NOT import another service repo (T4→T4 banned); depends only on UTL/UAC/`unified-*-interface`.
  Known tracked violation: UMI(T2)→UDC(T3) `cohesion-umi-udc-dep-violation`. **Conflicts:** plans adding a service↔service import.
- **M29 `LANDED`** — domain schema types from `unified_api_contracts.{domain}` / `.internal`; local equivalents banned
  (event_facade_sink.py:14-17; sentinels.py:12-19). **Conflicts:** plans defining local manifest/event/config dataclasses.

### Domain 8 — stale-source flags (codex docs that are the stale side)

- **M30.1** — `instruments-service-as-ssot-for-mtds.md` (06-16): core IS→MTDS contract ACCURATE, but its "current state"
  (writers "0% of 7.4M rows at v8", mid-v8-migration) is STALE — manifest is now v9. Plans leaning on its state numbers cite stale.
- **M30.2** — `shard-level-failure-isolation.md` (05-17): no-raise rule + classify-or-UNCLASSIFIED intent CORRECT, but the
  `classify_venue_error(e)` call-signature illustration is stale (live = venue-aware token-based + `UNCLASSIFIED:` fallback).
- **M30.3** ⚖️ — `pipeline-mode-partition.md` Phase-8 (reader legacy-fallback removal) target 2026-06-15 has PASSED (today
  06-29); gated on `READER_FELL_BACK_TO_LEGACY_PATH`=0/7d, `last_executed: NEVER`. **Operator-attention.**
- **M30.4** ⚖️ — `tradfi-databento-sourcing-ssot.md`: the `live_massive` source-stamp fix is code-landed (UAC@1205ae44)
  but DEPLOY-gated (tarball rebuild); live rows written pre-rebuild are still mis-stamped `live_massive`. **Operator-attention.**

---

## Section B — Triage (MTDS-specific contested-token signal across 74 plans)

Signal = grep across 7 token-groups (venue-universe · pipeline_mode · shard · event-spine · writer · databento · infra).
~37 MTDS-material plans deep-read across 15 cluster-agents (M-C1…M-C15). Domain-5 honest-coverage findings that already
appear in the IS audit are cross-referenced, not duplicated; MTDS focus = Domains 1-4, 6-7.

| Cluster | Plans                                                                                                            |
| ------- | --------------------------------------------------------------------------------------------------------------- |
| M-C1    | cefi_manifest_canonicalisation · tradfi_manifest_canonicalisation                                               |
| M-C2    | defi_manifest_canonicalisation · prediction_manifest_canonicalisation                                           |
| M-C3    | sports_manifest_canonicalisation · downstream_services_manifest_canonicalisation                                |
| M-C4    | master_data_canonicalisation_migration_catalogue                                                                |
| M-C5    | pipeline_mode_source_batch_live_replay_standardisation · bucket_name_ssot_legacy_dual_write_remediation         |
| M-C6    | data_completion_to_100_all_ag · path_to_100pct_backfill_mtds_is · data_pipeline_hardening_self_monitoring       |
| M-C7    | instruments_mtds_subset_consistency_remediation · instruments_foundation_completeness · migration_verif_orphan  |
| M-C8    | data_source_provenance_all_asset_groups · tradfi_massive_dual_source · tradfi_multisource_backfill              |
| M-C9    | mvp_backfill_tradfi_ohlcv1m_v10 · tradfi_cme_event_contract_backfill · cryptovenue_equity_perps_and_tokenized   |
| M-C10   | citadel_paper_batch_live_reconciliation · features_service_e2e_pipeline_test · sports_p2_features_history_to_ml |
| M-C11   | prediction_venue_perps_and_live_clob_depth · carry_staked_basis_funding_scan_experiment                         |
| M-C12   | solana_defi_legacy_migration · master_to_live_defi · v2_engine_venue_buildout                                   |
| M-C13   | cross_ag_shard_4pillar_validation_harness · macro_econ_adapter_scaffolds · tradfi_mdps_passthrough_dependency   |
| M-C14   | sports_p1_golden_window_mtds_odds · honest_coverage_smoke_harness · audit_criteria_automation · bar_edge_l_v_r  |
| M-C15   | data_feed_sla_registry · monitoring_control_plane_master · data_status_tab_downloads · unified_deploy_health · mtds_file_size_refactor |

**Set aside (low/zero MTDS-specific signal — honest-coverage-only overlaps already scored in the IS audit, or CI/gov/org):**
the v10 MVP plans (mvp_backfill_defi_onchain / cefi_tick / mvp_catalogue_finalization / mvp_reconciliation_closeout —
their MTDS signal is writer-side honest-coverage, covered by the IS audit's D-clusters), capability_wizard, the sports
P1/P2 family (A4-clean), defi_onchain_derivable_values, tradfi_sp500_ml, predictions_other_bucket,
sports_odds_bookmaker_coverage_enumeration, + cicd/scripts/governance/org plans (cicd_*, repo_scripts_governance,
scripts_lifecycle_marker_rollout, org_migration, codex_*, work_split, harsh_day_master, test_fleet_image_builds).

## Section C — Deep-read findings (15 cluster-agents, 41 plans)

**Tally: 0 MAJOR-CONFLICT · 0 SUPERSEDED · 26 MINOR-DRIFT · 15 ALIGNED.** Markedly cleaner than the IS audit — the
MTDS-specific axes (pipeline_mode/source, shard isolation, event spine) are mature and the writer-side migrations
already shipped. No plan instructs an action that contradicts a LANDED M# on an open item with material risk. All
findings are MED-or-below and sit inside MINOR-DRIFT plans. `*` = open `[ ]` item.

### Plans carrying a MED finding (watch-items, no MAJOR)

| Plan                                   | MED finding                                                                                                                              |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `instruments_foundation_completeness`  | **M4/M1\*** EXTENDED cefi adapter falls back to a HARDCODED market list on fetch-failure → records `captured` (stale) not `record_failed` — the "false-complete" pattern (open P1, IS-side adapter, self-diagnosed). |
| `tradfi_massive_dual_source`           | **M22** Operator-decision #3 (L53) + L180 still list **Barchart** in the `ohlcv_15m` SOURCE_PRIORITY — Barchart was RETIRED 2026-06-24 (VIX 15m now via Databento XCBF.PITCH). Stale-premise on a removed source. |
| `prediction_venue_perps_and_live_clob_depth` | **M12/M13** interim deviation — live book_snapshot_5 reverts to a direct-GCS `LiveWebsocketTickSink`; the facade→Pub/Sub→warm-GCS path is **BLOCKED-CREDENTIALS** (documented). Plus M14 — verify SINK_MATRIX entries exist for the new cefi perp `book_snapshot` shards. |
| `carry_staked_basis_funding_scan_experiment` | **M4/M14\*** `perp_daily_ctx` is a research-grade, **manifest-invisible** data_type written to GCS — must canonicalize to `derivative_ticker` + register before any production pipeline consumes it (self-flagged). |
| `master_data_canonicalisation_migration_catalogue` | **M21** R5 smoke ledger probed **`XNAS.ITCH`** as a Databento dataset alongside the allowlisted `GLBX.MDP3`/`DBEQ.BASIC` — verify `assert_databento_request_allowed` blocked it or it's a probe mislabel (US-equities → `DBEQ.BASIC`). |
| `bucket_name_ssot_legacy_dual_write_remediation` | **M1\*** open+DEFERRED fix for env-LESS instruments-store readers in the MTDS orchestrator (`engine/orchestrator/__init__.py:445-451`, `_instruments_metadata.py`) — risks silently reading the non-prd IS index. Don't strand. |
| `path_to_100pct_backfill_mtds_is`      | **M10\*** open re-fetch task names the retired `VENUE_FETCH_FAILED` label (relabel, not a new emission — see IS audit). **M16\*** pre-gate DeFi `[~]` continuation VMs must run on a post-`fbac3a9` tarball so `SOURCE_RETURNED_ZERO` carries FetchEvidence. |
| `instruments_mtds_subset_consistency_remediation` | **M16\*** `_af_record_empty(reason='')` blank-reason at IS orchestrator:4271 needs a typed `EmptyConfirmedReason` (open P2). (Its `_CEFI_VENUES` dedup item is correctly IS-side here, not an MTDS M1 hit.) |
| `tradfi_mdps_passthrough_dependency_gap`| **M28** (MDPS-scoped) verify the new passthrough adapter imports only UAC/UTL types, not `market_tick_data_service.*`. |
| `mtds_file_size_refactor`              | **M9/M13/M25** execution-risk: the behavior-preserving split of `live/websocket_runner.py` must keep facade+ServiceBootstrap; `engine/orchestrator.py` split must not reintroduce a `raise` at shard grain. (status=deferred.) |

### MINOR-DRIFT (low only)

`tradfi_manifest_canonicalisation` (M5 table omits `batch_eia`) · `defi_manifest_canonicalisation` (self-annotated
superseded `pipeline_mode=batch` refs) · `prediction_manifest_canonicalisation` (deep-import QG hygiene, not an M28
boundary) · `pipeline_mode_source_batch_live_replay_standardisation` (stale work-unit checkboxes vs shipped progress
log — flip them) · `data_completion_to_100_all_ag` (M10 legacy label; M7 progress-log refs) · `cryptovenue_equity_perps`
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
`sports_p1_golden_window_mtds_odds` · `bar_edge_left_vs_right_remediation` · `data_feed_sla_registry_and_active_self_healing`
· `data_status_tab_and_downloads_remediation`.

## Section D — Synthesis: cross-plan clusters + proposed resolutions

⚖️ = operator decision; 🔧 = mechanical. Findings collapse into 10 clusters (MD1–MD10).

### MD1 ⚖️ — The ledger may be stale: M7 is probably LANDED, not IN-FLIGHT (the headline outcome)

Multiple live writers already emit the post-gate `live_<source>` form — `live_kalshi_perp`
(`prediction_venue_perps`), `live_deribit` (`v2_engine_venue_buildout`), `live_odds_api` (`sports_manifest`) — and
`pipeline_mode_source_batch_live_replay_standardisation` reports **M1-BREAKING COMPLETE + `LIVE_WEBSOCKET` deleted
fleet-wide** (`rg live_websocket --type py` = 0). That means the **M7 "IN-FLIGHT / `live_websocket` transitional" framing
in the ledger + codex `pipeline-mode-partition.md`, and the M30.3 "reader legacy-fallback removal NEVER (target 06-15
passed)" flag, are likely the STALE side** — not the plans. **Proposed resolution:** (1) verify the M1-BREAKING tranche
is deployed to all live writers at runtime (not just code), then **flip M7 LANDED** in the codex + this ledger; (2)
execute or formally close the **M30.3** reader-legacy-fallback removal (it's gated on `READER_FELL_BACK_TO_LEGACY_PATH`=0/7d).
This single reconciliation reclassifies ~4 "alignment-needed" plan findings (perps/deribit/odds/master-catalogue) to aligned.

### MD2 ⚖️ — Databento allowlist hygiene (M21)

`master_data…catalogue` R5 smoke ledger probed `XNAS.ITCH` (not on the 3-dataset allowlist). **Resolution:** verify the
smoke log shows `assert_databento_request_allowed` raised `DatabentoDatasetNotAllowedError` *before* the network call (in
which case the guard works and it's just a noisy probe label → 🔧 fix the probe to `DBEQ.BASIC`); if it reached the
vendor, that's a real allowlist-bypass to fix. Operator confirm which.

### MD3 🔧 — Barchart-retired stale references (M22)

`tradfi_massive_dual_source` Operator-decision #3 (L53) + L180 + L386 still list Barchart in the `ohlcv_15m`
SOURCE_PRIORITY / valid-source set. → update to `[databento, massive, yahoo]`; VIX 15m is Databento XCBF.PITCH now.

### MD4 ⚖️ — Live-persistence interim deviation from the facade spine (M12/M13)

`prediction_venue_perps` runs live book_snapshot_5 through a **direct-GCS `LiveWebsocketTickSink`** because the
facade→Pub/Sub→warm-GCS subscription is **BLOCKED-CREDENTIALS**. Documented, but it's a standing deviation from the M12/M13
end-state. **Operator:** provision the Cloud-Storage subscription (un-block credentials) or accept + explicitly track the
interim. Also 🔧 verify SINK_MATRIX has the new cefi perp `book_snapshot` shards (M14) before any live launch.

### MD5 🔧 — Silent-capture / manifest-invisible risks (M4/M14/M16) — all self-tracked, close before trusting the data

`instruments_foundation` EXTENDED hardcoded-fallback→false-`captured` (P1) · `carry` `perp_daily_ctx` manifest-invisible
data_type · `instruments_mtds_subset` blank-reason `_af_record_empty` (P2) · `downstream_services` E5 CF-11 3-way logic
must be canonical before the cefi/tradfi/prediction rebuild scripts run. Each is correctly open in its plan; resolution =
land the fix before that plan's data is treated as honest-coverage ground truth.

### MD6 🔧 — Retired VENUE_FETCH_FAILED label in open re-fetch tasks (M10)

`path_to_100pct` + `data_completion` open CeFi re-fetch tasks name `VENUE_FETCH_FAILED` as the scoping label. It's
legacy-cell *identification*, not a new emission (no M10 writer violation). → relabel to "cells whose legacy
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
3. **MD4 ⚖️:** un-block the Pub/Sub Cloud-Storage subscription for live book_snapshot_5, or accept the documented direct-GCS interim.

Everything else (MD3, MD5–MD10) is mechanical and folds into the alignment pass alongside the IS edits.

## Progress Log

- **2026-06-29** — Doc created. Trust model carried from the IS reconciliation. Codex freshness checked (2 old docs:
  IS↔MTDS boundary 06-16, shard-isolation 05-17 — both pattern-stable, current-state drift flagged M30). **Section A
  M-ledger (M1–M29 + M30 stale flags) written** — contract-extraction verified every assertion against live
  market-tick-data-service + UAC code. 74 plans reference MTDS. Next: Section B triage + deep-read fan-out.
- **2026-06-29** — Section B triage + 15 cluster-agents deep-read **41 plans** against M1–M30. **Sections C + D written.**
  **Tally: 0 MAJOR-CONFLICT · 26 MINOR-DRIFT · 15 ALIGNED** — far cleaner than IS (the MTDS-specific axes are mature;
  the v10-MVP MAJORs were IS-side / honest-coverage overlap set-aside here). Findings collapse into 10 clusters (MD1–MD10).
  **Headline (MD1): the ledger/codex is probably the stale side on M7 + M30.3** — live writers already emit `live_<source>`
  (live_kalshi_perp / live_deribit / live_odds_api) and M1-BREAKING reports complete + `LIVE_WEBSOCKET` deleted fleet-wide,
  so M7 should likely flip IN-FLIGHT→LANDED and M30.3 reader-fallback removal should be executed/closed. **3 operator items**
  (MD1 M7/M30.3 flip · MD2 XNAS.ITCH allowlist verify · MD4 live book_snapshot_5 Pub/Sub subscription). Read-only pass;
  no subject plans edited. Companion to the IS reconciliation (committed `2ad201e18`).
