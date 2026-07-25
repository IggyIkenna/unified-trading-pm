---
doc_type: plan
title: TradFi consolidated close-out — one-pass code→migrations→coverage→smoke-test to MVP-backfill-ready
summary:
  Coordination index (umbrella) that AGGREGATES (references, does not duplicate) every open tradfi + tradfi-touching
  IS/MTDS plan/issue into ONE ordered pass, mirroring cefi_consolidated_closeout_2026_07_18.md. **2026-07-24 line-cap
  remediation** trimmed the doc from 2549 lines to an umbrella-eligible coordination index — the manifest/content
  id-canonicalisation completion work (Phase A1 residual + Phase B/B.5), the download/backfill throughput follow-ups
  (Phase A3/A3.1), and the Phase-D terminal gate were forked verbatim to 3 sibling plans (see `related:` below); this
  parent retains the ground-truth context, MVP universe, Phase A2 (adapter/registry correctness), Phase C
  (data-status/honest-coverage), the aggregated reference index, and a condensed milestone summary of the full
  historical Progress Log (full detail lives on the 3 children now). GROUND-TRUTH CORRECTION (measured live 2026-07-18,
  superseding this plan's own first-draft "largely done" verdict) — the persisted tradfi manifest and catalogue are ~100
  percent NON-canonical for derivatives at the plan's outset; see the 3 children for how much of that has since been
  closed.
status: active
nature: process
asset_group: [tradfi]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-service,
    deployment-api,
    features-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [
    tradfi,
    close-out,
    consolidation,
    canonicalisation,
    instrument-id,
    manifest,
    honest-coverage,
    backfill,
    throughput,
    mvp,
    umbrella,
  ]
related:
  [
    /plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md,
    /plans/active/tradfi_backfill_throughput_followups_2026_07_24.md,
    /plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md,
    /plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
    /plans/active/tradfi_massive_dual_source_2026_05_28.md,
    /plans/active/tradfi_multisource_backfill_2026_06_22.md,
    /plans/active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md,
    /plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
    /plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md,
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/archive/2026_07/data_pipeline_e2e_check_2026_07_10.md,
    /plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md,
    /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
    /plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
  ]
created: 2026-07-18
last_updated: "2026-07-24"
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [tradfi_manifest_content_recovery_completion_2026_07_24, tradfi_backfill_throughput_followups_2026_07_24]
gate_on_depends:
  true # mechanism note: regen_backlog_from_plan.py's gate_on_depends holds the WHOLE plan (every todo, incl. the
  # otherwise-unrelated Phase A2 adapter/registry todos), not just the 2 todos this was written for — Phase C
  # (data-status/honest-coverage) is gated on Phase B, which forked to
  # tradfi_manifest_content_recovery_completion_2026_07_24; the BLOCKED-INFRA "Certify tradfi Layer-1" todo is gated on
  # the catalogue rebuild+promote, which forked to tradfi_backfill_throughput_followups_2026_07_24 — both were real,
  # un-machine-enforced cross-plan gates found by the 2026-07-24 AO-flip-safety audit; encoded here so a future
  # `assigned_vm: planning` flip can't dispatch Phase C or BLOCKED-INFRA before their real prerequisites land (the
  # whole-plan gate is broader than intended but is the accepted cost of the mechanism, not restructured here).
source:
  Operator, 2026-07-18 — after spotting DERIBIT:FUTURE:AVAX@LIN-20260718 missing its quote and then seeing raw symbols
  in tradfi parquet names, manifest entries, and the instruments data-status page/catalogue, directed a single one-pass
  tradfi close-out mirroring the cefi one that aggregates ALL tradfi IS/MTDS plans+issues — "one pass get all the code
  ready then migrations then anything data status and honest coverage related and then smoke test the backfills again
  with data-pipeline-check-mtds and data-pipeline-check-is skills adapted to tradfi so we know its complete and ready
  for mvp backfills" (S&P index futures + index options + delta-one single-stock equities + CME BTC/ETH futures+options
  + daily treasuries + daily KRW). Authored + ground-truth-verified from a 3-agent doc audit + direct live GCS reads
  (slot-3, 2026-07-18). **On 2026-07-24** the doc was trimmed + split 3 ways per the operator-approved plan-hygiene
  line-cap remediation (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md` row 29) — this doc had grown to
  2549 lines (over the 2000L umbrella ceiling) via an ~1700-line tick-by-tick Progress Log; content moved verbatim to
  the 3 children in the related list above, and this parent is now a trimmed coordination index (the `umbrella=true`
  frontmatter key that carried this was later stripped 2026-07-24, ruled inert workspace-wide).
---

# TradFi consolidated close-out — one pass to MVP-backfill-ready

> **Purpose.** Coordination index (umbrella) that aggregates every open tradfi + tradfi-touching IS/MTDS plan/issue into
> a single ordered pass. This plan **references** the source docs; it does not duplicate them. Close a track by closing
> its source doc(s), then tick it here. Mirrors `cefi_consolidated_closeout_2026_07_18.md`; ordered per the operator's
> directive: **Phase A code → Phase B migrations → Phase C data-status/honest-coverage → Phase D re-smoke-test →
> MVP-backfill-ready.**

## Split notice (2026-07-24 — plan-hygiene line-cap remediation)

> **This plan was trimmed from 2549 lines and forked 3 ways**, per the operator-approved split in
> `/plans/active/issues/plan_line_cap_remediation_2026_07_23.md` (row 29). The 3-way split was overwhelmingly driven by
> an ~1700-line tick-by-tick Progress Log sitting next to a small tail of genuinely open todos — every todo and every
> Progress Log line was moved **verbatim** to its destination, nothing was summarized, rewritten, or dropped. This
> parent stays under the 2000-line umbrella ceiling as a trimmed coordination index (the `umbrella=true` frontmatter key
> was later stripped 2026-07-24, ruled inert workspace-wide and absent from PLAN_FORMAT.md's schema).
>
> | Child plan                                                                                                               | Carries                                                                                                                                       |
> | ------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
> | [`tradfi_manifest_content_recovery_completion_2026_07_24.md`](tradfi_manifest_content_recovery_completion_2026_07_24.md) | Phase A1 residual + Phase B/B.5 — the catalogue/manifest/GCS-filename/tick-content id-canonicalisation completion work (the biggest of the 3) |
> | [`tradfi_backfill_throughput_followups_2026_07_24.md`](tradfi_backfill_throughput_followups_2026_07_24.md)               | Phase A3/A3.1 — download/backfill throughput follow-ups (DNS-starvation fix, T+1 job, OOM hardening, Databento e2e throughput optimization)   |
> | [`tradfi_phase_d_terminal_gate_2026_07_24.md`](tradfi_phase_d_terminal_gate_2026_07_24.md)                               | Phase D — the post-migration all-shards re-smoke-test terminal gate                                                                           |
>
> **Per-child open-todo digest (2026-07-24, so this split is AO-legible without opening the children)**:
>
> - `tradfi_manifest_content_recovery_completion_2026_07_24.md` — **8 open** (2×P0, 5×P1, 1×P2, re-verified 2026-07-25
>   against the child's own checkboxes — down from the earlier 11-open/5×P0 count). Top P0s still open: (1) **Migrate
>   the catalogue (Surface A)** via `canonicalize_tradfi_catalogue_usd_lin_*.py` — NOT yet executed (DURABILITY TRAP: a
>   `prod/n`-only rewrite silently reverts on the next `build_instrument_catalogue.py` rebuild — must also migrate the
>   per-day corpus); (2) **Migrate GCS filenames + tick CONTENT (Surfaces C+D)**. The manifest migration (Surface B) is
>   now DONE + RE-VERIFIED LIVE 2026-07-25, and the enumeration-driven-migration casing sub-scope CLOSED 2026-07-25 (its
>   semantic-mislabel + null/blank residual moved to a separate open P1) — both are no longer open P0s.
> - `tradfi_backfill_throughput_followups_2026_07_24.md` — **6 open as of 2026-07-25 (was 11 at this digest's 2026-07-24
>   generation; 3 more shipped independently since — SIGKILL verify, phantom-row retirement, concurrency-cap raise —
>   corrected via plan-reconcile; expect this to drop further once tradfi batch2 lands)**. Top P1s: (1) Backfill-VM
>   startup OOM rc137 + OOM remediation baked default + consolidator throughput/backlog monitor (3 sub-issues bundled);
>   (2) TradFi has NO working T+1 forward-fill job — add source-scoped `…-tradfi-databento-t1-recon` Cloud Run job.
> - `tradfi_phase_d_terminal_gate_2026_07_24.md` — **2 open** (1×P0, 1×P1). The P0: MVP backfill readiness gate — run
>   the tradfi MVP backfills only after A-D are green; **still blocked** on the chain-bundle sampler follow-up. The P1:
>   post-full-backfill `/data-pipeline-reconciliation` RUN checkpoint, gated on the P0.
>
> **Retained here**: the ground-truth verdict + MVP universe (foundational context for all 3 children), Phase A2
> (adapter/registry correctness), Phase C (data-status + honest-coverage), the aggregated Codex SSOT + source-doc index,
> and a condensed milestone summary replacing the full tick-by-tick Progress Log (see the 3 children for full historical
> detail on their respective workstreams).

## Ground-truth verdict (measured live 2026-07-18 — supersedes the first-draft "largely done" claim)

The operator was right: tradfi is overwhelmingly raw. Direct reads of the live prod buckets, NOT the migration docs'
claims:

| Surface                                                              | Canonical (`@LIN`/`@INV`) for FUTURE/OPTION | Reality                                                                 |
| -------------------------------------------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------- |
| Catalogue `instruments-store-tradfi/prod/catalog.parquet`            | **0 of 1,111,322** rows                     | raw/bare (e.g. `CBOE:FUTURE:VX/F1`, `CME:FUTURE:GCQ26`)                 |
| Manifest `market-data-tick-tradfi/_index/availability_index.parquet` | **0** across all years                      | 2026 alone: 568,165 raw (`EWF6_P6490`, `ESM0_P2500`) + 63,661 malformed |
| Tick parquet **filenames** (equities / futures_chain)                | canonical                                   | `NASDAQ:EQUITY:AAPL-USD.parquet`, `CME/CRUDE.parquet` (bundled)         |
| Tick parquet **content** `instrument_key`/`symbol` column            | TBD (verify in Phase A)                     | column present; forward-write may be canonical, historical not          |

**Conclusion**: the id-canonicalisation is barely started on the derivative **id columns** (manifest + catalogue),
despite the migration scripts existing and a VM run being logged — the run either targeted a narrow slice or a different
surface, and the live manifest/catalogue never converged. The four surfaces (GCS filename / parquet `instrument_id`
column / manifest key / reader) are the CeFi model; tradfi is done on filenames only.

**Live confirmation (operator, 2026-07-18, the deployment-api instruments data-status "Upcoming expiries" widget)**:
real catalogue rows render as `CME:OPTION:E3AN6 C7960` / `E3AN6 C7975` / `E3AN6 C8000` — raw weekly-option product code
(`E3AN6`), a **literal SPACE** as sub-delimiter (the banned-whitespace class), no `@LIN`, no `-USD`, no `YYYYMMDD`,
strike glued as `C7960`. Target for this exact row: `CME:OPTION:SP500-USD@LIN-<expiry>-7960-C`. This IS the catalogue
surface — Phase A1 (writer) → B (migrate `prod/catalog.parquet`) → C (widget renders canonical) fix it end to end.

## MVP universe (operator-defined 2026-07-18 — the Phase-D readiness target)

- **S&P index futures** (ES) + **S&P index options**.
- **Delta-one single-stock equities** (S&P/NASDAQ single names — already canonical on filenames; verify the id columns).
- **CME BTC/ETH/MBT/MET futures** — FUTURES ONLY, no crypto options (operator 2026-07-21 "no CME option for BTC and
  ETH"; `option_underliers={ES}`).
- **Daily Treasuries** (yields, `ohlcv_24h`) + **daily KRW** (FX daily).
- **2026-07-21 +409 expansion** (`uac@afa2dd64`→`22e6a534`, Progress Log tick "MVP def expanded"): VIX FUTURE (CBOE),
  CBOE treasury-yield INDEX (US3M/US2Y/US5Y/US10Y/US30Y), and FX KRW (`FX:SPOT_PAIR:KRW-USD`) added to the MVP universe
  alongside the CME crypto futures above.

Everything below is scoped so these cells are canonical, honestly-covered, and smoke-tested green before MVP backfill.

> **Data-type × source priority for MVP backfills (operator, 2026-07-18 — supersedes any "restore mbp_10" framing):**
> For **Databento** tradfi, the billing entitlement is **1-month L3 + 1-year L1** — so `mbp_10`/`trades`/`tbbo` are
> **billing-gated by design (documented, NOT a bug to fix)**. The MVP backfill data_type for the instruments we care
> about is **`ohlcv_1m` only** (it has FULL history). The venue capability _declaration_ MAY still enumerate what's
> _possible_ (mbp_10/trades/tbbo within their limits), but the actual **MVP backfills = 1m candles**. For **daily**
> cells we use **Yahoo Finance** as the source (still gives **24h / 1d**): daily Treasuries `ohlcv_24h` + daily **KRW**
> FX. So Phase D smoke-tests + Phase-D MVP backfills iterate: Databento intraday shards → `ohlcv_1m`; Yahoo daily shards
> → `ohlcv_24h`/`ohlcv_1d`. This DE-SCOPES the A2 "mbp_10/trades/tbbo restoration" item to "declaration reflects the
> documented billing reality" (verify, don't chase L3 full history).

### MVP cells — proven wired (backfill=paper=live) vs. declared in-scope only

| MVP cell                                      | Declared in-scope                | Backfill proven (this plan's Phase-D condensed summary above)                                                            | Paper/live wiring proven  |
| --------------------------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ------------------------- |
| S&P index futures (ES)                        | yes                              | partial — `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` shows the ohlcv 1s+1m backfill IN FLIGHT, not complete | NOT VERIFIED IN THIS PASS |
| S&P index options                             | yes                              | not launched — singleton Databento lock held by the futures fleet (same doc)                                             | NOT VERIFIED IN THIS PASS |
| Delta-one single-stock equities               | yes                              | filenames already canonical; id-column verification still open (Phase A2)                                                | NOT VERIFIED IN THIS PASS |
| CME BTC/ETH/MBT/MET futures                   | yes (+409 expansion, 2026-07-21) | backfill fleet launched at scale (2026-07-21 Progress Log); completion not re-confirmed                                  | NOT VERIFIED IN THIS PASS |
| Daily Treasuries + daily KRW (Yahoo)          | yes                              | KRX equities gap closed 2026-07-22 (new Yahoo-daily launcher); Treasuries backfill status not re-confirmed               | NOT VERIFIED IN THIS PASS |
| VIX FUTURE (CBOE) + CBOE yield INDEX + FX KRW | yes (+409 expansion)             | part of the same 2026-07-21 backfill fleet launch; completion not re-confirmed                                           | NOT VERIFIED IN THIS PASS |

> **Honest finding (this pass, 2026-07-24)**: every "Backfill proven" cell above is sourced from this plan's own
> Progress Log / child-plan digests — none is a fresh re-verification. The "Paper/live wiring proven" column is entirely
> unpopulated: nothing in this plan, its 3 children, or the Aggregated-source-docs index references a paper-trading
> ledger, live-trading ledger, or the epsilon=0 batch=live=paper determinism proof
> (`/codex/09-strategy/operational/paper-batch-live-reconciliation.md`) for ANY tradfi MVP cell — this plan's scope is
> data-backfill readiness only, and the paper/live wiring question has not been investigated by any tradfi doc found in
> this pass.

- [ ] [DATA] P2. Determine, per MVP cell in the table above, whether it has actually been proven wired through
      backfill=paper=live — cite the actual paper-trading ledger / live-trading ledger / batch-rerun determinism proof
      (epsilon=0 per `/codex/09-strategy/operational/paper-batch-live-reconciliation.md`) per cell, or state plainly
      that no such proof exists yet for that cell. Also re-verify each "Backfill proven" cell against a fresh
      `data-pipeline-check-is`/`data-pipeline-check-mtds` run rather than the last-recorded Progress Log entry.
      Definition-of-done: 0 remaining "NOT VERIFIED IN THIS PASS" cells in the table, each replaced with a real
      verdict + evidence citation (report path / ledger query / dispatch_id).

---

## Remaining in this coordinator — Phase A2 (adapter/registry correctness) + Phase C (data-status/honest-coverage)

> Phase A1 (writer convergence) and Phase B/B.5 (the migration itself) forked to
> `tradfi_manifest_content_recovery_completion_2026_07_24.md`; Phase A3/A3.1 (download/backfill throughput) forked to
> `tradfi_backfill_throughput_followups_2026_07_24.md`; Phase D (the terminal gate) forked to
> `tradfi_phase_d_terminal_gate_2026_07_24.md`. The two sections below (A2 + C) are the only phases that stayed on this
> parent, unchanged.

### A2 — Adapter / registry correctness (so the MVP cells actually fetch + classify)

- [ ] [BACKEND] P1. **CME `mbp_10`/`trades`/`tbbo` `VENUE_DATA_TYPE_CAPABILITIES` restoration** + no `ohlcv_15m/24h`
      aggregation writer exists (leaves `vix_features` unfed) —
      `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`. Gate:
      `VENUE_DATA_TYPE_CAPABILITIES` verified to declare mbp_10/trades/tbbo as billing-gated (per the "Data-type ×
      source priority" note above — declared possible, not chased to full L3 history), and a recorded decision on
      whether an `ohlcv_15m/24h` aggregation writer ships to feed `vix_features`. (repos: market-tick-data-service,
      unified-api-contracts)
- [ ] [BACKEND] P2. **KRX equities intraday registry-vs-adapter mismatch**
      (`krx_intraday_ohlcv_registry_vs_adapter_mismatch_2026_07_12.md`, RESOLVED — this is about KRX (Korean)
      **equities** `ohlcv_1m`/`ohlcv_15m` registry coverage, a separate cell from the declared MVP **FX KRW** cell
      (`FX:SPOT_PAIR:KRW-USD`, daily); verify the equities fix still holds, and separately verify the FX KRW cell has no
      analogous registry-vs-adapter gap). **IBKR `_SEC_TYPE_MAP` / Databento `_resolve_product_root` / combo-leg** —
      DONE in code (`canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`, single-leg todo already `[x]`).
      **`mvp_mode` dead gate** decision (`tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md`). Gate: KRX-equities
      mismatch re-verified still resolved, the FX KRW cell separately confirmed to have no registry-vs-adapter gap, and
      the `mvp_mode` dead-gate decision (wire a real caller or remove) is made and recorded. (repos:
      instruments-service, market-tick-data-service)
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
- [ ] [BACKEND] P1. **NEW 2026-07-24 — two live defects found by the raw-tick reconciliation's 3rd run: (1) ICE/KRX/FX
      (all Yahoo-exclusive per SSOT) captured under `source=databento` since ~2026-07-18 (real values, wrong provenance
      stamp, root cause not yet found — hypothesis: the 2026-06-24 DATABENTO-FIRST change missing a per-venue
      `_VENUE_SOURCE_EXCLUSIONS` guard); (2) FX `SPOT_PAIR` manifest `instrument_id` is 0% well-formed across its entire
      2020-2026 captured history (the GCS object + content are fine — this is a pure manifest-copy defect).** Positive
      counter-finding same run: captured-row id-form canonicality measured ~99.3% corpus-wide (up from the 07-21
      report's 30.8%), independently corroborated by a 99.95%-clean reconstructed-path check — strong evidence the
      Phase-B migration in `tradfi_manifest_content_recovery_completion_2026_07_24.md` has substantially landed; that
      plan's relevant todo should be confirmed/flipped against this evidence rather than treated as still-open. Full
      evidence for both defects + the `_quarantine/` register going stale (146K→400K+ objects in 3-4 days, register
      still says "deleted"): `/plans/active/issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`. (repos:
      market-tick-data-service, unified-api-contracts, unified-trading-pm)

## Phase C — data-status + honest-coverage (gated on Phase B)

- [x] ✅ [BACKEND] P1. **Honest-coverage for tradfi**: out-of-window `expected_unattempted` clipping
      (`/plans/archive/issues/honest_coverage_out_of_window_expected_unattempted_not_clipped_2026_07_16.md`, RESOLVED —
      verify for tradfi); reference-data shard-dimension model
      (`honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`); coverage-floor registry
      cross-propagation (`coverage_floor_registries_no_cross_propagation_2026_07_17.md`). Gate: all 3 cited findings
      re-verified against live tradfi data (clipping holds, shard-dimension model applied, coverage-floor registries
      cross-propagate) with the results recorded. **VERIFIED 2026-07-25, all 3 against LIVE tradfi manifests
      (`market-data-tick-tradfi-prd-central-element-323112` 5,826,709 rows +
      `instruments-store-tradfi-prd-central-element-323112` 27,251 rows, both freshly downloaded):** (1) **out-of-window
      clipping — STILL HOLDS.** All 400,643 `expected_unattempted` rows carry blank `error_reason` (never an
      `EXPECTED_*` reason, so `expected_unattempted_known_empty` stays empty for tradfi exactly as the archived doc
      predicted); 2,647,410 of 3,802,192 `empty_confirmed` rows carry an `OUT_OF_COVERAGE_WINDOW_REASONS` member
      (`EXPECTED_INSTRUMENT_NOT_LISTED`/`_DELISTED`/`_NO_PROVIDER_COVERAGE`/`_OUT_OF_COVERAGE_WINDOW`/
      `_DEPRECATED_DATA_TYPE`) and are clipped from both numerator+denominator by deployment-api's
      `coverage.py::oow_reason_mask` against UAC's live `OUT_OF_COVERAGE_WINDOW_REASONS` frozenset — code path unchanged
      since the 2026-07-16 verification. (2) **reference-data shard-dimension model — CORRECTLY APPLIED.** All 7 tradfi
      IS venues show real per-`(venue, instrument_type)` splits with no blank-collapse (CME:
      FUTURE=2024/COMBO=1995/OPTION=1995; CBOE 5 types; ICE/NYSE/NASDAQ/KRX/FX all multi-type) — the 2026-07-07
      `_split_by_instrument_type` writer fix is live for tradfi; residual blank-`instrument_type` rows (4,504/27,251)
      are exclusively `EXPECTED_WEEKEND`/`_HOLIDAY`/`_PRE_VENUE_LAUNCH` non-trading pre-stamps (already documented as
      "no fix needed" in the source doc) + 93 genuine unclassified adapter errors, not a writer regression; no
      DERIBIT-COMBO-style fake-venue analog exists in tradfi's venue list. (3) **coverage-floor cross-propagation — WAS
      STILL LIVE, NOW FIXED.** Confirmed the cited CME mismatch was still unresolved as of session start
      (`coverage_starts.py:175` `"CME": date(2010, 1, 1), # TODO verify` vs `venue_mapping.py:334` `"CME": "2020-01-01"`
      no TODO). Probed the live MTDS manifest per `coverage_starts.py`'s own docstring instruction — earliest CME
      `capture_status=captured` row is 2020-01-01, every pre-2020 date is `empty_confirmed`/`expected_unattempted` —
      confirming `venue_mapping.py` was right. **Shipped: unified-api-contracts@32b2879c** updates
      `TRADFI_SOURCE_COVERAGE_START["CME"]` to `date(2020, 1, 1)` and drops the TODO; gate `dbd6491`→`32b2879c` all
      green (583s, sentinel `dbd649140e946cbcf91275a6bd10bd73c12516a5`). Matching P2 todo flipped in
      `coverage_floor_registries_no_cross_propagation_2026_07_17.md`. The other 2 registries (TARDIS `# TODO verify`,
      the 8 CeFi mismatches, POLYMARKET, DeFi drifts) are that doc's own separately-tracked P1/P2/P3 items, out of this
      tradfi-scoped todo's gate.
