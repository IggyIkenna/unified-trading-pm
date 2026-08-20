---
doc_type: issue
title: >-
  unified_trading_library.cloud_interface's download_from_storage/list_blobs returned stale content for a
  frequently-updated GCS object, producing a false "possibly wedged VM" alarm
summary: >-
  While re-verifying a live shard-24 backfill VM's health (cefi_residual_ao_dispatch_2026_08_15_finalize.md), repeated
  fresh-client calls to `get_storage_client().list_blobs()` / `download_from_storage()` against the VM's GCS-synced
  `run.log` object returned content frozen at a `last_modified` timestamp 40+ real minutes stale — long enough to look
  like a genuine stall (the VM's own watchdog log appeared frozen too, by the same read path). Direct SSH into the VM
  and `tail`ing its LOCAL log file immediately disproved the stall: the process was healthy and progressing normally the
  whole time. Not root-caused — worth investigating if this recurs, since it can directly mislead a stall/wedge
  diagnosis the same way it did here.
status: open
nature: issue
asset_group: [infrastructure, cefi]
stage: [meta]
repos: [unified-trading-library, instruments-service]
scope: [engineer]
tags: [gcs, cloud_interface, staleness, caching, vm-monitoring, false-positive, big-finding]
related:
  [/plans/archive/2026_08/cefi_residual_ao_dispatch_2026_08_15_finalize.md, /codex/05-infrastructure/gcs-object-operations.md]
created: "2026-08-15"
author: ikennaigboaka [slot-16]
priority: P3
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
effort: medium
drift_direction: advance-code
estimate_class: research
depends_on: []
parent_epic: security_and_cross_cutting_master
resolved_by:
source: "cefi_residual_ao_dispatch_2026_08_15_finalize.md re-verification session, 2026-08-15"
locked_by:
context_scope:
  [
    /codex/05-infrastructure/gcs-object-operations.md,
    unified-trading-library/unified_trading_library/cloud_interface,
    deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh,
    /plans/active/issues/cefi_content_migration_shard24_recurring_wedge_needs_diagnosis_2026_08_09.md,
  ]
---

# `cloud_interface` stale-read finding — misled a VM stall diagnosis

## What happened

Verifying `canonical-migration-cefi-content-apply-20260815-181337`'s health, two separate fresh-client
`get_storage_client().list_blobs(...)` + `download_from_storage(...)` calls (via `instruments-service`'s own venv),
roughly 40 minutes apart, both returned the GCS-synced `run.log` object with an IDENTICAL `last_modified` timestamp and
byte-identical tail content — despite the underlying VM process being confirmed (via direct SSH `tail` of its LOCAL,
pre-GCS-sync log file) to be actively healthy and writing new progress lines the entire time. A THIRD call, made
immediately after, returned genuinely fresh content (a larger size, a newer `last_modified`, new tail lines) — no code
change, no explicit cache-bust, just a retry.

This is not merely a sync-lag question (the `vm-exec-with-gcs-tee.sh` wrapper that mirrors the VM's local log to GCS
plausibly batches or delays its own uploads) — a NORMAL sync lag would not explain two consecutive reads 40 minutes
apart returning byte-identical content while a THIRD read moments later was current. That pattern is more consistent
with the read path (client library, an intermediate HTTP cache, or GCS's own read-after-write consistency window for a
frequently-overwritten object) serving stale content on some reads and fresh content on others, unpredictably.

## Why it matters

The false "stale run.log" reading produced a genuine, several-minutes false alarm that the VM might be wedged (matching
a real, previously-diagnosed failure class for this exact shard —
`plans/active/issues/cefi_content_migration_shard24_recurring_wedge_needs_diagnosis_2026_08_09.md`) — only resolved by
falling back to direct SSH + a local-file `tail`, which is a heavier, less-scalable check than the intended GCS-based
one. Any future automated monitor (or agent) using `cloud_interface.download_from_storage`/`list_blobs` to poll a
live-updating object for staleness/health could reach the same false conclusion.

## Not root-caused (this session)

Three plausible mechanisms, none confirmed or ruled out:

1. Client-side caching inside `unified_trading_library.cloud_interface` or the underlying `google-cloud-storage` client
   (e.g. a cached `Blob` object not calling `.reload()`).
2. `vm-exec-with-gcs-tee.sh`'s own upload cadence genuinely lagging by tens of minutes under some condition (not just
   the normal few-second lag observed elsewhere).
3. GCS read-after-write staleness on a single, frequently-overwritten object (unusual for GCS's strong consistency model
   on reads of the latest object version, but not impossible if requests hit different edges/paths).

## Todos

- [ ] [INFRA] P3. **Root-cause which of the 3 mechanisms above (or another) explains the stale reads** — reproduce
      deliberately: write to one GCS object in a tight loop from one process while polling it via
      `cloud_interface.download_from_storage`/`list_blobs` from a fresh client each time; compare against a parallel
      `gcloud storage cat`/direct REST poll of the same object to isolate whether the staleness is client-library-side
      or genuinely server-side. (repo: unified-trading-library)
- [ ] [DOC] P3. **If confirmed client-side caching**: document the workaround (e.g. `blob.reload()` or a cache-busting
      query param) in `/codex/05-infrastructure/gcs-object-operations.md`, and note it as a caveat anywhere the codebase
      polls a live-updating GCS object for freshness/health (VM watchdogs, log tailers). (repo: unified-trading-pm)

## Progress Log

- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:be800b4106c15bf3]: RECLASSIFY_WHOLE —
  `assigned_vm: NA` → `planning`. Both open todos are bounded, deterministic engineering work with a stated
  reproduction method and done-when; no operator gate, banner, or `depends_on` found. Conflict-check clean — a
  same-day cefi-tranche `/na-eligibility-audit` run independently found this doc, correctly deferred to infra
  ownership per the Phase-0 primary-owner rule, and took no action on it (see
  `cefi_satellite_ao_dispatch_batch21_2026_08_17.md`'s own Progress Log).
- **context-scout 2026-08-17**: populated context_scope (4 entries) -- expanded from the sole codex SSOT to add the
  UTL `cloud_interface` module and the `vm-exec-with-gcs-tee.sh` wrapper (both named in the doc's own root-cause
  hypotheses), plus the sibling shard-24 wedge-diagnosis issue doc cited under "Why it matters".
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
