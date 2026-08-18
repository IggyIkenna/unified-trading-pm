---
doc_type: audit-result
title: "Data-pipeline reconciliation — cefi (2026-08-16), raw-tick layer, Tier-1 only"
summary: >-
  Scheduled daily cefi spot-check (cefi_reconciliation_auditor role, dispatch agt-10f80e, slot 14) — first run since
  2026-08-09 (7-day gap in the daily cadence). Phase 0: both cefi buckets reachable; instruments-store healthy/fresh
  no-op; market-data consolidator was MID-RUN at check time (lock held since 16:31:23Z, ~65min elapsed, not flagged
  stalled) on an unusually high-churn day — the last COMPLETED run (05:01:57Z) processed 31.43M rows, well above
  08-09's 11.9M snapshot, consistent with the reporting gap. `phantom_audit` is now 20 days stale (unremediated since
  08-09's 13-day note); `reprobe_audit` is NEWLY fresh (generated same-day) after being 26-days-stale on 08-09.
  Census (§3f): venue axis shows 7 M-C drift entries — 3 unchanged/carried (bare-OKX 5,225; KALSHI_PERP 2;
  OKX-OPTIONS 2), 3 fully explained by an ALREADY-CLOSED same-day incident (BYBIT-FUTURES's growth to 10,268 rows and
  part of a new depth_of_book_10 data_type gap both trace to
  `cefi_queue_mode_tier3_sentinel_false_empty_confirmed_2026_08_16.md`, independently root-caused, fixed, and
  re-verified by a different slot earlier today — NOT a new problem this run is surfacing), and 1 genuinely
  new/independent finding (BINANCE-DELIVERY, 4,838 rows spanning 07-27..08-09, including a self-diagnosed
  non-canonical-path code error). instrument_type/data_type/chain axes otherwise match the established baseline
  (index=3,910, 5 stray ohlcv_* @ 2 rows each, chain 100% blank) plus the new depth_of_book_10 registry gap (39,120
  rows / 11,914 genuinely `captured`, from a real shipped BYBIT-FUTURES book-ticker connector, undeclared in
  `DATA_TYPES_BY_ASSET_GROUP["cefi"]`) and two benign legacy-brand-name entries (CRYPTOFACILITIES/OKEX-FUTURES, both
  100% `EXPECTED_INSTRUMENT_DELISTED`). Honest-coverage: the previously-escalated P1 OOM issue (4 consecutive missed
  cycles as of 08-09) is CONFIRMED RESOLVED — closed 2026-08-15 by a different slot, verified live via today's fresh,
  complete `coverage.json` (all 5 asset_groups measured, `partial=false`); formula independently re-derived and
  matches `honest-coverage-model.md` exactly (captured 9,756,593 / 21,400,603 = 45.59%, byte-match to the published
  figure); cefi layer_1 completeness improved slightly to 94.52% (69/73, was 93.15%/68 on 08-09). One in-scope doc
  fix shipped: the skill's Phase-0(a) env-var note was missing the `AWS_ACCOUNT_ID` requirement (`GCP_PROJECT_ID` was
  documented, `AWS_ACCOUNT_ID` was not) — added.
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
    honest-coverage-oom-resolved,
    bybit-futures-migration-crossref,
    binance-delivery-non-canonical-path,
    depth-of-book-10-registry-gap,
    bare-okx-carried,
  ]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    honest-coverage-model,
    data_pipeline_reconciliation_cefi_2026_08_09,
    cefi_queue_mode_tier3_sentinel_false_empty_confirmed_2026_08_16,
    honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08,
  ]
created: 2026-08-16
resulting_plan:
lib_version:
  "market-tick-data-service@HEAD (slot 14), unified-api-contracts@HEAD (audited only; no code changes shipped this
  run — one doc fix in unified-trading-pm)"
doc_versions_checked:
audited_scope:
  "asset_group=cefi, layer=raw-tick, PROD (-prd-) buckets only, read-only, Phase 0 + census (Tier-1) +
  honest-coverage verification per the cefi_reconciliation_auditor role (subset of /data-pipeline-reconciliation) —
  daily scheduled spot-check, not a full campaign. First run in 7 days (last: 2026-08-09)."
