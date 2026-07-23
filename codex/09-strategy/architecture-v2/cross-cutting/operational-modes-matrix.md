---
doc_type: codex-ssot
title: Operational Modes Matrix — Cross-Cutting Infrastructure
summary:
  "Human-readable matrix of the orthogonal operational axes (ENVIRONMENT / DATA_MODE / RUNTIME_MODE / CLOUD_PROVIDER /
  TESTNET_MODE / PHASE_MODE / OPERATIONAL_MODE + ExecutionTarget/Trigger) that compose mock/real/testnet/local-cloud;
  machine SSOT is UAC `modes.py` + `env_canon.py`. `TestingStage` is deprecated — decompose to the new axes."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [system-integration-tests, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: [operational-modes, uac, testnet, migration, cefi, defi]
related:
  [
    ../../../06-coding-standards/integration-testing-layers.md,
    ../../../08-workflows/local-dev.md,
    /codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md,
    ../../../04-architecture/manual-trade-booking.md,
  ]
created: 2026-03-27
authoritative_for: [operational-modes orthogonal-axes composition matrix (mock/real/testnet/local-cloud)]
referenced_by:
  [
    /codex/04-architecture/research-service-and-dart-integration.md,
    /codex/06-coding-standards/README.md,
    /codex/08-workflows/local-dev.md,
    /codex/09-strategy/README.md,
    /codex/09-strategy/_archived_pre_v2/STRATEGY_CATALOG_AND_WORKFLOW_ALIGNMENT.md,
    /codex/09-strategy/_archived_pre_v2/cross-cutting/config-architecture.md,
    /codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md,
    plans/epics/cross_cutting_may_23_SUPERSEDED_2026_05_21.md,
  ]
owner:
last_reviewed: 2026-05-18
code_refs:
---

> **DART route surface update 2026-05-13**: the DART manual-trade lane now has a dedicated route surface at
> `/services/dart/terminal/manual/` (form + preview + dispatch) and `/services/dart/terminal/manual/[instructionId]/`
> (per-instruction monitor). The Sheet-over-trading-overview (`manual-trading-panel.tsx`) is preserved in parallel for
> the trading overview surface; Sheet retirement is post-cutover polish. Unified `lib/api/dart-client.ts` provides typed
> wrappers for the 4 DART endpoints (preview / submit / status / mode-transition). Reference:
> `plans/active/dart_manual_trade_ux_refactor_2026_05_13.md` Phase C.

# Operational Modes Matrix — Cross-Cutting Infrastructure

**SSOT (machine-readable):** `unified-api-contracts/unified_api_contracts/internal/modes.py` (StrEnums) +
`unified_api_contracts/internal/env_canon.py` (`EnvVars` — canonical env var **names**).

**SSOT (runtime values):** `unified-config-interface` `UnifiedCloudConfig` / service-specific config subclasses (load
env at startup; services must not scatter `os.getenv` — see `06-coding-standards/README.md` bootstrap table).

**Venue endpoints (testnet vs mainnet URLs, chains, sandbox APIs):** `unified-api-contracts` registry /
`provider_api_versions.yaml` + capability declarations — **not** duplicated per service.

This document is the **human-readable matrix** for how mock, real, testnet, and local-cloud concepts compose.

**Secrets + import order:** Config modules that fetch Secret Manager must not import `unified_cloud_interface` at module
scope (avoids init cycles when cloud loads `UnifiedCloudConfig`). See `07-security/secrets-management.md` — section
**Unified config ↔ unified cloud — package import order**.

---

## 1. Orthogonal axes (prefer one switch per concern)

| Axis                   | Env var (`EnvVars`)      | Enum               | Default   | What it controls                                                                                                                           |
| ---------------------- | ------------------------ | ------------------ | --------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Deployment tier        | `ENVIRONMENT`            | `EnvironmentMode`  | dev       | Config bucket, secret policy, dashboards                                                                                                   |
| Data plane             | `DATA_MODE`              | `DataMode`         | real      | Mock generators vs real feeds/storage reads                                                                                                |
| Transport / job shape  | `RUNTIME_MODE`           | `RuntimeMode`      | live      | Streaming/event vs batch/historical jobs                                                                                                   |
| Cloud stack            | `CLOUD_PROVIDER`         | `CloudProvider`    | gcp       | GCP vs AWS vs **local emulators**                                                                                                          |
| Venue environment      | `TESTNET_MODE`           | `TestnetMode`      | mainnet   | **Which** endpoint/chain per venue (resolved in UAC)                                                                                       |
| Data availability      | `PHASE_MODE`             | `PhaseMode`        | phase3    | Pipelines that may be absent in early phases                                                                                               |
| Strategy maturity      | (persisted / config)     | `TestingStage` ⚠️  | MOCK      | **DEPRECATED** — use `OperationalMode` + `ExecutionTarget` + `ExecutionTrigger`; kept for 6 consumer call-sites; migrate via `decompose()` |
| How the service trades | `OPERATIONAL_MODE`       | `OperationalMode`  | live      | live vs manual vs backtest vs **paper**                                                                                                    |
| Execution destination  | (via `ExecutionTarget`)  | `ExecutionTarget`  | mainnet   | Where orders go: mainnet / testnet / fork / simulation — independent of mode                                                               |
| Instruction source     | (via `ExecutionTrigger`) | `ExecutionTrigger` | automated | Who generates the instruction: automated strategy vs manual operator                                                                       |

