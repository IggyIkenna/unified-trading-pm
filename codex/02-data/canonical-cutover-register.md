---
doc_type: codex-ssot
title: Canonical cutover register — per-asset-group effective-from dates per canonical axis
summary: >-
  The durable register of WHEN each canonical axis became mandatory for each asset_group, so a reconciliation pass can
  separate "legitimately historical" (written before the cutover — not a finding) from "non-canonical" (written after
  the cutover — a real regression). Covers require_pipeline_mode, instrument_type case, the tradfi chain tail, the defi
  leaf filename, and the sports data_type case. Dates are derived from the four consolidated close-out plans and the
  tradfi migration issue doc, each cited by plan and sha; where a cutover date cannot be established from the record it
  is recorded UNKNOWN rather than guessed. Exists because the close-out plans ARCHIVE and would take these dates with
  them.
status: current
nature: ssot
asset_group: [meta]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service, instruments-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    canonicalisation,
    cutover,
    effective-from,
    reconciliation,
    pipeline-mode,
    instrument-type,
    migration,
    per-asset-group,
  ]
related:
  [
    cross-asset-canonical-target-ssot.md,
    pipeline-mode-partition.md,
    defi-canonical-naming-ssot.md,
    availability-manifest-and-data-status.md,
    orphan-object-detection.md,
    ../../plans/active/defi_consolidated_closeout_2026_07_18.md,
    ../../plans/active/cefi_consolidated_closeout_2026_07_18.md,
    ../../plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    ../../plans/active/sports_consolidated_closeout_2026_07_19.md,
    ../../plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md,
  ]
created: 2026-07-20
authoritative_for:
  [
    canonical cutover dates per asset_group,
    effective-from dates for canonical axes,
    historical-vs-noncanonical classification rule,
  ]
referenced_by:
  [
    codex/02-data/orphan-object-detection.md,
    codex/02-data/four-surface-reconciliation-procedure.md,
    codex/02-data/reconciliation-finding-taxonomy.md,
  ]
owner:
last_reviewed: 2026-07-20
code_refs:
  [
    unified-api-contracts/unified_api_contracts/canonical/partition_paths.py,
    instruments-service/scripts/migration_orphan_sweep.py,
  ]
---

# Canonical cutover register

> **Why this doc exists.** The cutover dates currently live only inside four consolidated close-out plans and one issue
> doc — all of which **archive**. A reconciliation pass that does not know them either floods false positives on
> pre-cutover data or silently passes post-cutover regressions. This register is the durable form.
>
> **This doc REFERENCES the canonical target; it does not restate it.** What the canonical form _is_ →
> [`cross-asset-canonical-target-ssot.md`](cross-asset-canonical-target-ssot.md). What `pipeline_mode` _means_ →
> [`pipeline-mode-partition.md`](pipeline-mode-partition.md). This doc answers only **from when**.

---

## §1 — The classification rule this register enables

For an object or manifest row written at time `T`, on canonical axis `A`, for asset_group `AG`:

| Condition                            | Classification                 | Reconciliation action                             |
| ------------------------------------ | ------------------------------ | ------------------------------------------------- |
| `T < effective_from(AG, A)`          | **legitimately historical**    | Not a finding. May be a _migration_ target.       |
| `T >= effective_from(AG, A)`         | **non-canonical (regression)** | A finding. Root-cause the writer.                 |
| `effective_from(AG, A)` is `UNKNOWN` | **UNDECIDABLE**                | Report as `unknown-vintage`; never auto-classify. |
| Axis is `UNRULED` (see §4)           | **out of scope**               | MUST NOT be reported as a finding at all.         |

Two things this rule is **not**:

- It is **not** a licence to delete pre-cutover data. Pre-cutover data is normally the _only_ copy (the v9 migration
  COPIED, it did not MOVE — the GCS DELETE SAFETY INVARIANT in
  [`pipeline-mode-partition.md`](pipeline-mode-partition.md) §"GCS DELETE SAFETY INVARIANT", codified 2026-06-18).