date: 2026-08-16
auditor: "cefi_reconciliation_auditor (scheduled role, slot 14, dispatch agt-10f80e)"
parent_epic: security_and_cross_cutting_master
severity: P2
skill: data-pipeline-reconciliation
run_date: 2026-08-16
generated_at: 2026-08-16T17:57:32+00:00
---

# Data-pipeline reconciliation — cefi (2026-08-16), raw-tick layer, Tier-1 only

**Fully read-only this run** — no GCS writes, no manifest writes, no deletes, no VM launches; one code-adjacent
change, a documentation fix to the skill's own Phase-0(a) env-var note (§7). Daily scheduled `cefi_reconciliation_auditor`
spot-check: Phase 0 (reachability + freshness) + the §3f distinct-value census + honest-coverage formula/freshness
verification. **First run since 2026-08-09** — a 7-day gap in the daily cadence, so "carried" findings below are
compared against the 08-09 baseline by value, not by an unbroken day-count streak.

## 0. Phase-0 reachability + freshness

| bucket                                               | reachable | consolidator lock                                                    | last COMPLETED run (UTC) | verdict                                                                 |
| ----------------------------------------------------- | --------- | ---------------------------------------------------------------------- | ------------------------- | ------------------------------------------------------------------------ |
| `market-data-tick-cefi-prd-central-element-323112`   | yes       | **HELD** since 2026-08-16T16:31:23.19Z (instance `1-02a1a35c`, ~65min elapsed at check time) | 2026-08-16T05:01:57.94Z   | produced (31,428,500 rows in → 29,938,146 out; 1,490,354 dedup-dropped; 7,851 shards scanned, 5,454 changed) |
| `instruments-store-cefi-prd-central-element-323112`  | yes       | not locked                                                              | 2026-08-16T17:00:53.97Z   | empty (0 rows, no-op — consistent with every prior run)                |

`consolidator_stall_state.json`: market-data `streak=0, baseline_shards=7851` (**not flagged stalled** — a `streak=0`
in-progress run is a normal in-flight state, not a stall signal); instruments-store `streak=0, baseline_shards=2`.
The market-data lock's ~65min-and-counting duration is longer than the last completed run's own 26.6min
(`duration_ms=1,597,353`), but today saw unusually high manifest churn (§3 below — a live incident, its fix, two
manifest migrations, and a VM relaunch all landed in the ~19h before this check), so a longer first post-churn
consolidation pass is the more likely explanation than a genuine stall. **Not independently reverified as complete
by the time this report was written** — if the lock is still held on tomorrow's run, that would upgrade this from an
observation to a real stall finding (§6).

- `_index/phantom_audit_latest.json` (market-data): `phantom_count=0`, `generated_at=2026-07-27T17:38:18Z` — **20
  days stale** (was 13 on 08-09; zero remediation across the intervening week — carried, escalating slightly, §6).
- `_index/reprobe_audit_latest.json` (market-data): `generated_at=2026-08-16T09:00:49.76Z`, `day=2026-08-16`,
  `new_empties=18, disagreements=12, ambiguous=0, proven=0, reclassified=0` — **NEWLY FRESH** (same-day) after being
  26-days-stale on 08-09 (`generated_at=2026-07-14`). A genuinely new signal in this role's lineage — not previously
  observed running on any cadence. Not investigated further this run (§5); worth confirming on tomorrow's run whether
  the daily cadence holds and whether the 12 disagreements need a look (§6).
- `instruments-store-cefi` still has **no** `phantom_audit_latest.json` / `reprobe_audit_latest.json` (both `null`) —
  standing declared coverage gap (H5), unchanged.

**AWS cross-check (Phase 0(a)/(b)):** `resolve_bucket_name(cloud="aws", …)` initially raised `BucketNamingError` —
`AWS_ACCOUNT_ID` was unset in this session's environment (the skill's Phase-0(a) note only documented the GCP-side
`GCP_PROJECT_ID` requirement). Set `AWS_ACCOUNT_ID=427895769566` (confirmed correct — matches the bucket names the
08-09 report already recorded) and re-resolved cleanly. Both AWS-side mirror buckets
(`market-data-tick-cefi-prd-427895769566`, `instruments-store-cefi-prd-427895769566`) are reachable and **completely
empty (0 objects)** — unchanged from every prior run (dual-cloud-active write is still opt-in per-workload-promotion,
not the live default for cefi raw-tick capture). Fixed the skill doc's own gap (§7) rather than leaving it for the
next run to rediscover.

