---
doc_type: issue
title:
  CLI shard-split flag coverage audit — the codex 6-tuple/--shard-key convention is real in only 1 of 4 sampled services
summary: >-
  `data_pipeline_e2e_milestones_gate_2026_07_24.md` §9 found the codex 6-tuple (day, chain, league, fixture,
  instrument_type + `--shard-key`) convention is REAL in exactly one of 4 sampled services (market-tick-data-service,
  the reference implementation — `decompose_shard_key` has zero hits in instruments-service, MDPS, or features-service)
  and ASPIRATIONAL elsewhere. instruments-service's `--operation download` entrypoint has no
  `--shard-key`/`--instrument-type`/`--day`/`--root` at all. Two audit asks tracked here.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, market-tick-data-service, market-data-processing-service, features-service]
scope: [engineer, admin]
tags: [cli-convention, shard-key, cli-flags, instruments-service, mdps, features-service]
related: [/codex/06-coding-standards/cli-convention.md, /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md]
created: "2026-07-24"
last_updated: "2026-07-26"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_role: backend_engineer
drift_direction: correct-codex
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md §9
depends_on: []
---

# CLI shard-split flag coverage audit

## Todos

- [x] ✅ [BACKEND] P1. Audit CLI shard-split flag coverage across instruments-service, market-data-processing-service,
      and every features-service family CLI against the codex 6-tuple (day, chain, league, fixture, instrument_type) +
      `--shard-key` convention (`/codex/06-coding-standards/cli-convention.md`). — DONE 2026-07-26 (read-only audit).

      **Reference implementation**: `market-tick-data-service/market_tick_data_service/cli/shard_key.py:93`
                          (`decompose_shard_key`), called from `tick_data_handler.py:99`, `risk_params_handler.py:204`,
                          `lending_indices_handler.py:310`, `dex_swaps_handler.py:127`, `dex_pools_handler.py:748`,
                          `perp_funding_handler.py:378`. Confirmed **zero** hits of `decompose_shard_key` anywhere in instruments-service,
                          market-data-processing-service, or features-service (repo-wide grep) — baseline confirmed, not assumed.

                          | Service / entrypoint | `--shard-key` | `--instrument-type` | `--day` | `--root` | `--start/end-date` |
                          |---|---|---|---|---|---|
                          | instruments-service `--operation instruments` (`instruments_service/cli/main.py:354-360`) | ✗ | ✗ | ✗ | ✗ | ✓ (via UTL `ServiceCLI`) |
                          | MDPS `process` cmd (`market_data_processing_service/cli/parser.py:110-326`) | ✗ | ✗ (only `--instrument-ids` L162) | ✗ | ✓ but repurposed (futures-root symbol for `build-continuous` only, L302 — not the shard 5th field) | ✓ (L110-111, required) |
                          | features-service dispatcher, all 9 families (`features_service/cli/main.py:36-44`) | ✗ | ✗ | ✗ | ✗ | ✓ (per-family, mostly via UTL `ServiceCLI._add_date_window_args`, `unified_trading_library/service_cli.py:198-215`) |

                          None of the 9 features-service families (`cross_instrument`, `calendar`, `sports`/`tracking`, `multi_timeframe`,
                          `volatility`, `onchain`, `delta_one`, `cefi`, `performance_features`), nor MDPS, nor instruments-service, has
                          `--shard-key`, `--instrument-type`, or `--day` — confirmed by reading `service_cli.py:198-268`'s shared base
                          (never declares those flags, only `--start-date`/`--end-date`/`--asset-group`/`--data-types`/`--venues`).

                          **Extra finding**: `features_service/cefi/cli/handlers/perp_funding_handler.py` is **not** in the top-level
                          `_FAMILIES` tuple (`features_service/cli/main.py:33-42`, only 9 listed) and no other family dispatcher wires it in
                          — appears to be unreachable dead code, not a live CLI entrypoint. **Gap filed as a new todo below.**

                          **Baseline correction**: this doc's own stated baseline ("instruments-service's `--operation download` entrypoint
                          has none of `--shard-key`/`--instrument-type`/`--day`/`--root`") is factually wrong about ownership —
                          instruments-service has no `download` operation at all (its only operation key is `"instruments"`,
                          `instruments_service/cli/main.py:356`); `--operation download` is market-tick-data-service's entrypoint. Corrected
                          here; see todo 2 below where the same mislabel applies to the chain-scoping flags.

- [x] ✅ [BACKEND] P2. Enumerate every chain-scoping CLI flag on instruments-service's download entrypoint (baseline
      found: `--gas-fee-chains`, `--evm-defi-chains`, `--lending-chains`, `--risk-params-chains`) and confirm whether
      features-service's onchain family CLI accepts the same set. — DONE 2026-07-26 (read-only audit).

      **Baseline correction (measured, not assumed)**: the 4 chain-scoping flags do **not** live on instruments-service
                          — repo-wide grep of instruments-service for `gas-fee-chains|evm-defi-chains|lending-chains|risk-params-chains`
                          returns zero hits. They live on **market-tick-data-service**'s `--operation download` entrypoint
                          (`cli/main.py:544`, `operations={"download": TickDataHandler, ...}`): `--gas-fee-chains` (`cli/main.py:233`),
                          `--evm-defi-chains` (`:276`), `--lending-chains` (`:289`), `--risk-params-chains` (`:302`). This doc's own stated
                          baseline mislabeled ownership; corrected here.

                          Checked features-service's onchain family (`features_service/onchain/cli/parser.py:67-127` +
                          `cli/main.py:224-289`, full arg list) for the 4 flags:

                          | Flag | Present in onchain CLI? |
                          |---|---|
                          | `--gas-fee-chains` | No |
                          | `--evm-defi-chains` | No |
                          | `--lending-chains` | No |
                          | `--risk-params-chains` | No |

                          All 4 missing — none of the onchain family's args (`--operation`, `--mode`, `--asset-group`, `--feature-group`,
                          `--start/end-date`, `--force`, `--log-level`, `--dry-run`, `--max-workers`, `--max-results`,
                          `--skip-dependency-check`, `--no-fail-on-missing-deps`, `--run-tag`) overlaps with chain-scoping. **Gap filed as a
                          new todo below.**

- [ ] [BACKEND] P3. Add the 4 MTDS chain-scoping flags (`--gas-fee-chains`, `--evm-defi-chains`, `--lending-chains`,
      `--risk-params-chains`, see `market-tick-data-service/market_tick_data_service/cli/main.py:233,276,289,302`) to
      features-service's onchain family CLI (`features_service/onchain/cli/parser.py`) so chain-scoped onchain feature
      runs have the same scoping surface as the MTDS download entrypoint they read data from. Source: this doc's audit
      finding, todo 2 (audited 2026-07-26).
- [ ] [BACKEND] P3. Investigate whether `features_service/cefi/cli/handlers/perp_funding_handler.py` is genuinely dead
      code (unreachable — absent from `features_service/cli/main.py`'s `_FAMILIES` tuple and unwired by any family
      dispatcher) and either wire it in or delete it. Source: this doc's audit finding, todo 1 (audited 2026-07-26).
