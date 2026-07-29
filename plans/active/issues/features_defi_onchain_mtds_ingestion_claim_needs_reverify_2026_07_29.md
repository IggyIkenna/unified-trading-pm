---
doc_type: issue
title: >-
  data_pipeline_check_mdps_features todo's "MTDS never ingested DEFI onchain raw-tick types" claim looks contradicted by
  data_completion_defi's captured-row counts — needs a quick re-verify before trusting the gate
summary: >-
  `plans/active/data_pipeline_check_mdps_features_2026_07_20.md` (line ~906, dated 2026-07-29, slot-13) gates
  `DEFI:onchain` real-throughput work on "MTDS has never ingested vault_share_price/lst_rates/lending_indices/
  oracle_prices/perp_funding" (a 2026-07-27 dependency-check failure for one specific benchmark day). But
  `plans/active/data_completion_defi_2026_07_15.md` shows large CAPTURED row counts for exactly these data_types as of
  ~2026-07-28 (lending_indices=336,041 captured, lst_rates=70,355, perp_funding=12,500, oracle_prices=125,371) —
  directly contradicting "never ingested." Investigation this session (partial, not completed) confirmed the dependency
  checker's bucket resolution for DEFI (`features_service/onchain/app/core/dependency_checker.py`, `bucket_template:
  "market-data-tick-{asset_group_lower}-prd-{project_id}"`) does NOT look like the wrong-bucket bug class that hit
  PREDICTION delta_one earlier in the same plan (4 call sites bypassing `_resolve_mdps_bucket`) — so a bucket-name bug
  is not the likely explanation. Most likely explanation not yet confirmed: the specific benchmark DAY used by the
  2026-07-27 dependency check falls in a real per-day coverage gap for these data_types (a freshness-lag false negative
  for THAT DAY, not "never ingested" at all), but this was not verified before this session ended.
status: open
nature: issue
asset_group: [defi]
stage: [data, features]
repos: [features-service, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [defi, onchain, mtds, dependency-checker, manifest, contradiction, needs-reverify]
related:
  [/plans/active/data_pipeline_check_mdps_features_2026_07_20.md, /plans/active/data_completion_defi_2026_07_15.md]
created: 2026-07-29
priority: P2
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
drift_direction: advance-code
source:
  [
    "slot-6, data_engineering, 2026-07-29, discovered while checking whether data_pipeline_check_mdps_features-050's
    DEFI:onchain gate had cleared",
  ]
resolved_by:
locked_by:
locked_since:
---

# DEFI onchain "MTDS never ingested" claim vs data_completion_defi's captured counts — reconcile

## What I found

While checking whether `data_pipeline_check_mdps_features_2026_07_20.md`'s gated todo (real per-family throughput
numbers for CEFI/TRADFI/DEFI, split off 2026-07-29 by slot-13) could proceed for the `DEFI:onchain` leg, I found what
looks like a direct contradiction between two active-plan claims:

- `data_pipeline_check_mdps_features_2026_07_20.md` (~line 887, 2026-07-27/28 entries): the `DEFI:onchain` dependency
  check failed with "no MTDS manifest in `market-data-tick-defi-prd-...` — MTDS has not run for
  `vault_share_price`/`lst_rates`/`lending_indices`/`oracle_prices`/`perp_funding`" for the specific benchmark day
  tested — read (and written into the gating todo) as "MTDS has never ingested these data_types at all."
- `data_completion_defi_2026_07_15.md` (a census table, dated ~2026-07-28 per its own progress log) shows real captured
  counts for the SAME data_types: `lending_indices=336,041 captured / 141 empty_confirmed / 52 attempted_failed`,
  `lst_rates=70,355 captured`, `perp_funding=12,500 captured`, `oracle_prices=125,371 captured`. This is not a small or
  edge-case amount — MTDS has clearly ingested these types extensively, somewhere in its history.

## Why it matters

If "never ingested" is actually "not captured for this ONE benchmark day" (a freshness-lag false negative, not a
structural gap), then `data_pipeline_check_mdps_features-050`'s DEFI:onchain leg may not actually need to wait on a real
MTDS backfill — it may just need a benchmark day picked from a window where these types ARE captured. Currently the
gating todo tells every future picker-upper "do NOT re-run DEFI before the named gap closes", which could be blocking
real, doable throughput-measurement work on a false premise. Conversely, if the dependency check's target day genuinely
falls after these types' capture cutoff (an ingestion that ran once historically and then stopped), that's a real,
still-open gap and the current gating is correct — this needs to be distinguished, not assumed either way.

## What I ruled out (partial investigation, not completed)

Read `features_service/onchain/app/core/dependency_checker.py::_check_mtds_manifest` / `check_dependencies` (DEFI
branch): the DEFI bucket resolves via `bucket_template: "market-data-tick-{asset_group_lower}-prd-{project_id}"` →
`market-data-tick-defi-prd-<project>`, which matches the actual bucket named in the original failure message — i.e.,
this does NOT look like the `_resolve_mdps_bucket` wrong-bucket bug class that hit `PREDICTION:delta_one` earlier in the
same plan (4 call sites each independently reconstructing the bucket name, fixed in `features-service@306bef65`). So a
bucket-name defect is probably NOT the explanation here — the check is very likely reading the right bucket and the
right data_type key.

Did NOT complete: actually reading `read_manifest_rows(bucket, date, data_type)`'s scoping (is it a single-day-exact
lookup, or does it look for the freshest-available row?) to confirm whether the 2026-07-27 test day genuinely has zero
manifest rows for these 5 data_types, versus the check being too strict about "today" vs "most recent captured date." An
attempt to verify this directly (import `unified_trading_library.manifest_writer.read_availability_index` in a throwaway
Python session) went down an expensive rabbit hole rebuilding a full ad-hoc venv from scratch (see the "measurement
trap" note below) and was killed before reaching a conclusion, to avoid burning more disk/compute on a 1-hour task.

## Recommended fix path

- [ ] [DATA] P2. Determine whether `DEFI:onchain`'s dependency-check failure (2026-07-27) was a single-day freshness-lag
      false negative or a genuine structural gap: pick a benchmark day from within a window `data_completion_defi` shows
      as densely captured for `lending_indices`/`lst_rates`/`perp_funding`/`oracle_prices` (e.g. within the 2023-2026
      range, cross-check against that doc's own census dates) and re-run
      `features-service/scripts/pipeline_e2e_check.py --day <chosen-day> --asset-group DEFI --family onchain --legs force --require-captured --auto-day`
      (or a lighter direct call to `check_dependencies("DEFI", <day>)`) to see if the dependency check now passes. If it
      passes: `data_pipeline_check_mdps_features_2026_07_20.md`'s gating note for `DEFI:onchain` is STALE and should be
      corrected (the real gap is day-selection, not an MTDS ingestion gap) and the throughput-measurement todo un-gated
      for DEFI. If it still fails on a densely-captured day: the "never ingested" framing is confirmed and the gate
      stands as-is — just note the specific evidence. Repo: features-service.

## Measurement trap (for whoever picks up P2 above, or anyone else needing to call into `unified_trading_library`

standalone)

Do NOT try to `pip install` a fresh ad-hoc venv to import `unified_trading_library`/`unified_api_contracts` for a quick
manifest check — the package has extensive version-pinned deps (`fastapi>=0.137,<1.0`, `PyJWT`, a Python-3.13-only
`TypeVar(..., default=...)` usage in `feature_calculator/registry.py`, etc.) that a hand-assembled
`pip install <guessed-list>` venv will not match correctly (hit
`ImportError: cannot import name 'iter_route_contexts' from fastapi.routing`, then
`ModuleNotFoundError: No module named 'jwt'`, then a `TypeVar` `default=` TypeError under a wrong Python minor version,
in sequence, ~910MB of throwaway venv built chasing it). The workspace's own repo `.venv` (created via
`uv`/`scripts/quality-gates.sh`, not manually) is the only venv guaranteed to match these pins — if a per-repo `.venv`
doesn't exist yet in your slot's checkout, either run the repo's own bootstrap (whatever `quality-gates.sh` uses to
provision it) or do the check via a narrower path that doesn't need the full package import at all (e.g. reading the
consolidated manifest parquet directly with a minimal `pandas`/`pyarrow`-only script, or just grepping existing plan
census docs as this session ultimately did instead).

## Progress Log

- 2026-07-29 (slot-6, data_engineering): Filed while investigating whether `data_pipeline_check_mdps_features-050`'s
  DEFI:onchain gate had cleared. Did not resolve the contradiction — see "What I ruled out" above. Also confirmed
  (separately, via grep of `plans/active/`) that the CEFI billing-waste operator go-ahead named in the same gating todo
  has NOT been granted as of this session (no matching approval text found anywhere in `plans/active/`).
  TRADFI:volatility's options/futures raw-tick backfill status was not independently re-checked this session beyond what
  the plan already documents.
- 2026-07-29 (slot-11, data_engineering, todo-054): Picked up the P2 fix-path recommendation above (re-verify via a
  direct `check_dependencies("DEFI", <day>)` call, no VM). Hit a NEW, more fundamental blocker before reaching a
  day-selection answer: the manifest read itself did not complete — root-caused to a missing `defi` entry in
  `AG_STALENESS_BUDGET_SEC`, filed + fixed as
  `issues/defi_manifest_consolidator_staleness_budget_missing_2026_07_29.md` (shipped
  `unified-trading-library@13d3daef` + `deployment-api@9b3e35e`). This doc's own P2 todo (pick a densely-captured day
  and re-run the dependency check) is now UNBLOCKED but still NOT executed — the fast consolidated-index read path
  should work now, but the actual re-verify call itself was not re-attempted this session (scope/time; see the sibling
  doc's own P2 followup, which restates this exact next step). Leaving this doc open until that call is actually made.
