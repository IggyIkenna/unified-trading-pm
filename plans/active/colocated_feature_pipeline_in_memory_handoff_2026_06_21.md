---
doc_type: plan
title:
  Colocated feature pipeline — in-memory DAG handoff, parquet consolidation, read-time pruning, basedpyright strictness
  restore
summary:
  "Land deferred colocated feature pipeline I/O efficiency items (in-memory DAG handoff, parquet consolidation, column
  pruning) and restore features-service basedpyright strictness."
status: active
nature: process
stage: [meta]
repos: [features-service]
scope: [engineer, admin]
tags: [features, pipeline, in-memory, parquet, basedpyright, efficiency, colocated]
related: [../epics/features_and_ml_master.md, ../archive/2026_06/features_calc_efficiency_and_correctness_2026_05_27.md]
created: "2026-06-21"
parent_epic: features_and_ml_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P3
estimate_class: design
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 3.0
assigned_role: data-pipeline-engineer
drift_direction: advance-code
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-06-21
supersedes:
superseded_by:
depends_on:
source:
---

# Colocated feature pipeline — in-memory handoff + I/O efficiency + basedpyright strictness restore

> **MIGRATED FROM:** `features_calc_efficiency_and_correctness_2026_05_27.md` (archived 2026-06-21). That plan shipped
> the feature-calc efficiency + correctness work; these four items were deferred there (1.3b/1.4/1.5b behind a "revisit
> after end-to-end" gate, and 1.7e behind an operator "dedicated session" gate) with placeholder/un-filed successors.
> Consolidated here so they have a real owning plan.

## Objective

Land the deferred colocated-feature-pipeline I/O efficiency items (in-memory DAG handoff, one-parquet-per-(day,fg,tf)
consolidation, read-time column pruning) **and** restore features-service basedpyright strictness (the `reportUnknown*`
severities were weakened to `"none"`, masking 574 errors).

## Todos

- [ ] [DESIGN] P3. **1.4 — feature dependency DAG handoff in-memory** — pass derived feature frames between calculators
      in-process instead of round-tripping through parquet, so a colocated feature run computes the dependency DAG once.
      Repo: features-service. **MIGRATED FROM:** `features_calc_efficiency_and_correctness` item 1.4.
- [ ] [REFACTOR] P3. **1.3b — one parquet per (day, feature_group, timeframe)** — consolidate the per-instrument parquet
      fan-out into a single file per (day,fg,tf) to cut object count + selective-read list cost. Repo: features-service.
      **MIGRATED FROM:** item 1.3b.
- [ ] [REFACTOR] P3. **1.5b — column pruning at the delta_one read** — push column selection down so a delta_one read
      materialises only the requested feature columns. Revisit after the end-to-end pipeline is green. Repo:
      features-service. **MIGRATED FROM:** item 1.5b.
- [ ] [CODE] P2. **1.7e — restore features-service basedpyright strictness (574 errors masked)** — the
      `reportUnknownMemberType` / `reportUnknownVariableType` / `reportUnknownArgumentType` (+ 6 more) severities were
      set to `"none"` in `features-service/pyrightconfig.json`/`pyproject.toml`, hiding ~574 errors. Restore them to
      `error` (or a ratcheted budget) and burn down the errors in a dedicated session. NOTE: distinct from
      `codex_violations_ratchet_to_five` (that gate is the CODEX_MAX_VIOLATIONS lint budget + file-size splits, NOT the
      basedpyright-severity weakening). Repo: features-service. **MIGRATED FROM:** item 1.7e (no prior home).

## Success criteria

- In-memory DAG handoff + parquet consolidation + read-time pruning land with features-service `quality-gates.sh` green
  and a measured I/O reduction (object count / read bytes) on a sample (day, fg, tf).
- features-service basedpyright `reportUnknown*` severities back to `error` (or a downward-only ratchet) with the 574
  errors burned down; no new suppressions added.

## Temporary states + their canonical follow-up plans

- (none — this IS the canonical follow-up for the archived `features_calc_efficiency_and_correctness` deferrals.)
