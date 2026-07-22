---
doc_type: issue
title: >-
  STADER/STAKEWISE/SWELL/MANTLE have no lst_rates_handler.py registry entries at all (verified-but-manual-only claim was
  a probe script, not shipped code); uts-prod-mtds-collect-lst-rates cron separately crash-loops + targets the wrong
  date
summary: >-
  Follow-up to `defi_five_never_captured_venues_fix_2026_07_22.md` and `unified-api-contracts@91b6f094`'s
  DEFI_VENUE_MTDS_ADAPTER_VERIFIED_NOT_YET_SCHEDULED dict. Operator asked to run a 90-day backfill for
  ANKR/STADER/STAKEWISE/SWELL/MANTLE/MAKER; investigating the currently-running mtds-lst-rates-20260722-181845 VM
  backfill (multi-year, real infra) before launching a redundant one revealed the real scope. The VM's 9,300+ line log
  covers lido/rocketpool/coinbase/ankr/idle/marinade/sanctum only -- grep for stader/stakewise/swell/mantle returns zero
  matches. `market-tick-data-service/market_tick_data_service/cli/handlers/ lst_rates_handler.py` has zero registry
  entries for those 4 venues (confirmed via direct grep) -- only ankrETH exists in code, matching the VM's actual
  output. This means the 91b6f094 commit's "verified-accurate read" claim for STADER/STAKEWISE/SWELL/MANTLE came from a
  one-off manual/ad-hoc probe (never shown to be part of any committed handler code), not from shippable logic sitting
  unscheduled -- the earlier framing ("adapter verified, just not scheduled") undersold the remaining work for these 4
  specifically; ANKR and MAKER are closer to schedule-only gaps (ANKR's ratio() read already exists in the handler and
  is running on the VM right now; MAKER's sDAI is already captured via vault_share_price_handler.py, a separate data
  axis -- confirm whether an LST-rate-axis MAKER entry is actually needed or if that was a duplicate framing before
  implementing it here). Operator approved proceeding with full implementation via /autonomous (2026-07-22, chat, this
  session).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-api-contracts]
scope: [engineer]
tags: [defi, lst-rates, stader, stakewise, swell, mantle, ankr, maker, cron-crash-loop, backfill, manifest-freshness]
related:
  - defi_five_never_captured_venues_fix_2026_07_22.md
  - defi_venue_phase_live_definition_contradiction_2026_07_22.md
  - vault_share_price_handler_capture_gap_since_2026_06_22.md
  - plans/active/lst_rate_honest_coverage_2026_07_21.md
created: "2026-07-22"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.5
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
source: [operator-approved-2026-07-22-chat]
---

# What's actually needed (operator-approved, 2026-07-22)

Three ordered steps, per the operator's explicit instruction -- do NOT skip to (3):

## 1. Implement real `lst_rates_handler.py` registry entries for STADER, STAKEWISE, SWELL, MANTLE

Not yet started. For each of the 4 venues, mirror the existing `ankrETH` / `idle` entries' pattern
(`lst_rates_handler.py:152` area + the ratio-fetch dispatch around `:889`):

- Confirm the correct on-chain contract address for each LST token (ETHx/Stader, osETH/StakeWise, swETH/Swell,
  mETH/Mantle) via a primary source (etherscan `creation_transaction_hash` or the protocol's own docs), the same rigor
  `vault_share_price_handler.py`'s GTUSDCP fix comment demonstrates (that fix exists BECAUSE a seed address was accepted
  without this verification -- do not repeat that mistake here).
- Add each to whatever registry dict the handler dispatches from, with the correct `underlying`/decimals/rate-method
  (`getExchangeRate()` for Stader per the 91b6f094 commit message; verify the others independently, do not assume the
  same method name applies to all 4).
- Add unit tests mirroring the existing per-vault test coverage pattern in this handler's test file.
- Do NOT wire these into `DEFI_VENUE_PHASE`/`VENUES_BY_ASSET_GROUP`/`MVP_SCOPE` directly -- that follows the same
  additive, non-breaking pattern already used for `DEFI_VENUE_MTDS_ADAPTER_VERIFIED_NOT_YET_SCHEDULED`; promote only
  once real production capture is confirmed (see `codex/02-data/honest-coverage-model.md`).
