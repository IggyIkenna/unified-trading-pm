---
doc_type: codex-ssot
title: Reconciliation distinct-value census + per-datapoint validation + two-tier compute model
summary: >-
  Extends the four-surface reconciliation with three additions the per-shard oracle loop does not cover: (1) a cheap
  in-session DISTINCT-VALUE CENSUS that enumerates every axis value (instrument_type / data_type / venue / chain)
  actually present in the manifest column AND the GCS path segments and diffs both against the canonical UAC vocabulary,
  plus a manifest-vs-GCS distinct-set diff that catches shard-atom desync at vocabulary level; (2) PER-DATAPOINT
  id-canonical validation (every row's instrument_id rebuilt through the UAC SSOT builder, not the sampled filename-stem
  check) and PER-DATAPOINT schema validation (columns / dtypes / UTC / non-NaN / non-placeholder via the UAC schema
  contracts); (3) a TWO-TIER COMPUTE MODEL — the census stays in-session and bounded, while the per-datapoint checks
  (which read millions of parquets) run on a SPOT VM as the ONE sanctioned single-walk, writing a results manifest the
  skill reads back. Names the finding-types each check emits and flags the three that the taxonomy must add. REFERENCES
  the four-surface procedure and the finding taxonomy; does not restate them.
status: current
nature: ssot
asset_group: [meta]
stage: [data]
repos:
  [
    unified-trading-pm,
    unified-api-contracts,
    unified-trading-library,
    deployment-api,
    deployment-service,
    market-tick-data-service,
  ]
scope: [engineer, admin]
tags:
  [
    reconciliation,
    distinct-value-census,
    canonicalisation,
    per-datapoint-validation,
    id-canonical,
    schema-validation,
    single-walk,
    compute-tiers,
    spot-vm,
    machine-oracle,
  ]
related:
  [
    four-surface-reconciliation-procedure.md,
    reconciliation-finding-taxonomy.md,
    cross-asset-canonical-target-ssot.md,
    canonical-cutover-register.md,
    non-canonical-path-inventory.md,
    availability-manifest-and-data-status.md,
    ../05-infrastructure/spot-vms-for-backfill.md,
    ../05-infrastructure/vm-launcher-runbook.md,
    ../12-agent-workflow/async-wait-and-poll-discipline.md,
  ]
created: 2026-07-20
authoritative_for:
  [
    reconciliation distinct-value census,
    axis-value vocabulary flagging,
    per-datapoint id-canonical validation,
    per-datapoint schema validation,
    reconciliation compute-tier model,
    reconciliation single-walk VM job,
  ]
referenced_by: []
owner:
last_reviewed: 2026-07-20
code_refs:
  [
    deployment-api/deployment_api/routes/data_status/_axis_census.py,
    deployment-api/deployment_api/routes/data_status/_distinct_values.py,
    unified-trading-library/unified_trading_library/manifest_writer/_read_index.py,
    unified-api-contracts/unified_api_contracts/_instrument_enums.py,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    unified-api-contracts/unified_api_contracts/registry/chain_env.py,
    unified-api-contracts/unified_api_contracts/canonical/partition_paths.py,
    unified-api-contracts/unified_api_contracts/internal/reference/canonical_id_builder.py,
    unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py,
    unified-api-contracts/unified_api_contracts/internal/schemas/_validation.py,
    unified-trading-library/unified_trading_library/core/parquet_schema_enforcer.py,
    unified-trading-library/unified_trading_library/io/base_writer.py,
    unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py,
    deployment-service/deployment_service/vm_prefix_registry.py,
    deployment-service/scripts/vm/launch-manifest-recon-all-vm.sh,
    deployment-service/scripts/vm/launch-canonical-migration-vm.sh,
  ]
---

# Reconciliation distinct-value census + per-datapoint validation + two-tier compute model

