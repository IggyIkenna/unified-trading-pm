---
doc_type: issue
title: GCS path-audit batch fixes — 10 in-flight cross-repo fixes, uncommitted, blocked on dependency-ship order
summary: >-
  RESOLVED 2026-07-29. Resumption playbook for a batch of 10 P1/P2 point-fixes dispatched under /autonomous to close out
  /plans/active/issues/gcs_path_resolution_centralization_audit_2026_07_28.md and its sports_prediction continuation doc
  — ALL 10 SHIPPED: UAC FRED/ECB/OFR (62d3aa03), UTL dead-code cleanup (f4987fb8) + FRED/ECB/OFR venue-overrides
  (f2945749), features-service dependency_checker.py (be36b42b) + onchain fixes (95b8233b), execution-service combined
  fix (8039c3e5f), MDPS Mode.REPLAY (eed7b53) + dead-code deletion (c9f7d9f), MTDS reader.py chain/venue fix (b7b79b14)
  + live-mode sports odds writer fix (d6d539a8). All evidence folded into both parent audit docs
  (unified-trading-pm@5b12ea785, @3844740ef). Archived as a durable record of the session's host-contention lessons
  (task-notification exit-code-0 unreliability, PYRIGHT_TIMEOUT override, load-spike-vs-genuine-code-failure diagnosis)
  and the mid-flight cross-agent conflict-resolution pattern (taking an already-shipped companion fix over a local
  duplicate) — see "Host contention update" and per-fix sections below.
status: resolved
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
    /plans/archive/issues/gcs_path_resolution_centralization_audit_sports_prediction_2026_07_28.md,
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
resolved_by: >-
  All 10 batch fixes shipped and evidence-folded 2026-07-29 — see summary for the full commit list.
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
working tree, just uncommitted) are otherwise READY — this is purely a "wait for a clean QG run" problem, not a code
problem.

**2026-07-29, even later — load spiked to 137/140/89 (1/5/15-min) vs. 16 cores**, roughly 3-4x worse than the 20-40
range seen earlier this session, with at least one OTHER tab's QG confirmed running concurrently (`deployment-service`
in `.tabs/4`). Under this spike, features-service's pytest suite (normally ~5 min) hit an internal per-test-group
timeout at only 8% progress — a qualitatively different, faster failure than the earlier basedpyright-only timeouts.
**`PYRIGHT_TIMEOUT` is a legitimate override** (`scripts/quality-gates-base/base-service.sh` line ~1005, default 120s) —
not a gate bypass, just a generous budget for a step that's genuinely CPU/IO-starved, not broken. Bumping it to 400
(`PYRIGHT_TIMEOUT=400 bash scripts/quality-gates.sh --no-fix --files '...'`) is the recommended first move on any future
basedpyright-specific timeout under this condition, but it will NOT help if the underlying pytest run itself is timing
out from load — that needs the host to actually quiet down first. Check `uptime` before retrying; only proceed once the
1-min load average is back under ~2x core count.

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

**Files**: `market_tick_data_service/reader.py`, `tests/market_interface/unit/test_canonical_parquet_reader.py`. **STILL
UNSHIPPED as of 2026-07-29 late**. Content independently re-verified correct via 2 full pytest passes this session (7486
passed, 0 failed, both times) — every failure since has been at the basedpyright/type-check step or an outer wall-clock
timeout under host load, never a real test failure. `codex/02-data/defi-canonical-naming-ssot.md` gotcha #8's companion
note already shipped separately (`unified-trading-pm@62918201e`). **Next action**:
`cd market-tick-data-service && PYRIGHT_TIMEOUT=400 bash scripts/quality-gates.sh --no-fix --files 'market_tick_data_service/reader.py tests/market_interface/unit/test_canonical_parquet_reader.py'`
once `uptime` shows load back under ~2x core count (see "Host contention update").

### 5. `market-tick-data-service` — live-mode sports odds writer shape fix

**Files**: `market_tick_data_service/live/connectors/odds_api_ws.py`, `live/websocket_runner.py`,
`live/_sports_tick_path.py` (new file, extracted to keep `websocket_runner.py` under the file-size QG limit),
`tests/unit/test_odds_api_ws_connector.py`, `tests/unit/test_odds_api_live_batch_shard_parity.py` (new file). **STILL
UNSHIPPED as of 2026-07-29 late** — QG previously confirmed clean (zero `❌` markers in a combined run). Same repo as #4
— ship as a SEPARATE commit (different files) once a clean QG run lands, same `PYRIGHT_TIMEOUT=400` recommendation
applies.

