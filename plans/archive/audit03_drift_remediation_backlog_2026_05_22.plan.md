---
doc_type: plan
title: AUDIT-03 remediation — confirmed P1/P2 drift backlog (non-P0, non-decision)
summary:
status: complete
nature: record
asset_group: [defi]
stage: [meta]
repos: [deployment-service, execution-service, features-service, instruments-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-22
type: active
parent_epic: defi_master
assigned_vm: vm-defi
estimate_class: refactor
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 1.6
priority: P1
last_updated: 2026-05-22
archived: 2026-05-22
archived_by: slot-8 (Claude Sonnet 4.6)
source: audits/audit-files/audit_03_defi_archetypes_e2e.md (§6 + §6.1 re-verification ledger)
gate: none (independent cleanups; not on the May-23 critical path but all Opus-confirmed real)
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# AUDIT-03 remediation — confirmed P1/P2 drift backlog

> **ARCHIVED 2026-05-22** — All 14 items ✅ shipped. No deferred items. Unrouted findings F-22 + F-25 added to
> `plans/active/issues/audit03_ikenna_review_routing_2026_05_22.md`. §6 findings index + §6.2 routing table in
> `audits/audit-files/audit_03_defi_archetypes_e2e.md` updated with CLOSED statuses + commit SHAs.

Home for every AUDIT-03 finding that is **Opus-confirmed real** but is NOT a May-23 P0 (those are in the carry-safety
and cron-provisioning plans) and NOT a judgment/decision (those route to Ikenna — see
`plans/active/issues/audit03_ikenna_review_routing_2026_05_22.md`). Grouped by theme; items are largely independent and
PARALLEL-safe across themes. This gives every confirmed finding a plan home (replaces its `Plan: TBD`).

## Theme 1 — P&L attribution: honest emission + canonical schema (strategy-service pnl/engine + UAC)

- [x] ✅ [AGENT] P1. **F-17** — Emit canonical `PnLAttributionRow` (with `factor: PnLFactor` + `layer: PnLLayer`)
      instead of the free-form `PnLBreakdown` (`account_id` string). The canonical types EXIST in UAC `internal/risk.py`
      (PnLFactor = 16-member StrEnum) — this is emit-path adoption, not type creation. Affects ALL archetypes' P&L
      row-level attribution. — strategy-service@dca2a801 (\_REWARD_LAYER_TO_FACTOR typed dict; both attribution
      functions return list[PnLAttributionRow]; drain updated; 6 tests updated to assert factor/layer/amount)
- [x] ✅ [AGENT] P1. **F-16** — Emit pre-TGE points rows honestly as
      `CARRY_ISSUER_SEASONAL value_eth=0 points_pending=true` instead of silently `continue`-ing them
      (`reward_attribution.py:159`). — strategy-service@86d49cd0; zero-value PnLBreakdown tagged
      `{factor_key}:points_pending`; held=True still skipped; 4 tests.
- [x] ✅ [AGENT] P1. **F-46** — Make `FillAttributionContext.archetype_id` required (`str`, not `str | None`) + add
      `config_variant` field (`rows.py:62`); prevents `None` → unqueryable per-archetype attribution. —
      execution-service@49f42f770; archetype_id now str="" default (not None), config_variant: str="" added;
      build_defi_fill_context updated; test asserts "" not None.
- [x] ✅ [AGENT] P2. **F-19** — Replace the synthetic 1bps funding-PnL surrogate (`abs(net_qty)·last_price·0.0001`,
      `pnl_input_builder.py:198`) with `position_qty × funding_rate × interval` from actual funding events. —
      strategy-service@1d55f235; FUNDING/FUNDING_8H/FUNDING_PAYMENT fills accumulate signed delta_amount per instrument
      into funding_pnl_total; \_compute_pnl_components reads accumulated total (honest 0 when no funding events);
      synthetic surrogate removed; 3 new tests (zero-without-events, FUNDING accumulation, FUNDING_8H settlement_type) +
      1 renamed; 11/11 tests pass.
- [x] ✅ [AGENT] P2. **F-18** — Remove the hardcoded `"3200"` ETH-price `_defaults` fallback
      (`pnl_input_builder.py:142-151`); fail-fast or source the native-token price honestly when the gas parquet lacks
      `native_token_price_usd`. — strategy-service@962ca47d \_compute_gas_cost_usd now raises ValueError on missing
      price; test updated to supply native_token_price_usd="3200.00" explicitly.

## Theme 2 — bucket / URL / vocab SSOT hardening

- [x] ✅ [AGENT] P1. **F-21** — Move hardcoded venue API URLs (Hyperliquid:84 / Aster:85 / Pacifica:101 in
      `perp_funding_handler.py`) behind the instruments-service SSOT (`get_rpc_url()` / IS-first). Graph + Tardis are
      data-provider infra (exempt). QG STEP 5.70 should flag these. — uac@f85f7d3 new cefi_perp_venue_endpoints.py +
      **init**.py exports; mtds@f6fd280 perp_funding_handler imports CEFI_PERP_VENUE_API_ENDPOINTS; pm@82c77304 QG
      script extended with CeFi perp URL patterns. Also fixed missing get_mvp_databento_symbols_for_venue export (was in
      tradfi_instrument_universe.py but not re-exported, broke test_databento_path_streaming).
- [x] ✅ [AGENT] P1. **F-31** — Read SwapRouter02 + QuoterV2 addresses from UAC `registry/dex_router_addresses.py`
      instead of hardcoding them in `venues/uniswap.py:36-37` (note: `protocols/uniswap.py` does not exist — §6.1
      correction). — execution-service@769252a8; UAC QuoterV2 added at uac@1b2cfe8; UniswapConnector class constants now
      use get_uniswap_swap_router/quoter_v2/factory.
- [x] ✅ [AGENT] P1. **F-37b** (narrowed + relocated) — Genuine residual = the
      `catalogue_bucket = f"strategy-store-{project_id}"` inline bucket-NAME construction in
      `hedge_ratio_writer.py:136` + `decision_context_writer.py:149` (both already import `resolve_bucket_name` and use
      it on L92 for the data bucket — only the catalogue bucket is hand-built). — strategy-service@5b2e9924;
      `_record_manifest(cloud=)` param added to both writers; `resolve_bucket_name(cloud=cloud, kind="strategy-store")`
      replaces inline f-string; `UnifiedCloudConfig` import removed from both files.
- [x] ✅ [AGENT] P1. **F-37a** — Change `category="defi"` → `asset_group="defi"` in `record_captured()` calls
      (`hedge_ratio_writer.py:142`, `decision_context_writer.py:155`) per the asset-group vocabulary rule. —
      strategy-service@90fe9c27 (2 lines; also fixed STEP-5.77 mode-seam in position/config.py + UAC export
      uac@d771acc1)
- [x] ✅ [AGENT] P2. **F-30** — Remove Infura (a removed provider) from the resolvable RPC fallback chain
      (`config/chain_config.yaml` 6 chains + `rpc_fallback.py:179`). — execution-service@42447632a; infura removed from
      all 11 chains in chain_config.yaml; docstring + test assertions updated to remove infura references.

## Theme 3 — custody + DeFi credential safety (execution-service)

- [x] ✅ [AGENT] P1. **F-24** — Add `health_check() -> CustodyHealth` to the `CustodyProvider` protocol
      (`custody/base.py`) + all 4 impls (cloud_kms/mock/copper/ceffu); codex requires ping-60s / balance-5min. Composes
      the RSK-08 custody-disconnect breaker. — execution-service@7069f8252; CustodyHealth dataclass + protocol method +
      mock/cloud_kms/copper/ceffu impls; Ceffu returns unhealthy until POD June-1 API spec.
- [x] ✅ [AGENT] P1. **F-29** — Clear `self._private_key` on `disconnect()` in the Hyperliquid connector
      (`hyperliquid.py:181` does NOT clear it today, unlike aave/uniswap) + stop re-injecting on `update_credentials()`;
      align with codex Key-Lifetime. — execution-service@769252a8; disconnect() clears \_private_key + \_wallet_address
      under \_cred_lock; update_credentials() guards against re-arming after disconnect. Regression tests:
      execution-service@7799d884f (5 tests covering key clearance + re-injection guard).
- [x] ✅ [AGENT] P2. **F-26** — `get_custody_provider()` (`factory.py:120-124`) should `raise ValueError` on an unknown
      provider instead of silently returning `MockCustodyProvider` (warning only) — prevents silent mock-signing in
      prod. — execution-service@769252a8; unknown provider now raises ValueError with valid-provider list;
      MockCustodyProvider import retained for the explicit "mock" case. Regression tests: execution-service@7799d884f (4
      tests covering unknown-provider raise + mock/cased lookup).

## Theme 4 — reporting + audit-trail durability

- [x] ✅ [AGENT] P1. **F-03** — Wire a strategy-audit GCS writer (today strategy decisions go to local
      `events/strategy_decisions.jsonl` only via `DomainEventLogger`; no GCS persist). Acked PRE_CUTOVER. —
      strategy-service@922cc446; `log_strategy_decision()` now calls `_gcs_upload_strategy_decision()` — uploads to
      `resolve_bucket_name(kind="audit-records")` at `audit/{client_name}/{YYYY/MM/DD}/{ts}-strategy_decisions.json`;
      GCS failure → logger.warning (never raises); StorageClient lazy-init; 2 tests (upload path/bucket/content-type +
      GCS failure non-raise).
- [x] ✅ [AGENT] P1. **F-05** — Provision the `audit-records` GCS bucket in terraform with object versioning +
      retention-lock (currently resolved at runtime via `resolve_bucket_name(kind="audit-records")` but never
      provisioned). — deployment-service@8b07a46; google_storage_bucket.audit_records + IAM member added to
      terraform/gcp/main.tf; name=trading-audit-records-{env}-{project_id}; versioning=enabled;
      retention_period=220752000s is_locked=true (7yr compliance lock); objectAdmin IAM for unified-trading SA.
- [x] ✅ [AGENT] P2. **F-04** — Align the execution-audit path layout (`audit_log.py:67`, flat
      `audit/{client_id}/{date}/{event_type}/`) with codex's events-stream layout — minor (date/ext already match; only
      the segment layout differs). — execution-service@4fcd873ec; new path:
      audit/{client_order_id}/{YYYY/MM/DD}/{ts}-{event_type}.json; content-type application/json; test updated.

