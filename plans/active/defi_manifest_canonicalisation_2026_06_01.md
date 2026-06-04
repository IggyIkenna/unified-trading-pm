---
title: "MASTER: canonical-SSOT for data+manifest (cross-plan coordinator) + DeFi manifest canonicalisation"
created: 2026-06-01
author: ikenna
parent_epic: epics/mtds_mdps_master.md
assigned_vm: vm-defi
status: active
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 9
estimate_calibrated_ai_days: 3.6
locked_by: live-defi-rollout
locked_since: 2026-05-21
source:
  - plans/audit/results/defi_master_audit_2026_06_01.md (the audit that surfaced all of this)
  - plans/audit/instructions/defi_master_audit_instructions.md (items o–y)
---

# MASTER: Canonical-SSOT for Data + Manifest (cross-plan coordinator) + DeFi Manifest Canonicalisation

> **This file plays two roles** (operator 2026-06-01): (1) the **MASTER coordinator** for the whole "single canonical
> SSOT — no fallback, no dual" programme (the `## MASTER` section sequences every sub-plan); (2) the **DeFi L3
> executor** (the `## A`–`## G` sections ARE the DeFi single-walk). An agent drives the MASTER section + delegates the
> sub-plans (parallelisable where marked) to sub-agents.

## MASTER — cross-plan execution order → single canonical SSOT (no fallback, no dual)

> **🔴 CROSS-AG FOUNDATION GATE (filed 2026-06-04, slot-3) — blocks EVERY AG's MTDS `--apply`.** instruments-service is
> the foundation; before any AG runs its MarketTick-data migration `--apply`, the **proper instrument catalogue** must
> be GREEN: `plans/active/proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md` (P0, vm-cross-cutting). It builds
> the time-independent known-instrument universe by rolling up the maintained per-date
> `instrument_availability/by_date/` definitions (the v2 enumerator's `catalog.parquet` had **no producer** → a static
> snapshot that goes stale two ways). Every AG lane (cefi/defi/tradfi/sports-fixtures/prediction) depends on it for a
> correct could-exist universe (`expected_unattempted`, coverage denominators, instrument-existence guards). **Dry-runs
> (migrator + manifest-rebuild) are NOT gated** by it — only the irreversible `--apply`. Depends on
> `instruments_manifest_canonicalisation` (IS indices canonical first). Per-AG slices drive via each AG master; the
> shared roll-up + completeness gate are vm-cross-cutting.

> **✅ CROSS-AG DEAD-BUCKET REGRESSION FINDING — RESOLVED 2026-06-02 (was: escalated from the sports lane — affected
> EVERY AG before its legacy delete)**: two shared surfaces still resolve the NO-ENV (legacy) bucket form, which BREAKS
> once any AG's legacy bucket is deleted: (1) **UAC `gcs_paths.bucket_name(asset_group, …)` returns the NO-ENV form**
> (e.g. `market-data-tick-sports-{PID}` / `instruments-store-{ag}-{PID}`), pinned by
> `unified-api-contracts/tests/unit/test_gcs_paths_facade.py` — it CONTRADICTS the UTL SSOT `resolve_bucket_name` which
> returns `-prd-`; the UI mirrors it (`unified-trading-system-ui/context/api-contracts/…/sports/mapping_resolver.py`).
> (2) **UTL `instrument_lifecycle_loader.py` `_BUCKETS` / `_INSTRUMENTS_STORE_BUCKETS`** hardcode the no-env template
> for ALL AGs (cefi/defi/tradfi/sports/prediction). Sports-lane already fixed its OWN readers (`sports_fixtures.py`
> keystone truthset reader → `resolve_bucket_name`, e2e scripts → `-prd-`; UTL@b3b70c13 + e2e@b418afc). **These two
> SHARED surfaces must be canonicalised once, cross-AG, BEFORE the first legacy delete** — either route them through
> `resolve_bucket_name` or make the facade env-tiered, + update the pinning tests so QG regression-catches. Each AG's
> dead-bucket sweep (in its `*_manifest_canonicalisation` plan) depends on this. Owner: master coordinator / UAC+UTL
> owner (NOT a per-AG-lane unilateral change — it would desync the other lanes). SSOT for the sports slice:
> `sports_manifest_canonicalisation_2026_06_01.md` § "Dead-bucket regression gate".
>
> **✅ RESOLVED 2026-06-02 (dedicated cross-AG session)**: both shared surfaces are now canonical — (1) UAC
> `gcs_paths.bucket_name(...)` defaults `env="prd"` (env-tiered `-prd-`, no longer no-env); (2) UTL
> `instrument_lifecycle_loader` routes through `resolve_bucket_name` (UTL@fd91ee74 Task 3,
> `_BUCKETS`/`_INSTRUMENTS_STORE_BUCKETS` hardcodes removed). The remaining cross-AG no-env / explicit-`project_id`
> readers were swept the same session: UTL `instruments_catalog_reader`@4c1c9a68, instruments-service
> `catalogue_builder`@f693e34e (also removed a dead `try/except ImportError` inline no-env fallback), deployment-service
> `manifest_reader` + `sports_trigger_scheduler`@9886911. **QG ratchet STEP 5.93**
> `check_no_explicit_project_id_bucket.py` (PM@60a27debe) regression-guards the whole class. (IS `sports_dependency` +
> features `gcs_paths` were already canonical via the sports lane.)

**Goal (operator)**: full canonical DATA + MANIFEST — historically AND for all backfill + crons + code — one SSOT, no
legacy, no fallback read path, no dual-write. **Invariant**: a legacy bucket is deleted ONLY after canonical provably
holds ALL its data + an authoritative **v9** manifest. **One single-walk per `_index`** (HARD RULE) — every per-bucket
transform (env-split, `asset_group=`, `pipeline_mode=` partition, v9, underscore data_type, flat venue+chain, typed
empty-reason, `source` column) BUNDLES into that bucket's single walk; no plan opens a second walk on the same `_index`.

### Sub-plan registry (what this master wraps)

