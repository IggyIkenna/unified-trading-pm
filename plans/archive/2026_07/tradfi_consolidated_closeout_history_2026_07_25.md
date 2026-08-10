---
doc_type: plan
title:
  TradFi consolidated closeout — history companion (2026-07-25 second-tier trim — closed Phase C verdicts + condensed
  Progress Log)
summary: >-
  Companion doc to `tradfi_consolidated_closeout_2026_07_18.md` — moved verbatim during that plan's 2026-07-25
  second-tier line-cap trim (the parent had grown back to 927 lines since the 2026-07-24 3-way split; this trim forks
  the STILL-OPEN residue of Phase A2 + Phase C to `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` and extracts
  the FULLY-CLOSED historical narrative here). Carries 2 fully-closed Phase C mega-verdicts — the honest-coverage
  3-finding re-verification (out-of-window clipping, shard-dimension model, coverage-floor cross-propagation, all
  re-verified live 2026-07-25) and the KRX human-readable-name 4/4-code-surfaces shipment (2026-07-20) — plus the
  parent's full "condensed milestone summary" Progress Log (2026-07-18 through 2026-07-23 ticks). Nothing below was
  rewritten; it is the original text, relocated. Zero open todos — pure narrative/evidence record; the parent plan and
  its 3 siblings + the new registry/ao-readiness child remain the live sources of truth for all open work.
status: complete
nature: record
asset_group: [tradfi]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-service,
    deployment-api,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [tradfi, close-out, canonicalisation, honest-coverage, krx, catalogue, progress-log, history, plan-hygiene]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md,
    /plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md,
    /plans/active/tradfi_backfill_throughput_followups_2026_07_24.md,
    /plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md,
    /plans/archive/2026_07/tradfi_manifest_content_recovery_completion_history_2026_07_24.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  Plan-hygiene discipline (task_template.md §3 finding J — extract fully-closed sections as you go rather than wait for
  a remediation pass), applied during a 2026-07-25 line-cap-driven split of `tradfi_consolidated_closeout_2026_07_18.md`
  (927 lines, over the 500L soft-warn line for a plans/active/ doc and drifting back toward the 1000L hard cap since the
  2026-07-24 3-way split). This companion carries the 2 fully-closed Phase C mega-verdicts + the full condensed Progress
  Log; the STILL-OPEN Phase A2 + Phase C residue moved instead to
  `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` (a live, active child) — see that doc for the current open
  work, not here.
assigned_role: data_engineering
drift_direction: none
---

# TradFi consolidated closeout — history companion

> **Companion history doc, not the live plan.** It holds two things extracted verbatim from
> `/plans/active/tradfi_consolidated_closeout_2026_07_18.md` during that plan's 2026-07-25 second-tier line-cap trim:
> (1) 2 fully-closed Phase C mega-verdicts (honest-coverage re-verification, KRX name-column shipment) that were sitting
> inline in the "still-open Phase C" section despite being done; (2) the parent's full condensed-milestone-summary
> Progress Log. Nothing below was rewritten; it is the original text, relocated. All open todos (Phase A2 + the
> STILL-OPEN Phase C residue) moved instead to `/plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` —
> that document, not this one, is where current open work on this content lives. This companion has 0 open todos of its
> own.

---

