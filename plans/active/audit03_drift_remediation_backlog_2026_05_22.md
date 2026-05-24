---
name: audit03_drift_remediation_backlog
title: "AUDIT-03 remediation — confirmed P1/P2 drift backlog (non-P0, non-decision)"
type: active
parent_epic: defi_master
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

- [x] ✅ [AGENT] P1. **F-17** — Emit canonical `PnLAttributionRow` (with `factor: PnLFactor` + `layer: PnLLayer`)
      instead of the free-form `PnLBreakdown` (`account_id` string). The canonical types EXIST in UAC `internal/risk.py`
      (PnLFactor = 16-member StrEnum) — this is emit-path adoption, not type creation. Affects ALL archetypes' P&L
      row-level attribution. — strategy-service@dca2a801 (feat(pnl): F-17 adopt PnLAttributionRow in reward attribution,
      backfilled 2026-05-24)
- [x] ✅ [AGENT] P1. **F-16** — Emit pre-TGE points rows honestly as
      `CARRY_ISSUER_SEASONAL value_eth=0 points_pending=true` instead of silently `continue`-ing them
      (`reward_attribution.py:159`). — strategy-service@86d49cd0 (fix(reward-attribution): F-16 emit zero-value row,
      backfilled 2026-05-24)
- [x] ✅ [AGENT] P1. **F-46** — Make `FillAttributionContext.archetype_id` required (`str`, not `str | None`) + add
      `config_variant` field (`rows.py:62`); prevents `None` → unqueryable per-archetype attribution. —
      execution-service@49f42f770 (fix(pnl_attribution): archetype_id required str + config_variant added, backfilled
      2026-05-24)
- [x] ✅ [AGENT] P2. **F-19** — Replace the synthetic 1bps funding-PnL surrogate (`abs(net_qty)·last_price·0.0001`,
      `pnl_input_builder.py:198`) with `position_qty × funding_rate × interval` from actual funding events. —
      strategy-service@1d55f235 (fix(pnl): F-19 replace synthetic surrogate with real funding accumulation, backfilled
      2026-05-24)
- [x] ✅ [AGENT] P2. **F-18** — Remove the hardcoded `"3200"` ETH-price `_defaults` fallback
      (`pnl_input_builder.py:142-151`); fail-fast or source the native-token price honestly when the gas parquet lacks
      `native_token_price_usd`. — strategy-service@962ca47d (refactor(pnl): fail-fast on missing native_token_price_usd,
      backfilled 2026-05-24)

## Theme 2 — bucket / URL / vocab SSOT hardening

- [x] ✅ [AGENT] P1. **F-21** — Move hardcoded venue API URLs (Hyperliquid:84 / Aster:85 / Pacifica:101 in
      `perp_funding_handler.py`) behind the instruments-service SSOT (`get_rpc_url()` / IS-first). Graph + Tardis are
      data-provider infra (exempt). QG STEP 5.70 should flag these. — market-tick-data-service@f6fd280b
      (refactor(perp_funding): source HL/Aster/Pacifica URLs from UAC registry CEFI_PERP_VENUE_API_ENDPOINTS, backfilled
      2026-05-24)
- [x] ✅ [AGENT] P1. **F-31** — Read SwapRouter02 + QuoterV2 addresses from UAC `registry/dex_router_addresses.py`
      instead of hardcoding them in `venues/uniswap.py:36-37` (note: `protocols/uniswap.py` does not exist — §6.1
      correction). — execution-service@98ae2116d (protocols/uniswap.py + venues/uniswap.py both wired to UAC)
- [ ] [AGENT] P1. **F-37b** (narrowed + relocated) — Genuine residual = the
      `catalogue_bucket = f"strategy-store-{project_id}"` inline bucket-NAME construction in
      `hedge_ratio_writer.py:136` + `decision_context_writer.py:149` (both already import `resolve_bucket_name` and use
      it on L92 for the data bucket — only the catalogue bucket is hand-built). **The
      `gcs_storage_service.py:185/251/293` + `grid_generator.py:100` `gs://` strings are NOT violations** — they are
      `# noqa: gs-uri`-exempt display URIs built from an already-resolved bucket (`resolve_bucket_name` wired by
      `strategy_execution_contract_remediation_2026_05_20.md` todo 4a ✅). **This item is folded into that plan
      (best-of-both) — see its AUDIT-03 follow-up todo. Tracked there, not here.**
- [x] ✅ [AGENT] P1. **F-37a** — Change `category="defi"` → `asset_group="defi"` in `record_captured()` calls
      (`hedge_ratio_writer.py:142`, `decision_context_writer.py:155`) per the asset-group vocabulary rule. —
      strategy-service@90fe9c27 (fix(carry_staked_basis): F-37a category→asset_group + STEP-5.77 mode-seam noqa,
      backfilled 2026-05-24)
- [x] ✅ [AGENT] P2. **F-30** — Remove Infura (a removed provider) from the resolvable RPC fallback chain
      (`config/chain_config.yaml` 6 chains + `rpc_fallback.py:179`). — execution-service@42447632a
      (refactor(rpc-fallback): remove infura from all chain fallback lists, backfilled 2026-05-24)

