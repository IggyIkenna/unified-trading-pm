---
doc_type: plan
title: TradFi consolidated closeout — native AO extract (fresh eligibility triage of the parent's OWN todos)
summary: >-
  Fresh AO-eligibility triage of `tradfi_consolidated_closeout_2026_07_18.md`'s own 13 open native `- [ ]` todos
  (deliberately excluded from this session's earlier `tradfi_satellite_ao_dispatch_batch1/2_2026_07_25.md` extractions,
  which sourced only from OTHER referenced docs). Classified each of the 13 against `task_template.md` §4's "Dispatch-
  scope eligibility" bar: 10 carried a genuinely bounded/checkable sub-scope and are drafted below (several narrowed to
  strip an embedded judgment call or an already-resolved sub-piece — see each todo's provenance note); 3 stay out (1
  already substantively resolved/mis-scoped for tradfi — recommend a checkbox flip, not new dispatch; 1 has its bounded
  sub-piece already done live and its remaining sub-pieces already correctly conflict-gated in batch2's own Deferred
  section — not re-drafted here; 1 is an explicit `BLOCKED-INFRA` marker gated on an unshipped sibling P0). Two live
  cross-checks against the child plan `tradfi_manifest_content_recovery_completion_2026_07_24.md` found the parent's own
  Split-notice digest (2026-07-24) is now STALE relative to that child's live checkboxes — catalogue Surface A
  migration, which the parent's digest still calls "NOT yet executed," actually shipped+applied live 2026-07-25
  (`instruments-service@52d8b3ef`) — this directly un-blocks one of the drafted todos below (see its provenance note)
  and is flagged as a standalone finding for the operator/session, not silently corrected in the parent doc by this
  extraction.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos:
  [
    unified-api-contracts,
    instruments-service,
    market-tick-data-service,
    execution-service,
    deployment-api,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, native-extract, conflict-checked]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md,
    /plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md,
    /plans/active/issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md,
    /plans/active/distinct_values_noncanonical_audit_2026_07_20.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.7
estimate_calibrated_ai_days: 0.56
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Fresh AO-eligibility triage session, 2026-07-25 — "of tradfi_consolidated_closeout_2026_07_18.md's own remaining open
  todos, how many are now genuinely bounded/AO-eligible versus how many genuinely must stay human-only?" This doc's own
  13-item enumeration + classification IS the triage evidence; see per-todo provenance notes below for the reasoning
  chain per item (no separate journal file was produced — this is a single-agent read-and-classify pass, not a
  multi-agent workflow).
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# TradFi consolidated closeout — native AO extract

> **Status: draft.** Per CLAUDE.md's plan-destination rule, flip `status` to `active` only after operator review. All 10
> todos below are same-priority-independent and touch DISTINCT files/targets (verified per-todo below — none of them
> writes back to `tradfi_consolidated_closeout_2026_07_18.md` itself except todo 10, whose entire purpose is exactly
> that; every other todo records its evidence in its own cited source/target so no two todos in this batch collide on
> the same file), so they are safe to dispatch concurrently once activated.

## Why 3 of the 13 native todos are NOT here (see also the closing classification table)

- **Native "Full MTDS+IS adapter smoke findings" todo** — direct read of all 3 cited docs found their real open items
  are **NOT tradfi-scoped**: `mtds_is_full_adapter_smoketest_findings_2026_07_07.md`'s 2 open items are FLUID
  `lending_indices` (DeFi) and DERIBIT/COMBO mistagging (CeFi);
  `uac_data_type_validity_combinator_fragmentation_2026_07_07.md`'s 4 open items are onchain/DeFi (`_L5_VENUES`
  residual), Prediction (POLYMARKET/KALSHI), DeFi/Prediction dead-code, and a DeFi DESIGN decision;
  `instruments_remaining_work_audit_2026_07_10.md` already shows 0 open todos. **Net: 0 genuinely tradfi-scoped open
  work remains across all 3 cited docs** — this native todo is substantively already satisfied for tradfi. Not drafted;
  recommend the closeout flip this checkbox citing this finding rather than treat it as live AO work.
