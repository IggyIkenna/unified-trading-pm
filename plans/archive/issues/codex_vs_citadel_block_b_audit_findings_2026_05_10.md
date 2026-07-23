---
doc_type: issue
title: Codex-vs-Citadel Block B (data + correctness model) — audit findings preserved from retired question doc
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    features-service,
    instruments-service,
    market-tick-data-service,
    strategy-service,
    unified-trading-library,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-10
author: ikenna + main agent
source:
  [
    PM@e381d016 (Block B audit fill landed in retired question doc),
    PM@5d2d74c1 (parallel agent retired plans/questions/codex_vs_citadel_infrastructure_specs_2026_05_08.md per
    lifecycle Step 5 — plan-spawned graduates to active plan),
    plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md (spawned active plan; this issue doc seeds its
    audit findings section ahead of the 12 sub-agent fan-out),
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-10
---

# Codex-vs-Citadel Block B audit findings — preserved from retired question doc

> **Severity**: P1 — recommendations are post-cutover but high-leverage; preserving the audit findings before they rot
> in git history. **Blast radius**: UAC + UTL + ~30 adapters across MTDS / instruments-service / features-service /
> sports adapters / DeFi adapters; ~6 codex docs; ~400 lines of CLAUDE.md. **Suggested owner**: spawned audit plan
> (`plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md`) Phase 4 (pre-cutover items) for the QG ADD-GATE
> A2 part-2 only; everything else is Phase 5 (post-cutover plans filed).

## Why this doc exists

The retired question doc `plans/questions/codex_vs_citadel_infrastructure_specs_2026_05_08.md` (PM@872f6984 → 3fa1504b →
e381d016 → deleted in 5d2d74c1) carried a fresh-eyes audit of 6 blocks (A repo-shape / B data-correctness / C
researcher-experience / D operational-governance / E missing-alpha-primitives / F non-negotiable-primitives) against the
Citadel-grade non-HFT combination benchmark.

When the parallel agent retired the question doc per lifecycle Step 5, the Block B fills (B1-B5, ~310 lines of analysis
with file:line evidence) were preserved only in git history. This issue doc migrates those findings into the active
surface so the spawned audit plan + the named active plans I'd extend can consume them.

## Block A — partial audit findings recap

### A2 — Codex inflation + codex staleness (status: SHIPPED + 1 part pending)

- **Shipped**: PM@b9c93a38 + PM@96fbd444 — codex stale-string sweep across 6 canonical-doc lines; workspace-manifest
  `versions` dict cleanup (3 archived features-_ removed); `.code-workspace` cleanup (8 archived features-_ folder
  entries removed). 27-active-repo count now consistent across `repositories` / `versions` / `.code-workspace`.
- **Pending**: QG ADD-GATE step. PM `scripts/quality-gates.sh` adds STEP that greps for `\b(60\+|[5-9][0-9]) repo` in
  canonical doc dirs + fails CI if any survive. Sentinel: any time codex hard-codes a fact that lives elsewhere as SSOT,
  fail loud.
- **Active plan to extend**: `plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md` Phase 4 (pre-cutover
  items) — add this gate as a deliverable.

## Block B — full audit findings (5 sub-questions)

### B1 — Honest-coverage taxonomy as runtime convention vs as type system

- **Code state**: `unified-trading-library/unified_trading_library/manifest_writer.py` is **4360 lines**. The 4-state
  taxonomy enforced by 4 separate methods on `ManifestWriter` (line 1053): `record_captured` (1968), `record_empty`
  (1397), `record_failed` (1595), `record_expected_unattempted` (1542). Plus `record_captured_from_counts` variant
  (2222). `CaptureStatus` str-enum (134) has 4 members. 6 distinct exception classes (`MissingClusterValidationError`
  173, `MissingFeatureFamilyError` 204, `UpstreamTimestampBiasError` 259, `MalformedTickFieldError` 308,
  `UnknownEmptyConfirmedReasonError` 349, `ClusterCoverageError` 379) plus `LookaheadBiasError` (point_in_time module).
  All runtime, not type-level.
- **Operational state — fire-rate**: 6 documented incidents in 30 days caught only after the fact: 2026-05-05 MDPS
  1440-NaN-OHLC-bars-per-day-for-years; 2026-05-06 TradFi MVP ES.OPT 18-dates-with-single-parent-fills (partial-bundle
  marked `captured`); 2026-05-07 RED ALERT 5 CeFi VMs writing 96-100% empty rows with all blank reasons; 2026-04-29 +
  2026-05-04 phantom audits (167k + 130,897 phantoms); 2026-05-07 MTDS Databento partial-bundle. Net fire-fight cost: ~2
  weeks of senior-agent time over 90 days.
- **Codex state**: ~6 docs cover the surface; ~400 lines of CLAUDE.md alone dedicated to honest-coverage discipline +
  enforcement protocol. Cross-referenced by name in ~30 codex docs + ~50 plan files.
- **Citadel-benchmark gap**: model adapter output as discriminated-union ADT —
  `AdapterResult = Captured(parquet_path, row_count: PositiveInt, available_at_envelope, cluster_coverage) | EmptyConfirmed(reason: EmptyConfirmedReason, attempted_at) | Failed(error: VenueError, attempted_at) | ExpectedUnattempted(attempted_at)`.
  Adapter returns this; manifest writer takes it as input; can't write `captured` for an empty result because can't
  construct `Captured(row_count=0)`. 6 runtime exception classes collapse into ~3 type-level invariants enforced by
  construction. Composes naturally with operator's "common SSOT codebase + hooks + min duplicate" directive.
- **Recommendation**: **LIFT (post-cutover)**. ~3-5 AI-days for UAC ADT + UTL `write_result(result: AdapterResult)`
  entry point + 1-2 reference adapter + tests; +1-2 AI-days per adapter family for migration sweep; ~400 lines of
  CLAUDE.md collapse to ~50; 4 of 6 exception classes become unconstructible. Workspace QG grep step asserts no
  `record_*(` direct calls in adapter source post-migration.
- **Active plan to extend / file**: file new plan `plans/active/honest_coverage_adt_lift_<date>.md` post-cutover OR fold
  into the spawned monorepo plan as a Phase under `unified-trading-core/contracts/` redesign.

### B2 — Per-source colocation vs per-(asset_group, data_type) colocation

- **Code state**: UAC `external/` has **73 source sub-directories** (sample: `bybit/` has `__init__.py`, `examples/`,
  `mocks/`, `normalize.py`, `schemas.py`). 73 sources are NOT 1:1 with ~53 venues — extra ~20 are data-providers
  (databento, tardis, alchemy, defillama, cryptoquant, barchart, coinglass, etc.) + macro feeds + auxiliary services.
  Cross-cutting "per-data*type" view comes from prose matrices in `/codex/02-data/mtds-data-source-coverage-matrix.md` +
  `sports-data-source-coverage-matrix.md` cross-linked to UAC registry helpers (`VenueMapping.all*\*\_venues`,
  `get_expected_data_types_for_venue`, `get_venue_data_type_start_date`).
- **Operational state**: per-source colocation works for "add a source" (1 PR / 1 dir / 1 registry entry). Strains on
  cross-cutting audits — ~5 documented incidents involved cross-cutting drift not catchable from single-source view.
  2026-04-20 phantom-audit incident (false 26% sports ODDS phantom) was matrix-doc / registry-code drift.
- **Codex state**: 2 prose matrix docs (~500 lines each) hand-typed; cross-link to registry helpers but ARE prose.
- **Citadel-benchmark gap**: keep per-source colocation (natural physical shape); generate per-data_type view from
  **typed registry**. Each source declares emitted data_types as `SOURCE_EMITS: dict[DataType, EmissionSpec]` in
  `external/{source}/registry.py` next to `schemas.py`. UAC exposes `data_type_coverage(dt)` derived helper. Matrix doc
  becomes generated artefact (committed .md rendered from registry at QG time). Composes with operator's "common SSOT +
  hooks + min duplicate" — `EmissionSpec` is the extension hook.
- **Recommendation**: **KEEP per-source; LIFT cross-cutting view to typed-registry-derived (post-cutover)**. ~2-3
  AI-days for registry + render script + 1-2 reference migrations; +1 AI-day per source family for sweep. Drift-induced
  phantom incidents become impossible by construction.
- **Active plan to extend**: `plans/active/manifest_evolution_master_2026_05_08.md` — add a Wave for cross-cutting
  registry lift. OR file as Phase under spawned monorepo plan.

### B3 — Manifest as side-effect-of-write vs as pre-flight planner + post-flight verifier

- **Code state**: today's manifest written as side-effect via 4 `record_*` methods (B1 above).
  `record_expected_unattempted` (line 1542) is the early planner-side form — pre-flight enumerator pre-populates
  expected rows; adapters supersede them.
- **Operator's existing direction**: `plans/active/expected_universe_v2_design_2026_05_08.md` (status: draft, folded
  into `manifest_evolution_master_2026_05_08` umbrella) is the canonical "manifest = pre-flight plan + post-flight
  verification" plan. Frontmatter declares the three-axis invariant: schema (UAC) + writer code (UTL + adapter
  callsites) + GCS data layout co-evolve.
