---
type: audit-report
audit_run: 2026-05-07
scope: all active plans + 37 running VMs
status: durable-reference
---

# Active Plan Audit — 2026-05-07

Cross-plan dependency graph + per-plan status snapshot. Companion to per-plan `## Audit 2026-05-07` headers +
`[AUDIT 2026-05-07: ...]` per-todo markers inserted in 16 of 20 active plans (commit `dada46d1`, 2026-05-07).

**Methodology**: 8 parallel sub-agents, one per plan-cluster. Each enumerated unchecked todos via `grep -n "- \[ \]"`,
verified implementation against shipped commits (UAC / UTL / MTDS / MDPS / instruments-service / execution-service /
strategy-service / deployment-api+ui / deployment-service / features-\* / ml-training / ml-inference repos), matched
against 37 currently-running VMs, and cross-referenced sibling plans for blocker chains.

**Deadline**: 2026-05-23 (live DeFi trading on real wallet ≥7 days). **Days remaining**: 16.

> ⚠️ Note: 4 large plans (master_to_live_defi, writegate, dart_ux_cockpit, strategy_architecture_v2) lost their per-todo
> markers mid-audit to concurrent agent `git reset` operations. Their findings are preserved in this doc rather than
> re-edited in the plan files (low-collision recovery). The other 16 plans have full per-todo markers in-place.

---

## 1. Per-plan status snapshot

| Plan                                                       | Total todos<br>unchecked | Mis-marked<br>→ flipped DONE | In-flight<br>(VMs running) | Blocked-by<br>(plans) | Stale | Recommendation                                                                                                                   |
| ---------------------------------------------------------- | -----------------------: | ---------------------------: | -------------------------: | --------------------: | ----: | -------------------------------------------------------------------------------------------------------------------------------- |
| **master_to_live_defi_2026_05_23**                         |                      110 |                            5 |                         ~6 |                   ~70 |   ~10 | needs-scoping; 3 keystone unblocks (work-stream A endpoints, alerting plan, AWS cost analysis) cascade through ~50 BLOCKED items |
| **writegate_honest_coverage_endtoend_2026_05_06**          |                       87 |                           15 |                          1 |                     1 |     1 | keep active; Phase 4.A typed-error rendering = highest leverage next                                                             |
| **dart_ux_cockpit_refactor_2026_04_29**                    |                        7 |                            0 |                          0 |                     0 |     0 | substantively shipped; 7 polish/SSOT items not live-blocking                                                                     |
| **strategy_architecture_v2_finalization_2026_04_19**       |                       67 |                            9 |                          0 |                     1 |     4 | rescope: split into 4 successor plans (post-V1-RETIRE cleanup, futures-roll, UI service-split fold-in, Unity UAT)                |
| **manifest_migration_master_2026_05_07**                   |                       18 |                            0 |                          0 |                     8 |     0 | keep active; convert to codex SSOT after Stage 4                                                                                 |
| **cefi_master_2026_05_07**                                 |                       22 |                            4 |                12 (24 VMs) |                     6 |     2 | keep active; VM-tied work draining 2026-05-08 to 2026-05-09                                                                      |
| **defi_master_2026_05_07**                                 |                       32 |                            2 |                          0 |                     6 |     0 | **TOP-PRIORITY P0** (May-23 headline)                                                                                            |
| **tradfi_master_2026_05_07**                               |                       18 |                            1 |                 5+ (5 VMs) |                     2 |     2 | keep active; P1 batch-only this cycle                                                                                            |
| **sports_master_2026_05_07**                               |                       70 |                            0 |                  3 (4 VMs) |                    22 |     0 | keep active; heavy P0 surface, cross-plan coupling                                                                               |
| **predictions_master_2026_05_07**                          |                       35 |                            1 |                          0 |                    13 |     0 | keep active; P1, 14 P0 items in 16 days = tight                                                                                  |
| **infrastructure_master_2026_05_07**                       |                       30 |                            0 |            33 (live tests) |                    17 |     4 | keep active; 9 actionable + 17 blocked                                                                                           |
| **venue_axis_asset_group_vocabulary_2026_04_25**           |                        3 |                            0 |                          0 |                     1 |     0 | **archive-ready** after folding 3 absorbed items into umbrellas                                                                  |
| **instruments_and_market_tick_data_completion_2026_05_01** |                       22 |                            0 |         26 (sports + cefi) |                    13 |     2 | keep active; gates master operator-facing data-status                                                                            |
| **mtds_per_instrument_download_api_2026_04_24**            |                       11 |                            1 |                          0 |                     6 |     1 | keep active; Phase 1.5 critical-path for May-23 (DeFi multi-chain)                                                               |
| **feature_dag_uac_ssot_and_features_coverage_2026_05_06**  |                       11 |                            0 |                          0 |                     7 |     0 | keep active; Phase 1A is highest-leverage 1-day work                                                                             |
| **features_consolidation_and_drilldown_2026_05_06**        |                       14 |                            0 |                          0 |                     4 |     0 | keep active; P2/P3, post-May-23                                                                                                  |
| **ml_training_feature_read_perf_2026_05_06**               |                       11 |                            0 |                          0 |                     0 |     0 | keep active; 1-3 day pure-win, post-May-23                                                                                       |
| **consolidated_ml_advanced_pipeline_2026_04_15**           |                       17 |                            1 |                          0 |                     4 |     0 | rescope; ~70% partially done; cross-asset-group ML scaffolding (no umbrella covers)                                              |
| **consolidated_operational_validation_2026_04_15**         |                       11 |                            0 |                33 (inputs) |                     9 |     0 | keep active; cross-cutting, fold into master Group F or successor post-May-23                                                    |
| **consolidated_strategy_and_ui_2026_04_15**                |                       32 |                            1 |                          0 |                     8 |     0 | rescope; supersession candidate flagged in plan body itself                                                                      |