> **Scope.** This doc extends the four-surface reconciliation with three checks the per-shard oracle loop does not
> perform. It **references** `four-surface-reconciliation-procedure.md` (the per-shard comparison loop, the shard-atom
> grain, the single-walk constraint and its three sanctioned no-walk routes) and `reconciliation-finding-taxonomy.md`
> (the closed finding set, severities, delete-eligibility, the accepted-exception list). It **does not restate** them —
> where a rule already lives there, this doc points and stops.
>
> **Why these three exist.** The per-shard oracle `canonical_path_violations()`
> (`unified-api-contracts/unified_api_contracts/canonical/partition_paths.py:661`) validates path **structure** only. It
> never checks the **values** of the `instrument_type=` / `data_type=` / `chain=` / `venue=` segments against their
> enums, and it **drops the filename** before validating (so a wire-named `instrument_id` reads canonical). Those two
> blind spots are the exact class that produced the false "twin absent" verdict on 2026-07-20 — probing
> `instrument_type=pool` when the writer emits `solana_amm_pool`. The census (G1) closes the vocabulary blind spot
> cheaply and in-session; the per-datapoint checks (G2/G3) close the id-form and content blind spots at 100%, on a VM
> (G4), because they read the whole corpus.

---

## 1. The distinct-value census (G1) — in-session, cheap, always runs

The census enumerates the **distinct set** of each axis value present on two surfaces, badges each value canonical /
non-canonical against the UAC vocabulary, and runs three set comparisons. It reads exactly two cheap surfaces (one
manifest index parquet + a delimited directory listing) and **opens no data parquet**, so it neither violates
single-walk nor needs the VM tier.

### 1.1 Manifest side — reuse the existing endpoint

The manifest-side distinct-value census **already exists** as a deployment-api endpoint:
`get_axis_value_census(service, asset_group)` (`deployment-api/deployment_api/routes/data_status/_axis_census.py:134`),
over `AXIS_CENSUS_COLUMNS = (venue, chain, instrument_type, data_type, source, pipeline_mode)` (`_axis_census.py:86`).
It reads via the slim, column-pruned, cached read of the ONE consolidated `_index/availability_index.parquet` —
`read_availability_index(bucket, columns=[...])`
(`unified-trading-library/unified_trading_library/manifest_writer/_read_index.py:296`) — the identical read every
data-status endpoint already serves. It returns `{value, count}` per axis with blank sentinels dropped, **RAW spellings
preserved, verdict undecided** (by design, `_axis_census.py` docstring).

A manifest index read is **single-walk-exempt** (it reads the manifest, not the corpus). The census reuses this endpoint
verbatim and applies the canonical badging below; it does **not** modify the endpoint.

### 1.2 GCS side — delimiter descent, no whole-corpus walk

