---
doc_type: issue
title:
  vm_zombie_watchdog's richer per-VM manifest-shard-staleness signal was missing for 3 launcher families that DO write
  real per-VM shards — they fell through to generic heartbeat-only catch-alls, so a "VM alive + heartbeating but writing
  zero rows" failure (the exact 2026-07-18 sports-fixtures incident class) would never have been caught for them
summary: >-
  A live VM-fleet audit this session initially suspected `cefi-hyperliquid-` and `mtds-dex-swaps-backfill` were missing
  from `VM_PREFIX_TO_BUCKET` (deployment-service `scripts/vm/vm_zombie_watchdog.py`'s richer-signal opt-in map: prefixes
  listed there ALSO get a per-VM manifest-shard-mtime staleness check, on top of the catch-all heartbeat liveness every
  running VM gets) — that suspicion was based on grepping `vm_zombie_watchdog.py` directly, which no longer contains the
  dict literal (it moved to `deployment_service/vm_prefix_registry.py` on 2026-07-13 and is re-exported); both prefixes
  were, on inspection of the real registry file, already correctly registered with real buckets. A systematic
  cross-reference of every `scripts/vm/launch-*.sh` launcher that writes a real per-VM manifest shard
  (`ManifestWriter(per_vm_shards=True)`, the exact `_index/per_vm/{vm_name}.parquet` blob the watchdog polls) against
  the registry's current bucket coverage found 3 launcher families that WERE genuinely mis-registered as heartbeat-only
  despite writing that exact shard into a statically-deterministic per-asset_group bucket: `features-sfi-progressive-`
  (fell through to the generic `features-` catch-all), `manifest-recon-apply-{cefi,defi,tradfi}-` (fell through to the
  read-only `manifest-recon-` catch-all — a DIFFERENT, dry-run-only launcher that never writes a shard), and
  `blank-reason-recon-{cefi,defi,tradfi,sports,prediction}-` (registered but bucket=None despite the launcher's own
  docstring stating the exact per-AG write target). All 3 were confirmed by reading the underlying Python entrypoint's
  bucket-resolution code (not launcher comments alone) to rule out the adjacent trap: `expected-universe-v2-` ALSO
  writes per-VM shards but into a "-part{N:05d}" CHUNKED filename the watchdog's exact-path check can never observe —
  that one is correctly left bucket=None (a "fix" there would be a no-op, not a real improvement) and is documented as a
  deliberate non-fix in the shipped code comment. Fixed in deployment-service (9 new `VM_PREFIX_TO_BUCKET` entries +
  matching `LAUNCHER_FOR_VM_PREFIX` parity entries + a new regression-test class,
  `TestManifestShardWriterBucketCoverage`, that asserts these 9 prefixes can never silently regress to heartbeat-only).
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags:
  [
    vm-monitoring,
    zombie-watchdog,
    vm-prefix-to-bucket,
    manifest-shard,
    heartbeat,
    launcher-registry,
    observability,
    regression-test,
  ]
related:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/deployment-observability.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    /plans/active/issues/migration_vm_hung_detection_monitoring_gap_2026_07_27.md,
    /plans/active/issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md,
  ]
created: 2026-08-06
author: unknown
parent_epic: infrastructure_master
priority: P2
estimate_class: infra
assigned_role: infra
source:
  "Live VM-fleet audit this session (checking whether cefi-hyperliquid-2024/2025 and mtds-dex-swaps-backfill-2, all 3
  confirmed genuinely alive and doing real work, would be caught by the richer shard-staleness signal if they ever went
  silent) initially misread the registry location (grepped vm_zombie_watchdog.py directly, which only re-exports the
  dict since the 2026-07-13 move to deployment_service/vm_prefix_registry.py) — both originally-suspected prefixes
  turned out already correctly registered. Escalated to a full systematic audit per the task brief rather than a narrow
  2-entry patch, which found the 3 real gaps documented here instead."
assigned_vm: NA
execution_scope: local-only
drift_direction: none
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    deployment-service/scripts/vm/vm_zombie_watchdog.py,
    deployment-service/deployment_service/vm_prefix_registry.py,
    deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py,
    deployment-service/tests/unit/test_vm_zombie_watchdog.py,
  ]