## 1. Census — venue axis (M = manifest distinct, C = UAC `VENUES_BY_ASSET_GROUP["cefi"]`, 25 venues)

Read via pyarrow native `GcsFileSystem`, one axis (2 columns: axis + `capture_status`) at a time via
`pc.value_counts`/`group_by` — never pandas, never all 9 axis columns at once — wrapped in
`scripts/dev/run-bounded-analysis.sh --mem-cap 6G` per the shared-host memory-bounding HARD RULE (this host has no
working `systemd --user` instance; the wrapper fell back to its RSS-poll enforcement path). Total manifest rows read:
29,938,146 (matches the last COMPLETED consolidator run's `rows_out` — this census read reflects that pre-in-progress-run
snapshot, not whatever the still-running 16:31:23Z pass produces).

- **C − M (orphaned declarations)**: **empty** — all 25 UAC-declared cefi venues have manifest presence.
- **M − C (drift)** — **7 entries**, three distinct characters:

  | venue              | rows   | capture_status breakdown                                    | character                                                                                          |
  | ------------------ | ------ | -------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
  | `OKX` (bare)        | 5,225  | 100% `attempted_failed`                                        | **carried, count identical to 08-09** — the 08-04 orchestrator-literal fix still holds.               |
  | `KALSHI_PERP`       | 2      | 100% `attempted_failed`                                        | **carried, count identical to 08-09**.                                                                |
  | `OKX-OPTIONS`       | 2      | 100% `attempted_failed`                                        | **carried, count identical to 08-09**.                                                                |
  | `BYBIT-FUTURES`     | 10,268 | 10,256 `attempted_failed` (sentinel below) + 12 `empty_confirmed` | **NOT a new problem** — 10,256 of these rows carry `error_reason=CORRECTIVE_MIGRATION_queue_mode_tier3_sentinel_no_prior_capture_check_2026_08_16`, the exact sentinel written by an ALREADY-CLOSED same-day data-correctness fix (§3). |
  | `BINANCE-DELIVERY`  | 4,838  | 578 `attempted_failed` + 4,255 `empty_confirmed` + 5 `captured` | **genuinely new/independent** — `attempted_at` spans 2026-07-27..2026-08-09 (predates today's incident entirely); see below. |
  | `CRYPTOFACILITIES`  | 10     | 100% `EXPECTED_INSTRUMENT_DELISTED`                             | benign — legacy Kraken-derivatives brand name, system correctly recognized delisted instruments.     |
  | `OKEX-FUTURES`      | 36     | 100% `EXPECTED_INSTRUMENT_DELISTED`                             | benign — legacy OKX brand name (pre-rebrand), same as above.                                          |

**BINANCE-DELIVERY detail (new finding, §6):** `error_reason` breakdown — `SOURCE_RETURNED_ZERO` (4,255),
`UNCLASSIFIED:404 GET https`/`404 GET https` (483 combined), and **73 rows carrying
`build_partition_path built a non-canonical GCS path for BINANCE-DELIVERY/futures`** — a self-diagnosing error
message from the path-builder code itself, i.e. the codebase already knows this venue name produces a non-canonical
path. Zero rows ever reached `captured` status via a canonical path (the 5 `captured` rows are pre-error-detection
artifacts). This has the same shape as the 2026-08-04 bare-OKX precedent (a dormant/legacy venue name some launcher
or registry entry still probes) but was not previously reported in the 08-05..08-09 report lineage.

## 2. Census — instrument_type + data_type axes

- **instrument_type** (13 distinct manifest values vs 7 canonical — `combo, future, futures_chain, option,
  options_chain, perpetual, spot_pair`, derived from `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE` keys where
  `ag="cefi"`):
  - Case-only variants (`PERPETUAL` 19,193,915 / `SPOT_PAIR` 8,257,788 / `FUTURE` 1,600,589 / `OPTION` 282,202 /
    `COMBO` 31,557 alongside their lowercase-canonical counterparts) are the ruled C2a `migration_pending` casing
    axis — suppressed, not findings (§5.1 of the taxonomy).
  - **Case-insensitive drift**: `''` (blank, 157,337 rows, 100% `empty_confirmed`) / `'None'` (null-valued, 162,190
    rows) / `'index'` (3,910 rows, 100% `captured` — carried DERIBIT `volatility_index` registry gap, count
    unchanged since 08-09, still undeclared in any cefi registry, §6). The blank/null population (≈319,527 rows
    combined) was not itemized by count in the 08-05..08-09 report lineage — recorded here for the first time as a
    baseline; not asserted to be new, just newly measured.
- **data_type** (16 distinct manifest values vs 9 canonical from `DATA_TYPES_BY_ASSET_GROUP["cefi"]`):
  - 5 stray `ohlcv_{15m,15s,1d,1h,5m}` @ 2 `captured` rows each (10 total) — **carried, byte-identical to every prior
    report**.
  - **`depth_of_book_10`** — 39,120 rows (11,914 `captured` + 23,168 `empty_confirmed` + 4,038 `attempted_failed`) —
    **NEW finding, registry gap** (§6). Traced to a real, shipped connector:
    `market_tick_data_service/live/connectors/bybit_futures_book_ticker_ws.py` explicitly emits `depth_of_book_10`
    (alongside `book_snapshot_5`/`derivative_ticker`) for BYBIT-FUTURES — this is intentional, working capture
    (11,914 genuine successful rows), just never declared in `DATA_TYPES_BY_ASSET_GROUP["cefi"]`. The 2,566
    `attempted_failed` rows under this data_type that carry today's migration sentinel (§3) are part of the
    already-closed incident; the `captured`/remaining `empty_confirmed` rows are independent, ongoing, healthy
    capture under an undeclared name.
  - **`perp_daily_ctx`** — 7 `captured` rows, new, tiny, not investigated further this run (§6).
- **chain**: 100% blank (29,938,146 / 29,938,146, 1 distinct value) — the 2026-07-28 chain-axis heal continues to
  hold in today's snapshot (cannot independently confirm unbroken daily continuity across the 08-09→08-16 gap, but
  today's read is clean).
- `quote_asset`/`margin_type` grew substantially since 08-09 (`USDT` 593,124→4,709,481, `linear` 594,202→5,086,961) —
  consistent with continued MDPS candle-row capture, same vocabulary set, no drift; not investigated further, per
  established practice.

## 3. Today's live incident — cross-referenced, NOT re-investigated

While tracing the BYBIT-FUTURES and `depth_of_book_10` drift, found their `attempted_failed` rows carry
`error_reason=CORRECTIVE_MIGRATION_queue_mode_tier3_sentinel_no_prior_capture_check_2026_08_16` — traced this to
`plans/active/issues/cefi_queue_mode_tier3_sentinel_false_empty_confirmed_2026_08_16.md` (filed and **fully closed**
by a different slot earlier today, all 3 P0 todos ✅). Summary for this report's context (full detail in that doc,
not duplicated here): a `SINGLE_VM_QUEUE=1` CeFi Tardis backfill's Tier-3 sentinel fan-out
(`sentinels.py::_emit_tier3_for_dt`) wrote `empty_confirmed` over shards with a pre-existing real `captured` row
(directly confirmed false for `BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN` trades `2020-01-02`) because it decided
captured-vs-empty using only the current run's own in-memory fetch results, never checking the manifest/GCS first.
Both the code (`market-tick-data-service@f134d16595c3e5d1761ec76a7f40041535a6f4e3`) and the data (163,421 affected
rows migrated `empty_confirmed→attempted_failed` via a CAS write, consolidator-pause-gated per the delete-safety
protocol, independently re-verified) are fixed and shipped. **This report's own findings above correctly reflect
that corrected post-migration state** — the BYBIT-FUTURES/`depth_of_book_10` `attempted_failed` counts are not a new
regression this run is discovering; they are the expected, self-correcting output of an already-resolved incident,
and `check_shard_freshness(..., retry_failed=True)` will naturally re-attempt them on the next backfill pass. No
action item filed here for this incident — it already has its own complete, closed record.

