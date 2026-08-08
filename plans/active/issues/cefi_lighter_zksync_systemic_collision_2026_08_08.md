---
doc_type: issue
title: CeFi LIGHTER-ZKSYNC systemic wire/canonical dual-write collision — 11,494 objects across 30+ dates (2026-08-08)
summary: >-
  During the `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` resume sequence's 4-venue safe-residual
  apply, the LIGHTER-ZKSYNC leg — previously characterized as "zero collision risk" per that doc's Finding 10 — hit
  STOP-ON-SURPRISE with 11,494 genuine collisions spanning 30+ distinct dates (2026-04-18, plus a dense run
  2026-06-24..2026-07-14 at ~157/day, ~157 = the full LIGHTER-ZKSYNC PERPETUAL symbol universe). This is a materially
  larger/different-shaped population than the single-day precedent (Finding 8/10's HYPERLIQUID/ASTER 6-date pattern) —
  it looks like an ongoing, ~2-month ranging dual-write (both wire-form and canonical-form objects being written for the
  same day/symbol slot), not a one-off transitional artifact. Zero mutation occurred (script correctly refused).
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [cefi, manifest, chain-drop, late-renames, collision, data-correctness]
related:
  [
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
    /plans/active/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_finalize_2026_08_08.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: 2026-08-08
author: unknown
parent_epic: cefi_master
priority: P2
source: >-
  Discovered while resuming cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md's sole open todo (the
  2,962-object safe-residual venue-scoped rename apply), slot 18, 2026-08-08.
resolved_by:
locked_by:
assigned_vm: planning
assigned_role: data_engineering
code_refs:
  [
    market-tick-data-service/scripts/migrate_cefi_tardis_filename_canonical_2026_07_17.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py,
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
    market-tick-data-service/scripts/migrate_cefi_tardis_filename_canonical_2026_07_17.py,
  ]
---

# CeFi LIGHTER-ZKSYNC systemic wire/canonical dual-write collision

## What I found

Resuming `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`'s sole open todo (apply the 2,962-object safe
residual across EXTENDED-STARKNET/LIGHTER-ZKSYNC/BYBIT-SPOT/COINBASE-FUTURES — all 4 previously declared "zero collision
risk" per that doc's Finding 10 full-range scan from 2026-07-25):

- **EXTENDED-STARKNET**: applied cleanly. 3,168 renamed (grown from the original 704 estimate — expected drift, more
  data accumulated since 2026-07-25), 0 errors, manifest updated.
  `canonical-migration-cefi-late-renames- 20260808-134921`, exit 0.
- **LIGHTER-ZKSYNC**: first full-range attempt (`...-150429`, retried after one prior stall-kill on `...-140152`) hit
  STOP-ON-SURPRISE: 40 genuine collisions, all on exactly 2026-04-17 (all PERPETUAL symbols) — same shape as the doc's
  own established Finding 8/10 precedent (a single transitional day, safe to exclude via date-range split). Split into
  two date-range applies excluding that day:
  - Range 1 (2025-11-01..2026-04-16): `...-153907`, exit 0, 0 renames needed in this sub-range (all LIGHTER-ZKSYNC
    activity postdates 2026-04).
  - Range 2 (2026-04-18..2026-07-24): `...-154345`, hit STOP-ON-SURPRISE again — **this time 11,494 unhandled
    collisions** across 30+ distinct dates: 2026-04-18 (the day right after the excluded one) plus a dense, near-daily
    run from 2026-06-24 through 2026-07-14 at ~156-157 collisions/day. 157 is the apparent full LIGHTER-ZKSYNC PERPETUAL
    symbol count (0G, 2Z, AAPL, AAVE, ADA, AERO, AMD, AMZN, APEX, APT, ARB, ARC, ASML, ASTER, AVAX, AVNT, AXS, AZTEC,
    BCH, BERA, BIRB, BMNR, BNB, BTC, COIN, CRCL, CRO, CRV, DASH, DIA, DOGE, DOLO, DOT, DUSK, DYDX, EDEN, EDGE, EIGEN,
    ENA, ETH, ... — same 40 seen in the first attempt reappear plus many more). Zero mutation (STOP-ON-SURPRISE fires
    before any write). `...-154345`, exit 4.
- **BYBIT-SPOT / COINBASE-FUTURES**: not yet characterized against this finding — proceeding with them separately
  (unaffected by this LIGHTER-ZKSYNC-specific issue per the original zero-collision breakdown).

## Why it matters

This is a **different-shaped population** than every prior collision finding in the parent doc:

- Finding 8/10's precedent (HYPERLIQUID/ASTER/DERIBIT) was a **handful of dates** (6, later a mislabel-driven trickle) —
  bounded, explicable as a one-off writer-transition artifact, safely excludable via date-range split.
- This LIGHTER-ZKSYNC population is **~30+ dates, densely packed across nearly 3 weeks in a row** (2026-06-24 through
  2026-07-14), each day showing essentially the **entire symbol universe** colliding — not a handful of stragglers. That
  shape (whole-universe, sustained, near-daily) is much more consistent with an **ongoing dual-write** (a live/forward
  pipeline now writing canonical-form filenames directly for LIGHTER-ZKSYNC, while something — a parallel backfill, a
  stale writer path, or a re-capture — is ALSO still writing wire-form for the same slots) than with a single discrete
  transition event.
- Continuing to date-split around this would mean excluding ~30 individual dates (or wide contiguous ranges) just to
  force the "safe residual" through — that stops being a safe, bounded, worker-determinable action and starts being
  exactly the kind of open-ended judgment call `data_engineering.md` says to escalate rather than absorb.
- No data was lost or merged incorrectly — the STOP-ON-SURPRISE gate did exactly its job. This is a report of a live,
  ongoing write-path issue, not a required data recovery.

## Recommended decision

1. **Root-cause investigation (bounded, worker-determinable)**: for a sample of the 2026-06-24..2026-07-14 dates, pull
   both the wire-form and canonical-form objects' capture timestamps (`timeCreated` via `gsutil stat` or the manifest's
   own capture columns) to determine whether this is (a) a live pipeline now writing canonical-form going forward while
   a **still-running historical backfill** independently re-captures the same recent days in wire-form (classic race,
   self-resolving once the backfill catches up / is stopped), or (b) two genuinely different, sustained capture paths
   that will keep colliding indefinitely (a real writer misconfiguration needing a code fix, not just a migration
   exclusion).
