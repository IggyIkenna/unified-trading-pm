---
doc_type: plan
title: TradFi consolidated closeout — native AO extract finalize (reconcile the parent's own checkboxes + archive)
summary: >-
  Gated closeout for `tradfi_consolidated_native_ao_extract_2026_07_25.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until all 10 of that plan's todos are done. Unlike the batch1/batch2 satellite extractions
  (whose "source docs" were OTHER plans/issues), this extraction's todos are the CLOSEOUT PLAN'S OWN native todos — so
  the reconciliation target for most of them is `tradfi_consolidated_closeout_2026_07_18.md` itself: flip its 9
  corresponding native checkboxes (todo 10 of the parent extraction already edits that file directly and is excluded
  from this reconciliation pass), correct the Split-notice digest's stale catalogue-migration line (found live during
  the extraction's own triage), and re-check the 3 deliberately-deferred native todos for any newly-cleared gate.
status: complete
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, native-extract, archival]
related:
  [
    /plans/active/tradfi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md,
    /plans/active/tradfi_backfill_throughput_followups_2026_07_24.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-30"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [tradfi_consolidated_native_ao_extract_2026_07_25]
gate_on_depends: true
source: >-
  Fresh AO-eligibility triage session, 2026-07-25, per `task_template.md` §4's finalize-plan-coverage rule — every
  AO-dispatched plan needs a companion gated finalize plan.
assigned_role: data_engineering
context_scope:
  [
    /plans/active/tradfi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md,
  ]
sequential: true
drift_direction: advance-code
---

# TradFi consolidated closeout — native AO extract finalize

> **🟢 ARCHIVED 2026-08-04.** All 3 todos done (slot-13 verified parent extraction's 9 todos; slot-16 reconciled
> closeout doc; slot-12 archived both the extraction plan and this finalize doc). Both docs moved to
> `plans/archive/2026_07/`. All corpus referrers updated to archive paths.

> **Machine-gated on `tradfi_consolidated_native_ao_extract_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 10 tasks in that plan are `done`. `sequential: true` because
> todo 2 (reconcile) needs todo 1's context and both write to the SAME file
> (`tradfi_consolidated_closeout_2026_07_18.md`) as todo 10 of the parent extraction already touched — this whole plan's
> edits to that file must run as one serial pass, and todo 3 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **Verify each of the parent extraction's 9 non-todo-10 todos actually landed with real evidence**
      — VERIFIED 2026-08-04 (slot-13, infra→review). Per-todo evidence confirmed:

      1. **MVP cell wiring** ✅ — Audit report at `plans/audit/results/tradfi_mvp_cell_wiring_and_pipeline_verification_2026_08_04.md`
                                 (20,195 bytes) exists; commit `unified-trading-pm@cc9e1d144` (`docs(plans): tradfi MVP cell wiring-proof +
                                 data-pipeline re-verification audit`) confirmed on origin. Report contains per-cell IS/MTDS availability-index
                                 pass/fail verdicts with live-read row counts; NO cell has paper/live wiring proven (TradFi is batch-only per
                                 `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md:82`). Both IS + MTDS availability-index reads
                                 executed against live prod data 2026-08-04.

                              2. **CME billing-gate verification** ✅ — Doc at `plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`
                                 has a clear "2026-07-31 (slot 4, review)" Progress Log entry: `VENUE_DATA_TYPE_CAPABILITIES["CME"]` declares only
                                 `{ohlcv_1s, ohlcv_1m}` — `mbp_10`/`trades`/`tbbo` absent entirely; billing enforcement confirmed live via
                                 `databento_subscription_allowlist.py`'s `LEVEL_MAX_LOOKBACK_DAYS` and unit-tested in
                                 `tests/unit/test_databento_subscription_allowlist.py`. Clean pass, no code shipped (read-only audit).

                              3. **KRX + FX KRW registry-vs-adapter** ✅ — Archived KRX doc at `plans/archive/issues/krx_intraday_ohlcv_registry_vs_adapter_mismatch_2026_07_12.md`
                                 exists (status: resolved). Live code grep confirmed: (a) `expected_coverage.py` still declares `"KRX": ["ohlcv_24h"]`
                                 only; (b) `VENUE_DATA_TYPE_CAPABILITIES["KRX"]` agrees; (c) `_umi_yahoo.py::route_yahoo_tradfi` honest-empty guard
                                 still live (`if data_types and "ohlcv_24h" not in data_types: return pd.DataFrame()`). FX KRW cell: confirmed
                                 no analogous gap (`expected_coverage.py` → `"FX": ["ohlcv_24h"]`, `VENUE_DATA_TYPE_CAPABILITIES["FX"]` agrees,
                                 `fetch_yahoo_fx` hardcodes `data_type="ohlcv_24h"`, same honest-empty guard applies). Both PASS.

                              4. **Adapter dead-code audit** ✅ — Issue doc at `plans/active/issues/tradfi_adapter_dead_code_fallback_audit_2026_07_25.md`
                                 (33,929 bytes) exists with 11 tracked todos across 3 repos (instruments-service, market-tick-data-service,
                                 execution-service). Headline finding: `massive.py` is live/tested/wired, contradicting codex SSOT claim of
                                 deletion — flagged as big finding. 21/29 MTDS files, 8/11 IS files clean; no duplicate-implementation
                                 violations found.

                              5. **Billing-entitlement classification** ✅ (WORK DONE, UAC SHA MIS-CITED IN PARENT) — MTDS commit `b0d44fb2`
                                 (`feat(databento): classify billing-guard rejections as honest-absence (SKIP)`) confirmed on origin, adds
                                 `_classify_databento_exception` with `DATABENTO_LOOKBACK_EXCEEDED`/`DATABENTO_SUBSCRIPTION_GUARD` → `ErrorAction.SKIP`,
                                 14 unit tests (5 UAC + 9 MTDS). **UAC SHA CORRECTION**: parent plan's checkbox cites `UAC@f2a86e1e` but that
                                 commit (`feat(tradfi): canonicalize ICE qualifier suffixes`) is the WRONG change — the REAL UAC billing-
                                 entitlement commit is `9fd24804` (`feat(errors): classify Databento billing-guard rejections as SKIP (honest
                                 absence)`). Both error codes ARE live on `origin/live-defi-rollout` in
                                 `unified_api_contracts/canonical/crosscutting/errors/tradfi.py` (confirmed via `git grep`). The parent
                                 plan's SHA citation is wrong; the work itself is genuinely shipped. **Not a blocker** — note this for the
                                 reconciliation pass (todo 2 of this plan) to correct the citation when flipping the closeout doc's checkbox.

                              6. **Data-status page canonical ids** ✅ — Doc at `plans/active/data_status_page_ux_and_canonicalisation_2026_07_16.md`
                                 (54,913 bytes) has "2026-07-27 (slot-8, review) — tradfi native-extract todo 6" Progress Log entry: catalogue
                                 Surface A migration landed live 2026-07-25 (`instruments-service@52d8b3ef`); `list_upcoming_expiries_page(asset_group="tradfi")`
                                 returns 149,957 rows, every sampled `instrument_id` fully canonical; venue-lookup gap fix confirmed to hold
                                 (CME/NYSE/NASDAQ/CBOE/ICE → TRADFI via canonical UAC registry). deployment-api commit `c19edcc` exists on origin.

                              7. **Distinct-values census** ✅ — Doc at `plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md`,
                                 status: `complete`, archived 2026-07-28. The 2026-07-28 tradfi live-evidence run recorded in the doc: 3 named
                                 dupes (FUTURE/future/FUTURES, EQUITY/equity, BARCHART) are NOT zero but ARE explained (case-drift owned by
                                 in-flight master_data_canonicalisation migration; BARCHART matches standing operator quarantine ruling). One
                                 new P2 finding (rollup-backed `/distinct-values` under-reports case-drift + 2 wrong-axis clusters). Satisfies
                                 the todo's "or explicitly explained" acceptable outcome.

                              8. **3 denominator/catalogue findings** ✅ — All 3 cited docs confirmed to exist: (1)
                                 `plans/archive/issues/tradfi_instrument_type_migration_read_stale_legacy_object_2026_07_17.md` (archived, status:
                                 resolved) — 153 KRX duplicate row_keys re-verified **0** on canonical composite; (2)
                                 `plans/archive/issues/phantom_captures_tradfi_2026_06_28.md` (archived, status: resolved) — blank-`data_type`
                                 rows now **0** (was 1,083 on 2026-06-28); ICE/FX phantom cohort deferred (needs GCS listing, per conflict-
                                 precedence note); (3) `plans/archive/issues/tradfi_expected_reason_attempted_failed_misclassification_2026_07_15.md`
                                 (archived, status: resolved) — **0** current `attempted_failed` rows carry `EXPECTED_*`-prefixed `error_reason`
                                 (writer guard held 16 days). All counts re-measured via live `read_availability_index()` (single consolidated-
                                 parquet read, no GCS walk). Writer identity not found — reported honestly.

                              9. **KRX name-column** ✅ — (a) Catalogue-as-SSOT decision CONFIRMED still stands: no `name` field exists in
                                 manifest schema/writer; (b) name column ALREADY LANDED LIVE via daily `lifecycle-catalogue-regen-tradfi` Cloud
                                 Run Job (green every day 2026-07-22 through 2026-07-31); live-read confirms all 6 KRX single-stock-equity
                                 rows carry `name` column (SK Hynix, Hyundai Motor, Samsung Electronics). Side finding: weekly full-regen job
                                 had 3 consecutive failures — RESOLVED 2026-08-01, see
                                 `plans/archive/issues/tradfi_catalogue_full_regen_job_failing_2026_07_31.md`.

                              **Overall verdict: 9/9 confirmed real. TODO 5's UAC SHA is mis-cited in the parent plan (`f2a86e1e` should be
                              `9fd24804`) but the work itself is genuinely shipped and verified live on origin. Fix the SHA citation during the
                              reconciliation pass (todo 2 below).**

