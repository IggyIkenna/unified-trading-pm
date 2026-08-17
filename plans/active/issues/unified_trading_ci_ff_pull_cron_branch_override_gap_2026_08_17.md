---
doc_type: issue
title:
  slot-cron-ff-pull.sh's own branch-override registry never got a unified-trading-ci row — every 5-minute
  --all-slots cron tick re-diverged the repo, causing a recurring FM5 branch-quarantine page storm
  (2026-08-17, 03:26-05:1x UTC+, ~30 slots)
summary: >-
  Live incident: #agent-orchestrator-alerts fired a recurring "autospawn failed: branch-state quarantine
  (FM5/FM7), auto-heal failed" page roughly every 5 minutes across 30+ distinct slots (1,4-33), every single
  occurrence scoped to `unified-trading-ci` and never any other repo. Confirmed via SSM this was STILL firing
  at investigation time (05:18:40 UTC healthz timestamp; matching activity-log rows across 32 distinct slots;
  104 `wip-preserve/slot-*-unified-trading-ci-*` branches minted on GitHub, timestamps running up to
  051446Z — seconds before the check). Root cause: THREE independent, un-synced registries in this codebase
  answer "what branch does repo X integrate on" — (A) agent-orchestrator's `_REPO_INTEGRATION_BRANCH` dict
  in `server/worktree_clean_check/_branch_state.py` (fixed 2026-08-08, `agent-orchestrator@8b4c737`, confirmed
  live-deployed — is an ancestor of `origin/live-defi-rollout`); (B) PM's `setup-tab-worktrees.sh`'s
  `base_branch_for_repo()`, which reads `workspace-manifest.json`'s `integration_branch` field dynamically
  (correct, used only at initial slot-repo clone time); (C) PM's `scripts/dev/slot-cron-ff-pull.sh`'s
  `branch_for_repo()`, which reads a SEPARATE hand-maintained flat file
  `scripts/dev/cron-branch-overrides.txt` — NOT derived from the manifest, NOT covered by (A)'s parity test
  (`test_branch_state_integration_branch_matches_manifest`) — and had ZERO row for `unified-trading-ci`.
  That cron runs `*/5 * * * * ... slot-cron-ff-pull.sh --all-slots --quiet` on EVERY host (confirmed in both
  this laptop's `crontab -l` and the orchestrator VM's `crontab -l -u ubuntu`), so every tick defaulted
  `unified-trading-ci` to `live-defi-rollout` and fast-forward-merged that branch into whatever was checked
  out locally (branch `main`, per (B)'s correct clone-time setup) — confirmed directly via this slot's own
  `unified-trading-ci` reflog: 7 repeated `merge origin/live-defi-rollout: Fast-forward` entries onto local
  `main`, 2026-08-13 through 2026-08-17. That stayed harmless while `live-defi-rollout` was a strict superset
  of `main`'s history; once `unified-trading-ci`'s two branches genuinely forked (confirmed: local `main` is
  NOT an ancestor of `origin/main`, 1 commit ahead / 3 behind, `HEAD == origin/live-defi-rollout` exactly),
  every slot's local `main` was permanently polluted with live-defi-rollout-only content — genuinely diverged
  from the CORRECTLY-resolved `origin/main` that (A)'s fixed lookup now (rightly) compares against, tripping
  FM5 quarantine. AO's own heal (`heal_dead_slot_branch_quarantine`) correctly realigns a slot back to
  `origin/main` via `checkout -B`, but the SAME 5-minute cron re-diverges it on its very next tick (until the
  branches are un-FFable, at which point the cron's Step 5 `[skip:diverged]` stops making it WORSE but never
  makes it BETTER either) — explaining the observed "realigned_repos: ['unified-trading-ci']" yet
  "still-quarantined-after-heal" / re-quarantined-within-minutes pattern across the fleet.
status: open
nature: issue
asset_group: [ci, ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator, unified-trading-ci]
scope: [engineer, admin]
tags: [ci-cd, branch-quarantine, autospawn, unified-trading-ci, cron, git, multi-agent-safety, alerting]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /plans/archive/issues/ao_scheduled_job_branch_quarantine_friction_2026_07_28.md,
    /plans/active/issues/slot7_unified_trading_ci_foreign_slot12_commit_wrong_branch_2026_08_14.md,
    /plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md,
  ]
created: 2026-08-17
priority: P1
parent_epic: infrastructure_master
source: >-
  Operator pasted a 03:26-05:01 UTC #agent-orchestrator-alerts dump showing ~20 near-identical "autospawn
  failed" pages across dozens of slots; interactive slot-5 investigation confirmed the page was STILL
  actively firing at 05:14-05:18 UTC (well past the pasted window's apparent end) and root-caused it.
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
depends_on: []
resolved_by: slot-5 (interactive), unified-trading-pm (cron-branch-overrides.txt data fix)
locked_by:
last_updated: 2026-08-17
context_scope:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    scripts/dev/slot-cron-ff-pull.sh,
    scripts/dev/cron-branch-overrides.txt,
  ]
---

# unified-trading-ci FM5 branch-quarantine storm — slot-cron-ff-pull's own override registry never got a row

## What I found (see `summary:` above for the full causal chain — not repeated here)

- **Confirmed still-live at investigation time** (2026-08-17 ~05:15-05:20 UTC), not stopped by 05:01 as the
  pasted Slack dump's apparent end suggested: `/api/healthz` on the orchestrator VM reported
  `"ts":"2026-08-17T05:18:40Z"`; a raw GitHub branch listing on `unified-trading-ci` showed
  `wip-preserve/slot-*-unified-trading-ci-*` branches with timestamps up to `20260817T051446Z`, 12 seconds
  before a `date -u` check; `/api/activity?limit=2000` on the VM had 137 matching
  quarantine+unified-trading-ci rows spanning 32 distinct slots (`1, 4-33`).
