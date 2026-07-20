---
doc_type: issue
title:
  "Daily tarball rotation silently reaps SHA-pinned code + mints orphan manifests — breaks every VM relaunch/preemption
  recovery"
summary:
  The daily `tarball_cleanup_cron` (Cloud Run Job `uts-prod-tarball-cleanup`, `--keep 5`, live delete) ranks
  `{svc}-code@{sha}.tar.gz` purely by GCS mtime with ZERO awareness of what is running, so it evicts tarballs that
  running/relaunch-eligible VMs are pinned to; because it only enumerates `*.tar.gz` it structurally cannot delete the
  sibling `.manifest.json`, minting a permanent ORPHAN MANIFEST (a pin that still resolves but whose code is gone).
  unified-api-contracts is the highest-velocity repo (~72 live @sha objects), so at `--keep 5` a UAC pin is evicted
  within DAYS. On 2026-07-20 this made every relaunch/preemption-recovery of the cefi migration fleet impossible,
  DEFEATING the shipped PROGRESS.json checkpoint contract. A v1 fix was attempted and is INERT — it sources pins from
  `LAUNCH_PARAMS.json`, which no pinning launcher writes. The correct source (GCE instance metadata) is NOT reachable
  through the UTL cloud interface, which is the open design decision this doc gates.
status: open
nature: issue
asset_group: [cefi, tradfi, defi]
stage: [meta, data]
repos: [deployment-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    vm-tarball-deployment,
    spot-preemption,
    relaunch-recovery,
    retention-sweep,
    orphan-manifest,
    silent-failure,
    fail-closed,
    data-correctness,
  ]
related:
  [zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23, vm_startup_scripts_no_auto_rollout_to_gcs_2026_07_19]
created: 2026-07-20
priority: P0
parent_epic: infrastructure_master
source: "Adversarial refutation of the v1 fix (3/3 verifiers refuted=true) + independent re-verification, 2026-07-20"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm:
resolved_by:
---

# Tarball rotation breaks VM recovery (2026-07-20)

> **🔴 BLOCKED ON A DESIGN DECISION.** The measured incident and both root causes below are settled. The fix is NOT
> shipped: the prescribed pin source (GCE instance metadata) is not reachable through the UTL cloud interface, and
> closing that requires a change to `unified-trading-library`, which the current work order forbids. See § Open
> decision.

## 1. Measured incident

- Cloud Scheduler `tarball_cleanup_cron` runs DAILY at `0 2 * * *` UTC —
  `deployment-service/terraform/gcp/tarball_cleanup_scheduler.tf:87-88`.
- It invokes Cloud Run Job `uts-prod-tarball-cleanup` with args exactly
  `["scripts/vm/cleanup_old_tarballs.py","--project",var.project_id,"--keep","5"]` — a **live delete, no `--dry-run`**.
- Mode 1 (`cleanup_name_versioned`) ranks `{svc}-code@{sha}.tar.gz` per-service by GCS object mtime and deletes
  everything past `--keep 5`. Ranking is by mtime ONLY — there is no cross-reference against running VMs.
- `_parse_tarballs` (`scripts/vm/cleanup_old_tarballs.py:113-114`) skips every object not ending `.tar.gz`, so the sweep
  **structurally cannot** delete the sibling `...@{sha}.manifest.json`. Every run that deletes a tarball therefore mints
  a permanent **orphan manifest**: a pin that still RESOLVES but whose code is gone.
- `unified-api-contracts` is the highest-velocity repo in the fleet (~72 live `@sha` objects), so at `--keep 5` any
  fleet outliving 5 UAC pushes loses its pin **deterministically, not unluckily** — within days.
- Consequence on 2026-07-20: every relaunch / preemption-recovery of the cefi migration fleet died at
  `scripts/vm/setup-data-pipeline-vm.sh:641-647`, which correctly refuses a floating fallback → `exit 1` → the VM
  self-deletes. This **defeats the shipped PROGRESS.json checkpoint contract outright**: resuming from the correct date
  is worthless when the pinned code tarball no longer exists.

