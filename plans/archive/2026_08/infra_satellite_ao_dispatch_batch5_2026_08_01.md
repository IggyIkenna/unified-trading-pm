---
doc_type: plan
title:
  Infra satellite AO batch 5 — the DataStatusTab `DATA_PIPELINE_SERVICES` gap (G3), unblocked now that cross-cutting's
  same-file claim shipped
summary: >-
  Fifth AO-dispatch batch for the `infra` topic tranche, produced by `/ag-closeout-audit infra` (autonomous mode,
  2026-08-01). Not a fresh Phase-1 sweep — this run's iterative-drain step 1 (re-check the prior batches' own Deferred
  gates before fresh triage, per the skill's own methodology) found that batch1 Deferred item 4 / batch3's tracked gate
  G3 — deployment-ui's `DATA_PIPELINE_SERVICES` stale-names gap in `DataStatusTab.tsx`, held back since 2026-07-26
  because `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` item (B) claimed the same file for a different,
  then-unshipped change — has now genuinely cleared: item (B) shipped today (`deployment-ui@727298b`, 2026-08-01 01:42
  UTC). This is the ONLY gate that cleared this run (G1/G2 remain gated on the same `base-service.sh`/ `base-library.sh`
  serialization as before; G4 was already resolved elsewhere and shipped 2026-07-31; G5's MTDS >900-line sub-item is now
  also resolved elsewhere with a correct checkbox, not new batch material; G6 stays owned by tradfi). The one new
  never-cited candidate this run surfaced (`issues/deployment_scripts_bucket_soft_delete_retention_drift_2026_07_31.md`)
  is a genuine operator-gated judgment call (which side of a live/config terraform drift is correct, plus a
  delete-safety-adjacent apply), not worker-determinable — reported in the parked-findings doc, not drafted here.
  Single-todo plan per `task_template.md` §4's carve-out (`check_finalize_plan_coverage.py`'s `_todo_count(...) <= 1`
  threshold) — no separate finalize plan; archival is folded into the one todo's own "Done when", mirroring
  `infra_satellite_ao_dispatch_batch4_2026_07_31.md`.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-ui, unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ao-dispatch, ag-closeout-audit, satellite-docs, batch-5, plan-hygiene, data-status]
