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
depends_on: []
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

## Progress Log

### 2026-06-29 — Step 1 pre-audit complete (AWAITING OPERATOR SIGN-OFF on divergences)

**Plan activated** (status draft→active, operator-approved): unified-trading-pm@f92cd93d9.

**Premise correction (BIG FINDING — surfaced to operator):** the plan assumed the venue producers already return
_identical_ sets to `VENUES_BY_ASSET_GROUP[ag]` and the refactor is a no-behaviour-change wiring exercise. The pre-audit
shows IS and UAC **diverge by design across all 5 AGs** — grain differences (cefi), orthogonal registries (sports), and
a UAC superset (defi). So `set(IS) == set(UAC)` is FALSE today; the invariant must be
`set(IS) == set(UAC) modulo NAMED filters`, and for cefi/sports a grain/semantic adapter (not just a filter) is needed.
This does not make it non-pure-refactor (behaviour still must be byte-identical before/after) but the filter surface is
large and several items need an operator deliberate-vs-drift ruling before any code moves.

**File:line citations:**

- UAC `VENUES_BY_ASSET_GROUP`: `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:222`
  (cefi 223-270, tradfi 271-294, defi `list(_ALL_DEFI_VENUES)` 295, sports 296-315, prediction 316-320). DeFi venue set:
  `unified_api_contracts/registry/defi_venues.py` (`_ALL_DEFI_VENUES`); subgraph chains
  `registry/capability_declarations/_defi.py` (`SUBGRAPH_IDS`, `get_supported_chains_for_protocol`).
- IS `_CEFI_VENUES`: `instruments-service/instruments_service/engine/orchestrator/venue_core.py:91-140`;
  `_TRADFI_VENUES` 143-155; `_SPORTS_PROVIDER_VENUES` 158-166; `get_venues_for_asset_groups` 307-341 (prediction branch
  line 340 is a **local literal** `["POLYMARKET","KALSHI"]`, NOT UAC-sourced; sports branch 329-336 is a local literal
  of reference-data providers).
- IS DeFi: `engine/orchestrator/defi.py` — `_STATIC_DEFI_VENUES` 76-81, `_SOLANA_DEFI_VENUES` 85-93,
  `_SUBGRAPH_PROTOCOL_TO_VENUE_PREFIX` 50-72, `_build_defi_venues()` 102-110 (= subgraph-derived ∪ static ∪ solana).

**Divergence summary (non-MATCH only; full per-venue table in session audit a102683176b3bb714):**

| AG         | divergence                                                                                                                                                             | side         | code-comment evidence                                                                                                                                          | provisional class                            |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| cefi       | `OKX` (UAC) vs `OKX-SPOT`/`-SWAP`/`-FUTURES` (IS)                                                                                                                      | grain        | IS: "Do NOT add bare OKX — maps to same Tardis exchange as OKX-SPOT (duplicate data)"                                                                          | **DECISION A — grain adapter**               |
| cefi       | `COINBASE` (UAC) vs `COINBASE-SPOT` (IS)                                                                                                                               | grain        | UAC keeps bare COINBASE; IS uses Tardis-disambiguated COINBASE-SPOT                                                                                            | **DECISION A — grain adapter**               |
| cefi       | `KALSHI-PERP`, `POLYMARKET-PERP` (UAC-only; IS adapters exist, not in `_CEFI_VENUES`)                                                                                  | UAC          | UAC 268-269 perp CLOBs; IS factory has adapters but enumeration omits them                                                                                     | **DECISION B — bug vs intended**             |
| tradfi     | `YAHOO_FINANCE` (UAC-only)                                                                                                                                             | UAC          | UAC: "legacy source-as-venue artifact … not a real venue, kept to avoid manifest churn"                                                                        | deliberate filter (comment)                  |
| sports     | UAC odds venues (ODDS_API/PINNACLE/BETFAIR\*/DRAFTKINGS/FANDUEL) vs IS ref-providers (API_FOOTBALL/FOOTYSTATS/UNDERSTAT/TRANSFERMARKT/SOCCER_FOOTBALL_INFO/OPEN_METEO) | orthogonal   | IS: "betting market instruments come from MTDS via Odds API — documented exception"                                                                            | **DECISION C — orthogonal sets**             |
| prediction | none (sets MATCH; IS is a local literal not UAC-sourced)                                                                                                               | sourcing     | wire IS→UAC, no set change                                                                                                                                     | proceed (no decision)                        |
| defi       | ~70 UAC-only venues (LST/vault/restaking "pipeline", gas/governance/bridge MTDS-only, multi-chain morpho/yearn, marginfi/solend/solblaze/jitorestaking-SOLANA)         | UAC superset | mixed: euler_v2 "removed — not needed yet", JUPITER "execution-only, not instrument discovery", COMPOUND_V3-POLYGON "not active on Polygon"; others no comment | **DECISION D — subgraph-backed-only filter** |
| defi       | IS `_STATIC_DEFI_VENUES`/`_SOLANA_DEFI_VENUES` are already a SUBSET of UAC `_ALL_DEFI_VENUES`                                                                          | (none)       | the "promote into UAC" Phase-1 task is largely already done in UAC; real work = make IS READ UAC + filter                                                      | confirm during Step 2                        |

