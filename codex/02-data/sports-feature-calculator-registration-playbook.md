---
doc_type: codex-ssot
title: Registering a new sports feature calculator against the coverage-gating architecture
summary: >-
  Step-by-step playbook for adding a new features-sports-service calculator so it gets Phase-1/2/3 honest-coverage
  treatment automatically: the UAC FEATURE_UPSTREAM_REQUIREMENTS entry (declares upstream dependencies), the
  _gate_then_run wiring in the dispatcher (runs check_calculator_coverage before compute), and the deployment-api
  per-calculator meta (auto-derived from the UAC entry — no manual touch needed). Also covers the DATA_TYPE_TO_REF_KEY
  mapping touch point for a genuinely new upstream data_type. Written for
  features_sports_deployment_ui_coverage_tab_and_registry_playbook_2026_07_21.md P8.C.
status: current
nature: ssot
asset_group: [sports]
stage: [data]
repos: [unified-api-contracts, features-service, deployment-api]
scope: [engineer]
tags: [sports, features, honest-coverage, calculator, registration, playbook, coverage-gate]
related:
  [
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
  ]
created: "2026-07-21"
authoritative_for: [sports feature calculator registration procedure]
referenced_by: []
owner:
last_reviewed: "2026-07-21"
code_refs:
  [
    unified-api-contracts/unified_api_contracts/canonical/domain/sports/feature_upstream.py,
    features-service/features_service/sports/compute/coverage_gate.py,
    features-service/features_service/sports/exporters/derived_new_calculators.py,
    deployment-api/deployment_api/services/data_status/sports_helpers.py,
  ]
---

# Registering a new sports feature calculator

This is the recipe for adding a new features-sports-service calculator (e.g. a new derived stat) so it participates in
the Phase-1/2/3 honest-coverage architecture from day one — the per-calculator `upstream_missing` / `out_of_coverage`
distinction, the coverage gate that skips a calculator honestly instead of crashing or emitting a silent zero, and the
deployment-ui/deployment-api visibility (`sports_honest_coverage()`, `FEATURES_SPORTS_PER_CALC_META` — see
[`honest-coverage-model.md`](honest-coverage-model.md) for the general architecture this plugs into).

**There are exactly 2 touch points a new calculator's author must make, plus 1 conditional third.** A common mistake is
trying to also touch deployment-api directly — don't; its per-calculator metadata is auto-derived from step 1.

## Step 1 — declare the calculator's upstream dependencies (UAC)

Add an entry to `FEATURE_UPSTREAM_REQUIREMENTS` in
`unified-api-contracts/unified_api_contracts/canonical/domain/sports/feature_upstream.py`, keyed by the calculator name
AS IT APPEARS IN THE DISPATCHER (the short form, e.g. `"team_form"`, not `"team_form_calculator"` — see the
"short-then-long fallback" note in Step 2):

```python
FEATURE_UPSTREAM_REQUIREMENTS: dict[str, list[UpstreamReq]] = {
    ...
    "my_new_calculator": [
        UpstreamReq(source="api_football", data_type="FIXTURES"),
        UpstreamReq(source="footystats", data_type="MATCHES", required=False, notes="enriches xG when available"),
    ],
    ...
}
```

`UpstreamReq` fields (`feature_upstream.py:39-66`):

- `source` — one of the registered source keys (`api_football` / `footystats` / `understat` / `transfermarkt` /
  `soccer_football_info` / `open_meteo` / `odds_api` / `mdps_odds_horizon_bucket`), or the special token `"derived"`
  when this calculator consumes ANOTHER calculator's output (set `data_type` to that upstream calculator's name — its
  coverage propagates automatically, see `coverage_gate.py:134-138`).
- `data_type` — the UAC canonical data_type this dependency reads (`FIXTURES`, `XG`, `PLAYER_VALUES`, etc.).
- `required` — `True` (default): missing + in-coverage upstream → the gate skips the WHOLE calculator with
  `upstream_missing`. `False`: missing upstream just NaNs that one input column; the calculator still runs on its other
  inputs (use this for optional enrichment sources, e.g. Transfermarkt `PLAYER_VALUES` enriching a primary api_football
  feature).
- `notes` — free-text, why this dependency exists (shows up for future maintainers, not machine-read).

This ONE entry is the SSOT both the compute-time gate (Step 2) and deployment-api's honest-coverage reporting (Step 3,
automatic) read from — declare it once, both sides stay in sync by construction.

## Step 2 — wire the calculator into `_gate_then_run` (features-service)

The dispatcher never calls a calculator's `compute_xxx_batch()` function directly — it always routes through
`_gate_then_run` (`features-service/features_service/sports/exporters/derived_new_calculators.py:46-77`), which:

1. Calls `check_calculator_coverage(calc_name, ref_data, target_date)` (`coverage_gate.py:94`) — looks up the
   calculator's `FEATURE_UPSTREAM_REQUIREMENTS` entry from Step 1 and, for each required upstream, checks (a) UAC
   `in_coverage()` (is this upstream even expected for this date/league — pre-launch dates and known gaps return
   `OUT_OF_COVERAGE`, which is NaN-by-design, not a failure) then (b) whether `ref_data` actually has non-empty rows for
   that upstream (empty + in-coverage = `UPSTREAM_MISSING`, a genuine gap).
