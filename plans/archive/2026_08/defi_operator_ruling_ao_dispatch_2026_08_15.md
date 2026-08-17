---
doc_type: plan
title: DeFi phoenix delete + orphan-bucket delete verify + live-poller scoping
summary: >-
  Operator-ruled 2026-08-15 (na-eligibility-audit follow-up Q&A) — three DeFi items from
  cross_ag_live_capture_parity_2026_08_14.md and defi_migration_audit_log_2026_07_24.md: delete phoenix_ws.py dead code,
  verify-then-execute the duplicate/legacy DeFi orphan-bucket delete, and begin scoping the ~40 BLOCKED-BUILD DeFi live
  pollers the operator approved building.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service, instruments-service]
scope: [engineer]
tags: [defi, canonicalization, venue-registry, gcs-delete, live-capture]
related:
  [
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/archive/2026_08/issues/uac_venue_to_asset_group_defi_registry_gap_2026_08_09.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
assigned_role: data_engineering
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A, 2026-08-15"
locked_by:
context_scope:
  [
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/archive/2026_08/issues/uac_venue_to_asset_group_defi_registry_gap_2026_08_09.md,
    /plans/active/issues/plan_reconciler_findings_defi_2026_08_17.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
locked_since:
resolved_by:
---

> **ARCHIVED 2026-08-17** — all 3 todos done, unlocked, closed out via the standard 6-step ritual (finalize doc
> `defi_operator_ruling_ao_dispatch_2026_08_15_finalize.md` archived alongside). Every corpus referrer has been
> fixed to point at the archive path. This doc is retained for provenance only.

# DeFi phoenix delete + orphan-bucket delete verify + live-poller scoping

## Todos

- [x] ✅ [DATA] P2. **DONE 2026-08-17 — resolved: NOT a real contradiction; SKIPPED the deletion (the original
      "UAC-excluded venue" premise was factually wrong).** Full evidence in this doc's Progress Log below.
      **RETAGGED 2026-08-16 (operator ruling, na-eligibility-audit follow-up round 4): this is a
      read-then-compare task, not an operator judgment call — dispatch it, do not gate it.** Reconcile before
      deleting: `cross_ag_live_capture_parity_2026_08_14.md` line 148-151 claims `PHOENIX-SOLANA` is "not in current
      UAC `VENUES_BY_ASSET_GROUP` at all" (verified live, 168-venue universe) and its REST API was deprecated
      2026-05-15 — operator ruled 2026-08-15 to delete `phoenix_ws.py` as dead code on that basis. But that same
      source doc's own Progress Log (line 383-385) separately notes
      `/plans/archive/2026_08/issues/uac_venue_to_asset_group_defi_registry_gap_2026_08_09.md` (open, `assigned_vm: planning`)
      independently found `PHOENIX-SOLANA` **IS** present in `ALL_DEFI_VENUES`. These two findings directly disagree on
      whether `PHOENIX-SOLANA` exists in any UAC venue registry today. Read both docs, resolve which is current, and
      only THEN execute (or skip) the `phoenix_ws.py` deletion — do not delete blind on the operator's original ruling
      alone, since that ruling was made without this contradiction surfaced. (repos: unified-api-contracts,
      market-tick-data-service)
- [x] ✅ [DATA] P1. **NOT CONFIRMED — did not delete. Two independent blockers found, reported in
      `/plans/active/issues/defi_orphan_bucket_delete_list_includes_canonical_bucket_2026_08_15.md`.** (1) The
      unique-gap migration (Aave 2022-03..10, marinade LST, KAMINO DEX pools) has NOT landed: zero code/script evidence
      anywhere — `_migrate_defi_classify.py`'s 9 `BucketSpec` entries cover none of the three gaps, no
      `marinade`/`KAMINO` hits anywhere under `market-tick-data-service/.../scripts/`, no one-off backfill script
      exists, and the source todo (`defi_migration_audit_log_2026_07_24.md` line 522-529) is still open. (2)
      Independently, the delete list itself is stale: `market-data-tick-defi{,-prd}` — the FIRST bucket pair in the
      dispatched list — is the PERMANENT canonical DeFi bucket today, not a legacy orphan, per the 2026-07-10..07-16
      bucket estate cleanup already documented in
      `/plans/active/issues/defi_migration_dedicated_bucket_architecture_retired_2026_08_14.md`. Executing the delete as
      originally scoped would have destroyed the live canonical DeFi tick-data bucket. Filed the new issue doc with a
      corrected re-scoped delete list + the still-needed migration todos. (repo: instruments-service — verification
      only, no code change needed for this todo)
- [x] ✅ [DATA] P2. Enumerated the DeFi venues currently left as `BLOCKED-BUILD` live-poller placeholders
      (`cross_ag_live_capture_parity_2026_08_14.md` § Finding D) and produced a phased build plan —
      `/plans/active/defi_live_poller_phased_build_2026_08_15.md` (unified-trading-pm, this commit). Measured 39
      currently BLOCKED-BUILD (not the `~40` estimate — 41 registered across the two scaffolds, 2 already taken over by
      real connectors), phased into a prerequisite connector-pattern-extraction tranche + 4 chain-footprint tranches,
      with 2 operator follow-up todos (TVL-ordering confirmation, dispatch-cadence ruling) filed in the new plan. Not
      all 40 pollers built — that was never this todo's done-when.

## Progress Log

- **2026-08-15 (na-eligibility-audit follow-up, operator ruling)**: extracted from
  `cross_ag_live_capture_parity_2026_08_14.md` and `defi_migration_audit_log_2026_07_24.md`. The `.bak*` retention
  question from the same source doc was answered "leave as-is indefinitely" (no dispatch) — recorded directly in that
  doc, not part of this plan. The phoenix contradiction (todo 1) was found during this extraction, after the operator's
  ruling — flagged rather than silently resolved either way.

- **2026-08-15 (data_engineering, slot 27, task `defi_operator_ruling_ao_dispatch-e5203df5b8c2`)**: todo 2 closed — NOT
  CONFIRMED, did not delete. Found a SECOND stale-doc contradiction of the same shape as todo 1's: the dispatched delete
  list named `market-data-tick-defi{,-prd}` as a delete-after-migration candidate, but that bucket is now the PERMANENT
  canonical DeFi tick-data bucket (2026-07-10..07-16 bucket estate cleanup), not a legacy orphan — already predicted by
  `defi_migration_dedicated_bucket_architecture_retired_2026_08_14.md`'s "Recommended decision" #2, now confirmed live.
  Separately, the Aave 2022-03..10 / marinade / KAMINO unique-gap migration this todo was gated on has no code/script
  evidence of ever landing. Full evidence + a corrected re-scoped delete list + follow-up migration todos filed in
  `/plans/active/issues/defi_orphan_bucket_delete_list_includes_canonical_bucket_2026_08_15.md`.

- **2026-08-15 (data_engineering, slot 10, task `defi_operator_ruling_ao_dispatch-656d2e5acbf7`)**: todo 3 closed —
  enumerated the two BLOCKED-BUILD scaffold registries directly (`dex_swap_scaffold_ws.py` 22 keys,
  `defi_lending_scaffold_ws.py` 19 keys; 2 already taken over by real connectors) and produced the phased build plan at
  `/plans/active/defi_live_poller_phased_build_2026_08_15.md`. `status: draft` on the new plan — it needs an operator
  ruling on dispatch cadence (filed as a follow-up todo in that plan) before any tranche is extracted into an
  AO-dispatchable batch.

- **2026-08-17 (slot 9, data_engineering, task `defi_operator_ruling_ao_dispatch-7dde9fa028b0`)**: todo 1 closed —
  resolved the `PHOENIX-SOLANA` contradiction and **SKIPPED the `phoenix_ws.py` deletion**. Live-verified against
  `unified-api-contracts` (workspace `.venv`, both registries imported directly):

  ```
  PHOENIX-SOLANA in ALL_DEFI_VENUES: True   (170 total members)
  PHOENIX-SOLANA DEFI_VENUE_PHASE: pipeline
  PHOENIX-SOLANA in VENUES_BY_ASSET_GROUP['defi']: False   (103 members, unchanged)
  PHOENIX-SOLANA in VENUE_TO_ASSET_GROUP: defi
  ALL_DEFI_VENUES - VENUE_TO_ASSET_GROUP.keys(): set()   (empty — the 2026-08-09 registry-gap fix holds)
  ```

  **Not a real contradiction — two docs correctly describing two different registries.** `PHOENIX-SOLANA` genuinely
  is, and has consistently been (confirmed already present as of the 2026-08-09 registry-gap doc, predating the
  2026-08-14 "not in UAC at all" claim), a member of `ALL_DEFI_VENUES` — just `DEFI_VENUE_PHASE="pipeline"`
  (batch/backfill-only), correctly excluded from the narrower live-phase `VENUES_BY_ASSET_GROUP["defi"]` by design
  (unrelated to the dead REST API). `VENUE_TO_ASSET_GROUP["PHOENIX-SOLANA"] == "defi"` today, per the fix already
  shipped in the registry-gap doc (`unified-api-contracts@7b96791e`).

  **The original deletion rationale is factually wrong on both counts it cited**: (1) "venue doesn't exist in UAC
  at all" — false, per above; (2) "dead REST API" — moot, `phoenix_ws.py`
  (`market-tick-data-service/market_tick_data_service/live/connectors/phoenix_ws.py`) never depends on
  `api.phoenix.trade`; it's a fully-implemented Jupiter-quote-polling adapter built specifically to route around
  that dead REST API (`lite-api.jup.ag/swap/v1/quote?dexes=Phoenix`), with proper reconnect/backoff semantics — not
  scaffold/stub code. It IS actively imported via `connectors/__init__.py::register_all()`'s standard rollout list
  (not orphaned/unreferenced).

  **Why it's still currently unreachable at dispatch time — a different, fixable reason**: it registers under the
  bare lowercase venue key `"phoenix"` (`register_ws_feed_connector(venue="phoenix", ...)`), and
  `resolve_ws_feed_venue_key()`'s exact/`.lower()`/`.upper()` lookup chain
  (`market-tick-data-service/market_tick_data_service/cli/handlers/websocket_streaming_handler.py:63-85`) cannot
  bridge `"phoenix"` → the canonical `"PHOENIX-SOLANA"` dispatch key it would be looked up under — the exact same
  resolver-mismatch bug class already fixed for `curve`/`morpho`/`orca`/`raydium` (re-registered under their full
  canonical chain-suffixed key). Phoenix was left unfixed at the time solely because of the now-refuted "doesn't
  exist" premise.

  **Decision: SKIPPED the deletion.** Deleting a real, working, purpose-built connector on a refuted premise would
  destroy real reusable work for no valid remaining reason. Corrected the stale claim + resolved the source
  `[OPERATOR]` todo in place — `/plans/active/cross_ag_live_capture_parity_2026_08_14.md` (see its 2026-08-17
  correction block + Progress Log entry, same commit). **Two genuine follow-up decisions remain, deliberately NOT
  resolved here** (out of this bounded task's scope — the first is mechanical but only meaningful paired with the
  second, which is a real priority/resourcing call, not mine to make unilaterally): (1) apply the same
  canonical-key re-registration fix as curve/morpho/orca/raydium; (2) whether to promote `PHOENIX-SOLANA` from
  `DEFI_VENUE_PHASE="pipeline"` to `"live"` in `market_data_categories.py` so live dispatch actually selects it in
  the first place. No code shipped for this todo (the correct action was to NOT change `phoenix_ws.py`); the
  shipped change is the doc corrections above (unified-trading-pm).

**context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