**Totals**: ~628 unchecked todos audited / ~40 mis-marked → flipped DONE / ~38 in-flight VM-tied / ~150 cross-plan
blocked / ~26 stale.

---

## 2. Cross-plan dependency graph

```
                ┌──────────────────────────────────────────┐
                │ master_to_live_defi_2026_05_23 (umbrella)│
                │ Group A code-health · B data-correctness │
                │ C runtime-parity · D coverage · E ops    │
                │ F live-trading · G operator UX           │
                └──────────────────────────────────────────┘
                                    ▲
       ┌────────────────────────────┼────────────────────────────┐
       │                            │                            │
       │ feeds Group F live trading │                feeds Group G operator UX
       │                            │                            │
┌──────┴──────┐  ┌──────────────────┴────┐  ┌──────────────────┐ │
│defi_master  │  │cefi_master            │  │tradfi_master     │ │
│ (P0 hd)     │  │ (P0; 24 VMs draining) │  │ (P1 batch-only)  │ │
└─────┬───────┘  └──────────┬────────────┘  └────────┬─────────┘ │
      │                     │                        │           │
      │ blocked by          │ blocked by             │ blocked by│
      ▼                     ▼                        ▼           │
┌─────────────────────────────────────────────────────────────┐  │
│ writegate_honest_coverage_endtoend_2026_05_06               │  │
│   Phase 2.A: adapter migration                              │◀─┘
│   Phase 2.E: orchestrator pre-skip → reasons (PARTIAL)      │
│   Phase 3.D: legacy-row reconcilers (3D.1 + 3D.2 SHIPPED)   │
│   Phase 4.A: deployment-api typed-error rendering (KEY)     │
│   Phase 5: baseline + ratchet (gates May-23)                │
└─────┬───────────────────────────────────────────────────────┘
      │ blocked by
      ▼
┌─────────────────────────────────────┐
│ manifest_migration_master_2026_05_07│
│ Stage 1: sports rename (operator)   │
│ Stage 4: cross-asset rescan         │
└─────┬───────────────────────────────┘
      │ blocked by
      ▼
┌──────────────────────────────────────┐
│ infrastructure_master_2026_05_07     │◀─── 33 backfill VMs are
│ shard-axis SSOT · drilldown · build  │     LIVE TESTS of this
│ raw-tables-migration (cross-asset)   │     plan's shipped infra
└──────────────────────────────────────┘
      ▲
      │ vocabulary basis (Wave A/B/C/D/E shipped)
      │
┌─────┴───────────────────────────────────┐
│ venue_axis_asset_group_vocabulary_      │  ARCHIVE-READY pending
│ 2026_04_25 (3 absorbed items remain)    │  fold into umbrellas
└─────────────────────────────────────────┘

                ┌───────────────────────────────────────────┐
                │ Group G (operator UX) — feeds master      │
                ▼                                           ▼
┌──────────────────────────┐               ┌──────────────────────────────┐
│ dart_ux_cockpit_refactor │               │ strategy_architecture_v2_    │
│ 2026_04_29               │               │ finalization_2026_04_19      │
│ (substantively shipped)  │               │ (rescope: split into 4)      │
└──────────────────────────┘               └──────────┬───────────────────┘
                                                      │ blocks
                                                      ▼
                                         ┌──────────────────────────────┐
                                         │ Group F (live trading) gate  │
                                         └──────────────────────────────┘

      ┌─────────────────────────────────┐
      │ sports_master · predictions_    │
      │ master · features-* + ML        │
      ▼                                 ▼
┌───────────────────────────┐   ┌────────────────────────────────────┐
│ feature_dag_uac_ssot_and_ │──▶│ features_consolidation_and_        │
│ features_coverage         │   │ drilldown                          │
│ (Phase 1A = key 1-day)    │   │ (P2/P3 post-May-23)                │
└──────────┬────────────────┘   └────────────────────────────────────┘
           │ blocks
           ▼
┌─────────────────────────────────┐
│ ml_training_feature_read_perf   │  (self-contained; no upstream)
└──────────┬──────────────────────┘
           │ blocks Phase-1C
           ▼
┌──────────────────────────────────────────────┐
│ consolidated_ml_advanced_pipeline_2026_04_15 │  ~70% partially-shipped
│ consolidated_operational_validation_2026_04_15│  cross-cutting cluster e2e
│ consolidated_strategy_and_ui_2026_04_15       │  supersession candidate
└──────────────────────────────────────────────┘

instruments_and_market_tick_data_completion_2026_05_01:
  ├─ blocked by writegate Phase 2.A (MDPS parity)
  ├─ blocked by predictions_master Phase 1 (canonical_question_group SSOT)
  ├─ blocked by defi_master DeFi-protocol-backfill
  └─ gates master operator-facing data-status verification (≥99% captured)

mtds_per_instrument_download_api_2026_04_24:
  ├─ Phase 1 + Phase 4 done
  ├─ Phase 1.5 chain axis: largely unblocked (UAC CHAIN_RPC_TEMPLATES shipped)
  ├─ Phase 1.5 prediction axis: mostly unblocked (UAC predictions_master partial)
  └─ gates infrastructure_master Phase B.2/C.13 drilldown leaf access
```

