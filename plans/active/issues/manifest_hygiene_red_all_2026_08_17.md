---
doc_type: issue
title: "Manifest hygiene RED — 4 AG(s) with findings (2026_08_17)"
summary: >-
  Daily manifest-hygiene audit found oracle_expects_but_empty (DIVERGENT_EMPTY) candidates for
  cefi/tradfi/prediction and a 1-row schema_version_not_v9 straggler for cefi. Diagnosed 2026-08-17:
  prediction's 461-cell finding is 91% one shape — POLYMARKET's prediction_canonical_question_group
  CQG-bundle rollup is empty on 43% of days across the whole history including today, while raw trades
  capture is mostly fine (though it has its own separate 8-day-and-counting outage as of 2026-08-16 — see
  Todos). Slot-9's 2026-08-17 all-or-nothing-coverage-gate root-cause claim was REFUTED by slot-14's
  round-2 LIVE measurement the same day (zero attempted_failed rows found on clean test dates) — real
  cause not yet confirmed, needs a fresh code trace (see "Diagnosis update (slot-14 round 2)"); cefi
  (58,362 cells) and tradfi (8,468 cells) still need a VM-scale re-run of detect_manifest_divergence.py
  (OOMs the shared host).
status: open
nature: issue
asset_group: [cefi, tradfi, prediction]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [manifest-hygiene, divergent-empty, data-correctness, prediction, cefi, tradfi]
created: 2026-08-17
author: "manifest_hygiene_daily.py (data-pipeline daily audit)"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
source:
  - manifest_hygiene_daily.py
  - data_pipeline_hardening_self_monitoring_2026_06_22.md
related: []
locked_by:
locked_since:
resolved_by:
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    unified-trading-library/scripts/detect_manifest_divergence.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/manifest_finalize.py,
    unified-trading-library/unified_trading_library/manifest_writer/_writer_validation.py,
    /plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/prediction_tier3_lifecycle.py,
  ]
---

# Manifest hygiene RED — 4 AG(s) with findings (2026_08_17)

> Auto-filed by the daily data-pipeline audit `manifest_hygiene_daily.py` (Wave 4b, Phase 5
> scripted→LLM escalation hop). A deterministic candidate list was non-empty — the
> verdicts below need a worker's judgment (real gap vs code bug, straggler
> vs intentional new venue). See `/codex/05-infrastructure/data-pipeline-alerts.md`.

## What I found

The daily manifest-hygiene-vs-GCS orchestrator found non-empty candidate lists for: cefi, defi, prediction, sports, tradfi. Finding-classes: schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk, phantom_captured_no_parquet, shard_4pillar_fail.

Candidate list(s) (deterministic, machine-written):

- `/app/unified-trading-pm/plans/audit/results/manifest_hygiene_cefi_2026_08_17.csv`
- `/app/unified-trading-pm/plans/audit/results/manifest_hygiene_tradfi_2026_08_17.csv`
- `/app/unified-trading-pm/plans/audit/results/manifest_hygiene_sports_2026_08_17.csv`
- `/app/unified-trading-pm/plans/audit/results/manifest_hygiene_prediction_2026_08_17.csv`

## Why it matters

Each class is a data-correctness signal: non-v9 rows are pre-canonicalisation stragglers; oracle-expects-but-empty is a candidate C1 misclassification (real gap vs code bug — needs judgment); non-canonical paths break selective reads; phantoms are captured cells with no parquet.

## Recommended decision

Triage each candidate CSV: confirm real gaps → backfill; confirm code bugs → fix the adapter/writer; confirm intentional new venues/spellings → extend the UAC oracle/canonical builders. Per data_pipeline_hardening_self_monitoring_2026_06_22.md Phase 3/5.

