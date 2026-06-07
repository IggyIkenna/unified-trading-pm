---
title: "SIT 94 failures — accumulated regression masked by the dangling staging lock"
created: 2026-06-07
author: ikennaigboaka [slot-1·laptop]
source:
  - "cicd_contract_hardening_2026_06_01.md (staging-lock deadlock root-cause)"
  - "system-integration-tests SIT run 27101141832 (94 failed, 4527 passed)"
locked_by: live-defi-rollout
---

## What I found

While fixing the fleet-wide staging→main deadlock (a dangling breaking-cascade lock — see
`cicd_contract_hardening_2026_06_01.md`), I drained the stuck lock to verify the fix. The drain let the
SIT (`system-integration-tests`) run for the first time in 75+ minutes — and it **failed with 94 test
failures** (4527 passing). The dangling lock had been **masking** this: while the lock was held, no SIT
ran, so the `staging→main` cascade was blocked AND the accumulated SIT regression went undetected.

The 94 failures cluster into ~8 categories (all in `tests/integration/`):

| Category | Representative tests | File | Likely verdict |
| --- | --- | --- | --- |
| Canonical-error-as-exception | `test_is_not_a_python_exception`, `test_unknown_*_code_emits_event_and_reraises`, `test_error_normalisation` | `test_error_normalisation.py`, `test_interface_mock_chains.py` | **Stale test** — UAC deliberately made `CanonicalError(Exception)` (`5afc7f9b`/`3368669b`); 10 adapters `raise` canonical errors → they MUST be exceptions. |
| Retired workflow | `test_critical_workflows_exist` (`assert not ['quality-gates.yml']`) | `test_pm_infrastructure.py` | **Stale test** — `quality-gates.yml` retired in the v2 migration. |
| UAC export surface | `test_uac_completeness*`, `test_uac_all_no_duplicates`, `test_uac_contract_coverage`, `test_uac_orphan_count_under_cap`, `test_uac_source_class_in_all` | `test_uac_completeness.py` | **TBD** — many classes (`AbsenceType`, `ActionProvenance`…) missing from `_UAC_EXPORTED`; real export gap vs stale list to be diagnosed per-class. |
| UI ports/contracts | `test_ui_ports_in_valid_range`, `test_unified_trading_ui_port_is_*`, `test_ui_api_contract_coverage` | `test_ui_api_contract_coverage.py` | **TBD**. |
| Misc | `test_pm_infrastructure`, `test_instrument_alignment`, `test_all_mock_scenarios_have_unique_seeds`, `test_urdi_adapter_venues_*` (URDI is a phantom name per CLAUDE.md) | various | **TBD** — diagnose test-vs-code each. |

## Why it matters

- The `staging→main` promotion cascade for the 6 pending service repos (instruments/features/fund-admin/
  greeks/trading-agent/agent-orchestrator) cannot complete until the SIT is green — the SIT is the
  promotion gate. Staging is currently **open** ("SIT failed — open for fixes"), so pushes aren't blocked,
  but nothing promotes to `main`.
- Some failures may be **real regressions** (UAC export gaps), not just stale tests — fixing them
  test-side without diagnosis would mask real contract drift (violates the "diagnose before fix" rule).
- This is the kind of accumulated debt the dangling-lock fix (now in PM #169) will prevent recurring,
  because the SIT will run on every cascade lock going forward (so regressions surface immediately).

## Recommended decision

Operator directed (2026-06-07): **tackle all 94 now** — diagnose test-vs-code per category, fix stale
tests, fix real code regressions at the wrong side. Track via this issue; archive when SIT is green and
the cascade promotes. Quick wins (canonical-error contract + retired-workflow) first; UAC export gaps
need per-class diagnosis (real gap → fix UAC export; stale list → fix test).

## Status

- [ ] [TEST] P0. Fix canonical-error-as-exception stale tests (`test_error_normalisation.py`, `test_interface_mock_chains.py`) — repo: system-integration-tests
- [ ] [TEST] P0. Fix retired-workflow test `test_critical_workflows_exist` (`test_pm_infrastructure.py`) — repo: system-integration-tests
- [ ] [TEST] P0. Diagnose + fix UAC export-surface failures (`test_uac_completeness.py`) — real gap → UAC export; stale → test
- [ ] [TEST] P0. Diagnose + fix UI ports/contract failures (`test_ui_api_contract_coverage.py`)
- [ ] [TEST] P0. Diagnose + fix remaining (`test_instrument_alignment.py`, mock seeds, URDI)
- [ ] [VERIFY] P0. SIT green locally + on CI; staging→main cascade promotes the 6 pending repos