- [ ] [CODE] P2. **Billing-gated Databento L2/L3 cells must not count as `attempted_failed`.** Databento tradfi's
      billing entitlement is 1-month L3 + 1-year L1 (see the "Data-type × source priority" note above), so
      `mbp_10`/`trades`/`tbbo` lookback/entitlement-guard rejections are EXPECTED, not real failures — but no
      classification mechanism currently excludes them, so a hit outside the entitlement window records
      `attempted_failed` today. Wire a durable classification (a new UAC `classify_venue_error()` outcome or
      `expected_reason` value) that recognizes the billing-entitlement-guard rejection and routes it to
      `empty_confirmed`/`expected_unattempted` instead of `attempted_failed`. Definition-of-done: a unit test asserting
      a simulated entitlement-guard rejection for `mbp_10`/`trades`/`tbbo` on a Databento tradfi shard yields 0
      `attempted_failed` rows, plus a live manifest spot-check showing the count trending down after the fix ships.
      (repos: unified-api-contracts, market-tick-data-service)
- [ ] [BACKEND] P1. **Data-status page renders canonical tradfi** (the "Upcoming expiries" + instruments/catalogue
      views) — `data_status_page_ux_and_canonicalisation_2026_07_16.md`; deployment-api legacy venue-lookup gap
      (`deployment_api_legacy_instrument_availability_venue_lookup_gap_2026_07_13.md`, RESOLVED — verify tradfi). Gate:
      the "Upcoming expiries" widget + catalogue view render canonical ids for a live sample row (no raw
      `E3AN6     C7960`-style output per the Ground-truth verdict table above), and the venue-lookup gap fix is
      confirmed to hold for tradfi.
