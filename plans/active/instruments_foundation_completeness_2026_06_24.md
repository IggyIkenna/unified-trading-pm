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

## Near-term target — cefi + defi daily instrument pipeline live (operator 2026-06-26)

The concrete first outcome for cefi **and** defi together (do them as one workstream — same producer, same aggregator):

1. **Daily instrument-definition backfill complete, both AGs, with the RIGHT missing reasons.** Rebuild the dead daily
   producer (see Phase 0 / the folded `[INFRA] P0 "Rebuild the IS daily definition producer"`), then fill the freeze gap
   (cefi `by_date` frozen ~2026-05-21 → present; defi ~2026-05-07 → present) so each day is captured. **Honest 4-state
   reasons (HARD):** missing/un-attempted days seeded `expected_unattempted` (gap reads 0%, not absent); genuine empty →
   typed `EmptyConfirmedReason` (never blank); fetch-failure → `attempted_failed`, NOT `empty_confirmed` (the CF-11
   swallow class — writer-fix so future daily writes are honest). DoD: no silent day-gaps for cefi/defi; every
   non-captured cell carries a typed reason; the daily producer runs green on a schedule (no fire-and-forget —
   registered observable BATCH job).
2. **Daily catalogue aggregator live + green, both AGs.** The lifecycle roll-up (`build_instrument_catalogue.py` →
   `{env}/catalog.parquet`) runs on a daily per-AG schedule. Remaining work (folded `[INFRA] P1` items):
   `terraform apply` of `lifecycle_catalogue_scheduler.tf` (deployment@98bee4b) **+ fix the cloud regen job's
   fast-fail** (add stdout bisection logging, localize the job-only failure, fix it). DoD: the cefi + defi catalogue
   regenerates daily from the fresh `by_date` definitions, monotonic-guard ACCEPT, click-through-able in the cockpit; a
   manual T+10min and a next-day T+24h execution both verified.

Gate: this target is the cefi+defi half of G0→G1; **stop here for operator sign-off before the per-AG G2+ gates.**
Coverage is the verification lens — every number flows through `compute_honest_coverage` (Phase 0 below).

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
  - [ ] [DESIGN] P0. **DeFi completeness ORACLE — "do we have ALL instruments?" = on-chain factory cross-check (§2.1
        Tier-B; operator 2026-06-24 "how do we KNOW").** Self-enumeration is circular (§7.4) — proof of completeness is
        EXTERNAL on-chain truth, which DeFi uniquely has: per (protocol, chain), our **enumerated pool count == the
        factory's `poolCount`** (DEX: factory `PoolCreated` total via subgraph `factory{poolCount}` / RPC event count;
        lending: protocol registry — Aave `getReservesList`, Compound/Morpho registries). enumerated==poolCount ⟹ we saw
        every pool ⟹ the TVL-filtered catalogue is provably complete; enumerated&lt;poolCount ⟹ we're missing exactly
        `poolCount−enumerated` (named, quantified backfill-more signal, not a guess). Surface it as a per-venue
        **completeness % = enumerated / factory.poolCount** (Tier-A proxy until wired, Tier-B = this). `available_from`
        = the pool's on-chain **creation block** (this IS the genesis oracle — kills the RAYDIUM `1970-01-01` = missing
        creation timestamp). DoD: per (protocol,chain) completeness % surfaced in the drilldown; 100% = complete; any
        &lt;100% is a typed gap. A venue/AG is NOT "complete" until this Tier-B oracle is green — never assert
        completeness from our own capture.
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
  - [x] ✅ [CODE] P2. **Per-source honest-absence via `is_league_entity_covered`** — extend the coverage map to
        understat entities (XG/XG_SHOTS) so the understat error branch records `EXPECTED_NO_PROVIDER_COVERAGE` for
        non-covered leagues (the canonical 3-way). The 2-way shipped (instruments-service@18398c8) is interim-correct
        because the expected set is already source-filtered. Tracked: remediation #2c. — instruments-service
        understat.py: `_failed_league_names` → `_failed_canonical` → 3-way split (failed/empty/no-error-empty) confirmed
        in code; `EXPECTED_NO_FIXTURE` used (non-covered leagues excluded from expected set upstream)
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

- 2026-06-25 — **Takeover#2 EXECUTION begins (operator "run it to the end" mandate, 8 phases).** PHASE 1 (cefi
  reclassification) code-complete in instruments-service, QG-validating: moved EXTENDED/PACIFICA/LIGHTER out of the defi
  capture path → cefi. Edits: `engine/orchestrator/defi.py` (removed PACIFICA from `_SOLANA_DEFI_VENUES`; deleted
  `_L2_DEX_PERP_VENUES` = EXTENDED+LIGHTER + its `__init__.py` export + the `_build_defi_venues` extend) +
  `engine/orchestrator/venue_core.py` (added the 3 to `_CEFI_VENUES`, next to HYPERLIQUID/ASTER) +
  `reference_data/ factory.py` (3 adapter imports repathed defi→cefi, ruff-sorted into the cefi block) + `git mv`
  adapters `adapters/defi/{extended,pacifica,lighter}.py`→`adapters/cefi/` (relative imports
  `...base_adapter`/`...schemas` resolve unchanged — same depth) + test `git mv`
  `test_lighter_extended_pacifica_coverage.py` defi→cefi + repath + `tests/unit/test_is_adapter_fetch_failure_raises.py`
  repath. The expected-universe enumerator + its tests ALREADY treated the 3 as cefi
  (`test_cefi_yields_..._for_lighter`, `_make_cefi_entry`) — only the IS capture path had drifted, now aligned. Codex
  `defi-canonical-naming-ssot.md` got an "on-chain perp CLOBs are CeFi" section;
  `availability- manifest-and-data-status.md` already documented the cefi-instrument shape for these. They ride the
  **cefi backfill** like HL/ASTER (`_CEFI_VENUES`); no special path. NOTE: only EXTENDED has a UAC cefi
  `SourceCapability` — PACIFICA/ LIGHTER MTDS-cefi market-data capture is a separate cefi-track gap (IS
  instrument-reference is now cefi-correct for all 3). The §3 subgraph investigation (background agent) returned a lead:
  TRADER_JOE_V2-AVALANCHE (empty), UNISWAP_V4 + VELODROME_V2 (not-yet-collected), ORCA/KAMINO/RAYDIUM (Solana-REST, not
  subgraphs — "6 subgraphs" is a partial misnomer; RAYDIUM also carries the 1970 genesis bug) — to verify against live
  coverage at §3. The MTDS-breakdown agent mapped the IS §6 gap: IS lacks the 4-state `capture_status` per (venue,chain)
  shard that MTDS records.

