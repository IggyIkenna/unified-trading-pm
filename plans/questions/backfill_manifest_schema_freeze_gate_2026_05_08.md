---
title: Backfill + manifest schema freeze gate — can MTDS/MDPS backfills (re)start without invalidation?
type: question-doc
status: ratified-spawned-successor
spawned_plan: plans/active/manifest_schema_final_gate_2026_05_09.md
created: 2026-05-08
last_updated: 2026-05-09
author: ikenna
related:
  - plans/active/manifest_v7_schema_migration_design_2026_05_08.md
  - plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md
  - plans/active/manifest_cross_asset_rescan_design_2026_05_08.md
  - plans/active/writegate_honest_coverage_endtoend_2026_05_06.md
  - plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md
  - plans/active/features_repo_consolidation_2026_05_08.md
  - plans/epics/manifest_migration_master_2026_05_07.md
  - plans/active/master_to_live_defi_2026_05_23.md
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Backfill + manifest schema freeze gate — can MTDS/MDPS backfills (re)start without invalidation?

> **Operator concern (verbatim, 2026-05-08).** "We keep changing manifest schema → re-running backfills → changing again
> → burning Databento/Tardis API quota." Need a **freeze gate** answer: are we ready to (re)start MTDS / MDPS backfills
> with confidence the manifest schema + on-disk shape won't change again under us before the May-23 cutover?
>
> **Why this matters.** Databento + Tardis quota is finite + paid. Every restart = real $ + real wall-clock. Sports +
> TradFi backfills are cheaper but the schema-churn cost is the same: features / ML / strategy compute downstream of
> MTDS reads the manifest, so a schema change mid-flight either (a) silently corrupts downstream output or (b) forces a
> downstream re-run too.
>
> **Scope.** This Q-group is **NOT** "is the live pipeline ready" (that's
> [`topology_features_strategy_ml_execution_2026_05_08.md`](topology_features_strategy_ml_execution_2026_05_08.md)) and
> NOT "is paper-mode wired" (that's
> [`paper_vs_live_workflow_maturity_2026_05_08.md`](paper_vs_live_workflow_maturity_2026_05_08.md)). It is specifically
> about whether the **batch backfill layer** (MTDS adapters + MDPS reprocess + features-\* recompute) can run to
> 7-day-pre-cutover-completion without a mid-run schema change forcing a redo.

---

## State of play — what's shipped vs what's pending (2026-05-08)

> Fold-in from the freeze-gate audit done 2026-05-08 (see § Decision log at bottom). Numbers + commit shas need operator
> verification — agent assertions only.

### Shipped + canonical (safe to backfill against)

| Item                                                                                                                                                  | Where                                  | Status                                                                                                                                       |
| ----------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **v5 base manifest schema** (asset_group, venue, chain, data_type, instrument_type, instrument_id, league_id, timeframe, feature_group, model_family) | UTL `manifest_writer.py`               | Live since 2026-04. Stable.                                                                                                                  |
| **v6 columns** (`quote_asset`, `margin_type`, `combo_type`, `leg_weights`)                                                                            | UTL                                    | Shipped. Deribit linear-vs-inverse + multi-leg synthetic disambiguation.                                                                     |
| **v7 columns** (`fixture_id`, `job_id`)                                                                                                               | UTL @ `ed658e9b`                       | Shipped. Sports per-fixture + ML/strategy/execution experiment keys.                                                                         |
| **4-state `capture_status`** (`captured` / `empty_confirmed` / `attempted_failed` / `expected_unattempted`)                                           | UTL + UAC                              | Shipped. `expected_unattempted` added 2026-05-07 evening per writegate Phase 3.D.5.                                                          |
| **Typed `error_reason`** (`EMPTY_CONFIRMED_REASONS` closed set)                                                                                       | UAC                                    | Shipped. `LegacyBlankErrorReasonError` raises loud on blank reasons (UTL @ 68b3804a).                                                        |
| **Per-row `available_at` column**                                                                                                                     | UTL `record_captured` writer assertion | Shipped. Write-time stamping per writegate Phase 1A.                                                                                         |
| **`pipeline_mode` UAC enum + UTL kwarg**                                                                                                              | UAC + UTL Phase 1A/1B/1C               | Shipped 2026-05-08 (`unified-api-contracts@8bc3f2a`, `unified-trading-library@87134364`, `unified-api-contracts@6a8529f`). Default `= None`. |