- [ ] [REVIEW] P1. **Run the already-shipped distinct-values/axis-value census for tradfi and verify 0 non-canonical**
      (supersedes the prior "RE-ADD the dimensions enumeration view" todo — that view already shipped live:
      deployment-api `GET /distinct-values/{asset_group}` + `GET /axis-value-census`, code at
      `deployment-api/deployment_api/routes/data_status/_distinct_values.py` + `_axis_census.py`; tracked corpus-wide in
      `/plans/active/distinct_values_noncanonical_audit_2026_07_20.md`). Call both endpoints for `asset_group=tradfi`
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
- [x] [BACKEND] P1. **KRX (Korean) equities carry a human-readable NAME across catalogue + manifest + data-status
      (operator, 2026-07-20)** — **instruments-service@6780f10e** (the 4th and last code surface; gate green **4712
      passed / 0 failed / 3 skipped**, `.qg_last_passed_sha == 9267e0ea` at ship time). _**CODE 4/4 LANDED 2026-07-20**
      — read-surface chain is complete and shipped: **UAC@f7e0301d** (first-class optional `InstrumentRecord.name` +
      `KRX_EQUITY_NAMES` bare-code→issuer-name SSOT, derived from the EXISTING `KrxEquityDef.name` — no new mapping
      invented, no provider re-fetch needed), **deployment-api@65f5593** (`name` on the Catalogue Explorer JSON route +
      the download-CSV, schema-aware read so a pre-`name` catalogue degrades to blank rather than raising),
      **deployment-ui@2ff1e61** (Name column, em-dash for honest-absent; `pw:L2 ✓`
      `tests/e2e/data-status-catalogue-name-column.spec.ts`). **instruments-service@6780f10e SHIPPED 2026-07-20**
      (`name` in `CATALOG_COLUMNS` + `_add_instrument_name` on-the-fly stamp mirroring
      `_add_mvp_column`/`_add_equity_tags`, + `name=eq.name` on the KRX records). *It was gate-blocked for ~4h on
      failures that were NOT from this work* — first the 5 UAC↔IS DeFi drift guards from UAC@3f79489f
      (METEORA/LIFINITY/PHOENIX + CHAINLINK/PYTH declared without matching IS adapter classes), then, once those
      cleared, a 6th unrelated cross-repo lockstep (`test_expected_matches_golden[sports]`, golden=27 vs actual=47, from
      uac@b6a1d83a adding 20 ODDS_API fan-out bookmakers). **Both were other agents' in-flight work and both
      self-resolved** — DeFi via is@793125ad + is@6506b505 (adapters wired + goldens regenerated), sports via
      is@9267e0ea (goldens regenerated). This deliverable deliberately did NOT touch either: no guard was weakened,
      excluded, or baselined, and no foreign golden was regenerated to force green. Ship gate at is@9267e0ea: **4712
      passed / 0 failed / 3 skipped, exit 0**. Residual DeFi coverage-honesty finding (3 live venues with measured-dead
      upstreams + `expected_coverage` not phase-gated), tracked in
      `/plans/archive/issues/uac_is_defi_oracle_dex_adapter_drift_2026_07_20.md`, was NOT this plan's to fix and is now
      RESOLVED — 2026-07-22, `uac@9a047a31` + `instruments-service@52a1cb53` (defi_consolidated_closeout_2026_07_18.md
      session), narrowed the 3 dead-upstream venues to `phase="pipeline"` + dropped their `expected_coverage.py` rows.
      **Verified on a SAMPLE (no full regen):** `_add_instrument_name` stamps `KRX:EQUITY:005930`→"Samsung Electronics",
      `KRX:EQUITY:000660`→"SK Hynix", `KRX:EQUITY:005380`→"Hyundai Motor", and also catches the legacy
      `KRX:EQUITY:005930.KS-USD` variant (same `base_asset`); non-KRX rows stay honestly blank. Live tradfi
      `prod/catalog.parquet` today has 10 KRX rows and NO `name` column — it appears on the next roll-up. **STILL
      OPEN:** (a) the availability-manifest `name` column (item 2 below) — deliberately NOT done here, the manifest is
      availability data and its shard-atom/writer is owned by another agent; catalogue-as-SSOT + display-time join is
      preferred; (b) the catalogue regeneration that makes the name land LIVE (main agent). **Audit of other
      opaque-coded venues:** KRX is the only venue needing this — DeFi pool addresses already carry human-readable
      `glued_pair_id` + `base_asset`, prediction conditionIds already carry `question`, sports fixtures already carry
      team names, and CME/CBOE/NASDAQ/NYSE roots are already readable._ KRX equities are identified by the 6-digit
      exchange code (`KRX:EQUITY:000660` = SK Hynix, `005930` = Samsung Electronics, `005380` = Hyundai Motor) — the
      code is the stable/unique official ticker (kept as the canonical `instrument_id`, analogous to
      `NASDAQ:EQUITY:AAPL`), but it is NOT human-readable. Add a first-class reference-data `name` field (romanized
      company name) resolved from a KRX code→name mapping (source: provider security description — Yahoo `.KS` /
      Databento — else a maintained KRX listing reference in instruments-service), and SURFACE it on every read surface:
      (1) deployment-api Catalogue Explorer + download-CSV (`instrument_id` + `name`), (2) the availability manifest
      (`name` column carried by the WRITER, never re-derived downstream), (3) the data-status dimensions view. GCS
      object PATHS keep the stable code id (paths must be stable/unique; names change on rebrand/merger) — the readable
      name rides as metadata/column, not in the path. Audit whether any other venue shares the numeric-code pattern.
      Regenerate catalogue + manifest so the name lands live; verify the Catalogue Explorer shows `SK Hynix` /
      `Samsung Electronics` next to the code. (repos: instruments-service, market-tick-data-service, deployment-api,
      deployment-ui)