## 4. Honest-coverage — previously-escalated P1 CONFIRMED RESOLVED

The 08-09 report escalated `honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md` to P1 after 4 consecutive
missed cycles. Re-checked live this run:

- **Issue doc status**: still `status: open` but with **all todos closed** and `archive_exempt: true` set (2026-08-15
  Progress Log entry) — two independent root causes found and fixed the same week: (1) the post-defi-canonicalization
  rebuild grew the defi primary manifest to ~158M rows, which OOM'd even a 32GiB `e2-highmem-4` re-launch; fixed by
  relaunching on `e2-highmem-8` (64GiB) with `--oom-monitor`; (2) a SEPARATE, independent bug — the 2026-08-11
  `get_storage_client` refactor left `google.cloud`-style calls (`upload_from_string`, `get_blob`) on UTL handles
  that don't expose them, so even a successful compute pass crashed on write. Fixed
  `instruments-service@4bb2164e`.
- **Confirmed live, independently, this run**: `gs://central-element-323112-honest-coverage/2026-08-16/coverage.json`
  exists, `generated_at=2026-08-16T00:43:09Z`, `schema_version=2`, `asset_groups_measured=[cefi, defi, tradfi,
  sports, prediction]` (all 5), `asset_groups_failed=[]`, `partial=false` — a clean, complete run, not a partial or
  degraded one.
