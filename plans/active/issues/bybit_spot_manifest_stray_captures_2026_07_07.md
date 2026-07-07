---
doc_type: issue
title:
  BYBIT-SPOT manifest carries 135k rows in three anomalous states — mixed EMPTY / PERPETUAL instrument_type +
  spot-nonsense data_types (derivative_ticker / futures_chain / options_chain / perp_funding / liquidations)
summary:
  'Found 2026-07-07 while implementing cefi_layer1_denominator_gaps -006 (BYBIT-SPOT PERPETUAL itype-stamp fix). The
  scope of the BYBIT-SPOT captured-manifest defect is materially LARGER than that plan anticipates. Total 135,444 rows;
  by instrument_type: 81,659 EMPTY + 53,785 PERPETUAL; by data_type: 40,755 trades + 40,755 book_snapshot_5 + 13,350
  derivative_ticker + 13,350 futures_chain + 13,350 ohlcv_1m + 13,350 options_chain + 267 perp_funding + 267
  liquidations. NONE of derivative_ticker, futures_chain, options_chain, perp_funding, or liquidations is a valid
  data_type for a SPOT venue — those (~54k rows) look like stray captures from a different venue that leaked into the
  BYBIT-SPOT partition. The 81k EMPTY-instrument_type rows are ALSO anomalous — separately from the 53k PERPETUAL-stamp
  defect the -006 plan describes. A simple PERPETUAL→SPOT_PAIR relabel of the 53k subset would NOT close the Layer-1
  Gate ("manifest by_venue_instrument_type shows the split") because the other 82k rows are in states the plan does not
  model.'