Cold-start context: read `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
in full + `/codex/05-infrastructure/data-pipeline-alerts.md` + the candidate CSV(s)
above before acting.

## Diagnosis (2026-08-17, slot-14)

Ran `unified-trading-library/scripts/detect_manifest_divergence.py` (the actual DP-MANIFEST-004
detector behind these CSVs' `oracle_expects_but_empty` finding) directly against prod to get the real
per-cell breakdown rather than the manifest_hygiene CSVs' truncated stdout-tail samples (only 3 dates
survive the 2000-char tail per AG — not representative of which venue dominates).

**prediction (461 DIVERGENT_EMPTY) — FULL breakdown obtained, real root-cause hypothesis identified.**
`unified-trading-library`'s manifest read for `prediction` is small enough to run locally
(`--asset-group prediction`, wrote `unified-trading-pm/plans/audit/results/divergence_2026-08-17.csv`,
23,466 cells). Breakdown:

| venue | data_type | DIVERGENT_EMPTY | date range |
| --- | --- | --- | --- |
| POLYMARKET | `prediction_canonical_question_group` | **419** | 2024-01-01 → 2026-08-17 (spans the ENTIRE coverage history + TODAY) |
| POLYMARKET | `trades` | 33 | 2026-05-13 → 2026-08-16 |
| POLYMARKET | `book_snapshot_5` | 5 | 2026-06-21 → 2026-07-28 |
| KALSHI | `book_snapshot_5` | 2 | 2026-06-22 → 2026-07-09 |
| KALSHI | `trades` | 2 | 2026-06-22 → 2026-06-24 |

91% of the finding is ONE cell shape: `(POLYMARKET, prediction_canonical_question_group)` empty on 419
of ~970 days (43%) across the whole history, INCLUDING today (2026-08-17) — an active, ongoing gap, not
a stale historical artifact. Meanwhile raw `trades` for POLYMARKET is only divergent on 33 days — real
trades ARE being captured on most days. This means the BUNDLED CQG-rollup manifest row
(`market_tick_data_service/engine/orchestrator/manifest_finalize.py::_finalize_prediction_bundles`,
`data_type=prediction_canonical_question_group`, shard atom per `/codex/04-architecture/
shard-level-failure-isolation.md`) is systematically failing to reflect real captured trades data on
~43% of days, while the underlying raw trades DO exist.

Traced the write path (`market_tick_data_service/engine/orchestrator/`):
- `partitioned_writer.py::PartitionedTickWriter._write_group` calls `_update_prediction_counts` on
  EVERY `write_chunk` group (gated only on `asset_group=="prediction"` +
  `"canonical_question_group" in group_df.columns` — genuinely data-type-agnostic, so `trades` writes
  should feed it) — populates `self._prediction_cluster_counts[cqg][symbol] += len(sub_df)`.
- `venue_fetch.py::_record_venue_shard_counts` (called post-write) copies
  `writer.prediction_cluster_counts` into `state.prediction_cluster_counts_by_venue[venue]` ONLY
  `if writer.prediction_cluster_counts:` (truthy check).
- `manifest_finalize.py::_finalize_prediction_bundles` early-returns if the WHOLE
  `state.prediction_cluster_counts_by_venue` dict is empty (line 533), else iterates every venue
  present and for each `cqg` in `cqg_counts` calls `record_captured_from_counts`; every
  `CanonicalQuestionGroup` member NOT present in `cqg_counts` gets `record_empty(SOURCE_RETURNED_ZERO)`
  (the "zero-trading-day sentinel", line ~618) — this is what produces `empty_confirmed` rows.
- `umi_tick_provider.py::_route_prediction` DOES forward the same `writer=` the orchestrator passes
  for every other asset_group (line 559) — so on its face POLYMARKET's batch trades SHOULD flow
  through the same writer whose counts feed the bundle. **Not yet confirmed**: whether the writer
  instance that captures POLYMARKET's `trades` chunk on a given date is the SAME instance object
  `_record_venue_shard_counts`/`_finalize_prediction_bundles` read `state.prediction_cluster_counts_by_venue`
  from for that date's run, or whether the historical rows (spanning back to 2024-01-01, well before
  this bundle mechanism was "added 2026-06-16" per `expected_coverage.py`'s own comment) were instead
  written by a ONE-TIME migration (`market_tick_data_service/scripts/rebuild_prediction_manifest.py` /
  `canonicalize_prediction_manifest_2026_07_18.py --bundle-mode normalize`) whose own classification
  logic may not be what today's live orchestrator re-derives — i.e. whether TODAY's (2026-08-17) cell
  reflects a fresh, currently-buggy live/batch run, or a frozen migration-era stamp the daily
  orchestrator never revisits for already-`empty_confirmed` dates.

**Next debugging step (not yet done — needs a `data_engineering`/`backend_engineer` pass with time to
verify against live data)**: for ONE recent divergent date (e.g. 2026-08-16, where `trades` itself is
NOT divergent — real trades exist), read the actual `trades` parquet shard(s) for POLYMARKET that day,
count distinct real `canonical_question_group` values with real rows, and compare against what the
`prediction_canonical_question_group` manifest row for that date actually shows. If real CQGs with
real trades exist but the manifest row is `empty_confirmed`, the bug is confirmed in the write path
above (most likely: the orchestrator's per-date run instantiates a FRESH writer per data_type/route
rather than sharing one writer instance across `trades` + the finalize pass, so
`prediction_cluster_counts` never survives to the finalize step that reads it). If genuinely zero CQGs
traded that day, the bug is in the ORACLE (`expected_coverage.py`'s `_PREDICTION["POLYMARKET"]` blanket
`SHOULD_HAVE_DATA` for every calendar day, never accounting for a legitimately zero-activity day) and
the fix is either a genuine zero-activity-bar honest-empty exemption or scoping expected_coverage's
per-day check to whether ANY market was live/open that day.

## Diagnosis update (2026-08-17, slot-9) — root cause CONFIRMED via code-path trace, third mechanism

The two hypotheses slot-14 left open are both **disproven** by a full call-chain read (not yet a live-data
read — see "Still needed" below): the writer-lifetime hypothesis is disproven structurally — the SAME
`PartitionedTickWriter` instance created once per `(venue, date)` in
`venue_fetch.py::_process_venue` is threaded UNCHANGED through
`umi_tick_provider._route_prediction` → `PolymarketAdapter.download_batch` →
`_fetch_trades_for_date` → `_polymarket_helpers._aggregate_trade_results`, which calls
`writer.write_chunk(df)` directly on that same object per `condition_id`. No second writer, no
cross-instance gap.

The classifier-miss hypothesis is also disproven: `classify_polymarket_to_canonical_group`
(`unified-api-contracts/.../predictions/classifiers.py:587`) no longer returns `None` for an
unclassifiable market — a prior fix changed the residual to `CanonicalQuestionGroup.OTHER` /
`MISC_NOVELTY` specifically so classification failure doesn't silently vanish. Virtually every real
trade lands in SOME CQG bucket.

**The real mechanism: the CQG-bundle's cluster-coverage gate is all-or-nothing over every LISTED
market in the group, not just the markets that actually traded that day.**

1. `manifest_finalize.py::_finalize_prediction_bundles` calls, per `(cqg, day)`:
   `pred_writer.record_captured_from_counts(..., expected_root_clusters=expected_clusters,
   observed_clusters=market_counts, ...)`, where `expected_clusters` comes from
   `preflight.py::_load_expected_clusters_for_cqg` — which reads
   `market_lifecycle/by_canonical_group/day={date}/group={cqg}/market_lifecycle.parquet` from the
   instruments-service prediction bucket and returns `{market_id: 1}` for **every market_id listed in
   the group that day**, not just markets with real trading activity.
2. `unified-trading-library/.../manifest_writer/_writer_captured.py::record_captured_from_counts` (line
   ~676) runs `check_cluster_coverage_from_counts(observed_clusters, expected_root_clusters=expected)`
   (`_writer_validation.py:288`) — this is a **hard ALL-OR-NOTHING gate**: `missing = {cluster: min_rows
   for cluster, min_rows in expected.items() if observed.get(cluster, 0) < min_rows}`; if `missing` is
   non-empty (i.e. even ONE listed market_id in the group had zero observed trades that day), the whole
   bundle routes to `record_failed(ClusterCoverageError)` — **never** `record_captured`, regardless of
   how much real trading happened in the group's OTHER markets.
3. Meanwhile the zero-trading-day sentinel loop (same file, line ~611) emits `record_empty` rows for
   every `CanonicalQuestionGroup` member **entirely absent** from `cqg_counts` (i.e. groups with literally
   zero trades anywhere).
4. `detect_manifest_divergence.py::_classify` groups by `(asset_group, venue, data_type, date)` — NOT by
   `instrument_id`/CQG — so a single day's classification is `OK_CAPTURED` if ANY row for that cell is
   `captured`, else `DIVERGENT_EMPTY` if ANY row is `empty_confirmed`. Given step 2, a day where every
   ACTIVE CQG has at least one thin/illiquid market with zero trades (extremely common for
   multi-bucket groups like HOURLY price-direction markets, which can list 24 markets/day) never
   produces a single `captured` row — every group either fails coverage (→ `attempted_failed`, step 2)
   or has zero trades (→ `empty_confirmed`, step 3) — so the day classifies `DIVERGENT_EMPTY` even
   though real trades were captured and are sitting in the raw `trades` parquet the whole time.

This is a **design gap, not a transient bug**: the coverage gate conflates "every market currently
LISTED for a CQG" with "every market that traders were actually active in" — appropriate for a TradFi
chain bundle (CME options/futures clusters are genuinely all-or-nothing per cutover register precedent)
but wrong for prediction markets, where a group legitimately has partial daily activity across its
listed members. This explains the "spans the ENTIRE coverage history + TODAY" observation precisely —
it isn't a regression from a specific commit, it is structural to how `_load_expected_clusters_for_cqg`
was scoped when the bundle-write path was built (`wave2_polymarket_record_captured_from_counts_2026_05_09`).

**Fix requires a semantics decision, not a mechanical patch** — two candidate directions, either viable:
  (a) Loosen `_finalize_prediction_bundles`'s call so a CQG bundle with ANY observed trading activity
      routes to `record_captured_from_counts` with `expected_root_clusters` narrowed to observed-or-known-
      active markets (drop the all-or-nothing gate for this data_type specifically — `record_captured`
      already tracks `instrument_count`/`observed_clusters` so partial coverage stays visible, just not
      fatal); or
  (b) Keep the strict gate but change `_load_expected_clusters_for_cqg`'s source query so "expected"
      means "known to be actively promoted for trading that day" (if instruments-service exposes that
      distinction) rather than "every listed market_id", so illiquid-but-listed markets don't poison
      the whole bundle.
  (a) is the smaller, safer change (single call-site in MTDS) and matches how the analogous chain-bundle
  case already tolerates partial legs via `quarantined_legs` visibility rather than an outright failure;
  (b) requires an instruments-service data-model change with unknown blast radius on TradFi's identical
  `check_cluster_coverage_from_counts` consumer (CME options/futures — where all-or-nothing IS probably
  still correct). Recommend (a), scoped to the prediction CQG bundle call-site only —
  `check_cluster_coverage_from_counts` itself and its TradFi callers are untouched.

**Still needed before shipping (a)**: one live spot-check (e.g. 2026-08-16) confirming
`market_lifecycle.parquet` really does list markets with zero real trades that day (not a separate bug
in the IS lifecycle writer itself) — this diagnosis is from a full code-path read, not yet a live-data
read, per CLAUDE.md CLAIM≤MEASUREMENT. Needs `data_engineering`/`backend_engineer` GCS read access +
an operator ruling on direction (a) vs (b) before landing on prod data-correctness code shared with
TradFi chain bundles — filed as a new todo below rather than freelanced, since both directions touch
shared prod manifest-write semantics beyond this one venue.

**cefi (58,362 DIVERGENT_EMPTY) and tradfi (8,468 DIVERGENT_EMPTY) — NOT fully diagnosed this session.**
`detect_manifest_divergence.py --asset-group cefi` / `--asset-group tradfi` both OOM the shared host
just reading the manifest index alone (`_index/availability_index.parquet`) — tradfi hit 14.4M raw
rows and exceeded a 4GB RSS cap before even reaching the aggregate/join step; cefi's is larger still.
Per `/codex/05-infrastructure/vm-launcher-runbook.md` + RULES.md § "Bound memory BEFORE running any
heavy script directly on this shared host" — this is genuinely corpus-scale and belongs on a dedicated
VM, not this shared host. The manifest_hygiene CSV samples (venue=UPBIT/trades for cefi,
venue=NYSE/ohlcv_1s for tradfi, both only the last 3-4 dates) are NOT proof those venues dominate the
total — the sample is whatever survived a 2000-char stdout-tail truncation, not the top-N breakdown by
volume (see `manifest_hygiene_daily.py::_read_divergence_csv`'s own docstring on this exact failure
mode — a 2026-07-06 finding on a different AG found the tail undercounted by 2-3 orders of magnitude
when it fell back to the tail path; here it's unclear if the CSV path or the tail-fallback path was hit
for cefi/tradfi specifically). Needs a VM-launched run of `detect_manifest_divergence.py --asset-group
{cefi,tradfi}` (real per-cell CSV, not the stdout tail) before any code-vs-real-gap verdict.

**sports (0 DIVERGENT_EMPTY) — clean, no action needed.**

## Diagnosis update (2026-08-17, slot-14 round 2) — LIVE MEASUREMENT REFUTES BOTH prior hypotheses

Per the "Still needed before shipping (a)" todo (live spot-check on a divergent date where `trades` itself
is captured OK), ran a narrowly-filtered read of prod `_index/availability_index.parquet`
(bucket `market-data-tick-pred-prd-central-element-323112`, `resolve_bucket_name(cloud="gcp",
kind="market-data-tick-prediction")`, 209.8MB / 2,805,608 rows total, filtered in-memory to
`venue=POLYMARKET, data_type=prediction_canonical_question_group` for one date at a time — no new
whole-corpus walk). Script: `scripts/dev/run-bounded-analysis.sh`-wrapped, kept in scratchpad, not
committed (throwaway read-only diagnostic).

**Picked dates via measurement, not guesswork**: cross-referencing `divergence_2026-08-17.csv`'s own
per-date rows, the ONLY 3 dates across the ENTIRE ~2.5-year history where `trades` is `OK_CAPTURED`
(any_captured=True) **but** `prediction_canonical_question_group` is `DIVERGENT_EMPTY` are 2026-07-27,
2026-08-03, and 2026-08-17 (today, still in-progress — excluded). Used 2026-07-27 and 2026-08-03 — every
OTHER CQG-divergent date in the history is ALSO trades-divergent (2024-01-01→2025-03-13, and
2026-08-09→2026-08-16 — trades itself hasn't captured POLYMARKET for over a week; a second, separate
finding, not yet triaged — see new P1 todo below), so those dates can't isolate the CQG-bundle mechanism
from a plain trades-capture outage.

**Result — both prior hypotheses are refuted by the live data:**

1. **Slot-9's all-or-nothing `ClusterCoverageError`/coverage-gate hypothesis is REFUTED**: zero
   `attempted_failed` rows exist for `(POLYMARKET, prediction_canonical_question_group)` on EITHER test
   date (0/79 on 2026-08-03, 0/90 on 2026-07-27). That mechanism's own code
   (`record_captured_from_counts` → `check_cluster_coverage_from_counts`) can ONLY ever produce
   `record_failed`/`attempted_failed` rows on a coverage miss — never `empty_confirmed` or
   `expected_unattempted`. If the coverage gate were firing, these would show `attempted_failed`, not
   the profile actually observed.
2. **Slot-14's original "frozen migration-era stamp" hypothesis is ALSO REFUTED**: `written_at`/
   `attempted_at` for these rows are timestamped on (or within days of) the row's OWN `date`
   (e.g. `2026-08-03T01:32:40Z` for the 2026-08-03 cell, `2026-07-27T01:32:36Z` for 2026-07-27) — not a
   frozen `2026-07-18` migration-script stamp. Something IS actively (re)writing these cells near their
   processing date.
3. **The REAL measured profile** — capture_status breakdown for `(POLYMARKET,
   prediction_canonical_question_group)`:
   - 2026-08-03 (79 rows): 67 `expected_unattempted` (85%), 12 `empty_confirmed` (reason
     `EXPECTED_INSTRUMENT_DELISTED` ×12).
   - 2026-07-27 (90 rows): 56 `expected_unattempted` (62%), 34 `empty_confirmed` (reason
     `EXPECTED_INSTRUMENT_DELISTED` ×28, `EXPECTED_INSTRUMENT_NOT_LISTED` ×6).
   - `expected_unattempted` dominating means `_finalize_prediction_bundles`'s own per-CQG sentinel loop
     (`manifest_finalize.py` line ~611, `for cqg_member in CanonicalQuestionGroup: ... record_empty(...,
     reason="SOURCE_RETURNED_ZERO")`) is NOT the process touching most of these rows — that loop
     unconditionally iterates every `CanonicalQuestionGroup` member and would stamp `SOURCE_RETURNED_ZERO`
     on all of them, not leave 62-85% at `expected_unattempted` (materialised-by-writer / never-attempted)
     and stamp the rest with a DIFFERENT reason vocabulary.
   - The `EXPECTED_INSTRUMENT_DELISTED`/`_NOT_LISTED` reasons trace to
     `market_tick_data_service/engine/orchestrator/prediction_tier3_lifecycle.py::_classify_prediction_tier3_reason`
     — a SEPARATE "Tier-3 sentinel fan-out" (split out of `sentinels.py`) whose own docstring describes it
     as classifying **per-market condition_id/ticker `trades` cells** against the lifecycle map, not
     CQG-bundle cells. Whether this tier-3 path is being (mis)applied against CQG-level `instrument_id`
     values too, or a third still-unidentified writer shares its reason vocabulary, is **not yet
     confirmed** — needs a read of `sentinels.py`'s tier-3 fan-out call site to see what `data_type`/
     `instrument_id` set it iterates for prediction.

**Conclusion**: `_finalize_prediction_bundles` (the CQG-bundle finalize path both slot-14's original and
slot-9's diagnoses centered on) does not appear to be the process actually producing most of these
manifest rows in production — its own early-return guard (`if not prediction_cluster_counts_by_venue:
return`, line 533) or the `_record_venue_shard_counts` truthy-check (`if writer.prediction_cluster_counts:`)
may be silently skipping POLYMARKET on these dates despite real trades being captured that day (37/319,830
and 8/196,303 trades rows were `captured`, so SOME `write_chunk` activity occurred). **Neither candidate
fix (a) nor (b) from the "Diagnosis update (slot-9)" section addresses this** — both assume the
all-or-nothing coverage gate is the live code path producing the divergence, which this measurement
disproves. Implementing either now would ship a fix for a disproven mechanism on prod data-correctness
code. The operator-ruling todo below is retargeted accordingly — do NOT rule on (a) vs (b) as originally
framed; the open question is now "why does `_finalize_prediction_bundles` not reach POLYMARKET's CQGs at
all on days with real captured trades, and what does the Tier-3 sentinel fan-out's `EXPECTED_INSTRUMENT_
DELISTED/NOT_LISTED` stamping actually cover for this data_type" — a fresh code-path trace, not an (a)/(b)
choice.

## Diagnosis update (2026-08-18, slot-6) — write-path structurally sound; two new candidate gaps identified, live check still required

Followed the P1 todo's directive to check the two named suspects: `_finalize_prediction_bundles`'s
line-533 early-return, and `_record_venue_shard_counts`'s truthy-check.

**Traced the full write-time accumulation chain end-to-end — no structural gap found in it.**
`partitioned_writer.py::_update_prediction_counts` (line 557) is called unconditionally on EVERY
`write_chunk` group when `asset_group=="prediction"` + a `canonical_question_group` column is present +
`symbol_str` is truthy — this is genuinely data-type-agnostic (confirms slot-14's original claim).
`polymarket_adapter.py::_annotate_cid_dataframe` (line 461-466) stamps `canonical_question_group`
unconditionally on EVERY cid's trades DataFrame, before `write_chunk` is ever called
(`_polymarket_helpers.py::_aggregate_trade_results`, line 277-280) — so a captured POLYMARKET trades row
should always carry a classified group by the time it reaches the writer.

**Ruled out one new hypothesis this session**: an unguarded `ValueError` from
`validate_canonical_question_group` (`unified-api-contracts/.../write_guard.py:55`, raises if the value
isn't a genuine `CanonicalQuestionGroup` enum member) mid-way through the per-cid loop in
`_run_taxonomy_classifiers` (`_polymarket_helpers.py:237-244`, no try/except around the loop body) could
plausibly abort processing of later cids in a day's fetch, silently truncating that day's
`_prediction_cluster_counts` contribution. **Disproven by reading `classify_polymarket_to_canonical_group`
itself** (`unified-api-contracts/.../classifiers.py:587-624`): its return type is always a genuine
`CanonicalQuestionGroup` enum member (falls through to `OTHER`/`MISC_NOVELTY` for unmatched combinations,
never a raw string) — so `validate_canonical_question_group(group.value)` cannot raise from this call
site by construction. Not the mechanism.

**Two new candidate gaps identified, NEITHER confirmed against live data (still needed, see todo below)**:
1. Slot-9's "structural" disproof of the writer-lifetime hypothesis confirmed ONE writer instance is
   threaded through the trades path in general, but did not specifically verify instance identity for
   the two measured-divergent dates (2026-07-27, 2026-08-03) — a batch-chunked or retried fetch for those
   SPECIFIC dates could still construct more than one writer if the orchestrator's retry/chunking logic
   (not yet read this session) ever re-invokes `download_batch` with a fresh writer mid-run.
2. `_prediction_cluster_counts` is accumulated across ALL prediction data_types sharing one
   `symbol`-keyed bucket per CQG (no data_type discrimination in `_update_prediction_counts`) — the
   37/319,830 and 8/196,303 "captured" counts slot-14 cited were read from the manifest's `trades`
   data_type cell specifically; whether those captured trades rows are the SAME underlying write_chunk
   calls that populate `_prediction_cluster_counts`, versus a differently-batched fetch path (e.g. the
   `book_snapshot_5` gate at `_polymarket_helpers.py:411`, which shares the same accumulator), was not
   verified this session.

**Why this session did not go further**: both remaining candidates require live-data verification (actual
run logs for 2026-07-27/2026-08-03, or a live instrumented count at the `_record_venue_shard_counts` call
site) — a third round of code-only reading without live data is unlikely to add new information past what
two prior sessions + this one already extracted from the same call chain. Per CLAUDE.md CLAIM≤MEASUREMENT,
recording this as unconfirmed rather than picking one to ship a fix against.

## Diagnosis update (2026-08-18, slot-19) — POLYMARKET raw `trades` gap ROOT-CAUSED: upstream instruments-service catalogue stopped writing POLYMARKET, not an MTDS/adapter bug

Per the "SEPARATE, more acute finding" P1 todo (diagnose whether POLYMARKET trades capture broke
recently vs a genuine multi-day lull), started from `polymarket_adapter.py` per the todo's own
pointer. `_RETRYABLE_STATUS_CODES`/CF-11 fetch-failure signalling (`_emit_fetch_failures` →
`failed_per_dt["trades"] = TRADES_FETCH_RETRIES_EXHAUSTED` → `attempted_failed`) is intact and
correctly wired — so if the Data API itself were erroring/rate-limiting, the manifest would show
`attempted_failed` rows. It does not.

**Live manifest read** (`_index/availability_index.parquet`,
`market-data-tick-pred-prd-central-element-323112`, filtered to
`venue=POLYMARKET,data_type=trades,date∈[2026-08-01,2026-08-17]` — no new whole-corpus walk, same
bounded-read pattern as slot-14's round-2 measurement):

- Every divergent date (2026-08-10, 08-12 → 08-16) shows EXACTLY 10 manifest rows, ALL
  `capture_status=empty_confirmed, reason=SOURCE_RETURNED_ZERO`, `written_at` near-live (day+1
  ~01:0x UTC) — zero `attempted_failed` rows anywhere in the range. Contrast with a healthy day
  (2026-08-11): ~50 rows, a real mix of `captured` (up to 464 trades/shard) and
  `empty_confirmed` — the normal shape of "most shards traded, a few didn't".
- The suspiciously-constant "10 rows, all zero" on every divergent date is NOT a trading lull —
  it is the shard-level zero-trading-day sentinel stamping a FIXED small shard set because the
  adapter had **zero condition_ids to query that day**, not because real markets returned no
  trades.

**Traced to source — `PolymarketAdapter._load_instruments_from_gcs` → `load_polymarket_instruments_df`**
(`market_tick_data_service/market_interface/adapters/prediction/_polymarket_helpers.py`) reads
`instrument_availability/by_date/day={date}/.../venue=POLYMARKET/.../instruments.parquet` from the
**instruments-service** prediction bucket (`instruments-store-pred-prd-central-element-323112`) —
this is `cid_to_shard` in `download_batch`; empty → the early-return "no instruments" path (never
calls the Data API at all, so no failure is ever possible to signal).

**Live GCS listing of that exact prefix, per date** (`instrument_availability/by_date/day={date}/`,
total blobs vs POLYMARKET-venue blobs):

| date | total blobs | POLYMARKET blobs |
| --- | --- | --- |
| 2026-08-08 | 108 | 62 (healthy) |
| 2026-08-09 | 79 | 33 (degraded but present) |
| 2026-08-10 | 46 | **0** |
| 2026-08-11 | 51 | 2 (anomalous partial blip — OTHER shard only) |
| 2026-08-12 | 49 | **0** |
| 2026-08-13 | 49 | **0** |
| 2026-08-14 | 49 | **0** |
| 2026-08-15 | 50 | **0** |
| 2026-08-16 | 50 | **0** |
| 2026-08-17 | 50 | **0** (today, in progress) |

Other venues' instrument-availability files ARE present in the SAME day's listing on every date
(total blobs stays 46-50 throughout) — this rules out an instruments-service-wide outage. The gap
is POLYMARKET-specific, started between 2026-08-09 and 2026-08-10, and is STILL ONGOING as of
2026-08-17.

**Conclusion**: the POLYMARKET raw-`trades` `DIVERGENT_EMPTY` finding is a symptom, not the bug —
the actual defect is in **instruments-service**'s POLYMARKET instrument-catalogue writer
(`instruments_service/engine/orchestrator/process_write.py::_write_prediction_venue` per
`instrument_availability_paths.py`'s own docstring), which stopped emitting POLYMARKET
`instruments.parquet` objects around 2026-08-10 while continuing to write every other venue. MTDS's
adapter is working exactly as designed (CF-11 signalling intact); it simply has no condition_ids to
fetch. This is a DIFFERENT repo (`instruments-service`) than this issue doc's `repos:` frontmatter
names — filed as a new todo below per findings-triage rather than freelanced across repos.

**Not yet done** (out of this diagnosis's scope — instruments-service code, not
market-tick-data-service/unified-trading-library): why `_write_prediction_venue` stopped emitting
POLYMARKET specifically on 2026-08-10 (a recent instruments-service commit/config change,
credential/rate-limit issue on IS's OWN Polymarket catalogue source, or a filter/classification
change that now excludes POLYMARKET) — needs an `instruments-service` repo trace + its own run logs
for 2026-08-09→2026-08-10.

## Diagnosis update (2026-08-18, slot-22) — LIVE `written_at` measurement REFUTES slot-14 round 2's "near-live" conclusion; every known writer for the DELISTED/NOT_LISTED reasons is now ruled out

Per the open `[OPERATOR/DATA] P1. LIVE-verify` todo's part 2 (what does
`prediction_tier3_lifecycle.py::_classify_prediction_tier3_reason` actually cover), read the
call site directly: `sentinels.py::_emit_tier3_for_dt` line ~685-689 loads the lifecycle map
(and therefore can ever produce a `_classify_prediction_tier3_reason` verdict) **only when
`venue.upper() in {"POLYMARKET","KALSHI"} and dt == "trades"`** — confirmed by reading the exact
guard, not inferred from the docstring. For any other `dt` (including
`prediction_canonical_question_group`), `_prediction_lifecycle_map` is `{}`, so `_lc_reason` is
always `None` and the branch never stamps `EXPECTED_INSTRUMENT_DELISTED`/`_NOT_LISTED`. **This
means the Tier-3 sentinel fan-out — the mechanism BOTH prior diagnosis rounds pointed at as the
likely source of those reasons on CQG cells — structurally cannot be the writer.** The
`prediction_tier3_lifecycle.py` module docstring ("classifying per-market condition_id/ticker
trades cells") is accurate; the confusion in prior rounds came from `_emit_lifecycle_prefetch_skips`
(`_polymarket_helpers.py:321-340`)'s own docstring claiming "the downstream Tier-3 sentinel fan-out
... independently re-derives this classification" — true for `trades`, but that docstring doesn't
scope the claim to `dt=="trades"` and reads as if it covers CQG too. **Fix the misleading docstring
in the same turn this is read** (CLAUDE.md "a doc/comment that misled you is a finding") — filed as
a P3 todo below rather than freelanced (touches prod adapter code, wants its own QG pass).

**Live measurement (bounded, no new whole-corpus walk)** — ran a `scripts/dev/run-bounded-analysis.sh`-
wrapped read of `_index/availability_index.parquet` (bucket
`market-data-tick-pred-prd-central-element-323112`), filtered in-memory to
`venue=POLYMARKET, data_type∈{trades,prediction_canonical_question_group}, date∈{2026-07-27,2026-08-03}`
(516,302 rows before filter to the two dates; script not committed, scratchpad-only per the
diagnostic-throwaway convention). This is the SAME cell slot-14 round 2 measured — this session
pulled `written_at` distributions the prior measurement didn't report.

**Result: the `written_at` values are NOT clustered near each row's own date — they show REPEATED
REWRITES, most heavily on 2026-08-09.**

| cell | capture_status/error_reason breakdown | distinct `written_at` dates observed |
| --- | --- | --- |
| POLYMARKET/prediction_canonical_question_group/2026-07-27 (90 rows) | 56 `expected_unattempted`; 34 `empty_confirmed` (28 `EXPECTED_INSTRUMENT_DELISTED`, 6 `EXPECTED_INSTRUMENT_NOT_LISTED`) | 2026-07-27 (original), **2026-07-30, 2026-07-31**, 2026-08-09 (×2 distinct clusters: ~01:32 UTC and ~14:07-14:36 UTC) |
| POLYMARKET/prediction_canonical_question_group/2026-08-03 (79 rows) | 67 `expected_unattempted`; 12 `empty_confirmed` (`EXPECTED_INSTRUMENT_DELISTED`) | 2026-08-03 (original), 2026-08-09 (×2 clusters: ~01:32 UTC and ~14:06-14:24 UTC) |
| POLYMARKET/trades/2026-07-27 (196,303 rows) | 196,295 `empty_confirmed(SOURCE_RETURNED_ZERO)`; 8 `captured` | 2026-07-28 (8 distinct sub-timestamps, the original per-date run), **2026-08-09T14:02:30.2xxxxx (196,303 near-identical microsecond-apart stamps — a full bulk rewrite of every row in this shard)** |
| POLYMARKET/trades/2026-08-03 (319,830 rows) | 319,793 `empty_confirmed`; 37 `captured` | 2026-08-04 (original per-date run), 2026-08-05 (more original-run stamps) — did not need to sample past this to establish the point |

Slot-14 round 2 measured `written_at ≈ 2026-08-03T01:32:40Z`/`2026-07-27T01:32:36Z` for these cells
and concluded "near-live, not frozen" — **that measurement is real but incomplete**: it read only
one `written_at` value per cell (or an aggregate) and didn't check for multiple distinct values.
The `~01:32 UTC` stamp IS present and IS close to each row's own date — but it is not the ONLY
write event, and — critically — it recurs on LATER dates too for the SAME (venue, data_type, date)
cell: the 2026-07-27 cell was rewritten again at `2026-07-30T01:32`, `2026-07-31T01:33`, AND
`2026-08-09T01:32`, always at the same ~01:32 UTC time-of-day. A live per-date orchestrator run for
`date=2026-07-27` only runs once, shortly after that date; it does not explain why the SAME cell
gets touched again 3, 4, and 13 days later, always at the same time of day.

**Ruled out `canonicalize_prediction_manifest_2026_07_18.py --bundle-mode normalize` as the source
of the DELISTED/NOT_LISTED content** (though it IS almost certainly the 08-09 ~14:0x-14:3x cluster —
its `_apply_targets_in_place` only mutates `data_type`/`instrument_type`/`source`, confirmed by
reading the function body; `build_canonical_frame`/`_apply_additive_shard` unconditionally bump
`written_at = datetime.now(UTC).isoformat()` on line 722 for every row it touches, **regardless of
whether content changed** — this is the exact "fresh written_at, unchanged error_reason" signature
measured live). It never touches `capture_status`/`error_reason` — grep confirms zero references
to `EmptyConfirmedReason`/`EXPECTED_INSTRUMENT_*` anywhere in the file. Likewise ruled out
`rebuild_prediction_manifest.py` (zero references to `EmptyConfirmedReason`/`EXPECTED_INSTRUMENT_*`
either). And per the docstring-vs-guard finding above, the Tier-3 sentinel fan-out cannot write
these reasons for `dt="prediction_canonical_question_group"` — its lifecycle map is `{}` for any
`dt != "trades"`. `_finalize_prediction_bundles` (the live per-date CQG writer) also cannot: its
only three write calls are `record_captured_from_counts` (success path), `record_failed(error=
"missing_available_at_envelope")`, and `record_empty(reason="SOURCE_RETURNED_ZERO")` — no
`EXPECTED_INSTRUMENT_DELISTED`/`_NOT_LISTED` reason string appears anywhere in
`manifest_finalize.py`'s CQG code path (confirmed by direct read, not grep-absence).

**Conclusion: a FOURTH, still-unidentified writer produced the ORIGINAL `EXPECTED_INSTRUMENT_
DELISTED`/`_NOT_LISTED` classification on these CQG cells** — every writer in the current codebase
that touches this cell has now been read and ruled out (`_finalize_prediction_bundles`,
`_emit_tier3_for_dt`, `canonicalize_prediction_manifest_2026_07_18.py`,
`rebuild_prediction_manifest.py`). Two live possibilities, neither yet confirmed:
(1) the original stamp predates all four of these — an EARLIER, now-removed or since-narrowed
version of the Tier-3 fan-out (before the `dt == "trades"` guard was added — the file's own header
says it was "Extracted from sentinels.py" and the 2026-07-14 P1 plan
`prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md` may show the guard
narrowing from "all prediction dts" to "trades only" without a corresponding manifest rewrite of
already-stamped CQG rows — this is a git-history/plan-history question, answerable without new live
GCS reads); or (2) there is a recurring ~01:32 UTC daily process (NOT the documented `0 9 * * *`
empty re-probe/auto-flip cron, which fires 8 hours later and only re-touches TODAY's new empties,
not a cell 3-13 days in the past) that neither this nor any prior session has located — needs a
search of Cloud Scheduler job configs / `deployment-service`'s prediction-specific cron registrations
for anything firing near 01:3x UTC.

This does not change the operator-ruling ask from the prior round (still needed: whether to loosen
the coverage gate or not) — it DOES mean that ruling should NOT be made on the assumption that the
current live orchestrator code is what's producing these specific manifest rows; it structurally
is not, for either candidate CQG-bundle writer that exists today.

## Diagnosis update (2026-08-20, slot-33) — ROOT-CAUSED + FIXED via live reproduction: Gamma's pagination-offset ceiling

Per the still-open P1 todo ("trace WHY instruments-service's POLYMARKET catalogue writer stopped emitting"),
traced the URDI fetch stage upstream of the write path slot-19 pinpointed (2026-08-18): `_write_prediction_venue`
only ever runs when `venue_str in df.groupby("venue")` — i.e. only if the URDI fetch stage
(`urdi_reference_provider.py::_fetch_one_venue` → `PolymarketReferenceDataAdapter.get_instruments_cached`)
returned at least one record for POLYMARKET that day. Traced the fetch call chain
(`process_fetch.py::_fetch_urdi_records` → `fetch_instruments_for_all_venues` → `_fetch_one_venue` →
`get_adapter_for_canonical_venue` → `PolymarketReferenceDataAdapter.get_instruments`) and ruled out the two
`4b55c57b` refactor (2026-08-09 23:36, deleted the dead `_cross_reference_fixture()` capability) call sites —
`get_adapter_for_canonical_venue`'s `elif adapter_key == "polymarket"` branch it removed just falls through to
the generic `create_reference_data_adapter("polymarket", ...)` else-branch, which resolves `_ADAPTERS["polymarket"]
= PolymarketReferenceDataAdapter` correctly (confirmed by direct read) — not the bug.

**Live-reproduced the actual bug** (bounded, read-only, public no-auth Gamma endpoint — no GCS/prod credentials
touched): ran `PolymarketReferenceDataAdapter().get_instruments(date=None)` directly (this slot's own freshly
`uv sync`'d venv) and it failed with `RuntimeError: Polymarket gamma/markets fetch failed (error_code=UNKNOWN,
retry_safe=True): 422, message='Unprocessable Entity', url='https://gamma-api.polymarket.com/markets?...
&offset=2100&order=volume24hr&ascending=false'` — i.e. **right now, today, the live Gamma `/markets` endpoint
has an undocumented hard pagination-offset ceiling: it 422s once `offset` crosses ~2000-2100.**

