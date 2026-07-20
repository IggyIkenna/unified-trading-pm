---
doc_type: plan
title: Sports consolidated close-out — canonical, honestly-covered, leakage-free, ML-ready (one pass through features)
summary: >-
  The single actionable plan that takes the sports asset_group all the way to ML-ready: canonical SSOT + naming, right
  buckets, codex migration, no-regression guards, honest-coverage backfill across instruments-service /
  market-tick-data-service / market-data-processing-service / features-service, smoke-test + speed enhancement, and zero
  leakage. Absorbs ~7 fold-in sports plans + ~17 issue docs (see the audit's reconciliation). Fed by
  sports_consolidated_audit_2026_07_19. Track-structured like defi_consolidated_closeout. LOCAL/human plan.
status: active
nature: process
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
tags: [sports, canonical, honest-coverage, data-completion, ml-readiness, leakage, codex, close-out]
related:
  [
    sports_consolidated_audit_2026_07_19.md,
    sports_features_layer_findings_sweep_2026_07_18.md,
    sports_legacy_bucket_cutover_2026_07_16.md,
    sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md,
    defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-07-19"
last_updated: "2026-07-19"
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 9.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
assigned_role: data_engineering
drift_direction: advance-code
---

# Sports consolidated close-out — one pass to canonical, honestly-covered, leakage-free, ML-ready

> **Read `sports_consolidated_audit_2026_07_19.md` first** — it is the measured evidence base (every claim here traces
> to a GCS/parquet/manifest measurement in that doc). This plan is the actionable projection: what to fix, in what
> order, to reach "everything sport-related is canonical with no SSOT confusion, backfills at honest-100% across all
> sources and downstream MDPS/features, no leakage, ready for ML training."

## Headline verdict — how sports differs from cefi/tradfi/defi

Sports is **light and mostly filled** (reference layer canonical, round work terminal), so — unlike the heavier AGs that
needed a separate `data_completion_*` plan — this goes **all the way through features in one plan**. What blocks
ML-ready is not bulk backfill; it is (1) one live data-correctness defect (now fixed, re-run pending), (2) a few
canonical-honesty gaps (manifest atom, cross-AG bleed, K-casing), and (3) the honest-coverage/leakage tail.

**Foundation gate**: the FEATURES corpus re-run (F-track) is the last thing before ML, and it must run AFTER the CANON
manifest-atom fix (C-track) and the ODDS-LEAK shard cleanup — else the re-run bakes in stale atoms again.

## Canonical target (the SSOT everything converges on)

- **data_type = UPPER everywhere** (operator K0-DECISION (b), 2026-07-18). Sports is the only AG that is UPPER; CF-7's
  UPPER→lower map is SUPERSEDED for sports. Reference layer already conformant; market-data-sports is the only mixed
  bucket.
- **Fixtures entity split**: `entity=fixtures_schedule` (schedule fields incl. `round`) + `entity=fixtures_outcomes`
  (scores/status), under `pipeline_mode=batch_api_football/`. The legacy bare `entity=fixtures/` is FROZEN (last real
  write 2026-05-23) and must not be read or written. **The manifest `data_type` must record the split entities, not the
  `"FIXTURES"` umbrella** (§ C1).
- **timeframe is its own column** — never baked into `data_type`. `odds_horizon_bucket_{15m,1h,4h,1d}` is a dead cohort.
- **Buckets** (via `resolve_bucket_name`, never string-interpolate): reference → `instruments-store-sports-prd`, odds →
  `market-data-tick-sports-prd` (the `market-data-sports-prd` name 404s — the real name carries a `tick-` infix),
  features → `features-sports-prd`.
- **Honest absence, never a placeholder**: `attempted_failed` is a real-failure signal — root-cause before any relabel
  (§ B2 precedent).

---

## Track F — FEATURES: the live data-correctness defect + the ML-ready re-run · P0 (FOUNDATION GATE)

- [x] [CODE] P0. ✅ §Z season_context fabrication FIXED — **features-service@c6eb1f38** (QG green). Gate derives
      matchday from `round`; `_competition_phase`/games_remaining honest `None` on NaN; 2 regression tests. The 8-VM
      re-run fleet writing the fabricated pattern was STOPPED.
- [~] [DATA] P0. **Clean corpus-wide `derived_features` re-run** (2019→present, replaces the stopped fleet) — bounded
  per-year SPOT chunks (the `--force` × SPOT preemption-replay hard rule: a preempted force-run restarts at day one, so
  chunk it), watchdog on a validated creation-time metric (whole-date filter, not an hour pattern — cf. codex async rule
  1a). **PREREQUISITE (measured 2026-07-19): the features-service GCS tarball must include the §Z fix before launching**
  — the tarball was STALE (`aa7ea0ff`, built 07:30Z, pre-fix); a naive relaunch would have REPEATED the corrupt run.
  Rebuilt via `create-code-tarballs.sh --include features-service` (all 5 repos verified clean@LDR first) → features
  tarball now `c6eb1f38`. **CORRECTION: this re-run does NOT depend on § C1** — C1 is instruments-service manifest
  bookkeeping; the re-run reads fixture PARQUETS (already correct via §Q/T/W round + §V split-read), so it is gated only
  on the §Z code fix + a fresh tarball (both done). 2024 pilot chunk launched; verify its shards show a real
  early/mid/late competition_phase spread before fanning out the remaining years. Verify via corpus re-scan (matchday
  non-null ≈ round non-null; phase NOT 100% 'late'). 2019 + 2020 initially failed to re-run — the SPOT VMs hit the
  `--force` × SPOT preemption-replay hazard WITHIN the year (log shows repeated restart at YYYY-01-01; never reached
  mid-year; exited 0 having covered ~48/366 of ~4000/2900 shards). **Per-YEAR chunking was not fine-grained enough
  against within-year preemption.** Fix: re-ran 2019+2020 **ON-DEMAND** (`--on-demand` FLAG — the `ON_DEMAND=true` ENV
  is overridden by the launcher's internal default, a foot-gun) so they can't be preempted. **⚠️ CORRECTION 2026-07-20 —
  the earlier "VERIFIED corpus-wide: 2021-2026 CLEAN" claim on this line was OVERSTATED and is RETRACTED.** It sampled
  days, and the sampled days were ones the re-run had rewritten. A creation-time census of all 124,554
  `derived_features` objects + a 250-object stratified content sample measured a **100% fabrication rate among ALL
  pre-fix objects (249/250)** — i.e. "pre-fix" means fabricated, not merely suspect — totalling **35,045 fabricated
  parquet objects**, of which **2,821 sit inside the supposedly-clean 2021-2026**. Two structural gaps: (a) this task's
  scope is "2019→present" but the corpus starts `day=2017-02-02`, so **2017+2018 (26,089 files — 2018 is the LARGEST
  year in the corpus) were never in scope**; (b) `--force` only overwrites days the run PRODUCES output for, so
  fabricated objects survive on days that yield nothing (observed: `day=2019-04-20`, passed at 12:42Z, still 100%
  `'late'`). Full evidence + required remediation:
  `issues/sports_derived_features_fabricated_corpus_scope_2026_07_20.md`. This todo is NOT done — see the three
  follow-ups below.
- [ ] [DATA] P0. **Re-run 2017 + 2018 `derived_features`** — never in this plan's "2019→present" scope, and measured
      100% fabricated (26,089 parquet objects; 2018 alone is 22,077, the largest year in the corpus). ON-DEMAND, same
      per-year chunking + `--force` as the 2019/2020 recovery.
- [ ] [DATA] P0. **PURGE the fabricated remainder — overwriting is provably insufficient.** After the re-runs, every
      `derived_features` parquet still carrying a PRE-`2026-07-19` GCS creation timestamp is fabricated by measurement
      and must be DELETED, not left to a re-run that never rewrites a day it produces no output for. Honest absence
      beats an invented `competition_phase` (`codex/02-data/honest-absence-downstream-handling.md`). Snapshot the delete
      list first; the bucket has GCS soft-delete (7-day recovery).
- [ ] [DATA] P0. **Re-verify by CENSUS, not sampling** — the terminal check is "zero pre-fix-dated `derived_features`
      objects remain", decidable from object metadata alone. Sampling is what produced the retracted CLEAN claim above.
- [ ] [DIAG] P1. `sfi_progressive_features` is corpus-empty (1 manifest row) despite a documented 2020→today window —
      find why the backfill never ran, then run it. Without it every HT/progressive-SFI ML feature is unavailable.
- [ ] [DIAG] P2. `is_promotion_relegation` is hardcoded `False` (dead) — wire it from the standings relegation-zone
      classification (`_compute_league_batch` already computes it) or formally retire it + its points_at_stake
      multiplier.
- [ ] [DIAG] P2. Settle whether `clv_*`/`odds_movement_*` all-null in odds_features is honest-absence or a gap (wider
      multi-date spot-check) before relying on them for ML.
- [ ] [DATA] P2. Purge the 4 dead dimension groups still inflating the features manifest (players/coaches/referees/
      rounds, 4,216 rows each) — the outstanding §A2 purge.

## Track C — CANON: data_type UPPER + venue/instrument_type + manifest atom · P0

- [ ] [CODE] P0. **C1 — migrate the fixtures manifest atom** from hardcoded `"FIXTURES"` to `FIXTURES_SCHEDULE`/
      `FIXTURES_OUTCOMES` across the 8 call sites (`sports_reference_fixtures.py:242,279`, `process_write.py`,
      `writers.py:219`, `catalogue.py:136`, `process_completeness.py`, `process_preflight.py`,
      `process_zero_records.py`, `sports_fixtures_daily_repoll.py`) so the manifest atom == the writer atom. Gates the
      F-track re-run.
- [ ] [CODE] P0. **K1 — emit UPPER at the LIVE writer**: fix `_build_sports_shard_path` (`venue_fetch.py:871-900`) + the
      sentinel row-key builders (`sentinels.py` v1:420-426, v2:305-311, skip-fan:180-197) to emit
      `DATA_TYPE=TRADES`/`INSTRUMENT_TYPE=ODDS`. This is the currently-running writer; must ship BEFORE K2.
- [ ] [DATA] P1. **K2 — migrate the historical lower-case rows UP** (only after K1). **SCOPE CORRECTED (contradiction
      sweep #9): the dominant lower-case data_type is `trades` = 1,806,553 rows (91.5% of the bucket), NOT the ~20k
      `odds`-family.** K1 already commits to fixing the live writer to emit `TRADES` — so K2 must migrate the historical
      `trades` rows too (the `odds`→`ODDS` (20,331) / `odds_movement`/`odds_snapshot` (4+4) / dead
      `odds_horizon_bucket_{15m,1h,4h,1d}` (1,337) family is the SMALL tail). Decide explicitly: either K2 migrates
      ~1.8M `trades`→`TRADES` (the real bucket-wide job, not "one bucket, small"), or state why `trades` is deferred
      relative to the `odds` family. CF-7's UPPER→lower map is superseded for sports.
- [ ] [CODE] P1. **F1/F2 — venue/instrument_type cleanup**: fix the footystats legacy bundle mislabel
      (`venue=ODDS_API`→`FOOTYSTATS`, 42,476 rows); clean the `instrument_type` pollution (110,759 blank + 56,048 None +
      bookmaker-name rows). Do NOT touch the deliberate `mdps_odds_horizon_bucket` `venue=ODDS_API` aggregate (124,294,
      reconciled 2026-07-14).
- [ ] [CODE] P1. **Promote the existing market vocabulary** (`ODDS_API_MARKET_TO_CANONICAL`, already UPPER on
      `market_key`) to the `instrument_type` axis — K1's "introduce a betting-market vocabulary" already exists, just on
      a different column. Reconcile `canonical_writer_shaping.py:218`'s "instrument_type IS 'odds'" claim first.
- [ ] [CODE] P2. **EXCHANGE_ODDS vs FIXED_ODDS fork** — absorb `sports_odds_exchange_fixed_fork_2026_07_18` (§F2
      dimension-pollution): separate exchange (Betfair) from fixed-odds bookmaker prices in the canonical dimensions.
- [ ] [REVIEW] P1. QG assertion: sports `data_type` ∈ the UAC **UPPER** sports vocabulary, `venue` ∉ {vendor names},
      `instrument_type` ∈ the declared sports vocabulary — so this class cannot silently return.

## Track S — STORE: bucket hygiene + legacy path elimination · P1

- [ ] [DATA] P1. Complete `sports_legacy_bucket_cutover_2026_07_16` T2.9 (MDT schema drift) + T2.10 (47,253 phantom
      `api_football×trades` rows) + its post-phase codex audit.
- [ ] [CODE] P2. Eliminate (or document) the legacy bare `entity=fixtures/` (no `pipeline_mode=`) write path still
      active today alongside the canonical split writer (5-league subset).
- [ ] [CLEANUP] P2. Snapshot-then-cull the dead `sports_reference_v2/by_date/` dual-layout (frozen 2026-04-20, no
      entities). Confirm no reader consumes it first.
- [ ] [DATA] P1. Absorb `sports_canonical_migrated_odds_mistamped_footystats` +
      `sports_canonical_raw_truncated_rederive_destroys_corpus` (HIGH — corpus-destroying rederive risk; guard before
      any rederive).

## Track E — ENTITY-SPLIT: repoint every remaining stale consumer · P1 (sports-specific, no defi analog)

- [ ] [CODE] P1. Repoint the remaining stale `entity=fixtures` consumers (sweep §R's ~9-file list:
      `sports_dependency.py`, `sports_fixtures_daily_repoll.py`, `backfill_weather.py:154`,
      `backfill_sports_fixture_stats_manifest.py:91`, `rescan_sports_fixtures_canonical.py:328,452`,
      `enumerate_expected_universe.py:1902`, `migrate_sports_per_league.py`,
      `reconcile_sports_blank_empty_reason_2026_06_24.py`) to `fixtures_schedule` (+`fixtures_outcomes` where scores are
      needed).
- [ ] [CODE] P1. Wire the T0/T1 dependency gate for real (`sports_t0_t1_dependency_gate_never_wired_2026_07_15` — the
      pre-flight only fires `if date is not None` and no caller passes it, so the fail-loud boundary is unreachable).

## Track O — ODDS-LEAK: post-kickoff contamination + the B2 dead-zone · P1

- [x] [DATA] P0. ✅ **RETENTION CLIFF DISSOLVED — the restore was never the right recovery, and no deadline applies.**
      Operator approved the controlled-window restore (2026-07-20); executing it measured-first showed the premise was
      **wrong on two counts**, so it was NOT run. **(1) The soft-deleted generation does not hold the true values.** The
      v9 clobber ran FOUR times, each rebuild re-stamping the previous stamp — measured across the live index + 8
      `_index/snapshots/` objects: | index state | `attempted_at` window (BETFAIR/MATCHBOOK/PINNACLE) | verdict | | ---
      | --- | --- | | `pre_migration_v9_2026-07-12_availability_index.parquet` (07-12T22:19Z) | 2026-06-21 14:23:10 →
      22:41:51 (29,922s) | ✅ TRUE | | `pre_migration_v9_2026-07-13…` / `pre_force_consolidate_…06_36` | 2026-07-12
      23:17:54 → 23:18:04 (10s) | clobber #1 | | `pre_cf8_backfill_20260713T210725Z` | 2026-07-13 06:16:02 → 06:16:12
      (10s) | clobber #2 | | `pre_cf8_backfill_retry_20260713T233900Z` | 2026-07-13 21:23:42 → 21:23:49 (7s) | clobber
      #3 | | LIVE `availability_index.parquet` | 2026-07-13 23:56:41 → 23:56:48 (7s) | clobber #4 | The soft-deleted
      generation `#1783986822147154` was created 2026-07-13T23:53:42Z — **between clobber #3 and #4** — so restoring it
      would have yielded the 21:23 window: another clobbered value mistaken for the truth. **(2) The true values need no
      restore at all.** They survive in `_index/snapshots/pre_migration_v9_2026-07-12_availability_index.parquet` — an
      ordinary LIVE object (112,278 triplet rows, 8.3h spread), no soft-delete, no retention deadline, readable with a
      plain `cp`. **Also measured**: pausing the consolidator cron would have fired an ERROR-level page —
      `consolidator_liveness.py` has an explicit `REASON_SCHEDULER_PAUSED` branch ("deterministically dead, will NOT
      self-recover") on a `*/2` watchdog, wired to PagerDuty/Telegram. The approved op would have paged an away
      operator, risked a live 5.3M-row index, and recovered nothing. Evidence: `scratchpad/verify_preclobber.py`,
      `scratchpad/ladder.py`.
- [ ] [DATA] P1. **Repair `attempted_at` on the 112,277 rows from the named pre-clobber snapshot** (source above).
      DELIBERATELY NOT done unsupervised: the write races the same every-60s consolidator, and with the cliff gone there
      is no longer any reason to take that risk without a human watching. Do it in a normal window: verify whether the
      consolidator carries forward existing index rows (it merges per-VM shards; these rows have no new shards) — if it
      does, the edit persists and no pause is needed at all.
- [ ] [DATA] P0. Run `reprocess_sports_odds.py --force` for 2025-12-18/24/31 through the REAL script so the manifest
      coarse row flips off the stale `captured` (from the legacy-path leak) to `attempted_failed` (18,31) /
      `empty_confirmed` (24) — the B2 diagnosis was never persisted.
- [ ] [DATA] P1. Purge/backup-delete the 27 leaked legacy-path (no `pipeline_mode=`) T-0 shards for 2025-12-18/24/31
      (100% post-kickoff) — confirm no live reader consumes the unprefixed path first (if one does, that reader leaks
      today).
- [ ] [DIAG] P1. Root-cause the 112,277 `attempted_failed` rows confined to exactly BETFAIR/MATCHBOOK/PINNACLE (all 6
      years) — likely `_SNAPSHOT_VENUES` CLV completeness, not primary capture. Do NOT relabel without root-cause.
- [ ] [DIAG] P1. Locate the emitter of the 139,620 `venue=ODDS_API, source=api_football, empty_confirmed` rows (not
      `_emit_sports_v1/v2_sentinels`) before folding into K2.
- [ ] [DIAG] P2. Corpus-wide scan for other low-fixture dates whose only in-window odds fall in the T-12h↔T-24h
      615-minute dead-zone; consider adding a T-18h horizon or widening the T-24h staleness cap; investigate why the
      multi-shot `TIER_1_OFFSETS` loop apparently didn't run on the quiet 2025-12 days (only 1 fetch_utc observed).
- [ ] [DATA] P2. Purge the 1,337 dead `odds_horizon_bucket_{15m,1h,4h,1d}` manifest rows.

## Track H — HONEST-COVERAGE: manifest honesty + denominators · P1

- [ ] [DIAG] P1. Why do `reason`/`error_code`/`empty_reason`/`classified_error` read back blank for the sports odds
      manifest (schema gap or C5-class silent-empty) — blocks root-causing § O findings.
- [ ] [DIAG] P2. Confirm sports genuinely never emits `expected_unattempted` in the odds manifest (0 of 1.97M) by
      design, or fix the miscoercion into `empty_confirmed`.
- [ ] [DATA] P1. Merge `sports_manifest_read_staleness_budget_missing_2026_07_15` into sweep §J's
      `AG_STALENESS_BUDGET_SEC["sports"]` fix (same defect, two docs).
- [ ] [REVIEW] P2. Honest-coverage atom regrade to per-calculator grain (sweep §C3, operator-decided) + league_id
      namespace reconciliation (§C2) + `fixture_stats` 708-failure root-cause (§C6).

## Track V — COVERAGE: backfill to honest-100% · P1 (operator-gated where noted)

- [ ] [DATA] P1. Round-derivation residual: run the retargeted backfill for the reachable in-window pairs already scoped
      (sweep §T/§W terminal state); the cup-vs-league classification is resolved (they are blank-round leagues,
      fetchable).
- [ ] [OPERATOR] P1. **§U decision** — 489 in-window (league,season) pairs / 10,869 rows in leagues ABSENT from the UAC
      registry: extend the registry or stop capturing. BLOCKED-OPERATOR-DECISION. "Backfilled 100%" can't be asserted
      until settled.
- [ ] [OPERATOR] P2. **§T decision** — pre-2019 blank-round rows (122,864) are outside the stated 2019→2026 window:
      confirm whether 2013–2018 is in scope. BLOCKED-OPERATOR-DECISION.
- [ ] [DATA] P1. Absorb `sports_p2_history_apifootball_2015_to_present` residuals + the 94-league enrichment backfill
      from `sports_canonical_universe_and_apifootball_reference_expansion`.
- [ ] [OPS] P2. Re-roll `build_instrument_catalogue.py --asset-group sports --since 2019-01-01` to pick up the §T/§U/§W
      +26,894 round rows (catalogue snapshot predates them).
- [ ] [CODE] P2. Upgrade the catalogue `player` grain from `entity=injuries` (injured-only) to `entity=fixture_lineups`
      (full roster, now carries 100% player/coach identity).

## Track K — SMOKE + SPEED + right-days · P1

- [x] [CODE] P0. ✅ CONTENT assertion shipped — **features-service@84cb4613 + @0ae9f460**.
      `_verify_sports_feature_content()` asserts `matchday` populated on numbered rounds, `competition_phase` not
      single-valued (§Z), and `round_name` / `coach_id` not 100% null (§V, checked first so it fails on its own).
      **@0ae9f460 also fixed a path bug in my own @84cb4613**: the layout is `day=<D>/league=<N>/feature_group=<G>/` —
      the league segment sits BETWEEN day and feature_group, so the original `day=<D>/feature_group=<G>/` prefix matched
      nothing and the check passed vacuously. Measured against the live bucket.
- [x] [CODE] P1. ✅ `SPORTS_SMOKE_DATES` pinned — **features-service@84cb4613 + @0ae9f460** (busy `2025-12-20` / thin
      `2025-12-24` / known_buggy_odds `2025-12-18` / known_buggy_fixtures `2024-03-09`; league-shard counts measured
      2026-07-19). @0ae9f460 added the enforcement half: for SPORTS, `empty_confirmed` PASSes only on the pinned thin
      date — a busy slate returning empty is now a FAIL.
- [ ] [CODE] P1. Promote the existing golden window (2025-09-01…11-30) to a shared "right days" SSOT module both smoke
      tests and backfill launches import — the "speed / right days" pillar.
- [ ] [CODE] P1. Build a sports pipeline-check for the tick/MDPS middle leg (none exists) covering IS→tick→MDPS→features
      with CONTENT assertions, not just presence.

## Track D — CODEX: doc alignment · P1

- [x] [DOC] P1. ✅ CORRECTION BANNERS added to all 9 drifted codex docs (PM, this commit) — canonical facts stated at
      the top (split entity, UPPER data_type per K0-(b), pipeline_mode segment, unreachable T0/T1 gate, deleted
      scrapers, SUPERSEDED integration-plan, dead sports_reference_v2). Full body rewrites are a deliberate follow-up;
      the banners stop the drift from misleading a reader NOW. Remaining: rewrite `sports-adapter-dependency-order.md`
      (repoint to split entities; wire the T0/T1 gate note) + `sports-data-types-catalog.md` (UPPER per K0-(b); F3
      timeframe) + `sports-gcs-path-ssot.md` (pipeline_mode + split entity rows).
- [ ] [DOC] P2. SUPERSEDED banner on `sports-integration-plan.md`; retire the deleted-scrapers §3 in
      `sports-live-odds-connectivity.md`; split-note `sports-scheduling-and-sharding.md`/`sports-fixtures-lifecycle.md`/
      `sports-batch-live.md`/`sports-data-source-coverage-matrix.md`; fix the 5 broken `related:` paths in
      `sports_master.md`.

## Track X — CLEANUP + plan reconciliation · P2

- [x] [SCRIPT] P2. ✅ Flipped 10 sports issue docs `open` → `resolved` (PM@b659c768d) — every one re-verified as 0 open
      todos / >0 done / citing a real commit, with `resolved_by` populated from the cited `<repo>@<sha>`. **Zero
      resolved-but-open sports issue docs remain.** (The sweep's "~30" was the estimate; the measured set with genuinely
      zero remaining todos is 10 — the rest still have open items and are correctly left open.) ~~Flip
      `status: resolved` on the ~30 fully-checked-but-open sports issue docs~~ (list in the audit's reconciliation) —
      pure hygiene.
- [ ] [PLAN] P1. Archive the fold-in plans as superseded-by this closeout
      (`sports_manifest_canonicalisation_2026_06_01`, `sports_pipeline_to_100pct_golden_window_first`) once their live
      items land here; keep the 2 near-done KEEP-ACTIVE plans standalone.
- [ ] [CLEANUP] P3. Drop the frozen 2018-2020 `markets`/`outcomes`/`settlements`/`arbitrage_opportunity` scaffolding;
      correct `SPORTS_INSTRUMENTS.md` stale "Known gaps" (lineups player-id strip claim is false); junk-symbol guard for
      non-ASCII fixtures (sweep §D).

---

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
7. **`sports-data-types-catalog.md` still documents lower-case sports data_types** — contradicts K0-(b). Exact quote
   captured. (CODEX.)
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
- **C** — `sports_odds_ownership_registry_split_brain`: DEFERRED PURGE of 127,018 bogus `api_football×ODDS` rows + "did
  the re-seed stop" verify. → CANON/ODDS-LEAK.
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
- **O** — `sports_legacy_canonical_row_gap` OR-1 Option D (player_stats-only union + fixture_events re-fetch) never
  executed + 3 unfiled loose ends (canonical player_stats 2x dup; standings/teams writing 2026 live under historical
  `day=`; 640-row cartesian player_values). → STORE.

### Duplicate/merge + status-flip recommendations

- Merge `sports_manifest_read_staleness_budget_missing` → sweep §J. Merge `sports_trades_venue_fetch_failed` → the
  112,277 item. Flip `sports_golden_window_attempted_failed_remediation` +
  `sports_is_odds_capture_code_incomplete_reversal` → resolved, pointing at `sports_odds_ownership_registry_split_brain`
  (terminal). **~20+ issue docs are shipped-in-body but still `status: open`** — the Track X status-flip sweep should
  cover the full list, not a sample.

## Cross-AG finding (belongs to a prediction/tick close-out, tracked here for visibility)

- [ ] [DIAG] P1. **4,097 live `asset_group="prediction"` rows (+2 cefi/defi) physically in the sports bucket manifest**
      (Kalshi/Polymarket, `service=market-tick-data-service`, dates 2026-06-26…07-18). Two write paths ruled out; next:
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
4. **K2 casing → MIGRATE ALL ~1.8M `trades` → `TRADES`.** Full canonical consistency; the bucket ends UPPER everywhere
   per K0-(b). This supersedes the original "~20,339 rows, one bucket" scoping (which wrongly excluded `trades` = 91.5%
   of the bucket). **K1 (live writer emits UPPER) must ship BEFORE K2** or the migration re-dirties on the next write.

### Newly-actionable todos from these decisions

- [ ] [DIAG] P1. Root-cause the cross-AG emitter (decision 1), then purge. **MEASURED 2026-07-20 — it is LIVE and
      GROWING, and larger than the audit said**: 4,097 (audit, 07-19) → **6,597 now**, +2,500 added TODAY alone (07-17:
      1,756 · 07-19: 2,341 · 07-20: 2,500, newest `written_at` 00:54:58Z). So a DAILY job is still writing. Fingerprint
      (from a direct read of `instruments-store-sports-prd/_index/availability_index.parquet`):
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
- [ ] [DATA] P0. **Migrate the 214,842 historical non-canonical manifest rows.** The manifest carries NO numeric id and
      its only other provenance column is `venue` (a bookmaker), so the **75,432 rows on an ambiguous name cannot be
      resolved from the manifest alone**. The underlying parquet CAN resolve them: `home_team`/`away_team` are populated
      and colliding leagues have disjoint squads (verified — `CHAMPIONSHIP`→Barnsley/Fulham = ENG,
      `PRIMERA_DIVISION`→San Lorenzo/Vélez = ARG, `SUPER_LEAGUE`→Young Boys/Zürich = SWISS). Map the 139,410 unambiguous
      rows by name; resolve the ambiguous ones per-shard by team set, leaving undecidable shards UNTOUCHED. **Note
      `league_id=` is a live GCS partition segment** — this is a RELOCATION, not a manifest rewrite. Snapshot first.
- [ ] [CODE] P1. Apply the same fix to the instruments-service per-fixture path — `sports_reference_fixtures.py:224-229`
      always takes the `fx.league.league_id` branch, making the numeric-id `elif` dead code, and `build_league_id()`
      falls back to a bare slug when `country` is empty. Live leakage already on disk:
      `.../entity=injuries/league=235/`.
- [ ] [DATA] P2. Dispose of the genuinely-out-of-universe rows (decision 2): exclude from the denominator; purge only
      once confirmed. **STILL BLOCKED on the historical migration above** — until the 214,842 raw-named rows are
      canonicalised, a registry-membership test on the symbolic `league_id` still classifies Premier League / La Liga /
      the Championship as non-registry, and the purge would DELETE core trading data. Snapshot before any delete.
- [ ] [DOC] P3. Document pre-2019 (2013–2018) as an intentional, explained exclusion (decision 3) in the audit's gap
      table so the remaining-blanks arithmetic reads clean.
- [ ] [DATA] P1. K2 scope is now ALL lower-case rows incl. ~1.8M `trades` (decision 4) — gated on K1 shipping first.

## Operator decisions needed (blocking)

- **§U** registry-absent leagues (10,869 rows) · **§T** pre-2019 scope (122,864 rows) · **§O** the two
  `attempted_failed`/third-sentinel diagnoses before any relabel.

## Codex SSOTs (read before touching a track)

`codex/02-data/sports-gcs-path-ssot.md`, `…/sports-data-types-catalog.md`, `…/sports-data-source-coverage-matrix.md`,
`…/sports-adapter-dependency-order.md`, `…/availability-manifest-and-data-status.md`,
`…/honest-absence-downstream-handling.md`, `…/pipeline-mode-partition.md`, `codex/04-architecture/sports-batch-live.md`,
`codex/05-infrastructure/spot-vms-for-backfill.md`, `codex/12-agent-workflow/async-wait-and-poll-discipline.md` (rule
1a). Plan↔codex drift is review-blocking.

## Progress Log

- 2026-07-19 — Plan authored from the 6-agent audit. §Z (Track F P0) already FIXED (features-service@c6eb1f38); the
  writing fleet was stopped; corpus re-run pending behind the C1 manifest-atom fix. All other tracks open.