- [ ] [BACKEND] P2. **NEW 2026-07-25 (plan-reconcile) — track the KRX name-column "STILL OPEN" work above as a real
      todo, not just prose behind a checked box.** The P1 item above is `[x]` (code shipped 4/4, catalogue-side name
      confirmed live), but its own STILL OPEN note names 2 pieces of work never separately tracked: (a) the
      availability-manifest `name` column (owned by another agent — the manifest's shard-atom/writer, not the catalogue)
      — deliberately deferred there in favor of catalogue-as-SSOT + display-time join; (b) the catalogue regeneration
      that actually lands the name LIVE (distinct from the code shipping — confirm this has happened since the
      2026-07-20 "10 KRX rows and NO name column" sample check, or run it). **Done when**: either both are confirmed
      already done with fresh evidence (a live catalogue read showing the `name` column populated for KRX rows), or both
      are executed and verified. Repos: instruments-service, market-tick-data-service, deployment-api.
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
  STEP" this todo's gate cites now lives on the sibling `tradfi_backfill_throughput_followups_2026_07_24.md` (gated on
  backfill completion — rebuild+promote the served catalogue so `mvp=True` reflects the +409 expansion), not on this
  parent directly — see that child for the current status.

## Plan-quality — AO-dispatch-readiness pass (owed)

- [ ] [REVIEW] P2. Run the same adversarial AO-dispatch-readiness pass that produced sports's Track Y findings A-G (the
      6 defect classes: bare section shorthand, ambiguous verbs, delete-tagging inconsistency, missing
      definition-of-done, stale checkboxes, digest-checkbox misuse — see
      `/plans/archive/2026_07/sports_consolidated_closeout_history_2026_07_24.md`'s "Track Y — PLAN-QUALITY REMEDIATION"
      section for the original method, extracted there by sports's own line-cap-remediation split) against this entire
      plan file: check for bare `§X` cross-doc shorthand used as a todo's sole meaning, ambiguous non-literal verbs
      (`absorb`/`incorporate`/`handle`/`address`), inconsistent delete-risk `[OPERATOR]` tagging, todos missing a stated
      definition-of-done, and stale checkboxes a later section already shows resolved. Definition-of-done: a filed
      finding list (or a stated "clean" verdict) covering all 6 categories, with any fixes applied directly or filed as
      follow-up todos. **Same-session spot-check (2026-07-24, this pass)**: no bare `§X`-as-sole-meaning or banned-verb
      instances found among this file's real (non-digest) `- [ ]` todos; delete-risk tagging on the real todos is
      consistent (no untagged prod-delete todo exists in this file); a full stale-checkbox + definition-of-done sweep
      across every real todo is still owed.

## Codex SSOTs (read before touching a phase)

`/codex/02-data/tradfi-databento-sourcing-ssot.md`, `/codex/02-data/availability-manifest-and-data-status.md`,
`/codex/02-data/honest-coverage-model.md`, `/codex/02-data/pipeline-mode-partition.md`,
`/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`,
`/codex/05-infrastructure/manifest-consolidator-ssot.md`, `/codex/05-infrastructure/vm-launcher-runbook.md`.

## Aggregated source docs (referenced, not duplicated)

> Each doc below carries its real repo-root-relative path + a condensed digest of its currently-OPEN top-level todos
> (unchecked `- [ ]` only), so an AO worker can dispatch off THIS doc without opening a dozen others. Digests generated
> 2026-07-24 via `grep -n '^- \[ \]'` per file; docs with 0 hits are closed/archived/record-only. Docs with >8 open
> todos list every P0/P1 in full and cap P2/P3 with a `+N more` marker (never a silent drop).

- **Child plans (forked from this parent, 2026-07-24 split — digested here too so this section alone is complete without
  needing the Split-notice table above)**:
  - [`plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md`](/plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md)
    (11 open — capped)
    - **[DATA] P0.** Migrate the catalogue (Surface A) via `canonicalize_tradfi_catalogue_usd_lin_*.py`
    - **[DATA] P0.** Enumeration-driven migration (SINGLE SOURCE OF TRUTH, operator 2026-07-18) — must be driven by the
      full distinct dimension-value set, not sampled shapes
    - +9 more (P0/P1/P2) — see file for the rest
  - [`plans/active/tradfi_backfill_throughput_followups_2026_07_24.md`](/plans/active/tradfi_backfill_throughput_followups_2026_07_24.md)
    (11 open — capped)
    - **[INFRA] P1.** Backfill-VM startup OOM rc137 + OOM remediation baked default + consolidator throughput/backlog
      monitor (3 sub-issues bundled)
    - **[DATA] P1.** TradFi has NO working T+1 forward-fill job — add source-scoped `…-tradfi-databento-t1-recon` Cloud
      Run job
    - +9 more (P1/P2) — see file for the rest
  - [`plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md`](/plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md)
    (2 open)
    - **[DATA] P0.** MVP backfill readiness gate — run the tradfi MVP backfills only after A-D are green; still blocked
      on the chain-bundle sampler follow-up
    - **[DATA] P1.** Post-full-backfill reconciliation RUN checkpoint (both raw-tick and candles layers), gated on the
      P0 above going green

- **ID-format**:
  - [`plans/active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`](/plans/active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md)
    - **[SCRIPT] P2.** Extend the 1-4 leg hard cap + logged-drop behavior to Deribit's existing combo builders
    - **[SCRIPT] P3.** Extend UAC's `build_leg()` with an opt-in venue-omission mode
  - [`plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md`](/plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md)
    - **[SCRIPT] P2.** DEX-pool catalog regeneration (finding 2, all 13 protocols)
    - **[DECISION] P2.** Confirm exact target quote-currency per on-chain-perp venue (finding 4)
  - [`plans/archive/issues/tradfi_cme_options_chain_legacy_layout_2026_07_10.md`](/plans/archive/issues/tradfi_cme_options_chain_legacy_layout_2026_07_10.md)
    (done) — 0 open todos (closed/archived/record-only)
  - [`plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md`](/plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md)
    (9 open — capped)
    - **[DATA] P1.** Retrofit the ~48 DeFi adapters that build `instrument_key` as an ad hoc f-string
    - **[DATA] P1.** Resolve the non-canonical TYPE-token question before retrofitting todo 1
    - **[DATA] P1.** Fix the real "no VENUE:TYPE: wrap at all" gap in both Prediction adapters
    - +6 more (P2/P3) — see file for the rest
  - [`plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md`](/plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md)
    - **[DATA] P0.** slot 6 (TradFi) — G4 `--apply` (databento/massive; daily listing)
    - **[DATA] P0.** R8-sports/pred gates (sports done 2026-06-11; prediction regen remains)
    - **[UAC] [IS] P1.** G1-ENUM present-set asymmetry — combo/chain underlyings get PHANTOM `expected_unattempted`
      seeds
    - **[CODE] P1.** slot 7 — post-apply consumer cleanups (execution-service defi loader, deployment-api
      FLAG-1/3/dedup)
    - **[INFRA] P1.** R5-fix-5 — restore manifest consolidator for `instruments-store-*` (+ defi data buckets)
    - **[CODE] P2.** WAVE 5 / live-side (gated, after batch migration)
    - **[DATA] P2.** R5-fix-7 — re-probe defi `lst_rates` + `dex_pools` post-R4 catalog re-promote

