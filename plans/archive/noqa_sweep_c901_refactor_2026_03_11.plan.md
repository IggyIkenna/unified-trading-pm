---
name: noqa Suppression Sweep + C901 Complex Function Refactor
status: DONE
completed: 2026-03-11
owner: agent
---

# noqa Sweep + C901 Refactor — 2026-03-11

Extension of `linter_audit_all_repos_2026_03_10` (which eliminated hard ruff errors). This plan eliminated all `# noqa`
suppressions and refactored all C901 complex functions.

## Phase 1 — noqa Suppression Sweep (DONE)

Started at 752 `# noqa` comments in production source across 15+ repos. Ended at 0 (excluding C901 pending refactor, and
`archive/` which is legacy code).

| Rule                            | Count fixed | Fix applied                                        |
| ------------------------------- | ----------- | -------------------------------------------------- |
| deep-import / qg-deep-import    | ~80         | Converted to relative imports                      |
| E402                            | ~95         | Moved to top + relative imports                    |
| F401                            | ~122        | `__all__` for re-exports, removed unused           |
| E501                            | ~109        | Line breaks with parentheses                       |
| BLE001                          | ~26         | Moved to pyproject.toml per-file-ignores           |
| qg-empty-fallback               | ~17         | Removed try/except ImportError fallbacks           |
| qg-inside-import                | ~42         | Removed stale noqa (TYPE_CHECKING pattern correct) |
| N806/N802/E712/E731/B904/SIM117 | ~16         | Syntax fixes                                       |
| G004/G201/UP047                 | ~5          | Logging + syntax fixes                             |
| cloud-sdk-direct                | 7           | Documented boundary exception in per-file-ignores  |

Repos touched: unified-domain-client, unified-defi-execution-interface, unified-sports-execution-interface,
market-data-processing-service, unified-config-interface, deployment-service, deployment-api, unified-trading-library,
market-tick-data-service, strategy-service, features-sports-service, instruments-service,
unified-trade-execution-interface, features-delta-one-service, ml-training-service, execution-service,
batch-live-reconciliation-service, unified-trading-pm

## Phase 2 — C901 Complex Function Refactoring (DONE)

43 `# noqa: C901` comments in market-data-processing-service + 61 complex functions in deployment-api (noqa already
removed, needed refactoring to pass ruff C901 checks).

New utility modules created:

- `market_data_processing_service/app/utils/path_parsing.py`
- `market_data_processing_service/app/utils/adapter_utils.py`

Key refactoring work:

- S1: Deduplicated `_list_instrument_files()` (scanner + scheduling) via shared path_parsing.py
- S2: `write_candles()` decomposed in data_sink.py + output_writer_service.py
- S3: market_state_detector.py CEFI/TRADFI dispatch pattern extracted
- S4: 14 duplicate `_locf_fill` definitions removed across adapters; shared adapter_utils.py
- S5: Numba kernels split; aggregation rules lookup dict; CLI helpers extracted
- S6: deployment_processor.py — 25 private helpers extracted from 400-line functions
- S7: data_batch_processing.py + service_status_execution.py — 12 helpers extracted
- S8: auto_sync.py — 15 helpers extracted from nested closures

Final state: 0 C901 violations in both repos.
