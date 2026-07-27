---
doc_type: issue
title:
  Static audit of the four backfill-smoke skills — test-bucket-only enforcement is real but implemented FOUR different
  ways (one with a prod-write escape hatch), and two audited writers still emit non-canonical GCS paths
summary: >-
  Code-read audit (no backfill run, no VM launched) answering two questions for /data-pipeline-check-is,
  /data-pipeline-check-mtds, /data-pipeline-check-mdps and /data-pipeline-check-features. (1) Test-bucket-only: every
  default path writes only to a `-test-` bucket, but via four DIFFERENT mechanisms — IS/MTDS route through
  `IS_TEST_RUN=true` metadata baked by the launcher, MDPS through an explicit `--output-bucket` string, features through
  an explicit `--sink-bucket` string. IS is fail-closed (`--test-run` is hardcoded into every argv, no CLI flag can
  remove it); MTDS carries one genuine prod-write escape hatch, `--allow-live-prod-writes`, which launches
  launch-mtds-live.sh WITHOUT --test-run; MDPS and features are fail-OPEN (drop the bucket string and the run writes
  PROD, no guard). MTDS's freshness READ is confirmed PROD-scoped as the skill already documents. (2) Canonical grammar:
  MTDS PartitionedTickWriter emits canonical paths for cefi/tradfi/prediction, but the CeFi CHAIN tail falls through to
  the bare v5 `underlying={U}/ticks.parquet` because quote/margin are populated for tradfi ONLY; and the
  instruments-service instrument_availability writer emits the FLAT two-key `day=/venue=` shape with no `pipeline_mode=`
  and no `asset_group=`, contradicting three in-repo comments that assert it emits the hive layout. The UTL sink sorts
  partition keys ALPHABETICALLY, so canonicalising IS by adding keys to the partition dict is structurally impossible —
  it needs the sink PREFIX mechanism the sports lane already uses.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    unified-trading-library,
    unified-api-contracts,
    deployment-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [data-correctness, canonical, gcs-paths, test-isolation, smoke-check, skills, mtds, instruments-service]
related:
  [
    ../data_pipeline_reconciliation_skill_2026_07_20.md,
    /codex/02-data/non-canonical-path-inventory.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
    /codex/05-infrastructure/bucket-isolation-model.md,
  ]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
assigned_role: data
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  STATIC code read 2026-07-20 for TODO P1-15 of data_pipeline_reconciliation_skill_2026_07_20.md (skill § 4c). No
  backfill was run, no VM was launched, no GCS object was written or read. Every claim below cites a file:line that was
  opened and read, not grepped.
---

# Backfill-smoke write paths — test-bucket enforcement and canonical-grammar audit

> **Scope discipline**: this is the § 4c static audit the `/data-pipeline-reconciliation` skill mandates. It **reports**
> writer defects; it does not fix them. Each defect below belongs to its own service's plan — fixing it here risks a
> collision with the agent that owns that repo.

## 1. Verdict — do the smoke skills write to `-test-` buckets only?

**Yes on every default path — but through four different mechanisms with materially different failure modes.** Two are
fail-closed, two are fail-open, and one carries an explicit prod-write escape hatch.

All four sibling skills exist in `cursor-configs/skills/` as of this audit: `data-pipeline-check-is`,
`data-pipeline-check-mtds`, `data-pipeline-check-mdps`, `data-pipeline-check-features`.

