---
doc_type: issue
title:
  ManifestWriter._write_unconditional has NO generation/version check — under heavy concurrent-writer contention it
  silently DROPS newly-written rows (confirmed data loss, not theoretical)
summary:
  'Found 2026-07-13 while re-running collect-onchain-perp-batch for the cefi live-only-tuples fix
  (cefi_live_only_data_types_vs_layer1_denominator_contradiction_2026_07_12.md P3). Of 6 typed empty_confirmed rows the
  handler wrote across ASTER/PACIFICA-SOLANA/EXTENDED-STARKNET/LIGHTER-ZKSYNC, 2 (EXTENDED-STARKNET/book_snapshot_5,
  LIGHTER-ZKSYNC/book_snapshot_5) were logged as successfully written ("ManifestWriter: updated availability index … 1
  new") but were VERIFIABLY ABSENT from the manifest on direct query moments later — silent data loss, not a
  logging/read artifact. Root cause: `_write_unconditional` (unified_trading_library/manifest_writer/_writer_io.py:794)
  is the fallback path used after `_MAX_GENERATION_RETRIES` (15) generation-conflict retries are exhausted — it does a
  plain read-existing → merge → write with NO `if_generation_match` guard at all. Under the heavy concurrent-writer
  contention this workspace runs routinely on the shared cefi manifest (directly observed: every single write in this
  session needed 1-15 retries before succeeding), two concurrent `_write_unconditional` calls can race: both read the
  same base snapshot, both append their own new row, and whichever writes LAST wins — the other write is silently
  discarded, with no error, no warning, and a misleading "1 new" success log for the row that then vanishes.'
status: open
nature: notes
asset_group: [cefi]
stage: [data]
repos: [unified-trading-library]
scope: [engineer, admin]
tags: [manifest-writer, data-loss, race-condition, concurrency, data-correctness, honest-coverage, cross-cutting]
related:
  [
    cefi_live_only_data_types_vs_layer1_denominator_contradiction_2026_07_12.md,
    ../../../codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-13
parent_epic: infrastructure_master
priority: P1
source:
  cefi_live_only_data_types_vs_layer1_denominator_contradiction_2026_07_12.md P3 re-verification, 2026-07-13 session
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
assigned_role: backend-engineer
model_tier: sonnet-doable
thinking_tier: high
drift_direction: advance-code
depends_on: []
---

## What I found

While closing out the P3 todo in `cefi_live_only_data_types_vs_layer1_denominator_contradiction_2026_07_12.md` (confirm
the Layer-1 missing-tuple count drops after the (b)-fix lands), I ran a real `collect-onchain-perp-batch` for 2026-07-11
across the 4 affected venues (ASTER, PACIFICA-SOLANA, EXTENDED-STARKNET, LIGHTER-ZKSYNC). The run logged 6/6 expected
typed `empty_confirmed` rows written successfully (one `ManifestWriter: updated availability index (…, 1 new)` line per
tuple, no errors). Running `measure_honest_coverage.py --asset-group cefi` immediately after showed the Layer-1
missing-tuple count drop from the pre-fix baseline, BUT 2 of the 6 target tuples (`EXTENDED-STARKNET/book_snapshot_5`,
`LIGHTER-ZKSYNC/book_snapshot_5`) were STILL in the missing list. Direct query of the raw (un-merged) primary manifest
confirmed **zero rows** existed for either tuple — despite the log claiming a successful write for each.

Re-running a narrowly-scoped retry for just those 2 tuples succeeded (both rows landed and verified present on direct
query). This rules out a code bug in the (b)-fix itself (`_record_live_only_empty_rows` /
`_onchain_perp_batch_live_only.py`) — the SAME code path, run again, worked correctly. The only variable that changed
between the failed first attempt and the successful retry is the level of concurrent write contention (the first run
raced against ~10+ other slots' constant generation-conflict retries on the same shared cefi manifest at the time,
confirmed by the _other_ 4 tuples in the same run each needing 1-15 retries before landing).

### Root cause — confirmed by code read

`unified_trading_library/manifest_writer/_writer_io.py`:

- `_write_with_generation_match` (line 732) is the primary path: `if_generation_match=<generation>` on the GCS
  `upload_from_string` call gives true optimistic-locking — a concurrent writer's intervening write bumps the generation
  and this call raises `PreconditionFailed`, which is retried (`_MAX_GENERATION_RETRIES`, exponential backoff
  0.5s/1.0s/1.5s/…) up to 15 times.
- On the 15th failure, line 770 calls `self._write_unconditional(client, new_df)` — the FALLBACK.
- `_write_unconditional` (line 794): `existing_df = self._read_existing_index(client)` →
  `merged = self._merge_dataframes(...)` → writes back **with no `if_generation_match` at all** (confirmed by reading
  the full method body). This is a plain read-then-write with ZERO atomicity guarantee.

Under the fleet's normal operating conditions (many concurrent slots/agents writing the SAME shared cefi manifest,
directly observed in this session as near-constant generation-conflict retries), two writers can BOTH exhaust their 15
retries at roughly the same time and BOTH fall through to `_write_unconditional` concurrently. Both read the same
"existing" snapshot, both append their own row, and whichever's `upload_from_string` lands LAST overwrites the other's
work — the earlier writer's new row is silently gone, with no exception, no warning, and a log line claiming success
that becomes false the moment it's overwritten.

## Why it matters

This is not a theoretical race — it happened, was directly observed, and directly explains 2 of 6 rows a real backfill
run believed it wrote successfully being **absent** from the manifest. Every service in this workspace's manifest
pipeline shares this same `ManifestWriter` (`unified-trading-library`, imported by MTDS/instruments-service/features
etc. per `codex/02-data/availability-manifest-and-data-status.md`), so this bug is NOT scoped to cefi onchain-perp — any
manifest write, from any writer, on any asset_group, that happens to lose the generation-match race 15 times in a row
under contention is silently discarded. Given "Data pipeline correctness is the heartbeat" (CLAUDE.md HARD RULE) and
"never silent placeholders" — this is the inverse failure mode: not a silent PLACEHOLDER, but a silent DROP of a row the
writer itself believed succeeded. Layer-1/Layer-2 coverage numbers, `denominator_complete` gates, and any downstream
consumer trusting a `capture_status` row's presence are all exposed to this whenever the shared manifest is under heavy
concurrent-write load — which, per this session's own observations, is the NORMAL steady state for the cefi manifest,
not an edge case.

## Recommended decision (architecture call, not mine to make unilaterally per findings-triage)

Two candidate fixes, not mutually exclusive:

- **(a) Make `_write_unconditional` retry-with-reread instead of single-shot**: even without `if_generation_match`,
  looping the read-merge-write cycle a bounded number of times (checking whether the blob changed via
  `etag`/`generation` comparison before AND after the write, or simply re-reading immediately before the final write to
  shrink the race window) would reduce — not eliminate — the loss window. Cheap, but still theoretically racy (just a
  smaller window).
- **(b) Extend `_MAX_GENERATION_RETRIES` / raise it adaptively under detected contention, and/or never truly fall back
  to unconditional** — i.e., treat exhausting the generation-match retries as a real, escalating backoff situation
  (longer waits, more attempts) rather than giving up into an unsafe path at all. This fully preserves atomicity but
  risks a writer blocking much longer under sustained fleet-wide contention (which, per this session, can mean many
  minutes).
- A third option worth architecture input: shard the manifest write path per-VM/per-slot (`MANIFEST_PER_VM_SHARDS`
  already exists per `codex/05-infrastructure/vm-launcher-runbook.md` for launcher-level sharding) so concurrent writers
  don't all contend on ONE blob's generation at all — the true fix for the contention, not just the race it induces.

I have NOT attempted a fix — this is `unified-trading-library`, imported by every service's manifest writer; a change
here is cross-cutting and needs an architecture call on which mitigation (or combination) is correct, per this
workspace's "SSOT contradiction / cross-repo" big-finding NOTIFY OPERATOR rule.

## Todos

- [x] ✅ [BACKEND] P1. Decide + implement a fix for `ManifestWriter._write_unconditional`'s missing generation-check
      (one of: bounded retry-with-reread, escalating backoff instead of unconditional-fallback, or per-writer manifest
      sharding — see options above) so concurrent writers cannot silently drop each other's rows. (repo:
      unified-trading-library, file: unified_trading_library/manifest_writer/_writer_io.py) —
      unified-trading-library@2c7f37eb