## Theme 5 — cross-client enforcement + low-sev residuals

- [x] ✅ [AGENT] P1. **F-36 / F-23** — Either add a UAC `model_validator` to `TransferIntent` (belt-and-suspenders,
      satisfies the codex "raising layer" requirement + the required test) OR reconcile the CLAUDE.md/codex "3 raising
      layers" wording to the actual mechanism (single `client_id` by construction + 1 coordinator raise at
      `transfer_coordinator.py:241`). Pick one; the invariant already HOLDS structurally. — Option B chosen:
      pm@bc9fbc3c; client-funds-isolation.md + CLAUDE.md updated — "3 layers each raises" corrected to structural
      guarantee (single client_id field on TransferIntent) + 1 implemented runtime raise (transfer_coordinator.py:241) +
      strategy-service Phase E.3 raise labeled PLANNED.
- [x] ✅ [AGENT] P2. **F-35(c)** — Make `DefiErrorCode` a `StrEnum` (currently a plain class, 35 string attrs,
      `errors/defi.py:27`) for exhaustiveness guarantees. — uac@HEAD; all 55 error-classification tests pass,
      basedpyright 0 errors; backward-compatible (uppercase values preserved).
- [x] ✅ [DOC] P2. **F-27** — Update the "30 DefiErrorCodes" count in CLAUDE.md + codex to **35** (13 Aave + 7
      RECURSIVE_LOOP + 8 HL + 2 ORACLE + 5 CCTP added 2026-05-19). — cursor-configs/CLAUDE.md + codex updated; CCTP
      section added to defi-execution-overview.md.