- It is **not** a substitute for the machine oracle. Canonical/non-canonical shape is decided by UAC
  `canonical_path_violations()` (`unified-api-contracts/unified_api_contracts/canonical/partition_paths.py:661`); this
  register only supplies the **date gate** and the per-AG value of the `require_pipeline_mode` keyword
  (`partition_paths.py:661`, default **`False`** — see §2).

---

## §2 — Axis: `require_pipeline_mode`

The `pipeline_mode=` path segment was added to every parquet across **all five asset_groups in one bundled GCS
migration**, Phase 3, on **2026-05-19** — 31 VMs, all terminated exit 0, no data loss
([`pipeline-mode-partition.md`](pipeline-mode-partition.md) `:35`, `:46`, `:55`). That is a single fleet-wide event, so
the effective-from date is the same for every AG.

| asset_group | `require_pipeline_mode` effective-from | Evidence                                                     |
| ----------- | -------------------------------------- | ------------------------------------------------------------ |
| cefi        | **2026-05-19**                         | `pipeline-mode-partition.md:55` (Phase 3, all 5 AGs, 31 VMs) |
| tradfi      | **2026-05-19**                         | same                                                         |
| defi        | **2026-05-19**                         | same                                                         |
| prediction  | **2026-05-19**                         | same                                                         |
| sports      | **2026-05-19**, with a known exception | same; exception below                                        |

**Sports exception (operator-ACCEPTED, do not re-report).** 19,274 `instruments-store-sports` rows predating
**2026-07-08** carry blank `pipeline_mode` **and** blank `source`, accepted as permanently untyped under `BLK-d48acae4`.
_(**Count is a ceiling, not an exact figure — ≤ baseline; last measured 13,903 on 2026-07-20** (acceptance review,
sports reconciliation run). 19,274 is the original baseline; the measured 13,903 is below it, consistent with the
count-only-decreases exit rule — the population can only shrink as rows are typed/cleaned, never grow. Keep the 19,274
baseline; treat the live count as ≤ baseline and re-measure per run.)_ A reconciliation pass MUST suppress these as a
known exception, not surface them as a fresh finding. _(Recorded in the Phase-0 audit's per-asset-group synthesis for
sports; the underlying blocker id is `BLK-d48acae4`. **UNVERIFIED**: this agent did not read the row-level evidence
behind the 19,274 count.)_

**The machine gate is currently WEAKER than this register.**
`canonical_path_violations(..., require_pipeline_mode: bool = False)` defaults to `False` (`partition_paths.py:661`). A
caller that omits the keyword will pass a path with no `pipeline_mode=` segment. Any reconciliation pass reading
post-2026-05-19 data MUST pass `require_pipeline_mode=True` explicitly. Which lanes do and do not is a separate open
item (plan todo P1-10).

---

## §3 — Axis: `instrument_type` case

This axis splits into **three sub-axes** with different rulings. ~~Two are settled; one is BLOCKING and unruled.~~ **(⛔
corrected 2026-07-20: all three are now RULED — PATH lowercase (3a), ID middle UPPER (3b), COLUMN target UPPERCASE but
`migration_pending` today (3c).)**

### 3a. PATH segment — SETTLED, lowercase

The `instrument_type=` **hive path segment** is lowercase (`{it_lower}`) for every asset_group carrying the segment —
cefi, tradfi, defi, prediction. This is uniform across all four canonical path grammars recorded in the Phase-0 audit
synthesis and is what the builders in `partition_paths.py` emit.

| asset_group | PATH segment case                                   | effective-from                                        |
| ----------- | --------------------------------------------------- | ----------------------------------------------------- |
| cefi        | lowercase                                           | **UNKNOWN** — predates the close-out record           |
| tradfi      | lowercase                                           | **UNKNOWN**                                           |
| defi        | lowercase                                           | **UNKNOWN**; migration worklist is quantified, see 3c |
| prediction  | lowercase (`instrument_type=prediction_market`)     | **UNKNOWN**                                           |
| sports      | n/a — sports has no `instrument_type=` path segment | n/a                                                   |

`UNKNOWN` here is load-bearing: the lowercase path rule is clearly current, but no document in the corpus states the
date it became mandatory. Treat a pre-2026 upper-case path segment as `unknown-vintage`, not a regression.

### 3b. ID segment — SETTLED, UPPER inside the canonical id

