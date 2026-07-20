---
doc_type: codex-ssot
title: GCS + manifest delete-safety protocol (five-part proof · disposition vocabulary · human-only hard stops)
summary: >-
  The contract any tool, skill or agent MUST satisfy before proposing — let alone executing — the deletion of a GCS
  object, prefix, bucket or manifest row. Defines the FIVE-PART PROOF (twin resolves via gcs_describe_object · CONTENT
  verify not existence · nothing still WRITES it · nothing still READS it · the legacy-COPIED-not-MOVED invariant), the
  closed disposition vocabulary (yes-twin-confirmed / yes-after-verify / no-migrate-first / no-still-authoritative /
  unknown), the enumerated human-only hard stops an agent never crosses autonomously, and the sanctioned mechanics (UTL
  gcs_* helpers, resolve_bucket_name, never subprocess gcloud/gsutil, never an inline gs://). Absorbs the GCS DELETE
  SAFETY INVARIANT previously stranded in pipeline-mode-partition.md.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    unified-trading-pm,
    unified-trading-library,
    market-tick-data-service,
    instruments-service,
    execution-service,
    deployment-api,
  ]
scope: [engineer, admin]
tags: [delete-safety, canonicalisation, migration, gcs, manifest, data-correctness, hard-rule, reconciliation]
related:
  [
    pipeline-mode-partition.md,
    cross-asset-canonical-target-ssot.md,
    availability-manifest-and-data-status.md,
    defi-canonical-naming-ssot.md,
    ../05-infrastructure/gcs-object-operations.md,
    ../05-infrastructure/bucket-isolation-model.md,
    ../../plans/active/data_pipeline_reconciliation_skill_2026_07_20.md,
    ../../plans/active/issues/defi_dex_pools_delete_order_stale_2026_07_20.md,
  ]
created: 2026-07-20
authoritative_for:
  [
    the five-part delete proof,
    the delete disposition vocabulary,
    human-only delete hard stops,
    the legacy-COPIED-not-MOVED invariant,
  ]
referenced_by:
  [
    codex/02-data/four-surface-reconciliation-procedure.md,
    codex/02-data/reconciliation-finding-taxonomy.md,
    codex/02-data/non-canonical-path-inventory.md,
    codex/02-data/orphan-object-detection.md,
  ]
owner:
last_reviewed: 2026-07-20
code_refs: [unified-trading-library/unified_trading_library/cloud_interface/gcs_blob_ops.py]
---

# GCS + manifest delete-safety protocol

**Deleting data is the only irreversible operation in the pipeline.** Every other mistake — a wrong path, a bad manifest
row, a mis-scoped backfill — is repairable by re-running. A delete is not. This doc is the contract an agent, script or
skill cites before proposing a delete, and the gate it must pass before any suggestion rises above `unknown` confidence.

**Scope**: GCS objects, GCS prefixes, GCS buckets, and availability-manifest rows. It does NOT cover code deletion (that
is `codex/06-coding-standards/`, where deleting deprecated code is required, not gated).

**The default posture is SUGGEST, never EXECUTE.** A read-only reconciliation tool emits dispositions; a human decides.
The reconciliation skill that consumes this contract is
[`plans/active/data_pipeline_reconciliation_skill_2026_07_20.md`](../../plans/active/data_pipeline_reconciliation_skill_2026_07_20.md).

---

## 1. The five-part proof

A delete suggestion may be emitted at a confidence above `unknown` **only when all five parts pass**. Any part failing →
disposition `no-migrate-first` (or `unknown` where the part could not be evaluated at all). There is no partial credit
and no "probably".

### Part 1 — the canonical twin RESOLVES via `gcs_describe_object`, not by path construction

Building the canonical path string and asserting it "should" exist is not evidence. The twin must be **fetched**:

```python
from unified_trading_library.cloud_interface import gcs_describe_object

meta = gcs_describe_object(twin_uri)   # BlobMetadata | None
if meta is None:
    disposition = "no-migrate-first"   # the twin does not exist
```

