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
    /plans/active/instruments_satellite_ao_dispatch_batch1_finalize_2026_07_27.md,
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

- [ ] [DATA] P1. **Raw-parquet spot-check the 5 additional CeFi venues** flagged by the pre-audit's registry read as
      likely hitting the same multi-type blank-collapse: `OKX-FUTURES`, bare `BYBIT`, `BINANCE-FUTURES`,
      `KRAKEN-FUTURES`, `BINANCE-DELIVERY` — same method already used on DERIBIT/ASTER (download
      `availability_index.parquet`, check `instrument_type` distribution). Repo: instruments-service. Source:
      `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` ("Raw-parquet spot-check the 5 additional
      CeFi venues..."). Done when: each of the 5 venues has a recorded pass/fail against the same coverage class
      DERIBIT/ASTER were checked against, with the raw-parquet read cited.
- [ ] [DATA] P1. **Add `missing_dates`/`dates_found_list` to the per-instrument_type and per-underlying breakdown
      entries** (`deployment-api/deployment_api/services/data_status/breakdowns_core.py` —
      `_build_instrument_type_breakdown` ~405-409, `_build_underlying_breakdown` ~508-512; mirror
      `_build_data_type_breakdown`'s entry shape ~629-643, which already carries this). Needs a matching
      `deployment-ui/src/components/DataStatusTab.tsx` render tweak and the `TurboInstrumentTypeStatus`/
      `TurboUnderlyingStatus` types in `api/client.ts:1156-1169` to carry the new fields (mirroring
      `TurboDataTypeStatus` at `client.ts:984-999`). Repo: deployment-api, deployment-ui. Source:
      `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` ("Add `missing_dates`/`dates_found_list`
      to the per-instrument_type and per-underlying breakdown entries..."). Done when: both breakdown entry types carry
      both fields in the mirrored shape, the UI renders them, with a passing test.
- [ ] [DATA] P1. **Pull the real per-instrument_type breakdown for DERIBIT live** (the comparison built for the source
      doc used illustrative numbers pending this) and confirm whether OPTION coverage is actually healthy or is itself a
      live gap once visible. Repo: market-tick-data-service. Source:
      `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` ("Pull the real per-instrument_type
      breakdown for DERIBIT live..."). Done when: a real, current per-instrument_type breakdown for DERIBIT live is
      recorded (not inferred), cited against the live source data, with an explicit OPTION-coverage verdict.
- [ ] [VERIFY] P2. **Audit whether the same MTDS/reference-data conflation risk exists anywhere else** — e.g. the TradFi
      `POLYGON`/`FRED` reference-data-in-the-wrong-registry smell noted at `market_data_categories.py:1279-1286` (not
      yet confirmed live). A precisely-scoped "does X match Y" check, not a design call. Repo: instruments-service.
      Source: `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` ("Audit whether the same
      MTDS/reference-data conflation risk exists anywhere else..."). Done when: a definitive yes/no is recorded for
      TradFi POLYGON/FRED with the checked evidence cited; if yes, file a follow-up todo/issue doc rather than fixing
      inline (this todo is the audit, not the fix).
- [ ] [CODE] P1. **Widen the writer-fix scope to Solana DeFi + CURVE-OPTIMISM** — the blank-`instrument_type` bug found
      on DERIBIT (writer emitting one blended row per venue-day instead of splitting by instrument_type) also hits
      `DRIFT-SOLANA`, `KAMINO-SOLANA`, `MARGINFI-SOLANA`, `MARINADE-SOLANA`, `ORCA-SOLANA`, `RAYDIUM-SOLANA`,
      `SOLEND-SOLANA`, and `CURVE-OPTIMISM` — all have real captured dates but zero `instrument_types` breakdown. Apply
      the SAME already-implemented, already-proven fix pattern (split the manifest row by instrument_type instead of
      writing one blended row per venue-day) to these 8 named venues — not a new design, a mechanical
      repeat-application. Repo: instruments-service or market-tick-data-service (wherever the DERIBIT fix itself
      landed). Source: `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` ("Widen the writer-fix
      scope to Solana DeFi + CURVE-OPTIMISM..."). Done when: all 8 named venues show a genuine per-instrument_type
      breakdown (no longer blended/blank) using the same fix pattern as DERIBIT, verified against real captured data for
      each.

## Conflict-check note (Solana DeFi widen item)

Also confirmed via a broader grep across the corpus that this item is not independently claimed elsewhere: 3
consolidated-closeout docs (`cefi_consolidated_closeout_aggregated_sources_2026_07_24.md:260`,
`defi_consolidated_closeout_aggregated_sources_2026_07_24.md:253`, `tradfi_consolidated_closeout_2026_07_18.md:479`)
carry it as a non-ingestable bold digest citation (`- **[CODE] P1.** ...`, no `- [ ]` brackets — per `task_template.md`
finding H, a digest is not a dispatch claim), and `instruments_completion_tracker_2026_07_06.md`'s own Progress Log
narrates the same finding but explicitly defers to this doc as the one place it's actually tracked. No competing
checkbox found anywhere.
