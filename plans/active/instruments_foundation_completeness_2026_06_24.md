---
title: "Instruments Foundation & Catalogue Completeness — gated rebuild, every asset group"
created: 2026-06-24
parent_epic: instruments_master
assigned_vm: vm-cefi
estimate_class: design
estimate_baseline_ai_days: 32
estimate_calibrated_ai_days: 19
source:
  - operator directive 2026-06-24 (foundation-first reset; ask-every-gate; observability mandatory; coverage in-line
    with UI)
  - cefi instruments ground-truth audit 2026-06-24 (read-only; see §Starting state)
locked_by: live-defi-rollout
priority: P0
status: active
---

# Instruments Foundation & Catalogue Completeness — gated rebuild

**Codex SSOT (the standard this plan executes):** `codex/02-data/instruments-foundation-and-catalogue-completeness.md`.

**Operator directive 2026-06-24 (the reset):** reference data is the foundation MTDS filters against. We were chasing
MTDS coverage while the instruments foundation had day-gaps, a paused daily capture, and late MVP tags — backwards.
Rebuild it in the **gated order**, **operator sign-off at every gate** (ask every time — do not run ahead). Every
backfill/roll-up/job must be a **registered, observable BATCH deployment** in the cockpit (no fire-and-forget). Every
coverage number flows through the **`compute_honest_coverage` SSOT** so the deployment-UI shows the same real number.
**cefi first**, then defi · tradfi · sports — same process.

## Starting state — cefi ground-truth audit (read-only, 2026-06-24)

GOOD: history 2019-03-30→2026-06-23 (2,640 days); MVP tags present (157,092 / 227,576); Binance stocks/commodities
present (AAPL/TSLA/MSTR/NVDA/XAU/XAG); `compute_honest_coverage` SSOT exists + deployment-api aligns. RED: **3 day-gaps
06-19/20/21 silently absent** (99.9% is blind); **expected-universe not materialised** for missing days; coverage is
**per-(venue,day) shallow** (no depth); **per-venue cumulative count non-monotonic** (1000s of day-over-day drops,
unreconciled); **junk-symbol noise**; **daily-capture trigger (08:30) PAUSED**. **MTDS cefi is PAUSED** (no backfill
fleet running) pending this foundation.

**tradfi ground-truth (2026-06-24, §9):** GOOD — 7 venues incl. new KRX, VX futures under CBOE, US session SSOTs, shared
SSOT. RED — KRX 96% silently absent (62/1,690 days) + no Korea calendar (24/7 default); ICE non-billable yet enumerated
(8,856→1); CBOE polluted (9 VX + 91 SPOT_PAIR + 5 un-deleted INDEX); equities only from 2023-04-15; NASDAQ/NYSE shallow
(no depth oracle); `available_to` false-delistings (global-`latest_day`); verify tradfi daily-capture not PAUSED.

**defi ground-truth (2026-06-24):** the catalogue/manifest is correctness-clean (single canonical namespace, EU 100%
genuine-fetchable) but G4 catalogue-as-filter is incomplete — capture fetched the subgraph top-N, not the catalogue
pools, so honest_cov is stuck ~25.7% (overlap-flat). Live work in the DeFi plan (cross-ref above).

**sports ground-truth (2026-06-24, read-only audit):** RED — **G1 enumeration NOT MVP-scoped**: api_football FIXTURES
span **1,531 leagues vs the ~101 canonical** (1,437 non-canonical = ~106k noise rows). **G2 foundation holes within the
94 canonical leagues**: 2015–2017 = **0 captured** (35,889 all-`empty_confirmed` across 76 MVP leagues that played) +
**40,041 `attempted_failed`** (2018/2021/2023 clusters); 7 canonical leagues with zero fixtures rows. GOOD —
golden-window FIXTURES ~100% (other-agent reclassify); the per-source coverage model (`is_league_entity_covered`) +
season-window/ off-season guards exist. Already shipped THIS session (manifest-correctness, not the gates): #1
phantom-reconcile pipeline_mode fix (IS@c01bb1c), #2 understat per-league 404 2-way (IS@18398c8), #3 api_football MTDS
wrong-source odds wipe (1.4M rows + 231,532 objects; MTDS `trades` now 100%/0-failed), #4 `DP_HIGH_ATTEMPTED_FAILED`
alert (deployment-service@cb330f7). **Sports does NOT start its G1→G5 until cefi is DONE** — these are the audit + the
pre-staged manifest-correctness fixes, tracked in `sports_golden_window_attempted_failed_remediation_2026_06_24.md` +
`sports_fixture_completeness_oracle_2026_06_24.md`.

---

## Phase 0 — cross-cutting foundations (block G2; build once, reused by every AG)

- [ ] [INFRA] P0. **Observability wiring (§0.5) for every instruments/MTDS backfill VM + roll-up job** — register as a
      classified `DeploymentTarget` (`classify_deployment_target` + `cloud_run_job_registry` / VM `lifecycle_class`),
      `ServiceBootstrap` + `log_event` + 60s `PIPELINE_HEARTBEAT` + ≥1 progress/hr, error→`#data-pipeline-alerts`,
      terminal `exit_code` + log-mtime persisted, **appears in `/deployments` BATCH tab with click-through to logs**.
      DoD: a launched job is click-through-able in the cockpit; SSH not required. SSOT:
      `codex/05-infrastructure/deployment-observability.md`.
- [ ] [SCRIPT] P0. **Layered coverage via the SSOT (day + depth)** — implement `day_coverage` + `depth_coverage` (§2)
      strictly through `compute_honest_coverage`, with the **expected-universe materialised** (missing days/instruments
      seeded `expected_unattempted`, gaps = 0% not absent). Surface BOTH per-AG/per-venue in manifest → `/data-status` →
      deployment-API → deployment-UI. **No ad-hoc coverage scripts** that diverge from the UI. DoD: UI shows day+depth
      per venue; a synthetic gap drags day_coverage down.
- [ ] [SCRIPT] P0. **Cumulative-drawdown health metric (§1.2)** — per venue, the cumulative-instruments-ever-seen
      series; any negative day-over-day delta = a hard defect (flag + block). Active-count drops must net to a typed
      reason (cefi/tradfi delisting; DeFi delisting OR `NOT_ENOUGH_TVL`). DoD: drawdown count per venue surfaced; target
      zero.
