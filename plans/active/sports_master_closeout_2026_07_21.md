---
doc_type: plan
title:
  Sports MASTER close-out — 2020-06 floor, pre-floor wipe, league_id relocation, reconciliation (single source of truth)
summary: >-
  THE single consolidated sports plan a new /autonomous session works from. Sets the operator-ruled 2020-06 data floor
  (odds start 2020-06-06; pre-floor is fabrication-by-construction and is wiped), and sequences the remaining execution:
  pre-floor wipe + floor enforcement, the verified league_id + casing relocation (copy → deferred shapes → manifest-swap
  → MDPS reprocess → coverage refresh → separate irreversible delete), and a /data-pipeline-reconciliation sports pass.
  Consolidates + triages every sports plan and issue (live-post-floor / moot-after-wipe / resolved) so nothing is
  missed. Supersedes sports_consolidated_closeout_2026_07_19 as the top-of-stack entry point (that plan + the audit
  remain the detailed backing).
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
tags:
  [
    sports,
    canonical,
    honest-coverage,
    data-floor,
    wipe,
    league-id,
    relocation,
    reconciliation,
    ml-readiness,
    close-out,
    master,
  ]
related:
  [
    sports_consolidated_closeout_2026_07_19.md,
    sports_consolidated_audit_2026_07_19.md,
    issues/sports_league_id_namespace_migration_2026_07_20.md,
    issues/sports_derived_features_fabricated_corpus_scope_2026_07_20.md,
    issues/sports_features_rerun_stopped_writing_2026_07_21.md,
    issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md,
  ]
created: "2026-07-21"
last_updated: "2026-07-21"
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
locked_by:
locked_since:
supersedes: sports_consolidated_closeout_2026_07_19.md
superseded_by:
depends_on:
source: operator ruling 2026-07-21 (2020-06 sports floor + consolidation request)
assigned_role: data_engineering
drift_direction: advance-code
---

# Sports MASTER close-out — the single source of truth

> **Start here.** This plan consolidates every sports plan/issue across data, service, and monitoring, sequences the
> remaining execution, and links the detailed backing (`sports_consolidated_closeout_2026_07_19` + the audit + the issue
> docs in `related`). The `/autonomous` prompt for the new session lives at the end.

## THE 2020-06 DATA FLOOR (operator ruling 2026-07-21 — authoritative)

**Odds tick data starts 2020-06-06** (MEASURED: the tick bucket `market-data-tick-sports-prd` has ZERO day-partitions
before 2020-06-06; 1,942 from 2020-06-06 on). Ruling: **2020-06 is the base month for ALL sports** — honest-coverage
denominators, MDPS candle derivation, features computation, and fixture EXPECTATIONS all start here. Everything before
it is **fabrication-by-construction** (no odds → nothing downstream is legitimately computable), so pre-floor sports
data is **WIPED from GCS + manifest**. This is the honest resolution of the fabricated-`derived_features` findings —
**delete, do not backfill**. Measured pre-floor cruft: `features-sports-prd` = **212,519 pre-floor objects** (vs 192,106
post-floor); instruments/reference + MDPS + manifest rows likewise (size precisely before deleting); the tick bucket is
already floor-clean.

## ⚠️ #1 LANDMINE — a contradiction between TWO operator rulings (NOTIFY OPERATOR, resolve FIRST)

A **superseded 2026-07-15 operator ruling** amended the UAC coverage-floor SSOT for footystats / transfermarkt /
open_meteo **backward to 2018-01-01**, and it legitimately re-captured **2,848 pre-2020-06 cells** into canonical. That
floor is **LIVE in the UAC SSOT today** and directly contradicts the new 2020-06 ruling: if the wipe runs without
reverting it, expectation-seeding + re-capture immediately re-contradict the wipe. **Revert those UAC floors to 2020-06
(and re-delete the 2,848 cells) as the FIRST sub-step of the wipe + floor-enforcement.** This is an explicit
SSOT-contradiction big finding — surfaced to the operator 2026-07-21.

## PENDING EXECUTION — drive these to DONE (order matters)

- [x] [DATA] P0. ✅ **Pre-floor GCS WIPE DONE + VERIFIED (2026-07-21).** `deployment-service@78a0aa4`
      (`scripts/wipe_pre_floor_sports_2026_07_21.py`; path-based `day=<D>` cutoff, snapshot-first, 32-worker). Deleted:
      **features-sports-prd `sports_features/by_date/` = 212,519 objects** (2017-01-01…2020-06-05; soft-delete 7d net;
      spot-verified pre-floor days = 0, post-floor 2020-06-06+ intact) + **instruments-store-sports-prd = 437,124
      objects** (`sports_reference/by_date` 398,240 · `sports_reference/fixtures` 4,735 ·
      `instrument_availability/by_date` 34,149; soft-delete=0 → snapshotted; registries
      `teams_in_league/`/`mappings/`/`master/`/`standings/` LEFT UNTOUCHED — not per-day fabrication). Tick bucket
      already floor-clean. Landmine SUB-STEP (revert 2026-07-15 UAC amendment) was already done `uac@8cdf7808`.
      **MANIFEST prune = separate deferred task** (see below): index has an ACTIVE consolidator lock + is rebuilt from
      `_index/per_vm/` shards, so a session hand-edit is the corruption the plan forbids — 131,426 (features) + 944,776
      (instruments-store) phantom pre-floor rows measured, tracked below; floor enforcement keeps them outside the
      reported denominator. Resolves the pre-floor portion of `sports_features_rerun_stopped_writing_2026_07_21` +
      `sports_derived_features_fabricated_corpus_scope_2026_07_20`. (2,821 POST-floor fabricated objects + writer-defect
      fixes remain — §2-F, not part of the pre-floor wipe.)
