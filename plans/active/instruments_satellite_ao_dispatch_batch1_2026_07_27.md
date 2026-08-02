---
doc_type: plan
title:
  Instruments satellite docs — AO dispatch batch 1 (5 AO-eligible todos extracted from 1 NA-audited instruments plan via
  /na-eligibility-audit)
summary: >-
  First /na-eligibility-audit interactive dry-run (tradfi tranche, 2026-07-27) classified
  honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md as mixed across 14 open items: 8 are genuinely
  operator/judgment-gated (stay NA), 5 are bounded worker-determinable audits/spot-checks with an already-proven method
  or already-decided pattern, and 1 (the CLOB-on-chain HYPERLIQUID/ASTER classification widen) turned out to be already
  shipped elsewhere — closed on the source doc directly, not extracted here. Per the shared conflict-check protocol's
  fresh-carve-out shape, only the 5 conflict-cleared items are extracted here — checked against every active
  parent_epic:instruments_master planning doc, zero collisions found. This is the first
  `instruments_satellite_ao_dispatch` batch (no prior one existed for this parent_epic). **Process note**: the dry-run's
  first-pass sonnet classification of this specific doc under-read it (missed 8 of its 14 open items on the first read);
  a full direct re-read before authoring this batch caught the gap — see the source doc's own 2026-07-27 Progress Log
  entry for the full accounting.
