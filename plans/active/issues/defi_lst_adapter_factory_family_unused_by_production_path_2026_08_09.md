---
doc_type: issue
title:
  "MTDS DeFi adapter-factory audit (widen-scope item): CoinbaseCbEthAdapter was genuinely built-but-unwired (now fixed)
  -- but the audit also surfaced 6 sibling LST adapter classes that ARE registered in VENUE_REGISTRY yet are never
  actually invoked anywhere in production, because real LST-rate capture runs through a separate direct on-chain path"
summary:
  "Widening the systemic unregistered-handler audit to market-tick-data-service's adapter-factory layer
  (market_interface/factory.py VENUE_REGISTRY/get_adapter()) found one clean built-but-unwired case --
  CoinbaseCbEthAdapter (lst_coinbase_adapter.py): fully built, unit-tested (26 tests), documented, but never imported
  into factory.py or registered in VENUE_REGISTRY -- fixed this session (registered under 'coinbase_cbeth' + a
  regression test, mirroring the Deribit options_chain precedent). But confirming the fix surfaced something the
  original 2-case binary (built-but-unwired vs genuinely-not-built) doesn't capture: RenzoAdapter, PufferAdapter,
  RocketPoolAdapter, SolblazeAdapter, LidoAdapter, and EtherFiAdapter are ALL already registered in VENUE_REGISTRY (have
  been since the original 2026-06 DeFi adapter fan-out commit) but are never instantiated anywhere in the codebase
  except their own test files -- grep for get_adapter() calls or direct instantiation with these venue keys returns zero
  hits outside adapters/defi/*.py and tests/. Real LST exchange-rate capture for stETH / wstETH / rETH / cbETH / mETH /
  swETH runs entirely through a separate, simpler mechanism: lst_rates_handler.py::_collect_evm_lst_rows() +
  _EVM_LST_ABI_METADATA (direct on-chain ABI calls, e.g. exchangeRate() for cbETH), which does not call get_adapter() or
  import any of these classes at all. Registering CoinbaseCbEthAdapter closes the literal 'unregistered' gap and is safe
  (VENUE_REGISTRY membership is inert -- nothing auto-iterates it to trigger new captures), but the deeper question --
  whether this whole adapter-class family is dead code that should be deleted, or unused infrastructure that should be
  wired into a real backfill/live operation because its 3-tier fallback (native API / AAVE oracle / DefiLlama) captures
  something the simpler ABI path doesn't -- is a design call, not a mechanical fix, and is out of this todo's scope."
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [honest-coverage, defi, lst, adapter-factory, unregistered-handler-audit, dead-code, data-correctness]
related:
  [
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md,
    /plans/active/issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md,
  ]
created: 2026-08-09
author: ikennaigboaka [slot-30]
parent_epic: instruments_master
priority: P2
source:
  "Widen-scope adapter-factory-layer unregistered-handler audit,
  cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md item 'Widen the systemic unregistered-handler audit to the
  adapter-factory layer' -- diff of every DeFi protocol/adapter class registered in market_interface/factory.py against
  cli/main.py + deployment-service/scripts/vm/ invocation sites."
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
estimate_class: design
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.6
last_updated: 2026-08-09
supersedes:
superseded_by:
depends_on: []
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
context_scope: [market-tick-data-service/market_tick_data_service/market_interface/factory.py, market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py, market-tick-data-service/market_tick_data_service/cli/handlers/_oracle_prices_constants.py]
---

## What was actually checked, and how

The widen-scope todo asked to diff every DeFi protocol/adapter handler class registered in `market_interface/factory.py`
against `cli/main.py` + `deployment-service/scripts/vm/` invocation sites, mirroring the already-fixed Deribit
`options_chain` (operations-dispatcher layer) and the original 2026-07-06 handler-registration audit
(`market-tick-data-service@015abaf5`/`@efd658c8`, which covered the `cli/handlers/` → `operations={…}` dispatcher layer
only). This is the same audit methodology, one layer down: `market_interface/factory.py`'s `VENUE_REGISTRY` +
`get_adapter()` dispatch.

1. **Enumerated every class exported from `adapters/defi/__init__.py`** (28 names) and diffed against `VENUE_REGISTRY`'s
   26 pre-existing DeFi entries in `factory.py`. Exactly one class was exported but never imported into `factory.py` at
   all: `CoinbaseCbEthAdapter` (`lst_coinbase_adapter.py`, 557 lines, a fully-built 3-tier fallback adapter — Coinbase
   Advanced Trade API → AAVE Oracle → DefiLlama — with 26 passing unit tests in `test_lst_coinbase_adapter.py`). This is
   a clean, unambiguous built-but-unwired case.
2. **Grepped for actual invocation** of the 6 nearest sibling classes (Renzo/Puffer/RocketPool/Solblaze/Lido/EtherFi —
   same `BaseDefiAdapter` LST-family shape, same era, same registration pattern) across both `market-tick-data-service`
   and `instruments-service`, for both `get_adapter("<venue>", ...)` calls and direct `ClassName(...)` instantiation.
   Zero hits outside `adapters/defi/*.py` (self-referential) and `tests/`.
3. **Traced how cbETH (and the other LST tokens) are actually captured in production** today:
   `lst_rates_handler.py::_collect_evm_lst_rows()` iterates `_EVM_LST_ABI_METADATA` (a flat dict of ABI
   method/selector/decimals per token) and calls the token's on-chain contract directly via `web3` — e.g. cbETH's
   `exchangeRate()` — with zero dependency on `CoinbaseCbEthAdapter`, `RenzoAdapter`, etc. Additionally, `oracle_prices`
   for the same LST tokens (including cbETH, via both a Chainlink `cbETH/ETH` feed AND a direct AAVE-oracle
   `getAssetPrice` call, `_oracle_prices_constants.py`) are captured by a THIRD, also-independent path
   (`oracle_prices_handler.py` / `_aave_oracle_collection.py`).

## Why this doesn't fit the todo's original built-but-unwired / genuinely-not-built binary

- `CoinbaseCbEthAdapter` is a clean **built-but-unwired** case — fixed this session (see Todos below).
- The 6 siblings are neither: they're **built, registered, and callable via `get_adapter()`**, so they're not "unwired"
  in the literal sense the audit was built to catch. But they are also not "genuinely not built" (they're fully
  implemented, real logic, real tests). They're a third category this audit didn't anticipate: **built, registered, but
  never actually invoked because a separate, simpler mechanism already captures the same data.** Whether that's a
  problem depends on a design question the audit itself can't answer:
  - If the ABI-direct path (`_collect_evm_lst_rows`) and the oracle-prices path (`_aave_oracle_collection.py`) together
    already give equivalent or better coverage than these adapter classes would (they arguably do — Chainlink +
    AAVE-oracle + on-chain `exchangeRate()` is at least as good as the adapters' own AAVE-oracle/DefiLlama fallback
    chain, and doesn't depend on Coinbase credentials the adapter is `BLOCKED-CREDENTIALS` on), then the adapter classes
    are dead code that should be deleted per CLAUDE.md's "delete deprecated code (no shims)" rule.
  - If the adapters were meant to serve a DIFFERENT purpose not covered by the two live paths (e.g.
    `get_instrument_metadata()` / `fetch_lst_instruments()` for instruments-service's reference-data catalogue, which
    the ABI/oracle paths don't populate at all — checked: instruments-service imports none of these classes either, so
    this purpose is also currently unfulfilled), then the right fix is wiring a real consumer, not deleting.
- This is exactly the kind of judgment call `task_template.md`'s dispatch-scope-eligibility rule reserves for a human
  decision, not a worker todo — "finish what's already built" vs "delete now-redundant infrastructure" is not something
  a worker can determine from the code alone without an explicit design ruling.

## Todos

- [x] ✅ [SCRIPT] P1. Register `CoinbaseCbEthAdapter` in `market_interface/factory.py`'s `VENUE_REGISTRY` under
      `"coinbase_cbeth"` (the bare `"coinbase"` key is already taken by the CEFI spot `CoinbaseAdapter`) + add it to the
      `.adapters.defi` import block. Repo: market-tick-data-service. Done when:
      `get_adapter("coinbase_cbeth", chain="ethereum")` resolves to a `CoinbaseCbEthAdapter` instance; a regression test
      pins it. — market-tick-data-service (this session, slot-30, un-shipped at file time — see plan Progress Log for
      the SHA). `test_defi_coinbase_cbeth` (`TestGetAdapter`) + `test_registry_has_coinbase_cbeth` (`TestVenueRegistry`)
      added to `tests/market_interface/unit/test_factory_and_venue_registry.py`; full local suite green except 2
      confirmed pre-existing unrelated failures (`test_bucket_resolution_uses_category_tradfi`,
      `TestKalshiMarket::test_market_validates_against_ac_schema` — reproduced identically on a clean stash of this
      diff).
- [ ] [SCRIPT] P2. Delete RenzoAdapter/PufferAdapter/RocketPoolAdapter/SolblazeAdapter/LidoAdapter/EtherFiAdapter (+
      CoinbaseCbEthAdapter) — 7 now-redundant LST adapter classes + their tests — from market-tick-data-service. The
      ABI-direct (`_collect_evm_lst_rows`) + oracle-prices (`_aave_oracle_collection.py`) paths already give
      complete, honest LST coverage. Per D61 ruling (2026-08-22): approved — delete now; reconsider only on a named
      product need. Repo: market-tick-data-service.

## Progress Log

- **2026-08-09 (slot-30)**: filed while executing the widen-scope adapter-factory-layer unregistered-handler audit todo
  in `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`. `CoinbaseCbEthAdapter` fixed inline (mechanical,
  in-scope); the broader 6-adapter dead-code-or-wire question extracted here as a design call, per this todo's own
  "genuinely-not-built ones are filed as new issue docs (not built here)" instruction — this is the closest-fitting
  disposition for a finding that's neither cleanly "unwired" nor cleanly "not built."
- **round9-reclassify-satellite-sweep 2026-08-09** (defi tranche): KEEP-NA, valid — the sole open item is explicitly an
  `[OPERATOR]` (a) delete vs (b) wire-a-real-consumer decision, and the doc's own "Why this doesn't fit the todo's
  original... binary" section states plainly this is a design call `task_template.md`'s dispatch-scope-eligibility rule
  reserves for a human, not something a worker can determine from the code alone. No RECLASSIFY or satellite-extraction
  applies — there is only the one item, and it is not bounded. Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-16** [body-hash:fe02c3b6ddf2195d]: KEEP-NA, valid — The one prior todo (registering CoinbaseCbEthAdapter) is already closed with concrete evidence (regression tests added, full local suite green modulo two confirmed pre-existing unrelated failures).
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **2026-08-22 — ruling D61 (Unused LST adapter family)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Delete — ABI-direct already gives equivalent-or-better coverage; reconsider only
  on a named product need. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
