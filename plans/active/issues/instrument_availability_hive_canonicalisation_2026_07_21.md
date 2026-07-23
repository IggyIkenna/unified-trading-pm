---
doc_type: issue
title:
  instrument_availability full-hive canonicalisation (2026-07-21) — reduced-flat tree must use the full canonical hive
  grammar
summary: >-
  Operator HARD RULE 2026-07-21 — every data-at-rest bucket MUST use the full canonical hive grammar (the canonical key
  set including pipeline_mode= and asset_group=, in the canonical ORDER), not a reduced/flat subset.
  instrument_availability is FLAT today in BOTH the UTL registry and the live instruments-service writer (day= + venue=
  only, missing pipeline_mode=/asset_group=/instrument_type=). market_lifecycle and futures_contracts carry the same
  reduced-flat shape. The fix MUST use the sink PREFIX mechanism to bake the ordered canonical keys, NOT the partition
  dict — the UTL sink sorts partition-dict keys ALPHABETICALLY, so adding keys to the dict produces the wrong order
  (asset_group first, day not first). The registry template is the SSOT and must be updated to the full-hive shape too.
status: open
nature: issue
asset_group: [cefi, tradfi, defi, prediction]
stage: [data]
repos: [instruments-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    canonicalisation,
    instrument-availability,
    hive,
    pipeline-mode,
    asset-group,
    market-lifecycle,
    futures-contracts,
    sink-prefix,
    migration,
    operator-ruling,
  ]