---

## 3. Critical path to 2026-05-23

Three keystone unblocks cascade through ~50 BLOCKED items:

### Week 1 (2026-05-07 → 2026-05-13) — KEYSTONE UNBLOCKS

1. **Open `alerting-service-live-rules_2026_*.plan.md`** — does not exist anywhere (confirmed via
   `ls plans/active/ plans/ai/ plans/archive/`). Highest single-line risk to Week-2 alerting/kill-switch verification.
   `master_to_live_defi:work-stream-E` is the home; cascade gates Group F+G.
2. **Ship `master_to_live_defi:work-stream-A` deployment-api endpoints** (`/api/backfill/launch`, `/api/vm/events`).
   Without these the Week-2 Group F/G items cannot start.
3. **Author AWS migration cost-analysis report** — gates all D.1-D.5
   (`infrastructure_master:Phase 5+ deployment build`). Without it, AWS work is permanently gated.

### Week 1 (parallel)

4. **`writegate:Phase 4.A` deployment-api typed-error rendering** — unblocks operator visibility AND
   `infrastructure_master:data_status_multi_axis`. ~3 days; high-leverage.
5. **`feature_dag:Phase 1A`** = highest-leverage 1-day work for LookaheadBiasError honesty. Blocks
   features_consolidation Phase 1B + ML downstream.
