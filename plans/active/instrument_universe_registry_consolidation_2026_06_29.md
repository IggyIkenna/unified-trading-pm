---
doc_type: plan
title: "Instrument-Universe Registry Consolidation — UAC is the single source for venues + adapter routing (all 5 AGs)"
summary:
  "Kill the hardcoded venue mirrors and the parallel adapter map in instruments-service so the venue universe is sourced
  from UAC at runtime for every asset_group (cefi, defi, tradfi, sports, prediction). Two phases, lowest-risk-first: (1)
  all per-AG venue producers read VENUES_BY_ASSET_GROUP at runtime — delete _CEFI_VENUES/_TRADFI_VENUES, promote the
  hardcoded DeFi static + Solana venue lists into UAC, align the sports-provider and prediction venue sources; (2)
  adapter routing becomes UAC-derived (UAC owns venue→adapter-KEY data, IS owns key→class). The expected-universe
  single-entry-point work (former Phase 3) is folded into honest_coverage_v2_instrument_denominator. No MVP-rule or
  manifest-schema change."
status: active
nature: design
asset_group: [cefi, defi, tradfi, sports, prediction, infrastructure]
stage: [data-ingestion, meta]
repos: [unified-api-contracts, instruments-service]
scope: [engineer, admin]
tags: [instrument-universe, venue-registry, adapter-routing, honest-coverage, ssot-consolidation, data-correctness]
related:
  [
    ../../codex/04-architecture/instrument-universe-registry-consolidation.md,
    ../../codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    ../../codex/04-architecture/tier-and-import-architecture.md,
    ../../codex/02-data/honest-coverage-model.md,
    honest_coverage_v2_instrument_denominator_2026_06_28.md,
  ]
created: 2026-06-29
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 1.6
assigned_role: backend-engineer
drift_direction: advance-code
last_updated: 2026-06-29
locked_by: NA
source: [operator request 2026-06-29]
---

# Instrument-Universe Registry Consolidation (all 5 AGs)

> **Status: active** — operator-approved 2026-06-29. Codex target:
> [`instrument-universe-registry-consolidation.md`](../../codex/04-architecture/instrument-universe-registry-consolidation.md).
> **Resolved 2026-06-29:** expected-universe single-entry-point work folded into
> [`honest_coverage_v2_instrument_denominator`](honest_coverage_v2_instrument_denominator_2026_06_28.md) (this plan =
> venues
>
> - adapter routing only); DeFi static **and Solana** venues promoted into UAC; adapter = key-in-UAC / class-in-IS;
>   deliberate venue divergences are surfaced to the operator AS THEY ARISE during the Phase-1 diff (no upfront list).

## Coverage — all five asset groups

Each AG has a venue producer that must read from UAC instead of a hardcoded/parallel source:

| AG         | Today's venue source (to consolidate)                                                                         |
| ---------- | ------------------------------------------------------------------------------------------------------------- |
| cefi       | `_CEFI_VENUES` (hardcoded mirror of `VENUES_BY_ASSET_GROUP[cefi]`) — delete                                   |
| tradfi     | `_TRADFI_VENUES` (hardcoded mirror) — delete                                                                  |
| defi       | dynamic from UAC subgraph protocols ✓ + `_STATIC_DEFI_VENUES` + `_SOLANA_DEFI_VENUES` — promote both into UAC |
| sports     | `_SPORTS_PROVIDER_VENUES` (provider→venue dict) — align to UAC `VENUES_BY_ASSET_GROUP[sports]`                |
| prediction | POLYMARKET + KALSHI venue source — confirm sourced from UAC, not a local literal                              |

## Phase 1 — all per-AG venue producers read from UAC at runtime [SEQUENTIAL, first]

