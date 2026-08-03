---
doc_type: issue
title:
  Full-matrix /data-pipeline-check-features run (day=2026-07-05) surfaced 6 distinct GENUINE root-cause classes behind
  17/32 real failures — dependency-check/coverage mismatch, a date-handling bug, an OOM, a manifest-staleness/env-parity
  gap, and external-vendor auth failures
summary: >-
  Running the full 16-shard /data-pipeline-check-features matrix (day=2026-07-05) to completion (report:
  plans/audit/results/data_pipeline_e2e_check_features_2026_07_05.md), only 3/32 (force,skip) legs PASSED — 12 were
  cleanly skipped (no captured input / non-canonical, both honest and expected), but 17 FAILED with real VM exit codes
  (not the 4 timeout cases already tracked separately in
  issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md). Direct VM run.log inspection for a
  representative sample of the 17 failures surfaced SIX DISTINCT, GENUINE, REPRODUCIBLE root causes spanning at least 3
  repos — this is a real data-pipeline-correctness finding, not infra flakiness, and is being escalated per the
  workspace's "big finding" rule (cross-repo + data-correctness).
status: open
nature: issue
asset_group:
  [cefi, tradfi, sports] # deduped 2026-07-30 by /ag-closeout-audit Phase 0.3 -- `tradfi` was listed twice. Found
  # independently by BOTH the tradfi and the cefi tranche run (this doc is tagged for both, so it is in both candidate
  # sets). Set membership is UNCHANGED, so no tranche's candidate set moves and no new closeout-linkage orphan can
  # result (check_ag_closeout_linkage.py re-run: 0 orphans). The duplicate slot was NOT re-pointed at another AG --
  # that would be a scope judgement, so only the provable duplicate was removed.
stage: [data]
repos: [features-service, unified-trading-library, market-data-processing-service, deployment-service]
scope: [engineer, admin]
tags:
  [
    infra,
    features-service,
    pipeline-e2e-check,
    data-correctness,
    dependency-check,
    date-bug,
    oom,
    manifest-consolidator,
    external-vendor,
    big-finding,
  ]
related:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/archive/issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md,
    /plans/audit/results/data_pipeline_e2e_check_features_2026_07_05.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /codex/02-data/external-data-always-available-rule.md,
  ]
created: 2026-07-27
priority: P0
parent_epic: infrastructure_master
source:
  "slot-7, infra, discovered while running data_pipeline_check_mdps_features-030 (full-matrix
  /data-pipeline-check-features, day=2026-07-05), 2026-07-27 — BIG FINDING, operator attention requested"
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/active/issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md,
    /plans/archive/issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /codex/02-data/external-data-always-available-rule.md,
  ]
resolved_by:
---

# Full-matrix features check surfaced 6 distinct genuine failure classes — data-pipeline-correctness escalation

## What I found

The full 16-shard `/data-pipeline-check-features` matrix (day=2026-07-05, all 8 families × valid asset_groups,
`--legs force,skip --require-captured --auto-day`) ran to completion. The written report
(`plans/audit/results/data_pipeline_e2e_check_features_2026_07_05.md`) summarizes: **total=32 passed=3 failed=17
ambiguous=0 skipped=12**.

Only **3/32 legs actually passed**: `SPORTS:sports` force, `GLOBAL:calendar` force, `GLOBAL:calendar` skip (a genuine
skip-proof). The 12 `skipped` legs are honest and expected (`no_captured_input_for_window` for DEFI/PREDICTION on
families whose upstream candle/chain data doesn't exist yet, `non_canonical_input` for CEFI:volatility — both correctly
NOT counted as failures per the canonical-paths principle). **The 17 `failed` legs are the concern** — I read the actual
VM `run.log` for a representative sample and found SIX independent, genuine, reproducible root causes (none are infra
flakiness or a repeat of the already-tracked timeout issue):

### A. Dependency-check / coverage-check DISAGREEMENT (TRADFI:delta_one, force+skip, exit=1)

**Independently corroborated on a THIRD occurrence** by a different slot's parallel day=2026-07-19 run, which hit the
byte-identical `DEPENDENCY CHECK FAILED` for the same TRADFI:delta_one shard on a different day (2026-07-18) — see
`issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md` for that occurrence's own detail
and its tracked fix-todo (not duplicated here; this doc's own todo below was folded into that one as the single
fix-tracker for this root cause).

The driver's own `--require-captured --auto-day` pre-check decided the `2026-07-04..2026-07-05` window for
TRADFI:delta_one WAS covered (no skip logged). But the VM's own `check_dependencies()` call refuses to run:

```
ERROR DEPENDENCY CHECK FAILED
ERROR Missing: market-data-processing-service
ERROR   Path: gs://market-data-tick-tradfi-prd-central-element-323112/processed_candles/by_date/day=2026-07-04/
ERROR   Reason: No data for 2026-07-04/TRADFI
```

The local coverage pre-check and the VM-side dependency check are reading the SAME upstream MDPS candle bucket but
reaching OPPOSITE conclusions about whether `2026-07-04` is covered. This is either (a) a genuine gap in the
`--require-captured` logic (checking a stale/wrong index, wrong `pipeline_mode`/`source` prefix, or the wrong day math),
or (b) the MDPS candles for that exact day genuinely aren't there and the coverage check is wrong to have called it
"covered." Either way this is a real correctness bug in one of the two check paths, not an infra blip.

