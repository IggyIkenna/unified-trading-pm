---
title:
  "Downstream data-pipeline services manifest canonicalisation (MDPS / features / strategy / execution) — audit-first,
  low-data single-walk"
created: 2026-06-01
author: ikenna
parent_epic: epics/mtds_mdps_master.md
assigned_vm: vm-ml
status: active
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
locked_by: live-defi-rollout
locked_since: 2026-06-01
related_plans:
  - plans/epics/features_and_ml_master.md
  - plans/epics/strategy_master.md
  - plans/epics/execution_master.md
source:
  - defi_manifest_canonicalisation_2026_06_01.md §MASTER (per-service canonicalisation axis — downstream uncovered)
  - canonical_form_cross_service_audit_checklist.md (CF-1…CF-12)
master: defi_manifest_canonicalisation_2026_06_01.md (cross-plan canonical-SSOT coordinator)
---

# Downstream data-pipeline services manifest canonicalisation (MDPS / features / strategy / execution)

> **MASTER**: `defi_manifest_canonicalisation_2026_06_01.md` §MASTER (L3, per-service axis). The data pipeline is
> `instruments → MTDS → MDPS → features → strategy → execution`. The per-AG plans cover MTDS; `instruments_manifest_…`
> covers the input side. THIS plan covers the four **downstream** services whose `_index`(es) carry the same
> canonical-form debt. **Operator 2026-06-01**: "we haven't run much data for MDPS / features / strategy / execution, so
> those should be fairly quick — but still should be audited and in plans." So this plan is **audit-first**: read each
> service's actual `_index` state (small corpus → fast), then bundle any debt into ONE single-walk per bucket.

## Per-service scope + what each owns / inherits (no overlap)

| Service       | Surface                                                  | CF items it OWNS (live check)                                       | Notes                                                                                                                                                                          |
| ------------- | -------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **MDPS**      | `processed_candles/` (in the AG tick buckets)            | CF-1,2,3,5,8,9,11,12; **CF-4 source PROPAGATED** from the raw cell  | Per-AG plans already COPY `processed_candles/`; this plan ensures the canonical FORM + source propagation are audited there. Coordinate — no second walk on an AG tick bucket. |
| **features**  | `features-{onchain,delta-one,volatility,…}-{ag}`         | CF-1,2,3,5,8,9,11,12; **CF-4 EXEMPT** (computed — no vendor source) | defi §D backfill is the data; this plan is the FORM + exempt-source audit. CF-6 propagates upstream `expected_unattempted`.                                                    |
| **strategy**  | strategy output `_index` (signals / candidate manifests) | CF-1,2,5,8,9,12; **CF-4 EXEMPT** (computed)                         | Little data run → quick. CF-3/CF-10/CF-11 n/a (no raw fetch / no on-disk pipeline_mode).                                                                                       |
| **execution** | execution-record `_index` (fills / transfers / ledger)   | CF-1,2,5,8,9,12; **CF-4 EXEMPT** (computed)                         | Little data run → quick. Ledger rows still need v9 + `asset_group=` + typed reasons.                                                                                           |

**Key**: CF-4 `source` is **EXEMPT** for features/strategy/execution (computed outputs — lineage is the upstream cell,
not a vendor, per `data_source_provenance` COMPUTED_SOURCES). MDPS **propagates** the upstream raw cell's `source` so a
tardis-derived vs venue-derived candle stays distinguishable. So "source covered everywhere" = stamped on ingest
(mtds/instruments), propagated by MDPS, exempt for the pure-computed tail — verified, not blank-by-accident.

## Sequencing

Gated behind the upstream layers (foundation-completion-gate): a downstream service's walk is meaningful only after its
INPUT is canonical — MDPS after the AG MTDS walks; features after MDPS; strategy/execution after features. Audit can run
anytime (read-only); the migration walk per bucket follows its input going C-GREEN. L0 tarball-prune applies if on a VM.

## Phased execution

### P0 — per-service canonical-form AUDIT (run the SSOT checklist; small corpus → fast)

> **Scope is a prior, not a ceiling — fix-fully-autonomously (HARD RULE)**: "low-data / quick" is a prior, not a promise.
> Read DATA-STATE per service and fix EVERY CF-RED the audit surfaces in the same walk (the cefi precedent: a bucket
> framed "~complete" was actually 100% v8 / no source / no asset_group / blank pipeline_mode). NOT descoped, deferred,
> post-cutover, or `BLOCKED-OPERATOR-DECISION` (a data-state gap is not a design fork). SSOT:
> `canonical_form_cross_service_audit_checklist.md` § "Audit scope is a PRIOR, not a ceiling".

- [x] ✅ [DATA] P0. **MDPS** — data-state (slot-3, 2026-06-01): MDPS candles share the **same AG MTDS `_index`** as raw
      ticks (the `processed_candles/` prefix lives in `market-data-tick-{ag}-prd`; the AG `_index` carries `ohlcv_*` /
      `odds_horizon_bucket*` candle data_types alongside raw). The cefi/sports audits already cover them: **same systemic
      debt** (100% v8, no source col, blank pipeline_mode, no available_at, flat paths). So MDPS is **NOT a separate
      walk** — it rides each AG's MTDS single-walk (single-walk discipline; CF-4 source PROPAGATION from the raw cell
      lands there). Feeds `mtds_mdps_master_audit_instructions.md` Canonical-form section.