Inside the canonical instrument id the type token is **UPPER** and is part of the id grammar, not the path grammar:
`VENUE:TYPE:BASE-QUOTE@MARGIN` (cefi), `VENUE:EQUITY:SYM-USD` (tradfi cash), `VENUE-CHAIN:TYPE:SYMBOL` (defi symbolic),
`VENUE:PREDICTION_MARKET:{condition_id}` (prediction). The id-segment case is **not** the same axis as the column case
in 3c and must not be conflated with it. Grammar SSOT:
[`cross-asset-canonical-target-ssot.md`](cross-asset-canonical-target-ssot.md).

### 3c. MANIFEST COLUMN case — ✅ RULED UPPERCASE (TARGET), `migration_pending` today (was BLOCKING, contradiction B2)

> **⛔ corrected 2026-07-20, operator ruling D1 — RE-RECONCILED 2026-07-20 (acceptance review).** ~~This axis was "🔴
> UNRULED (BLOCKING)"; the register refused to pick a side.~~ ~~A reconciliation pass now ENFORCES UPPERCASE for the
> column.~~ **RULED: the canonical TARGET for the manifest `instrument_type` COLUMN is UPPERCASE (catalogue enum
> wins).** Recorded in
> [`../../plans/active/data_pipeline_reconciliation_skill_2026_07_20.md`](../../plans/active/data_pipeline_reconciliation_skill_2026_07_20.md)
> § "OPERATOR DECISIONS — ALL THREE RULED 2026-07-20", and mirrored in
> [`cross-asset-canonical-target-ssot.md`](cross-asset-canonical-target-ssot.md) §7 / §11a. Three separate legs, never
> collapsed: manifest **COLUMN → UPPERCASE (target)** · GCS **path segment → lowercase** (unchanged, ALWAYS enforced) ·
> **id middle segment → UPPER** (unchanged, ALWAYS enforced).
>
> **The UPPERCASE column is the TARGET, NOT yet implemented — the column is `migration_pending` (measured 2026-07-20:
> mixed on disk — defi both cases present, prediction 99.46% UPPER, cefi ~99.41% adjusted).** Therefore the
> reconciliation skill: **(1)** does **NOT REFUSE** the axis (the old "REFUSE — awaiting operator ruling" is REMOVED —
> the ruling is made); **(2)** compares the `instrument_type` COLUMN **case-INSENSITIVELY** and emits **NO** casing
> finding during the `migration_pending` window — flagging lowercase-today would false-flag all un-migrated data;
> **(3)** the TARGET is UPPERCASE — **POST-migration the column is enforced UPPERCASE.** The two already-shipped
> uppercase scripts (`instruments-service@555ddf1c` + the tradfi Phase-B script) are **RATIFIED** and their DRAIN-GATED
> `--apply` freeze is **LIFTED**; defi/other rows not yet folded UP are `migration_pending`, not a fresh non-canonical
> finding. **Gate**: the honest-coverage harness must be made case-robust BEFORE the migration flips writers — see
> [`../../plans/active/issues/honest_coverage_harness_instrument_type_case_break_on_d1_migration_2026_07_20.md`](../../plans/active/issues/honest_coverage_harness_instrument_type_case_break_on_d1_migration_2026_07_20.md).
> The pre-ruling table + "binding consequence" text below is HISTORY — do not act on it.

| Side          | Claim                                                        | Citation                                             |
| ------------- | ------------------------------------------------------------ | ---------------------------------------------------- |
| **LOWERCASE** | manifest `instrument_type` column is lowercase               | `cross-asset-canonical-target-ssot.md` §7 / §11      |
| **UPPERCASE** | manifest `instrument_type` column is UPPER, catalogue = SSOT | `tradfi_consolidated_closeout_2026_07_18.md` Phase B |

Aggravating facts, both recorded in the Phase-0 audit synthesis:

- **cefi and tradfi have already SHIPPED scripts that uppercase the column** — e.g. `instruments-service@555ddf1c`
  (dry-run: 3,824,258 itype rows changed; canonical fraction 84.98%→99.41%; **NOT applied**, drain-gated). So the
  shipped-code tiebreak points UPPER while the designated tie-breaker doc says lower.
