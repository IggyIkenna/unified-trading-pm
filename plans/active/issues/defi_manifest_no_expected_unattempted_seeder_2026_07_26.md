---
doc_type: issue
title:
  "C8 re-diagnosis: DeFi has NO expected_unattempted seeder at all — under-enumeration is not a stale/partial venue list"
summary: >-
  Investigation of defi_satellite_ao_dispatch_batch2_2026_07_26.md's C8 todo ("fill DeFi manifest venue-key
  under-enumeration... confirm the enumerator is driven off the full UAC venue-capability registry rather than a
  stale/partial list") found the todo's premise is false: there is no enumerator/seeder for DeFi at all. The
  sentinel-based expected_unattempted path that CeFi/TradFi/Sports/Prediction use
  (market_tick_data_service/engine/orchestrator/__init__.py:413-421 explicitly excludes every defi-asset-group venue
  from active_venues, with the comment "Skipping %d DeFi venues (use collect-* handlers)") never fires for DeFi, and
  DefiManifestRecorder (cli/handlers/_defi_manifest.py:343-802) has no record_expected_unattempted method at all. A DeFi
  manifest row exists iff a collect-* handler's own hand-maintained protocol list happened to name that venue that day —
  there is no seeded "not yet attempted" honest-absence row for anything outside those lists. Building a real seeder is
  a genuine cross-cutting architecture decision (new manifest-writing code path + a decision on what the denominator
  should be), not a config/list fix, and per CLAUDE.md's Dispatch-scope-eligibility ruling should not be improvised
  inline in a 1-hour P1 todo. This doc also corrects two false premises baked into the plan's C8 "done when" criteria
  (DRIFT-SOLANA requirement, FRAX family classification) and flags that the FLUID-ETHEREUM gap specifically is NOT
  list-drift — it's the SAME known "adapter built but not wired to the CLI handler used for manifest writes" class
  already tracked in mtds_is_full_adapter_smoketest_findings_2026_07_07.md, so a naive fix would either duplicate that
  doc's tracked work or (if done wrong) write dishonest zero-row manifest stamps.
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, manifest, availability-index, expected-unattempted, honest-coverage, re-scope]
related:
  [
    defi_satellite_ao_dispatch_batch2_2026_07_26,
    data_completion_defi_2026_07_15,
    mtds_is_full_adapter_smoketest_findings_2026_07_07,
  ]
created: 2026-07-26
parent_epic: defi_master
assigned_vm: planning
source: [defi_satellite_ao_dispatch_batch2-001 (task C8)]
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# C8 re-diagnosis: no DeFi expected_unattempted seeder exists

## What I found

Dispatched task `defi_satellite_ao_dispatch_batch2-001` (plan item C8) asked to "audit the enumeration path that seeds
`expected_unattempted` rows for defi... confirm it is being driven off the full UAC venue-capability registry rather
than a stale/partial venue list; re-run (or extend) the seeding pass." A full-repo investigation found the premise
itself is false:

1. **No DeFi seeder exists.** `market_tick_data_service/engine/orchestrator/__init__.py:413-421`
   (`_build_active_venues_for_date`) explicitly filters every `VENUE_TO_ASSET_GROUP.get(v) == "defi"` venue OUT of
   `active_venues` before the sentinel fan-out (`market_tick_data_service/engine/orchestrator/sentinels.py:787-900` /
   `record_expected_unattempted` at `sentinels.py:664-772`) ever runs. `DefiManifestRecorder`
   (`cli/handlers/_defi_manifest.py:343-802`, the shared shim every DeFi `collect-*` handler calls) has methods
   `record_captured`/`record_empty`/`record_zero_rows`/`record_failed`/`record_catalog_unavailable` — **no
   `record_expected_unattempted` at all**. A DeFi (venue, chain, data_type) triple gets a manifest row **iff and only
   if** some handler's own hardcoded venue loop names it and the handler actually ran that day. There is no seeding pass
   to extend — one has never existed.

