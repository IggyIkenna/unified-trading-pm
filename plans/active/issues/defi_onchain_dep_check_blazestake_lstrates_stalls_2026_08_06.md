---
doc_type: issue
title: >-
  DEFI:onchain benchmark blocked on two dep-check failures — BLAZESTAKE attempted_failed rows in lst_rates (persists
  every date), lending_indices stalled after 2026-07-31
summary: >-
  DEFI:onchain VM (features-e2e-defi-20260806-025432-onch5, start_date=2026-07-27) failed exit_code=1: DependencyChecker
  found 3 deps failing. Root-cause analysis: (1) lst_rates — BLAZESTAKE venue has `attempted_failed` rows on every date;
  `_evaluate_manifest_rows` treats ANY attempted_failed row as a dep failure (no known-outage exemption for BLAZESTAKE
  in `_KNOWN_OUTAGE_VENUES_BY_SVC`). A blazestake→SOLBLAZE-SOLANA canonical-migration shard (2026-08-06T02:45Z) adds
  SOLBLAZE-SOLANA captured rows but does NOT delete the old BLAZESTAKE attempted_failed rows — so the dep check still
  fails post-merge. (2) lending_indices — stalled after 2026-07-31; no captured data for 2026-08-01+. Net: no single
  date satisfies BOTH (dates ≤2026-07-31 fail lst_rates, dates ≥2026-08-01 fail lending_indices). (3) perp_funding
  (HYPERLIQUID/CEFI bucket) — captured 2026-07-30+ (passes), was fine once the cefi-bucket path fix shipped (Option B,
  2026-08-01 issue). TRADFI:volatility is under a SEPARATE issue doc.
status: open
nature: issue
asset_group: [defi]
stage: [data, features]
repos: [features-service, market-tick-data-service]
scope: [engineer, admin]
tags: [defi, onchain, dep-check, lst-rates, lending-indices, blazestake, data-availability]
related:
  [
    /plans/archive/issues/defi_onchain_perp_funding_permanently_unsatisfiable_dependency_2026_07_31.md,
    /plans/archive/issues/defi_oracle_prices_capture_stalled_since_2026_07_22.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
  ]
created: 2026-08-06
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
resolved_by:
source: >-
  slot-5 (data_engineering), 2026-08-06: post-VM log analysis for data_pipeline_check_mdps_features-056
context_scope:
  [
    features-service/features_service/onchain/app/core/dependency_checker.py,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    deployment-service/deployment_service/data_pipeline_monitors/attempted_failed_staleness.py,
    /plans/archive/2026_08/issues/defi_hyperliquid_residual_manifest_rows_2026_08_04.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
  ]
---

## Finding summary

**VM**: `features-e2e-defi-20260806-025432-onch5`, start_date=2026-07-27, exit_code=1

**3 failing deps on date 2026-07-27:**

| Service key                      | data_type       | Failure reason                                                   |
| -------------------------------- | --------------- | ---------------------------------------------------------------- |
| market-tick-data-service-lst     | lst_rates       | 1 attempted_failed shard (BLAZESTAKE) — re-run MTDS              |
| market-tick-data-service-lending | lending_indices | 6 attempted_failed shards (2026-07-27); stalled after 2026-07-31 |
| market-tick-data-service-perp    | perp_funding    | no HYPERLIQUID row on 2026-07-27                                 |

**Note**: vault_share_price and oracle_prices passed for 2026-07-27. perp_funding passes for dates ≥2026-07-30
(HYPERLIQUID captured from 2026-07-30).

## Root cause: lst_rates / BLAZESTAKE

`_evaluate_manifest_rows` (dependency_checker.py:142): ANY `attempted_failed` row causes failure, even if 33 other rows
are `captured`. `_KNOWN_OUTAGE_VENUES_BY_SVC` only exempts `POLYMARKET_PERP`/`BINANCE-DELIVERY` for
`market-tick-data-service-perp` — no exemption for BLAZESTAKE.

