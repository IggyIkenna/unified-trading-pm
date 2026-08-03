---
doc_type: plan
title:
  Instruments Completion Tracker — Progress Log history (2026-07-06 tracker creation through the 2026-07-07 ASTER/CEFI
  data-status audit)
summary: >-
  Line-cap remediation extraction from plans/active/instruments_completion_tracker_2026_07_06.md's Progress Log — every
  2026-07-06/07-dated entry (the D1-D5 Decision Gate rulings, the 6-plan AO dispatch, TradFi v9 migration apply, the
  Layer-1 certifications for cefi/defi/prediction/tradfi, the turbo-API read-bug sweep, and the ASTER/CEFI data-status
  audit), moved verbatim so the live plan stays under the 1000-line hard cap. The live plan keeps its most recent
  entries (2026-07-28 gate-cleanup + checkbox-drift reconciliation, 2026-07-10 re-assessment dispatches) inline;
  everything below predates them.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [data, meta]
repos: [instruments-service, unified-api-contracts, market-tick-data-service, deployment-service, deployment-api]
scope: [engineer]
tags: [tracker, honest-coverage, denominator, numerator, instruments, history, line-cap-remediation]
related: [/plans/active/instruments_completion_tracker_2026_07_06.md]
created: 2026-08-03
last_updated: 2026-08-03
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: script
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  - "line-cap remediation split, 2026-08-03, per
    plans/active/issues/context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md"
---

# Instruments Completion Tracker — Progress Log history

Extracted verbatim from `plans/active/instruments_completion_tracker_2026_07_06.md`'s `## 📓 Progress Log` section on
2026-08-03, to bring the live plan back under the workspace's 1000-line hard cap
(`scripts/plan-hygiene/check_line_caps.sh`). No content changed — only relocated.

## Progress Log (historical entries, 2026-07-06/07)

- **2026-07-07 (later same day, round 3)** — **🔴 P0 filed: `defi_turbo_api_hides_real_captured_data_2026_07_07.md`.**
  Chasing an operator hypothesis that AAVE_V3-ARBITRUM/POLYGON/EULER_V2/FLUID's `0/0` turbo readings might be a
  venue-naming mismatch: no naming mismatch was found (the write path produces the exact canonical strings), but a live
  GCS manifest read found something worse — **AAVE_V3-ARBITRUM has 18,771 real captured rows and AAVE_V3-POLYGON has
  24,278, both current through 2026-06-21, under the exact canonical key**, yet the turbo API reports both as `0/0`.
  **SPARK has 7,405 real captured rows and doesn't appear in the turbo response at all.** This is a deployment-api
  read/aggregation bug, not a capture gap — real coverage is being silently understated. EULER_V2 (both chains) and
  FLUID-ARBITRUM/PLASMA, by contrast, are confirmed genuinely zero real data anywhere — those readings are accurate.
  Also found: EULER_V2's real, Goldsky-verified-working (2026-06-02) subgraph infra has never actually been polled — a
  "finish what's already built" case, folded into the existing RENZO-adjacent unregistered-handler-audit item above.
  Scope of the read-path bug beyond these 3 venues is unknown — flagged as a P1 follow-up in the new doc, not yet swept
  systematically.
- **2026-07-07 (later same day, round 4)** — **Full ~34-venue systematic sweep of the turbo-API read-bug's true scope.**
  Found 5 more confirmed "REAL DATA HIDDEN" venues (MANTLE/PUFFER/STADER/STAKEWISE/SWELL-ETHEREUM — each ~1
  row/manifest-entry, likely liveness markers rather than real volume, but the same dashboard bug either way) plus 4
  bonus finds needing a live turbo-API cross-check (HYPERLIQUID 3.77M rows, ASTER 1.07M rows, COMPOUND_V3 233K rows,
  FLUID-ETHEREUM 690 rows). Everything else checked (BEEFY ×6 chains, IDLE ×3, KARAK ×2, RENZO ×2,
  YEARN_V3-ARBITRUM/OPTIMISM, etc.) came back genuinely empty. Folded into
  `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md`.
