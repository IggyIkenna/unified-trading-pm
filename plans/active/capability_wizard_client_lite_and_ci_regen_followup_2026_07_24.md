---
doc_type: plan
title: Capability wizard — client-lite successor + CI-runner openapi regen follow-up
summary: >-
  Small follow-up plan forking the 2 residual items left open when `capability_wizard_and_manifest_2026_06_11.md`
  archived (65/67 todos done, plan-line-cap remediation 2026-07-24): (1) the CI-runner-blocked full
  `generate-unified-openapi.sh` regen (F12/F14 — needs a `.venv-workspace`-importable host), and (2) the
  named-but-unauthored "client-lite wizard" successor (use case 4 — client-facing configurator, successor of the public
  strategy questionnaire). This plan is the owner-of-record for both until each is actioned.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [agent-orchestrator, deployment-api, deployment-service, deployment-ui, e2e-testing, execution-service]
scope: [engineer, admin]
tags: [strategy, capability-wizard, ci-regen, client-lite, successor-plan, docspec]
related:
  [
    /plans/archive/2026_07/capability_wizard_and_manifest_2026_06_11.md,
    /plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md,
    /plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md,
    /codex/09-strategy/architecture-v2/capability-wizard.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch11_2026_08_09.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch11_finalize_2026_08_09.md,
  ]
created: "2026-07-24"
parent_epic: strategy_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.0
last_updated: "2026-08-09"
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes: [capability_wizard_and_manifest_2026_06_11]
superseded_by:
depends_on: []
source: >-
  Forked from `capability_wizard_and_manifest_2026_06_11.md` (archived 2026-07-24) per the operator-approved plan
  line-cap remediation in `plans/active/issues/plan_line_cap_remediation_2026_07_23.md` — that plan was 65/67 todos done
  (97%) and locked (`locked_by: live-defi-rollout`); the operator approved archiving it outright once its 2
  genuinely-open residual items were forked into a small successor plan rather than attempting a real split.
context_scope:
  [
    /codex/09-strategy/architecture-v2/capability-wizard.md,
    /plans/archive/2026_07/capability_wizard_and_manifest_2026_06_11.md,
    scripts/openapi/generate-unified-openapi.sh,
    "unified-trading-system-ui/app/(public)/questionnaire/",
    /plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md,
    /plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md,
  ]
---

# Capability wizard — client-lite successor + CI-runner regen follow-up

## Scope

This plan carries forward the **only 2 open items** from the now-archived
[`capability_wizard_and_manifest_2026_06_11.md`](/plans/archive/2026_07/capability_wizard_and_manifest_2026_06_11.md)
(archived 2026-07-24 at 65/67 todos done — Phases 0-6 + Wave-2 all shipped). Everything else that plan tracked is DONE;
nothing else is forked here. Codex SSOT for the wider capability-wizard concept:
[`/codex/09-strategy/architecture-v2/capability-wizard.md`](/codex/09-strategy/architecture-v2/capability-wizard.md).

Both residual items are individually small/blocked — this is intentionally a thin placeholder plan, not a new build.
`execution_scope: local-only` (inherited from the parent) — item 1 is genuinely undispatchable until `.venv-workspace`
exists on a CI runner, and item 2 is a deliberately-deferred scope-later item, so neither should be auto-queued to a
worker.

## Residual 1 — CI-runner-blocked full openapi regen (F12/F14)

