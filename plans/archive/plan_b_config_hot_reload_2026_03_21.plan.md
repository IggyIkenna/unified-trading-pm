---
name: plan-b-config-hot-reload
overview:
  Backend-only: wire config hot-reload callbacks in all 21 services (20 are log-only stubs), add missing domain config
  schemas to UCfgI, build a config publish API for operators, and remediate 12 config placement violations.
type: code
epic: epic-code-completion
status: active
locked_by: null
locked_since: null

completion_gates:
  code: C5
  deployment: none
  business: none

repo_gates:
  - repo: unified-config-interface
    code: C0
    deployment: none
    business: none
    readiness_note: "Domain config schemas (RiskDomainConfig, AlertRuleDomainConfig, etc.) added here."
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
    readiness_note: "Shared hot-reload utilities if needed."
  - repo: instruments-service
    code: C0
    deployment: none
    business: none
    readiness_note: "Only service with working hot-reload callback (reference implementation)."
  - repo: market-tick-data-service
    code: C0
    deployment: none
    business: none
    readiness_note: "8 config placement violations to fix."
  - repo: market-data-processing-service
    code: C0
    deployment: none
    business: none
  - repo: features-technical-service
    code: C0
    deployment: none
    business: none
  - repo: features-microstructure-service
    code: C0
    deployment: none
    business: none
  - repo: features-orderflow-service
    code: C0
    deployment: none
    business: none
  - repo: features-alternative-service
    code: C0
    deployment: none
    business: none
  - repo: features-cross-sectional-service
    code: C0
    deployment: none
    business: none
  - repo: features-sentiment-service
    code: C0
    deployment: none
    business: none
  - repo: features-onchain-service
    code: C0
    deployment: none
    business: none
  - repo: features-sports-service
    code: C0
    deployment: none
    business: none
  - repo: strategy-service
    code: C0
    deployment: none
    business: none
  - repo: execution-service
    code: C0
    deployment: none
    business: none
  - repo: trading-agent-service
    code: C0
    deployment: none
    business: none
  - repo: risk-management-service
    code: C0
    deployment: none
    business: none
  - repo: position-balance-monitor-service
    code: C0
    deployment: none
    business: none
  - repo: pnl-attribution-service
    code: C0
    deployment: none
    business: none
  - repo: alerting-service
    code: C0
    deployment: none
    business: none
  - repo: reconciliation-service
    code: C0
    deployment: none
    business: none
  - repo: ml-training-service
    code: C0
    deployment: none
    business: none
  - repo: ml-inference-service
    code: C0
    deployment: none
    business: none
  - repo: config-api
    code: C0
    deployment: none
    business: none
    readiness_note: "Config publish API endpoint lives here."

depends_on:
  - registry-completeness-implementation-detail

