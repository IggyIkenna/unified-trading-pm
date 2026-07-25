---
doc_type: plan
title:
  TradFi registry/adapter correctness + honest-coverage residuals — Phase A2 + Phase C (forked from the closeout,
  2026-07-25)
summary: >-
  Forked from `tradfi_consolidated_closeout_2026_07_18.md`'s 2026-07-25 second-tier line-cap trim (mirrors the
  2026-07-24 3-way split pattern — see that plan's Split notice). Carries Phase A2 (adapter/registry correctness — CME
  capability declarations, KRX equities registry-vs-adapter mismatch, MTDS+IS adapter smoke findings, dead-code/fallback
  audit, the two live provenance defects) and the STILL-OPEN residue of Phase C (data-status/honest-coverage — billing-
  gated classification, data-status page canonical render, distinct-values census, denominator/catalogue-completeness,
  the KRX name-column follow-up, the BLOCKED-INFRA Layer-1 certify gate). The 2 fully-closed Phase C mega-verdicts that
  used to sit inline here (honest-coverage re-verification, KRX name-column shipment) moved instead to
  `tradfi_consolidated_closeout_history_2026_07_25.md` — pure historical record, not duplicated here. 8 AO-dispatch-
  readiness fixes applied during the move (2 broken cross-doc "above" references restated inline, 1 finding-H digest
  reformat, 1 missing self-justification added, 1 stale whole-plan gate relocated here, the `related:` gap closed on the
  parent, 2 bundled VERIFY+DECIDE todos split into a bounded verify + a non-dispatchable decision pointer). Several
  items already have AO-dispatchable derivatives drafted in `tradfi_consolidated_native_ao_extract_2026_07_25.md`
  (status: draft) — this doc keeps the NATIVE (non-duplicated) form only; see this doc's fork-note for the mapping.
status: draft
nature: process
asset_group: [tradfi]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    execution-service,
    deployment-api,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [tradfi, close-out, registry, adapter, honest-coverage, data-status, canonicalisation, plan-hygiene]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md,
    /plans/active/tradfi_backfill_throughput_followups_2026_07_24.md,
    /plans/active/tradfi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/tradfi_consolidated_native_ao_extract_2026_07_25_finalize.md,
    /plans/archive/2026_07/tradfi_consolidated_closeout_history_2026_07_25.md,
    /plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
    /plans/active/issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md,
    /plans/active/issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 0.96
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [tradfi_manifest_content_recovery_completion_2026_07_24, tradfi_backfill_throughput_followups_2026_07_24]
gate_on_depends:
  true # mechanism note: relocated verbatim from the parent's frontmatter (2026-07-25 line-cap trim, fix #6) — real
  # teeth only if this plan is ever flipped to assigned_vm: planning (documentation-only while NA, same idiom the
  # parent used pre-trim). Phase C's honest-coverage-gated-on-Phase-B residue (the still-open items below) is gated
  # on Phase B, which forked to tradfi_manifest_content_recovery_completion_2026_07_24; the BLOCKED-INFRA
  # "Certify tradfi Layer-1" todo is gated on the catalogue rebuild+promote "FINAL STEP", which forked to
  # tradfi_backfill_throughput_followups_2026_07_24. Encoded here so a future assigned_vm: planning flip of THIS plan
  # (or an AO-extraction drafted off its content) can't dispatch either item before its real prerequisite lands.