- **Manifest / v9 / status**:
  - [`plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md`](/plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/archive/issues/tradfi_manifest_row_loss_regression_2026_07_12.md`](/plans/archive/issues/tradfi_manifest_row_loss_regression_2026_07_12.md)
    (done) — 0 open todos (closed/archived/record-only)
  - [`plans/archive/issues/tradfi_manifest_cf4_source_and_cf7_phantom_gaps_2026_07_07.md`](/plans/archive/issues/tradfi_manifest_cf4_source_and_cf7_phantom_gaps_2026_07_07.md)
    (done) — 0 open todos (closed/archived/record-only)
  - [`plans/archive/issues/tradfi_manifest_consolidator_row_count_varchar_crash_2026_07_12.md`](/plans/archive/issues/tradfi_manifest_consolidator_row_count_varchar_crash_2026_07_12.md)
    (done) — 0 open todos (closed/archived/record-only)
  - [`plans/archive/issues/tradfi_expected_reason_attempted_failed_misclassification_2026_07_15.md`](/plans/archive/issues/tradfi_expected_reason_attempted_failed_misclassification_2026_07_15.md)
    (archived, `status: resolved` — 2 residual open items below)
    - **[DESIGN] P3.** Taxonomy decision: add `EXPECTED_SOURCE_NOT_AVAILABLE`/`EXPECTED_CHAIN_META_ROW_NOT_DOWNLOADABLE`
      to UAC's closed-set `EmptyConfirmedReason` enum
    - **[INVESTIGATE] P3.** The actual writer that produced the original 34,260 misclassified rows was never identified
  - [`plans/active/issues/phantom_captures_tradfi_2026_06_28.md`](/plans/active/issues/phantom_captures_tradfi_2026_06_28.md)
    - **[CODE] P2.** Diagnose tradfi phantom root cause (ICE/FX 309 phantoms predate billing lockdown; blank data_type
      1,083 pre-v9 rows)
  - [`plans/active/issues/cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`](/plans/active/issues/cross_cutting_manifest_canonicalisation_findings_2026_07_11.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`](/plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md)
    (9 open — capped)
    - **[OPERATOR] P0.** BLOCKED-OPERATOR-DECISION — coordinate a maintenance window for the prediction + tradfi
      consolidator crons before pausing either
    - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — Snapshot the prediction canonical manifest index and pause its
      consolidator cron
    - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — Apply `rebuild_prediction_manifest.py` (full date range),
      force-consolidate, re-verify fill rate
    - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — Resume the prediction consolidator cron; record before/after fill-rate
      evidence
    - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — Snapshot the tradfi canonical manifest index and pause its consolidator
      cron
    - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — Apply `rebuild_tradfi_manifest.py` (full date range),
      force-consolidate, verify fill rate + guardrail
    - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — Resume the tradfi consolidator cron; record evidence in the Progress
      Log
    - +2 more (P2/P3) — see file for the rest

- **Coverage / sourcing**:
  - [`plans/active/data_completion_tradfi_2026_07_15.md`](/plans/active/data_completion_tradfi_2026_07_15.md) (stale
    fork; 20 open — capped)
    - **[DATA] P0.** Phase 0 — layout audit (MANDATORY, blocking) — enumerate ALL top-level trees + nested layouts
      before the walk
    - **[DATA] P0.** G1.run `--apply-write` for tradfi — GATED, NOT runnable this wave
    - **[DATA] P1.** Verify the corpus venue / data_type strings are underscore-canonical (relabel `UNKNOWN`/blank
      drift)
    - **[DATA] P1.** E6 CF-7 relabel: `UNKNOWN`/blank venue + blank data_type → canonical
    - **[DATA] P1.** COVERAGE GAP → IN PROGRESS — tradfi equities/ETF (NYSE/NASDAQ) originally never genuinely ingested
    - **[CODE] P1.** tradfi could-exist denominator seed — build the `--catalog-path` parquet from the tradfi IS catalog
    - **[INFRA] P1.** Wire the tradfi `build_instrument_catalogue.py` daily rollup scheduler (GATED on gate-b capture
      restore)
    - **[DATA] P1.** R1 RUNBOOK — the tradfi `migrate_tradfi_to_v9_canonical --apply` MUST include `--also-legacy`
    - **[DATA] P1.** R2 DELETE-AFTER sweep — after the tradfi v9 `--apply` + G7 byte-verify, run the gated delete of
      old-format source paths
    - **[BLOCKED-CREDENTIALS] P1.** EIA live fetch + cassette recording — needs the free EIA API key
    - **[OPERATOR-DECISION] P1.** `altdata` home — revive `altdata` as a real `asset_group` vs model macro as a SHARED
      cross-asset axis
    - +9 more (P2/P3) — see file for the rest
  - [`plans/active/tradfi_multisource_backfill_2026_06_22.md`](/plans/active/tradfi_multisource_backfill_2026_06_22.md)
    - **[BACKFILL] P1.** Run the FX yahoo backfill to completion (operational)
    - **[TEST] P3.** NICE-TO-HAVE — deployment-service test skip resolves service name from worktree dirname
  - [`plans/active/tradfi_massive_dual_source_2026_05_28.md`](/plans/active/tradfi_massive_dual_source_2026_05_28.md)
    (`status: superseded`; 10 open — capped; most items below tagged OBSOLETE/WONTFIX in-doc but checkbox not yet
    flipped)
    - **❌ [UTL] P0.** OBSOLETE. Manifest consolidator dedup key omits `source` — no Massive fetches exist, moot
    - **[MTDS] P1.** Equity/ETF tick-level `trades`+`tbbo` — OPERATOR DECISION RESOLVED: NOT needed for TradFi MVP
      (connector must still implement)
    - **[UAC] [UTL] P1.** EXTRA Massive fields — DECISION FOR IKENNA (flag at plan-push)
    - **❌ [MTDS] P1.** OBSOLETE/WONTFIX. Add retry/backoff/rate-limit handling to `_get`/`_get_paginated` — no
      paid-tier fetch path to protect
    - **❌ [SCRIPT] P1.** OBSOLETE. Build the S3 flat-files bulk-backfill ingester — Massive removed as a tradfi source
    - **❌ [SCRIPT] P1.** OBSOLETE (no-longer-massive-relevant). Fix `backfill_tradfi_source_column.py` walk prefix
    - +4 more (P2) — see file for the rest
  - [`plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`](/plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md)
    - **[DESIGN] P2.** Decide whether real aggregated `ohlcv_15m`/`ohlcv_24h` TradFi bars are wanted (not just alert
      silence)
    - **[VERIFY] P3.** Trace the orchestrator/sentinel classification layer for `attempted_failed` vs `empty_confirmed`
  - [`plans/archive/issues/tradfi_databento_ohlcv_silent_zero_rows_2026_07_12.md`](/plans/archive/issues/tradfi_databento_ohlcv_silent_zero_rows_2026_07_12.md)
    (done) — 0 open todos (closed/archived/record-only)
  - [`plans/archive/issues/tradfi_ice_ohlcv_1m_no_working_fetch_path_2026_07_13.md`](/plans/archive/issues/tradfi_ice_ohlcv_1m_no_working_fetch_path_2026_07_13.md)
    (done) — 0 open todos (closed/archived/record-only)
  - [`plans/active/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md`](/plans/active/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md)
    - **[SCRIPT] P2.** Stale `barchart` manifest rows (4,655) — fully-retired source, same orphan class as massive

- **Throughput / jobs / VMs**:
  - [`plans/active/issues/databento_default_executor_dns_starvation_risk_2026_07_17.md`](/plans/active/issues/databento_default_executor_dns_starvation_risk_2026_07_17.md)
    - **[CODE] P1.** Give the Databento chunk pull a dedicated executor (mirror
      `tardis_csv_transport._get_parse_executor`)
    - **[AUDIT] P2.** Sweep the repo for other `run_in_executor(None, ...)` call sites doing network-blocking work
    - **[CODE] P2.** Consider an `aiodns`/`AsyncResolver` for aiohttp sessions
  - [`plans/active/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`](/plans/active/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/active/issues/tradfi_backfill_oom_remediation_2026_06_24.md`](/plans/active/issues/tradfi_backfill_oom_remediation_2026_06_24.md)
    - **[INFRA] P2.** After the next deployment-service image rebuild, drop the runtime `TRADFI_OHLCV_MACHINE` env
      override
    - **[TRADFI] P2.** memray the ~15 GB per-date transient footprint
  - [`plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md`](/plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md)
    - **[REVIEW] P1.** Local verify now; Cloud Build deploy DEFERRED (operator 2026-07-10 — local-dev-only)
    - **[BACKEND] P1.** Per-run output-production verdict endpoint (the seam deployments links to)
    - **[REVIEW] P1.** QG both repos green + LOCAL verify the seam resolves live
  - [`plans/active/issues/tradfi_t1_no_working_mtds_job_2026_07_17.md`](/plans/active/issues/tradfi_t1_no_working_mtds_job_2026_07_17.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/active/issues/group_c_cloud_run_job_failures_triage_2026_07_16.md`](/plans/active/issues/group_c_cloud_run_job_failures_triage_2026_07_16.md)
    - **[INFRA] P1.** Decide + implement a default-to-yesterday date bridge for MTDS's batch CLI