- **Date-dir coverage since 08-09**: `08-09, 10, 12, 14, 15, 16` present; `08-11, 13` missing. The `08-11/08-12` gap
  is fully explained by the incident above (both root causes were live across that exact window); `08-13`'s gap was
  not independently chased (out of this role's cefi-only scope — the OOM affected all 5 asset groups identically).
- **Formula verification (per role scope — "confirm the formula matches honest-coverage-model.md")**: cefi
  `by_asset_group` entry — `captured=9,756,593`, `empty_confirmed=6,437,038`, `attempted_failed=764,259`,
  `expected_unattempted=10,879,751`, `total=27,837,641`, published `coverage_pct=45.59`. Independently re-derived via
  the named formula (`captured / (captured + attempted_failed + expected_unattempted)`, `empty_confirmed` correctly
  EXCLUDED): `9,756,593 / (9,756,593 + 764,259 + 10,879,751)` = `9,756,593 / 21,400,603` = **45.591…%** — byte-match
  to the published `45.59%`. **No formula drift.**
- **cefi layer_1** (denominator-completeness view, a separate top-level block from `by_asset_group`):
  `completeness_pct=94.52` (69/73 present tuples) — improved from 08-09's `93.15%` (68/73). `missing_tuples` (4, same
  family as before, one fewer): `BITGET-FUTURES/future` × 2 data_types (`book_snapshot_5`, `derivative_ticker`) +
  `OKX-FUTURES/perpetual` × 2 (`book_snapshot_5`, `derivative_ticker`) — was 5 missing on 08-09 (3×BITGET-FUTURES/future
  + 2×OKX-FUTURES/perpetual); one BITGET-FUTURES/future data_type is now present. `denominator_status=INCOMPLETE`,
  `instrument_gates_download=true` — `coverage_pct` remains a **lower bound**, unchanged caveat.
- **Total-row note**: `coverage.json`'s cefi `total` (27,837,641) is ~2.1M below this run's own census read
  (29,938,146) — the rollup snapshot (00:43 UTC) predates both today's manifest migration (~16:57 UTC) and the later
  05:01:57 consolidator run; an expected staleness gap given the generation timestamps, not a discrepancy.

## 5. What this run does NOT cover (declared, per the role's Tier-1 scope)

- No machine-oracle path-structure sweep, no id-form/schema Tier-1 sampled check or Tier-2 VM validation, no
  orphan-object sweep / delete suggestions — never this role.
- **No batch-layer GCS-vs-manifest delimiter-descent spot-check this cycle** (§3 in the prior report lineage,
  2026-08-05..08-09) — the census + honest-coverage verification already surfaced multiple concrete findings needing
  write-up and todo-filing; explicitly skipping rather than silently dropping it. Good candidate for tomorrow's run.
- Did not independently investigate `reprobe_audit_latest.json`'s `new_empties=18`/`disagreements=12` — flagged as a
  new signal (§0), not chased at Tier-1 depth this run.
