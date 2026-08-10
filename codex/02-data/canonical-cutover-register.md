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
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    /codex/02-data/pipeline-mode-partition.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/orphan-object-detection.md,
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
    /codex/02-data/orphan-object-detection.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
    /codex/02-data/reconciliation-finding-taxonomy.md,
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

**Known content-desync findings (row VALUE mismatch, not a path-structure violation).** This axis's invariant is
SOURCE-AWARE `{mode}_{source}` (`pipeline-mode-partition.md`) — a row can carry a syntactically-valid `pipeline_mode=`
segment that still disagrees with its own `source` column. Distinct from the path-structure violations §1/§5 track.

| Finding | Severity | Description                                                                                                                                                                  | Delete-eligible | Source                                                    |
| ------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- | --------------------------------------------------------- |
| F10     | MEDIUM   | defi `YEARN_V3/ETHEREUM/yield_bearing/vault_share_price` row: `pipeline_mode=batch_onchain_rpc` but `source=onchain_subgraph` — breaks the `{mode}_{source}` invariant above | NO              | `data_pipeline_reconciliation_defi_2026_07_20.md` §4 / §9 |

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
> [`../../plans/archive/issues/honest_coverage_harness_instrument_type_case_break_on_d1_migration_2026_07_20.md`](../../plans/archive/issues/honest_coverage_harness_instrument_type_case_break_on_d1_migration_2026_07_20.md)
> (resolved, archived). The pre-ruling table + "binding consequence" text below is HISTORY — do not act on it.
>
> **⛔ DeFi carve-out, 2026-07-24 (operator, `adb28421d`,
> `/plans/archive/2026_08/cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md`) — DeFi is NOT part of the
> blanket-UPPERCASE population this subsection and the §7 table row otherwise describe.** DeFi's corpus was measured
> genuinely mixed (not close-to-one-direction like cefi/tradfi/prediction), so DeFi's target is decided
> **per-`instrument_type`-value, least-migration-cost** (whichever casing already dominates for a given value becomes
> that value's target; the minority migrates), with a hard constraint that casing be 100% internally consistent within
> each `(instrument_type, asset_group=defi)` pair post-migration — different values MAY land on different casings from
> each other. (An intermediate same-day agent note briefly mis-read this as "defi is permanently lowercase,
> out-of-scope" — that note is itself superseded by this later, explicit operator directive; see
> `reconciliation-finding-taxonomy.md` §5.1 for the full chain.) Execution:
> `plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md` "Manifest instrument_type case + venue-spelling
> unify" todo.

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
[`../../plans/archive/2026_07/defi_lending_writer_retire_prerequisite_2026_07_20.md`](../../plans/archive/2026_07/defi_lending_writer_retire_prerequisite_2026_07_20.md)
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

**UPDATED 2026-07-27 — migration COMPLETE, not operator-gated/pending.** The physical tradfi path+manifest
canonicalization `--apply` RAN: run `20260720-120911` (mtds-code@5581dcf9), 20/20 SPOT shards reporting ORPHAN=0 over
2,649,469 objects (848,886 MIGRATE→canonical); data-loss forensics CLOSED (0 permanent loss; true victim set = 95, all
restored+verified live; the 385,341 "twins" were benign rename-to-live, e.g. CL→CRUDE/NG→NATGAS). Catalogue (Surface A)
SHIPPED+APPLIED LIVE 2026-07-25 (instruments-service@52d8b3ef): `prod/n` 775,116/776,387 canonical (99.84%), per-day
corpus 68,133,635/68,406,251 canonical (99.60%). Manifest (Surface B) RE-VERIFIED LIVE 2026-07-25: FUTURE/OPTION
`instrument_id` 90.2% canonical, EQUITY/ETF 98.9%. Chain-bundle content (Surfaces C+D) GATE CLOSED 2026-07-27 (slot-9):
`assert_tradfi_derivative_ids_canonical` checked=961 canonical=961 violations=0. Residual non-canonical is by-design
quarantine (ICE qualifier variants — `BLOCKED-OPERATOR-DECISION`, non-MVP) + writer-path re-drift, tracked separately —
not a pending physical migration. Cite `tradfi_manifest_content_recovery_completion_2026_07_24.md`.

---

## §5 — Axis: defi leaf filename (one parquet per instrument)

**Target ruled: 2026-07-18** (operator). The leaf is **ONE parquet per instrument**, named by the **symbolic
`canonical_instrument_id`**, such that `filename == manifest key == canonical_instrument_id`. This SUPERSEDED the
previous capture-batch model.

| Milestone                            | Date                                         | Evidence                                                                                                                                                    |
| ------------------------------------ | -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Operator ruling (target set)         | **2026-07-18**                               | `defi_consolidated_closeout_2026_07_18.md:126` ("shard key = the symbolic `canonical_instrument_id`")                                                       |
| R3 historical migration ALL-TERMINAL | **2026-07-20**                               | 30/30 sub-shards, full 2020q1–2026q2 corpus (Phase-0 audit synthesis, defi migration_state)                                                                 |
| Writer emits the new leaf            | **NOT YET (as of last live reconfirmation)** | leaf-naming code fix shipped `market-tick-data-service@0fddb95e` (2026-07-27); not yet independently reconfirmed live against fresh writes in this register |

**Correction 2026-07-28 — the "DeFi capture is STOPPED / no new defi writes" premise below is FALSE for the batch lane**
(measured live during `/data-pipeline-reconciliation --asset-group defi`, 2026-07-24; full detail:
`issues/defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24.md` § "Fact 1"). Only the
**live/websocket lane** (11 collect + 3 forward crons) was PAUSED (~40 days) — **batch/backfill capture never stopped**:
`pipeline_mode=batch_onchain_subgraph`/`batch_chainlink`/`batch_onchain_rpc`/`batch_aave` objects were actively writing
through `day=2026-07-24` (e.g. `.../UNISWAP_V2/.../COMP-WETH-30.0.parquet`, `time_created=2026-07-24T22:46:34Z`, ~1h
before the probe). The manifest rebuild's `MalformedRowKeyError` crash in the CF-11 honest-absence re-emit is unaffected
by this correction and remains open separately. Therefore:

- Post-2026-07-20 defi objects at the old (pre-fix) batch leaf are **not** frozen historical residue — the batch lane
  kept writing under the old leaf shape the whole time, so the population was actively growing until the leaf-naming fix
  (`mtds@0fddb95e`, 2026-07-27) landed in code.
- The correct `effective_from` for the defi leaf axis is **the date the fixed writer is confirmed live for every DeFi
  handler routing through `write_defi_rows()`** (6 of 7 handlers per the R1 changelog), which has not yet been
  independently reconfirmed in this register. Until that reconfirmation, defi leaf-shape findings against batch-lane
  objects should be read against the pre-fix vs. post-fix commit boundary, not treated as `unknown-vintage` on the
  now-withdrawn "no new writes" premise.

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
RATIFIES the UTL paths registry, which already declares it. **In force at the writer: 2026-07-21 →
`features-service@57f8b45d`. Historical migration EXECUTED 2026-07-27 (304/304 legacy `delta_one` CEFI objects
twin-verified-deleted; volatility had zero legacy objects). Effective-from for classification: 2026-07-21.**

| Kind             | Registry SSOT (already canonical)                                 | Live writer today                                                                                                                                           | State                                 |
| ---------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| delta_one (cefi) | `registry.py:57` `delta_one/by_date/day=…`                        | ✅ `delta_one/by_date/day=…` (`feature_writer.py:132-136` prefix `"delta_one/by_date"`; probe `:793-796` updated in lockstep) — `features-service@57f8b45d` | canonical (migrated)                  |
| volatility       | `registry.py:90` `volatility/by_date/day=…`                       | ✅ `volatility/by_date/day=…` (`volatility/core/feature_writer.py:152-155` `prefix="volatility/by_date"`) — `features-service@57f8b45d`                     | canonical (no legacy objects existed) |
| onchain (defi)   | `registry.py:74` `onchain/by_date/day=…`                          | ✅ `onchain/adapters/onchain_writer.py:62` already `by_date/day=` (verify-only)                                                                             | canonical (verify)                    |
| sports           | writer `sports/data/writer.py:26` `sports_features/by_date/day=…` | ✅ already `by_date/day=` (verify `feature_versioning.py:57` prefix `"by_date"`)                                                                            | canonical (verify)                    |

Cutover EXECUTED. Historical `delta_one/day=…` (CEFI) legacy objects were twin-verified-deleted 304/304 (0 skipped) —
TRADFI delta_one and volatility (CEFI+TRADFI) had zero legacy objects to begin with. **Post-migration probe
2026-07-27**: `gcloud storage ls` on `delta_one/day=`, `volatility/`, and bucket-root `day=` in
`features-cefi-prd-central-element-323112` all return zero matches; `delta_one/by_date/day=…/` is populated and live.
Full detail:
[`../../plans/archive/issues/features_by_date_root_canonicalisation_2026_07_21.md`](../../plans/archive/issues/features_by_date_root_canonicalisation_2026_07_21.md)
(todos 1-8, all closed). Non-canonical-path-inventory row #17 retired in lockstep.

---

## §6b — Axis: `instrument_availability` full canonical hive grammar (R2, 2026-07-21)

**Target ruled: 2026-07-21** (operator R2, HARD RULE) — every data-at-rest bucket MUST use the FULL canonical hive
grammar (canonical key set incl. `pipeline_mode=`/`asset_group=`, in canonical order), not a reduced/flat subset. This
resolves the "`instrument_availability` FLAT vs hive" contested axis → **RULED HIVE**. **In force at the writer:
2026-07-22 → `unified-trading-library@43fa6f3f` + `instruments-service@a9be6ce9`. Historical migration: EXECUTED
2026-08-03 for the recognized flat `day=/venue=` shape (see below). effective-from for classification stays 2026-07-22**
(the writer-ship date, per this register's own convention — the historical backfill date is recorded separately, not
substituted in).

| Surface       | State today                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| registry SSOT | ✅ hive — `registry.py:35` `instrument_availability/by_date/day={date}/pipeline_mode={pipeline_mode}/asset_group={category}/venue={venue}/`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| live writer   | ✅ hive for cefi/defi/tradfi/prediction — `process_write.py` + `writers.py` (`_instrument_availability_sink_for`/`_market_lifecycle_sink_for` sink-prefix helpers). ⚠️ **sports: code fixed but NOT YET LIVE** — `instruments-service@ba87cc32` (merged to LDR 2026-08-03T08:48:16Z) makes `_write_sports_fixture_venue` emit the ruled `league=`-trailing hive shape, but a live GCS check the same day (09:11:53Z) still showed the OLD un-hived flat shape (`day=/league=/venue=`) — the fix had not yet reached `main`, and the production `uts-prod-instruments-service-sports-fixtures` Cloud Run Job pins an image digest built from `main`, not LDR. Re-verify before citing as live; see "Residual" below for the historical-backlog status. |
| siblings      | ✅ same fix applied: `market_lifecycle`, `futures_contracts`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| readers       | ✅ layout-tolerant across the cutover (day-scoped listing matched on the venue-tail): `cloud_data_provider.py`, `instrument_lifecycle_loader.py`, `manifest_writer/*`, `options_cluster_lookup.py`, `tradfi_live.py`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |

**Trap (avoided):** the UTL sink sorts partition-dict keys ALPHABETICALLY (`protocol_impls.py:26`), so
`pipeline_mode=`/`asset_group=` cannot be added to the partition dict — the fix bakes ordered keys into the sink PREFIX,
and updates the registry template (SSOT).

**Historical migration — EXECUTED 2026-08-03 for the recognized flat `day=/venue=` shape, real PROD infra, both legs
dedicated-VM (never in-session, per the heavy-I/O rule):**

- **Copy-and-verify** (todo 7c): `instruments-service@242b29ae` (tool) + `deployment-service@1c19e5e` (launcher wiring),
  `{ag}-iah` VM categories, one VM per asset_group, full mode; every asset_group re-run twice (idempotency confirmed —
  second run `copied: 0`).
- **Purge** (todo 7d): `instruments-service@06be51ec` (tool — fresh per-object Part1+Part2 re-verify immediately before
  every delete + generation-matched `gcs_conditional_delete`) + `deployment-service@b19c94b7` (launcher wiring),
  `{ag}-iah-purge` VM categories, one VM per asset_group.
- **Recognized-flat-shape candidate population: 117,166** (cefi 7,650 / defi 73,679 / tradfi 25,402 / prediction 4,105 /
  sports 6,330). Of these: **84,320 copied-to-hive-and-purged-from-flat** (safe, twin-verified; cefi 6,156 / defi 42,364
  / tradfi 25,365 / prediction 4,105 / sports 6,330 — prediction and sports 100% clean, zero residual flat). **32,846
  content_mismatch** (cefi 1,494 / defi 31,315 / tradfi 37) — the hive target already exists with a DIFFERENT (crc32c,
  size) than the flat source; correctly left in place pending an operator authoritative-source decision, NOT deleted.
  **0 failed.**
- **Dated post-migration probe (2026-08-03, this todo)** — live `gcloud storage ls` (bucket-scoped, not a corpus walk)
  on `instruments-store-cefi-prd-central-element-323112/instrument_availability/by_date/`: `day=2020-06-15/` returns
  ONLY the `pipeline_mode=` hive subtree (flat fully purged); `day=2019-03-30/` returns BOTH `pipeline_mode=` (hive,
  copied) AND the preserved flat `venue=DERIBIT/instruments.parquet` — exactly the expected
  content_mismatch-preservation behavior 7c/7d report, not a migration miss.

**Residual — was NOT covered by this migration, tracked + progressively closed in a separate issue doc:** discovered
2026-08-03 during 7c/7d — sports's live writer never actually emitted the assumed flat `day=/venue=` shape (it emitted a
THIRD, unrecognized shape, `day=/league=/venue=`, ~172,595 objects), and prediction had TWO additional unrecognized
shapes (`canonical_question_group=/day=/venue=` + `market_lifecycle`'s `day=/group=/venue=`, group-before-day) — these
two plus a third, older prediction shape (see below) totaled 25,745 unrecognized objects combined, not just the two
named shapes. **Status as of 2026-08-03 (same day):** sports's writer fix + migration-tool extension are CODE-SHIPPED
(`instruments-service@ba87cc32`) but the writer fix is not yet confirmed live in production (see "live writer" row
above) and the ~172,595-object historical backlog has not yet been applied/copied; prediction's two shapes are
recognized + migration-tool-extended (`instruments-service@aaa0866c`), dropping `unrecognized` from 25,745 to 12,463 —
the residual 12,463 is a THIRD, even older prediction shape (`day=/market=/venue=`, predates the
`canonical_question_group` scheme, needs an operator ruling before it can be migrated, not a mechanical rename). Full
writeup + todos (writer fix, target-shape ruling, tool extension, content_mismatch resolution policy, the residual
`market=` shape):
[`../../plans/archive/2026_08/issues/instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md`](../../plans/archive/2026_08/issues/instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md).

**Prediction's two migration-tool-extended shapes — APPLIED 2026-08-09 (`instruments-service@aaa0866c` tool, this
todo):** fresh dry-run confirmed 13,282 flat candidates across the two shapes (`canonical_question_group=/day=/venue=` +
`market_lifecycle`'s `day=/group=/venue=`), matching the 2026-08-03 sizing. `--apply-prod --confirm-prod-write`
copy-and-verify completed **0 failed**: 13,280 `already_present_verified` + 2 `content_mismatch` (left in place pending
an operator authoritative-source decision, not deleted — same policy as the 2026-08-03 cefi/defi/tradfi run). The
residual 12,463 `unrecognized` count for prediction is entirely the THIRD, still-pending `market=` shape (gated on the
sibling issue doc's todo 8) — the two named shapes' own unrecognized count is 0.

Full detail:
[`../../plans/archive/issues/instrument_availability_hive_canonicalisation_2026_07_21.md`](../../plans/archive/issues/instrument_availability_hive_canonicalisation_2026_07_21.md)
(todos 1-8, all closed). Non-canonical-path-inventory row #16 updated in lockstep.

---

## §6c — Axis: cefi chain-tail v6 (R3, 2026-07-21)

**Target ruled: 2026-07-21** (operator R3) — the v6 tail `underlying={ROOT}/quote={Q}/margin={M}/ticks.parquet` is
canonical everywhere; the v5 bare tail `underlying={ROOT}/ticks.parquet` is LOSSY (same-underlying USD/USDT +
linear/inverse chains collide) and ALL v5 must migrate. This resolves the "cefi chain-tail v5 vs v6 — two live-written
shapes" contested axis → **RULED v6**. **CODE fully EXECUTED 2026-07-27 (write + read + guard, real-GCS proven). DATA
MIGRATION: N/A — 0 v5 (or any) cefi chain objects exist anywhere in the corpus (see below). effective-from for
classification = 2026-07-22** (the date `mtds@04222eb0` shipped; no cefi chain object has EVER been written, so there is
no pre-cutover population to grandfather).

| Surface                    | v6 state                                                                                                                                                                                                                                                                                                              |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| UAC builder                | ✅ v6 — `partition_paths.py:252-253` (`build_cefi_partition_path`); structural guard `unified-api-contracts@9a92cf4f`                                                                                                                                                                                                 |
| W2 (Tardis lane)           | ✅ v6 — `tardis_shared.py:668-669`                                                                                                                                                                                                                                                                                    |
| W1 (PartitionedTickWriter) | ✅ v6 — `market-tick-data-service@04222eb0` (`_cefi_chain_partition_dims`); guard `_assert_canonical_chain_path` raises on synthetic v5 (real-GCS proven)                                                                                                                                                             |
| reader                     | ✅ FIXED 2026-07-27 — was v6-first for tradfi ONLY (cefi always fell to the bare v5 tail, unreadable post-W1-fix); now lists the chain's own `underlying={id}/` subtree (handles multiple v6 settlement variants sharing one underlying, e.g. DERIBIT BTC USD/inverse + USDC/linear) — `_cefi_chain_underlying_blobs` |

**Real-GCS proof (2026-07-27, `-test-` bucket, no mocking)**: wrote a DERIBIT BTC options-chain chunk (two settlement
variants) via the real `PartitionedTickWriter.write_chunk` — both objects landed at the v6 path (confirmed via
`gcs_describe_object`); `CanonicalParquetReader.read_shard` round-tripped both rows back (after the reader fix above);
`_assert_canonical_chain_path` raised on a hand-constructed synthetic v5 path. All 3 checks PASS. Proof script:
`market_tick_data_service/scripts/prove_cefi_chain_tail_v6_e2e_2026_07_27.py`.

**Data migration — confirmed 0 objects (2026-07-27)**: queried the real consolidated availability manifest
(`market-data-tick-cefi-prd-central-element-323112`) for every row with
`instrument_type in (options_chain, futures_chain)`: 307 rows, ALL
`capture_status ∈ {attempted_failed, empty_confirmed}` — **ZERO rows with `capture_status == captured`**, across the
ENTIRE corpus, any date, any venue, any writer. Spot-verified with real `gcloud storage ls` against the attempted-failed
(day, venue) prefixes: zero objects. This extends the issue doc's todo-1 finding (W1 reaches zero live objects) to the
whole corpus: no cefi chain object — v5 or v6 — has EVER been successfully captured. Migration is therefore a confirmed
no-op; there is nothing to copy, verify, or leave in place.

Fix + migration record:
[`../../plans/archive/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md`](../../plans/archive/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md).

---

## §6d — Axis: `processed_candles/` LOCKED shape (MDPS, Option-A corrected 2026-07-21)

**Target ruled: 2026-07-21** (operator Option-A, corrected the same evening) — `instrument_type=` added to the path for
cefi/tradfi/defi (prediction already carries it); `pipeline_mode=` added; `data_type` STAYS SOURCE on the path (manifest
re-aligns to source, not the reverse — the original framing had this backwards). See AE-6,
`/codex/02-data/mdps-candle-canonical-reconciliation.md`. **In force at the writer: NOT YET — no migration has run.
Effective-from PENDING for every asset_group below.**

| asset_group | effective-from | state                                                                                                                                                                                                                                                        |
| ----------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| defi        | PENDING        | migration_pending — first in the ruled sequence                                                                                                                                                                                                              |
| prediction  | PENDING        | migration_pending — already carries `instrument_type=` (terminal axis), needs `pipeline_mode=` only                                                                                                                                                          |
| cefi        | PENDING        | migration_pending — **BLOCKED**: an active `canonical-migration-cefi-*` raw-tick fleet is running (verified 2026-07-22 via `gcloud compute instances list`); candle cutover must wait for it to drain (manifest-shard contention + pre-migration-drain rule) |
| tradfi      | PENDING        | migration_pending — last in the ruled sequence                                                                                                                                                                                                               |

**Machine-checkable now:**
`unified_api_contracts.canonical_path_violations(path, require_candle_migration_complete=False)` (the default)
suppresses the pending axes above for `processed_candles/` paths; pass `require_candle_migration_complete=True` to check
against the fully-migrated LOCKED shape. Shipped `unified-api-contracts@6329fc04`. Folded into
`plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md` as a new phase — the actual data migration
is NOT owned by this reconciliation-skill plan.

---

## §6e — Axis: prediction `trades` schema — POLYMARKET market-question metadata (title/slug/event_slug)

**Target ruled 2026-07-25** (operator,
`plans/archive/issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md` Q3): extend the
canonical `data_type=trades` schema to carry `title`/`slug`/`event_slug` (market-question metadata with no surviving
copy elsewhere once the legacy dual-write trees are retired) instead of dropping it or permanently forking a separate
canonical shape. Trader-identity/PII fields (`proxy_wallet`/`name`/`pseudonym`/`bio`/`profile_image`) are explicitly
EXCLUDED from this cutover — still a separate, unresolved operator call.

**Writer-root fix EXECUTED 2026-07-28** (slot-12): `unified-api-contracts@90ddcc01` (added `title`/`slug`/`event_slug`
`ColumnSpec` entries to `_schema_spec_prediction.py`; `outcome`/`outcome_index` were already present) +
`market-tick-data-service@84154e1a` (`PolymarketAdapter` no longer drops `title`/`slug`/`eventSlug` at ingest;
`eventSlug`→`event_slug`/`outcomeIndex`→`outcome_index` renamed to canonical snake_case). **Effective-from 2026-07-28
for NEW writes only** — the historical legacy raw-tick objects (shapes #3/#3b `data_type=prediction_trades`, 2,477
manifest rows/348 dates, and shape #4's 10-segment tree, corpus-wide extent NOW KNOWN — 348 days, 1,126,358 objects,
563,173 unique condition_ids; 4b-ii enumeration COMPLETE 2026-08-04, slot-15, `market-tick-data-service@e46fb943`) are
now split: shapes #3/#3b MIGRATED (4b-i COMPLETE 2026-08-06 — 3,574 legacy objects deleted, 0 remain), while shape #4
(4b-iii) remains pending. All in `market-data-tick-pred-prd-{pid}`:

- **Shapes #3/#3b** (`data_type=prediction_trades` bundle-per-underlying): 2,477 manifest rows, 348 dates (2025-03-14 →
  2026-04-14), 14 `underlying` values, 100% `capture_status=captured`. Migration (4b-i) in progress:
  `market-tick-data-service@e4acf0c4` (`scripts/migrate_prediction_trades_legacy_bundle_2026_07_28.py`), **COMPLETE
  2026-08-06 — 3,574 legacy `prediction_trades` objects enriched + deleted across the full 2025-03-14→2026-04-14 range,
  0 legacy objects remain** (final verification re-run over all 348 dates; see
  `plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md` todo 4b session-end entry). Delete executed after
  a fresh `gcs_bucket_soft_delete_retention_seconds()` check (604800s, reversibility-qualified).

- **Shape #4** (10-segment `data_source=POLYMARKET_CLOB/.../data_type=trades/{cid}.parquet` tree under
  `raw_tick_data/by_date/day=.../pipeline_mode=batch_polymarket_clob/asset_group=prediction/`): **1,126,358 objects,
  563,173 unique condition_ids**, 100% of days have canonical flat twins. Merge+delete (4b-iii) is a separate follow-on,
  gated on 4b-i completing (both share the same canonical target).