- **Not the same bug as `ao_scheduled_job_branch_quarantine_friction_2026_07_28.md`** — that fix (narrowed
  300s recency guard + different-slot retry) was scoped to the `plan_health` scheduled-job dispatch family
  only and is unrelated to this repo/mechanism.
- **Not a regression of the 2026-08-08 `_REPO_INTEGRATION_BRANCH` fix either** — verified that fix
  (`agent-orchestrator@8b4c737`) IS live-deployed (`git merge-base --is-ancestor 8b4c737 origin/live-defi-rollout`
  → yes). The lookup table it fixed is correct today; the bug is in a DIFFERENT, unrelated registry
  (`cron-branch-overrides.txt`) that nothing had ever populated for this repo.
- `workspace-manifest.json` confirms `unified-trading-ci` is the ONLY repo in the fleet with a non-default
  `integration_branch` (`main`, not `live-defi-rollout`) — so this gap could not have silently affected any
  other repo.

## Fix shipped

`unified-trading-pm@<pending-quickmerge-sha>` — added a `unified-trading-ci main` row to
`scripts/dev/cron-branch-overrides.txt` (the file's own header literally says "Add a row when a repo's
canonical integration branch is NOT live-defi-rollout" — this repo qualified since 2026-08-07 and no one had
added it). The cron self-updates this file from `origin/live-defi-rollout` before every tick (see the
crontab's `git show origin/$b:$d` snippet), so the fix propagates to every laptop + the orchestrator VM
within one 5-minute cycle of landing, with no manual per-host action needed. Once the cron stops re-diverging
each slot, AO's existing `heal_dead_slot_branch_quarantine` realign (already correct) should hold across the
fleet without further intervention — self-healing, not something this doc's todos need to force per-slot.

## Left open — recommend as follow-up, not blocking this fix

1. **No regression test protects registry (C) against manifest drift** — (A) has
   `test_branch_state_integration_branch_matches_manifest`; nothing analogous exists for
   `cron-branch-overrides.txt` vs `workspace-manifest.json`, so this exact gap (a repo's manifest override not
   mirrored into the cron's own file) can recur silently the next time a single-branch repo is added. Options:
   (a) add a CI check asserting every manifest `integration_branch != live-defi-rollout` repo has a matching
   `cron-branch-overrides.txt` row [recommended — smallest, mirrors the existing (A) parity test's pattern];
   (b) collapse all three registries into one, having (B) and (C) both read `workspace-manifest.json` directly
   instead of maintaining independent copies (bigger, touches 2 scripts, worth doing eventually but not
   incident-blocking).
2. **Alerting-dedup observation (task step 4)**: `_alert_branch_quarantine` (`agent-orchestrator/server/autospawn.py:2003`)
   dedupes by `(slot_id, offending-repo-signature)`, which is correct for "the same slot re-alerting on an
   unchanged problem" but has NO cross-slot/incident-level collapse — a single systemic root cause hitting 30+
   slots simultaneously legitimately produces 30+ distinct pages under today's dedup key, one per slot, because
   each slot's signature is technically novel to that slot. `/codex/04-architecture/agent-orchestrator-alerting.md`
   classifies the underlying "quarantine starving dispatch" case as a legitimate PAGE (via
   `notify_slot_quarantined`) when walls/backlog are queued — so the individual pages were policy-correct, NOT a
   summary-vs-page doc/reality drift as originally suspected. The real gap is narrower: no fleet-wide "N slots
   quarantined on the SAME repo for the SAME reason" rollup that could have collapsed this into one alert. Not
   fixing this now — flagging as a P2 alerting-hardening idea for whoever owns `agent-orchestrator-alerting.md`
   next, since it's a design change to the dedup key, not a bug.

## Todos

- [x] [SCRIPT] P1. Add `unified-trading-ci main` to `scripts/dev/cron-branch-overrides.txt` so
      `slot-cron-ff-pull.sh` stops defaulting this repo to `live-defi-rollout`. Repo: unified-trading-pm. —
      unified-trading-pm (this session, quickmerge pending).
- [ ] [ADMIN] P2. After the fix has propagated (one cron cycle + one autospawn heal cycle, ~10-15 min), verify
      no NEW `wip-preserve/slot-*-unified-trading-ci-*` branches appear on GitHub and the `#agent-orchestrator-alerts`
      quarantine pages for this repo have stopped. Repo: unified-trading-ci (verification only, no code).
- [ ] [SCRIPT] P2. Add a CI/QG check asserting every `workspace-manifest.json` repo with
      `integration_branch != live-defi-rollout` has a matching row in `scripts/dev/cron-branch-overrides.txt`
      (mirrors agent-orchestrator's existing `test_branch_state_integration_branch_matches_manifest` pattern for
      registry (A)) — closes the systemic gap, not just this one instance. Repo: unified-trading-pm.
- [ ] [OPERATOR] P3. Decide whether to collapse registries (B)/(C) into a single manifest-driven lookup
      (removes the duplicate-registry class of bug entirely) or keep them separate with the new parity test as
      the guard — design call, not blocking. Repo: unified-trading-pm.

## Progress Log

- **2026-08-17 (slot-5, interactive)**: root-caused via SSM live-VM check (confirmed still-firing,
  32 distinct slots, 137 matching activity rows), local reflog inspection of this slot's own
  `unified-trading-ci` clone (7× `merge origin/live-defi-rollout: Fast-forward` onto local `main`,
  2026-08-13→2026-08-17), and direct inspection of all three branch-resolution registries. Shipped the
  one-line data fix to `cron-branch-overrides.txt`.
