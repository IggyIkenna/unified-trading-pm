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
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
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
- [x] ✅ [DATA] P1. **Root-cause why `lending_indices` capture stopped 2026-08-01 — DIAGNOSED + FIXED 2026-08-14
      (slot-5).** Cron/Workflow-trigger hypothesis FALSIFIED: `uts-prod-mtds-collect-lending-indices-cron` (Cloud
      Scheduler, `45 0 * * *`) fired reliably every single day throughout the stall. Real root cause found via Cloud Run
      Job execution history + logs: the target job `uts-prod-mtds-collect-lending-indices` has failed EVERY scheduled
      run since 2026-08-02 except one (08-07) — `OOM ("configured memory limit reached")` 08-02..08-10, then
      `timeout ("configured timeout reached")` 08-11..08-14 — because `LendingIndicesHandler.process()` called
      `freshness_cache.bulk_load()` raw via `asyncio.to_thread`, unlike sibling handlers (`gas_fee_handler`,
      `lst_rates_handler`, `_oracle_prices_freshness`) which already route the identical
      `ManifestFreshnessCache.bulk_load()` call through `_gas_fee_helpers.bounded_freshness_warmup()` (the proven
      gas_fees crash-loop fix). Cloud Logging on a live verification execution confirmed unbounded, near-linear RSS
      growth (~67 MiB/s, no plateau — 481MiB→2493MiB→4514MiB→6524MiB across 4 samples 30s apart) entirely inside the
      bulk_load call, both on the original attempt and its retry, killed by SIGKILL (signal 9) each time. **Fixed**: (1)
      `market-tick-data-service@4925f88d73` — wired `lending_indices_handler.py` onto `bounded_freshness_warmup()`,
      mirroring `lst_rates_handler.py`'s exact call-site pattern; (2) `deployment-service@21e6814616` — bumped the Cloud
      Run Job to 2CPU/8Gi (from 1CPU/2Gi, unchanged since launch), matching the settled config for sibling jobs
      `lst-rates`/`risk-params` that hit the identical OOM onset (2026-08-02) against the same ~42M-row defi
      availability index and were already fixed this way; applied live via `gcloud run jobs update` + verified via
      manual execution before landing the terraform sync. **Caveat — the resource bump alone was verified
      INSUFFICIENT**: a fresh manual execution at 2CPU/8Gi (execution `uts-prod-mtds-collect-lending-indices-nzdsm`)
      still OOM'd in ~5 min at the same growth rate, confirming this is a genuine unbounded-load issue in
      `bulk_load()`/`read_availability_index()` for the defi bucket's current index size, not merely an undersized
      ceiling — the `bounded_freshness_warmup()` code fix is the mechanism expected to actually resolve it (fails open
      on a stuck/slow load instead of blocking the whole job on it), but its live effect could NOT be verified in this
      diagnosis session: the Cloud Run Job's container image is built by `market-tick-data-service/cloudbuild.yaml`, so
      the code fix only takes effect once that image is rebuilt + redeployed (async, outside this session). **Follow-up
      needed**: after the next MTDS image build/deploy, run one more manual
      `gcloud run jobs execute uts-prod-mtds-collect-lending-indices` and confirm it completes with
      `records_written > 0` — if it still OOMs/times out even with the bounded wrapper, the underlying
      `ManifestFreshnessCache.read_availability_index()` likely needs a genuine memory-bounded/streaming read path
      (library-level UTL work, not a per-handler patch) since a `date_range=(target_day, target_day)` filter does not
      appear to bound its memory footprint today.
- [ ] [DATA] P2. **Verify the `bounded_freshness_warmup()` fix (`market-tick-data-service@4925f88d73`) actually resolves
      the `lending_indices` OOM/timeout once a fresh MTDS Cloud Build image deploys it** — this fix could not be
      live-verified in the 2026-08-14 diagnosis session (the running Cloud Run Job image predates the code change; MTDS
      ships to the image via `market-tick-data-service/cloudbuild.yaml`, not directly on quickmerge-land). Once
      redeployed:
      `gcloud run jobs execute uts-prod-mtds-collect-lending-indices --region=asia-northeast1     --project=central-element-323112`
      and confirm it completes with `records_written > 0` (not just exit_code=0 — check the manifest for real captured
      rows). If it STILL OOMs/times out, `ManifestFreshnessCache.bulk_load()` / `read_availability_index()` needs a
      genuine memory-bounded read path for a `date_range`-filtered call (the filter does not currently appear to bound
      memory) — that would be library-level UTL work, not a per-handler patch, and should be filed as its own issue doc
      against `unified_trading_library` if confirmed. AO-dispatchable once the image redeploy is confirmed (check
      `gcloud run jobs describe uts-prod-mtds-collect-lending-indices` for a recent image digest change, or the next
      `market-tick-data-service` Cloud Build history).
