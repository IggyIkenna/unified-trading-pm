---
doc_type: plan
title: Instrument-Universe Registry Consolidation — UAC is the single source for venues + adapter routing (all 5 AGs)
summary:
  "Kill the hardcoded venue mirrors in instruments-service so the venue universe is UAC-sourced per asset_group. FINAL
  scope (post-audit, operator-locked 2026-06-29; see Progress Log): cefi → IS reads UAC via a named Tardis grain-adapter
  (UAC unchanged) + auto-fixes the KALSHI-PERP/POLYMARKET-PERP omission; tradfi → IS reads UAC minus a named
  YAHOO_FINANCE filter; prediction → IS reads UAC (was a local literal); defi + sports → EXEMPT from set-equality (IS
  keeps its defi producer; sports stays a two-registry split with MTDS owning odds venues); PLUS an operator-approved
  defi MVP-exclusion (re-phase DEFI_VENUE_PHASE live⟺IS-producible, narrow VENUES_BY_ASSET_GROUP[defi] denominator,
  remove ROCKETPOOL-ETHEREUM from MVP, bump MVP_SCOPE_CONFIG_VERSION). Phase 2 = UAC-derived adapter routing. The
  expected-universe single-entry-point work is folded into honest_coverage_v2_instrument_denominator. Two behaviour
  deltas (cefi +2 perps, defi MVP) are deliberate + operator-approved; all other AGs byte-identical."
status: completed
nature: design
asset_group: [cefi, defi, tradfi, sports, prediction, infrastructure]
stage: [data, meta]
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
last_updated: 2026-07-03
locked_by: NA
locked_since:
supersedes:
superseded_by:
depends_on: []
source: [operator request 2026-06-29]
assigned_role: backend-engineer
drift_direction: advance-code
---

## Deferred work — migrated to: **None** — successor: not applicable (all 14 todos completed; the two "deferred"

mentions in the body are incidental prose — "verdict deferred to the investigation result" and "no deferred `- [ ]` left
in this plan" — not DEFERRED-tagged items)

# Instrument-Universe Registry Consolidation (all 5 AGs)

> **✅ COMPLETED + ARCHIVED 2026-07-03.** All 14 todos done. Phase 1 (venue producers → UAC) shipped 2026-06-29
> (`instruments-service@4da6fe8` + `unified-api-contracts@6bcff215`); Phase 2 (adapter routing → UAC keys) + codex flip
> shipped 2026-07-03 (`unified-api-contracts@9eb5518`+`@6516ed4`, `unified-trading-library@5a83484`,
> `instruments-service@8b7ce01`). Standing SSOT:
> [`codex/04-architecture/instrument-universe-registry-consolidation.md`](../../codex/04-architecture/instrument-universe-registry-consolidation.md).
> One follow-up re-homed to `instruments_mtds_subset_consistency_remediation_2026_06_17.md` (MTDS prefix-map mirror).

> **Operator-approved 2026-06-29.** Codex target:
> [`instrument-universe-registry-consolidation.md`](../../codex/04-architecture/instrument-universe-registry-consolidation.md).
> **Resolved 2026-06-29:** expected-universe single-entry-point work folded into
> [`honest_coverage_v2_instrument_denominator`](honest_coverage_v2_instrument_denominator_2026_06_28.md) (this plan =
> venues
>
> - adapter routing only); DeFi static **and Solana** venues promoted into UAC; adapter = key-in-UAC / class-in-IS;
>   deliberate venue divergences are surfaced to the operator AS THEY ARISE during the Phase-1 diff (no upfront list).

## Coverage — all five asset groups (FINAL approach, post-investigation 2026-06-29 — see Progress Log for evidence)

> The original "every producer reads `VENUES_BY_ASSET_GROUP[ag]` directly and returns an identical set" premise was
> **overturned by the pre-audit** — IS and UAC diverge by design across all 5 AGs. The per-AG approach below is the
> operator-locked resolution. Authoritative detail + investigation evidence = the **Progress Log** at the bottom.