- **Native "NEW 2026-07-24 — two live defects" todo** (source-mislabeling + FX manifest id) — its own text names two
  actions: (a) root-cause/fix the two live defects, and (b) "confirm/flip [the child plan's] relevant todo" against the
  cited 99.3%/99.95% canonicality counter-finding. Live-checked (b) against
  `tradfi_manifest_content_recovery_completion_2026_07_24.md` directly: the cited Phase-B manifest migration todo is
  **already `[x]` "RE-VERIFIED LIVE 2026-07-25"** — action (b) is already done. Action (a) is the exact pair of
  candidates `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s own Deferred section already re-checked and left
  genuinely conflict-gated against this SAME native todo (its own text: _"conflict with the closeout's own still-open
  Phase A2 'NEW 2026-07-24' todo, which directly restates both findings... still unshipped on the closeout side"_).
  Re-drafting (a) here would contradict batch2's own live conflict-check instead of resolving it — not drafted.
  Recommend the closeout's own note be corrected to reflect (b) is done; (a) stays exactly where batch2 already
  correctly left it.
- **Native "BLOCKED-INFRA — Certify tradfi Layer-1" todo** — carries the literal `BLOCKED-INFRA` non-dispatchable marker
  (`task_template.md` §3) and is gated on `tradfi_backfill_throughput_followups_2026_07_24.md`'s own "FINAL STEP"
  (rebuild+promote the served catalogue so `mvp=True` reflects the +409 expansion) — live-checked, still not done (that
  doc's own text: _"currently still old 70,930 set; new groups not yet flagged"_). Stays blocked/human.

## Todos

- [ ] [DATA] P2. **Determine, per MVP cell, whether backfill=paper=live wiring is actually proven — and re-verify each
      "Backfill proven" cell against a FRESH `data-pipeline-check-is`/`data-pipeline-check-mtds` run.** Source native
      todo (lines 218-224 of `tradfi_consolidated_closeout_2026_07_18.md`): for each of the 6 MVP cells in that doc's
      "MVP cells — proven wired" table, either (a) cite the actual paper-trading ledger / live-trading ledger /
      batch-rerun determinism proof (epsilon=0, per `/codex/09-strategy/operational/paper-batch-live-reconciliation.md`)
      for that cell, or (b) state plainly no such proof exists yet. Separately, re-run `data-pipeline-check-is` and
      `data-pipeline-check-mtds` scoped to tradfi (auto-select a high-coverage day) and record a fresh pass/fail per MVP
      cell, rather than trusting the last Progress Log entry. **Scope note**: do NOT re-run the CBOE-specific
      `ohlcv_1s,ohlcv_1m` force+skip command already assigned to `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`'s
      todo 3 (that todo owns confirming that specific in-flight VM's terminal state) — this todo's fresh run is the
      broader all-MVP-cells sweep, a different granularity. **Conflict precedence note**: this native todo is the exact
      "foothold" `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s own Deferred section cites when excluding 2 OTHER
      candidates (verify/launch ES CME futures ohlcv 2021-2024; check/launch the ES_OPT lock, both from
      `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`) as "same ES-futures/options ground, different
      verification method" — those 2 stay deferred until/unless this todo's run resolves the same ground. Repos:
      unified-trading-pm (report), market-tick-data-service, instruments-service. **Done when**: a
      `plans/audit/results/` report (or equivalent dispatch-outcome citation) records, per MVP cell, either a real
      wiring-proof citation or an explicit "no proof exists yet" statement, PLUS a fresh
      `data-pipeline-check-is`/`-mtds` pass/fail verdict with report path/dispatch_id — 0 cells left with only a stale
      Progress Log citation. The closeout's own MVP-cell table gets updated by this batch's companion finalize plan, not
      by this todo directly. Source: `tradfi_consolidated_closeout_2026_07_18.md` (native, lines 218-224).