| Skill / driver                                                                         | Enforcement mechanism (verified)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | Fail mode                                                                      | Prod-write path?                                            |
| -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ----------------------------------------------------------- |
| `/data-pipeline-check-is` → `instruments-service/scripts/pipeline_e2e_check.py`        | `--test-run` is **hardcoded** into the launcher argv at `instruments-service/scripts/pipeline_e2e_check.py:398`. The argparse block (`:1032`-`:1071`) exposes no flag that can remove it. The launcher bakes `IS_TEST_RUN=true` into VM metadata (`deployment-service/scripts/vm/launch-instruments-backfill-vm.sh:178`), and `_get_instruments_bucket()` (`instruments-service/instruments_service/engine/orchestrator/catalogue.py:55-79`) turns that into `deployment_env="test"` for **both** the write and the freshness read. | **Fail-closed.** No code path in this script reaches a prod bucket.            | **None.**                                                   |
| `/data-pipeline-check-mtds` → `market-tick-data-service/scripts/pipeline_e2e_check.py` | Batch force/skip legs hardcode `--test-run` at `market-tick-data-service/scripts/pipeline_e2e_check.py:1369`; default live leg at `:2014`. Launcher bakes `IS_TEST_RUN=true` (`launch-mtds-backfill-vm.sh:198`). The WRITE target resolves through `get_tick_data_bucket(..., test_aware=True)` (`.../engine/orchestrator/__init__.py:772-829`, test tier at `:809`, `:822-828`), called on the write path at `.../__init__.py:667`, `:681` and `.../engine/orchestrator/_manifest_bucket.py:74`.                                   | **Fail-closed on the default sweep; one explicit opt-in hatch.**               | **YES — `--allow-live-prod-writes`.** See § 1a.             |
| `/data-pipeline-check-mdps`                                                            | The skill instructs `launch-mdps-backfill-vm.sh … --output-bucket market-data-tick-<ag>-test-<pid>` (`data-pipeline-check-mdps/SKILL.md:108`). The launcher turns that string into `MDPS_OUTPUT_BUCKET_{CAT}` (`deployment-service/scripts/vm/launch-mdps-backfill-vm.sh:114`, `:222-223`, `:281`).                                                                                                                                                                                                                                 | **Fail-OPEN.** Omit or mistype `--output-bucket` and the run writes PROD.      | Yes, implicitly — the absence of the flag IS the prod path. |
| `/data-pipeline-check-features`                                                        | The skill instructs `launch-features-vm.sh … --sink-bucket features-<ag>-test-<pid>` (`data-pipeline-check-features/SKILL.md:146`). The launcher converts that into `IS_TEST_RUN=true` **plus** `PROTOCOL_DATA_SINK_BUCKET_{AG}` (`deployment-service/scripts/vm/launch-features-vm.sh:111-112`, `:159`, `:263-266`).                                                                                                                                                                                                               | **Fail-OPEN.** No `--sink-bucket` → no `IS_TEST_RUN`, no sink override → PROD. | Yes, implicitly.                                            |

### 1a. The one genuine prod-write code path — MTDS `--allow-live-prod-writes`