The refusal at `setup-data-pipeline-vm.sh` is CORRECT behaviour and must be preserved — the floating tarball is by
definition newer, un-asserted code, and running it against a half-migrated corpus is a data-correctness hazard, not
merely a reproducibility one. The bug is upstream, in retention.

## 2. Root cause A — retention has no notion of "in use"

Retention is a pure mtime ranking. Nothing in the delete path consults GCE, the deployment registry, or any record of
what a live VM is pinned to. "Old" and "unused" are conflated. Because pin eviction is a function of _push velocity on
an unrelated repo_, the blast radius is unbounded and the failure is silent until a relaunch detonates on it.

## 3. Root cause B — the pair is not atomic, and only the unsafe half is deletable

The tarball and its manifest must share a fate. The sweep can only ever delete the `.tar.gz`, leaving the manifest —
which is precisely the unsafe survivor:

- manifest deleted / tarball survives → a pin that no longer resolves at all; `setup-data-pipeline-vm.sh` refuses it
  loudly ("cannot verify provenance"). Recoverable, nothing runs un-asserted code.
- tarball deleted / manifest survives → **orphan manifest**; the pin still resolves, and the failure is silent until
  recovery time. This is the 2026-07-20 shape.

## 4. Why the v1 fix is INERT (independently re-verified 2026-07-20)

The v1 fix added `deployment_service/vm/tarball_pins.py` + pin-awareness in the sweep. It does not work, because it
sources pins from a blob that no pinning launcher writes.

**The writer set and the pinner set are DISJOINT.** Measured:

- `grep -rl 'lc_write_launch_params' scripts/vm/` → **only** `launch-cefi-sharded-backfill.sh` (+ the definition in
  `lib/launcher_common.sh`). Neither call site (`:569-582`, `:778-792`) passes ANY `*_TARBALL_SHA` key — verified by
  reading both argument lists in full.
- `grep -rl 'TARBALL_SHA' scripts/vm/` → `launch-canonical-migration-vm.sh:283-285`,
  `launch-legacy-bucket-migration-sharded.sh:94-96`, `launch-mdps-backfill-vm.sh:276-277`,
  `launch-mdps-sharded-backfill.sh:293-294`, `launch-mtds-dex-swaps-backfill-vm.sh:152-156`. **All five** set the sha as
  GCE **instance metadata** (`md="${md},UAC_TARBALL_SHA=..."`) and **none** calls `lc_write_launch_params`.
- The consumer confirms metadata is the real channel: `setup-data-pipeline-vm.sh:187-192` reads each sha via
  `_meta <KEY>` (metadata server), not from any GCS blob.

Therefore:

1. **`collect_in_use_pins()` returns the EMPTY SET for every VM, always.** `tarball_pins.py:184-187` sources all pins
   from `read_launch_params`; `pins_from_launch_env` (`:106-113`) finds no `*_TARBALL_SHA` key → `frozenset()` →
   `is_pin_protected` (`cleanup_old_tarballs.py:203`) is False for every candidate. **The 2026-07-20 reap reproduces
   verbatim — and now the manifest goes with it**, since v1 added pair-deletion without fixing protection.
2. **The relaunch re-pin actuator is a no-op for the same reason.** `scripts/recovery/relaunch_backfill_vm.py:388-391`
   reads `requested = env.get(env_key, "").strip()` from the same empty launch env → the loop `continue`s on all four
   keys → ZERO re-pins, ZERO `DP_VM_TARBALL_REPINNED`, ZERO pages, ever.
3. **Pair deletion is not atomic.** `cleanup_old_tarballs.py:164-166` discards the manifest delete's return value
   (`_delete_object(manifest_path, dry_run)` unassigned) and returns only the tarball result, so a partial failure is
   reported as success.
