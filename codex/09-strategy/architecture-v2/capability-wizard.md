---
scope: [engineer, admin]
last_reviewed: 2026-06-11
---

# Capability Wizard — manifest, prospectus, walkthrough

## What is this?

The capability wizard is three artifacts over one data model:

1. **Capability manifest** — a machine-generated SSOT (`generate_capability_manifest.py`, in the PM repo's
   `scripts/openapi/` generator family) describing everything the system can do as a graph of typed edges: archetype →
   instrument_type → venue → execution algo → order semantics → data source/mode → features → models → fund structure →
   wallet/collateral. Every edge carries a status: `available | partial | not_available | not_registered`.
2. **Strategy prospectus generator** — a script that takes a concrete strategy configuration + the manifest and renders
   a document as if presenting to the internal allocation team or a potential investor: what the strategy does, how it
   makes decisions (full alpha disclosure while in debugging mode), exposures and how they are normalised (e.g.
   staked-ETH vs ETH), a mermaid fund-flow diagram (treasury/trading wallets and venues as boxes, deposit → conversion →
   venue paths), risk scenarios, applicable circuit breakers and their configuration, and expected
   returns/Sharpe/max-drawdown from backtests.
3. **Walkthrough wizard UI** — progressive configuration where **every dropdown IS the availability answer**: each step
   offers only what remains possible given prior answers; unavailable options are shown greyed with the reason and gap
   type; every config field carries side-by-side help text from pydantic `Field(description=…)`.

## The four use cases

1. **Visibility (internal)** — see into strategy capabilities end-to-end: instruments, venues, actual data availability,
   risk and margining, execution capabilities, flow of funds, and what strategy decision-making is possible/configurable
   per archetype.
2. **End-to-end parameterization** — parameterize the whole system around a stated execution preference. The wizard
   exposes whether we are flexible enough; any question it cannot answer is itself a finding (system expansion candidate
   or missing registry).
3. **Two-sided audit** — verify that what the wizard thinks is possible is actually possible in code, in all directions.
   Dead ends are classified: **logical** (e.g. options on sports venues — correctly impossible) vs **unbuilt**
   (adapter/registry/code not written). Orphaned config, instruments, venues, and strategy types fall out of the same
   sweep. The prospectus is diffed against the hand-written archetype docs in [`archetypes/`](archetypes/) —
   wizard-thinks vs codex-says vs code-does.
4. **Client onboarding (eventual)** — a lighter client-facing wizard ending in a strategy config, a credentials
   checklist ("what I need from you: these API keys"), and an on-demand backtest of the configured preference. Advanced
   successor to the public strategy questionnaire.

## Architectural rules

- **Static capability ≠ runtime data availability.** The manifest answers "does the code support it" and is generated
  from registries/code with no live system. "Is the data actually there" delegates to deployment-api
  `/api/data-status/*` (the Data Status drilldown remains the runtime catalogue). The two compose: e.g. min-data-to-run
  per (archetype, venue, timeframe) is derived from feature-group lookbacks × ML training windows in the manifest, then
  checked against live shard counts via the drilldown API.
- **No silent omissions.** A dimension the exporter cannot populate is emitted as a typed gap
  (`missing_registry | missing_extraction | needs_code_scan | logical_dead_end`), never dropped.
- **Escalation order: script → test → agent.** As much as possible is scripted. Issues found get tests pinned to them.
  Interactive agents (agent-orchestrator) are invoked only for `needs_code_scan` gaps, and their answers are written
  back into the manifest as annotations so credits are spent once.
- **Schema first.** Capability areas without a registry (collateral/haircuts/LTV per venue, fees at multiple
  granularities, simulation/matching assumptions, fund-structure offerings, order-semantics per venue adapter,
  trading-agent/LLM permissions) get their UAC schema defined before backfill — the manifest emitting `not_registered`
  for them is the forcing function.

## Surfaces

| Surface                                          | Repo                                          | Audience                        |
| ------------------------------------------------ | --------------------------------------------- | ------------------------------- |
| Walkthrough wizard (route group `app/(wizard)/`) | unified-trading-system-ui                     | internal now, client-lite later |
| Capability matrix tab (next to Data Status)      | deployment-ui                                 | operators                       |
| Manifest + prospectus + audit reports            | unified-trading-pm `scripts/openapi/` outputs | engineers, CI                   |

## See also

- Question bank (every wizard question pinned to its code anchor):
  [`capability-wizard-question-bank.md`](capability-wizard-question-bank.md)
- Plan:
  [`plans/active/capability_wizard_and_manifest_2026_06_11.md`](../../../plans/active/capability_wizard_and_manifest_2026_06_11.md)
- Gap tracker:
  [`plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md`](../../../plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md)
- Archetype taxonomy:
  [`enums.py` StrategyArchetype/StrategyFamily](../../../../unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py) +
  [`archetype_capability.py`](../../../../unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability.py)
- Wallet/capital flow:
  [`codex/04-architecture/wallet-hierarchy-and-capital-flow.md`](../../04-architecture/wallet-hierarchy-and-capital-flow.md)