- [ ] [SCRIPT] P2. Once fixed, audit whether OTHER asset_groups/venues show the same symptom (a manifest write logged as
      successful but the row absent on direct query) by cross-referencing recent
      `ManifestWriter: updated availability     index` log lines (Cloud Logging) against the corresponding rows' actual
      presence, to size how much silent loss has already accumulated historically. (repo: instruments-service or
      unified-trading-library, whichever owns the log query tooling)
- [ ] [SCRIPT] P3. Re-run `measure_honest_coverage.py --asset-group cefi` after the fix lands + after any additional
      affected asset_groups are identified, to confirm no further silent-loss regressions recur under normal fleet
      contention. (repo: instruments-service)

## Progress Log

- **2026-07-13 (slot-6, sonnet/high)** — Discovered while closing out
  `cefi_live_only_data_types_vs_layer1_denominator_contradiction_2026_07_12.md` P3: ran a real
  `collect-onchain-perp-batch` for 2026-07-11 (ASTER/PACIFICA-SOLANA/EXTENDED-STARKNET/LIGHTER-ZKSYNC), confirmed 4/6
  target typed-empty rows landed correctly but 2 (EXTENDED-STARKNET, LIGHTER-ZKSYNC book_snapshot_5) were logged
  successful yet verifiably absent on direct manifest query. Re-ran narrowly scoped to just those 2 tuples — both landed
  on retry, confirming the underlying fix code is correct and this is a manifest-write concurrency bug, not a code
  defect in the live-only-tuples fix. Filed this issue doc per CLAUDE.md's big-finding (data-correctness, cross-repo)
  NOTIFY OPERATOR rule. Did not attempt a fix — `unified-trading-library` is cross-cutting and the mitigation choice is
  an architecture call.
