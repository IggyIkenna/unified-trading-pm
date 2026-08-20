---
doc_type: plan
title:
  Prediction Phase A-B residuals — code-ready writers + manifest migration follow-through (split from
  prediction_consolidated_closeout_2026_07_18)
summary: >-
  Phases A (get-the-code-ready — capture path, canonical-identity writers, venue-perps residuals, fixture-attribute
  writers) and B (manifest/catalogue migrations) of the prediction consolidated close-out, split out verbatim (line-cap
  remediation, 2026-07-24) — most items already shipped and verified. **Residual open work corrected 2026-08-19
  (/plan-reconcile predictions_master, was stale — 4 of the 5 previously-named items here had already closed)**: the
  manifest enumeration-driven canonical/dedupe migration `--apply`, the historical fixture-match-attribute backfill,
  the `instrument_type` casing re-verify to 100%, and the 3x-cadence reconciliation top-up (4 open `- [ ]` todos,
  live-recounted 2026-08-19, matching this doc's own 2026-08-18 na-eligibility-audit marker).
status: active
nature: process
asset_group: [prediction]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-service,
    deployment-api,
    deployment-ui,
    features-service,
    e2e-testing,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [
    prediction,
    close-out,
    capture-incident,
    canonical-identity,
    manifest,
    canonicalisation,
    fixture-attributes,
    venue-perps,
    clob-depth,
  ]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_phase_c_data_status_ui_2026_07_24.md,
    /plans/active/prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md,
    /plans/active/prediction_phase_e_football_arb_live_2026_07_24.md,
    /plans/active/prediction_capture_incident_remediation_2026_07_06.md,
    /plans/archive/2026_07/prediction_perps_kalshi_polymarket_parked_2026_07_24.md,
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-31" # was 2026-07-30 — flipped A5 (adapter dead-code/fallback audit) to DONE: 2 dead-code findings filed as issue docs (is_polymarket_dead_fixture_cross_reference_2026_07_31.md, mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md), 0 fallback/duplicate-implementation violations found. Prior: was 2026-07-26 — /plan-reconcile prediction shard corrected the A1 Kalshi-smoke-matrix todo's per-todo repo attribution (e2e-testing, not MTDS-only); no checkbox changes. 2026-07-25 — consolidated-closeout split pass added 2 todos relocated from the parent (adapter dead-code audit as new A5; merged reconciliation-cadence + duplicate-note in Phase B) + folded the POLYMARKET schema-extension ruling into the existing A2 todo (no new checkbox); open-todo count 11 -> 13. 2026-07-27 — batch2 todo-2 conflict-check re-verified item 9's instrument_type residual case-insensitively (still open, 176 genuinely-malformed rows, blank sub-population actively growing ~10/day); added new Phase-B P2 todo for the growing-blank finding; open-todo count 13 -> 14. 2026-07-30 — `prediction_satellite_ao_dispatch_batch1_finalize_2026_07_25.md` todo 1 reconciliation: flipped A1b (dead Kalshi host), A2a (canonical-identity migration, now 8/8), A2b (route writer through canonical builder), and A2c (POLYMARKET legacy dual-write trees) to DONE citing batch1's 7 commits; A1a annotated but stays open (Phase 6 fix still outstanding); open-todo count freshly re-verified live (not trusting either historical figure) at 9 of 19 total (was 14 pre-reconciliation)
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
sequential: true
source: >-
  Split from `prediction_consolidated_closeout_2026_07_18.md` (Phase A section, lines 177-266, and Phase B section,
  lines 267-343, of that doc as of 2026-07-18/2026-07-24) per the operator-approved line-cap remediation triage
  `/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md` (row 22, "4-way split along the plan's own Phase A-E
  boundaries"). Content moved verbatim, not summarized. Phase A and Phase B are combined into one child per the triage's
  specific guidance for this plan ("Phase A-B residuals"). `sequential: true` added 2026-07-24 (plan audit finding) to
  encode this doc's own "Phase B — run the migrations (gated on Phase A green)" header text as a real ordering — this is
  a WITHIN-plan A-before-B ordering, not a cross-plan gate, so `sequential` (not `depends_on`) is the correct mechanism.
context_scope:
  [
    /plans/active/prediction_capture_incident_remediation_2026_07_06.md,
    /codex/02-data/reconciliation-finding-taxonomy.md,
    /codex/02-data/canonical-cutover-register.md,
    market-tick-data-service/scripts/canonicalize_prediction_manifest_2026_07_18.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/manifest_finalize.py,
  ]
---

# Prediction Phase A-B residuals — code-ready writers + manifest migration follow-through

> **Split from `prediction_consolidated_closeout_2026_07_18.md` (2026-07-24).** This is the Phase A + Phase B sections
> of that close-out, moved verbatim (Phase A = get-the-code-ready; Phase B = run the migrations, gated on Phase A
> green). For the full historical execution narrative (Progress Log, ticks 1-31, 2026-07-18 through 2026-07-20) and
> shared cross-phase context (the Ground-truth verdict table, the prediction shard-atom definition — the CQG-bundle vs
> per-CID `instrument_type` key distinction that is the root of the Phase-B canonicalisation work below — and the MVP
> universe scope), see the parent doc. Sibling phase children: `prediction_phase_c_data_status_ui_2026_07_24.md` (Phase
> C), `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md` (Phase D),
> `prediction_phase_e_football_arb_live_2026_07_24.md` (Phase E — gated on this plan + Phase D, since this plan carries
> the Phase-B fixture-attribute backfill Phase E depends on).

## Phase A — get ALL the code ready (writers live+batch · adapters · migration scripts · fixture-attribute writers)

> Nothing migrates until every WRITER emits the canonical shape and the capture path is honest. Includes the fixture
> attribute-writer work (Phase E depends on it) so the Phase-D re-backfill already carries the new columns.

### A0 — Enumerate the live prediction dimensions FIRST (single source of truth)

- [x] ✅ [AUDIT] P0. **Enumerated the FULL distinct prediction dimension set from live prod GCS (slot-2, 2026-07-18)** —
      manifest `availability_index` 756,817 rows + catalogue `prod/catalog.parquet` 2,900,318 rows; see Progress Log §
      A0. **Non-canonical/dedupe targets found (drive Phase B), catalogue = SSOT:** (1) `data_type` DUPE
      `prediction_trades` vs canonical `trades`; (2) manifest `instrument_type` 18 distinct — canonical
      `PREDICTION_MARKET` mixed with lowercase dupes `prediction`/`prediction_market` + underlying-asset LEAKAGE
      (BTC/ETH/SPX/DJIA/NDX/GOLD/SILVER/CRUDE_OIL/DOGE/XRP/BNB/HYPE/OTHER) + `''`, while the catalogue is clean
      (`PREDICTION_MARKET` only); (3) `source` empty `''`; (4) catalogue `base_asset` 572,211 distinct raw market-title
      text w/ leading-whitespace dupes. **Clean:** CQG (81 canonical UPPERCASE values, no dupes) + catalogue
      `instrument_type`. Reusable reads: scratchpad `enumerate_prediction_dimensions.py` /
      `count_prediction_baseline.py`. (repos: instruments-service, market-tick-data-service)

### A1 — Capture path honest + live (fold: capture-incident remediation)

- [x] ✅ [BACKEND] P0. **DONE 2026-08-15 (plan_reconciler) — Phase 6 fully shipped.** Finish the prediction
      capture-incident remediation — harden the capture path (consolidator utf8 typing, backfill the 07-01→07-06 missed
      window) and confirm the KALSHI/POLYMARKET-PERP adapters no longer hit the wrong Kalshi host (the fake-PERPETUAL
      cefi contamination). `prediction_capture_incident_remediation_2026_07_06.md` (**CORRECTED 2026-08-16
      (plan_reconciler)**: 7 open, not 9 — Phase 6's 2 items are now `[x]` DONE 2026-08-15; all 7 remaining are
      `[DESCOPED-NOT-MVP 2026-07-14]` parked pending the perps prod-access operator ruling). **Reconciled 2026-07-30 (`prediction_satellite_ao_dispatch_batch1_2026_07_25.md` todos
      2+3, via the batch1 finalize plan) — NOT a clean close, still open.** Batch1 closed 2 items in that doc: todo 2
      quantified + root-caused the "fake-PERPETUAL contamination" question (the `KXMVE*` event family IS captured
      correctly; the REAL bug is 79% of Kalshi volume also landing in `canonical_question_group=OTHER` due to a one-line
      write-time bug at `instruments-service/instruments_service/engine/orchestrator/prediction.py:95` — filed as that
      doc's new Phase 6, NOT implemented) and todo 3 shipped the Phase 5 write-time `*-PERP` guardrail
      (`instruments-service@a4137022`, now flipped there). Phase 6's CQG-bucketing fix + its backfill-assessment
      follow-up are the only genuinely open work remaining; this checkbox stays open until Phase 6 ships. (repos:
      market-tick-data-service, unified-trading-library, deployment-service) **na-eligibility-audit 2026-08-03
      (blocker-currency check): Phase 6's CODE fix has now SHIPPED** —
      `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 1 (`status: active`, `assigned_vm: planning`) landed
      it `instruments-service@e0f7aaad` (2026-07-30, verified: 3/3 `test_prediction_canonical_group_shard.py -k kalshi`
      pass at HEAD) and that same todo confirms Phase 6's checkbox in the source doc
      (`prediction_capture_incident_remediation_2026_07_06.md`) is flipped too. This checkbox stays open here
      nonetheless — the remaining scope is exactly Phase 6's OWN backfill-assessment follow-up, which that source doc
      labels **"operator/architect call, not a mechanical todo"** (assess whether the historical `OTHER`-bucketed Kalshi
      rows are worth a backfill/reclassify pass, per the data-pipeline-correctness "fix in FULL" bar vs. practical cost)
      — a genuine judgment call, not something a worker can close alone. `assigned_vm` untouched. **RULED 2026-08-07
      (operator, via consolidated NA-blocker-digest audit) — YES, backfill/reclassify the historical `OTHER`-bucketed
      Kalshi rows, AND delete the bad classifications from both GCS objects and the manifest** (not an in-place relabel
      — the mis-bucketed rows get removed/replaced, matching the data-pipeline-correctness "fix in FULL" bar). Actual
      execution tracked in `prediction_capture_incident_remediation_2026_07_06.md` Phase 6 (the doc that structurally
      owns this backfill-assessment item) — see that doc for the real todo. **na-eligibility-audit 2026-08-10: citation
      gap closed** — that Phase 6 item has since been independently extracted, verbatim, into
      [`prediction_satellite_ao_dispatch_batch10_2026_08_09.md`](/plans/archive/2026_08/prediction_satellite_ao_dispatch_batch10_2026_08_09.md)
      (Source cites `prediction_capture_incident_remediation_2026_07_06.md` Phase 6's second checkbox verbatim) —
      batch10 landed and its finalize plan reconciled both source docs; both batch10 docs are now archived complete
      (2026-08-10). **Landing verified 2026-08-15 (plan_reconciler)**: `instruments-service@d4e5c23d` ("add Kalshi
      historical OTHER-bucket CQG reclassify script") is a confirmed ancestor of `origin/live-defi-rollout`. The
      commonly-cited `instruments-service@e0f7aaad` ("fix(prediction): extract bare Kalshi ticker before CQG
      classification") is NOT itself an ancestor — it lives only on
      `origin/wip-preserve/slot-5-instruments-service- diverged-20260805T111826Z` (the same rebase-drift class the
      batch6 parent-SHA finding documents elsewhere in this corpus) — but its content landed verbatim under the rebased
      SHA `instruments-service@94f3ee11` (identical commit message, confirmed ancestor of `origin/live-defi-rollout`).
      This checkbox stays closed on that corrected citation.
- [x] ✅ [BACKEND] P0. **DONE 2026-07-30 (reconciling `prediction_satellite_ao_dispatch_batch1_2026_07_25.md` todo 1).**
      Kill the dead Kalshi `trading-api.kalshi.com` host reintroduced into the smoke matrix + add the regression check
      that the elections-subdomain plan Phase 4 never added; fix the `raw_tick_data/by_date/` drift.
      `issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`. **Both legs closed**: (1) the dead-host +
      regression-check leg — `e2e-testing@371ac1b` repoints `_fetch_kalshi_instruments()` at `api.elections.kalshi.com`
      (was `trading-api.kalshi.com`, 401s since the 2026-05-20 migration); new
      `tests/unit/test_validate_batch_live_smoke_matrix.py` scans the module's own source for the dead host string (not
      just the one call site) so a third reintroduction anywhere in the file fails the build. (2) the
      `raw_tick_data/by_date/` drift leg — separately confirmed + fixed via that issue doc's own 2026-07-27/28 entries
      (not batch1's work): the ~29-day live-capture stall was root-caused (no producer VM/Cloud Run running anywhere in
      the fleet) and relaunched (`prediction_satellite_ao_dispatch_batch5_2026_07_26.md` todo 4 — 4 fresh
      `prediction-live-{venue}-{data_type}` VMs, manifest-confirmed captures through `day=2026-07-27`). (repos:
      **e2e-testing** — `e2e-testing/scripts/validation/validate_batch_live_smoke_matrix.py:552` +
      market-tick-data-service for the `by_date/` drift leg)
- [x] ✅ [BACKEND] P1. **STALE — CLOSED 2026-07-31 (na-eligibility-audit, prediction tranche).** Adapters must apply
      lifecycle bounds BEFORE the network call — today inactive days land as `SOURCE_RETURNED_ZERO` instead of an honest
      `EXPECTED_*`, and the CLOB catalogue scoped to `end_date_iso==day` can cap backfills to the resolution day. **Its
      own source doc is now fully resolved and archived**:
      `/plans/archive/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md` (all 5 todos
      done — pre-fetch gate `market-tick-data-service@abe0904d`, active-window catalogue widening
      `instruments-service@41ca79d7`, historical re-backfill terminal 2026-07-30, full-corpus VERIFY 81.8%
      captured÷attempted). This checkbox described the same deliverable and was simply never flipped once the source doc
      landed. (repos: market-tick-data-service). **Reconciled 2026-07-26** (resolved
      `autonomous_session_operator_decisions_2026_07_25.md` entry #13, option A) against
      `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` todo 1's overlapping lifecycle-bounds legs — this todo's
      `EXPECTED_*` target state is the ratified contract (already an `OUT_OF_COVERAGE_WINDOW_REASONS` member, clipped
      from the denominator); batch4 todo 1 leg (3) was rewritten to match instead of removing the enum members.

### A2 — Instrument-id / underlying / CQG writers converge (fold: canonical-identity migration)

- [x] ✅ [BACKEND] P0. **DONE 2026-07-30 (reconciling `prediction_satellite_ao_dispatch_batch1_2026_07_25.md` todo 7) —
      8/8 done.** Finish the prediction canonical-identity migration — was 7/8 done (confirmed 2026-07-19), only todo 2
      open. Shipped: todos 1/3/4/5 (`instruments-service@0d0c3742` — adapter `underlying` from
      `classify_*_to_canonical_group`, cross-venue `canonical_instrument_id`, titles-map decision, Polymarket sports
      `build_fixture_id`) + todo 6 as VERIFY (`unified-trading-pm@16272205a` — downstream `instrument_id` uniqueness
      SAFE, venue embedded by construction) + todo 7 (`unified-api-contracts@511a9c62` — `gcs_paths.py` bucket
      abbreviation flip, migration gate re-confirmed live 2026-07-19: legacy `market-data-tick-prediction-prd-*` 404s,
      `market-data-tick-pred-prd-*` is the sole live SSOT) + todo 8 (MDPS UAC-pin — assessed 2026-07-19, NO bump needed;
      the MDPS→UAC dep is an in-workspace editable range-pin that absorbs the 0.x flip by design; MDPS assertions
      already reconciled at `market-data-processing-service@27bce46`/`@5febb77`). **Todo 2 (full `prod/catalog.parquet`
      regen) is now CLOSED too — RESOLVED-BY-VERDICT, not executed.** The remaining question was whether the
      daily/weekly `lifecycle-catalogue-regen-prediction` cron already carries the shipped `underlying` + cross-venue
      `canonical_instrument_id` fields through, making a fresh manual regen redundant.
      `prediction_satellite_ao_dispatch_batch1_2026_07_25.md` todo 7 (read-only, unified-trading-pm) answered **YES**:
      code proof (`build_instrument_catalogue.py:2081-2088` carries the fields straight through from whatever the
      per-date snapshot recorded) + execution proof (the daily job has run clean every day 2026-07-16→2026-07-27; the
      weekly full re-walk ran 2026-07-11/18/25, all post-fix) + data proof (live `prod/catalog.parquet` read 2026-07-27
      shows the expected step-change: pre-fix rows 2.0%/0.3% populated for `underlying`/`canonical_instrument_id` vs
      post-fix rows 78.3%/4.6%). Full evidence in this doc's Progress Log (2026-07-27T18:00Z entry). The staged manual
      regen adds nothing beyond what the cron already does; the only unresolved residual (permanently-`""` pre-fix
      legacy rows, since the by-date snapshots themselves are never retroactively regenerated) is a distinct
      retroactive-backfill question, out of this todo's scope and not something the manual regen would have fixed
      either. Source: `prediction_canonical_identity_migration_2026_07_08.md` (folded in + archived 2026-07-21,
      consolidation pass — all other todos resolved, this was its sole remaining open item). **Phase-E Leg-1 seam** =
      todo 5 (done Polymarket; Kalshi extended in Phase E). (repos: instruments-service, unified-api-contracts)
- [x] ✅ [BACKEND] P1. **DONE 2026-07-27 (`prediction_satellite_ao_dispatch_batch1_2026_07_25.md` todo 6, slot-9) —
      reconciled 2026-07-30.** Route every prediction id/underlying/CQG writer through the shared canonical builder + a
      QG that fails a non-canonical prediction `instrument_id`/`canonical_question_group` on write — re-drift
      prevention, so new writes can't reintroduce the dupes A0 enumerates. `unified-api-contracts@08d48757`: new
      `validate_prediction_instrument_type()` / `validate_canonical_question_group()` guardrail
      (`canonical/domain/predictions/write_guard.py`), re-exported from the `predictions` facade, mirroring the CeFi
      `*-PERP` write-guard pattern; new `tests/unit/test_prediction_write_guard.py` — the new QG the todo requires —
      asserts both functions raise on every A0-enumerated dupe (lowercase `prediction`/`prediction_market`,
      underlying-asset leakage `BTC`/`ETH`/etc., case-mismatched CQG) and pass on canonical values.
      `instruments-service@517baeb9`: Kalshi + Polymarket adapters call `validate_canonical_question_group()` at every
      `canonical_question_group` computation site; Polymarket's `instrument_type` literal now uses the `InstrumentType`
      enum (matches Kalshi's convention). `market-tick-data-service@b7272103`: the REAL live bug —
      `kalshi_adapter.py`/`polymarket_adapter.py` previously hand-rolled `instrument_id` as a raw f-string and stamped
      lowercase `instrument_type="prediction_market"`, diverging from every live WS connector (uppercase
      `PREDICTION_MARKET`) and the catalogue SSOT; `instrument_id` now routes through `build_canonical_instrument_id()`,
      `instrument_type` uses `InstrumentType.PREDICTION_MARKET.value`, `canonical_question_group` is validated once per
      distinct classifier cache key. All 3 repos' `quality-gates.sh` green. (repos: instruments-service,
      market-tick-data-service, unified-api-contracts)
- [x] ✅ [BACKEND] P1. **DONE — reconciled 2026-07-30. NEW 2026-07-24 — POLYMARKET raw-tick data found living under ≥4
      structurally-distinct GCS path trees for the SAME shard (content-verified, byte-matching); the UAC oracle passes
      ALL of them as canonical (structure-only blindness). One tree (10-segment,
      `data_source=`/`market_category=`/`market_type=`/ `resolution_period=`) has NO manifest column at all — genuinely
      unrepresentable, not just unmigrated — and carries `title`/`slug`/`eventSlug` market-question text the canonical
      schema drops (metadata-loss risk, no delete suggested). Separately, manifest `data_type=prediction_trades` (2,477
      rows, still being written 2 days before the audit) is a genuine non-canonical axis value, not a
      `migration_pending` case.** No writer identified yet for the legacy shapes (deferred to the issue doc's own todo,
      a code-read task). Full evidence + 3 open questions (Q1 catalogue metadata recoverability, Q2
      still-being-written?, **Q3 retro-register vs migrate/purge — RULED 2026-07-25 (operator): extend the canonical
      `trades` schema to preserve the trader-identity + market-question + outcome-label content, then migrate — not drop
      the metadata, not leave it permanently forked**):
      `/plans/archive/issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md`. (repos:
      market-tick-data-service, unified-api-contracts, instruments-service) **Schema-extension migration (relocated
      2026-07-25 from the parent's "Queued audits + reviews" section, folded into this todo rather than opened as a new
      checkbox — same issue doc, same underlying finding):** per the Q3 ruling above, a 3-step sequence tracked in full
      detail in the linked issue doc — (1) design the extended canonical `trades` schema (2,477 manifest rows + the
      related ~158+-object non-canonical deep-tree shape both need a home), (2) implement the writer update + migrate
      the existing rows, (3) register the new shape in the cutover/non-canonical-path inventories. **Done when**: all 3
      steps are checked with evidence in
      `/plans/archive/issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md` itself (that
      doc's own todos remain the source of truth for step-by-step evidence); this bullet is satisfied once that doc
      shows all 3 checked. **Trader-identity/PII fields sub-question RULED 2026-07-28** (the one piece of step 1 the
      issue doc flagged as needing "a separate call"): a corpus-wide grep for
      `proxy_wallet`/`pseudonym`/`profile_image`/`name` across execution-service, strategy-service, features-service,
      ml-service, deployment-api, deployment-ui, and unified-trading-system-ui returns zero downstream consumers — the
      only hits are inside market-tick-data-service's own Polymarket adapter, which already drops them at ingest
      (confirmed live in `unified-api-contracts/unified_api_contracts/registry/_schema_spec_prediction.py`'s current
      docstring). Applying the doc's own "confirm real downstream need first" recommendation as a bounded, checkable
      task rather than an open privacy debate: no consumer exists today, so the trader-identity/PII fields are EXCLUDED
      from the canonical `trades` schema permanently (matches the already-shipped default). No further design/privacy
      decision is outstanding on this sub-item. **All 3 schema-extension steps + the Q1/Q2 diagnostic legs are now
      checked in the linked issue doc — this bullet's own Done-when is MET.**
      `prediction_satellite_ao_dispatch_batch1_2026_07_25.md` todo 5 (slot-12, read-only) closed the Q1/Q2 diagnostic
      legs: (a) all 3 legacy path shapes (#3/#3b/#4) are HISTORICAL, none written by any live code path today (shapes
      #3/#3b are the pre-2026-04-19 Polymarket-adapter drift, fixed forward by `da270f9b`/`ca246a9b`; shape #4 was
      produced solely by the now-deleted one-off `migrate_polymarket_canonical.py`, added `da270f9b` 2026-04-19, deleted
      `bce12993` 2026-06-10); (b) slug is fully recoverable from `instruments-service`'s `catalog.parquet`
      (`raw_symbol`, 0% NULL), but title/question is NOT reliable (93.2% NULL corpus-wide) and eventSlug is recoverable
      nowhere (no persisted column). The schema-extension migration itself (design → writer/migrate → register) was
      completed separately via `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`: `unified-api-contracts@90ddcc01`
      added `title`/`slug`/`event_slug` as first-class canonical `trades` `ColumnSpec` entries;
      `market-tick-data-service@84154e1a` stopped the Polymarket writer dropping them at ingest; both registered in
      `/codex/02-data/canonical-cutover-register.md` §6e + `/codex/02-data/non-canonical-path-inventory.md` row 22. The
      issue doc is now `status: resolved` and archived. **Residual not closed by this bullet** (tracked separately, not
      this checkbox's scope): the historical raw-object migration of shapes #3/#3b/#4 themselves is registered
      `no-migrate-first` and absorbed by `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` todo 4b — this bullet's
      own done-when (the issue doc showing all 3 schema-extension steps checked) is satisfied regardless.

### A3 — Venue-perps + live CLOB depth residuals (fold)

- [x] ✅ [BACKEND] P1. **Retagged 2026-07-29 (corpus hygiene pass): resolved-by-reference — this item was split +
      archived 2026-07-24 into 3 successor docs, and the doc's own text below already directs future work to them; no
      independent work remains under this checkbox.** **Close the 12 residuals on Kalshi/Polymarket perpetual futures +
      live CLOB depth/quotes** (funding / basis / dispersion arb inputs).
      `prediction_venue_perps_and_live_clob_depth_2026_06_20.md` (12 open of 85) — **split + archived 2026-07-24** (plan
      line-cap remediation) into `prediction_perps_kalshi_polymarket_parked_2026_07_24.md` (1 open),
      `prediction_live_clob_depth_capture_2026_07_24.md` (2 open), and
      `prediction_cross_venue_arb_and_coverage_2026_07_24.md` (9 open + 2 in-progress); the residual-fold above should
      now target those 3 successors, not the archived original. (repos: market-tick-data-service, unified-api-contracts,
      features-service)

      **2026-07-26 fold-in** (resolved `autonomous_session_operator_decisions_2026_07_25.md` entry #12, option A):
          `prediction_perps_kalshi_polymarket_parked_2026_07_24.md`'s sole remaining open item folds in here —
          **Polymarket-perp enumerator, BLOCKED-UPSTREAM** (no public perps API exists — `perps-api.polymarket.com` /
          `perps.polymarket.com` / `perp.polymarket.com` all NXDOMAIN, web-UI beta only, CFTC-DCM-approved perps launched
          2026-04-21; re-verified 2026-06-22 that the unified CLOB/Gamma discovery path does not enumerate perp markets
          either). Scaffold shipped at every layer (`PolymarketPerpReferenceDataAdapter` + MTDS adapter/connector +
          launcher gating + strategy honest-absence); real unblock is Polymarket publishing the public perps API or
          operator-provisioned beta credentials — status stays BLOCKED-CREDENTIALS, not descoped, auto-flows on endpoint
          availability. Ping: slot_0. Repo: instruments-service. The shell plan (10 other todos, all shipped) archived —
          see its own Progress Log.

### A4 — Fixture-attribute WRITERS (Phase E depends on this landing before the Phase-D re-backfill)

- [x] ✅ [BACKEND] P0. **Fixture-match attributes on prediction soccer — RESOLVER + SCHEMA + MATERIALIZATION COMPLETE
      (instrument-level, 2026-07-18).** The 6 fixture columns now flow resolver→side-table→instrument parquet: UAC
      `InstrumentRecord` + `INSTRUMENTS_PARQUET_SCHEMA` `unified-api-contracts@e7ed754e` (additive nullable) + IS
      `process_write._records_to_dataframe` join `instruments-service@e3ffc613` (type-boundary handled: side-table
      int/str → contract str/date, honest-absence on bad values; cross-AG round-trip verified — non-prediction rows keep
      all 6 None; QG-green 4579 passed). MTDS prediction-tick schema = OPTIONAL/DEFERRED (catalogue carries the attrs;
      tick-grain only if the arb path needs it). Historical BACKFILL of the columns for existing instruments = held with
      the Phase-B prod run. Resolver increment SHIPPED `instruments-service@85988ade` (QG-green, 662 lines, 8 files):
      new `adapters/prediction/fixture_match.py` resolver + per-instrument side-table — **Polymarket** soccer resolves +
      stamps `af_fixture_id` off the SAME fixtures parquet the MTDS `FixtureIdResolver` reads
      (`candidate_parquet_paths("FIXTURES",…,BATCH_API_FOOTBALL)`, cached per (league,day), canonicalising both sides
      through the SAME `validate_team_resolution` alias index — no new GCS walk); **Kalshi** soccer stamps
      honest-absence (`af_fixture_match_status=UNRESOLVED_TEAM_NAME`, `af_fixture_id=None`,
      `af_league_id`+`fixture_date` still resolved) pending E2; closed set
      `MATCHED`/`UNRESOLVED_TEAM_NAME`/`NO_FIXTURE_DATA`, nullable int, no sentinel; resolver never raises. Tests:
      `test_prediction_fixture_match.py`. **NOW SHIPPING (round-2, constraint lifted)** — materialize the 6 attrs as
      real parquet/manifest COLUMNS: UAC `InstrumentRecord` ✅ e7ed754e + IS `process_write._records_to_dataframe` join
      (reads `fixture_match_for_instrument_key`, ~6-line extension of the `clob_token_ids` block) + the MTDS
      prediction-tick schema — see HELD list. (repos: instruments-service ✅; unified-api-contracts +
      market-tick-data-service DEFERRED)

### A5 — Adapter code-quality audit (relocated 2026-07-25 from the parent's "Queued audits + reviews" section)

- [x] ✅ [BACKEND] P2. **Adapter dead-code/fallback audit — DONE 2026-07-31.** Audited instruments-service's
      (`kalshi.py`, `fixture_match.py`, `polymarket/{adapter,clob,markets,parsing,_pkg_ref}.py`) and
      market-tick-data-service's (`kalshi_adapter.py`, `polymarket_adapter.py`, `base_prediction_adapter.py`,
      `_polymarket_helpers.py`, `_polymarket_shard_classify.py`) prediction adapters for dead code, silent fallback
      branches, and duplicated logic, per `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md`.
      **Awareness note confirmed**: `prediction_satellite_ao_dispatch_batch1_2026_07_25.md` todo 1 already landed
      (status: complete) — the dead `trading-api.kalshi.com` host defect is fixed with a regression-guard test
      (`e2e-testing/tests/unit/test_validate_batch_live_smoke_matrix.py`); not re-filed. **2 distinct defect classes
      found and filed as issue docs** (rule 1, dead code — no rule-2 silent-fallback or rule-3 duplicate-implementation
      violations found; the several documented, logged fallback patterns present — e.g. Kalshi's `_resolve_cutoff()`
      cutoff-lookup-failure default, the `market_lifecycle` GCS-read fallback chain — are all logged
      (`logger.debug`/`.warning`) and code-commented with the specific historical incident each guards against, matching
      the codex rule's "genuine, intentional fallback... named as such and logged" bar, not a silent
      catch-and-continue): 1. `plans/active/issues/is_polymarket_dead_fixture_cross_reference_2026_07_31.md` —
      instruments-service's `PolymarketReferenceDataAdapter._cross_reference_fixture()` + its
      `_api_football_key`/`_fixture_cache` state, wired end-to-end from `factory.py` (resolves + injects a real
      `api_football` secret) but never invoked by any live code path; the code's own comment calls it "unused." 2.
      `plans/active/issues/mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md` —
      market-tick-data-service's `KalshiAdapter`/`PolymarketAdapter` carry a whole dead "live REST-polling" interface
      (`get_markets`/`get_prices`/`normalize_market`/`normalize_odds`/`parse_market`/`parse_token`/
      `parse_order_book`/`parse_trade`/`_convert_gamma_market`/`_build_order_book_record`, plus two
      self-labeled-"Legacy" wrapper methods) — exercised only by tests, zero production call sites; the live pipeline is
      exclusively `download_batch()` -> `get_trades_batch`/`get_books_batch`. Both issue docs carry a `[BACKEND] P2` fix
      todo (delete-or-document-activation-path) — neither fixed inline here per findings-triage (genuine judgment call
      between delete vs. document, not auto-resolved by an audit). (repos: instruments-service,
      market-tick-data-service)

## Phase B — run the migrations (gated on Phase A green)

> Pre-migration drain per the VM runbook; direct manifest mutation MUST use the additive per-VM-shard write (race-free
> vs the ~10-min consolidator) — do NOT do a naive `_index`-only rewrite.

- [x] ✅ [DATA] P0. **CQG-bundle-atom wipe FIXED (verified 2026-07-18, slot-2 A0).** The phantom-reconciler bundle-atom
      exemption (`MANIFEST_ONLY_BUNDLE_DATA_TYPES` in `unified_trading_library/reconcile/manifest.py`) landed 2026-07-11
      and the rebuild restored the CQG cluster rows; A0 live read confirms **17,352 captured**
      `prediction_canonical_question_group` rows (was "ZERO"). Original P0 closed —
      `issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` steps 1-4 landed.
- [x] ✅ [BACKEND] P1. **CQG-issue residuals 5-6 — DONE (2026-07-18).** (5) `pipeline_mode=live_*` prefixes shipped —
      `unified-api-contracts@e7ed754e` (operator DECIDED union batch+live): `live_kalshi`/`live_polymarket_clob` were
      already emitted (2026-07-11); added the missing `live_polymarket_gamma_api` via a prediction-scoped
      `_EXTRA_LIVE_PROBE_SOURCES_BY_AG` probe (did NOT fabricate a `LIVE_POLYMARKET_GAMMA_API` enum member — that source
      is batch-only by design); rule-11 verified cefi/tradfi/defi/sports template counts byte-unchanged. (6) KALSHI
      provenance mislabel already fixed `market-tick-data-service@3397e7ae` (see §6).
      `issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` §5 flipped `pm@4436e59f0`. (repos:
      unified-api-contracts ✅, market-tick-data-service ✅)
- [ ] [DATA] P0. **Enumeration-driven canonical/dedupe migration of the prediction manifest (A0-driven, single source of
      truth, operator 2026-07-18)** — CONCRETE A0 targets, catalogue is SSOT: (a) `data_type` `prediction_trades` →
      `trades`; (b) `instrument_type` → `PREDICTION_MARKET` — fold lowercase `prediction`/`prediction_market`, and
      re-stamp the underlying-asset-leakage rows (`BTC`/`ETH`/`SPX`/`DJIA`/`NDX`/`GOLD`/`SILVER`/`CRUDE_OIL`/`DOGE`/
      `XRP`/`BNB`/`HYPE`/`OTHER`/`''`, the pre-Plan-A legacy `data_type=<base_asset>` shape) by classifying from the
      CQG/underlying, NOT trusting the column; (c) stamp empty `source=''` from the writer's `default_source`; (d)
      catalogue `base_asset` whitespace-strip + dedupe (leading-space title variants). Additive per-VM-shard write
      (race-free vs the ~10-min consolidator). Fold: the prediction slice of `data_completion_prediction_2026_07_15.md`
      (23 open). (repos: market-tick-data-service, instruments-service, unified-trading-library) **SCRIPT WRITTEN +
      dry-run measured — `market-tick-data-service@5392b20b`** (initial) **+ `@916dd992`** (COMPLETE — now handles both
      findings: `--bundle-mode {normalize,leave}` default normalize, and `--remove-stragglers` design =
      pause-consolidator + snapshot + in-place `_index` CAS rewrite, guarded, NOT run). The 916dd992 agent found the
      WRITER ROOT of finding (i): `engine/orchestrator/manifest_finalize._finalize_prediction_bundles` stamps lowercase
      `instrument_type="prediction"` on every bundle row — so the bundle is emitted lowercase, not null; the writer-root
      fix is on the operator-review checklist (else a `--force` rebuild resurrects stragglers).
      (`scripts/canonicalize_prediction_manifest_2026_07_18.py`, `--dry-run` DEFAULT, `--apply` behind
      `--confirm-prod-write`; prod RUN HELD per operator). Live dry-run (756,817 rows): #1 `prediction_trades`→`trades`
      3,385 rows (99.55%→100%); #2 per-CID `instrument_type`→`PREDICTION_MARKET` 648,616 rows (per-CID 4.16%→100%,
      all-rows 11.70%→**97.40%**); #3 `source` 2 empty→`polymarket_clob`. **TWO FINDINGS FOR THE HELD RUN
      (operator-decision, revises decision-2):** (i) **RESOLVED 2026-08-19 (operator ruling, `BLK-2062d75e`)** — the
      CQG bundle is NOT null-by-design in practice — 80,068 rows =
      60,427 `PREDICTION_MARKET` + 17,361 lowercase `prediction` + only 2,280 null; keeping it unstamped caps all-rows
      at 97.40%, and its 17,361 lowercase `prediction` are themselves non-canonical → decide: normalize the bundle to
      `PREDICTION_MARKET` too (→~100%) vs enforce SSOT "bundle null" (un-stamps 77,788) vs leave inconsistent.
      **RULED: normalize the bundle to `PREDICTION_MARKET` too** — matches the per-CID precedent, reaches ~100%
      canonical coverage, avoids reversing the 60,427 rows already correctly stamped. Execution:
      `prediction_satellite_ao_dispatch_batch12_2026_08_17.md` todo 4 (its `[OPERATOR]` gate removed same ruling). (ii)
      `instrument_type`/`data_type` are consolidator DEDUP-KEY columns → the additive shard adds the corrected rows but
      leaves ~652k OLD rows as stragglers (doubling); reaching the target % needs an old-row sweep = the "naive direct
      `_index` rewrite" that resurrects on `--force` rebuild → the run needs a tombstone/removal strategy. Both
      documented in the script docstring + printed by dry-run. **CROSS-REF added 2026-08-19 (plan_reconciler,
      agt-4a2f8b), RESOLVED same day**: `prediction_satellite_ao_dispatch_batch12_2026_08_17.md` todo 4 executes the
      stamp (both the 9,260-row per-CID half and the 2,280-row CQG-bundle half of finding (i)) — the operator ruled
      (`BLK-2062d75e`) to normalize the bundle too, so that todo's `[OPERATOR]` gate has been removed and it runs as
      originally written. **✅ MANIFEST `--apply` APPLIED 2026-07-19 (tick 18) —
      `market-data-tick-pred-prd/_index` CAS REPLACE, generation `…161980856`→`…195626006`, 745,107 rows, 12,524
      stragglers removed, `instrument_type` 11.80%→100% / `data_type` 100% / `source` 100%, 0 captured cells lost;
      snapshot `_index/backups/pre_prediction_canonicalize_20260719T103301075148Z.parquet`; consolidator paused→resumed
      (ENABLED). Manifest targets (a)(b)(c) DONE; catalogue `base_asset` (d) = the separate A2 catalogue regen (below).
      Durability caveat: per-CID + `prediction_trades` re-accumulate until the items-2+3 follow-up lands.**
- [x] [DATA] P1. **✅ DONE 2026-07-19 (tick 21) — item 2 `market-tick-data-service@71761d7f` (per-CID shard-key itype
      folds to canonical `PREDICTION_MARKET`, prediction-venue-gated RULE-11, +tests; note the writer actually carried
      lowercase `prediction_market` not null, so the fold is unconditional) + item 3 `unified-api-contracts@1794f3e5`
      (`prediction_trades` dual-seed retired across 7 files, +34/−186; adversarially verified no live consumer requires
      it; QG green). The Phase-B `--apply` cleanup is now DURABLE (per-CID no longer re-accumulates; the phantom
      `prediction_trades` expected rows are gone). Writer-root durability COMPLETION (items 2+3 of the migration
      checklist step 0) — the Phase-B `--apply` cleanup is DURABLE for the CQG bundle (item 1 SHIPPED
      `market-tick-data-service@1ec415f8`) but TRANSIENT for per-CID + `prediction_trades` until these land** (surfaced
      tick 17): (2) canonicalize the prediction per-CID `instrument_type` at the **shard-key construction** UPSTREAM of
      the generic per-CID writer (which stamps `itype_key` verbatim, RULE-11 — do NOT canonicalize in the generic
      writer; 640,701 per-CID null rows re-accumulate otherwise); (3) retire the legacy `prediction_trades` seed key —
      `PREDICTION_MVP_SEED_INSTRUMENTS` dual-seeds `("VENUE","trades")` + `("VENUE","prediction_trades")` "during
      rollout" (retired 2026-04-19); rollout-completion across 6 UAC files (`defi_prediction_instrument_seeds`,
      `data_type_capability`, `schema_spec`, `_schema_spec_prediction`, `expected_coverage`, `market_data_categories`) —
      DELICATE (breaks un-migrated callers; affects the `expected_unattempted` denominator) → verify no live consumer
      still emits/expects `prediction_trades` before removing. Until both land, a periodic re-run of
      `canonicalize_prediction_manifest_2026_07_18.py --remove-stragglers --apply` closes the drift. (repos:
      market-tick-data-service, unified-api-contracts)
- [ ] [DATA] P0. **Backfill the fixture-match attributes (A4 columns) across historical Polymarket + Kalshi soccer** —
      resolve `af_fixture_id` per market from the fixtures parquet (canonical `home_id`/`away_id` + `af_league_id` +
      `fixture_date`) OR by parsing the human-readable canonical name, stamping `af_fixture_match_status`. Honest nulls
      where unresolved; the match-rate summary line logged per (league, day). (repos: market-tick-data-service,
      instruments-service)
- [x] [DATA] P1. **RULED 2026-07-28 — apply the standing canonicalization precedent by default; escalate only a genuine
      residual.** This was previously `[DECISION] P1`, gated on an operator decision, pending a fresh enumeration of the
      A0 ambiguous set. Ruling (general theme — canonicalization work should be done properly, not left as an open-ended
      standing gate): (1) enumerate the FULL A0-ambiguous set live (this is itself a bounded, checkable task — the
      enumeration script already exists, `enumerate_prediction_dimensions.py`), listing each value's candidate canonical
      readings; (2) resolve each one by applying the SAME precedent this exact migration already established for
      prediction (operator, 2026-07-18: canonical = UPPERCASE enum, the catalogue is SSOT — see A0/A2 above) — i.e.
      default to whichever candidate reading matches the catalogue's existing clean canonical form / the established
      UPPERCASE-enum convention, and record the specific per-value mapping decisions made under this default with the
      evidence cited; (3) do NOT block the unambiguous majority of the migration on this — unchanged from the original
      framing. **Only if a specific value survives (2) still genuinely tied between two readings with no catalogue
      precedent to break the tie — not merely "not obviously spelled one way" — escalate that SPECIFIC residual value**
      (not the whole todo) as a narrow, options+recommendation operator question, mirroring the format already used
      elsewhere in this corpus (see `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s per-item
      operator-decision-gate bullets for the pattern). Done when: the full ambiguous set is enumerated with a
      disposition (resolved-by-precedent or escalated-as-residual) recorded per value in this doc's Progress Log.
      **Extracted 2026-08-17 (na-eligibility-audit, per-todo RECLASSIFY_SPLIT)** — the ruling is already on record, the
      procedure is bounded/worker-determinable; promoted to `prediction_satellite_ao_dispatch_batch12_2026_08_17.md`
      todo 1. Execution now tracked there, not here.
- [ ] [DATA] P0. **Re-verify + close the `instrument_type` casing/canonicalisation gap to literal 100% (operator,
      2026-07-24) — the historical numbers in this doc DISAGREE and need reconciling, not just re-citing.** The tick-18
      `--apply` (line 229 above) measured `instrument_type` 11.80%→100% live on 2026-07-19; but the cross-AG D1 ruling
      snapshot (`/codex/02-data/reconciliation-finding-taxonomy.md` §5.1) measured prediction at only 99.46% UPPER one
      day later (2026-07-20) — the two don't agree, most likely because ongoing captures between the two reads
      re-introduced non-canonical rows (the durability gap items 2+3 above were still open at the 07-19 apply and only
      closed at tick 21). **Done when**: a FRESH live manifest read today shows literal 0 non-canonical
      `instrument_type` rows (not either historical snapshot) AND the deployment-ui data-status Distinct Values panel
      confirms 0 non-canonical entries for prediction. This is the cross-AG standard — tradfi/cefi/sports all target the
      same 100% bar; DeFi is the sole exception (genuinely mixed per-instrument_type, tracked separately in
      `defi_consolidated_closeout_2026_07_18.md`). **Narrowed 2026-07-25
      (`prediction_satellite_ao_dispatch_batch2_2026_07_25.md` todo 2) to the case-insensitive standard the RULED C2a
      ruling actually mandates** (`/codex/02-data/reconciliation- finding-taxonomy.md` §5.1 — UPPERCASE target,
      `migration_pending`, compared case-INSENSITIVELY, no casing finding during the migration window) — **still open,
      see 2026-07-27 Progress Log entry**: a fresh read found 176 genuinely-malformed (non-casing) rows, not 0.
- [x] [DIAG] P2. **NEW 2026-07-27 — prediction manifest blank/null `instrument_type` rows are ACTIVELY GROWING, not
      static residue (found while re-verifying the casing item above).** Live counts across 3 dated reads: 30
      (2026-07-20) → 70 (2026-07-24) → 100 (2026-07-27) — a consistent ~10 rows/day linear rate over both intervals (+40
      over 4 days, +30 over 3 days, both ≈10.0/day). This contrasts with the co-located 76-row `prediction` (singular)
      malformed residual on the SAME axis, which has been static/unchanged across all 3 reads since 2026-07-20 — that
      population is dead historical residue, not active, while the blank population is evidence of an ONGOING writer
      defect still stamping blank `instrument_type` on ~10 prediction rows/day. **Done when**: the writer/cron path
      responsible for the blank stamps is identified by name (file:line) with a live-vs-historical verdict — candidates
      include the per-CID writer path near `engine/orchestrator/manifest_finalize. _finalize_prediction_bundles`
      (already known from the tick-18 finding above to mis-stamp `instrument_type` on bundle rows, though that finding
      was lowercase `"prediction"`, not blank) or a different live/per-CID path — and either a fix ships and is verified
      against the next day's count, or the ~10/day gap is recorded as accepted with a stated reason. Repo:
      market-tick-data-service. Source: `prediction_satellite_ao_dispatch_batch2_2026_07_25.md` todo 2 (this doc's item
      9 re-verify surfaced it as a byproduct). **Extracted 2026-08-17 (na-eligibility-audit, per-todo
      RECLASSIFY_SPLIT)** — bounded diagnose-then-fix-or-accept task, no open design/judgment call; promoted to
      `prediction_satellite_ao_dispatch_batch12_2026_08_17.md` todo 2. Execution now tracked there, not here.
- [ ] [DATA] P2. **`/data-pipeline-reconciliation` post-migration 3x-cadence + duplicate-note merge (relocated
      2026-07-25 from the parent's "Queued audits + reviews" + "Distinct Values / axis-value census" P3 sections — both
      tracked the same underlying action, merged into this one todo).** Reach the 3x dated-pass cadence
      `task_template.md` finding K requires for prediction: baseline (confirmed) `2026-07-20` —
      `/plans/audit/results/data_pipeline_reconciliation_prediction_2026_07_20.md`; a 2nd pass already exists, uncited
      until now — `/plans/audit/results/data_pipeline_reconciliation_prediction_2026_07_24.md` (diffs against the
      2026-07-20 baseline: reachable_coverage 95.82% vs 94.63%; F2 malformed `instrument_type` 76 `prediction` rows
      unchanged, +70 blank, was 30); the 3rd and final pass is the genuinely-blocked post-Phase-B-migration final gate
      (this same doc's migration todo above must land first) — re-run `/data-pipeline-reconciliation prediction` once it
      does and diff against the 2026-07-20 baseline. Also verify whether any `/data-pipeline-reconciliation prediction`
      run PREDATES the 2026-07-20 baseline (search `plans/audit/results/`, `plans/active/`, `plans/archive/`) — record
      found-with-path or confirmed-absent. Also also tracked as an AO-dispatchable partial-slice execution copy in
      `prediction_consolidated_native_ao_extract_2026_07_25.md` (`status: draft`) todo 4 — that plan's own Done-when now
      cites this checkbox + the parent doc's "Distinct Values / axis-value census" section (updated 2026-07-25,
      corpus-wide referrer fixup) as its reconciliation targets. **Done when**: all 3 dated runs' report paths are cited
      together in this plan's Progress Log, and the parent's "Distinct Values / axis-value census" section lists the
      2026-07-24 pass alongside the 2026-07-20 baseline.

## Progress Log

- **na-eligibility-audit 2026-08-04 (prediction tranche)**: KEEP-NA, valid — 7 open, unchanged count since the
  2026-07-31 marker (re-verified live via `grep -cE '^- \[ \]'`, matches). Today's only content change is the new entry
  immediately below (partial progress on the Phase-B `/data-pipeline-reconciliation` cadence todo — predating-run search
  confirmed-absent, citation added) — the todo itself remains open (3rd/final post-migration pass still gated on the
  Phase-B migration landing). All 7 open items independently re-confirmed: each ends in a race-sensitive operator-held
  `_index` CAS `--apply`, an infra drain window, or a genuine per-item escalation — none worker-determinable end to end.
  Not a RECLASSIFY case. Doc stays NA.

- **round11 RECLASSIFY + satellite-extraction sweep 2026-08-09 (prediction tranche)**: KEEP-NA, valid — re-checked
  against the full round-11 precedent set (IAM self-service default, D16 all-repos carve, S5.1 tiering,
  plan-destination-default-to-AO for auto-filed findings, escalation-N=3-days, reversibility-qualified deletes
  agent-executable after a fresh check, Option B retirement, GSM secret `deepseek-v4-pro-api-key` + 5 Slack webhooks) —
  none newly bound any of the 7 open items (A1's pointer to the capture-incident doc's Phase 6, the Phase-B `--apply`
  migration itself, the ambiguous-value canonicalization enumeration, the casing re-verify, the growing-blank-rows
  diagnostic, the fixture-attribute backfill, and the 3x-cadence reconciliation follow-up) — each still ends in a
  race-sensitive operator-held `_index` CAS write, a design/investigation step, or a cross-doc pointer. A1's own target
  (`prediction_capture_incident_remediation_2026_07_06.md` Phase 6) was independently extracted today into
  `prediction_satellite_ao_dispatch_batch10_2026_08_09.md` — verified, not re-actioned here (A1 itself is a rollup
  pointer, not separately dispatchable). No reclassification.

- **2026-08-04 (slot-4, data_engineering) — `prediction_consolidated_native_ao_extract_2026_07_25.md` todo 4
  (partial-slice execution of this doc's Phase-B `/data-pipeline-reconciliation` cadence todo) DONE.** (a) Corpus search
  for a `/data-pipeline-reconciliation prediction` report dated BEFORE the 2026-07-20 baseline (`plans/audit/results/`,
  `plans/active/`, `plans/archive/`): **confirmed-absent** — the only two dated reconciliation reports for
  `asset_group=prediction` in the entire corpus are
  `/plans/audit/results/data_pipeline_reconciliation_prediction_2026_07_20.md` (the confirmed baseline) and
  `/plans/audit/results/data_pipeline_reconciliation_prediction_2026_07_24.md` (the 2nd pass); no earlier one exists.
  (b) The 2nd pass (`/plans/audit/results/data_pipeline_reconciliation_prediction_2026_07_24.md`) was already cited in
  the parent `prediction_consolidated_closeout_2026_07_18.md`'s "Distinct Values / axis-value census" section as of the
  2026-07-25 relocate-todos commit (`41768ed9`) — added the explicit report path there (was cited by date only, no link)
  and appended this same predating-run search result inline. No new live `/data-pipeline-reconciliation` run was
  executed per this todo's own scope (not needed — the discovery/citation work was the deliverable). This item's own
  **Done when** (this entry + the parent-doc citation) is satisfied; the 3rd/final post-Phase-B-migration dated pass —
  and this doc's own merged Phase-B todo above (which that 3rd pass gates) — remain genuinely open, unaffected by this
  partial slice.
- **na-eligibility-audit 2026-08-03 (reclassify pass)**: KEEP-NA, valid (blocker-currency only) — A1's own "stays open
  until Phase 6 ships" condition is now MET (`instruments-service@e0f7aaad`, shipped via
  `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 1, 2026-07-30); annotated in place with the SHA + the
  reason A1 nonetheless stays open (Phase 6's own backfill-assessment follow-up is explicitly an "operator/architect
  call, not a mechanical todo"). No other open item's cited blocker/reference was found stale on a fresh read. Not a
  RECLASSIFY case — every remaining item ends in a writer-drain + race-sensitive `_index` CAS `--apply`, an infra
  window, or a genuine per-item/design escalation. `assigned_vm` untouched.

- **na-eligibility-audit 2026-07-31 (prediction tranche)**: KEEP-NA, stale item closed — 7 open (was 9 at the 2026-07-30
  marker: A5 adapter dead-code audit resolved same-day by a sibling dispatch, -1; A1c closed this pass as stale, -1).
  A1c ("Adapters must apply lifecycle bounds BEFORE the network call") described work whose own source doc
  (`issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md`) is now fully resolved and
  archived — closed with citation. Remaining 7 open items re-verified against the 2026-07-30 marker's own reasoning,
  unchanged: A1a stays gated on `prediction_capture_incident_remediation_2026_07_06.md`'s unimplemented Phase 6
  (out-of-tranche doc, not re-opened this pass); the 6 Phase-B items (enumeration-driven manifest migration,
  fixture-attribute historical backfill, ambiguous-canonical-value per-value escalation, instrument_type casing
  re-verify, the actively-growing blank-instrument_type diagnostic, and the reconciliation-cadence top-up — the last
  already a confirmed duplicate of `prediction_consolidated_native_ao_extract_2026_07_25.md` todo 4) each require a
  writer drain + operator-held `--apply` on a race-sensitive `_index` CAS rewrite, an infra drain window, or end in a
  genuine per-item escalation path — none worker-determinable end to end. Doc stays NA.

- **2026-07-31 (slot-12, backend_engineer) — A5 adapter dead-code/fallback audit DONE, dispatched via
  `prediction_consolidated_native_ao_extract_2026_07_25.md` todo 1.** Audited every prediction adapter file in scope
  (instruments-service `kalshi.py`/`fixture_match.py`/`polymarket/*`, market-tick-data-service `kalshi_adapter.py`/
  `polymarket_adapter.py`/`base_prediction_adapter.py`/`_polymarket_helpers.py`/`_polymarket_shard_classify.py`) against
  `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md`'s 3 rules. Confirmed the batch1 dead
  `trading-api.kalshi.com` host defect already landed (status: complete, regression-guarded) — not re-filed. Found +
  filed 2 distinct dead-code (rule 1) defect classes as issue docs (repo-wide grep-verified zero non-test production
  call sites for each): `is_polymarket_dead_fixture_cross_reference_2026_07_31.md` (instruments-service —
  `_cross_reference_fixture()` + its `_api_football_key`/`_fixture_cache` state, wired end-to-end from `factory.py`'s
  real secret resolution but never invoked) and `mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md`
  (market-tick-data-service — a whole dead "live REST-polling" method family on `KalshiAdapter`/`PolymarketAdapter`,
  test-only coverage, zero production call sites; the live pipeline is exclusively `download_batch()`-driven). No rule-2
  silent-fallback violations found — every fallback branch checked (Kalshi `_resolve_cutoff()`'s cutoff-lookup-failure
  default, `market_lifecycle`'s multi-path GCS-read degrade chain, etc.) is logged (`logger.debug`/`.warning`) and
  code-commented with the specific incident it guards against. No rule-3 duplicate-implementation violations found (IS
  reference-data adapters vs. MTDS market-data adapters are different services by design, not same-service duplicates).
  Flipped the A5 checkbox above with full evidence; both issue docs carry their own `[BACKEND] P2` follow-up todo
  (delete-or-document-activation-path — a genuine judgment call, not fixed inline per findings-triage).

- **na-eligibility-audit 2026-07-30 (prediction tranche)**: KEEP-NA, valid — 9 open, re-verified live against this doc's
  own 2026-07-30 reconciliation entry (9 open / 10 done / 19 total, matches). A1a stays gated on the sibling doc's
  unimplemented Phase 6; A5 (adapter dead-code audit) and the Phase-B `/data-pipeline-reconciliation` cadence top-up are
  CONFLICT — both already extracted into `prediction_consolidated_native_ao_extract_2026_07_25.md`
  (`assigned_vm: planning`, `status: active`) todos 1 and 4. The Phase-B migration items require a writer drain + a
  race-sensitive `_index` CAS rewrite with an operator-held `--apply`, and the ambiguous-canonical-value item ends in a
  per-value escalation path. None is worker-determinable end to end.

- **2026-07-24 (plan-hygiene split) — forked from `prediction_consolidated_closeout_2026_07_18.md`.** This plan carries
  forward the Phase A + Phase B sections verbatim (14 todos total: 5 done / 9 open at split time). See the parent's
  Progress Log (ticks 1-31, especially the A0/A2/A4/§5/§6 and Phase-B `--apply` entries — ticks 1, 4-9, 16-18, 21) for
  the full session-by-session history of what is already shipped here. Future work on this plan logs new entries below.
- **2026-07-25 (consolidated-closeout split pass) — relocated 2 items in from the parent's now-forked "Queued audits +
  reviews" / "Distinct Values" P3 sections.** Added new "A5 — Adapter code-quality audit" subsection (1 todo). Added 1
  merged Phase-B todo combining the `/data-pipeline-reconciliation` 3x-cadence top-up with the former "Distinct Values"
  P3 duplicate-note (both tracked the same underlying post-Phase-B-migration reconciliation action). Folded the
  operator-ruled (2026-07-25) POLYMARKET `prediction_trades` schema-extension migration into the existing A2
  dual-write-trees todo (same source issue doc, same finding — no new checkbox needed). Net: open-todo count 11 → 13. No
  engineering work executed in this pass — pure relocation + reconciliation of pre-existing tracked items.
- **2026-07-26 (`/plan-reconcile` prediction shard, autonomous) — one AO-dispatch-readiness repo-attribution fix, no
  checkbox changes.** The A1 "Kill the dead Kalshi `trading-api.kalshi.com` host" todo annotated
  `(repos: market-tick-data-service)`, but its primary named action lives in a repo that annotation never named:
  `e2e-testing/scripts/validation/validate_batch_live_smoke_matrix.py:552` — re-verified 2026-07-26 that the dead host
  is still literally in the current tree at that exact line, and that the linked issue doc
  (`/plans/archive/2026_08/issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`) lists `e2e-testing` first in
  its own `repos:`. A worker dispatched on the todo's own annotation would have searched MTDS and found nothing. Repo
  list corrected to name both legs (`e2e-testing` for the smoke matrix, `market-tick-data-service` for the
  `raw_tick_data/by_date/` drift). The plan's frontmatter `repos:` already included `e2e-testing` — the gap was
  per-todo, which is the level AO dispatch actually reads.
- **2026-07-27T15:28:46Z (slot-4, `prediction_satellite_ao_dispatch_batch2_2026_07_25.md` todo 2) — fresh
  case-insensitive live read of item 9's `instrument_type` residual: still open, and the blank sub-population is
  actively growing, not static.** Per the RULED C2a standard (`/codex/02-data/reconciliation-finding-taxonomy.md` §5.1 —
  UPPERCASE target, compared case-INSENSITIVELY, no casing finding during `migration_pending`), read
  `market-data-tick-pred-prd-central-element-323112`'s `availability_index.parquet` `instrument_type` column live via a
  slim, column-pruned `read_availability_index(bucket, columns=["instrument_type"])` (single-walk, no whole-corpus scan;
  mirrors deployment-api's `_axis_census.py` pattern) at 2026-07-27T15:28:46Z:
  - **785,035 total rows.** 775,139 exact-uppercase `PREDICTION_MARKET` (98.74%) + 9,720 lowercase `prediction_market`
    casing-variant (1.24%) — correctly NOT flagged, `migration_pending` per the ruling — + **176 genuinely malformed,
    non-casing rows (0.0224%)**: 76 rows literally `prediction` (singular) + 100 blank/null.
  - **Checkbox stays open** — the count is non-zero, not the 0 the (case-insensitive-narrowed) done-when requires.
  - **Composition matters and is new information**: the 76 `prediction`-singular rows are IDENTICAL to the count at both
    the 2026-07-20 baseline (76) and the 2026-07-24 pass ("76 unchanged" per that pass's own note) — this sub-population
    is dead historical residue, not re-accumulating. The blank/null count is NOT static: 30 (2026-07-20) → 70
    (2026-07-24) → 100 (2026-07-27) — a consistent ~10 rows/day linear rate over both gaps (+40/4d, +30/3d). This is
    evidence of an ACTIVE writer defect, not a closed historical gap — filed as a new Phase-B todo above rather than
    only noted here.
  - Citing THIS read as current. The 2026-07-20 baseline (106 total) and the 2026-07-24 pass (146 total, inferred from
    its own "76 unchanged + 70 blank" note) are both superseded snapshots, not current state.
  - **Did NOT run** `canonicalize_prediction_manifest_2026_07_18.py --remove-stragglers --apply` (out of this todo's
    scope per its source batch2 plan — that `--apply` still needs its own separate D1-migration-execution sign-off).
    Read-only: no code changed, no manifest mutation.
- **2026-07-27T18:00Z (slot-10, `prediction_satellite_ao_dispatch_batch1_2026_07_25.md` todo 7) — verdict: YES, the
  `lifecycle-catalogue-regen-prediction` cron already carries the shipped `underlying` + cross-venue
  `canonical_instrument_id` fields (instruments-service@0d0c3742, landed 2026-07-09) into the live
  `prod/catalog.parquet` — the staged full manual regen adds nothing beyond what the existing daily/weekly cron already
  does automatically.**
  - **Collision check**: verified via the live plan text that batch2's own conflicting todo
    (`prediction_satellite_ao_dispatch_batch2_2026_07_25.md`, its "Conflict-check" item citing this same doc) is already
    marked `[x]` **DONE 2026-07-27 (slot-4)** — no concurrent-dispatch risk at execution time.
  - **Checked columns**: `underlying`, `canonical_instrument_id` (both present in the live schema, 40 columns total,
    `instrument_type=PREDICTION_MARKET` only — venues `KALSHI`/`POLYMARKET`).
  - **Code proof** (`instruments-service/scripts/build_instrument_catalogue.py:2081-2088`): the roll-up does NOT
    re-derive these fields — it carries them straight through from whatever the per-date
    `instrument_availability/by_date/day=…/venue=…/instruments.parquet` snapshot recorded, which is `""` (honest
    absence) for any snapshot captured before the 2026-07-09 fix and real values for any snapshot captured after. So
    "does the cron carry the fix through" reduces to "has the cron run since 2026-07-09, on windows that include
    post-fix by-date snapshots" — confirmed both ways below.
  - **Execution proof** (`gcloud run jobs executions list`, read via the ambient `unified-trading-sa` identity, live
    2026-07-27): the DAILY `lifecycle-catalogue-regen-prediction` job has completed successfully every day 2026-07-16
    through 2026-07-27 (the 2026-07-13/14/15 OOM failures pre-date the 16Gi/cpu4 memory bump — already fixed, see the
    terraform comment); the WEEKLY `lifecycle-catalogue-full-prediction` (`--mode full`, a genuine whole-history by_date
    re-walk) succeeded 2026-07-11, 2026-07-18, and 2026-07-25 — all after the fix landed.
  - **Data proof**: downloaded the live `gs://instruments-store-pred-prd-central-element-323112/prod/catalog.parquet`
    (211MB, last-modified 2026-07-27T11:04:06Z — matches that day's 11:00 UTC daily-job execution) and read it directly
    (pandas/pyarrow, instruments-service `.venv`). 3,040,264 rows total (KALSHI 205,341 / POLYMARKET 2,834,923).
    Splitting on `available_to` vs. the fix's landing date shows the exact expected step-change:
    | segment                                                                                                           | rows      | `underlying` populated | `canonical_instrument_id` populated |
    | ----------------------------------------------------------------------------------------------------------------- | --------- | ---------------------- | ----------------------------------- |
    | `available_to` < 2026-07-09 (pre-fix legacy)                                                                      | 2,573,214 | 2.0%                   | 0.3%                                |
    | `available_to` >= 2026-07-09 (post-fix)                                                                           | 467,050   | 78.3%                  | 4.6%                                |
    | Row samples: post-fix KALSHI — `KALSHI:PREDICTION_MARKET:KXBNB15M-26JUL171000-00` → `underlying="BNB"`,           |
    | `canonical_instrument_id="PRICE::BNB::UP_DOWN::2026-07-17::DIR"`; post-fix POLYMARKET (sports market) —           |
    | `underlying="OTHER"`, `canonical_instrument_id="ELITESERIEN:FREDRIKSTAD_FK_EXACT_SCORE_v_FK_BOD_GLIMT:20260717"`; |
    | pre-fix legacy row `ELON_STATEMENTS` (POLYMARKET, `available_to=2026-05-25`) — both fields `""`, honest absence,  |
    | exactly as the code comment documents.                                                                            |
  - **Verdict on "is the staged full manual regen still needed?" — NO.** Whatever that manual run would do
    (`build_instrument_catalogue.py --asset-group prediction` against real GCS data), the WEEKLY job already does it
    automatically (last ran 2026-07-25, 2 days ago) — a manual invocation would re-read the identical by-date snapshot
    files and produce the same result. **Residual not solved by either the cron or the staged manual regen**: the 85%
    pre-fix legacy rows are permanently `""` for these two fields — the per-date snapshot files themselves were written
    before the fix and are never retroactively regenerated (neither the daily incremental merge nor the weekly full
    re-walk re-derives from raw; both only read what's already in the by-date parquets). Closing that residual, if ever
    wanted, is a distinct retroactive-backfill of historical by-date snapshots — out of scope for this todo and not
    something the parent A2 todo's "full catalogue regen" line was ever going to fix either. Read-only: no code changed,
    no GCS writes.
- **2026-07-30 (`prediction_satellite_ao_dispatch_batch1_finalize_2026_07_25.md` todo 1, reconciliation pass) — flipped
  4 of this doc's checkboxes to DONE citing batch1's 7 commits, annotated a 5th that stays open.** Batch1's 7 todos all
  cited this doc as Source but wrote their Done-when evidence into 3 different sibling docs' Progress Logs
  (`prediction_capture_incident_remediation_2026_07_06.md`,
  `/plans/archive/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md`,
  `plans/archive/issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md`) plus this doc itself
  for todo 7 — all 3 sibling docs' Progress Log entries + their own checkboxes were already correctly flipped (confirmed
  by direct read); the gap was that NONE of batch1's 7 commit SHAs had yet been cited in THIS doc's own checkbox list.
  Flipped: **A1b** (dead Kalshi host, todo 1, `e2e-testing@371ac1b` — both legs now closed, the second via an unrelated
  later relaunch); **A2a** (canonical-identity migration, todo 7, now 8/8 — the cron-already-covers-it verdict); **A2b**
  (route writer through canonical builder, todo 6, 3 commits); **A2c** (POLYMARKET legacy dual-write trees, todo 5
  diagnostic + batch4's separate schema-extension work — issue doc now resolved/archived). **A1a** (finish
  capture-incident remediation) stays open — todo 2's diagnostic + todo 3's Phase 5 guardrail closure
  (`instruments-service@a4137022`, also flipped in that sibling doc directly) are both cited, but that doc's own Phase 6
  (the `prediction.py:95` CQG-bucketing fix todo 2's diagnostic surfaced) is still unimplemented, so the bundled
  checkbox correctly stays open. **Also found + fixed while reconciling**:
  `issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`'s own prose "suggested next step" #2 (the e2e-testing
  host fix) was still un-struck-through despite being resolved by the same batch1 todo 1 commit — struck through with
  citation, a small adjacent consistency fix, not new scope. **Re-verified live** (not trusting any historical count in
  this doc's own frontmatter/notes, per this todo's own instruction): fresh `grep -c '^- \[ \]'`/`'^- \[x\]'` over the
  current file gives **9 open / 10 done / 19 total** — 0 open todos remaining is NOT the outcome (as the finalize plan
  itself predicted): A1a, A1c (reconciled by a different batch, unrelated to batch1), A5 (adapter dead-code audit, never
  batch1 scope), and 6 Phase-B items (enumeration-driven migration, fixture-attribute backfill,
  ambiguous-canonical-value ruling application, instrument_type casing re-verify = the excluded item 9, the
  growing-blank-instrument_type diagnostic, and the `/data-pipeline-reconciliation` 3x-cadence top-up) remain genuinely
  open — none of them batch1's scope. No code changed this turn — doc-only reconciliation across 3 files (this doc,
  `prediction_capture_incident_remediation_2026_07_06.md`,
  `issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`).
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) -- swapped in the capture-incident-remediation
  plan + reconciliation-finding-taxonomy.md (both directly cited by open P0s) + 2 source paths (the migration script,
  the writer-root bundle-stamping bug location).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-07 (prediction tranche, autonomous)**: KEEP-NA, valid — re-verified, 7 open, unchanged
  since the 2026-08-04 marker (5th consecutive audit reaching this verdict on this item set: 07-30, 07-31, 08-03, 08-04,
  now 08-07). Every item confirmed genuinely operator/infra-gated or judgment-call-bearing (prod manifest CAS `--apply`
  "HELD per operator", explicit "operator/architect call, not a mechanical todo" backfill assessments, an accept-vs-fix
  writer-defect judgment branch, item 7 gated on item 2 within this same doc) — a mixed doc, not RECLASSIFY-eligible.
  Doc stays NA.

- **na-eligibility-audit 2026-08-17** [body-hash:4c30ce85929a61ff]: KEEP-NA, valid — 6 open Phase-B todos
  (enumeration-driven manifest migration, fixture-attribute historical backfill, ambiguous-canonical-value precedent
  application, instrument_type casing re-verify to 100%, growing-blank-instrument_type diagnostic, 3x-cadence
  reconciliation top-up). Re-confirmed against the unbroken KEEP-NA history (07-30 through 08-07, round11 08-09) —
  every item ends in an operator-held race-sensitive `_index` CAS `--apply` (explicitly "HELD per operator"), a
  per-item design/judgment call, or a same-doc dependency. **Flagging 2 items for closer review on a future pass**
  (not acted on here — entangled with the same gated Phase-B migration sequence, consistent with this doc's
  conservative precedent): the "apply standing canonicalization precedent" todo reads as a bounded
  enumerate+apply+escalate-residuals-only procedure, and the "blank/null instrument_type ACTIVELY GROWING" item reads
  as a bounded root-cause diagnostic — both tagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE for the next run to weigh
  independently. Doc stays NA.

- **na-eligibility-audit 2026-08-17 (per-todo RECLASSIFY_SPLIT)** [body-hash:ec3591907e5e446e]: re-assessed the 2
  items the same-day marker above tagged `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` (the canonicalization-precedent-application
  todo and the growing-blank-instrument_type diagnostic) — both promoted: the ruling is already on record for the
  former, and the latter is a bounded diagnose-then-fix-or-accept task, neither requiring an open design/judgment
  call. Both extracted to `prediction_satellite_ao_dispatch_batch12_2026_08_17.md` (todos 1 and 2 respectively),
  checkboxes flipped `[x]` citing the batch. Remaining 4 open Phase-B items (enumeration-driven manifest migration
  `--apply`, fixture-attribute historical backfill, instrument_type casing re-verify to 100%, 3x-cadence
  reconciliation top-up) stay NA — each still ends in an operator-held race-sensitive `_index` CAS `--apply`, an
  infra drain window, or a same-doc dependency. Doc stays NA (4 open items remain, down from 6).

- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries) -- re-verified, unchanged.
- **na-eligibility-audit 2026-08-18** [body-hash:0dbf0233de00254b]: KEEP-NA, valid -- 4 open items re-confirmed: the manifest migration carries two live unresolved operator decisions (bundle-normalization choice, --remove-stragglers sign-off) plus un-run catalogue dedupe; the instrument_type casing re-verify and the 3x-cadence reconciliation top-up both explicitly chain on that same migration landing first. Re-examined the fixture-attribute (A4) historical backfill item flagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE this run: the todo offers two resolution methods ("OR by parsing...") with no stated preference/done-when and is a historical write across all prod instrument records -- does not clear the bounded-outcome bar; downgraded to KEEP-NA, consistent with prior passes' decision (2026-08-17) not to promote it either. Doc stays NA.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-21 (prediction tranche)**: KEEP-NA, valid — 4 open items re-confirmed live
  (`grep -cE '^- \[ \]'` = 4): the enumeration-driven manifest migration `--apply` (still carries 2 live unresolved
  operator-decision legs — bundle normalization sign-off, `--remove-stragglers` sign-off — plus the catalogue dedupe
  itself un-run), the fixture-attribute (A4) historical backfill, the `instrument_type` casing re-verify to literal
  100%, and the 3x-cadence reconciliation top-up (both chain on the migration landing first). Consistent with the
  2026-08-18 marker's decision not to promote the A4 backfill (2 unweighted resolution methods, no stated
  preference — does not clear the bounded-outcome bar). Doc stays NA.
