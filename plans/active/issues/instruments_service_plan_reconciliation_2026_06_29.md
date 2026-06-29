---
doc_type: issue
title: "Instruments-Service Plan Reconciliation — open plans vs SSOT (UAC + 3 new plans + fresh codex)"
summary:
  "Find-first reconciliation: score every open plan that touches instruments-service against the anointed truth set
  (live UAC code + the 3 new plans + freshness-gated codex + plans newer than the 2026-06-26 cutoff) to surface
  task-item CONTRADICTIONS, so they can be aligned in a later pass. This pass is read-only: it finds and classifies,
  it does NOT edit the subject plans. Section A = the SSOT assertion ledger (the yardstick). Section B = triage of all
  67 plans. Section C = deep-read findings. Section D = synthesis + proposed resolutions."
status: active
nature: audit
asset_group: cross-asset
stage: [meta]
repos: [instruments-service, unified-api-contracts]
scope: [admin]
tags: [reconciliation, ssot-audit, plan-hygiene, instruments-service, honest-coverage, venue-registry]
related:
  [
    ../instrument_universe_registry_consolidation_2026_06_29.md,
    ../honest_coverage_v2_instrument_denominator_2026_06_28.md,
    ../honest_coverage_v2_opus_checkpoints_2026_06_28.md,
    ../../../codex/02-data/honest-coverage-model.md,
    ../../../codex/04-architecture/instrument-universe-registry-consolidation.md,
  ]
created: 2026-06-29
last_updated: 2026-06-29
assigned_vm: NA
execution_scope: local-only
priority: P1
source: [operator request 2026-06-29]
drift_direction: advance-code
depends_on: []
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Instruments-Service Plan Reconciliation (2026-06-29)

> **Read-only FIND pass.** Goal: surface every open-plan task item that CONTRADICTS the truth set, classify it, and
> propose a resolution — **without editing the subject plans**. Operator decides per-contradiction (or per-cluster)
> what to act on afterward.

## Truth-set / trust model (operator-locked 2026-06-29, FINAL)

**No plan is SSOT.** The only SSOT = **live UAC code + fresh codex**. A plan is trusted *only where it aligns with both
UAC and codex*; anywhere it doesn't, that misalignment is a contradiction to report. There is **no date-based trust
exemption** — every plan touching the contested surface is a subject, including the 06-27 v10 plans (they predate the
06-29 MVP-v12 landing and may misalign on defi).

- **SSOT (truth):** live UAC code (ultimate tiebreaker for concrete venue/MVP/config facts) + codex (freshness-gated —
  a doc whose git date predates the 2026-06-29 landings is the *stale side*, recorded as its own finding; see A20).
- **The 3 new plans** are trusted because they match UAC — they are the *aligned reference*, not a privileged tier.
- **`last_updated` is NOT trustworthy** — it was bulk-added to all plans on one day and is also bumped by agents on item
  completion. Ignore it. Use **`created`** only to prioritize reading order; use **git history at the item level** when
  recency actually matters.
- **Subjects = every plan with a contested-surface signal**, scored for alignment with UAC+codex regardless of date.

### Codex freshness check (git last-modified)

| Codex doc                                                    | git date   | verdict                                              |
| ------------------------------------------------------------ | ---------- | --------------------------------------------------- |
| `02-data/honest-coverage-model.md`                           | 2026-06-29 | ✅ FRESH — Tier-1-aligned (authoritative v2 model)  |
| `04-architecture/instrument-universe-registry-consolidation` | 2026-06-29 | ✅ FRESH — Tier-1-aligned                            |
| `02-data/honest-absence-downstream-handling.md`              | 2026-06-27 | ✅ fresh enough (≥ cutoff)                           |
| `02-data/availability-manifest-and-data-status.md`           | 2026-06-27 | ✅ fresh enough (≥ cutoff)                           |
| `02-data/data-pipeline-correctness-hard-rule.md`             | 2026-06-25 | 🟡 borderline (process doc; not MVP/venue lists)    |
| `04-architecture/instruments-service-as-ssot-for-mtds.md`    | 2026-06-16 | ❌ **STALE** on venue-registry/MVP — see **A20**     |

---

## Section A — SSOT assertion ledger (the yardstick)