Context (carried from the parent plan's Phase 0, verbatim history preserved there): the full
`generate-unified-openapi.sh` run needs every service importable in ONE interpreter (`.venv-workspace`), which was
absent on every host used during the original build. `generate_config_registry.py` extracts 0/32 services and would
EMPTY the committed registry if run on such a host (restored via `git checkout` when this was hit — finding F12). No CI
workflow runs `generate-unified-openapi.sh` on any runner today; `uic-openapi-sync` (uts-ui and fund-admin-service)
ships TS types only, from already-committed `*.openapi.json/yaml`, not a fresh aggregate regen (finding F14). Per the
original plan's operator mandate, no new CI infrastructure was built to work around this — the todo stayed open, blocked
on a `.venv-workspace`-capable CI runner being provisioned (operator action).

- [ ] [SCRIPT] P1. Fresh full run of `generate-unified-openapi.sh`; commit regenerated outputs; verify
      `check_openapi_drift.py` quality gate is green and actually fires on synthetic drift. **PARTIAL 2026-06-11
      (capability-exporter, slot-4):** UAC-importable outputs regenerated + committed — `ui-reference-data.json`
      (byte-identical to committed = already current post-Phase-0), `capability-manifest.json` (new,
      unified-api-contracts@1bc2f07). **STILL BLOCKED ON-HOST:** `config-registry.json` +
      `unified-trading-system.openapi.json` need every service importable in ONE interpreter (`.venv-workspace`), which
      is ABSENT on this host — `generate_config_registry.py` extracts 0/32 and would EMPTY the registry if committed
      (restored via `git checkout`; finding F12). The per-service `.venv`s exist (the capability exporter uses them via
      subprocess), but the aggregate spec generator does not yet do per-service-venv extraction. Full run must happen on
      the laptop / CI runner with `.venv-workspace`; the `uic-openapi-sync` CI regenerates TS types on its runner
      regardless. **CI-REGEN UNIT 3 (2026-06-12):** No workflow runs `generate-unified-openapi.sh` on any CI runner.
      `uic-openapi-sync` (uts-ui + fund-admin-service) ships TS types ONLY from `*.openapi.json/yaml`. No new CI
      infrastructure built per mandate. Annotated as F14-confirmed: blocked until `.venv-workspace` is provisioned on a
      CI runner (operator action). See findings file for full F14 annotation.

**Gate**: `.venv-workspace` provisioned on a CI runner (or a laptop with full workspace) → re-run
`generate-unified-openapi.sh` end-to-end → `check_openapi_drift.py` exits 0 with all 3 outputs
(`ui-reference-data.json`, `config-registry.json`, `unified-trading-system.openapi.json`) freshly regenerated and
committed.

**RE-SCOPED 2026-08-07 (operator: "do it, agent can do it that's fine")** — investigated before executing. **The gate
does NOT actually require new CI infrastructure** — the doc's own alternative ("a laptop with full workspace") already
exists: the AO orchestrator VM (`ip-172-31-5-118`) has a full multi-repo checkout + healthy disk headroom (171G free,
75% used — not a capacity risk). **But its `.venv-workspace` directory exists without being properly populated** —
`import instruments_service` fails (`ModuleNotFoundError`), confirming the exact F12 footgun class this doc warns about
(an incomplete/stale venv, not the 32-service editable-install workspace the regen needs). Real remaining work, not done
this pass: (1) run the proper `.venv-workspace` setup (`scripts/setup-workspace-venv.sh` or
`scripts/workspace/setup-dev-environment.sh`) on that VM to completion, (2) verify ALL 32 services import cleanly before
touching the regen (not just spot-checking 1-2), (3) run `generate-unified-openapi.sh`, and CRITICALLY (4) check the
extraction count BEFORE committing anything — F12's own history shows a broken venv silently extracts 0/32 and would
empty the committed registry if blindly committed. Deferred to its own pass given the real-data-corruption risk of
rushing step 4 under time pressure, not because it needs new infrastructure — that part of the original framing was
wrong.

**EXTRACTED 2026-08-09 (round-11 RECLASSIFY + satellite-extraction sweep)** to
`ci_satellite_ao_dispatch_batch11_2026_08_09.md` todo 1 — actioning the 2026-08-07 na-eligibility-audit's own "worth a
RECLASSIFY look... for a future pass with room to execute carefully" flag below. The extraction formalizes the 4-step
procedure above into an explicit, worker-executable safety gate (verify-all-imports → regen → extraction-count
checkpoint against the committed baseline → commit-or-revert), directly addressing the rushed-step-4 data-corruption
risk that held it back rather than working around it. This checkbox stays open here until batch 11's gated finalize twin
(`ci_satellite_ao_dispatch_batch11_finalize_2026_08_09.md`) reconciles it with the shipped commit or a clean `BLOCKED-*`
finding.

**RECONCILED 2026-08-09 (batch 11 finalize twin) — checkbox stays OPEN, `BLOCKED-EXTRACTION-REGRESSION`, nothing
committed.** Batch 11's todo 1 ran to completion but landed on its own explicitly-valid blocked outcome, not a shipped
commit: `.venv-workspace` was fixed (root cause was `setup-workspace-venv.sh` never applying a repo's own
`[tool.uv].override-dependencies` during editable installs, permanently blocking `execution-service` and its dependents
— fixed and shipped at `unified-trading-pm@026a84d6f6`), every real service now imports cleanly, and
`generate-unified-openapi.sh` ran end-to-end producing a fresh `unified-trading-system.openapi.json` that improved on
every metric (473→628 paths, 105→353 schemas, no regression). But the mandatory extraction-count checkpoint caught a
genuine per-metric regression on `config-registry.json`: `total_repos` 19→14 (though `total_configs` rose 26→30) versus
the committed baseline. Root-caused (not auto-resolved): the 7 "missing" repos are exactly the phantom per-family
services (`features-calendar-service`, `features-commodity-service`, `features-cross-instrument-service`,
`features-delta-one-service`, `features-multi-timeframe-service`, `features-sports-service`, `ml-inference-service`)
that `generate_config_registry.py`'s own header comment says were consolidated 2026-06-11 into
`features-service`/`ml-service` monorepos — the committed baseline predates that consolidation-aware script update and
was never regenerated since, which is the whole premise of this Residual. Per the batch11 todo's own non-discretionary
checkpoint rule, the worker discarded the generated outputs (`git checkout --`) rather than commit and did not override
the gate unilaterally. Full findings + 4 follow-up todos (re-verify-and-commit is todo 1, a deprecated-gate correction,
an unrelated GCS 404, a stale phantom-repo entry) are tracked at
`/plans/active/issues/venv_workspace_openapi_regen_batch11_findings_2026_08_09.md` — the next picker-up should start
there (specifically its todo 1) rather than repeat this investigation.

## Residual 2 — Client-lite wizard successor (use case 4)

Context (carried verbatim from the parent plan's use-case list and "Out of scope / named successors" section): the
parent's four operator-stated use cases were (1) visibility, (2) end-to-end parameterization, (3) two-sided code audit,
and (4) **client-lite wizard** — "eventual client-facing configurator (successor of the public strategy questionnaire in
`unified-trading-system-ui/app/(public)/questionnaire/`), ending in a config + credentials checklist + on-demand
backtest (\"here is what I need from you: these API keys; want a 5-year backtest of your configured preference?\")." The
parent's own "Out of scope / named successors" section named this exact gap: "Client-facing lite wizard +
alpha-curtailment tiers (use case 4) — successor plan." and its final "Deferred work — migrated to:" note recorded that
no successor plan existed yet and that the parent "remains the owner of record until one is authored and named." **This
plan is that successor** — it does not yet build client-lite mode; it is the named owner-of-record so the gap is not
lost, per the same DEFERRED item carried forward verbatim below.

- [ ] [DEFERRED] P3. Client-lite wizard mode (use case 4) — named successor plan once internal wizard is hardened.

**Gate (scoping, not yet building)**: when picked up, this todo's first step is to write the actual build plan
(archetype curtailment tiers, credentials-checklist UX, on-demand backtest gating) as its own dated sub-plan under this
one's `parent_epic`, since the internal wizard (Phases 0-6 + Wave-2) is now fully hardened and this was the explicit
precondition named by the parent plan.

## Deferred work — migrated to:

- P1 (Residual 1, CI-runner-blocked openapi regen): extracted to `ci_satellite_ao_dispatch_batch11_2026_08_09.md` todo 1
  (round-11 RECLASSIFY sweep, 2026-08-09). Stays open here until batch 11's gated finalize twin reconciles this checkbox
  with a shipped commit or a clean `BLOCKED-*` finding.
- P3 (client-lite wizard mode, use case 4): N/A — no migration. This plan IS the named successor/owner-of-record for the
  item (see "Context" above); it stays open here until the internal wizard precondition is met and the build sub-plan is
  authored under this plan's `parent_epic`.

## Out of scope (inherited from the parent, unchanged)

- Replacing the public strategy questionnaire — it stays as demand capture; the wizard supersedes it only for
  onboarding.
- Rebuilding any part of the data-status drilldown — delegation only (`/api/data-status/*`).
- Live integration beyond deployment-api data-status + backtest runner calls (wizard is registry/code-driven by design).

## Progress Log (append-only)

- 2026-07-24 — Plan created by forking the 2 residual items off `capability_wizard_and_manifest_2026_06_11.md` during
  the operator-approved plan line-cap remediation (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`). The
  parent plan archived to `plans/archive/2026_07/capability_wizard_and_manifest_2026_06_11.md` in the same action
  (`superseded_by: capability_wizard_client_lite_and_ci_regen_followup_2026_07_24`). No new work done yet — both items
  carried forward verbatim, unchanged in status (open/blocked, open/deferred).
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: re-verified context_scope (6 entries), unchanged — already carries the openapi-regen
  script + questionnaire UI source paths and all entries still resolve.
- **context-scout 2026-08-07**: re-verified context_scope (6 entries), unchanged — all 6 entries confirmed still
  resolving on disk (codex doc, archived parent plan, both issue docs, the openapi-regen script under
  `scripts/openapi/`, and the questionnaire UI dir).
- **round-11 RECLASSIFY + satellite-extraction sweep 2026-08-09**: Residual 1 extracted to
  `ci_satellite_ao_dispatch_batch11_2026_08_09.md` todo 1 + its gated finalize twin. See the na-eligibility-audit
  verdict entry above for the full disposition. Residual 2 untouched.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-30** (tranche `ci`, autonomous): KEEP-NA, valid — both residuals are genuinely gated.
Residual 1 is blocked on an operator-provisioned `.venv-workspace`-capable CI runner, and the parent plan's own operator
mandate forbids building new CI infrastructure to work around it. Residual 2 is an unscoped design call whose own stated
first step is authoring the build sub-plan — a human decision, not a bounded worker outcome.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — operator-gated: CI-runner provisioning + deferred design call

**na-eligibility-audit 2026-08-07** (tranche `ci`): KEEP-NA, valid — re-read fresh post the same-session RE-SCOPED
2026-08-07 note under Residual 1; that note is real new information (the gate does NOT strictly require new CI infra,
and the operator said "agent can do it"), but the todo's own step 4 ("check extraction count BEFORE committing — a
broken venv silently extracts 0/32 and would empty the registry") is a genuine data-corruption risk the note itself says
was deliberately deferred rather than rushed. Flagging Residual 1 as **worth a RECLASSIFY look** (bounded 4-step
procedure, operator already blessed agent execution) for a future pass with room to execute carefully — not
reclassifying here given the real risk of a rushed step 4 and this batch's docs-only scope. Residual 2 unchanged:
deferred design call, its own stated first step is authoring a build sub-plan.

**round-11 RECLASSIFY + satellite-extraction sweep 2026-08-09** (tranche `ci`): whole-doc stays **KEEP-NA** (Residual 2
remains a genuine unscoped design call, unchanged), but **Residual 1 is per-item RECLASSIFIED via satellite-extraction**
— actioning the 2026-08-07 flag above. `ci_satellite_ao_dispatch_batch11_2026_08_09.md` todo 1 formalizes the 4-step
procedure into an explicit worker-executable safety gate: verify every service imports cleanly → run the regen → check
the extraction count against the currently-committed baseline BEFORE any commit → commit only if at-or-above baseline,
else revert and report `BLOCKED-*`. This directly closes the rushed-step-4 data-corruption risk that held the prior
audit back, rather than working around it. Conflict-checked: no other active `assigned_vm: planning` plan under
`parent_epic: strategy_master` touches `.venv-workspace`/openapi regen; no sibling `ci_satellite_ao_dispatch_batch*` doc
references this source doc; no consolidated-closeout doc covers it.
`ci_satellite_ao_dispatch_batch11_finalize_ 2026_08_09.md` (gated) reconciles this doc's Residual-1 checkbox once batch
11 lands. This doc's own `assigned_vm` stays `NA` — a partial (per-item) extraction, not a whole-doc reclassify, since
Residual 2 remains genuinely open.