- The tradfi close-out **contradicts itself within one file** — its own worklist orders the fold in the opposite
  direction to its Phase-B statement.

~~**Binding consequence until the operator rules:** a reconciliation pass MUST NOT report manifest `instrument_type`
column casing as a finding, MUST NOT propose a casing migration, and the two DRAIN-GATED `--apply` runs stay frozen
(plan todo P0-02).~~ **(SUPERSEDED by ruling D1 above — the axis is now enforced UPPERCASE and the freeze is lifted.)**

_(Defi flat `LENDING` — **⛔ corrected 2026-07-20, operator ruling D2.** ~~"parked and NOT a casing question"~~. The
full retire (A_TOKEN/DEBT_TOKEN split, all lending data_types — not holdings-only) is now **RULED and is the TARGET**,
but is **NOT yet implemented** — gated on the MTDS lending-writer fix
[`../../plans/active/defi_lending_writer_retire_prerequisite_2026_07_20.md`](../../plans/active/defi_lending_writer_retire_prerequisite_2026_07_20.md)
→ migrate ~16.7M rows → re-sync the shard atom. Until the migration completes, market/event flat `LENDING` is
`migration_pending` — a reconciliation pass neither flags it as a fresh finding nor treats it as unruled. See
`cross-asset-canonical-target-ssot.md` §5 banner.)_

---

## §4 — Axis: tradfi chain tail (`underlying=` / `quote=` / `margin=`)

**effective-from: 2026-07-19** — the first date on which a tradfi chain write emits the three-segment tail. This is the
best-evidenced cutover in the register.

| Leg          | Shipped                                                                                                              | Evidence                                                                       |
| ------------ | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| CHAIN WRITE  | `uac@ad28e55a` + `mtds@145e4aae` — writer emits `underlying=/quote=/margin=/ticks.parquet`, test-verified atom==path | `plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md:196` |
| CHAIN READ   | `mtds@935e1f8d` — `reader.py::_blob_paths_derivative` probes the new tail                                            | same doc `:198`                                                                |
| SINGLES tail | `mtds@d257b7be` (QG-green: 6433 passed, 0 failed)                                                                    | same doc `:148`                                                                |

The write-time guard on this lane **RAISES** (tradfi is the only AG with a raising canonical write guard), so a
post-2026-07-19 tradfi chain object without the tail is a genuine regression and should be reported as such.

**Two carve-outs that MUST be suppressed, not reported:**

- **`combo`** keeps the bare `underlying=/ticks.parquet` fan-in and is deliberately outside the full-id filename guard —
  a documented carve-out (leg-id grammar unsettled), not drift.
- **`batch_massive`** — HISTORICAL carve-out, no longer active. Massive was removed as a tradfi source 2026-07-19, and
  the gated GCS purge **COMPLETED 2026-07-21** (1,701,422 objects → 0, accepted permanent loss, operator Option C). 0
  Massive objects remain, so the orphan-suppression no longer guards anything; `batch_massive` `PipelineMode` +
  `possible_manifest` read-recognition can now be removed from code. See
  [`tradfi-databento-sourcing-ssot.md`](tradfi-databento-sourcing-ssot.md).

The tradfi corpus is canonical on **filenames only** — the manifest measured **0 canonical rows across all years**, and
the physical migration `--apply` is operator-gated. So for tradfi the manifest surface is expected non-canonical
wholesale; that is migration state, not per-shard regression.

---

## §5 — Axis: defi leaf filename (one parquet per instrument)

**Target ruled: 2026-07-18** (operator). The leaf is **ONE parquet per instrument**, named by the **symbolic
`canonical_instrument_id`**, such that `filename == manifest key == canonical_instrument_id`. This SUPERSEDED the
previous capture-batch model.

| Milestone                            | Date           | Evidence                                                                                              |
| ------------------------------------ | -------------- | ----------------------------------------------------------------------------------------------------- |
| Operator ruling (target set)         | **2026-07-18** | `defi_consolidated_closeout_2026_07_18.md:126` ("shard key = the symbolic `canonical_instrument_id`") |
| R3 historical migration ALL-TERMINAL | **2026-07-20** | 30/30 sub-shards, full 2020q1–2026q2 corpus (Phase-0 audit synthesis, defi migration_state)           |
| Writer emits the new leaf            | **NOT YET**    | defi capture is fully STOPPED pending the writer fix                                                  |

