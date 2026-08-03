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
status: resolved
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
context_scope:
  [
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    /codex/02-data/canonical-cutover-register.md,
    /codex/02-data/non-canonical-path-inventory.md,
    /plans/active/issues/defi_dead_storage_shape_b_cleanup_candidate_2026_07_10.md,
    unified-trading-library/unified_trading_library/cloud_interface/providers/protocol_impls.py,
  ]
locked_since:
supersedes:
superseded_by:
resolved_by:
  "todo 8 (slot-3, 2026-08-03) — historical migration EXECUTED (todos 7c/7d), canonical-cutover-register.md §6b +
  non-canonical-path-inventory.md row #16 updated with a dated post-migration probe. All 8 todos closed. Residual
  (content_mismatch + sports/prediction unrecognized shapes) filed separately:
  instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md"
source: operator HARD RULE 2026-07-21 (every data-at-rest bucket uses the full canonical hive grammar)
depends_on: []
sequential: true
---

> **🟢 ARCHIVED 2026-08-03** — status=resolved, archived per /codex/11-project-management/issue-doc-lifecycle.md's
> archive-on-resolve rule. All 8 todos closed; the recognized flat-shape historical migration ran to completion (117,166
> candidates: 84,320 copied-to-hive-and-purged, 32,846 content_mismatch correctly preserved, 0 failed). Genuine residual
> work (content_mismatch resolution policy, sports's actual live-writer shape, prediction's second unrecognized shape)
> is tracked in a NEW issue doc, not here:
> `instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md`.

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

- [x] 7c. ✅ [DATA] P2. **Copy-and-verify half — COMPLETE for the recognized-flat-shape population, real PROD infra,
      2026-08-03 (slot-8, building on an earlier slot-9 partial run same day).** Built + ran
      `instruments-service/scripts/migrate_instrument_availability_hive_2026_08_03.py` (`instruments-service@242b29ae`)
      via the `{ag}-iah` categories wired into `deployment-service/scripts/vm/launch-canonical-migration-vm.sh`
      (`deployment-service@1c19e5e`) — one dedicated VM per asset_group, full mode
      (`--apply-prod     --confirm-prod-write`), never in-session, per the heavy-I/O rule. Every asset_group re-run
      TWICE (idempotency reconfirmed: second run reports `copied: 0`, same content_mismatch count both times).

      **Important correction to this todo's own premise**: the 465,375 figure (7b's raw prefix-object COUNT) was NOT
                          a shape classification — it included already-hive objects, and, critically, objects in shapes the tool doesn't
                          even recognize. The REAL recognized-flat-shape candidate population across the 5 buckets is **117,166**
                          (cefi 7,650 / defi 73,679 / tradfi 25,402 / prediction 4,105 / sports 6,330), of which:

                          - **84,320 copied-or-verified-present** (safe, additive, real PROD writes: cefi 6,156 / defi 42,364 / tradfi
                            25,365 / prediction 4,105 / sports 6,330 — prediction and sports are 100% clean, zero residual).
                          - **32,846 content_mismatch** (cefi 1,494 / defi 31,315 / tradfi 37) — the hive target already exists with a
                            DIFFERENT (crc32c, size) than the flat source; the tool correctly refuses to overwrite. Needs a human
                            authoritative-source decision before these can resolve — tracked as todo 4 of the new issue doc below.
                          - **0 failed.**

                          **New finding, NOT covered by this todo's original scope — filed separately**: sports's writer was NEVER
                          actually fixed by `a9be6ce9` (still emitting a THIRD flat shape, `day=/league=/venue=/...`, as of TODAY
                          2026-08-02) and prediction has a SECOND unrecognized shape
                          (`canonical_question_group=/day=/venue=/...`, group-before-day) — combined **~198,340 objects** (sports
                          172,595 + prediction 25,745) are invisible to this migration tool entirely and were NOT touched by this todo.
                          Full writeup + 5 new todos (writer fix, target-shape ruling, tool extension, content_mismatch resolution
                          policy, doc correction):
                          `/plans/active/issues/instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md`.

                          Evidence: `instruments-service@242b29ae` (tool) + `deployment-service@1c19e5e` (launcher wiring, both pre-existing
                          this session) — real VM runs this session: `canonical-migration-{cefi,defi,tradfi,prediction,sports}-iah-2026080
                          3-0708xx` through `-0724xx` (asia-northeast1-c), all self-deleted on completion, fleet confirmed clean after.

