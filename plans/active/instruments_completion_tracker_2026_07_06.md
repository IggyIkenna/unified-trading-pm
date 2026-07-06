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

> **🟢 TradFi v9 migration APPLY DONE (2026-07-06) — all 6 years 2020-2025 `exit_code=0`, fatal=0.** The D3 fix held at
> scale (e2-standard-16 · SPOT · workers 24 · per-year chunks; memory ~6.7 GB / 64 GB per VM; `moved<planned` =
> idempotent skips of already-canonical objects). Launcher OOM-fix: **deployment-service@77cfcda**. **STILL PENDING
> (deferred → AO/Ikenna):** 2026 (held for the live CME-OHLCV capture VMs) · post-apply chain (orphan-sweep E=0 ·
> straggler re-run · `rebuild_tradfi_manifest` · IS enumerate-seed + catalogue) · Ikenna's migration sign-off (gates the
> legacy-twin bucket deletes). See Stage 1 + the Progress Log.

---

## ✅ Decision Gates — clear these first (only the operator can)

D1–D3 **block Stage 2**. D4–D5 are lower-urgency. Record your call + date in the last column.

| #       | Decision                                                                                                                             | Options — **[REC]** = my recommendation                                                                        | Status            | Your call (date)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **D1**  | defi `expected_unattempted` seeding (≥1.38M cells never seeded → defi denominator understated + scans halt at 1M cap)                | **A: full 1,380,376-row apply, one run [REC]** · B: 684 recent only · Other: custom `--start/--end` slice      | ✅ **DECIDED: A** | **A — full apply** (2026-07-06). Genesis-verified safe: MVP floor = CURVE 2020-01-19; per-protocol pre-genesis classification. Still to execute the apply + 3-step verify.                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **D2a** | cefi Layer-1 `(venue,itype)` gate authority (whole venues currently omitted → 79.55% is not even a bound)                            | **switch to UAC `INSTRUMENT_TYPES_BY_VENUE` [REC]** · extend `venue_instrument_type_to_tardis` · dedicated map | ✅ **DECIDED**    | **switch to `INSTRUMENT_TYPES_BY_VENUE`** + complete the 10 missing declared venues (2026-07-06). DERIBIT-COMBO → OPTION **(CONFIRMED by Ikenna 2026-07-06 — future_combo NOT in MVP, options only)**.                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| **D2b** | `VENUE_DATA_TYPE_CAPABILITIES` semantics for wholly-absent venues (BYBIT-SPOT / COINBASE-FUTURES / BINANCE-DELIVERY / KALSHI-PERP …) | add owner-verified capability entries · codify the no-entry semantics                                          | ✅ **DECIDED**    | **complete the table properly** + codify absent = not-expected (2026-07-06).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| **D3**  | TradFi v9 `--apply` OOM restart (lone AG not yet canonical)                                                                          | restart the migration VM with **lower concurrency / larger machine** (mechanical; operator-launched)           | ✅ **DECIDED**    | **`--workers 24`** (fallback 16) · **per-year chunks** 2020→2026 · **e2-standard-16** · idempotent restart (2026-07-06). Manifest schema **v9** confirmed current.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **D4**  | cefi_tick G4 gate — Layer-1 carve-out                                                                                                | sanction as intentional Layer-2-only gate · **fold under the two-layer gate [REC]**                            | ✅ **DECIDED**    | **Fold under the two-layer gate** — ALREADY RESOLVED by Ikenna 2026-07-03 (C4 option a): G4 enforces Layer-1 AND Layer-2; cefi-MVP not honest-complete while the denominator has holes. Matches the governing law; G4 can't close until D2 (`cefi_layer1_denominator_gaps`) lands. Tracker was stale (reconciliation predated the 07-03 call).                                                                                                                                                                                                                                                                                                     |
| **D5**  | Deribit options stance (`options_chain` effectively uncaptured)                                                                      | **not a standalone decision** — capture gap, root-caused to an unregistered handler (Ikenna C5)                | ✅ **RESOLVED**   | **Not an operator fork — ROOT-CAUSED (Ikenna C5, verified in code 2026-07-06).** DERIBIT `options_chain` captured=0/1 because `DeribitOptionsChainHandler` is BUILT but NEVER REGISTERED (absent from `handlers/__init__.py` `__all__`, `main.py` import, and the operations dispatcher) → no operation invokes it → zero shards. **A re-measure alone won't move it — it's a real CAPTURE GAP.** Fix = Ikenna's 3-line MTDS handler registration (he owns it, in progress) → `deribit-options-chain` backfill (Stage 5) → THEN the honest number shows in the Stage-3 re-measure. MVP "don't widen beyond BTC/ETH `options_chain`" stance STANDS. |

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
- [ ] [ADMIN] P1. Plan consolidation (from `issues/instruments_service_plan_reconciliation_2026_06_29.md` §F.1) —
      **REASSESSED 2026-07-06**:
  - [x] **merge `path_to_100pct` → `data_completion` = ✅ ALREADY DONE** (superseded + archived 2026-06-30;
        `data_completion` § "Folded-in from `path_to_100pct`"; only the DEDUP residual remains = the Stage-5 item).
  - [ ] **flip `instruments_catalogue_incremental_rollup` → completed = ⛔ DO NOT FLIP** — its lone open item is a LIVE
        issue, not moot: the operator-declined tradfi catalogue-scheduler band-aid **re-triggered 2026-07-03** (tradfi
        `prod/catalog.parquet` stale since 2026-06-29, daily `lifecycle_catalogue_scheduler` runs killed at 3600s
        timeout). Flipping would bury it → operator decision needed (re-enable band-aid vs. ship Phase-3 incremental).
  - [ ] **archive `mvp_catalogue_finalization_v10`** (0-open, done) + **fold `instruments_mtds_subset` cefi items →
        foundation** (60 open, ⚖️ REVIEW) — both `locked_by: live-defi-rollout` → **operator unlock/sign-off REQUIRED**
        (HARD RULE: locked-plan archival is never-autonomous; §F.4 ⚖️). _(Do before engineering so you don't work a plan
        you're about to retire.)_

## Stage 1 — Close the canonical manifest baseline

_(cefi + defi already canonical — they do NOT wait on this; only tradfi does.)_

- [ ] [DATA] P0. TradFi v9 G4 `--apply` — per **D3**: `--workers 24` (fallback 16) · per-year chunks 2020→2026
      (`--start-date/--end-date`) · e2-standard-16 · idempotent restart → `migration_verification_orphan_safety` V6
      closes; **all 5 AGs canonical**. Then `rebuild_tradfi_manifest.py` (E5) + IS enumerate-seed + IS catalogue for
      tradfi. **🟡 IN FLIGHT (2026-07-06): 2025 smoke VALIDATED (memory 6.7 GB / 64 GB steady, 172k candles migrating) →
      FANNED OUT 2020-2024 (6 VMs total: `canonical-migration-tradfi-*`, e2-standard-16 · SPOT · workers 24 · MTDS
      9ecd1e2; launcher fix deployment-service@77cfcda). 2026 held last (live CME-OHLCV capture VMs writing 2026).
      Post-apply: orphan-sweep E=0 + idempotent re-run for transient-503 stragglers, then `rebuild_tradfi_manifest` + IS
      enumerate-seed + IS catalogue.**
- [ ] [DATA] P1. Operator-gated legacy-twin **deletes** (defi / tradfi / pred; cefi + sports already done) in a quiet
      window

## Stage 2 — Denominator correctness (the core; cefi leads)

- [ ] [CODE] P0. **2a. Land the single `build_expected` producer** (A17 — `honest_coverage_v2` Phase 1). Root fix; **now
      unblocked** (blocker archived 07-03). Bake **D2a** into it.
- [ ] [CODE] P0. **2b. cefi gate-authority fix on `build_expected`** (`issues/cefi_layer1_denominator_gaps`): apply
      D2a/D2b → ASTER live-forward split (**enumerator `start_date` support is a hard prereq before the UAC capability
      flip**) → BYBIT-SPOT `PERPETUAL` relabel → C2 MVP-data-type intersection
- [ ] [DATA] P0. **2c. cefi capture-rule residual** (`issues/cefi_universe_capture_rule`) — **REASSESSED (opus,
      2026-07-06)**: **cap-drop = ✅ ALREADY DONE `is@0fe8e71` (06-23)** (`_passes_asset_filter` now applies only
      accepted-quote + BTC/ETH- options gates; full-universe enumeration verified). **Reclassification `--apply` = ⛔ DO
      NOT RUN — RE-SCOPED.** The `reclassify_cefi_manifest_mvp_universe_2026_06_23.py` script is unsafe + superseded:
      (a) `_derive_base` DATA-LOSS bug — mis-parses Bitfinex `ADAF0:USTF0` + Kraken `PF_/PI_` wire-forms → would DELETE
      ~380k+ legit in-MVP **captured** BITFINEX/KRAKEN rows; (b) architecturally superseded (honest-coverage-v2 forbids
      deriving the denominator from the manifest — circular); (c) collides with the in-flight ASTER split (461k empty→EU
      flips are ASTER `SOURCE_RETURNED_ZERO`); (d) the 6 "stale" venues are ALREADY in the manifest with real data. It
      already ran 2× on 06-23 (snapshots exist — "never confirmed run" resolved). **→ retire the manifest-pruning
      script; do the MVP filter as a read-time gate in `measure_honest_coverage` folded into 2a `build_expected`,
      sequenced after 2b + the ASTER split.**
- [ ] [DATA] P0. **2d. IS-catalogue completion `B0→B1→B2`** (`instruments_mtds_subset`): backfill instruments to
      no-missing (B0) → regen catalogue + un-pause daily schedulers (B1) → codify MVP-vs-total universe (B2). _B0 gates
      every expected-universe consumer._
- [x] [DATA] P0. **2e. defi seeding apply (D1) — ✅ DONE** (opus, run_id `enum-universe-defi-20260706-130616`):
      **+1,380,376 typed `empty_confirmed` rows** (per-year matches the issue to the row: 2018=695,830 / 2019=683,862 /
      2021-25=684), `expected_unattempted` +0 (zero downloads), fresh full-window scan **→ 0 candidates** (≥1M
      enumerator halt cleared), consolidator merged into the canonical defi manifest. Scan-gate hit EXACTLY 1,380,376 +
      1-day smoke verified first. No enumerator edit (read/run only).
- [ ] [VERIFY] P2. **2e follow-on** (was bundled into 2e): the cross-AG never-seeded backlog check on **cefi / tradfi /
      pred** (scan-only investigation — dispatch separately)
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
- [x] [CODE] P1. **Deribit `options_chain` — handler registration** (Ikenna C5; taken over from Ikenna + verified) —
      **DONE, mtds@9ecd1e29e** (QG-green + quickmerge). Registered `DeribitOptionsChainHandler` in the MTDS operations
      dispatcher (`main.py` import + `"deribit-options-chain"` key) + a regression test asserting the operation
      resolves. NOTE: the `__init__.py` `__all__` step in Ikenna's sketch was cosmetic (main.py imports handlers by full
      path) and correctly skipped. Root cause of D5's captured=0 is now closed at the code level.
