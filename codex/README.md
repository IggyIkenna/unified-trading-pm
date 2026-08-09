---
scope: [engineer, admin]
---

# Unified Trading Codex

The governing principles for the Unified Trading System. This repository is the single source of truth: if the code
disagrees with the codex, either the code or the codex needs updating.

## What Is the Codex?

"Codex" means a systematic collection of laws, rules, and principles. This repo documents how every service, mode
(batch/live), asset class, and client deployment should behave in the Unified Trading System.

## How to Navigate

Every directory follows the same pattern: `README.md` (universal) -> `batch/` (batch-specific) -> `live/`
(live-specific) -> `per-service/` (service-specific deviations). Read top-down: the README is always true, batch/live
extends it, per-service captures what is unique.

**SSOT:** See [`00-SSOT-INDEX.md`](./00-SSOT-INDEX.md) for the master map of canonical data sources.

### Directory Map

| Directory                | One-line description                                                                                            |
| ------------------------ | --------------------------------------------------------------------------------------------------------------- |
| `00-SSOT-INDEX.md`       | Master data source index — where every piece of information lives                                               |
| `00-getting-started/`    | Workflow diagrams, bootstrapping, E2E workflow                                                                  |
| `01-domain/`             | Business domain: instruments, asset classes, signal-based strategies, client model                              |
| `02-data/`               | Data schemas, subscription/publishing model, partitioning, data quality                                         |
| `02-venues/`             | Venue registry, prime brokers, integration specs                                                                |
| `03-deployment/`         | Deployment surface docs: data-status UI surface, honest-coverage % display                                      |
| `03-observability/`      | 3-tier event logging (lifecycle + resource + domain), alerting, monitoring                                      |
| `03-services/`           | Per-service documentation and specifications                                                                    |
| `04-architecture/`       | Batch-live symmetry, deployment topology, concurrency, pipeline DAG                                             |
| `05-infrastructure/`     | Cloud-agnostic abstractions, unified libraries, CI/CD, Terraform, Docker                                        |
| `06-coding-standards/`   | Quality gates, testing, contribution workflow, dependency management                                            |
| `07-security/`           | Secrets management, API keys, permissions, dependency scanning                                                  |
| `08-workflows/`          | Local dev, batch DAG, version cascade, config injection, service-pair flows                                     |
| `09-strategy/`           | Strategy architecture v2 (families, archetypes, axes, cross-cutting)                                            |
| `10-audit/`              | Codex compliance checklists (canonical, 100+ items per service across 9 principle areas)                        |
| `11-project-management/` | Issue tracking, roadmaps (batch/live production), priority matrix, milestones                                   |
| `12-agent-workflow/`     | AI agent workflow guides, task templates, sub-agent patterns                                                    |
| `13-codex-governance/`   | SSOT boundary rules, section registry, governance README                                                        |
| `14-customer-journeys/`  | **Customer playbook SSOT**: 3 audiences × 3 environments × 3 auth tiers × 4 catalogues + 177-page triage matrix |
| `15-runbooks/`           | Live-trading on-call runbooks: alerting, backfill, position reconciliation, smoke testing, kill-switch          |
| `16-strategy-playbooks/` | Domain strategy + infra playbooks (DeFi, ML, strategy, infra-spec)                                              |

### Start Here

| Goal                  | Read                                                                                                                                                                                                            |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| New service developer | `04-architecture/README.md` → `06-coding-standards/README.md` → service's per-service docs                                                                                                                      |
| AI agent              | `unified-trading-pm/DOC_INDEX.generated.md` (grep, never read whole) → `authoritative_for:` frontmatter facet → confirm `summary:` → open doc — see `/codex/11-project-management/doc-frontmatter-schema.md` §1 |
| Code reviewer         | `10-audit/` checklists for compliance verification                                                                                                                                                              |
| Ops / infra engineer  | `deployment-service/configs/` → `05-infrastructure/` → `00-SSOT-INDEX.md`                                                                                                                                       |

