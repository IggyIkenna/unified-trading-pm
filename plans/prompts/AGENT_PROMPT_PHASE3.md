# Agent Prompt — Phase 3: Service Hardening & Integration

> Paste this entire prompt into a new agent session to execute Phase 3. REQUIRES Phase 1 AND Phase 2 fully complete.
> Verify preconditions before starting.

> **2026-03-24 topology note:** The **active** surface is **`unified-trading-system-ui`** + **`deployment-ui`** and APIs
> (`scripts/dev/ui-api-mapping.json`). Sections below that list **11 UIs** or **`execution-results-api`** are
> **historical** parallel-agent staging; legacy repos live under workspace-root **`archive/README.md`**.

---

Follow all workspace cursor rules in .cursorrules. No summary docs (no-summary-docs.mdc). uv not pip. quickmerge not git
push. basedpyright <dir>/ not basedpyright. Delete deprecated code; no parallel code paths. Search unified libraries
before implementing anything new.

WORKSPACE_ROOT=${UNIFIED_TRADING_WORKSPACE_ROOT}/unified-trading-system-repos All Python/pytest/ruff/basedpyright/QG
commands: cd $WORKSPACE_ROOT
&& source .venv-workspace/bin/activate first.

---

## Standard of Work — Citadel Audit-Worthy

> **When in doubt, assume a senior quant engineer at a top-tier fund (Citadel, Two Sigma, DE Shaw) is reviewing every
> PR. Build accordingly.**

This means — no exceptions, no shortcuts:

- **No silent errors** — every `except` block must reraise, raise a typed error, or log at ERROR + reraise. `pass` is a
  build failure.
- **No empty fallbacks** — `os.getenv(KEY, '')` is forbidden. Use `UnifiedCloudConfig` or fail on missing config.
- **No untyped boundaries** — every API endpoint, PubSub message, and GCS schema uses Pydantic models. `dict[str, Any]`
  at a boundary is a type violation.
- **No service→service Python imports** — services communicate via HTTP, GCS, or PubSub only.
- **No test project IDs in production code** — `central-element-323112` → `test-project` in tests, not in production
  paths.
- **No TODO comments** in production code — open a GitHub issue and link it.
- **Full observability** — every request logs `correlation_id`, `service_name`, `timestamp`. Every failure is
  structured.
- **Every secret** through Secret Manager. Every config through `UnifiedCloudConfig`.
- **Every external call** has retry logic (`@with_retry` from UTL) and a timeout.
- **Every async operation** has an explicit timeout — no indefinite awaits.
- If it would fail a Citadel code review, it is not done.

---

## Preconditions (verify ALL before starting)

```bash
# T0–T3 libraries all green
# Check spot: did UDC pass D5?
ls unified-domain-client/scripts/quickmerge.sh  # exists
python -c "import unified_domain_client"          # exits 0
bash unified-domain-client/scripts/setup.sh --check  # exits 0

# Deployment repos exist
ls deployment-service/ deployment-api/ deployment-ui/ system-integration-tests/

# No old names anywhere
rg 'market-tick-data-handler|client-reporting-api|alerting-service|ml-training-ui|execution-analytics-ui' --type py
# must return zero hits
```

If any check fails: STOP. Complete Phase 1/2 first.

---

## SSOT

| Source                 | Path                                                                                                                           |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Workspace manifest DAG | `unified-trading-pm/WORKSPACE_MANIFEST_DAG.svg` — 63 repos, 13 levels (L0-L12, AUTHORITATIVE). L0=PM, L1=codex, L2+=code repos |
| Runtime topology       | `deployment-service/configs/RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg`                                                               |
| Service pair flows     | `unified-trading-/codex/08-workflows/service-pair-flows.md`                                                                    |
| Tier architecture      | `unified-trading-/codex/04-architecture/TIER-ARCHITECTURE.md`                                                                  |
| Batch/live symmetry    | `unified-trading-/codex/04-architecture/batch-live-symmetry.md`                                                                |
| Integration layers     | `unified-trading-/codex/06-coding-standards/integration-testing-layers.md`                                                     |

---

## Canonical Repo Names — Enforce at Every Step

**T4 Services (19 total):**

| Abbrev | Canonical Name                    | Batch |
| ------ | --------------------------------- | ----- |
| IS     | instruments-service               | A     |
| MTDH   | market-tick-data-service          | B     |
| MDPS   | market-data-processing-service    | B     |
| FCS    | features-calendar-service         | C     |
| FDS    | features-delta-one-service        | C     |
| FVS    | features-volatility-service       | C     |
| FOS    | features-onchain-service          | C     |
| FSS    | features-sports-service           | C     |
| FCIS   | features-cross-instrument-service | C     |
| FMTS   | features-multi-timeframe-service  | C     |
| MLTR   | ml-training-service               | D     |
| MLIN   | ml-inference-service              | D     |
| STR    | strategy-service                  | E     |
| EXEC   | execution-service                 | E     |
| PBS    | position-balance-monitor-service  | F     |
| PNL    | pnl-attribution-service           | F     |
| RES    | risk-and-exposure-service         | F     |
| AS     | alerting-service                  | F     |