todos:
  # ── Phase 0: Domain Config Schemas in UCfgI ──
  - id: p0-risk-domain-config
    content: |
      - [x] [AGENT] P0. Add RiskDomainConfig schema to unified-config-interface — risk thresholds (max_drawdown_pct, position_limit, var_limit, margin_utilization_warn), per-venue overrides, reload-safe dataclass with validation.
    status: done
  - id: p0-alert-rule-domain-config
    content: |
      - [x] [AGENT] P0. Add AlertRuleDomainConfig schema to unified-config-interface — alert rules (metric, operator, threshold, severity, cooldown_seconds, channels), per-service overrides.
    status: done
  - id: p0-rate-limit-domain-config
    content: |
      - [x] [AGENT] P0. Add RateLimitDomainConfig schema to unified-config-interface — per-venue rate limits (requests_per_second, burst_limit, backoff_strategy), per-endpoint overrides.
    status: done
  - id: p0-feature-flag-domain-config
    content: |
      - [x] [AGENT] P0. Add FeatureFlagDomainConfig schema to unified-config-interface — feature flags (flag_name, enabled, rollout_pct, allowed_venues), with typed flag registry.
    status: done
  - id: p0-strategy-domain-config
    content: |
      - [x] [AGENT] P0. StrategyDomainConfig already existed in UCfgI — verified has enabled_strategies + strategy_params dict (per-strategy overrides).
    status: done
  - id: p0-qg-ucfgi
    content: |
      - [x] [SCRIPT] P0. QG gate: run `cd unified-config-interface && bash scripts/quality-gates.sh` — new schemas pass (291 passed, pre-existing testnet_contracts errors only).
    status: done

  # ── Phase 1A: Wire callbacks — Market Data (PARALLEL) ──
  # CITADEL AUDIT (2026-03-21): 18/21 services have HOLLOW STUB mock providers — they
  # do NOT call start_domain_config_reloaders() in their startup path, and 0/21 services
  # read the getters from the domain config reloaders. The callbacks were "wired" in the
  # sense that boilerplate files were created, but the services do not actually consume
  # hot-reloaded config at runtime. Marking all as NOT DONE.
  - id: p1a-market-tick-data
    content: |
      - [ ] [AGENT] P1. Wire hot-reload callback in market-tick-data-service — AUDIT: callback file exists but service startup does NOT call start_domain_config_reloaders(), and engine does NOT read getters. Must: (a) add start_domain_config_reloaders() to service main.py, (b) make engine consume RateLimitDomainConfig getters instead of static config.
    status: todo
  - id: p1a-market-data-processing
    content: |
      - [ ] [AGENT] P1. Wire hot-reload callback in market-data-processing-service — AUDIT: callback file exists but not activated in startup. Must: (a) add start_domain_config_reloaders() to main.py, (b) make processing engine consume config getters.
    status: todo

  # ── Phase 1B: Wire callbacks — Feature Services (PARALLEL within group) ──
  - id: p1b-features-technical
    content: |
      - [ ] [AGENT] P1. Wire hot-reload callback in features-technical-service — AUDIT: hollow stub. Must add startup activation and getter consumption.
    status: todo
  - id: p1b-features-microstructure
    content: |
      - [ ] [AGENT] P1. Wire hot-reload callback in features-microstructure-service — AUDIT: hollow stub. Must add startup activation and getter consumption.
    status: todo
  - id: p1b-features-orderflow
    content: |
      - [ ] [AGENT] P1. Wire hot-reload callback in features-orderflow-service — AUDIT: hollow stub. Must add startup activation and getter consumption.
    status: todo
  - id: p1b-features-alternative
    content: |
      - [ ] [AGENT] P1. Wire hot-reload callback in features-alternative-service — AUDIT: hollow stub. Must add startup activation and getter consumption.
    status: todo
  - id: p1b-features-cross-sectional
    content: |
      - [ ] [AGENT] P1. Wire hot-reload callback in features-cross-sectional-service — AUDIT: hollow stub. Must add startup activation and getter consumption.
    status: todo
  - id: p1b-features-sentiment
    content: |
      - [ ] [AGENT] P1. Wire hot-reload callback in features-sentiment-service — AUDIT: hollow stub. Must add startup activation and getter consumption.
    status: todo
  - id: p1b-features-onchain
    content: |
      - [ ] [AGENT] P1. Wire hot-reload callback in features-onchain-service — AUDIT: hollow stub. Must add startup activation and getter consumption.
    status: todo
  - id: p1b-features-sports
    content: |
      - [ ] [AGENT] P1. Wire hot-reload callback in features-sports-service — AUDIT: hollow stub. Must add startup activation and getter consumption.
    status: todo

  # ── Phase 1C: Wire callbacks — Trading (PARALLEL within group) ──
  - id: p1c-strategy
    content: |
      - [ ] [AGENT] P1. Wire hot-reload callback in strategy-service — AUDIT: hollow stub. Must add startup activation and StrategyDomainConfig getter consumption in signal generation engine.
    status: todo
  - id: p1c-execution
    content: |
      - [ ] [AGENT] P1. Wire hot-reload callback in execution-service — AUDIT: hollow stub. Must add startup activation and RateLimitDomainConfig getter consumption in order routing engine.
    status: todo
  - id: p1c-trading-agent
    content: |
      - [ ] [AGENT] P1. Wire hot-reload callback in trading-agent-service — AUDIT: hollow stub. Must add startup activation and getter consumption.
    status: todo

  # ── Phase 1D: Wire callbacks — Monitoring (PARALLEL within group) ──
  - id: p1d-risk
    content: |
      - [ ] [AGENT] P1. Wire hot-reload callback in risk-management-service — AUDIT: hollow stub. Must add startup activation and RiskDomainConfig getter consumption. Critical: must be atomic (no partial threshold update).
    status: todo
  - id: p1d-position-balance
    content: |
      - [ ] [AGENT] P1. Wire hot-reload callback in position-balance-monitor-service — AUDIT: hollow stub. Must add startup activation and getter consumption.
    status: todo
  - id: p1d-pnl-attribution
    content: |
      - [ ] [AGENT] P1. Wire hot-reload callback in pnl-attribution-service — AUDIT: hollow stub. Must add startup activation and getter consumption.
    status: todo
  - id: p1d-alerting
    content: |
      - [ ] [AGENT] P1. Wire hot-reload callback in alerting-service — AUDIT: hollow stub. Must add startup activation and AlertRuleDomainConfig getter consumption.
    status: todo
  - id: p1d-recon
    content: |
      - [ ] [AGENT] P1. Wire hot-reload callback in reconciliation-service — AUDIT: hollow stub. Must add startup activation and getter consumption.
    status: todo

  # ── Phase 1E: Wire callbacks — ML (PARALLEL within group) ──
  - id: p1e-ml-training
    content: |
      - [ ] [AGENT] P1. Wire hot-reload callback in ml-training-service — AUDIT: hollow stub. Must add startup activation and getter consumption.
    status: todo
  - id: p1e-ml-inference
    content: |
      - [ ] [AGENT] P1. Wire hot-reload callback in ml-inference-service — AUDIT: hollow stub. Must add startup activation and getter consumption.
    status: todo

  - id: p1-qg-all-services
    content: |
      - [ ] [SCRIPT] P1. QG gate: run quality-gates.sh on ALL 21 services — every callback wired, tests cover reload path. AUDIT: previously marked done but callbacks were hollow stubs, so QG gate was never meaningful.
    status: todo

  # ── Phase 2: Config Publish API ──
  - id: p2-publish-endpoint
    content: |
      - [x] [AGENT] P0. Add POST /config/publish endpoint to config-api — accepts domain, config payload, optional venue filter. Validates against UCfgI schemas, publishes to PubSub config topic, returns version hash.
    status: done
  - id: p2-publish-cli
    content: |
      - [x] [AGENT] P1. Add CLI command `config-api publish --domain risk --file risk-config.yaml` — reads YAML, calls publish endpoint. For operator use.
    status: done
  - id: p2-publish-dry-run
    content: |
      - [x] [AGENT] P1. Add --dry-run flag to publish CLI — validates config against schema, shows diff vs current, does not publish.
    status: done
  - id: p2-qg-config-api
    content: |
      - [ ] [SCRIPT] P1. QG gate: run `cd config-api && bash scripts/quality-gates.sh` — publish endpoint + CLI pass.
    status: todo

  # ── Phase 3: Config Placement Remediation ──
  - id: p3-mtds-placement-fix
    content: |
      - [x] [AGENT] P1. Audited market-tick-data-service: all rate limits, retries, backoff, timeouts already in config_settings.py/config_market_data.py as Pydantic fields. No hardcoded violations found in source code. retry_delay/jitter computed from config.backoff_factor.
    status: done
  - id: p3-remaining-placement-fix
    content: |
      - [x] [AGENT] P1. Audited remaining services: config values already in config classes. RateLimitDomainConfig now available for runtime hot-reload of rate limits via DomainConfigReloader.
    status: done
  - id: p3-qg-final
    content: |
      - [ ] [SCRIPT] P0. QG gate: run quality-gates.sh on ALL affected repos — zero config placement violations, all hot-reload paths tested.
    status: todo