related:
  [
    /plans/active/issues/issue_docs_remediation_sweep_2026_06_02.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch3_2026_07_30.md,
    /plans/archive/2026_08/infra_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/ag_closeout_audit_infra_parked_2026_08_01.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-06"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  `/ag-closeout-audit infra` run 2026-08-01 (ag_closeout_auditor scheduled worker, slot 5). Phase 0 re-derived the
  covering set via `generate_ag_closeout_audit_candidates.py --tranche infra` (39 members / 10 covering docs / 1 never
  cited). Per the skill's batchN iterative-drain methodology ("re-check the prior batch's Deferred section first... only
  then run a fresh pass over whatever's left"), this run re-verified batch1/batch3's tracked Deferred gates (G1-G6)
  against live checkbox/commit state before considering fresh Phase-1 triage of the single new never-cited candidate.
  That re-check is what surfaced this batch's one todo — a targeted delta read, not a from-scratch 10-agent
  re-classification of all 39 members (most already self-dispatched or already-covered, per 4 prior audit rounds on this
  tranche: 2026-07-26, 2026-07-27, 2026-07-30, 2026-07-31 ×2).
---

# Infra satellite AO batch 5

> **✅ STATUS: `active`** — operator-approved 2026-08-06, dispatching. Flipped from `draft` per CLAUDE.md § "Plan
> destination — ASK BEFORE CREATING" and the `/ag-closeout-audit` skill's autonomous-mode rule. Nothing here has been
> shipped.

## Why this batch exists — a conflict-gated item that cleared, not a fresh orphan

`infra_satellite_ao_dispatch_batch1_2026_07_26.md` Deferred item 4 (restated as gate **G3** in
`infra_satellite_ao_dispatch_batch3_2026_07_30.md`'s tracking table) has been held back since 2026-07-26:

> deployment-ui `DATA_PIPELINE_SERVICES` (GAP G-UI). Stale `features-cefi/defi/tradfi/prediction-service` names +
> omitted strategy-service in `DataStatusTab.tsx`. `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` item (B)
> already edits `DataStatusTab`/`HonestCoverageCard` for a different change. Same file, two batches — parked.

The sequencing was explicitly ruled 2026-07-26 (`autonomous_session_operator_decisions_2026_07_25.md` entry #35, option
A): **let cross-cutting batch1 land first, infra picks it up once quiet.** Batch3 (2026-07-30) re-verified this still
gated — cross-cutting's item (B) was still `- [ ]`. **This run re-verified it live and found it now `[x]` DONE**:

- `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md:222` — `[x] ✅ [INFRA] P2. DONE 2026-08-01` — sub-item (B)
  ("deployment-ui could-exist/capture surfacing") cites `deployment-ui@727298b`, verified real:
  `git show --stat 727298b` in the `deployment-ui` slot clone resolves to
  `feat(data-status): surface could-exist + out-of-window as distinct coverage values`, committed 2026-08-01 01:42:03
  UTC, touching `HonestCoverageCard.tsx` + a new smoke spec.
- **The shipped commit never actually touched `DataStatusTab.tsx` itself** (`git show 727298b -- '*DataStatusTab*'`
  returns empty) — the original 2026-07-26 framing anticipated both files; what shipped only needed the sibling
  component. This doesn't weaken the unblock, it strengthens it: `DataStatusTab.tsx`'s own last commit is `8f6c4bc`
  (2026-07-27, an unrelated instruments-service render tweak, already `[x]` done elsewhere) — the file has sat untouched
  for 4+ days and cross-cutting's own claim against it (item B) is now closed regardless of which file it ended up
  touching.
- **File genuinely quiet — checked beyond the one collision partner**: corpus-wide `rg` for `DataStatusTab` across all
  `plans/active/*.md` + `plans/active/issues/*.md` surfaces 3 other docs with open todos —
  `data_status_tab_and_downloads_remediation_2026_06_16.md` (8 open items, but every one is already **CODE-SHIPPED** per
  its own text, e.g. `deployment-ui@80c547d`; the checkboxes are unticked only because a full-suite `pw:L2` gate hasn't
  exited 0 for an unrelated reason — a 🟡-banner Fleet-Git nav regression — not because the code is unshipped),
  `data_status_page_ux_and_canonicalisation_2026_07_16.md` (1 open item, an `InstrumentRecord extra='forbid'` schema
  task, does not touch `DataStatusTab.tsx`), and `instruments_satellite_ao_dispatch_batch1_2026_07_27.md` (its only
  `DataStatusTab.tsx` mention sits inside an already-`[x]` item). No live, unshipped, in-flight edit anywhere in the
  corpus currently targets this file.

## Why a single-todo plan with no finalize twin

`task_template.md` §4's finalize-plan-coverage rule requires a gated finalize twin for an `assigned_vm: planning` plan —
EXCEPT the single-todo carve-out, which `scripts/quality_gates/check_finalize_plan_coverage.py` implements literally
(`_todo_count(...) <= 1`, filtered on `assigned_vm: planning` regardless of `status`). Measured before authoring:
baseline is 0 violations / 0 draft-gate issues on this tree. This plan has exactly one todo, so the archival +
source-checkbox-reconciliation work a finalize twin would normally do is folded into that todo's own "Done when" — the
same shape `infra_satellite_ao_dispatch_batch4_2026_07_31.md` and the archived
`ci_satellite_ao_dispatch_batch3_2026_07_30.md` used.

## Conflict check performed before drafting

- **`deployment-ui/src/components/DataStatusTab.tsx` / `DATA_PIPELINE_SERVICES`** — `rg` across ALL of `plans/active/`
  (plans + issues, not just infra-tagged) for `DATA_PIPELINE_SERVICES` returns exactly 4 hits: this batch's own sources
  (`infra_satellite_ao_dispatch_batch1_2026_07_26.md`, `infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`,
  `infra_satellite_ao_dispatch_batch3_2026_07_30.md`, all infra's own prior tracking of this exact gate) and the
  original source doc (`issues/issue_docs_remediation_sweep_2026_06_02.md`, still `- [ ]`). Zero competing claims.
- **`DataStatusTab.tsx` broadly** — see the file-quiet check above. No other active, unshipped claim.
- **`SERVICE_TO_KIND` (`deployment-api/deployment_api/services/data_status_drilldown/_core.py`)** — read-only reference
  for this todo (establishes the current real service names); `rg` for `SERVICE_TO_KIND` across `plans/active/` returns
  no plan proposing to change that dict itself. No collision.
- **`check_delete_vm_launch_gating.sh` shape** — the todo is a frontend constant + UI fix with a `pw:L2` regression
  spec. No GCS delete, no `--apply`, no VM launch. No `[OPERATOR]` tag or delete-safety citation required.

## Todos

- [x] ✅ [UI] P2. **Fix deployment-ui GAP G-UI: `DATA_PIPELINE_SERVICES` stale names + missing `strategy-service`** —
      deployment-ui@fecd67c (`deployment-ui/src/components/DataStatusTab.tsx:152-161`, currently a hardcoded `Set` of
      `["instruments-service", "market-tick-data-service", "market-data-processing-service",     "features-cefi-service", "features-defi-service", "features-tradfi-service", "features-sports-service",     "features-prediction-service"]`).
      **Re-verify the live set with
      `grep -n -A12 'const DATA_PIPELINE_SERVICES'     deployment-ui/src/components/DataStatusTab.tsx` before starting**
      in case it has drifted further since this todo was written. The 4 `features-{cefi,defi,tradfi,prediction}-service`
      names are stale relative to the backend's current FOLD A naming
      (`deployment-api/deployment_api/services/data_status_drilldown/_core.py:37-61`, `SERVICE_TO_KIND` — features
      collapsed into family-named services `features-delta-one-service`, `features-volatility-service`,
      `features-onchain-service`, plus the untouched
      `features-sports-service`/`features-calendar-service`/`features-multi-timeframe-service`/
      `features-cross-instrument-service`), and `strategy-service` (present in `SERVICE_TO_KIND` as
      `"strategy-service": "strategy-store"`) is omitted from the UI set entirely. **Investigative step first**:
      cross-reference `SERVICE_TO_KIND`'s keys against which services are genuinely live/deployed data-pipeline services
      today (not stale dict entries of their own — check via the deployment-service/deployment-api service registry or
      an actual Cloud Run services listing, not just the Python dict, since the dict itself could contain its own
      staleness) — do not blind-copy `SERVICE_TO_KIND`'s key list into the UI without that cross-check. **Preserve the
      existing runtime-service exclusion** (`execution-service`/risk/pnl/alerting stay OUT — the component's own comment
      at line 150-151 documents this boundary; do not add `execution-service` even though it also has a
      `SERVICE_TO_KIND` entry, since the source doc never asked for that and the UI's own docstring explicitly scopes
      those to Monitor → Live/Experiments instead). Add `strategy-service` per the source doc's explicit instruction.
      `pw:L2` gate applies — add/extend a regression spec proving the pipeline-services banner and any per-service
      filtering render correctly for both an added service (`strategy-service`) and a renamed one (one of the FOLD A
      family names). **Then reconcile the source doc**: in `issues/issue_docs_remediation_sweep_2026_06_02.md`, flip the
      G-UI `[CODE] [UI] P2` checkbox (line ~415-423) `[x]` citing this todo's actual shipped commit sha (re-verify the
      sha resolves with `git show`, do not copy this todo's own text blind), and check whether that doc has any other
      still-open todos before considering its own archival (expected: yes, other gaps in that doc are unrelated and stay
      open — do NOT archive the source doc unless it is genuinely down to zero open items). **Then archive this batch
      plan itself** (it will have zero remaining open todos) via the standard 6-step archival ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) — update every corpus-wide referrer of
      this plan's path (expected: none yet, this is a brand-new plan) before moving it. **Done when**: the UI's
      `DATA_PIPELINE_SERVICES` set contains the current real data-pipeline service names (no stale per-AG feature
      names), includes `strategy-service`, still excludes the documented runtime services, a `pw:L2` regression spec
      covers the change and passes, `bash scripts/quality-gates.sh` is green in `deployment-ui`, the source doc's
      checkbox is flipped with a verified sha, and this batch plan is archived. Repo: deployment-ui (the fix),
      unified-trading-pm (source-doc reconciliation + this plan's own archival). Source:
      `issues/issue_docs_remediation_sweep_2026_06_02.md` (G-UI, line ~415-423); gate history:
      `infra_satellite_ao_dispatch_batch1_2026_07_26.md` Deferred item 4,
      `infra_satellite_ao_dispatch_batch3_2026_07_30.md` gate G3.

## Codex SSOTs (read before executing this todo)

- `/codex/06-coding-standards/ui-testing-layers.md` — the `pw:L2` regression-spec requirement this todo carries
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the conflict-check protocol this batch
  ran before drafting
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step ritual this todo folds in
- `plans/active/task_template.md` §4 — the single-todo finalize-plan-coverage carve-out this plan uses

## Progress Log

- **2026-08-01** — Drafted by `/ag-closeout-audit infra` (Autonomous/AO-dispatched mode, scheduled daily run, slot 5).
  Phase 0 re-derived the 10-doc covering set via `generate_ag_closeout_audit_candidates.py --tranche infra` (39 members,
  1 never-cited: `issues/deployment_scripts_bucket_soft_delete_retention_drift_2026_07_31.md`, an operator-gated
  terraform-drift judgment call, not batchable — see the parked-findings doc). Per the skill's iterative-drain
  methodology, re-checked batch1/batch3's tracked Deferred gates (G1-G6) against live state before considering fresh
  Phase-1 triage: G1/G2 (`base-service.sh`/`base-library.sh` serialization) still gated —
  `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`'s own claim (the MTDS retry_safe `[BACKEND] P3` item,
  sub-item 3) is still `- [ ]`. G4 (`PYTEST_UNIT_DIR`) confirmed already resolved by operator ruling + shipped elsewhere
  (cefi's approach, 2026-07-31) — not infra's to draft, matches batch1's own Deferred record. G5's MTDS
  > 900-line-tail sub-item confirmed already resolved elsewhere too (`codex_violations_ratchet_to_five_2026_06_10.md`,
  > verified 2026-07-27, all 11 named files split) — a stale-tracking note, not new batch material. G6 stays owned by
  > `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`, unchanged. **G3 cleared** — see "Why this batch exists" above.
  > This is the batch's sole todo. Left `status: draft` deliberately; the flip to `active` is the operator's call. Other
  > findings from this run (2 carried-forward stale-checkbox items from 2026-07-31, 1 carried-forward `asset_group`
  > mistag still unretagged, plus 2 new findings — a stale draft-banner in batch3's body text contradicting its own
  > already-`active` frontmatter, and a tooling self-referential citation blind spot in
  > `generate_ag_closeout_audit_candidates.py`) are recorded in `issues/ag_closeout_audit_infra_parked_2026_08_01.md`,
  > not here.
