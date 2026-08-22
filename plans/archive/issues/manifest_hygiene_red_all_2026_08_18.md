---
doc_type: issue
title: "Manifest hygiene RED — 4 AG(s) with findings (2026_08_18)"
created: 2026-08-18
context_scope: [/codex/02-data/availability-manifest-and-data-status.md, /codex/05-infrastructure/data-pipeline-alerts.md, /codex/02-data/four-surface-reconciliation-procedure.md]
parent_epic: observability_master
assigned_vm: planning
source:
  - manifest_hygiene_daily.py
  - data_pipeline_hardening_self_monitoring_2026_06_22.md
locked_by:
summary: "The daily manifest-hygiene-vs-GCS orchestrator found non-empty candidate lists for: cefi, defi, prediction, sports, tradfi. ..."
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [data-pipeline, daily-audit, manifest-hygiene-red-all]
related: [manifest_hygiene_red_all_2026_08_17]
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-19
resolved_by: market-tick-data-service@f67a7480b3 (docstring fix); root-cause fix work tracked on manifest_hygiene_red_all_2026_08_17's still-open todos
---

> **📦 ARCHIVED 2026-08-22 (archival pass 2)** — `locked_by: live-defi-rollout` placeholder cleared (corpus-wide
> fix, `scripts/plans/clear_locked_by_placeholder_2026_08_12.py --apply`); 0 open todos, `status: resolved`.
> Kept as a historical daily-monitor record.
# Manifest hygiene RED — 4 AG(s) with findings (2026_08_18)

> Auto-filed by the daily data-pipeline audit `manifest_hygiene_daily.py` (Wave 4b, Phase 5
> scripted→LLM escalation hop). A deterministic candidate list was non-empty — the
> verdicts below need a worker's judgment (real gap vs code bug, straggler
> vs intentional new venue). See `/codex/05-infrastructure/data-pipeline-alerts.md`.

## What I found

The daily manifest-hygiene-vs-GCS orchestrator found non-empty candidate lists for: cefi, defi, prediction, sports, tradfi. Finding-classes: schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk, phantom_captured_no_parquet, shard_4pillar_fail.

Candidate list(s) (deterministic, machine-written):

- `/app/unified-trading-pm/plans/audit/results/manifest_hygiene_cefi_2026_08_18.csv`
- `/app/unified-trading-pm/plans/audit/results/manifest_hygiene_tradfi_2026_08_18.csv`
- `/app/unified-trading-pm/plans/audit/results/manifest_hygiene_sports_2026_08_18.csv`
- `/app/unified-trading-pm/plans/audit/results/manifest_hygiene_prediction_2026_08_18.csv`

## Why it matters

Each class is a data-correctness signal: non-v9 rows are pre-canonicalisation stragglers; oracle-expects-but-empty is a candidate C1 misclassification (real gap vs code bug — needs judgment); non-canonical paths break selective reads; phantoms are captured cells with no parquet.

## Recommended decision

Triage each candidate CSV: confirm real gaps → backfill; confirm code bugs → fix the adapter/writer; confirm intentional new venues/spellings → extend the UAC oracle/canonical builders. Per data_pipeline_hardening_self_monitoring_2026_06_22.md Phase 3/5.

Cold-start context: read `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
in full + `/codex/05-infrastructure/data-pipeline-alerts.md` + the candidate CSV(s)
above before acting.

## Diagnosis (2026-08-19, slot-7) — DUPLICATE of 2026_08_17's already-open findings; one concrete fix landed, rest cross-referenced not re-diagnosed

Compared this doc's candidate CSVs against `manifest_hygiene_red_all_2026_08_17.md`'s (5 diagnosis rounds already
recorded there) before doing any fresh investigation, per CLAUDE.md findings-triage ("fits another plan → annotate
it, don't fix — collision risk") and the sub-agent CLAIM≤MEASUREMENT rule (don't re-derive what's already measured):

- **sports**: `DIVERGENT_EMPTY: 0` — clean, matches 08-17's "clean, no action needed" verdict. No action.
- **cefi** (58,362 DIVERGENT_EMPTY, sample venue=UPBIT/trades) and **tradfi** (8,477, sample venue=NYSE/ohlcv_1s):
  same magnitude and same sample shape as 08-17's cefi (58,362) / tradfi (8,468) findings, which 08-17 already
  determined need a VM-scale re-run of `detect_manifest_divergence.py` (local host OOMs on the manifest read
  alone) — NOT re-diagnosed here. Tracked by 08-17's still-open P2 todos ("Launch a VM to run
  `detect_manifest_divergence.py --asset-group {cefi,tradfi}`"); this doc does not duplicate those todos.
- **prediction** (463 DIVERGENT_EMPTY, sample venue=POLYMARKET/trades, dates 2026-08-15→17): matches the
  POLYMARKET raw-`trades` gap 08-17 slot-19 already ROOT-CAUSED (see 08-17's "Diagnosis update (2026-08-18,
  slot-19)") — instruments-service's POLYMARKET instrument-catalogue writer stopped emitting objects starting
  2026-08-10, still ongoing as of this audit's 2026-08-18 sample dates. NOT an MTDS/adapter bug (CF-11 signalling
  intact). Tracked by 08-17's still-open P1 todo scoped to `instruments-service`; not re-diagnosed or duplicated
  here.
- **Concrete fix shipped this session** (the one piece of NEW, not-yet-tracked work found while cross-checking):
  08-17's open P3 docstring-fix todo (`market-tick-data-service`) — landed as `market-tick-data-service@f67a7480b3`,
  flipped on the 08-17 doc. See that doc's Todos for the fix detail; not restated here to avoid drift between the
  two copies.

No new root-cause diagnosis needed for cefi/tradfi/prediction beyond what 08-17 already has — this todo closes as
a duplicate-with-cross-reference, per the daily audit's own recurring-refile design (it re-files the same
candidate list every day until the underlying VM-scale re-run / instruments-service trace actually lands).

## Todos

- [x] ✅ [CODE] P1. Manifest hygiene RED — 4 AG(s) with findings (2026_08_18) — 2026-08-19 slot-7. DUPLICATE of
      `manifest_hygiene_red_all_2026_08_17.md`'s already-open findings for cefi/tradfi/prediction (same magnitude,
      same sample shape); sports is clean (0). See "Diagnosis (2026-08-19, slot-7)" above for the cross-reference.
      Root-cause fix work for cefi/tradfi (VM-scale `detect_manifest_divergence.py` re-run) and prediction
      (instruments-service POLYMARKET catalogue trace) stays tracked on 08-17's still-open P1/P2 todos — not
      duplicated here. Concrete code fix landed this session: `market-tick-data-service@f67a7480b3` (docstring
      correction, flipped on 08-17's P3 todo).

## Progress Log

- **slot-7 2026-08-19**: cross-checked this doc's candidate CSVs against `manifest_hygiene_red_all_2026_08_17.md`
  (same magnitude/sample-shape for cefi/tradfi/prediction, sports clean) — closed as duplicate-with-cross-reference
  rather than re-diagnosing. Landed the one genuinely new, not-yet-tracked item found during the cross-check (a
  misleading docstring flagged as an open P3 on the 08-17 doc): `market-tick-data-service@f67a7480b3`, also fixed
  the same unscoped claim in `kalshi_adapter.py`'s copy (not named in the original todo, found while editing).
