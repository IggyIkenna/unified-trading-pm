---
title: Issue-docs remediation sweep — code-fixable items across the 2026-05/06 issue-doc backlog
created: 2026-06-02
author: ikenna (slot 7)
parent_epic: master_to_live_defi_2026_05_23.md
priority: P1
status: IN-FLIGHT — slot 7 executing; items flip + source issue docs archive as each is verified complete
locked_by: live-defi-rollout
locked_since: 2026-06-02
estimate_class: brand-new
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4
source:
  - plans/active/issues/alerting_fp_rate_analysis_2026_05_23.md
  - plans/active/issues/api_host_chronic_impairment_2026_05_29.md
  - plans/active/issues/batch_live_reconciliation_service_audit_2026_05_27.md
  - plans/active/issues/cefi_processed_candles_manifest_file_disconnect_2026_05_25.md
  - plans/active/issues/defi_code_codex_drift_2026_05_27.md
  - plans/active/issues/deployment_scripts_bucket_softdelete_log_churn_2026_06_01.md
  - plans/active/issues/features_service_defi_data_loading_blockers_2026_05_29.md
  - plans/active/issues/fleet_audit_triad_deferred_followups_2026_06_01.md
  - plans/active/issues/gcs_hive_partition_malformed_paths_remediation_2026_06_01.md
  - plans/active/issues/mdps_state_adapter_leading_nan_audit_2026_05_29.md
  - plans/active/issues/running_vm_fleet_status_2026_05_27.md
  - plans/active/issues/uniswap_v3_ethereum_28k_attempted_failed_2026_05_28.md
---

## Why this exists

A 2026-06-02 (slot 7) code-audit of every `plans/active/issues/*.md` doc verified each open claim against current code
(with git-log dates, since docs predate today). Outcome: a large fraction of "open" items were **already fixed in code**
after the docs were written; what remains is consolidated here as canonical `- [ ]` todos so it is dispatchable +
auditable in one place. This tracker IS the dispatch (per CLAUDE.md "the plan todo is the dispatch"). Items flip to
`- [x] ✅ — <repo>@<sha>` per Commit+Push+Flip; each **source issue doc is archived the moment ALL of its items here are
verified complete**.

**Exclusions (NOT credential-blocked — explicitly out of scope):**

- **Tardis paid key** — operator non-activation (the one acknowledged credential blocker). No other "credential /
  no-data / no-API" framing is accepted as a blocker; all such items below are reframed as actionable.
- **R2** (tradfi v9 migrator zero-row guard) — being done elsewhere.
- **R3** (deployment-service `test_sports_tier3_fixture_diagnostic` time-of-day flake) — reported in-flight by another
  agent; NOT yet on `origin/live-defi-rollout` as of 2026-06-02 (no `timedelta`, 0 incoming). Left out to avoid
  collision; **pick up if their fix does not land.**

## Status taxonomy in this doc

`- [ ]` actionable now · `BLOCKED-DISCIPLINE` (single-walk / HOLD banner) · `BLOCKED-OPERATOR-DECISION` · `NEEDS-LIVE`
(operator-gated infra run, not credentials).

---

## agent-orchestrator (integration base = `main`)

- [x] ✅ [CODE] P1. agent-orchestrator: add `PRAGMA busy_timeout=30000` in `server/db.py` `_on_connect()` — prevents
      DB-locked cascades after an OOM-induced restart. — agent-orchestrator@`1fe3386`. Source:
      api_host_chronic_impairment.
- [x] ✅ [INFRA] P2. agent-orchestrator: provision a 16 GiB swapfile (new `scripts/orchestrator/ensure_swap.sh`,
      idempotent + `vm.swappiness=10`) wired as STEP 2.5 in `scripts/bootstrap_vm.sh` — belt-and-braces against the
      32–57 GiB pytest OOM on the API host. — agent-orchestrator@`1fe3386`. Source: api_host_chronic_impairment.

## market-data-processing-service — MDPS leading-NaN workstream (operator chose Option A + carry-from-prior-day)

- [ ] [CODE] P0. MDPS: add `state_col: str | None` + `flow_cols` kwargs to `base_adapter._finalize_session_grid` (per
      issue-doc §Scope items 1–3). Source: mdps_state_adapter_leading_nan.
