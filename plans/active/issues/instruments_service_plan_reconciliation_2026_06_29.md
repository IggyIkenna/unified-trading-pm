---
doc_type: issue
title: Instruments-Service Plan Reconciliation — open plans vs SSOT (UAC + 3 new plans + fresh codex)
summary:
  "Find-first reconciliation: score every open plan that touches instruments-service against the anointed truth set
  (live UAC code + the 3 new plans + freshness-gated codex + plans newer than the 2026-06-26 cutoff) to surface
  task-item CONTRADICTIONS, so they can be aligned in a later pass. This pass is read-only: it finds and classifies, it
  does NOT edit the subject plans. Section A = the SSOT assertion ledger (the yardstick). Section B = triage of all 67
  plans. Section C = deep-read findings. Section D = synthesis + proposed resolutions."
status: open
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, unified-api-contracts]
scope: [admin]
tags: [reconciliation, ssot-audit, plan-hygiene, instruments-service, honest-coverage, venue-registry]
related:
  [
    ../instrument_universe_registry_consolidation_2026_06_29.md,
    ../honest_coverage_v2_instrument_denominator_2026_06_28.md,
    ../honest_coverage_v2_opus_checkpoints_2026_06_28.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/04-architecture/instrument-universe-registry-consolidation.md,
  ]
created: 2026-06-29
parent_epic: instruments_master
priority: P1
source: [operator request 2026-06-29]
assigned_vm: NA
resolved_by:
locked_by: live-defi-rollout
last_updated: 2026-07-14 # bumped 2026-07-14 (was: 2026-07-03, unchanged despite substantive 2026-07-12 body corrections e.g. A19 §158; finding 129)
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_since: 2026-05-21
---

# Instruments-Service Plan Reconciliation (2026-06-29)

> **Read-only FIND pass.** Goal: surface every open-plan task item that CONTRADICTS the truth set, classify it, and
> propose a resolution — **without editing the subject plans**. Operator decides per-contradiction (or per-cluster) what
> to act on afterward.

## Truth-set / trust model (operator-locked 2026-06-29, FINAL)

**No plan is SSOT.** The only SSOT = **live UAC code + fresh codex**. A plan is trusted _only where it aligns with both
UAC and codex_; anywhere it doesn't, that misalignment is a contradiction to report. There is **no date-based trust
exemption** — every plan touching the contested surface is a subject, including the 06-27 v10 plans (they predate the
06-29 MVP-v12 landing and may misalign on defi).

- **SSOT (truth):** live UAC code (ultimate tiebreaker for concrete venue/MVP/config facts) + codex (freshness-gated — a
  doc whose git date predates the 2026-06-29 landings is the _stale side_, recorded as its own finding; see A20).
- **The 3 new plans** are trusted because they match UAC — they are the _aligned reference_, not a privileged tier.
- **`last_updated` is NOT trustworthy** — it was bulk-added to all plans on one day and is also bumped by agents on item
  completion. Ignore it. Use **`created`** only to prioritize reading order; use **git history at the item level** when
  recency actually matters.
- **Subjects = every plan with a contested-surface signal**, scored for alignment with UAC+codex regardless of date.

### Codex freshness check (git last-modified)

| Codex doc                                                    | git date   | verdict                                            |
| ------------------------------------------------------------ | ---------- | -------------------------------------------------- |
| `02-data/honest-coverage-model.md`                           | 2026-06-29 | ✅ FRESH — Tier-1-aligned (authoritative v2 model) |
| `04-architecture/instrument-universe-registry-consolidation` | 2026-06-29 | ✅ FRESH — Tier-1-aligned                          |
| `02-data/honest-absence-downstream-handling.md`              | 2026-06-27 | ✅ fresh enough (≥ cutoff)                         |
| `02-data/availability-manifest-and-data-status.md`           | 2026-06-27 | ✅ fresh enough (≥ cutoff)                         |
| `02-data/data-pipeline-correctness-hard-rule.md`             | 2026-06-25 | 🟡 borderline (process doc; not MVP/venue lists)   |
| `04-architecture/instruments-service-as-ssot-for-mtds.md`    | 2026-06-16 | ❌ **STALE** on venue-registry/MVP — see **A20**   |

---

## Section A — SSOT assertion ledger (the yardstick)

Each assertion = a normative fact a subject plan can contradict. `LANDED` = shipped ground truth; `IN-FLIGHT` = the
target end-state the new plans are still executing (a contradiction here is "will-conflict", flag as alignment-needed).
Citations are file:line or plan/commit.

### Domain 1 — Venue registry & IS-as-mirror

- **A1 `LANDED`** — IS venue producers READ UAC; hardcoded mirrors `_CEFI_VENUES` / `_TRADFI_VENUES` are **DELETED**.
  cefi via named `expand_cefi_tardis_endpoints()` (bare `OKX`→`OKX-SPOT/-SWAP/-FUTURES`, `COINBASE`→`COINBASE-SPOT`);
  tradfi via named `_TRADFI_NON_VENUE_KEYS={YAHOO_FINANCE}` filter; prediction reads
  `VENUES_BY_ASSET_GROUP[prediction]`. _(registry plan Phase 1 / instruments-service@4da6fe8)._ **Conflicts:** any task
  that adds/edits/maintains a hardcoded IS venue list, or treats IS as the venue SSOT.
- **A2 `LANDED`** — UAC `VENUES_BY_ASSET_GROUP` is the canonical venue universe per AG (market_data_categories.py:223).
  cefi members include `KALSHI-PERP`/`POLYMARKET-PERP` (asset_group=**cefi**, CFTC perps), plus `DERIBIT-COMBO`,
  `BINANCE-DELIVERY`, Tardis Tier-3 expansion venues. **Conflicts:** plans treating KALSHI-PERP as prediction, or
  omitting the perps/combo/delivery venues from the cefi universe.
- **A3 `LANDED`** — UAC bare `OKX`/`COINBASE` are **KEPT** (execution-context alias); the Tardis split lives **IS-side**
  only. The "push the split INTO UAC / drop bare forms" approach was **REJECTED** (cross-service breaking via UTL
  `Venue` enum). _(registry FINAL Decision A.)_ **Conflicts:** plans proposing to add `OKX-SWAP`/`COINBASE-SPOT` to UAC
  or drop bare `OKX`/`COINBASE`.
  - **CORRECTION (2026-07-12, finding id 98, §A2 "50 reclassified" blanket ruling):** the bare-`COINBASE` half of this
    REJECTED ruling was superseded by a later 'main' directive + the executed
    `coinbase_bare_name_migration_2026_07_06.md` plan (was: "bare COINBASE KEPT, drop-bare-forms REJECTED" — now: bare
    `COINBASE` was safely RE-KEYED to `COINBASE-SPOT` in `VENUES_BY_ASSET_GROUP["cefi"]`, landed
    unified-api-contracts@42270f63 2026-07-10, "feat(registry): migrate bare COINBASE cefi venue key to COINBASE-SPOT",
    on `live-defi-rollout`). The migration explicitly guarded against the exact `_CEFI_VENUE_FOLD` cross-service
    regression A3 warned about (see `market_data_categories.py:261-270` comment). **Bare `OKX` was NOT touched** — it is
    still KEPT alongside a new `OKX-SPOT` entry (2026-07-10), so A3's OKX half stands as originally written; only the
    COINBASE half is corrected here.
- **A4 `LANDED`** — **sports = TWO registries, EXEMPT from set-equality.** IS owns reference-data providers
  (`API_FOOTBALL`/`FOOTYSTATS`/`UNDERSTAT`/`TRANSFERMARKT`/`SOCCER_FOOTBALL_INFO`/`OPEN_METEO`); UAC sports = MTDS
  **odds** venues (`ODDS_API`/`PINNACLE`/`BETFAIR*`/`DRAFTKINGS`/`FANDUEL`). Do **NOT** merge. _(registry Decision C.)_
  **Conflicts:** plans that merge the two sports registries or expect odds venues in the IS producer.
- **A5 `LANDED`** — prediction venues `{POLYMARKET, KALSHI}` (binary markets) are **DISTINCT** from cefi
  `KALSHI-PERP`/`POLYMARKET-PERP`. **KEEP BOTH; no adapter collapse.** _(registry Decision B / INV-1.)_ **Conflicts:**
  plans proposing to collapse the prediction & perp adapters/venues into one.
- **A6 `LANDED`** — defi venue producer `_build_defi_venues()` stays **IS-hardcoded, EXEMPT** from set-equality; the
  "promote `_STATIC_DEFI_VENUES`/`_SOLANA_DEFI_VENUES` into UAC" task is **DROPPED** (already a subset). _(registry
  Decision D.)_ **Conflicts:** plans tasked with promoting IS defi venues into UAC.
- **A7 `IN-FLIGHT`** — Phase 2 = **UAC-derived adapter routing** (`VENUE_TO_ADAPTER_KEY` in UAC; factory resolves
  key→class; `CANONICAL_VENUE_TO_ADAPTER` stops being venue truth). NOT yet landed. **Alignment-needed:** plans that
  treat `CANONICAL_VENUE_TO_ADAPTER` / a frozen IS set as venue truth will conflict once Phase 2 lands.

### Domain 2 — DeFi MVP & denominator (UAC ground truth)

- **A8 `LANDED`** — `MVP_SCOPE_CONFIG_VERSION == 12` (mvp_scope.py:761). **Conflicts:** plans citing v11 or earlier as
  current (stale-number).
- **A9 `LANDED`** — `VENUES_BY_ASSET_GROUP["defi"]` == the **55** `phase=="live"` (IS-producible) venues; the **67**
  `phase=="pipeline"` venues are **EXCLUDED** from the honest-coverage denominator (defi_venues.py `DEFI_VENUE_PHASE`;
  market_data_categories.py:303). **Conflicts:** plans expecting the old ~122-venue defi superset in the denominator, or
  that re-add pipeline venues to live / to MVP coverage.
- **A10 `LANDED`** — `ROCKETPOOL-ETHEREUM` is **removed from `DeFiMvpRule.venues` and re-phased to `"pipeline"`** (NOT
  deleted from the registry; still in `defi_venues.py:59/417`). _(mvp_scope.py:557.)_ **Conflicts:** plans expecting
  ROCKETPOOL in MVP/live coverage; (NON-conflict: plans that merely reference it as a registered venue).
- **A11 `LANDED`** — the defi denominator-narrowing + `check_enumeration_completeness.py` is **OWNED by
  honest_coverage_v2_instrument_denominator** (explicit "do NOT edit that script here" comment,
  market_data_categories.py ~:300). **Conflicts:** plans editing that script / the defi denominator outside
  honest_coverage_v2 (duplicate-owner).

### Domain 3 — Honest Coverage v2 model (codex honest-coverage-model.md, fresh 06-29)

- **A12 `LANDED`** — Coverage is **TWO-LAYER**: Layer-1 (instrument-denominator completeness) **GATES** Layer-2
  (download coverage). A Layer-2 % is trustworthy only at Layer-1 = 100%. No flat single-number "100% coverage" claim is
  valid without the gate. _(honest-coverage-model.md / CK3.)_ **Conflicts:** plans claiming flat coverage % / "100%" /
  "G1 complete" without the two-layer gate.