BLAZESTAKE (venue `BLAZESTAKE`, instrument `blazestake-solana:lst:bsol`) has `attempted_failed` lst_rates on:
2026-07-28, 2026-07-29, 2026-07-30, 2026-07-31, 2026-08-04, 2026-08-05.

A canonical-migration shard (`canonical-migration-defi-blazestake-retire-20260806-024520.parquet`) adds
`SOLBLAZE-SOLANA/bSOL/captured` rows for historical dates but does NOT delete/overwrite the old
`BLAZESTAKE/blazestake-solana:lst:bsol/attempted_failed` rows — they have different (venue, instrument_id) keys in the
dedup index.

## Root cause: lending_indices stall

DEFI MTDS capture for `lending_indices` stalled after 2026-07-31. The per_vm shards directory has NO lending_indices
shard newer than the pre-2026-08-01 index. Root cause of the stall is out of scope for this issue (separate MTDS capture
investigation needed).

## No-overlap constraint

- Dates ≤2026-07-31: lst_rates fails (BLAZESTAKE attempted_failed on 28th/29th/30th/31st)
- Dates 2026-08-01+: lending_indices missing (stalled); also lst_rates missing for 2026-08-01 to 2026-08-03

There is no date where BOTH lst_rates AND lending_indices pass the dep check.

## Resolution options

**Option A (code fix, recommended)**: Add `BLAZESTAKE` to `_KNOWN_OUTAGE_VENUES_BY_SVC` for
`market-tick-data-service-lst` in `dependency_checker.py`. BLAZESTAKE is being retired (canonical migration 2026-08-06)
— its `attempted_failed` rows represent the retirement transition, not a data gap relevant to the onchain feature
consumer (which reads `bSOL` staking yields, now under SOLBLAZE-SOLANA in canonical form). After Option A, the effective
date range shrinks to 2026-07-29+ (where lending_indices+lst_rates both pass).

**Option B (manifest fix)**: Set BLAZESTAKE's attempted_failed rows to `empty_confirmed` in the DEFI MTDS index.
Requires a one-off manifest manipulation script — more invasive than Option A.

**Option C (MTDS fix)**: Resume `lending_indices` capture past 2026-07-31. Unblocks 2026-08-01+ dates (subject to
BLAZESTAKE still blocking — Option A still needed).

**Operator decision needed**: Confirm Option A (code fix to dep checker for BLAZESTAKE known-outage) or Option B
(manifest cleanup). This is `BLOCKED-OPERATOR-DECISION` until confirmed.

## Todos

- [x] ✅ [CODE] P1. **RULED 2026-08-06 (operator), option A: approved.** `[CODE]` tag (was `[OPERATOR]`),
      AO-dispatchable — add BLAZESTAKE to the known-outage exemption in `dependency_checker.py`'s
      `_KNOWN_OUTAGE_VENUES_BY_SVC`. **Closed via `defi_satellite_ao_dispatch_batch10_2026_08_06.md` todo —
      `features-service@919ab7ed`** (2026-08-07, slot-10).
- [x] ✅ [DATA] P1. **Implement chosen option and relaunch DEFI:onchain benchmark VM** — once dep check passes for any
      date, relaunch `launch-features-vm.sh FAMILY=onchain ASSET_GROUP=DEFI start_date=<clean_date>` and capture
      throughput numbers for -056. **Closed via `defi_satellite_ao_dispatch_batch10_2026_08_06.md` todo** (2026-08-07,
      slot-10): VM `features-onchain-defi-20260807-172238` (SPOT, asia-northeast1-c, 1-day benchmark date=2026-07-29)
      exit_code=0; dep-check ✅ passed; 7/13 groups; lending_rates: 28045 rows written, lst_yields: 18 rows written;
      wall_clock≈121s/benchmark-day. Numbers recorded in progress log below.
