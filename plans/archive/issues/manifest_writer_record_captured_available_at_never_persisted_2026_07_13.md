---
doc_type: issue
title:
  ManifestWriter.record_captured() / record_captured_from_counts() validate available_at but never persist it — every
  CAPTURED manifest row system-wide has always defaulted to ""
summary: >
  While root-causing the sports CF-8 available_at backfill regression
  (sports_cf8_available_at_backfill_regression_2026_07_13.md), found a second, separate, and much broader bug in the
  SAME area: ManifestWriter.record_captured() validates that its df carries a populated available_at column
  (assert_available_at_present), and record_captured_from_counts() validates its available_at_envelope, but NEITHER
  method ever passes that value into the AvailabilityRecord it constructs. Fixed both (unified-trading-library@9c9cdc50)
  with unit-test coverage, but this defect predates the fix by an unknown amount of time and affects every asset_group
  that calls record_captured() (confirmed non-test call sites: 18 in instruments-service, 43 in
  market-tick-data-service, 3 in market-data-processing-service, 4 in execution-service, 5 in strategy-service) — the
  CF-8-style audit only ever ran against sports; other asset_groups' manifest available_at fill rate has never been
  checked and may be systemically low for the same reason.
status: open
nature: notes
asset_group: [cross-cutting]
stage: [data]
repos:
  [
    unified-trading-library,
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    execution-service,
    strategy-service,
  ]
