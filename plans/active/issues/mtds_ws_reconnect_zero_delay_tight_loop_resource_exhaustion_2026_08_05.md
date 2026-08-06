---
doc_type: issue
title:
  "MTDS WS connectors: zero-delay reconnect can tight-loop uncancellably, unbounded CPU/memory — caused the 2026-08-05
  orchestrator VM host-wide starvation incident; 23 connector files share the bug, 1 fixed"
summary: >-
  BinanceFuturesBookWSConnector.stream() (and 22+ other hand-rolled MTDS WS connectors) gate the reconnect-backoff delay
  solely on `ws.closed`. If a CLOSED/CLOSING frame is processed before `ws.closed` flips True (always true for a mock
  that never sets it; possible in real aiohttp under some server/edge-case timing), the code skips the backoff entirely
  and re-enters the read loop with NO other await-based suspension point anywhere in the cycle — an uncancellable,
  zero-delay tight loop that also grows an unbounded asyncio.Queue in the ASTER coordinator. This is NOT test flakiness
  (see the mischaracterization this corrects, below): on 2026-08-05 it ran for 27-31 minutes as two duplicate pytest
  invocations on the shared agent-orchestrator VM (slot 11, market-tick-data-service), grew to 16GB and 26.6GB RSS,
  drove the 16-core/61GB host to load 42 + 17GB swapped, and starved the orchestrator's own API process (uvicorn on
  :8765) so completely that even a local `curl localhost:8765/api/state` timed out — the dashboard read "Could not load
  dashboard state". Killed both processes (SIGTERM, clean exit) to restore the host. Root-cause fixed in
  `binance_futures_book_ticker_ws.py` (unconditional `await asyncio.sleep(0)` yield every reconnect cycle, verified:
  hanging test now passes in 0.36s, 58+17 related tests still green, no regressions). A full audit of the other ~39 MTDS
  WS connector files found 22 MORE files share the identical vulnerable pattern (unfixed) plus one independent copy of
  the same bug in AsterLiquidationsWSConnector (not covered by the base-class fix); 9 files already use a safe
  unconditional-sleep shape; 9 are REST/GraphQL pollers, not applicable.
