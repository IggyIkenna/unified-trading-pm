---
doc_type: plan
title: TradFi consolidated close-out — one-pass code→migrations→coverage→smoke-test to MVP-backfill-ready
summary:
  Coordination index (umbrella) that AGGREGATES (references, does not duplicate) every open tradfi + tradfi-touching
  IS/MTDS plan/issue into ONE ordered pass, mirroring cefi_consolidated_closeout_2026_07_18.md. **2026-07-24 line-cap
  remediation** trimmed the doc from 2549 lines to an umbrella-eligible coordination index — the manifest/content
  id-canonicalisation completion work (Phase A1 residual + Phase B/B.5), the download/backfill throughput follow-ups
  (Phase A3/A3.1), and the Phase-D terminal gate were forked verbatim to 3 sibling plans (see `related:` below).
  **2026-07-25 second-tier trim** (the doc had grown back to 927 lines) forked Phase A2 (adapter/registry correctness)
  and the STILL-OPEN residue of Phase C (data-status/honest-coverage) to a 4th child,
  `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`; the 2 fully-closed Phase C mega-verdicts (honest-coverage
  re-verification, KRX name-column shipment) that used to sit inline plus the full condensed Progress Log moved to
  `tradfi_consolidated_closeout_history_2026_07_25.md` (pure record). This parent now retains the ground-truth context,
  MVP universe, the Codex SSOT index, and the aggregated reference index (untouched, 421 lines) — see the 4 children for
  all open work and the history companion for closed narrative. GROUND-TRUTH CORRECTION (measured live 2026-07-18,
  superseding this plan's own first-draft "largely done" verdict) — the persisted tradfi manifest and catalogue are ~100
  percent NON-canonical for derivatives at the plan's outset; see the children for how much of that has since been
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
    /plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md,
    /plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25_finalize.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
    /plans/active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md,
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
  ]
created: 2026-07-18
last_updated: "2026-08-09"
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
effort: xhigh
context_scope:
  [
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-coverage-model.md,
    /plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md,
    /plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md,
    /plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md,
  ]
drift_direction: none
archive_exempt: true
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
  [
    tradfi_manifest_content_recovery_completion_2026_07_24,
    tradfi_backfill_throughput_followups_2026_07_24,
    tradfi_phase_d_terminal_gate_2026_07_24,
  ]
# 2026-08-01 (ag-closeout-audit, tradfi tranche): added the 3rd forked child (tradfi_phase_d_terminal_gate_2026_07_24)
# to depends_on -- it was named in the Split notice table above from day one but never actually listed here, which
# left generate_ag_closeout_audit_candidates.py's covering-plan discovery blind to it (that script only resolves
# depends_on for *_finalize* docs, so a closeout's own depends_on needs to be complete for docs with no finalize pair).
# gate_on_depends removed 2026-07-25 (second-tier trim, fix #6): the 2 items it protected -- Phase C's
# honest-coverage-gated-on-Phase-B residue, and the BLOCKED-INFRA Layer-1-cert item -- both forked to
# tradfi_registry_coverage_and_ao_readiness_2026_07_25.md, which now carries the real depends_on+gate_on_depends:true.
# This parent's one remaining native todo (MVP wiring backfill=paper=live verify) isn't gated on either upstream plan,
# so depends_on here is retained as documentation/history only (also still gates this plan's own archival per
# PLAN_FORMAT.md, independent of gate_on_depends).
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
  frontmatter key that carried this was later stripped 2026-07-24, ruled inert workspace-wide). **On 2026-07-25** a
  second-tier trim (the doc had grown back to 927 lines) forked Phase A2 + the still-open Phase C residue to a 4th child
  (`tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`) and extracted the 2 fully-closed Phase C mega-verdicts +
  the full condensed Progress Log to a history companion (`tradfi_consolidated_closeout_history_2026_07_25.md`) — see
  this doc's own "Phase A2 + Phase C — forked 2026-07-25" section for the pointer.
---

# TradFi consolidated close-out — one pass to MVP-backfill-ready

> **Purpose.** Coordination index (umbrella) that aggregates every open tradfi + tradfi-touching IS/MTDS plan/issue into
> a single ordered pass. This plan **references** the source docs; it does not duplicate them. Close a track by closing
> its source doc(s), then tick it here. Mirrors `cefi_consolidated_closeout_2026_07_18.md`; ordered per the operator's
> directive: **Phase A code → Phase B migrations → Phase C data-status/honest-coverage → Phase D re-smoke-test →
> MVP-backfill-ready.**

## Split notice (2026-07-24 — plan-hygiene line-cap remediation)

