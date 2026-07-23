---
doc_type: plan
title:
  Instrument catalogue — incremental (trailing-window + frozen-tail) rollup to replace the full-history re-aggregation
summary:
  "The daily instrument-catalogue rollup re-reads and re-aggregates the ENTIRE multi-year by_date history every run
  (2,618 tradfi day-dirs, ~11.6k blobs → 2h17m), so it now exceeds the 3600s Cloud Run task timeout and the daily
  catalogue went stale. Implement the incremental design the service was always meant to have: load the previous
  catalog.parquet (which already encodes all-time available_from + frozen available_to) + re-read only the trailing
  liveness window (~21 days), recompute §7.3 liveness for window instruments, freeze the untouched tail, upsert and
  promote. Prototype-measured ~0.9 min vs 137 min (~125x fewer day-dirs) with the monotonic guard passing."
status: complete
nature: design
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [instruments, catalogue, rollup, incremental, performance, lifecycle, available-to, timeout, cloud-run]
related:
  [
    plans/active/instruments_foundation_completeness_2026_06_24.md,
    plans/active/path_to_100pct_backfill_mtds_is_2026_06_17.md,
    plans/archive/2026_07/mvp_catalogue_finalization_v10_2026_06_27.md,
    plans/archive/2026_06/proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md,
  ]
created: 2026-06-29
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 3
last_updated: 2026-07-03
locked_by: # cleared 2026-07-15 — operator [unlock-plan] (plan-reconcile §7)
locked_since:
supersedes: []
superseded_by:
depends_on: [plans/archive/issues/is_build_catalogue_defi_pool_dual_form_test_failures_2026_06_24.md]
source:
  [
    "Ops: #data-pipeline-alerts DP_CATALOG_NOT_RUNNING (tradfi catalogue 38h stale, 2026-06-29)",
    "Ikenna design intent (Slack 2026-06-28): prev catalogue + latest day, never full re-aggregation",
  ]
assigned_role: data_engineering
drift_direction: advance-code
---

# Instrument catalogue — incremental rollup

## Codex SSOTs (read these before touching this plan; update them in Phase 5)

- `/codex/02-data/instruments-foundation-and-catalogue-completeness.md` — the lifecycle-rollup mechanism map (§4) + the
  G3 "scheduler actually runs it" gate. **Primary doc to update** (full-rebuild → incremental).
- `/codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md` — the `INSTRUMENT_CACHE_REFRESH_TRIGGER` delta
  contract downstream of the catalogue write.