| AG         | FINAL approach (operator-locked)                                                                                                                                                                                                                                     |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| cefi       | IS reads UAC via a NAMED Tardis grain-adapter `expand_cefi_tardis_endpoints()` (UAC bare `OKX`/`COINBASE` → IS Tardis splits). UAC unchanged. Delete `_CEFI_VENUES`. Auto-includes `KALSHI-PERP`/`POLYMARKET-PERP` (fixes omission).                                 |
| tradfi     | IS reads `VENUES_BY_ASSET_GROUP[tradfi]` minus a NAMED non-venue filter (`YAHOO_FINANCE`). Delete `_TRADFI_VENUES`.                                                                                                                                                  |
| defi       | **EXEMPT from set-equality.** IS keeps `_build_defi_venues()` as-is. SEPARATE: UAC defi MVP-exclusion (re-phase live→pipeline for non-IS-producible, narrow `VENUES_BY_ASSET_GROUP[defi]` to the producible/denominator set, remove `ROCKETPOOL-ETHEREUM` from MVP). |
| sports     | **EXEMPT.** Two separate registries: IS owns reference-data providers; UAC sports = MTDS odds venues. Document, don't merge.                                                                                                                                         |
| prediction | IS reads `VENUES_BY_ASSET_GROUP[prediction]` (was a local literal). `KALSHI`/`POLYMARKET` (binary markets) stay distinct from the `*-PERP` cefi venues — KEEP BOTH.                                                                                                  |

## Phase 1 — per-AG venue producers consolidated to UAC (named filters where divergent) [SEQUENTIAL, first]

- [x] [AGENT] P1. **Pre-audit, all 5 AGs + operator verdicts.** Diff table + 3 follow-up investigations
      (adapter-reality, OKX/COINBASE blast-radius, defi MVP mechanism) complete; every divergence has an
      operator-confirmed verdict (A/B/C/D locked). — `unified-trading-pm@e084ed554` + Progress Log. **Gate met:** diff
      table checked in; all verdicts confirmed.
- [x] [AGENT] P1. **[IS] CeFi named Tardis grain-adapter.** ✅ `expand_cefi_tardis_endpoints()` added (bare `OKX`→3
      Tardis splits, `COINBASE`→`COINBASE-SPOT`, else passthrough); `get_venues_for_asset_groups(["CEFI"])` returns
      `expand(VENUES_BY_ASSET_GROUP[cefi])`; all `_CEFI_VENUES` consumers migrated to `VENUE_TO_ASSET_GROUP`; literal
      deleted. cefi delta == exactly `+{KALSHI-PERP, POLYMARKET-PERP}`; `rg '_CEFI_VENUES'` = 0; IS QG green. —
      `instruments-service@4da6fe8`.
- [x] [AGENT] P1. **[IS] TradFi UAC read + named filter.** ✅ `get_venues_for_asset_groups(["TRADFI"])` =
      `VENUES_BY_ASSET_GROUP[tradfi]` − named `_TRADFI_NON_VENUE_KEYS={YAHOO_FINANCE}`; `_TRADFI_VENUES` deleted; tradfi
      set unchanged before/after; IS QG green. — `instruments-service@4da6fe8`.
- [x] [AGENT] P1. **[IS] Prediction UAC read.** ✅ local literal replaced with `VENUES_BY_ASSET_GROUP[prediction]`; set
      unchanged; IS QG green. — `instruments-service@4da6fe8`.
- [x] [AGENT] P1. **[IS] Sports two-registry documentation.** ✅ IS reference-provider list unchanged; comment documents
      the MTDS-owns-odds-venues split (Decision C; ODDS_API et al. live in MTDS). — `instruments-service@4da6fe8`.
- [x] [AGENT] P1. **[UAC] DeFi MVP-exclusion (data-correctness; Decision D).** ✅ `DEFI_VENUE_PHASE` re-phased so
      `live ⟺ IS-producible` (28 live→pipeline, 33 pipeline→live); `VENUES_BY_ASSET_GROUP[defi]` narrowed to the
      live/producible denominator (`_ALL_DEFI_VENUES` kept as the full registry); `ROCKETPOOL-ETHEREUM` removed from
      `DeFiMvpRule.venues`; `MVP_SCOPE_CONFIG_VERSION` 11→12; tests updated. **Orchestrator-INDEPENDENTLY-verified:**
      `VENUES_BY_ASSET_GROUP[defi]` == the 55-venue producible set P EXACTLY (empty symmetric diff), version==12,
      ROCKETPOOL gone, all defi-MVP venues ⊆ P. UAC QG green. — `unified-api-contracts@6bcff215`. _(First agent attempt
      misread the static/Solana constants → reverted; redone with authoritative P. See Progress Log.)_
