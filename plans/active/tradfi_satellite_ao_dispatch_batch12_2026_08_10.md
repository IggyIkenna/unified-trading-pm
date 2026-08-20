---
doc_type: plan
title:
  TradFi satellite AO batch 12 — the one doc slot-25's 52-candidate snapshot missed (2026-08-10, sharded re-run,
  dispatch agt-a19d1f)
summary: >-
  Satellite-batch extraction mirroring /ag-closeout-audit's pattern. This is the THIRD same-day tradfi tranche dispatch
  (slot 26 all-mode → slot 25 sharded, both already parked in `ag_closeout_audit_tradfi_parked_2026_08_10.md`; this is
  slot-22/dispatch agt-a19d1f). Rather than re-running the full 52-agent Phase 1 fan-out slot-25 already completed 4
  hours prior (near-certain duplicate given almost nothing in the corpus changed in that window), this pass re-ran Phase
  0.3's candidate generator fresh (55 candidates now vs. 52 then — the delta is 3 newly-tagged/newly-created docs, not a
  re-scope) and diffed it against every one of the 17 currently-active tradfi covering docs' actual cited-doc text (not
  just batch11's summary claim) to find anything genuinely uncited anywhere. Of 5 "never-cited" hits, 2 were already
  fully triaged (in `ag_closeout_audit_tradfi_parked_2026_08_10.md` findings 1+4), 1 is correctly out-of-scope
  (`dp_cron_did_not_fire_false_positive_burst_2026_08_10.md`, 5-tranche cross-cutting doc owned by `infra` per
  `parent_epic: infrastructure_master`), 1 is operator-gated and already independently triaged by the CONCURRENT
  cross-cutting tranche's own audit 10 minutes after slot-25's snapshot
  (`databento_ice_opra_subscription_ask_2026_08_09.md`, retagged `cross-cutting`→`tradfi` at
  `unified-trading-pm@ca9dd1cdac`, i.e. genuinely didn't exist as a tradfi candidate at slot-25's snapshot time — not a
  miss). The 5th, extracted below, is a genuine gap: a real, open, conflict-clear, bounded P2/P3 code-fix doc that
  existed as `asset_group: [tradfi]` since 2026-08-09 (well before any of today's 3 passes) and simply never appeared in
  any covering doc's text.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, satellite-extraction, batch-12, orphan-extraction, discovery-floor]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/cboe_venue_level_discovery_floor_blocks_yahoo_treasury_pre_2020_2026_08_09.md,
    /plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch11_2026_08_10.md,
    /plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch11_2026_08_10_finalize.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_tradfi_parked_2026_08_10_r2.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-17"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/issues/cboe_venue_level_discovery_floor_blocks_yahoo_treasury_pre_2020_2026_08_09.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/__init__.py,
  ]
depends_on: []
source: >-
  /ag-closeout-audit tradfi-tranche pass (2026-08-10, dispatch agt-a19d1f, slot 22) — the 3rd same-day tradfi tranche
  dispatch. Ran `generate_ag_closeout_audit_candidates.py --tranche tradfi` fresh (55 candidates, 17 covering docs incl.
  batch11+finalize) rather than repeating slot-25's already-thorough 52-agent Phase 1 fan-out from 4 hours prior; diffed
  the fresh never-cited set against slot-25's batch11 Deferred/Flagged text (read in full) and the existing same-day
  parked-findings doc to isolate genuinely new gaps. Only this one doc survived that diff as a real, unaddressed,
  AO-eligible orphan. Full methodology + the other 4 never-cited docs' disposition recorded in
  `ag_closeout_audit_tradfi_parked_2026_08_10.md` (appended this pass).
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
---

# TradFi satellite AO batch 12 — 2026-08-10 (residual gap, sharded re-run)