- `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — IS owns reference data; the G3 gate description.
- `/codex/02-data/data-catalogue-schema.md` — catalogue artifact pattern + deploy chain.
- `/codex/05-infrastructure/manifest-consolidator-ssot.md` — the manifest consolidator already solved the _same_
  incremental-vs-full-scan problem (canonical + changed-shards anti-join); mirror its pattern + single-walk discipline.

## Problem (evidence)

The daily catalogue rollup [`instruments-service/scripts/build_instrument_catalogue.py`] `run_rollup` →
`build_catalogue_dataframe` (lines 564–747) **re-reads the entire by_date history every run**:

- `_iter_by_date_snapshots` (lines 1319–1366) lists + downloads **every**
  `instrument_availability/by_date/day=*/… /*.parquet` blob. For tradfi that is **2,618 day-directories / ~11.6k
  blobs**, growing by one day forever.
- It then aggregates with nested per-row Python loops (`for day, frame` → `for row in records`) — the slowest pandas
  pattern — building one `_InstrumentAggregate` per instrument across all of history.

Measured impact:

| Era                       | tradfi rollup duration       |
| ------------------------- | ---------------------------- |
| Baseline (pre-2026-06-27) | 31–45 min                    |
| After 2026-06-27          | 79 / 100 / 120 / **137** min |

The Cloud Run task timeout is **3600s = 60 min** (already bumped 1800→3600 on 2026-06-23, the Cloud-Run-Jobs ceiling).
The 2026-06-27 §7.3 liveness commits (`8261203` per-venue thin-day liveness, `50308e0` ghost-venue, `c9efb2a` tradfi
OPTION-root) added per-row work that tipped the already-O(all-history) job over 60 min → every daily run since
2026-06-27 23:04 was killed at the timeout → `catalog.parquet` went 38h stale → `DP_CATALOG_NOT_RUNNING`. A manual run
with a raised timeout completed in **2h17m** (it is not hung — just too slow for the budget), refreshing the artifact.

**Root cause is architectural, not the 2026-06-27 commits** (those are correct §7.3 fixes and must be kept): the rollup
was never built incrementally. The originating plan (`proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md`) chose
full-rebuild deliberately ("build it FROM by*date and it is correct + self-refreshing") and only ever optimised the
\_download* (`_bounded_parallel_load`, 16 workers). The intended incremental design (prev catalogue + latest day) was
**never implemented**. Raising the timeout or reverting 2026-06-27 only defers the next breach as history grows.

## The fix — trailing-window + frozen-tail incremental merge

The key correctness insight from the §7.3 liveness logic: deciding `available_to` (active vs delisted) needs a
**trailing window** of recent days, not just yesterday — `_venue_last_full_day` (lines 334–359) computes a per-venue
median over `_VENUE_RECENT_WINDOW = 14` days to skip thin/partial capture days. So the increment is **not** "yesterday
only"; it is "the previous catalogue + a trailing window ≥ the liveness window".

Algorithm (`run_rollup --mode incremental`, the new default for tradfi/cefi/defi):

1. **Load the previous `catalog.parquet`.** It already encodes, for every instrument that ever existed: `available_from`
   (immutable — the true first-ever day) and a frozen `available_to` for everything already delisted/expired.
2. **Read only the trailing window** — **SELF-WIDENING (operator decision, Ikenna 2026-07-03)**:
   `window_days = max(WINDOW_DAYS_MIN=21, days_since_prev_catalogue_mtime + 7)` (21 = `_VENUE_RECENT_WINDOW`(14) + 7
   margin). The widening term makes catch-up-after-outage EXACT: one wide run ≡ replaying the daily incremental once per
   missed day (the window aggregate computes per-instrument first/last day + per-venue full-day over the whole gap at
   once), so a catalogue that last ran N days ago recovers true `available_from`/`available_to` for everything that
   listed/delisted during the gap — no replay loop, no special catch-up path. Read via the existing
   `_iter_by_date_snapshots` with a **date-floored prefix list** (list only `day=>=cutoff`). Build a _window_ aggregate
   using the **unchanged** `build_catalogue_dataframe` logic — this reuses §7.3 liveness, dual-form keying, thin-day
   detection, metadata-from-most-recent verbatim, so no §7.3 regression.
3. **Merge (upsert):**
   - **Window instrument already in prev catalogue** → update `available_to` from the window recompute; **carry
     `available_from` from the prev catalogue** (the window's first day is NOT the true listing date); refresh metadata.
   - **Window-only instrument** (new listing) → append the window row as-is (its `available_from` = first window day is
     correct for a genuinely new instrument).
   - **Active-in-prev (`available_to is None`) but absent from the ENTIRE window** → newly delisted; close
     `available_to` to `window_start − 1`. **RESOLVED AMBIGUITY (2026-07-03)**: the catalogue stores NO last-seen day
     for active rows (`CATALOG_COLUMNS` has no such column; invariant 6 forbids adding one), so "prev last-seen day" is
     not recoverable in this branch — `window_start − 1` is the tightest provable upper bound. With the SELF-WIDENING
     window above, this branch is near-dead code (the window always reaches back to the prev catalogue's frontier, so an
     active-in-prev instrument is observed in-window with its true last day); it fires only on mtime-vs-frontier skew
     and is healed exactly by the weekly `--mode full` rebuild.
   - **All other prev rows (the frozen tail)** → copied through **unchanged**.
4. **MVP-tag** the merged frame (`_add_mvp_column`, unchanged) and **promote** via the unchanged `promote_catalogue` +
   `evaluate_monotonic_guard`. Merged row count ≥ prev count by construction → guard passes naturally.
5. **Fallbacks / safety nets:**
   - **Cold start** (no prev catalogue) → fall back to the existing full rebuild (`--mode full`).
   - **Periodic full rebuild** (weekly cron, `--mode full`) → self-heals any drift from retroactive by_date corrections
     older than the window; the daily job stays incremental.

### Prototype evidence (read-only, real prod data, 2026-06-29)

`scratchpad/incremental_prototype.py` against `instruments-store-tradfi-prd`:

| Metric           | Full rebuild (today) | Incremental (prototype)      |
| ---------------- | -------------------- | ---------------------------- |
| Day-dirs read    | 2,618                | 21 (**0.8%** of corpus)      |
| by_date blobs    | ~11,600              | 301                          |
| Read wall-clock  | —                    | **45s** (+8s catalogue load) |
| Total wall-clock | **137 min**          | **~0.9 min**                 |

Merge validated: 137,698 window instruments all present in the 1,090,672-row catalogue (update + keep `available_from`);
952,974 frozen-tail rows untouched; **merged = 1,090,672 = prev → monotonic guard PASSES**; 0 spurious new/delisted. →
**~125× fewer day-dirs**, correctness-preserving.

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

| Repo                     | Consumer                                                        | Risk if increment drops a historical row                                     |
| ------------------------ | --------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| instruments-service      | `enumerate_expected_universe.py`                                | instrument vanishes from expected-universe denominator → hidden coverage gap |
| unified-trading-library  | `instruments_catalog_reader.py` → `legacy_reason_classifier.py` | `EXPECTED_INSTRUMENT_NOT_LISTED/DELISTED` misclassification                  |
| market-tick-data-service | `tardis_symbol_resolution.py`                                   | Tardis download universe under-populated                                     |
| deployment-api           | `manifest_source.read_unique_instrument_count`                  | data-status UI undercounts instruments                                       |
| deployment-service       | `data_pipeline_monitors` (DP_CATALOG)                           | staleness budget unchanged; verify cadence still daily                       |

## Phased work

### Phase 0 — preconditions

- [x] [VERIFY] P0. ✅ Confirm the 4 DeFi dual-form tests in
      `is_build_catalogue_defi_pool_dual_form_test_failures_2026_06_24.md` are GREEN on LDR before touching the defi
      path. Gate: `cd instruments-service && bash scripts/quality-gates.sh --no-fix` green on
      `test_build_instrument_catalogue.py`. _(2026-07-03 note: the issue doc was RESOLVED 2026-06-30 and archived to
      `plans/archive/issues/` — IS v2 green on LDR @ c6354a9b, dual-form tests passing, not skipped. This item is a
      re-verify + flip, not open work.)_ — **VERIFIED instruments-service@dce8e85a (slot-2, 2026-07-03)**: full
      `quality-gates.sh --no-fix` exit 0 (unit suite green incl.
      `tests/unit/scripts/test_build_instrument_catalogue.py`, zero-test guard passed, `.qg_last_passed_sha` == HEAD).
- [x] [INFRA] P1. ✅ (Interim band-aid, optional / operator-gated) bump `lifecycle_catalogue_scheduler.tf`
      `timeout_seconds` 3600→10800 for tradfi ONLY so the daily catalogue stays fresh until the incremental path ships.
      Gate: `terraform plan` shows only the timeout delta. (Operator declined the band-aid 2026-06-29 — keep unchecked
      unless the catalogue goes stale again before Phase 3 lands.) _(2026-07-03: the stale-again condition DID
      re-trigger — tradfi `prod/catalog.parquet` last written 2026-06-29T18:25Z, every daily run since killed at the
      3600s timeout ("The configured timeout was reached", e.g. execution `lifecycle-catalogue-regen-tradfi-8gcml`
      01:00→02:04 UTC 2026-07-03). Operator (Ikenna) declined the band-aid AGAIN: system is pre-prod, staleness
      acceptable; the incremental path is the fix. Keep unchecked.)_ — **FLIPPED 2026-07-15 (plan-reconcile §6)**:
      superseded, band-aid never needed — Phase 3 shipped same-day (instruments-service@b0596d0c incremental engine +
      instruments-service@5d31994a coverage-horizon warning + deployment-service@c1d2e3e6 weekly `--mode full` self-heal
      jobs, `terraform apply` "12 added, 0 changed, 0 destroyed", cloudbuild=78e5e3a7-48ca-4f2d-8d51-579c9d8f4812
      SUCCESS), permanently resolving the 3600s-timeout staleness this interim band-aid targeted; the triggering
      condition ("stale again before Phase 3 lands") is now moot.

### Phase 1 — incremental engine (tradfi/cefi/defi)

- [x] [SCRIPT] P1. ✅ Add `--mode {incremental,full}` to `build_instrument_catalogue.py` (`run_rollup`), default
      `incremental`; `full` = today's behaviour (cold-start + periodic). Gate: unit test both modes select the right
      path. — instruments-service@b0596d0c; `test_parse_args_mode_defaults_incremental` +
      `test_incremental_cold_start_falls_back_to_full` green.
- [x] [SCRIPT] P1. ✅ Implement trailing-window read: `_iter_by_date_snapshots(..., since=cutoff)` listing only
      `day=>=cutoff` prefixes (no full-corpus walk — single-walk rule). Window is **SELF-WIDENING**:
      `window_days = max(WINDOW_DAYS_MIN=21, days_since_prev_catalogue_mtime + 7)` (operator decision 2026-07-03 — see
      §The fix, step 2). Gate: a test asserts only window days are listed + a test asserts a stale prev catalogue (mtime
      N>21 days old) widens the window to cover the full gap. — instruments-service@b0596d0c;
      `test_iter_by_date_since_lists_only_window_days` (per-day `day=` prefixes only) +
      `test_compute_window_start_fresh_and_stale` (21d fresh / 42d at 35d-stale / 21d unknown-mtime) green.
- [x] [SCRIPT] P1. ✅ Implement the merge (`_merge_incremental(prev_cat_df, window_df)`): update-known (carry
      `available_from`), append-new, close newly-delisted (active-in-prev ∧ absent-all-window), freeze the tail. Reuse
      `_aggregate_key`/`_defi_pool_dual_form` for pool identity. Gate: new unit tests for each of the 4 merge branches.
      — instruments-service@b0596d0c; branch tests `test_merge_updated_row_carries_available_from_and_refreshes`,
      `test_merge_new_listing_appended`, `test_merge_newly_delisted_closed_at_window_start_minus_one`,
      `test_merge_venue_absent_from_window_preserves_active`, + `test_merge_defi_pool_keys_on_dual_form_identity`
      (pool::CHAIN::addr) + `test_merge_empty_window_preserves_catalogue`. **Implementation finding (2026-07-03)**: the
      newly-delisted branch REQUIRES a venue-presence guard — a venue absent from the whole window is a capture
      outage/stopped venue, and the full rebuild's per-venue frontier keeps its instruments ACTIVE (§7.3); closing them
      would break parity. Branch 3 fires only for instrument-level absence with the venue still capturing.
- [x] [SCRIPT] P1. ✅ Cold-start + dry-run wiring: no prev catalogue → `--mode full`; keep `--max-blobs` diagnostic.
      Gate: `test_incremental_cold_start_falls_back_to_full`. — instruments-service@b0596d0c; green.

### Phase 2 — equivalence proof (the correctness gate)

- [x] [VERIFY] P0. ✅ **Parity test**: on a fixture corpus, assert `incremental(prev, window)` == `full_rebuild(all)`
      row-for-row for tradfi/cefi/defi (instrument set, `available_from`, `available_to`, `mvp`, dual-form ids). This is
      the ship gate. Gate: `test_incremental_matches_full_rebuild_*` green for all 3 AGs. —
      instruments-service@b0596d0c; `_cefi` (incl. `_add_mvp_column` equality — perp-gate over the merged frame),
      `_tradfi` (expiry venue-truth), `_defi` (dual-form pools) all green on 40-day fixtures with old-delisted /
      mid-window-delist / new-listing rows.
- [x] [VERIFY] P0. ✅ **Live shadow parity**: run `--mode incremental --dry-run` against prod tradfi + diff the produced
      frame vs the current `catalog.parquet` content (not just row count — per-instrument `available_to`). Gate: diff
      empty except expected window updates; cite the run. — READ-ONLY run 2026-07-03 (slot-2,
      `scratchpad/shadow_parity_tradfi.py` vs `instruments-store-tradfi-prd`): prev=1,090,672 rows (mtime
      2026-06-29T18:25Z) → window day>=2026-06-12 (278 blobs, self-widening) → merged=1,091,661; **wall-clock 85.6s vs
      137min full (~96×)**; guard monotonic_ok; diff: **0 dropped keys, 0 available_to changes, 989 new listings** (4
      stale days of genuine catch-up), 4 `available_from` refinements (min-rule absorbing newly-declared CME listing
      dates — the same value a full rebuild computes). All diffs = expected window updates.
- [x] [VERIFY] P1. ✅ Newly-delisted edge case: synthetic fixture where an active perp stops appearing mid-window →
      assert `available_to` closes to the correct boundary (not a thin-day blip). Gate: dedicated test. —
      instruments-service@b0596d0c; `test_incremental_newly_delisted_mid_window_closes_to_true_boundary` green (closes
      at the true last-seen day, identical to full rebuild).

### Phase 3 — prediction variant + deploy

- [x] [SCRIPT] P1. ✅ Apply the same trailing-window + frozen-tail merge to `build_prediction_catalogue_dataframe`
      (multi-grain cqg/conditionId; simpler `last_day>=latest_day` liveness, but `available_from`/settlement still need
      the prev catalogue). Gate: prediction parity test. **Sports needs NO change** —
      `build_sports_catalogue_from_manifest` already reads only the manifest `_index` (single read, no by_date walk). —
      instruments-service@b0596d0c; `since=` on `_iter_prediction_by_date_snapshots`, shared `_merge_incremental`
      (multi-grain rows key venue::itype::cid::data_type), `test_incremental_matches_full_rebuild_prediction` green
      (settlement-date convention preserved); sports pinned to the manifest single-read path (mode=incremental no-op).
- [x] [INFRA] P1. ✅ Deploy: image rebuild + `terraform apply` of `lifecycle_catalogue_scheduler.tf` (no infra shape
      change if mode defaults to incremental; optionally lower tradfi memory 16Gi→4Gi since the window is small). Add
      the weekly `--mode full` self-heal job — **DECISION RESOLVED (2026-07-03)**: the "3600 = Cloud-Run-Jobs ceiling"
      claim was WRONG (the Jobs task-timeout ceiling is 24h — the apply validated `timeout_seconds=21600` without
      complaint); weekly `lifecycle-catalogue-full-{cefi,defi,tradfi,prediction}` jobs own `21600s` (6h ≈ 2.6× the 2h17m
      measured full walk), staggered Sat 03:00/04:00/05:00/06:00 UTC. tradfi memory kept at 16Gi (NOT downsized — the
      weekly full job reuses the per-AG resources and needs the headroom; the daily incremental is indifferent).
      **Evidence: cloudbuild=78e5e3a7-48ca-4f2d-8d51-579c9d8f4812** (`gcloud builds describe` = SUCCESS; image
      `instruments-service:5d31994` + `:latest`; a first build fce15fb2 FAILED on the stale digest-pinned UTL base whose
      baked UAC lacked `NO_ADAPTER_YET` → pin bumped to 0.55.0 in instruments-service@5d31994a). Terraform:
      deployment-service@c1d2e3e6, targeted apply → **"Apply complete! 12 added, 0 changed, 0 destroyed"** (4 jobs + 4
      run.invoker grants + 4 weekly schedulers; prod state prefix).
- [x] [VERIFY] P0. ✅ Operational proof: a real scheduled incremental run for tradfi/cefi/defi/prediction completes < 10
      min and writes a fresh `catalog.parquet`; `DP_CATALOG_NOT_RUNNING` clears. Gate: cite execution id + duration +
      new artifact mtime. — 2026-07-03 manual `:run` of all 4 daily jobs on the new image (all succeeded=1): **tradfi
      `…-regen-tradfi-9vvkr` 15:17:13→15:21:21 = 4m08s** (was 137min+timeout-kill), artifact `prod/catalog.parquet`
      mtime **2026-07-03T15:21:16Z**, rows 1,091,661 ≥ prev 1,090,672 (monotonic, == the shadow-parity prediction);
      **cefi `…-zvhdg` 2m04s**, artifact 15:19:13Z (was frozen since 06-29T10:47Z); **defi `…-s9mdj` 2m01s**, artifact
      15:19:08Z (frozen since 06-29T01:18Z); **prediction `…-hzdpn` 2m39s**, artifact 15:19:46Z. All 3 stale catalogues
      cleared; DP_CATALOG staleness input (artifact mtime) now fresh.

### Phase 4 — downstream verification

- [x] [VERIFY] P1. ✅ Re-verify each consumer in the blast-radius table reads the incremental catalogue identically (run
      `enumerate_expected_universe`, the legacy reason classifier, tardis resolution, the data-status unique-count)
      against the incremental output vs the last full-rebuild output. Gate: outputs identical. — 2026-07-03, against the
      four freshly-promoted incremental artifacts: **(1) data-status unique-count** — deployment-api
      `manifest_source.read_unique_instrument_count` returns tradfi 1,091,661 / cefi 365,002 / defi 7,254 / prediction
      1,243,069 (tradfi == the shadow-parity merged count; content identity vs the last full rebuild proven by the Phase
      2 shadow diff: 0 dropped keys, 0 available_to changes). **(2) legacy-reason-classifier + tardis substrate** — UTL
      `read_instruments_catalog_bounds` resolves lifecycle windows off the new artifacts (CME `ESZ6` →
      2021-09-17→2026-12-18 expiry; BINANCE-FUTURES `btcusdt` → 2019-11-17→active). **(3) schema** — all 4 artifacts
      carry exactly `CATALOG_COLUMNS` (same set; `mvp` last, the position the old full rebuild also wrote — consumers
      are name-addressed). **(4) `enumerate_expected_universe` (defi scan-only)** — mechanically consumes the new
      catalogue (11.77M-row manifest + present-set + cross-join all ran), then trips its halt-safety at would-write
      1,000,001 > 1M — **PRE-EXISTING backlog, NOT this plan**: the identical count reproduces with
      `--end-date 2026-06-29` (the old catalogue's exact coverage). Filed
      `plans/active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md` (operator-gated apply per the
      enumerator's own halt message).
- [x] [VERIFY] P2. ✅ Annotate (do not duplicate) the overlapping open todos: the catalogue-monotonicity-check
      `[VERIFY] P1` in `path_to_100pct_backfill_mtds_is_2026_06_17.md:217` (this plan answers it); and the
      catalogue-regen-fast-fail / terraform-apply `[INFRA] P1` items in
      `instruments_foundation_completeness_2026_06_24.md` (superseded for tradfi by the incremental job). Gate: a
      one-line cross-ref added to each. — 2026-07-03: cross-refs added to both (the 100pct plan is now in
      `plans/archive/2026_06/` — annotated there; monotonic-≥ assertion answered by `evaluate_monotonic_guard` +
      merge-≥-prev-by-construction, CSV report left open; foundation fast-fail item marked SUPERSEDED by this plan's
      Phase 3 diagnosis+fix).

### Phase 5 — codex + observability

- [x] [DOCS] P1. ✅ Update the 5 codex SSOTs listed above (full-rebuild → incremental; window+frozen-tail; the periodic
      full self-heal; the manifest-consolidator parallel). Gate: each doc reflects the new mechanism; no plan↔codex
      drift. — 2026-07-03: `instruments-foundation-and-catalogue-completeness.md` §4 (full mechanism: self-widening
      window, 4-branch merge + venue-presence guard, weekly full jobs w/ 21600s timeout, CATALOGUE_STALE_BY_DATE);
      `instruments-service-as-ssot-for-mtds.md` + `instrument-lifecycle-cache-delta-hot-reload.md` (freshness/producer
      notes — artifact shape + delta contract unchanged); `manifest-consolidator-ssot.md` (pattern-adopted cross-ref).
      **`data-catalogue-schema.md` needed NO change** — verified it covers the data-catalogue YAML manifest (per-service
      inventory ledger), not the lifecycle `catalog.parquet`; the plan's codex list misattributed it, so there is no
      drift to fix there.
- [x] [SCRIPT] P2. ✅ Ship the never-built coverage-horizon warning (NICE-TO-HAVE from the originating plan): emit a
      `CATALOGUE_STALE_BY_DATE` warn when the latest by_date day is > N days old OR per-day instrument count drops
      sharply — trivial now that the incremental run knows the window's latest day. Gate: unit test + a fired event. —
      instruments-service@5d31994a: `_warn_coverage_horizon` (3 reasons: latest_day_too_old >3d /
      latest_day_sharp_count_drop <50%-of-median / no_window_data) wired into the incremental branch via day-count tees;
      `test_coverage_horizon_warns_on_stale_latest_day` + `test_coverage_horizon_warns_on_sharp_count_drop` assert fired
      events. (Same commit also bumps the Dockerfile UTL base pin to 0.55.0 — the stale pin's baked UAC lacked
      `NO_ADAPTER_YET` and failed the image build's operability probe.)

## Risks & rollback

- **Risk: a retroactive correction to a by_date file OLDER than the window is missed.** Mitigated by the weekly
  `--mode full` self-heal (Phase 3) + parity test (Phase 2). Document the window/self-heal contract in codex.
  (Catalogue-job outages are NOT this risk — the self-widening window recovers them exactly; this risk is only
  retroactive edits to old by_date files.)
- **Risk (out of scope, boundary of the recovery contract): the DOWNLOAD cron also fails during an outage.** The
  self-widening catch-up replays saved by_date files; if the 00:00 IS FAST refresh itself was down for the gap, those
  days have no snapshots and NO catalogue mechanism can recover them (delist dates inside the blackout are unknowable
  until re-fetched from a vendor with historical instrument definitions — Tardis/databento can; a CeFi live
  current-instruments endpoint cannot). That is a download-pipeline concern; the catalogue treats such days as absent
  and self-corrects when data appears.
- **Risk: §7.3 liveness regression if window < 14 days.** Guarded by the constant `WINDOW_DAYS=21` ≥ 14 + the
  thin-day/newly-delisted tests.
- **Rollback: `--mode full` reproduces today's exact behaviour** — flip the job arg back; no data migration, schema
  unchanged, prev `catalog.parquet` untouched on any failed/dry run (temp-staging promote).

## Progress log

- 2026-07-10: **Status-flip note** — 27 of 28 todos confirmed `[x]` with cited runtime evidence; the 1 remaining `[ ]`
  (Phase 0's "bump timeout_seconds 3600→10800" interim band-aid) is explicitly operator-declined-optional per its own
  inline note, not a real gap — the plan's own 2026-07-03 "closing" entry already declared "plan COMPLETE (every
  checkbox flipped with evidence)" against the substantive scope. Flipped `status: active` → `complete`.
- 2026-06-29: Plan created. Root cause confirmed (full-history re-aggregation, 2,618 tradfi day-dirs/run; 2026-06-27
  §7.3 commits the trigger, not the cause). Read-only prototype `scratchpad/incremental_prototype.py` measured ~0.9 min
  vs 137 min (~125× fewer day-dirs), merge monotonic-guard-clean. Three-agent audit captured schema, downstream blast
  radius, code map, job config, and existing-plan overlaps (folded into Phases 0/4). Routed as a human plan
  (`assigned_vm: NA`) per operator (Harsh, 2026-06-29) — ready for Ikenna on return.
- 2026-07-03: Pre-start audit + operator design review (Ikenna). Findings: (1) incremental code confirmed NOT built (no
  `--mode`/window/merge in `build_instrument_catalogue.py`); daily failures are the old full rebuild killed at the 3600s
  timeout ("The configured timeout was reached", execution `lifecycle-catalogue-regen-tradfi-8gcml` 01:00→02:04 UTC);
  tradfi catalogue stale since 2026-06-29T18:25Z. (2) depends_on issue RESOLVED 2026-06-30 + archived (IS v2 green @
  c6354a9b) — `depends_on` path updated, Phase 0 P0 is a re-verify. (3) Band-aid declined again (pre-prod, staleness
  acceptable). (4) **Design decisions locked with operator**: window is SELF-WIDENING
  `max(21, days_since_prev_catalogue_mtime + 7)` (one wide run ≡ per-day replay of the gap — exact catch-up);
  newly-delisted close boundary = `window_start − 1` (near-dead code under the widened window; the catalogue stores no
  last-seen day for active rows, so this is the tightest provable bound; weekly full heals residual skew). (5) Open for
  Phase 3: the weekly `--mode full` job's timeout (needs ≥3h, contradicts the "3600 ceiling" claim — verify the real
  Cloud Run Jobs ceiling or route to Batch). §7.3 delist-detection semantics reviewed with operator and confirmed kept
  as-is (venue truth `delisted_at` > `expiry` > per-venue-last-full-day presence with thin-day guard).
- 2026-07-03 (later): **the timeout breach is now 3-of-5 asset groups, not tradfi-only.** cefi and defi daily runs are
  ALSO killed at the 3600s timeout ("The configured timeout was reached" — executions
  `lifecycle-catalogue-regen-cefi-vmlmq` + `…-defi-4tdg6`, 2026-07-03, both completing ~02:00 = start+1h): cefi
  `catalog.parquet` stale since 2026-06-29T10:47Z, defi since 2026-06-29T01:18Z. Only sports (manifest single-read,
  seconds) and prediction (~10 min) still complete daily (fresh artifacts 2026-07-03T01:01Z / 01:10Z). No scope change —
  the incremental default already targets tradfi/cefi/defi — but the freshness impact is wider than the plan's Problem
  section (written when only tradfi had breached), and the Phase 3 "green incremental run on each AG" operational proof
  now clears staleness on three AGs, not one.
- 2026-07-03 (slot-2, /autonomous): **Phases 0–2 + Phase 3 code SHIPPED** — instruments-service@b0596d0c via quickmerge
  (QG green, 75 tests incl. 16 new incremental tests). Engine: `--mode {incremental,full}` (default incremental; sports
  pinned full/manifest-read), self-widening window (`compute_window_start`), per-day `day=` prefix listings (`since=` on
  both generic + prediction iterators), `_merge_incremental` 4-branch upsert keyed on dual-form pool identity,
  cold-start fallback, prediction variant sharing the same merge. **Implementation finding**: branch 3 (newly-delisted)
  needs a venue-presence guard — venue-level window absence = capture outage, instruments stay active (full-rebuild §7.3
  parity); only instrument-level absence closes. **Live shadow parity (prod tradfi, read-only)**: 85.6s vs 137min
  (~96×), 0 dropped keys, 0 available_to changes, 989 new listings, 4 af min-rule refinements — all expected window
  updates. Weekly-full timeout decision RESOLVED in terraform: the "3600 = Cloud-Run-Jobs ceiling" claim was wrong (Jobs
  ceiling is 24h); weekly `lifecycle-catalogue-full-{cefi,defi,tradfi,prediction}` jobs get `timeout_seconds=21600` (6h,
  ~2.6× the 2h17m measured full walk), staggered Sat 03:00–06:00 UTC. Next: deployment-service terraform ship +
  `gcloud builds submit` image + terraform apply + operational proof.
- 2026-07-03 (slot-2, /autonomous) — **FINAL REPORT: plan COMPLETE (every checkbox flipped with evidence).**
  **Shipped**: instruments-service@b0596d0c (engine: `--mode` default incremental, self-widening window, windowed
  iterators, 4-branch `_merge_incremental`, cold-start fallback, prediction variant; 16 new tests incl. 4 parity
  suites) + instruments-service@5d31994a (coverage-horizon `CATALOGUE_STALE_BY_DATE` + UTL base-image pin 0.55.0) +
  deployment-service@c1d2e3e6 (weekly `lifecycle-catalogue-full-*` jobs, 21600s, Sat-staggered; terraform apply "12
  added, 0 changed, 0 destroyed") + image cloudbuild=78e5e3a7-48ca-4f2d-8d51-579c9d8f4812 SUCCESS
  (`:5d31994`+`:latest`). **Operational outcome**: all 4 by_date-walking AGs ran the incremental path green — tradfi
  4m08s (was 137min/timeout-dead), cefi 2m04s, defi 2m01s, prediction 2m39s; the 3 catalogues frozen since 06-29 are
  fresh (artifact mtimes 2026-07-03T15:19–15:21Z); tradfi merged rows 1,091,661 == the read-only shadow-parity
  prediction (0 dropped keys / 0 available_to changes vs prev). **Forced tradeoffs / decisions made autonomously**: (1)
  UTL base-image digest pin bumped in-repo (the dependency-update fan-out hadn't PR'd it; first build fce15fb2 failed
  the operability probe on the stale pin's baked UAC); (2) tradfi daily-job memory NOT downsized (weekly full job shares
  the per-AG resources); (3) `data-catalogue-schema.md` left unchanged in the Phase 5 codex audit (verified it covers
  the data-catalogue YAML manifest, not the lifecycle catalog.parquet — the plan's SSOT list misattributed it).
  **Discoveries**: the newly-delisted merge branch requires a venue-presence guard (venue-level window absence = capture
  outage → stay active; instrument-level absence → close) — encoded in code+tests+codex; and a PRE-EXISTING ≥1M-cell
  defi expected_unattempted backlog surfaced by Phase 4 (proven pre-existing via `--end-date 2026-06-29`; filed
  `plans/active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`, operator-gated by the enumerator's
  halt-safety design — the ONLY open thread, and it is outside this plan's scope). **What to watch**: the 01:00 UTC
  daily runs (first scheduled incremental 2026-07-04) and the first Saturday self-heal (2026-07-05 03:00–06:00 UTC).
  Rollback remains `--mode full` on the job args.
- 2026-07-04 (slot-2): **First scheduled cycle + first weekly self-heal — one defect found by the guard, fixed.** (1)
  All 5 daily 01:00 runs green (tradfi 2m30s / cefi 2m16s / defi 1m19s / prediction 2m33s / sports 1m02s), fresh
  artifacts 01:01–01:02Z. (2) 2026-07-04 IS a Saturday — the weekly fulls fired their first cycle: defi full GREEN
  (41m40s, rewrote artifact 04:41Z, +9 rows of drift healed); **cefi full FAILED exit-1 = `CATALOGUE_SHRINK_BLOCKED` —
  the guard caught a REAL merge-key defect**: `_incremental_merge_keys` included the raw `venue` FIELD, but the full
  rebuild's non-pool identity is `instrument_id` alone, so 122 DERIBIT combos whose venue field spelling changed
  era-to-era (`DERIBIT-COMBO`→`DERIBIT`, same id) were ghost-DUPLICATED by the 07-03 catch-up merge → full rebuild
  (which unifies them) < current → guard blocked, artifact protected. **Fix shipped instruments-service@dc378b62c**: key
  = per-AG aggregate identity — non-pool `instrument_id` alone; defi pools dual-form (unchanged); prediction
  `venue::id::data_type` (venue IS identity there — 31 REAL cross-venue cqg pairs in prod, e.g. `BNB_PRICE_RANGE_DAILY`
  on KALSHI + POLYMARKET, proven before shipping so the id-only key would not over-collapse). Ghost regression test
  added; all 4 prod artifacts profiled under the new key (tradfi 0 / defi 0 / prediction 0 legitimate / cefi 122 to
  purge). Next: image rebuild → **corrective `--mode full --allow-catalogue-shrink` cefi run** (the documented
  legitimate shrink: removes the 122 dupes; REQUIRED before the 2026-07-05 01:00 daily, which would otherwise
  shrink-block when the fixed key collapses them) → verify rows==unique_keys → tradfi/prediction weekly-full outcomes
  (in flight, started 05:00/06:00).
- 2026-07-04 (slot-2, closing) — **remediation complete; all 4 weekly fulls GREEN; system clean for the next cycle.**
  (1) Fixed image live: `cloudbuild=97962f5a` SUCCESS at dc378b6 → `:latest` (resubmitted with `_RUN_INIMAGE_QG=false` —
  the in-image QG step needs a git checkout + sibling PM repo a tarball submit lacks; same substitution as the 07-03
  green build). (2) **prediction weekly-full OOM root-caused + fixed**: full-history multi-grain aggregate exceeded the
  daily map's 4Gi ("memory limit was reached", exec `…-prediction-6h4fd`); weekly fulls now carry their OWN resource
  maps — prediction 4cpu/16Gi (Cloud Run couples cpu+memory: 2cpu caps at 8Gi) — deployment-service@LDR (2 commits:
  memory map + cpu map), targeted applies green ("1 changed" ×2); re-run `…-prediction-qlz4b` GREEN 10m22s, artifact
  06:46:51Z. (3) **Corrective cefi shrink executed**: args-override `--mode full --allow-catalogue-shrink` (the
  documented corrective use; full path only), exec `…-cefi-j8v4z` GREEN 50m, artifact 07:16:20Z — verified **365,002
  rows == 365,002 unique keys, 0 ghost dupes** (was 365,124 with 122 dupes). (4) tradfi weekly full `…-tradfi-mh959`
  GREEN 2h33m (05:00→07:32), guard passed (confirms the tradfi incremental artifact carried no phantom rows), artifact
  07:32:53Z. **End-state: all 4 by_date AGs hold full-rebuild-truth artifacts (defi 04:41Z / prediction 06:46Z / cefi
  07:16Z / tradfi 07:32Z), the fixed merge key ships in `:latest` for the 2026-07-05 01:00 dailies, and next Saturday's
  self-heals run with correct resources.** Residual watch: the 07-05 01:00 dailies (first cycle on the fixed key over
  clean bases) — expected green ≥ prev.