6. **`writegate:Phase 2.A` residual** (batch_workers path B/C, `_write_manifest_records` delete, MDPS cluster wiring).
   ~3-4 days.
7. **VM drain awareness** — 24 cefi backfill VMs ETA 2026-05-08 to 09; do not start any cefi-master
   "MTDS-100%-verification" or cross-asset rescan work before VMs stop (manifest_migration_master:Stage 4 explicitly
   waits).

### Week 2 (2026-05-14 → 2026-05-20)

8. **`writegate:Phase 5` baseline + ratchet + workspace QG** — gates May-23 ratchet activation. ~2-3 days.
9. **`writegate:Phase 2.E.3` consumer-class audits** (execution / ml-training / ml-inference / 3× features-\* / strategy
   / reconciliation), 6 audits ~2 days each, parallelisable. GATES live-DeFi May-23 deadline.
10. **DART manual-trade gate (`dart_ux_cockpit:Group G`)** — substantively shipped per DART agent audit; 7 polish items
    not live-blocking. Verify Playwright matrix passes 6 personas × manual-trade flow.
11. **Strategy alpha measurement** — `strategy_architecture_v2:Phase 5 Unity UAT` blocked by external-commercial $550
    fee + Java Feed Connector binary (operator action).

### Week 3 (2026-05-21 → 2026-05-23)

12. **End-to-end live DeFi smoke** — carry_staked_basis lead + leveraged_funding_arb on real wallet, 6-perp-venue hedge
    legs (Bybit, Deribit, Binance, OKX, Hyperliquid, Aster).
13. **AWS↔GCP cloud parity validation** (deferrable post-May-23 per agent findings; hard floor is GCP-only).

### Defer post-May-23 (do NOT attempt before deadline)

- DART v2 archetype roadmap (HUMAN-P1, plan author already flagged "not blocking v1")
- Marketing copy reconciliation (§25.A.1-A.3 vs problem-led pivot)
- features_consolidation Phase 1 (consolidation 500 LOC)
- ml_training_feature_read_perf Phase 4
- All `consolidated_*_2026_04_15` rescoping
- `venue_axis_asset_group_vocabulary` 3 absorbed-item folds
- `mtds_per_instrument_download_api` Phase 2 + 3 P1-deferral

---

## 4. In-flight VM ETAs

37 VMs running as of 2026-05-07T03:30 UTC. Plans referencing these backfills are IN-FLIGHT, NOT BLOCKED — work is in
progress.

### CeFi historical (24 VMs) — ETA 2026-05-07 to 2026-05-09

Owner plan: **cefi_master_2026_05_07**.

| Group                          | VMs                                                         | Created             | Elapsed | Heavy/light          | ETA              |
| ------------------------------ | ----------------------------------------------------------- | ------------------- | ------: | -------------------- | ---------------- |
| bitfinex spot 2020-2026 (6)    | `cefi-bitfinex-spot-{2020..2026}-heavy-...`                 | 2026-05-06T08:01-02 |     19h | heavy                | 2026-05-07 to 09 |
| bitfinex futures 2021-2025 (4) | `cefi-bitfinex-futures-{2021,22,23,25}-heavy-...`           | 2026-05-06T09:53-56 |     18h | heavy                | 2026-05-07 to 08 |
| bitget futures 2025-2026 (3)   | `cefi-bitget-futures-2025-h/2025-l/2026-h-...`              | 2026-05-06T10:03-04 |     17h | mixed                | 2026-05-07 to 08 |
| coinbase spot ada+avax (4)     | `cefi-coinbase-spot-2021/22/24-ada-usd + 2025-avax-usd-...` | 2026-05-06T13:28    |     14h | per-instrument light | 2026-05-08       |
| hyperliquid 2024-2025 (2)      | `cefi-hyperliquid-{2024,25}-light-...`                      | 2026-05-06T04:18    |  22-23h | light                | 2026-05-07       |
| kraken futures 2020 (1)        | `cefi-kraken-futures-2020-heavy-...`                        | 2026-05-06T09:57    |     17h | heavy                | 2026-05-07 to 08 |
| kraken spot 2020-2026 (7)      | `cefi-kraken-spot-{2020..2026}-heavy-...`                   | 2026-05-06T17:11-12 |  10-11h | heavy                | 2026-05-08 to 09 |

