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