**The writer cutover date is `UNKNOWN` because it has not happened.** DeFi capture is STOPPED (11 collect + 3 forward
crons PAUSED ~40 days), and the manifest rebuild currently CRASHES in the CF-11 honest-absence re-emit with
`MalformedRowKeyError`. Therefore:

- Post-2026-07-20 defi objects at the old batch leaf are **not** a writer regression — there are no new defi writes.
- The correct `effective_from` for the defi leaf axis is **the date capture resumes with the fixed writer**, which is
  not yet set. Until then defi leaf-shape findings are `unknown-vintage`, not regressions.

A stale template inside the designated tie-breaker doc is a known corpus defect: `cross-asset-canonical-target-ssot.md`
§8 still shows the pre-ruling defi leaf template and is scheduled for correction (plan todo P1-09). Until corrected,
**this register's §5 wins for the leaf filename**.

Note also the **two-id model (Option A, intentional)**: `canonical_instrument_id` is symbolic and address-free while
`instrument_id` is address-anchored, and POOL `instrument_id` **collides across chains BY DESIGN**. Divergence between
the two ids on a POOL row is an accepted exception, never a finding.

---

## §6 — Axis: sports `data_type` case

**Ruled UPPER: 2026-07-18** — operator K0-DECISION (b). Sports is the **only** asset_group whose `data_type` is UPPER,
and CF-7's generic UPPER→lower map is **SUPERSEDED for sports** (`sports_consolidated_closeout_2026_07_19.md:71-72`).

But the ruling is **not yet in force at the writer**, so the effective-from for _classification_ is not 2026-07-18:

| Step                              | State                        | Evidence                                                                                      |
| --------------------------------- | ---------------------------- | --------------------------------------------------------------------------------------------- |
| K0-DECISION (b) — UPPER is target | ruled 2026-07-18             | `sports_consolidated_closeout_2026_07_19.md:71`                                               |
| K1 — LIVE writer emits UPPER      | **NOT SHIPPED**              | `:126-128` — fixes `_build_sports_shard_path` (`venue_fetch.py:871-900`); must ship BEFORE K2 |
| K2 — historical rows migrate UP   | **NOT STARTED**, gated on K1 | `:129-135`, `:507`                                                                            |

**effective-from for sports `data_type` UPPER = UNKNOWN (pending K1 ship).** Until K1 ships, lower-case sports
`data_type` rows are the _expected_ live-writer output, not a regression. Scope, corrected in the close-out after it
contradicted itself (`:316-317`): the dominant lower-case value is **`trades` = 1,806,553 rows (91.5% of the bucket)**,
not the ~20k `odds` family; decision 4 (`:406`) is MIGRATE ALL ~1.8M.

Two further sports facts a reconciliation pass needs, both from the Phase-0 audit synthesis:

- Sports has **no `asset_group=` hive key at all** (`sports_reference/by_date/day={D}/pipeline_mode=…/entity={E}/…`),
  and an `entity=` folder name is **NEVER** a data_type (HARD RULE). A generic per-AG loop produces structural false
  positives here.
- The fixtures writer still emits the hardcoded umbrella `data_type="FIXTURES"` (333,594 rows, last written
  2026-07-19T10:11:33Z) with **zero** `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` rows — the 2026-05-23 split never reached
  the writer. That IS a live regression, on a different axis than casing.

---

## §6a — Axis: features data-at-rest `by_date/day=` root (R1, 2026-07-21)

**Target ruled: 2026-07-21** (operator R1) — every features data-at-rest tree MUST carry the `by_date/day=` level. This
RATIFIES the UTL paths registry, which already declares it. **In force at the writer: NOT YET → effective-from for
classification is UNKNOWN.**