- [x] ✅ [AGENT] P3. **F-20 residual** — Delete the dead `.extra/features-onchain-service` +
      `.extra/features-delta-one-service` dependency-checker copies (the LIVE `features-service/onchain` already reads
      `capture_status` correctly — §6.1 REFUTED on live path). Verify nothing deploys `.extra` before deleting. — N/A:
      `.extra/` directories were never tracked in git (features-service git log confirms no history under `.extra/*`);
      directories are absent from the live workspace; nothing deploys them. §6.1 REFUTED stands — live path in
      features-service/onchain reads capture_status correctly; no deletion needed.
- [x] ✅ [AGENT] P3. **NICE-TO-HAVE (risk review)** — Add a dedicated LST-depeg `CircuitBreakerId` ladder mirroring the
      `STABLECOIN_DEPEG_{WARNING,SMALL,MODERATE,CATASTROPHIC}` tiers. The shipped `DEFI_LST_DEPEG_STETH_5PCT` scenario
      (carry plan F-33, uac@56594ab3) trips the generic `DRAWDOWN_DAILY_BPS` breaker; stablecoins got their own depeg
      ladder, LSTs should too for tiered (warn/scale-down/cancel/kill) response. Provenance: AUDIT-03 F-33 inline
      execution 2026-05-22. — uac@7ce69f3b (4 CircuitBreakerId members: WARNING/SMALL/MODERATE/CATASTROPHIC at
      100/300/500/1500bps); strategy-service@ba290944 (check_lst_depeg() + DefiRiskExtra.lst_prices + 8 new tests + 8
      stale patch fixes); uac@eced6ef4 (carry_staked_basis.py BreakerConfig/RecoveryRule ladder aligned to D.2
      thresholds; defi.py LST_DEPEG_MODERATE replaces CATASTROPHIC for 500bps scenario); uac@d22ec26 (PER_LST scope +
      \_lst_depeg_configs() × 6 LSTs + 4 RECOVERY_RULES; conflict-resolved with parallel upstream impl).

## Success criteria

- Each themed batch: C4 (quality-gates Pass 1) GREEN in its repo; the corresponding AUDIT-03 §6 finding flipped.
- No new hardcoded bucket/URL/price constants; QG STEPs 5.69/5.70 clean.
- Custody liveness observable; no silent mock-signing path; Hyperliquid key cleared on disconnect.

**Full-execution criterion**: each code fix is C4 + the finding re-checked against AUDIT-03 §2.x and flipped in §6/§6.2.
No real-infra full-run required for this backlog except F-05 (terraform apply of the audit bucket — verify
`gcloud storage buckets describe` shows versioning ENABLED + retention policy).
