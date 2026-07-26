---
doc_type: issue
title: MTDS — 77 test files silently ungated (tests/market_interface/**, tests/integration/**)
summary:
  market-tick-data-service never set PYTEST_UNIT_DIR, so its quality gate only ever collected tests/unit/ — the entire
  tests/market_interface/ family (49 unit modules + 28 others) and tests/integration/ have never run in the gate or in
  CI. Measured 2026-07-17 while shipping FIX D3, a whole-tree run is 40 failed / 8414 passed, so the fix is gated on
  fixing those 40 first.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos:
  - market-tick-data-service
scope: [engineer, admin]
tags:
  - quality-gates
  - testing
  - tech-debt
related:
  - plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md
  - plans/active/issues/_cefi_canonical_blueprint_2026_07_17.md
created: 2026-07-17
parent_epic: mtds_mdps_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: backend
drift_direction: none
source:
  FIX D3 MTDS reader half (slot-3, 2026-07-17) — 17 new gated tests left the passed-count unmoved at 6046, exposing that
  base-service.sh only ever collected tests/unit/
resolved_by:
locked_by:
depends_on: []
---

# MTDS — 77 test files silently ungated

## The finding (measured, 2026-07-17, slot-3)

`market-tick-data-service/scripts/quality-gates.sh` never set `PYTEST_UNIT_DIR`, so it inherited the `base-service.sh`
default of `tests/unit/`. MTDS has a **per-family layout** (`tests/market_interface/unit/`, …), so every test outside
`tests/unit/` has **never executed in the quality gate or in `quality-gates-v2` CI**.

**Surfaced by**: FIX D3 (MTDS reader wire↔canonical bridge). The blueprint specified extending
`tests/market_interface/unit/test_canonical_parquet_reader.py`; the gate reported an unchanged `6046 passed` with 17 new
tests added, which is what exposed the gap.

**Scale (measured)**:

| Family                              | test files | gated before                         |
| ----------------------------------- | ---------: | ------------------------------------ |
| `tests/unit/**`                     |        313 | ✅ yes                               |
| `tests/market_interface/**`         |         77 | ❌ no                                |
| — of which `market_interface/unit/` |         49 | ❌ no                                |
| `tests/integration/**`              |         12 | ❌ no (also `RUN_INTEGRATION=false`) |

**MTDS is the fleet outlier**: every other repo with a per-family layout sets `PYTEST_UNIT_DIR` explicitly —
`ml-service` / `strategy-service` / `unified-api-contracts` (`"tests/"`), `execution-service` /
`unified-trading-library` (explicit per-file/per-dir lists). CLAUDE.md § "Environment + how to run quality gates"
already prescribes the rule: _"Per-family layouts (`tests/<family>/unit/`) need `PYTEST_UNIT_DIR="tests/"` before
`source base-service.sh`."_

## Why the one-line fix does NOT ship as-is

Measured with `PYTEST_UNIT_DIR="tests/" bash scripts/quality-gates.sh --no-fix` (2026-07-17, clean host):

```
===== 40 failed, 8414 passed, 54 skipped, 15 warnings in 68.05s =====
Total coverage: 80.40% (gate 79.0%) — coverage is NOT the blocker
```

Enabling the whole tree would take the MTDS gate (and `quality-gates-v2` CI) RED fleet-wide on 40 pre-existing failures.
Per `AUTONOMOUS_AGENT_RULES.md` rule 11(a) — _a gate you make stricter must be one the tree already passes, proven in
the same change_ — the flip is blocked until they are fixed.

**The 40, by owning file** (none are FIX D3 regressions; all pre-date it and were simply never run). **The 2
`test_tardis_canonical_output.py` failures are FIXED + the whole file is now GATED (2026-07-17) — 38 remain**:

|    count | file                                                                        | smell                                                                                                                                                                                                                                                                                                                                                          |
| -------: | --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|        7 | `tests/market_interface/adapters/tradfi/test_databento_canonical_output.py` | canonical-output drift                                                                                                                                                                                                                                                                                                                                         |
|        5 | `tests/market_interface/unit/test_defi_handlers.py`                         | `test_stale_catalog_records_failed_and_returns_early` ×5                                                                                                                                                                                                                                                                                                       |
|        5 | `tests/market_interface/adapters/tradfi/test_databento_write_pipeline.py`   | write-pipeline drift                                                                                                                                                                                                                                                                                                                                           |
|        5 | `tests/integration/test_polymarket_integration.py`                          | integration, needs creds/network                                                                                                                                                                                                                                                                                                                               |
|        3 | `tests/integration/test_kalshi_integration.py`                              | integration, needs creds/network                                                                                                                                                                                                                                                                                                                               |
|        2 | `tests/market_interface/unit/test_defi_adapters_boost_2.py`                 | `ethena_adapter` attempts real DefiLlama sockets (pytest-socket blocks)                                                                                                                                                                                                                                                                                        |
| ~~2~~ ✅ | ~~`tests/market_interface/adapters/cefi/test_tardis_canonical_output.py`~~  | **FIXED + GATED 2026-07-17** — bisected PRE-EXISTING (not d302f07a): a stale Kraken `PF_XBTUSD`→`@INV` expectation (real marker is `@LIN`) + an inert bucket-resolver patch on a 2026-07-10-abandoned call site (rewritten to the real `IS_TEST_RUN` resolver). Also fixed 3 `download_batch` config-singleton isolation bugs that only surfaced under gating. |
|        2 | `tests/integration/test_macro_adapters_integration.py`                      | integration, needs creds/network                                                                                                                                                                                                                                                                                                                               |
|        1 | `tests/market_interface/unit/test_barchart_and_yahoo_adapters.py`           | Barchart is RETIRED (per codex) — likely delete                                                                                                                                                                                                                                                                                                                |
|        1 | `tests/market_interface/adapters/tradfi/test_tradfi_canonical_writes.py`    | canonical-write drift                                                                                                                                                                                                                                                                                                                                          |
|        1 | `tests/market_interface/adapters/cefi/test_tardis_options_adapter.py`       | options adapter drift (`test_tardis_options_real_fetch`) — NOT the canonical_output file above                                                                                                                                                                                                                                                                 |

Note the `tests/integration/**` failures (10) are a separate axis — they are gated by `RUN_INTEGRATION=false` too, so
`PYTEST_UNIT_DIR="tests/"` would pull them into the UNIT phase, which is wrong regardless of whether they pass.

## Interim state (extended 2026-07-17 with the cefi write-side finalise)

`scripts/quality-gates.sh` now carries an **explicit list**, so proven-green files gate immediately without importing
the remaining 38. Extended (`market-tick-data-service@0388e1a9`) to add the three cefi write-side files `d302f07a`
shipped but never executed:

```bash
PYTEST_UNIT_DIR="tests/unit/ tests/market_interface/unit/test_canonical_parquet_reader.py tests/market_interface/adapters/cefi/test_catalog_decompose_all_venues.py tests/market_interface/adapters/cefi/test_cefi_canonical_filename_stem.py tests/market_interface/adapters/cefi/test_tardis_canonical_output.py"
```

**Proof the gate now executes them**: full `bash scripts/quality-gates.sh` GREEN moved from **6046 → 6162 passed** (exit
0, ZERO ❌). The count that never moved despite 17 new D3 tests WAS the bug; it now climbs.

## Todos

- [ ] [BACKEND] P1. **Fix the 8 non-integration `tests/market_interface/unit/` failures** (`test_defi_handlers.py` ×5,
      `test_defi_adapters_boost_2.py` ×2, `test_barchart_and_yahoo_adapters.py` ×1). The `ethena_adapter` DefiLlama
      socket attempts mean a unit test is reaching the network — that is its own correctness bug, not just a gate gap.
      Barchart is RETIRED per `/codex/02-data/tradfi-databento-sourcing-ssot.md`, so its test may simply delete. (repo:
      market-tick-data-service)
- [ ] [BACKEND] P1. **Fix the remaining 14 `tests/market_interface/adapters/**` canonical-output/write failures**
      (databento ×12, tradfi-writes ×1, tardis-options ×1). **The 2 `test_tardis_canonical_output.py` failures are
      DONE** (2026-07-17, `market-tick-data-service@0388e1a9` — bisected PRE-EXISTING, fixed against the prod contract,
      file now gated). The 1 remaining "tardis" failure is
      `test_tardis_options_adapter.py::test_tardis_options_real_fetch`, a separate file. These assert canonical
      write/output shape — given FIX D1/D2 just changed the cefi filename + column contract, verify whether they encode
      the OLD contract before "fixing" them. (repo: market-tick-data-service)
- [ ] [BACKEND] P1. **Widen `PYTEST_UNIT_DIR` to
      `tests/unit/ tests/market_interface/unit/ tests/market_interface/adapters/     tests/market_interface/clients/ tests/market_interface/schema_validation/ tests/cli/`**
      once the two todos above are green — proving it in the same change (rule 11a). Do NOT include
      `tests/integration/**` in the unit phase; route those via `RUN_INTEGRATION` instead. (repo:
      market-tick-data-service)
- [ ] [BACKEND] P2. **Decide the `tests/integration/**` story** — `RUN_INTEGRATION=false` means 12 integration modules
      never run anywhere, including `test_canonical_parquet_reader_integration.py` (updated by FIX D3 for the new cefi
      read contract). Either wire them into a credentialled CI lane or mark the credential-dependent ones explicitly.
      (repo: market-tick-data-service)
- [ ] [QG] P2. **Fleet sweep: assert no repo has an ungated test family** — a PM quality-gate check comparing each
      repo's `tests/*/unit/` dirs against its `PYTEST_UNIT_DIR`. MTDS was the only outlier today, but nothing prevents
      the next one. (repo: unified-trading-pm)

## Progress Log

- **2026-07-17 (slot-3)** — Found while shipping FIX D3's MTDS reader half. 17 new tests in
  `tests/market_interface/unit/test_canonical_parquet_reader.py` produced an **unchanged** `6046 passed` in the gate,
  which is what exposed the collection gap. Measured the whole-tree run (40 failed / 8414 passed / coverage 80.40%),
  confirmed MTDS is the only fleet repo with a per-family layout and no `PYTEST_UNIT_DIR`, and shipped the explicit-list
  interim so the D3 guards actually gate. The 40 failures are NOT D3 regressions — they pre-date it and had simply never
  been executed.
- **2026-07-17 (slot-3, finalise) — `market-tick-data-service@0388e1a9`.** Landed the inherited D3 reader half (dead
  originating agent, liveness-gated inherit) and closed the two cutover blockers:
  - **BLOCKER 1 (bisect)** — ran `test_tardis_canonical_output.py` at `d302f07a` vs `d302f07a^` in isolated git
    worktrees with `PYTHONPATH=<worktree>` override, verifying each ref imported its own code via a ref-only symbol
    (`cefi_wire_bridge`, present only at the new ref). **IDENTICAL 2 failures at BOTH refs → PRE-EXISTING, NOT
    d302f07a**; all of d302f07a's own D2 assertion updates pass. Fixed both against the prod contract: (a) a Kraken
    `PF_XBTUSD` expectation still asserting `@INV` — the exact bug `tardis_margin_marker.py` fixed 2026-07-10
    (`PI_/FI_`=inverse, `PF_/FF_`=linear, verified against the real `cryptofacilities` feed + mirrored from
    instruments-service `_infer_margin_type`); (b) `test_adapter_resolves_canonical_bucket_shape` patched
    `engine.orchestrator.get_market_data_bucket`, a target `_resolve_canonical_cefi_bucket` stopped calling on
    2026-07-10 — the patch was inert (tautology), so once the real resolver ran it returned the `prd` bucket. Rewritten
    to exercise the real `IS_TEST_RUN`-aware write-path resolver (now a genuine regression guard for the 2M-row
    prod-bucket bug).
  - **Isolation bugs (surfaced ONLY by gating)** — 3 `test_download_batch_*` tests set
    `monkeypatch.setenv(TARDIS_STREAMING_FINALIZE, "false")` but `config/service_config.get_config()` is a module-level
    singleton, so the setenv was silently ineffective once an earlier suite test built it → adapter took the streaming
    path → blocked socket → 0 rows → `assert 0==1`. Fixed by resetting the singleton so `get_config()` re-reads the env
    (auto-restored via `monkeypatch.setattr`). This is exactly the "ungated tests only ever ran in isolation" hazard.
  - **BLOCKER 2 (gate)** — extended `PYTEST_UNIT_DIR` (kept the D3 reader entry) to add the 3 cefi write-side files.
    Full gate GREEN, **6046 → 6162 passed** proving they execute.
  - **Stale-base note**: the whole-tree gate also hit a `is_in_known_gap` `ImportError` in `_rebuild_sports_classify.py`
    — a stale-base artifact fixed by pulling origin (commit `31d4a9c0` deleted that dead file), not a MTDS-code issue.