| Kind             | Registry SSOT (already canonical)                                 | Live writer today                                                                                         | State               |
| ---------------- | ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------- |
| delta_one (cefi) | `registry.py:57` `delta_one/by_date/day=…`                        | ❌ `delta_one/day=…` — NO `by_date/` (`feature_writer.py:132-136` prefix `"delta_one"`; probe `:793-796`) | `migration_pending` |
| volatility       | `registry.py:90` `volatility/by_date/day=…`                       | ❌ **bucket root** — `get_data_sink` with NO `prefix=` (`volatility/core/feature_writer.py:152-155`)      | `migration_pending` |
| onchain (defi)   | `registry.py:74` `onchain/by_date/day=…`                          | ✅ `onchain/adapters/onchain_writer.py:62` already `by_date/day=` (verify-only)                           | canonical (verify)  |
| sports           | writer `sports/data/writer.py:26` `sports_features/by_date/day=…` | ✅ already `by_date/day=` (verify `feature_versioning.py:57` prefix `"by_date"`)                          | canonical (verify)  |

Until the delta_one + volatility writers ship the `by_date/` prefix, their existing objects are `migration_pending`
(written before the ruling), NOT a regression. Fix + migration:
[`../../plans/active/issues/features_by_date_root_canonicalisation_2026_07_21.md`](../../plans/active/issues/features_by_date_root_canonicalisation_2026_07_21.md).

---

## §6b — Axis: `instrument_availability` full canonical hive grammar (R2, 2026-07-21)

**Target ruled: 2026-07-21** (operator R2, HARD RULE) — every data-at-rest bucket MUST use the FULL canonical hive
grammar (canonical key set incl. `pipeline_mode=`/`asset_group=`, in canonical order), not a reduced/flat subset. This
resolves the "`instrument_availability` FLAT vs hive" contested axis → **RULED HIVE**. **In force at the writer: NOT YET
→ effective-from UNKNOWN.**

| Surface       | State today                                                                                                                 |
| ------------- | --------------------------------------------------------------------------------------------------------------------------- |
| registry SSOT | ❌ FLAT — `registry.py:35` `instrument_availability/by_date/day={date}/venue={venue}/` (2 keys)                             |
| live writer   | ❌ FLAT — `process_write.py:612` prefix `"instrument_availability/by_date"` + `writers.py:201-208` partition `{day, venue}` |
| siblings      | ❌ same reduced-flat shape: `market_lifecycle` (`process_write.py:614`), `futures_contracts` (`writers.py:359,382`)         |

**Trap (do not repeat):** the UTL sink sorts partition-dict keys ALPHABETICALLY (`protocol_impls.py:26`), so
`pipeline_mode=`/`asset_group=` cannot be added to the partition dict — the fix bakes ordered keys into the sink PREFIX,
and updates the registry template (SSOT). Flat objects are `migration_pending`, not a fresh finding. Fix + migration:
[`../../plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md`](../../plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md).

---

## §6c — Axis: cefi chain-tail v6 (R3, 2026-07-21)

**Target ruled: 2026-07-21** (operator R3) — the v6 tail `underlying={ROOT}/quote={Q}/margin={M}/ticks.parquet` is
canonical everywhere; the v5 bare tail `underlying={ROOT}/ticks.parquet` is LOSSY (same-underlying USD/USDT +
linear/inverse chains collide) and ALL v5 must migrate. This resolves the "cefi chain-tail v5 vs v6 — two live-written
shapes" contested axis → **RULED v6**. **In force at W1: NOT YET → cefi effective-from UNKNOWN.**

| Surface                    | v6 state                                                                                                                                                                      |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| UAC builder                | ✅ v6 — `partition_paths.py:252-253` (`build_cefi_partition_path`)                                                                                                            |
| reader                     | ✅ v6-first, v5-fallback — `reader.py:402-403`                                                                                                                                |
| W2 (Tardis lane)           | ✅ v6 — `tardis_shared.py:668-669`                                                                                                                                            |
| W1 (PartitionedTickWriter) | ❌ bare v5 for cefi — quote/margin derived ONLY under `asset_group=="tradfi"` (`partitioned_writer.py:291-292`); guard `_assert_canonical_tradfi_path` (`:83`) is tradfi-only |

