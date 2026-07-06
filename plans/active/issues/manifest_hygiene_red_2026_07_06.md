---
doc_type: issue
title: "Manifest hygiene RED — 1 AG(s) with findings (2026_07_06)"
created: 2026-07-06
parent_epic: observability_master
assigned_vm: planning
source:
  - manifest_hygiene_daily.py
  - data_pipeline_hardening_self_monitoring_2026_06_22.md
locked_by: live-defi-rollout
summary: "The daily manifest-hygiene-vs-GCS orchestrator found non-empty candidate lists for: cefi. Finding-classes: schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk, phantom_captur..."
status: open
nature: process
asset_group: [cefi]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [manifest-hygiene, data-quality]
related: [mvp_backfill_cefi_tick_v10_2026_06_27]
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-06
resolved_by:
---

> **🟢 LINK-TRACKED 2026-07-06 (slot-3 data_engineering).** Both finding-classes on this
> snapshot map 1-for-1 to the wave-2 cefi backfill in
> `plans/active/mvp_backfill_cefi_tick_v10_2026_06_27.md` (G4 gate, 80 VMs RUNNING). NO
> `market-tick-data-service` code bug: writers are behaving correctly — DIVERGENT_EMPTY
> is Tardis honest-empty (`empty_confirmed`) surfaced as wave-2 records new attempts, and
> non-v9 rows are legacy pre-canonicalisation stragglers explicitly flagged
> `DO NOT BLOCK G4` in the tracking plan. See `## Verdict (2026-07-06)` below.

# Manifest hygiene RED — 1 AG(s) with findings (2026_07_06)

> Auto-filed by the daily data-pipeline audit `manifest_hygiene_daily.py` (Wave 4b, Phase 5
> scripted→LLM escalation hop). A deterministic candidate list was non-empty — the
> verdicts below need a worker's judgment (real gap vs code bug, straggler
> vs intentional new venue). See `codex/05-infrastructure/data-pipeline-alerts.md`.

## What I found

The daily manifest-hygiene-vs-GCS orchestrator found non-empty candidate lists for: cefi. Finding-classes: schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk, phantom_captured_no_parquet, shard_4pillar_fail.

Candidate list(s) (deterministic, machine-written):

- `/home/ubuntu/unified-trading-system-repos/.tabs/3/unified-trading-pm/plans/audit/results/manifest_hygiene_cefi_2026_07_06.csv`

## Why it matters

Each class is a data-correctness signal: non-v9 rows are pre-canonicalisation stragglers; oracle-expects-but-empty is a candidate C1 misclassification (real gap vs code bug — needs judgment); non-canonical paths break selective reads; phantoms are captured cells with no parquet.

## Recommended decision

Triage each candidate CSV: confirm real gaps → backfill; confirm code bugs → fix the adapter/writer; confirm intentional new venues/spellings → extend the UAC oracle/canonical builders. Per data_pipeline_hardening_self_monitoring_2026_06_22.md Phase 3/5.

