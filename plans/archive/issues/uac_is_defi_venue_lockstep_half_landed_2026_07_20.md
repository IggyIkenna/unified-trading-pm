---
doc_type: issue
title:
  "UAC/IS DeFi venue lockstep half-landed (uac@3f79489f) — 9 venues declared, chainlink adapter never written; 5 tests
  RED, instruments-service tree blocked fleet-wide"
summary: >-
  unified-api-contracts@3f79489f (slot-4, 2026-07-20) declared 9 new DeFi venues — METEORA-SOLANA / LIFINITY-SOLANA /
  PHOENIX-SOLANA (Solana DEX), PYTH-SOLANA and CHAINLINK-{ETHEREUM,ARBITRUM,BASE,OPTIMISM,POLYGON} (oracles) — with the
  commit message claiming "in drift-guard lockstep". The instruments-service half never landed, so the IS tree has been
  RED for 2+ hours and NOTHING can ship from it (quickmerge Pass-1 needs a green QG sentinel). Two DIFFERENT gaps hide
  behind the 9: (1) meteora/lifinity/phoenix/pyth are pure BOOKKEEPING — the adapter classes exist and are
  ctor-compatible, they were simply never added to factory._ADAPTERS / ADAPTER_DATA_SOURCES; (2) chainlink is a REAL
  MISSING ARTIFACT — instruments_service/reference_data/adapters/defi/chainlink.py does not exist anywhere in the repo,
  yet UAC's own comments assert it does. Registering the 4 alone fixes NOTHING (tests 1+3 still fail on the absent
  chainlink key), so unblocking REQUIRES a chainlink decision. Owned by slot-4 (the feature author) — deliberately NOT
  fixed from slot-3 to avoid a cross-slot collision on their in-flight files.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, instruments-service]
scope: [engineer]
tags: [cross-repo-drift, cross-slot, uac, adapter-registry, defi, blocking, tree-red, lockstep]
related: [defi_consolidated_closeout_2026_07_18, defi_catalogue_available_to_false_delisting_2026_07_20]
created: 2026-07-20
priority: P0
parent_epic: instruments_master
source: "slot-3 diagnosis 2026-07-20 while blocked shipping the DeFi available_to close-out"
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
resolved_by:
  "unified-api-contracts@ae83689b (flip CHAINLINK-* back to phase=live + real adapter key) +
  instruments-service@6506b505 (ChainlinkOracleReferenceDataAdapter + factory registration) +
  instruments-service@9267e0ea (DERIVED citations on chainlink.py, CHAINLINK-* added to the IS venue set, goldens
  regenerated) + instruments-service@793125ad (meteora/lifinity/phoenix/pyth wired into factory + goldens) — all four
  verified present + reachable via `git log --oneline | grep <sha>` in their repos, commit messages match the claimed
  content, dated 2026-07-20 on live-defi-rollout"
---

# UAC/IS DeFi venue lockstep half-landed — instruments-service tree RED fleet-wide

> **✅ RESOLVED 2026-07-21.** Adapter-first ordering (Option A from "Remediation options" below) completed same-day:
> `is@6506b505` landed the real `ChainlinkOracleReferenceDataAdapter`, `is@9267e0ea` + `is@793125ad` wired all 5
> outstanding venues into the IS factory/venue-set/goldens, and `uac@ae83689b` re-declared CHAINLINK-* `phase=live` with
> real adapter keys. Cross-referenced evidence: `defi_consolidated_closeout_2026_07_18.md` Progress Log, the 2026-07-20
> entry titled "✅✅ CHAINLINK FULLY FIXED end-to-end; the adapter-first bet paid off" — measured **IS 98 == UAC 98,
> drift guard EQUAL=True, `UAC-only` empty**. All four cited commits independently confirmed real and reachable on
> `live-defi-rollout` in both repos before this doc was flipped.

## Impact (why this is P0)

`instruments-service` **cannot ship anything**. `quality-gates.sh` is red → no `.qg_last_passed_sha` sentinel →
`quickmerge` Pass-2 refuses. This blocks every agent working in that repo, not just the author. Measured RED
continuously from ~12:37 to ~13:46 (5 polls) and still red at time of writing.

## Root cause — ONE cause, 5 failing tests

`unified-api-contracts@3f79489f` (**slot-4**, 2026-07-20, ~2h before this doc):

> `feat(defi): canonicalize DeFi catalogue venues - add METEORA/LIFINITY/PHOENIX (Solana DEX) + CHAINLINK x5/PYTH (oracles) **in drift-guard lockstep**; add DEFI_FORCE_INCLUDE_POOLS …`

It added 9 venues to UAC (`VENUE_TO_ADAPTER_KEY` + `VENUES_BY_ASSET_GROUP["defi"]`, with `defi_venues.py` marking
CHAINLINK-\* `live` and `defi_venue_capabilities.py` giving each a per-chain `oracle_prices` coverage floor). The
claimed lockstep half in instruments-service was never written.

