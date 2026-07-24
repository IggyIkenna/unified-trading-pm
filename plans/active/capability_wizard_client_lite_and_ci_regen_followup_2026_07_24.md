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
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, deployment-api, deployment-service, deployment-ui, e2e-testing, execution-service]
scope: [engineer, admin]
tags: [strategy, capability-wizard, ci-regen, client-lite, successor-plan, docspec]
related:
  [
    plans/archive/2026_07/capability_wizard_and_manifest_2026_06_11.md,
    plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md,
    plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md,
    /codex/09-strategy/architecture-v2/capability-wizard.md,
  ]
created: "2026-07-24"
parent_epic: strategy_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.0
last_updated: "2026-07-24"
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
workflow runs `generate-unified-openapi.sh` on any runner today; `uic-openapi-sync` (uts-ui

- fund-admin-service) ships TS types only, from already-committed `*.openapi.json/yaml`, not a fresh aggregate regen
  (finding F14). Per the original plan's operator mandate, no new CI infrastructure was built to work around this — the
  todo stayed open, blocked on a `.venv-workspace`-capable CI runner being provisioned (operator action).

* [ ] [SCRIPT] P1. Fresh full run of `generate-unified-openapi.sh`; commit regenerated outputs; verify
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
