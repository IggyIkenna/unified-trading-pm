---
doc_type: audit-result
title: "Data-pipeline reconciliation — cefi (2026-08-18), raw-tick layer, Tier-1 only"
summary: >-
  Scheduled daily cefi spot-check (cefi_reconciliation_auditor role, dispatch agt-dea4f2, slot 20), third
  consecutive daily run since the 2026-08-16 restart. Phase 0: both cefi buckets reachable; instruments-store
  consolidator healthy/no-op; market-data consolidator's instantaneous state looks nominal (a successful
  consolidated write completed at 02:13:57Z, current lock only ~11min old at check time) BUT
  consolidator_stall_state.json's streak counter escalated sharply again, 10 -> 89, since yesterday's already-P1
  escalation — mechanism not diagnosable at Tier-1, flagged for an infra-level look. Census (§3f): all 7 venue
  M-C drift entries and the depth_of_book_10 self-heal are BYTE-IDENTICAL to yesterday (stable, no regression).
  Unlike yesterday's run (which read a stale/replayed snapshot), today's manifest genuinely advanced: total rows
  grew 29,938,146 -> 30,001,825 (+63,679), concentrated almost entirely in instrument_type=FUTURE (+63,346) and
  OPTION (+333) while PERPETUAL/SPOT_PAIR/COMBO stayed exactly flat. NEW finding this run: today's (2026-08-18)
  honest-coverage cefi by_asset_group rollup is BYTE-IDENTICAL to yesterday's (2026-08-17) rollup in every
  captured/attempted_failed/expected_unattempted/coverage_pct field despite the underlying manifest's real
  growth in the same window — plausibly (not confirmed) the same consolidator-stall root cause feeding a stale
  snapshot into the coverage compute; formula itself re-verified correct against the (frozen) published numbers.
  No code fix shipped this run — every finding is either carried-unchanged, a confirmed-stable self-heal, or a
  todo needing an infra-level look.
status: pass
nature: record
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm, unified-api-contracts, market-tick-data-service]
scope: [engineer, admin]
tags:
  [
    reconciliation,
    canonicalisation,
    census,
    cefi,
    honest-coverage,
    consolidator-stall-escalation,
    honest-coverage-freeze,
    bybit-futures-selfheal-stable,
    depth-of-book-10-selfheal-stable,
    binance-delivery-carried,
    bare-okx-carried,
  ]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    honest-coverage-model,
    data_pipeline_reconciliation_cefi_2026_08_17,
  ]
created: 2026-08-18
resulting_plan:
lib_version: "market-tick-data-service@HEAD (slot 20), unified-api-contracts@HEAD (audited only; no code changes shipped this run)"
doc_versions_checked:
audited_scope:
  "asset_group=cefi, layer=raw-tick, PROD (-prd-) buckets only, read-only, Phase 0 + census (Tier-1) +
  honest-coverage verification per the cefi_reconciliation_auditor role (subset of /data-pipeline-reconciliation) —
  daily scheduled spot-check, not a full campaign. Third consecutive daily run (prior: 2026-08-16, 2026-08-17)."
date: 2026-08-18
auditor: "cefi_reconciliation_auditor (scheduled role, slot 20, dispatch agt-dea4f2)"
parent_epic: security_and_cross_cutting_master
severity: P1
skill: data-pipeline-reconciliation
run_date: 2026-08-18
generated_at: 2026-08-18T02:35:00+00:00
---

# Data-pipeline reconciliation — cefi (2026-08-18), raw-tick layer, Tier-1 only

**Fully read-only this run** — no GCS writes, no manifest writes, no deletes, no VM launches, no code changes.
Daily scheduled `cefi_reconciliation_auditor` spot-check: Phase 0 (reachability + freshness) + the §3f
distinct-value census + honest-coverage formula/freshness verification. Third consecutive daily run since the
2026-08-16 restart (predecessors: 2026-08-16, 2026-08-17).

## 0. Phase-0 reachability + freshness

| bucket | reachable | consolidator lock | last write to `availability_index.parquet` | verdict |
| --- | --- | --- | --- | --- |
| `market-data-tick-cefi-prd-central-element-323112` | yes | **HELD** since 2026-08-18T02:21:07.21Z (instance `1-009632fc`, ~11min elapsed at check ~02:32Z) | 2026-08-18T02:13:57.71Z (generation `1787019237694916`, size 443,800,429 bytes) | instantaneous state nominal; see stall-streak finding below |
| `instruments-store-cefi-prd-central-element-323112` | yes | not locked | 2026-08-18T02:00:53.22Z (generation `1787018453204347`, 1 shard scanned, 0 changed) | healthy, consistent with every prior run |

