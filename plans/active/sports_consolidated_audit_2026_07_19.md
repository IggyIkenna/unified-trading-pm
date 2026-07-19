---
doc_type: plan
title: Sports consolidated audit — measured current state across IS / tick / MDPS / features (2026-07-19)
summary: >-
  A measured, read-only audit of the full sports data path (instruments-service reference, market-tick-data-service
  odds, market-data-processing-service bucketing, features-service) plus SSOT/codex alignment and plan reconciliation.
  Produced by a 6-agent parallel fan-out, every claim backed by a GCS/parquet/manifest measurement. Feeds the actionable
  sports_consolidated_closeout_2026_07_19 plan. This is a LOCAL audit doc — not AO-ingested.
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
tags: [audit, sports, canonical, honest-coverage, data-completion, ml-readiness, data-correctness]
related:
  [
    sports_features_layer_findings_sweep_2026_07_18.md,
    sports_consolidated_closeout_2026_07_19.md,
    defi_consolidated_closeout_2026_07_18.md,
    data_completion_defi_2026_07_15.md,
  ]
created: "2026-07-19"
last_updated: "2026-07-19"
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: research
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
assigned_role: data_engineering
drift_direction: advance-code
---

# Sports consolidated audit — measured current state (2026-07-19)

> **Method**: 6 read-only sub-agents fanned out across the four sports-path services + one
> SSOT/codex/plan-reconciliation agent + one smoke/speed agent. Every coverage %, naming state, and gap below is backed
> by a direct GCS listing, parquet column read, or manifest read — **not** a grep-and-conclude. Cross-agent claims were
> adversarially verified (two agent errors were caught and corrected during synthesis — see § Verification notes). This
> doc is the measured foundation; the actionable work lives in `sports_consolidated_closeout_2026_07_19.md`.

## Headline verdict

The sports vertical is **structurally sound and mostly complete**, with the reference layer canonical and the round work
from the 2026-07-18 sweep (§§ Q/R/T/U/W) confirmed terminal. It is **NOT yet ML-ready**, blocked by one live
data-correctness defect and a handful of canonical/honest-coverage gaps:

- **🔴 P0 (LIVE, now FIXED) — season_context fabrication (§ Z)**: the features layer was writing fabricated non-null
  `competition_phase='late'` / `games_remaining=0.0` / `points_at_stake=0.0` for the whole corpus — silently-wrong
  values a model reads as real signal. Root-caused, fixed (features-service, see closeout FEATURES track), the writing
  fleet was **stopped**, and a clean corpus-wide re-run is required.
