---
doc_type: plan
title:
  Sports consolidated close-out — resolved history (contradiction resolution, answered operator decisions, Progress Log)
summary: >-
  Archive-bound extraction (2026-07-24, 2nd line-cap trim pass after the same-day operator ruling removed the
  umbrella:true exemption) of every resolved/historical section from sports_consolidated_closeout_2026_07_19.md: the
  2026-07-19 contradiction-resolution audit, the cross-AG finding note, the "Operator decisions — ANSWERED 2026-07-20"
  section, and the full Progress Log (including the 2026-07-23 root-cause sweep, PLAN-QUALITY REMEDIATION Track Y,
  issue-doc re-triage, and the 16-decision contradiction/confusion-risk reconciliation). Every item here is either
  checked-off, explicitly marked ANSWERED/no-longer-blocking, or pure narrative — zero open todos. Record-only; not
  intended for further action. The parent's still-open work lives at
  /plans/active/sports_consolidated_closeout_2026_07_19.md.
status: complete
nature: record
asset_group: [sports]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    unified-api-contracts,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [sports, history, archive, plan-hygiene, contradiction-resolution, progress-log]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days:
estimate_calibrated_ai_days:
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Plan line-cap hygiene remediation, 2nd pass, /plans/active/issues/plan_line_cap_remediation_2026_07_23.md -- operator
  ruling 2026-07-24 removed the umbrella:true exemption entirely (flat 1000L hard cap, no exceptions), which
  retroactively put sports_consolidated_closeout_2026_07_19.md (1847L under the old exemption) back over cap.
assigned_role: data_engineering
drift_direction: advance-code
---

# Sports consolidated close-out — resolved history (archive-bound record)

## Contradiction resolution (sports, 2026-07-19)

From a dedicated contradiction sweep (56 issue docs + 11 plans + 9 codex docs + the epic, all read directly, plus 6
GCS/parquet measurements). Matches the `defi_consolidated_closeout` "Contradiction resolution" pattern. **Two of these
are self-contradictions in THIS closeout / the audit — both now fixed** (marked ✅).

### DOC-vs-DOC

1. **112,277 `attempted_failed` triplet — ALREADY root-caused, and TIME-CRITICAL.** Audit §2.5 / Track O called it
   "root-cause needed"; `sports_trades_venue_fetch_failed_2026_07_15` already traced it (v9-rebuild `attempted_at`
   clobber, fix @6fad6565) with a ~2026-07-20 retention cliff. → escalated as the Track O P0 OPERATOR item above.
2. **Staleness budget — same defect as sweep §J, conflicting fix values.** Both target
   `AG_STALENESS_BUDGET_SEC["sports"]` in `_staleness_budget.py`. §J proposed 180–240s (merge-duration); the issue doc
   proposed 1800s (observed ~11-min blob-age swing). The read gate checks blob AGE → §J's value would still false-trip.
   **RESOLUTION**: merge into one fix; size off the observed refresh interval (≥1800s) or re-measure current cadence.
   (HONEST-COVERAGE track.)
3. **`sports-adapter-dependency-order.md` §5 "gate is the one correct DependencyError" ↔
   `sports_t0_t1_dependency_gate_never_wired`**: grep-verified every T1 caller omits `date=`, so the gate never fires
   (confirmed: understat has captured rows 2014-2017 where api-football has zero fixtures — impossible if the gate
   fired). Codex is stale. (ENTITY-SPLIT/CODEX.)
4. **`sports_dependency_check_manifest_vs_gcs_path` measures 11-25 min cost of the same function #3 shows is
   unreachable.** Either the cost was measured via a synthetic `date=`-passing path or the optimization solves a
   non-materializing cost. NOT resolved — reconcile the 5 named call sites against the 11 enumerated in the gate doc.
   (ENTITY-SPLIT.)

### DOC-vs-REALITY (settled by direct measurement)

5. **Manifest atom is literally `"FIXTURES"`** — measured: 333,594 rows, max `written_at` 2026-07-19T10:11:33Z (today),
   ZERO `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES`. Confirms Track C1 objectively. (CANON C1.)
6. ✅ **SELF-CONTRADICTION in the audit (FIXED)**: §2.1 said `entity=fixtures` FROZEN, §2.6 said "still active today".
   Measured: every file incl. today's `day=` partition has `Creation Time 2026-05-23T20:35:42Z` — FROZEN. §2.6 conflated
   pre-fetched future-dated file _presence_ with active writing. Audit §2.6 reworded to "stale, not actively written".
7. ~~**`sports-data-types-catalog.md` still documents lower-case sports data_types** — contradicts K0-(b). Exact quote
   captured. (CODEX.)~~ **INVERTED BY THIS SESSION'S 2026-07-23 RECONCILIATION**: that doc's lower-case content is now
   the CORRECT, settled answer — K0-(b)'s UPPER decision is what's superseded (see Canonical target section above). This
   item is retained struck-through so the history of "which one contradicted which" stays legible.
8. ✅ **SELF-CONTRADICTION in THIS closeout (FIXED)**: K2's "~20,339 rows, one bucket" excluded `trades` = 1,806,553
   rows (91.5%, lower-case) that K1 commits to fixing at the writer. K2 scope corrected above to name the ~1.8M `trades`
   decision explicitly.

### STALE-SUPERSEDED

9. `sports_fixture_round_not_captured_competition_phase_unknown_2026_07_17` headline "3.2%" superseded by measured 70.6%
   (§R-FIXED); status still open. Residual NOT captured elsewhere: audit the sibling `status_long` "Unknown" default
   (same bug class). (COVERAGE/CLEANUP.)
10. Two FOLD plans still list `sports_reference_v2/` as "migrate-worthy" — it's confirmed dead (frozen 2026-04-20). Add
    a retraction note at fold-in. (STORE.)
11. Codex `sports-scheduling-and-sharding.md` §9/§12, `sports-live-odds-connectivity.md` §3 (13 deleted scrapers),
    `sports-integration-plan.md` (mislabeled current) — all confirmed drifted with specifics. (CODEX.)

### NOT-duplicates (explicit, to prevent a future false-merge)

12. Sweep **§B2** (615-min TIER1 dead-zone → EMPTY output) vs `sports_odds_stale_fixture_reinjection` (frozen board
    re-bucketed → OVER-population; Russia-PL zombie class still open, partial fix MDPS@3bf56ff). Different mechanisms,
    same module. Do NOT merge. (ODDS-LEAK — add the reinjection item.)

### Aggregation-completeness gaps — open work NOT in the tracks above (now folded in)

- **A [largest] — the elo/travel/read_historical_fixtures gap-fill campaign is entirely absent from both docs** (grep-0
  for `elo`/`travel`/`read_historical_fixtures`/"521 date"). 4 issue docs, all shipped-in-body but `status: open`:
  `sports_elo_calculator_tz_naive_season_boundary_silent_skip` (@04274b6a),
  `sports_travel_calculator_home_venue_coords_never_resolved` (@6efefde2,@9923b0d8),
  `sports_travel_calculator_tz_aware_kickoff_crash` (@d878f11a,@81036512),
  `sports_read_historical_fixtures_series_ambiguous` (@538c233e,@4be73e2a — a ~521-date recompute fleet ran). **Confirm
  this 521-date gap-fill and the §Z re-run are ONE combined recompute, not dropped against each other.** → FEATURES.