**T5 API Services (active SSOT):** `unified-trading-api`, `auth-api`, `deployment-api`, `client-reporting-api`,

**T6 UIs (historical list — archived split UIs):** `batch-audit-ui`, `client-reporting-ui`, `deployment-ui`,
`execution-analytics-ui`, `live-health-monitor-ui`, `logs-dashboard-ui`, `ml-training-ui`, `onboarding-ui`,
`settlement-ui`, `strategy-ui`, `trading-analytics-ui` — **active:** `unified-trading-system-ui` + `deployment-ui` only.

---

## Naming Check — Run at Step A of Every Repo

```bash
rg 'market-tick-data-handler|market_tick_data_handler' .    # must be zero
rg 'client-reporting-api|client_reporting_api' .    # must be zero
rg 'alerting-service|alerting_service' .                      # must be zero
rg 'position-balance-monitor[^-s]' .                        # must be zero (bare form without -service)
rg 'ml-training-ui|ml_training_ui' .                    # must be zero
rg 'execution-analytics-ui|execution_analytics_ui' .                              # must be zero
```

Any hit = fix at ALL levels before continuing (pyproject.toml, Python package dir, all imports across 57 repos, AR
package, cloudbuild.yaml, Cloud Build trigger, workspace-manifest.json, runtime-topology.yaml, cursor rules, codex docs,
PubSub topics, Secret Manager, Cloud Run service name).

---

## Bottom-Up Development Rule — No Exceptions

> If a service needs new functionality that does not exist in a library, add it to the correct library FIRST. Never
> define schemas, error types, event names, or contracts inline in a service.

| If you need...                       | Add to first                           | Tier |
| ------------------------------------ | -------------------------------------- | ---- |
| New error schema / typed exception   | `unified-api-contracts` (AC)           | T0   |
| New internal event / domain contract | `unified-internal-contracts` (UIC_INT) | T0   |
| New lifecycle event name             | `unified-trading-library` (UEI)        | T0   |
| New config field                     | `unified-config-interface` (UCI)       | T0   |
| New cloud primitive                  | `unified-cloud-interface` (UCLI)       | T0   |
| New market schema / adapter protocol | `unified-market-interface` (UMI)       | T2   |
| New domain entity                    | `unified-domain-client` (UDC)          | T3   |

**Workflow:** Add to library → run D5 on that library → bump version → `--dep-branch` cascade to all consumers → use in
service. No shortcuts.

---

## Testing Progression — Fastest Feedback First

Every service follows this ladder in order. Fix each step before running the next.

| Step         | Command                    | ~Time   | Catches                                                       |
| ------------ | -------------------------- | ------- | ------------------------------------------------------------- |
| Import smoke | `python -c "import <pkg>"` | 2s      | Broken `__init__`, circular imports, missing deps             |
| D1           | `--lint-only`              | 30s     | Syntax, formatting, import order                              |
| D2           | `--unit-only`              | ~2 min  | Type errors, unit test failures                               |
| D3           | `--qg-only`                | ~5 min  | Integration failures, coverage gaps — no git, safe to retry   |
| D4           | `--quick`                  | ~8 min  | Full QG + git ops, no act                                     |
| D5           | (no flags)                 | ~15 min | Full pipeline with act simulation — the only gate that counts |

**D5 is the only valid green gate.** `--quick` alone is not sufficient for tier promotion.

**Error handling (Step B every service):** Every `except` block must reraise, raise typed error, or log ERROR + reraise.
Silent `pass` = build failure. Missing typed error class → add to AC/UIC_INT first (bottom-up rule).

**File/function size (Step C every service):**

```bash
find . -name "*.py" ! -path "./.venv*" ! -path "*/tests/*" | xargs wc -l 2>/dev/null | sort -rn | awk '$1 > 900 {print}'
```

Any file >900 lines → split by SRP before starting the D1–D5 ladder.

---

## DAG Pipeline Order — Invariant

**Never start batch N until batch N-1 is fully D5 green.**