### Designed-but-not-shipped (additive — won't invalidate captured rows if MTDS writes with `pipeline_mode=` kwarg)

| Item                                                            | Plan                                                       | Status                                                                                            | Invalidation risk                                                                                                                        |
| --------------------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **`pipeline_mode=` hive partition on disk**                     | `gcs_migration_bundle_pipeline_mode_2026_05_08` Phase 3    | DRAFT — Phase 0 + 1 + 2 shipped; Phase 3 (the actual migration VMs) operator-gated.               | **Low** — Phase 5 reader fallback paths cover legacy → canonical lookup ≤30d post-migration. Backfill-during-Phase-3 is the risk window. |
| **`category=` → `asset_group=` rekey on disk**                  | gcs_migration Phase 3 (bundled)                            | DRAFT — same Phase 3 VM run.                                                                      | **Low** — reader fallback already exists per CLAUDE.md "asset-group vocabulary" rule.                                                    |
| **5 drift axes cleared** (354 residual phantom rows from 05-04) | gcs_migration Phase 6 + cross-asset rescan                 | DRAFT — runs after Phase 3.                                                                       | **None** for backfill — phantoms are dead rows, not data corruption.                                                                     |
| **Phase 4 consumer sweep** (explicit `pipeline_mode=` kwarg)    | gcs_migration Phase 4                                      | DRAFT — workspace-wide grep + per-adapter wire-in pending.                                        | **High if skipped, low if shipped before backfill** — without explicit kwarg, MTDS writes `pipeline_mode=None` rows that need re-stamp.  |
| **`hard_schema_enforcement_2026_05_08`**                        | `plans/active/hard_schema_enforcement_2026_05_08.md`       | DRAFT — schema-on-read enforcement.                                                               | **Additive** — fails loud on bad rows; doesn't change row shape.                                                                         |
| **`available_at_lookahead_bias_completion_2026_05_08`**         | `plans/active/available_at_lookahead_bias_completion_*.md` | DRAFT — extends `LookaheadBiasError` enforcement to every features-\* calculator (warn → strict). | **None for MTDS** — it's a features-layer change, not a writer-layer change.                                                             |

### Designed-but-not-shipped (DESTRUCTIVE — WILL invalidate captured rows if it ships mid-backfill)

| Item                                                                                                                                                            | Plan                                             | Status                                                                                      | Invalidation risk                                                                                                                                                                                                                        |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **v8 manifest schema** (`service_emission_state` + `last_emission_decision_at` + `expected_window_completeness_pct` columns; row-key extension)                 | `manifest_v7_schema_migration_design_2026_05_08` | **DRAFT — BLOCKED** on `live_pipeline_mtds_mdps_features_2026_05_08` Phase 11 slice b spec. | **Critical.** Stage 1 schema-bump commit gated on slice b. If slice b ships + Stage 1 commits while backfill is in-flight → captured rows split between v7 + v8 shapes → reader inconsistency → re-stamp needed across the whole window. |
| **Cross-asset rescan flip schema** (class A mutable / B immutable / C triage)                                                                                   | `manifest_cross_asset_rescan_design_2026_05_08`  | DRAFT — design only; Python script + launcher Harsh Tab 4 / future-session.                 | **Low if rescan runs AFTER backfill complete** (correct sequencing per its Q3). **High if rescan runs concurrently** with backfill — same row_key written by both writers races on the canonical CAS.                                    |
| **Manifest migration master Stage 4** (residual sports rename / writegate Phase 2.A residuals / any other Stage-4 migrations bundled with the GCS Phase 3 walk) | `manifest_migration_master_2026_05_07` (epics)   | Stage 1+2+3 status unverified; Stage 4 explicitly bundled with gcs_migration Phase 3.       | **Low if bundled with Phase 3 as planned** — same parquet walk, single rewrite. **High if Stage 4 spawns its own walk after Phase 3** — second migration over already-migrated data risks re-keying mid-flight.                          |
| **features-\* repo consolidation** (5-6 repos → 1 features-service)                                                                                             | `features_repo_consolidation_2026_05_08`         | DRAFT — 3-5 day pre-req for live-pipeline activation.                                       | **None for MTDS writer** — features-\* is downstream. **High for MDPS / features-\* backfill data** if consolidation changes feature_group taxonomy + invalidates the feature_group manifest column.                                     |