- **A13 `LANDED`** — `coverage.json` **schema_version == 2** (additive: `layer_1`,
  `by_venue_instrument_type[_data_type]`, `by_day`, gate fields). **Conflicts:** plans referencing the old single-layer
  coverage schema as current.
- **A14 `LANDED`** — `measure_honest_coverage.py` reads the **freshest bucket** (blob.updated ranking) + **merges
  prd+non-prd**; the old "bucket with the most rows" selection was a bug (caused cefi 11.68% off a 20-day-stale bucket).
  **Conflicts:** plans relying on most-rows bucket selection / single-bucket coverage reads.
- **A15 `LANDED`** — `instrument_type` is a **canonical lowercase** manifest column (writer normalizes; MTDS@4c2a13b6);
  shard atom includes it; blanks / casing dupes / data_type-leakage are fixed bugs (backfill of historical rows still
  pending). **Conflicts:** plans assuming uppercase or blank-tolerant `instrument_type`, or a shard atom without it.
- **A16 `LANDED`** — opaque `VENUE_FETCH_FAILED` catch-all is **RETIRED** → `UNCLASSIFIED:{code}` + UAC
  `classify_venue_error()` decomposition. **Conflicts:** plans treating `VENUE_FETCH_FAILED` as the failure model.
- **A17 `IN-FLIGHT`** — exactly **ONE** expected-universe producer `expected_universe.build_expected(asset_group)`;
  re-mirrored per-AG enumerators are banned (folded into denominator Phase 1; **OPEN**, blocked on registry Phases 1-2).
  **Alignment-needed:** plans creating/maintaining a parallel expected-universe enumerator.
- **A18 `LANDED`** — Deribit options **"G1 complete" is FALSE** — `options_chain` effectively uncaptured (captured=1).
  **Conflicts:** plans asserting Deribit BTC/ETH options are complete/captured.
- **A19 `LANDED`** — **Certified Layer-1 (06-29):** cefi 65.91 | defi 69.44 | tradfi 51.43 | sports 30.77 | prediction
  66.67. **Layer-2 lower bounds:** cefi 37.86 | defi 57.55 | tradfi 88.81 | sports 100.00 | prediction 20.56. These
  **supersede ALL earlier coverage figures** (incl. cefi 11.68% stale-bucket and the 74.55% interim). **Conflicts:**
  plans citing other coverage numbers as current (stale-number). **Corrected 2026-07-12 (was: this A19 entry itself now
  the stale artifact; finding 345, §A2 B-queue ruling): these 06-29 figures were themselves superseded by the 2026-07-03
  UAC/writer reconciliation (cefi 65.91→79.55) and then by the 2026-07-06 15:01 UTC re-certification in
  `plans/archive/2026_07/layer1_remeasure_and_certify_2026_07_06.md:98` (cefi 73.61, defi 94.81, tradfi 51.43
  [BLOCKED-PLAN2], sports 30.77, prediction 66.67), which explicitly labels the intervening 79.55 number "stale
  (06-29)". cefi was re-measured again 2026-07-07 08:54 UTC to 72.60% — see
  `plans/archive/issues/cefi_layer1_denominator_gaps_2026_07_03.md:200`. Treat `layer1_remeasure_and_certify_2026_07_06`
  (+ its 07-07 cefi update) as the current Layer-1 certification, not this A19 entry.**

### Domain 4 — Stale-source flags

- **A20** — `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md` is **git-dated 2026-06-16** → **STALE** on
  venue-registry/MVP (predates registry consolidation + MVP v12; the registry plan's Phase-2 "codex flip" to fix it is
  still OPEN). Any plan leaning on this doc for venue/MVP truth is citing a stale source.

---

## Section B — Triage (contested-token signal across the 67 plans)

**Extracted 2026-07-25 (line-cap)** — the full cluster-agent roster + zero-hit set-aside list + wave 1/2 coverage
accounting now lives verbatim at
`plans/archive/2026_07/instruments_service_plan_reconciliation_triage_history_2026_07_25.md`. Pure process/scoping
record; Section C's findings stand on their own without it.

## Section C — Deep-read findings (wave 1: 12 cluster-agents, 31 plans; wave 2 C13–C15: +14 plans)