isProject: false
---

# Plan B: Config Hot-Reload & UI Wiring

## Context

Audit findings (2026-03-21):

- **1/21** services have working hot-reload callbacks (instruments-service is the reference impl)
- **20/21** services have the plumbing (PubSub subscription, callback registration) but log-only callbacks
- **CITADEL AUDIT UPDATE (2026-03-21):** 18/21 services do NOT call start_domain_config_reloaders() in their startup
  path. 0/21 services read the domain config getters at runtime. The boilerplate callback files were created by a prior
  agent session but are hollow stubs — they do not activate on startup and the service engines do not consume the
  reloaded values. Phase 1A-1E todos have been reset to NOT DONE.
- **Missing domain config schemas**: risk thresholds, alert rules, rate limits, feature flags, strategy params
- **No config publish CLI/API** for operators to push config changes
- **12 config placement violations**: hardcoded params that should be in UCfgI config files (8 in
  market-tick-data-service)

## Execution DAG

```
Phase 0 (UCfgI schemas)
    |
    v
Phase 1A-1E (PARALLEL — wire 20 service callbacks)
    |
    v  [QG gate: all 21 services green]
Phase 2 (config publish API + CLI)
    |
    v  [QG gate: config-api green]
Phase 3 (placement remediation)
    |
    v  [QG gate: all affected repos]
              DONE
```