source: >-
  2026-07-25 second-tier line-cap trim of `tradfi_consolidated_closeout_2026_07_18.md` (927 lines, target ~690L after
  the trim). This fork carries Phase A2 + the STILL-OPEN residue of Phase C verbatim in substance, with the 8
  AO-dispatch-readiness fixes from that trim's design pass applied — see the fork-note below for the fix-by-fix
  rationale and the cross-check against `tradfi_consolidated_native_ao_extract_2026_07_25.md` (a sibling pass's
  AO-eligibility triage of the parent's OWN native todos, drafted the same day) that avoided re-drafting any item that
  pass had already covered.
---

# TradFi registry/adapter correctness + honest-coverage residuals

> **Forked 2026-07-25** from `tradfi_consolidated_closeout_2026_07_18.md` (second-tier line-cap trim — that parent had
> grown back to 927 lines since the 2026-07-24 3-way split; see its Split notice for that earlier precedent and its new
> "Phase A2 + Phase C — forked 2026-07-25" section for the pointer back here). Carries Phase A2 (adapter/registry
> correctness) and the STILL-OPEN residue of Phase C (data-status/honest-coverage) — the 2 items in Phase C that were
> already fully closed (honest-coverage re-verification, KRX name-column shipment) moved instead to
> `tradfi_consolidated_closeout_history_2026_07_25.md`, pure record, not duplicated here. Parent coordination index:
> `tradfi_consolidated_closeout_2026_07_18.md`. Siblings: `tradfi_manifest_content_recovery_completion_2026_07_24.md`,
> `tradfi_backfill_throughput_followups_2026_07_24.md`, `tradfi_phase_d_terminal_gate_2026_07_24.md`.

## Fork note — 8 AO-dispatch-readiness fixes applied during this move, and the native-extract overlap check

Read `tradfi_consolidated_native_ao_extract_2026_07_25.md` (status: draft, same-day sibling pass) before drafting any
NEW AO-dispatchable derivative of this doc's content — several items below already have one there (todos 2, 3, 4, 5, 6,
7, 8, 9 of that plan derive from the exact same underlying facts as this doc's A2/Phase-C items). This doc intentionally
keeps the NATIVE (non-AO-dispatched, `assigned_vm: NA`) form only, mirroring its 3 sibling children — it is not itself
an AO-dispatch surface; a future `/ag-closeout-audit` or similar pass drafts AO batches off ITS content the same way it
already has off the parent's.

Fixes applied (verbatim content preserved, only the specific defect corrected):

1. **CME mbp_10/trades/tbbo todo** — broken "see the note above" (the parent's MVP-universe section, not present here)
   restated inline: the Databento billing-entitlement fact is now stated directly in the todo below.
2. **Billing-gated Databento L2/L3 todo** — same broken "above" reference, same fix.
3. **KRX name-column STILL-OPEN todo** — broken "The P1 item above is `[x]`..." reference (the P1 item moved to history,
   no longer adjacent) rewritten to restate the shipped-code fact directly.
4. **"Two live defects" todo** — reformatted from a real checkbox to a non-checkbox bold digest pointer (finding H): its
   own linked issue doc's "Suggested next steps" are explicitly marked "not executed"/undecided, so no bounded action
   was actually stated; a future pass should scope a bounded first investigative step once the root-cause hypothesis is
   confirmed — not attempted here.
5. **KRX catalogue-rebuild+promote sub-item** — added an inline self-justification clause (same already-established
   rebuild-from-source + atomic-promote pattern used elsewhere in this plan family, never itself `[OPERATOR]`-gated) —
   not a raw delete, so no `[OPERATOR]` tag needed.
6. **Stale whole-plan gate** — `depends_on` + `gate_on_depends: true` relocated here from the parent (both items it
   protects — the honest-coverage-gated-on-Phase-B residue and the BLOCKED-INFRA cert item — live here now).
7. (Applies to the parent's `related:` list, not this doc.)
8. **CME mbp_10 todo + KRX-equities-mismatch todo** — each split into a bounded AO-eligible VERIFY-only todo plus a
   non-dispatchable `[DESIGN]`/`[DECISION]` pointer noting the companion decision stays open elsewhere (both decisions
   are independently tracked in their own source docs already).

## Phase A2 — adapter / registry correctness (so the MVP cells actually fetch + classify)

- [ ] [BACKEND] P1. **VERIFY: CME `mbp_10`/`trades`/`tbbo` `VENUE_DATA_TYPE_CAPABILITIES` declares billing-gated status,
      not full-history-available** —
      `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`. Databento tradfi's billing
      entitlement is 1-month L3 + 1-year L1, so `mbp_10`/`trades`/`tbbo` lookback/entitlement-guard rejections are
      billing-gated by design, not a bug. Gate: `VENUE_DATA_TYPE_CAPABILITIES` confirmed to declare mbp_10/trades/tbbo
      as billing-gated (declared possible, not chased to full L3 history) — a pure verify, no code change. (repos:
      market-tick-data-service, unified-api-contracts)
- **[DESIGN] P2.** Whether an `ohlcv_15m/24h` aggregation writer ships to feed `vix_features` (currently unfed) is a
  SEPARATE, still-open design decision — tracked in its own doc's `[DESIGN] P2` item
  (`tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`), not resolved by the verify todo
  above. Non-dispatchable pointer, not a real checkbox (finding H).
- [ ] [BACKEND] P2. **VERIFY: KRX equities intraday registry-vs-adapter mismatch fix still holds live, and the FX KRW
      cell (`FX:SPOT_PAIR:KRW-USD`, daily) has no analogous registry-vs-adapter gap** —
      `krx_intraday_ohlcv_registry_vs_adapter_mismatch_2026_07_12.md` (RESOLVED — this is about KRX equities
      `ohlcv_1m`/`ohlcv_15m` registry coverage, a separate cell from the FX KRW cell). **IBKR `_SEC_TYPE_MAP` /
      Databento `_resolve_product_root` / combo-leg** — already DONE in code
      (`canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`, single-leg todo already `[x]`; nothing to
      re-verify here). Gate: KRX-equities mismatch re-verified still resolved, and the FX KRW cell separately confirmed
      to have no registry-vs-adapter gap. (repos: instruments-service, market-tick-data-service)
- **[DECISION] P2.** The `mvp_mode` dead-gate decision (wire a real caller, or remove the dead path) is a SEPARATE,
  still-open design call, tracked in its own doc
  (`plans/active/issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md`) — genuinely operator-gated (already
  classified "0 AO-eligible candidates" by `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s own re-triage).
  Non-dispatchable pointer, not a real checkbox (finding H) — not resolved by the verify todo above.
- [ ] [BACKEND] P2. **Full MTDS+IS adapter smoke findings** — `mtds_is_full_adapter_smoketest_findings_2026_07_07.md`,
      `instruments_remaining_work_audit_2026_07_10.md` (tradfi slice),
      `uac_data_type_validity_combinator_fragmentation_2026_07_07.md`. Gate: every open finding in the 3 cited docs
      re-verified current against live tradfi state or re-filed as its own tracked todo.
- [ ] [BACKEND] P2. Audit every adapter/handler module under
      `instruments-service/instruments_service/reference_data/adapters/tradfi/`,
      `market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/`, and the tradfi venue files
      under `execution-service/execution_service/trade_execution/adapters/` for duplicate implementations, a runtime
      fallback masking a real failure, and dead (referenced-but-never-scheduled) code, per the rule in
      `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md`. Definition-of-done: a filed finding (or a
      stated "clean" verdict) per adapter directory, cited with file paths, recorded in this plan's Progress Log or a
      new `plans/active/issues/` doc. (repos: instruments-service, market-tick-data-service, execution-service)
- **[BACKEND] P1.** NEW 2026-07-24 — two live defects found by the raw-tick reconciliation's 3rd run: (1) ICE/KRX/FX
  (all Yahoo-exclusive per SSOT) captured under `source=databento` since ~2026-07-18 (real values, wrong provenance
  stamp, root cause not yet found — hypothesis: the 2026-06-24 DATABENTO-FIRST change missing a per-venue
  `_VENUE_SOURCE_EXCLUSIONS` guard); (2) FX `SPOT_PAIR` manifest `instrument_id` is 0% well-formed across its entire
  2020-2026 captured history (the GCS object + content are fine — this is a pure manifest-copy defect). Positive
  counter-finding same run: captured-row id-form canonicality measured ~99.3% corpus-wide (up from the 07-21 report's
  30.8%), independently corroborated by a 99.95%-clean reconstructed-path check — strong evidence the Phase-B migration
  in `tradfi_manifest_content_recovery_completion_2026_07_24.md` has substantially landed (**that plan's Surface-B
  manifest-migration todo is now confirmed `[x]` "RE-VERIFIED LIVE 2026-07-25"** — verified live 2026-07-25 during this
  fork; the evidence-reconciliation action is done). **Not a real checkbox** (finding H, applied 2026-07-25) — this
  doc's own "Suggested next steps" are explicitly marked "not executed"/undecided, so no bounded action is stated yet; a
  future pass should scope a bounded first investigative step once the root-cause hypothesis is confirmed, rather than
  this fork guessing one. Full evidence + the `_quarantine/` register going stale (146K→400K+ objects in 3-4 days,
  register still says "deleted"): `/plans/active/issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`.
  (repos: market-tick-data-service, unified-api-contracts, unified-trading-pm)

## Phase C — data-status + honest-coverage (still-open residue only — closed verdicts live in the history companion)

- [ ] [CODE] P2. **Billing-gated Databento L2/L3 cells must not count as `attempted_failed`.** Databento tradfi's
      billing entitlement is 1-month L3 + 1-year L1, so `mbp_10`/`trades`/`tbbo` lookback/entitlement-guard rejections
      are EXPECTED, not real failures — but no classification mechanism currently excludes them, so a hit outside the
      entitlement window records `attempted_failed` today. Wire a durable classification (a new UAC
      `classify_venue_error()` outcome or `expected_reason` value) that recognizes the billing-entitlement-guard
      rejection and routes it to `empty_confirmed`/`expected_unattempted` instead of `attempted_failed`.
      Definition-of-done: a unit test asserting a simulated entitlement-guard rejection for `mbp_10`/`trades`/`tbbo` on
      a Databento tradfi shard yields 0 `attempted_failed` rows, plus a live manifest spot-check showing the count
      trending down after the fix ships. (repos: unified-api-contracts, market-tick-data-service)
- [ ] [BACKEND] P1. **Data-status page renders canonical tradfi** (the "Upcoming expiries" + instruments/catalogue
      views) — `data_status_page_ux_and_canonicalisation_2026_07_16.md`; deployment-api legacy venue-lookup gap
      (`deployment_api_legacy_instrument_availability_venue_lookup_gap_2026_07_13.md`, RESOLVED — verify tradfi). Gate:
      the "Upcoming expiries" widget + catalogue view render canonical ids for a live sample row (no raw
      `E3AN6     C7960`-style output), and the venue-lookup gap fix is confirmed to hold for tradfi.
- [ ] [REVIEW] P1. **Run the already-shipped distinct-values/axis-value census for tradfi and verify 0 non-canonical** —
      deployment-api `GET /distinct-values/{asset_group}` + `GET /axis-value-census`
      (`deployment-api/deployment_api/routes/data_status/_distinct_values.py` + `_axis_census.py`; tracked corpus-wide
      in `/plans/active/distinct_values_noncanonical_audit_2026_07_20.md`). Call both endpoints for `asset_group=tradfi`
      against the current nightly rollup + manifest and confirm every distinct
      `instrument_type`/`data_type`/`chain`/`source`/`pipeline_mode`/`venue` value is canonical (0 non-canonical, or
      only explicitly-accepted exceptions per the cutover register) — the exact dupes the 2026-07-18 audit found
      (`FUTURE`/`future`/`FUTURES`, `EQUITY`/`equity`, stale `barchart`) must be 0 or explained. Definition-of-done: a
      recorded run (date + endpoint response, or a link to the refreshed
      `distinct_values_noncanonical_audit_2026_07_20.md` ground-truth table) showing the tradfi row. (repos:
      deployment-api)
- [ ] [BACKEND] P2. **Denominator / catalogue-completeness + new untracked findings** — 875 tradfi atoms with narrowed
      historical objects + 153 duplicate KRX row_keys
      (`tradfi_instrument_type_migration_read_stale_legacy_object_2026_07_17.md`); phantom captures
      (`phantom_captures_tradfi_2026_06_28.md`); expected_reason misclassification P3s. Gate: each of the 3 cited
      findings re-verified against live tradfi state (counts re-measured or explained as stale) and recorded.
- [ ] [BACKEND] P2. **NEW 2026-07-25 (plan-reconcile) — track the KRX name-column "STILL OPEN" work as a real todo, not
      just prose behind a checked box.** The KRX name-column code (4/4 read surfaces) shipped 2026-07-20 —
      instruments-service@6780f10e, uac@f7e0301d, deployment-api@65f5593, deployment-ui@2ff1e61; ship gate 4712 passed/0
      failed/3 skipped — but 2 pieces of follow-up work were never separately tracked: (a) the availability-manifest
      `name` column (owned by another agent — the manifest's shard-atom/writer, not the catalogue) — deliberately
      deferred there in favor of catalogue-as-SSOT + display-time join; (b) the catalogue regeneration that actually
      lands the name LIVE (distinct from the code shipping — confirm this has happened since the 2026-07-20 "10 KRX rows
      and NO name column" sample check, or run it; this is the same already-established rebuild-from-source +
      atomic-promote pattern used elsewhere in this plan family — the catalogue rebuild+promote "FINAL STEP" already
      referenced in `tradfi_backfill_throughput_followups_2026_07_24.md`, never itself `[OPERATOR]`-gated — not a raw
      delete, so no `[OPERATOR]` tag is needed here either). **Done when**: either both are confirmed already done with
      fresh evidence (a live catalogue read showing the `name` column populated for KRX rows), or both are executed and
      verified. Full shipped-KRX-name-column narrative (verification samples, the gate-blocked-for-4h detour, the
      residual DeFi coverage-honesty finding):
      `/plans/archive/2026_07/tradfi_consolidated_closeout_history_2026_07_25.md`. Repos: instruments-service,
      market-tick-data-service, deployment-api.
- [ ] [VERIFY] P0. 🚧 BLOCKED-INFRA — **Certify tradfi Layer-1** — post the v9 migration + rebuild + IS catalogue (Plan
      2), record the fresh tradfi denominator + %. Gate: tradfi number recorded; all 5 AGs now canonical-and-measured.
      **STILL BLOCKED 2026-07-21 (only PARTIALLY unblocked)**: the v9 manifest migration/rebuild are done (task 10,
      2026-07-16), but the served catalogue has not yet been rebuilt/promoted for the +409 MVP expansion
      (`uac@afa2dd64`→`22e6a534`) — so the fresh tradfi denominator this todo must record is not yet final. Gated on the
      pending catalogue rebuild + promote (see `tradfi_backfill_throughput_followups_2026_07_24.md` "FINAL STEP"), not
      cleanly runnable yet. (FOLDED IN from layer1_remeasure_and_certify_2026_07_06, 2026-07-15, plan-reconcile §6
      operator ruling)

  **Note (2026-07-24)**: relocated verbatim from `tradfi_v9_stage1_finish_2026_07_06.md`'s "Folded-in scope 2026-07-15"
  section during the plan-hygiene line-cap remediation (that plan is now archived, 0 remaining open todos). The "FINAL
  STEP" this todo's gate cites lives on the sibling `tradfi_backfill_throughput_followups_2026_07_24.md` (gated on
  backfill completion — rebuild+promote the served catalogue so `mvp=True` reflects the +409 expansion) — see that child
  for the current status. **Re-confirmed still blocked 2026-07-25** (live-checked during this fork): the "FINAL STEP" is
  still pending as of that date (`tradfi_backfill_throughput_followups_2026_07_24.md`: "currently still old 70,930 set;
  new groups not yet flagged").

## Plan-quality — AO-dispatch-readiness pass (owed, fresh copy for this child's own content)

- [ ] [REVIEW] P2. Run the same adversarial AO-dispatch-readiness pass (`task_template.md` §3's finding taxonomy A-S)
      against THIS doc's own A2 + Phase C content, re-checked as this child's content evolves rather than treated as
      permanently satisfied by the 2026-07-25 fork's own pass (see `tradfi_consolidated_closeout_2026_07_18.md`'s
      Plan-quality section for that pass's 8 fixes, closed the same day this child was created). Definition-of-done: a
      filed finding list (or a stated "clean" verdict) covering every defect class in `task_template.md` §3, with any
      fixes applied directly or filed as follow-up todos.

## Codex SSOTs (read before touching a phase)

`/codex/02-data/tradfi-databento-sourcing-ssot.md`, `/codex/02-data/availability-manifest-and-data-status.md`,
`/codex/02-data/honest-coverage-model.md`, `/codex/02-data/pipeline-mode-partition.md`,
`/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`,
`/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md`, `/codex/05-infrastructure/vm-launcher-runbook.md`.