**status: active — reviewed and dispatched (see frontmatter).** CORRECTED 2026-08-16 (plan_reconciler, tranche=tradfi,
agt-a74a6a): this body banner still read `status: draft`, contradicting the frontmatter's `status: active` and the
fact that todo 1 already shipped (`UAC@a65c2fa9`, `MTDS@fe000178`) — the operator review this banner describes has
already happened. Only 1 source doc, 2 todos — deliberately thin; this batch exists to close a specific, verified gap,
not to re-litigate slot-25's already-thorough batch11.

## Todos

- [x] [DATA] P2. **Make the CBOE venue-availability discovery-floor check data-type-aware, so the Yahoo Treasury-INDEX
      series' real pre-2020 history stops being silently skipped.** `is_venue_available(venue, date)`
      (`market_tick_data_service/engine/orchestrator/__init__.py:410` — confirmed live on `origin/live-defi-rollout`
      this pass, still the 2-arg `(venue: str, date: str) -> bool` signature described in the source doc, i.e. NOT yet
      fixed) checks a single per-venue floor date with no data_type dimension. CBOE is a mixed venue: the registered
      floor (~2020-06-01) is correct for its Databento VX-futures leg, but wrong for its separate Yahoo-routed
      `ohlcv_24h` Treasury yield-curve INDEX leg, which has real fetchable history back to 2000-01-03 (4 of 5 tenors) /
      2018-08-13 (US2Y). Every pre-floor CBOE `ohlcv_24h` date is currently classified honest-absence
      (`EXPECTED_PRE_SOURCE_COVERAGE_START`) for the wrong reason — structurally correct signal, wrong floor. Add an
      optional `data_types` parameter to `is_venue_available()`; when venue=CBOE and the requested data_types are a
      subset of the existing `_CBOE_YAHOO_TREASURY_DATA_TYPES` set, resolve against a Yahoo-specific floor (2000-01-03,
      or a per-tenor table) instead of the registered `VenueMapping` floor — mirror the same discrimination pattern
      `_CBOE_YAHOO_ONLY_DATA_TYPES` already uses in `tick_data_handler.py::_resolve_source` (shipped
      `market-tick-data-service@af2c53ce`). Thread `data_types` through `_build_active_venues_for_date()` and its
      callers. Add regression tests: (a) CBOE Databento VX-futures dates before ~2020-06 still correctly skip as
      honest-absence: (b) CBOE Yahoo `ohlcv_24h` dates 2000-01-03 through ~2020-06 now attempt a real fetch instead of
      auto-skipping. Repo: market-tick-data-service. Source:
      `issues/cboe_venue_level_discovery_floor_blocks_yahoo_treasury_pre_2020_2026_08_09.md` todo 1. ✅ `UAC@a65c2fa9` —
      `_data_type_floor_overrides` field in `VenueMapping`; `MTDS@fe000178` — `data_type` param on
      `is_venue_available()` wrapper.
- [ ] [DATA] P3. **Relaunch the CBOE Treasury-INDEX backfill for the newly-unblocked 2018-2020-06 window.** Once the
      floor fix above ships, relaunch `launch-tradfi-bf-cboe-indices-ohlcv-24h.sh` with `--start-floor 2018-01-01` and
      verify real `captured` rows land in the manifest for all 4 pre-2018 tenors (US3M/US5Y/US10Y/US30Y) from 2018-01-01
      onward, and US2Y back to 2018-08-13. Capped at 2018 per operator decision 2026-08-10 — real Yahoo history exists
      back to 2000-01-03 for 4 of 5 tenors, but the operator explicitly does not want that chased; 2018 onward is
      sufficient. Repo: market-tick-data-service / deployment-service. Source:
      `issues/cboe_venue_level_discovery_floor_blocks_yahoo_treasury_pre_2020_2026_08_09.md` todo 2. Sequenced after
      todo 1 above within this same-priority pair only by logical dependency (the launcher would no-op without the fix)
      — not marking `sequential: true` at the plan level since no other todo exists to race. Done when: a live manifest
      query (venue=CBOE, data_type=ohlcv_24h, date<2020-06-01) shows `captured` rows with populated `instrument_id` for
      all 4 tenors' history from 2018-01-01 onward.