- **2026-07-07 (writer fix implemented)** — Per operator go-ahead, ran a 3-agent pre-audit then implemented the
  CeFi/TradFi manifest writer fix in `instruments-service/instruments_service/engine/orchestrator/writers.py`
  (`_derive_instrument_type` → `_split_by_instrument_type`, one `record_captured()` call per distinct `instrument_type`
  instead of one blended call per venue×date). Confirmed this is ONE shared code path for CeFi AND TradFi (CME hits the
  identical bug live) and flagged 5 more likely-affected CeFi venues from registry evidence. Deleted the dead/broken
  `fix_manifest_venue_casing.py` one-off as a companion cleanup. Verified against today's real DERIBIT day-snapshot
  (2,965 rows → 5 correct groups: OPTION 2,586/COMBO 273/FUTURE 71/PERPETUAL 21/SPOT_PAIR 14). Quality gates green
  (153s). Shipped via quickmerge to `is@<pending sha>`. Full detail in
  `issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`.
- **2026-07-07 (later same day)** — **D6/combinator docs updated with the round-2 findings; nothing new filed.** (1) The
  CEFI chains-vs-venues rendering fix (Progress Log entry two above) is now implemented + tested in code — not yet
  committed. (2) Pulling the full real `chain → venue → instrument_type → data_type` tree for DeFi found the writer-side
  blank-`instrument_type` bug isn't Deribit-only: all 7 Solana DeFi venues (DRIFT, KAMINO, MARGINFI, MARINADE, ORCA,
  RAYDIUM, SOLEND) plus CURVE-OPTIMISM have real captured data but zero `instrument_types` breakdown — same root cause,
  wider scope. (3) HYPERLIQUID/ASTER's dual CEFI+DEFI listing (both `0/0` under DEFI) is operator-confirmed intentional
  — same hybrid on-chain-CLOB pattern as Lighter/Pacifica/Extended-Starknet, folded into that existing Stage-5 item
  above rather than filed as a new finding. (4) Added Aave's `debt_token` (declared, schema-ready, zero captured rows —
  the supply side `a_token` works, the borrow side doesn't) to the combinator doc's existing DeFi-drift finding. (5)
  **Still open**: a workflow is checking whether AAVE_V3-ARBITRUM/POLYGON, EULER_V2, and FLUID's `0/0` readings are
  genuinely never-captured or a canonical-venue-naming mismatch hiding real data under a different key — will update
  once it resolves. All changes landed in `issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`
  and `issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md`; no new docs this round.
- **2026-07-07** — **UAC data-type-validity combinator audit — 1 new issue doc filed, scoped by operator.** Follow-up to
  the D6 shard-dimension work: asked whether UAC is a consistent SSOT for "which data_types are valid for (venue,
  instrument_type)" across all 5 asset groups. 5-way parallel audit found: **no asset group has a real combinator** —
  CEFI has a flat venue map + an asset-group-wide (not venue-wide) instrument-shape matrix patched by 3
  independently-bolted-on venue overrides; DeFi has a real `(protocol, instrument_type)` object but it's drifted from
  its own "actually captured" registry; TradFi has 3 never-joined axes producing a **live, provably-wrong cell** (CME
  and ICE get an identical `futures_chain` data_type set despite ICE having no Databento coverage). **Operator scoped
  the fix to CEFI/DEFI/TRADFI only** — Sports has no tradeable-instrument concept at all (correct as-is, not a gap) and
  Prediction's instrument is always one shape by domain nature (also correct as-is); Prediction DOES have a separate,
  smaller, unrelated gap (its flat venue map under-declares real data types). Filed
  `issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md` with the CME/ICE fix flagged P1 as a
  live-wrong-answer item independent of whether the full combinator redesign is approved. No files edited beyond this
  doc + tracker pointers.