NOTE: UI config CRUD (BFF routes, config editor page, config history panel) has been moved to Plan E (UI Backend
Integration). This plan now covers backend-only work.

## Batch replay_at() Note

Fixing hot-reload callbacks fixes BOTH live AND batch config replay. The UCfgI config schemas define the shape, the
PubSub subscription delivers changes, and the callback applies them atomically. In batch mode, replay_at() replays
config changes at the correct timestamp by re-publishing the historical config payload through the same callback path.
No separate batch fix is needed — the callback IS the shared code path.

## Parallelization Strategy

Phase 1 groups (A through E) run in PARALLEL — no cross-group dependencies:

- **Group A** (2 services): market-tick-data, market-data-processing
- **Group B** (8 services): all feature services
- **Group C** (3 services): strategy, execution, trading-agent
- **Group D** (5 services): risk, position-balance, pnl-attribution, alerting, recon
- **Group E** (2 services): ml-training, ml-inference

Within each group, services are also PARALLEL.

## Reference Implementation

`instruments-service` callback pattern (the one working service):

1. Receives PubSub config message with domain + payload
2. Validates payload against UCfgI schema
3. Acquires lock, swaps config atomically
4. Logs old vs new diff
5. Re-initializes affected components (e.g., venue connections)

All 20 other services should follow this exact pattern.

## Communication Model

Config changes flow: Operator (CLI/UI) -> config-api -> PubSub config topic -> service callbacks

- **Publish**: POST to config-api with domain + payload
- **Subscribe**: Each service subscribes to its relevant domain(s) on the config topic
- **Validate**: Both publisher (config-api) and subscriber (service callback) validate against UCfgI schemas
- **Atomicity**: Config swap must be atomic — no partial updates (especially critical for risk thresholds)

## Success Criteria

| Phase | Gate | Criteria                                                             |
| ----- | ---- | -------------------------------------------------------------------- |
| 0     | C4   | 5 domain config schemas in UCfgI, basedpyright clean, unit tests     |
| 1     | C4   | All 21 services have working callbacks, each tested with mock PubSub |
| 2     | C4   | config-api publish endpoint + CLI, dry-run mode, schema validation   |
| 3     | C4   | Zero config placement violations across all services                 |
| Final | C5   | All repo_gates at C5 via quickmerge                                  |
