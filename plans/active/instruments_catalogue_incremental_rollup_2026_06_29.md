---
doc_type: plan
title: Instrument catalogue — incremental (trailing-window + frozen-tail) rollup to replace the full-history re-aggregation
summary: 'The daily instrument-catalogue rollup re-reads and re-aggregates the ENTIRE multi-year by_date history every run (2,618 tradfi day-dirs, ~11.6k blobs → 2h17m), so it now exceeds the 3600s Cloud Run task timeout and the daily catalogue went stale. Implement the incremental design the service was always meant to have: load the previous catalog.parquet (which already encodes all-time available_from + frozen available_to) + re-read only the trailing liveness window (~21 days), recompute §7.3 liveness for window instruments, freeze the untouched tail, upsert and promote. Prototype-measured ~0.9 min vs 137 min (~125x fewer day-dirs) with the monotonic guard passing.'
status: active
nature: design
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [instruments, catalogue, rollup, incremental, performance, lifecycle, available-to, timeout, cloud-run]
related: [plans/active/instruments_foundation_completeness_2026_06_24.md, plans/active/path_to_100pct_backfill_mtds_is_2026_06_17.md, plans/active/mvp_catalogue_finalization_v10_2026_06_27.md, plans/archive/2026_06/proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md]
created: 2026-06-29
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 3
last_updated: 2026-06-29
locked_by: live-defi-rollout
locked_since: 2026-06-29
supersedes: []
superseded_by:
depends_on: [plans/active/issues/is_build_catalogue_defi_pool_dual_form_test_failures_2026_06_24.md]
source: ['Ops: #data-pipeline-alerts DP_CATALOG_NOT_RUNNING (tradfi catalogue 38h stale, 2026-06-29)', 'Ikenna design intent (Slack 2026-06-28): prev catalogue + latest day, never full re-aggregation']
assigned_role: data-pipeline-engineer
drift_direction: advance-code
---

# Instrument catalogue — incremental rollup

## Codex SSOTs (read these before touching this plan; update them in Phase 5)

- `codex/02-data/instruments-foundation-and-catalogue-completeness.md` — the lifecycle-rollup mechanism map (§4) + the
  G3 "scheduler actually runs it" gate. **Primary doc to update** (full-rebuild → incremental).
- `codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md` — the `INSTRUMENT_CACHE_REFRESH_TRIGGER` delta
  contract downstream of the catalogue write.
