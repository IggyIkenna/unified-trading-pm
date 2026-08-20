---
doc_type: issue
title: CeFi instrument_type casing residual is an ACTIVE writer regression, not stale debt
summary: >-
  Re-verifying the instrument_type casing residual cited in cefi_consolidated_closeout_2026_07_18.md
  line 523 (2,982 rows) found it has grown 13x to 39,286 — an active writer regression, not stale
  historical debt. Traces a plausible root cause in market-tick-data-service's partitioned_writer.py
  (GCS-path lowercasing leaking into the manifest row-key), fixes 3 safety defects in the existing
  --apply script, and finds the apply itself is genuinely VM-scale (166k+ per-VM shard objects, a
  29.9M-row consolidated index) rather than safe to run on the shared host.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [cefi, instrument-type, casing, manifest, writer-regression]
related:
  [
    /plans/archive/2026_08/cefi_casing_residual_ao_dispatch_2026_08_16.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md,
  ]
created: 2026-08-17
author: slot-14 (data_engineering)
# was: cefi_master (epic-assignment audit 2026-08-19) -- root-cause fix patches shared
parent_epic: mtds_mdps_master
  # MTDS manifest-writer plumbing (_tradfi_manifest_shard.py::_tradfi_manifest_itype), which hardcoded a
  # tradfi-only gate causing EVERY non-tradfi asset group to skip instrument_type canonicalization -- not a
  # cefi-specific bug, cefi was just where the 13x regrowth was noticed first
source: [/plans/archive/2026_08/cefi_casing_residual_ao_dispatch_2026_08_16.md]
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by:
resolved_by:
drift_direction: advance-code
depends_on: []
sequential: true # added 2026-08-18 (plan_reconciler) — the 3 remaining open todos are already written as a
  # prose-gated chain ("once the dry-run reaches a terminal state, review... then launch the FULL --apply", "after
  # the --apply VM reaches a terminal state, trigger the consolidator rebuild", "once the consolidator rebuild is
  # confirmed complete, re-run the audit script") with no machine enforcement — an AO worker could otherwise
  # dispatch them out of order (e.g. trigger the consolidator rebuild before the --apply VM actually finished).