## Phase C — closed verdicts (moved verbatim from the parent's Phase C section)

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
      IS venues show real per-`(venue, instrument_type)` splits with no blank-collapse (CME: FUTURE=2024/COMBO=1995/
      OPTION=1995; CBOE 5 types; ICE/NYSE/NASDAQ/KRX/FX all multi-type) — the 2026-07-07 `_split_by_instrument_type`
      writer fix is live for tradfi; residual blank-`instrument_type` rows (4,504/27,251) are exclusively
      `EXPECTED_WEEKEND`/`_HOLIDAY`/`_PRE_VENUE_LAUNCH` non-trading pre-stamps (already documented as "no fix needed" in
      the source doc) + 93 genuine unclassified adapter errors, not a writer regression; no DERIBIT-COMBO-style
      fake-venue analog exists in tradfi's venue list. (3) **coverage-floor cross-propagation — WAS STILL LIVE, NOW
      FIXED.** Confirmed the cited CME mismatch was still unresolved as of session start (`coverage_starts.py:175`
      `"CME": date(2010, 1, 1), # TODO verify` vs `venue_mapping.py:334` `"CME": "2020-01-01"` no TODO). Probed the live
      MTDS manifest per `coverage_starts.py`'s own docstring instruction — earliest CME `capture_status=captured` row is
      2020-01-01, every pre-2020 date is `empty_confirmed`/`expected_unattempted` — confirming `venue_mapping.py` was
      right. **Shipped: unified-api-contracts@32b2879c** updates `TRADFI_SOURCE_COVERAGE_START["CME"]` to
      `date(2020, 1, 1)` and drops the TODO; gate `dbd6491`→`32b2879c` all green (583s, sentinel
      `dbd649140e946cbcf91275a6bd10bd73c12516a5`). Matching P2 todo flipped in
      `coverage_floor_registries_no_cross_propagation_2026_07_17.md`. The other 2 registries (TARDIS `# TODO verify`,
      the 8 CeFi mismatches, POLYMARKET, DeFi drifts) are that doc's own separately-tracked P1/P2/P3 items, out of this
      tradfi-scoped todo's gate.

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

  > **Follow-up note (added 2026-07-25, in the parent, before this extraction):** this todo's own "STILL OPEN" items
  > (a)/(b) above were never separately tracked as their own todo until a 2026-07-25 plan-reconcile pass added one — see
  > `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`'s "KRX name-column STILL OPEN" todo for the current, live
  > status of (a)/(b). That todo is the active tracker; this entry is historical record only.

---

## Progress Log — condensed milestone summary (2026-07-24, replaces the pre-split ~1700-line tick-by-tick log)

> **The full tick-by-tick history was NOT deleted** — it was split verbatim across 3 sibling children by workstream in
> the 2026-07-24 3-way split (see the parent's own Split notice). This section is a short, condensed orientation only;
> for exact commands, shas, measured numbers, and the full narrative, read the relevant child's own Progress Log.

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

> **This "state as of 2026-07-24" summary is itself now historical** — see
> `tradfi_consolidated_closeout_2026_07_18.md`'s own "State as of the 2026-07-25 fork" paragraph (added by this same
> extraction) for the current bottom line, and `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` for the
> still-open Phase A2 + Phase C work.

## Progress Log entries — 2026-07-30 through 2026-08-08 (moved 2026-08-09, line-cap remediation)

> Moved verbatim from `tradfi_consolidated_closeout_2026_07_18.md`'s "## Progress Log" section during the 2026-08-09
> line-cap remediation (parent had grown to 1005 lines, over the 1000-line hard cap enforced by `check_line_caps.sh`) —
> nothing summarized, rewritten, or dropped, per
> `/plans/active/issues/tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md` todo 1.

- **na-eligibility-audit 2026-08-08** (tradfi tranche, dispatch agt-29c933): **KEEP-NA, valid -- 6th consecutive pass, 0
  checkboxes confirmed genuine (not a prose-trap), 1 stale digest fixed (see corrected `canonical_id_p1` entry below).**
  Also backfilling: `/ag-closeout-audit tradfi` 2026-08-08 (slot 6) drafted
  `tradfi_satellite_ao_dispatch_batch8_2026_08_08.md` (17 orphans found, 3 drafted) but its creation was never narrated
  here (only frontmatter touched) -- full detail lives in that plan's own Progress Log, not reproduced here.
- **`/ag-closeout-audit tradfi` 2026-08-06 (slot 3, dispatch agt-7d91ed, sharded scheduled `ag_closeout_auditor` worker,
  operator away)**: fresh full pass (Phase 0 via `generate_ag_closeout_audit_candidates.py`, extended with a direct dump
  for the full member list). 54 real tradfi-primary candidates classified via a 54-agent Workflow against the 11-doc
  covering set: 1 excluded (genuine mistag, `defi_cefi_venue_chain_axis_contamination_2026_07_28.md` is 100% defi/cefi),
  15 archivable now, 2 archivable-after-planned-work, 36 orphaned (11 partial, 25 never-touched) — up from batch6's 12,
  mostly newly-surfaced findings (2 issue docs postdate batch6's 2026-08-01 cutoff; several others' latest dated
  Progress Log section moved since). Phase 3 re-verified batch6's own Deferred items first (batch5's MDPS
  `continuous_future` re-test DID ship 2026-08-03, but the result — 20.8%, up from 18.9% — did NOT clear
  `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`'s blocker, so it correctly stays deferred), then
  conflict-checked the 36 orphans: 4 cleared (from 5 source docs — 2 combined into one todo touching the same file) and
  are drafted as `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` (+ gated finalize), `status: draft` pending
  operator review — including `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`'s 0%-twin-coverage root-cause
  investigation, which batch6_finalize's own todo 2 explicitly anticipated as "a batch7 todo." The other 32 orphans stay
  deferred across 5 categories in batch7's own Deferred/Flagged sections (too-large-or-risky, operator-gated,
  self-dispatched-already/stale-tag, already-drafted-elsewhere-pending-promotion, cross-tranche-owned) — see that plan
  for the full per-doc accounting. **Standing-state note**: `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` has sat
  `status: draft`, unreviewed, for 5 days as of this pass — flagging for operator attention, not re-drafting its
  content.