**Environment note**: both `GCP_PROJECT_ID` and `AWS_ACCOUNT_ID` resolved correctly from the start this run — no
repeat of the 2026-08-16 skill-doc gap.

### Consolidator — instantaneous state nominal, but stall-streak counter escalated sharply again

The sequence reconstructed from the three status reads this run: a check at **02:06:36Z** found the index
locked and no-op'd (`error_reason="locked"`, `duration_ms=23,606.2` ≈ 24s) → a consolidator run **completed
successfully** and wrote fresh output at **02:13:57Z** (~7min later) → a **new** lock was acquired at
**02:21:07Z** (instance `1-009632fc`) and was still held ~11min later at my check (~02:32Z). None of this, taken
alone, looks like a multi-hour hang the way yesterday's 6.5h run did — the most recent full cycle (lock → write)
took well under 15 minutes.

**However**, `_index/consolidator_stall_state.json` reads `streak=89, baseline_shards=7851` — **escalated again
from yesterday's `streak=10`** (which was itself escalated from the 2026-08-16 baseline of `streak=0`). An 8.9x
jump in one day, on top of an already-P1-escalated finding, while the *instantaneous* snapshot looks healthy is
a genuine tension this run cannot resolve at Tier-1: either the streak counter is accumulating faster because
checks are running more frequently now, or the underlying reliability problem is measurably worse than
yesterday's framing captured. **Not diagnosed further this run** (needs the same infra-level look yesterday's
report already called for, now with added urgency given the trend direction) — see §6 for the carried/escalated
todo. `phantom_audit_latest.json`: `phantom_count=0`, `generated_at=2026-07-27T17:38:18Z` — **22 days stale**
(was 21 on 08-17), carried, escalating by 1 day, zero remediation for 3+ weeks.

`_index/reprobe_audit_latest.json` (market-data): still `generated_at=2026-08-17T09:01:31.62Z` (unchanged from
yesterday's read at that same timestamp) — **not yet regenerated today** as of the ~02:3x UTC check window. This
is the SAME "too early to conclude" situation as every prior run: if the cadence is genuinely anchored near
09:00 UTC (consistent with the one successful 08-17 09:01 generation now on record), a check at 02:3x UTC is
still ~6.5h before the next expected run. Confirming the daily cadence needs a check dispatched between
09:00-12:00 UTC — still deferred, third run running into the same scheduling mismatch (§6).

`instruments-store-cefi` still has **no** `phantom_audit_latest.json` / `reprobe_audit_latest.json` (both 404,
confirmed via direct read) — standing declared coverage gap, unchanged.

**AWS cross-check**: both AWS-side mirror buckets (`market-data-tick-cefi-prd-427895769566`,
`instruments-store-cefi-prd-427895769566`) confirmed reachable and **completely empty** (`top_level_count=0` for
both via a direct delimiter-scoped listing) — unchanged from every prior run.

## 1. Census — venue axis (M = manifest distinct, C = UAC `VENUES_BY_ASSET_GROUP["cefi"]`, 25 venues)

Read via UTL's `read_availability_index(bucket, columns=[...])` (the same SSOT reader
`get_axis_value_census`/every data-status endpoint uses), one axis (2 columns: axis + `capture_status`) at a
time, wrapped in `scripts/dev/run-bounded-analysis.sh --mem-cap 8G`. Total manifest rows read: **30,001,825** —
**+63,679 vs yesterday's 29,938,146**. Unlike the 2026-08-16→08-17 comparison (which found a byte-identical,
stale-replayed snapshot), this run's snapshot is **genuinely fresh**: see §2 for exactly where the growth landed.

- **C − M (orphaned declarations)**: **empty** — all 25 UAC-declared cefi venues have manifest presence.
- **M − C (drift)** — **7 entries**, and every single one is **byte-identical in both row count AND
  capture_status composition to yesterday's report** — a clean, stable carry, zero regression:

  | venue | rows | capture_status breakdown (today) | vs. yesterday |
  | --- | --- | --- | --- |
  | `BYBIT-FUTURES` | 10,268 | 100% `empty_confirmed` | **identical** (the 08-16 self-heal remains fully stable) |
  | `OKX` (bare) | 5,225 | 100% `attempted_failed` | **identical**, carried since 08-04 |
  | `BINANCE-DELIVERY` | 4,838 | 578 `attempted_failed` + 5 `captured` + 4,255 `empty_confirmed` | **identical** |
  | `OKEX-FUTURES` | 36 | 100% `empty_confirmed` | **identical** |
  | `CRYPTOFACILITIES` | 10 | 100% `empty_confirmed` | **identical** |
  | `OKX-OPTIONS` | 2 | 100% `attempted_failed` | **identical** |
  | `KALSHI_PERP` | 2 | 100% `attempted_failed` | **identical** |