| failing test                                                                          | what it proves                                                                    |
| ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `test_adapter_routing_uac_invariant::test_every_uac_adapter_key_resolves_to_a_class`  | 9 UAC `VENUE_TO_ADAPTER_KEY` entries have no class in `factory._ADAPTERS`         |
| `test_factory_comprehensive::test_adapter_data_sources_covers_all_adapters`           | `pyth, phoenix, chainlink, lifinity, meteora` missing from `ADAPTER_DATA_SOURCES` |
| `test_orchestrator_helpers::test_defi_set_equals_uac_denominator_drift_guard`         | "UAC-only (denominator re-widened)" = exactly those 9                             |
| `test_expected_universe_golden::test_expected_matches_golden[defi]`                   | golden=222 vs actual=237 (CHAINLINK × {spot_asset,spot_pair} × oracle_prices …)   |
| `test_pipeline_e2e_prediction::test_rule11_per_ag_dedup_target_counts_byte_unchanged` | DEFI dedup'd target count 98 ≠ 89 (+9)                                            |

## The two gaps are NOT the same

1. **BOOKKEEPING (4 keys).** `adapters/defi/{meteora,lifinity,phoenix,pyth}.py` all exist with ctor-compatible classes
   (`MeteoraReferenceDataAdapter`, `LifinityReferenceDataAdapter`, `PhoenixReferenceDataAdapter`,
   `PythOracleReferenceDataAdapter`); none is in the factory's `accepts_date`/`supports_protocol_slug` sets, so no extra
   ctor plumbing is needed. They just need registering in `_ADAPTERS` + `ADAPTER_DATA_SOURCES`.
2. **REAL MISSING ARTIFACT (chainlink).** `adapters/defi/chainlink.py` **does not exist** (verified repo-wide). UAC
   nonetheless asserts it does — `venue_adapter_keys.py:228-230` ("new IS chainlink.py adapter (per-chain aggregator
   feeds via Alchemy RPC)"), `_defi.py:893-894`, `defi_venues.py:232-233`. The only Chainlink feed registry in the
   workspace is **MTDS-side** (`_oracle_prices_constants.py::_CHAINLINK_FEEDS_BY_CHAIN`), which instruments-service may
   NOT import (T4 no service→service deps).

**Registering the 4 alone does NOT unblock** — tests 1 and 3 both still fail on the absent `chainlink` key. A chainlink
decision is REQUIRED.

## Notes that matter for whoever fixes it

- `_DEFI_GRAPH_ADAPTERS` is **additive to** `_ADAPTERS`, not an alternative: `factory.py:568` does a bare
  `_ADAPTERS[adapter_key]` subscript → a key in the frozenset but absent from `_ADAPTERS` is a runtime `KeyError`.
- `test_adapter_routing_uac_invariant` excludes keys equal to `NO_ADAPTER_YET` (`= "__no_adapter_yet__"`, already used
  for FX / ODDS_API / PINNACLE / BETFAIR_SB_UK) — the sanctioned sentinel for a **declared-but-adapterless** venue.
- `test_factory_comprehensive`'s `known_gaps` is a **local set literal in the test body**, not a production allowlist,
  and is already dead code (both entries are present in `ADAPTER_DATA_SOURCES`). **Do not grow it** to paper over this.
- The golden has a sanctioned regeneration recipe: `.venv/bin/python scripts/regenerate_expected_universe_golden.py` —
  but regenerating BEFORE the universe is genuinely settled would bake in a half-complete denominator.
- `jupiter.py` is unregistered **deliberately** (execution-only, per `venue_adapter_keys.py:246`) — unrelated; leave it
  alone.

## Remediation options (author's call — both touch slot-4's in-flight surface)

- **A — complete the lockstep forward.** Write the real `adapters/defi/chainlink.py` (per-chain aggregator feeds; needs
  an IS-local curated feed registry, or promote `_CHAINLINK_FEEDS_BY_CHAIN` into UAC as the shared SSOT), register all 5
  keys, add the venues to the IS defi venue producer so `_build_defi_venues()` == `VENUES_BY_ASSET_GROUP["defi"]`, then
  regenerate the golden + update the DEFI count 89→98.
- **B — narrow honestly until the adapter lands.** Register the 4 that exist; set `CHAINLINK-*` → `NO_ADAPTER_YET` and
  drop CHAINLINK-\* from `VENUES_BY_ASSET_GROUP["defi"]` (the @6bcff215 invariant is _denominator == IS-producible set_,
  and an adapterless venue is not producible); regenerate the golden + count for the +4 (not +9). Reversible when
  chainlink.py lands.

**Do NOT** register a chainlink stub or alias it to the Pyth class — UAC declares those 5 venues `live` with real
coverage floors, so a stub would silently emit wrong reference data instead of failing loudly.

## Why slot-3 did not fix it

Autonomous rule 4 ("red gates are yours to fix") is premised on _"assume no one else is working — one operator, one
laptop, one slot."_ That premise is **false here**: `3f79489f` is **slot-4**, 2 hours old, and both remediation paths
edit that agent's in-flight surface (their UAC declaration and/or the IS half they are presumably writing). Per
multi-agent safety ("never edit unfamiliar/recently-pushed files"; "never two agents on the same file"), slot-3
diagnosed it fully and handed it back to its owner rather than racing them into a merge conflict. Writing a speculative
Chainlink adapter would additionally have produced unverifiable reference data.

**Blocked behind this:** the Option B DeFi on-chain removal-probe subsystem (built, tested, runtime-verified on prod)
cannot be shipped from slot-3 until the IS tree is green — see
`defi_catalogue_available_to_false_delisting_2026_07_20.md`.