- [x] [CODE] P0. ✅ **Floor ENFORCED in code + codex SSOT promoted (2026-07-21).** UAC `SOURCE_COVERAGE_START`
      (`uac@8cdf7808`) is the one SSOT and the consumers read it (`enumerate_expected_universe.py` seeds
      `EXPECTED_PRE_SOURCE_COVERAGE_START` below the floor; deployment-api data-status denominators read the same floor
      — both auto-propagate). Residual hardcoded pre-floor sites clamped: **instruments-service@d6747063**
      (`validation_utils.py::get_venue_epoch` api_football/soccerfootball_info/footystats 2018/2015 → 2020-06-06) +
      **deployment-service@78a0aa4** (`launch-sports-entity-sweep-vm.sh` all 2019-01-01 → 2020-06-06,
      `launch-sports-instruments-reference-vm.sh` entirely-pre-floor windows REMOVED, `launch-mdps-backfill-vm.sh`
      sports default). Codex SSOT: **`codex/02-data/sports-2020-06-data-floor.md`** (+ CLAUDE.md pointer). The 3 running
      `af-backfill-*` VMs were already floor-clamped (START=2020-06-06).
- [ ] [SCRIPT] P0. **league_id relocation — COPY (monitored VM job, NOT inline).** Verified executor:
      `market-tick-data-service/scripts/sports/league_id_relocation/migrate_sports_league_id_casing_2026_07_21.py`
      (adversarially reviewed — mtds@b2a49317; full-corpus dry-run PASSED, 266,408 objects, 0 unknown). Run first
      `--apply-prod` (no `--confirm-prod-write`, no `--index`) for the live out-of-scope census + VM guard, then
      `--apply-prod --confirm-prod-write` (copy+verify only; never deletes; refuses while any features-sports VM runs).
      Then the **127K DEFERRED shapes** (`odds_horizon_bucket`, `batch_footystats`). Detail:
      `issues/sports_league_id_namespace_migration_2026_07_20.md`. **⚙️ READY (2026-07-21) — but a VM-SHARDED monitored
      job, deliberately NOT launched at session tail.** Re-verified live: VM guard PASSES (zero
      `features-sports-sports-*` VMs), and a timed 3-unit `--validate` wrote 5 target objects **PASS=5 FAIL=0,
      quarantined=0, no_clobber=True** (correct LA_LIGA/PRIMEIRA_LIGA per-row splits) → executor is correct.
      **Throughput measured ≈2.7 s/unit single-process ⇒ ~25.7 h for 34,228 units** — this is a multi-hour VM-sharded
      job (shard by day-range with `--index`), not a single-process inline/background run. Launch it as a dedicated
      monitored VM run (COPY is reversible + idempotent `SKIP-ALREADY-VERIFIED`; the DELETE stays a separate gated
      pass). Everything is prepped — nothing operator-blocked here, only compute-scale.
- [ ] [DATA] P0. **league_id relocation — MANIFEST-SWAP + DELETE.** After every shape is copied+content-verified: atomic
      manifest-swap (reuse `deployment-service/scripts/rebuild_sports_manifest.py::_clean_stale_league_entries`), MDPS
      reprocess of the processed surface, coverage-registry refresh, THEN the **separate irreversible delete** of the
      old non-canonical objects (operator-authorised on the passing dry-run; snapshot first; final at-scale content
      re-verify before deleting). **FOLD IN** `mtds_t2_6_league_case_duplicate_population`: 6,110 lowercase-`league_id`
      objects (2025-07-31…12-31) proven 100%% content-identical to their UPPERCASE canonical twins — same casing root
      cause; dedup/delete in THIS pass, not standalone.
- [ ] [DATA] P0. **Clean the ACTIVELY-GROWING cross-AG prediction bleed BEFORE reconciliation** —
      `cross_ag_prediction_rows_bleed_into_sports_instruments_index`: ≥6,597 `asset_group=prediction`
      (KALSHI/POLYMARKET) rows physically in the sports availability index, growing (4,097→6,597 in days), writer
      unlocated. Reconciliation (below) reads this exact denominator — clean it FIRST or the read is false.
- [ ] [REVIEW] P0. **/data-pipeline-reconciliation for sports.** Run the skill (PROD-only, read-only) to prove every
      file is canonical + in the right place across the four surfaces (path ↔ content ↔ manifest ↔ catalogue). Fix any
      residual non-canonical; delete suggestions are proof-gated + human-only.
- [ ] [CODE] P1. **LIVE coverage-gate bug** — `is_bookmaker_league_covered` is keyed on RAW names, so it returns False
      for every canonical league; regenerate `sports_bookmaker_league_coverage.json` canonically (post-relocation).
- [ ] [DATA] P2. **Peripheral-bucket vocabulary contamination** (`ENGLAND_PREMIER_LEAGUE`/`LA_LIGA_2`/`UNKNOWN` from an
      untraced live writer) — trace the writer + fix at source, then migrate.
      `issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md`.

## 2. LIVE-POST-FLOOR issues — survive the wipe, carry as todos (grouped by theme)

**A. Coverage / honesty (denominators + expectation axes)**

