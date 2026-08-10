---
doc_type: issue
title:
  ao-self-pull.sh dirty-gate wedged 7+ hours by the main agent's untracked scratch inbox — live orchestrator silently
  ran stale code, no alert fired
summary: >-
  Found live 2026-07-30 while running the operator_gated_blocked_answer_is_a_no_op_2026_07_30.md [REVIEW] E2E
  verification todo: the two D3-ruling backlog tasks it produced would not dispatch. Root-caused to an UNRELATED, more
  severe bug — ao-self-pull.sh (the cron that FF-pulls the root agent-orchestrator checkout serving :8765 and restarts
  it on change) had been dirty-skipping for 28 consecutive ~15-min ticks (~7h), because agents/main.md's documented
  scratch file (`${WORKSPACE_ROOT}/.orch-main-inbox.json`) landed INSIDE the agent-orchestrator repo checkout instead of
  the true workspace root, sat untracked-but-not-gitignored, and permanently failed the dirty-gate. The wedge-alert
  Slack path fired every tick but silently no-op'd (`no webhook`) since `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` isn't
  configured on this host — so nobody was paged while the live orchestrator serving every worker's
  /boot|/heartbeat|/progress|/done calls kept running progressively stale code. Fixed the gitignore gap
  (agent-orchestrator@474d7e0) + an unrelated confounding regen bug found in the same investigation
  (agent-orchestrator@93862de) that was ALSO blocking those two ruling tasks. One manual, one-time step remains: someone
  with real shell access to this host must clear the CURRENT wedge (the fix prevents recurrence, it does not
  retroactively un-wedge the already-dirty file already on disk) — flagged [OPERATOR] below since it needs root-checkout
  access outside any slot worktree's scope.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, deploy-currency, ao-self-pull, dirty-gate, main-agent, gitignore, silent-alert-failure]
related: [/plans/archive/issues/operator_gated_blocked_answer_is_a_no_op_2026_07_30.md]
created: 2026-07-30
author: unknown
priority: P1
parent_epic: orchestrator_master
source:
  "found live 2026-07-30 while executing operator_gated_blocked_answer_is_a_no_op_2026_07_30.md's [REVIEW] E2E
  verification todo (slot 14): two --ruling backlog tasks would not dispatch; root cause traced past a confounding regen
  prereq bug into a 7h+ live ao-self-pull.sh dirty-gate wedge, confirmed via /var/log/ao-self-pull.log tick history +
  git status on the root agent-orchestrator checkout"
execution_scope: local-only
drift_direction: advance-code
depends_on: []
assigned_vm: NA
sequential: false
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    agent-orchestrator/scripts/ao-self-pull.sh,
    /agents/main.md,
    /plans/archive/issues/operator_gated_blocked_answer_is_a_no_op_2026_07_30.md,
  ]
---

# What I found

While running `operator_gated_blocked_answer_is_a_no_op_2026_07_30.md`'s `[REVIEW]` E2E-verification todo, the two
already-materialized `--ruling` backlog tasks (`operator_gated_blocked_answer_is_a_no_op-003--ruling` / `-004--ruling`)
would not dispatch. Investigating why surfaced two independent bugs; this doc covers the more severe one.

## The live orchestrator's own checkout was wedged dirty for ~7 hours

`ao-self-pull.sh` (documented in its own header: FF-pulls the checkout the `orchestrator` systemd service actually runs
`uvicorn server.server:app --reload --reload-dir server` from, restarting on change — the ONLY mechanism that gets a
merged fix live, since the running process is a long-lived Python import, not a per-request subprocess) runs on a
~15-min cron. `/var/log/ao-self-pull.log` on the planning VM showed, at the time of investigation (2026-07-30 ~13:07
UTC):

```
2026-07-30T13:00:01Z ao-self-pull: /home/ubuntu/unified-trading-system-repos/agent-orchestrator is dirty (non-churn) — skip (manual review)
2026-07-30T13:00:01Z ao-self-pull: WEDGE (tree stuck dirty (non-churn) for 28 consecutive ticks — deploy-currency silently frozen regardless of LDR drift distance) — no webhook
```

28 ticks × ~15 min ≈ 7 hours. `git status --porcelain` on the root checkout showed exactly one blocking entry:

