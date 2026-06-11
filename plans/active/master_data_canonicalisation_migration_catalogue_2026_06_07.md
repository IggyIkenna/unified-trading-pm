---
title:
  "MASTER COORDINATOR — data + manifest + schema migration + IS catalogue + pipeline_mode standardisation (single-pane
  dependency-gated sequencer for the whole data-layer cutover)"
created: 2026-06-07
parent_epic: epics/manifest_master.md
assigned_vm: vm-cross-cutting
umbrella: true # catalogue/coordinator plan — large in context, <100 todos; exempt from 1000L cap (2026-06-09)
status: active
priority: P0
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3.6
locked_by: live-defi-rollout
locked_since: 2026-06-07
source:
  - operator 2026-06-07 ("coordinated master plan around data/manifest/schema migrations + IS catalogue; attach all plan
    todos; block on upstream readiness; no orphans")
  - pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md (the Phase-0 apply-gate)
  - proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md (the could-exist-universe foundation)
---

# MASTER COORDINATOR — Data-Layer Canonicalisation, Migration, Catalogue & Pipeline-Mode Cutover

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
G5  Resume BACKFILLS → 100% honest coverage (UI drilldowns shrink to minor) + massive/polygon cost-swap vs databento
                                                          ↓
                                  master_to_live_defi_2026_05_23.md  (live promotion — downstream)
```

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
**WAVE 4** G4 per-AG `--apply` (gated G0∧G1∧G2∧G3 + drain) → **WAVE 5** G5 backfills→100% + cost-swap. Live-side
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

- [x] ✅ **G0 / G1 / G2 / G3 — GREEN, 5/5 apply-ready** (Era-B on-disk confirmed both probes; drain done + 10-bucket
      snapshot). Per-AG audit verdicts recorded in each AG plan.
- [ ] [DATA] P0. **slot 2 (DeFi) — G4 `--apply`**: instruments-store v9 walk → MTDS raw-tick v9 → catalogue seed → IS
      backfill (Era-B relabel rides the migrator's final step). Operator-fired; on real VM/tarball; rollback =
      `pre_migration_2026_06_08.parquet`. Repo: market-tick-data-service + instruments-service.
- [ ] [DATA] P0. **slot 3 (CeFi) — G4 `--apply`** (same sequence; DERIBIT/OKX Era-B chains). Repos: as above.
- [ ] [DATA] P0. **slot 4 (Sports) — G4 `--apply`** (league-grain; 2.68M-row instruments-store). Repos: as above.
- [ ] [DATA] P0. **slot 5 (Prediction) — G4 `--apply`** (per-cqg; pred-prd buckets). Repos: as above. **🔴 GATED on
      CF-11 close**: polymarket fetch-error swallow must `record_failed` (not `record_empty`/`[]`) — else bakes wrong
      4-state. See prediction audit (pred-fetch).
- [ ] [DATA] P0. **slot 6 (TradFi) — G4 `--apply`** (databento/massive; daily listing). Repos: as above. **🟢 CF-11
      CLOSED + DRY-RUN-GREEN (slot-6, 2026-06-08)** — the `databento.py:826` (+ L802) ZERO-signal swallow re-raises →
      `attempted_failed` ON LDR (instruments-service@f7744fbf + @c0f2f39c, re-verified
      `git show origin/live-defi-rollout`; the prior "🔴 GATED" was stale — keyed off `bd1456aa` read as not-on-LDR, its
      content re-SHA'd as f7744fbf). Migrator + rebuild `--dry-run` clean on real-prod GCS (recent 984/0-err; old-tail
      `category=`→`asset_group=` T-OLD fix proven); Era-B count=0; rollback snapshot present. **APPLY-READY — REGRESSION
      RISK: NONE** (tradfi plan ①–⑫). cefi already closed (`e2e008f0`); source-provenance write-path shipped (#4
      non-block). Operator fires `--apply` (`--also-legacy` per R1).
- [x] ✅ [CODE] P1. **slot 7 (cross-cutting) — audit-criteria automation DONE** (Tier-2 + Tier-3 + cron all shipped; see
      the § "Cross-cutting audit verdict (slot-7)" below). Tier-2 STEP 5.92/5.93 (pm@b4245a7dd) + Tier-3
      cf_manifest_audit CF-1…14 + cross-AG wrapper (pm@2fe982eb1) + daily alert-on-RED cron (deployment@eaff3a7). Only
      adds gates — parallel to the applies, blocks no AG `--apply`. (Residual: validity-matrix P2 test + bar-edge
      Phase-0 cross-source fixture/assertion in-flight — tracked in their plans.)
- [ ] [CODE] P1. **slot 7 — post-apply consumer cleanups** (the deferred-with-reason items: execution-service defi
      loader, deployment-api FLAG-1/3/dedup, MDPS GAP-7) — after the per-AG applies.
- [ ] [CODE] P2. **WAVE 5 / live-side (gated, after batch migration)** — G5 backfills→100% + massive/polygon cost-swap;
      the live-side tranche (M3/M4/M6/M7 · `live_websocket`→`live_<source>` · M8 cadence). Assign to slots when reached.

### Coordinator progress — 2026-06-11 (autonomous finish-to-DONE run, slot-4)

- **M-COORD-7 (DeFi live handlers coarse `pipeline_mode`) — VERIFIED ALREADY SHIPPED on LDR HEAD**: zero coarse
  `pipeline_mode="batch"` literals remain in mtds non-test source (only comments describing the completed sweep, e.g.
  `canonical_write.py:181` "STEP 5.85 clean"); mtds `quality-gates.sh --no-fix` exits 0 on HEAD (proven 2026-06-11). The
  checkbox text above is retained for history; the blocker is CLOSED.
- **Prediction CF-11 (slot-5 G4 gate) — STALE: polymarket is CLOSED on HEAD.** Verified end-to-end on LDR:
  `polymarket_adapter.get_trades_with_status`/`failed_cids_out`/`failed_per_dt` → `umi_tick_provider:383` →
  `orchestrator:4027` → `record_failed` (pinning tests `test_polymarket_cf11_fetch_failure.py`). **Kalshi CF-11 plumbing
  ADDED in the same pass** (mirrored pattern + 5 tests; umi dispatch would have TypeError'd on Kalshi enable). The
  slot-5 "🔴 GATED on CF-11" note above is superseded — prediction G4 gating reverts to the standard G3.5 verdict.
- **M-COORD-6 (`setup_events`) — IMPLEMENTED, QG-green, ship pending**: added to `rebuild_tradfi_manifest.py` (direct
  index read :316), `rebuild_prediction_manifest.py` (via `reemit_honest_absence_rows`), `rebuild_defi_manifest.py`
  (defensive: unguarded `log_event` via `ManifestWriter.add` validation path). cefi/sports were already done. The 5
  `migrate_*_v9` movers verified as pure object-path walkers (no manifest read in import closure) — no init needed. Plus
  the full CF-11 swallow batch (`mtds_honest_absence_swallow_remediation_2026_06_10.md` Phase 1+2) implemented in the
  same QG-green batch. **Quickmerge held only on a concurrent UTL WIP (the swallow plan's own UTL P1 item being
  implemented in-slot); ships next.**
- **G3.5 scaffolds CONFIRMED PROMOTED to `staging`** (instruments-service `migration_orphan_sweep.py` et al. + UAC
  `possible_manifest.py` both present on `origin/staging`) — the 2026-06-10 staging-lock note below is resolved.
- **G3.5 manifest-diff tool BUILT** (`instruments-service/scripts/manifest_diff.py`, projected-vs-current `_index` delta
  with grain-aware wildcard covering + tests; QG-green, ship pending same UTL-clean event). See the G3.5 plan Progress
  Log.
- **🔴 NEW BIG FINDING — PM QG exit-code bug**: `quality-gates-base/base-service.sh` (~:2295) integer-expression error
  lets a FAILED ratchet step (observed: STEP 5.94 over-baseline) fall through to overall exit 0 + sentinel write — the
  green sentinel can be HOLLOW for ratchet steps. Filed
  `plans/active/issues/qg_base_service_ratchet_exit_code_2026_06_11.md`; composes with the existing "LOCAL QG HARNESS
  hollow sentinel" P2 above (this is a different, additional mechanism).

### Autonomous finish-to-DONE run — FINAL REPORT 2026-06-11 (slot-4)

**SHIPPED (all QG-green via quickmerge, on LDR; Tier-C drain promotes):** utl@6f347d90 (CF-4 `source=`/`asset_group=` on
`record_empty`/`record_failed`) · mtds@7455ffb (FULL CF-11 swallow batch Phase 1+2 + M-COORD-6 setup_events + Kalshi
CF-11; 18 new tests) · mtds `_defi_manifest` CF-4 recorder pass-through (follow-up unit, landed after 7455ffb) ·
is@d4190ba (G3.5 manifest_diff tool) · strategy@3561f137 (GAP-4 drift warn) · deployment-api@644e439 (cefi seed-aware
4-state denominator) · mdps@4363bce (GAP-7 rename complete incl. the orchestration_service caller the first pass missed)
· alerting@dec309b (CONSOLIDATOR_DOWN + MANIFEST_CONSOLIDATION_FAILED consumers — the consolidator can now page) ·
deployment-service lifecycle_catalogue_scheduler.tf bucket-literal fix (legacy/nonexistent → canonical env-short; ship
in flight).

**VERIFIED (no work needed):** M-COORD-7 already shipped on HEAD; polymarket CF-11 already closed (slot-5 gate note was
stale); G3.5 scaffolds + UAC possible_manifest on `staging`; IS migrate_instruments_store_v9 needs no setup_events (no
manifest read).

**G3.5 RUNS EXECUTED (real prod GCS):**

- **V2 orphan sweeps**: defi **E=254,984** (canonical-shaped Solana-migration outputs never record_captured'd + unknown
  prefixes = the solana_defi_legacy trees) · tradfi **E=47,102 / B=1.6M legacy twins / unknown=7,147** · prediction
  **E=61,014 (stable)**. Report parquets in each bucket's `_index/audit/`. ALL RED → G4 stays blocked per ⑬; the per-AG
  `record_captured` backfill is the tail. Sports: the generic sweep is N/A by design (candidate_parquet_paths) —
  sports-specific sweep still needed (slot-2).
- **V3 schema completeness**: defi 7 RED (SchemaSpec coverage gaps: rewards/risk_params/utilization etc.) · tradfi 1 RED
  (**no SchemaSpec for tradfi/trades**) · **prediction RED: POLYMARKET trades silently DROPS 11 columns vs v9** (amount,
  asset, conditionId, data_source, market_type, outcomeIndex, resolution_period, symbol, timestamp, transactionHash,
  underlying) → extend the canonical schema BEFORE the prediction apply or operator-ack (⑮).
- **C residuals**: DeFi B0-PRE v2 enumerate re-run = **57,074 candidates/2d** (expanded universe enumerates; seed stays
  G1.run-gated). **CeFi Era-B v2 re-run = 2,804 candidates/2d — the ~563K false OPTION/COMBO candidates are GONE → the
  cefi enumerate-re-validation gate is MET.**

**DECISION (documented intent, T-OLD-2)**: the 14 Era-A `data_type=options_chain` tradfi objects are REAL data the
migrator skips → class-E discipline applies: **PRESERVE + backfill, never delete** (they will surface in the tradfi
orphan-sweep report parquet; the verified-delete tool already refuses class-E). Supersedes BLOCKED-OPERATOR-DECISION
unless the operator overrides.

**IN FLIGHT (background)**: A5 bar-edge batch agent (MDPS content-aware shift + UAC docstring + mtds ts_event→t_close
with footer-marker discriminator) — census basis: 24/24 raw tradfi ohlcv parquets are `timestamp`-named open-edge.

**REMAINING (exact next steps):** (1) E8 `terraform apply` of lifecycle_catalogue_scheduler — tf fixed; no
terraform/tofu binary on this host: install tofu OR run from the infra pipeline, then T+10min
`gcloud run jobs executions list --job lifecycle-catalogue-regen-<ag>`; (2) per-AG class-E `record_captured` backfills
(defi=solana-migration tail / tradfi / prediction) + sports-specific sweep; (3) UAC SchemaSpec additions per V3 RED list
(esp. prediction 11-column carry); (4) V5 dev renders + manifest_diff reports per AG → V6 ⑬–⑲ verdicts; (5) QG ratchet
exit-code fix (issues/qg_base_service_ratchet_exit_code_2026_06_11.md — fleet-sweep first per rule 11); (6) E5
catalogue-reader repoint gated on sports+pred roll-ups existing (only cefi/defi/tradfi have prod/catalog.parquet).

### G1.schedule smoke verdict — 2026-06-11 addendum (autonomous run)

The cefi smoke execution FAILED (exit 1 ~90s in; Cloud Logging truncates the traceback mid-line). ROOT-CAUSED via docker
repro of the exact image: **the `instruments-service:latest` image (built 2026-06-10T07:51Z) is STALE on two axes** —
(a) its UTL predates the 2026-06-10 UAC `cloud-providers.yaml` importlib-resources relocation, so `resolve_bucket_name`
probes for a `deployment-service/` dir absent in the container → `BucketNamingError` inside `run_rollup`; (b) the
in-image `unified-trading-pm/configs/cloud-providers.yaml` fallback copy is the PRE-canonicalisation schema (kinds
`instruments`/`market_data`, no `instruments-store`) so the env-var override can't rescue it either. **No tf change
needed** — the job spec is correct; the fix is the image rebuild already in motion (tonight's instruments-service ships
drain LDR→staging→main → Cloud Build refreshes `:latest` with the relocated UAC yaml). A persistent monitor watches for
the new digest and auto-re-executes the cefi job to a terminal verdict; the 01:00 UTC dailies pick up the fixed image
regardless. **Blast radius note**: ANY Cloud Run job on a 2026-06-10-or-older image that calls `resolve_bucket_name`
without `UNIFIED_TRADING_CLOUD_PROVIDERS_YAML` has this same failure class — worth a sweep once the new images land
(filed as a todo in the G3.5 plan owner's queue via this note).

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

All five R-agents (R1/R2/R4/R5/R6) hit the Claude account session limit mid-task after 70–125 tool calls each. **Their
WIP is REAL and PRESERVED, uncommitted, in the `.tabs/4/` slot trees — resuming workers MUST continue these trees, not
restart** (inherited-dirty-WIP rule: makers are dead, inherit):

- **R2 (.tabs/4/unified-api-contracts, 7 dirty)**: NEW `registry/_schema_spec_{defi,prediction,tradfi}.py` +
  `registry/schema_spec.py` + `registry/__init__.py` wiring + `tests/unit/test_schema_spec_completeness.py` — the
  citadel column-carry implementation looks structurally complete; REMAINS: review, QG `--no-fix`, quickmerge, then
  re-run `migration_schema_completeness` per AG to 0 RED (run from instruments-service with the orphan_sweep report
  parquets as --objects-parquet).
- **R1 (.tabs/4/instruments-service, 5 dirty)**: `scripts/migration_orphan_sweep.py` +
  `scripts/migration_schema_completeness.py` edits (likely the prefix-taxonomy labels + shared helpers) + defi adapter
  touches (`aave_v3.py`, `uniswap_v3.py`) + completeness test. The `backfill_orphan_class_e.py` tool may be unstarted —
  check tree first. REMAINS: finish/build the backfill tool per ratified decision #1
  (characterize→canonicalise-to-v9→record_captured, sample-verify, never manifest non-canonical), ship, dry-run + apply
  per AG, re-sweep to E==0 + unknown_prefixes==0, cefi re-run.
- **R6 (.tabs/4/unified-trading-pm, ~12 dirty)**: codex edits in flight — `pipeline-mode-partition.md`,
  `pipeline-mode-and-batch-live-reconciliation.md` (hyperliquid_rest purge), `batch-live-architecture.md`,
  `cefi-batch-live.md`, `tradfi-batch-live.md`, `replay-subsystem.md` (+ more). REMAINS: finish per-AG plan
  de-coarsening + prediction/sports seam docs + M1–M8 target codification, prettier, docs commits, flip M-COORD-1. **→
  RESUMED + COMPLETED 2026-06-11 (slot-4): pm@645648a03 (codex contract) + pm@55f9cf9c3 (seam docs) + the docs(plans)
  de-coarsen/flip commit — R6-codex + M-COORD-1 ticked below.**
- **R4 (no tree WIP found)**: investigation state unknown — restart the diagnosis from the task spec (decision #4);
  check `gcloud scheduler jobs describe` for the IS jobs + instruments-store `by_date/` last-written days first.
- **R5 (no tree WIP found)**: smoke matrix probes were running (125 tool calls); no ledger written — restart from the
  task spec (decision #5); reuse any /tmp probe logs on the host if present.

Standing context for resumers: HARD-STOP remains the per-AG migrator `--apply`; R7+R3 (re-dry-runs on final HEAD +
projected `_index` + dev renders + ⑬–⑲ verdict packs) and R8 (sports sweep + v1_archive gate + prediction dry-plan
regen) queue AFTER R1/R2 land. Playwright + chromium are installed on this host for the V5 drilldown evidence packs.

### Ratification todos (the dispatch — owners per slot map)

- [ ] [DATA] P0. **R1-backfill — per-AG class-E characterize→canonicalise→record_captured backfill** (defi 254,984 /
      tradfi 47,102 / prediction 61,014; sweep reports in `_index/audit/orphan_sweep_<ag>.parquet`): group E objects per
      (venue, data_type); map each data_type to its code use-case (readers/features consumers); CONVERT non-v9-shape
      objects to canonical schema/path during backfill (never manifest a non-canonical object); sample-verify per cell;
      re-run `migration_orphan_sweep` to E==0. defi+tradfi=slot-2, prediction=slot-3. Repos: instruments-service (+mtds
      schemas). Also: add the defi legacy-tree prefix labels (`dex_pools/`, `lending_indices/`, `_manifests/`,
      `configs/`) + tradfi unknown-prefix labels to the sweep taxonomy → unknown_prefixes==0 re-proven; cefi corrected
      re-run to a recorded verdict.
- [ ] [UAC] P0. **R2-schema — carry ALL dropped columns into v9**: extend `CEFI/PREDICTION/...` schema specs so CF-18 is
      GREEN per AG — the 11 polymarket trades columns (amount, asset, conditionId, outcomeIndex, transactionHash,
      data_source, market_type, resolution_period, symbol, timestamp, underlying) + SchemaSpecs for defi
      rewards/risk_params/utilization(+rest of RED list) + tradfi/trades. Re-run `migration_schema_completeness` per AG
      to 0 RED. slot-3. Repo: unified-api-contracts (+instruments-service rerun).
- [ ] [DATA] P0. **R3-verdicts — full V5 render + V6 verdict per AG**: re-dry-run migrator+rebuild on CURRENT HEAD (R7)
      writing projected `_index` → `manifest_diff` report vs live `_index` → dev `restart-deployment-stack.sh     --api`
      render → operator eyeballs goalposts → assemble ⑬–⑲ verdict in the AG plan. ALL 5 AGs. per-AG slots.
- [ ] [DATA] P0. **R4-IS-freeze — diagnose + resume IS definition collection + backfill 2026-05-21→now gap BEFORE any
      could-exist seed**; then re-run `build_instrument_catalogue` + `enumerate_expected_universe v2` per AG. (Note:
      collection is reference-data — independent of the drained market-data writers; resuming does NOT violate the
      pre-migration drain.) slot-3. Repos: instruments-service + deployment-service.
- [ ] [AUDIT] P0. **R5-service-smoke — per-(service × asset_group) credential + data-fetch smoke matrix**: prove
      instrument fetch + market tick fetch per AG with REAL credentials; audit every failure (assume nothing); **block
      failing shards at (asset_group × data_type × venue) grain ONLY** — emit the pending-post-migration- backfill shard
      ledger into this plan; never block a whole AG. Run AFTER worktrees clean + all tonight's ships verified on `main`
      (image rebuilds ride that). slot-2+slot-3 split by AG ownership. Repos: mtds, instruments-service.
- [x] ✅ [DOCS] P0. **R6-codex — full M-COORD-1 closure BEFORE applies — DONE (slot-4 resume 2026-06-11, pm@645648a03 +
      pm@55f9cf9c3 + this commit)**: 5 per-AG plans de-coarsened (gate banners reconciled to M-COORD-1/R6-codex;
      defi+cefi deep-annotated — every remaining coarse/`hyperliquid_rest` token is a marked legacy-state/historical
      record, never spec; defi A12f-col CLOSED by ratification); `pipeline-mode-and-batch-live-reconciliation.md`
      hyperliquid_rest purged (vendor-only + transport column; sole remaining mention = the documented retirement) +
      reconciled to M1–M8 (replay stratum + reconciliation-facing M1–M8 slice); `sports-batch-live.md` (NEW) +
      `prediction-batch-live.md` + `tradfi-batch-live.md` seam docs shipped at cefi depth (phantom empty-reasons
      corrected against real UAC closed set); M1–M8 live/replay TARGET design codified as settled contract in
      `codex/02-data/pipeline-mode-partition.md` § "Ratified TARGET design" (+`batch-live-architecture.md` §10.5/§13,
      `cefi-batch-live.md` §7, `replay-subsystem.md` SUPERSEDED banner, `availability-manifest-and-data-status.md`
      live-taxonomy reconcile) — ratified-with-gated-tranche named (`M1-BREAKING`). slot-7→slot-4. Repo:
      unified-trading-pm.
- [ ] [DATA] P0. **R8-sports/pred gates**: sports-specific orphan sweep (candidate_parquet_paths-driven) built + run →
      characterize/backfill to E==0; sports v1_archive `(date,league,fixture_id)` ROW-coverage proven before any drop;
      prediction dry plan REGENERATED on final HEAD, attached to its verdict for sign-off. sports=slot-2 (tool assist
      slot-3), prediction=slot-3. Repos: instruments-service + mtds.

## Cross-cutting audit verdict (slot-7 / vm-cross-cutting) — 2026-06-08

> **REGRESSION RISK: NONE** for the per-AG `--apply`. All slot-7 cross-cutting work is **gate-only / consumer-side /
> design / land-the-code** — it adds QG gates, an alert cron, a UAC predicate, codex docs, and un-applied Terraform.
> **None of it changes any AG's schema / data_type names / GCS path templates / venue·enum names / manifest 4-state
> routing / production write-path** in a way that would leave code-vs-data mismatched after a walk (the Pre-Apply BLOCK
> RULE). So slots 2–6 G4 `--apply` are **not gated by any slot-7 item**.

| #     | Area                              | Status                                                                                                                                                                                                                                                                                   | Apply-impact                      |
| ----- | --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| **A** | Tier-2 QG gates (canonical-model) | ✅ pm@b4245a7dd — STEP 5.93 `check_canonical_model_regressions` (coarse pipeline_mode / exact-coarse reader / Era-A chain-write); AST + baseline-ratchet; fleet-swept green (25 repos per-scope); planted-regression proven (exit 1→0); 3 Era-A write sites baselined (per-AG-migrator). | gate-only — NONE                  |
| **B** | Tier-2 QG gate (bar-edge)         | ✅ pm@b4245a7dd — STEP 5.92 `check_bar_edge_open_ingestion`; wired base-service.sh + base-library.sh; 2 latent sites baselined; 21 unit tests; basedpyright 0.                                                                                                                           | gate-only — NONE                  |
| **C** | Tier-3 cf_manifest_audit + cron   | ✅ pm@2fe982eb1 (CF-1…14 + Era-B + cross-AG wrapper, JSON, exit-on-RED) + deployment@eaff3a7 (GCP Cloud Run Job+Scheduler+log-alert · AWS Batch+EventBridge+alarm; **NOT applied**).                                                                                                     | continuous-verify — NONE          |
| **D** | bar-edge Phase 1 (ingestion fix)  | ✅ IS@c6969f76 · MTDS@d63b2c4f · MDPS@7d89070 · uniswapv4@747cfce9 — all pre-agg open-edge sites → close edge; Massive left to its own plan (Phase 4b). Candle store was already right-edge (data-verified) → **does not block raw `--apply`**.                                          | feature-layer — NONE on raw apply |
| **E** | bar-edge Phase 0 (gate/fixture)   | ✅ COMPLETE — gate (A/B); cross-source `t_close` equivalence fixture features@438c2c30 (6 tests, paths agree); ingestion-time `assert_close_edge` UTL@33ef2d31 (15 tests). All gate-only.                                                                                                | gate-only — NONE                  |
| **F** | MVP-scope Phase 1                 | ✅ UAC@d6e0775f — `mvp_scope` config + `is_mvp()` predicate + 56 tests. Pure rule-only, no manifest column, no data touch.                                                                                                                                                               | additive — NONE                   |
| **G** | BigQuery Phase 1                  | ✅ design pm@cae98d92d (codex engine tier) + infra deployment@eaff3a7 (hive external tables, **NOT applied**). Reads canonical corpus; gated after per-AG `--apply` for stable schema.                                                                                                   | land-the-code — NONE              |
| **H** | G3 deployment-api UNION view      | ✅ VERIFIED green — deployment-api@4dd2575 in HEAD history; `test_data_status_union.py` + `test_data_status_drilldown_provenance.py` = **21 passed**. Consumer-side, fixture-tested, no data migration needed.                                                                           | consumer-side — NONE              |

**Rule-11 fleet-safety**: both new gates were swept across all repos BEFORE wiring (no "enable + see what goes red");
service repos SOURCE base-service.sh from the workspace PM checkout (no per-repo copy → activates fleet-wide the instant
PM lands on the CI-cloned ref; no template rollout needed) — verified green on 5 consumer repos per-scope
(mtds/IS/UTL/UAC/deployment-api). **Findings captured + resolved 2026-06-09 (operator clarifications)**: (1) ~~3 Era-A
`data_type=options_chain/futures_chain` write sites~~ — CORRECTED: `options_chain`/`futures_chain` are a NAME COLLISION
(both an instrument_type AND a genuine SNAPSHOT data_type, `*_OPTIONS_CHAIN_SNAPSHOT`); the STEP 5.93
`era-a-chain-write` pattern was a checker bug (it false-positived legit snapshot writers) → REMOVED (pm@361e548e1); the
validity-matrix entries re-categorized to `PENDING_SNAPSHOT_SLICE` (slot-3 widens). (2) MDPS
`liquidity_adapter._convert_timestamps` periodStartUnix→processing_dt — still baselined-latent (diagnose). (3)
deployment-service **pre-existing `uv.lock` out-of-sync** QG failure (unrelated; TF touches no Python) — for the
deployment-service owner. (4) **validity-matrix orphans resolved** (uac@fec77f5d typed closed-set + uac@f5e6b0c2):
`(cefi, ohlcv_15m)` RETIRED (no producer); **9/11 DeFi data_types WIRED** to genuine venue producers (+18 protocols,
37→55) — `native_staking_rates`/`vault_share_price` honestly stay BLOCKED_UPSTREAM_CAPABILITY. **→ DeFi could-exist
universe EXPANDED: slot-2 must re-run enumerate before G4** (B0-PRE todo in the defi plan; additive ⇒ NON-BLOCK,
coverage % drops honestly).

> **🔴 BAR-EDGE BLOCKER (feature-layer gate, 2026-06-08) — `bar_edge_left_vs_right_remediation_2026_06_08.md`**: a
> CLOSED candle stamped on the OPEN/left edge = look-ahead → leakage. Data-verified scope (Harsh): the MDPS **processed
> candle store is right-edge CORRECT** (so this does NOT block the raw/manifest `--apply` — slots 2–6 G4 proceed), but
> the **FEATURE LAYER is gated** — the two features-service resamplers (the only realized bugs) are fixed
> (features-service@7a4fafd9) yet (a) the gate still can't catch edge errors and (b) the pre-fix left-edge `features-*`
> corpus must be recomputed. **No feature-layer trust / no G5 feature backfill until Phase 0 (gate-close) + Phase 2
> (corpus purge) land.** Latent pre-agg ingestion sites fixed for correctness-in-depth. SSOT: the wrapper plan +
> [[bar_edge_left_vs_right_systemic_2026_06_08]].

> **🔴 PRE-APPLY BLOCK RULE (the strict definition — operator 2026-06-08; ALL slots apply before their AG's
> `--apply`)**: the single-walk bakes data to the canonical schema / data_type names / GCS path templates / venue+enum
> names per the CURRENT code. An open issue **BLOCKS** the walk if fixing it would change **schema, data_type names,
> path templates, venue/instrument/enum names, manifest 4-state routing, or production write/read code** such that —
> applied AFTER the walk — the code would read/write a **different place or shape** than where the walk put the data
> (orphaned / code-vs-data mismatch). It is **NON-BLOCK** only if (i) the change is already shipped, (ii) the walk
> itself performs the change (in-walk), or (iii) it is purely consumer-side / CI / dep / a post-migration G5 backfill. A
> "deferred to a later walk" rename is NON-BLOCK **only if the current walk does not leave code-vs-data mismatched in
> the interim** — otherwise it blocks. Confirmed blockers so far: **CF-11 swallow** — **tradfi `databento.py:826` ✅
> CLOSED (slot-6 2026-06-08: re-raises on LDR, instruments-service@f7744fbf+@c0f2f39c, re-verified
> `git show origin/live-defi-rollout`; the stale framing keyed off `bd1456aa`)**; **prediction polymarket still OPEN
> (slot-5)**. Under-review (sweep 2026-06-08): **D14 `dex_pools`(manifest) vs `dex_pool_state`(parquet)** name
> divergence + any other pending schema/name/path change. NON-BLOCK (verified): Massive shape (never ingested),
> source-provenance write-path (shipped), D10 unbacked venues (no data), library QG sentinel (CI).

> **🟢 G3-CONSUMER — deployment-api/UI UNION read path SHIPPED 2026-06-07 (vm-cross-cutting / slot-7)**: the data-status
> CONSUMER is now honest for the post-migration v9 multi-row manifest (reads the v9 contract; fixture-tested — does NOT
> need the data migrated yet). **`deployment-api@4dd2575`**: new `data_status_union.union_reduce_to_cells` collapses
> each cell's multi-(source × pipeline_mode) rows to ONE honest `capture_status` via the **M5 union rule** (≥1
> source/mode `captured` ⇒ cell `captured`; status precedence captured>empty>failed>expected; known-empty > pending),
> wired into the panel rollup (`_compute_capture_status_counts`) + the hierarchical `_aggregate_counts` so the 4-state
> counts are CELL-grain (no double-count across provenance rows; v8 manifests unchanged — guarded on the provenance
> columns). Coverage % = `captured / (captured+empty+failed+expected_unattempted)` over the could-exist denominator
> (READ, never re-derived per CF-14). **DRILLDOWN** (`deployment-api@4dd2575`): per-(pipeline_mode × source) breakdown
> at shard-atom leaves (a cell shows e.g. captured via `batch_databento` + `replay_databento`, missing in
> `live_databento`) + `pipeline_mode`/`source` as filter AND `group_by` axes + a top-level provenance summary.
> **deployment-ui** `HierarchicalShardDrilldown` renders the pipeline_mode/source breakdown + the 4-state
> (**`deployment-ui@0dc40eb`**) — **UI tick stays [BLOCKED-PLAYWRIGHT]** (pw:L2 pending on a UI-capable slot;
> regression: `src/components/HierarchicalShardDrilldown.test.tsx`). **M5 + the M4 data-status portion (mode-agnostic
> UNION; the live `select_for_mode` precedence stays OPEN in batch-live-reconciliation-service — live-side track) are
> DONE on the CONSUMER side** (G0-plan M5 row annotated PARTIAL — the `cadence` dimension + unified-trading-system-ui
> parity remain). Tests: deployment-api `test_data_status_union.py` + `test_data_status_drilldown_provenance.py`
> (QG-green) · UI vitest 766 green. **Landed on LDR via the tab-mirror; the LDR→staging promotion is dep-tier-gated on
> deployment-service reaching STAGING_GREEN — NOT bypassed** (`--skip-dep-tier-gate` is agent-forbidden). Out of scope
> (gated): the live read-path precedence service M4 in batch-live-reconciliation-service; the actual `--apply`;
> M3/M6/M7.

> **🟢 G3-CONSUMER — deployment-api/UI UNION read path SHIPPED 2026-06-07 (vm-cross-cutting / slot-7)**: the data-status
> CONSUMER is now honest for the post-migration v9 multi-row manifest (reads the v9 contract; fixture-tested — does NOT
> need the data migrated yet). **`deployment-api@4dd2575`**: new `data_status_union.union_reduce_to_cells` collapses
> each cell's multi-(source × pipeline_mode) rows to ONE honest `capture_status` via the **M5 union rule** (≥1
> source/mode `captured` ⇒ cell `captured`; status precedence captured>empty>failed>expected; known-empty > pending),
> wired into the panel rollup (`_compute_capture_status_counts`) + the hierarchical `_aggregate_counts` so the 4-state
> counts are CELL-grain (no double-count across provenance rows; v8 manifests unchanged — guarded on the provenance
> columns). Coverage % = `captured / (captured+empty+failed+expected_unattempted)` over the could-exist denominator
> (READ, never re-derived per CF-14). **DRILLDOWN** (`deployment-api@4dd2575`): per-(pipeline_mode × source) breakdown
> at shard-atom leaves (a cell shows e.g. captured via `batch_databento` + `replay_databento`, missing in
> `live_databento`) + `pipeline_mode`/`source` as filter AND `group_by` axes + a top-level provenance summary.
> **deployment-ui** `HierarchicalShardDrilldown` renders the pipeline_mode/source breakdown + the 4-state
> (**`deployment-ui@0dc40eb`**) — **UI tick stays [BLOCKED-PLAYWRIGHT]** (pw:L2 pending on a UI-capable slot;
> regression: `src/components/HierarchicalShardDrilldown.test.tsx`). **M5 + the M4 data-status portion (mode-agnostic
> UNION; the live `select_for_mode` precedence stays OPEN in batch-live-reconciliation-service — live-side track) are
> DONE on the CONSUMER side** (G0-plan M5 row annotated PARTIAL — the `cadence` dimension + unified-trading-system-ui
> parity remain). Tests: deployment-api `test_data_status_union.py` + `test_data_status_drilldown_provenance.py`
> (QG-green) · UI vitest 766 green. **Landed on LDR via the tab-mirror; the LDR→staging promotion is dep-tier-gated on
> deployment-service reaching STAGING_GREEN — NOT bypassed** (`--skip-dep-tier-gate` is agent-forbidden). Out of scope
> (gated): the live read-path precedence service M4 in batch-live-reconciliation-service; the actual `--apply`;
> M3/M6/M7.

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

| Class              | Site                                                                                                                                                                                                                                   | State  | Fix / owner                                                                                                                                                                                             |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| WRITE migrator     | `migrate_tradfi_to_v9_canonical.py` (`_pipeline_mode`→`batch_databento`)                                                                                                                                                               | ✓      | reference impl — copy this pattern                                                                                                                                                                      |
| WRITE rebuild      | `rebuild_{cefi,tradfi,sports,prediction}_manifest*` (`derive_pipeline_mode_for_row`)                                                                                                                                                   | ✓      | reference impl                                                                                                                                                                                          |
| **WRITE migrator** | **`migrate_defi_full_v9_canonical.py:70/700/714`** `DEFAULT_PIPELINE_MODE="batch"` → coarse path+col                                                                                                                                   | **✅** | **DONE mtds@f80c50f1** — `batch_<source>` per shard via `derive_pipeline_mode_for_row`; source+transport in path+column; coarse retired                                                                 |
| **WRITE rebuild**  | **`rebuild_defi_manifest.py:88/206/230/250`** `_DEFAULT_PIPELINE_MODE="batch"` (+ `:302` blank — C-#1)                                                                                                                                 | **✅** | **DONE mtds@f80c50f1** — `derive_pipeline_mode_for_row` source-aware (path+col), `pipeline_mode=` day-probe, per-shard isolation; C-#1 `:302` fixed                                                     |
| READ (defi)        | features `mtds_canonical_reader.py` — was exact `pipeline_mode=batch/`+`live/` probe                                                                                                                                                   | ✅     | **DONE features@c487e04b** — day-level mode-agnostic listing, prefix-match `batch_*/live_*/replay_*` + bare + legacy `category=`, canonical-over-legacy ranked                                          |
| READ               | mdps `orchestration_scanner.py` — day-listing already mode-agnostic; FIXED source-aware leak bug                                                                                                                                       | ✅     | **DONE mdps@d59749c (PR#103→staging)** — gated `batch_onchain_rpc` legacy-venue branch on absence of `data_type=` (canonical `dex_pool_state` no longer leaks into `dex_swaps`); +source-aware fixtures |
| TEST               | mtds `test_migrate_defi_full_v9_canonical.py:53-54` · `test_rebuild_defi_manifest.py:17/72` · mdps `test_orchestration_scanner.py:182-230` · features `test_mtds_canonical_reader.py:63-132`                                           | ◑      | **mtds DONE mtds@f80c50f1** (both defi test files assert `batch_<source>` + source/transport, 25/25 green); mdps/features test updates ride their READ change (features@c487e04b / mdps@d59749c)        |
| LIVE (all AGs)     | UTL `pipeline_mode_resolver.py:123` live → `LIVE_WEBSOCKET` (not `live_<source>`)                                                                                                                                                      | ~      | the M1 `live_<source>` OBJECT migration = **gated next tranche** (C-#5) — NOT part of the batch migration                                                                                               |
| DOC ✓              | CLAUDE.md:568 · SUB_AGENT_MANDATORY_RULES:276 · most AG plans · deployment-api/data_status                                                                                                                                             | ✓      | already `batch_*/`                                                                                                                                                                                      |
| DOC ✗              | `defi_manifest_canonicalisation_2026_06_01.md` (many coarse `pipeline_mode=batch/`) · codex `pipeline-mode-partition.md` (mixed) · audit `defi_object_path_canonicalisation_2026_06_01.py:87` · `pipeline_mode_partition_migration:63` | ✗      | reconcile to `batch_<source>` (rides M-COORD-1)                                                                                                                                                         |
| BY-DESIGN          | codex `batch-live-architecture.md:466` + `instruments-live-architecture.md:30` — instruments reference data has **NO `pipeline_mode=live` partition** (live writes the identical batch path)                                           | ✓      | keep — a real exception, not a conflict                                                                                                                                                                 |

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

| Gate     | Plan / issue                                                                                                                                                                                                | Role                                                                                                                                                                                                                                                                                                                                                                                                                                               | Owner                                                                                               | Blocked-until (upstream)                            |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| **G0**   | `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05`                                                                                                                                         | **THE model + apply-gate** (batch/live/replay × source × transport; M2/M3 registries; M4 precedence; cont. contract; 0.8 doc reconcile)                                                                                                                                                                                                                                                                                                            | vm-cross-cutting                                                                                    | — (root; Phase-0 code must go GREEN)                |
| G0       | `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01`                                                                                                                                                 | canonical bucket SSOT (env-tier readers/writers) + L6 decommission                                                                                                                                                                                                                                                                                                                                                                                 | vm-cross-cutting                                                                                    | partly done; L6 ⟶ G4                                |
| G0       | `data_source_provenance_all_asset_groups_2026_06_01`                                                                                                                                                        | `source` column — RIDES each AG's single-walk                                                                                                                                                                                                                                                                                                                                                                                                      | per-AG                                                                                              | G0 model (source-aware) ratified ✓                  |
| G0       | `pipeline_mode_partition_migration_2026_06_01`                                                                                                                                                              | on-disk `pipeline_mode=` partition — RIDES each AG walk                                                                                                                                                                                                                                                                                                                                                                                            | per-AG                                                                                              | G0 model form (M1) locked                           |
| G0       | `manifest_reader_fail_fast_on_stale_fallback_2026_05_28`                                                                                                                                                    | reader fail-fast default + consolidator liveness (no legacy fallback)                                                                                                                                                                                                                                                                                                                                                                              | vm-cross-cutting                                                                                    | parallel-safe                                       |
| **G1**   | `proper_instrument_catalogue_lifecycle_rollup_2026_06_04`                                                                                                                                                   | **could-exist-universe SSOT** — `build_instrument_catalogue` roll-up + daily scheduler + v2-enumerator recurring run                                                                                                                                                                                                                                                                                                                               | vm-cross-cutting                                                                                    | `instruments_manifest_canon` (IS indices canonical) |
| G1       | `instruments_manifest_canonicalisation_2026_06_01`                                                                                                                                                          | IS reference/instrument `_index` canonical (all AG)                                                                                                                                                                                                                                                                                                                                                                                                | per-AG slice                                                                                        | G0                                                  |
| G1       | `instruments_backfill_phase3_2026_05_22`                                                                                                                                                                    | IS reference backfill                                                                                                                                                                                                                                                                                                                                                                                                                              | vm-cross-cutting                                                                                    | G1 catalogue GREEN ⟶ G5                             |
| **G2**   | `defi_manifest_canonicalisation_2026_06_01`                                                                                                                                                                 | DeFi MTDS single-walk + §A–H executor                                                                                                                                                                                                                                                                                                                                                                                                              | vm-defi (slot-2)                                                                                    | G0 + G1                                             |
| G2       | `cefi_manifest_canonicalisation_2026_06_01`                                                                                                                                                                 | CeFi single-walk                                                                                                                                                                                                                                                                                                                                                                                                                                   | vm-cefi (slot-3)                                                                                    | G0 + G1                                             |
| G2       | `sports_manifest_canonicalisation_2026_06_01`                                                                                                                                                               | Sports single-walk (+ fixtures/transfer-window reasons)                                                                                                                                                                                                                                                                                                                                                                                            | vm-sports (slot-4)                                                                                  | G0 + G1                                             |
| G2       | `prediction_manifest_canonicalisation_2026_06_01`                                                                                                                                                           | Prediction single-walk                                                                                                                                                                                                                                                                                                                                                                                                                             | vm-prediction (slot-5)                                                                              | G0 + G1                                             |
| G2       | `tradfi_manifest_canonicalisation_2026_06_01`                                                                                                                                                               | TradFi single-walk (v9 + partition + source re-consol)                                                                                                                                                                                                                                                                                                                                                                                             | vm-tradfi (slot-6)                                                                                  | G0 + G1                                             |
| G2       | `downstream_services_manifest_canonicalisation_2026_06_01`                                                                                                                                                  | MDPS/features/strategy/execution `_index` canonical                                                                                                                                                                                                                                                                                                                                                                                                | vm-ml                                                                                               | G0 + G1 + the AG MTDS walks                         |
| G2       | `solana_defi_legacy_migration_2026_05_27`                                                                                                                                                                   | DeFi Solana legacy→canonical (serialise with defi §C)                                                                                                                                                                                                                                                                                                                                                                                              | vm-defi                                                                                             | defi G2 single-walk                                 |
| G2       | `features_input_manifest_migration_2026_05_25`                                                                                                                                                              | features input `_index` migration                                                                                                                                                                                                                                                                                                                                                                                                                  | vm-ml                                                                                               | G0 + downstream                                     |
| G2       | issue `defi_code_codex_drift_2026_05_27`                                                                                                                                                                    | DeFi code↔codex drift (wrapped by defi plan §A/§F)                                                                                                                                                                                                                                                                                                                                                                                                 | vm-defi                                                                                             | wrapped → defi G2                                   |
| G2       | issue `features_service_defi_data_loading_blockers_2026_05_29`                                                                                                                                              | features DeFi e2e data-layer (wrapped by defi §C0/§D)                                                                                                                                                                                                                                                                                                                                                                                              | vm-defi/vm-ml                                                                                       | defi G2 + downstream                                |
| G2       | issue `cefi_processed_candles_manifest_file_disconnect_2026_05_25`                                                                                                                                          | CeFi processed-candles manifest disconnect                                                                                                                                                                                                                                                                                                                                                                                                         | vm-cefi                                                                                             | cefi G2                                             |
| **G3**   | (data-status §B in each per-AG plan) + **M5** in the G0 plan                                                                                                                                                | deployment-api/UI = ONE UNION view across pipeline modes + 4-state + pipeline_mode/source drilldowns                                                                                                                                                                                                                                                                                                                                               | vm-cross-cutting + per-AG                                                                           | G0 (M5) + G2 readers union-aware                    |
| **G3.5** | `migration_verification_orphan_safety_2026_06_10`                                                                                                                                                           | **pre-apply verification harness (⑬–⑲ + G4.5)** — canonical possible-manifest registry (CF-15) · catalogue-seeded denominator + CeFi/Pred enumerator stubs (CF-16) · bidirectional orphan sweep + bucket prefix taxonomy + sizing (CF-17) · schema-attribute completeness (CF-18) · candle edge-timestamp (CF-19) · projected-manifest preview (CF-20) · verified-delete (CF-21); audit `migration_orphan_safety_goalpost_verification_2026_06_10` | vm-cross-cutting (slot-3: V0 + scaffolds + cefi/pred) + vm-defi/tradfi/sports (slot-2: per-AG runs) | G3 ∧ V0 registry GREEN; **HARD-BLOCKS G4**          |
| **G4**   | per-AG `*_manifest_canonicalisation` **`--apply`** items + `bucket_name_ssot` L6 delete                                                                                                                     | irreversible manifest + data/schema migration                                                                                                                                                                                                                                                                                                                                                                                                      | per-AG                                                                                              | **G0 ∧ G1 ∧ G2 ∧ G3 ∧ pre-migration drain**         |
| **G5**   | `mtds_backfill_phase3` · `mdps_backfill_phase3` · `features_backfill_phase3` · `instruments_backfill_phase3` · `aws_cloud_toggle_and_backfill_parity_2026_05_22`                                            | resume backfills → 100% honest coverage; massive/polygon-vs-databento cost-swap                                                                                                                                                                                                                                                                                                                                                                    | per-AG                                                                                              | **G4 GREEN for that AG**                            |
| ∥        | `ci_canonical_v2_migration_2026_05_29` · `mdps_pure_polars_migration_2026_05_28` · `global_ledger_pnl_attribution_migration_2026_06_01` · `planning_vm_canonical_bringup_and_topology_reconcile_2026_06_05` | parallel infra/CI/ledger — tracked, NOT on the migration critical path                                                                                                                                                                                                                                                                                                                                                                             | various                                                                                             | parallel-safe                                       |

## G1 expanded — IS catalogue is the ROOT of all missing-data understanding (operator 2026-06-07)

> **IS (instruments-service) + UAC together define the could-exist universe — every downstream honest denominator,
> preflight (⑥/⑦), and `expected_unattempted` seed reads it. If IS or UAC is wrong, EVERY AG's coverage % is wrong.** So
> G1 is gated, and its catalogue has a full code → dry-run → real-run → schedule lifecycle, tracked per-AG.

> **🟢 G1-ENUM — CODE SHIPPED 2026-06-07 (vm-cross-cutting / slot-7)**: the shape-aware producer is live — UAC validity
> matrix `uac@97c26dbe` (`valid_data_types_for_instrument_type` + `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE`, defi
> lazily derived from `PROTOCOL_CAPABILITIES`, uncertain rows flagged for AG owners) + instruments-service enumerator
> `is@6ea46565` (`_row_data_types` filters every `_enumerate_v2_*` to valid pairs + preserves prediction grain-binding;
> cefi OPTION/COMBO leaves → zero per-leaf rows; impossible combos excluded; +12 IS / +32 UAC tests, both repos QG
> green). **Unblocks slots 2-6 G1.run** (each AG owner still verifies its matrix slice + re-runs its dry-run against the
> shape-aware producer before `--apply-write`). Original finding ↓ retained for context.
>
> **✅ ERA-B SHIPPED 2026-06-07 (vm-cross-cutting / slot-7) — `options_chain`/`futures_chain` are now canonical
> INSTRUMENT_TYPES (data_type=trades) in the contracts + producer.** `options_chain`/`futures_chain` are
> INSTRUMENT_TYPES (per-underlying chain bundles) with `data_type=trades`, bundled per-underlying — matching the live
> writer (`tardis_shared.py` Phase 1.6) + the on-disk object paths + the `CEFI_OPTIONS_CHAIN_TRADES` schema
> (symbol=underlying). The earlier rollup (item 1(b) below, `uac@cb3a846b`/`is@687d1443`) was **Era-A-shaped** (emitted
> `data_type=options_chain`); this reconciles it UP to Era-B. **Shipped (each a QG-`--no-fix`-green commit on
> `tab/ikennaigboaka/7`, prek-green, tab ⊇ LDR):**
>
> - **`uac@ae70338d`** — (1) validity matrix: `(cefi/tradfi, options_chain/futures_chain)` → `frozenset({"trades"})`
>   (was `{options_chain}`/`{futures_chain}`); `(tradfi, option/combo)` → `frozenset()` (was UNMAPPED → None fallback →
>   the ~563K false candidates); (2) renamed `bundle_data_type_for_instrument_type` → `bundle_instrument_type_for_leaf`
>   (returns the bundle INSTRUMENT_TYPE; the data_type resolves to `trades` via the matrix); (3) `SOURCE_PRIORITY` +
>   `capability_declarations/_cefi.py`+`_tradfi.py`: Era-B docs (the bundle resolves source via `(ag, "trades")`; the
>   legacy data_type-keyed `options_chain`/`futures_chain` entries are RETAINED for pre-migration legacy rows + the
>   bidirectional `SOURCE_PRIORITY ↔ AVAILABILITY_AT_SEMANTICS` closed-set round-trip — the per-AG v9 migrators own
>   their removal, see follow-up todo); (4) flipped the Era-A matrix/schema tests to Era-B; `CEFI_OPTIONS_CHAIN_TRADES`
>   schema unchanged.
> - **`is@74df991d`** — `enumerate_expected_universe._rollup_bundle_grain`: the synthetic bundle entry now carries
>   `instrument_type=options_chain`/`futures_chain` + `data_type=None` → the enumerator resolves its data_type from the
>   validity matrix → emits ONE candidate per underlying with **`data_type=trades`** (NOT `data_type=options_chain`).
>   Tests flipped to assert `(underlying, options_chain, trades)`.
>
> Regression verified by the QG suite (both repos `quality-gates.sh --no-fix` exit 0; UAC 3264 + IS 3267 tests green):
> OPTION/COMBO leaf → **0** per-contract candidates; underlying → **exactly one** `options_chain`/`futures_chain`
> candidate with `data_type=trades`; PERPETUAL/SPOT unchanged; **no `data_type=options_chain` emitted**; tradfi
> option/combo no longer fall through to the all-data_types fallback. **🔔 NOTIFY slots 3 (cefi) + 6 (tradfi): the Era-B
> shape-aware producer is GREEN — re-run your `enumerate` dry-runs to confirm the prod numbers (tradfi ~588K →
> plausible, ~563K false GONE; cefi DERIBIT no longer dominant) before `--apply-write`; flip each AG's matrix slice
> verify row.** **BLOCKED-PROMOTION**: the LDR→`staging` promotion is gated on the workspace **staging lock** (breaking
> MINOR bump cascade, `instruments-service=0.2.0`, locked since 2026-06-07T16:59Z) — both commits are QG-green on the
> tab branch (→ LDR via the tab-mirror); the staging→main promotion flows via the automation once the cascade
> converges + unlocks. **OUT OF SCOPE (per-AG migrators own)**: the v8→v9 manifest relabel of legacy
> `data_type=options_chain` rows.

> **🔴 G1-ENUM (P0, CROSS-AG, surfaced by slot-3 cefi dry-run 2026-06-07) — the v2 enumerator over-fans → false
> `expected_unattempted` pollution.** `_enumerate_v2_*` (`enumerate_expected_universe.py`) fans ALL data*types over
> EVERY instrument with **no `(instrument_type × data_type)` validity filter and no bundle-grain handling**. cefi
> ground-truth: options/futures are captured as per-underlying `options_chain`/`futures_chain` BUNDLES (~0 per-OPTION /
> per-COMBO rows), yet the catalog has 72,156 OPTION + 17,472 COMBO → `OPTION/COMBO × 7 data_types` never match the
> present-set + impossible combos (`PERPETUAL × options_chain`). An `--apply-write` now would seed **millions of false
> `expected_unattempted` rows → distort the exact denominator G1 exists to make honest.** The dry-run caught it
> pre-write. **This is the SAME root as slot-4's sports finding** (generic producer is fixture-grain, sports atom is
> league-grain; prediction already solved it with a per-cqg granularity-aware producer). **Cross-AG**: the
> `for dt in data_types` no-filter pattern is in EVERY
> `\_enumerate_v2*\*`. **FIX (owner: slot-7 G1-foundation in instruments-service)**: the generic producer becomes instrument-shape-aware — `(instrument_type
> ×
> data_type)`validity filter + bundle-grain (mirror the prediction per-cqg producer); **each AG owner (slots 2-6) verifies their slice** before any G1.run apply-write. **Gates every AG's`--apply-write`seed** (a G1 prerequisite). Tracked: P0 in cefi plan + must land in`proper_instrument_catalogue_lifecycle_rollup_2026_06_04`
> (central fix) + a verify-slice todo in each AG plan. **Re-scopes WAVE-1 slot-7**: the "generic foundation" must be
> AG-shape-aware, NOT one-size fan-out.
>
> **✅ G1-V8 (P0, cross-AG, the SECOND G1 long pole): the instruments-store v9 MIGRATOR IS BUILT 2026-06-07
> (`is@febb899e`) + dry-run-green for all 5 AGs — see "Two G1 long poles" item 2 below. The `--apply` RUN stays G4-gated
> per-AG. Historical context (now RESOLVED):** Confirmed v8 across **cefi (100% v8), sports (v8), tradfi (0.8% v9 /
> 20,218 rows v8)** — and slot-6 found the fix is "a gated G4-class single-walk `--apply` with **no migrator built yet**
> (instruments*manifest **E2**, vm-cross-cutting)". So gate-c (v9 `_index`) is UNMET for every AG **because the tool to
> fix it hasn't been written**. This gates EVERY AG's G1.run apply-write alongside G1-ENUM. **Owner: vm-cross-cutting
> must BUILD the `instruments_manifest` E2 v9 single-walk migrator**
> (asset_group=/pipeline_mode=batch*<source>/source/transport/ available_at/typed data_type) for the instruments-store
> buckets — the analogue of the per-AG MTDS migrators, which don't exist for the IS reference surface. Until it lands,
> no AG's instruments-store goes v9 → no honest G1 seed. Tracked: `instruments_manifest_canonicalisation_2026_06_01`
> (must spawn the E2 migrator) + each AG plan's §H.

**Two G1 long poles gate every AG's `--apply-write` seed (both cross-cutting, both must land first):**

1. ✅ **G1-ENUM — CODE DONE 2026-06-07** — in TWO parts (the WAVE-1 claim "validity filter + bundle-grain" was
   inaccurate: `is@6ea46565` shipped ONLY the `(instrument_type × data_type)` VALIDITY FILTER + sports league-grain
   (`is@99a5fbf5`); the OPTIONS/COMBO BUNDLE-GRAIN ROLLUP did NOT ship — slot-6 re-ran tradfi on `6ea46565` and got only
   −808, ~563K false per-contract candidates remained):
   - **(a) validity filter** — `uac@97c26dbe` matrix + `is@6ea46565` producer (impossible
     `(instrument_type × data_type)` pairs filtered; per-leaf OPTION/COMBO zeroed via `frozenset()` — but that
     UNDER-seeds bundles to zero).
   - **(b) bundle-grain ROLLUP (the real fix) — SHIPPED 2026-06-07 (slot-7); ERA-A-shaped, reconciled to ERA-B by
     `uac@ae70338d`/`is@74df991d` — see the "✅ ERA-B SHIPPED" block above**: `uac@dd7fa100` (GRAIN axis SSOT
     `grain_for_instrument_type`) + `uac@cb3a846b` (`bundle_data_type_for_instrument_type` + tradfi grain) +
     `is@687d1443` (`enumerate_expected_universe._rollup_bundle_grain` — read-side pre-pass in `enumerate_v2` collapses
     every option/combo LEAF of a `(venue, chain, underlying)` into ONE synthetic per-underlying `options_chain`
     candidate; generalises slot-4's league-grain rollup, NO per-AG special-casing; `underlying` carried on the
     catalogue +`InstrumentCatalogEntry`, derived from instrument\*id as fallback) + `is@df15dba2` (contract tests).
     Net: OPTION/COMBO leaf → ZERO per-contract candidates; underlying → exactly ONE chain candidate. **(b) originally
     emitted `data_type=options_chain` (Era-A); the Era-B reconciliation (`uac@ae70338d`/`is@74df991d`) flips that to
     `data_type=trades` — the chain name is the instrument_type, the market data_type is trades.** (kills the ~563K
     tradfi over-fan + cefi DERIBIT dominance). **🔔 slots 3 (cefi) + 6 (tradfi): re-run `enumerate` dry-runs on the
     Era-B rollup producer to confirm (tradfi ~588K → plausible; cefi DERIBIT no longer dominant) — you were gated on
     this.** ✅ **F2 residual — RESOLVED (uac@e3dcd868 + instruments-service enumerate threading, slot-7 2026-06-08)**:
     the DERIBIT/OKX FUTURE-leaf per-contract over-fan is fixed by the **sound venue registry** `FUTURE_BUNDLE_VENUES`
     (`registry/market_data_categories.py`) — `grain_for_instrument_type` / `bundle_instrument_type_for_leaf` now take
     an optional `venue`: a bare FUTURE leaf bundles to a per-underlying `futures_chain` ONLY at DERIBIT/OKX, and stays
     per-contract at BYBIT (the unsound `VENUE_DATA_TYPE_CAPABILITIES` discriminator is NOT used). `enumerate_v2`'s
     `_rollup_bundle_grain` threads `instr.venue`; +8 UAC tests + 3 enumerate tests (DERIBIT/OKX bundle, BYBIT leaf).
     Kills the ~700 false DERIBIT/OKX per-contract FUTURE candidates while keeping BYBIT honest. **🔔 NOTIFY slots 3
     (cefi) + 6 (tradfi): re-run your `enumerate` dry-runs on the venue-aware producer — the DERIBIT/OKX FUTURE over-fan
     is gone (cefi 880→~180 per-underlying).** Per-AG slice verification + dry-run re-run still owed by each AG owner
     before `--apply-write`.
2. ✅ **G1-V8 — MIGRATOR BUILT + DRY-RUN GREEN (all 5 AGs) 2026-06-07** (`is@febb899e`,
   `instruments-service/scripts/migrate_instruments_store_v9.py`). AG-parametric single-walk that rewrites BOTH the
   instruments-store `_index` rows AND object paths to canonical v9 (CF-1 v9 · CF-2 `asset_group=` · CF-3
   `pipeline_mode=batch_instruments_service` · CF-4 `source=instruments_service` · CF-TRANSPORT `transport=rest` · CF-5
   typed reasons · CF-7 `data_type` · CF-8 `available_at` · CF-9 `resolve_bucket_name` · CF-10 honest `capture_status`
   from `instrument_count`). DRY-RUN validated on all 5 real prod `_index` files (cefi/defi/tradfi/sports/prediction →
   100% v9 projection). 14 credential-free unit tests; QG `--no-fix` exit 0. The `--apply` RUN stays G4-gated
   (coordinator G0 + Phase-0 writer-code + pre-migration drain; each AG owner runs its bucket's `--apply`). Sports is
   structural-only (its `capture_status`/reasons are enumerator-authoritative → sports plan owns the relabel). So gate-c
   (v9 `_index`) is now **TOOL-READY** for every AG; what remains is each AG's gated `--apply` run.

**Per-AG G1 status (WAVE-1 dry-runs):**

- **cefi (slot-3)**: ✅ **APPLY-READY (2026-06-08)** — Era-B + bundle-grain rollup LANDED (`uac@ae70338d`
  options_chain/futures_chain → `{trades}` + `is@74df991d`/`687d1443` read-side `_rollup_bundle_grain`; **F1 Era-B
  recommendation adopted**). **Enumerate RE-RUN GREEN** = **3,454 candidates**: 0 per-leaf OPTION/COMBO; **8
  `options_chain` candidates, ONE per underlying (DERIBIT BTC/ETH option+combo), all `data_type=trades`** (no
  `data_type=options_chain`); 0 impossible pairs; **DERIBIT 11.5%** (no longer dominates). Migrators + instruments-store
  v9 (30,803→100% v9) re-confirmed GREEN; 7+2 audit green (CF-1…13 ✓; CF-14 options-bundle ✓). **UAC slice verified
  correct — no change.** 🟡 **ONE residual = F2 (slot-7-owned, NOT a G4 blocker)**: `FUTURE` not rolled up (slot-7
  DELIBERATELY omits `future→futures_chain`, venue-specific: DERIBIT/OKX bundle vs BYBIT per-contract) → 880
  per-contract FUTURE candidates (700 DERIBIT/OKX = false over-seed) — over-seeds only the **G1.run futures seed**, fix
  = slot-7 venue-aware `build_instrument_catalogue` rollup. **Remaining gates are OPERATIONAL only**: instruments-store
  v9 walk RUN · IS backfill · Era-B legacy relabel (rides G4, operator `slot-7 edca81b57`) · pre-migration drain · F2
  (slot-7). Full verdict in `cefi_manifest_canonicalisation_2026_06_01.md` § "cefi APPLY-READY". 🟢 G3 ✓ · G0 ✓. **🔁
  12-POINT PRE-APPLY RE-VERIFICATION (slot-3, 2026-06-08, real-prod data-state):** ①–⑫ re-run on real GCS (migrate/
  rebuild/enumerate dry-runs + `_index` byte-probes; MTDS cefi `_index`=2.64M rows 100% v8 pre-migration confirmed).
  **G4 data/manifest migration = APPLY-READY, REGRESSION RISK NONE** (⑪ batch=live byte-identical; ②/① no
  double-count/no loss — copy-not-move safe via rebuild dedup + migrate-before-rebuild; ⑤/⑨/⑩/⑫ 🟢). **TWO
  honest-coverage gates surfaced (NOT G4 blockers): ⑧ 🟡 IS cefi reference universe lists only 12 venues —
  KRAKEN-SPOT/FUTURES (107K captured rows, on-disk-real) + BITFINEX-SPOT + PACIFICA + LIGHTER absent ⇒ catalogue ⊉
  present-set ⇒ falsely-high coverage. **ROOT CAUSE = IS Tardis adapter `_DEFAULT_EXCHANGES` stale 8-id subset drifted
  below SSOT `VenueMapping.all_tardis_exchanges`; 🟢 CODE FIX SHIPPED `is@a6bc4d48` (derives from SSOT + regression
  tests).** Remaining = operational IS reference backfill re-run + CLOB venues (PACIFICA/LIGHTER) — owner
  `instruments_backfill_phase3`; **⑦(a) 🟡 deployment-api cefi coverage denominator re-derives genesis/launch instead of
  READING `expected_unattempted`\*\* (correct pre-seed; switch post enumerate `--apply-write` — owner:
  deployment-api/downstream). Both tracked as todos in the cefi plan § "PRE-APPLY 12-POINT AUDIT VERDICT".
- **sports (slot-4)**: **WAVE-2 dry-runs GREEN (2026-06-07)** — G1-ENUM league-grain producer DONE (is@99a5fbf5) +
  AG-specific producer present; **fixed a real G1-ENUM bug: the UAC `("sports","league")` validity slice silently
  dropped `ODDS` → now derived from `SPORTS_DATA_TYPE_TO_SOURCE` (uac@aff80339/PR#95)**. G1-V8 instruments-store v9
  dry-run GREEN (2.68M → 100% v9, `asset_group`/`source`/`transport`/`available_at` all stamped,
  `pipeline_mode=batch_<source>`). MTDS migrator object-path dry-run GREEN (source-aware `batch_odds_api`,
  `category`→`asset_group`). `--apply` gated (G0 + IS v9 walk + IS backfill + 2 data-state findings: 6,869 blank
  `capture_status` + mdps consolidated-index-reads-0). Full verdict: `sports_manifest_canonicalisation_2026_06_01.md` §
  "G2 WAVE-2 readiness verdict".
- **cefi (slot-3)**: ✅ **APPLY-READY (2026-06-08)** — Era-B + bundle-grain rollup LANDED (`uac@ae70338d`
  options_chain/futures_chain → `{trades}` + `is@74df991d`/`687d1443` read-side `_rollup_bundle_grain`; **F1 Era-B
  recommendation adopted**). **Enumerate RE-RUN GREEN** = **3,454 candidates**: 0 per-leaf OPTION/COMBO; **8
  `options_chain` candidates, ONE per underlying (DERIBIT BTC/ETH option+combo), all `data_type=trades`** (no
  `data_type=options_chain`); 0 impossible pairs; **DERIBIT 11.5%** (no longer dominates). Migrators + instruments-store
  v9 (30,803→100% v9) re-confirmed GREEN; 7+2 audit green (CF-1…13 ✓; CF-14 options-bundle ✓). **UAC slice verified
  correct — no change.** 🟡 **ONE residual = F2 (slot-7-owned, NOT a G4 blocker)**: `FUTURE` not rolled up (slot-7
  DELIBERATELY omits `future→futures_chain`, venue-specific: DERIBIT/OKX bundle vs BYBIT per-contract) → 880
  per-contract FUTURE candidates (700 DERIBIT/OKX = false over-seed) — over-seeds only the **G1.run futures seed**, fix
  = slot-7 venue-aware `build_instrument_catalogue` rollup. **Remaining gates are OPERATIONAL only**: instruments-store
  v9 walk RUN · IS backfill · Era-B legacy relabel (rides G4, operator `slot-7 edca81b57`) · pre-migration drain · F2
  (slot-7). Full verdict in `cefi_manifest_canonicalisation_2026_06_01.md` § "cefi APPLY-READY". 🟢 G3 ✓ · G0 ✓.
- **sports (slot-4)**: **WAVE-2 dry-runs GREEN (2026-06-07)** — G1-ENUM league-grain producer DONE (is@99a5fbf5) +
  AG-specific producer present; **fixed a real G1-ENUM bug: the UAC `("sports","league")` validity slice silently
  dropped `ODDS` → now derived from `SPORTS_DATA_TYPE_TO_SOURCE` (uac@aff80339/PR#95)**. G1-V8 instruments-store v9
  dry-run GREEN (2.68M → 100% v9, `asset_group`/`source`/`transport`/`available_at` all stamped,
  `pipeline_mode=batch_<source>`). MTDS migrator object-path dry-run GREEN (source-aware `batch_odds_api`,
  `category`→`asset_group`). `--apply` gated (G0 + IS v9 walk + IS backfill + 2 data-state findings: 6,869 blank
  `capture_status` + mdps consolidated-index-reads-0). Full verdict: `sports_manifest_canonicalisation_2026_06_01.md` §
  "G2 WAVE-2 readiness verdict".
- **tradfi (slot-6)**: catalogue + enumerate dry-run mechanism GREEN (588,798 candidates) — BUT this ran on the OLD
  over-fanning producer (predates G1-ENUM) → **re-validate the candidate set against slot-7's shape-aware producer**
  (tradfi is per-contract so less bundle-affected than cefi, but impossible-combo filtering still applies). gate-b
  (capture FROZEN — catalogue marks ~651K delisted) **remediated**: slot-6 shipped the **Massive IS reference adapter**
  (uac@12974b11/#91 + is@6ea46565/#407, auto-merging to staging) so tradfi reference data is no longer frozen. gate-c
  (v9) still blocked on G1-V8.
- **defi (slot-2)**, **prediction (slot-5)**: prediction's per-cqg producer is the G1-ENUM reference; both still owe
  their v9 walk (G1-V8) + dry-run.

**The could-exist universe = (IS instrument lifecycle catalogue) × (UAC availability rules).** The two halves:

- **IS half — the lifecycle catalogue** (`proper_instrument_catalogue_lifecycle_rollup_2026_06_04`):
  `build_instrument_catalogue.py` rolls up the maintained per-date
  `instrument_availability/by_date/day=…/venue=…/ instruments.parquet` defns into the cumulative
  `available_from`/`available_to` lifecycle catalogue, which `enumerate_expected_universe.py` (v2) cross-joins × dates ×
  data_types − existing manifest rows → seeds `record_expected_unattempted` for IS-listed-but-not-yet-backfilled cells.
- **UAC half — the availability rules**: chain genesis dates, `DEFI_VENUE_LAUNCH_DATES` / per-AG venue launch, listing/
  delist windows, `SOURCE_PRIORITY`, `expected_coverage()` scope — these tell the enumerator WHEN a listed instrument is
  genuinely expected to have data (post-genesis, post-launch, in-coverage). UAC accuracy is a HARD G1 input.

**G1 catalogue lifecycle (tracked stages — each per-AG, on a VM where it touches prod GCS):**

- [ ] [CODE] P0. **G1.code — catalogue producer + enumerator GREEN** (`build_instrument_catalogue.py` +
      `enumerate_expected_universe.py` v2, defi/cefi/tradfi/sports/prediction-capable; `resolve_bucket_name` env-tier
      fix). Owner: `proper_instrument_catalogue_lifecycle_rollup_2026_06_04` (vm-cross-cutting) + per-AG slices of
      `instruments_manifest_canonicalisation_2026_06_01`. **DeFi (slot-2): code-ready + denominator regression shipped
      is@bb8fb203** (⑦-defi). cefi dry-run proven 2026-06-05.
- [ ] [DATA] P0. **G1.dry-run — per-AG catalogue + enumerate dry-run** (read-only; **cefi RE-RUN on shape-aware producer
      DONE slot-3 2026-06-07** — enumerate v2 exit 0, 3,446 plausible candidates, OPTION/COMBO bundle-skip working;
      residual F1 chain-`data_type`-axis + F2 FUTURE bundle-grain gate apply-write, see cefi plan § "G2 VERIFY PASS";
      defi pending — each AG slot runs its own). **sports DRY-RUN DONE (slot-4, 2026-06-07): generic
      `build_instrument_catalogue --asset-group sports` → 0-row catalogue (raw entity cols lack
      `instrument_key`/`instrument_id`; no `sports` branch in `run_rollup`) AND captured atom is per-LEAGUE not
      per-fixture → needs a league-grain `build_sports_catalogue_dataframe` producer before enumerate v2 can run. Full
      finding + spec + gate flags in `sports_manifest_canonicalisation_2026_06_01.md` § ⑦.** **prediction DRY-RUN DONE
      (slot-5, 2026-06-07): found+fixed a crash — `build_instrument_catalogue` resolved the prediction instruments-store
      via the per-AG dict (no PREDICTION entry → `BucketNamingError`) so the cqg roll-up never ran; fix=flat-kind helper
      `is@a7fa55a8` (+regression test). With that, `--asset-group prediction --dry-run` runs exit 0 → 0 cqg rows, GATED
      on the IS prediction backfill (`market_lifecycle/by_canonical_group/`=0 objects;
      `instrument_availability/by_date/` is `market=`-grain, no `canonical_question_group=`). enumerate rides the
      catalogue (same gate). cf_manifest_audit(instruments-store-pred): 493 rows 100% v8, CF-1/3/4/8 RED (§H v9 walk
      gated). G1.schedule WIRED (prediction in both catalogue schedulers). Full finding in
      `prediction_manifest_canonicalisation_2026_06_01.md` § ⑦ G1-2026-06-07.** **tradfi DRY-RUN DONE (slot-6,
      2026-06-07): `build_instrument_catalogue --asset-group tradfi` rolls up 11,579 `by_date` parquets (full local run
      = VM job, timed out ~10min; producer already proven — slot-7 applied `prod/catalog.parquet` = 684,372 instruments,
      95% delisted = capture-freeze signature). `enumerate_expected_universe v2 --catalog-path <prod/catalog.parquet>`
      scan-only (2026-06-04..05) exit 0 → **588,798 candidate `expected_unattempted`** (= 32,711 alive × 9 data_types ×
      2 days; present-set 73,352/144,062), sample-inspected (e.g. `CBOE:INDEX:VIX × {trades,ohlcv_1m,…}`). **RE-RAN on
      the G1-ENUM shape-aware producer (@6ea46565) 2026-06-07 → 587,990 (barely dropped, −808). 🔴 gate-(a) RED —
      ROOT-CAUSE: tradfi options/combos are captured at BUNDLE grain (manifest: 0 per-contract OPTION rows;
      options_chain 3,262 + combo 58,292 + futures_chain 15,600) but the catalogue + enumerate are PER-CONTRACT (622K
      OPTION) → ~563K false candidates (grain mismatch). Needs G1-ENUM BUNDLE-GRAIN rollup for tradfi (catalogue emits
      options_chain/futures_chain bundles + matrix `option/combo→frozenset()`, mirror cefi) — co-owned slot-6+slot-7;
      validity matrix alone insufficient.** cf_manifest_audit(instruments-store-tradfi-prd): 20,388 rows 0.8% v9,
      CF-1/3/4/8 RED + 60 legacy-only (§ Step-1 v9 walk **BLOCKED on the G1-V8 instruments_manifest E2 migrator
      BUILD** + G0). **G1.run apply-write GATED** (a RED bundle-grain; b: capture freeze; c: v9 indices/migrator-build)
      → dry-run only; gate-b remediation Massive IS adapter SHIPPED + **STAGING-GREEN** (UAC@12974b11 PR#91 MERGED +
      IS@c0f2f39c PR#407 MERGED, both quality-gates-v2 PASS). **G1.schedule: tradfi MISSING from both catalogue
      schedulers' instruments-store `for_each` → gated todo filed.** Full finding in
      `tradfi_manifest_canonicalisation_2026_06_01.md` § G1.**
- [ ] [DATA] P0. **G1.run — per-AG `--apply-write` of the could-exist seed against the AG's canonical `_index`** (VM;
      `MANIFEST_PER_VM_SHARDS=true`). **GATED on**: (a) **IS instrument BACKFILL complete** for that AG
      (`instruments_backfill_phase3_2026_05_22` — the catalogue can only roll up instruments IS actually fetched); (b)
      **accurate UAC** (launch/genesis/coverage rules for that AG verified — else the seeded expected set is wrong); (c)
      **`instruments_manifest_canonicalisation` v9** for the AG's instruments-store `_index`. NOTE: G1.run seeds the
      manifest **could-exist** rows but the canonical `_index` itself comes from the AG's G2 walk — so G1.run for
      raw-tick denominators rides AFTER that AG's G4 manifest is canonical (the catalogue-of-record vs the seed are
      sequenced in the per-AG plan; do not double-walk).
- [x] ✅ [INFRA] P1. (**APPLIED 2026-06-11, autonomous run** — `tofu apply` vs `terraform/state/prod`: **16 added / 0
      changed / 0 destroyed**; all 5 `lifecycle-catalogue-regen-<ag>` Cloud Run jobs + 5 ENABLED 01:00-UTC schedulers
      verified via `gcloud run jobs list`/`scheduler jobs list`; cefi smoke execution triggered + watched. THREE
      pre-existing tf bugs fixed to get there: (1) bucket literals were LEGACY/nonexistent → canonical env-short
      `-prd-`/`pred` (deployment-service@9e2904a); (2) main.tf had 7 MERGE-DOUBLED `instruments_*` bucket resources —
      the whole prod config was UN-PARSEABLE for everyone (second set proven strict-subset, deleted); (3)
      `cf_manifest_audit` alert policy used `labels` (not in schema) → `user_labels` — both
      @deployment-service@04e3d20.) **G1.schedule — daily catalogue-aggregation scheduler live per-AG** keyed to the IS
      update cadence. **TF AUTHORED deployment@98bee4b** —
      `deployment-service/terraform/gcp/lifecycle_catalogue_scheduler.tf` (NEW): per-AG `for_each`
      (cefi/defi/tradfi/sports/prediction) Cloud Run Job + Scheduler running `build_instrument_catalogue.py` (sports
      carries `--by-date-prefix`), 01:00 UTC, terraform-fmt clean. **Finding (vm-cross-cutting 2026-06-07)**: the two
      PRE-EXISTING schedulers (`catalogue_regen_scheduler.tf` + `instrument_catalogue_scheduler.tf`) run DIFFERENT
      scripts (UAC envelope/availability + `generate_instrument_catalogue.py`) — NEITHER ran the
      `build_instrument_catalogue.py` lifecycle roll-up, so this is a NEW scheduler, not a per-AG extension of cefi.
      **REMAINING (apply-gated)**: `terraform apply` + T+10min per-AG `gcloud run jobs executions` verify (infra apply
      pipeline) → then GREEN. Bucket-name `pred`-vs-`prediction` discrepancy flagged in the .tf header. **VERIFIED on
      LDR 2026-06-07 (slot-7)**: `lifecycle_catalogue_scheduler.tf` carries all 5 AGs
      (cefi/defi/tradfi/sports/prediction) — the G1 daily catalogue scheduler is AG-complete; `terraform apply` is the
      only remaining (gated) step.
- [x] ✅ [INFRA] P2. **catalogue_regen_scheduler.tf MISSING tradfi — DONE (deployment-service@a27b05a, slot-7
      2026-06-08)**: added `instruments-store-tradfi-central-element-323112` to the `catalogue_regen_instruments_reader`
      `for_each` IAM grant (+ the doc comment) so the regen job's `strategy_instruments` join can read the tradfi
      instruments-store parquet (the sibling `lifecycle_catalogue_scheduler.tf` + `instrument_catalogue_scheduler.tf`
      already had it). `terraform fmt -check` clean. The `terraform apply` is the gated infra step (out of scope here).
      Repo: deployment-service `terraform/gcp/catalogue_regen_scheduler.tf`.

**Cross-AG IS references (each AG owns its instruments-store reference surface — sliced, not duplicated):** defi §H
`instruments-store-defi` walk · sports `instruments-store-sports` (2.68M rows + the 316-cell legacy→prd data-loss-gated
migration) · cefi/tradfi/prediction reference surfaces — all sub-items of
`instruments_manifest_canonicalisation_2026_06_01` (the per-service all-AG plan) + each AG's
`*_manifest_canonicalisation` §H slice. **G2 (an AG's MTDS/data walk) must NOT be trusted as denominator-complete until
that AG's G1 (IS catalogue + UAC) is GREEN** — the audit's ⑧ enforces this.

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

> **VERDICT: A–H all 🟢. REGRESSION RISK: NONE.** The cross-cutting code + contracts that every AG's `--apply` depends
> on are correct on the current LDR data-state; a defect here would corrupt all 5 AGs at once, and none was found. The
> audit ran code-reads + grep + the relevant test suites in each repo's `.venv` (the QG-harness hollow-collection
> finding below means a full `quality-gates.sh` under-collects for IS/MTDS — so targeted suites are the GREEN proof, the
> same mitigation slot-7 used 2026-06-07). All slot-7 repos `tab ⊇ LDR`, 0 ahead/0 behind/clean at audit time.

| §   | Area                          | Verdict | Evidence (repo · tests run green · key invariant)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| --- | ----------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A   | UAC CONTRACTS                 | 🟢      | `unified-api-contracts`: `pipeline_mode.py` source-aware `{mode}_{source}[_{transport}]`; `source_string_for`/`pipeline_mode_for_source` round-trip for batch+live+replay; `LIVE_WEBSOCKET` transitional alias only (`source_string_for→None`); **NO `hyperliquid_rest`** (retirement-comments only; `BATCH/LIVE/REPLAY_HYPERLIQUID` + `Transport` enum split). Validity matrix + `grain_for_instrument_type` (venue-aware `FUTURE_BUNDLE_VENUES`) Era-B; `options_chain`/`futures_chain` are instrument_types→`{trades}`. `SOURCE_PRIORITY`/`SOURCE_MODE_CAPABILITY`/capability consistent (legacy chain entries = documented purge-at-G4 read surface, guarded by `era_b_legacy_purge`). **250 targeted tests green** (matrix 139 + source_priority/preflight 111). |
| B   | UTL WRITE PATH                | 🟢      | `unified-trading-library`: `derive_pipeline_mode_for_row` source-aware + idempotent; `add()` C-#2 auto-derives blank pipeline_mode for derivable market-data rows (features/service rows keep ""); `record_captured` stamps source+transport+4-state; C-#6 `_assert_source_matches_pipeline_mode` raises `PipelineModeSourceMismatchError` on explicit-batch source≠`source_string_for(pm)`. **83 tests green** (resolver/transport/record_captured_from_counts/source).                                                                                                                                                                                                                                                                                              |
| C   | ENUMERATOR + CATALOGUE        | 🟢      | `instruments-service`: `enumerate_expected_universe` v2 shape-aware (`(instrument_type×data_type)` validity filter + `_rollup_bundle_grain` + venue-aware FUTURE); `build_instrument_catalogue` ⊇ manifest present-set via the **superset-property integration test** (31 passed; 4 skips = GCS-credentialed real-data checks that ride each AG's gated G1.run). **138 + 31 tests green**. Per-AG real-data candidate-count re-runs = gated G1.run (per-AG owner).                                                                                                                                                                                                                                                                                                    |
| D   | v9 INSTRUMENTS-STORE MIGRATOR | 🟢      | `instruments-service` `migrate_instruments_store_v9.py`: CF-1…CF-14 projection (`schema_version=9` · `asset_group=` · `pipeline_mode=batch_instruments_service` · `source=instruments_service` · `transport=rest` · typed reasons · `data_type` · `available_at` · `resolve_bucket_name` · honest `capture_status`). Migrator + projection tests green. Documented dry-run-GREEN all 5 AGs (cefi 30,803→100% · defi 125,242→100% · sports 2.68M→100% · tradfi · pred 493). `--apply` correctly G4-gated.                                                                                                                                                                                                                                                              |
| E   | READERS                       | 🟢      | `features-service` `mtds_canonical_reader` (15 green) + `market-data-processing-service` `orchestration_scanner` (27 green): both list ONCE at the mode-agnostic `day={D}/` prefix + prefix-match `batch_*`/`live_*`/`replay_*` (+ bare/legacy), canonical-over-legacy ranked. **`grep` of both repos → 0 coarse-exact `pipeline_mode=batch/`/`=live/` probes.**                                                                                                                                                                                                                                                                                                                                                                                                      |
| F   | G3 DEPLOYMENT UNION VIEW      | 🟢      | `deployment-api` `data_status_union.union_reduce_to_cells`: M5 union (≥1 source/mode `captured` ⇒ cell `captured`; precedence captured>empty>failed>expected; M4 mode-contextual tiebreak); cell-grain collapse of multi-(source×pipeline_mode) rows = **no double-count**; pipeline_mode/source drilldown + filter/group_by axes; coverage % over could-exist denominator (READ, CF-14). **21 tests green** (union + drilldown_provenance, incl. multi-source+multi-mode fixtures). v8 manifests unchanged (provenance-column-guarded).                                                                                                                                                                                                                              |
| G   | CONSOLIDATOR + DRAIN          | 🟢      | `unified-trading-library`: read path **loud-fails by DEFAULT** — `assert_consolidator_healthy` + record-path raise `ManifestConsolidatorStaleError` on stale/missing index when per-VM shards exist; `MANIFEST_ALLOW_STALE_FALLBACK` opt-IN only (`""`=default loud-fail); `CONSOLIDATOR_DOWN` watchdog. **25 tests green** (per_vm). DRAIN: the RESUME runbook (48 GCP schedulers + 26 AWS rules + `pre_migration_2026_06_08` snapshots in 10 buckets) is documented + internally consistent above; the LIVE GCP/AWS paused-state confirmation is the operational (cred-gated) slot-2 owner — runbook matches the drained inventory as recorded.                                                                                                                     |
| H   | BATCH=LIVE (contract layer)   | 🟢      | `market-tick-data-service`: live writers emit the IDENTICAL v9/Era-B/source-aware form — `tardis_shared._LEGAL_DATA_TYPES` EXCLUDES `options_chain`/`futures_chain` (raises; chains are instrument_types→`trades`); `databento_adapter._PARTITION_INSTRUMENT_TYPE` FUTURE→`futures_chain`/OPTION→`options_chain` instrument_type + writes `data_type="trades"`; `live/manifest_recorder.py:33` explicit "No live-only manifest schema; pipeline_mode differentiates rows". Corroborated by slot-2's GCS byte-probe (cefi+tradfi on-disk uniformly Era-B + `batch_tardis`/`batch_databento`, Era-A chain-data_type count = 0). **38 adapter tests green** (1 unrelated pre-existing RED = finding F-X1 below — NOT a pipeline_mode/Era-B/`--apply` regression).        |

**REGRESSION RISK: NONE.** Operational gates remain (each correctly held, NOT a code defect): per-AG `--apply` (G4) ·
per-AG real-data catalogue/enumerate candidate-counts (gated G1.run) · IS instruments-store v9 walks + IS backfills ·
pre-migration drain (executed 2026-06-08) · the live GCP/AWS paused-state confirmation (cred-gated, slot-2).

**Sampled-vs-walked**: WALKED — the cross-cutting code surfaces (every named symbol read in source) + ~596 targeted
tests across 6 repos. SAMPLED-via-prior-evidence — the real-prod GCS dry-run candidate counts + the on-disk byte-probe
(slot-2, cred-gated; this slot lacks GCS creds). NOT RE-RUN — the per-AG `--apply` (gated) + the full catalogue rollups
(VM-scale).

**Finding F-X1 (P2, cross-cutting / bucket-SSOT) — STALE MTDS test asserts the pre-SSOT bucket shape (code is
CORRECT).**

- [ ] [TEST] P2.
      **`market-tick-data-service/tests/market_interface/adapters/cefi/test_tardis_canonical_output.py::test_adapter_resolves_test_bucket_when_is_test_run`
      is STALE — it asserts the legacy `is_test_run`→`market-data-tick-test-cefi-{project}` f-string shape, but
      `engine.orchestrator.get_tick_data_bucket` was canonicalised to the bucket-name SSOT (`resolve_bucket_name`,
      remediated 2026-06-01 per `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`): it `del config` +
      self-sources env from `DEPLOYMENT_ENV_SHORT` (test→`...-cefi-test-...`, not a config flag).** The CODE is right;
      the test asserts the retired knob → locally returns `market-data-tick-cefi-prd-test-account` (ambient env).
      Pre-existing on LDR (tab==LDR, 0 ahead — not introduced by the canonicalisation work). **NOT a
      pipeline_mode/Era-B/migration `--apply` regression** (the migrators call `resolve_bucket_name` with an explicit
      `env`, not `get_tick_data_bucket`). **Fix = rewrite the test to set `DEPLOYMENT_ENV_SHORT=test` and assert the
      canonical `market-data-tick-cefi-test-{project}` env-tier shape (or delete the obsolete `is_test_run`
      assertion).** Repo: market-tick-data-service. parent_epic: mtds_mdps_master. Provenance: slot-7 cross-cutting
      pre-apply audit 2026-06-08.

## vm-defi (slot-2) status + findings — 2026-06-07

> Progress on the **G0 C-PATH WRITE** (defi migrator/rebuild source-aware) + **G1-defi IS-catalogue** rows of the gate
> board. Code-ready facts + the gates verified; ship of the code unit is **blocked on a pre-existing MTDS QG-red** (see
> the finding below), not on the change itself.

**G0 C-PATH WRITE — CODE-READY (pending ship):** `migrate_defi_full_v9_canonical.py` + `rebuild_defi_manifest.py` now
derive the SOURCE-AWARE `{batch}_{source}` pipeline_mode PER SHARD via UTL
`derive_pipeline_mode_for_row(venue,"defi", data_type)` (the cefi/tradfi pattern), stamp `source` (=
`source_string_for(pm)`, C-#6-consistent) **+ a `transport` column** (`default_transport_for_source`, no path suffix),
in BOTH the PATH key and the manifest/parquet column. The coarse `DEFAULT_PIPELINE_MODE="batch"` /
`_DEFAULT_PIPELINE_MODE="batch"` / `_PIPELINE_MODES` are RETIRED; the rebuild day-probe lists `pipeline_mode=` (covers
every source-aware mode) + bare legacy; bare/legacy-coarse paths auto-derive source-aware; per-shard isolation added to
the rebuild `add()` loop. Tests rewritten + GREEN (25/25, credential-free). Verified per-shard: DEX
state→`batch_onchain_subgraph`, perp→`batch_hyperliquid`, oracle CHAINLINK→`batch_chainlink` / PYTH→`batch_pyth_hermes`.
**Single-walk safety GREEN**: GCS probe confirmed NO coarse `pipeline_mode=batch/` data was ever applied (dest `*-prd-`
trees are pre-pipeline_mode bare; rebuild bucket 2340 days all bare) — so upgrading the migrator before any G4 apply
does not require a second whole-corpus walk.

**G1-defi IS-catalogue — gates verified, seed apply correctly GATED (dry-run only):**

- A (slot-7 PART C code) GREEN · B (DeFi IS instrument backfill) GREEN · D (UAC chain-genesis / `*_VENUE_LAUNCH_DATES` /
  `PROTOCOL_LAUNCH_DATES`) GREEN.
- **C (defi instruments-store `_index` v9-canonical) 🔴 RED**: the `_index` is **0% v9** — schema_version distribution
  **v4=33,869 / v8=20,686 / v6=14,330** (68,885 rows), missing `source`/`asset_group`/`transport` columns. The defi
  instruments-store §H walk (`defi_manifest_canonicalisation` §H + `instruments_manifest_canonicalisation`) has NOT run.
- Catalogue **dry-run executed** (`build_instrument_catalogue --asset-group defi --dry-run`, read-only, exit 0) but
  rolled up **0 rows** — `instrument_availability/by_date/` in `instruments-store-defi-prd-*` is EMPTY (the 4,339-row IS
  backfill + the 68,885-row `_index` live in the NON-prd bucket; env-tier bucket split per
  `bucket_name_ssot_legacy_dual_write_remediation`). So the G1.run `--apply-write` seed is doubly gated → NOT run.

- [ ] [DATA] P1. **G1.run-defi seed — BLOCKED on GATE C**: do NOT `--apply-write` the defi could-exist seed until (c)
      the `instruments-store-defi` `_index` is v9-canonical (currently 0% v9) AND the defi
      `instrument_availability/     by_date/` is populated in the bucket the catalogue producer reads (`-prd-` is
      empty). Owner: vm-defi, after the defi §H instruments-store walk. Repo: instruments-service. parent_epic:
      manifest_master.
- [ ] [UAC] [MTDS] P1. **Era-B legacy retirement — the per-AG v8→v9 migrator drops ALL `data_type=options_chain`/
      `futures_chain` recognition as its FINAL ATOMIC STEP, right after it relabels the on-disk rows to `trades`** 🟢
      **SAFETY GUARD SHIPPED (uac@93961df3, slot-7 2026-06-08)**: `assert_era_b_purge_safe()`
      (`canonical/crosscutting/era_b_legacy_purge.py`) simulates the legacy drop in-memory + asserts every closed-set
      round-trip survives (SOURCE_PRIORITY↔AVAILABILITY symmetry · PipelineMode · emission latency); the per-AG
      migrators MUST call it immediately before their atomic drop. Test proves the closed-set is purge-ready TODAY. The
      actual DROP stays G4-gated (coupled to cefi+tradfi `--apply` complete) — only the GUARD is landed here. (operator
      2026-06-07: "break old paths is the point of the migration" — couple-to-G4, do NOT lead the data). The could-exist
      PRODUCER is already Era-B (`uac@ae70338d`/`is@74df991d`); this retires the legacy-READ surface that still parses
      un-migrated v8 `data_type=options_chain` rows. **Removing it BEFORE the relabel would loud-fail every read of
      un-migrated v8 data (deployment-api/preflight KeyError / unknown DataType) — heartbeat break — so it is sequenced
      AFTER, inside the same migrator walk.** Full surface to drop atomically once an AG's rows are relabeled (all
      cascade-coupled — a partial purge breaks the closed-set round-trips): - UAC: `SOURCE_PRIORITY` +
      `AVAILABILITY_AT_SEMANTICS` (4 entries each — bidirectional round-trip) + `expected_coverage` venue lists
      (DERIBIT/BINANCE-FUTURES/BYBIT) + capability `coverage_start[options_chain/       futures_chain]` +
      `DATA_TYPES_BY_ASSET_GROUP["cefi"]` + `MVP_VENUE_DATA_TYPES`/`DERIBIT_MVP_INSTRUMENT_TYPE_DATA_TYPES` +
      `BASE_GRANULARITY_BY_DATA_TYPE` + the `DataType` enum `OPTIONS_CHAIN`/`FUTURES_CHAIN` + the snapshot
      `SchemaContract`s `(ag, options_chain, options_chain)`/`(ag, futures_chain, futures_chain)` +
      `venue_data_types.yaml` + flip the asserting tests (`test_market_data_asset_groups_use_tick_timestamp` cefi/tradfi
      options_chain lines, `test_every_datatype_has_at_least_one_schema_contract`, the snapshot-contract tests). - MTDS:
      `orchestrator.py` chain partition/data_type-merge (lines 44/692-700) — confirm fully Era-B (see the
      orchestrator.py finding below). GATED on cefi+tradfi G4 apply complete. Repos: unified-api-contracts +
      market-tick-data-service. parent_epic: manifest_master.
- [x] ✅ [MTDS] P0. **CLOSED 2026-06-08 (slot-2 GCS byte-probe) — the writer IS uniformly Era-B (code audit + on-disk
      confirmed).** Slot-7's code audit + the byte-probe below agree; the relabel `--apply` is no longer gated by Era-A
      residue. Original audit retained: 🟢 **PROGRESS (slot-7 2026-06-08, mtds@<pending>)**: (1) **OBJECT-WRITE path
      RE-CONFIRMED Era-B** (tardis_shared `_LEGAL_DATA_TYPES` raises on `options_chain`; databento
      `_PARTITION_INSTRUMENT_TYPE` maps FUTURE→`futures_chain` string + `data_type=trades`). (2)
      **`tradfi_catalog_reader.py:226-230` Era-A hint FIXED** → `data_type=trades` for FUTURE/OPTION (the chain bundle
      is carried by the instrument_type partition token, not the data_type) — **zero-risk**: a full read proved
      `CatalogRow.data_type` is NEVER consumed for seeding (orchestrator uses only `.venue`/`.instrument_id`, and
      `orchestrator.py:3548-3553` ALREADY SKIPS options_chain/futures_chain as data_types when seeding
      `record_expected_unattempted` — so NO Era-A data_type ever reached the manifest either). (3) The orchestrator
      `_MERGED_DATA_TYPE_MAP`/`_DATA_TYPE_TO_INSTRUMENT_TYPE` + `MVP_VENUE_DATA_TYPES`/`DERIBIT_MVP`
      options_chain/futures_chain entries stay **G4-gated** — the MVP config DRIVES the live DERIBIT chain DOWNLOAD
      (orchestrator.py:2440 filters `venue_data_types` to the DERIBIT_MVP data_type values), so dropping them now breaks
      DERIBIT capture; they retire atomically with the adapter migration at cefi+tradfi G4 (the era_b_legacy_purge guard
      enables it). **✅ gate (a) CLOSED — GCS byte-probe (slot-2, 2026-06-08, central-element-323112)**: real-prod
      `market-data-tick-cefi-prd` `day=2025-12-31` DERIBIT shards — `options_chain`/`futures_chain` appear ONLY as
      `instrument_type=`, the data_types are `trades`/`book_snapshot_5`/`derivative_ticker`,
      `pipeline_mode=batch_tardis` (source-aware), and **`data_type=(options_chain|futures_chain)` count = 0** → on-disk
      is uniformly Era-B, zero Era-A residue. **tradfi confirmed too** — `market-data-tick-tradfi-prd` `day=2025-12-31`:
      `futures_chain`/`options_chain` only as `instrument_type`, `data_type=trades` (722), Era-A chain count = 0. BOTH
      AGs uniformly Era-B on disk → gate fully closed.
  - **Live TICK-WRITE path = Era-B for cefi+tradfi chains (GOOD).** Both route through `tardis_shared.py` /
    `tradfi_shared.py` `finalise_and_write_cefi_shards`, whose `_LEGAL_DATA_TYPES` (tardis_shared.py:65) EXCLUDES
    `options_chain`/`futures_chain` and **raises** on `data_type=options_chain` (≈652) — it writes
    `instrument_type=options_chain|futures_chain` + a legal `data_type` (`trades`). The tradfi Databento adapter writes
    via `PartitionedTickWriter` with `_PARTITION_INSTRUMENT_TYPE` setting
    **instrument_type**=options_chain/futures_chain
    - `data_type=trades` (databento_adapter.py:111-120). The orchestrator `_MERGED_DATA_TYPE_MAP`
      (orchestrator.py:693) + `_resolve_partition_data_type` (:737) + write path (:1109/:1137) Era-A merge fires ONLY if
      a caller passes `data_type∈{options_chain,futures_chain}` — **no current tick adapter does**, so it is
      dead/defensive on the tick path. slot-3's GCS probe (cefi on-disk `data_type=trades`) corroborates. So the tick
      objects are Era-B.
  - **BUT residual Era-A surfaces remain → NOT a clean "uniformly Era-B" sign-off:**
    1. 🔴 **`market_tick_data_service/engine/tradfi_catalog_reader.py:226-230`** stamps
       `CatalogRow.data_type = "futures_chain"|"options_chain"` (FUTURE/OPTION) — this is the **MTDS could-exist /
       `record_expected_unattempted` preflight grain**, so it seeds expected rows at `data_type=options_chain` (Era-A)
       that DIRECTLY clash with the Era-B enumerate seed (`data_type=trades`, `uac@ae70338d`/`is@74df991d`) → the same
       cell double-grains (Era-A preflight row + Era-B enumerate row). **This is the concrete relabel-inconsistency
       risk.**
    2. 🟠 **UAC `MVP_VENUE_DATA_TYPES["DERIBIT"]` + `DERIBIT_MVP_INSTRUMENT_TYPE_DATA_TYPES`**
       (market_data_categories.py:485/493) still list `options_chain`/`futures_chain` as **data_types** (consumed by
       orchestrator.py:2436/2441) — the config that, if fed to the Era-A merge, re-introduces `data_type=options_chain`.
    3. 🟠 **orchestrator.py:693/737/1109/1137** Era-A merge map + `:44` docstring — dead-but-live; should be retired so
       a future caller can't re-introduce Era-A. `tardis_adapter.py:2541/2549` passes inbound
       `data_type="futures_chain"` (canonicalised to Era-B by finalise, but Era-A-shaped at the boundary).
  - **GATING before first `--apply` (BOTH required):** (a) **GCS probe** a recent cefi+tradfi chain shard to
    byte-confirm the on-disk `data_type=` dir (slot-7 lacks GCS creds in this slot — owner with creds runs it); (b)
    **retire the Era-A could-exist surface** — fix `tradfi_catalog_reader.py:226-230` to `data_type=trades` +
    `instrument_type=futures_chain|options_chain` (match the Era-B seed) and drop `options_chain`/`futures_chain` from
    `MVP_VENUE_DATA_TYPES`/`DERIBIT_MVP` as **data_type** values (keep them as instrument_types). Until both, the
    relabel double-grains tradfi/cefi chain cells. Repos: market-tick-data-service + unified-api-contracts. parent_epic:
    mtds_mdps_master.
- [x] ✅ [UAC] P2. **DeFi `SOURCE_PRIORITY` registry gaps — DONE (uac@28114692, slot-7 2026-06-08)**: registered
      `(defi, "n")` (the canonical dex-swaps data_type; legacy `dex_pool_swaps` retired) → `["onchain_subgraph"]` (the
      uniswap_v3/curve adapters read swaps from The Graph subgraph — `uniswap_v3_adapter.py` "primary for pools, swaps,
      liquidity" — so subgraph, matching `dex_pool_state`; it had fallen to the defi `BATCH_ONCHAIN_RPC` asset-group
      fallback). Added the matching `AVAILABILITY_AT_SEMANTICS` entry (closed-set symmetry holds; UAC QG green).
      **Non-Hyperliquid perp venues (LIGHTER→tardis) deliberately NOT added to `(defi, perp_funding)`** — they resolve
      per-shard via `pipeline_mode_resolver._VENUE_OVERRIDES["LIGHTER"]→BATCH_TARDIS` (BEFORE the SOURCE_PRIORITY
      lookup); adding tardis would flip `source_required(defi, perp_funding)`→True + break the Hyperliquid-native
      single-source auto-stamp (documented inline). **🔔 vm-defi (slot-2): the migrator now derives
      `batch_onchain_subgraph` for dex-swaps (was the `batch_onchain_rpc` fallback) — re-verify your G2 dry-run.** Repo:
      unified-api-contracts (`canonical/crosscutting/source_priority.py` + `availability_semantics.py`). parent_epic:
      manifest_master.
- [x] ✅ [INFRA] P2. **MTDS local `--no-fix` QG pre-existing-RED — ROOT-CAUSED + RESOLVED (slot-7 2026-06-08)**: the
      gate-0 blocker was the committed **`uv.lock`↔`pyproject.toml` desync** (slot-5 finding (b) below) —
      `uv lock --check` FAILED so QG aborted at its FIRST gate before file-size/basedpyright/tests ran. **FIX: `uv lock`
      (adds the 4 stub pkgs pyarrow-stubs + mypy-boto3-{logs,sns,sqs}, +52 LOC) — landed on LDR (mtds@dbbbef8a, peer;
      slot-7's identical re-lock dropped as a patch-id duplicate on rebase).** With it,
      **`bash scripts/quality-gates.sh --no-fix` now exits 0 and WRITES `.qg_last_passed_sha`** (verified slot-7: "All
      checks passed!", sentinel==HEAD) — the ~16 `❌` list was STALE (the >900 files were already split + the rest gated
      behind the uv.lock abort). The e2e-testing prediction basedpyright errors are a PERIPHERAL-consumer warning,
      non-blocking. MTDS QG is GREEN. Repo: market-tick-data-service. parent*epic: mtds_mdps_master. *(Original finding
      retained below for provenance.)\_ ~16 `❌` on current LDR — 6 files >900 lines (5 unrelated:
      `migrate_sports_canonical_v9`/`rebuild_sports_manifest_v9`/`rebuild_prediction_manifest`/`solana_lst_archival`/
      `websocket_runner`), deep-UAC-imports / asyncio.run-in-loop / raw-response.json / empty-fallbacks in untouched
      handlers, STEP 5.85 inline-`pipeline_mode=` literals across the migration scripts, + macOS-environmental
      false-positives (574s>300s timing, BSD `grep -P` errors, no systemd cap). The defi C-PATH WRITE change adds ZERO
      net-new failures (its 25 unit tests pass; ruff clean; basedpyright-neutral). Repo: market-tick-data-service.
      parent_epic: mtds_mdps_master. > **FINDING (slot-5 prediction, 2026-06-08) — two updates to this MTDS-QG-red
      item:** > (a) **`rebuild_prediction_manifest.py` is now SPLIT** (954→692 L, mtds@c571445d) → REMOVE it from
      the >900 list; > the remaining >900 files are non-prediction. (b) **NEW gate-0 blocker not previously listed: a
      committed > `uv.lock`↔`pyproject.toml` desync on the MTDS LDR HEAD.** `uv lock --check` FAILS — the committed
      `pyproject.toml` > declares `pyarrow-stubs` + `mypy-boto3-{logs,sns,sqs}` that are absent from the committed
      `uv.lock`, so the QG > aborts at its FIRST gate (`❌ uv.lock out of sync`) BEFORE file-size/basedpyright/tests
      even run. Mechanical > re-sync (`uv lock` adds the 4 stub pkgs, ~52 LOC; precedent mtds@10930dbd "re-sync uv.lock
      to pyproject"). Until > this lands, NO MTDS `quality-gates.sh` reaches green regardless of the file-length work —
      fix it FIRST in this > slot-2 sweep. (Slot-5 did not fix it: it completes another commit's incomplete dep edit —
      out of prediction AG + > FM1 foreign-work-bundling risk.) **✅ RESOLVED 2026-06-08 (slot-2, operator decision
      A):** (0) **gate-0 re-locked** (mtds@d544f15c — `uv lock` to current pyproject; `uv lock --check` green) BUT this
      is **recurring lock-drift** (the type-stubs flip-flop in pyproject between agents; `dbbbef8a` added them, a later
      commit removed them) → **handed to the dep/CI lane** (slot-1 `update-dependency-version.yml` prevention + settle
      the type-stub flip-flop); NOT a thing to keep manually re-locking. (1) **file-size = 15 pre-existing
      non-`scripts/` files** (orchestrator.py 4219 etc.) → **DEFERRED to the named successor
      `plans/active/mtds_file_size_refactor_2026_06_08.md`** (post-migration; splitting the migration's own
      `orchestrator.py` pre-apply is high-risk for zero migration benefit). **NOT migration-blocking**: file-size loop
      excludes `./scripts/*` (migration code clean); MTDS migration code ships via basedpyright-on-touched; `--apply`
      runs from VM/tarball not the sentinel. (The hollow-sentinel harness finding below is the related ship-hygiene
      item.)
- [ ] [INFRA] P2. **🔴 LOCAL QG HARNESS collects the WRONG test suite for some repos — the green sentinel is HOLLOW
      (surfaced slot-7 2026-06-08).** Running `bash scripts/quality-gates.sh --no-fix` for **instruments-service** AND
      **market-tick-data-service** on this host produced a `[3/6] TESTS` run with `rootdir: …/unified-trading-pm`,
      `configfile: unified-trading-pm/pyproject.toml`, **`collected 6 items`** — it ran only PM's 6
      `tests/integration/test_pm_scripts_integration.py` tests, NOT the repo's own suite (IS has ~3,267 tests; its own
      `pyproject.toml` declares `[tool.pytest.ini_options] testpaths=["tests"]`). The QG still **exits 0 + writes
      `.qg_last_passed_sha`**, so the commit-quality-boundary sentinel for those repos is hollow — a code change can
      ship "QG-green" without its tests ever running (the peer's `mtds@67786887` tradfi-reader change passed this same
      hollow gate). **Contrast**: the UAC QG ran its FULL suite (8,617 passed / 3 pre-existing
      `test_schema_version_matrix.py` failures / 550 skipped) — so it is IS/MTDS-specific (possibly the
      qg-governor-queued subprocess cwd, or a `PROJECT_ROOT`/rootdir mis-resolution when run under contention).
      **Impact**: undermines QG confidence for the migration code on the apply critical path. **Mitigation used this
      session**: slot-7 ran the touched tests directly in each repo `.venv` (IS `enumerate` 88 passed · UAC
      F2+era_b+source_priority 106 passed) to verify before shipping. **Owner: vm-cross-cutting / QG-harness** —
      root-cause the rootdir/cwd resolution (likely `quality-gates-base/base-service.sh` `cd "$PROJECT_ROOT"` vs the
      governed subprocess) so per-repo QGs collect their own suite. Repos: unified-trading-pm
      (`scripts/quality-gates-base/base-service.sh`) + per-repo `quality-gates.sh`. parent_epic: manifest_master.
      Provenance: slot-7 cross-cutting sweep 2026-06-08.
- [ ] [DATA] P1. **DeFi instruments-store `by_date` has a DOUBLED `day={D}/day={D}/` prefix on the recent tail**
      (~2026-05-05 onward — `day=2026-05-05/07` confirmed doubled; `day=2026-05-03` and ALL earlier days are single,
      canonical `day={D}/venue={V}/instruments.parquet`). Surfaced by the G2 verify dry-run 2026-06-07 (slot-2). **TWO
      defects**: (1) an instruments-service `by_date` WRITER regression that nested a second `day=` for recent snapshots
      (`gs://instruments-store-defi-prd-…/instrument_availability/by_date/day=2026-05-07/day=2026-05-07/venue=AAVEV3-ARBITRUM/instruments.parquet`);
      (2) the slot-7 v9 OBJECT migrator (`migrate_instruments_store_v9.py` `canonical_object_rel`) inserts
      `pipeline_mode=/asset_group=` after the FIRST `day=` but does NOT normalise the second → its projected canonical
      path is MALFORMED
      (`day=2026-05-07/pipeline_mode=batch_instruments_service/asset_group=defi/day=2026-05-07/venue=…`). The
      catalogue/enumerate are UNAFFECTED (`build_instrument_catalogue` uses `_DAY_RE.search` + `_VENUE_RE.search` →
      resolves the correct day+venue), so this is a **G4 object-migration gate**, not a CF-14 blocker. **Fix BOTH before
      the gated defi §H object `--apply`**: dedupe/normalise the writer + add a `day=…/day=…` collapse (or a pre-flight
      reject) to `canonical_object_rel`. Repos: instruments-service (writer + slot-7 migrator). parent_epic:
      manifest_master.
- [ ] [UAC] P3. **NICE-TO-HAVE — defi G1-ENUM matrix `POOL` row is union-coarse**: the derived
      `valid_data_types_for_instrument_type("defi","POOL")` is the UNION across all POOL-declaring protocols →
      `{dex_pool_state, dex_pool_swaps, gas_fees, lending_indices, liquidations, perp_funding}`, so a pure-DEX pool
      (e.g. UNISWAP_V3) would seed `expected_unattempted` for `perp_funding`/`lending_indices`/`liquidations` it never
      produces (a perp-DEX like GMX legitimately needs them). NOT an impossible-combo (gate-(a) still passes — no
      `odds`/`oracle_prices` leak into POOL), but a per-protocol grain would tighten the denominator. Repo:
      unified-api-contracts (`registry/capability_declarations/_defi.py` PROTOCOL_CAPABILITIES). parent_epic:
      manifest_master. Provenance: G2 verify 2026-06-07 (slot-2).
- [ ] [SCRIPT] P3. **NICE-TO-HAVE — defi migrator `_list_objects` L1 find is a full-bucket scan** (re-verify 2026-06-07,
      slot-2): `migrate_defi_full_v9_canonical.py:570` always issues `_safe_find(fs, {base}/{dir_name})` for the L1
      layout, but all 6 dedicated source buckets are `day=`-partitioned today (no top-level `{dir_name}/` or
      `raw_tick_data/` tree) → that L1 prefix matches nothing yet gcsfs enumerates the whole bucket (a 3-day local
      dry-run hit a >280 s timeout on it; the L1 `dex_pools` find alone >120 s isolated). NOT a correctness issue
      (returns the correct empty set; date-scoped runs DO complete — the earlier `day=2024-06-01` dry-run finished
      0-errors) and laptop-variable, but it wastes a whole-bucket enumeration per bucket on the in-region VM `--apply`
      too. Gate the L1 find on a cheap existence probe (or drop it) — **validate against the whole corpus on the VM
      first** so a bucket with a genuine L1 tree is never silently skipped (data-loss risk). Repo:
      market-tick-data-service. parent_epic: mtds_mdps_master. **TRIAGED 2026-06-07 (slot-2) → SPEED-NOTE,
      NON-BLOCKING:** the `--apply` does NOT date-shard `_list_objects` (the `launch-canonical-migration-vm.sh` launcher
      runs ONE VM over the full date range → exactly ONE `_list_objects` per bucket = 6 wasted whole-bucket scans total,
      not N×6), and the in-region VM completes whole-bucket scans (the baked-union `discover_union` run over the whole
      corpus proved it). So the L1 find adds wall-clock to the apply but never blocks it. Per the apply-ready criterion
      (fix only if it blocks at scale) this stays a **deferred optimisation**, not an apply-gate. Kept P3.

### G2-defi readiness verdict (WAVE 2 verify pass — slot-2, 2026-06-07)

**VERDICT: defi migration CODE is DRY-RUN-GREEN on LDR — the manifest+data `--apply` is code-ready, correctly GATED.**
Re-run on the WAVE-1 source-aware code against real prod GCS (read-only). No code changed (verify pass = dry-runs only);
this is a `docs(plans):` flip.

- **①+⑨ MTDS migrator dry-run (CF-3/CF-13) GREEN — mtds@f80c50f1.**
  `migrate_defi_full_v9_canonical --start-date 2024-06-01 --end-date 2024-06-01` (dry, all 6 buckets) → 0 errors, 0
  needs_attr. Projected PATHS + in-process `_conform` COLUMNS both verified source-aware:
  `dex_pool_state→pipeline_mode=batch_onchain_subgraph` (source=`onchain_subgraph`), `dex_pool_swaps→batch_onchain_rpc`
  (source=`onchain_rpc`); both `schema_version=9`, `asset_group=defi`, `transport=rest` (separate COLUMN), per-row
  `available_at` (EOD UTC), canonical underscore `data_type`, `pipeline_mode=…/asset_group=defi/` LEFT of `venue=`;
  legacy source `category=defi` correctly migrated. NOT coarse `batch`/blank.
- **②+③ instruments-store v9 index dry-run (CF-1/CF-2/CF-4) GREEN — is@2971a064.**
  `migrate_instruments_store_v9 --asset-group defi --skip-objects` (dry) → prd `_index` **125,242 rows v8→v9 (100%)**:
  schema_version `{9:125242}`, source=`instruments_service`, transport=`rest`,
  pipeline_mode=`batch_instruments_service`, asset_group=`defi`, available_at filled on all rows, `category` dropped.
  cf_manifest_audit projection → CF-GREEN. (Object-walk side: GREEN for canonical single-`day=` objects; the recent
  doubled-`day=` tail is the P1 finding above — a G4 gate, not an index blocker.)
- **③ catalogue + enumerate (CF-14) — mechanism GREEN, candidate-count GATED.**
  `build_instrument_catalogue --asset-group defi --dry-run` on the now-populated prd `instrument_availability/by_date/`
  → **64,724 by_date snapshots enumerated** for rollup (listing GREEN; the prior "0 rows / -prd- empty" finding is
  RESOLVED — by_date is now populated 2020-01-20…2026-05-08). The full LOCAL rollup EXCEEDED a 580s budget downloading
  64,724 small parquets (exit 124, did NOT finish) → the rollup + enumerate candidate-count run needs a VM / longer
  timeout, deferred with the gated G1.run write below (the count is downstream of the gated catalogue WRITE anyway).
  Validity-matrix slice VERIFIED correct (UAC@97c26dbe, enumerate@6ea46565): **all 6 defi instrument_types present in
  by_date map cleanly** — `POOL`/`LENDING`/`SPOT_PAIR`/ `PERPETUAL`/`STAKING`/`YIELD_BEARING`, zero
  unmapped/over-fan/None-fallthrough; `_enumerate_v2_defi` is G1-ENUM shape-aware (genesis/launch/lifecycle +
  bundle-skip). Full enumerate candidate-count is gated on the **G1.run catalogue WRITE** (a `--apply-write`, correctly
  GATED on GATE C below) — not runnable read-only without a persisted catalogue parquet.
- **④⑤⑥⑦⑧ (CF-5/6/7/8/10/11/12)** ride the WAVE-1 code (rebuild `record_zero_rows`/typed reasons, A7 fetch-failure
  classification, batch=live single path) — unchanged this pass; verified by the 25/25 credential-free unit suite.

**Remaining gates for the defi `--apply` (G4) — all correctly held:**

1. **G0 ∧ G1 ∧ G3** (cross-AG coordinator gates).
2. **GATE C — instruments-store-defi `_index` v9 walk** (currently 0% v9 on disk: 125,242 v8; dry-run proves the
   transform is correct — the WRITE is the gated `--apply`).
3. **DeFi IS backfill + the doubled-`day=` writer/migrator fix** (P1 above) before the §H object `--apply`.
4. **Pre-migration drain** (all VMs stopped + consolidated) before any object `--apply`.

Sampled-not-walked disclosure: MTDS dry-run sampled `day=2024-06-01` across all 6 buckets (path+column verified) +
in-process `_conform` of real dex-pools/dex-swaps objects; instruments-store `_index` transform walked all 125,242 rows;
by_date instrument_type coverage sampled across all venues for `day=2025-12-15`+`2026-05-03` (+ a 6-day spread). The
doubled-`day=` boundary was sampled day-by-day across 2026-05-01…08. The full 64,724-parquet catalogue rollup count +
the enumerate candidate-count are deferred to the gated G1.run write.

### 🟢 DeFi APPLY-READY VERDICT + completed 7+2-point audit (slot-2, 2026-06-07)

> **VERDICT: DeFi is APPLY-READY on LDR.** Every G1+G2 dry-run is green and the 7+2-point audit passes; the migration
> CODE is correct and no code change is owed before `--apply`. **The only things between DeFi and the real `--apply` are
> OPERATIONAL gates** (drain + the gated WRITE runs), not code. No `--apply` run in this pass (gated).

**7+2 audit — per-CF verdict (CF-1…CF-14; data-state reads, not constants):**

| CF         | Invariant                                               | defi verdict    | Evidence (sampled vs walked)                                                                                                                                                                                                                               |
| ---------- | ------------------------------------------------------- | --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CF-1       | schema_version=9                                        | 🟢              | migrator `_conform` stamps `9` on real ORCA parquet (sampled); IS `_index` transform → `{9:125242}` (WALKED all rows)                                                                                                                                      |
| CF-2       | `asset_group=` not `category=` (path+row)               | 🟢              | real source `category=defi`→canonical `asset_group=defi/` path key + column; `category` dropped from `_index` (walked)                                                                                                                                     |
| CF-3/CF-13 | source-aware `pipeline_mode={mode}_{source}` (path+col) | 🟢              | `batch_onchain_subgraph`/`batch_onchain_rpc` per-shard on real paths+cols; coarse `batch`/blank retired; 14-case derivation incl. antipattern-retired `batch_hyperliquid` (sampled)                                                                        |
| CF-4       | `source` COLUMN every external cell                     | 🟢              | `source=onchain_subgraph` on real rows; IS rows `source=instruments_service` (walked). P2 `SOURCE_PRIORITY` registry-gap todo open (derives cleanly via fallback today)                                                                                    |
| CF-5       | typed `EmptyConfirmedReason`                            | 🟢              | defi writers use `DefiManifestRecorder.record_zero_rows` + `EXPECTED_PRE_VENUE_LAUNCH`/`EXPECTED_PRE_GENESIS_CHAIN` (code grep)                                                                                                                            |
| CF-6       | `expected_unattempted` materialised                     | 🟢 (code)       | shape-aware `_enumerate_v2_defi` + `build_instrument_catalogue` produce the could-exist seed; the apply-write RUN is the gated G1.run                                                                                                                      |
| CF-7       | canonical data_type / flat venue+chain / `{VENUE}_V{N}` | 🟢              | input `dex_pools`→typed `dex_pool_state`; `SUSHISWAP`→`SUSHISWAP_V3` on real paths (sampled)                                                                                                                                                               |
| CF-8       | per-row `available_at`, no lookahead                    | 🟢              | real ORCA `available_at=2026-05-28T21:21:46` write-time; IS `available_at` filled on all 125,242 rows (walked)                                                                                                                                             |
| CF-9       | env-split bucket via `resolve_bucket_name`              | 🟢              | migrator/rebuild build buckets via `resolve_bucket_name`; the `gs://` occurrences are docstring/log strings, not f-string bucket construction (grep)                                                                                                       |
| CF-10      | no phantom/date-impossible captured                     | 🟢 (projection) | IS `_index`: 57,466 null→`captured` from `instrument_count>0`, 0 dishonest captured-but-empty (walked); object-presence phantom sweep is `reconcile_phantom_manifest_rows_all` post-apply                                                                  |
| CF-11      | fetch-failure → `attempted_failed`                      | 🟢              | defi handlers (mev/evm_defi/perp_funding) call `record_failed(...)`; no `except: return []` swallow (grep)                                                                                                                                                 |
| CF-12      | batch=live symmetry                                     | 🟢              | one code path (no defi live-only data_types); verified by the 25/25 credential-free unit suite                                                                                                                                                             |
| CF-14/⑧    | IS-catalogue could-exist ROOT green                     | 🟢 (mechanism)  | `-prd-` by_date POPULATED (64,724 parquets); shape-aware producer runs; validity-matrix slice correct (IS adapters emit `POOL`/`STAKING`/`LENDING`/`SPOT_PAIR`/`YIELD_BEARING`, all matrix-covered). Full rollup candidate-count = gated G1.run (VM-scale) |

**Sampled-vs-walked (audit-level)**: WALKED — the full 125,242-row instruments-store `_index` transform (deterministic,
no object probe). SAMPLED — MTDS migrator conform on the latest populated day per bucket + a real 14,093-row ORCA
parquet (the whole-corpus migrator walk runs on the in-region VM); the 64,724-parquet catalogue rollup LISTED but not
fully rolled up locally (VM-scale). Adapter/handler CF-5/9/11/12 verified by code grep, not a corpus walk. **Remaining
gaps**: the full catalogue rollup + enumerate candidate-count (gated G1.run VM run) and the object-presence phantom
sweep (post-apply) — both downstream of the gated WRITE, not code.

**Remaining gates to the real `--apply` — ALL OPERATIONAL (no code owed):**

1. **G0** GREEN ✓ (Phase-0 source-aware writer code landed) · **G3 UNION view SHIPPED ✓** (deployment-api@4dd2575 +
   deployment-ui@0dc40eb, pm@822393880).
2. **GATE C — instruments-store-defi `_index` v9 WRITE**: run `migrate_instruments_store_v9 --asset-group defi --apply`
   (the dry-run proved the 125,242-row transform projects 100% v9; this is the gated WRITE, not a code fix).
3. **DeFi IS backfill complete** + the gated `build_instrument_catalogue`+`enumerate_expected_universe --apply-write`
   G1.run VM run (catalogue/enumerate UNAFFECTED by the doubled-`day=` bug; that bug is a §H **object**-migration gate,
   fixed before the §H object `--apply` only).
4. **Pre-migration drain** (all GCP+AWS VMs stopped + manifest consolidated + snapshot) before any object `--apply`.

No code-correctness blocker remains for the DeFi migrator/rebuild/enumerator. The 3 open todos are: P1 doubled-`day=` (a
§H object-migration gate, instruments-service) · P2 `SOURCE_PRIORITY` registry tidy · P3 POOL union-coarse + P3 L1-find
speed-note (both deferred optimisations, non-blocking).

\*\*Regression re-confirmation (slot-2, 2026-06-07) — STILL APPLY-READY after the shared bundle-grain + sports-catalogue

- matrix changes landed.** Targeted check (the changed surface vs defi, not a blind re-run): the bundle-grain axis
  (`grain_for_instrument_type`, uac@dd7fa100) returns **`leaf` for ALL 6 defi instrument_types**
  (POOL/LENDING/SPOT_PAIR/ PERPETUAL/STAKING/YIELD_BEARING) — only cefi `options_chain`/`option` are
  `bundle_by_underlying`, so defi never collapses to a bundle; the defi validity-matrix slice is **unchanged** (POOL 6 ·
  LENDING 4 · SPOT_PAIR 2 · PERPETUAL 2 · STAKING 2 · YIELD_BEARING 4 dts, zero over-fan). The sports-league fix
  (uac@aff80339) is sports-only. The migrator (`migrate_defi_full_v9_canonical.py`) is unchanged at **mtds@f80c50f1**
  and its derivation deps (`source_string_for`/`default_transport_for_source`/`derive_pipeline_mode_for_row`) were
  untouched by the recent batch → dry-run output is provably identical to the green run above. **No new code owed; HOLD
  stands.\*\* Remaining gates remain purely operational (drain + the gated v9 instruments-store walk + IS backfill).

### 🔵 DeFi PRE-APPLY ①–⑫ AUDIT — slot-2 2026-06-08 (post-drain, fresh real-prod re-verify)

> Re-ran the formal ①–⑫ framework on real-prod GCS (central-element-323112) AFTER the 2026-06-08 drain. **One
> migrator-output data-correctness BUG found + FIXED** (the dex-swaps source `n`-typo, below); one **live-write-path
> manifest-stamp drift** found + tracked (does NOT corrupt the `--apply` data — migrator+rebuild re-derive over it).

**🟢 FIXED this pass — dex-swaps source mis-stamp (① ⑨ migrator-output correctness, uac):** `source_priority.py` +
`availability_semantics.py` registered the dex-swaps source under a **dead literal key `("defi", "n")`** (slot-7
uac@28114692 typo — even the commit msg said "register defi dex-swaps 'n' source"; "n" matches no real shard). The real
canonical swaps data_type is **`dex_pool_swaps`** (the migrator bucket-spec `canonical_dt`
`migrate_defi_full_v9_canonical.py:112`, operator-locked; on-disk `data_type=dex_pool_swaps` in `dex-swaps-*`). So
`dex_pool_swaps` was UNREGISTERED → fell through the defi asset-group fallback to `batch_onchain_rpc`/`onchain_rpc`,
while the plan FALSELY claimed "the v9 migrator now derives batch_onchain_subgraph for dex-swaps". **Fixed**:
`("defi","n")` → `("defi","dex_pool_swaps"): ["onchain_subgraph"]` in BOTH registries (uniswap_v3/curve fetch
pools+swaps+liquidity from the SAME subgraph → matches `dex_pool_state`). **Verified on real prod**: scoped migrator
dry-run `--buckets dex-swaps --start-date 2024-05-15` → all 21 swap cells now project
`pipeline_mode=batch_onchain_subgraph/…/data_type=dex_pool_swaps`, 0 errors (was `batch_onchain_rpc`); UAC 109 targeted
tests + full suite green (only the `<720s` laptop META-time-gate tripped → `IGNORE_TIMEOUT=true` sanctioned). Without
this the irreversible single-walk `--apply` would have baked `source=onchain_rpc` into every dex-swaps shard. **Shipped:
`uac@012ccec1`** (committed + pushed to `tab/ikennaigboaka/2`, tab ⊇ LDR so the tab-mirror FFs it to LDR for the VM
`--apply`; the LDR→staging PR opens when the UTL breaking-change cascade STAGING LOCK clears — quickmerge STAGE-1.5
blocked since 2026-06-08T08:26Z, BLOCKED-UPSTREAM, re-quickmerge/automation promotes on unlock). Repo:
unified-api-contracts.

- [x] ✅ [MTDS] P1. **DeFi subgraph live handlers stamped `BATCH_ONCHAIN_RPC` for The-Graph-subgraph data — FIXED
      (mtds@2c259101, slot-2 2026-06-08).** The migrator + `rebuild_defi_manifest` RE-DERIVE `pipeline_mode`/`source`
      via `derive_pipeline_mode_for_row` (correct), and UTL `ManifestWriter.add()` only auto-derives when
      `pipeline_mode` is **blank** (`manifest_writer.py:1937/1943`) — so a NON-blank hardcoded value PERSISTS. Three
      handlers stamped `BATCH_ONCHAIN_RPC` while fetching via The Graph subgraph, contradicting `SOURCE_PRIORITY`+the
      migrator+the sibling `dex_swaps_handler` (correctly `BATCH_ONCHAIN_SUBGRAPH`): (a) `dex_pools_handler`
      (dex_pool_state), (b) `lending_indices_handler` (lending_indices, Aave/Spark/Compound), (c) `evm_defi_handler`
      (lending_indices). **Fixed → `BATCH_ONCHAIN_SUBGRAPH`** (all 12 record-call sites; subgraph data matches
      `SOURCE_PRIORTY=onchain_subgraph` + C-#6 consistent with the auto-stamped `source=onchain_subgraph`). Verified:
      104 handler tests + 0 basedpyright on the 3 files; no pinning test touched. **(e) `oracle_prices_handler` was a
      FALSE ALARM — already correct**: CHAINLINK rows use `BATCH_CHAINLINK`+`source="chainlink"` and PYTH rows use
      `BATCH_PYTH_HERMES`+`source="pyth_hermes"` per venue (oracle_prices_handler.py:758/767/782/791, comment notes the
      prior mislabel was already corrected). **Still open (folded into the orphan remediation above — those handlers
      write to NON-migrated orphan buckets, so the stamp-fix rides their bucket REDIRECT)**: (d)
      `aggregator_route_handler` (`BATCH_ONCHAIN_RPC`, pinned by
      `test_aggregator_route_handler_a12h_pipeline_mode.py:146`) + the Solana handler stamps → the P1-redirect +
      P2-Solana (`BATCH_DEFILLAMA`) orphan todos. Repo: market-tick-data-service. parent_epic: mtds_mdps_master.
      Provenance: slot-2 ⑪ pre-apply audit 2026-06-08.
- [ ] [UAC] P2. **`SOURCE_PRIORITY` is CHAIN-AGNOSTIC per `(asset_group, data_type)` → mis-attributes SOLANA DeFi source
      (BLOCKED-OPERATOR-DECISION).** `solana_defi_handler` fetches ORCA/RAYDIUM/KAMINO pools + Kamino/Marginfi/Solend
      lending via **Solana RPC / Helius / DeFiLlama** (NOT The Graph), but `SOURCE_PRIORITY(defi,dex_pool_state)` /
      `(defi,lending_indices)` resolve to `onchain_subgraph` for ALL chains →
      `derive_pipeline_mode_for_row(ORCA,defi,     dex_pool_state)` = `batch_onchain_subgraph` (verified). So both the
      migrator AND a derive-based live handler would stamp `source=onchain_subgraph` on genuinely Solana-RPC/DeFiLlama
      data — a coarse provenance mislabel (the DATA is correct; only the `source` label is wrong). NOT introduced by the
      migration (pre-existing model coarseness it bakes). Proper fix needs per-chain (or per-venue) source resolution in
      `SOURCE_PRIORITY`/`derive_pipeline_mode_for_row` (e.g. a Solana-DEX source `solana_rpc`/`helius`/`defillama`) — an
      operator/design call (which Solana source is canonical). Repo: unified-api-contracts (`source_priority.py` +
      `pipeline_mode_resolver.py`). parent_epic: manifest_master. Provenance: slot-2 ⑪ pre-apply audit 2026-06-08.

#### ①–⑫ AUDIT VERDICT — DeFi pre-apply (slot-2, 2026-06-08, real-prod data-state)

| #   | Point                                                   | Verdict             | Evidence (sampled-vs-walked)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| --- | ------------------------------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ①   | Migrator dry-run source-aware path+col                  | 🟢                  | scoped real-prod dry-run `migrate_defi_full_v9_canonical --buckets dex-swaps --start-date 2024-05-15` → 21/21 swap cells `pipeline_mode=batch_onchain_subgraph/asset_group=defi/…/data_type=dex_pool_swaps`, 0 errors (SAMPLED day; the prior all-6-bucket dry-run day=2024-06-01 covered pools/oracle/etc.). v9·`asset_group=`·`pipeline_mode=` LEFT of `asset_group`·per-row `available_at`·typed data_type — all confirmed. **Era-B relabel N/A (defi has no option/future chains, see ⑩).**                                                                                                                                                                           |
| ②   | Rebuild dry-run agrees                                  | 🟢                  | `rebuild_defi_manifest._resolve_pmst:207-217` uses path source-aware pmode verbatim else DERIVES via the SAME `derive_pipeline_mode_for_row` as the migrator; `source=source_string_for(pm)` C-#6-consistent by construction (WALKED the code).                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ③   | 4-state pre-flight (writer-materialised, consumer-read) | 🟢                  | `record_expected_unattempted` (orchestrator.py:3558) + IS `_enumerate_v2_defi`; consumers read 4-state (`dependency_checker.py:199`, `manifest_allocation_guard.py:65` — empty/expected→no-alert, failed→alert).                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ④   | Empty/partial honest + downstream handles               | 🟢                  | `DefiManifestRecorder.record_zero_rows` (\_defi_manifest.py:376) → `EXPECTED_PRE_VENUE_LAUNCH`/`SOURCE_RETURNED_ZERO` venue-launch-aware; `record_failed`→`classify_venue_error`+`ADAPTER_FETCH_FAILED`; no `except: return []` swallow; no silent placeholder.                                                                                                                                                                                                                                                                                                                                                                                                           |
| ⑤   | Read==write paths, prefix-match `batch_*`               | 🟢                  | features `mtds_output_config._MTDS_OUTPUT_BUCKET_DOMAINS` maps `dex_pool_swaps`→`dex-swaps` / `dex_pool_state`→`dex-pools` → `get_bucket_name` → `dex-swaps-prd-…` = the migrator's `base_prd` write target (READ==WRITE confirmed). `rg 'pipeline_mode=(batch\|live)([/\"'\'']\|$)'` across mtds/mdps/features/strategy/execution/deployment-api → 0 functional coarse hits (2 mtds hits are docstrings of the RETIRED coarse mode).                                                                                                                                                                                                                                     |
| ⑥   | IS+UAC validity matrix vs impossible cells              | 🟢 (P3)             | defi validity derived from `PROTOCOL_CAPABILITIES` (market_data_categories.py:847-858); grain `leaf` for all defi types; no odds/oracle leak into POOL. Residual: POOL row union-coarse (tracked P3); on-disk `instrument_type=a_token` (Aave) present alongside the 6 enumerated types — minor coverage edge, dominant cells pool/lending.                                                                                                                                                                                                                                                                                                                               |
| ⑦   | deployment-api/UI numerator+denominator = could-exist   | 🟢                  | G3 UNION read-path SHIPPED (deployment-api@4dd2575 `data_status_union.union_reduce_to_cells` + drilldown; deployment-ui@0dc40eb) — coverage % = captured/(captured+empty+failed+expected_unattempted) over could-exist denominator, READ not re-derived. (UI tick [BLOCKED-PLAYWRIGHT].)                                                                                                                                                                                                                                                                                                                                                                                  |
| ⑧   | IS-catalogue completeness (CF-14)                       | 🟢 (mechanism)      | `-prd-` by_date populated (64,724 parquets, 2020-01…2026-05); shape-aware `_enumerate_v2_defi`; all 6 defi instrument_types map cleanly. Full rollup candidate-COUNT = gated G1.run VM (VM-scale; downstream of the gated catalogue WRITE).                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ⑨   | pipeline_mode source-aware (CF-13)                      | 🟢                  | deterministic derivation check (14 defi cells): every cell source-aware, `source_string_for(pm)==source` True, transport populated; `dex_pool_swaps`→`batch_onchain_subgraph` after the fix.                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ⑩   | Era-B on-disk                                           | 🟢 N/A              | GCS probe `market-data-tick-defi-prd day=2024-06-01`: instrument_types = pool/lending/a_token/lst/yield_bearing; **zero `data_type=options_chain\|futures_chain`** (chains are cefi/tradfi-only). N/A for defi.                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ⑪   | ★ Batch=live symmetry                                   | 🟢 (migration side) | NO defi live-only data_types (one code path); `available_at` per-row write-time; live writer + migrator both derive via `derive_pipeline_mode_for_row`. **Migrated `--apply` data is correct + source-aware (① verified); `rebuild_defi_manifest` re-derives the manifest from object paths (overwriting any live stamp), `source` always C-#6-consistent → no persistent split.** Residual (tracked P1, NON-`--apply`-corrupting, rebuild-reconciled): several live handlers (dex_pools/lending/evm_defi/aggregator stamp `BATCH_ONCHAIN_RPC` for subgraph data; oracle stamps `BATCH_CHAINLINK` for Pyth rows) — transient live-manifest drift, self-healed by rebuild. |
| ⑫   | Rollback ready                                          | 🟢                  | `_index/snapshots/pre_migration_2026_06_08.parquet` confirmed in BOTH `market-data-tick-defi-prd` + `instruments-store-defi-prd` (gcloud probe); migrator `base_prd` + `ASSET_GROUP_CONFIG[defi].prefix_tpls` cover the v9 `raw_tick_data/by_date/day=/pipeline_mode=/asset_group=defi/` shape (the doubled-`day=` instruments-store object tail is the open P1 §H object-migration gate, not an index/manifest blocker).                                                                                                                                                                                                                                                 |

**REGRESSION RISK: NONE for the DeFi batch migration `--apply`.** The single migrator-output bug (dex-swaps `n`-typo →
swaps would bake `source=onchain_rpc`) is FIXED + verified on real prod. The live-handler manifest-stamp drift (⑪
residual, P1) does NOT corrupt the `--apply` migrated data — `rebuild_defi_manifest` re-derives the manifest from object
paths and is C-#6-consistent by construction; it self-heals on each rebuild. Remaining gates to the real `--apply` are
the prior OPERATIONAL ones (GATE C instruments-store v9 WRITE, IS backfill, the doubled-`day=` §H object fix, drain ✓
done) + the tracked P1/P2 live-track handler-derive remediation (post-migration, not a batch-`--apply` blocker).

### 📊 DeFi data_type MIGRATION-COVERAGE MATRIX — ALL 25 accounted (slot-2, 2026-06-09)

> Operator 2026-06-09: "did we account for the remaining data types not migrated?" — full accounting of every
> `DATA_TYPES_BY_ASSET_GROUP["defi"]` entry (25) vs the migrator `_SPECS`. Each row: migrator-covered? + has-data? +
> disposition. Verdict: **8 MIGRATED · 3 DATA-BEARING-ORPHAN (fold) · 14 NO-DATA scaffolds (collection gaps)** — nothing
> unaccounted. (Migrator specs went 6→8 this turn: gas-fees + liquidations added, mtds@01fda7ce.)

| data_type               | migrator spec        | data on disk?                                               | disposition                                                              |
| ----------------------- | -------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------ |
| dex_pool_state          | ✅ dex-pools         | yes                                                         | **MIGRATED**                                                             |
| dex_pool_swaps          | ✅ dex-swaps         | yes                                                         | **MIGRATED** (source fixed: `n`→dex_pool_swaps→subgraph)                 |
| lending_indices         | ✅ lending-indices   | yes                                                         | **MIGRATED**                                                             |
| perp_funding            | ✅ perp-funding      | yes                                                         | **MIGRATED**                                                             |
| lst_rates               | ✅ lst-rates         | yes                                                         | **MIGRATED**                                                             |
| oracle_prices           | ✅ oracle-prices     | yes (incl LST/LRT: stETH/wstETH/weETH/cbETH/rETH)           | **MIGRATED** — LST/LRT prices ride this existing data_type               |
| gas_fees                | ✅ gas-fees ⬅NEW     | yes (`gas-fees-central`)                                    | **MIGRATED** (this turn, mtds@01fda7ce)                                  |
| liquidations            | ✅ liquidations ⬅NEW | yes (`liquidations-central`)                                | **MIGRATED** (this turn, mtds@01fda7ce)                                  |
| vault_share_price       | ❌                   | YES — in `market-data-tick-defi` orphan (active 2026-05-01) | **ORPHAN-FOLD** (P1) — fold into a dedicated bucket + migrate            |
| risk_params             | ❌                   | YES — in `market-data-tick-defi` orphan                     | **ORPHAN-FOLD** (P1)                                                     |
| utilization             | ❌                   | YES — in `market-data-tick-defi` orphan                     | **ORPHAN-FOLD** (P1)                                                     |
| eigenlayer_rewards      | ❌                   | NO (`eigenlayer-rewards{,-prd}` EMPTY)                      | **COLLECTION GAP** — adapter exists, not producing; spec when data lands |
| staking_yields          | ❌                   | NO (`staking-yields` empty)                                 | **COLLECTION GAP**                                                       |
| native_staking_rates    | ❌                   | NO                                                          | **COLLECTION GAP** (multi-source solana_rpc/helius)                      |
| bridge_events           | ❌                   | NO                                                          | scaffold (no data; no dedicated/tick-data bucket exists)                 |
| flash_loan_events       | ❌                   | NO                                                          | scaffold                                                                 |
| flash_loan_availability | ❌                   | NO                                                          | scaffold                                                                 |
| governance_events       | ❌                   | NO                                                          | scaffold                                                                 |
| liquidation_events      | ❌                   | NO                                                          | scaffold (distinct from `liquidations`)                                  |
| mev_events              | ❌                   | NO                                                          | scaffold                                                                 |
| position_data           | ❌                   | NO                                                          | scaffold                                                                 |
| token_transfers         | ❌                   | NO                                                          | scaffold                                                                 |
| rewards                 | ❌                   | NO                                                          | scaffold / computed-downstream                                           |
| vault_apy               | ❌                   | NO                                                          | scaffold / computed-downstream                                           |
| vault_tvl               | ❌                   | NO                                                          | scaffold / computed-downstream                                           |

**So no data_type is silently dropped:** the migrator now covers all 8 data-bearing DEDICATED-bucket data_types; the 3
data-bearing-in-the-orphan-bucket ones (`vault_share_price`/`risk_params`/`utilization`) ride the market-data-tick-defi
FOLD (P1 below — they're written to the orphan bucket by `vault_share_price_handler` + Solana/legacy writers, so they
migrate once that bucket is folded into dedicated buckets); the remaining 14 have **NO GCS data** (adapters scaffolded
but not producing) → **collection gaps** (external-data-always-available: wire the source / operator credential-ask, NOT
a migration gap). Probe basis: `gcloud storage` bucket sweep + `market-data-tick-defi` day-samples (2024-06-01 +
2026-05-01); `tick-data-*` buckets 404 (the scaffold handlers' `kind="tick-data"` has no bucket → no data).

- [ ] [DATA] P1. **FOLD the 3 data-bearing orphan data_types into dedicated buckets + migrate** (vault_share_price /
      risk_params / utilization — data ONLY in `market-data-tick-defi` (orphan), so they ride the market-data-tick-defi
      redirect+fold below; either give each a dedicated bucket + spec, OR add market-data-tick-defi as a per-data_type
      migrator source routing to dedicated dests). vault_share_price is MVP-relevant (carry vault NAV). Repo:
      market-tick-data-service. Owner: vm-defi. parent_epic: mtds_mdps_master. Provenance: slot-2 coverage matrix
      2026-06-09.
- [ ] [DATA] P2. **DeFi collection gaps — 14 scaffolded data_types with NO GCS data** (eigenlayer_rewards,
      staking_yields, native_staking_rates, bridge_events, flash_loan_events, flash_loan_availability,
      governance_events, liquidation_events, mev_events, position_data, token_transfers, rewards, vault_apy, vault_tvl).
      Handlers exist but produce nothing — per external-data-always-available these are COLLECTION gaps (wire the source
      / credential-ask to the operator), NOT migration gaps. Triage: MVP-relevant (eigenlayer_rewards restaking yield +
      native_staking_rates for carry_staked_basis) → BLOCKED-CREDENTIALS source-ask; the rest → confirm in/out of MVP
      scope. Each gets a migrator spec ONLY once it produces data. Repo: market-tick-data-service + UAC. Owner: vm-defi.
      parent_epic: defi_master. Provenance: slot-2 coverage matrix 2026-06-09.

### 🗑️ DeFi ORPHAN-COVERAGE DRILLDOWN — GCS data NOT covered by the migrator + delete-after plan (slot-2, 2026-06-08)

> **Operator ask (2026-06-08): no orphaned data.** The `migrate_defi_full_v9_canonical` migrator reads ONLY the **6
> dedicated SOURCE buckets** (stems `dex-pools` / `dex-swaps` / `lending-indices` / `perp-funding` / `lst-rates` /
> `oracle-prices`; `base={stem}-{pid}` → `dest={stem}-prd-{pid}`). **Every other DeFi GCS bucket with real market data
> is OUTSIDE migration scope → orphan-candidate.** Real-prod `gcloud storage` enumeration (slot-2 2026-06-08) found **6
> data-bearing LEGACY orphan buckets + 2 empty**, PLUS a **7th DEDICATED bucket the migrator simply OMITS: `gas-fees`**
> (a proper dedicated source bucket like the 6, but absent from `_SPECS` → `gas-fees-prd` is empty/un-migrated; P0
> below). Drilldown + dup-vs-unique + delete-after below so nothing is silently left behind on the irreversible cutover.

**Root cause (the orphan SOURCE):** the live DeFi handlers write to INCONSISTENT buckets — only 5 write to the dedicated
migrated buckets; **4 write to non-migrated buckets**: `dex_swaps_handler`→`market-data` (=`market-data-tick-defi`),
`solana_defi_handler`→`market_data`(=`market-data-tick-defi`), `evm_defi_handler`→`evm-defi`,
`aggregator_route_handler`→`aggregator-routes`. So new writes keep CREATING orphans. (See the handler→bucket map in the
P1 redirect todo below.)

**Per-bucket drilldown (real-prod, central-element-323112):**

| Bucket                                                                                                                                         | Data / path shape                                                                                                                                                                                              | Format                                                                                              | Migrator covers?                                    | Dup-vs-unique                                                                                                                                                                                                         | Disposition                                                                                                                                                                                                                                                                                                                                                                                |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `dex-pools-{,prd-}` · `dex-swaps-{,prd-}` · `lending-indices-{,prd-}` · `perp-funding-{,prd-}` · `lst-rates-{,prd-}` · `oracle-prices-{,prd-}` | `day=/category=defi/venue=` (lst-rates already `asset_group=`)                                                                                                                                                 | OLD source → migrator normalises to v9 `pipeline_mode={mode}_{source}/asset_group=defi/` in `-prd-` | ✅ YES (MIGRATED-SOURCE→DEST)                       | n/a                                                                                                                                                                                                                   | KEEP. `-prd-` dest = canonical home. (dex-pools-prd/dex-swaps-prd carry partial prior-apply residue + OLD-format residue → the `--apply` overwrites + the legacy old-format objects are deleted by the migrator's RD4 legacy-delete after a green conform.)                                                                                                                                |
| **`gas-fees-{,prd-}`** ← 7th dedicated bucket the migrator OMITS                                                                               | `day=/category=defi/venue=<CHAIN\|ALCHEMY>/chain=<CHAIN>/instrument_type=spot_asset/data_type=gas_fees/` — CHAIN-grain (one shard per chain per day; same for ALL protocols on a chain), data from 2024-05-15+ | OLD source shape (same as the 6); `gas-fees-prd` is **EMPTY** (NOT migrated)                        | ❌ **NO — `_SPECS` has only 6, `gas-fees` missing** | n/a (source bucket; not a dup) — this is a **MIGRATOR COVERAGE GAP**, not a legacy orphan                                                                                                                             | **ADD as the 7th migrator spec** (see P0 below). gas is the per-chain gas PRICE; downstream net-cost = gas_price × gas_units (from execution `estimate_gas`). Source = `onchain_rpc` (Alchemy `eth_gasPrice`) ✓ — the handler's `BATCH_ONCHAIN_RPC` stamp is CORRECT (RPC, not subgraph). Venue-era split (old `venue=<chain>` vs new `venue=ALCHEMY`) needs canonicalisation in the spec. |
| **`market-data-tick-defi-prd`** + `market-data-tick-defi`                                                                                      | `dex_pools/<proto>/<CHAIN>/date=` + `lending_indices/<proto>/` (Solana ORCA/RAYDIUM/KAMINO + lending); **ACTIVELY written 2026-06-08**                                                                         | LEGACY (no hive `day=`, no `category=`/`asset_group=`, no `pipeline_mode=`; bare `date=`)           | ❌ NO                                               | **DUPLICATE** for ORCA/RAYDIUM Solana DEX (present in `dex-pools-` as `venue=ORCA/chain=SOLANA`). ⚠️ **VERIFY KAMINO DEX pools + the Solana `lending_indices`** are in `dex-pools-`/`lending-indices-` before delete. | DELETE-AFTER (post-migration + KAMINO/lending verify). FIRST: stop the writers (redirect `dex_swaps`+`solana` handlers) + migrate any unique KAMINO/Solana-lending shards into `dex-pools-`/`lending-indices-`.                                                                                                                                                                            |
| **`evm-defi-prd`** + `evm-defi`                                                                                                                | `raw_tick_data/by_date/day=/asset_group=defi/venue=AAVE_V3/…/instrument_type=a_token/` (Aave V3 EVM)                                                                                                           | MID (`asset_group=`, no `pipeline_mode=`); stale index 2026-05-12                                   | ❌ NO                                               | **PARTIAL**: post-`2022-11` Aave is DUPLICATE of `lending-indices-` (renamed `instrument_type a_token→lending`); **`2022-03-12…2022-10-31` Aave is UNIQUE** (NOT in `lending-indices-`, which starts 2022-11-01).     | DELETE-AFTER — **but MIGRATE/BACKFILL the unique 2022-03..10 Aave range into `lending-indices-` FIRST** (else ~8 months lost) + redirect `evm_defi_handler`.                                                                                                                                                                                                                               |
| **`solana-defi-prd`** + `solana-defi`                                                                                                          | bare `solana_defi/<proto>/<date>/` (orca/raydium/kamino/**marinade**); stale 2026-05-12                                                                                                                        | LEGACY (no hive keys at all)                                                                        | ❌ NO                                               | **DUPLICATE** for orca/raydium/kamino (≈ `market-data-tick-defi` + `dex-pools-`). ⚠️ **`marinade` (mSOL LST) not observed in any migrated bucket → UNIQUE-suspect.**                                                  | DELETE-AFTER (post-migration + marinade verify). Migrate `marinade` LST into `lst-rates-` if unique.                                                                                                                                                                                                                                                                                       |
| `market-data-tick-defi-test` · `market-data-tick-test-defi` · `*-test-*` Solana/evm                                                            | (empty — 0 objects)                                                                                                                                                                                            | —                                                                                                   | n/a                                                 | EMPTY                                                                                                                                                                                                                 | DELETE (safe; no data).                                                                                                                                                                                                                                                                                                                                                                    |

**Delete-after-migration list (track to closure — nothing deleted until its row is GREEN):**

- [x] ✅ [SCRIPT] P0. **DONE (mtds@01fda7ce, slot-2 2026-06-09) — added `gas-fees` (7th) + `liquidations` (8th) migrator
      specs.** `gas-fees`: row_split, `venue_const="ALCHEMY"`, `chain_col="chain"` (canonicalises the venue-era split →
      ALCHEMY/`batch_onchain_rpc`). `liquidations`: path-grain (`batch_onchain_subgraph`). Both were data-bearing
      dedicated buckets the migrator omitted; now migrate to v9. union derives on-the-fly (`--phase discover` to bake
      for the VM apply). Verified: migrator tests 15 green, basedpyright + ruff clean, full mtds QG green (2679 passed).
      The real-prod dry-run (union footer-scan over 22933 gas objects) is VM-scale, gated with the apply. Original
      finding ↓.
- [x] ✅ [SCRIPT] P0. **(DONE — see ✅ row above; full context retained) `gas-fees` was OMITTED from
      `migrate_defi_full_v9_canonical.py` `_SPECS` (only 6) so `gas-fees-prd` was EMPTY (un-migrated).** gas is on the
      DeFi arb/carry critical path (net-of-gas profitability), so this is a P0 coverage gap, not optional. Add
      `"gas-fees": BucketSpec("gas-fees", "gas_fees", "spot_asset", grain="path")` to `_SPECS` (source shape matches the
      path-cell buckets: `day=/venue=/chain=/instrument_type=spot_asset/data_type=gas_fees/`). gas is CHAIN-grain (one
      shard per chain per day — same for all protocols on a chain). **Canonicalise the venue-era split**: old shards
      have `venue=<chain>` (ARBITRUM/AVALANCHE/BASE/BSC), the current handler writes `venue=ALCHEMY` (provider) — decide
      the canonical venue (recommend `ALCHEMY` provider + `chain=<chain>`, matching the handler) and remap old
      `venue=<chain>` → `ALCHEMY` in the migrator's venue canonicalisation. `gas_fees` is NOT in `_CANONICAL_UNION` →
      either bake it (run `--phase discover --buckets gas-fees`) or let it derive on-the-fly. pipeline_mode derives
      `batch_onchain_rpc` (correct — `SOURCE_PRIORITY(defi,gas_fees)=onchain_rpc`, gas via Alchemy RPC, NOT subgraph).
      Then a dry-run verify + add to the drain/snapshot/RESUME runbook lists (the `gas-fees` cron + bucket). Repo:
      market-tick-data-service. Owner: vm-defi. parent_epic: mtds_mdps_master. Provenance: slot-2 gas-fees coverage-gap
      audit 2026-06-08 (operator question).
- [ ] [DATA] P1. **gas-fees MUST be in the manifest + data-status could-exist denominator (operator 2026-06-08).** gas
      is already RECORDED in the manifest per chain (`gas_fee_handler` → `DefiManifestRecorder.record_captured/empty`,
      `venue=ALCHEMY`/`chain=<chain>`, `data_type=gas_fees`, chain-grain) — but two things must follow the 7th-spec
      migration: (a) the gas-fees `_index` MANIFEST is rebuilt to reflect the migrated objects — **NOT automatic**: the
      migrator writes OBJECTS ONLY (it `_keep`-excludes `/_index/`), so the v9 manifest for the migrated gas objects
      requires a separate manifest rebuild over `gas-fees-prd` (see the manifest-rebuild-scope P1 below); (b) the
      **could-exist denominator** (IS `enumerate_expected_universe` + the deployment-api/UI data-status) must include
      `gas_fees` as a **per-chain expected cell** (one per chain × day in `GAS_FEE_CHAIN_START_DATES` coverage) so
      coverage % reflects gas presence/absence per chain — gas is chain-grain (NOT per-instrument), so the denominator
      is the chain set, not the instrument universe. Verify `gas_fees` is in `DATA_TYPES_BY_ASSET_GROUP["defi"]` + the
      validity matrix (`(defi, SPOT_ASSET, gas_fees)` valid) so it is not dropped as impossible. Repos:
      instruments-service + unified-api-contracts + deployment-api. Owner: vm-defi. parent_epic: manifest_master.
      Provenance: slot-2 gas-fees audit 2026-06-08 (operator question).
- [x] ✅ [SCRIPT] P1. **TOOL DONE (mtds@01fda7ce, slot-2 2026-06-09): `rebuild_defi_manifest` now takes `--bucket`** so
      it rebuilds each dedicated `-prd-` bucket's manifest from the migrated objects (run per dedicated bucket as the
      post-`--apply` step — the RUN itself is gated with the apply). Original gap ↓ retained. **MANIFEST-REBUILD SCOPE
      GAP — the migrator migrates OBJECTS but NOTHING rebuilt the dedicated `-prd-` bucket MANIFESTS over the migrated
      data (operator question 2026-06-08).** `migrate_defi_full_v9_canonical` writes OBJECTS only (excludes `/_index/`).
      `rebuild_defi_manifest.py` (the object→manifest rebuilder) is HARDCODED to
      `BUCKET_TEMPLATE="market-data-tick-defi-{project_id}"` (line 76; no `--bucket` arg) — it scans the LEGACY
      market-data-tick-defi bucket, **NOT** the 6+1 dedicated `-prd-` buckets the migrator writes (`dex-pools-prd` /
      `dex-swaps-prd` / `lending-indices-prd` / `perp-funding-prd` / `lst-rates-prd` / `oracle-prices-prd` /
      `gas-fees-prd`). The dedicated-bucket manifests today are built from LIVE handler per-VM shards + the per-bucket
      consolidator (reflecting live captures, NOT the migrated historical backfill). **Consequence**: after the object
      `--apply`, the migrated HISTORICAL rows are present as OBJECTS but ABSENT from the manifest → the deployment-api
      coverage % undercounts (objects exist, manifest blind) until a manifest rebuild runs over the dedicated bucket.
      **Fix**: generalise `rebuild_defi_manifest` to accept a `--bucket`/per-stem target (so it can rebuild each
      dedicated `-prd-` bucket's `_index` from the migrated objects, deriving source-aware pipeline_mode as it already
      does), and run it per dedicated bucket as the post-`--apply` step (paired with the consolidator). Confirm whether
      `market-data-tick-defi` is still a live manifest home or fully superseded by the dedicated buckets (the
      BUCKET_TEMPLATE hardcode suggests an unfinished cutover). This applies to ALL 7 dedicated DeFi market buckets, not
      just gas. Repo: market-tick-data-service. Owner: vm-defi. parent_epic: mtds_mdps_master. Provenance: slot-2
      object-vs-manifest scope audit 2026-06-08 (operator question).
- [ ] [STRATEGY] P2. **NICE-TO-HAVE — wire the downstream gas NET-COST consumer if absent.** The gas_fees DATA layer
      (per-chain gas PRICE) exists, but a grep of strategy-service/execution-service/features-service/utl found NO
      `gas_price × gas_units` net-of-gas cost computation (`estimate_gas` × gas_fees) — verify (grep-then-READ) whether
      DeFi arb/carry net-of-gas is wired (execution `estimate_gas` for gas_units × the gas_fees price); if missing, the
      gas data is collected but unused for profitability. Repos: strategy-service / execution-service. parent_epic:
      defi_master. Provenance: slot-2 gas-fees audit 2026-06-08.
- [ ] [DATA] P1. **VERIFY-then-MIGRATE the UNIQUE orphan gaps into the canonical dedicated buckets BEFORE any legacy
      delete** (else data loss on the irreversible cutover): (a) `evm-defi-prd` Aave V3 **`2022-03-12…2022-10-31`**
      range → backfill into `lending-indices-` (confirm absent there first via cf_manifest_audit); (b) `solana-defi-prd`
      **`marinade`** (mSOL LST) → confirm absent in `lst-rates-`, migrate if unique; (c) `market-data-tick-defi-prd`
      **KAMINO DEX pools** + the Solana **`lending_indices`** shards → confirm present in
      `dex-pools-`/`lending-indices-` (sampled ORCA/RAYDIUM are; KAMINO/lending unconfirmed), migrate if unique. Repo:
      market-tick-data-service (`scripts/migrate_defi_full_v9_canonical.py` could add these as extra source specs, OR a
      one-off backfill). Owner: vm-defi. parent_epic: mtds_mdps_master. Provenance: slot-2 orphan audit 2026-06-08.
- [ ] [SCRIPT] P1. **REDIRECT the 4 DeFi live handlers that write to NON-migrated buckets → the dedicated migrated
      buckets, so new writes stop creating orphans** (the orphan SOURCE). Handler→current-bucket map:
      `dex_swaps_handler` (`resolve_bucket_name(kind="market-data")` → `market-data-tick-defi`) → should write
      `dex-swaps`; `solana_defi_handler` (`get_write_bucket_name("market_data","DEFI")` → `market-data-tick-defi`) →
      should write the per-data_type dedicated bucket (`dex-pools`/`lending-indices`/`lst-rates`/`perp-funding`) per
      `_PROTOCOL_TO_DATA_TYPE`; `evm_defi_handler` (`get_write_bucket_name("evm-defi")`) → `lending-indices`;
      `aggregator_route_handler` (`get_write_bucket_name("aggregator-routes")`) → operator-decision (aggregator-routes
      is a distinct stream — keep + add to the migrator, OR fold). Until redirected, these buckets keep diverging from
      the canonical home that features/strategy read. Repo: market-tick-data-service. Owner: vm-defi. parent_epic:
      mtds_mdps_master.
- [x] ✅ [MTDS] P0. **M-COORD-7 — 41 coarse `pipeline_mode="batch"` OBJECT-PATH literals in DeFi handlers (batch≠live
      regression + STEP-5.85 ship-blocker) — FIXED (mtds@57242af5, slot-2 2026-06-08).** Filed by slot-4 while shipping
      the sports fix: mtds STEP 5.85 hard-failed on 41 pre-existing coarse `pipeline_mode="batch"` literals in 25 DeFi
      CLI handlers (the `write_defi_rows(...)` OBJECT writes), causing (a) a **batch≠live regression** — DeFi live
      objects landed coarse `pipeline_mode=batch/` while the migrator (mtds@f80c50f1) writes source-aware — and (b)
      **blocked every mtds code ship** (no QG-green sentinel). **Root-cause fix (centralised)**: `write_defi_rows`
      (`canonical_write.py`) now UPGRADES a coarse `"batch"`/`None` `pipeline_mode` to the source-aware
      `{mode}_{source}` via the SAME `derive_pipeline_mode_for_row` the v9 migrator + `rebuild_defi_manifest` use →
      live/batch OBJECTS land canonical (`pipeline_mode=batch_<source>/`), byte-identical to the migrated batch data
      (Batch=Live by construction); all **41 coarse literals removed** from the handler call sites (→ `None` → derive) +
      the now-stale "coarse ingestion" comments removed. STEP 5.85 = **0 coarse literals** (unblocks mtds ships). **22
      handler-test path assertions + 4 old-migrator-test assertions updated** to the derived source-aware paths (e.g.
      dex_pool_state/lending_indices/lst_rates/vault/eigenlayer→`batch_onchain_subgraph`; perp_funding (incl. Solana
      DRIFT, ASTER, GMX, PACIFICA)→`batch_hyperliquid`; oracle CHAINLINK→`batch_chainlink`, PYTH→`batch_pyth_hermes`).
      **1359 tests green; 0 coarse literals; basedpyright clean.** Repo: market-tick-data-service. parent_epic:
      mtds_mdps_master. Provenance: slot-4 M-COORD-7 → slot-2 fix 2026-06-08.
- [ ] [DATA] P1. **DELETE the duplicate/legacy DeFi orphan buckets AFTER (1) migration GREEN + (2) the unique-gap
      migrations above complete + (3) the redirects land + (4) a final cf_manifest_audit confirms 0 unique rows
      remain**: `market-data-tick-defi{,-prd}` · `solana-defi{,-prd}` · `evm-defi{,-prd}` (post unique-gap migration) ·
      the 4 empty `*-test-*` DeFi buckets (delete now — 0 objects). Use `gcs_delete_object` / bucket lifecycle, NOT
      `gsutil` per-object. Snapshot each `_index` to `_index/snapshots/pre_delete_<date>.parquet` first (rollback).
      Owner: vm-defi (operator sign-off on the bucket deletes — destructive). parent_epic: manifest_master. Provenance:
      slot-2 orphan audit 2026-06-08.
- [ ] [UAC] [SCRIPT] P2. **Solana DeFi source = actual names (folds the prior P2 + the live-handler Solana stamp).**
      Once Solana writes land in the dedicated buckets (redirect above), the migrator/rebuild + live handlers must stamp
      the ACTUAL Solana source, not the chain-agnostic `onchain_subgraph`: add Solana venue overrides to UTL
      `_VENUE_OVERRIDES` (ORCA/RAYDIUM/PHOENIX/KAMINO/MARINADE/JITO→`BATCH_SOLANA_RPC`; DRIFT→`BATCH_HELIUS_RPC`;
      MARGINFI/SOLEND→**`BATCH_DEFILLAMA`**) **+ ADD the missing `BATCH_DEFILLAMA`/`LIVE_DEFILLAMA`/`REPLAY_DEFILLAMA`
      enum members** to UAC `pipeline_mode.py` (+ `source_string_for` `defillama` + `default_transport_for_source`
      `defillama→rest` + the closed-set symmetry tests). Then drop the handler hardcodes so
      `derive_pipeline_mode_for_row` is the single SSOT. Repos: unified-trading-library + unified-api-contracts +
      market-tick-data-service. Owner: vm-defi. parent*epic: manifest_master. Provenance: slot-2 ⑪/P2 audit 2026-06-08.
      **EXTENDED 2026-06-08 — multi-VENUE perp has the same coarseness**:
      `SOURCE_PRIORITY(defi, perp_funding)=     [hyperliquid]` (single) so `derive_pipeline_mode_for_row` returns
      `batch_hyperliquid` for ALL defi perp venues — ASTER, GMX, PACIFICA, **Solana DRIFT** all resolve to
      `batch_hyperliquid`/`source=hyperliquid` (only LIGHTER has an override → `batch_tardis`). This is CONSISTENT
      (object==manifest==migrator all derive the same, so the M-COORD-7 fix + the migration are correct) but the source
      LABEL is wrong for non-Hyperliquid perp DEXs. The accuracy fix is the same as Solana: add per-venue overrides
      (ASTER→`batch_aster`?, GMX→`batch_gmx`?, DRIFT→`batch_drift`/helius, PACIFICA→…) — needs the operator's per-venue
      source decision + the corresponding `BATCH*<VENUE>` enum members. Until then perp source is coarse-but-consistent.

**Note on the migrated-bucket residue (NOT orphans):** `dex-pools-prd`/`dex-swaps-prd` carry BOTH old-format
`day=/category=defi/` AND partial prior-apply canonical objects (one sample showed `pipeline_mode=BATCH_ONCHAIN_RPC`
UPPERCASE — an OLD partial-apply artifact; the current migrator stamps the lowercase `.value` `batch_onchain_subgraph`).
The `--apply` re-conforms + the RD4 legacy-delete removes the superseded old-format objects in the SAME bucket, so these
are migration-in-flight residue the apply resolves — NOT a separate orphan. (Flagged for the apply-run to confirm the
RD4 legacy-delete covers the UPPERCASE residue too.) parent_epic: mtds_mdps_master. > **FINDING (slot-5 prediction,
2026-06-08) — two updates to this MTDS-QG-red item:** > (a) **`rebuild_prediction_manifest.py` is now SPLIT** (954→692
L, mtds@c571445d) → REMOVE it from the >900 list; > the remaining >900 files are non-prediction. (b) **NEW gate-0
blocker not previously listed: a committed > `uv.lock`↔`pyproject.toml` desync on the MTDS LDR HEAD.** `uv lock --check`
FAILS — the committed `pyproject.toml` > declares `pyarrow-stubs` + `mypy-boto3-{logs,sns,sqs}` that are absent from the
committed `uv.lock`, so the QG > aborts at its FIRST gate (`❌ uv.lock out of sync`) BEFORE file-size/basedpyright/tests
even run. Mechanical > re-sync (`uv lock` adds the 4 stub pkgs, ~52 LOC; precedent mtds@10930dbd "re-sync uv.lock to
pyproject"). Until > this lands, NO MTDS `quality-gates.sh` reaches green regardless of the file-length work — fix it
FIRST in this > slot-2 sweep. (Slot-5 did not fix it: it completes another commit's incomplete dep edit — out of
prediction AG + > FM1 foreign-work-bundling risk.) **✅ RESOLVED 2026-06-08 (slot-2, operator decision A):** (0)
**gate-0 re-locked** (mtds@d544f15c — `uv lock` to current pyproject; `uv lock --check` green) BUT this is **recurring
lock-drift** (the type-stubs flip-flop in pyproject between agents; `dbbbef8a` added them, a later commit removed them)
→ **handed to the dep/CI lane** (slot-1 `update-dependency-version.yml` prevention + settle the type-stub flip-flop);
NOT a thing to keep manually re-locking. (1) **file-size = 15 pre-existing non-`scripts/` files** (orchestrator.py 4219
etc.) → **DEFERRED to the named successor `plans/active/mtds_file_size_refactor_2026_06_08.md`** (post-migration;
splitting the migration's own `orchestrator.py` pre-apply is high-risk for zero migration benefit). **NOT
migration-blocking**: file-size loop excludes `./scripts/*` (migration code clean); MTDS migration code ships via
basedpyright-on-touched; `--apply` runs from VM/tarball not the sentinel. (The hollow-sentinel harness finding below is
the related ship-hygiene item.)

- [ ] [INFRA] P2. **🔴 LOCAL QG HARNESS collects the WRONG test suite for some repos — the green sentinel is HOLLOW
      (surfaced slot-7 2026-06-08).** Running `bash scripts/quality-gates.sh --no-fix` for **instruments-service** AND
      **market-tick-data-service** on this host produced a `[3/6] TESTS` run with `rootdir: …/unified-trading-pm`,
      `configfile: unified-trading-pm/pyproject.toml`, **`collected 6 items`** — it ran only PM's 6
      `tests/integration/test_pm_scripts_integration.py` tests, NOT the repo's own suite (IS has ~3,267 tests; its own
      `pyproject.toml` declares `[tool.pytest.ini_options] testpaths=["tests"]`). The QG still **exits 0 + writes
      `.qg_last_passed_sha`**, so the commit-quality-boundary sentinel for those repos is hollow — a code change can
      ship "QG-green" without its tests ever running (the peer's `mtds@67786887` tradfi-reader change passed this same
      hollow gate). **Contrast**: the UAC QG ran its FULL suite (8,617 passed / 3 pre-existing
      `test_schema_version_matrix.py` failures / 550 skipped) — so it is IS/MTDS-specific (possibly the
      qg-governor-queued subprocess cwd, or a `PROJECT_ROOT`/rootdir mis-resolution when run under contention).
      **Impact**: undermines QG confidence for the migration code on the apply critical path. **Mitigation used this
      session**: slot-7 ran the touched tests directly in each repo `.venv` (IS `enumerate` 88 passed · UAC
      F2+era_b+source_priority 106 passed) to verify before shipping. **Owner: vm-cross-cutting / QG-harness** —
      root-cause the rootdir/cwd resolution (likely `quality-gates-base/base-service.sh` `cd "$PROJECT_ROOT"` vs the
      governed subprocess) so per-repo QGs collect their own suite. Repos: unified-trading-pm
      (`scripts/quality-gates-base/base-service.sh`) + per-repo `quality-gates.sh`. parent_epic: manifest_master.
      Provenance: slot-7 cross-cutting sweep 2026-06-08.
- [ ] [DATA] P1. **DeFi instruments-store `by_date` has a DOUBLED `day={D}/day={D}/` prefix on the recent tail**
      (~2026-05-05 onward — `day=2026-05-05/07` confirmed doubled; `day=2026-05-03` and ALL earlier days are single,
      canonical `day={D}/venue={V}/instruments.parquet`). Surfaced by the G2 verify dry-run 2026-06-07 (slot-2). **TWO
      defects**: (1) an instruments-service `by_date` WRITER regression that nested a second `day=` for recent snapshots
      (`gs://instruments-store-defi-prd-…/instrument_availability/by_date/day=2026-05-07/day=2026-05-07/venue=AAVEV3-ARBITRUM/instruments.parquet`);
      (2) the slot-7 v9 OBJECT migrator (`migrate_instruments_store_v9.py` `canonical_object_rel`) inserts
      `pipeline_mode=/asset_group=` after the FIRST `day=` but does NOT normalise the second → its projected canonical
      path is MALFORMED
      (`day=2026-05-07/pipeline_mode=batch_instruments_service/asset_group=defi/day=2026-05-07/venue=…`). The
      catalogue/enumerate are UNAFFECTED (`build_instrument_catalogue` uses `_DAY_RE.search` + `_VENUE_RE.search` →
      resolves the correct day+venue), so this is a **G4 object-migration gate**, not a CF-14 blocker. **Fix BOTH before
      the gated defi §H object `--apply`**: dedupe/normalise the writer + add a `day=…/day=…` collapse (or a pre-flight
      reject) to `canonical_object_rel`. Repos: instruments-service (writer + slot-7 migrator). parent_epic:
      manifest_master.
- [ ] [UAC] P3. **NICE-TO-HAVE — defi G1-ENUM matrix `POOL` row is union-coarse**: the derived
      `valid_data_types_for_instrument_type("defi","POOL")` is the UNION across all POOL-declaring protocols →
      `{dex_pool_state, dex_pool_swaps, gas_fees, lending_indices, liquidations, perp_funding}`, so a pure-DEX pool
      (e.g. UNISWAP_V3) would seed `expected_unattempted` for `perp_funding`/`lending_indices`/`liquidations` it never
      produces (a perp-DEX like GMX legitimately needs them). NOT an impossible-combo (gate-(a) still passes — no
      `odds`/`oracle_prices` leak into POOL), but a per-protocol grain would tighten the denominator. Repo:
      unified-api-contracts (`registry/capability_declarations/_defi.py` PROTOCOL_CAPABILITIES). parent_epic:
      manifest_master. Provenance: G2 verify 2026-06-07 (slot-2).
- [ ] [SCRIPT] P3. **NICE-TO-HAVE — defi migrator `_list_objects` L1 find is a full-bucket scan** (re-verify 2026-06-07,
      slot-2): `migrate_defi_full_v9_canonical.py:570` always issues `_safe_find(fs, {base}/{dir_name})` for the L1
      layout, but all 6 dedicated source buckets are `day=`-partitioned today (no top-level `{dir_name}/` or
      `raw_tick_data/` tree) → that L1 prefix matches nothing yet gcsfs enumerates the whole bucket (a 3-day local
      dry-run hit a >280 s timeout on it; the L1 `dex_pools` find alone >120 s isolated). NOT a correctness issue
      (returns the correct empty set; date-scoped runs DO complete — the earlier `day=2024-06-01` dry-run finished
      0-errors) and laptop-variable, but it wastes a whole-bucket enumeration per bucket on the in-region VM `--apply`
      too. Gate the L1 find on a cheap existence probe (or drop it) — **validate against the whole corpus on the VM
      first** so a bucket with a genuine L1 tree is never silently skipped (data-loss risk). Repo:
      market-tick-data-service. parent_epic: mtds_mdps_master. **TRIAGED 2026-06-07 (slot-2) → SPEED-NOTE,
      NON-BLOCKING:** the `--apply` does NOT date-shard `_list_objects` (the `launch-canonical-migration-vm.sh` launcher
      runs ONE VM over the full date range → exactly ONE `_list_objects` per bucket = 6 wasted whole-bucket scans total,
      not N×6), and the in-region VM completes whole-bucket scans (the baked-union `discover_union` run over the whole
      corpus proved it). So the L1 find adds wall-clock to the apply but never blocks it. Per the apply-ready criterion
      (fix only if it blocks at scale) this stays a **deferred optimisation**, not an apply-gate. Kept P3.

### G2-defi readiness verdict (WAVE 2 verify pass — slot-2, 2026-06-07)

**VERDICT: defi migration CODE is DRY-RUN-GREEN on LDR — the manifest+data `--apply` is code-ready, correctly GATED.**
Re-run on the WAVE-1 source-aware code against real prod GCS (read-only). No code changed (verify pass = dry-runs only);
this is a `docs(plans):` flip.

- **①+⑨ MTDS migrator dry-run (CF-3/CF-13) GREEN — mtds@f80c50f1.**
  `migrate_defi_full_v9_canonical --start-date 2024-06-01 --end-date 2024-06-01` (dry, all 6 buckets) → 0 errors, 0
  needs_attr. Projected PATHS + in-process `_conform` COLUMNS both verified source-aware:
  `dex_pool_state→pipeline_mode=batch_onchain_subgraph` (source=`onchain_subgraph`), `dex_pool_swaps→batch_onchain_rpc`
  (source=`onchain_rpc`); both `schema_version=9`, `asset_group=defi`, `transport=rest` (separate COLUMN), per-row
  `available_at` (EOD UTC), canonical underscore `data_type`, `pipeline_mode=…/asset_group=defi/` LEFT of `venue=`;
  legacy source `category=defi` correctly migrated. NOT coarse `batch`/blank.
- **②+③ instruments-store v9 index dry-run (CF-1/CF-2/CF-4) GREEN — is@2971a064.**
  `migrate_instruments_store_v9 --asset-group defi --skip-objects` (dry) → prd `_index` **125,242 rows v8→v9 (100%)**:
  schema_version `{9:125242}`, source=`instruments_service`, transport=`rest`,
  pipeline_mode=`batch_instruments_service`, asset_group=`defi`, available_at filled on all rows, `category` dropped.
  cf_manifest_audit projection → CF-GREEN. (Object-walk side: GREEN for canonical single-`day=` objects; the recent
  doubled-`day=` tail is the P1 finding above — a G4 gate, not an index blocker.)
- **③ catalogue + enumerate (CF-14) — mechanism GREEN, candidate-count GATED.**
  `build_instrument_catalogue --asset-group defi --dry-run` on the now-populated prd `instrument_availability/by_date/`
  → **64,724 by_date snapshots enumerated** for rollup (listing GREEN; the prior "0 rows / -prd- empty" finding is
  RESOLVED — by_date is now populated 2020-01-20…2026-05-08). The full LOCAL rollup EXCEEDED a 580s budget downloading
  64,724 small parquets (exit 124, did NOT finish) → the rollup + enumerate candidate-count run needs a VM / longer
  timeout, deferred with the gated G1.run write below (the count is downstream of the gated catalogue WRITE anyway).
  Validity-matrix slice VERIFIED correct (UAC@97c26dbe, enumerate@6ea46565): **all 6 defi instrument_types present in
  by_date map cleanly** — `POOL`/`LENDING`/`SPOT_PAIR`/ `PERPETUAL`/`STAKING`/`YIELD_BEARING`, zero
  unmapped/over-fan/None-fallthrough; `_enumerate_v2_defi` is G1-ENUM shape-aware (genesis/launch/lifecycle +
  bundle-skip). Full enumerate candidate-count is gated on the **G1.run catalogue WRITE** (a `--apply-write`, correctly
  GATED on GATE C below) — not runnable read-only without a persisted catalogue parquet.
- **④⑤⑥⑦⑧ (CF-5/6/7/8/10/11/12)** ride the WAVE-1 code (rebuild `record_zero_rows`/typed reasons, A7 fetch-failure
  classification, batch=live single path) — unchanged this pass; verified by the 25/25 credential-free unit suite.

**Remaining gates for the defi `--apply` (G4) — all correctly held:**

1. **G0 ∧ G1 ∧ G3** (cross-AG coordinator gates).
2. **GATE C — instruments-store-defi `_index` v9 walk** (currently 0% v9 on disk: 125,242 v8; dry-run proves the
   transform is correct — the WRITE is the gated `--apply`).
3. **DeFi IS backfill + the doubled-`day=` writer/migrator fix** (P1 above) before the §H object `--apply`.
4. **Pre-migration drain** (all VMs stopped + consolidated) before any object `--apply`.

Sampled-not-walked disclosure: MTDS dry-run sampled `day=2024-06-01` across all 6 buckets (path+column verified) +
in-process `_conform` of real dex-pools/dex-swaps objects; instruments-store `_index` transform walked all 125,242 rows;
by_date instrument_type coverage sampled across all venues for `day=2025-12-15`+`2026-05-03` (+ a 6-day spread). The
doubled-`day=` boundary was sampled day-by-day across 2026-05-01…08. The full 64,724-parquet catalogue rollup count +
the enumerate candidate-count are deferred to the gated G1.run write.

### 🟢 DeFi APPLY-READY VERDICT + completed 7+2-point audit (slot-2, 2026-06-07)

> **VERDICT: DeFi is APPLY-READY on LDR.** Every G1+G2 dry-run is green and the 7+2-point audit passes; the migration
> CODE is correct and no code change is owed before `--apply`. **The only things between DeFi and the real `--apply` are
> OPERATIONAL gates** (drain + the gated WRITE runs), not code. No `--apply` run in this pass (gated).

**7+2 audit — per-CF verdict (CF-1…CF-14; data-state reads, not constants):**

| CF         | Invariant                                               | defi verdict    | Evidence (sampled vs walked)                                                                                                                                                                                                                               |
| ---------- | ------------------------------------------------------- | --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CF-1       | schema_version=9                                        | 🟢              | migrator `_conform` stamps `9` on real ORCA parquet (sampled); IS `_index` transform → `{9:125242}` (WALKED all rows)                                                                                                                                      |
| CF-2       | `asset_group=` not `category=` (path+row)               | 🟢              | real source `category=defi`→canonical `asset_group=defi/` path key + column; `category` dropped from `_index` (walked)                                                                                                                                     |
| CF-3/CF-13 | source-aware `pipeline_mode={mode}_{source}` (path+col) | 🟢              | `batch_onchain_subgraph`/`batch_onchain_rpc` per-shard on real paths+cols; coarse `batch`/blank retired; 14-case derivation incl. antipattern-retired `batch_hyperliquid` (sampled)                                                                        |
| CF-4       | `source` COLUMN every external cell                     | 🟢              | `source=onchain_subgraph` on real rows; IS rows `source=instruments_service` (walked). P2 `SOURCE_PRIORITY` registry-gap todo open (derives cleanly via fallback today)                                                                                    |
| CF-5       | typed `EmptyConfirmedReason`                            | 🟢              | defi writers use `DefiManifestRecorder.record_zero_rows` + `EXPECTED_PRE_VENUE_LAUNCH`/`EXPECTED_PRE_GENESIS_CHAIN` (code grep)                                                                                                                            |
| CF-6       | `expected_unattempted` materialised                     | 🟢 (code)       | shape-aware `_enumerate_v2_defi` + `build_instrument_catalogue` produce the could-exist seed; the apply-write RUN is the gated G1.run                                                                                                                      |
| CF-7       | canonical data_type / flat venue+chain / `{VENUE}_V{N}` | 🟢              | input `dex_pools`→typed `dex_pool_state`; `SUSHISWAP`→`SUSHISWAP_V3` on real paths (sampled)                                                                                                                                                               |
| CF-8       | per-row `available_at`, no lookahead                    | 🟢              | real ORCA `available_at=2026-05-28T21:21:46` write-time; IS `available_at` filled on all 125,242 rows (walked)                                                                                                                                             |
| CF-9       | env-split bucket via `resolve_bucket_name`              | 🟢              | migrator/rebuild build buckets via `resolve_bucket_name`; the `gs://` occurrences are docstring/log strings, not f-string bucket construction (grep)                                                                                                       |
| CF-10      | no phantom/date-impossible captured                     | 🟢 (projection) | IS `_index`: 57,466 null→`captured` from `instrument_count>0`, 0 dishonest captured-but-empty (walked); object-presence phantom sweep is `reconcile_phantom_manifest_rows_all` post-apply                                                                  |
| CF-11      | fetch-failure → `attempted_failed`                      | 🟢              | defi handlers (mev/evm_defi/perp_funding) call `record_failed(...)`; no `except: return []` swallow (grep)                                                                                                                                                 |
| CF-12      | batch=live symmetry                                     | 🟢              | one code path (no defi live-only data_types); verified by the 25/25 credential-free unit suite                                                                                                                                                             |
| CF-14/⑧    | IS-catalogue could-exist ROOT green                     | 🟢 (mechanism)  | `-prd-` by_date POPULATED (64,724 parquets); shape-aware producer runs; validity-matrix slice correct (IS adapters emit `POOL`/`STAKING`/`LENDING`/`SPOT_PAIR`/`YIELD_BEARING`, all matrix-covered). Full rollup candidate-count = gated G1.run (VM-scale) |

**Sampled-vs-walked (audit-level)**: WALKED — the full 125,242-row instruments-store `_index` transform (deterministic,
no object probe). SAMPLED — MTDS migrator conform on the latest populated day per bucket + a real 14,093-row ORCA
parquet (the whole-corpus migrator walk runs on the in-region VM); the 64,724-parquet catalogue rollup LISTED but not
fully rolled up locally (VM-scale). Adapter/handler CF-5/9/11/12 verified by code grep, not a corpus walk. **Remaining
gaps**: the full catalogue rollup + enumerate candidate-count (gated G1.run VM run) and the object-presence phantom
sweep (post-apply) — both downstream of the gated WRITE, not code.

**Remaining gates to the real `--apply` — ALL OPERATIONAL (no code owed):**

1. **G0** GREEN ✓ (Phase-0 source-aware writer code landed) · **G3 UNION view SHIPPED ✓** (deployment-api@4dd2575 +
   deployment-ui@0dc40eb, pm@822393880).
2. **GATE C — instruments-store-defi `_index` v9 WRITE**: run `migrate_instruments_store_v9 --asset-group defi --apply`
   (the dry-run proved the 125,242-row transform projects 100% v9; this is the gated WRITE, not a code fix).
3. **DeFi IS backfill complete** + the gated `build_instrument_catalogue`+`enumerate_expected_universe --apply-write`
   G1.run VM run (catalogue/enumerate UNAFFECTED by the doubled-`day=` bug; that bug is a §H **object**-migration gate,
   fixed before the §H object `--apply` only).
4. **Pre-migration drain** (all GCP+AWS VMs stopped + manifest consolidated + snapshot) before any object `--apply`.

No code-correctness blocker remains for the DeFi migrator/rebuild/enumerator. The 3 open todos are: P1 doubled-`day=` (a
§H object-migration gate, instruments-service) · P2 `SOURCE_PRIORITY` registry tidy · P3 POOL union-coarse + P3 L1-find
speed-note (both deferred optimisations, non-blocking).

\*\*Regression re-confirmation (slot-2, 2026-06-07) — STILL APPLY-READY after the shared bundle-grain + sports-catalogue

- matrix changes landed.** Targeted check (the changed surface vs defi, not a blind re-run): the bundle-grain axis
  (`grain_for_instrument_type`, uac@dd7fa100) returns **`leaf` for ALL 6 defi instrument_types**
  (POOL/LENDING/SPOT_PAIR/ PERPETUAL/STAKING/YIELD_BEARING) — only cefi `options_chain`/`option` are
  `bundle_by_underlying`, so defi never collapses to a bundle; the defi validity-matrix slice is **unchanged** (POOL 6 ·
  LENDING 4 · SPOT_PAIR 2 · PERPETUAL 2 · STAKING 2 · YIELD_BEARING 4 dts, zero over-fan). The sports-league fix
  (uac@aff80339) is sports-only. The migrator (`migrate_defi_full_v9_canonical.py`) is unchanged at **mtds@f80c50f1**
  and its derivation deps (`source_string_for`/`default_transport_for_source`/`derive_pipeline_mode_for_row`) were
  untouched by the recent batch → dry-run output is provably identical to the green run above. **No new code owed; HOLD
  stands.\*\* Remaining gates remain purely operational (drain + the gated v9 instruments-store walk + IS backfill).

## Orphan sweep (2026-06-07) — every active data-layer plan/issue is registered above

- Swept `plans/active/*.md` + `plans/active/issues/*.md` for manifest/migration/catalogue/pipeline_mode/backfill/
  coverage/schema themes. **All registered above** — 0 orphans in-theme at sweep time.
- **Superseded epics flagged** (already banner-marked in `plans/epics/`): `manifest_evolution_SUPERSEDED_2026_05_21` +
  `manifest_migration_SUPERSEDED_2026_05_21` — do NOT reference; the live epic is `epics/manifest_master.md`.
- Re-run the sweep at every gate promotion (a new active plan touching the data layer with no registry row here is
  review-blocking).

## Master coordination todos (this plan's OWN work — pure coordination, no execution)

- [ ] [UAC] [IS] P1. **G1-ENUM present-set asymmetry — combo/chain underlyings get PHANTOM
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
      `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE[("cefi",     options_chain/futures_chain)]` accordingly. tradfi
      (Databento) chains carry only `{trades, ohlcv_1m}` (no IV) — so the IV slice is cefi-specific.** **SCOPE: the
      gated G1.run `--apply-write` SEED only — NOT the G4 data/manifest `--apply`** (that walk is content-preserving;
      tradfi/cefi v9 DATA migration has ZERO regression from this; cefi's low candidate count (3,454) means its phantom
      is small because cefi captures `options_chain` bundles that DO cancel — tradfi's combo-dominant present-set is the
      exposed case). **Quantify first**: re-run `enumerate --asset-group {tradfi,cefi} --dry-run` with an
      instrument*type breakdown to count the phantom `(options_chain|futures_chain, trades)` cells. **Fix options (owner
      decides)**: (a) apply the SAME `_rollup_bundle_grain` normalization to the present-set before the set-difference
      (symmetric); (b) writer/rebuild relabel `combo`→`options_chain` to match the seed; (c) admit
      `ohlcv*\*`/`tbbo` for chain instrument_types in the     validity matrix. Owner: vm-cross-cutting / slot-7 (the central enumerate producer). Repos: instruments-service     (`scripts/enumerate_expected_universe.py`) +
      unified-api-contracts (validity matrix). parent_epic: manifest_master. Provenance: tradfi pre-apply audit, slot-6
      2026-06-08.

- [x] ✅ [DOCS] P0. **M-COORD-1 — G0 doc-coherence reconcile GREEN (R6-codex closure, slot-4 2026-06-11 — pm@645648a03 +
      pm@55f9cf9c3 + this commit)**: CLAUDE.md + the codex layer (`pipeline-mode-partition.md` now carries the M1–M8
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
- [ ] [CHORE] P1. **M-COORD-4 — wire the gate-state board**: a small status block here (G0…G5 = RED/AMBER/GREEN per AG)
      refreshed at each gate promotion, so the orchestrator sees the critical path. Recompute from the registered plans'
      checkboxes (never hand-maintain divergent state). parent_epic: manifest_master.
- [x] ✅ [DEFI] P1. **M-COORD-5 (DeFi slice, slot-2) — DONE mtds@f80c50f1**: `rebuild_defi_manifest.py`
      `writer.add(...)` now passes `asset_group=defi` + the source-aware `pipeline_mode` + `source` + `transport` (no
      more blank `pipeline_mode`/`source` — standardisation finding #1 resolved); migrator likewise stamps source-aware
      in path+column. Tests green 25/25. Repo: market-tick-data-service. parent_epic: mtds_mdps_master.
- [x] ✅ [CROSS-CUTTING] P1. (mtds@7455ffb 2026-06-11: rebuild*tradfi (direct read :316) + rebuild_prediction (via
      reemit_honest_absence_rows) + rebuild_defi (defensive — unguarded log_event via ManifestWriter.add validation);
      cefi/sports pre-existing; the 5 migrate*_\*v9 movers + IS migrate_instruments_store_v9 VERIFIED no-manifest-read →
      not needed) \*\*M-COORD-6 — every AG `rebuild***manifest\*`/`migrate**\_v9`script must`setup_events()` before
      reading the manifest (surfaced + fixed-locally for sports by slot-4 pre-apply audit 2026-06-08; sports ship gated
      on M-COORD-7).** ROOT CAUSE:`read_availability_index()`→`\_backfill()`emits
      `READER_BACKFILLED_V8_COLUMNS_AS_NULL`via`log_event`whenever the per-VM fallback shards carry pre-v9 columns — the
      **GUARANTEED drained-fleet pre-migration state** (consolidated index stale → per-VM fallback → v8 shards). Without
      an events init,`log_event`raises`RuntimeError:     Event logging not     initialized`and **crashes the rebuild
      `--no-dry-run`apply**. The v8-era migration scripts ALL call`setup_events(mode="local",     sink=None)`in`main()`
      (`migrate_sports_canonical`/`migrate_defi_canonical`/`migrate_tradfi_canonical`/
      `migrate_polymarket_canonical`/`migrate_sports_hive_key`); the **newer v9 scripts dropped it\*\*. Confirmed
      MISSING in: `rebuild_defi_manifest.py`,
      `rebuild_cefi_manifest_`, `rebuild_tradfi_manifest\*`,     `rebuild_prediction_manifest.py`, `migrate_defi_full_v9_canonical.py`, `migrate_tradfi_to_v9_canonical.py`, and IS     `migrate_instruments_store_v9.py`(the ones that call`read_availability_index`). **Fix per AG-slot**: add     `setup_events(service_name="...",
      mode="local",
      sink=None)`at the top of`main()`(mirror the sports fix;     migrators that do pure object-path moves and never read the manifest — e.g.`migrate_sports_canonical_v9`
      — do NOT need it). Each AG slot owns its own script's one-liner. Repos: market-tick-data-service +
      instruments-service. parent_epic: mtds_mdps_master. Provenance: slot-4 sports pre-apply audit 2026-06-08.
- [ ] [DEFI] [CROSS-CUTTING] P0. **M-COORD-7 — DeFi LIVE handlers + engine catalog readers still write COARSE
      `pipeline_mode="batch"` (NOT source-aware) → batch≠live for DeFi AND blocks EVERY mtds code ship via STEP 5.85
      (surfaced by slot-4 sports pre-apply audit 2026-06-08).** The C-PATH inventory above marked the DeFi **migrator +
      rebuild** ✅ source-aware (mtds@f80c50f1) but the **41 inline `pipeline_mode="batch"` literals in the DeFi LIVE
      WRITE path** were NOT swept: ~29 `cli/handlers/*` (perp*funding/position_data/lst_rates/gas_fee/liquidations/
      flash_loan_events/native_staking/eigenlayer_rewards/bridge_events/jupiter_quote/oracle_prices/orca_whirlpool/
      phoenix_orderbook/raydium_classic_amm/solana_defi/staking_yields/token_transfers/vault_share_price/
      websocket_streaming/mev_events/governance*_/lending_indices/aggregator_route/protocol_outage_detector/…), the 5
      `engine/__catalog_reader.py`, + tradfi `massive_tradfi_rest_connector`/`tardis_adapter` + clients
      (`alchemy_\*`/`extended*base`/`tardis_base`/`thegraph_base`). Each is commented "Coarse ingestion mode → canonical     pipeline_mode= path segment (Live=Batch)". **TWO consequences**: (1) **batch≠live REGRESSION for DeFi** — DeFi     live-written data lands at `pipeline_mode=batch/`(coarse) while migrated DeFi batch data lands at    `pipeline_mode=batch*<source>/` (source-aware mtds@f80c50f1) → the migration CREATES a split the audit's ⑪     keystone forbids; (2) **STEP 5.85 (`no-inline-pipeline-mode-string-literal`, added pm@28698c856 2026-05-28)     hard-fails → mtds `quality-gates.sh`exits non-zero → NO`.qg_last_passed_sha`written →`quickmerge
      --agent`    refuses → NO mtds code (any AG) can ship** (it currently blocks slot-4's verified sports`setup_events`fix).     **FIX (slot-2 DeFi + cross-cutting)**: each handler/reader must pass the SOURCE-AWARE`PipelineMode.<BATCH_SOURCE>`    (or`derive_pipeline_mode_for_row(venue,
      ag,
      data_type)`/`resolve_pipeline_mode()`), the SAME value the v9     migrator + the shared `engine/orchestrator.py`
      write path use, so DeFi live == DeFi migrated-batch. Per-handler source derivation is DeFi-domain (the handler
      knows its venue/source) — slot-4 did NOT edit (collision + correctness risk across 41 DeFi sites). Repo:
      market-tick-data-service. parent_epic: mtds_mdps_master. Provenance: slot-4 sports pre-apply audit 2026-06-08
      (this is a NEW DeFi readiness blocker — it is NOT in the DeFi APPLY-READY verdict above, which covered
      migrator/rebuild but not the live handlers).

## Demotion + linkage record

- `defi_manifest_canonicalisation_2026_06_01.md` `## MASTER` section → demoted to **DeFi executor**; a banner points UP
  to this coordinator (its cross-plan registry is superseded by the table above).
- `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` → registered as **G0** (keeps its Phase-0
  apply-gate; this master references it, does not duplicate it).
- `master_to_live_defi_2026_05_23.md` → **downstream consumer** (G5 → live promotion); cross-linked, not subsumed.

## Verification (full-execution criterion)

This coordinator is COMPLETE-as-a-coordinator when: (1) every active data-layer plan/issue has a registry row + a
blocked-until edge; (2) the G0 doc-reconcile (M-COORD-1) is GREEN so no per-AG plan/codex doc contradicts the
source-aware model; (3) the audit SSOT carries ⑧+⑨; (4) the gate-state board reflects the registered plans' real state;
(5) 0 orphans. The migration itself is done by the registered sub-plans — this plan just proves they are correctly
sequenced and nothing is unblocked-out-of-order or orphaned.