4. **The tests are vacuous.** `tests/unit/test_tarball_pins.py:131` fabricates a `LAUNCH_PARAMS` blob shape
   (`_launch_params(UAC_TARBALL_SHA=...)`) that **no launcher produces**; `tests/unit/test_cleanup_old_tarballs.py:146`
   injects `pins=frozenset({TarballPin(...)})` directly, bypassing `collect_in_use_pins` entirely. No test exercises pin
   collection against any real launcher's actual output — which is exactly why a fix that protects nothing passed green.

Additionally, `launch-canonical-migration-vm.sh:283` gates the pin on the **ambient shell env**
(`[[ -n "${UAC_TARBALL_SHA:-}" ]]`), so an unset variable silently degrades that launch to a floating pull with no
signal — the same silent-degrade class, on the launch path rather than the retention path.

## 5. Open decision — the prescribed pin source is not reachable

The work order prescribed reading `*_TARBALL_SHA` from GCE **instance metadata**, "reusing the EXISTING transport
(`aggregated_list_instances` / `gcp_instance_lister.py:44` → `metadata.items`)". **That transport does not carry
metadata.** Measured:

- `unified-trading-library/unified_trading_library/cloud_interface/providers/gcp_compute.py:172-179` builds each result
  dict with exactly three keys — `{"name", "status", "zone"}`. Instance metadata is dropped at the provider boundary and
  never crosses into deployment-service.
- The `ComputeEngineClient` abstraction
  (`unified-trading-library/unified_trading_library/cloud_interface/abstractions.py:617-631`) exposes only
  `provider_name`, `aggregated_list_instances`, and `get_serial_port_output`. There is **no** metadata-bearing method.
- deployment-service has no other compute path; importing `google.cloud.compute_v1` directly is QG-banned, and shelling
  out to `gcloud` is the pattern being retired.

So instance-metadata pin collection **requires an additive change to unified-trading-library** (include `metadata` in
the `aggregated_list_instances` result dict). The work order forbids touching UTL, citing in-flight foreign WIP — but
the UTL working tree is measurably **CLEAN** (`git -C unified-trading-library status --porcelain` → empty), so the
stated basis for that constraint does not currently hold. (instruments-service IS dirty as stated, and was not touched.)

### Options

- **A — additive UTL change [RECOMMENDED].** Add `metadata` to the dict in `gcp_compute.py:172-179` (plus the
  abstraction docstring). Purely additive, no existing caller reads the dict exhaustively, UTL tree is clean. Instance
  metadata then becomes the primary pin source, covering already-running VMs on day one. Union it with a durable
  bucket-side pin registry (below) for the deleted/preempted window.
- **B — launcher-written durable pin registry only (no UTL change).** Add `lc_write_tarball_pin_record` to
  `lib/launcher_common.sh`, call it from all five pinning launchers, write `vm-logs/{vm}/TARBALL_PINS.json` at launch.
  Fully inside deployment-service and satisfies "a source the five pinning launchers actually populate". Residual gap:
  VMs launched BEFORE rollout have no record, so the sweep must fail closed whenever a RUNNING data-pipeline-prefixed VM
  has no pin record — cleanup pauses loudly until the fleet recycles, rather than reaping silently.
- **C — A + B (both sources, union).** Strictly the most robust and what a final design should converge on; B alone is
  the safe subset if UTL must stay untouched.

Under all options the remaining requirements are unchanged and independent: fail-closed on lister/registry error, atomic
pair semantics (delete the manifest only AFTER the tarball delete succeeds, check BOTH results), a real re-pin actuator
reading the same authoritative source and emitting a loud old→new audit record, making the
`launch-canonical-migration-vm.sh:283` ambient-env gate observable, and non-vacuous tests built from a real launcher's
actual output shape.

## 6. Residual risk while unfixed

The cron is live and fires daily at 02:00 UTC with `--keep 5` and no dry-run. Every run can evict a live pin and mints
orphan manifests. Any SPOT preemption or relaunch of a pinned fleet during this window fails silently and self-deletes.
**Interim mitigation available without any code change: raise `--keep` substantially or suspend `tarball_cleanup_cron`**
until the fix lands — storage cost is negligible against a silently bricked fleet recovery.
