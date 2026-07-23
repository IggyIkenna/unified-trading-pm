---
doc_type: issue
title:
  "Slot 6 — an unidentified process force-reset 8 repo worktrees mid-session, silently discarding committed-but-unpushed
  work"
summary:
  "While shipping the fleet-wide cryptography GHSA-537c-gmf6-5ccf floor bump, 6 (later confirmed via a second hit,
  effectively an active/recurring pattern) of slot 6's committed-but-unpushed local commits were silently wiped by a
  `git checkout -B <branch> origin/<branch>`-shaped operation (reflog: `branch: Reset to origin/live-defi-rollout`)
  across unified-trading-library, instruments-service, execution-service, client-reporting-api, strategy-service,
  deployment-service — and unified-trading-library was hit a SECOND time ~5 minutes after the first recovery. All
  commits were recoverable via `git cherry-pick <dangling-sha-from-reflog>` since the commit objects were still in the
  local object DB, but this is a live data-loss risk for any mid-session agent with local-ahead commits, and directly
  contradicts `slot-cron-ff-pull.sh`'s own documented contract ('Never destructive. Never runs reset --hard. Skips:
  dirty / ahead / diverged / detached.')."
status: superseded
superseded_by: plans/active/issues/slot11_silent_branch_reset_data_loss_2026_07_13.md
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    unified-trading-library,
    instruments-service,
    execution-service,
    client-reporting-api,
    strategy-service,
    deployment-service,
  ]
scope: [engineer, admin]
tags: [multi-agent-safety, data-loss, git, per-tab-worktrees, incident]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    plans/active/issues/slot11_silent_branch_reset_data_loss_2026_07_13.md,
  ]
created: 2026-07-13
parent_epic: infrastructure_master
priority: P1
source: fleet_hygiene_crypto_ghsa_mtds_baseline_2026_07_13 (discovered while shipping)
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
assigned_role: infra
model_tier: opus-required
thinking_tier: high
drift_direction: advance-code
depends_on: []
---

## What I found

While shipping 17 repos' worth of `pyproject.toml`/`uv.lock` cryptography-floor-bump commits from slot 6 (`.tabs/6/`), I
observed the following sequence in each affected repo's `git reflog`:

```
<my-commit-sha> HEAD@{15:0X:XX}: commit: fix(deps): bump cryptography floor off GHSA-537c-gmf6-5ccf ...
<origin-tip-sha> HEAD@{15:2Y:YY}: branch: Reset to origin/live-defi-rollout
```

The `branch: Reset to <ref>` reflog message is what git records for `git checkout -B <branch> <start-point>` (force
re-pointing an existing branch to a new start point while checked out on it) — NOT a plain `git reset --hard` (whose
reflog message is `reset: moving to <ref>`), and NOT anything `slot-cron-ff-pull.sh` does per its own header comment
("Never destructive. Never runs `merge --no-ff`, never `rebase`, never `reset --hard`. ... Skips: dirty / ahead /
diverged / detached."). Something else — I could not identify the exact process from within the agent session (no
crontab read permission, no matching systemd timer, no PID caught mid-act) — is running a `checkout -B` style repair
against slot 6's worktrees on roughly a 5-minute-ish cadence and evidently does NOT correctly detect "local branch is
ahead of origin with real commits" as a skip condition, unlike what `slot-cron-ff-pull.sh` claims to do.

**Affected repos (commits actually lost, recovered via cherry-pick):** `unified-trading-library`, `instruments-service`,
`execution-service`, `client-reporting-api`, `strategy-service`, `deployment-service`. `unified-trading-library` was hit
**twice** — once at 15:27-ish (wiping my first commit `c0c65c2c`/`fd75d128`), and again at 15:33:26 (wiping my recovery
cherry-pick `fd75d128` a second time, after which I re-recovered as `b65cf8d2` and pushed it within ~60s of the QG
finishing, before a third sweep could hit it).