`gcs_describe_object` returns `BlobMetadata | None` and is `None` for a non-existent object
(`unified-trading-library/unified_trading_library/cloud_interface/gcs_blob_ops.py:51-54`). A `None` return is a **hard
fail** of Part 1, not an inconclusive result.

Measured precedent: the defi `dex_pools/` relic's presumed canonical twin under `venue={ORCA,RAYDIUM,KAMINO,SOLEND}` was
verified ABSENT for KAMINO `dex_pool_state` and SOLEND on both the relic's own day and a recent day — the legacy objects
are the **only copy in existence** for those cells (`plans/active/defi_consolidated_closeout_2026_07_18.md:466-478`).

### Part 2 — a CONTENT verify, not merely existence

**Existence of a twin does not prove duplication.** Two objects at the "same" logical cell can hold disjoint or
partially-overlapping row sets. Compare CONTENT — row keys, not object presence, not object size, not path shape.

**The R5 precedent (the reason this part exists).** The defi close-out plan carried a batch-DELETE order for the "dead
Shape-B `dex_pools/` + `lending_indices/` top-level prefixes", on the premise that they duplicated the canonical tree. A
later content-verify **in the same plan** overturned that verdict: legacy = 98 pools, canonical = 99, **intersection
only 66**, with **32 legacy-only high-TVL Raydium pools absent from canonical** (XMR/USDC $47M,
BNB/USDC $18M, USD1/USDC
$9.9M, ZEC/USDC $7.5M). The paths looked duplicated; the content was not. Executing the original order would have
destroyed 32 high-TVL pools. Evidence and the corrected order:
`plans/active/defi_consolidated_closeout_2026_07_18.md:466-478` and
`plans/active/issues/defi_dex_pools_delete_order_stale_2026_07_20.md`.

A snapshot-before-delete is **not** an adequate substitute for Part 2 — the same source states so explicitly.

### Part 3 — grep-then-READ proof that no live code still WRITES the location

Zero grep hits does NOT mean unwritten; paths are frequently assembled at runtime from templates and registry lookups.
**READ the candidate writer.** Conversely, a docstring describing a write is not proof that the write happens.

Measured precedent, in both directions, in one file: the MTDS dex-pools handler's module docstring declares
`GCS paths: gs://{bucket}/dex_pools/{protocol}/{chain}/date={YYYY-MM-DD}/…`
(`market-tick-data-service/market_tick_data_service/cli/handlers/dex_pools_handler.py:17-18`), while the code twenty
lines further down records that the canonical on-disk `data_type` is `dex_pool_state` — "identical to the on-disk path
`data_type=` segment `write_defi_rows` emits. The legacy 2-layer split (on-disk `dex_pool_state` vs manifest
`dex_pools`) is RETIRED" (`…/dex_pools_handler.py:80-84`). **The docstring describes a write the code does not
perform.** Docstrings and comments are never evidence for Part 3 — only the emitting call path is.

### Part 4 — grep-then-READ proof that no live code still READS it

A location with no writer may still have live readers, and deleting under a live reader is a production incident, not a
cleanup.

Measured precedent: `execution-service` reads the legacy `dex_pools/` shape **today**. The template is
`_DEX_POOLS_PATH_TEMPLATE = "dex_pools/{protocol}/SOLANA/date={date}/"`
(`execution-service/execution_service/providers/solana_amm_depth_provider.py:41`) and it is used as a live GCS prefix
scan at `…/solana_amm_depth_provider.py:258` → `storage.list_blobs(bucket, prefix=prefix)` at `:288`. The same file's
read path is also referenced by `execution_service/data/defi_lateral_loader.py:61` and
`execution_service/data/validator.py:250,257`.

**Part 4 fails "loudly-broken" readers too.** A reader that currently raises is still a reader: it is a repoint
obligation, not a licence to delete. `SolanaAmmDepthProvider._load_from_gcs` calls
`resolve_bucket_name(cloud="gcp", kind="market-data-tick-defi", asset_group="defi", env="prod", project_id=…)`
(`…/solana_amm_depth_provider.py:248-254`); the close-out plan records that this call **raises** —
`kind="market-data-tick-defi"` is a bucket-name fragment with no yaml key and `env=`/`project_id=` are not parameters
(`plans/active/defi_consolidated_closeout_2026_07_18.md:475-477`). Correct sequencing is repoint-then-delete; the
required order for this specific case is stated in that plan's correction banner.

