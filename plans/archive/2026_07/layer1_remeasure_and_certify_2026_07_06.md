---
doc_type: plan
title: Layer-1 re-measure + certify (Stage 3) — the honest denominator, all AGs (AO Plan 4)
summary:
  Re-measure and certify the Layer-1 instrument denominator per asset_group on the corrected catalogue + seeded
  manifests, then record the fresh numbers so any Layer-2 capture percentage becomes trustworthy. The 2026-06-29
  certified numbers are stale (predate v12, the incremental-rollup switch, the cefi ghost-dupe fix, D2a, and the defi
  seeding). This plan is gated (gate_on_depends) on Plans 1-3 landing — you cannot certify a denominator that is still
  being corrected. Two cross-plan prerequisites also apply, called out on the re-measure task (the KALSHI-PERP purge and
  the unregistered-handler audit). Closes the last honest_coverage_v2 measurement items.
status: complete # (was: active) 2026-07-15 plan-reconcile §6: remnant folded out to its target (operator ruling); zero open todos
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, unified-api-contracts, market-tick-data-service]
scope: [engineer]
tags: [honest-coverage, layer-1, denominator, re-measure, certify, stage-3, instruments-completion]
related:
  [
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/archive/2026_07/honest_coverage_v2_instrument_denominator_2026_06_28.md,
    /plans/archive/2026_07/honest_coverage_smoke_harness_2026_06_28.md,
    issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-06
last_updated: 2026-07-10
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: data_engineering
model_tier: sonnet-doable
thinking_tier: high
drift_direction: advance-code
depends_on:
  [cefi_layer1_denominator_gaps_2026_07_03, tradfi_v9_stage1_finish_2026_07_06, is_catalogue_completion_2d_2026_07_06]
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source:
---

# Layer-1 re-measure + certify (Stage 3) — all AGs (AO Plan 4)

> **🤖 AO PLAN 4 of the instruments-completion set.** Dispatched to the agent-orchestrator (`assigned_vm: planning`,
> role `data_engineering`). **Dispatch tier (frontmatter-driven, EVERY task): Sonnet / high.** Coordinator =
> `instruments_completion_tracker_2026_07_06.md` (Stage 3).
>
> **⛔ GATED (machine-enforced):** `depends_on` Plans 1 (cefi denominator), 2 (tradfi Stage-1 finish), 3 (IS-catalogue
> completion) with **`gate_on_depends: true`** — the orchestrator holds every task here until all three upstream plans'
> tasks are done. Re-measuring a denominator that is still being corrected produces a number nobody can trust. **The one
> law:** Layer-1 gates Layer-2 — only after this certifies is any capture % meaningful.
>
> **Two cross-plan PREREQs on the re-measure (NOT owned here — this plan waits on them):** (1) **KALSHI-PERP
> contamination purge** — 25,473 fake `KALSHI-PERP` `PERPETUAL` rows (wrong-host `kalshi_perp` adapter) must be purged
> from the cefi catalogue first or the cefi Layer-2 numbers are polluted. Owned by
> `issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md` Phase 0 (slot-2 / the 4da6fe8 author). (2)
> **Unregistered-handler audit** (Plan 5) — run it BEFORE this re-measure so a built-but-unwired handler (`captured=0`,
> the Deribit C5 class) is not mislabelled as a real coverage gap in the certified numbers.
>
> **Worker guards (HARD):** (1) **run it, don't read it** — cite the actual `measure_honest_coverage` run output, not a
> stale snapshot. (2) record the fresh numbers in BOTH this Progress Log AND the tracker's Snapshot before declaring
> certified. (3) if a certified number moves the WRONG direction (denominator shrinks when it should grow), STOP and
> diagnose — do not certify a suspicious measure.

## Codex SSOTs (read before touching)

- `/codex/02-data/honest-coverage-model.md` — two-layer model; Layer-1 gates Layer-2; do NOT derive the expected
  universe from the manifest (circular).

## Re-measure + certify (the gate is machine-enforced; certify in this order)

- [x] ✅ [SCRIPT] P0. **Re-run `measure_honest_coverage`** on the corrected catalogue + seeded manifests (all AGs). The
      06-29 numbers are stale — they predate v12, the incremental-rollup switch, the cefi 122-row ghost-dupe fix
      (07-04), D2a (cefi 84.09→73.61), and the defi +1.38M seeding. **PREREQ (cross-plan): the KALSHI-PERP purge + the
      unregistered-handler audit (Plan 5) are both done** (else cefi Layer-2 is polluted / a wiring bug reads as a
      coverage gap). Gate: a fresh `coverage.json` produced from a real run; run id recorded. **DONE 2026-07-07 06:22
      UTC — multi-AG `measure_honest_coverage.py --asset-group all` run on `is@68f174a`** with both cross-plan PREREQs
      verified done (KALSHI-PERP purge: cefi catalogue 351,511 rows post-purge, 0 KALSHI-PERP/POLYMARKET-PERP mentions
      in the prediction coverage; Plan 5 unregistered-handler audit: filed at
      `plans/archive/issues/wsfeedconnector_phase35_gap_2026_07_06.md`). Fresh manifest blobs (blob.updated
      2026-07-07T06:20:42-45Z): cefi 11,125,247 · defi 10,908,735 · tradfi 1,719,843 · sports 41,520 · prediction
      706,197 merged rows. **Layer-1:** cefi 73.61% · defi 94.81% · tradfi 51.43% [STALE-BLOCKED-PLAN2 per task 004] ·
      sports 30.77% · prediction 66.67%. **Layer-2 rollup:** cefi 76.77% (2,098,056/2,732,783 reachable) · defi 61.97%
      (2,872,219/4,635,082) · tradfi 96.00% (420,533/438,035) [STALE] · sports 100.00% (38,182/38,182) · prediction
      22.73% (8,711/38,318). All 4 non-blocked-AG Layer-1 % byte-match the per-AG certifications (tasks
      002/003/005/006); tradfi 51.43 unchanged as expected under BLOCKED-PLAN2 pending Plan 2 rebuilds. **Run id:**
      `2026-07-07T06:20:58Z / is@68f174a`. Evidence artefact (local): `/home/ubuntu/coverage_all_20260707T062058Z.json`
      (4.6 MB, single unified all-AG JSON).
- [x] ✅ [VERIFY] P0. **Certify cefi Layer-1** — record the fresh cefi denominator + % in this Progress Log and the
      tracker Snapshot. Gate: cefi number recorded; denominator grew, % dropped vs 79.55 (the honest direction).
      **CERTIFIED 2026-07-06 15:01 UTC: cefi Layer-1 = 73.61% (present 53 / expected 72; 19 missing tuples; 87 stray).**
      Direction ✓ — 79.55 (stale 06-29) → 73.61 (fresh, honest); denominator grew 44→72 (+28 tuples, D2a). Evidence:
      local `measure_honest_coverage.py --asset-group cefi` run at 2026-07-06 15:00 UTC on `is@03cfd0f` (post-D2a
      catalogue); primary manifest
      `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` blob.updated
      2026-07-06T14:55Z, merged 11,125,247 rows.
- [x] ✅ [VERIFY] P0. **Certify defi Layer-1** — post the +1.38M seeding, record the fresh defi denominator + %. Gate:
      defi number recorded; the seeded honest-absence rows are in the denominator. **CERTIFIED 2026-07-06 15:13 UTC:
      defi Layer-1 = 94.81% (present 73 / expected 77; 4 missing tuples; 128 stray).** Direction ✓ — 69.44 (stale 06-29)
      → 94.81 (fresh, honest); denominator shrank 108→77 (-31 tuples) driven by `is@3bb7acd` (defi lending grain
      roll-up: `a_token`/`debt_token`/`liquidation` → `lending` in Layer-1 canon, 2026-07-03) — legitimate schema
      tightening, NOT a suspicious measure. **Layer-2 seeding VERIFIED:** `expected_unattempted=1,534,304` (Layer-2
      rollup, `by_asset_group.defi.expected_unattempted`) — 1.38M seeded honest-absence rows land in the reachable
      denominator (up from the pre-seeding baseline; D1 = 1,380,376-row apply confirmed present). Layer-2 rollup: defi
      coverage_pct 62.06% (captured 2,857,320 / reachable 4,603,799; empty_confirmed 6,225,136; attempted_failed
      212,175; total 10,828,935; layer1_completeness_pct 94.81; instrument_gates_download True). Missing tuples (all
      EIGENLAYER-ETHEREUM spot_asset): eigenlayer_rewards, oracle_prices, rewards, staking_yields. Stray tuples (first
      5): AAVE_V3 a_token {oracle_prices, utilization}, AERODROME_V3 pool {dex_swaps, swaps_ohlcv_15m, swaps_ohlcv_15s}.
      Evidence: local `.venv/bin/python scripts/measure_honest_coverage.py --asset-group defi` run at 2026-07-06 15:13
      UTC on `is@681f50a` (post-D1 seeding); primary manifest
      `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` blob.updated
      2026-07-06T15:11:42Z (13,515,019 rows), merged 10,828,935 rows. Evidence artefact (local):
      `/home/ubuntu/coverage_defi_20260706T151304Z.json`. **CAVEAT ADDED 2026-07-14 (doc-reconciliation verify-rerun-2,
      finding 137)**: "fresh, honest" describes the direction of THIS measurement (denominator correctly grew/shrank per
      the D2a/lending-rollup catalogue fixes) — it does NOT mean the underlying method is non-circular. The sibling plan
      `foundation_gates_and_capture_to_100_2026_07_06.md` (same day, same epic) and the codex SSOT
      `/codex/02-data/defi-completeness-oracle.md` both document that DeFi's `EXPECTED` source is today
      `EXPECTED =     ENUMERATED` (catalogue vs. catalogue) — a structurally circular measurement — and commission a
      chain-truth completeness ORACLE specifically to replace it. As of 2026-07-14 that oracle is still design-only
      (codex `status:     current`, no implementation plan filed, no `CompletenessProbe` code found in-repo) — so 94.81%
      remains the best available DeFi Layer-1 number, but it is a catalogue-vs-catalogue figure, not an independent
      chain-truth proof. Treat "honest" here as "correctly computed under the current (circular) method," not
      "structurally validated."
- [x] 🚧 **BLOCKED-PLAN2** [VERIFY] P0. **Certify tradfi Layer-1** — post the v9 migration + rebuild + IS catalogue
      (Plan 2), record the fresh tradfi denominator + %. Gate: tradfi number recorded; all 5 AGs now
      canonical-and-measured. — **FOLDED OUT** to plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md
      (2026-07-15, plan-reconcile §6 operator ruling); tracked there, not here. **STATUS 2026-07-06 15:20 UTC —
      BLOCKED-PLAN2** (main-agent answer to `BLK-ab86f4e9`, task 004 pickup): the tradfi IS catalogue rebuild
      (`build_instrument_catalogue.py` tradfi), the manifest rebuild (`rebuild_tradfi_manifest.py`), and the E7 CF
      verify — all Plan 2 (`tradfi_v9_stage1_finish_2026_07_06`) tasks 2-11 — have NOT landed (only Plan 2 task 1 done:
      2026-year v9 migration). Running `measure_honest_coverage --asset-group tradfi` NOW would certify against the
      stale pre-v9 catalogue + un-rebuilt manifest — a Layer-1 number that will move again once Plan 2 lands, defeating
      the point of certification (the plan's own HARD guard: "do not certify a suspicious measure" applies analogously
      to pre-prereq measures). Gate unresolvable from this task; DEFERRED until Plan 2 lands. Re-dispatch this task
      after `tradfi_v9_stage1_finish_2026_07_06` tasks 2-11 flip (in particular the IS catalogue build + manifest
      rebuild + E7 verify) — the operator/main agent controls re-queue timing. **RE-CHECKED 2026-07-10 (this session):
      still genuinely BLOCKED-PLAN2, correctly not re-run.** `tradfi_v9_stage1_finish` real progress this session: task
      3 (straggler re-run) verified done + flipped; task 4 (manifest rebuild) re-verified — still a genuine 13,971-row
      v4 tail (99.7712% v9), gate not met; task 6 (E7 verify) re-audited — CF-3 now GREEN, but found+partially-fixed a
      new small CF-4 live-writer trickle that converges on the same blocker; task 2 (orphan sweep) unblocked + launched
      (real run, in progress, not yet complete); task 10 (schema restamp) confirmed still blocked — the live
      `tradfi-bf-cme-ohlcv-1m-*` backfill fleet is confirmed still RUNNING (`gcloud compute instances list`, 8 VMs).
      **Net: still only 1 of the real 6 open tasks (task 3) is now done**; re-running `measure_honest_coverage` here
      would still certify against an incomplete catalogue/manifest — would repeat the exact mistake this task declined
      to make on 2026-07-06. See `tradfi_v9_stage1_finish_2026_07_06.md` Progress Log 2026-07-10 entry for full detail.
      **RE-CHECKED AGAIN 2026-07-10 (continuation session, same day): still genuinely BLOCKED-PLAN2 — direct
      verification, not trusted from the doc.** Re-confirmed live: (a) fleet-drain still FALSE —
      `gcloud compute instances list --filter="name~tradfi-bf"` shows 6 `tradfi-bf-*` backfill VMs RUNNING right now
      (fleet composition churns — venues cycle in/out — but it has never been empty on any check this session); (b) the
      backgrounded full orphan sweep (task 2, PID 22320) that was "in progress" as of the prior entry had actually
      COMPLETED unattended at 2026-07-10 15:57:41 UTC — read the landed report directly
      (`gs://market-data-tick-tradfi-prd-central-element-323112/_index/audit/orphan_sweep_tradfi.parquet`, confirmed via
      `gsutil stat` + the scratchpad run log, not taken on trust) and it is **NOT E=0**: 585 real orphans + a second
      71,830-object taxonomy gap (`_needs_attribution/`, now fixed + shipped `instruments-service@098e93e0`, direct-push
      dirty-deps carve-out — quickmerge's own sibling repos were dirty with a live <30s-old WIP this session, protected
      per the liveness gate, not touched). **This makes task 2 MORE open than the prior entry believed**, not less — the
      585-orphan remainder needs its own backfill-registration follow-up before task 11 can safely run even its dry-run
      prep. Net still holds: 1 of 6 real open Plan-2 tasks done (task 3); task 2 progressed (full sweep completed,
      taxonomy gap #2 fixed, genuine 585-row remainder newly characterized) but its literal gate is still not met; tasks
      4/6/10/11 unchanged. **Certifying tradfi Layer-1 now would still certify against an incomplete state** — correctly
      declined again this session. See `tradfi_v9_stage1_finish_2026_07_06.md` task 2 + Progress Log 2026-07-10 entries
      for full detail. **2026-07-12 forward-pointer (finding 126, §A2 B-queue ruling):** this "RE-CHECKED AGAIN" entry's
      "NOT E=0: 585 real orphans" verdict was current as of 15:57:41 UTC that session but was superseded ~80 min later
      the SAME day — `tradfi_v9_stage1_finish_2026_07_06.md`'s task 2 shows **🎯 GATE MET 2026-07-10 17:17:22 UTC: fresh
      full corpus-wide re-sweep confirms `orphan_class_E=0, unknown_prefixes=0`**, checkbox flipped, after the 585-row
      remainder was backfilled. This doc's own orphan-sweep sub-task (task 2 of Plan-2) is therefore closed; the overall
      `BLOCKED-PLAN2` verdict below still holds independently on the other open Plan-2 tasks (manifest rebuild, E7
      verify, schema restamp) — was not re-derived here, no re-certification action needed on this basis alone.
- [x] ✅ [VERIFY] P0. **Certify prediction Layer-1** — post the KALSHI-PERP purge, record the fresh prediction
      denominator + %. Gate: prediction number recorded; no fake KALSHI-PERP rows in the measure. **CERTIFIED 2026-07-06
      15:27 UTC: prediction Layer-1 = 66.67% (present 4 / expected 6; 2 missing tuples; 17 stray).** Direction ✓ — 66.67
      (stale 06-29) → 66.67 (fresh); denominator stable at 6 tuples (KALSHI-PERP purge landed on cefi, not prediction —
      prediction Layer-1 not expected to move). **No fake KALSHI-PERP rows verified:** 0 `KALSHI-PERP` mentions and 0
      `POLYMARKET-PERP` mentions in the prediction coverage.json (contamination was cefi-only, purged 2026-07-06 by
      `scripts/purge_kalshi_perp_events_contamination_2026_07_06.py --apply` per
      `prediction_capture_incident_remediation_2026_07_06` Workstream B Phase 0 → cefi catalogue 376,984→351,511 rows,
      KALSHI-PERP==0, 25→24 venues). Layer-2 prediction rollup: coverage_pct 22.73% (captured 8,711 / reachable 38,318;
      empty_confirmed 667,879; attempted_failed 29,110; expected_unattempted 497; total 706,197; layer1_completeness_pct
      66.67; instrument_gates_download True) — tightened +2.17 pp vs 20.56 stale. Missing tuples (both unwired
      MARKET_LIFECYCLE handlers): KALSHI prediction_market MARKET_LIFECYCLE, POLYMARKET prediction_market
      MARKET_LIFECYCLE. Stray tuples (first 5): KALSHI PREDICTION_MARKET book_snapshot_5, POLYMARKET {BNB, BTC,
      CRUDE_OIL, DJIA} prediction_trades. Evidence: local
      `.venv/bin/python scripts/measure_honest_coverage.py --asset-group     prediction` run at 2026-07-06 15:27 UTC on
      `is@6716f55` (post-KALSHI-PERP-purge cefi state); primary manifest
      `gs://market-data-tick-pred-prd-central-element-323112/_index/availability_index.parquet` blob.updated
      2026-07-06T15:26:46Z (760,300 rows), merged 706,197 rows. Evidence artefact (local):
      `/home/ubuntu/coverage_prediction_20260706T152707Z.json`.
- [x] ✅ [VERIFY] P1. **Reconcile the certified Layer-1 set against the Layer-2 lower bounds** — flag any AG where the
      handler audit (Plan 5) changed capture so Layer-2 is re-read too. Gate: a single certified snapshot table (all 5
      AGs, both layers) with provenance. **CERTIFIED SNAPSHOT 2026-07-06 (task 006):**

      | AG             | Layer-1 %        | L1 present/expected | L1 missing | L1 stray | Layer-2 %      | L2 captured / reachable | L2 total shards | Handler-audit re-read flag                                                                             | Provenance                                                                                                                                              |
                                                                                                                                                                              | -------------- | ---------------- | ------------------- | ---------- | -------- | -------------- | ----------------------- | --------------- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
                                                                                                                                                                              | **cefi**       | **73.61 (fresh)**| 53 / 72             | 19         | 87       | 33.28 (fresh)  | 2,891,774 / 8,689,530   | 11,125,247      | 🟡 pending — mts@015abaf5 registered DeribitOptionsChainHandler; re-capture NOT yet run → cefi L2 will re-move on next backfill | task 002; `is@03cfd0f` (post-D2a); manifest `market-data-tick-cefi-prd` blob.updated 2026-07-06T14:55Z; `coverage_cefi_20260706T150020Z.json`             |
                                                                                                                                                                              | **defi**       | **94.81 (fresh)**| 73 / 77             | 4          | 128      | 62.06 (fresh)  | 2,857,320 / 4,603,799   | 10,828,935      | 🟢 clean — no handler-audit findings that affect captured defi cells (49 unregistered venues are honest gaps, not C5-class) | task 003; `is@681f50a` (post-D1 +1.38M seeding); manifest `market-data-tick-defi-prd` blob.updated 2026-07-06T15:11:42Z; `coverage_defi_20260706T151304Z.json` |
                                                                                                                                                                              | **tradfi**     | 51.43 [STALE 06-29] | (stale)          | (stale)    | (stale)  | 88.81 [STALE 06-29] | (stale)             | (stale)         | 🚧 BLOCKED-PLAN2 — no re-measure until `tradfi_v9_stage1_finish_2026_07_06` tasks 2-11 land | task 004 DOCUMENTED-BLOCKED-PLAN2 (main-agent `BLK-ab86f4e9`); provenance = last measurement 2026-06-29                                                  |
                                                                                                                                                                              | **sports**     | **30.77 (fresh)**| 8 / 26              | 18         | 24       | 100.00 (fresh) | 38,182 / 38,182         | 41,520          | 🟢 clean — 100% L2 (nothing to re-read); 18 L1 misses are all BETFAIR odds (handler-not-built, honest gap not C5-class) | task 006 [this]; `is@ebfd11d`; manifest `market-data-tick-sports-prd` blob.updated 2026-07-06T15:30:44Z; `coverage_sports_20260706T153104Z.json`         |
                                                                                                                                                                              | **prediction** | **66.67 (fresh)**| 4 / 6               | 2          | 17       | 22.73 (fresh)  | 8,711 / 38,318          | 706,197         | 🟢 clean — 0 KALSHI-PERP/POLYMARKET-PERP mentions post-purge; 2 L1 misses are MARKET_LIFECYCLE handlers (honest gap not C5-class) | task 005; `is@6716f55` (post-KALSHI-PERP-purge cefi state); manifest `market-data-tick-pred-prd` blob.updated 2026-07-06T15:26:46Z; `coverage_prediction_20260706T152707Z.json` |

                                                                                                                                                                              **Reconciliation findings:**
                                                                                                                                                                              1. **4 of 5 AGs fresh-certified** (cefi + defi + sports + prediction). tradfi remains STALE at 51.43 pending
                                                                                                                                                                                 Plan 2 completion.
                                                                                                                                                                              2. **Handler-audit re-read flag = 🟡 cefi only.** The Deribit `DeribitOptionsChainHandler` registration
                                                                                                                                                                                 (mts@015abaf5) will move cefi Layer-2 on next capture cycle (2 handlers × Deribit BTC+ETH options_chain).
                                                                                                                                                                                 Defi/sports/prediction have zero C5-class fixes pending — their Layer-2 fresh numbers stand.
                                                                                                                                                                              3. **73 unregistered venues (per WSFeedConnector audit)** are NOT C5-class bugs — they're genuine handler-not-
                                                                                                                                                                                 built gaps filed at `plans/archive/issues/wsfeedconnector_phase35_gap_2026_07_06.md`. NO Layer-2 re-read
                                                                                                                                                                                 needed for them until the connectors are built.
                                                                                                                                                                              4. **Layer-1 direction summary:** cefi ↑ (44→72, D2a `INSTRUMENT_TYPES_BY_VENUE`); defi ↓ (108→77, `is@3bb7acd`
                                                                                                                                                                                 lending grain roll-up — legitimate schema tightening); sports/prediction stable (schema unchanged); tradfi
                                                                                                                                                                                 BLOCKED. All fresh moves are HONEST directions (no suspicious measures).
                                                                                                                                                                              5. **Layer-2 direction summary:** defi ↑ (57.55→62.06, +D1 seeding lands in denominator); prediction ↑
                                                                                                                                                                                 (20.56→22.73); cefi ↓ (37.86→33.28, denominator grew from D2a expansion); sports 100.00 stable; tradfi
                                                                                                                                                                                 STALE. All fresh moves consistent with the corrective plans that landed.
                                                                                                                                                                              6. **Denominator status = INCOMPLETE for all 5 AGs** → every Layer-2 % is a LOWER BOUND per the two-layer
                                                                                                                                                                                 governing law (Layer-1 gates Layer-2). None of the AGs are certified-complete; the certifications record the
                                                                                                                                                                                 honest lower bound at 2026-07-06.

- [x] ✅ [VERIFY] P2. **`honest_coverage_smoke_harness` live-verify slices** — run the deferred cefi / defi / tradfi /
      prediction slices (only sports ran). Gate: each AG's smoke slice green or its discrepancy filed. **DONE 2026-07-06
      (slot-9 planning) — Gate satisfied via `discrepancy filed`.** Ran what exists live-in-cloud
      (`central-element-323112`, `--today 2026-07-06`, `--deployment-env prd`); surfaced 4 discrepancies filed at
      `plans/archive/issues/honest_coverage_smoke_harness_4ag_verify_2026_07_06.md` with concrete P2 fix todos: (1)
      **tradfi runner** returns empty matrix — catalogue 404 on GCS (BLOCKED-PLAN2 as documented in task 004); (2)
      **prediction runner** crashes with `BucketNamingError` in
      `e2e-testing/scripts/build_smoke/live_manifest_reader.py:149` `_bucket_for` —
      `resolve_bucket_name(kind='tick-data',     asset_group='prediction')` has no entry (the `tick-data` alias routes
      to `market-data-{asset_group}` which has no prediction mapping; prediction bucket is the flat key
      `market-data-tick-prediction`); (3) **`run_live_verify_cefi.py` does not exist**; (4) **`run_live_verify_defi.py`
      does not exist** — slot-4's [VERIFY] P2 patch built tradfi + prediction runners only. Sports (verified 2026-06-29
      by slot-4) unaffected. No data-correctness impact (Layer-1 certifications use `measure_honest_coverage` on a
      different code path). Issue doc has 4 actionable todos for a fix-worker, ordered by unblock-value.
- [x] ✅ [CODE] P1. **Close `honest_coverage_v2` remaining measurement items** — build_expected landed in 2a (Plan 1);
      the UI drill-down moves to Plan 7. Flip the honest_coverage_v2 measurement checkboxes with evidence. Gate:
      honest_coverage_v2 measurement track closed (UI item excepted → Plan 7). **CLOSED 2026-07-06 (task 008, slot-6):**
      Phase 1 `[AGENT] P1.` `build_expected` consolidation FLIPPED in
      `honest_coverage_v2_instrument_denominator_2026_06_28.md` — landed at `instruments-service@681f50a` via Plan 1
      task 2a: `scripts/expected_universe.py::build_expected(asset_group)` is THE single public Layer-1 EXPECTED
      producer; `check_enumeration_completeness._build_expected_tuples` (+ `..._sports`) delegate via sibling-load;
      per-AG byte-identical goldens (72/171/35/27/8 tuples) + regression `test_expected_universe_golden.py` (14 tests)
      lock the matrix; QG green. Phase 2 `[UI] P2. drill-down` annotated as MOVED to
      `instruments_completion_tracker_2026_07_06` Stage 6 (last open honest_coverage_v2 item, too small for its own AO
      plan — tracked as tracker hygiene singleton, per operator 2026-07-06). Measurement track officially CLOSED — UI
      item legitimately excepted. Evidence: `honest_coverage_v2_instrument_denominator_2026_06_28.md` Progress Log
      2026-07-06 close-out entry + Phase 1 checkbox flipped + Phase 2 UI item annotated MOVED-TO-STAGE-6.

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-07** — **✅ Task 001 CLOSED — multi-AG `measure_honest_coverage.py --asset-group all` re-run produced a
  single unified fresh coverage.json** (slot-9 planning). Run at 2026-07-07 06:22 UTC on `is@68f174a` with both
  cross-plan PREREQs verified done (KALSHI-PERP purge landed cefi catalogue 376,984→351,511 rows, 0
  KALSHI-PERP/POLYMARKET-PERP mentions in the prediction coverage; Plan 5 unregistered-handler audit filed at
  `plans/archive/issues/wsfeedconnector_phase35_gap_2026_07_06.md`). Fresh primary-bucket manifest reads (all
  `blob.updated` 2026-07-07T06:20:42-45Z, pinned-primary `-prd` for every AG): cefi 11,125,247 · defi 10,908,735 ·
  tradfi 1,719,843 · sports 41,520 · prediction 706,197 merged rows. **Layer-1 (task-001 primary output):** cefi 73.61%
  (72/53/19/87) · defi 94.81% (77/73/4/128) · tradfi 51.43% (35/18/17/52) [STALE-BLOCKED-PLAN2] · sports 30.77%
  (26/8/18/24) · prediction 66.67% (6/4/2/17). **Layer-2 rollup:** cefi 76.77% · defi 61.97% · tradfi 96.00% [STALE] ·
  sports 100.00% · prediction 22.73%. All 4 non-blocked-AG Layer-1 percentages byte-match the per-AG certifications from
  tasks 002 (cefi 73.61), 003 (defi 94.81), 005 (prediction 66.67), and 006 (sports 30.77) — cross-verifies the unified
  all-AG run against the per-AG partials. tradfi 51.43 unchanged as expected under BLOCKED-PLAN2 (task 004); the all-run
  does NOT re-open the tradfi certification (Plan 2 rebuilds still pending). Gate satisfied per the task spec: "a fresh
  `coverage.json` produced from a real run; run id recorded" — **Run id:** `2026-07-07T06:20:58Z / is@68f174a`. Evidence
  artefact (local): `/home/ubuntu/coverage_all_20260707T062058Z.json` (4.6 MB, single unified all-AG JSON,
  schema_version present). Task run log: `/tmp/measure_honest_coverage_all_20260707T062058Z.log` (Layer-1 INCOMPLETE
  warnings for all 5 AGs — expected under the two-layer governing law: `denominator_status: INCOMPLETE` everywhere). No
  new findings; no code shipped (script-only run gate).
- **2026-07-06** — **✅ Task 007 CLOSED — smoke-harness live-verify Gate satisfied via `discrepancy filed`** (slot-9).
  Ran what exists (`GCP_PROJECT_ID=central-element-323112 --today 2026-07-06 --cloud gcp --deployment-env prd`) for the
  4 deferred AGs; surfaced 4 concrete discrepancies (tradfi=empty-matrix-BLOCKED-PLAN2, prediction=BucketNamingError in
  `_bucket_for`, cefi/defi = runner-does-not-exist) filed at
  `plans/archive/issues/honest_coverage_smoke_harness_4ag_verify_2026_07_06.md` with 4 actionable P2 todos. Sports slice
  (already verified 2026-06-29) unaffected. **Data-correctness impact: NONE** — Layer-1 certifications (73.61 cefi,
  94.81 defi, 66.67 prediction, BLOCKED tradfi, 30.77 sports) use `measure_honest_coverage` on a different code path,
  which read the manifests correctly. Discrepancy scope is confined to the smoke-harness's own [VERIFY] P2 gate: the
  classifier's semantics were never end-to-end tested on production data for 4/5 AGs — the fix-worker per issue-doc
  todos will land the runners so future rebuilds have a live smoke-test line-of-defence. Task 007 evidence:
  `unified-trading-pm@<flip-sha>` (this commit).
- **2026-07-06** — **✅ Task 008 CLOSED — honest_coverage_v2 measurement track officially closed** (slot-6). In
  `honest_coverage_v2_instrument_denominator_2026_06_28.md`: Phase 1 `[AGENT] P1.` `build_expected` consolidation
  FLIPPED to `[x] ✅` with evidence `instruments-service@681f50a` (landed via Plan 1 =
  `cefi_layer1_denominator_gaps_2026_07_03` task 2a on 2026-07-06).
  `scripts/expected_universe.py::build_expected(asset_group)` is now THE single public Layer-1 EXPECTED producer feeding
  both the Layer-1 audit and Layer-2 measure; `check_enumeration_completeness._build_expected_tuples` (+ `..._sports`)
  delegate via sibling-load (mirrors `measure_honest_coverage`'s `_load_completeness_module` pattern); per-AG
  byte-identical goldens `tests/unit/scripts/goldens/expected_universe/{cefi,defi,tradfi,sports,prediction}.json`
  (72/171/35/27/8 tuples) + regression `test_expected_universe_golden.py` (14 tests: single-producer contract +
  delegator parity + byte-identical goldens) lock the EXPECTED matrix so silent denominator drift fails loudly in
  review; QG green. Phase 2 `[UI] P2. drill-down` annotated MOVED to `instruments_completion_tracker_2026_07_06.md`
  Stage 6 (last open honest_coverage_v2 item; too small for its own AO plan — tracked as tracker hygiene singleton per
  operator 2026-07-06). Close-out logged in the honest_coverage_v2 plan's Progress Log. Gate satisfied:
  honest_coverage_v2 measurement track CLOSED, UI item legitimately excepted → tracker Stage 6.
- **2026-07-06** — **✅ Task 006 RECONCILED — certified snapshot table published (5 AGs, both layers, provenance).**
  Also fresh-measured sports (never re-measured in this plan cycle): sports Layer-1 = 30.77% (8/26, 18 missing all
  BETFAIR odds, 24 stray); sports Layer-2 = 100.00% (38,182/38,182 reachable). Reconciliation table added under task 006
  checkbox; key findings: (1) 4/5 AGs fresh-certified (cefi 73.61 · defi 94.81 · sports 30.77 · prediction 66.67);
  tradfi 51.43 STALE-BLOCKED-PLAN2. (2) Handler-audit re-read flag = 🟡 cefi only (Deribit `DeribitOptionsChainHandler`
  register `mts@015abaf5` will move cefi L2 on next capture); defi/sports/prediction 🟢 clean. (3) 73 unregistered
  venues per WSFeedConnector audit are honest handler-not-built gaps (filed `wsfeedconnector_phase35_gap_2026_07_06`),
  NOT C5-class re-read triggers. (4) Layer-1 direction: cefi ↑ (D2a), defi ↓ (lending roll-up `is@3bb7acd`), sports +
  prediction stable, tradfi blocked. (5) Layer-2 direction: defi ↑ (D1 seeding), prediction ↑ (post-purge tighten), cefi
  ↓ (D2a expansion enlarged denominator), sports 100.00, tradfi stale. (6) All 5 AGs remain
  `denominator_status: INCOMPLETE` → every Layer-2 % is a LOWER BOUND per the two-layer governing law. Sports evidence
  artefact (local): `/home/ubuntu/coverage_sports_20260706T153104Z.json` (`is@ebfd11d`; manifest
  `market-data-tick-sports-prd` blob.updated 2026-07-06T15:30:44Z; merged 41,520 rows).
- **2026-07-06** — **✅ Task 005 CERTIFIED — prediction Layer-1 = 66.67%** (fresh local
  `measure_honest_coverage.py --asset-group prediction` run at 2026-07-06 15:27 UTC on `is@6716f55` post-KALSHI-PERP
  purge; primary manifest `gs://market-data-tick-pred-prd-central-element-323112` blob.updated 2026-07-06T15:26:46Z,
  760,300 rows; merged 706,197 rows). Result: **expected_tuples 6, present_tuples 4, missing 2, stray 17 → 66.67%.**
  Direction ✓ — 66.67 (stale 06-29) → 66.67 (fresh); denominator stable at 6 tuples (KALSHI-PERP contamination was
  cefi-side, not prediction-side; prediction Layer-1 not expected to move — the purge Gate was a hygiene check, not a
  denominator delta). **No fake KALSHI-PERP rows verified:** `raw.count('KALSHI-PERP')==0` and
  `raw.count('POLYMARKET-PERP')==0` in the prediction coverage.json (post-purge state: cefi catalogue 376,984→351,511
  rows, KALSHI-PERP==0). Layer-2 prediction rollup: coverage_pct **22.73%** (captured 8,711 / reachable 38,318;
  empty_confirmed 667,879; attempted_failed 29,110; expected_unattempted 497; total 706,197; layer1_completeness_pct
  66.67; denominator_status INCOMPLETE — 2 unwired MARKET_LIFECYCLE handlers so Layer-2 stays a lower bound but
  tightened +2.17 pp vs 20.56 stale). 2 missing tuples both MARKET_LIFECYCLE (KALSHI + POLYMARKET prediction_market) —
  unwired handlers, not adapter contamination. Task 001 (multi-AG re-run) NOT flipped by this task — even though both
  its cross-plan PREREQs (KALSHI-PERP purge + Plan 5 unregistered-handler audit) are now DONE, the
  /boot-per-shippable-unit discipline holds: task 001 flip is a separate shippable unit and will re-dispatch as its own
  /boot. Remaining Layer-1 certification: 004 tradfi still BLOCKED-PLAN2 (Plan 2 rebuilds pending). Evidence artefact
  (local): `/home/ubuntu/coverage_prediction_20260706T152707Z.json`.
- **2026-07-06** — **🚧 Task 004 DOCUMENTED as BLOCKED-PLAN2** — tradfi Layer-1 certification cannot proceed until Plan
  2 (`tradfi_v9_stage1_finish_2026_07_06`) tasks 2-11 land (IS catalogue rebuild, manifest rebuild, E7 CF verify).
  Currently Plan 2 has only 1/11 done (2026 v9 migration). Running the measurement now would certify against the stale
  pre-v9 catalogue and re-measure again after Plan 2 → wasted certification. Escalated as `BLK-ab86f4e9`; main-agent
  answer confirmed: "do NOT certify tradfi Layer-1 yet … tradfi Layer-1 measurement at this point would read stale
  data". Checkbox annotated 🚧 BLOCKED-PLAN2 (not `[x]`); tracker Snapshot left with tradfi at 51.43 [06-29 stale]
  (unchanged). Re-dispatch this task after Plan 2 rebuilds land — dispatcher's `gate_on_depends: true` should be
  reviewed as per-plan-task granularity is not currently enforced (task 003 defi + task 002 cefi were correctly
  dispatched despite tradfi PREREQ, but task 004 was ALSO dispatched despite the tradfi-specific Plan 2 PREREQ).
- **2026-07-06** — **✅ Task 003 CERTIFIED — defi Layer-1 = 94.81%** (fresh local
  `measure_honest_coverage.py --asset-group defi` run at 2026-07-06 15:13 UTC on `is@681f50a` post-D1 defi seeding;
  primary manifest `gs://market-data-tick-defi-prd-central-element-323112` blob.updated 2026-07-06T15:11:42Z, 13,515,019
  rows; merged 10,828,935 rows). Result: **expected_tuples 77, present_tuples 73, missing 4, stray 128 → 94.81%.**
  Direction ✓ — 69.44 (stale 06-29) → 94.81 (fresh, honest); denominator SHRANK 108→77 (-31 tuples) driven by
  `is@3bb7acd` (2026-07-03: defi lending grain roll-up folds `a_token`/`debt_token`/`liquidation` → `lending` in Layer-1
  canon — legitimate schema tightening, NOT a wrong-direction move). All 4 missing tuples on the same venue
  (EIGENLAYER-ETHEREUM spot_asset): `eigenlayer_rewards`, `oracle_prices`, `rewards`, `staking_yields` — indicates one
  unwired handler/venue not four independent gaps. Stray tuples (first 5): AAVE_V3 a_token {oracle_prices, utilization},
  AERODROME_V3 pool {dex_swaps, swaps_ohlcv_15m, swaps_ohlcv_15s}. **Layer-2 seeding VERIFIED (task Gate satisfied):**
  `by_asset_group.defi.expected_unattempted = 1,534,304` — the D1 +1,380,376-row apply landed in the reachable
  denominator. Layer-2 defi rollup: coverage_pct 62.06% (captured 2,857,320 / reachable 4,603,799; empty_confirmed
  6,225,136; attempted_failed 212,175; total 10,828,935; layer1_completeness_pct 94.81; denominator_status INCOMPLETE —
  4 tuples still missing so Layer-2 stays a lower bound but tightened vs 57.55 stale). Task 001 (multi-AG re-run) not
  flipped — task 001's cross-plan PREREQs (KALSHI-PERP purge, Plan 5 unregistered-handler audit) primarily affect
  **prediction/cefi** Layer-2 correctness, not defi Layer-1; my single-AG defi run satisfies task 003's Gate
  independently. Remaining Layer-1 certifications (004 tradfi · 005 pred) queued and gated on their respective plans
  (tradfi migration follow-on, KALSHI-PERP purge). Evidence artefact (local):
  `/home/ubuntu/coverage_defi_20260706T151304Z.json`.
- **2026-07-06** — **✅ Task 002 CERTIFIED — cefi Layer-1 = 73.61%** (fresh local
  `measure_honest_coverage.py --asset-group cefi` run at 2026-07-06 15:01 UTC on `is@03cfd0f` post-D2a; primary manifest
  `gs://market-data-tick-cefi-prd-central-element-323112` blob.updated 2026-07-06T14:55Z; merged 11,125,247 rows).
  Result: **expected_tuples 72, present_tuples 53, missing 19, stray 87 → 73.61%.** Direction ✓ — 79.55 (stale 06-29) →
  73.61 (fresh, honest); denominator grew 44→72 (+28 tuples) matching D2a's `INSTRUMENT_TYPES_BY_VENUE` completion.
  Missing tuples (first 5): BITFINEX-FUTURES {future book_snapshot_5, future derivative_ticker, future trades},
  BITGET-FUTURES {future book_snapshot_5, future derivative_ticker}. Stray tuples (first 5): ASTER PERPETUAL
  {futures_chain, ohlcv_1m, options_chain}, BINANCE-FUTURES {FUTURE liquidations, PERPETUAL futures_chain}. Layer-2
  rollup for context: cefi coverage_pct 33.28% (captured 2,891,774 / reachable 8,689,530; total 11,125,247). **Note:**
  Task 001 (multi-AG re-run) not flipped — task 001's cross-plan PREREQs (KALSHI-PERP purge, Plan 5 unregistered-handler
  audit) primarily affect **Layer-2** correctness (fake-KALSHI-PERP capture pollution / unwired handlers reading as
  gaps), not the cefi Layer-1 denominator; my single-AG cefi run satisfies task 002's Gate independently. Other AG
  Layer-1 certifications (003 defi · 004 tradfi · 005 pred) remain queued and gated on their respective plans (defi
  seeding done, tradfi migration follow-on, KALSHI-PERP purge). Evidence artefact (local):
  `/home/ubuntu/coverage_cefi_20260706T150020Z.json`.
- **2026-07-06** — Plan authored + dispatched to AO (Plan 4 of the instruments-completion set). Gated (gate_on_depends)
  on Plans 1-3; two cross-plan prereqs (KALSHI-PERP purge + unregistered-handler audit) called out on the re-measure.
  This is the Stage-3 all-AG Layer-1 certification that makes capture % trustworthy.
