---
doc_type: issue
title: Manifest schema-drift dup — root causes resolved, residual re-scoped to operator decision
summary: >-
  Live re-measurement confirms the 2026-05-04 schema-drift-dup finding's named root causes (instrument_type casing +
  schema_version drift) are resolved; a different residual (byte-identical legacy duplicates the incremental
  consolidator merge never re-examines once settled) remains and needs an operator decision on scheduled force=True
  rebuilds, not a writer-side code fix.
assigned_vm: NA
created: "2026-08-15"
last_updated: "2026-08-21"
author: slot-11 (infra)
source: [plans/active/cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md]
status: open
nature: issue
parent_epic: security_and_cross_cutting_master
priority: P2
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library, unified-trading-pm]
scope: [engineer]
tags: [manifest, consolidator, dedup, data-correctness]
related: [/plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md]
resolved_by:
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    unified-trading-library/unified_trading_library/manifest_consolidator.py,
    deployment-service/scripts/migrations/instruments-service/dedupe_manifest_schema_drift.py,
    /plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md,
  ]
---

# Manifest schema-drift dup — root causes resolved, residual re-scoped

## What I found

Investigated the source doc's todo: "Investigate the systemic schema-drift dup (16% of shards with >1 manifest row) and
fix writer-side row-key idempotency" (originally measured 2026-05-04 via `scripts/dedupe_manifest_schema_drift.py`
against `gs://market-data-tick-cefi-.../…availability_index.parquet`).

Bounded live re-measurement (2026-08-15, column-projected + predicate-pushed pyarrow read of the prod CeFi manifest, no
full-corpus load):

- At the original script's coarse key (venue, date, data_type, instrument_id), BINANCE-FUTURES now shows 9.94% shards
  with >1 row (down from the 2026-05-04 baseline's 16%). Sampling those groups shows `instrument_type` uniformly
  `PERPETUAL` and `schema_version` uniformly `9` — the casing/schema-version drift the original finding named is GONE,
  fixed by `canonicalize_manifest_instrument_type()` landing in the writer's `_record_status`/`record_captured` paths
  (2026-07-27) plus the consolidator's `TRY_CAST`-typed column projection (2026-07-20).
- Most of the remaining coarse-key "duplication" is legitimate: 2+ different `service_name` producers (MTDS raw
  capture + MDPS derived candles) each correctly hold their own row for the same shard identity — `service_name` is a
  BASE dedup-key column by design (`manifest_consolidator._BASE_DEDUP_COLS`), not drift.
- At the TRUE consolidator dedup key (adding `service_name` + `instrument_type` + `timeframe`), duplication drops to
  4.15%. The residual rows are BYTE-IDENTICAL twins — same `date`/`data_type`/`instrument_id`/`service_name`/
  `instrument_type`/`timeframe`/`capture_status='captured'`/`attempted_at` down to the microsecond.

## Why it matters

The residual is NOT a writer race or a missing dedup dimension. It is a structural property of the manifest
consolidator's INCREMENTAL merge (`manifest_consolidator.py::consolidate()`, the steady-state `*/1` cron path): it
re-dedupes ONLY the keys touched by shards whose mtime is newer than the last content-write marker, and streams the rest
of the canonical straight through unexamined (by design, for bounded memory on a 75M+-row canonical). A duplicate pair
that entered the canonical BEFORE the consolidator's dedup key/status-priority logic matured (2026-07-12 source-aware
collapse, 2026-07-15 legacy-seed guard) and that no later shard-write has touched since stays in the canonical FOREVER
under the routine incremental cron — only an explicit `consolidate(bucket, force=True)` full rebuild re-examines it.

## Recommended decision

Did NOT attempt a code change to `manifest_consolidator.py` (3625 lines, 15+ documented production incidents in its own
module comments, heavily memory/perf-tuned) or to the per-VM shard writer. Whether the durable fix is a scheduled
periodic full-rebuild (compute/memory cost tradeoff on multiple multi-hundred-GB canonicals) vs. a narrower
incremental-merge enhancement is an operator/design call, not a worker-determinable outcome, per CLAUDE.md's
"AO-eligible = outcome determinable by the worker alone" rule.

## Todos

- [ ] [OPERATOR] P2. DEFERRED-BY-DESIGN — per D94 ruling (2026-08-21, issues_corpus_completion_dispatch_2026_08_21.md
      ledger): No action — touching the incident-scarred 3625-line consolidator carries more risk than the
      duplication's cost. Original ask: decide whether to schedule periodic `consolidate(bucket, force=True)`
      full-rebuild sweeps across the CeFi/other per-AG manifest buckets to durably clear byte-identical legacy-
      duplicate manifest rows the routine incremental `*/1` consolidator cron structurally never re-examines once
      settled (measured 2026-08-15: BINANCE-FUTURES ~4.15% dup shard-keys at the true dedup key). Repo:
      unified-trading-library (consolidator) + deployment-service (scheduler).

## Progress Log

- **context-scout 2026-08-17**: populated context_scope (4 entries).
- **na-eligibility-audit 2026-08-17** [body-hash:34db568726207d9c]: KEEP-NA, valid -- Sole open todo is explicitly [OPERATOR]-tagged and the doc's own 'Recommended decision' section states in plain text that the choice between a scheduled periodic full-rebuild sweep vs. a narrower incremental-merge enhancement 'is an operator/design call, not a worker-determinable outcome, per CLAUDE.md's AO-eligible = outcome determinable by the worker alone rule' — citing the exact governing rule against itself. The doc explicitly declined to attempt a code change to the 3625-line, heavily production-incident-scarred manifest_consolidator.py.
- **context-scout 2026-08-20**: refreshed context_scope (4 entries) — repointed the schema-drift dedupe script entry to its actual location (deployment-service/scripts/migrations/instruments-service/, not instruments-service/scripts/).
- **2026-08-21 — ruling D94 (Byte-identical manifest duplicates)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch
  authority, AUTONOMOUS_AGENT_RULES rule 2): No action — touching the incident-scarred 3625-line consolidator
  carries more risk than the duplication's cost. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md
  ledger.