---

## Currently-running VMs / pending operations

> Operator: please verify these counts; agent has not run live `gcloud compute instances list`.

| Surface                                          | Count                                                                                    | Pipeline_mode kwarg?                                                                                                | Bounce-sweep needed?                                                             |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| MTDS CeFi historical (Databento + Tardis)        | "18 awaiting bounce" (CLAUDE.md memory 2026-05-07) — current state?                      | Defaulting to `None` until Phase 4 sweep + adapter wire-in lands. Re-launch after Phase 4 to write canonical paths. | YES — to write `pipeline_mode=BATCH_DATABENTO` / `BATCH_TARDIS` instead of None. |
| MTDS TradFi (Databento futures + ETFs + options) | mdps-tradfi-2021..2025 5 VMs (writegate audit 2026-05-07)                                | Same as above.                                                                                                      | YES.                                                                             |
| MTDS Sports backfill (af / fs / sfi / us)        | 4 VMs (writegate audit 2026-05-07)                                                       | Same.                                                                                                               | YES.                                                                             |
| MTDS DeFi (Pyth / Chainlink / on-chain)          | Unknown — agent didn't probe.                                                            | Same.                                                                                                               | YES if running; otherwise launch fresh post-freeze.                              |
| MTDS Prediction (Polymarket / Kalshi)            | Unknown.                                                                                 | Same + market-lifecycle considerations per CLAUDE.md prediction lifecycle rule.                                     | YES if running.                                                                  |
| MDPS reprocess                                   | Likely paused per Tab 2 deferred-after-features-consolidation note in memory 2026-05-08. | N/A until features consolidation lands.                                                                             | Not yet — gated on features consolidation.                                       |
| features-\* compute                              | Same — paused for consolidation.                                                         | N/A.                                                                                                                | Not yet.                                                                         |

---

## Question blocks

### Block A — Schema freeze: can we lock v7 as final-for-backfill?

A1. **Can `live_pipeline_mtds_mdps_features_2026_05_08` Phase 11 slice b be deferred until AFTER MTDS backfill
completes?** Slice b is the closed-set spec for `ServiceEmissionStateEnum` + manifest-read protocol. If slice b ships +
the v8 Stage 1 schema-bump commit lands while backfill VMs are mid-run, the manifest will have a mix of v7 rows
(captured before slice b) and v8 rows (captured after) — readers must handle both, and any post-backfill rescan sees
inconsistent shape. **Operator decision needed:** lock v7 as the final shape until backfill completes, OR ship slice b
with explicit synchronization (drain VMs → ship Stage 1 → relaunch VMs).

A2. **If slice b cannot be deferred, what's the synchronization protocol?** Options:

- (a) Pause backfill for 6-12h while Stage 1 + the v8 migration script bump every existing row.
- (b) Let backfill complete on v7; v8 Stage 1 ships post-backfill; the cross-asset rescan picks up the v8 backfill in a
  single pass.
- (c) Run the v8 migration script as a continuous daemon during backfill — but this conflicts with the per-VM shard
  isolation rule (the daemon would race on canonical CAS with the writers).

A3. **Is there any OTHER pending schema change not in the table above?** Specifically: any UAC enum that's about to gain
a new value (`PipelineMode`, `EMPTY_CONFIRMED_REASONS`, `ServiceEmissionPolicy`, instrument_type taxonomy) mid-flight?
Adding a value to a closed set is technically additive but invalidates "we already enumerated all possibilities"
assertions in downstream consumers.

### Block B — On-disk shape freeze: GCS Phase 3 timing

B1. **When does `gcs_migration_bundle_pipeline_mode_2026_05_08` Phase 3 run?** Two scenarios:

