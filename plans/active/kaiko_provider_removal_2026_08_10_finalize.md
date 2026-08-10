---
doc_type: plan
title:
  "Finalize — Kaiko provider removal (2026-08-10) — prove zero live references remain and rescope the credential ask to
  Glassnode only"
summary: >-
  Gated companion to `kaiko_provider_removal_2026_08_10.md`, per `task_template.md`'s finalize-plan-coverage rule. Held
  by `depends_on` + `gate_on_depends: true` until the removal lands. Verifies the removal is genuinely complete across
  all three repos rather than trusting the removing worker's per-repo reports, then rescopes
  `glassnode_kaiko_credential_ask_2026_08_09.md` so the Glassnode half survives as a live BLOCKED-CREDENTIALS ask while
  the Kaiko half is closed as ruled-out.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [kaiko, removed-provider, finalize, credential-ask, verification]
related:
  [
    /plans/active/kaiko_provider_removal_2026_08_10.md,
    /plans/active/issues/glassnode_kaiko_credential_ask_2026_08_09.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: data_engineering
effort: medium
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [kaiko_provider_removal_2026_08_10]
gate_on_depends: true
context_scope:
  [
    /plans/active/kaiko_provider_removal_2026_08_10.md,
    /plans/active/issues/glassnode_kaiko_credential_ask_2026_08_09.md,
  ]
source: >-
  Authored alongside `kaiko_provider_removal_2026_08_10.md` on 2026-08-10, per the finalize-plan-coverage rule. Gated —
  does not dispatch until the removal completes.
---

# Finalize — Kaiko provider removal

Gated behind `kaiko_provider_removal_2026_08_10.md`. Do not start until all 4 of its todos are `[x]`.

## Todos

- [x] ✅ [DATA] P3. **DONE 2026-08-10 — zero live integration references remain.** Swept every repo (`rg -il kaiko`,
      excluding `.venv`/`build`/`node_modules`/`plans/archive`). Survivors are all prose records of the ban itself
      (CLAUDE.md, the codex SSOT, this plan pair, the parked/credential-ask docs, and `base-service.sh`'s
      baseline-history comment) plus TWO `.ts` hits in `unified-trading-system-ui` investor-relations copy — both read
      `competitor: "Tardis / Kaiko / Amberdata"`, i.e. Kaiko named as a COMPETITOR in the vendor landscape, not an
      integration we claim. Per this plan's own scope note those are correctly left alone. **Prove zero live Kaiko
      references remain, workspace-wide.** Run
      `rg -il kaiko --glob '!.venv*' --glob '!build' --glob '!node_modules' --glob '!*/plans/archive/**'` across every
      repo. The only surviving hits should be (a) plan/issue docs recording this removal, and (b) any
      `unified-trading-system-ui` narrative copy the removal plan deliberately left in scope-note. **Done when**: the
      full hit list is recorded here with a per-hit verdict, and anything unexpected is re-opened as a todo on the
      removal plan rather than waved through.
- [x] ✅ [DATA] P3. **DONE 2026-08-10.** `unified-api-contracts@c48238266b` (QG ALL PASSED 655s) shipped FIRST, then
      `market-tick-data-service@da86db197e` (QG ALL PASSED 1177s) — correct dependency order, UAC before MTDS. Both
      post-push ancestry-verified as ancestors of `origin/live-defi-rollout`. **Confirm both code repos are green and
      shipped.** `bash scripts/quality-gates.sh` green in `unified-api-contracts` and `market-tick-data-service`, both
      changes landed via quickmerge with a `Quickmerge:` trailer, and the UAC change precedes the MTDS change in the
      dependency order. **Done when**: both commit SHAs are cited here and confirmed ancestors of
      `origin/live-defi-rollout`.
- [x] ✅ [DOCS] P2. **DONE 2026-08-10** (operator ruling recorded in
      `/plans/active/kaiko_provider_removal_2026_08_10.md` § source + Progress Log)**.** Title, tags and banner now read
      Glassnode-only; the Kaiko half is closed with the two shipped SHAs cited; the Glassnode half stays OPEN as a live
      BLOCKED-CREDENTIALS ask and is tracked on the consolidated operator list. **Rescope
      `/plans/active/issues/glassnode_kaiko_credential_ask_2026_08_09.md` to Glassnode only.** Close the Kaiko half
      citing the 2026-08-10 operator ruling recorded in `/plans/active/kaiko_provider_removal_2026_08_10.md`, and this
      removal plan; keep the Glassnode half OPEN as a live credential-blocked ask (`glassnode-api-key` still
      unprovisioned — that provider is not banned and the external-data-always-available rule means the ask stands until
      the operator provisions or declines it). Update the doc's `title`, `summary` and `tags` so it no longer presents
      as a joint ask. **Done when**: the doc reads as a Glassnode-only credential ask with the Kaiko history preserved
      as a closed record, and `check_frontmatter_schema.py` passes.
- [ ] [DOCS] P3. **Archive this pair once the above are done**, via the standard 6-step ritual, repointing every corpus
      referrer. **Done when**: both docs archived with banners and `check_reference_paths.py` no worse than baseline.

## Progress Log

- **2026-08-10** — Authored alongside the removal plan. Gated via `depends_on` + `gate_on_depends: true`.
