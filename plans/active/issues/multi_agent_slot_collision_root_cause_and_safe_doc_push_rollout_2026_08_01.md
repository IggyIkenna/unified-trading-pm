---
doc_type: issue
title:
  Multiple concurrent agents observed sharing ONE slot's checkout (`.tabs/1`) live, causing repeated git contention,
  lost/re-fought edits, and wrong commit attribution — safe-doc-push.sh built + shipped to harden the doc-push symptom;
  the slot-collision root cause itself is still open
summary: >-
  Live-observed 2026-08-01: up to 6 concurrent `claude` processes were simultaneously pointed at
  `/active/unified-trading-system-repos/.tabs/1` (at least two distinct operators — this session's user and
  `harshkantariya [slot-1·harsh_pc]`), all sharing the exact same `.git` directory (one index, one HEAD, one set of
  refs, one `user.name`/`user.email` config). This is not a rare edge case — it reproduced 3 times in ~15 minutes during
  this session alone, and matches a pattern already documented 2.5 weeks earlier
  (`two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md`, 3 recurrences on 07-15/16/17) plus a long
  string of quickmerge-contention issue docs
  (`quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md` and its archived siblings). Symptom
  fixed this session: `scripts/dev/safe-doc-push.sh` (shipped `unified-trading-pm@0e48d252f`) gives the
  CLAUDE.md-sanctioned "pure doc/plan-flip -> prek only" fast path the same contention-hardening quickmerge.sh already
  has for code (fetch/reconcile/stage-by-name/foreign-content-isolation/ retry), so an agent no longer has to manually
  re-fight a collision from scratch every time one happens. Root cause NOT fixed: nothing currently stops multiple live
  agents from landing in the same slot's checkout in the first place (`.agent-claim` exists but is a static timestamp,
  not a live heartbeat, and nothing checks it at session start) — also newly observed as a consequence: commit AUTHOR
  ATTRIBUTION is wrong whenever two operators share one slot, since `user.name`/`user.email` in `.git/config` is also
  shared state (this session's own dogfood-test commit, content correct, landed under `harshkantariya`'s identity
  instead of this session's operator).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [multi-agent-safety, slot-collision, git, contention, throughput, commit-attribution, per-tab-worktrees]
related:
  [
    /plans/active/issues/autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md,
    /plans/active/issues/two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md,
    /plans/active/issues/quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-01"
priority: P1
parent_epic: agent_operating_framework_master
source: >-
  Live incident during this session's operator-decision review, 2026-08-01: `ps aux` showed up to 6 concurrent `claude`
  processes against `.tabs/1` (PIDs observed: 1204697/ad5ea160 [ended mid-session], 3366101/ad5ea160 [respawned],
  3411511 [fresh, no --resume], 3411880/c31ab739 [this session], 2722922 [interactive terminal], 3382569/0445ab77 [root
  unified-trading-pm, separate clone — not itself a collision]). Two distinct operator identities landed commits in the
  same window: this session (via safe-doc-push.sh) and harshkantariya [slot-1·harsh_pc]'s session (context-scout
  backfill batches 1-5, na-eligibility-audit sweeps, the batch2->batch4 rename fix, and a prettier-corruption fix — all
  independently verified correct and already on origin).
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

# Multi-agent slot collision — symptom fixed, root cause still open

## What actually happened (verified live, not inferred)

During this session, editing a single one-line annotation in `ao_open_issues_consolidated_close_out_2026_07_17.md`
required recovering the same edit from a `git stash` autostash entry TWICE, and a raw `git commit` failed on
`fatal: Unable to create '.git/index.lock': File exists` — because a second live Claude Code session
(`harshkantariya [slot-1·harsh_pc]`, resumed session `ad5ea160-...`) was actively running its own
`git pull --rebase --autostash` cycles, context-scout backfill commits, and an na-eligibility-audit sweep in the **exact
same checkout** at the same time. `ps aux` at the peak showed 6 concurrent `claude` processes all pointed at `.tabs/1`.
This is not "two slots colliding" (the architecture the per-tab-worktrees model defends against) — this is **multiple
operators/sessions sharing ONE slot's single clone**, which the architecture has no defense against at all, because
`assigned_vm`/slot allocation only governs AO-DISPATCHED workers; nothing allocates or protects an INTERACTIVE session's
slot choice.

## Why this is bigger than one bad edit

- **Every doc-push collision costs real tokens and turns** — this session spent ~15 minutes and dozens of tool calls
  manually re-deriving the exact defensive git dance (fetch, overlap-check, correct pull strategy, stage-by-name,
  detect-and-strip foreign staged content, retry) from first principles, because nothing automates it. That dance is now
  scripted (`safe-doc-push.sh`) — but the COLLISION FREQUENCY itself is untouched by that fix. A faster recovery from
  contention is not the same as less contention.
- **Wrong commit attribution**: this session's own dogfood-test commit (`unified-trading-pm@0e48d252f`, content
  independently verified correct) landed under `harshkantariya`'s author identity, not this session's operator, because
  `.git/config`'s `user.name`/`user.email` is shared state in a shared checkout. `check-slot-commit-identity.sh` audits
  this per the "commit attribution = slot + host" rule, but that rule's own premise ("each slot clone has its own
  `.git/config`, set at clone time") is violated the moment two operators share one slot.