**Severity normalized by the orchestrator** (agents under-graded verdicts — a plan with a HIGH finding on an OPEN item
is MAJOR regardless of the agent's label). Grade = worst OPEN-item finding. `*` = finding sits on an OPEN `[ ]` item
(live, will mislead execution); historical/`[x]` claims are noted but not graded MAJOR.

### MAJOR-CONFLICT (open-item HIGH that would mislead an executing agent)

| Plan                              | Findings                                                                                                                                                                                                                                                                                                                                                                                              |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mvp_backfill_defi_onchain_v10`   | **A8/A10\*** L165 OPEN G2 gate `attempted_failed=0 AND expected_unattempted=0` runs against the v10 universe (incl. ROCKETPOOL-ETHEREUM in lst_rates) → under v12 ROCKETPOOL is `pipeline`, so the gate flags its gaps as blocking failures. L75-76/L91 v10 "ONLY scope authority" banner + Definition-of-100% embed the v10 denominator. → re-anchor the gate to the v12 / 55-live denominator (A9). |
| `mvp_backfill_cefi_tick_v10`      | **A12\*** L534 "Layer-1 … does NOT block G4 gate directly" — head-on contradiction of the gate model on the OPEN G4 item. **A8\*** L97 "mvp_scope.py v10 … the ONLY scope authority" (live=v12). **A18** L48/L167 "🟢 G1 COMPLETE … most Deribit options_chain shards already captured" (A18: captured=1).                                                                                            |
| `mvp_reconciliation_closeout_v10` | **A8\*** L44-46 "fix the PLAN to v10 — never the reverse … the single place that enumerates + closes every such conflict" + L57 "7 v10 decisions every plan must agree with" → declares the system reconciled at v10; the R1 re-scan table (L183-216) pre-dates v12 and is now stale on the defi-denominator axis.                                                                                    |

### MEDIUM (HIGH/notable finding, narrower or single-item)

| Plan                                               | Findings                                                                                                                                                                                                                                                              |
| -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `instruments_mtds_subset_consistency_remediation`  | **A1\*** L1795 OPEN "[MTDS] P2. De-duplicate the IS venue universe … make the fetch path read the UAC registry" — asks to do what the registry consolidation ALREADY shipped (IS@4da6fe8). **A16\*** L141 step-9 backfill targets retired `VENUE_FETCH_FAILED` label. |
| `data_completion_to_100_all_ag`                    | **A16\*** L99 OPEN "re-fetch the ~88k genuine `VENUE_FETCH_FAILED`" (retired → `UNCLASSIFIED:{code}`). **A12\*** flat "captured=100% of could-exist" success criterion, no gate. **A17\*** per-AG enumerator (alignment-needed).                                      |
| `path_to_100pct_backfill_mtds_is`                  | **A16\*** same VENUE_FETCH_FAILED re-fetch (near-duplicate of above). **A12\*** "Definition of 100%" flat. **A18\*** Deribit `options_chain` bundled into a generic tradfi backfill. **A17\*** per-AG enumerator.                                                     |
| `mvp_backfill_tradfi_ohlcv1m_v10`                  | **A8\*** L43 v10 "ONLY scope authority" banner. **A12** L126 "G2 GATE MET eu=0 af=0" presented as done, Layer-2-only. **A13** coverage %s maybe from pre-v2 harness.                                                                                                  |
| `cefi_deribit_binance_futures_bundle_verification` | **A18\*** L102-104 OPEN spot-check items implicitly assume Deribit options fetchable; backfill is gated → may run against empty corpus + misread NaN as failure.                                                                                                      |
| `data_status_tab_and_downloads_remediation`        | **A18\*** L333/L368 OPEN item + success-criterion operator note (2026-06-16) "BTC/ETH options FINE for now — do NOT widen" contradicts A18's certified "uncaptured."                                                                                                  |
| `mvp_scope_catalogue_tagging`                      | **A8** illustrative scope block lists tradfi `trades` (v10/12 = ohlcv_1m-only); **A2/A5/A15** same block uppercase types + omits KALSHI-PERP / KALSHI.                                                                                                                |
| `instruments_foundation_completeness`              | **A12\*** L243 OPEN "Layered coverage" Phase-0 todo doesn't bake in the two-layer gate / v2 schema; A7/A13/A17 low.                                                                                                                                                   |
| `mvp_catalogue_finalization_v10`                   | **A8** L52 v10 cite in "Codex SSOTs READ before executing"; **A20** L57 leans on stale `instruments-service-as-ssot-for-mtds.md` (low — draws no venue facts from it).                                                                                                |

### MINOR-DRIFT (low / historical only)

`cefi_manifest_canonicalisation` (A17 low) · `prediction_manifest_canonicalisation` (A17 low + a latent-trap P3 keyed on
A17) · `defi_manifest_canonicalisation` (A12 low — denominator already uses 55-set, aligned with A9) ·
`downstream_services_manifest_canonicalisation` (2 stale un-flipped duplicate checkboxes, work shipped elsewhere) ·
`master_data_canonicalisation_migration_catalogue` (A12 header + A19 historical, low) · `tradfi_massive_dual_source`
(stale status table + `[x]`-but-not-verified hygiene) · `v2_engine_venue_buildout` (A7 low, strategy-layer surface) ·
`capability_wizard_and_manifest` (A8 low — "53" vs own "57") · `pipeline_mode_source_batch_live_replay` (un-flipped
wrapper checkbox).

### ALIGNED (no actionable contradiction)

`tradfi_manifest_canonicalisation` · `sports_manifest_canonicalisation` · `data_pipeline_hardening_self_monitoring` ·
`migration_verification_orphan_safety` (ROCKETPOOL mention is captured-data, correct per A10) ·
`solana_defi_legacy_migration` · `master_to_live_defi` (stale content all historical, nothing live) ·
`prediction_venue_perps_and_live_clob_depth` (the SOURCE of the A2/A5 distinction) ·
`cryptovenue_equity_perps_and_tokenized_stocks` · `sports_odds_bookmaker_coverage_enumeration` ·
`tradfi_multisource_backfill`.

### Wave 2 (C13–C15, +14 previously-uncovered plans) — 0 MAJOR · 0 MEDIUM · 5 MINOR · 9 ALIGNED

The sports cluster is clean: **A4 two-registry split intact in every plan** (IS reference providers vs MTDS odds venues,
never merged). All findings are low and map to existing clusters — no new cluster, no change to the 3 operator
decisions.

- **MINOR-DRIFT (low only):** `sports_p1_golden_window_apifootball` (A12 "100% honest coverage" wording, all `[x]`) ·
  `sports_pipeline_to_100pct_golden_window_first` (A17 per-source enumerator + stale coordinator burn-down table) ·
  `sports_p2_daily_forward_catalogue_and_final_gate` (A12 success-criteria wording + A17) ·
  `sports_canonical_universe_and_apifootball_reference_expansion` (A19 dated 65.2% snapshot + A12 open P1 wording) ·
  `sports_p1_golden_window_e2e_gate` (A12 "FULL sports stack 100%" coordinator wording).
- **ALIGNED:** `sports_p2_history_reference_and_odds_2015_to_present` · `sports_p2_history_apifootball_2015_to_present`
  · `sports_fixtures_schema_split_completion` · `sports_p2_features_history_to_ml_ready` ·
  `sports_p0_sourcing_and_honest_coverage_correctness` · `unified_deployment_health_cockpit` (passthrough coverage tile)
  · `codex_violations_ratchet_to_five` · `work_split_2026_05_22_ikenna` · `repo_scripts_governance_audit`.

**Full tally (45 deep-read):** 3 MAJOR · 9 MEDIUM · 14 MINOR-DRIFT · 19 ALIGNED. Wave-2 low findings feed clusters D2b
(A12 wording), D6 (A17 per-source enumerators), D8 (stale snapshot/burn-down hygiene).

## Section D — Synthesis: cross-plan clusters + proposed resolutions

Findings collapse into **9 clusters**. ⚖️ = needs an operator decision (not auto-fixable); 🔧 = mechanical/auto-fixable
in the later alignment pass.

### D1 ⚖️ — v10→v12 MVP version drift (DOMINANT cluster)

**Plans:** `mvp_backfill_defi_onchain_v10`, `mvp_backfill_cefi_tick_v10`, `mvp_backfill_tradfi_ohlcv1m_v10`,
`mvp_catalogue_finalization_v10`, `mvp_reconciliation_closeout_v10`. **SSOT:** A8 (v12), A9 (55-live denom), A10
(ROCKETPOOL→pipeline). All 5 created 2026-06-27, two days before MVP-v12 landed. The "`mvp_scope.py` **v10** = the ONLY
scope authority" banners are _standing instructions to executing agents_, not historical notes. **Live risk:** the OPEN
G2 gate in `mvp_backfill_defi_onchain_v10` (L165) would mis-fire on ROCKETPOOL; `mvp_reconciliation_closeout_v10` would
declare the system reconciled at v10. **Proposed resolution — operator picks:** (a) **update banners to v12 in place +
re-run the closeout reconciliation at v12** (preserves the plans), or (b) **archive the v10 backfill + closeout plans as
done-at-v10 and open a single `mvp_v12_defi_exclusion_followup` plan** carrying only the still-open G2 gate + a v12
re-scan. Either way the OPEN `defi_onchain` G2 gate MUST be re-anchored to the 55-live denominator **before** it is run.

### D2 ⚖️ — Layer-1 does not gate Layer-2 (A12)

**(a) Operator-decision item:** `mvp_backfill_cefi_tick_v10` L534 explicitly carves out "Layer-1 … does NOT block G4
gate directly." A12 says a Layer-2 % isn't trustworthy until Layer-1=100%. **Is the G4 gate an intentional,
operator-sanctioned Layer-2-only backfill gate, or must it adopt the two-layer gate?** Operator's call. **(b) 🔧
Definitional (med/low):** flat "100% = captured/could-exist" definitions missing the gate qualifier — `data_completion`,
`path_to_100pct`, `master_data_canonicalisation_migration_catalogue`, `defi_manifest`, `instruments_foundation`. →
mechanical: add the two-layer-gate qualifier citing `honest-coverage-model.md`.

### D3 ⚖️ — Deribit options treated as complete/closeable (A18)

**Plans:** `mvp_backfill_cefi_tick_v10` ("G1 COMPLETE"), `cefi_deribit_bundle` (spot-check assumes fetchable),
`data_status_tab` (operator note "FINE for now — do NOT widen"), `path_to_100pct` (options_chain in generic backfill).
**SSOT:** A18 (captured=1, effectively uncaptured). **Operator-decision item:** the `data_status_tab` note is a prior
operator stance (2026-06-16) that A18 overturns — **reaffirm "fine for now" or update to track the real gap?** The rest
→ 🔧 annotate `options_chain` as a known Layer-1 gap, gate the spot-checks behind ">0 captured."

### D4 🔧 — Retired VENUE_FETCH_FAILED in OPEN re-fetch tasks (A16)

**Plans:** `data_completion_to_100_all_ag` L99, `path_to_100pct_backfill_mtds_is` L99, `instruments_mtds_subset` L141.
Open tasks target the retired `VENUE_FETCH_FAILED` label (→ `UNCLASSIFIED:{code}` + `classify_venue_error()`). →
mechanical: rewrite the open tasks to query the new error taxonomy. (Historical `[x]` refs in `cefi_deribit_bundle` need
no action.)

### D5 🔧 — Open work to do an already-shipped consolidation (A1)

`instruments_mtds_subset_consistency_remediation` L1795 OPEN item "make the fetch path read the UAC registry / delete
the `_*_VENUES` mirrors" is already done (IS@4da6fe8). → close as superseded after a no-regression check.

### D6 — Single expected-universe producer / per-AG enumerators (A17, IN-FLIGHT → alignment-needed)

**Plans:** `cefi_manifest`, `prediction_manifest`, `sports_manifest`, `data_completion`, `path_to_100pct`,
`instruments_foundation`, `master_data_canonicalisation_migration_catalogue`. These run/maintain per-AG
`_enumerate_v2_*` / `enumerate_expected_universe.py`. NOT a now-conflict — A17's single `build_expected()` is in-flight
(blocked on registry Phases 1-2 + folded into `honest_coverage_v2`). → annotate each with the fold-in dependency; no
edit until `build_expected` lands. (This is the SAME work the honest_coverage_v2 plan already owns — see A11/A17.)

### D7 — Adapter-routing awareness (A7, IN-FLIGHT → alignment-needed)

`instruments_foundation_completeness`, `v2_engine_venue_buildout` lean on `CANONICAL_VENUE_TO_ADAPTER` as venue truth.
Phase 2 (UAC `VENUE_TO_ADAPTER_KEY`) will deprecate that. → annotate; no action until Phase 2 lands.

### D8 🔧 — Stale illustrative blocks + plan hygiene (A2/A5/A8/A15, low)

`mvp_scope_catalogue_tagging` illustrative scope block (tradfi `trades`→ohlcv_1m-only; uppercase→lowercase types; add
KALSHI-PERP + KALSHI) · `capability_wizard` "53"→"57" archetypes · un-flipped duplicate checkboxes in
`downstream_services_manifest`, `tradfi_massive_dual_source`, `pipeline_mode_source_batch_live_replay`. → doc-accuracy
cleanup, low priority.

### D9 🔧 — Stale codex source lean (A20)

`mvp_catalogue_finalization_v10` lists the 06-16-stale `instruments-service-as-ssot-for-mtds.md` as a "read before
executing" SSOT. The codex flip that fixes the doc itself is already an OPEN item in
`instrument_universe_registry_consolidation_2026_06_29` (Phase-2 codex flip). → annotate the citation as stale-on-MVP;
the doc fix is tracked there.

### Headline for the operator (3 decisions)

1. **D1 — v10 MVP plans:** update-in-place to v12 + re-run closeout, OR archive-as-done-at-v10 + single v12 follow-up?
   (Hard prerequisite either way: re-anchor the OPEN `mvp_backfill_defi_onchain_v10` G2 gate to the 55-live denominator
   before any run.)
2. **D2a — cefi_tick G4 gate:** intentional Layer-2-only exception, or bring under the two-layer gate?
3. **D3 — Deribit options stance (`data_status_tab` note):** reaffirm "fine for now" or update to track the A18 gap?

Everything else (D2b, D4, D5, D8, D9) is mechanical and can be applied in a follow-up alignment pass once the 3
decisions are made; D6/D7 are in-flight alignment notes requiring no edit yet.

## Section E — Pass 2 (adversarial verification + ledger-completeness critique)

A second pass (Opus ledger critic + code-grounded skeptics) tested the find-pass conclusions against live code. It both
**refuted over-graded findings** and **exposed real ledger gaps**. The find pass (Sections A–D) is a single-vote FIND;
Section E is the verified correction layer — where they conflict, **E wins**.

### E.1 — Corrections to Section C/D findings (verified vs code)

- **D1 (the headline MAJOR) — REFUTED / DOWNGRADE to MINOR.** Claim was: the OPEN G2 gate in
  `mvp_backfill_defi_onchain_v10` would mis-fire on ROCKETPOOL under v12. It will NOT. `measure_honest_coverage.py` +
  `check_enumeration_completeness.py` resolve scope **live from UAC at runtime** (`VENUES_BY_ASSET_GROUP` + `is_mvp` +
  `DeFiMvpRule.venues` v12) — no hardcoded v10 list. ROCKETPOOL (`phase=="pipeline"`, removed from `DeFiMvpRule`)
  produces no `expected_unattempted` skeleton, so it can't trip the gate; it isn't even in the plan's gap-list
  (ETHENA/ETHERFI/JITO/LIDO/MARINADE). **The prerequisite "re-anchor the G2 gate before running" was WRONG — the gate is
  already safe.** Remaining D1 issue = stale "v10 scope authority" _banner text_ only (low/med). **So the IS audit has 2
  MAJOR, not 3** (cefi_tick + reconciliation_closeout banners remain; the operational-misfire risk is gone).
- **A18 (Deribit options uncaptured) — INDETERMINATE / likely partly stale.** `captured=1` was the _pre-G1_ state; a G1
  backfill ran 2026-06-28 (7 SPOT VMs) and the G4 final-verify is still open. Settle with a live
  `measure_honest_coverage --asset-group cefi` filtered to DERIBIT `options_chain` — do not cite `captured=1` as
  current.
- **A16 (VENUE_FETCH_FAILED retired) — CONFIRMED.** Open re-fetch tasks target historical GCS rows → relabel-only (D4
  stands).

### E.2 — A-ledger gaps (MISSING/WRONG) — the systematic blind spot

The A-ledger is accurate on venue-set + defi-MVP axes but treats the **catalogue / reference-data half of IS** as a
black box. High-leverage additions (each is an axis a scored-ALIGNED plan may sit on, untested):

- **A21 (was MISSING-10)** — Sports MVP = the canonical **94-league FOOTBALL** universe (derived
  `_mvp_football_league_ids()`, mvp_scope.py:317-323), 7 non-football leagues EXCLUDED. **Wave-2 graded 10 sports plans
  on A4 alone — league-membership was never tested.**
- **A22 (MISSING-7)** — Per-venue/per-itype MVP data_type carve-outs: COINBASE-SPOT/-FUTURES = `{trades}` only (no
  book5), Deribit OPTION = `{options_chain}` only (mvp_scope.py:465-483,770-781). A "100% Coinbase depth" / per-strike
  item contradicts MVP.
- **A23 (MISSING-9)** — TradFi tick is SUPPRESSED: `TRADFI_TICK_DATA_WINDOWS = []` (market_data_categories.py:1322-1353)
  — only OHLCV in scope. An OPEN tradfi `trades`/`tbbo`/`mbp_10` fetch item spins silent-0-row VMs.
- **A24 (MISSING-8)** — CeFi MVP capture universe is PERP-GATED (`is_in_mvp_capture_universe`) w/ named spot-only
  exceptions (UPBIT + 28-member STAKING_SPOT). A plan expecting every spot pair MVP over-counts the cefi denominator.
- **A25 (MISSING-1)** — Catalogue lifecycle is VENUE-TRUTH-FIRST w/ thin-day liveness
  (`build_instrument_catalogue.py`:674-701); last-seen only as labelled fallback. This is the _producer of the Layer-1
  denominator_; false-delist = fake-honest "complete".
- **A26 (MISSING-13)** — Availability gates on listing-window / chain-genesis / venue-launch; IS owns
  `source_archive_url_template`/`coverage_start/end`/`listed_at`/`delisted_at`; MTDS must NOT hardcode these (the A20
  doc's _contract_).
- **A27 (MISSING-12)** — `EXPECTED_COVERAGE_BY_ASSET_GROUP` is a THIRD denominator (capability ≠ expected ≠ MVP); the
  `out_of_scope` data-status view keys off it, not `is_mvp`.
- **A28 (MISSING-3/HOLE-3)** — Live UAC↔writer **validity-matrix gap + ASTER carve-out contradiction** (tracked in
  `honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md`). Plans touching `VALID_DATA_TYPES_*` / ASTER
  capabilities had no yardstick.
- **WRONG-1 (amend A19)** — the certified Layer-1 %s are an **UPPER bound** where UAC under-specifies (codex CK3 caveat
  the ledger dropped). A plan citing 65.91% as a hard "done" bar measures against a number the SSOT says will move. Also
  (minor) the live artifact is `coverage_v3.json` (cert commit instruments-service@051e5a8), not `coverage_v2`.

### E.3 — Pass 3: re-score on the new axes (did any plan EXPLOIT the gaps, or were they latent?)

Re-scored the specific plans sitting on each new A21–A28 axis. Result: **2 axes exploited (new real findings the
find-pass structurally could not see), the rest latent-clean (plans were genuinely aligned, just previously unscored).**

**EXPLOITED — new contradictions:**

- **A23 (tradfi tick suppressed, `TRADFI_TICK_DATA_WINDOWS=[]`):**
  - `path_to_100pct_backfill_mtds_is` — **HIGH**: open `[~]`/Step-3 items "backfill … tradfi
    **trades/ohlcv/options_chain/tbbo**" would fetch tradfi `trades`/`tbbo` → silent-0-row VMs. Annotate as post-MVP;
    only `ohlcv_1m` is an MVP fetch target.
  - `tradfi_massive_dual_source` — **MED**: Phase-4b rebuild + success-criteria premised on fetching Massive tradfi
    `trades`/`tbbo`.
  - `data_completion_to_100_all_ag` — **MED**: folded-in Step-3 names tradfi `trades`/`tbbo` as fetch targets.
- **A28 (UAC↔writer validity-matrix gap + ASTER carve-out):**
  - `master_data_canonicalisation_migration_catalogue` — **MED**: open `G1.dry-run`/`G1.run` verify-slices + the Era-B
    purge use `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE` without cross-referencing the matrix-reconciliation issue
    doc; the ASTER book5/liquidations carve-out means signing-off/purging the ASTER slice could mis-handle data that
    physically exists.

**LATENT-CLEAN (verified aligned on the new axis, not just unscored):**

- **A21 (sports = 94-league football)** — all **13 sports plans ALIGNED**; none carried the old 2-league (EPL+LA_LIGA)
  drift into open items (the drift lived in `mvp_scope.py`, fixed there). The biggest "we never tested this" hole closes
  clean.
- **A22 (Coinbase trades-only / Deribit options-only)** — ALIGNED; `mvp_backfill_cefi_tick_v10` explicitly absorbed the
  v11 Coinbase-book5 cut + Deribit-options-only; `cefi_deribit…` spot-checks are options_chain-level.
- **A24 (cefi perp-gate)** · **A25 (venue-truth delisting / thin-day liveness)** · **A26 (listing-window/genesis from
  UAC)** — all ALIGNED; the catalogue plans frame these as fixes-to-land, not broken premises (`instruments_foundation`
  G3b is a verbatim restatement of the A25 fix; `migration_verification` reads
  `get_chain_genesis_date`/`get_protocol_launch_date`).
- **WRONG-1 (A19 upper-bound)** — no plan cites 65.91% as a hard "done" bar in an open item.

**Net pass-3:** 4 new tradfi-tick/ASTER findings (1 HIGH, 3 MED) + the 8 latent axes confirmed clean. The "IS audit
under-tested ~12 plans" worry resolves to **4 real misses, the rest genuinely aligned**.

## Section F — Consolidation & cleanup execution plan (MVP-cefi FIRST)

Goal: collapse the IS/MVP plan set to a clean, non-contradictory spine so the remaining real work is crisp — **before**
executing engineering items. MVP = **cefi-completeness first** (the foundation plan is cefi-gated; defi/tradfi/sports
gated behind "cefi DONE"). **Non-MVP consolidation deferred** to a later pass: tradfi-tick (A23), sports, and ALL MTDS
(M32/M33/M36 + the MTDS doc's MD-clusters). ⚖️ = needs operator sign-off (locked-plan archival is never-autonomous).

### F.1 — Plan dispositions (MVP-cefi set)

| Plan                                                       | open/done | disposition                                                                                                |
| ---------------------------------------------------------- | --------- | ---------------------------------------------------------------------------------------------------------- |
| `instruments_foundation_completeness`                      | 56/25     | **KEEP** — MVP-completeness spine (cefi G2–G5).                                                            |
| `honest_coverage_v2_instrument_denominator`                | 2/13      | **KEEP** — Layer-1 denominator SSOT (`build_expected` + drift-guard).                                      |
| `mvp_backfill_cefi_tick_v10`                               | 1/6       | **KEEP** until G4 closes; clean stale v10 banner.                                                          |
| `cefi_manifest_canonicalisation`                           | 26/56     | **KEEP** — active cefi v8→v9 apply.                                                                        |
| `cefi_deribit_binance_futures_bundle_verification`         | 2/5       | **KEEP** — cefi Deribit verify.                                                                            |
| `mvp_scope_catalogue_tagging`                              | 2/8       | **KEEP** — MVP tagging.                                                                                    |
| `honest_coverage_uac_writer_matrix_reconciliation` (issue) | open      | **KEEP** — ASTER/matrix fix tracker.                                                                       |
| `honest_coverage_v2_opus_checkpoints`                      | 0/3       | ⚖️ **ARCHIVE** — CK1–3 certified, done.                                                                    |
| `mvp_catalogue_finalization_v10`                           | 0/9       | ⚖️ **ARCHIVE** — done.                                                                                     |
| `mvp_reconciliation_closeout_v10`                          | 0/9       | ⚖️ **ARCHIVE + v12-superseded banner** — done at v10; stop it reading as the live reconciliation baseline. |
| `path_to_100pct_backfill_mtds_is`                          | 22/0      | ⚖️ **MERGE → `data_completion`** (spec vs execution near-dup), then archive-as-superseded.                 |
| `data_completion_to_100_all_ag`                            | 11/132    | **KEEP** — absorbs path_to_100pct's live cefi items.                                                       |
| `instruments_mtds_subset_consistency_remediation`          | 60/50     | ⚖️ **REVIEW** — 60 open, heavy foundation overlap; fold cefi items into foundation (focused pass).         |

### F.2 — Cleanups in the KEEP plans (mechanical; after F.1 sign-off so we don't clean a plan we archive)

- `mvp_backfill_cefi_tick_v10`: v10→v12 banner note (A8); annotate A18 Deribit "G1 complete" as pending a live cefi
  `options_chain` query (E.1); D2a — note the G4 Layer-1-gate carve-out as operator-sanctioned-or-fix.
- `data_completion_to_100_all_ag`: relabel the open cefi `VENUE_FETCH_FAILED` re-fetch task → "cells whose legacy
  `error_reason` was VENUE_FETCH_FAILED" (A16, verified retired-from-live-emission).
- `honest_coverage_v2_instrument_denominator` + the ASTER issue: annotate the ASTER enumerator over-seed (A28) as the
  cefi-denominator-correctness blocker (UAC correct; enumerator over-seeds; fix = apply `VENUE_DATA_TYPE_CAPABILITIES`
  carve-out in `enumerate_expected_universe.py`). Also flag the stale `mvp_scope.py:413` comment ("ASTER …
  book_snapshot_5").
- `cefi_manifest_canonicalisation`: annotate the per-AG `_enumerate_v2_cefi` item with the fold-into-`build_expected`
  (A17) dependency.

### F.3 — Distilled cefi-MVP remaining real work (post-consolidation — the "what needs to be done")

1. **ASTER enumerator carve-out (A28)** — removes a permanent cefi-MVP fake-incompleteness (book5/liquidations seeded
   but captured=0). Small, diagnosed, in-scope.
2. **Single expected-universe producer `build_expected` (A17)** — collapse the two-producer divergence (the root of #1).
3. **Foundation cefi gates** G2 (backfill) · G3 (scheduler-runs-latest) · G3b (dated `available_to` venue-truth) · G4
   (MTDS per-day filter) · G5 (coverage-rises) + verification discipline (key-overlap, FetchEvidence silent-cap audit).
4. **`mvp_backfill_cefi_tick` G4 close** + **`cefi_manifest` v9 apply close**.

### F.4 — Sequence

(1) ⚖️ operator sign-off on F.1 archive/merge/review → (2) execute F.2 mechanical cleanups on the KEEP plans + the
archival ritual on the agreed plans → (3) THEN the F.3 engineering items, cefi-first. Non-MVP consolidation = a later
pass.

## Section G — Contradiction review log (per-item; Ikenna decides each)

> Walking the cefi-MVP contradictions one at a time (index C1–C9). Each entry: the contradiction, the ground-truth
> check, the corrected verdict, the decision options. **Kept LOCAL/unpushed per operator 2026-06-29; Ikenna decides each
> resolution when back.** Index: C1 ASTER over-seed · C2 two expected-universe producers · C3 v10-scope-authority banner
> · C4 G4 Layer-1-gate carve-out · C5 Deribit "G1 complete" · C6 retired VENUE_FETCH_FAILED re-fetch · C7 A19
> upper-bound · C8 mvp_scope.py:413 ASTER comment · C9 EXTENDED candle-path failure-record.

### C1 — ASTER `book_snapshot_5` / `liquidations` in the cefi-MVP denominator — CHECKED vs official API; verdict CORRECTED

**Contradiction (as first flagged, A28):** `enumerate_expected_universe.py` seeds `expected_unattempted` for
`(ASTER, perpetual, book_snapshot_5)` + `(…, liquidations)` with `captured=0` forever → flagged as enumerator
"over-seed" of cells ASTER supposedly can't produce. UAC `VENUE_DATA_TYPE_CAPABILITIES["ASTER"]` =
`{trades, derivative_ticker, perp_funding}` (omits book5/liquidations, "no wired fetch path"); but `mvp_scope.py:413`
comment says ASTER surface = "trades + book_snapshot_5 + derivative_ticker".

**Ground-truth check — official AsterDex futures API (`fapi.asterdex.com`):**

| data_type          | REST (historical backfill)                              | WebSocket (live)                     |
| ------------------ | ------------------------------------------------------- | ------------------------------------ |
| book_snapshot_5    | ❌ `/fapi/v3/depth` = current snapshot only; NO archive | ✅ `@depth5` (100/250/500 ms)        |
| liquidations       | ❌ no `allForceOrders`-type endpoint                    | ✅ `@forceOrder` / `!forceOrder@arr` |
| trades (aggTrades) | ✅ `/fapi/v3/aggTrades` (startTime/endTime/fromId)      | ✅ `@aggTrade`                       |
| funding            | ✅ `/fapi/v3/fundingRate` + `/premiumIndex`             | ✅ `@markPrice`                      |

Sources: `docs.asterdex.com/product/aster-perpetuals/api` · `github.com/asterdex/api-docs`.

**CORRECTED verdict:** ASTER book5 + liquidations are **live-capturable (WS), NOT historically backfillable (no REST
archive).** Therefore:

- UAC `VENUE_DATA_TYPE_CAPABILITIES["ASTER"]` is **WRONG/incomplete** — it omits book5/liquidations, which ARE
  produceable (live). "No wired fetch path" = a real GAP, not an impossibility.
- The enumerator bug is **not "garbage over-seed"** — it seeds book5 across ALL history (no historical source) instead
  of: typed honest-absence for the historical window + expected from the live-wired date forward.
- `mvp_scope.py:413` ("ASTER … book_snapshot_5") is actually **RIGHT** → this **INVERTS C8** (the "stale comment"
  finding). `honest_coverage.py:212` ("ASTER REST exposes only current-book") is right about REST but misses the live
  WS.
- **Not ASTER-only:** LIGHTER / EXTENDED / PACIFICA (the CLOB-perp-DEX class) likely share the same live-WS / no-REST
  profile.

**Decision (Ikenna) — now a SCOPE choice, not a capability fact (data exists live):**

- **(a) Wire it** — connect MTDS to ASTER `@depth5` (+ `@forceOrder`) like HYPERLIQUID; book5 captured live-forward;
  historical book5/liquidations = typed honest-absence; FIX UAC capability to include book5.
- **(b) Carve out of MVP** — decide book5/liquidations not MVP-required for ASTER; remove from enumerator + UAC + the
  comment.
- **(c) Hybrid (Harsh+Claude lean)** — book5 IS the CLOB-perp MVP surface → wire live (a); liquidations not in the MVP
  comment → carve (b). Historical window honest-absent either way.

**UAC + redundancy analysis (2026-06-30) — REFRAMES the decision toward CARVE:** what UAC says ASTER provides
(`market_data_categories.py:1135-1148`): `trades` (_"aggTrades REST, **~30-day rolling depth**"_ — thin history!),
`derivative_ticker`, `perp_funding` (_"pre-2024 funding is **BINANCE-PROXIED**, NOT Aster-native"_). `book_snapshot_5` +
`liquidations` are _"out of scope (no wired fetch path)."_ **Is the same data available elsewhere?** Checked the live
cefi manifest (ASTER = 431 instruments / 191 bases):

- **book5** is captured from **18 other venues** incl. **HYPERLIQUID** (the directly-comparable CLOB-perp DEX, book5
  wired since 2023-04-15); **86 of ASTER's 191 bases also list on HYPERLIQUID** (BTC/ETH/BNB/SOL/DOGE/AVAX…). So the
  _instrument's_ perp microstructure is well-covered without ASTER's book5.
- **liquidations** comes ONLY from CEX-futures (Binance/Bybit/OKX/Deribit/Bitfinex/Bitget/Kraken-Futures) **+ GMX** —
  **no CLOB-perp DEX provides it** (not HL, not ASTER). Structurally a CEX data_type.

**→ Refined recommendation:** **liquidations → carve (clear)** — CEX-only; sibling HL lacks it; over-seeding it is
wrong. **book5 → carve for data-completeness; wire live-forward ONLY IF ASTER is an MVP _execution_ venue** (its own
book matters only for ASTER fills/slippage; the instrument's book5 is already covered by HL + 17 CEXes). **The keystone
question is ASTER's role: execution venue → wire book5 live; data/reference venue → carve both.** (Niche wrinkle: ASTER
lists a few tokenized-equity perps — AAPL/AMZN/AVGO/BRKB — not on crypto venues; minority of the 191.)

**STATUS:** ✅ **RESOLVED — IKENNA DECIDED 2026-07-03 (wire live-forward, the prediction-AG pattern).** Verbatim intent:
ASTER **batch** gives funding rates + index + aggTrades ("dump in trades canonical"); **live** adds liquidations +
book_snapshot_5 on top — "similar to how in predictions AG we can't get orders info for batch but we can stream live and
store; eventually this builds us a history for the data types we can't get directly from batch." At the canonical grain:
**batch+live = `trades` (aggTrades) / `derivative_ticker` (index+mark) / `perp_funding`** (today's capability set
stands); **live-only-forward = `book_snapshot_5` + `liquidations`** (history before the wire date = typed honest absence
— the 2026-07-03 17,282-row purge of the historical over-seed stays correct). Instruments + manifests must support the
mode split; Ikenna: "I think we would have that capability already — please check and report back."

**CAPABILITY CHECK (Harsh session, 2026-07-03) — mostly YES, four named gaps:**

_Already in place:_

1. **The live connectors literally exist**: MTDS `live/connectors/aster_book_liq_ws.py` — book_snapshot_5 via
   `wss://fstream.asterdex.com/stream` `<sym>@depth5@100ms` + liquidations via `!forceOrder@arr`, docstring already says
   "LIVE-ONLY data_types captured going forward". Built per `issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md` BUG #4.
2. **The manifest/pipeline spine supports it**: v9 `pipeline_mode = {mode}_{source}` distinguishes `live_aster` from
   `batch_aster` rows; the live=batch event-facade sink is the deployed default; the in-cefi precedent runs today
   (KALSHI-PERP live book5 VM `cefi-kalshi-perp-book-snapshot`, `live_kalshi_perp` rows in the manifest).
3. **The expectation-registry pattern exists**: `EXPECTED_COVERAGE_BY_ASSET_GROUP` already encodes the prediction
   precedent (KALSHI/POLYMARKET `book_snapshot_5`, "Batch=live: same canonical data_type") — and its `_CEFI["ASTER"]`
   entry ALREADY lists `trades, book_snapshot_5, derivative_ticker, liquidations`.

_Gaps (the "report back"):_

1. **Connector never wired**: `aster_book_liq_ws.py` is NOT in `live/connector_registry.py` (0 references) and has never
   run — the live cefi manifest holds **zero `live_aster` rows** (only `batch_aster`: trades captured=180 /
   derivative_ticker captured=899 / ec≈461k). Register + launch the live VM.
2. **UAC self-contradiction on exactly these two types**: `EXPECTED_COVERAGE._CEFI["ASTER"]` includes book5+liquidations
   (data-status scoping says expected) while `VENUE_DATA_TYPE_CAPABILITIES["ASTER"]` omits them (honest-coverage
   carve-out says cannot-exist). Ikenna's decision reconciles them — both types belong in the capability table **with
   `start_date` = the live-wire date**.
3. **Date-gated seeding is the one real missing capability**: the capability table's VALUE is a per-(venue,`data_type`)
   `start_date`, but NEITHER `enumerate_expected_universe._row_data_types` NOR the Layer-1 checker reads
   `get_venue_data_type_start_date` — membership-only checks. Adding book5/liquidations to ASTER's entry TODAY would
   re-seed `expected_unattempted` across all history (re-creating the exact over-seed purged 2026-07-03). The
   enumerator's date loop must honour the per-dt `start_date` (seed eu only from `start_date`; earlier days = typed
   `EXPECTED_*` absence or out-of-universe) BEFORE the capability flip.
