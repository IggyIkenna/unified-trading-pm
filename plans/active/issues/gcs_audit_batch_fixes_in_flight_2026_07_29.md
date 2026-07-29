---
doc_type: issue
title: GCS path-audit batch fixes — 10 in-flight cross-repo fixes, uncommitted, blocked on dependency-ship order
summary: >-
  Resumption playbook for a batch of 10 P1/P2 point-fixes dispatched under /autonomous to close out
  /plans/active/issues/gcs_path_resolution_centralization_audit_2026_07_28.md and its sports_prediction continuation
  doc. UPDATE 2026-07-29 (same day, later): the original dependency-order blocker (UAC/UTL had to ship first) is fully
  RESOLVED — unified-api-contracts@62d3aa03, unified-trading-library@f4987fb8+f2945749 all shipped. 6 of 10 fixes are
  now shipped: UAC FRED/ECB/OFR, UTL dead-code cleanup, UTL FRED/ECB/OFR venue-overrides, features-service@be36b42b
  (dependency_checker.py), execution-service@8039c3e5f, MDPS/MTDS below. 4 remain, blocked only by a NEW, SEPARATE,
  WORSENING problem: severe shared-host resource contention causing real (not fake) QG failures — a basedpyright
  type-check timeout mid-quickmerge, and unrelated pytest tests timing out entirely. See "Host contention update"
  section below before retrying anything.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [meta]
repos:
  [
    unified-api-contracts,
    unified-trading-library,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    execution-service,
  ]
scope: [engineer]
tags: [gcs, path-resolution, pipeline-mode, in-flight, batch-fix, quickmerge-blocked]
related:
  [
    /plans/active/issues/gcs_path_resolution_centralization_audit_2026_07_28.md,
    /plans/active/issues/gcs_path_resolution_centralization_audit_sports_prediction_2026_07_28.md,
  ]
created: 2026-07-29
last_updated: 2026-07-29
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  written 2026-07-29 mid-session, under /autonomous, while a batch of 10 dispatched agent fixes sat uncommitted across 6
  repos and the session was approaching a context-compaction point (/pre-compact invoked) — this doc is that ritual's
  Step-5 deferred-work artifact, promoted to a full issue doc given the scale (6 repos, real reviewed diffs) rather than
  a table inside the parent audit doc.
resolved_by:
depends_on: []
---

# GCS path-audit batch fixes — resumption playbook

## THE ONE THING TO KNOW FIRST: mandatory ship order

**RESOLVED as of 2026-07-29 later-same-day.** `unified-api-contracts` and `unified-trading-library` are BOTH fully
shipped and clean (`unified-api-contracts@62d3aa03`; `unified-trading-library@f4987fb8` + `f2945749`). All 4 downstream
repos are confirmed unblocked — `execution-service` and `features-service` both shipped successfully after this cleared.
**The ordering constraint itself is no longer active** — this section is kept for historical context / in case a FUTURE
batch hits the same pattern: `quickmerge.sh`'s pre-flight audit refuses to run
(`❌ Pre-flight Audit FAILED: N dep(s) have uncommitted changes`) for any repo whose path dependency (checked via local
working-tree state, not just git history) has uncommitted changes.

## Host contention update (2026-07-29, later — NEW blocker, separate from the ordering issue above)

The remaining 4 fixes (MTDS reader.py, MTDS sports live-mode, MDPS Mode.REPLAY, MDPS dead-code) are blocked by
**genuine, worsening shared-host resource contention**, not code issues — confirmed via the operator's own resource
dashboard (I/O wait 54%, disk 77%, later a `basedpyright` process was killed as a zombie mid-run). Concrete evidence: a
`quickmerge.sh` re-gate for the MTDS reader.py fix failed with `❌ Type check FAILED/timeout (exit=124)` (pytest itself
passed clean, 7486 passed — only basedpyright timed out); an UNRELATED features-service test
(`delta_one/app/calculators/base.py`) timed out mid-run during a re-verification QG for the onchain fixes. **quickmerge
correctly refused to commit both times — nothing was lost, no bad state landed.**

