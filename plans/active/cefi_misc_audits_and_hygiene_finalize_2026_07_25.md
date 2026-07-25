---
doc_type: plan
title: CeFi misc audits + hygiene — finalize (reconcile checkboxes + archive)
summary: >-
  Gated closeout for cefi_misc_audits_and_hygiene_2026_07_25.md — machine-held via depends_on + gate_on_depends: true
  until all 3 of that plan's todos are done. Reconciles the parent (cefi_consolidated_closeout_2026_07_18.md) checkboxes
  for the UAC-fallback decision, the reconciliation-gap spot-check, and the archival todo, then archives.
status: draft
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, close-out, hygiene, archival]
related:
  [/plans/active/cefi_misc_audits_and_hygiene_2026_07_25.md, /plans/active/cefi_consolidated_closeout_2026_07_18.md]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_misc_audits_and_hygiene_2026_07_25]
gate_on_depends: true
source: >-
  Per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize
  plan. Precedent: cefi_satellite_ao_dispatch_batch1_2026_07_25.md /
  cefi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# CeFi misc audits + hygiene — finalize

> **Machine-gated on `cefi_misc_audits_and_hygiene_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 3 tasks in that plan are `done`. `sequential: true` because todo 2
> (archival) must run after todo 1 (reconciliation).

## Todos

- [ ] [REVIEW] P1. **Reconcile `cefi_consolidated_closeout_2026_07_18.md`'s 3 corresponding checkboxes.** Flip the
      UAC-fallback-removal `[OPERATOR]` decision item (record the ruling, whatever it was), the reconciliation-gap-doc
      `[VERIFY]` spot-check item, and the consolidate+archive `[PM]` item, citing this plan's evidence — verify each
      cited commit/record actually exists before citing it. Repo: unified-trading-pm. **Done when**: all 3 named
      checkboxes/sections in the parent doc are flipped with verified evidence.
- [ ] [DOC] P2. **Archive `cefi_misc_audits_and_hygiene_2026_07_25.md`** via the standard 6-step ritual (per CLAUDE.md's
      plan-archival rule): confirm no Deferred items remain untracked → add the archive banner → run the codex-alignment
      check → grep the corpus for every referrer of `cefi_misc_audits_and_hygiene_2026_07_25` and fix each path to point
      at the archived location → clear `locked_by` (already empty, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself gets
      archived alongside it in the same commit.