### Part 5 — the LEGACY-COPIED-NOT-MOVED invariant

_(Absorbs the GCS DELETE SAFETY INVARIANT codified 2026-06-18, previously stranded at
`pipeline-mode-partition.md:66-77`. That doc should point here rather than restate it.)_

The v9 migration **COPIED** objects to canonical `pipeline_mode={mode}_{source}/asset_group={ag}/…` paths — **COPY, not
MOVE**. The legacy bare `asset_group=` / `category=` / top-level `day=` shapes therefore still exist alongside the
canonical ones. Two consequences that together form the trap:

1. **The manifest `_index` is CELL-KEYED and path-agnostic** — it does not by itself tell you whether a cell's data sits
   at a canonical path.
2. **A reconcile prefix-matches BOTH shapes** — so a green reconcile only proves "some object exists", never "a
   canonical object exists".

Therefore a cell backed **only** by a legacy copy passes reconcile, yet:

- a blind delete of the legacy copy ORPHANS that cell (its data is simply gone), and
- it already reads **MISSING** under canonical-only data-status (deployment-api `DATA_STATUS_CANONICAL_PATHS_ONLY`).

The invariant: **never delete a legacy object without `gcs_describe_object`-verifying a twin already in CANONICAL
format** (for defi, additionally with normalized venue / instrument_type). Require **100% canonical-twin coverage per
asset_group** before executing that asset_group's delete list. Where no twin exists, the object is `no-migrate-first`:
COPY to canonical via the `migrate_*_v9_canonical` path first, then re-evaluate.

---

## 2. Disposition vocabulary (closed set)

Every candidate location carries exactly one of these five values. The set is closed — a tool that needs a sixth value
has found a gap in this doc and must say so rather than invent one.

| Disposition              | Meaning                                                                                                   | Proof state                                               | Who may act                     |
| ------------------------ | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | ------------------------------- |
| `yes-twin-confirmed`     | Canonical twin exists AND content-verified equivalent; no live writer; no live reader.                    | All 5 parts PASS.                                         | Human executes; agent suggests. |
| `yes-after-verify`       | Strong evidence of redundancy, but at least one part evidenced by sampling rather than exhaustively.      | All 5 parts pass, ≥1 by sample — name the sample in-line. | Human executes; agent suggests. |
| `no-migrate-first`       | Twin absent, content diverges, or a live writer/reader remains. Migration or repoint precedes any delete. | ≥1 part FAILS.                                            | Nobody deletes. Fix first.      |
| `no-still-authoritative` | The location is the current SSOT for its data, canonical shape or not. Not a delete candidate at all.     | Not applicable — deletion is wrong by definition.         | Nobody.                         |
| `unknown`                | Default. A part could not be evaluated (twin unknown, content unreadable, consumer set unresolved).       | Insufficient evidence.                                    | Nobody. Investigate.            |

**`unknown` is the default value**, not a fallback. A location starts at `unknown` and is promoted only by evidence. A
tool that emits anything above `unknown` without all five parts recorded is in violation of this doc.

Each emitted disposition MUST carry, inline: the twin URI probed (or `NONE`), the content-verify method and result, the
writer grep+READ result, the reader grep+READ result, and the twin-coverage percentage for the enclosing asset_group.

---

## 3. Human-only hard stops

These are **never** crossed autonomously, at any confidence, under `/autonomous`, or on any operator instruction that
does not name the specific stop in the same turn. An agent that believes one of these should proceed escalates with
structured options (per `SUB_AGENT_MANDATORY_RULES.md` § escalation) — it does not act.

1. **Any prod-bucket delete.** Object, prefix or bucket, in any `-prd-` / production-serving bucket. There is no
   confidence level at which an agent deletes from prod.
2. **Any legacy-object delete after copy.** The entire v9-migration legacy estate is gated by Part 5 above; the copy
   made the legacy object look redundant without proving it is.