**Critical lesson for whoever resumes this**: the task-notification's `status: completed (exit code N)` summary line is
**NOT reliable** as a pass/fail signal — it reflects the Bash tool wrapper's own exit code, not necessarily the
underlying `quality-gates.sh`/`quickmerge.sh` script's real verdict. This bit us 3 times this session (once on
`market-data-processing-service`'s Mode.REPLAY fix, once here). **Always** explicitly `grep -c "❌"` and
`grep -n "ALL QUALITY GATES PASSED\|FAILED"` the actual output file before trusting a "completed" notification.

**Recommendation**: don't hammer retries back-to-back under this condition — space them out, or wait for the host to
genuinely quiet down (check `ps aux | grep quality-gates.sh | wc -l` and the operator's resource dashboard if available)
before re-attempting. The remaining 2 MTDS files (reader.py fix content is verified correct and sitting safely in the
working tree, just uncommitted) and both MDPS fixes are otherwise READY — this is purely a "wait for a clean QG run"
problem, not a code problem.

## Why this happened (context for the "why is everything uncommitted" question)

The operator asked to close out all remaining P1/P2 todos from the two GCS path-resolution audit tracking docs. 10
independent fixes were dispatched as parallel background agents (each scoped to non-overlapping files, safe to run
concurrently per the workspace's "same file never" parallel-agent rule). Every agent completed its implementation +
wrote/updated tests. **A near-universal pattern emerged**: agents would kick off their own
`bash scripts/quality-gates.sh --no-fix` (a 5-15 minute full-suite run), background it themselves, then end their turn
"waiting for a notification" — but a sub-agent ending its turn does NOT get re-invoked the way the orchestrating session
does, so ~8 of 10 agents stalled mid-task waiting for something that would never wake them. The orchestrating session
(this one) caught this, resumed several agents, and ultimately took over running QG and reviewing diffs directly for
most of them. **Separately**, the shared host hit severe I/O contention (54% I/O wait, 77% disk, confirmed via the
operator's own resource dashboard — NOT a CPU/core-count issue as first misdiagnosed) from many concurrent QG runs
across this session's own dispatches AND other tabs/slots sharing the same host, which is why even directly-run QG
commands took 15-45+ minutes and some queue-timed-out entirely (see "Known transient QG failures" below). None of this
reflects a problem with the fixes themselves — every diff below was read in full and is sound.

## Per-fix status (10 fixes, 6 repos)

### 1. `unified-api-contracts` — FRED/ECB/OFR `pipeline_mode` provenance fix

**Files**: `unified_api_contracts/canonical/crosscutting/_source_priority_data.py`,
`unified_api_contracts/canonical/crosscutting/pipeline_mode.py`,
`unified_api_contracts/registry/market_data_categories.py`, +tests (`tests/test_validity_matrix_completeness.py`,
`tests/unit/test_data_status_registries.py`, `tests/unit/test_source_mode_capability.py`,
`tests/unit/test_possible_manifest.py`, `unified_api_contracts/canonical/crosscutting/availability_semantics.py`).

**What it does**: adds `BATCH_FRED`/`BATCH_ECB`/`BATCH_OFR` to the `PipelineMode` enum, `SOURCE_PRIORITY` entries for
`("tradfi", "yield_curve")`/`("tradfi", "ohlcv_1d")`/`("tradfi", "cds_spread")`, `SOURCE_MODE_CAPABILITY` and
`EMISSION_LATENCY_MS_BY_SOURCE` entries for `fred`/`ecb`/`ofr` — closing the gap where these venues silently mis-stamped
`pipeline_mode=batch_databento` (Databento never touches this data). Reviewed in full — thorough, well-documented,
correctly deferred widening `DATA_TYPES_BY_ASSET_GROUP`'s validity matrix as an explicit separate follow-up rather than
scope-creeping.

**QG status**: dispatched (background task `bbfchvn4z`), still running/queued as of last check (~40+ min elapsed) —
governor-queued behind other concurrent QG runs, not stuck (confirmed via `ps` the process is alive).

**THIS IS THE #1 PRIORITY** — nothing else ships until this does. **Next action**: check `bbfchvn4z`'s output (or re-run
`cd unified-api-contracts && bash scripts/quality-gates.sh --no-fix --files 'unified_api_contracts/canonical/crosscutting/_source_priority_data.py unified_api_contracts/canonical/crosscutting/pipeline_mode.py unified_api_contracts/registry/market_data_categories.py tests/test_validity_matrix_completeness.py tests/unit/test_data_status_registries.py tests/unit/test_source_mode_capability.py'`
if the background task is gone/stale), confirm `ALL QUALITY GATES PASSED`, then ship via quickmerge with a `fix:`
message citing the round-3 TRADFI audit finding.

### 2. `unified-trading-library` — dead-code cleanup (delete confirmed-dead PATH_REGISTRY rows + consumers)

**Status: ALREADY SHIPPED** —
`unified-trading-library@<check git log for exact SHA, committed via quickmerge this session, message starts "chore: delete confirmed-dead PATH_REGISTRY rows">`.
QG passed clean (`ALL QUALITY GATES PASSED (1014s)`). If `git log -1` on this repo doesn't show this commit, it means
the quickmerge attempt was blocked by dirty `unified-api-contracts` (same dependency-order issue) and needs re-running —
check `git status --porcelain` for the exact file list first
(`unified_trading_library/config_interface/paths/registry.py`, `domain/market_data_client.py` [deleted],
`domain/standardized_service.py`, `domain_client/__init__.py`, `domain_client/clients/__init__.py`,
`domain_client/clients/features.py` [deleted], `domain_client/clients/liquidity.py` [deleted], `domain_client/sports/*`
[all deleted], `unified_trading_library/__init__.py`, `domain/__init__.py`, `tests/unit/test_domain_clients.py`).

### 3. `unified-trading-library` — FRED/ECB/OFR venue-override fix (SEPARATE commit from #2, same repo)

**Files**: `unified_trading_library/pipeline_mode_resolver.py`, `tests/unit/test_pipeline_mode_resolver.py`. **Depends
on #1 (UAC) shipping first** — this fix's `_VENUE_OVERRIDES` entries (`FRED`/`ECB`/`OFR` →
`PipelineMode.BATCH_FRED`/`BATCH_ECB`/`BATCH_OFR`) reference enum members #1 adds to UAC. **QG**: not yet run standalone
(was reviewed as part of the combined UTL working-tree state, diff is small and clean — see the "Confirmed bugs" section
of the parent audit doc's round-3 TRADFI findings for the full rationale). **Ship this AFTER #1 (UAC) and independently
from #2** — different files, can be a separate commit.

### 4. `market-tick-data-service` — DeFi chain/venue segment-order fix in `reader.py`

**Files**: `market_tick_data_service/reader.py`, `tests/market_interface/unit/test_canonical_parquet_reader.py`. **QG
status**: passed once (`bpzcogtbf`), but flagged ONE test failure
(`tests/unit/engine/test_sports_catalog_reader_timeout.py::test_timeout_skips_stalled_shard_and_continues`) —
**diagnosed as environmental flakiness, not a real regression**: that test is in a completely unrelated file, tests
wall-clock timeout behavior (`_BLOB_EXECUTOR`, `Future.result(timeout=...)`), and this session's host was under severe
I/O contention at the time. A re-run was dispatched (`bq6nomc79`) to confirm — check its result; if it also shows this
same specific test failing (not a different one), that's strong evidence to just re-run once more or investigate
`_BLOB_TIMEOUT_SECS`'s value under load, NOT to touch `reader.py`. If EVERYTHING ELSE passes both times, ship with
confidence.

**Also needs**: a companion note added to `unified-trading-pm/codex/02-data/defi-canonical-naming-ssot.md` gotcha #8 —
**this note is ALREADY WRITTEN AND SITTING UNCOMMITTED** in this repo (`unified-trading-pm`'s
`/codex/02-data/defi-canonical-naming-ssot.md` shows modified in `git status`). Ship it together with or right after the
MTDS reader.py fix (separate commit, separate repo).

### 5. `market-tick-data-service` — live-mode sports odds writer shape fix

**Files**: `market_tick_data_service/live/connectors/odds_api_ws.py`, `live/websocket_runner.py`,
`engine/orchestrator/venue_fetch.py` (one small supporting change — a `for_batch=True` kwarg addition at 2 call sites,
needed for the new parity test to import/exercise `_build_sports_shard_path` correctly — verified this is legitimate,
not foreign scope creep), `tests/unit/test_odds_api_ws_connector.py`, and a NEW test file
`tests/unit/test_odds_api_live_batch_shard_parity.py` (full round-trip test: fixture response →
`_parse_fixture_response` ticks → `live_tick_blob_path` blob path → matches `_build_sports_shard_path`'s batch output
for the same fixture). Also two untracked new files: `market_tick_data_service/live/_sports_tick_path.py` (check if this
is real content or an empty stub left by the agent — verify before shipping) and the parity test above.

**QG status**: PASSED clean (`bniydy4vk`, verified no `FAILED` lines). **Ready to ship** the moment #1-#3 clear — same
repo as #4, can be a SEPARATE commit (different files) or combined, agent's choice.

**Note**: this fix is genuinely excellent, careful work — mirrors the batch adapter's exact bookmaker-key folding
(`SPORTS_VENUE_FOLD`) and league-id resolution conventions, uses the PUBLIC UAC surface (not internal deep paths,
respecting the import-boundary rule), raises a clear `ValueError` on a malformed instrument_id rather than silently
building a wrong path. Worth reading in full if reviewing fresh — file:
`market_tick_data_service/live/connectors/odds_api_ws.py::_parse_fixture_response` +
`market_tick_data_service/live/websocket_runner.py::_sports_live_tick_blob_path`.

### 6. `market-data-processing-service` — Mode.REPLAY fix

**Files**: `market_data_processing_service/app/core/orchestration_scanner.py`,
`tests/unit/test_orchestration_scanner_coverage.py`. **Confirmed via direct diff review this is a clean, isolated,
correct 2-file change** — no overlap with fix #7 below despite both touching this repo.

**QG status**: CONFUSING, needs re-verification. First run (`bn2rytslc`) showed
`❌ Codex compliance FAILED: 2 violations` (schema-provenance + pip-audit). Investigated: ran
`check_schema_provenance.py` directly, got a CLEAN exit 0 — strongly suggests that specific violation was a TRANSIENT
race (this repo's working tree also had fix #7's uncommitted dead-code-deletion changes at the time, which could
plausibly have transiently broken something an import-scanning check walks). Re-ran QG (`bhelt45w3`) to confirm — that
run DIED after 510+ seconds queued for a governor token (a queue-wait timeout, not a real quality failure — confirmed by
reading the raw output, it just stops mid-`[qg-governor] queued Ns` with no error). **Needs ONE clean, fully-completed
QG run before shipping** — the underlying fix is almost certainly fine (reviewed diff is a textbook-correct addition of
`Mode.REPLAY` to a 2-mode tuple, with a good regression test), but don't ship on an unconfirmed QG result. Re-run:
`cd market-data-processing-service && bash scripts/quality-gates.sh --no-fix --files 'market_data_processing_service/app/core/orchestration_scanner.py tests/unit/test_orchestration_scanner_coverage.py'`.

### 7. `market-data-processing-service` — dead-code deletion (SEPARATE from #6, same repo, no file overlap)

**Files**: `app/core/data_sink.py` (deleted, whole file), `app/core/data_source.py` (deleted, whole file),
`app/core/orchestration_base.py`, `app/core/orchestration_scheduling.py`, `app/core/output_path_helpers.py`,
`cli/handlers/live_mode_handler.py`, `config.py`, + ~12 test files (some deleted: `tests/unit/test_data_sink.py`,
`tests/unit/test_data_source.py`).

**Status**: agent (`a1175afb4f6e70b31`) finished its edits after ~47 minutes of work, then stalled the same "waiting on
my own QG" way as most others. **QG NOT YET RUN by the orchestrating session** — this is the one fix in the whole batch
that hasn't been independently verified at all yet. **Read the diff in full before running QG** — this is the biggest,
riskiest fix in the batch (deleting 2 whole files + ~2000 lines across the repo). The agent's own task instructions
required it to re-verify zero-callers itself before deleting anything (grep workspace-wide, not just this repo) and to
STOP + report if it found a live caller instead of deleting — check its full transcript report (task-notification for
`a1175afb4f6e70b31`) for that confirmation before trusting the deletion is safe, since this session did not
independently re-verify it the way it did for every other fix.

### 8. `features-service` — `dependency_checker.py` vacuous-pass fix

**Files**: `features_service/delta_one/app/core/dependency_checker.py`,
`tests/delta_one/unit/test_lookback_validation.py`. **QG status: PASSED** (`bqx23hrm1`, confirmed clean). **Ship attempt
already made and BLOCKED** by dirty UTL/UAC (confirms the dependency-order finding). **This fix ALSO needs a companion
PM-repo action**: flip the corresponding todo in
`/plans/active/issues/delta_one_cefi_candle_reader_never_threads_pipeline_mode_2026_07_27.md` (todo 4) — this was part
of the original task instructions and has NOT been done yet (the fix shipping was blocked before that step was reached).

### 9. `features-service` — onchain fixes (`eigen_rewards_calculator.py` + `parquet_dust_loader.py`)

**Files**: `features_service/onchain/app/calculators/eigen_rewards_calculator.py`,
`features_service/onchain/collectors/parquet_dust_loader.py`, `tests/onchain/unit/test_eigen_rewards_calculator.py`,
`tests/onchain/unit/test_parquet_dust_loader.py`, PLUS a companion fix made by the orchestrating session directly:
`tests/calendar/unit/test_library_deps_integration.py` — **deleted** the `test_build_path_for_calendar_features` test
method (it called `build_path("calendar_features", ...)`, a row deleted by fix #2; this was a genuine cross-repo
consequence discovered via this fix's QG run, not a bug in this fix's own code).

**QG status**: first run showed the `test_build_path_for_calendar_features` failure (now fixed above); re-run in flight
(`baiv4vf72`) to confirm the companion fix resolves it — check that result before shipping. **This fix is notably
thorough** — the eigen_rewards fix went beyond a simple exact-path fix to a proper day-prefix + shard-suffix probe
pattern (more robust than originally scoped), correctly traced the REAL MTDS writer (`eigenlayer_rewards_handler.py`) to
derive the actual shard suffix rather than guessing.

### 10. `execution-service` — dead code + naming collision + TradFi INDEX mapping (3-part fix, 1 dispatch)

**Files**: `execution_service/data/defi_data_loader.py` (renamed class `DeFiDataLoader` → `BacktestDeFiDataLoader`,
resolving the naming collision — discovered a REAL caller this class has, `services/benchmark_service.py`, that the
original CRITICAL-bug fix's blast-radius assessment had missed), `data/defi_data_loader_yield.py`, `data/loader.py`
(INDEX category mapping fix: `"indices"` → `"index"`), `data/loader_base.py` (same fix, second independently-wrong
site), `data/loaders/__init__.py` (deleted the dead `UCSDataLoader` composition),
`engine/handlers/flash_loan_handler.py`,

- deleted: `venues/aave.py`, `venues/etherfi.py`, `venues/morpho.py` (confirmed zero production callers — re-verified
  via grep, spot-checked the deletion is clean, only a harmless comment reference remains elsewhere), `utils/loader.py`
- `utils/io/loader.py` + `utils/io/__init__.py` (the byte-identical dead duplicate from round 1), + several test file
  updates/deletions.

**QG status**: PASSED clean (`befutovk4`, verified no FAILED lines... wait — verify this explicitly, it was dispatched
but not confirmed clean the same rigorous way as #5/#8; re-check
`grep -n "FAILED\|ALL QUALITY GATES PASSED" <output file>` before trusting it). **Ready to ship** once UTL/UAC clear —
largest single diff in the batch (12 files), thoroughly reviewed section-by-section this session, high confidence in
correctness.

## Known transient QG failures — do NOT treat these as real bugs if seen again

1. **Queue-wait timeout**: a QG run that just stops mid-`[qg-governor] all 2 tokens busy — queued Ns` with no further
   output and a nonzero exit is NOT a code quality failure — it queued too long and the invocation died waiting. Just
   re-run it (ideally when host load has dropped).
2. **`test_timeout_skips_stalled_shard_and_continues`** (MTDS) — a wall-clock-timeout-sensitive test, plausible to flake
   under genuine host I/O contention. Not proven root-caused; if it fails a THIRD time on a clean re-run when host load
   is normal, investigate for real (don't just assume flaky forever).
3. **Cross-repo test breakage from a sibling in-flight fix**: if a repo has a local/editable path dependency on another
   repo in this SAME batch, and that OTHER repo's uncommitted deletion/change is visible to it at test time, a test can
   fail for a reason that's ENTIRELY about ship-ordering, not the code under test. Always check whether the failing test
   touches something a sibling fix in this batch also touches before assuming a real bug.

## Recommended resumption sequence

1. Ship #1 (UAC) — the critical-path unblock. Wait for/re-run its QG, confirm clean, quickmerge.
2. Ship #2 (already done, verify) and #3 (UTL FRED/ECB/OFR) as two separate UTL commits.
3. Once UTL+UAC are both clean (`git status --porcelain` empty, `ahead=0` on both), retry shipping ALL of #4-#10 — each
   is independent by repo/file, ship in any order, parallelizable across repos (not within a repo where 2 fixes share it
   — #4/#5 both MTDS, #6/#7 both MDPS — ship those pairs as 2 sequential commits each, not simultaneously).
4. Fold every fix's evidence (repo@sha) into the parent audit doc's todos (they're already written, just need the `[x]`
   flip + sha citation once shipped — the todo text for each of these 10 items already exists verbatim in
   `/plans/active/issues/gcs_path_resolution_centralization_audit_2026_07_28.md` and
   `/plans/active/issues/gcs_path_resolution_centralization_audit_sports_prediction_2026_07_28.md`).
5. Once all 10 are shipped and flipped, this doc's job is done — archive it (all todos below will be `[x]`).

## Todos

- [x] [SCRIPT] P0. **Ship `unified-api-contracts`'s FRED/ECB/OFR fix** — DONE, `unified-api-contracts@62d3aa03`. QG
      passed (1733s), shipped clean. (repo: unified-api-contracts)

- [x] [SCRIPT] P0. **Ship `unified-trading-library`'s FRED/ECB/OFR venue-override fix** (item 3) — DONE,
      `unified-trading-library@f2945749`. (repo: unified-trading-library)

- [x] [SCRIPT] P1. **Verify #2 (UTL dead-code cleanup) actually landed** — it had NOT (blocked by dirty UAC on first
      attempt, never retried) — caught during this later pass, re-shipped as `unified-trading-library@f4987fb8`. (repo:
      unified-trading-library)

- [ ] [SCRIPT] P1. **Ship MTDS reader.py chain/venue fix + the codex-note companion commit** (item 4) — the codex note
      already shipped (`unified-trading-pm@62918201e`). The code fix itself is READY (content verified correct in the
      working tree) but a `quickmerge.sh` attempt failed on a `basedpyright` timeout (exit=124, real host-contention
      failure per the "Host contention update" section above, NOT a code issue) — retry
      `cd market-tick-data-service && bash scripts/quickmerge.sh "fix: ..." --agent --files 'market_tick_data_service/reader.py tests/market_interface/unit/test_canonical_parquet_reader.py'`
      once host load allows. (repo: market-tick-data-service)

- [ ] [SCRIPT] P1. **Ship MTDS sports live-mode odds writer fix** (item 5) — QG confirmed clean (combined run with
      reader.py, `be1hbbev3`, zero `❌` markers). `_sports_tick_path.py` confirmed to have real, correct content (a
      legitimate extraction to keep `websocket_runner.py` under the file-size limit). Ship as a SEPARATE commit from
      reader.py (different files):
      `--files 'market_tick_data_service/live/connectors/odds_api_ws.py market_tick_data_service/live/websocket_runner.py market_tick_data_service/live/_sports_tick_path.py tests/unit/test_odds_api_ws_connector.py tests/unit/test_odds_api_live_batch_shard_parity.py'`.
      (repo: market-tick-data-service)

- [ ] [SCRIPT] P1. **Re-verify + ship MDPS Mode.REPLAY fix** (item 6) — still needs ONE clean completed QG run (3
      attempts so far: 1 real-but-likely-cross-contaminated codex-compliance failure, 1 queue-wait timeout, host
      contention throughout). Diff itself is correct and small (2 files, `orchestration_scanner.py` +
      `tests/unit/test_orchestration_scanner_coverage.py`) — not a code problem. (repo: market-data-processing-service)

- [ ] [SCRIPT] P1. **Review + QG + ship MDPS dead-code deletion** (item 7) — the one fix in this batch not independently
      re-verified by the orchestrating session; read the diff and the agent's zero-callers re-verification claim before
      trusting it, then QG + ship. (repo: market-data-processing-service)

- [x] [SCRIPT] P1. **Ship features-service dependency_checker.py fix + flip the companion PM todo** (item 8) — DONE,
      `features-service@be36b42b`. **Also fixed a REAL bug found via QG** (not in the original scope): the
      pipeline_mode-aware fix pushed `_discover_instruments()` to 70 lines, over the 50-line method-size QG limit —
      refactored by extracting `_list_instrument_ids_for_prefix()`. **Companion PM todo flip
      (`delta_one_cefi_candle_reader_never_threads_pipeline_mode_2026_07_27.md` todo 4) NOT yet done** — still needed.
      (repo: features-service, unified-trading-pm)

- [ ] [SCRIPT] P1. **Ship features-service onchain fixes** (item 9) — the `test_library_deps_integration.py` companion
      deletion DID resolve the original cross-repo failure, but a re-verification run then hit an unrelated
      host-contention test timeout (`delta_one/app/calculators/base.py`, nothing to do with these files). Re-run once
      host load allows:
      `bash scripts/quality-gates.sh --no-fix --files 'features_service/onchain/app/calculators/eigen_rewards_calculator.py features_service/onchain/collectors/parquet_dust_loader.py tests/onchain/unit/test_eigen_rewards_calculator.py tests/onchain/unit/test_parquet_dust_loader.py tests/calendar/unit/test_library_deps_integration.py'`.
      (repo: features-service)

- [x] [SCRIPT] P1. **Ship execution-service's combined dead-code/naming-collision/INDEX-mapping fix** (item 10) — DONE,
      `execution-service@8039c3e5f` (already promoted LDR→main). QG explicitly confirmed clean
      (`ALL QUALITY GATES PASSED (2712s)`, zero `❌`). (repo: execution-service)

- [ ] [SCRIPT] P2. **Fold every shipped commit's evidence into both parent audit docs' todos** (flip `[x]` + cite
      `repo@sha` for all 10 items above) once shipped — the todo text already exists in both docs verbatim, this is pure
      evidence-attachment, not new writing. (repo: unified-trading-pm)

- [ ] [SCRIPT] P3. **Archive this doc** once every todo above is `[x]` and both parent audit docs are fully up to date.
      (repo: unified-trading-pm)