- [ ] [REVIEW] P2. **Verify CME's `VENUE_DATA_TYPE_CAPABILITIES` declares `mbp_10`/`trades`/`tbbo` as billing-gated (not
      chased to full L3 history) — audit-only, no code change.** Source native todo (lines 238-244): the closeout's
      framing that "no `ohlcv_15m/24h` aggregation writer exists" is **STALE** — live-checked against
      `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s todo 1, which found the writer code already shipped
      (`canonical_writer` fixes, tests green) and merely pending a tarball-rebuild deploy (that deploy is THAT todo's
      own scope, not re-drafted here). The **decision on whether to feed `vix_features`** is a genuine DESIGN call —
      already tracked as its own `[DESIGN] P2` todo in
      `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` and explicitly excluded from
      dispatch by both this triage and batch2's own todo (same source doc, same exclusion) — NOT included here. What IS
      still open and genuinely checkable: confirm live that `VENUE_DATA_TYPE_CAPABILITIES` (or its current equivalent)
      declares CME `mbp_10`/`trades`/`tbbo` as billing-gated per the "Data-type × source priority" note in the closeout
      doc (1-month L3 + 1-year L1 entitlement), not as unrestricted full-history-available. Repo: unified-api-contracts
      (read-only verify, no edit). **Done when**: a recorded live grep/read of the current capability-declaration source
      confirming CME mbp_10/trades/tbbo are declared billing-gated (or a filed finding if they are NOT), appended to
      `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`'s Progress Log. Source:
      `tradfi_consolidated_closeout_2026_07_18.md` (native, lines 238-244), narrowed.

- [ ] [REVIEW] P2. **Verify the KRX equities intraday registry-vs-adapter mismatch fix still holds live, and separately
      confirm the FX KRW cell (`FX:SPOT_PAIR:KRW-USD`, daily) has no analogous registry-vs-adapter gap — audit-only.**
      Source native todo (lines 245-254), narrowed: the `mvp_mode` dead-gate decision bundled in the same native todo is
      a genuine DESIGN call, already independently tracked as its own doc
      (`plans/active/issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md`) that
      `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md` already classified "0 AO-eligible candidates... genuinely
      operator-gated" — NOT included here, stays with that classification. The "IBKR `_SEC_TYPE_MAP`/Databento
      `_resolve_product_root`/combo-leg" sub-clause is already DONE per the native todo's own text (single-leg todo
      `[x]` in `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`) — nothing to re-verify there. What's
      left: (a) live-confirm the fix in the (now-archived, `status: resolved`)
      `krx_intraday_ohlcv_registry_vs_adapter_mismatch_2026_07_12.md` still holds for KRX equities
      `ohlcv_1m`/`ohlcv_15m` (do not reopen/edit the archived doc — cite it, don't rewrite it); (b) confirm FX KRW's own
      capability declaration + adapter fetch path agree (same class of check, different venue/instrument_type — this is
      a DIFFERENT cell from KRX equities per the closeout's own explicit distinction). Repos: instruments-service,
      market-tick-data-service. **Done when**: a recorded live check for both (a) and (b), each with a pass/fail
      verdict + citation (live registry/adapter read for each), reported via this todo's own commit/dispatch outcome
      (the archived doc is cited, not edited). Source: `tradfi_consolidated_closeout_2026_07_18.md` (native, lines
      245-254), narrowed.

- [ ] [BACKEND] P2. **Audit every adapter/handler module under the 3 named tradfi directories for duplicate
      implementations, a runtime fallback masking a real failure, and dead (referenced-but-never-scheduled) code, per
      `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md`.** Source native todo (lines 259-266),
      unmodified — this is already precisely scoped in the closeout doc: audit
      `instruments-service/instruments_service/reference_data/adapters/tradfi/`,
      `market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/`, and the tradfi venue files
      under `execution-service/execution_service/trade_execution/adapters/`. Repos: instruments-service,
      market-tick-data-service, execution-service. **Done when**: a filed finding (or a stated "clean" verdict) per
      adapter directory, cited with file paths, recorded in a NEW
      `plans/active/issues/tradfi_adapter_dead_code_fallback_audit_2026_07_25.md` doc (do not write into the closeout
      plan directly — this batch's finalize plan reconciles the closeout's own checkbox once this lands). Source:
      `tradfi_consolidated_closeout_2026_07_18.md` (native, lines 259-266).

- [ ] [CODE] P2. **Wire a durable classification so billing-gated Databento L2/L3 entitlement-guard rejections
      (`mbp_10`/`trades`/`tbbo` outside the 1-month L3 / 1-year L1 window) do not count as `attempted_failed`.** Source
      native todo (lines 314-323), unmodified — a scoped code change: a new UAC `classify_venue_error()` outcome or
      `expected_reason` value recognizing the billing-entitlement-guard rejection, routing it to
      `empty_confirmed`/`expected_unattempted` instead of `attempted_failed`. Repos: unified-api-contracts,
      market-tick-data-service. **Done when**: a unit test asserts a simulated entitlement-guard rejection for
      `mbp_10`/`trades`/`tbbo` on a Databento tradfi shard yields 0 `attempted_failed` rows, PLUS a live manifest
      spot-check shows the count trending down after the fix ships; `quality-gates.sh --no-fix` green in both repos.
      Evidence is the shipped commit + test name + spot-check numbers (cited in this todo's own commit message; no
      separate markdown doc needed). Source: `tradfi_consolidated_closeout_2026_07_18.md` (native, lines 314-323).

- [ ] [REVIEW] P1. **Verify the data-status page (Upcoming expiries widget + catalogue view) now renders canonical
      tradfi ids, given catalogue Surface A shipped live since this native todo was written — plus confirm the
      venue-lookup gap fix still holds for tradfi.** Source native todo (lines 324-329), unmodified scope but
      **UN-BLOCKED**: at authoring time (2026-07-18/24) this todo was effectively blocked — the closeout's own
      Ground-truth verdict table showed catalogue `prod/catalog.parquet` at 0% canonical for derivatives. Live-checked
      2026-07-25 against `tradfi_manifest_content_recovery_completion_2026_07-24.md` directly: catalogue Surface A
      migration is now `[x]` **"SHIPPED + APPLIED LIVE 2026-07-25"** (`instruments-service@52d8b3ef`, 775,116/776,387 =
      99.84% canonical post-apply). This is a real, previously-unnoted prerequisite clearing — the parent closeout's own
      digest table still says "NOT yet executed," which is now STALE (flagged in this doc's frontmatter `summary`, not
      silently corrected in the parent). Given the prerequisite has landed, this verify task is now genuinely ready to
      run (a "still stale, rollup lag" finding is still an acceptable, valid outcome — not a mandate to force green).
      The `deployment_api_legacy_instrument_availability_venue_lookup_gap_2026_07_13.md` re-verify is a much smaller,
      independent, always-ready check (archived/resolved doc, cite don't edit). Repo: deployment-api (read-only verify).
      **Done when**: a live sample row from the "Upcoming expiries" widget/catalogue view is read and confirmed
      canonical (no raw `E3AN6     C7960`-style output, matching the Ground-truth verdict table's target shape) or, if
      still stale, the specific reason cited (e.g. rollup lag, not-yet-promoted); AND the venue-lookup gap fix is
      confirmed to hold for tradfi with a live citation. Recorded in
      `data_status_page_ux_and_canonicalisation_2026_07_16.md`'s Progress Log. Source:
      `tradfi_consolidated_closeout_2026_07_18.md` (native, lines 324-329).

- [ ] [REVIEW] P1. **Run the already-shipped distinct-values/axis-value census for `asset_group=tradfi` and confirm 0
      non-canonical values (or only explicitly-accepted cutover-register exceptions).** Source native todo (lines
      330-341), unmodified — call deployment-api's `GET /distinct-values/tradfi` and `GET /axis-value-census` against
      the current nightly rollup + manifest; confirm every distinct `instrument_type`/`data_type`/`chain`/`source`/
      `pipeline_mode`/`venue` value is canonical. Repo: deployment-api (read-only calls). **Done when**: a recorded run
      (date + endpoint response) appended to `distinct_values_noncanonical_audit_2026_07_20.md`'s live-evidence tables,
      confirming the exact dupes the 2026-07-18 audit found (`FUTURE`/`future`/`FUTURES`, `EQUITY`/`equity`, stale
      `barchart`) are 0 or explicitly explained per the doc's own accepted-exceptions register. Source:
      `tradfi_consolidated_closeout_2026_07_18.md` (native, lines 330-341).

- [ ] [BACKEND] P2. **Re-verify 3 named denominator/catalogue-completeness findings against live tradfi state.** Source
      native todo (lines 342-346), unmodified: (1) 875 tradfi atoms with narrowed historical objects + 153 duplicate KRX
      row_keys — re-measure against the (now-archived, `status: resolved`)
      `tradfi_instrument_type_migration_read_stale_legacy_object_2026_07_17.md`'s claimed repair, cite don't edit the
      archived doc; (2) phantom captures — re-measure the ICE/FX 309-phantom and blank-`data_type` 1,083-row counts in
      `phantom_captures_tradfi_2026_06_28.md` against live state, update that doc's own open `[CODE] P2` diagnosis item
      if the counts changed; (3) `expected_reason` misclassification P3s — re-verify against the (archived,
      `status: resolved`) `tradfi_expected_reason_attempted_failed_misclassification_2026_07_15.md`'s 2 residual P3
      items (a DESIGN taxonomy decision — stays human, do not resolve here — and an INVESTIGATE item on the original
      writer's identity — attempt the trace, report found-or-not-found either way). **Conflict precedence note**: this
      native todo is the exact "foothold" `tradfi_satellite_ao_dispatch_batch2_2026_07-25.md`'s Deferred section cites
      when excluding `data_completion_tradfi_2026_07_15.md`'s "⑫ FOLLOW `reconcile_phantom_manifest_rows_all.py`
      --dry-run re-run" candidate ("cites the SAME `phantom_captures_tradfi_2026_06_28.md` ground via a different
      mechanism") — that candidate stays deferred; this todo does NOT run that script, it re-measures counts only.
      Repos: instruments-service, market-tick-data-service. **Done when**: counts re-measured or explained as stale for
      all 3 findings, recorded in each finding's own doc (phantom_captures_tradfi_2026_06_28.md gets a live update; the
      2 archived docs are cited with fresh evidence, not edited). Source: `tradfi_consolidated_closeout_2026_07_18.md`
      (native, lines 342-346).

- [ ] [BACKEND] P2. **KRX name-column "STILL OPEN" tracking (added 2026-07-25) — confirm or execute the 2 named
      remaining pieces.** Source native todo (lines 392-400), unmodified: (a) the availability-manifest `name` column —
      per the parent P1 item's own STILL OPEN note this was **deliberately deferred** in favor of catalogue-as-SSOT +
      display-time join (manifest shard-atom/writer "owned by another agent") — this todo's job for (a) is to CONFIRM
      that decision still stands (not to implement the manifest column unilaterally, which would contradict the recorded
      ownership/preference note); (b) the catalogue regeneration that lands the `name` column LIVE — this is a standard
      `build_instrument_catalogue.py` rollup (the same rebuild pattern already used elsewhere in this doc family without
      an `[OPERATOR]` tag, e.g. the "FINAL STEP" catalogue rebuild+promote in
      `tradfi_backfill_throughput_followups_2026_07_24.md`) — run it if not already run since the 2026-07-20 "10 KRX
      rows and NO name column" sample check, then verify live. Repos: instruments-service, market-tick-data-service,
      deployment-api. **Done when**: (a) a recorded confirmation the catalogue-as-SSOT decision still stands (or, if
      it's genuinely changed, a filed new tracked todo — this todo does not itself implement the manifest column); (b) a
      live catalogue read shows the `name` column populated for KRX rows
      (`SK Hynix`/`Samsung Electronics`/`Hyundai     Motor` or equivalent), with the regen commit/run cited. Evidence
      reported via this todo's own commit/dispatch outcome (this batch's finalize plan updates the closeout's own "STILL
      OPEN" note). Source: `tradfi_consolidated_closeout_2026_07_18.md` (native, lines 392-400).

- [ ] [REVIEW] P2. **Run the adversarial AO-dispatch-readiness pass against `tradfi_consolidated_closeout_2026_07_18.md`
      itself, for the 3 categories the doc's own 2026-07-24 spot-check left "still owed."** Source native todo (lines
      418-430), narrowed: the doc's own in-line spot-check already confirmed clean for 3 of the 6 defect classes (bare
      `§X` cross-doc shorthand, ambiguous non-literal verbs, delete-risk `[OPERATOR]` tagging consistency) — do NOT
      re-check those 3, they're already recorded clean. This session's OWN triage pass (the one that produced this
      extraction doc) additionally spot-checked the parent's 13 native todos directly and found: (i) the parent's own
      Split-notice digest table is STALE relative to the child plan's live checkboxes (see this doc's frontmatter
      `summary` and the "why 3 of 13 are not here" section above — catalogue Surface A migration shows "NOT yet
      executed" in the digest but `[x]` "SHIPPED + APPLIED LIVE 2026-07-25" in the child); (ii) no digest-checkbox
      misuse found among the native todos checked (all real `- [ ]`/`- [x]`, the Aggregated-source-docs section
      correctly uses bold-no-brackets digest format). What's left for the full 6-category sweep: a formal stale-checkbox
      sweep (the digest-staleness above is one instance — check for more) and a formal missing-definition-of-done sweep
      across every native todo (this triage found all 13 DID carry a stated done-when, so this may resolve to a clean
      verdict — but the closeout doc's own todo asks for the sweep to be run and recorded formally, not just spot-
      checked). Repo: unified-trading-pm. **Done when**: a filed finding list (or a stated "clean" verdict) covering the
      2 remaining categories (stale checkboxes, missing definition-of-done), with any fixes applied directly to
      `tradfi_consolidated_closeout_2026_07_18.md` in the same commit, INCLUDING correcting the Split-notice digest's
      stale catalogue-migration line found by this extraction. This is the ONE todo in this batch that edits the
      closeout doc directly — no other todo in this batch touches that file. Source:
      `tradfi_consolidated_closeout_2026_07_18.md` (native, lines 418-430), narrowed to the 3 still-owed categories.

## Deferred — stays human (3 of the 13 native todos)

See "Why 3 of the 13 native todos are NOT here" above for the full reasoning per item:

1. **"Full MTDS+IS adapter smoke findings" re-verify** — substantively already resolved for tradfi (0 real tradfi-scoped
   open items across all 3 cited docs); not a dispatch candidate, a checkbox-flip candidate.
2. **"NEW 2026-07-24 — two live defects" (source-mislabeling + FX manifest id)** — the evidence-reconciliation sub-piece
   is already done (child plan's Phase-B todo is `[x]` RE-VERIFIED LIVE 2026-07-25); the defect-fixing sub-pieces remain
   exactly where `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s own Deferred section already, correctly, left
   them (conflict-gated against this same native todo) — not re-drafted here to avoid contradicting that finding.