- **2026-08-04 (slot-16, review — `tradfi_consolidated_native_ao_extract_2026_07_25_finalize.md` todo 2
  reconciliation)**: reconciled this closeout doc's own native content against the parent extraction's 9 completed todos
  (verified by slot-13, 2026-08-04, in the finalize plan's todo 1). Changes in this commit: (a) MVP-cell table — all 6
  rows updated with fresh IS + MTDS availability-index evidence from
  `plans/audit/results/tradfi_mvp_cell_wiring_and_pipeline_verification_2026_08_04.md`; Paper/live wiring column now
  definitively reads "NOT PROVEN — TradFi is batch-only" (per
  `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md:82`); 0 remaining "NOT VERIFIED IN THIS PASS" cells. (b)
  `[DATA] P2` MVP-cell-wiring-proof checkbox flipped `[x]` with evidence citation. (c) Phase A2+C digest updated — A2
  and Phase C item-level notes reconciled against parent-extraction todos 2-9 (all 8 now completed); KRX name-column
  note updated (name column already landed live via daily regen, both sub-items confirmed done). (d) 3
  deliberately-deferred native todos re-checked 2026-08-04: (#1) adapter smoke findings — still 0 tradfi-scoped open
  items, checkbox-flip candidate; (#2) live defects — evidence-reconciliation done, defect-fixing still conflict-gated
  (no gate cleared); (#3) BLOCKED-INFRA Certify tradfi Layer-1 — still blocked (catalogue rebuild+promote "FINAL STEP"
  in `tradfi_backfill_throughput_followups_2026_07_24.md` still pending, live-verified 2026-08-04). (e) Split-notice
  digest's catalogue-migration line — already corrected by the 2026-07-31 sweep; live re-verified catalogue commit
  `instruments-service@52d8b3ef` still on LDR, claim accurate.
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — swapped the IS-SSOT codex doc for the 2 other live
  sibling children (Phase-D gate + registry/coverage) so the umbrella's reading list covers all 3 forked-child
  companions plus the 3 domain codex SSOTs.
- **`/ag-closeout-audit tradfi` 2026-08-01 (slot 2, dispatch agt-d7b683, scheduled `ag_closeout_auditor` worker,
  operator away)**: fresh full pass. Phase 0 fixed a same-session tooling gap
  (`generate_ag_closeout_audit_candidates.py` wasn't resolving this doc's own `depends_on:` for finalize-less forks —
  see this doc's own `depends_on:` fix above) that corrected the covering-plan count 11→13 and the real candidate count
  67→65. Phase 1 ran a 65-agent Workflow classifying every tradfi-primary candidate against the 13-doc covering set: 31
  excluded (genuinely multi-AG, confirmed by content not just tag), 3 archivable now, 19 archivable-after-planned-work,
  12 orphaned (5 partial, 7 never-touched). Phase 3 conflict-check cleared 4 of the 12 for a fresh batch —
  `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` (+ gated finalize), `status: draft` pending operator review. The
  other 8 orphans stay deferred (3 too-large-or-risky unchanged + 1 newly-scoped, 3 operator-gated unchanged, 1 whose
  precondition changed since batch5 and needs fresh investigation before any todo —
  `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`'s delete gate now measures 0% twin-coverage, not the 100% it
  needs). One further genuine orphan (`mtds_is_full_adapter_smoketest_findings_2026_07_07.md`, 4 TradFi bugs never
  promoted to checkboxes) is flagged but not batched — that doc is genuinely 5-AG-shared
  (`parent_epic: instruments_master`), so per the primary-owner rule its write belongs to whichever tranche actually
  owns it. See `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md`'s own summary + Deferred sections for full detail.
- **AO-dispatch-readiness sweep 2026-07-31 (slot 14, via
  `/plans/archive/2026_07/tradfi_consolidated_native_ao_extract_2026_07_25.md` todo 10 — the 2 remaining categories:
  stale checkboxes, missing definition-of-done)**: `sports_consolidated_closeout`'s Track Y method applied to the 2
  categories this file's own todo (below, `[x]` closed 2026-07-25) left owed after closing for A2+Phase C content only.
  **Real-checkbox sweep**: `grep -n '^- \[ \]\|^- \[x\]'` finds exactly 2 native todos in this file (line ~250
  `[DATA] P2` MVP-cell-wiring-proof, line ~324 `[REVIEW] P2` the audit-pass todo itself) — both carry a stated
  definition-of-done, neither is stale (the P2 correctly cross-references its live tracking location; the REVIEW todo's
  own `[x]` closure text is accurate for its stated A2+Phase C scope). **Missing-dod sweep: clean, 0 findings.**
  **Stale-checkbox-class sweep (the digest bullets, not real checkboxes, per this file's own bold-no-brackets
  convention)**: live re-derived 4 digest sections against their cited child docs' actual `- [ ]` counts — found + fixed
  3 stale entries: (1) Split-notice digest's `tradfi_manifest_content_recovery_ completion_2026_07_24.md` line
  (previously flagged stale by an earlier pass but never actually corrected — this pass replaced the "8 open, catalogue
  NOT yet executed" text with the true 3-open/all-done state); (2) same digest's
  `tradfi_backfill_throughput_followups_2026_07_24.md` line (6→1, T+1 job shipped+archived, not previously flagged); (3)
  the separate "Aggregated source docs § Child plans" digest for the SAME 3 children, which cited yet a THIRD,
  even-more-stale set of counts (11/11/2) naming the ORIGINAL 2026-07-24 P0s that are now done — corrected to match.
  Also re-derived the Phase A2+C fork's own digest for `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` (11→14
  open; 3 genuinely new todos landed since 2026-07-25 plus the child's own copy of this same audit-pass todo) —
  corrected with a count-drift note rather than a full item-by-item rewrite (all 11 originally-named items are still
  open and still accurately described; only the total was stale). `tradfi_phase_d_terminal_gate_2026_07_24.md`'s digest
  (2 open) was independently re-verified accurate, no correction needed. Evidence: live grep counts run 2026-07-31
  against each child's current `plans/active/*.md`. No new stale entries found beyond these 4; not an exhaustive
  re-verification of every one of the ~40 docs referenced in the Aggregated source docs section (out of this todo's
  1h-class scope) — the 4 corrected here were the highest-risk (most recently active, most-cited) digests.
- **na-eligibility-audit 2026-07-31** (tradfi tranche, dispatch agt-6d6eaf): **KEEP-NA-STALE, re-verified — citation
  still accurate, no change needed.** This is this doc's correct owning tranche (per the note below). Independently
  re-checked the sole open checkbox's duplicate claim against current state, not a rubber-stamp: the extracting doc
  (`/plans/archive/2026_07/tradfi_consolidated_native_ao_extract_2026_07_25.md`) is still `status: active` /
  `assigned_vm: planning`, and its own near-verbatim copy of this todo is still unchecked. Only one commit has touched
  this file since the 2026-07-30 marker (`39d663e92`, 2026-07-31 — an unrelated cross-reference path fix), so nothing
  material changed. `assigned_vm` stays unchanged; no backlog impact.
- **na-eligibility-audit 2026-07-30** (infra tranche, dispatch agt-30721a): KEEP-NA-STALE — sole remaining native
  checkbox is already duplicated near-verbatim in the active
  `/plans/archive/2026_07/tradfi_consolidated_native_ao_extract_2026_07_25.md`; citation added above, zero
  `assigned_vm`/backlog impact. NOTE: this doc's real `asset_group` is `[tradfi]`, not `infra` — a residual scope-leak
  from this session's pre-fix Phase 0 population (see
  `na_doc_tranche_inventory_stale_citation_membership_cross_contamination_2026_07_29.md`'s own Progress Log for the full
  accounting); classified here for completeness, no other state changed, the `tradfi` tranche's own future audit owns
  this doc going forward.
- **Operator-ruling closeout sweep 2026-07-30**: grepped this file for every `RULED`/`Operator-ruled`/`operator ruling`
  instance. Found the `tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md` digest entry (Aggregated source docs §
  TradFi-specific residuals) was STALE — it described a "remaining open" `[CODE] P1` implementation todo that had
  already shipped. Verified live: the issue doc itself shows all 4 todos `[x]`, and
  `git -C deployment-service log --oneline -1 c847395e` resolves to
  `feat(vm): wire tradfi mvp_mode via opt-in --mvp-mode flag on the forward-poll launcher` — corrected the digest entry
  above to reflect 0 open todos. The other 2 live rulings in this file (ES CME futures manifest-verify + ES_OPT launch,
  both "Operator-ruled 2026-07-29") are pointers to concrete `[DATA] P0` todos tracked in
  `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` (confirmed still genuinely open there, not this file's own
  checkbox to flip, and out of this pass's assigned-file scope) — left as-is, already accurate.
- **na-eligibility-audit 2026-08-01** (tradfi tranche): **KEEP-NA-STALE, re-verified — citation still accurate.** Sole
  native open checkbox (MVP-cell-wiring-proof, line ~262) re-read; count matches tranche-inventory tool (1).
  Independently re-confirmed the extracting doc
  (`/plans/archive/2026_07/tradfi_consolidated_native_ao_extract_2026_07_25.md`) is still `status: active` with its own
  near-verbatim copy still unchecked. The only touches since the 2026-07-31 marker were the 2026-08-01
  `/ag-closeout-audit tradfi` pass (batch6 drafting + a `depends_on:` fix, neither affecting this todo) and a
  context-scout backfill — nothing material changed. `assigned_vm` stays unchanged.
- **na-eligibility-audit 2026-08-02** (tradfi tranche, dispatch agt-6397c9): **KEEP-NA-STALE, re-verified — citation
  still accurate (4th consecutive confirmation).** Full end-to-end read via an independent sub-agent classification (892
  lines: frontmatter, Split notice, Ground-truth verdict, MVP table, the one native todo, Progress Log, Phase A2+C fork,
  Plan-quality review, Codex SSOTs, Aggregated source docs digest); sole native checkbox count reconciled (1/1) —
  confirmed the "digest bullets" throughout the Aggregated source docs section are deliberately bold-not-bracket
  formatted and correctly NOT counted as this doc's own open checkboxes. Independently re-confirmed the extracting doc
  (`/plans/archive/2026_07/tradfi_consolidated_native_ao_extract_2026_07_25.md`) is still
  `status: active`/`assigned_vm: planning` with its own copy still unchecked. Nothing here is RECLASSIFY-eligible — the
  sole native todo is correctly NA because the real dispatchable copy already lives on an active planning doc.
  `assigned_vm` stays unchanged.
- **context-scout 2026-08-03**: re-verified context_scope (6 entries) — still accurate, no changes needed.
- **archive_candidates_content_verification 2026-08-06 (slot 9, review)**: `archive_exempt: true` — this is an umbrella
  coordination index (`nature: process`) serving as a standing reference hub for the TradFi consolidated close-out. All
  2/2 native checkboxes are done, but the doc's "Aggregated source docs" section is actively maintained as the single
  entry-point digest of ~50+ tradfi-touching plans/issues with live open-todo counts. It has 3 active child plans with
  open work (`depends_on`). Archiving it would orphan the coordination index for the multi-phase tradfi close-out.

- **na-eligibility-audit 2026-08-07** (tradfi tranche): **KEEP-NA, valid -- re-verified, unchanged.** 0 real open
  checkboxes (confirmed via literal-pattern grep: 12 `[x]`, 0 `- [ ]`; the 3 raw `[ ]` substring hits are prose
  describing the pattern, not checkboxes). `archive_exempt: true` is set in frontmatter (2026-08-06 ruling) and
  correctly NOT re-litigated here -- this doc is a standing coordination-index/reference hub for the tradfi close-out
  with 3 active child plans depending on it, not an ARCHIVE candidate despite having 0 native open todos. Doc stays NA.