> **This plan was trimmed from 2549 lines and forked 3 ways**, per the operator-approved split in
> `/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md` (row 29). The 3-way split was overwhelmingly driven by
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
> **Per-child open-todo digest — RE-DERIVED LIVE 2026-07-31 (slot 14, AO-dispatch-readiness sweep)**: the prior digest
> text (2026-07-24/25 vintage) was stale relative to each child's own current checkboxes; live `grep -c '^- \[ \]'`
> counts substituted below, replacing the earlier "8 open" / "6 open" figures rather than layering another banner on top
> of them.
>
> **STALE AGAIN 2026-08-18 (plan_reconciler) — the 2026-07-31 counts below have drifted further, live-recounted this
> pass** (`grep -c '^- \[ \]'`, this pass): `tradfi_manifest_content_recovery_completion_2026_07_24.md` is now **1
> open** (not 3) — only the "decision on the 1,328-cell unrecoverable population" item remains; the qualifier-
> normalization fix and the `candle_feature_canonical_path_divergence` verify-and-close pointer are both now `[x]`.
> `tradfi_phase_d_terminal_gate_2026_07_24.md` is now **1 open** (not 2), and it's a DIFFERENT item than either one
> named below — both the P0 MVP-gate and P1 reconciliation items are now `[x]`; the sole remaining open item is a
> `[SCRIPT] P3` (add `TestIsBundledChainShardCboeCorrection` tests, line ~514). `tradfi_backfill_throughput_
> followups_2026_07_24.md`'s "1 open" figure below is still accurate, re-confirmed. Not re-deriving the full bullet
> text below in place (this doc is dense enough that a surgical rewrite risks a worse mismatch than this note) —
> treat the specific counts/item-lists in the 3 bullets immediately below as informational history, not current
> state; the 3 figures in this correction are the current ones.
>
> - `tradfi_manifest_content_recovery_completion_2026_07_24.md` — **3 open (live 2026-07-31)**, down from the 2026-07-24
>   vintage's 8. The 2 P0s that digest named (catalogue Surface A migration, GCS-filename/tick-content Surfaces C+D
>   migration) are BOTH now done — catalogue SHIPPED+APPLIED LIVE 2026-07-25 (`instruments-service@52d8b3ef`),
>   chain-bundle content GATE CLOSED 2026-07-27 (checked=961 canonical=961 violations=0). What remains open now is
>   different work entirely: (1) a 2026-07-28-ruled qualifier-normalization fix, (2) a 2026-07-28-ruled decision on the
>   1,328-cell unrecoverable population, (3) a verify-and-close pointer to
>   `candle_feature_canonical_path_divergence_2026_07_20.md` todo 3.
> - `tradfi_backfill_throughput_followups_2026_07_24.md` — **1 open (live 2026-07-31)**, down from the 2026-07-25
>   digest's 6 (both named P1s — the OOM/monitor bundle and the T+1 forward-fill job — the T+1 job has since shipped;
>   `tradfi_t1_no_working_mtds_job_2026_07_17.md` is archived `status: resolved` per this same doc's own Aggregated
>   source docs section below). The one remaining open item is the Backfill-VM startup OOM rc137 + OOM-remediation +
>   consolidator throughput/backlog-monitor bundle.
> - `tradfi_phase_d_terminal_gate_2026_07_24.md` — **2 open (live 2026-07-31, unchanged from the 2026-07-24 digest)**:
>   re-verified accurate, no correction needed. The P0: MVP backfill readiness gate — run the tradfi MVP backfills only
>   after A-D are green; **still blocked** on the chain-bundle sampler follow-up. The P1: post-full-backfill
>   `/data-pipeline-reconciliation` RUN checkpoint, gated on the P0.
>
> **Retained here (as of 2026-07-24)**: the ground-truth verdict + MVP universe (foundational context for all children),
> Phase A2 (adapter/registry correctness), Phase C (data-status + honest-coverage), the aggregated Codex SSOT +
> source-doc index, and a condensed milestone summary replacing the full tick-by-tick Progress Log. **Updated
> 2026-07-25**: Phase A2 and the still-open residue of Phase C were forked to a 4th child
> (`tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`) and the condensed milestone summary moved to a history
> companion (`tradfi_consolidated_closeout_history_2026_07_25.md`) — see the "Phase A2 + Phase C — forked 2026-07-25"
> section and the Progress Log section below for the current pointers. What's still genuinely retained here now: the
> ground-truth verdict + MVP universe, and the aggregated Codex SSOT + source-doc index.

## Ground-truth verdict (measured live 2026-07-18 — supersedes the first-draft "largely done" claim)

> **SUPERSEDED 2026-07-27 — this 2026-07-18 baseline verdict is historical.** The canonicalisation described below as
> "barely started / 0%" is now COMPLETE and VERIFIED: catalogue (Surface A) SHIPPED+APPLIED LIVE 2026-07-25
> (instruments-service@52d8b3ef) — `prod/n` 775,116/776,387 canonical (99.84%), per-day corpus 68,133,635/68,406,251
> canonical (99.60%); manifest (Surface B) RE-VERIFIED LIVE 2026-07-25 — FUTURE/OPTION `instrument_id` 90.2% canonical,
> EQUITY/ETF 98.9%; chain-bundle content (Surfaces C+D) GATE CLOSED 2026-07-27 (slot-9) —
> `assert_tradfi_derivative_ids_canonical` checked=961 canonical=961 violations=0. Data-loss forensics CLOSED: 95 real
> victims (restored); 385,341 "twins" were benign rename-to-live. Residual non-canonical is by-design quarantine (ICE
> qualifier variants, `BLOCKED-OPERATOR-DECISION`, non-MVP) + writer-path re-drift, tracked separately — see
> `tradfi_manifest_content_recovery_completion_2026_07_24.md`. The table below is retained only as the 2026-07-18
> pre-migration baseline.

The operator was right: tradfi is overwhelmingly raw **(as of the 2026-07-18 baseline below — see the supersede note
above for current state)**. Direct reads of the live prod buckets, NOT the migration docs' claims:

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

> **🟡 2026-08-09 scope:** `/plans/archive/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`.

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
> For **Databento** tradfi, the billing entitlement is **1-month L2 + 1-year L1** (`mbp-10`→L2, not L3; `mbo` is the
> real L3 schema — corrected 2026-08-19, plan_reconciler; see `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`'s
> 2026-08-18 correction, independently re-verified against `unified-api-contracts/unified_api_contracts/registry/databento_subscription_allowlist.py`)
> — so `mbp_10`/`trades`/`tbbo` are
> **billing-gated by design (documented, NOT a bug to fix)**. The MVP backfill data_type for the instruments we care
> about is **`ohlcv_1m` only** (it has FULL history). The venue capability _declaration_ MAY still enumerate what's
> _possible_ (mbp_10/trades/tbbo within their limits), but the actual **MVP backfills = 1m candles**. For **daily**
> cells we use **Yahoo Finance** as the source (still gives **24h / 1d**): daily Treasuries `ohlcv_24h` + daily **KRW**
> FX. So Phase D smoke-tests + Phase-D MVP backfills iterate: Databento intraday shards → `ohlcv_1m`; Yahoo daily shards
> → `ohlcv_24h`/`ohlcv_1d`. This DE-SCOPES the A2 "mbp_10/trades/tbbo restoration" item to "declaration reflects the
> documented billing reality" (verify, don't chase L3 full history).

### MVP cells — proven wired (backfill=paper=live) vs. declared in-scope only