- **(a) Phase 3 runs 2026-05-13/14/15 as planned in the bundle.** MTDS backfill must queue until Phase 3.6 QA gate
  passes per asset_group (~2026-05-16 earliest start). 7-day testing window before May-23 cutover gets cut to ~6 days
  max if backfill takes the full 5 days.
- **(b) Phase 3 deferred until AFTER MTDS backfill completes (≥2026-05-21).** MTDS backfill writes legacy paths + Phase
  5 reader fallback handles them ≤30d post-migration. Phase 3 sweeps backfill output + rewrites in single walk. Gives
  12-13 day backfill window.
- **(c) Phase 3 abandoned; legacy paths kept indefinitely.** Violates workspace "no double SSOT" rule — readers must
  keep both paths forever. **Banned.**

B2. **Phase 4 consumer sweep — is it gating MTDS launches or can MTDS launch with explicit `pipeline_mode=` kwarg
hand-coded per adapter NOW?** Phase 4 is the broader workspace sweep. If MTDS adapters get explicit kwargs hand-edited
NOW (≤1d work for ~6 adapters), the rest of Phase 4 (instruments-service, MDPS, features-\*, deployment-api,
e2e-testing) can lag.

B3. **Cross-asset rescan timing — can it be deferred to post-cutover (post-May-23)?** Its Q3 says "rescan must run AFTER
gcs_migration Phase 3 + Phase 6 phantom cleanup, not before." But does it need to run BEFORE backfill, or AFTER? If it's
a post-backfill cleanup, the freeze gate question is moot for rescan.

### Block C — Operationally vs code shipped (Plans Run To Actual Completion HARD RULE)

> Per CLAUDE.md HARD RULE codified 2026-05-08: code-shipped ≠ operationally-shipped. Verify every backfill prerequisite
> actually ran on real infra, not just merged.

C1. **Was Phase 0 of gcs_migration actually run on a same-region GCE VM?** The Phase 0 plan body marks `[x]` (issue doc
shipped at `gcs_migration_bundle_preaudit_2026_05_08.md`), but Phase 0 § "Run results" was deferred to operator on a
same-region VM. **Has the operator's same-region run actually completed?** If no, the migration cost estimate + parquet
count + drift histograms are unknown — Phase 3's wall-clock estimate (cefi 8h / defi 4h / tradfi 6h / sports 12h /
prediction 2h) is uncalibrated.

C2. **Was the writegate Phase 5 ratchet baseline measured on production manifests?** Per CLAUDE.md memory entry
2026-05-07 evening: "Per-data_type cells TBD via operator-run measure-honest-coverage.py on same-region GCE VM." If
baseline isn't locked before MTDS backfill writes new rows, coverage % will shift mid-run + the baseline becomes
meaningless.

C3. **Were the existing 18+ MTDS VMs from the parallelization fix actually drained, or are they still running with the
old un-parallelized adapter?** Per memory 2026-05-07: "MTDS@28db65a Tardis swap shipped + 18 VMs awaiting bounce-sweep"
— sweep may not have happened. Running adapters with old code + new manifest writer = silent inconsistency.

C4. **Has the cross-asset rescan launcher script actually been written?** Per
`manifest_cross_asset_rescan_design_2026_05_08.md` line 113: "Launcher script ... is queued as a follow-up; not shipped
in this session due to rate-limit cap on the launcher sub-agent." If still not shipped, rescan can't be
operator-triggered post-backfill.

### Block D — Quota math: how many backfills are we paying for?

D1. **What's the rough Databento + Tardis monthly quota burn from the existing 18 VMs?** If we restart from scratch
post-freeze, what's the additional cost? Operator-only data — agent can't probe billing.

D2. **Is the manifest concurrency principle (read-once + per-shard freshness check + write-time CAS, per CLAUDE.md
"Manifest concurrency principle") actually wired into MTDS adapters?** If yes, restarting backfill on already-captured
days is a no-op (skip). If no, restart re-fetches every day in the manifest's date range — full quota cost for each
restart. **The freeze gate matters more if no, less if yes.**

D3. **Backfill chunking — are existing VMs sharded such that a kill-and-restart of one VM doesn't re-fetch the entire
range, just the un-captured days within that VM's slice?** Per `MANIFEST_PER_VM_SHARDS=true` + per-VM shard isolation
rule, this should be true. Operator: confirm.

