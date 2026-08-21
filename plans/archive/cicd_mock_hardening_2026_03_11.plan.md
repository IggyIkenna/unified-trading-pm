---
doc_type: plan
title: CI/CD Mock Infrastructure Hardening (Citadel-Grade)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [client-reporting-api, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-11'
overview: 'Harden all 63 repos to Citadel-grade mock/sim/demo testability: credential-free CI gate, protocol-faithful GCP emulators (Pub/Sub, GCS, BigQuery), AWS moto coverage, WebSocket feed simulator, Hyperliquid responses mock, cassette UAC parity checks, nightly drift detection, fault injection, tick replay engine, and full demo-mode orchestration. Extends production_mock_e2e_plan_d90c8f20.md with 14 missing CI/CD hardening items.'
todos:
- {id: h5-2-cassette-parity, content: 'P0: Create unified-api-contracts/tests/test_cassette_schema_parity.py — loads every committed cassette YAML and validates response body against UAC Pydantic model; fails QG on violation; zero network calls', status: completed}
- {id: h8-credential-free-gate, content: 'P0: Create unified-trading-pm/scripts/dev/network_block_plugin.py (pytest plugin — responses passthrough=False for full session); add credential-free CI step to system-integration-tests workflow with CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true', status: completed}
- {id: h2-moto-aws, content: 'P1: Add moto[s3,secretsmanager,sqs]>=5.0.0 to unified-cloud-interface test deps; create tests/integration/test_aws_mode.py with @mock_aws coverage for S3StorageClient, AWSSecretClient, SQS queue; gate aws_migration codebuild-canary-run', status: completed}
- {id: h1-1-pubsub-emulator, content: 'P1: Wire PUBSUB_EMULATOR_HOST=localhost:8085 into unified-cloud-interface/tests/conftest.py and system-integration-tests/tests/conftest.py; add gcr.io/google.com/cloudsdktool/google-cloud-cli Docker service to CI workflows', status: done}
- {id: h4-1-hyperliquid-responses, content: 'P1: Create unified-defi-execution-interface/tests/fixtures/hyperliquid_responses.py using responses library (@responses.activate passthrough=False) for order place/cancel/query; add responses>=0.24.1 to pyproject.toml test deps if missing', status: completed}
- {id: h4-2-defi-zero-io-assertion, content: 'P1: Wrap all DeFi adapter tests (Aave/Morpho/Uniswap/Lido/EtherFi) with responses passthrough=False to prove zero network calls in CI; any future accidental live call fails fast', status: completed}
- {id: h3-websocket-simulator, content: 'P2: Create unified-market-interface/tests/fixtures/mock_ws_server.py (MockWebSocketFeed — aiohttp.test_utils WS server); add ws_ticks_binance.json, ws_ticks_deribit.json, ws_ticks_hyperliquid.json fixtures; add test_ws_manager.py and execution-service test_deribit_ws.py', status: done}
- {id: h1-2-gcs-emulator, content: 'P2: Wire fsouza/fake-gcs-server:latest (port 4443) into UCI + SIT conftest via STORAGE_EMULATOR_HOST=http://localhost:4443; covers bucket lifecycle, ACLs, signed URLs not covered by LocalStorageProvider', status: done}
- {id: h7-thegraph-fixtures, content: 'P2: Create unified-market-interface/tests/fixtures/thegraph_responses.py with aioresponses fixtures per query hash (replaces 9-key live rotation in CI)', status: done}
- {id: h7-alchemy-fixtures, content: 'P2: Create responses fixtures for Alchemy/Infura JSON-RPC eth_call patterns used in DeFi market data paths', status: done}
- {id: h7-cassette-completion, content: 'P2: Complete VCR cassette coverage for all Databento and Tardis endpoints used in unified-reference-data-interface and market-data-service; add Pyth/BloxRoute fixtures if used in production paths', status: done}
- {id: h6-fault-injection, content: 'P3: Create unified-trading-pm/scripts/dev/fixtures/fault_injection.py (FaultInjectionMiddleware — latency, error_rate, timeout_rate for httpx/aiohttp); add test_fault_scenarios.py to execution-service, market-data-service, unified-cloud-interface covering: timeout→circuit breaker, 429→backoff, cascade→alert event', status: done}
- {id: h9-tick-replay, content: 'P3: Create unified-trading-pm/scripts/dev/fixtures/tick_replay.py (TickReplayEngine — reads mock_data_dev_project seed fixtures, freezegun time control, UAC Tick schema validation); depends on mock_data_dev_project_seeding_2026_03_10 seed fixtures', status: done}
- {id: h1-3-bigquery-emulator, content: 'P3: Wire ghcr.io/goccy/bigquery-emulator:latest (port 9050) into trading-analytics-api and client-reporting-api test suites via BIGQUERY_EMULATOR_HOST; document known emulator gaps in window functions', status: done}
- {id: h1-4-secret-rotation-test, content: 'P3: Add tests/integration/test_secret_rotation.py to unified-cloud-interface using LocalSecretProvider (no emulator needed); validates rotation logic not currently tested', status: done}
- {id: h5-1-cassette-drift, content: 'P4: Create unified-trading-pm/.github/workflows/cassette-drift-check.yml — nightly 02:00 UTC; re-records cassettes against real APIs; schema-level Pydantic diff (not byte diff); GitHub issue + Telegram alert on drift; alerting-only (not CI-blocking)', status: done}
- {id: h10-1-docker-compose-mock, content: 'P4: Create unified-trading-pm/docker/docker-compose.mock.yml — all T2/T3 services with CLOUD_MOCK_MODE=true CLOUD_PROVIDER=local; optional GCP emulator containers (Pub/Sub, GCS); seed fixture volume mounts', status: done}
- {id: h10-2-demo-mode-script, content: 'P4: Create unified-trading-pm/scripts/demo-mode.sh — single command: starts all services (mock) + all UIs (VITE_MOCK_API=true) + seeds data from mock_data_dev_project fixtures; stakeholder-ready with --open-browser flag', status: done}
isProject: true
---

# CI/CD Mock Infrastructure Hardening — Citadel-Grade

**Parent plan:** [production_mock_e2e_plan_d90c8f20.md](production_mock_e2e_plan_d90c8f20.md) **Status:** active |
**Priority:** P0–P4 phased | **Owner:** infra | **Target:** 2026-04-01

---

## Context

The existing `production_mock_e2e_plan_d90c8f20.md` defines the right scope (VCR cassettes, service mock replay, UI mock
API, sandbox mode) but was missing critical CI/CD hermeticity: no GCP or AWS emulators, no WebSocket feed simulator, no
mechanism to detect when real exchange APIs drift from committed cassettes, and no proof that CI makes zero live network
calls. This plan adds the 14 hardening items needed to reach institutional-grade ("Citadel-grade") testability.

**CRCD = CI/CD** — this plan directly addresses all CI/CD sim-vs-real API call gaps.

---

## Gap Summary

| Gap                                                         | Severity | Item |
| ----------------------------------------------------------- | -------- | ---- |
| No cassette → UAC parity check                              | Critical | H5.2 |
| No credential-free CI gate                                  | Critical | H8   |
| No AWS moto (migration active)                              | High     | H2   |
| No GCP Pub/Sub emulator                                     | High     | H1.1 |
| Hyperliquid REST excluded from CI                           | High     | H4.1 |
| DeFi adapters: no zero-I/O assertion                        | High     | H4.2 |
| UMI WS manager: no mock                                     | High     | H3   |
| GCS emulator missing (LocalProvider skips ACLs/signed URLs) | High     | H1.2 |
| TheGraph/Alchemy: live RPC calls in CI                      | Medium   | H7   |
| No fault injection for circuit breaker validation           | Medium   | H6   |
| No deterministic tick replay engine                         | Medium   | H9   |
| BigQuery: no emulator                                       | Medium   | H1.3 |
| Cassette drift: no nightly detection                        | Medium   | H5.1 |
| No end-to-end sim orchestration or demo mode                | Low      | H10  |

---

## Priority Order

| Priority | ID    | Item                         | Key Files                                                                  |
| -------- | ----- | ---------------------------- | -------------------------------------------------------------------------- |
| P0       | H5.2  | Cassette UAC parity test     | `unified-api-contracts/tests/test_cassette_schema_parity.py`               |
| P0       | H8    | Credential-free CI gate      | `unified-trading-pm/scripts/dev/network_block_plugin.py`                   |
| P1       | H2    | AWS moto                     | `unified-cloud-interface/tests/integration/test_aws_mode.py`               |
| P1       | H1.1  | Pub/Sub emulator             | `unified-cloud-interface/tests/conftest.py`, SIT conftest                  |
| P1       | H4.1  | Hyperliquid `responses` mock | `unified-defi-execution-interface/tests/fixtures/hyperliquid_responses.py` |
| P1       | H4.2  | DeFi zero-I/O assertion      | All DeFi adapter tests wrapped with `responses` passthrough=False          |
| P2       | H3    | WebSocket feed simulator     | `unified-market-interface/tests/fixtures/mock_ws_server.py`                |
| P2       | H1.2  | GCS emulator                 | `unified-cloud-interface/tests/conftest.py`, SIT conftest                  |
| P2       | H7    | Third-party fixtures         | TheGraph, Alchemy, Databento/Tardis, Pyth/BloxRoute                        |
| P3       | H6    | Fault injection              | `unified-trading-pm/scripts/dev/fixtures/fault_injection.py`               |
| P3       | H9    | Tick replay engine           | `unified-trading-pm/scripts/dev/fixtures/tick_replay.py`                   |
| P3       | H1.3  | BigQuery emulator            | trading-analytics-api, client-reporting-api conftest                       |
| P3       | H1.4  | Secret rotation test         | `unified-cloud-interface/tests/integration/test_secret_rotation.py`        |
| P4       | H5.1  | Nightly cassette drift       | `unified-trading-pm/.github/workflows/cassette-drift-check.yml`            |
| P4       | H10.1 | docker-compose.mock.yml      | `unified-trading-pm/docker/docker-compose.mock.yml`                        |
| P4       | H10.2 | Demo mode script             | `unified-trading-pm/scripts/demo-mode.sh`                                  |

---

## Venue / API Coverage Matrix (All 63 Repos)

| Domain           | Venues                                                     | CI State Before              | CI State After      |
| ---------------- | ---------------------------------------------------------- | ---------------------------- | ------------------- |
| CeFi execution   | Binance, Coinbase, ByBit, OKX, Deribit, Hyperliquid, Upbit | `mode="sim"` ✓               | + fault injection   |
| TradFi execution | CME, CBOE, NYSE, NASDAQ, ICE, FX (IBKR)                    | `MagicMock(spec=IB)` ✓       | + WS TWS event mock |
| DeFi execution   | Hyperliquid REST, Aave, Morpho, Uniswap, Lido, EtherFi     | Hyperliquid excluded ✗       | H4.1+H4.2 ✓         |
| Sports execution | 1xBet + others (USEI)                                      | `aioresponses` + VCR ✓       | Complete cassettes  |
| Market data WS   | Binance WS, Deribit WS, OKX WS                             | No mock ✗                    | H3 WS simulator ✓   |
| Market data REST | Databento, Tardis, Yahoo Finance                           | VCR partial                  | H7 complete ✓       |
| Market data DeFi | TheGraph, Alchemy, Pyth, BloxRoute                         | Live calls in CI ✗           | H7 fixtures ✓       |
| Cloud infra GCP  | GCS, Pub/Sub, Secret Manager, BigQuery                     | LocalProvider partial ✗      | H1 emulators ✓      |
| Cloud infra AWS  | S3, SQS, Secrets Manager                                   | `unittest.mock.patch` only ✗ | H2 moto ✓           |
| Reference data   | Databento, Tardis, OpenBB, FRED, ECB                       | VCR partial                  | H7 complete ✓       |

---

## Integration with Related Plans

| Plan                                                | Integration                                                      |
| --------------------------------------------------- | ---------------------------------------------------------------- |
| `aws_migration.md` — `codebuild-canary-run` pending | H2 (moto) gates canary                                           |
| `mock_data_dev_project_seeding_2026_03_10.md`       | H9 tick replay consumes seed fixtures; H10 demo mode mounts them |
| `cloud_infra_bucket_auth_2026_03_10.md`             | H1.2 GCS emulator enables bucket auth tests                      |
| `institutional_hardening_2026_03_10.md`             | H6 fault injection validates circuit breakers                    |
| `phase3_service_hardening_integration.md`           | H3 WS mock, H5 drift detection                                   |
| `stub_completion_interfaces_and_infra.md`           | H4.1 Hyperliquid mock unblocks DeFi stub tests                   |

---

## Verification Checklist

- [ ] `cd unified-api-contracts && pytest tests/test_cassette_schema_parity.py` — all cassettes validate ✓
- [ ] CI run with no secrets: `CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true pytest -m "not sandbox"` exits 0 ✓
- [ ] `cd unified-cloud-interface && pytest tests/integration/test_aws_mode.py` — moto tests pass, zero real AWS calls ✓
- [ ] `PUBSUB_EMULATOR_HOST=localhost:8085 pytest tests/integration/test_event_bus.py` passes ✓
- [ ] `cd unified-defi-execution-interface && pytest tests/ -v` — Hyperliquid order tests pass with `responses` active ✓
- [ ] `cd unified-market-interface && pytest tests/integration/test_ws_manager.py` — tick replay deterministic ✓
- [ ] `bash scripts/demo-mode.sh --seed` starts full system with no credentials required ✓