- [x] [AGENT] P1. **[IS] Invariant test.** ✅ `TestVenueProducerUACInvariant` added:
      `set(get_venues_for_asset_groups([ag]))` == named-filter-adjusted `VENUES_BY_ASSET_GROUP[ag]` for
      cefi/tradfi/prediction; defi + sports assert the documented EXEMPT relationship. Passes in IS unit suite (3964
      tests green). — `instruments-service@4da6fe8`. _(Follow-up when UAC defi lands: add a cross-repo drift-guard
      asserting `VENUES_BY_ASSET_GROUP[defi] == get_venues_for_asset_groups(["DEFI"])`.)_

## Phase 2 — adapter routing UAC-derived [SEQUENTIAL, after Phase 1]

- [x] [AGENT] P1. Add `VENUE_TO_ADAPTER_KEY` (venue→adapter-key, pure data, no IS import) to the UAC registry — respects
      the tier/import architecture (UAC upstream of IS). **Gate:** UAC QG green; every venue in `VENUES_BY_ASSET_GROUP`
      has a key or a loud "no-adapter-yet" sentinel. ✅ **DONE 2026-07-03** — `unified-api-contracts@9eb5518`
      (`registry/venue_adapter_keys.py`: `VENUE_TO_ADAPTER_KEY` 141 entries + `NO_ADAPTER_YET` sentinel ×9 +
      `VENUE_PREFIX_TO_PROTOCOL`/`PROTOCOL_TO_ADAPTER_KEY` moved from IS + `VENUES_WITH_REFERENCE_ADAPTER` frozenset;
      subgraph multi-chain expansion runs in UAC from its own `SUBGRAPH_IDS`) + root re-export `@6516ed4` (UTL top-level
      import surface). Gate met: UAC QG green (228s) ×2; `tests/unit/test_venue_adapter_keys.py` (8 tests)
      machine-asserts every `VENUES_BY_ASSET_GROUP` venue has a key-or-sentinel AND the sentinel set is exactly the 9
      declared venues. **Parity-proven**: non-sentinel map == old IS `CANONICAL_VENUE_TO_ADAPTER` byte-identical (0
      only-old / 0 only-new / 0 value-diffs); sentinels cover only venues that raised before.