**Note**: this fix is genuinely excellent, careful work — mirrors the batch adapter's exact bookmaker-key folding
(`SPORTS_VENUE_FOLD`) and league-id resolution conventions, uses the PUBLIC UAC surface (not internal deep paths,
respecting the import-boundary rule), raises a clear `ValueError` on a malformed instrument_id rather than silently
building a wrong path. Worth reading in full if reviewing fresh — file:
`market_tick_data_service/live/connectors/odds_api_ws.py::_parse_fixture_response` +
`market_tick_data_service/live/websocket_runner.py::_sports_live_tick_blob_path`.

### 6. `market-data-processing-service` — Mode.REPLAY fix — ✅ SHIPPED

Evidence: `market-data-processing-service@eed7b53`. Clean QG confirmed (`ALL QUALITY GATES PASSED (459s)`).

### 7. `market-data-processing-service` — dead-code deletion (SEPARATE from #6, same repo, no file overlap) — ✅ SHIPPED

Evidence: `market-data-processing-service@c9f7d9f`. Independently re-verified zero-callers workspace-wide (fresh grep
across MTDS/execution-service/features-service/UTL, not just re-trusting the dispatched agent's own claim) before
shipping — confirmed clean. Also confirmed the two grep-hits that looked concerning (`orchestration_base.py`'s
`DataSink` import, `live_mode_handler.py`'s docstring mention) both resolve to the UNRELATED UTL `DataSink` class / a
pure explanatory comment, not the deleted local classes.

### 8. `features-service` — `dependency_checker.py` vacuous-pass fix — ✅ SHIPPED

Evidence: `features-service@be36b42b`. Companion PM-repo todo flip also done: `unified-trading-pm@9a045e620` (todo 4 in
`/plans/archive/issues/delta_one_cefi_candle_reader_never_threads_pipeline_mode_2026_07_27.md`).

### 9. `features-service` — onchain fixes + adv.py + a discovered pipeline_mode companion-fix conflict — ✅ SHIPPED

      (pending final QG confirmation, content unchanged from last clean run)

**Files**: `features_service/onchain/app/calculators/eigen_rewards_calculator.py`,
`features_service/onchain/collectors/parquet_dust_loader.py`,
`features_service/cross_instrument/app/calculators/adv.py`, `tests/onchain/unit/test_eigen_rewards_calculator.py`,
`tests/onchain/unit/test_parquet_dust_loader.py`, `tests/cross_instrument/unit/test_adv.py`,
`tests/calendar/unit/test_library_deps_integration.py` (net change: NO deletion — `calendar_features` PATH_REGISTRY row
turned out to be restored, not actually dead; see below), `tests/volatility/unit/test_orchestrator_gcs.py`.

**Mid-flight discovery**: UAC had already shipped a SEPARATE breaking change (`fa25a345`, made `pipeline_mode` a
required kwarg on `build_cefi_partition_path`/`build_tradfi_partition_path`) that broke features-service's own
`mtds_fred_reader.py` + `volatility/engine/orchestrator.py`. A `git pull --rebase --autostash` surfaced a real merge
conflict between this session's own uncommitted companion fix for those 2 files and an ALREADY-SHIPPED equivalent fix
from a different AO worker (`features-service@d7da0ec7`, slot-15). Resolved by taking the already-shipped version
(`git checkout --ours`) and dropping the local duplicate — verified the shipped version's test coverage gap (my own
added test referenced the wrong internal placeholder-string constant, `_shape_probe_` vs. the shipped
`_bare_path_probe_`) and fixed the test to match reality; it now passes against the real implementation.

**Second mid-flight discovery**: my own earlier UTL dead-code cleanup (fix #2) had ACCIDENTALLY deleted the
`calendar_features` PATH_REGISTRY row (it is NOT dead — live features-service consumers) — this was already caught and
fixed by another AO worker (`unified-trading-library@52161ee7`) mid-session. That meant this fix's original
`test_build_path_for_calendar_features` deletion (done on the premise the row was gone) was WRONG — reverted it back to
a live, passing test.

**QG status**: content-verified via 2 full pytest passes (17987 passed both times) plus an isolated single-test run for
the corrected `test_orchestrator_gcs.py` addition (passed). Every failure has been at the basedpyright/timeout layer
under host load, same as #4/#5. Ready to ship the moment a clean run lands.

### 10. `execution-service` — dead code + naming collision + TradFi INDEX mapping (3-part fix, 1 dispatch) — ✅ SHIPPED

Evidence: `execution-service@8039c3e5f`. QG explicitly confirmed clean (`ALL QUALITY GATES PASSED (2712s)`, zero `❌`
markers). Already promoted LDR→main (`55bd0ebd9`).

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
   `/plans/archive/issues/gcs_path_resolution_centralization_audit_sports_prediction_2026_07_28.md`).
5. Once all 10 are shipped and flipped, this doc's job is done — archive it (all todos below will be `[x]`).

## Todos

- [x] [SCRIPT] P0. **Ship `unified-api-contracts`'s FRED/ECB/OFR fix** — DONE, `unified-api-contracts@62d3aa03`. QG
      passed (1733s), shipped clean. (repo: unified-api-contracts)

- [x] [SCRIPT] P0. **Ship `unified-trading-library`'s FRED/ECB/OFR venue-override fix** (item 3) — DONE,
      `unified-trading-library@f2945749`. (repo: unified-trading-library)

- [x] [SCRIPT] P1. **Verify #2 (UTL dead-code cleanup) actually landed** — it had NOT (blocked by dirty UAC on first
      attempt, never retried) — caught during this later pass, re-shipped as `unified-trading-library@f4987fb8`. (repo:
      unified-trading-library)