`market-tick-data-service/scripts/pipeline_e2e_check.py:2561` registers the flag; `:2642` threads it into the run;
`_run_live_leg` branches on it at `:1983` and delegates to `_run_live_leg_prod_unbounded` (`:2118-2172`). That function
builds its launcher argv at `:2140-2149` **without `--test-run`** — so `IS_TEST_RUN` is never set, `test_aware` never
fires, and `get_tick_data_bucket` returns the PROD `-prd-` bucket. The docstring is honest about this ("the OLD
real-PROD, forever-running live launch — explicit opt-in only, never used by the default sweep"), and it is additionally
fire-and-forget: it returns `status="skipped"` with "verification skipped" because the VM never terminates.

**Assessment**: this is a correctly-gated, clearly-documented escape hatch, not a latent bug. But
`data-pipeline-check-mtds/SKILL.md` never mentions the flag, so nothing in the skill text tells an agent not to reach
for it. Recommend the skill add an explicit prohibition (todo below).

### 1b. The known IS/MTDS asymmetry — CONFIRMED

The lead is correct and the code matches the existing documentation. `TickDataHandler._resolve_freshness_bucket()`
(`market-tick-data-service/market_tick_data_service/cli/handlers/tick_data_handler.py:123-134`) calls
`get_tick_data_bucket(None, asset_group=...)` at `:133` — **without `test_aware=True`**, so the default
`test_aware: bool = False` (`.../engine/orchestrator/__init__.py:772`) applies and the resolver falls to
`get_market_data_bucket(ag)` at `:829`, which resolves off `DEPLOYMENT_ENV_SHORT`, not `IS_TEST_RUN`.

So under `--test-run` MTDS **reads PROD capture state and writes the `-test-` bucket**. This is a read/write split, not
a prod-write leak: the write target is genuinely test-only. It is already handled correctly — `prod_precheck.py`
(`unified-trading-library/unified_trading_library/pipeline_e2e_check/prod_precheck.py:4-21`, `:33-56`) exists precisely
to label a skip verdict `genuine (prod-captured)` vs `ambiguous`, and the MTDS skill documents the asymmetry at
`SKILL.md:27` and `:187`. No action needed; recorded here so a future reader does not re-derive it as a finding.

**IS, by contrast, is self-contained**: `catalogue.py:78` sets `deployment_env = "test" if cfg.is_test_run else None`
for the single resolver both the read and the write use — which is why the IS skill can call its skip proof complete.
MDPS is likewise self-contained by construction (same bucket read and written —
`data-pipeline-check-mdps/SKILL.md:31-33`).

## 2. Writer audit table — does each write path emit the canonical grammar?

Scope per the todo: **market-tick-data-service and instruments-service**.

| #   | Writer / path-builder (file:line)                                                                                                   | Emits canonical?              | Shape emitted                                                                                                                                                                                                  |
| --- | ----------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `market-tick-data-service/.../engine/orchestrator/symbol_rules.py:383-466` `_build_partition_path_for_asset_group` — **cefi**       | ✅ yes                        | `raw_tick_data/by_date/day={D}/pipeline_mode={m}/asset_group=cefi/venue={V}/instrument_type={IT}/data_type={DT}/{file_name}` (`pipeline_mode` inserted at `:466`)                                              |
| 2   | same, **tradfi** branch `:418-429`                                                                                                  | ✅ yes                        | same grammar; inline build (`:426-429`) because the UAC enum lacks some series-class tokens; `pipeline_mode=` inserted by the shared `.replace` at `:466`                                                      |
| 3   | same, **prediction** branch `:430-439`                                                                                              | ✅ yes                        | same grammar, `asset_group=prediction`                                                                                                                                                                         |
| 4   | same, **sports / defi**                                                                                                             | n/a — raises                  | `:440-444` raises `ValueError` rather than emitting a wrong shape. Correct fail-loud design.                                                                                                                   |
| 5   | `unified-api-contracts/.../canonical/partition_paths.py:194-253` `build_cefi_partition_path`                                        | ✅ yes (the builder is right) | v5 base `:242-245`; v6 chain tail `:249-253` gated on `is_chain and underlying and quote_asset and margin_type`                                                                                                |
| 6   | **`market-tick-data-service/.../engine/orchestrator/partitioned_writer.py:171-215` `_resolve_writer_file_name` (W1) — CEFI CHAINS** | ❌ **NO**                     | bare v5 `underlying={U}/ticks.parquet` (`:201`) instead of canonical `underlying={U}/quote={Q}/margin={M}/ticks.parquet` (`:197-200`). See § 3a.                                                               |
| 7   | `market-tick-data-service/.../market_interface/adapters/cefi/tardis_shared.py:598-640` `build_partition_path` (W2)                  | ✅ yes                        | passes `quote_asset` / `margin_type` / `underlying` from its call site (`:861-870`) → emits the v6 chain tail. This is the writer W1 diverges from.                                                            |
| 8   | **`instruments-service/.../engine/orchestrator/process_write.py:612` + `writers.py:201-208`** — `instrument_availability`           | ❌ **NO**                     | `instrument_availability/by_date/day={D}/venue={V}/instruments.parquet` — **flat, two keys**, no `pipeline_mode=`, no `asset_group=`. See § 3b.                                                                |
| 9   | `instruments-service/.../engine/orchestrator/writers.py:377-383` — `futures_contracts.parquet`                                      | ❌ no                         | same flat `day={D}/venue={V}/` prefix (same sink, same two-key partition dict) → `…/day={D}/venue={V}/futures_contracts.parquet`                                                                               |
| 10  | `instruments-service/.../engine/orchestrator/process_write.py:614` + `writers.py:495-501` — `market_lifecycle`                      | ❌ no                         | partition `{"group","day","venue"}` → alphabetical sort emits `market_lifecycle/by_canonical_group/group={G}/day={D}/venue={V}/…` — **`day=` is not first**. See § 3c.                                         |
| 11  | `instruments-service/.../engine/orchestrator/sports_fixtures.py:99-113` `_sports_ref_sink_for`                                      | ✅ yes                        | `sports_reference/by_date/day={D}/pipeline_mode={pm}/entity={E}/league={L}/…` — day and pipeline_mode are in the **prefix**; only `entity`/`league` go in the partition dict. **This is the correct pattern.** |
| 12  | `instruments-service/.../engine/orchestrator/writers.py:589-595` — `sports_reference/venues`                                        | n/a                           | `partition={}` (`:592`) → `sports_reference/venues/venues.parquet`. A singleton reference object, not a dated shard; not in the shard grammar's scope.                                                         |

## 3. The non-canonical writers — highest-value findings

### 3a. MTDS W1 emits the bare v5 CeFi chain tail; W2 emits the canonical v6 one (dual-shape corpus)

`partitioned_writer.py:291-293`:

```python
quote_asset, margin_type = "", ""
if is_derivative and self._asset_group == "tradfi" and itype_str in ("futures_chain", "options_chain"):
    underlying_str, quote_asset, margin_type = _tradfi_chain_partition_dims(underlying_str)
```

The lead is **CONFIRMED**. `quote_asset` / `margin_type` are populated for `tradfi` ONLY. For a **cefi** `options_chain`
/ `futures_chain` they stay `""`, so `_resolve_writer_file_name` takes the `:201` branch and returns
`underlying={U}/ticks.parquet` instead of the `:197-200` canonical tail. Meanwhile W2 (`tardis_shared.py:861-870`)
passes all three axes and emits the canonical v6 shape for the same asset_group. The corpus therefore carries **both**
shapes for cefi chains — exactly the v5/v6 dual chain-tail hazard the reconciliation skill's § 3d cefi row already warns
about, now traced to its source line.

Two aggravating details found while reading:

1. `partitioned_writer.py:249-258` calls `_build_partition_path_for_asset_group` **without** `underlying` /
   `quote_asset` / `margin_type` — the UAC v6 branch (`partition_paths.py:249`) is unreachable from W1 by construction;
   the tail arrives only via `file_name`. Any fix that only populates the dims at `:291` must also confirm the tail
   reaches the path.
2. **Casing divergence**: `:198` upper-cases the underlying (`underlying.upper()`); `:201` does **not**
   (`f"underlying={underlying}/…"`). So the two shapes can differ in case as well as in segment count.

**Owner**: market-tick-data-service. Do not fix from a reconciliation/skill plan.

### 3b. instruments-service `instrument_availability` emits the FLAT shape — three in-repo comments say otherwise

Settled by reading both halves of the write:

- `instruments-service/instruments_service/engine/orchestrator/process_write.py:612`
  `sink = _orch.get_data_sink(bucket=bucket, prefix="instrument_availability/by_date")` — the prefix carries **no**
  `pipeline_mode=`, **no** `asset_group=`.
- `instruments-service/instruments_service/engine/orchestrator/writers.py:201-208`
  `_gated_sink_write(sink, data=…, partition={"day": date, "venue": venue_str}, filename="instruments.parquet", …)` —
  two partition keys, nothing else.

Emitted shape: **`instrument_availability/by_date/day={D}/venue={V}/instruments.parquet`**.

The claims this contradicts (all READ, not grepped):

- `market-tick-data-service/market_tick_data_service/instrument_availability_paths.py:1-23` — module docstring states
  the tree "was re-homed on 2026-07-09 … **to** the SOURCE-AWARE hive layout". The one-time migration did produce hive
  objects (for cefi); the **live writer** was never changed, so the tree is mixed, not re-homed.
- `instruments-service/docs/DEFI_INSTRUMENTS.md:642` — documents the hive path as the current shape.
- `instruments-service/scripts/repair_tradfi_instrument_type_counts_2026_07_17.py:21` and `:181`, plus
  `canonicalize_cefi_defi_instrument_type_2026_07_17.py:38`/`:203` — one-off scripts that CONSTRUCT the hive path and
  will therefore miss any object the live writer has emitted since the migration.

This matches `/codex/02-data/non-canonical-path-inventory.md` entry 16, which already records the same verdict as
VERIFIED 2026-07-20 with the same two citations. This audit **independently reproduces** that finding from the code; it
is not a re-report of the doc.

**Data-correctness consequence**: every day since the 2026-07-09 migration, the live IS writer has been laying down
objects at the legacy flat path while migration/repair tooling looks at the hive path. Any tool keyed on the hive shape
under-counts; any tool keyed on the flat shape misses the migrated cefi objects. **Operator notification warranted.**

**Owner**: instruments-service. Do not fix from a reconciliation/skill plan.

### 3c. THE TRAP — the UTL sink sorts partition keys alphabetically, so the obvious fix is wrong

`unified-trading-library/unified_trading_library/cloud_interface/providers/protocol_impls.py:23-29`:

```python
def _build_partition_path(prefix: str, partition: dict[str, str] | None, filename: str) -> str:
    parts = [prefix.rstrip("/")]
    if partition:
        for k, v in sorted(partition.items()):
            parts.append(f"{k}={v}")
    parts.append(filename)
    return "/".join(p for p in parts if p)
```

`sorted(partition.items())` at `:26` — **CONFIRMED**. The read side does the same at `:102`.

So "just add `asset_group` and `pipeline_mode` to the partition dict" produces:

```
instrument_availability/by_date/asset_group={ag}/day={D}/pipeline_mode={m}/venue={V}/instruments.parquet
```

Wrong on **both** counts required by `/codex/02-data/pipeline-mode-partition.md`: `day=` must come first, and
`pipeline_mode=` must sit immediately after `day=` (left of `asset_group=`). Alphabetically `asset_group` < `day` <
`pipeline_mode` < `venue`, which is a different order and cannot be reached by renaming keys.

**The correct mechanism is the sink PREFIX** — exactly what the sports lane already does. `sports_fixtures.py:99-113`
builds `prefix=f"sports_reference/by_date/day={date}/pipeline_mode={pm}"` and leaves only the keys whose alphabetical
order happens to be canonical (`entity` < `league`) in the partition dict; its own docstring at `:104-107` states the
reasoning explicitly. Any canonicalisation of `instrument_availability` must follow that pattern.

The same trap already bit `market_lifecycle` (row 10): `partition={"group","day","venue"}` sorts to
`group=/day=/venue=`, putting `group=` ahead of `day=`.

## 4. UNVERIFIED / out of scope

1. **Whether prod GCS actually contains both cefi chain shapes.** § 3a is a code-level proof that W1 and W2 emit
   different tails; confirming the resting corpus carries both requires a prod listing, which this static audit did not
   perform (and which the reconciliation skill's Phase 1 owns).
2. **Whether the flat `instrument_availability` objects outnumber the hive ones, and from which date.** Requires a
   prod-bucket listing. Not attempted.
3. **`_gated_sink_write` internals.** Verified only that it forwards `partition` and `filename` to the sink; the gating
   predicate itself (emission policy) was not read. It does not affect path construction.
4. **MDPS and features writer path builders.** Explicitly out of this todo's scope (which named MTDS and IS). They are
   already covered by `plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md`.
5. **DeFi write paths in MTDS.** `_build_partition_path_for_asset_group` raises for defi (`symbol_rules.py:440-444`);
   defi writes go through `write_defi_rows` / per-handler builders, which this audit did not open.
6. **AWS-side bucket resolution.** `get_write_bucket_name`'s legacy fallback (`cloud_constants.py:379-385`)
   string-mangles `-test-` into an untiered name. Only the GCP path was traced; the AWS branch was read but not
   exercised.

## Acceptance criteria for closing this issue

1. `data-pipeline-check-mtds/SKILL.md` explicitly names `--allow-live-prod-writes` as a prohibited flag for the skill.
2. `data-pipeline-check-mdps` and `data-pipeline-check-features` gain a Phase-0 assertion that the resolved write bucket
   contains `-test-`, so the fail-open mechanism becomes fail-closed at the skill layer.
3. The instruments-service `instrument_availability` writer either emits the canonical shape via the sink PREFIX
   mechanism, or the three in-repo comments in § 3b are corrected to describe the flat shape the code actually emits.
4. The MTDS W1/W2 cefi chain-tail divergence has a ruling on which shape is canonical, recorded in
   `/codex/02-data/non-canonical-path-inventory.md`.

## Follow-up todos

- [x] 1. [DATA] P1. **[already covered by
      plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md, see that doc for execution]**
      instruments-service: canonicalise the `instrument_availability` write to
      `…/day={D}/pipeline_mode={m}/asset_group={ag}/venue={V}/instruments.parquet` using the sink **PREFIX** mechanism
      (`sports_fixtures.py:99-113` is the working reference), NOT the partition dict — the UTL sink sorts keys
      alphabetically (`protocol_impls.py:26`). Provenance: this audit § 3b/§ 3c.
- [x] 2. [DATA] P1. **[already covered by plans/active/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md, see
      that doc for execution]** market-tick-data-service: rule on and fix the cefi chain tail —
      `partitioned_writer.py:291-293` populates `quote_asset`/`margin_type` for tradfi only, so W1 emits bare
      `underlying={U}/ticks.parquet` while W2 (`tardis_shared.py:861-870`) emits the canonical v6 tail. Include the
      `:198` vs `:201` casing divergence. Provenance: this audit § 3a.
- [ ] 3. [DOCS] P2. instruments-service + market-tick-data-service: correct the three in-repo comments that assert the
      IS live writer emits the hive layout (`instrument_availability_paths.py:1-23`, `DEFI_INSTRUMENTS.md:642`,
      `repair_tradfi_instrument_type_counts_2026_07_17.py:21`). Provenance: this audit § 3b.
- [ ] 4. [SCRIPT] P2. unified-trading-pm: add a Phase-0 `-test-` assertion on the resolved WRITE bucket to
      `data-pipeline-check-mdps` and `data-pipeline-check-features`, closing their fail-open `--output-bucket` /
      `--sink-bucket` mechanism. Provenance: this audit § 1.
- [ ] 5. [DOCS] P2. unified-trading-pm: add an explicit "never pass `--allow-live-prod-writes`" prohibition to
      `data-pipeline-check-mtds/SKILL.md`. Provenance: this audit § 1a.
- [ ] 6. [DATA] P3. instruments-service: decide whether `market_lifecycle` (`writers.py:495-501`,
      `partition={"group","day","venue"}` → `group=/day=/venue=`) and `futures_contracts` (`writers.py:377-383`, flat
      `day=/venue=`) are in the canonical shard grammar's scope; if so they inherit todo 1's fix. Provenance: this audit
      § 2 rows 9-10.