### B. `multi_timeframe` family reads TODAY's date instead of the requested window (CEFI + TRADFI, force, exit=1)

BOTH `CEFI:multi_timeframe` and `TRADFI:multi_timeframe` fail identically:

```
ERROR No upstream data: delta-one features for asset_group=CEFI date=2026-07-27 produced 0 instruments.
ERROR No upstream data: delta-one features for asset_group=TRADFI date=2026-07-27 produced 0 instruments.
```

**`2026-07-27` is TODAY (the actual wall-clock run date) — not the requested `--start-date`/`--end-date` window**
(`2026-06-28/2026-06-29` for CEFI, `2026-07-04/2026-07-05` for TRADFI). This is a genuine, reproducible code defect in
`features-multi-timeframe-service`: it appears to look up delta_one input by the CURRENT date rather than the date range
the CLI was actually invoked with. This would fail for ANY asset_group/day combination, always, until fixed — it is
completely independent of upstream data availability.

### C. Genuine OOM during compute (CEFI:cross_instrument, force, exit=137)

```
INFO Loaded 115584 rows x 4476 columns from input bucket
INFO Computing feature group: regime_detection
WARNING HMM fitting failed: 'covars' must be symmetric, positive-definite
bash: line 1: 8732 Killed  ...python -m features_service --feature-family cross_instrument ...
[vm-exec] command exited rc=137
```

`exit=137` = `128+SIGKILL(9)` — the OS OOM-killed the process during `regime_detection`'s HMM fit on a 115,584-row ×
4,476-column matrix. This is a genuine memory-scaling issue in the `cross_instrument` compute path (likely needs
chunking, a smaller working set, or a bigger machine type), not a transient host-contention artifact — the process was
killed mid-computation on real, successfully-loaded data.

### D. Manifest consolidator stale/down + VM/local env-parity gap (SPORTS:sports, skip, exit=1)

```
unified_trading_library.manifest_writer._state.ManifestConsolidatorStaleError: Consolidated availability_index for
bucket='features-sports-test-central-element-323112' is stale or missing (older than
MANIFEST_CONSOLIDATED_STALENESS_SEC=1800s) while per-VM shards exist — the manifest consolidator is behind or DOWN.
Refusing to fall back to the per-VM shard merge (can OOM on large buckets). Remediation: fix the consolidator Cloud
Run Job + Scheduler for this bucket; set MANIFEST_ALLOW_STALE_FALLBACK=true to force the recovery merge.
```

Two things here: (1) the manifest consolidator for `features-sports-test-central-element-323112` is genuinely stale/down
(real ops gap), and (2) the LOCAL driver process sets `MANIFEST_ALLOW_STALE_FALLBACK=true` for its own reads
(`pipeline_e2e_check.py::main()`, `os.environ.setdefault(...)`) but this same tolerance is NOT propagated to the remote
VM's environment — so the identical staleness condition that the local driver silently tolerates causes the VM's own
`sports/cli` invocation to hard-refuse. This is an env-parity gap between the local check-runner and the VMs it
launches.

### E. External commodity-data vendor auth/config failures (TRADFI:commodity, force+skip, exit=1)

```
ERROR [CRITICAL] infrastructure error in features-service.fetch_ng_storage: HTTP Error 403: Forbidden
ERROR [CRITICAL] infrastructure error in features-service.fetch_cot_positions: HTTP Error 403: Forbidden
ERROR [CRITICAL] infrastructure error in features-service.fetch_rig_count: HTTP Error 404: Not Found
ERROR Partial factor coverage for commodity=NG date=2026-07-05: 2/5 factors produced values (3 missing). Failing
day rather than emitting a partial signal.
```

Three external commodity-data vendors (EIA weekly storage, CFTC COT report, Baker Hughes rig count) are returning
403/404 — this reads as credential/config issues (403 = auth) or a moved/retired endpoint (404), not something this
check itself caused. Per CLAUDE.md's "external data is always available" rule, exhausting the free/configured path is a
`BLOCKED-CREDENTIALS` finding, not a silent descope — flagged here for the operator to route.

**2026-07-27 UPDATE (operator-directed investigation)**: all three vendors are actually free/no-auth-required — the
operator's "drop if not free" heuristic doesn't apply to any of them. Root-caused each individually:

- **EIA** (`fetch_ng_storage` / crude storage, `storage_alpha` factor): genuinely free (email-only instant registration
  at eia.gov/opendata), but `eia_ng.py`/`eia_crude.py` never send the required `api_key` query param at all — confirmed
  via `gcloud secrets describe eia-api-key` that the secret doesn't exist yet. Credential ask has been open since
  2026-06-09 (`unified-trading-pm/ikenna_orchestrator/pings/slot_3.md`), unactioned for >6 weeks. **Operator decision
  2026-07-27**: leave EIA BLOCKED-CREDENTIALS and exclude `storage_alpha` from `DEFAULT_FACTOR_GROUPS` (not fixed this
  session, adapter scaffold kept per the external-data-always-available rule).