| Plan                                                        | Role / layer                                                                                                                                                                             | Status                           | Parallel?                                                                                                      |
| ----------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01` | L1 code-fix ✅ · L2 drain+cron-pause · L6 decommission                                                                                                                                   | code shipped; decommission gated | after L3 per-AG                                                                                                |
| THIS plan §A–G                                              | L1 DeFi writer code · **L3 DeFi single-walk (§C)** · L5 DeFi backfill                                                                                                                    | C open (C0 RUN-ON-VM)            | DeFi-only, serial within DeFi                                                                                  |
| `data_source_provenance_all_asset_groups_2026_06_01`        | L1 write-path `source=` · rides each L3 walk                                                                                                                                             | open (tradfi done)               | parallel per-AG (NOT tradfi)                                                                                   |
| `pipeline_mode_implementation_2026_05_28`                   | L1 `pipeline_mode` column                                                                                                                                                                | ✅ DONE                          | —                                                                                                              |
| `pipeline_mode_partition_migration_2026_06_01`              | L3 RIDER: on-disk `pipeline_mode=` partition                                                                                                                                             | open P2                          | **rides each AG's L3 walk**                                                                                    |
| `tradfi_massive_dual_source_2026_05_28`                     | tradfi L1 source write-path + Massive ingest (NOT the L3 walk)                                                                                                                           | mostly ✅; -031 absorbed by ↓    | done — see CONFLICT-2                                                                                          |
| `tradfi_manifest_canonicalisation_2026_06_01`               | **L3 tradfi single-walk** (v9 + pipeline_mode partition + source re-consol)                                                                                                              | open P0                          | parallel per-AG                                                                                                |
| `sports_manifest_canonicalisation_2026_06_01`               | **L3 sports single-walk** (v9 + partition + fixture-dependent typed reasons + source path→column)                                                                                        | open P0                          | parallel per-AG                                                                                                |
| `instruments_manifest_canonicalisation_2026_06_01`          | **L3 per-SERVICE** (instruments I/O input — all-AG reference/instrument indices, audit-first)                                                                                            | open P0                          | parallel per-service                                                                                           |
| `proper_instrument_catalogue_lifecycle_rollup_2026_06_04`   | **L3.5 FOUNDATION** — lifecycle catalogue roll-up from per-date `by_date/` defns (all-AG + sports fixtures); the could-exist-universe SSOT feeding `expected_unattempted` + denominators | open P0                          | **GATES every AG's MTDS `--apply`** (dry-runs NOT gated; depends on `instruments_manifest_canonicalisation` ↑) |
| `downstream_services_manifest_canonicalisation_2026_06_01`  | **L3 per-SERVICE** (MDPS/features/strategy/execution — audit-first, low-data quick walk)                                                                                                 | open P1                          | parallel per-service                                                                                           |
| `canonical_form_cross_service_audit_checklist` (audit SSOT) | **L7 AUDIT SSOT**: CF-1…CF-12 union + (service×CF) coverage matrix — re-run proves canonical                                                                                             | shipped                          | —                                                                                                              |
| `manifest_reader_fail_fast_on_stale_fallback_2026_05_28`    | **L4/L7 "no fallback"**: reader fail-fast default + liveness                                                                                                                             | step-1 ✅; follow-up open        | parallel (independent)                                                                                         |
| `aws_manifest_consolidator_scope_2026_05_21`                | L4 AWS canonical consolidator                                                                                                                                                            | P1.10 `tofu apply` open (HUMAN)  | parallel (AWS infra)                                                                                           |
| `manifest_consolidator_liveness_health_2026_06_01`          | L4 GCP consolidator liveness                                                                                                                                                             | (not on this branch)             | parallel — CONFLICT-3                                                                                          |
| `solana_defi_legacy_migration_2026_05_27`                   | **DeFi-specific** Solana legacy→canonical (Kamino/Solend/Orca/Raydium) — SAME dedicated DeFi buckets §C rewrites                                                                         | open P1                          | DeFi-only — serialise with §C                                                                                  |

> **This master owns the ENTIRE DeFi vertical (slot 2, five-slot asset-group split, operator 2026-06-03).** Beyond the
> cross-AG canonicalisation sub-plans above, slot-2 / this master orchestrates ALL DeFi work across **IS
> (instruments-service) · MTDS · MDPS · features · all downstream (strategy/execution) · all buckets/data/manifest · the
> data-status UI** — the DeFi slice of every per-service plan rides §H, and the DeFi-specific plans + issues below are
> wrapped here. Orphaned DeFi cross-references attach to THIS plan. (`master_to_live_defi_2026_05_23.md` is the
> higher-level live-cutover master — this canonicalisation plan is its data-layer child, NOT subordinated to it.)

### DeFi-scope wrapped issues (this master owns / closes their DeFi slice)

| Issue                                                           | What it is                                                                      | How this master resolves it                                       |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `issues/defi_code_codex_drift_2026_05_27`                       | DeFi code↔codex drift audit (D1–D13: data-types, venues, banned providers)      | §A writer + §F docs/SSOT close the code/codex drift items         |
| `issues/features_service_defi_data_loading_blockers_2026_05_29` | features-service DeFi e2e blocked on data-layer (dex_swaps→dex_pool_swaps etc.) | §C0–C2 canonical-naming walk + §D features propagation resolve it |

### Layered order (gates top-down; asset_groups parallelise within a layer)

- **L0 INFRA UNBLOCK** — ✅ RESOLVED 2026-06-01 (slot 7). Loud-fail SHA-pin path shipped (deployment-service@a0fcba7 +
  `MTDS_TARBALL_SHA` @58ee0a9): a `RUN ON A VM` launch now runs the exact pinned commit or fails loudly (never silent
  stale). Issue archived → `plans/archive/issues/pinned_tarball_prune_breaks_vm_deploys_2026_06_01.md`. RUN-ON-VM todos
  (C0/C6/G1; bucket_ssot Phase 2/4) unblocked.
  - [ ] [VERIFY] P2. On first `C0 — RUN ON A VM`, confirm the loud-fail path in practice (VM ran the intended sha; a
        deliberately-wrong pin hard-fails exit 1). Residual: `create-code-tarballs.sh` still aborts on a dirty tree —
        build from a clean slot worktree.
- **L1 CODE SSOT (write path)** — bucket_ssot Phase 1 ✅ + QG grep-guard + UTL dead-code · this plan §A (A2a/A2b/A4/A5)
  · `data_source_provenance` §Phased `source=` threading · `pipeline_mode_implementation` ✅.
- **L2 STOP LEGACY-SIDE** — bucket_ssot Phase 3 drain ✅ · Phase 7 pause 10 `*-legacy-cron` + TF removal.
- **L3 HISTORICAL DATA+MANIFEST CANONICALISATION — THE GATE** (one bundled single-walk per AG; riders =
  `data_source_provenance` source-col + `pipeline_mode_partition` partition + v9):
  - **defi** (16,206 legacy-only cells) → this plan §C (`C0`→`C12`, then `B0`). GATES DeFi backfill.
  - **prediction** (2,039 legacy-only, only 783 overlap → LEAST complete) → ✅ FILED
    `prediction_manifest_canonicalisation_2026_06_01.md` (owner `vm-prediction`).
  - **cefi** (838 recent legacy-only cells) → ✅ FILED `cefi_manifest_canonicalisation_2026_06_01.md` (owner `vm-cefi`).
  - **tradfi** (4 legacy-only → DATA ~complete, but canonical FORM owed: live `_index` v8 + no partition) → ✅ FILED
    `tradfi_manifest_canonicalisation_2026_06_01.md` (owner `vm-tradfi`; absorbs `tradfi_massive` -031 re-consolidation
    into ONE walk per CONFLICT-2).
  - **sports** (0 legacy-only → DATA complete, but canonical FORM + fixture-dependent typed honest-absence owed) → ✅
    FILED `sports_manifest_canonicalisation_2026_06_01.md` (owner `vm-sports`; NOT pure verify-only — v9 + partition +
    typed reasons + source path→column).
  - **PER-SERVICE axis (the data pipeline is `instruments → MTDS → MDPS → features → strategy → execution` — every
    service's `_index` needs canonical form, not just MTDS)**: the per-AG plans above cover the **MTDS** row; the other
    services are covered by ✅ FILED `instruments_manifest_canonicalisation_2026_06_01.md` (I/O input, all-AG reference
    indices, `vm-cross-cutting`) + ✅ FILED `downstream_services_manifest_canonicalisation_2026_06_01.md`
    (MDPS/features/strategy/execution — audit-first, low-data, `vm-ml`). Both are **audit-first** against the CF-1…CF-12
    SSOT and bundle every transform into one walk per bucket (MDPS rides the AG tick walk — no second `_index` walk).
- **L4 CONSOLIDATOR SSOT** — `aws_manifest_consolidator_scope` P1.10 · `manifest_consolidator_liveness_health` ·
  `manifest_reader_fail_fast` follow-up (fail-fast default) · keep env-tiered crons.
- **L5 BACKFILL/RELAUNCH** — bucket_ssot Phase 4 (writer relaunch) · this plan C6/D1/E1/G1 — gated C-GREEN.
- **L6 DECOMMISSION** — bucket_ssot Phase 6 verify → Phase 7 delete legacy buckets (GCP+AWS).
- **L7 GUARDRAILS** — QG grep-guard · `batch_live_symmetry` audit check ✅ · codex docs (this plan F1–F4 +
  `data_source_provenance` QG 5.64 + bucket_ssot codex) · **cross-service audit SSOT
  `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md`** (CF-1…CF-12 union + (service×CF) coverage
  matrix; every per-service + per-AG audit-instruction file carries a "Canonical-form coverage" section citing it, so
  re-running the audits proves the whole pipeline is canonical — a CF column with no owning audit is review-blocking).

### CONFLICTS found (cross-plan check 2026-06-01 — RESOLVE before parallel dispatch)

- **CONFLICT-1 — `pipeline_mode_partition_migration` must NOT open its own walks.** It adds the `pipeline_mode=` on-disk
  partition to cefi/tradfi/sports/prediction; per single-walk it BUNDLES into each AG's L3 walk. It is a RIDER, not an
  independent plan; its P2 todo is satisfied by the L3 owner. (DeFi partition already in this plan's §C target-form.)
- **CONFLICT-2 — tradfi v9 + partition NOT actually landed → RESOLVED 2026-06-01 by new L3 owner.** `tradfi_massive`
  reports source-col + v8→v9 done, but its "Manifest re-consolidation" was `BLOCKED-DEPENDENCY deferred` AND the live
  canonical tradfi `_index` reads **v8**. So tradfi is NOT L3-green: v9 re-consolidation + the `pipeline_mode=`
  partition still owe a walk. **Owner = `tradfi_manifest_canonicalisation_2026_06_01.md`** (the v9 + partition +
  venue/data_type verify + `available_at` bundled walk, which **absorbs `tradfi_massive` Task -031** so source
  re-consolidation rides the SAME walk — never two). `tradfi_massive` keeps only the `source` write-path + Massive
  ingest. Verify with a fresh `_index` `schema_version` read before declaring tradfi decommission-ready.
- **CONFLICT-3 — duplicate consolidator-liveness ownership.** `manifest_reader_fail_fast` §Follow-up and
  `manifest_consolidator_liveness_health` both define watchdog + alerting + fail-fast-default. ONE owns the watchdog
  (recommend `manifest_consolidator_liveness_health`); `manifest_reader_fail_fast` keeps only the UTL reader-default
  flip.
- **CONFLICT-4 — `data_source_provenance` must SKIP tradfi.** tradfi's `source` column already shipped via
  `tradfi_massive`; provenance must not re-walk tradfi. Scope it to cefi/defi/sports/prediction.

### Agent assignment (2026-06-01; **FIVE-slot split — one slot per asset_group, full asset-group split, operator 2026-06-03**; the SUM completes EVERYTHING, no defers, no fallbacks)

> **Reassignment 2026-06-03 (operator) — clean asset-group split, ONE slot per asset_group (5 slots).** Each of the five
> asset_groups is a **full vertical** owned by a **dedicated slot** that owns **everything for that AG across every
> service** — IS (instruments-store reference) + MTDS (market-data-tick) + MDPS + features + strategy/execution + the
> deployment UI/menu/bucket/data/manifest surfaces — not just the MTDS walk. Each AG's
> `*_manifest_canonicalisation_2026_06_01.md` is the **MASTER orchestrator plan for that whole vertical** (this defi
> plan is the defi analogue): every other plan/issue for that AG + every orphaned cross-reference attaches to its AG
> master. The two per-service plans (`instruments`, `downstream`) are **sliced across all five AG slots** — each AG owns
> its own slice; `vm-cross-cutting` / `vm-ml` hold only the non-AG glue (cross-AG reference indices, shared reader
> form). A slot does NOT edit another AG slot's surfaces — ping instead.
>
> | Slot | AG         | vm            | AG master plan                                    |
> | ---- | ---------- | ------------- | ------------------------------------------------- |
> | 2    | DeFi       | vm-defi       | `defi_manifest_canonicalisation_2026_06_01`       |
> | 3    | CeFi       | vm-cefi       | `cefi_manifest_canonicalisation_2026_06_01`       |
> | 4    | Sports     | vm-sports     | `sports_manifest_canonicalisation_2026_06_01`     |
> | 5    | Prediction | vm-prediction | `prediction_manifest_canonicalisation_2026_06_01` |
> | 6    | TradFi     | vm-tradfi     | `tradfi_manifest_canonicalisation_2026_06_01`     |
>
> **Slot 2 = the ENTIRE DeFi vertical (this plan).** Owns `defi_manifest_canonicalisation_2026_06_01.md` end-to-end: the
> MASTER coordinator role + §A (defi writers) + §B (defi consolidation/data-status) + **§C the DeFi single-walk**
> (C0–C12)
>
> - §D (defi features) + §E (cefi-perp hedge leg the defi hybrid needs) + §F (defi docs) + §G (Solana basis MVP) + **§H
>   the DeFi slices of the instruments + downstream per-service plans**. The defi C0 walk carries the defi riders
>   (source col + pipeline_mode partition + v9 + category→asset_group) per § Rider closure.
>
> **Slot 3 = the ENTIRE CeFi vertical.** Owns `cefi_manifest_canonicalisation_2026_06_01.md` as the **CeFi MASTER
> orchestrator** (cefi single-walk: 838-cell gap-fill + v9 + partition + source) + the cefi slices of IS / MDPS /
> features / strategy-execution / downstream + the cefi deployment-UI/bucket surfaces + every cefi plan/issue
> cross-linked in.
>
> **Slot 4 = the ENTIRE sports vertical.** Owns `sports_manifest_canonicalisation_2026_06_01.md` as the **sports MASTER
> orchestrator**, and through it everything sports across all services: **both sports surfaces** —
> `market-data-tick-sports` (MTDS) **and** `instruments-store-sports` (IS reference, 2.68M rows + the 316-cell
> legacy→prd data-loss-gated migration) — plus the sports rows/tests in MDPS / features / execution, the sports
> deployment-UI/menu/bucket surfaces, the sports single-walk (v9 + partition + fixture/season/transfer-window/genesis
> typed reasons + source path→column), and its riders. **Every other sports plan/issue + every orphaned sports
> cross-reference is cross-linked INTO the sports master plan** (`sports_retired_data_types_code_cleanup`,
> `epics/sports_master`, and the sports slices of the phase-3 backfill / provenance / bucket-SSOT plans).
>
> **Slot 5 = the ENTIRE Prediction vertical.** Owns `prediction_manifest_canonicalisation_2026_06_01.md` as the
> **Prediction MASTER orchestrator** (prediction single-walk: legacy→canonical copy + v9 + partition + source = API) +
> the prediction slices of IS / MDPS / features / strategy-execution / downstream + the prediction deployment-UI/bucket
> surfaces + every prediction plan/issue (Polymarket/Kalshi work, the Kalshi classifier-None divergence) cross-linked
> in.
>
> **Slot 6 = the ENTIRE TradFi vertical.** Owns `tradfi_manifest_canonicalisation_2026_06_01.md` as the **TradFi MASTER
> orchestrator** (tradfi single-walk: v9 + partition + source re-consol; **absorbs `tradfi_massive` -031**) + the tradfi
> slices of IS / MDPS / features / strategy-execution / downstream + the tradfi deployment-UI/bucket surfaces + every
> tradfi plan/issue (`tradfi_massive_dual_source_2026_05_28`, the tradfi phase-3 backfill slice, the VIX/Massive
> continuity work) cross-linked in.
>
> **The two per-service plans are sliced, not slot-owned.** `instruments_manifest_canonicalisation_2026_06_01.md` and
> `downstream_services_manifest_canonicalisation_2026_06_01.md` each carry five AG slices — defi→slot 2 (§H here),
> cefi→slot 3, sports→slot 4, prediction→slot 5, tradfi→slot 6 — plus the cross-AG glue (`vm-cross-cutting` / `vm-ml`).
> No slot edits another AG's slice.
>
> Each AG-slot plan's single bundled walk INCLUDES its rider work — so completing them also closes
> `data_source_provenance_all_asset_groups_2026_06_01` (cefi/sports/prediction source; tradfi skipped per CONFLICT-4) +
> `pipeline_mode_partition_migration_2026_06_01` (cefi/tradfi/sports/prediction/instruments) for those AGs. **No second
> walk on any `_index`** (single-walk discipline). **NO DEFERS, NO FALLBACKS** (CLAUDE.md "Data Pipeline Correctness Is
> The Heartbeat" + "Plans Run To Actual Completion"): the only legitimate non-completion is the closed operator-gated
> set (`BLOCKED-CREDENTIALS` / `BLOCKED-OPERATOR-DECISION` / `BLOCKED-UPSTREAM-OUTAGE` / `BLOCKED-PLAYWRIGHT`).
> **Combined acceptance**: every (service × AG × CF-1…CF-12) cell GREEN per the audit SSOT
> `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md` → hands C-GREEN to `bucket_name_ssot…` L6.
> Every migration script obeys the § Migration-script performance contract (parallel/shardable/observable).
>
> **Scope is a PRIOR, not a ceiling (HARD — codified 2026-06-01)**: each plan's headline cell-count / "~complete" /
> "verify-only" is a coarse pre-audit prior. The audit-first P0 reads DATA-STATE; whatever extra canonical-form debt it
> surfaces is **fixed FULLY and AUTONOMOUSLY in the same walk** — never descoped to the headline, never deferred, never
> `BLOCKED-OPERATOR-DECISION` (a data-state gap is not a design fork). **Reference incident**: cefi, framed "~complete /
> 838-cell gap", was found 100% v8 + no `source`/`asset_group` column + blank `pipeline_mode` = a full
> re-canonicalisation — fixed in-walk, not deferred. SSOT: audit checklist § "Audit scope is a PRIOR, not a ceiling".

### Parallelisation guidance (for the dispatching agent)

- **Strictly serial-gating**: L0 → (L1,L2) → L3-per-AG → L5-per-AG → L6. L6 (delete) waits for ALL AGs L3-green.
- **Parallel-safe NOW** (independent of L3 walks): `manifest_reader_fail_fast` follow-up ·
  `aws_manifest_consolidator_scope` P1.10 · `manifest_consolidator_liveness_health` · bucket_ssot QG-guard + UTL
  dead-code · this plan §A writer fixes · `data_source_provenance` L1 threading (cefi/defi/sports/pred).
- **Parallel-per-AG at L3** (one sub-agent per asset_group, each owns its single bundled walk): defi (this plan §C) ·
  prediction (new plan) · cefi (new gap-fill) · tradfi (new canonicalisation plan per CONFLICT-2) · sports (new
  canonicalisation plan). NEVER two walks on one `_index`.
- **L3 owners (all asset_groups now covered)**: defi=this plan §C ·
  prediction=`prediction_manifest_canonicalisation_2026_06_01` · cefi=`cefi_manifest_canonicalisation_2026_06_01` ·
  tradfi=`tradfi_manifest_canonicalisation_2026_06_01` (CONFLICT-2; absorbs `tradfi_massive` -031) ·
  sports=`sports_manifest_canonicalisation_2026_06_01` (v9 + partition + fixture-dependent typed reasons). **L6
  decommission** (owner `bucket_name_ssot_legacy_dual_write_remediation` Phase 7) deletes each legacy bucket ONLY after
  its AG's L3 plan reports C-GREEN (legacy-only CELLS = 0 + canonical v9).

> **🟡 CROSS-PLAN COORDINATION — DeFi `_index` shared with
> `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` (2026-06-01)**: the C0 single-walk on
> `market-data-tick-defi-prd-…` (`migrate_defi_full_v9_canonical.py`: read+rewrite to `asset_group=defi` +
> `pipeline_mode=` partition + v9 + `source` + canonical `_V{N}` venue + `available_at`; launcher-wired
> `launch-canonical-migration-vm.sh defi`) mutates the **same `_index`** that the bucket-remediation plan's
> `--manifest-only` seed writes legacy→canonical rows into. Single-walk discipline (HARD RULE) forbids two concurrent
> whole-corpus walks on that `_index`. **Ordering (HARD)**: the bucket plan's DeFi manifest seed runs **BEFORE** this
> plan's `C0` single-walk — otherwise the seed re-injects un-canonicalised legacy rows (old venue strings, v4–v8,
> phantom grid) _after_ C0 cleans them. As of 2026-06-01 **neither DeFi walk has launched** (bucket "Manifest seed" P0 +
> this plan's "C0 — RUN ON A VM" P0 both open) — no live race yet; do NOT launch C0 without confirming the bucket
> DeFi-`_index` seed is not mid-run (and vice-versa). `data_source_provenance_all_asset_groups_2026_06_01.md`
> `source`-column backfill must ride **this plan's C0 single-walk** — it must NOT open a third walk on the DeFi
> `_index`. Coordination owner: epic `mtds_mdps_master`. Banner-remove when the DeFi `_index` is seeded (bucket) +
> canonical (this plan C-GREEN).

> **Why this exists**: the 2026-06-01 DeFi coverage audit took many passes because the data is **not in canonical form**
> — scattered buckets, hyphen/underscore + VENUE-CHAIN + blank-chain duplicates, a phantom grid, a v4–v8 schema spread,
> mislabeled empty reasons, and (the keystone) **no materialised `expected_unattempted` state**. The hard-to-find-ness
> IS the bug. This plan makes the **data, manifest, data-status tab/UI, owner code, and docs** canonical so the next
> audit is one pass. Single-walk discipline applies — the multi-bucket sweep MUST be one bundled walk, not N ad-hoc
> walks.

## Sequencing — canonical migration is a GATE before ANY backfill (HARD RULE, operator 2026-06-01)

> Operator: "pipeline mode needs to be in legacy which needs to be migrated — this is why we keep having mess before
> more backfills. Everything must be fully migrated into the right form (env splits etc) so that manifest AND data AND
> data-status are all in their right format."

**No backfill, no B0-run, no `expected_unattempted` generation until the in-scope buckets are in canonical form.**
Backfilling into the legacy layout (no `pipeline_mode`, `category=` not `asset_group=`, no env split, v4–v8, hyphen/
VENUE-CHAIN names) just manufactures more non-canonical data to re-migrate. So **C (migration) is a foundation gate**;
C6 (Pyth backfill) / D1 (features backfill) / E1 (cefi fetch) / B0 (run the chain) are **review-blocked until C is GREEN
for the affected bucket.** Composes with single-walk discipline + the pre-migration-drain HARD RULE (stop VMs + snapshot
before cutover).

### Canonical target form — what "right format" means (every in-scope object + manifest row)

| Dimension        | Legacy (now)                            | Canonical (target)                                                                            |
| ---------------- | --------------------------------------- | --------------------------------------------------------------------------------------------- |
| Bucket env split | `oracle-prices-{project}` (no env)      | `oracle-prices-{env}-{project}` (`-prd`/`-test`) — or fold into `market-data-tick-defi-{env}` |
| Asset-group key  | `category=defi`                         | `asset_group=defi`                                                                            |
| Pipeline mode    | absent in path                          | `pipeline_mode=` hive partition (value `batch` or `live`)                                     |
| Schema version   | v4–v8 spread                            | v9                                                                                            |
| data_type name   | hyphen / `staking_yields`               | underscore canonical (`lst_rates`, `dex_pools`, …)                                            |
| Venue / chain    | `UNISWAPV3-ETHEREUM`, blank chain       | flat `venue` + populated `chain`                                                              |
| Empty reason     | blank / `SOURCE_RETURNED_ZERO` mislabel | typed (`EXPECTED_PRE_GENESIS_CHAIN`, …)                                                       |
| 4th state        | absent                                  | `expected_unattempted` materialised by the run (B0)                                           |

All of the above land in **one bundled single-walk** per bucket (C2–C5 + C7 + C9 + env-split), then the consolidated
`_index` + data-status reflect the canonical form, then backfills run into the correct structure.

> **`category=`→`asset_group=` spans all three surfaces, all five asset_groups (HARD — operator 2026-06-01)**: (1)
> **CODE** (writers/CLI/env emit `asset_group=`, not `category=`) is **already shipped** workspace-wide via the archived
> `venue_axis_asset_group_vocabulary_2026_04_25` plan (Waves A–E) — new writes are canonical, so the remaining work is
> historical only; (2) **DATA** (object PATH key `category=`→`asset_group=`) + (3) **MANIFEST** (`_index` ROW
> `category=`→`asset_group=`) are migrated by **each asset_group's L3 single-walk** — defi §C (C0 tool +C9 object-path
> item), cefi/prediction/tradfi/sports C0 each state the path+row relabel explicitly. No asset_group leaves it implicit;
> the relabel rides the SAME bundled walk (never a separate `category` walk).

## Architecture principle (the governing contract)

**Annotate honestly ONCE at write/consolidation-time (manifest, via the `expected_coverage()` oracle); READ everywhere
else. Never re-derive the expected set in a consumer.**

- **Manifest = canonical honest 4-state ledger.** Every IS∩UAC-expected cell carries one of: `captured` /
  `empty_confirmed[typed reason]` / `attempted_failed` / **`expected_unattempted`** (IS-listed + post-genesis +
  post-launch + in source-coverage, but no data yet). The typed empty reason IS the IS/UAC annotation.
- **Data-status summary + drilldown = VIEWS**: group/aggregate/display by READING `capture_status`; never re-derive.
  Operator filter-chips narrow at request time (never expand). The drilldown `_aggregate_counts` is generic → one fix
  serves IS/MTDS/MDPS/features.
- **Strategy/features preflight = read the SAME 4-state.** No re-deriving genesis/launch/IS rules per consumer.
- **CORRECTION 2026-06-01 (system-first save)**: `expected_unattempted` is **already canonical + the propagation chain
  is already shipped** — archived plan `expected_unattempted_propagation_chain_2026_05_12.md` (Phase 0 UAC reasons
  `EXPECTED_UPSTREAM_EMPTY`/`EXPECTED_OUTSIDE_PROCESSING_SCOPE` ✅; Phase 1 MTDS instruments-service pre-flight →
  `record_expected_unattempted` ✅; Phase 2 MDPS ✅). It is **writer/orchestrator-driven** (MTDS pre-flight reads the IS
  manifest and records owed cells on skip), **NOT** consolidator-driven. The DeFi manifest shows **0**
  expected_unattempted rows for ONE reason (deferred Phase 6,
  `issues/expected_unattempted_validation_pending_phase3_2026_05_19.md`): **no prod MTDS batch has RUN on the
  post-Phase-1+2 code yet** (defi 1.6M rows, 0 owed). So the fix is **run the existing chain + validate**, NOT build a
  parallel consolidator mechanism. (The earlier "never materialised / 0 source hits" reading was wrong — the handlers
  don't reference it because the pre-flight lives in the batch orchestrator, not per-handler.)

## `expected_unattempted` — the mechanism exists; RUN it for DeFi (corrected B0)

**Do NOT build a consolidator step (rejected — would duplicate the shipped chain).** The propagation chain already
exists (`expected_unattempted_propagation_chain_2026_05_12.md`, archived, Phases 0–2 shipped): the MTDS batch
orchestrator does an instruments-service **pre-flight** — it reads the IS manifest, and for every instrument the IS
lists that the batch will NOT attempt (outside scope / upstream empty), it calls `record_expected_unattempted(...)` with
reason `EXPECTED_OUTSIDE_PROCESSING_SCOPE` / `EXPECTED_UPSTREAM_EMPTY`. MDPS + features propagate it downstream. The
owed rows are written by the **writer**, at shard grain, gated by the **IS manifest** (which already encodes "this
instrument should exist") — exactly the operator's intent (`we have the instrument + it's post-genesis, but no data`).

