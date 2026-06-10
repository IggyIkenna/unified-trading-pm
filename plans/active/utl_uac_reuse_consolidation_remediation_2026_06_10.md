---
title: "UTL/UAC reuse consolidation — kill local reimplementations, strongest-combination merge"
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 18
estimate_calibrated_ai_days: 7.2
locked_by: live-defi-rollout
locked_since: 2026-06-10
related_plans:
  - plans/epics/infrastructure_master.md
  - plans/epics/strategy_master.md
  - plans/epics/features_and_ml_master.md
  - plans/epics/execution_master.md
  - plans/epics/orchestrator_master.md
---

# UTL/UAC Reuse Consolidation — Remediation

## What this is

A parallel-agent audit (2026-06-10) of all 18 service repos found code that **reimplements functionality UTL
(`unified_trading_library`) or UAC (`unified_api_contracts`) already provide**. This plan fixes every finding,
**critical → low**, using the **strongest-combination** of the local and canonical implementations for each conflict —
NOT a blind "delete local, use the lib". Three of the headline findings were deep-verified and the naive "it's a
duplicate" framing was **wrong** in important ways (see Phases 1, 3, 4); the merge decisions below reflect the verified
reality.

**Guiding rule (CLAUDE.md conflict-resolution SSOT):** _Align = the MERGED COMBINATION, never "take mine / take
theirs"._ Where two implementations both carry genuine work, keep both; where one is a strict superset, adopt it and
preserve the residual; where the lib lacks a load-bearing local control, **extend the lib first**, then delete local.

**Clean repos (audit found nothing actionable — do not touch):** market-data-processing-service, trading-agent-service,
fund-administration-service, ibkr-gateway-infra, batch-live-reconciliation-service, greeks-service (math is correctly
local; one trivial LOW stub only).

---

## Severity ledger (every finding, critical → low)