- Separately confirm whether a MAKER LST-rate-axis entry is actually distinct from the already-shipped
  `vault_share_price_handler.py` sDAI capture, or whether the original 11-venue survey double-counted the same protocol
  under two axes -- do not implement a duplicate.

## 2. Fix `uts-prod-mtds-collect-lst-rates`'s own crash-loop + wrong-date bug

Not yet started. Two distinct defects, both cited in the 91b6f094 commit message:

- **Crash-loop**: same bug CLASS as the gas-fees fix already shipped (`market-tick-data-service@522185a6`,
  `_bounded_freshness_warmup()` in `_gas_fee_helpers.py`) -- OOM/timeout, likely the same
  `AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC["defi"]=4200s` vs. this job's own (shorter) Cloud Run timeout mismatch. Verify
  via
  `gcloud run jobs executions list --job uts-prod-mtds-collect-lst-rates --region asia-northeast1 --project central-element-323112`
  before assuming it's identical -- confirm the actual failure mode first, then apply the same bounded-warmup/fail-open
  pattern if it matches.
- **Wrong-date targeting**: the cron "targets 'yesterday' relative to run date" per the commit message, rather than an
  explicit historical day -- root-cause this in the handler's date-resolution logic (likely defaults to
  `date.today() - 1` instead of accepting an explicit `--start-date`/`--end-date` the way `vault_share_price_handler.py`
  does via `BatchPayload.date`). Fix so a manual historical re-run (needed for step 3's backfill) actually targets the
  day requested.

## 3. Run the 90+ day backfill

Only after (1) and (2) ship and are QG-green + verified on real infra (per this workspace's "runtime verification" hard
rule -- a code fix isn't done until it's been run and produced a real manifest row). Scope: ANKR, STADER, STAKEWISE,
SWELL, MANTLE (and MAKER only if step 1's duplicate-axis question resolves to "yes, implement it"), back to whatever
start date the reconciled contract-deployment dates support (do not assume 90 days without checking each token's actual
on-chain genesis, per the `lst_rate_honest_coverage_2026_07_21.md` doc's own "Lessons" section on this exact mistake
class). Before launching: check whether `mtds-lst-rates-20260722-181845` (or its successor) is still running and could
absorb these venues once step 1 ships, rather than launching a second, separate VM.

# Why this doc exists separately from `lst_rate_honest_coverage_2026_07_21.md`

That plan is actively being edited by a concurrent session/agent this same evening (confirmed live, large ongoing Phase
0-6 effort) and is scoped to a broader LST honest-coverage initiative already covering
lido/rocketpool/coinbase/ankr/idle/marinade/sanctum. This doc is scoped narrowly to the 4-6 venues from the
five-venues-fix thread specifically, to avoid editing a file another live session owns right now. Whoever picks this up
should check that plan's current state first (`plans/active/lst_rate_honest_coverage_2026_07_21.md`'s own `RESUME POINT`
section) in case the two efforts have since merged or one has superseded the other.

# Deferred work after 2026-07-22

| Item                                                        | State              | Blocked on                                                                                             |
| ----------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------ |
| STADER/STAKEWISE/SWELL/MANTLE handler registry entries      | Not done           | Nobody -- real engineering work, not yet started                                                       |
| uts-prod-mtds-collect-lst-rates crash-loop + wrong-date fix | Not done           | Nobody -- verify actual failure mode first, do not assume it matches gas-fees without checking         |
| MAKER LST-rate-axis duplicate-check                         | Not done           | Nobody -- quick check against vault_share_price_handler.py's existing sDAI capture before implementing |
| 90+ day backfill for the confirmed-in-scope venues          | Cannot be done yet | Items above must ship + verify first                                                                   |

**Recommended next item**: start with the MAKER duplicate-check (cheapest, unblocks scoping the rest), then the
crash-loop root-cause investigation (informs whether the gas-fees fix pattern truly transfers), then the 4 new venue
implementations, then the backfill.
