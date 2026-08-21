---
doc_type: plan
title: Instruments Foundation & Catalogue Completeness — gated rebuild, every asset group
summary:
  Gated (G0->G5, operator sign-off each gate) rebuild of the instruments foundation cefi-first then defi/tradfi/sports
  -- honest 4-state capture, expected_unattempted seeded by the IS writer, catalogue available_to from venue-truth (not
  last-seen) to kill mass false-delisting, Honest-Coverage v2 two-layer coverage via compute_honest_coverage, every
  backfill a registered observable BATCH deployment. SLIMMED 2026-07-24 (plan line-cap remediation, 4-way split) into a
  process SSOT + rolling-status index over 4 children -- Phase-0 cross-cutting foundations, cefi G1->G5 gate execution,
  tradfi G1->G5 gate execution (all 3 new), plus the pre-existing defi/sports per-AG delegated plans.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags:
  [
    instruments,
    catalogue,
    honest-coverage,
    data-correctness,
    backfill,
    cefi,
    defi,
    tradfi,
    sports,
    manifest,
    foundation,
    umbrella,
  ]
related:
  [
    /codex/02-data/instruments-foundation-and-catalogue-completeness.md,
    instruments_foundation_phase0_cross_cutting_2026_07_24,
    instruments_cefi_g1_g5_gate_execution_2026_07_24,
    instruments_tradfi_g1_g5_gate_execution_2026_07_24,
    /plans/archive/2026_06/defi_instrument_catalogue_and_capture_pipeline_2026_06_23.md,
    /plans/archive/2026_06/sports_fixture_completeness_oracle_2026_06_24.md,
    plans/archive/2026_07/instruments_mtds_subset_consistency_remediation_2026_06_17.md,
    plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md,
  ]
created: 2026-06-24
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only # was: orchestrator-agent — corrected 2026-07-14, verify-rerun finding 113, per the finding-9 operator ruling precedent (two-track model stands): assigned_vm NA => local-only; AO regen ignores NA plans regardless, so ingestion semantics unchanged
priority: P0
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3
assigned_role: monitor
last_updated: "2026-07-24" # was: 2026-07-13 — updated 2026-07-24, plan-line-cap remediation 4-way split (plans/active/issues/plan_line_cap_remediation_2026_07_23.md row #14): Phase-0/cefi/tradfi gate-execution content + the 945-line historical Progress Log extracted to 3 new child plans; this file slimmed to a process SSOT + rolling-status index; locked_by/locked_since cleared per operator-approved unlock.
locked_by:
locked_since:
context_scope:
  [
    /codex/02-data/instruments-foundation-and-catalogue-completeness.md,
    /plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md,
    /plans/active/instruments_cefi_g1_g5_gate_execution_2026_07_24.md,
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
    /codex/02-data/defi-completeness-oracle.md,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/honest_coverage.py,
  ]
supersedes:
superseded_by:
depends_on:
source:
  [
    operator directive 2026-06-24 (foundation-first reset; ask-every-gate; observability mandatory; coverage in-line
    with UI),
    cefi instruments ground-truth audit 2026-06-24 (read-only; see §Starting state),
    "plan-hygiene 4-way split 2026-07-24 (operator-approved, see
    plans/active/issues/plan_line_cap_remediation_2026_07_23.md row #14)",
  ]
drift_direction: advance-code
---

# Instruments Foundation & Catalogue Completeness — gated rebuild