- [ ] [INFRA] P1. **Deribit `options_chain` — live runner**: wire a live cron/VM to run
      `--operation deribit-options-chain` (the handler is **live/replay only — no backfill**, `process()` collects
      `date.today()`), so it actually captures BTC/ETH `options_chain` daily → then feeds the Stage-3 re-measure.
      Historical options are NOT captured by this handler (separate concern if ever needed).
- [ ] [SCRIPT] P1. **Systemic unregistered-handler audit** (generalizes the Deribit C5 bug — do BEFORE the Stage-3
      re-measure). Diff every handler class in `market-tick-data-service/.../cli/handlers/` against the `operations={…}`
      dispatcher keys in `cli/main.py` to find handlers that are **built but never wired** (silent `captured=0`, same
      class as Deribit). The MTDS QG live-coverage roll-up flags large `blocked-not-registered` counts (cefi 104 · defi
      1225 · sports 70 · tradfi 40 cells) — the audit distinguishes **built-but-unwired** (fixable like C5: register +
      test) from **genuinely-not-built** (needs a new handler / is honest-absence). Running it before the re-measure
      keeps us from mislabelling a wiring bug as a real coverage gap. Each finding → register-and-test, or file/triage.
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
  Remaining before execution = leaving "local" mode to run the live steps. **Ikenna's DERIBIT-COMBO reply LANDED
  2026-07-06 — OPTION-only (future_combo not in MVP); resolved below.**