### TradFi MDPS (5 VMs) — ETA 2026-05-08

Owner plan: **tradfi_master_2026_05_07**.

- `mdps-tradfi-{2021,22,23,24,25}-...` created 2026-05-06T05:00, T+22h, ETA 2026-05-08

### Sports recovery (4 VMs) — ETA 2026-05-07 to 2026-05-08

Owner plan: **sports_master_2026_05_07**.

- `af-backfill-20260507-033214` (api_football, T+0h)
- `fs-backfill-20260507-010724` (footystats, T+5h)
- `sfi-backfill-20260507-010938` (soccer-football-info, T+5h)
- `us-backfill-20260507-010653` (understat, T+5h)
- ETA: 4-12h depending on date range, so 2026-05-07 to 2026-05-08

### Always-on (1 VM)

- `vm-zombie-watchdog-20260506-175221` — infra; never has an ETA

### NOT currently running (ETAs N/A)

- DeFi backfills: 0 running. **defi_master_2026_05_07** has no in-flight VM cover; needs new launches for May-23
  critical path.
- Predictions backfills: 0 running. **predictions_master_2026_05_07** same.
- ml-training/inference VMs: 0 running.

---

## 5. Plans this audit recommends archiving

**None ready as of 2026-05-07.**

Closest candidates (not yet — listed for follow-up tracking):

- `venue_axis_asset_group_vocabulary_2026_04_25` — 5 main waves all shipped (Wave A/B/C/D/E per CLAUDE.md). 3 absorbed
  items remain (VenueMapping deletion, dashboard SSOT, poolGetSnapshots). Recommend folding those into asset_group
  umbrellas, then archive.
- `dart_ux_cockpit_refactor_2026_04_29` — 9-phase cockpit programme substantively shipped; 7 polish/SSOT items remain.
  Could archive after fold of 3 AGENT-P0 items into a `dart_polish_2026_*` follow-up.

---

## 6. Anomalies + workspace risks

1. **Concurrent `git reset` operations** wiped per-todo audit markers from 4 large plans mid-audit (master_to_live_defi,
   writegate, dart, strategy). Reflog shows 2 separate `reset: moving to HEAD` events. The 16 surviving plans were
   committed + pushed (commit `dada46d1`) immediately to lock them in. Workspace rule "plan-checkbox-flips MUST happen
   at ship time" (CLAUDE.md hard rule per `896c9bc5`) is exactly this lesson.

2. **Plan-body references to folded plans**: `master_to_live_defi` body references `defi_e2e_pipeline_2026_04_30`,
   `leveraged_leg_controller_ 2026_05_01`, `defi_pipeline_extension_2026_05_01` as live plans — all folded into
   `defi_master_2026_05_07` per Stage 7 batch consolidation. Work-stream-E EXTEND items + critical-path Week-1 alerting
   line need updating to point at `defi_master:Fork 1`.

3. **Service readiness matrix in master plan** lists `manual_trade_booking_reconciliation_2026_03_22` as "to archive"
   but Stage 1 already archived it. Matrix row should now reference only
   `consolidated_operational_validation_2026_04_15`.

4. **Plan-hygiene work-stream G** assumes ~148 active plans with 140/142/31 affected — Stage 7 batch consolidation
   reduced active/ to ~25 plans, so item counts are obsolete; script scope must re-derive.

5. **Stale module-path reference in manifest_migration_master**: line 473 cites
   `unified_api_contracts.canonical.crosscutting.empty_confirmed_ reasons.EMPTY_CONFIRMED_REASONS` — actual canonical
   module is `honest_coverage.py`. Fix on next ship.

6. **MDPS-1440-NaN reproduction-test** in infrastructure_master is STALE (superseded by writegate Phase 2.A adapter
   migrations + reconciler `MDPS@d3be0ef`).

