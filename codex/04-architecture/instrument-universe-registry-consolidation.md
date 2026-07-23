---
doc_type: codex-ssot
title: Instrument-Universe Registry Consolidation — UAC owns venue + adapter-key truth
summary:
  UAC owns venue + adapter-KEY truth — VENUES_BY_ASSET_GROUP + VENUE_TO_ADAPTER_KEY as the single declaration,
  instruments-service reduced to thin runtime resolvers, hardening the honest-coverage Layer-1 EXPECTED denominator.
status: current
nature: design
asset_group: [meta]
stage: [meta]
repos: [instruments-service]
scope: [engineer, admin]
tags: [instruments, uac, canonicalisation, honest-coverage, registry, refactor]
related:
  [
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/04-architecture/asset-class-ownership.md,
  ]
created: 2026-06-29
authoritative_for: [UAC VENUE_TO_ADAPTER_KEY and venue-enumeration consolidation]
referenced_by:
  [
    /codex/04-architecture/asset-class-ownership.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    plans/active/issues/instruments_service_plan_reconciliation_2026_06_29.md,
    plans/audit/results/mvp_instrument_universe_gap_audit_2026_06_17.md,
  ]
owner:
last_reviewed: 2026-06-29
code_refs:
---

# Instrument-Universe Registry Consolidation — UAC owns venue + adapter-key truth

> **Status: IMPLEMENTED** — Phase 1 (venue producers UAC-consolidated) shipped 2026-06-29
> (`instruments-service@4da6fe8` + `unified-api-contracts@6bcff215`); Phase 2 (adapter routing UAC-derived:
> `registry/venue_adapter_keys.py::VENUE_TO_ADAPTER_KEY` + `NO_ADAPTER_YET` sentinel, IS factory resolves key→class
> only, `URDI_SUPPORTED_VENUES` UAC-derived, UTL startup venue validation reads UAC directly) shipped 2026-07-03.
> Execution record: `plans/.../instrument_universe_registry_consolidation_2026_06_29.md`. Move 3 (one expected-universe
> entry point) remains tracked under
> [`plans/archive/2026_07/honest_coverage_v2_instrument_denominator_2026_06_28.md`](../../plans/archive/2026_07/honest_coverage_v2_instrument_denominator_2026_06_28.md).

## Problem — the universe is assembled across mirrored layers

"Which instruments should be grabbed daily, per asset_group × venue × instrument_type × data_type (× league for sports)"
is the foundation of MTDS honest coverage: the [honest-coverage model](/codex/02-data/honest-coverage-model.md) Layer-1
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

## Architecture — one canonical input, thin runtime resolvers

```
UAC canonical registry  (the ONLY place a venue/data_type/coverage-window is DECLARED)
  ├─ VENUES_BY_ASSET_GROUP / DATA_TYPES_BY_ASSET_GROUP / *_SOURCE_COVERAGE_START   (canonical)
  └─ VENUE_TO_ADAPTER_KEY (registry/venue_adapter_keys.py)                          (venue→adapter KEY, data only)
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

1. **Venues read from UAC at runtime — SHIPPED 2026-06-29** (`instruments-service@4da6fe8` +
   `unified-api-contracts@6bcff215`). `_CEFI_VENUES` / `_TRADFI_VENUES` deleted; `get_venues_for_asset_groups()` returns
   `VENUES_BY_ASSET_GROUP[ag]` modulo NAMED filters (`expand_cefi_tardis_endpoints()` cefi grain-adapter,
   `_TRADFI_NON_VENUE_KEYS`); defi denominator == IS-producible set; sports documented two-registry EXEMPT.
   `TestVenueProducerUACInvariant` is the regression gate.
2. **Adapter routing UAC-derived — SHIPPED 2026-07-03.** UAC owns the venue→adapter-**key** mapping
   (`registry/venue_adapter_keys.py::VENUE_TO_ADAPTER_KEY`, pure data, no IS import — UAC is upstream of IS), with the
   explicit `NO_ADAPTER_YET` sentinel for declared-adapterless venues (MTDS-owned odds venues, `YAHOO_FINANCE`,
   expand-only bare `COINBASE`). IS keeps only key→**class** instantiation (`factory._ADAPTERS`); the old IS
   `CANONICAL_VENUE_TO_ADAPTER` dict is DELETED; a venue with no UAC key raises loudly; `URDI_SUPPORTED_VENUES` and UTL
   `validate_venue_names()` derive from UAC `VENUES_WITH_REFERENCE_ADAPTER`. Regression gates:
   `test_venue_adapter_keys.py` (UAC — every canonical venue has a key or sentinel) +
   `test_adapter_routing_uac_invariant.py` (IS — every key resolves to a class).
3. **One expected-universe entry point.** `build_expected(asset_group)` is the single public function; the genuinely
   different per-AG grains (cefi lifecycle, defi chain-genesis, tradfi calendar, sports per-league) live behind it as
   per-AG strategy objects sharing one interface. This is a unified _interface_, not a collapse of the per-AG logic.
   **Execution note:** this third move is tracked under
   [`plans/archive/2026_07/honest_coverage_v2_instrument_denominator_2026_06_28.md`](../../plans/archive/2026_07/honest_coverage_v2_instrument_denominator_2026_06_28.md)
   (the honest-coverage Layer-1 effort that owns `check_enumeration_completeness.py`), not the consolidation plan — they
   share the same surface, so they were merged 2026-06-29.

## Invariant this buys

`set(IS expected venues for ag) == set(UAC.VENUES_BY_ASSET_GROUP[ag])` for every `asset_group`, enforceable as a single
test/QG check. The honest-coverage Layer-1 denominator becomes _provably_ the UAC canonical universe instead of a mirror
that has to be eyeballed. MVP filtering (`is_mvp` / `get_mvp_data_types_for_cefi_venue`) is unchanged — it composes on
top of the canonical venue set exactly as today.

## Non-goals / explicitly out of scope

- No change to the MVP scope rules ([`mvp-scope-canonical.md`](/codex/02-data/mvp-scope-canonical.md) / `mvp_scope.py`).
- No change to the honest-coverage two-layer model or the manifest schema — only the _source_ of the Layer-1 EXPECTED
  matrix is consolidated.
- DeFi dynamic venue discovery from subgraph protocols stays; the hardcoded static **and Solana** venue lists are
  promoted into UAC so `VENUES_BY_ASSET_GROUP[defi]` is the full DeFi universe (resolved 2026-06-29).

## SSOTs this composes with

- [`instruments-service-as-ssot-for-mtds.md`](instruments-service-as-ssot-for-mtds.md) — IS owns capture; this doc
  clarifies UAC owns the _enumeration_ IS reads.
- [`tier-and-import-architecture.md`](tier-and-import-architecture.md) — why the adapter _class_ can't live in UAC (UAC
  is upstream), only the adapter _key_.
- [`/codex/02-data/honest-coverage-model.md`](/codex/02-data/honest-coverage-model.md) — the consumer of the EXPECTED
  matrix this consolidation hardens.
