---
doc_type: issue
title: DERIBIT options_chain af=10,114 (cap=1) — G4 gate blocker
summary:
  Deribit options_chain nearly completely failed in wave-1 backfill. Tardis confirms 426,474 Deribit option symbols with
  options_chain data type available since 2019 — data IS there. Failure was likely transient (preemption/OOM in wave-1).
  Wave-1 reprobe VMs launched 2026-07-03 include DERIBIT light group (options_chain). G4 gate Part 2 blocked until af=0.
status: open
nature: record
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [g4-gate, deribit, options_chain]
related: [plans/archive/2026_07/mvp_backfill_cefi_tick_v10_2026_06_27.md]
created: 2026-07-03
parent_epic: cefi_master
priority: P0
source: [plans/archive/2026_07/mvp_backfill_cefi_tick_v10_2026_06_27.md]
assigned_vm: NA
execution_scope: human
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-15
locked_by: live-defi-rollout
locked_since: 2026-05-21
resolved_by:
---

# DERIBIT `options_chain` af=10,114 (cap=1) — G4 gate blocker

## What I found

The cefi prd manifest (2026-07-03T10:41Z) shows DERIBIT options_chain:

- `attempted_failed` = 10,114
- `captured` = 1

This means the wave-1 Deribit options_chain backfill nearly completely failed. The G4 gate requires "Deribit OPTION
present as options_chain ONLY" — options_chain af>0 blocks G4.

## Root cause investigation

Tardis API confirms: 426,474 Deribit option symbols with `options_chain` data type, available since 2019-03-30. Source
data IS available (not a structural absence like `futures_chain`).

The failure was most likely:

1. Wave-1 Deribit light VMs were preempted (SPOT) and restarted, leaving incomplete coverage
2. Memory/OOM on older SPOT machine types (426K symbols bundled in-memory per date)
3. Rate limiting / transient Tardis API errors during the wave-1 run

## Mitigation

Wave-1 reprobe (2026-07-03T10:56Z) includes DERIBIT in `VENUES`, which will launch:

- `cefi-deribit-<year>-light` VMs (options_chain + derivative_ticker + futures_chain)
- Machine type: `n2-highmem-16` (registry floor for DERIBIT — sufficient memory for bundling)

After reprobe completes, expect options_chain af → 0 (or near-zero with any genuinely missing historic dates pre-2019).

## Resolution gate

Run `measure_honest_coverage.py --asset-group cefi` after reprobe VMs complete. Gate: DERIBIT options_chain
`attempted_failed` = 0.

If options_chain still shows af > 1,000 after reprobe, escalate to operator for investigation into Tardis rate limits or
machine sizing for Deribit bundling.

## Open actions

- [ ] [VERIFY] P0. Verify DERIBIT options_chain af after wave-1 reprobe VMs complete (ETA: 1-3 hours)
- [ ] [MONITOR] P1. If af > 0 after reprobe: check DERIBIT light VM logs for OOM/preemption evidence
- [ ] [OPS] P1. Close issue when DERIBIT options_chain af=0 in prd manifest

## 2026-07-15 corroboration — still unresolved 12 days later, `futures_chain` shows the identical pattern

Corroborating from a `#data-pipeline-alerts` `DP_RUN_MOSTLY_EMPTY` batch (window 2026-07-14 23:50Z–2026-07-15 00:19Z),
triaging cefi/tradfi 100%-failed cells against `market-data-tick-cefi-prd-central-element-323112`:

- **cefi `options_chain`**: 113,595/113,596 attempted_failed (99.999%) — same near-total-failure shape as this doc's
  original 2026-07-03 finding (af=10,114, captured=1), just an order of magnitude larger denominator from 12 more days
  of retry accumulation. **Still open** — no `[x]` on the "Open actions" above; the G4 gate blocker has not been
  cleared. Did not re-verify the reprobe VMs' live status in this pass (read-only manifest-count triage only) — the
  "Open actions" verify/monitor/close todos above remain the right next steps for whoever picks this up.
- **cefi `futures_chain`**: 112,727/112,727 attempted_failed (**exactly** 100.0%, 0 captured) — NOT previously tracked
  under this doc's title (which only names `options_chain`), but this doc's own "Mitigation" section already scopes the
  wave-1 reprobe VMs as `cefi-deribit-<year>-light` bundling **options_chain + derivative_ticker + futures_chain**
  together on the same machine — so a preemption/OOM root cause on that VM class would plausibly hit all three
  data_types, not just options_chain. `futures_chain`'s 100.0% (vs `options_chain`'s 99.999%) is consistent with
  `futures_chain` never having even the 1 lucky capture options_chain got. **Do not conflate this with**
  `bybit_futures_chain_write_shape_2026_07_13.md` — that doc is about BYBIT `futures_chain` rows being written to the
  WRONG PATH SHAPE (still `capture_status=captured`, just non-canonical hive layout), a completely different failure
  mode from DERIBIT `futures_chain` never capturing at all. Recommend the reprobe-verification todo above be widened to
  check `futures_chain` af alongside `options_chain` af before this issue is closed.
- Not independently re-diagnosed (root cause + fix path is exactly what this doc already describes) — filed as a
  corroborating note per the triage task's instruction to annotate rather than duplicate.