- [ ] [AGENT] P1. **Pre-audit, all 5 AGs.** Per asset_group, diff `VENUES_BY_ASSET_GROUP[ag]` against the IS venue
      producer (cefi/tradfi mirrors, defi assembled list incl. static+Solana, sports-provider dict, prediction source).
      Produce a diff table (venue, in-UAC?, in-IS?, verdict). **Surface each divergence to the operator as it is found**
      (no assumption it's deliberate or stale). **Gate:** diff table checked in under plan notes; every divergence has
      an operator-confirmed verdict.
- [ ] [AGENT] P1. **Promote DeFi static + Solana venues into UAC.** Move `_STATIC_DEFI_VENUES` + `_SOLANA_DEFI_VENUES`
      into the UAC DeFi venue registry so `VENUES_BY_ASSET_GROUP[defi]` is the full DeFi universe (subgraph-derived ∪
      static ∪ Solana). **Gate:** UAC QG green; `rg '_STATIC_DEFI_VENUES|_SOLANA_DEFI_VENUES'` returns 0 hits in
      instruments-service.
- [ ] [AGENT] P1. **Rewrite the venue producers to read UAC** for cefi, tradfi, defi, sports, prediction:
      `venue_core.get_venues_for_asset_groups()` returns `VENUES_BY_ASSET_GROUP[ag]` directly; encode any
      operator-confirmed deliberate narrowing as a NAMED, reasoned filter function (never a parallel list). Delete
      `_CEFI_VENUES` / `_TRADFI_VENUES`; align `_SPORTS_PROVIDER_VENUES` + the prediction source to UAC. **Gate:**
      `rg '_CEFI_VENUES|_TRADFI_VENUES'` = 0 hits; instruments-service QG green.
- [ ] [AGENT] P1. **Invariant test across all 5 AGs:**
      `set(get_venues_for_asset_groups([ag])) == set(VENUES_BY_ASSET_GROUP[ag])` (modulo named filters) for cefi, defi,
      tradfi, sports, prediction. **Gate:** test passes in instruments-service unit suite.

## Phase 2 — adapter routing UAC-derived [SEQUENTIAL, after Phase 1]

- [ ] [AGENT] P1. Add `VENUE_TO_ADAPTER_KEY` (venue→adapter-key, pure data, no IS import) to the UAC registry — respects
      the tier/import architecture (UAC upstream of IS). **Gate:** UAC QG green; every venue in `VENUES_BY_ASSET_GROUP`
      has a key or a loud "no-adapter-yet" sentinel.
- [ ] [AGENT] P1. Rewrite `factory.get_adapter_for_canonical_venue()` to resolve UAC adapter-key → IS adapter **class**;
      `CANONICAL_VENUE_TO_ADAPTER` stops being a source of venue truth (keep only the key→class table). A venue with no
      UAC key raises loudly. **Gate:** `rg 'CANONICAL_VENUE_TO_ADAPTER'` only matches the key→class table;
      `URDI_SUPPORTED_VENUES` derives from UAC, not a frozen IS set.
- [ ] [AGENT] P2. Invariant test: every UAC venue resolves to an adapter (or an explicit not-yet-supported sentinel); no
      silent `KeyError`. **Gate:** test passes.

## Codex flip

- [ ] [AGENT] P2. After Phases 1–2 land, remove the PROPOSAL banner from
      `codex/04-architecture/instrument-universe-registry-consolidation.md` and update
      `instruments-service-as-ssot-for-mtds.md` to point at the consolidated registry. **Gate:** `docs(plans):` flip +
      codex audit clean.

## Success criteria (workspace-wide)

- [ ] [VERIFY] P1. `unified-api-contracts` + `instruments-service` both `quality-gates.sh` green. **Gate:** two green QG
      sentinels.
- [ ] [VERIFY] P1. End-to-end invariant for all 5 AGs: `IS expected venues per ag == UAC VENUES_BY_ASSET_GROUP[ag]`
      (modulo named filters). **Gate:** the Phase-1 invariant test green for cefi/defi/tradfi/sports/prediction.

## Notes / context

Implements
[`codex/04-architecture/instrument-universe-registry-consolidation.md`](../../codex/04-architecture/instrument-universe-registry-consolidation.md).
Pure-refactor SSOT consolidation (`estimate_class: refactor`, 0.4× multiplier): no behaviour change, no MVP-rule change,
no manifest-schema change — venue producers must return the same sets before and after (the invariant test is the
regression gate). Value: the venue side of the honest-coverage Layer-1 denominator becomes _provably_ the UAC canonical
universe instead of five separately-sourced lists that can silently drift. The expected-universe single-producer work
that consumes this lives in `honest_coverage_v2_instrument_denominator_2026_06_28.md` (folded there per operator
2026-06-29).

**Sizing note:** one human/local-only tracker (`assigned_vm: NA`, `execution_scope: local-only`). If promoted to
orchestrator dispatch, split Phase 1 and Phase 2 into two `status: draft` plans chained by `prereqs` per the
"plans-not-phases" rule (`PLAN_FORMAT.md` § Citadel Standards 2) — they are sequential and context-coupled.