context_scope:
  [
    /plans/archive/2026_08/cefi_casing_residual_ao_dispatch_2026_08_16.md,
    /plans/active/issues/cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/partitioned_writer.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/_tradfi_manifest_shard.py,
    market-tick-data-service/scripts/normalize_instrument_type_casing.py,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
---

## What I found

Dispatched to re-verify the `instrument_type` casing residual cited in
`cefi_consolidated_closeout_2026_07_18.md` line 523 (2,982 non-canonical rows, "dominated by
already-ruled lowercase-casing variants") before running the `--apply` casing fix. A fresh live
re-count against the current cefi manifest (independently measured twice: once by a research
fork, once by myself, both via
`market-tick-data-service/scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py`,
run 2026-08-17 05:44 UTC) found the residual has **grown 13x, not shrunk**:

- Manifest size: 29,938,146 rows (was 8,880,557 in July — 3.4x growth from real capture volume).
- Genuine casing-variant residual (lowercase of a canonical `InstrumentType`): **39,286** rows
  (`perpetual`=38,083, `future`=1,191, `spot_pair`=12) — up from the cited 2,982.
- **NOT part of the casing residual, and NOT a new finding**: `instrument_type` also carries
  `futures_chain`=173,043 and `options_chain`=36,329 rows (up from 307/1,100 in the 2026-07-27
  snapshots below). This was already investigated and RESOLVED 2026-07-27 as an intentional,
  workspace-wide "bundled chain shard" writer convention, not a bug — see
  `issues/cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md`
  Finding 1. Correctly excluded from this doc's casing-fix scope; noted here only so the raw
  counts in the Evidence section below aren't mistaken for a new open defect. Also present and
  likewise excluded: `None`=162,190, blank=157,337, `index`=3,910 (unclassified, not casing
  variants).

**Plausible root cause of the active regrowth** (repo: market-tick-data-service — flagged as a
candidate, not confirmed with the same rigor as the 2026-07-27 doc's RESOLVED sections; a fix
should re-verify against the actual single-instrument `record_captured` call sites before
shipping):
`market_tick_data_service/engine/orchestrator/partitioned_writer.py::_resolve_instrument_type_column`
(line 401-414) deliberately lowercases the `instrument_type` column
(`df["instrument_type"].astype(str).str.lower()`) so it matches the GCS hive-partition-path
convention (`CHAIN_INSTRUMENT_TYPES`/`SINGLE_INSTRUMENT_TYPES` are lowercase by convention for
`build_*_partition_path`). The sibling function
`market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py:565` does the identical
lowercase-for-path-building. This is correct/by-design for path construction. The open question:
whether that same lowercased column also feeds the manifest `record_captured` row-key for
SINGLE-instrument (non-bundle) shards (`manifest_finalize.py`'s `itype_key`, e.g. line 264/488) —
the 2026-07-27 doc's RESOLVED trace only examined the BUNDLE-shard write path
(`_write_bundle_shard_row`) for the `futures_chain`/`options_chain` question, not this one. If
confirmed, the fix is to re-map to canonical uppercase specifically at the manifest-write call
site, keeping the lowercase value only for `build_*_partition_path`. Whatever the exact mechanism,
the residual's 13x growth since 2026-07-18 is itself solid evidence (independently measured
twice) that SOME live write path is still minting lowercase-cased manifest rows — the
`canonicalize_cefi_instrument_type_legacy_lowercase_2026_07_16.py` script's claim that the writer
was "already fixed" is stale/wrong for the MTDS manifest, though apparently still accurate for
the separate, much smaller instruments-service `_index/availability_index.parquet` surface (0
legacy rows there, independently re-verified this session).

**Existing `--apply` fix tooling had three separate safety defects** (found + fixed in this
session, `market-tick-data-service/scripts/normalize_instrument_type_casing.py`):
1. Mask over-reach: `itype.ne(itype.str.upper())` would have also uppercased the unrelated
   `futures_chain`/`options_chain`/`None`/`index` categories into `FUTURES_CHAIN`/`OPTIONS_CHAIN`/
   etc — still non-canonical, actively wrong (and would have fought the 2026-07-27-ruled-intentional
   convention). Fixed: mask now requires the uppercased form to be in
   `CANONICAL_ITYPES = {PERPETUAL, FUTURE, OPTION, SPOT_PAIR, COMBO}`.
2. No collision-dedup: `instrument_type` is part of the manifest's composite row-identity key
   (`unified_trading_library.manifest_writer._ROW_KEY_COLUMNS`) — uppercasing in place with no
   dedup could silently DUPLICATE a manifest row wherever an already-canonical-cased row exists for
   the same real shard atom. Fixed: dedups on the real composite key, keeping the
   latest-`attempted_at` survivor, mirroring the instruments-service sibling script's mechanics.
3. No backup: the original script overwrote the live PROD blob in place with zero backup. Fixed:
   backs up every touched blob to a timestamped sibling key before overwriting.

**The `--apply` run itself could not be safely completed in this interactive slot session** — this
is genuinely VM-scale work, not shared-host-scale:
- The per-VM shard scan is **166,686 individual GCS objects** (`_index/per_vm/*.parquet`) — a
  sequential download-modify-upload loop over that many objects timed out at 480s having barely
  started (per-object HTTP round-trips at that count are hours of wall-clock, not minutes).
- Even an `--index-only` run (added this session — skips the per-VM scan, touches only the single
  consolidated `_index/availability_index.parquet`, which is what `read_availability_index()`
  actually serves to readers/audits) was OOM-killed (exit 137) reading + building the composite
  row-key across the full 29.9M-row frame.

## Why it matters

- The plan's stated done-when ("re-count live; if a real residual exists, apply the fix") cannot be
  honestly closed by a quick apply — the residual is real, larger than believed, AND actively
  regenerating. A one-time apply without the writer fix would decay back toward today's 39,286
  within weeks, matching the exact growth pattern already observed since the 2026-07-18 baseline.
- `cefi_consolidated_closeout_2026_07_18.md`'s "Enumeration-audit terminal checkpoint" claim
  (2,982 residual, "dominated by already-ruled lowercase-casing variants") is now stale by an order
  of magnitude and should not be cited as current state.
- The task's own plan (`cefi_casing_residual_ao_dispatch_2026_08_16.md`) declared
  `repos: [instruments-service]`, but every script involved (the audit, the writer, the apply fix)
  lives in `market-tick-data-service` — corrected in that plan's own frontmatter as part of this
  session's flip.

## Recommended decision

- [x] ✅ [BACKEND] P1. **DONE 2026-08-17 (slot-11, backend_engineer craft)** — Confirmed and fixed the
      writer-side root cause. `market-tick-data-service@c07cc70e93`.

      **Confirmed**: `venue_fetch.py`'s `_record_venue_shard_counts` derives `manifest_itype` (the
      value that becomes `manifest_finalize.py`'s `itype_key`) via
      `fallback_itype = _tms._tradfi_manifest_itype(venue, itype)` (line ~410), where `itype` comes
      from `writer.underlying_counts` — keyed on the SAME lowercased `instrument_type` column
      `partitioned_writer.py::_resolve_instrument_type_column` stamps for GCS-path-building.
      `_tradfi_manifest_shard.py::_tradfi_manifest_itype` (pre-fix) hardcoded
      `if VENUE_TO_ASSET_GROUP.get(venue) != "tradfi": return itype` — so every CeFi venue (asset_group
      `cefi`, not `tradfi`) fell through this gate and the lowercase value was passed straight into
      the manifest row-key, unchanged. The shared UTL canon
      (`unified_trading_library.canonical.canonicalize_manifest_instrument_type`) already ships a
      `cefi` mapping table (`perpetual`/`spot_pair`/`spot`/`option`/`future` → canonical
      `InstrumentType`) — it was simply never reached for cefi.

      **Fix**: `_tradfi_manifest_itype` now calls
      `canonicalize_manifest_instrument_type(VENUE_TO_ASSET_GROUP.get(venue, ""), itype)`
      unconditionally, letting the shared canon's own asset_group gating (only `tradfi`/`cefi` have
      mapping tables; every other asset_group + the bundle-grain exclusion set — `futures_chain`/
      `options_chain`/`combo`/`combo_chain`/`continuous_future` — pass through unchanged) do the work,
      instead of re-gating on `== "tradfi"` in this file. The lowercase value is still used verbatim
      for `build_*_partition_path` (`partitioned_writer.py`/`tardis_shared.py` untouched) — only the
      MANIFEST-column casing changes, per the plan's own scoping.

      **Tests**: added `test_tradfi_manifest_itype_upgrades_cefi_venue` (BINANCE-SPOT/BYBIT/DERIBIT
      lowercase → canonical uppercase) and `test_tradfi_manifest_itype_bundle_grain_axis_still_unchanged_for_cefi`
      (Deribit `futures_chain`/`options_chain` stay lowercase, confirming the bundle-grain exclusion is
      asset-group-agnostic). Full `tests/unit/engine/test_tradfi_manifest_shard.py` +
      `tests/unit/test_venue_fetch_cefi_manifest_canonicalization.py` +
      `tests/unit/engine/test_sentinels_coverage.py` (111 tests) green — no pre-existing test assumed
      the buggy cefi-passthrough behavior as correct. Full `quality-gates.sh` green on `c07cc70e93`
      (sentinel-verified).

      This does NOT itself shrink the existing 39,286-row residual (that's todo 2's `--apply` VM
      dispatch, gated behind this fix per the plan) — it stops new lowercase-cased rows from being
      minted going forward, which is this todo's own done-when.
- [x] ✅ [DATA] P2. **DONE 2026-08-17 (slot-33, data_engineering craft)** — Added the dedicated VM
      dispatch path + shipped it a dry-run against PROD, per
      `/codex/05-infrastructure/vm-launcher-runbook.md`.

      **`deployment-service@8495b8a3e4`**: new `cefi-itype-casing-apply` category in
      `launch-canonical-migration-vm.sh` (folds under the already-registered
      `canonical-migration-` `VM_PREFIX_TO_BUCKET` catch-all, no new registry entry needed).
      DRY-BY-DEFAULT via the tool's own `--dry-run` flag (generic else-branch append, no
      special-casing needed — this tool has no `--apply` flag). `MACHINE_TYPE` defaults to
      `e2-standard-16` given the corpus size (29.9M-row consolidated index).

      **`market-tick-data-service@ccec3e5ebe`**: added `--workers` (ThreadPoolExecutor, default 8)
      to the per-VM shard scan — the prior strictly-sequential loop over 166k+ objects would have
      been hours of wall-clock on a dedicated VM; each blob is independently processed (own
      download/transform/upload) so concurrent execution is safe, dedup/collision handling stays
      per-blob.

      **`market-tick-data-service@df55d85d85`**: follow-up fix — `--workers` above the `requests`
      library's default connection-pool size of 10 caused constant "Connection pool is full,
      discarding connection" churn (confirmed live on the dry-run VM at `--workers 16`). Mounts a
      larger `HTTPAdapter` on both the main HTTP session and the separate OAuth token-refresh
      session, mirroring
      `migrate_prediction_instrument_id_wrap_2026_07_09._boost_connection_pool`'s already-proven
      fix for the identical problem class.

      **Dry-run VM dispatched + confirmed live+progressing** (STARTED + ongoing-progress, per the
      no-fire-and-forget rule):
      `canonical-migration-cefi-itype-casing-apply-20260817-130229` (asia-northeast1-c,
      e2-standard-16, SPOT), launched on the pre-connection-pool-fix tarball
      (`mtds-code@ccec3e5eb`). Confirmed via `run.log`: `DEPLOYMENT_STARTED`, then
      `Scanning 169081 per-VM shards in gs://market-data-tick-cefi-prd-central-element-323112/_index/per_vm/
      (workers=16)` (close to the 166,686 baseline count, consistent with the still-active
      writer-regression growth the P1 fix above only just stopped), heartbeats continuing every
      ~60s as of 13:23 UTC. `market-data-tick-cefi-central-element-323112` (the legacy non-tiered
      bucket name, first of the two `--all-buckets` targets) 404s — pre-existing, unrelated to this
      session's changes; the real target `-prd-` bucket scans correctly.

      This dry-run VM is still in-flight (169k objects at this scale is realistically 1.5-3h
      wall-clock even at workers=16) — its own connection-pool churn (running the OLDER tarball)
      will make it slower than a fresh run would be, but that's a dry-run inefficiency only, not a
      correctness issue. Remaining chain tracked as new todos below rather than absorbed into this
      one, per the one-task-per-session AO worker model.