Each assertion = a normative fact a subject plan can contradict. `LANDED` = shipped ground truth; `IN-FLIGHT` = the
target end-state the new plans are still executing (a contradiction here is "will-conflict", flag as alignment-needed).
Citations are file:line or plan/commit.

### Domain 1 — Venue registry & IS-as-mirror

- **A1 `LANDED`** — IS venue producers READ UAC; hardcoded mirrors `_CEFI_VENUES` / `_TRADFI_VENUES` are **DELETED**.
  cefi via named `expand_cefi_tardis_endpoints()` (bare `OKX`→`OKX-SPOT/-SWAP/-FUTURES`, `COINBASE`→`COINBASE-SPOT`);
  tradfi via named `_TRADFI_NON_VENUE_KEYS={YAHOO_FINANCE}` filter; prediction reads `VENUES_BY_ASSET_GROUP[prediction]`.
  _(registry plan Phase 1 / instruments-service@4da6fe8)._
  **Conflicts:** any task that adds/edits/maintains a hardcoded IS venue list, or treats IS as the venue SSOT.
- **A2 `LANDED`** — UAC `VENUES_BY_ASSET_GROUP` is the canonical venue universe per AG (market_data_categories.py:223).
  cefi members include `KALSHI-PERP`/`POLYMARKET-PERP` (asset_group=**cefi**, CFTC perps), plus `DERIBIT-COMBO`,
  `BINANCE-DELIVERY`, Tardis Tier-3 expansion venues. **Conflicts:** plans treating KALSHI-PERP as prediction, or
  omitting the perps/combo/delivery venues from the cefi universe.
- **A3 `LANDED`** — UAC bare `OKX`/`COINBASE` are **KEPT** (execution-context alias); the Tardis split lives **IS-side**
  only. The "push the split INTO UAC / drop bare forms" approach was **REJECTED** (cross-service breaking via UTL `Venue`
  enum). _(registry FINAL Decision A.)_ **Conflicts:** plans proposing to add `OKX-SWAP`/`COINBASE-SPOT` to UAC or drop
  bare `OKX`/`COINBASE`.
- **A4 `LANDED`** — **sports = TWO registries, EXEMPT from set-equality.** IS owns reference-data providers
  (API_FOOTBALL/FOOTYSTATS/UNDERSTAT/TRANSFERMARKT/SOCCER_FOOTBALL_INFO/OPEN_METEO); UAC sports = MTDS **odds** venues
  (ODDS_API/PINNACLE/BETFAIR*/DRAFTKINGS/FANDUEL). Do **NOT** merge. _(registry Decision C.)_ **Conflicts:** plans that
  merge the two sports registries or expect odds venues in the IS producer.
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
  honest_coverage_v2_instrument_denominator** (explicit "do NOT edit that script here" comment, market_data_categories.py
  ~:300). **Conflicts:** plans editing that script / the defi denominator outside honest_coverage_v2 (duplicate-owner).

### Domain 3 — Honest Coverage v2 model (codex honest-coverage-model.md, fresh 06-29)

- **A12 `LANDED`** — Coverage is **TWO-LAYER**: Layer-1 (instrument-denominator completeness) **GATES** Layer-2
  (download coverage). A Layer-2 % is trustworthy only at Layer-1 = 100%. No flat single-number "100% coverage" claim is
  valid without the gate. _(honest-coverage-model.md / CK3.)_ **Conflicts:** plans claiming flat coverage % / "100%" /
  "G1 complete" without the two-layer gate.
- **A13 `LANDED`** — `coverage.json` **schema_version == 2** (additive: `layer_1`, `by_venue_instrument_type[_data_type]`,
  `by_day`, gate fields). **Conflicts:** plans referencing the old single-layer coverage schema as current.
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
  plans citing other coverage numbers as current (stale-number).

### Domain 4 — Stale-source flags

- **A20** — `codex/04-architecture/instruments-service-as-ssot-for-mtds.md` is **git-dated 2026-06-16** → **STALE** on
  venue-registry/MVP (predates registry consolidation + MVP v12; the registry plan's Phase-2 "codex flip" to fix it is
  still OPEN). Any plan leaning on this doc for venue/MVP truth is citing a stale source.

