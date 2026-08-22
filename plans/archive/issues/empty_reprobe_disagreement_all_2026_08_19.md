---
doc_type: issue
title: "Empty re-probe disagreements — today's new empties may be C1 bugs (2026_08_19)"
created: 2026-08-19
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
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [manifest-hygiene, data-pipeline, honest-coverage, empty-reprobe]
related: [/plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md]
resolved_by: slot-16 2026-08-19 -- diagnosed as duplicate of tracked P0 billing blocker, no code fix applicable
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
---

> **📦 ARCHIVED 2026-08-22 (archival pass 2)** — `locked_by: live-defi-rollout` placeholder cleared (corpus-wide
> fix, `scripts/plans/clear_locked_by_placeholder_2026_08_12.py --apply`); 0 open todos, `status: resolved`.
> Kept as a historical daily-monitor record.
# Empty re-probe disagreements — today's new empties may be C1 bugs (2026_08_19)

> Auto-filed by the daily data-pipeline audit `reprobe_new_empty_confirmed.py` (Wave 4b, Phase 5
> scripted→LLM escalation hop). A deterministic candidate list was non-empty — the
> verdicts below need a worker's judgment (real gap vs code bug, straggler
> vs intentional new venue). See `/codex/05-infrastructure/data-pipeline-alerts.md`.

## What I found

The daily empty re-probe found cells that became empty_confirmed+SOURCE_RETURNED_ZERO today where the UAC coverage oracle SHOULD_HAVE_DATA (or a wired re-fetch returned rows), plus ambiguous cells. AGs: cefi, defi, prediction, sports, tradfi.

Candidate list(s) (deterministic, machine-written):

- `/app/unified-trading-pm/plans/audit/results/empty_reprobe_tradfi_2026_08_19.csv`

## Why it matters

This is the operator's #1 failure class (C1): a real-empty misclassified as honest-absence. An ORACLE_EXPECTS_DATA / REPROBE_RETURNED_ROWS verdict means the data exists but we recorded empty — a code bug, not a true gap. AMBIGUOUS verdicts need judgment (oracle silent + no re-fetch hook).

## Recommended decision

For each disagreement: trace the adapter path that recorded the empty and route it to record_failed (thread fetch_evidence per Phase 1). For ambiguous: decide real-gap vs new-venue, extend the oracle. Per data_pipeline_hardening_self_monitoring_2026_06_22.md Phase 1/5.

Cold-start context: read `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
in full + `/codex/05-infrastructure/data-pipeline-alerts.md` + the candidate CSV(s)
above before acting.

## Todos

- [x] ✅ [CODE] P1. Empty re-probe disagreements — today's new empties may be C1 bugs (2026_08_19) — diagnose + fix the root cause (misclassified-empty vs real gap, not-v9 schema row, or oracle-expects-but-empty divergence) in `market-tick-data-service`. Read `SUB_AGENT_MANDATORY_RULES.md` + the data-pipeline codex SSOT + the candidate CSV(s) above first (source `reprobe_new_empty_confirmed.py`). — diagnosed, no code fix applicable (see Progress Log)

## Progress Log

- **2026-08-19 (slot-16)**: Diagnosed the single tradfi candidate — `(CME, trades, day=2026-08-19)`, verdict
  `ORACLE_EXPECTS_DATA` (`oracle SHOULD_HAVE_DATA (None) but cell is empty_confirmed`). Ruled out the two known
  code-bug classes first: (1) the delivery-lag Tier-3 sentinel classification gap
  (`market-tick-data-service@bf9fe5c4cc`, fixed 2026-08-17) already covers CME/CBOE and is live on
  `origin/live-defi-rollout`, but that fix targets the BATCH Tier-3 sentinel path (`sentinels.py::_emit_tier3_for_dt`),
  not this cell's actual writer; (2) direct read of the live tradfi `_index/availability_index.parquet` (UTL
  `read_manifest_index` with a pushed-down `venue='CME' AND data_type='trades'` filter, not a full-corpus walk —
  79,183 total CME/trades rows, 4 for day=2026-08-19) confirmed all 4 rows are `capture_status=empty_confirmed`,
  `error_reason=SOURCE_RETURNED_ZERO`, **`pipeline_mode=live_databento`**, written `2026-08-19T13:15-13:16Z` — the
  same live producer (`mtds-live-tradfi-cme-trades-20260809-163443`) and identical `pipeline_mode=live_databento`
  signature the 2026-08-18 sibling issue doc (`empty_reprobe_disagreement_all_2026_08_18.md`) already diagnosed for
  day=2026-08-18. **Root cause: already tracked** —
  `/plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md` (P0, `status: blocked`,
  `assigned_vm: NA`, operator-gated) — its own 2026-08-19 (slot 31) entry independently confirmed the SAME live
  producer still `RUNNING`/actively-attempting with CME trades last genuinely `captured` 7.5 days ago (staleness
  monotonically widening, zero recovery) — the same GLBX.MDP3-dataset-scoped Databento billing outage (unpaid
  invoice, `402 account_delinquent_invoice`), unresolved since 2026-08-12. This todo's candidate is a duplicate
  discovery of that already-diagnosed, already-`BLOCKED-OPERATOR-DECISION` outage — not a new C1 misclassified-empty
  bug, and per that doc's own explicit conclusion (7 independent corroborating sessions 2026-08-14 through
  2026-08-19) there is no code fix to ship for it. Resolving this todo by cross-reference rather than re-diagnosing
  or re-paging (the billing doc's open `[OPERATOR]` P0 "pay the invoice again" todo already covers the ask, and its
  same-day 2026-08-19 entry already corroborated the outage via an independent method — a redundant Progress Log
  entry there would add no new information); no code changed. Mirrors the established precedent in
  `empty_reprobe_disagreement_all_2026_08_18.md`.
