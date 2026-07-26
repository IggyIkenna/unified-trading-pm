---
doc_type: issue
title: "CME monolith trades migration tool built + shipped — execution against real objects still pending"
summary: >-
  `market_tick_data_service/scripts/migrate_cme_monolith_trades_2026_07_26.py` (mtds@02284f8e) is designed, built,
  unit-tested, and quality-gates green — it migrates the 30 real `day=*/venue=CME/ticks.parquet` monolith objects
  (Databento MBP-0/trades, all CME symbols mixed per day, no Hive partitioning) to canonical per-contract/chain form via
  the SAME production write path live adapters use (`write_tradfi_shard`), then additively registers manifest rows. This
  doc tracks what's NOT yet done: actually running the tool against the 30 real objects, verifying the writes, and
  (separately, gated) running its `--delete-source` phase.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer]
tags: [tradfi, cme, migration, only-copy, manifest]
related: [/plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md]
created: 2026-07-26
priority: P2
parent_epic: mtds_mdps_master
source: "slot 3, interactive session, 2026-07-26, /autonomous dispatch on the CME monolith P2 todo"
assigned_vm: NA
execution_scope: local-only
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
---

# CME monolith migration — tool shipped, execution pending

## What's done

- Tool designed + built: reuses `classify_databento_symbol` (real production classifier — combo/option/future/
  continuous detection, expiry derivation) and `write_tradfi_shard` (real production canonical write path) rather than
  reimplementing canonicalisation logic. Combo rows with an unrecoverable underlying are dropped (honest absence),
  mirroring `databento_enrichment.py::_classify_row` exactly.
- Manifest safety mirrors the proven `canonicalize_cme_options_chain_legacy_flat_2026_07_14.py` precedent: additive
  CAS-write, pre-write snapshot backup, consolidator-cron pause/resume (best-effort), dedup-for-idempotency.
- Verify-before-manifest-row: every real write is re-downloaded and row-count-checked before a manifest row is even
  constructed for it.
- `--delete-source` is a SEPARATE CLI phase (never bundled with migrate) that refuses to delete any source object unless
  the live manifest already shows a `captured` row for that day — re-verified live, not from a stale ledger.
- Real worklist: the 30 real days were directly enumerated 2026-07-26 (server-side `match_glob`, 339s off-region —
  confirms this exact shape's already-documented cross-region listing latency) and hardcoded as the tool's static
  worklist (single-walk discipline; this is dead legacy data, no longer written to). One malformed partition value
  observed (`day=2026-03-20T00:00:00+00:00` instead of a plain date) is handled explicitly.
- Shipped: `mtds@02284f8e` — `market_tick_data_service/scripts/migrate_cme_monolith_trades_2026_07_26.py` +
  `tests/unit/scripts/test_migrate_cme_monolith_trades_2026_07_26.py`. Full `quality-gates.sh` green (7056+ tests
  passed, lint clean, no new basedpyright/codex-compliance violations).

## What's NOT done (this doc's actual scope)

- [ ] [DATA] P2. Run the migrate phase for real against all 30 objects on a VM (per
      `/codex/05-infrastructure/vm-launcher-runbook.md`'s heavy-I/O rule — not from a laptop), via
      `launch-canonical-migration-vm.sh` (either add a new category mirroring `tradfi-manifest-cas`'s pattern, or a
      generic VM exec wrapping
      `python -m market_tick_data_service.scripts.migrate_cme_monolith_trades_2026_07_26     --all-days --apply --stamp <ts>`).
      Start with `--day <one>` as a canary before `--all-days`.
- [ ] [DATA] P2. Verify the real write: re-check the live manifest shows new `captured` rows for
      `venue=CME,     data_type=trades` across the expected days/underlyings, and spot-check 2-3 written canonical
      objects' content (instrument_id, row counts) directly.
- [ ] [DATA] P2. Run `--delete-source` in DRY-RUN first (default) and report the candidate list — this is an only-copy
      corpus (2026-07-21 reconciliation report), so the actual `--apply` delete is a judgment call for whoever picks
      this up, informed by the dry-run's confirmed-migrated-days list. Never auto-apply the delete in the same pass as
      migrate.

## Why split into its own doc

The parent plan (`tradfi_manifest_content_recovery_completion_2026_07_24.md`) is at its 1000-line hard cap; this sibling
doc carries the remaining execution scope per the standard "outside-plan → issue doc" convention rather than cramming
further into an already-full file.

## Codex SSOTs

`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` (only-copy delete discipline),
`/codex/05-infrastructure/vm-launcher-runbook.md` (heavy-I/O-on-a-VM rule).