See `plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md` todo 4b and
`/codex/02-data/non-canonical-path-inventory.md` row 22 for the full disposition.

| asset_group | effective-from (new writes) | historical backfill state                                                                                                                              |
| ----------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| prediction  | 2026-07-28                  | shapes #3/#3b MIGRATED + legacy deleted 2026-08-06 (4b-i, 3,574 objects, 0 remaining); shape #4 (1.13M objects enumerated) merge+delete pending 4b-iii |

---

## §7 — Summary table

| asset_group | require_pipeline_mode                 | instrument_type PATH | instrument_type COLUMN                                                                | chain tail                                              | defi leaf                    | sports data_type case  |
| ----------- | ------------------------------------- | -------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------- | ---------------------------- | ---------------------- |
| cefi        | 2026-05-19                            | lower · UNKNOWN date | ✅ UPPER target · migration_pending (D1, §3c)                                         | **2026-07-22** — EXECUTED, 0-object migration (R3, §6c) | n/a                          | n/a                    |
| tradfi      | 2026-05-19                            | lower · UNKNOWN date | ✅ UPPER target · migration_pending (D1, §3c)                                         | **2026-07-19**                                          | n/a                          | n/a                    |
| defi        | 2026-05-19                            | lower · UNKNOWN date | ⚠ PER-VALUE target, not blanket UPPER · migration_pending (2026-07-24 carve-out, §3c) | n/a                                                     | UNKNOWN (writer not resumed) | n/a                    |
| prediction  | 2026-05-19                            | lower · UNKNOWN date | ✅ UPPER target · migration_pending (D1, §3c)                                         | n/a                                                     | n/a                          | n/a                    |
| sports      | 2026-05-19 (+ BLK-d48acae4 exception) | n/a                  | ✅ UPPER target · migration_pending (D1, §3c)                                         | n/a                                                     | n/a                          | UNKNOWN (K1 unshipped) |