- **🟠 P1 — three canonical-honesty gaps**: the fixtures **manifest atom** never migrated to the split entity
  (`data_type` still `"FIXTURES"`, not `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES`); a **cross-AG manifest bleed** (4,097
  live `asset_group=prediction` rows in the sports bucket); and the **K-series data_type casing** (market-data-sports
  still mixed UPPER/lower vs the operator's K0-(b) UPPER decision).
- **🟢 Leakage posture is CLEAN** where measured: FEATURE_HORIZONS input-scoping is monotonic and enforced, no
  post-kickoff data reaches a pre-match feature, HT is honest-absent. The one residual leak surface is 27 legacy
  post-kickoff T-0 odds shards on disk (§ B2 dates), pending a reader-consumption check.

Everything the 2026-07-18 sweep shipped (round derivation, catalogue entity repoint, backfills, § V split-read, § S
total_matchdays, leakage fixes) is **independently re-confirmed terminal** in code and in the live corpus.

---

## 1. Per-service measured state

### 1.1 instruments-service — reference data (bucket `instruments-store-sports-prd`)

Reference layer is **healthy and canonical**. Measured coverage (manifest `data_type`):

| entity          | captured | empty_confirmed | attempted_failed | expected_unattempted | verdict                              |
| --------------- | -------: | --------------: | ---------------: | -------------------: | ------------------------------------ |
| FIXTURES\*      |   94,225 |         239,369 |                0 |                    0 | honest sparsity                      |
| TEAMS           |  435,236 |          24,991 |               21 |                2,209 | healthy                              |
| STANDINGS       |  109,913 |         187,335 |              287 |                    0 | healthy (287 = 0.096% micro-gap)     |
| INJURIES        |   10,479 |         278,476 |                0 |                9,921 | healthy                              |
| WEATHER         |   12,290 |         243,397 |                0 |                  456 | healthy                              |
| LEAGUES         |    8,780 |               0 |                0 |                    0 | write path retired 2026-05-07        |
| PLAYER_STATS    |   26,207 |         195,586 |                0 |                1,830 | healthy                              |
| FIXTURE_STATS   |   42,125 |         185,137 |                1 |                1,893 | healthy                              |
| FIXTURE_EVENTS  |   42,936 |         174,916 |                2 |                1,935 | healthy                              |
| FIXTURE_LINEUPS |   42,173 |         175,302 |                0 |                1,925 | healthy + full player/coach identity |

\* FIXTURES is an **umbrella label** — see the manifest-atom finding in § 2.1. Catalogue (`prod/catalog.parquet`,
164,763 rows, written 02:01:36Z) matches R-FIXED exactly: `round` 100% not-null / 78.1% non-empty on fixture rows;
`competition_phase`/`round_name`/`is_promotion_relegation` correctly ABSENT (they are `features_sports` UAC fields, not
catalogue columns — R-FIXED's retraction validated). K0-(b) UPPER conformant. 4-state manifest correct, no fake
captures. **Catalogue is stale** relative to the same-day §§ T/U/W backfills (+26,894 round rows) — needs a re-roll.

### 1.2 market-tick-data-service — odds capture (bucket `market-data-tick-sports-prd`)

Manifest 1,974,679 rows (unchanged since 07-18 — no migration has run). Coverage:

| source                   |      rows | note                                                                 |
| ------------------------ | --------: | -------------------------------------------------------------------- |
| odds_api                 |   388,868 | **28 distinct bookmaker venues, all 23 declared present, ZERO gaps** |
| footystats               |    42,476 | all mislabeled `venue=ODDS_API` (legacy bundle)                      |
| api_football (sentinels) | 1,398,256 | 1,247,647 empty_confirmed                                            |
| mdps_odds_horizon_bucket |   124,294 | deliberate cross-bookmaker aggregate                                 |
| polymarket_clob          |    20,785 |                                                                      |

**Markets vocabulary already exists**: `ODDS_API_MARKET_TO_CANONICAL` (h2h→MATCH_ODDS, spreads→ASIAN_HANDICAP,
totals→OVER_UNDER, btts→BOTH_TEAMS_TO_SCORE…), UPPER already, on the `market_key` column — K1's "introduce a
betting-market vocabulary" is really _promote the existing vocab to the `instrument_type` axis_, not build new.

**Capture cadence — corrects the sweep's § E note**: the "single daily 12:00 UTC fetch" is only the _discovery_ call;
the odds-snapshot loop is **multi-shot** via `TIER_1_OFFSETS` (measured 16 distinct `fetch_utc` in a 2022 shard). BUT
recent quiet days (2025-12-18/31) showed only 1 fetch — an open question (did the multi-shot loop not run?) that
compounds § B2. `live_odds_api` = **14 rows in 6 years** — the in-play WS connector is dark; HT-horizon starvation is
structural.

### 1.3 market-data-processing-service — odds horizon bucketing

**§ B2 ROOT-CAUSED** (both prior hypotheses measured false — not a join, not a threshold): a **615-minute structural
dead-zone between the T-12h `[675,765]` and T-24h `[1380,1500]` TIER1_HORIZONS windows**. On a low-fixture day the few
active fixtures' single-fetch `bm_minutes_to_kickoff` (~1144–1266 min) all land in that gap → `horizon_idx=-1` → zero
output → `ADAPTER_RETURNED_EMPTY_OUTPUT`. 2025-12-24 is genuine honest-absence (0 in-window). A normal match day
(2025-12-20) buckets 11,018 rows through cleanly. **F3 timeframe migration is DONE** for the live canonical writer
(124,294 rows, `timeframe` populated). Leakage guard is on the correct column (`bm_minutes_to_kickoff`).

### 1.4 features-service — feature groups (bucket `features-sports-prd`)

Manifest 200,793 rows: derived_features 61,461 · fixture_features 76,643 · odds_features 4,273 · **sfi_progressive 1
(corpus-empty!)** · dead dimension groups players/coaches/referees/rounds 4,216 each (§ A2 purge still outstanding).

**🔴 § Z — the LIVE P0 (now fixed)**: `matchday` 0% populated in written shards; `competition_phase`/`games_remaining`/
`points_at_stake` **fabricated** (100% `"late"` / `0.0`, zero variance). Root cause fully traced and reproduced on
2019/2024 dates — see § 2.2. **Leakage: CLEAN** — FEATURE_HORIZONS monotonic and enforced (verified in data), no
post-kickoff leak, HT honest-absent. ML loader correctly reads the per-league layout (fixed 2026-07-14).

---

## 2. Cross-cutting findings (NEW — not captured by any existing plan)

### 2.1 🟠 Manifest atom ≠ writer atom for fixtures — P1 CANON

The GCS writer split to `entity=fixtures_schedule`/`fixtures_outcomes` weeks ago, but the **manifest still records
`data_type="FIXTURES"`** (hardcoded, writing that label as recently as 2026-07-19T10:06:36Z). Violates the workspace's
"shard atom identical across writer/manifest/status/gate/UI" rule — every honest-coverage tool reading `"FIXTURES"` is
blind to the schedule-vs-outcomes split. 8 call sites: `sports_reference_fixtures.py:242,279`, `process_write.py`,
`writers.py:219`, `catalogue.py:136`, `process_completeness.py`, `process_preflight.py`, `process_zero_records.py`,
`sports_fixtures_daily_repoll.py`.

### 2.2 🔴 season_context fabrication — P0 FEATURES (LIVE → FIXED)

`derived_features_exporter.py:149-151` merges `footystats_matches` with no `candidate_cols` filter → injects an all-NaN
`match_week`; `derived_features_helpers.py:782-788` gate checked column _presence_ not population → preferred all-NaN
`match_week` over round-derived `matchday`; NaN then fell through `_competition_phase` to `'late'` and
`max(0.0, total-NaN)` to `0.0`. **Fixed**: gate now derives from `round` (match_week fills only genuine gaps),
`_competition_phase`/batch-loop/single-fixture path return honest `None` on NaN. Verified via the real gate path
(matchday 40/40, phase `{early,mid,late}`); 2 regression tests added. **Requires a clean corpus-wide re-run.**

### 2.3 🟠 Cross-AG manifest bleed — P1 DIAG (operator-notify)

4,097 rows tagged `asset_group="prediction"` (Kalshi/Polymarket, `service=market-tick-data-service`) + 2 cefi/defi are
physically in the **sports** bucket's consolidated manifest index — dates 2026-06-26…07-18, **live, not legacy**. Two
obvious write paths ruled out (both resolve `instruments-store-prediction` correctly / fail loud). Root cause unlocated
— next: `ingest_kalshi_bulk_to_canonical.py`, `rebuild_prediction_manifest.py`, the sentinel fan-out. 0.08% of 5.37M
rows but a cross-repo/SSOT-contradiction class finding.

### 2.4 🟠 K-series data_type casing — P1 CANON

market-data-sports is the ONLY mixed bucket (4 UPPER + 9 lower) vs operator K0-(b) "sports → UPPER everywhere".
Lower-case needing UPPER: `odds` 20,331 + `odds_movement` 4 + `odds_snapshot` 4 + dead
`odds_horizon_bucket_{15m,1h,4h,1d}` 1,337 = **20,339 rows, all from ONE legacy artifact**
(`ticks_migrated_20260505T152043Z.parquet`), NOT a live writer. BUT the **live writer** (`venue_fetch.py:871-900`) emits
lower-case `instrument_type=odds/data_type=trades` for all 388,852 active captures — K1 must fix the live writer +
sentinels _before_ K2 migrates the historical rows.

### 2.5 🟠 attempted_failed triplet — P1 DIAG (no relabel)

112,277 `attempted_failed` rows confined to **exactly** BETFAIR 37,426 / MATCHBOOK 37,426 / PINNACLE 37,425, all 6
years, all leagues, `source=api_football`. Suspicious — PINNACLE/MATCHBOOK capture fine elsewhere. Hypothesis:
`_SNAPSHOT_VENUES` CLV/closing-line completeness triplet. Root-cause needed; do NOT relabel (§ B2 precedent).

### 2.6 Other measured findings

- **Legacy bare `entity=fixtures/` path is STALE, not actively written** (CORRECTED — contradiction sweep measured every
  sampled file incl. today's `day=2026-07-19` partition at `Creation Time 2026-05-23T20:35:42Z`, zero writes since). The
  files remain VISIBLE under forward `day=` partitions because they are pre-fetched future-dated schedule objects
  written back in May, not an ongoing dual-write. My earlier "still active today" wording conflated presence with active
  writing — there is no live dual-write hazard; the dead code path should still be culled. (P2)
- **Dead `sports_reference_v2/` dual-layout** (frozen 2026-04-20, no entities) — cull. (P2/CLEANUP)
- **27 leaked legacy post-kickoff T-0 odds shards** on the § B2 dates (100% post-kickoff, unprefixed path B1 never
  touched) — live leak surface if any reader consumes the unprefixed path. (P1)
- **sfi_progressive corpus-empty** (1 manifest row) despite a documented 2020→today backfill window. (P1)
- **is_promotion_relegation structurally dead** (hardcoded False; standings relegation-zone could feed it). (P2)
- **Manifest reason/error_code blank** for the odds manifest; **zero `expected_unattempted`** in 1.97M odds rows —
  possible C5-class silent-empty. (P2 DIAG)
- **1,337 dead `odds_horizon_bucket_{15m,1h,4h,1d}` rows** + frozen 2018-2020 markets/outcomes/settlements/
  arbitrage_opportunity scaffolding — purge. (P2/P3 CLEANUP)
- **fixture_lineups now carries full player/coach identity** → catalogue `player` grain can upgrade from `injuries`
  (injured-only) to `fixture_lineups` (full roster). (P2 opportunity)

---

## 3. Codex drift (9 docs)

| doc                                     | verdict          | fix                                                                                    |
| --------------------------------------- | ---------------- | -------------------------------------------------------------------------------------- |
| `sports-adapter-dependency-order.md`    | DRIFTED (worst)  | §1/§3 point at frozen `entity=fixtures`; repoint to split; §5 gate unreachable in prod |
| `sports-data-types-catalog.md`          | DRIFTED          | data_types shown lower-case; rewrite UPPER per K0-(b); state F3 timeframe resolution   |
| `sports-gcs-path-ssot.md`               | DRIFTED          | add `pipeline_mode=` segment + split-entity rows                                       |
| `sports-scheduling-and-sharding.md`     | DRIFTED          | §9 diagram cites legacy path; §12 roadmap (13 plans) all done → banner                 |
| `sports-live-odds-connectivity.md`      | DRIFTED          | §3 describes 13 scrapers deleted 2026-07-08 → retirement banner                        |
| `sports-integration-plan.md`            | SEVERELY DRIFTED | pre-impl artifact mislabeled current → SUPERSEDED banner                               |
| `sports-fixtures-lifecycle.md`          | current-ish      | add split-first read note (§ V)                                                        |
| `sports-data-source-coverage-matrix.md` | mostly current   | add split note to §2.1                                                                 |
| `sports-batch-live.md`                  | mostly current   | add split note + sync venue list                                                       |

Plus `sports_master.md` epic has 5 broken `related:` paths (now under `../archive/`).

---

## 4. Plan reconciliation — collapse ~11 plans + 58 issues → a handful

**Active plans**: FOLD-INTO-CLOSEOUT → `sports_manifest_canonicalisation_2026_06_01` (master predecessor),
`sports_legacy_bucket_cutover_2026_07_16` (STORE; T2.9/T2.10 big),
`sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24` (CANON/COVERAGE),
`sports_p2_history_apifootball_2015_to_present_2026_06_27` (COVERAGE),
`sports_catalog_league_grain_only_scope_2026_07_08` (CATALOG), `sports_odds_exchange_fixed_fork_2026_07_18` (CANON),
`sports_p2_features_history_to_ml_ready_2026_06_27` (FEATURES). KEEP-ACTIVE (near-done):
`sports_data_sources_canonical_completion_2026_07_13`, `features_sports_service_consolidation_deploy_2026_07_15`.
DONE→archive: `sports_odds_bookmaker_coverage_enumeration_2026_06_20`. SUPERSEDED:
`sports_pipeline_to_100pct_golden_window_first_2026_06_27` (coordinator, absorb 2 remaining children).

**Issue docs (58)**: ~30 DONE-but-unflipped (need `status: resolved`); 2 SUPERSEDED; ~17 FOLD; 1 KEEP (cross-AG). Full
disposition list is in the closeout's Track X + the Contradiction Resolution section; the CODEX+CLEANUP tracks carry the
status-flips. (Corrected: the earlier "reconciliation bank" reference named a scratch artifact that is not a repo doc.)

---

## 5. Smoke tests + speed + "right days"

**No sports-specific smoke test exists**; the features one only checks `feature_group="odds"` and would NOT have caught
§ V, § Z, or § B2 (verified). No test exercises `IS → tick → MDPS → features` with content assertions. Date selection is
`resolve_latest_captured_date()` or a hardcoded pre-cutover `2026-05-03` — no busy/thin awareness, so a smoke test can
land on a legitimately-empty holiday day and silently pass. **Prior art**: the golden window (2025-09-01…11-30) already
exists in one-off scripts → promote to a shared "right days" SSOT (busy `2025-12-20` / thin `2025-12-24` / known-buggy
`2025-12-18` + `2024-03-09`). This is the "speed / right days / fixtures-really-return-results" pillar of the operator's
ask.

---

## 6. Operator decisions needed

- **§ U** — 489 in-window (league,season) pairs / 10,869 blank-round rows in leagues **absent from the UAC registry**:
  extend the registry or stop capturing them. "Sports backfilled 100%" can't be asserted until settled.
- **§ T** — pre-2019 blank-round rows (122,864) are outside the stated 2019→2026 window: confirm whether 2013–2018 is in
  scope.
- **§ 2.3 cross-AG bleed** and **§ 2.5 attempted_failed triplet** — both are notify-class; root-cause before any
  relabel.

---

## Verification notes (adversarial cross-checks during synthesis)

- Agent F reported the live split entity at `sports_reference_v2/` "nearly empty" — **refuted by direct measurement**:
  the live layout is `sports_reference/by_date/` (4,332 days, active to 2026-12-06); `sports_reference_v2/` is a frozen
  abandoned experiment. The session's round work is in the correct live layout. (v2 → CLEANUP finding.)
- My own § X claim (`competition_phase` 77.2% populated) was **wrong** — it measured the isolated
  `_compute_season_features`, not the real pipeline, which was 0%. Caught by agent D + confirmed on freshly-written
  shards (100% fabricated `'late'`). This is the § Z P0.

## Progress Log

- 2026-07-19 — 6-agent audit fan-out complete; all findings measured + banked. § Z P0 root-caused, fixed, fleet stopped.
  This audit doc authored; feeds `sports_consolidated_closeout_2026_07_19.md`.