### Block E — The actual freeze-gate verdict

E1. **Decision: lock the schema NOW (v7 final until cutover) — yes / no?** If yes, slice b + v8 are deferred to
post-cutover; cross-asset rescan deferred; gcs_migration Phase 3 still runs (it's additive). MTDS backfill can launch
once adapters pass explicit `pipeline_mode=` kwarg.

E2. **Decision: GCS Phase 3 timing — (a) before backfill or (b) after backfill?** Cleanest answer is (b): backfill
writes legacy paths, single Phase 3 walk migrates everything (backfill output + pre-backfill data) in one pass. Tighter
answer is (a): backfill writes canonical paths from day 1, no migration of new data. Operator's call; depends on Phase 3
wall-clock confidence (Block C1).

E3. **Decision: pre-launch checklist for the bounce-sweep.** Closed set:

1. UTL `manifest_writer.py` `pipeline_mode=` kwarg verified shipped + default kept as `None` (back-compat) until Phase 4
   closes.
2. Each MTDS adapter (Databento / Tardis / CCXT / Barchart / Yahoo / Sports / DeFi / Prediction) explicitly passes
   `pipeline_mode=PipelineMode.BATCH_<source>` per UAC SOURCE_PRIORITY mapping (Phase 1C reader pattern).
3. Manifest concurrency principle (`_TTL_SECONDS=60` + `_refresh_captured_cache` + `_is_now_captured`) wired into every
   MTDS launcher script.
4. Per-VM shard isolation envvars (`MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=<unique-tag>`) set in every launcher.
5. Event-stream verification protocol: STARTED + per-instrument progress events + STOPPED. Per CLAUDE.md "no
   fire-and-forget VM launches."
6. Tarballs refreshed via `bash deployment-service/scripts/vm/create-code-tarballs.sh --all` after Phase 4 lands.
7. Watchdog dict (`vm_zombie_watchdog.py`) registers every prefix used by the bounce-sweep.

E4. **Recommended freeze-gate mitigation if v8 cannot be deferred:** drain VMs at end of each asset-group's backfill
(natural sub-completion boundary), let v8 Stage 1 land, relaunch for the next asset-group. Sequence: cefi (1-2d) → drain
→ v8 if ready → defi (1d) → drain → tradfi (1-2d) → drain → sports (2-3d) → drain → prediction (<1d) → final cross-asset
rescan post-cutover.

---

## Cross-references

- **Topology Q-group** —
  [`topology_features_strategy_ml_execution_2026_05_08.md`](topology_features_strategy_ml_execution_2026_05_08.md):
  features / strategy / ML / execution layer topology across batch/live/paper. This Q-group sits UPSTREAM of that — MTDS
  backfill is the data substrate the topology questions assume exists.
- **Paper-vs-live workflow** —
  [`paper_vs_live_workflow_maturity_2026_05_08.md`](paper_vs_live_workflow_maturity_2026_05_08.md): operational mode
  semantics. Orthogonal — backfill is batch-only by definition.
- **Master plan** — [`../active/master_to_live_defi_2026_05_23.md`](../active/master_to_live_defi_2026_05_23.md): Group
  F item 17 (paper-trade smoke) + item 18 (batch-vs-live recon) both depend on MTDS backfill being complete + manifest
  being stable. This Q-group is the gating layer.
- **Manifest migration epic** —
  [`../epics/manifest_migration_master_2026_05_07.md`](../epics/manifest_migration_master_2026_05_07.md): the umbrella
  Stage 1-4 plan; this Q-group is the concrete decision layer for Stage 3 → Stage 4 transition.

## Decision log

- **2026-05-08** — Q-group created from operator concern about repeated schema-change-induced backfill restarts.
  Triggered by 2026-05-08 close-out reads of `manifest_v7_schema_migration_design`,
  `gcs_migration_bundle_pipeline_mode`, `manifest_cross_asset_rescan_design`. Awaiting operator review of Block A-E.
- **2026-05-09 — B1 / E2 ANSWERED: option (a).** GCS Phase 3 runs first (~May 13-15 in the bundle). MTDS backfill queues
  until Phase 3.6 QA gate passes per asset_group. Backfill writes canonical `pipeline_mode=` paths from day 1 — no
  migration of new data needed.
- **2026-05-09 — A1 / E1 OVERRIDE: ship the BEST manifest before cutover, NOT the v7-frozen-partial.** Operator
  direction (verbatim): _"i want the best manifest before may 23rd not a partial one all the items done."_ This reverses
  the previous "v7 lock + defer v8/slice b/rescan post-cutover" reading. Maximalist sequence: every
  designed-but-not-shipped item lands before May 23. The bundled-walk approach is the only way the math fits in 14 days
  — Phase 3's parquet walk MUST also do the v8 NULL-column backfill + drift cleanup in the same pass, so one walk covers
  `pipeline_mode=` partition + `category=`→`asset_group=` rekey + 5 drift axes + v8 columns + cross-asset rescan
  auto-fixes. A second walk is unaffordable.

### Implications of "best manifest, all items done before May 23"

- **A1 / E1 → NO, do NOT lock at v7.** Ship v8 (all 3 columns: `service_emission_state` + `last_emission_decision_at` +
  `expected_window_completeness_pct`) before May 23. `live_pipeline` Phase 11 slice b is now the **#1 critical-path
  blocker** — it gates `manifest_v7_schema_migration_design` Stage 1, which gates the Phase 2 migration script
  extension, which gates the Phase 3 bundled walk, which gates MTDS backfill.
- **A1 sub-decision → unblock slice b NOW.** Two paths: (i) operator directs an agent to ship the closed-set
  `ServiceEmissionStateEnum` (the design doc's proposed 4 values: `PUBLISHED_OK` / `PUBLISHED_DEGRADED` /
  `STALE_DATA_HEARTBEAT_ONLY` / `BLOCKED`) + manifest-read protocol by ~May 11; (ii) ratify the proposed 4-value set as
  the closed set NOW (operator approves on this Q-doc) and an agent ships the spec inline as a sub-plan. **Recommend
  (ii)** — saves the slice-b spawn cycle. The 4 values cover the writegate Phase 4 typed-error rendering needs + the
  live_pipeline Phase 12 batch-vs-live reconciliation gate; expanding later is additive.
- **B2 → Phase 4 consumer sweep is workspace-wide critical path.** MTDS hand-edit isn't enough — every consumer of
  `record_*` (instruments-service / MDPS / features-\* / deployment-api / e2e-testing harnesses) must pass explicit
  `pipeline_mode=` kwarg AND populate the 3 new v8 columns at the policy-hook boundary. Parallel-agent fan-out per
  CLAUDE.md "Sub-Agents & Autonomous Agents" rule — paste mandatory rules + spec each repo.
- **B3 → cross-asset rescan runs BEFORE cutover, bundled into the Phase 3 walk.** Rescan's class-A auto-fixes
  (hive-vocab / instrument_type casing / schema-4 empty / chain-bundle equivalence) overlap with Phase 3's drift axes —
  fold them into a single pass. Class-C triage rows go to operator review during the May 16-22 testing window. Launcher
  script (Q C4) ships by May 11.
- **C1 → Phase 0 pre-audit run is the absolute first step.** Without calibrated Phase 3 wall-clock, the entire May 13-15
  window is a guess. Run May 9-10 on a same-region GCE VM. Per CLAUDE.md phantom-audit recipe.
- **C2 → writegate Phase 5 ratchet baseline locks by May 12.** Baseline must reflect post-bundled-walk + post- backfill
  state, but to compute the ratchet the pre-backfill baseline must be measured first. Run `measure-honest-coverage.py`
  May 10 on production manifests, then re-measure post-cutover for the ratchet.
- **C3 → 18-VM bounce-sweep happens TWICE.** First sweep before Phase 3 (May 12) to drain stale VMs from the manifest.
  Second sweep after Phase 3 (May 16) with full Phase 4 wire-in (explicit `pipeline_mode=` + `service_emission_state` +
  per-row `available_at` + manifest concurrency principle).
- **D2 / D3 → manifest concurrency principle MUST be verified in MTDS adapters this week.** If not wired, bounce-sweep
  #2 re-fetches every day in scope — full Databento + Tardis quota cost. Audit Tab 2 / MTDS parallelization plan output
  to confirm `_TTL_SECONDS=60` + `_refresh_captured_cache` + per-VM shard isolation.

### Critical-path schedule (maximalist — best manifest, all items done by May 23)

| Date      | Milestone                                                                                                                               | Owner            |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| May 9     | Operator ratifies slice b 4-value `ServiceEmissionStateEnum` (or directs spec sub-plan).                                                | Operator         |
| May 9-10  | Phase 0 pre-audit run on same-region GCE VM.                                                                                            | Operator-gated   |
| May 9-10  | writegate Phase 5 ratchet PRE-baseline measurement.                                                                                     | Operator-gated   |
| May 9-11  | UAC v8 schema-bump (slice b enum + 3 manifest columns) ships.                                                                           | UAC / Tab 2      |
| May 9-11  | Cross-asset rescan launcher script ships (Q C4 closed).                                                                                 | Harsh / launcher |
| May 10-12 | UTL v8 ManifestWriter columns + `record_*` hooks ship.                                                                                  | UTL / Tab 2      |
| May 10-12 | Phase 4 workspace-wide consumer sweep (parallel agents per repo).                                                                       | Multi-tab        |
| May 11-12 | v8 migration script + bundled into gcs_migration Phase 2 (single walk: pipeline_mode + asset_group rekey + drift + v8 + rescan).        | Tab 3            |
| May 12    | Bounce-sweep #1 — drain stale MTDS VMs + tarball refresh (`create-code-tarballs.sh --all`).                                             | Tab 2 / launcher |
| May 13-15 | gcs_migration Phase 3 (bundled walk) — multi-VM fleet, per-asset-group QA gate (Phase 3.6 + Phase 6 phantom cleanup + rescan auto-fix). | Operator-gated   |
| May 15    | Cross-asset rescan class-C triage review (operator decides ambiguous rows).                                                             | Operator         |
| May 16    | Bounce-sweep #2 — MTDS backfill launches with full Phase 4 wire-in. Parallel by asset_group / zone where dependency-free.               | Tab 2 / launcher |
| May 16-20 | Backfill runs to actual completion + sample-parquet inspection per CLAUDE.md "Plans Run To Actual Completion."                          | MTDS / Tab 2     |
| May 20-21 | MDPS reprocess + features-\* compute (downstream of MTDS — features-consolidation must be shipped by May 16 per Tab 2 deferred list).   | Tab 2            |
| May 21-22 | Paper-trade smoke + batch-vs-live recon (master plan F17 + F18) + writegate Phase 5 ratchet POST-baseline + ratchet lock-in.            | Cross-tab        |
| May 23    | Live cutover. Manifest is at v8-final, every column populated, every drift axis cleared, every plan item flipped `[x]`.                 | Operator         |

### Slack analysis (where the schedule can absorb slip)

- **5-day MTDS backfill estimate** (May 16-20) is the largest slack consumer. Sports = 12h / cefi = 8h / tradfi = 6h /
  defi = 4h / prediction = 2h per gcs Phase 3 estimate; if those translate to backfill wall-clock it's ~32h sequential
  or <8h parallel-by-zone. Real backfill cost depends on Databento/Tardis quota + per-shard parallelism per Tab 2
  ParallelPerSymbolRunner.
- **Phase 3 bundled walk** (May 13-15) is the next-largest. Calibrated by C1 pre-audit. If C1 returns >36h estimate,
  drop drift axes 4 + 5 from the bundle (defer to post-cutover) — they're additive cleanup, not correctness-blocking.
- **Phase 4 consumer sweep** is parallelizable across repos — bottleneck is review + QG. Can run 2026-05-10 in parallel
  with UAC/UTL Stage 1 (both write to different files; collision-free).
- **Slice b 4-value enum** is tiny if operator ratifies on this Q-doc — collapses to a single UAC commit + a unit test
  that asserts the closed set. <2h work; not on critical path if ratified May 9.

### Critical-path risk: features consolidation

- Features consolidation (5-6 repos → 1 features-service per `features_repo_consolidation_2026_05_08`) is a 3-5 day
  pre-req per Tab 2 architecture memory entry. **It MUST land by May 16** so MDPS reprocess + features compute (May
  20-21) runs against the consolidated repo. If consolidation slips past May 16, MDPS + features blocked — paper-trade
  smoke + batch-vs-live recon also blocked.
- This is a separate critical path from the manifest freeze gate but inherits the same May 23 constraint. Recommend a
  parallel work-split tab focused on features consolidation completion this week.

## Successor plan

Decisions ratified 2026-05-09 (E2=(a) + A1=NO + maximalist sequence). Spawn one-shot **manifest-schema-final-gate plan**
at `plans/active/manifest_schema_final_gate_2026_05_09.md` that codifies:

1. Closed-set ratification: v8 = v7 + 3 columns above, `ServiceEmissionStateEnum` = 4 proposed values, no further schema
   additions until post-cutover (post-May-23).
2. Bundled Phase 3 walk: `pipeline_mode=` + `category=`→`asset_group=` + 5 drift axes + v8 NULL backfill + cross-asset
   rescan auto-fixes in ONE parquet walk, May 13-15.
3. Workspace-wide Phase 4 consumer sweep across UAC / UTL / MTDS / MDPS / features-\* / instruments-service /
   deployment-api / e2e-testing — parallel-agent fan-out, P0 by May 12.
4. Two-stage MTDS bounce-sweep (drain May 12, full launch May 16) with E3 7-item launcher checklist.
5. Banner every `plans/active/*.md` whose work touches MTDS / MDPS / features / manifest with
   `🟡 IN-FLIGHT REFACTOR — manifest v8 FINAL by 2026-05-23; bundled Phase 3 walk May 13-15; MTDS bounce-sweep May 16-20; no schema additions until post-cutover`
   per CLAUDE.md "Cross-Plan Coordination Banners" rule.
6. Cross-plan coordination with `features_repo_consolidation_2026_05_08` — features consolidation MUST land by May 16.
   Banner that plan with the same maximalist deadline.
7. Hard-stop: any new schema column proposal between 2026-05-09 and 2026-05-23 is REJECTED — defer to post-cutover. The
   "best manifest" by May 23 is v8 with the closed set above; nothing gets added mid-flight.

Remaining open (need operator):

- A1 sub-decision → ratify slice b 4-value `ServiceEmissionStateEnum` on this Q-doc (recommend (ii) ratify-now)?
- A3 → audit any other UAC enums about to gain values (recommend a 2-hour grep sweep this week to surface + freeze them
  too).
- B2 sub-question → confirm the workspace repo list for Phase 4 sweep — full set vs MTDS-only.
- C4 → who ships the cross-asset rescan launcher script (Harsh's tab queue or fresh sub-agent).
- D1 → quota burn estimate for double bounce-sweep (May 12 drain + May 16 launch) vs single sweep — operator data only.
- D2 / D3 → confirm manifest concurrency principle is wired in MTDS adapters (Tab 2 verification).

- **2026-05-09 — RATIFIED ALL: maximalist v8-final + 7-item launcher checklist.** Operator direction (verbatim): _"yeah
  do all this v8 should not be deferred should be done"_ + ratified the E3 7-item closed-set pre-launch checklist
  verbatim (UTL `manifest_writer.py` `pipeline_mode=` kwarg shipped + default `None` until Phase 4 closes;
  per-MTDS-adapter explicit `pipeline_mode=PipelineMode.BATCH_<source>`; manifest concurrency principle wired into every
  MTDS launcher; per-VM shard isolation envvars; event-stream STARTED+progress+STOPPED protocol; tarball refresh
  post-Phase-4; watchdog dict prefix registration). Implies: A1=NO (no v7 lock), A1-sub=ratify-now (slice b 4-value
  enum + read protocol = ratified), B2=workspace-wide Phase 4 sweep, B3=rescan bundled into Phase 3 walk, E1=v8 final,
  E3=ratified-as-listed. Q-doc status flipped → `ratified-spawned-successor`. Successor:
  `plans/active/manifest_schema_final_gate_2026_05_09.md`.
