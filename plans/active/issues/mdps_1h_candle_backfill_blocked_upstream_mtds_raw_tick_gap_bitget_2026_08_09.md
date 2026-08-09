---
doc_type: issue
title:
  "MDPS 1h/4h/24h candle backfill for BITGET-FUTURES/BITGET-SPOT 2026-04-14..04-30 is only PARTIALLY closable —
  BITGET-SPOT has ZERO raw MTDS ticks in the entire window, and BITGET-FUTURES trades are expected_unattempted for
  2026-04-14..04-19"
summary:
  "Auditing the named MDPS gap from cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md todo 2 (v8 manifest,
  market-data-tick-cefi-prd bucket, filtered date=2026-04-14..2026-04-30): confirmed CeFi 1h candles + BITGET-SPOT
  4h/24h candles were genuinely missing for the whole window (only 2026-04-14 had any candle rows at all, 2026-04-15..
  04-30 zero rows). Root-cause check against the upstream market-tick-data-service (MTDS) raw-tick manifest (same
  bucket, service_name=market-tick-data-service, data_type=trades) found the candle gap is NOT purely an MDPS
  reprocessing gap: BITGET-SPOT has literally ZERO raw-tick manifest rows (not even expected_unattempted) for
  venue=BITGET-SPOT across the entire 2026-04-14..04-30 window and every data_type, and BITGET-FUTURES trades are
  capture_status=expected_unattempted (MTDS never attempted capture) for 2026-04-14..04-19 specifically, only becoming
  captured from 2026-04-20 onward. MDPS cannot derive candles from raw ticks that were never captured. Dispatched the
  MDPS-side portion that IS closable (BITGET-FUTURES 1h/4h/24h/etc, 2026-04-20..04-30, real raw ticks exist) via a
  scoped SPOT VM (market-data-processing-service repo, deployment-service launcher) — see the parent todo's flip for
  evidence. This issue tracks the REMAINING upstream MTDS gap that MDPS cannot close on its own: BITGET-FUTURES
  2026-04-14..04-19 (6 days) and ALL of BITGET-SPOT 2026-04-14..04-30 (17 days) need a market-tick-data-service (MTDS)
  raw-tick capture/backfill decision before MDPS candles can ever be derived for that portion."
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service]
scope: [engineer]
tags: [manifest, mtds, mdps, cefi, bitget, raw-tick-gap, honest-absence, backfill]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md,
    /plans/active/features_service_e2e_pipeline_test_2026_05_26.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-08-09
last_updated: 2026-08-09
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: cross_cutting_satellite_ao_dispatch_batch5-77d480c19d08 (slot 22, 2026-08-09 audit)
---

# MDPS candle backfill for BITGET 2026-04-14..04-30 is upstream-blocked (MTDS raw-tick gap)

## What I found

Audited
`read_availability_index_safe(market-data-tick-cefi-prd-central-element-323112, filters=[date 2026-04-14.. 2026-04-30])`,
split by `service_name`:

**MDPS side (candles) — confirmed genuine, now partly fixed:**

- BITGET-FUTURES 1h: only 2026-04-14 had rows (27); 2026-04-15..04-30 (16 days) had ZERO rows.
- BITGET-SPOT 1h: only 2026-04-14 had rows (17); 2026-04-15..04-30 (16 days) had ZERO rows.
- BITGET-SPOT 4h: only 2026-04-14 had rows (17); 2026-04-15..04-30 (16 days) had ZERO rows.
- BITGET-SPOT 24h: ZERO rows for all 17 days.

**MTDS side (raw ticks) — root cause of most of the above:**