- **✅ DERIBIT-COMBO `future_combo` — RESOLVED (Ikenna 2026-07-06): OPTION-only.** `future_combo` is **NOT in MVP**
  (Deribit MVP = `options_chain` only), so DERIBIT-COMBO stays `{OPTION}` in `INSTRUMENT_TYPES_BY_VENUE` — the
  provisional is now final, **no code change beyond it**. D2a fully closed; nothing further to wire for Deribit combo in
  the denominator.
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

- **2026-07-06** — **TradFi v9 migration APPLY COMPLETE — all 6 years (2020-2025), exit_code=0, fatal=0.** The D3 fix
  (e2-standard-16 · SPOT · workers 24 · per-year chunks) held at scale — memory stayed ~6.7 GB / 64 GB per VM, zero OOM
  across the fleet. `moved<planned` on every year = idempotent skips of already-canonical objects (per-year TOTALs: 2021
  moved 783,448 · 2022 738,644 · 2024 786,334 · etc.). **NEXT (deferred → AO / Ikenna):** 2026 migration (after the live
  CME-OHLCV capture VMs drain) → orphan-sweep E=0 + idempotent straggler re-run (transient 503s) →
  `rebuild_tradfi_manifest` (E5) → IS enumerate-seed + catalogue → all 5 AGs canonical +
  `migration_verification_orphan_safety` V6 closes. Ikenna's migration sign-off gates the legacy-twin bucket deletes.