- [ ] [DESIGN] P1. **Expected-universe ORACLE design (§2.1)** — the `depth_coverage` denominator: (a) per-instrument
      true genesis from **venue truth** (not circular first-seen); (b) **time-varying futures expiry/listing rules** per
      venue, versioned by effective-date, in UAC. Ship **Tier-A proxy** first (labelled), **Tier-B truth** is the
      completion bar. DoD: design doc + the UAC rule-registry shape; sourcing decision for venue-truth genesis.
- [ ] [SCRIPT] P0. **Consolidation reconcile (§2.2)** — incremental for steady-state + **scoped `--force`/reconcile**
      after any backfill + periodic, reconciling **actual shards vs the materialised expected-universe** to _discover_
      unexpected-missing shards (→ 0% in day_coverage + re-fetch queue). Never a blind whole-corpus `--force` (clip the
      window; purge discipline vs the 32Gi OOM). DoD: a deleted/absent expected shard is surfaced as a gap, not silently
      merged-around.
- [ ] [SCRIPT] P0. **Drilldown-correctness guard (§2.3)** — (1) UI renders the SSOT value, never recomputes; (2)
      **reconciliation guard**: independent raw-GCS recompute == manifest/SSOT/UI (ε=0), wired as a QG step + watchdog →
      `#data-pipeline-alerts` on drift; (3) manifest-freshness watchdog + per-cell click→GCS traceability. DoD: a seeded
      manifest/raw divergence trips the guard; cockpit number is proven == ground-truth.
- [ ] [SCRIPT] P0. **Verification discipline — captured↔expected KEY-OVERLAP, not raw count (§6.1/§6.3)** — the G5/
      backfill success signal is `expected_unattempted` DROPS / the captured∩expected per-(instrument,day) overlap
      CLIMBS, proven by grepping actual captured key-tuples against the expected set — NEVER `captured++` (captures can
      land as net-new cells keyed differently than the EU seeds — the 2026-06-24 DeFi stall). "Done" = the **metric
      moved in prod**, cross-checked vs the run.log terminal `exit_code` — never "job exited 0 / tests green" (the
      exit-0-but-empty blind spot). DoD: an overlap-vs-expected check is the wired completion verdict, not VM-gone/pass.
- [ ] [SCRIPT] P0. **Silent-cap source audit + FetchEvidence enforcement (§6.2/§6.5)** — for EVERY source, find + page
      PAST the truncating cap (Graph `skip`≤5000 → timestamp-cursor [done mtds@08b45468]; top-N daily snapshot →
      explicit instrument filter; REST page limit; vendor free-tier window). A cap that truncates the universe is a
      G1/G2 capture-correctness defect; its missing rows are **never** recorded `NOT_ENOUGH_TVL`/`SOURCE_RETURNED_ZERO`
      — the keystone `FetchEvidence`/`UnprovenHonestAbsenceError` gate enforced at every empty-write. DoD: per-source
      cap audited + paged-past; keystone gate green fleet-wide.
- [ ] [SCRIPT] P0. **Depth-aware re-fetch trigger (§7.5) — NOT blanket `--force`, NOT just unexpected-missing** —
      re-fetch ONLY `{missing/EU, attempted_failed, captured-but-instrument_count < expected_depth}` (the
      shallow-capture a plain skip-if-exists misses); needs the §2.1 depth oracle for `expected_depth`; the §2.2
      reconcile-vs-expected pass _discovers_ the set. DoD: a synthetic shallow `captured` cell is re-queued, a good full
      cell skipped, no blind whole-corpus `--force`.
- [ ] [DESIGN] P1. **Cost/entitlement-boundary reason class (§6.4)** — cells deliberately unfetched for cost (TradFi
      beyond-free Databento window, ~241k clipped) are a typed `KNOWN_SOURCE_GAP`/cost-boundary EXPECTED state in the
      §2.1 oracle — not `attempted_failed`, not silent absence — so coverage shows "available-but-intentionally-
      unfetched". DoD: reason class exists + the denominator accounts for it.
