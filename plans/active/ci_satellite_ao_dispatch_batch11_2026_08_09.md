---
doc_type: plan
title: CI satellite AO batch 11 — eleventh AO-dispatch extraction for the ci tranche (strategy_master group)
summary: >-
  Round-11 combined RECLASSIFY + satellite-extraction sweep, `ci` tranche. Extracts Residual 1 (the CI-runner-blocked
  full `generate-unified-openapi.sh` regen) out of `capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md`
  into a bounded, safety-gated AO todo — actioning that doc's own 2026-08-07 na-eligibility-audit flag ("worth a
  RECLASSIFY look... not reclassifying here given the real risk of a rushed step 4"). The gate this batch adds is the
  explicit checkpoint that flag was waiting on: verify ALL services import cleanly, then verify the extraction count
  BEFORE committing anything, so a broken/incomplete `.venv-workspace` can never silently empty the committed registry
  (the exact F12 footgun the parent doc names). Residual 2 (client-lite wizard successor, an unscoped design call) is
  NOT extracted — it stays open/NA in the parent doc, unchanged.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, unified-api-contracts]
scope: [engineer, admin]
tags: [ci, ao-dispatch, satellite-docs, openapi, capability-wizard, venv-workspace, reclassify, strategy_master]
related:
  [
    /plans/active/capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md,
    /plans/active/ci_satellite_ao_dispatch_batch11_finalize_2026_08_09.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch10_2026_08_09.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /codex/09-strategy/architecture-v2/capability-wizard.md,
    scripts/openapi/generate-unified-openapi.sh,
    scripts/setup-workspace-venv.sh,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
effort: medium
sequential: false
drift_direction: advance-code
context_scope:
  [
    /plans/active/capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md,
    scripts/openapi/generate-unified-openapi.sh,
    scripts/openapi/generate_config_registry.py,
    scripts/setup-workspace-venv.sh,
    scripts/quality_gates/check_openapi_drift.py,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Round-11 combined RECLASSIFY + satellite-extraction sweep, run 2026-08-09, against the `ci`-tranche candidate list
  (docs whose existing KEEP-NA marker predates today's precedent set). This item's source
  (`capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md` Residual 1) carries `parent_epic:
  strategy_master`, distinct from every other active `ci`-tranche satellite batch (batch7/9=infrastructure_master,
  batch8=agent_operating_framework_master, batch10=observability_master) — new group, new batch number per the
  established parent_epic-grouping rule.
---

# CI satellite AO batch 11 (strategy_master group)

> **Why this is a separate doc from batch 7-10.** Different source doc, different `parent_epic` (`strategy_master`, not
> shared by any prior `ci`-tranche batch) — per the established batch7/batch8/batch9/batch10 parent_epic-grouping
> precedent, a new group gets its own batch+finalize pair even at 1 item.

## Todos

- [ ] 1. [INFRA] P1. **Provision `.venv-workspace` on the orchestrator VM to completion, verify EVERY service imports
      cleanly, regenerate the unified OpenAPI/config-registry outputs, and commit ONLY if the extraction-count
      checkpoint passes.** Full context + the F12 data-corruption footgun this guards against:
      `/plans/active/capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md` § "Residual 1" (verbatim
      history + the 2026-08-07 RE-SCOPED investigation this todo formalizes into a safety-gated procedure).

  **Re-verify current state fresh first** — the 2026-08-07 note found `.venv-workspace` present but improperly populated
  (`import instruments_service` failed); 2+ days have passed and other sessions may have touched this host — do not
  assume that diagnosis still holds, confirm it live before acting.

  1. Run `bash scripts/setup-workspace-venv.sh --check` (workspace root on the orchestrator VM, the same host this AO
     dispatch runs on). If it reports the venv already complete and every repo importable, skip to step 2. Otherwise run
     `bash scripts/setup-workspace-venv.sh --force` to rebuild it from scratch (editable-installs every repo with a
     `pyproject.toml`, topological T0→T3 order — idempotent, safe to re-run).
  2. **Verify ALL services import cleanly — enumerate and confirm each one individually, not a spot check.** Re-derive
     the live service list from the workspace manifest the setup script reads (do not trust a hardcoded "32" — the true
     count may have moved since 2026-07-24; compare against whatever the script itself reports as the expected count).
     If ANY service fails to import, STOP HERE — do not proceed to step 3. Report `BLOCKED-VENV-INCOMPLETE` with the
     exact failing import(s); do not attempt the regen against a partial venv.
  3. Only once every service is confirmed importable: run `bash scripts/openapi/generate-unified-openapi.sh` end to end
     (produces `unified-trading-system.openapi.json`, `ui-reference-data.json`, `config-registry.json`,
     `capability-manifest.json`, + siblings under `unified-api-contracts/openapi/`).
  4. **CRITICAL CHECKPOINT — before committing anything**, inspect the freshly generated `config-registry.json` (and
     `unified-trading-system.openapi.json`'s `paths`/`components.schemas` counts): the number of services/paths
     represented must be AT OR ABOVE the currently-committed baseline's own count (diff against
     `git show HEAD:unified-api-contracts/openapi/config-registry.json` in that repo, not a hardcoded number — this is
     exactly the F12 failure mode the parent doc found: a broken venv silently extracts 0/32 and would EMPTY the
     committed registry if blindly committed). **If the fresh count is LOWER than the committed baseline for ANY tracked
     output file, DO NOT commit** — `git checkout` to discard the generated files in that working tree and report
     `BLOCKED-EXTRACTION-REGRESSION` with the before/after counts instead.
  5. If the checkpoint passes (count at or above baseline for every regenerated file): commit the regenerated outputs in
     `unified-api-contracts` via the normal quickmerge path for that repo.
  6. Verify `check_openapi_drift.py` (this repo's own quality gate) is green against the newly-committed outputs, and
     that it actually still fires on synthetic drift (do not just check the happy path) — this closes the parent doc's
     own stated Gate.
  7. Flip `capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md`'s Residual-1 todo `[x]` citing the
     `unified-api-contracts` commit SHA + the observed extraction counts (via this batch's finalize twin, not directly
     here — see `ci_satellite_ao_dispatch_batch11_finalize_2026_08_09.md`).

  **Done when**: either (a) outputs regenerated + committed with a verified-passing extraction-count checkpoint and a
  green `check_openapi_drift.py`, or (b) a clean `BLOCKED-VENV-INCOMPLETE` / `BLOCKED-EXTRACTION-REGRESSION` report with
  nothing partially committed — both are valid completions of this todo; silently skipping the checkpoint is not.

  - Source: `capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md`, Residual 1 (its own `[SCRIPT] P1`
    todo).

## Codex SSOTs (read before executing this todo)

- `/codex/09-strategy/architecture-v2/capability-wizard.md` — wider capability-wizard concept this regen feeds.
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan's sibling satisfies.

## Progress Log

- **2026-08-09 (round-11 RECLASSIFY + satellite-extraction sweep, `ci` tranche)** — Authored by extracting Residual 1
  out of `capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md`, actioning that doc's own 2026-08-07
  na-eligibility-audit flag ("worth a RECLASSIFY look... for a future pass with room to execute carefully — not
  reclassifying here given the real risk of a rushed step 4"). This is that future pass: the todo above formalizes the
  4-step procedure the parent doc already outlined into an explicit, worker-executable safety gate (verify-all-imports →
  regen → extraction-count checkpoint → commit-or-revert), directly addressing the rushed-step-4 risk that held it back
  rather than working around it. Conflict-checked: no other active `assigned_vm: planning` plan under
  `parent_epic: strategy_master` touches `.venv-workspace`/openapi regen (grepped
  `venv-workspace|generate-unified-openapi|generate_config_registry` across `plans/active/` — only the source doc and
  this batch itself match); no sibling `ci_satellite_ao_dispatch_batch*` doc references this source doc or this content;
  no consolidated-closeout doc covers it. Residual 2 (client-lite wizard successor) deliberately NOT extracted — it
  remains a genuine unscoped design call per the parent doc's own unchanged reasoning.
