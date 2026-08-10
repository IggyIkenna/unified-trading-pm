---
doc_type: codex-ssot
title: Scenario Overlay Semantics
summary: >-
  Scenario overlay data-contract SSOT — the 3 scenario-provenance parquet columns (scenario_id / run_id /
  synthetic=True), per-row scenario_id propagation through MTDS->MDPS->features->strategy->ScenarioReport, the
  available_at discipline under stale-hold mutations (lookahead downgraded via SCENARIO_OVERLAY_LOOKAHEAD_DOWNGRADE,
  never suppressed), the deferred MANIFEST-tap scenario_id column, and per-consumer scenario-row handling.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service]
scope: [engineer, admin]
tags: [scenario, manifest, data-correctness, validation, monitoring]
related: [plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md Phase 8.C]
created: 2026-05-18
authoritative_for: [scenario overlay parquet provenance columns, scenario_id propagation contract]
referenced_by: [/codex/04-architecture/scenario-injection-architecture.md]
owner:
last_reviewed: 2026-10-22
code_refs:
author: harsh-slot-3
---

# Scenario Overlay Semantics

> **Parent architecture**:
> [`/codex/04-architecture/scenario-injection-architecture.md`](/codex/04-architecture/scenario-injection-architecture.md)
> — tap layers, mutation types, synthetic provenance. This doc covers the data contracts for scenario overlay output:
> how rows are marked, how provenance chains, and how `available_at` is treated.

## Overlay parquet schema

Scenario runs produce parquet output at each pipeline stage (post-cutover Phase 2.C). The canonical parquet schema adds
three scenario-provenance columns on top of the existing per-stage schema:

| Column        | Type   | Present on                | Description                                                            |
| ------------- | ------ | ------------------------- | ---------------------------------------------------------------------- |
| `scenario_id` | `str`  | All scenario-overlay rows | Snake-case scenario identifier; matches UAC `SCENARIO_REGISTRY`        |
| `run_id`      | `str`  | All scenario-overlay rows | UUID for the `ScenarioRunner` execution that emitted this row          |
| `synthetic`   | `bool` | All scenario-overlay rows | Always `True`; guards against mixing with real rows in downstream jobs |

Non-scenario rows do NOT carry these columns (they are absent / NULL). Downstream jobs that consume the parquet MUST
handle the nullable `scenario_id` column — do not assume it is always populated.

**Pre-cutover shape**: `ScenarioReport` is emitted in-memory and JSONL-serialised by the matrix runner; the parquet sink
(`ScenarioReportEmitter`) is a post-cutover Phase 2.C addition. The schema above is the SSOT for both the in-memory and
parquet representations.

> **[DELTA 2026-05-22]** **Current state:** Parquet sink (`ScenarioReportEmitter`) not yet active — `ScenarioReport` is
> in-memory + JSONL only. **Planned delta:** `plans/active/simulation_scenarios_post_cutover_2026_06_01.md` Phase 2.C
> wires the GCS parquet sink post-cutover. **Target architecture:** All scenario runs emit `report.parquet` +
> `matrix.parquet` to the GCS path below; `synthetic=True` rows distinguishable in downstream jobs without inspecting
> JSONL.

**GCS path** (post-cutover Phase 2.C):

```
gs://{pid}-scenario-reports/{archetype}/{YYYY-MM-DD}/{scenario_id}/{run_id}/report.parquet
gs://{pid}-scenario-reports/matrix/{archetype}/{YYYY-MM-DD}/{run_id}/matrix.parquet
```

Bucket resolved via `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)` — never inline
`gs://` f-strings.

## Per-row `scenario_id` provenance

`scenario_id` is threaded through the full pipeline stage sequence so every row's origin is traceable:

```
MTDS injection  →  scenario_id stamped on output parquet row
                ↓
MDPS feature    →  propagated as-is from input row (same scenario_id)
                ↓
features-*      →  each calc propagates scenario_id from input tick rows (same)
                ↓
strategy-signal →  signal row carries scenario_id from feature input
                ↓
ScenarioReport  →  run_id + scenario_id on report; per-assertion evidence linked by run_id
```