```
T4 BATCH A:  IS
T4 BATCH B:  MTDH  MDPS                             (parallel, after IS D5)
T4 BATCH C:  FCS  FDS  FVS  FOS  FSS  FCIS  FMTS    (parallel, after B D5)
T4 BATCH D:  MLTR  MLIN                             (parallel, after C D5)
T4 BATCH E:  STR   EXEC  SVS                        (parallel, after D D5)
T4 BATCH F:  PBS   PNL   RES   AS                   (parallel, after E D5)
T5:          ERA   MDA   CRA                         (parallel, after ALL T4 D5)
T6:          11 UIs in parallel batches of 4         (after ALL T5 D5)
```

---

## Per-Service Step Pattern

Every service (T4/T5) and UI (T6) follows this pattern:

**Step A — Connectivity audit + naming check:**

- `bash scripts/setup.sh --check` exits 0 (environment healthy)
- Run the naming check commands above (zero hits required)
- `python -c 'import <package>'` exits 0
- Zero `os.getenv(API_KEY)`, zero hardcoded URLs, zero direct `requests`/`aiohttp` to venues — all via UDC/UMI/UTEI/URDI
- `cloudbuild.yaml` image tag uses canonical name
- AR package name matches `workspace-manifest.json`
- Populate `AGENTS.md` from template (`unified-trading-pm/templates/AGENTS.md`) with repo-specific caveats, known test
  failures, and isolation notes

**Step B — Tests first (before any code rewrite):**

- Write/fix unit tests first
- Add `tests/unit/test_schema_robustness.py`: required field missing → `ValidationError`; optional absent → passes;
  wrong type → fails
- Add `tests/unit/test_imports.py`: imports every public module — catches broken `__init__` in CI
- Coverage: every new code path has a test

**Step C — Code adjustments:**

- Fix all violations found in Step A
- `UPLOAD_STARTED` / `UPLOAD_COMPLETED` → `PERSISTENCE_STARTED` / `PERSISTENCE_COMPLETED`
- Remove all service→service Python deps (HTTP/GCS/PubSub only)
- Wire batch/live seam tests
- Split any file >900 lines by SRP

**D1 → D5:** Run quickmerge ladder. Fix each step before the next. D5 = service green gate.

---

## Tier 4 — Batch Notes

**Batch A — instruments-service:**

- Wire to URDI: replace direct exchange REST calls with `get_reference_adapter(venue).get_instruments()`
- Fix event naming in `cloud_instrument_storage.py`

**Batch B — market-tick-data-service + market-data-processing-service:**

- Naming: verify zero hits for `market-tick-data-handler` everywhere
- MDPS live seams: `live_data_source.py` Pub/Sub subscriber + `broadcast_sink.py` publisher; engine mode-agnostic
- MDPS: ~1yr rolling window in Redis

**Batch C — 7 Feature Services:**

- FCIS + FMTS: consume from L3 via GCS/PubSub — no direct Python import from other feature services
- Features trigger on MDPS completion PubSub event — not a timer

**Batch D — ML Pipeline:**

- Remove `ml-training-service` from `ml-inference-service` `pyproject.toml` — share via UML only
- ML inference: PubSub subscription for live features (not BigQuery polling)

**Batch E — strategy-service + execution-service:**

- execution-service: split `engine.py` (2826L) by SRP; fix 201 bare excepts; remove service→service Python deps
- Fix `central-element-323112` → `test-project` in all test files

**Batch F — position-balance-monitor-service + pnl-attribution-service + risk-and-exposure-service + alerting-service:**

- Naming: zero hits for `position-balance-monitor` (bare) and `alerting-service` everywhere
- Circuit breaker: alerting-service publishes `CIRCUIT_BREAKER_OPEN` to PubSub
- Kill switch: deployment-api `/kill-switch` → PubSub → execution-service + strategy-service

---

## Tier 5 — API Services

3 agents in parallel after all T4 D5:

- Naming: zero hits for `client-reporting-api` everywhere
- Add CDC (Consumer-Driven Contract) tests for ERA/MDA/CRA
- Replace all `dict[str, Any]` at API boundaries with Pydantic response models
- SSE endpoints (sse-starlette) on ERA + live-health-monitor
- Google OAuth SA token inter-service auth
- `/health` + `/readiness` probes on all 3

---

## Tier 6 — UIs (11 repos)

**Before starting T6:** `ui-local-dev-setup` — add `.env.local.example` to all 11 UI repos. Port map:

11 agents in parallel after all T5 D5:

1. `trading-analytics-ui` — Google OAuth TRADER; /positions /pnl /executions /risk /orderbook /latency
2. `execution-analytics-ui` — **canonical name; old name `execution-analytics-ui` is wrong everywhere** — TCA + alpha +
   execution analytics; SSE from execution-results-api
3. `live-health-monitor-ui` — ServiceStatusGrid, CPUMemoryTimeSeries, PubSubLagBars, DLQ badges, Alerts SSE
4. `onboarding-ui` — AMLScreening, FeeStructureConfig, HWMInit, APIKeyManagement, VenueOnboarding, StrategyOnboarding
   (Google OAuth ADMIN)
