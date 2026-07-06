---
doc_type: plan
title: Instruments Completion Tracker — denominator → numerator (cefi-first, operator-driven)
summary:
  Operator-owned working tracker to drive the instruments denominator/numerator completion to done. Points at the source
  plans/issues (does NOT restate them). Holds the live Decision Gates, the dependency-ordered Stage 0–6 checklist, the
  parallel per-AG track status, the blocked/waiting register, and a Progress Log. The governing law is Layer-1
  (instrument denominator) gates Layer-2 (capture) — correct + certify the denominator, cefi-first, then complete
  capture.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, meta]
repos: [instruments-service, unified-api-contracts, market-tick-data-service, deployment-service, deployment-api]
scope: [admin, engineer]
tags: [tracker, coordinator, honest-coverage, denominator, numerator, instruments, cefi-first, layer-1-gates-layer-2]
related:
  [
    honest_coverage_v2_instrument_denominator_2026_06_28.md,
    instruments_foundation_completeness_2026_06_24.md,
    migration_verification_orphan_safety_2026_06_10.md,
    instruments_mtds_subset_consistency_remediation_2026_06_17.md,
    data_completion_to_100_all_ag_2026_06_21.md,
    mvp_scope_catalogue_tagging_2026_06_08.md,
    instruments_catalogue_incremental_rollup_2026_06_29.md,
    issues/cefi_layer1_denominator_gaps_2026_07_03.md,
    issues/defi_expected_unattempted_backlog_1m_2026_07_03.md,
    issues/cefi_universe_capture_rule_2026_06_23.md,
    issues/honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md,
    issues/instruments_service_plan_reconciliation_2026_06_29.md,
    issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md,
    ../../codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-06
last_updated: 2026-07-06
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
---

> **🧭 HUMAN TRACKER — operator-owned (`assigned_vm: NA`, NOT auto-dispatched).** This is the working checklist to drive
> instruments completion to done. It **points at** the source plans/issues; it does not restate them. Tick items as they
> land, record each decision in the **Decision Gates** table, and append dated notes to the **Progress Log**. The
> tracker's own `estimate_*` reflects tracker maintenance only — the tracked engineering effort lives in the source
> plans.
>
> **⚖️ The one law — Layer-1 gates Layer-2.** The instrument denominator (could-exist universe) must be certified
> 100%-honest **before** any capture (%) number means anything — enforced at runtime, not just on paper
> (`assert_defi_catalog_fresh`; sports odds only enumerate against catalogued fixtures). So the order is always:
> **correct + certify the denominator (cefi-first) → then complete capture.**

---

## ✅ Decision Gates — clear these first (only the operator can)

D1–D3 **block Stage 2**. D4–D5 are lower-urgency. Record your call + date in the last column.

| #       | Decision                                                                                                                             | Options — **[REC]** = my recommendation                                                                        | Status            | Your call (date)                                                                                                                                                                                                             |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- | ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **D1**  | defi `expected_unattempted` seeding (≥1.38M cells never seeded → defi denominator understated + scans halt at 1M cap)                | **A: full 1,380,376-row apply, one run [REC]** · B: 684 recent only · Other: custom `--start/--end` slice      | ✅ **DECIDED: A** | **A — full apply** (2026-07-06). Genesis-verified safe: MVP floor = CURVE 2020-01-19; per-protocol pre-genesis classification. Still to execute the apply + 3-step verify.                                                   |
| **D2a** | cefi Layer-1 `(venue,itype)` gate authority (whole venues currently omitted → 79.55% is not even a bound)                            | **switch to UAC `INSTRUMENT_TYPES_BY_VENUE` [REC]** · extend `venue_instrument_type_to_tardis` · dedicated map | ✅ **DECIDED**    | **switch to `INSTRUMENT_TYPES_BY_VENUE`** + complete the 10 missing declared venues (2026-07-06). DERIBIT-COMBO → OPTION **(PROVISIONAL — future_combo Q sent to Ikenna 2026-07-06; awaiting reply, see Blocked register)**. |
| **D2b** | `VENUE_DATA_TYPE_CAPABILITIES` semantics for wholly-absent venues (BYBIT-SPOT / COINBASE-FUTURES / BINANCE-DELIVERY / KALSHI-PERP …) | add owner-verified capability entries · codify the no-entry semantics                                          | ✅ **DECIDED**    | **complete the table properly** + codify absent = not-expected (2026-07-06).                                                                                                                                                 |
| **D3**  | TradFi v9 `--apply` OOM restart (lone AG not yet canonical)                                                                          | restart the migration VM with **lower concurrency / larger machine** (mechanical; operator-launched)           | ✅ **DECIDED**    | **`--workers 24`** (fallback 16) · **per-year chunks** 2020→2026 · **e2-standard-16** · idempotent restart (2026-07-06). Manifest schema **v9** confirmed current.                                                           |
| **D4**  | cefi_tick G4 gate — Layer-1 carve-out                                                                                                | sanction as intentional Layer-2-only gate · fold under the two-layer gate                                      | ⬜ PENDING        |                                                                                                                                                                                                                              |
| **D5**  | Deribit options stance (`options_chain` effectively uncaptured)                                                                      | reaffirm "fine for now" · track the gap in data-status                                                         | ⬜ PENDING        |                                                                                                                                                                                                                              |

**Already-resolved (no action — context only):** Issue-4 UAC↔writer strays (RESOLVED 07-03, cefi 65.91→79.55) · ASTER
mode-split + C2 direction (Ikenna 07-03) · v10→v12 MVP drift (defi-only, banner text; no operational risk).

---

## 📊 Snapshot (2026-07-06)

- **Certified Layer-1 (denominator), 2026-06-29 — STALE, needs re-measure (Stage 3):** cefi **79.55** · defi 69.44 ·
  tradfi 51.43 · sports 30.77 · pred 66.67. _(Upper bounds where UAC under-specifies.)_
- **Layer-2 lower bounds (capture):** cefi 37.86 · defi 57.55 · tradfi 88.81 · sports 100 · pred 20.56.
- **DONE already:** denominator **generation** (catalogue built + self-refreshing) · Issue-4 strays · 4/5 AG v9
  `--apply` · opus-checkpoints + registry-consolidation (archived).
- **REMAINING (this tracker):** denominator **correctness + certification** → then **capture**.

---

## Stage 0 — Unblock (decisions + plan consolidation)

- [x] [DESIGN] P0. **D1–D3 decided** (see Decision Gates) — **hard gate on Stage 2** (all three decided 2026-07-06)
- [ ] [ADMIN] P1. Plan consolidation (from `issues/instruments_service_plan_reconciliation_2026_06_29.md` §F.1): archive
      `mvp_catalogue_finalization_v10` (done) · flip `instruments_catalogue_incremental_rollup` → `completed` (done,
      never flipped) · merge `path_to_100pct` → `data_completion` · fold cefi items of `instruments_mtds_subset` →
      foundation. _(Do this before engineering so you don't work a plan you're about to retire.)_

## Stage 1 — Close the canonical manifest baseline

_(cefi + defi already canonical — they do NOT wait on this; only tradfi does.)_

- [ ] [DATA] P0. TradFi v9 G4 `--apply` — per **D3**: `--workers 24` (fallback 16) · per-year chunks 2020→2026
      (`--start-date/--end-date`) · e2-standard-16 · idempotent restart → `migration_verification_orphan_safety` V6
      closes; **all 5 AGs canonical**. Then `rebuild_tradfi_manifest.py` (E5) + IS enumerate-seed + IS catalogue for
      tradfi.
- [ ] [DATA] P1. Operator-gated legacy-twin **deletes** (defi / tradfi / pred; cefi + sports already done) in a quiet
      window

## Stage 2 — Denominator correctness (the core; cefi leads)

- [ ] [CODE] P0. **2a. Land the single `build_expected` producer** (A17 — `honest_coverage_v2` Phase 1). Root fix; **now
      unblocked** (blocker archived 07-03). Bake **D2a** into it.
- [ ] [CODE] P0. **2b. cefi gate-authority fix on `build_expected`** (`issues/cefi_layer1_denominator_gaps`): apply
      D2a/D2b → ASTER live-forward split (**enumerator `start_date` support is a hard prereq before the UAC capability
      flip**) → BYBIT-SPOT `PERPETUAL` relabel → C2 MVP-data-type intersection
- [ ] [DATA] P0. **2c. cefi capture-rule residual** (`issues/cefi_universe_capture_rule`): drop
      `CEFI_BASE_ASSET_UNIVERSE` cap from the IS adapter + **run the manifest reclassification `--apply`** (never
      confirmed run → denominator may be stale for 6 venues)
- [ ] [DATA] P0. **2d. IS-catalogue completion `B0→B1→B2`** (`instruments_mtds_subset`): backfill instruments to
      no-missing (B0) → regen catalogue + un-pause daily schedulers (B1) → codify MVP-vs-total universe (B2). _B0 gates
      every expected-universe consumer._
- [ ] [DATA] P0. **2e. defi seeding apply** (D1) → then the follow-on check for the same never-seeded backlog on cefi /
      tradfi / pred
- [ ] [CODE] P1. **2f.** Reapply the denominator-gap model to **LIGHTER / EXTENDED / PACIFICA**

## Stage 3 — Re-measure + certify Layer-1

> **⛔ PREREQUISITE (added 2026-07-06):** the cefi re-measure is GATED on the **KALSHI-PERP contamination purge** —
> 25,473 fake `KALSHI-PERP` `PERPETUAL` rows (Kalshi _event contracts_ mis-emitted by the wrong-host `kalshi_perp`
> adapter, `is@4da6fe8`) must be purged from the cefi catalogue first, or the Layer-2 cefi numbers are polluted. Owned
> by `issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md` **Phase 0** (slot-2 + the 4da6fe8 author) — NOT
> this tracker's work; Stage 3 just waits on it. (POLYMARKET-PERP is clean, 0 rows.)

- [ ] [SCRIPT] P0. Re-run `measure_honest_coverage` on the corrected catalogue + seeded manifests (**06-29 numbers are
      stale** — predate v12, the incremental-rollup switch, and the cefi 122-row ghost-dupe fix of 07-04)
- [ ] [VERIFY] P0. Certify per-AG Layer-1; **record fresh numbers in the Progress Log** — only now is any Layer-2 %
      trustworthy
- [ ] [CODE] P1. Close `honest_coverage_v2` remaining (build_expected done in 2a; UI drill-down → Stage 6)

## Stage 4 — Foundation gate sign-offs (formalize the spine, cefi-first)

_(`instruments_foundation_completeness` has heavy checkbox-vs-reality drift — much of G2/G3 actually ran; the work is
reconciling + signing off, not redoing.)_

- [ ] [CODE] P0. cefi **G1.2** (`record_failed` routing + 06-26 re-capture) + **G1.3 follow-up** (on-chain-CeFi-perp
      venue form)
- [ ] [VERIFY] P0. Reconcile checkbox drift; take the formal **G2 → G5** sign-offs (cefi)
- [ ] [DATA] P1. tradfi **§8 retirement purge** (4-leg GCS delete — ICE / CBOE-OPRA / VX-spread / VIX-cash) —
      **OPERATOR-CONFIRM**
- [ ] [DESIGN] P1. defi completeness **oracle** design

## Stage 5 — Capture to 100% (Layer-2 — only after Layer-1 is honest)

- [ ] [INFRA] P1. `data_completion` operator-gated items: pyth `collect-oracle-prices` launch · Live ODDS quota · MANTLE
      paid RPC · CLOB-on-chain asset_group classification (Lighter/Pacifica/Extended) · rate-limit probe VM
- [ ] [DATA] P1. Reconcile the DEDUP-flagged folded-in tail (from merged `path_to_100pct`) — **do not double-run**
- [ ] [CODE] P1. DeFi `risk_params` MTDS handler (193,042 EU, no handler today)
- [ ] [CODE] P1. prediction live token-universe fix (owned by `prediction_venue_perps_and_live_clob_depth_2026_06_20`;
      live=0 today)

## Stage 6 — Hygiene (run in parallel; non-blocking)

- [ ] [ADMIN] P2. Flip stale / self-contradictory checkboxes (`instruments_mtds_subset`: `N9c`, `N5r/N6r`,
      "migrate-first 4 AGs"; `instruments_catalogue_incremental_rollup` → completed)
- [ ] [VERIFY] P2. `honest_coverage_smoke_harness`: run the deferred **cefi / defi / tradfi / prediction** live-verify
      slices (only sports ran)
- [ ] [DATA] P2. v9 `schema_version` tail re-stamp (quiet window, post fleet-drain)
- [ ] [UI] P2. data-status **UI drill-down** (last open `honest_coverage_v2` item)

---

## 🚦 Parallel per-AG tracks (current gate on each)

| AG             | Canonical? | Current gate / next action                                                                          |
| -------------- | ---------- | --------------------------------------------------------------------------------------------------- |
| **cefi**       | ✅ yes     | **LEAD.** Needs D2a/D2b → Stage 2a→2c → re-measure (3) → capture (5)                                |
| **tradfi**     | ❌ no      | Blocked on **D3** (OOM restart) → Stage 1 → B0 backfill → denominator                               |
| **defi**       | ✅ yes     | Blocked on **D1** (seeding) → 2e → honest denominator                                               |
| **sports**     | ✅ yes     | **RE-HOMED** to `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` — out of this tracker |
| **prediction** | ✅ yes     | Denominator ~ok; **live=0** blocked on the prediction CLOB plan (stale IS token universe)           |

## ⛔ Blocked / waiting register

- **✅ All Stage-0 decisions DECIDED 2026-07-06** (D1 full-seed · D2a/D2b declarative gate · D3 tradfi restart).
  Remaining before execution = (a) leaving "local" mode to run the live steps, (b) Ikenna's DERIBIT-COMBO reply (below).
- **DERIBIT-COMBO `future_combo`** — sub-question of D2a, **sent to Ikenna 2026-07-06, awaiting reply.** Proceeding
  PROVISIONALLY with `{OPTION}` (MVP-correct; Deribit MVP = `options_chain` only) so D2 isn't blocked. **When his answer
  lands, update:**
  - **A / OPTION-only** → confirm, clear this line, done (no code change beyond the provisional).
  - **B / `{OPTION, FUTURE}`** → add `FUTURE` to DERIBIT-COMBO in `INSTRUMENT_TYPES_BY_VENUE` **and**
    `VENUE_DATA_TYPE_CAPABILITIES`, then re-measure (Stage 3).
  - **Other / drop** → remove DERIBIT-COMBO from the cefi denominator entirely.
- **KALSHI-PERP contamination purge (25,473 fake rows)** — **Stage-3 re-measure prerequisite**; owned by
  `issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md` Phase 0 (slot-2 / 4da6fe8 author), NOT this
  tracker. Stop-emit at source + purge the `venue=KALSHI-PERP` cefi cells. POLYMARKET-PERP clean.
- **KALSHI-PERP / POLYMARKET-PERP real capture** — BLOCKED-CREDENTIALS: real perps live on the auth'd margin API (Kalshi
  member-rollout; Polymarket beta), not the events host. **Venues STAY declared in the cefi denominator (D2 unchanged)**
  but read as credentials-gated honest-absence until the Phase-4 prod cutover.