| MVP cell                                      | Declared in-scope                | Backfill proven (re-verified 2026-08-04 — `plans/audit/results/tradfi_mvp_cell_wiring_and_pipeline_verification_2026_08_04.md`, `unified-trading-pm@cc9e1d144`)                                                                                                                                                                                                                                    | Paper/live wiring proven          |
| --------------------------------------------- | -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| S&P index futures (ES)                        | yes                              | ✅ IS availability-index: data present. MTDS availability-index: data present. Fleet finished (all 7 `es-{2020..2026}` shards self-deleted by 2026-07-21T09:48Z, zero preemptions). Manifest-verify still owed (`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` `[DATA] P0`).                                                                                                              | NOT PROVEN — TradFi is batch-only |
| S&P index options                             | yes                              | ✅ IS availability-index: data present. MTDS availability-index (corrected manifest count-check, 2026-08-09 — `plans/archive/issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md` third finding): 2020-2024 ~94.8-100% covered, 2025 confirmed 0% gap, 2026 73% partial. Manifest-verify still tracked in `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`. | NOT PROVEN — TradFi is batch-only |
| Delta-one single-stock equities               | yes                              | ✅ IS availability-index: data present. MTDS availability-index: data present. Filenames already canonical; id-column verification tracked in `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`.                                                                                                                                                                                           | NOT PROVEN — TradFi is batch-only |
| CME BTC/ETH/MBT/MET futures                   | yes (+409 expansion, 2026-07-21) | ✅ IS availability-index: data present. MTDS availability-index: data present. Backfill fleet launched at scale (2026-07-21 Progress Log); completion not independently re-confirmed this pass.                                                                                                                                                                                                    | NOT PROVEN — TradFi is batch-only |
| Daily Treasuries + daily KRW (Yahoo)          | yes                              | ✅ IS availability-index: data present. MTDS availability-index: data present. KRX equities gap closed 2026-07-22; Treasuries backfill status not re-confirmed.                                                                                                                                                                                                                                    | NOT PROVEN — TradFi is batch-only |
| VIX FUTURE (CBOE) + CBOE yield INDEX + FX KRW | yes (+409 expansion)             | ✅ IS availability-index: data present. MTDS availability-index: data present. Part of the same 2026-07-21 backfill fleet launch; completion not independently re-confirmed this pass.                                                                                                                                                                                                             | NOT PROVEN — TradFi is batch-only |

> **Re-verified 2026-08-04** (`plans/audit/results/tradfi_mvp_cell_wiring_and_pipeline_verification_2026_08_04.md`,
> `unified-trading-pm@cc9e1d144`): the table above is now updated with fresh IS + MTDS availability-index reads (live
> prod data, 2026-08-04). **Paper/live wiring**: NO tradfi MVP cell has paper/live wiring proven — TradFi is batch-only
> this cycle (per `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md:82`). This finding replaces the 2026-07-24
> "not verified in this pass" placeholder; the wiring question is now definitively answered (batch-only, not a gap to
> close).

- [x] ✅ [DATA] P2. **Determine, per MVP cell, whether backfill=paper=live wiring is proven — VERIFIED 2026-08-04
      (`plans/audit/results/tradfi_mvp_cell_wiring_and_pipeline_verification_2026_08_04.md`,
      `unified-trading-pm@cc9e1d144`, dispatched via
      `/plans/archive/2026_07/tradfi_consolidated_native_ao_extract_2026_07_25.md` todo 1).** Verdict: **NO tradfi MVP
      cell has paper/live wiring proven** — TradFi is batch-only this cycle (per
      `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md:82`). Fresh IS + MTDS availability-index reads against
      live prod data (2026-08-04): all 6 MVP cells have pipeline data present. Cell 2 (S&P index options) flagged: 66%
      MTDS `attempted_failed` — launch not yet executed. Table above updated with per-cell verdicts. The extracting
      doc's todo is now `[x]` done; this closeout checkbox is flipped here as part of the reconciliation pass
      (`tradfi_consolidated_native_ao_extract_2026_07_25_finalize.md` todo 2).

## Progress Log

