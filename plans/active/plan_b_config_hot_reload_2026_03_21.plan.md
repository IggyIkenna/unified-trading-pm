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
  - id: p1a-market-tick-data
    content: |
      - [x] [AGENT] P1. Wire hot-reload callback in market-tick-data-service — config snapshot with atomic swap + RateLimitDomainConfig reloader added.
    status: done
  - id: p1a-market-data-processing
    content: |
      - [x] [AGENT] P1. Wire hot-reload callback in market-data-processing-service — config snapshot with atomic swap.
    status: done

  # ── Phase 1B: Wire callbacks — Feature Services (PARALLEL within group) ──
  - id: p1b-features-technical
    content: |
      - [x] [AGENT] P1. Wire hot-reload callback in features-technical-service — on config change: update indicator params (window sizes, thresholds) without restart.
    status: done
  - id: p1b-features-microstructure
    content: |
      - [x] [AGENT] P1. Wire hot-reload callback in features-microstructure-service — on config change: update microstructure calculation params.
    status: done
  - id: p1b-features-orderflow
    content: |
      - [x] [AGENT] P1. Wire hot-reload callback in features-orderflow-service — on config change: update order flow aggregation windows.
    status: done
  - id: p1b-features-alternative
    content: |
      - [x] [AGENT] P1. Wire hot-reload callback in features-alternative-service — on config change: update alternative data source params.
    status: done
  - id: p1b-features-cross-sectional
    content: |
      - [x] [AGENT] P1. Wire hot-reload callback in features-cross-sectional-service — on config change: update cross-sectional calculation universe.
    status: done
  - id: p1b-features-sentiment
    content: |
      - [x] [AGENT] P1. Wire hot-reload callback in features-sentiment-service — on config change: update sentiment source weights, refresh intervals.
    status: done
  - id: p1b-features-onchain
    content: |
      - [x] [AGENT] P1. Wire hot-reload callback in features-onchain-service — on config change: update on-chain polling intervals, contract addresses.
    status: done
  - id: p1b-features-sports
    content: |
      - [x] [AGENT] P1. Wire hot-reload callback in features-sports-service — on config change: update odds source priorities, staleness thresholds.
    status: done

  # ── Phase 1C: Wire callbacks — Trading (PARALLEL within group) ──
  - id: p1c-strategy
    content: |
      - [x] [AGENT] P1. Wire hot-reload callback in strategy-service — on config change: update alpha thresholds, position sizing params, rebalance intervals. Use StrategyDomainConfig.
    status: done
  - id: p1c-execution
    content: |
      - [x] [AGENT] P1. Wire hot-reload callback in execution-service — on config change: update venue rate limits, order routing weights, slippage tolerance. Use RateLimitDomainConfig.
    status: done
  - id: p1c-trading-agent
    content: |
      - [x] [AGENT] P1. Wire hot-reload callback in trading-agent-service — on config change: update agent decision thresholds, kill switch params.
    status: done

  # ── Phase 1D: Wire callbacks — Monitoring (PARALLEL within group) ──
  - id: p1d-risk
    content: |
      - [x] [AGENT] P1. Wire hot-reload callback in risk-management-service — on config change: update risk thresholds (drawdown, VaR, position limits). Use RiskDomainConfig. Critical: must be atomic (no partial threshold update).
    status: done
  - id: p1d-position-balance
    content: |
      - [x] [AGENT] P1. Wire hot-reload callback in position-balance-monitor-service — on config change: update balance alert thresholds, reconciliation intervals.
    status: done
  - id: p1d-pnl-attribution
    content: |
      - [x] [AGENT] P1. Wire hot-reload callback in pnl-attribution-service — on config change: update attribution model params, benchmark references.
    status: done
  - id: p1d-alerting
    content: |
      - [x] [AGENT] P1. Wire hot-reload callback in alerting-service — on config change: update alert rules, severity mappings, channel routing. Use AlertRuleDomainConfig.
    status: done
  - id: p1d-recon
    content: |
      - [x] [AGENT] P1. Wire hot-reload callback in reconciliation-service — on config change: update reconciliation schedules, tolerance thresholds.
    status: done

  # ── Phase 1E: Wire callbacks — ML (PARALLEL within group) ──
  - id: p1e-ml-training
    content: |
      - [x] [AGENT] P1. Wire hot-reload callback in ml-training-service — on config change: update training hyperparams, data window sizes, feature selection.
    status: done
  - id: p1e-ml-inference
    content: |
      - [x] [AGENT] P1. Wire hot-reload callback in ml-inference-service — on config change: update inference batch sizes, model version overrides, feature flags.
    status: done

  - id: p1-qg-all-services
    content: |
      - [x] [SCRIPT] P1. QG gate: run quality-gates.sh on ALL 21 services — every callback wired, tests cover reload path.
    status: done

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
      - [ ] [AGENT] P1. Fix 8 config placement violations in market-tick-data-service — move hardcoded venue configs, rate limits, and reconnection params from source code to UCfgI domain config files. Replace inline constants with config lookups.
    status: todo
  - id: p3-remaining-placement-fix
    content: |
      - [ ] [AGENT] P1. Fix remaining 4 config placement violations (from audit) across other services — move hardcoded params to UCfgI config files.
    status: todo
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
