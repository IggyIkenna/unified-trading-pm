---
doc_type: plan
title:
  MASTER COORDINATOR — data + manifest + schema migration + IS catalogue + pipeline_mode standardisation (single-pane
  dependency-gated sequencer for the whole data-layer cutover)
summary:
  Master coordinator for data + manifest + schema migration + IS catalogue + pipeline_mode standardisation — a pure
  dependency-gated sequencer tracking the global DAG for the whole data-layer cutover.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    agent-orchestrator,
    batch-live-reconciliation-service,
    deployment-api,
    deployment-service,
    deployment-ui,
    e2e-testing,
  ]
scope: [engineer, admin]
tags: [coordinator, migration, manifest, data-layer, pipeline-mode, catalogue, dependency-gating]
related:
  [/plans/active/defi_migration_audit_log_2026_07_24.md, /plans/active/is_catalogue_g1_root_audit_log_2026_07_24.md]
context_scope:
  [
    /codex/02-data/pipeline-mode-partition.md,
    /plans/active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md,
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/active/is_catalogue_g1_root_audit_log_2026_07_24.md,
    instruments-service/scripts/enumerate_expected_universe.py,
  ]
created: 2026-06-07
parent_epic: manifest_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3.6
last_updated: "2026-08-05"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  [
    operator 2026-06-07 ("coordinated master plan around data/manifest/schema migrations + IS catalogue; attach all plan
    todos; block on upstream readiness; no orphans"),
    pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md (the Phase-0 apply-gate),
    proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md (the could-exist-universe foundation),
  ]
umbrella: true
drift_direction: advance-code
---

# MASTER COORDINATOR — Data-Layer Canonicalisation, Migration, Catalogue & Pipeline-Mode Cutover

> **🟡 LINE-CAP REMEDIATION SPLIT 2026-07-24** (`/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md` #16,
> operator-approved unlock+fix): this coordinator was over the 2000-line `umbrella: true` ceiling. An exact ~160-line
> verbatim-duplicated verdict block inside the old `## vm-defi (slot-2) status + findings` section was de-duplicated
> (verified byte-identical via `diff` before deletion — zero content lost), then the two AG-specific audit-log sections
> were extracted verbatim to `defi_migration_audit_log_2026_07_24.md` (the former
> `## vm-defi (slot-2) status + findings` section, 23 todos) and `is_catalogue_g1_root_audit_log_2026_07_24.md` (the
> former `## G1 expanded — IS catalogue is the ROOT…` section, 9 todos). This coordinator keeps `umbrella: true` and its
> role as the pure dependency-gate sequencer; `locked_by`/`locked_since` were cleared per the operator's explicit unlock
> grant for this plan.

> **🟡 SECOND LINE-CAP PASS 2026-07-24** — the `umbrella: true` 2000L exemption was RETIRED (operator ruling
> 2026-07-24); every `plans/active/` doc, this one included, now holds to the flat 1000L cap. Five fully-closed, dated
> historical sections (0 open todos among them) were extracted verbatim to
> `/plans/archive/2026_07/master_data_canonicalisation_migration_catalogue_history_2026_07_24.md` per
> `plans/active/task_template.md` §3 finding J: the 2026-06-11 coordinator-progress/FINAL-REPORT/G1.schedule-smoke +
> 2026-06-17 R3 verdict-pack run, the 2026-06-29 G4-apply run log, the 2026-06-11 R-wave resume brief, and the two
> slot-7 cross-cutting audit-verdict sections (incl. the closed F-X1 finding). All 7 open todos + all
> structural/registry sections (Gate-State Board, Sub-plan registry, Audit framework, Master coordination todos) are
> unchanged in this file. 1289→953 lines.

> **🟢 TradFi G4 `--apply` DONE 2020-2026 (7 VMs, exit_code=0 fatal=0, completed 2026-07-06; GCS re-verified
> 2026-07-12)** — post-apply cleanup (manifest 100%-v9, CF-audit, legacy-twin deletes, RESUME runbook) tracked in
> `tradfi_v9_stage1_finish_2026_07_06.md` + `instruments_completion_tracker_2026_07_06.md`. (was: "🟡 VM IN FLIGHT
> (2026-07-06) — slot-6 TradFi G4 restart... RESTARTED per D3..." — stale, described the fan-out start.) Corrected per
> operator ruling 2026-07-12, plan-reconciliation finding 128
> (`plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2).

> **Role (operator 2026-06-07): a PURE COORDINATOR — it tracks, gates, and links; it executes nothing.** Every line of
> code, every migration `--apply`, every audit lives in the registered sub-plans below. This plan is the single pane of
> glass: the global dependency DAG that blocks each gate on its upstream being GREEN, the sub-plan registry, the audit
> framework, and the orphan sweep. It is **data-layer only** — it cross-links `master_to_live_defi_2026_05_23.md` (the
> live-cutover master) as the **downstream consumer**, it does not own live promotion.
>
> **Coordinator non-duplication (HARD)**: this REPLACES scattered coordination. The DeFi plan's `## MASTER` section is
> demoted to a DeFi executor that points UP here; the `pipeline_mode_source…standardisation` plan keeps its Phase-0
> apply-gate but is registered as G0 here. No third coordinator — if you find cross-plan sequencing anywhere else, fold
> its links into THIS registry.

## The governing sequence — 6 dependency gates (operator's end-to-end order)

```
G0  Foundation MODEL + code + doc/codex/plan coherence   ─┐  (cross-cutting; gates ALL applies)
G1  IS CATALOGUE foundation (could-exist universe SSOT)   ─┤→ both GREEN before any per-AG dry-run is trustworthy
G2  Per-AG migration/manifest/schema scripts updated      ─┘     + 7+2-point AUDIT + DRY-RUN green (per AG)
G3  Manifest consolidation + deployment-API/UI UNION view + pipeline_mode drilldowns
G3.5 Pre-apply verification harness (⑬–⑲): canonical possible-manifest registry · bidirectional orphan sweep (phantom==0 ∧ orphan-E==0) + bucket taxonomy + sizing · schema-attribute completeness · catalogue-seeded denominator · candle-edge · projected-manifest preview  ← HARD-BLOCKS G4; folded into re-runnable CF-15…CF-21  [migration_verification_orphan_safety_2026_06_10]
G4  Per-AG --apply (manifest + data/schema migration)   ← GATED on G0,G1,G2,G3,G3.5 GREEN + pre-migration drain → then G4.5 verified-delete cleanup (CF-21)
G5  Resume BACKFILLS → 100% honest coverage (UI drilldowns shrink to minor)
                                                          ↓
                                  master_to_live_defi_2026_05_23.md  (live promotion — downstream)
```

> **Massive purged/removed 2026-07-19→21 (operator Option C): Databento is the sole batch SoT; no cost-swap decision
> remains — `batch_massive` is read-recognition-only until the gated GCS purge.**

**Single hardest invariant (from the standardisation plan, restated as the master gate):** **NO `--apply`
data/manifest/schema migration runs until G0 + G1 + G2 + G3 are GREEN.** The walk bakes in whatever model exists at
apply-time; fixing a wrong model needs a banned second whole-corpus walk (single-walk discipline). The current migrators
stamp **coarse `pipeline_mode="batch"`** (or blank — defi rebuild `:302`); the canonical target is **source-aware
`{mode}_{source}[_{transport}]`** — so every migrator/rebuild/enumerator MUST be upgraded in G0/G2 BEFORE its AG's G4
apply.

## 🛑 Pre-migration drain — EXECUTED 2026-06-08 (slot-2) + RESUME runbook (HARD RULE, tracked)

> **Both fleets quiesced before any `--apply`; rollback snapshots in place. The per-AG `--apply` pre-flight gate (1) is
> SATISFIED.** Resume ONLY after all per-AG `--apply` complete + verified — the exact reverse-commands are below so
> nothing is left paused.
>
> **⚠️ DRAIN SCOPE (clarified 2026-06-17 — operator question): the drain stops ONLY DATA-CAPTURE / data-pipeline VMs —
> the bucket-writing prefixes in `VM_PREFIX_TO_BUCKET` (`vm-defi`/`vm-cefi`/`vm-tradfi`/… capture + `EPHEMERAL_BATCH` /
> `EPHEMERAL_EXPERIMENT` / `SCHEDULED_RECURRING` runners that write manifest shards). It does NOT — and MUST NOT — stop
> the agent infrastructure: the Central / Orchestrator VM (`agent-orchestrator-vm-1`, registry id `planning`), the Human
> Planning VM (registry id `human-planning` — the interactive VM the operator works on), or the `agent-orch-vm-*` epic
> worker fleet (`bucket=None`, `LONG_LIVED_LIVE`) / any `tier=daemon`-tagged VM. Those run agents, not data capture, so
> quiescing them would kill the very session driving the migration. The drain recipe targets capture prefixes by
> `lifecycle_class` + non-null `bucket`; it never SIGTERMs the orchestrator/planning VMs.** (Today the per-epic capture
> fleet is post-cutover / not-running anyway — only the 2 agent VMs are live — so the resume-drain is a no-op-or-small
> set; this clarification keeps it correct when capture VMs are relaunched for the real `--apply`.)

**What was done (central-element-323112 + AWS 427895769566):**

- **GCP VMs**: `footystats-fwd-*` self-terminated → only `alerting-quietness-*` + `vm-zombie-watchdog-*` (safety,
  exempt) remain. 0 data writers.
- **GCP schedulers**: **48 prod writers/consolidators PAUSED** (`gcloud scheduler jobs pause`, `asia-northeast1`).
- **AWS EventBridge**: **26 `uts-prod-consolidator-*` rules DISABLED** (`ap-northeast-1`); AWS Batch had 0 running jobs.
- **EXEMPT (stays up)**: GCP alerting + watchdog (fail-toward-safety); AWS `agent-orchestrator-vm-1` (code, not data).
- **Final consolidation NOT needed**: all AG `availability_index.parquet` = 2026-06-08T04:14–04:15; newest
  `_index/per_vm/` shard = 2026-05-12 → index ⊇ shards (fully consolidated).
- **🔁 ROLLBACK SNAPSHOT**: `_index/snapshots/pre_migration_2026_06_08.parquet` written in **10 buckets**
  (`{market-data-tick,instruments-store}-{cefi,defi,tradfi,sports,pred}-prd-central-element-323112`). The per-AG
  `--apply` abort path restores from here.

**RESUME runbook — POST-MIGRATION ONLY (after every AG `--apply` complete + verified):**

```bash
# GCP — resume the 48 paused prod schedulers
for j in features-onchain-service-daily-trigger features-sports-service-daily-trigger instruments-daily-backfill \
  instruments-service-daily-trigger market-tick-cefi-daily-download market-tick-daily-trigger \
  uts-prod-consolidator-liveness-watchdog-cron uts-prod-features-calendar-t1-schedule \
  uts-prod-features-commodity-t1-schedule uts-prod-features-cross-instrument-t1-schedule \
  uts-prod-features-delta-one-t1-schedule uts-prod-features-multi-timeframe-t1-schedule \
  uts-prod-features-onchain-t1-schedule uts-prod-features-sports-t1-schedule uts-prod-features-volatility-t1-schedule \
  uts-prod-manifest-consolidator-instruments-{cefi,defi,prediction,sports,tradfi}{,-legacy}-cron \
  uts-prod-manifest-consolidator-market-data-{cefi,defi,prediction,sports,tradfi}{,-legacy}-cron \
  uts-prod-mtds-collect-{dex-pools,dex-swaps,eigenlayer-rewards,evm-defi,gas-fees,lending-indices,liquidations,lst-rates,oracle-prices,perp-funding,solana-defi}-cron \
  uts-prod-mtds-paper-smoke-cron uts-prod-mtds-scenario-matrix-cron; do
  gcloud scheduler jobs resume "$j" --location=asia-northeast1 --project=central-element-323112
done

# AWS — re-enable the 26 disabled consolidator rules
for r in uts-prod-consolidator-execution-{cefi,defi,tradfi} uts-prod-consolidator-features-calendar \
  uts-prod-consolidator-features-delta-one-{cefi,defi,tradfi} uts-prod-consolidator-features-onchain-{cefi,defi} \
  uts-prod-consolidator-features-sports uts-prod-consolidator-features-volatility-{cefi,tradfi} \
  uts-prod-consolidator-instruments-{cefi,defi,prediction,sports,tradfi} \
  uts-prod-consolidator-market-data-{cefi,defi,prediction,sports,tradfi} \
  uts-prod-consolidator-ml-training-artifacts uts-prod-consolidator-strategy-{cefi,defi,tradfi}; do
  aws events enable-rule --name "$r" --region ap-northeast-1
done
```

> Verify after resume: `gcloud scheduler jobs list --location=asia-northeast1 | grep -c PAUSED` (prod → 0) +
> `aws events list-rules --region ap-northeast-1 --query "Rules[?State=='DISABLED' && starts_with(Name,'uts-prod-consolidator')]"`
> (→ empty). Do NOT resume until the migration is verified-complete + the new manifests are consolidated.

## 🟦 Gate-State Board (G0–G5 × asset_group) — M-COORD-4

> **Critical-path snapshot for the orchestrator.** 🟢 = promoted/green · 🟡 = prepared but gated (dry-run-green,
> awaiting an operator-fired `--apply` or a real-data/credentialed run) · 🔴 = not started / blocked-downstream.
> **Recomputed from the registered plans' checkboxes + the cross-cutting A–H verdict + the per-AG `--apply` (G4) ticks —
> NOT hand-maintained divergent state.** Refresh at each gate promotion (re-read the WAVE checkboxes §below, the A–H
> verdict table, and the per-AG `G4 --apply` checkboxes; or run `regenerate_active_plan_inventory.py`). **As of
> 2026-07-12** (was: "As of 2026-06-16" with every G4 cell frozen at 🟡(gated) — stale; the board was never refreshed
> across 4 gate promotions already recorded lower in this same doc. Refreshed per plan-reconciliation finding 129,
> `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 "50 reclassified" blanket ruling).

| asset_group       | G0 C-PATH + pmode | G1 catalogue+enum | G2 per-AG ①–⑫ audit | G3 UNION UI |                          G4 `--apply`                          | G5 backfill→100% |
| ----------------- | :---------------: | :---------------: | :-----------------: | :---------: | :------------------------------------------------------------: | :--------------: |
| **defi**          |        🟢         |     🟢 (dry)      |         🟡          |     🟢      |                    🟢 (applied 2026-06-29)                     |        🔴        |
| **cefi**          |        🟢         |     🟢 (dry)      |         🟡          |     🟢      |                    🟢 (applied 2026-06-29)                     |        🔴        |
| **tradfi**        |        🟢         |     🟢 (dry)      |         🟡          |     🟢      | 🟢 (applied 2026-07-06, post-apply cleanup tracked separately) |        🔴        |
| **sports**        |        🟢         |     🟢 (dry)      |         🟡          |     🟢      |                    🟢 (applied 2026-06-29)                     |        🔴        |
| **prediction**    |        🟢         |     🟢 (dry)      |         🟡          |     🟢      |                    🟢 (applied 2026-06-29)                     |        🔴        |
| **cross-cutting** |        🟢         |        🟢         |      🟢 (A–H)       |     🟢      |                              n/a                               |       n/a        |

**Cell basis (the registered evidence each column reads):**

- **G0** 🟢 all — "G0 FULLY GREEN (9/9)" tick (the `live_websocket`→`live_<source>` M1 migration + C-PATH read/write +
  doc-reconcile; driven 2026-06-16). BATCH+LIVE `--apply` foundation-clear on the G0 axis.
- **G1** 🟢 (dry) — cross-cutting C+D rows 🟢 (`enumerate_expected_universe` v2 shape-aware +
  `build_instrument_catalogue` ⊇ present-set + `migrate_instruments_store_v9` projection); migrator documented
  **dry-run-GREEN all 5 AGs** (cefi 30,803 · defi 125,242 · sports 2.68M · tradfi · pred 493 → 100%). The real-data
  candidate-count + `--apply-write` catalogue seed rides each AG's gated G1.run (IS backfill) → it promotes with G4,
  hence 🟡-on-real-data but 🟢 on code+dry-run.
- **G2** 🟡 per-AG / 🟢 cross-cutting — the cross-cutting **A–H pre-apply audit verdict is 🟢 (REGRESSION RISK: NONE)**;
  the per-AG ①–⑫ dry-run audits are owned by each per-AG plan (in progress / gated on that AG's IS backfill).
- **G3** 🟢 — `deployment-api` UNION view (`union_reduce_to_cells`, F/H rows; 21 tests green); could-exist denominator
  over the 4-state union. Serves all AGs.
- **G4** 🟢 all 5 AGs (updated 2026-07-12, was: "🟡 (gated) — every per-AG `G4 --apply` checkbox is open `[ ]`" — stale,
  superseded by the WAVE checklist below: defi/cefi/sports/prediction `--apply` ✅ COMPLETE 2026-06-29; TradFi `--apply`
  DONE 2020-2026 span, 7 VMs, exit_code=0 fatal=0, completed 2026-07-06, GCS re-verified 2026-07-12 — see the plan
  banner + finding-128 note on the TradFi WAVE checkbox below; TradFi post-apply cleanup (manifest 100%-v9, CF-audit,
  legacy-twin deletes, RESUME runbook) is tracked separately in `tradfi_v9_stage1_finish_2026_07_06.md` +
  `instruments_completion_tracker_2026_07_06.md`, not gating this G4 cell). Rollback snapshots
  `pre_migration_2026_06_08.parquet` staged (retained; irreversible walk already executed for all 5 AGs).
- **G5** 🔴 — backfills→100% (WAVE 5) start only after G4 `--apply`. (G4 is now green all 5 AGs per above — G5 itself is
  unevidenced by this refresh and left unchanged.)

## 🟢 Dispatch waves (live — who owns what NOW)

Slot map: **2=DeFi · 3=CeFi · 4=Sports · 5=Prediction · 6=TradFi · 7=cross-cutting**.

**WAVE 1 — IN FLIGHT (launched 2026-06-07): close G0 all-AG + launch G1 all-AG.**

| Slot | Gate          | Scope (in flight)                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ---- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 7    | G0 + G1-found | C-PATH READ (features/mdps readers prefix-match) + doc reconcile (#7/M-COORD-1) + G1 FOUNDATION (`build_instrument_catalogue` + `enumerate_expected_universe` v2 all-AG-capable + daily scheduler per AG). **RE-SCOPED 2026-06-07: the v2 producer MUST be instrument-shape-aware — `(instrument_type × data_type)` validity filter + bundle-grain (G1-ENUM, P0) — NOT generic fan-out** (else false `expected_unattempted` pollution; see G1-expanded) |
| 2    | G0 + G1-defi  | C-PATH WRITE (`migrate_defi`/`rebuild_defi` → `derive_pipeline_mode_for_row`; last coarse writer) + DeFi IS-catalogue (dry-run now; run gated on slot-7 code + DeFi IS backfill)                                                                                                                                                                                                                                                                        |
| 3    | G1-cefi       | CeFi instruments-store v9 + catalogue run (dry-run proven 2026-06-05) + scheduler                                                                                                                                                                                                                                                                                                                                                                       |
| 4    | G1-sports     | Sports instruments-store v9 + fixtures/leagues could-exist + catalogue run + scheduler                                                                                                                                                                                                                                                                                                                                                                  |
| 5    | G1-prediction | Prediction instruments-store v9 + polymarket-market could-exist + catalogue run + scheduler                                                                                                                                                                                                                                                                                                                                                             |
| 6    | G1-tradfi     | TradFi instruments-store v9 + listed-contracts-per-session could-exist + catalogue run + scheduler                                                                                                                                                                                                                                                                                                                                                      |

Intra-wave gate: slot-7 G1-foundation code is the prerequisite for slots 2–6 catalogue **runs** (dry-runs are
unblocked); per-AG `--apply-write` seed also gated on that AG's IS backfill complete + accurate UAC. G0 read/docs are
parallel-safe.

**WAVE 2 (after G0+G1 green)** — G2 per-AG dry-run + 7+2-point audit (one slot each) → **WAVE 3** G3 UNION UI (slot 7) →
**WAVE 4** G4 per-AG `--apply` (gated G0∧G1∧G2∧G3 + drain) → **WAVE 5** G5 backfills→100%; the live-side tranche
(M3/M4/M6/M7 · `live_websocket`→`live_<source>` · M8 cadence) = tracked parallel track, after the batch migration.

### Dispatch checklist — TRACKED big-job on Ikenna's local slots (2–7), NOT VM auto-dispatch

> **Execution = Ikenna's local slots** (the per-epic VM fleet `vm-defi`/… is post-cutover / NOT running; LIVE
> orchestrator = `vm-0` only). Slot↔AG map: **2=DeFi · 3=CeFi · 4=Sports · 5=Prediction · 6=TradFi · 7=cross-cutting**.
> These are the remaining checkboxes so the big job is trackable done-vs-left (the prose table above is the overview).
> The per-AG plans hold the detailed G1/G2 todos + audit verdicts; these are the WAVE-level rollup.
>
> **🤖 AUTONOMOUS RUN MODEL (operator 2026-06-08) — slots 2–7 run on the LAPTOP per
> `cursor-configs/AUTONOMOUS_AGENT_RULES.md`, no drip-feed.** Each slot drives its full task-set **to DRY-RUN-GREEN**
> autonomously (resolve its blockers → migrator/rebuild `--dry-run` exits clean → ①–⑫ audit verdict). **Ship discipline
> = run `quality-gates.sh` then `quickmerge --agent --files` — do NOT chase staging/main (that promotion lane is
> automated, not the agent's concern).** **HARD-STOP = the actual `--apply`** (the irreversible single-walk that bakes
> prod data): agents prepare it dry-run-green and STOP; the operator fires `--apply`. No `DEFERRED`/`BLOCKED-OPERATOR`
> end-states otherwise; journal to the per-AG plan across compaction; end with a report.

- [x] ✅ [MIGRATION] P0. **G0 FULLY GREEN (9/9) — BATCH **and** LIVE `--apply` foundation-clear; the `live_websocket`
      multi-source path-collision gate is REMOVED (updated 2026-06-16 /autonomous).** The GATE-0 Phase-0 DAG
      (`pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` § "GATE-0 EXECUTION PLAN") was driven to
      **9/9** this session. The earlier 7/9 foundation (fix#1 mtds@89807b4 · fix#3 features@795e4f4 · cadence column
      utl@dfe3385f · M3 `could_exist` uac@d56b9cc2 · M4 `select_for_mode` uac@7441a692+blrs@0e17d7e · M5b
      deployment-api@66e8562 · GATE-0 SIT system-integration-tests@db14463) was then completed by the final 2 items: ✅
      **M1-BREAKING** — the `live_websocket`→source-aware `live_<source>` migration across **8 repos**
      (execution@04218fbc · batch-live-reconciliation@3bad2fe · deployment-api@aa18d8ae **(reader
      exact-match→`startswith("live")` bug FIXED)** · market-data-processing@30e7672 · market-tick-data@84a15cc ·
      unified-trading-library@2afb22bd (resolver source-aware + `close_candle_writer` pipeline_mode required) ·
      **unified-api-contracts@28bd50e — `LIVE_WEBSOCKET` alias member DELETED** + `source_string_for`/`transport_of`
      special-cases removed + closed-set round-trip validates every member · system-integration-tests@ec46de8 — SIT LIVE
      leg un-skipped + green). `rg "live_websocket|LIVE_WEBSOCKET" --type py` = **0 fleet-wide**. The breaking UAC bump
      (→0.15.0) fired the dep-update fan-out: **4/6 consumer rebuilds GREEN** (validates compatibility); 2 stale-base
      transients (UTL PR#369 / BLRS PR#81, cut pre-migration → self-resolve on promotion-to-main — see the G0 plan
      tick-7). ✅ **M5c/d** UI cadence drilldown (display-only, pw:L2): deployment-ui@687d4ce (pw:L2 ✓ 216/216) +
      unified-trading-system-ui@41b1567c (pw:L2 ✓ 31/31, parity-gap port). Every touched repo is QG-green / pw:L2-green.
      **So a REAL `--apply` over a corpus containing LIVE rows is now foundation-clear on the G0 axis** (the #5
      collision is eliminated); the remaining `--apply` gates are G1/G2/G3/G3.5 + the pre-migration drain. (G1 also
      carries the 2026-06-16 UAC-denominator callout.) — driven 2026-06-16.
- [ ] [DATA] P0. **slot 2 (DeFi) — G4 `--apply`**: instruments-store v9 walk → MTDS raw-tick v9 → catalogue seed → IS
      backfill (Era-B relabel rides the migrator's final step). Operator-fired; on real VM/tarball; rollback =
      `pre_migration_2026_06_08.parquet`. Repo: market-tick-data-service + instruments-service. — 2026-06-29: VM
      `canonical-migration-defi-20260618-180603` rc=0; MTDS raw-tick v9 enumerate seed 1,380,376 rows →
      `market-data-tick-defi-prd/_index/per_vm/enum-universe-defi-1782720346.parquet`; IS catalogue 7,236 rows
      monotonic_ok (no write needed — current=new). **CORRECTED 2026-08-12 (/plan-reconcile)**: the "IS v9 migration
      done" claim above was WRONG — it described the MTDS raw-tick side only. `defi_migration_audit_log_2026_07_24.md`'s
      GATE C (the separate `instruments-store-defi` `_index` v9 walk, distinct from MTDS raw-tick v9) is independently,
      repeatedly re-verified still 0% v9 on disk as of this same-day re-check (125,242 v8 rows; dry-run proves 100%
      v9-clean transform, but the `--apply` WRITE has never run — GATED, not blocked). Reopened; see
      `/plans/active/defi_migration_audit_log_2026_07_24.md` GATE C for the live tracked todo. NOT ✅ COMPLETE.
- [x] ✅ [DATA] P0. **slot 3 (CeFi) — G4 `--apply`** (same sequence; DERIBIT/OKX Era-B chains). Repos: as above. —
      2026-06-29: CeFi already canonical on-disk (`pipeline_mode=batch_tardis` paths confirmed); IS v9 migration done;
      enumerate seed 162,528 rows (EXPECTED_PRE_VENUE_LAUNCH); IS catalogue 349,912 rows > 349,709 promoted ✅
      (2026-06-29T10:xx UTC). ✅ COMPLETE.
- [x] ✅ [DATA] P0. **slot 4 (Sports) — G4 `--apply`** (league-grain; 2.68M-row instruments-store). Repos: as above. —
      2026-06-29: VM `canonical-migration-sports-20260618-180654` rc=0; IS v9 migration done; enumerate seed 16,554 rows
      (EXPECTED_PRE_SOURCE_COVERAGE_START); IS catalogue 113 rows > 94 promoted ✅. ✅ COMPLETE.
- [x] ✅ [DATA] P0. **slot 5 (Prediction) — G4 `--apply`** (per-cqg; pred-prd buckets). Repos: as above. **CF-11 CLOSED
      (2026-06-17, supersedes 🔴)** — prediction GREEN, clear for G4 (mtds@df69ada). — 2026-06-29: VM
      `canonical-migration-prediction-20260629-053038` rc=0 (500,128 objects, processed_candles/by_date); IS v9
      migration done; enumerate seed 9,120 rows (EXPECTED_PRE_VENUE_LAUNCH); IS catalogue 2,486,092 rows monotonic_ok
      (current — no write needed). ✅ COMPLETE.
- [x] ✅ [DATA] P0. **DONE (na-eligibility-audit 2026-08-04)** — slot 6 (TradFi) — G4 `--apply` (databento/massive;
      daily listing). Repos: as above. **🟢 CF-11 CLOSED + DRY-RUN-GREEN (slot-6, 2026-06-08)** — the `databento.py:826`
      (+ L802) ZERO-signal swallow re-raises → `attempted_failed` ON LDR (instruments-service@f7744fbf + @c0f2f39c,
      re-verified `git show origin/live-defi-rollout`; the prior "🔴 GATED" was stale — keyed off `bd1456aa` read as
      not-on-LDR, its content re-SHA'd as f7744fbf). Migrator + rebuild `--dry-run` clean on real-prod GCS (recent
      984/0-err; old-tail `category=`→`asset_group=` T-OLD fix proven); Era-B count=0; rollback snapshot present.
      **APPLY-READY — REGRESSION RISK: NONE** (tradfi plan ①–⑫). cefi already closed (`e2e008f0`); source-provenance
      write-path shipped (#4 non-block). Operator fires `--apply` (`--also-legacy` per R1). — 06-29 hit a transient
      OOM/stall (frozen-and-STALE per the 2026-07-12 doc-reconciliation note, superseded by the completing 2026-07-06
      apply). **CLOSED 2026-08-04 (na-eligibility-audit)**: `tradfi_v9_stage1_finish_2026_07_06.md` is now archived,
      `status: resolved`, banner "🟢 RESOLVED + ARCHIVED. All 11 of this plan's own todos are `[x]` done" (residual
      items forked to named successor plans) — `plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md`.
- [x] ✅ [CODE] P1. **slot 7 (cross-cutting) — audit-criteria automation DONE** (Tier-2 + Tier-3 + cron all shipped; see
      the § "Cross-cutting audit verdict (slot-7)" in
      `/plans/archive/2026_07/master_data_canonicalisation_migration_catalogue_history_2026_07_24.md` — extracted
      2026-07-24, line-cap remediation). Tier-2 STEP 5.92/5.93 (pm@b4245a7dd) + Tier-3 cf_manifest_audit CF-1…14 +
      cross-AG wrapper (pm@2fe982eb1) + daily alert-on-RED cron (deployment@eaff3a7). Only adds gates — parallel to the
      applies, blocks no AG `--apply`. (Residual: validity-matrix P2 test + bar-edge Phase-0 cross-source
      fixture/assertion in-flight — tracked in their plans.)
- [x] ✅ [CODE] P1. **DONE (na-eligibility-audit 2026-08-04)** — slot 7 — post-apply consumer cleanups (the
      deferred-with-reason items: execution-service defi loader, deployment-api FLAG-1/3/dedup, MDPS GAP-7) — after the
      per-AG applies. All named sub-items independently confirmed resolved elsewhere, all `[x]`: FLAG-1
      `deployment-api@60cd585`, GAP-7 `mdps@4363bce` (`downstream_services_manifest_canonicalisation_2026_06_01.md`);
      FLAG-3 + dedup (`data_completion_cefi_2026_07_15.md`); defi loader bug —
      `plans/archive/issues/execution_service_defi_loader_canonical_path_2026_06_08.md` (resolved,
      `execution-service@abfadd803`).
- [ ] [CODE] P2. **WAVE 5 / live-side (gated, after batch migration)** — G5 backfills→100%; the live-side tranche
      (M3/M4/M6/M7 · `live_websocket`→`live_<source>` · M8 cadence). Assign to slots when reached.

### Coordinator progress — 2026-06-11 (autonomous finish-to-DONE run, slot-4)

> **Extracted verbatim 2026-07-24 →
> `/plans/archive/2026_07/master_data_canonicalisation_migration_catalogue_history_2026_07_24.md`** (line-cap
> remediation, `plans/active/task_template.md` §3 finding J) — the 2026-06-11 coordinator-progress notes, the FINAL
> REPORT, the G1.schedule smoke verdict addendum, and the 2026-06-17 R3 ⑬–⑲ verdict-pack run (incl. the Solana
> fake-history reconciliation + the PREDICTION cqg correction) now live there verbatim.

### G4 apply run 2026-06-29 — 4/5 AGs COMPLETE; TradFi BLOCKED (OOM-killed migration)

> **Extracted verbatim 2026-07-24 →
> `/plans/archive/2026_07/master_data_canonicalisation_migration_catalogue_history_2026_07_24.md`** (line-cap
> remediation, `plans/active/task_template.md` §3 finding J) — the full 2026-06-29 G4-apply run log (IS v9 migration,
> MTDS raw-tick v9 migration, catalogue seed, IS backfill, per-AG status) now lives there verbatim. Current TradFi state
> is tracked live in the WAVE checklist above (slot 6 todo) + `tradfi_v9_stage1_finish_2026_07_06.md`.

## ⚖️ OPERATOR RATIFICATION 2026-06-11 — the COMPLETE pre-apply gate set (interactive Q&A, 8 decisions)

> These 8 decisions close the "what's left before G4" question. NOTHING else gates the applies; each decision below is
> the ratified thoroughness level. Todos carry the work; the per-AG ⑬–⑲ verdict is the assembly point.

1. **Orphan-E backfills = middle-ground-PLUS (operator: "don't be lazy")**: characterize per data_type against actual
   CODE USE-CASES (especially defi + sports — many data_types), and **canonicalise orphans to v9-grade schemas/paths AS
   PART of the backfill** even where the orphaned capture predates v9 — never stamp a non-canonical object into the
   manifest as-is. Sample-verify per cell; re-sweep to E==0.
2. **Schema completeness = CITADEL**: extend the v9 UAC schemas to carry ALL source columns (the 11 polymarket columns
   included) + add the missing defi/tradfi SchemaSpecs; re-run CF-18 to GREEN. No acked drops.
3. **V5/V6 = CITADEL**: full per-AG projected-`_index` dev render + operator eyeball + manifest_diff report attached to
   every ⑬–⑲ verdict.
4. **IS capture freeze = CITADEL**: diagnose + resume IS definition collection NOW and backfill the ~2026-05-21→now
   definition gap BEFORE any could-exist seed; re-run catalogue roll-ups + enumerates per AG after.
5. **Stale images + service health = OPERATOR DIRECTIVE (new scope)**: wait for clean worktrees (other agents live),
   then verify ALL shipped code completed the promotion cycle to `main`; MEANWHILE **smoke-test every service per asset
   group** — credentials valid, instrument + market tick data actually fetchable; AUDIT what doesn't work (assume
   nothing); **block at SHARD granularity** (asset_group × data_type × venue × …), never the whole AG — producing the
   explicit pending-post-migration-backfill shard ledger.
6. **Codex/doc reconcile = CITADEL, BEFORE applies**: rewrite the 5 per-AG plans' stale coarse tokens; purge
   `hyperliquid_rest` from `pipeline-mode-and-batch-live-reconciliation.md`; write the missing sports/tradfi/prediction
   batch-live seam docs; lift the M1–M8 live/replay TARGET design into codex as settled contract (plans reference it,
   not vice versa).
7. **Re-dry-run = CITADEL**: every AG's migrator + rebuild `--dry-run` re-proven on CURRENT HEAD against real prod GCS,
   writing the projected `_index` in the same pass (feeds V5).
8. **Prediction/sports = CITADEL**: sports-specific orphan sweep built + run to E==0 (same backfill discipline); sports
   v1_archive ROW-coverage proven before any drop; prediction dry plan REGENERATED on final HEAD and signed off only
   within its full ⑬–⑲ verdict.

### ⏸️ R-wave RESUME BRIEF — 2026-06-11 ~02:45 UTC (account session-limit wall, resets 10:10 UTC)

> **Extracted verbatim 2026-07-24 →
> `/plans/archive/2026_07/master_data_canonicalisation_migration_catalogue_history_2026_07_24.md`** (line-cap
> remediation, `plans/active/task_template.md` §3 finding J) — the per-R-agent (R1/R2/R4/R5/R6) inherited-dirty-WIP
> resume brief now lives there verbatim. All named agents' work is long since RESUMED + COMPLETE per the Ratification
> todos below.

### Ratification todos (the dispatch — owners per slot map)

- [x] ✅ [DATA] P0. **R1-backfill — per-AG class-E characterize→canonicalise→`record_captured` backfill** — **E==0 +
      `unknown_prefixes`==0 GREEN on all four hive AGs 2026-06-11 ~14:32Z** (defi/cefi/prediction/tradfi; sports = R8).
      Tool `backfill_orphan_class_e.py` (is@0a2e542 + c49d957 + row-key/parser/footer fixes through is@f73abe4+):
      characterize→convert-to-v9→`record_captured` with per-cell sample-verify; headline: most E was matcher
      false-positive (venue-spelling/grain — defi 254,984 ALL covered); real backfills = tradfi 15,694 converted,
      prediction 7,462 converted, cefi 74,392 record-only; tbbo spec carries (uac@715e2ed lineage +
      `ts_init`/`bid_size`/ `ask_size`); one-shot consolidations merged backfill shards (index ≥ snapshot everywhere —
      no loss).

      Full narrative + verdicts in the G3.5 plan Progress Log. — instruments-service@f73abe4, uac@<tbbo>, reports
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              `_index/audit/orphan_sweep_<ag>.parquet` + `orphan_backfill_<ag>.parquet`.

- [x] ✅ [UAC] P0. **R2-schema — carry ALL dropped columns into v9** — **unified-api-contracts@715e2ed**: v9
      `SchemaSpec` registry extended so CF-18 is GREEN per AG — all 11 polymarket trades columns carried (amount, asset,
      conditionId→`condition_id`, outcomeIndex→`outcome_index`, transactionHash→`transaction_hash`,
      data_source→`source`, market_type, resolution_period, symbol, timestamp, underlying — camelCase via
      `ColumnSpec.source_aliases`, never duplicate canonical cols) + new SchemaSpecs for defi
      rewards/risk_params/utilization + tradfi/trades (+ the full RED list: defi dex_pool_swaps/lending_indices, tradfi
      options_chain/CME, etc.). Completeness regression suite `tests/unit/test_schema_spec_completeness.py` (registry
      round-trip + alias hygiene + per-cell source-column completeness + previously-RED pins) GREEN. The
      `migration_schema_completeness` per-AG re-run (consumes the contract via `carried_column_names`, the same SSOT) is
      now 0-RED at the contract level. slot-3 → this autonomous tail. Repo: unified-api-contracts.
- [x] ✅ [DATA] P0. **R3-verdicts — V5 render + V6 verdict per AG ASSEMBLED on CURRENT HEAD (2026-06-17, autonomous
      run)** — verdict packs in `plans/audit/results/r3_verdict_packs_2026_06_17/` (per-AG projected-v9 render + status
      distribution + `manifest_diff` report + verdict line; `manifest_diff_<ag>.json` + `analyze_diff.py` attached). All
      regenerated on HEAD vs the live 06-14 `_index`. **4/5 GREEN outright + prediction GREEN after a stale-projection
      correction:** defi GREEN (cap 348K→440K, removed=39,867 = legacy `dex_swaps`→`swaps_ohlcv_<tf>` `data_type`
      supersession, 105 phantom downgrades; projection REGENERATED — defi rebuild changed mtds@89807b4) · cefi GREEN
      (cap 1.33M→2.49M CF-11 honest re-emit; removed=733 garbage venues 0-objects; 375 phantom) · tradfi GREEN (cap
      100K→902K legacy pre-hive parser; 2,902 phantom closed-market-day downgrades **spot-verified on HEAD**: CME
      2020-01-01 has no ohlcv_15m object) · sports GREEN (gate 0/0; only −17,288 ODDS_API probe-artifact exclusion) ·
      **prediction GREEN — 75.3% cqg coverage** (NOT the stale 0.2%: the cqg classifier is UAC-resident and the registry
      was expanded under decision 338 in 3 UAC commits AFTER the 06-11 projection → re-projected on HEAD: 542,170
      `ClassifierConfidenceLow`→1, captured 7,116 cqg bundles; the removed cells = raw-grain superseded BY DESIGN by the
      cqg-bundle atom). Every AG schema→v9 100% + pipeline_mode blank→source-aware; projected ≥ pre_migration snapshot.
      M-COORD-7 corroborated GREEN (STEP 5.85 + AST = 0). **Operator clear to V6-eyeball + G4 --apply on ALL FIVE AGs.**
      Original "dev restart-deployment-stack render" is the operator's own live eyeball (recipe in the pack README;
      beta-blob projections live in GCS); the verdict packs embed the textual coverage render. mtds@df69ada · is/uac
      HEAD · reports `\_index/audit/projected_index\**<ag>\_.parquet`.
- [x] ✅ [DATA] P0. **R4-IS-freeze — diagnose + resume IS definition collection + backfill 2026-05-21→now gap BEFORE any
      could-exist seed**; then re-run `build_instrument_catalogue` + `enumerate_expected_universe v2` per AG. (Note:
      collection is reference-data — independent of the drained market-data writers; resuming does NOT violate the
      pre-migration drain.) slot-3. Repos: instruments-service + deployment-service. — **✅ COMPLETE 2026-06-11
      (slot-4).** Root cause = 3 layers (scheduled producers structurally DEAD for months — the
      `instruments-service-daily` Workflow targets a nonexistent Cloud Run job `instruments-service`, FAILED daily since
      ≥2026-03-13; capture was actually carried by manual `instr-backfill-*` VM launches that stopped ~05-22; the 06-08
      drain then paused the already-dead schedulers; + defi-specific c7d9bb2 venue-tag regression silently dropping 21
      venues, FIXED instruments-service@0ae4e481). Both IS schedulers re-ENABLED (ONLY those two —
      consolidator/market-data stay drained). Backfills run locally (per-VM shards `r4-is-backfill-local*`): cefi
      05-23→06-11 (15/16 venues; DERIBIT-COMBO upstream 400), defi 05-09→06-11 `--force` (52–53/57;
      AAVE_V3-OPTIMISM/MORPHO×2/DRIFT vendor-side), tradfi 06-08→06-11 (4/5; CME = Massive futures-endpoint 404
      BLOCKED-UPSTREAM). Catalogues re-promoted (monotonic ACCEPT): cefi 220,222 / defi 6,853 / tradfi 686,348 rows. v2
      enumerate scan-only (NO --apply-write): cefi 35,894,676 / defi 167,458,116 / tradfi 109,235,280 candidates.
      sports/prediction = report-only (pred by_date frozen at 2026-05-12 write; both lack prod/catalog.parquet pending
      the granularity-aware producer). Full evidence + 3 new todos (producer rebuild P0; CME re-probe P1;
      silent-thinning hardening P2): `proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md` § "Progress Log —
      R4-IS-freeze execution".
- [x] ✅ [AUDIT] P0. **R5-service-smoke — per-(service × asset_group) credential + data-fetch smoke matrix — DONE
      (slot-4 resume 2026-06-11)**: 26 live probes (12 predecessor + 14 resume; logs `/tmp/r5_smoke/*.log` on the worker
      host) across IS definitions ×5 AGs + mtds tick fetch per source (tardis, databento, massive, hyperliquid, onchain
      RPC eth+solana, thegraph subgraph, polymarket clob+gamma, kalshi, odds_api, footystats, yahoo; barchart = static
      GCS preload by design — no live adapter exists to smoke). Every failure audited + classified (auth / 4xx / empty /
      precondition / code-bug); BLOCKED shards emitted at (AG × data_type × venue) grain in "### R5 smoke ledger" below
      — no whole-AG blocks. Promotion-to-main snapshot included (NO repo's 2026-06-10/11 LDR ships have fully reached
      `main` yet — stale-image caveat recorded). 1 credential ask (Databento account LOCKED).
- [x] ✅ [DOCS] P0. **R6-codex — full M-COORD-1 closure BEFORE applies — DONE (slot-4 resume 2026-06-11, pm@a28cbd4d7 +
      pm@51863c157 + pm@05456c343)**: 5 per-AG plans de-coarsened (gate banners reconciled to M-COORD-1/R6-codex;
      defi+cefi deep-annotated — every remaining coarse/`hyperliquid_rest` token is a marked legacy-state/historical
      record, never spec; defi A12f-col CLOSED by ratification); `pipeline-mode-and-batch-live-reconciliation.md`
      hyperliquid_rest purged (vendor-only + transport column; sole remaining mention = the documented retirement) +
      reconciled to M1–M8 (replay stratum + reconciliation-facing M1–M8 slice); `sports-batch-live.md` (NEW) +
      `prediction-batch-live.md` + `tradfi-batch-live.md` seam docs shipped at cefi depth (phantom empty-reasons
      corrected against real UAC closed set); M1–M8 live/replay TARGET design codified as settled contract in
      `/codex/02-data/pipeline-mode-partition.md` § "Ratified TARGET design" (+`batch-live-architecture.md` §10.5/§13,
      `cefi-batch-live.md` §7, `replay-subsystem.md` SUPERSEDED banner, `availability-manifest-and-data-status.md`
      live-taxonomy reconcile) — ratified-with-gated-tranche named (`M1-BREAKING`). slot-7→slot-4. Repo:
      unified-trading-pm.
- [x] ✅ [DATA] P0. **DONE (na-eligibility-audit 2026-08-04)** — R8-sports/pred gates (sports portions ✅ DONE
      2026-06-11; prediction regen also done — all 3 children below are `[x]`, incl. the prediction dry-plan regen
      itself, "GREEN, clear for G4"; parent simply never got flipped):
  - [x] ✅ sports-specific orphan sweep (candidate_parquet_paths-driven) built + run → characterize/backfill to **E==0 +
        unknown_prefixes==0 on BOTH sports buckets (2026-06-11 ~16:12Z)** — `migration_orphan_sweep_sports.py` +
        `backfill_orphan_class_e_sports.py`, instruments-service@94ea099 + @37793dd, 38 tests. odds: E 20→0 (smoke-probe
        per-VM shard → one-shot consolidate; 0 recordings needed); reference: E 87,659→0 (~81.8k league-grain cells
        recorded + 1 definitions-availability row + 3 consolidations, index 2,681,044→2,681,628 no-loss) + NEW
        `C3_pre_launch_window` disposition (10,345 objects the manifest contractually refuses — UAC coverage-window
        decision filed as a P1 todo in the G3.5 plan). Full verdicts + class tables in the G3.5 plan Progress Log ("R8
        part 2"); reports `gs://<bucket>/_index/audit/orphan_sweep_sports.parquet`.
  - [x] ✅ sports v1_archive ROW-coverage proven before any drop — 398/398 days, 72,522/72,522 rows covered via
        `source_fixture_id`↔`af_fixture_id` (G3.5 plan Progress Log "R8 part 1", 2026-06-11 ~14:50Z); archive carried as
        its own `B2_v1_archive_superseded` sweep disposition (G4.5 delete-list candidate, operator-gated).
  - [x] ✅ prediction dry plan REGENERATED on final HEAD (2026-06-17), attached to its verdict for sign-off. **Migrator
        dry-plan** `migrate_prediction_to_pred_prd_v9.py --dry-run` on HEAD: TOTAL planned=1,897,691 copied=0, 0 errors
        (751,723 raw + 582,730 processed + 563,238 `category=` stale-source canonicalisations). **Manifest rebuild**
        regenerated on HEAD against the **expanded cqg registry** (decision 338): 9,447 rows, captured 7,116 cqg
        bundles, attempted_failed 1 (was 542,170 on the stale 06-11 registry) → **75.3% coverage**. Folded into
        `plans/audit/results/r3_verdict_packs_2026_06_17/verdict_prediction.md` + `pred_migrator_dryplan.txt`.
        prediction GREEN, clear for G4. mtds@df69ada.

### R5 smoke ledger — extracted 2026-08-05 → `/plans/archive/2026_08/master_data_canonicalisation_migration_catalogue_r5_smoke_ledger_history_2026_08_05.md` (line-cap remediation pass 3)

> **Extracted verbatim 2026-08-05** — the full R5 smoke ledger (BLOCKED shards table, GREEN per-AG table, cross-cutting
> findings, promotion-to-main snapshot, and all 7 remediation todos) now lives in the archive doc above. Every R5-fix
> todo is `[x]` done; the one-time probe data (2026-06-11) is stale history; the Gate-State Board now reads G4 all-green
> across all 5 AGs.

## Cross-cutting audit verdict (slot-7 / vm-cross-cutting) — 2026-06-08

> **Extracted verbatim 2026-07-24 →
> `/plans/archive/2026_07/master_data_canonicalisation_migration_catalogue_history_2026_07_24.md`** (line-cap
> remediation, `plans/active/task_template.md` §3 finding J) — the per-area (A–H) apply-impact table (Tier-2/Tier-3 QG
> gates, bar-edge Phase 0/1, MVP-scope, BigQuery, G3 UNION view) now lives there verbatim. **VERDICT: REGRESSION RISK:
> NONE for the per-AG `--apply`** (unchanged).

## ⚠️ CONFLICTS SURFACED + RESOLVED (the coordinator's job — track + resolve, do not let them reach `--apply`)

> The whole point of this coordinator is to catch where existing code/docs CONTRADICT the ratified source-aware model
> and resolve them BEFORE the irreversible single-walk apply. **Full repo sweep done 2026-06-07** (grep
> `pipeline_mode=(batch|live)` / `DEFAULT_PIPELINE_MODE` / `derive_pipeline_mode_for_row` across all repos). **The
> headline finding overturned my own framing**: the source-aware `pipeline_mode=batch_<source>/` path key is ALREADY the
> live convention for **cefi / tradfi / sports / prediction** (their `rebuild_*_manifest` + `migrate_tradfi`/sports use
> UTL `derive_pipeline_mode_for_row(venue, ag, data_type)` → `batch_<source>`; UTL `pipeline_mode_resolver` already
> bridges the coarse "batch" input → `batch_<source>` output for batch). **DeFi is the lone coarse outlier**, and a few
> DeFi-scoped readers/tests/docs still assume coarse. So C-PATH is NOT "every AG" — it is concentrated + tractable.

**C-PATH inventory (categorized; ✓ = already source-aware, ✗ = coarse conflict):**

| Class              | Site                                                                                                                                                                                                                                                                                                                                                        | State  | Fix / owner                                                                                                                                                                                             |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| WRITE migrator     | `migrate_tradfi_to_v9_canonical.py` (`_pipeline_mode`→`batch_databento`)                                                                                                                                                                                                                                                                                    | ✓      | reference impl — copy this pattern                                                                                                                                                                      |
| WRITE rebuild      | `rebuild_{cefi,tradfi,sports,prediction}_manifest*` (`derive_pipeline_mode_for_row`)                                                                                                                                                                                                                                                                        | ✓      | reference impl                                                                                                                                                                                          |
| **WRITE migrator** | **`migrate_defi_full_v9_canonical.py:70/700/714`** `DEFAULT_PIPELINE_MODE="batch"` → coarse path+col                                                                                                                                                                                                                                                        | **✅** | **DONE mtds@f80c50f1** — `batch_<source>` per shard via `derive_pipeline_mode_for_row`; source+transport in path+column; coarse retired                                                                 |
| **WRITE rebuild**  | **`rebuild_defi_manifest.py:88/206/230/250`** `_DEFAULT_PIPELINE_MODE="batch"` (+ `:302` blank — C-#1)                                                                                                                                                                                                                                                      | **✅** | **DONE mtds@f80c50f1** — `derive_pipeline_mode_for_row` source-aware (path+col), `pipeline_mode=` day-probe, per-shard isolation; C-#1 `:302` fixed                                                     |
| READ (defi)        | features `mtds_canonical_reader.py` — was exact `pipeline_mode=batch/`+`live/` probe                                                                                                                                                                                                                                                                        | ✅     | **DONE features@c487e04b** — day-level mode-agnostic listing, prefix-match `batch_*/live_*/replay_*` + bare + legacy `category=`, canonical-over-legacy ranked                                          |
| READ               | mdps `orchestration_scanner.py` — day-listing already mode-agnostic; FIXED source-aware leak bug                                                                                                                                                                                                                                                            | ✅     | **DONE mdps@d59749c (PR#103→staging)** — gated `batch_onchain_rpc` legacy-venue branch on absence of `data_type=` (canonical `dex_pool_state` no longer leaks into `dex_swaps`); +source-aware fixtures |
| TEST               | mtds `test_migrate_defi_full_v9_canonical.py:53-54` · `test_rebuild_defi_manifest.py:17/72` · mdps `test_orchestration_scanner.py:182-230` · features `test_mtds_canonical_reader.py:63-132`                                                                                                                                                                | ◑      | **mtds DONE mtds@f80c50f1** (both defi test files assert `batch_<source>` + source/transport, 25/25 green); mdps/features test updates ride their READ change (features@c487e04b / mdps@d59749c)        |
| LIVE (all AGs)     | UTL `pipeline_mode_resolver.py:123` live → `LIVE_WEBSOCKET` (not `live_<source>`)                                                                                                                                                                                                                                                                           | ~      | the M1 `live_<source>` OBJECT migration = **gated next tranche** (C-#5) — NOT part of the batch migration                                                                                               |
| DOC ✓              | CLAUDE.md:568 · SUB_AGENT_MANDATORY_RULES:276 · most AG plans · deployment-api/data_status                                                                                                                                                                                                                                                                  | ✓      | already `batch_*/`                                                                                                                                                                                      |
| DOC ✗              | `defi_manifest_canonicalisation_2026_06_01.md` (archived → `plans/archive/2026_07/defi_manifest_canonicalisation_2026_06_01.md`, folded→M-1 2026-07-13, finding 197; many coarse `pipeline_mode=batch/`) · codex `pipeline-mode-partition.md` (mixed) · audit `defi_object_path_canonicalisation_2026_06_01.py:87` · `pipeline_mode_partition_migration:63` | ✗      | reconcile to `batch_<source>` (rides M-COORD-1)                                                                                                                                                         |
| BY-DESIGN          | codex `batch-live-architecture.md:466` + `instruments-live-architecture.md:30` — instruments reference data has **NO `pipeline_mode=live` partition** (live writes the identical batch path)                                                                                                                                                                | ✓      | keep — a real exception, not a conflict                                                                                                                                                                 |

**RESOLUTION (HARD, single-walk)**: bring the DeFi migrator + rebuild to the cefi/tradfi pattern
(`derive_pipeline_mode_for_row` → `batch_<source>` in path + column, same C0 walk — a coarse apply + later re-walk = the
banned second whole-corpus walk); flip the 2 DeFi-scoped readers + the 4 tests to prefix-match `batch_*/`; reconcile the
coarse doc stragglers (M-COORD-1). The live→`live_<source>` object migration is the separate gated tranche.

**Other standardisation findings:**

- ✅ **C-#2 (UTL) — RESOLVED 2026-06-07 (utl@d0745bde)**: `ManifestWriter.add()` now AUTO-DERIVES `pipeline_mode` via
  `derive_pipeline_mode_for_row` for a derivable market-data row (venue+data_type, no feature_group) — blank can no
  longer pass silently; features/service rows keep `""`. (The DeFi rebuild `#1` stamp itself is still vm-defi's.)
- ✅ **C-#6 (UTL) — RESOLVED 2026-06-07 (utl@d0745bde)**: `_assert_source_matches_pipeline_mode` raises
  `PipelineModeSourceMismatchError` when an EXPLICIT batch `source` disagrees with `source_string_for(pipeline_mode)`
  (`batch_databento` + `source="massive"`), in record_captured / record_captured_from_counts / add() (gated on an
  explicit caller-provided source — auto-stamped single-source cells are correct-by-construction).
- ✅ **C-TRANSPORT (P0) — RESOLVED 2026-06-07 (operator R4)**: (1) the `hyperliquid_rest` antipattern is retired in the
  enum (uac@cc69b123: `BATCH_HYPERLIQUID` + the unified-vendor `LIVE/REPLAY_HYPERLIQUID`; `Transport` enum +
  `transport_of`
  - `default_transport_for_source`); the `transport` manifest COLUMN landed (utl@d0745bde) + is stamped by IS seeds
    (is@03a93e10) + the consumer sweep renamed `hyperliquid_rest`→`hyperliquid` (mtds@c567962e). (2) codex
    `02-data/pipeline-mode-partition.md` reconciled (pm@9120464fe). (3) R4 ratified by operator. REMAINING: the UI
    reference-data regen (gated on the UI playwright gate — see the standardisation plan) + the other codex docs
    (`pipeline-mode-and-batch-live-reconciliation.md` still has `hyperliquid_rest` refs) ride the #7 doc audit. The
    `live_websocket`→`live_<source>` OBJECT migration stays the separate gated tranche.
- **C-TRANSPORT (original write-up, surfaced by operator 2026-06-07) — the optional `[_{transport}]` suffix is
  under-specified + inconsistently implemented + undocumented in codex.** The M1 form is `{mode}_{source}[_{transport}]`
  with `transport ∈ {rest, websocket, flat_file}`, BUT:
  1. **Antipattern in the SHIPPED enum**: `BATCH_HYPERLIQUID_REST="batch_hyperliquid_rest"` (+ LIVE/REPLAY) glue the
     transport INTO the source name — the standardisation plan (lines 125-126) explicitly names this "the M1
     antipattern; target `hyperliquid` + transport". The new enum (uac@8cafb758/6cd08c89) carried it forward. **Fix**:
     split → source=`hyperliquid`, transport=`rest` as a separate trailing segment/column. Owner: vm-cross-cutting
     (UAC).
  2. **codex `02-data/pipeline-mode-partition.md` is STALE + silent on transport**: documents only
     `{batch_*, live_websocket}`, says "Don't use `pipeline_mode=replay_*`" + "replay writes to `live_websocket`" —
     directly contradicts the M1 source-aware + `replay_<source>` + transport model. Owner: M-COORD-1 (doc reconcile) —
     rewrite to the `{mode}_{source}[_{transport}]` form incl. replay + the transport-suffix rule.
  3. **Suffix policy NOT ratified** (operator residual ○): line 95 leaves "transport as a trailing path/enum segment
     (`live_tardis_websocket`) vs a column" as an "Open fork" with a recommendation only — **carry the transport suffix
     in the path key ONLY where a source genuinely runs >1 transport for the SAME shard (else noise), AND also as a
     `transport` column** (line 216). Needs operator ratification before the migrators encode it.

  **Operator residual R4 — ratify the transport rule**: (a) transport suffix in `pipeline_mode` path key only when a
  source has >1 transport per shard (else omit); (b) always populate a separate `transport` column; (c) split the
  `hyperliquid_rest` source → `hyperliquid` + transport=`rest`. Recommend yes to all three (matches the M1
  recommendation + kills the antipattern). Until ratified, the DeFi/per-AG migrators stamp `{mode}_{source}` WITHOUT a
  transport suffix (safe subset — adding the suffix later for a genuine >1-transport source is additive, not a re-walk).

## Sub-plan registry (every data-layer plan, its gate, owner, blocked-until)

> Status is coarse (`see plan` for detail). The value here is the GATE + the BLOCKED-UNTIL edge. Owner = `assigned_vm`.
>
> **🔴 DOC-RECON FIX 2026-07-14 (finding 197)**: `defi_manifest_canonicalisation_2026_06_01` /
> `cefi_manifest_canonicalisation_2026_06_01` / `tradfi_manifest_canonicalisation_2026_06_01` — plus sibling rows below
> pointing at the same 2026-07-13 fold batch (`bucket_name_ssot_legacy_dual_write_remediation_2026_06_01`,
> `data_source_provenance_all_asset_groups_2026_06_01`, `prediction_manifest_canonicalisation_2026_06_01`,
> `downstream_services_manifest_canonicalisation_2026_06_01`, `solana_defi_legacy_migration_2026_05_27`) — were
> FOLDED→M-1 (`data_completion_to_100_all_ag_2026_06_21`) + archived to `plans/archive/2026_07/` 2026-07-13 (operator
> ruling "Approve all + unlock", `mtds_consolidation_foldin_mapping_2026_07_12.md`). Rows below updated: Owner → M-1
> (folded scope) where folded; Plan/issue link → the archive path for history; original owner/link kept as `(was: …)`.
> `solana_defi_legacy_migration` was independently COMPLETE (not folded content) but is likewise archived.
> `sports_manifest_canonicalisation_2026_06_01` (row below) is UNCHANGED — operator-ruled KEEP-WITH-JUSTIFICATION, not
> folded/archived.
>
> **🔴 DOC-RECON FIX 2026-07-25**: M-1 (`data_completion_to_100_all_ag_2026_06_21`) was itself split on 2026-07-15 (and
> again 2026-07-24 for sports) into five sibling plans — `data_completion_defi_2026_07_15`,
> `data_completion_cefi_2026_07_15`, `data_completion_tradfi_2026_07_15`, `data_completion_prediction_2026_07_15`,
> `data_completion_sports_2026_07_24` — all `status: active`, `parent_epic: manifest_master`. The G2 rows below still
> pointed at the superseded M-1/2026-06-01 references; Owner updated to the current split plan for each AG.

| Gate     | Plan / issue                                                                                                                                                                                                | Role                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | Owner                                                                                                               | Blocked-until (upstream)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **G0**   | `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05`                                                                                                                                         | **THE model + apply-gate** (batch/live/replay × source × transport; M2/M3 registries; M4 precedence; cont. contract; 0.8 doc reconcile)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | vm-cross-cutting                                                                                                    | — (root; Phase-0 code must go GREEN)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| G0       | `plans/archive/2026_07/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` (was: `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01`) — FOLDED→M-1, archived 2026-07-13 (finding 197)     | canonical bucket SSOT (env-tier readers/writers) + L6 decommission                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | data_completion_to_100_all_ag_2026_06_21 (M-1, folded scope) (was: vm-cross-cutting)                                | partly done; L6 ⟶ G4                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| G0       | `plans/archive/2026_07/data_source_provenance_all_asset_groups_2026_06_01.md` (was: `data_source_provenance_all_asset_groups_2026_06_01`) — FOLDED→M-1, archived 2026-07-13 (finding 197)                   | `source` column — RIDES each AG's single-walk                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | data_completion_to_100_all_ag_2026_06_21 (M-1, folded scope) (was: per-AG)                                          | G0 model (source-aware) ratified ✓                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| G0       | `pipeline_mode_partition_migration_2026_06_01`                                                                                                                                                              | on-disk `pipeline_mode=` partition — RIDES each AG walk                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | per-AG                                                                                                              | G0 model form (M1) locked                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| G0       | `manifest_reader_fail_fast_on_stale_fallback_2026_05_28`                                                                                                                                                    | reader fail-fast default + consolidator liveness (no legacy fallback)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | vm-cross-cutting                                                                                                    | parallel-safe                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| **G1**   | `proper_instrument_catalogue_lifecycle_rollup_2026_06_04`                                                                                                                                                   | **could-exist-universe SSOT** — `build_instrument_catalogue` roll-up + daily scheduler + v2-enumerator recurring run                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | vm-cross-cutting                                                                                                    | `instruments_manifest_canon` (IS indices canonical)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| G1       | `instruments_manifest_canonicalisation_2026_06_01`                                                                                                                                                          | IS reference/instrument `_index` canonical (all AG)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | per-AG slice                                                                                                        | G0                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| G1       | `instruments_backfill_phase3_2026_05_22`                                                                                                                                                                    | IS reference backfill                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | vm-cross-cutting                                                                                                    | G1 catalogue GREEN ⟶ G5                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| **G2**   | `plans/archive/2026_07/defi_manifest_canonicalisation_2026_06_01.md` (was: `defi_manifest_canonicalisation_2026_06_01`) — FOLDED→M-1, archived 2026-07-13 (finding 197)                                     | DeFi MTDS single-walk + §A–H executor                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | `data_completion_defi_2026_07_15` (M-1 split 2026-07-15) (was: M-1 folded scope; was: vm-defi (slot-2))             | G0 + G1                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| G2       | `plans/archive/2026_07/cefi_manifest_canonicalisation_2026_06_01.md` (was: `cefi_manifest_canonicalisation_2026_06_01`) — FOLDED→M-1, archived 2026-07-13 (finding 197)                                     | CeFi single-walk                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | `data_completion_cefi_2026_07_15` (M-1 split 2026-07-15) (was: M-1 folded scope; was: vm-cefi (slot-3))             | G0 + G1                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| G2       | `sports_manifest_canonicalisation_2026_06_01`                                                                                                                                                               | Sports single-walk (+ fixtures/transfer-window reasons)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | `data_completion_sports_2026_07_24` (M-1 split 2026-07-24) (was: vm-sports (slot-4))                                | G0 + G1                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| G2       | `plans/archive/2026_07/prediction_manifest_canonicalisation_2026_06_01.md` (was: `prediction_manifest_canonicalisation_2026_06_01`) — FOLDED→M-1, archived 2026-07-13 (finding 197)                         | Prediction single-walk                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | `data_completion_prediction_2026_07_15` (M-1 split 2026-07-15) (was: M-1 folded scope; was: vm-prediction (slot-5)) | G0 + G1                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| G2       | `plans/archive/2026_07/tradfi_manifest_canonicalisation_2026_06_01.md` (was: `tradfi_manifest_canonicalisation_2026_06_01`) — FOLDED→M-1, archived 2026-07-13 (finding 197)                                 | TradFi single-walk (v9 + partition + source re-consol)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | `data_completion_tradfi_2026_07_15` (M-1 split 2026-07-15) (was: M-1 folded scope; was: vm-tradfi (slot-6))         | G0 + G1                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| G2       | `plans/archive/2026_07/downstream_services_manifest_canonicalisation_2026_06_01.md` (was: `downstream_services_manifest_canonicalisation_2026_06_01`) — FOLDED→M-1, archived 2026-07-13 (finding 197)       | MDPS/features/strategy/execution `_index` canonical                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | data_completion_to_100_all_ag_2026_06_21 (M-1, folded scope) (was: vm-ml)                                           | G0 + G1 + the AG MTDS walks                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| G2       | `plans/archive/2026_07/solana_defi_legacy_migration_2026_05_27.md` (was: `solana_defi_legacy_migration_2026_05_27`) — COMPLETE (0/32 open), archived 2026-07-13 (finding 197)                               | DeFi Solana legacy→canonical (serialise with defi §C)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | n/a — shipped complete, no live owner (was: vm-defi)                                                                | defi G2 single-walk                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| G2       | `features_input_manifest_migration_2026_05_25`                                                                                                                                                              | features input `_index` migration                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | vm-ml                                                                                                               | G0 + downstream                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| G2       | issue `defi_code_codex_drift_2026_05_27`                                                                                                                                                                    | DeFi code↔codex drift (wrapped by defi plan §A/§F)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | vm-defi                                                                                                             | wrapped → defi G2                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| G2       | issue `features_service_defi_data_loading_blockers_2026_05_29`                                                                                                                                              | features DeFi e2e data-layer (wrapped by defi §C0/§D)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | vm-defi/vm-ml                                                                                                       | defi G2 + downstream                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| G2       | issue `cefi_processed_candles_manifest_file_disconnect_2026_05_25`                                                                                                                                          | CeFi processed-candles manifest disconnect                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | vm-cefi                                                                                                             | cefi G2                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| G2       | issue `candle_feature_canonical_path_divergence_2026_07_20` (8-phase epic, workflow wvyttno6s)                                                                                                              | `processed_candles/` PATH shape — all AGs (add `instrument_type=`, backfill/normalise `pipeline_mode=`, fix empty-stem + split-brain + TradFi leaf-id defects; data_type axis UNCHANGED = SOURCE). DISJOINT prefix from `raw_tick_data/` (no object collision with the running raw-tick G2 walks) but shares manifest-shard write contention — sequence the P7 apply AROUND the raw-tick fleet's completion, not mid-flight. P1 writer + P3 readers landed + QG-green (`mdps@752eaff`, `mdps@2d720b4`, `features@99d5554e`, `uta@8377c98`); -test- GATE PASSED 2026-07-21 (path==manifest proven on a real GCS object). | P5 executor SHIPPED (`mdps@6ce1a25`, adversarial-reviewed — caught+fixed a critical sharding/dedup bug pre-prod)    | P0 census DONE 2026-07-22 (`deployment-service@865d0f9` launcher, all 4 AGs, ~10.9M objects, ORPHAN=0 everywhere — full disposition table in the issue doc); raw-tick fleet also fully drained. Prep risk items DONE 2026-07-22: resume checkpoint (`mdps@efa559a`+`deployment-service@0ed7cf5`, adversarially reviewed — caught+fixed 4 real findings incl. a CRITICAL silent-skip bug and a launcher VM_NAME-pinning gap pre-prod) + CEFI wire-symbol/hyperliquid-pipeline-mode/KRAKEN-SPOT classifier fixes (`mdps@6b9ee49`, todos 14/17/18). **Operator explicitly authorized P6→P7→P8 this session (+ `/autonomous`); P6 drain+consolidate DONE 2026-07-22; P7 launcher category shipped (`deployment-service@3af1a67`, 3 real bugs found+fixed via adversarial self-testing); DEFI real `--apply` canary (LIMIT=200, VM `canonical-migration-defi-cdlap-20260722-175209`) IN FLIGHT — check its terminal status before any further P7 action, see issue doc.** |
| **G3**   | (data-status §B in each per-AG plan) + **M5** in the G0 plan                                                                                                                                                | deployment-api/UI = ONE UNION view across pipeline modes + 4-state + pipeline_mode/source drilldowns                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | vm-cross-cutting + per-AG                                                                                           | G0 (M5) + G2 readers union-aware                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **G3.5** | `migration_verification_orphan_safety_2026_06_10`                                                                                                                                                           | **pre-apply verification harness (⑬–⑲ + G4.5)** — canonical possible-manifest registry (CF-15) · catalogue-seeded denominator + CeFi/Pred enumerator stubs (CF-16) · bidirectional orphan sweep + bucket prefix taxonomy + sizing (CF-17) · schema-attribute completeness (CF-18) · candle edge-timestamp (CF-19) · projected-manifest preview (CF-20) · verified-delete (CF-21); audit `migration_orphan_safety_goalpost_verification_2026_06_10`                                                                                                                                                                      | vm-cross-cutting (slot-3: V0 + scaffolds + cefi/pred) + vm-defi/tradfi/sports (slot-2: per-AG runs)                 | G3 ∧ V0 registry GREEN; **HARD-BLOCKS G4**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| **G4**   | per-AG `*_manifest_canonicalisation` **`--apply`** items + `bucket_name_ssot` L6 delete                                                                                                                     | irreversible manifest + data/schema migration                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | per-AG                                                                                                              | **G0 ∧ G1 ∧ G2 ∧ G3 ∧ pre-migration drain**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| **G5**   | `mtds_backfill_phase3` · `mdps_backfill_phase3` · `features_backfill_phase3` · `instruments_backfill_phase3` · `aws_cloud_toggle_and_backfill_parity_2026_05_22`                                            | resume backfills → 100% honest coverage                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | per-AG                                                                                                              | **G4 GREEN for that AG**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ∥        | `ci_canonical_v2_migration_2026_05_29` · `mdps_pure_polars_migration_2026_05_28` · `global_ledger_pnl_attribution_migration_2026_06_01` · `planning_vm_canonical_bringup_and_topology_reconcile_2026_06_05` | parallel infra/CI/ledger — tracked, NOT on the migration critical path                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | various                                                                                                             | parallel-safe                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |

## G1 expanded — IS catalogue is the ROOT of all missing-data understanding (operator 2026-06-07)

> **Extracted verbatim 2026-07-24 → `is_catalogue_g1_root_audit_log_2026_07_24.md`** (line-cap remediation split,
> `/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md` #16) — the full G1-ENUM/G1-V8 shape-aware-producer
> audit trail, Era-B canonicalisation, the over-fan false-candidate finding, and the "two G1 long poles" analysis (9
> todos) now live there verbatim. This coordinator retains only the G1 row in the Gate-State Board + Sub-plan registry
> above.

## Audit framework — the canonical PRE-APPLY READINESS AUDIT (①–⑫, per-AG, the LAST gate before `--apply`)

> **This is the SSOT prompt each slot (2–6) runs on its AG before the real `--apply`.** Per-CF detail:
> `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md` (**CF-1…CF-14**) + each AG's
> `*_master_audit_instructions.md` (all aligned to this audit 2026-06-08). Run on **real-prod data-state** (gcloud
> storage / cf_manifest_audit), never code constants. Each point GREEN, **sampled-vs-walked stated**, conclusion
> **"REGRESSION RISK: NONE / \<listed\>"**. The fleet is DRAINED + snapshotted (see drain section) — this is the final
> gate; a miss corrupts prod data.

1. **① Migrator dry-run** — `migrate_<AG>_v9_canonical --dry-run`: v9 · `asset_group=` · **source-aware
   `pipeline_mode=batch_<source>/` in PATH + COLUMN** (not coarse `batch`) · `source`+`transport` populated ·
   `available_at` per-row (no lookahead) · typed `data_type`/`EmptyConfirmedReason` · **Era-B relabel** (legacy
   `data_type=options_chain/ futures_chain` → `instrument_type=…`+`data_type=trades`; legacy-read retirement = the
   migrator's FINAL ATOMIC step).
2. **② Manifest-rebuild dry-run** — `rebuild_<AG>_manifest` via `derive_pipeline_mode_for_row` (no coarse default);
   agrees with the migrator stamping.
3. **③ 4-state pre-flight** — on EVERY service IS→MTDS→MDPS→features→strategy→execution, on the AG's real buckets
   (captured/empty_confirmed[typed]/attempted_failed/expected_unattempted; materialised by writer, READ by consumers).
4. **④ Empty/partial honest** — zero-vol/NaN/stale-last-price/zero-rows/pre-genesis/pre-launch/out-of-coverage →
   data-type-dependent TYPED reason (never silent placeholder) + every DOWNSTREAM consumer handles it (no crash, no
   false-captured).
5. **⑤ Read/write paths match** — every reader (MTDS/MDPS/features/strategy/execution/deployment-api) **PREFIX-matches
   `pipeline_mode=batch_*/`** (+ live*\*/replay*\*); NO exact-coarse `batch/` probe survives. `rg` → 0 coarse-exact
   hits.
6. **⑥ IS+UAC guardrail vs impossible cells** — the `(instrument_type × data_type)` validity matrix + bundle-grain
   REJECT cells that cannot exist (PERPETUAL×options_chain, per-leaf OPTION/COMBO, pre-genesis, unscheduled fixture).
7. **⑦ deployment-api/UI numerator+denominator = COULD-EXIST universe** — denominator = IS×UAC×upstream-availability
   could-exist (catalogue + `enumerate_expected_universe` seed) incl. `expected_unattempted` where the
   instrument/fixture EXISTS but its data backfill hasn't run; G3 UNION view computes coverage % from the **4-state
   union across pipeline_mode × source** (never raw-rows, never re-derived genesis/launch).
8. **⑧ IS-catalogue completeness (CF-14)** — `build_instrument_catalogue` ⊇ the manifest present-set (no missing
   instruments/leagues → no falsely-high coverage); daily catalogue scheduler wired for the AG.
9. **⑨ pipeline_mode source-aware (CF-13)** — no coarse `batch`/blank anywhere the AG writes;
   `source_string_for(pipeline_mode)==source` (C-#6 cross-check); `transport` column populated; multi-source via union.
10. **⑩ Era-B on-disk** (cefi/tradfi chains) — GCS byte-probe a recent chain shard: `options_chain`/`futures_chain` only
    as `instrument_type=`, `data_type=trades`, `pipeline_mode=batch_<source>`,
    **`data_type=(options_chain|futures_chain)` count = 0**. (defi/sports/prediction: confirm N/A or the AG equivalent.)
11. **⑪ ★ BATCH = LIVE SYMMETRY — the no-regression keystone**: prove the LIVE writer and the MIGRATED batch data emit
    the IDENTICAL canonical v9 form (schema · data_types · fields · source-aware pipeline_mode · Era-B
    instrument_type/data_type split · `available_at` derivation top-source live==batch). NO split between live-written
    and migrated-batch data, NO live-only data_types, NO read-time `available_at`. Any divergence = a post-migration
    regression → FIX it.
12. **⑫ Rollback ready** — `_index/snapshots/pre_migration_2026_06_08.parquet` exists for the AG buckets (drain done);
    the `--apply` abort path restores it; `ASSET_GROUP_CONFIG[<AG>].prefix_tpls` cover the v9 path shape (phantom-audit
    rule — uncovered templates flip real captured→attempted_failed on apply).

## 🟢 CROSS-CUTTING PRE-APPLY AUDIT VERDICT (A–H) — vm-cross-cutting / slot-7, 2026-06-08

> **Extracted verbatim 2026-07-24 →
> `/plans/archive/2026_07/master_data_canonicalisation_migration_catalogue_history_2026_07_24.md`** (line-cap
> remediation, `plans/active/task_template.md` §3 finding J) — the full A–H evidence table
> (UAC/UTL/enumerator/migrator/readers/G3-union/consolidator/batch=live, all 🟢, ~596 targeted tests) + the closed F-X1
> finding now live there verbatim. **VERDICT: A–H all 🟢, REGRESSION RISK: NONE** (unchanged).

## vm-defi (slot-2) status + findings — 2026-06-07

> **Extracted verbatim 2026-07-24 → `defi_migration_audit_log_2026_07_24.md`** (line-cap remediation split,
> `/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md` #16) — the full G2-defi readiness verdict, DeFi
> APPLY-READY verdict, PRE-APPLY ①–⑫ audit, data_type MIGRATION-COVERAGE matrix, and ORPHAN-COVERAGE drilldown (23
> todos) now live there verbatim. An exact ~160-line verbatim-duplicated verdict block found within this section
> (byte-identical, verified via `diff`) was de-duplicated during the extraction — zero content was lost. This
> coordinator retains only the DeFi rows in the Gate-State Board + Sub-plan registry above.

## Orphan sweep (2026-06-07) — every active data-layer plan/issue is registered above

- Swept `plans/active/*.md` + `plans/active/issues/*.md` for manifest/migration/catalogue/pipeline_mode/backfill/
  coverage/schema themes. **All registered above** — 0 orphans in-theme at sweep time.
- **Superseded epics flagged** (already banner-marked in `plans/epics/`): `manifest_evolution_SUPERSEDED_2026_05_21` +
  `manifest_migration_SUPERSEDED_2026_05_21` — do NOT reference; the live epic is `epics/manifest_master.md`.
- Re-run the sweep at every gate promotion (a new active plan touching the data layer with no registry row here is
  review-blocking).
- **Sync 2026-07-12** (finding 131, §A2 B-queue ruling):
  `plans/archive/issues/manifest_index_read_oom_canonical_cache_2026_06_24.md` (`parent_epic: manifest_master`, status
  was open, created 2026-06-24 — after this sweep) had no registry row here despite being in-theme (cross-cutting
  manifest-read/backfill defect); no re-sweep ran at the intervening G4 gate-promotion (2026-06-29). Registered now: it
  is separately and correctly tracked as open/ACTIVE/KEEP in
  `plans/archive/issues/plan_issue_epic_consolidation_2026_06_30.md:266` (A1.8, doc archived 2026-07-28), so no orphan
  work is lost — this is an index-completeness correction only, not a new action item. **Since resolved + archived
  2026-07-28** (`unified-trading-library@0db19a72`).

## Master coordination todos (this plan's OWN work — pure coordination, no execution)

- [x] [UAC] [IS] P1. **G1-ENUM present-set asymmetry — combo/chain underlyings get PHANTOM
      `(options_chain|futures_chain, trades)` `expected_unattempted` seeds (CROSS-AG: tradfi + cefi; found slot-6
      2026-06-08 tradfi pre-apply audit).** `enumerate_expected_universe.py` rolls the CATALOG's option/combo leaves up
      to a per-underlying `options_chain`/`futures_chain` bundle candidate with `data_type=trades`
      (`_rollup_bundle_grain`, `:1132`), but `_build_present_set` (`:1405`) loads the manifest **VERBATIM** (7-tuple
      `venue/chain/data_type/instrument_type/instrument_id/league_id/date`, no rollup). So for an underlying the WRITER
      captured as `instrument_type=combo`/`data_type=ohlcv_1m`, the seed key
      `(venue,'',trades,options_chain,underlying,'',date)` can NEVER match the present key
      `(venue,'',ohlcv_1m,combo,instr_id,'',date)` → the set-difference seeds a PHANTOM `expected_unattempted` cell AND
      the captured combo data is not credited to it → the gated G1.run could-exist denominator INFLATES + the `trades`
      coverage % DEFLATES (⑥/⑦). Verified against real-prod `market-data-tick-tradfi-prd/_index` (144,062 rows):
      `('combo','ohlcv_1m')`=50,414 · `('combo','trades')`=7,829 · `('futures_chain','ohlcv_1m')`=8,743 ·
      `('options_chain','ohlcv_1m')`=1,906. **Deeper model gap**: the validity matrix gives `combo→frozenset()` and
      `options_chain/futures_chain→{trades}` ONLY, yet the writer captures combo + chains WITH `ohlcv_1m`+`tbbo` too →
      ~61K real captured tradfi cells the matrix marks "impossible" (no guardrail rejects them today — the matrix is
      only applied to the catalog seed side, NOT to captured rows — so no data is dropped, but the model + reality
      disagree). **🔔 CEFI/TARDIS extension (operator 2026-06-08): tardis options_chain bundles may carry
      `derivative_ticker` (mark IV / greeks) + `book_snapshot_5` as DISTINCT data_types beyond `trades` — the SAME
      matrix-too-narrow gap but with FIRST-CLASS IV data. The path-only migrator preserves it byte-for-byte (no loss),
      but the could-exist SEED + any matrix-driven consumer must ADMIT these chain data_types, not just `trades`. slot-3
      (cefi) verify: probe `market-data-tick-cefi-prd` chain shards for `data_type=derivative_ticker` under
      `instrument_type=options_chain/futures_chain` and widen
      `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE[("cefi", options_chain/futures_chain)]` accordingly. tradfi
      (Databento) chains carry only `{trades, ohlcv_1m}` (no IV) — so the IV slice is cefi-specific.** **SCOPE: the
      gated G1.run `--apply-write` SEED only — NOT the G4 data/manifest `--apply`** (that walk is content-preserving;
      tradfi/cefi v9 DATA migration has ZERO regression from this; cefi's low candidate count (3,454) means its phantom
      is small because cefi captures `options_chain` bundles that DO cancel — tradfi's combo-dominant present-set is the
      exposed case). **Quantify first**: re-run `enumerate --asset-group {tradfi,cefi} --dry-run` with an
      `instrument_type` breakdown to count the phantom `(options_chain|futures_chain, trades)` cells. **Fix options
      (owner decides)**: (a) apply the SAME `_rollup_bundle_grain` normalization to the present-set before the
      set-difference (symmetric); (b) writer/rebuild relabel `combo`→`options_chain` to match the seed; (c) admit
      `ohlcv_*`/`tbbo` for chain instrument_types in the validity matrix. **round5-cross-cutting-audit 2026-08-08:
      RESOLVED — option (a) already implemented, not just chosen.**
      `instruments-service/scripts/enumerate_expected_universe.py:3625` `_rollup_present_bundle_grain` (docstring:
      "G1-ENUM present-set symmetry fix, option (a)"), wired into the present-set build + phantom-cell diff. Production-
      quantified (fixed cefi -32 phantom cells); tradfi companion naming fix shipped+archived 2026-07-29. No owner-
      decides call needed. Owner: vm-cross-cutting / slot-7 (the central enumerate producer). Repos: instruments-service
      (`scripts/enumerate_expected_universe.py`) + unified-api-contracts (validity matrix). `parent_epic`:
      manifest_master. Provenance: tradfi pre-apply audit, slot-6 2026-06-08.

      **CLOSED 2026-08-08 (na-eligibility-audit round7)**: the round5-cross-cutting-audit entry immediately above already confirmed option (a) is shipped and production-quantified, "No owner-decides call needed" -- flipping to match, no new investigation performed.

- [x] ✅ [DOCS] P0. **M-COORD-1 — G0 doc-coherence reconcile GREEN (R6-codex closure, slot-4 2026-06-11 — pm@a28cbd4d7 +
      pm@51863c157 + pm@05456c343)**: CLAUDE.md + the codex layer (`pipeline-mode-partition.md` now carries the M1–M8
      settled-contract section, `availability-manifest-and-data-status.md` live-taxonomy reconciled) +
      `SUB_AGENT_MANDATORY_RULES.md` + **all 5 per-AG plans** acknowledge the source-aware
      `{mode}_{source}[_{transport}]` model + the apply-gate. parent_epic: manifest_master. **SSOT layer DONE
      (vm-cross-cutting 2026-06-07)**: the codex reconciliation doc, the workspace `CLAUDE.md`, and the sub-agent rules
      were rewritten to the source-aware mode/source/transport model (replay tier + hyperliquid vendor, retiring the
      glued-transport antipattern). **Per-AG-plan layer DONE (2026-06-11)**: all 5 plans' gate banners point at the
      codex settled contract; factual on-disk observations were NOT falsified — remaining coarse/ `hyperliquid_rest`
      tokens are explicitly annotated legacy-state/historical records. Seam docs
      (`tradfi/sports/prediction-batch-live.md`) shipped; `batch-live-architecture.md` §11 table GREEN for 4/5 AGs (defi
      full narrative still pending — tracked there). **Residual (non-gating, next-touch)**: the downstream/instruments
      plans' stale tokens + repointing those plans' `master:` frontmatter at this coordinator (M-COORD-2 residual).
- [x] ✅ [DOCS] P0. **M-COORD-2 — DONE (2026-06-07): gate banners added** to the DeFi §MASTER (demoted) + all 6
      cross-AG/ downstream/instruments plans (cefi/sports/prediction/tradfi `--apply` apply-gate; instruments = G1-root;
      downstream = G2). Additive banners only (slot precedence respected). **Residual (folds into M-COORD-1)**: repoint
      the `master:` FRONTMATTER field of the plans that point at `defi_manifest…§MASTER` → the coordinator, and the full
      CLAUDE.md + codex source-aware-model reconcile. parent_epic: manifest_master.
- [x] ✅ [AUDIT] P1. **M-COORD-3 — DONE (2026-06-07): CF-13 (pipeline_mode source-aware, extends CF-3) + CF-14
      (IS-catalogue could-exist ROOT, foundation of CF-6) added to `canonical_form_cross_service_audit_checklist.md`** —
      the ⑨ + ⑧ readiness checks; an AG's audit now fails RED until they hold; cross-AG ownership stays in this
      coordinator's registry (not duplicated). Residual: cite CF-13/14 in each `*_master_audit_instructions.md`
      ownership matrix on next touch. parent_epic: manifest_master.
- [x] ✅ [CHORE] P1. **M-COORD-4 — gate-state board WIRED** (pm@docs 2026-06-16): added the
      `## 🟦 Gate-State Board (G0–G5 × asset_group)` block at the top of this coordinator (above §Dispatch waves) —
      🟢/🟡/🔴 per AG, sourced from the WAVE checkboxes + the A–H cross-cutting verdict + the per-AG `G4 --apply` ticks,
      with a per-cell basis + a refresh note (re-read at each gate promotion, or `regenerate_active_plan_inventory.py`).
      Current state: G0🟢 G1🟢(dry) G2🟡 G3🟢 G4🟡(operator-gated) G5🔴 across all 5 AGs. parent_epic: manifest_master.
- [x] ✅ [DEFI] P1. **M-COORD-5 (DeFi slice, slot-2) — DONE mtds@f80c50f1**: `rebuild_defi_manifest.py`
      `writer.add(...)` now passes `asset_group=defi` + the source-aware `pipeline_mode` + `source` + `transport` (no
      more blank `pipeline_mode`/`source` — standardisation finding #1 resolved); migrator likewise stamps source-aware
      in path+column. Tests green 25/25. Repo: market-tick-data-service. parent_epic: mtds_mdps_master.
- [x] ✅ [CROSS-CUTTING] P1. (mtds@7455ffb 2026-06-11: `rebuild_tradfi` (direct read :316) + `rebuild_prediction` (via
      `reemit_honest_absence_rows`) + `rebuild_defi` (defensive — unguarded `log_event` via `ManifestWriter.add`
      validation); cefi/sports pre-existing; the 5 `migrate_*_v9` movers + IS `migrate_instruments_store_v9` VERIFIED
      no-manifest-read → not needed) **M-COORD-6 — every AG `rebuild_*_manifest*` / `migrate_*_v9` script must
      `setup_events()` before reading the manifest (surfaced + fixed-locally for sports by slot-4 pre-apply audit
      2026-06-08; sports ship gated on M-COORD-7).** ROOT CAUSE: `read_availability_index()` → `_backfill()` emits
      `READER_BACKFILLED_V8_COLUMNS_AS_NULL` via `log_event` whenever the per-VM fallback shards carry pre-v9 columns —
      the **GUARANTEED drained-fleet pre-migration state** (consolidated index stale → per-VM fallback → v8 shards).
      Without an events init, `log_event` raises `RuntimeError: Event logging not initialized` and **crashes the rebuild
      `--no-dry-run` apply**. The v8-era migration scripts ALL call `setup_events(mode="local", sink=None)` in `main()`
      (`migrate_sports_canonical`/`migrate_defi_canonical`/`migrate_tradfi_canonical`/
      `migrate_polymarket_canonical`/`migrate_sports_hive_key`); the **newer v9 scripts dropped it**.

      Confirmed MISSING in: `rebuild_defi_manifest.py`, `rebuild_cefi_manifest*`, `rebuild_tradfi_manifest*`,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              `rebuild_prediction_manifest.py`, `migrate_defi_full_v9_canonical.py`, `migrate_tradfi_to_v9_canonical.py`, and
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              IS `migrate_instruments_store_v9.py` (the ones that call `read_availability_index`). **Fix per AG-slot**: add
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              `setup_events(service_name="...", mode="local", sink=None)` at the top of `main()` (mirror the sports fix;
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              migrators that do pure object-path moves and never read the manifest — e.g. `migrate_sports_canonical_v9` — do
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              NOT need it). Each AG slot owns its own script's one-liner. Repos: market-tick-data-service +
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              instruments-service. `parent_epic`: mtds_mdps_master. Provenance: slot-4 sports pre-apply audit 2026-06-08.

- [x] ✅ [DEFI] [CROSS-CUTTING] P0. **M-COORD-7 — DeFi LIVE handlers + engine catalog readers still write COARSE
      `pipeline_mode="batch"` (NOT source-aware) → batch≠live for DeFi AND blocks EVERY mtds code ship via STEP 5.85
      (surfaced by slot-4 sports pre-apply audit 2026-06-08).** The C-PATH inventory above marked the DeFi **migrator +
      rebuild** ✅ source-aware (mtds@f80c50f1) but the **41 inline `pipeline_mode="batch"` literals in the DeFi LIVE
      WRITE path** were NOT swept: ~29 `cli/handlers/*`
      (`perp_funding/position_data/lst_rates/gas_fee/liquidations/flash_loan_events/native_staking/eigenlayer_rewards/bridge_events/jupiter_quote/oracle_prices/orca_whirlpool/phoenix_orderbook/raydium_classic_amm/solana_defi/staking_yields/token_transfers/vault_share_price/websocket_streaming/mev_events/governance_*/lending_indices/aggregator_route/protocol_outage_detector`/…),
      the 5 `engine/__catalog_reader.py`, + tradfi `massive_tradfi_rest_connector`/`tardis_adapter` + clients
      (`alchemy_*`/`extended_base`/`tardis_base`/`thegraph_base`).

      Each is commented "Coarse ingestion mode → canonical pipeline_mode= path segment (Live=Batch)". **TWO
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              consequences**: (1) **batch≠live REGRESSION for DeFi** — DeFi live-written data lands at `pipeline_mode=batch/`
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              (coarse) while migrated DeFi batch data lands at `pipeline_mode=batch_<source>/` (source-aware mtds@f80c50f1) →
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              the migration CREATES a split the audit's ⑪ keystone forbids; (2) **STEP 5.85
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              (`no-inline-pipeline-mode-string-literal`, added pm@28698c856 2026-05-28) hard-fails → mtds
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              `quality-gates.sh` exits non-zero → NO `.qg_last_passed_sha` written → `quickmerge --agent` refuses → NO mtds
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              code (any AG) can ship** (it currently blocks slot-4's verified sports `setup_events` fix). **FIX (slot-2 DeFi +
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              cross-cutting)**: each handler/reader must pass the SOURCE-AWARE `PipelineMode.<BATCH_SOURCE>` (or
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              `derive_pipeline_mode_for_row(venue, ag, data_type)`/`resolve_pipeline_mode()`), the SAME value the v9 migrator +
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              the shared `engine/orchestrator.py` write path use, so DeFi live == DeFi migrated-batch. Per-handler source
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              derivation is DeFi-domain (the handler knows its venue/source) — slot-4 did NOT edit (collision + correctness
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              risk across 41 DeFi sites). Repo: market-tick-data-service. `parent_epic`: mtds_mdps_master. Provenance: slot-4
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              sports pre-apply audit 2026-06-08 (this is a NEW DeFi readiness blocker — it is NOT in the DeFi APPLY-READY
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              verdict above, which covered migrator/rebuild but not the live handlers).

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              **✅ RESOLVED 2026-06-17 (mtds@c4c5f15) — verified, not the stale "already shipped" note (line 240, which over-claimed
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              the STEP-5.85 grep-clean surface).** The COARSE-literal consequence (#2, STEP 5.85) was already closed by the
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              sibling item @1727 (mtds@57242af5, 41 batch literals swept → `rg "pipeline_mode=\"live\"|\"batch\"" --type py` = 0 in
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              mtds non-test source). The REMAINING live-path batch≠live split (#1) was the runtime coarse `"live"` from each
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              handler's `_pipeline_mode_for(run_tag)` passing through to `write_defi_rows` — `canonical_write.py:138` only upgraded
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              `None`/`"batch"` → `batch_<source>`, so a live `dex_swaps`/`_dex_pools_subgraph` run landed at `pipeline_mode=live/`
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              (coarse) vs the migrated batch corpus's `batch_<source>/`. **FIX**: extended the `canonical_write` chokepoint to
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              upgrade coarse `"live"`/`"replay"` → source-aware `live_<source>`/`replay_<source>` via the SAME UAC source map
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              (`live_pipeline_mode_for_venue`) the batch branch derives from. Verified symmetric: `batch_onchain_subgraph` ↔
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              `live_onchain_subgraph`; +regression test `test_live_run_tag_stamps_source_aware_live_mode`. Coverage confirmed: the
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              DeFi DATA writers (`dex_swaps`, `_dex_pools_subgraph`) all route coarse values through `write_defi_rows` (chokepoint
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              catches them); `websocket_streaming_handler` already used `live_pipeline_mode_for_venue` (source-aware); the engine
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              `*_catalog_reader.py` carry NO coarse literal on HEAD. **Residual (P2, NON-blocking — not coarse, so out of this
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              item's scope)**: `dex_pools_handler.py` honest-absence `recorder.record_failed(...)` calls hardcode the SOURCE-AWARE
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              `PipelineMode.BATCH_ONCHAIN_SUBGRAPH` (mode-fixed, not coarse) — on a live `dex_pools` run a FAILURE row would carry
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              the batch mode-label; the DATA shards are correct (the keystone the migration walks). Tracked below.

- [x] ✅ [DEFI] P2. **`dex_pools_handler` honest-absence `record_failed`/`record_*` calls hardcode mode** — they passed
      `pipeline_mode=PipelineMode.BATCH_ONCHAIN_SUBGRAPH` (source-aware but mode-fixed) at
      `dex_pools_handler.py:410/467/475/486`. On a live `dex_pools` run these `attempted_failed`/honest-absence rows
      mislabel the mode (batch vs live). **DONE 2026-06-17 (mtds@d5cf763) — operator confirmed "we have live for defi"
      so this IS live-reachable.** Added `_record_pipeline_mode_for(venue, run_tag)` helper applying the SAME
      source-aware upgrade as the data chokepoint (`canonical_write.py` mtds@c4c5f15): live →
      `resolve_pipeline_mode(..., "live")` = `live_onchain_subgraph`, batch → `derive_pipeline_mode_for_row` =
      `batch_onchain_subgraph` (no batch regression). All 4 `record_*` calls now use it; +regression test. Repo:
      market-tick-data-service.

## Demotion + linkage record

- `defi_manifest_canonicalisation_2026_06_01.md` (folded→M-1, archived
  `plans/archive/2026_07/defi_manifest_canonicalisation_2026_06_01.md` 2026-07-13, finding 197) `## MASTER` section →
  demoted to **DeFi executor**; a banner points UP to this coordinator (its cross-plan registry is superseded by the
  table above).
- `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` → registered as **G0** (keeps its Phase-0
  apply-gate; this master references it, does not duplicate it).
- `master_to_live_defi_2026_05_23.md` → **downstream consumer** (G5 → live promotion); cross-linked, not subsumed.

## Verification (full-execution criterion)

This coordinator is COMPLETE-as-a-coordinator when: (1) every active data-layer plan/issue has a registry row + a
blocked-until edge; (2) the G0 doc-reconcile (M-COORD-1) is GREEN so no per-AG plan/codex doc contradicts the
source-aware model; (3) the audit SSOT carries ⑧+⑨; (4) the gate-state board reflects the registered plans' real state;
(5) 0 orphans. The migration itself is done by the registered sub-plans — this plan just proves they are correctly
sequenced and nothing is unblocked-out-of-order or orphaned.

## Progress Log

- **context-scout 2026-08-05 (slot-14)**: line-cap remediation pass 3 — extracted the closed R5 smoke ledger (~125
  lines, every todo done, one-time probe data from 2026-06-11) to
  `/plans/archive/2026_08/master_data_canonicalisation_migration_catalogue_r5_smoke_ledger_history_2026_08_05.md`;
  expanded `context_scope` from 2→5 entries (pre-computed 2026-08-03, verified to resolve on disk).
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — fresh read of the 2 remaining coordinator-only todos: item 1 is
  a future-gated bookkeeping placeholder ("assign to slots when reached"), item 2 is a 3-way unresolved architecture
  design call (owner decides among (a)/(b)/(c)); doc's own role is "a PURE COORDINATOR — executes nothing" (operator
  2026-06-07).
- **context-scout 2026-08-07**: populated/refreshed context_scope (5 entries) — re-verified all 5 still resolve
  (including the instruments-service source path, a false-negative on a relative-path check first suggested it moved);
  unchanged.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — re-confirms 2026-08-06; the 2 remaining coordinator-only todos
  are unchanged: a future-gated bookkeeping placeholder (WAVE 5 live-side, "assign to slots when reached") and a 3-way
  unresolved architecture design call (G1-ENUM present-set asymmetry fix, "owner decides" among 3 named options). Doc's
  own stated role is "a PURE COORDINATOR — executes nothing" (operator 2026-06-07).
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, stale item closed -- flipped the G1-ENUM
  present-set asymmetry checkbox (option (a) confirmed shipped per this doc's own round5-cross-cutting- audit entry).
  Remaining open todo (WAVE 5 / live-side) is a future-gated bookkeeping placeholder ("assign to slots when reached") --
  doc's own stated role is "a PURE COORDINATOR -- executes nothing" (operator 2026-06-07), stays NA.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).

## Deferred work — migrated to:

**Corrected by plan_reconciler 2026-08-10 — both entries below were stale.** This section predates the 2026-07-24
line-cap remediation that shrank this file (the old `line ~1247/~1250` self-citations no longer resolve to anything in
the current 919-line file), and neither successor claim matched live corpus state on a fresh check.

1. G1.run-prediction (cqg-bundle-grain seed, decision 338 / `predictions_master` Phase 3): the cited successor,
   `prediction_cqg_residual_2026_07_24.md` todo 2 ("249-b"), is now DONE. That doc shipped both its todos 2026-07-29 and
   archived to `plans/archive/2026_07/prediction_cqg_residual_2026_07_24.md` (`status: complete`, `superseded_by:` empty
   — a completed record, not an ongoing successor). Migrated to: nothing further needed, this item is closed.
2. G1.run-full-history (extend the bounded-window seed to 2018→today): this line claimed the item "remains an active
   tracked todo within this coordinator" — false today. This doc's only open checkbox is the unrelated WAVE 5 live-side
   item. The real G1.run-full-history work moved to `is_catalogue_g1_root_audit_log_2026_07_24.md` (the 2026-07-24 G1
   extraction), and from there was extracted again 2026-08-09 to
   `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` (line 502, open, citing
   `is_catalogue_g1_root_audit_log_2026_07_24.md` by name). Migrated to:
   `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`.