- [ ] [CODE] P0. MDPS: add prior-day carry-seed logic to `_finalize_session_grid` (Decision 1 — seed leading bins from
      last-known price/ts instead of dropping). Source: mdps_state_adapter_leading_nan.
- [ ] [CODE] P0. MDPS: wire the 7 state adapters to call `_finalize_session_grid(output, state_col=…)` —
      cefi/derivative, cefi/futures_chain, cefi/options_chain, defi/liquidity, defi/market_state, cefi/book_snapshot,
      tradfi/tbbo. Source: mdps_state_adapter_leading_nan.
- [ ] [TEST] P0. MDPS: add leading-gap + prior-day-carry + cold-start-drop + density tests
      (`tests/unit/test_state_adapter_density.py` + extend per-adapter tests). Source: mdps_state_adapter_leading_nan.
- [ ] [VERIFY] P0. MDPS: remove the NaN WARN diagnostic in `fast_candle_aggregation.py:304-318` ONLY after all 7
      adapters fixed + full MDPS suite green. Source: mdps_state_adapter_leading_nan.

## batch-live-reconciliation-service

- [ ] [CODE] P1. BLRS: register the resolution router in `api/main.py` AND rename prefix `/reconciliation` → `/t1-recon`
      (R1 + D4) — resolution endpoints are currently unreachable at runtime. Source:
      batch_live_reconciliation_service_audit.
- [ ] [CODE] P1. BLRS: add `drawdown_pct` + `fill_rate_min` orchestrator green gates alongside the existing
      `bps_delta_max` (D3 — operator ruled "build all three"). Source: batch_live_reconciliation_service_audit.
- [ ] [CODE] P2. BLRS: wire `stage2_strategy_recon` to the strategy-service/position query API as the canonical position
      baseline (D2) instead of raw GCS event archives. Source: batch_live_reconciliation_service_audit.
- [ ] [CODE] P2. BLRS: implement `soak_mode` in `ReconConfig` (+ alerting-service CRITICAL-suppression counterpart)
      (G4). Source: batch_live_reconciliation_service_audit.
- [ ] [CODE] P2. BLRS: build `analysis/threshold_distribution.py` (bps gate analyzer over past `summary_*.json`) (G5).
      Source: batch_live_reconciliation_service_audit.

## unified-api-contracts

- `BLOCKED-DISCIPLINE` [CODE] P1. UAC: registry key drift in `registry/market_data_categories.py` — `"dex_pools"`/
  `"dex_swaps"` → `"dex_pool_state"`/`"dex_pool_swaps"`. RECLASSIFIED 2026-06-02 (was "risk LOW" in the audit — WRONG):
  a consumer audit found the legacy keys are STILL live across MTDS source (`engine/orchestrator.py:621`,
  `cli/handlers/schema_validation.py`, `market_interface/adapters/defi/uniswap_v3_adapter.py`, `solana_defi_handler.py`,
  migration scripts). Renaming the registry keys standalone would break
  `needs_candle_processing`/timeframe/schema-validation lookups mid-migration. The rename is the coordinated
  registry-alignment scope of `defi_manifest_canonicalisation_2026_06_01.md` §C0-RD (operator-locked SSOT
  `defi-canonical-naming-ssot.md`). Do NOT do standalone. Source: defi_code_codex_drift D14.
- [x] ✅ [DOC] P2. UAC: add OHLC-semantics docstring to the `swaps_ohlcv_*` schema in
      `internal/schemas/_candle_contracts.py` — O/H/L/C = USD-normalized pool spot price (`amountUSD/|base_amount|`),
      ≈1.0 for USDC/WETH, 3 fallback methods. — unified-api-contracts@`455ddf9a`. Source: features_service_defi #3.
- [ ] [CODE] P2. UAC venue-registry coherence (`registry/.../defi_venues.py` + `_defi.py`) — **BLOCKED-OPERATOR-DECISION
      per option**: (a) D15 HYPERLIQUID/ASTER `pipeline`→`live` (handler actively collects — code-reality-aligned, will
      implement unless vetoed); (b) D10 EULER_V2/VENUS/BENQI/RADIANT `live` with no `PROTOCOL_CAPABILITIES` → downgrade
      to `pipeline` (conservative) OR add caps; (c) D8 Starknet `infura_compatible` template rename vs document; (d)
      SOLAYER/PICASSO/CAMBRIAN register in `ALL_DEFI_VENUES` or drop caps. Source: defi_code_codex_drift.
