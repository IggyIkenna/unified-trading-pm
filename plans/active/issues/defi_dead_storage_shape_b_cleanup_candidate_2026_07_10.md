---
doc_type: issue
title: DeFi — ~104K dead-storage duplicate objects, confirmed unread by every real consumer (safe-to-delete candidate)
summary:
  The DeFi legacy-naming audit (2026-07-09) found a fully distinct duplicate write path
  (`day={D}/pipeline_mode=batch_instruments_service/asset_group=defi/venue={V}/...`) mirroring ~104K real objects in the
  `-prd-` bucket. Two spot-checked samples (oldest 2020-01-20, recent 2026-06-10, CRC32C+MD5 hash-verified) were
  byte-for-byte identical to their flat-shape sibling, and every real consumer confirmed to read only the flat shape.
  Recommended as its own dedicated SAFE-TO-DELETE audit — not executed, and not a full-corpus reconciliation (only 2
  samples checked).
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [instruments-service]
scope: [engineer, admin]
tags: [dead-storage, cleanup, gcs, cost, defi]
related: [instrument_id_format_canonicalization_2026_07_08.md]
created: 2026-07-10
parent_epic: instruments_master
assigned_vm:
resolved_by:
source:
  "Real finding from the DeFi legacy-naming audit agent (wf_9e5f13e3-962, 2026-07-09), the same session that found and
  fixed the ghost-venue-merge + its data-contamination bug."
priority: P3
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

## What I found

Real narrow-prefix GCS listing across `instruments-store-defi-prd-central-element-323112` found a second, fully distinct
real duplicate write path: `day={D}/pipeline_mode=batch_instruments_service/asset_group=defi/venue={V}/...` mirroring
~104K real objects (2,353 of 2,363 real day-partitions) of the flat-shape tree. Real writes to this shape stopped
~2026-06-30 (confirmed dead going forward, not an actively-growing duplicate).

**Confirmed real, not assumed**:

- 2 spot-checked samples (oldest real date `day=2020-01-20`, a recent `day=2026-06-10`), CRC32C+MD5 hash-verified —
  byte-for-byte identical to the flat-shape sibling.
- Confirmed **unread by every real consumer** — grepped `unified_trading_library`'s `instrument_lifecycle_loader.py`,
  `domain/instruments_client.py`, `domain_client/clients/instruments.py`, `options_cluster_lookup.py`,
  `core/cloud_data_provider.py` — all read the flat shape only.

**Important caveat, stated honestly by the finding agent**: this is only 2 spot-checked samples out of 2,353 real
day-partitions, not a full reconciliation — treat as a real-but-narrow finding, not a proven full-corpus guarantee,
until a dedicated audit checks more broadly (or all) of the 2,353 partitions.

This mirrors the exact same shape-B pattern the CeFi legacy-naming audit found for OKX in the same session — but unlike
OKX's shape B (which DID carry stale/buggy unmigrated content and needed a real fix), this DeFi shape B appears to be
genuinely redundant dead storage, not a coverage gap.

## Why it matters

~104K real objects of confirmed-dead, confirmed-duplicate storage is a real, quantifiable GCS cost with zero functional
value if the full-corpus check confirms the 2-sample finding holds broadly. Not urgent (no correctness risk — nothing
reads it), but a legitimate cleanup opportunity once verified safe at scale.

## Recommended next step

A dedicated SAFE-TO-DELETE audit, same pattern as
`market-tick-data-service/e2e-testing/scripts/defi/ audit_legacy_gcs_dup_delete_list.py` and the exact shape-B pattern
the CeFi audit already used:

1. Real full (or much larger sample) reconciliation across all 2,353 real day-partitions — confirm byte-identical
   duplication holds broadly, not just for 2 samples.
2. Re-confirm zero real consumers read this shape (broader grep + a runtime check if feasible, e.g. log-based access
   auditing over a real time window).
3. Only then: a real, backup-first (or GCS-versioning-based) deletion pass, with the same rigor as every other migration
   this session (dry-run first, verify, then real delete).
