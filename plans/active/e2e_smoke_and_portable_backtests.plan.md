---
name: E2E Smoke and Portable Backtests Plan
overview:
  Layer 0–3 E2E smoke (contract alignment → schema robustness → infra verification → system smoke/full_e2e) plus
  CEFI/TradFi/DeFi/Sports portable backtests with VCR/fixtures.
todos:
  - id: layer-0-1-smoke
    content:
      Layer 0–1 — unified-api-contracts, unified-internal-contracts, per-service test_schema_*.py (blocks quickmerge)
    status: pending
  - id: layer-2-3-smoke
    content:
      Layer 2–3 — deployment-service verify_infra.py; system-integration-tests smoke + full_e2e (blocks first
      deployment)
    status: pending
  - id: portable-backtests-cefi-tradfi-defi
    content: Portable backtests — CEFI, TradFi, DeFi via run_parallel_backtests.sh and runners
    status: pending
  - id: portable-backtests-sports
    content:
      "Sports portable arb backtest — VCR cassettes for odds/line feeds. SCRIPT:
      strategy-service/scripts/run_sports_arb_backtest.py (to be created). COMMAND: cd strategy-service && python
      scripts/run_sports_arb_backtest.py --fixtures tests/fixtures/sports_odds/ --output
      artifacts/sports_backtest_result.json. Loads VCR-recorded odds/line feeds from tests/fixtures/sports_odds/ (no
      live API calls); runs arb detection via features_sports_service arb module; outputs
      artifacts/sports_backtest_result.json with fields: n_opportunities, n_trades, pnl, win_rate, max_drawdown. GATE:
      exits 0; artifact written with all required fields; no live API calls at runtime."
    status: pending
  - id: portable-criteria
    content: Ensure no live API calls in CI; deterministic; batch-live symmetry
    status: pending

  - id: local-service-play
    content: |
      LOCAL SERVICE DEVELOPMENT PLAY: Before Layer 2 infra verification, attempt running each core
      service locally in batch mode with mocked/local deps. Purpose: surface missing env vars, import
      errors, and config gaps before deploying to GCP sandbox.

      Per service, create or verify scripts/run_local.sh with:
        SERVICE_MODE=batch CLOUD_PROVIDER=local python -m <service_module>

      Priority order (DAG):
        1. instruments-service (gates all others)
        2. market-data-processing-service
        3. features-delta-one-service
        4. strategy-service
        5. execution-service

      For each service document in deployment-service/docs/local-dev/:
        - Required env vars (with example values)
        - Any setup steps (seed data, mock pubsub, local GCS bucket)
        - Known blockers

      GATE: each service starts and processes one synthetic batch record without crashing.
    status: pending
    activeForm: "Running each core service locally to surface config and import issues"
isProject: false
---

# E2E Smoke and Portable Backtests Plan (Merged)

**References:** E2E_SMOKE_PLAN.md, PORTABLE_BACKTESTS_PLAN.md, master_pre_deployment_plan_chain.plan.md **SSOT:**
system-integration-tests/README.md, unified-trading-codex integration-testing-layers.md **Order:** Day 8–9 in execution
sequence (Plans 7–8 in chain)

---

## Scope

1. **Layer 0–3 E2E smoke** — Contract alignment → schema robustness → infra verification → system smoke/full_e2e
2. **CEFI / TradFi / DeFi / Sports portable backtests** — No live API keys; VCR/fixtures; batch-live symmetry

---

## Integration Layers (E2E Smoke)

| Layer         | Where                                                                                                           | Credentials   | In quickmerge?                         | Blocks                    |
| ------------- | --------------------------------------------------------------------------------------------------------------- | ------------- | -------------------------------------- | ------------------------- |
| 0             | unified-cloud-interface, unified-market-interface, unified-reference-data-interface (schemas defined in AC/UIC) | None          | Yes                                    | Contract alignment        |
| 1             | Per-service test*schema*\*.py                                                                                   | None          | Yes                                    | Schema robustness         |
| **Layer 1.5** | Per-component integration tests (mocked direct deps)                                                            | None          | Yes — blocks quickmerge                | Component merge readiness |
| 2             | deployment-service verify_infra.py                                                                              | GCP read-only | Post-deploy ONLY — never in quickmerge | First deployment          |
| 3a            | system-integration-tests/tests/smoke/                                                                           | GCP sandbox   | Post-deploy                            | First deployment          |
| 3b            | system-integration-tests/tests/e2e/                                                                             | GCP sandbox   | Post-deploy                            | First deployment          |