**Mechanism, confirmed by code read**: `57c71bd4` (2026-08-09 08:55 UTC, "fix(polymarket): remove silent
top-2000-by-volume live-market cap") raised `_MAX_PAGES_ACTIVE` from 20 to 10000 specifically to stop the
live-mode pagination loop (`adapter.py::get_instruments`) from silently truncating the active-market universe
below 2000 markets. That fix's OWN intent was correct (the old cap WAS silently truncating), but it didn't
account for Gamma's real offset ceiling. Once the live universe exceeds ~2100 markets (apparently the normal
case now — reproduced today), the loop always pages into the 422. `adapter.py::_fetch_page`'s error handler
deliberately RAISES on any page failure (documented, correct CF-11 behaviour for genuine transient errors — "a
mid-pagination page failure must NOT silently truncate the live universe... RAISE so the per-venue handler
records the cell attempted_failed"), but the raise happens INSIDE the same loop that's still accumulating
`results` locally, with no try/except around the loop preserving what was already fetched — so the exception
propagates out of `get_instruments()` entirely and **discards every already-successfully-fetched page along
with it**. `urdi_reference_provider.py::_fetch_one_venue` catches the `RuntimeError`, classifies it
`RETRY_EXHAUSTED`/retryable, and returns `[]` for POLYMARKET that call. Since the underlying 422 is a
deterministic API-side wall (not a transient blip), every retry hits the identical boundary — POLYMARKET
contributes literally zero `InstrumentRecord`s to that day's fetch, so `venue == "POLYMARKET"` never appears in
the write-stage groupby and `_write_prediction_venue` is never invoked at all. This is exactly why NO GCS
objects (not even an `attempted_failed`/`empty_confirmed` manifest stamp) appear for POLYMARKET on affected
days — nothing downstream of the fetch ever runs. 57c71bd4 turned "truncate at ~2000" into "return zero, every
run" the moment the live universe crossed the offset ceiling (which it apparently did definitively by
2026-08-10, matching the observed 62→33→0 blob-count collapse slot-19 measured 2026-08-08→08-10).