- [x] 7d. ✅ [DATA] P2. **Purge half — COMPLETE, real PROD infra, 2026-08-03 (slot-3).** Built
      `instruments-service/scripts/purge_flat_instrument_availability_hive_2026_08_03.py`
      (`instruments-service@06be51ec`) — never trusts 7c's prior report: fresh per-object Part1+Part2 re-verify
      (re-describes source AND hive twin immediately before every delete) + a generation-matched
      `gcs_conditional_delete` (closes the verify-then-delete race), mirroring
      `market-tick-data-service/scripts/sports/k1k2_casing_revert_2026_07_27/delete_stale_uppercase_2026_07_27.py`'s
      structural template as this todo suggested. Wired into
      `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` as a new `{ag}-iah-purge` category
      (`deployment-service@b19c94b7`), one dedicated VM per asset_group, never in-session, per the heavy-I/O rule.

      **Same-run finding-T check**: every asset_group's fresh `gcs_bucket_soft_delete_retention_seconds()` call
              returned exactly `604800s` (7 days) — all 5 buckets qualify, no separate operator sign-off needed, purge
              proceeded per this todo's own pre-authorization.

              **Real PROD delete results** (fresh per-object verify, dry-run-confirmed candidate counts matched 7c's figures
              exactly before any delete):

              | asset_group | flat candidates | deleted (safe, twin-verified) | skipped content_mismatch (preserved, untouched) | failed |
              |---|---:|---:|---:|---:|
              | cefi | 7,650 | 6,156 | 1,494 | 0 |
              | defi | 73,679 | 42,364 | 31,315 | 0 |
              | tradfi | 25,402 | 25,365 | 37 | 0 |
              | sports | 6,330 | 6,330 | 0 | 0 |
              | prediction | 4,105 | 4,105 | 0 | 0 |
              | **TOTAL** | **117,166** | **84,320** | **32,846** | **0** |

              Totals reconcile exactly with 7c's own figures: 84,320 deleted == 7c's "copied-or-verified-present" safe set;
              32,846 preserved == the content_mismatch population tracked in
              `/plans/active/issues/instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md`
              todo 4 (still pending the operator's authoritative-source decision — those flat originals are correctly left
              alone, not purged). Sports's/prediction's unrecognized-shape populations (league=/canonical_question_group=,
              ~198,340 objects, tracked in the same issue doc's todos 2-3) were never in scope for this tool and remain
              untouched. `no_twin`/`source_vanished`/`race_lost` were 0 across every asset_group — no unexpected drift since
              7c's run earlier the same day.

              **New IAM gap found + self-fixed** (RULES.md §5 self-service, not an `[OPERATOR]` escalation): the first full-mode
              attempt on all 5 asset_groups failed identically —
              `uts-prd-sa@central-element-323112.iam.gserviceaccount.com does not have storage.buckets.get access` — because
              7c's copy tool only ever needed object-level `gcs_describe_object`/`gcs_copy_object` (covered by the existing
              `roles/storage.objectAdmin`), while this purge tool's §3a retention check calls `gcs_bucket_soft_delete_retention_seconds()`,
              which needs bucket-metadata read. Confirmed via `gcloud compute operations list` that this failed BEFORE any
              per-object work (the retention check is the first GCS call in `main()`) — zero deletes attempted, safe to
              retry cleanly. Self-granted `roles/storage.legacyBucketReader` (least-privilege bucket-scoped role covering
              exactly `storage.buckets.get`, not a broader grant) on all 5 `instruments-store-{ag}-prd` buckets via the
              `unified-trading-sa` self-service identity (`/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`),
              then relaunched — all 5 succeeded on the retry.

              Also hit 3 transient SPOT preemptions during the dry-run phase (cefi x2, prediction x1,
              `compute.instances.preempted` confirmed via `gcloud compute operations list`) — pure bad luck, zero work lost
              (dry-run does no GCS writes), relaunched each and all completed cleanly.

              Evidence: `instruments-service@06be51ec` (script+tests) + `deployment-service@b19c94b7` (launcher wiring, both
              shipped this session) — real VM runs: `canonical-migration-{cefi,defi,tradfi,sports,prediction}-iah-purge-2026080
              3-0816xx` through `-0817xx` (full mode, asia-northeast1-c), all self-deleted on completion, fleet confirmed
              clean after.

- [x] 8. ✅ [REVIEW] P1. **DONE 2026-08-03 (slot-3).** Recorded the historical-migration cutover in
      `/codex/02-data/canonical-cutover-register.md` §6b (`unified-trading-pm` this commit) — 117,166 recognized flat
      `day=/venue=` candidates, 84,320 copied-to-hive-and-purged (`instruments-service@242b29ae`+`06be51ec`,
      `deployment-service@1c19e5e`+`b19c94b7`), 32,846 content_mismatch correctly preserved pending an operator
      decision, 0 failed. Flipped non-canonical-path-inventory row #16 to RETIRED (partial) with a dated 2026-08-03 live
      `gcloud storage ls` post-migration probe (cefi `day=2020-06-15/` purged clean; `day=2019-03-30/` shows the
      expected hive+preserved-flat content_mismatch pair). **Not marked fully EXECUTED**: sports's live writer was never
      actually fixed (still emits an unrecognized THIRD flat shape) and 32,846 content_mismatch objects + prediction's
      second unrecognized shape remain non-canonical — both docs cross-link the new residual issue doc
      `instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md` rather than
      overclaiming closure. **Dispatch-hygiene note (2026-07-27, slot-2)**: this todo was originally dispatched before
      the migration had run; a prior worker correctly declined rather than fabricating a cutover date. That gate
      (`sequential: true` chaining todo 8 behind 7d via `plan_order`) is what allowed this todo to dispatch only now
      that 7d is done.