related:
  [
    /plans/active/issues/features_by_date_root_canonicalisation_2026_07_21.md,
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    /codex/02-data/canonical-cutover-register.md,
    /codex/02-data/non-canonical-path-inventory.md,
    /codex/02-data/pipeline-mode-partition.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-21
last_updated: 2026-07-21
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: operator HARD RULE 2026-07-21 (every data-at-rest bucket uses the full canonical hive grammar)
depends_on: []
---

# instrument_availability full-hive canonicalisation (2026-07-21)

> **The HARD RULE (operator, 2026-07-21).** Every data-at-rest tree MUST use the FULL canonical hive grammar — the
> canonical key set INCLUDING `pipeline_mode=` and `asset_group=`, in the canonical ORDER — never a reduced/flat subset.
> `instrument_availability` is the standing violation and must be migrated to full hive.

## What "full canonical hive grammar" means here

The canonical hive order (per `/codex/02-data/cross-asset-canonical-target-ssot.md` §8) is:
`by_date/day={D}/pipeline_mode={mode}_{src}/asset_group={ag}/venue={V}/instrument_type={it}/…`.
`instrument_availability` today carries only `day=` and `venue=` — it is missing `pipeline_mode=`, `asset_group=` (and,
where applicable, `instrument_type=`). The target is the full ordered key set; the exact trailing keys (whether
`instrument_type=` belongs in an availability listing) is a design decision for the executing effort, but
`pipeline_mode=`/`asset_group=`/canonical order are mandatory.

## The finding (grounding, verified 2026-07-21)

### FLAT in the registry SSOT

`unified-trading-library/unified_trading_library/config_interface/paths/registry.py:35` — the `instruments` dataset:
`path_template="instrument_availability/by_date/day={date}/venue={venue}/"`, `partition_keys=["date", "venue"]`. This is
the reduced-flat shape — no `pipeline_mode=`, no `asset_group=`, no `instrument_type=`. **The registry template is the
SSOT and MUST be updated to the full-hive shape** as part of this fix.

### FLAT in the live writer

`instruments-service/instruments_service/engine/orchestrator/process_write.py:612` —
`sink = _orch.get_data_sink(bucket=bucket, prefix="instrument_availability/by_date")`; the per-bucket helper repeats the
same prefix at `:624`. `instruments-service/instruments_service/engine/orchestrator/writers.py:201-208` — the write is
`partition={"day": date, "venue": venue_str}, filename="instruments.parquet"`. So the emitted tree is
`instrument_availability/by_date/day={D}/venue={V}/instruments.parquet` — two keys only.

### Same reduced-flat shape on the siblings

- **market_lifecycle** — `process_write.py:614`: `prefix="market_lifecycle/by_canonical_group"` (repeated `:629`);
  reduced `group=/day=/venue=`-class shape, same defect. (This is the sibling that ALREADY hit the alphabetical-sort
  trap once — see below.)
- **futures_contracts** — `writers.py:359` (docstring path
  `instrument_availability/by_date/day={date}/venue={venue}/futures_contracts.parquet`) + `writers.py:382`
  (`filename="futures_contracts.parquet"`). It shares the `instrument_availability/by_date` prefix and the flat
  `{day, venue}` partition, so it inherits the same reduced-flat shape.

## CRITICAL — the alphabetical-sort trap (why you CANNOT just add keys to the partition dict)

The UTL sink builds the object path by iterating the partition dict in **alphabetical key order**, NOT insertion order:

`unified-trading-library/unified_trading_library/cloud_interface/providers/protocol_impls.py:23-29` —
`_build_partition_path(prefix, partition, filename)`:

```python
def _build_partition_path(prefix: str, partition: dict[str, str] | None, filename: str) -> str:
    parts = [prefix.rstrip("/")]
    if partition:
        for k, v in sorted(partition.items()):   # <-- ALPHABETICAL SORT of the keys
            parts.append(f"{k}={v}")
    parts.append(filename)
    return "/".join(p for p in parts if p)
```

So if you naively add `pipeline_mode` and `asset_group` to the partition dict
`{"day", "venue", "pipeline_mode", "asset_group"}`, the sink emits `asset_group=…/day=…/pipeline_mode=…/venue=…` —
**wrong order, and `day` is not first**. This exact trap already bit market_lifecycle.

**The fix MUST use the sink PREFIX mechanism**: bake the ordered canonical keys into the `prefix` string per shard (the
write loop already knows `day`, `venue`, and can derive `pipeline_mode`/`asset_group`), exactly as the sports lane does
(it builds the full ordered path template itself rather than relying on `sorted(partition)`). Construct e.g.
`prefix=f"instrument_availability/by_date/day={date}/pipeline_mode={pm}/asset_group={ag}/venue={venue}"` (canonical
order) and pass an empty partition (or only a single trailing key), so the sort cannot reorder the hive keys. Verify the
emitted path byte-for-byte against `cross-asset-canonical-target-ssot.md` §8 before shipping.

## Migration note

Existing flat `instrument_availability/by_date/day={D}/venue={V}/…` objects (and the market_lifecycle /
futures_contracts equivalents) are `migration_pending` — they are the current authoritative copies and are FLAT because
they were written before this ruling. Fix the writer + registry FIRST, PROVE green, THEN migrate the historical objects
UP into the full-hive tree, THEN re-sync the manifest / data-status so all four canonical surfaces agree. Do not delete
the flat tree until the full-hive twin is verified present. The instruments-service reader / manifest-consolidator that
consume these paths must be updated in lockstep with the writer.

## Todos

- [x] 1. ✅ [DATA] P1. RULED — no `instrument_type=`, key set is `day/pipeline_mode/asset_group/venue` (an availability
      listing is per-venue, not per-instrument-type). Written into `cross-asset-canonical-target-ssot.md` §8 —
      `unified-trading-pm` (this batch).
- [x] 2. ✅ [DATA] P1. UTL registry `registry.py:35` updated to the full-hive `path_template`/`partition_keys` —
      `unified-trading-library@43fa6f3f`.
- [x] 3. ✅ [DATA] P1. instruments-service writer fixed via the sink PREFIX mechanism
      (`_instrument_availability_sink_for` helper, alphabetical-sort trap cited in the code comment) —
      `instruments-service@a9be6ce9`.
- [x] 4. ✅ [DATA] P1. `futures_contracts` full-hive prefix fix shipped in the same commit —
      `instruments-service@a9be6ce9`.
- [x] 5. ✅ [DATA] P1. `market_lifecycle` full-hive prefix fix (`_market_lifecycle_sink_for` helper) shipped in the same
      commit — `instruments-service@a9be6ce9`.
- [x] 6. ✅ [REVIEW] P1. Readers made layout-tolerant across the cutover (day-scoped listing matched on the venue-tail
      so both pre-/post-cutover shapes resolve): `cloud_data_provider.py`, `instrument_lifecycle_loader.py`,
      `manifest_writer/_maintenance.py`, `manifest_writer/_queries.py`, `options_cluster_lookup.py` —
      `unified-trading-library@43fa6f3f`; `tradfi_live.py` reader — `instruments-service@a9be6ce9`.
- [ ] 7. [DATA] P1. PROVE the fixed writers green on one real day (write + skip-if-fresh + manifest row), then migrate
      the historical flat `instrument_availability` / `market_lifecycle` / `futures_contracts` objects UP into full hive
      (copy → verify → human-only purge of the flat tree). **Deferred to Round 2** — likely VM-scale given the volume of
      prior capture days; size it before attempting.
- [ ] 8. [REVIEW] P1. On writer ship, record the `instrument_availability` full-hive cutover date in
      `/codex/02-data/canonical-cutover-register.md` (repo@sha) and flip the non-canonical-path-inventory row #16 to
      EXECUTED with a dated post-migration probe. **Deferred to Round 2** (pairs with todo 7 — cutover date should be
      the historical-migration date, not the writer-ship date, per the register's own convention).