- `BLOCKED-DISCIPLINE` [CODE] P2. UAC: drop duplicate cols `swap_count`/`volume_quote_usd` from `_DEX_EXT` — MUST bundle
  into the C0 migration walk (single-walk discipline), NOT standalone. Source: features_service_defi #4.
- `BLOCKED-DISCIPLINE` [CODE] P1. UAC: `FEATURE_GROUP_DATA_TYPE_OVERRIDES["defi"]` → `dex_pool_swaps` — coordinate with
  C2 data walk landing (reading-path mapping must not lead the on-disk canonicalisation). Source: features_service_defi
  #1.

## features-service

- [ ] [CODE] P1. features-service: in `delta_one/app/core/data_loader.py`, filter processed-candle manifest reads by
      `service_name="market-data-processing-service"` to eliminate the MTDS raw-tick `captured` false-positive. Source:
      cefi_processed_candles_manifest_file_disconnect.
- [ ] [CODE] P3. features-service: delete the dead `DEFI_DATA_TYPE_OVERRIDES` dict in
      `delta_one/engine/orchestrator.py:103-120` (UAC `resolve_data_type_for_feature_group()` is the real router).
      Source: features_service_defi.

## market-tick-data-service

- [x] ✅ [CODE] P1. MTDS: remove banned `bloxroute` relay URLs (`cli/handlers/mev_events_handler.py`) + delete the
      tracked `mev_events_handler.py.bak`. — market-tick-data-service@`d3e02228` (ruff+basedpyright clean). Source:
      defi_code_codex_drift D7.
- [ ] [SCRIPT] P2. MTDS: add a QG lint guard that fails on malformed `by_date/` paths not matching
      `^raw_tick_data/by_date/day=\d{4}-\d{2}-\d{2}/`. Source: gcs_hive_partition.
- `BLOCKED-DISCIPLINE` [CODE] P2. MTDS: extend `scripts/sweep_phantom_manifest_rows.py` for the raw-trade
  `captured`-with-no-processed-candle phantom class — RECLASSIFIED 2026-06-02: pruning those rows is a whole-corpus GCS
  walk that MUST bundle into the cefi C0 canon walk (single-walk discipline), NOT a standalone sweep. The read-side
  false-positive is instead killed by the features-service `service_name` filter below. Source: cefi_processed_candles.

## alerting-service

- [ ] [CODE] P2. alerting-service: wire `AlertCode.RISK_RULE_BLOCKED` / `RISK_RULE_MONITOR_FIRED` into
      `rules/risk_threshold_rules.py` output (CRITICAL→BLOCKED, WARNING→MONITOR_FIRED). Source: alerting_fp_rate.
- [ ] [CODE] P2. alerting-service: add structured GCS quietness-report emission
      (`events/alerting-service/{date}/quietness-{run_id}/report.jsonl`: alert_code/fires/suppressed/fp_count/
      fp_rate/threshold). Source: alerting_fp_rate.
- [ ] [CODE] P1. alerting-service: publish `RECON_FREEZE_ARMED` from `rules/reconciliation_rules.py` on CRITICAL/SEV0 so
      execution-service arms the order block (G12; mirrors observability_master:73). Source:
      batch_live_reconciliation_service_audit.
- `BLOCKED-OPERATOR-DECISION` [DATA] P3. alerting-service: ML threshold baseline for the 5 `ml_*` codes (ML inference
  not yet live) + `tick_staleness_seconds` per-venue baseline (needs live MTDS feeds). Source: alerting_fp_rate.

## unified-trading-api

- [ ] [CODE] P2. unified-trading-api: `services/pbm_performance.py:46` → call strategy-service/position pnl route
      instead of the dead `http://position-balance-monitor:8080`; clean stale `workspace-manifest.json:1570` PBMS
      stanza. Source: batch_live_reconciliation_service_audit §9.2.

## deployment-service

