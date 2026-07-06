---
doc_type: plan
title: IS-catalogue completion (2d) — backfill to no-missing, regen, un-pause (AO Plan 3)
summary:
  Complete the instruments-service could-exist catalogue so every expected-universe consumer reads a full, deduped
  instrument lifecycle. Sequence is B0 (backfill instruments to no-missing) gates B1 (catalogue regen + un-pause the
  per-AG daily schedulers) and the B2 downstream wiring (enumerate_expected_universe reads the shipped
  TOTAL_UNIVERSE_AXES UAC SSOT). B0 is the hard prereq for the Stage-3 denominator re-measure (Plan 4) — a stale
  catalogue means a wrong could-exist universe. Source items live in instruments_mtds_subset +
  instruments_catalogue_incremental_rollup + mvp_scope_catalogue_tagging — this plan carries the catalogue-completion
  slice and references them for detail.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, unified-api-contracts, deployment-service]
scope: [engineer]
tags: [instruments, catalogue, could-exist, backfill, b0, b1, b2, mvp-universe, instruments-completion]
related:
  [
    instruments_completion_tracker_2026_07_06.md,
    instruments_mtds_subset_consistency_remediation_2026_06_17.md,
    instruments_catalogue_incremental_rollup_2026_06_29.md,
    mvp_scope_catalogue_tagging_2026_06_08.md,
    ../../codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
  ]
created: 2026-07-06
last_updated: 2026-07-06
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
model_tier: opus-required
thinking_tier: max
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
---

# IS-catalogue completion (2d) — B0 → B1 → B2 (AO Plan 3)

> **🤖 AO PLAN 3 of the instruments-completion set.** Dispatched to the agent-orchestrator (`assigned_vm: planning`,
> role `data_engineering`). **Dispatch tier (frontmatter-driven, EVERY task): Opus / max.** Coordinator =
> `instruments_completion_tracker_2026_07_06.md` (Stage 2d). Runs in **parallel** with Plans 1 (cefi) + 2 (tradfi). **B0
> is foundational** — it gates B1 + the Stage-3 re-measure (Plan 4): every expected-universe consumer
> (`enumerate_expected_universe.py`, data-status could-exist) reads the catalogue, so a stale/incomplete catalogue = a
> wrong denominator. Source detail lives in `instruments_mtds_subset_consistency_remediation` (B0/B1/B2, F1) — READ
> there; those items stay tracked-but-not-dispatched (that plan is `assigned_vm: NA`), this plan carries the dispatched
> slice.
>
> **Worker guards (HARD):** (1) **smoke-first** on any backfill VM — one venue/slice foreground + verify the IS store +
> catalogue side-effect before fanning out; **backfill VMs default SPOT**; no fire-and-forget (verify T+10min). (2) **B0
> before B1** — do NOT regen the catalogue on an incomplete instrument set. (3) **scheduler un-pause is a cadence
> decision** — if the daily rollup still times out at 3600s, RAISE the BLOCKED-Q (band-aid vs. Phase-3 incremental), do
> not silently re-enable a scheme the operator declined. (4) ship via quickmerge; flip + Progress-Log in the same turn.

## Codex SSOTs (read before touching)