---

## Section B — Triage (contested-token signal across the 67 plans)

Signal = grep hits across 7 token-groups (venue-registry · OKX-split · perp · defi-MVP · enumeration · honest-coverage ·
coverage-numbers). All plans below are **subjects** (no date exemption). 17 zero-hit plans are set aside (don't touch the
SSOT axes at all). Deep-read clustered into 12 read-only agents (C1–C12).

**Deep-read roster (HIGH/MED — by theme):**

| Cluster | Plans                                                                                                 |
| ------- | ----------------------------------------------------------------------------------------------------- |
| C1      | cefi_manifest_canonicalisation · prediction_manifest_canonicalisation                                 |
| C2      | tradfi_manifest_canonicalisation · defi_manifest_canonicalisation                                     |
| C3      | sports_manifest_canonicalisation · downstream_services_manifest_canonicalisation                      |
| C4      | master_data_canonicalisation_migration_catalogue                                                      |
| C5      | mvp_backfill_defi_onchain_v10 · mvp_catalogue_finalization_v10 · mvp_reconciliation_closeout_v10       |
| C6      | mvp_backfill_cefi_tick_v10 · mvp_backfill_tradfi_ohlcv1m_v10 · mvp_scope_catalogue_tagging             |
| C7      | prediction_venue_perps_and_live_clob_depth · cryptovenue_equity_perps_and_tokenized_stocks            |
| C8      | data_completion_to_100_all_ag · path_to_100pct_backfill_mtds_is · data_pipeline_hardening_self_monitor |
| C9      | instruments_foundation_completeness · instruments_mtds_subset_consistency · migration_verif_orphan     |
| C10     | solana_defi_legacy_migration · master_to_live_defi · v2_engine_venue_buildout                         |
| C11     | cefi_deribit_binance_futures_bundle_verification · tradfi_multisource_backfill · tradfi_massive_dual   |
| C12     | sports_odds_bookmaker_coverage_enum · data_status_tab_downloads · capability_wizard · pipeline_mode_src |

**Set aside — 17 zero-hit (no contested-surface signal; logged, not deep-read):** bar_edge_left_vs_right_remediation,
cicd_sit_full_coverage_handoff, data_source_provenance_all_asset_groups, codex_vs_repo_docs_ssot_audit,
predictions_other_bucket_and_ui_drilldown, defi_onchain_derivable_values_and_date_drift, stash_pile_workspace_cleanup,
cicd_consolidated_remaining, pipeline_mode_partition_migration, doc_frontmatter_schema_and_validator,
sports_reference_backfill_oom, orchestrator_strict_vm_matching_and_plan_frontmatter_governance,
scripts_lifecycle_marker_rollout, mtds_file_size_refactor, test_fleet_image_builds_from_current_code,
tradfi_cme_event_contract_backfill, utl_uac_reuse_consolidation_remediation.

**Coverage correction (2026-06-29):** the first deep-read wave (C1–C12) covered **31** subject plans, not all
contested-signal subjects. **14 contested-signal plans were uncovered** (initially mis-bucketed as date-trusted before
the no-date-exemption model was locked). Now covered by a **follow-up wave C13–C15**: _sports (10)_
— sports_p2_history_reference_and_odds (32 sig), sports_p2_history_apifootball (24), sports_p1_golden_window_apifootball
(14), sports_pipeline_to_100pct_golden_window_first (7), sports_p2_daily_forward_catalogue_and_final_gate (4),
sports_canonical_universe_and_apifootball_reference_expansion (3), sports_fixtures_schema_split_completion (2),
sports_p1_golden_window_e2e_gate (2), sports_p2_features_history_to_ml_ready (1),
sports_p0_sourcing_and_honest_coverage_correctness (1); _misc (4)_ — unified_deployment_health_cockpit (5),
codex_violations_ratchet_to_five (4), work_split_2026_05_22_ikenna (3), repo_scripts_governance_audit (1).
**Subject coverage after C13–C15 = 45/62 deep-read + 17 set-aside = 62/62 accounted.**

## Section C — Deep-read findings (wave 1: 12 cluster-agents, 31 plans; wave 2 C13–C15: +14 plans)