**Layer 0–1 block quickmerge.** Layer 2–3 block first deployment.

> **Layer 0 — Schema test ownership note:** Schema tests are DEFINED in AC (unified-api-contracts) and UIC
> (unified-internal-contracts) for coverage tracking, but are EXECUTED by their owning interface repositories:
>
> - unified-cloud-interface: tests cloud SDK integration
> - unified-market-interface: tests market data sources (using VCR cassettes from AC's vcr_endpoints.py)
> - unified-reference-data-interface: tests reference data sources
> - AC contains external venue/source schemas only; UIC contains internal service-to-service schemas; no duplication
>   between them

---

## Internal Contracts Only (Layer 3)

**Rule:** system-integration-tests uses **internal contracts (UIC)** only. No external API keys.

| Allowed                       | Not allowed                                 |
| ----------------------------- | ------------------------------------------- |
| HTTP to service endpoints     | Direct API keys for Tardis, Databento, etc. |
| UIC schema validation         | VCR replay (lives in interfaces)            |
| GCP sandbox (buckets, PubSub) | Live external API calls                     |

---

## Execution Order: Day 8–9

### Day 8 — E2E Smoke (Layer 0–3)

| Step | Layer                | Path                             | Command / Script                                                                                                               | Agent-ready         |
| ---- | -------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------- |
| 8.1  | 0                    | unified-cloud-interface          | `cd unified-cloud-interface && pytest tests/integration/ -v`                                                                   | Yes                 |
| 8.2  | 0                    | unified-market-interface         | `cd unified-market-interface && pytest tests/integration/ -v`                                                                  | Yes                 |
| 8.2b | 0                    | unified-reference-data-interface | `cd unified-reference-data-interface && pytest tests/integration/ -v`                                                          | Yes                 |
| 8.3  | 1                    | Per-service                      | `cd <service> && pytest tests/unit/test_schema*.py -v` (instruments-service, strategy-service, execution-service, features-\*) | Yes                 |
| 8.4  | 2 (post-deploy only) | deployment-service               | `cd deployment-service && python scripts/verify_infra.py` — **run after deployment is live; never pre-deploy**                 | Yes (GCP read-only) |
| 8.5  | 3a                   | system-integration-tests         | `cd system-integration-tests && uv pip install -e ".[dev]" && pytest -m smoke -v`                                              | Yes                 |
| 8.6  | 3b                   | system-integration-tests         | `cd system-integration-tests && pytest -m full_e2e -v`                                                                         | Yes                 |

**Script paths (workspace-relative):**

- `system-integration-tests/` — pytest from repo root
- `deployment-service/scripts/verify_infra.py` — **post-deploy only**
- `unified-cloud-interface/tests/integration/` — executes cloud SDK schema tests
- `unified-market-interface/tests/integration/` — executes market data schema tests (VCR cassettes from AC's
  vcr_endpoints.py)
- `unified-reference-data-interface/tests/integration/` — executes reference data schema tests
- AC (`unified-api-contracts`) and UIC (`unified-internal-contracts`) define schemas for coverage tracking only; tests
  are executed by the interface repos above

---

### Day 9 — Portable Backtests (CEFI, TradFi, DeFi, Sports)

| Step | Category | Path                           | Script / Command                                                                           | Agent-ready |
| ---- | -------- | ------------------------------ | ------------------------------------------------------------------------------------------ | ----------- |
| 9.1  | CEFI     | strategy-service               | `scripts/run_parallel_backtests.sh <grid_id> cefi [max_parallel]` or `run_backtest_api.py` | Yes         |
| 9.2  | TradFi   | execution-service              | `scripts/runners/run_tradfi_l1_l2_backtests.py`                                            | Yes         |
| 9.3  | DeFi     | execution-service              | `scripts/runners/run_defi_backtests.py`                                                    | Yes         |
| 9.4  | Sports   | strategy-service / sports path | Portable arb backtest (VCR cassettes for odds/line feeds)                                  | Yes         |

**Script paths (workspace-relative):**

- `strategy-service/scripts/run_parallel_backtests.sh` — CEFI/TradFi/DeFi via domain arg
- `strategy-service/scripts/run_backtest_api.py`
- `execution-service/scripts/runners/run_defi_backtests.py`
- `execution-service/scripts/runners/run_tradfi_l1_l2_backtests.py`

**Portable criteria:**

1. No live API calls in CI — VCR cassettes, fixtures, or mock adapters
2. Deterministic — same input → same output
3. Fast — &lt;5 min per strategy (or marked integration)
4. Shared engine — same strategy logic as live mode (batch-live symmetry)

---

## Agent-Ready Steps (Copy-Paste)

### Day 8 — E2E Smoke

```bash
# 8.1 Layer 0 — unified-cloud-interface (executes cloud SDK schema tests defined in AC)
cd unified-cloud-interface && pytest tests/integration/ -v

# 8.2 Layer 0 — unified-market-interface (executes market data schema tests; VCR cassettes from AC's vcr_endpoints.py)
cd unified-market-interface && pytest tests/integration/ -v

# 8.2b Layer 0 — unified-reference-data-interface (executes reference data schema tests)
cd unified-reference-data-interface && pytest tests/integration/ -v

# 8.3 Layer 1 — Schema robustness (sample services)
cd instruments-service && pytest tests/unit/test_schema*.py -v 2>/dev/null || :
cd strategy-service && pytest tests/unit/test_schema*.py -v 2>/dev/null || :
cd execution-service && pytest tests/unit/test_schema*.py -v 2>/dev/null || :

# 8.4 Layer 2 — Infra verification (POST-DEPLOY ONLY — requires deployment to be live, GCP_PROJECT_ID, GCP creds)
# DO NOT run this pre-deploy or as part of quickmerge checks
cd deployment-service && python scripts/verify_infra.py

# 8.5 Layer 3a — Smoke
cd system-integration-tests && uv pip install -e ".[dev]" && pytest -m smoke -v

# 8.6 Layer 3b — Full E2E
cd system-integration-tests && pytest -m full_e2e -v
```

### Day 9 — Portable Backtests

```bash
# 9.1 CEFI (requires GCS configs; use fixtures for portable CI)
cd strategy-service && ./scripts/run_parallel_backtests.sh <grid_id> cefi 4
# Or: python -m strategy_service.cli.main --mode batch --config-gcs <path> ...

# 9.2 TradFi
cd execution-service && python scripts/runners/run_tradfi_l1_l2_backtests.py

# 9.3 DeFi
cd execution-service && python scripts/runners/run_defi_backtests.py

# 9.4 Sports — portable arb (VCR cassettes)
# TBD: strategy-service or sports execution path with mock odds/line feeds
```

---

## system-integration-tests Structure

```
system-integration-tests/
  tests/
    smoke/           # Layer 3a — happy path, health checks
      test_api_smoke.py
      test_pipeline_smoke.py
    e2e/             # Layer 3b — full e2e, auth, multi-date
      test_pipeline_e2e.py
      test_auth_e2e.py
      test_aws_s3_smoke.py   # @pytest.mark.integration (S3_TEST_BUCKET)
```

**Markers:** `@pytest.mark.smoke` (Layer 3a), `@pytest.mark.full_e2e` (Layer 3b)

---

## Environment (Layer 3)

```bash
INSTRUMENTS_SERVICE_URL=http://localhost:8080
DEPLOYMENT_API_URL=http://localhost:8001
ERA_URL=http://localhost:8002
CRA_URL=http://localhost:8003
MDA_URL=http://localhost:8004
GCS_TEST_BUCKET=<sandbox-bucket>
GCP_PROJECT_ID=<project-id>
S3_TEST_BUCKET=<sandbox-bucket>   # optional, for AWS S3 tests
```

---

## References

- E2E_TESTING_GUIDE_2026-02-17.md (archived)
- VCR_CREDENTIAL_RECORDING_PLAN.md
- mvp-universe.yaml strategies
- batch-live-symmetry.mdc
- integration-testing-layers.md (codex)