2. **The real per-family "enumeration" is 3 independently hand-maintained lists**, none derived from or cross-checked
   against UAC's `DEFI_VENUE_DATA_TYPE_CAPABILITIES` / `DEFI_VENUE_PHASE`
   (`unified-api-contracts/unified_api_contracts/registry/defi_venue_capabilities.py`, `defi_venues.py`):
   - `lending_indices_handler.py:176`:
     `_DEFAULT_PROTOCOLS = ["aave_v3", "spark", "compound_v3", "morpho", "kamino_lending", "solend", "marginfi"]` — no
     `fluid`.
   - `risk_params_handler.py:107`: includes `fluid`.
   - `liquidations_handler.py:149`: includes `fluid`.
   - Chain enumeration for whichever protocols the handler DOES know about is a 4th, separate source:
     `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py:62-217` (`SUBGRAPH_IDS`),
     e.g. `"morpho": {"ETHEREUM": ..., "BASE": ...}` (comment: "ARBITRUM/OPTIMISM/POLYGON: 0 major-asset markets as of
     2026-03") and `"fluid": {"ETHEREUM": "fluid-mainnet"}` only.

3. **The plan's own "done when" bakes in a stale requirement.** C8 (migrated 2026-07-13 from
   `defi_manifest_canonicalisation_2026_06_01.md`, predating the 2026-07-16 Solana-perp-DEX sweep) requires
   "DRIFT-SOLANA... confirmed present" in the manifest. DRIFT-SOLANA was **deliberately, comprehensively removed** from
   every UAC registry 2026-07-16 (operator ruling: all Solana perp DEXes dropped except Jupiter) — confirmed via a full
   grep of every `DRIFT` hit in `unified-api-contracts` (`defi_venues.py:198-200,601-602,720,793`,
   `venue_adapter_keys.py:210`, `chain_env.py:298`, `venue_launch_dates.py:76,207`,
   `venue_collateral.py:8,105,218, 237-238`, `expected_coverage.py:307`, `market_data_categories.py:162-163,1082-1085`,
   `venue_mapping.py:125-126,246,394,1056`, `perp_funding_cadence.py:75`,
   `internal/reference/instrument_validation.py:36,154,160`, `scripts/enumerate_strategy_instruments.py:115` — every hit
   is a removal comment; the only surviving `DRIFT` tokens are the unrelated CeFi token symbol). DRIFT-SOLANA's manifest
   absence is CORRECT, not a gap — "confirmed present" as a done-criterion is wrong and must never be satisfied.

4. **FRAX-ETHEREUM's capability is `vault_share_price`, not `lst_rates`/`lending_indices`**
   (`defi_venue_capabilities.py:259`) — it was never in scope for the "lst 14/22" or "lending 6/21" family counts the
   plan cited; that's a category-mismatch in the plan's framing, not a coverage bug. If FRAX-ETHEREUM genuinely has zero
   manifest rows under `vault_share_price`, that's a `vault_share_price_handler.py` run/scheduling question (handler
   already has a real `_VAULTS["sFRAX"]` entry and calls `record_captured`/`record_failed`), separate from this C8
   enumeration question.

5. **FLUID-ETHEREUM's gap is NOT the list-drift it looks like.** Adding `"fluid"` to `lending_indices_handler.py:176`'s
   `_DEFAULT_PROTOCOLS` would NOT work even mechanically: `_query_and_parse`'s `cascades` dict
   (`cli/handlers/lending_indices_subgraph.py:192-206`) only has entries for `aave_v3`/`spark`/ `compound_v3`, and
   `_maybe_dedicated_collector` (`cli/handlers/lending_indices_morpho.py:44-65`) only special-cases Solana protocols +
   `morpho`. A bare `fluid` entry would hit `cascade = cascades.get("fluid")` → `None` → an empty DataFrame → a
   **dishonest zero-rows manifest stamp** (Fluid genuinely has data; the query just never ran) — exactly the
   silent-placeholder failure mode the data_engineering craft north-star bans. Fluid's REAL collection path is a
   separate, fully-built RPC adapter (`market_interface/adapters/defi/fluid_adapter.py`, `FluidAdapter` /
   `BaseDefiAdapter`, `download_market_data`/`_download_rate_indices`) that is **not wired into
   `lending_indices_handler.py`'s CLI/manifest-write loop at all** — the same "functional adapter never invoked by the
   production orchestrator" class already tracked for VENUS/BENQI/RADIANT/EULER_V2 (`defi_venue_capabilities.py:141-144`
   cites `mtds_is_full_adapter_smoketest_findings_2026_07_07.md` P1 for those 4). **FLUID's own adapter bugs are ALREADY
   tracked and partially fixed in that same doc** (§ "FLUID lending_indices revert-data guard" P0, shipped
   `market-tick-data-service@3c00b504` + follow-ups 2026-07-08→14; a still-open P1 VERIFY item about an ~18-month
   pre-2025-11-26 data gap). Filing a new "fix FLUID list drift" todo here would duplicate that doc's tracked work, not
   create new work.