The GCS-path distinct set is gathered by **delimiter child-prefix listing** (no-walk route #2 in the four-surface
procedure's single-walk section): descend one `key=value/` partition level at a time using
`list_blobs(..., delimiter="/")` and read only the returned `prefixes` (directory nodes) — **never leaf object names,
never parquet bytes**. Split each returned child prefix on `=`, collect `value` into the per-axis set for `key`.

- **Derive the descent order from the per-AG path grammar, never a hardcoded segment order.** The SSOT is
  `canonical_path_templates(asset_group)`
  (`unified-api-contracts/unified_api_contracts/registry/possible_manifest.py:352`, exported from
  `unified_api_contracts`), which returns the canonical + legacy GCS path TEMPLATES with `{date}` / `{venue}` /
  `{chain}` / `{instrument_type}` / `{data_type}` placeholders — parse the placeholder order straight from it. (It
  returns an **empty list for sports** — that is the "use the sports dispatcher `candidate_parquet_paths`" signal, not
  "no paths".) The underlying builders it composes — `build_defi_partition_path` (`partition_paths.py:88`),
  `build_cefi_partition_path` (`:194`), `build_tradfi_partition_path` (`:287`), `build_prediction_partition_path`
  (`:383`) — are the per-AG detail. A hand-rolled segment order is itself the `drift_axis_false_positive` class.
- **Bound the descent** to a small recent day window (the vocabulary is day-stable) plus, when a historical cutover is
  in scope, one pre-cutover day. Total `list_blobs` calls = O(vocabulary-cardinality × |day-sample|) — tens to
  low-hundreds, not O(objects). This is not a whole-corpus walk (contrast the single sanctioned enumerator; see the
  procedure's single-walk section).
- **Sports / prediction differ**: sports has no `asset_group=` node (tree is `entity=`-keyed via
  `candidate_parquet_paths`) and prediction is `conditionId`-keyed — use the AG's own grammar, per the per-AG reference
  sheets. `chain` is a defi-only axis (empty elsewhere).

### 1.3 Canonical vocabulary to flag against (line-anchored)

| Axis              | Canonical set (SSOT)                                                                          | Grain rule (reuse `_distinct_values._comparison_set`, `:241`)                                                 |
| ----------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `instrument_type` | `InstrumentType` enum — `unified-api-contracts/unified_api_contracts/_instrument_enums.py:17` | **defi**: case-insensitive; **cefi/tradfi**: EXACT case-sensitive                                             |
| `venue`           | `VENUES_BY_ASSET_GROUP[ag]` — `registry/market_data_categories.py:268`                        | **defi**: compare against bare protocol bases (`_distinct_values._defi_bare_venue_bases`, `:213`); else EXACT |
| `data_type`       | `DATA_TYPES_BY_ASSET_GROUP[ag]` — `registry/market_data_categories.py:118`                    | EXACT                                                                                                         |
| `chain`           | `MAINNET_CHAIN_IDS` keys — `registry/chain_env.py:10`                                         | EXACT; defi-only axis                                                                                         |

The canonical-set + grain logic already exist as `_distinct_values._canonical_set` (`:200`) and `_comparison_set`
(`:241`); the census reuses them (mapping the singular manifest column name to the plural axis name the helpers key on).

### 1.4 The three comparisons + finding-types

Per axis, let `M` = manifest distinct set, `G` = GCS distinct set, `C` = canonical set (grain-resolved via
`_comparison_set`):

| #   | Comparison               | Meaning                                    | Finding-type emitted                                                    |
| --- | ------------------------ | ------------------------------------------ | ----------------------------------------------------------------------- |
| a   | `M − C` (grain-aware)    | a manifest value outside the vocabulary    | **`non_canonical_axis_value`** (surface S3) — NEW, taxonomy must add it |
| b   | `G − C` (grain-aware)    | a GCS path segment value outside the vocab | **`non_canonical_axis_value`** (surface S1) — NEW, taxonomy must add it |
| c   | `M △ G` (symmetric diff) | manifest ↔ GCS disagree at vocab level     | **`shard_atom_vocab_desync`** — NEW, taxonomy must add it               |

`non_canonical_axis_value` is **distinct from** `non_canonical_path` (taxonomy §2.2): that type is defined by the oracle
rejecting the path structure, and the census does not run the oracle — the oracle is vocabulary-blind. See §4 for the
proposed taxonomy blocks.

### 1.5 Mandatory suppression before emitting

The census applies the taxonomy's accepted-exception list BEFORE emitting, or it re-reports refused/accepted axes and
destroys report signal:

- **C2a instrument_type COLUMN casing** — a value differing from a canonical value only by case (cefi/tradfi) routes to
  a `REFUSED — C2a casing` line, never a `non_canonical_axis_value` finding, and proposes no migration. (defi is
  case-folded by `_comparison_set`, so no defi casing noise.)
- **Decision-D `LENDING` keying** — never flag `lending` / `solana_lending` on defi market/event data_types.
- **`batch_massive`** (source axis) is not non-canonical / not delete-eligible.
- **Sports blank `pipeline_mode` / `source`** — already dropped as blank sentinels; never re-report.

### 1.6 Worked example (the 2026-07-20 slip)

The defi writer emits lowercase `solana_amm_pool`; both `SOLANA_AMM_POOL` (`_instrument_enums.py:79`) and `POOL` (`:50`)
are enum members. The census prints the writer's ACTUAL token as a present, canonical value and shows `pool`
conspicuously **absent** from the set — so probing `instrument_type=pool` (the earlier false verdict) becomes
impossible: you read the real vocabulary off the census instead of guessing. Had a stray object been written at
`instrument_type=pool/` while the manifest carried `solana_amm_pool`, comparison (c) fires immediately →
`shard_atom_vocab_desync`.

---

## 2. Per-datapoint id-canonical (G2) + schema (G3) validation

Both are per-ROW / per-PARQUET checks over the full corpus. They are the 100% lift of checks the four-surface loop today
performs only **sampled** (the filename-stem == column check, and the four-pillar content spot-check). They run on the
VM tier (§3), not in-session.

### 2.1 G2 — id-canonical validation (builder-as-judge, never a regex)

For every row, reconstruct the id from the row's own structured columns using the UAC SSOT builder and assert
byte-equality with the stored `instrument_id` (and, for defi, `canonical_instrument_id`).

- **Judge** = `build_canonical_instrument_id` / `build_instrument_id`
  (`unified-api-contracts/unified_api_contracts/internal/reference/canonical_id_builder.py:972` / `:735`) — the single
  dispatch the writers themselves use. **Never** a re-implemented regex (a migration-heuristic `_CANON_ID_RE` is a
  fallback, not the oracle).
- **Which column holds the symbol is looked up, not guessed** — `SchemaContract.symbol_column`
  (`unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py:142`), resolved via `lookup_contract`
  (`contracts.py:1121`) on `(asset_group, instrument_type, data_type)`. Dated-derivative parts (`expiry_date`, `strike`,
  `option_right`, `margin_marker`) come from their own columns.
- **Legitimately id-less shapes emit no id-form finding** — pattern-#2 bundles (`options_chain` / `futures_chain`, null
  `instrument_id` by design), the symbol-less `ticks.parquet` fan-in, the prediction CQG filename-id bundle. This
  mirrors the procedure's own stem-less carve-out (four-surface §4.3).
- **Suppressed by AE-3** — a defi POOL `instrument_id ≠ canonical_instrument_id` divergence is the intentional two-id
  model, not a finding.

A stored id (`ADAF0:USTF0`, or double-wrapped `BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0`) that does not equal the builder
output, or a row that raises `ValueError` through the builder, is a violation → **`non_canonical_id`** (NEW; taxonomy
must add it). This is the id-FORM leg that `non_canonical_path` is structurally blind to.

### 2.2 G3 — schema validation (reuse `validate_dataframe`, invent nothing)

Per parquet, resolve the `SchemaContract` via `lookup_contract` and run the existing read-side validator
`validate_dataframe(df, contract)` (`unified-api-contracts/unified_api_contracts/internal/schemas/_validation.py:49`,
re-exported from `contracts.py:165`) — the read-side twin of the write-time `ParquetSchemaEnforcer.validate_dataframe`
(`unified-trading-library/unified_trading_library/core/parquet_schema_enforcer.py:93`; write machinery
`unified-trading-library/unified_trading_library/io/base_writer.py`). It emits the closed violation set:

1. **Required columns present** → `missing_column`.
2. **Dtypes correct** → `wrong_dtype`.
3. **Timestamps UTC-tz-aware (DTZ at content grain)** — falls out of #2 because the contract dtype is the tz-aware
   literal `datetime64[ns, UTC]`; a tz-naive column is a `wrong_dtype` violation.
4. **No NaN in non-nullable columns / row-count floor** → `null_in_required` / `row_count_too_low`.
5. **Placeholder-that-looks-populated** — a `captured` manifest row over a 0-row / all-NaN parquet, or an
   `empty_confirmed` row with blank `error_reason`. This is the content-grain expression of the honest-absence rule
   (`record_captured` / `record_empty`, never a fake `record_captured`).

**Schema SSOT per layer** (all under `unified-api-contracts/unified_api_contracts/internal/schemas/`): raw tick =
`CONTRACT_REGISTRY` + `lookup_contract` keyed by `(asset_group, instrument_type, data_type)`; candle / feature / ml
layers = their sibling contract registries. G3 is the four-pillar content check (`row_count>0`; NaN-ratio;
schema-matches-contract; coverage) lifted from **sampled to 100%**.

G3 emits the **existing** `shard_pillar_fail` (+ `masked_empty_row`) types — the report drops the "SAMPLED spot-check"
qualifier only for a Tier-2 full scan. G3 needs **no** new finding-type.

---

## 3. Two-tier compute model (G4)

The census (§1) is cheap and in-session; the per-datapoint checks (§2) read millions of parquets and MUST NOT run as
in-session compute — done naively they also violate single-walk. The model is two tiers.

### 3.1 Tier 1 — in-session, bounded, always runs (no VM, no corpus walk)

1. **Census (§1)** — one slim manifest read + delimiter descent. Sanctioned no-walk routes.
2. **Per-shard path oracle** — unchanged from the skill's current Phase 1 (`canonical_path_violations()`).
3. **Sampled id/schema smoke** — prove the G2/G3 validator logic on a bounded sample via prefix-scoped, manifest-derived
   listing (no-walk route #1): **at most 1 object per distinct manifest shard-atom, hard-capped at ≤ 500 fetched objects
   per asset_group** (deterministic: newest object per atom, atoms sorted, truncate at 500). A clean sample is reported
   as **"id/schema validated on a SAMPLE of ≤500, NOT the full corpus"** — never a 100% claim.

Tier-1 cost: a handful of manifest reads + ≤500 object GETs per AG. No VM. No whole-corpus walk.

### 3.2 Tier 2 — SPOT VM, the ONE sanctioned single-walk, opt-in for a 100% claim

Per-datapoint G2 + G3 over the full corpus, as ONE fresh walk per corpus per campaign (the
`launch-canonical-migration-vm.sh` single-walk pattern). **G2 and G3 are two PASSES bundled onto that ONE snapshot
walk**, run in order per object — not two VMs, not two walks. Any future per-datapoint check bundles onto the SAME walk.

**Launcher — REUSE, do not hand-roll a VM name.** The launcher name MUST match a real `VM_PREFIX_TO_BUCKET` entry
(`deployment-service/deployment_service/vm_prefix_registry.py:99`) — an unregistered name is silently invisible in
deployment-ui / cockpit / Slack. Model the launcher on the read-only audit shape
`deployment-service/scripts/vm/launch-manifest-recon-all-vm.sh` (per-AG, singleton-locked, `e2-standard-4`, zone
`asia-northeast1-c`, chained read-only scripts over ONE VM, `VM_SHUTDOWN_ON_COMPLETION=true`, results to `recon-logs/`).
Register a **real `VmPrefixSpec`** (`LifecycleClass.EPHEMERAL_BATCH`) for a
`datapoint-validation-{cefi,defi,tradfi,sports,prediction}-` prefix pointing at the results bucket **before first
launch** (ship it via quickmerge first). The heartbeat-only `None` prefixes (`manifest-recon-` `:571`,
`reconcile-phantom-` `:732`, `cross-asset-rescan-` `:733`) are reusable but get **no shard-progress monitor** — the
full-corpus results-writing job needs a real `VmPrefixSpec` + `MANIFEST_PER_VM_SHARDS=true` so the fleet monitor can key
on target-artifact write-progress (the 2026-07-18 entity-agnostic blind spot).

**SPOT + preemption (backfill HARD RULE, `../05-infrastructure/spot-vms-for-backfill.md`).** The job is idempotent per
shard (a shard whose results row already exists is presence-skipped), so it is backfill-class → **SPOT by default**:
`--provisioning-model=SPOT --instance-termination-action=DELETE --no-restart-on-failure`, `ON_DEMAND=false`. Preemption
**resumes from measured PROGRESS, never a replay-from-start** — the VM emits progress on results-shard frontier advance
→ `PROGRESS.json` (monotonic-gated); `RelaunchPreemptedVm` resumes from the frontier. Because it is presence-skip (NOT
`--force`), the standard relaunch is correct and the force-PAGE guard never fires. Call `lc_write_launch_params()` at
create time so the relaunch replays the exact `(asset_group[, venue, data_type])` scope.

**No fire-and-forget (`../12-agent-workflow/async-wait-and-poll-discipline.md`).** Arm ONE `run_in_background` heartbeat
watchdog (≤30-min, `kill -0` liveness, no self-match, terminal verdict on every exit path) in the SAME turn as the
launch. It watches, per VM: STARTED < 60s; **progress metric = count of results-index rows written in the run window,
entity-scoped to `(asset_group, campaign_id)` on `time_created`** (NEVER log/heartbeat activity), require ≥1
progress/hr, flat ⇒ STALL ⇒ diagnose; STOPPED/FAILED via terminal `exit_code` from the persisted `run.log` + log-mtime;
verify T+10min.

### 3.3 Results manifest — the skill reads it back, not the data

The VM writes a **results manifest** (not the data) to a dedicated results bucket resolved via
`resolve_bucket_name(...)` (`unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py:366`) with
a new `datapoint-validation` kind (added to `configs/cloud-providers.yaml`, mirroring the flat `defi-validation`
precedent). Layout: `results/{asset_group}/campaign={ts}/_index/…` (per-VM shards under `campaign={ts}/vm={VM_NAME}/`,
consolidated by the standard scheduled consolidator). One row per validated object, written with the UTL
manifest/`base_writer.py` machinery so the skill's existing `read_availability_index` reader works unchanged, carrying:
`{asset_group, venue, chain, instrument_type, data_type, day, object_path, file_generation, campaign_id, schema_verdict + schema_failure_codes[], id_verdict + id_failure_codes[], validated_at}`.

The skill reads it back with a **slim manifest read** (`read_availability_index(columns=[…verdicts…])` on the
`datapoint-validation` bucket for `campaign_id`) — single-walk-exempt, never a re-walk — and folds per-shard PASS/FAIL
counts into the four-surface report's **S2 (content) column**, upgrading it from "sampled" to "100% validated,
campaign={ts}". If no Tier-2 campaign exists for the AG, the report keeps the Tier-1 SAMPLED verdict and says so.

### 3.4 Dispatch decision + autonomous boundary

- **Default = Tier 1 only.** Every invocation runs census + oracle + ≤500 sampled smoke, reporting id/schema SAMPLED.
- **Tier 2 launches** when a 100% id+schema claim is wanted, or to size the blast radius of a Tier-1 sample failure.
  Reuse an existing `campaign_id` if a recent one covers the corpus (no redundant walk).
- **Under `/autonomous` the skill MAY autonomously DISPATCH the read-only Tier-2 scan.** It **reads** parquets and
  **writes only a results index** to the `datapoint-validation` bucket — provably disjoint from every prod DATA kind
  (`raw_tick_data`, `features-*`, …) via `resolve_bucket_name`. A prod-DATA-bucket WRITE or DELETE stays the human-only
  hard stop — the reconciliation skill's autonomous boundary is otherwise unchanged.

---

## 4. Finding-types — which each check emits, and what the taxonomy must add

`reconciliation-finding-taxonomy.md` is the closed set; this doc does not edit it. Three NEW types are required — until
they are added, the census/per-datapoint checks report them under an explicit "taxonomy-gap" banner (per the taxonomy's
own "a disagreement that fits no type is itself a finding" rule).

| Check           | Finding-type                               | New?     | Surface(s)   |
| --------------- | ------------------------------------------ | -------- | ------------ |
| Census (a)/(b)  | `non_canonical_axis_value`                 | NEW      | S1 and/or S3 |
| Census (c)      | `shard_atom_vocab_desync`                  | NEW      | S1 ↔ S3      |
| G2 id-canonical | `non_canonical_id`                         | NEW      | S2 (+ S1)    |
| G3 schema       | `shard_pillar_fail` (+ `masked_empty_row`) | EXISTING | S2           |

**Proposed taxonomy blocks** (the taxonomy owner adds these; this is a todo, not an edit here):

- **`non_canonical_axis_value`** — an axis value (`instrument_type` / `data_type` / `venue` / `chain`) present on a
  surface but outside the canonical UAC vocabulary for that axis + asset_group, grain-resolved via
  `_distinct_values._comparison_set`. Carries a `surface` field (S1 = GCS path segment, S3 = manifest column). Distinct
  from `non_canonical_path`, which is STRUCTURE-only (`canonical_path_violations()` does not validate segment values,
  `partition_paths.py:661`). Severity MEDIUM, date-conditional against `canonical-cutover-register.md`. Delete-eligible
  **NO** (a mis-spelled value is a re-stamp target, never a delete).
- **`shard_atom_vocab_desync`** — for one axis + asset_group, the manifest distinct set and the GCS distinct set
  disagree at vocabulary level (e.g. GCS `instrument_type=pool` while manifest carries `solana_amm_pool`). The
  vocabulary-scale early warning of the phantom / missing_row class before per-shard scan. Severity HIGH.
  Delete-eligible **NO**.
- **`non_canonical_id`** — a parquet row whose `instrument_id` (and, for defi, `canonical_instrument_id`) does not
  byte-match the id rebuilt through `build_canonical_instrument_id` (`canonical_id_builder.py:972`) from the row's own
  structured axes. The id-FORM leg that `non_canonical_path` is structurally blind to. Detected by the Tier-2 scan
  artifact; Tier-1 is a sampled smoke. Not-applicable to legitimately id-less shapes. Suppressed by AE-3 (defi two-id
  model). Severity MEDIUM, date-conditional. Delete-eligible **NO** (a wrong id is migrated / re-keyed, never deleted).

Adding the two estate types raises the taxonomy's estate-type count; the taxonomy owner updates its count line and
delete-eligibility table when adding them.
