---
title: "Instruments Foundation & Catalogue Completeness — gated rebuild, every asset group"
created: 2026-06-24
parent_epic: instruments_master
assigned_vm: vm-cefi
estimate_class: design
estimate_baseline_ai_days: 18
estimate_calibrated_ai_days: 11
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

## Progress log

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