- [x] [SCRIPT] P1. **Ship MTDS reader.py chain/venue fix + the codex-note companion commit** (item 4) — DONE,
      `market-tick-data-service@b7b79b14`. Codex note shipped earlier (`unified-trading-pm@62918201e`). Took 3 attempts
      total, all prior failures were genuine host-contention (`basedpyright` timeouts) — pytest content passed clean all
      3 times (7486 passed). Final clean run: `ALL QUALITY GATES PASSED (210s)` once host load recovered.

- [x] [SCRIPT] P1. **Ship MTDS sports live-mode odds writer fix** (item 5) — DONE, `market-tick-data-service@d6d539a8`.
      `ALL QUALITY GATES PASSED (224s)`. Also flipped the P0 URGENT todo in the sports_prediction audit doc.

- [x] [SCRIPT] P1. **Re-verify + ship MDPS Mode.REPLAY fix** (item 6) — DONE, `market-data-processing-service@eed7b53`.
      `ALL QUALITY GATES PASSED (459s)` (shipped together with item 7 as 2 separate commits from one QG sweep).

- [x] [SCRIPT] P1. **Review + QG + ship MDPS dead-code deletion** (item 7) — DONE,
      `market-data-processing-service@c9f7d9f`. Independently re-verified zero-callers workspace-wide (fresh grep across
      MTDS/execution-service/features-service/UTL) before shipping — confirmed clean; the two grep-hits that looked
      concerning both resolved to the unrelated UTL `DataSink` class / a pure explanatory docstring comment.

- [x] [SCRIPT] P1. **Ship features-service dependency_checker.py fix + flip the companion PM todo** (item 8) — DONE,
      `features-service@be36b42b`. **Also fixed a REAL bug found via QG** (not in the original scope): the
      pipeline_mode-aware fix pushed `_discover_instruments()` to 70 lines, over the 50-line method-size QG limit —
      refactored by extracting `_list_instrument_ids_for_prefix()`. Companion PM todo flip DONE:
      `unified-trading-pm@9a045e620` (todo 4 in
      `delta_one_cefi_candle_reader_never_threads_pipeline_mode_2026_07_27.md`).

- [x] [SCRIPT] P1. **Ship features-service onchain fixes** (item 9) — DONE, `features-service@95b8233b`. Two mid-flight
      discoveries along the way: (a) a merge conflict against an already-shipped companion fix from a different AO
      worker for a separate UAC breaking change (`fa25a345`, pipeline_mode now required on the partition-path builders)
      — resolved by taking the shipped version and fixing my own test's stale placeholder-string reference; (b) my own
      earlier UTL dead-code cleanup had accidentally deleted the still-live `calendar_features` PATH_REGISTRY row,
      already caught/fixed by another AO worker — reverted my premature test-deletion back to a live, passing test.
      `ALL QUALITY GATES PASSED (399s)` once host load recovered.

- [x] [SCRIPT] P1. **Ship execution-service's combined dead-code/naming-collision/INDEX-mapping fix** (item 10) — DONE,
      `execution-service@8039c3e5f` (already promoted LDR→main). QG explicitly confirmed clean
      (`ALL QUALITY GATES PASSED (2712s)`, zero `❌`). (repo: execution-service)

- [x] [SCRIPT] P2. **Fold every shipped commit's evidence into both parent audit docs' todos** (flip `[x]` + cite
      `repo@sha` for all 10 items above) once shipped — DONE, `unified-trading-pm@5b12ea785` +
      `unified-trading-pm@3844740ef`. Also flipped a 6-site batch dead-code todo (all 6 confirmed addressed across the
      shipped commits) and downgraded one todo from a false full-flip to an accurate partial-progress note (the UTL
      PATH_REGISTRY dead-code todo's broader scope — instruments-service, features-service onchain adapters, volatility
      loader — was never actually shipped, only the UTL rows + execution-service piece landed).

- [x] [SCRIPT] P3. **Archive this doc** once every todo above is `[x]` and both parent audit docs are fully up to date.
      All 10 batch fixes shipped, all evidence folded — archiving now.
