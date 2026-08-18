---
doc_type: audit-result
title: "Data-pipeline reconciliation — cefi (2026-08-17), raw-tick layer, Tier-1 only"
summary: >-
  Scheduled daily cefi spot-check (cefi_reconciliation_auditor role, dispatch agt-901c67, slot 31), second
  consecutive daily run after the 2026-08-16 restart. Phase 0: both cefi buckets reachable; instruments-store
  consolidator healthy/no-op; market-data consolidator shows a CONFIRMED multi-hour stall pattern — the lock from
  2026-08-16T16:31:23Z (flagged as "an observation, not yet a finding" in yesterday's report) was still held at
  2026-08-17T00:01:08Z (>=7.5h, vs a ~27min baseline run), `consolidator_stall_state.json` streak escalated from 0
  to 10, and the consolidated index my census read (`availability_index.parquet`, generation timestamp
  2026-08-16T23:11:06Z) reflects an unusually long (~6.5h) completed run sandwiched between that stuck lock and a
  fresh lock (instance 1-7ebc7e39) acquired 2026-08-17T00:06:27Z and still held at check time — escalated to a P1
  todo per yesterday's own stated upgrade condition. Census (§3f): all 7 venue M-C drift entries and all 7 data_type
  M-C drift entries are byte-identical in ROW COUNT to 2026-08-16 (confirms same underlying snapshot lineage), but
  two entries tied to the already-closed `cefi_queue_mode_tier3_sentinel_false_empty_confirmed_2026_08_16.md`
  incident (BYBIT-FUTURES venue, 10,268 rows; `depth_of_book_10` data_type's 4,038 attempted_failed rows) have now
  fully transitioned to `empty_confirmed`/`SOURCE_RETURNED_ZERO` — consistent with, and a direct confirmation of,
  that incident's own predicted self-healing retry cycle (not independently verified as the CORRECT terminal
  classification for every shard, but structurally coherent, not a regression). instrument_type/chain axes match
  the established baseline exactly, with one refinement: of the 5 C2a-suppressed uppercase/lowercase pairs, only
  `combo` and `option` (lowercase) have ZERO manifest presence at all (100% uppercase-only today), unlike
  perpetual/spot_pair/future which are genuinely case-mixed — a more precise measurement than prior reports'
  blanket phrasing, still correctly suppressed as migration_pending. Honest-coverage: today's (08-17) rollup has
  not generated yet as of the 00:1x-00:2x UTC check window (expected, not yet due — the observed cadence is
  ~00:43 UTC); freshest available remains 2026-08-16T00:43:09Z, re-confirmed byte-identical to yesterday's
  already-verified figures (cefi 45.59% coverage, 94.52% layer_1 completeness, formula matches
  honest-coverage-model.md exactly). No code fix shipped this run — every finding is either carried-unchanged, a
  confirmed self-heal (no action needed), or a todo needing an operator/infra look (consolidator) or further
  investigation (BINANCE-DELIVERY, carried from prior runs).
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
    bybit-futures-selfheal-confirmed,
    depth-of-book-10-selfheal-confirmed,
    binance-delivery-carried,
    bare-okx-carried,
  ]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    honest-coverage-model,
    data_pipeline_reconciliation_cefi_2026_08_16,
    cefi_queue_mode_tier3_sentinel_false_empty_confirmed_2026_08_16,
  ]
created: 2026-08-17
resulting_plan:
lib_version: "market-tick-data-service@HEAD (slot 31), unified-api-contracts@HEAD (audited only; no code changes shipped this run)"
doc_versions_checked:
audited_scope:
  "asset_group=cefi, layer=raw-tick, PROD (-prd-) buckets only, read-only, Phase 0 + census (Tier-1) +
  honest-coverage verification per the cefi_reconciliation_auditor role (subset of /data-pipeline-reconciliation) —
  daily scheduled spot-check, not a full campaign. Second consecutive daily run (prior: 2026-08-16)."
date: 2026-08-17
auditor: "cefi_reconciliation_auditor (scheduled role, slot 31, dispatch agt-901c67)"
parent_epic: security_and_cross_cutting_master
severity: P1
skill: data-pipeline-reconciliation
run_date: 2026-08-17
generated_at: 2026-08-17T00:25:00+00:00
---

