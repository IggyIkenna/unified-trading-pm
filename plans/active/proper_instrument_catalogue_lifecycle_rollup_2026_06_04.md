---
title:
  "Proper instrument catalogue — lifecycle roll-up from per-date definitions + IS completeness gate (all asset groups,
  v9)"
created: 2026-06-04
author: ikenna
parent_epic: epics/instruments_master.md
assigned_vm: vm-cross-cutting
status: active
priority: P0
estimate_class: brand-new
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 8
locked_by: live-defi-rollout
locked_since: 2026-06-04
source:
  - cefi_manifest_canonicalisation_2026_06_01.md Dim-7 P3 (the v2-enumerator `catalog.parquet` has NO producer)
  - operator architecture decision 2026-06-04 (lifecycle catalogue = roll-up of the per-date `by_date/` instrument
    definitions; materialise + overwrite with a monotonic row-count promotion guard; v9, NOT v10)
master: defi_manifest_canonicalisation_2026_06_01.md (cross-plan canonical-SSOT coordinator)
---

# Proper instrument catalogue — lifecycle roll-up + IS completeness gate (all asset groups)

> **FOUNDATION-GATE (HARD).** instruments-service is the foundation MTDS/MDPS sit on; it must be **perfect before the
> MarketTick-data migration `--apply` runs**. This plan makes the **proper instrument catalogue** real (the
> time-independent known-instrument universe), derived from the maintained per-date definitions, so every downstream
> "could-exist" computation (expected_unattempted, coverage denominators, instrument-existence guards) reads a SSOT that
> is correct AND self-refreshing. **The MTDS migration DRY-RUN may proceed** (gated only on all code being available +
> the manifest being ready); the MTDS `--apply` is gated on this plan being GREEN. **v9, NOT v10** — this is part of the
> v9 canonicalisation, no new schema version is introduced.

## Why this exists — the catalogue has no producer, and a static snapshot is wrong two ways

The v2 expected-universe enumerator (`instruments-service/scripts/enumerate_expected_universe.py`) requires
`--catalog-path` = a `catalog.parquet` (`InstrumentCatalogEntry`: one row per instrument + `available_from`/
`available_to` lifecycle window). It is a **cumulative, all-instruments-ever lifecycle catalogue**, NOT a current
snapshot — the enumerator emits `EXPECTED_INSTRUMENT_DELISTED` for `date > available_to`, which is only possible if the
file **retains delisted instruments with `available_to` stamped**.

**Finding (slot-3, 2026-06-04):** workspace-wide grep shows **NO automated/recurring producer** writes that
`catalog.parquet` — only the launcher (`launch-expected-universe-v2-vm.sh`) + its test reference the path. So today it
is an operator-supplied, hand-maintained snapshot. A static snapshot is **stale two ways at once**: (1) missing newly
listed instruments, AND (2) wrong about what is still alive (a since-delisted instrument is shown alive → its cells are
marked `expected_unattempted` forever instead of `DELISTED`).

