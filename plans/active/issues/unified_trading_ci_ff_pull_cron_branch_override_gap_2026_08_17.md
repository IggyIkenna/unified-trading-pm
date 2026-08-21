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
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
    /plans/active/issues/slot7_unified_trading_ci_foreign_slot12_commit_wrong_branch_2026_08_14.md,
    /plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md,
  ]
created: 2026-08-17
priority: P1
parent_epic: ci_master
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
last_updated: 2026-08-19 # was 2026-08-17 -- stale vs the 2026-08-19 /ao-watchdog entry (the doc's true tail); corrected (plan_reconciler ao)
context_scope:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    scripts/dev/slot-cron-ff-pull.sh,
    scripts/dev/cron-branch-overrides.txt,
    scripts/quality_gates/check_cron_branch_override_parity.py,
    agent-orchestrator/server/autospawn.py,
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

`unified-trading-pm@2b3601a545` (commit timestamp `2026-08-17T06:31:22+01:00` = `05:31:22 UTC` — this repo's
local clocks run +01, so subtract 1h for UTC) — added a `unified-trading-ci main` row to `scripts/dev/cron-branch-overrides.txt` (the file's own
header literally says "Add a row when a repo's canonical integration branch is NOT live-defi-rollout" — this
repo qualified since 2026-08-07 and no one had added it). The cron self-updates this file from
`origin/live-defi-rollout` before every tick, so the fix propagates to every laptop + the orchestrator VM
within one 5-minute cycle of landing, with no manual per-host action needed.

## Verification (2026-08-17, ~05:35-05:42 UTC — real re-check, not assumed clean)

Confirmed the fix actually stopped the storm, not just shipped:

- `cron-branch-overrides.txt` on live `origin/live-defi-rollout` carries the `unified-trading-ci main` row
  (`git show origin/live-defi-rollout:scripts/dev/cron-branch-overrides.txt`).