- **Coverage/data-status/honest**:
  - [`plans/archive/issues/honest_coverage_out_of_window_expected_unattempted_not_clipped_2026_07_16.md`](/plans/archive/issues/honest_coverage_out_of_window_expected_unattempted_not_clipped_2026_07_16.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`](/plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md)
    (14 open — capped)
    - **[DESIGN] P1.** Fix the mockup's leaf model everywhere it still needs it (Finding 1) — CEFI/TRADFI/DEFI
      leaf3/proto builders
    - **[DESIGN] P1.** Design the CEFI instrument-definition parquet resharding (Finding 2, decided)
    - **[CODE] P1.** Widen the writer-fix scope to Solana DeFi + CURVE-OPTIMISM (blank `instrument_type` bug)
    - **[CODE] P1.** Pull the real per-instrument_type breakdown for DERIBIT live
    - **[CODE] P1.** Add `missing_dates`/`dates_found_list` to the per-instrument_type and per-underlying breakdown
      entries
    - **[CODE] P1.** Move `market_metadata` off the MTDS `per_venue_per_data_type_daily` axis
    - **[VERIFY] P1.** Raw-parquet spot-check the 5 additional CeFi venues flagged by the pre-audit's registry read
    - **[CODE] P1.** Backfill historical CeFi/TradFi manifest rows with the corrected per-instrument_type split
    - +6 more (P2/P3) — see file for the rest
  - [`plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md`](/plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md)
    - **[CODE] P1.** Add a falsifier test that fails CI when a venue/source key disagrees between `coverage_starts.py`
      and `venue_mapping.py`
    - **[DATA] P1.** Resolve the 8 confirmed multi-year/multi-month CeFi mismatches (BITFINEX, KRAKEN, COINBASE-SPOT,
      etc.)
    - ~~**[DATA] P2.** Resolve the CME mismatch — `coverage_starts.py`'s 2010-01-01 vs `venue_mapping.py`'s 2020-01-01~~
      — **SHIPPED, stale digest entry corrected 2026-07-25 (plan-reconcile)**: `unified-api-contracts@32b2879c` updates
      `coverage_starts.py` to match `venue_mapping.py`'s verified 2020-01-01; this doc's own Phase C todo (line ~280)
      and `coverage_floor_registries_no_cross_propagation_2026_07_17.md:163` are both already flipped `[x]` — this
      digest bullet alone was stale relative to the rest of this same file.
    - **[DATA] P2.** Resolve the POLYMARKET mismatch (CLOB-launch vs first-actual-instrument)
    - **[DATA] P3.** Resolve the small 1-21 day DeFi protocol drifts + AAVE_V3 chain-axis question
    - **[DATA] P3.** Publish an explicit key-mapping table between `coverage_starts.py` and `venue_mapping.py` keys
  - [`plans/active/data_status_page_ux_and_canonicalisation_2026_07_16.md`](/plans/active/data_status_page_ux_and_canonicalisation_2026_07_16.md)
    - **[DATA] P3.** DECIDED (operator 2026-07-18) — `InstrumentRecord` silently swallows unknown kwargs,
      `extra='forbid'` fix
  - [`plans/archive/issues/deployment_api_legacy_instrument_availability_venue_lookup_gap_2026_07_13.md`](/plans/archive/issues/deployment_api_legacy_instrument_availability_venue_lookup_gap_2026_07_13.md)
    — 0 open todos (closed/archived/record-only)

- **ML/backtest readiness (downstream, orthogonal)**:
  - [`plans/active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`](/plans/active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md)
    (9 open — capped)
    - **[AGENT] P0.** BLOCKED-OPERATOR-DECISION — Run MDPS `--operation build-continuous --root ES` after process VM
      completes
    - **[AGENT] P0.** BLOCKED-OPERATOR-DECISION — Run `features-delta-one-service` for tradfi/ES across its calculators
    - **[AGENT] P0.** Run `features-volatility-service` for tradfi/ES + tradfi/CBOE-VIX (realized-vol + skew)
    - +6 more (P2/P3) — see file for the rest
  - [`plans/archive/issues/features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md`](/plans/archive/issues/features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md)
    — 0 open todos (closed/archived/record-only)

- **Skills**:
  [`plans/archive/2026_07/data_pipeline_e2e_check_2026_07_10.md`](/plans/archive/2026_07/data_pipeline_e2e_check_2026_07_10.md)
  — 0 open todos (closed/archived/record-only; superseded by the `data-pipeline-check-mtds`/`data-pipeline-check-is`
  skills, no bare `.md` todo tracker to check).

- **TradFi-specific residuals**:
  - [`plans/active/issues/cme_combo_underlying_extraction_garbage_2026_07_19.md`](/plans/active/issues/cme_combo_underlying_extraction_garbage_2026_07_19.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/active/issues/instruments_service_fx_adapter_key_unresolved_2026_07_23.md`](/plans/active/issues/instruments_service_fx_adapter_key_unresolved_2026_07_23.md)
    (`status: resolved`) — 0 open todos (closed/archived/record-only)
  - [`plans/active/issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md`](/plans/active/issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md)
    - **[INVESTIGATE] P1.** Root-cause the actual `WithinBoundsTradfiSourceZero` trigger for the live, active
      `ohlcv_1s`/`ohlcv_1m` population
    - **[DATA] P2.** Purge or reclassify the 1,242 dead CBOE `ohlcv_15m` rows (frozen since 2026-07-07)
    - **[DESIGN] P2.** Give `check_high_attempted_failed` a way to mark a cell "known-dead, expected-coverage-narrowed"
  - [`plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`](/plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md)
    - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — legacy-twin bucket DELETES (defi/tradfi/pred), Ikenna's migration
      sign-off gates this
  - [`plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`](/plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md)
    (15 open — capped)
    - **[DATA] P0.** ES CME futures ohlcv 1s+1m — IN FLIGHT (`tradfi-bf-cme-ohlcv-1m-es-{2020,2025,2026}` RUNNING)
    - **[DATA] P0.** ES CME OPTIONS (ES_OPT) ohlcv 1s+1m — NOT yet launched (singleton Databento lock held by futures
      fleet)
    - **[INFRA] P1.** tradfi — same gates; Databento universe (GLBX/DBEQ/XCBF) + Yahoo (KRX/FX)
    - **[DATA] P1.** FINDING — IS `by_date` capture frozen ~2026-05-21 fleet-wide; tradfi degraded from ~2026-05-04
    - **[DATA] P1.** FINDING — ICE futures + CME futures-options not on Massive → BLOCKED-CREDENTIALS
    - **[DATA] P1.** tradfi CME futures reference gap from 2026-06-08 — Massive `/futures/vX/{products,contracts}` 404
    - **[IS] P1.** Backfill the IS CME (GLBX.MDP3) catalog for 2019-01-01→present
    - **[SCRIPT] P1.** (→ M-1) MTDS tradfi market-data backfill across all 3 datasets (GLBX.MDP3 + DBEQ.BASIC + CFE)
    - **[SCRIPT] P1.** instruments-service — post tradfi-v9 close-out, tombstone dropped Databento instruments
    - **[UAC] P1.** Unit tests for `databento_subscription_allowlist`
    - **[PM] P1.** QG grep-ratchet — no raw `batch.submit_job` outside the guarded `submit_batch_job`
    - +4 more (P2/P3) — see file for the rest