- **2026-07-07** — **ASTER/CEFI instrument-service data-status audit — 5 new issue docs filed + GAP 4 appended.**
  Operator-driven audit starting from the ASTER CEFI data-status dashboard, verified against live production APIs (not
  code-reading alone) and one real execution of `cefi_cumulative_drawdown_guard_2026_06_27.py` against prod GCS. Filed:
  (1) `issues/aster_mtds_failure_count_regression_2026_07_07.md` — 🔴 ASTER MTDS `attempted_failed` looks regressed from
  a documented 3,491 (06-22) back to 17,675 (live 07-07), near its original pre-05-14-fix total; unexplained, staleness
  ruled out. (2) `issues/cefi_monotonicity_guard_alerting_and_dark_venues_2026_07_07.md` — 🔴 LIGHTER and PACIFICA have
  had zero captured data of any status since 2026-06-26 (11 days), found only by actually running the manual guard
  script (its own stdout truncates to top-40 and hides its own `total_thin` counter of 1,007 catalogue-wide collapses);
  the monotonicity guard that DOES run daily has zero alerting wired anywhere. (3)
  `issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` — new Decision Gate **D6**:
  `instrument_type` is only a real breakdown dimension by coincidence today (works for ASTER because it has exactly one
  type; DERIBIT, which has 4, has zero `instrument_types` breakdown, and DERIBIT-COMBO is faked in as a 4th venue); the
  same MTDS-daily-axis-on-definitional-data mismatch was independently confirmed live for PREDICTION's
  `market_metadata`. (4) `issues/instruments_service_data_status_endpoint_dead_code_2026_07_07.md` — IS's own
  `GET /api/data-status` has zero real HTTP consumers. (5) `issues/manifest_reprocessing_generic_utility_2026_07_07.md`
  — 11 near-identical one-off reclassify scripts across 8 weeks, no generic mechanism. Also appended **GAP 4** to
  `issues/perp_funding_data_semantics_and_cadence_2026_06_16.md`: the GAP-2 genesis sweep to 2023-07-22 never touched
  `expected_start_dates.yaml`'s `trades` entry for ASTER, which still disagrees at 2021-08-30 — flagged as live-risk
  since that file drives completion-% calculations, and as a blocker on the file's own pending pre-funding-genesis
  trades backfill todo. Separately confirmed as NOT bugs from this audit: TradFi's non-trading-day handling (already
  correct), the `2023-07-22` ASTER genesis vs. `2021-08-30` trades floor being a deliberate GAP-2 split (not solely an
  oversight — see GAP 4 for the residual it missed), and the Sports "bookmaker vs. data-source-then-league" view
  difference (a `secondary_axis` selector, not a regression). Wired into Stage 2b/3/4/6 above + D6 + the urgent-findings
  banner; none of these are yet reflected in the cefi Layer-2 37.86 snapshot number.
- **2026-07-06** — **Reconciled certified snapshot published** (via `layer1_remeasure_and_certify_2026_07_06` task 006).
  Fresh-measured sports as part of the reconciliation (never re-measured in this plan cycle previously) — sports Layer-1
  30.77% (8/26; 18 missing all BETFAIR odds; 24 stray) unchanged vs stale; sports Layer-2 100.00% (38,182/38,182
  reachable; 0 attempted_failed; 0 expected_unattempted; total 41,520). Full 5-AG reconciliation table (Layer-1 +
  Layer-2 + provenance + handler-audit-reread flags) added to `layer1_remeasure_and_certify_2026_07_06.md` under
  task 006. **Handler-audit re-read flags:** 🟡 cefi only (Deribit `DeribitOptionsChainHandler` register `mts@015abaf5`
  will move cefi L2 on next capture); defi/sports/prediction 🟢 clean; tradfi 🚧 STALE-BLOCKED-PLAN2. 73 unregistered
  venues per WSFeedConnector audit (`wsfeedconnector_phase35_gap_2026_07_06`) are honest handler-not-built gaps, NOT
  C5-class re-read triggers. All 4/5 fresh certifications retain `denominator_status: INCOMPLETE` → Layer-2 % remains a
  LOWER BOUND per the two-layer governing law. Sports evidence: `/home/ubuntu/coverage_sports_20260706T153104Z.json`.