- Did not chase `perp_daily_ctx` (7 rows) beyond noting it, nor the pre-existing April-2026 BINANCE-FUTURES
  manifest-row gap the incident doc (§3) itself left explicitly unchased (that doc's own scoping call, not this
  run's).
- Did not investigate the `2026-08-13` honest-coverage date-dir gap independently (out of cefi-only scope).
- Did not identify which launcher/registry entry still probes `BINANCE-DELIVERY` — the M−C drift and its
  self-diagnosing error message are recorded (§1), but the root-cause site wasn't traced with enough confidence this
  run to safely propose a one-line fix the way the bare-OKX precedent allowed.

## 6. Todos

- [ ] [DATA] P2. **BINANCE-DELIVERY venue drift (4,838 rows, genuinely pre-existing — NOT part of today's
      incident)**: includes 73 rows with a self-diagnosing code error
      (`build_partition_path built a non-canonical GCS path for BINANCE-DELIVERY/futures`), 483 combined `404`
      errors, and 4,255 `SOURCE_RETURNED_ZERO` rows; zero rows ever reached `captured` via a canonical path.
      Candidate for the same "deregister dormant legacy alias" fix class as the 2026-08-04 bare-OKX precedent — needs
      a quick launcher/registry grep to confirm which config still probes it before a narrowly-scoped fix (not
      identified with enough confidence this run). Repo: market-tick-data-service / unified-api-contracts.
- [ ] [DATA] P2. **`depth_of_book_10` data_type registry gap (39,120 rows, 11,914 genuinely `captured`)** — produced
      by the real, shipped `bybit_futures_book_ticker_ws.py` connector, undeclared in
      `DATA_TYPES_BY_ASSET_GROUP["cefi"]`. Same shape as the carried `instrument_type=index` gap below — decide
      add-vs-document; an addition needs its downstream consumers (MVP predicate, schema contract) checked in the
      same change per the entity-rename/registry-migration rule. Repo: unified-api-contracts.
- [ ] [INFRA] P3. **`phantom_audit` for cefi now 20 days stale** (was 13 on 08-09, zero remediation across the
      intervening week) — carried, escalating slightly given the additional week of staleness. Repo:
      instruments-service.
- [ ] [DATA] P3. **CRYPTOFACILITIES (10 rows) / OKEX-FUTURES (36 rows)** — both 100% `EXPECTED_INSTRUMENT_DELISTED`
      (benign, system behaving correctly), but the venue NAME is a legacy pre-rebrand label outside
      `VENUES_BY_ASSET_GROUP["cefi"]`. Candidate for the accepted-exception list rather than continued M−C reporting.
      Repo: unified-api-contracts.
- [ ] [DATA] P4. **`instrument_type=index` (3,910 rows, DERIBIT/volatility_index)** — carried, count unchanged since
      08-09. Still undeclared in any cefi registry. Repo: unified-api-contracts.
- [ ] [DIAG] P4. **`perp_daily_ctx` data_type (7 `captured` rows, new)** — small, unexplored; confirm in-scope or
      expected-pilot. Repo: unified-api-contracts.
- [ ] [DIAG] P4. **`reprobe_audit_latest.json` newly fresh** (first time observed on a same-day cadence in this
      role's lineage), `new_empties=18, disagreements=12` — confirm on tomorrow's run whether the daily cadence holds
      and whether the 12 disagreements need a look. Repo: market-tick-data-service / instruments-service.
- [ ] [DIAG] P4. **market-data consolidator lock held ~65min+ at check time** (started 2026-08-16T16:31:23Z, not
      flagged stalled via `streak=0`, plausibly the first post-high-churn consolidation pass) — if still held on
      tomorrow's Phase-0 check, that upgrades this from an observation to a genuine stall finding. Repo:
      market-tick-data-service / deployment-service.
- [x] [DIAG] P4. ✅ **RESOLVED (independently, by a different slot, prior to this run) — honest-coverage daily VM
      OOM**, closed 2026-08-15 (`honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md`, `archive_exempt:
      true`). Confirmed live via today's fresh, complete `coverage.json` (§4) — no action needed; recorded here for
      this report lineage's continuity.
- [x] [DOCS] P4. ✅ **FIXED this run** — `cursor-configs/skills/data-pipeline-reconciliation/SKILL.md` § Phase 0(a)
      was missing the `AWS_ACCOUNT_ID` env-var requirement for the AWS-side cross-check (only `GCP_PROJECT_ID` was
      documented). Added a matching note. `unified-trading-pm` (this commit).