- **MANTLE paid RPC** — BLOCKED-CREDENTIALS (paid endpoint key → Secret Manager)
- **SFI + Transfermarkt sports keys** — BLOCKED-CREDENTIALS (subscription, not rotation)
- **cefi batch-Tardis historical (~776k cells)** — billing-gated, **permanent sanctioned exclusion** (not "open")
- **rate-limit probe** — needs a disposable-IP VM (operator-gated)
- **`source_data_latency.py` re-pin** — needs ~2 weeks of live accrual (time-gated, not a decision)

## 📓 Progress Log

- **2026-07-06** — **KALSHI-PERP contamination assessed vs D2** (from the pulled
  `prediction_universe_capture_dead_since_07_01` issue; surfaced by the slot-2 incremental-catalogue agent). The
  `kalshi_perp` adapter points at the WRONG Kalshi host (events `api.elections.kalshi.com`, binary-only) → its category
  filter is a no-op → it emitted **25,473 Kalshi event contracts as fake `KALSHI-PERP` `PERPETUAL`** into the cefi store
  (6.8% of the cefi catalogue; 0 MVP-tagged; span 06-29→07-06 from `is@4da6fe8`). POLYMARKET-PERP clean (0 rows).
  **Impact on D2 (assessed): denominator decision UNCHANGED** — KALSHI-PERP/POLYMARKET-PERP are real declared cefi perp
  venues, already `{PERPETUAL}` in `INSTRUMENT_TYPES_BY_VENUE` (NOT in D2's 10-missing list), operator ruled "keep the
  venues, correct the adapter." **Two sequencing consequences added:** (1) Stage-3 cefi re-measure now GATED on the
  Phase-0 purge; (2) real KALSHI/POLYMARKET-PERP capture is BLOCKED-CREDENTIALS (margin API) → credentials-gated
  honest-absence in the denominator. Correction owned by slot-2 + the 4da6fe8 author — adapters NOT touched here.
- **2026-07-06** — **D3 DECIDED.** TradFi v9 `--apply` (the last un-canonical AG) restart: **`--workers 24`** (fallback
  16 if SSL-EOF/pool-full recurs) · **per-year chunks** 2020→2026 (via `--start-date/--end-date`) · **e2-standard-16
  (64GB)** · idempotent restart (skips the ~37k already done). Root cause = connection-pool thrash at `--workers 64` on
  e2-standard-8 **+** up-front full object-list accumulation (tradfi is the biggest AG, ~6M objects) — NOT a data-volume
  wall (defi succeeded at 96; sports deliberately dropped to 16), so lower concurrency + chunking is the fix, not just
  more RAM. **Manifest schema = v9 confirmed current** (`CANONICAL_SCHEMA_VERSION = 9`; the v12 is MVP-scope, orthogonal
  — operator flagged, verified). Execution step (live VM) — queued for leaving "local" mode; monitor per
  no-fire-and-forget (STARTED<60s · progress · verify T+10min). Migrator fixes object PATHS only;
  `rebuild_tradfi_manifest.py` (E5) + IS enumerate-seed + IS catalogue for tradfi follow. **Closes Stage-0 — all 3
  blockers decided.**
- **2026-07-06** — DERIBIT-COMBO `future_combo` question **relayed to Ikenna** (context message drafted + passed on by
  operator; he'll answer when available). **Proceeding provisionally with `{OPTION}`** (MVP-correct — Deribit MVP =
  `options_chain` only) so D2 is not blocked. Flagged as awaiting-reply in the D2a Decision-Gates row + the
  Blocked/waiting register, with the exact per-answer (A/B/Other) update actions listed there for a one-line change when
  he replies.
- **2026-07-06** — **D2 DECIDED.** **D2a** = switch the cefi Layer-1 itype-gate authority from the tardis fetch-routing
  map (`VenueMapping.venue_instrument_type_to_tardis`, iterated in
  `check_enumeration_completeness._get_cefi_venue_itypes`) → the **declarative `INSTRUMENT_TYPES_BY_VENUE`** (aligns
  cefi with defi `PROTOCOL_CAPABILITIES.instrument_types` / tradfi `TRADFI_VENUE_INSTRUMENT_TYPES`), AND **complete it
  for the 10 declared cefi venues currently missing** (of 24 in `VENUES_BY_ASSET_GROUP["cefi"]`): BINANCE-DELIVERY ·
  DERIBIT-COMBO · COINBASE-FUTURES · BITFINEX-SPOT · BITFINEX-FUTURES · BITGET-SPOT · BITGET-FUTURES · PACIFICA-SOLANA ·
  EXTENDED-STARKNET · LIGHTER-ZKSYNC. Proposed itypes (owner-verify at impl): `-SPOT`→{SPOT_PAIR};
  `-FUTURES`/BINANCE-DELIVERY→{PERPETUAL,FUTURE}; PACIFICA/EXTENDED/LIGHTER →{PERPETUAL}; **DERIBIT-COMBO→{OPTION}**
  (operator 2026-07-06). Rejected: extend-tardis-map (fetch blast radius; sourcing≠existence), dedicated-new-map (drift
  surface). **D2b** = complete `VENUE_DATA_TYPE_CAPABILITIES` for the declared-but-absent venues + codify "a declared
  venue MUST carry a capability entry; absent = stray/not-expected" (resolves the checker-treats-absent-as-carved-out vs
  enumerator-treats-absent-as-not-gated asymmetry). Expected effect: cefi Layer-1 denominator GROWS, % drops below
  79.55% — the honest direction. **⚠️ OPEN NUANCE (non-MVP):** DERIBIT-COMBO venue registration carries BOTH
  `option_combo` AND `future_combo` kinds; {OPTION} is correct for MVP (Deribit MVP = `options_chain` only), but a
  {OPTION}-only type omits `future_combo` from the full-universe denominator — confirm defer-future_combo (non-MVP) vs
  {OPTION,FUTURE}. Also reconcile the COINBASE (declared) vs `COINBASE_SPOT` (map constant) naming at impl. Sequenced
  AFTER C2 MVP-gate intersection (already decided); re-measure closes it (Stage 3).