```
?? .orch-main-inbox.json
```

## Root cause: a documented main-agent scratch file landing in the wrong place

`unified-trading-pm/agents/main.md` (line ~307) instructs the persistent main agent:

> The moment you drain a NON-EMPTY `messages`, append it to a scratch file (`${WORKSPACE_ROOT}/.orch-main-inbox.json`)
> BEFORE doing anything else, so a mid-tick `/compact` cannot make you forget to answer.

`${WORKSPACE_ROOT}` is used elsewhere in the same doc (`${WORKSPACE_ROOT}/unified-trading-pm/plans/...`) to mean the
true top-level workspace root (`/home/ubuntu/unified-trading-system-repos`), OUTSIDE any git repo. Live, the file landed
at `/home/ubuntu/unified-trading-system-repos/agent-orchestrator/.orch-main-inbox.json` — INSIDE the repo checkout the
orchestrator serves from. Its content (6 real entries, `created_at` 2026-07-30T01:08 through 2026-07-30T04:02, last
`Modify` mtime 04:03:17Z) confirms it is genuinely the main agent's scratch inbox, not a stray/foreign file — the main
agent's own cwd or an unresolved `${WORKSPACE_ROOT}` put it one directory level too deep. (This doc does not fix that
root cause — it belongs to whatever governs the main agent's execution environment — see Recommended decision below.)

Being untracked and NOT covered by `.gitignore`, this single file was enough to fail `ao-self-pull.sh`'s
`git status --porcelain` dirty-gate on every tick, indefinitely — the exact same failure class already hit and fixed
TWICE before in this repo's `.gitignore` (`data/config/accounts.json.bak-pre-sub-*`, found blocking self-pull 2+ hours
on 2026-07-29; the `data/state/` directory-wide ignore, `orchestrator_autonomy_residual_findings_2026_06_02` F1). Every
occurrence of this class is the same shape: a legitimate runtime/scratch artifact nobody remembered to gitignore,
silently freezing deploy-currency.

## The wedge-alert path fired but reached nobody

`ao-self-pull.sh`'s own `_alert_wedge` (drift ≥ `AO_DRIFT_ALERT_COMMITS`, default 10 commits behind) and the dirty-tick
tracker (`_track_dirty_tick`, ≥4 consecutive ticks ≈ 1h) both correctly detected the condition and tried to page —
`_post_wedge_slack_alert` logs `"no webhook"` every time because `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` isn't set in this
host's `.env.local`. The alerting MACHINERY worked exactly as designed; the notification channel itself is unconfigured,
so a real, hours-long, fleet-wide deploy-currency freeze produced zero pages — visible only to whoever happened to read
the log file (this investigation, by chance, while chasing an unrelated dispatch question).

## Why this matters (bigger than the two blocked ruling tasks)

Every code fix any worker ships to `agent-orchestrator` reaches the LIVE dispatcher/regen/API surface only via this
exact FF-pull-and-restart path (there is no other deploy mechanism for this self-hosted repo — confirmed:
`server/routes/backlog.py`'s `/api/backlog/regen` endpoint does an in-process `from .. import regen_backlog_from_plan`,
not a subprocess re-invocation, so a module-level fix genuinely requires the running Python process to reload). For as
long as this wedge held, EVERY agent-orchestrator fix that landed on `live-defi-rollout` was silently NOT live —
including, at the time this was found, my own `fix(backlog): strip stale sequential-chain prereqs...`
(agent-orchestrator@93862de, filed as its own fix below) and potentially others from other slots/tasks in the same
window. A worker or reviewer verifying "shipped to LDR" as proof of "live" would have been wrong for the whole wedge
duration.

# Fixes shipped

- `agent-orchestrator@474d7e0` — added `.orch-main-inbox.json` to `.gitignore` (mirroring the
  `data/config/accounts.json.bak-pre-sub-*` / `data/state/` precedent: this is scratch state that should never be ABLE
  to dirty the tree, not a tracked file that legitimately churns — so gitignoring is the correct fix, not adding it to
  `ao-self-pull.sh`'s `RUNTIME_CHURN_PATHS` stash allowlist, which exists for tracked churning files like
  `data/config/backends.json`). New regression test `test_orch_main_inbox_is_gitignored` in
  `tests/test_state_dir_deploy_safety.py` mirrors the existing `data/state/state.db` coverage assertion.
