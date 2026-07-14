---
doc_type: plan
title:
  Deployment registry Firestore migration — Phase 2 — migrate readers to Firestore + decouple existence from enrichment
summary:
  Cut every registry reader from downloading N GCS blobs to a single indexed Firestore query, Firestore-first with a
  loud GCS fallback so it stays identical to today while Firestore fills. The safety-critical part — inventory EVERY
  reader before cutting any (dual-write must outlive the last reader) — and the correctness win — decouple the census so
  VM rows come from the fast GCE list and registry metadata is best-effort per row, so a slow or absent registry
  degrades enrichment columns to a dash, never the row set. Removes the download-all-in-45s failure mode entirely.
status: draft
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-api, unified-trading-library]
scope: [engineer]
tags: [firestore, deployment-registry, census, partial-render, migration]
related:
  - deployment_registry_firestore_migration_2026_07_14.md
  - deployment_registry_firestore_p1_dualwrite_2026_07_14.md
created: "2026-07-14"
last_updated: "2026-07-14"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
assigned_role: backend-engineer
model_tier: opus-required
drift_direction: advance-code
depends_on:
  - deployment_registry_firestore_p1_dualwrite_2026_07_14.md
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: deployment_registry_firestore_migration_2026_07_14.md (master, Phase 2)
---

# Phase 2 — Migrate readers to Firestore + decouple existence from enrichment

> **Dispatch:** `assigned_role: backend-engineer` · **model: Opus** (`opus-required`) · **effort: max** — highest
> blast-radius phase. `status: active`; `gate_on_depends` holds it until Phase 1 is done, `sequential: true` orders its
> todos. Runs in PARALLEL with Phase 4 (both gate only on Phase 1).

> **SAFETY-CRITICAL SEQUENCING:** the Phase-1 dual-write must OUTLIVE the last reader. Do the reader INVENTORY (first
> todo) BEFORE cutting any reader. A missed reader that still parses GCS after cutover reads stale/empty data.

## Context (read first — self-contained)

Phase 1 made Firestore a validated mirror (collection `deployments`, doc/deployment_id, `query_by_status`). This phase
moves reads there. Two things happen together:

1. **Reader migration (Firestore-first, GCS-fallback).** Build a migration-safe primitive that reads Firestore first and
   **degrades LOUDLY to the GCS list** on empty/error — so while Firestore is still filling it returns exactly today's
   data, then shifts to Firestore-truth as docs appear. Every reader routes through it. (Same pattern as
   `resolve_ci_status_map` in the CI-status migration.)

2. **Decouple existence from enrichment (the partial-render fix).** Today the `"gcp-vm"` census bundles the GCE VM list
   (fast) and the registry download (slow) into ONE future bounded by `_PROVIDER_CENSUS_TIMEOUT_SEC = 45.0`; on timeout
   `_census_or_degrade("gcp-vm", f_vm, empty_vm)`
   ([`deployments_inventory.py:1615`](../../deployment-api/deployment_api/routes/deployments_inventory.py)) throws away
   BOTH — so the 44 live VMs vanish with the registry. Split them: build VM rows from the GCE aggregated list
   (`get_vm_instance_details` — the unmanaged-VM row-builder already exists in `deployments_inventory.py`), then enrich
   each row from the single Firestore `query_by_status` result, **best-effort per row**. A slow/absent registry sets
   enrichment columns (umbrella/health/heartbeat/disk-mem) to "—", never removes the row.

Readers to inventory (starting list — the first todo must confirm/complete it): the census (`deployments_inventory.py`),
`vm_deployments.py`, `fleet_reconciliation.py`, `fleet.py`, the `/{id}/detail` drill-down, `reap_stale` itself
(`list_active`), and any UI/CLI consumer.

**Gotchas:** dual-write stays ON the whole phase (do not touch Phase 1's write path). The GCS-fallback must be LOUD (a
logged warning), not silent. Per-provider census isolation (other KINDs — Cloud Run jobs/AWS/scheduler) must remain
untouched. No `raise` in per-row enrichment (best-effort). UTC datetimes; QG-green before commit.

## Todos

- [ ] [REVIEW] P2. Reader inventory (audit) — grep every consumer of `list_active` / the GCS registry read and produce
      the definitive cutover checklist (file : read-call), confirming/extending the starting list above. This is the
      gate for the rest of the phase; record it in the Progress Log.
- [ ] [BACKEND] P2. Add the migration-safe read primitive (e.g. `resolve_active_registry()` in deployment-api) —
      Firestore `query_by_status`/`list` first; on empty or error, **log a warning and fall back to the GCS list**
      (verbatim today's behaviour). Unit-test both branches (Firestore-hit and GCS-fallback-on-error).
- [ ] [BACKEND] P2. Decouple the census: in `deployments_inventory.py`, build VM rows from the GCE list first, then
      enrich each from the Firestore query result, best-effort per row (missing/failed enrichment → columns "—", row
      stays). The `"gcp-vm"` future must NO LONGER be able to drop live VMs on a slow registry read.
- [ ] [BACKEND] P2. Cut each reader from the inventory to `resolve_active_registry()`, one at a time (census,
      vm_deployments, fleet_reconciliation, fleet, detail drill-down, reap path). Keep dual-write on throughout.
- [ ] [REVIEW] P2. Parity + fault-injection + scale tests: (a) inventory matches the pre-migration live fleet; (b)
      inject a registry-read failure and assert rows STILL render with enrichment "—" (not an empty tab); (c) with 1k+
      synthetic Firestore docs the query path stays well under the 45s bound. `bash scripts/quality-gates.sh` green in
      deployment-api and UTL.
- [ ] [INFRA] P2. Ship (commit + push, cite shas) and flip this plan's items (`docs(plans):`). THEN hand off — set
      `deployment_registry_firestore_p3_cutover_2026_07_14.md` frontmatter `status: draft`→`active` and commit
      (`docs(plans):`) so the fleet ingests Phase 3 (the cutover). Activate ONLY Phase 3, nothing further.

## Success criteria

- Every reader in the inventory reads Firestore-first with a loud GCS fallback; none parse `active/` blobs directly.
- Census renders every live VM from the GCE list; a registry-read failure degrades enrichment columns, never the row set
  (proven by fault injection).
- Query path stays under budget at 1k+ docs; other census KINDs (Cloud Run/AWS/scheduler) unaffected.
- No `raise` in per-row enrichment; UTC datetimes; QG green both repos.

## Codex SSOTs

- `codex/04-architecture/shard-level-failure-isolation.md` — the per-KIND degradation principle the census follows.
- `codex/05-infrastructure/deployment-observability.md` — registry SSOT (updated Phase 5).
