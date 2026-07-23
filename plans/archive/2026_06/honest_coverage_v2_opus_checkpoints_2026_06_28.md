---
doc_type: plan
title: Honest Coverage v2 — Opus checkpoints (cross-repo schema design + Layer-1 matrix + final certification)
summary:
  "The few opus-required checkpoints of Honest-Coverage-v2: design the coverage.json v2 schema + two-layer/gate
  semantics (cross-repo UAC + IS + UTL manifest + deployment simultaneously), design the Layer-1
  enumeration-completeness matrix (catalogue × UAC expected-data-types), and the final integrated certification that the
  honest-100% semantics hold. Everything else is the sonnet-doable companion plan."
status: complete
nature: design
asset_group: [cross-cutting]
stage: [data, meta]
repos: [unified-api-contracts, instruments-service, unified-trading-library, deployment-service]
scope: [engineer, admin]
tags: [honest-coverage, denominator-audit, architecture, cross-repo, opus-checkpoint, data-correctness]
related:
  [
    /plans/archive/2026_07/honest_coverage_v2_instrument_denominator_2026_06_28.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    /codex/06-coding-standards/model-tier-selection.md,
  ]
created: 2026-06-28
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
estimate_class: design
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.2
last_updated: 2026-06-28
locked_by: live-defi-rollout
locked_since: 2026-06-28
supersedes:
superseded_by:
depends_on:
source:
model_tier: opus-required
thinking_tier: high
assigned_role: data_engineering
drift_direction: advance-code
---

> **✅ ARCHIVED — 2026-06-30 — TRULY-DONE.** All 3 Opus checkpoints shipped; schema + enumeration matrix written to
> `/codex/02-data/honest-coverage-model.md` (the SSOT), CK3 certified (`instruments-service@051e5a8`). The Sonnet
> companion `honest_coverage_v2_instrument_denominator` stays active. Content-verified (§6 B2.2 of
> `plan_issue_epic_consolidation_2026_06_30`).

> **HUMAN PLAN (`assigned_vm: NA`)** — operator-driven. The **Opus** half of Honest-Coverage-v2; the sonnet-doable
> mechanical work is `honest_coverage_v2_instrument_denominator_2026_06_28.md`.
>
> **🤖 MODEL TIER: `opus-required` (thinking: high).** These checkpoints are cross-repo architecture — they require
> holding UAC (expected-data-types) + IS (catalogue/enumerate/measure) + UTL (manifest writer) + deployment
> (status/gate) in context simultaneously, which is the SSOT's opus-required bar. **A Sonnet agent must NOT execute
> these.** **BOOT GATE (run FIRST, STOP on non-zero):**
> `python3 scripts/plans/audit_model_tier.py --assert plans/active/honest_coverage_v2_opus_checkpoints_2026_06_28.md` —
> exits 1 if a non-Opus agent reaches this plan (SSOT: `/codex/06-coding-standards/model-tier-selection.md`).

## Ordering

`CK1 + CK2` (design, Opus) → sonnet companion plan implements + runs the fixes → `CK3` (certification, Opus). The
companion plan's `[OPUS-CK→companion]` items are blocked on CK1/CK2 output.

## Checkpoints

- [x] [AGENT] CK1 P0. **Design the Honest-Coverage-v2 `coverage.json` schema + two-layer/gate semantics.** Decide the
      structure that carries: Layer-1 (instrument coverage) + Layer-2 (download coverage), both the day-by-day and
      shard-breakdown views, and the drill-down/roll-up tree
      (`asset_group → venue → instrument_type → data_type →     day`), plus the instrument-gates-download flag. Requires
      reconciling UAC `DATA_TYPES_BY_ASSET_GROUP` / `get_expected_data_types_for_venue`, the IS catalogue grain, the UTL
      manifest shard atom, and the deployment data-status/gate consumer **at once**. Output = the schema spec the sonnet
      plan implements. `Gate:` spec written + reviewed against all four repos' contracts. ✅ unified-trading-pm —
      authoritative schema spec written to `/codex/02-data/honest-coverage-model.md` § "coverage.json v2 schema (CK1)" +
      "Layer-2 read grain". Reconciled vs ground-truth from all 4 repos: **decisive correction** — schema made ADDITIVE
      (live consumers deployment-api `/api/data-status/honest-coverage` + deployment-ui `HonestCoverageCard`/
      `HonestCoverageResponse` + pinned route test read top-level `by_asset_group`/`by_venue`/`by_venue_data_type` + 6
      per-cell fields VERBATIM → v2 keeps them, adds `layer_1`/`by_venue_instrument_type[_data_type]`/`by_day` + gate
      fields as OPTIONAL); manifest `instrument_type` confirmed a real lowercase column (v1 harness omitted it); shard
      atom + `CaptureStatus` + `EmptyConfirmedReason` pinned to UTL/UAC source.

