---
doc_type: issue
title: "DP-FETCH-009 cefi/liquidations candidate breakdown unresolved after ASTER hypothesis"
summary: >-
  CRITICAL DP_RUN_MOSTLY_EMPTY / DP-FETCH-009 for cefi/liquidations: 160105 attempted_failed
  cells of 1852684 attempted (8.6%), including 720 fresh cells in the last day. The initial
  ASTER batch-filter hypothesis is falsified by the authoritative UAC registry and an existing
  MTDS regression test; the failing venue/source/error breakdown is not present in the escalation.
status: open
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [data-pipeline, dp-fetch-009, dp-run-mostly-empty, cefi, liquidations, aster, attempted-failed]
related:
  - /codex/05-infrastructure/data-pipeline-alerts.md
  - /plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md
  - /plans/active/issues/dp_fetch_009_cefi_liquidations_raw_contract_overwritten_2026_08_20.md
parent_epic: observability_master
source:
  - DP-FETCH-009 escalation agt-9d9a98 (2026-08-20)
assigned_vm: planning # FIXED 2026-08-21 (ag-closeout-audit cefi Phase 3): was stale legacy `vm-cross-cutting` (pre-2026-06-27 multi-VM value) — regen_backlog_from_plan.py's single-VM ingestion only matches `assigned_vm==vm_id` ("planning") or absent, so this doc's open todo was never actually reaching the AO backlog despite `execution_scope: orchestrator-agent`.
created: 2026-08-20
priority: P1
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
assigned_role: data_pipeline_failure
drift_direction: advance-code
depends_on: []
context_scope:
  - /codex/05-infrastructure/data-pipeline-alerts.md
  - /codex/02-data/availability-manifest-and-data-status.md
  - market-tick-data-service/market_tick_data_service/cli/handlers/_onchain_perp_batch_live_only.py
  - market-tick-data-service/market_tick_data_service/cli/handlers/onchain_perp_batch_handler.py
---

# DP-FETCH-009 cefi/liquidations candidate breakdown unresolved after ASTER hypothesis

## What I found

The fresh escalation reports asset_group=cefi and data_type=liquidations, with 160105
attempted_failed cells out of 1852684 attempted (8.6%), including 720 fresh cells in the
last one-day window. The initial ASTER hypothesis is falsified: UAC's authoritative
_NO_BATCH_SOURCE_BY_VENUE["ASTER"] includes liquidations, and the existing MTDS
test_onchain_perp_batch_handler regression test verifies that ASTER liquidations are filtered
before shard dispatch. The escalation provides no candidate venue, source, pipeline-mode, or
error-reason breakdown, so the actual failing producer remains unresolved.

## Why it matters

attempted_failed is an honest retryable state. Declaring ASTER as the fix would be misleading
and could leave the real 160105-row population untouched. A bounded candidate breakdown is
needed before changing a producer, source capability, or manifest classification.

## Recommended decision

Obtain a bounded breakdown of the alert population by venue, source, pipeline mode, error_reason,
attempted timestamp, and run/VM identifier. Diagnose the exact producer from that evidence, then
fix and test it in the owning repository. Do not add a redundant ASTER local filter or fabricate
empty/captured rows; retain existing historical failures for separate reclassification policy.

## Todos

- [ ] [DIAGNOSE] P1. **NARROWED 2026-08-20 (/plan-reconcile F-CEFI-4)** — the venue/error breakdown was already
      obtained by a sibling doc filed the same day against the SAME escalation (`agt-9d9a98`):
      `/plans/active/issues/dp_fetch_009_cefi_liquidations_raw_contract_overwritten_2026_08_20.md`. It found 1,632
      schema-contract violations (Binance-Futures 720, Bybit 509, Bitget-Futures 395, Bitfinex-Futures 8) and shipped
      a fix at `unified-api-contracts@cff7a237`. Separately, 810 Tardis HTTP 403 code=274 concurrent-IP-lock failures
      are a distinct population that sibling doc explicitly does NOT cover ("do not mark those failures as resolved
      by the registry fix"). **This todo's remaining true scope is only the Tardis code-274 lockout slice** — the
      schema-contract diagnosis is done, do not re-derive it.

## Progress Log

- **ag-closeout-audit 2026-08-21 (cefi tranche, Phase 3 sweep)**: found this doc mis-classified "orphaned" by the
  Phase 1 pass — re-verified it was actually never AO-reachable at all: `assigned_vm: vm-cross-cutting` is a stale
  legacy per-VM value from the pre-2026-06-27 multi-VM architecture that the current single-VM
  `regen_backlog_from_plan.py` ingestion path does not match. Fixed to `assigned_vm: planning` (+ added the missing
  `assigned_role: data_pipeline_failure`, mirroring its sibling doc) so the remaining Tardis code-274 lockout
  investigation todo actually reaches the backlog. No new batch doc needed — this is a direct un-orphaning.
- 2026-08-20: Falsified the initial ASTER omission hypothesis against the authoritative UAC
  registry and the existing MTDS ASTER batch-filter regression test. No code fix shipped; the
  alert's candidate breakdown is required to continue safely.
- **context-scout 2026-08-20**: reviewed context_scope (already populated at authoring time with 2 codex SSOTs +
  2 real source paths) — no changes needed, left at 4 entries.