- **2026-07-06** — **D1 DECIDED = A** (full 1,380,376-row apply). Verified safe before deciding: (1) enumerator
  classifies pre-genesis **per-(chain, protocol)** via on-chain-derived `PROTOCOL_LAUNCH_DATES` + `CHAIN_GENESIS_DATES`
  (`enumerate_expected_universe.py` L27-28/96-99); (2) defi MVP universe = 11 curated venues, earliest =
  **CURVE-ETHEREUM 2020-01-19** (web-confirmed Jan 2020; Balancer/Lido/Uniswap-V3 cross-checks all matched the SSOT) →
  all 2018-2019 is pre-genesis for MVP; (3) MAKER (2017) / IDLE (2019-08) are NOT in MVP and are per-protocol-classified
  in the full universe → no real-data clipping. Zero downloads; +1.38M typed honest-absence rows. **Remaining:** execute
  the apply (`enumerate_expected_universe.py --asset-group defi --apply-write --max-writes-per-run 1500000`) + 3-step
  verify (row-delta ≈ +1.38M · fresh scan → ~0 candidates · data-status refresh), then the P2 cross-AG backlog check.
  Minor follow-up noted: Balancer SSOT date 2020-03-31 vs first V1 bronze deploy ~2020-02-26 (~34d, immaterial to this
  seeding; in the 2020 actionable zone, not the 2018-19 pre-genesis block).