- BITGET-FUTURES `data_type=trades`: `expected_unattempted` for 2026-04-14..04-19 (48 expected/day, 0 attempted);
  `captured` (371-391 rows/day) from 2026-04-20 onward. `derivative_ticker` WAS captured throughout — only `trades`
  (MDPS's candle source data_type) has the gap.
- BITGET-SPOT: **zero rows of ANY data_type** under `service_name=market-tick-data-service` for the entire
  2026-04-14..04-30 window. Not `expected_unattempted`, not `attempted_failed` — the manifest has no record of
  BITGET-SPOT being in scope for this venue during this window at all.

MDPS cannot derive a candle from a raw tick that was never captured — this is not an MDPS reprocessing bug, it's an
upstream input gap.

## What was closed (this session, MDPS-scope)

Launched `mdps-backfill-cefi-20260809-123352` (SPOT, e2-highmem-8, asia-northeast1-c) via
`deployment-service/scripts/vm/launch-mdps-backfill-vm.sh --data-types trades --venues "BITGET-FUTURES" cefi 2026-04-20 2026-04-30 full`
— scoped exactly to the window where raw BITGET-FUTURES trades ticks genuinely exist. Writes to the prod
`market-data-tick-cefi-prd-central-element-323112` bucket. See the parent todo's checkbox flip in
`cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md` for the run outcome/evidence.

Direct in-process invocation on the shared planning VM was abandoned after a single date (`2026-04-20`, BITGET-FUTURES,
`trades`, `1h` only) reached **15.1 GB RSS within ~30 seconds** before being SIGTERM'd — this is the same memory-blowup
shape as the 2026-07-27/07-31/08-01 incidents (`RULES.md` § 1's memory-bounding guardrail); the `cefi_wire_bridge`
module reloads the full 431,540-row instruments catalogue multiple times per date without caching, which is a plausible
contributor and may be worth its own investigation (not scoped here — flagging only).

## Why it matters

The source plan (`features_service_e2e_pipeline_test_2026_05_26.md`) needs contiguous ≥14-day 1h-base candle history for
`delta_one` to derive 4h/24h higher-timeframe features. Even after this session's BITGET-FUTURES fix, BITGET-SPOT still
has a 17-day gap and BITGET-FUTURES still has a 6-day gap (04-14..04-19) — neither closable without an MTDS raw tick
capture decision first.

## Recommended decision

Whoever owns market-tick-data-service scope should determine, for BITGET-SPOT and BITGET-FUTURES 2026-04-14..04-19: (a)
was this venue/window ever meant to be in MTDS's capture scope (a genuine historical backfill gap), or (b) is
BITGET-SPOT's total absence in this window an intentional venue-onboarding-date fact (BITGET-SPOT wasn't yet in-scope
before some later date)? If (a), MTDS raw-tick backfill for this scope, then re-run the MDPS candle backfill for the
newly-available days. If (b), the MDPS gap is honest-absence, not a defect — no action needed beyond documenting it.

## Todo

- [ ] [DATA] P2. **Determine whether BITGET-SPOT's total 2026-04-14..04-30 raw-tick absence is a genuine MTDS capture
      gap or an intentional pre-onboarding absence** (check MTDS venue-onboarding history / config for when BITGET-SPOT
      was added to the CeFi capture scope). Repo: market-tick-data-service.
- [ ] [DATA] P2. **If a genuine gap: run the MTDS raw-tick backfill for BITGET-SPOT (all data_types) 2026-04-14.. 04-30
      and BITGET-FUTURES trades 2026-04-14..04-19** using the same MTDS backfill tooling this workspace already uses for
      CeFi raw-tick catch-up (mirrors `launch-mtds-cefi-backfill.sh` per
      `features_service_e2e_pipeline_test_2026_05_26.md` Phase 0.5 provenance). Repo: market-tick-data-service.
- [ ] [DATA] P3. **Once the raw ticks land, re-run the scoped MDPS candle backfill** (same pattern as this session's
      `mdps-backfill-cefi-20260809-123352`:
      `launch-mdps-backfill-vm.sh --data-types trades --venues "BITGET-SPOT"     cefi 2026-04-14 2026-04-30 full` + the
      BITGET-FUTURES 04-14..04-19 residual) to close the remaining candle gap. Repo: market-data-processing-service.