status: open
nature: notes
asset_group: [cefi]
stage: [data, meta]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [honest-coverage, denominator-audit, layer-1, data-correctness, cefi, bybit-spot, manifest-surgery]
related:
  [
    cefi_layer1_denominator_gaps_2026_07_03.md,
    ../../../codex/02-data/honest-coverage-model.md,
    ../../../codex/02-data/availability-manifest-and-data-status.md,
    ../../../codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-07
parent_epic: infrastructure_master
priority: P1
source: cefi_layer1_denominator_gaps-006 implementation session (slot-8 planning)
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
model_tier: sonnet-doable
thinking_tier: high
estimate_class: research
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.8
last_updated: 2026-07-07
supersedes:
superseded_by:
depends_on: [cefi_layer1_denominator_gaps-006]
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> **NOTIFY-OPERATOR class finding (data-correctness).** Surfaced 2026-07-07 while shipping the forward-path fix for
> `cefi_layer1_denominator_gaps-006` (BYBIT-SPOT PERPETUAL itype-stamp) in `market-tick-data-service`. The forward path
> is fixed (no NEW mis-stamps); the state of ALREADY-captured BYBIT-SPOT rows in the manifest is worse than that plan's
> corrective-relabel step models.

## What I found

Ran `measure_honest_coverage._read_manifest("cefi")` against the pinned-primary consolidated manifest
(`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, 7,219,598 rows + secondary
4,115,773 → merged 11,125,247). Filtered to `venue == "BYBIT-SPOT"`:

```
total BYBIT-SPOT rows: 135,444
by instrument_type: {'': 81,659, 'PERPETUAL': 53,785}
by data_type:
  trades:             40,755
  book_snapshot_5:    40,755
  derivative_ticker:  13,350
  futures_chain:      13,350
  ohlcv_1m:           13,350
  options_chain:      13,350
  perp_funding:          267
  liquidations:          267
```

Three anomalies stack:

1. **The plan's PERPETUAL-stamp defect (~53k rows).** Root-caused in `market-tick-data-service`:
   `TardisAdapter._classify_row_instrument_type` at line 321 lacked `"BYBIT-SPOT"` in its SPOT-venue set, so BYBIT-SPOT
   rows arriving via the `bybit-spot` Tardis exchange fell through to `return InstrumentType.PERPETUAL`. Symmetrical gap
   in `symbol_rules._VENUE_INSTRUMENT_TYPE` (bare `"BYBIT": "perpetual"` but no `"BYBIT-SPOT"` entry). BOTH fixed on the
   forward path by the -006 code shipping in this session — regression-tested via
   `test_classify_row_instrument_type_option_future_perp_spot`.

2. **~82k rows with EMPTY `instrument_type`.** Not modeled by the -006 plan. Distinct from the PERPETUAL subset — these
   rows carry `instrument_type=""` in the manifest. Root cause unknown — the writer's `_resolve_instrument_type_column`
   at `engine/orchestrator/partitioned_writer.py:244` normalises an existing `instrument_type` column via
   `.str.lower()`, so an EMPTY string in the manifest means either (a) the source DataFrame carried `instrument_type=""`
   (writer stamped it that way) or (b) the manifest _consolidator_ is dropping the field for some subset. Needs
   diagnosis before any relabel.

3. **Spot-nonsense data_types on ~54k rows.** BYBIT-SPOT is a canonical SPOT venue — its valid data_types are `trades`
   and `book_snapshot_5` (per `VENUE_DATA_TYPE_CAPABILITIES["BYBIT-SPOT"]` which is CURRENTLY empty per the
   cefi_layer1_denominator_gaps issue doc). But the manifest holds ~13,350 rows each of `derivative_ticker`,
   `futures_chain`, `options_chain`, `ohlcv_1m` plus 267 each of `perp_funding` and `liquidations` under
   `venue=BYBIT-SPOT`. **None of these data_types make sense for a spot venue.** They look like stray captures from
   BYBIT-FUTURES / BYBIT (bare) that leaked into the BYBIT-SPOT partition — possibly via the same
   canonicalisation-venue-map bug from a related pipeline. Not modeled by -006's
   `by_venue_instrument_type shows the split` Gate.

## Why it matters

- **Data-pipeline-correctness HARD RULE** — silent placeholders / mis-routed captures are the exact class of defect
  Honest Coverage v2 exists to kill; leaving 82k rows in an unknown state (EMPTY instrument_type) and 54k rows under
  nonsense data_types keeps cefi Layer-2 accounting dishonest for BYBIT-SPOT.
- **-006's plan Gate** says "manifest `by_venue_instrument_type` shows the split" — with 82k rows still in
  EMPTY-instrument_type after any PERPETUAL→SPOT_PAIR relabel, the Gate is NOT satisfied without addressing the other
  two subsets. A partial corrective-relabel would leave a misleading half-fix.
- **Worker-guard "stop-on-surprise"** (from the -006 plan header) — a corrective touching more rows than expected or a
  measure moving the wrong direction requires STOP + raise, not push-through. This finding is exactly that class.
- **Downstream measure drift** — the re-measure task (`cefi_layer1_denominator_gaps-005`) currently PARKED with
  KALSHI-PERP purge as one prereq would land a % that is either misleading (if BYBIT-SPOT stays in
  EMPTY/PERPETUAL/nonsense states) or double-counted (if the nonsense-data_type rows are also on BYBIT-FUTURES / BYBIT
  under the same shard atom).

## Recommended decision

Ship the -006 forward-path fix as-is (map entries + regression tests + issue doc — `docs(plans):` cross-repo PM flip +
`feat(...)` MTDS quickmerge). Handle the three ALREADY-captured subsets as three follow-up sub-todos in this issue doc,
in order (each a machine-encoded backlog task the orchestrator will dispatch to a data_engineering worker). Do NOT
attempt the corrective-relabel in the -006 session because (a) the scope is materially different from what the -006 plan
describes and (b) each subset needs its own diagnosis before mutation.

## Todos

- [ ] [SCRIPT] P1. **Diagnose the ~82k BYBIT-SPOT rows with EMPTY `instrument_type`.** Trace: (i) which
      writer/consolidator produced them; (ii) which asset_group they land under in the raw parquet vs the consolidated
      manifest; (iii) whether their `symbol` values match spot-symbol patterns. Read-only — no manifest mutation.
      Deliverable: a diagnosis appended to this issue doc naming the root writer + whether the EMPTY-string is a
      manifest projection artifact or a real writer bug (repo: market-tick-data-service).
- [ ] [SCRIPT] P1. **Diagnose the ~54k BYBIT-SPOT rows under spot-nonsense data_types** (derivative_ticker /
      futures_chain / options_chain / ohlcv_1m / perp_funding / liquidations). Two candidate root causes: (i)
      canonical-venue-map bug that routed BYBIT-FUTURES rows to `venue=BYBIT-SPOT`; (ii) writer that stamps
      `venue=BYBIT-SPOT` on a wrong shard. Read-only — cross-reference the rows' `symbol` values + GCS paths + capture
      windows against the BYBIT-FUTURES manifest to see whether these are duplicates of BYBIT-FUTURES captures.
      Deliverable: a diagnosis + a smoke-first delete/re-route plan appended here (repo: market-tick-data-service).
- [ ] [SCRIPT] P1. **Once (a) + (b) are diagnosed, ship a corrective-relabel script for the ~53k PERPETUAL-stamp
      subset** (the class the -006 plan originally described). Smoke-first: relabel ONE shard, verify manifest split via
      `by_venue_instrument_type`, then scale. Gate: BYBIT-SPOT rows carry SPOT_PAIR; manifest `by_venue_instrument_type`
      shows the split. Depends on the two diagnostic todos above so we do not compound existing wrong labels (repo:
      market-tick-data-service).
- [ ] [CONFIG] P2. **Populate `VENUE_DATA_TYPE_CAPABILITIES["BYBIT-SPOT"]` in UAC** with `trades` + `book_snapshot_5`
      (SPOT venue capabilities) so the cefi Layer-1 EXPECTED denominator includes BYBIT-SPOT instead of carve-out-1
      excluding it. Currently empty — matches the plan's separate BYBIT-SPOT capability-gap observation. Cross-repo
      depends on the corrective-relabel landing so the Layer-1 tuple appears with real captured data (repo:
      unified-api-contracts).

## Progress Log

- **2026-07-07** — Filed by slot-8 planning during the -006 implementation session. Forward-path code fix shipped in the
  -006 quickmerge (MTDS `symbol_rules._VENUE_INSTRUMENT_TYPE` + `TardisAdapter._classify_row_instrument_type`
  - `test_tardis_canonical_output.py` regression). The four follow-on todos above are the tracked-work outputs; the
    corrective-relabel step from the -006 plan text is deferred pending the diagnosis todos so we do not push through a
    partial fix that leaves the other 82k EMPTY rows + 54k spot-nonsense-data_type rows unaddressed.
