---
doc_type: plan
title: Root-cause the dex_swaps recent multi-venue gap cluster (bounded first step, NOT the full migration)
summary: >-
  Operator asked to dispatch the dex_swaps → dex_pool_swaps migration
  (defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md). That doc has been independently re-checked
  4 separate times (2026-08-04 x2, 2026-08-07, 2026-08-09) and each time corroborated as `too_large_or_risky` /
  genuinely judgment-heavy for AO dispatch AS A WHOLE: 22 of 24 (venue,chain) pairs have real legacy-only content
  (up to 84% on SUSHISWAP_V3/ARBITRUM) that a blind rename would destroy, and there's an unexplained
  ~2025-07-27..2025-08-06+ multi-venue gap cluster that must be root-caused BEFORE any migration can even be
  designed (is a legacy writer still live for some venues today? if so, migrating without first stopping/
  redirecting it would just regenerate the gap). Per the AO-eligibility rule ("outcome DETERMINABLE by the worker
  alone, never an open-ended judgment/design call"), only the root-cause check is bounded and AO-dispatchable
  today — dispatching the full migration design would repeat exactly the mistake this doc's own R5 precedent
  warns against. Scoping the dispatch to this one bounded step; the actual migration (once root-caused) needs its
  own follow-on plan and a full five-part delete-safety proof, not this one.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, dex_swaps, canonicalization, root-cause, gap-investigation]
related:
  [
    /plans/active/issues/defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
effort: max
drift_direction: none
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 7, 2026-08-16 — operator asked to dispatch the migration; scoped to the bounded root-cause first step, see summary"
locked_by:
context_scope:
  [
    /plans/active/issues/defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/dex_swaps_handler.py,
  ]
locked_since:
resolved_by:
---

# Root-cause the dex_swaps recent multi-venue gap cluster

## Todos

- [ ] [DATA] P2. **Root-cause the ~2025-07-27..2025-08-06+ multi-venue gap cluster.** For the affected venues
      (`AERODROME_V3/BASE`, `CAMELOT_V3/ARBITRUM`, `PANCAKESWAP_V3/{BASE,ETHEREUM}`, `SUSHISWAP_V3/{AVALANCHE,ETHEREUM}`,
      `UNISWAP_V3/{ARBITRUM,BASE,OPTIMISM}`): determine (a) is a legacy `dex_swaps`-emitting writer still active
      today for any of these venues (check `dex_swaps_handler.py` deployment/dispatch history, not just current
      source code — the code being retired doesn't prove no old deployment is still running), or (b) did the
      canonical `dex_pool_swaps` writer silently stop/lag for this window across many venues simultaneously. This
      is a bounded, determinable-by-worker-alone measurement (check live writer status + manifest recency per
      venue) — it does NOT include designing or executing the actual content migration, which stays gated on this
      finding plus a full five-part delete-safety proof. Report the finding back into
      `defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md`'s Progress Log; do not proceed to
      migration design in this same dispatch. Repo: market-tick-data-service.

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 7, operator ruling — scoped)**: operator asked to dispatch
  the dex_swaps migration; scoped down to only the bounded root-cause step per repeated `too_large_or_risky`
  corroboration in the source doc (see summary above) — the full migration is NOT dispatched by this plan.
**context-scout 2026-08-17**: populated/refreshed context_scope (2 entries)