4. **Sequencing**: (a) enumerator start_date gating → (b) UAC capability flip (book5+liq @ wire-date) → (c) register +
   launch the connector → (d) re-measure. Doing (b)/(c) before (a) corrupts the denominator again.

_Not-ASTER-only rider (from the C1 CORRECTED verdict): LIGHTER/EXTENDED/PACIFICA likely share the live-WS/no-REST
profile — apply the same mode-split model when those venues' Layer-1 gaps are worked
(`cefi_layer1_denominator_gaps_2026_07_03.md`)._

### C2 — Two+ expected-universe producers read DIFFERENT source-of-truth functions (the structural root of C1; A17) — CHECKED vs live code; CONFIRMED now-divergence

**Contradiction (A17 / D6):** A17 asserts exactly **ONE** producer `expected_universe.build_expected(asset_group)`;
re-mirrored per-AG enumerators are banned. C1 surfaced ASTER book5 as an "enumerator over-seed." C2 asks the structural
question underneath C1: **how many code paths construct "which (venue × data_type) cells should exist," and do they
agree?**

**Ground-truth check — live code (slot-1 @ current LDR; behind-1 is a doc commit, code is current):**

1. **`build_expected` does NOT exist.** `rg "build_expected"` finds only `_build_expected_entities` (preflight,
   unrelated), `_build_expected_universe` (a one-off tradfi script), `_build_expected_tuples` (a _checker_). A17's
   single canonical producer is **genuinely unbuilt** → IN-FLIGHT confirmed.