## Theme 3 — custody + DeFi credential safety (execution-service)

- [x] ✅ [AGENT] P1. **F-24** — Add `health_check() -> CustodyHealth` to the `CustodyProvider` protocol
      (`custody/base.py`) + all 4 impls (cloud_kms/mock/copper/ceffu); codex requires ping-60s / balance-5min. Composes
      the RSK-08 custody-disconnect breaker. — execution-service@6063cc320 (custody/base.py CustodyHealth + protocol
      method, backfilled 2026-05-24)
- [x] ✅ [AGENT] P1. **F-29** — Clear `self._private_key` on `disconnect()` in the Hyperliquid connector
      (`hyperliquid.py:181` does NOT clear it today, unlike aave/uniswap) + stop re-injecting on `update_credentials()`;
      align with codex Key-Lifetime. — execution-service@6063cc320 + test_hyperliquid_key_lifetime.py added (backfilled
      2026-05-24)
- [x] ✅ [AGENT] P2. **F-26** — `get_custody_provider()` (`factory.py:120-124`) should `raise ValueError` on an unknown
      provider instead of silently returning `MockCustodyProvider` (warning only) — prevents silent mock-signing in
      prod. — execution-service@6063cc320 + test_factory.py::test_unknown_provider_raises_value_error (backfilled
      2026-05-24)

## Theme 4 — reporting + audit-trail durability

- [x] ✅ [AGENT] P1. **F-03** — Wire a strategy-audit GCS writer (today strategy decisions go to local
      `events/strategy_decisions.jsonl` only via `DomainEventLogger`; no GCS persist). Acked PRE_CUTOVER. —
      strategy-service@922cc446 (feat(logging): F-03 wire GCS audit writer for strategy decisions, backfilled
      2026-05-24)
- [x] ✅ [AGENT] P1. **F-05** — Provision the `audit-records` GCS bucket in terraform with object versioning +
      retention-lock (currently resolved at runtime via `resolve_bucket_name(kind="audit-records")` but never
      provisioned). — deployment-service@8b07a46 (infra(terraform): F-05 provision audit-records GCS bucket with
      versioning + 7yr retention lock, backfilled 2026-05-24)
- [x] ✅ [AGENT] P2. **F-04** — Align the execution-audit path layout (`audit_log.py:67`, flat
      `audit/{client_id}/{date}/{event_type}/`) with codex's events-stream layout — minor (date/ext already match; only
      the segment layout differs). — execution-service@4fcd873ec (fix(audit_log): F-04 align execution-audit GCS path to
      codex events-stream layout, backfilled 2026-05-24)

## Theme 5 — cross-client enforcement + low-sev residuals

- [x] ✅ [AGENT] P1. **F-36 / F-23** — Either add a UAC `model_validator` to `TransferIntent` (belt-and-suspenders,
      satisfies the codex "raising layer" requirement + the required test) OR reconcile the CLAUDE.md/codex "3 raising
      layers" wording to the actual mechanism (single `client_id` by construction + 1 coordinator raise at
      `transfer_coordinator.py:241`). Pick one; the invariant already HOLDS structurally. — PM@bc9fbc3c5 (docs(codex):
      F-36/F-23 reconcile client-funds-isolation to actual code — 2 layers, not 3; CLAUDE.md updated to reflect actual
      mechanism, backfilled 2026-05-24)
- [x] ✅ [AGENT] P2. **F-35(c)** — Make `DefiErrorCode` a `StrEnum` (currently a plain class, 35 string attrs,
      `errors/defi.py:27`) for exhaustiveness guarantees. — unified-api-contracts@e8094607 (refactor(errors): convert
      DefiErrorCode plain class to StrEnum, backfilled 2026-05-24)
- [x] ✅ [DOC] P2. **F-27** — Update the "30 DefiErrorCodes" count in CLAUDE.md + codex to **35** (13 Aave + 7
      RECURSIVE_LOOP + 8 HL + 2 ORACLE + 5 CCTP added 2026-05-19). — PM@e4e099b6e (MASTER_READINESS codex updated
      2026-05-24; workspace CLAUDE.md + defi-execution-overview.md already correct)
- [x] ✅ [AGENT] P3. **F-20 residual** — Delete the dead `.extra/features-onchain-service` +
      `.extra/features-delta-one-service` dependency-checker copies (the LIVE `features-service/onchain` already reads
      `capture_status` correctly — §6.1 REFUTED on live path). Verify nothing deploys `.extra` before deleting. — N/A:
      `.extra` directories absent from workspace (verified 2026-05-24 — not present in features-service worktree,
      already removed)

## Success criteria

- Each themed batch: C4 (quality-gates Pass 1) GREEN in its repo; the corresponding AUDIT-03 §6 finding flipped.
- No new hardcoded bucket/URL/price constants; QG STEPs 5.69/5.70 clean.
- Custody liveness observable; no silent mock-signing path; Hyperliquid key cleared on disconnect.

**Full-execution criterion**: each code fix is C4 + the finding re-checked against AUDIT-03 §2.x and flipped in §6/§6.2.
No real-infra full-run required for this backlog except F-05 (terraform apply of the audit bucket — verify
`gcloud storage buckets describe` shows versioning ENABLED + retention policy).