**Fix shipped** (`instruments-service@a586f34102`): in `adapter.py`'s live-mode pagination loop, catch the
SPECIFIC `(page > 0, HTTP 422)` shape and treat it exactly like a genuinely-short final page — stop paging, keep
every market already fetched (restores the ~2000-2100-market universe instead of losing it entirely). Any other
failure (network, 5xx, auth, or a 422 on page 0 itself) still raises exactly as before — unchanged CF-11
fail-loud behaviour for genuine outages, regression-tested (`test_live_page_failure_raises_not_truncates`,
`test_clob_scan_midscan_failure_raises_not_truncates` still pass; two new tests added:
`test_live_pagination_422_ceiling_preserves_partial_universe`,
`test_live_pagination_non_422_failure_past_page_zero_still_raises`). `bash scripts/quality-gates.sh` green.

**Residual note — this is a partial-universe recovery, not a full fix for Gamma's ceiling.** The adapter now
returns ~2000-2100 markets (sorted `volume24hr desc`, so the highest-volume ones) instead of zero, matching (and
slightly improving on) the pre-57c71bd4 behaviour — but any market beyond the offset ceiling is still silently
absent from the catalogue, same as before 57c71bd4. A genuine fix for the FULL universe would need a different
Gamma query strategy (e.g. cursor/id-based pagination if the API supports it, or a supplemental
lowest-volume-first pass) — out of scope for this todo (which was to root-cause and stop the zero-output
regression); if the full >2100-market long tail matters, file a fresh todo for that separately rather than
scope-creep this fix.

