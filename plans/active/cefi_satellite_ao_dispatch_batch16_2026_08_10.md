---
doc_type: plan
title: CeFi satellite AO batch 16 — deployment-ui Barchart label spot-check
summary: >-
  Sixteenth AO-dispatch batch for cefi. Single-item extraction from
  `issues/deployment_ui_barchart_label_spotcheck_2026_08_09.md`, itself migrated from
  `cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 5's own scope-boundary note (that todo's Barchart code removal
  covered unified-api-contracts + market-tick-data-service only; deployment-ui was explicitly flagged as unchecked,
  never actually swept). Found orphaned by the 2026-08-10 `/ag-closeout-audit cefi` run — no active cefi
  batch/consolidated-closeout doc claims this deployment-ui-specific spot-check, and the work is a small, bounded,
  deterministic grep-and-conditional-removal with a stated done-when, so it clears the AO dispatch-scope bar even though
  the source issue doc itself currently self-declares `assigned_vm: NA`.
status: draft
nature: process
asset_group: [cefi]
stage: [meta]
repos: [unified-trading-pm, deployment-ui]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-16, satellite-docs, item-level-extraction, barchart]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch16_finalize_2026_08_10.md,
    /plans/active/issues/deployment_ui_barchart_label_spotcheck_2026_08_09.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch11_2026_08_09.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.12
assigned_role: ui_developer
effort: low
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit cefi (2026-08-10, all-tranche run, slot 26). Phase 1 per-doc classification via Workflow flagged
  `issues/deployment_ui_barchart_label_spotcheck_2026_08_09.md` orphaned_never_touched + ao_eligible=true.
context_scope:
  [
    /plans/active/issues/deployment_ui_barchart_label_spotcheck_2026_08_09.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch11_2026_08_09.md,
  ]
---

# CeFi satellite AO batch 16 — deployment-ui Barchart label spot-check

> **Status: DRAFT — awaiting operator approval to flip `active`.** Conflict-checked 2026-08-10: grepped all cefi tranche
> covering docs (`cefi_consolidated_closeout_2026_07_18.md`, its `aggregated_sources` sibling, and every active
> `cefi_*batch*`/`*finalize*` doc) for "Barchart"/"barchart" — the only hits are
> `cefi_consolidated_closeout_2026_07_18.md` lines 198-201, which describe batch11's ALREADY-SHIPPED code/adapter/schema
> removal in `unified-api-contracts` + `market-tick-data-service` — a different repo scope than this todo's
> `deployment-ui` UI-layer target, no overlap.

## Todos

- [ ] [UI] P3. Grep `deployment-ui` for `"Barchart"`/`"barchart"` references in launch/devops console source dropdowns
      or config (source: `issues/deployment_ui_barchart_label_spotcheck_2026_08_09.md`). If found, remove/replace
      mirroring the already-shipped `unified-api-contracts@fc1b4897` + `market-tick-data-service@aea655a9` cleanup. If
      none exist, close the source issue doc citing the negative-result grep as evidence. **Done when**: either a
      committed diff removes every "Barchart"/"barchart" UI reference in `deployment-ui`, or the source issue doc is
      updated + archived with the negative-result grep output quoted as evidence. Repo: deployment-ui (code path) /
      unified-trading-pm (doc close-out).

## Codex SSOTs

- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the shared conflict-check protocol.
- `/cursor-configs/skills/ag-closeout-audit/SKILL.md` — the audit run this batch was drafted from.

## Progress Log

- **2026-08-10** — Drafted by the `/ag-closeout-audit cefi` run (slot 26, all-tranche mode). Source doc found orphaned
  by `check_ag_closeout_linkage.py` (no related:/mention path to the cefi closeout family) and confirmed by a real
  Phase-1 classification agent as `orphaned_never_touched` + `ao_eligible=true` — a small bounded
  grep-and-conditional-fix with a stated done-when, genuinely uncovered by any active cefi plan. `status: draft` per the
  skill's autonomous-mode safety rail; flip to `active` only after operator review.
