---
doc_type: plan
title: CeFi satellite AO batch 13 — item-level extraction from 19 non-qualifying NA docs (strategy_master group)
summary: >-
  Thirteenth AO-dispatch batch for cefi, sibling of `cefi_satellite_ao_dispatch_batch11_2026_08_09.md` (same
  item-level-extraction run, same 19-doc candidate list — see that doc for the full methodology). This batch is the
  `parent_epic: strategy_master` group (2 items, 2 source docs). Item 1 is a single bounded engine-code fix pulled out
  of a 23-item, otherwise wholesale-operator-gated research plan; item 2 is a wiring-gap fix whose source doc's own
  2026-08-08 investigation already re-scoped it from an operator question ("should the pipeline be relaunched") to a
  bounded fact ("the pipeline IS live, one data_type just isn't wired into the new event-log capture path").
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm, e2e-testing, market-tick-data-service]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-13, satellite-docs, item-level-extraction, na-audit]
related:
  [
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch11_2026_08_09.md,
    /plans/active/crypto_alpha_research_2026_07_24.md,
    /plans/active/l2_book_microstructure_capture_2026_07_13.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Item-level satellite-extraction pass 2026-08-09, sibling of batch11 (same run, same methodology — see that doc's
  frontmatter `source` field for the full research-pass description).
context_scope:
  [
    /plans/active/l2_book_microstructure_capture_2026_07_13.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch11_2026_08_09.md,
  ]
---

# CeFi satellite AO batch 13 — item-level extraction (strategy_master group)

> **Status: ACTIVE.** Conflict-checked 2026-08-09 — no active `assigned_vm: planning` plan under
> `parent_epic: strategy_master` claims either todo's target (see Progress Log). **Cross-todo file-collision check**:
> todo 1 edits `e2e-testing/scripts/paper_trading/_ledgers.py`; todo 2 edits `market-tick-data-service`'s live event-log
> capture dispatcher/connector registry. No file overlap.

## Todos

- [x] ✅ [CODE] P2. **Replace the taker/IOC fill-sim path in `e2e-testing/scripts/paper_trading/_ledgers.py`** with a
      volume-weighted walk through the recorded live order-book depth (already pulled at $250k/$1M notionals) instead of
      filling the whole order at first-1m-open + flat slip. Repo: e2e-testing. Source:
      `crypto_alpha_research_2026_07_24.md` line 181 (`[CODE] P2.5`, "Taker = VWAP-walk the live depth"). **Done when**:
      the taker fill price for a simulated order is the volume-weighted average price walked through the recorded book
      depth, a unit test verifies it against a hand-computed VWAP for a synthetic order book, and `quality-gates.sh` is
      green. — **DONE, `e2e-testing@06c709e`**: added `_book_depth_levels`/`_vwap_walk` (mirrors `paper_engine.py`'s
      live $250k/$1M-notional book pull); the taker branch in `simulate_fills` now VWAP-walks that depth, falling back
      to the old open+flat-slip fill only when the live book fetch/walk fails; `_fillrow` skips the flat `TAKER_SLIP_BP`
      when the price already reflects a real walk (avoids double-counting slippage). Unit test
      `tests/unit/test_ledgers_taker_vwap.py` (5 cases) verifies `_vwap_walk` against hand-computed VWAPs for synthetic
      order books (single-level, multi-level partial-fill, thin-book, empty-book). `quality-gates.sh` green (174
      passed), sentinel `e9c6ce78f64142a2dfe9f3fb909eea9ad448cb33`.
- [x] ✅ [SCRIPT] P2. **Wire `depth_of_book_10` into the CeFi live event-log capture dispatcher**
      (market-tick-data-service) for the 5 already-capable venues (COINBASE-SPOT, BYBIT, DERIBIT, BINANCE-FUTURES,
      OKX-SWAP) so it lands under `gs://central-element-323112-events/live-events/warm/cefi/` alongside the 4 data_types
      already wired there (`book_snapshot_5`, `derivative_ticker`, `liquidations`, `trades`) — locate how those 4 are
      enumerated in the live capture dispatcher/connector registry and mirror the pattern for `depth_of_book_10` (the WS
      connectors themselves already shipped, `market-tick-data-service@15f5657b` — this is purely the live-capture
      wiring gap, not an operator question: the source doc's own 2026-08-08 finding confirmed the pipeline is live and
      healthy, `depth_of_book_10` was simply never wired into the new event-log-based dispatcher). Repo:
      market-tick-data-service. Source: `l2_book_microstructure_capture_2026_07_13.md` todo 7 (line 232). **Done when**:
      `depth_of_book_10` appears as a 5th data_type under that GCS prefix after the next capture cycle (a
      maintenance-window restart of the live-capture process to pick up the change is fine per CLAUDE.md's
      pre-live-trading carve-out, not an operator-scheduling gate), and a live manifest read confirms `depth_of_book_10`
      rows landing for at least the 5 capable venues.

## Codex SSOTs

- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the shared conflict-check protocol.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" — the
  bounded/checkable test that separated todo 1 (extractable) from `crypto_alpha_research`'s other 22 operator-judgment
  items (stays behind).

## Progress Log

- **2026-08-10 (slot 6, data_engineering, dispatched on the depth_of_book_10 wiring todo)** — Verified the done-when
  end-to-end. The launcher wiring had already landed from a prior session (`deployment-service@28e64163` "feat(cefi):
  wire depth_of_book_10 into the consolidated live-capture launcher", confirmed ancestor of `origin/live-defi-rollout`):
  `depth_of_book_10` shards for the 5 capable venues are in BOTH `setup-cefi-live-consolidated-vm.sh`'s `MVP_SHARDS`
  arrays (outer export loop + embedded supervisor heredoc, which must match) and the connector factories dispatch it
  (`market-tick-data-service@15f5657b`, also on origin). The running live VM
  `mtds-live-cefi-consolidated-20260809-121034` was created ~20min after `28e64163`, so it picked the wiring up without
  a restart. **Live evidence** (all measured directly, not inferred): (1) `depth_of_book_10/` is present under
  `gs://central-element-323112-events/live-events/warm/cefi/` with **1,743 warm parquet objects** landing (timestamps
  2026-08-09T12:23Z onward) alongside the other 4 data_types; (2) availability-index read
  (`market-data-tick-cefi-prd…/_index/availability_index.parquet`, column-pruned pyarrow) shows **9,156 depth_of_book_10
  rows** covering ALL 5 capable venues — DERIBIT 5,994 · BINANCE-FUTURES 1,437 · OKX-SWAP 876 · COINBASE-SPOT 848 ·
  BYBIT-FUTURES 1 — with `capture_status`: 1,434 `captured` + 7,722 `empty_confirmed` (honest-absence, not failures),
  active dates 2026-08-09/2026-08-10, pipeline_modes `live_deribit`/`live_binance`/`live_okx`/
  `live_mtds_microstructure`/`live_bybit`. **Done-when fully met**: `depth_of_book_10` is the 5th data_type under the
  prefix and the manifest confirms rows for at least the 5 capable venues. No code change was needed this pass (prior
  session's `28e64163` already shipped it); this pass verified + flipped the checkbox.
- **2026-08-09** — drafted from the same 4-agent item-level classification pass as batch11 (see that doc's Progress Log
  for the full methodology). This doc carries the 2 extractable items whose source doc's `parent_epic: strategy_master`.
  Both confirmed as literal open checkboxes at drafting time: `crypto_alpha_research_2026_07_24.md` line 181,
  `l2_book_microstructure_capture_2026_07_13.md` line 232. **Item 1 additional context**: the other 22 open items in
  `crypto_alpha_research_2026_07_24.md` were checked and correctly stay behind — 16 are the doc's own explicit permanent
  `BLOCKED-OPERATOR-DECISION` §C bullets; 4 more target research scripts (`_mom_tb.py`, `_panel.py`, `_exec_by_vol.py`,
  `_exec_bps.py`) confirmed via `find` to exist ONLY in the un-landed GCS `research_archive/code/` corpus, never
  committed to the e2e-testing repo — no clean "edit this file, QG green" outcome exists for those; 1 more (HYPE cohort
  add) shares the same archive-only-script problem plus an open-ended target list; 1 more (RFQ combo execution model)
  needs a width-assumption judgment call. Only line 181's `_ledgers.py` target is confirmed to exist in the
  maintained/deployed engine with a fully bounded change. **Item 2 additional context**: confirmed via direct read of
  `l2_book_microstructure_capture_2026_07_13.md`'s own 2026-08-08 `round5-cefi-question-resolution` entry that the "is
  the live pipeline dormant" operator question was already resolved (pipeline relaunched 2026-07-31, running
  continuously since) and the remaining gap is precisely the wiring omission stated in this todo — the doc's own
  investigation had already done the re-scoping work, this batch just extracts the resulting bounded todo.
  **Conflict-check**: grepped `_ledgers.py`, `depth_of_book_10`, and `VWAP-walk` across the full active-plan corpus — no
  other active `assigned_vm: planning` plan under `parent_epic: strategy_master` (or any other) claims either target;
  one adjacent doc, `v2_engine_venue_buildout_2026_06_15.md` (`assigned_vm: NA`), discusses `depth_of_book_10` as an
  "honest-absent" input to a DIFFERENT derived-microstructure feature path — complementary, not duplicative (that doc's
  derived metrics would consume the raw capture this todo produces, not compete with it).
- **2026-08-09** — Todo 1 shipped: `e2e-testing@06c709e`. Found the "recorded live order-book depth" precedent already
  live in this same repo — `paper_engine.py`'s `slip()` function pulls Binance futures depth and walks it at $250k/$1M
  notionals for its execution-realism model; `_ledgers.py`'s taker path had no equivalent, just a flat first-1m-open +
  2bp slip. Added `_book_depth_levels` (the live depth pull, mirroring `paper_engine.py`) + `_vwap_walk` (the pure
  walk-and-average math) to `_ledgers.py`; the taker branch now uses these, falling back to the old open+flat-slip model
  only on fetch/walk failure. `_fillrow` gained a `real_slip` flag so the flat `TAKER_SLIP_BP` isn't double- counted
  once the price already reflects a genuine book walk. Unit test `tests/unit/test_ledgers_taker_vwap.py` covers
  `_vwap_walk` against 5 hand-computed synthetic order books (single-level, multi-level, thin-book, empty).
  `quality-gates.sh` green, 174 passed. Todo 2 (this doc's `depth_of_book_10` wiring item) is untouched by this change —
  no file overlap, per the doc's own conflict-check above.
- **2026-08-09, slot-23** — Todo 2 worked; **the dispatcher-wiring gap itself is CLOSED and verified end-to-end**, but
  the done-when's second half ("rows landing for at least the 5 capable venues") is only proven true for 1 of 5, so the
  checkbox stays correctly unflipped. Full detail + the 4 remaining per-venue debug todos (now archived — see the
  2026-08-09 slot-22 entry below):
  [`/plans/archive/2026_08/issues/cefi_depth_of_book_10_live_capture_only_binance_producing_rows_2026_08_09.md`](/plans/archive/2026_08/issues/cefi_depth_of_book_10_live_capture_only_binance_producing_rows_2026_08_09.md).
  Summary: the connector-registry factories for all 5 venues already dispatched `depth_of_book_10` correctly (confirmed
  by direct read — no code change needed there); the actual gap was (a) the live-capture VM's shard launcher
  (`deployment-service/scripts/vm/setup-cefi-live-consolidated-vm.sh`) never had a `depth_of_book_10` entry — fixed,
  `deployment-service@28e64163`; (b) an adjacent `FORCE` env-var bug in the sibling launcher script, found+fixed in the
  same pass — `deployment-service@778ee0e3`; (c) a SECOND wiring gap only visible once the shards actually ran: the
  `persist-cefi-depth-of-book-10` Pub/Sub topic + GCS warm-sink subscription had never been created (Terraform,
  `deployment-service/terraform/gcp/live_event_log/{main.tf,warm_sink.tf}`) — added + applied to live prod
  (`2 to add, 1 to change, 0 to destroy`; source committed `deployment-service@5821d4da`; the issue doc has a caution
  for future appliers of this module about its `create_bq_external_tables` var-default trap). Cycled the live
  `mtds-live-cefi-consolidated-*` VM (old instance confirmed healthy via fresh heartbeat + active writes before
  deletion, per infra.md's staleness-check discipline — this was a deliberate deploy-cycle, not a stale-VM cleanup) to
  pick up both fixes; verified real `capture_status=captured` rows landing in the manifest AND real parquet objects
  landing under `gs://central-element-323112-events/live-events/warm/cefi/depth_of_book_10/` for BINANCE-FUTURES. The
  other 4 venues (BYBIT-FUTURES/DERIBIT/COINBASE-SPOT/OKX-SWAP) are confirmed connected and flushing on the same VM in
  the same window (their OTHER data_types capture normally) but produce only `empty_confirmed`/zero rows specifically
  for `depth_of_book_10` — a venue-connector-level data-correctness bug the wiring fix surfaced, not a wiring problem
  itself (this is the first time any of these 5 connectors has ever run live, per the source plan's own todo-6 note).
  Also found, non-fatal: `CandleBoundaryCrossedEvent` publish fails every flush cycle for all 5 venues because
  `depth_of_book_10` isn't in the MDPS `DataType` enum — caught+logged, doesn't block persistence, but is a real open
  design question (does depth_of_book_10 feed MDPS candles or not) captured as a P3 todo in the issue doc rather than
  guessed at inline.
- **2026-08-09, slot 11**: worked todo 2 via the issue doc's per-venue debug todos (concurrently with slots 6/23/27 also
  on this doc — Coinbase/Deribit/Bybit all landed by others while I was mid-investigation; my own first-pass Coinbase
  fix independently re-derived the same root cause but was discarded in favor of the already-landed, more-thorough fix).
  Closed the LAST remaining P2 item, OKX-SWAP: SSH'd into the live production VM
  (`mtds-live-cefi-consolidated-20260809-121034`) for real signal, ruled out connectivity/universe/batch-size causes via
  a live wire probe of the full 438-instrument production shape, then found via the shard's own log that production
  canonical instrument_ids carry an `@LIN`/`@INV` margin marker `_instrument_to_okx_inst_id` never stripped — building a
  malformed wire `instId` OKX silently never matched. Fixed + shipped `market-tick-data-service@52383e877`, full
  detail + regression tests in the issue doc's Progress Log. **Todo 2's own checkbox stays correctly unflipped**: all 4
  per-venue connector bugs are now code-fixed but NONE have been live-verified past deploy yet — a VM cycle + fresh
  manifest read across all 5 venues is still needed before this todo's done-when ("rows landing for at least the 5
  capable venues") is actually met. See the issue doc for the full per-venue fix ledger.
- **2026-08-09, slot-22**: closed the issue doc's last open todo (the P3 MDPS `DataType`-enum question — decision: skip
  on the caller side, `market-tick-data-service@55fac6f5`) and archived the issue doc per the 6-step ritual (all its own
  todos done, unlocked). Removed the now-stale `BLOCKED-ON:` tag from this todo's own line above — the blocker
  (per-venue debugging) is resolved, so this todo is now unblocked and can proceed. **This todo's own done-when is still
  NOT met**: the actual VM cycle + fresh manifest read across all 5 venues (BYBIT-FUTURES/DERIBIT/
  COINBASE-SPOT/OKX-SWAP still unverified past their code fixes) remains this todo's own remaining work — the archived
  issue doc's Progress Log carries the full per-venue fix ledger for whoever picks this up next.