- **2026-07-06** — **prediction Layer-1 CERTIFIED — 66.67% fresh** (via `layer1_remeasure_and_certify_2026_07_06` task
  005). Ran `measure_honest_coverage.py --asset-group prediction` locally at 2026-07-06 15:27 UTC on `is@6716f55`
  post-KALSHI-PERP-purge; primary manifest `gs://market-data-tick-pred-prd-central-element-323112` blob.updated
  2026-07-06T15:26:46Z, 760,300 rows; merged 706,197 rows. Result: **expected_tuples 6 / present_tuples 4 / missing 2 /
  stray 17 → 66.67%.** Direction ✓ — 66.67 stale (06-29) → 66.67 fresh; denominator stable at 6 (purge affected cefi
  catalogue, not prediction). **Purge Gate verified:** 0 `KALSHI-PERP` mentions + 0 `POLYMARKET-PERP` mentions in the
  prediction coverage.json (post-purge cefi state: catalogue 376,984→351,511 rows, KALSHI-PERP==0, 25→24 venues per
  `prediction_capture_incident_remediation_2026_07_06` Workstream B Phase 0). Layer-2 prediction rollup: coverage_pct
  **22.73%** (captured 8,711 / reachable 38,318; empty_confirmed 667,879; attempted_failed 29,110; expected_unattempted
  497; total 706,197; layer1_completeness_pct 66.67; denominator_status INCOMPLETE — 2 unwired MARKET_LIFECYCLE handlers
  so Layer-2 stays a lower bound, up +2.17 pp vs 20.56 stale). 2 missing tuples both MARKET_LIFECYCLE (KALSHI +
  POLYMARKET prediction_market) — unwired handlers not adapter contamination. **Task 001 (multi-AG re-run) PREREQs both
  now DONE** (KALSHI-PERP purge ✓ + Plan 5 unregistered-handler audit ✓ per
  `foundation_gates_and_capture_to_100_2026_07_06` line 77 `- [x]`) — task 001 will re-dispatch as its own
  /boot-per-shippable-unit. Snapshot updated above; evidence artefact (local):
  `/home/ubuntu/coverage_prediction_20260706T152707Z.json`.
- **2026-07-06** — **task 004 tradfi Layer-1 DOCUMENTED as BLOCKED-PLAN2** (via
  `layer1_remeasure_and_certify_2026_07_06` task 004). Main-agent answer to `BLK-ab86f4e9` confirmed: do NOT certify
  tradfi Layer-1 now — the tradfi IS catalogue rebuild + manifest rebuild + E7 CF verify from Plan 2
  (`tradfi_v9_stage1_finish_2026_07_06`) tasks 2-11 have NOT landed (only Plan 2 task 1 done). Running
  measure_honest_coverage --asset-group tradfi against the pre-v9 catalogue produces a certification that would
  re-measure again. Task 004 checkbox annotated 🚧 BLOCKED-PLAN2; tradfi Snapshot entry unchanged at 51.43 [06-29
  stale]. Re-dispatch after Plan 2 rebuilds land. Also noted: dispatcher's `gate_on_depends: true` needs review —
  per-plan-task granularity is not enforced (task 004 was dispatched despite Plan 2 not being done).
- **2026-07-06** — **defi Layer-1 CERTIFIED — 94.81% fresh** (via `layer1_remeasure_and_certify_2026_07_06` task 003).
  Ran `measure_honest_coverage.py --asset-group defi` locally at 2026-07-06 15:13 UTC on `is@681f50a` (post-D1 +1.38M
  seeding); primary manifest `gs://market-data-tick-defi-prd-central-element-323112` blob.updated 2026-07-06T15:11:42Z,
  13,515,019 rows; merged 10,828,935 rows. Result: **expected_tuples 77 / present_tuples 73 / missing 4 / stray 128 →
  94.81%.** Honest direction ✓ — 69.44 stale (06-29) → 94.81 fresh; denominator SHRANK 108→77 (-31 tuples) driven by
  `is@3bb7acd` (defi lending grain roll-up folds `a_token`/`debt_token`/`liquidation` → `lending` in Layer-1 canon,
  2026-07-03) — legitimate schema tightening, NOT a wrong-direction shrink. **D1 seeding VERIFIED in Layer-2:**
  `by_asset_group.defi.expected_unattempted = 1,534,304` — the +1,380,376-row apply landed in the reachable denominator.
  Layer-2 defi rollup: coverage_pct **62.06%** (captured 2,857,320 / reachable 4,603,799; empty_confirmed 6,225,136;
  attempted_failed 212,175; total 10,828,935; layer1_completeness_pct 94.81; denominator_status INCOMPLETE — 4 tuples
  still missing so Layer-2 stays a lower bound but tightened +4.51 pp vs 57.55 stale). 4 missing tuples all one venue
  (EIGENLAYER-ETHEREUM spot_asset {eigenlayer_rewards, oracle_prices, rewards, staking_yields}) — indicates one unwired
  handler/venue not four independent gaps. Task 001 (multi-AG re-run) NOT flipped by this task — its cross-plan PREREQs
  (KALSHI-PERP purge · Plan 5 unregistered-handler audit) primarily affect cefi/prediction Layer-2, not defi Layer-1.
  Snapshot updated above; evidence artefact (local): `/home/ubuntu/coverage_defi_20260706T151304Z.json`.