scope: [engineer, admin]
tags: [data-correctness, available-at, manifest-writer, cross-cutting, record-captured, lookahead-bias]
related:
  [
    plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md,
    plans/active/sports_manifest_canonicalisation_2026_06_01.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-13
parent_epic: manifest_master
priority: P1
source:
  sports_manifest_canonicalisation-004 dispatch, slot 3, 2026-07-13 (found while root-causing a different, sports-scoped
  todo)
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-13
locked_by:
resolved_by:
---

# record_captured() / record_captured_from_counts() never persisted available_at onto the manifest index

## What happened

Dispatched to `sports_manifest_canonicalisation-004` ("CF-8 `available_at` live backfill pass"). The plan's own text
(and `sports_cf8_available_at_backfill_regression_2026_07_13.md`) explicitly forbade re-running that live backfill until
its P0 root-cause todo was resolved, so instead of re-attempting the destructive operation I worked that P0 todo: a
synthetic (non-production) repro of `ManifestWriter._records_to_dataframe()`.

While doing so, another agent (slot 11) independently found and fixed the SAME root cause concurrently
(`unified-trading-library@f5f15e3a`): the serializer never included `available_at` in its per-row dict, so every
`write()` silently dropped the column regardless of what the in-memory record carried. That fix is correct and
sufficient for the `record_empty`/`record_failed`/`add()` write paths (all three DO correctly thread `available_at` onto
the in-memory `AvailabilityRecord` — confirmed by reading `_writer_record.py` / `_writer_ingest.py`).

**But `record_captured()` and `record_captured_from_counts()` — the OTHER two write paths, and the ones actual
production adapters use for real captured data — never threaded `available_at` onto the in-memory record AT ALL**,
independent of the serializer bug:

- `record_captured(df=..., ...)` (`unified_trading_library/manifest_writer/_writer_captured.py`) calls
  `assert_available_at_present(df)` — a **validation-only** gate confirming the caller's data `df` has a populated
  `available_at` column — then constructs the `AvailabilityRecord` for the MANIFEST INDEX row without ever reading that
  column's value. The manifest row's `available_at` field is simply omitted from the constructor call, so it silently
  defaults to `""`.
- `record_captured_from_counts(available_at_envelope=..., ...)` accepts a mandatory, validated (presence + tz-awareness)
  `available_at_envelope` parameter, uses it for `attempted_at=envelope_ts.isoformat()`... but never for
  `available_at=`. Same omission.

This is a genuinely different bug from the serializer issue: even with `f5f15e3a` alone, every row written via
`record_captured()`/`record_captured_from_counts()` would STILL have `available_at=""` on the manifest index, because
the value never reaches the `AvailabilityRecord` constructor in the first place. The serializer fix only guarantees that
whatever value the record carries survives to the parquet — it does nothing for a record that never had the value
stamped on it.

## Why this was missed for so long

The masking pattern is identical to the one `test_manifest_writer_serialized_columns.py`'s own docstring describes for
the pre-2026-06-16 v6-v9 column drop: `test_manifest_writer_live_mode_available_at.py` (the existing "A.8" contract test
for `record_captured` + `available_at`) asserts ONLY that no `LookaheadBiasError` is raised and that shard-shape fields
(`capture_status`, `data_type`, `venue`, `instrument_count`) are correct — it never asserts
`writer._records[-1].available_at` or the serialized DataFrame's value. The presence-gate
(`assert_available_at_present`) passing was mistaken for "available_at is stamped," when it only ever validated the
INPUT, not the OUTPUT.

## Blast radius (NOT yet audited — this issue doc's main ask)

Confirmed non-test call sites of `record_captured(` (a floor, not a full audit — services not checked, e.g.
alerting-service, deployment-api, fund-administration-service, greeks-service, trading-agent-service, ml-service,
features-service families, unified-trading-system-ui backend, are not yet grepped):

| repo                           | non-test `record_captured(` call sites |
| ------------------------------ | -------------------------------------- |
| market-tick-data-service       | 43                                     |
| instruments-service            | 18                                     |
| strategy-service               | 5                                      |
| execution-service              | 4                                      |
| market-data-processing-service | 3                                      |

Every asset_group these services write (tradfi, cefi, defi, sports, and whatever strategy/execution stamp) has, until
`unified-trading-library@9c9cdc50`, had `available_at=""` on every `record_captured`-written manifest row — the CF-8
sports investigation only ever measured sports (IS 62.9%, MDPS ~0%) because that is the ONLY asset_group with a
dedicated audit script (`cf_manifest_audit_2026_06_01.py`). Whether tradfi/cefi/defi manifest `available_at` fill rates
are similarly degraded is UNKNOWN — no equivalent audit exists for them.

## Fix applied

`unified-trading-library@9c9cdc50` (built on top of `f5f15e3a`):

- `record_captured()`: after the existing `assert_available_at_present(df)` gate passes, derive
  `_available_at_value = str(df["available_at"].max())` (empty df / missing column → `""`) and pass
  `available_at=_available_at_value` into the `AvailabilityRecord` constructor.
- `record_captured_from_counts()`: pass the already-validated `available_at_envelope` through as
  `available_at=envelope_ts.isoformat()`.
- Extended `test_manifest_writer_serialized_columns.py` with value-level assertions
  (`row["available_at"] == writer._records[-1].available_at`) on both `record_captured` tests, so a future regression in
  either method fails loudly rather than only checking column presence.

Full `quality-gates.sh` green (281s). Unit-tested only — **NOT verified against production data** (no production write
was made or attempted by this touch).

## Audit Results (2026-07-13)

Ran `plans/audit/results/available_at_fill_rate_audit_2026_07_13.py` — reads each bucket's CONSOLIDATED
`_index/availability_index.parquet` via UTL `read_availability_index()` (no whole-corpus GCS walk), filters
`capture_status=captured`, computes `available_at != ""` fill rate. Live production data, read 2026-07-13 ~23:29 UTC
(same day `9c9cdc50` landed — this is still overwhelmingly the historical pre-fix backlog).

**`market-data-tick` buckets (MTDS + MDPS write path — the actual buggy `record_captured`/`record_captured_from_counts`
call path):**

| asset_group | bucket                                               |                                                                                                                                                                                                                                                                                                                                                                                                                                 captured rows | filled | fill rate |
| ----------- | ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | -----: | --------: |
| defi        | `market-data-tick-defi-prd-central-element-323112`   |                                                                                                                                                                                                                                                                                                                                                                                                                                     3,010,913 |      0 |  **0.0%** |
| tradfi      | `market-data-tick-tradfi-prd-central-element-323112` |                                                                                                                                                                                                                                                                                                                                                                                                                                     1,620,826 |      0 |  **0.0%** |
| sports      | `market-data-tick-sports-prd-central-element-323112` |                                                                                                                                                                                                                                                                                                                                                                                                                                       377,194 |      0 |  **0.0%** |
| prediction  | `market-data-tick-pred-prd-central-element-323112`   |                                                                                                                                                                                                                                                                                                                                                                                                                                        45,542 |      0 |  **0.0%** |
| cefi        | `market-data-tick-cefi-prd-central-element-323112`   | NOT MEASURED — manifest consolidator for this bucket is stale/down (consolidated blob age 267–390s, over the 120s `MANIFEST_CONSOLIDATED_STALENESS_SEC` threshold); `read_availability_index()` correctly refused the per-VM-shard fallback merge (OOM risk on this bucket size) rather than silently under-report. This is a SEPARATE consolidator-health issue, not part of this audit's fix — flagged as a new todo below, not fixed here. |

Per-service breakdown confirms the 0% is uniform, not concentrated in one writer: e.g. `market-tick-data-service` (2.65M
rows), `market-data-processing-service` (364K rows), and `instruments-service` (172 rows) are ALL 0.0% filled in the
defi bucket; same pattern in tradfi/sports/prediction.

**Verdict: WORSE than sports-only.** The CF-8 sports-only signal ("IS 62.9%, MDPS ~0%") undersold the true blast radius
— every measurable non-sports asset_group on the MTDS/MDPS write path is uniformly **0%** filled, not partially
degraded. This confirms the issue's own hypothesis ("may be systemically low for the same reason") as TRUE, not just
possible.

**`instruments-store` buckets (instruments-service's own captured rows):**

| asset_group | bucket                                                | captured rows |    filled |  fill rate |
| ----------- | ----------------------------------------------------- | ------------: | --------: | ---------: |
| cefi        | `instruments-store-cefi-prd-central-element-323112`   |        64,327 |    64,327 | **100.0%** |
| defi        | `instruments-store-defi-prd-central-element-323112`   |       171,200 |   171,200 | **100.0%** |
| tradfi      | `instruments-store-tradfi-prd-central-element-323112` |        11,888 |    11,888 | **100.0%** |
| sports      | `instruments-store-sports-prd-central-element-323112` |     1,224,719 | 1,224,719 | **100.0%** |
| prediction  | `instruments-store-pred-prd-central-element-323112`   |        25,432 |    25,432 | **100.0%** |

All 5 asset_groups are fully filled (this is HIGHER than the CF-8 sports figure of 62.9% cited in "What happened" above
— not reconciled here; possibly a metric-definition difference [CF-8's `.notna()` check over the WHOLE index vs this
audit's captured-only `available_at != ""` check] or genuine state change from concurrent same-day sports work. Either
way, current live IS-side state is clean — no backfill action needed there).

**`strategy-store` bucket (strategy-service write / execution-service read path, `data_type=strategy_instructions`):**
`strategy-store-central-element-323112` is **completely empty** — 0 rows in the entire consolidated index, not just 0
captured. No fill-rate to measure; not a manifest defect, just no production data yet for this shard atom.

**New finding while auditing strategy-service/execution-service call sites (P2 below):**
`StrategyManifestRecorder.record_captured()`
(`strategy-service/strategy_service/engine/core/strategy_manifest.py:107-129`) and
`ExecutionManifestRecorder.record_captured()`
(`execution-service/execution_service/strategy_instructions/manifest.py:106-129`) call UTL `ManifestWriter.add()`
directly — NOT `record_captured()`/`record_captured_from_counts()` — and never pass `available_at=` to `add()` at all.
This is a DIFFERENT, NOT-YET-FIXED bug (the `9c9cdc50` fix only touched `_writer_captured.py`); it won't surface in the
fill-rate numbers above only because the bucket is currently empty, but the first `strategy_instructions` row ever
written will land with `available_at=""` regardless.

**Not-yet-grepped services re-check**: re-grepped `record_captured(` (non-test, non-comment) across alerting-service,
deployment-api, deployment-service, fund-administration-service, greeks-service, trading-agent-service, ml-service,
features-service, unified-trading-system-ui — **0 call sites in every one**. The blast-radius table in "What happened"
above (MTDS/IS/strategy-service/execution-service/MDPS) was already exhaustive; no additional services are affected.

## Recommended next steps (not mine to decide unilaterally — routing to operator/manifest_master owner)

1. ~~**Audit the true blast radius**~~ — DONE, see "Audit Results (2026-07-13)" above. Verdict: **worse than
   sports-only** — every measurable non-sports asset_group on the MTDS/MDPS write path is uniformly 0% filled (not
   partially degraded); instruments-store side is 100% filled; strategy-store is empty (no data yet).
2. **Decide whether a backfill is warranted for non-sports asset_groups** — YES per the audit: defi (3.0M rows), tradfi
   (1.6M rows), sports (377K rows, already covered by the sports-scoped plan), prediction (46K rows) on the MTDS/MDPS
   `market-data-tick` write path are all 0% filled. This is a much larger cross-asset-group backfill program than
   sports-only. Should become its own plan under `manifest_master` (todo P2 below) rather than living in this issue doc.
3. **New captures are now correct** (as of `9c9cdc50`) — no further action needed for rows written after this fix lands
   on `live-defi-rollout`/promotes; this issue is only about the historical backlog.
4. This does NOT block or change `sports_cf8_available_at_backfill_regression_2026_07_13.md`'s own P1 todo (re-attempt
   the sports-scoped full-corpus backfill) — that fix (`f5f15e3a`) is independently sufficient for the `record_empty`/
   `record_failed`/`add()` paths the sports rebuild script uses. This issue doc's fix (`9c9cdc50`) is orthogonal —
   relevant to `record_captured`-based captures, not the rebuild-walk path.

## Todos

- [x] [DATA] P1. Audit current manifest `available_at` fill rate for `capture_status=captured` rows, per asset_group,
      for every service in the blast-radius table above (plus the not-yet-grepped services named in that section) —
      determine whether this is sports-severity or worse elsewhere. (repo: unified-trading-library, all services above)
      — ✅ unified-trading-pm (this doc + `plans/audit/results/available_at_fill_rate_audit_2026_07_13.py`). Verdict:
      WORSE than sports-only (0% uniform across defi/tradfi/sports/prediction on the MTDS/MDPS write path); IS side
      100%; strategy-store empty. See "Audit Results (2026-07-13)" above for full evidence.
- [x] ✅ [DATA] P2. Scope + execute a cross-asset-group backfill plan for the `market-data-tick` `available_at` backlog
      (defi 3.0M rows, tradfi 1.6M rows, prediction 46K rows — sports already covered by
      `sports_cf8_available_at_backfill_regression_2026_07_13.md`) — route through `manifest_master` epic as its own
      plan, NOT this issue doc. Re-derive `available_at` per-row from source data per `AVAILABILITY_AT_SEMANTICS` (same
      approach as the sports rebuild), not a synthetic/estimated fill. (repo: TBD per plan) — **SCOPED, slot 7,
      2026-07-13**: `plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`. Found prediction/tradfi rebuild
      scripts already derive `available_at_envelope` correctly for captured clusters (just needed the library fix, same
      mechanism as the sports rebuild — a `--force` rerun now backfills them); defi has NO existing capture-path
      threading (its rebuild script only calls `record_empty`/`record_failed`, zero `record_captured*` call sites — real
      new engineering work across ~30 per-data_type handlers). Plan phases prediction → tradfi (execute, gated on an
      operator-coordinated maintenance window per the sports Finding 1 cron-collision precedent) then audits + gates
      defi behind an explicit operator go/no-go given the sports CF-8 regression precedent. No production writes made by
      this touch — scoping only, execution is the plan's own todos.
- [x] ✅ [DATA] P3. Fix `StrategyManifestRecorder.record_captured()`
      (`strategy-service/strategy_service/engine/core/strategy_manifest.py:107-129`) and
      `ExecutionManifestRecorder.record_captured()`
      (`execution-service/execution_service/strategy_instructions/manifest.py:106-129`) — neither passes `available_at=`
      to the underlying `ManifestWriter.add()` call, so every `strategy_instructions` manifest row will land with
      `available_at=""` the moment production data starts flowing (the bucket is currently empty, so this hasn't
      surfaced yet). Separate, not-yet-fixed bug — `9c9cdc50` only touched `_writer_captured.py`. (repo:
      strategy-service, execution-service) — **FIXED, slot 3, 2026-07-14**: both recorders now pass
      `available_at=datetime.now(UTC).isoformat()` into `writer.add()` — `strategy_instructions` has no upstream tick
      timestamp to derive from (the strategy engine IS the source), so the honest value is the write-time timestamp, not
      a synthetic/estimated fill. Unit-tested (asserts a non-empty, parseable, tz-aware ISO string reaches
      `writer.add()`, and that `row_count<=0` still routes to `record_empty` without touching `add()`).
      `strategy-service@6514fe87`, `execution-service@05289cb4`. Both repos' `strategy_instructions` buckets are
      currently empty (per this doc's own audit) so no production backfill was needed — this closes the gap before the
      bucket ever receives its first row.
- [x] ✅ [INFRA] P3. Investigate the stale/down manifest consolidator for
      `market-data-tick-cefi-prd-central-element-323112` (consolidated blob age observed 267s→390s and rising against
      the 120s staleness threshold during this audit, 2026-07-13 ~23:29 UTC) — this bucket could not be read via
      `read_availability_index()` (correctly refused the OOM-risk per-VM-shard fallback), so cefi's `available_at` fill
      rate is UNKNOWN, not confirmed-green. (repo: deployment-service, per
      `/codex/05-infrastructure/manifest-consolidator-ssot.md`) — **INVESTIGATED, slot 10 (infra), 2026-07-14. Verdict:
      NOT a current outage; a real, still-open root-cause gap found instead.**
  - **Live health, verified directly (not from logs/cache)**: `uts-prod-manifest-consolidator-market-data-cefi`'s last 8
    Cloud Run executions (checked via the Cloud Run Admin API REST, `google-auth` — `gcloud` is broken on this host,
    same snap-confine `cap_dac_override` issue every prior touch on this host hit) are ALL
    `succeededCount=1, failedCount=None`, firing on a steady `*/1` cron (createTime deltas ~60-70s apart, 11:10-11:17
    UTC today). Direct GCS read of `market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`:
    `blob.updated` age = **7.1s** at check time. The consolidator is healthy and actively writing right now.
  - **Root cause of yesterday's 267-390s reading: NOT the same as the outage this todo's title implies.**
    `/codex/05-infrastructure/manifest-consolidator-ssot.md` already documents (finding 205, 2026-07-12,
    `deployment-api@90ace9f`) that cefi is a legitimate ~60-70s-cadence-but-**86400s**-budget consolidator (matching its
    launchers' own `MANIFEST_CONSOLIDATED_STALENESS_SEC` override) — its blob age naturally swings within that cadence,
    and any reader applying the generic **120s** default sees false "stale" positives roughly 60% of the time. That
    finding fixed `deployment-api`'s cockpit health endpoint (`_AG_STALENESS_BUDGET_SEC: dict[str,int]={"cefi":86400}`
    in `deployment_api/routes/health_consolidator.py`, confirmed via direct grep — the ONLY place that dict exists in
    the fleet).
  - **The gap this touch actually found**: `unified-trading-library`'s `read_availability_index()` — the REAL data-read
    gate the sports audit script (and any production reader) hits, via `_read_slow_path()` in
    `manifest_writer/_read_index.py` calling `_resolve_consolidated_staleness_sec()` in `manifest_writer/_state.py` — is
    **NOT** per-asset-group-aware. It resolves a single global `manifest_consolidated_staleness_sec` config value
    (default 120, per `UnifiedCloudConfig`) with no bucket/asset_group parameter anywhere in the call chain. The
    `deployment-api@90ace9f` fix only ever reached the COCKPIT DISPLAY layer, never this actual read-refusal gate — so
    any process reading cefi manifest data without its OWN environment overriding
    `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` (as cefi's dedicated launchers do) will still intermittently and
    incorrectly raise `ManifestConsolidatorStaleError` on a perfectly healthy consolidator — exactly what the sports
    audit hit on 2026-07-13. This is the higher-stakes gap: a raised error here blocks real reads/audits/backfills, not
    just a UI display.
  - **Follow-up todo filed below** (new engineering — extending the read-path budget resolution to be asset-group-aware
    needs its own review, not a blind port of the cockpit dict into a shared library function many callers depend on) —
    not implemented in this investigate-scoped touch.
- [x] ✅ [INFRA] P2. Make UTL's `read_availability_index()` staleness-refusal gate
      (`_resolve_consolidated_staleness_sec()` in `manifest_writer/_state.py`, consumed by `_read_slow_path()` in
      `manifest_writer/_read_index.py`) asset-group-aware, mirroring `deployment-api@90ace9f`'s already-shipped
      `_AG_STALENESS_BUDGET_SEC` cockpit fix — so a cefi (or any future daily-batch-cadence) bucket read doesn't
      intermittently false-positive-refuse against the generic 120s default the way the sports audit hit on 2026-07-13.
      Needs a bucket→asset_group resolution path threaded into `read_availability_index(bucket, ...)` (it currently only
      takes a raw bucket string) — a design decision, not a batch-size judgment call, per this doc's own precedent for
      similar write-path fixes. (repo: unified-trading-library) — unified-trading-library@084e62f0. New module
      `manifest_writer/_staleness_budget.py` (split out — `_state.py` was already at 897/900 lines) holds
      `asset_group_from_bucket()` (best-effort token match against the closed cefi/defi/tradfi/sports/prediction
      vocabulary) + `AG_STALENESS_BUDGET_SEC` (intentionally duplicated from deployment-api's dict — cross-repo import
      is the wrong dependency direction). `_resolve_consolidated_staleness_sec()` threads an optional `bucket` parameter
      through its 5 call sites (`assert_consolidator_healthy` + the 3 `read_availability_index` staleness checks);
      `bucket=None` (every existing zero-arg caller, incl. deployment-api's own default lookup) preserves the prior
      global-only behaviour unchanged. 4 new unit tests, including two end-to-end `assert_consolidator_healthy`
      regressions — one proving a 600s-stale cefi bucket now correctly no-ops (reproduces the exact false-positive on
      pre-fix code, verified via git-stash revert), one proving a same-age non-cefi bucket still correctly raises. Full
      `quality-gates.sh` green + sentinel-verified, shipped via `quickmerge --agent`.