- [ ] [INFRA] P1. deployment-service: schedule `scripts/vm/cleanup_old_tarballs.py` (currently 0 schedule refs) via a
      Cloud Run Job + Cloud Scheduler `--keep 5`, `terraform/gcp/tarball_cleanup_scheduler.tf` following the
      `manifest_consolidator_scheduler.tf` pattern; add an `owner/cadence/verifier/last_executed` runbook block. Source:
      deployment_scripts_bucket.
- [ ] [DOC] P2. deployment-service: fix cosmetic ASCII-art bucket labels in `docs/DEPLOYMENT_GUIDE.md` +
      `DEPLOYMENT_GUIDE_FEMI.md` (~L391-393) to env-tiered names. Source: gcs_hive_partition.

## unified-trading-pm — codex / doc-drift

- [ ] [DOC] P2. PM: flip the D14 checkbox in `defi_code_codex_drift` + audit-result doc, update
      `codex/.../defi-data-types-catalog.md` body + `defi-canonical-naming-ssot.md` fan-out rows (code shipped
      MTDS@0a3a7071). Source: defi_code_codex_drift D14.
- [ ] [DOC] P2. PM: fix stale repo names in `codex/04-architecture/data-flow-map.md`
      (`trading-analytics-api`→`unified-trading-api`, `trading-analytics-ui`→`unified-trading-system-ui`). Source:
      batch_live_reconciliation_service_audit §7.
- [ ] [DOC] P3. PM: add a "NOT YET DEPLOYED — tofu apply pending" warning to
      `codex/05-infrastructure/vm-log-archival.md` (cron authored but not applied). Source: fleet_audit_triad.
- [ ] [DOC] P3. PM: B2 codex marker reconciliation — replace `zero_activity=True` / `ZERO_ACTIVITY_BAR` with
      `staleness_seconds>0 + trade_count==0` in `honest-absence-downstream-handling.md` +
      `live-pipeline-architecture.md` (no code consumers — pure doc drift). Source: fleet_audit_triad.
- [ ] [DOC] P1. PM: write `codex/06-coding-standards/adapter-finalization-contract.md` + a per-adapter density section
      in `honest-absence-downstream-handling.md` (after the MDPS workstream lands). Source:
      mdps_state_adapter_leading_nan.

## Operator-gated infra (NOT credentials — ADC admin perms exist; runs after code lands)

- [ ] [INFRA] P1. `tofu apply` the `tarball_cleanup_scheduler` (after TF authored above). Source:
      deployment_scripts_bucket.
- [ ] [INFRA] P2. `tofu apply` `vm_log_archival_scheduler.tf` + `vm_serial_capture_scheduler.tf` +
      `api_host_auto_reboot.tf`; verify `apply_resource_limits.sh` (MemoryMax=56G) is live on the API host. Source:
      fleet_audit_triad + api_host_chronic_impairment.
- [ ] [INFRA] P2. deployment-scripts bucket: add prefix-scoped lifecycle rules (`vm-logs/`>14d, `log-archive/`>90d) +
      cross-bucket soft-delete bloat audit via `gcs_bucket_stats.py --bloat_pct`. Source: deployment_scripts_bucket.

## BLOCKED clusters (NOT credentials — discipline / coordination)

- **DeFi/TradFi backfill VM cluster** — uniswap_v3 28k retry, tradfi 712-day reprocess, MDPS cefi backfill, the C0/C2
  DeFi-manifest walk. `BLOCKED-DISCIPLINE`: gated on the harsh-side `cefi_manifest_canonicalisation_2026_06_01` HOLD
  banner + the operator directive to "run all chain-affected venues together, not piecemeal". Code for these is already
  on LDR; only the coordinated live run remains. Do NOT cross the HOLD.
- **stash-archive purge** (`shared_stash_pile_archive_cleanup`) — time-gated to 2026-06-08; not actionable today.

## Per-source-doc archive criterion

A source issue doc archives to `plans/archive/issues/` (with `[unlock-plan]` in the commit for locked docs) once
**every** item it contributed here is `- [x] ✅` or carries an operator-acked `BLOCKED-*`/`NEEDS-LIVE` line. Docs gated
on a BLOCKED cluster (cefi_processed_candles, uniswap_28k, fleet_audit_triad, running_vm_fleet, shared_stash) stay open
with updated status until their cluster clears.