- **2026-07-06** — **2e SHIPPED — defi denominator corrected (+1,380,376 rows).** D1 defi `expected_unattempted` seeding
  ran (opus, v1 enumerator — the `--enumerator-version=v2` in the dispatch was my spec error, caught by the agent +
  confirmed). run_id `enum-universe-defi-20260706-130616`. Scan-gate hit **exactly 1,380,376** (0% dev) → 1-day smoke
  (1,910 rows, 3-step clean) → full apply **1,380,376 rows** (per-year to the row) → fresh scan **→ 0 candidates** (≥1M
  halt cleared), `expected_unattempted` +0 (zero downloads), consolidator merged into the canonical defi manifest. No
  enumerator edit; poisoned `/tmp` cache cleaned. **Ready to flip** `issues/defi_expected_unattempted_backlog_1m` (same
  evidence). Cross-AG never-seeded follow-on (cefi/tradfi/pred) split to a separate P2.
- **2026-07-06** — **D2a SHIPPED + VERIFIED — cefi Layer-1 dropped to the honest number.** Both halves landed:
  **uac@e76d874a** (`INSTRUMENT_TYPES_BY_VENUE` completes the 10 declared venues; DERIBIT-COMBO OPTION-only) +
  **is@03cfd0f** (`_get_cefi_venue_itypes` now sources declarative `INSTRUMENT_TYPES_BY_VENUE`, not the tardis
  fetch-routing table). QG-green both repos, trees clean, in sync, 41 tests pass (dynamic — no golden edits). **Measured
  delta (same manifest snapshot, back-to-back): cefi Layer-1 84.09% → 73.61%** (expected 44→72, +28 tuples, 0 removed) —
  the honest direction (the "79.55%" was a stale point-in-time snapshot; the before/after PAIR is apples-to-apples).
  Agent caught + fixed 2 latent regressions via tuple-diffing: bare `COINBASE` (declared but absent from the dict) +
  `DERIBIT` missing `SPOT_PAIR` (would have REMOVED 2 real tuples). D2b: added `VENUE_DATA_TYPE_CAPABILITIES` for
  PACIFICA/EXTENDED/LIGHTER/COINBASE-FUTURES. **⚠️ BIG FINDING (operator decision): bare `COINBASE` + `DERIBIT-COMBO`
  still produce 0 EXPECTED** — absent from `MVP_SCOPE["cefi"].venues` (which has COINBASE-SPOT/FUTURES, not bare
  COINBASE), so gate #3 zeroes them regardless of the dict fix. **Decide: add bare `COINBASE` to `MVP_SCOPE.venues` (+ a
  DERIBIT-COMBO MVP-membership call), or confirm intentionally out.** (BINANCE-DELIVERY also 0 — COIN-M explicitly
  not-MVP per 06-27 decision #3, correct.)
- **2026-07-06** — **2c cefi capture-rule REASSESSED (opus agent) — prevented a ~380k-row data-loss.** Cap-drop half was
  ALREADY shipped (`is@0fe8e71`, 06-23). Reclassification half STOPPED at the smoke (mutated NOTHING): the
  `reclassify_cefi_manifest_mvp_universe_2026_06_23.py` script would DELETE ~380k+ legit in-MVP **captured**
  BITFINEX/KRAKEN rows via a `_derive_base` bug (mis-parses Bitfinex `ADAF0:USTF0` + Kraken `PF_/PI_` wire-forms → wrong
  base → perp-gate drops their spot rows), is architecturally superseded (honest-coverage-v2 forbids deriving the
  denominator from the manifest — circular), collides with the in-flight ASTER split (461k ASTER `SOURCE_RETURNED_ZERO`
  empty→EU flips), and destabilises measurement (index rewrite flips PRIMARY-bucket selection). It already ran 2× on
  06-23 (snapshots exist). **RE-SCOPE (operator decision): retire the manifest-pruning script → MVP filter as a
  read-time gate in `measure_honest_coverage`, folded into 2a `build_expected`, sequenced after 2b + the ASTER split.**
  No data mutated, no reserved file touched.
- **2026-07-06** — **TradFi smoke VALIDATED → fanned out 2020-2024.** The 2025 smoke proved the D3 fix: memory flat at
  **6.7 GB / 64 GB** for 18+ min while migrating candles (172k/577k, steady ~11k/min) — vs. the 06-29 climb-to-OOM at
  workers 64. Setup ran in ~1 min (`uv` install). Fanned out **2020, 2021, 2022, 2023, 2024** as 5 concurrent per-year
  VMs (disjoint day-partitions; all e2-standard-16 · SPOT · workers 24 · MTDS 9ecd1e2 pinned). **2026 held for last**
  (live `tradfi-bf-cme-ohlcv-1m-*` capture VMs are writing 2026 processed_candles). Noted: a transient GCS 503 burst
  ("internal error, retry") left ~7 objects unmoved on 2025-02-03/04 — not memory / not our bug, self-limited; recovered
  by the migrator's idempotency + the mandatory post-apply orphan-sweep (V6 E=0). Fleet watchdog armed on `run.log` (the
  serial console is blind to the backgrounded migrator — lesson). **Next:** per-year completion (VMs self-stop) → 2026 →
  orphan-sweep + straggler re-run → `rebuild_tradfi_manifest` + IS enumerate-seed + IS catalogue.