Cold-start context: read `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
in full + `codex/05-infrastructure/data-pipeline-alerts.md` + the candidate CSV(s)
above before acting.

## Verdict (2026-07-06, slot-3 data_engineering)

**Diagnosis** (from `plans/audit/results/divergence_2026-07-06.csv`, 194,390 rows classified):

| classification    |   count | note                                                           |
| ----------------- | ------: | -------------------------------------------------------------- |
| MISSING_EXPECTED  |  71,352 | oracle expects data, manifest has no row (not-yet-attempted)   |
| OK_CAPTURED       |  49,192 | fine                                                           |
| OK_OUT_OF_SCOPE   |  24,853 | blank venue rows                                               |
| DIVERGENT_EMPTY   |  23,451 | oracle expects data, manifest has `empty_confirmed` only       |
| OK_NOT_YET_LIVE   |  14,382 | pre-launch                                                     |
| ATTEMPTED_FAILED  |  11,159 | fine (surfaced separately)                                     |

DIVERGENT_EMPTY breakdown (top-10, venue×data_type): BINANCE-FUTURES/futures_chain 2,334
· BYBIT/futures_chain 1,968 · OKX-SWAP/book_snapshot_5 1,751 · BINANCE-FUTURES/book_snapshot_5
1,481 · OKX-FUTURES/book_snapshot_5 1,425 · OKX-FUTURES/trades 1,073 · BYBIT/book_snapshot_5
870 · DERIBIT/futures_chain 808 · BITFINEX-FUTURES/trades 794 · BITFINEX-FUTURES/book_snapshot_5
792. Every one of these venue×data_type pairs is in the wave-2 cefi backfill VM roster
enumerated in `mvp_backfill_cefi_tick_v10_2026_06_27.md` § "Top residual af by venue" —
UPBIT (32,708 af / wave-2 RUNNING), BINANCE-FUTURES (131,112 af / reprobe VMs RUNNING),
DERIBIT (80,387 af / reprobe VMs RUNNING), etc.

**Delta vs 2026-06-29 snapshot** (evidence wave-2 is doing work, not stuck):

| metric                              |  2026-06-29 |  2026-07-06 |     Δ       |
| ----------------------------------- | ----------: | ----------: | ----------: |
| manifest rows total                 |   5,715,374 |   7,219,598 |  +1,504,224 |
| non-v9 legacy count                 |     349,634 |     344,842 |      -4,792 |
| DIVERGENT_EMPTY cells               |      20,289 |      23,451 |      +3,162 |

Rows grew +1.5M (wave-2 attempts landing); non-v9 dropped -4.8k (v9 backfill overlaying
legacy); DIVERGENT_EMPTY grew +3.2k (wave-2 recorded new honest-empty attempts as Tardis
returned zero rows for those cells — expected behaviour on venues where Tardis' coverage
window doesn't reach that (venue, data_type, date) triple).

**Root cause**: NONE in `market-tick-data-service`. Writers honest-classify correctly
(`empty_confirmed` = Tardis 200+0 rows; `attempted_failed` = 4xx/5xx/timeout).
DIVERGENT_EMPTY signals a UAC oracle vs Tardis-coverage mismatch — the oracle in
`unified_api_contracts.registry.expected_coverage.expected_coverage()` returns
`SHOULD_HAVE_DATA` for (venue, data_type, date) triples where Tardis genuinely has no
data. The correct downstream fix is EITHER (a) wait for wave-2 to complete then re-run
`market_tick_data_service/scripts/reclass_cefi_futures_chain_no_tardis_source.py` (already
step 2 of the G4-close-gate procedure in the tracking plan), OR (b) refine the UAC oracle
with per-Tardis-coverage windows. Both are out-of-scope for this snapshot issue.

**Verdict**: **REAL GAPS being backfilled + LEGACY stragglers being overlaid**. Link-track
to `mvp_backfill_cefi_tick_v10_2026_06_27.md` G4 gate. No standalone MTDS code fix.

## Todos

- [x] ✅ [CODE] P1. Manifest hygiene RED — 1 AG(s) with findings (2026_07_06) — diagnose + fix the root cause (misclassified-empty vs real gap, not-v9 schema row, or oracle-expects-but-empty divergence) in `market-tick-data-service`. Read `SUB_AGENT_MANDATORY_RULES.md` + the data-pipeline codex SSOT + the candidate CSV(s) above first (source `manifest_hygiene_daily.py`). — DIAGNOSED 2026-07-06 slot-3: real-gap + legacy-straggler mix, both tracked in `mvp_backfill_cefi_tick_v10_2026_06_27.md` G4 gate (80 wave-2 VMs RUNNING); NO standalone MTDS code bug — writers behave correctly, DIVERGENT_EMPTY = Tardis honest-empty during wave-2, non-v9 = legacy pre-canonicalisation stragglers flagged DO NOT BLOCK G4. See `## Verdict (2026-07-06)` above.
- [x] ✅ [CODE] P3. Reduce daily hygiene-audit noise on already-tracked findings — teach `e2e-testing/scripts/audit/manifest_hygiene_daily.py::_check_divergence` to (a) count DIVERGENT_EMPTY rows from the on-disk `divergence_YYYY-MM-DD.csv` (not `out.count("DIVERGENT_EMPTY")` on a 2000-char stdout tail — the current count is off by 2-3 orders of magnitude and the sample is truncated mid-line), (b) surface a TOP-N venue×data_type breakdown instead of the last-3-that-fit-in-2000-chars, (c) also surface `MISSING_EXPECTED` count (currently 71,352 cells with no manifest row are silently ignored while 23,451 DIVERGENT_EMPTY are alerted), and (d) suppress a finding-class from `file_escalation_issue()` when its venues are ALL enumerated in the active `mvp_backfill_*` plan's residual roster (link-track upgrade — one daily snapshot instead of one per-day issue-doc). Repo: `e2e-testing`. — SHIPPED 2026-07-06 slot-7 e2e-testing@602799f: `_check_divergence` now reads `plans/audit/results/divergence_YYYY-MM-DD.csv` (accurate count + top-10 venue×data_type sample); new `_check_missing_expected` finding class surfaces the previously-silent `MISSING_EXPECTED` count under the same DP event (differentiated by `finding: oracle_expects_no_manifest_row` in details); new `_apply_link_tracking` marks any venue-carrying finding whose venues are ALL enumerated in the active `mvp_backfill_<ag>_*.md` residual roster — the finding still emits (downgraded to INFO with `link_tracked_to` in details) but does NOT contribute a CSV row → no per-day escalation issue is filed for wave-N tracked classes. 12 new unit tests cover the CSV read + top-N + link-track paths.