**Gate status:** diff table checked in ✅. Operator verdicts on DECISION A–D PENDING — pre-audit checkbox stays
unflipped until every divergence has a confirmed verdict (per the gate). No code moved.

### 2026-06-29 — Operator verdicts (sign-off received)

- **DECISION A — CeFi grain (OKX/COINBASE):** **PUSH SPLIT INTO UAC.** Replace bare `OKX`→`OKX-SPOT`/`-SWAP`/`-FUTURES`
  and `COINBASE`→`COINBASE-SPOT` (+ existing `COINBASE-FUTURES`) in `VENUES_BY_ASSET_GROUP[cefi]`; drop the bare forms.
  IS then reads UAC directly (no grain adapter) so `set(IS)==set(UAC)` holds for cefi. **PREREQ: full UAC + workspace
  blast-radius audit of bare `"OKX"`/`"COINBASE"` consumers (capabilities, coverage_starts, mvp_scope,
  VENUE_TO_ASSET_GROUP reverse-lookup, MTDS/IS) before the edit** — this touches the canonical universe.
- **DECISION B — CeFi perps (KALSHI-PERP/POLYMARKET-PERP):** **INVESTIGATE FIRST.** Determine whether the perp venues
  (cefi) and the prediction venues (KALSHI/POLYMARKET) use one adapter or two-in-two-places; check WHICH actually ran +
  deployed (live as recently as today, batch a few days ago) and treat that as canonical; collapse to ONE. Focus only on
  the deployed path. Verdict deferred to the investigation result.
- **DECISION C — Sports:** **TWO SEPARATE REGISTRIES.** Sports is EXEMPT from the set-equality invariant. IS
  reference-data providers (API_FOOTBALL/FOOTYSTATS/UNDERSTAT/TRANSFERMARKT/SOCCER_FOOTBALL_INFO/OPEN_METEO) stay
  IS-owned; UAC sports = market-data/odds venues. **Operator clarification 2026-06-29: `ODDS_API` (and the odds venues)
  live in MTDS, not IS — that is why they are absent from the IS producer.** Document the two-layer split; the invariant
  skips sports.
- **DECISION D — DeFi:** **KEEP IS HARDCODED SUBSET** + **EXCLUDE-FROM-MVP the UAC-only venues not yet in IS.** IS
  `_build_defi_venues()` stays as-is (no UAC read for defi; "promote \_STATIC/\_SOLANA into UAC" task DROPPED — already
  a subset). **Operator directive 2026-06-29: the ~70 UAC-only defi venues that are not in IS yet must be excluded from
  MVP** so they do not corrupt the honest-coverage denominator (live-phase-but-0-rows). **This overrides the plan's "no
  MVP-rule change" hard constraint FOR DEFI ONLY, operator-approved.** PREREQ: investigate the cleanest mechanism
  (`DEFI_VENUE_PHASE` re-phase vs `mvp_scope.py` exclusion) before editing.
- **Comment-backed deliberate filters (no controversy):** tradfi `YAHOO_FINANCE` stays UAC-only (not a real venue) → IS
  excludes via a named filter.

**Revised Phase-1 scope after verdicts:** set-equality invariant applies cleanly to **cefi** (after the UAC grain push),
**tradfi** (modulo the named YAHOO_FINANCE filter), and **prediction** (wire IS→UAC). **defi** and **sports** are EXEMPT
from set-equality (documented), but defi gains an MVP-exclusion sub-task. Next: three read-only investigations before
any edit — (1) UAC blast-radius for dropping bare OKX/COINBASE; (2) KALSHI/POLYMARKET adapter-reality (deployed path);
(3) defi MVP-exclusion mechanism for the UAC-only-not-in-IS venues.

### 2026-06-29 — Three investigation results (read-only; gate the edits) — RE-DECISIONS NEEDED

