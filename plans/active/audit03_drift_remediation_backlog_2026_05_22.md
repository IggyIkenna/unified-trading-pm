---
name: audit03_drift_remediation_backlog
title: "AUDIT-03 remediation — confirmed P1/P2 drift backlog (non-P0, non-decision)"
type: active
parent_epic: defi_master
assigned_vm: vm-defi
estimate_class: refactor
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 1.6
status: active
priority: P1
created: 2026-05-22
last_updated: 2026-05-22
locked_by: live-defi-rollout
source: audits/audit-files/audit_03_defi_archetypes_e2e.md (§6 + §6.1 re-verification ledger)
gate: none (independent cleanups; not on the May-23 critical path but all Opus-confirmed real)
---

# AUDIT-03 remediation — confirmed P1/P2 drift backlog

Home for every AUDIT-03 finding that is **Opus-confirmed real** but is NOT a May-23 P0 (those are in the carry-safety
and cron-provisioning plans) and NOT a judgment/decision (those route to Ikenna — see
`plans/active/issues/audit03_ikenna_review_routing_2026_05_22.md`). Grouped by theme; items are largely independent and
PARALLEL-safe across themes. This gives every confirmed finding a plan home (replaces its `Plan: TBD`).

## Theme 1 — P&L attribution: honest emission + canonical schema (strategy-service pnl/engine + UAC)

- [ ] [AGENT] P1. **F-17** — Emit canonical `PnLAttributionRow` (with `factor: PnLFactor` + `layer: PnLLayer`) instead
      of the free-form `PnLBreakdown` (`account_id` string). The canonical types EXIST in UAC `internal/risk.py`
      (PnLFactor = 16-member StrEnum) — this is emit-path adoption, not type creation. Affects ALL archetypes' P&L
      row-level attribution.
- [ ] [AGENT] P1. **F-16** — Emit pre-TGE points rows honestly as
      `CARRY_ISSUER_SEASONAL value_eth=0 points_pending=true` instead of silently `continue`-ing them
      (`reward_attribution.py:159`).
- [ ] [AGENT] P1. **F-46** — Make `FillAttributionContext.archetype_id` required (`str`, not `str | None`) + add
      `config_variant` field (`rows.py:62`); prevents `None` → unqueryable per-archetype attribution.
- [ ] [AGENT] P2. **F-19** — Replace the synthetic 1bps funding-PnL surrogate (`abs(net_qty)·last_price·0.0001`,
      `pnl_input_builder.py:198`) with `position_qty × funding_rate × interval` from actual funding events.
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
- [ ] [AGENT] P1. **F-37b** (narrowed + relocated) — Genuine residual = the
      `catalogue_bucket = f"strategy-store-{project_id}"` inline bucket-NAME construction in
      `hedge_ratio_writer.py:136` + `decision_context_writer.py:149` (both already import `resolve_bucket_name` and use
      it on L92 for the data bucket — only the catalogue bucket is hand-built). **The
      `gcs_storage_service.py:185/251/293` + `grid_generator.py:100` `gs://` strings are NOT violations** — they are
      `# noqa: gs-uri`-exempt display URIs built from an already-resolved bucket (`resolve_bucket_name` wired by
      `strategy_execution_contract_remediation_2026_05_20.md` todo 4a ✅). **This item is folded into that plan
      (best-of-both) — see its AUDIT-03 follow-up todo. Tracked there, not here.**
- [ ] [AGENT] P1. **F-37a** — Change `category="defi"` → `asset_group="defi"` in `record_captured()` calls
      (`hedge_ratio_writer.py:142`, `decision_context_writer.py:155`) per the asset-group vocabulary rule.
- [x] ✅ [AGENT] P2. **F-30** — Remove Infura (a removed provider) from the resolvable RPC fallback chain
      (`config/chain_config.yaml` 6 chains + `rpc_fallback.py:179`). — execution-service@42447632a; infura removed from
      all 11 chains in chain_config.yaml; docstring + test assertions updated to remove infura references.

## Theme 3 — custody + DeFi credential safety (execution-service)

- [ ] [AGENT] P1. **F-24** — Add `health_check() -> CustodyHealth` to the `CustodyProvider` protocol
      (`custody/base.py`) + all 4 impls (cloud_kms/mock/copper/ceffu); codex requires ping-60s / balance-5min. Composes
      the RSK-08 custody-disconnect breaker.
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

- [ ] [AGENT] P1. **F-03** — Wire a strategy-audit GCS writer (today strategy decisions go to local
      `events/strategy_decisions.jsonl` only via `DomainEventLogger`; no GCS persist). Acked PRE_CUTOVER.
- [ ] [AGENT] P1. **F-05** — Provision the `audit-records` GCS bucket in terraform with object versioning +
      retention-lock (currently resolved at runtime via `resolve_bucket_name(kind="audit-records")` but never
      provisioned).
- [ ] [AGENT] P2. **F-04** — Align the execution-audit path layout (`audit_log.py:67`, flat
      `audit/{client_id}/{date}/{event_type}/`) with codex's events-stream layout — minor (date/ext already match; only
      the segment layout differs).

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
- [ ] [AGENT] P3. **F-20 residual** — Delete the dead `.extra/features-onchain-service` +
      `.extra/features-delta-one-service` dependency-checker copies (the LIVE `features-service/onchain` already reads
      `capture_status` correctly — §6.1 REFUTED on live path). Verify nothing deploys `.extra` before deleting.
- [ ] [AGENT] P3. **NICE-TO-HAVE (risk review)** — Add a dedicated LST-depeg `CircuitBreakerId` ladder mirroring the
      `STABLECOIN_DEPEG_{WARNING,SMALL,MODERATE,CATASTROPHIC}` tiers. The shipped `DEFI_LST_DEPEG_STETH_5PCT` scenario
      (carry plan F-33, uac@56594ab3) trips the generic `DRAWDOWN_DAILY_BPS` breaker; stablecoins got their own depeg
      ladder, LSTs should too for tiered (warn/scale-down/cancel/kill) response. Provenance: AUDIT-03 F-33 inline
      execution 2026-05-22.

## Success criteria

- Each themed batch: C4 (quality-gates Pass 1) GREEN in its repo; the corresponding AUDIT-03 §6 finding flipped.
- No new hardcoded bucket/URL/price constants; QG STEPs 5.69/5.70 clean.
- Custody liveness observable; no silent mock-signing path; Hyperliquid key cleared on disconnect.

**Full-execution criterion**: each code fix is C4 + the finding re-checked against AUDIT-03 §2.x and flipped in §6/§6.2.
No real-infra full-run required for this backlog except F-05 (terraform apply of the audit bucket — verify
`gcloud storage buckets describe` shows versioning ENABLED + retention policy).