5. `strategy-ui` — BacktestGridResult → StrategyConfig promotion; POST /api/v1/config/promote; ConfigStore; deployed_by
   from OAuth
6. `client-reporting-ui` + `settlement-ui` — assess data schema availability; scope SSE integration
7. `ml-training-ui` — **canonical name; old name `ml-training-ui` is wrong everywhere** — /experiments,
   /experiments/:runId/deploy, /models, /training-runs (Google OAuth)
8. `logs-dashboard-ui` + `batch-audit-ui` — assess data schema availability; scope SSE integration
9. `deployment-ui` — orchestrator run status SSE, Cloud Build trigger buttons, shard calculator viz, Cloud Run health
   panel
10. `onboarding-ui` AI summaries — add `ai_summary.py` using claude-3-5-haiku; API key via Secret Manager
    `anthropic-api-key`
11. Grafana dashboard exports (trading-overview.json, system-health.json) + `03-observability/prometheus-metrics.md`

---

## Final QG Sweep (after all T0–T6 green, before post-refactor)

10 parallel agents:

- Upgrade `reportAny` from `'warning'` to `'error'` in ALL repos; fix every Any-type violation
- Final `rg` sweep: zero old names, zero `os.getenv(KEY, '')`, zero silent except blocks
- Fix all remaining `ARCHITECTURAL_VIOLATION` suppressions
- Reduce `# type: ignore` to <10 total, each documented in `QUALITY_GATE_BYPASS_AUDIT.md`
- Venue name canonicalization: binance/okx/deribit/bybit → UCI venue constants
- Run QG on all repos; record final pass/fail + coverage % in manifest `ci_status`

---

## Post-Refactor Sequence — Strictly Ordered, No Shortcuts

```
ALL TIERS GREEN (T0–T6, D5 each) + Final QG sweep
  ↓ Step 1: Sandbox deploy — all T4 services via deployment-service CLI
  ↓ Step 2: GET /infra/health — GCS buckets, PubSub topics, IAM, secrets all pass
  ↓ Step 3: pytest -m smoke (system-integration-tests) — happy path, <5 min
  ↓ Step 4: pytest -m full_e2e (system-integration-tests) — corner cases, 15–30 min
  ↓ Step 5: Declare healthy → merge staging → main → v1.0.0
```

If any step fails: fix and re-run **that step**. Never skip forward. L3b passing is required before declaring healthy.

---

## Integration Layers

| Layer                   | Where                                            | When                 |
| ----------------------- | ------------------------------------------------ | -------------------- |
| L0 — Contract alignment | unified-api-contracts, UMI, URDI                 | Done in Phase 2      |
| L1 — Schema robustness  | Per-service `test_schema_robustness.py`          | Each service Step B  |
| L2 — Infra verification | `GET /infra/health` on deployment-api            | After sandbox deploy |
| L3a — Pipeline smoke    | `pytest -m smoke` in system-integration-tests    | After L2 passes      |
| L3b — Full E2E          | `pytest -m full_e2e` in system-integration-tests | After L3a passes     |

---

## Done Criteria

- [ ] All 19 T4 services pass D5 (in DAG batch order)
- [ ] All 3 T5 API services pass D5
- [ ] All 11 T6 UIs pass D5
- [ ] Final QG sweep: zero Any-types, zero arch violations, zero old names
- [ ] `rg` for all old names returns zero hits across all 57 repos
- [ ] Sandbox deploy stable
- [ ] `/infra/health` all green
- [ ] `pytest -m smoke` passes
- [ ] `pytest -m full_e2e` passes
- [ ] Declared healthy; versions bumped to 1.0.0

---

## Key Files

- `unified-trading-pm/plans/active/phase3_service_hardening_integration.md` — full task list
- `unified-trading-pm/workspace-manifest.json` — repo registry
- `deployment-service/configs/runtime-topology.yaml` — runtime topology
- `unified-trading-/codex/08-workflows/service-pair-flows.md` — service-to-service data flows
- `unified-trading-/codex/04-architecture/TIER-ARCHITECTURE.md` — tier rules
- `unified-trading-/codex/06-coding-standards/integration-testing-layers.md` — 4-layer strategy
- `unified-trading-/codex/04-architecture/batch-live-symmetry.md` — batch/live seam pattern
- `unified-trading-pm/scripts/workspace-bootstrap.sh` — full workspace bootstrap for fresh VMs
- `unified-trading-pm/templates/AGENTS.md` — per-repo caveats template (populate during hardening)
- `.cursor/rules/delete-deprecated.mdc` — no backward compat