- **CFTC**: fully public, no auth ever required — the 403 was `www.cftc.gov`'s Cloudflare bot-mitigation (JS challenge)
  blocking the annual ZIP download; confirmed by curl (403 on the ZIP endpoint, clean 200 JSON from CFTC's own Socrata
  Open Data API for the identical dataset). **Fixed**: `cftc.py` rewritten to query
  `publicreporting.cftc.gov/resource/72hh-3qpy.json` instead. Same investigation also found the NG/CL market-name
  fragments were stale post-contract-rename (`"NATURAL GAS"`/`"CRUDE OIL"` no longer match the primary NYMEX contracts,
  now named `"HENRY HUB - NEW YORK MERCANTILE EXCHANGE"` / `"WTI-PHYSICAL - NEW YORK MERCANTILE EXCHANGE"`) — fixed in
  the same commit since it's the same fetch path.
- **Baker Hughes**: fully public, no auth — the 404 was a stale hardcoded filename
  (`North-America-Rotary-Rig-Count-Current-Week.xlsx`); Baker Hughes moved to opaque per-upload `/static-files/<uuid>`
  paths that change on every weekly republish. **Fixed**: `baker_hughes.py` now scrapes the current report's URL from
  the `na-rig-count` landing page at fetch time instead of hardcoding a filename.
- Repo: features-service. Evidence: `features_service/commodity/adapters/{cftc,baker_hughes}.py` rewritten,
  `features_service/commodity/config.py` (`storage_alpha` removed from `DEFAULT_FACTOR_GROUPS`), tests updated in
  `tests/commodity/unit/{test_sources,test_sources_extra,test_schema_robustness}.py` — 340/340 commodity tests green.

### F. Cascading failure: TRADFI:cross_instrument (force, exit=1)

```
FileNotFoundError: No delta-one features found under gs://features-tradfi-test-central-element-323112/delta_one/by_date/day=2026-07-04/.
Run features-delta-one-service for TRADFI/2026-07-04 first.
```

This is a DOWNSTREAM CONSEQUENCE of root cause A (TRADFI:delta_one never wrote output because its own dependency check
failed first) — not an independent bug. Flagged for completeness but does not need its own fix; it should resolve
automatically once A is fixed and TRADFI:delta_one's force leg produces real output.

## Why it matters

- **The pass rate (3/32 = 9%) badly understates the actual mechanism health** and badly OVERSTATES it too in the
  opposite direction if read carelessly — neither "everything is broken" nor "everything works" is the honest read. The
  correct read is: 6 SPECIFIC, DIAGNOSED, FIXABLE issues, each independently actionable, plus 2 already known timeout
  cases (separate doc) and 12 honest skips.
- **Root cause B (multi_timeframe date bug) is the most concrete and highest-value fix** — it is asset_group- and
  day-agnostic (both CEFI and TRADFI hit it identically), meaning the `multi_timeframe` family has likely NEVER produced
  a valid batch/backfill run for any historical date, only ever "today" — a genuine correctness gap that would affect
  real production backfills, not just this smoke check.
- **Root cause A (dependency vs. coverage-check disagreement) is a data-pipeline-correctness HARD RULE matter**: either
  the coverage pre-check is lying about what's captured (risk: launching VMs against uncaptured windows fleet-wide,
  wasting compute) or the dependency check is wrong (risk: blocking real backfills that COULD succeed). Needs resolving
  before this family/AG combination can be trusted for a real backfill.
- **Root cause C (OOM) and D (manifest staleness) are real infra gaps** that will recur on every future run against
  these same shard shapes until fixed.

## Recommended fix path