**Open first:** whether any native-REST cefi venue routes `options_chain`/`futures_chain` through W1 (vs the W2 Tardis
lane) — this sizes the live v5 cefi migration blast radius. Fix + migration:
[`../../plans/active/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md`](../../plans/active/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md).

---

## §7 — Summary table

| asset_group | require_pipeline_mode                 | instrument_type PATH | instrument_type COLUMN                        | chain tail                                 | defi leaf                    | sports data_type case  |
| ----------- | ------------------------------------- | -------------------- | --------------------------------------------- | ------------------------------------------ | ---------------------------- | ---------------------- |
| cefi        | 2026-05-19                            | lower · UNKNOWN date | ✅ UPPER target · migration_pending (D1, §3c) | ✅ v6 target · migration_pending (R3, §6c) | n/a                          | n/a                    |
| tradfi      | 2026-05-19                            | lower · UNKNOWN date | ✅ UPPER target · migration_pending (D1, §3c) | **2026-07-19**                             | n/a                          | n/a                    |
| defi        | 2026-05-19                            | lower · UNKNOWN date | ✅ UPPER target · migration_pending (D1, §3c) | n/a                                        | UNKNOWN (writer not resumed) | n/a                    |
| prediction  | 2026-05-19                            | lower · UNKNOWN date | ✅ UPPER target · migration_pending (D1, §3c) | n/a                                        | n/a                          | n/a                    |
| sports      | 2026-05-19 (+ BLK-d48acae4 exception) | n/a                  | ✅ UPPER target · migration_pending (D1, §3c) | n/a                                        | n/a                          | UNKNOWN (K1 unshipped) |

> **⛔ corrected 2026-07-20, operator ruling D1 — RE-RECONCILED 2026-07-20 (acceptance review).** The
> `instrument_type COLUMN` cells above read "🔴 UNRULED (§3c)" until the 2026-07-20 ruling, then briefly "RULED
> UPPERCASE (enforce now)". The reconciled stance: the column TARGET is **UPPERCASE** but is **`migration_pending`**
> (mixed on disk today) — the reconciliation skill compares it **case-INSENSITIVELY** and emits **NO** casing finding
> until the migration completes; UPPERCASE is enforced POST-migration. See §3c.

**cefi chain-tail hazard (not a date, a fork).** _(**⛔ RULED 2026-07-21, operator R3 — see §6c.** The fork is resolved:
**v6 is canonical**, v5 is LOSSY and ALL v5 migrates. The W1 cefi-emits-v5 divergence is now a WRITER DEFECT to fix
(`partitioned_writer.py:291-292` derives quote/margin only under `asset_group=="tradfi"`), not a permanent two-shape
fork; it is `migration_pending` until W1 ships. Until then a reconciliation pass still accepts both cefi tails and does
NOT flag v5 as a fresh finding.)_ cefi has **two live write lanes emitting two different tails for the same shard**:
MTDS W1 `PartitionedTickWriter` emits the bare v5 tail `underlying={U}/ticks.parquet` because `write_chunk` gates
quote/margin derivation on `asset_group == "tradfi"` only, while the W2 Tardis lane emits the v6 tail. There is no cefi
cutover date to record because cefi never cut over — both shapes are being written **now**. A reconciliation pass must
accept both cefi tails and report the fork itself as one finding, not per-shard. _(**UNVERIFIED by this agent**: the
`partitioned_writer.py:290-293` and `tardis_shared.py:667-671` line references come from the Phase-0 audit synthesis;
this agent did not open the MTDS writer files.)_

---

## §8 — Maintaining this register

- **A new cutover is not shipped until it is recorded here.** Add the row in the same turn as the writer ship, with the
  repo@sha.
- **Never guess a date.** `UNKNOWN` is a valid, useful value; a wrong date silently mis-classifies a whole corpus in the
  quiet direction.
- **Distinguish "ruled" from "in force".** §5 and §6 are both cases where the operator ruled but the writer has not
  shipped — the classification gate keys off **in force at the writer**, not the ruling date.
- **An UNRULED axis is not a finding.** Do not let a reconciliation pass launder an unruled axis into a report. (§3c
  _was_ the standing example until it was RULED UPPERCASE on 2026-07-20 — it is no longer unruled; the principle stands
  for any future genuinely-unruled axis.)