resolved_by:
  "deployment-service@a43aa6523ae55ef87aaca38dbcd47d4fd1eb3314 — added 9 VmPrefixSpec entries to VM_PREFIX_TO_BUCKET
  (features-sfi-progressive- -> features-sports bucket; manifest-recon-apply-{cefi,defi,tradfi}- -> each AG's
  market-data-tick bucket; blank-reason-recon-{cefi,defi,tradfi,sports,prediction}- -> each AG's manifest bucket, sports
  via instruments-store), matching LAUNCHER_FOR_VM_PREFIX parity entries in data_pipeline_monitors/launcher_registry.py,
  and a new TestManifestShardWriterBucketCoverage test class in tests/unit/test_vm_zombie_watchdog.py asserting real
  (non-None) bucket coverage for all 9 prefixes plus that the bucket values match the shared _TICK_*/_INSTR_*/_FEAT_*
  constants (never a hand-typed duplicate literal). Full quality-gates.sh green (sentinel
  f2f1ab86a39beaf4a0605724e3c269a1579d4779); shipped via quickmerge, landed on live-defi-rollout."
---

# vm_zombie_watchdog richer-signal (shard-staleness) coverage gap — 3 launcher families

## What I found

`deployment-service/scripts/vm/vm_zombie_watchdog.py` watches EVERY `RUNNING` VM for heartbeat liveness (catch-all,
2026-05-06 design — closing an earlier "added launcher, forgot the dict, VM zombies forever" footgun). Separately,
`VM_PREFIX_TO_BUCKET` (moved to `deployment_service/vm_prefix_registry.py` on 2026-07-13, re-exported for back-compat)
is a _richer-signal opt-in_: a prefix listed there ALSO gets a per-VM manifest-shard-mtime staleness check
(`_index/per_vm/{vm_name}.parquet` in the mapped bucket) — the signal that catches "VM alive + heartbeating, but writing
NOTHING at all," a real failure mode this codebase has hit before (documented in the module's own docstring: the
2026-07-18 sports-fixtures incident, 3.5h, zero rows written, heartbeat never lapsed).

### False start