2. **There are ≥3 independent constructions of the expected/valid cell-set, reading DIFFERENT UAC functions:**

| Path                                                                                | Role                                                             | Source function it reads                                                                                      | venue-aware?                    | ASTER book5 verdict             |
| ----------------------------------------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------- | ------------------------------- |
| `_enumerate_v2_cefi` → `_row_data_types` (`enumerate_expected_universe.py:992,829`) | **PRODUCER of `expected_unattempted` — the Layer-2 denominator** | `valid_data_types_for_venue_instrument_type` → (cefi branch, UAC:1019) `valid_data_types_for_instrument_type` | ❌ **itype-grain, venue-BLIND** | **SEEDED** (captured=0 forever) |
| backfill launchers / MTDS orchestrator / live-VM data_type selection                | **CAPTURE gate (what is actually fetched)**                      | `get_mvp_data_types_for_cefi_venue` (mvp_scope.py:887)                                                        | ✅ venue-aware                  | **NOT fetched**                 |
| `_build_expected_tuples` (`check_enumeration_completeness.py`)                      | **CHECKER (validates the enumeration)**                          | `get_mvp_data_types_for_cefi_venue` + `VENUE_DATA_TYPE_CAPABILITIES` skip-filter                              | ✅ venue-aware                  | **excluded**                    |
| `seed_for_venue_and_data_type` (market_data_categories.py:1746)                     | MVP seed (spot trades/book5 fan-out)                             | `VENUE_DATA_TYPE_CAPABILITIES`                                                                                | ✅ venue-aware                  | **empty `()`**                  |

**Mechanism (confirmed line-by-line):** `valid_data_types_for_venue_instrument_type` at UAC:1019 short-circuits for
non-defi → `valid_data_types_for_instrument_type(ag, itype)` (pure instrument_type grain). The cefi `perpetual`
itype-grain set INCLUDES `book_snapshot_5` + `liquidations` (market_data_categories.py:550/618). `_enumerate_v2_cefi`
gates the **instrument** (venue+base) at :975 but applies **no per-data_type MVP filter** — `_row_data_types` (:992) is
the only data_type filter, and it never calls `get_mvp_data_types_for_cefi_venue` or `VENUE_DATA_TYPE_CAPABILITIES`. So
every MVP ASTER perp emits book5+liquidations as `expected_unattempted` straight to the manifest (:1009-1034).

**CONFIRMED verdict — this is a NOW-divergence, not latent:**

- **The denominator producer is the ONLY venue-BLIND path; every sibling path (capture gate, checker, seed-fn) is
  venue-aware.** → **EXPECTED ⊋ CAPTURABLE by construction**: the enumerator expects cells the capture side is never
  asked to fetch and the checker doesn't recognise → permanent `captured=0` cells depressing Layer-2 coverage.