- **Cross-cutting infra / audit (shared across asset groups, tradfi-relevant)**:
  - [`plans/active/candle_canonical_path_migration_execution_2026_07_24.md`](/plans/active/candle_canonical_path_migration_execution_2026_07_24.md)
    (16 open — nearly all P0, listed in full per the "never silently drop a P0/P1" rule)
    - **[DATA] P0.** Rebuild code tarballs (`refresh_code_tarballs.sh`) for the 4 already-shipped repos
    - **[DATA] P0.** VERIFY on `-test-` via `/data-pipeline-check-mdps` (force+skip+canonical legs) that the writer now
      emits canonically
    - **[DATA] P0.** VERIFY readers dual-read correctly (features-service delta_one + volatility, unified-trading-api)
    - **[SCRIPT] P0.** Run the sanctioned Tier-2 spot-VM single-walk census
    - **[SCRIPT] P0.** Build the migration executor (P5)
    - **[SCRIPT] P0.** Implement the path transform in the executor (backward-add `instrument_type=`)
    - **[SCRIPT] P0.** Implement DEDUP in the executor for the split-brain candle layout
    - **[SCRIPT] P0.** Implement PURGE of empty-stem objects
    - **[SCRIPT] P0.** Implement QUARANTINE (never guess) for unresolvable legacy TradFi leaf ids
    - **[SCRIPT] P0.** Wire manifest re-record to the SOURCE-keyed row (via `record_captured`, path-independent)
    - **[SCRIPT] P0.** Upgrade the executor's pre-delete verification from SIZE-only to crc32c checksum
    - **[DATA] P0.** Extend `launch-canonical-migration-vm.sh` for this migration's per-AG SPOT fleet launch
    - **[DATA] P1.** P6 drain+snapshot: coordinate with the running `canonical-migration-cefi-wp*` raw_tick VMs
    - **[DATA] P0.** P7 per-AG SPOT migration apply, in order defi→prediction→cefi→tradfi (tradfi last)
    - **[DATA] P0.** P8 verify/reconcile: 4-surface reconciliation + extend the UAC canonical-path-violations oracle
    - **[DATA] P1.** Root-cause + close the candle object↔manifest disconnect (6 degenerate MDPS manifest rows vs 20k+
      objects)
  - [`plans/active/data_pipeline_check_mdps_features_2026_07_20.md`](/plans/active/data_pipeline_check_mdps_features_2026_07_20.md)
    (28 open — capped; P0/P1 listed in full, P2/P3 capped)
    - **[DATA] P0.** RUN + VALIDATE `/data-pipeline-check-mdps` e2e: auto-select high-coverage day per AG, prove
      force+skip for every MVP candle shard
    - **[DATA] P0.** RUN + VALIDATE `/data-pipeline-check-features` e2e: multi-day input window per family, prove
      force+skip
    - **[DATA] P0.** Cross-repo orphan/lineage audit (MTDS→MDPS→features→ml/strategy) + MIGRATE existing candle/feature
      data to zero orphans
    - **[DATA] P0.** Produce concrete ETA to backfill all remaining DeFi MVP
    - **[DATA] P0.** Verify whether MDPS `max_workers` (8 on e2-standard-8) actually OVERLAPS the GCS writes
    - **[DATA] P0.** Enumerate the candle-coverage GAP per (asset_group, venue, data_type, timeframe)
    - **[DATA] P0.** Run `/data-pipeline-check-mdps` across all relevant AGs NOT already in candles
    - **[DATA] P0.** Run `/data-pipeline-check-features` across ALL shards (8 families x valid AGs)
    - **[DATA] P0.** VERIFY the prod projection on a real prod-bucket MDPS run before sizing the win (biggest unknown in
      the ETA)
    - **[SCRIPT] P0.** Implement F1+F2 (UTL `manifest_completeness.py`) + F3 (MDPS `_publish_emission_check`)
    - **[DATA] P0.** Audit every `read_availability_index` caller on defi for a missing column/filter projection (1.58
      GB index OOM risk)
    - **[SCRIPT] P0.** Fix the shared seed context (per-call immutable value object + collision-proof frame-cache key)
    - **[SCRIPT] P0.** Implement R1 (concurrent date-subprocesses) — the months->weeks lever that is SAFE today
    - **[DATA] P0.** Real-VM re-measure of end-to-end per-instrument-day rate against a PROD-sized index
    - **[DATA] P1.** Steady-state benchmark VMs (250GB disk) per representative shard-type
    - **[SCRIPT] P1.** Backfill-processing path (download→process→upload) code-ready + OPTIMIZED learning from cefi
    - **[DATA] P1.** Full DeFi-MVP candle backfill on real infra — GATED on
      `candle_canonical_path_migration_execution_2026_07_24.md` P8
    - **[SCRIPT] P1.** Add the all-NaN-parquet-vs-`captured` assertion to `/data-pipeline-check-mdps`
    - **[DOC] P1.** Correct `/codex/05-infrastructure/spot-vms-for-backfill.md`: preemption signal now installed via
      systemd unit
    - **[SCRIPT] P1.** Close residual risk 1 — make arg-required launchers relaunchable (features especially)
    - **[DATA] P1.** Blast radius: did any PAST prod MDPS run use `max_workers>1` over a heterogeneous list
    - **[SCRIPT] P1.** Implement R1: bounded-concurrent `_run_date_as_subprocess` dispatch (gated on the seed-context
      fix)
    - +6 more (P2/P3) — see file for the rest
  - [`plans/active/mdps_features_reduced_artifact_tracker_2026_06_28.md`](/plans/active/mdps_features_reduced_artifact_tracker_2026_06_28.md)
    (`status: draft`) — 0 open todos (closed/archived/record-only; not yet flipped `active`)
  - [`plans/active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`](/plans/active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md)
    - **[VERIFY] P1.** Check whether manifest regeneration is automatic or requires an explicit re-enumeration trigger
    - **[VERIFY] P2.** Spot-check 2-3 more findings from the smoke-test doc across all 3 layers
    - **[DECISION] P2.** Once the pilot trace (AAVE_V3) lands, decide the reconciliation cadence for the remaining 58
      findings
  - [`plans/active/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md`](/plans/active/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md)
    - **[DATA] P1.** instruments-service: canonicalise the `instrument_availability` write via the sink PREFIX mechanism
    - **[DATA] P1.** market-tick-data-service: rule on and fix the cefi chain tail (`partitioned_writer.py:291-293`)
    - **[DOCS] P2.** instruments-service + market-tick-data-service: correct three in-repo comments asserting hive
      layout
    - **[SCRIPT] P2.** unified-trading-pm: add a Phase-0 `-test-` assertion on the resolved WRITE bucket
    - **[DOCS] P2.** unified-trading-pm: add an explicit "never pass `--allow-live-prod-writes`" prohibition to the
      skill doc
    - **[DATA] P3.** instruments-service: decide whether `market_lifecycle`/`futures_contracts` are in the canonical
      shard grammar's scope
  - [`plans/active/issues/canonical_closeout_open_questions_2026_07_18.md`](/plans/active/issues/canonical_closeout_open_questions_2026_07_18.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md`](/plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md)
    - **[DATA] P1.** Re-run CeFi surface-A reconciliation with the fixed oracle and restate the verdict
    - **[DATA] P2.** The legitimately-unresolvable objects need a quarantine/honest-absence disposition (separate
      design)
  - [`plans/active/issues/estate_orphan_assessment_2026_07_21.md`](/plans/active/issues/estate_orphan_assessment_2026_07_21.md)
    - **[INFRA] P1.** Run the orphan sweep for defi/cefi/tradfi/prediction on a VM
    - **[CODE] P2.** Make the manifest load resumable/streamed in `migration_orphan_sweep.py`
    - **[CODE] P2.** Give `backfill_orphan_class_e.py --apply` a batched-incremental `record_cells()` call
    - **[CODE] P3.** `GcsEventSink` never `.shutdown()`s its background `ThreadPoolExecutor`
  - [`plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md`](/plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/active/issues/manifest_completeness_full_corpus_map_build_2026_07_20.md`](/plans/active/issues/manifest_completeness_full_corpus_map_build_2026_07_20.md)
    - **[DATA] P0.** VERIFY the prod projection before sizing the win (is `_publish_emission_check` firing on prod MDPS
      backfills)
    - **[DATA] P0.** The 1.58 GB defi-prd index is its own P0 — audit every `read_availability_index` caller for OOM
      risk
    - **[DOC] P2.** Record in codex that the per-VM manifest flush is ALREADY debounced (50 entries/5.0s)
  - [`plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md`](/plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md)
    - **[SCRIPT] P1.** S1-c — `mdps-sports-<year>-<ts>` emitted but registered in NEITHER registry → invisible to zombie
      watchdog
    - **[SCRIPT] P2.** S1-a — `launch-prediction-features-vm.sh` BROKEN (packages removed, import-verify
      ModuleNotFounds)
    - **[SCRIPT] P2.** S1-b — `launch-mdps-features-live.sh` non-runnable but registered in `vm_prefix_registry.py`
    - **[SCRIPT] P3.** S2-a — trim `launch-features-backfill-vm.sh` to the redirect stub (dead body)
    - **[SCRIPT] P3.** S2-b — delete the 8 stale `features_*_service` keys in `setup-data-pipeline-vm.sh`
      SERVICE_TARBALLS
    - **[SCRIPT] P3.** S3-a — delete MDPS one-offs past `Delete-when` after verifying each condition
    - **[SCRIPT] P3.** S3-c — repoint `features-service/scripts/sports/smoke_matrix.py` SSOT citations
    - **[SCRIPT] P3.** S3-b — sports dual entrypoint operator/design adjudication (fold submodule behind family flag OR
      bless it)
  - [`plans/active/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md`](/plans/active/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md)
    - **[DATA] P1.** Assess blast radius on EXISTING candle data — any past MDPS run with `max_workers>1` over a
      heterogeneous file list
  - [`plans/active/issues/phantom_audit_estate_coverage_gap_2026_07_10.md`](/plans/active/issues/phantom_audit_estate_coverage_gap_2026_07_10.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/active/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md`](/plans/active/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/active/issues/tarball_rotation_breaks_vm_recovery_2026_07_20.md`](/plans/active/issues/tarball_rotation_breaks_vm_recovery_2026_07_20.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/active/issues/ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md`](/plans/active/issues/ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/active/issues/vm_backfill_data_correctness_findings_2026_06_29.md`](/plans/active/issues/vm_backfill_data_correctness_findings_2026_06_29.md)
    — 0 open todos (closed/archived/record-only)