The task brief (from a prior session's audit) suspected `cefi-hyperliquid-` and `mtds-dex-swaps-backfill` were
unregistered, based on a grep of `vm_zombie_watchdog.py` that only turned up an `mtds-live-` entry. That grep target was
stale: the dict literal moved to `deployment_service/vm_prefix_registry.py` in 2026-07-13 (the watchdog script now just
imports it for back-compat), so a grep of the watchdog script alone only ever sees the import line. Reading the real
registry file confirmed both prefixes were ALREADY correctly registered with real buckets (`cefi-hyperliquid-` -> the
cefi market-data-tick bucket, `mtds-dex-swaps-backfill` -> the defi market-data-tick bucket). No fix was needed there.

### The real gap

Per the task brief's instruction to do a systematic audit rather than a narrow patch, I cross-referenced every
`scripts/vm/launch-*.sh` script against `VM_PREFIX_TO_BUCKET`'s current bucket coverage, focused specifically on
launchers whose underlying Python entrypoint genuinely writes a per-VM manifest shard
(`ManifestWriter(per_vm_shards=True)`) into a bucket that is STATICALLY DETERMINISTIC from the VM name (not genuinely
multi-bucket-ambiguous, like `replay-`/`cross-asset-rescan-`/the generic `features-` family/`dm-`, which are correctly
left heartbeat-only per the registry's own long-standing documented rationale for each). 3 launcher families were
confirmed mis-registered:

1. **`features-sfi-progressive-`** (`launch-sfi-progressive-features-backfill-vm.sh` ->
   `features_service.sports.scripts.compute_sfi_progressive_only`). The launcher hardcodes
   `BUCKET="features-sports-prd-${PROJECT}"` and passes it via `--bucket`; the script constructs
   `ManifestWriter(..., per_vm_shards=True)` (confirmed by source read). Fell through to the generic `features-`
   catch-all (bucket=None) since its VM_NAME (`features-sfi-progressive-{ts}`) starts with `features-` but there was no
   more-specific registry entry.

2. **`manifest-recon-apply-{cefi,defi,tradfi}-`** (`launch-manifest-recon-apply-vm.sh`, cefi/defi/tradfi only — the
   launcher's own arg validation rejects any other asset_group). Chains 3 instruments-service reconciler scripts with
   `--unphantom`/`--apply-flips` (a REAL write, distinct from the read-only `manifest-recon-{ag}-` dry-run launcher that
   shares the shorter `manifest-recon-` prefix and correctly stays heartbeat-only — it never passes `--apply-flips`). 2
   of the 3 chained scripts (`reconcile_expected_absence_reasons.py`, `reconcile_legacy_blank_to_typed_reason.py`,
   confirmed by source read) write the exact `_index/per_vm/{vm_name}.parquet` blob into
   `resolve_bucket_name(kind="market-data", asset_group=<ag>)` — the SAME bucket the
   `_TICK_CEFI`/`_TICK_DEFI`/`_TICK_TRADFI` constants already resolve to elsewhere in the registry. Fell through to the
   shorter `manifest-recon-` catch-all (bucket=None, correct for its OWN dry-run VMs, wrong for this longer,
   undifferentiated-until-now prefix).

3. **`blank-reason-recon-{cefi,defi,tradfi,sports,prediction}-`** (`launch-blank-reason-recon-vm.sh`, all 5 asset
   groups). The launcher's own docstring states the exact write target:
   `gs://market-data-tick-{asset_group}-{pid}/_index/per_vm/{vm_name}.parquet` (sports via `instruments-store-sports`
   instead). Confirmed against `reconcile_blank_error_reason_rows.py`'s `ASSET_GROUP_BUCKETS` map and its exact (not
   chunked) `_index/per_vm/{vm_name}.parquet` write. The registry's own comment for this prefix ("Heartbeat-only —
   writes to per-VM manifest shards") was internally contradictory on its face — it WAS registered, but as bucket=None,
   despite the same comment stating it writes per-VM shards.

### Deliberately NOT fixed (checked, ruled out)

`expected-universe-v2-` also sets `MANIFEST_PER_VM_SHARDS=true` and writes per-VM shards via
`enumerate_expected_universe.py`'s `_write_v2_per_vm_shard_chunk`, into the same kind of deterministic per-AG bucket —
but the blob name it writes is `_index/per_vm/{vm_name}-part{part_index:05d}.parquet` (a CHUNKED filename), not the
exact `_index/per_vm/{vm_name}.parquet` the watchdog's `_evaluate_vm` polls via an exact-path stat (never a
prefix/glob). Registering a bucket for this prefix would be a no-op in practice — the shard-mtime check would
permanently see "missing" and fall through to heartbeat anyway, so the existing `bucket=None` entry is functionally
correct despite its comment's slightly imprecise wording ("no canonical data bucket to poll"). Left unchanged.

Also explicitly out of scope per the task brief: daemon/live/cron/paper-trading prefixes that already carry documented,
deliberate `bucket=None` heartbeat-only rationale (`strategy-live-`, `strategy-paper-`, `defi-paper-`,
`defi-recursive-`, `funding-ensemble-paper-`, `replay-`, `features-xc-`, `defi-backtest-`, `mtds-live-smoke-`) — none of
these were touched.

## Fix shipped

`deployment-service@a43aa6523ae55ef87aaca38dbcd47d4fd1eb3314`:

- `deployment_service/vm_prefix_registry.py` — added the 9 `VmPrefixSpec` entries listed above, each resolving to the
  SAME shared bucket constant (`_TICK_CEFI`/`_TICK_DEFI`/`_TICK_TRADFI`/`_TICK_PRED`/`_INSTR_SPORTS`/`_FEAT_SPORTS`)
  other per-AG launchers in this file already use — never a hand-typed duplicate literal.
- `deployment_service/data_pipeline_monitors/launcher_registry.py` — matching `LAUNCHER_FOR_VM_PREFIX` entries (guard
  test `test_every_watchdog_prefix_has_a_registry_entry` / `test_no_extra_registry_prefixes` requires bidirectional
  parity with `VM_PREFIX_TO_BUCKET`). All 9 map to their own launcher (idempotent re-verification / presence-skip — safe
  to auto-relaunch on SPOT preemption), not `None`.
- `tests/unit/test_vm_zombie_watchdog.py` — new `TestManifestShardWriterBucketCoverage` class (regression guard, see
  todo below).

## Todos

- [x] ✅ [SCRIPT] P2. Add real `VmPrefixSpec` bucket coverage for the 3 mis-registered launcher families
      (`features-sfi-progressive-`, `manifest-recon-apply-{cefi,defi,tradfi}-`,
      `blank-reason-recon-{cefi,defi,tradfi,sports,prediction}-`) + matching `launcher_registry.py` parity entries + a
      regression test asserting these 9 prefixes can never silently revert to heartbeat-only — deployment-service@
      a43aa6523ae55ef87aaca38dbcd47d4fd1eb3314, `quality-gates.sh` green (sentinel
      f2f1ab86a39beaf4a0605724e3c269a1579d4779), shipped via quickmerge onto `live-defi-rollout`.

## Codex SSOTs

- `/codex/05-infrastructure/vm-launcher-runbook.md` — launcher naming / `VM_PREFIX_TO_BUCKET` + `lifecycle_class`
  registration convention this doc's fix follows.
- `/codex/05-infrastructure/deployment-observability.md` — fleet monitoring architecture the watchdog is part of.
- `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` — "backfill progress = target artifact, entity-scoped"
  rule the watchdog's own docstring explicitly scopes itself OUT of (this module is liveness-only, not
  entity-correctness — that scope limit is unchanged by this fix).