2. **Do NOT force a rename/merge/delete decision on this population without that investigation** — per the parent doc's
   own established policy (Finding 2/5/8), "two real captures, no way to prefer one without a policy call" defaults to
   leave-both-as-is until characterized.
3. Once characterized: if (a) self-resolving, re-run the LIGHTER-ZKSYNC Range 2 apply after the backfill completes (no
   code change needed, just a later retry). If (b) a genuine writer bug, the fix belongs in `tardis_shared.py`'s
   canonicalization path (same file/pattern as the parent doc's Finding 9 recurrence fix) — scope that as its own
   follow-up once root-caused.
4. The remainder of the resume sequence (BYBIT-SPOT, COINBASE-FUTURES, cron resume, loop-until-dry verifier, 4-surface
   re-proof) is unaffected and proceeds independently — see the parent todo's own progress log.

## Todos

- [ ] [DATA] P2. **Root-cause the LIGHTER-ZKSYNC wire/canonical dual-write collision** — sample 5-10 dates from the
      2026-06-24..2026-07-14 dense run, compare wire-form vs canonical-form object `timeCreated` + row counts via
      `gsutil stat`/manifest columns, determine self-resolving-race vs genuine-writer-bug per the "Recommended decision"
      above. Audit only — do NOT rename/delete/merge anything. (repo: market-tick-data-service)
- [ ] [DATA] P2. **Re-attempt the LIGHTER-ZKSYNC Range 2 (2026-04-18..2026-07-24) `cefi-late-renames` apply** once the
      root-cause todo above determines the population is resolved/stable — pause cron, verify PAUSED, run, verify 0
      unhandled collisions, resume cron, verify ENABLED. (repo: market-tick-data-service, deployment-service)

## Progress Log

- **2026-08-08** — Filed during the `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` resume, slot 18.
  EXTENDED-STARKNET applied clean; LIGHTER-ZKSYNC blocked on this systemic collision after a safe single-day exclusion
  attempt proved insufficient; proceeding to BYBIT-SPOT/COINBASE-FUTURES independently.