2. On `UPSTREAM_MISSING` or `OUT_OF_COVERAGE`, records the skip on the `quality_tracker` and returns — your `compute_fn`
   never runs, and the manifest write path marks the shard `attempted_failed` with reason
   `upstream_missing:{source}/{data_type}` (the honest-absence contract; see
   [`honest-absence-downstream-handling.md`](honest-absence-downstream-handling.md)).
3. Only on `READY` does it call your `compute_fn` via `_run_calc`.

Add your calculator to the appropriate dispatcher function (e.g. `_run_phase4_history_calculators` for a
history-dependent calculator) using the same `gate(...)` closure pattern every existing entry uses:

```python
gate(
    "my_new_calculator",
    lambda: compute_my_new_batch(target_fixtures, some_ref_df),
    extra_guard_ok=<a boolean if you need an extra in-pipeline precondition beyond the coverage gate>,
    extra_guard_status="skipped_no_data",  # or a more specific reason string
)
```

`calc_name` here MUST match the key you used in Step 1 (short form) — `check_calculator_coverage` tries the exact key
first, then falls back to `f"{calc_name}_calculator"` for legacy entries (`coverage_gate.py:119-126`); new calculators
should just use the short form consistently on both sides and skip the fallback entirely.

**Conditional Step 2b** — if your calculator's `UpstreamReq.data_type` is a data_type NOT already in
`DATA_TYPE_TO_REF_KEY` (`coverage_gate.py:67-82` — the UAC-data_type → `ref_data` dict-key mapping), add an entry there
too, mapping to whatever key `read_all_reference_data` populates for that entity. Skip this if you're reusing an
already-mapped data_type (`FIXTURES`, `XG`, `PLAYER_VALUES`, etc. are all already covered) — most new calculators will
not need this step.

## Step 3 — deployment-api / deployment-ui visibility (automatic, DO NOT hand-edit)

`FEATURES_SPORTS_PER_CALC_META` in `deployment-api/deployment_api/services/data_status/sports_helpers.py` is a DICT
COMPREHENSION over `FEATURE_UPSTREAM_REQUIREMENTS` (imported from UAC):

```python
FEATURES_SPORTS_PER_CALC_META: dict[str, dict[str, object]] = {
    calc_name: {
        "source": next((r.source for r in reqs if r.required and r.source != "derived"), "derived"),
        "classifications": ("Prediction",),
        "axis": "per_feature_per_league_per_fixture_date",
        "unit": "fixture_dates",
    }
    for calc_name, reqs in FEATURE_UPSTREAM_REQUIREMENTS.items()
}
```

Your Step-1 UAC entry alone is what makes `sports_honest_coverage()` compute a per-league honest breakdown for your new
calculator — no deployment-api commit is needed. **If you find yourself editing `sports_helpers.py` to "add" a
calculator, stop — you're duplicating what Step 1 already gives you for free.** The one exception: today this
per-calculator axis is reachable only via `sports_honest_coverage()`'s internal computation, not yet wired to any HTTP
route for per-calculator drill-down (only the 3 rollup categories — `FIXTURE_FEATURES`/`ODDS_FEATURES`/
`DERIVED_FEATURES` — are exposed over `GET /api/data-status/turbo` today); see
`/plans/archive/issues/features_sports_deployment_ui_coverage_tab_and_registry_playbook_2026_07_21.md` for that gap.

## Worked example — adding a hypothetical `set_piece_calculator`

1. UAC: `"set_piece_calculator": [UpstreamReq(source="api_football", data_type="FIXTURE_EVENTS")]` in
   `feature_upstream.py`.
2. features-service: write `compute_set_piece_batch(fixtures_df, events_df)` in a new
   `calculators/set_piece_calculator.py`; add
   `gate("set_piece_calculator", lambda: compute_set_piece_batch(target_fixtures, ref_data.get("fixture_events", pd.DataFrame())))`
   to the relevant dispatcher function.
3. `FIXTURE_EVENTS` is already in `DATA_TYPE_TO_REF_KEY` (maps to `"fixture_events"`) — no Step 2b needed.
4. deployment-api — nothing to do; `sports_honest_coverage("set_piece_calculator", ...)` now works automatically once
   instruments-service has captured `FIXTURE_EVENTS` rows for the relevant dates.

## Codex SSOTs

[`honest-coverage-model.md`](honest-coverage-model.md) (the general two-layer honest-coverage architecture this
per-calculator gate is a features-sports-service-specific instance of),
[`honest-absence-downstream-handling.md`](honest-absence-downstream-handling.md) (the `attempted_failed` /
`upstream_missing` contract downstream of the gate),
[`availability-manifest-and-data-status.md`](availability-manifest-and-data-status.md) (the 4-state `capture_status`
model).