- **[SCRIPT] P3. EXTRACTED 2026-08-09 → `defi_satellite_ao_dispatch_batch11_2026_08_09.md`.** RULED 2026-08-08
  (operator), option (c): reclassify the 1,404 BLAZESTAKE retirement markers OUT of `attempted_failed` entirely** — the
  previously-open options (a)/(b) are superseded by this ruling. Disposition evidence: slot-6 escalation agt-d87c1c,
  2026-08-06. **Scoping read of `attempted_failed_staleness.py` (2026-08-08, before filing this todo)**: that module is
  a pure staleness-LABELING helper (`stale_days_since`/`stale_backlog_annotation`) — it computes a display annotation
  ("STATIC BACKLOG — no new activity in Nd") for an alert body; it does **NOT** mutate `capture_status` and does **NOT**
  gate/suppress paging cadence (its own docstring says so explicitly). Its threshold
  (`STATIC_BACKLOG_STALE_DAYS_THRESHOLD = 1`) is a 1-day label cutoff, not the "~14-day trailing window" this doc's
  earlier 2026-08-08 context note speculated might self-resolve the backlog — no code in this module supports that
  self-resolve assumption; the 1404 rows stay `attempted_failed` in the manifest indefinitely (and keep tripping
  DP-FETCH-009's abs-threshold count) until something actually rewrites their `capture_status`. **The real fix is a
  manifest-mutation script**, not a config/threshold change: write a targeted reclassification script (same shape as the
  already-shipped `relabel_retire_blazestake_venue_2026_08_06.py`, which flipped these exact rows
  `captured`→`attempted_failed` with reason
  `superseded_by_content_verified_canonical_solblaze_solana_relabel_2026_08_06`) that finds every
  `(defi, lst_rates, BLAZESTAKE)` row with `capture_status=attempted_failed` AND an `error_reason` starting
  `superseded_by_` (currently 1,404 rows, live-reverify the count at execution time — do NOT assume it's still exactly
  1,404), and rewrites each to `capture_status=empty_confirmed` via the standard manifest recorder's honest-absence path
  (mirrors how a retired/superseded venue is otherwise represented — `empty_confirmed` is the manifest's designated
  state for "genuinely will never produce data", distinct from `attempted_failed` = "we tried and it errored"; matches
  the sibling doc's own Option B framing). Verify: (1) a bounded pushdown read (`pyarrow.fs.GcsFileSystem` +
  `dataset.scanner(columns=..., filter=...)`, NOT a full `to_table()` — the 2.6GB defi `_index` OOMs on a full read, per
  this doc's own verification-traps note) confirms 0 remaining `attempted_failed` rows for `(BLAZESTAKE, lst_rates)`
  with a `superseded_by_*` reason after the script runs; (2) DP-FETCH-009's `(defi, lst_rates)` `attempted_failed` count
  drops by the reclassified row count. Repo: deployment-service (or wherever the manifest-mutation script family for
  this consolidator lives — mirror the existing `relabel_retire_blazestake_venue_2026_08_06.py`'s repo). parent_epic:
  infrastructure_master.

## Progress Log

- **2026-08-14 (slot-5, backend_engineer)**: item 3 (`lending_indices` stall) root-caused and fixed — see the flipped
  todo above for the full writeup. Summary: cron NOT stalled (falsified); the target Cloud Run Job OOM'd/timed out on
  every scheduled run since 2026-08-02 except one, due to an unbounded `ManifestFreshnessCache.bulk_load()` call that 3
  sibling handlers already route through the sanctioned `bounded_freshness_warmup()` fail-open wrapper.
  `market-tick-data-service@4925f88d73` (code fix), `deployment-service@21e6814616` (2CPU/8Gi resource bump, live +
  IaC-synced). Resource bump alone verified INSUFFICIENT (still OOM'd at 8Gi on a fresh manual execution); the code fix
  could not be live-verified this session (needs a fresh MTDS Cloud Build image) — flagged as a follow-up check once
  that image redeploys, plus a possible library-level (UTL `ManifestFreshnessCache`) memory-bounding gap if the wrapper
  alone doesn't resolve it.
- **round5-na-digest-defi 2026-08-08 (apply pass, item 72)**: operator answered the DP-FETCH-009 paging-policy question
  — option (c), reclassify the 1,404 markers out of `attempted_failed` entirely. Read `attempted_failed_staleness.py`
  first to scope the real change: confirmed it is a pure display-labeling helper (no `capture_status` mutation, no
  paging gate) with a 1-day (not ~14-day) staleness threshold — the earlier "self- resolves ~2026-08-19/20" context note
  has no code basis and is corrected here. Retagged the todo `[OPERATOR]`→ `[SCRIPT]` and filed the concrete
  manifest-mutation script scope (reclassify to `empty_confirmed`, mirroring the already-shipped
  `relabel_retire_blazestake_venue_2026_08_06.py`'s shape) — not implemented directly this session (real prod-manifest
  mutation across ~1,404 rows warrants its own careful build+verify pass, not a blind inline edit).
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

- **na-corpus-digest-closeout 2026-08-08**: item 3's live re-check (recommended by batch9, pending since 2026-08-07) is
  now done — a sibling read-only agent this session read `_index/availability_index.parquet` directly for
  `lending_indices` and confirmed the stall is real and ongoing: captured-row counts by `date` decline 07-25→143 through
  07-31→250, then zero 08-01..08-05, a one-off backfill spike 08-06→217 (single shared `attempted_at`, historical `date`
  spread — not fresh capture), then zero again 08-07/08. This also explains away the KAMINO counter-evidence that caused
  the original park — same backfill-`attempted_at` misread. Removed the `BLOCKED-OPERATOR-DECISION` park, upgraded item
  3 to `[DATA] P1` (root-cause diagnosis, AO-dispatchable — the 08-06 spike proves some process can still write,
  pointing at a scheduling/trigger issue over a code-level break). Item 4 (BLAZESTAKE paging policy) left
  untouched/still operator-gated per instruction, with a non-reclassifying context note added (self-resolves
  ~2026-08-19/20 once the 08-06-stamped retirement markers age out of the ~14-day trailing alert window).
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: CONFLICT-DEFERRED, not reclassified — item 3 (now
  `[DATA] P1`, AO-dispatchable per today's own self-resolution above) is still held by an ACTIVE sibling plan,
  `defi_satellite_ao_dispatch_batch9_2026_08_06.md` (`status: active`), whose own "Deferred — conflict-parked, needs an
  operator ruling" section explicitly recommends a live re-read before drafting a diagnosis todo — that re-read WAS done
  today (this doc's own na-corpus-digest-closeout entry above) and confirmed the gap, but batch9's park text has not
  itself been updated/closed to reflect it, and `batch10` (also `status: active`) independently lists this doc's item 3
  under its own `time_gated` bucket pending the same re-check "next round." Flipping this doc's `assigned_vm` now —
  before either sibling batch reconciles its own stale characterization — risks exactly the "second, redundant dispatch
  path" this doc's own 2026-08-07 verdict already guarded against. Item 4 (the `[SCRIPT] P3` manifest-mutation script,
  filed today) is not mentioned in either batch and would itself be a clean RECLASSIFY candidate, but the whole-doc-flip
  constraint means it can't be split from item 3's conflict. Recommend: batch9/batch10 owners reconcile their stale park
  text against this doc's live self-resolution next round, then re-run this classification. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA valid -- Sole open checkbox (root-cause `lending_indices`
  capture stoppage) reads AO-dispatchable on its own text, but this doc's own round7 (2026-08-08) entry ruled it
  CONFLICT-DEFERRED -- held by the active `defi_satellite_ao_dispatch_batch9_2026_08_06.md`'s operator-ruling-pending
  park. Not re-litigated. Doc stays `assigned_vm: NA`.
