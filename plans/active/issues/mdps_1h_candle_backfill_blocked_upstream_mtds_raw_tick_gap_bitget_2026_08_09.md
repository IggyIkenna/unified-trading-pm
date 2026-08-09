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
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md,
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

## BITGET-SPOT determination (2026-08-09, slot 18)

**Verdict: (b) — intentional pre-onboarding absence, NOT a genuine MTDS capture gap. No backfill warranted for
BITGET-SPOT in the 2026-04-14..04-30 window.**

Evidence (converging, three independent layers, all post-dating the audited window):

1. **Venue not even mapped yet.** BITGET's Tardis venue mapping (the prerequisite for MTDS to resolve any Bitget symbol
   at all) was added `market-tick-data-service@9ff43846` (2026-05-01 19:13 UTC+1) — "Tier-3" onboarding wave, per
   `tests/unit/test_mtds_venue_coverage.py`'s own comment ("Tier-3 (2026-05-01: BITFINEX-SPOT/FUTURES, BITGET-SPOT,
   BITGET-FUTURES, KRAKEN-SPOT, KRAKEN-FUTURES)"). This is AFTER the entire audited window (2026-04-14..04-30) ends.
2. **Venue not in the MVP capture universe until 6+ weeks after the window.** `unified-api-contracts`'s `mvp_scope.py`
   module (the capture-gating SSOT; `is_in_mvp_capture_universe` is what
   `market_tick_data_service/engine/ cefi_catalog_reader.py` actually consults to decide what to download) didn't exist
   before 2026-06-08, and BITGET-SPOT/BITGET-FUTURES were added to its `venues` frozenset only in
   `unified-api-contracts@54325576` (2026-06-23, MVP_SCOPE v7→v8, commit msg: "Add the 8 venues (...BITGET-*...) to the
   MVP rule venues set (were absent -> mvp=0)"). Per `plans/active/issues/cefi_universe_capture_rule_2026_06_23.md`,
   this 2026-06-23 operator ruling is what SUPERSEDES the pre-existing informal "curated top-100 guess" capture universe
   — i.e. there was no earlier formal mechanism that could have included BITGET-SPOT before this date either.
3. **Live transport wired even later.** `bitget_spot_ws.py`'s `WSFeedConnector` was first registered in
   `market-tick-data-service@6bf4f616` (2026-07-07, "BITGET-SPOT + BITGET-FUTURES WSFeedConnectors (gap-003)").
4. **Manifest shape matches "never in scope," not "attempted and failed."** The audit's own finding (§ "What I found"
   above) is that BITGET-SPOT has zero rows of ANY `capture_status` — not even `expected_unattempted`, which the WRITER
   materializes for any cell it considers in-scope. A truly in-scope-but-unattempted cell would show
   `expected_unattempted` (as BITGET-FUTURES trades correctly does for its own 04-14..04-19 gap); BITGET-SPOT's total
   absence from the manifest denominator is the expected, correct signature of a venue that was outside the capture
   universe entirely at the time — not a bug.

This does **not** resolve the separate BITGET-FUTURES `trades` 2026-04-14..04-19 question (todo 2 below) — that cell
DOES show `expected_unattempted` (i.e. was already in-scope, just not yet attempted), which is a materially different
manifest signature and needs its own check against when BITGET-FUTURES `trades` specifically entered the capture
schedule, separate from BITGET-SPOT's venue-mapping/MVP-scope timeline above.

## Todo

- [x] ✅ [DATA] P2. **Determine whether BITGET-SPOT's total 2026-04-14..04-30 raw-tick absence is a genuine MTDS capture
      gap or an intentional pre-onboarding absence** (check MTDS venue-onboarding history / config for when BITGET-SPOT
      was added to the CeFi capture scope). Repo: market-tick-data-service. — RESOLVED (b): intentional pre-onboarding
      absence, see "BITGET-SPOT determination" above. No MTDS backfill needed for BITGET-SPOT in this window; the
      manifest's total absence is honest-absence, not a defect.
- [ ] [DATA] P2. **BITGET-FUTURES trades 2026-04-14..04-19 only** (BITGET-SPOT portion resolved above — no action):
      determine whether this `expected_unattempted` gap is a genuine backfillable capture gap, and if so run the MTDS
      raw-tick backfill for BITGET-FUTURES trades 2026-04-14..04-19 using the same MTDS backfill tooling this workspace
      already uses for CeFi raw-tick catch-up (mirrors `launch-mtds-cefi-backfill.sh` per
      `features_service_e2e_pipeline_test_2026_05_26.md` Phase 0.5 provenance). Repo: market-tick-data-service.
- [ ] [DATA] P3. **Once the BITGET-FUTURES raw ticks land, re-run the scoped MDPS candle backfill** for the
      BITGET-FUTURES 04-14..04-19 residual (same pattern as this session's `mdps-backfill-cefi-20260809-123352`) to
      close the remaining candle gap. BITGET-SPOT candle backfill is NOT needed (see resolved todo above — the
      underlying raw ticks were never meant to exist). Repo: market-data-processing-service.