**Repos NOT affected** (in the same session, same timeframe, same slot): `market-tick-data-service`,
`unified-trading-pm`, `market-data-processing-service`, `unified-trading-api`, `batch-live-reconciliation-service`,
`trading-agent-service`, `deployment-api`, `ibkr-gateway-infra`, `system-integration-tests`,
`fund-administration-service`, `e2e-testing` — either because I'd already pushed them before the sweep, or the sweep
just didn't touch every repo in a given pass (unclear which).

## Why it matters

This is a live risk for the entire multi-agent fleet: ANY slot with a committed-but-unpushed commit (the normal state
between `git commit` and the QG-gated `quickmerge` push — which can be minutes long for large repos) can have that
commit silently discarded with zero error, zero warning, and zero visible signal to the agent unless it happens to
`git status`/`git log` at exactly the right moment. I only caught this because I was doing systematic sentinel-match
verification across 17 repos as part of a large batch ship. A smaller, single-repo task would likely never notice — the
agent would just see its own commit "disappear" and might assume it never committed, silently losing real work with no
error surfaced anywhere.

This directly contradicts the HARD RULE in workspace `CLAUDE.md` § "Multi-agent safety": "**Never** ... force-push a
shared branch" and the `slot-cron-ff-pull.sh` design contract itself ("Never destructive... Skips: dirty / ahead /
diverged / detached").

## Recommended decision

