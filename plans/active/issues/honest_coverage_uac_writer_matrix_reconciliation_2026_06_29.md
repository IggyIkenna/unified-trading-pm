---
doc_type: plan
title: "Honest-Coverage Layer-1 — UAC↔writer expected-matrix reconciliation (strays + carve-out contradiction)"
summary:
  "Surfaced by the Honest-Coverage-v2 CK3 certification (2026-06-29): the Layer-1 enumeration-completeness check found
  high stray counts (writer captures (venue,instrument_type,data_type) combos UAC's per-itype validity matrix does not
  sanction) plus one writer↔UAC carve-out contradiction. These make Layer-1 completeness % an UPPER bound for the
  affected nodes. Resolve via owner-verified UAC matrix expansion + writer canonicalisation so EXPECTED and ENUMERATED
  agree on the could-exist universe."
status: active
nature: investigation
stage: [data-ingestion, meta]
repos: [unified-api-contracts, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [honest-coverage, denominator-audit, uac, writer, data-correctness, ssot-contradiction]
related:
  [
    ../honest_coverage_v2_opus_checkpoints_2026_06_28.md,
    ../honest_coverage_v2_instrument_denominator_2026_06_28.md,
    ../../../codex/02-data/honest-coverage-model.md,
  ]
created: 2026-06-29
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
last_updated: 2026-06-29
supersedes:
superseded_by:
depends_on:
source: honest_coverage_v2_opus_checkpoints_2026_06_28.md
assigned_role: data_engineering
drift_direction: advance-code
asset_group: cross-asset
---

> **Source.** Discovered during Honest-Coverage-v2 **CK3** certification (Opus, 2026-06-29). The Layer-1
> enumeration-completeness check (`instruments-service/scripts/check_enumeration_completeness.py`, run
> `coverage_v3.json` 06:00 UTC) aligned EXPECTED (UAC vocabulary) ↔ ENUMERATED (writer/manifest vocabulary) and, after
> removing all dialect artifacts, still found **high stray counts** (enumerated-but-not-expected): cefi 118, defi 131,
> tradfi 52, sports 24, prediction 17. Strays mean the writer captures real `(venue, instrument_type, data_type)` combos
> that UAC's per-itype validity matrix does not sanction → for those nodes EXPECTED is too small → Layer-1 completeness
> is **over-reported** (an upper bound). This is a cross-repo SSOT gap, not a measurement bug. Codex SSOT:
> `codex/02-data/honest-coverage-model.md` § "CK3 — final integrated certification" (caveat).

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

- [ ] [INVESTIGATE] P1. Triage every stray class above against the venue/itype owners; produce the keep-in-EXPECTED vs
      writer-fix vs out-of-scope verdict per stray (use the `--diagnose-layer1` per-AG samples in `coverage_v3.json`
      `layer_1.by_asset_group[ag].diagnostics.enumerated_only_samples`).
- [ ] [CODE] P1. **UAC**: expand `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE` / per-protocol / per-venue validity for
      the class-1 strays that owners confirm are genuinely expected (CME futures_chain mbp_10/ohlcv_24h/tbbo; KALSHI
      book_snapshot_5; AAVE a_token data_types; clear the `UNCERTAIN — owner verify` entries touched).
- [ ] [CODE] P1. Resolve the class-2 ASTER carve-out contradiction — fix the writer to honour the carve-out, OR correct
      UAC's `VENUE_DATA_TYPE_CAPABILITIES["ASTER"]` if ASTER does produce book5/liquidations.
- [ ] [CODE] P2. Promote the replicated `_VENUE_INSTRUMENT_TYPE` venue→itype map into UAC; delete the
      instruments-service replica.
- [ ] [CODE] P2. Decide + implement the cefi venue-suffix policy (writer emits canonical venue, or the check folds
      suffixes); re-measure so cefi real-holes exclude captured-under-suffix false holes.
- [ ] [SCRIPT] P2. Re-run `measure_honest_coverage.py --asset-group all` after the above; the certified Layer-1 numbers
      in `codex/02-data/honest-coverage-model.md` CK3 table will tighten — update them.

## Progress Log

- **2026-06-29** — Filed from CK3 certification. The Honest-Coverage-v2 MODEL + MEASUREMENT are certified honest; this
  issue is the follow-up reconciliation that tightens the per-node completeness % (currently upper bounds where UAC
  under-specifies). Not blocking the CK3 sign-off — the model correctly + visibly surfaces these as strays. </content>
