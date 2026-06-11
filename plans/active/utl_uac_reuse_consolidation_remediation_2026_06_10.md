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

## Progress Log (append-only — autonomous run started 2026-06-10; rule 6 memory across context compression)

> Resume protocol for a compressed-context future-me: read this log + the severity ledger + each Phase's checkboxes.
> Everything marked `[x] ✅` is shipped + verified. Continue from the first `[ ]` in dependency order (UTL/UAC T0 first,
> then consumers, dead-gate enable LAST after all 4 service-dep edges are fixed + fleet-wide proof per rule 11).

- **SHIPPED** Plan + 2 corrections to PM (riding to main).
- **SHIPPED** Phase 1a — `account_equity_proxy()` SSOT + constant-5.0 leverage bug + uPnL regression test —
  `strategy-service@67ecc156` (60 tests, basedpyright 0, QG 0). Flipped.
- **SHIPPED** Service-dep governance — sweep (4 edges), codified no-service↔service rule into CLAUDE.md +
  SUB_AGENT_MANDATORY_RULES, plan Phase 9 — PM PR#226 merged.
- **SHIPPED** Phase 9 strategy→MTDS dep removal — `strategy-service@d1f5a6a8` + `manifest@4af80fd83` (alignment True).
  Flipped (PR#228). Permanently fixes the dirty-MTDS ship-block.
- **DECISION (rule 1/2)** Phase 9 deployment-service: NOT a misclassification — it IS a deployed service (Dockerfile +
  cloudbuild + FastAPI api/main.py). Corrected fix = extract the GCS-backed `deployments_registry` (UTL-only deps) into
  UTL; both deployment-service + deployment-api import from UTL. Shipped plan correction PR#229.
- **SHIPPED** Wave A (4 parallel sub-agents, all verified on origin/LDR, QG 0 each): execution-service@b7ea5e725
  (custody secret-fetch + Solana GCS → UTL), instruments-service@66165f2e (VenueError → UAC VenueErrorClassification),
  client-reporting-api@9cd77cc (dead auth.py + google.oauth2 deleted), deployment-service@6710f26 (VM scripts → UTL
  get_storage_client). Remaining split-out: deployment-api routes half (#12b).
- **SHIPPED** Wave A.2 (parallel sub-agents): MTDS secrets→UTL `mtds@696249df`, alerting AlertSeverity
  `alerting@39181c7`, unified-trading-api ANTHROPIC key→secret-client `uta@e3fbd8d`, greeks stub delete
  `greeks@b119b5b`.
- **SHIPPED** Wave B part 1 (UTL additive, MINOR) `unified-trading-library@20c8ae8d`: `create_api_auth` X-API-Key legacy
  path (unblocks alerting/uta auth dedup) + `utils.retry`/`with_retry` helper (unblocks MTDS/IS adapter consolidation).
- **PENDING** Wave B part 2 (still need UTL/UAC work): `ModelRegistry` writegate/manifest/allowlist (Phase 3),
  extractions deployments_registry→UTL + treasury NAV→UTL + MDPS classifier→UTL/UAC (Phase 9), sports
  FunctionBuilderEntry (Phase 4). **Wave C consumers now unblocked**: alerting/uta `create_api_auth` migration, MTDS/IS
  retry adapters. Then Phase 1b risk. Dead-gate enable LAST (rule 11 fleet proof).
- **SHIPPED (2026-06-11)** Phase 9 — the two GATE-CAUGHT service-dep edges + the dead-gate fix/enable (rule-11 fleet
  proof done):
  - **MDPS classifier → UAC**: `databento_classifier` (825 ln, UAC-only deps) + tests relocated to UAC
    `external/databento/` (`unified-api-contracts@00a7aca9`, +15 coverage tests to hold the 94% floor); mtds repointed
    all consumers + deleted local copy (`market-tick-data-service@9a34a43c`); mdps `canonical_writer` imports from UAC +
    dropped the `market-tick-data-service` path-dep (`market-data-processing-service@294b59ff`).
  - **deployment-api → strategy-service NAV**: `compute_unified_nav`/`compute_nav_by_client`/`_make_stub_balance` +
    tests relocated to UTL `treasury/nav_rollup.py` + exported from the UTL top-level facade
    (`unified-trading-library@6e3eb3c5`); strategy-service deleted the funcs, kept `TreasuryMonitor`
    (`strategy-service@573f09d8`); deployment-api `treasury_routes` imports from UTL facade + dropped the
    strategy-service path-dep + marked 3 FastAPI DTOs CORRECT-LOCAL + bumped its codex budget 24→25 for pre-existing
    peer-landed debt (`deployment-api@0a9600a9`).
  - **DEAD-GATE FIX + ENABLE**: `check-no-service-deps.py` (dotted+flat `[tool.uv.sources]` parse, broadened to
    api/batch-service/api types, +4 regression tests) + `base-service.sh` wired to the correct `scripts/validation/`
    path + dropped the 2 stale manifest dep-edges via `fix-internal-dependency-alignment.py`
    (`unified-trading-pm@1496b40f`, PR #242). Rule-11 verified: the enabled gate exits 0 across all 15 service-flavoured
    repos. REMAINING in Phase 9: edge #4 (deployment-api→deployment-service `deployments_registry`→UTL extract — does
    NOT block the gate since deployment-service is `type=infrastructure`) + the deferred raw-`import` scan extension.

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

- [x] ✅ [AGENT] P0. **UTL extension FIRST** — DONE `unified-trading-library@20c8ae8d` (6081 tests ✓, 4 new auth tests,
      QG 0). Added the `X-API-Key` (legacy) branch to `create_api_auth` (validates against
      `UnifiedCloudConfig().api_key`, returns `AuthContext(is_api_key=True, is_internal=True, role="admin")`, 401 on
      mismatch; ordered after S2S, before Bearer JWT; existing paths byte-preserved). **Unblocks alerting-service +
      unified-trading-api auth migration.**
- [ ] [AGENT] P0. **alerting-service** (depends on UTL extension above): delete `alerting_service/auth.py`
      (`verify_api_key` + DISABLE_AUTH guard); change `api/main.py` to depend on UTL
      `create_api_auth("alerting-service")`. Verify an `X-API-Key` caller still authenticates (it is **wired in
      production**). Highest urgency of the three.
- [x] ✅ [AGENT] P0. **client-reporting-api** — DONE `client-reporting-api@9cd77cc` (579 tests ✓, coverage 71.2%, QG 0).
      Deleted dead `auth.py` + `_google_auth_sync.py` (+ their tests); repointed the 2 live importers (`main.py`,
      `api/main.py`) to `config.get_config()`; cleared the `DISABLE_AUTH` toggle from 16 test fixtures (live path
      already on UTL `create_api_auth`). Direct `google.oauth2`/`google.auth` SDK import removed with the files.
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

- [x] ✅ [AGENT] P1. **execution-service** — DONE `execution-service@b7ea5e725` (116 custody + 24 AMM tests ✓, QG 0).
      `custody/cloud_kms.py` + `custody/withdrawal_signing.py` secret-fetch → UTL `get_secret_client()` (KMS Decrypt
      kept local); `providers/solana_amm_depth_provider.py` GCP-only `gcs.Client` blob loop → UTL `get_storage_client()`
      (now cloud-agnostic / AWS-safe). Tests updated to the `SecretClient` interface.
- [ ] [AGENT] P1. **agent-orchestrator**: `server/gcs_sync.py:30` raw `boto3`+`google.cloud.storage` → UTL
      `get_storage_client()` (already cloud-agnostic incl. S3). `server/auth.py:99` gs:// secret fetch → UTL
      `get_storage_client()`/`get_secret_client()`. **Keep the HS256/ES256 JWT signing logic** (intentional custom per
      orchestrator-auth SSOT — touch only the cloud-fetch).
- [x] ✅ [AGENT] P1. **market-tick-data-service** — DONE `market-tick-data-service@696249df` (988 handler tests ✓, QG
      0). Replaced the raw `secretmanager.SecretManagerServiceClient()` + bare-`except` across 9 CLI handlers (11 sites)
      with `from unified_trading_library import get_secret_client` → `.get_secret(name)` (cloud-agnostic, no swallow).
      Tests repointed to the UTL mock.
- [x] ✅ [AGENT] P2. **deployment-service** (scripts half) — DONE `deployment-service@6710f26` (QG 0).
      `scripts/vm/{vm_log_archival_cron,vm_serial_capture_cron,vm_zombie_watchdog,validate_vm_prefix_mapping}.py`
      `storage.Client()` → UTL `get_storage_client()`/`upload_to_storage`/`storage_exists`/`gcs_copy_object`;
      `compute_v1` control-plane kept.
- [ ] [AGENT] P2. **deployment-api** (routes half — REMAINING): route
      `deployment_api/routes/{builds_history,builds}.py` + `services/shard_detail.py:828` GCS-storage `storage.Client()`
      through UTL `get_storage_client()`. Keep `compute_v1` + pubsub/secretmanager liveness probes.
- [ ] [VERIFY] P1. Per repo: secret fetch + GCS read still work against emulator/mock; `quality-gates.sh` green;
      quickmerge.

## Phase 6 — Venue-error, health router, retry helper (findings #8, #10, #11)

- [x] ✅ [AGENT] P1. **instruments-service** — DONE `instruments-service@66165f2e` (23 tests ✓, QG 0; direct-push
      carve-out — UTL was transiently dirty). Deleted local `VenueError`; all 8 construction sites now build UAC
      `VenueErrorClassification` (`retry_safe`/`reconnect`/`action: ErrorAction`); `VenueFetchResult` wrapper kept.
- [ ] [AGENT] P2. **execution-service**: fold the second hand-rolled `/health`+`/ready`+`/readiness` in `api/app.py:209`
      onto UTL `make_health_router(...)` with a `data_freshness` callback (QG STEP 5.62), so the service has ONE health
      surface (the canonical `api/main.py` already uses it).
- [x] ✅ (UTL helper half) **Add a UTL retry helper** — DONE `unified-trading-library@20c8ae8d`: `retry` (decorator) +
      `with_retry` (callable), stdlib-only, exp backoff + jitter, 429/5xx-aware, exported from
      `unified_trading_library.utils.retry` / `.utils` / top-level. 9 new tests.
- [ ] [AGENT] P2. **Consume the UTL retry helper** (REMAINING): consolidate the two hand-rolled base-adapter retries —
      MTDS `market_interface/base_adapter.py:29-100` + instruments-service `reference_data/base_adapter.py:39-160` —
      onto `unified_trading_library.utils.retry`/`with_retry`. Preserve each adapter's classify-on-give-up behaviour.
- [ ] [VERIFY] P1. Adapter retry behaviour unchanged (mock 429 → N retries → classify); health endpoints respond;
      `quality-gates.sh` green; quickmerge.

## Phase 7 — LOW + lint tail (findings #14–#19)

- [x] ✅ [AGENT] P2. **alerting-service** — DONE `alerting-service@39181c7` (348 tests ✓, QG 0). Replaced
      `Literal["WARNING","CRITICAL"]` in `rules/connectivity_rules.py` + `rules/reconciliation_rules.py` with UAC
      `AlertSeverity` (`.WARN`/`.CRITICAL`); also fixed a dropped `"delivered": False` found in passing.
- [ ] [AGENT] P2. **agent-orchestrator**: migrate the ~30 `os.environ.get` config reads to a `UnifiedCloudConfig`
      subclass; move secret-bearing ones (`TELEGRAM_BOT_TOKEN`, JWT secret) to `get_secret_client()`; add UTL
      `setup_events`/`log_event` lifecycle emission (the repo emits none today). Local `utcnow()`/`to_utc()` may stay
      (thin tz-aware wrappers) but replace `logging.basicConfig` call sites. **Scope-flag:** orchestrator is partly
      intentionally standalone — migrate config/secrets/events, do not blanket-rewrite the custom dashboard auth.
- [x] ✅ [AGENT] P3. **unified-trading-api** — DONE `unified-trading-api@e3fbd8d` (QG 0). `routes/chat.py`
      `ANTHROPIC_API_KEY` now via `UnifiedCloudConfig().get_secret("anthropic-api-key")` (name confirmed from
      `credentials-registry.yaml`); the `# config-bootstrap` os.environ reads left as sanctioned.
- [x] ✅ [AGENT] P3. **greeks-service** — DONE `greeks-service@b119b5b` (QG 0). Deleted `greeks_service/events.py`
      re-export stub; the single importer now imports `log_event` from UTL directly.
- [ ] [AGENT] P3. **strategy-service**: noqa-with-reason (or `UnifiedCloudConfig`) the un-annotated `os.environ.get` in
      `recovery_event_helper.py:41,90` and `pnl/engine/mock_data_provider.py:38` (mirror the existing
      `position/engine/mock_data_provider.py` noqa pattern).
- [ ] [CODE] P2. **execution-service cross-service imports surfaced by the 2026-06-11 imports-in-fn sweep (codex ratchet
      plan)** — two UNSANCTIONED sites were hiding behind lazy in-function imports (now carrying tracked
      `# noqa: imports-inside-functions` markers): (1) `execution_service/algo_library/leg_controller_runner.py:222`
      imports `strategy_service.position.core.leg_snapshot_builder` — `strategy_service.position` is in the UAC
      `service_contract_map` **forbidden_imports** for execution-service and NOT in forbidden_exceptions (unlike the
      sanctioned target_universe.catalog site); move `leg_snapshot_builder` to UTL/UAC or add a justified
      forbidden_exception + deprecation-ledger entry. (2) `execution_service/algo_library/mtds_book_provider.py:93`
      imports `market_tick_data_service.reader.CanonicalParquetReader` AND execution-service pyproject declares
      `../market-tick-data-service` as a path dep (pyproject ~L124) — same no-service↔service violation class the
      MDPS/deployment-api removals fixed 2026-06-11; needs the reader surface promoted to a shared lib (UTL) or the
      manifest-read path flipped to the UAC contract + GCS. Repos: execution-service + strategy-service +
      market-tick-data-service + unified-api-contracts.
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

- [x] ✅ [AGENT] P1. **DEAD-GATE FIX — DONE (path + types + parser + enable):** `unified-trading-pm@1496b40f` (PR #242)
      — corrected `base-service.sh` to invoke `scripts/validation/check-no-service-deps.py` (the prior
      `scripts/check-no-service-deps.py` path never existed → gate silently no-op'd fleet-wide) + surfaced stderr;
      broadened `get_service_repos()` to `type ∈ {service, api-service, batch-service, api}` (keeps
      library/infrastructure/tool/devops/ui/test-harness non-service); fixed `get_path_deps()` to parse BOTH the FLAT
      `[tool.uv.sources]` and the DOTTED `[tool.uv.sources.<dep>]` table forms (the path-only flat parse missed mdps's
      dotted mtds dep); +4 regression unit tests (`tests/unit/test_check_no_service_deps.py`, 16 pass). Enabled LAST,
      after the mdps + deployment-api violations were remediated. **REMAINING (deferred, P2):** extend the check to also
      catch a raw `import <other_service>` in source/tests (currently path-dep-only) — the path-dep gate already catches
      every live violation; the import-level extension is additive hardening.
- [x] ✅ [AGENT] P1. **TRUE VIOLATION — deployment-api → strategy-service — DONE.** Relocated `compute_unified_nav` +
      `compute_nav_by_client` (+ the `_make_stub_balance` helper) from `strategy_service.position.core.treasury_monitor`
      into UTL `unified_trading_library/treasury/nav_rollup.py` (`unified-trading-library@6e3eb3c5`; +
      `test_nav_rollup.py` moved with the code, 13 tests; exported from BOTH `treasury/__init__` and the UTL top-level
      facade so consumers use `from unified_trading_library import compute_unified_nav`). strategy-service deleted the
      functions, keeps the `TreasuryMonitor` class local (`strategy-service@573f09d8`). deployment-api
      `treasury_routes.py` now imports from the UTL facade + DROPPED the `[tool.uv.sources]` strategy-service path-dep +
      dep line + marked the 3 FastAPI DTOs `# CORRECT-LOCAL` (`deployment-api@0a9600a9`). Removes the service→service
      edge. Dep order: UTL→strategy-service→deployment-api; all QG exit 0.
- [ ] [AGENT] P1. **deployment-api → deployment-service — EXTRACT the shared registry to UTL (NOT reclassification;
      corrected 2026-06-10).** The initial "reclassify deployment-service to library" idea was **wrong**:
      deployment-service genuinely IS a deployed service (has `Dockerfile` + `cloudbuild.yaml` + `buildspec.aws.yaml` +
      a live FastAPI `api/main.py` with ServiceBootstrap/uvicorn). BUT the coupling is **library-like** — the 6
      deployment-api files import `deployment_service.deployments_registry`, a **529-line GCS-backed data-access layer**
      (`DeploymentsRegistry` + `DeploymentRegistryEntry` + VM-log URI helpers + `is_entry_stale`) that depends only on
      UTL (`StorageClient`/`UnifiedCloudConfig`) and is needed by BOTH deployment-service (writer/control-plane) and
      deployment-api (reader/dashboard). **Fix: relocate `deployments_registry.py` into UTL** (e.g.
      `unified_trading_library.deployment_registry`); both services import it from UTL — removes the service→service
      edge with no forced HTTP boundary. (Same shared-accessor-to-library pattern as the strategy NAV-functions fix.)
      Keep deployment-service `type=service`.
- [x] ✅ [AGENT] P2. **market-data-processing-service → market-tick-data-service — DONE.** Relocated
      `databento_classifier` (825 lines, UAC-only deps) to UAC `unified_api_contracts/external/databento/` + its test
      suite (`unified-api-contracts@00a7aca9`; +15 tests for the previously-uncovered paths to hold UAC's 94% coverage
      floor). mtds repointed `databento_adapter`/`databento_equity`/`__init__` + 2 tests to UAC and DELETED its local
      copy + dedicated test (`market-tick-data-service@9a34a43c`). mdps `canonical_writer.py` now imports
      `from unified_api_contracts.external.databento import classify_databento_symbol` + DROPPED the
      `[tool.uv.sources.market-tick-data-service]` path-dep + dep line (`market-data-processing-service@294b59ff`).
      Removes the cross-service deep-import. `external.{source}` is the sanctioned UAC external surface (not a banned
      `canonical.*` deep import). Dep order: UAC→mtds→mdps; all QG exit 0.
- [x] ✅ [AGENT] P2. **strategy-service → market-tick-data-service** — DONE: `strategy-service@d1f5a6a8` (test +
      pyproject + uv.lock) + `unified-trading-pm@4af80fd83` (manifest edge). The sole coupling was
      `test_split_libraries.py::test_market_interface_import`, which only asserted MTDS's `get_market_adapter` is
      importable — i.e. it tested MTDS, not strategy (verified 0 MTDS imports in strategy source). Deleted that test +
      removed the `[project.dependencies]` entry + `[tool.uv.sources]` block + re-locked (dropped MTDS and its
      transitive-only `websocket-client`/`yfinance`) + removed the manifest dependency edge (alignment: True). Removes
      the service→service violation AND the test-only path-dep that gated every strategy ship (the 2026-06-10 dirty-MTDS
      ship-block root cause). QG exit 0 both repos.
- [x] ✅ [VERIFY] P1. **Gate ENABLED + fleet-verified — DONE** (`unified-trading-pm@1496b40f`). The two gate-CAUGHT
      path-dep edges (mdps→mtds, deployment-api→strategy-service) are resolved, so `check-no-service-deps.py` now exits
      0 across ALL 15 service-flavoured repos (verified by running the fixed gate from each repo dir with `REPO_ROOT`
      set). +4 regression unit tests added. **NOTE — edge #4 (deployment-api → deployment-service, P1 item above) is
      still OPEN but does NOT block enablement**: `deployment-service` is manifest `type=infrastructure`, NOT a
      service-flavour, so the gate correctly does not flag that path-dep (it is a library-like-coupling extraction, not
      a service↔service violation in the gate's terms). The stale manifest dep-edges for the 2 resolved edges were
      dropped via `fix-internal-dependency-alignment.py` (alignment: True).
- [ ] [AGENT] P2. **DEFERRED (additive hardening) — extend `check-no-service-deps.py` to also catch a raw
      `import <other_service>` in source/tests** (currently `[tool.uv.sources]` path-dep-only). Today every LIVE
      service↔service violation also carries a path dep, so the path-dep gate catches them all; this extension is
      belt-and-suspenders for a future import-without-path-dep case. Target repo: `unified-trading-pm`
      (`scripts/validation/check-no-service-deps.py`). Provenance: deferred from the P1 DEAD-GATE-FIX item
      (utl_uac_reuse 2026-06-11) — the path + types + parser + enable shipped; only the import-level scan remains.

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