- [x] [AGENT] P1. Rewrite `factory.get_adapter_for_canonical_venue()` to resolve UAC adapter-key → IS adapter **class**;
      `CANONICAL_VENUE_TO_ADAPTER` stops being a source of venue truth (keep only the key→class table). A venue with no
      UAC key raises loudly. **Gate:** `rg 'CANONICAL_VENUE_TO_ADAPTER'` only matches the key→class table;
      `URDI_SUPPORTED_VENUES` derives from UAC, not a frozen IS set. ✅ **DONE 2026-07-03** —
      `instruments-service@8b7ce01`: venue→key dict + dynamic loop + both prefix maps DELETED from `factory.py` (~170
      lines); `_resolve_uac_adapter_key()` raises loudly on unknown ("UNKNOWN to UAC") AND sentinel ("UAC declares it
      adapterless") venues, both keeping the historical "No URDI adapter" message prefix;
      `URDI_SUPPORTED_VENUES = VENUES_WITH_REFERENCE_ADAPTER` (UAC-derived); `urdi_reference_provider`
      unsupported-classification now also catches sentinels; 3 migration scripts + 7 test files + README migrated. Gate
      EXCEEDED: `rg 'CANONICAL_VENUE_TO_ADAPTER'` = **0 hits repo-wide** (name fully deleted, no shim). IS QG green
      (93s, full suite). **Cross-repo rider (same ship unit):** `unified-trading-library@5a83484` —
      `validate_venue_names()` reads UAC `VENUES_WITH_REFERENCE_ADAPTER` directly (hard dep), deleting the fragile
      optional `instruments_service` sibling import that would have broken on the symbol deletion; the silent
      degrade-to-warning path (URDI missing → skip validation) is GONE — venue preflight now always enforces. UTL QG
      green.
- [x] [AGENT] P2. Invariant test: every UAC venue resolves to an adapter (or an explicit not-yet-supported sentinel); no
      silent `KeyError`. **Gate:** test passes. ✅ **DONE 2026-07-03** — `instruments-service@8b7ce01`
      `tests/unit/test_adapter_routing_uac_invariant.py` (6 tests): key→class closure (every non-sentinel UAC key ∈
      `_ADAPTERS`), canonical-venue coverage cross-check, `URDI_SUPPORTED_VENUES is VENUES_WITH_REFERENCE_ADAPTER`
      identity, expanded-cefi enumeration fully resolvable end-to-end, loud-raise on sentinel (`ODDS_API`) + unknown
      venues. Companion UAC-side suite in `test_venue_adapter_keys.py`.

## Codex flip

- [x] [AGENT] P2. After Phases 1–2 land, remove the PROPOSAL banner from
      `codex/04-architecture/instrument-universe-registry-consolidation.md` and update
      `instruments-service-as-ssot-for-mtds.md` to point at the consolidated registry. **Gate:** `docs(plans):` flip +
      codex audit clean. ✅ **DONE 2026-07-03** (this commit) — consolidation doc: PROPOSAL banner → IMPLEMENTED status
      note with ship evidence, moves 1+2 marked SHIPPED (move 3 stays tracked in
      `honest_coverage_v2_instrument_denominator`); SSOT-for-MTDS doc gains the "where the universe is DECLARED" pointer
      block; workspace `cursor-configs/CLAUDE.md` service one-liner updated ("venue lists + adapter KEYS are UAC data").

## Success criteria (workspace-wide)

- [x] [VERIFY] P1. `unified-api-contracts` + `instruments-service` both `quality-gates.sh` green. ✅ IS QG green
      (`@4da6fe8`, 3964 tests); UAC QG green (`@6bcff215`).
- [x] [VERIFY] P1. End-to-end invariant: cefi/tradfi/prediction — `IS == UAC[ag]` modulo named filters (invariant test
      green, `@4da6fe8`); defi — `VENUES_BY_ASSET_GROUP[defi]` narrowed to == IS-producible set P
      (orchestrator-verified, `@6bcff215`); sports — documented EXEMPT two-registry split. _(Drift-guard follow-up below
      makes the defi equality a live test.)_
- [x] ✅ [AGENT] P2. **[IS] DeFi denominator drift-guard (follow-up, hardening).** Add an IS unit test asserting
      `set(VENUES_BY_ASSET_GROUP["defi"]) == set(get_venues_for_asset_groups(["DEFI"]))` (== `_build_defi_venues()`), so
      a future change to either side that re-introduces denominator/producible drift fails CI. Now PASSES (both == P
      after `@6bcff215`). **Gate:** test green in IS suite. _(Captured 2026-06-29; small single-test IS ship.)_ — **DONE
      2026-07-01** `instruments-service@e0ca6c2`: on inspection the pre-existing `test_defi_exempt_is_subset_of_uac` was
      STALE (subset-only, docstring claimed ~70 UAC-only venues). Verified live
      `is_defi == uac_defi ==     _build_defi_venues() == 55` (zero either side), so upgraded it to a two-direction
      equality drift-guard (`test_defi_set_equals_uac_denominator_drift_guard`) + fixed the stale class/method
      docstrings. IS QG green (147s).

## Notes / context

Implements
[`codex/04-architecture/instrument-universe-registry-consolidation.md`](../../codex/04-architecture/instrument-universe-registry-consolidation.md).
Originally scoped pure-refactor SSOT consolidation (`estimate_class: refactor`, 0.4× multiplier). **AMENDED 2026-06-29
(see Progress Log):** the pre-audit overturned the "identical sets before/after" premise; the FINAL operator-locked
scope has two deliberate, operator-approved behaviour deltas — (1) cefi now enumerates `KALSHI-PERP`/`POLYMARKET-PERP`
(fixes the `_CEFI_VENUES` omission), and (2) an approved **defi MVP-scope change** (re-phase + denominator narrow +
ROCKETPOOL). All other AGs remain byte-identical (the invariant test is the regression gate for cefi/tradfi/prediction).
Value: the venue side of the honest-coverage Layer-1 denominator becomes _provably_ the UAC canonical universe instead
of five separately-sourced lists that can silently drift. The expected-universe single-producer work that consumes this
lives in `honest_coverage_v2_instrument_denominator_2026_06_28.md` (folded there per operator 2026-06-29).

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

### 2026-06-29 — FINAL operator verdicts (locked — implementation may proceed)

- **DECISION A → PIVOT to named grain-adapter in IS.** UAC keeps bare canonical cefi venues unchanged; IS adds a NAMED
  `expand_cefi_tardis_endpoints()` filter (bare `OKX`→`OKX-SPOT`/`-SWAP`/`-FUTURES`; `COINBASE`→`COINBASE-SPOT`; all
  other UAC cefi venues pass through) and `get_venues_for_asset_groups(["CEFI"])` returns
  `expand(VENUES_BY_ASSET_GROUP["cefi"])`. Delete `_CEFI_VENUES`. Invariant = `set(IS)==expand(set(UAC[cefi]))`. NO UAC
  venue-registry change, NO UTL `Venue` enum change (stays in-scope UAC+IS). The expand auto-includes `KALSHI-PERP` +
  `POLYMARKET-PERP` → fixes the INV-1 omission (the ONLY before≠after delta for cefi: +2 perp venues, intended).
- **DECISION B → KEEP BOTH (confirmed).** No adapter collapse. Watch-items at implementation: (1) perp adapters emit
  lowercase `venue` (`"kalshi-perp"`) vs UAC `"KALSHI-PERP"` — verify normalization; (2) `POLYMARKET-PERP` is
  BLOCKED-UPSTREAM — verify IS enumeration records honest-absence and does NOT crash when its adapter early-exits.
- **DECISION C → TWO SEPARATE REGISTRIES (confirmed earlier).** sports producer stays IS-owned reference-providers;
  document the MTDS-owns-odds-venues split; invariant test SKIPS sports.
- **DECISION D → DO THE FULL DEFI MVP-EXCLUSION HERE NOW.** (a) re-phase the live-but-not-IS-producible defi venues
  `live`→`pipeline` in `DEFI_VENUE_PHASE`; (b) narrow `VENUES_BY_ASSET_GROUP["defi"]` so the honest-coverage denominator
  == the IS-producible set (no 0-row inflation AND no undercount — must verify the phase-vs-producible relationship, as
  some pipeline-phase venues ARE produced by IS, e.g. `UNISWAP_V3-ARBITRUM`); (c) remove `ROCKETPOOL-ETHEREUM` from
  `DeFiMvpRule.venues` + bump `MVP_SCOPE_CONFIG_VERSION` 11→12 + update `test_defi_identity_with_mds_capture_mvp`.
  Operator-approved MVP-scope change for defi. Coordinate with `honest_coverage_v2_instrument_denominator` (it owns
  `check_enumeration_completeness.py`) — add a cross-reference, don't double-edit the denominator code.

**Implementation split (different repos → parallelizable):** (1) instruments-service venue-producer refactor (cefi
grain-adapter + tradfi + prediction + sports doc + invariant test); (2) unified-api-contracts defi MVP-exclusion
(re-phase + narrow defi denominator + ROCKETPOOL + version bump + tests). Each ships via its own
`quality-gates.sh`-green

- quickmerge.

### 2026-06-29 — instruments-service SHIPPED (`instruments-service@4da6fe8`)

cefi/tradfi/prediction venue producers consolidated to UAC; `_CEFI_VENUES`/`_TRADFI_VENUES` deleted (consumers migrated
to `VENUE_TO_ASSET_GROUP`); `expand_cefi_tardis_endpoints()` named grain-adapter;
`_TRADFI_NON_VENUE_KEYS={YAHOO_FINANCE}` filter; sports/defi left as-is (EXEMPT, documented);
`TestVenueProducerUACInvariant` added. IS QG green (3964 tests). **Perp casing fix folded in** (newly exposed by
enabling perp enumeration): `kalshi_perp.py`/`polymarket_perp.py` now emit canonical uppercase
`KALSHI-PERP`/`POLYMARKET-PERP` (was lowercase → would have mis-tagged the manifest atom on the first batch run); 6
adapter tests updated; router still resolves (it lowercases for lookup). Watch confirmed: `POLYMARKET-PERP` records
honest-absence (BLOCKED-UPSTREAM), does not crash.

### 2026-06-29 — UAC defi MVP-exclusion: FIRST AGENT FAILED, REVERTED, RE-DOING

The first UAC defi sub-agent **misread `_STATIC_DEFI_VENUES`/`_SOLANA_DEFI_VENUES`** (claimed
static=AAVE/COMPOUND/UNISWAP/ FLASHBOTS, solana=JUPITER/ORCA/RAYDIUM/METEORA/LIFINITY/WHIRLPOOL) → wrong producible set
→ would have DROPPED the real LST venues (LIDO/ETHERFI/ETHENA/EIGENLAYER) from the denominator and ADDED non-producible
ones. QG passed because QG can't check denominator semantics. **All 4 UAC files reverted.** Authoritative producible set
**P = 55 venues** computed by RUNNING `_build_defi_venues()` in the IS venv (operator-confirmed shape: subgraph
AAVE_V3/COMPOUND_V3/DEX ∪ LST static ∪ Solana). Re-dispatched with P provided verbatim + a required self-verification;
orchestrator will INDEPENDENTLY re-verify the narrowed denominator == P before shipping (no trust in agent
self-verification). **`[UAC] DeFi MVP-exclusion` checkbox stays OPEN until that lands.**

### 2026-06-29 — UAC defi MVP-exclusion SHIPPED (`unified-api-contracts@6bcff215`) — PHASE 1 COMPLETE

Redo with authoritative P succeeded. **Orchestrator independently re-verified** (re-ran the import in the UAC venv, not
the agent's self-report): `VENUES_BY_ASSET_GROUP["defi"]` == the 55-venue producible set P EXACTLY (empty symmetric
diff), `MVP_SCOPE_CONFIG_VERSION` == 12, `ROCKETPOOL-ETHEREUM` removed from `DeFiMvpRule`, all remaining defi-MVP venues
⊆ P. Re-phase: 28 live→pipeline (LST roadmap, gas/governance/bridge, MORPHO multi-chain, MARGINFI/SOLEND), 33
pipeline→live (subgraph-backed AAVE_V3/COMPOUND_V3/UNISWAP_V3/BALANCER/CURVE/etc. multi-chain). UAC QG green.

**PHASE 1 DONE** — both repos shipped to LDR, both QG-green, all 5 AGs consolidated (cefi/tradfi/prediction set-equal to
UAC modulo named filters; defi denominator == IS-producible; sports two-registry EXEMPT). Two deliberate behaviour
deltas landed (cefi +2 perps; defi MVP v12). **Remaining (separate follow-ups, NOT this task):** the P2 defi drift-guard
test (hardening, captured above); **Phase 2** (adapter routing UAC-derived); the **Codex flip** (after Phase 2). Process
note: 1 of 6 implementation sub-agents (the first UAC-defi one) produced incorrect output (misread constants) and was
caught by orchestrator independent verification + revert — a reminder that data-correctness sub-agent output MUST be
independently verified against ground truth, never trusted on self-report.

### 2026-07-03 — PHASE 2 + CODEX FLIP SHIPPED — PLAN COMPLETE (Harsh session)

Four ship units, each `quality-gates.sh`-green before quickmerge:

1. **`unified-api-contracts@9eb5518`** — `registry/venue_adapter_keys.py`: `VENUE_TO_ADAPTER_KEY` (141 entries; the
   whole IS dict moved verbatim incl. load-bearing comments) + `NO_ADAPTER_YET` sentinel (9 deliberate entries: bare
   `COINBASE` expand-only alias, `YAHOO_FINANCE` source-as-venue, 7 MTDS-owned sports odds venues per Decision C) +
   `VENUE_PREFIX_TO_PROTOCOL`/`PROTOCOL_TO_ADAPTER_KEY` (moved from IS privates) + subgraph multi-chain expansion now
   computed inside UAC from its own `SUBGRAPH_IDS` + `VENUES_WITH_REFERENCE_ADAPTER` frozenset; 8-test gate suite.
   **Refactor invariant PROVEN before shipping**: non-sentinel map == old `CANONICAL_VENUE_TO_ADAPTER` with empty
   symmetric diff and zero value diffs (run in the IS venv against the live old dict).
2. **`unified-api-contracts@6516ed4`** — root re-export of `VENUE_TO_ADAPTER_KEY` + `VENUES_WITH_REFERENCE_ADAPTER`
   (discovered requirement: UTL's codex gate bans `unified_api_contracts.registry` deep imports at max=0, so the UTL
   consumer needs the top-level surface).
3. **`unified-trading-library@5a83484`** — `validate_venue_names()` now validates against UAC
   `VENUES_WITH_REFERENCE_ADAPTER` via a hard top-level import. Deletes the optional
   `instruments_service.reference_data` sibling import (which caught only `ModuleNotFoundError` and would have CRASHED
   on the IS symbol deletion wherever both packages are installed) AND the silent degrade path ("URDI not installed →
   skip validation") — venue-name preflight is now always enforced. Test suite rewritten against the REAL registry (old
   suite mocked a fictional one containing bare `BINANCE`/`COINBASE`, which never existed in the real dict); new
   sentinel-rejection test (`ODDS_API` must fail preflight).
4. **`instruments-service@8b7ce01`** — factory keeps ONLY key→class (`_ADAPTERS`); `_resolve_uac_adapter_key()` gives
   loud, distinct errors for unknown-to-UAC vs declared-adapterless (both keep the "No URDI adapter" prefix for existing
   `pytest.raises` matchers); `URDI_SUPPORTED_VENUES` = UAC `VENUES_WITH_REFERENCE_ADAPTER` (exactly equal to the
   pre-move set, since sentinels were never in the old dict); `urdi_reference_provider` classifies sentinel venues as
   UNSUPPORTED honest-absence exactly like before; 3 migration scripts switched to UAC `VENUE_PREFIX_TO_PROTOCOL`; 7
   test files + README migrated; NEW `tests/unit/test_adapter_routing_uac_invariant.py` (6 tests).
   `rg 'CANONICAL_VENUE_TO_ADAPTER'` = 0 hits repo-wide (gate asked "only the key→class table"; delivered full deletion,
   no shim). QG initially failed on the function-size cap (my raise branches pushed `get_adapter_for_canonical_venue` to
   204L > 200L) → extracted `_resolve_uac_adapter_key()` helper → green (93s).

**Codex flip (this commit):** consolidation doc PROPOSAL→IMPLEMENTED (moves 1+2 SHIPPED with evidence; move 3 remains
with `honest_coverage_v2_instrument_denominator_2026_06_28.md`); `instruments-service-as-ssot-for-mtds.md` gains the
"where the universe is DECLARED" block; `cursor-configs/CLAUDE.md` service one-liner updated.

**Discovered follow-up (captured as a todo in `instruments_mtds_subset_consistency_remediation_2026_06_17.md`):** MTDS
`cli/handlers/_instruments_metadata.py` maintains a hand-mirror of the venue-prefix→protocol map whose comment cites the
now-deleted IS `_SUBGRAPH_VENUE_PREFIX_TO_PROTOCOL` — it can now read UAC `VENUE_PREFIX_TO_PROTOCOL` (the exact
drift-class this plan exists to kill). Cosmetic residue noted, not actioned: `unified-trading-system-ui`
`lib/types/defi.ts:226` comment names the deleted dict — update on next touch of that file.

**PLAN COMPLETE** — all 14 todos ✅ (Phase 1: 7; success criteria: 3; Phase 2: 3; codex flip: 1). Status flipped
`active → completed`; archived per the 5-step ritual (no deferred `- [ ]` left in this plan; codex-alignment done this
session; `locked_by: NA`).