**Why DeFi shows 0**: no prod MTDS batch has run on the post-Phase-1+2 code for the DeFi buckets since 2026-05-19. So
the remaining work is to **RUN the existing chain for the DeFi handlers + validate** (the deferred Phase 6), NOT
re-implement.

What to verify/wire (B0 corrected scope):

- Confirm the DeFi MTDS batch orchestrator path (oracle / perp / lst / lending / dex handlers) goes through the same
  instruments-service pre-flight that records `expected_unattempted` (Phase 1 wired CeFi/TradFi; confirm DeFi handlers
  are on that path — they may need wiring since DeFi uses dedicated buckets + a different orchestration).
- Run a DeFi MTDS dry-run on a sample date → confirm `expected_unattempted` rows generate with correct reasons.
- Then the denominator is honest automatically: `% = captured / (captured + empty + failed + expected_unattempted)` —
  consumers just read it (B1/B2/B3).
- Composes with `issues/expected_unattempted_validation_pending_phase3_2026_05_19.md` (the deferred validation).

## Status legend: ✅ shipped · ⏳ ready/in-flight · ☐ todo · canonical todos below feed the orchestrator backlog

## A. Owner code (writers) — canonical writes

- [x] ✅ [CODE] P0. A1 pre-genesis empty-reason: oracle + evm-defi handlers classify via UAC `get_chain_genesis_date()`
      → `EXPECTED_PRE_GENESIS_CHAIN`. market-tick-data-service@840d85f1.
