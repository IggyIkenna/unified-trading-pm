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

- [ ] [DATA] P0. **MDPS** — run CF-1…CF-12 (`canonical_form_cross_service_audit_checklist.md`) against
      `processed_candles/` across AGs: schema_version data-state, `asset_group=`, `pipeline_mode=` partition, `source`
      PROPAGATION (candle carries the raw cell's source), typed empty reasons, `available_at` (no read-time derivation),
      batch=live. Emit per-CF GREEN/RED. Feeds `mtds_mdps_master_audit_instructions.md` Canonical-form section.
- [ ] [DATA] P0. **features** — run CF-1…CF-12 against `features-*-{ag}` indices: confirm CF-4 EXEMPT (computed; no
      blank external-source RED), CF-6 propagates `expected_unattempted`, v9, `asset_group=`, typed reasons,
      `available_at`. Feeds `features_and_ml_master_audit_instructions.md`.
- [ ] [DATA] P0. **strategy** — run the applicable CF set against strategy output `_index`: v9, `asset_group=`, typed
      reasons, `available_at`, batch=live; CF-4 exempt. Feeds `strategy_master_audit_instructions.md`.
- [ ] [DATA] P0. **execution** — run the applicable CF set against execution-record/ledger `_index`: v9, `asset_group=`,
      typed reasons, `available_at`, batch=live; CF-4 exempt. Feeds `execution_master_audit_instructions.md`.

### C — single-walk per service bucket (only where P0 surfaces debt; bundle CF items)

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