- `codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — IS owns reference data; the G3 gate description.
- `codex/02-data/data-catalogue-schema.md` — catalogue artifact pattern + deploy chain.
- `codex/05-infrastructure/manifest-consolidator-ssot.md` — the manifest consolidator already solved the *same*
  incremental-vs-full-scan problem (canonical + changed-shards anti-join); mirror its pattern + single-walk discipline.

## Problem (evidence)

The daily catalogue rollup [`instruments-service/scripts/build_instrument_catalogue.py`] `run_rollup` →
`build_catalogue_dataframe` (lines 564–747) **re-reads the entire by_date history every run**:

- `_iter_by_date_snapshots` (lines 1319–1366) lists + downloads **every** `instrument_availability/by_date/day=*/…
  /*.parquet` blob. For tradfi that is **2,618 day-directories / ~11.6k blobs**, growing by one day forever.
- It then aggregates with nested per-row Python loops (`for day, frame` → `for row in records`) — the slowest pandas
  pattern — building one `_InstrumentAggregate` per instrument across all of history.

Measured impact:

| Era | tradfi rollup duration |
|---|---|
| Baseline (pre-2026-06-27) | 31–45 min |
| After 2026-06-27 | 79 / 100 / 120 / **137** min |

The Cloud Run task timeout is **3600s = 60 min** (already bumped 1800→3600 on 2026-06-23, the Cloud-Run-Jobs ceiling).
The 2026-06-27 §7.3 liveness commits (`8261203` per-venue thin-day liveness, `50308e0` ghost-venue, `c9efb2a` tradfi
OPTION-root) added per-row work that tipped the already-O(all-history) job over 60 min → every daily run since
2026-06-27 23:04 was killed at the timeout → `catalog.parquet` went 38h stale → `DP_CATALOG_NOT_RUNNING`. A manual run
with a raised timeout completed in **2h17m** (it is not hung — just too slow for the budget), refreshing the artifact.

**Root cause is architectural, not the 2026-06-27 commits** (those are correct §7.3 fixes and must be kept): the rollup
was never built incrementally. The originating plan
(`proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md`) chose full-rebuild deliberately ("build it FROM by_date
and it is correct + self-refreshing") and only ever optimised the *download* (`_bounded_parallel_load`, 16 workers).
The intended incremental design (prev catalogue + latest day) was **never implemented**. Raising the timeout or
reverting 2026-06-27 only defers the next breach as history grows.

## The fix — trailing-window + frozen-tail incremental merge

The key correctness insight from the §7.3 liveness logic: deciding `available_to` (active vs delisted) needs a
**trailing window** of recent days, not just yesterday — `_venue_last_full_day` (lines 334–359) computes a per-venue
median over `_VENUE_RECENT_WINDOW = 14` days to skip thin/partial capture days. So the increment is **not** "yesterday
only"; it is "the previous catalogue + a trailing window ≥ the liveness window".

Algorithm (`run_rollup --mode incremental`, the new default for tradfi/cefi/defi):

1. **Load the previous `catalog.parquet`.** It already encodes, for every instrument that ever existed:
   `available_from` (immutable — the true first-ever day) and a frozen `available_to` for everything already
   delisted/expired.
2. **Read only the trailing window** (`WINDOW_DAYS`, default **21** = `_VENUE_RECENT_WINDOW`(14) + 7 margin) of by_date
   snapshots via the existing `_iter_by_date_snapshots` with a **date-floored prefix list** (list only
   `day=>=cutoff`). Build a *window* aggregate using the **unchanged** `build_catalogue_dataframe` logic — this reuses
   §7.3 liveness, dual-form keying, thin-day detection, metadata-from-most-recent verbatim, so no §7.3 regression.
3. **Merge (upsert):**
   - **Window instrument already in prev catalogue** → update `available_to` from the window recompute; **carry
     `available_from` from the prev catalogue** (the window's first day is NOT the true listing date); refresh metadata.
   - **Window-only instrument** (new listing) → append the window row as-is (its `available_from` = first window day is
     correct for a genuinely new instrument).
   - **Active-in-prev (`available_to is None`) but absent from the ENTIRE window** → newly delisted; close
     `available_to` to its prev last-seen day. (The window ≥ liveness window guarantees a true absence, not a thin-day
     blip.)
   - **All other prev rows (the frozen tail)** → copied through **unchanged**.
4. **MVP-tag** the merged frame (`_add_mvp_column`, unchanged) and **promote** via the unchanged `promote_catalogue` +
   `evaluate_monotonic_guard`. Merged row count ≥ prev count by construction → guard passes naturally.
5. **Fallbacks / safety nets:**
   - **Cold start** (no prev catalogue) → fall back to the existing full rebuild (`--mode full`).
   - **Periodic full rebuild** (weekly cron, `--mode full`) → self-heals any drift from retroactive by_date
     corrections older than the window; the daily job stays incremental.

### Prototype evidence (read-only, real prod data, 2026-06-29)

`scratchpad/incremental_prototype.py` against `instruments-store-tradfi-prd`:

| Metric | Full rebuild (today) | Incremental (prototype) |
|---|---|---|
| Day-dirs read | 2,618 | 21 (**0.8%** of corpus) |
| by_date blobs | ~11,600 | 301 |
| Read wall-clock | — | **45s** (+8s catalogue load) |
| Total wall-clock | **137 min** | **~0.9 min** |

Merge validated: 137,698 window instruments all present in the 1,090,672-row catalogue (update + keep
`available_from`); 952,974 frozen-tail rows untouched; **merged = 1,090,672 = prev → monotonic guard PASSES**; 0 spurious
new/delisted. → **~125× fewer day-dirs**, correctness-preserving.

## Invariants this plan MUST preserve (regression net)

1. **§7.3 venue-truth liveness** — `available_to` priority `delisted_at` > `expiry` > per-venue-last-full-day; thin-day
   skip (`_THIN_DAY_FRACTION=0.5`, `_VENUE_RECENT_WINDOW=14`). The window must be ≥ 14 days or live perps mass-false-
   delist. (Tests: `test_rollup_thin_latest_day_*`, `test_rollup_*_available_to_*`.)
2. **`available_from` is immutable** once set — always carried from the prev catalogue for known instruments.
3. **Monotonic shrink guard** (`evaluate_monotonic_guard`, lines 1208–1236) — merged frame must be ≥ prev row count;
   never pass `--allow-catalogue-shrink` on the incremental path. (Tests: `test_guard_*`.)
4. **DeFi dual-form pool keying** — merge by canonical `pool::<CHAIN>::<addr.lower()>` (`_aggregate_key` 429–460,
   `_defi_pool_dual_form` 508–561), NOT raw `instrument_key`; prev catalogue stores `instrument_id = addr.lower()`.
   (Tests: `test_rollup_defi_pool_*`, `test_rollup_*_ghost_*`.) **Depends on the 4 failing dual-form tests being green —
   see `depends_on`.**
5. **MVP v10 tagging** — `_add_mvp_column` on the merged frame, `MVP_SCOPE_CONFIG_VERSION = 10`.
6. **Schema unchanged** — `CATALOG_COLUMNS` (lines 140–186); no new column/version. Output stays one-row-per-instrument
   all-time cumulative (every downstream consumer assumes this).
7. **Single-walk discipline** — the incremental path must NOT introduce a second whole-corpus walk (review-blocking).

## Downstream blast radius — verify each still correct after the change (Phase 4)

Every consumer assumes the catalogue is the cumulative all-instruments-ever snapshot. The incremental output is
byte-equivalent in shape (full merged frame), so these should be unaffected — but each must be re-verified:

| Repo | Consumer | Risk if increment drops a historical row |
|---|---|---|
| instruments-service | `enumerate_expected_universe.py` | instrument vanishes from expected-universe denominator → hidden coverage gap |
| unified-trading-library | `instruments_catalog_reader.py` → `legacy_reason_classifier.py` | `EXPECTED_INSTRUMENT_NOT_LISTED/DELISTED` misclassification |
| market-tick-data-service | `tardis_symbol_resolution.py` | Tardis download universe under-populated |
| deployment-api | `manifest_source.read_unique_instrument_count` | data-status UI undercounts instruments |
| deployment-service | `data_pipeline_monitors` (DP_CATALOG) | staleness budget unchanged; verify cadence still daily |

## Phased work

### Phase 0 — preconditions
- [ ] [VERIFY] P0. Confirm the 4 DeFi dual-form tests in
  `is_build_catalogue_defi_pool_dual_form_test_failures_2026_06_24.md` are GREEN on LDR before touching the defi path.
  Gate: `cd instruments-service && bash scripts/quality-gates.sh --no-fix` green on `test_build_instrument_catalogue.py`.
- [ ] [INFRA] P1. (Interim band-aid, optional / operator-gated) bump `lifecycle_catalogue_scheduler.tf`
  `timeout_seconds` 3600→10800 for tradfi ONLY so the daily catalogue stays fresh until the incremental path ships.
  Gate: `terraform plan` shows only the timeout delta. (Operator declined the band-aid 2026-06-29 — keep unchecked
  unless the catalogue goes stale again before Phase 3 lands.)

### Phase 1 — incremental engine (tradfi/cefi/defi)
- [ ] [SCRIPT] P1. Add `--mode {incremental,full}` to `build_instrument_catalogue.py` (`run_rollup`), default
  `incremental`; `full` = today's behaviour (cold-start + periodic). Gate: unit test both modes select the right path.
- [ ] [SCRIPT] P1. Implement trailing-window read: `_iter_by_date_snapshots(..., since=cutoff)` listing only
  `day=>=cutoff` prefixes (no full-corpus walk — single-walk rule). `WINDOW_DAYS=21` constant + override. Gate: a test
  asserts only window days are listed.
- [ ] [SCRIPT] P1. Implement the merge (`_merge_incremental(prev_cat_df, window_df)`): update-known (carry
  `available_from`), append-new, close newly-delisted (active-in-prev ∧ absent-all-window), freeze the tail. Reuse
  `_aggregate_key`/`_defi_pool_dual_form` for pool identity. Gate: new unit tests for each of the 4 merge branches.
- [ ] [SCRIPT] P1. Cold-start + dry-run wiring: no prev catalogue → `--mode full`; keep `--max-blobs` diagnostic.
  Gate: `test_incremental_cold_start_falls_back_to_full`.

### Phase 2 — equivalence proof (the correctness gate)
- [ ] [VERIFY] P0. **Parity test**: on a fixture corpus, assert `incremental(prev, window)` == `full_rebuild(all)`
  row-for-row for tradfi/cefi/defi (instrument set, `available_from`, `available_to`, `mvp`, dual-form ids). This is the
  ship gate. Gate: `test_incremental_matches_full_rebuild_*` green for all 3 AGs.
- [ ] [VERIFY] P0. **Live shadow parity**: run `--mode incremental --dry-run` against prod tradfi + diff the produced
  frame vs the current `catalog.parquet` content (not just row count — per-instrument `available_to`). Gate: diff empty
  except expected window updates; cite the run. (Builds on `scratchpad/incremental_prototype.py`.)
- [ ] [VERIFY] P1. Newly-delisted edge case: synthetic fixture where an active perp stops appearing mid-window → assert
  `available_to` closes to the correct boundary (not a thin-day blip). Gate: dedicated test.

### Phase 3 — prediction variant + deploy
- [ ] [SCRIPT] P1. Apply the same trailing-window + frozen-tail merge to `build_prediction_catalogue_dataframe`
  (multi-grain cqg/conditionId; simpler `last_day>=latest_day` liveness, but `available_from`/settlement still need the
  prev catalogue). Gate: prediction parity test. **Sports needs NO change** — `build_sports_catalogue_from_manifest`
  already reads only the manifest `_index` (single read, no by_date walk).
- [ ] [INFRA] P1. Deploy: image rebuild + `terraform apply` of `lifecycle_catalogue_scheduler.tf` (no infra shape change
  if mode defaults to incremental; optionally lower tradfi memory 16Gi→4Gi since the window is small). Add the weekly
  `--mode full` self-heal job. Gate: `Evidence: cloudbuild=<id>` SUCCESS + a green incremental run on each AG.
- [ ] [VERIFY] P0. Operational proof: a real scheduled incremental run for tradfi/cefi/defi/prediction completes < 10
  min and writes a fresh `catalog.parquet`; `DP_CATALOG_NOT_RUNNING` clears. Gate: cite execution id + duration + new
  artifact mtime.

### Phase 4 — downstream verification
- [ ] [VERIFY] P1. Re-verify each consumer in the blast-radius table reads the incremental catalogue identically (run
  `enumerate_expected_universe`, the legacy reason classifier, tardis resolution, the data-status unique-count) against
  the incremental output vs the last full-rebuild output. Gate: outputs identical.
- [ ] [VERIFY] P2. Annotate (do not duplicate) the overlapping open todos: the catalogue-monotonicity-check
  `[VERIFY] P1` in `path_to_100pct_backfill_mtds_is_2026_06_17.md:217` (this plan answers it); and the
  catalogue-regen-fast-fail / terraform-apply `[INFRA] P1` items in `instruments_foundation_completeness_2026_06_24.md`
  (superseded for tradfi by the incremental job). Gate: a one-line cross-ref added to each.

### Phase 5 — codex + observability
- [ ] [DOCS] P1. Update the 5 codex SSOTs listed above (full-rebuild → incremental; window+frozen-tail; the periodic
  full self-heal; the manifest-consolidator parallel). Gate: each doc reflects the new mechanism; no plan↔codex drift.
- [ ] [SCRIPT] P2. Ship the never-built coverage-horizon warning (NICE-TO-HAVE from the originating plan): emit a
  `CATALOGUE_STALE_BY_DATE` warn when the latest by_date day is > N days old OR per-day instrument count drops sharply —
  trivial now that the incremental run knows the window's latest day. Gate: unit test + a fired event.

## Risks & rollback
- **Risk: a retroactive correction to a by_date file OLDER than the window is missed.** Mitigated by the weekly
  `--mode full` self-heal (Phase 3) + parity test (Phase 2). Document the window/self-heal contract in codex.
- **Risk: §7.3 liveness regression if window < 14 days.** Guarded by the constant `WINDOW_DAYS=21` ≥ 14 + the
  thin-day/newly-delisted tests.
- **Rollback: `--mode full` reproduces today's exact behaviour** — flip the job arg back; no data migration, schema
  unchanged, prev `catalog.parquet` untouched on any failed/dry run (temp-staging promote).

## Progress log
- 2026-06-29: Plan created. Root cause confirmed (full-history re-aggregation, 2,618 tradfi day-dirs/run; 2026-06-27
  §7.3 commits the trigger, not the cause). Read-only prototype `scratchpad/incremental_prototype.py` measured ~0.9 min
  vs 137 min (~125× fewer day-dirs), merge monotonic-guard-clean. Three-agent audit captured schema, downstream blast
  radius, code map, job config, and existing-plan overlaps (folded into Phases 0/4). Routed as a human plan
  (`assigned_vm: NA`) per operator (Harsh, 2026-06-29) — ready for Ikenna on return.