- 2026-06-25 — **DeFi takeover #2 (opus) — verified handoff baseline, corrected it on 3 points, got 2 operator
  decisions, built+ran the §1.2 monotonic guard.** Prober re-run confirms the banked baseline EXACTLY (IS-PRD/MTDS/
  catalogue/per_vm 0 glued; ENVLESS 75,649; by_date PATH 56/day; by_date COL 2,620/15; UAC registry 156). Reader audit
  (10 sites / 5 repos) + the canonical SSOT (governs `raw_tick_data`+manifest ONLY — both already canonical) established
  the IS `instrument_availability/by_date/venue={glued}/` snapshot PATH is a SEPARATE reference key, not an SSOT
  violation.
  - **OPERATOR DECISION 1 — by_date glued PATH + UAC registry = DOCUMENT as canonical internal key** (NOT migrate). The
    5-repo physical migration (10 readers + 2,345-day rewrite) is rejected; instead scope the prober's glued-ban to
    `manifest`+`raw_tick_data` and document the IS-snapshot/registry glued exception in the canonical SSOT. **Path
    structure is uniform**: ALL asset_groups write ONE shape `instrument_availability/by_date/day=/venue=/<file>` (glued
    is just the defi VALUE of the single `venue=` key); the second IS plane
    `sports_reference/by_date/.../entity=/ [league=]/` is a different data category → legitimately different.
  - **OPERATOR DECISION 2 — EXTENDED = CeFi; PURGE the defi contaminant** (REVERSED from the initial "adopt as defi"
    once full evidence surfaced). EXTENDED-STARKNET is **already a fully-registered CeFi on-chain perp**: cefi
    `SourceCapability` (`_cefi.py:754` `_EXTENDED`, source="extended", `api.starknet.extended.exchange` REST+WS, SM
    keys, plan `extended_starknet_historical_data_path_2026_05_20.md`) + 6 more cefi registries
    (venue_mapping=extended_api, venue_instrument_config=PERPETUAL, venue_launch_dates 2024-09-01,
    market_data_categories, data_type_capability grouped with PACIFICA/LIGHTER). Same class as HYPERLIQUID/ASTER
    (`venue_constants→"cefi"`). STARKNET is NOT in UAC `KNOWN_CHAINS` (prober's local set has it → why it flagged
    EXTENDED-STARKNET "glued"). So the **119 cefi rows are CORRECT**; the **603 defi rows (556 catalog + 47 blank) are
    contamination** from the **misplaced `adapters/defi/extended.py`** (a cefi perp adapter in the defi folder feeding
    the defi instrument-catalog). Plan: **purge the 603 defi `_index` rows (snapshot-first) + retire/relocate the
    misplaced adapter**; EXTENDED cefi-completeness is a **cefi-track** item (defi scope = contaminant cleanup only).
    Initial "adopt-as-defi" checked ONLY defi registries + saw the misplaced defi adapter — the 7 cefi registrations
    were the missing evidence.
  - **ROOT CAUSE FOUND + finding BROADENED to 3 venues (EXTENDED + PACIFICA + LIGHTER), 1,802 contaminant defi rows.**
    UAC `market_data_categories.VENUE_TO_ASSET_GROUP` correctly maps all three → **cefi** (lines 258-260), but the IS
    **defi capture path** `engine/orchestrator/defi.py` carries them in its OWN static lists: `_SOLANA_DEFI_VENUES`
    (`PACIFICA-SOLANA`) + `_L2_DEX_PERP_VENUES` (`LIGHTER-ZKSYNC`, `EXTENDED-STARKNET`) → `_build_defi_venues()` →
    captured as defi (ongoing, up to 06-21). `_index` contamination: **EXTENDED 603 defi (+119 cefi correct), PACIFICA
    357 defi (0 cefi), LIGHTER 842 defi (0 cefi)**. NONE are in the IS cefi enumeration → removing from defi without
    cefi pickup leaves PACIFICA/LIGHTER uncaptured (acceptable: **cefi is PAUSED** pending this foundation; they'll
    capture correctly as cefi when it resumes). Adapters `adapters/defi/{extended,pacifica,lighter}.py` are misplaced
    (cefi perps in the defi folder; HYPERLIQUID/ASTER correctly live in `adapters/cefi/`). Tied surfaces: tests
    `tests/unit/reference_data/adapters/defi/test_lighter_extended_pacifica_coverage.py` +
    `test_enumerate_expected_universe*` (LIGHTER assertions) + the expected-universe seeder (seeds these as defi).
  - [x] ✅ [SCRIPT] P0. **Phase-1 CODE: reclassify EXTENDED/PACIFICA/LIGHTER defi→cefi** — IS@2f7d454: removed the 3
        from `defi.py` `_SOLANA_DEFI_VENUES`/`_L2_DEX_PERP_VENUES` (+ `__init__.py` export); added to
        `venue_core._CEFI_VENUES` (ride the cefi backfill like HYPERLIQUID/ASTER); relocated adapters
        `adapters/defi/`→`adapters/cefi/`; moved+repathed tests; adapter-contract baseline keys renamed (count=3
        **preserved**, NOT regenerated, PM@8ef0dffe8) + extended test now ASSERTS the `ADAPTER_FETCH_FAILED` emit; codex
        on-chain-perp-is-cefi note. QG-green (94s); peer's concurrent VIX test fix reconciled (autostash conflict, took
        peer's canonical version, my defi changes intact).
  - [x] ✅ [SCRIPT] P0. **Phase-2 DATA: purged the 1,802 contaminant defi `_index` rows** (EXTENDED 603 + PACIFICA 357 +
        LIGHTER 842) — `scripts/purge_cefi_perp_defi_contamination_2026_06_25.py --apply`, snapshot-first
        (`_index/snapshots/pre_phase2_purge_2026_06_25.parquet` + `.phase2.bak`). VERIFIED live: \_index
        176,186→174,384, defi-3venue=0, cefi-3venue=119 preserved; monotonic guard defi venues 31→28 (3 dropped),
        drop-days 182→180. Catalogue (asset_group-AGNOSTIC, venue-keyed instrument defs) left intact. REMAINING (minor):
        the orphaned by_date defi snapshots for the 3 venues (~3/day, no longer enumerated after Phase 1) + stop the
        expected-universe seeder from seeding them as defi — tracked below.
  - [ ] [CEFI-TRACK] P1. **EXTENDED violates the CF-11 honest-absence contract** — on fetch failure it emits
        `ADAPTER_FETCH_FAILED` but FALLS BACK to a hardcoded market list instead of raising, so a real outage records
        `captured` (stale fallback) not `attempted_failed` (the A8 false-complete pattern). Its sibling on-chain perps
        (HYPERLIQUID/ASTER/LIGHTER) raise. Decide: make EXTENDED raise-on-fetch-failure (honest) vs keep the fallback.
        Target repo: instruments-service `adapters/cefi/extended.py`. Cefi-track (behaviour change w/ manifest
        implications).
  - [ ] [SCRIPT] P2. **Phase-2 tail: purge orphaned by_date defi snapshots for EXTENDED/PACIFICA/LIGHTER** (~3/day
        across history, un-enumerated after Phase 1) + ensure the expected-universe seeder no longer seeds these as defi
        `expected_unattempted`. DoD: 0 `venue=EXTENDED-STARKNET|PACIFICA-SOLANA|LIGHTER-ZKSYNC` by_date defi blobs.
  - [ ] [CEFI-TRACK] P1. **MTDS-cefi capability for PACIFICA/LIGHTER** — only EXTENDED has a UAC cefi `SourceCapability`
        (`_cefi.py`); PACIFICA/LIGHTER have none, so their cefi market-data capture is unbuilt (IS instrument-reference
        is now cefi-correct for all 3). Build their MTDS cefi capture when cefi resumes. Target repo:
        market-tick-data-service.
  - **§1.2 MONOTONIC GUARD BUILT + RUN** (`instruments-service/scripts/defi_cumulative_drawdown_guard_2026_06_25.py`):
    per-venue daily active instrument_count from the `_index`, flags day-over-day drops. Result: **182 venue drop-days
    across 30 defi venues** (UNISWAP_V3 −1759, BALANCER −2101, PANCAKESWAP_V3 −493, MORPHO −431, …). **EXTENDED is
    GUARD-CLEAN** (1 drop-day, −1) → safe to adopt. CAVEAT: for DEX top-N-by-TVL venues most active-count drops are
    legitimate top-N churn; the hard-defect invariant is the cumulative-ever-seen UNION (needs instrument-lifecycle
    modeling), so the 182 need delisting-vs-missing classification — the full §1.2 reconciliation P0.
  - **GENESIS diagnosed** — the 15 RAYDIUM `1970-01-01` rows are in the CATALOGUE (`prod/catalog.parquet`), are STALE
    legacy roll-up rows (live by_date RAYDIUM snapshot has NO `available_from` col, 0×1970) with EMPTY `pool_address` →
    no RPC genesis-oracle resolution possible. Current adapter already floors to `get_protocol_floor_date('raydium')` =
    `2021-02-21` (RAYDIUM AMM mainnet launch). Fix = patch the 15 to the floor (the honest conservative the live code
    produces) + confirm regen-durable.
  - **ENVLESS redundancy PROVEN** — chain-agnostic, 39,512/40,115 ENVLESS cells are in `-prd-`; the 603 residual are ALL
    `EXTENDED-STARKNET` glued-form twins of `-prd-`'s split form (only "missing" because my splitter skips the
    unsanctioned EXTENDED venue). Identical date ranges (2020-01-20..2026-06-21). ENVLESS is genuinely redundant → safe
    to snapshot-then-delete. (Corrects the first-pass "39,240 missing" which was a chain-blank-vs-populated artifact.)
  - **FINDING (sports track, not defi) — file as todo:** IS writes sports instruments at
    `instrument_availability/by_date/.../venue=API_FOOTBALL/` with NO `league=` segment, but deployment-api's reader
    (`_instruments.py:251`) constructs `.../league={league}/venue={venue}/` → reader/writer path mismatch.
  - **REMAINING (decided, executing):** (a) ship EXTENDED UAC adoption + purge 119 cefi; (b) genesis floor-patch (15
    RAYDIUM); (c) ENVLESS snapshot-then-delete; (d) prober tighten + SSOT document the glued internal-key exception; (e)
    §1.2 full reconciliation of the 182 drops (delisting-vs-missing); (f) recency 06-22→today + 6 subgraphs + clean
    backfill. Scripts banked: `defi_cumulative_drawdown_guard_2026_06_25.py`, `diagnose_*_2026_06_25.py` (read-only).
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
  - **Step 1 SNAPSHOT ✅** — IS PRD/ENVLESS `_index` + catalogue + MTDS defi `_index` →
    `_index/snapshots/ pre_migration_2026_06_25.parquet` (+ `prod/snapshots/catalog.pre_migration_2026_06_25.parquet`).
    Regression baseline fingerprints (per venue×data_type captured counts) recorded. KEY INVARIANT: IS PRD captured
    **cells** = 174,926.
  - **Step 2 COLLAPSE ALL drift → bare canonical ✅ APPLIED**
    (`instruments-service/scripts/ collapse_defi_drift_to_canonical_2026_06_25.py`, ruff-green; per-blob
    `.driftcanon.bak`). before→after, live prod: `_index` 187,850→176,186 rows, **glued 76,904→0, ghost 0→0**, chain
    100% populated, captured **cells** 174,926→174,926 (ε=0; 11,664 dropped rows were glued+bare twins of the SAME
    canonical cell, merged captured-wins); `prod/catalog.parquet` glued 1,001→0, ghost 197→0, chain 100% populated;
    `_index/per_vm/_legacy_seed` glued/ghost→0. Caught+fixed a dedup bug mid-build (first version kept BOTH captured
    twins → duplicate canonical cells; fixed to one-row-per-cell, status-priority captured>empty>failed>EU, richest
    instrument_count; ε=0 asserted on captured CELLS).
  - **EMITTER ROOT-FIX SHIPPED** (IS@92084d5c3, QG-green 95s, quickmerged): the glued treadmill is the by_date snapshot
    — the daily writer writes the parquet `venue` column GLUED (`AAVE_V3-ARBITRUM`) with NO `chain` column for non-pool
    rows, and the GCS path is `venue=AAVE_V3-ARBITRUM/` (no chain= segment). The MANIFEST column split
    (`writers.py::_write_venue` parse_defi_venue → bare+chain) is ALREADY correct in current code (so the live glued
    manifest rows were LEGACY accumulation, cleaned by Step 2). The CATALOGUE was re-drifting because
    `build_instrument_catalogue.py` only split venue for POOL rows; non-pool DeFi (lending/lst/staking/perp) passed the
    glued parquet venue through. **Fix**: `_canonical_bare_venue_chain` (ghost-fix + known-chain-suffix split) on the
    non-pool fallthrough — no-op for bare-canonical + non-DeFi (BINANCE-FUTURES/API_FOOTBALL untouched, verified).
    **VERIFIED (coordinator #3):** a bounded catalogue regen from the actual glued by_date snapshots → **0 glued / 0
    ghost, chain 100% populated**. Treadmill broken on the catalogue side.
  - **NO-REGRESSION PROVEN (coordinator #1):** the "+30,719" was a wrong-baseline compare (vs stale ENVLESS 145,467, not
    true PRD 187,850). Against the snapshot: 187,850→176,186 (DECREASE of 11,664 = glued+bare twins merged); snapshot
    CAPTURED rows collapsed to canonical keys = **174,926 distinct canonical captured cells == live 174,926** (ε=0); 0
    live captured cells absent from snapshot; 0 snapshot canonical captured cells lost; 0 duplicate canonical-cell rows
    post-apply. attempted_failed 1,260 preserved exactly.
  - **STILL TODO** (remaining sequence): junk `1970-01-01` genesis = **15 RAYDIUM POOL rows** (epoch-zero from a missing
    on-chain creation ts) → Step 4 venue-truth genesis (don't mask with a hasty proxy). `available_from` already uniform
    ISO-string (no mixed-type defect; the sort-crash was `available_to` str+None). Step 3 one-bucket: ENVLESS `_index`
    is a stale SUBSET of `-prd-` (no env-less-only data) BUT retiring needs every reader confirmed on `-prd-` first (the
    DURABLE gotcha #1 + MTDS `check_reader_writer_bucket_parity` gate) — code-verify before delete. Then: venue-truth
    genesis · recency 06-22→today · 6 uncovered-venue subgraphs · GCS by_date path-split (Step 5, writers.py:113) · cefi
    `EXTENDED-STARKNET` (119) purge (retirement) · clean backfill.
- 2026-06-25 — **SESSION HANDOFF (clean boundary, NO destructive op half-applied; snapshots intact). Banked + verified
  this session; next session resumes from this + the prober ground-truth.**
  - **Step 3 reader-parity VERIFIED (code, read-only):** every defi instruments READER resolves env-short `-prd-` via
    `resolve_bucket_name(kind="instruments-store", asset_group="defi")` — `_defi_manifest.py` (via
    `assert_reader_writer_bucket_parity`, the gotcha-#1 fix is LIVE), `_instruments_metadata.py` (3 sites),
    `_catalogue_filter.py`, `defi_catalog_reader.py`. **0 readers on env-less.** So the ENVLESS bucket DELETE is
    unblocked BUT NOT YET DONE (left for the fresh session per handoff — it's a destructive 70,151-by_date-obj delete;
    must first prove those objs are redundant-vs-`-prd-`, then snapshot-then-delete). ENVLESS `_index` (145,467 rows /
    75,649 glued) is moot once deleted.
  - **MTDS `_index` glued FIXED ✅** (`--target market-data` venue-only-no-dedup; 6 `UNISWAP_V4-ETHEREUM`→`UNISWAP_V4`
    +chain=ETHEREUM, rows UNCHANGED 7,390,534, captured 1,971,546 preserved, per-blob `.driftcanon.bak`). **CRITICAL
    SAFETY CATCH:** the generic IS-tuned `collapse_frame` dedup applied to MTDS would have dropped **345,219 rows** —
    the MTDS `_index` natural key is WIDER (pipeline_mode varies in 27,116 dup-groups, capture_status in 345,015) → a
    venue-ONLY rewrite (no dedup) is the only safe op there. Never run the IS dedup on the MTDS manifest.
  - **ZERO-GLUED PROBER baseline (record — run `scripts/audit_defi_zero_glued_2026_06_25.py` to refresh):** | surface |
    glued | ghost | state | |---|---|---|---| | IS-PRD `_index` | 0 | 0 | ✅ Step 2 | | IS-PRD catalogue | 0 | 0 | ✅
    Step 2 | | IS-PRD per_vm seed | 0 | 0 | ✅ Step 2 | | MTDS defi `_index` | 0 | 0 | ✅ this session | | MTDS
    raw_tick_data PATH | 0 | 0 | ✅ already canonical (MTDS writer fixed earlier) | | IS-ENVLESS `_index` | 75,649 | 0 |
    → Step 3 DELETE (stale bucket) | | **IS by_date PATH** (`venue=AAVE_V3-ARBITRUM/`) | 56/day (ALL) | 0 | **REMAINING
    — Step 5 path-migration** | | **IS by_date COLUMN** (in-file `venue`, no chain col on non-pool) |
    2,620/15-file-sample | 0 | **REMAINING — Step 5** | | **UAC `ALL_DEFI_VENUES`** | 156 | 0 | **REMAINING — glued-form
    registry; flip-or-document decision** |
  - **REMAINING for the fresh session** (NONE started; no half-applied destructive op): (a) **Step 3** ENVLESS bucket
    delete (readers verified `-prd-`; snapshot-then-delete after redundancy proof). (b) **Step 4** venue-truth genesis
    (15 RAYDIUM `1970-01-01` + scan for other epoch-zero). (c) **Step 5** the by_date PATH+COLUMN migration (the big
    one: 2,345 days × ~56 venues, glued path→`venue=PROTOCOL/chain=X/` + in-file venue→bare + add chain col) AND the
    `writers.py:113` path-split EMITTER fix (the catalogue-read-side fix shipped IS@1e97931; the writer path-split is
    NOT done — by_date still WRITES glued). (d) **UAC registry** flip-to-bare-or-document (operator bar = no glued
    vocabulary; the drilldown splits it to `(PROTOCOL,CHAIN)` pairs so it's an internal join key, not a path/manifest/UI
    surface — decision pending). (e) recency 06-22→today · 6 uncovered subgraphs · `EXTENDED-STARKNET` 119 cefi purge ·
    clean backfill. **Snapshots intact** (`_index/snapshots/pre_migration_2026_06_25.parquet` in all 3 buckets +
    per-blob `.driftcanon.bak`). Banked this session: IS@1e97931 (Step-2 collapse + catalogue emitter fix), IS HEAD
    (MTDS venue-only collapse + prober).
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
    - [x] ✅ [SCRIPT] P0. **G1.a billable-venue guard (§7.1)** — IS@92084d5c QG-green. Stripped non-billable datasets
          (IFEU/IFUS/OPRA/XNAS.ITCH/XNAS.BASIC/XNYS.PILLAR) from `_DATASET_TO_VENUE`/`_DATASET_TO_asset_group`/
          `_FUTURES_DATASETS` (now only the 3 billable) + exclusion-marker comments; the
          `assert_databento_request_allowed` fetch gate was already present (adapter.py L424). Regression:
          `test_g1a_billable_dataset_maps_only_three`. **Follow-up todos filed below**: router.py + massive.py still
          reference non-billable datasets (the latter is the actual OPRA/I:VIX pollution source).
    - [x] ✅ [SCRIPT] P0. **G1.b exclude cefi-domain equity singles** — IS@92084d5c. `get_instruments` filters curated
          defs to `asset_group ∈ frozenset(AssetClass)` → the 12 cefi-singles (asset_group="cefi") not enumerated as
          tradfi; SP500-overlap tickers still enter via the SP500 path. Regression:
          `test_g1b_cefi_singles_excluded_from_tradfi_enumeration`.
    - [x] ✅ [SCRIPT] P0. **G1.c XCBF.PITCH = COMMODITY + outright-only** — UAC@256dfc4a (`_CFE_FUTURES` VX.FUT
          "equity"→"commodity" + UAC regression test) + IS@92084d5c (`_DATASET_TO_asset_group["XCBF.PITCH"]`→COMMODITY;
          drop XCBF class-S VX spreads in `_parse_row_to_record`). Regression:
          `test_g1c_xcbf_outright_only_drops_vx_spreads` (IS) + `test_vx_future_asset_group_is_commodity` (UAC). The
          IS↔UAC test coupling was DECOUPLED (UAC content asserted in UAC's suite, not IS) to avoid false-fails under
          UAC promotion lag.
    - [x] ✅ [SCRIPT] P0. **G1.d DBEQ.BASIC class-S → EQUITY** — IS@92084d5c. Equity-spot rows no longer mis-typed
          SPOT_PAIR. Regression: `test_g1d_dbeq_class_s_is_equity_not_spot_pair`.
    - [x] ✅ [SCRIPT] P0. **G1.e calendars+sessions FAIL-CLOSED** — IS@92084d5c. Declared KRX (XKRX cal + KST hours) +
          FX (24/7 explicit) + `is_non_trading_day` raises `UndeclaredTradfiVenueError` for an undeclared tradfi venue
          (was silent 24/7). ICE re-DECLARED in sessions pending the whole-venue retirement (so no spurious raise
          mid-transition; curated enumeration already drops ICE instruments). Regression:
          `test_g1e_krx_uses_korean_calendar` + `test_g1e_fx_is_24_7` + `test_g1e_undeclared_venue_fail_closed`; updated
          the prior fail-open test.
    - [ ] [SCRIPT] P0. **G1.f macro/currency canonicalise** — PARTIAL (operator-reshaped 2026-06-25): VIX cash-index
          REMOVED from UAC `YAHOO_INDICES` ✅ (uac@43db03f8 + databento VIX-USD tests IS@fb13355e); DXY KEEPS venue=ICE
          ✅ (operator REVERSED the planned ICE→FX — DXY IS the ICE/NYBOT US Dollar Index, Yahoo-sourced, the ONLY
          retained ICE exception, documented in-registry; ICE→FX key-migration CANCELLED). REMAINING split into G1.f.2
          (VIX-15m index removal) + G1.f.3 (treasuries actually reach the catalogue) below.
    - [ ] [SCRIPT] P1. **G1.f.2 — retire the VIX-15m INDEX (superseded by VX futures 1s OHLCV; operator 2026-06-25)** —
          remove `CBOE:INDEX:VIX-USD` ohlcv_15m as a distinct index. 3-repo, consumers-first. VX.FUT futures
          (`CBOE:FUTURE:VX`, XCBF.PITCH ohlcv-1s/1m, aggregated downstream) is KEPT — it IS the VIX-vol source;
          features=0 consumers of the VIX-15m index. **STAGE 1 — MTDS DONE ✅ mtds@833fa14c (QG-green):** removed
          `fetch_yahoo_vix_15m` (`_umi_yahoo.py`) + the CBOE+ohlcv_15m→Yahoo routing (`umi_tick_provider.py`) +
          `download_vix_15m` + the `VIX_INDEX_INSTRUMENT` special-case in `YahooFinanceAdapter.fetch_instruments` (→
          `[]`). A direct `(CBOE, ohlcv_15m)` fetch now returns empty (no Yahoo, no error) — VERIFIED. Tests: deleted
          `test_vix_15m_source_layering.py`; dropped the obsolete Yahoo-routing tests; `CBOE+ohlcv_15m` asserts
          empty-no-Yahoo. **STAGE 2 — MDPS (TODO):** `orchestration_writer.py` `_record_vix_gap_empty` (already a no-op
          since `is_vix_15m_gap_date` is always False) + its `orchestration_service.py` caller + the
          `VIX_INSTRUMENT_KEY`/`is_vix_15m_gap_date` UAC imports + the MDPS test. **STAGE 3 — UAC (TODO, LAST — removes
          public exports → breaking, after MDPS no longer imports them):** `data_source_continuity.py`
          (`get_vix_15m_source` / `is_vix_15m_gap_date` / `get_yahoo_vix_15m_start` / `VIX_15M_SOURCE_HISTORY` /
          `YAHOO_VIX_15M_WINDOW_DAYS` / `DATABENTO_VX_FUTURES_FIRST_DATE` / `VIX_INSTRUMENT_KEY` + the
          `("CBOE:INDEX:VIX-USD","ohlcv_15m")` `_SOURCE_RESOLVERS` entry) + `tradfi_symbology.py`
          `VIX_INDEX_INSTRUMENT` + UAC tests. Then update the CLAUDE.md/SSOT VIX-15m rows. **NB (data-correctness,
          verify at G2): VIX-15m now depends on `CBOE:FUTURE:VX` being captured at ohlcv-1s/1m + the downstream
          1s/1m→15m aggregation — confirm that path is wired so removing the Yahoo fetch leaves no silent 15m gap.**
          Provenance: operator 2026-06-25.
    - [x] ✅ [SCRIPT] P0. **G1.f.3 — CBOE treasury-yield INDICES into the daily instrument definitions (operator
          2026-06-25)** — DONE uac@0b8a775c + IS@2536d9b4. **US2Y ADDED** to UAC `YAHOO_INDICES` as
          `CBOE:INDEX:US2Y-USD` via Yahoo `2YY=F` (operator: "use Yahoo, don't care which ticker"; the only Yahoo 2Y is
          the 2YY=F future — no ^-series cash 2Y exists) + the shared treasury source-resolver + genesis 2018-08-13 (CME
          yield-futures launch, best-estimate — VERIFY at backfill; honest-absence surfaces freshness since 2YY=F was
          noted stale). Target curve = **3M / 2Y / 5Y / 10Y** (operator) + 30Y KEPT (the features
          `treasury_yields_calculator` depends on it; operator curve is a subset). US5Y/US10Y/US3M/US30Y already in the
          registry. Tests updated (UAC `_TREASURY_TENORS` + resolver-coverage gate; IS `_create_yahoo_index_records`
          loop). **Catalogue population is OPERATIONAL, not a code gap**: CBOE IS in `_TRADFI_VENUES`
          (venue_core.py:138) + `build_instrument_catalogue.py` rolls up from the written
          `instrument_availability/venue=CBOE/` parquets WITHOUT filtering INDEX — so the treasuries reach the catalogue
          once a CBOE instruments-backfill writes the `CBOE:INDEX:USxY-USD` records (rides **G2**). The operator's
          "never in the catalogue" = no CBOE-index backfill has run since the yahoo-index path landed, not a code
          exclusion. **FOLLOW-UP (features): `treasury_yields_calculator.py` builds the curve from 5Y/10Y/30Y — wiring
          it to consume the new 2Y/3M points is a features-track todo (not blocking the instrument-definition add).**
          Provenance: operator 2026-06-25.
    - [ ] [SCRIPT] P1. **G1.g MVP tags on the tradfi MVP universe** (VX futures + basis tickers).
    - [ ] [SCRIPT] P0. **G1.h §7.3 `available_to` venue-truth + per-venue `latest_day`** —
          `build_instrument_catalogue.py` (SHARED with cefi item 4; coordinate — do NOT double-edit).
    - [ ] [INFRA] P0. **G1 retirement (§8, 4 legs) — OPERATOR-CONFIRM before purge** — ICE (whole venue, 16,158) · CBOE
          OPRA OPTION (33,258) · CBOE VX-spread SPOT_PAIR (4,216) · VIX-cash INDEX (^VIX+I:VIX) · NASDAQ/NYSE mis-class
          SPOT_PAIR (318) · cefi-singles. Pause consolidator→snapshot→filter→resume; verify gone all 4 legs.
    - [x] ✅ [SCRIPT] P1. **G1.a.2 §7.1 follow-up — massive.py (the OPRA/I:VIX pollution source)** — DONE
          instruments-service@1198549 (LDR). massive KEPT as the tradfi FALLBACK (operator 2026-06-25); endpoint
          `https://api.polygon.io` VERIFIED correct (Polygon.io→Massive 2025-10-30 rebrand kept the host). Removed the
          two pollution-fetch paths the databento §7.1 guard (G1.a) does not touch: `_fetch_indices` (CBOE cash-index /
          VIX-cash over YAHOO_INDICES) + `_fetch_index_options` (OPRA SPX/VIX cash-index OPTION chains) — both retired
          (VX vol rides Databento XCBF.PITCH) — plus ICE from `_FUTURES_VENUES` (Databento-billing-blocked, no canonical
          source). massive now fetches NASDAQ/NYSE equities + FX + CME futures ONLY, ending CBOE-OPTION (33,258) /
          VIX-cash / ICE catalogue pollution at source. Regression: `test_cboe_and_ice_filters_yield_no_pollution`
          (CBOE+ICE venue filters yield zero records); dead index/option fixtures + coverage-boost tests removed.
          QG-green, 58 tests pass, basedpyright 0. NOTE: this is the SOURCE fix (stop writing pollution); the GCS PURGE
          of the already-written CBOE-OPTION/VIX-cash/ICE parquets stays in the operator-gated G1 retirement (§9).
          Actual method names were `_fetch_indices`/`_fetch_index_options` (plan's earlier `_fetch_opra_options`/
          `_fetch_index_universe` were guesses). Provenance: slot-3 G1.a diagnosis 2026-06-25.
    - [x] ✅ [SCRIPT] P2. **G1.a.3 §7.1 follow-up — router.py dead non-billable dataset config** — DONE
          instruments-service@5ef1958f (LDR). DELETED (not realigned) the whole dead path: the databento adapter
          resolves each instrument's dataset PER-INSTRUMENT from the curated `TRADFI_DATABENTO_INSTRUMENTS` registry
          (§7.1 billable allowlist DBEQ.BASIC / GLBX.MDP3 / XCBF.PITCH), so the router's `_DATABENTO_VENUE_DATASETS`
          venue→dataset map (nasdaq/nyse/apple/binance→XNAS.ITCH/XNYS.PILLAR + cboe_options→OPRA.PILLAR, all
          non-billable) + `_resolve_databento_datasets` resolver + `_route_databento`'s resolve-and-pass + the unused
          `datasets=` ctor param (all callers kwargs-only) were 100% dead. Removed all four + the misleading docstring
          annotations. Routing behaviour unchanged (databento still → DatabentoReferenceDataAdapter); only the dead
          non-billable annotation is gone. Tests: removed `TestResolveDatabentoDatasetsRouter` + dead import;
          `test_router` routing assertions unchanged (still pass — they assert isinstance, not datasets). QG-green, 68
          tests pass, basedpyright 0. Provenance: slot-3 G1.a diagnosis 2026-06-25.
- 2026-06-25 — **cefi VM-drain for the canonical-form migration (operator-directed, this session).** Operator flagged
  cefi backfills running before the foundation code lands (G4/G5-before-G1–G3 + would write against the buggy catalogue
  - race the canonical-form migration). **STOPPED (graceful, reversible — process killed, not deleted):**
    `cefi-binance-futures-2020-heavy-20260624-222326` (cefi MTDS market-data backfill) ·
    `cefi-hyperliquid-2024-20260623-113700` (cefi MTDS backfill, 1.5d-running) · `mtds-perp-funding-backfill` (tagged
    `VM_ASSET_GROUP=DEFI`/`defi-backfill` but cefi-named + servicing cefi funding — the cross-AG-servicing-cefi case).
    Operator decision: **cefi-scoped drain + any cross-AG VM servicing cefi stopped + per-AG VMs only going forward.**
    LEFT RUNNING (other active agents' single-AG work, per cefi-scope): ~15 `mtds-live-cefi-*` LIVE producers (decide
    after auditing whether cefi market-data bucket needs migration — they write it continuously), 16 `tradfi-bf-*` +
    `tradfi-fwd-daily-cron` (slot-3 tradfi track), `instr-backfill-defi` + `defi-fwd-oracle-prices-poll` + `mtds-dex-*`
    (defi agent), `prediction-live-*`, `sports-ref-v3-*`. **Finding (per-AG VM hygiene):** `mtds-perp-funding-backfill`
    (DEFI metadata, cefi-name, no AG prefix) + the untagged `defi-fwd-*`/ `tradfi-fwd-*`/`mtds-dex-*` pollers (no
    `VM_ASSET_GROUP`) are the cross-AG/untagged anti-pattern the operator named — launchers must set `VM_ASSET_GROUP` +
    an AG-prefixed name; tracked under the canonical-form/observability items.
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
    deribit/hyperliquid/kraken/okx + batch modes); `processed_candles/by_date/day=…` clean (0 orphans). \*\*DUAL-SoT
    FOUND
    - FIXED:** 9 stray flat `raw_tick_data/by_date/<symbol>.parquet` (AVAXUSDT/BTC-28MAR25/BTC-PERPETUAL/BTCUSDT/
      ETH-PERPETUAL/ETH-USD-250328/KRW-LINK/SOL-ETH/TRX-USDT), all stamped **2026-05-12T17:01** = the pre-`day=`/
      `pipeline_mode=` flat layout that the ~05-12 path migration rewrote into the canonical tree but **never deleted
      the source** (manifest-invisible → never in coverage). **Snapshotted →
      `_index/backups/orphan_flat_files_pre_sot_ cleanup_2026_06_25/` then PURGED\*\* → 0 flat orphans remain, 2,645
      canonical `day=` dirs intact. Single-SoT restored.
  - Remaining canonical-form work (the tracked Phase-0 single-SoT item, runs in cefi G1–G3): full schema_version
    distribution of the 144MB market-data `_index` (measured, not the constant) · venue/instrument_id casing across the
    market-data manifest · the §2.3 ε=0 reconciliation guard wiring · the 24 blank-source / all-blank-data_type
    instruments residual. cefi canonical-form is otherwise GREEN (no further dual-SoT pollution found).
- 2026-06-25 — **TRADFI G1.a–e SHIPPED + tradfi compute fully stopped (slot-3).** **Code (QG-green, both repos):**
  UAC@256dfc4a (`_CFE_FUTURES` VX.FUT "equity"→"commodity" + UAC regression test) + instruments-service@92084d5c
  (symbology billable-venue map cleanup → only the 3 billable datasets; `get_instruments` excludes cefi-domain singles;
  XCBF class-S VX spreads dropped + XCBF→COMMODITY; DBEQ class-S→EQUITY; KRX XKRX-calendar + FX-24/7 + fail-closed
  `UndeclaredTradfiVenueError`; ICE re-declared in sessions pending the whole-venue retirement; **8 regression tests**
  in `test_databento_tardis_adapter.py::TestTradfiG1FoundationRegression` + the IS↔UAC VX assertion DECOUPLED into UAC's
  suite to avoid UAC-promotion-lag false-fails). These STOP the active catalogue pollution at source (4,216 VX-spread
  SPOT_PAIR + 318 equity-spot mis-class + cefi-singles + VX=EQUITY); stale rows (ICE 16,158 / OPRA 33,258 / VIX-cash)
  are the operator-gated retirement. **Findings filed** (above): OPRA/I:VIX pollution actually comes from massive.py
  (G1.a.2); router.py dead non-billable config (G1.a.3). **Awaiting G1 sign-off.**
  - **Tradfi compute STOPPED (operator P0 2026-06-25 — "another track relaunched the tradfi-bf fleet overnight despite
    the pause"):** killed the 18 RUNNING `tradfi-bf-*` OHLCV backfills (the ~6 KRX ones had self-completed); deleted the
    `tradfi-fwd-daily-cron` launcher host (was a 06:00 forward-poll launcher — same gate-jump class);
    `uts-prod-tradfi- wave-launcher-cron` + `instruments-daily-backfill` schedulers confirmed PAUSED (the automated
    relaunch path — it never actually fired; the overnight launch was external/manual). Also paused
    **`lifecycle-catalogue-regen-tradfi-daily` (01:00)** + **`instrument-catalogue-regen-nightly` (02:00)** at 01:38 UTC
    — protective, before the 02:00 fire would re-bake the §7.3 false-delistings into the tradfi catalogue SSOT. **Left
    running** (per dispatch "leave the live producer"): `mtds-live-tradfi-cme-trades` (live `databento` WS) — flagged
    for the operator. **Cross-AG flag:** the other AGs' `lifecycle-catalogue-regen-{cefi,defi,sports,prediction}`
    (01:00) + `catalogue-regen-nightly` (04:30) are still ENABLED (cefi has the same §7.3 bug) — operator to decide a
    fleet-wide catalogue-regen pause.
  - **G1.f / G1.h / retirement sequencing:** G1.f (macro/currency: VIX-cash removal + DXY venue ICE→FX) is a canonical
    key-migration (UAC `YAHOO_INDICES` + `data_source_continuity._SOURCE_RESOLVERS`
    `ICE:INDEX:DXY-USD`→`FX:INDEX:DXY-USD`
    - EU enumerator + massive + the existing DXY market-data GCS re-key) → done COORDINATED with the operator-gated
      retirement/canonical-migration (a standalone code change would create the exact dual-SoT the operator banned).
      Operator clarified DXY+KRWUSD+treasuries are canonical Yahoo-daily KEEP (not one-offs); only VIX-cash is removed.
      G1.h §7.3 `available_to`/per-venue-`latest_day` is the cefi agent's item-4 (AG-agnostic
      `build_instrument_catalogue.py`) — coordinate, one fix both AGs.
- 2026-06-25 — **G4 catalogue-as-filter BUG fixed (tradfi) — market-tick-data-service@dda5040d (QG-green).**
  Read-verified the MTDS catalogue-as-filter and found a real bug: `TradFiCatalogReader` probed a DEAD prefix
  `reference_data/instruments/asset_group=tradfi/` (absent in the bucket — only `prod/catalog.parquet` exists) AND read
  the legacy `available_*_datetime` column names (the roll-up uses un-suffixed `available_from`/`available_to`), so it
  ALWAYS returned an empty iterator → the MTDS sentinel fan-out silently fell back to the UAC ("BTC"/"ETH") MVP seed and
  never filtered the real tradfi catalogue. Fixed: probe `{prod,staging,dev}/catalog.parquet` + canonical
  `available_from`/`available_to` (mirrors the `CeFiCatalogReader` BUG #4 fix, 2026-06-22) + 2 regression tests. **G4
  mechanism is now functional** (active-on-date window filter + FUTURE/OPTION root dedup); the gate's DoD (MTDS attempts
  == catalogue-active-for-day) becomes verifiable once the catalogue is clean (post-retirement + §7.3). NB the
  `catalog_list_instruments(ag)` sentinel path (sentinels.py) is a SEPARATE Tier-1 reader from this Tier-3 chain reader.
- 2026-06-25 — **Reversible drivable work remaining (no operator gate): G1.g MVP tags; G1.a.2 massive.py §7.1 (the
  actual OPRA/I:VIX pollution source); G1.a.3 router.py dead non-billable config. Operator-gated: retirement GCS purge ·
  G2 fleet · G1.f DXY key-migration. cefi-coordinated: G1.h §7.3 `available_to`/per-venue-`latest_day` (still the cefi
  agent's unstarted item-4; AG-agnostic, blocks G3 for both AGs). CI-verified: IS#629 merged-staging-green; UAC + MTDS
  Tier-C-draining.**

## Folded-in (I-1 consolidation 2026-06-26)

> Open todos migrated here from 3 archived plans during the instruments/MTDS plan consolidation
> (`instruments_mtds_plan_consolidation_2026_06_26.md`). Bullets are condensed to the actionable essence + provenance;
> **full detail lives in the archived source** under `archive/2026_06/`. This survivor (I-1) is now the live home for
> instruments-foundation + catalogue-completeness + tradfi-universe-lockdown + DeFi-LST-universe work.

### From `proper_instrument_catalogue_lifecycle_rollup_2026_06_04` (archived)

- [ ] [INFRA] P0. **Rebuild the IS daily definition producer** — resumed schedulers point at dead infra; recreate the
      Cloud Run job / repoint `instruments-service-daily` Workflow at a CURRENT image + CLI
      (`--operation instruments --mode batch --asset-group …`), per-VM shard env, post-2026-06-10 cloud-providers.yaml.
      Until this lands the dailies only "succeed" at the scheduler layer. Repo: deployment-service +
      instruments-service. assigned_vm: vm-cross-cutting. (MIGRATED FROM:
      `proper_instrument_catalogue_lifecycle_rollup_2026_06_04`.)
- [ ] [INFRA] P1. **Wire the lifecycle roll-up to trigger on every IS instruments update (per-AG).** TF authored
      (deployment@98bee4b, `lifecycle_catalogue_scheduler.tf`); REMAINING = `terraform apply` + T+10min per-AG execution
      verify. (MIGRATED FROM: `proper_instrument_catalogue_lifecycle_rollup_2026_06_04`.)
- [ ] [INFRA] P1. **Make the cloud lifecycle-catalogue-regen job log, then fix the real error** — add
      `print(...,     flush=True)` bisection markers per `run_rollup` phase (or bootstrap stdout logging), localize the
      job-only failure (suspect grpc/pyarrow/GCS native init or a job-env gap), fix it. Until fixed the catalogue
      refreshes via the local-run path. Repo: instruments-service + deployment-service (job env). (MIGRATED FROM: same —
      supersedes the earlier "diagnose fast-fail" bullet.)
- [ ] [CODE] P1. **All asset groups adopt the proper catalogue.** cefi/tradfi/defi catalogues APPLIED 2026-06-05; G1
      shape-aware enumerator DONE (is@6ea46565). REMAINING = granularity-aware producer for **prediction** (per-cqg
      grain) + **sports** (per-league vs per-fixture), and per-AG `_enumerate_v2_*` verify emits `expected_unattempted`
      against the real universe. Per-AG slices ride the sibling AG masters. (MIGRATED FROM: same.)
- [ ] [DATA] P1. **FINDING — IS `by_date` capture frozen ~2026-05-21 fleet-wide; tradfi degraded from ~2026-05-04.**
      Applied catalogues are honest snapshots-as-of-freeze (cefi usable; tradfi marks ~651K "delisted" → liveness not
      trustworthy until tradfi capture fixed + catalogue regenerated). Diagnose the tradfi 16K→2/day anomaly (slot-6 /
      tradfi vertical) + add a coverage-horizon staleness check to producer/audit. (MIGRATED FROM: same.)
- [ ] [DATA] P1. **FINDING — ICE futures + CME futures-options not on Massive → BLOCKED-CREDENTIALS.** Massive covers
      CME-group only, no options-on-futures product; old databento ~16-18K/day was CME ES futures-options. **Operator
      ask**: an ICE-futures + CME-futures-options reference source, or unblock Databento billing. Repo:
      instruments-service. assigned_vm: vm-tradfi. (MIGRATED FROM: same.)
- [ ] [DATA] P1. **tradfi CME futures reference gap from 2026-06-08** — Massive `/futures/vX/{products,contracts}` 404
      (worked 2026-06-07). `BLOCKED-UPSTREAM-OUTAGE`: re-probe, on restore re-run
      `--asset-group TRADFI --source massive` for missing days so `venue=CME` refills, then regen the tradfi catalogue.
      Repo: instruments-service. (MIGRATED FROM: same.)
- [ ] [CODE] P2. **FINDING — MTDS Massive connector uses the wrong futures endpoint.**
      `massive_tradfi_rest_connector.py` maps futures→`/v3/reference/futures/contracts` (404s); working path is
      `/futures/vX/contracts` (+ `/futures/vX/products` for contract size). Repo: market-tick-data-service. assigned_vm:
      vm-tradfi. (MIGRATED FROM: same.)

### From `tradfi_databento_subscription_universe_lockdown_2026_06_18` (archived; 26/33 done — universe lockdown + billing guards SHIPPED)

- [ ] [IS] P1. **Backfill the IS CME (GLBX.MDP3) catalog for 2019-01-01→present** (the IS-side universe producer — owned
      HERE) so the tradfi OHLCV download has a per-date instrument universe (definition schema is L0/free, 16y). CME
      futures expire daily — never copy definitions between dates. Repo: instruments-service. **The downstream MTDS
      market-data download is M-1's** (`path_to_100pct_backfill_mtds_is`); the CME EC\* event-contract slice is the
      tradfi-domain plan-of-record `tradfi_cme_event_contract_backfill_2026_06_20` (tradfi_master) — coordinate, don't
      duplicate. (MIGRATED FROM: `tradfi_databento_subscription_universe_lockdown_2026_06_18`.)
- [ ] [SCRIPT] P1. **(→ M-1) MTDS tradfi market-data backfill across all 3 datasets** (GLBX.MDP3 + DBEQ.BASIC + CFE) ×
      the L0 16y window, sharded; verify per-dataset manifest coverage (captured + honest-absence); confirm equity cells
      re-routed to DBEQ.BASIC and CFE/VX cells exist. **EXECUTE UNDER M-1** (`path_to_100pct_backfill_mtds_is`, which
      owns MTDS market-data backfill-to-100% and already ran the Databento OHLCV pass 2026-06-19) — gated on the IS CME
      catalog backfill above. Listed here only as the cross-link. (MIGRATED FROM: same.)
- [ ] [SCRIPT] P1. **instruments-service — post tradfi-v9 close-out, tombstone dropped Databento instruments.** Run
      `reconcile_manifest_after_entity_change.py --mode remove --asset-group tradfi` for the dropped ICE roots
      (BRN/G/DX, softs CT/CC/KC/SB/OJ; datasets IFEU.IMPACT/IFUS.IMPACT) → `REMOVED_ENTITY_TOMBSTONE` (dry-run → audit
      CSV → apply), then a phantom sweep. Repo: instruments-service. (MIGRATED FROM: same.)
- [ ] [UAC] P1. **Unit tests for `databento_subscription_allowlist`** (allowed/blocked dataset, banned OHLCV schema,
      per-level lookback floor boundaries, batch ban, break-glass, enum-repr normalization). Repo:
      unified-api-contracts. (MIGRATED FROM: same.)
- [ ] [PM] P1. **QG grep-ratchet** — no raw `batch.submit_job` outside the guarded `submit_batch_job`; no off-allowlist
      dataset string literal in tradfi fetch paths. Wire into market-tick-data-service `quality-gates.sh`. Repo: PM +
      market-tick-data-service. (MIGRATED FROM: same.)
- [ ] [SCRIPT] P2. **instruments-service — re-fetch a sample of old tradfi dates whose `instrument_count` changed**
      (equity ETFs XNAS.ITCH→DBEQ.BASIC; CME cells now include EC\* event contracts) to confirm the new parquet's
      instrument set matches the new universe; enumerate the un-refetched range. Repo: instruments-service. (MIGRATED
      FROM: same.)
- [ ] [SCRIPT] P3. **OPTIONAL physical-GCS cleanup of old ICE-Databento instrument parquets** once tombstone
      reconciliation confirms 0 consumers (twin-verify; operator-gated delete, never blind). Repo: deployment-service +
      instruments-service. (MIGRATED FROM: same.)

### From `defi_venue_name_canonicalisation_and_reth_2026_06_17` (archived; 4/5 done — venue canonicalisation + rETH SHIPPED)

- [ ] [REGISTRY] P2. **NICE-TO-HAVE — add cbETH as `COINBASE-ETHEREUM` to the DeFi LST universe** (full new-venue add:
      `ALL_DEFI_VENUES` + `DEFI_VENUE_PHASE` + `defi_venue_capabilities.py` lst_rates/oracle_prices genesis 2022-08-26 +
      chain-qualified `LEGACY_DEFI_VENUE_ALIASES` + catalogue DEFI genesis). Care: `COINBASE` name collides with the
      CeFi spot exchange — use a chain-qualified alias only. Repo: unified-api-contracts + unified-trading-pm. (MIGRATED
      FROM: `defi_venue_name_canonicalisation_and_reth_2026_06_17`.)