## Conflict-check (per `ao-dispatch-batch-naming-and-conflict-check.md` §3)

Grepped `is_venue_available`, `cboe`, and the source doc's basename against:
`tradfi_consolidated_closeout_2026_07_18.md`, all 4 forked children (`tradfi_manifest_content_recovery_completion`,
`tradfi_backfill_throughput_followups`, `tradfi_phase_d_terminal_gate`, `tradfi_registry_coverage_and_ao_readiness` +
finalize), and every active satellite batch (6/7/8/9/11 + finalizes). Zero hits on this specific fix — the only other
CBOE-related open work in flight is `issues/mdps_cboe_vx_futures_chain_grain_excluded_from_ohlcv_15m_24h_2026_08_09.md`
(batch9's Deferred, MDPS aggregation-grain policy question, a completely different subsystem/file from MTDS's
venue-availability preflight gate) — no overlap.

## Not extracted this batch — the other 4 "never-cited" hits, and why

- `issues/plan_reconciler_findings_2026_08_06.md` — already triaged (`ag_closeout_audit_tradfi_parked_2026_08_10.md`
  finding 1: `archivable_now`-by-content but `locked_by`-blocked, `[OPERATOR]` todo already filed there). Not re-parked.
- `issues/plan_reconciler_findings_tradfi_2026_08_09.md` — already triaged (same parked doc, finding 4: stalled/
  abandoned `/plan-reconcile` run, `[OPERATOR]` todo already filed there). Not re-parked.
- `issues/dp_cron_did_not_fire_false_positive_burst_2026_08_10.md` —
  `asset_group: [cross-cutting, tradfi, sports, prediction, defi]`, `parent_epic: infrastructure_master`. Per the
  primary-owner rule (`parent_epic`, not `asset_group`, decides ownership for a multi-tranche doc), this is `infra`'s
  doc to extract from, not tradfi's — correctly excluded here, consistent with batch11's own "Flagged, not batched —
  cross-tranche ownership" precedent. Its 2 open `[OPERATOR]` todos (VM-relaunch decisions spanning 5 registries) aren't
  tradfi-specific anyway.
- `issues/databento_ice_opra_subscription_ask_2026_08_09.md` — verdict `operator_gated_credential_ask` (a Databento
  ICE/OPRA subscription is a billing decision, not mechanical work) — but this doc was tagged `[cross-cutting]`, not
  `[tradfi]`, at the exact moment slot-25 generated its 52-doc candidate snapshot (`unified-trading-pm@6489d742bf`,
  01:24:46 UTC); the cross-cutting tranche's own concurrent `/ag-closeout-audit` retagged it to `[tradfi]` 10 minutes
  later (`unified-trading-pm@ca9dd1cdac`, 01:34:37 UTC) AND already classified + parked it
  (`ag_closeout_audit_cross_cutting_parked_2026_08_10.md`, "verdict `operator_gated_credential_ask`" — matches this
  pass's independent read exactly). Genuinely not a miss by either pass, just a cross-tranche retag racing slot-25's
  snapshot by 10 minutes. No action needed; noted here for tradfi-side discoverability only.

## Progress Log

- 2026-08-10 (ag_closeout_auditor, slot 22, dispatch agt-a19d1f): drafted alongside its finalize twin, `status: draft`.
  1 conflict-clear item (2 todos) extracted from the 1 genuine gap found in slot-25's 4-hours-prior 52-candidate
  snapshot. Full same-day methodology (why a fresh 52-agent Phase 1 fan-out was NOT re-run, and how the gap was found
  instead) recorded in this pass's Phase 2 report and cross-referenced in
  `ag_closeout_audit_tradfi_parked_2026_08_10.md`.
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).