- [x] [AGENT] CK2 P0. **Design the Layer-1 enumeration-completeness matrix.** Define exactly what "should exist" means
      per (venue, instrument_type, data_type) = IS catalogue (within listing window) × UAC expected-data-types,
      INCLUDING the structural honest-absence carve-outs (e.g. Deribit options=options_chain-only, ASTER historical
      book5 absent, A_LEAGUE×footystats) so a legitimate absence is not counted as a denominator hole. Output = the
      matrix spec + carve-out list the sonnet `enumerate`/`measure` impl asserts against. `Gate:` matrix spec enumerates
      every in-MVP (venue, instrument_type, data_type) with its expected/absent verdict. ✅ unified-trading-pm — matrix
      spec + carve-out table written to `/codex/02-data/honest-coverage-model.md` § "Layer-1 enumeration-completeness
      matrix (CK2)". **Decisive grain correction**: expected matrix keyed by
      `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE[(ag, instrument_type)]` (NOT broad `DATA_TYPES_BY_ASSET_GROUP`, a
      superset that over-counts) × `VENUE_DATA_TYPE_CAPABILITIES` (carve-outs + listing windows) ×
      `FUTURE_BUNDLE_VENUES` (bundle grain) × `is_mvp(...)`. `(cefi,option)=∅` → options roll up to `options_chain`
      bundle (`data_type=trades`), so the real expected tuple is `(DERIBIT, options_chain, trades)` NOT
      `(DERIBIT, OPTION, options_chain)`. Carve-outs SOURCED FROM UAC (not hardcoded); known examples tabulated as the
      impl's regression assertions. Deribit gap classified as a real Layer-1 hole (not a carve-out).