**The relationship (the fix):** the lifecycle catalogue is a **derivative of the maintained per-date definitions**. IS
already writes `instrument_availability/by_date/day={date}/venue={venue}/instruments.parquet` daily (the point-in-time,
reproducible-batch source — the "what existed on date t" slice; protected by the "never copy instrument definitions
between dates" rule). For each instrument: `available_from` = first day it appears across the `by_date/` snapshots,
`available_to` = last day. So the data already exists; the catalogue is a roll-up of it. Build it **from** `by_date/`
and it is correct + self-refreshing, with no separate artifact to drift.

## Operator design decisions (2026-06-04) — transcribe, do not re-litigate

1. **Materialise the proper catalogue** (do NOT switch to a transient in-enumerator read). Write it to the canonical
   path the launcher + enumerator already expect:
   `gs://instruments-store-{ag_short}-{env_short}-{project}/{env}/catalog.parquet` (per asset group). The existing
   enumerator/launcher then consume it unchanged.
2. **Overwrite on regen — NOT a separate file per day.** Regenerate → write to a **temp/new name** → assert row count is
   **strictly `>=` the current catalogue** (instrument rows grow **monotonically** — new listings add rows; delisted
   rows persist with `available_to` set) → on pass **promote** (replace canonical + delete the temp/previous); on a
   **regression (`<`)** treat it as a bug / incomplete regen → **keep the previous good catalogue, alert, do NOT
   overwrite**. (Caveat to encode: a legitimate corrective shrink — removing a bad instrument row — needs an explicit
   `ALLOW_CATALOGUE_SHRINK` override; the ratchet is a safety default, not an absolute.)
3. **v9, NOT v10.** Part of the v9 canonicalisation; no schema-version bump.
4. **Foundation gate.** This must be GREEN before the MTDS data migration `--apply`. The MTDS dry-run + manifest-rebuild
   dry-run may still run (gated on code-ready + manifest-ready), but the irreversible `--apply` waits on this.

## The four requirements (operator, 2026-06-04)

- [ ] [AUDIT] P0. **IS completeness gate — `instrument_availability/by_date/` is 100% complete (no `attempted_failed`)
      per the UAC expected shard universe (venues × data_types × dates), ALL asset groups + sports fixtures (same
      service).** Build/extend a completeness check that, per AG, diffs the captured `by_date/` instrument-definition
      cells against UAC's expected `(venue × instrument-defn data_type × date)` universe and reports
      `attempted_failed`/missing. **DELICATE — cannot be fully trusted until the manifest + data migrations run:** the
      current `_index` is pre-migration (v8/mixed; cefi 100% v8, see cefi plan), so a "complete" verdict now is
      provisional. Run it BEST-EFFORT now (surface gross gaps) and RE-RUN as a hard gate AFTER the IS manifest
      canonicalisation lands. No catalogue/enumerator output can be trusted while this is RED for an AG. Repo:
      instruments-service (+ UAC for the expected-universe definition). assigned_vm: vm-cross-cutting.
- [ ] [CODE] P0. **Roll-up producer — derive the lifecycle catalogue from the per-date `by_date/` definitions.** New
      instruments-service script/job (per AG, AG-agnostic core): walk
      `instrument_availability/by_date/day={date}/venue={venue}/instruments.parquet`, aggregate to one
      `InstrumentCatalogEntry` row per instrument (`instrument_id`, `instrument_type`, `venue`, `chain`/`league_id`,
      `available_from`=min present day, `available_to`=max present day or null if present on the latest day), write
      `{env}/catalog.parquet` with the **monotonic-guard promotion** (req-2 mechanism above). Reuse the existing
      `InstrumentCatalogEntry` / `_catalog_from_dataframe` contract the enumerator already consumes (no schema drift).
      Cloud-agnostic I/O (`get_storage_client`, `resolve_bucket_name` — never inline `gs://`). +unit tests (roll-up
      lifecycle math; monotonic-guard accept/reject/override). Repo: instruments-service.
- [ ] [INFRA] P1. **Trigger on every instruments update (per AG; reference data → generally ≤ a few times/day).** Wire
      the roll-up to run after each IS instrument-definition write per AG (event-driven off the IS write, or a frequent
      scheduler keyed to the IS update cadence — pick per the IS update mechanism; do NOT fire-and-forget). The v2
      enumerator's recurring run (cefi Dim-7 P3, currently BLOCKED) then reads an always-fresh catalogue. Repo:
      deployment-service (terraform) + instruments-service. assigned_vm: vm-cross-cutting.
- [ ] [CODE] P1. **All asset groups adopt the proper catalogue.** cefi / defi / tradfi / **sports (fixtures)** /
      prediction each produce + consume their `{env}/catalog.parquet` via the same roll-up. Verify each AG's
      `_enumerate_v2_*` reads it and emits `expected_unattempted` against the real, current universe. Per-AG slices
      drive via the sibling AG masters (cefi → slot-3, defi → slot-2, sports → slot-4, prediction → slot-5, tradfi →
      slot-6); vm-cross-cutting owns the shared roll-up + the gate.

## Phased DAG + gates

1. **Phase 0 — completeness audit (best-effort now → hard gate post-migration).** Req-1. Output: per-AG
   complete/incomplete verdict + gap list. Gate: no downstream catalogue trust while RED.
2. **Phase 1 — roll-up producer + monotonic guard.** Req-2. Gate: unit tests green + a dry-run roll-up over a real AG
   produces a catalogue that matches a hand-spot-check of `by_date/` lifecycle for sample instruments.
3. **Phase 2 — trigger wiring.** Req-3. Gate: observed re-generation on a real IS update + the monotonic guard rejects a
   truncated input in test.
4. **Phase 3 — all-AG adoption + enumerator unblock.** Req-4. Gate: each AG's v2 enumerator reads the fresh catalogue;
   cefi Dim-7 P3 enumerator-cron unblocks (now points at a self-refreshing catalogue).
5. **GATE → MTDS migration `--apply`.** Foundation-completion-gate: IS catalogue GREEN for the AG before its MTDS
   `--apply`. Dry-runs are NOT gated on this.

## Codex SSOT updates (required before archival)

- `codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — add the lifecycle-catalogue roll-up contract
  (catalogue = roll-up of `by_date/` definitions; canonical path; monotonic-guard regen; v2-enumerator consumer).
- `codex/02-data/availability-manifest-and-data-status.md` — note the catalogue as the could-exist-universe SSOT feeding
  `expected_unattempted`.

## Cross-references + supersedes

- **SUPERSEDES** `cefi_manifest_canonicalisation_2026_06_01.md` Dim-7 P3 (enumerator-cron, BLOCKED-OPERATOR-DECISION):
  the recurring enumerator is no longer the unit of work — this plan is. Once Phase 3 lands, the cefi Dim-7 P3 cron is a
  thin wrapper over the now-fresh catalogue.
- **Per-date denominator refinement (separate, smaller P3 — tracked in cefi plan):** the deployment-api coverage
  denominator (deployment-api@d55bcb6) reads ONE current IS availability snapshot, not the per-date `by_date/`
  definitions, so it is not per-date point-in-time-correct (the universe as-of each historical date). Optional
  follow-up; NOT part of this foundation plan.

## Pre-audit / open questions for the executor

- Confirm the exact `by_date/` instrument-definition columns per AG (and the sports-fixtures analog) before writing the
  roll-up aggregation keys.
- Confirm whether the IS `_index` (post-canonicalisation) is the right completeness source for Req-1, or whether the
  expected-universe must come from UAC `DATA_TYPES_BY_ASSET_GROUP` × the IS catalog × dates (mirror
  `enumerate_expected_universe._enumerate_v2_*`).
- Confirm the canonical catalogue object path matches `resolve_bucket_name` output for `kind="instruments-store"` (the
  launcher hardcodes `instruments-store-{ag_short}-{env_short}-{project}/{env}/catalog.parquet`; the producer must write
  exactly where the enumerator reads).