3. **"BLOCKED-INFRA — Certify tradfi Layer-1"** — literal `BLOCKED-INFRA` marker, gated on
   `tradfi_backfill_throughput_followups_2026_07_24.md`'s still-pending "FINAL STEP" catalogue rebuild+promote (verified
   not yet done, live-checked 2026-07-25).

Also excluded (embedded judgment/design calls, narrowed OUT of the 3 native todos that got drafted above but were
originally bundled with real audit-eligible work): the `vix_features` 15m/24h-aggregation-writer DESIGN decision (stays
in `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`) and the `mvp_mode` dead-gate
DESIGN decision (stays in `issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md`, already classified "genuinely
operator-gated" by batch2).

## Reconciliation

Once a todo here ships, its evidence lands in the target/source doc named in its own text (or, for the 3 todos whose
natural target IS the closeout doc's own table/note text — todos 1 and 9 above — the evidence is recorded elsewhere and
the closeout doc itself gets updated by the finalize plan below, not by the individual todo, to avoid any todo other
than todo 10 touching that file). This plan's own reconciliation-then-archive step is machine-gated via a companion
`tradfi_consolidated_native_ao_extract_2026_07_25_finalize.md`
(`depends_on: [tradfi_consolidated_native_ao_extract_2026_07_25]`, `gate_on_depends: true`), mirroring the batch1/batch2
finalize-plan pattern.

## Codex SSOTs

No new durable contract is created by this plan — every todo executes an already-scoped verification/audit/code-change
from the closeout doc's own native todo text (narrowed where a judgment call was embedded).
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" is the standard
this extraction applied throughout.