- **Operational state**: 4 documented phantom-audit incidents in 30 days are the manifestation of "writer-as-SSOT means
  audit-after-the-fact."
- **Citadel-benchmark gap**: NONE conceptually — operator's existing plan sketches the right shape. Gap is execution.
- **Recommendation**: **ALIGN — follow operator's existing plan**. Track v2 enumerator landing + audit whether it
  actually replaces writer-as-SSOT vs sits alongside as parallel layer. **Zero new active plan updates** — operator's
  already on it.

### B4 — `live = batch` principle: prose vs type-level enforcement

- **Code state**: grep for `mode == "live"` / `mode == "batch"` / `pipeline_mode == ...` across strategy-service +
  features-service + market-tick-data-service: **only 11 occurrences**. Lower than expected given the volume of doc +
  plan content asserting the principle. Suggests principle is mostly enforced; the 11 are likely legitimate seam
  dispatchers (data source / output sink / live-trigger vs batch-trigger).
- **Codex state**: `/codex/04-architecture/batch-live-architecture.md` (436 lines) is SSOT — folded from 2 prior
  separate docs per `codex_refactor_2026_05_08`. Volume substantial (~500 lines) but earned.
- **Operational state**: low fire-rate in past 90 days. Principle is mostly self-enforcing.
- **Alpha-relevance**: **direct** — bad batch=live correspondence = backtest results don't predict live PnL.
- **Citadel-benchmark gap**: small. Bigger win is structural: per Block A1 consolidation, `Pipeline` base class lives in
  `unified-trading-core/runtime/` as shared primitive every service inherits, not 5+ copy-paste implementations.