1. Identify the actual process doing this (search server-side / VM-side for anything running `git checkout -B` or
   `git branch -f` against `.tabs/*/` worktrees — candidates per `/codex/05-infrastructure/per-tab-worktrees.md`: the
   orchestrator's structural pre-spawn branch-state gate (`worktree_clean_check.check_slot_branch_state`, described in
   `unified-trading-pm/agents/worker.md` as "repairs a stale upstream + FFs when behind and QUARANTINES a
   detached/wrong-branch/diverged clone") is the most likely candidate given it explicitly "repairs" branch state, and
   may be firing on a periodic health-check pass mid-session (not just pre-spawn) and misclassifying "ahead with real
   commits" as a state needing repair.
2. Fix the ahead-detection: any repair/FF logic MUST skip a slot repo whose branch is ahead of
   `origin/<integration-branch>` (`git rev-list --count origin/<branch>..HEAD` > 0) exactly like `slot-cron-ff-pull.sh`
   already claims to.
3. Consider whether the fix should also cover the case where a slot is BOTH ahead and behind (rebase needed, not reset)
   — that's what an agent's own fresh-pull loop already handles correctly via `git merge --ff-only` (refuses rather than
   resets).

## Todos

- [x] ✅ [INFRA] P1. Identify the process doing `checkout -B <branch> origin/<branch>` against per-slot worktrees
      mid-session and fix its ahead/diverged detection so it never discards local commits — DONE via the superseding
      master doc `slot11_silent_branch_reset_data_loss_2026_07_13.md` UPDATE 7 + todos 1/2. Root cause:
      `heal_dead_slot_branch_quarantine()` (`agent-orchestrator/server/worktree_clean_check/_branch_state.py`) issuing
      `git checkout -B <base> origin/<base>` — empirically the exact `branch: Reset to origin/<base>` reflog signature
      this doc reported (its code comment falsely claimed the form was reflog-silent). Fix shipped
      `agent-orchestrator@911036c4`: `_MIN_AHEAD_COMMIT_AGE_SECONDS_FOR_REALIGN = 900` recent-commit guard
      (`_branch_state.py:383`, param `min_ahead_age_seconds`) — refuses to touch (genuine no-op, leaves quarantined for
      the `_alert_branch_quarantine` human-page path) any stop-state repo whose HEAD commit is younger than 15 min, so a
      live/heartbeating worker with a stale claim file no longer has its fresh commit discarded. 2 unit tests, full
      suite green. Verified 2026-07-14 (slot 4): guard present at `_branch_state.py:383,460-476` + `911036c4` is an
      ancestor of `origin/live-defi-rollout`. (Todo 2 below — the backward-HEAD-movement canary/alert — is a separate
      P2, not yet done.)
- [x] ✅ [INFRA] P2. Add a canary/alert: if a slot's local HEAD for a repo the slot has an in-flight task on ever moves
      backward (loses a commit that was previously at HEAD) without the agent's own git action causing it, page — this
      class of failure is currently silent. — DONE `agent-orchestrator@5297819` (slot 12, 2026-07-14). Shipped
      `server/head_backward_canary.py` — a `HeadBackwardCanary` daemon (started in `server.py` lifespan, cadence
      `ORCHESTRATOR_HEAD_BACKWARD_CANARY_INTERVAL_SECONDS`, default 180s) that scans every `.tabs/<slot>/<repo>` reflog
      for the out-of-band `branch: Reset to origin/<branch>` fingerprint discarding a `commit:` now reachable from
      neither HEAD nor origin (the exact `AT_RISK_REFLOG_ONLY` signature `audit-fleet-reflog-resets.sh` classifies), and
      pages `notify_head_backward_dataloss` (new, `notifications/slack.py`) with the per-clone `git cherry-pick <sha>`
      recovery. First-tick-baselined + disk-persisted seen-set dedup (`dedup_state.head_backward_canary_*`) so it pages
      each NEW loss exactly once and never re-pages the ~276-hit historical backlog (UPDATE 3) or floods on a restart.
      Read-only wrt every slot clone. Deliberately scans ALL slot repos (not just DB-"in-flight" ones) because the
      claim/tmux liveness that defines "in-flight" is precisely what false-negatives a live worker (UPDATE 7) — gating
      on it would blind the canary to the case it exists to catch. 7 unit tests (`tests/test_head_backward_canary.py`),
      full `quality-gates.sh` green (1276 passed, sentinel `4319e577`). Alerting SSOT
      `/codex/04-architecture/agent-orchestrator-alerting.md` updated (new PAGE row). This was the last open todo in
      this doc — both P1 (Todo-1 realign guard) and this P2 (Todo-2 detection canary) are now shipped.

## Progress Log

- **2026-07-13 (slot-6, sonnet/high)** — Discovered while shipping `fleet_hygiene_crypto_ghsa_mtds_baseline_2026_07_13`
  todo 1 (cryptography floor bump, 17 repos). Recovered all 6 lost commits via `git cherry-pick` from dangling SHAs
  still in each repo's reflog/object DB (none were unrecoverable). All 16 shippable repos' fixes are now confirmed on
  `origin/live-defi-rollout` via `git merge-base --is-ancestor`. Filed this issue for the operator/infra owner to
  investigate root cause — I do not have the access from within this agent session to identify the exact process.
- **2026-07-13 (slot-6, sonnet/high)** — Main confirmed this is the SAME actively-firing mechanism already tracked
  fleet-wide in `plans/active/issues/slot11_silent_branch_reset_data_loss_2026_07_13.md` (18 at-risk commits across the
  fleet as of that session). Marking this doc superseded — the 8-repo/6-commit evidence above is additional
  corroboration for the master doc, not a separate incident. A follow-up fleet-wide audit also flagged 3 more
  possibly-at-risk commits in this slot's clones (instruments-service `0a34152a`, market-tick-data-service `b9cb1aa2`,
  unified-trading-pm `510be6e9a`); investigated all 3 and none needed recovery — each is a redundant duplicate of work
  already shipped independently (data_type=instruments fix already live + its issue doc already `status: resolved`;
  BITFINEX-SPOT/FUTURES connectors already exist with tests; the fastapi-ceiling issue already tracked+resolved via a
  different doc). See `slot11_silent_branch_reset_data_loss_2026_07_13.md` for the consolidated root-cause
  investigation.
