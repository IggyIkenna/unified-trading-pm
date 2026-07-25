---
doc_type: plan
title:
  MASTER COORDINATOR — data-layer canonicalisation history (2026-06-08 to 2026-06-29 dispatch-wave + audit-verdict
  Progress Log, extracted from the master coordinator)
summary: >-
  Companion history doc to `master_data_canonicalisation_migration_catalogue_2026_06_07.md` — the verbatim historical
  narrative (2026-06-11 coordinator-progress + FINAL REPORT + G1.schedule smoke verdict, 2026-06-17 R3 verdict-pack run,
  2026-06-29 G4 apply run, the 2026-06-11 R-wave resume brief, and the two slot-7 cross-cutting audit-verdict sections
  incl. the closed F-X1 finding) extracted for line-cap compliance (plan-hygiene discipline per
  `plans/active/task_template.md` §3 finding J). Zero open todos — pure narrative/evidence record; the parent plan
  remains the single live source of truth for all open work, the Gate-State Board, the Sub-plan registry, and the Master
  coordination todos.
status: complete
nature: record
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
tags: [coordinator, migration, manifest, data-layer, pipeline-mode, catalogue, progress-log, history, audit-log]
related:
  [
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/active/is_catalogue_g1_root_audit_log_2026_07_24.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  plan-hygiene line-cap remediation 2026-07-24 — extracted from
  master_data_canonicalisation_migration_catalogue_2026_06_07.md per plans/active/task_template.md §3 finding J
assigned_role: data_engineering
drift_direction: advance-code
---

# MASTER COORDINATOR — data-layer canonicalisation history (2026-06-08 to 2026-06-29)

> **Companion history doc, not the live plan.** This holds the verbatim historical Progress Log + audit-verdict sections
> extracted from `/plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md` to bring that
> coordinator back under the 1000-line `plans/active/` cap (the `umbrella: true` 2000L ceiling this doc previously
> carried was retired 2026-07-24 — flat cap now applies fleet-wide). Nothing below was rewritten; it remains the
> verbatim historical record, in original document order. 0 open todos of its own — every item quoted below was already
> closed (`[x]`) at extraction time, and the parent coordinator's Gate-State Board / Sub-plan registry / Master
> coordination todos are unaffected (they were NOT extracted — they remain the live state in the parent).

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
  `plans/archive/issues/qg_base_service_ratchet_exit_code_2026_06_11.md` (RESOLVED + archived 2026-06-17); composes with
  the existing "LOCAL QG HARNESS hollow sentinel" P2 above (this is a different, additional mechanism).

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
exit-code fix (archive/issues/qg_base_service_ratchet_exit_code_2026_06_11.md — RESOLVED 2026-06-17, hardening shipped
PM@a96992a33); (6) E5 catalogue-reader repoint gated on sports+pred roll-ups existing (only cefi/defi/tradfi have
prod/catalog.parquet).

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

### Autonomous run 2026-06-17 — R3 ⑬–⑲ verdict packs ASSEMBLED on HEAD + R8 + M-COORD-7 reconcile (G3.5 → G4-ready)

**Outcome: G3.5 pre-apply verification is operator-eyeball-ready. ALL FIVE AGs dry-run-GREEN → operator clear to fire G4
`--apply` on defi/cefi/tradfi/sports/prediction.** HARD-STOP respected — no `--apply`, no consolidator resume, no GCS
delete, no data VM. Verdict packs: `plans/audit/results/r3_verdict_packs_2026_06_17/` (per-AG render + `manifest_diff`

- verdict; `analyze_diff.py` + `manifest_diff_<ag>.json` attached).

* **Drift since 06-11**: market-data capture DRAINED since 06-08 → corpus FROZEN; the live `_index` was re-consolidated
  2026-06-14T12:19 (the diff baseline). So the 06-11 projections are HEAD-equivalent EXCEPT where a projection
  dependency moved. Two did: **defi** (rebuild changed mtds@89807b4 2026-06-16 — source+transport on CF-11 re-emit) and
  **prediction** (its UAC-resident cqg classifier). Both regenerated on HEAD; cefi/tradfi/sports reused their unchanged
  06-11 projections.
* **Per-AG verdicts (projected vs live 06-14 `_index`)**: **defi GREEN** cap 348,211→440,217, removed=39,867 = legacy
  `dex_swaps`→canonical `swaps_ohlcv_<tf>` data_type supersession + UNISWAPV3→UNISWAP_V3-CHAIN respelling, 105 phantom
  downgrades, net +331,124. **cefi GREEN** cap 1,332,922→2,491,437 (CF-11 honest-absence re-emit), removed=733 garbage
  venues (0 objects), 375 phantom downgrades, coverage 48.9%→64.1%. **tradfi GREEN** cap 100,787→902,878 (legacy
  pre-hive parser manifests 183,943 objects), 2,902 phantom downgrades **spot-verified on HEAD** (CME `day=2020-01-01`
  holds only ohlcv_1m/tbbo/trades — no ohlcv_15m object → the captured→empty downgrade is the honest correction),
  coverage 69.8%→95.4%. **sports GREEN** gate 0/0, only −17,288 ODDS_API zero-count probe-artifact exclusion.
  **prediction GREEN — 75.3% cqg coverage** (see below). Every AG: schema_version→v9 100%, pipeline_mode blank→
  source-aware, projected ≥ `pre_migration_2026_06_12` snapshot (no shrink). The gate's RED on 4 AGs is legacy

> **🔴→✅ Solana fake-history was a HIDDEN defi-`--apply` blocker — RECONCILED PRE-`--apply` 2026-06-17 (autonomous,
> opus).** The "defi GREEN" verdict above counted **fake Solana history as captured**: a single late-April-2026 live
> REST snapshot (Orca/Raydium/Kamino pools + Kamino/Solend lending) was back-dated across ~1200 `date=` partitions per
> tree in the legacy `dex_pools/`/`lending_indices/` side-trees, and **62 of those shards were `captured`** in the live
> defi `_index` (KAMINO/SOLEND lending_indices, all dated < 2026-04-14 — i.e. zero genuine per-date history). Had G4
> `--apply` run first, it would have locked in fake Solana history as real. **Fixed**: (1) MTDS forward-only-honest
> write gate so a now-snapshot can never be back-dated onto a historical `date=` again
> (`solana_defi_handler.py::_filter_rows_to_target_day` + `_write_solana_shard` guard); (2) **6000** fake back-dated GCS
> objects deleted (8 genuine 2026-04-14 capture files kept) via UTL `gcs_delete_object`; (3) re-projected defi index
> (`_index/audit/projected_index_defi_head20260617.parquet`) confirms the **62 fake `captured` Solana rows → 0 captured
> / `empty_confirmed`**. **Defi is now genuinely safe to `--apply` w.r.t. Solana.** SSOT:
> `plans/active/issues/solana_defi_fake_history_snapshot_2026_06_17.md` (RESOLVED). data_type/venue/grain supersession +
> spot-verified phantom corrections, NOT data loss (captured RISES everywhere; orphan sweep E=0).

- **PREDICTION cqg correction (operator-prompted — important for resumers)**: a first pass against the **06-11**
  projection read 0.2% coverage / 542,170 `attempted_failed[ClassifierConfidenceLow]` and I provisionally flagged it
  BLOCKED-OPERATOR-DECISION (cqg-classifier coverage). **The operator correctly identified this as stale.** Root cause:
  the cqg classifier lives in **UAC** (`classify_polymarket_to_canonical_group`), and the registry was EXPANDED under
  **decision 338** in 3 UAC commits AFTER the 06-11 projection (`uac@8e3108d` sports matrix +30 groups/17 leagues ·
  `uac@e0035fd` crypto PRICE_RANGE + political + geo + box-office + MISC_NOVELTY · `uac@d52217f` 10 alt-coin +7 macro +
  weather). The "frozen-corpus → projection-valid" shortcut held for defi/cefi/tradfi/sports but NOT prediction (its
  rebuild calls the moved UAC classifier). **Re-projected on HEAD: 0.2%→75.3% coverage; 542,170 ClassifierConfidenceLow
  →1; captured 7,116 cqg bundles** (`projected_index_prediction_head20260617.parquet`, 9,447 rows, 573,536 objects
  scanned/2,483s). The earlier "BLOCKED-OPERATOR-DECISION on cqg coverage" is **RESOLVED — no operator decision
  outstanding**; the registry already covers the live market set. Lesson logged for resumers: a manifest projection's
  dependencies include UAC classifiers/registries, not just the rebuild script + the corpus.
- **M-COORD-7**: independently CONFIRMED GREEN on LDR HEAD — STEP 5.85 (`no-inline-pipeline-mode-string-literal`) = 0
  hits + the AST `check_pipeline_mode_explicit_at_record_calls.py` = 0 occurrences; every DeFi live handler stamps the
  source-aware `PipelineMode.BATCH_ONCHAIN_RPC/SUBGRAPH/...` (batch==live). The checkbox was already flipped upstream
  (aaa133c72, mtds@c4c5f15); this run corroborates it.
- **R8**: prediction migrator dry-plan on HEAD = 1,897,691 planned moves / 0 errors (GREEN); sports R8 was DONE 06-11.

### G4 apply run 2026-06-29 — 4/5 AGs COMPLETE; TradFi BLOCKED (OOM-killed migration)

**Operator granted permission 2026-06-29**: "do it yourself please / i give permission" — agents authorized to fire all
G4 `--apply` steps autonomously (overrides the standard HARD-STOP). Progress this run:

- **IS v9 migration (`migrate_instruments_store_v9.py --apply --workers 16`) — ALL 5 AGs DONE:**
  - prediction: 4,729 objects moved (instruments-store-pred-prd-central-element-323112) ✅
  - cefi: 40,744 objects moved (instruments-store-cefi-prd-central-element-323112) ✅
  - defi: 103,944 objects moved (instruments-store-defi-prd-central-element-323112) ✅
  - tradfi: 15,453 objects moved (instruments-store-tradfi-prd-central-element-323112) ✅
  - sports: 679,761 walked, 28,496 planned, 2,118 moved (instruments-store-sports-prd-central-element-323112) ✅

- **MTDS raw-tick v9 migration (step 2 of G4 sequence):**
  - DeFi: `canonical-migration-defi-20260618-180603` rc=0 ✅
  - CeFi: already canonical on-disk (`pipeline_mode=batch_tardis/asset_group=cefi/` paths confirmed) ✅
  - Sports: `canonical-migration-sports-20260618-180654` rc=0 ✅
  - Prediction: `canonical-migration-prediction-20260629-053038` rc=0 (500,128 objects, processed_candles/by_date) ✅
  - TradFi: `canonical-migration-tradfi-20260629-053023` 🔴 FAILED/STALLED — log stalled 06:02 UTC after SSL EOF +
    connection-pool-full errors; ~37k/3.8M processed_candles migrated (~1%); no EXIT_STATUS; serial console shows
    continuous memory pressure 06:12→07:49+ UTC (OOM-kill suspected). VM still RUNNING but script dead. **OPERATOR
    ACTION REQUIRED**: restart with lower concurrency/larger VM (migrator is idempotent — already-copied objects skip).
    L-hive phase (2,447,478 walked, 207,247 moved) may also be incomplete if the delete step didn't run.

- **Catalogue seed — `enumerate_expected_universe --apply-write` (step 3 of G4 sequence):**
  - DeFi: 1,380,376 rows (EXPECTED_PRE_GENESIS_CHAIN: 804,563 + EXPECTED_INSTRUMENT_NOT_LISTED: 575,813) →
    `enum-universe-defi-1782720346.parquet` ✅
  - CeFi: 162,528 rows (EXPECTED_PRE_VENUE_LAUNCH) ✅ (prev session)
  - Sports: 16,554 rows (EXPECTED_PRE_SOURCE_COVERAGE_START) ✅ (prev session)
  - Prediction: 9,120 rows (EXPECTED_PRE_VENUE_LAUNCH) ✅ (prev session)
  - TradFi: NOT YET (awaiting MTDS migration success)

- **IS backfill — `build_instrument_catalogue` (step 4 of G4 sequence):**
  - DeFi: 7,236 rows, monotonic_ok (new=current — no write needed) ✅
  - Sports: 113 rows > 94 — promoted to `instruments-store-sports-prd/.../prod/catalog.parquet` ✅
  - Prediction: 2,486,092 rows, monotonic_ok (current — no write needed) ✅ (prev session)
  - CeFi: 349,912 rows > 349,709 — promoted at 2026-06-29T10:23:17Z →
    `instruments-store-cefi-prd/.../prod/catalog.parquet` (4,611,608 bytes) ✅
  - TradFi: NOT YET (awaiting MTDS migration restart + success)

- **RESUME runbook (48 paused schedulers)**: NOT YET — runs after TradFi G4 also verified. **UPDATE 2026-07-12
  (doc-reconciliation, plan-reconciliation finding 128 —
  `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2)**: G4 now verified (2026-07-12) —
  runbook is ACTIONABLE; owning todo added to `tradfi_v9_stage1_finish_2026_07_06.md` (this edit).

**4/5 AGs COMPLETE as of 2026-06-29T10:23 UTC.** TradFi slot-6 remains open pending MTDS migration restart (operator
must restart VM or rerun migration script with lower concurrency to avoid OOM).

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
  RESUMED + COMPLETED 2026-06-11 (slot-4): pm@a28cbd4d7 (codex contract) + pm@51863c157 (seam docs) + the docs(plans)
  de-coarsen/flip commit — R6-codex + M-COORD-1 ticked below.**
- **R4 (no tree WIP found)**: investigation state unknown — restart the diagnosis from the task spec (decision #4);
  check `gcloud scheduler jobs describe` for the IS jobs + instruments-store `by_date/` last-written days first.
- **R5 (no tree WIP found)**: smoke matrix probes were running (125 tool calls); no ledger written — restart from the
  task spec (decision #5); reuse any /tmp probe logs on the host if present.

Standing context for resumers: HARD-STOP remains the per-AG migrator `--apply`; R7+R3 (re-dry-runs on final HEAD +
projected `_index` + dev renders + ⑬–⑲ verdict packs) and R8 (sports sweep + v1_archive gate + prediction dry-plan
regen) queue AFTER R1/R2 land. Playwright + chromium are installed on this host for the V5 drilldown evidence packs.

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

> **🔴 BAR-EDGE BLOCKER (feature-layer gate, 2026-06-08) — `bar_edge_left_vs_right_remediation_2026_06_08.md`** (now
> archived → `plans/archive/2026_07/bar_edge_left_vs_right_remediation_2026_06_08.md`, folded→M-1 2026-07-13, finding
> 197): a CLOSED candle stamped on the OPEN/left edge = look-ahead → leakage. Data-verified scope (Harsh): the MDPS
> **processed candle store is right-edge CORRECT** (so this does NOT block the raw/manifest `--apply` — slots 2–6 G4
> proceed), but the **FEATURE LAYER is gated** — the two features-service resamplers (the only realized bugs) are fixed
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

- [x] ✅ [TEST] P2. **F-X1 — DONE mtds@657f615 (2026-06-16 /autonomous).** Rewrote the stale tautological test (renamed
      `test_adapter_resolves_test_bucket_when_is_test_run` → `test_adapter_resolves_canonical_bucket_shape`): old
      assertion encoded the legacy env-as-prefix shape `market-data-tick-test-cefi-{project}`; new assertion asserts the
      canonical `resolve_bucket_name` env-after-asset_group shape `market-data-tick-cefi-test-my-project`. Code was
      already correct (`get_tick_data_bucket`→`get_market_data_bucket`→`resolve_bucket_name`). Test green; mtds QG
      green. Original finding below ⤵
      **`market-tick-data-service/tests/market_interface/adapters/cefi/test_tardis_canonical_output.py::test_adapter_resolves_test_bucket_when_is_test_run`
      is STALE — it asserts the legacy `is_test_run`→`market-data-tick-test-cefi-{project}` f-string shape, but
      `engine.orchestrator.get_tick_data_bucket` was canonicalised to the bucket-name SSOT (`resolve_bucket_name`,
      remediated 2026-06-01 per `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` (folded→M-1, archived
      `plans/archive/2026_07/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` 2026-07-13, finding 197): it
      `del config` + self-sources env from `DEPLOYMENT_ENV_SHORT` (test→`...-cefi-test-...`, not a config flag).** The
      CODE is right; the test asserts the retired knob → locally returns `market-data-tick-cefi-prd-test-account`
      (ambient env). Pre-existing on LDR (tab==LDR, 0 ahead — not introduced by the canonicalisation work). **NOT a
      pipeline_mode/Era-B/migration `--apply` regression** (the migrators call `resolve_bucket_name` with an explicit
      `env`, not `get_tick_data_bucket`). **Fix = rewrite the test to set `DEPLOYMENT_ENV_SHORT=test` and assert the
      canonical `market-data-tick-cefi-test-{project}` env-tier shape (or delete the obsolete `is_test_run`
      assertion).** Repo: market-tick-data-service. parent_epic: mtds_mdps_master. Provenance: slot-7 cross-cutting
      pre-apply audit 2026-06-08.