## Todos

- [x] ✅ [CODE] P1. Manifest hygiene RED — diagnosed (not fully fixed) 2026-08-17 slot-14. See "Diagnosis"
      section above — root-cause hypothesis for prediction's 419/461-cell finding identified with code
      citations; cefi/tradfi need a VM-based re-run (local host OOMs on the manifest read alone). Split
      into the concrete follow-ups below per findings-triage (audit-scope → tracked todos, not a blind
      fix on unconfirmed root cause for prod data-correctness code).
- [x] ✅ [CODE] P1. Confirm the `(POLYMARKET, prediction_canonical_question_group)` CQG-bundle
      divergence root cause — 2026-08-17 slot-9. Both hypotheses left open by slot-14 (writer-lifetime
      gap, oracle-blanket-expects) are DISPROVEN by a full call-chain read; the real mechanism is the
      all-or-nothing `check_cluster_coverage_from_counts` gate in `record_captured_from_counts`
      (`unified-trading-library`) combined with `_load_expected_clusters_for_cqg` (`market-tick-data-service`)
      expecting EVERY listed market_id in a CQG to trade, not just active ones. See "Diagnosis update
      (2026-08-17, slot-9)" section above for the full 4-step trace + code citations. NOT a mechanical
      fix — split into the two follow-ups below since the gate is shared with TradFi chain bundles and
      the fix direction needs a decision from the operator before landing (see next todo).
