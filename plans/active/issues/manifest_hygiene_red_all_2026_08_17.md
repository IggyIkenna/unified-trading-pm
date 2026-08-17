---
doc_type: issue
title: "Manifest hygiene RED — 4 AG(s) with findings (2026_08_17)"
summary: >-
  Daily manifest-hygiene audit found oracle_expects_but_empty (DIVERGENT_EMPTY) candidates for
  cefi/tradfi/prediction and a 1-row schema_version_not_v9 straggler for cefi. Diagnosed 2026-08-17:
  prediction's 461-cell finding is 91% one shape — POLYMARKET's prediction_canonical_question_group
  CQG-bundle rollup is empty on 43% of days across the whole history including today, while raw trades
  capture is mostly fine. ROOT CAUSE CONFIRMED 2026-08-17 (slot-9): the all-or-nothing cluster-coverage
  gate in record_captured_from_counts requires every LISTED CQG market to trade, not just active ones —
  fix needs an operator ruling (two candidate directions, see Todos); cefi (58,362 cells) and tradfi
  (8,468 cells) still need a VM-scale re-run of detect_manifest_divergence.py (OOMs the shared host).
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
- [ ] [OPERATOR] P1. Rule on the CQG-bundle cluster-coverage fix direction — (a) loosen
      `_finalize_prediction_bundles` (`market-tick-data-service`) to route a CQG bundle with ANY
      observed trading activity to `record_captured_from_counts` with `expected_root_clusters` narrowed
      to observed-or-known-active markets (drops the all-or-nothing requirement for prediction bundles
      only — recommended, smaller blast radius) vs (b) narrow `_load_expected_clusters_for_cqg`'s
      "expected" set itself to markets known to be actively promoted that day (needs an
      instruments-service data-model change, unknown blast radius on TradFi's identical
      `check_cluster_coverage_from_counts` consumer for CME options/futures). See "Fix requires a
      semantics decision" in the diagnosis section above for the full tradeoff writeup.
- [ ] [DATA] P1. Once (a) or (b) is ruled on: live spot-check ONE recent divergent date (e.g.
      2026-08-16) confirming `market_lifecycle.parquet` really does list markets with zero real trades
      that day (rules out a separate bug in the IS lifecycle writer itself), then implement + ship the
      ruled-on fix in `market-tick-data-service` (+ `unified-trading-library` if (b)). This is a
      currently-ACTIVE gap (today's date is divergent too), not just a historical backfill task.
- [ ] [DATA] P2. Launch a VM to run `detect_manifest_divergence.py --asset-group cefi` (14M+ row
      manifest OOMs the shared host at a 4GB cap) and get the real per-cell CSV breakdown (not the
      stdout-tail sample) — determine which venue(s)/data_type(s) actually drive the 58,362
      DIVERGENT_EMPTY count before triaging real-gap vs code-bug vs oracle-bug. `market-tick-data-service`
      / `unified-trading-library` (the detector script's home).
- [ ] [DATA] P2. Same as above for tradfi (`--asset-group tradfi`, 8,468 DIVERGENT_EMPTY,
      14,464,340-row manifest already confirmed to OOM a 4GB local cap).