- **2026-07-06** — Tracker created. Baseline captured from the 4-plan deep-read +
  `instruments_service_plan_reconciliation` §D/E/F. Awaiting decisions D1–D3 to open Stage 2.

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

---

### Source plans / issues (pointers — read there, don't duplicate here)

- **Model / measure:** `honest_coverage_v2_instrument_denominator_2026_06_28.md` ·
  `honest_coverage_smoke_harness_2026_06_28.md`
- **Denominator generation (done):** `mvp_catalogue_finalization_v10_2026_06_27.md` ·
  `instruments_catalogue_incremental_rollup_2026_06_29.md` · `mvp_scope_catalogue_tagging_2026_06_08.md`
- **Spine / apply gate:** `instruments_foundation_completeness_2026_06_24.md` ·
  `migration_verification_orphan_safety_2026_06_10.md` · `instruments_mtds_subset_consistency_remediation_2026_06_17.md`
- **Capture:** `data_completion_to_100_all_ag_2026_06_21.md`
- **Open corrections:** `issues/cefi_layer1_denominator_gaps_2026_07_03.md` ·
  `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md` · `issues/cefi_universe_capture_rule_2026_06_23.md`
- **Resolved / map:** `issues/honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md` ·
  `issues/instruments_service_plan_reconciliation_2026_06_29.md`
- **SSOT:** `../../codex/02-data/honest-coverage-model.md`