| #   | Sev      | Repo                               | Finding                                                                                                                | Merge decision (strongest combination)                                                                                                                                                                                                                                         | Phase |
| --- | -------- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----- |
| 1   | **CRIT** | strategy-service                   | `max(equity)` HWM + duplicate threshold engines across 3 risk modules                                                  | **Compose, don't delete.** UTL = rule-aggregation + fee-HWM SSOT; strategy = metric-computation + DeFi-monitoring + equity-drawdown-HWM SSOT. Dedupe the ONE twin helper; migrate the v2 legacy-portfolio-gate branch to UTL rules; keep all DeFi/VaR/staleness compute local. | 1     |
| 2   | HIGH     | alerting-service                   | `auth.py verify_api_key` hand-rolled, **wired in prod**                                                                | Delete `auth.py`; wire `create_api_auth("alerting-service")`                                                                                                                                                                                                                   | 2     |
| 3   | HIGH     | client-reporting-api               | `auth.py` dead parallel auth path (+ direct `google.oauth2`)                                                           | Delete dead file; live path already on `create_api_auth`                                                                                                                                                                                                                       | 2     |
| 4   | HIGH     | ml-service                         | local 689-ln `ModelRegistry` reimplements UTL `ModelRegistry`                                                          | **Extend UTL first** (writegate + manifest-emit + joblib allowlist), then delete local; adopting UTL fixes a latent manifest-match bug                                                                                                                                         | 3     |
| 5   | HIGH     | features-service                   | local `BuilderEntry`/`resolve_build_order` in 4 families + delta_one calc base                                         | mt/volatility/onchain = **drop-in**; sports = **extend UTL or resolver-only**; base.py = only `_boxcox_transform` clean-swap                                                                                                                                                   | 4     |
| 6   | HIGH     | execution-service                  | custody hand-rolls GCP/AWS secret-fetch branching; Solana provider GCP-only `gcs.Client`                               | Route to UTL `get_secret_client()` / `get_storage_client()`; KMS half stays local (no UTL equiv)                                                                                                                                                                               | 5     |
| 7   | HIGH     | agent-orchestrator                 | `gcs_sync.py` raw `boto3`+`google.cloud.storage`; `auth.py` gs:// secret fetch                                         | Route cloud I/O to UTL `get_storage_client()`/`get_secret_client()`; **keep** the custom HS256/ES256 JWT logic                                                                                                                                                                 | 5     |
| 7b  | MED      | unified-trading-api                | `middleware/auth.py` hand-rolled X-API-Key                                                                             | Migrate validation core to `create_api_auth`; keep gateway app_state wiring                                                                                                                                                                                                    | 2     |
| 8   | MED      | instruments-service                | `urdi_reference_provider.VenueError` local taxonomy                                                                    | Route classification through UAC `classify_venue_error()` / `VenueErrorClassification`                                                                                                                                                                                         | 6     |
| 9   | MED      | market-tick-data-service           | 11 CLI handlers fetch secrets via raw `secretmanager` + bare `except`                                                  | Replace with UTL `get_secret()`; removes the swallow + AWS-blind path                                                                                                                                                                                                          | 5     |
| 10  | MED      | MTDS + instruments-service         | near-identical hand-rolled HTTP retry/backoff base-adapters                                                            | No UTL retry helper exists → **add one UTL helper**, consolidate both                                                                                                                                                                                                          | 6     |
| 11  | MED      | execution-service                  | second hand-rolled `/health` in `api/app.py` alongside `make_health_router`                                            | Fold onto `make_health_router` + `data_freshness` (QG 5.62)                                                                                                                                                                                                                    | 6     |
| 12  | MED      | deployment-service/api             | VM-cron + builds scripts use `storage.Client()` directly                                                               | Route to UTL `get_storage_client()` (also fixes `_gcp_sdk` boundary bypass); `compute_v1` control-plane stays                                                                                                                                                                  | 5     |
| 13  | MED      | ml-service                         | `inference/types.py ModelMetadata` TypedDict                                                                           | **Dead code** (no importers) → delete                                                                                                                                                                                                                                          | 3     |
| 14  | LOW      | alerting-service                   | `Literal["WARNING","CRITICAL"]` in rules/                                                                              | Use UAC `AlertSeverity`                                                                                                                                                                                                                                                        | 7     |
| 15  | LOW      | agent-orchestrator                 | ~30 `os.environ.get` config reads; local `utcnow()`; no UTL event layer                                                | Migrate config to `UnifiedCloudConfig`; secrets via `get_secret_client()`; add `setup_events`/`log_event`                                                                                                                                                                      | 7     |
| 16  | LOW      | unified-trading-api                | `ANTHROPIC_API_KEY` from `os.environ`                                                                                  | Move to `get_secret_client()`                                                                                                                                                                                                                                                  | 7     |
| 17  | LOW      | greeks-service                     | `events.py` 3-line re-export stub                                                                                      | Delete; import `log_event` from UTL directly                                                                                                                                                                                                                                   | 7     |
| 18  | lint     | strategy-service                   | un-noqa'd `os.environ.get` in `recovery_event_helper.py`, `pnl/.../mock_data_provider.py`                              | `UnifiedCloudConfig` or noqa-with-reason                                                                                                                                                                                                                                       | 7     |
| 19  | lint     | MTDS + IS + execution + deployment | `from google.cloud import storage` / `os.environ` / `gs://` / `GOOGLE_CLOUD_PROJECT` in one-off `scripts/` (~70 files) | Ratchet tail — convert opportunistically; fix `GOOGLE_CLOUD_PROJECT`→`GCP_PROJECT_ID` where present                                                                                                                                                                            | 7     |