- **2026-07-06** — **Stage-0 consolidation REASSESSED (the one-liner was partly stale).** Investigated §F.1 before
  executing: (1) **`path_to_100pct` → `data_completion` merge = already DONE** (superseded + archived 2026-06-30;
  `data_completion` carries the "Folded-in from `path_to_100pct`" section; DEDUP residual is already a Stage-5 item — no
  orphaned work). (2) **`instruments_catalogue_incremental_rollup` → completed = must NOT flip** — its lone open item is
  a LIVE issue: the operator-declined tradfi catalogue-scheduler band-aid **re-triggered 2026-07-03** (tradfi
  `prod/catalog.parquet` stale since 2026-06-29; daily `lifecycle_catalogue_scheduler` runs killed at the 3600s
  timeout). Flipping would bury it. (3+4) **archive `mvp_catalogue_finalization_v10`** (0-open) + **fold
  `instruments_mtds_subset` cefi items → foundation** (60 open, ⚖️ REVIEW) are both `locked_by: live-defi-rollout` →
  **operator unlock/sign-off required** (HARD RULE: locked-plan archival never-autonomous; §F.4). No plan mutated
  pending sign-off; surfaced to operator.
- **2026-07-06** — **TradFi v9 migration RESTARTED (D3 fix) — 2025 smoke launched.** The 2026-06-29 full-range run
  OOM-killed on e2-standard-8 at `--workers 64`; baked the D3 fix into the launcher (`launch-canonical-migration-vm.sh`:
  `MACHINE_TYPE` override, SPOT default + `ON_DEMAND=true` opt-out, tradfi `--workers` default 24) —
  **deployment-service@77cfcda** (QG-green + quickmerge). Verified the VM runs from GCS **code tarballs** (no Docker)
  and pinned `MTDS_TARBALL_SHA=9ecd1e2` (today's build; tradfi migrator byte-identical to LDR HEAD) so the smoke proxies
  the fan-out. Launched the **2025 smoke** `canonical-migration-tradfi-20260706-170108` (e2-standard-16 · SPOT · workers
  24 · `--apply`), verified STARTED (RUNNING <60s), armed a no-fire-and-forget watchdog. Migrator date-shards its walk
  (`_iter_days`) so a 1-year range bounds the up-front object-list accumulation (the OOM cause). **Next:** watchdog
  verdict ~T+16min → if memory-bounded + objects migrating, fan out 2020-2024 + 2026 (2026 last, after the live
  CME-OHLCV capture VMs). NOT blocked on Stage 0 (its leftover is doc-consolidation on cefi/catalogue plans — running in
  parallel).
- **2026-07-06** — **DERIBIT-COMBO `future_combo` RESOLVED (Ikenna).** Ikenna confirmed `future_combo` is **NOT in MVP**
  — Deribit uses `options_chain` (OPTION) only. DERIBIT-COMBO stays `{OPTION}` in `INSTRUMENT_TYPES_BY_VENUE`; the D2a
  provisional is now **final, with no further code change**. Cleared the D2a Decision-Gates note, the Blocked/waiting
  register entry, and the D2 OPEN-NUANCE flag. **D2a fully closed** — the last open external item on this tracker's own
  decisions is resolved (the remaining open items — KALSHI-PERP purge (slot-2) and credentials-gated captures — are not
  our decisions).
- **2026-07-06** — **C5 FIX SHIPPED — took over Ikenna's unfinished fix.** Ikenna's C5 registration fix hadn't landed
  (bad network Friday), so we completed it properly: verified the root cause end-to-end, made the minimal-correct change
  (2 lines in `cli/main.py` — import + `"deribit-options-chain"` dispatcher key; the `__init__.py` `__all__` step in his
  sketch was cosmetic — main.py imports handlers by full path — so skipped), added a regression test
  (`test_deribit_options_chain_operation_registered`), ran the full MTDS QG (green, sentinel written), shipped via
  quickmerge → **mtds@9ecd1e29e** on live-defi-rollout (Tier-C drain runs `quality-gates-v2` on the promote PR).
  **Remaining to actually capture:** the handler is LIVE/replay only (no backfill — `process()` = `date.today()`), so a
  live cron/VM must run `--operation deribit-options-chain` (Stage-5 [INFRA] item) before the Stage-3 re-measure shows
  real Deribit options coverage. Historical options not covered by this handler.
- **2026-07-06** — **D5 root cause CONFIRMED (Ikenna's C5, verified in our code).** DERIBIT `options_chain` captured=0/1
  because `DeribitOptionsChainHandler` (built — `cli/handlers/deribit_options_chain_handler.py`) is NEVER REGISTERED:
  absent from `handlers/__init__.py` `__all__` (line 9), no `cli/main.py` import, and NOT a key in the operations
  dispatcher (`cli/main.py` 533–582: `download`→…→`collect-onchain-perp-batch`, no `deribit-options-chain`). No
  operation invokes it → zero shards → captured=0. **Corrects the earlier "measurement-gated" framing** — a genuine
  CAPTURE GAP, not a re-measure artifact. Fix = Ikenna's 3-line handler registration (his MTDS workstream, in progress)
  → a `deribit-options-chain` backfill (added to Stage 5) → THEN the honest number shows in the Stage-3 re-measure. Not
  touched by me (Ikenna owns the MTDS fix).
- **2026-07-06** — **D5 confirmed NOT a standalone decision** (resolves via Stage-3 re-measure). Deribit
  `options_chain`: reconciliation §E.1 downgraded A18 to indeterminate-pending-remeasure; the
  `cefi_deribit_binance_futures_bundle_verification` GCS scan already found the pre-backfill "138 captured" were genuine
  PHANTOMS (zero options_chain/futures_chain blobs) → the honest number falls out of the Stage-3 re-measure post the
  06-28 backfill. MVP "don't widen beyond BTC/ETH options_chain" stance STANDS (Deribit OPTION = options_chain only).
  Mechanical residual (annotate the Layer-1 gap + gate spot-checks behind ">0 captured") folds into D2 /
  cefi_deribit_bundle. **All 5 decisions now closed** (D1–D3 decided · D4 resolved 07-03 · D5 measurement-gated); open
  external items = Ikenna's DERIBIT-COMBO reply + the KALSHI-PERP purge (slot-2) + credentials-gated captures.
- **2026-07-06** — **D4 found ALREADY RESOLVED** (not a new decision). The cefi_tick G4 "Layer-1 does not block G4"
  carve-out was superseded by **Ikenna's C4 decision 2026-07-03, option (a): G4 enforces Layer-1 AND Layer-2**
  (`mvp_backfill_cefi_tick_v10` § G4 — "verify honest-complete (BOTH layers)"). Same direction as the governing law; G4
  cannot close until D2 (`cefi_layer1_denominator_gaps`) lands. Corrected the stale PENDING → DECIDED (the
  reconciliation snapshot predated the 07-03 call). Next: D5 (Deribit options stance) likely resolves via the Stage-3
  re-measure per reconciliation §E.1 (A18 indeterminate until a live DERIBIT `options_chain` measure), not a standalone
  decision.
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
  79.55% — the honest direction. **✅ DERIBIT-COMBO future_combo RESOLVED (Ikenna 2026-07-06):** OPTION-only —
  `future_combo` is NOT in MVP (Deribit MVP = `options_chain` only), so `{OPTION}` is final (not just provisional) and
  `future_combo` stays out of the MVP denominator. Also reconcile the COINBASE (declared) vs `COINBASE_SPOT` (map
  constant) naming at impl. Sequenced AFTER C2 MVP-gate intersection (already decided); re-measure closes it (Stage 3).
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