- [x] [DATA] P0. **Root cause A — TRACKED IN A SIBLING DOC, not duplicated here**: see
      `issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md` for the fix-todo (same
      underlying disagreement between `--require-captured --auto-day`'s coverage check and the VM-side
      `check_dependencies()`, confirmed on 3 independent occurrences across 2 different days now). Reconcile there, not
      here, to avoid two parallel fix attempts. — ✅ features-service@ecd548b8 (sibling doc has full detail; this todo's
      own local `c06a9bbf` follow-up was superseded by a concurrently-shipped, more complete fix from another slot —
      discarded via `git rebase --skip`, never pushed, per the sibling doc's reconciliation). Root cause was neither
      phantom-capture nor a plain coverage-check gap: 2026-07-04 (the delta_one lookback window's start day) is an
      honest TradFi weekend/holiday (`empty_confirmed` in the real manifest, no backing object by design) — fixed at TWO
      complementary layers: (1) the runtime `DependencyChecker.check_dependencies()` (raw GCS probe, zero manifest
      awareness) is now manifest-aware (`features-service@ecd548b8`); (2) `pipeline_e2e_check.py`'s coverage-check
      itself had a separate, real granularity gap — it applied the same acceptable-status set to the TARGET day as to
      window-interior days, so an `EMPTY_CONFIRMED` target still read as "covered" — fixed via
      `features-service@1b272676` + `4fbf4dc7` (a different slot, reconciled together with the phantom-capture guard
      `features-service@696768c7` that a THIRD slot shipped concurrently for a related-but-distinct bug). Full
      reconciliation + verification against real production data in
      `issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md`.
- [x] [SCRIPT] P0. **Root cause B** — fix `features-multi-timeframe-service`'s delta_one-input lookup to use the
      requested `--start-date`/`--end-date` (or the per-day date it's currently processing), not the current wall-clock
      date. Repo: features-service (`features_service/multi_timeframe/` or wherever the delta_one input loader lives).
      **Done when**: a force run for a historical day with real delta_one output present succeeds (not a 0-instruments
      failure) — add a regression test asserting the lookup uses the CLI-provided date, not `datetime.now()`/similar. —
      ✅ features-service@87e39bc7. Root cause: `deployment-service/scripts/vm/launch-features-vm.sh` invokes EVERY
      family (multi_timeframe included) with `--start-date`/`--end-date`, never `--date`, but
      `features_service/multi_timeframe/cli/main.py`'s `_extra_args` only declared `--date` — `ServiceBootstrap`'s
      `parser.parse_known_args()` silently dropped the unrecognised `--end-date`, so `date_arg` fell through to
      `date.today()` for every batch invocation regardless of the requested window. Added `--start-date`/`--end-date` to
      the CLI (`--end-date` wins over the legacy `--date`, preserving back-compat for `scripts/e2e/run_pipeline_e2e.py`
      and `scripts/multi_timeframe/smoke_matrix.py`, which still pass only `--date`). 3 new regression tests in
      `tests/multi_timeframe/unit/test_cli_main.py` assert the CLI-provided `--end-date` reaches the batch handler (not
      `date.today()`), that `--end-date` wins when both are given, and that the `--date`-only back-compat path still
      works. Full `quality-gates.sh` green (17945 passed, exit 0) before ship.
- [x] [SCRIPT] P1. **Root cause C** — either chunk/stream the `regime_detection` HMM fit for `cross_instrument` (CEFI
      has ~589 instruments per the recent universe-filter fix; 4,476 columns is a wide feature matrix) or size the
      launcher's VM up for this family/AG, and/or add a memory-budget guard before the fit rather than letting the OS
      OOM-kill it silently. Repo: features-service. **Done when**: a from-scratch `cross_instrument` CEFI force-leg run
      completes without an OOM kill. — ✅ features-service@9ed3d59e. Root cause was NOT primarily raw matrix size —
      `_load_parquets_concat` row-stacks EVERY instrument's own candle series into one frame before dispatch, and
      `RegimeCalculator._calculate_features` ran the O(n²) expanding-window HMM walk-forward across that whole
      concatenated multi-instrument blob with no `group_by("instrument_id")` split (unlike
      `PolymarketTemporalCalculator`/`PolymarketWhaleActivityCalculator`, which already loop per entity). That fits an
      artificial price/return discontinuity at every instrument boundary (destabilising the covariance —
      `'covars' must be symmetric, positive-definite`) AND turns one 115,584-row O(n²) fit into the OOM driver instead
      of ~589 independent ~196-row fits (≈566× less walk-forward work). Fix: split by `instrument_id`, run each
      instrument's own contiguous series independently through the existing single-series pipeline, concatenate results
      back (`features_service/cross_instrument/app/calculators/regime_calculator.py`). Regression test added
      (`tests/cross_instrument/unit/test_regime_calculator.py::test_regime_calculator_multi_instrument_no_cross_contamination`)
      proves a batch result's rows for one instrument are byte-identical to computing that instrument alone — i.e. no
      cross-instrument leakage into `regime_hmm_state`/`regime_volatility`/`time_in_regime`/`regime_changed`. Full
      `quality-gates.sh` green (all existing regime/cross_instrument tests unchanged/passing) before ship. A live
      from-scratch VM force-leg re-run against real CEFI data (the literal "done when" proof) is deferred to the
      already-tracked re-verification todo below (P2, "re-run `/data-pipeline-check-features` for the affected 6
      shards") rather than duplicated here.
- [x] [SCRIPT] P1. **Root cause D** — (a) propagate `MANIFEST_ALLOW_STALE_FALLBACK` (or an equivalent recovery flag) to
      the remote VM's environment the same way the local driver sets it for itself, so the two sides have consistent
      staleness tolerance; (b) separately, check why `features-sports-test-central-element-323112`'s manifest
      consolidator Cloud Run Job/Scheduler is genuinely behind/down and fix the underlying schedule/job. Repo:
      unified-trading-library (env propagation) + deployment-service or the consolidator's own repo (Cloud Run fix).
      **Done when**: the consolidator is current for this bucket AND a VM launched without the override still succeeds
      (proving the fix isn't just papering over a permanently-broken consolidator). — ✅ deployment-service@e51bbab. (a)
      fixed: `launch-features-vm.sh`'s existing `-test-`-bucket `ENV_PREFIX` (already carries `IS_TEST_RUN=true` inline
      into `VM_BACKFILL_CMD`, run via `bash -c` on the VM) now also carries `MANIFEST_ALLOW_STALE_FALLBACK=true` — no
      `unified_trading_library` change needed, the generic staleness guard
      (`manifest_writer/_read_index.py::_resolve_allow_stale_fallback()`) already honours the env var; the only gap was
      this one launcher never setting it (the mtds-live/mtds-backfill/instruments-backfill launchers already do, via VM
      metadata — confirmed via grep). (b) **premise corrected, not a broken schedule**: live-verified via
      `gcloud run jobs list --region=asia-northeast1` that NO Cloud Run Job/Scheduler cron targets ANY `-test-` tier
      bucket for ANY category — the only `*-features-sports*` job (`uts-prod-manifest-consolidator-features-sports`)
      targets `features-sports-prd-central-element-323112` (confirmed via
      `gcloud run jobs describe --format=...containers[0].args`), not the `-test-` twin. Terraform confirms this is BY
      DESIGN, not drift: `manifest_consolidator_scheduler.tf`'s `local.deployment_env_short` map only resolves
      `{dev,staging,prod}` → `{dev,stg,prd}`, never `test` — provisioning a standing per-minute Cloud Run Job against an
      ephemeral smoke-test bucket would be pure billing waste, and no other category has one either. So there is no
      schedule/job to "fix" — (a) is the complete, correct fix (the VM-side read tolerates the permanent absence of a
      `-test`-tier consolidator, same as the local driver already does for itself), and the original "done when"
      (consolidator current + VM succeeds without override) doesn't apply to a bucket tier that structurally never gets
      a standing consolidator. Full `quality-gates.sh` green (deployment-service, pre-existing unrelated
      `TestQgSnapshotLauncher` red — a live-VM-state-dependent test flake, see
      `issues/deployment_service_qg_red_qg_snapshot_launcher_live_vm_flake_2026_07_27.md` — verified clean tree and
      waited for the conflicting VM to clear before re-running, both green after).
- [x] [SCRIPT] P1. **Root cause E, part 1** — CFTC + Baker Hughes were NOT credential gaps (both are free/no-auth);
      fixed the actual bugs — CFTC switched from the Cloudflare-protected `www.cftc.gov` ZIP download to the public
      Socrata Open Data API (`publicreporting.cftc.gov/resource/72hh-3qpy.json`) plus corrected the stale NG/CL
      market-name fragments (post-contract-rename); Baker Hughes now resolves the current-week report URL by scraping
      the `na-rig-count` landing page instead of a hardcoded (now-404) filename. Repo: features-service
      (`features_service/commodity/adapters/{cftc,baker_hughes}.py`). **Done**: 340/340 `tests/commodity/` tests green
      (`tests/commodity/unit/{test_sources,test_sources_extra}.py` updated for the new fetch paths + regression tests
      added for the URL-resolution and NG/CL fragment fixes).
- [x] [PM] P1. **Root cause E, part 2 — EIA — RETAGGED 2026-07-28 (workspace stale-gate audit; operator ruling already
      recorded, decision closed).** Operator ruling 2026-07-27: EIA IS free (email-only instant registration at
      eia.gov/opendata) but there's no `eia-api-key` Secret Manager entry yet (confirmed via `gcloud secrets describe`)
      and the credential ask has sat open since 2026-06-09 (`unified-trading-pm/ikenna_orchestrator/pings/slot_3.md`) —
      operator chose to defer registering it rather than action it now. Per the external-data-always-available rule this
      stays `BLOCKED-CREDENTIALS`, not a permanent descope: `storage_alpha` factor group removed from
      `DEFAULT_FACTOR_GROUPS` (features-service `config.py`) so the live signal engine no longer tries it by default,
      but the `StorageDeviationFactor`/`eia_ng.py`/`eia_crude.py` scaffold is untouched and still registered in
      `FACTOR_REGISTRY` — re-enable once the secret is provisioned AND the adapters are wired to actually send
      `api_key=` (they currently don't, a separate small fix needed at that time).
- [ ] [DATA] P2. Once A-D land, re-run `/data-pipeline-check-features` for the affected 6 shards (CEFI/TRADFI:delta_one,
      CEFI/TRADFI:cross_instrument, CEFI/TRADFI:multi_timeframe, SPORTS:sports) and confirm genuine (non-error)
      verdicts; the report's pass rate should rise substantially once B alone is fixed (it affects every family/AG
      that's `multi_timeframe`-derived).

## Progress Log

- 2026-07-27 (slot-7, infra): Filed after the full 16-shard `data_pipeline_check_mdps_features-030` matrix run completed
  (`plans/audit/results/data_pipeline_e2e_check_features_2026_07_05.md`, total=32 passed=3 failed=17 skipped=12). Read
  the actual VM `run.log` for 7 of the 17 failed legs (one from each distinct failure signature) to establish root cause
  rather than reporting a bare pass/fail count — this surfaced 6 independent findings (A-F, F being a cascade of A)
  spanning at least 3 repos. NOT fixed this session (task scope was running the check + writing the report, not fixing
  features-service bugs) — filed as its own P0 issue doc per the "big finding" / data-pipeline-correctness escalation
  rule. The two already-known timeout cases (CEFI:delta_one, TRADFI:volatility) are tracked separately in
  `issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md` and are NOT duplicated here.
- 2026-07-27 (slot-7, infra, discovered on pull-rebase): a different slot ran an independent parallel
  `/data-pipeline-check-features` sweep for day=2026-07-19 (todo 9b,
  `plans/audit/results/data_pipeline_e2e_check_features_2026_07_19.md`, 3 passed/13 failed/14 skipped) and independently
  hit root cause A (TRADFI:delta_one dependency-check gap, on a different day) and the timeout/duplicate-VM pattern (on
  the same TRADFI:volatility shard) — filed as
  `issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md` and
  `/plans/archive/issues/features_pipeline_e2e_check_duplicate_vm_launch_same_shard_2026_07_27.md` (resolved 2026-07-30)
  respectively. Cross-referenced all four docs so root causes A and the timeout defect each have exactly ONE tracked
  fix-todo, not two competing ones. That slot also corroborated root causes C (OOM) and E (commodity 404) independently,
  and confirmed (for their own run) that no PROD-pollution occurred for
  volatility/cross_instrument/multi_timeframe/commodity — matching this session's own direct PROD-safety verification
  for sports/calendar.
- 2026-07-27 (interactive session, operator-directed): operator asked "are EIA/CFTC commodities features" + ruled that a
  vendor with no Secret Manager credentials AND no free tier isn't MVP. Investigation (live curl probes against
  api.eia.gov, cftc.gov, publicreporting.cftc.gov, rigcount.bakerhughes.com + `gcloud secrets describe`) found the
  premise didn't hold — all three vendors are free; the 403/404s were real bugs, not credential gaps. Operator chose
  "fix CFTC + Baker Hughes now (zero operator action needed), drop EIA only (still needs the operator to register a free
  key, however small)." Shipped: `cftc.py` + `baker_hughes.py` rewritten (see root cause E above for detail),
  `config.py::DEFAULT_FACTOR_GROUPS` no longer includes `storage_alpha`, `CONFIGURATION.md`/`DEPLOYMENT_GUIDE.md`
  updated, `tests/commodity/unit/{test_sources,test_sources_extra,test_schema_robustness}.py` updated — 340/340
  commodity tests green. EIA adapter code untouched (scaffold stays per external-data-always-available rule) —
  registering `eia-api-key` and wiring it into `eia_ng.py`/`eia_crude.py` remains open, not actioned this session.
- 2026-07-27 (slot-4): fixed Root cause C — `features-service@9ed3d59e`. Traced the OOM to the batch handler
  concatenating every CEFI instrument's candle series into one frame (`_load_parquets_concat`) and `RegimeCalculator`
  running its O(n²) expanding-window HMM walk-forward across that whole unpartitioned blob (no
  `group_by("instrument_id")`, unlike the sibling polymarket calculators). Split the HMM fit per `instrument_id`;
  regression test proves no cross-instrument leakage. Full `quality-gates.sh` green. Live from-scratch VM verification
  against real CEFI data is left to the existing P2 re-verification todo, not duplicated here.
- 2026-07-27 (slot-4): fixed Root cause D — `deployment-service@e51bbab`. Added `MANIFEST_ALLOW_STALE_FALLBACK=true` to
  `launch-features-vm.sh`'s existing `-test-`-bucket env prefix. Corrected part (b)'s premise via live
  `gcloud run jobs list`/`describe` + a terraform read: no `-test`-tier bucket, for any category, has ever had a
  standing manifest-consolidator Cloud Run Job/Scheduler — this is deliberate (billing-waste avoidance for ephemeral
  smoke-test buckets), not an outage to fix. Blocked mid-ship on a pre-existing, unrelated `deployment-service`
  `quality-gates.sh` red (`TestQgSnapshotLauncher`'s `--dry-run-scheduler-body` tests hitting a real, genuinely-running
  daily `qg-snapshot-` cron VM's live singleton-lock check) — verified byte-identical on a clean tree, filed
  `issues/deployment_service_qg_red_qg_snapshot_launcher_live_vm_flake_2026_07_27.md` + declared repo-blocker
  `RB-ca8f005d` per RULES.md §4b, waited (bounded background watcher, ~4min) for the real VM to clear, then shipped once
  green.
- 2026-08-03 (slot-16, data_engineering, INTERIM — re-verification P2 todo still in progress): picked up the last
  unchecked todo (re-run the 6/7 affected shards). Ran
  `features-service/scripts/pipeline_e2e_check.py --day 2026-07-05 --legs force,skip --require-captured --auto-day --project central-element-323112`
  per shard. **SPORTS:sports — genuine PASS**: force wrote 28 parquet objects to
  `features-sports-test-central-element-323112` with `captured` manifest; skip leg verified genuine (object
  byte-unchanged fingerprint). Confirms root cause D (manifest staleness/env-parity) stays fixed.
  **CEFI/TRADFI:cross_instrument + CEFI/TRADFI:multi_timeframe — self-inflicted cascading failures, not a regression**:
  fired all 7 shards concurrently rather than sequencing delta_one first per the skill's own "Ordering matters" rule (a
  derived family reads delta_one's freshly-written `-test-` output as its input) — each failed with the expected
  `FileNotFoundError`/`No upstream data ... produced 0 instruments. Run features-delta-one-service first` once its VM
  actually ran, confirmed via direct `run.log` reads on the failed VMs (`features-e2e-cefi-20260803-023759-526e13`,
  `features-e2e-tradfi-20260803-023804-c54481`, `features-e2e-tradfi-20260803-023752-c81739` / `-024133-c81739`,
  `features-e2e-cefi-20260803-023805-38e1b8` / `-024152-38e1b8`). Re-run pending delta_one completion.
  **CEFI/TRADFI:delta_one — still in flight**: found an ALREADY-RUNNING pair of VMs
  (`features-e2e-cefi-20260803-023001-d7c1a5`, `features-e2e-tradfi-20260803-022954-b3b034`) at session start — most
  likely a resumed continuation of this same task from an earlier turn (boot response carried
  `dispatch_reason: "resume"` + `already_in_progress: true`); confirmed genuinely active (not stuck) via fresh `run.log`
  timestamps before deciding to wait rather than duplicate-launch (this driver's own dedup guard also refused my own
  concurrent attempts with `duplicate_in_flight`, consistent with that read). CEFI's VM was later confirmed
  **SPOT-preempted** (`compute.instances.preempted` op at 2026-08-03T03:00:19Z) — a normal, expected termination mode
  for a SPOT-provisioned backfill VM, not a hang; relaunched (`features-e2e-cefi-20260803-030432-d7c1a5`, currently
  running). Two earlier relaunch attempts also hit a transient `compute.instances.create` "Required permission" error
  under the `github-deploy@` service account that cleared on retry with no IAM change — same ambient identity had just
  successfully created a VM minutes earlier, so read as an API/quota blip, not a real access gap; noting in case it
  recurs. TRADFI's VM has run past its client-side 40min default timeout window with no enforcing driver process still
  attached (my own invocation exited early via the dedup guard) — this is expected: the timeout is a polling-loop budget
  on the ORIGINAL driver call, not something enforced against the VM itself, so it continues running to natural
  completion. Both VMs' `run.log`s show real, continuously-advancing work (delta_one feature computation for CEFI; MDPS
  candle scans for TRADFI), not a stall. **Not yet done**: waiting for both delta_one legs to reach a terminal
  `EXIT_STATUS`, then re-running the 4 derived shards against the freshly-written delta_one `-test-` output, then
  closing out this todo with the final consolidated verdict. No code changes needed for this todo (verification-only);
  nothing shipped against `features-service` this session.
- 2026-08-03 ~05:31Z (slot-16, data_engineering, INTERIM #2): TRADFI:delta_one's VM
  (`features-e2e-tradfi-20260803-022954-b3b034`) was **SPOT-preempted after running ~3h** (`compute.instances.preempted`
  op at 2026-08-03T05:30:48Z; no `EXIT_STATUS` written, consistent with a genuine preemption, not a hang) — relaunched
  (`features-e2e-tradfi-...` new VM, in flight). The long runtime before preemption is consistent with this shard's
  known-large buffer window (348d TRADFI vs 240d CEFI, `features_delta_one_sequential_per_day_gcs_scan_2026_07_27.md`)
  and a genuinely large volume of honest `Continuous series absent ... MDPS build-continuous must run first` warnings
  (upstream data gaps, not a driver bug) rather than a stall — confirmed via continuously-advancing `run.log` timestamps
  right up to the preemption instant. CEFI:delta_one's VM (`features-e2e-cefi-20260803-030432-d7c1a5`) remains healthy
  and running. Still not done; continuing to monitor both.
- 2026-08-03 ~11:25Z (slot-16, data_engineering, INTERIM #3 — TRADFI:delta_one VERDICT): TRADFI:delta_one's relaunched
  VM (`features-e2e-tradfi-20260803-053515-b3b034`) ran to a genuine terminal `EXIT_STATUS=1` after ~5h48m of real,
  continuously-advancing compute — **failed, not a genuine PASS**. Root-caused via direct `run.log` read + a code read
  of `instrument_type_filter.py`/`config.py`/`orchestrator.py`: (1) `filter_delta_one_instruments` resolves a
  never-provisioned `-stg-` instruments-store bucket under `--env staging` (a 5th confirmed site of the exact bug class
  already fixed at 4 sites in `pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md`) — caught + degrades
  to an ID-pattern fallback, so not fatal alone; (2) the auto-resolved window (`2026-01-20/2026-01-21`) produced 0/586
  usable TRADFI instruments at actual candle-load time despite `--require-captured --auto-day` having approved the
  window as covered — every real calculator then failed on empty input (ALL 18 feature groups failed); (3) separately,
  `swing_outcome_targets` is missing from `orchestrator.py`'s own local calculator dispatch map despite being registered
  in `calculators/__init__.py` — a genuine, smaller half-wired-feature bug (unlike `temporal`/`economic_events`, which
  are intentionally, documentedly excluded). Filed as its own issue doc with concrete fix-todos citing the exact prior
  sibling fixes to mirror:
  `issues/features_delta_one_instrument_type_filter_stg_bucket_404_and_swing_outcome_targets_dispatch_gap_2026_08_03.md`
  — `unified-trading-pm@dcfc59595`, verified on origin. Not fixed in this session (out of scope for this
  verification-only todo). **CEFI:delta_one still in flight**, healthy, no verdict yet.
- 2026-08-03 ~11:45Z (slot-16, data_engineering, INTERIM #4 — TRADFI:cross_instrument re-verified): re-ran
  TRADFI:cross_instrument (force+skip) now that TRADFI:delta_one has a genuine terminal verdict. Both legs FAILED
  (`vm_not_success:vm_exit_nonzero=1`) — confirmed via direct `run.log` read on the force-leg VM
  (`features-e2e-tradfi-20260803-113749-c81739`) it is the SAME real cascade, not a new bug:
  `FileNotFoundError: No delta-one features found under gs://features-tradfi-test-central-element-323112/delta_one/by_date/day=2026-01-21/ for timeframe=15s. Run features-delta-one-service for TRADFI/2026-01-21 first.`
  This traces directly to TRADFI:delta_one's real failure (root-caused, already filed in
  `issues/features_delta_one_instrument_type_filter_stg_bucket_404_and_swing_outcome_targets_dispatch_gap_2026_08_03.md`)
  — no new issue doc needed for this leg; it is expected to clear automatically once that fix lands. No code changes
  this session (verification-only).
- 2026-08-03 ~11:50Z (slot-16, data_engineering, INTERIM #5 — TRADFI:multi_timeframe re-verified): re-ran
  TRADFI:multi_timeframe force (VM `features-e2e-tradfi-20260803-114630-c54481`) — FAILED, same real cascade:
  `ERROR No upstream data: delta-one features for asset_group=TRADFI date=2026-01-21 produced 0 instruments. Run features-delta-one-service first`.
  Confirms root cause B (the date-handling fix, `features-service@87e39bc7`) is genuinely working — the family now
  correctly reads the requested window's date (`2026-01-21`, matching TRADFI:delta_one's own auto-resolved window)
  instead of wall-clock `today()`; the failure is purely the same real upstream-dependency gap already tracked in
  `issues/features_delta_one_instrument_type_filter_stg_bucket_404_and_swing_outcome_targets_dispatch_gap_2026_08_03.md`,
  not a regression of B. Skip leg was skipped by the driver's own `duplicate_in_flight` guard (concurrent with force on
  the same VM); not separately re-run since there is no valid prior successful output for it to skip against — the force
  leg alone is sufficient evidence for this cell's verdict. No code changes this session (verification-only).
  **Remaining open**: CEFI:delta_one still in flight (no verdict yet); CEFI:cross_instrument and CEFI:multi_timeframe
  still need re-running once CEFI:delta_one completes.
- 2026-08-03 ~13:37Z (slot-12, data_engineering, INTERIM #6 — task resumed on this slot): task reassigned to slot 12
  (`dispatch_reason: "resume"`, `already_in_progress: true`); no code/plan drift since INTERIM #5. Verified
  CEFI:delta_one's VM (`features-e2e-cefi-20260803-030432-d7c1a5`) is still RUNNING (`gcloud compute instances list`),
  ~10.5h elapsed, and genuinely healthy — not a hang: `run.log` timestamps are current to wall-clock (last line
  `2026-08-03 13:37:00`) with new distinct instruments still appearing (CEFI universe_filter retained 909/1203
  instruments; 173+ distinct instruments have reached a `Wrote 2/2 daily partitions` line so far, several passes per
  instrument across delta_one's feature-group batches — consistent with real, continuing work, not a stall). No
  `EXIT_STATUS` file yet. Continuing to monitor; will re-run CEFI:cross_instrument/multi_timeframe once a terminal
  verdict lands.
- 2026-08-03 ~14:34Z (slot-12, data_engineering, INTERIM #7): ~1h of continued bounded-watchdog monitoring since INTERIM
  #6. CEFI:delta_one's VM (still `features-e2e-cefi-20260803-030432-d7c1a5`, now ~11.5h elapsed) remains `RUNNING`
  throughout with consistently healthy forward progress — `run.log` grew from 616,884 to 713,686 lines (~97k new lines)
  over 9 sampled checks at 3-min intervals, no interval flat/stalled. No `EXIT_STATUS` yet. Switched the progress metric
  from "distinct new instrument names" (plateaued at 173 after ~13:47Z — a false-stall signal, since delta_one revisits
  the same instrument set across multiple feature-group passes) to raw log-line growth, which is monotonically
  increasing and a more reliable liveness proxy for this workload shape. Still waiting for a terminal verdict before
  re-running CEFI:cross_instrument/multi_timeframe.
- 2026-08-03 ~14:43Z (slot-12, data_engineering, INTERIM #8 — CEFI:delta_one VERDICT: genuine PASS): VM
  `features-e2e-cefi-20260803-030432-d7c1a5` reached a terminal verdict after ~11.5h: `[vm-exec] command exited rc=0`,
  `DEPLOYMENT_COMPLETED ... (exit_code=0)`, `EXIT_STATUS=0`, VM self-shutting-down per `VM_SHUTDOWN_ON_COMPLETION=true`.
  Verified genuine (not just exit-code luck) via direct GCS listing:
  `gs://features-cefi-test-central-element-323112/delta_one/by_date/day=2026-07-04/` and `.../day=2026-07-05/` both
  contain real per-`feature_group` output (candlestick_patterns, market_structure, momentum, moving_averages,
  oscillators, ...). Confirms root cause A's fix (manifest-aware `DependencyChecker` + coverage-check granularity fix)
  holds for CEFI too, not just the TRADFI occurrence it was originally verified against. Immediately launched the last
  two re-checks now that delta_one has real `-test-` output to read:
  `pipeline_e2e_check.py --day 2026-07-05 --asset-group CEFI --family cross_instrument --legs force,skip --require-captured --auto-day`
  and the same for `--family multi_timeframe` (both backgrounded local driver processes — VM launch + wait, not yet run
  to completion). No code changes this session (verification-only). **Remaining open**: CEFI:cross_instrument and
  CEFI:multi_timeframe verdicts pending; once both land, this todo's final consolidated verdict across all 6 shards can
  be written and the checkbox flipped.