- [x] [AGENT] CK3 P0. **Final integrated certification (after the sonnet impl + fixes + re-measure).** Hold the whole
      pipeline in context and certify: Layer-1 gates Layer-2; both views are correct; no silent denominator holes; the
      post-fix numbers are trustworthy (stale-bucket + manifest-split + instrument_type + VENUE_FETCH_FAILED fixes all
      verified). Sign off the codex SSOT as the standing definition. `Gate:` a written certification + the codex doc
      flipped to the authoritative v2 model. ✅ **CERTIFIED** unified-trading-pm@<this commit> — certification written
      to `/codex/02-data/honest-coverage-model.md` § "CK3 — final integrated certification"; codex flipped to
      authoritative. Evidence: instruments-service@051e5a8 (CI v2 GREEN #688, 38 tests), live `coverage_v3.json`
      2026-06-29 06:00 UTC. Verified: Layer-1 gates Layer-2 (all 5 AGs INCOMPLETE→`instrument_gates_download=true`);
      empty-denominator fails CLOSED (UNDEFINED, caught the defi EXPECTED=0); both views (`by_day` +
      `by_venue_instrument_type_data_type`) + schema back-compat; EXPECTED↔ENUMERATED vocabulary aligned (retired the
      defi/sports 0% artifacts). Certified Layer-1: cefi 65.91% | defi 69.44% | tradfi 51.43% | sports 30.77% |
      prediction 66.67%. **Caveat (documented):** completeness % is an UPPER bound where UAC under-specifies — strays
      surfaced a UAC↔writer matrix gap tracked in
      `issues/honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md` (not blocking — model honestly surfaces
      them as strays).

## Progress Log

- **2026-06-28** — Created as the Opus half of the Honest-Coverage-v2 split (operator: "sonnet-capable items with a few
  opus checkpoints, failing if the model doesn't match"). Hard-fail tier gate wired via
  `scripts/plans/audit_model_tier.py --assert`.
- **2026-06-29 tick-1 (Opus `/autonomous`)** — Boot gate passed (Opus 4.8). Fanned out 4 read-only Explore agents (one
  per repo: UAC / IS / UTL-manifest / deployment) to gather ground-truth contracts. Findings: (UAC) real Layer-1 grain
  authority = `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE` × `VENUE_DATA_TYPE_CAPABILITIES` × `FUTURE_BUNDLE_VENUES` ×
  `is_mvp` — NOT the broad `DATA_TYPES_BY_ASSET_GROUP`; `(cefi,option)=∅` bundle roll-up. (IS)
  `enumerate_expected_universe.py` already has a v2 path (`_enumerate_v2_*` + `_rollup_bundle_grain`);
  `measure_honest_coverage.py` exists but reads only `[capture_status,venue,data_type,date]` — no instrument_type, no
  Layer-1, no day-by-day. (UTL) manifest v9, `instrument_type` is a real lowercase column, shard atom +
  `CaptureStatus`/`EmptyConfirmedReason` pinned. (deployment) coverage.json has LIVE consumers → schema is constrained,
  not greenfield. **CK1 + CK2 authored** into `/codex/02-data/honest-coverage-model.md` (additive schema + enumeration
  matrix + UAC-sourced carve-out table). Next: dispatch Sonnet impl of companion Phase-1/Phase-2 against the spec.
- **2026-06-29 tick-2..4 — companion IMPL + 3 Layer-1 bugs found & fixed.** Sonnet impl shipped Phase-1 completeness
  check + Phase-2 v2 harness (instruments-service@875c47b→051e5a8, CI v2 GREEN #688, 38 tests; companion checkboxes
  flipped @379963718,@f9ca06fd7). Three denominator-honesty bugs surfaced via operator review + the live runs, each
  fixed: **Bug-1** defi EXPECTED=0 (authority was the raw `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE` dict which has no
  defi keys → switched to UAC functions
  `valid_data_types_for_venue_instrument_type`/`valid_data_types_for_instrument_type`; defi 0→3,581 expected tuples);
  **Bug-2** empty denominator falsely reporting 100% → fail-CLOSED `UNDEFINED` guard; **Bug-3** EXPECTED↔ENUMERATED
  vocabulary/grain mismatch (casing PERPETUAL vs perpetual, venue AAVE_V3/AAVEV3, sports itype odds vs exchange_odds)
  producing artifact 0%/low → canonical-key alignment + `--diagnose-layer1` mode. Codex updated for all three
  (@379963718-area + @248a35c72).
- **2026-06-29 tick-5 — CK3 CERTIFIED (Rule-9 final report).** Held the full pipeline; certified the Honest-Coverage-v2
  MODEL + MEASUREMENT honest (NOT a 100%-coverage claim — the opposite: it honestly reports real gaps + gates Layer-2).
  Verified gate propagation, no-silent-holes (empty-denom guard + diagnostic), both views, schema back-compat,
  vocabulary alignment. Certified Layer-1: cefi 65.91% (29/44), defi 69.44% (75/108), tradfi 51.43% (18/35), sports
  30.77% (8/26), prediction 66.67% (4/6); Layer-2 lower-bounds: cefi 37.86 | defi 57.55 | tradfi 88.81 | sports 100.00 |
  prediction 20.56. Real holes are honest backfill backlog (BITFINEX/BYBIT, defi absent protocols, CBOE/ICE, BETFAIR
  snapshot types, KALSHI/POLYMARKET market_lifecycle). **Forced tradeoff (Rule-1):** did NOT autonomously rewrite UAC's
  expected matrix to absorb the 300+ strays — many UAC entries are `UNCERTAIN — owner verify`, so sanctioning them needs
  owner judgment; filed as `issues/honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md` (P1) + flagged to
  operator. CK1+CK2+CK3 all ✅. Plan is `locked_by: live-defi-rollout` → archival is operator-gated (not autonomous).