**Severity normalized by the orchestrator** (agents under-graded verdicts — a plan with a HIGH finding on an OPEN item
is MAJOR regardless of the agent's label). Grade = worst OPEN-item finding. `*` = finding sits on an OPEN `[ ]` item
(live, will mislead execution); historical/`[x]` claims are noted but not graded MAJOR.

### MAJOR-CONFLICT (open-item HIGH that would mislead an executing agent)

| Plan                                  | Findings                                                                                                                                                                                                                                                            |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mvp_backfill_defi_onchain_v10`       | **A8/A10\*** L165 OPEN G2 gate `attempted_failed=0 AND expected_unattempted=0` runs against the v10 universe (incl. ROCKETPOOL-ETHEREUM in lst_rates) → under v12 ROCKETPOOL is `pipeline`, so the gate flags its gaps as blocking failures. L75-76/L91 v10 "ONLY scope authority" banner + Definition-of-100% embed the v10 denominator. → re-anchor the gate to the v12 / 55-live denominator (A9). |
| `mvp_backfill_cefi_tick_v10`          | **A12\*** L534 "Layer-1 … does NOT block G4 gate directly" — head-on contradiction of the gate model on the OPEN G4 item. **A8\*** L97 "mvp_scope.py v10 … the ONLY scope authority" (live=v12). **A18** L48/L167 "🟢 G1 COMPLETE … most Deribit options_chain shards already captured" (A18: captured=1).                                  |
| `mvp_reconciliation_closeout_v10`     | **A8\*** L44-46 "fix the PLAN to v10 — never the reverse … the single place that enumerates + closes every such conflict" + L57 "7 v10 decisions every plan must agree with" → declares the system reconciled at v10; the R1 re-scan table (L183-216) pre-dates v12 and is now stale on the defi-denominator axis. |

### MEDIUM (HIGH/notable finding, narrower or single-item)

| Plan                                              | Findings                                                                                                                                                                              |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `instruments_mtds_subset_consistency_remediation` | **A1\*** L1795 OPEN "[MTDS] P2. De-duplicate the IS venue universe … make the fetch path read the UAC registry" — asks to do what the registry consolidation ALREADY shipped (IS@4da6fe8). **A16\*** L141 step-9 backfill targets retired `VENUE_FETCH_FAILED` label. |
| `data_completion_to_100_all_ag`                   | **A16\*** L99 OPEN "re-fetch the ~88k genuine `VENUE_FETCH_FAILED`" (retired → `UNCLASSIFIED:{code}`). **A12\*** flat "captured=100% of could-exist" success criterion, no gate. **A17\*** per-AG enumerator (alignment-needed). |
| `path_to_100pct_backfill_mtds_is`                 | **A16\*** same VENUE_FETCH_FAILED re-fetch (near-duplicate of above). **A12\*** "Definition of 100%" flat. **A18\*** Deribit `options_chain` bundled into a generic tradfi backfill. **A17\*** per-AG enumerator. |
| `mvp_backfill_tradfi_ohlcv1m_v10`                 | **A8\*** L43 v10 "ONLY scope authority" banner. **A12** L126 "G2 GATE MET eu=0 af=0" presented as done, Layer-2-only. **A13** coverage %s maybe from pre-v2 harness.                  |
| `cefi_deribit_binance_futures_bundle_verification`| **A18\*** L102-104 OPEN spot-check items implicitly assume Deribit options fetchable; backfill is gated → may run against empty corpus + misread NaN as failure.                      |
| `data_status_tab_and_downloads_remediation`       | **A18\*** L333/L368 OPEN item + success-criterion operator note (2026-06-16) "BTC/ETH options FINE for now — do NOT widen" contradicts A18's certified "uncaptured."                 |
| `mvp_scope_catalogue_tagging`                     | **A8** illustrative scope block lists tradfi `trades` (v10/12 = ohlcv_1m-only); **A2/A5/A15** same block uppercase types + omits KALSHI-PERP / KALSHI.                                |
| `instruments_foundation_completeness`             | **A12\*** L243 OPEN "Layered coverage" Phase-0 todo doesn't bake in the two-layer gate / v2 schema; A7/A13/A17 low.                                                                   |
| `mvp_catalogue_finalization_v10`                  | **A8** L52 v10 cite in "Codex SSOTs READ before executing"; **A20** L57 leans on stale `instruments-service-as-ssot-for-mtds.md` (low — draws no venue facts from it).               |

### MINOR-DRIFT (low / historical only)

`cefi_manifest_canonicalisation` (A17 low) · `prediction_manifest_canonicalisation` (A17 low + a latent-trap P3 keyed on A17) ·
`defi_manifest_canonicalisation` (A12 low — denominator already uses 55-set, aligned with A9) ·
`downstream_services_manifest_canonicalisation` (2 stale un-flipped duplicate checkboxes, work shipped elsewhere) ·
`master_data_canonicalisation_migration_catalogue` (A12 header + A19 historical, low) · `tradfi_massive_dual_source`
(stale status table + `[x]`-but-not-verified hygiene) · `v2_engine_venue_buildout` (A7 low, strategy-layer surface) ·
`capability_wizard_and_manifest` (A8 low — "53" vs own "57") · `pipeline_mode_source_batch_live_replay` (un-flipped wrapper checkbox).

### ALIGNED (no actionable contradiction)

`tradfi_manifest_canonicalisation` · `sports_manifest_canonicalisation` · `data_pipeline_hardening_self_monitoring` ·
`migration_verification_orphan_safety` (ROCKETPOOL mention is captured-data, correct per A10) · `solana_defi_legacy_migration` ·
`master_to_live_defi` (stale content all historical, nothing live) · `prediction_venue_perps_and_live_clob_depth` (the
SOURCE of the A2/A5 distinction) · `cryptovenue_equity_perps_and_tokenized_stocks` · `sports_odds_bookmaker_coverage_enumeration` ·
`tradfi_multisource_backfill`.

### Wave 2 (C13–C15, +14 previously-uncovered plans) — 0 MAJOR · 0 MEDIUM · 5 MINOR · 9 ALIGNED

The sports cluster is clean: **A4 two-registry split intact in every plan** (IS reference providers vs MTDS odds venues,
never merged). All findings are low and map to existing clusters — no new cluster, no change to the 3 operator decisions.

- **MINOR-DRIFT (low only):** `sports_p1_golden_window_apifootball` (A12 "100% honest coverage" wording, all `[x]`) ·
  `sports_pipeline_to_100pct_golden_window_first` (A17 per-source enumerator + stale coordinator burn-down table) ·
  `sports_p2_daily_forward_catalogue_and_final_gate` (A12 success-criteria wording + A17) ·
  `sports_canonical_universe_and_apifootball_reference_expansion` (A19 dated 65.2% snapshot + A12 open P1 wording) ·
  `sports_p1_golden_window_e2e_gate` (A12 "FULL sports stack 100%" coordinator wording).
- **ALIGNED:** `sports_p2_history_reference_and_odds_2015_to_present` · `sports_p2_history_apifootball_2015_to_present` ·
  `sports_fixtures_schema_split_completion` · `sports_p2_features_history_to_ml_ready` ·
  `sports_p0_sourcing_and_honest_coverage_correctness` · `unified_deployment_health_cockpit` (passthrough coverage tile) ·
  `codex_violations_ratchet_to_five` · `work_split_2026_05_22_ikenna` · `repo_scripts_governance_audit`.

**Full tally (45 deep-read):** 3 MAJOR · 9 MEDIUM · 14 MINOR-DRIFT · 19 ALIGNED. Wave-2 low findings feed clusters
D2b (A12 wording), D6 (A17 per-source enumerators), D8 (stale snapshot/burn-down hygiene).

## Section D — Synthesis: cross-plan clusters + proposed resolutions

Findings collapse into **9 clusters**. ⚖️ = needs an operator decision (not auto-fixable); 🔧 = mechanical/auto-fixable
in the later alignment pass.

### D1 ⚖️ — v10→v12 MVP version drift (DOMINANT cluster)

**Plans:** `mvp_backfill_defi_onchain_v10`, `mvp_backfill_cefi_tick_v10`, `mvp_backfill_tradfi_ohlcv1m_v10`,
`mvp_catalogue_finalization_v10`, `mvp_reconciliation_closeout_v10`. **SSOT:** A8 (v12), A9 (55-live denom), A10
(ROCKETPOOL→pipeline). All 5 created 2026-06-27, two days before MVP-v12 landed. The "mvp_scope.py **v10** = the ONLY
scope authority" banners are *standing instructions to executing agents*, not historical notes. **Live risk:** the OPEN
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
operator stance (2026-06-16) that A18 overturns — **reaffirm "fine for now" or update to track the real gap?** The rest →
🔧 annotate `options_chain` as a known Layer-1 gap, gate the spot-checks behind ">0 captured."

### D4 🔧 — Retired VENUE_FETCH_FAILED in OPEN re-fetch tasks (A16)

**Plans:** `data_completion_to_100_all_ag` L99, `path_to_100pct_backfill_mtds_is` L99, `instruments_mtds_subset` L141.
Open tasks target the retired `VENUE_FETCH_FAILED` label (→ `UNCLASSIFIED:{code}` + `classify_venue_error()`). →
mechanical: rewrite the open tasks to query the new error taxonomy. (Historical `[x]` refs in `cefi_deribit_bundle` need
no action.)

### D5 🔧 — Open work to do an already-shipped consolidation (A1)

`instruments_mtds_subset_consistency_remediation` L1795 OPEN item "make the fetch path read the UAC registry / delete the
`_*_VENUES` mirrors" is already done (IS@4da6fe8). → close as superseded after a no-regression check.

### D6 — Single expected-universe producer / per-AG enumerators (A17, IN-FLIGHT → alignment-needed)

**Plans:** `cefi_manifest`, `prediction_manifest`, `sports_manifest`, `data_completion`, `path_to_100pct`,
`instruments_foundation`, `master_data_canonicalisation_migration_catalogue`. These run/maintain per-AG
`_enumerate_v2_*` / `enumerate_expected_universe.py`. NOT a now-conflict — A17's single `build_expected()` is in-flight
(blocked on registry Phases 1-2 + folded into `honest_coverage_v2`). → annotate each with the fold-in dependency; no edit
until `build_expected` lands. (This is the SAME work the honest_coverage_v2 plan already owns — see A11/A17.)

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

## Progress Log

- **2026-06-29** — Doc created. Truth model locked (alignment-based: no plan is SSOT; SSOT = UAC + fresh codex; no
  date exemption). Codex freshness checked via git dates (`instruments-service-as-ssot-for-mtds.md` flagged STALE). Live
  UAC ground truth verified: defi 55 live / 67 pipeline, `MVP_SCOPE_CONFIG_VERSION==12`, ROCKETPOOL re-phased pipeline
  (not deleted), cefi carries KALSHI-PERP/POLYMARKET-PERP, sports 8 odds venues, prediction {POLYMARKET,KALSHI}.
  **Section A assertion ledger (A1–A20) written.**
- **2026-06-29** — Section B triage of all 67 (contested-token signal). 30 plans deep-read across 12 read-only
  cluster-agents; 17 zero-hit plans set aside (logged).
- **2026-06-29** — **Wave-1 Sections C + D written** (12 cluster-agents, 31 plans). Findings collapse into 9 clusters
  (D1–D9); dominant = D1 v10→v12 MVP drift.
- **2026-06-29** — **Coverage correction + Wave 2.** Wave-1 left 14 contested-signal subjects uncovered (sports-06-27
  family + 4 misc, initially mis-bucketed as date-trusted). Wave 2 (C13–C15) deep-read all 14: 0 MAJOR · 0 MEDIUM ·
  5 MINOR · 9 ALIGNED — sports A4 two-registry intact everywhere; findings feed existing clusters D2b/D6/D8, no new
  cluster. **FIND pass complete + full coverage: 45 deep-read + 17 set-aside = 62/62 subjects accounted.**
- **Final tally (45 deep-read):** 3 MAJOR-CONFLICT (all v10 MVP plans) · 9 MEDIUM · 14 MINOR-DRIFT · 19 ALIGNED.
  **3 operator decisions pending** (D1 v10-plan disposition · D2a cefi_tick G4 gate · D3 Deribit options stance) before
  the alignment (edit) pass. No subject plans were edited in this pass (read-only, as designed).
