---
title: "MTDS: coverage → ≥75% + codex violations → 0 (MIN_COVERAGE=75, CODEX_MAX_VIOLATIONS=0)"
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
estimate_class: refactor
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 2.4
created: 2026-06-11
source:
  - operator dispatch 2026-06-11 ("lets take it to 75% coverage and 0 codex violations … follow
    AUTONOMOUS_AGENT_RULES.md, dont talk to me until its at 75%")
related_plans:
  - plans/active/codex_violations_ratchet_to_five_2026_06_10.md
locked_by: live-defi-rollout
locked_since: 2026-06-11
---

# MTDS → 75% coverage + 0 codex violations

## Success criteria

1. `market-tick-data-service` line coverage ≥ 75% as measured by the QG pytest run (`coverage.xml` line-rate ≥ 0.75).
2. Codex compliance V = 0 (all 15 currently-firing classes cleared honestly — no new exclude-glob gaming).
3. `scripts/quality-gates.sh` ratcheted: `MIN_COVERAGE=75`, `CODEX_MAX_VIOLATIONS=0`; full QG green at those budgets.
4. Shipped via quickmerge (UAC facade unit first, then MTDS units); QUALITY_GATE_BYPASS_AUDIT.md reconciled with
   actual config (found drift: gas_fee_handler.py in BE_EXCLUDE_GLOBS undocumented; FUNCTION_SIZE_EXTRA_EXCLUDES ~30
   files vs "None" in §2.1).

## Baseline (2026-06-11, MTDS@eb33603)

- Coverage 64.87% (13,745/21,189 lines; coverage.xml from QG run 04:41Z). Need ≥ 15,892 covered (+2,147).
- V=15 classes: (1) asyncio.run-in-loop websocket_streaming_handler; (2) imports-inside-functions — 85 sites (75
  market_interface + 10 engine/orchestrator); (3) raw response.json ×2 massive_tradfi_rest_connector; (4) empty-str
  fallback ~150 sites (scripts/connectors/orchestrator/_solana_defi_fetch); (5) empty-dict/list ~18 sites;
  (6) hardcoded prod project-id in tests ×2; (7) setup_events-without-sink comment-match _rebuild_prediction_cf11;
  (8) pytest.skip-credential ×5 connector tests; (9) deep unified-lib imports ×3 scripts; (10) broad except ×5
  scripts sites; (11) files >900 ×5 (websocket_runner 912 / solana_lst_archival 988 / rebuild_sports_manifest_v9
  1137 / migrate_defi_full_v9_canonical 1284 / migrate_sports_canonical_v9 1056); (12) fn/method size ×37 (limits:
  method 50 / function 200); (13) unit-tests-real-cloud docstring matches ×3; (14) backward-compat comment ×1
  tardis_batch_download; (15) STEP 5.23 deep UAC imports (scripts + engine/orchestrator + 5 catalog readers).
- Top coverage gaps (misses): umi_tick_provider 482; migrate_defi_full 301; migrate_sports 219; gas_fee 212;
  perp_funding 205; _solana_defi_fetch 200; deribit_book_ticker_ws 200; kraken_futures_book_ticker_ws 191;
  bybit_futures_book_ticker_ws 186; rebuild_sports_manifest_v9 178; book-ticker family ~790 total.

## Approach

- UAC facade (additive-first, Phase-2 pattern of the ratchet plan): re-export candidate_parquet_paths,
  SPORTS_DATA_TYPE_TO_SOURCE, get_league, get_league_fixture_calendar, is_in_known_gap,
  get_league_by_api_football_id, footystats_season_status_for_day, list_instruments, list_not_yet_listed_cefi,
  register_catalog_reader at the top-level facade. DONE in-tree 2026-06-11 (ships as its own unit).
- Wave 1 (codex → 0): 9 parallel sub-agents on disjoint file sets (sports-scripts / defi-cefi-scripts /
  tradfi-pred-scripts / engine-orchestrator / engine-readers / live / cli-handlers / market_interface / tests+small).
  Honest fixes only: hoist or `# noqa: imports-inside-functions` (deliberate lazy imports), narrow or log-and-continue
  broad excepts, fail-fast or justified `# noqa: qg-empty-fallback`, real file/function splits preserving public
  surfaces + test patch targets (pre-audit `rg` for patch sites before moving symbols).
- Wave 2 (coverage → 75%): ~7 parallel test-writer agents on per-file targets (new test files only).
- Final: ratchet quality-gates.sh to MIN_COVERAGE=75 / CODEX_MAX_VIOLATIONS=0, full QG sweep, quickmerge per repo
  (UAC first), flip ratchet-plan checkboxes that this work completes, reconcile QUALITY_GATE_BYPASS_AUDIT.md.

## Todos

- [ ] [CODE] P1. UAC facade re-exports (10 symbols) — unified-api-contracts. (in-tree, ships first)
- [ ] [REFACTOR] P1. Wave 1: clear all 15 codex classes — market-tick-data-service.
- [ ] [TEST] P1. Wave 2: coverage 64.87% → ≥75% — market-tick-data-service.
- [ ] [CODE] P1. Ratchet MIN_COVERAGE=75 + CODEX_MAX_VIOLATIONS=0 + full QG green + ship — market-tick-data-service.
- [ ] [DOCS] P2. Reconcile QUALITY_GATE_BYPASS_AUDIT.md with actual quality-gates.sh excludes — market-tick-data-service.

## Progress Log (append-only)

- 2026-06-11: Baseline census complete (V=15 classes enumerated with file:line detail; coverage 64.87%).
- 2026-06-11: UAC facade additions made in-tree + import-verified via MTDS venv (all 10 symbols resolve).
