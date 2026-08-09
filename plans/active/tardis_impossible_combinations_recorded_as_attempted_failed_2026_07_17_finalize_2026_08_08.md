---
doc_type: plan
title: Tardis impossible-combinations vendor-catalog gate + apply-purge — finalize (reconcile + archive)
summary: >-
  Gated closeout for issues/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md — machine-held via
  depends_on + gate_on_depends: true until that doc's 2 remaining todos (P0 vendor-catalog request gate; P1 `--apply`
  reclass of historical 400-coded attempted_failed rows) are done. Re-verifies both landed with real evidence, then
  archives the source doc.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service, unified-api-contracts, instruments-service]
scope: [engineer]
tags: [cefi, tardis, honest-coverage, denominator, close-out, archival]
related:
  [
    /plans/active/issues/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17]
gate_on_depends: true
source: >-
  Per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize
  plan. Authored as part of na-eligibility-audit round7 RECLASSIFY sweep (cefi tranche, batch 3), 2026-08-08.
assigned_role: data_engineering
effort: medium
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/issues/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/tardis_csv_transport.py,
    market-tick-data-service/scripts/reclass_cefi_tardis_impossible_combinations_400_2026_07_27.py,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Tardis impossible-combinations vendor-catalog gate + apply-purge — finalize

> **Machine-gated on `tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue any todo below until both remaining todos in that doc
> (`[CODE] P0` vendor-catalog gate, `[DATA] P1` `--apply` purge) are `done`. `sequential: true` because todo 3
> (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Re-verify the vendor-catalog request gate (P0) landed.** Confirm a real commit (repo@sha) wires the
      per-venue Tardis catalog cache (`GET /v1/exchanges/<venue>`, refreshed daily) into the shard-enumeration/
      request-generation path so a (symbol, data_type, date) combination failing the 3-condition gate (symbol in catalog
      AND data_type in symbol.dataTypes AND availableSince<=date<=availableTo) is never requested and never recorded as
      any capture_status. Repo: market-tick-data-service. **Done when**: the source doc's `[CODE] P0` checkbox is `[x]`
      with a verified repo@sha citation.
- [ ] [REVIEW] P1. **Re-verify the `--apply` purge (P1) ran.** Confirm the sizing script
      (`reclass_cefi_tardis_impossible_combinations_400_2026_07_27.py`) was re-run fresh (counts drift per its own note)
      immediately before `--apply`, the reversibility check (`softDeletePolicy.retentionDurationSeconds` ≥604800s) was
      re-confirmed same-run, and the manifest row-count delta (attempted_failed → empty_confirmed,
      `error_reason: EXPECTED_TARDIS_STRUCTURAL_ABSENCE_400`) actually landed against the live
      `market-data-tick-cefi-prd` manifest. Repo: market-tick-data-service. **Done when**: the source doc's `[DATA] P1`
      checkbox is `[x]` with a verified repo@sha + before/after row-count citation.
- [ ] [DOC] P2. **Archive
      `plans/active/issues/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md`** via the standard
      6-step ritual (per CLAUDE.md's plan-archival rule): confirm no Deferred items remain untracked → add the archive
      banner → run the codex-alignment check → grep the corpus for every referrer of
      `tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17` and fix each path to point at the
      archived location → clear `locked_by` (already empty, confirm). **Done when**: the doc is moved to
      `plans/archive/2026_08/`, every corpus referrer resolves to the new path, and this finalize doc itself gets
      archived alongside it in the same commit.

## Progress Log

- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