- [ ] [DATA] P2. **Investigate lending_indices capture stall (post-2026-07-31)** — diagnose why DEFI MTDS isn't writing
      lending_indices rows for 2026-08-01+; may require a separate issue in MTDS. **Conflict-park note (2026-08-07):
      `defi_satellite_ao_dispatch_batch9_2026_08_06.md` (2026-08-06) ran this exact conflict-check and found
      contradicting evidence — `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` item 7 (KAMINO captured a
      row 2026-08-05) and the resolved `defi_manifest_consolidator_stale_lock_silent_stall_2026_08_05.md`
      (`KAMINO-SOLANA captured=80`) both directly contradict this item's "no captured data since 2026-07-31" premise —
      possibly a different manifest surface (per_vm shards vs live availability_index) or a partial/venue-scoped stall,
      not resolvable from text alone. batch9 PARKED this exact item as BLOCKED-OPERATOR-DECISION rather than drafting a
      from-scratch diagnosis todo, recommending a live per-venue `lending_indices` availability_index re-check FIRST.
      This na-eligibility-audit pass respects that standing park — do not reclassify this item independently of that
      ruling.**
- [ ] [OPERATOR] P3. **Decide DP-FETCH-009 paging policy for permanent retirement-marker cells** — the 1404 BLAZESTAKE
      markers permanently keep `(defi, lst_rates)` over the `attempted_failed` abs threshold, so the alert re-pages as
      STATIC BACKLOG each re-nag cooldown forever. Suppression / paging-cadence policy for stale cells is explicitly
      left open to the operator/alerting owner (`attempted_failed_staleness.py` docstring); options: (a) accept visible
      pressure on the known backlog, (b) have the detector exclude `superseded_by_*`-reason rows from the high count,
      (c) reclassify markers out of `attempted_failed`. Disposition evidence: slot-6 escalation agt-d87c1c, 2026-08-06.

## Progress Log

- **2026-08-06 (slot-5, data_engineering)**: diagnosed from VM exit_code=1 log. Filed this issue. BLAZESTAKE
  attempted_failed + lending_indices stall = no valid date for the dep check. Recommended Option A (known-outage
  exemption code fix). BLOCKED-OPERATOR-DECISION.