- Generator suite: `unified-trading-pm/scripts/openapi/generate-unified-openapi.sh` and `docs/ui-alignment-ssot.md`

## Current state (shipped 2026-06-11 — autonomous build session)

| Piece                            | Where                                                    | Evidence                                                                                                                |
| -------------------------------- | -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Generator repair (Phase 0)       | `unified-trading-pm/scripts/openapi/`                    | PM@50bdbcd36 (PR #268) — service auto-discovery, fail-on-drift, architecture_v2 extraction                              |
| Manifest schema + gap registries | `unified_api_contracts/internal/architecture_v2/`        | UAC@6f31f59 — capability_manifest + collateral/fees/sim/fund-structures/order-semantics/agent-capability (honest-empty) |
| Capability manifest v1           | `unified-api-contracts/openapi/capability-manifest.json` | PM@78b2e893a (PR #270) + UAC@1bc2f07 — 409 nodes / 663 edges, all gaps typed; orphan report alongside                   |
| Prospectus ×57 + two-sided audit | `unified-api-contracts/openapi/prospectus/`              | PM PR #272 + UAC@fe37eae — 1 contradiction + 2 orphan docs found                                                        |
| Scenario stepper                 | `e2e-testing/scripts/strategy/`                          | UAC@6262c3f + strategy-service@e0ed11c + e2e-testing@3e41ecb — real engine, kill-trips proven                           |
| Annotation write-back            | `unified-trading-pm/scripts/openapi/`                    | PM@f84a119 — capability-annotations.yaml sidecar + _capability_annotations.py + emit_capability_gap_todos.py; 2 annotated edges, 1 P2 todo |
| Backtest-on-demand               | `e2e-testing/scripts/strategy/`                          | e2e-testing@194d66b — backtest_from_wizard_config.py; GroupBRunner wired; honest PRECHECK_UNAVAILABLE verdict confirmed |
| Wizard UI (`/wizard`)            | `unified-trading-system-ui/app/(wizard)/`                | uts-ui@9f40331 — pw:L2 8/8                                                                                              |
| Capability tab                   | `deployment-ui` (per-service tab next to Data Status)    | dep-ui@13ac831 — pw:L2 6/6                                                                                              |

Open work: wizard stepper stage, registry backfills, Wave-2 enhancements (operator sign-off pending).

## How to run / view

- **Wizard UI**: `cd unified-trading-system-ui && pnpm install && NEXT_PUBLIC_MOCK_API=true pnpm dev` →
  `http://localhost:3000/wizard` (engine warning on node < 22 is benign; manifest data is committed in
  `lib/registry/capability-manifest.json`, no backend needed).
- **Capability tab**: `cd deployment-ui && npm install && npm run dev` → `http://localhost:5183` → pick a service →
  "Capability" tab (static manifest; Data Status needs deployment-api but Capability does not). Node ≥ 20.19 required
  for the rolldown binding (finding F19 has the workaround).
- **Scenario stepper**: from `e2e-testing/`, strategy-service venv, credential-free:
  `CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true python scripts/strategy/scenario_stepper.py --steps scripts/strategy/scenarios/apd_price_dispersion_btc.json`
  (or `--interactive` REPL).
- **Regenerate manifest/prospectus** (UAC venv suffices for these steps):
  `python scripts/openapi/generate_capability_manifest.py` → `generate_strategy_prospectus.py` →
  `audit_prospectus_vs_codex.py`; full-suite `generate-unified-openapi.sh` needs `.venv-workspace` — see finding F12
  (config-registry regen is DESTRUCTIVE without it).
- **Escalation emitter** (append `[AGENT] P2.` todos for unannotated needs_code_scan gaps — idempotent):
  from `unified-trading-pm/scripts/openapi/`, UAC venv:
  `python emit_capability_gap_todos.py` (reads `unified-api-contracts/openapi/capability-manifest.json`,
  appends under `## Escalated needs_code_scan (auto-emitted)` in `plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md`).
- **Backtest-on-demand** (GroupBRunner over wizard config, honest data precheck — CLOUD_MOCK_MODE always returns PRECHECK_UNAVAILABLE):
  from `e2e-testing/`, strategy-service venv, credential-free:
  `python scripts/strategy/backtest_from_wizard_config.py --steps scripts/strategy/scenarios/apd_price_dispersion_btc.json`
  (or `--config path/to/config.json`; `--days N`; `--out-dir /tmp/results`). Results JSON + markdown written to out-dir.
- **Read the outputs**:
  `unified-api-contracts/openapi/{capability-manifest.json, capability-orphan-report.txt, prospectus/<ARCHETYPE>.md, prospectus/prospectus-codex-audit.md}`.

## Plan of record + trackers

- Plan:
  [`plans/active/capability_wizard_and_manifest_2026_06_11.md`](../../../plans/active/capability_wizard_and_manifest_2026_06_11.md)
  (append-only Progress Log = build history)
- Capability gaps:
  [`plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md`](../../../plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md)
- Bugs/conflicting truths (F1–F19):
  [`plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md`](../../../plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md)
