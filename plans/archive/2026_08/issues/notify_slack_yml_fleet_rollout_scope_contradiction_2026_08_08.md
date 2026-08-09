---
doc_type: issue
title:
  notify-slack.yml fleet-rollout premise contradicted a same-day deletion decision — near-regression caught before push
summary: >-
  ci_satellite_ao_dispatch_batch6_2026_08_08.md todo 9 instructed rolling out a shellcheck fix to notify-slack.yml "so
  all 26 consuming repos pick it up," sourced from unified_trading_ci_no_promotion_tiers_divergence_2026_08_07.md's
  claim that "all 25 OTHER repos' local copies are still on the un-fixed pattern." That claim was already stale the day
  it was written: fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md todo 6 (landed the same day,
  2026-08-07) had just DELETED notify-slack.yml from 22 of 23 non-PM repos as genuinely dead code (their only local
  callers, main-backmerge-to-ldr.yml/semver-agent.yml, had migrated to unified-trading-ci-hosted reusable workflows).
  Running the literal rollout instruction today would have resurrected 20 dead workflow-call files fleet-wide as a
  silent regression of yesterday's cleanup. Caught before any push; reverted; the actual bugfix was scoped down to the 2
  genuine remaining consumers (unified-trading-pm, deployment-service) instead.
status: resolved
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, deployment-service, execution-service, strategy-service]
scope: [engineer]
tags: [ci, cicd, notify-slack, ssot-contradiction, workflow-templates, near-miss, plan-staleness]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch6_2026_08_08.md,
    /plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md,
    /plans/active/issues/unified_trading_ci_no_promotion_tiers_divergence_2026_08_07.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
author: slot-24 (cicd)
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: cicd
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
locked_by:
locked_since:
resolved_by: execution-service@9fbe2a42, strategy-service@92841614 (dead notify-slack.yml copies deleted, sole todo)
source: >-
  Discovered while executing ci_satellite_ao_dispatch_batch6_2026_08_08.md todo 9 (fleet-propagate the SC2015 shellcheck
  fix to notify-slack.yml).
context_scope:
  [
    /plans/active/ci_satellite_ao_dispatch_batch6_2026_08_08.md,
    /plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md,
    unified-trading-pm/scripts/workflow-templates/rollout-workflow-templates.sh,
    unified-trading-pm/scripts/quality_gates/detect_template_drift.py,
  ]
---

# notify-slack.yml fleet-rollout premise contradicted a same-day deletion decision

## What I found

`ci_satellite_ao_dispatch_batch6_2026_08_08.md` todo 9 instructed: fix a shellcheck (SC2015) issue in
`scripts/workflow-templates/notify-slack.yml`, then "re-run `rollout-workflow-templates.sh` so all 26 consuming repos
pick it up." Its source, `issues/unified_trading_ci_no_promotion_tiers_divergence_2026_08_07.md` (written 2026-08-07),
claimed "all 25 OTHER repos' local copies are still on the un-fixed pattern."

I ran the dry-run and it showed 21 of 24 targets as `dry-create` (no existing local copy at all, not "un-fixed pattern"
— genuinely absent), not `dry-update`. I ran the real rollout anyway on the theory that `notify-slack.yml` being listed
in `detect_template_drift.py`'s blanket per-repo canonical-template scan meant every manifest repo was _supposed_ to
carry a copy — this matched the manifest's 26-repo count and momentarily seemed to validate the "26 consumers" framing.
**This was wrong.** Digging into `unified-trading-pm` git history surfaced the real, same-day decision this todo's
source doc didn't account for:

- `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` todos 3-5 (2026-08-07) converted
  `main-backmerge-to-ldr.yml`/`staging-backmerge-to-ldr.yml`/`semver-agent.yml` fleet-wide into thin
  `uses: unified-trading-ci/...` caller stubs — removing their local `uses: ./.github/workflows/notify-slack.yml` calls
  in every repo.
- Todo 6 (same day, 2026-08-07, ~21:49 UTC — commit `e2c3b8af5`) then deleted the now-dead local `notify-slack.yml` copy
  from 22 of 23 non-PM repos, explicitly verified via
  `git show origin/live-defi-rollout:.github/workflows/notify-slack.yml` (absent) per-repo. Two confirmed exceptions:
  `unified-trading-pm` (44 internal-only consumers, e.g. `branch-health.yml`) and `deployment-service`
  (`cloud-run-traffic-drift-check.yml` still calls it locally).
- The `unified_trading_ci_no_promotion_tiers_divergence_2026_08_07.md` issue doc I was pointed to was authored the SAME
  day but apparently didn't cross-check this concurrent deletion — its "25 other repos still on the un-fixed pattern"
  claim conflated "the drift checker flags 21 repos as missing the canonical template" (true, and BY DESIGN
  post-deletion) with "21 repos have a stale-but-present copy" (false).