# Data-pipeline reconciliation — cefi (2026-08-17), raw-tick layer, Tier-1 only

**Fully read-only this run** — no GCS writes, no manifest writes, no deletes, no VM launches, no code changes.
Daily scheduled `cefi_reconciliation_auditor` spot-check: Phase 0 (reachability + freshness) + the §3f
distinct-value census + honest-coverage formula/freshness verification. Second consecutive daily run since the
2026-08-05 origin (2026-08-09→08-16 had a 7-day gap; today continues the now-daily cadence started 2026-08-16).

## 0. Phase-0 reachability + freshness

| bucket | reachable | consolidator lock | last write to `availability_index.parquet` | verdict |
| --- | --- | --- | --- | --- |
| `market-data-tick-cefi-prd-central-element-323112` | yes | **HELD** since 2026-08-17T00:06:27.35Z (instance `1-7ebc7e39`, ~14min elapsed at last check 00:20:48Z) | 2026-08-16T23:11:06.12Z (generation `1786921866108814`, size 420,631,019 bytes) | see stall finding below |
| `instruments-store-cefi-prd-central-element-323112` | yes | not locked | n/a (no-op, 1 shard scanned, 0 changed) | healthy, consistent with every prior run |

**Environment note**: both `GCP_PROJECT_ID` and `AWS_ACCOUNT_ID` were set correctly from the start this run (the
2026-08-16 report's skill-doc fix holds — no repeat of that gap).

### Consolidator stall — CONFIRMED escalation from yesterday's "observation, not yet a finding"

Yesterday's report explicitly flagged: *"The market-data lock's ~65min-and-counting duration... [is] Not
independently reverified as complete by the time this report was written — if the lock is still held on tomorrow's
run, that would upgrade this from an observation to a real stall finding."* Measured today:

- The lock acquired **2026-08-16T16:31:23Z** (instance `1-02a1a35c`, cited in yesterday's report) was **still held
  at 2026-08-17T00:01:08Z** — a consolidator run attempt at that exact timestamp found the index locked and
  immediately no-op'd (`_index/latest.json`: `shards_scanned=0, rows_in=0, no_op=true, error_reason="locked"`,
  `duration_ms=28738.7`). That is **>=7.5 hours** the 16:31:23Z lock was held, versus the ~27-minute baseline
  (`duration_ms=1,597,353` on the last-known-good completed run cited in the 08-16 report).
- `_index/consolidator_stall_state.json`: `streak=10, baseline_shards=7851` — **escalated from yesterday's
  `streak=0`**. The system's own stall-streak counter registered this as anomalous across 10 consecutive checks
  (yesterday's `streak=0` was explicitly read as "a normal in-flight state, not a stall signal" — a `streak=10`
  today is not that).
- However, the underlying object was NOT stuck forever: `availability_index.parquet` itself carries
  `time_created=2026-08-16T23:11:06Z` — a consolidator run DID complete and write fresh output at 23:11:06,
  ~6.5 hours after the 16:31:23Z lock was acquired (vs. the ~27min baseline — an anomalously long run, not a
  permanent hang). A **second** run attempt then hit "locked" at 00:01:08Z (see above), and a **third**, currently
  in-progress run (instance `1-7ebc7e39`) acquired a fresh lock at 00:06:27Z and was still running at last check
  (~14min in — not concerning on its own; well within normal range).
- **Net effect on this run's census**: the manifest snapshot my census reads below is the 23:11:06Z output — about
  1h13min after yesterday's report was generated (17:57:32Z) and ~1h10-20min stale relative to this check. The
  total row count (29,938,146, identical to yesterday's 29,938,146) confirms this is the SAME underlying corpus,
  not a fresh ingest — consistent with "an unusually long run that re-merged the same input, not new data."

**Assessment**: not a data-loss or correctness issue (the run did complete), but a confirmed, 2-consecutive-day
reliability anomaly on the core cefi consolidation path (a ~6.5h run where baseline is ~27min, plus a stall-streak
counter that escalated 0→10) — upgraded to a **P1 todo** (§6) per yesterday's own stated escalation condition.
Possibly related to the high manifest churn noted yesterday (a live incident, its fix, two manifest migrations,
and a VM relaunch all landing in the ~19h window before yesterday's check) and/or to
`plans/active/issues/cefi_tardis_date_serial_barrier_still_open_2026_08_16.md` if that concerns the same backfill
contention — not cross-checked this run (out of Tier-1 census scope); flagged for the next investigator.

- `_index/phantom_audit_latest.json` (market-data): `phantom_count=0`, `generated_at=2026-07-27T17:38:18Z` — **21
  days stale** (was 20 on 08-16) — carried, escalating by 1 day, zero remediation, unchanged P3 todo.
- `_index/reprobe_audit_latest.json` (market-data): still `generated_at=2026-08-16T09:00:49.76Z` (unchanged from
  yesterday's read) — **not yet regenerated today** as of the 00:1x-00:2x UTC check window. Too early to read as a
  cadence break: if this file follows a ~24h cadence anchored near its last generation time, it is not yet due.
  Genuinely confirming the daily cadence needs a later-in-the-day check (deferred, per yesterday's own todo).
- `instruments-store-cefi` still has **no** `phantom_audit_latest.json` / `reprobe_audit_latest.json` (both
  absent) — standing declared coverage gap, unchanged.

**AWS cross-check**: both AWS-side mirror buckets (`market-data-tick-cefi-prd-427895769566`,
`instruments-store-cefi-prd-427895769566`) confirmed reachable and **completely empty** via a direct S3
`list_objects_v2` call (`KeyCount=0`, `IsTruncated=False` for both) — unchanged from every prior run.
(Methodology note: an initial GCS-client probe against these AWS bucket names 404'd, as expected — that was a
same-script labeling artifact of probing an AWS bucket name via the GCS API, not a real reachability signal; the
S3-native check above is the authoritative one, consistent with precedent.)

## 1. Census — venue axis (M = manifest distinct, C = UAC `VENUES_BY_ASSET_GROUP["cefi"]`, 25 venues)

Read via pyarrow native `GcsFileSystem` + `pyarrow.parquet.read_table`, one axis (2 columns: axis + capture_status)
at a time, wrapped in `scripts/dev/run-bounded-analysis.sh --mem-cap 6G`. Total manifest rows read: 29,938,146 —
**byte-identical to yesterday's total**, confirming the same snapshot lineage discussed in §0.

- **C − M (orphaned declarations)**: **empty** — all 25 UAC-declared cefi venues have manifest presence.
- **M − C (drift)** — **7 entries**, row counts byte-identical to 2026-08-16 for all 7; two have a materially
  different `capture_status` composition (see below):

  | venue | rows | capture_status breakdown (today) | character |
  | --- | --- | --- | --- |
  | `BYBIT-FUTURES` | 10,268 | **100% `empty_confirmed`**, `error_reason=SOURCE_RETURNED_ZERO` (uniform) | **CARRIED venue-name drift, but status SHIFTED — see §3** (was 10,256 `attempted_failed` + 12 `empty_confirmed` yesterday) |
  | `OKX` (bare) | 5,225 | 100% `attempted_failed` | carried, count identical since 08-04 |
  | `BINANCE-DELIVERY` | 4,838 | 578 `attempted_failed` + 4,255 `empty_confirmed` + 5 `captured` | carried, count identical, still-open P2 todo (root-cause site not yet identified) |
  | `OKEX-FUTURES` | 36 | 100% `empty_confirmed` | carried, benign (legacy pre-rebrand OKX brand name; `EXPECTED_INSTRUMENT_DELISTED` per prior runs, not re-derived this run) |
  | `CRYPTOFACILITIES` | 10 | 100% `empty_confirmed` | carried, benign (legacy Kraken-derivatives brand name) |
  | `OKX-OPTIONS` | 2 | 100% `attempted_failed` | carried, count identical |
  | `KALSHI_PERP` | 2 | 100% `attempted_failed` | carried, count identical |

## 2. Census — instrument_type + data_type + chain axes

- **instrument_type** (12 distinct manifest values found via this run's null/blank-collapsing groupby — corrected
  to 13 after a targeted re-check distinguishing NULL from empty-string, matching yesterday's split exactly: see
  methodology note below):
  - Case-only variants (`PERPETUAL` 19,193,915 / `SPOT_PAIR` 8,257,788 / `FUTURE` 1,600,589 / `OPTION` 282,202 /
    `COMBO` 31,557 — all row counts byte-identical to 2026-08-16) are the ruled C2a `migration_pending` casing
    axis — suppressed, not findings.
  - **Refinement over prior reports' phrasing (measured, not assumed)**: of these 5 pairs, only 3
    (`perpetual`/`spot_pair`/`future`) are genuinely case-**mixed** in the manifest today (both spellings present).
    `combo` and `option` (lowercase) have **zero** manifest presence — the manifest is 100% `COMBO`/`OPTION`
    (uppercase-only) for those two values, which is exactly why they appear in this axis's C−M set (`['combo',
    'option']`) rather than the M−C set. Still correctly suppressed under C2a migration_pending either way — no
    finding — but the more precise split is worth recording for whoever eventually plans the D1 migration cutover.
  - **Methodology note**: my first pass collapsed NULL and empty-string (`""`) instrument_type values into one
    bucket, printing a merged count that (due to a same-key-overwrite artifact, not a data issue) understated the
    combined population. A follow-up targeted read separated them precisely: **NULL = 162,190 rows**, **`""` =
    157,337 rows**, combined **319,527** — byte-identical to yesterday's separately-itemized `None` (162,190) +
    blank (157,337) figures. No data drift; a self-caught and corrected read-methodology gap in this run's own
    script, recorded per the measurement-claims-discipline rule rather than silently papered over.
  - **Case-insensitive drift, carried**: `'index'` (3,910 rows, 100% `captured`) — DERIBIT `volatility_index`
    registry gap, count unchanged since every prior run, still undeclared in any cefi registry (existing P4 todo).
- **data_type** (16 distinct manifest values vs 9 canonical from `DATA_TYPES_BY_ASSET_GROUP["cefi"]`):
  - 5 stray `ohlcv_{15m,15s,1d,1h,5m}` @ 2 `captured` rows each (10 total) — carried, byte-identical to every
    prior report.
  - **`depth_of_book_10`** — 39,120 rows, but **capture_status composition SHIFTED since yesterday**: today reads
    27,206 `empty_confirmed` + 11,914 `captured` (no `attempted_failed` remaining); yesterday read 11,914
    `captured` + 23,168 `empty_confirmed` + 4,038 `attempted_failed`. `27,206 − 23,168 = 4,038` — **exactly** the
    prior `attempted_failed` count, i.e. those rows transitioned cleanly to `empty_confirmed`. See §3 — this is the
    SAME pattern as BYBIT-FUTURES above, both tied to the same closed incident. Still a real, undeclared registry
    gap (`depth_of_book_10` is genuinely captured data from the shipped `bybit_futures_book_ticker_ws.py`
    connector, just never added to `DATA_TYPES_BY_ASSET_GROUP["cefi"]`) — existing P2 todo carried unchanged.
  - **`perp_daily_ctx`** — 7 `captured` rows, carried unchanged, still not investigated further (existing P4 todo).
- **chain**: 100% blank (29,938,146 / 29,938,146, 1 distinct value) — unchanged, the 2026-07-28 chain-axis heal
  continues to hold.
- **quote_asset**/**margin_type**: non-blank rows now 5,043,561 / 5,253,484 respectively — continued growth from
  yesterday's cited `quote_asset` figure (4,709,481), consistent with the established "ongoing MDPS candle-row
  capture" pattern (same vocabulary, no drift) — not investigated further, per established practice.

## 3. Confirmed self-heal — the closed 2026-08-16 incident's predicted retry cycle, observed landing

Yesterday's report cross-referenced (but did not re-investigate) `attempted_failed` rows on BYBIT-FUTURES and
`depth_of_book_10` carrying the migration sentinel from the same-day-closed
`cefi_queue_mode_tier3_sentinel_false_empty_confirmed_2026_08_16.md` incident, and predicted: *"
`check_shard_freshness(..., retry_failed=True)` will naturally re-attempt them on the next backfill pass."*

This run's census directly measures that prediction landing, on **two independent axes**:

- **BYBIT-FUTURES** (venue axis): all 10,268 rows now `empty_confirmed`/`SOURCE_RETURNED_ZERO` (a legitimate,
  non-sentinel typed reason) — was 10,256 `attempted_failed` (sentinel) + 12 `empty_confirmed` yesterday.
  `attempted_at` for this venue spans 2026-07-31 → 2026-08-16T04:38:01Z (original first-attempt timestamps,
  apparently not updated by the reclassification itself, so this range does not by itself date the retry).
- **`depth_of_book_10`** (data_type axis): the prior 4,038 `attempted_failed` rows are now `empty_confirmed`
  (§2) — the count math (`27,206 − 23,168 = 4,038`) matches exactly.

**Assessment**: this is consistent with, not contradictory to, the incident's own stated closure and predicted
self-healing — a plausible-good outcome, not a regression. **Explicitly not independently verified**: whether
`SOURCE_RETURNED_ZERO` is the factually-correct terminal classification for every one of these 10,268+4,038 shards
(that would require checking against the exchange/source itself — out of this role's Tier-1 census scope). Recorded
as a confirmation for whoever owns that incident's aftermath, not re-opened, and not treated as a fresh finding.

## 4. Honest-coverage — freshest available re-confirmed, today's rollup not yet due

- Today's (2026-08-17) `coverage.json` **does not exist yet** as of the 00:1x-00:2x UTC check window
  (`gs://central-element-323112-honest-coverage/2026-08-17/coverage.json` absent). This is consistent with, not a
  break from, the observed generation pattern (yesterday's file generated at `00:43:09Z`) — checked here ~20-30min
  before that historical time, so absence is expected, not a gap.
- Date-dir continuity (last 12 in the bucket): `2026-07-30, 07-31, 08-01, 08-02, 08-04, 08-05, 08-09, 08-10, 08-12,
  08-14, 08-15, 08-16` present. `08-03, 08-06, 08-07, 08-08, 08-11, 08-13` missing across this window — the
  08-11/08-12-adjacent gap is already explained by the OOM incident closed 2026-08-15 (per yesterday's report);
  the older 08-03/06/07/08 gaps predate that investigation and were not chased this run (out of cefi-only,
  Tier-1 scope). **Three consecutive successful days (08-14, 15, 16) since the 08-15 fix closure** — the cadence
  looks to have stabilized; today's file is simply not due yet at check time.
- **Formula re-verification** (per role scope): re-read the freshest available rollup, `2026-08-16T00:43:09Z`
  (byte-identical file to what yesterday's report already verified — no new rollup has landed since). cefi
  `by_asset_group`: `captured=9,756,593`, `empty_confirmed=6,437,038`, `attempted_failed=764,259`,
  `expected_unattempted=10,879,751`, `total=27,837,641`, published `coverage_pct=45.59`. Independently re-derived:
  `9,756,593 / (9,756,593 + 764,259 + 10,879,751) = 9,756,593 / 21,400,603 = 45.591…%` — matches published exactly.
  **No formula drift** (re-confirmation, not a new measurement — same underlying file as yesterday).
- **cefi layer_1**: `completeness_pct=94.52` (69/73), `denominator_status=INCOMPLETE`,
  `instrument_gates_download=true` — unchanged from yesterday (same file). `missing_tuples` (4, unchanged):
  `BITGET-FUTURES/future` × 2 (`book_snapshot_5`, `derivative_ticker`) + `OKX-FUTURES/perpetual` × 2
  (`book_snapshot_5`, `derivative_ticker`).

## 5. What this run does NOT cover (declared, per the role's Tier-1 scope)

- No machine-oracle path-structure sweep, no id-form/schema Tier-1 sampled check or Tier-2 VM validation, no
  orphan-object sweep / delete suggestions — never this role.
- No batch-layer GCS-vs-manifest delimiter-descent spot-check this cycle (same as 08-16 — the census + honest-
  coverage verification + the consolidator-stall investigation already filled this run's scope).
- Did not independently investigate `reprobe_audit_latest.json`'s cadence (still showing yesterday's generation as
  of this check window — too early in the day to conclude either way).
- Did not diagnose the consolidator stall's root cause (§0) — flagged as a P1 todo, not chased further; genuinely
  needs an infra-level look this role cannot give at Tier-1.
- Did not chase `perp_daily_ctx` (7 rows) or the older 08-03/06/07/08 honest-coverage date-dir gaps.
- Did not identify which launcher/registry entry still probes `BINANCE-DELIVERY` (carried from 08-16, still
  unresolved).
- Did not independently verify `SOURCE_RETURNED_ZERO` is the factually-correct terminal state for the BYBIT-
  FUTURES / `depth_of_book_10` rows discussed in §3 (would require an exchange-side check, out of scope).

## 6. Todos

- [ ] [INFRA] P1. **Market-data consolidator confirmed multi-hour stall pattern, 2 consecutive days** —
      2026-08-16's lock (16:31:23Z) was held >=7.5h (vs ~27min baseline), the eventual completed run
      (23:11:06Z) took ~6.5h, `consolidator_stall_state.json` streak escalated 0→10, and a second lock-contention
      no-op occurred at 00:01:08Z before a fresh run started 00:06:27Z. Escalated per yesterday's own stated
      upgrade condition ("if the lock is still held on tomorrow's run, that would upgrade this from an observation
      to a real stall finding"). Not a data-loss issue (the run did complete), but a reliability signal needing an
      infra-level look — possibly tied to the high manifest churn noted 08-16, or to
      `cefi_tardis_date_serial_barrier_still_open_2026_08_16.md` (not cross-checked this run). Repo:
      market-tick-data-service / deployment-service.
- [ ] [DATA] P2. **BINANCE-DELIVERY venue drift (4,838 rows, carried unchanged)** — includes 73 rows with a
      self-diagnosing code error (`build_partition_path built a non-canonical GCS path for BINANCE-DELIVERY/
      futures`), 483 combined `404` errors, and 4,255 `SOURCE_RETURNED_ZERO` rows; zero rows ever reached
      `captured` via a canonical path. Candidate for the same "deregister dormant legacy alias" fix class as the
      2026-08-04 bare-OKX precedent — still needs the launcher/registry grep to confirm which config still probes
      it (not identified with enough confidence in this or the prior run). Repo: market-tick-data-service /
      unified-api-contracts.
- [ ] [DATA] P2. **`depth_of_book_10` data_type registry gap (39,120 rows, 11,914 genuinely `captured`, carried)**
      — produced by the real, shipped `bybit_futures_book_ticker_ws.py` connector, undeclared in
      `DATA_TYPES_BY_ASSET_GROUP["cefi"]`. Same shape as the carried `instrument_type=index` gap below — decide
      add-vs-document; an addition needs its downstream consumers (MVP predicate, schema contract) checked in the
      same change per the entity-rename/registry-migration rule. Repo: unified-api-contracts.
- [ ] [INFRA] P3. **`phantom_audit` for cefi now 21 days stale** (was 20 on 08-16, zero remediation for 3+ weeks)
      — carried, escalating by 1 day again. Repo: instruments-service.
- [ ] [DATA] P3. **CRYPTOFACILITIES (10 rows) / OKEX-FUTURES (36 rows)** — both benign (100% `empty_confirmed`,
      legacy delisted-instrument handling per prior runs), but the venue NAME sits outside
      `VENUES_BY_ASSET_GROUP["cefi"]`. Candidate for the accepted-exception list rather than continued M−C
      reporting. Repo: unified-api-contracts.
- [ ] [DATA] P4. **`instrument_type=index` (3,910 rows, DERIBIT/volatility_index, carried unchanged)** — still
      undeclared in any cefi registry. Repo: unified-api-contracts.
- [ ] [DIAG] P4. **`perp_daily_ctx` data_type (7 `captured` rows, carried, still unexplored)** — confirm in-scope
      or expected-pilot. Repo: unified-api-contracts.
- [ ] [DIAG] P4. **`reprobe_audit_latest.json` daily-cadence not yet confirmable** — still showing 2026-08-16's
      generation as of this run's 00:1x-00:2x UTC check window; too early in the day to conclude either way (own
      the check on a later-in-the-day run, or a run dispatched closer to its ~09:00 UTC-ish generation time). Repo:
      market-tick-data-service / instruments-service.
- [x] [DIAG] P4. ✅ **CONFIRMED self-heal (not a fix, an observation)** — the closed 2026-08-16 incident's
      predicted retry-cycle landed on both BYBIT-FUTURES and `depth_of_book_10` (§3): `attempted_failed` sentinel
      rows transitioned cleanly to `empty_confirmed`/`SOURCE_RETURNED_ZERO`. No action needed; recorded for this
      report lineage's continuity and for whoever owns that incident's aftermath.