**Verified NON-findings (do NOT "fix" — agents confirmed no UTL/UAC equivalent):** greeks BSM kernel (UAC has only
delta-strike schemas), execution-service per-venue order circuit breaker (UTL's CB is DR-recovery tooling), batch-live
stage-grain recon schemas, trading-agent ephemeral ledger, ibkr TCP health probe, client-reporting-api
`core/hwm_seeds.py` (static seeds for UTL's three-method HWM — not a `max(equity)` reimpl).

---

## Phase DAG + gates

```
Phase 0 (guardrails) ─┬─> Phase 1 (strategy risk/HWM)        [independent]
                      ├─> Phase 2 (auth dedup ×3)             [independent]
                      ├─> Phase 3 (ml ModelRegistry)         [needs UTL extension → ship UTL first]
                      ├─> Phase 4 (features builder_registry)[sports needs UTL extension]
                      ├─> Phase 5 (cloud-SDK-direct ×4)       [independent]
                      └─> Phase 6 (venue-err / health / retry)[Phase 5 retry-helper feeds #10]
Phases 1-6 GREEN ─────> Phase 7 (LOW + lint tail) ─> Phase 8 (codex SSOT + archive)
```

Gate between phases: each repo touched reaches **C4** (`quality-gates.sh` Pass-1 green) before its todos flip, and is
shipped via `quickmerge --agent --files`. UTL/UAC extensions (Phases 3, 4, 6) are **MINOR bumps** that propagate by
range-pin pull — no consumer rebuild unless they cross `<1.0.0`.

---

## Phase 0 — Guardrails (do first)

- [ ] [AUDIT] P0. Add the cross-plan banner `> **🟡 IN-FLIGHT REFACTOR — UTL/UAC reuse consolidation**` to the 5 epic
      plans in `related_plans`, so concurrent slots don't re-touch the same risk/auth/registry surfaces.
- [ ] [VERIFY] P0. Snapshot pre-change behaviour: for strategy risk + ml registry + features builders, capture a
      golden-output fixture (one client risk eval, one inference-date model selection, one `resolve_build_order` per
      family) so each merge is provably behaviour-preserving, not just compiling.
- [ ] [SPEC] P0. Confirm UTL/UAC are the SSOT targets for every extension below and that no parallel old+new path is
      left behind (CLAUDE.md "delete deprecated code").

## Phase 1 — strategy-service risk/HWM (finding #1, CRITICAL) — COMPOSE, do not delete

> **Verified reality:** the three "duplicate engines" are the metric-**computation** layer; UTL `risk.rule_evaluator` /
> `risk_preflight` / `family_aggregator` is the **comparison/aggregation** layer (every input arrives pre-computed in
> `RuleEvalContext`). All three local engines are LIVE and feed the UTL gate — they are NOT superseded. UTL HWM
> (`post_trade.hwm_invariants`/`hwm_periods`) is **fee-crystallization HWM**, a different domain from the equity-curve
> drawdown peak — do **not** collapse them.

- [ ] [AGENT] P0. **Dedupe the twin threshold/equity helper.** `risk/core/risk_calculator.py` and
      `risk/engine/risk_metrics.py` carry near-identical `get_threshold_status` + equity/concentration/peak computation.
      Collapse to ONE shared pure helper (keep the **stateless** `risk_metrics` form for batch=live symmetry); have
      `RiskCalculator.calculate_drawdown` wrap it with its per-`client_id` peak dict. Preserve: per-client peak store,
      UAC `RiskMetrics`/`RiskStatus` assembly, `assert_client_allowed`.
- [ ] [AGENT] P0. **Migrate the one genuine same-layer duplication** —
      `risk/v2/preflight.py:226 _run_legacy_portfolio_gates` (daily-loss / drawdown / family-cap) → UTL `RiskRule`
      registry entries (`MaxDailyLossTrigger`/`MaxDrawdownTrigger` + a family-cap trigger). After migration the legacy
      `PortfolioContext` branch reduces to the **recon-staleness** check only (explicitly NOT a RiskRule — keep local).
- [ ] [AGENT] P0. **Route the 6 comparison checks through UTL rules** where the gate already runs: feed
      `pre_trade_check_engine.py`'s already-computed position_size/leverage/gross/net/concentration into UTL
      `evaluate_rule` so the threshold **numbers** have one SSOT (UAC caps), not `RiskLimits` config + UAC rules
      diverging. Preserve local: notional math (`_compute_notional_for_qty` inverse/linear), staleness, market-hours,
      cash-reserve, VaR (`_normal_quantile`), single-instrument + venue caps, `LimitCheckResult` reject contract.
- [x] ✅ [AGENT] P0. **Fix the local quality bug found in passing** — SHIPPED `strategy-service@67ecc156` | 60 risk
      tests ✓ | basedpyright 0 ✓ | full `quality-gates.sh` exit 0 ✓ | regression:
      `tests/risk/unit/test_pre_trade_check_engine.py::test_leverage_estimate_is_upnl_sensitive_not_constant`.
      `pre_trade_check_engine.py:579` used a hardcoded `equity = new_position_value / Decimal("5")` proxy → made
      leverage a **constant 5.0** for every book, so `leverage > max_leverage` could never fire. Extracted
      `account_equity_proxy()` in `risk_calculator.py` as the equity-formula SSOT (`value/maxlev + uPnL`, floored at 1);
      both `RiskCalculator.estimate_account_equity` and the pre-trade engine now use it; pre-trade bases equity on the
      **post-trade** value (neutral uPnL → `leverage == max_leverage` baseline preserved; negative uPnL → higher
      leverage → can breach). **This also delivers the first slice of the P0 "dedupe twin equity helper" above** (the
      equity-proxy formula is now single-sourced).

- [ ] [AGENT] P1. **Extract one local `equity_curve_drawdown()` helper** for the duplicated peak/max-drawdown loop in
      `engine/core/components/pnl_monitor.py:214-222` and `engine/core/output_builders.py:153-158`. Keep it **local**
      (do NOT route to UTL `hwm_invariants` — wrong domain). Leave fee-crystallization HWM to UTL `post_trade`.
- [ ] [AGENT] P2. Keep `risk/core/correlation_matrix.py` (instrument NxN) as-is — UTL `family_aggregator` only gives
      **family-level pairwise** rhos, a different axis/shape. Optional local cleanup: unify the 3 local correlation
      shapes (instrument-matrix / family-pairwise-dict / v2 nested-dict) — local typing only, not a UTL migration.
- [ ] [VERIFY] P0. Golden risk-eval fixture from Phase 0 reproduces identically; `quality-gates.sh` green; ship via
      quickmerge.

## Phase 2 — API auth dedup (findings #2, #3, #7b)

> **⚠️ ACCURACY CORRECTION (verified 2026-06-10 during execution — do NOT blind-swap):** UTL `create_api_auth`
> authenticates via **Bearer JWT + X-Service-Token (S2S) + DISABLE_AUTH only — it does NOT read `X-API-Key`** (the
> `AuthContext.is_api_key` field is unused; client-reporting-api's "X-API-Key (legacy)" comment refers to its OWN dead
> `auth.py`, not UTL). alerting-service `verify_api_key` and unified-trading-api `middleware/auth.py` authenticate via
> **`X-API-Key`**. So replacing them with `create_api_auth` as-is would **break every X-API-Key caller** (prod auth
> regression on alerting-service). The strongest-combination is **UTL-extension-first** (like Phase 3): add a 4th
> `X-API-Key` (legacy) path to `create_api_auth` validating against `UnifiedCloudConfig.api_key`, MINOR-bump UTL, THEN
> migrate the services. client-reporting-api (#3) is unaffected — it is pure dead-code deletion (already on the JWT/S2S
> path).

- [ ] [AGENT] P0. **UTL extension FIRST**: add an `X-API-Key` (legacy) branch to `cloud_interface/api_auth.py`
      `create_api_auth` — read the `X-API-Key` header, validate against `UnifiedCloudConfig().api_key`, return an
      internal/admin `AuthContext` (set `is_api_key=True`), 401 on missing/invalid. Preserves the existing JWT + S2S +
      DISABLE_AUTH paths. Ship as a UTL MINOR bump. (Prevents the prod-auth regression on the two X-API-Key services.)
- [ ] [AGENT] P0. **alerting-service** (depends on UTL extension above): delete `alerting_service/auth.py`
      (`verify_api_key` + DISABLE_AUTH guard); change `api/main.py` to depend on UTL
      `create_api_auth("alerting-service")`. Verify an `X-API-Key` caller still authenticates (it is **wired in
      production**). Highest urgency of the three.
- [ ] [AGENT] P0. **client-reporting-api** (no UTL extension needed — pure dead-code deletion): delete the dead
      `client_reporting_api/auth.py` (`verify_api_key` + `verify_service_token` + `GoogleOAuthMiddleware`). Live path
      (`api/main.py` + `auth_standardized.py`) already uses `create_api_auth` / `create_s2s_auth_dependency`. Deleting
      it also removes the direct `google.oauth2`/`google.auth` SDK import (`_google_auth_sync.py`/`auth.py:123`). Grep
      for any residual importers of the dead module before deleting.
- [ ] [AGENT] P1. **unified-trading-api** (depends on UTL extension above): migrate `middleware/auth.py` X-API-Key
      validation core to UTL `create_api_auth(...)`'s new legacy path; preserve the gateway-specific mock/app_state
      wiring (the only local-specific bit).
- [ ] [VERIFY] P0. Auth smoke per repo (200 with valid **X-API-Key**, 200 with Bearer JWT / X-Service-Token, 401
      without, DISABLE_AUTH refused in prod mode); `quality-gates.sh` green; quickmerge each.

## Phase 3 — ml-service ModelRegistry (findings #4, #13) — EXTEND UTL FIRST

> **Verified reality:** walk-forward selection (`get_model_for_inference_date`) and the GCS storage layout /
> MANIFEST_PATH are **byte-identical** between local and UTL — zero reconciliation needed there. BUT local carries
> load-bearing controls UTL lacks, and local has a latent bug UTL does not.

- [ ] [AGENT] P0. **Carry into UTL `ModelRegistry` (ship UTL MINOR bump first):**
  - [ ] `store_model` writegate — `training_completeness_fraction` param +
        `_check_emission_policy`/`publish_with_policy` BLOCK_CRITICAL gate (suppresses partial-coverage model writes +
        P0 alert). Data-correctness invariant.
  - [ ] `store_model` availability-manifest emission — `ManifestWriter.add(...).write()` with `job_id`.
  - [ ] `load_model` joblib **trusted-prefix allowlist** (`_ALLOWED_JOBLIB_PREFIXES`) — keep UTL's `expected_sha256`
        integrity param too (strongest combination = both).
- [ ] [AGENT] P0. **Adopt UTL's correct manifest-match** — local `get_model_metadata`/`_upsert_version` test
      `... or training_period == ""` (`:531`,`:646`) returns the WRONG version from cache; UTL's `== training_period` is
      correct. Consolidating onto UTL **fixes** this for ml-service.
- [ ] [AGENT] P0. **Audit the local-only escape hatches before deleting:** `CLOUD_PROVIDER=local` no-bucket guard + AWS
      S3 bucket fallback (`ml_models_s3_bucket`) + `None`-on-miss error contract. If any ml-service test or AWS
      deployment depends on them, add the equivalent local/S3 path to UTL first; else confirm `config.ml_source_bucket`
      is always set on the training path.
- [ ] [AGENT] P0. Delete `ml_service/training/ml/model_registry.py`; repoint `training_orchestrator.py`,
      `final_training_handler.py`, `model_loader.py` (loader already uses UTL) to
      `from unified_trading_library import     ModelRegistry`.
- [ ] [AGENT] P1. Delete the **dead** `inference/types.py:ModelMetadata` TypedDict (no importers; the live
      `ModelMetadata` everywhere is the UTL dataclass).
- [ ] [VERIFY] P0. Golden inference-date selection fixture reproduces; writegate still blocks a partial-coverage write;
      `quality-gates.sh` green for UTL + ml-service; quickmerge.

## Phase 4 — features-service builder_registry + calc base (finding #5)

> **Verified reality:** mt/volatility/onchain `BuilderEntry` field sets are identical (onchain just omits
> `lookback_candles`, UTL default `0` reproduces it) and all four `resolve_build_order` bodies are semantically
> identical to UTL's. **sports is genuinely divergent** (function-based builders, `columns`/`required_inputs`/
> `default_kwargs`, no `calculator_name`/`sources`). In `delta_one/app/calculators/base.py` **only `_boxcox_transform`
> is a clean 1:1 swap**; `calculate_zscore` (rolling) and element-wise `calculate_time_since` have **no UTL
> equivalent**.

- [ ] [AGENT] P1. **Drop-in migrate** mt, volatility, onchain: delete local `BuilderEntry` + `resolve_build_order`
      (incl. `_build_dag`/`_kahn_bfs`) → `from unified_trading_library import BuilderEntry, resolve_build_order` (match
      the already-shipped calendar/delta_one pattern). Keep `_build_registry`/`get_builder`; volatility keeps its
      orthogonal `_CALCULATOR_CLASS_MAP`.
- [ ] [AGENT] P1. **sports — resolver-only migration now** (safe: `depends_on`-based, identical semantics):
      `resolve_build_order()` → `_utl_resolve_build_order(_get_registry())`. **Do NOT blind-swap the dataclass.**
- [ ] [DESIGN] P2. **sports dataclass — operator/design call**: either (a) add a UTL `FunctionBuilderEntry` sibling
      (callable + `columns` + `required_inputs` + `default_kwargs`), or (b) keep sports' local function-based dataclass.
      Default to (b) unless a 2nd function-based consumer appears (YAGNI).
- [ ] [AGENT] P2. **delta_one base.py — surgical, not wholesale**: migrate `_boxcox_transform` → UTL
      `transformations.boxcox_transform` (adapt the `1e-8` vs `+1` edge-shift) and DELETE local. Leave
      `calculate_time_since` (element-wise log/lookback), `calculate_time_to_next`, rolling `calculate_zscore`,
      `normalize_bounded_metric`/`_logit_transform`, `safe_rolling_metric` (richer than UTL `calculate_rolling_stats`),
      and `normalize_distribution` (boxcox-inclusive, tuple-vs-series mismatch) **local** — UTL has no 1:1. The
      `FeatureCalculator(ABC)` validate/enrich pipeline stays local.
- [ ] [AGENT] P3. **Fix the mis-marked bucket inline** found in passing: `volatility/io/writer.py:35`
      `bucket = f"features-volatility-{ag}-{pid}"` is marked `# CORRECT-LOCAL` but is a genuine miss → use
      `resolve_bucket_name(kind="features-volatility", asset_group=...)` (its own sibling configs already do).
- [ ] [VERIFY] P1. `resolve_build_order` golden output identical per family; `quality-gates.sh` green; quickmerge.

## Phase 5 — Cloud-SDK-direct → UTL cloud_interface (findings #6, #7, #9, #12)

- [ ] [AGENT] P1. **execution-service**: `custody/cloud_kms.py:118` + `custody/withdrawal_signing.py:37` — replace the
      hand-rolled GCP/AWS secret-fetch branching with UTL `get_secret_client()`. **Keep** the KMS Decrypt half (no UTL
      equivalent). `providers/solana_amm_depth_provider.py:281` — replace GCP-only `gcs.Client` blob loop with UTL
      `get_storage_client()`/`io.download_parquet` (fixes the AWS-blind correctness/portability bug).
- [ ] [AGENT] P1. **agent-orchestrator**: `server/gcs_sync.py:30` raw `boto3`+`google.cloud.storage` → UTL
      `get_storage_client()` (already cloud-agnostic incl. S3). `server/auth.py:99` gs:// secret fetch → UTL
      `get_storage_client()`/`get_secret_client()`. **Keep the HS256/ES256 JWT signing logic** (intentional custom per
      orchestrator-auth SSOT — touch only the cloud-fetch).
- [ ] [AGENT] P1. **market-tick-data-service**: replace the raw `secretmanager.SecretManagerServiceClient()` + bare
      `except Exception` in the 11 CLI handlers (`perp_funding_handler.py:214,225`, `dex_swaps_handler.py:345`,
      `gas_fee_handler.py:110,447`, `evm_defi_handler.py:459`, `dex_pools_handler.py:364`,
      `aggregator_route_handler.py:385`, `lending_indices_handler.py:333`, `lst_rates_handler.py:687`,
      `liquidations_handler.py:218`) with UTL `get_secret()` (cloud-agnostic, no swallow, matches the documented adapter
      convention).
- [ ] [AGENT] P2. **deployment-service / deployment-api**: route the GCS-storage `storage.Client()` calls in
      `scripts/vm/{vm_log_archival_cron,vm_serial_capture_cron,vm_zombie_watchdog,validate_vm_prefix_mapping}.py` and
      `deployment_api/routes/{builds_history,builds}.py` + `services/shard_detail.py:828` through UTL
      `get_storage_client()` (also fixes the repo's own `_gcp_sdk` boundary bypass). **Keep** `compute_v1` VM
      control-plane (no UTL abstraction exists yet) and pubsub/secretmanager liveness probes.
- [ ] [VERIFY] P1. Per repo: secret fetch + GCS read still work against emulator/mock; `quality-gates.sh` green;
      quickmerge.

## Phase 6 — Venue-error, health router, retry helper (findings #8, #10, #11)

- [ ] [AGENT] P1. **instruments-service**: route `engine/urdi_reference_provider.py:42 VenueError` classification
      through UAC `classify_venue_error()` → `VenueErrorClassification` (single-source retryable/permanent with the
      adapters). Keep the `VenueFetchResult` orchestration wrapper.
- [ ] [AGENT] P2. **execution-service**: fold the second hand-rolled `/health`+`/ready`+`/readiness` in `api/app.py:209`
      onto UTL `make_health_router(...)` with a `data_freshness` callback (QG STEP 5.62), so the service has ONE health
      surface (the canonical `api/main.py` already uses it).
- [ ] [AGENT] P2. **Add a UTL retry helper** (none exists today) — a single `unified_trading_library.utils` exponential
      backoff-on-(429/5xx/Connection/Timeout/OSError) helper — then consolidate the two near-identical hand-rolled
      base-adapter retries: MTDS `market_interface/base_adapter.py:29-100` and instruments-service
      `reference_data/base_adapter.py:39-160`. Ship the UTL helper (MINOR) first.
- [ ] [VERIFY] P1. Adapter retry behaviour unchanged (mock 429 → N retries → classify); health endpoints respond;
      `quality-gates.sh` green; quickmerge.

## Phase 7 — LOW + lint tail (findings #14–#19)

- [ ] [AGENT] P2. **alerting-service**: replace `Literal["WARNING","CRITICAL"]` in `rules/connectivity_rules.py:58`,
      `rules/reconciliation_rules.py:81,163,251` with UAC `AlertSeverity` (already imported elsewhere in the service).
- [ ] [AGENT] P2. **agent-orchestrator**: migrate the ~30 `os.environ.get` config reads to a `UnifiedCloudConfig`
      subclass; move secret-bearing ones (`TELEGRAM_BOT_TOKEN`, JWT secret) to `get_secret_client()`; add UTL
      `setup_events`/`log_event` lifecycle emission (the repo emits none today). Local `utcnow()`/`to_utc()` may stay
      (thin tz-aware wrappers) but replace `logging.basicConfig` call sites. **Scope-flag:** orchestrator is partly
      intentionally standalone — migrate config/secrets/events, do not blanket-rewrite the custom dashboard auth.
- [ ] [AGENT] P3. **unified-trading-api**: move `routes/chat.py:258 ANTHROPIC_API_KEY` off `os.environ` to
      `get_secret_client()`. The `# config-bootstrap`-marked `os.environ` reads in `main.py`/health/reporting are
      sanctioned bootstrap — leave.
- [ ] [AGENT] P3. **greeks-service**: delete the `greeks_service/events.py` 3-line re-export stub; import `log_event`
      from UTL at the call sites.
- [ ] [AGENT] P3. **strategy-service**: noqa-with-reason (or `UnifiedCloudConfig`) the un-annotated `os.environ.get` in
      `recovery_event_helper.py:41,90` and `pnl/engine/mock_data_provider.py:38` (mirror the existing
      `position/engine/mock_data_provider.py` noqa pattern).
- [ ] [AGENT] P3. **lint ratchet tail (opportunistic, not blocking)**: in MTDS/IS/execution/deployment one-off
      `scripts/` (~70 files), convert `from google.cloud import storage` → `get_storage_client()`, `gs://` →
      `resolve_bucket_name`, per-object `gsutil`/`gcloud` subprocess → UTL `gcs_copy/delete/describe_object`, and fix
      the banned env name `GOOGLE_CLOUD_PROJECT` → `GCP_PROJECT_ID` (`cleanup_kraken_spot_empty_confirmed.py:96`,
      `cleanup_may4_bait_sentinels.py:117`, MTDS `cleanup_*`). These are QG-baselined; counts only go down.
- [ ] [VERIFY] P2. `quality-gates.sh` green per touched repo; ratchet baselines decrease (never increase); quickmerge.

## Phase 9 — Service↔service dependency violations + DEAD enforcement gate (operator sweep 2026-06-10)

> Operator-requested sweep found **4 service→service path-dep edges** that the documented HARD RULE
> (`codex/04-architecture/tier-and-import-architecture.md` § "No service ↔ service imports") forbids — live on the
> integration branch because **the QG gate is dead**: `base-service.sh:615` invokes
> `unified-trading-pm/scripts/check-no-service-deps.py` but the file is at `scripts/validation/check-no-service-deps.py`
> → the `[ -f ]` guard is false → **the check never runs, fleet-wide**; and even if pathed, `get_service_repos()`
> matches only `type=="service"` (misses `api-service`/`batch-service`/`api`). The sweep surfaced THREE distinct classes
> — fix each correctly, do NOT blanket-force HTTP boundaries.

- [ ] [AGENT] P1. **DEAD-GATE FIX (do this LAST — after the violations below are remediated, else it red-walls the 3
      repos):** correct `base-service.sh` to invoke `scripts/validation/check-no-service-deps.py`, AND broaden
      `get_service_repos()` to treat `type ∈ {service, api-service, batch-service, api}` as deployable services (keep
      `library`/`infrastructure`/`tool`/`devops`/`ui`/`test-harness` as non-service). Extend the check to also catch a
      raw `import <other_service>` in source/tests (not just `[tool.uv.sources]` path deps) — the current check is
      path-dep-only. Roll out via PM SSOT; unit-test the broadened classifier. SSOT:
      `codex/04-architecture/tier-and-import-architecture.md`.
- [ ] [AGENT] P1. **TRUE VIOLATION — deployment-api → strategy-service** (`routes/treasury_routes.py:27` imports
      `compute_unified_nav` + `compute_nav_by_client` from `strategy_service.position.core.treasury_monitor`; the DTOs
      are already correctly in UAC `internal.domain.treasury`). **Relocate the two pure NAV-rollup functions to UTL**
      (`unified_trading_library.treasury/`, which exists); strategy-service + deployment-api both import from UTL. (Or,
      if they need live position state, deployment-api calls strategy-service's treasury HTTP endpoint.) Removes the
      service→service edge.
- [ ] [AGENT] P1. **MISCLASSIFICATION — deployment-api → deployment-service is NOT a real violation**:
      deployment-service is functionally a deployment **engine/library** (`deployments_registry`,
      `cloud-providers.yaml`, terraform, VM launchers), consumed as a package by deployment-api (6 files import
      `deployment_service.deployments_registry`). **Fix the manifest `type` for deployment-service → library/engine**
      (not `service`) so the gate correctly treats the API↔engine pairing as legitimate. Do NOT force an HTTP boundary
      between an API and its own engine. Confirm deployment-service is not independently run as a live service before
      reclassifying.
- [ ] [AGENT] P2. **market-data-processing-service → market-tick-data-service** (`app/core/canonical_writer.py:59`
      imports `market_tick_data_service.market_interface.adapters.tradfi.databento_classifier`, currently
      `# noqa:     qg-deep-import`). Relocate the shared `databento_classifier` to UTL/UAC (it is
      reference-classification logic, a library concern), or have MDPS consume the classification via the contract.
      Removes the cross-service deep-import.
- [ ] [AGENT] P2. **strategy-service → market-tick-data-service** (test-only:
      `tests/position/integration/     test_split_libraries.py`
      `importorskip("market_tick_data_service.market_interface")`). Per the contract-test rule, rewrite the integration
      test to assert against the UAC `market_interface` contract + a mock/fake, then **drop the
      `market-tick-data-service` path-dep from strategy-service `pyproject.toml`** — removing the test-only dep that
      gates every strategy-service ship (the root cause of the 2026-06-10 dirty-MTDS ship-block).
- [ ] [VERIFY] P1. After all four edges are resolved + classifications fixed, enable the gate (todo 1) and confirm
      `check-no-service-deps.py` exits 0 fleet-wide; add a regression unit test per fixed edge.

## Phase 8 — Codex SSOT + archive (HARD RULE)

- [ ] [AUDIT] P1. Update codex for every contract this plan changes: `codex/06-coding-standards/README.md`
      (reuse-before-reimplement rule + the new UTL retry helper), `codex/04-architecture/agent-orchestrator-overview.md`
      (cloud I/O via UTL; auth-fetch only), `codex/09-strategy/operational/pnl-attribution.md` (strategy
      equity-drawdown-HWM is local + distinct from UTL fee-crystallization HWM — record the NON-finding so a future
      audit doesn't re-flag it), and the ml model-registry doc (UTL is SSOT; writegate/manifest/allowlist now in UTL).
- [ ] [AUDIT] P1. Record the **verified NON-findings** list (greeks BSM, execution order-CB, hwm_seeds, etc.) in the
      relevant codex docs so the next reuse audit doesn't re-open them.
- [ ] [VERIFY] P1. Remove the Phase-0 in-flight banners; run plan-hygiene + active-inventory regen; archive per the
      5-step HARD RULE once all repos hit C5.

---

## Success criteria (per phase → C4 minimum, plan archives at C5 all-repos)

| Phase | Done when                                                                                                                                 |
| ----- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | golden risk-eval identical; 3 engines compose with UTL gate; `/5` bug fixed; no `max(equity)` collapsed into UTL HWM                      |
| 2     | 3 repos depend on `create_api_auth`; hand-rolled `auth.py` deleted; no direct `google.oauth2`                                             |
| 3     | UTL `ModelRegistry` carries writegate+manifest+allowlist; local registry + dead TypedDict deleted; manifest-match bug gone                |
| 4     | mt/vol/onchain on UTL `BuilderEntry`; sports resolver on UTL; only `_boxcox_transform` swapped in base.py; volatility bucket via resolver |
| 5     | no `boto3`/`google.cloud`/raw `secretmanager` in service runtime of the 4 repos (scripts tail tracked separately)                         |
| 6     | `classify_venue_error` single-sources IS venue errors; execution has ONE health surface; one UTL retry helper, two adapters consolidated  |
| 7     | UAC `AlertSeverity` used; orchestrator on `UnifiedCloudConfig`+events; stubs/lint cleared; ratchet baselines down                         |
| 8     | codex updated for every changed contract + NON-findings recorded; banners removed; archived per HARD RULE                                 |

## Notes for the worker

- **MINOR-bump-first ordering:** Phases 3, 4, 6 add to UTL/UAC — ship the lib bump, let the range-pin pull carry it,
  then migrate consumers. Don't edit consumer + lib in a way that needs a coordinated MAJOR.
- **Behaviour-preserving is the bar:** every merge is verified against the Phase-0 golden fixture, not just "compiles".
- **Commit + Push + Flip each shippable unit in the same turn** (CLAUDE.md HARD RULE) — one checkbox per `quickmerge`.
- Paste `SUB_AGENT_MANDATORY_RULES.md` for any sub-agent fan-out within a phase.