- **2026-08-06 (slot-6, data_pipeline_failure escalation agt-d87c1c)**: DP-FETCH-009 (`DP_RUN_MOSTLY_EMPTY`) fired on
  `defi/lst_rates` — 1406 attempted_failed cells of 74859 attempted (ratio 1.9%, abs>=500). Verified via bounded
  pushdown read of `_index/availability_index.parquet`:
  - **1404/1406 = BLAZESTAKE venue rows**, all stamped
    `superseded_by_content_verified_canonical_solblaze_solana_relabel_2026_08_06` — deliberate retirement markers from
    the shipped `relabel_retire_blazestake_venue_2026_08_06.py` (Phase B flips captured→attempted_failed + reason;
    commits `5da218b9`/`cf84eb30`/`e8c5d29a`). NOT genuine fetch failures.
  - **2/1406 = LIDO `429` rate-limit** — transient, self-resolving.
  - **0 captured BLAZESTAKE rows remain** (retirement complete); UAC
    `get_defi_declared_venues_for_data_type('lst_rates')` no longer returns BLAZESTAKE; all live handlers write
    canonical `SOLBLAZE-SOLANA`.
  - **Verdict: STATIC BACKLOG** — 1 attempted_failed row in last 1d (below the 500-row materiality floor); decaying
    trickle on already-tracked backlog, NOT a fresh regression. No code fix shipped (root cause already fixed + tracked
    here + in `defi_hyperliquid_residual_manifest_rows_2026_08_04.md`).
  - **Residual (monitoring-hygiene, operator-owned)**: the 1404 permanent retirement markers keep `(defi, lst_rates)`
    over the DP-FETCH-009 abs threshold, so the alert re-pages as STATIC BACKLOG each re-nag cooldown. Suppression /
    paging-cadence policy for stale cells is explicitly left open to the operator/alerting owner per
    `attempted_failed_staleness.py` module docstring — not decided here.

  - **Verification traps (re-learn these, don't re-derive)**: (1) read the availability index via
    `pyarrow.fs.GcsFileSystem` + `dataset.scanner(columns=..., filter=...)` row-group pushdown — a full `to_table()` on
    the 2.6 GB defi `_index` OOMs/times out on the shared host; only ever read filtered columns. (2)
    `GCP_PROJECT_ID=central-element-323112` must be exported for `resolve_bucket_name`. (3) The `error_reason` column is
    the discriminator: `superseded_by_*` = deliberate retirement marker (NOT a fetch failure) — never diagnose a
    DP-FETCH-009 cell as a regression without checking it first. (4) A cell's `max_attempted_at` near the daily 01:00
    UTC cron window is NOT new activity when the row carries a retirement reason — the retire script stamps reason
    without touching `attempted_at`.

- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA-STALE (already-duplicated), OVERRIDES this run's own
  Phase-1 classifier draft verdict of RECLASSIFY. The Phase-1 read correctly found items 1-2 bounded/AO-eligible and
  item 4 safely `[OPERATOR]`-tagged, but did not cross-check the two defi satellite AO-dispatch batch docs before
  recommending reclassification. Conflict-check against the active corpus found: items 1-2 already extracted verbatim
  into `defi_satellite_ao_dispatch_batch10_2026_08_06.md:116-123` (status: draft, pending operator approval) —
  reclassifying this doc now would open a second, redundant dispatch path the moment batch10 activates. Item 3 was
  independently conflict-checked by `defi_satellite_ao_dispatch_batch9_2026_08_06.md` (2026-08-06) and PARKED as
  `BLOCKED-OPERATOR-DECISION` over contradicting live evidence (KAMINO counter-examples) — a standing ruling this pass
  respects rather than re-litigates. Item 4 stays `[OPERATOR]`-tagged regardless. Net: nothing here is a clean,
  conflict-clear reclassify today. Citations added on items 1-3 above. Doc stays `assigned_vm: NA`; a future audit pass
  should re-check batch10's approval status and, separately, whether item 3's live-availability- index re-check (per
  batch9's own recommendation) has been done.
- **context-scout 2026-08-07**: populated context_scope (5 entries).

- **2026-08-07 (slot-10, backend_engineer)**: items 1+2 closed via `defi_satellite_ao_dispatch_batch10_2026_08_06.md`.
  BLAZESTAKE exemption shipped (`features-service@919ab7ed`); benchmark VM launched + completed. **DEFI:onchain
  benchmark — MEASURED ✅**: VM `features-onchain-defi-20260807-172238` (SPOT, asia-northeast1-c, 1-day benchmark
  date=2026-07-29, `launch-features-vm.sh --feature-family onchain --asset-group DEFI`).
  - dep-check: ✅ `Dependencies verified for 2026-07-29/DEFI` at 17:27:03 UTC (BLAZESTAKE exemption live)
  - IS catalogue: 7161 DEFI instruments; 13 on-chain feature groups processed
  - Results: 7/13 groups succeeded; 2 groups wrote real data (`lending_rates`: 28045 rows, `lst_yields`: 18 rows);
    remaining 5 `empty_confirmed(EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE)` or
    `attempted_failed(calculator_produced_base_columns_only)` (honest-absent — IS no availability partition for
    2026-07-29)
  - EXIT_STATUS=0; wall_clock≈121s/1-benchmark-day (17:27:09→17:29:10 UTC)
  - **Throughput: ~121 s/benchmark-day** (for reference: TRADFI:commodity was ~39 s/shard-day on a 7-day run)
  - Note: `data_pipeline_check_mdps_features_2026_07_20.md` at 1000L hard cap — numbers recorded here, not in -056 plan.