- [x] ✅ [REVIEW] P1. **Reconcile `tradfi_consolidated_closeout_2026_07_18.md`'s own 9 corresponding native checkboxes**
      — unified-trading-pm@860f3f529. MVP-cell table: all 6 rows updated with fresh IS/MTDS evidence; 0 "NOT VERIFIED"
      cells remaining. `[DATA] P2` checkbox flipped `[x]`. Phase A2+C digest: A2 and Phase C item-level items reconciled
      (parent-extraction todos 2-9 all done). KRX name-column note updated (name column live via daily regen). 3
      deferred native todos re-checked: adapter smoke (still 0 tradfi-scoped), live defects (still conflict-gated),
      BLOCKED-INFRA (still blocked — catalogue rebuild+promote FINAL STEP still pending). Split-notice
      catalogue-migration line already corrected by 2026-07-31 sweep, live re-verified (instruments-service@52d8b3ef on
      LDR). No gate cleared on any deferred item — no new todo/plan needed.
- [x] ✅ [DOC] P1. **Archive `tradfi_consolidated_native_ao_extract_2026_07_25.md`** — DONE 2026-08-04 (slot-12,
      infra→data_engineering). Archived via the standard 6-step ritual: Deferred items confirmed tracked elsewhere,
      archive banner added, codex-alignment confirmed clean (no new contracts), all 12 corpus referrers updated to
      archive path, `locked_by` confirmed empty, plan moved to `plans/archive/2026_07/`.

## Progress Log

- **context-scout 2026-08-03**: re-verified context_scope (4 entries) — still accurate (finalize gate, code-free), no
  changes needed.
- **2026-08-04 (slot-13, infra→review) — todo 1 verified**: re-checked all 9 non-todo-10 parent-extraction todos against
  live evidence. 8/9 confirmed with real files/commits/Progress-Log entries. 1 SHA citation error found (todo 5: parent
  plan cites `UAC@f2a86e1e` — ICE qualifier canonicalization — the real billing-entitlement commit is `UAC@9fd24804`).
  The work itself IS genuinely shipped and verified live on origin; only the citation is wrong. This should be corrected
  during the reconciliation pass (todo 2) when flipping the closeout doc's own checkbox.
