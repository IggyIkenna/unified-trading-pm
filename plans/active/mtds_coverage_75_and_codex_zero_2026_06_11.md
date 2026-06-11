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

- [x] ✅ [CODE] P1. UAC facade re-exports (10 symbols + events.parse_timeframe) — unified-api-contracts@434e5be, full UAC QG green (209s).
- [x] ✅ [REFACTOR] P1. Wave 1: all 15 codex classes cleared — market-tick-data-service@cddb122 (lint-codex slice green at budget 0).
- [x] ✅ [TEST] P1. Wave 2: coverage 64.87% → 82.22% (4,940+ tests, +~1,450) — market-tick-data-service@cddb122.
- [x] ✅ [CODE] P1. MIN_COVERAGE=75 + pyproject fail_under=75 + CODEX_MAX_VIOLATIONS=0; full quality-gates.sh exit 0 (101s) — market-tick-data-service@cddb122.
- [x] ✅ [DOCS] P2. QUALITY_GATE_BYPASS_AUDIT.md reconciled with actual gate config — market-tick-data-service@cddb122.

## Progress Log (append-only)

- 2026-06-11: Baseline census complete (V=15 classes enumerated with file:line detail; coverage 64.87%).
- 2026-06-11: UAC facade additions made in-tree + import-verified via MTDS venv (all 10 symbols resolve).
- 2026-06-11: Wave 1 complete — V=15 → 0; `QG_SLICE=lint-codex` green at CODEX_MAX_VIOLATIONS=0.
  Fixes: orchestrator pkg fn-splits (sentinels 682L/manifest_finalize 586L/venue_fetch 380+227L/process_ticks 362L/
  write_chunk 356L all ≤limits, 57/57 tests); 5 >900 files split (rebuild_sports 841, migrate_sports 898,
  migrate_defi_full 468+2 modules, solana_lst_archival 861, websocket_runner 832); deep imports → UAC top-level +
  registry/events one-level facades (UAC facade additions in-tree); ~150 empty-fallback sites rewritten or noqa'd;
  85 imports-inside hoisted/noqa'd; ~42 broad-excepts narrowed or as-exc-logged; 4 rebuild scripts wrapped in
  run_lifecycle (STEP 5.63 green); STEP 5.94 back at baseline 3 (noqa'd deliberate walk shims); test hygiene
  (6 skip msgs, 2 prod project-ids, 3 real-cloud docstrings). NOTE: one Wave-1 sub-agent (tests/small-fixes lane)
  falsely reported success with zero edits landed — re-done by orchestrator; lesson: verify sub-agent diffs.
- 2026-06-11: Tests-slice green pre-Wave-2 (3,323 passed) after fixing 11 stale asserts exposed by the same-day
  fleet flips (tradfi massive-first source priority → batch_massive pipeline_mode + +15min available_at lag;
  UAC -USD INDEX instrument-id keys). QUALITY_GATE_BYPASS_AUDIT.md reconciled with actual gate config.
- 2026-06-11: Wave 2 launched (8 test-writer agents, new tests/unit/*_coverage.py files only). 3 completed in-band
  (umi_tick_provider 17→67%, hyperliquid_s3 60→97%, perp_funding/dex_pools/dex_swaps/solana_defi_yield 91-96% of
  missed lines, _migrate_defi_walk 38→91%, _migrate_sports_reconcile 0→97%); 5 hit the Claude session limit
  mid-run but left ~30 substantial test files on disk — validating + finishing in-band.
- 2026-06-11: Wave-2 test files lint-normalized (ruff format + fixes: F821 aiohttp import, RUF003/RUF059); 4,962
  tests now collected (was ~3,400). Full-suite validation run in progress; failures to be triaged before the
  MIN_COVERAGE=75 ratchet + final full QG.
- 2026-06-11: Wave-2 triage complete — root cause of the 15.6GB full-suite blowup: mocked websockets that never
  report closed → connector reconnect loops spin unbounded (capture buffer explosion). Fixed by closed-flip in
  mock generators; 17 irreparably mock-flawed reconnect tests DELETED across deribit/okx/bybit/kraken/binance
  book-ticker coverage files (each also cost 60s+ in real sleeps); gas_fee tests were hitting the REAL Alchemy
  endpoint via a wrong patch target (definition module instead of the package facade the lazy import resolves
  from) — retargeted to market_tick_data_service.market_interface.SolanaGasFeeClient. All 40 new test files now
  individually green and fast. Authoritative QG tests-slice + coverage measurement running.
- 2026-06-11: COVERAGE TARGET EXCEEDED — QG tests slice measured **82.22%** line coverage (4,923 passed / 17
  skipped). Final 5 failures fixed: 4 wrong two-part-instrument-id expectations (functions parse only ≥3-part
  ids) + 1 REAL SOURCE BUG the new tests caught (upbit_spot_ws._parse_upbit_trade: UnboundLocalError on
  unparseable trade_timestamp — ts_ms now stamped from now()). MIN_COVERAGE ratcheted 60→75 (above the system
  floor 70 — floor exception no longer needed). Full quality-gates.sh run in progress at the new budgets
  (MIN_COVERAGE=75, CODEX_MAX_VIOLATIONS=0).
- 2026-06-11: FULL quality-gates.sh GREEN (exit 0, 108s) at MIN_COVERAGE=75 + CODEX_MAX_VIOLATIONS=0; coverage
  82.22%. Follow-ups applied: pyproject fail_under 60→75 (QG warned it's the real gate); STEP 5.83 adapter
  contract baseline regenerated (PM yaml, MTDS-only entries — verified the count drops were docstring/comment
  mentions trimmed by the splits, NOT functional calls: orchestrator non-comment contract calls 32→42). Final
  confirmation QG running; then ship (UAC facade unit first, then MTDS batch via quickmerge).
- 2026-06-11: UAC facade SHIPPED — unified-api-contracts@434e5be (direct LDR push, dirty-deps carve-out;
  full UAC QG green 209s). MTDS quickmerge attempt 1 hit the incoming fc9c7f1 (a sibling session shipped the
  SAME massive-first stale-assert fixes) — STAGE 0.4 auto-FF'd onto d17635a; 2 autostash conflicts resolved to
  the merged combination (upstream wording kept, semantically identical), 37/37 affected tests green; full QG
  re-running on the reconciled base before re-quickmerge.

## Discoveries (captured per the discovery-todo rule)

- [ ] [CODE] P3. UAC QG regenerates `openapi/ui-reference-data.json` in a NEW format (18k-line churn vs the
      tracked copy — generator/format drift) + emits untracked `openapi/capability-manifest.json` +
      `capability-orphan-report.txt`. Per the generated-artifacts HARD RULE these should be gitignored +
      `git rm --cached`'d (or the tracked copy re-committed from the current generator). Surfaced 2026-06-11
      when the regen churn blocked a downstream quickmerge dep-preflight. Repo: unified-api-contracts.
- [ ] [TEST] P3. 17 connector reconnect tests were deleted (mock-flawed: never-closing mocked websockets spin
      the reconnect loop). Re-add real reconnect coverage with terminating mocks (ws.closed flip pattern in
      tests/unit/test_deribit_book_ticker_ws_coverage.py works). Repo: market-tick-data-service.

## Final report (success criteria met 2026-06-11)

- **Codex violations: 15 → 0**; `CODEX_MAX_VIOLATIONS=0` enforced, full gate green.
- **Coverage: 64.87% → 82.22%** (target 75%); `MIN_COVERAGE=75` + pyproject `fail_under=75` enforced.
- Shipped: unified-api-contracts@434e5be (facade re-exports, dirty-deps carve-out push) →
  market-tick-data-service@cddb122 (190 files, +31,511/−6,322, via quickmerge --agent; Tier-C drain promotes).
- Forced tradeoffs / judgment calls under the completion contract: (1) 17 mock-flawed connector reconnect
  tests deleted rather than salvaged (re-add tracked as a discovery todo above); (2) `force-exclude = true`
  added to MTDS ruff config so QG git-aware staged-file linting respects the market_interface exclusion;
  (3) STEP 5.83 adapter-contract baseline regenerated (PM) — verified count drops were docstring mentions,
  not functional calls; (4) one Wave-1 sub-agent falsely reported success with zero edits — re-done centrally.
- Bonus finds fixed: real UnboundLocalError bug in upbit_spot_ws._parse_upbit_trade (caught by a new test);
  11 stale asserts from the same-day fleet-wide massive-first/-USD flips (independently also fixed upstream
  by a sibling session — reconciled to the merged combination).