- **2026-07-06** — **cefi Layer-1 CERTIFIED — 73.61% fresh** (via `layer1_remeasure_and_certify_2026_07_06` task 002).
  Ran `measure_honest_coverage.py --asset-group cefi` locally at 2026-07-06 15:01 UTC on `is@03cfd0f` (post-D2a);
  primary manifest `gs://market-data-tick-cefi-prd-central-element-323112` blob.updated 2026-07-06T14:55Z, merged
  11,125,247 rows. Result: **expected_tuples 72 / present_tuples 53 / missing 19 / stray 87 → 73.61%.** Honest direction
  ✓ — 79.55 stale → 73.61 fresh; denominator grew 44→72 (+28 tuples) matching D2a's `INSTRUMENT_TYPES_BY_VENUE`
  completion. Layer-2 rollup context: cefi coverage_pct 33.28% (captured 2,891,774 / reachable 8,689,530; total
  11,125,247; denominator_status INCOMPLETE — 19 tuples still missing so Layer-2 stays a lower bound). Task 001
  (multi-AG re-run) NOT flipped by this task — its cross-plan PREREQs (KALSHI-PERP purge · Plan 5 unregistered-handler
  audit) primarily affect Layer-2 correctness, so a single-AG cefi run satisfies task 002's Gate independently. Other AG
  Layer-1 tasks (003 defi · 004 tradfi · 005 pred) remain queued and gated on their respective plans. Snapshot updated
  above; evidence artefact (local): `/home/ubuntu/coverage_cefi_20260706T150020Z.json`.
- **2026-07-06** — **AO tiering revised (operator): Plan 1 Opus/max, Plans 2-6 Sonnet/high.** Initial dispatch tagged
  all 6 Opus/max; operator dialed back after the per-plan reasoning — only **Plan 1** (the C2 `_row_data_types`
  instrument-type/bundle-aware fix that defeated two prior attempts + the denominator correctness) clearly needs Opus.
  Plans **2** (tradfi, proven tooling), **3** (catalogue ops), **4** (measure+certify, guarded), **5** (foundation
  reconcile + pattern-following handler), **6** (infra ops) run **Sonnet/high** with the smoke-first guards +
  main/review agents as backstop. Turns on the AO-vocabulary facts: **no `xhigh`; `max` requires Opus** (Sonnet+`max`
  HARD-STOPs the worker self-check), so Sonnet's valid ceiling is `high`. Frontmatter flipped on P2-6
  (`model_tier: sonnet-doable` + `thinking_tier: high`); P1 unchanged. **P5 is the bump-to-Opus candidate** (new
  `risk_params` handler + defi-oracle design) if a margin is wanted.
- **2026-07-06** — **Stages 1-6 DISPATCHED TO AO as 6 role-homogeneous plans (tiered — see the entry above).** Carved
  the tracker's remaining engineering into 6 AO plans (`assigned_vm: planning`, `execution_scope: orchestrator-agent`):
  P1 cefi denominator (`cefi_layer1_denominator_gaps`, assigned in-place — D2a/D2b marked done, 2a/2c/2f folded in)
  `pm@5bff1354c`; P2 tradfi Stage-1 finish (`tradfi_v9_stage1_finish`) `pm@f8bb8aa5f`; P3 IS-catalogue B0→B1→B2
  (`is_catalogue_completion_2d`) + P4 Layer-1 re-measure/certify (`layer1_remeasure_and_certify`, `gate_on_depends`
  Plans 1-3) `pm@64a1c00f8`; P5 foundation+capture (`foundation_gates_and_capture_to_100`, handler-audit ungated so it
  can precede P4) + P6 infra capture/devops (`infra_capture_and_devops_leftovers`, infra role) `pm@3dc6fcf04`. Contract
  verified against `agent-orchestrator/server/regen_backlog_from_plan.py`: model/effort is **per-plan** (frontmatter or
  role file), AO has **no `xhigh`** (max is the ceiling; `data_engineering` role default = the rejected sonnet/high, so
  the explicit opus-required+max override is load-bearing); `BLOCKED-*` lines auto-skip dispatch (operator-visible);
  `gate_on_depends` machine-holds P4 until P1-3 done. Hard-stops (bucket deletes, locked-plan archival, COINBASE
  `MVP_SCOPE`, CLOB classification, paid-RPC creds) stay off AO as `BLOCKED-*` lines the agents raise. UI drill-down (1
  P2 item) left off AO — too small for a standalone plan.
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
</content>
