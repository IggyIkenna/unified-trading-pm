---
title: workspace-qg.yml workflow-template — redesign needed before rollout (operator escalation)
created: 2026-05-15
author: harsh-main (audit pass)
source:
  - PM@21686e55 (slot 8: workspace-qg.yml.tmpl created)
  - PM@542f0e26 (slot 8: substitution fix in rollout script)
  - PM@128dbf03 + PM@68ba6e7c (harsh-main: UI-only template tier split)
  - alerting-service@05dec98 (slot 8: workspace-qg.yml committed to alerting-service as PoC)
locked_by: live-defi-rollout
locked_since: 2026-05-15
severity: P1 — blocks rollout of CI workflow unification across 21 Python repos
suggested_owner: ikenna-side OR opus-max-tier slot (NOT sonnet — design + trigger semantics decisions needed)
---

## TL;DR

Slot 8 (Sonnet) built `scripts/workflow-templates/workspace-qg.yml.tmpl` intending to
unify the inconsistent `quality-gates.yml` files across 21 Python service repos.
The template **omits the `live-defi-rollout` branch from its trigger list**, which
9 production repos currently rely on for every-push QG runs (hundreds of
runs/day). Rolling it out as-is would silently kill those triggers.

Operator decision 2026-05-15 ~23:00 UTC: **discard slot 8's template, file this
issue doc with full state, escalate to opus-max tier (likely Ikenna's side)
for redesign + proper rollout.**

This doc captures the full state so the redesign doesn't re-discover everything.

---

## Current per-repo trigger audit (Quality Gates workflows on origin/live-defi-rollout)

Audited 2026-05-15 22:55 UTC across all 21 Python repos. **5 distinct trigger
patterns** exist in the wild:

| Trigger pattern                                  | Repos (count)                                                                                                                                                                                                                       | Notes                                          |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------- |
| `[main, staging, live-defi-rollout]`             | deployment-api, deployment-service, execution-service, features-service, instruments-service, market-tick-data-service, market-data-processing-service, strategy-service, unified-trading-library (**9**)                          | Fires on every LDR push (hundreds/day)         |
| `[main]` only                                     | alerting-service, batch-live-reconciliation-service, ml-inference-service, pnl-attribution-service, risk-and-exposure-service, system-integration-tests, client-reporting-api (**7**)                                              | Only fires on PR-to-main (slow cadence)        |
| `[main, staging]`                                 | unified-api-contracts, ibkr-gateway-infra (**2**)                                                                                                                                                                                   | Standard target-branch pattern                 |
| `[main, develop]`                                 | position-balance-monitor-service (**1**)                                                                                                                                                                                            | Uses `develop` instead of `staging` (drift)    |
| empty `branches:` (likely parse issue)            | ml-training-service, trading-agent-service (**2**)                                                                                                                                                                                  | Need investigation — may be broken triggers    |

**Verified via `gh run list`**:
- execution-service: 15× `Quality Gates` on push to LDR (last 30 runs sample)
- alerting-service: 0× `Quality Gates` on push to LDR + 4× `workspace-qg` on PR-to-main from LDR (the slot 8 PoC at @05dec98)

## What slot 8 built (2026-05-15)

- `unified-trading-pm/scripts/workflow-templates/workspace-qg.yml.tmpl`:
  ```yaml
  name: workspace-qg
  on:
    push:
      branches: [main, staging]    # ⚠️ NO `live-defi-rollout`
    pull_request:
      branches: [main, staging]
  jobs:
    quality-gates:
      uses: IggyIkenna/unified-trading-pm/.github/workflows/python-quality-gates.yml@live-defi-rollout
      with:
        dep_repos: "{{DEP_REPOS}}"   # rendered from workspace-manifest.json
      secrets: inherit
  ```
- `rollout-workflow-templates.sh` enhanced with `.tmpl` substitution support
  (`{{DEP_REPOS}}`, `__REPO_NAME__`, `__SOURCE_DIR__` placeholders).
- Slot 8 ran the rollout from the **main** PM clone (not their tab), which
  dropped untracked `workspace-qg.yml` files in every Python repo's
  `.github/workflows/` in the main workspace.
- Slot 8 committed `workspace-qg.yml` to alerting-service ONLY (commit
  `05dec98`), as a proof-of-concept. The other 20 untracked files were never
  committed.

## Harsh-main follow-ups today (2026-05-15)

- PM@128dbf03 — moved UI-only templates (`uac-registry-sync.yml` +
  `uic-openapi-sync.yml`) from `scripts/workflow-templates/` to a new
  `scripts/workflow-templates-ui/` dir. Reason: rollout was propagating them
  to every Python repo as dead code (UAC dispatches to UI repo only).
- PM@68ba6e7c — added UI-tier loop to `rollout-workflow-templates.sh`
  targeting `unified-trading-system-ui` only for the UI templates.
- Python cleanup pass — removed 44 untracked spurious UI-only yamls from main
  workspace clones. UI repo's committed copies (live) preserved.
- **Did NOT yet remove the 20 untracked `workspace-qg.yml` files** —
  awaiting redesign decision (this doc).
- The alerting-service commit `05dec98` is now live: alerting-service has a
  `workspace-qg.yml` running on PRs from LDR → main. It's working but
  redundant with the existing `quality-gates.yml` (also on `[main]` trigger).
  No duplicate-CI yet because alerting-service is in the `[main]`-only
  cluster, and PR-from-LDR-to-main fires both workflows — confirmed: see
  alerting-service runs at 10:57 / 12:14 / 12:52 / 13:15 UTC today (each
  pair of runs is one PR triggering both).

## Why this needs opus-max + Ikenna review

The redesign is **not mechanical**. Decisions needed:

1. **Trigger surface**: should the unified workflow fire on `live-defi-rollout`
   pushes (matching the 9 current LDR-trigger repos), `main` PRs only
   (matching the 7 main-only repos), or both? May-23 cutover removes LDR
   entirely — what's the post-cutover trigger?
2. **Migration sequencing**: if the unified template adds `live-defi-rollout`,
   when we adopt it, do we ALSO remove existing `quality-gates.yml` to avoid
   duplicate CI runs? Or rename the existing one out of the way?
3. **`dep_repos` source of truth**: the new template pulls from
   `workspace-manifest.json` (✅ correct); the existing per-repo files have
   hand-crafted lists. alerting-service's existing list includes **3 phantom
   deps** that no longer exist as repos (`unified-cloud-interface`,
   `unified-config-interface`, `unified-internal-contracts`) + a duplicate
   `unified-trading-library`. That's a workspace-wide cleanup all by itself.
4. **`develop` branch outlier**: position-balance-monitor-service uses
   `develop` instead of `staging`. Stale? Migrate?
5. **Empty `branches:`**: ml-training-service + trading-agent-service show
   empty `branches:` in the audit — need a careful read of the file to
   determine if the trigger is broken or just on a different line.
6. **Ikenna-side equivalence**: does Ikenna's side have similar workflow
   drift? Should this unification touch his repos too? Cross-side coordination
   needed.
7. **Post-cutover canonical**: May-23 retires LDR. The template should
   declare what the post-cutover canonical trigger is (main + staging? main
   only?) so this isn't re-litigated in 8 days.

## Recommended next steps (for whoever picks this up)

1. **Pre-design**: re-read this issue doc + the 3 commits (21686e55, 542f0e26,
   128dbf03+68ba6e7c).
2. **Trigger design decision**: write the canonical trigger surface to
   `codex/08-workflows/ci-cd-flow.md` (slot 8 created this doc — extend it).
3. **Template fix**: update `workspace-qg.yml.tmpl` triggers to match the
   decision. Add `live-defi-rollout` to branches if keeping pre-cutover.
4. **Per-repo migration plan**: for each of 21 repos, identify (a) drop
   existing `quality-gates.yml` (b) rename to keep both (transition window)
   (c) merge configs. Document per-repo before touching.
5. **`dep_repos` cleanup**: cross-reference every existing per-repo
   `dep_repos` list against `workspace-manifest.json`. File a separate
   issue doc for phantom-dep cleanup if the count is high (alerting-service
   alone has 4 phantom/duplicate entries).
6. **Coordinated rollout**: when the design lands, run the rollout from
   main workspace (per the existing pattern), commit per-repo + push to LDR.
7. **Continuous verification**: add `Last verified` column to the master plan
   for CI workflow consistency (per CLAUDE.md "Master Plan Continuous
   Verification Column" hard rule).

## State of the artifacts as of 2026-05-15 ~23:00 UTC

- ✅ **Deleted by harsh-main** (this doc creation): `workspace-qg.yml.tmpl` from
  `scripts/workflow-templates/` + 20 untracked `workspace-qg.yml` artifacts
  from main workspace Python repo clones (excluded: alerting-service, which
  has a committed copy).
- 🟡 **Still live on origin/live-defi-rollout**: `alerting-service@05dec98`
  with `workspace-qg.yml` deployed. Redesigner decides: revert that commit OR
  keep alerting-service as the "first cutover repo" reference.
- 🟢 **Preserved**: UI-tier templates (`uac-registry-sync.yml` +
  `uic-openapi-sync.yml`) in `scripts/workflow-templates-ui/`, scoped via
  PM@68ba6e7c so they only target unified-trading-system-ui. Working
  correctly.
- 🟢 **Untouched**: `python-quality-gates.yml` reusable workflow in PM (this
  is the actual QG logic — every per-repo workflow file calls it). Slot 8
  did not modify this file.

## Cross-side handoff

Cross-side ping filed in `plans/active/_agent_pings.md` at 2026-05-15 23:00 UTC
asking Ikenna to (a) take ownership of the redesign or (b) confirm Harsh-side
should re-spawn this on an opus-max slot.

execution: owner: ikenna-main (pending ack) OR harsh-main on opus-max slot
cadence: one-shot redesign + multi-repo rollout
verifier: per-repo `gh run list` shows expected trigger pattern on appropriate branches
last_executed: NEVER