7. **Phase 3 of strategy_architecture_v2 is entirely STALE**: V1-RETIRE bypassed the 14-21d shadow window per operator
   directive. All 4 OPS items in Phase 3 should be dropped in next housekeeping.

8. **mlr-p3-shap-inference (consolidated_ml_advanced_pipeline)**: SHAP wiring shipped (UAC `InferenceRequest.explain` +
   `inference_shap.py` + orchestrator wiring). Plan body says "no schema field" but verified at
   `internal/domain/ml/schemas.py:605`. Flipped to DONE.

9. **cda-p2-microstructure (consolidated_strategy_and_ui)**:
   `features-delta-one-service/.../calculators/microstructure.py` + tests shipped. Flipped to DONE.

10. **features-cross-instrument paired-dispersion stack** (UAC@`0e7ba95` +
    features-cross-instrument@`d1da107`/`071604f`/etc.) belongs to **strategy v2 Phase 9**, NOT to feature_dag plan.
    Confusion risk: anyone reading "features-cross-instrument shipped" in commit logs may falsely flip feature_dag items
    as DONE.

11. **manifest_migration_master is NOT superseded by writegate Phase 3.D.2** reader-side fallback. Read-side fallback
    (UTL@`c5c2669e` + deployment-api@`176c599`) classifies legacy null-reason rows on read; manifest_migration_master
    scripts are the WRITE-side back-fill. Both required.

12. **Lighter `block_height` on-chain replay is INFEASIBLE** (sequencer- internal, NOT zkSync L1).
    `defi_master:dex_historical_replay_*` section needs marking STALE / BLOCKED-ON
    `dex_perp_onboarding_handover Item C`.

13. **`alerting-service-live-rules_2026_*.plan.md` does not exist anywhere** in active/ai/archive.
    master_to_live_defi:work-stream-E references it as the alerting plan — must be authored before any Week-2 Group F
    alerting verification.

---

## 7. Operator action items (in priority order)

1. **Open the alerting plan**. Single highest leverage. ~1 hour. Unblocks master:work-stream-E + Group F alerting
   verification.
2. **Ship `master_to_live_defi:work-stream-A` deployment-api endpoints** (`/api/backfill/launch`, `/api/vm/events`). 1-2
   days.
3. **Author AWS migration cost-analysis report**. Gates D.1-D.5 + cloud parity Group D.
4. **Drain 24 cefi VMs (ETA 2026-05-08/09) before launching cross-asset manifest rescan**. Schedule the rescan launch
   for 2026-05-09 09:00 UTC.
5. **Update `master_to_live_defi` plan body** to drop refs to folded defi-\* plans + obsolete plan-hygiene counts
   (anomalies #2, #4).
6. **Author `master_to_live_defi:Phase Audit-Followup`** that lists the 13 anomalies above so they don't fall off the
   radar.
7. **DART live-readiness check**: confirm 6-persona Playwright matrix passes manual-trade flow. Plan claims it does;
   verify by running.
8. **Strategy `Phase 5 Unity UAT`**: pay $550 fee + acquire Java Feed Connector binary. Operator-only.

---

## 8. Sub-agent IDs (for follow-up SendMessage if needed)

| Cluster                   | Agent ID            |
| ------------------------- | ------------------- |
| master_to_live_defi       | `a4e4b25035dc1d61e` |
| writegate_honest_coverage | `a3f456bbd88c77198` |
| dart_ux_cockpit_refactor  | `a6036d08c25dfc3a1` |
| strategy_architecture_v2  | `a219040e2d22d62db` |
| manifest_migration_master | `a03f5a3fb2c072fea` |
| 5 asset_group umbrellas   | `a775c69dc6e14e657` |
| infrastructure cluster    | `a95f323a70fcbaa02` |
| features + ML cluster     | `a262040dedc07c538` |

---

## 9. Re-running this audit

This audit is a snapshot. Recommended cadence: weekly, or after any major backfill completion. To re-run:

1. `git fetch origin live-defi-rollout && git pull` to sync plan state.
2. `gcloud compute instances list --filter="status:RUNNING"` for current VMs.
3. Per-cluster sub-agent prompts in this conversation provide the template.
4. Push commit immediately after agent edits to defeat concurrent resets.