**INV-1 (KALSHI/POLYMARKET adapter-reality) → resolves DECISION B as "KEEP BOTH":** there are TWO distinct adapters per
platform serving DIFFERENT instrument universes, sharing only the physical exchange — `KALSHI`/`POLYMARKET` = prediction
YES/NO binary markets (`PREDICTION_MARKET`, asset_group=prediction), `KALSHI-PERP`/`POLYMARKET-PERP` = CFTC crypto perps
(`PERPETUAL`, asset_group=cefi, funding). Deployed reality: prediction venues actively enumerate + capture (4,360
KALSHI + 468 POLYMARKET instruments, live CLOB day=2026-06-22/23); `KALSHI-PERP` live WS + perp-funding deployed
(mtds@c487a78, VM `cefi-kalshi-perp-book-snapshot`) but IS BATCH enumeration silently SKIPS it because `_CEFI_VENUES`
omits it; `POLYMARKET-PERP` scaffold BLOCKED-UPSTREAM (`perps-api.polymarket.com` NXDOMAIN since 2026-06-21,
honest-absence). **Verdict: keep all four; the `_CEFI_VENUES` omission is the only real bug — and the cefi consolidation
(IS reads UAC) fixes it for free** (POLYMARKET-PERP records honest-absence, not fake rows). NO adapter collapse.
Implementation watch-item: the perp adapters' `InstrumentRecord.venue` is lowercase (`"kalshi-perp"`) vs UAC canonical
`"KALSHI-PERP"` — verify normalization on enumeration.

**INV-2 (UAC OKX/COINBASE blast-radius) → DECISION A must be RE-DECIDED — "push split into UAC" is a CROSS-SERVICE
BREAKING CHANGE, out of plan scope:**

- Bare `OKX`/`COINBASE` are an INTENTIONAL execution-context alias, NOT drift: UAC comments it
  (`market_data_categories.py:1082` "Bare 'OKX' kept for execution-context/client-config callers that don't split by
  market") and `mvp_scope._CEFI_SUB_VENUE_BASES = frozenset({"OKX"})` exists specifically to resolve bare-OKX callers.
- Dropping the bare forms cascades into **UTL `Venue` StrEnum** (`config_interface/instrument.py:27,30`
  `Venue.OKX="OKX"`, `Venue.COINBASE="COINBASE"`) consumed by **execution-service + strategy-service** → a `feat!`
  breaking change needing a semver bump + multi-service migration — OUTSIDE this plan's repos (UAC + IS only).
- Data-correctness risk: split forms (`OKX-SPOT/-SWAP/-FUTURES`, `COINBASE-SPOT/-FUTURES`) have NO genesis dates in
  `coverage_starts.py` → expected-denominator corruption unless backfilled; `OKX-SWAP` is not even in the cefi list yet.
- ~22 UAC/UTL/IS consumer sites enumerated (capabilities, venue_mapping tardis-routing, session_times,
  venue_launch_dates, instrument_config, capability_declarations, instrument_key parse-compat, paper/transfer/exec
  types, tests).
- **WORKER RECOMMENDATION: PIVOT Decision A back to the named grain-adapter in IS** (the original Option A): UAC keeps
  bare canonical cefi venues (+ the split forms already present in capabilities); IS derives its Tardis-fetch venues
  from UAC via a NAMED, reasoned `expand_cefi_tardis_endpoints()` filter (bare OKX→3 Tardis splits,
  COINBASE→SPOT/FUTURES). Invariant becomes `set(IS) == expand(set(UAC[cefi]))`. Delivers the SSOT-consolidation value
  (IS stops being a hand-maintained mirror; KALSHI-PERP/POLYMARKET-PERP auto-included → fixes INV-1 bug) WITHOUT the
  breaking enum change and stays in-scope (UAC + IS). Awaiting operator confirm.

**INV-3 (defi MVP-exclusion) → mechanism fork + one urgent fix:**

- The honest-coverage denominator is driven by `VENUES_BY_ASSET_GROUP["defi"]` (= full `_ALL_DEFI_VENUES`), NOT by
  `is_mvp`; `is_mvp("defi",…)` already returns False for all but 13 venues (`DeFiMvpRule.venues`). `DEFI_VENUE_PHASE` is
  orthogonal (deployment-UI only).
- **URGENT clearly-correct fix (in UAC scope): `ROCKETPOOL-ETHEREUM` is phase=live AND in `DeFiMvpRule.venues`
  (MVP-expected) BUT not producible by IS** → permanent MVP-tagged `expected_unattempted` rows depressing MVP coverage
  %. Per operator "not in IS → exclude from MVP", remove it from `DeFiMvpRule.venues` (`mvp_scope.py:557`) + bump
  `MVP_SCOPE_CONFIG_VERSION` 11→12; update `test_defi_identity_with_mds_capture_mvp`.
- The broader "exclude the other ~23 live-but-not-IS venues from the denominator" requires narrowing
  `VENUES_BY_ASSET_GROUP["defi"]` (or making the denominator respect `is_mvp`) — that logic lives in
  `check_enumeration_completeness.py`, owned by the `honest_coverage_v2_instrument_denominator_2026_06_28.md` plan.
  **WORKER RECOMMENDATION: do the ROCKETPOOL fix here; route the denominator-narrowing to honest_coverage_v2 as a
  tracked todo** (avoids cross-plan collision + scope creep). Awaiting operator confirm.