status: active
nature: process
asset_group: [cefi, defi, tradfi, prediction]
stage: [meta]
repos: [instruments-service, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [instruments, ao-dispatch, na-eligibility-audit, satellite-docs, batch-1, plan-hygiene]
related:
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/archive/2026_07/instruments_satellite_ao_dispatch_batch1_finalize_2026_07_27.md,
    /plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
archive_exempt: true # archival routed through plans/active/issues/instruments_satellite_batch1_finalize_false_completion_claim_2026_08_02.md's reconciliation, not standalone (see Progress Log)
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /na-eligibility-audit interactive dry-run, tradfi tranche, 2026-07-27 (operator-supervised, sonnet-tier classification
  workers, requested to validate the skill's own Phase 0-5 procedure before its daily cron's first unsupervised fire).
  Phase 2 conflict-checked this candidate against all 4 active parent_epic:instruments_master planning docs
  (canonical_id_builder_retrofit_checklist_2026_07_08.md, infra_capture_and_devops_leftovers_2026_07_06.md + finalize,
  is_daily_enum_capture_heal_2026_07_07.md) — zero overlap found.
context_scope:
  [
    /plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md,
    /codex/02-data/honest-coverage-model.md,
    deployment-api/deployment_api/services/data_status/breakdowns_core.py,
    instruments-service/instruments_service/engine/orchestrator/writers.py,
  ]
---

# Instruments satellite docs — AO dispatch batch 1 (na-eligibility-audit extraction)

## Why this plan exists

`honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`'s D6 design decision was approved and largely
shipped 2026-07-07 (writer fix, UI fix, phantom `SPOT_PAIR` removal). Several remaining open todos are bounded
execution/audit work — a checkable fact-find with an already-proven method, or a scoped code change mirroring an
existing named pattern — that was simply never assessed against the AO dispatch-scope bar. Two items stay correctly NA:
the 2 originally-flagged items (the CEFI instrument-definition parquet resharding design, explicitly operator-gated
pending a mockup review; and moving `market_metadata` off the MTDS axis, a genuine two-option judgment call) plus 6 more
found on full re-read (Finding 1's SPORTS/PREDICTION leaf re-verify, paced to the operator's own mockup-review cadence;
the phantom `OPTION` removal on bare OKX/OKX_FUTURES, explicitly deferred pending a go-ahead that hasn't been given; the
BINANCE-DELIVERY GAP tooltip copy change, low-priority/cosmetic; retiring DERIBIT-COMBO as its own venue key, which
needs its own unscoped consumer-impact audit first; renaming the "Instrument breakdown" venue-detail link, a genuine
naming call gated on other work landing; and the historical CeFi/TradFi manifest backfill, whose approach depends on a
not-yet-confirmed generic reprocessing utility). This plan extracts only the 5 conflict-cleared bounded items; the
source doc is untouched (beyond one stale-checkbox citation fix, done directly, not via this batch) and stays
`assigned_vm: NA` for its 8 judgment-gated items.

## Rules this plan follows

- Every todo ends with `Source: <doc>.md`, quoting the original item's own text, plus a **Done when** clause.
- Checked against all 4 currently-active `parent_epic: instruments_master` planning docs — zero file-level collisions.
- `sequential:` deliberately unset — these 5 touch disjoint code paths and are independently dispatchable.
- The source NA doc's own checkboxes for these 5 extracted items are NOT touched by this plan — the finalize twin does
  that once each todo below is actually `[x]`. (The 1 already-shipped item found during authoring — CLOB-on-chain
  HYPERLIQUID/ASTER classification widen — was closed directly on the source doc instead, since no new work is needed.)

## Todos

- [x] ✅ [DATA] P1. **Raw-parquet spot-check the 5 additional CeFi venues** flagged by the pre-audit's registry read as
      likely hitting the same multi-type blank-collapse: `OKX-FUTURES`, bare `BYBIT`, `BINANCE-FUTURES`,
      `KRAKEN-FUTURES`, `BINANCE-DELIVERY` — same method already used on DERIBIT/ASTER (download
      `availability_index.parquet`, check `instrument_type` distribution). Repo: instruments-service. Source:
      `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` ("Raw-parquet spot-check the 5 additional
      CeFi venues..."). Done when: each of the 5 venues has a recorded pass/fail against the same coverage class
      DERIBIT/ASTER were checked against, with the raw-parquet read cited. — read-only, no commit (no code changed).
      Downloaded `gs://instruments-store-cefi-prd-central-element-323112/_index/availability_index.parquet` (the exact
      bucket cited in the source doc's Finding 3) and computed the `instrument_type` distribution per venue, split
      pre/post the 2026-07-07 writer-fix date. Result: **2 of 5 genuinely hit the DERIBIT-class blank-collapse bug, 3 of
      5 did not**: - **FAIL→confirmed bug (matches DERIBIT's class)**: bare **`BYBIT`** — 277 blank-`instrument_type`
      rows pre-2026-07-08 (out of 3,847 pre-fix rows: PERPETUAL 2,380 / FUTURE 1,190 / blank 277), **0 blank** in the 58
      post-fix rows (cleanly split PERPETUAL 20 / FUTURE 20 / SPOT_PAIR 17 / 1 `expected_unattempted` placeholder) — the
      writer fix resolved it going forward; historical rows stay blank pending the already-tracked separate backfill
      todo. **`BINANCE-DELIVERY`** — 444 blank + 31 `expected_unattempted`-null rows pre-fix (out of 4,783: FUTURE 2,182
      / PERPETUAL 2,126 / blank 444), **0 blank** in the 41 post-fix rows (FUTURE 20 / PERPETUAL 20 / 1 placeholder) —
      same pattern, fix confirmed working. - **PASS→no bug found**: **`OKX-FUTURES`**, **`BINANCE-FUTURES`**,
      **`KRAKEN-FUTURES`** — **zero** blank-type rows anywhere in their full history (2019-03-30 → 2026-07-27); all
      three were already cleanly split by `instrument_type` even before the fix (e.g. BINANCE-FUTURES/KRAKEN-FUTURES:
      PERPETUAL 2,657 / FUTURE 11 pre-fix, byte-identical row totals between the two venues — a real coincidence, not a
      shared-bug artifact, each venue's own rows filtered independently). The registry-derived assumption that these 3
      would hit the same collapse as DERIBIT does not hold in the real data. - **Secondary observation (not a new
      finding — corroborates already-tracked work, no new issue doc filed)**: OKX-FUTURES's own PERPETUAL rows (2,631
      historically) stop entirely from 2026-07-08 onward (only FUTURE continues, 101-136 rows/day) — checked whether
      this is a live capture regression by confirming OKX-SWAP independently and continuously captured its own PERPETUAL
      rows across the same window (402-423/day, unaffected), ruling out a routing-consolidation explanation. This is
      consistent with — not a new instance of — the already-tracked OKX-FUTURES dated-futures-mislabeled-PERPETUAL
      cleanup (`plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md:458-461`, fix tracked in
      `/plans/archive/issues/cefi_batch2_010_misscoped_gated_bundle_2026_07_26.md` todo 3): OKX-FUTURES's canonical
      declared type is `future`-only (`cefi_future_instrument_type_no_candle_schema_contract_2026_07_21.md`'s venue
      table), so the historical PERPETUAL rows were themselves the mislabel, and their disappearance from 2026-07-08
      reads as that mislabel resolving, not a capture gap opening. Confirmed all 4 NULL-`instrument_type` rows found
      across the 5 venues are honest `capture_status=expected_unattempted` placeholders (`row_count=0`), unrelated to
      the blank-collapse bug pattern.
- [x] ✅ [DATA] P1. **Add `missing_dates`/`dates_found_list` to the per-instrument_type and per-underlying breakdown
      entries** (`deployment-api/deployment_api/services/data_status/breakdowns_core.py` —
      `_build_instrument_type_breakdown` ~405-409, `_build_underlying_breakdown` ~508-512; mirror
      `_build_data_type_breakdown`'s entry shape ~629-643, which already carries this). Needs a matching
      `deployment-ui/src/components/DataStatusTab.tsx` render tweak and the `TurboInstrumentTypeStatus`/
      `TurboUnderlyingStatus` types in `api/client.ts:1156-1169` to carry the new fields (mirroring
      `TurboDataTypeStatus` at `client.ts:984-999`). Repo: deployment-api, deployment-ui. Source:
      `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` ("Add `missing_dates`/`dates_found_list`
      to the per-instrument_type and per-underlying breakdown entries..."). Done when: both breakdown entry types carry
      both fields in the mirrored shape, the UI renders them, with a passing test. — deployment-api@554cde9,
      deployment-ui@8f6c4bc. `_build_instrument_type_breakdown`/`_build_underlying_breakdown` now compute
      `it_found_dates`/`ul_found_dates` (intersection of observed vs. UAC-expected dates) and emit `dates_missing`,
      `missing_dates`, `dates_found_list` — same shape as `_build_data_type_breakdown`. 2 new unit tests
      (`test_instrument_type_breakdown_includes_missing_dates_and_found_list`,
      `test_underlying_breakdown_includes_missing_dates_and_found_list`) assert the exact found/missing split on a
      narrow 3-day fixture; both pass (4/4 incl. the 2 pre-existing clamp tests). `TurboInstrumentTypeStatus`/
      `TurboUnderlyingStatus` in `client.ts` carry the 3 new optional fields; `DataStatusTab.tsx`'s instrument_type and
      underlying rows now render an expandable found/missing date-list drilldown (mirroring the existing per-data_type
      block, `openShardDetail` wired with `instrument_type`/`underlying`/`data_type: ""`). Verified: `tsc --noEmit`
      clean, `eslint` clean, full `npm run build` clean, full `vitest run` (1099 passed / 16 skipped, no regressions),
      both repos' `quality-gates.sh` green pre-commit.
- [x] ✅ [DATA] P1. **Pull the real per-instrument_type breakdown for DERIBIT live** (the comparison built for the
      source doc used illustrative numbers pending this) and confirm whether OPTION coverage is actually healthy or is
      itself a live gap once visible. Repo: market-tick-data-service. Source:
      `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` ("Pull the real per-instrument_type
      breakdown for DERIBIT live..."). Done when: a real, current per-instrument_type breakdown for DERIBIT live is
      recorded (not inferred), cited against the live source data, with an explicit OPTION-coverage verdict. —
      read-only, no commit (no code changed). Pulled
      `GET /api/data-status/manifest?service=instruments-service&asset_group=CEFI&start_date=2026-06-27&end_date=2026-07-27&secondary_axis=instrument_type`
      live against the real prod deployment-api Cloud Run endpoint
      (`https://uts-shared-deployment-api-cldtjniqvq-an.a.run.app`), 2026-07-27, HTTP 200 — pulled twice independently
      (a sub-agent fetch, then a direct curl reproducing byte-identical numbers) and confirmed against the parsed JSON
      response. Real, current DERIBIT `instrument_types` breakdown (30-day window,
      `deployment-api/deployment_api/services/data_status/breakdowns_core.py:395` `_build_instrument_type_breakdown`):
      **OPTION 2,676/2,677 dates (99.96%)**, FUTURE 2,676/2,677 (99.96%), PERPETUAL 2,676/2,677 (99.96%), COMBO
      1,434/1,435 (99.93%), SPOT_PAIR 1,190/1,191 (99.92%) — all five types near-identical and near-100%, each missing
      exactly ONE day (2026-07-27, today, `expected_unattempted_pending_fetch` — not yet fetched, not a failure).
      **Verdict: OPTION coverage is healthy — not a live gap.** The venue-level blend this doc originally flagged
      (`instrument_types: null`, 2026-07-07) is resolved in production: the writer-split fix
      (`_split_by_instrument_type`, shipped same day) is confirmed live-visible — an OPTION-specific outage would now
      show up distinctly instead of hiding inside one blended venue-level number (venue-level completion_pct in this
      same pull: 96.77% over the 30-day window / 99.99% cumulative honest_coverage, consistent with the per-type
      numbers, not blending them). **Repo-tag note**: the data actually pulled + verified is instruments-service's
      reference-data breakdown, not an MTDS market-tick-data-service pull — `market-tick-data-service`'s own DERIBIT
      OPTION adapter (`tardis_options_adapter.py`) is `BLOCKED-CREDENTIALS`/not live, so there is nothing to check on
      the MTDS side; the source doc's own text (`honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`
      section discussing the two as separate pipelines) and its own "OPTION coverage... blended into one 99%+ number"
      framing both refer only to the instruments-service breakdown throughout — this todo's `Repo:` tag reads as
      inherited from the source doc's multi-repo `repos:` frontmatter, not a substantive claim. Noted here rather than
      filed as a separate issue doc since it doesn't change the verdict or require any fix. Residual, out-of-scope
      cosmetic gap also noted in passing: the top-level `instrument_types.OPTION` entry doesn't itself carry
      `missing_dates`/`dates_found_list` (only its nested `data_types.instruments` child does — the data_type-weighted
      aggregation override at `breakdowns_core.py:472-495` rewrites `dates_found`/`dates_expected`/`completion_pct` at
      the parent level but not the missing-date lists) — a display nuance downstream of the already-shipped
      missing_dates/dates_found_list todo above, not a new correctness bug, so not separately filed.
- [x] ✅ [VERIFY] P2. **Audit whether the same MTDS/reference-data conflation risk exists anywhere else** — e.g. the
      TradFi `POLYGON`/`FRED` reference-data-in-the-wrong-registry smell noted at `market_data_categories.py:1279-1286`
      (not yet confirmed live). A precisely-scoped "does X match Y" check, not a design call. Repo: instruments-service.
      Source: `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` ("Audit whether the same
      MTDS/reference-data conflation risk exists anywhere else..."). Done when: a definitive yes/no is recorded for
      TradFi POLYGON/FRED with the checked evidence cited; if yes, file a follow-up todo/issue doc rather than fixing
      inline (this todo is the audit, not the fix). — read-only, no commit (no code changed to the audited registries;
      one new issue doc filed for the one gap found). **Verdict: mostly resolved, with one small missed spot found.**
      The two specific in-flux threads the source doc left open (2026-07-29/30) have both since settled, verified
      2026-08-02 against current `origin/live-defi-rollout` HEAD: (1) **`market_data_categories.py`'s
      `VENUE_DATA_TYPE_CAPABILITIES["POLYGON"]`** (the exact site cited) — fixed, `unified-api-contracts@e34afc1d`
      (2026-07-31, verified reachable on origin) removed it as stale post-2026-07-19-removal dead code; confirmed
      `VENUES_BY_ASSET_GROUP["tradfi"]` has no bare `POLYGON` venue key. (2) **`FRED`** — confirmed correctly placed,
      not a conflation instance: registered as a real venue 2026-07-29 with a real adapter
      (`market-tick-data-service/.../adapters/tradfi/fred_adapter.py`), and its capability entry
      (`{"yield_curve", "ohlcv_1d"}`) matches exactly what `FredAdapter.write_canonical_shard` emits (verified in the
      adapter source — never `macro_result`, which was the pre-fix bug). (3) The adjacent real bug this thread traces to
      — `corporate_action_confirmed`/`earnings_result` orphaned in the MTDS tick manifest (real writer =
      features-service's calendar module, not MTDS) — is also already fixed via 2 verified-reachable commits
      (`instruments-service@03f71c81` 2026-07-15 stopped the forward-seed, `market-tick-data-service@c24db4cf`
      2026-07-28 deleted 428,343 orphaned rows, 0 captured rows lost); `enumerate_expected_universe.py`'s "TRADFI IS
      DELIBERATELY NOT GATED" comment (line 711) still stands as confirmed operator-ratified design, not an unaddressed
      bug. **But (4) auditing "anywhere else" turned up one real miss**: `data_availability.py`'s
      `VENUE_DATA_AVAILABILITY["POLYGON"]` entry (a sibling registry in the same file family, NOT touched by `e34afc1d`)
      is still present and, unlike the already-cleaned capability dict, is NOT dead code —
      `unified-trading-pm/scripts/openapi/generate_ui_reference_data.py`'s `extract_venue_data_availability()` iterates
      it unconditionally into the generated `ui-reference-data.json`, so it currently surfaces "POLYGON" as a live
      TradFi provider. The established removal pattern
      (`tradfi_unreachable_databento_data_types_..._2026_07_15.md:270-272`, proven on the
      `YAHOO_FINANCE`/`unified-api-contracts@fec3f110` cleanup) names this exact file as one of 5 venue-shaped
      registries that must be swept together; only this one was missed for POLYGON. Filed as a follow-up per this todo's
      own instruction (audit-only, not fix-inline):
      `plans/active/issues/uac_venue_data_availability_stale_polygon_entry_2026_08_02.md`. **Also surfaced (not
      re-filed, already tracked)**: `tradfi_adapter_dead_code_fallback_audit_2026_07_25.md` Finding I-2 (open
      `[OPERATOR] P1`, filed 2026-07-31) found instruments-service's actual `massive.py` Polygon.io adapter is still
      live/tested/fully-wired, contradicting the codex/CLAUDE.md "removed 2026-07-19" claim — corroborates that the
      Polygon.io removal was executed inconsistently across repos/registries, the same root cause as (4). — verified by
      data_engineering (instruments_satellite_ao_dispatch_batch1-004) 2026-08-02.
- [x] ✅ [CODE] P1. **Widen the writer-fix scope to Solana DeFi + CURVE-OPTIMISM** — the blank-`instrument_type` bug
      found on DERIBIT (writer emitting one blended row per venue-day instead of splitting by instrument_type) also hits
      `DRIFT-SOLANA`, `KAMINO-SOLANA`, `MARGINFI-SOLANA`, `MARINADE-SOLANA`, `ORCA-SOLANA`, `RAYDIUM-SOLANA`,
      `SOLEND-SOLANA`, and `CURVE-OPTIMISM` — all have real captured dates but zero `instrument_types` breakdown. Apply
      the SAME already-implemented, already-proven fix pattern (split the manifest row by instrument_type instead of
      writing one blended row per venue-day) to these 8 named venues — not a new design, a mechanical
      repeat-application. Repo: instruments-service or market-tick-data-service (wherever the DERIBIT fix itself
      landed). Source: `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` ("Widen the writer-fix
      scope to Solana DeFi + CURVE-OPTIMISM..."). Done when: all 8 named venues show a genuine per-instrument_type
      breakdown (no longer blended/blank) using the same fix pattern as DERIBIT, verified against real captured data for
      each. — **read-only, no commit (no code changed)** — audited and found this premise stale, same class of finding
      as this plan's todo 1 (3/5 CeFi venues had no bug either): `_split_by_instrument_type`
      (`instruments-service/instruments_service/engine/orchestrator/writers.py:131`) is already venue-agnostic — it is
      applied unconditionally to EVERY venue passing through `_write_venue` with a manifest, cefi/tradfi/defi alike
      (`_cat = "defi" if manifest_chain else ...` at `writers.py:286`), so no per-venue "widen" was ever needed in the
      writer itself. Verified against BOTH the raw manifest index and the live production API for all 8 named venues: 1.
      **Raw manifest** — downloaded
      `gs://instruments-store-defi-prd-central-element-323112/_index/availability_index.parquet` (135,829 rows) and
      computed the `instrument_type` distribution per venue among `capture_status=captured` rows (DeFi manifest rows are
      keyed `venue=PROTOCOL` + `chain=CHAIN`, per `_canonical_manifest_venue_chain` — so `DRIFT-SOLANA` → `venue=DRIFT`,
      etc.). Every one of the 8 already carries a clean, fully-accounted per-type split with **zero blank rows among
      genuinely captured data**: DRIFT (PERPETUAL 1,351 / SPOT_PAIR 1,351), KAMINO (POOL 1,278 / SOLANA_VAULT 9),
      MARGINFI (A_TOKEN 16 / DEBT_TOKEN 16), MARINADE (STAKING 1,822), ORCA (POOL 936 / SOLANA_AMM_POOL 9), RAYDIUM
      (POOL 2,348 / SOLANA_AMM_POOL 9), SOLEND (A_TOKEN 16 / DEBT_TOKEN 16), CURVE/OPTIMISM (POOL 1,657, real captured
      data since its 2022-01-13 mainnet launch per UAC `venue_launch_dates.py`). CURVE/OPTIMISM's only 724 blank rows
      are `row_count=0` phantom captures dated 2020-01-20→2022-01-12 — entirely BEFORE the venue's mainnet launch, so
      there is no real (non-zero) data to split; a pre-launch phantom-zero-row issue, unrelated to the
      instrument_type-split bug this todo targets, not separately filed since it doesn't change this todo's verdict. 2.
      **Live production API** —
      `GET /api/data-status/manifest?service=instruments-service&asset_group=DEFI&start_date=2026-06-27&end_date=2026-07-27&secondary_axis=instrument_type`
      against `https://uts-shared-deployment-api-cldtjniqvq-an.a.run.app`, HTTP 200, confirms the breakdown actually
      surfaces end-to-end (not just present in the raw index): `venues.CURVE.instrument_types = [POOL]` (96.77%
      completion), `DRIFT = [PERPETUAL, SPOT_PAIR]` (64.52%), `KAMINO = [POOL, SOLANA_VAULT]` (96.77%),
      `MARGINFI = [A_TOKEN, DEBT_TOKEN]` (58.06%), `MARINADE = [STAKING]` (96.77%),
      `ORCA = [POOL,        SOLANA_AMM_POOL]` (96.77%), `RAYDIUM = [POOL, SOLANA_AMM_POOL]` (96.77%),
      `SOLEND = [A_TOKEN, DEBT_TOKEN]` (58.06%) — none blended/blank. **Secondary observation (not a new finding, no fix
      needed)**: the API also carries 3 literal `<PROTOCOL>-SOLANA` glued-name venue keys (`MARGINFI-SOLANA`,
      `SOLEND-SOLANA`, `JITORESTAKING-SOLANA`) at 0.0% completion with `instrument_types=None` — traced to 173
      raw-manifest rows each where `venue` was stamped as the glued literal string with `chain=None`, but every one of
      those rows is `capture_status=empty_confirmed`/`row_count=0` (honest zero-row placeholders, not `captured` data),
      so the blank `instrument_type` on them is CORRECT per the honest-absence contract — not an instance of this todo's
      bug class, so not separately filed. **Verdict: the registry-derived assumption that these 8 venues inherited
      DERIBIT's blank-collapse bug does not hold in the real data — the writer fix already covers them, going all the
      way back to each venue's own capture history.**

## Conflict-check note (Solana DeFi widen item)

Also confirmed via a broader grep across the corpus that this item is not independently claimed elsewhere: 3
consolidated-closeout docs (`cefi_consolidated_closeout_aggregated_sources_2026_07_24.md:260`,
`defi_consolidated_closeout_aggregated_sources_2026_07_24.md:253`, `tradfi_consolidated_closeout_2026_07_18.md:479`)
carry it as a non-ingestable bold digest citation (`- **[CODE] P1.** ...`, no `- [ ]` brackets — per `task_template.md`
finding H, a digest is not a dispatch claim), and `instruments_completion_tracker_2026_07_06.md`'s own Progress Log
narrates the same finding but explicitly defers to this doc as the one place it's actually tracked. No competing
checkbox found anywhere.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **data_engineering 2026-08-02 (instruments_satellite_ao_dispatch_batch1-004)**: closed todo 4 (TradFi POLYGON/FRED
  conflation audit). Verdict + full evidence trail on the flipped checkbox above; one gap found and filed as
  `plans/active/issues/uac_venue_data_availability_stale_polygon_entry_2026_08_02.md`. All 5 todos in this batch are now
  genuinely `[x]`. **Note — this plan's gated finalize twin
  (`instruments_satellite_ao_dispatch_batch1_finalize_2026_07_27.md`) already archived itself 2026-07-29/30 claiming all
  5 were done + this parent was archived — BOTH claims were false at the time (this todo 4 was still open, and this
  parent plan was never actually moved to archive/, which is why it was still live and dispatchable today). See
  `plans/active/issues/instruments_satellite_batch1_finalize_false_completion_claim_2026_08_02.md` for the full finding
  — this plan's real archival + the source doc's real reconciliation are tracked there, not here.
