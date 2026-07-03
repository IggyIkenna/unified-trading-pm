---
doc_type: issue
title: DERIBIT options_chain af=10,114 (cap=1) — G4 gate blocker
summary: Deribit options_chain nearly completely failed in wave-1 backfill. Tardis confirms
  426,474 Deribit option symbols with options_chain data type available since 2019 — data IS
  there. Failure was likely transient (preemption/OOM in wave-1). Wave-1 reprobe VMs launched
  2026-07-03 include DERIBIT light group (options_chain). G4 gate Part 2 blocked until af=0.
status: open
nature: data-correctness
asset_group: [cefi]
stage: [backfill]
repos: [market-tick-data-service]
scope: [engineer]
tags: [g4-gate, deribit, options_chain]
related: [plans/active/mvp_backfill_cefi_tick_v10_2026_06_27.md]
created: 2026-07-03
parent_epic: mvp_backfill_cefi_tick_v10
priority: P0
source: [plans/active/mvp_backfill_cefi_tick_v10_2026_06_27.md]
assigned_vm: NA
execution_scope: human
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-03
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# DERIBIT `options_chain` af=10,114 (cap=1) — G4 gate blocker

## What I found

The cefi prd manifest (2026-07-03T10:41Z) shows DERIBIT options_chain:
- `attempted_failed` = 10,114
- `captured` = 1

This means the wave-1 Deribit options_chain backfill nearly completely failed. The G4 gate
requires "Deribit OPTION present as options_chain ONLY" — options_chain af>0 blocks G4.

## Root cause investigation

Tardis API confirms: 426,474 Deribit option symbols with `options_chain` data type, available
since 2019-03-30. Source data IS available (not a structural absence like `futures_chain`).

The failure was most likely:
1. Wave-1 Deribit light VMs were preempted (SPOT) and restarted, leaving incomplete coverage
2. Memory/OOM on older SPOT machine types (426K symbols bundled in-memory per date)
3. Rate limiting / transient Tardis API errors during the wave-1 run

## Mitigation

Wave-1 reprobe (2026-07-03T10:56Z) includes DERIBIT in `VENUES`, which will launch:
- `cefi-deribit-<year>-light` VMs (options_chain + derivative_ticker + futures_chain)
- Machine type: `n2-highmem-16` (registry floor for DERIBIT — sufficient memory for bundling)

After reprobe completes, expect options_chain af → 0 (or near-zero with any genuinely
missing historic dates pre-2019).

## Resolution gate

Run `measure_honest_coverage.py --asset-group cefi` after reprobe VMs complete.
Gate: DERIBIT options_chain `attempted_failed` = 0.

If options_chain still shows af > 1,000 after reprobe, escalate to operator for investigation
into Tardis rate limits or machine sizing for Deribit bundling.

## Open actions

- [ ] [VERIFY] P0. Verify DERIBIT options_chain af after wave-1 reprobe VMs complete (ETA: 1-3 hours)
- [ ] [MONITOR] P1. If af > 0 after reprobe: check DERIBIT light VM logs for OOM/preemption evidence
- [ ] [OPS] P1. Close issue when DERIBIT options_chain af=0 in prd manifest
