---
doc_type: issue
title: Honest-Coverage Layer-1 — UAC↔writer expected-matrix reconciliation (strays + carve-out contradiction)
summary:
  "Surfaced by the Honest-Coverage-v2 CK3 certification (2026-06-29): the Layer-1 enumeration-completeness check found
  high stray counts (writer captures (venue,instrument_type,data_type) combos UAC's per-itype validity matrix does not
  sanction) plus one writer↔UAC carve-out contradiction. These make Layer-1 completeness % an UPPER bound for the
  affected nodes. Resolve via owner-verified UAC matrix expansion + writer canonicalisation so EXPECTED and ENUMERATED
  agree on the could-exist universe."
status: resolved
nature: notes
asset_group: [cross-cutting]
stage: [data, meta]
repos: [unified-api-contracts, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [honest-coverage, denominator-audit, uac, writer, data-correctness, ssot-contradiction]
related:
  [
    ../honest_coverage_v2_opus_checkpoints_2026_06_28.md,
    ../honest_coverage_v2_instrument_denominator_2026_06_28.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-06-29
parent_epic: infrastructure_master
priority: P1
source: honest_coverage_v2_opus_checkpoints_2026_06_28.md
assigned_vm: NA
resolved_by:
  harsh session 2026-07-03 — unified-api-contracts@59de09d6 + instruments-service@3bb7acd + ASTER manifest purge +
  re-measure (cefi L1 65.91→79.55)
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
last_updated: 2026-07-03
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since: 2026-05-21
---

> **Source.** Discovered during Honest-Coverage-v2 **CK3** certification (Opus, 2026-06-29). The Layer-1
> enumeration-completeness check (`instruments-service/scripts/check_enumeration_completeness.py`, run
> `coverage_v3.json` 06:00 UTC) aligned EXPECTED (UAC vocabulary) ↔ ENUMERATED (writer/manifest vocabulary) and, after
> removing all dialect artifacts, still found **high stray counts** (enumerated-but-not-expected): cefi 118, defi 131,
> tradfi 52, sports 24, prediction 17. Strays mean the writer captures real `(venue, instrument_type, data_type)` combos
> that UAC's per-itype validity matrix does not sanction → for those nodes EXPECTED is too small → Layer-1 completeness
> is **over-reported** (an upper bound). This is a cross-repo SSOT gap, not a measurement bug. Codex SSOT:
> `/codex/02-data/honest-coverage-model.md` § "CK3 — final integrated certification" (caveat).

## OPERATOR DECISIONS — RESOLVED 2026-06-29 (HANDOVER-READY; no open operator gates)

Every cross-repo decision is locked. A handover executor can implement with NO further operator input. Net engineering
outcome: **zero UAC expected-matrix additions** — all strays resolve via cutoffs, over-seed carve-outs, or grain
roll-up.

| #   | Decision area                       | Operator verdict                                                                                                                                       | Engineering action (where)                                                                              |
| --- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| 1   | UAC strays — billing cutoffs        | Do NOT add CME `mbp_10` (Databento L2, 30d-free), CME `ohlcv_24h` (non-Databento/VIX)                                                                  | No change; they're deliberate cutoffs. SSOT `tradfi-databento-sourcing-ssot.md`                         |
| 2   | UAC strays — out-of-MVP             | MVP scope is correct; do NOT add sports non-MVP bookmakers, POLYMARKET per-underlying partitions                                                       | No change; stays strays (warnings)                                                                      |
| 3   | defi `a_token` strays               | **NO UAC add** — grain mismatch (risk_params/lending_indices already declared; utilization=column; oracle_prices not collected by AAVE)                | Roll `a_token`/`debt_token`→`lending` in enumerator/producer                                            |
| 4   | defi instrument_type grain          | **Roll fine grains → UAC canonical `lending`**                                                                                                         | enumerator/`check_enumeration_completeness.py` normalisation                                            |
| 5   | defi expected scope                 | **Curated per-protocol `PROTOCOL_CAPABILITIES.data_types`, narrowed to IS-producible (Decision-D)** — NOT block+ohlcv-only, NOT the broad 25-type list | already how `valid_data_types_for_instrument_type` builds it; defi denominator narrow per registry plan |
| 6   | cefi venue-suffix (OKX-SWAP vs OKX) | Registry-plan **Decision-A** `expand_cefi_tardis_endpoints()` grain-adapter                                                                            | honest-coverage EXPECTED consumes the consolidated producer → suffixes match                            |
| 7   | ASTER carve-out contradiction       | UAC correct; enumerator over-seeds                                                                                                                     | Apply `VENUE_DATA_TYPE_CAPABILITIES` carve-out in enumerator seeding                                    |
| 8   | Sequencing                          | Land all enumerator fixes WITHIN the active `instrument_universe_registry_consolidation` plan's enumerator work (same file) — no parallel agent        | —                                                                                                       |

## The three stray classes (with evidence)

1. **UAC per-itype matrix under-specifies real captured data_types (UAC fix — owner-verified).** The writer genuinely
   delivers data_types absent from `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE` / the per-protocol/league validity:
   - tradfi `CME` `futures_chain` → `mbp_10`, `ohlcv_24h`, `tbbo` (Databento delivers these; UAC's futures_chain set is
     `{trades, ohlcv_1s, ohlcv_1m, tbbo}`). Also `CME` `combo`/`futures` `trades`.
   - prediction `KALSHI` `prediction_market` → `book_snapshot_5` (UAC per-itype set omits it though
     `DATA_TYPES_BY_ASSET_GROUP["prediction"]` lists it).
   - defi `AAVE_V3` `a_token` → `oracle_prices`/`rate_indices`/`risk_params`/`utilization` (PROTOCOL_CAPABILITIES for
     AAVE_V3 under-declares the `a_token` instrument_type grain).
   - Many UAC matrix entries are already marked `# UNCERTAIN — owner verify` — this finding is the verification trigger.

2. **Writer↔UAC carve-out contradiction (writer OR UAC fix).** cefi `ASTER` `perpetual` → `book_snapshot_5`,
   `liquidations` appear in the manifest as strays, but UAC declares ASTER cannot produce them (absent from
   `VENUE_DATA_TYPE_CAPABILITIES["ASTER"]`). Either the writer is emitting rows for capabilities ASTER lacks (writer
   bug) or UAC's ASTER carve-out is wrong (UAC fix). Also `ASTER perpetual futures_chain` (a perpetual carrying a
   futures_chain data_type) is suspect. Resolve which side is correct.

3. **Out-of-MVP / finer-grain strays — correctly NOT holes (no fix, classification only).** sports non-MVP bookmaker
   venues (BETMGM/BETONLINEAG/BETRIVERS/…) `odds` `trades`; POLYMARKET per-underlying partitions (btc/eth/crude_oil/…)
   `prediction_trades`; KALSHI `book_snapshot_5` partitions. These are real captured data outside the UAC MVP scope or
   at a finer grain — the check already classifies them as strays (warnings), not holes. Confirm the MVP venue set is
   the intended scope; no denominator change required.

## Secondary findings (same provenance)

- **SSOT-placement: `_VENUE_INSTRUMENT_TYPE` replicated into instruments-service.** `check_enumeration_completeness.py`
  replicates an MTDS venue→instrument_type map (with citation, because cross-repo import is banned). A replicated SSOT
  drifts. Promote the canonical venue→instrument_type map into **UAC** (the shared contract lib both IS and MTDS may
  import) and delete the replica.
- **cefi venue-suffix grain (measurement refinement).** cefi perps/spot are captured under venue-suffix variants
  (`OKX-SWAP` vs `OKX`, `BYBIT-SPOT` vs `BYBIT`), so some cefi "holes" are captured-under-suffix false holes. Both forms
  are legitimately in UAC; decide whether the writer should emit the canonical bare venue, or the check should fold
  suffixes. Until resolved, a subset of the 15 cefi real-holes are false.

## Todos

- [x] [INVESTIGATE] P1. Triage every stray class against billing/MVP/owner rules. ✅ DONE 2026-06-29 — verdict per class
      in the "OPERATOR DECISIONS — RESOLVED" table above (billing cutoff / out-of-MVP / over-seed carve-out / grain
      roll-up). Net: zero UAC additions warranted.
- [x] [CODE] P1. **NO UAC additions — the a_token strays are a GRAIN mismatch, not missing data (re-verified +
      operator-confirmed 2026-06-29).** ✅ DONE 2026-07-03 — `instruments-service@3bb7acd` (see Progress Log): the
      Layer-1 canon (`check_enumeration_completeness.py`) folds defi `a_token`/`debt_token`/`liquidation` → `lending`
      and defi `rate_indices` → `lending_indices`; real-data-at-wrong-grain strays now MATCH their expected lending
      cells (defi strays 133→128); the residual a_token-displayed strays are the adjudicated over-seed/column artifacts
      (`oracle_prices`, `utilization`) — correctly visible warnings, per this todo NO UAC change. Earlier "add a*token
      protocol-state" was OVERTURNED on inspection of `capability_declarations/_defi.py`: `risk_params` +
      `lending_indices` are ALREADY declared in `_LENDING_DATA=[lending_indices,liquidations,risk_params]`;
      `rate_indices` = `lending_indices` (non-canonical name); `utilization` is a COLUMN of lending_indices, not a
      data_type (code comment l.335); AAVE's `mtds_operations` do NOT collect `oracle_prices` (over-seed). Root cause:
      writer emits fine `a_token`/`debt_token`/`liquidation` grains; UAC models lending at the coarser `lending`
      instrument_type. **FIX (operator: "Roll a_token/debt_token → lending"):** normalise the fine grains to UAC's
      canonical `lending` instrument_type in the enumerator/writer (same home as the ASTER carve-out —
      `enumerate_expected_universe.py` / the consolidated producer); NO UAC change. The lending data_types are already
      declared. **Operator REJECTED all other adds:** CME `mbp_10` (Databento L2 30d-free billing cutoff — not in CME
      `expected_coverage`), CME `ohlcv_24h` (not a Databento schema — VIX/Barchart), KALSHI `book_snapshot_5`, defi
      `pool     swaps_ohlcv*\*`. Net: **zero UAC expected-matrix additions**; every stray resolves via billing/MVP
      cutoff, enumerator over-seed carve-out, or grain roll-up. Billing SSOT:
      `/codex/02-data/tradfi-databento-sourcing-ssot.md` § schema-allowlist.
- [x] [CODE] P1. Resolve the class-2 ASTER carve-out contradiction. ✅ DONE 2026-07-03 — (a) enumerator fix
      `instruments-service@3bb7acd`: `_row_data_types` applies the `VENUE_DATA_TYPE_CAPABILITIES` carve-out at seeding
      (CEFI ONLY — tradfi deliberately ungated: its capability entries are the OHLCV-window MVP declaration, and the
      operator-ratified T-OLD-2b test pins protect chain-trades/earnings seeding; Decision-1 keeps tradfi strays as
      deliberate cutoffs); regression tests in `test_enumerate_expected_universe.py`. (b) live manifest purge
      `scripts/delete_aster_overseeded_capability_rows.py --apply` 2026-07-03 08:33–09:09 UTC: **17,282 rows deleted**
      (legacy canonical 13,223 = eu 6,954 + ec[EXPECTED_NO_SOURCE_DATA] 6,243 + af[VENUE_FETCH_FAILED] 26; prd
      enum-universe per-VM shard 4,056; legacy seed shard 3), backup-then-write (`.20260703-083335.bak.parquet`).
      Verified: ASTER book5/liquidations strays GONE from the 08:52 re-measure. The sequencing constraint (registry plan
      same-file) had cleared — that plan archived complete earlier today. **DIAGNOSED 2026-06-29 (Opus, from
      `coverage_v3.json`): UAC is CORRECT; the ENUMERATOR over-seeds.** ASTER PERPETUAL `book_snapshot_5` +
      `liquidations` are 100% `expected_unattempted` (3477 rows each; captured=0, empty_confirmed=0,
      attempted_failed=0), while ASTER `trades`/`derivative_ticker` show real captures (captured=180/899,
      empty=231051/230332). So nothing ever produced ASTER book5/liquidations — the rows exist only because
      `enumerate_expected_universe.py` seeded `expected_unattempted` for `(ASTER, perpetual, book5|liquidations)`,
      violating `VENUE_DATA_TYPE_CAPABILITIES["ASTER"]` (trades/derivative_ticker/perp_funding only — ASTER is a perp
      DEX with no orderbook-snapshot or liquidation feed). **FIX:** the enumerator must apply the same venue-capability
      carve-out the Layer-1 EXPECTED matrix applies — do NOT seed `expected_unattempted` for `(venue, itype, dt)` absent
      from `VENUE_DATA_TYPE_CAPABILITIES[venue]` (cefi/tradfi). **SEQUENCING:** this fix is IN
      `enumerate_expected_universe.py`, under active concurrent edit by the
      `instrument_universe_registry_consolidation_2026_06_29.md` plan (slot-4, last commit `a510db1` 2026-06-29) — land
      it WITHIN that plan's enumerator work to avoid a same-file collision, not as a separate parallel agent.
- [x] [CODE] P2. Promote the replicated `_VENUE_INSTRUMENT_TYPE` venue→itype map into UAC; delete the
      instruments-service replica. ✅ DONE 2026-07-03 — UAC `TRADFI_VENUE_INSTRUMENT_TYPES` added to
      `registry/market_data_categories.py` (`unified-api-contracts@59de09d6`, docstring cites the MTDS writer-side
      counterpart `symbol_rules._VENUE_INSTRUMENT_TYPE` + the itype-column overrides); IS replica `_TRADFI_VENUE_ITYPES`
      DELETED from the checker, which now imports the UAC symbol (`instruments-service@3bb7acd`).
- [x] [CODE] P2. Decide + implement the cefi venue-suffix policy (writer emits canonical venue, or the check folds
      suffixes); re-measure so cefi real-holes exclude captured-under-suffix false holes. ✅ DONE 2026-07-03 —
      implemented as **the check folds suffixes** (`_CEFI_VENUE_FOLD` in the Layer-1 canon: OKX-SPOT/-SWAP/-FUTURES→OKX,
      COINBASE-SPOT→COINBASE, BYBIT-FUTURES→BYBIT, legacy OKEX\*/CRYPTOFACILITIES/BITFINEX-DERIVATIVES/
      COINBASE-INTERNATIONAL → canonical; UAC-canonical suffixed venues like BYBIT-SPOT/KRAKEN-FUTURES deliberately NOT
      folded). Decision-6's "EXPECTED consumes the consolidated producer" was implemented via this todo's sanctioned
      fold alternative: re-keying the EXPECTED axis to split-grain venues would require re-homing the
      capability/MVP/bundle authorities (all keyed bare in UAC) — a denominator redesign, not a dialect fix. Ground
      truth confirmed no writer-side change needed: the legacy dialect venues carry only blank-itype rows (already
      outside Layer-1). Effect: 6 of cefi's 15 holes were captured-under-suffix false holes → GONE.
- [x] [SCRIPT] P2. Re-run `measure_honest_coverage.py --asset-group all` after the above; the certified Layer-1 numbers
      in `/codex/02-data/honest-coverage-model.md` CK3 table will tighten — update them. ✅ DONE 2026-07-03 08:52 UTC —
      **cefi Layer-1 65.91% → 79.55%** (35/44, missing 15→9 — all 9 remaining are REAL defects: BITFINEX/KRAKEN-FUTURES
      `future` grain, BYBIT spot writer mis-stamp, OKX options_chain never enumerated); defi strays 133→128 (grain
      folds); ASTER strays gone; tradfi/sports/prediction unchanged (their strays are adjudicated cutoffs/out-of-MVP).
      CK3 table updated in the codex SSOT. NOTE: an intermediate measure flagged a harness fragility (freshest-bucket
      primary selection flips after manifest surgery — mitigated by a prd metadata bump; hardening todo filed in
      `cefi_layer1_denominator_gaps_2026_07_03.md`).

## Progress Log

- **2026-06-29** — Filed from CK3 certification. The Honest-Coverage-v2 MODEL + MEASUREMENT are certified honest; this
  issue is the follow-up reconciliation that tightens the per-node completeness % (currently upper bounds where UAC
  under-specifies). Not blocking the CK3 sign-off — the model correctly + visibly surfaces these as strays.
- **2026-07-03 — ALL 5 TODOS DONE, issue RESOLVED (Harsh session).** Ships: `unified-api-contracts@59de09d6`
  (TRADFI_VENUE_INSTRUMENT_TYPES promotion), `instruments-service@3bb7acd` (Layer-1 canon: `_CEFI_VENUE_FOLD`
  suffix/dialect fold, defi lending grain roll-up + `rate_indices` fold, UAC tradfi-map import; enumerator
  `_row_data_types` venue-capability carve-out CEFI-ONLY; `delete_aster_overseeded_capability_rows.py` one-off + pinning
  tests). Live surgery: 17,282 ASTER book5/liquidations rows purged from both cefi manifest buckets (backups
  `.20260703-083335.bak.parquet`). Re-measure 08:52 UTC: **cefi Layer-1 65.91% → 79.55%** (missing 15→9, all real);
  ASTER strays gone; defi strays 133→128; codex CK3 table updated. Scope judgments recorded for review: (1) Decision-6
  implemented as the todo's check-folds-suffixes option (re-keying EXPECTED to split-grain venues would re-home the
  bare-keyed capability/MVP/bundle authorities — denominator redesign); (2) the enumerator carve-out is CEFI-ONLY —
  blanket tradfi gating broke the operator-ratified T-OLD-2b pins (tradfi capability entries are the OHLCV-window
  declaration, not full capability; Decision-1 keeps those strays deliberate). Two NEW findings filed in
  `cefi_layer1_denominator_gaps_2026_07_03.md` (NOTIFY-OPERATOR): cefi expected-matrix omits whole gate-blind venues
  (Tardis-map + capability-table gaps; the 44-tuple denominator under-counts the real universe), and the measure's
  freshest-bucket primary selection is fragile to manifest surgery (observed live; mitigated with a prd metadata bump).
  </content>