- **Not ASTER-only — it's systematic.** `get_mvp_data_types_for_cefi_venue("COINBASE-SPOT")` excludes `book_snapshot_5`
  (the Coinbase **trades-only** MVP carve-out, asserted in its own docstring), but the venue-blind enumerator would
  expect book5 for Coinbase too. **Any per-venue MVP carve-out is silently over-expected by the denominator.**
- **LIVE CONFIRMATION (coverage.json 2026-06-30):** the cefi Layer-1 audit reports **118 `stray_tuples`** (ENUMERATED ∉
  EXPECTED) — the over-seed, measured. Top entries: `(ASTER,PERPETUAL,book_snapshot_5)`,
  `(ASTER,PERPETUAL,liquidations)`, `(ASTER,PERPETUAL,options_chain/futures_chain/ohlcv_1m)`,
  `(BINANCE-SPOT,SPOT_PAIR,options_chain/liquidations/futures_chain/derivative_ticker)`. The venue-blind enumerator is
  expanding every cefi instrument to the full `instrument_type` cross-product, exactly as predicted. _(Some are also
  uppercase-vs-lowercase `instrument_type` artifacts — A15 grain — so the 118 is C2 over-seed ∪ A15 casing; both are the
  same `build_expected`/denominator family.)_
- **Interaction with C1:** the three venue-aware paths are driven by `VENUE_DATA_TYPE_CAPABILITIES` /
  `get_mvp_data_types_for_cefi_venue`, so the **C1 capability-table fix would auto-propagate to the seed-fn + checker
  but NOT to the enumerator** (venue-blind). So C2 (producer reads the wrong source) must be fixed **independently** of
  C1 (table content): even after C1 makes the tables say "ASTER has book5 live-forward," the enumerator would still
  expect book5 for ALL history (no live-wired-date floor) and still over-expect Coinbase book5.
- **A17 surface is bigger than one function:** two dispatch tables coexist in the same file — v1 `_ENUMERATORS`
  (`main()`@2983) and v2 `_V2_ENUMERATORS` (`enumerate_v2()`@1995), 5 per-AG functions each. The file's own docstring
  (:43) calls v2 "the live path"; v1 is reachable but presumed legacy.

**Decision (Ikenna) — this is a SEQUENCING choice (the bug is unambiguous; it's not a "which is stale" pick):**

- **(a) Point-fix now** — in `_row_data_types` (cefi branch) intersect the data_types with
  `get_mvp_data_types_for_cefi_venue(venue)` so the denominator matches the capture gate. ~5 lines; removes the ASTER +
  Coinbase over-seed immediately; honest cefi Layer-2 coverage today. Band-aid on a path A17 will delete.
- **(b) Fold into A17 `build_expected`** — leave `_row_data_types` as-is; build the single venue-aware producer, delete
  the venue-blind path + the v1 dispatch + redundant builders together. Correct end-state, but A17 is blocked on
  registry Phases 1-2, so the over-seed persists until then.
- **(c) Both (Harsh+Claude lean)** — point-fix `_row_data_types` now (stop the denominator lying today) AND keep A17 as
  the structural consolidation. Plus a sub-item: confirm v1 `_ENUMERATORS`/`main()` path is legacy → delete it.
- **Note:** the per-data_type fix direction (use `get_mvp_data_types_for_cefi_venue`) is the same code under any C1
  outcome; only the table CONTENT (does ASTER book5 belong) changes with C1.

**SELECTED DIRECTION — (c) Both** _(Harsh, 2026-06-30; pending Ikenna confirmation)_: point-fix `_row_data_types` (cefi
branch) now to intersect with `get_mvp_data_types_for_cefi_venue(venue)` so the denominator stops over-seeding today,
AND keep A17 `build_expected` as the structural consolidation that later deletes the venue-blind path, the v1
`_ENUMERATORS` dispatch, and the redundant builders. Sub-item: confirm v1 `_ENUMERATORS`/`main()` path is legacy →
delete. Code direction is C1-independent; only the table CONTENT (does ASTER book5 belong) tracks C1.

**STATUS:** ✅ **CONFIRMED — IKENNA AGREED 2026-07-03 (direction (c) as pre-selected).** Point-fix `_row_data_types`
(cefi branch) to intersect `get_mvp_data_types_for_cefi_venue(venue)` now + keep A17 `build_expected` as the structural
consolidation + confirm-then-delete the legacy v1 `_ENUMERATORS` dispatch. C1 is resolved (live-forward split), so the
table CONTENT question is settled too. Execution todos: point-fix + v1-deletion filed in
`cefi_layer1_denominator_gaps_2026_07_03.md` § "C2 point-fix"; the A17 fold stays owned by
`honest_coverage_v2_instrument_denominator_2026_06_28.md` (its open P1). Note: the 2026-07-03 capability carve-out
(`instruments-service@3bb7acd`) already covers the VENUE_DATA_TYPE_CAPABILITIES half of the over-seed; this point-fix
adds the MVP-gate half (e.g. COINBASE-SPOT trades-only cut).

### C3 — `mvp_backfill_cefi_tick_v10` L96 "scope authority = `mvp_scope.py` **v10**" vs live **v12** (A8) — RESOLVED (stale label, not a real fork)

Not a true contradiction like C1/C2 (no two live sources disagree on a fact) — just a **stale version label**: the
plan's authority banner cited `mvp_scope.py` **v10**; live is **v12** (mvp_scope.py:761). Near-zero cefi-execution
impact — the only v10→v12 cefi delta (v11's Coinbase-trades-only cut) is already encoded in the plan's own L39 banner,
and v12's changes are DeFi-only. Pass-2 already refuted the scary "v10 gate misfires" version → MINOR hygiene.

**RESOLVED 2026-06-30 (operator: fix in place):** bumped the cefi_tick L96 authority pointer to `mvp_scope.py` v12
(`MVP_SCOPE_CONFIG_VERSION`) and clarified the OPTION cut as "canonical since v10, in force at v12" so L96 no longer
competes with the L39 v11 banner. Applied to `plans/archive/2026_07/mvp_backfill_cefi_tick_v10_2026_06_27.md` (local
commit, unpushed per hold). **Deferred (out of cefi scope):** the same stale-`v10` authority pin recurs in the other 4
v10 plans (defi_onchain / tradfi_ohlcv1m / catalogue_finalization / reconciliation_closeout) — fix when each is next
touched.

### C4 — `mvp_backfill_cefi_tick_v10` L534 "Layer-1 does NOT block the G4 gate" vs the two-layer model (A12 / D2a) — CHECKED vs codex + the G4 gate def; CONFIRMED real contradiction (terminal-gate certification), coupled to C2

**Contradiction (A12 / D2a):** the plan's G4 (its TERMINAL gate, titled **"verify honest-complete"**, L211-219) is
defined as **`attempted_failed==0 AND expected_unattempted==0`** over the enumerated denominator — **no Layer-1
precondition**. L534 makes the carve-out explicit: **"Layer-1 completeness (v2): 14.88% … denominator_complete: False …
Note: Layer-1 is a denominator audit; does NOT block G4 gate directly."**

**Ground-truth check — what A12 actually requires (codex honest-coverage-model.md):**

- L66/L109-113: "Layer 1 … **gates Layer-2 trust**. … trustworthy **only when Layer-1 = 100%**. The system NEVER reports
  'downloads look good' while the instrument denominator has holes."
- L239/L254: "not-yet-trustworthy, **never certify it** … CK3 cannot certify any AG whose denominator is incomplete."
- L242/L246: `missing_tuples = EXPECTED − ENUMERATED`; `denominator_complete = (missing_tuples == ∅)`.

**CONFIRMED — this is a real contradiction, and it is the SAME axis as C2:**

- **Mechanically L534 is TRUE** — Layer-1 holes (missing tuples) aren't in the manifest, so they don't surface as `af`
  or `eu`; they can't mechanically flip the G4 counters. So af==0 ∧ eu==0 (G4 MET) is **reachable while
  denominator_complete==False.**
- **Normatively L534 is UNSAFE** — G4 is named "verify honest-complete" and is the plan's terminal gate, so closing it
  certifies cefi-MVP "honest-complete." Per A12 that certification is forbidden at Layer-1 < 100%. → **G4 can declare
  cefi done while Layer-1 < 100%, over an incomplete denominator.** Exactly the false-positive the two-layer gate exists
  to stop. _(NB: the plan's "14.88%" (L532) is STALE — a buggy-tool reading; LIVE cefi Layer-1 = **65.91%** (29/44
  tuples), `denominator_complete: false`, coverage.json 2026-06-30, matches A19. Still < 100%, so the contradiction
  holds.)_
- **Layer-1 < 100% IS C2 measured as a number.** Layer-1 = `EXPECTED − ENUMERATED` = the producer-divergence axis. The
  live run reports **118 cefi `stray_tuples`** (ENUMERATED − EXPECTED) led by `(ASTER,PERPETUAL,book_snapshot_5)` +
  `(ASTER,PERPETUAL,liquidations)` — the exact C1/C2 over-seed, confirmed live. So Layer-1 climbs to 100% **only when
  C2/A17 lands** (one venue-aware producer). C4 and C2 resolve together; G4 cannot legitimately close until the
  denominator is fixed.

**Two readings (both sides diagnosed) — they converge on the same safety rule:**

1. **L534 contradicts A12 (codex-strict read):** "verify honest-complete" is a certification → it MUST incorporate
   Layer-1=100%. Fix = add `denominator_complete==True` as a G4 precondition (G4 closes only at Layer-1=100% ∧ af==0 ∧
   eu==0); delete L534.
2. **L534 is a scoping statement (charitable read):** Layer-1 / denominator completeness is owned by the
   `honest_coverage_v2` plan (A11/A17 build_expected), not this CAPTURE plan; "Layer-1 does NOT block G4" = "G4 is the
   Layer-2 capture half; Layer-1 gates separately." Then the fix is NAMING + a cross-plan gate: rename G4 to "verify
   Layer-2 capture-complete," and make the OVERALL cefi-MVP certification require BOTH.

Either way: **cefi-MVP must not be declared honest-complete while Layer-1 < 100%.** The disagreement is only WHERE that
gate lives (inside G4, or as a cross-plan certification gate in the foundation plan). L534 as literally worded is unsafe
because G4 reads as the terminal "done" gate.

**Decision (Ikenna):**

- **(a) Gate G4 on Layer-1=100% (codex-strict)** — add `denominator_complete==True` to the G4 gate; delete L534. Couples
  this plan's closure to C2/A17 landing (correct, but G4 can't close until the denominator work does).
- **(b) Rescope + rename** — G4 → "Layer-2 capture-complete"; reword L534 to "Layer-1 gated separately
  (`honest_coverage_v2`); cefi-MVP final certification requires BOTH"; add the named cross-plan gate so nobody reads
  G4-closed as cefi-done.
- **(c) Hybrid (Harsh+Claude lean)** — do (b)'s rename (G4 = Layer-2 capture, scope-honest) AND record the explicit
  overall-cefi-MVP certification gate `= G4(Layer-2) ∧ Layer-1==100%` in `instruments_foundation_completeness` (the MVP-
  completeness owner). Keeps plan scopes clean, guarantees no false "cefi done," and ties the Layer-1=100% requirement
  to the C2/A17 fix. Sub-item: confirm the foundation plan owns that cross-gate.