- `agent-orchestrator@93862de` — the CONFOUNDING regen bug found in the same investigation (unrelated root cause, same
  symptom of "these two tasks won't dispatch"): `_wire_sequential_prereqs` only iterated plans currently in
  `sequential_plan_refs`, so a plan flipping `sequential: true` → `false` left its already-wired same-plan
  `completed_tasks` links in the DB forever. Now strips stale same-plan links on every plan present in the backlog,
  every tick, regardless of its current `sequential` value. 3 new tests in `tests/test_regen_reconcile.py`.

Both landed on `live-defi-rollout` at commit time, but per the section above, LANDING ON LDR IS NOT THE SAME AS LIVE
while this wedge holds — see the todo below for confirming they actually took effect.

# Why it wasn't just resolved on the spot

Clearing the CURRENT wedge (removing/moving the already-on-disk `.orch-main-inbox.json` from the root
`/home/ubuntu/unified-trading-system-repos/agent-orchestrator/` checkout, then letting the next `ao-self-pull.sh` tick
FF-pull + restart `orchestrator.service`, or running it manually) requires write access to a ROOT clone and a restart of
the service every slot/review/main agent depends on. Both are explicitly outside a slot worker's authorized scope per
`unified-trading-pm/agents/RULES.md` § 1 ("Root-repo reads are READ-ONLY... ALL work happens inside your assigned slot
directory... never edit, commit, or run work in root clones") — this is a HARD boundary, not a craft-specific one, so no
worker role (including infra) is authorized to cross it from a slot session. This needs whoever has actual
host/root-clone access (main agent's own session, or the operator).

# Recommended decision

1. Clear the current wedge (one-time, safe, reversible): on the planning VM, as the checkout owner —
   `cd /home/ubuntu/unified-trading-system-repos/agent-orchestrator && git status --porcelain` should show clean once
   the gitignore fix (`474d7e0`) is present on that checkout (a plain `git pull --ff-only origin live-defi-rollout` will
   apply it AND clear the untracked file's dirty status in one step — gitignoring a path that's already untracked
   doesn't require removing the file, `git status` simply stops reporting it). Confirm via
   `systemctl status orchestrator` that `ExecMainStartTimestamp` moves forward after the next tick (or restart manually:
   `sudo systemctl restart orchestrator`).
2. Configure `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` in this host's `.env.local` so the NEXT occurrence of this failure class
   actually pages instead of silently logging — the alerting code path already works, only the channel is missing.
3. Root-cause the main-agent cwd/`${WORKSPACE_ROOT}` resolution gap that put the scratch file inside the repo in the
   first place (separate from this doc's gitignore fix, which only stops it from being ABLE to wedge deploy — it will
   still write to the wrong place until this is fixed).

## Todos

- [x] ✅ [OPERATOR] P1. Clear the current ao-self-pull.sh wedge on the live orchestrator host: confirm
      `agent-orchestrator@474d7e0` + `@93862de` have reached the root checkout at
      `/home/ubuntu/unified-trading-system-repos/agent-orchestrator` (`git log -1`), confirm `git status --porcelain` is
      clean, and confirm `orchestrator.service`'s `ExecMainStartTimestamp` moved forward on the next `ao-self-pull.sh`
      tick (or restart manually) — this requires root-checkout + service-restart access outside any slot worker's scope
      (repo: agent-orchestrator, host-level). — Confirmed live 2026-07-30 17:49 UTC via SSM on i-0c9b283b31d6b5ca7: HEAD
      at `agent-orchestrator@bd522d0` (well past both cited SHAs), `git status --porcelain` empty,
      `origin/live-defi-rollout` ahead=0/behind=0. A second, DISTINCT wedge had independently developed on top of the
      original one — the running uvicorn process had fallen 3 consecutive `ao-self-pull.sh` ticks behind HEAD
      ("stale-process self-heal not resolving") — resolved by the same tick's restart path: new `MainPID=686237`,
      `ExecMainStartTimestamp=2026-07-30 17:49:27 UTC`, verified serving real data (`GET /api/backlog` → 200, 1029
      tasks). Root checkout is current and the live service is proven serving current code, not just current on disk.
- [ ] [OPERATOR] P2. Set `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` in the planning VM's `.env.local` so future
      `ao-self-pull.sh` wedge/drift alerts actually page instead of logging `no webhook` (repo: agent-orchestrator,
      host-level config).

      **PREPARED 2026-08-08 (operator ruling, ao round-5 apply session item 20): "Operator will set it - needs
                                                                  Claude to provide exact file/value/steps."** Verified against the live repo -- `agent-orchestrator/scripts/bootstrap_vm.sh`
                                                                  (lines ~1069-1109) already implements this wiring for a fresh VM bootstrap; this is that same recipe run
                                                                  manually on the already-live planning VM (`i-0c9b283b31d6b5ca7`, EIP 13.113.200.22). Exact file:
                                                                  `${WORKSPACE_ROOT}/agent-orchestrator/.env.local` (systemd EnvironmentFile, read by
                                                                  `server/notifications/slack.py`'s `_WEBHOOK_URL = os.environ.get("AGENT_ORCHESTRATOR_SLACK_WEBHOOK", "")`).
                                                                  The value already lives in GCP Secret Manager (project `central-element-323112`, per
                                                                  `agent-orchestrator/docs/ENV_VARS.md`) -- no new secret needs creating. Run on the planning VM:
                                                                  ```bash
                                                                  cd "${WORKSPACE_ROOT}/agent-orchestrator"
                                                                  WEBHOOK_VAL="$(gcloud secrets versions access latest --secret=AGENT_ORCHESTRATOR_SLACK_WEBHOOK --project=central-element-323112 2>/dev/null)"
                                                                  if [ -z "$WEBHOOK_VAL" ]; then
                                                                    WEBHOOK_VAL="$(gcloud secrets versions access latest --secret=alerting-uts-live-alerts-slack-webhook --project=central-element-323112 2>/dev/null)"
                                                                  fi
                                                                  if [ -n "$WEBHOOK_VAL" ] && ! grep -q '^AGENT_ORCHESTRATOR_SLACK_WEBHOOK=' .env.local 2>/dev/null; then
                                                                    printf 'AGENT_ORCHESTRATOR_SLACK_WEBHOOK=%s\n' "$WEBHOOK_VAL" >> .env.local
                                                                    sudo systemctl restart orchestrator
                                                                  fi
                                                                  ```
                                                                  **Verify**: after restart, confirm `journalctl -u orchestrator --since '5 min ago' | grep -i webhook` shows
                                                                  no fresh "no webhook" lines and a real Slack message lands on the next wedge/drift trigger. Do NOT echo
                                                                  `$WEBHOOK_VAL` to any log.

- [x] ✅ [INFRA] P2. Root-cause why the main agent's `${WORKSPACE_ROOT}/.orch-main-inbox.json` checkpoint (agents/
      main.md) landed inside the agent-orchestrator repo checkout instead of the true workspace root — likely an
      unresolved/unset `WORKSPACE_ROOT` env var or a cwd assumption in the main agent's own session/tooling. Fix so
      future scratch-inbox writes land at the correct absolute path regardless of cwd (repo: unified-trading-pm and/or
      agent-orchestrator, whichever owns the main agent's execution environment). — Root cause confirmed:
      `WORKSPACE_ROOT` is NEVER delivered to the main agent's session — `agents/main.md`'s own "Your boot message
      provides" list (§ near the top) enumerates only `server_url`/`model`/`machine`/`rc_url`/`loop_seconds`, no
      `WORKSPACE_ROOT` — yet the checkpoint instruction (line ~307) referenced the bare `${WORKSPACE_ROOT}` token with
      NO fallback, unlike `worker.md`'s own fresh-pull script which already defends against exactly this with
      `${WORKSPACE_ROOT:-$HOME/unified-trading-system-repos}`. An unset var expands empty in bash, so the resolved path
      is cwd-dependent — landing wherever the main agent's shell happened to be (here, inside the `agent-orchestrator`
      checkout) instead of the true workspace root. Fixed both `${WORKSPACE_ROOT}` usages in
      `unified-trading-pm/agents/main.md` (the scratch-inbox checkpoint line + the `/plan-status` skill's plan-file
      path) to use the same cwd-independent `${WORKSPACE_ROOT:-$HOME/unified-trading-system-repos}` fallback pattern, so
      future writes/reads resolve to the correct absolute path regardless of the main agent's cwd —
      unified-trading-pm@186fb7c57.

# Codex SSOTs

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`,
`/codex/04-architecture/agent-orchestrator-alerting.md` (the actionable-only / dedup convention the wedge-alert already
follows correctly — only the webhook config is missing).

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-02** (infra tranche, incremental run): **KEEP-NA, valid.** First verdict for this doc
  (no prior marker). Read end-to-end; `grep -cE '^- \[ \]'` = **1**, matching this verdict's item count. The sole
  remaining todo is `[OPERATOR] P2` — set `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` in the planning VM's `.env.local` —
  host-level config on a root checkout, explicitly outside any slot worker's authorised scope per `agents/RULES.md` § 1,
  and not a cloud-IAM grant the self-service rule covers. Unambiguous human-only action. **Also flagged**:
  `asset_group: [infrastructure]` with `parent_epic: orchestrator_master` — the first-reported instance (2026-07-31
  finding 3) of the `ao`-mistag deadlock, still unretagged after three audits. Measured this run:
  `generate_na_doc_tranche_inventory.py --tranche ao` returns 61 docs and does not include this one, so the tranche the
  retag is reserved for provably cannot see it. Tranche-level BLOCKED-OPERATOR-DECISION with options recorded in
  `infra_consolidated_closeout_2026_07_25.md`'s 2026-08-02 marker.
- **na-eligibility-audit 2026-08-03** (ao tranche): KEEP-NA, valid — re-affirmed. Doc has 3 total todos, 2 already
  closed; the sole surviving open item is an `[OPERATOR]`-tagged host-level Slack-webhook secret-configuration task on a
  ROOT checkout, explicitly outside any slot worker's authorized scope per `agents/RULES.md` § 1, requiring an external
  credential a worker cannot self-provision. No evidence the webhook has since been configured. **Also closing the loop
  on the mistag deadlock flagged above**: `generate_na_doc_tranche_inventory.py`'s 2026-08-02 fix (`owning_tranche()`'s
  sole-generic-infra-bucket fallback, per that script's own docstring) resolved it — `--tranche ao` now returns 81 docs
  and DOES include this one (confirmed live: this doc is in this run's own Phase 0 in-scope population), so the
  tranche-level deadlock this doc's 2026-08-02 marker flagged no longer applies.
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — deduped a repeated `agents/main.md` entry
  (previously listed both as `/agents/main.md` and `unified-trading-pm/agents/main.md`, the same file); content
  otherwise unchanged and all entries verified to resolve.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **Operator ruling 2026-08-07 (interactive session, via consolidated NA-blocker-digest audit)**: `asset_group` mistag
  RULED — Option B/C combined ("make it correct"). Retagged `[infrastructure]` → `[ao]` directly (this doc is the
  finding-6 original, 5 consecutive days parked as `ag_closeout_audit_infra_parked`'s `BLOCKED-OPERATOR-DECISION`). See
  `ag_closeout_audit_infra_parked_2026_08_07.md` findings 6/18/19 for full cross-finding context — a 3rd instance
  (`ao_deepseek_provider_model_telemetry_mislabeled_2026_08_06.md`) retagged in the same pass; the authoring-time
  default fix (Option C) tracked separately.

- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — sole open item ([OPERATOR] P2, set
  `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` in the planning VM's `.env.local`) remains a host-level secret-configuration action
  on a ROOT checkout, explicitly outside any slot worker's authorized scope per `agents/RULES.md` § 1. No evidence the
  webhook has since been configured.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3)**: KEEP-NA, valid — full re-read of the sole open
  item (set `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` in `.env.local` on the ROOT orchestrator checkout). Explicit hard
  boundary (`agents/RULES.md` § 1: no worker role may edit root clones) — same item cross-referenced in
  `operator_action_items_consolidated_2026_08_08.md`. 5 prior audits agree; no new facts found.