## 2. Census — instrument_type + data_type + chain axes

- **instrument_type** — today's growth is concentrated almost entirely here:
  - Case-only variants (ruled C2a `migration_pending`, suppressed, not findings): `PERPETUAL` 19,193,915
    (**unchanged, byte-identical to 08-17**) / `SPOT_PAIR` 8,257,788 (**unchanged**) / `COMBO` 31,557
    (**unchanged**) / `FUTURE` **1,663,935** (was 1,600,589 — **+63,346**) / `OPTION` **282,535** (was 282,202 —
    **+333**). `63,346 + 333 = 63,679` — accounts for **exactly** the total manifest row growth this run
    measured (§1). Today's active capture/reclassification activity landed entirely in FUTURE/OPTION-typed
    shards; PERPETUAL/SPOT_PAIR/COMBO shards saw zero net change since yesterday's snapshot. Not independently
    attributed to a specific venue this run (would need a 3-column venue×instrument_type×capture_status read,
    out of this role's Tier-1 scope) — plausibly normal date-rollover capture across the several FUTURE-typed
    venues, but flagged as an observation given it coincides with the consolidator-stall trend (§0).
  - Lowercase variants (still C2a `migration_pending`, suppressed): `perpetual` 38,083 (369 `attempted_failed` +
    26,737 `captured` + 10,977 `empty_confirmed`), `future` 1,191 (100% `captured`), `spot_pair` 12 (100%
    `captured`). `combo`/`option` (lowercase): **zero** manifest presence, confirming yesterday's refinement
    still holds today — the manifest remains 100% `COMBO`/`OPTION` (uppercase-only) for those two values.
  - **NULL vs `""` split** (re-verified via the same NULL/blank-distinguishing read yesterday's report
    self-corrected to): **NULL = 162,190** rows (29,163 `attempted_failed` + 133,027 `empty_confirmed`), **`""` =
    157,337** rows (100% `empty_confirmed`) — **both byte-identical to yesterday's figures**, unchanged.
  - **Case-insensitive drift, carried**: `'index'` (3,910 rows, 100% `captured`) — DERIBIT `volatility_index`
    registry gap, count unchanged since every prior run, still undeclared in any cefi registry (existing P4
    todo).
- **data_type** (vs 9 canonical from `DATA_TYPES_BY_ASSET_GROUP["cefi"]`):
  - 5 stray `ohlcv_{15m,15s,1d,1h,5m}` @ 2 `captured` rows each (10 total) — carried, byte-identical to every
    prior report.
  - **`depth_of_book_10`** — 39,120 rows (11,914 `captured` + 27,206 `empty_confirmed`, zero `attempted_failed`)
    — **byte-identical to yesterday's post-self-heal figures**: the 2026-08-16 self-heal (§3, prior report)
    remains fully durable, no reversion. Still a real, undeclared registry gap (genuinely captured data from the
    shipped `bybit_futures_book_ticker_ws.py` connector, never added to `DATA_TYPES_BY_ASSET_GROUP["cefi"]`) —
    existing P2 todo carried unchanged.
  - **`perp_daily_ctx`** — 7 `captured` rows, byte-identical to yesterday, carried unchanged (existing P4 todo).
- **chain**: 100% blank (30,001,825 / 30,001,825, 1 distinct value) — unchanged, the 2026-07-28 chain-axis heal
  continues to hold.
- **quote_asset**/**margin_type**: non-blank rows now 5,105,270 / 5,315,193 respectively — both grew by the
  identical **+61,709** since yesterday's cited figures (5,043,561 / 5,253,484), consistent with the established
  "ongoing MDPS candle-row capture" pattern (same vocabulary, no drift) — not investigated further, per
  established practice.

## 3. Honest-coverage — formula re-verified correct, but the rollup itself did NOT advance (new finding)

- **Today's (2026-08-18) `coverage.json` EXISTS** — generated `2026-08-18T00:49:39.92Z`, the **third consecutive
  day** landing in the ~00:43-00:49 UTC window (08-16 `00:43:09Z`, 08-17 `00:49:33Z`, 08-18 `00:49:39Z`) —
  extends yesterday's "three consecutive successful days" observation to **four**; the post-08-15-fix cadence
  continues to look stable. Date-dir existence also confirmed for 08-14 through 08-18 (all present via direct
  per-date probes).
- **Formula re-verification** (per role scope), against the fresh 08-18 file: `by_asset_group.cefi`:
  `captured=9,842,980`, `empty_confirmed=6,392,460`, `attempted_failed=892,679`, `expected_unattempted=10,894,199`,
  `total=28,022,318`, published `coverage_pct=45.51`. Independently re-derived:
  `9,842,980 / (9,842,980 + 892,679 + 10,894,199) = 9,842,980 / 21,629,858 = 45.508…%` — matches published
  `45.51` exactly. **No formula drift.**
- **NEW finding — the 08-18 rollup is byte-identical to the 08-17 rollup in every `by_asset_group.cefi` field
  except `storage_bytes_tb_mtds`** (47.1488 → 47.3726 TB, a small, plausible continued-growth delta):
  `captured`/`empty_confirmed`/`attempted_failed`/`expected_unattempted`/`total`/`coverage_pct`/
  `all_shards_coverage_pct`/`layer1_completeness_pct` are **all identical, to the byte**, between the two days'
  files. This is unexpected given §1-§2 measured the underlying raw-tick manifest growing by +63,679 rows
  (concentrated in FUTURE/OPTION instrument_type shards) in the SAME 08-17→08-18 window. **Plausible but NOT
  independently confirmed root cause**: the same consolidator-stall pattern (§0, `streak` 10→89) may be feeding
  the honest-coverage compute job a snapshot that itself didn't materially advance between the two days' ~00:4x
  UTC runs — the coverage job's own input-snapshot timestamp was not inspected this run (would require reading
  its compute code/logs, out of this role's Tier-1 census scope). Flagged as a new P1 todo (§6), explicitly tied
  to the consolidator finding rather than treated as independent, since both surfaced in the same run and share
  a plausible common cause.
- **cefi layer_1**: not present under the `layer_1` key in this rollup shape this run (`layer_1.cefi` returned
  empty `{}` when read directly) — the `layer1_completeness_pct=94.52` figure lives inside `by_asset_group.cefi`
  instead (matches yesterday's cited `94.52` exactly, so the figure itself is unchanged and not itself a new
  concern) — noted as a schema-navigation correction for whoever next scripts against this rollup, not a
  finding about the data.

## 4. What this run does NOT cover (declared, per the role's Tier-1 scope)

- No machine-oracle path-structure sweep, no id-form/schema Tier-1 sampled check or Tier-2 VM validation, no
  orphan-object sweep / delete suggestions — never this role.
- No batch-layer GCS-vs-manifest delimiter-descent spot-check this cycle (same as every prior run).
- Did not independently investigate `reprobe_audit_latest.json`'s cadence (still showing 08-17's generation as
  of this check window — third consecutive run landing too early in the UTC day to conclude either way; see the
  explicit recommendation in §6 to dispatch a check between 09:00-12:00 UTC).
- Did not diagnose the consolidator stall-streak escalation's root cause (§0), nor the honest-coverage rollup
  freeze's root cause (§3) — both flagged as todos, not chased further; genuinely need an infra-level look this
  role cannot give at Tier-1.
- Did not attribute the FUTURE/OPTION instrument_type growth (§2) to a specific venue.
- Did not chase `perp_daily_ctx` (7 rows) or the older 08-03/06/07/08 honest-coverage date-dir gaps (not
  re-checked this run; no new information).
- Did not identify which launcher/registry entry still probes `BINANCE-DELIVERY` (carried, still unresolved).

## 5. No code fix this run

Every finding this run is either a carried-unchanged / confirmed-stable observation, or a new todo needing an
infra-level look beyond this role's narrowly-scoped-fix carve-out (the consolidator stall-streak escalation and
the honest-coverage freeze are both genuinely undiagnosed at Tier-1, not "well-understood" fixes).

## 6. Todos

- [ ] [INFRA] P1. **Market-data consolidator stall-streak counter escalated sharply again, 10 → 89 (3rd
      consecutive day of this finding, worsening)** — the *instantaneous* state at check time looked nominal (a
      successful consolidated write completed 2026-08-18T02:13:57Z, ~7min after the prior locked no-op, and the
      current lock was only ~11min old at check time) but `consolidator_stall_state.json`'s `streak` field
      jumped 8.9x since yesterday's already-P1-escalated `streak=10`. Mechanism not diagnosable at Tier-1 —
      needs an infra-level look at what `streak` actually counts (consecutive-locked-encounters at some polling
      interval?) and whether that interval itself changed, or whether the real underlying reliability problem is
      genuinely worse. Repo: market-tick-data-service / deployment-service.
- [ ] [DATA] P1. **NEW — honest-coverage cefi `by_asset_group` rollup byte-identical 08-17→08-18 despite real
      underlying manifest growth in the same window** — `captured`/`attempted_failed`/`expected_unattempted`/
      `coverage_pct` etc. are all identical between the two days' `coverage.json` files, while §1-§2 measured the
      raw-tick manifest growing +63,679 rows (FUTURE/OPTION instrument_type) in the same 08-17→08-18 window.
      Formula itself re-verified correct against the (frozen) numbers — this is a rollup-freshness issue, not a
      formula bug. Plausibly tied to the consolidator-stall finding above (same run, same window, no other
      explanation identified) but not independently confirmed — the honest-coverage compute job's own input-
      snapshot source/timestamp was not inspected this run. Repo: instruments-service (or wherever the
      honest-coverage compute job lives — not confirmed this run).
- [ ] [DATA] P2. **BINANCE-DELIVERY venue drift (4,838 rows, carried unchanged, byte-identical to 08-17)** —
      includes 578 `attempted_failed` + 5 `captured` + 4,255 `empty_confirmed`; zero rows ever reached `captured`
      via a canonical path per prior runs' investigation. Candidate for the same "deregister dormant legacy
      alias" fix class as the 2026-08-04 bare-OKX precedent — still needs the launcher/registry grep to confirm
      which config still probes it (not identified with enough confidence in this or any prior run). Repo:
      market-tick-data-service / unified-api-contracts.
- [ ] [DATA] P2. **`depth_of_book_10` data_type registry gap (39,120 rows, 11,914 genuinely `captured`, carried,
      self-heal confirmed durable)** — produced by the real, shipped `bybit_futures_book_ticker_ws.py`
      connector, undeclared in `DATA_TYPES_BY_ASSET_GROUP["cefi"]`. Same shape as the carried
      `instrument_type=index` gap below — decide add-vs-document; an addition needs its downstream consumers
      (MVP predicate, schema contract) checked in the same change per the entity-rename/registry-migration rule.
      Repo: unified-api-contracts.
- [ ] [INFRA] P3. **`phantom_audit` for cefi now 22 days stale** (was 21 on 08-17, zero remediation for 3+
      weeks) — carried, escalating by 1 day again. Repo: instruments-service.
- [ ] [DATA] P3. **CRYPTOFACILITIES (10 rows) / OKEX-FUTURES (36 rows)** — both benign (100% `empty_confirmed`,
      legacy delisted-instrument handling per prior runs), byte-identical to every prior report. Candidate for
      the accepted-exception list rather than continued M−C reporting. Repo: unified-api-contracts.
- [ ] [DATA] P4. **`instrument_type=index` (3,910 rows, DERIBIT/volatility_index, carried, byte-identical)** —
      still undeclared in any cefi registry. Repo: unified-api-contracts.
- [ ] [DIAG] P4. **`perp_daily_ctx` data_type (7 `captured` rows, carried, byte-identical, still unexplored)** —
      confirm in-scope or expected-pilot. Repo: unified-api-contracts.
- [ ] [DIAG] P4. **`reprobe_audit_latest.json` daily-cadence STILL not confirmable — 3rd consecutive run hitting
      the same scheduling mismatch** — this role's dispatch window (~00:1x-02:3x UTC) is consistently ~6.5h+
      before the observed single successful generation timestamp (08-17 09:01 UTC). Recommend dispatching one
      check specifically between 09:00-12:00 UTC to actually confirm or refute the daily cadence, rather than
      continuing to carry this as "too early" indefinitely. Repo: market-tick-data-service / instruments-service.

## Progress Log

- **cefi_reconciliation_auditor 2026-08-18** [dispatch agt-dea4f2, slot 20]: Phase 0 + §3f census + honest-coverage
  verification complete, read-only. Consolidator stall-streak escalation (10→89) and a new honest-coverage
  rollup-freeze finding are this run's headline items, both filed as P1 todos tied to the same likely root
  cause. All 7 venue M-C drift entries + the depth_of_book_10 self-heal confirmed byte-identical/stable vs
  2026-08-17. No code fix shipped.
