---
doc_type: plan
title:
  DeFi satellite AO batch 12 — item-level extraction from onchain_staking_apy_bps_single_day_annualization_noise
  (2026-08-09)
summary: >-
  Twelfth AO-dispatch batch for the defi tranche (`parent_epic: features_and_ml_master`, distinct from batch9-11's
  `defi_master` grouping — see `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §2 on
  grouping by parent_epic, not asset_group). Extracts the single bounded, worker-determinable item from
  `issues/onchain_staking_apy_bps_single_day_annualization_noise_2026_08_09.md`: confirm whether strategy-service's
  `CARRY_STAKED_BASIS` archetype consumes the features-onchain `staking_apy_bps` field raw or through an existing
  smoothing/clamping layer. This is a bounded grep-and-read diagnostic (not the doc's second item, which is an explicit
  quant-math methodology design call and stays `assigned_vm: NA` on the source doc). Conflict-checked against
  `cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md` (the plan that discovered and filed the source issue, 0
  open todos remaining, no overlapping claim).
status: complete # (was: active) 2026-08-09 -- sole todo done, archived alongside its finalize plan
nature: process
asset_group: [defi]
stage: [strategy]
repos: [strategy-service]
scope: [engineer]
tags: [defi, ao-dispatch, satellite-extraction, batch-12, onchain, lst-yields, staking-apy, carry-staked-basis]
related:
  [
    /plans/active/issues/onchain_staking_apy_bps_single_day_annualization_noise_2026_08_09.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md,
    /plans/active/defi_satellite_ao_dispatch_batch12_2026_08_09_finalize.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: features_and_ml_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.18
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/onchain_staking_apy_bps_single_day_annualization_noise_2026_08_09.md,
    features-service/features_service/onchain/engine/lst_features.py,
    strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py,
  ]
source: >-
  Round-9 combined RECLASSIFY + satellite-extraction sweep, 2026-08-09 (defi tranche) — the source doc's todo 1 ([DIAG]
  P2) is a bounded, worker-determinable grep-and-read task (confirm raw-vs-smoothed consumption of `staking_apy_bps` by
  `CARRY_STAKED_BASIS`), independently actionable regardless of the source doc's second item (a genuine quant-math
  design call, stays NA). Conflict-check clear: the only other corpus reference to the source doc is
  `cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md`'s citation, which is the source doc's OWN origin (the
  Phase-A run that filed it), now at 0 open todos — no competing claim.
assigned_role: quant_dev
effort: low
sequential: false
drift_direction: advance-code
---

# DeFi satellite AO batch 12 — 2026-08-09

> **✅ ARCHIVED 2026-08-09 — sole todo done.** RAW-consumption verdict recorded; source doc's second todo retagged
> P2→P1; reconciled + archived by `defi_satellite_ao_dispatch_batch12_2026_08_09_finalize.md`.

Single-item extraction from a targeted end-to-end read of
`issues/onchain_staking_apy_bps_single_day_annualization_noise_2026_08_09.md` during the round-9 RECLASSIFY +
satellite-extraction sweep. Cleared the shared conflict-check
([`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`](/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md)
§3) — the only other reference to the source doc anywhere in the corpus is
`cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md`'s citation (that plan's own origin filing, now 0 open todos),
not a duplicate claim.

## Todos

- [x] ✅ [DIAG] P2. **Confirm whether `CARRY_STAKED_BASIS` (strategy-service) consumes `staking_apy_bps` raw or through
      a smoothing/clamping layer already.** Read the archetype's engine (`carry_and_yield/staked_basis.py` and whichever
      feature-read path pulls `lst_yields.staking_apy_bps`) to determine: (a) if a rolling window / sign / magnitude
      sanity clamp already exists, downgrade the source doc's finding to a cosmetic-only note (no further action
      needed); (b) if the raw single-day value is consumed directly, retag the source doc's second todo ([DESIGN] P2,
      the annualization-noise fix) to P1 — a wobble like the one measured (5/60 rows negative, -184 to -3453 bps; 2/60
      rows exceeding +5000 bps off single-day moves under 0.2%) could cause a spurious defensive-mode flip. Repo:
      strategy-service. Source: `issues/onchain_staking_apy_bps_single_day_annualization_noise_2026_08_09.md` todo 1
      (verbatim). **Done when**: the raw-vs-smoothed verdict is recorded with a file:line citation, and the source doc's
      checkbox + (if applicable) its second todo's priority are updated to match.

## Progress Log

- **2026-08-09** (round-9 combined RECLASSIFY + satellite-extraction sweep, defi tranche): drafted, `status: active`, no
  work started — extraction only. Source doc's todo 1 checkbox replaced with a citation pointer to this doc in the same
  commit.
- **2026-08-09** (slot-11 quant_dev worker): **Verdict — RAW, no smoothing/clamp.**
  `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py:440` (`_preflight`) reads
  `features.get("staking_apy_bps")` and feeds it straight into `net_carry = f * (staking_apy + funding_apy) - fees` at
  line 459 with no rolling window, no sign/magnitude clamp anywhere in the file (grepped for
  `clamp|smooth|rolling|ewma|moving_avg|window` — only unrelated hits at `venue haircut`-clamp and
  `sharpe_window_n=None`). Upstream, `features-service/features_service/onchain/engine/lst_features.py:84-91`
  (`_annualise_and_stamp`) computes `staking_apy_bps` as the raw single-day `(exchange_rate/prev_rate)**365 - 1` with no
  smoothing applied before the strategy consumes it. Per the todo's branch (b): retagged the source doc's second todo
  ([DESIGN]) from P2 → P1 in
  `/plans/active/issues/onchain_staking_apy_bps_single_day_annualization_noise_2026_08_09.md`.