6. No codex doc under `codex/02-data/` describes a DeFi expected_unattempted seeder/enumerator/universe-builder —
   consistent with none existing.

## Why it matters

The honest-coverage denominator for DeFi manifest families (lst/lending/perp/etc.) is currently whatever the union of
several hand-maintained, independently-drifting per-handler lists happens to cover — not derived from, or cross-checked
against, UAC's `DEFI_VENUE_DATA_TYPE_CAPABILITIES`/`DEFI_VENUE_PHASE` registries. This means a venue can have a real UAC
capability declaration and STILL get zero manifest signal of any kind (not even an honest `expected_unattempted`/"not
producible" row) if no handler's hardcoded list happens to include it — indistinguishable, from the manifest's point of
view, from a venue nobody ever declared. This is a data-pipeline-correctness class finding
(honest-absence-downstream-handling is the governing SSOT: `/codex/02-data/honest-absence-downstream-handling.md`).

## Recommended decision

C8, as scoped in `plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md` (P1, 1 estimated hour, "re-run or extend
the seeding pass"), cannot be completed as written — there is no seeding pass to extend, and its own done-criterion
(DRIFT-SOLANA present) is unsatisfiable-by-design. This needs an operator/architecture decision before any AO-dispatch,
not a worker fixing it inline:

- **Option A (recommended)**: commission a dedicated design+build plan for a real DeFi `expected_unattempted` seeder
  mirroring the sentinels.py pattern, keyed off `DEFI_VENUE_DATA_TYPE_CAPABILITIES` + `DEFI_VENUE_PHASE` as the
  denominator SSOT (needs a decision on how to reconcile that against the per-handler
  `SUBGRAPH_IDS`/`_DEFAULT_PROTOCOLS` reality — a capability entry existing doesn't mean a working collector exists, per
  the FLUID case above).
- **Option B**: decide DeFi intentionally has no seeder (handlers ARE the enumeration, by design) and instead correct
  the plan's C8 "done when" to something achievable (e.g., reconcile `_DEFAULT_PROTOCOLS`/`SUBGRAPH_IDS` against
  `DEFI_VENUE_DATA_TYPE_CAPABILITIES` and flag mismatches, without requiring new manifest-writing code).

Either way, C8's DRIFT-SOLANA requirement must be dropped from any future done-criteria.

## Follow-up todos

- [ ] [DATA] P2. BLOCKED-OPERATOR-DECISION — Design + build a DeFi `expected_unattempted` seeder (mirrors
      `sentinels.py`'s `record_expected_unattempted` pattern) keyed off UAC's `DEFI_VENUE_DATA_TYPE_CAPABILITIES` +
      `DEFI_VENUE_PHASE` — **RULED 2026-07-26 (BLK-7c950d06: Option A)**: this is the correct direction, tracked now as
      its own human plan `defi_expected_unattempted_seeder_design_2026_07_26.md` (assigned_vm: NA per BLK-3221d4b3 — the
      capability-vs-collectibility reconciliation, see FLUID finding #5, is an open-ended per-venue judgment call, not
      AO-dispatchable until an operator resolves it). This line stays non-dispatchable and superseded-by-tracking; do
      the actual work in that plan, not here. (repo: market-tick-data-service)
- [x] ✅ [DATA] P3. **DONE 2026-07-26 (slot-10, data_engineering)** — Reconciled `lending_indices_handler.py:177` /
      `risk_params_handler.py:111` / `liquidations_handler.py:149`'s three `_DEFAULT_PROTOCOLS` lists against each other
      and against `SUBGRAPH_IDS`
      (`unified-api-contracts/unified_api_contracts/registry/capability_declarations/     _defi.py:62-217`) +
      `_risk_params_stage.py:23`'s `SOLANA_LENDING_PROTOCOLS`. Read-only — no code changed (per this todo's own
      guardrail: do not add `fluid` to `lending_indices_handler.py` without a real collector).

      | protocol | lending_indices | risk_params | liquidations | `SUBGRAPH_IDS` |
          |---|---|---|---|---|
          | `aave_v3` / `spark` / `compound_v3` / `morpho` | Y | Y | Y | Y |
          | `fluid` | **N** (no `cascades` entry — confirmed real gap, already tracked as this doc's finding #5) | Y (`_CATALOGUE_ONLY_PROTOCOLS`, deliberate) | Y (dedicated `_FLUID_LIQUIDATIONS_QUERY`/`_parse_fluid_liquidations`) | Y |
          | `kamino_lending` | Y (dedicated RPC fetcher) | Y | **N** (absent, no rationale found) | N (Solana, RPC-based) |
          | `solend` | Y (dedicated RPC fetcher) | **N** | **N** | N (Solana) |
          | `marginfi` | Y (dedicated RPC fetcher) | **N** | **N** | N (Solana) |

          **Findings**:
          1. `fluid`'s gap is lending_indices-ONLY, confirmed — `risk_params_handler.py` (`_CATALOGUE_ONLY_PROTOCOLS =
             frozenset({"morpho", "fluid"})`, line 115) and `liquidations_handler.py` (dedicated fluid query, lines
             588/724/739) both have REAL, working, deliberate `fluid` paths; only `lending_indices_handler.py`'s
             `_query_and_parse` cascades dict lacks a `fluid` entry. No new work needed beyond what #5 already tracks.
          2. **New, previously-unflagged gap**: `risk_params_handler.py`'s own imported `SOLANA_LENDING_PROTOCOLS`
             constant (`_risk_params_stage.py:23`, `frozenset({"kamino_lending", "solend", "marginfi"})`) declares all 3
             Solana lending protocols as catalogue-fallback-capable (the dispatch logic at lines 330/408 correctly
             branches on `protocol in SOLANA_LENDING_PROTOCOLS`), but `_DEFAULT_PROTOCOLS` (the actual iteration list,
             line 380) only includes `kamino_lending` — `solend`/`marginfi` risk_params are silently NEVER collected even
             though the underlying mechanism already supports them. Unlike the documented `fluid`/`morpho`
             `_CATALOGUE_ONLY_PROTOCOLS` reasoning, no comment justifies omitting `solend`/`marginfi` here — reads as an
             unintentional oversight (the 3-Solana-protocol set exists as a real shared constant, just not fully wired
             into this one handler's dispatch list), not a documented scope decision. Filed as a fresh, precisely-scoped
             follow-up (P3) below rather than fixed inline (adding them changes runtime dispatch behavior, out of scope
             for a read-only reconciliation todo).
          3. `liquidations_handler.py` has ZERO Solana-protocol coverage (no `kamino_lending`/`solend`/`marginfi`, no
             `SOLANA_LENDING_PROTOCOLS` import at all) — no comment either way; flagging as unconfirmed (may be an
             intentional scope limit if Solana lending liquidations genuinely have no equivalent data source) rather than
             asserting it's a bug.
          4. The 4 core EVM protocols (`aave_v3`/`spark`/`compound_v3`/`morpho`) are fully consistent across all 3
             handlers and `SUBGRAPH_IDS` — no mismatch.
          (repo: market-tick-data-service)

- [ ] [DATA] P3. **NEW (found while reconciling the todo above)** — `risk_params_handler.py`'s `_DEFAULT_PROTOCOLS`
      (line 111) omits `solend`/`marginfi` even though its own imported `SOLANA_LENDING_PROTOCOLS` constant
      (`_risk_params_stage.py:23`) declares both as catalogue-fallback-capable and the dispatch logic (lines 330/408)
      already branches correctly on membership in that set — the only missing piece is adding them to the line-380
      iteration list. Confirm with the handler owner whether this is a genuine oversight (most likely, given no
      rationale comment exists, unlike the documented `fluid`/`morpho` `_CATALOGUE_ONLY_PROTOCOLS` case) or an
      intentional scope limit, then either add `"solend"`/`"marginfi"` to `_DEFAULT_PROTOCOLS` (if the IS catalogue
      actually carries risk-param fields for these two Solana protocols — verify before flipping, don't assume) or
      document why they're excluded. (repo: market-tick-data-service). Done when: the omission is confirmed deliberate
      (documented) or fixed (protocols added + a regression test proves they now dispatch), with real IS-catalogue data
      confirmed present before any dispatch-list change ships.
- [ ] [DATA] P3. Confirm whether FRAX-ETHEREUM's `vault_share_price_handler.py` has actually run/been scheduled recently
      — if its manifest rows are genuinely absent, that's a scheduling gap, not an enumeration gap. (repo:
      market-tick-data-service)
- [ ] [DATA] P3. Confirm MORPHO-ARBITRUM/OPTIMISM/POLYGON's manifest absence is the intentional "0 major-asset markets
      as of 2026-03" `SUBGRAPH_IDS` scoping decision (re-verify the underlying claim is still current) vs. needing an
      honest "not IS-producible" manifest stamp once/if the P2 seeder above exists. (repo: unified-api-contracts docs
      review + market-tick-data-service)
- [x] ✅ [INFRA] P3. **DONE 2026-07-26 (slot-4)** — Close a gate gap in agent-orchestrator's `/done` M3 verification
      found 2026-07-26 (slot-2, BLK-0222fc53 ruling): a `- [ ]` cross-repo todo that is genuinely re-scoped/superseded
      (never flipped `[x]`, because there is nothing to complete against — see
      `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s C8 entry, converted to a non-checkbox `CANCELLED — SUPERSEDED`
      bold marker) has no `/done` path: M3 hard-rejects (`cross_repo_pm_file_touched_no_checkbox_flip`) any commit
      touching the plan file that doesn't flip `[ ]`→`[x]`, forcing a worker to `/skip-current-task` instead, with no
      way to record real disposition on the task itself. Added the M3 exception: `verify.check_plan_flip`
      (agent-orchestrator@c9f805c) now also recognizes a `- [ ] <brief>` line converted to a non-checkbox
      CANCELLED/SUPERSEDED marker bullet (per `task_template.md`'s "remove a todo" convention) — in both single-repo and
      cross-repo modes, via new helper `_diff_cancels_checkbox` — and accepts `/done` with
      `reason="todo_cancelled_superseded"`, without requiring a `[x]` flip. Regression coverage:
      `tests/test_done_gate_plan_flip_hard_reject.py` (+2 tests, single-repo + cross-repo modes); full
      `quality-gates.sh` green (1755 passed, 1 skipped). (repo: agent-orchestrator)
- [x] ✅ [DOCS] P3. **DONE 2026-07-26 (slot 9)** — Corrected `data_completion_defi_2026_07_15.md` item C8: dropped the
      stale "DRIFT-SOLANA... confirmed present" done-criterion (deliberately removed 2026-07-16, must never reappear)
      and the FRAX category-mismatch framing, with a pointer to this doc's full re-diagnosis. A `plans/active/` grep for
      the same stale framing turned up one more instance —
      `defi_consolidated_closeout_aggregated_sources_2026_07_24.md`'s C8 summary bullet (line 152) repeated the
      identical "genuine absentees DRIFT-SOLANA/FRAX/MORPHO/FLUID" line — corrected there too, same pointer added. The
      plan's own `defi_satellite_ao_dispatch_batch2_2026_07_26.md` C8 todo (lines 82-101) still states the original
      stale framing verbatim in its body text, but that's intentional — it's the ORIGINAL task text being re-diagnosed
      by this doc's annotation immediately below it, not a separate uncorrected citation; left as-is as the historical
      record. (repo: unified-trading-pm)

## Progress Log

- 2026-07-26 (slot 2): Re-dispatch of `defi_satellite_ao_dispatch_batch2-001` (C8) hit this doc's already-filed
  re-diagnosis. Escalated the two open decisions from § Recommended decision: (1) BLK-7c950d06 — ruled **Option A**
  (build the real seeder; C8's checkbox cannot be completed as written and stays honestly unchecked). (2) BLK-3221d4b3 —
  the seeder design/build work's plan destination ruled **human plan** (`assigned_vm: NA`), because the
  capability-vs-collectibility reconciliation (FLUID finding #5) is an open-ended per-venue judgment call, not
  AO-dispatchable. Created `defi_expected_unattempted_seeder_design_2026_07_26.md` to track the design + the gating P0
  reconciliation todo; marked the P2 follow-up todo above `BLOCKED-OPERATOR-DECISION` + superseded-by-tracking so it
  does not get picked up by a worker ahead of that plan. No code changes; this task's disposition is fully captured in
  this doc + the new plan.
- 2026-07-26 (slot 2): `/done` (unified-trading-pm@628324586) rejected with
  `cross_repo_pm_file_touched_no_checkbox_flip` — M3 requires an actual `[ ]`→`[x]` flip, which the ruling above
  forbids. Escalated as BLK-0222fc53; ruled **Option A**: self-`/skip-current-task` (no M3 run) + convert the C8 todo in
  `defi_satellite_ao_dispatch_batch2_2026_07_26.md` from a `- [ ]` checkbox to a non-checkbox `CANCELLED — SUPERSEDED`
  bold marker (per `task_template.md`'s "remove a todo" convention) so `regen_backlog_from_plan.py` drops it from the
  dispatchable queue instead of re-deriving it. Done: batch2 plan's C8 entry converted; the M3 gate-gap itself filed as
  a new P3 follow-up todo above (repo: agent-orchestrator) per the ruling's guardrail, not a blocker on closing this
  task.
- 2026-07-26 (slot 4): Closed the P3 `[INFRA]` gate-gap follow-up todo above. `server/verify.py`'s
  `check_plan_flip`/`_diff_flips_checkbox` only ever recognized a `- [ ] <brief>` line turning into `- [x] ...`; added
  `_ADDED_CANCELLED_LINE_RE` + a new `_diff_cancels_checkbox` helper so a `- [ ] <brief>` line converted to a
  non-checkbox `CANCELLED`/`SUPERSEDED` marker bullet (the exact convention slot-2 used above) is ALSO accepted, in both
  the single-repo and cross-repo (PM sibling-worktree log-walk) modes — `found_in_commit=True`,
  `reason="todo_cancelled_superseded"`. Added 2 regression tests to `tests/test_done_gate_plan_flip_hard_reject.py`
  mirroring the existing single-repo/cross-repo flip-acceptance tests but asserting the CANCELLED-marker path. Full
  `quality-gates.sh` green (1755 passed, 1 skipped; dashboard tsc+vitest green). Shipped `agent-orchestrator@c9f805c`.
  Session died mid-task after this work was complete but before shipping; the orchestrator's pre-spawn dirty-state gate
  preserved the WIP on `wip-preserve/orchestrator-slot-4-f38f2db` (auto-committed, branch reset afterward), recovered
  cleanly on resume since that commit's parent was exactly the resumed session's HEAD — no work lost.
- 2026-07-26 (slot 10, `data_engineering`): Closed the P3 `_DEFAULT_PROTOCOLS`-reconciliation follow-up todo. Read-only
  investigation (no code touched) confirmed `fluid`'s lending_indices gap is real + already tracked (finding #5), and
  surfaced a NEW, previously-unflagged gap: `risk_params_handler.py`'s own `SOLANA_LENDING_PROTOCOLS` constant declares
  `solend`/`marginfi` as catalogue-fallback-capable but `_DEFAULT_PROTOCOLS` never dispatches them — filed as a fresh,
  precisely-scoped P3 follow-up todo (not fixed inline; a dispatch-list change needs the IS-catalogue data confirmed
  present first).
