---
doc_type: issue
title: PACIFICA-SOLANA canonical-rename mechanism unconfirmed — no tracked commit found
summary: >-
  pacifica_solana_ao_dispatch_2026_08_15.md (archived) re-verified 787 PACIFICA-SOLANA raw-tick GCS objects and found
  them ALREADY carrying canonical PACIFICA-SOLANA:PERPETUAL: filenames + 787 matching manifest rows, even though the
  plan's own scope was to EXECUTE that rename+backfill migration. Both todos' Progress Log entries confirm zero
  tracked rename/migration commits landed in either consumer repo between the 2026-08-14 and 2026-08-15 scans. Data
  is independently verified CORRECT; the mechanism that produced it is not. Filed per the finalize review's own
  archival-ritual check (plan-completion-and-archival-discipline.md § "every follow-up is a canonical todo, never
  prose") — this was flagged twice in the now-archived plan's Progress Log as "out of scope to root-cause here" and
  never converted into a tracked todo.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, market-tick-data-service]
scope: [engineer]
assigned_vm: planning
execution_scope: orchestrator-agent
tags: [defi, canonicalization, pacifica, data-provenance, investigation]
priority: P3
source: pacifica_solana_ao_dispatch_2026_08_15_finalize_review_2026_08_15
parent_epic: defi_master
related:
  [
    /plans/archive/2026_08/pacifica_solana_ao_dispatch_2026_08_15.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-15
resolved_by: pacifica_solana_canonical_mechanism_unconfirmed_2026_08_15_worker_2026_08_16
locked_by:
drift_direction: advance-code
depends_on: []
context_scope: [/plans/archive/2026_08/pacifica_solana_ao_dispatch_2026_08_15.md]
---

# PACIFICA-SOLANA canonical-rename mechanism unconfirmed

## What I found

`pacifica_solana_ao_dispatch_2026_08_15.md` (now archived at
`/plans/archive/2026_08/pacifica_solana_ao_dispatch_2026_08_15.md`) re-verified 787 `PACIFICA-SOLANA` raw-tick GCS
objects and found them ALREADY carrying the canonical `PACIFICA-SOLANA:PERPETUAL:` filename prefix, with 787 matching
manifest rows (`ohlcv_1m`/`captured`, spanning 2025-07-15..2025-12-31) already present — even though the plan's own
scope was to EXECUTE that rename+backfill migration (it had NOT been done as of the prior 2026-08-14 scan that
originally discovered these 787 objects). Both todos' Progress Log entries record the same check:
`git log --since="2026-08-15 07:00" --all -i --grep=pacifica` across both `instruments-service` and
`market-tick-data-service` returned ZERO commits — no tracked rename/migration landed between the two scans. The
mechanism that produced the canonical filenames + manifest rows is UNCONFIRMED. This was noted twice in the archived
plan's Progress Log as "out of scope to root-cause here" — prose, never converted into a tracked todo, which is the
gap this issue doc closes.

## Why it matters

Data pipeline correctness is this workspace's heartbeat HARD RULE. An unexplained production data mutation — even one
independently re-verified as CORRECT (right count, right shape, right canonical form, manifest 1:1) — is worth
confirming the mechanism for: it is either (a) an expected, recurring capture-adapter behavior (e.g. a scheduled
live/backfill capture job re-writing these shards with the modern adapter's canonical id-builder as ordinary
operation, worth documenting so a future "already canonical" surprise for a quarantined venue isn't re-investigated
from scratch), or (b) an undocumented/unaudited process writing to prod outside the normal migration-tracking
discipline, which would be a process gap worth closing.

## Recommended decision

Investigate and document which of (a)/(b) is true:

- Check `market-tick-data-service` (and `instruments-service`) for any scheduled/cron capture job whose lookback
  window covers 2025-07-15..2025-12-31 for `venue=PACIFICA-SOLANA` that could plausibly have re-written these shards
  using the modern adapter's canonical id-builder as a normal side effect of routine operation.
- Sample GCS object metadata (e.g. blob `updated`/`timeCreated`) on a handful of the 787 objects to establish WHEN the
  canonical rename actually happened, and correlate against any deploy/capture-run timestamp in that window.
- Once the mechanism is identified, document it (a short note in the relevant capture-service's own module docs/
  comments is enough) so a future scan finding an already-quarantined venue "already canonical" isn't re-investigated
  from scratch.

- [x] ✅ [DATA] P3. Identify and document the mechanism that made the 787 `PACIFICA-SOLANA` raw-tick objects + manifest
      rows canonical between the 2026-08-14 and 2026-08-15 scans, per the investigation steps above (repos:
      market-tick-data-service, instruments-service). — `unified-api-contracts@e33011699d`,
      `market-tick-data-service@1d977903d7`.

## Progress Log

- **2026-08-16 (mechanism confirmed)**: sampled GCS blob `last_modified` metadata on all 787 `PACIFICA-SOLANA`
  raw-tick objects across the full 2025-07-15..2025-12-31 window (every `day=` prefix, not a subsample) via
  `unified_trading_library.get_storage_client()` against the live `market-data-tick-cefi-prd-central-element-323112`
  bucket. Result: every object's `last_modified` falls inside a single ~16.5-minute window,
  **2026-08-15T14:47:40Z-15:04:12Z**, strictly monotonic in chronological `day=` order (day=2025-07-15 first,
  day=2025-12-31 last) — the unambiguous signature of one sequential day-ordered backfill/rewrite run, not organic
  drip-fed live capture. No legacy bare-stem (non-canonical) object remains at any sampled prefix — confirms a genuine
  rename/rewrite, not coexistence of old+new names. Traced the code path:
  `market_tick_data_service/engine/orchestrator/partitioned_writer.py::PartitionedWriter._resolve_writer_file_name`
  already wraps every CeFi/on-chain-perp single-instrument write in its resolved canonical `instrument_id` (written
  verbatim as the filename) — this is the STANDARD writer path every capture/backfill run for this venue has used
  since its 2026-08-14 reintegration, not migration-specific code. **Conclusion: option (a)** from this issue's
  "Recommended decision" — an ordinary capture/backfill CLI re-run for `PACIFICA-SOLANA` over
  2025-07-15..2025-12-31, issued directly against the existing, already-canonical-by-default writer (no new script,
  hence no commit in either repo), fully explains both the rename and the manifest backfill as routine operation.
  Documented in `unified_api_contracts/canonical/quarantine.py`'s `QUARANTINE_REGISTRY["PACIFICA-SOLANA"]` entry
  (`unified-api-contracts@e33011699d`) and the reconcile script's own docstring
  (`market-tick-data-service@1d977903d7`) so a future "already canonical" surprise for a quarantined venue isn't
  re-investigated from scratch. Every todo in this issue is now done — resolved.
  Side finding filed as a separate P1 issue (out of this task's scope to fix): quickmerge's
  `no_hardcoded_venue_urls.sh` pre-push gate is currently RED for market-tick-data-service on a pre-existing,
  unrelated hardcoded `blue-api.morpho.org` literal in `_oracle_prices_constants.py` (dated 2026-08-14, confirmed not
  part of this task's diff) — see `/plans/active/issues/mtds_morpho_hardcoded_url_qg_red_2026_08_16.md`. The gate did
  not actually block this task's push (non-fatal in the version that ran), but the violation itself is still live on
  `origin/live-defi-rollout`.