- **B** — the ⏰ 112,277 retention cliff (finding #1) → Track O P0 above.
- **C** — `sports_odds_ownership_registry_split_brain`: ✅ **DONE 2026-07-16** (corrected 2026-07-24 — was stale here).
  The DEFERRED PURGE (123,149 bogus `api_football×ODDS` rows, re-measured at execution time vs. the originally-estimated
  127,018) + "did the re-seed stop" verify both completed via `sports_legacy_bucket_cutover_2026_07_16.md` T3.1/T3.2; 0
  rows remain, independently re-verified 2026-07-23/24. → CANON/ODDS-LEAK.
- **D** — `sports_manifest_null_vs_empty_dedup_double_count`: unexplained consolidator incremental-dedup gap + 612,682
  blank-`error_reason` `empty_confirmed` residue. → HONEST-COVERAGE.
- **E** — `sports_index_recency_masked_captured_atoms`: redeploy `expected-universe-v2-sports` Cloud Run image + P3
  cross-AG seeder-over-captured sweep. → HONEST-COVERAGE.
- **F** — `sports_odds_team_name_alias_gap_south_america`: Chile PRIMERA_DIVISION Odds-API aliases missing (57% match).
  → CANON/COVERAGE.
- **G** — `sports_odds_stale_fixture_reinjection` Russia-zombie half (finding #12). → ODDS-LEAK.
- **H** — `status_long` "Unknown" default audit (finding #9). → CLEANUP.
- **I** — `sports_derived_features_per_league_layout_unread_by_ml_loader`: features-bucket path SSOT codex doc +
  `odds_api_team_mapping` coverage. → CODEX/CANON.
- **J** — `sports_dependency_check_manifest_vs_gcs_path`: manifest-slice replacement for `check_api_football_dependency`
  (finding #4). → ENTITY-SPLIT.
- **K** — `sports_reference_function_size_qg_regression`: 3 functions over the QG size ratchet. → CLEANUP.
- **L** — `sports_cf8_available_at_backfill_regression`: RED on both surfaces, parked pending an operator window. →
  operator decisions.
- **M** — `sports_halftime_odds_sfi_vs_inplay`: `_apply_ht_odds_pit_gate` default-cutoff branch is dead code; 12,463 T-0
  rows at `bm<-55` flow ungated. → ODDS-LEAK.
- **N** — `sports_is_manifest_eu_regression_overwrite`: footystats MATCHES (5,641) + PREDICTIONS (44,163) residuals not
  root-caused at the writer. → HONEST-COVERAGE.
- **O** — ~~`sports_legacy_canonical_row_gap` OR-1 Option D (player_stats-only union + fixture_events re-fetch) never
  executed~~ **CORRECTED 2026-07-23 (re-triage)**: OR-1 Option D WAS executed the same day as this audit
  (`sports_legacy_bucket_cutover_2026_07_16.md` T2.4, 388,825 rows / 4,015 cells recovered) — this line was stale from
  authoring, not a real gap; see `issues/sports_legacy_canonical_row_gap_2026_07_16.md`'s RE-TRIAGE section for the
  exact match. The 3 unfiled loose ends (canonical player_stats 2x dup; standings/teams writing 2026 live under
  historical `day=`; 640-row cartesian player_values) were NOT re-verified today — still presumed open. → STORE.

### Duplicate/merge + status-flip recommendations

- Merge `sports_manifest_read_staleness_budget_missing` → sweep §J. Merge `sports_trades_venue_fetch_failed` → the
  112,277 item. Flip `sports_golden_window_attempted_failed_remediation` +
  `sports_is_odds_capture_code_incomplete_reversal` → resolved, pointing at `sports_odds_ownership_registry_split_brain`
  (terminal). **~20+ issue docs are shipped-in-body but still `status: open`** — the Track X status-flip sweep should
  cover the full list, not a sample.

## Cross-AG finding (belongs to a prediction/tick close-out, tracked here for visibility)

- [x] [DIAG] P1. ✅ **STALE CHECKBOX FLIPPED 2026-07-23 (adversarial-review finding C)** — this todo's own document
      already shows it fully resolved further down (root-caused, fixed, and remediated — see the checked item below and
      the "re-triage" section's `mtds@a7ff45f9`/`@299ef540` entries). Original text retained for history: **4,097 live
      `asset_group="prediction"` rows (+2 cefi/defi) physically in the sports bucket manifest** (Kalshi/Polymarket,
      `service=market-tick-data-service`, dates 2026-06-26…07-18). Two write paths ruled out; next:
      `ingest_kalshi_bulk_to_canonical.py`, `rebuild_prediction_manifest.py`, the sentinel fan-out. Cross-repo/SSOT
      class — NOTIFY OPERATOR (done in-session 2026-07-19).

## Operator decisions — ANSWERED 2026-07-20 (no longer blocking)

All four resolved in interactive chat. These are now actionable, not gated:

1. **Cross-AG bleed → ROOT-CAUSE FIRST, THEN PURGE.** Locate the third emitter writing `asset_group=prediction` rows
   into the sports manifest (two paths already ruled out: MTDS Kalshi/Poly write paths resolve
   `instruments-store-prediction` correctly; `websocket_runner.py:77` fails loud). Candidates to check:
   `ingest_kalshi_bulk_to_canonical.py`, `rebuild_prediction_manifest.py`, the `SportsCatalogReader`/`FixtureIdResolver`
   sentinel fan-out. Fix the writer, THEN purge the 4,097 rows — purging while the emitter is live just means they
   return (same ordering as K1-before-K2).
2. **§U registry gap → STOP CAPTURING NON-REGISTRY LEAGUES** (operator chose to narrow capture, NOT to extend the
   registry). Target state is **captured == intended**: the sports capture universe is the UAC registry, full stop.
   Implementation: narrow the capture/enumeration path to the registry universe so no non-registry league is fetched
   again; then decide the disposition of the ALREADY-captured non-registry rows (10,869 blank-round rows across 489
   league-seasons) — they must be excluded from the coverage denominator at minimum, and are purge candidates since they
   are by definition out-of-universe. **Consequence: "sports backfilled 100%" becomes literally true against the
   registry denominator**, because the unreachable rows stop being part of the universe.
3. **§T pre-2019 → OUT OF SCOPE.** The window stays 2019-01-01..present. The 122,864 pre-2019 blank-round rows
   (2013–2018) are **intentionally excluded** — document them as a known, explained exclusion, not a gap. No further
   api-football spend.
4. **K2 casing → MIGRATE ALL ~1.8M `trades` → `TRADES`.** ~~Full canonical consistency; the bucket ends UPPER everywhere
   per K0-(b).~~ **SUPERSEDED 2026-07-23**: K0-(b) itself is now superseded (see Canonical target section above) —
   sports data_type is being reconciled to LOWER-case for ALL types, so K2's UPPER direction is being reverted, not the
   other way around. This decision's scoping-correction half still stands (the "~20,339 rows, one bucket" estimate
   wrongly excluded `trades` = 91.5% of the bucket) — only the casing DIRECTION it targeted is now wrong. This
   supersedes the original "~20,339 rows, one bucket" scoping. **K1 (live writer emits UPPER) must ship BEFORE K2** or
   the migration re-dirties on the next write — this ordering lesson is REUSED, not retracted, for the revert:
   registry+writers before data (see Track C's new revert todo).

### Newly-actionable todos from these decisions

- [x] [DIAG] P1. ✅ **STALE CHECKBOX FLIPPED 2026-07-23 (adversarial-review finding C)** — root-caused, fixed
      (`mtds@5581dcf9`, then the manifest-bucket sibling bug via `mtds@299ef540`), and remediated (`mtds@a7ff45f9`,
      VERIFY PASSED, 0 remaining) — see this doc's own 2026-07-23 re-triage section. This checkbox was never flipped
      despite the resolution being recorded further down in this same document. Original text retained for history:
      Root-cause the cross-AG emitter (decision 1), then purge. **MEASURED 2026-07-20 — it is LIVE and GROWING, and
      larger than the audit said**: 4,097 (audit, 07-19) → **6,597 now**, +2,500 added TODAY alone (07-17: 1,756 ·
      07-19: 2,341 · 07-20: 2,500, newest `written_at` 00:54:58Z). So a DAILY job is still writing. Fingerprint (from a
      direct read of `instruments-store-sports-prd/_index/availability_index.parquet`):
      `service_name=market-tick-data-service`, `pipeline_mode` batch_kalshi (6,562) / batch_polymarket_clob (35),
      `venue` KALSHI/POLYMARKET, `data_type` trades (6,484) + prediction_canonical_question_group (113),
      `capture_status` captured (6,567) / empty_confirmed (30), schema_version 9, DATA dates 2026-07-16..07-19
      (forward/recent, i.e. the LIVE capture path — not a historical migration). Plus 1 cefi + 1 defi row
      (BITGET-FUTURES / UNISWAP_V3-BASE, service=instruments-service). **RULED OUT**: (a)
      `ingest_kalshi_bulk_to_canonical.py` and `canonicalize_prediction_manifest_2026_07_18.py` both resolve
      `market-data-tick-prediction` correctly; (b) `websocket_runner.py:451` resolves `instruments-store-prediction`;
      (c) the current per-VM shards in the sports bucket — they contain only sports + blank-`asset_group` rows, NO
      prediction rows. **FALSE LEAD, discarded (do not re-chase)**: the two live `af-backfill-*` per-VM shards hold
      ~100k rows with EMPTY-STRING `asset_group` — that is BENIGN, the consolidator fills asset_group from bucket
      context on merge (consolidated index has **0** blank-asset_group rows). Blank `venue` is likewise normal (4.3M
      sports reference rows have none). **NEXT**: the emitter writes to the sports instruments-store manifest on a DAILY
      cadence from the live Kalshi/Polymarket capture path, bypassing the per-VM shard route. Find the live prediction
      capture job's ManifestWriter bucket resolution (anything resolving `kind="instruments-store"` with a
      defaulted/sports asset_group while writing prediction rows), fix it, THEN purge (purging first = they return
      tomorrow). **✅ ROOT-CAUSED 2026-07-20 — NOT manifest-only: REAL TRADE PARQUET BYTES are in the wrong bucket.**
      Emitter = Cloud Run Job `mtds_fast_t1_recon_job`
      (`deployment-service/terraform/gcp/audit03_cron_provisioning.tf:69`, daily `30 0 * * *` per
      `t1_batch_scheduler.tf:128-131` — matches the newest write 2026-07-20T00:54:58Z), which runs
      `--asset-group SPORTS PREDICTION` in ONE invocation. Bug:
      `market_tick_data_service/engine/orchestrator/__init__.py:680-682` sets `primary_asset_group = next(...)` =
      **"SPORTS" (first element) for the WHOLE run**; `_manifest_bucket.py:49-52`'s sports carve-out then routes the
      manifest to instruments-store-sports for EVERY venue incl. KALSHI/POLYMARKET. Worse, `venue_fetch.py:506,633-635`
      writes the DATA to that same run-level `state.bucket`, so parquet lands in `market-data-tick-sports-prd-*`. The
      row's `asset_group` COLUMN is stamped correctly by the per-venue `_resolve_asset_group` (`venue_fetch.py:614`) —
      so **bucket resolution is PER-RUN while asset_group resolution is PER-VENUE. That inconsistency is the whole
      bug.** CONFIRMED LIVE: 6,451 KALSHI + 3 POLYMARKET real trade parquet files physically under
      `gs://market-data-tick-sports-prd-.../raw_tick_data/by_date/day=2026-07-16|18|19/.../venue=KALSHI/`. Isolated to
      this job (TRADFI already excluded for the analogous mis-stamp reason; CEFI/DEFI have dedicated jobs). Downstream:
      prediction readers looking only at the prediction bucket are BLIND to this data. **The 1 cefi + 1 defi rows are a
      DIFFERENT cause** (`service_name=instruments-service`) — own look, do not assume shared root cause.
- [ ] [INFRA] P2. **Defense-in-depth (no longer urgent — the code fix removes the need)**: split
      `mtds_fast_t1_recon_job` into two jobs (`--asset-group SPORTS` and `--asset-group PREDICTION` separately),
      mirroring the existing `mtds_cefi_t1_recon_job` isolation. Config-only.
- [x] [CODE] P1. ✅ **FIXED — market-tick-data-service@5581dcf9** (QG green). Resolves data buckets **per-venue** in
      `process_ticks()` (reuse the per-venue `_resolve_asset_group(venue, asset_groups)` at `venue_fetch.py:614`)
      instead of one run-level bucket.
- [x] [DATA] P1. ✅ **CROSS-AG DATA REMEDIATION COMPLETE (2026-07-20)** — executed in the safe order, every step
      verified, nothing orphaned: (a) **Snapshotted both manifests** first →
      `_index/backups/pre_crossag_remediation_20260720T103143Z.parquet` in BOTH `instruments-store-sports-prd` and
      `market-data-tick-pred-prd`. (b) **Relocated 6,454 objects** (6,451 KALSHI + 3 POLYMARKET, days 2026-07-16/18/19)
      sports→prediction tick bucket via UTL `gcs_copy_object` (server-side): **6,454/6,454 crc32c-VERIFIED, 0 missing, 0
      mismatch, 0 fail**. (c) **Upgraded the PREDICTION manifest**: wrote per-VM shard
      `_index/per_vm/crossag_relocation_20260720.parquet` with **6,560 genuinely-new rows** (37 of the 6,597 already
      existed and were correctly deduped on `date/venue/data_type/instrument_type/instrument_id`) — read-back verified
      (KALSHI 6,526 / POLYMARKET 34). (d) **Purged the sports manifest**: 6,597 `asset_group=prediction` rows removed,
      **0 remaining** (5,377,593 → 5,370,996). The 1 `cefi` + 1 `defi` rows were deliberately LEFT — different root
      cause (`service_name=instruments-service`), purging them blind could mask a separate bug. (e) **Deleted the
      sports-bucket duplicates**: 6,454 removed, **0 skipped**, with a per-file re-verify that the prediction copy
      existed with matching crc32c immediately before each delete. Final sweep: **0 `asset_group=prediction` objects
      remain in the sports tick bucket.** Ordering mattered: prediction manifest rows were written BEFORE deleting the
      sports originals, so the data was never unlisted in either direction.
- [x] [CODE] P1. ✅ **ALREADY SHIPPED (2026-07-13) — no new work needed.** `_is_in_canonical_write_universe`
      (`orchestrator/sports.py`) already gates per-league captured writes to the registry universe and is WIRED at 9+
      live call sites (`sports_reference_core.py:431,507,594`, `footystats.py:203,613,991`, `sports_fixtures.py:431`,
      `understat.py:190,470`). The 2026-07-13 24-league de-registration ruling set "the sports universe is EXACTLY the
      registered-league set" and the catalogue gates on `_sports_league_registered` too. Decision 2's _forward_ half is
      done.
- [ ] [DIAG] **P0 — ⛔ BLOCKS decision 2's purge half. LEAGUE_ID NAMESPACE MISMATCH, measured 2026-07-20.** The
      manifest's `league_id` namespace does NOT match the canonical registry's:

      | manifest `league_id` (raw) | canonical registry key |
                                                                                                                                                                                                                                                                                                                                                  | -------------------------- | ---------------------- |
                                                                                                                                                                                                                                                                                                                                                  | `PREMIER_LEAGUE`           | `EPL`                  |
                                                                                                                                                                                                                                                                                                                                                  | `CHAMPIONSHIP`             | `ENG_CHAMPIONSHIP`     |
                                                                                                                                                                                                                                                                                                                                                  | `PRIMERA_DIVISION`         | `LA_LIGA`              |
                                                                                                                                                                                                                                                                                                                                                  | `2._BUNDESLIGA`            | `BUNDESLIGA_2`         |
                                                                                                                                                                                                                                                                                                                                                  | `FIRST_DIVISION_A`         | (no registry entry)    |

                                                                                                                                                                                                                                                                                                                                                  Measured: **328,999 manifest rows carry a `league_id` absent from `LEAGUE_REGISTRY`, and 265,134 of them were
                                                                                                                                                                                                                                                                                                                                                  written ON/AFTER the 2026-07-13 gate ruling** (statuses: captured 213,861 / empty_confirmed 50,975 /
                                                                                                                                                                                                                                                                                                                                                  attempted_failed 298). Verified there is NO alias — `PREMIER_LEAGUE`/`PRIMERA_DIVISION`/`2._BUNDESLIGA`/
                                                                                                                                                                                                                                                                                                                                                  `FIRST_DIVISION_A` appear nowhere in any registry entry's definition (only `CHAMPIONSHIP` partially matches
                                                                                                                                                                                                                                                                                                                                                  `ENG_CHAMPIONSHIP`/`SCOTTISH_CHAMPIONSHIP`/`USL_CHAMPIONSHIP` as a substring, which is itself ambiguous).

                                                                                                                                                                                                                                                                                                                                                  **⛔ CONSEQUENCE: executing decision 2's "purge the non-registry rows" against the SYMBOLIC `league_id` would
                                                                                                                                                                                                                                                                                                                                                  DELETE core trading data — Premier League, La Liga, the Championship.** Those are not out-of-universe leagues;
                                                                                                                                                                                                                                                                                                                                                  they are in-universe leagues recorded under a different naming convention. The purge MUST NOT run until the
                                                                                                                                                                                                                                                                                                                                                  namespace is reconciled.

                                                                                                                                                                                                                                                                                                                                                  NOTE this is a DIFFERENT axis from §U's 489-pair finding, which compared NUMERIC `af_league_id` against the
                                                                                                                                                                                                                                                                                                                                                  registry's `api_football_id` set (sound, numeric-vs-numeric). Both are real; do not conflate them. This is the
                                                                                                                                                                                                                                                                                                                                                  §C2 "league_id namespace reconciliation" item, now measured and escalated to P0.

- [x] [CODE] P0. ✅ **WRITE PATH CANONICALISED — operator chose canonicalise-at-write (2026-07-20); shipped
      market-tick-data-service@ad4f1872.** `_canonical_league_id()` resolves via the NUMERIC `api_football_id`; all 30
      write-path prediction leagues resolve (0 unresolved), 13 of 30 change value; unresolvable ids fall back to the raw
      name so an unregistered league still captures. The `--leagues` filter now accepts BOTH forms — it previously
      compared the raw value, so every existing launcher invocation would otherwise have silently fetched nothing.
      **Measurement proved the alias-map alternative would have CORRUPTED data**: six raw names are ambiguous
      (`BUNDESLIGA` German+Austrian, `SERIE_A` Italian+Brasileirao, `SERIE_B`, `CHAMPIONSHIP` English+Scottish,
      `PRIMERA_DIVISION` Argentina+Chile, `SUPER_LEAGUE` Greek+Swiss) — a name-keyed map MERGES them. 3 regression
      tests, incl. one asserting the collisions resolve to DISTINCT slugs. Design + history plan:
      `issues/sports_league_id_namespace_migration_2026_07_20.md`.
- [x] [DATA] P0. ✅ **RE-TRIAGE 2026-07-24 (live GCS + manifest verification): this IS the same work as
      `sports_master_closeout_2026_07_21.md`'s executed COPY+SWAP — this item was STALE, describing the pre-migration
      state.** Migrate the 214,842 historical non-canonical manifest rows (75,432 of them ambiguous, resolved via
      per-row `sport_key` classification — see `issues/sports_league_id_namespace_migration_2026_07_20.md` for the full
      design). **Status, independently re-verified this session (not re-derived from the doc's prose alone):** (1) GCS
      COPY relocation EXECUTED — 275,136/275,136 target objects verify=PASS, 54,835,957 rows written (mtds@b2a49317,
      24-VM fleet, 2026-07-21/22); I re-aggregated all 24 raw shard-report JSONs directly from
      `gs://deployment-scripts-central-element-323112/canonical-migration-sports-reloc/reports/` this session and
      independently reproduced the exact same totals (275,136 objects / 54,835,957 rows) — not just trusting the doc's
      claim. (2) The manifest ADD/REMOVE swap for this relocation EXECUTED 2026-07-22 (folded into the combined K1/K2
      casing swap per master_closeout's "fourth/sixth wave" log: ADD 373,296 keys, of which 275,135 were this
      relocation's canonical rows; REMOVE dropped the stale raw-keyed rows; VERIFY PASSED stale_remaining=0). (3) Live
      spot-check this session (`day=2020-06-30/venue=BETVICTOR`): canonical
      `league_id=EPL/instrument_type=ODDS/     data_type=TRADES/ticks.parquet` exists; the OLD raw-keyed
      `league_id=PREMIER_LEAGUE/` GCS prefix is STILL PRESENT for the same cell — confirms COPY+SWAP is done, the
      GCS-object DELETE genuinely has not run. **Only the human-gated delete of the old raw-keyed GCS objects remains**
      — was tracked in `sports_master_closeout_2026_07_21.md`'s own P0 "RUN THE MANIFEST-SWAP TOOL FOR REAL, then
      DELETE" todo; that doc is now ARCHIVED (2026-07-24, `/plans/archive/2026_07/sports_master_closeout_2026_07_21.md`)
      and its delete action + full 5-part-proof checklist are folded verbatim into the new todo directly below, so the
      action isn't lost. Detail: `issues/sports_league_id_namespace_migration_2026_07_20.md`.
- [ ] [DATA] P0. **NEW 2026-07-24 (folded in from archived `sports_master_closeout_2026_07_21.md`) — execute the gated
      DELETE of the old raw-keyed league_id GCS objects.** The manifest-swap ADD/REMOVE already executed (see above);
      only the object delete remains — a codex hard stop, human-only regardless of confidence
      (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3 #1). **5-part-proof checklist as of 2026-07-22
      (RE-VERIFY before acting, especially Part 3 given the K1/K2 casing-direction revert decided in Track C above)**:
      Part 1 twin probe PASS (275,136/275,136 target objects written, mtds@b2a49317); Part 2 content PASS (the
      relocation's own verify + the manifest-swap's independent re-derivation land on the exact same 275,136 ADD /
      260,298 REMOVE, zero collisions); Part 3 writers **FAIL as of 2026-07-22** (`venue_fetch.py:887,896` +
      `manifest_finalize.py:347` were still writing new objects to the old non-canonical shape every day — only
      `league_id` casing was fixed at the source, not this axis); Part 4 readers NOT BLOCKING (MDPS reprocess tolerates
      old+new coexisting); Part 5 twin coverage 100% for relocated historical cells, 0% for any cell written after the
      relocation's index walk. Disposition as of 2026-07-22: no-migrate-first (Part 3 failed then) — re-evaluate live,
      do not assume still true. **FOLD IN**: the already-deleted 6,110 `mtds_t2_6` lowercase-twin objects' manifest rows
      are the SAME population as the "prune the twin-delete phantom manifest rows" todo in Track S below — one pass, not
      two.
- [ ] [CODE] P1. **LIVE BUG — canonicalise the bookmaker-league coverage registry.** Measured 2026-07-20: the sports v2
      sentinel calls `is_bookmaker_league_covered(bm, _canon_lid)` with a CANONICAL id (`sentinels.py:319`) but
      `BOOKMAKER_LEAGUE_COVERAGE` (`unified-api-contracts/.../sports_bookmaker_league_coverage.py`) is keyed on RAW
      names — independently confirmed `is_bookmaker_league_covered("BETFAIR_EX_EU","EPL")==False` vs
      `…,"PREMIER_LEAGUE")==True`. So every not-yet-captured (bookmaker, canonical-league, fixture) shard is mis-stamped
      `EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE` instead of surfacing as a real gap — a standing coverage false-negative
      TODAY, independent of the relocation. Fix: regenerate the registry JSON from `ODDS_API_DISPLAY_TO_CANONICAL` (or
      re-run `refresh_sports_bookmaker_league_coverage_2026_06_21.py` after the manifest is canonical).
- [x] [CODE] P1. ✅ instruments-service per-fixture path — **SHIPPED instruments-service@815ad06c.**
      `sports_reference_fixtures.py` always took the `fx.league.league_id` branch, making the numeric-id `elif` dead
      code (`CanonicalLeague` always carries `league_id`, so the first branch always won). Precedence inverted to
      resolve by numeric `api_football_id` first, falling back to the raw value only for an unregistered league (honest
      absence, not a vanished map entry). 2 regression tests pin the precedence. Earlier blocked by another worker's
      divergent defi WIP in the clone (AUTOSTASH_POP_CONFLICT); verified green on the clean origin base via a sibling
      worktree (160 tests incl. the previously-foreign golden/dedup failures now fixed upstream), then shipped once the
      clone reconciled — foreign WIP never touched. Companion to the write-path fix mtds@ad4f1872.
- [ ] [DATA] P2. Dispose of the genuinely-out-of-universe rows (decision 2): exclude from the denominator; purge only
      once confirmed. **UNBLOCKED 2026-07-24** — the historical migration above has its manifest-side COPY+SWAP executed
      and verified (stale_remaining=0), so the manifest's `league_id` values for Premier League / La Liga / the
      Championship are now canonical and a registry-membership test correctly classifies them as in-registry; the purge
      is no longer at risk of deleting core trading data on that account. Snapshot before any delete regardless.
- [ ] [DOC] P3. Document pre-2019 (2013–2018) as an intentional, explained exclusion (decision 3) in the audit's gap
      table so the remaining-blanks arithmetic reads clean.
- [x] [DATA] P1. ~~K2 scope is now ALL lower-case rows incl. ~1.8M `trades` (decision 4) — gated on K1 shipping first.~~
      **SUPERSEDED 2026-07-23**: K1/K2 shipped the OPPOSITE direction (migrated `trades` UP to `TRADES`, not "all
      lower-case"). This session's casing reconciliation now supersedes decision 4 itself — see the Canonical target
      section's data_type entry above: the target is all-lower including `trades`, and K1/K2's uppercase migration is
      being reverted, not extended. This todo's original wording is now moot.

<!-- REMOVED 2026-07-23 (reconciliation pass): the "## Operator decisions needed (blocking)" section that lived here
     listed §U and §T as still-blocking, but the "Operator decisions — ANSWERED 2026-07-20" section above already
     resolved both, and Track O's P0 retention-cliff item is separately marked done — this was a stale leftover
     carried unedited from the parent audit doc through three later revision passes. Deleted per operator decision;
     current genuinely-open operator items are tracked in the "Operator decisions needed (blocking) — 2026-07-23"
     section further down, right after the 2026-07-23 root-cause sweep. -->

## Progress Log

- 2026-07-19 — Plan authored from the 6-agent audit. §Z (Track F P0) already FIXED (features-service@c6eb1f38); the
  writing fleet was stopped; corpus re-run pending behind the C1 manifest-atom fix. All other tracks open.
- 2026-07-22/23 — K1 (live writer casing) + K2 (historical casing migration) + the phantom `soccer_*` manifest-row prune
  ALL SHIPPED + VERIFIED complete for their scope (`batch_odds_api`/TRADES axis: 373,297 canonical rows, 0 remaining
  lowercase, 0 remaining phantom rows). Full evidence + SHAs:
  `/plans/archive/2026_07/sports_master_closeout_2026_07_21.md` (archived 2026-07-24) fourth/fifth/sixth-wave Progress
  Log. Track C's K1/K2 todos above are flipped with evidence.
- **2026-07-23 (interactive reconciliation session) — this closeout had drifted into internal contradiction and lost
  track of 9 sibling plans; both fully reconciled.** A 2-pass multi-agent audit (covering every related plan/issue/
  codex doc, ~85 documents total) plus direct code verification found: a critical unreconciled casing conflict (this doc
  said UPPER, a same-day codex reversal said lower for the odds-family, K1/K2 shipped UPPER anyway ~19h after the
  reversal landed); a stale "Operator decisions needed" section contradicting its own ANSWERED section 150 lines above
  it (same stale pattern ALSO found duplicated inside Track V's §U/§T todos — both fixed); 4 plans this doc claimed to
  "fold in" that were never actually archived and had live contradicting content; 5 more live sports plans with real
  scope overlap this doc never knew existed; a Track D "done" checkbox certifying codex banners that a fresh read showed
  were incomplete (3 docs with no banner, 3 more stale under their own banner); and — via a live Distinct Values read
  from the deployment-ui pasted by the operator mid-session — confirmation that sports' venue/instrument_type/chain
  non-canonical rates (9/17, 16/16, 3/3 respectively) trace to 3 sibling positional-parse bugs in
  `market-data-processing-service` that were only partially root-caused before (instrument_type's mechanism was known;
  chain's was assumed-same-function but is actually a sibling function with a different bug shape; venue's
  parts[0]-misread was undiscovered). The operator was walked through every conflict interactively (16 numbered
  decisions) and ruled on each — see the new "2026-07-23 — full contradiction + confusion-risk reconciliation" section
  further down for the complete decision record, and the Tracks above for the resulting new todos. **Per explicit
  operator instruction, this entire pass is DOCS-AND-PLANS ONLY — no code shipped, no data migrated, no GCS/manifest
  writes executed.** The next session should start from Track C's data_type-revert + 3-bug-fix todos (P0, gates
  everything else) and Track H's odds-pipeline-dormancy investigation (P0, the single highest-priority unknown).
- **2026-07-23 (reconciliation session, completion) — all mechanical reconciliation work landed.** Ran to completion via
  a follow-up multi-agent workflow: (1) all 4 fold-in plans archived (`status: superseded`,
  `superseded_by: sports_consolidated_closeout_2026_07_19.md`, each with its own banner) with live content extracted and
  pulled in — the EXCHANGE_ODDS/FIXED_ODDS 9-step sequence into Track C, the remaining ~20 items into the new "Track S2
  — FOLD-IN ABSORPTION" section; (2) all 5 orphan plans linked (`related:` + banner) with a reconciliation todo each,
  now in Track X; (3) 9 codex docs fixed with real body rewrites (not just banners):
  `sports-adapter-dependency-order.md`, `sports-scheduling-and-sharding.md`, `sports-fixtures-lifecycle.md`,
  `honest-absence-downstream-handling.md` (new finding: `SCHEDULE_DEFINING_DATA_TYPES` is a 9th C1 call site, added
  above), `sports-batch-live.md`, `pipeline-coverage-matrix.md`, `sports-integration-plan.md`,
  `sports-live-odds-connectivity.md`; (4) `sports_master_closeout_2026_07_21.md`'s entry-point self-contradiction
  resolved via a new `entry_point_for:` frontmatter field (added to `plans/PLAN_FORMAT.md`'s schema); (5) the
  odds-feature four-way-naming decision (new deliberate naming, full data+manifest migration) + a generative naming
  scheme recorded in `sports_odds_feature_naming_canonicalization_2026_07_21.md`'s Progress Log. **Still nothing
  executed** — every item above is a documentation/plan edit; no code shipped, no GCS/manifest write, no data moved. A
  fresh session can now execute top-to-bottom without hitting any of the contradictions this pass found.

## 2026-07-23 — root-cause sweep on sports odds honest coverage (session continuation)

Answering an operator Q&A thread on sports MDPS/MTDS honest-coverage tracking surfaced 3 real findings, all investigated
to a root cause (not just symptom-documented) and either fixed or properly scoped:

- [x] [DATA] P0. ✅ **api_football wrong-source manifest rows (1,266,874) — root-caused + fixed + wiped.** Root cause:
      `SOURCE_PRIORITY` had no `("sports","TRADES")` entry, so `derive_pipeline_mode_for_row()` fell through to the
      sports asset-group's `api_football` default, mislabeling every sports TRADES sentinel row. Fixed:
      `unified-api-contracts@44623d25`. Wiped (CAS-safe, manifest-only): `market-tick-data-service@e9d9dec0`
      (1,266,874/1,266,874 removed, VERIFY PASSED). GCS-object deletion for the ~7,251 captured cells remains a
      SEPARATE, operator-gated step (prod-bucket delete = human-only). Full detail:
      `issues/mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md` (resolved). This SAME wipe
      also removed the exact 58,016-row dead-residue population `issues/sports_trades_attempted_failed_2026_07_23.md` (a
      concurrent agent's independent DP_RUN_MOSTLY_EMPTY alert triage) had just diagnosed — that doc's todo #1 (restore
      historical `attempted_at`) is now superseded (rows deleted, not restored).
- [x] [DATA] P2. ✅ **MDPS `odds_movement`/`odds_snapshot`/`arbitrage_opportunity` zero-production-objects —
      root-caused: dead code.** The only live sports MDPS Cloud Run job (`uts-prod-mdps-odds-horizon-bucket`) runs a
      standalone script (`reprocess_sports_odds.py`) hardcoded to `odds_horizon_bucket` only — never touches
      `CandleAdapterRegistry`, the generic path these 3 adapters are registered under. No other job/scheduler/VM reaches
      them. Registered in `SOURCE_PRIORITY`/`DATA_TYPES_BY_ASSET_GROUP` (aspirational), never actually scheduled.
      Operator decision needed: wire them up for real, or retire the registrations. Detail:
      `issues/sports_mdps_derived_odds_products_zero_prod_objects_2026_07_23.md` (resolved — the "why" is answered; the
      "what to do about it" is an open P2 decision).
- [ ] [DATA] P1. **NEW, bigger finding: sports ODDS_API (TRADES) capture pipeline scheduling status UNKNOWN.** While
      verifying the api_football fix had reached running instances, found ZERO sports manifest writes of any kind for
      ~12h+ at time of check, the historical `oddspapi-w01/w02/w03` Cloud Run jobs last ran 2026-03-29 (~4 months ago),
      and no GCP Cloud Scheduler entry or running VM currently drives sports odds capture. Could NOT check AWS-side
      scheduling (IAM-denied) or persistent-VM-internal crontabs. **Genuinely unknown whether new sports odds data is
      arriving at all right now** — this matters more than the two findings above, since fixing label-correctness of
      data that has stopped arriving is far less valuable than it looks. NOT resolved — needs its own dedicated
      investigation with proper infra access. Detail:
      `issues/sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md`.
- [x] [VERIFY] P1. ✅ **Sentinel fan-out for TRADES honest-coverage — verified mechanism exists + looks correct.**
      `sentinels.py::_emit_sports_v2_sentinels` fans out over every (bookmaker × league × fixture) from the
      instruments-service fixture catalog, checks UAC `is_bookmaker_league_covered_exact()`, and resolves EVERY combo to
      `record_failed`/`record_zero_rows`(empty_confirmed)/captured — nothing left silently untracked, by design. Could
      not observe it actually firing in production (ties to the dormant-pipeline finding above) — the current manifest
      shows 373,297/373,297 = 100% `captured`, 0 empty/failed for the `batch_odds_api` scope, which is consistent with
      either genuine completeness or the mechanism simply not having run recently enough to surface any gaps. Re-verify
      once the dormant-pipeline question above is resolved.
- [ ] [OPERATOR] P0. **The separate, irreversible, 5-part-proof-gated DELETE of old non-canonical K1/K2 GCS objects**
      (and now also the ~7,251 `api_football` captured-cell objects) remains human-only per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3#1 — evidence prepared, not executed, not something
      to do autonomously regardless of confidence.

### Sports issue-doc index (swept 2026-07-23 — every `plans/active/issues/sports_*.md` not already linked above)

Not individually triaged/re-verified today (that is its own large effort) — listed here so nothing is orphaned from
discovery. Priorities are each doc's own self-assessed value; treat as a starting point, not a re-confirmed ranking.

## Track Y — PLAN-QUALITY REMEDIATION (2026-07-23, adversarial-review findings A/B/D/E/F/G)

A second independent agent adversarially reviewed this doc's AO-dispatch-readiness (findings lettered A-G; finding C — 2
stale checkboxes — was fixed directly above, in place, with evidence). The remaining findings are real defects in THIS
document, tracked here rather than silently fixed under time pressure so nothing is lost:

- [x] [DOC] P0. ✅ **Finding A — PARTIAL FIX 2026-07-23.** Rewrote all 4 flagged Track F todos (re-run, 2017+2018
      re-run, PURGE, re-verify) + the Track C revert todo (3 layers were buried past line 1) + the F1/F2 parse-bug fix
      todo (the actual fix was buried past a problem-only line 1) so the complete instruction — action, method, and any
      hard constraint like ON-DEMAND vs SPOT — is now on line 1 of each. **Not yet exhaustive**: a background sweep of
      Tracks H/K/D/X/S2 for the same pattern is in progress (dispatched same session) — this checkbox reflects the Track
      F/C fix, not a doc-wide guarantee yet; see the follow-up todo below once that sweep reports.
- [x] [DOC] P0. ✅ **Finding B — FIXED 2026-07-23.** The re-run todo now states its own dependency exactly once ("does
      NOT depend on Track C's C1... gated only on the season_context fix + a fresh tarball") with an explicit "this is
      the ONE place this is stated" guard; the PURGE and re-verify todos now each open with "only after <predecessor> is
      done." **Not machine-enforced** — this plan is `assigned_vm: NA` (not currently AO-dispatched), so
      `sequential: true`/`gate_on_depends` wiring is deliberately deferred until this chain is actually extracted for
      dispatch (consistent with the operator's 2026-07-23 "a guard comment is enough for now" ruling on the broader
      child-plan-split question) — the prose guard is the interim safety net, not a permanent substitute.
- [x] [DOC] P1. ✅ **Finding D — FIXED for every open-todo first-use 2026-07-23.** Resolved each label's real meaning by
      reading `sports_consolidated_audit_2026_07_19.md` directly rather than guessing: §Q/§R/§T/§U/§W = "the round work
      from the 2026-07-18 sweep... confirmed terminal" (round-derivation/catalogue-repoint/backfill, per the audit's own
      headline verdict) — T/U further specialize into the two now-answered operator decisions (pre-2019 scope; registry
      membership); §V = the split-entity read fix; §A2 = `plan_reconciliation_operator_decisions_2026_07_11.md`'s own
      §A2 ruling batch (a different doc, cited correctly now). §C2/C3/C6/§R/§B2 turned out to already state their fact
      adjacent to the label (citation-only, not load-bearing) — left as-is. **§W's meaning could not be recovered**
      anywhere in this doc or the audit — dropped rather than carried forward bare (stated explicitly in place, not
      silently).
- [x] [DOC] P2. ✅ **Finding E — FIXED for both flagged instances 2026-07-23.** Track S's "Absorb
      `sports_canonical_migrated_odds_mistamped_footystats` + `sports_canonical_raw_truncated_rederive_destroys_corpus`"
      reworded to the literal action — and downgraded from HIGH once checked: the rederive-risk doc is
      `status:     resolved` with 1 real open todo (runbook correction) to merge; the footystats doc doesn't exist
      standalone, it's already Track C's venue-cleanup todo. Track V's "Absorb `sports_p2_history_apifootball...`"
      reworded to "execute the open residual work from archived `...`'s own todos."
- [x] [DOC] P2. ✅ **Finding F — FIXED 2026-07-23, with reasoning, not a blind tag.** The PURGE todo is deliberately
      **not** `[OPERATOR]`-tagged (unlike the K1/K2 GCS-delete, which is) — stated explicitly in place: GCS soft-delete
      gives a 7-day recovery window, making this reversible-for-a-week rather than the irreversible class
      `gcs-and-manifest-delete-safety-protocol.md` reserves for human-only sign-off.
- [x] [DOC] P2. ✅ **Finding G — FIXED for both named examples 2026-07-23**, plus 4 more todos gained a done-criterion
      along the way (the casing revert, the F1/F2 fix, the round-derivation residual, the dimension-group purge). T0/T1
      gate: "done when a T0-before-T1 violation actually raises in a test." Tick/MDPS pipeline-check: "done when the
      check fails on a real busy date if any leg's output is empty or shape-wrong." **Not exhaustive** — no full sweep
      of every remaining todo across Tracks H/K/D/X/S2 for a missing done-criterion was performed this pass.
- [ ] [REVIEW] P1. **Follow-up once the Track H/K/D/X/S2 background sweeps (Finding A + Finding C, dispatched
      2026-07-23) report back**: apply their findings the same way as above — fix directly if small and clear, or
      re-open a scoped todo here if not. Do not let the sweep's own output sit unconsumed.
- [ ] [REVIEW] P1. **Full finding-C sweep** — only 2 stale-checkbox instances were found+fixed (the cross-AG emitter
      todo, the 4,097-row finding). A second independent agent found these by spot-check, not an exhaustive pass —
      re-sweep the WHOLE doc for any other todo whose own body (or a later section) already shows it resolved, and flip
      it with evidence, so AO never re-investigates an already-solved problem.

**P0 (open, 6):** `sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md`,
`sports_cf8_available_at_backfill_regression_2026_07_13.md`, `sports_features_rerun_stopped_writing_2026_07_21.md`,
`sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`,
`sports_is_index_fixtures_job_direct_write_328k_row_cut_2026_07_15.md`,
`sports_is_manifest_eu_regression_overwrite_2026_06_29.md`,
`sports_is_odds_capture_code_incomplete_reversal_2026_06_27.md`, `sports_legacy_canonical_row_gap_2026_07_16.md`.

**P1 (open, 11):** `cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md`,
`dp_catalog_not_running_sports_prediction_2026_07_15.md`,
`sports_derived_features_per_league_layout_unread_by_ml_loader_2026_07_14.md`,
`sports_index_recency_masked_captured_atoms_2026_07_13.md`, `sports_legacy_duplicate_triage_2026_07_22.md`,
`sports_live_writer_instrument_type_casing_never_fixed_2026_07_22.md` (superseded by K1 completion above — worth a
formal status flip, not done here), `sports_manifest_read_staleness_budget_missing_2026_07_15.md`,
`sports_odds_stale_fixture_reinjection_2026_07_14.md`,
`sports_pre_floor_fixtures_orphan_misclassification_2026_07_22.md`,
`sports_shard_enumeration_cartesian_blowup_2026_07_20.md`,
`sports_weather_uac_layout_per_day_bare_vs_writer_per_day_per_league_2026_07_20.md`.

**P2 (open, 8):** `sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`,
`sports_golden_window_attempted_failed_remediation_2026_06_24.md`,
`sports_odds_feature_naming_four_way_mismatch_2026_07_21.md`,
`sports_odds_team_name_alias_gap_south_america_2026_07_09.md`,
`sports_phantom_audits_reference_not_marketdata_2026_07_14.md`,
`sports_t0_t1_dependency_gate_never_wired_2026_07_15.md`, `sports_trades_venue_fetch_failed_2026_07_15.md` (see the
2026-07-23 finding above — partially resolved by the api_football wipe), `sports_trades_attempted_failed_2026_07_23.md`
(today's DP_RUN_MOSTLY_EMPTY triage, resolved — metric artifact of the K1/K2 swap, not a regression).

**P3 (open, 3):** `sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md`,
`sports_reference_function_size_qg_regression_2026_07_16.md`,
`sports_source_mdps_instruments_service_not_leakage_2026_07_16.md`.
(`features_sports_deployment_ui_coverage_tab_and_registry_playbook_2026_07_21.md` resolved + archived 2026-07-24 — see
`/plans/archive/issues/features_sports_deployment_ui_coverage_tab_and_registry_playbook_2026_07_21.md`.)

**Recommended next item for a fresh session:** the dormant-pipeline investigation
(`sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md`) — it gates whether any of the honest-coverage
work above is measuring a live, growing dataset or a frozen one, and needs infra access this session didn't have (AWS
IAM, persistent-VM inspection).

- [ ] [DOC] P3. **Triaged against `/home/ubuntu/unified-trading-system-repos/sports_plan_changes.md` (2026-07-23) — a
      reference-only "AO-ready instruction-clarity model" rewrite of an earlier version of this closeout, built by a
      different session/agent, `status: draft` + `assigned_vm: NA` (never dispatched, not in `plans/active/`).**
      Verdict: it predates this session's interactive casing-revert ruling — its Track C still frames data_type/
      instrument_type as UPPER (the K1/K2 decision this closeout has since REVERTED to all-lower) — do not adopt that
      framing, this closeout is the more-current, more-canonical side on that specific point. It independently converges
      on nearly the same 6 defect classes Track Y above already fixed (first-line completeness, single-place ordering,
      resolved section-shorthand, literal-verb instructions, consistent delete-tagging, stated done-when) — treat that
      convergence as validation, not a reason to import its content. **One real structural technique worth adopting as
      its own follow-up (not done here, scope is ~150 todos across this whole doc)**: stable per-track todo IDs (`F-3`,
      `C-4`, `N-8`, …) so a `Prerequisite: F-3, F-4` note can name an exact todo instead of prose ("after the
      re-runs...") — this would make Finding B-class ordering issues structurally harder to reintroduce. Lower-value,
      higher-risk, not recommended: regrouping scattered Progress-Log narrative into new named tracks (its Track
      N/R23/T23) — would require moving already-correct, already-cited content with real risk of dropping evidence in
      transit, for a mostly-cosmetic gain.

## 2026-07-23 — re-triage of the full sports issue-doc index (6 parallel agents)

Every doc in the swept index above was individually re-verified against CURRENT code/data state (not just re-read) — 30
docs total, each check backed by a live grep/query/commit citation, not assumption. Result: **13 resolved** (fixes
shipped and verified working), **1 superseded** (a fix landed with the opposite disposition than the doc recommended,
tracked separately), **~15 confirmed still open and accurate**, **1 confirmed still open and getting worse than the last
recorded state**. Full per-doc verdicts are in each file's own `## RE-TRIAGE (2026-07-23)` section. SHAs:
`pm@bd88f337c`, `pm@d510c0938`, `pm@c864972b1`, `pm@1bda5148f`, `pm@2b5a3f623`, `pm@63c765a1c`.

**Two findings from the re-triage needed escalation — both dug into further the same day, one fully resolved, one
corrected to a properly-scoped code fix:**

- [ ] [DATA] P0. **`cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` — REOPENED 2026-07-24,
      round-2's "RESOLVED" claim below does not hold.** Root-caused precisely (round 2): the 07-20 "complete" claim
      fixed the raw-data-bucket bug (`mtds@5581dcf9`) but missed the MANIFEST-bucket's own copy of the same bug
      (`orchestrator/__init__.py::_resolve_manifest_bucket`, resolving once per RUN not per-venue), not fixed until
      `mtds@299ef540` (2026-07-22T02:01:44Z) — during that ~39.5h gap the manifest bug kept writing fresh bleed rows
      even though the raw data was already routing correctly. Confirmed zero bleed rows written after `299ef540` (writer
      bug fixed + holding) before remediating. Executed `market-tick-data-service@a7ff45f9`: CAS-safe ADD 5,056 + REMOVE
      11,727 across both manifests, snapshot-first, **VERIFY PASSED at the time** (0 remaining, 0 still missing).
      **RE-TRIAGE ROUND 3 (2026-07-24)**: a fresh live read of the SAME index found the **exact same 11,727 rows, exact
      same venue/date breakdown**, back in place — round-2's remediation has NOT held. Confirmed metadata-only (no
      physical objects found in the sports bucket) and ruled out the obvious stale-per-VM-shard hypothesis
      (`_index/per_vm/` holds only an unrelated 18KB seed file dated 2026-06-28). Root cause of the REVERSION is
      unconfirmed — working hypothesis is a consolidator rebuild path that re-merges a surface round-2's remediation
      never touched. **Do NOT re-flip this to resolved** — full detail + next-step investigation plan in the issue doc's
      own "RE-TRIAGE ROUND 3 (2026-07-24)" section. (Also carried as its own P0 todo, "clean the already-accumulated
      cross-AG prediction bleed rows," in the now-archived `sports_master_closeout_2026_07_21.md` — folded in here
      2026-07-24, no new content: this item's round-3 findings already supersede it.)
- [x] [DATA] P1. ✅ **`sports_index_recency_masked_captured_atoms_2026_07_13.md` — root cause CORRECTED, redeploy todo
      was targeting the WRONG job.** Traced the actual 04:06:54Z masking write via Cloud Run execution history instead
      of assuming: it's `uts-prod-instruments-service-sports-fixtures` (generic instruments-service batch capture,
      `--operation=instruments --mode=batch`), NOT `expected-universe-v2-sports` (which ran hours earlier, 01:30Z) — a
      completely different code path from where the `ba306543` oscillation guard lives. Redeploying
      `expected-universe-v2-sports` would have fixed nothing. Also checked whether the shipped reader-side tie-break
      neutralizes this — it doesn't, this masking is explicitly cross-dedup-key. Real fix needed: extend the guard to
      the batch-capture emission path (`instruments-service`, new P1 CODE todo in the issue doc) — genuine code work,
      correctly left for a fresh session rather than rushed here.

**Also found**: `sports_consolidated_closeout_2026_07_19.md`'s own item **O** (a stale claim from this doc's own
2026-07-19 authoring) was corrected in place above — OR-1 Option D WAS executed the same day, contrary to what was
recorded. And a near-duplicate doc outside this sweep,
`issues/instruments_service_codex_compliance_ceiling_drift_2026_07_20.md`, was found resolved by the same commit as
`sports_reference_function_size_qg_regression_2026_07_16.md` but never updated — annotated, not fully flipped (2 of its
3 sub-todos remain genuinely open).

## 2026-07-23 — full contradiction + confusion-risk reconciliation (interactive, 16 operator decisions)

A dedicated multi-pass audit (2 workflow passes across every related plan/issue/codex doc + direct code verification)
found this closeout had drifted into internal self-contradiction and had lost track of several live sibling plans. The
operator was walked through every point of conflict interactively and ruled on each — this section is the consolidated
record. **Per explicit operator instruction: everything below is DECIDED and being written into docs/ plans NOW; none of
the data-moving or code-shipping work has been EXECUTED yet** — that is deliberate, so a fresh agent (or a future
session) picks up a fully reconciled, non-contradictory plan rather than doing archaeology on which of two conflicting
SSOT claims is current.

**Decisions made (ruling → what it changed):**

1. **data_type casing** → ALL-LOWER for every sports data_type, reverting K1/K2's TRADES-to-UPPER migration. See
   Canonical target section + Track C's new revert todo.
2. **Stale "Operator decisions needed (blocking)" header** → deleted (was contradicted by the ANSWERED section 150 lines
   above it).
3. **4 fold-in plans never actually archived** → archive all 4 now, pulling their live content into this closeout first
   (`sports_manifest_canonicalisation_2026_06_01`, `sports_pipeline_to_100pct_golden_window_first_2026_06_27`,
   `sports_odds_exchange_fixed_fork_2026_07_18`, `sports_p2_history_apifootball_2015_to_present_2026_06_27`) — see the
   new todos this pulled in below.
4. **5 orphan plans with real overlap, never linked to this closeout** (corrected 2026-07-24 — was miscounted "6" here,
   already correctly "5" elsewhere in this doc, e.g. line ~606) → link all + file a reconciliation todo each
   (`sports_catalog_league_grain_only_scope_2026_07_08`, `sports_odds_bookmaker_coverage_enumeration_2026_06_20`,
   `sports_odds_feature_naming_canonicalization_2026_07_21`, `sports_p2_features_history_to_ml_ready_2026_06_27`,
   `sports_predictions_live_mode_activation_readiness_2026_07_21`) — see the new todos below.
5. **Track D's "9 docs banner-fixed" claim was inaccurate** → do the full body rewrites now, not more banners (6 docs:
   `sports-adapter-dependency-order.md`, `sports-scheduling-and-sharding.md`, `sports-fixtures-lifecycle.md`,
   `honest-absence-downstream-handling.md`, `sports-batch-live.md`, `pipeline-coverage-matrix.md`), see Track D.
6. **Honest-coverage UI denominator** → implement the registry-aware fix in `compute_coverage_for_bucket()` now (not
   just a doc caveat) — new Track H todo below. Sequenced AFTER the league_id migration (decision 7) since a
   registry-membership test can't be correct until that lands.
7. **League_id historical migration (214,842 rows)** → schedule the monitored prod-apply + human-only delete session now
   — see Track V, still the same P0, now explicitly scheduled rather than indefinitely deferred.
8. **Sports ODDS_API capture pipeline dormancy** → investigate now, get the AWS IAM access this session lacked — new
   Track H todo below, explicitly the single highest-priority NEXT action across this whole closeout.
9. **`sports_master_closeout_2026_07_21.md`'s summary-vs-supersedes self-contradiction** → formalize a real entry-point
   relationship field in the plan frontmatter schema rather than just rewording prose — new Track D/X todo below
   (touches `plans/PLAN_FORMAT.md`, may need a schema discussion, not a same-session mechanical fix).
10. **MDPS's 3 dead derived-odds products** → wire them up for real (not retire) — new Track H todo below, gated on
    confirming downstream demand first (features-service/strategy-service consumer check).
11. **CF-8 available_at fix** → schedule the maintenance window now, lift operator stop `BLK-d9137d48` — Track H.
12. **1,066,231-row manifest purge** → design + build the missing cross-object-CAS safety tooling now — new Track H todo
    below (harder blocker than league_id's pure scheduling gate — nothing to schedule until this exists).
13. **AvailableAtStampingError write-abort contract** → raise on all-NaT (fail loud), not skip-with-record — new Track H
    design todo below, to prevent a future CF-8-class silent regression.
14. **83,541 pre-floor FIXTURES_SCHEDULE/FIXTURES_OUTCOMES rows** → execute the wipe now (consistent with the
    already-established 2020-06-06 sports data floor policy) — new Track V todo below.
15. **MTDS live-odds fixture_id-blank collapse** → investigate + fix now, don't just re-check status — new Track O todo
    below.
16. **OR-1's 2 unfiled loose ends** (standings/teams season-2026 under historical `day=` partitions; unidentified junk
    `player_values` writer) → investigate both now — new Track S todo below.
17. **Sports live-mode prediction trading go/no-go** → GO, gated explicitly on confirming the cross-AG bleed fix
    (`mtds@a7ff45f9`, see the 2026-07-23 re-triage section above) is durable, not just verified-once — new todo on
    `sports_predictions_live_mode_activation_readiness_2026_07_21.md` (linked in decision 4 above).
18. **Odds-feature naming (BLK-a1ce4719's remaining field-name call)** → new deliberate naming, not adopted from any
    single existing convention, full data+manifest migration so every real consumer's need is met. Scheme + gap analysis
    recorded in `sports_odds_feature_naming_canonicalization_2026_07_21.md`'s Progress Log (2026-07-23).

**New evidence folded in during this pass (not from the original audit)**: a live "Distinct Values" read from the
deployment-ui's sports Instruments Service view showed 9/17 non-canonical venues, 16/16 (100%) non-canonical
instrument_types, 3/11 non-canonical data_types, and 3/3 (100%) non-canonical chains. Root-caused to 3 separate
asset_group-blind positional-parse bugs in `market-data-processing-service` (see Canonical target section + Track C's
new todos). **Target, stated explicitly for the first time**: by the end of this closeout, that Distinct Values panel
reads 0 non-canonical across all four axes for sports.