> **2026-08-09 line-cap remediation**: this parent had grown to 1005 lines, over the `check_line_caps.sh` 1000-line hard
> cap, blocking routine content edits (see
> `/plans/active/issues/tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md` todo 1). The
> 2026-07-30 through 2026-08-08 entries previously here (14 audit-pass / dispatch-pass log entries) moved **verbatim** —
> nothing summarized, rewritten, or dropped — to
> [`tradfi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/2026_07/tradfi_consolidated_closeout_history_2026_07_25.md)'s
> new "Progress Log entries — 2026-07-30 through 2026-08-08 (moved 2026-08-09, line-cap remediation)" section — same
> pattern as the 2026-07-24/2026-07-25 trims above. New entries append here going forward; see the history doc (or the
> "Progress Log — pointer" section below, which already holds the 2026-08-06/2026-08-09 entries) for the full record.

---

## Phase A2 (adapter/registry correctness) + Phase C (data-status/honest-coverage) — forked 2026-07-25

> **Second-tier line-cap trim** (this parent had grown back to 927 lines since the 2026-07-24 3-way split — a smaller,
> second-tier trim of the same kind, this time forking the STILL-OPEN residue of Phase A2 + Phase C rather than
> already-closed narrative). The 2 fully-closed Phase C mega-verdicts (the honest-coverage 3-finding verification, and
> the KRX human-readable-name 4/4-code-surfaces shipment) are pure historical record now — moved verbatim to
> [`plans/archive/2026_07/tradfi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/2026_07/tradfi_consolidated_closeout_history_2026_07_25.md)
> alongside the Progress Log (see below). Every STILL-OPEN item from A2 + Phase C moved to
> [`tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`](/plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md)
> (8 AO-dispatch-readiness fixes applied during the move — 2 broken cross-doc references restated inline, 1 finding-H
> digest reformat, 1 missing self-justification added, 1 stale whole-plan gate relocated to the child, 2 bundled
> VERIFY+DECIDE todos split — see that child's own fork-note for the full list). A gated finalize plan
> (`tradfi_registry_coverage_and_ao_readiness_2026_07_25_finalize.md`) reconciles + archives that child once its content
> is fully closed.
>
> **Open-todo digest (2026-07-25, so this fork is AO-legible without opening the child)** — **STALE, count-corrected
> 2026-07-31 (slot 14, AO-dispatch-readiness sweep)**: live `grep -c '^- \[ \]'` against the child shows **14 open**
> (not 11) as of 2026-07-31 — 3 genuinely new todos landed since 2026-07-25 (a 2026-07-29 historical-backfill execution
> todo, a 2026-07-29 operator-ruling dry-run todo, a 2026-07-29 Databento `by_date` re-feed P0), plus the child itself
> now carries its own copy of this same audit-obligation `[REVIEW]` todo (added when the child was created — an audit
> todo is re-run per-file as content evolves, per this parent's own established convention above). The 11 items
> originally named below are still open (still accurate as descriptions), just no longer the complete set — re-derive
> the live list from the child directly rather than trusting "11" as the total:
>
> - **A2 (adapter/registry correctness)** — 4 real checkboxes as of 2026-07-31. **Reconciled 2026-08-04** against
>   `/plans/archive/2026_07/tradfi_consolidated_native_ao_extract_2026_07_25.md`'s completed todos: CME
>   mbp_10/trades/tbbo capability-declaration verify (P1) — verified 2026-07-31 (billing enforcement confirmed live,
>   clean pass); KRX equities registry-vs-adapter verify (P2) — verified 2026-07-31 (fix holds, FX KRW no analogous gap,
>   both PASS); adapter dead-code/fallback audit (P2) — done 2026-07-31 (3-repo audit, 11 tracked todos filed in
>   `tradfi_adapter_dead_code_fallback_audit_2026_07_25.md`, all 3 repos clean of duplicate-implementation violations);
>   the `ohlcv_15m/24h` writer DESIGN decision and the `mvp_mode` DECISION remain split out as non-dispatchable pointers
>   in the forked child. Full MTDS+IS adapter smoke findings re-verify (P2) was substantively resolved for tradfi (0
>   tradfi-scoped open items across all 3 cited docs — checkbox-flip candidate, per the parent extraction's
>   deferred-item #1). The "two live defects" digest pointer (source-mislabel + FX manifest id) —
>   evidence-reconciliation sub-piece done (child plan Phase-B todo `[x]` RE-VERIFIED LIVE 2026-07-25); defect-fixing
>   sub-pieces remain conflict-gated in `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s Deferred section (parent
>   extraction deferred-item #2).
> - **Phase C (data-status/honest-coverage) — still-open residue only** — 6 named items as of 2026-07-31. **Reconciled
>   2026-08-04** against `/plans/archive/2026_07/tradfi_consolidated_native_ao_extract_2026_07_25.md`'s completed todos:
>   data-status page canonical render (P1) — verified 2026-07-27 (deployment-api@c19edcc, fully canonical, venue-lookup
>   holds); distinct-values/axis-value census (P1) — done 2026-07-28 (3 named dupes explained, 1 new P2 filed);
>   denominator/catalogue-completeness re-verify (P2) — done 2026-07-31 (all 3 findings re-measured, 0 recurrence); KRX
>   name-column follow-up tracking (P2) — **DONE 2026-07-31, name column already landed live** via daily
>   `lifecycle-catalogue-regen-tradfi` (green every day 2026-07-22 through 2026-08-04; all 6 KRX single-stock-equity
>   rows carry `name` column); catalogue-as-SSOT decision still stands (no `name` field in manifest schema). The
>   billing-gated Databento L2/L3 classification (P2) and BLOCKED-INFRA "Certify tradfi Layer-1" gate (P0) remain open —
>   see the forked child for current status. Re-checked 2026-08-04: BLOCKED-INFRA still blocked (catalogue
>   rebuild+promote "FINAL STEP" in `tradfi_backfill_throughput_followups_2026_07_24.md` still pending); billing-gated
>   classification verified 2026-08-04 by parent-extraction todo 5 (UAC@9fd24804 + MTDS@b0d44fb2, both shipped).
>
> **Retained here**: the ground-truth verdict + MVP universe (unchanged), the Codex SSOTs index, and the Aggregated
> source docs digest (untouched, 421 lines).

## Plan-quality — AO-dispatch-readiness pass (owed)

- [x] ✅ [REVIEW] P2. Run the same adversarial AO-dispatch-readiness pass that produced sports's Track Y findings A-G
      (the 6 defect classes: bare section shorthand, ambiguous verbs, delete-tagging inconsistency, missing
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
      across every real todo is still owed. **CLOSED 2026-07-25 (this pass)**: the 2026-07-25 second-tier line-cap
      trim's own design pass ran exactly this sweep against the A2 + Phase C content (since forked to
      `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`) and found + fixed 8 concrete defects: 2 broken
      cross-doc "above" references restated inline (the CME mbp_10/trades/tbbo todo, the Billing-gated Databento L2/L3
      todo), 1 broken "above" reference in the KRX name-column STILL-OPEN todo rewritten to state the fact directly, 1
      finding-H violation (the "two live defects" todo reformatted as a non-checkbox digest pointer), 1 missing
      self-justification added (the KRX catalogue-rebuild+promote sub-item), 1 stale whole-plan `gate_on_depends`
      relocated to the child that actually carries the gated content, the `related:` frontmatter gap closed (4 sibling
      AO-dispatch/triage docs added), and 2 bundled VERIFY+DECIDE todos split into a bounded AO-eligible verify + a
      non-dispatchable decision pointer each. This closes the sweep for A2+Phase C content; the remainder of this file
      (Ground-truth verdict, MVP universe, Aggregated source docs) was already spot-checked clean 2026-07-24 (see
      above). A fresh copy of this same audit-obligation todo now lives on
      `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` (an audit todo is re-run per-file as content evolves,
      not treated as permanently satisfied).

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
  needing the Split-notice table above)**. **STALE digest corrected 2026-07-31 (slot 14, AO-dispatch-readiness sweep)**
  — this section's item-level text still named the ORIGINAL 2026-07-24 P0s (catalogue/enumeration migration), both now
  done; see the Split-notice table above for the fuller re-derivation + evidence citations. **STALE AGAIN 2026-08-18
  (plan_reconciler)** — the counts/items below are ALSO now out of date; see the "STALE AGAIN 2026-08-18" correction
  in the Split-notice table above for current counts (1 open / 1 open, both a different item than named below in
  the phase_d_terminal_gate case) — not re-derived here to avoid a 3rd copy of the same drifting data:
  - [`plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md`](/plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md)
    (3 open — live 2026-07-31, down from 11)
    - **[DATA] P2.** RULED 2026-07-28 — qualifier-normalization fix (Option A)
    - **[DATA] P1.** RULED 2026-07-28 — decision on the 1,328-cell unrecoverable population
    - **[DATA] P2.** Verify + close `candle_feature_canonical_path_divergence_2026_07_20.md` todo 3
  - [`plans/active/tradfi_backfill_throughput_followups_2026_07_24.md`](/plans/active/tradfi_backfill_throughput_followups_2026_07_24.md)
    (1 open — live 2026-07-31, down from 11; the T+1 forward-fill job shipped + archived, see Aggregated source docs §
    Throughput / jobs / VMs below)
    - **[INFRA] P1.** Backfill-VM startup OOM rc137 + OOM remediation baked default + consolidator throughput/backlog
      monitor (3 sub-issues bundled)
  - [`plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md`](/plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md)
    (2 open — live 2026-07-31, unchanged)
    - **[DATA] P0.** MVP backfill readiness gate — run the tradfi MVP backfills only after A-D are green; still blocked
      on the chain-bundle sampler follow-up
    - **[DATA] P1.** Post-full-backfill reconciliation RUN checkpoint (both raw-tick and candles layers), gated on the
      P0 above going green

- **ID-format**:
  - [`plans/active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`](/plans/active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md)
    (1 open -- **digest corrected 2026-08-08**: the leg-hard-cap P2 + `build_leg()` P3 items below are stale, both `[x]`
    DONE 2026-07-26/27; actual open item is the residual-91-CBOE+312-DBEQ catalog re-apply, extracted into batch8 todo 1
    above)
  - [`plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md`](/plans/archive/issues/instrument_id_format_canonicalization_2026_07_08.md)
    - **[SCRIPT] P2.** DEX-pool catalog regeneration (finding 2, all 13 protocols)
    - **[DECISION] P2.** Confirm exact target quote-currency per on-chain-perp venue (finding 4)
  - [`plans/archive/issues/tradfi_cme_options_chain_legacy_layout_2026_07_10.md`](/plans/archive/issues/tradfi_cme_options_chain_legacy_layout_2026_07_10.md)
    (done) — 0 open todos (closed/archived/record-only)
  - [`plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md`](/plans/archive/2026_08/canonical_id_builder_retrofit_checklist_2026_07_08.md)
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
  - [`plans/archive/issues/phantom_captures_tradfi_2026_06_28.md`](/plans/archive/issues/phantom_captures_tradfi_2026_06_28.md)
    - **[CODE] P2.** Diagnose tradfi phantom root cause (ICE/FX 309 phantoms predate billing lockdown; blank data_type
      1,083 pre-v9 rows)
  - [`plans/archive/2026_08/issues/cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`](/plans/archive/2026_08/issues/cross_cutting_manifest_canonicalisation_findings_2026_07_11.md)
    (archived 2026-08-15) — 0 open todos (closed/archived/record-only)
  - [`plans/archive/2026_08/mtds_available_at_cross_asset_backfill_2026_07_13.md`](/plans/archive/2026_08/mtds_available_at_cross_asset_backfill_2026_07_13.md)
    (archived 2026-08-05, all 16 todos done)
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
  - [`plans/archive/2026_08/tradfi_multisource_backfill_2026_06_22.md`](/plans/archive/2026_08/tradfi_multisource_backfill_2026_06_22.md)
    (**ARCHIVED 2026-08-03** — both items below since resolved, digest stale, left for history)
    - ~~**[BACKFILL] P1.** Run the FX yahoo backfill to completion (operational)~~ — done, dry-run verified,
      `deployment-service@eab5aeb`
    - ~~**[TEST] P3.** NICE-TO-HAVE — deployment-service test skip resolves service name from worktree dirname~~ — done,
      `deployment-service@077a063`
  - [`plans/archive/tradfi_massive_dual_source_2026_05_28.md`](/plans/archive/tradfi_massive_dual_source_2026_05_28.md)
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
  - [`plans/archive/2026_08/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`](/plans/archive/2026_08/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md)
    - **[DESIGN] P2.** Decide whether real aggregated `ohlcv_15m`/`ohlcv_24h` TradFi bars are wanted (not just alert
      silence)
    - **[VERIFY] P3.** Trace the orchestrator/sentinel classification layer for `attempted_failed` vs `empty_confirmed`
  - [`plans/archive/issues/tradfi_databento_ohlcv_silent_zero_rows_2026_07_12.md`](/plans/archive/issues/tradfi_databento_ohlcv_silent_zero_rows_2026_07_12.md)
    (done) — 0 open todos (closed/archived/record-only)
  - [`plans/archive/issues/tradfi_ice_ohlcv_1m_no_working_fetch_path_2026_07_13.md`](/plans/archive/issues/tradfi_ice_ohlcv_1m_no_working_fetch_path_2026_07_13.md)
    (done) — 0 open todos (closed/archived/record-only)
  - [`plans/archive/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md`](/plans/archive/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md)
    (done) — 0 open todos (closed/archived/record-only; barchart keep-vs-purge RESOLVED 2026-07-30,
    quarantine-with-tracking per the 2026-07-20 operator ruling)

- **Throughput / jobs / VMs**:
  - [`plans/archive/issues/databento_default_executor_dns_starvation_risk_2026_07_17.md`](/plans/archive/issues/databento_default_executor_dns_starvation_risk_2026_07_17.md)
    - **[CODE] P1.** Give the Databento chunk pull a dedicated executor (mirror
      `tardis_csv_transport._get_parse_executor`)
    - **[AUDIT] P2.** Sweep the repo for other `run_in_executor(None, ...)` call sites doing network-blocking work
    - **[CODE] P2.** Consider an `aiodns`/`AsyncResolver` for aiohttp sessions
  - [`plans/archive/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`](/plans/archive/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/archive/2026_08/issues/tradfi_backfill_oom_remediation_2026_06_24.md`](/plans/archive/2026_08/issues/tradfi_backfill_oom_remediation_2026_06_24.md)
    — 0 open todos (archived 2026-08-16, plan_reconciler Phase -1; the 2 items below were both already `[x]` at
    archival time — env-override drop confirmed 2026-07-14/07-25, memray done 2026-07-27)
  - [`plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md`](/plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md)
    - **[REVIEW] P1.** Local verify now; Cloud Build deploy DEFERRED (operator 2026-07-10 — local-dev-only)
    - **[BACKEND] P1.** Per-run output-production verdict endpoint (the seam deployments links to)
    - **[REVIEW] P1.** QG both repos green + LOCAL verify the seam resolves live
  - [`plans/archive/issues/tradfi_t1_no_working_mtds_job_2026_07_17.md`](/plans/archive/issues/tradfi_t1_no_working_mtds_job_2026_07_17.md)
    — 0 open todos; `status: resolved` 2026-07-26 (live-reverified: 6 consecutive scheduled T+1 executions succeeded,
    2026-07-21 through 2026-07-26; archived 2026-07-26 per issue-doc-lifecycle.md)
  - [`plans/archive/issues/group_c_cloud_run_job_failures_triage_2026_07_16.md`](/plans/archive/issues/group_c_cloud_run_job_failures_triage_2026_07_16.md)
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
  - [`plans/archive/2026_08/data_status_page_ux_and_canonicalisation_2026_07_16.md`](/plans/archive/2026_08/data_status_page_ux_and_canonicalisation_2026_07_16.md)
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
  - [`plans/archive/issues/cme_combo_underlying_extraction_garbage_2026_07_19.md`](/plans/archive/issues/cme_combo_underlying_extraction_garbage_2026_07_19.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/archive/issues/instruments_service_fx_adapter_key_unresolved_2026_07_23.md`](/plans/archive/issues/instruments_service_fx_adapter_key_unresolved_2026_07_23.md)
    (`status: resolved`) — 0 open todos (closed/archived/record-only)
  - [`plans/archive/issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md`](/plans/archive/issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md)
    (`status: resolved`) — 0 open todos (closed/archived; ohlcv_1s/ohlcv_1m root-cause tracked in
    `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`, the 1,242-row CBOE `ohlcv_15m` reclassify shipped
    `market-tick-data-service@0cd76b93`)
    - **[DESIGN] P2.** Give `check_high_attempted_failed` a way to mark a cell "known-dead, expected-coverage-narrowed"
  - [`plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`](/plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md)
    - **[DATA] P1.** BLOCKED-OPERATOR-DECISION — legacy-twin bucket DELETES (defi/tradfi/pred), Ikenna's migration
      sign-off gates this
  - [`plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`](/plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md)
    (14 open — capped; the tombstone/`_default_csv_path()` item below is done, removed from this count 2026-07-30 —
    fixed `instruments-service@fc07e6b6`, `tradfi_satellite_ao_dispatch_batch4_2026_07_26.md` todo 4)
    - **[DATA] P0.** ES CME futures ohlcv 1s+1m — fleet FINISHED, manifest-verify still owed (MEASURED 2026-07-26: all 7
      `tradfi-bf-cme-ohlcv-1m-es-{2020..2026}` shards inserted 2026-07-21T03:42Z and self-deleted by 2026-07-21T09:48Z,
      zero preemptions)
    - **[DATA] P0.** ES CME OPTIONS (ES_OPT) ohlcv 1s+1m — NOT yet launched, but the stated blocker has CLEARED (the
      singleton-Databento-lock-holding futures fleet is gone; zero `tradfi-bf-*` instances exist as of
      2026-07-26T02:20Z)
    - **[INFRA] P1.** tradfi — same gates; Databento universe (GLBX/DBEQ/XCBF) + Yahoo (KRX/FX)
    - **[DATA] P1.** FINDING — IS `by_date` capture frozen ~2026-05-21 fleet-wide; tradfi degraded from ~2026-05-04
    - **[DATA] P1.** FINDING — ICE futures + CME futures-options not on Massive → BLOCKED-CREDENTIALS
    - **[DATA] P1.** tradfi CME futures reference gap from 2026-06-08 — Massive `/futures/vX/{products,contracts}` 404
    - **[IS] P1.** Backfill the IS CME (GLBX.MDP3) catalog for 2019-01-01→present
    - **[SCRIPT] P1.** (→ M-1) MTDS tradfi market-data backfill across all 3 datasets (GLBX.MDP3 + DBEQ.BASIC + CFE)
    - **[UAC] P1.** Unit tests for `databento_subscription_allowlist`
    - **[PM] P1.** QG grep-ratchet — no raw `batch.submit_job` outside the guarded `submit_batch_job`
    - +4 more (P2/P3) — see file for the rest

- **Cross-cutting infra / audit (shared across asset groups, tradfi-relevant)**:
  - [`plans/active/candle_canonical_path_migration_execution_2026_07_24.md`](/plans/archive/2026_07/candle_canonical_path_migration_execution_2026_07_24.md)
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
  - [`plans/archive/2026_07/mdps_features_reduced_artifact_tracker_2026_06_28.md`](/plans/archive/2026_07/mdps_features_reduced_artifact_tracker_2026_06_28.md)
    — ARCHIVED 2026-07-27, 0 open todos, all 9 mini-plans confirmed archived/complete
  - [`plans/active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`](/plans/active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md)
    - **[VERIFY] P1.** Check whether manifest regeneration is automatic or requires an explicit re-enumeration trigger
    - **[VERIFY] P2.** Spot-check 2-3 more findings from the smoke-test doc across all 3 layers
    - **[DECISION] P2.** Once the pilot trace (AAVE_V3) lands, decide the reconciliation cadence for the remaining 58
      findings
  - [`plans/active/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md`](/plans/archive/2026_08/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md)
    - **[DATA] P1.** instruments-service: canonicalise the `instrument_availability` write via the sink PREFIX mechanism
    - **[DATA] P1.** market-tick-data-service: rule on and fix the cefi chain tail (`partitioned_writer.py:291-293`)
    - **[DOCS] P2.** instruments-service + market-tick-data-service: correct three in-repo comments asserting hive
      layout
    - **[SCRIPT] P2.** unified-trading-pm: add a Phase-0 `-test-` assertion on the resolved WRITE bucket
    - **[DOCS] P2.** unified-trading-pm: add an explicit "never pass `--allow-live-prod-writes`" prohibition to the
      skill doc
    - **[DATA] P3.** instruments-service: decide whether `market_lifecycle`/`futures_contracts` are in the canonical
      shard grammar's scope
  - [`plans/archive/issues/canonical_closeout_open_questions_2026_07_18.md`](/plans/archive/issues/canonical_closeout_open_questions_2026_07_18.md)
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
  - [`plans/archive/issues/manifest_completeness_full_corpus_map_build_2026_07_20.md`](/plans/archive/issues/manifest_completeness_full_corpus_map_build_2026_07_20.md)
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
  - [`/plans/archive/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md`](/plans/archive/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md)
    - **[DATA] P1.** Assess blast radius on EXISTING candle data — any past MDPS run with `max_workers>1` over a
      heterogeneous file list
  - [`plans/active/issues/phantom_audit_estate_coverage_gap_2026_07_10.md`](/plans/active/issues/phantom_audit_estate_coverage_gap_2026_07_10.md)
    — **1 open (re-verified 2026-08-16)**: **[SCRIPT] P2.** Widen the phantom audit to the full ~47-bucket kind×AG
    matrix as ONE combined batched walk (per the 2026-08-08 operator ruling)
  - [`plans/active/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md`](/plans/archive/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/archive/issues/tarball_rotation_breaks_vm_recovery_2026_07_20.md`](/plans/archive/issues/tarball_rotation_breaks_vm_recovery_2026_07_20.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/archive/issues/ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md`](/plans/archive/issues/ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md)
    — 0 open todos (closed/archived/record-only)
  - [`plans/archive/issues/vm_backfill_data_correctness_findings_2026_06_29.md`](/plans/archive/issues/vm_backfill_data_correctness_findings_2026_06_29.md)
    — **CORRECTED 2026-07-27** (was falsely cited "0 open todos" — F4-F7 are prose findings, not checkboxes, so a naive
    checkbox-count read the doc as closed): F1-F3 fixed (instruments-service@a4dfa6b,
    market-tick-data-service@7da5f6ad/75c8f148); F4/F5/F6 are DeFi/CeFi findings, rehomed to
    `defi_consolidated_closeout_2026_07_18.md` / `cefi_consolidated_closeout_2026_07_18.md`; F7 is the TradFi-relevant
    finding, rehomed below.
    - **[DATA] P1.** F7 — TradFi capture is NOT `is_mvp`-gated (CeFi/DeFi catalog readers call `is_mvp`, TradFi gates
      nowhere). **Operator decision 2026-07-27: gate TradFi capture by `is_mvp`.** Confirmed active out-of-scope under
      the same `wave_launcher.py` cron: NASDAQ/NYSE full equity universe (~227 of ~278 tickers vs the 105-ticker basis
      universe, `launch-tradfi-bf-nasdaq-ohlcv-1m.sh:70`), CME 49-root list vs 9 MVP underliers (~39 out, incl. 10 FX
      futures + crypto BTC/ETH/MBT/MET + micros — operator-confirmed OUT). `ohlcv_1s` + non-MVP DeFi data_types:
      operator said KEEP pending per-item review, do not auto-strip. **Open keystone**: confirm whether the TradFi
      `expected_unattempted` enumerator itself filters by `is_mvp` (decides whether out-of-scope cells become dispatched
      gap cells) before building the gate. Source doc still `locked_by: live-defi-rollout` — archive it only after an
      explicit `[unlock-plan]` grant (not yet asked).

- **Newly discovered (2026-07-24 completeness sweep — `grep -l '^asset_group:.*tradfi'` hits not previously named in
  this section; several were already mentioned inline in the Phase A2 prose above but never carried a real entry
  here)**:
  - [`plans/archive/issues/instrument_availability_hive_canonicalisation_2026_07_21.md`](/plans/archive/issues/instrument_availability_hive_canonicalisation_2026_07_21.md)
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
    — **CORRECTED 2026-08-10 (na-eligibility-audit, tradfi tranche, dispatch agt-a70469 — was stale, said "0 open
    todos")**: actually 3 open todos (2 DEPENDENCY_BLOCKED, 1 OPERATOR_QUESTION); KEEP-NA valid, re-confirmed across 8
    consecutive audit passes. The follow-up `tradfi_phase_d_terminal_gate_2026_07_24.md` P0 still gates on this finding.
  - [`/plans/archive/issues/tradfi_docs_reconciliation_findings_2026_07_21.md`](/plans/archive/issues/tradfi_docs_reconciliation_findings_2026_07_21.md)
    — **CORRECTED 2026-07-30 (was stale — listed 3 items below as open after the doc had already closed all 35)**: 0
    open, `status: resolved`, **35/35 findings applied** (32 on 2026-07-21, final 3 — including these exact
    P1(L97)/P1(L460)/P1(L237) items — on 2026-07-27, `unified-trading-pm@935de9424` + `@1dd1a22fd`); archived
    2026-07-28. L97's supersede banner and L237's canonical-cutover-register rewrite are both live; L460's target
    checkboxes had already moved via the 2026-07-24 fork to `tradfi_manifest_content_recovery_completion_2026_07_24.md`
    and were found already `[x]` there — disposed as applied-by-decomposition, no parent-doc edit needed.
  - [`plans/archive/issues/tradfi_manifest_rebuild_deletion_resurrection_gap_2026_07_20.md`](/plans/archive/issues/tradfi_manifest_rebuild_deletion_resurrection_gap_2026_07_20.md)
    - **[BACKEND] P1.** Add a manifest-vs-disk consistency check so a `captured` row with no object on disk fails loudly
  - [`plans/archive/issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md`](/plans/archive/issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md)
    — **CORRECTED 2026-07-30 (was wrongly listed "0 open"; this is exactly the checkbox-grep trap the doc carried
    PROSE-only remaining work with zero checkboxes at generation time).** `status: open`, 4 open todos added 2026-07-27
    by the post-drain re-measurement (post-fix equity/etf/index canonicality 99.57%, up from 30.8%, but 3 new live-path
    residuals found):
    - **[DATA] P1.** Root-cause + fix the live-path null-`instrument_id` write for tradfi equity/ETF (NASDAQ/NYSE,
      `ohlcv_1m`+`trades`)
    - **[DATA] P1.** Root-cause why the FX `SPOT_PAIR` manifest-row `instrument_id` is still bare/null for
      post-2026-07-25 captures
    - **[DATA] P2.** Investigate the CBOE `ohlcv_15m` `INDEX`/`OPTION` null-`instrument_id` writes (103 rows)
    - **[DOC] P3.** Re-verify the `future`/`FUTURE` population characterization (now 9,126 rows and growing, was stale
      "2,023 static")
  - [`plans/archive/issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md`](/plans/archive/issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md)
    — **0 open todos, all 4 `[x]`.** RULED 2026-07-29 (wire via forward-poll opt-in flag) AND the concrete **[CODE] P1**
    implementation (VM_MVP_MODE metadata plumbing + `--mvp-mode` flag on `launch-tradfi-forward-poll.sh` + regression
    tests) are both now shipped — `deployment-service@c847395e`, quality-gates green, quickmerge landed on
    `live-defi-rollout`. Doc archived, nothing left to dispatch off it.
  - [`plans/archive/issues/tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md`](/plans/archive/issues/tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md)
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
  - [`plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md`](/plans/archive/issues/candle_feature_canonical_path_divergence_2026_07_20.md)
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

## Progress Log — pointer (full condensed milestone summary moved 2026-07-25)

> The full "condensed milestone summary" Progress Log (2026-07-18 through 2026-07-23 ticks, replacing the original
> ~1700-line tick-by-tick log per the 2026-07-24 split) moved verbatim to
> [`plans/archive/2026_07/tradfi_consolidated_closeout_history_2026_07_25.md`](/plans/archive/2026_07/tradfi_consolidated_closeout_history_2026_07_25.md)
> during this 2026-07-25 second-tier trim — nothing summarized, rewritten, or dropped. For exact commands, shas,
> measured numbers, and the full narrative, read that history doc or the 3 sibling children's own Progress Logs.

**State as of the 2026-07-25 fork**: manifest/content migration is substantially complete — catalogue (Surface A) and
manifest (Surface B) both migrated + re-verified live 2026-07-25, chain-bundle content (Surfaces C/D) tool shipped +
dry-run measured but `--apply` at scale still pending on a dedicated VM — with a 50,520-row retire-phase batch still
awaiting operator sign-off (Child 1); backfill throughput is measured + optimized (1.56x shipped), the catalogue
rebuild+promote "FINAL STEP" still pending as of 2026-07-25 (Child 2); the Phase-D terminal gate found and fixed 3 real
cross-cutting checker bugs but is not yet fully green, blocked on the chain-bundle sampler follow-up (Child 3). Phase A2
(adapter/registry correctness) + the still-open Phase C (data-status/honest-coverage) residue moved to a 4th child,
`tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` (Child 4), this same day. Two AO-dispatch satellite batches
(`tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`, `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`) and a
native-todo AO-eligibility extract (`/plans/archive/2026_07/tradfi_consolidated_native_ao_extract_2026_07_25.md`) have
since drafted AO-dispatchable candidates off this plan's satellite docs and native todos — all `status: draft`, pending
operator activation.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-06** (tradfi tranche, dispatch agt-e38653): **KEEP-NA — 0 native open todos (sole
  `[DATA] P2` MVP-cell-wiring checkbox flipped `[x]` 2026-08-04), coordination index disposition unchanged.** This doc
  is the tranche's aggregated-reference umbrella + `check_ag_closeout_linkage.py` linkage anchor, and its archival
  disposition is the still-pending operator decision (item 8 in
  `tradfi_autonomous_session_operator_decisions_2026_07_25.md`, option B recommended: keep as the tranche coordination
  index) — a folding/archival judgment call, never autonomous. `depends_on` 3 still-active children
  (`tradfi_manifest_content_recovery_completion_2026_07_24`, `tradfi_backfill_throughput_followups_2026_07_24`,
  `tradfi_phase_d_terminal_gate_2026_07_24`) gates archival per PLAN_FORMAT.md regardless. `assigned_vm` unchanged.
- **na-eligibility-audit 2026-08-09** (tradfi tranche, dispatch agt-3df41f) [body-hash:4adac7a23a03a549]: **KEEP-NA,
  valid** -- 0 native open todos confirmed; today's new MVP-of-MVP banner verified an accurate, correctly-scoped redirect
  (narrows near-term dispatch only, doesn't rewrite this doc). FLAGGED not corrected (over-cap doc, append-only budget):
  the "Aggregated source docs" digest entry for `tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` says "0 open
  todos" but that doc actually carries 3 -- see it directly. `assigned_vm` unchanged.
- **na-eligibility-audit 2026-08-10** (tradfi tranche, dispatch agt-a70469) [body-hash:a306d90bafa82e1d]: **KEEP-NA,
  valid.** `archive_exempt: true` + `depends_on` 3 still-active children
  (`tradfi_manifest_content_recovery_completion_ 2026_07_24`, `tradfi_backfill_throughput_followups_2026_07_24`,
  `tradfi_phase_d_terminal_gate_2026_07_24`) gates archival per PLAN_FORMAT.md regardless of this doc's own
  0-native-open-todo count. **Fixed this pass** (small, in-cap): the stale "0 open todos" digest pointer for
  `tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` the 08-09 marker flagged-but-declined-to-correct (over-cap
  budget concern) -- doc is 881 lines, well under the 1000-line hard cap, so a 1-line correction is safe; corrected
  above to the real count (3). `assigned_vm` unchanged.
- **na-eligibility-audit 2026-08-16** (tradfi tranche, dispatch agt-45ad7b): **KEEP-NA, valid.** 0 open todos
  confirmed (live grep). NOT an ARCHIVE candidate: `archive_exempt: true`, tranche aggregated-reference umbrella /
  `check_ag_closeout_linkage.py` linkage anchor with still-open dependent children gating its archival.
  `assigned_vm` unchanged.
- **`check_ag_closeout_linkage.py` linkage fix (2026-08-16)**: 3 single-AG `[tradfi]` docs had accumulated since the
  last linkage sweep with no mention here, tripping the ratchet (3 orphans vs baseline 0) — noted separately, not
  content this closeout plan otherwise tracks:
  `cboe_venue_level_discovery_floor_blocks_yahoo_treasury_pre_2020_2026_08_09.md` (CBOE venue-level discovery floor
  blocking real pre-2020 history on the Yahoo Treasury-INDEX series) and the
  `tradfi_satellite_ao_dispatch_batch12_2026_08_10.md` / `tradfi_satellite_ao_dispatch_batch12_2026_08_10_finalize.md`
  AO-dispatch pair. Content itself unreviewed by this entry — this fixes the linkage gap only.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries).
- **na-eligibility-audit 2026-08-18** (tradfi tranche, dispatch agt-31bfcb): **KEEP-NA, valid — reaffirmed (6th
  consecutive pass).** 0 open native todos (live grep confirmed). NOT an ARCHIVE candidate: `archive_exempt: true`,
  tranche aggregated-reference umbrella / `check_ag_closeout_linkage.py` linkage anchor, with still-open dependent
  children gating archival per PLAN_FORMAT.md regardless. Only intervening changes were the plan_reconciler
  child-digest count corrections (Split-notice table) and a context-scout touch — neither shifts this disposition.
  `assigned_vm` unchanged.
- **na-eligibility-audit 2026-08-19** (tradfi tranche, dispatch agt-5d34f9): **KEEP-NA, valid — reaffirmed (7th
  consecutive pass).** 0 open native todos (live grep confirmed). Doc came back into this run's scope because
  `plan_reconciler@193df835e1` touched it after the 08-18 marker (Split-notice table stale-count corrections) —
  content-only, doesn't shift disposition. NOT an ARCHIVE candidate: `archive_exempt: true`, tranche
  aggregated-reference umbrella / `check_ag_closeout_linkage.py` linkage anchor, with still-open dependent children
  gating archival per PLAN_FORMAT.md regardless. `assigned_vm` unchanged.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-21** (tradfi tranche): **KEEP-NA, valid — reaffirmed (9th consecutive pass).** 0 open
  native todos (live grep confirmed). NOT an ARCHIVE candidate: `archive_exempt: true`, tranche aggregated-reference
  umbrella / `check_ag_closeout_linkage.py` linkage anchor, with still-open dependent children gating archival per
  PLAN_FORMAT.md regardless. `assigned_vm` unchanged.