- [~] [DATA] P1. A2 pre-venue-launch reason — manifest migration (operator: "captured in UAC if genuinely pre venue +
  migrated in manifest"). **UAC ALREADY HAS** most launch dates in `DEFI_VENUE_LAUNCH_DATES` keyed `VENUE-CHAIN`
  (MARINADE-SOLANA 2021-08-02, JITO-SOLANA 2022-08-16, LIDO-ETHEREUM 2020-12-19, ETHERFI/ETHENA, …) — my earlier "None"
  was a wrong-key lookup (flat `LIDO` vs `LIDO-ETHEREUM`). **APPLIED 2026-06-01**:
  `plans/audit/results/defi_venue_launch_relabel_migration_2026_06_01.py --apply` relabeled **1,337** lst-rates rows →
  `EXPECTED_PRE_VENUE_LAUNCH` (ETHENA/ETHERFI/LIDO 353 each + MARINADE 278), UAC-backed + snapshotted.
- [ ] [CODE] P1. A2a populate UAC `DEFI_VENUE_LAUNCH_DATES` for the venue-chains genuinely missing it (the migration
      reports them): **perp** `ASTER`, `LIGHTER-ZKSYNC`, `PACIFICA-SOLANA`, `HYPERLIQUID` (clear new venues — add
      accurate launch dates). **DEX per-chain** (`CURVE-OPTIMISM`, `PANCAKESWAPV3-BSC`, `UNISWAPV3-POLYGON`,
      `BALANCER-OPTIMISM`, `AAVE_V3-BASE`, `SPARK-ETHEREUM`, …) — **data-quality flag**: their captured rows show a
      uniform first-captured `2021-01-01` across ALL chains incl. Base (launched 2023), which is impossible →
      investigate (placeholder/wrong-date captured rows) BEFORE adding launch dates. Do NOT bulk-add ambiguous dates.
      Then re-run the relabel. parent_epic: manifest_master.
- [x] ✅ [CODE] P1. A2b — `DefiManifestRecorder.record_zero_rows()` routes pre-launch zero-rows →
      `EXPECTED_PRE_VENUE_LAUNCH` via the venue-chain launch lookup; `lst_rates_handler` + `solana_defi_handler` empty
      branches wired + regression tests. — mtds@PR#115 + mtds@48d08b11 (PR#117). **Incident note**: #115 used a
      bare-venue launch lookup but `DEFI_VENUE_LAUNCH_DATES` keys by `VENUE-CHAIN` → pre-launch mis-routed to
      `SOURCE_RETURNED_ZERO`; #117 fixed to `f"{venue}-{chain}"` + bare fallback. 2444 unit tests green.
- [x] ✅ [CODE] P1. A3 data_type name SSOT at write — **verify-done 2026-06-01**: every DeFi handler `_DATA_TYPE`
      constant + `data_type=` literal is underscore-canonical
      (`dex_pools`/`dex_swaps`/`lending_indices`/`lst_rates`/`oracle_prices`/ `perp_funding`/`dex_pool_state`); **zero
      hyphen literals written by any handler**. The hyphen variants (`lending-indices`/`dex-pools`/`dex-swaps`) +
      `staking_yields` in the corpus are purely LEGACY data → fixed by C2.
- [x] ✅ [CODE] P2. A4 (WRITE-PATH) — `BlankChainError` guard on `record_captured` (canonical data rows fail loud on a
      blank chain). — mtds@PR#115; **narrowed to the write-path only in mtds@48d08b11 (PR#117)** after the original
      `_build_row_key` guard broke `perp_funding_handler` gmx's intentional `chain=''` coarse freshness-marker (2
      `TestFreshnessSkip` failures — a #115 regression caught + fixed same-session).
- [ ] [CODE] P2. **A4-full — extend the blank-chain guard to ALL record paths (re-filed from the #117 narrowing).**
      Prerequisite: make `perp_funding_handler` GMX per-chain — `_collect_gmx` already records ARBITRUM+AVALANCHE
      captured rows, but the loop uses a coarse `chain=''` freshness/attempt marker (`_chain_map.get("gmx","")`, L312 +
      the fallback empty at L369). Make the freshness check + fallback-empty per-chain so no `chain=''` row is ever
      keyed, THEN restore the `_build_row_key` blank-chain guard so empty/failed markers are also chain-canonical.
      parent_epic: mtds_mdps_master.
- [ ] [CODE] P1. A5 LIGHTER perp_funding adapter fix: `SOURCE_RETURNED_ZERO` across full post-launch life (zkSync
      endpoint returns nothing) — verify endpoint/auth.
- [x] ✅ [CODE] P0. A6 `expected_unattempted` is ALREADY canonical in UAC (`honest_coverage.py`:
      `EXPECTED_UPSTREAM_EMPTY` + `EXPECTED_OUTSIDE_PROCESSING_SCOPE` reasons; shipped via
      `expected_unattempted_propagation_chain_2026_05_12.md` Phase 0). No new state to add — verified 2026-06-01.
- [x] ✅ [CODE] P0. A7 **fetch-failure swallow bug — record `attempted_failed` not `empty_confirmed`** (operator
      2026-06-01). Systemic: a fetch helper does `except Exception: … return []`, swallowing a timeout/DNS/RPC error →
      caller sees zero-rows-no-error → `record_empty(SOURCE_RETURNED_ZERO)` = a silent lie the data is genuinely empty.
      **Fixed (mtds@d3d26f56, re-raise → caller `record_failed`)**: `lst_rates_handler` L697, `oracle_prices_handler`
      L820/L948. **Swept clean**: instruments-service + features-service adapter I/O — **no swallow sites found** (the
      bug was MTDS-specific). **⚠️ CORRECTION 2026-06-02 (slot-2): the IS "swept clean" claim was INCOMPLETE** — A7
      swept the `except → return []` shape, but a SECOND shape (`HTTP-200 {"errors":[...]}` / missing-`data` →
      `return []` "treating as empty") survives in IS DeFi subgraph adapters (aave_v3/spark/morpho/uniswap_v3) — see
      **A8** (reopens this). **`lending_indices_handler` L989** (Aave RPC fallback): the handler already routes subgraph
      errors to `record_failed` (comments L736-741/L838-839 reference a prior fix for this exact class) — the residual
      `_do_rpc_walk` `return []` is an ambiguous fallback path, NOT a clear bug; flagged for careful tracing under audit
      item (i), do NOT rush a fix. Per-adapter audit codified in `defi_master`(aa)/`mtds_mdps`(i)/`instruments`(h)/
      `features_and_ml`(u). 3 mtds fixes need QG green before LDR. parent_epic: mtds_mdps_master.
- [x] ✅ [CODE] P1. A8 **REOPENS A7's "instruments-service swept clean" claim — a SECOND swallow shape exists in IS DeFi
      subgraph adapters** (slot-2 audit 2026-06-02, answering operator "is an API issue → attempted_failed not
      empty_confirmed?"). **✅ A8 SHIPPED for the 3 single-query subgraph adapters — IS@17309f05** (new shared
      `defi_utils.assert_subgraph_payload()` raises ConnectionError on 200-with-`errors`/missing-`data` →
      `aave_v3`+`spark`+`morpho` wired; 4 enshrined-the-bug unit tests updated). **✅ A8b SHIPPED — IS@359f245c**:
      `uniswap_v3` made cascade-aware (tries Messari/Algebra/Sushi; RAISES only if ALL legs errored with 0 pools; fixed
      a messari `{data:None}` NoneType crash) + 7 REST/Solana adapters
      (drift/flash_trade/lifinity/mango/meteora/phoenix/ zeta) routed through new
      `defi_utils.extract_rest_list_or_raise()` (bare `[]`/`{key:[]}`=legit-empty, missing-key/error-envelope=raise);
      jupiter/pyth left (static-constant discovery, no swallow). Tests flipped+added; IS QG green. Repo:
      instruments-service. parent_epic: mtds_mdps_master. A7 swept the `except Exception: … return []` shape and found
      IS clean — but it MISSED the `HTTP-200 + {"errors":[...]}` / missing-`data`-field → `return []` "treating as
      empty" shape. CONFIRMED in
      `instruments-service/instruments_service/reference_data/adapters/defi/aave_v3.py:144-152` + `spark.py:166-173`
      (both in the `get_instruments` discovery path; comment literally says "rate-limit / transient indexing issues …
      treating as empty"). On a transient subgraph error these return an EMPTY instrument universe with NO exception →
      those instrument-days silently drop out of the expected universe entirely (never `attempted_failed`, never even
      `expected_unattempted` — worse than `empty_confirmed`). FIX: on a 200-with-`errors` body raise (→ caller records
      the discovery failure) instead of `return []`. **Audit ALL ~53 DeFi adapters under `reference_data/adapters/defi/`
      for the same shape** (the `return []`-on-soft-error pattern is workspace-wide; only aave_v3/spark carry the
      explicit "treating as empty" comment but the others need verifying). Repo: instruments-service. parent_epic:
      mtds_mdps_master.
- [x] ✅ [CODE] P1. A9 **MTDS `dex_swaps_handler` balancer branch made consistent with the cascade's honest-failure
      handling — SHIPPED mtds@45dced01.** The univ3/messari cascade already RAISES `RuntimeError` when all schemas
      return GraphQL errors (`dex_swaps_handler.py:700-708`, "records ADAPTER_FETCH_FAILED rather than
      SOURCE_RETURNED_ZERO") — the single-query **balancer** branch (`dex_swaps_handler.py:658`) returned an empty frame
      on a `None` (200-with-`errors`) response → downstream `record_empty(SOURCE_RETURNED_ZERO)` (false complete-empty).
      Now raises on `data is None`, matching the cascade. MTDS QG green (sentinel 8ffb2acd). (Same commit set unblocked
      a pre-existing foreign import-pattern violation in `migrate_tradfi_to_v9_canonical.py` → facade import,
      mtds@89aff1b1.) Repo: market-tick-data-service. parent_epic: mtds_mdps_master.
- [ ] [CODE] P1. A10 **wire the `EmptyFromLiveInstrumentError` backstop — it is DEFINED but never RAISED** (slot-2 audit
      2026-06-02). The operator-directed (2026-05-07) safety net — `record_empty(SOURCE_RETURNED_ZERO)` must cross-check
      the IS catalog and reject (force `attempted_failed`) when the instrument was ALIVE on that day — exists only as a
      class in `unified-api-contracts/.../honest_coverage.py:979` + `__all__` export; grep finds ZERO raise sites in the
      write path. UTL `record_empty` (`manifest_writer.py:1958`) only guards blank/unknown reason
      (`LegacyBlankErrorReasonError`), NOT live-instrument emptiness. Without this backstop, correctness depends
      entirely on each adapter raising — so the A8/A9 swallow gaps go uncaught. **DESIGN (operator-refined 2026-06-02):
      abstract into a UTL helper + ENFORCE with a quality gate** — the "expected universe" oracle is per-asset-group
      (sports = fixtures exist for the day; cefi/defi/tradfi/prediction = instrument listed-and-not-delisted), but the
      _routing_ (zero-rows + was-expected → `attempted_failed` via `EmptyFromLiveInstrumentError`, else
      `empty_confirmed[reason]`) is generic and belongs in UTL so callers can't get it wrong. Sub-items:
  - [x] ✅ [CODE] P1. **A10a — UAC `was_instrument_alive(available_from, available_to, day) -> bool` SHIPPED
        uac@10e69f08.** Pure lifecycle primitive (on
        `InstrumentRecord.available_from_datetime`/`available_to_datetime` + shard `day`) next to
        `EmptyFromLiveInstrumentError`; CONSERVATIVE (fires only on positive catalog confirmation; unknown
        `available_from` → False). Facade-exported (`from unified_api_contracts import was_instrument_alive`) + 5 unit
        tests. UAC QG green. Repo: unified-api-contracts. parent_epic: mtds_mdps_master.
  - [x] ✅ [CODE] P1. **A10b — UTL `ManifestWriter.record_zero_rows(...)` routing helper SHIPPED utl@44d762d9** (+ UAC
        facade-export `EmptyFromLiveInstrumentError` uac@daf1888c). `was_expected` →
        `record_failed(     EmptyFromLiveInstrumentError(...))` (attempted_failed); else → `record_empty(reason)`.
        Caller computes `was_expected` from the per-AG oracle (sports fixtures / `was_instrument_alive`). Single
        sanctioned zero-rows write path; +2 routing tests; UAC+UTL QG green. Repos: unified-trading-library +
        unified-api-contracts. parent_epic: mtds_mdps_master.
  - [ ] [CODE] P1. **A10c — QG enforcement step** (MTDS/IS/MDPS/features quality-gates, STEP 5.70 family): fail any
        `record_empty(...SOURCE_RETURNED_ZERO...)` callsite NOT routed through `record_zero_rows` (baselined ratchet +
        `# QG-allow:` waiver for audited exceptions). Makes the backstop un-bypassable. Repo: per-service
        `quality-gates.sh` + a shared check script. parent_epic: mtds_mdps_master.
  - [ ] [CODE] P1. **A10d — migrate the DeFi `SOURCE_RETURNED_ZERO` callsites** (dex_pools/dex_swaps/lst/lending/perp
        handlers) to `record_zero_rows` with the `was_instrument_alive` oracle. NOTE: DeFi records at (venue,chain)
        shard granularity, so the oracle is "was ANY in-universe instrument for this venue/chain alive on this day" —
        and for DeFi the venue-launch gate (A1/A2, shipped) already covers most of it; A10d closes the residual. Repo:
        market-tick-data-service. parent_epic: mtds_mdps_master. Repos: unified-api-contracts +
        unified-trading-library + market-tick-data-service. parent_epic: mtds_mdps_master.
- [ ] [CODE] P0. A11 **DEAD-BUCKET / CANONICAL-PATH PRE-MIGRATION ALIGNMENT — code must not regress against legacy/dead
      buckets BEFORE the migrations run** (operator 2026-06-02: "refactor read/write cloud-storage paths across the
      board to match canonical so QG-fed tests don't regress by association with dead buckets; same for data-status in
      deployment API + UI which resolve many bucket-name / menu / data_type / manifest conventions"). Slot-2 two-front
      audit 2026-06-02 found the C0-CN sweep aligned the DeFi raw read/write path but NOT the **manifest-handler /
      data-status / deployment-API+UI** surfaces, which hardcode legacy bucket names + data_types. Each sub-item names
      repo + file:line; VERIFY-then-fix (some are intentional logical-name distinctions — confirm against
      `codex/02-data/per-asset-group-bucket-layouts.md` + `resolve_bucket_name()` before editing). Tag `[DATA]` surfaces
      that need a test added so the regression can't reappear. parent_epic: mtds_mdps_master.
  - [x] ✅ [CODE] P0. **A11a — MTDS `data_manifest_handler.py` SHIPPED mtds@7ebfa749.** The 5 `_scan_*` f-strings
        (`market-data-tick-defi`, `gas-fees`, `{bucket_key}-{pid}`) now resolve via
        `resolve_bucket_name(kind=…,     asset_group="defi")` → env-tiered `-prd` canonical; resolutions verified
        end-to-end; MTDS QG green (IGNORE_TIMEOUT — only the <300s meta-gate tripped on the contended host; all
        substantive gates passed). Repo: market-tick-data-service. parent_epic: mtds_mdps_master.
  - [x] ✅ [CODE] P0. **A11b — deployment-service data-status now resolves buckets via `resolve_bucket_name()` — SHIPPED
        deployment-service@2e91ab2.** `manifest_reader.py` (BUCKET_TEMPLATES + \_EXTRA_BUCKETS → canonical kinds),
        `catalog.py` (SERVICE_GCS_CONFIGS), `data_status_checkers.py` (L624) all route through
        `resolve_bucket_name(kind=…, asset_group=…)` → env-tiered `-prd` canonical (survives legacy-bucket deletion);
        behavior-preserving + verified equivalent. + cloud-providers.yaml 6 DeFi kinds. deployment-service QG green
        (sentinel 4cbb2e27). Repo: deployment-service. parent_epic: mtds_mdps_master.
  - [x] ✅ [CODE] P0. **A11b-blocker — `state.py` STEP 5.90 FIXED (deployment-service@2e91ab2).** Was a genuine
        pre-existing contract violation (the `/data-status` route delegated to `DataCatalog` which computes
        file-existence completion, NOT canonical honest-coverage — the banned inline pattern). `get_data_status` now
        ADDITIVELY attaches `coverage` (canonical 5-field `compute_honest_coverage`) + `coverage_counts`, resolving each
        AG's bucket via `resolve_bucket_name` + summing `CaptureStatusCounts` from `compute_coverage_for_bucket` (UI
        keys preserved; catalog file-existence metric untouched). STEP 5.90 ✅. Repo: deployment-service. parent_epic:
        mtds_mdps_master.
  - [x] ✅ [CODE] P1. **A11c — DONE (slot-2 2026-06-02): full canonical denominator collapse across UAC + cross-repo
        cascade** — uac@a967121a + mdps@56503c2 + deployment-api@14dfe2e + mtds@b986a3e1 (all QG-green except
        deployment-api's pre-existing acknowledged provenance debt). Residual follow-ups DECOUPLED + tracked below:
        A11c-candle-enum (Phase-2 collision) + C0-RD6 (`_DEX_EXT` split). **A11c — UAC
        `registry/market_data_categories.py` DeFi data_type list legacy vs canonical**: L144-177 lists
        `dex_pools`/`dex_swaps` (legacy logical) while the v9 on-disk + manifest canonical is
        `dex_pool_state`/`dex_pool_swaps` (operator-locked `defi-canonical-naming-ssot.md`). VERIFY whether this list is
        a logical menu (intentional) or a physical-key source consumed by data-status; if the latter, align to
        canonical + reconcile `registry/data_type_capability.py` L336-345 "aspirational/deferred" note. Repo:
        unified-api-contracts. **⚠️ VERIFIED-CONSUMED + SCOPE EXPANDED 2026-06-02 (slot-2 grep-then-read): A11c is NOT a
        logical menu — it is a physical expected-key consumed by the data-status DENOMINATOR**, and the legacy
        `dex_pools`/`dex_swaps` data_type string is used as a physical key across a COUPLED SET of UAC registries far
        beyond A11c's 2 named files, ALL of which the C0-CN sweep (CN1–CN8) left on the legacy name even though CN2
        already moved the **manifest** data_type to canonical `dex_pool_state`/`dex_pool_swaps`. Confirmed break:
        `registry/expected_coverage.py` `expected_coverage()` does a literal `data_type not in in_scope_types` match
        (`_DEFI[venue]=["dex_pools","dex_swaps"]`) → a canonical `dex_pool_state` cell returns `NOT_IN_SCOPE` (canonical
        pool/swap rows fall OUT of the DeFi coverage denominator). Coupled UAC surfaces still on legacy name:
        `expected_coverage.py` (`_DEFI_DEX_PAIRS`), `defi_venue_capabilities.py` (35 per-(venue,data_type) start-date
        keys), `capability_declarations/_defi.py` (protocol `data_types`), `market_data_categories.py`
        (BASE_GRANULARITY/NEEDS_CANDLE_PROCESSING/DATA_TYPES_BY_ASSET_GROUP/\_PER_INSTRUMENT_SHARD
        /FEATURE_GROUP_DATA_TYPE_OVERRIDES), `source_priority.py`, `availability_semantics.py`,
        `canonical/domain/features/required_inputs.py`, `defi_prediction_instrument_seeds.py`, `venue_constants.py`
        (`DEX_POOL`), `internal/domain/.../candle_schema.py` (`DEX_POOLS`/`DEX_SWAPS` enum),
        `internal/schemas/contracts.py` + `_defi_v2_contracts.py` (schema-registry keys). Cross-repo consumers of these
        registries (MTDS orchestrator, MDPS scanner, deployment-api data_status, features data_loader) inherit the key.
        **This is the "reader/denominator fixes land FIRST" gate (naming-SSOT Sequencing #1) — it must land BEFORE the
        C0 `--apply` or migrated data is NOT_IN_SCOPE in data-status.** Decision recorded with operator 2026-06-02 (full
        canonical rename, lands before apply). Repo: unified-api-contracts (+ coupled cross-repo consumer verification).
    - [x] ✅ [CODE] P1. **A11c-UAC — UAC registries + tests + venue_data_types.yaml canonicalised** — uac@a967121a +
          PM-configs@ad30e9fd1 (slot-2 2026-06-02, UAC QG green): word-boundary rename `dex_pools`→`dex_pool_state`,
          `dex_swaps`→`dex_pool_swaps` across all 14 UAC source files above + `data_type_capability.py` note
          reconciled + 6 UAC tests updated (`test_data_type_canonicalization` `_BANNED_ALIASES`: `dex_pools`/`dex_swaps`
          now THEMSELVES banned legacy aliases) + both `venue_data_types.yaml` (PM-configs + mtds-configs). Bucket NAMES
          (`dex-pools`/`dex-swaps` hyphen) + enum MEMBER names (`DEX_POOLS`) preserved — only the data_type STRING value
          collapsed. Pending UAC QG-green + commit.
    - [x] ✅ [CODE] P1. **A11c-MDPS — candle-adapter re-registered dex_pool_swaps** — mdps@56503c2 (MDPS QG green). the
          orchestrator selects the candle adapter by the exact UAC data_type, now `dex_pool_swaps`, but
          `app/adapters/defi/swap_adapter.py` registers `@CandleAdapterRegistry.register(DEFI, "dex_swaps")` → "No
          adapter for defi/dex_pool_swaps" (the adapter docstring warns of this exact failure). Re-register under
          `dex_pool_swaps` + update `app/core/canonical_writer.py` legacy keys (`"dex_swaps":"swaps_ohlcv"`,
          `("defi","dex_swaps"):"swap"`) to canonical. `orchestration_scanner.py` `_CANONICAL_LEGACY` map already
          accepts both (transition-aware — no change). Repo: market-data-processing-service. parent_epic:
          mtds_mdps_master.
    - [x] ✅ [CODE] P1. **A11c-deployment-api — data-status canonical** — deployment-api@14dfe2e (TESTS green; repo QG
          blocked ONLY by PRE-EXISTING acknowledged schema-provenance debt across many local DTOs — UNRELATED, flagged
          for workspace-QG-green sweep). `_BUCKET_DOMAIN_TO_DATA_TYPE` (`services/data_status_service.py`
          `"dex-swaps":"dex_swaps"`/`"dex-pools":"dex_pools"`) + `services/shard_detail.py` grouped-bundle set +
          `services/data_query_service.py` `"DEFI":["dex_swaps",…]` default → canonical
          `dex_pool_swaps`/`dex_pool_state` (the expected denominator via `get_expected_data_types_for_venue` is now
          canonical, so these must match). Repo: deployment-api. parent_epic: mtds_mdps_master.
    - [x] ✅ [CODE] P1. **A11c-MTDS — adapters + orchestrator + live connector canonical** — mtds@b986a3e1 (MTDS QG
          green; ALSO flipped 5 DeFi DEX adapters' SUPPORTED*DATA_TYPES/\_default_data_types/branch-dispatch, forced
          canonical by the UAC denominator flip) (slot-2 2026-06-02): `engine/orchestrator.py` per-data_type config
          (`"dex_pools"`/`"dex_swaps"` sort-key map L621-622) + live `live/connectors/curve_defi_ws.py`
          `_data_type == "dex_pools"`/`"dex_swaps"` dispatch (live=batch — handler now sets canonical `_DATA_TYPE`) →
          canonical. Do NOT touch the historical migration/backfill SCRIPTS that intentionally map legacy→canonical
          (`migrate_legacy_solana*_`, `canonicalize*defi_manifest_data_types*_`,     `gate3_solana_manifest_reconcile`).
          Repo: market-tick-data-service. parent_epic: mtds_mdps_master.
    - [x] ✅ [CODE] P2. **A11c-features — verify-only: NO functional break** (Explore sub-agent confirmed
          features-onchain already canonical-aware post-C0-CN4; hits are comments/docstrings/yaml) (slot-2 2026-06-02).
          features-onchain hits are comments/docstrings + `feature_definitions.yaml` post-C0-CN4; confirm no functional
          `data_type=="dex_pools"` literal break, update docstrings/yaml for accuracy. Repo: features-service.
          parent_epic: features_and_ml_master.
    - [ ] [CODE] P2. **A11c-candle-enum — UAC `candle_schema.DataType` snapshot-vs-timeseries naming COLLISION** (slot-2
          found 2026-06-02): `internal/domain/market_data_processing/candle_schema.py` `DataType` enum has BOTH a legacy
          `DEX_POOLS = "dex_pools"` / `DEX_SWAPS = "dex_swaps"` (candle-input) AND a DISTINCT Phase-2
          `DEX_POOL_STATE = "dex_pool_state"` (spot-DEX time-series state, comment: "distinct from the existing
          DEX*POOLS \_snapshot* type"). The operator-locked canonical pool name `dex_pool_state` **collides** with the
          Phase-2 member's value → a StrEnum alias if DEX_POOLS is renamed to it. **Slot-2 left DEX_POOLS/DEX_SWAPS on
          the legacy values** (they are not consumed by member-name anywhere; functional collapse is enforced on
          market_data_categories/expected_coverage/defi_venue_capabilities). RECONCILE: decide whether the legacy
          `dex_pools` snapshot type and the Phase-2 `dex_pool_state` time-series type are the SAME (merge — remove
          DEX_POOLS, point all to DEX_POOL_STATE) or genuinely DIFFERENT shapes (then the operator's canonical-pool name
          needs a distinct token from the Phase-2 type — **operator decision**). Also check `DEX_POOL_SWAPS` does not
          exist yet (only DEX_POOL_STATE/DEX_ORDERBOOK/DEX_QUOTE/DEX_TRADES). Repo: unified-api-contracts. parent_epic:
          mtds_mdps_master.
  - [ ] [CODE] P1. **A11d — MTDS `data_manifest_handler.py` OPERATIONS metadata legacy data_types**
        (`bucket_type:     dex-pools`/`dex-swaps`/`lending-indices`) — reconcile with the canonical
        `dex_pool_state`/`dex_pool_swaps` handler `_DATA_TYPE` consts (C0-CN2). Repo: market-tick-data-service.
  - [ ] [DATA] P1. **A11e — TESTS encoding legacy buckets/data_types (silent-regression maskers)**: e.g. mtds
        `tests/unit/test_smoke_matrix.py` (`market-data-tick-{category}-{pid}` mock), `test_defi_manifest_recorder.py`
        (`data_type="dex_pools"` asserts), `test_curve_defi_ws_connector.py` (`dex_pools`); deployment-ui
        `tests/unit/components/DataStatusTab.phase8h.test.ts` (`honest["dex_pools"]`). Update to assert CANONICAL
        forms + add a guard test so the legacy form can't silently pass. Repos: market-tick-data-service +
        deployment-ui.
  - [ ] [CODE] P2. **A11f — residual `category=` writers** (legacy hive key vs canonical `asset_group=`): mtds
        `market_interface/__init__.py` + live manifest recorder `category=` alias. Readers already probe
        canonical→legacy (transitional OK); migrate writers so post-cutover writes are canonical-only. Repo:
        market-tick-data-service.
- [ ] [CODE] P0. A12 **UPSTREAM-DATA PREFLIGHT CHECKS — every consuming service, every in-scope (DeFi) cell** (operator
      2026-06-02). Audit + ensure each consuming service runs an upstream-data **preflight** before processing, that:
      (1) **reads via the post-migration canonical SSOT** — `resolve_bucket_name()` buckets + canonical
      path/`pipeline_mode=`/`data_type` + canonical column schemas (no dead-bucket/legacy-path/legacy-data_type
      assumptions — composes with A11); (2) **gates on data-quality** — 0-volume / NaN-price / all-null / row-count-0 /
      schema-missing-column → when the upstream cell is **genuinely missing + EXPECTED**, take the honest-absence path
      (`record_zero_rows(was_expected=…)` / `record_empty(reason=…)` per A10b, NOT fabricated placeholders); (3)
      **manifest marks incomplete-expected** — every owed-but-absent cell is `expected_unattempted` / `empty_confirmed`
      / `attempted_failed` (A8/A9/A10 + B0), so "incomplete-but-expected" is visible, never silently complete. (4)
      **LIVE = BATCH check symmetry, DIVERGENT actions** (live=batch principle): identical preflight check LOGIC in both
      modes; only the POST-check ACTION differs — **live** → emit alert + trip circuit-breaker + halt/skip-trade (bad
      data is capital risk; never trade on it), **batch** → fill-what-you-can + log + continue (best-effort backfill, no
      halt). Verify the action divergence is wired (live circuit-breaker/alerting on failed preflight) and that the
      CHECK itself is shared code (no live-only/batch-only check drift). **Scope: DeFi** across mtds (handlers/readers)
      · mdps (scanner/adapters) · features-onchain (readers/calculators) · strategy (data preflight before signal) ·
      execution (mark/price preflight before order). **Audit-first** (read DATA-STATE + code; surface where checks are
      missing/legacy-bucket-bound/live-batch-asymmetric), then fix per service with a guard test. Sub-items per service
      to be filed from the audit. **GATED-COMPOSES**: depends on A11 (canonical buckets) + A8/A9/A10 (honest-absence
      routing) being landed so the preflight reads the right place + marks the right state. parent_epic:
      mtds_mdps_master.
  - [x] ✅ [AUDIT] P0. A12-AUDIT — **6-service preflight audit DONE (slot-2, 2026-06-04)**: preflight + honest-absence +
        the operator's zero-volume/NaN/last-price candle ask are **substantially engrained via SHARED code** (UAC
        `honest_coverage.py` EmptyConfirmedReason/RecordFailedReason/compute_honest_coverage; UTL BaseDependencyChecker
        / run_preflight / assert_consolidator_healthy / classify_venue_error; MDPS `BaseCandleAdapter`
        `_make_zero_activity_candle_output`/`_carry_forward_ohlc` LOCF/`_finalize_session_grid`). **4/6 services DONE**:
        MDPS candle layer (zero-vol/LOCF/NaN, batch=live via batch_workers+live_workers), features-onchain
        (capture_status-aware DependencyError), strategy-service (`validation/freshness_gate.assert_feature_fresh` →
        DataStalenessError, live-halt vs batch-warn), execution-service (`validation/freshness_gate` — NaN/Inf benchmark
        blocked BOTH modes; stale → live kill_switch.activate vs batch degrade+continue). Concrete GAPS filed below
        (A12a-A12e). parent_epic: mtds_mdps_master.
  - [x] ✅ [CODE] P1. A12a — **upstream-IS preflight GATE wired** (uac@d67d8061 + mtds@e2fc7d51): added
        `PreflightTrigger.DEFI_COLLECT_DAILY` → `defi_market_data` → `INSTRUMENTS_PREFLIGHT_REQUIREMENTS`
        (instrument-catalog ≤24h, mirrors CeFi/TradFi) in UAC; `assert_defi_catalog_fresh()` in `_defi_manifest.py`
        wraps UTL `run_preflight` (honest-absence: returns False → caller `record_failed` per shard, no raise in
        per-venue loop; live circuit-breaker downstream). Wired into the 2 May-23-critical handlers
        (dex_pools=arbitrage, lst_rates=carry) + guard tests (UAC +4, MTDS +3). Both repos QG-green. **Residual
        (A12a-rollout, P1)**: the same one-line gate at the remaining ~25 DeFi collect handlers (mechanical) — see
        sub-todo. parent_epic: mtds_mdps_master.
  - [ ] [CODE] P1. A12a-rollout — extend `assert_defi_catalog_fresh()` (the A12a gate) to the remaining ~25 DeFi collect
        handlers (eigenlayer*rewards, evm_defi, gas_fee, lending_indices, liquidations, oracle_prices, perp_funding,
        solana_defi, native_staking, vault_share_price, staking_yields, token_transfers, position_data,
        flash_loan_events, governance*\*, mev_events, jupiter_quote, orca_whirlpool_state, raydium_classic_amm,
        aggregator_route, bridge_events, drift_v2_historical, protocol_outage_detector, liquidation_events) at each
        `process()` chokepoint + a per-handler guard test. Mechanical (mirror dex_pools/lst_rates). Repo:
        market-tick-data-service. parent_epic: mtds_mdps_master.
  - [x] ✅ [CODE] P1. A12b — **CONFIRMED ALREADY EXISTS, no change needed** (slot-2 deep-read 2026-06-04): the DeFi
        owed-cell backstop is enumerator-driven —
        `instruments-service/scripts/enumerate_expected_universe.py::_enumerate_v2_defi` yields
        `ExpectedRow(capture_status="expected_unattempted")` for every catalog-alive DeFi cell with no manifest row
        (pre-genesis/listing → `empty_confirmed[EXPECTED_*]`; delisted → `EXPECTED_INSTRUMENT_DELISTED`), materialised
        by `_write_absent_rows` (per-VM shard, row_count=0, never omitted/fabricated), guarded by
        `test_enumerate_expected_universe_v2.py::test_defi_v2_alive_date_not_in_present_set_yields_expected_unattempted`
        (+ 2 negatives). The earlier "unconfirmed" was a grep-0 artifact; `EmptyFromLiveInstrumentError` is correctly an
        MTDS-CONSUMER concern (A10c/d), not IS. IS DeFi writes resolve buckets via `resolve_bucket_name` (canonical).
        Repo: instruments-service (no code change). parent_epic: mtds_mdps_master.
  - [x] ✅ [CODE] P1. A12c — **CONFIRMED already-wired for DeFi** (slot-2 deep-read 2026-06-04; guard added
        mtds@e2fc7d51): the earlier "RED gap" was stale. UAC `SOURCE_PRIORITY[(defi,*)]` already carries every DeFi
        data*type; `ManifestWriter.add()._resolve_and_validate_source` auto-stamps single-source cells + raises
        `MissingSourceError` on blank multi-source; `DefiManifestRecorder.record_captured` already accepts+forwards
        `source`. The only multi-source DeFi cells — `oracle_prices` (pyth_hermes/chainlink) + `native_staking_rates`
        (solana_rpc/helius_rpc) — already pass `source=`; all others single-source → auto-stamped. Added the missing
        integration guard through the REAL writer (`test_defi_recorder_real_writer*\*`: single-source auto-stamp +
        multi-source blank → MissingSourceError). No UAC/handler change needed. parent_epic: mtds_mdps_master.
  - [x] ✅ [CODE] P2. A12d — **DONE** (mtds@b66b15d2): deleted 6 stale `*.bak` files (native_staking /
        protocol_outage_detector / staking_yields / tick_data / token_transfers / websocket_streaming). Bucket-SSOT
        audit found **no hardcoded-bucket drift** — every DeFi handler resolves writes via `resolve_bucket_name` /
        `get_write_bucket_name` / `build_bucket` (the `gs://` strings are log-format args, not inline f-strings); the
        `_defi_instruments.py` constant fallbacks are the intentional IS-fallback contract (left, noted). Residual flag:
        `gas_fee_handler.py:960` `_collect_latest_fees` builds a non-canonical `gas_fees/chain_id=…` path manually (not
        a `write_defi_rows` call) — triaged into A11/legacy-path sweep. Repo: market-tick-data-service. parent_epic:
        mtds_mdps_master.
  - [x] ✅ [DATA] P2. A12e — **CONFIRMED intended (operator-locked Option A 2026-05-16)**: MDPS aggregates 5 DeFi
        data_types (book_snapshot_5/dex_swaps/fx_rates/market_state/liquidity) with the full zero-vol/last-price/NaN
        candle treatment (`BaseCandleAdapter._make_zero_activity_candle_output`/`_carry_forward_ohlc` LOCF/
        `_finalize_session_grid`); on-chain snapshot types (vault_share_price/lst_rates/oracle_prices/lending_indices/
        perp_funding) BYPASS MDPS by design → flow MTDS-raw direct to features-onchain, which applies its own honest
        NaN/all-null handling (e.g. `perp_funding_rates_defi.py` → `record_empty(EXPECTED_NO_FUNDING_RATE_TICKS)`). So
        the candle-honesty IS covered end-to-end, just split across MDPS (swap/state types) + features-onchain (snapshot
        types) per the locked architecture. parent_epic: mtds_mdps_master.
  - [x] ✅ [CODE] P0. A12f (PATHS MATCH POST-MIGRATION — deliverable-4 PATH closure DONE; mtds@b66b15d2): the 3-way path
        divergence is RESOLVED — **(1) DONE** live DeFi writers now emit the canonical `pipeline_mode="batch"` segment
        on all 44 `write_defi_rows` calls across 26 handlers (coarse ingestion mode, NOT run*tag →
        `test_live_run_tag_leaves_path_unchanged` preserved); **(2) DONE** `rebuild_defi_manifest.py` regex + day-prefix
        probe made pipeline_mode-aware (parses migrated `pipeline_mode=batch/` + bare legacy; +10 tests) so
        post-migration rebuild no longer emits zero rows. Now migrator + live-writers + rebuild-scanner + reader ALL
        agree on `day=/pipeline_mode=batch/asset_group=defi/…`. MTDS QG green (286s, codex 14/15). **RESIDUAL (3) —
        column-vocab reconcile (P2, decoupled below as A12f-col):** the on-disk PATH segment is now coarse `batch`
        everywhere, but the manifest pipeline_mode COLUMN still differs (migrator stamps coarse `"batch"` string; live
        recorders pass fine `PipelineMode` enum to record*\*). Path-match (the deliverable) is closed; column-vocab is a
        forward-compat consistency item. Repo: market-tick-data-service. parent_epic: mtds_mdps_master.
  - [ ] [CODE] P2. A12f-col — **pipeline_mode COLUMN vocab reconcile** (decoupled from A12f): pick ONE vocab for the
        manifest `pipeline_mode` column — coarse `batch`/`live` (matches the path segment + migrator) vs the fine
        `PipelineMode` enum the live recorders currently pass to `record_captured`/`record_empty`/`record_failed`. Today
        the column is path-derived (coarse) at read-time so this is forward-compat, not a current-correctness bug; ties
        to the cross-AG `PipelineMode` vocabulary decision. Repo: market-tick-data-service (+ UAC). parent_epic:
        mtds_mdps_master.
  - [x] ✅ [CODE] P1. A12g — **DONE** (mtds@b66b15d2): added `tests/unit/scripts/test_migrate_defi_full_v9_canonical.py`
        (13 tests) covering the v9 migrator the launcher actually runs — asserts `_canonical_path` emits
        `pipeline_mode=batch/` left of `asset_group=defi/`, `_conform` stamps
        schema_version=9/asset_group/pipeline_mode/ source/available_at + LOUD-fails columns outside the union, and
        dry-run plans without writing (fake in-memory gcsfs, credential-free). Repo: market-tick-data-service.
        parent_epic: mtds_mdps_master.

## B. Manifest consolidation + data-status (owner code) — honest by default

- [ ] [DATA] P0. B0 (CORRECTED — do NOT build a consolidator step) RUN the existing expected_unattempted chain for DeFi:
      confirm the DeFi MTDS batch orchestrator goes through the instruments-service pre-flight that calls
      `record_expected_unattempted` (wire the DeFi handlers onto it if not), then run a prod DeFi MTDS batch so the owed
      rows generate; validate the denominator. **GATED on C-GREEN** — the owed rows must land in the canonical structure
      (env-split/`pipeline_mode`/`asset_group=`), so migrate first. Closes deferred
      `issues/expected_unattempted_validation_pending_phase3_2026_05_19.md`. parent_epic: manifest_master.
- [x] ✅ [CODE] P1. B1 `coverage-summary` (`data_status_service._build_coverage_for_cat`): drops the `len(index)`
      self-referential denominator — reads the 4-state `capture_status` breakdown + honest `completion_pct`
      (captured/(captured+empty+failed+expected_unattempted)), aggregated into service totals; v4 rows without
      capture_status keep the legacy all-captured path. — deployment-api@c631b39 (on LDR) | QG ✅ (938s) | regression:
      test_data_status_hierarchical.py + test_data_status_capture_status.py (603 green).
- [x] ✅ [CODE] P0. B2 drilldown (`data_status_hierarchical._aggregate_counts`): now counts the 4th bin
      `expected_unattempted` (4-tuple); `DrilldownNode`+`_totals_dict`+`_children_for_axis`+both
      `get_hierarchical_drilldown` unpack sites carry it; to_dict golden schema now 11 keys. Generic path → fixes
      IS/MTDS/MDPS/features at once. — deployment-api@c631b39 | regression:
      test_to_dict_golden_schema_has_exactly_eleven_keys + test_capture_status_counts_split_by_status (4-bin) +
      test_expected_unattempted_counts_in_total_and_dilutes_completion.
- [x] ✅ [CODE] P1. B3 drilldown denominator: `% = captured / (captured+empty+failed+expected_unattempted)` — `total`
      property + `_totals_dict` + B1 coverage all include the 4th bin. — deployment-api@c631b39.
- [x] ✅ [CODE] P2. B4 `data_status_rollup_worker.py`: **subsumed by B1** — the worker only delegates to
      `_get_coverage_summary_sync`/`_get_manifest_status_sync` (no row-count denominator of its own); B1's 4-state flows
      through it. Verified: worker `len()` uses are blob byte-sizes + asset_group count only. — deployment-api@c631b39.
- [ ] [UI] P1. B5 deployment-ui drilldown: render the 4-state (esp. `expected_unattempted`) + per-chain split; badge
      legend. (playwright gate applies)

## C. Data / manifest migration (single-walk, bundled) — fix existing rows

> **THE WHOLE POINT — fix the PAST, not just future writes (operator 2026-06-01, re-affirmed)**: the root of our
> recurring problems has been fixing the _code_ (so future writes are correct) while leaving the _past_ data + past
> manifests in legacy form — which forces fallbacks, dual-write, and a split SSOT. This plan exists to END that. §C is
> NOT manifest-only and NOT future-only. The C0 single-walk (`migrate_defi_full_v9_canonical.py`) **reads every past
> parquet object** and rewrites BOTH its **columns** (`schema_version→9`, `venue`→canonical `_V{N}`, `source` populated,
> `pipeline_mode` column, `available_at` preserve-or-backfill) AND its **path** (`category=defi`→`asset_group=defi` +
> `pipeline_mode=` partition + env-split `-prd` bucket). C0e then **rebuilds the past manifest** (consolidator) FROM the
> rewritten data — so data + manifest + data-status are all in line. C0f + L6 **delete the legacy originals** (kills the
> dual SSOT), and the reader is fail-fast-by-default with **no legacy fallback** (`manifest_reader_fail_fast`). A change
> that only corrects new writes while leaving historical objects/manifests legacy is **review-blocking** — it re-creates
> the exact fallback/dual-SSOT problem this plan deletes.
>
> **C is the foundation gate** (see Sequencing). One bundled single-walk per bucket applies C0+C2+C3+C4+C5+C7+C9
> together (no N ad-hoc walks). Backfills (C6/D1/E1) + B0-run are blocked until C is GREEN for the affected bucket.

### Migration-script performance contract (HARD RULE — codified 2026-06-01)

> **Whole-corpus GCS migration scripts MUST be built parallel + observable + shardable from day one.** Incident
> 2026-06-01: the C0 tool (`migrate_defi_full_v9_canonical.py`) walked ~40–50K objects **single-threaded** (~26% CPU of
> an 8-vCPU VM, projected **hours**), and `--workers`/`--start-date`/`--end-date` were parsed but **never used** (dead
> args). Fixed at mtds@92b8d25b. Every migration/backfill/reconciler script that walks a bucket MUST satisfy:
>
> 1. **Parallelise the object walk** with `ThreadPoolExecutor(max_workers=workers)` — GCS read/write **release the
>    GIL**, so I/O-bound walks overlap and get 5–10× (the dominant cost is GCS round-trips, not CPU). A bare
>    `for obj in objs:` loop over a remote bucket is **review-blocking**. (CPU-bound _serialize_ is GIL-capped; if
>    profiling shows serialize-bound, escalate to `ProcessPoolExecutor`/multiprocessing — but threads first for pure
>    I/O.)
> 2. **Wire the knobs — no dead args.** `--workers` actually sizes the pool; `--start-date`/`--end-date` actually filter
>    the walk (this also makes the job **date-shardable across many VMs** — the real horizontal scale lever; see
>    `launch-legacy-bucket-migration-sharded.sh`). A parsed-but-unused arg is a latent perf/scope bug.
> 3. **Path-only move ⇒ `gcs_copy_object` (server-side, ~250× faster); content/column transform ⇒ download+transform+
>    upload (unavoidable) but parallelised.** Never download+reupload when only the path changes. Idempotent: re-running
>    on already-canonical objects is a no-op (skip).
> 4. **Observability**: log a progress counter every N objects (e.g. 1000) AND run under `python -u` /
>    `PYTHONUNBUFFERED=1` — otherwise block-buffered stdout hides all progress until exit (the C0 dry showed only 3
>    sample lines for 25 min, indistinguishable from a hang without an SSH CPU check).
> 5. **Per-object failure isolation** — `try/except … continue` per object (log + skip), never `raise` inside the walk
>    (composes with shard-level failure isolation). The run completes; the verify step (C0e) catches any gaps.
> 6. **Tune for the bottleneck**: I/O-bound → more workers + GCS client connection-pool headroom (gcsfs/aiohttp default
>    ~100 conns covers workers≤~64); CPU/bandwidth-bound → bigger VM (more vCPU + egress) or shard across VMs by date.
>    GCS has **no client-side warm cache** — concurrency (in-flight requests), not "warming", is the throughput lever.
>
> SSOT for GCS object ops + this contract: `codex/05-infrastructure/gcs-object-operations.md` (add a "migration-script
> performance contract" section there when this plan archives).
>
> **`source` is a COLUMN, not a path key (provenance SSOT — operator 2026-06-01)**: all sources co-mingle on the SAME
> read path, so the consumer-facing layout is identical ("data looks the same") — the `source` column exists only so WE
> can identify where a row came from when we audit. It is additive (one extra column); resolution by `SOURCE_PRIORITY`
> only matters when >1 source exists for a cell. This holds for every AG's walk (sports lifts source path→column; the
> rest stamp the column directly). Applies to the rider closure below.
>
> **Rider closure (driving §C completes the DeFi rows of the two cross-cutting rider plans)**: the C0 single-walk
> BUNDLES both riders for DeFi, so flipping C0 GREEN also closes them for `asset_group=defi` — no separate DeFi walk in
> either plan: (1) **`pipeline_mode_partition_migration_2026_06_01`** DeFi row — the `pipeline_mode=` on-disk partition
> is in the C0 target-form + C9; (2) **`data_source_provenance_all_asset_groups_2026_06_01`** DeFi rows (Phase 2
> backfill) — the `source` column (UAC SOURCE_PRIORITY: `onchain_subgraph`/`oracle_prices`=pyth+chainlink/
> `native_staking_rates`=solana_rpc+helius_rpc) is written by the C0 tool in the SAME pass (per the cross-plan banner
> above — provenance must NOT open a third walk on the DeFi `_index`). When C0 is verified, flip those plans' DeFi rows
> with `— defi via defi_manifest C0@<sha>`.

> **🛑 CRITICAL DISCOVERY 2026-06-01 (data-state audit) — C0's premise below is WRONG; tool needs a redesign before
> rerun.** The C0 note says "current dedicated-bucket objects are in the flat `day=/category=defi/…` form." The audit
> (`audit_canonical_form.py` + recursive ls) proves each source DeFi bucket holds **THREE overlapping layouts**, and the
> flat form is the minority. For dex-pools (191,456 parquet):
>
> - `dex_pools/{venue}/{chain}/date=…` (lowercase venue, `date=` not `day=`, no asset_group) — **166,257 (87%)**,
>   oldest, worst schema, FULL history.
> - `day=/category=defi/venue=…` (flat) — 19,257 (10%), middle.
> - `raw_tick_data/by_date/day=/asset_group=defi/venue={CANONICAL}/…/data_type=dex_pool_state/` — ~5,900 (3%), **best
>   schema** (canonical `_V{N}` venue + asset_group) but missing `pipeline_mode=` partition + **partial coverage**.
>
> All 6 buckets share the 2-tree shape (`{data_type}/…` + `raw_tick_data/…`). The trees hold the **SAME venues**
> (`curve`/`CURVE`, `aerodrome_v3`/`AERODROME_V3`, …) → **overlapping/duplicate data in different schemas + different
> coverage**, NOT complementary venues. The shipped `migrate_defi_full_v9_canonical.py` only parses the flat `day=` form
> (and my day-prefix listing missed `raw_tick_data/` + `dex_pools/` entirely) → it migrated ~10% and skipped ~90%. **The
> 2026-06-01 sharded run was STOPPED for this reason; nothing was deleted.**
>
> **C0-REDESIGN (operator 2026-06-01 — "audit it, figure out overlap/freshest schema, migrate once on v9, delete ALL old
> buckets+paths so data-status has ONE SSOT; stop missing things"):**
>
> **DEEPER DATA-STATE AUDIT (2026-06-01, slot-2) — SSOT `plans/audit/results/defi_c0_datastate_audit_2026_06_01.md`**:
> scope is materially deeper than "3 layouts". (a) **L1 path structure DIFFERS per bucket**: dex-pools/dex-swaps/
> lending-indices = `{dir}/{venue}/{chain}/date=`; perp-funding = `{dir}/{venue}/date=` (no chain); **lst-rates +
> oracle-prices = `{dir}/date=` only (no venue/chain in path)**. (b) **data_type NAME forks**: object-path
> `dex_pool_state`→`dex_pools`, `dex_pool_swaps`→`dex_swaps` (manifest + plan C2 canonical). (c) **venue-grain
> mismatch**: lst-rates objects store aggregate `venue=LST` but the manifest shards **per-protocol across 14 venues** →
> migration SPLITS objects by token/protocol→venue (UAC `LST_VENUE_TO_TOKENS`). (d) per-data_type COLUMN sets diverge
> materially; UAC `parquet_records.py` dataclasses are STALE. **Operator decisions (binding, this session)**: (1)
> **uniform schema = SUPERSET UNION (lossless)** — union of all observed data columns + v9 metadata, reindex every
> object, drop nothing; (2) **perp-funding = include in union + DERIVE funding_rate_long/short from raw L1 OI** via the
> handler formula `(long_oi−short_oi)/total_oi` (perp_funding_handler.py:951-971). Investigated: perp L1 raw-OI vs L3
> derived-funding = same data_type; OI unique to perp_funding within DeFi; GMX tvl/volume partially double-covered by
> dex-pools `venue=GMX`.
>
> - [x] ✅ [CODE] P0. C0-RD1 — **enumerate ALL THREE layouts** + per-bucket cell-key normalisation (path for
>       dex/lending; **row-split** by token/protocol/feed/chain for lst/oracle/perp whose L1 lacks venue/chain);
>       venue→UAC `_V{N}` via `to_canonical_venue`. **DONE — mtds@e14d656b** (ruff+basedpyright 0-err + helper
>       unit-tests green; GCS-facing dry-run is the VM gate). parent_epic: manifest_master.
> - [x] ✅ [CODE] P0. C0-RD2 — **dedup overlapping cells**: most-complete row set → freshest layer (L3>L2>L1) → latest
>       write ts; never two objects per canonical cell; complementary cells preserved. **DONE — mtds@e14d656b.**
> - [x] ✅ [CODE] P0. C0-RD3 — **SUPERSET-UNION v9 conform** (operator-chosen lossless): footer-discovered per-data_type
>       column union (`--phase discover`) + v9 metadata (schema_version=9/asset_group/pipeline_mode/source/available_at)
>       → reindex → identical column set across every output object regardless of source layout → write ONCE to
>       env-split `{stem}-prd-{pid}` canonical path
>       `raw_tick_data/by_date/day=/pipeline_mode=batch/asset_group=defi/venue=/chain=/instrument_type=/data_type=/…`;
>       perp funding-derive; unattributable rows→`_needs_attribution/` (never guess-then-delete). Perf-contract
>       conformant (ThreadPool/--workers/--start-end date-shard/idempotent/per-cell isolation). **DONE —
>       mtds@e14d656b.**
> - [x] ✅ [DATA] P0. C0-RD3b — **VM dry-run validation — GREEN** (in-region VM
>       `canonical-migration-defi-20260601-214111`, 2022-01 L1-heavy slice, pinned mtds@e14d656b). **0 errors, 0
>       UNRECOGNISED trees, `_needs_attribution=0` across ALL 6 buckets** (lst token→venue split, oracle CHAINLINK+chain
>       attribution, perp GMX→ARBITRUM default-chain all resolved every row). Authoritative superset unions: dex_pools
>       53 cols (EVM + Solana-AMM coexist), lending_indices 43, dex_swaps 31, perp_funding 20, lst_rates 17,
>       oracle_prices 17. Path convention confirmed
>       (`…/venue=BALANCER/chain=ARBITRUM/instrument_type=pool/data_type=dex_pools/balancer_ARBITRUM_2022-01-03.parquet`).
>       Dedup collapses multi-write-ts duplicates (dex-pools 2573→899 cells, lst 279→31). Walkthrough in operator chat.
>       Follow-up mtds@e46b5f6b adds per-phase timing + obj/s + LOUD error-exit for the apply run. parent_epic:
>       manifest_master.
> - [x] ✅ [CODE] P0. C0-RD3c — **oracle attribution + needs_attribution diagnostic — SHIPPED mtds@90aac6e1** (slot-2
>       2026-06-02). The full-range dry surfaced held rows the 2022-01 slice (RD3b) didn't: ~5,187 oracle (pre-chain
>       Chainlink) + ~917 lst. Migration tool now inverts
>       `oracle_prices_handler._CHAINLINK_FEEDS_BY_CHAIN`+`_PYTH_FEEDS` → `contract→chain` and fills blank-chain oracle
>       rows from the row `contract` (deterministic; addresses are chain-unique) + a dry-run DIAGNOSTIC enumerating
>       distinct unattributable `(contract,feed)`/`(token,protocol)` so the residual lst-token registry (UAC
>       `LST_VENUE_TO_TOKENS`) is closed from REAL data, not guessed. `_needs_attribution` stays HELD-never-guessed.
>       **Next: busy-week re-dry → read the diagnostic → add the enumerated lst tokens → re-dry to needs_attr≈0 (or
>       operator-ack) → THEN C0-RD4.** parent_epic: mtds_mdps_master.
> - [ ] [DATA] P0. C0-RD4 — **completeness + uniformity gate**: post-walk, assert canonical `-prd` distinct-cell count ≥
>       union of all 3 source layouts' distinct cells (per bucket); **exactly ONE schema (column set) per data_type
>       across ALL output objects** (no schema drift between cells of different source-layout origin); CF-1…CF-12 GREEN
>       on the rebuilt `-prd` `_index` (`audit_canonical_form.py`); `_needs_attribution/` count 0 OR operator-acked.
>       Only then is C-GREEN.
> - [ ] [DATA] P0. C0-RD5 — **delete ALL legacy** (every source bucket + every legacy path/tree) ONLY after C0-RD4
>       GREEN, so data-status/manifest shows a single canonical v9 SSOT (operator end-state). Snapshots retained.
> - [ ] [DATA] P0. C0-RD5b — **orphan sweep of the pre-existing legacy-FORM objects ALREADY in `-prd`** (slot/Harsh
>       bucket-state verification 2026-06-02). The `-prd` buckets were pre-seeded by an earlier env-split copy and hold
>       legacy-FORM objects (`day=/asset_group=defi/…`, NO `pipeline_mode=`; sample parquet cols lack
>       `schema_version`/`source`/`pipeline_mode`/`asset_group`). The C0 walk writes NEW canonical paths
>       (`day=/pipeline_mode=/asset_group=defi/…`), so those pre-existing `-prd` objects become ORPHANS → the C0e
>       consolidator rebuild would double-count or a non-`pipeline_mode`-aware reader reads stale. So C0-RD4/RD5 MUST
>       also delete the legacy-FORM objects sitting in `-prd` (not just the legacy SOURCE buckets). Measured 2026-06-02
>       (Cloud Monitoring `storage/v2/total_count`, live-object): `market-data-tick-defi-prd` 365,792 (~43% of legacy
>       855,497) + still carries legacy flat `dex_pools/{kamino,orca,raydium}/` trees (3-layout NOT consolidated);
>       `dex-pools-prd` 185,079 (~97%), `dex-swaps-prd` 68,764 (~99%) — all legacy-FORM. parent_epic: manifest_master.
> - [ ] [CODE] P1. C0-RD6 — **exclude the exact-alias columns from the `dex_swaps` superset union** (DeFi #4, from
>       archived `features_service_defi_data_loading_blockers`). Slot-7 DeFi #3 investigation confirmed `swap_count` ==
>       `trade_count` and `volume_quote_usd` == `volume` (intentional aliases populated in
>       `market_data_processing_service/app/adapters/defi/swap_adapter.py:159-160`). Dropping them is **lossless-in-
>       information** (no data lost — the values survive in `trade_count`/`volume`), so it is compatible with the
>       operator "lossless superset-union, drop nothing-of-value" rule. **Fold into the C0-RD3 union for `dex_swaps`
>       BEFORE C0-RD4 apply** (so the single canonical write omits the 2 dup cols — currently `dex_swaps` union = 31
>       cols → 29); if C0-RD4 has already applied, this becomes a scheduled post-C0 next-migration-window column cleanup
>       (no extra whole-corpus walk per single-walk discipline). Paired non-manifest edits: drop the 2 columns from UAC
>       `DEX_SWAPS_SCHEMA` + stop emitting them in `swap_adapter.py`. parent*epic: manifest_master. Repos:
>       unified-api-contracts + market-data-processing-service. **⚠️ BLOCKER FOUND 2026-06-02 (slot-2) — needs a schema
>       SPLIT, not a flat drop**: the candle-output `DEX_SWAPS_SCHEMA` is `_candle_contracts.py`
>       `_DEX_EXT = [swap_count, volume_quote_usd]`, but `_DEX_EXT` is **SHARED** — it is applied to BOTH
>       `swaps_ohlcv*{tf}`(dex_pool_swaps) AND`state*ohlcv*{tf}`(dex_pool_state)     via`extra_cols=\_DEX_EXT`(L375/L390/L401). The docstring says`dex_pool_state
>       → OHLCV(mid) +
>       swap_count`(state     legitimately keeps`swap_count`), so a flat drop of both cols from `\_DEX_EXT`would over-reach and strip    `swap_count`from`dex_pool_state`too. C0-RD6 therefore requires SPLITTING`\_DEX_EXT`into a swaps-ext (drop both     dup aliases) vs state-ext (keep`swap_count`only — note state never had`volume_quote_usd` per the docstring, so     there is also a pre-existing state/`\_DEX_EXT`inconsistency to fix). The swap_adapter`swap_count=`/`volume_quote_usd=`    emission was provisionally added then **reverted** by slot-2 (kept ONLY the A11c`dex_pool_swaps`re-registration)     so C0-RD6 can land as its own careful unit. Also still owed: the RAW migration superset-union exclusion (31→29) in    `migrate_defi_full_v9_canonical.py` `\_VENUE_SCHEMA["dex_pool_swaps"]`
>       before apply. DECOUPLED from the A11c landing.

### C0-CN — Canonical-naming reconciliation (operator-locked 2026-06-01) — SSOT `codex/02-data/defi-canonical-naming-ssot.md`

> A naming-alignment audit (codex + IS + MTDS + MDPS, 2026-06-01) found the migration would have regressed consumers (it
> normalised the on-disk `data_type` to the logical manifest name, and the live readers don't read `pipeline_mode=`).
> Operator directive: **converge on the canonical form, fix the readers/writers + plans + codex — do not bend the
> migration to legacy.** Locked canonical: path
> `…/day=/pipeline_mode={mode}/asset_group=defi/venue=/ chain=/instrument_type=/data_type=/…`; data_type
> `dex_pool_state`/`dex_pool_swaps` (collapsed ONE name everywhere, not the legacy on-disk-vs-manifest split) +
> `lst_rates`/`lending_indices`/`oracle_prices`/`perp_funding`; chain `HYPERLIQUID` (not `HYPERLIQUID_L1`);
> `instrument_type=perpetual` VALID for DeFi on-chain perps (Drift/GMX/HL); bare `venue=` + separate `chain=`; dedicated
> `{stem}-prd-` buckets. **Migration already conforms (mtds@6a8372b2).** **The apply is GATED on the reader fixes
> landing** (else migrated data is unreadable). Full status + sequencing: the codex SSOT above.

- [x] ✅ [CODE] P0. C0-CN1 — migration writes canonical (`dex_pool_state`/`dex_pool_swaps`, `pipeline_mode=` path,
      `HYPERLIQUID`, `perpetual`). mtds@6a8372b2 + codex `defi-canonical-naming-ssot.md`. parent_epic: mtds_mdps_master.
- [x] ✅ [CODE] P0. C0-CN2 — **MTDS handlers**: `dex_pools_handler._DATA_TYPE`→`dex_pool_state`,
      `dex_swaps_handler._DATA_TYPE`→`dex_pool_swaps` (both path + manifest), `pipeline_mode=` threaded into
      `write_defi_rows`/`build_defi_partition_path` (live=batch). **mtds@0a3a7071, QG green.** parent_epic:
      mtds_mdps_master.
- [x] ✅ [CODE] P0. C0-CN3 — **on-disk↔logical data_type remap dropped (now identity)**: mtds `defi_catalog_reader`
      `_ITYPE_TO_DATA_TYPE[POOL]`→`dex_pool_state` (mtds@0a3a7071); features `mtds_output_config._PATH_DATA_TYPE`
      identity + `_MTDS_OUTPUT_BUCKET_DOMAINS` rekeyed to `dex_pool_state`/`dex_pool_swaps` (features-service@dec1b687).
      No live consolidator remap existed. parent_epic: mtds_mdps_master.
- [x] ✅ [CODE] P0. C0-CN4 — **features-onchain reader pipeline_mode-aware**: `mtds_canonical_reader`
      `read_canonical_defi_parquets` probes `pipeline_mode=batch`→bare→`pipeline_mode=live`→legacy via UAC
      `build_defi_partition_path(pipeline_mode=)`; `_PATH_DATA_TYPE` identity. **features-service@dec1b687, QG green.**
      parent_epic: features_and_ml_master.
- [x] ✅ [CODE] P0. C0-CN5 — **MDPS reader pipeline_mode-aware + canonical data_type**: `orchestration_scanner`
      `_blob_matches_data_type_partition` accepts `dex_pool_state`/`dex_pool_swaps` (+ legacy) under
      `pipeline_mode={batch|live}` (day-prefix listing captures the segment). **mdps@4b9e6e5, QG green.** parent_epic:
      mtds_mdps_master.
- [x] ✅ [CODE] P0. C0-CN6 — **UAC**: `build_defi_partition_path(pipeline_mode=)` canonical (candidate_parquet_paths
      delegates); `to_canonical_chain_wire`+`CHAIN_WIRE_VALUE_OVERRIDES` resolve HL→`HYPERLIQUID` (non-breaking alias);
      `DEFI_ONCHAIN_INSTRUMENT_TYPES`+=`PERPETUAL`. **uac@dad96e42, QG green.** parent_epic: mtds_mdps_master.
- [x] ✅ [CODE] P0. C0-CN7 — **instruments-service: VERIFIED no change needed** — IS already produces DeFi `perpetual`
      InstrumentRecords (Lighter/etc. perp adapters) + the UAC validator already accepts `perpetual` (routed via the
      pair branch; UAC allowlist now also lists it); chain wire via UAC `to_canonical_chain_wire`; IS is
      data_type-agnostic for the tick universe. parent_epic: mtds_mdps_master.
- [x] ✅ [DOCS] P1. C0-CN8 — codex `02-data/defi-data-types-catalog.md` banner **resolves D14** (canonical
      `dex_pool_state`/`dex_pool_swaps`, NOT `dex_pools`; `pipeline_mode=` path; `HYPERLIQUID`; DeFi `perpetual`;
      EVM+Solana union) + cross-refs `defi-canonical-naming-ssot.md` (authoritative SSOT, already shipped). parent_epic:
      mtds_mdps_master.

- [ ] [DATA] P0. C0 **path + bucket canonicalisation (the foundational migration) — RUN ON A VM (operator-confirmed
      2026-06-01)**. **Two-tool lineage (system-first)**: Phase-1.8 `migrate_defi_canonical.py` already did
      VENUE-CHAIN→flat (C3), data*type canonicalisation (C2), `{NAME}_V{N}` promotion, instrument_type + canonical
      instrument_id — that step is DONE; the current dedicated-bucket objects are in the flat
      `day=/category=defi/venue={FLAT}/chain=/…` form. The C0/**v9** step is a NEW, separate read+rewrite tool —
      `market-tick-data-service/.../scripts/migrate_defi_full_v9_canonical.py` (**WRITTEN + launcher-wired 2026-06-01**,
      proper home beside the other
      `migrate*\*.py`; dry-run-able; ruff+parse clean; helpers verified) — that takes the     flat objects to FULL canonical: `category=defi`→`asset_group=defi`+`pipeline_mode={MODE}`partition +     schema_version=9 +`source`column (UAC SOURCE_PRIORITY) + canonical`\_V{N}` venue (UAC SSOT, complete incl     TraderJoe/Velodrome post-C12-UAC) + **`available_at`preserve-or-backfill** (preserve where present; backfill only     missing/null from day end-of-day UTC — never regenerate to migration-time) + env-split`{kind}-prd-{project}`
      bucket. mtds@a07cea55; launcher deployment-service@4484802. **Remaining = the C0a–C0f VM-cutover sub-todos
      below.** parent_epic: manifest_master. **The VM-cutover sequence is tracked as explicit sub-todos C0a–C0f below.**
  - [x] ✅ [SCRIPT] P0. C0-PROVISION — **5 dedicated DeFi `-prd` buckets PROVISIONED** (operator-authorized 2026-06-03,
        supersedes the "no new buckets/VMs" pause): `oracle-prices-prd`, `lst-rates-prd`, `lending-indices-prd`,
        `perp-funding-prd`, `gas-fees-prd` — all `*-prd-central-element-323112`, ASIA-NORTHEAST1, NEARLINE@90d +
        versioning + UBLA + prod labels. Via `terraform apply -target` against `terraform/state/prod` (clean-create:
        plan = 5 add / 0 change / 0 destroy; backend reset to dev after; `gcloud storage buckets describe` verified all
        5). `evm-defi-prd`/`solana-defi-prd`/`eigenlayer-rewards-prd` + `dex-pools`/`dex-swaps` `-prd` already existed.
        **Residual (P1)**: `liquidations-prd` is absent + has no TF resource (`liquidations_handler` resolves it via
        cloud-providers.yaml:186) → future liquidations backfills would fail-write; add the TF resource + apply. —
        deployment-service (TF resources applied). parent_epic: manifest_master.
  - [x] ✅ [CODE] P0. C0a — wire the tool into the launcher **DONE** (deployment-service@4484802;
        dry=default/full=--apply; `bash -n` + command-emission verified). Remaining: a `--start/--end` smoke on a 1-day
        slice (rolls into C0b dry VM).
  - [ ] [DATA] P0. C0b — **dry VM** (`launch-canonical-migration-vm.sh defi <start> <end> dry`) → review the planned
        rewrites in the VM log (sample legacy→canonical paths, venue canonicalisation,
        v9/source/pipeline_mode/available_at). **Discover-phase CORPUS SCOPING DONE** (local dry-run 2026-06-03,
        workers=32, read-only): 6 buckets / **~458,486 objects** / discover wall ~2.2h — dex-pools 191,451 (53 union
        cols), lending-indices 138,325 (43), dex-swaps 69,236, lst-rates 34,821 (17), oracle-prices 13,167, perp-funding
        11,486. Sharding/perf: dex-pools+lending+swaps ≈88% of objects → most date-shards/workers there; the launcher's
        date-shard + `--workers 96` + per-bucket-VM model fits; union cols vary (53/43/17) so v9 must union per-bucket.
        **`--phase all` migrate-PLAN dry-run VALIDATED** (local, lst-rates, 2026-06-04, clean network): planned_cells=96
        / objects_read=96 / cells_written=0 (DRY) / **0 errors / 0 needs_attr / 0 dedup_dropped**; sample PLAN cells
        (COINBASE/STADER/STAKEWISE/MARINADE...) correctly identified for canonical `pipeline_mode=batch/` rewrite +
        migrate=6.3s. Migrator dry-run confirmed end-to-end. Remaining = the full dry VM over ALL 6 buckets (operational
        C0b step) once the pre-migration drain (C0c) is scheduled.
  - [ ] [DATA] P0. C0c — **pre-migration drain (HARD RULE)**: stop GCP+AWS fleet (`vm_zombie_watchdog.py` inventory →
        per-prefix SIGTERM → wait STOPPED) + run consolidator + snapshot each in-scope `_index` to
        `_index/snapshots/pre_migration_2026_06_01.parquet`. Confirm the bucket-remediation DeFi seed is NOT mid-walk
        first.
  - [ ] [DATA] P0. C0d — **full VM** (`… defi … full`) → monitor (STARTED<60s, ≥1 progress/hr, STOPPED at exit, T+10min
        registry+describe RUNNING check). No fire-and-forget.
  - [ ] [DATA] P0. C0e — **consolidator re-run + verify**: rebuild `_index/availability_index.parquet`; assert
        schema_version=9 = 100% of rewritten rows, canonical `_V{N}` venues only (0 glued ghosts), `pipeline_mode=`
        partition present, `source` populated for multi-source cells; produce the per-venue/chain coverage table.
  - [ ] [DATA] P0. C0f — **delete legacy originals** after C0e verify GREEN (canonical objects confirmed; snapshot
        retained).
- [x] ✅ [CODE] P0. C12-UAC **UAC venue SSOT `_V{N}` everywhere FIRST** — `TRADER_JOEV2`/`VELODROMEV2` →
      `TRADER_JOE_V2`/ `VELODROME_V2`. **DONE 2026-06-01**: authoritative `PROTOCOL_CAPABILITIES.venue_prefix` +
      `ALL_DEFI_VENUES` + `LEGACY_DEFI_VENUE_ALIASES` (legacy glued bare + `-CHAIN` → underscore canonical) +
      `defi_protocol_registry` + `defi_venue_capabilities` + `chain_env`/`venue_mapping` launch dates +
      `expected_coverage` docstrings + `_defi_coverage` ghost set (+`TRADER_JOEV2`/`TRADERJOEV2`) +
      `instrument_validation` + regenerated `ui-reference-data.json`; tests flipped (37 venue + 69 related green).
      **Write-time consumers** (slug→venue maps that emit the venue string into data/manifest) also fixed so NEW writes
      are canonical: IS `orchestrator.py`/`factory.py` + MTDS `_instruments_metadata.py`. Reverses DF-17 glued-canonical
      (operator "TRADER_JOEV2/VELODROMEV2 is wrong"). — uac@6261bea2 + instruments-service@ce85abb1 + mtds@a07cea55.
      parent_epic: manifest_master.
- [x] ✅ [CODE] P0. C12-WIRE **wire `migrate_defi_full_v9_canonical` into `launch-canonical-migration-vm.sh defi`**.
      **DONE 2026-06-01**: launcher `defi` runs the v9 tool (complete canonical `_V{N}` incl TraderJoe/Velodrome
      post-C12-UAC); mode convention dry=tool-default / full=`--apply`; `bash -n` + command-emission verified. Also
      fixed the MISLEADING "no-underscore canonical" docstring in `migrate_mtds_defi_legacy_venue_underscore.py` (UAC
      keeps underscores; transform is flat→combined VENUE-CHAIN). — deployment-service@4484802 + mtds@6dd8d8a1.
      parent_epic: manifest_master.
- [ ] [CHORE] P2. C13 **move misplaced migration scripts** out of `plans/audit/results/` (PM docs dir) into
      `market-tick-data-service/scripts/` (the runnable ones: oracle_relabel / chain_genesis / venue_launch /
      phantom_captured / captured_pre_existence / captured_vs_objects / index_venue_canonicalise / object_path); the
      `.md` audit RESULTS + the coverage QUERY stay. parent_epic: manifest_master.
- [x] ✅ [DATA] P0. C1 oracle-prices index relabel + Pyth dedup — **APPLIED 2026-06-01** via
      `plans/audit/results/defi_oracle_relabel_migration_2026_06_01.py --apply`: 728 pre-genesis relabel →
      `EXPECTED_PRE_GENESIS_CHAIN`; Pyth 1,185 chain `''`→`SOLANA` + dropped 1,034 dup empties; 9,717→8,683 rows; PYTH
      now all `chain=SOLANA` (1,447 = 1,185 captured + 262 owed). Original snapshotted →
      `_index/snapshots/pre_relabel_2026_06_01.parquet`. Fixes the consolidated index; durable until a full consolidator
      rebuild (which needs the source rows fixed too — the bundled C2–C7 walk). Writer A1 makes future writes correct.
- [ ] [DATA] P1. C2 data_type alias dedup across buckets — **canonical is the ON-DISK form (operator-locked 2026-06-01,
      see C0-CN + codex `defi-canonical-naming-ssot.md`)**: hyphen→underscore (`lending-indices`→`lending_indices`),
      `staking_yields`→`lst_rates`, and the pool/swap data_type collapses to `dex_pool_state`/`dex_pool_swaps`
      EVERYWHERE (NOT the logical `dex_pools`/`dex_swaps` — that was the regression the naming audit caught). Rides the
      C0 walk (the migration already writes `dex_pool_state`/`dex_pool_swaps`). ONE walk.
- [ ] [DATA] P1. C3 VENUE-CHAIN→flat: legacy `UNISWAPV3-ETHEREUM` venue strings → flat `venue` + populated `chain`. Same
      walk.
- [ ] [DATA] P1. C4 schema v4–v8 → v9 re-version across the dedicated DeFi buckets. Same walk. parent_epic:
      manifest_master.
- [ ] [DATA] P1. C5 phantom-grid delete: remove the cartesian `data_type × venue` empty grid in `market-data-tick-defi`;
      point data-status at the dedicated indexes.
- [ ] [DATA] P2. C6 Pyth ~5-week backfill (2026-04-15→present, Hermes API) on a VM. **GATED on C0/C-GREEN** (backfill
      into the canonical env-split/`pipeline_mode`/`asset_group=` structure, never the legacy layout).
- [x] ✅ [DATA] P2. C7 reason relabel — chain-genesis portion APPLIED 2026-06-01 (warmup-retry fix landed it locally) —
      `plans/audit/results/defi_chain_genesis_relabel_migration_2026_06_01.py` (snapshot-protected, idempotent,
      `get_chain_genesis_date`-driven). Dry-run across all dedicated buckets: oracle ✅ done (C1, 728 rows); **lst-rates
      75 rows (SOLANA pre-2020-03-16) pending** — apply kept failing on flaky LOCAL GCS DNS (lst-rates/lending-indices
      time out); lending/perp/dex already clean on chain-genesis. **Run this on a VM in asia-northeast1** (stable
      in-region network) to land lst-rates. **Pre-VENUE-launch portion** (PACIFICA/ASTER/ETHERFI/LIDO/MARINADE
      pre-launch) stays blocked on A2a (`DEFI_VENUE_LAUNCH_DATES` populated) — bundle into the C2–C4 walk.
- [ ] [DATA] P1. C8 fill manifest under-enumeration: UAC declares 90 defi venue-keys but manifest enumerated only lst
      14/22, lending 6/21, perp 5/8; genuine absentees DRIFT-SOLANA (Solana MVP), FRAX, MORPHO, FLUID. parent_epic:
      defi_master.
- [ ] [DATA] P1. C9 legacy DeFi bucket object paths are pre-canonical —
      `day=/category=defi/venue=/chain=/instrument_type=/data_type=/file.parquet`: **`category=` not `asset_group=`**
      AND **no `pipeline_mode=` partition** (canonical raw_tick_data layout is
      `…/day=/pipeline_mode={mode}/asset_group={ag}/…`). The manifest ROWS carry pipeline_mode (handlers pass it); the
      object PATHS don't. Normalise the dedicated DeFi bucket paths in the same single-walk as C2–C4. parent_epic:
      manifest_master.
- [x] ✅ [DATA] P0. C10 **bad start dates — phantom captured-pre-genesis fix APPLIED 2026-06-01**
      (`plans/audit/results/defi_phantom_captured_pre_genesis_fix_2026_06_01.py --apply`): **8,477** index rows falsely
      marked `captured` for a (chain, date) before the chain's UAC genesis (no backing objects — verified) →
      `empty_confirmed/EXPECTED_PRE_GENESIS_CHAIN`. dex-pools 8,410 (BASE 4,750 / ARBITRUM 1,452 / OPTIMISM 1,396 /
      ZKSYNC 812), dex-swaps 61, oracle 6. Snapshotted. Removes the false-captured coverage inflation. parent_epic:
      manifest_master.
- [x] ✅ [DATA] P0. C10b **captured-pre-VENUE-launch fix APPLIED 2026-06-01**
      (`plans/audit/results/defi_captured_pre_existence_fix_2026_06_01.py --apply`): **401** more captured rows dated
      before the VENUE launched (UAC `DEFI_VENUE_LAUNCH_DATES`) → `empty_confirmed/EXPECTED_PRE_VENUE_LAUNCH` (dex-pools
      GMX-AVALANCHE 370 / GMX-ARBITRUM 1, lst-rates ETHENA 29 / ROCKETPOOL 1). Snapshotted. **Combined with C10: all
      8,878 date-impossible captured rows (pre-chain-genesis + pre-venue-launch) are now corrected — no more bad
      pre-genesis/pre-launch labelling.** parent_epic: manifest_master.
- [ ] [DATA] P0. C11 **deeper phantom audit — are the POST-launch dex `captured` rows object-backed?** Date-impossible
      ones are done (C10/C10b); the remaining question is whether post-launch captured rows have real objects.
      Spot-check 2026-06-01: `dex-pools day=2025-06-01` HAS objects ✅ but `day=2024-01-01` returned 0 (inconclusive —
      read flaked). The uniform `2021-01-01` first-captured still warrants a full **captured-vs-objects walk**
      (dex-pools/dex-swaps), relabeling any captured row with no object honest. **NOTE 2026-06-01**: an initial walk
      falsely reported 74% phantom — that was an index-venue↔object-venue MISMATCH (`UNISWAPV3` vs `UNISWAP_V3`), now
      fixed for those venues by C12. Re-run the walk AFTER C12 lands everywhere, WITHOUT any read-path normalisation.
      **VM job** (object listing at scale). parent_epic: manifest_master.
- [~] [DATA] P0. C12 **venue-name `{VENUE}_V{N}` canonicalisation — EVERYWHERE (code + manifest + data + docs)**
  (operator 2026-06-01: "switched to canonical form with `_V2` etc everywhere … TRADER_JOEV2/VELODROMEV2 is wrong").
  Canonical = underscore before the version (`UNISWAP_V3`, `TRADER_JOE_V2`, `VELODROME_V2`, `AERODROME_V3`, …).
  Surfaces: - **UAC** (the SSOT — fix first): `registry/defi_venues.py`, `defi_venue_capabilities.py`,
  `defi_protocol_registry.py`, `expected_coverage.py`, `venue_mapping.py`, `chain_env.py`,
  `capability_declarations/_defi*.py`, `internal/reference/instrument_validation.py` + the `canonicalize_defi_venue`
  function + its tests (`test_venue_key_parity.py`, `test_canonicalize_defi_venue_combined.py`).
  `TRADER_JOEV2`→`TRADER_JOE_V2`, `VELODROMEV2`→`VELODROME_V2` (and confirm all `*V{N}` use the underscore). - **Code
  (writers)**: MTDS `_instruments_metadata.py` + any handler that emits a venue string. - **Data (objects)**: rename
  object paths `venue=TRADER_JOEV2`→`TRADER_JOE_V2` etc. — VM single-walk (bundle with C0). - **Manifest index**:
  `dex-pools`/`dex-swaps` index — DONE for the already-underscore venues (UNISWAP_V3 39,355 + dex-swaps); TODO
  TRADER_JOE_V2/VELODROME_V2 (coordinate with the object rename so index==object). - **Docs**:
  `codex/02-data/availability-manifest-and-data-status.md`, `contracts-scope-and-layout.md`, etc. Coordinated cross-repo
  migration (all surfaces together; objects = VM). parent_epic: manifest_master.

## D. Features propagation (L3) — coverage must reach features-service

- [ ] [DATA] P0. D1 features-onchain-defi is near-empty (3 rows); features-delta-one-defi + features-volatility-defi
      have NO index → derived features (staking*apy_bps/funding_rate_apy_bps/basis_bps/realized_vol*\*) absent. Run the
      features backfill for the in-scope DeFi instruments over the captured window. **GATED on C-GREEN** (features must
      read canonical raw, else they inherit the mess). parent_epic: features_and_ml_master.
- [ ] [DATA] P1. D2 **MDPS swaps_ohlcv reprocess for the stale chain-column `attempted_failed` rows** (MIGRATED FROM
      archived `issues/uniswap_v3_ethereum_28k_attempted_failed_2026_05_28.md`, slot-2 2026-06-02). 28,634
      `UNISWAP_V3-ETHEREUM` `swaps_ohlcv_*` rows on the **consolidated `market-data-tick-defi` `_index`**
      (`processed_candles` layer) are `attempted_failed`/`SCHEMA_VALIDATION_FAILED` — **stale point-in-time records**
      from the 2026-05-23/24 chain-propagation fix-deploy window (root cause = blank `chain`; the canonical migration
      removes it source-side). Code fix already live (`mdps@7f1a5b5`+`3799c8d`); slot-7 pre-flight verified live candles
      now carry `chain`. **No code change** — needs an MDPS reprocess rerun once our C0 canonicalises the source (rows
      flip `captured`). Companion chain-column venues to reprocess in the SAME pass (do NOT race the migration with a
      one-venue VM): UNISWAP_V2-ETHEREUM 3,444 · AAVEV3-OPTIMISM 2,820 · EIGENLAYER 1,311 · CURVE-ETHEREUM 1,281 · MAKER
      1,113 · FRAX 1,032 · DRIFT-SOLANA 200 · KAMINO/JITO/MARGINFI ~75. **GATED on C-GREEN.** Verify post-retry:
      `attempted_failed` for these venues → 0 (now `captured` or legit `empty_confirmed`). Repos:
      market-data-processing-service. parent_epic: mtds_mdps_master.

## E. CeFi perp leg (hybrid hedge) — fix-fetch

- [ ] [DATA] P0. E1 CeFi `derivative_ticker` (funding carrier) fetch failures: OKX-FUTURES + ASTER 100%
      attempted_failed; refresh to current (stale ~3–5 weeks). parent_epic: cefi_master.

## F. Docs / SSOT — record canonical forms

- [ ] [DOCS] P1. F1 `codex/02-data/defi-data-types-catalog.md`: underscore-canonical data_type names + dedicated bucket
      per type + hyphen aliases deprecated.
- [ ] [DOCS] P1. F2 `codex/02-data/availability-manifest-and-data-status.md` + `data-status-drilldown.md`: document the
      materialised `expected_unattempted` 4-state + the manifest-annotates-once/consumers-read principle + per-chain
      requirement.
- [ ] [DOCS] P2. F3 `_defi_manifest.py` reason-labeling docstring (~L213-220 "future refinement" TODO) → mark
      pre-genesis done (A1); note pre-launch (A2).
- [ ] [DOCS] P2. F4 CLAUDE.md "Manifest + honest absence" note: `expected_unattempted` is materialised at consolidation
      from the oracle; consumers read, never re-derive.

## G. Solana basis MVP — operationalisation (migrated from archived `solana_basis_trading_mvp_2026_06_01.md`)

> **Migrated 2026-06-01** from `plans/archive/solana_basis_trading_mvp_2026_06_01.plan.md` (Phases 1–4 code SHIPPED;
> these 4 follow-ups are the operationally-shipped half per CLAUDE.md "Plans Run To Actual Completion"). The Solana MVP
> plan documented: Drift V2 historical ingester + 4 Solana spot DEX ingesters (Orca/Raydium/Phoenix-stub/Jupiter)
>
> - 7 canonical UAC data types (PERP_TRADES, PERP_MARK_ORACLE, PERP_OPEN_INTEREST, DEX_POOL_STATE, DEX_ORDERBOOK,
>   DEX_QUOTE, DEX_TRADES) + `InstrumentType.DEX_POOL` + `SolanaBasisGcsLoader` wiring into the existing
>   `CARRY_BASIS_PERP@raydium-drift-sol-1h-sol-v5-prod` archetype + `--live --continuous` flag (the concrete realization
>   of CLAUDE.md "Live = batch" hard rule).
>
> All four operator-launched follow-ups (G1–G4) must land in **canonical structure** (env-split bucket +
> `pipeline_mode=` partition + `asset_group=defi`) — so they are **GATED on C-GREEN for the dedicated DeFi buckets that
> hold the Solana writes** (`market-data-tick-defi-prd-…` for perp_funding/perp_trades + dedicated `dex-pools-prd-…` /
> new `dex-pool-state-prd-…` / `dex-orderbook-prd-…` / `dex-quote-prd-…` if those are split per A1 SSOT). If the
> dedicated bucket for a Solana data_type doesn't exist yet, that's a **bucket provisioning** prerequisite (file under
> C0 / `cloud-providers.yaml`) — not a license to write to the legacy `market-data-tick-defi-${PID}` (no env, no
> pipeline_mode) path.

| Dep                        | Item       | Owner    | Verification                                          |
| -------------------------- | ---------- | -------- | ----------------------------------------------------- |
| (a) before (b) → (c) → (d) | sequential | operator | each gated on prior step's manifest-verified evidence |

- [ ] [DATA] P0. G1 Launch the full 2024-06-01 → 2026-06-01 backfill VM (Drift V2 historical + Solana spot DEX state).
      Operator-launched from laptop OR `vm-defi`. Recipe: the four CLI scripts in
      `market_tick_data_service/scripts/backfill_drift_v2_historical.py` (perp_funding + perp_trades) +
      `backfill_solana_dex_state.py` (Orca Whirlpool + Raydium classic AMM) for each day in window; estimated ~36GB
      total payload across the 730-day window. **GATED on C-GREEN for the dedicated DeFi buckets** that hold these
      writes (env-split + `pipeline_mode=batch` + `asset_group=defi`). Verification (per CLAUDE.md "Plans Run To Actual
      Completion"):
      `gsutil ls gs://market-data-tick-defi-prd-${PID}/raw_tick_data/by_date/day=*/pipeline_mode=batch/asset_group=defi/venue=DRIFT/chain=SOLANA/instrument_type=perpetual/data_type=perp_funding/`
      returns a parquet per day in window; sample-inspect 3 random parquets (early/mid/late window) for non-empty
      `funding_rate`, `oracle_price_twap`, `mark_price_twap` columns; manifest-verified row count > 0 per day-shard;
      equivalent checks for `perp_trades` (active days only; allow `empty_confirmed[SOURCE_RETURNED_ZERO]` on quiet
      days) + `dex_pool_state` for Orca + Raydium. **No silent gaps**: any day with 0 rows MUST carry a typed
      `empty_confirmed` reason (not `attempted_failed`). parent_epic: mtds_mdps_master. **Operator-launched (long
      wall-clock; not a dispatch).**
- [ ] [DATA] P0. G2 Launch live-mode snapshotters via `--live --continuous` (mtds@1d35c7f2 unified live/batch path).
      Terminal A:
      `python -m market_tick_data_service.scripts.backfill_drift_v2_historical --markets SOL-PERP --live     --continuous --interval-seconds 3600 --data-types funding`
      (hourly). Terminal B:
      `python -m market_tick_data_service.scripts.backfill_solana_dex_state --venues orca,raydium --live --continuous     --interval-seconds 60 --samples-per-day 60 --data-types pool_state`
      (1-min). These run as long-lived VMs on `vm-defi` (lifecycle_class=LONG_LIVED_LIVE per CLAUDE.md vm naming SSOT).
      **GATED on G1** (need backfilled history to be loadable as warmup) + **C-GREEN** (writes target canonical
      structure). Verification (per CLAUDE.md "Plans Run To Actual Completion"): T+5min check post-launch — both VMs
      RUNNING in `gcloud compute instances describe`; ≥1 parquet under
      `day=<TODAY>/pipeline_mode=live/asset_group=defi/…` within the first interval (1 min for DEX, 1 h for Drift
      funding); manifest `capture_status=captured` rows generated. Symptom of regression: `SolanaBasisGcsLoader` logs
      `no perp_funding rows for live`. Depends on G1 (backfill warmup) before paper trade can run a meaningful history.
      parent_epic: mtds_mdps_master. **Operator-launched.**
- [ ] [PLAY] P0. G3 Run 24h paper trade via `e2e-testing/scripts/defi/run-paper.sh --strategy SOL_BASIS`. Recipe:
      `bash     cd e2e-testing && bash scripts/defi/run-paper.sh --strategy SOL_BASIS --tick-interval 3600 --continuous \         --execution-provider solana-devnet --initial-capital-usd 100000     `
      Engine flows `--strategy SOL_BASIS` → `colocated_engine.py` → `SolanaBasisGcsLoader` → fill-sim on devnet (signed,
      not broadcast). **GATED on G2** (live data must be flowing so the engine reads a non-stale tape). Verification
      (per CLAUDE.md "Plans Run To Actual Completion" + Promote Workflow Path SSOT): 24h wall-clock session writes a
      non-empty trade log + PnL series; Firestore `MinimalCandidateManifest` populated; Sharpe ratio + realised funding
      earnings − slippage computed; sample-inspect 3 trades for honest fill simulation (no NaN/inf, no fictional fills
      against zero-liquidity ticks); manifest path `gs://market-data-tick-defi-prd-${PID}/paper_trade/…` (or whichever
      sink the engine writes to) has the session's full output. **DART `ManualTradeGateDialog` enforces first-3-days
      hand-confirmation per CLAUDE.md Promote Workflow Path.** parent_epic: mtds_mdps_master. **Operator-launched (long
      wall-clock; not a dispatch).**
- [ ] [HUMAN] P0. G4 Promote to live wallet — **HUMAN-ONLY per CLAUDE.md hard-stop list**
      (`## Plans Run To Actual     Completion`: wallet keys + kill-switch arming are human-only; agent never runs
      `run-live.sh`). Valid promote target per CLAUDE.md Promote Workflow Path is `paper_1d → live_early`; `live_full`
      is post-cutover. Operator runs:
      `bash     cd e2e-testing && bash scripts/defi/run-live.sh --strategy SOL_BASIS --tick-interval 3600 --continuous \         --execution-provider <copper|ceffu|cloud_kms_encrypted> --capital <amount> --wallet <KMS_KEY_ALIAS>     `
      **GATED on G3** (Sharpe-positive ack required) + **C-GREEN** + **G2 live data flowing**. Verification: real wallet
      ≥7-day session per CLAUDE.md Master Plan (live DeFi 2026-05-23 gate already shipped — this is a
      Solana-archetype-specific operational gate, not a master-plan blocker). The agent **never** ticks G4 — the
      operator does after the live run completes. parent_epic: mtds_mdps_master.

### G5–G8 — post-MVP feature follow-ups (migrated 2026-06-01 from archived MVP plan body)

> **MIGRATED FROM** `plans/archive/solana_basis_trading_mvp_2026_06_01.plan.md` § "Phase 2 deferred / P1 follow-ups".
> These were orphaned in the archive body — not picked up by the inventory regenerator, not in canon §G's G1–G4
> operational chain. Restored to active inventory here so backlog-derivation crons + done-vs-left dashboards pick them
> up. None are MVP-blockers (G1–G4 are sufficient to ship the basis trade); these are post-MVP feature additions and
> depth-of-data improvements.

- [ ] [CODE] P1. G5 **Phoenix radix-slab decode (top-of-book bid + ask + size).** The market account is 1.7MB; the
      top-of-book decode is ~50-100 LOC of binary parsing against Phoenix's documented slab layout. Full L2 (deeper
      levels) is harder + can ship later. Current state: `PhoenixOrderbookIngester` (mtds@d3d26f56) fetches the market
      account successfully (proves the RPC path) but routes via
      `record_failed(reason="SOURCE_HANDLER_TODO_PHOENIX_DECODE")`. Acceptance: top-of-book parsed;
      `best_bid_price + best_ask_price + their sizes + spread_bps + mid_price` populated; `record_captured` instead of
      `record_failed`; 5+ unit tests cover the binary decode against known slab states. parent_epic: mtds_mdps_master.
      Not GATED on G1–G4 (independent feature add).
- [ ] [CODE] P2. G6 **Jupiter historical reconstruction.** `JupiterQuoteIngester` (mtds@d3d26f56) is forward-only —
      Jupiter doesn't expose historical quote endpoints. For the 2024-06-01 → today backtest window, reconstruct
      historical Jupiter routes by simulating Jupiter's routing algorithm against the underlying Orca/Raydium pool
      states at the same timestamps. Acceptance: per (timestamp, size-bucket) row matching forward-collected quote
      structure within ±5%; backtest harness can read Jupiter quotes for any day in window. parent_epic:
      mtds_mdps_master. GATED on G1 (need Orca + Raydium pool states backfilled).
- [ ] [CODE] P2. G7 **Orca tick-array decode** (concentrated-liquidity depth visualisation). Current MVP uses
      `sqrt_price` + `liquidity` scalars (sufficient for next-tick slippage approximation). Full tick-array decode
      enables tick-distribution depth maps + better mid-size-fill simulation. ~150-200 LOC binary parsing of the 3
      nearest tick arrays around `tick_current_index`. Acceptance: per-snapshot tick array state captured alongside pool
      state; downstream consumers can compute fill slippage at arbitrary sizes. parent_epic: mtds_mdps_master. Not GATED
      on G1–G4 (independent depth improvement).
- [ ] [CODE] P2. G8 **Raydium second WSOL/USDC pool** — extend `RaydiumClassicAmmIngester` defaults if a meaningful TVL
      pool materialises. The plan-time secondary Raydium pool dropped to $4.6K TVL by 2026-06-01 (below noise
      threshold); current default ingestion is just the top $8.8M pool. The constant scaffold is forward-compat — adding
      a pool requires only updating `_RAYDIUM_POOLS` dict. Acceptance: if a second SOL/USDC Raydium pool reaches > $1M
      TVL, add it; ingest from the canonical date; backtest harness reads both. parent_epic: mtds_mdps_master. Trigger:
      TVL probe shows > $1M.

### G — non-conflict notes (from conflict scan 2026-06-01)

- `solana_defi_legacy_migration_2026_05_27.md` (active): canonical Solana types per that plan are
  `dex_pools`+`SOLANA_AMM_POOL` (Kamino vault METADATA snapshot) vs the MVP's `DEX_POOL_STATE` (Orca/Raydium AMM STATE
  time-series for fill-sim) — **complementary, not conflicting** (different shard grain, different consumers, different
  UAC contracts). Both flow through the same dedicated-bucket SSOT (`get_write_bucket_name`); the new `DEX_POOL_STATE`
  writes target their own dedicated bucket once provisioned (C0 prerequisite).
- `plans/active/issues/bug_d_prime_drift_backfill_2026_05_31.md`: SUPERSEDED 2026-06-01 (the Helius sig-walking path
  that issue documents is OBSOLETE — Drift V2 historical now flows via `data.api.drift.trade` Velocity Data API per the
  archived MVP plan + new codex `codex/04-architecture/drift-v2-data-sources.md`). Issue doc gets a SUPERSEDED banner in
  the same archival commit.

## H. DeFi slices of the per-service plans (claimed via the five-slot asset-group split, operator 2026-06-03)

> These are the **DeFi-asset-group slices** of the two per-service canonicalisation plans. Under the five-slot split
> they ride **slot 2** (this lane), not the per-service plans' nominal `vm-cross-cutting` / `vm-ml`. Tracked here as
> real `- [ ]` items (not a referenced-but-unowned gap). Coordinate read-only with the other AG slots on shared helpers;
> never edit another AG's slice of those plans.

- [ ] [DATA] P0. **`instruments-store-defi` reference-surface canonical-form walk** (the DeFi slice of
      `instruments_manifest_canonicalisation_2026_06_01.md`, whose §C excludes defi). Phase-0 layout audit → single
      bundled walk on the `instruments-store-defi` `_index` + objects to v9 + `asset_group=` + `pipeline_mode=`
      partition + `source` column + typed `EmptyConfirmedReason`, same target form as the MTDS DeFi C0 walk. Re-run
      CF-1…CF-12 → GREEN before any DeFi instruments writer relaunch (master L3-gates-L5). NEVER a second walk on this
      `_index`.
- [ ] [CODE] P1. **DeFi downstream reader confirm** (the DeFi slice of
      `downstream_services_manifest_canonicalisation_2026_06_01.md` PREP3): confirm the MDPS candle-builder raw-tick
      read + features-onchain `data_loader` resolve the `pipeline_mode=` path PRIMARY for DeFi (writer side already
      shipped mdps@4b9e6e5 + features@dec1b687). Close the PREP3 "🟡 reader slot-2 coordination" note for DeFi.
- [ ] [CODE] P2. **FLAG 2 — `_BUCKET_CATEGORY_OVERRIDES` DeFi scope** (the DeFi slice flagged to slot-2 in the
      downstream plan): a DeFi `category` override absent from `cloud-providers.yaml` / unresolved by
      `resolve_bucket_name` → post-delete silent-empty. Resolve with
      `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` L6 (owns the bucket-name SSOT + the actual delete).

## Verification (full-execution criterion)

Re-run `plans/audit/results/defi_strategy_coverage_query_2026_06_01.py` + the drilldown: every DeFi cell carries a
canonical data_type (underscore), flat venue + populated chain, v9 schema, a typed reason, **a populated `source` (HARD
— zero blank on every external cell; the 2 multi-source cells `oracle_prices`=pyth+chainlink /
`native_staking_rates`=solana_rpc+helius_rpc emit two rows — closes `data_source_provenance` DeFi Phase 2)**;
`expected_unattempted` materialised so `% captured = captured / (captured+empty+failed+expected_unattempted)`;
coverage-summary == drilldown == manifest-status denominators; features-onchain-defi populated for the in-scope window;
**Solana basis MVP G1–G4 operationally-shipped (G4 human-only)**; the next audit needs one pass.

> **🟡 DRAINED-WRITER DEPENDENCY (2026-06-01)** — the legacy-bucket SSOT remediation drained writer VMs
> `mdps-backfill-defi` / `mdps-prediction-2025` / `sports-scheduler`. They must NOT be relaunched until the
> legacy→canonical migration + manifest work complete. SSOT + relaunch gate:
> `plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` Phase 4.

> **🟡 CROSS-PLAN ISSUES/BLOCKERS (2026-06-01, from bucket_name_ssot_legacy_dual_write_remediation)**:
>
> 1. **Tarball-prune blocker** — `C0 — RUN ON A VM` is exposed to the pinned-tarball prune race: a VM can pull stale
>    `mtds-code.tar.gz` and run wrong code / exit-2 silently. SSOT:
>    `plans/active/issues/pinned_tarball_prune_breaks_vm_deploys_2026_06_01.md`. Verify the VM ran the intended sha
>    before trusting C0 output.
> 2. **DeFi `_index` single-walk ordering (HARD)** — the bucket-SSOT remediation seeds legacy→canonical rows into the
>    SAME `market-data-tick-defi-prd-…` `_index` this plan's C0 rewrites. The remediation seed must run BEFORE C0 (so C0
>    canonicalises the seeded legacy rows: old venue strings / v4–v8 / phantom grid). Do NOT run C0 while the
>    remediation DeFi seed is mid-walk, and vice-versa. `data_source_provenance_…` rides C0 (no third walk).

## ⑦ Coverage-denominator could-exist seed — cross-AG note (filed by slot-5 2026-06-04)

> Operator 2026-06-04 (point ⑦): the deployment-api/ui coverage **denominator** must reflect the **could-exist
> universe** (instruments/fixtures that exist in IS but whose backfill has NOT run), not just rows that exist in the
> manifest. **The seeding mechanism already exists** — `instruments-service/scripts/enumerate_expected_universe.py` (v2
> expected-universe enumerator) cross-joins the IS catalog × dates × data_types, subtracts existing manifest rows, and
> seeds `record_expected_unattempted` for the residual; deployment-api `data_status_hierarchical` already counts
> `expected_unattempted` in the 4-state denominator. Slot-5 fixed the cross-cutting blocker: the enumerator's default
> bucket map was stale for ALL 5 AGs (missing the `-prd-` env tier) → now resolves via `resolve_bucket_name`
> (instruments-service, ⑦ in `prediction_manifest_canonicalisation_2026_06_01.md`). **Remaining for defi:**

- [ ] [CODE] P1. ⑦ defi could-exist denominator seed — build the `--catalog-path` parquet from the defi IS catalog
      (per-instrument lifecycle: `instrument_id`/`instrument_type`/`venue`/`available_from`/`available_to`) and run
      `enumerate_expected_universe.py --asset-group defi --catalog-path <catalog> --apply-write` against the canonical
      `_index` so the raw-tick denominator == could-exist universe (active-but-uncaptured instruments seeded
      `expected_unattempted`). Verify on a VM (GCS flaky locally); confirm `_enumerate_v2_defi` row-key/data_types match
      the defi captured atom; add a regression (IS-universe ⊃ manifest ⇒ denominator doesn't shrink). The mechanism +
      bucket fix are done; this is the per-AG catalog build + run + verify. parent_epic: mtds_mdps_master.