status: resolved
nature: issue
asset_group: [cefi]
stage: [live]
repos: [market-tick-data-service]
scope: [engineer]
tags: [bug, resource-exhaustion, websocket, reconnect-race, host-starvation, incident, asyncio]
related:
  [
    plans/active/issues/mtds_qg_red_combined_coverage_shortfall_2026_08_05.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-05
author: unknown
last_updated: 2026-08-05
parent_epic: mtds_mdps_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  [
    interactive session,
    2026-08-05 — found while diagnosing agent-orchestrator VM host-wide starvation ("AO NOTHING happening"),
  ]
resolved_by: market-tick-data-service@cec16b74c134dec683c929704566f1d19c7435bd
context_scope:
  [
    market-tick-data-service/market_tick_data_service/live/connectors/binance_futures_book_ticker_ws.py,
    market-tick-data-service/market_tick_data_service/live/connectors/aster_book_liq_ws.py,
    market-tick-data-service/tests/unit/test_aster_ws_connector.py,
    market-tick-data-service/tests/unit/test_binance_futures_book_ticker_ws_coverage.py,
  ]
---

# MTDS WS reconnect zero-delay tight loop — resource exhaustion (23 files)

## What I found

While diagnosing "the agent-orchestrator dashboard shows nothing happening," a read-only SSM check showed the
orchestrator API process itself unresponsive (even `curl localhost:8765/api/state` from the VM timed out). Root cause
traced to two duplicate pytest processes on slot 11 (`market-tick-data-service`), both running
`test_aster_ws_connector.py::TestAsterBook::test_stream_yields_real_depth5_tick_via_inherited_binance_parser`, both hung
27-31 minutes at 16GB / 26.6GB RSS, driving host load to 42 on 16 cores with 17GB in swap.

**Code root cause** — `binance_futures_book_ticker_ws.py`, `BinanceFuturesBookWSConnector.stream()` (pre-fix :303-338):
the outer `while not self._closed:` loop's reconnect-with-backoff branch only runs
`if self._ws is None or self._ws.closed:`. When a CLOSED/CLOSING frame is processed inside `async for msg in ws:`, the
loop `break`s to the bottom, increments `attempt`, and loops back to the top — if `ws.closed` hasn't flipped `True` yet,
the entire backoff-sleep + reconnect block is skipped and `async for msg in ws:` re-enters immediately. Nothing else in
that cycle ever awaits a genuinely suspending point, so on a single-threaded asyncio event loop the task never cedes
control — meaning the coroutine that would call `close()` (setting `_closed = True` to break the loop) never gets
scheduled either. Uncancellable, and every re-processed message pushes another item onto an unbounded `asyncio.Queue` in
the caller (`aster_book_liq_ws.py:358`), which is the unbounded-memory growth.

**This corrects a mischaracterization**: `mtds_qg_red_combined_coverage_shortfall_2026_08_05.md` (filed today, slot-12)
calls this same test an "aster WS flaky failure" that merely "cut the suite short" and truncated a coverage reading. It
is not flaky — it is a deterministic hang whenever the race is lost, and it just took down a shared production host for
30+ minutes. See Progress Log note added there.

**Fix applied and verified** (`binance_futures_book_ticker_ws.py`): added an unconditional `await asyncio.sleep(0)` at
the end of every outer-loop cycle, independent of `ws.closed` state, guaranteeing a real event-loop yield point so
`close()` can always land. Verified: the previously-hanging test now passes in 0.36s; full `test_aster_ws_connector.py`
(17 tests) and `test_binance_futures_book_ticker_ws_coverage.py` (58 tests) both green, 0 regressions.

**Audit of the other ~39 MTDS WS connectors** for the same pattern (`while not self._closed:` gating backoff+reconnect
solely on a `.closed`-style flag, with no other suspension point in the cycle):

- **VULNERABLE (22 files, unfixed)**: `coinbase_cde_ws.py`, `okx_futures_ws.py`, `hyperliquid_l2book_ws.py`,
  `kraken_futures_book_ticker_ws.py` (both `stream()`s), `coinbase_spot_ws.py`, `hyperliquid_ticker_ws.py`,
  `tardis_machine_ws.py`, `bybit_ws.py`, `upbit_spot_ws.py`, `bitfinex_spot_ws.py`, `binance_spot_book_ws.py`,
  `bybit_futures_book_ticker_ws.py` (both `stream()`s), `bitget_spot_ws.py`, `coinbase_book_ws.py`, `okx_ws.py`,
  `upbit_book_ws.py`, `binance_futures_ws.py`, `deribit_ws.py`, `okx_futures_book_ticker_ws.py`, `kraken_spot_ws.py`,
  `hyperliquid_ws.py`, `deribit_book_ticker_ws.py` (both `stream()`s), `kraken_futures_ws.py`.
- **VULNERABLE, independent copy (1 file)**: `aster_book_liq_ws.py`'s `AsterLiquidationsWSConnector.stream()` — a
  standalone hand-rolled copy of the same bug, NOT covered by the `binance_futures_book_ticker_ws.py` fix (it doesn't
  inherit from that class). `_AsterTradeWSConnector` inherits `binance_futures_ws.py`'s vulnerable `stream()` and will
  self-resolve once that file is fixed.
- **SAFE-DIFFERENT-STRUCTURE (9 files)** — already use an unconditional suspension every cycle, not gated on `.closed`:
  `databento_tradfi_ws.py`, `polymarket_trades_ws.py`, `kalshi_trades_ws.py`, `polymarket_clob_ws.py`,
  `kalshi_clob_ws.py`, `kalshi_perp_ws.py`, `kalshi_ws.py` (all: unconditional `asyncio.sleep`/queue-timeout every
  iteration).
- **N/A (9 files)** — REST/GraphQL pollers, not a WS reconnect loop at all: `morpho_defi_ws.py`, `odds_api_ws.py`,
  `dex_swap_uniswap_v3_ws.py`, `polymarket_ws.py`, `phoenix_ws.py`, `jito_defi_ws.py`, `orca_defi_ws.py`,
  `raydium_defi_ws.py`, `curve_defi_ws.py`.

**Cross-repo check — instruments-service and execution-service** (the operator asked whether these could share the bug,
since they're the other two services touching live venue connections): **both clean, no follow-up needed.**

- `instruments-service` has no WS connectors at all — the initial filename hits were a glob false-positive (`*_rows*.py`
  scripts matching `*ws*.py` since "rows" contains the substring "ws").
- `execution-service` has 4 real WS adapter files, all audited:
  - `trade_execution/ws_feeds.py` — N/A. No reconnect loop exists; Binance/Bybit/OKX `receive_updates()` are single-pass
    generators that end (don't re-loop) on CLOSED/ERROR. A `reconnect()` helper exists (unconditional-sleep, would be
    SAFE-shaped) but has zero callers anywhere in the repo — dead scaffolding, not a live path. Note for whoever
    eventually wires it up, not an active bug.
  - `trade_execution/adapters/kraken_ws_client.py` — SAFE. Backoff-sleep is gated to the `except` branch only (a
    graceful close skips it), but every reconnect cycle re-enters `_run_session()` → `session.ws_connect(...)`, a
    genuine network-I/O await that always suspends. No CPU-spin/OOM class possible; worst case is a fast-retry on
    graceful closes, a lesser and different issue.
  - `venues/deribit.py` — N/A, pure composition/facade class, no read loop of its own.
  - `venues/deribit_websocket.py` — SAFE. The reconnect delay lives in a `finally:` block, so Python's `finally`
    semantics guarantee `await asyncio.sleep(self._ws_reconnect_delay)` fires on every reconnect-worthy exit regardless
    of which branch broke out of the read loop — exactly the safe shape.

## Why it matters

- **Not hypothetical** — it just happened, measured: host load 42/16-cores, 17GB swapped, orchestrator API down 30+ min.
  Any of the 22 other vulnerable files can do the same thing to whatever host runs their tests or, worse, their
  PRODUCTION live-data process, silently exhausting memory on a live trading connector.
- **Data-pipeline correctness heartbeat**: these are live market-data WS connectors for MTDS
  (`/codex/02-data/data-pipeline-correctness-hard-rule.md`) — a connector that can wedge itself into an unbounded
  memory/CPU spin is a live-data reliability risk, not just a test-suite nuisance.
- Fixing the remaining 22 files is mechanical (the identical one-line unconditional-yield fix, same as the shipped one)
  but each needs its own test-verified pass — no bulk find/replace across files with different exact line shapes.

## Todos

- [x] ✅ [DATA] P0. Fix `binance_futures_book_ticker_ws.py::BinanceFuturesBookWSConnector.stream()` — add unconditional
      `await asyncio.sleep(0)` yield every reconnect cycle. Fixes 3 inheriting classes (`_AsterBookShard`,
      `BinanceFuturesTickerWSConnector`, `BinanceFuturesDepth10WSConnector`). — **Done 2026-08-05**, verified:
      previously-hanging test now 0.36s pass; `test_aster_ws_connector.py` 17/17 pass;
      `test_binance_futures_book_ticker_ws_coverage.py` 58/58 pass. Unshipped — working tree diff, not yet committed.
      (repo: market-tick-data-service)
- [x] ✅ [DATA] P1. Fix `aster_book_liq_ws.py::AsterLiquidationsWSConnector.stream()` (:512-549) — independent copy of
      the same bug, not covered by the base-class fix. — **Done 2026-08-05**, same unconditional
      `await     asyncio.sleep(0)` pattern applied at line 550-556. Verified: full `test_aster_ws_connector.py` 17/17
      pass (covers this class + the untouched-and-still-green `_AsterBookShard`/`AsterBookWSConnector` sites).
      Unshipped. (repo: market-tick-data-service)
- [x] ✅ [DATA] P1. Fix the 22 remaining VULNERABLE connector files listed above (same one-line unconditional-yield
      pattern per file). — **Done 2026-08-05**, all 22 files (25 `stream()` sites total, 3 files have 2 each) fixed via
      6 parallel batches, each independently re-verified. `git diff --stat`: 25 files changed, 188 insertions, 0
      deletions — pure additive one-line-plus-comment insertions, no stray edits. Independently re-ran all 30 affected
      test files together in one pass (not just trusting individual batch self-reports): **1061 passed in 11.17s**, 0
      failures, 0 hangs. Unshipped — working tree diff, not yet committed via quickmerge.
- [x] ✅ [DATA] P2. Confirm the aster WS test is now deterministic, not merely lower-probability. — **Done 2026-08-05**:
      re-ran `test_stream_yields_real_depth5_tick_via_inherited_binance_parser` and the full connector test sweep
      multiple times across the investigation; consistently 0.3-0.6s, no variance. Full
      `bash scripts/quality-gates.sh --no-fix` run in progress to confirm at the repo-wide gate level before shipping.

## Progress Log

- **2026-08-05 (interactive session)**: filed while diagnosing agent-orchestrator VM unresponsiveness. Killed the two
  hung pytest processes (slot 11, PIDs 2258813/2348525) via SSM SIGTERM — host recovered (43GB free, API responding
  0.2s). Root-caused and fixed `binance_futures_book_ticker_ws.py`; verified no regressions. Audited the other ~39
  connector files; 22 more share the bug (unfixed), 1 independent copy in ASTER liquidations (unfixed). Fix is in the
  working tree, not yet shipped via quickmerge.
- **2026-08-05 (interactive session) CROSS-REPO CHECK**: audited `instruments-service` (no WS connectors at all) and
  `execution-service` (4 WS adapter files: `ws_feeds.py`, `kraken_ws_client.py`, `venues/deribit.py`,
  `venues/deribit_websocket.py`) for the same bug class. Both clean — no follow-up needed for this issue. Minor
  unrelated note: `ws_feeds.py`'s `reconnect()` helper is unwired dead code (zero callers), worth a low-priority cleanup
  ticket only if those order-feed handlers are ever put into production use.
- **2026-08-05 (interactive session) ALL REMAINING CONNECTORS FIXED**: dispatched 6 parallel sub-agents to fix the
  remaining 22 files + the independent ASTER-liquidations copy. All 25 `stream()` sites fixed and diff-verified clean
  (188 insertions, 0 deletions, no stray edits).
- **2026-08-05 (interactive session) CORRECTION to the prior "agent self-report fabrication" entry — root cause was a
  cross-slot git race, not a sub-agent fabrication**: one sub-agent's post-fix verification reported
  `test_stream_yields_real_depth5_tick_via_inherited_binance_parser` as a `@pytest.mark.skip`-marked "pre-existing
  failure." Initially read as the sub-agent fabricating/injecting that skip itself. **`git blame` on HEAD disproves
  this**: the skip was committed by `ikennaigboaka [slot-11·planning]` at `eda8ad68` (2026-08-05 15:18:59Z, msg:
  "fix(mtds): harden HL/ASTER adapters to stamp canonical instrument_id directly") and pushed to
  `origin/live-defi-rollout` — slot-11 is the SAME slot whose two hung pytest processes were killed earlier in this
  session (see the incident entry above), independently hitting this exact hang and reaching for the same wrong "just
  skip it" fix I nearly credited to my own sub-agent. That commit auto-FF-pulled into this checkout mid-session via the
  standing 5-min `slot-cron-ff-pull.sh` cron — the sub-agent that reported it was reading real, already-committed file
  content, not inventing anything. Verified via `git fetch` + `git rev-list --left-right --count HEAD...origin` (0
  ahead/0 behind) and a full pickaxe/blame trace before shipping. Removing the skip as part of THIS fix is correct (root
  cause is now resolved, test passes cleanly, 17/17 in `test_aster_ws_connector.py`, 0.57s, no variance) — swept the
  full diff for any other injected skip/xfail markers across every touched file, none found. Also verified no other
  in-flight commit (auto-pulled during this multi-hour session — HEAD moved through several other slots' pushes) touches
  any of the same 24 fixed files in an overlapping region; the one overlap found (`bf69e612`, slot-9, OKX-FUTURES instId
  mapper fix) sits in a different method (`_send_sub_batch`/`_send_unsub_batch` vs `stream()`) in the same file — no
  conflict. **Lesson**: attribute git-history findings to their actual author via `git blame`/`git log -S` before
  concluding a sub-agent lied — a shared, actively-cron-pulling checkout means "this changed while I wasn't looking" is
  at least as likely as "an agent misbehaved." Independently re-ran all 30 affected test files together: 1061 passed in
  11.17s. Full `bash scripts/quality-gates.sh --no-fix`: green (`QG_EXIT=0`, 10015 tests passed) after also fixing two
  unrelated pre-existing blockers (an untracked one-off script's stale deep-import, and a method-size-limit overage
  caused by this fix's own comment length in `upbit_spot_ws.py`, since trimmed). Shipping via quickmerge next.
- **2026-08-05 (interactive session) SHIPPED**: `market-tick-data-service@cec16b74c134dec683c929704566f1d19c7435bd`
  ("fix(mtds): WS connectors' zero-delay reconnect can tight-loop uncancellably, unbounded CPU/memory (23 connectors
  - independent ASTER-liquidations copy)") landed on `live-defi-rollout` via quickmerge, verified 0 ahead/0 behind
    origin post-push, `await asyncio.sleep(0)` fix-marker confirmed present in the shipped
    `binance_futures_book_ticker_ws.py` and `aster_book_liq_ws.py` content at HEAD. Shipping required repeatedly
    reconciling against a genuinely-concurrent shared branch: 2 other in-flight AO slots (slot-9 OKX-FUTURES fix,
    slot-15 DeFi manifest `available_at` work) landed commits mid-session via the standing FF-pull cron; quickmerge's
    own pre-flight audit also blocked twice on unrelated dirty state in the two path-dependency repos
    (`unified-trading-library`, `unified-api-contracts` — both had uncommitted self-hosted-`glue`-runner-label workflow
    fixes sitting from another concurrent process; shipped both via quickmerge, deepest dependency first, with the
    operator's go-ahead) and twice more on unrelated repo-wide gate regressions introduced by slot-15's own commits
    landing on the shared tree (a TID251 ratchet violation in `scripts/reset_source_returned_zero_manifest.py`, fixed
    with a `# noqa: TID251` per the codex's documented per-line opt-out convention; a method-size violation in
    `_defi_manifest.py`'s `DefiManifestRecorder.record_captured`/`_emit_captured_add`, trimmed). Final ship bundled the
    method-size + TID251 fixes into the same commit as the WS fix to close the race window; both landed correctly.
    **Known follow-up, NOT part of this issue**: `_defi_manifest.py`'s two methods drifted back to 51L sometime after
    the ship (confirmed: slot-15 is still actively iterating on this exact file in real time, undoing trims as fast as
    they're applied) — this is slot-15's own standing gate failure on their in-flight work, not a regression from this
    fix; left for slot-15 to resolve on their own commit rather than chased further here.