3. **The tradfi `batch_massive` purge.** All objects under
   `gs://market-data-tick-tradfi-prd-{pid}/…/pipeline_mode=batch_massive`. Massive (formerly Polygon.io) was removed as
   a tradfi source 2026-07-19, but `batch_massive` **read-recognition** (`PipelineMode` + `possible_manifest`) is
   deliberately KEPT until the purge completes — removing recognition before the purge makes the phantom audit flag the
   entire corpus as unreachable. Design doc: `plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md`;
   vendor removal: `codex/02-data/tradfi-databento-sourcing-ssot.md`. **UNVERIFIED — object count**: the audit synthesis
   states the scale in two mutually inconsistent forms (a "1.47M-object purge" and "1,696,166 objects"). Neither was
   independently re-measured for this doc. Treat the scale as ~1.5M and re-measure before any purge; do not cite either
   figure as settled.
4. **Anything touching `instrument_type` casing — RULED UPPERCASE (D1), still a human-only hard stop for prod-scale
   rewrites.** ⛔ corrected 2026-07-20: this axis was previously "unruled / this doc does not pick a side"; the operator
   **ruled UPPERCASE for the manifest COLUMN** on 2026-07-20 (D1). The delete-safety consequence is **unchanged** — an
   object or row whose only non-canonical attribute is `instrument_type` casing is a `migration_pending` fold-UP item
   (repaired in place, **never a delete candidate**), and prod-scale casing rewrites (>12M rows, incl. defi rows not yet
   folded UP) remain a human-only hard stop. See § 4.
5. **The defi `dex_pools/` + `lending_indices/` delete.** The standing delete orders in
   `defi_consolidated_closeout_2026_07_18.md` Track 2 and `canonical_closeout_open_questions_2026_07_18.md` §A6 are
   **STALE and would destroy data** — overturned by R5 in the same plan (Part 2 above). Current disposition is
   FOLD-not-delete, in the order: (1) content-UNION the 32 legacy-only pools and the twin-less cells into canonical; (2)
   repoint `execution-service/execution_service/providers/solana_amm_depth_provider.py` to `data_type=dex_pool_state`
   and fix its raising `resolve_bucket_name` call; (3) only then consider delete. Issue doc:
   `plans/active/issues/defi_dex_pools_delete_order_stale_2026_07_20.md`.

**Not a hard stop, but adjacent**: manifest-row deletion via a phantom-audit `--apply`. That has its own gate —
`--apply` only after `prefix_tpls` cover every current path shape, verified by a clean `--dry-run` — documented at
`pipeline-mode-partition.md:94-101`. Running `--apply` against stale templates flips real `captured` rows to
`attempted_failed`, silently corrupting honest-coverage accounting.

---

## 4. Formerly-open axes — both RULED 2026-07-20 (retained as delete-safety guidance)

> **⛔ corrected 2026-07-20, operator rulings D1 + D2.** ~~"Open questions this doc deliberately does not resolve … this
> doc reports the disagreement and refuses the axis."~~ Both axes below were **RULED 2026-07-20** (recorded in
> `plans/active/data_pipeline_reconciliation_skill_2026_07_20.md` § "OPERATOR DECISIONS"). The delete-safety consequence
> is UNCHANGED by the rulings — neither axis ever makes an object a delete candidate — but they are no longer "open".

**C2a — manifest `instrument_type` column case. ✅ RULED UPPERCASE (D1).** Was contested (both sides `status: current`,
both dated 2026-07-18, both citing the operator: LOWERCASE = `cross-asset-canonical-target-ssot.md` §7/§11; UPPERCASE
catalogue-as-SSOT = `plans/active/tradfi_consolidated_closeout_2026_07_18.md` Phase-B). **Operator ruled UPPERCASE for
the manifest COLUMN**; the shipped cefi/tradfi uppercase scripts are RATIFIED. **Consequence for delete safety
(unchanged)**: an object or row whose only "non-canonical" attribute is `instrument_type` casing is a
`migration_pending` fold-UP item, **never a delete candidate** — a casing difference is repaired in place, not deleted.

