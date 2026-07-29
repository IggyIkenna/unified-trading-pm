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

- [x] ✅ [DATA] P2. **DONE 2026-07-29 (slot-6, data_engineering).** Determined whether `DEFI:onchain`'s dependency-check
      failure (2026-07-27) was a single-day freshness-lag false negative or a genuine structural gap, via direct
      `DependencyChecker(project_id="central-element-323112").check_dependencies("DEFI", <day>)` calls (not a VM launch
      — the repo's own `.venv` bootstrapped via `uv sync`, avoiding the measurement trap below) across **12 distinct
      days spanning 2026-05-01 through 2026-07-28** (2026-05-01, 06-01, 06-14, 07-01, 07-05, 07-20, 07-22, 07-24, 07-25,
      07-26, 07-27, 07-28). **Split verdict, both halves now resolved with hard evidence:** -
      **`vault_share_price`/`lst_rates`/`lending_indices`/`oracle_prices` — the "never ingested" framing WAS WRONG/STALE
      for these 4.** Each shows real captured manifest rows on MOST tested days (e.g. 2026-06-14: vault_share_price=8,
      lst_rates=60, lending_indices=260, oracle_prices=106 rows, all `available=True`) — genuine day-to-day coverage
      gaps exist (lending_indices failed on 07-20; oracle_prices failed on 07-25/07-27; lst_rates failed on 07-27,
      `lending_indices` even hit 6 `attempted_failed` shards on 07-27) but these are intermittent freshness gaps, not
      "never ingested." A day exists (2026-06-14, 2026-07-05) where all 4 pass simultaneously. - **`perp_funding` — the
      gate is GENUINE, not a false negative.** Zero MTDS manifest rows for `perp_funding` on **every single one of the
      12 tested days**
      (`no MTDS manifest in market-data-tick-defi-prd-central-element-323112       — MTDS has not run for perp_funding`,
      byte-identical message on all 12) — a real, currently-active structural gap distinct from the other 4. This
      directly conflicts with `data_completion_defi_2026_07_15.md`'s claim of `perp_funding=12,500 captured`
      historically and a live daily Cloud Scheduler job (`collect-perp-funding`, 01:15 UTC, per that doc's own audit)
      writing via `perp_funding_handler.py` → `get_write_bucket_name("market_data",       "defi")` (the same canonical
      bucket the dependency check reads) — i.e. the scheduler appears to run daily but produces no visible manifest rows
      for perp_funding across a ~3-month window. New follow-up todo below captures this as its own scoped investigation
      (out of scope for this todo — root-causing the scheduler/handler/manifest gap needs its own session). **Net effect
      on the gating todo**: `DEFI:onchain`'s dependency check will NOT pass on ANY day right now — it requires ALL 5
      deps (`required: True` on all 4 MTDS on-chain deps per `UPSTREAM_DEPS_DEFI`), and `perp_funding` is confirmed
      absent on every tested day. So `data_pipeline_check_mdps_features_2026_07_20.md`'s gate correctly STAYS closed for
      DEFI — but the "MTDS has never ingested vault_share_price/lst_rates/lending_indices/ oracle_prices/perp_funding"
      framing is now corrected to name `perp_funding` specifically as the sole live blocker (see that plan's updated
      line, same commit). Repo: features-service.
- [ ] [DATA] P2. **NEW 2026-07-29 (slot-6), follow-up split off the finding above.** Root-cause why the live daily
      `collect-perp-funding` Cloud Scheduler job (`market-tick-data-service`, `defi_collection_scheduler.tf:112`, 01:15
      UTC) produces zero MTDS manifest rows for `perp_funding` across every one of 12 tested days spanning 2026-05-01 to
      2026-07-28, despite `perp_funding_handler.py:225` resolving to the same canonical bucket
      (`get_write_bucket_name("market_data", "defi")`) the dependency check reads and a historical
      `perp_funding=12,500 captured` count in `data_completion_defi_2026_07_15.md`. Candidates to rule in/out: (a) the
      scheduler job is failing/erroring silently (check Cloud Scheduler execution logs + handler logs for the actual run
      window); (b) the handler writes real objects but something downstream (manifest consolidator / `record_captured`
      call) never registers them for the `perp_funding` data_type key specifically; (c) the historical 12,500-row count
      predates a since-broken code path and nothing has captured successfully since. Repo: market-tick-data-service
      (scheduler config + handler), possibly unified-trading-library (manifest consolidator) depending on root cause.

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
- 2026-07-29 (slot-6, data_engineering, re-dispatched to `data_pipeline_check_mdps_features-056` — the same gated parent
  todo): Resolved the P2 todo above. Re-checked all 3 gates fresh first: CEFI operator go-ahead still not granted
  (re-grepped `plans/active/`, no new approval text); TRADFI:volatility's raw-tick backfill status unchanged (no new
  evidence found). Then ran the 12-day `DependencyChecker` sweep documented in the now-flipped todo — confirmed
  `perp_funding` (not all 5 data_types) is the sole live blocker for `DEFI:onchain`. Corrected
  `data_pipeline_check_mdps_features_2026_07_20.md`'s gating note to name `perp_funding` specifically (same commit).
  Filed the new perp_funding-scheduler follow-up todo above. **Net: all 3 upstream gates (CEFI/TRADFI/DEFI) for the
  parent throughput-measurement todo remain genuinely closed** — the parent checkbox (line ~906 of that plan) stays
  `[ ]`; declining the dispatch again via `skip-current-task` (`reason_code: GATED`) rather than false-completing it,
  per the plans-run-to-actual-completion HARD RULE. This session's real, verifiable output is the corrected gate
  framing + the newly-scoped perp_funding follow-up, not the (still-blocked) throughput numbers themselves.
