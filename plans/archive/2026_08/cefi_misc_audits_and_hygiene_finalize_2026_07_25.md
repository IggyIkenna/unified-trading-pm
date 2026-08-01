---
doc_type: plan
title: CeFi misc audits + hygiene — finalize (reconcile checkboxes + archive)
summary: >-
  Gated closeout for cefi_misc_audits_and_hygiene_2026_07_25.md — machine-held via depends_on + gate_on_depends: true
  until all 3 of that plan's todos are done. Reconciles the parent (cefi_consolidated_closeout_2026_07_18.md) checkboxes
  for the UAC-fallback decision, the reconciliation-gap spot-check, and the archival todo, then archives.
status: complete
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, close-out, hygiene, archival]
related:
  [
    /plans/archive/2026_08/cefi_misc_audits_and_hygiene_2026_07_25.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-30"
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

> **🟢 ARCHIVED 2026-08-01.** Both todos done: the 3 parent-plan checkboxes reconciled, and
> `cefi_misc_audits_and_hygiene_2026_07_25.md` archived to `/plans/archive/2026_08/`. This finalize doc itself moves
> alongside it in a follow-up commit (per the never-combine-checkbox-flip-with-git-mv rule) to
> `/plans/archive/2026_08/cefi_misc_audits_and_hygiene_finalize_2026_07_25.md`. No new durable contract — codex
> alignment check: nothing to update.

> **Machine-gated on `cefi_misc_audits_and_hygiene_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 3 tasks in that plan are `done`. `sequential: true` because todo 2
> (archival) must run after todo 1 (reconciliation).

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile `cefi_consolidated_closeout_2026_07_18.md`'s 3 corresponding checkboxes.** DONE —
      unified-trading-pm@5282adf79. Flipped the UAC-fallback-removal ruling item (KEEP, do not remove — deferred not
      declined; evidence `issues/uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md`,
      unified-trading-pm@2a6a7db62), the reconciliation-gap-doc `[VERIFY]` spot-check item (3 findings spot-checked;
      evidence `issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md` Progress Log,
      unified-trading-pm@ab28a0f39), and the consolidate+archive `[PM]` item (moved to `plans/archive/issues/`,
      unified-trading-pm@ff8312609). All 3 cited commits/records verified to exist before citing. Repo:
      unified-trading-pm. **Done when**: all 3 named checkboxes/sections in the parent doc are flipped with verified
      evidence — met.
- [x] ✅ [DOC] P2. **Archive `cefi_misc_audits_and_hygiene_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): confirm no Deferred items remain untracked → add the archive banner → run the
      codex-alignment check → grep the corpus for every referrer of `cefi_misc_audits_and_hygiene_2026_07_25` and fix
      each path to point at the archived location → clear `locked_by` (already empty, confirm). DONE —
      unified-trading-pm@(this commit). Confirmed 0 untracked deferred items (no `## Deferred` section; the one separate
      finding surfaced mid-plan, `bybit_spot_manifest_stray_captures_2026_07_07.md`, was already independently closed
      2026-07-26 per the plan's own text). Codex-alignment check: nothing to update — the plan's own "Codex SSOTs"
      section already states no new durable contract. Moved to `plans/archive/2026_08/` (archival-date folder, per
      convention — verified against the live `plans/archive/2026_08/` directory, not the `2026_07` guess this todo's
      brief assumed). Corpus referrers fixed: `related:` frontmatter path-form hits in
      `issues/uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md` and this doc's own sibling reference, plus the
      path-shaped citation in `issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md` —
      bare backtick filename mentions in prose narrative (no path prefix, out of `check_reference_paths.py`'s scope)
      were left as historical record, matching this corpus's existing convention for archived-doc citations. `locked_by`
      confirmed empty on both docs. **Done when**: the plan is moved to `plans/archive/2026_08/`, every corpus referrer
      resolves to the new path, and this finalize doc itself gets archived alongside it in the same commit — met; this
      doc archives in its own follow-up commit immediately after (per the never-combine-flip-with-git-mv rule).