**SELECTED DIRECTION — (c) Hybrid** _(Harsh, 2026-06-30; pending Ikenna confirmation)_: rename cefi_tick G4 from "verify
honest-complete" → "verify Layer-2 capture-complete" + reword L534 to "Layer-1 gated separately (`honest_coverage_v2`)";
AND record the explicit overall gate `cefi-MVP done = G4(Layer-2 capture) ∧ Layer-1==100%` in
`instruments_foundation_completeness` (the MVP-completeness owner). Sub-item: confirm the foundation plan owns that
cross-gate. Couples to C2/A17 (Layer-1→100% needs the single venue-aware producer).

**STATUS:** ✅ **DECIDED — IKENNA 2026-07-03: option (a), STRICTER than the pre-selected (c).** "Make G4 enforce both
Layer-1 AND Layer-2 gates" — G4 itself gates on `denominator_complete == True` in addition to the Layer-2 criteria (no
rename/cross-plan split). EXECUTED same day: the G4 gate text in `mvp_backfill_cefi_tick_v10_2026_06_27.md` now requires
BOTH layers and supersedes the 06-29 "Layer-1 does NOT block G4" log note. Consequence: G4 cannot close until cefi
Layer-1 = 100% (currently 79.55% — the C2 point-fix + `cefi_layer1_denominator_gaps` work are on its critical path).

### C5 — `mvp_backfill_cefi_tick_v10` L47 "🟢 G1 COMPLETE … Deribit options_chain captured" vs A18 — CHECKED vs LIVE coverage.json (2026-06-30); verdict CONFIRMED FALSE (data-correctness)

**Contradiction (A18):** the plan's L47-49 banner asserts **"🟢 G1 COMPLETE … options_chain BTC+ETH shards already
captured in prd manifest. Gate: VMs gone = post-completion ✅."** A18 says Deribit options "G1 complete" is FALSE
(options_chain effectively uncaptured, captured≈1). Pass-2 left this **INDETERMINATE** — the plan's only options_chain
number (G0 L243: captured=1) was PRE-backfill, and the plan never re-measured after the G1 VMs "self-completed."

**Ground-truth check — live `gs://central-element-323112-honest-coverage/2026-06-30/coverage.json` (schema v2, generated
00:35Z):**

| grain (DERIBIT options_chain)             | captured |  af |          eu |    cov |
| ----------------------------------------- | -------: | --: | ----------: | -----: |
| `OPTION` (instrument grain)               |    **0** |   0 | **437,692** |   0.0% |
| `options_chain` (degenerate bundle grain) |    **1** |   0 |           0 | 100.0% |

- **Layer-1 counts DERIBIT as PRESENT** (not in the 15 cefi `missing_tuples`) — purely off that single bundle shard.
- **Codex SSOT settles it** (honest-coverage-model.md:280-281): _"options_chain with captured≈1, 99.9% blank
  instrument_type … **is a Layer-1 hole** (the bundle grain was not enumerated / instrument_type blank), NOT a
  legitimate carve-out. Layer-1 must surface it as a `missing_tuple`."_ So the live "PRESENT" classification is itself
  the bug.
- The G1 completion gate was **"VMs gone = post-completion ✅"** — it verified VM lifecycle, NOT captured rows. The
  captured count never moved from 1 (G0 → today). Textbook **silent-zero / fire-and-forget false-completion** (the exact
  anti-pattern: events hide silent-zeros; verify the parquet, not the VM).
- **SOURCE-OF-TRUTH cross-check (manifest, not just coverage.json):** queried both cefi availability indices directly
  (`_index/availability_index.parquet`) — **both independently report Deribit options_chain `captured=1`** (one day,
  2026-04-10): prd bucket (`market-data-tick-cefi-prd`, index updated 06-29 07:51, the one coverage.json reads) =
  captured 1 / af 10,114 / ec 11,161; legacy flat bucket (`market-data-tick-cefi`) = captured 1 / eu OPTION 439,328 /
  COMBO 78,940. So `captured=1` is REAL, not a coverage-tool grain artifact; the single shard is filed under
  `instrument_type=options_chain` (bundle grain) while the OPTION-grain cells are 2.88M `empty_confirmed` + 439K
  `expected_unattempted`, captured 0. (`coverage.json` = output of `measure_honest_coverage.py`:579, the SSOT tool;
  reads the freshest manifest index — verified right artifact AND right bucket.)

**CONFIRMED verdict — "G1 COMPLETE" is FALSE.** Deribit BTC/ETH options_chain (2020-2026) is effectively **uncaptured**
(1 shard; the OPTION grain shows 437,692 eu / 0 captured). This is a **data-correctness finding** (heartbeat HARD RULE),
not a stance — under the rule it FREEZES any downstream "Deribit options complete" claim.

**Decision (Ikenna) — this is a fix, not a preference; two parts, do both:**

- **(a) Re-open G1 + real backfill** — relaunch the Deribit options_chain backfill and gate on **verified captured rows
  per wave** (not "VMs gone"); flip the L47 banner from 🟢 COMPLETE to 🔴/🟡 until captured ≫ 1 and eu→0 on the OPTION
  grain.
- **(b) Fix the grain/gate that masked it** — Layer-1 must NOT count `captured≈1 / blank-instrument_type` options_chain
  as PRESENT (per codex:280); this is the bundle-grain enumeration gap (A15-adjacent / same denominator family as
  **C2**).

**Cross-ref:** same live coverage run quantifies **C2** — 118 cefi `stray_tuples` (enumerated∉expected), led by
`(ASTER,PERPETUAL,book_snapshot_5)` + `(ASTER,PERPETUAL,liquidations)` (the exact C1/C2 over-seed) and
`(BINANCE-SPOT,SPOT_PAIR,options_chain/liquidations/futures_chain)`. C5's grain bug and C2's over-seed are the same
denominator-producer family (A17 `build_expected`).

**STATUS:** 🔄 **WITH IKENNA (2026-07-03) — he is investigating this himself; NO doc/plan changes to be made from this
session per operator.** Recommendation (a) re-backfill + (b) grain fix stands as written for his reference.

### C6 — open re-fetch tasks name the retired `VENUE_FETCH_FAILED` label (A16 / D4) — CHECKED vs code + live manifest; verdict MINOR (label retired from EMISSION, but task still valid — relabel wording only)

**Contradiction (A16):** several open tasks scope a re-fetch by `VENUE_FETCH_FAILED` — e.g. `path_to_100pct` L99
(_"re-fetch the ~88k genuine `VENUE_FETCH_FAILED`/`HTTP_429`"_), `data_completion_to_100_all_ag`,
`instruments_mtds_subset` L141/L965. A16 says the opaque `VENUE_FETCH_FAILED` catch-all is RETIRED →
`UNCLASSIFIED:{code}` + `classify_venue_error()`.

**Ground-truth check (code + live data):**

- **Emission IS retired (code).** `sentinels.py:267-269,717-719,834-835`: every failure path now does
  `classify_venue_error(venue, code) → error_code`, else `f"UNCLASSIFIED:{code}"`. **`VENUE_FETCH_FAILED` is never
  emitted by live code** — A16 confirmed at source.
- **But the historical rows are PRESERVED, not migrated (live cefi prd manifest, 5.7M rows):** **`VENUE_FETCH_FAILED` =
  482,518 rows still present**; `UNCLASSIFIED*` = **0** rows. So the re-fetch task selecting
  `error_reason=="VENUE_FETCH_FAILED"` **still resolves to 482,518 real failed shards** — the task WORKS as written; it
  is NOT keyed on a phantom. The plan's "~88k genuine" is the de-noised re-fetchable subset (transients/HTTP_429
  excluded).
- **Side observation (not a contradiction):** 0 `UNCLASSIFIED:{code}` rows in cefi — live cefi failures classify to
  concrete codes instead (`Tardis HTTP 500`=32,653 / `400`=19,792 / `503`=15,893 top the list), so the
  `else UNCLASSIFIED` branch effectively never fires for cefi Tardis errors.

**Verdict — MINOR (like C3, milder):** the label is retired **from emission**, but it's a valid **historical selector**
(482k rows carry it). The task isn't broken; only the wording risks implying `VENUE_FETCH_FAILED` is a live failure
model. No behavioral bug; the re-fetch is genuine open work that should still run.

**Decision (Ikenna):**

- **(a) Relabel the task wording (D4 lean)** — "cells whose LEGACY `error_reason` was `VENUE_FETCH_FAILED` (retired from
  live emission; historical rows preserved)" across `path_to_100pct` / `data_completion` / `instruments_mtds_subset`.
  Fix once, reference from both (same as MTDS-doc MD6).
- **(b) Leave it** — the task selects the right rows as written; pure clarity nit.

**STATUS:** ⏸ AWAITING IKENNA. _(MINOR wording; not cefi-MVP-blocking. The 482k failed cefi shards ARE real open
re-fetch work, but that's execution, not a contradiction. These are all-AG completion plans, not the cefi_tick MVP
plan.)_

### C7 — A19 certified Layer-1 % (cefi 65.91) cited as a hard "done" bar? (WRONG-1 / A19) — verdict NON-CONTRADICTION (the number is used correctly)

**Concern (WRONG-1, pass-2 ledger note):** the certified Layer-1 %s are an **UPPER bound** (codex CK3 caveat: they move
as the denominator firms up). Risk = a plan citing 65.91% as a fixed "done" target.

**Ground-truth check:** the plans that cite 65.91% — `honest_coverage_v2_opus_checkpoints` (L101/L135),
`honest_coverage_v2_instrument_denominator` (L271) — quote it **as a measurement with provenance**
(`65.91% (29/44, missing=15, stray=118)`), explicitly Layer-1 and explicitly < 100%, NOT as a completion target. Pass-3
(L415) already verified: **no open item treats 65.91% as a hard done-bar.** Live coverage.json confirms 65.91% is the
current Layer-1 reading (29/44), `denominator_complete: false`.

**Verdict — NOT a contradiction.** The number is used correctly (a current measurement that signals "NOT done," which is
right). The only residual is ledger hygiene: A19 should carry the CK3 "upper bound — will move as `build_expected`/C2
firms the denominator" caveat wherever the certified %s are quoted, so nobody later mistakes it for a target. No plan
edit needed.

**STATUS:** ⏸ AWAITING IKENNA (informational). _(Lowest-severity item; clean. Tie-in: the same 65.91% is C4's Layer-1
number and moves with C2/A17.)_

### C8 — `mvp_scope.py:413` "ASTER … book_snapshot_5" comment flagged stale — INVERTED by C1; verdict RESOLVED (comment is CORRECT)

**Originally flagged (A28-adjacent):** the inline comment at mvp_scope.py:~413 describing the CLOB-perp surface as
"trades + book_snapshot_5 + derivative_ticker" was suspected stale (since UAC `VENUE_DATA_TYPE_CAPABILITIES[ASTER]`
omits book5).

