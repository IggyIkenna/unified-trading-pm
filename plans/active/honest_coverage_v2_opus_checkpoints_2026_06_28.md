---
doc_type: plan
title: "Honest Coverage v2 — Opus checkpoints (cross-repo schema design + Layer-1 matrix + final certification)"
summary:
  "The few opus-required checkpoints of Honest-Coverage-v2: design the coverage.json v2 schema + two-layer/gate
  semantics (cross-repo UAC + IS + UTL manifest + deployment simultaneously), design the Layer-1
  enumeration-completeness matrix (catalogue × UAC expected-data-types), and the final integrated certification that the
  honest-100% semantics hold. Everything else is the sonnet-doable companion plan."
status: active
nature: design
stage: [data-ingestion, meta]
repos: [unified-api-contracts, instruments-service, unified-trading-library, deployment-service]
scope: [engineer, admin]
tags: [honest-coverage, denominator-audit, architecture, cross-repo, opus-checkpoint, data-correctness]
related:
  [
    honest_coverage_v2_instrument_denominator_2026_06_28.md,
    ../../codex/02-data/availability-manifest-and-data-status.md,
    ../../codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    ../../codex/06-coding-standards/model-tier-selection.md,
  ]
created: 2026-06-28
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
model_tier: opus-required
thinking_tier: high
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
assigned_role: data_engineering
drift_direction: advance-code
asset_group: cross-asset
---

> **HUMAN PLAN (`assigned_vm: NA`)** — operator-driven. The **Opus** half of Honest-Coverage-v2; the sonnet-doable
> mechanical work is `honest_coverage_v2_instrument_denominator_2026_06_28.md`.
>
> **🤖 MODEL TIER: `opus-required` (thinking: high).** These checkpoints are cross-repo architecture — they require
> holding UAC (expected-data-types) + IS (catalogue/enumerate/measure) + UTL (manifest writer) + deployment
> (status/gate) in context simultaneously, which is the SSOT's opus-required bar. **A Sonnet agent must NOT execute
> these.** **BOOT GATE (run FIRST, STOP on non-zero):**
> `python3 scripts/plans/audit_model_tier.py --assert plans/active/honest_coverage_v2_opus_checkpoints_2026_06_28.md` —
> exits 1 if a non-Opus agent reaches this plan (SSOT: `codex/06-coding-standards/model-tier-selection.md`).

## Ordering

`CK1 + CK2` (design, Opus) → sonnet companion plan implements + runs the fixes → `CK3` (certification, Opus). The
companion plan's `[OPUS-CK→companion]` items are blocked on CK1/CK2 output.

## Checkpoints

- [ ] [AGENT] CK1 P0. **Design the Honest-Coverage-v2 `coverage.json` schema + two-layer/gate semantics.** Decide the
      structure that carries: Layer-1 (instrument coverage) + Layer-2 (download coverage), both the day-by-day and
      shard-breakdown views, and the drill-down/roll-up tree
      (`asset_group → venue → instrument_type → data_type →     day`), plus the instrument-gates-download flag. Requires
      reconciling UAC `DATA_TYPES_BY_ASSET_GROUP` / `get_expected_data_types_for_venue`, the IS catalogue grain, the UTL
      manifest shard atom, and the deployment data-status/gate consumer **at once**. Output = the schema spec the sonnet
      plan implements. `Gate:` spec written + reviewed against all four repos' contracts.

- [ ] [AGENT] CK2 P0. **Design the Layer-1 enumeration-completeness matrix.** Define exactly what "should exist" means
      per (venue, instrument_type, data_type) = IS catalogue (within listing window) × UAC expected-data-types,
      INCLUDING the structural honest-absence carve-outs (e.g. Deribit options=options_chain-only, ASTER historical
      book5 absent, A_LEAGUE×footystats) so a legitimate absence is not counted as a denominator hole. Output = the
      matrix spec + carve-out list the sonnet `enumerate`/`measure` impl asserts against. `Gate:` matrix spec enumerates
      every in-MVP (venue, instrument_type, data_type) with its expected/absent verdict.

- [ ] [AGENT] CK3 P0. **Final integrated certification (after the sonnet impl + fixes + re-measure).** Hold the whole
      pipeline in context and certify: Layer-1 gates Layer-2; both views are correct; no silent denominator holes; the
      post-fix numbers are trustworthy (stale-bucket + manifest-split + instrument_type + VENUE_FETCH_FAILED fixes all
      verified). Sign off the codex SSOT as the standing definition. `Gate:` a written certification + the codex doc
      flipped to the authoritative v2 model.

## Progress Log

- **2026-06-28** — Created as the Opus half of the Honest-Coverage-v2 split (operator: "sonnet-capable items with a few
  opus checkpoints, failing if the model doesn't match"). Hard-fail tier gate wired via
  `scripts/plans/audit_model_tier.py --assert`.