## The System at a Glance

- **13 service repos** total; **11 pipeline services**: instruments -> market-tick-data-service ->
  market-data-processing -> features-calendar -> features-delta-one, features-volatility, features-onchain ->
  ml-training -> ml-inference -> strategy -> execution-service _(corporate-actions decommissioned 2026-02-10 — see
  `10-audit/live/corporate-actions.yaml`)_
- **1 shared library**: unified-trading-library
- **4 deployment repos**: deployment-service (orchestration + configs + terraform), deployment-api (FastAPI),
  deployment-ui (React), system-integration-tests (Layer 3a/3b)
- **Asset classes**: equities, crypto (CeFi), DeFi, CFDs, options, futures, sports betting
- **Canonical categories**: CeFi, TradFi, DeFi, Sports
- **Cloud**: GCP primary, AWS secondary
- **Latency**: Signal-based strategies with <2s end-to-end latency target

## Pipeline DAG

```mermaid
flowchart TB
    subgraph data_io["Data I/O Layer"]
        instruments[instruments-service]
    end

    subgraph market_data["Market Data Layer"]
        tick[market-tick-data-service]
        processing[market-data-processing-service]
    end

    subgraph features["Feature Layer"]
        fs[features-service<br/>8 families: calendar · commodity · cross_instrument<br/>delta_one · multi_timeframe · onchain · sports · volatility<br/>consolidated 2026-05-08]
    end

    subgraph ml["ML Layer"]
        train[ml-training-service]
        inference[ml-inference-service]
    end

    subgraph execution["Execution Layer"]
        strategy[strategy-service]
        exec[execution-service]
    end

    instruments --> tick
    tick --> processing
    instruments --> processing

    processing --> fs
    tick --> fs

    fs --> train

    train --> inference
    fs --> inference

    inference --> strategy
    fs --> strategy
    instruments --> strategy

    strategy --> exec
    tick --> exec
    instruments --> exec
```

## Design Philosophy

- Abstract the commonalities, document the deviations
- Batch and live should be as similar as possible
- Services should be as similar as possible
- Asset class, instrument, strategy, and exchange should be as agnostic as possible
- Document what is genuinely different

## How to Use This Repo

| Goal                   | Read                                                                                                                                                                             |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Building a new service | `01-domain/`, `04-architecture/`, `06-coding-standards/`, then service's per-service docs in `07-services/`. **Checklist:** `deployment-service/configs/checklist.template.yaml` |
| Contributing code      | `06-coding-standards/contribution-guide.md`                                                                                                                                      |
| Debugging production   | `03-observability/`, `08-workflows/incident-response.md`                                                                                                                         |
| Onboarding a client    | `08-workflows/client-lifecycle.md`                                                                                                                                               |
| Assessing readiness    | `10-audit/`                                                                                                                                                                      |
| Finding canonical SSOT | [`00-SSOT-INDEX.md`](./00-SSOT-INDEX.md)                                                                                                                                         |

## Development Setup

This repository uses pre-commit hooks to ensure consistent formatting and quality of documentation.

### Quick Setup

```bash
# Install and setup pre-commit hooks
./scripts/setup-pre-commit.sh
```

### What Gets Checked

- **Prettier**: Formats markdown, YAML, and JSON files
- **Ruff**: Lints and formats Python scripts
- **Basic checks**: Trailing whitespace, end-of-file fixers, YAML/TOML validation

See [`.github/PRE_COMMIT_SETUP.md`](.github/PRE_COMMIT_SETUP.md) for detailed setup instructions.

## Relationship to Code

- This repo documents **how things should be**
- The code repos implement **what is**
- The audit (10-audit/) tracks the gap
- Goal: close the gap to 100% compliance for production readiness

<!-- quickmerge pipeline test 2025-03-13 -->
