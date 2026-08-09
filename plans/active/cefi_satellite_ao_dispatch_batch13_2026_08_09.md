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
    /plans/active/cefi_satellite_ao_dispatch_batch11_2026_08_09.md,
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
    /plans/active/cefi_satellite_ao_dispatch_batch11_2026_08_09.md,
  ]
---

# CeFi satellite AO batch 13 — item-level extraction (strategy_master group)

> **Status: ACTIVE.** Conflict-checked 2026-08-09 — no active `assigned_vm: planning` plan under
> `parent_epic: strategy_master` claims either todo's target (see Progress Log). **Cross-todo file-collision check**:
> todo 1 edits `e2e-testing/scripts/paper_trading/_ledgers.py`; todo 2 edits `market-tick-data-service`'s live event-log
> capture dispatcher/connector registry. No file overlap.

## Todos

- [ ] [CODE] P2. **Replace the taker/IOC fill-sim path in `e2e-testing/scripts/paper_trading/_ledgers.py`** with a
      volume-weighted walk through the recorded live order-book depth (already pulled at $250k/$1M notionals) instead of
      filling the whole order at first-1m-open + flat slip. Repo: e2e-testing. Source:
      `crypto_alpha_research_2026_07_24.md` line 181 (`[CODE] P2.5`, "Taker = VWAP-walk the live depth"). **Done when**:
      the taker fill price for a simulated order is the volume-weighted average price walked through the recorded book
      depth, a unit test verifies it against a hand-computed VWAP for a synthetic order book, and `quality-gates.sh` is
      green.
- [ ] [SCRIPT] P2. **Wire `depth_of_book_10` into the CeFi live event-log capture dispatcher**
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