Services that compute derived rows MUST copy `scenario_id` from input to output. Dropping it silently breaks the
attribution chain — use `propagate_scenario_provenance(input_row, output_row)` from
`unified_trading_library.scenario.provenance` (ships in Phase 3.B wire-in).

## `available_at` discipline under scenario overlay

Certain mutation types (`StaleHold`, `EventDrop`, `OracleDeviate` stale variant) legitimately shift the apparent
`available_at` of a row — a stale-hold scenario simulates a feed that stops updating, so downstream consumers see a
timestamp behind wall-clock.

Two rules govern this:

1. **Never silently shift `available_at`**: any mutation that changes `available_at` MUST do so explicitly in the
   `ScenarioOverlayApplier.apply()` method. Downstream `assert_no_lookahead_for_feature_group(...)` calls MUST receive
   `scenario_overlay_active=True` so violations are downgraded to a `SCENARIO_OVERLAY_LOOKAHEAD_DOWNGRADE` structured
   warning — NOT silently ignored.

2. **Downgrade, never suppress**: lookahead warnings under an overlay are downgraded from error to warning. The warning
   is logged with the `SCENARIO_OVERLAY_LOOKAHEAD_DOWNGRADE` marker (UTL @`9e84ee44`). Strict lookahead enforcement
   stays on for all non-overlay paths — accidental scenario-driven masking of real lookahead bugs is prevented.

## Manifest `scenario_id` column

> **[DELTA 2026-05-22]** **Current state:** `MANIFEST` tap layer is DEFERRED — `scenario_id` columns do NOT appear in
> the manifest. **Planned delta:** `plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md` Phase 3.G
> wires `ManifestPhantom` mutations post-cutover. **Target architecture:** Manifest rows carry `scenario_id` so
> deployment-UI and downstream consumers distinguish scenario-injected gaps from real gaps without inspecting the event
> stream.

When the `MANIFEST` tap layer is active (post-cutover Phase 3.G), `ManifestPhantom` mutations write manifest rows with a
`scenario_id` column alongside the standard `capture_status`, `reason`, and `available_at` fields. This allows the
manifest viewer (deployment-UI) and downstream consumers to distinguish scenario-injected gaps from real gaps without
inspecting the event stream.

Pre-cutover: the `MANIFEST` tap layer is DEFERRED; `scenario_id` columns do not appear in the manifest. Downstream
consumers that check `scenario_id IS NOT NULL` will find only NULL for pre-cutover runs.

## Consumer handling of scenario rows

See [`honest-absence-downstream-handling.md`](honest-absence-downstream-handling.md) § "Scenario-driven gap injection"
for the per-consumer-class rules. Key summary:

- **Execution**: applies the same skip/alert rule as for real gaps, PLUS alerting-service suppresses paging for
  `synthetic=True` rows.
- **ML training / inference**: NaN-fills the scenario row (same as real expected gap). The `data_quality_flag` column is
  set to `SCENARIO_SYNTHETIC` for optional model discounting.
- **Features (rolling window)**: `n_valid` denominator adjusted as normal; `scenario_id` is propagated to the calc
  output row.
- **Reconciliation**: both sides should agree on the synthetic gap; mismatch flags a scenario-harness bug.

## Cross-references

- Parent:
  [`/codex/04-architecture/scenario-injection-architecture.md`](/codex/04-architecture/scenario-injection-architecture.md)
  — tap layers + mutation types
- Gap handling: [`honest-absence-downstream-handling.md`](honest-absence-downstream-handling.md) — § "Scenario-driven
  gap injection"
- Manifest contract: [`availability-manifest-and-data-status.md`](availability-manifest-and-data-status.md) — 4-state
  capture_status + honest-absence SSOT
- Outcome assertions:
  [`/codex/04-architecture/scenario-outcome-assertions.md`](/codex/04-architecture/scenario-outcome-assertions.md) —
  PASS/FAIL/WARN semantics + matrix-red cutover-block
- Plan: `plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md` Phase 8.C
- Post-cutover scope: `plans/active/simulation_scenarios_post_cutover_2026_06_01.md` Phase 2.C (parquet sink)