- `codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — IS owns reference data; catalogue = the could-exist
  SSOT MTDS + data-status read.
- `codex/02-data/honest-coverage-model.md` — Layer-1 denominator; do NOT derive the expected universe from the manifest.

## B0 → B1 → B2 (order matters — each task's `PREREQ:` is load-bearing)

- [ ] [DATA] P0. **B0 — backfill instruments to NO-MISSING.** The F1/F2 instrument backfills + the broader could-exist
      instrument backfill (`path_to_100pct_backfill_mtds_is_2026_06_17.md`). Other services rely on instruments to know
      what is available/expected → this runs FIRST. **PREREQ: none (unblocked).** Gate: 0 missing instruments for the
      MVP venue set; a `build_instrument_catalogue` dry-run reports no-missing. instruments-service.
- [ ] [DATA] P1. **F1 — backfill IS for the CEFI venues MTDS has but instruments lacks historically** (part of B0's
      no-missing target; call it out because it is the cefi-denominator-relevant slice). **PREREQ: none.** Gate: the
      cefi venue set in the catalogue matches the MTDS-observed venue set (no venue MTDS captured but IS never
      catalogued).
- [ ] [DATA] P1. **Extended public instrument + perp backfill (UNBLOCKED — no key needed)** — IS daily public
      instrument + perp backfill for EXTENDED. **PREREQ: none.** Gate: EXTENDED instruments catalogued; feeds the cefi
      2f denominator work (Plan 1).
- [ ] [DATA] P1. **CME EC\* event-contract backfill (v9-certification dependency)** — the CME event-contract instruments
      the tradfi catalogue needs for the v9 cert. **PREREQ: none** (coordinate with Plan 2's tradfi IS seed). Gate: CME
      EC\* instruments catalogued.
- [ ] [INFRA] P1. **B1 — instrument catalogue regen + un-pause the per-AG daily schedulers.**
      `build_instrument_catalogue.py` + `catalogue_builder.py` exist; the Cloud Run jobs
      `lifecycle-catalogue-regen-{cefi,defi,tradfi,sports,prediction}` exist but the `*-daily` SCHEDULERS are PAUSED
      (last ran ~2026-06-11/15, pre-backfill, STALE). Re-run the regen jobs per AG → verify the catalogue reflects the
      full deduped instrument lifecycle (genesis/first-seen/last-seen) → decide cadence + un-pause (or keep manual).
      **PREREQ: B0 landed.** Gate: fresh catalogue per AG; scheduler cadence decided + applied.
- [ ] [CODE] P1. **B2 downstream — wire the enumerator to the TOTAL_UNIVERSE_AXES SSOT.** The UAC SSOT is SHIPPED
      (`unified-api-contracts@b654eb6` — `canonical/crosscutting/total_universe.py`: `TOTAL_UNIVERSE_AXES`,
      `UniverseProvenance`, `UniverseTier` + `universe_membership()` MVP⊆TOTAL). Wire `enumerate_expected_universe.py`
      to read these axes for the could-exist denominator (the downstream half B2 left open). **PREREQ: B0.** Gate:
      enumerator reads TOTAL_UNIVERSE_AXES; MVP⊆TOTAL respected; dynamic tests pass.
- [ ] [DATA] P2. **MVP tagging verify** — with MVP ON, data-status shows ~100% for captured MVP cells and does NOT count
      non-MVP cells in the MVP denominator (`mvp_scope_catalogue_tagging` verify). **PREREQ: B1.** Gate: MVP-view
      numbers correct on a spot slice.
- [ ] [INFRA] P2. **Prediction catalogue bucket mismatch** — fix the prediction catalogue reading/writing the wrong
      bucket (`instruments_mtds_subset` finding). Gate: prediction catalogue lands in the canonical bucket.
- [ ] [PLAN] P3. **Delete the orphaned static-snapshot catalogue path** (`reference_data/catalogue/catalogue_b…` legacy
      static path superseded by the lifecycle regen). Gate: no consumer reads the static snapshot; path removed.
- [ ] [INFRA] P1. **BLOCKED-OPERATOR-DECISION — tradfi catalogue-scheduler band-aid vs. Phase-3 incremental.** The
      operator-declined interim band-aid (`instruments_catalogue_incremental_rollup` — bump
      `lifecycle_catalogue_scheduler.tf` timeout) RE-TRIGGERED 2026-07-03: tradfi `prod/catalog.parquet` stale since
      2026-06-29, the daily `lifecycle_catalogue_scheduler` runs killed at the 3600s timeout. Decide: re-enable the
      band-aid (bump timeout) vs. ship the Phase-3 incremental rollup. RAISE via blocked-queue; do not silently
      re-enable the declined scheme. _(Carries `BLOCKED-` — the orchestrator will not dispatch it; stays
      operator-visible.)_

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-06** — Plan authored + dispatched to AO (Plan 3 of the instruments-completion set). Carries the B0→B1→B2
  IS-catalogue-completion slice pulled from instruments_mtds_subset + instruments_catalogue_incremental_rollup +
  mvp_scope_catalogue_tagging. B2 UAC SSOT already shipped (uac@b654eb6); B0 gates B1 + the Stage-3 re-measure.