- [ ] [DATA] P0. **Canonical-form single-SoT GCS migration (IS + MTDS, every AG) — NO two sources of truth (operator
      2026-06-24).** Any GCS data in a non-canonical **schema** (schema*version < v9 / drifted fields), **path**
      (missing
      `pipeline_mode={mode}*{source}/`/`asset*group=`keys, legacy sibling trees, glued`PROTOCOL-CHAIN`), or **naming**     (asset_group not in `{cefi,defi,tradfi,sports,prediction}`lowercase · venue/chain not canonical — defi    `venue=PROTOCOL`+`chain=X` · instrument_id not canonical) is **MIGRATED to the one canonical form** — never a     dual-write / legacy tree left beside the canonical one. The **manifest (`\_index/availability_index`) must line up     with the coverage SSOT ↔ `/data-status`↔ deployment-UI** (the §2.3 reconciliation guard proves it ε=0).     **Single-walk discipline** — bundle schema/path/rename into ONE corpus walk per AG (a new whole-corpus walk is     review-blocking otherwise). **defi is the DONE exemplar** (this session: glued→canonical`\_index`reconcile +     legacy`dex_pools/`/`lending_indices/`sweep + the catalogue-filter cell-key alignment). Generalise to cefi ·     tradfi · sports + instruments-service. Reconcile with the existing canonicalisation cluster (don't fork):    `pipeline_mode_partition_migration`·`\*\_manifest_canonicalisation_2026_06_01`·`master_data_canonicalisation*
      migration_catalogue_2026_06_07`·`migration_verification_orphan_safety_2026_06_10`. DoD per AG: schema_version
      distribution == v9 (measured, not the constant) · a path-prober finds **0** legacy-shape objects · asset_group/
      venue/chain/instrument_id canonical · 0 dual-SoT sibling trees · manifest↔index↔data-status↔UI ε=0 (§2.3 guard
      green). **Runs per-AG inside G1→G3** (the manifest must be canonical + aligned BEFORE its coverage number means
      anything) — this is foundation-correctness, not cleanup.

🚦 **GATE 0 — operator sign-off on Phase 0 before any backfill launches.**

---

## Phase 1 — cefi (FIRST), gated G1→G5

- [ ] [SCRIPT] P0. **G1 — instruments-service correct per-day** (mtds/instruments-service): code right + deterministic +
      on LDR + QG-green; single-day re-run byte-reproducible; **junk/test symbols rejected** at capture; per-instrument
      fields (available_from, type, symbol, MVP, universe-tag) correct. DoD: a sample day audited cell-correct.
- 🚦 **GATE G1 — sign-off.**
- [ ] [INFRA] P0. **G2 — backfill cefi all venues × all days × all years** (observable BATCH, un-pause + verify the
      daily 08:30 capture). DoD: **`day_coverage = 100%`** (no day-gaps incl. 06-19/20/21); cumulative monotonic (zero
      drawdowns); weekly type+symbol completeness; universe depth (MVP+Expanded+Binance-stocks/commodities); cockpit
      click-through green.
- 🚦 **GATE G2 — sign-off.**
- [ ] [SCRIPT] P0. **G3 — aggregate + verify the scheduler runs the latest code** — `build_instrument_catalogue.py` via
      `lifecycle-catalogue-regen-cefi` (01:00 UTC); verify the Cloud Run **image == latest LDR/main**, fired today,
      produced today's `catalog.parquet`, no silent staleness. DoD: catalogue available_from/available_to/MVP
      sample-correct; scheduler proven on latest code.
- [ ] [SCRIPT] P0. **G3b — cefi DATED instruments: `available_to`=venue-truth + expiry oracle (§6.6/§7.3)** — cefi is
      not purely 24/7-binary: **Deribit options** + dated FUTURE on Binance/Bybit/OKX expire. So `available_to` =
      venue-truth expiry/`last_trading_date` (NOT last-seen — last-seen + the global-`latest_day` bug cause false
      delistings, §7.3), and the §2.1 expiry/listing-rule registry governs the per-day expected dated set (a contract
      the rules say existed but isn't captured = a provable gap). DoD: a sample Deribit/dated-future expiry ==
      venue-truth; no false delistings from a lagging-venue `latest_day`.
- 🚦 **GATE G3 — sign-off.**
- [ ] [SCRIPT] P0. **G4 — MTDS filters the catalogue per-day** — capture only catalogue-active-for-day instruments (no
      pre-listing, no post-expiry, no out-of-universe). DoD: spot-check MTDS attempts == catalogue-active-for-day.
- 🚦 **GATE G4 — sign-off, THEN resume cefi MTDS backfill (observable BATCH).**
- [ ] [SCRIPT] P0. **G5 — verify cefi MTDS coverage rises** (day+depth via SSOT) day-by-day; residual gaps each have a
      typed understood reason. DoD: coverage trends up; no new unexplained honest-absence/failed.
- 🚦 **GATE G5 — sign-off; cefi DONE.**

---

## Phase 2+ — defi · tradfi · sports (same G0→G5, after cefi DONE)

- [ ] [INFRA] P1. **defi** — same gates; `window=expected, per-date-TVL=captured` 3-way (§1.3/§2.1: captured /
      `EXPECTED_NOT_ENOUGH_TVL` / `SOURCE_RETURNED_ZERO`); on-chain pool-creation genesis; **G4 catalogue-as-filter is
      load-bearing** (capture the catalogue pools in-window per (venue,chain,date), NOT the subgraph top-N — the cause
      of the 2026-06-24 overlap-flat stall); per-date TVL enumeration must be COMPLETE (316-vs-1,425 under-enumeration =
      G1/G2 defect); every catalogue protocol×chain has a source wired (uncovered: TRADER_JOE_V2/UNISWAP_V4/ORCA/KAMINO/
      VELODROME_V2/RAYDIUM = G1 gap); dual-form id (canonical `0x` key + glued `glued_pair_id`). **Execution detail +
      live work**: `plans/active/defi_instrument_catalogue_and_capture_pipeline_2026_06_23.md`.
- [ ] [INFRA] P1. **tradfi** — same gates; Databento universe (GLBX/DBEQ/XCBF) + Yahoo (KRX/FX). ("tradfi perps" =
      Binance single-stocks/commodities are **cefi**.) DeFi-distinct tradfi work (§7): **billable-venue guard** —
      enumerated venues == subscribed allowlist (ICE non-billable, 8,856→1; §7.1); **fail-closed per-venue calendars +
      sessions** (KRX in NO calendar SSOT → 24/7 default mis-handles Seollal/Chuseok; FX is the declared 24/7 exception;
      §7.2); **`available_to` per-venue + trading-day-aware** (global-`latest_day` falsely delists lagging KRX; §7.3);
      **equities pre-2023-04-15 silently absent**; **depth oracle** (NASDAQ ~41 / NYSE ~224 shallow); verify the tradfi
      daily-capture trigger isn't PAUSED. Baseline §9.
  - **Already-fixed G1 code (this session, IS `50bf1c8`, QG-green, 7/7 venues now write):** KRX→databento routing
    (`CANONICAL_VENUE_TO_ADAPTER`) + the `AssetClass("cefi")` crash on NASDAQ/NYSE equities (`_resolve_asset_group`
    guarded so domain values fall through to the dataset-default EQUITY). **Remaining G1 refinements (NOT yet done):**
    (i) the cefi-domain equity-perp singles (NVDA/MSFT/AAPL…, `DatabentoInstrumentDef.asset_group="cefi"`) currently
    resolve to EQUITY and **stay in the tradfi pipeline** — per the registry-comment intent ("keeps them out of the
    tradfi data pipeline") they must be **EXCLUDED** from the tradfi adapter (they belong to cefi), not just un-crashed;
    (ii) `_DATASET_TO_asset_group["XCBF.PITCH"]=EQUITY` + XCBF absent from `_FUTURES_DATASETS` — VX are FUTURE (the
    `instrument_type` lands FUTURE, but the asset-class map is wrong → fix to FUTURE/COMMODITY).
- [ ] [INFRA] P1. **sports** — same gates; **fixtures ARE the instruments**, universe = the **~101 canonical MVP
      leagues** (`LEAGUE_REGISTRY`); api_football is the fixture-catalogue source + genesis; enrichment sources
      (footystats/ understat/transfermarkt/open_meteo/sfi) layer OFF the canonical fixtures (per-source coverage = a
      SUBSET → honest absence, not failure). Season/competition calendar = the per-day "expected" (off-season
      honest-empty, not a gap). Sports-specific foundation work (audit 2026-06-24, §3 of the standard):
  - [ ] [DATA] P1. **G1 MVP-scope — delete the non-canonical league NOISE.** api_football FIXTURES enumerated **1,531
        leagues (94 canonical + 1,437 non-canonical = ~106k rows, incl. 27.5k captured-we-don't-care-about)**. Scope the
        expected-universe enumeration to the ~101 canonical leagues; wipe the 1,437 non-canonical (rows + objects,
        snapshot-first / consolidator-paused). A non-MVP league in the manifest is a G1 enumeration bug. Also: **7 of
        the 101 canonical leagues have ZERO fixtures rows** (registry/enumeration gap — diagnose).
  - [ ] [DATA] P1. **G2 diagnose the 2015–2017 ZERO-captured.** Canonical FIXTURES are **0 captured for 2015–2017**
        (35,889 all-`empty_confirmed` across 76 MVP leagues that demonstrably played). One direct api_football probe
        (e.g. EPL 2016) decides: real subscription/tier history limit (→ honest absence, fix `SOURCE_COVERAGE_START`) vs
        backfill-bug (→ **scoped `--force`** re-run of 2015–2017 — `empty_confirmed` is skip-existing's blind spot,
        §2.2). Do this BEFORE trusting any sports coverage number.
  - [ ] [DATA] P1. **G2 re-run the 40,041 FIXTURES `attempted_failed`** (2018/2021/2023 clusters — a quota/rate-limit/
        endpoint pattern during those backfill runs). **Normal re-run** (failed = "missing"), NOT blanket `--force`.
        This is where the api_football credits should go — not a re-fetch of the 51,657 good captured cells.
  - [ ] [CODE] P2. **Per-source honest-absence via `is_league_entity_covered`** — extend the coverage map to understat
        entities (XG/XG_SHOTS) so the understat error branch records `EXPECTED_NO_PROVIDER_COVERAGE` for non-covered
        leagues (the canonical 3-way). The 2-way shipped (instruments-service@18398c8) is interim-correct because the
        expected set is already source-filtered. Tracked: remediation #2c.
  - [ ] [DATA] P2. **Odds = MTDS, NOT IS** — wipe the misplaced IS footystats `ODDS` (194,789 rows; KEEP `PREDICTIONS`
        in-house) + drop `"ODDS":"footystats"` from the source map + remove the IS odds-capture path. odds-api in MTDS
        is canonical (211,299 captured / 0 failed; api_football MTDS odds wiped 2026-06-24 — 1.4M rows + 231,532
        objects). Tracked: remediation #6.
  - [ ] [DESIGN] P1. **`depth_coverage` Tier-B = the FIXTURE-COMPLETENESS ORACLE** (n_teams→expected_fixtures, per-team
        game count, promotion/relegation, season window + expected gaps, **reschedule = final kickoff time**). The
        sports realisation of §2.1's external-truth denominator. SSOT plan:
        `plans/active/sports_fixture_completeness_oracle_2026_06_24.md`.
  - [ ] [SCRIPT] P1. **Reuse the Phase-0 cross-cutting machinery** — phantom-reconcile-vs-expected (the candidate-path
        #5 gap heals the 3,164 golden-window phantom false-failures, incl. 3,003 TEAMS, with ZERO fetch via
        `--unphantom-only` once #5 lands); the `DP_HIGH_ATTEMPTED_FAILED` alert (deployment-service@cb330f7,
        MissTracker-gated); depth-aware re-fetch (§7.5); observability (§0.5).
- [ ] [INFRA] P1. **Retirement completeness (§8) — every AG, all 4 legs** (code+exclusion-marker / GCS snapshots /
      manifest rows / surfaces). A retired thing is done only when gone from catalogue/`/data-status`/UI, not just
      de-enumerated. Known live pollutants (2026-06-24): tradfi **ICE** (whole-venue), **CBOE** 91 SPOT_PAIR + 5
      un-deleted INDEX (VIX cash — adapter still creates it) + 9 stray VX; cefi-domain equity-perp singles if any. DoD:
      each pollutant verified absent on all 4 legs (pause-consolidator → snapshot → filter → resume for the manifest
      leg).

---

## Operator gates (the sign-off points — ask every time)

GATE 0 (Phase 0 done) · G1 · G2 · G3 · G4 · G5 per AG. No gate is crossed without operator sign-off. No parallel-up
across gates within an AG.

## Codex SSOT updates

- `codex/02-data/instruments-foundation-and-catalogue-completeness.md` (the standard) — this plan executes it; now spans
  §0 gates · §0.5 observability-precondition · §1 completeness (incl. §1.2 cumulative-drawdown) · §2 layered coverage +
  §2.1 oracle (cefi/tradfi expiry-rules + DeFi TVL) + §2.2 reconcile + §2.3 drilldown-correctness · §6 DeFi/TradFi
  cross-AG borrows · §7 tradfi/cefi-dated nuances (billable-venue, calendars, available_to, Tier-B, depth-aware
  re-fetch) · §8 retirement-completeness · §9 tradfi baseline. Keep this plan's todos in lockstep as the standard
  evolves.
- CLAUDE.md: add a one-line pointer to the standard.
- Compose: `availability-manifest-and-data-status.md` (expected-universe materialisation) ·
  `deployment-observability.md` (§0.5) · `honest_coverage_formula_consolidation_2026_05_19.md` (SSOT) ·
  `foundation-completion-gate-discipline.md` · `defi-canonical-naming-ssot.md` (defi) ·
  `tradfi-databento-sourcing-ssot.md` (tradfi allowlist).

## Related execution plans (per-AG detail lives here; this plan is the cross-AG umbrella)

This plan is the gated umbrella standard. The per-AG execution detail — where an AG has its own active plan — lives in:

- **defi** — `plans/active/defi_instrument_catalogue_and_capture_pipeline_2026_06_23.md` (the G4 catalogue-as-filter
  exemplar + the live skip-cap/cursor + per-pool capture work).
- **sports** — `plans/active/sports_fixture_completeness_oracle_2026_06_24.md` (the §2.1 Tier-B fixture-completeness
  oracle) + `plans/active/sports_golden_window_attempted_failed_remediation_2026_06_24.md` (the failed/phantom
  remediation).
- **cefi / tradfi** — detail is inline above (no separate active plan).

Per-AG plans MUST stay consistent with this umbrella's gates (G0→G5) + §0–§9 of the standard; this plan is the SSOT for
the _process_, those for the _AG-specific execution_.

## Progress log

- 2026-06-25 — **DeFi foundation migration STARTED (opus autonomous, full operator authority; DeFi drained — verified 0
  running defi backfill VMs, only cefi-live/tradfi/prediction/watchdog run, none write the defi buckets).** Ground-truth
  re-audit (read-only) corrected several stated-start figures: the IS PRD `_index` is **187,850 rows** (NOT 7,362 — that
  was the catalogue), with TWO populations — `data_type=instrument-catalog` (145,467 venue-day rows) + blank-data_type
  (42,383 per-instrument-type rows, stale-stops 2025-02-01, incl. **119 cefi `EXTENDED-STARKNET` contaminants**). The
  ENVLESS dual bucket (145,467) is exactly PRD's instrument-catalog subset (stale projection). **Canonical-form conflict
  RESOLVED** (Findings-Triage big): UAC `ALL_DEFI_VENUES` is glued-only, but the deployment-api drilldown
  (`data_status/defi.py`) splits each registry entry into `(PROTOCOL,CHAIN)` and matches the manifest's **bare
  `venue=PROTOCOL`+`chain=X`** (its `_is_legacy_defi_venue_row` drops glued+blank-chain as legacy) → **bare+chain is
  unambiguously canonical**; the registry does NOT need flipping; `canonicalize_defi_manifest_venue_2026_06_14.py`
  (canonicalizes to GLUED) is SUPERSEDED by this collapse.
  - **Step 1 SNAPSHOT ✅** — IS PRD/ENVLESS `_index` + catalogue + MTDS defi `_index` → `_index/snapshots/
    pre_migration_2026_06_25.parquet` (+ `prod/snapshots/catalog.pre_migration_2026_06_25.parquet`). Regression baseline
    fingerprints (per venue×data_type captured counts) recorded. KEY INVARIANT: IS PRD captured **cells** = 174,926.
  - **Step 2 COLLAPSE ALL drift → bare canonical ✅ APPLIED** (`instruments-service/scripts/
    collapse_defi_drift_to_canonical_2026_06_25.py`, ruff-green; per-blob `.driftcanon.bak`). before→after, live prod:
    `_index` 187,850→176,186 rows, **glued 76,904→0, ghost 0→0**, chain 100% populated, captured **cells** 174,926→174,926
    (ε=0; 11,664 dropped rows were glued+bare twins of the SAME canonical cell, merged captured-wins);
    `prod/catalog.parquet` glued 1,001→0, ghost 197→0, chain 100% populated; `_index/per_vm/_legacy_seed` glued/ghost→0.
    Caught+fixed a dedup bug mid-build (first version kept BOTH captured twins → duplicate canonical cells; fixed to
    one-row-per-cell, status-priority captured>empty>failed>EU, richest instrument_count; ε=0 asserted on captured CELLS).
  - **Root-cause located** for the glued treadmill: `instruments_service/engine/orchestrator/writers.py::_write_venue`
    — the MANIFEST column split (parse_defi_venue → bare venue+chain) is already correct in current code, but the **GCS
    by_date PATH partition (line 113) still writes glued `venue=AAVE_V3-ARBITRUM/`** (uses `venue_str`, not the split).
    Path-split root fix + the GCS path migration are the next units (Step 5). cefi `EXTENDED-STARKNET` (119) purge =
    retirement item. STILL TODO before backfill: root path-fix code (quickmerge) · junk `1970-01-01` genesis +
    mixed-type `available_from` normalize · one-bucket (retire ENVLESS) · venue-truth genesis · recency 06-22→today ·
    6 uncovered-venue subgraphs · clean backfill.
- 2026-06-24 — Reset to foundation-first (operator). cefi MTDS paused. cefi + tradfi instruments ground-truth audits
  done (read-only). Codex standard drafted + heavily enriched (gated order · observability precondition · layered
  coverage · expected-universe oracle · cumulative-drawdown · DeFi-TVL · §6 cross-AG borrows · §7 tradfi/cefi-dated
  nuances · §8 retirement · §9 tradfi baseline). This plan filed + completed to match the standard (Phase-0
  §6/§7.5/cost-boundary items; cefi G3b dated-instruments; expanded defi/tradfi/sports + retirement; tradfi+defi
  starting state). **Awaiting GATE 0 sign-off.**
- 2026-06-24 — defi: catalogue/manifest correctness-clean + the skip-cap cursor fix shipped (mtds@08b45468); G4
  catalogue-as-filter implementation IN FLIGHT (overlap-flat until it lands) — tracked in the DeFi plan, the G4 exemplar
  for this standard.
- 2026-06-24 — **tradfi audit + the foundation-first PIVOT (this session).** Started as the KRX/equities OPS pass; the
  operator's "how do we know instruments is honestly at coverage" probe surfaced the foundation gaps → reset to
  audit-first. **Shipped G1 code:** KRX routing + the cefi-`AssetClass` crash (IS `50bf1c8`, 7/7 venues write). **Audit
  findings** (now §9 + the tradfi todos above): ICE non-billable yet enumerated (8,856→1); CBOE pollution (91 SPOT_PAIR
  - 5 un-deleted VIX-INDEX); KRX 96% silently absent + no Korea calendar; `available_to` false-delistings (global
    `latest_day`); equities pre-2023 absent; shallow NASDAQ/NYSE. **PAUSED everything** (operator "no point wasting time
    and money"): catalogue-regen execution **cancelled** (it would have baked false KRX delistings, §7.3),
    `uts-prod-tradfi-wave-launcher-cron` **paused**, the 18 `tradfi-bf` OHLCV VMs **deleted**; live producer +
    non-tradfi VMs left. **Nothing builds downstream until G1 fixes land + GATE-0/G1 sign-off.** (Separate + still LIVE:
    the tradfi market-data EU-drain fix — massive purged, EU collapsed 1.08M→1,349 MVP, durable — not part of this
    foundation gate.)
- 2026-06-24 — **sports audit + manifest-correctness pre-staging (this session).** Operator clarified the sports model
  (fixtures = instruments; ~101 canonical MVP leagues; per-source coverage = a subset → honest absence; **odds = MTDS
  not IS**, the footystats exception being in-house `PREDICTIONS`). Read-only audit found the G1/G2 holes (1,531-vs-101
  league noise; 2015–2017 zero-captured; 40k FIXTURES failures) — now §3 of the standard + the sports todos above.
  Shipped this session (manifest-correctness, ahead of the gated rebuild): #1 phantom pipeline_mode fix, #2 understat
  2-way 404, #3 api_football MTDS odds wipe (1.4M rows / 231,532 objects; trades 100%/0-failed), #4
  DP_HIGH_ATTEMPTED_FAILED alert. Standard updated (codex §3 sports) + the fixture-completeness oracle plan filed.
  **Sports G1→G5 still gated behind cefi DONE.** OPEN: MVP-scope delete of the 1,437 non-canonical leagues; 2015–2017
  real-vs-bug diagnosis; 40k-failure re-run; #5 candidate_parquet_paths path-shape fix (unblocks the 3,164-phantom
  heal); #6 IS-odds wipe.
- 2026-06-25 — **cefi Phase-0 execution session START (this session, opus autonomous).** Re-confirmed clean LDR across
  IS/MTDS/UAC/UTL/deployment-{service,api,ui}/PM. Mapped the 6 Phase-0 surfaces (read-only) + GCS ground-truth (duckdb
  on the live cefi manifest + catalogue). **Findings that pin the cefi build:**
  - **day-gaps WIDENED:** cefi instruments `by_date/` day-dirs = 0 for **06-19/20/21 AND 06-24** (and 06-25 in progress)
    — the audit's 3 gaps are now 4; the daily 08:30 trigger is still paused. Even "present" days are partial (06-15/16 =
    8 venue-rows; 06-22 = 18; 06-23 = 20; vs ~21 full) — capture is unreliable, not just gappy.
  - **expected-universe is NOT materialised in the cefi INSTRUMENTS manifest** (`_index/availability_index.parquet`,
    62,137 rows, grain = per-(venue,day) with `instrument_count`): capture_status = 62,091 `captured` + 46
    `attempted_failed`, **ZERO `expected_unattempted` / ZERO `empty_confirmed`**. So the gap days are simply ABSENT (not
    seeded 0%), and coverage = captured/(captured+failed) ≈ 99.9% = the dishonest blind number. **day_coverage fix =
    seed expected_unattempted for every (venue, missing-day) genesis→today.** (NB: the expected-universe-v2-cefi
    enumerator seeds the MTDS market-data manifest, not this instruments-capture manifest — IS day_coverage needs its
    own venue-day EU seeding.)
  - **canonical-form (operator directive) — cefi INSTRUMENTS manifest is already largely canonical:** asset_group=all
    `cefi`, schema_version=all `9`, venue=UPPER, pipeline_mode=`batch_instruments_service`,
    service_name=`instruments- service`. Gaps: 24 blank-`source` rows; `data_type` all-blank (confirm intended for the
    instruments venue-day grain). **market-tick-data cefi bucket NOT yet audited for canonical form** — next.
  - **§7.3 false-delistings are LIVE in the catalogue** (`prod/catalog.parquet`, 227,576 rows, built 06-24T01:09 when
    global `latest_day`=06-23): `available_to=2026-06-18` stamped on **1,118** instruments (+943 @06-11, +long tail) —
    instruments last-seen on the last full day before the gap, falsely delisted by last-seen + global-latest_day.
    Confirms §7.3 bug A (last-seen not venue-truth) + B (global not per-venue latest_day). instrument_type: OPTION 146k
    / COMBO 67k / FUTURE 5.8k / SPOT_PAIR 4.8k / PERPETUAL 3.9k; mvp 157,092 T / 70,484 F.
  - **deployment-observability is largely BUILT** — `classify_deployment_target`,
    `cloud_run_job_registry.CLOUD_RUN_JOBS` (has
    `lifecycle-catalogue-regen-cefi`/`manifest-consolidator-cefi`/`expected-universe-v2-cefi` BATCH),
    `VM_PREFIX_TO_BUCKET` (`instr-backfill-cefi-`/`mtds-backfill-cefi-` EPHEMERAL_BATCH), `dp-exit-code-monitor`/
    `dp-heartbeat-watcher`/`dp-meta-watchers`, `/api/deployments/inventory`+`umbrella/{u}/summary`. Phase-0
    observability item = VERIFY the cefi launchers actually emit
    ServiceBootstrap/log_event/heartbeat/persist-exit_code + click-through in the cockpit (not assumed).
  - **G4 catalogue-as-filter for cefi is already substantially built** — `CeFiCatalogReader` +
    `catalog_list_instruments("cefi",date,date)` in MTDS `sentinels.py` reads `prod/catalog.parquet`, filters
    active-on-day + MVP-perp-gate; DeFi `_catalogue_filter.py` exemplar exists. G4 is mostly validation, not new build.
  - **compute_honest_coverage SSOT = single float** (`CaptureStatusCounts`→numerator/denominator, out_of_window clip);
    **no day/depth split, no reconciliation guard** → both are Phase-0 net-new. UI renders the SSOT value verbatim (no
    client recompute) ✓. **Build sequence (bottom-up T0→consumers):** (1) layered coverage SSOT day+depth in UAC +
    surface deployment-api/UI; (2) IS expected-universe DAY seeding (venue-day) + depth-expected; (3)
    cumulative-drawdown metric; (4) §7.3 available_to venue-truth + per-venue latest_day fix; (5) consolidation
    reconcile-vs-expected; (6) drilldown-correctness guard; (7) observability verify; (8) canonical-form audit
    MTDS-cefi. Driving unit-by-unit, QG+quickmerge+flip each, surfacing at GATE 0. **Awaiting GATE 0 sign-off before any
    backfill launch.**
- 2026-06-25 — **TRADFI track dispatched directly (operator), slot-3.** Sequencing: tradfi G1→G5 driven NOW (ahead of
  cefi-first ordering — the documented intent for this dispatch); reversible work driven to done, expensive/irreversible
  (G2 fleet launch, real-GCS purge) HARD-PAUSE for operator confirm. Composes with the Phase-0 canonical-form single-SoT
  migration item (above) — tradfi is one AG of it.
  - **Read-only audit of `prod/catalog.parquet` (814,011 rows) + `by_date/` + code — full tradfi pollutant inventory,
    root-caused, each fix STOPS it at source; stale rows = retirement (operator-confirm GCS purge):** daily-capture is
    BROKEN (`by_date/day=2026-06-24/` = ONLY `venue=CME`, 1 of 7 venues). Pollutants (cumulative catalogue counts): ICE
    COMBO+FUTURE BRN-Brent **16,157** (stale avail_to=2023-12-21; IFEU/IFUS non-billable maps) · ICE INDEX DXY **1** ·
    CBOE OPTION OPRA-SPX `O:SPX…` **33,258** (stale; OPRA non-billable) · CBOE SPOT_PAIR VX-spreads
    `VX/F1:1:S - VX/G1:1:B` **4,216** (ACTIVE; XCBF class-S→SPOT_PAIR) · CBOE INDEX **6** (^VIX, I:VIX,
    ^IRX/^FVX/^TNX/^TYX) · NASDAQ/NYSE SPOT_PAIR **102/216** (ACTIVE; DBEQ class-S equity-spot mis-typed) · cefi-singles
    in EQUITY (NVDA/MSFT/AAPL/CRCL/INTC/GOOGL/AMD/ TSLA/AMZN/META/HOOD/BABA, mvp=True; 50bf1c8 fixed only the crash NOT
    exclusion) · VX FUTURE asset_group=EQUITY **82** (should be COMMODITY) · `available_to`
    global-`latest_day`/last-seen bug (all →2026-06-23; VX/F7 falsely active) · MVP broken (895/814,011 True; VX futures
    all False) · KRX/FX in NO calendar SSOT (`is_non_trading_day` fails-OPEN → silent 24/7 → Korean holidays
    mishandled).
  - **MACRO-INDEX / CURRENCY decision (operator clarifications 2026-06-25):** (1) "DXY canonical along with KRWUSD as
    the currencies daily from Yahoo, **not one-offs**" → **KEEP + canonicalise** DXY (re-home venue ICE→**FX**,
    asset_group=fx)
    - KRWUSD (already FX) + the treasury-yield rate indices ^IRX/^FVX/^TNX/^TYX (Yahoo daily macro rates, venue=CBOE
      issuer-correct, asset_group=fixed_income). Yahoo daily series have NO billing issue → they stay (the §7.1
      yahoo-allowlist generalises beyond `{KRX,FX}` to the canonical Yahoo daily currency/macro series — codex §7.1 to
      update). (2) **REMOVE only VIX cash** (^VIX Yahoo + I:VIX OPRA) — redundant, VX futures cover VIX-15m
      (`is_vix_15m_gap_date` always False). (3) "**ICE is databento billing-blocked → purge EVERYWHERE**" → the ICE
      Databento BRN-Brent (16,158) purged across by_date + manifest + catalogue + surfaces; DXY moves off ICE so ICE
      venue is GONE. (This REVERSES the earlier "drop all YAHOO_INDICES" reading — DXY/treasuries/KRWUSD are
      canonical-keep.) DEPTH todo: expand the Yahoo currencies universe beyond DXY/KRWUSD ("not just one-offs").
  - **TRADFI G1 code checklist (slot-3; tradfi-databento files = NON-colliding with the cefi agent; the AG-agnostic
    `build_instrument_catalogue.py` §7.3 `available_to`/per-venue-`latest_day` fix is the cefi agent's item 4 — SHARED,
    coordinate, one fix covers both AGs):**
    - [ ] [SCRIPT] P0. **G1.a billable-venue guard (§7.1)** — `assert_databento_request_allowed` enum gate
          (adapter.py) + strip non-billable datasets (IFEU/IFUS/OPRA/XNAS.ITCH/XNAS.BASIC/XNYS.PILLAR) from
          `_DATASET_TO_VENUE`/ `_DATASET_TO_asset_group`/`_FUTURES_DATASETS` (symbology.py) + exclusion marker.
    - [ ] [SCRIPT] P0. **G1.b exclude cefi-domain equity singles** — filter curated defs where `asset_group ∉` valid
          `AssetClass` (the cefi/defi cross-domain marker), adapter.py `get_instruments`.
    - [ ] [SCRIPT] P0. **G1.c XCBF.PITCH = FUTURE/COMMODITY + outright-only** — UAC `_CFE_FUTURES` VX.FUT "equity"→
          "commodity"; `_DATASET_TO_asset_group["XCBF.PITCH"]`→COMMODITY; drop XCBF non-outright (class-S VX spreads).
    - [ ] [SCRIPT] P0. **G1.d DBEQ.BASIC class-S → EQUITY** (not SPOT_PAIR) on equity venues.
    - [ ] [SCRIPT] P0. **G1.e calendars+sessions FAIL-CLOSED** — declare KRX (XKRX cal + KST) + FX (24/7 explicit) +
          raise for an undeclared tradfi venue (sessions.py).
    - [ ] [SCRIPT] P0. **G1.f macro/currency canonicalise** — UAC `YAHOO_INDICES`: remove VIX; DXY venue ICE→FX; keep
          treasuries (fixed_income); doc as canonical Yahoo daily currency/macro series.
    - [ ] [SCRIPT] P1. **G1.g MVP tags on the tradfi MVP universe** (VX futures + basis tickers).
    - [ ] [SCRIPT] P0. **G1.h §7.3 `available_to` venue-truth + per-venue `latest_day`** —
          `build_instrument_catalogue.py` (SHARED with cefi item 4; coordinate — do NOT double-edit).
    - [ ] [INFRA] P0. **G1 retirement (§8, 4 legs) — OPERATOR-CONFIRM before purge** — ICE (whole venue, 16,158) · CBOE
          OPRA OPTION (33,258) · CBOE VX-spread SPOT_PAIR (4,216) · VIX-cash INDEX (^VIX+I:VIX) · NASDAQ/NYSE mis-class
          SPOT_PAIR (318) · cefi-singles. Pause consolidator→snapshot→filter→resume; verify gone all 4 legs.
- 2026-06-25 — **cefi VM-drain for the canonical-form migration (operator-directed, this session).** Operator flagged
  cefi backfills running before the foundation code lands (G4/G5-before-G1–G3 + would write against the buggy catalogue
  + race the canonical-form migration). **STOPPED (graceful, reversible — process killed, not deleted):**
  `cefi-binance-futures-2020-heavy-20260624-222326` (cefi MTDS market-data backfill) ·
  `cefi-hyperliquid-2024-20260623-113700` (cefi MTDS backfill, 1.5d-running) ·
  `mtds-perp-funding-backfill` (tagged `VM_ASSET_GROUP=DEFI`/`defi-backfill` but cefi-named + servicing cefi funding —
  the cross-AG-servicing-cefi case). Operator decision: **cefi-scoped drain + any cross-AG VM servicing cefi stopped +
  per-AG VMs only going forward.** LEFT RUNNING (other active agents' single-AG work, per cefi-scope): ~15
  `mtds-live-cefi-*` LIVE producers (decide after auditing whether cefi market-data bucket needs migration — they write
  it continuously), 16 `tradfi-bf-*` + `tradfi-fwd-daily-cron` (slot-3 tradfi track), `instr-backfill-defi` +
  `defi-fwd-oracle-prices-poll` + `mtds-dex-*` (defi agent), `prediction-live-*`, `sports-ref-v3-*`. **Finding (per-AG
  VM hygiene):** `mtds-perp-funding-backfill` (DEFI metadata, cefi-name, no AG prefix) + the untagged `defi-fwd-*`/
  `tradfi-fwd-*`/`mtds-dex-*` pollers (no `VM_ASSET_GROUP`) are the cross-AG/untagged anti-pattern the operator named —
  launchers must set `VM_ASSET_GROUP` + an AG-prefixed name; tracked under the canonical-form/observability items.
- 2026-06-25 — **cefi Unit-1 (UAC layered coverage SSOT) built.** `LayeredCoverage` NamedTuple +
  `compute_layered_coverage(day_counts, depth_counts)` — both layers via the single `compute_honest_coverage` so day +
  depth can never diverge from the formula the UI renders (instruments-foundation §2). Re-exported through
  `honest_coverage.py` + root `__init__.py` + `__all__`; 3 unit tests (both-via-SSOT, day-green/depth-low thin-day
  signal, missing-days-drag-day-coverage). Also fixed a PRE-EXISTING UAC-LDR red blocking ALL UAC (T0) promotion:
  `kalshi_trades_ws`/`polymarket_trades_ws` WS connectors landed without a `_CONNECTOR_TO_VENUE` entry → 2 failing
  coexistence tests; added the 2 mechanical map entries (both venues already carry a `*_ws.yaml`). Shipping next.
- 2026-06-25 — **cefi Unit-1 SHIPPED + cefi canonical-form audit + market-data dual-SoT cleanup.** Unit-1 (UAC
  layered-coverage SSOT + UAC-LDR red fix) landed **UAC@755c40515** on live-defi-rollout (strict-quickmerge clean;
  Tier-C drain → staging ≤15min). **Canonical-form audit (operator directive — cefi instruments + market-data GCS):**
  - **cefi INSTRUMENTS** (`instruments-store-cefi-prd`): manifest already canonical (asset_group=cefi · schema_version=9
    · venue UPPER · pipeline_mode=batch_instruments_service); residual = 24 blank-`source` rows + `data_type` all-blank
    (likely intended for the instruments venue-day grain — confirm). Raw path
    `instrument_availability/by_date/day={D}/venue={V}/instruments.parquet` carries no `pipeline_mode=`/`asset_group=`
    path-key — but for reference-data (one bucket per AG, single source `batch_instruments_service`) that is
    canonical-by-design (the keys are manifest COLUMNS). No instruments migration needed.
  - **cefi MARKET-DATA** (`market-data-tick-cefi-prd`): **canonical tree is CORRECT** —
    `raw_tick_data/by_date/day={D}/pipeline_mode={mode}_{source}/asset_group=cefi/venue={V}/…` (live_binance/bybit/
    deribit/hyperliquid/kraken/okx + batch modes); `processed_candles/by_date/day=…` clean (0 orphans). **DUAL-SoT FOUND
    + FIXED:** 9 stray flat `raw_tick_data/by_date/<symbol>.parquet` (AVAXUSDT/BTC-28MAR25/BTC-PERPETUAL/BTCUSDT/
    ETH-PERPETUAL/ETH-USD-250328/KRW-LINK/SOL-ETH/TRX-USDT), all stamped **2026-05-12T17:01** = the pre-`day=`/
    `pipeline_mode=` flat layout that the ~05-12 path migration rewrote into the canonical tree but **never deleted the
    source** (manifest-invisible → never in coverage). **Snapshotted → `_index/backups/orphan_flat_files_pre_sot_
    cleanup_2026_06_25/` then PURGED** → 0 flat orphans remain, 2,645 canonical `day=` dirs intact. Single-SoT restored.
  - Remaining canonical-form work (the tracked Phase-0 single-SoT item, runs in cefi G1–G3): full schema_version
    distribution of the 144MB market-data `_index` (measured, not the constant) · venue/instrument_id casing across the
    market-data manifest · the §2.3 ε=0 reconciliation guard wiring · the 24 blank-source / all-blank-data_type
    instruments residual. cefi canonical-form is otherwise GREEN (no further dual-SoT pollution found).