- [x] ✅ [DATA] P1. Live spot-check the CQG-bundle divergence on a real prod date — 2026-08-17 slot-14
      round 2. REFUTES both prior hypotheses (see "Diagnosis update (2026-08-17, slot-14 round 2) — LIVE
      MEASUREMENT" above): zero `attempted_failed` rows found (disproves slot-9's coverage-gate theory),
      `written_at` is near-live not frozen-migration (disproves slot-14's original theory). Real profile:
      62-85% `expected_unattempted` (never touched) + a minority `empty_confirmed` stamped by
      `prediction_tier3_lifecycle.py`'s Tier-3 sentinel fan-out, not `_finalize_prediction_bundles`'s own
      sentinel. Did NOT implement (a)/(b) — both are built on the now-disproven coverage-gate premise;
      shipping either would be a fix for the wrong mechanism on prod data-correctness code. Superseded by
      the two todos below.
- [x] ✅ [BACKEND] P1. Traced 2026-08-18 slot-6 — see "Diagnosis update (2026-08-18, slot-6)" above. The
      write-time accumulation chain (`_update_prediction_counts` → writer.prediction_cluster_counts →
      `_record_venue_shard_counts` truthy-check → `_finalize_prediction_bundles`) is structurally sound
      end-to-end on a THIRD full code-path read — no gap found in it this way. Ruled out one new
      hypothesis (an unguarded classifier `ValueError` truncating a day's cid loop) with a code citation
      showing `classify_polymarket_to_canonical_group` cannot raise by construction. Root cause remains
      UNCONFIRMED — this is a code-only-reading dead end; the two remaining candidates both need live
      data, not another read. Split into the concrete live-verification todo below (does NOT supersede
      the still-open `prediction_tier3_lifecycle.py` classifier-scope question from the prior todo — kept
      below alongside it).
- [x] ✅ [DATA] P1. LIVE-verified 2026-08-18 slot-22 — see "Diagnosis update (2026-08-18, slot-22)"
      above. Confirmed via direct code read (not inference from a docstring) that
      `_classify_prediction_tier3_reason` can NEVER fire for `data_type=prediction_canonical_
      question_group` — its lifecycle map is loaded only when `dt == "trades"`
      (`sentinels.py::_emit_tier3_for_dt` line ~687). Confirmed via a live bounded `written_at` read
      of the prod manifest index that the measured `EXPECTED_INSTRUMENT_DELISTED`/`_NOT_LISTED`
      rows were rewritten MULTIPLE times (2026-07-27's cell: 07-27, 07-30, 07-31, 08-09×2; 08-03's
      cell: 08-03, 08-09×2) — REFUTES slot-14 round 2's "written_at near-live, not frozen" reading
      (that measurement only sampled one written_at value per cell). Read + ruled out every
      candidate writer currently in the codebase (`_finalize_prediction_bundles`, the Tier-3
      fan-out, `canonicalize_prediction_manifest_2026_07_18.py`, `rebuild_prediction_manifest.py`)
      as the source of the DELISTED/NOT_LISTED classification — none of them write that reason
      vocabulary for this data_type. Root cause is now narrowed to two live hypotheses (a
      now-removed/narrowed earlier Tier-3 guard, or an unidentified ~01:32 UTC recurring process)
      — split into the two todos below rather than guessed at.
- [x] ✅ [DATA] P1. Diagnosed 2026-08-18 slot-19 — see "Diagnosis update (2026-08-18, slot-19)" above.
      ROOT-CAUSED via live GCS listing (not just code read): NOT an MTDS/adapter/API bug — CF-11
      fetch-failure signalling is intact (zero `attempted_failed` rows anywhere). The real cause is
      **instruments-service** — its POLYMARKET instrument-catalogue writer
      (`instrument_availability/by_date/day={date}/.../venue=POLYMARKET/...`) stopped emitting ANY
      POLYMARKET objects starting 2026-08-10 (0 POLYMARKET blobs on 08-10, 08-12→08-17, vs 33-62 on
      08-08/08-09) while every other venue kept writing that same day. MTDS's trades adapter
      correctly has zero condition_ids to fetch → the shard-level empty sentinel stamps a fixed
      10-row `empty_confirmed`/`SOURCE_RETURNED_ZERO` placeholder, masking what is actually an
      upstream catalogue-availability gap. Split into the instruments-service-scoped todo below
      (different repo than this issue's `repos:` frontmatter — not freelanced here).
- [ ] [DATA] P2. Check git history on `sentinels.py::_emit_tier3_for_dt`'s `dt == "trades"` guard on the Tier-3
      lifecycle map (line ~687) for whether it was ever broader (e.g. covered `prediction_canonical_question_group`
      too) before being narrowed, and whether that narrowing commit left already-stamped CQG rows unrewritten
      (corrected 2026-08-19, plan-reconcile observability_master: rewrapped for line-1 completeness —
      task_template.md §3). See "Diagnosis update (2026-08-18, slot-22)" above for why this is the leading
      hypothesis for the still-unidentified writer of the `EXPECTED_INSTRUMENT_DELISTED`/`_NOT_LISTED` reasons on
      CQG cells. `market-tick-data-service`.
- [ ] [DATA] P2. Find what recurring process touches the POLYMARKET `prediction_canonical_question_group` manifest
      cell at ~01:32 UTC on dates AFTER the cell's own date (measured live: 2026-07-27's cell rewritten again at
      07-30/07-31/08-09, always ~01:32-01:33 UTC) — NOT the documented `0 9 * * *` empty re-probe/auto-flip cron
      (corrected 2026-08-19, plan-reconcile observability_master: rewrapped for line-1 completeness). Wrong time,
      and that cron only re-touches TODAY's new empties per its own spec, not a 3-13-day-old cell. Search Cloud
      Scheduler job configs / `deployment-service`'s prediction-specific cron registrations for anything firing
      near 01:3x UTC. See "Diagnosis update (2026-08-18, slot-22)" above. `deployment-service` (or wherever the
      ~01:32 cron is registered — unconfirmed).
- [x] ✅ [DATA] P3. Fixed 2026-08-19 slot-7 — `market-tick-data-service@f67a7480b3`. Scoped the misleading claim
      in `_polymarket_helpers.py::_emit_lifecycle_prefetch_skips`'s docstring to `data_type="trades"` ONLY (it now
      states the Tier-3 fan-out's lifecycle-map load is guarded on `dt == "trades"`, so `book_snapshot_5` and the
      CQG-bundle cell `prediction_canonical_question_group` never get this re-derivation) — confirmed the guard
      live at `sentinels.py::_emit_tier3_for_dt` (`venue.upper() in {"POLYMARKET","KALSHI"} and dt == "trades"`)
      before editing. Found the SAME unscoped claim, verbatim, in `kalshi_adapter.py`'s own copy of
      `_emit_lifecycle_prefetch_skips` while fixing this (not named in the original todo) — fixed both in the
      same commit per CLAUDE.md "a doc/comment that misled you is a finding, fix it in the same turn".
- [x] ✅ [DATA] P1. Traced + FIXED 2026-08-20 slot-33 — `instruments-service@a586f34102`. See "Diagnosis update
      (2026-08-20, slot-33)" below for the full live-reproduced root cause + fix. Note: the code lives in
      `process_write_venue.py::_write_prediction_venue` (split out of `process_write.py` since this todo was
      filed — `process_write.py` now only imports it), but the actual bug is upstream of that write stage
      entirely (the URDI fetch never returns any POLYMARKET records to write, so `_write_prediction_venue` is
      never even invoked for that venue on an affected day) — filing this correction inline per CLAUDE.md "a
      doc/comment that misled you is a finding, fix it in the same turn" rather than leaving the stale path.
- [ ] [DATA] P2. Launch a VM to run `detect_manifest_divergence.py --asset-group cefi` (14M+ row manifest OOMs the
      shared host at a 4GB cap) and get the real per-cell CSV breakdown (not the stdout-tail sample) — determine
      which venue(s)/data_type(s) actually drive the 58,362 DIVERGENT_EMPTY count before triaging real-gap vs
      code-bug vs oracle-bug. `market-tick-data-service`/`unified-trading-library` (the detector script's home).
      No `[OPERATOR]` gate needed (task_template.md finding U — read-only/audit/census todo, writes only a new CSV
      artifact, touches no existing prod data; corrected 2026-08-19, plan-reconcile observability_master).
- [ ] [DATA] P2. Launch a VM to run `detect_manifest_divergence.py --asset-group tradfi` (8,468 DIVERGENT_EMPTY,
      14,464,340-row manifest already confirmed to OOM a 4GB local cap) — same read-only breakdown as the cefi
      todo immediately above, same repo, same no-`[OPERATOR]`-needed justification (corrected 2026-08-19,
      plan-reconcile observability_master: this todo previously read "Same as above" with no restated action —
      task_template.md §3 line-1 completeness; same-priority todos dispatch independently, so a worker claiming
      only this line needs the full instruction, not a backward reference).

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries).
- **slot-19 2026-08-18**: root-caused the POLYMARKET raw `trades` DIVERGENT_EMPTY todo — upstream
  instruments-service catalogue gap (POLYMARKET instrument_availability writes stopped 2026-08-10),
  not an MTDS adapter bug. Flipped that todo, filed the instruments-service-scoped follow-up.
- **slot-22 2026-08-18**: LIVE-verified the CQG-bundle `EXPECTED_INSTRUMENT_DELISTED`/`_NOT_LISTED`
  question — ruled out every current-codebase writer via a mix of direct code reads and a bounded
  live `written_at` read of the prod manifest index (script scratchpad-only, not committed). Key
  finding: these rows were rewritten multiple times (not written once near-live), which refutes
  slot-14 round 2's "near-live, not frozen" reading. Flipped the LIVE-verify todo, filed two P2
  follow-ups (git-history check on the Tier-3 guard; find the ~01:32 UTC recurring writer) plus a
  P3 docstring-fix todo.
- **slot-7 2026-08-19**: flipped the P3 docstring-fix todo — `market-tick-data-service@f67a7480b3`
  scopes `_emit_lifecycle_prefetch_skips`'s Tier-3-re-derivation claim to `dt=="trades"` in BOTH
  `_polymarket_helpers.py` (the originally-named file) and `kalshi_adapter.py` (same unscoped claim
  found verbatim there while editing, not named in the original todo). Also cross-referenced this
  doc's still-open findings (cefi/tradfi VM-scale re-run, prediction instruments-service trace)
  against `manifest_hygiene_red_all_2026_08_18.md`'s duplicate daily-audit refile — closed that
  doc's todo as a cross-reference rather than re-diagnosing; the two P2 and one P1 todos above
  remain the tracked fix work for cefi/tradfi/prediction.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **slot-33 2026-08-20**: root-caused + FIXED the still-open POLYMARKET-catalogue-writer P1 todo —
  `instruments-service@a586f34102`. Live-reproduced (bounded, read-only, no-auth public endpoint):
  Polymarket's Gamma `/markets` endpoint 422s past pagination offset ~2000-2100 — an undocumented API
  ceiling `57c71bd4` (2026-08-09) didn't account for when it raised `_MAX_PAGES_ACTIVE` to stop a DIFFERENT
  silent-truncation bug. The mid-loop raise (deliberate CF-11 fail-loud design) discarded every
  already-fetched page along with the failure, so POLYMARKET returned zero records — hence zero GCS
  catalogue objects — on any day its live universe crossed the ceiling (matches the measured 62→33→0
  blob-count collapse 2026-08-08→08-10). Fixed to preserve already-fetched pages on this specific
  (page>0, HTTP 422) shape while keeping fail-loud for every other failure kind; 2 regression tests added,
  `quality-gates.sh` green. See "Diagnosis update (2026-08-20, slot-33)" above for the full trace + the
  residual-scope note (still capped at ~2000-2100 by volume, same as pre-57c71bd4 — the long tail beyond
  that is a separate, unscoped follow-up if it matters). Also corrected the todo's stale file pointer
  (`process_write.py` → `process_write_venue.py`, split out since this todo was filed) inline per CLAUDE.md.