Axes are **intentionally independent**: e.g. `CLOUD_PROVIDER=local` with `DATA_MODE=real` can mean “real API calls but
emulated GCS/PubSub” if that combination is supported for the service.

---

## 2. Colloquial terms mapped to axes

| Informal term                                   | Typical combination                               | Notes                                                                                            |
| ----------------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| **Mock**                                        | `DATA_MODE=mock` (often + `CLOUD_PROVIDER=local`) | Synthetic data / stubs; may still use real HTTP to **sandbox** APIs if a test explicitly does so |
| **Real**                                        | `DATA_MODE=real`                                  | Production-like data paths                                                                       |
| **Testnet** (CeFi / DeFi / sports / prediction) | `TESTNET_MODE=testnet`                            | Concrete host, chain ID, or sandbox base URL comes from **UAC**                                  |
| **Cloud local**                                 | `CLOUD_PROVIDER=local`                            | Emulator stack (Pub/Sub, GCS fakes, etc.) — **infrastructure**, not “fake market data” by itself |

---

## 3. Legacy and migration

| Legacy                                    | Direction                                                                                                                                          |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CLOUD_MOCK_MODE`                         | Prefer `DATA_MODE=mock` + `UnifiedCloudConfig.is_mock_mode()`; `EnvVars.CLOUD_MOCK_MODE` remains in `env_canon` for CI/scripts until fully drained |
| `cloud_mock_mode` on `UnifiedCloudConfig` | Deprecated; same migration as above                                                                                                                |
| `SERVICE_MODE`                            | Use `RUNTIME_MODE` (`EnvVars.SERVICE_MODE` marked legacy in `env_canon`)                                                                           |

---

## 4. TradFi (IBKR) and `TESTNET_MODE`

IBKR **paper vs live** is **not** the same string as `TestnetMode`, but it is the same **class of concern** (execution
environment). Today, paper/live often arrives as `trading_mode` inside the `ibkr-account-credentials` Secret Manager
JSON (see `unified-config-interface` `ibkr_credentials.py`).

**Target architecture (document now; implement incrementally):**

- Platform-wide intent: `TESTNET_MODE=testnet` and/or `OperationalMode.PAPER` should **align** TradFi with other venues
  (adapters read `UnifiedCloudConfig` and choose paper gateway / sandbox paths consistently).
- Secret `trading_mode` remains valid as an **explicit override** for operators when it must differ from global mode.

---

## 5. CLI vs env injection

- **Production / CI:** inject the same env vars listed in §1 (names from `EnvVars`).
- **Local / ServiceCLI:** flags should **only** set those canonical names (or build a config overlay) — no per-service
  synonym flags. SSOT for CLI standardisation: `unified-trading-library` `ServiceCLI` / `BaseModeHandler` tests describe
  the intended axes.

---

## 6. Schemas and registry data (boundary reminder)

| Concern                                            | Owner                                           |
| -------------------------------------------------- | ----------------------------------------------- |
| External API shapes, normalised outputs            | `unified-api-contracts`                         |
| Internal messaging, cross-service DTOs             | `unified_api_contracts.internal`                |
| Parquet `SchemaDefinition` / column enforcement    | Service repo                                    |
| Secret **names** (e.g. `ibkr-account-credentials`) | `unified-cloud-interface` `CredentialsRegistry` |

---

## 7. SIT / Layer 3 E2E expectations

`system-integration-tests` should treat **declared** mode combinations as part of staging smoke where relevant:

- Smoke (3a): at minimum, document which default env matrix staging uses (`DATA_MODE`, `CLOUD_PROVIDER`, `TESTNET_MODE`)
  and assert health/readiness under that matrix.
- Full E2E (3b): when a venue supports testnet, add cases that **fail** if `TESTNET_MODE=testnet` still hits production
  endpoints (assert via cassette, URL capture, or known sandbox response).

New services: add a row to the service readiness YAML under data availability referencing this doc when
`asset_group_readiness` includes mock / testnet / live dimensions.

---

## Related documents

- `08-workflows/local-dev.md` — ports, `CLOUD_MOCK_MODE` in local tables (being aligned with `DATA_MODE`)
- `06-coding-standards/strategy-identity-versioning.md` — strategy config vs execution boundaries
- `06-coding-standards/integration-testing-layers.md` — Layer 3 scope
- `04-architecture/manual-trade-booking.md` — `OperationalMode` usage
- `09-strategy/cross-cutting/dart-manual-trade-spec.md` — peer doc: per-archetype DART manual-fallback scope (May-23
  cutover surfaces + post-cutover deferrals)