- **Recommendation**: **KEEP — light touch**. Spot-check the 11 mode-conditional branches; classify legitimate-seam vs
  mode-leakage; fix in place if leakage (single PR). Optional QG step that greps `if.*mode\s*==\s*` patterns + WARNs
  (not fails) so future leakage is visible. ~1 AI-day.
- **Active plan to extend**: NONE NEEDED — track as informal item in monorepo plan when spawned.

### B5 — `available_at` as write-time stamp vs schema-level invariant

- **Code state**: `unified_trading_library/availability_stamping.py` is **330 lines** with per-source stamping rules
  (sports `kickoff − 60min`, fixture_events `event_time`, post-match `match_end_time`, pre-match odds publication time,
  weather forecast-issue-time, tick-level `tick.timestamp + scrape_latency`).
  `manifest_writer.assert_available_at_present` (line 72) is the runtime gate; missing/null `available_at` raises
  `LookaheadBiasError`. Two layers: (1) stamping helpers — opt-in by adapter; (2) runtime gate — catches missing- stamp
  at write time. **Gap**: gate is at write time, not at row-construction time. **Worse**: an adapter that stamps with
  the WRONG rule (e.g. `event_time` for a post-match stat that should use `match_end_time`) never fails — silent
  lookahead bias.
- **Operational state**: lookahead-bias incidents in 3+ documented cases (carry-tracer, sports lineup leakage, sports
  fixture stats). Runtime gate catches missing-stamp; doesn't catch wrong-rule.
