---
doc_type: issue
title: "Empty re-probe disagreements — today's new empties may be C1 bugs (2026_08_18)"
created: 2026-08-18
context_scope: [/codex/05-infrastructure/data-pipeline-alerts.md, /codex/02-data/honest-absence-downstream-handling.md, /codex/02-data/tradfi-databento-sourcing-ssot.md]
parent_epic: observability_master
assigned_vm: planning
source:
  - reprobe_new_empty_confirmed.py
  - data_pipeline_hardening_self_monitoring_2026_06_22.md
locked_by:
summary: "The daily empty re-probe found cells that became empty_confirmed+SOURCE_RETURNED_ZERO today where the UAC coverage oracle SHOULD_HAVE_DATA (or a wired re-fetch returned rows), plus ambiguous ..."
status: resolved # corrected 2026-08-19 -- sole todo [x], diagnosed as duplicate of already-tracked P0 blocker
  # tradfi_databento_account_billing_suspended_2026_08_09.md, no code fix applicable
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [data-pipeline, daily-audit, empty-reprobe-disagreement-all]
related: []
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-19
resolved_by: interactive session 2026-08-19 -- diagnosed as duplicate of tracked P0 billing blocker, no code fix applicable
---

> **📦 ARCHIVED 2026-08-22 (archival pass 2)** — `locked_by: live-defi-rollout` placeholder cleared (corpus-wide
> fix, `scripts/plans/clear_locked_by_placeholder_2026_08_12.py --apply`); 0 open todos, `status: resolved`.
> Kept as a historical daily-monitor record.
# Empty re-probe disagreements — today's new empties may be C1 bugs (2026_08_18)

> Auto-filed by the daily data-pipeline audit `reprobe_new_empty_confirmed.py` (Wave 4b, Phase 5
> scripted→LLM escalation hop). A deterministic candidate list was non-empty — the
> verdicts below need a worker's judgment (real gap vs code bug, straggler
> vs intentional new venue). See `/codex/05-infrastructure/data-pipeline-alerts.md`.

## What I found

The daily empty re-probe found cells that became empty_confirmed+SOURCE_RETURNED_ZERO today where the UAC coverage oracle SHOULD_HAVE_DATA (or a wired re-fetch returned rows), plus ambiguous cells. AGs: cefi, defi, prediction, sports, tradfi.

Candidate list(s) (deterministic, machine-written):

- `/app/unified-trading-pm/plans/audit/results/empty_reprobe_tradfi_2026_08_18.csv`

## Why it matters

This is the operator's #1 failure class (C1): a real-empty misclassified as honest-absence. An ORACLE_EXPECTS_DATA / REPROBE_RETURNED_ROWS verdict means the data exists but we recorded empty — a code bug, not a true gap. AMBIGUOUS verdicts need judgment (oracle silent + no re-fetch hook).

## Recommended decision

For each disagreement: trace the adapter path that recorded the empty and route it to record_failed (thread fetch_evidence per Phase 1). For ambiguous: decide real-gap vs new-venue, extend the oracle. Per data_pipeline_hardening_self_monitoring_2026_06_22.md Phase 1/5.

Cold-start context: read `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
in full + `/codex/05-infrastructure/data-pipeline-alerts.md` + the candidate CSV(s)
above before acting.

## Todos

- [x] ✅ [CODE] P1. Empty re-probe disagreements — today's new empties may be C1 bugs (2026_08_18) — diagnose + fix the root cause (misclassified-empty vs real gap, not-v9 schema row, or oracle-expects-but-empty divergence) in `market-tick-data-service`. Read `SUB_AGENT_MANDATORY_RULES.md` + the data-pipeline codex SSOT + the candidate CSV(s) above first (source `reprobe_new_empty_confirmed.py`). — diagnosed, no code fix applicable (see Progress Log)

## Progress Log

- **2026-08-19**: Diagnosed the single tradfi candidate — `(CME, trades, day=2026-08-18)`, verdict
  `ORACLE_EXPECTS_DATA` (`oracle SHOULD_HAVE_DATA (None) but cell is empty_confirmed`). Direct read of the live
  tradfi `_index/availability_index.parquet` (UTL `download_bytes`, not gcloud/gsutil) confirmed 4 rows —
  `CME:FUTURES:{NQ,CL,GC,ES}`, `capture_status=empty_confirmed`, `error_reason=SOURCE_RETURNED_ZERO`,
  `pipeline_mode=live_databento`, `attempted_at=2026-08-18T23:59:01Z`. Ruled out yesterday's already-fixed
  delivery-lag classification gap (`empty_reprobe_disagreement_all_2026_08_17.md`,
  `market-tick-data-service@bf9fe5c4cc` widened `_TRADFI_DATABENTO_DELIVERY_LAG_VENUES` to include CME — that fix is
  live on `origin/live-defi-rollout` and is correct for the batch Tier-3 sentinel path it targets, but this cell's
  write comes from a DIFFERENT code path: the live WS producer's zero-tick-window handler
  (`market_tick_data_service/live/websocket_runner.py::_record_empty_window`), which has no delivery-lag concept at
  all (it always routes a 0-tick window to `record_zero_rows(SOURCE_RETURNED_ZERO)` unless
  `_in_connectivity_gap()`). A broader manifest scan (`groupby(["date","capture_status"])` on
  `venue=CME, data_type=trades`) showed real `captured` rows on 2026-08-09..08-11 then **100%
  `empty_confirmed`/`SOURCE_RETURNED_ZERO` on every date 2026-08-12 through 2026-08-19 (today)** for the live
  `mtds-live-tradfi-cme-trades-20260809-163443` VM (`pipeline_mode=live_databento`) — this is NOT a classification
  bug, it is a genuine multi-day live-capture outage. **Root cause: already tracked** —
  `/plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md` (P0, `status: blocked`,
  `assigned_vm: NA`, operator-gated) independently confirmed the IDENTICAL finding on the SAME VM, reading the SAME
  per-VM manifest shard, in a session dated the SAME day as this candidate's `day` (2026-08-18): "captured cleanly
  through 08-11, dead from 08-12 onward... no new mechanism, no code fix possible... the feed is dead on the vendor
  side per every prior diagnosis in this doc; a restart would not fix anything." This todo's candidate is a
  duplicate discovery of that already-diagnosed, already-`BLOCKED-OPERATOR-DECISION` outage (unpaid Databento
  invoice) — not a new C1 misclassified-empty bug, and per that doc's own explicit conclusion there is no code fix
  to ship for it. Resolving this todo by cross-reference rather than re-diagnosing; no code changed (mirrors the
  established precedent in
  `/plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_20260816_220209_databento_cme_billing_rootcause_2026_08_17.md`,
  which reached the same "not a code bug, do not relaunch" conclusion for a sibling CME/Databento symptom).
