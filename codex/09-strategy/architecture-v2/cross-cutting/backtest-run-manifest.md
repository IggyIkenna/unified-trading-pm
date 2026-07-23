---
doc_type: codex-ssot
title: Backtest Run Manifest
summary:
  STUB — per-run metadata written alongside every backtest (archetype, param hash, date range, data versions,
  Sharpe/drawdown/calmar, run duration) as results.json + run_manifest.json per run_id; full spec pending strategy Phase
  3.
implementation_status: stub
status: draft
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [strategy, backtest, manifest, archetypes]
related:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/backtest-persistence-and-ranking.md,
    /codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md,
  ]
created: 2026-05-21
authoritative_for: []
referenced_by: [/codex/09-strategy/architecture-v2/cross-cutting/backtest-persistence-and-ranking.md]
owner:
last_reviewed:
code_refs:
type: strategy
---

# Backtest Run Manifest

> **STUB** — Reference: `plans/epics/defi_master.md`.

Metadata written alongside every backtest run: archetype, param hash, date range, data versions, Sharpe/drawdown/calmar,
run duration. Format: `results.json` + `run_manifest.json` per run_id. Full spec pending strategy Phase 3.