> **⛔ corrected 2026-07-20, operator ruling D1 — RE-RECONCILED 2026-07-20 (acceptance review).** The
> `instrument_type COLUMN` cells above read "🔴 UNRULED (§3c)" until the 2026-07-20 ruling, then briefly "RULED
> UPPERCASE (enforce now)". The reconciled stance: the column TARGET is **UPPERCASE** but is **`migration_pending`**
> (mixed on disk today) — the reconciliation skill compares it **case-INSENSITIVELY** and emits **NO** casing finding
> until the migration completes; UPPERCASE is enforced POST-migration. See §3c.

**cefi chain-tail hazard — RESOLVED 2026-07-27.** _(Historical: ⛔ RULED 2026-07-21, operator R3 — see §6c. At the time
of ruling, cefi had two live write lanes emitting two different tails for the same shard: MTDS W1
`PartitionedTickWriter` emitting the bare v5 tail because `write_chunk` gated quote/margin derivation on
`asset_group == "tradfi"` only, while the W2 Tardis lane already emitted v6.)_ W1 shipped v6
(`market-tick-data-service@04222eb0`, 2026-07-22) and was proven end-to-end against real GCS 2026-07-27 (write + reader
round-trip + guard — see §6c). **No cefi chain-tail fork exists on disk to reconcile**: the corpus manifest shows ZERO
captured cefi `options_chain`/`futures_chain` rows anywhere, ever (§6c) — there was never a v5-shaped object written by
ANY lane, so a reconciliation pass finds nothing to accept or flag on this axis today.

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