- `ci_satellite_ao_dispatch_batch6`'s todo 9 (drafted 2026-08-08 by an automated `/ag-closeout-audit` sweep) inherited
  that stale premise verbatim without re-verifying current repo state.

**Near-miss, not an incident**: I caught this before pushing anything (all 24 sibling-repo git operations stayed
local/unpushed) by cross-checking git history once the dry-run's `dry-create`-vs-`dry-update` split looked inconsistent
with the source doc's specific factual claim. Reverted the 20 genuinely-dead resurrections and the 2 pre-existing-zombie
updates (`execution-service`/`strategy-service`, see below); kept only the 2 legitimate fixes (`unified-trading-pm`,
`deployment-service`).

**Residual finding, not fixed here** (out of todo 9's scope, small enough to be its own todo): `execution-service` and
`strategy-service` currently carry a _pre-existing_ `notify-slack.yml` copy with **zero remaining local callers** each
(confirmed via `grep -rn "uses:.*notify-slack" .github/workflows/*.yml` — no hits in either repo). These look like the
same class of dead file todo 6 deleted everywhere else, but todo 6's own explicit per-repo list did NOT include either
of them among the "22 of 23" it deleted — meaning they were either re-created after todo 6 ran (unclear by whom/why;
`execution-service`'s copy traces to a much older commit, `d537b812`, from _before_ the 2026-08-07 caller-stub migration
that made it dead) or todo 6's sweep genuinely missed them. Left untouched here (deliberately out of scope for a
shellcheck-propagation todo) but flagged for cleanup.

## Why it matters

`rollout-workflow-templates.sh --template notify-slack.yml` run against the full manifest would have silently re-created
20 dead `workflow_call`-only files (harmless at runtime — nothing calls them — but a direct, unflagged regression of a
deliberate, verified 2026-08-07 cleanup, and it would have re-poisoned `workflow_template_drift_baseline.json`'s ratchet
logic the next time someone tried to re-delete them "for real"). More generally: two same-day, same-repo-touching plans
(`fleet_workflow_template_dedup_to_unified_trading_ci` and the divergence-audit issue doc) reached opposite conclusions
about the same file set without cross-referencing each other — a genuine SSOT-contradiction class this workspace's
plan-conflict-check discipline is supposed to catch, but didn't here because the automated `/ag-closeout-audit` sweep
that drafted todo 9 sourced only from the (stale) divergence doc, not from the (authoritative, more recent) dedup plan.

## Recommended decision

1. Delete `execution-service`'s and `strategy-service`'s dead `notify-slack.yml` copies (same justification as todo 6's
   other 22 deletions — zero local callers, confirmed via grep).
2. When an `/ag-closeout-audit`-drafted todo instructs a fleet-wide propagation/rollout action sourced from an issue
   doc's factual claim about current repo state, the dispatched worker should re-verify that claim empirically (a quick
   `dry-run` + spot-check) before executing at fleet scale, not just before an audit-scope todo — this incident shows
   the same discipline applies to any wide-blast-radius mechanical action, not just audits.

## Todos

- [x] ✅ [CODE] P3. **Delete the dead `notify-slack.yml` copies** in `execution-service` and `strategy-service` (zero
      local callers confirmed via `grep -rn "uses:.*notify-slack" .github/workflows/*.yml`) — same pattern as
      `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` todo 6's other 22 deletions. **Done same
      session**: `execution-service@9fbe2a42`, `strategy-service@92841614`. Surfaced as a blocking
      `workflow-template-parity` QG failure on `unified-trading-pm` once the template's SC2015 fix made their
      (previously template-matching, un-fixed) stale content newly diverge — fixed inline rather than deferred, since it
      was directly blocking this session's own shipping. (repo: execution-service, strategy-service)

## Progress Log

- **slot-24 (cicd) 2026-08-08T23:05Z**: Caught mid-execution of `ci_satellite_ao_dispatch_batch6_2026_08_08.md` todo 9,
  before any push. Reverted the incorrect 20-repo resurrection + 2 zombie-repo updates; kept the 2 legitimate fixes
  (`unified-trading-pm@f5fe2372e`, `deployment-service@00a23128`). Filed this doc + flipped todo 9 with the corrected
  scope in the same session.
- **slot-24 (cicd) 2026-08-08T23:20Z**: The `execution-service`/`strategy-service` zombie copies turned into a blocking
  `workflow-template-parity` QG failure on `unified-trading-pm` (their stale content, previously matching the un-fixed
  template so no drift showed, newly diverged once the template got today's SC2015 fix) — fixed inline by deleting both,
  closing the sole open todo above in the same session.