> **🟢 SLIMMED 2026-07-24 (plan line-cap remediation, 4-way split, operator-approved unlock+split-as-is — see
> `plans/active/issues/plan_line_cap_remediation_2026_07_23.md` row #14).** This file is now the **process SSOT +
> rolling status index**. The G1→G5 gate-execution work + the ~945-line historical Progress Log that used to live inline
> here moved verbatim into 3 new child plans (Phase-0 cross-cutting foundations, cefi G1→G5, tradfi G1→G5); defi and
> sports were **already delegated** to their own per-AG plans in the pre-split text and are unchanged. See "Related
> execution plans" below for the full set of 4 children + the 2 already-delegated per-AG plans, and "Condensed rolling
> status table" for the current gate state of each. **`locked_by`/`locked_since` cleared** on this file as part of the
> operator-approved unlock (the 3 new children + this slimmed umbrella are NOT locked; the historical G2-G5 SIGNED-OFF
> record and the GATE 0/G1/G4 sign-off tensions flagged 2026-07-14 are accepted AS-IS, not re-litigated by this split).

**Codex SSOT (the standard this plan executes):** `/codex/02-data/instruments-foundation-and-catalogue-completeness.md`.

**Operator directive 2026-06-24 (the reset):** reference data is the foundation MTDS filters against. We were chasing
MTDS coverage while the instruments foundation had day-gaps, a paused daily capture, and late MVP tags — backwards.
Rebuild it in the **gated order**, **operator sign-off at every gate** (ask every time — do not run ahead). Every
backfill/roll-up/job must be a **registered, observable BATCH deployment** in the cockpit (no fire-and-forget). Every
coverage number flows through the **`compute_honest_coverage` SSOT** so the deployment-UI shows the same real number.
**cefi first**, then defi · tradfi · sports — same process.

---

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
`/plans/archive/2026_06/sports_fixture_completeness_oracle_2026_06_24.md`. **[⚠️ TENSION flagged 2026-07-14, doc-reconciliation vr2#116: the
2026-06-27 RE-HOMED banner immediately below hands ALL sports G1→G5 dispatch to a `status: active` coordinator plan that
carries no reference to this cefi-completion gate, and cefi is still NOT DONE per this same doc (GATE G4 OPEN pending
D2, GATE G5 only SUB-SIGNED) — yet coordinator-child G1 work (league-noise wipe) already executed 2026-06-28. Unclear
whether the 2026-06-27 re-homing was also an implicit operator override of this cefi-block rule; flagging for an
operator ruling rather than asserting either reading.]** **[✅ RESOLVED 2026-07-26 (operator ruling, answering the AO
question card in `sports_closeout_track_s2_foldin_2026_07_25.md`): the 2026-06-27 re-homing was a workspace-wide infra
migration (epic VMs → role-based single-VM dispatch, same-day system-wide change) that swept sports in as one of many
asset groups — not a deliberate sports-specific override of this gate, but retroactively BLESSED as an intended
exception rather than remediated. Reasoning: (1) direct precedent exists 2 days earlier —
`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md:169-171` records the operator personally dispatching TRADFI G1→G5
ahead of cefi-first ordering on 2026-06-25, with the explicit rule "reversible work driven to done,
expensive/irreversible HARD-PAUSE for operator confirm"; (2) the sports G1 league-noise wipe that ran 2026-06-28
followed that exact same pattern — snapshot-first, reversible
(`_index/snapshots/pre_noncanonical_leagues_delete_index_20260628_...`); (3) cefi/sports share no storage, manifest, or
denominator surface, so cefi's open gates could not have contaminated sports data by construction; (4) no harm traceable
to the sequencing itself has surfaced in the 4 weeks since — the data-quality issues that did occur post-2026-06-28
(FIXTURES re-fetch, season-boundary shortfall, phantom `expected_unattempted` rows) were internal sports-pipeline bugs
unrelated to cefi's gate state. **Standing rule going forward** (cefi is still not DONE as of 2026-07-26):
reversible/audit-class sports or tradfi work (snapshot-first audits, non-destructive fixes, diagnosis-only todos) is
cefi-first-gate-EXEMPT; irreversible/expensive operations (real fleet launches, permanent GCS purges/deletes) stay gated
on cefi DONE and need direct operator confirm, matching the TRADFI precedent's own distinction. No remediation required
— the already-executed G1 work stands.]**

> **🔱 SPORTS G1→G5 RE-HOMED (2026-06-27) — the sports G-gate todos above are flipped `[x]` here; they run via the
> golden-window-first sports plan set (`assigned_vm: NA`, role-based dispatch).** The work (G1 league-noise wipe · G2
> 2015-17 diagnosis + 40,041-failure re-run · the catalogue producer fix · the #2/#5 manifest-correctness fixes;
> footystats #6 `ODDS` is **KEPT in IS** per operator 2026-06-27 — predictive) is owned by coordinator
> [`sports_pipeline_to_100pct_golden_window_first_2026_06_27.md`](sports_pipeline_to_100pct_golden_window_first_2026_06_27.md)
> (children `sports_p0_*` … `sports_p2_*`). **Do NOT dispatch the sports G-gates from THIS plan.** This plan's sports
> section is audit/context only.

### Sports audit + manifest-correctness pre-staging (2026-06-24, moved here from the historical Progress Log 2026-07-24)

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

---

## Gated rebuild — phase index (2026-07-24 split)

The near-term cefi+defi kickoff work, the cross-cutting Phase 0 foundations, and the cefi Phase 1 (G1→G5) gate-execution
detail that used to live inline in this section now live in dedicated child plans (content moved verbatim, nothing
dropped):

- **Phase 0 — cross-cutting foundations** (observability wiring, Honest-Coverage v2, cumulative-drawdown metric,
  expected-universe oracle design, consolidation reconcile, drilldown-correctness guard, verification discipline,
  silent-cap audit, depth-aware re-fetch, cost/entitlement reason class, canonical-form single-SoT GCS migration; 🚦
  GATE 0) — **`instruments_foundation_phase0_cross_cutting_2026_07_24.md`**.
- **cefi — near-term target + Phase 1, gated G1→G5** (the 2026-06-26 "cefi+defi daily pipeline live" near-term-target
  work, the Sonnet-dispatch-#1 findings, and the full G1→G5 gate sequence incl. G1.1-G1.4 catalogue-correctness fixes) —
  **`instruments_cefi_g1_g5_gate_execution_2026_07_24.md`** (`depends_on` the Phase-0 child for GATE 0).

**Operator gates status (as of the pre-split state, 2026-07-14 doc-reconciliation pass — see each child for anything
newer):** GATE 0 NOT RECORDED SIGNED OFF · GATE G1 NOT RECORDED SIGNED OFF · GATE G2 SIGNED OFF 2026-07-06 · GATE G3
SIGNED OFF 2026-07-06 · GATE G4 OPEN pending D2 (sign-off contested 2026-07-13) · GATE G5 SUB-SIGNED 2026-07-06. Two
open sequencing tensions were flagged 2026-07-14 (GATE 0/G1 never recorded signed off despite G2-G4 crossing) and are
**accepted AS-IS by this split** per the operator's 2026-07-23 unlock ruling — not re-litigated here. See the cefi
child's Phase 1 section for the full gate-by-gate detail.

---

## Phase 2+ — defi · tradfi · sports (same G0→G5, after cefi DONE)

- [ ] [INFRA] P1. **defi** — same gates; `window=expected, per-date-TVL=captured` 3-way (§1.3/§2.1: captured /
      `EXPECTED_NOT_ENOUGH_TVL` / `SOURCE_RETURNED_ZERO`); on-chain pool-creation genesis; **G4 catalogue-as-filter is
      load-bearing** (capture the catalogue pools in-window per (venue,chain,date), NOT the subgraph top-N — the cause
      of the 2026-06-24 overlap-flat stall); per-date TVL enumeration must be COMPLETE (316-vs-1,425 under-enumeration =
      G1/G2 defect); every catalogue protocol×chain has a source wired (uncovered: TRADER_JOE_V2/UNISWAP_V4/ORCA/KAMINO/
      VELODROME_V2/RAYDIUM = G1 gap); dual-form id (canonical `0x` key + glued `glued_pair_id`). **Execution detail +
      live work**: `/plans/archive/2026_06/defi_instrument_catalogue_and_capture_pipeline_2026_06_23.md`.
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
        completeness from our own capture. — **PARTIAL — §9 P0 schema-only rollout step landed** (via
        `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`, 2026-07-26, slot-7):
        `unified-api-contracts@1407b7fd` landed `CompletenessProbe`/`CompletenessProbeStatus`/`CompletenessProbeKind` in
        `canonical/crosscutting/honest_coverage.py` per `/codex/02-data/defi-completeness-oracle.md` §2, plus
        `factory_address_by_chain` populated (web-verified on-chain addresses) for the top-10 DEX protocols on
        `_ProtocolCapability`. Schema-only — **no probe implementations, no `--use-defi-oracle` wiring, no on-chain
        `poolCount` cross-check runs yet** — this checkbox stays open pending the actual probe implementation +
        drilldown surfacing described above.

> **Folded-in defi residual** (from I-1 consolidation 2026-06-26, `defi_venue_name_canonicalisation_and_reth_2026_06_17`
> archived; 4/5 done — moved here verbatim 2026-07-24):

- [x] ✅ [REGISTRY] P2. **NICE-TO-HAVE — add cbETH as `COINBASE-ETHEREUM` to the DeFi LST universe** (full new-venue add:
      `ALL_DEFI_VENUES` + `DEFI_VENUE_PHASE` + `defi_venue_capabilities.py` lst_rates/oracle_prices genesis 2022-08-26 +
      chain-qualified `LEGACY_DEFI_VENUE_ALIASES` + catalogue DEFI genesis). Care: `COINBASE` name collides with the
      CeFi spot exchange — use a chain-qualified alias only. Repo: unified-api-contracts + unified-trading-pm. (MIGRATED
      FROM: `defi_venue_name_canonicalisation_and_reth_2026_06_17`.)
      ✅ 2026-08-21 — **already fully done, stale todo.** Verified in code: `COINBASE-ETHEREUM` is in
      `unified-api-contracts/unified_api_contracts/registry/defi_venues.py:247` (`ALL_DEFI_VENUES`) and `:495`
      (`DEFI_VENUE_PHASE["COINBASE-ETHEREUM"]="live"`); `registry/defi_venue_capabilities.py:235` carries
      `oracle_prices: 2022-08-26`; `registry/venue_launch_dates.py:267` has the genesis (2022-08-24);
      `registry/venue_adapter_keys.py:192` has adapter key `"cbeth"`; `registry/market_data_categories.py:2806-2814`
      even comments that this exact todo "already produces" the capability record. Chain-qualified per the
      collision warning — no bare `COINBASE` reuse. Nothing to ship.

**tradfi** — same gates; Databento universe (GLBX/DBEQ/XCBF) + Yahoo (KRX/FX). MOVED (2026-07-24 split, content moved
verbatim, nothing dropped) to `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` — includes the "Already-fixed G1
code" detail + the tradfi historical progress log; `depends_on` the Phase-0 child for GATE 0.

- [ ] [INFRA] P1. **sports** — same gates; **fixtures ARE the instruments**, universe = the **~101 canonical MVP
      leagues** (`LEAGUE_REGISTRY`); api_football is the fixture-catalogue source + genesis; enrichment sources
      (footystats/ understat/transfermarkt/open_meteo/sfi) layer OFF the canonical fixtures (per-source coverage = a
      SUBSET → honest absence, not failure). Season/competition calendar = the per-day "expected" (off-season
      honest-empty, not a gap). Sports-specific foundation work (audit 2026-06-24, §3 of the standard):
  - [x] [DATA] P1. **G1 — RE-HOMED → `sports_p2_history_apifootball_2015_to_present_2026_06_27` (assigned_vm: NA,
        role-based); do NOT dispatch from here.** (was: G1 MVP-scope — delete the non-canonical league NOISE.)
        api_football FIXTURES enumerated **1,531 leagues (94 canonical + 1,437 non-canonical = ~106k rows, incl. 27.5k
        captured-we-don't-care-about)**. Scope the expected-universe enumeration to the ~101 canonical leagues; wipe the
        1,437 non-canonical (rows + objects, snapshot-first / consolidator-paused). A non-MVP league in the manifest is
        a G1 enumeration bug. Also: **7 of the 101 canonical leagues have ZERO fixtures rows** (registry/enumeration gap
        — diagnose).
  - [x] [DATA] P1. **G2 — RE-HOMED → `sports_p2_history_apifootball_2015_to_present_2026_06_27` (NA, role-based); do NOT
        dispatch from here.** (was: G2 diagnose the 2015–2017 ZERO-captured.) Canonical FIXTURES are **0 captured for
        2015–2017** (35,889 all-`empty_confirmed` across 76 MVP leagues that demonstrably played). One direct
        api_football probe (e.g. EPL 2016) decides: real subscription/tier history limit (→ honest absence, fix
        `SOURCE_COVERAGE_START`) vs backfill-bug (→ **scoped `--force`** re-run of 2015–2017 — `empty_confirmed` is
        skip-existing's blind spot, §2.2). Do this BEFORE trusting any sports coverage number.
  - [x] [DATA] P1. **G2 re-run the 40,041 FIXTURES `attempted_failed` — RE-HOMED →
        `sports_p2_history_apifootball_2015_to_present_2026_06_27` (NA, role-based); do NOT dispatch from here.**
        (2018/2021/2023 clusters — a quota/rate-limit/ endpoint pattern during those backfill runs). **Normal re-run**
        (failed = "missing"), NOT blanket `--force`. This is where the api_football credits should go — not a re-fetch
        of the 51,657 good captured cells.
  - [x] ✅ [CODE] P2. **Per-source honest-absence via `is_league_entity_covered`** — extend the coverage map to
        understat entities (XG/XG_SHOTS) so the understat error branch records `EXPECTED_NO_PROVIDER_COVERAGE` for
        non-covered leagues (the canonical 3-way). The 2-way shipped (instruments-service@18398c8) is interim-correct
        because the expected set is already source-filtered. Tracked: remediation #2c. — instruments-service
        understat.py: `_failed_league_names` → `_failed_canonical` → 3-way split (failed/empty/no-error-empty) confirmed
        in code; `EXPECTED_NO_FIXTURE` used (non-covered leagues excluded from expected set upstream)
  - [x] [DATA] P2. **footystats `ODDS` KEPT in IS — REVERSED (operator 2026-06-27: predictive signal; do NOT wipe).**
        (was: Odds = MTDS, NOT IS — wipe the misplaced IS footystats `ODDS`) (194,789 rows; KEEP `PREDICTIONS`
        in-house) + drop `"ODDS":"footystats"` from the source map + remove the IS odds-capture path. odds-api in MTDS
        is canonical (211,299 captured / 0 failed; api_football MTDS odds wiped 2026-06-24 — 1.4M rows + 231,532
        objects). Tracked: remediation #6.
  - [ ] [DESIGN] P1. **`depth_coverage` Tier-B = the FIXTURE-COMPLETENESS ORACLE** (n_teams→expected_fixtures, per-team
        game count, promotion/relegation, season window + expected gaps, **reschedule = final kickoff time**). The
        sports realisation of §2.1's external-truth denominator. SSOT plan:
        `/plans/archive/2026_06/sports_fixture_completeness_oracle_2026_06_24.md`.
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
      **ICE: fully verified clean, all legs** — `instruments-service@42cf8ba5` (2026-08-16), see this doc's own
      history/other todos.
      **CBOE — 2026-08-21 (T2) first pass had a real analysis error, CORRECTED same session (operator caught
      it).** The first pass claimed "zero VX-matching FUTURE rows" and flagged ~7,615 manifest rows as a
      "VIX/VX pollutant" — **both wrong.** Root cause: a naive `"VX"` substring search against `instrument_id`
      missed the real symbols, which spell `VIX` (`V`-`I`-`X`, not a `VX` substring), so the search found
      nothing in the 83-row live FUTURE catalogue slice and then, going back with a broadened `"VIX"|"VX"`
      regex against the manifest, swept up an UNRELATED population (thousands of calendar-spread-combo
      enumeration rows shaped `VX/<mo><yr>:1:S - VX<n>/<mo><yr>:1:B`) and mislabelled the whole mixed bag
      "pollutant." **Re-checked properly:**
      - `CBOE:FUTURE:VIX-USD@LIN-*` (83 live catalogue contracts, `raw_symbol` like `VX/M0`) is REAL,
        LIVE, ACTIVELY-CAPTURED Databento (XCBF.PITCH) data — 24,504 `captured` manifest rows under
        `venue=CBOE, instrument_type=FUTURE, data_type=futures_chain` (bundle-grain: the whole VX futures
        curve captures as one shard per day, so individual per-contract rows correctly carry no
        `instrument_id` — not a bug). This is exactly the CFE/VX data the codebase's own
        `scripts/restamp_cboe_vx_databento_provenance_2026_06_19.py` describes ("Databento (XCBF.PITCH) is
        the SOLE source... captured rows are preserved, no GCS data deleted") — **never a retirement
        candidate, should never be purged.**
      - The genuinely narrow, still-open item is the **VIX CASH INDEX** (a different product — the level,
        not the futures — historically Yahoo/Barchart-sourced per that same restamp script's own note: "VIX
        cash INDEX ... a separate source question"): only **17** manifest rows literally match `VIX` under
        `instrument_type=INDEX` (`ohlcv_15m`×13, `ohlcv_1s`×2, `ohlcv_1m`×2, all `source=databento`) — a
        SMALL number, not thousands — and the catalogue's live 10 INDEX rows for CBOE are all yield/treasury
        symbols (`^FVX`/`^IRX`/`^TNX`/`^TYX`/`2YY=F`), confirming no VIX-cash INDEX is live today. Whether
        these 17 manifest rows are the genuine "5 un-deleted INDEX (VIX cash)" 2026-06-24 pollutant, or
        something else entirely, was NOT conclusively re-derived this pass — the number moved from an
        estimated 5 to a measured 17, close enough to plausibly be the same thing, not far enough to assert
        it confidently.
      - Catalogue leg otherwise CLEAN: 236 live CBOE rows (COMBO 143, FUTURE 83, INDEX 10), **zero**
        `SPOT_PAIR` rows — the 91-SPOT_PAIR pollutant is gone from the catalogue.
      **CBOE VIX-cash-INDEX manifest rows — PURGED 2026-08-21, operator-directed (explicit "purge them, we
      don't want them" ruling after the re-measurement above).** Confirmed no GCS objects existed behind any
      of the 17 rows (all `row_count=0`, none `captured`) — a manifest-only purge, nothing to delete on the
      GCS leg. Built `deployment-service/scripts/migrations/instruments-service/
      purge_cboe_vix_cash_index_manifest_rows_2026_08_21.py` mirroring the canonical CAS-write pattern
      (`purge_deprecated_etf_manifest_rows_2026_05_16.py`) plus the mandatory 2026-08-15 manifest-write
      coordination gate (`_assert_consolidator_paused` hard-abort check, matching
      `retire_dex_pool_fees_all_captured_rows_2026_08_12.py`'s worked example). Sequence executed and verified
      at each step: paused `uts-prod-manifest-consolidator-market-data-tradfi-cron`, dry-run confirmed exactly
      the same 17 rows (none `captured` — the script hard-aborts if any matched row carries `captured`, as a
      safety net), `--apply` succeeded via CAS write (`if_generation_match`, no race — new generation
      returned), resumed the consolidator, then a FRESH read (new generation, not cached) confirmed 0 matching
      rows remain out of 14,475,101 total tradfi manifest rows. **The production purge is complete and verified,
      and the script itself has now shipped**: `deployment-service@abeca2a5b0` (landed on `live-defi-rollout`
      after the blocking peer refactor of `scripts/migrations/lib/templates/template_canonicalize.py` was fixed
      upstream). This closes CBOE's remaining gap on the retirement-completeness
      DoD's "manifest rows" leg — real VX futures data (`instrument_type=FUTURE`, `futures_chain` bundle,
      24,504 `captured` rows) is untouched, exactly as it must be. `/data-status` UI surface and `cefi`-domain
      equity-perp-singles legs still not checked this pass.

---

## Operator gates (the sign-off points — ask every time)

GATE 0 (Phase 0 done) · G1 · G2 · G3 · G4 · G5 per AG. No gate is crossed without operator sign-off. No parallel-up
across gates within an AG.

## Codex SSOT updates

- `/codex/02-data/instruments-foundation-and-catalogue-completeness.md` (the standard) — this plan executes it; now
  spans §0 gates · §0.5 observability-precondition · §1 completeness (incl. §1.2 cumulative-drawdown) · §2 layered
  coverage + §2.1 oracle (cefi/tradfi expiry-rules + DeFi TVL) + §2.2 reconcile + §2.3 drilldown-correctness · §6
  DeFi/TradFi cross-AG borrows · §7 tradfi/cefi-dated nuances (billable-venue, calendars, available_to, Tier-B,
  depth-aware re-fetch) · §8 retirement-completeness · §9 tradfi baseline. Keep this plan's todos in lockstep as the
  standard evolves.
- CLAUDE.md: add a one-line pointer to the standard.
- Compose: `availability-manifest-and-data-status.md` (expected-universe materialisation) ·
  `deployment-observability.md` (§0.5) · `honest_coverage_formula_consolidation_2026_05_19.md` (SSOT) ·
  `foundation-completion-gate-discipline.md` · `defi-canonical-naming-ssot.md` (defi) ·
  `tradfi-databento-sourcing-ssot.md` (tradfi allowlist).

---

## Related execution plans (per-AG detail lives in 4 children as of 2026-07-24; this plan is the cross-AG umbrella)

This plan is the gated umbrella standard + rolling status index. The per-AG / cross-cutting execution detail lives in:

- **Phase 0 (cross-cutting)** — `instruments_foundation_phase0_cross_cutting_2026_07_24.md` (NEW 2026-07-24 split).
- **cefi** — `instruments_cefi_g1_g5_gate_execution_2026_07_24.md` (NEW 2026-07-24 split; `depends_on` Phase-0).
- **tradfi** — `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` (NEW 2026-07-24 split; `depends_on` Phase-0).
- **defi** — `/plans/archive/2026_06/defi_instrument_catalogue_and_capture_pipeline_2026_06_23.md` (the G4 catalogue-as-filter
  exemplar + the live skip-cap/cursor + per-pool capture work). Already delegated pre-split — unchanged.
- **sports** — `plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` (was: pointing to
  `/plans/archive/2026_06/sports_fixture_completeness_oracle_2026_06_24.md` + `sports_golden_window_attempted_failed_remediation_2026_06_24.md`
  — corrected 2026-07-14, doc-reconciliation vr2#117: both moved (the former to `archive/2026_06/`, the latter to
  `active/issues/`) when the 2026-06-27 RE-HOMED banner above handed ALL sports G1→G5 dispatch to the coordinator plan;
  this section had not been updated to match). Already delegated pre-split — unchanged.

Per-AG plans MUST stay consistent with this umbrella's gates (G0→G5) + §0–§9 of the standard; this plan is the SSOT for
the _process_, those for the _AG-specific execution_.

---

## Condensed rolling status table (2026-07-24 — replaces the ~945-line historical Progress Log, moved verbatim to the

cefi/tradfi/Phase-0 children; see each child's own "Historical progress log" section for full detail + evidence)

| AG / track              | Gate status (as of last verified pass)                                                                                                                                                                                                                                                                                        | Full detail lives in                                                        |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Phase 0 (cross-cutting) | GATE 0 NOT RECORDED SIGNED OFF — 6 items still `- [ ]` (observability, Honest-Coverage v2, canonical-form single-SoT migration, etc.)                                                                                                                                                                                        | `instruments_foundation_phase0_cross_cutting_2026_07_24.md`                 |
| cefi                    | G1 NOT RECORDED SIGNED OFF (G1.1/G1.3/G1.4 prod-verified 2026-06-27; G1.2 partial) · G2 SIGNED OFF 2026-07-06 · G3/G3b SIGNED OFF 2026-07-06 · G4 OPEN pending D2 (contested 2026-07-13) · G5 SUB-SIGNED 2026-07-06, full sign-off held for MVP-backfill steady state                                                         | `instruments_cefi_g1_g5_gate_execution_2026_07_24.md`                       |
| tradfi                  | G1.a-e/G1.h SHIPPED 2026-06-25/27 (billable-venue guard, calendars, XCBF/DBEQ class fixes, `available_to` venue-truth) · G1.f.2 (VIX-15m retirement) COMPLETE 2026-06-26 · G1 retirement (ICE/OPRA/CBOE purge) OPERATOR-CONFIRM pending · G4 catalogue-as-filter bug FIXED 2026-06-25 · KRX/ICE mis-sourcing FIXED 2026-06-27 | `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`                     |
| defi                    | G4 catalogue-as-filter is the exemplar; live capture/skip-cap work in progress                                                                                                                                                                                                                                                | `/plans/archive/2026_06/defi_instrument_catalogue_and_capture_pipeline_2026_06_23.md` |
| sports                  | G1/G2 RE-HOMED to the golden-window-first coordinator; sports G1→G5 gated behind cefi DONE                                                                                                                                                                                                                                    | `plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md`  |

**All 5 catalogues were regenerated + promoted 2026-06-26** (cefi 345,920 · defi 7,416 · tradfi 814,012 · sports 1,608 ·
prediction 1,204,816 rows; monotonic ACCEPT) and the per-AG daily scheduler (T+1 producers → catalogue aggregation,
monotonic guard) went live the same day (deployment-service@9d0e457) — see the cefi child's historical log for the full
autonomous-run narrative and the Phase-0 child's "Autonomous run results" section for the cross-AG summary.

## Progress Log

- **na-eligibility-audit 2026-08-02** (re-confirms 2026-07-30; only change since = context-scout `context_scope`
  frontmatter, body byte-identical): KEEP-NA, valid — gated umbrella whose entire premise is per-gate operator sign-off
  ('ask every time'); GATE 0 is NOT RECORDED SIGNED OFF and the remaining todos are per-AG G-gate work delegated to
  child plans.
- **context-scout 2026-08-03**: re-scouted; refreshed context_scope (6 entries) — added the DeFi completeness-oracle
  codex doc + its `honest_coverage.py` source target (the doc's only genuinely-open inline work; the tradfi child kept).
  Found stale dead-end pointers in this doc's own "Related execution plans"/Phase-2 prose
  (`/plans/archive/2026_06/defi_instrument_catalogue_and_capture_pipeline_2026_06_23.md` and `/plans/archive/2026_06/sports_fixture_completeness_oracle_2026_06_24.md`
  are both archived, not left in context_scope) — flagged for `/plan-reconcile`, not rewritten here.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — reaffirms 2026-08-02 (unchanged): gated umbrella requiring
  per-AG operator G-gate sign-off; genuine mix of redirect/partially-AO-covered/under-specified items, none clear the
  whole-doc RECLASSIFY bar (assigned_vm flips per-doc, not per-item).
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (6 entries), still accurate — the only change since
  the 2026-08-03 marker was a 2026-08-06 na-eligibility-audit reaffirmation, no new content/targets.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — reaffirms 2026-08-06 (unchanged): gated umbrella requiring
  per-AG operator G-gate sign-off ("ask every time"); the 7 open items mix redirect-only header bullets (defi/sports
  execution lives in delegated child plans), a partially-shipped DESIGN item (DeFi completeness oracle — schema landed,
  probe implementation still pending), and genuine per-AG retirement/registry work — none clear the whole-doc RECLASSIFY
  bar.
- **na-eligibility-audit 2026-08-21** (cross-cutting tranche): KEEP-NA, valid — reaffirms the chain of prior audit passes (2026-08-02/06/07), unchanged: gated umbrella whose entire premise is per-gate operator sign-off ('ask every time — do not run ahead'); GATE 0 is not recorded signed off and remaining todos are per-AG G-gate work delegated to child plans plus a partially-shipped DeFi completeness-oracle DESIGN item.
