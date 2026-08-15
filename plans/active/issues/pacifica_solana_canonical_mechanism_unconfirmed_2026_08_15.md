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
status: open
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
resolved_by:
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

- [ ] [DATA] P3. Identify and document the mechanism that made the 787 `PACIFICA-SOLANA` raw-tick objects + manifest
      rows canonical between the 2026-08-14 and 2026-08-15 scans, per the investigation steps above (repos:
      market-tick-data-service, instruments-service).