- **Documented recurrence, not a one-off**: `two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md`
  recorded the identical failure shape 3 times in 3 days (07-15/16/17) two and a half weeks ago, and its own Progress
  Log already named the fix this doc is now re-proposing ("each slot = ONE agent... not something either concurrent
  session can enforce on its own"). The gap between "documented" and "fixed" is exactly this doc's subject.

## Root cause

Slot allocation for AO-DISPATCHED workers is programmatic (role-based dispatch, backend-managed). Slot allocation for
INTERACTIVE sessions (a human opening a terminal / IDE tab and starting Claude Code) has **no equivalent mechanism** —
an operator just `cd`s into whichever `.tabs/N` they have open, and nothing warns them (or the session itself) if that
slot is already claimed by another live process. The `.agent-claim` file that exists per slot
(`/active/unified-trading-system-repos/.tabs/1/.agent-claim`, observed `last modified Jul 29` — i.e. 3+ days stale at
the time of this incident) is a **static marker, not a liveness heartbeat**, so even a script that checked it could not
have told "claimed and alive" apart from "claimed and abandoned weeks ago."

## Candidate fixes (not yet decided — for operator review, this touches session-start behavior fleet-wide)

1. **Live heartbeat on `.agent-claim`**: extend the existing per-slot 5-min cron (`slot-cron-ff-pull.sh` /
   `slot-git-status-report.sh`, already running per CLAUDE.md's "Multi-agent safety" section) to also touch
   `.agent-claim`'s mtime, so "claimed" and "alive within the last ~5 min" become distinguishable.
2. **Session-start collision check**: a lightweight script (or a `direnv`/shell-rc hook) that, when a new interactive
   Claude Code session starts in a `.tabs/N` directory, checks `.agent-claim` liveness (via the FM8 discriminator
   already used elsewhere in this codebase for dead-vs-live slot claims — tmux-session existence / `/api/state` liveness
   / `/proc/<pid>/cwd`) and prints a loud warning (not necessarily a hard refusal — an operator may deliberately want
   two sessions for a review pass) if the slot is already live-claimed by a different process.
3. **Operator-side convention**: simplest, zero-build fix — before opening a new terminal/Claude session, check
   `ls -la .tabs/*/.agent-claim` (or a future liveness-aware variant of it) and pick an unclaimed slot. Cheap, but
   depends on habit, not enforcement — likely worth doing as an IMMEDIATE mitigation regardless of which of (1)/(2) also
   gets built.

## Todos

- [x] ✅ [SCRIPT] P1. **Build + ship a contention-hardened wrapper for the docs-only fast path.** — **DONE 2026-08-01,
      `unified-trading-pm@0e48d252f`.** `scripts/dev/safe-doc-push.sh`: fetch + reconcile (merge-pull pre-commit /
      rebase+autostash+`restore --staged` post-commit, per the decided fix in
      `autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md`) + stage-by-name + defensive foreign-content
      isolation + bounded retry with backoff. Validated in a sandboxed clone against 3 scenarios (true fast-forward
      zero-overlap; a foreign file staged into the shared index mid-run, correctly isolated not swept in; post-commit
      drift forcing the rebase+restore-staged retry) — all pass, shellcheck-clean — then dogfooded live against the
      actual contested `.tabs/1` checkout (5 concurrent sessions active at the time) and succeeded on the first attempt.
- [ ] [OPERATOR] P1. **Decide whether `safe-doc-push.sh` becomes the CLAUDE.md-mandated default for the doc-push fast
      path** (replacing the current bare "prek only" direct-git guidance in the "Git discipline + shipping pipeline"
      section), or stays an optional tool agents can reach for. Fleet-wide behavior-guidance change — needs sign-off
      before every agent's standing instructions change.
- [ ] [SCRIPT] P1. **Implement candidate fix 1 (live heartbeat on `.agent-claim`)** — extend the existing per-slot 5-min
      cron to refresh `.agent-claim`'s mtime, so a future liveness check can tell claimed-and-alive from
      claimed-and-abandoned. Prerequisite for fix 2.
- [ ] [SCRIPT] P2. **Implement candidate fix 2 (session-start collision warning)** — once fix 1 lands, add a
      liveness-aware check (reuse the FM8 discriminator pattern) that warns loudly when a new interactive session starts
      in an already-live-claimed slot. Needs an operator ruling on warn-vs-refuse first.
- [ ] [DOCS] P2. Fold this incident + the commit-attribution gap into `/codex/05-infrastructure/per-tab-worktrees.md`'s
      "Troubleshooting" section and CLAUDE.md's "Multi-agent safety" block — currently neither documents "two operators
      sharing one slot" as a distinct failure mode from "two AO slots colliding on a file."

## Codex SSOTs

`/codex/05-infrastructure/per-tab-worktrees.md`, `/codex/05-infrastructure/claude-code-settings-symlink.md`,
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`.

## Progress Log

- **2026-08-01**: Filed live, mid-incident, during an operator-decision review session that hit this exact collision 3
  times in ~15 minutes. `safe-doc-push.sh` built, tested, shipped, and proven live same-session. Root-cause fix
  (candidates 1/2/3 above) deliberately left undecided — touches session-start behavior fleet-wide, needs operator input
  on warn-vs-refuse and on whether (1)+(2) are worth building now vs (3) alone as an interim mitigation.