- Live per-slot re-check on the orchestrator VM (`GET /api/state` + a fresh `git fetch`+ahead/behind on every
  slot's own `unified-trading-ci` clone, run twice ~2 min apart) found **zero NEW divergence** after the fix
  landed: every slot that was still stuck on the stale noise SHA (`403c921...`) at first check either
  self-healed via AO's own `heal_dead_slot_branch_quarantine` between the two checks (slot 10) or was fixed by
  this session's own reconciliation (see below); a re-check of all 14 previously-diverged slots ~2 min later
  showed all still clean (`0 ahead / 0 behind`, `head=c0d10ba6cfe4` = `origin/main` tip) — no re-divergence.
- Last hour of `#agent-orchestrator-alerts` (`slack-read-channel.py agent-orchestrator-alerts 1`, re-pulled at
  `05:41:18Z`): one ambiguous post-fix entry — slot-8 `DIVERGED ahead=3 behind=1` at `05:37Z` — but a direct
  git check of slot 8 taken within ~1 min of that alert (and again 5 min later) showed it clean both times;
  most likely the `slot-git-status-report.sh` reporter (fires `:02/:07/:12…` past the hour) caught a
  transitional moment right as AO's heal cleared it, not a genuine new divergence. No `worktree NOT on
  live-defi-rollout → spawns BLOCKED (FM5/FM7)` page (the actual autospawn-failure page shape from the
  original incident) appears anywhere after `05:31:22 UTC` in the pulled window.
- **Verdict: propagated and holding.** Not 100%-instantaneous (a few minutes of tail-end noise from
  in-flight cron/heal cycles that started before the fix landed), but no evidence of continued re-divergence.

## Idle-slot reconciliation (operator-directed, `ao-watchdog/SKILL.md` § 3g)

Per-slot liveness (`GET /api/state` status + a `tmux list-sessions` cross-check, both fresh) then, for
confirmed-idle slots only, a **verified** fast-forward-only realign (never blind): confirmed the slot's
`unified-trading-ci` HEAD SHA exactly matched a `wip-preserve/slot-<N>-unified-trading-ci-diverged-*` ref
already minted for THAT slot by AO's own auto-heal (`git ls-remote` lookup, not assumed) before discarding
the local pointer, then `git fetch origin main && git checkout -B main origin/main` — the same recovery
`heal_dead_slot_branch_quarantine` itself performs.

- **Reconciled by me** (12 slots — idle or killed, zero live tmux session, dirty=false, HEAD matched the
  known noise SHA `403c921...` exactly, preserve ref verified before touching): **4, 5, 15, 28, 29, 30, 31**
  (status `idle`) and **11, 19, 23, 32, 33** (status `killed`, no live tmux session). All now `0 ahead / 0
  behind` against `origin/main`, re-verified clean ~2 min later.
- **Self-healed-via-AO before I reached it**: **slot 10** — showed `head=c0d10ba...` (already == `origin/main`)
  on my second pass despite being `killed`/idle with no tmux session; AO's own heal cycle (likely triggered by
  an autospawn attempt against the killed slot) fixed it independently in the ~2-3 min between my two checks.
  My script correctly skipped it (head no longer matched the expected pre-fix noise SHA) rather than touching
  an already-clean repo.
- **Already clean, no divergence ever reached them or already resolved by another actor**: slots 6, 8, 13, 20,
  24, 25 — `0/0` at first check. Slot 6 specifically carries a manually-named
  `wip-preserve/slot-6-unified-trading-ci-stale-main-20260817` ref (not AO's own auto-heal naming pattern),
  suggesting another session/agent already reconciled it before this check — left as-is, not re-touched.
- **Still-live-left-alone (per policy — don't touch a live slot's checkout out of band)**: slots **1, 2, 3, 7,
  9, 12, 14, 16, 17, 18, 21, 22, 26, 27** — all showed `slot_status: working` (or `stale` for slot 2, which
  still carries an in-flight `current_task`) with a real dispatched task at check time, and most still carry
  the stale noise SHA in their `unified-trading-ci` clone (harmless — nothing in their current task touches
  that repo). Deliberately not reconciled: these workers were spawned *before* the cron re-diverged their
  checkout mid-task, and touching a live session's clone out of band risks exactly the shared-index/collision
  class this workspace's own multi-agent-safety rules exist to prevent. Their own next
  respawn/resume will run `check_slot_branch_state` fresh and heal cleanly now that the cron is fixed — no
  action needed unless one of them is still showing stale content days from now (would itself be a new,
  separate finding).
- **Genuinely needs operator input**: none. Every diverged slot found was either already self-healing,
  reconciled with a verified-safe realign, or correctly left for its live worker.

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
- [x] [ADMIN] P2. After the fix has propagated, verify no NEW `wip-preserve/slot-*-unified-trading-ci-*`
      branches appear on GitHub and the `#agent-orchestrator-alerts` quarantine pages for this repo have
      stopped. Repo: unified-trading-ci — **verified 2026-08-17 ~05:35-05:42 UTC**: no re-divergence on any of
      14 re-checked slots ~2 min apart, no new FM5/FM7 autospawn-failure page after `05:31:22 UTC`; see
      "Verification" section above. Also reconciled the 12 idle/killed slots still carrying pre-fix stale
      content (see "Idle-slot reconciliation" section) per operator direction.
- [x] ✅ [SCRIPT] P2. Add a CI/QG check asserting every `workspace-manifest.json` repo with
      `integration_branch != live-defi-rollout` has a matching row in `scripts/dev/cron-branch-overrides.txt`
      (mirrors agent-orchestrator's existing `test_branch_state_integration_branch_matches_manifest` pattern for
      registry (A)) — closes the systemic gap, not just this one instance. Repo: unified-trading-pm. —
      **unified-trading-pm@434e3adebc** (2026-08-17). Shipped `scripts/quality_gates/check_cron_branch_override_parity.py`
      (missing/wrong/stale-row detection, mirrors the agent-orchestrator parity-test pattern) + 10 unit tests
      (`test_check_cron_branch_override_parity.py`, incl. a live end-to-end smoke against the real repo files) +
      wired into `quality-gates.sh` alongside the existing manifest-canonical guard. Full `quality-gates.sh` green.
- [ ] [OPERATOR] P3. Decide whether to collapse registries (B)/(C) into a single manifest-driven lookup
      (removes the duplicate-registry class of bug entirely) or keep them separate with the new parity test as
      the guard — design call, not blocking. Repo: unified-trading-pm. **Scope correction 2026-08-19
      (plan_reconciler)**: this doc's own root-cause framing names only THREE registries (A/B/C above), but a
      FOURTH independently hand-maintained copy of the same "what branch does repo X use" fact exists:
      `scripts/dev/slot-git-status-report.sh:312-326` (fixed independently, `unified-trading-pm@b92d9ba52fe`,
      2026-08-11 — the git-status-nudge false-positive fix, see
      `/plans/active/issues/git_status_red_nudge_false_positive_wrong_branch_comparison_2026_08_17.md`). Currently
      correctly populated (no live bug there), but any registry-collapse decision made here should account for
      this 4th copy too, not just (B)/(C).
- [ ] [BACKEND] P2. Add a fleet-wide "N slots quarantined on the SAME repo for the SAME reason" rollup to
      `_alert_branch_quarantine`'s dedup key (`agent-orchestrator/server/autospawn.py:2003`) — today it dedupes by
      `(slot_id, offending-repo-signature)`, correct for a single slot re-alerting on an unchanged problem but with
      no cross-slot/incident-level collapse, so a single systemic root cause hitting 30+ slots simultaneously
      legitimately produces 30+ distinct pages under the current key (each slot's signature is technically novel to
      that slot). The individual pages are policy-correct per `/codex/04-architecture/agent-orchestrator-alerting.md`'s
      classification of quarantine-starving-dispatch as a legitimate PAGE — this is a design change to the dedup
      key/rollup granularity, not a bug fix. Converted from prose ("Left open" item 2 above) into a tracked todo per
      the corpus's "every follow-up is a `- [ ]` todo, never prose" HARD RULE. Repo: agent-orchestrator.
- [ ] [OPERATOR] P3. Reconcile MacBook-Pro slots 6-11's `unified-trading-ci` local `main` (each reporting
      `ahead=49` against `origin/main` in `/api/fleet/git-health`, 2026-08-18 ~16:52 UTC) and Mac slots 0/5-11
      (each `diverged ahead=3/behind=3`, same SHA across all of them). Checked from slot-2/this host: GitHub
      itself shows only a small, stable gap (`origin/main..origin/live-defi-rollout` = 6 commits,
      `origin/live-defi-rollout..origin/main` = 3) and no NEW `wip-preserve/*unified-trading-ci*` branches since
      2026-08-17 — so this is NOT active re-divergence on origin, consistent with residual local-only FF-merge
      pollution from the pre-fix cron bug (same mechanism as the already-reconciled slots in "Idle-slot
      reconciliation" above, just on the two laptop hosts rather than this VM). Not reconcilable from here — Mac
      and MacBook-Pro are separate physical hosts with no SSM/SSH reach from this session. Either their own next
      dispatch/heal cycle self-corrects (`checkout -B main origin/main`, same as `heal_dead_slot_branch_quarantine`)
      once genuinely idle, or an interactive session on those specific laptops reconciles directly per the
      liveness-gated realign recipe already used above. Repo: unified-trading-ci.

## Progress Log

- **2026-08-17 (slot-5, interactive)**: root-caused via SSM live-VM check (confirmed still-firing,
  32 distinct slots, 137 matching activity rows), local reflog inspection of this slot's own
  `unified-trading-ci` clone (7× `merge origin/live-defi-rollout: Fast-forward` onto local `main`,
  2026-08-13→2026-08-17), and direct inspection of all three branch-resolution registries. Shipped the
  one-line data fix to `cron-branch-overrides.txt` (`unified-trading-pm@2b3601a545`) + this issue doc
  (`unified-trading-pm@853926e097`).
- **2026-08-17 (slot-5, interactive, follow-up per operator direction)**: re-verified propagation with fresh
  live measurements (not assumed) — no re-divergence across 14 re-checked slots, no new autospawn-failure
  page post-fix. Reconciled 12 idle/killed slots per `ao-watchdog/SKILL.md` § 3g (liveness-gated,
  preserve-ref-verified realign); 1 slot (10) self-healed independently before reconciliation reached it; 14
  live/working slots deliberately left for their own workers. See "Verification" and "Idle-slot
  reconciliation" sections above for full detail.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-18 (ao tranche)**: KEEP-NA, valid — the sole remaining tracked todo is an explicit [OPERATOR] design call (collapse-registries question), no stated criterion for a worker to pick between the two options. Also converted a prose-only deferred-work item ("Left open" item 2, the alerting cross-slot-dedup gap) into a tracked `- [ ]` todo per the corpus HARD RULE — fixed in this same doc, same turn, per the "misleading doc / undocumented follow-up" finding rule.
- **2026-08-18 (review, slot-2, agt-15d551)**: main (agt-a03340) flagged a new wrinkle during routine
  git-health monitoring — MacBook-Pro slots 6-11 all reporting `unified-trading-ci` `ahead=49` and Mac slots
  0/5-11 all `diverged ahead=3/behind=3` at the same SHA, unusually large/uniform counts. Investigated from
  this session (only origin-reachable checks possible — no cross-host access to the Mac/MacBook-Pro laptops):
  `git fetch` + `rev-list --count` on both directions between `origin/main` and `origin/live-defi-rollout`
  shows only 6/3 commits respectively (small, stable), and `git ls-remote --heads origin 'refs/heads/wip-preserve/*'`
  shows no new `unified-trading-ci` preserve branches since the 2026-08-17 incident's own. Confirms main's
  hypothesis: this is residual local-only content from the pre-fix cron bug, not active re-divergence. Added a
  tracked `[OPERATOR]` todo above since the actual laptop-local checkouts aren't reconcilable from this session.
- **/ao-watchdog 2026-08-19 (interactive, Harsh)**: live `GET /api/state` on the orchestrator VM (host
  `ip-172-31-5-118`, not a laptop) shows slot 0's `unified-trading-ci` still `state=diverged, ahead=3, behind=3,
  not_clean_since=2026-08-11T07:12:03Z` — same shape, same VM host as this doc already tracks, still unresolved
  8 days later. Consistent with the 2026-08-18 "residual, not active re-divergence" verdict above (no new
  `wip-preserve/*` branches, no fresh autospawn-quarantine pages this session) — not treating as a new incident,
  just confirming the residual state persists and the `[OPERATOR]` collapse-registries todo is still the real
  fix. Not touched (slot 0 is `main`, status `working` — live, per this skill's own § 3g rule 1, its own worker
  reconciles in due course, not an outside session).
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-21 (ao tranche batch 3/3)**: KEEP-NA, valid — re-read all 3 open items: the
  registry-collapse question is an explicit `[OPERATOR]` design call (now scoped against 4 registries, not 3); the
  fleet-wide quarantine-alert dedup-key rollup is a genuine design change to alerting granularity, not a bug fix
  (per its own text); the MacBook-Pro/Mac laptop local-`main` reconciliation is cross-host-access-gated, not
  reachable from this session. None clears the bounded/deterministic bar without further scoping.
- **Interactive session 2026-08-21 (laptop `Mac.mynet` / ComputerName "MacBook Pro", slot-5)**: operator
  reported the Cursor SCM badge showing `unified-trading-ci` at 5↓ 7↑ on `live-defi-rollout`. Diagnosed and
  closed the RESIDUAL half this doc's 2026-08-17 fix did not cover.
  - **Fleet state (this host)**: all 12 checkouts — `.tabs/1..11` + the main-workspace clone — were still on
    the retired `live-defi-rollout`, not `main`. The 2026-08-17 `cron-branch-overrides.txt` row
    (`2b3601a545`) stopped the cron *re-diverging* local `main`, but nothing ever *moved* an already-stranded
    checkout, so they had sat there since the 2026-08-07 `integration_branch: main` ruling. Proved
    non-destructive before touching anything: `git diff origin/live-defi-rollout origin/main` is EMPTY (the
    branches are content-identical, SHA-disjoint only), and `git rev-list --branches --not origin/main
    origin/live-defi-rollout` returned 0 for all 12 clones. Switched all 12 to `main` @ `origin/main`; each now
    reports `## main...origin/main`, and a sweep of the other 31 repos × 12 slots confirms every remaining repo
    is correctly on `live-defi-rollout → origin/live-defi-rollout`.
  - **Why it self-perpetuated**: the 5-min cron *detected* it every tick and gave up. Step 0 correctly reset
    `@{upstream}` to `origin/main` (the override row works) but never moves HEAD, so with HEAD still on the
    retired branch the FF logic measured LDR-vs-main and logged `[skip:diverged] unified-trading-ci
    (live-defi-rollout → main) — ahead 7 (1 genuine), behind 5; manual/mirror will handle` — the exact
    7↑/5↓ in the operator's screenshot. Step 5's adopt-rebase refuses because one LDR commit
    (`chore: merge origin/main into live-defi-rollout`) is a merge commit `git cherry` scores `+` genuine.
    "manual/mirror will handle" was a handoff no automation owned.
  - **Root-cause fix shipped — `unified-trading-pm@24106a7374`**: Step 2b **stranded-branch self-heal** in
    `slot-cron-ff-pull.sh`. When HEAD's branch ≠ the resolved `int_branch`, switch to the canonical branch, but
    ONLY when provably nothing is at stake (clean tree AND no commit on HEAD absent from every origin ref AND
    none on the target branch either, since `checkout -B` resets it). Any local work →
    `[skip:stranded-branch] … resolve by hand`, clone untouched. Rebasing deliberately NOT used: it would graft
    the retired branch onto the canonical one. Scoped to fire only when HEAD sits on the fleet-default
    integration branch while the repo's `int_branch` is a per-repo override, so a deliberate feature-branch
    checkout is never yanked. Verified in a clean isolated workspace clone: full bats 380 ok / 0 failures; heal
    run logs `[stranded-branch-fix]` and lands `main...origin/main`; with one genuine unpushed commit it refuses
    (`head_unpushed=1`) and both branch and commit survive.
  - **Two process traps hit while shipping this** (both worth knowing, both cost a full cycle): (1) piping
    `quickmerge` through `tail` makes `$?` the PIPE's exit — a re-gate FAILURE read as success; (2) a
    quickmerge run in this 32-process shared slot reported success and cited a sha, but had amended a PEER's
    commit (`shared_clone_concurrent_commit_message_swap_2026_07_28.md`) and landed NOTHING of ours — caught
    only by grepping the content on `origin`, which is the sole trustworthy check. Committing scoped to the
    owned path (`git commit --only <path>`) before invoking quickmerge is what finally made the work durable
    against this slot's automated pre-reconcile quarantine.
  - **Residual**: the open `[OPERATOR] P3` laptop-reconciliation todo is left UNCHECKED on purpose — this
    session measured and fixed only THIS host; the other laptop was unreachable, so its state is unverified,
    not fixed. It should now converge without an interactive session: the cron self-updates
    `slot-cron-ff-pull.sh` from `origin/live-defi-rollout` every 5 minutes, so once `24106a7374` promotes, any
    host holding a stranded CLEAN checkout heals itself within one sweep. Worth confirming via
    `/api/fleet/git-health` rather than assuming.
  - **Deeper enabler, not addressed (operator call)**: `unified-trading-ci`'s `origin/live-defi-rollout` still
    EXISTS on GitHub despite being retired — which is why `_branch_state.py`'s "ref missing → fall back to
    main" check never fires (its own 2026-08-08 comment says so). Deleting that remote branch would remove this
    entire failure class at the source, but it is a shared-branch deletion and was not done here.
- **FLEET-WIDE MEASUREMENT 2026-08-21** (`/api/fleet/git-health` via the sanctioned read-only SSM path, since the
  endpoint is `AUTHED_DEPS` and 401s unauthenticated from a dev checkout): 74 slots, 1,619 repos, 4 hosts. The
  `unified-trading-ci` row per host — **`MacBook-Pro` 12/12 clean** (this session's host; the "Mac.mynet" hostname is
  ambiguous, the AO's own host label is the reliable one), **`hk` 16/16 clean**, **`ip-172-31-5-118` 33 clean + slot-0
  diverged** (ahead 3 / behind 5), **`Mac` 11 diverged + 1 clean** (ahead 6 / behind 3, `drift_violation: true`).
  So this doc's `[OPERATOR] P3` todo was right that two hosts were involved, but had them mis-scoped: `MacBook-Pro`
  was the one reachable/fixed this session, and **`Mac`** is the one still stranded, plus the orchestrator VM's own
  slot 0. Total still-stranded at measurement time: **12 slots across 2 hosts**.
- **Why those 12 need no cross-host access** (supersedes the "either their own dispatch/heal cycle self-corrects or an
  interactive session on those laptops reconciles" framing): the crontab entry self-updates
  `scripts/dev/slot-cron-ff-pull.sh` from `origin/live-defi-rollout` before every `--all-slots` run, and the Step 2b
  fix is already ON that branch (`24106a7374`) — no promotion to `main` required. Each stranded slot's `ahead=6`
  commits are LDR-only cherry-pick duplicates that DO exist on `origin/live-defi-rollout`, so Step 2b's
  `git rev-list HEAD --not --remotes=origin` guard scores them 0-unpushed and the heal fires; a clone whose tree is
  genuinely dirty correctly refuses instead.
- **DO NOT delete `unified-trading-ci`'s retired `origin/live-defi-rollout` yet** — recorded here because it looks
  like the obvious root fix and is currently the WRONG move. Step 2b's safety guard proves "nothing at stake" by
  finding the stranded HEAD's commits on some origin ref; that ref IS `origin/live-defi-rollout`. Delete it while any
  slot is still stranded and the guard flips to `head_unpushed=6`, refuses, and strands those slots HARDER than
  before. It is only a candidate once every host reports clean — and even then it is an operator call: the
  2026-08-07 ruling (`unified_trading_ci_no_promotion_tiers_divergence_2026_08_07.md`, archived) deliberately chose
  "enforced single-branch + stop pushing to LDR" and reconciled the branches byte-identical rather than deleting.