- **2026-07-13 (slot-3, sonnet/high)** — Implemented the P1 fix: `_write_unconditional`
  (`unified_trading_library/manifest_writer/_writer_io.py`) now re-reads the just-uploaded blob after every write and
  confirms its own new rows (keyed on `date`/`venue`/`data_type`/`service_name`, the columns `_merge_dataframes` always
  dedups on) actually survived; on a detected clobber it retries the whole read-merge-write cycle (shrinking the race
  window each attempt) up to `_MAX_UNCONDITIONAL_WRITE_RETRIES` (5) times, and only on total exhaustion logs loudly at
  ERROR (never the old misleading "success" INFO line) — closing the "silent" half of the bug even in the worst case.
  Chose this (bounded retry-with-reread + verification) over extending `_MAX_GENERATION_RETRIES` further, since that
  budget is already fleet-tuned (2026-04-22 HYPERLIQUID incident, see `_state.py` comment) and this path has no
  generation/etag primitive to lean on regardless (used by both the GCS-fallback AND non-GCS-provider call sites). Added
  a regression test (`test_unconditional_write_race_detected_and_retried`) that simulates the exact race — a concurrent
  writer's upload landing immediately after ours, clobbering our row — and asserts detection + retry + survival. Full
  `quality-gates.sh` green; shipped `unified-trading-library@2c7f37eb`. P2 (historical-loss audit) and P3 (post-fix
  honest-coverage re-run) remain open, scoped to `instruments-service` — not attempted here (out of this task's
  repo/role scope).