- [x] ✅ [DATA] P2. **DONE 2026-08-18 (slot-14, data_engineering craft)** — the prior
      `canonical-migration-cefi-itype-casing-apply-20260817-130229` dry-run never reached a
      terminal state and was diagnosed as a genuine hang, not a completed disposition; this todo's
      own done-when required reviewing a genuine disposition before ever considering `--apply`, so
      a FRESH dry-run VM (`canonical-migration-cefi-itype-casing-apply-20260818-012605`) was
      relaunched, confirmed STARTED, and confirmed making real progress (`Scanning 170038 per-VM
      shards ... workers=16`, connection pool boosted to 16 with none of the prior run's
      "Connection pool is full" churn) — the no-fire-and-forget bar. Reviewing the new VM's
      disposition (not the dead 130229 run's) and, if sane, launching the FULL `--apply` is carried
      forward as the next todo below.

      **Diagnosis of the 130229 dry-run (evidence, not guesswork)**: `gcloud compute instances
      describe` 404s (VM gone). `run.log` (`vm-logs/.../run.log`, read via UTL
      `download_from_storage`, never `gsutil` per the storage-ops rule) ends abruptly at
      2026-08-17T13:39:08Z mid-scan (169,081 per-VM shards, workers=16, heavy
      "Connection pool is full" churn right up to the cutoff — this VM ran the OLDER
      pre-`df55d85d85` tarball `mtds-code@ccec3e5eb`) with no `Grand total` line, no error, no
      exception. The archived serial console (`log-archive/snapshot_20260817_1508/.../
      serial-console.txt`) confirms the WHOLE VM went silent — zero kernel/systemd/gcloud-token-
      refresh activity — from 13:39:38Z to 15:04:26Z (**~85 minutes of total freeze**, not just
      an app-level stall), then resumed with `systemd-networkd: ens4: Could not set DHCPv4
      address: Connection timed out`, consistent with a host-level stall/network-blip rather than
      a clean GCE Spot preemption (no `compute.instances.preempted` event exists anywhere in
      Cloud Logging for the project over the same 3-day window — ruled out). `gcloud logging read`
      shows the zombie watchdog (running as `uts-prd-sa`) killed it at 15:08:55Z:
      `ZOMBIE canonical-migration-cefi-itype-casing-apply-20260817-130229 (asia-northeast1-c)
      age=125min hb=90min shard=MISSING reason=zombie_stale_heartbeat` — a real kill of a VM that
      truly had stopped producing any signal for 90 min, not a false-positive of the
      SIGPIPE-sidecar-during-download pattern documented in `vm-launcher-runbook.md` (that pattern
      explains a merely-frozen `run.log`/heartbeat-blob with the VM otherwise alive; this VM's
      *serial console* — kernel/systemd level, independent of the app or its heartbeat sidecar —
      was also silent for the same 85 minutes, which that documented pattern does not predict).
      Root cause of the freeze itself is NOT conclusively identified (no OOM-killer message, no
      panic/segfault in the serial console) — most plausible candidate given the timing is a
      GCE host-level stall coinciding with the heavy connection-pool churn, but this is not proven;
      not worth further forensics given a fresh run on the FIXED tarball is the cheaper path to a
      real answer.

      **Action taken**: refreshed tarballs (`lc_verify_tarball_freshness` confirmed mtds
      @ `aec3e7dff825`, a descendant of `df55d85d85` — the connection-pool fix IS in this tarball)
      and relaunched via `bash launch-canonical-migration-vm.sh cefi-itype-casing-apply 2026-08-18
      2026-08-18 dry` from `deployment-service`. New VM
      `canonical-migration-cefi-itype-casing-apply-20260818-012605` (asia-northeast1-c,
      e2-standard-16, SPOT) confirmed RUNNING + `DEPLOYMENT_STARTED` reached (see Progress Log for
      the exact confirmation) — the no-fire-and-forget bar for this session. Terminal-state review
      is the next todo below, updated to point at THIS VM's name/log, not the dead 130229 run's.
- [x] [DATA] P2. Once the dry-run reaches a terminal state, review the disposition, then `--apply` if sane.
      ✅ 2026-08-20 — **DONE, clean result, via my own `cefi-itype-casing-apply-rw-20260820-181447`
      (e2-highmem-16, `--workers 4`, post-fix tarball — not slot-18's pre-fix `...-173927`, which per the
      timing correction above almost certainly OOM'd on the same pre-fix code my earlier 172425 attempt did).**
      Terminal, clean exit: `rc=0`, `DEPLOYMENT_COMPLETED`. **`Grand total instrument_type values would be
      normalized: 39286 (collisions_dropped=8899)`** — an EXACT match (not just same order of magnitude) to
      the independently re-measured post-fix baseline earlier in this doc's own Progress Log
      (`perpetual=38,083 + future=1,191 + spot_pair=12 = 39,286`). Sane disposition, confirmed by measurement,
      not assumed. **`--apply` launched immediately after** — `cefi-itype-casing-apply-rw-20260820-185429`
      (`--workers 4 --apply-migration`, same `MACHINE_TYPE=e2-highmem-16`, a FRESH VM, not reusing the dry-run
      VM) — see Progress Log for the launch confirmation and terminal-state review.
- [ ] [DATA] P2. After the `--apply` VM reaches a terminal state (0 exit, backups written, grand
      total normalized matches the reviewed dry-run count), trigger the manifest consolidator to
      rebuild the merged `_index/availability_index.parquet` (per the script's own docstring) —
      see `/codex/05-infrastructure/manifest-consolidator-ssot.md` for the trigger mechanism.
- [ ] [DATA] P2. Once the consolidator rebuild is confirmed complete, re-run
      `market-tick-data-service/scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py`
      (the same script this doc's own live re-count used) to confirm the casing residual is 0. If
      not 0, diagnose before closing this issue doc out — a residual writer bug (the shipped P1 fix
      only stops NEW rows; it doesn't retroactively fix any writer callsite this doc's own
      root-cause trace didn't reach) is the most likely explanation for a nonzero post-apply count.

## Evidence

- Live re-count (2026-08-17 05:44 UTC, exit 0): manifest rows=29,938,146; casing residual=39,286
  (perpetual=38,083 + future=1,191 + spot_pair=12); bundle-shard-type (2026-07-27-resolved,
  intentional)=209,372 (futures_chain=173,043 + options_chain=36,329); other-non-canonical=323,437
  (None=162,190 + blank=157,337 + index=3,910).
- Code fix: `market-tick-data-service/scripts/normalize_instrument_type_casing.py` (mask fix +
  collision-dedup + backup + `--index-only` flag) — `market-tick-data-service@07861cf6`.
- Root-cause candidate code refs: `partitioned_writer.py:401-414`, `tardis_shared.py:565`,
  `manifest_finalize.py:259-269` (`itype_key` in `base_row_key`).

## Progress Log

- **2026-08-20 (worker follow-up, bounded retry)**: the prior workers=16 dry-run was terminally confirmed as OOM (exit 137) with no normalization count, so no apply was launched. Shipped deployment-service@45b6846450 changing the dedicated launcher default to --workers 4; quality gates passed (3,650 tests, 74.24% coverage, all gates green). A fresh pinned dry-run canonical-migration-cefi-itype-casing-apply-20260820-174218 was then created in asia-northeast1-c on e2-standard-16, with command normalize_instrument_type_casing.py --all-buckets --workers 4 --dry-run; gcloud compute instances describe confirmed RUNNING, and the read-only check_vm_cli returned exit 0. This VM remains in-flight; the terminal-count/apply-gated todo stays open.

- **2026-08-20 (T2 tranche, operator-authorized VM launch)**: launched a FRESH dry-run
  (`canonical-migration-cefi-itype-casing-apply-20260820-115340`, SPOT, asia-northeast1-c) via
  `deployment-service/scripts/vm/launch-canonical-migration-vm.sh cefi-itype-casing-apply 2026-08-20
  2026-08-20 dry` after confirming the prior dry-run VM
  (`canonical-migration-cefi-itype-casing-apply-20260818-012605`, referenced by this doc's own P2 todo below)
  no longer exists — self-deleted per its documented terminal behavior, and no persisted run.log was located
  for it via safe (non-`gsutil`) tooling in the time available. The fresh VM was confirmed RUNNING at launch
  time. **As of this checkpoint the VM is GONE** (`gcloud compute instances describe` returns "resource ...
  was not found") — consistent with either a completed dry-run self-deleting normally, or a failure that also
  self-deleted. **DETERMINED, same-day follow-up**: read the persisted final log via
  `unified_trading_library.deployment_registry.vm_run_log_final_uri(vm_name)` +
  `get_storage_client().download_bytes(...)` (never `gsutil`) —
  `gs://deployment-scripts-central-element-323112/log-archive/final/canonical-migration-cefi-itype-casing-apply-20260820-115340/run.log`.
  **The dry-run FAILED — OOM-killed, not a silent success and not still-running.** Heartbeats run
  2026-08-20T11:10:48Z through 11:28:48Z (~19 min), then: `bash: line 1: 5335 Killed
  /home/ikennaigboaka/venv/bin/python -u scripts/normalize_instrument_type_casing.py --all-buckets --workers 16
  --dry-run` → `[vm-exec] command exited rc=137` → deployment archived
  `status=failed, exit_code=137` (`gs://deployment-scripts-central-element-323112/deployments/archive/2026-08-20/e8335159-5f5f-4539-97c3-1ce7f53d0177.json`).
  **No `Grand total instrument_type values would be normalized: N` line exists — the script never reached that
  point.** The dedicated `e2-standard-16` VM (the machine type already bumped once, 2026-08-17, per this
  script's own launcher comment) still ran out of memory processing BOTH cefi buckets at `--workers 16`. This is
  a resourcing problem, not a data-safety problem — nothing was written (this was `--dry-run`), and it says
  nothing about whether the underlying casing fix or purge is safe, only that the current worker/memory ratio
  is too aggressive for this corpus scale. **Next step**: relaunch with materially fewer workers (e.g.
  `--workers 4`) and/or a larger machine type (this instance already got one size bump and still OOM'd — a
  second bump, or reducing per-worker memory footprint, or processing the two cefi buckets sequentially instead
  of `--all-buckets` in one process, are the candidate fixes; diagnose before just doubling machine size again).
  A near-identical OOM (SIGKILL, exit 137) also hit an UNRELATED laptop-side operation this same session (the
  AAVEV3 purge script's manifest read, see `defi_aavev3_bare_alias_enumerator_bug_2026_08_08.md`) — noted as a
  pattern, NOT asserted as a shared root cause without further evidence; the two operations use different code
  paths (this uses per-VM-shard listing + threaded rewrite, that uses a single `pd.read_parquet` of the full
  consolidated index) and different hosts (VM vs laptop).


- **context-scout 2026-08-17**: populated context_scope (6 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries).
- **slot-14 (data_engineering) 2026-08-18**: `canonical-migration-cefi-itype-casing-apply-20260817-130229`
  dry-run never reached a terminal state — diagnosed as an ~85-minute total VM freeze (kernel/systemd
  level, not just app/heartbeat) followed by a real (not false-positive) zombie-watchdog kill. See the
  updated todo above for full evidence. Relaunched a fresh dry-run,
  `canonical-migration-cefi-itype-casing-apply-20260818-012605`, on the current tarball (includes the
  `df55d85d85` connection-pool fix) — confirmed RUNNING, `DEPLOYMENT_STARTED` at 2026-08-18T01:28:39Z,
  then `Scanning 170038 per-VM shards in gs://market-data-tick-cefi-prd-central-element-323112/_index/
  per_vm/ (workers=16)` at 01:28:49Z with the connection pool boosted to 16 and no repeat of the prior
  run's "Connection pool is full" churn — genuine progress confirmed, not fire-and-forget.
- **cefi_reconciliation_auditor 2026-08-20** (Tier-1 daily audit, evidence found incidentally while
  cross-referencing today's census against this doc — NOT a full re-diagnosis, VM-ops relaunch/forensics
  stay out of this role's scope): the 2026-08-18 dry-run also never reached a terminal state — **the SAME
  freeze pattern as the 130229 run, undocumented until now**. `gcloud compute instances describe
  canonical-migration-cefi-itype-casing-apply-20260818-012605 --zone=asia-northeast1-c
  --project=central-element-323112` → 404 (VM gone, presumably zombie-reaped like its predecessor — not
  independently re-confirmed via Cloud Logging this pass). Its `run.log`
  (`gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-cefi-itype-casing-apply-20260818-012605/run.log`,
  read via UTL `download_bytes`) is a flat 8,242-byte file of `PIPELINE_HEARTBEAT` lines ending abruptly at
  `ts=2026-08-18T01:59:32Z`/last_modified `2026-08-18T02:01:40.949Z` — no `Grand total` line, no error, no
  exception, no shutdown marker — **frozen ~46h as of this check (2026-08-20T00:2xZ)**. The open todo below
  ("review the disposition... if it goes stale/silent again, diagnose per the freeze pattern") already
  anticipated this exact scenario; it needs a fresh dedicated dispatch to do the serial-console +
  zombie-watchdog-log forensics (per the 130229 precedent) and relaunch — genuinely VM-scale work, not a
  narrowly-scoped fix this Tier-1 read-only role can absorb. Separately, and more positively: today's cefi
  distinct-value census independently re-measured the casing residual at **byte-identical counts to this
  doc's 2026-08-17 post-fix baseline** — `perpetual`=38,083, `future`=1,191, `spot_pair`=12 (sum 39,286,
  exact match) — confirming the P1 writer fix (`c07cc70e93`) is holding with **zero regrowth in the 3 days
  since it shipped**. Full census: `plans/audit/results/data_pipeline_reconciliation_cefi_2026_08_20.md`.

- **slot-18 (data_engineering) 2026-08-20**: after the 2026-08-20 dry-run was confirmed OOM-killed (exit 137) before producing a count, launched a fresh reduced-concurrency dry-run `canonical-migration-cefi-itype-casing-apply-20260820-173927` through the canonical deployment-service launcher. The emitted command is `--all-buckets --workers 4 --dry-run`; the launcher refreshed and SHA-pinned the MTDS/UAC/UTL/deployment tarballs (`mtds-code@5bdd3d22e166`, `unified-api-contracts-code@949b9b2bebb4`, `unified-trading-library-code@089d7a32b81b`, `deployment-service-code@45b68464504b`). The VM is `RUNNING` in `asia-northeast1-c` on `e2-standard-16` SPOT. Rolling-log evidence: `DEPLOYMENT_STARTED` at `2026-08-20T17:44:21Z`, the process includes `--workers 4 --dry-run`, and the PROD-bucket scan is active. The legacy bucket's 404 is pre-existing and explicitly skipped. This run is **in-flight**, so the dry-run gate remains open and no `--apply` was launched.

- **Correction (slot-18, 2026-08-20)**: the earlier worker-follow-up entry above names `canonical-migration-cefi-itype-casing-apply-20260820-174218`, but a live fleet reconciliation found no such instance; it is not the VM launched by this session. The measured active VM and the open gate are `canonical-migration-cefi-itype-casing-apply-20260820-173927` (RUNNING, `--workers 4`, rolling log active). Preserve the earlier entry as historical provenance, but do not use its VM name for terminal-state review.
- [x] ✅ [DATA] P2. **DONE 2026-08-20 (slot-18)** — Diagnosed the `--workers 16` dry-run's
      terminal OOM (`exit 137`, no writes and no normalization total) and shipped the MTDS
      memory-bound fix in `market-tick-data-service@bccf8177ff`. The per-VM GCS listing now
      streams without materializing 170k+ blob metadata and retains at most two worker windows
      of futures; full `quality-gates.sh --no-fix` passed (11,093 passed, 28 skipped, 1 xpassed,
      82.01% coverage, exit 0). The reduced-concurrency retry remains gated by the next todo.
- **T2 tranche, `/autonomous`, 2026-08-20 (PARALLEL SESSION NOTICE + a self-correction)**: a **different
  concurrent VM**, `cefi-itype-casing-apply-rw-20260820-172425` (my own new
  `launch-cefi-itype-casing-apply-reduced-workers-vm.sh`, launched ~17:24Z — separate from slot-18's `...-173927`
  above, launched ~17:44Z, same underlying script, same `--workers 4`, different launcher/naming), reached a
  TERMINAL state first: OOM-killed (SIGKILL, rc=137) at 18:13:58Z, after ~28min of steady heartbeats with zero
  script output. **Checked the timing before drawing a conclusion, not after**: `market-tick-data-service`'s
  memory-bound streaming fix (`bccf8177ff`, the todo directly above) landed at **18:07:45Z** — AFTER my 172425 VM
  had already launched (~17:24Z) and pulled its tarball, so that VM ran entirely on the PRE-FIX
  materialize-170k+-blobs code the whole time. Its OOM does **NOT** show `--workers 4` is insufficient in
  general — it most likely reproduces the exact bug slot-18 had already root-caused and fixed, just on a
  tarball that predated the fix. Correcting my own earlier draft of this entry, which claimed the OOM "falsifies
  worker-count as the sole lever" before checking this timing — that claim is unsupported and withdrawn.
  **My own next attempt, `MACHINE_TYPE=e2-highmem-16` (128GB RAM) + `--workers 4`, launched after 18:07:45Z and so
  DOES include the streaming fix** — its result is the first real post-fix data point on this issue; treat it,
  not the pre-fix 172425 run, as the next thing to review. slot-18's `...-173927` VM (launched 17:44Z, also
  pre-fix) is very likely to OOM for the same pre-fix reason — worth a fresh post-fix relaunch on slot-18's side
  too rather than waiting out that VM's own outcome.


- **Correction (slot-18, 2026-08-20 18:34 UTC)**: the current slot-18 retry is
  `canonical-migration-cefi-itype-casing-apply-20260820-183425`, not the historical `...-173927` entry above.
  It was launched from `deployment-service` with `--all-buckets --workers 4 --dry-run` after the bounded-memory
  MTDS change reached `origin/live-defi-rollout` (`market-tick-data-service@bccf8177`; tarball manifest observed
  at `mtds-code@63ff30b953d4`). The VM is `RUNNING` in `asia-northeast1-c` on `e2-standard-16` SPOT. Serial
  console evidence at 18:38:49Z shows setup complete, heartbeat sidecar active, and the exact command launched;
  a read-only SSH check at 18:40:49Z shows the Python process alive at 566,592 KiB RSS with 60 GiB available.
  The rolling log has not yet been published, so this is **STARTED and live, not terminal**; no `--apply` has
  been launched.


- **Live check (slot-18, 2026-08-20 18:47 UTC)**: the post-fix VM remains active after roughly 9 minutes: Python PID 5272 is in `S` state at 634,496 KiB RSS, host memory reports 60 GiB available, and the sidecar emitted a heartbeat at 18:47:06Z. Repeated `Connection pool is full` messages continue at the launcher's pool-size-4 boundary, but there is no process exit, stall marker, or OOM evidence. The dry-run remains **in-flight** and `--apply` remains intentionally unlaunched.


- **Terminal disposition (slot-18, 2026-08-20 19:02 UTC)**: `canonical-migration-cefi-itype-casing-apply-20260820-183425` reached a measured terminal failure, exit 137, and self-deleted. Its log recorded `Scanned 110523 per-VM shards` before the final futures were collected; RSS rose from ~650 MiB to 45,966,576 KiB (host available memory fell to 16 GiB), then the VM was OOM-killed. No `Grand total` or normalization findings were produced and no writes occurred. This isolates the remaining memory failure to concurrent downloaded shard/DataFrame work: `max_pending=workers*2` retained eight large shard futures after listing, despite the listing itself being streamed.

- **Follow-up shipped (slot-18, 2026-08-20)**: tightened `max_pending` to exactly `max_workers` in `market-tick-data-service/scripts/normalize_instrument_type_casing.py`, correcting the one-window contract and documenting the measured OOM. `market-tick-data-service@abb4261b6b` landed on `origin/live-defi-rollout`; full `quality-gates.sh --no-fix` passed (11,093 passed, 28 skipped, 1 xpassed, 82.01% coverage).

- **Fresh retry (slot-18, 2026-08-20 19:10 UTC)**: launched `canonical-migration-cefi-itype-casing-apply-20260820-191035` with `--all-buckets --workers 4 --dry-run`; the launcher refreshed the MTDS tarball at `mtds-code@abb4261b6b45`. Serial-console evidence at 19:14:03Z confirms setup complete and the exact command launched. At 19:14:23Z, PID 5526 was active at 537,484 KiB RSS with 60 GiB available and the heartbeat/uploader loops running. This retry is **STARTED and in-flight**; no `--apply` has been launched.
