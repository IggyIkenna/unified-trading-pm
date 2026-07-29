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
    /plans/active/issues/defi_dead_storage_shape_b_cleanup_candidate_2026_07_10.md,
    /plans/archive/issues/features_by_date_root_canonicalisation_2026_07_21.md,
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    /codex/02-data/canonical-cutover-register.md,
    /codex/02-data/non-canonical-path-inventory.md,
    /codex/02-data/pipeline-mode-partition.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-21
last_updated: 2026-07-21
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
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
sequential: true
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

## 🔴 2026-07-29 — near-miss: a SEPARATE, older issue doc's stale "hive is dead storage" premise nearly undid this

migration's target shape; caught + reverted same-day

`plans/active/issues/defi_dead_storage_shape_b_cleanup_candidate_2026_07_10.md` (last edited 2026-07-26, i.e. AFTER this
doc's 2026-07-21 writer cutover but never cross-checked against it) carried an operator ruling to delete the DeFi
`instrument_availability` hive shape as "frozen dead storage." A worker executed that ruling literally and deleted
70,570 real hive objects — the CANONICAL shape this doc's writer fix (`instruments-service@a9be6ce9`) has been writing
exclusively since 2026-07-21 (confirmed via a fresh live check: zero flat writes on any of 2026-07-25 through
2026-07-29). Caught because the delete script's own no-twin-exclusion set (Part 5 of the delete-safety protocol)
contained objects dated as recent as the day of execution — impossible if hive were genuinely frozen. Fully restored
same-day via GCS Soft Delete (`instruments-service/scripts/restore_defi_hive_instrument_availability_2026_07_29.py`,
72,514 objects restored, live-version-guarded to avoid clobbering anything the active writer had re-written since the
mistaken delete; 1,438 candidates correctly skipped for exactly that reason). Full account, both docs cross-linked, in
the other doc's own 2026-07-29 entry — read it before touching either shape of this tree again. **No action needed on
THIS doc's todos** (7c/7d's copy-then-gated-purge sequence below is unaffected and remains the correct path for the FLAT
shape, which is the one now actually stale).

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
- [x] 7a. ✅ [DATA] P1. **PROVE the fixed writers green on one real day — DONE 2026-07-27 (slot-8).** Ran the
      `/data-pipeline-check-is`-pattern e2e checker
      (`instruments-service/scripts/pipeline_e2e_check.py --asset-group     CEFI --venue HYPERLIQUID --day 2026-07-26`),
      test-bucket-scoped (`instruments-store-cefi-test-central-element-323112`, `IS_TEST_RUN=true`, no PROD data
      touched), both legs on real infra (2 real VM launches: `instr-backfill-cefi-pchk-0727085259-f-hyperliquid` force,
      `instr-backfill-cefi-pchk-0727090448-s-hyperliquid` skip). **Write**: confirmed via the per-VM manifest shard
      (`_index/per_vm/instr-backfill-cefi-pchk-0727085259-f-hyperliquid.parquet`) — row
      `date=2026-07-26 venue=HYPERLIQUID asset_group=cefi pipeline_mode=batch_instruments_service     capture_status=captured row_count=177`;
      `verify_write()` confirmed the parquet lands at the exact new hive path
      `instrument_availability/by_date/day=2026-07-26/pipeline_mode=batch_instruments_service/asset_group=cefi/venue=HYPERLIQUID/instruments.parquet`
      (canonical order per `cross-asset-canonical-target-ssot.md` §8). **Skip-if-fresh**: skip leg
      `status=passed skip_proof=genuine` — object signature (etag+crc32c+size) unchanged from the force-leg write, and
      the freshness pre-flight skip signal fired in the VM's `run.log`. **Manifest row**: `capture_status=captured`
      confirmed both via the per-VM shard and the checker's own report (`data_pipeline_e2e_check_is_2026_07_26.md`:
      `total=1 passed=1 failed=0`). All 3 required proofs (write / skip / manifest) hold on real infrastructure. (Note:
      the consolidated `_index/availability_index.parquet` itself lags behind per-VM shards until the next
      manifest-consolidator tick — this is expected, documented behavior, not a writer defect; per-VM-shard reads are
      the correct verification path per `unified_trading_library.pipeline_e2e_check.shard_verify`'s own docstring.)
- [x] 7b. ✅ [DATA] P1. **SIZE the historical migration before attempting — DONE 2026-07-27 (slot-8).** Bounded
      prefix-listing (metadata-only, not a content walk) of the 5 PROD `instruments-store-{ag}` buckets under
      `instrument_availability/by_date/` (includes nested `futures_contracts.parquet` — it shares the same root, no
      separate top-level prefix) + `market_lifecycle/by_canonical_group/` (prediction only):

      | asset_group | instrument_availability (+ futures_contracts) | market_lifecycle |
                                                          |---|---|---|
                                                          | cefi | 53,419 | 0 |
                                                          | defi | 177,346 | 0 |
                                                          | tradfi | 50,700 | 0 |
                                                          | sports | 148,691 | 0 |
                                                          | prediction | 22,637 | 12,582 |
                                                          | **TOTAL** | **452,793** | **12,582** |

                                                          **465,375 flat objects total** need copy-up to full hive. Confirms the doc's own "likely VM-scale" assessment —
                                                          this is a dedicated migration-VM job (copy → verify → human-only purge per the delete-safety protocol), not an
                                                          in-session action. Sizing now available to scope todo 7c.

- [ ] 7c. [DATA] P2. **Split from the original 7c 2026-07-28, per its own recommendation below — copy-and-verify half,
      no `[OPERATOR]` tag needed.** Copy the 465,375 flat objects UP into the full-hive tree (VM-only, never in-session,
      per the heavy-I/O rule + the data-pipeline-correctness HARD RULE that migrations run to real completion), then
      verify content parity. This half is additive/reversible (nothing is deleted, the flat originals stay exactly where
      they are) — cited under task_template.md finding U, not `[OPERATOR]`-eligible on its own. Needs a dedicated
      migration-VM launch. Same pattern as the mdps_features plan's 11a/11b/11c split — once 7a/7b proved the writer
      correct and sized the remaining work, "migrate" itself is a separately-dispatchable, properly VM-scoped unit
      rather than bundled into a single checkbox no one session could honestly complete.
- [ ] 7d. [DATA] P2. **Purge half — gated on a same-run finding-T check, not a fresh `[OPERATOR]` ask.** Once 7c's copy
      is verified present, run `gcs_bucket_soft_delete_retention_seconds()` against each of the 5 target
      `instruments-store-{ag}-prd` buckets AS PART OF executing this todo: if every bucket returns `>=604800s`, that
      FRESH same-run check itself satisfies delete-safety-protocol §3a (finding T) — proceed with the human-only-
      execution-but-not-human-only-_decision_ purge of the flat tree, citing the check's own output as the evidence, no
      separate operator sign-off required. If any bucket returns below the threshold (or the check errors), STOP and
      escalate to the operator with the measured retention value — do not purge. **Cross-corpus note 2026-07-27**: same
      shape as the sports K1/K2 casing-revert migration (also 5-figure-object, also copy-then-later-gated-purge) — that
      one hit the exact bundling mistake the original todo 7c's text already avoided (a single `[OPERATOR]` tag covering
      both the copy AND the purge, when only the purge is genuinely irreversible): see
      `/plans/archive/issues/sports_k1k2_delete_bundled_with_twin_less_data_2026_07_27.md`'s history for the concrete
      near-miss. Mirrors `market-tick-data-service/scripts/sports/k1k2_casing_revert_2026_07_27/`'s
      migrate/report/manifest-swap trio as a structural template if useful.
- [ ] 8. [REVIEW] P1. On writer ship, record the `instrument_availability` full-hive cutover date in
      `/codex/02-data/canonical-cutover-register.md` (repo@sha) and flip the non-canonical-path-inventory row #16 to
      EXECUTED with a dated post-migration probe. **Still deferred** (pairs with todo 7d — the purge half, now that 7c
      is split — not 7a/7b: cutover date should be the historical-migration date, not the writer-ship date or the
      proof/sizing date, per the register's own convention). **Dispatch-hygiene note (2026-07-27, slot-2)**: this todo
      was dispatched to a worker before the migration had run (only `depends_on` scopes whole-plan ordering; there was
      no per-todo gate between the last two remaining todos) — recording a "cutover date" ahead of the actual migration
      would be fabricating the record, so the worker correctly declined rather than faking it. Added `sequential: true`
      to this plan's frontmatter so `regen_backlog_from_plan.py`'s `_wire_sequential_prereqs` chains todo 8 behind the
      migration by `plan_order` (harmless for the already-`[x]` todos 1-7b) — todo 8 will not re-dispatch until 7d is
      marked done.