- **Newly discovered (2026-07-24 completeness sweep — `grep -l '^asset_group:.*tradfi'` hits not previously named in
  this section; several were already mentioned inline in the Phase A2 prose above but never carried a real entry
  here)**:
  - [`plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md`](/plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md)
    - **[DATA] P1.** PROVE the fixed writers green on one real day, then migrate the historical flat objects UP into
      full hive
    - **[REVIEW] P1.** On writer ship, record the `instrument_availability` full-hive cutover date in the
      canonical-cutover-register
  - [`plans/active/issues/instruments_remaining_work_audit_2026_07_10.md`](/plans/active/issues/instruments_remaining_work_audit_2026_07_10.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md`](/plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md)
    - **[VERIFY] P1.** NEW (2026-07-14) — FLUID lending_indices silently returns 0 rows for ~18 months of its own
      declared availability window
    - **[VERIFY] P1.** Root-cause the 273 mistagged DERIBIT/COMBO rows (open question #1) — not attempted this session
    - **[CODE] P2.** Update both drilldown mockups — not attempted this session
  - [`plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md`](/plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md)
    — 0 open todos (closed/archived/record-only; design doc superseded by
    `candle_canonical_path_migration_execution_2026_07_24.md`)
  - [`plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`](/plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md)
    — 0 open todos (closed/archived/record-only; the follow-up `tradfi_phase_d_terminal_gate_2026_07_24.md` P0 gates on
    this finding)
  - [`plans/active/issues/tradfi_docs_reconciliation_findings_2026_07_21.md`](/plans/active/issues/tradfi_docs_reconciliation_findings_2026_07_21.md)
    (uses a line-referenced audit-finding format, not `[TAG] P<N>.` — quoted as-is)
    - **P1 (L97).** Ground-truth verdict header needs a supersede banner inserted (superseded by later migration
      progress)
    - **P1 (L460).** Phase B migration items still shown unchecked in a stale copy — flip the four false-negative boxes
    - **P1 (L237).** §4 closing paragraph needs rewriting to match the current migration state
  - [`plans/active/issues/tradfi_manifest_rebuild_deletion_resurrection_gap_2026_07_20.md`](/plans/active/issues/tradfi_manifest_rebuild_deletion_resurrection_gap_2026_07_20.md)
    - **[BACKEND] P1.** Add a manifest-vs-disk consistency check so a `captured` row with no object on disk fails loudly
  - [`plans/active/issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md`](/plans/active/issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/active/issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md`](/plans/active/issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md)
    - **[DECISION] P2.** Decide whether `mvp_mode` should ever be wired live
    - **[SCRIPT] P2.** Implement the chosen direction (wire a real caller, or remove the dead path cleanly)
    - **[SCRIPT] P2.** Ship via quickmerge, quality-gates green in both market-tick-data-service and
      unified-api-contracts
  - [`plans/active/issues/tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md`](/plans/active/issues/tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md)
    - **[DATA] P1.** Re-measure and break down the 182,407 by (venue, data_type, year)
    - **[BACKEND] P1.** Teach the sentinel/enumerator path the discovery floor
    - **[DATA] P1.** Run the corrective reclassification over the existing 182,407 cells, writer-side
    - **[BACKEND] P2.** Assert the invariant in the aggregator's fairness checks
    - **[DATA] P2.** Sweep the other tradfi venues for the same class (CBOE 2020-06-01, CME 2020-01-01)
  - [`plans/active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md`](/plans/active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md)
    - **[CODE] P2.** Fix `_L5_VENUES` (finding 4) — RESOLVED-BY-DELETION 2026-07-18 per in-doc note, checkbox not yet
      flipped
    - **[CODE] P2.** Add the missing `book_snapshot`/`market_metadata`/`fills` declarations to
      `VENUE_DATA_TYPE_CAPABILITIES`
    - **[DESIGN] P2.** New finding, 2026-07-10 — 31 DeFi (venue, data_type) pairs declare a genesis start-date in Layer
      2
    - **[SCRIPT] P3.** Delete confirmed-dead code: `MVP_VENUE_DATA_TYPES`, DeFi's emptied `DEFI_VENUE_AXIS_OVERRIDES`
  - [`plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md`](/plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md)
    (already in this plan's `related:` frontmatter; not previously given a digest entry here)
    - **[DATA] P0.** Root-cause the object↔manifest disconnect (20,734 cefi candle objects on 2026-04-14 vs 6 MDPS
      manifest rows)
    - **[DATA] P1.** Corpus-wide count of zero-length-stem candle objects; purge or repair
    - **[DATA] P1.** Canonicalise TradFi candle leaf ids (`E1AF0_C3200_migrated_*` → `VENUE:TYPE:SYMBOL`) — 84.8% of the
      corpus needs this
    - **[DATA] P1.** Split-brain candle layout (addendum iii-a) — quantify the corpus-wide split, fold into the A/B/C
      migration
    - **[SCRIPT] P2.** Fix `_copy_verify_delete()`'s retry-idempotency gap
    - **[DATA] P3.** `ProvisionalTargetIndex` keys lack a bucket component (cosmetic, fix before trusting the split
      count)
    - **[DOC] P3.** `build_canonical_candle_path()` docstring example still shows superseded semantics
    - **[SCRIPT] P3.** Investigate why `CEFI:DERIBIT:trades:24h`'s force-leg classification shows `off_template=29`

## Progress Log — condensed milestone summary (2026-07-24, replaces the pre-split ~1700-line tick-by-tick log)

> **The full tick-by-tick history was NOT deleted** — it was split verbatim across the 3 children by workstream (see the
> Split notice above). This section is a short, condensed orientation only; for exact commands, shas, measured numbers,
> and the full narrative, read the relevant child's own Progress Log.

- **2026-07-18 — Plan authored + ground-truth-corrected.** First-draft "largely done" claim disproved by direct live GCS
  reads: catalogue + manifest derivative ids measured at 0% canonical. Rewritten into the Phase A→B→C→D structure above.
  → full detail: `tradfi_manifest_content_recovery_completion_2026_07_24.md`.
- **2026-07-18 — Phase A1 writer convergence shipped** (UAC shared builder + MTDS/IS writers all emit `-USD@LIN`).
  **Phase B — manifest (Surface B) migration executed + RE-VERIFIED LIVE 2026-07-25**: migrated via
  pause-consolidator→CAS-rewrite→resume; fresh live read confirms FUTURE/OPTION `instrument_id` canonical
  363,954/403,467 (90.2%), EQUITY/ETF carrying `-USD` 3,189,939/3,225,484 (98.9%), durability independently re-verified.
  **Catalogue (Surface A) migration is NOT YET executed** — still an open P0 (DURABILITY TRAP: a `prod/n`-only rewrite
  silently reverts on the next catalogue rebuild); the 99.86% figure in the child doc is the PRE-migration
  canonicalizability measurement on the raw catalogue, not a completed-migration result. →
  `tradfi_manifest_content_recovery_completion_2026_07_24.md`.
- **2026-07-18 — A3.1 Databento e2e throughput optimization shipped + measured 1.56x** (gated concurrent-date driver,
  disk-policy fix, concurrency plumbing); a P0 fleet incident (88 launchers with a truncated `gcloud` command from an
  unrelated disk-policy sweep) found and fixed mid-measurement. → `tradfi_backfill_throughput_followups_2026_07_24.md`.
- **2026-07-19 — First Phase-D pass: 36/60 red, dominated by checker bugs, not real MVP-path failures** (billing-gated
  Databento datasets misclassified as failed; `--mvp-only` not suppressing non-MVP augmentation) — both fixed. CME
  `ohlcv_1m` root-caused to a genuine shard-atom design ambiguity (chain-bundle vs per-contract), flagged
  BLOCKED-OPERATOR-DECISION. Re-run: clean MVP verdict, 2/15 hard-fail (both CME, pending the ruling). →
  `tradfi_phase_d_terminal_gate_2026_07_24.md`.
- **2026-07-20 — Operator 6h-away mandate: complete everything autonomously.** Canonical GCS-PATH migration executed on
  20 SPOT VM shards (2.65M objects classified, 0 orphans, 2 defects found+fixed mid-run); CME shard-atom ruled Option A
  (chain bundle — fix the checker, not the writer); Massive purge initially HELD (the `trades`/`tbbo` corpus was the
  only copy, billing-gated), then operator-AUTHORIZED under accepted-permanent-loss (Option C — "our subscription is
  terminated, ohlcv_1m is more than enough"), then EXECUTED (1,701,422 objects purged, 0 collateral, soft-delete safety
  net held throughout). Post-migration audit confirmed complete (a 14-object residue found+fixed); manifest surgical
  cleanup dropped 686,005 stale massive rows + 3,615 disk-verified phantom rows. →
  `tradfi_manifest_content_recovery_completion_2026_07_24.md`.
- **2026-07-21 — MVP scope expanded +409 cells** (VIX futures, CBOE treasury-yield INDEX, FX KRW, CME crypto
  futures-only); backfill fleet launched at scale. Reconciliation run found the earlier "~99.65% canonical" claim was
  OVERSTATED — historical manifest/parquet-content id-form was actually only 30.8% canonical (0% pre-2023) — and an
  ACTIVE LIVE REGRESSION was caught: the currently-running backfill fleet wrote canonical GCS filenames but
  non-canonical manifest rows for the same capture (~850K bad rows/day). Writer bug root-caused + fixed same day. →
  `tradfi_manifest_content_recovery_completion_2026_07_24.md` (writer/manifest fix) +
  `tradfi_backfill_throughput_followups_2026_07_24.md` (backfill-drive fleet launch).
- **2026-07-21/22 — Cash-bucket crash bug fixed properly** (a per-row exception-isolation gap that had silently
  truncated the 2026-07-18 migration run); content-rewrite script shipped; manifest CAS re-stamp executed on VMs
  (6,262,988 rows rewritten in place: 1,751,779 cash rows migrated to `-USD`, combos re-stamped, derivative mislabels
  corrected). All remaining migration work deliberately moved onto VM compute (operator directive, session
  time/credit-constrained). → `tradfi_manifest_content_recovery_completion_2026_07_24.md`.
- **2026-07-22 — Honest-coverage audit run for real**; KRX equities gap found + closed (new Yahoo-daily launcher, no
  prior launcher had ever targeted this venue); chain-manifest recovery script built + shipped (register phase applied
  live: 1,545 rows registered for real captured-but-unregistered data; retire phase — 50,520 candidate rows —
  deliberately left `--apply`-gated pending operator review, NOT auto-applied); CME MBO monolith investigation found
  only 30 objects (not the previously-cited 107 — discrepancy investigated but not fully explained; migration tool
  design deferred as its own follow-up). → `tradfi_manifest_content_recovery_completion_2026_07_24.md`.
- **2026-07-23 — Phase D re-run found + fixed 3 real, independently-verified checker bugs**: (1) MTDS freshness
  pre-flight read the wrong (permanently-stale `-test-` tier) bucket under `--test-run`; (2) the skip-leg vacuously
  failed on an honest-empty force leg instead of recognizing there was nothing to prove a skip against; (3) IS's
  expected-write-prefix builder went stale after an unrelated 2026-07-21 hive-path canonicalisation change. IS check
  improved 0/14 → 11/14 passed (remaining 3 explained: 1 SPOT-preemption noise, 2 genuine honest-absence). Full MTDS
  all-shards run: 21 passed / 21 failed / 18 skipped — failures mostly SPOT preemption noise (measured via
  `gcloud compute operations list`, not assumed) plus 2 known pre-existing gaps and one newly-surfaced chain-bundle
  sampler root-mismatch, filed as its own follow-up issue rather than chased further in-session. →
  `tradfi_phase_d_terminal_gate_2026_07_24.md`.

**State as of the 2026-07-24 fork**: manifest/content migration is substantially complete on the primary surfaces with
one 50,520-row retire-phase batch awaiting explicit operator sign-off before `--apply` (Child 1); backfill throughput is
measured + optimized (1.56x shipped) with further ETA/concurrency-cap tuning identified but not yet applied (Child 2);
the Phase-D terminal gate has found and fixed 3 real cross-cutting checker bugs, but is **not yet fully green** — the
MVP backfill readiness gate stays blocked pending the chain-bundle sampler follow-up or an explicit operator acceptance
of the current evidence as sufficient (Child 3).
