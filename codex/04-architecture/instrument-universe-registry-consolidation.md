---
last_reviewed: 2026-06-29
scope: [engineer, admin]
status: PROPOSAL
nature: design
---

# Instrument-Universe Registry Consolidation — target architecture (PROPOSAL)

> **Status: PROPOSAL, not yet implemented.** This doc describes the TARGET. The current state is the
> layered/partly-mirrored arrangement described in
> [`instruments-service-as-ssot-for-mtds.md`](instruments-service-as-ssot-for-mtds.md). The execution plan is
> [`plans/active/instrument_universe_registry_consolidation_2026_06_29.md`](../../plans/active/instrument_universe_registry_consolidation_2026_06_29.md).
> Until that plan ships, the SSOT for "how the universe is assembled today" remains the layered arrangement below — do
> not code against this target before its phase lands.

## Problem — the universe is assembled across mirrored layers

"Which instruments should be grabbed daily, per asset_group × venue × instrument_type × data_type (× league for sports)"
is the foundation of MTDS honest coverage: the [honest-coverage model](../02-data/honest-coverage-model.md) Layer-1
audit reconciles an EXPECTED matrix against the ENUMERATED catalogue, and Layer-2 download coverage is only trustworthy
once Layer-1 = 100%. So the EXPECTED matrix is the denominator of the entire MVP coverage guarantee.

That EXPECTED matrix is sourced from **three places that can drift**:

1. **UAC is the canonical enum** — `VENUES_BY_ASSET_GROUP` / `DATA_TYPES_BY_ASSET_GROUP`
   (`unified_api_contracts/registry/market_data_categories.py`) + `*_SOURCE_COVERAGE_START`
   (`canonical/coverage_starts.py`). This is the intended SSOT.
2. **instruments-service re-declares venues** — `_CEFI_VENUES` / `_TRADFI_VENUES` in `engine/orchestrator/venue_core.py`
   are **hardcoded mirrors** of (1); `engine/orchestrator/defi.py` builds DeFi venues dynamically from UAC subgraph
   protocols but adds hardcoded `_STATIC_DEFI_VENUES` + `_SOLANA_DEFI_VENUES`.
3. **A separate adapter map** — `reference_data/factory.py::CANONICAL_VENUE_TO_ADAPTER` is an independent hardcoded
   venue→adapter dict, and the per-AG EXPECTED-universe enumerators live as separate functions in
   `scripts/enumerate_expected_universe.py` (`_enumerate_cefi/_tradfi/_defi/_sports`).

A hardcoded CeFi/TradFi mirror that silently diverges from UAC corrupts the denominator → corrupts the honest-coverage
verdict. The mirrors exist for runtime convenience, not by design.

## Target — one canonical input, thin runtime resolvers

```
UAC canonical registry  (the ONLY place a venue/data_type/coverage-window is DECLARED)
  ├─ VENUES_BY_ASSET_GROUP / DATA_TYPES_BY_ASSET_GROUP / *_SOURCE_COVERAGE_START   (already canonical)
  └─ VENUE_TO_ADAPTER_KEY                                                          (NEW — venue→adapter KEY, data only)
            │  read at runtime, never mirrored
            ▼
instruments-service (thin resolvers — code, no re-declared universe data)
  ├─ venue_core.get_venues_for_asset_groups()   reads UAC; _CEFI_VENUES/_TRADFI_VENUES DELETED
  ├─ factory.get_adapter_for_canonical_venue()   maps UAC adapter-KEY → adapter CLASS (key in UAC, class in IS)
  └─ expected_universe.build_expected(asset_group)  ONE entry point; per-AG strategy objects behind it
            │
            ▼
honest-coverage Layer-1 EXPECTED matrix  (denominator now provably == UAC)
```

### The three moves

1. **Venues read from UAC at runtime.** Delete `_CEFI_VENUES` / `_TRADFI_VENUES`; `get_venues_for_asset_groups()`
   returns `VENUES_BY_ASSET_GROUP[ag]` directly. Any deliberate IS-side narrowing (e.g. dropping a not-yet-adapterable
   venue) becomes an explicit, named filter with a reason — never a silent omission in a parallel list.
2. **Adapter routing UAC-derived.** UAC owns the venue→adapter-**key** mapping (pure data, no IS import — respects the
   tier/import architecture: UAC is upstream of IS). IS keeps only key→**class** instantiation.
   `CANONICAL_VENUE_TO_ADAPTER` stops being an independent source of venue truth; a venue with no adapter key is a loud
   UAC error, not a missing dict entry.
3. **One expected-universe entry point.** `build_expected(asset_group)` is the single public function; the genuinely
   different per-AG grains (cefi lifecycle, defi chain-genesis, tradfi calendar, sports per-league) live behind it as
   per-AG strategy objects sharing one interface. This is a unified _interface_, not a collapse of the per-AG logic.
   **Execution note:** this third move is tracked under
   [`plans/active/honest_coverage_v2_instrument_denominator_2026_06_28.md`](../../plans/active/honest_coverage_v2_instrument_denominator_2026_06_28.md)
   (the honest-coverage Layer-1 effort that owns `check_enumeration_completeness.py`), not the consolidation plan — they
   share the same surface, so they were merged 2026-06-29.

## Invariant this buys

`set(IS expected venues for ag) == set(UAC.VENUES_BY_ASSET_GROUP[ag])` for every asset*group, enforceable as a single
test/QG check. The honest-coverage Layer-1 denominator becomes \_provably* the UAC canonical universe instead of a
mirror that has to be eyeballed. MVP filtering (`is_mvp` / `get_mvp_data_types_for_cefi_venue`) is unchanged — it
composes on top of the canonical venue set exactly as today.

## Non-goals / explicitly out of scope

- No change to the MVP scope rules ([`mvp-scope-canonical.md`](../02-data/mvp-scope-canonical.md) / `mvp_scope.py`).
- No change to the honest-coverage two-layer model or the manifest schema — only the _source_ of the Layer-1 EXPECTED
  matrix is consolidated.
- DeFi dynamic venue discovery from subgraph protocols stays; the hardcoded static **and Solana** venue lists are
  promoted into UAC so `VENUES_BY_ASSET_GROUP[defi]` is the full DeFi universe (resolved 2026-06-29).

## SSOTs this composes with

- [`instruments-service-as-ssot-for-mtds.md`](instruments-service-as-ssot-for-mtds.md) — IS owns capture; this doc
  clarifies UAC owns the _enumeration_ IS reads.
- [`tier-and-import-architecture.md`](tier-and-import-architecture.md) — why the adapter _class_ can't live in UAC (UAC
  is upstream), only the adapter _key_.
- [`../02-data/honest-coverage-model.md`](../02-data/honest-coverage-model.md) — the consumer of the EXPECTED matrix
  this consolidation hardens.