- [x] ✅ [DATA] P0. **features** — data-state: for the non-defi AGs (cefi/tradfi/sports/prediction) the `features-*-{ag}`
      buckets have **NO `_index/availability_index.parquet`** (surveyed `features-delta-one/mtf/volatility/calendar` ×
      cefi/tradfi — all absent; only `features-onchain-defi-prd` has one = slot-2/defi). So **no features data has run**
      for my AGs → CF audit is vacuously N/A on data-state; the lever is the **WRITER fix (CF-5 typed reasons + CF-11
      no-swallow + CF-4 exempt-computed + stamp v9/asset_group/pipeline_mode COLUMNS)** so the first volume lands
      canonical. CF-6 `expected_unattempted` propagates from upstream. Feeds `features_and_ml_master_audit_instructions.md`.
- [x] ✅ [DATA] P0. **strategy** — data-state: `strategy-store-{ag}-prod` buckets exist but carry **no materialized
      `_index`** (no strategy output run for my AGs). CF audit vacuously N/A; writer-fix lever (v9 + asset_group +
      typed reasons COLUMNS; CF-4 exempt). Feeds `strategy_master_audit_instructions.md`.
- [x] ✅ [DATA] P0. **execution** — data-state: `execution-store-{ag}-prod/prd` buckets exist but **no `_index`**
      (surveyed cefi/tradfi/pred — none). CF audit vacuously N/A; writer-fix lever (ledger rows v9 + asset_group +
      typed reasons; CF-4 exempt). Feeds `execution_master_audit_instructions.md`.
- [x] ✅ [DATA] P0. **Net downstream finding (low-data confirmed)**: only MDPS has data (rides the AG MTDS walk — no
      separate walk); features/strategy/execution for cefi/tradfi/sports/prediction have NOT run → no `_index` to
      migrate. The downstream walk (§C) is therefore **WRITER-FIX-FIRST**: ship the canonical-write fixes so the first
      volume is born canonical, rather than migrating a non-existent corpus. Re-audit each when its input goes C-GREEN +
      its first batch runs.

### C — single-walk per service bucket (only where P0 surfaces debt; bundle CF items)

> **Migration-script performance contract (HARD — codified 2026-06-01, defi C0 lesson)**: any walk script MUST be
> parallel (`ThreadPoolExecutor` — GCS I/O releases the GIL → 5–10×; a bare `for obj` loop is review-blocking) + wire
> `--workers`/`--start-date`/`--end-date` (date-shardable across VMs — no dead args) + `gcs_copy_object` for path-only
> moves (server-side ~250×) / download+transform+upload only for content changes + unbuffered progress logging
> (`python -u`, counter every ~1000) + per-object `try/except…continue` isolation + idempotent re-runs. (Corpus is
> small here, but the contract still applies.) SSOT: `codex/05-infrastructure/gcs-object-operations.md` §
> "Migration-script performance contract".

- [ ] [DATA] P1. **MDPS** C-walk: bundle any `processed_candles/` debt into the SAME AG tick-bucket walk (no second walk
      on an AG `_index` — single-walk discipline); ensure CF-4 source PROPAGATION + CF-1/2/3/5/8 land there.
- [ ] [DATA] P1. **features** C-walk: ONE bundled walk per `features-*-{ag}` index for any P0 debt (v9 +
      `asset_group=` + `pipeline_mode=` partition + typed reasons + `available_at`); CF-4 stays exempt.
- [ ] [DATA] P1. **strategy** C-walk: ONE bundled walk for strategy output `_index` debt (v9 + `asset_group=` + typed
      reasons + `available_at`). Small corpus → likely local, fast.
- [ ] [DATA] P1. **execution** C-walk: ONE bundled walk for execution-record/ledger `_index` debt (same set). Small
      corpus → likely local, fast.
- [ ] [CODE] P1. Writer fixes (all four): emit typed `EmptyConfirmedReason` + `attempted_failed`-not-swallow (CF-11) so
      future writes are canonical (the corpus is small precisely because little has run — fix the writer before volume
      arrives).

### Verify + handoff

- [ ] [DATA] P1. Post-walk per service: re-run the P0 CF audit → all applicable CF GREEN (data-state). Each service's
      canonical-form section in its audit-instruction file goes GREEN. Hands C-GREEN to `bucket_name_ssot…` L6 for any
      downstream legacy buckets.

## Success criteria

- MDPS/features/strategy/execution `_index`(es) all CF-applicable-GREEN (v9 + `asset_group=` + typed reasons + honest
  `available_at` + batch=live; `pipeline_mode=` partition where applicable; `source` propagated/exempt as classified —
  never blank-by-accident).
- Each downstream service's audit-instruction Canonical-form section is wired + runnable by the operator.
- No second walk opened on any AG tick `_index` (MDPS rides the AG walk).

## Codex SSOTs

- `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md` — the CF checklist this plan audits.
- `codex/02-data/availability-manifest-and-data-status.md` — downstream canonical form + source propagation.