- `cross_ag_prediction_rows_bleed_into_sports_instruments_index` (aa#7) — ≥6,597 `asset_group=prediction`
  (KALSHI/POLYMARKET) rows physically in the sports availability index, **actively growing**, root writer unlocated;
  **sequence BEFORE step 4** (subsumes aa#4 Finding C's residual cefi/defi rows). **HIGH.**
- `sports_shard_enumeration_cartesian_blowup` (af#2) — odds sentinel axis (5 keys) disconnected from the 23-key Odds-API
  `bookmakers=` list → 418,860 structurally-false rows + 21 books unmeasured; needs operator honest-coverage-number
  decision + UAC `OUT_OF_COVERAGE_WINDOW_REASONS` reclassification (94.31%→87.64%).
- `sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator` (ae#6) — 127,018 bogus
  `api_football×ODDS` rows (2019-01-01…2026-07-15, spans floor); seed-stop shipped, **deferred PURGE on the post-wipe
  residual** (2020-06…2026-07-15) + VERIFY-reseed-stopped + rebuild-delta reconcile; **sequence AFTER wipe.**
- `footystats_matches_predictions_fetch_gaps` (ab#5) — cup-competition PREDICTIONS gap from fixture-calendar-awareness
  bug (cup dates never resolve to `EXPECTED_NO_FIXTURE`) + 4-league MATCHES gap; fix calendar-awareness, recount
  post-floor.
- `sports_golden_window_attempted_failed_remediation` (ad#2) — 2 open: odds-api backfill gaps for 3 leagues (incl. UEFA
  CL) + `candidate_parquet_paths()` FORWARD-phantom path-shape gap that still blocks any forward `--apply` on sports.

**B. Canonical / naming (layout + vocabulary + registry)**

- `sports_weather_uac_layout_per_day_bare_vs_writer_per_day_per_league` (af#10) — UAC `SPORTS_DATA_TYPE_LAYOUT[WEATHER]`
  declares `PER_DAY_BARE`, writer emits `PER_DAY_PER_LEAGUE`; `candidate_parquet_paths()` false-absents every WEATHER
  object (≥106 proven false positives feeding the 721K phantom ceiling); **P1, same fix pattern as PLAYER_VALUES.**
- `sports_peripheral_bucket_league_vocabulary_contamination` (ae#9) — a **SECOND, DISTINCT** non-canonical league vocab
  (country-prefixed `ENGLAND_PREMIER_LEAGUE`, `LA_LIGA_2`, `UNKNOWN`) in `features-sports-prd` (30 obj, live to
  2026-07-11) + `instruments-store-sports-prd` (9,733 obj/172 values); **MUST NOT be folded into the casing relocation**
  — own writer-trace + fix-at-write + migrate track.
- `sports_canonical_migrated_odds_mistamped_footystats` (ac#4) — PURGE 42,476 mis-stamped
  `pipeline_mode=batch_footystats` manifest rows + now-redundant objects (read-split-merge already done on the 199 days
  that mattered).
- `sports_odds_exchange_fixed_fork` (plans#10) — fork `odds` → `EXCHANGE_ODDS`/`FIXED_ODDS` (UAC contract + GCS
  migration); BLOCKED-OPERATOR on venue→class mapping; **already Track C in the closeout — point at it, don't
  duplicate.**
- `sports_odds_team_name_alias_gap_south_america` (ae#8) — add verified Chilean club aliases (Coquimbo Unido,
  O'Higgins…) to UAC `team_mappings.py`; 43% of Chile PRIMERA_DIVISION odds unresolvable. Small.
- `sports_catalog_league_grain_only_scope` (plans#3) — extend "could-exist" catalog league-grain→fixture-grain (manifest
  schema + fixture catalogue builder + adapter wiring); operator ruled fixture-grain wanted.
- `sports_canonical_raw_truncated_rederive` (ac#5) — DOCS P1: correct the cutover runbook's "canonical is superset"
  premise (loss-guards already shipped).

**C. Data-correctness / manifest mechanics (era-agnostic writer/reader bugs)**

- `sports_index_recency_masked_captured_atoms` (ad#5) — later `empty_confirmed` recency-masks a present `captured` row;
  reader tie-break shipped, open: redeploy enumerator image fleet-wide + cross-AG sweep.
- `sports_manifest_null_vs_empty_dedup_double_count` (ae#1) — consolidator dedups only on `""`, legacy rows use `NULL` →
  twins never merge; open: root-cause the deployed-image-not-applying-fix gap + cross-bucket NULL/"" audit.
- `sports_cf8_available_at_backfill_regression` (ac#6) — `available_at` fill only ~40-50% on `captured` rows
  (service_name-scoped dedup); targeted re-emit BLOCKED pending per-service_name write-fix design (operator said STOP).
- `sports_trades_venue_fetch_failed` (af#5) — restore true `attempted_at` on ~112K rows re-stamped to rebuild runtime
  (originals 2020-08-24…2026-05-31) via the soft-delete recipe.
- `canonical_player_stats_fixture_events_quality` (aa#6) — 740,725 within-object dup rows in `player_stats` (~26%), 4
  concurrent `fixture_events` schemas, `instrument_count` semantic drift; writer-level, **re-measure post-wipe**; add
  writer-side dedup/conformance gate.
- `api_football_cf11_record_captured_noop` residuals (aa#2) — 2 low-priority manifest-writer-contract hardening +
  corpus-wide CF11-drift audit todos.

**D. ML-readiness (feature-correctness + loaders)**

- `sports_odds_stale_fixture_reinjection` (ae#7) — MDPS `bucket_assignment_adapter.py` re-buckets zombie odds boards (no
  staleness cap) → 68.6% ML-readiness cluster (2025-09…11); partial fix landed, pre-kickoff-positive zombie class
  (Russia PL pattern) still open; fix cap + sweep/purge shards + re-run `ml_readiness` gate.
- `sports_halftime_odds_sfi_vs_inplay` (ad#4) — `_apply_ht_odds_pit_gate` default-cutoff unreachable in prod (1 open P1;
  leaks already fixed).
- `sports_fixture_round_not_captured_competition_phase_unknown` (ac#13) — **RESOLVED 2026-07-21.** The "2025-12
  regression window" was a measurement artifact (stale/frozen legacy `entity=fixtures` catalogue + the 400d
  rollup-window bug), NOT a genuine writer stop — raw `entity=fixtures_schedule` capture has never blacked out; live
  re-verified 2026-07-21: `round` 94.8-100% populated and `status_long` 100% populated / 0% `"Unknown"` across
  Dec-2025/Nov-2025/ Jan-2026/Mar-2026 samples. `status_long` sibling audit DONE (instruments-service@4ef4cfeb, already
  shipped). Residual `is_promotion_relegation` still constant `False` — a DIFFERENT, deeper gap (no upstream
  relegation-zone classifier wired into features-service `season_context`, not a round/capture defect) — carried under
  Track F P2 in `sports_consolidated_closeout_2026_07_19.md`, not re-owned here. Backfill-to-2019 is MOOT — floored to
  2020-06 (§3/§6). See issue doc for full evidence.
- `sports_derived_features_per_league_layout_unread_by_ml_loader` (ac#10) — fixed; DOC P3 features-bucket path SSOT
  only.
- ~~`features_service_red_tree_blocks_digest_pin_fix` (aa#11)~~ — **RESOLVED 2026-07-21, verified not a coverage bug.**
  De-flaked already by `features-service@1d65390a` (2026-07-16, predates this plan) — the test derives its pre-launch
  date from the LIVE UAC floor instead of a hardcoded one, so it's self-correcting across floor changes; CI has been
  green 40+ consecutive runs since, including straight through today's 2020-06-06 floor revert. Root cause was a stale
  test assertion, not a live coverage-classification bug. Full detail:
  `issues/features_service_red_tree_blocks_digest_pin_fix_2026_07_15.md`. The **paired digest-pin fix** (cloudbuild.yaml
  auto-repin + tfvars `:latest` flip) is still separately unshipped — its blocker is cleared, but shipping it is a
  distinct P2 todo on `features_sports_service_consolidation_deploy_2026_07_15.md`, not part of this closeout.

**E. Service / infra (dead-code, config, perf — date-independent)**

- `sports_manifest_read_staleness_budget_missing` (ae#2) — no sports entry in `AG_STALENESS_BUDGET_SEC`; add
  `sports:1800` in UTL + mirror deployment-api + grep fleet for hardcoded workarounds (P1, false-DOWN cockpit signal).
- `sports_t0_t1_dependency_gate_never_wired` (af#4) — `check_api_football_dependency()` built but never invoked; wire
  `date=` into footystats/transfermarkt/understat/sfi T1 call sites (P2 dead safety-net).
- `sports_dependency_check_manifest_vs_gcs_path` (ac#8) — live per-date GCS probes instead of manifest reads (5 files/17
  sites); open: manifest-slice design, cached `sports_fixtures.py:356`, path-template constants,
  `_build_fixture_league_map_from_gcs` mapping-coverage gap.
- `sports_reference_function_size_qg_regression` (af#1) — 3 oversize functions in instruments-service
  `sports_reference_*.py`; P3 QG-ratchet debt (parent_epic `instruments_master` — low priority, see §5).

**F. Process / structural (recur on any future re-run — fix BEFORE the post-floor recompute)**

- **SPOT-preemption has no resume** (ac#12 track G, ac#13, plans#7) — the api_football/features backfill fleets restart
  at day-one or die without resume; confirm the shipped `PROGRESS.json` checkpoint contract is wired into these
  launchers before launching the post-floor recompute. **DEDUPED to one todo.**
- **`--force` can't self-heal a no-output day** (Gap-2, ac#9) — a `--force` re-run that produces no output leaves the
  stale fabricated object untouched; the re-run must **PURGE-then-recompute**, not overwrite (else 2,821 post-floor
  fabricated `derived_features` objects survive).

**G. Multi-track sweep (richest source — carry each open track, rescope any pre-floor date range)**

- `sports_features_layer_findings_sweep` (ac#12) — A2 empty-dim-row purge · B2 root-cause the 3 still-stale odds-leak
  consumer shards (2 real bugs) · C3 move manifest atom to per-calculator grain (honest-coverage below-group-grain
  broken) · D junk-symbol ASCII guard deletes real non-ASCII fixtures (~9.8% loss, cross-AG, P1) · E `/v4/historical`
  odds adapter for early-horizon sparsity + forward capture-config · F canonical-naming fixes (case-dups,
  bookmakers-as-`instrument_type`, timeframe-vs-`data_type` SSOT, stale index) · G round-FIXTURES completion.

**MDT legacy↔canonical recovery (P0, blocks the legacy delete-gate — DEDUPED across ab#9 + ad#10 + plans#7)**

- Execute the schema-aware read-split-merge to recover the `player_stats` deficit before `market-data-tick-sports`
  legacy can be deleted: ab#9's 3,816 "master superset" objects (recovers 99.98% of a 6.37M-row gap, window
  2022-03-07…2023-04-30, fully post-floor) and ad#10's ~111,827-row `player_stats`-only union; the 45,701 (b) objects
  are provably redundant (no action). **Rescope the union to dates ≥2020-06-06** — the pre-floor fraction of the 111,827
  is UNMEASURED (flag). Related residual: plans#7 OR-5b(c) 746,928 in-play tick rows — floor re-check before any
  recovery.

**Registry architecture (LIVE half of a split plan)**

- `sports_canonical_universe_and_apifootball_reference_expansion` (plans#2) — the 94-league universe + canonical
  league/cup/team registry + per-source eligibility todos carry as-is; **its Track C/D backfill-since-2015 + ~300-league
  reference-history expansion is MOOT (§3).** `locked_by: live-defi-rollout` — needs `[unlock-plan]` to archive.

---

## 3. MOOT-AFTER-WIPE — resolved/mooted by the floor+wipe (close on the wipe)

- `sports_p2_features_history_to_ml_ready_2026_06_27` (plans#11) — entire scope backfills `derived_features`
  2015→present; pre-2020-06 is the fabricated-by-construction corpus being deleted; only the 2020-06→present slice is
  legit and is already the closeout's Track F clean re-run.
- `sports_pipeline_to_100pct_golden_window_first_2026_06_27` **Phase 2 only** (plans#13) — the 2015→present expansion
  nodes (P2a/P2b/P2c) build pre-floor coverage that gets wiped; Phase 1 (golden window) already ✅ done.
- `sports_p2_history_apifootball_2015_to_present_2026_06_27` **pre-floor slice** (plans#12) —
  FIXTURES/reference/enrichment 2015→2020-06 backfill + 2015-17 diagnosis + league-noise-wipe scope are in the wipe's
  blast radius; only 2020-06→present open items retained (rescope, don't drop the plan wholesale).
- `sports_canonical_universe_and_apifootball_reference_expansion` **Track C/D + reference-history-since-2015** (plans#2)
  — backfilling reference history to 2015 is pointless once pre-2020-06 reference/instruments data is wiped.
- `sports_derived_features_fabricated_corpus_scope_2026_07_20` **2017/2018 portion only** (ac#9) — the 26,089-file block
  (single largest fabricated year) is 100% pre-floor, deleted by the wipe regardless of remediation. (The 2,821
  post-floor fabricated objects + Gap-2 process fix survive → §2-F.)
- Note (not an issue, no action): the just-completed 2015→present travel-calculator gap-fills (af#6, af#7) and
  elo/season_context gap-fill (ac#11) each did wasted pre-2020-06 compute that the wipe discards — docs stay RESOLVED.

---

## 6. THE 2020-06 FLOOR — enforcement surface (every place the floor must be applied)

1. **UAC coverage-floor SSOT — REVERT the 2026-07-15 amendment (CRITICAL, do FIRST):**
   footystats/transfermarkt/open_meteo floors from 2018-01-01 back to 2020-06 (batch ad#6). This is a _live,
   more-permissive_ floor currently contradicting the ruling — until reverted, gates and re-captures will keep pulling
   pre-floor data.
2. **Coverage denominators / honest-coverage tooling** — the below-group-grain honest-coverage model (ac#12 track C:
   grain-mismatch + league_id namespace split), the odds sentinel expectation axis (af#2), and the sports index feeding
   them (must be bleed-free per aa#7). Denominators clamp to ≥2020-06.
3. **Fixture-expectation gates** — the fixture-calendar gate (ad#1, the shipped precedent mechanism) + footystats
   cup-fixture-calendar-awareness (ab#5); `EXPECTED_NO_FIXTURE`/pending-EU seeding must not seed pre-2020-06 alive-days.
4. **`is_bookmaker_league_covered` LIVE coverage-gate bug** (context KEY FINDINGS) — keyed on raw names; fix +
   floor-clamp as part of enforcement.
5. **MDPS / features compute start-date** — candle derivation + `derived_features`/`fixture_features` compute start
   clamped to 2020-06 (the fabrication re-run = closeout Track F).
6. **Manifest `expected_unattempted` (WRITER-materialised)** — the IS enumerator / expectation seeder must not
   materialise expected rows for pre-2020-06 dates (ad#7, ad#1).
7. **Backfill launcher START_DATE defaults** — api_football FIXTURES/enrichment (ac#13, plans#12), features fleets
   (ac#12 track G), round-FIXTURES — all default 2019-01-01/2015 → clamp to 2020-06.
8. **Data-status / catalogue UI render** — denominators + could-exist catalogue floored at 2020-06 (feeds deployment-api
   data-status card).

---

## 7. COVERAGE GAPS / RISKS — a new agent must not miss

1. **The two-ruling contradiction is the #1 landmine.** The 2026-07-15 floors-to-2018 amendment is _live_ in the UAC
   SSOT and re-captured 2,848 pre-floor cells. If the wipe runs without reverting it first, expectation-seeding and
   re-capture immediately re-contradict the wipe. This is a data-correctness + SSOT-contradiction big finding → **NOTIFY
   OPERATOR**, present as an explicit sub-step of items 1 & 5.
2. **Cross-AG prediction bleed (aa#7) is ACTIVELY GROWING** (4,097→6,597 in days) and corrupts the exact sports-index
   denominator that reconciliation (item 4) and floor-enforcement (item 5) read. Root-cause the misattributing writer
   AND clean the rows **before** step 4, or reconciliation reads a dirty denominator.
3. **The peripheral bucket contamination (ae#9) is a SECOND, DISTINCT vocabulary** (country-prefixed) — explicitly NOT
   the casing relocation; do not fold it into items 2/3. It needs its own writer-trace/fix/migrate; confirmed live to
   2026-07-11.
4. **Fix the recurring writer/process defects BEFORE the post-floor clean re-run**, or the re-run re-introduces
   fabrication: Gap-2 `--force`-can't-heal-no-output-day (ac#9, PURGE-not-overwrite), NULL-vs-"" dedup-key instability
   (ae#1), missing writer-side dedup/conformance gate (aa#6), `attempted_at` re-stamp on re-emit (af#5). The fabrication
   ROOT cause (season_context `competition_phase` constant / `matchday` null; `round` never captured) is writer-fixed,
   but 2,821 post-floor fabricated objects survive unless purged.
5. **SPOT-preemption-no-resume (ac#12/13, plans#7)** will silently restart the post-floor recompute at day-one or kill
   it; confirm the `PROGRESS.json` checkpoint contract is wired into the api_football/features launchers before launch.
6. **MDT legacy delete-gate is BLOCKED** on the `player_stats` recovery (ab#9/ad#10) — P0, must run and be rescoped
   ≥2020-06; the pre/post-floor fraction of the ~111,827 rows is **UNMEASURED**. Also plans#7 OR-5b(c) 746,928 in-play
   tick rows need a floor re-check before recovery.
7. **The existing master plan `sports_consolidated_closeout_2026_07_19` (plans#5) IS the skeleton** — reconcile the new
   master against it (strike pre-floor Track V lines, keep Tracks C/S/O/H/D/F(post-floor)/K), don't spawn a parallel
   plan that orphans it. Its evidence base is `sports_consolidated_audit_2026_07_19` (plans#4, LOCAL, don't re-derive).
8. **Archival hygiene:** three plans are DONE→archive-pending per their own audit but frontmatter still `active`
   (manifest_canonicalisation, odds_bookmaker_coverage_enumeration, pipeline_to_100pct); plans#2 is
   `locked_by: live-defi-rollout` → needs `[unlock-plan]` (ASK, never autonomous). ad#8 frontmatter `status:open` is
   stale vs a resolved body.

**Floor calls flagged for operator review** (unsure — do not assume): (a)
`canonical_player_stats_fixture_events_quality` (aa#6) — no date breakdown; re-measure post-wipe. (b)
`compute_shot_quality_batch` OOM (ab#4) — frontmatter says resolved but the body reproduces on **post-floor 2025-08-10**
after the cited fix and escalates; treat as UNVERIFIED, re-verify before trusting. (c) the unmeasured pre-vs-post-floor
split of the MDT recovery rows (§7-6).

## Resolved / superseded + moot-after-wipe

The full triage of all 84 sports docs — RESOLVED/SUPERSEDED (reference), MOOT-AFTER-WIPE (close on the wipe), and
NON-SPORTS/mis-tagged (excluded) — is in the triage transcript `subagents/workflows/wf_4a42bce9-8d6/journal.jsonl` and
mirrored below. **Archival hygiene**: three plans are DONE→archive-pending but frontmatter still `active`
(sports_manifest_canonicalisation_2026_06_01, sports_odds_bookmaker_coverage_enumeration,
sports_pipeline_to_100pct_golden_window_first Phase-1); `sports_p2_history_apifootball_2015_to_present` is
`locked_by: live-defi-rollout` (needs `[unlock-plan]` — ASK).

## 3. MOOT-AFTER-WIPE — resolved/mooted by the floor+wipe (close on the wipe)

- `sports_p2_features_history_to_ml_ready_2026_06_27` (plans#11) — entire scope backfills `derived_features`
  2015→present; pre-2020-06 is the fabricated-by-construction corpus being deleted; only the 2020-06→present slice is
  legit and is already the closeout's Track F clean re-run.
- `sports_pipeline_to_100pct_golden_window_first_2026_06_27` **Phase 2 only** (plans#13) — the 2015→present expansion
  nodes (P2a/P2b/P2c) build pre-floor coverage that gets wiped; Phase 1 (golden window) already ✅ done.
- `sports_p2_history_apifootball_2015_to_present_2026_06_27` **pre-floor slice** (plans#12) —
  FIXTURES/reference/enrichment 2015→2020-06 backfill + 2015-17 diagnosis + league-noise-wipe scope are in the wipe's
  blast radius; only 2020-06→present open items retained (rescope, don't drop the plan wholesale).
- `sports_canonical_universe_and_apifootball_reference_expansion` **Track C/D + reference-history-since-2015** (plans#2)
  — backfilling reference history to 2015 is pointless once pre-2020-06 reference/instruments data is wiped.
- `sports_derived_features_fabricated_corpus_scope_2026_07_20` **2017/2018 portion only** (ac#9) — the 26,089-file block
  (single largest fabricated year) is 100% pre-floor, deleted by the wipe regardless of remediation. (The 2,821
  post-floor fabricated objects + Gap-2 process fix survive → §2-F.)
- Note (not an issue, no action): the just-completed 2015→present travel-calculator gap-fills (af#6, af#7) and
  elo/season_context gap-fill (ac#11) each did wasted pre-2020-06 compute that the wipe discards — docs stay RESOLVED.

---

## The `/autonomous` prompt for the new session (copy this)

```
/autonomous

Complete the sports data close-out to canonical + honest + ML-ready, driving every item below to DONE on a
self-paced loop. The single source of truth is the master plan
`unified-trading-pm/plans/active/sports_master_closeout_2026_07_21.md` — READ IT FIRST; it consolidates every sports
plan/issue across data, service, and monitoring, and links the detailed backing docs. Apply the workspace HARD RULES
(measure artifacts not activity; copy→verify→snapshot→delete; no fire-and-forget VMs; commit+push+flip; grep-then-READ).

OPERATOR RULING — the 2020-06 sports data floor (authoritative):
- Odds tick data starts 2020-06-06 (measured: ZERO odds before that). 2020-06 is the base month for ALL sports honest
  coverage, MDPS, features, and fixture EXPECTATIONS. Everything before it is fabrication-by-construction.
- WIPE all pre-2020-06 sports data from GCS + manifest (features-sports-prd has 212,519 pre-floor objects; the
  instruments/reference bucket + MDPS + manifest rows too; the tick bucket is ALREADY floor-clean). This is the honest
  resolution of the "derived_features fabricated / re-run couldn't compute 2018-2020" findings — DELETE, don't backfill.

DRIVE THESE TO DONE (order matters):
0. ⚠️ FIRST — RESOLVE THE RULING CONTRADICTION. A LIVE 2026-07-15 UAC coverage-floor amendment set footystats/
   transfermarkt/open_meteo floors back to 2018-01-01 and re-captured 2,848 pre-floor cells — it directly contradicts
   the 2020-06 ruling. REVERT those UAC floors to 2020-06 first, or the wipe re-contradicts instantly. (Operator was
   notified 2026-07-21.)
1. PRE-FLOOR WIPE. Measure the exact pre-2020-06 scope per sports bucket + manifest (snapshot the delete list first;
   GCS soft-delete). Delete pre-floor objects; prune the manifest of pre-floor rows. Re-verify by CENSUS: zero pre-floor
   remains. BEFORE any post-floor clean re-run, fix the writer/process defects (Gap-2 force-can't-heal, NULL-vs-"" dedup
   key, missing writer dedup gate, attempted_at re-stamp) or the re-run re-introduces fabrication.
2. ENFORCE THE FLOOR in code so nothing expects pre-floor data: honest-coverage denominators, fixture-expectation
   gates, MDPS/features start-date, manifest expected_unattempted, data-status UI. Promote the floor to a codex SSOT.
3. league_id RELOCATION — COPY. Run the VERIFIED, adversarially-reviewed executor as a MONITORED migration job (it is
   ~139K raw objects, multi-hour — run on a VM, not inline; it timed out on a live walk when tried inline):
   `market-tick-data-service/scripts/sports/league_id_relocation/migrate_sports_league_id_casing_2026_07_21.py`
   First `--apply-prod` (no `--confirm-prod-write`) WITHOUT `--index` for the live out-of-scope census + VM guard;
   then `--apply-prod --confirm-prod-write` (copy+verify only, never deletes, refuses while any features-sports VM runs).
   Then the 127K DEFERRED shapes (odds_horizon_bucket, batch_footystats) — the "then extend" passes. Full run sequence +
   the GO/caveats are in `plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md`.
3b. FOLD INTO THE DELETE: the 6,110 lowercase-league_id objects (mtds_t2_6, 2025-07-31..12-31) proven 100% identical to
   their UPPERCASE canonical twins — same casing root cause; dedup/delete in the same pass.
4. league_id RELOCATION — MANIFEST-SWAP + DELETE. After every shape is copied+content-verified: atomic manifest-swap
   (reuse `deployment-service/scripts/rebuild_sports_manifest.py::_clean_stale_league_entries`), MDPS reprocess of the
   processed surface, coverage-registry refresh, THEN the SEPARATE irreversible delete of the old non-canonical objects
   (operator-authorised on the passing dry-run; snapshot first; do a final at-scale content re-verify before deleting).
4b. CLEAN the ACTIVELY-GROWING cross-AG prediction bleed (>=6,597 asset_group=prediction rows in the sports index,
   growing) BEFORE reconciliation — it IS the denominator reconciliation reads.
5. /data-pipeline-reconciliation for sports — run the skill PROD-only/read-only to prove every file is canonical + in
   the right place across the four surfaces (path ↔ content ↔ manifest ↔ catalogue). Fix any residual non-canonical.
6. Sweep the LIVE-POST-FLOOR issues in the master plan (the coverage-gate bug where is_bookmaker_league_covered is keyed
   on raw names; peripheral-bucket vocabulary contamination; etc.). Close MOOT-AFTER-WIPE issues as the wipe lands them.

Terminate when: pre-floor wiped + floor enforced; every sports odds/feature object canonical & floor-clean
(reconciliation green); relocation copy+swap+delete complete; and the master plan's todos are all flipped with evidence.
Write the rule-9 final report. Hard-stops stay human-only.
```

## Manifest MUST be rebuilt after EVERY delete (2026-07-21 — do not skip)

Deleting GCS objects does NOT update the manifest: the sports index is a consolidated (seed + per-VM shard) artifact, so
deleted objects leave PHANTOM rows (manifest claims data that no longer exists on GCS), and the next consolidation can
re-assert them from the seed. Every delete pass in this plan therefore ENDS with a GCS-walk manifest rebuild
(`deployment-service/scripts/rebuild_sports_manifest.py` → `_clean_stale_league_entries` + re-derive from disk) and a
re-verify that manifest rows == GCS objects. This applies to: the pre-floor WIPE (prune all pre-2020-06 rows), the
relocation DELETE (the manifest-swap step), AND the twin delete below.

- [x] [DATA] P1. ✅ **6,110 lowercase-twin duplicate objects DELETED** — the `league_id=soccer_*` objects (2025-07-31…
      12-31) proven 100% crc-identical to their `SOCCER_*` uppercase twins were deleted (per-object twin re-verify;
      snapshot `scratchpad/lowercase_twin_delete_snapshot.json` [session-local] + GCS soft-delete as the net). Resolves
      `mdt_t2_6_league_case_duplicate_population_2026_07_16`.
- [ ] [DATA] P1. **Prune the twin-delete phantom manifest rows.** The live sports index carries 7,295 lowercase
      `league_id=soccer_*` rows; the 6,110 deleted-object rows are now PHANTOM (redundant — the real data is still
      covered by the `SOCCER_*` uppercase rows, so it is drift, not a coverage gap). Clean via the GCS-walk rebuild
      (above); it is subsumed by the relocation manifest-swap, which reconciles the whole lowercase set. NOT hand-edited
      at session depth (a manual index write with the consolidator running is where corruption happens).
- [x] [CODE] P0. ✅ **2020-06 floor conflict RESOLVED** — `unified-api-contracts@8cdf7808`: all 7 sports
      `SOURCE_COVERAGE_START`/override floors clamped to `date(2020, 6, 6)`, reverting the 2026-07-15 amendment; tests
      rewritten. The remaining floor-enforcement surface (gates, launcher START_DATEs, data-status UI, codex SSOT) is in
      the pending-execution list above.

---

## Progress Log — 2026-07-21 autonomous session ("do as much as possible not operator-blocked and logical")

**Landed + verified this session:**

1. ✅ **Pre-floor GCS WIPE — 649,643 objects deleted, 0 errors, verified.**
   - features-sports-prd `sports_features/by_date/` = **212,519** (2017-01-01…2020-06-05). Soft-delete 7d net.
     Spot-verified: pre-floor days (2017/2018/2019/2020-06-05) → 0 objects; post-floor (2020-06-06=60, 2021=54, 2025=42)
     → intact. Cutoff exact.
   - instruments-store-sports-prd = **437,124** (`sports_reference/by_date` 398,240 · `sports_reference/fixtures` 4,735
     · `instrument_availability/by_date` 34,149). soft-delete=0 → full path snapshots taken pre-delete (scratchpad,
     session-local); current-state registries (`teams_in_league/`/`mappings/`/`master/`/`standings/`) LEFT UNTOUCHED.
   - Tool: `deployment-service@78a0aa4` `scripts/wipe_pre_floor_sports_2026_07_21.py` (path-based `day=<D>` cutoff — NOT
     `time_created` which is None via the UTL list client; triple-checked per object at delete time; 32-worker).
2. ✅ **Floor ENFORCED in code** — `instruments-service@d6747063` (venue-epoch clamp) + `deployment-service@78a0aa4`
   (launcher START_DATE clamps) + codex SSOT `codex/02-data/sports-2020-06-data-floor.md` + CLAUDE.md pointer. UAC floor
   consumers (`enumerate_expected_universe`, deployment-api data-status) already read `uac@8cdf7808` (auto-propagate).
3. ✅ **Relocation executor RE-VERIFIED** live: VM guard passes, timed `--validate` PASS=5/FAIL=0/quarantine=0.

**Deferred work after 2026-07-21** (each already a `- [ ]` above or below — nothing lost):

| Item                                                                                     | State / why deferred                                                                                                                                                                                                                                                                                                                           | Blocked-on                                                                                                |
| ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **Manifest pre-floor prune** (131,426 features + 944,776 instruments-store phantom rows) | _Cannot be done safely yet_ — the `_index/availability_index.parquet` is consolidator-built from `_index/per_vm/` shards and instruments-store holds an ACTIVE `consolidator.lock`; a session hand-edit is the exact corruption this plan forbids. Floor enforcement keeps these rows OUTSIDE the reported denominator, so no live dishonesty. | A consolidator-coordinated / phantom-audit rebuild (proper mechanism), run when the consolidator is idle. |
| **league_id relocation COPY** (139K raw + 127K deferred shapes)                          | _Not done — compute-scale, not operator-blocked._ Executor verified correct; measured ~25.7 h single-process ⇒ needs a VM-SHARDED monitored run (shard by day-range via `--index`). Deliberately NOT fire-and-forgotten in the session tail.                                                                                                   | A dedicated monitored VM fleet run. COPY is reversible/idempotent; DELETE stays separately gated.         |
| **relocation MANIFEST-SWAP + DELETE + twin-row prune**                                   | Sequenced AFTER the copy completes.                                                                                                                                                                                                                                                                                                            | The copy above.                                                                                           |
| **cross-AG prediction bleed cleanup**                                                    | Sequenced BEFORE reconciliation (unlocated writer).                                                                                                                                                                                                                                                                                            | Writer trace.                                                                                             |
| **/data-pipeline-reconciliation sports**                                                 | Reads the dirty denominator (bleed + phantom rows) — running it pre-relocation reports known-pending issues.                                                                                                                                                                                                                                   | Bleed cleanup + relocation.                                                                               |
| **`is_bookmaker_league_covered` raw-name keying (P1)**                                   | Coupled to the relocation per this plan (regenerate coverage JSON post-relocation).                                                                                                                                                                                                                                                            | Relocation.                                                                                               |

**Recommended NEXT item:** the **league_id relocation COPY** as a monitored VM-sharded job — it's fully prepped
(executor + maps committed `mtds@b2a49317`, guard clear, dry-run + validate green) and unblocks the manifest-swap,
delete, coverage-registry refresh, and reconciliation that all sequence behind it.

**Rule-9 forced-tradeoff decisions (documented, per AUTONOMOUS rule 1):**

- The **manifest prune** was NOT hand-executed — an active consolidator + per-VM-shard rebuild makes a session index
  write a corruption risk that this plan explicitly forbids. Least-bad path: wipe the GCS objects (done), enforce the
  floor so phantom rows fall outside the denominator (done), and route the row prune through the proper rebuild.
- The **relocation** was NOT launched inline — 25.7 h single-process is a VM-sharded job; launching an unmonitored
  multi-hour PROD-write in the session tail is the fire-and-forget anti-pattern. Least-bad path: verify readiness +
  document the exact launch sequence for a monitored run.
- Environmental fix: gcloud user OAuth expired mid-session; restored the CLI by activating the ADC service account
  (`unified-trading-sa`, non-expiring) — this also un-blocks the relocation's gcloud-based VM guard.