**Ground-truth (re-read + C1's official-API check):** the comment (`mvp_scope.py`:412-415) reads _"All three
[LIGHTER/EXTENDED/PACIFICA] are CLOB-based perp DEXs (confirmed: **same CLOB capture surface as HL/ASTER — trades +
book_snapshot_5 + derivative_ticker**). PACIFICA is forward-poll-only for tick (no historical book/trades backfill)."_
C1's official AsterDex-API check found ASTER book5 IS the live CLOB surface (WS @depth5), not historically backfillable
— **exactly what this comment says.** So the comment is **RIGHT**; the WRONG table is UAC `VENUE_DATA_TYPE_CAPABILITIES`
(C1). This **INVERTS** the "stale comment" finding.

**Verdict — RESOLVED: do NOT "fix" the comment; it is correct.** The fix belongs in UAC `VENUE_DATA_TYPE_CAPABILITIES`
(C1 decision) + the enumerator (C2), not here. (Folded into C1; logged separately so the original C8 flag isn't actioned
backwards.)

**STATUS:** ✅ RESOLVED (no action; inverted by C1). _(If anything, the comment is the SSOT the capability table should
match.)_

### C9 — EXTENDED candle/ohlcv fetch path silently swallows failures (honest-absence violation) — CHECKED vs code; CONFIRMED real (data-correctness, low MVP urgency)

**Finding:** `_fetch_extended_candles_for_symbol` (`adapters/_umi_extended.py:151`) — the EXTENDED
`/info/candles/{symbol}/trades` (PT1M candle/ohlcv) path — **does not record failures**, unlike every sibling EXTENDED
endpoint:

| EXTENDED path   | takes `failed_per_instrument`? | on HTTP error                      | on exception                       | on empty-200                            |
| --------------- | ------------------------------ | ---------------------------------- | ---------------------------------- | --------------------------------------- |
| `/candles` (C9) | **❌ no param**                | `logger.debug` (L180), no record   | `logger.warning`, no record (L182) | emits nothing (L173), no `record_empty` |
| `/funding`      | ✅ (L194)                      | warning + `record(...)` (L232-234) | warning + `record(...)`            | —                                       |
| `/trades`       | ✅ (L270)                      | warning + `record(...)` (L286-291) | warning + `record(...)`            | —                                       |
| `/orderbook`    | ✅ (L371)                      | warning + `record(...)` (L381-383) | —                                  | —                                       |

So an EXTENDED candle HTTP error → logged at **DEBUG** (near-invisible) → **no `attempted_failed` row**; an empty 200 →
**no `empty_confirmed` row**. The shard looks un-attempted. Violates the **"never silent placeholders /
honest-absence"** HARD RULE — the manifest can't distinguish "candle fetch failed" from "never tried."

**Verdict — CONFIRMED code bug (data-correctness), LOW cefi-MVP urgency.** The path is candle/**ohlcv_1m** (PT1M), which
is NOT in the cefi-perp MVP cut (trades + book5 + funding + derivative_ticker) — so it doesn't corrupt the MVP
denominator today. But it IS a genuine honest-absence gap and a latent trap if ohlcv is ever enumerated.

**Decision (Ikenna):**

- **(a) Fix to match siblings (lean)** — thread `failed_per_instrument: PerLeafFailureRouter` into
  `_fetch_extended_candles_for_symbol`; `logger.warning` + `record(...)` on HTTP-error/exception; `record_empty(...)` on
  empty-200. ~10 lines; closes the silent-failure.
- **(b) Defer** — it's non-MVP ohlcv; log as a known honest-absence gap and fix when ohlcv enters scope.

**STATUS:** ⏸ AWAITING IKENNA. _(Code bug, not a plan contradiction — really an issue found mid-reconciliation. Low MVP
urgency (ohlcv non-MVP) but a real honest-absence violation; recommend the ~10-line fix (a).)_

## Progress Log

- **2026-06-29** — Doc created. Truth model locked (alignment-based: no plan is SSOT; SSOT = UAC + fresh codex; no date
  exemption). Codex freshness checked via git dates (`instruments-service-as-ssot-for-mtds.md` flagged STALE). Live UAC
  ground truth verified: defi 55 live / 67 pipeline, `MVP_SCOPE_CONFIG_VERSION==12`, ROCKETPOOL re-phased pipeline (not
  deleted), cefi carries KALSHI-PERP/POLYMARKET-PERP, sports 8 odds venues, prediction {POLYMARKET,KALSHI}. **Section A
  assertion ledger (A1–A20) written.**
- **2026-06-29** — Section B triage of all 67 (contested-token signal). 30 plans deep-read across 12 read-only
  cluster-agents; 17 zero-hit plans set aside (logged).
- **2026-06-29** — **Wave-1 Sections C + D written** (12 cluster-agents, 31 plans). Findings collapse into 9 clusters
  (D1–D9); dominant = D1 v10→v12 MVP drift.
- **2026-06-29** — **Coverage correction + Wave 2.** Wave-1 left 14 contested-signal subjects uncovered (sports-06-27
  family + 4 misc, initially mis-bucketed as date-trusted). Wave 2 (C13–C15) deep-read all 14: 0 MAJOR · 0 MEDIUM · 5
  MINOR · 9 ALIGNED — sports A4 two-registry intact everywhere; findings feed existing clusters D2b/D6/D8, no new
  cluster. **FIND pass complete + full coverage: 45 deep-read + 17 set-aside = 62/62 subjects accounted.**
- **Final tally (45 deep-read):** 3 MAJOR-CONFLICT (all v10 MVP plans) · 9 MEDIUM · 14 MINOR-DRIFT · 19 ALIGNED. **3
  operator decisions pending** (D1 v10-plan disposition · D2a cefi_tick G4 gate · D3 Deribit options stance) before the
  alignment (edit) pass. No subject plans were edited in this pass (read-only, as designed).
- **2026-06-30** — **Section G review log opened (cefi-MVP contradictions, one-by-one for Ikenna).** C1 (ASTER
  book5/liquidations) checked vs official AsterDex API → verdict CORRECTED (live-capturable, not historically
  backfillable; UAC capability table wrong; INVERTS C8). C2 (two+ expected-universe producers) checked vs live code →
  CONFIRMED now-divergence: the denominator producer `_enumerate_v2_cefi` is venue-BLIND (reads
  `valid_data_types_for_instrument_type`) while the capture gate + checker + seed-fn are venue-aware (read
  `get_mvp_data_types_for_cefi_venue` / `VENUE_DATA_TYPE_CAPABILITIES`) → EXPECTED ⊋ CAPTURABLE (ASTER + Coinbase book5
  over-seeded); `build_expected` (A17) genuinely unbuilt. Both ⏸ AWAITING IKENNA. Kept LOCAL/unpushed per operator.
- **2026-06-30** — **C3-C5 walked + live coverage.json ground-truth.** C3 (v10-banner): stale label not a real fork →
  RESOLVED, bumped cefi_tick L96 authority pointer v10→v12 in place. C4 (Layer-1 ⊬ G4): CONFIRMED false-"done" risk (G4
  "verify honest-complete" has no Layer-1=100% precondition); dir (c) — rename G4 to Layer-2-capture + cross-gate in
  foundation plan. C5 (Deribit "G1 COMPLETE"): pulled LIVE `coverage.json` 2026-06-30 → CONFIRMED FALSE — Deribit
  OPTION/options_chain captured=0 eu=437,692 (only a degenerate captured=1 bundle shard; codex:280 calls captured≈1 a
  Layer-1 hole); "VMs gone = complete" masked a silent-zero → data-correctness re-backfill needed. Live run also
  corrects C4 (Layer-1 14.88%→65.91%) and quantifies C2 (118 stray tuples incl. exact ASTER book5/liquidations). C4/C5 ⏸
  AWAITING IKENNA. Kept LOCAL/unpushed per operator.
- **2026-06-30** — **C6-C9 walked (remaining cefi-MVP contradictions); cefi index C1-C9 COMPLETE.** C6 (retired
  `VENUE_FETCH_FAILED`): code-confirmed retired from emission (sentinels.py) but 482,518 historical rows preserved in
  live cefi manifest (0 `UNCLASSIFIED` rows) → task valid, MINOR relabel-only. C7 (A19 65.91% as done-bar):
  NON-CONTRADICTION — plans cite it as a measurement w/ (29/44) provenance, pass-3 confirmed no done-bar misuse; add CK3
  upper-bound caveat. C8 (`mvp_scope.py:413` ASTER comment): RESOLVED — INVERTED by C1, the comment is CORRECT (do not
  "fix"). C9 (EXTENDED candle path): CONFIRMED code bug — `_fetch_extended_candles_for_symbol` has no failure router,
  swallows HTTP-error (debug) / exception / empty-200 silently (honest-absence violation), unlike sibling
  /funding,/trades,/orderbook; LOW MVP urgency (ohlcv non-MVP), recommend ~10-line fix. C6/C7/C9 ⏸ AWAITING IKENNA; C8
  ✅ RESOLVED. Kept LOCAL/unpushed.
- **2026-07-03 — C1 RESOLVED (Ikenna, relayed by Harsh in-meeting): ASTER = live-forward mode split.** Batch+live =
  trades/derivative_ticker/perp_funding; live-only-forward = book_snapshot_5 + liquidations (prediction-AG pattern;
  pre-wire history stays typed honest absence — the 2026-07-03 purge stands). Capability check ("do we already have
  this?") — MOSTLY YES: connectors built (`aster_book_liq_ws.py`), pipeline_mode spine live (`live_kalshi_perp`
  precedent runs in cefi today), `EXPECTED_COVERAGE._CEFI["ASTER"]` already declares both types. FOUR gaps, tracked as
  ordered todos in `cefi_layer1_denominator_gaps_2026_07_03.md` § "ASTER live-forward mode split": (1) enumerator must
  honour per-(venue,dt) `start_date` FIRST (else the capability flip re-seeds all history), (2) UAC capability flip
  book5+liq @ wire-date (also resolves the EXPECTED_COVERAGE ↔ VENUE_DATA_TYPE_CAPABILITIES self-contradiction found
  during the check), (3) connector never registered in `connector_registry.py` — 0 `live_aster` rows ever — register +
  launch, (4) re-measure. Ledger: C1 ✅ · C3 ✅ · C8 ✅ · C2/C4 direction-selected awaiting confirm · C5/C6/C7/C9 ⏸.
- **2026-07-03 (later, same meeting) — C2/C4/C5 answered by Ikenna.** C2 ✅ CONFIRMED direction (c) as pre-selected
  (point-fix + A17 fold + v1-dispatch deletion; execution todos in `cefi_layer1_denominator_gaps_2026_07_03.md`). C4 ✅
  DECIDED **option (a)** — stricter than the pre-selected (c): G4 enforces BOTH layers; the `mvp_backfill_cefi_tick_v10`
  G4 gate text was amended same-day (Layer-1 `denominator_complete==True` is now a required conjunct; supersedes the
  06-29 "does NOT block G4" note). C5 🔄 WITH IKENNA — he is investigating the Deribit options false-complete himself;
  no changes from this side. C3 re-acknowledged (stale v10→v12 pointer, was already fixed in place). **Ledger now: C1 ✅
  · C2 ✅ · C3 ✅ · C4 ✅ · C8 ✅ · C5 🔄 with-Ikenna · C6/C7/C9 ⏸ (minor: wording relabel / informational / ~10-line
  honest-absence fix).**
