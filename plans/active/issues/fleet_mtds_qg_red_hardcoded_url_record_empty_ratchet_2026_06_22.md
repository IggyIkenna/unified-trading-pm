---
title:
  Fleet MTDS QG red — qg-base ratchet ERRORs pre-existing hardcoded-URL + record_empty-string debt (blocks ALL MTDS
  ships)
created: 2026-06-22
author: ikennaigboaka [slot-autonomous·laptop]
source: [prediction live-producer ship blocked, market-tick-data-service quality-gates.sh]
locked_by: live-defi-rollout
status: open
priority: P1
---

## What I found

`market-tick-data-service/scripts/quality-gates.sh` (Pass-1 + the staging v2 gate) is RED for EVERY committer, on
**foreign pre-existing** violations, after a `base-service.sh` qg-base rollout ~5-6h ago (PM commits 7adfefec9 /
923ee2e3f, 2026-06-22) appears to have tightened two checks to ERROR without baselining existing debt:

1. **`ERROR: 5 hardcoded-URL violation(s)`** — bare literals committed on LDR (oldest 6 days):
   - `market_tick_data_service/live/connectors/*` — `api.curve.finance`, `lite-api.jup.ag`
   - `market_tick_data_service/market_interface/adapters/defi/morpho_adapter.py` — `blue-api.morpho.org`
   - `market_tick_data_service/cli/handlers/{liquidations_handler,jupiter_quote_handler,solana_defi_handler}.py` —
     morpho/jupiter
   - Wants `get_evm_protocol_rest_url(...)` / `get_solana_protocol_url(...)` from `unified_api_contracts.registry`.
2. **`ERROR: 5 file(s) use blank or string-literal record_empty reasons`** (committed on LDR):
   - `market_tick_data_service/cli/handlers/drift_v2_historical_handler.py`
   - `strategy-service/strategy_service/engine/core/{strategy_manifest,gcs_storage_service}.py`
   - `execution-service/execution_service/strategy_instructions/{gcs,manifest}.py`
   - Wants `EmptyConfirmedReason` enum, not string literals.

All are DeFi / Drift / strategy / execution code — **zero prediction**. The MTDS QG runs workspace-wide consumer scans,
so the strategy/execution violations also surface from the MTDS gate. My earlier MTDS quickmerges THIS session
(c487a78/4ef4e02/88c2f0c) passed → the ERROR-enforcement is the new ~5-6h-old change, not the code.

## Why it matters

Blocks **all** MTDS LDR→staging promotion + every agent's MTDS quickmerge fleet-wide (the gate can't go green until the
pre-existing debt is remediated). Directly blocks the prediction live-producer reader fix (ready on
`origin/wip-preserve/prediction-live-reader-fix`, market-tick-data-service) from shipping → prediction live producers
can't emit at full universe.

## Recommended decision (operator / CI-qg lane)

- **Preferred**: BASELINE the pre-existing violations in the qg-base ratchet rollout (a tightening ratchet must baseline
  existing debt, not hard-ERROR it) — or revert the two checks to WARN until the owning lanes remediate. This unblocks
  the fleet immediately.
- OR each owning lane (defi / strategy / execution) remediates (replace bare URLs with the UAC registry getters; replace
  record_empty string reasons with `EmptyConfirmedReason`).
- Then: the prediction reader fix ships from wip-preserve (+ PM `adapter_contract_baseline.yaml` websocket_runner 13→11,
  a legit refactor rebaseline already staged), re-tarball, re-launch the 4 `prediction-live-*` shards.

## Prediction live-producer state (mine, ready)

Reader fix (IS-universe cqg-layout + column mapping condition_id/ticker→connector id + keep-alive) is CODE-COMPLETE +
locally verified (resolves 10 real POLYMARKET ids) on `origin/wip-preserve/prediction-live-reader-fix`. Redis/launcher
fix already shipped (deployment@af4d0f2). The 4 live VMs are deleted (clean) pending the reader fix shipping.