**Defi flat `LENDING` instrument_type. ✅ RULED — full retire is the TARGET, NOT yet implemented (D2).**
`cross-asset-canonical-target-ssot.md` §5's "`LENDING` is RETIRED (A_TOKEN/DEBT_TOKEN split, ~16.7M rows)" is the
correct TARGET, but the first attempt was **reversed in code** because it broke 5+ (really 8) MTDS lending writers into
`attempted_failed`/zero-data. Order: fix writers → migrate → re-sync atom, gated on
`plans/active/defi_lending_writer_retire_prerequisite_2026_07_20.md`. **Consequence for delete safety (unchanged)**:
flat `LENDING` on market/event data_types is `migration_pending` — never a finding, never a delete trigger — until the
migration lands.

---

## 5. Sanctioned mechanics

**Object operations — UTL helpers only.** Import from `unified_trading_library.cloud_interface`:

| Helper                              | Signature                                  | Use                                              |
| ----------------------------------- | ------------------------------------------ | ------------------------------------------------ |
| `gcs_describe_object(uri)`          | `-> BlobMetadata \| None`                  | Part 1 twin resolution; `None` = does not exist. |
| `gcs_copy_object(src_uri, dst_uri)` | `-> None` (server-side rewrite, no egress) | The migrate step of `no-migrate-first`.          |
| `gcs_delete_object(uri)`            | `-> None`                                  | The delete itself — human-gated per § 3.         |

Definitions: `unified-trading-library/unified_trading_library/cloud_interface/gcs_blob_ops.py:38` (copy), `:45`
(delete), `:51` (describe). All three split the `gs://` URI and dispatch through `get_storage_client()`.

**Never a subprocess.** `gcloud` / `gsutil` spawns cost ~500ms per call versus ~50-200ms for the REST helpers, and the
helpers release the GIL so `ThreadPoolExecutor` workers parallelise — a measured 250× throughput difference (~8,500 vs
~34 parquets/min at 32 workers). Rationale and benchmark:
[`codex/05-infrastructure/gcs-object-operations.md`](../05-infrastructure/gcs-object-operations.md), which remains the
SSOT for the helpers themselves; this doc governs only when a delete may be called.

**Never an inline `gs://` bucket literal (QG 5.69).** Resolve every bucket via
`resolve_bucket_name(cloud, kind, asset_group, deployment_env)` over `cloud-providers.yaml`. Pass `deployment_env=` —
never mutate process env to reach a tier. Do not use a bucket-name **fragment** as a `kind` (that is precisely the
raising call in Part 4). SSOT:
[`codex/05-infrastructure/bucket-isolation-model.md`](../05-infrastructure/bucket-isolation-model.md).

**Enumeration is walk-disciplined.** Building a delete candidate list must not open a new whole-corpus GCS walk (that is
review-blocking). Use the manifest-driven route or a sanctioned prefix-scoped / delimiter listing. SSOT:
[`availability-manifest-and-data-status.md`](availability-manifest-and-data-status.md) § 9.

**Pre-delete drain.** Any campaign that will delete or move objects at scale is preceded by the pre-migration drain —
stop all VMs on both clouds, consolidate the manifest, snapshot — per `codex/05-infrastructure/vm-launcher-runbook.md`.
Note that a snapshot does not substitute for Part 2 (§ 1).

---

## 6. Checklist an agent pastes into its report

```
Location:            <gs:// prefix or manifest cell>
Part 1 twin probe:   gcs_describe_object(<uri>) -> <BlobMetadata|None>
Part 2 content:      <method> -> legacy N / canon M / intersection K / legacy-only L
Part 3 writers:      grep <symbol> -> <hits>; READ <file:line> -> WRITES? yes/no
Part 4 readers:      grep <symbol> -> <hits>; READ <file:line> -> READS? yes/no
Part 5 twin coverage: <pct>% canonical-twin coverage for asset_group=<ag>
Disposition:         <yes-twin-confirmed|yes-after-verify|no-migrate-first|no-still-authoritative|unknown>
Hard stop:           <none|prod-bucket|legacy-after-copy|batch_massive|instrument_type-casing|defi-dex_pools>
```

Any line reading `NOT EVALUATED` forces the disposition to `unknown`.