- **Codex state**: `/codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md` + sports stamping rules in
  CLAUDE.md "Shard-granularity SSOT" section + ~5 plans + active `available_at_lookahead_bias_completion_*` plan.
  Substantial cross-referencing across multiple files.
- **Alpha-relevance**: **direct + critical**. Lookahead bias = invalid backtest = invalid alpha. Every minute of
  lookahead = potentially $X of phantom alpha that won't materialise live. **Single highest-priority Block-B item.**
- **Citadel-benchmark gap**: model `available_at` as **type-level required field on every row** with per-source
  `AvailabilityRule` Protocol. Row constructor invokes `rule.stamp(row)` automatically. Adding a new source = adding one
  `AvailabilityRule` impl.
- **Recommendation**: **LIFT (post-cutover, high-leverage)**. UAC `availability_rule.py` + row base class with pydantic
  validator + per-source migrations. 330 lines of `availability_stamping.py` collapse to ~50; lookahead-bias incident
  class becomes type-level unrepresentable. ~2-3 AI-days. Composes with B1 ADT lift (the `Captured(...)` ADT variant
  takes a row collection that's already stamped) + monorepo migration.
- **Active plan to extend**: extend `plans/active/available_at_lookahead_bias_completion_2026_05_08.md` with a
  post-cutover Phase for the type-level lift.

## Disposition + cross-references

| Sub-question | Recommendation                            | Active plan to extend                                                                              | Timing       |
| ------------ | ----------------------------------------- | -------------------------------------------------------------------------------------------------- | ------------ |
| A2 part-2    | ADD QG-GATE for hard-coded count strings  | `plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md` Phase 4                         | Pre-cutover  |
| B1           | LIFT to discriminated-union ADT           | NEW `honest_coverage_adt_lift_<date>.md` OR fold into spawned monorepo plan                        | Post-cutover |
| B2           | LIFT cross-cutting view to typed-registry | `plans/active/manifest_evolution_master_2026_05_08.md` Wave OR spawned monorepo plan Phase         | Post-cutover |
| B3           | ALIGN — follow operator's existing plan   | `plans/active/expected_universe_v2_design_2026_05_08.md` (operator already on it; no new plan)     | In flight    |
| B4           | KEEP — light touch                        | NONE NEEDED — informal item in monorepo plan                                                       | Post-cutover |
| B5           | LIFT to schema-level invariant            | `plans/active/available_at_lookahead_bias_completion_2026_05_08.md` extend with post-cutover Phase | Post-cutover |

## Recovery from git history

The full original audit findings (with prose explanations + benchmark-shape sketches) are preserved at PM@e381d016 under
`plans/questions/codex_vs_citadel_infrastructure_specs_2026_05_08.md`. Recover via:
`git -C unified-trading-pm show e381d016:plans/questions/codex_vs_citadel_infrastructure_specs_2026_05_08.md`.

## Block C/D/E/F audit fills — DEFERRED

Operator directive 2026-05-09 #3 was to fill remaining blocks self-paced. Block B is complete. Blocks C
(researcher-experience + alpha workflow), D (operational + governance — D3 per-agent worktrees promoted by directive
#1), E (missing alpha-multiplying primitives), F (non-negotiable primitives) remain to be filled.

These can land as additional issue docs in this directory (one per block) OR be folded into the spawned audit plan's
12-sub-agent fan-out as audit areas. Operator preference TBD — flag during the spawned plan's Phase 0 area enumeration.
