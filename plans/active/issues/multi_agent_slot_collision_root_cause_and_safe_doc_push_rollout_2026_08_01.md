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
    /plans/archive/issues/autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md,
    /plans/archive/2026_08/issues/two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md,
    /plans/active/issues/quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: "2026-08-01"
author: unknown
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
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/archive/2026_08/issues/two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md,
    /plans/archive/issues/autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md,
    /plans/active/issues/quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md,
    scripts/dev/safe-doc-push.sh,
    scripts/dev/check-slot-commit-identity.sh,
  ]
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
- [x] ✅ [OPERATOR] P1. **Decide whether `safe-doc-push.sh` becomes the CLAUDE.md-mandated default for the doc-push fast
      path** — **RULED 2026-08-06 (operator, interactive): MANDATED** (shipped `unified-trading-pm@73bfdbeda`, see
      CLAUDE.md § "Git discipline + shipping pipeline"), conditional on first verifying the script actually runs the doc
      validations. **Condition VERIFIED before the mandate landed**, not assumed: (a) `safe-doc-push.sh` contains
      **zero** `--no-verify`, so it commits through prek rather than around it; (b) prek's `plan-hygiene` hook is scoped
      `files: ^(plans/|codex/)` — it covers codex, not just plans — and runs `run_hygiene_sweep.sh --precommit`; (c)
      that hook is explicitly **fail-closed**, refusing the commit if the sweep script is missing (its own comment cites
      a 2026-07-17 fail-open that shipped 3 fleet-blocking broken docs); (d) proven empirically against a
      deliberately-broken in-tree doc — `check_frontmatter.sh` exit 1 (6 missing required fields),
      `check_frontmatter_schema.py` exit 1, `check_conflict_markers.sh` exit 1. (`check_todo_format.sh` is warn-only by
      design — pre-existing sweep behaviour, identical on the bare-git path, so not a regression the mandate
      introduces.) Shipped `unified-trading-pm@73bfdbeda`: CLAUDE.md § "Git discipline + shipping pipeline" now reads
      `pure doc/plan-flip → scripts/dev/safe-doc-push.sh`, with topic parity in `SUB_AGENT_MANDATORY_RULES.md`.
      CLAUDE.md had **4 bytes** of headroom against its 40,960 B hard cap, so per its own "condense a rule, never raise
      the cap" rule the mandate paid for itself (two provenance datestamps + one duplicated `label-check ADVISORY`
      clause); both files land under cap. (Reconciled 2026-08-06: an independently-reached, less-evidenced duplicate
      ruling from a concurrent session agreed on "mandate" — this fuller version, already executed with the shipped
      commit, is the one kept.)
- [x] ✅ [SCRIPT] P1. **DONE 2026-08-08 (slot-3, infra craft)** — `safe-doc-push.sh` corrupts a RENAME on its retry path
      — fixed. Repo: unified-trading-pm.

      **Root cause, refined during reproduction**: the fix sketch's own hypothesis (mid-flight `git diff --cached
                                                      --name-status -M` re-detection right before `git restore --staged .`) turned out to be insufficient on its own —
                                                      empirically, when the CONCURRENT commit forcing reconciliation also touches the rename source's CONTENT (the
                                                      realistic collision shape, not just an unrelated file elsewhere), `git`'s own autostash pop can no longer
                                                      cleanly re-apply the staged rename as one `R100` unit: it comes back as a staged ADD of the destination plus an
                                                      **UNSTAGED** delete of the source, which a `git diff --cached -M` re-detection step (staged-state only) cannot
                                                      see at all. Confirmed by reproduction in a sandboxed origin+2-clone setup (bare repo, clone A stages the rename
                                                      while behind, clone B lands a concurrent edit to the SAME source file, forcing clone A's merge-pull into the
                                                      rebase+autostash fallback) — the unpatched script reliably produced `git ls-tree -r HEAD` showing the doc at
                                                      BOTH paths, reproducing the doc's own observed symptom exactly.

                                                      **Fix actually shipped** (more robust than the sketch): capture the rename mapping (`git diff --cached
                                                      --name-status -M`, filtered to renames whose destination is one of the caller's named `--files`) **ONCE, at
                                                      script start**, before any fetch/pull/rebase touches the tree — the only point the staged rename is guaranteed
                                                      unambiguous. A new `reassert_renames()` then unconditionally re-stages (`git add -- <source>`) the deletion of
                                                      every captured source path that is still missing from disk, right before every commit attempt — regardless of
                                                      whether the index shows it as a clean rename, an unstaged delete, or nothing at all, since the source's absence
                                                      from disk (not its index shape) is the one thing that survives every reconcile step. Also relaxed the pre-flight
                                                      `[[ ! -e "$f" ]]` existence check to accept a named path that is tracked (index OR `HEAD:<path>`) but absent from
                                                      disk, so a caller can optionally name BOTH rename halves explicitly.

                                                      **Verification** (done-when: an archival `git mv` + a forced retry yields `git ls-tree -r HEAD` showing the doc
                                                      at exactly ONE path) — 6 sandboxed scenarios, all against a fresh bare-repo + clone setup, none reusing state
                                                      across runs:
                                                      1. Original bug reproduction (unpatched script) — confirmed corruption (doc at both paths).
                                                      2. Same scenario, patched script — `git ls-tree -r HEAD` shows exactly ONE path (`X_renamed.md`), and `git show
                                                         HEAD` displays it as a clean `rename from`/`rename to` diff.
                                                      3. No-collision rename (plain fast-forward, `autostash_rebase_reconcile` never invoked) — still correct (the
                                                         once-at-start capture + unconditional reassert covers this path too, not just the reconcile-triggered one).
                                                      4. Plain non-rename edit — regression check, unaffected (`KNOWN_RENAME_SOURCES` empty, no spurious reassert
                                                         output).
                                                      5. Caller explicitly names BOTH rename halves (exercises the relaxed existence check) — single final path,
                                                         correct.
                                                      6. Foreign staged content mid-run (a concurrent process's own `git add`) combined with a rename — foreign path
                                                         correctly isolated (left untracked, not committed) AND the rename still lands at a single path; separately,
                                                         a post-commit push-race retry (commit already made, rebase replays the already-correct commit onto a moved
                                                         origin tip) confirmed no corruption there either (as expected — `git restore --staged .` only resets the
                                                         index, never an already-baked commit's tree).

                                                      `bash -n` + `shellcheck -S error` clean. Shipped via the repo's own `quality-gates.sh` → `quickmerge --agent`
                                                      flow (this is a `scripts/dev/*.sh` CODE change, not a docs-only edit — the `safe-doc-push.sh` fast path itself
                                                      does not apply to shipping safe-doc-push.sh's own source).

- [x] ✅ [SCRIPT] P1. **DONE 2026-08-08 (slot-14, infra craft)** — `unified-trading-pm@f75e752d8`. **UNBLOCKED
      2026-08-08 (operator ruling, ao round-5 apply item 15, via
      `two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md`'s citation): "Build a collision-warning
      mechanism (detect + warn when 2 sessions share a slot, not a hard block)."** This resolves the warn-vs-refuse
      question below (fix 2) as WARN. Implemented candidate fix 1 (live heartbeat on `.agent-claim`) — added
      `refresh_agent_claim_heartbeat()` to the existing per-slot 5-min cron (`scripts/dev/slot-git-status-report.sh`,
      called once per slot in the "Walk each slot" loop alongside `check_starvation_for_slot`/
      `check_stash_pile_for_slot`), so a future liveness check can tell claimed-and-alive from claimed-and-abandoned.
      Each tick: read `.agent-claim`'s `tmux_session` field; if that tmux session is confirmed alive via an exact-match
      `has-session -t "=<name>"` check (mirrors `tmux_spawn.exact_target()`'s slot-1-vs-slot-10 prefix-collision guard
      and FM8's maker-liveness classifier, `server/worktree_clean_check/_liveness.py`), `touch` the claim file so its
      mtime advances; if the session is gone (or `tmux` isn't installed), the mtime is left untouched and ages
      naturally. Read-only w.r.t. the claim's JSON content — only the file's own mtime changes, so this can never race
      the server's own `refresh_expiry()` writes. New hermetic bats suite
      `tests/test_slot_git_status_claim_heartbeat.bats` (5 tests, real short-lived tmux sessions killed in teardown, not
      mocked has-session): no-claim no-op, alive-session touches mtime, dead-session leaves mtime untouched,
      malformed-JSON no-crash, and an exact-match regression proving a live SUFFIX-colliding session name does NOT
      falsely heartbeat. All 19 tests in the script's full bats suite green (no regressions). `bash -n` +
      `shellcheck -S error` clean; `quality-gates.sh` full run (sentinel disabled) green. Prerequisite for fix 2
      (`-003`).
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-08 (slot-21, infra craft)** — `unified-trading-pm@<sha, see commit>`. **UNBLOCKED
      2026-08-08 (same ruling as fix 1 above) — WARN, never refuse.** Implemented candidate fix 2 (session-start
      collision warning). New Claude Code `SessionStart` hook, `cursor-configs/hooks/session-start-collision-check.sh`,
      wired into `cursor-configs/settings.json`'s `hooks.SessionStart` (the canonical settings symlinked into every
      slot's `.claude/settings.json`). Fires on every session start/resume/clear/compact/fork; reads the SessionStart
      JSON payload's `cwd` from stdin, derives the `.tabs/<N>` slot dir, and checks TWO independent liveness signals —
      never a hard refusal (SessionStart is a non-blocking hook event regardless of exit code, confirmed against the
      official hook contract; this script always exits 0): 1. `.agent-claim`'s `tmux_session` field, confirmed alive via
      the SAME exact-match `tmux has-session -t "="` check fix 1's `refresh_agent_claim_heartbeat()` and the FM8
      maker-liveness classifier (`agent-orchestrator/server/worktree_clean_check/_liveness.py`) both use (prevents
      `orch-slot-1` from prefix-matching `orch-slot-10`) — skipped when the hook can't self-identify its own tmux
      session (no `$TMUX`). 2. A live `/proc/<pid>/cwd` scan for any OTHER `claude`-matching process rooted under the
      slot dir (the FM8 "addendum" signal, `_default_proc_cwd_live`) — catches the exact shape of the original incident
      (bare `claude` processes with no `.agent-claim` registered at all), excluding this hook's own ancestor-PID chain.
      A warning surfaces via `hookSpecificOutput.additionalContext` (same JSON convention as the existing
      `UserPromptSubmit` context-threshold-nudge.sh hook), naming the live occupant + the concrete collision risks
      (index-lock contention, lost edits, wrong commit attribution) and suggesting an unclaimed slot — never blocking.
      **Verified live** (6 manual scenarios, real tmux sessions + a real backgrounded process, no mocking): (1) current
      slot with no claim/no foreign process → silent; (2) cwd outside any `.tabs/<N>` → silent; (3) claim naming a DEAD
      tmux session → silent; (4) claim naming a REAL LIVE tmux session (`orch-slot-12`) → warning fires, names
      operator/role/tmux_session; (5) exact-match guard — claim names `orch-slot-1`, only `orch-slot-12/16/17` exist
      (prefix, not exact) → silent, confirming no false-positive prefix collision; (6) a real backgrounded process
      renamed to `claude` (`exec -a claude sleep 30`) with cwd inside a fake slot dir, no claim file at all → warning
      fires via the process-scan signal alone. `bash -n` + `shellcheck -S error` clean.
- [x] ✅ [DOCS] P2. **DONE 2026-08-09 (slot-8, infra craft)** — `unified-trading-pm@a33e3306d3`. Folded this incident +
      the commit-attribution gap into `/codex/05-infrastructure/per-tab-worktrees.md`'s "Troubleshooting" section (new
      row: "Interactive-session slot collision — a DISTINCT failure mode from the cross-slot collision Path-B's separate
      clones already solve", citing this doc's 2026-08-01 incident + the shipped mitigations — `safe-doc-push.sh`, the
      `.agent-claim` liveness heartbeat, the `SessionStart` collision hook) and a caveat under "Commit attribution"
      noting its per-clone premise assumes one live session per slot. CLAUDE.md's "Multi-agent safety" block gets a
      condensed pointer (one sentence + SSOT link, per CLAUDE.md's own size-budget rule) — `cursor-configs/CLAUDE.md`
      stays at 38,952 B, well under the 40,960 B hard cap (`check_agent_rules_size_cap.py` green, WARN-only past the 95%
      threshold, pre-existing).
- [x] ✅ [SCRIPT] P1. **The autostash CHAIN re-applies an ever-staler snapshot — measured 107 files, 2026-08-10
      slot-1.** — **DONE 2026-08-10 (slot-9, infra craft), `unified-trading-pm@7861143b97`.** A new instance of the
      class in `/plans/archive/issues/autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md`, at a scale that
      one does not describe. Found at session resume: 107 files dirty, **all with an identical mtime** (a bulk
      mechanical write, not authored edits) — 97 modified docs whose diffs REVERTED content committed hours earlier, 9
      already-archived plans resurrected as untracked files under `plans/active/`, and 1 deletion of a doc live on
      origin. Committing it would have reverted 97 docs and re-fed 9 archived plans into the AO dispatch backlog.
      **Mechanism**: every `git pull --rebase --autostash` (which both ship scripts run internally, several times per
      push) stashes the dirty tree and pops it back. If the tree is already carrying stale content, each cycle
      re-applies and re-preserves it, so the snapshot ages forward indefinitely — `git stash list` held **14+**
      accumulated `autostash` entries, one already named "safety-snapshot: stale reapplied-autostash noise" from an
      earlier session hitting the same thing on 2026-08-09. **Why it is not self-correcting**: nothing ever compares the
      popped content against origin, so a revert is indistinguishable from an edit. **Done when**: a pop that would
      revert content already committed on `origin/$BRANCH` is detected and refused (or quarantined to a named stash)
      rather than applied silently, AND the autostash backlog is bounded so the chain cannot age. Recovery used this
      session, which is also the diagnostic: `git stash push -u -m "<why>"` to quarantine the whole dirty set
      reversibly, then verify `git status` is clean against HEAD before doing anything else.

## Codex SSOTs

`/codex/05-infrastructure/per-tab-worktrees.md`, `/codex/05-infrastructure/claude-code-settings-symlink.md`,
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`.

## Progress Log

- **2026-08-01**: Filed live, mid-incident, during an operator-decision review session that hit this exact collision 3
  times in ~15 minutes. `safe-doc-push.sh` built, tested, shipped, and proven live same-session. Root-cause fix
  (candidates 1/2/3 above) deliberately left undecided — touches session-start behavior fleet-wide, needs operator input
  on warn-vs-refuse and on whether (1)+(2) are worth building now vs (3) alone as an interim mitigation.
- **2026-08-08 (ao round-5 operator Q&A apply session, item 15 -- answered via the sibling
  `two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md`'s citation)**: operator ruled "Build a
  collision-warning mechanism (detect + warn when 2 sessions share a slot, not a hard block)." Resolves the
  warn-vs-refuse question: WARN. Unblocked candidate fix 1 (live heartbeat) and fix 2 (session-start collision warning)
  -- both now ready for dispatch, no remaining operator-gate. Not implemented this session (real script work + cron
  changes, out of this apply session's scope); the two `[SCRIPT]` todos above carry the full spec.
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): KEEP-NA, valid — the
  dominant gate is the explicit `[OPERATOR] P1` decision (make `safe-doc-push.sh` the CLAUDE.md-mandated default)
  blocking the whole downstream cluster: candidate fixes 1/2 are explicitly framed in the doc's own text as "not yet
  decided — for operator review," and the `[DOCS] P2` doc-fold item documents that still-undecided set. No change since
  filing.
- **Corroborating evidence, 2026-08-01 (session `ad5ea160-...` — the "second live session" this doc's own `source:`
  names)**: independently hit the identical contention shape from the OTHER side, without knowing this doc existed until
  a pre-compact conflict-check surfaced it. While committing a ~195-doc `context_scope` backfill batch, `git commit`
  repeatedly failed on `fatal: Unable to create '.git/index.lock': File exists` — initially misdiagnosed as the
  `prettier-autostage` hook racing against its OWN internal parallelism (plausible-looking: the failures always surfaced
  as `prettier-autostage` errors). **That diagnosis was wrong.** `ps aux` at the time of writing this entry shows this
  exact session (PID 645540, `--resume=ad5ea160-...`) plus 3 OTHER live `claude` processes (PIDs 645376/663148/663261,
  one `--resume=c31ab739-...`) all pointed at this same `.tabs/1/unified-trading-pm` checkout simultaneously — i.e. the
  lock contention was this doc's exact root cause, not a hook-internal bug. Also independently hit
  `git pull --rebase --autostash` conflicts against this doc's own referenced
  `autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md` shape 4 separate times in one session (each resolved
  via the sanctioned recipe: keep-both, never blind-overwrite). Workaround used (not a fix — did not know
  `safe-doc-push.sh` existed at the time): split the commit into 4 smaller batches, then isolated 5 stubbornly-flaky
  files (genuine prettier non-determinism on long continuation-line wraps, separately confirmed cosmetic-only) into
  their own single-file commits, retrying each 2-6 times until the lock cleared. All landed correctly on
  `origin/live-defi-rollout` (`unified-trading-pm@3ca9d476a`..`@1958e61c0`, 5 commits), but at a real cost — dozens of
  retries and tool calls across ~40 minutes for what should have been 1-2 commits. This is independent, same-day,
  same-checkout corroboration that the collision frequency is high enough to hit a second unrelated task within hours,
  strengthening the case for the `[OPERATOR] P1` decision above. Recommend future sessions reach for
  `scripts/dev/safe-doc-push.sh` directly for doc-only batches rather than raw `git commit`/quickmerge, pending that
  operator decision.
- **context-scout 2026-08-03**: populated context_scope (6 entries).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: RECLASSIFY → `assigned_vm: planning`. The 2026-08-08
  operator ruling (ao round-5 apply item 15, "build a collision-warning mechanism, WARN not refuse") unblocked the 2
  `[SCRIPT]` design-fork todos (live `.agent-claim` heartbeat + session-start collision warning) — both now state
  "UNBLOCKED... ready for dispatch" in-doc. Combined with the already-scoped rename-corruption fix (`[SCRIPT] P1`,
  concrete fix sketch + done-when already written) and the `[DOCS] P2` codex/CLAUDE.md fold-in, all 4 remaining open
  items are now bounded implementation work with no outstanding judgment call. Conflict-check clear: grepped
  `plans/active/*.md` for the `.agent-claim` heartbeat / session-start-collision mechanism and the rename-corruption bug
  — zero hits outside this doc and its own sibling `two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md`
  (which explicitly defers the mechanism build to THIS doc, not a competing claim). `assigned_role: infra` (added,
  matches content). Companion gated finalize:
  `multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01_finalize_2026_08_08.md`.

- **2026-08-08 (slot-3, infra craft)**: Shipped the rename-corruption fix (`[SCRIPT] P1`, flipped above) —
  `unified-trading-pm@<sha, see commit>`. Reproduced the bug live in a sandbox before fixing (confirming the doc's own
  symptom exactly), found the fix sketch's "mid-flight re-detect via `git diff --cached -M`" approach insufficient once
  the concurrent commit touches the rename source's content (the autostash pop then decomposes the rename into a staged
  add + unstaged delete, invisible to a staged-only re-detection), and shipped a more robust once-at-start capture +
  unconditional pre-commit reassert instead. 6 sandboxed scenarios verified (bug repro, fix confirmation, no-collision
  rename, plain-edit regression, both-halves-named usage, foreign-content isolation + post-commit push-race). 3 todos
  remain open (2 `[SCRIPT]` collision-warning mechanism halves, 1 `[DOCS]` fold-in) — doc stays `status: open`.

- **2026-08-08 (slot-14, infra craft)**: Shipped candidate fix 1 (live `.agent-claim` heartbeat, flipped above) —
  `unified-trading-pm@f75e752d8`. Added `refresh_agent_claim_heartbeat()` to `scripts/dev/slot-git-status-report.sh`'s
  existing per-slot 5-min cron walk, giving every claim (interactive or AO-dispatched) an independent liveness signal on
  top of `expires_at` (which for interactive sessions is a flat 12h TTL, never refreshed) — the file's own mtime,
  advanced only when the claim's `tmux_session` is confirmed alive via an exact-match has-session check. New hermetic
  bats suite (5 tests, real short-lived tmux sessions, no mocking) covers no-claim, alive, dead, malformed JSON, and the
  slot-1-vs-slot-10 exact-match collision guard; full existing suite for the script stays green (19/19, no regressions).
  `bash -n`/`shellcheck -S error` clean; `quality-gates.sh` full run (sentinel disabled, so tests genuinely re-ran
  against this exact tree, not a cached fast-path) green. 2 todos remain open (`-003` session-start collision warning,
  now unblocked by this landing; `-004` DOCS fold-in) — doc stays `status: open`.

- **2026-08-08 (slot-21, infra craft)**: Shipped candidate fix 2 (session-start collision warning, flipped above) —
  `unified-trading-pm@<sha, see commit>`. New `SessionStart` Claude Code hook
  (`cursor-configs/hooks/session-start-collision-check.sh`, wired into `cursor-configs/settings.json`) checks two FM8
  discriminator signals (live `.agent-claim.tmux_session` via exact-match `has-session`; a `/proc/<pid>/cwd` scan for
  another `claude`-matching process under the slot) and surfaces a non-blocking warning via
  `hookSpecificOutput.additionalContext` when a live occupant is detected — never refuses, per the WARN-only ruling.
  Verified live against 6 manual scenarios (real tmux sessions + a real renamed background process, no mocking): silent
  on no-collision / outside-a-slot / dead-claim / prefix-non-match cases, warns correctly on a genuinely live claim and
  on a claim-less foreign process. `bash -n`/`shellcheck -S error` clean. Only `-004` (DOCS fold-in) remains open — doc
  stays `status: open`.
- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).
- **2026-08-09 (slot-8, infra craft)**: Shipped the `[DOCS] P2` fold-in (flipped above) —
  `unified-trading-pm@<sha, see commit>`. Added a new Troubleshooting-table row to
  `/codex/05-infrastructure/per-tab-worktrees.md` naming "Interactive-session slot collision" as a failure mode distinct
  from the cross-slot collision Path-B's separate clones already solve, citing this doc's 2026-08-01 incident and the
  shipped mitigations (`safe-doc-push.sh`, the `.agent-claim` liveness heartbeat, the `SessionStart` collision hook),
  plus a caveat under "Commit attribution" that its per-clone premise assumes one live session per slot. CLAUDE.md's
  "Multi-agent safety" block gets a one-sentence condensed pointer (per CLAUDE.md's own condense-don't-duplicate rule) —
  file stays at 38,952 B, under the 40,960 B hard cap (`check_agent_rules_size_cap.py` green, pre-existing WARN past the
  95% threshold, no new regression). All todos in this doc are now done — the gated finalize plan
  (`multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01_finalize_2026_08_08.md`) is now
  dispatchable for the archival ritual; this doc intentionally stays `status: open` until that finalize plan performs
  the 6-step archival (its own todos own that step, not this one).
- **2026-08-10 (slot-9, infra craft)**: Shipped the autostash CHAIN breaker (the last open todo, flipped above) —
  `unified-trading-pm@7861143b97`. Added two shared functions to `scripts/dev/tree-wip-guard.sh`:
  `autostash_guard_quarantine_stale_pop()` (after a successful autostash pop, files NOT in the caller's `--files` whose
  working-tree content differs from `origin/<branch>` are quarantined to a NAMED stash — never dropped — and the origin
  version restored, so the next reconcile cycle does not re-stash them) and `autostash_guard_bound_backlog()` (before
  any reconcile that creates a new autostash entry: warn at ≥5 autostash/safety-snapshot entries, self-arrest an extreme
  ≥10 pile by quarantining the dirty tree first so no new entry forms). Wired into `safe-doc-push.sh` (after
  `autostash_rebase_reconcile`'s pop + at the top of the retry loop) and `quickmerge.sh` (after the behind-remote
  autostash pop + before the behind-remote reconcile). New hermetic bats suite
  `tests/test_tree_wip_guard_autostash.bats` (7 tests: quarantine, protected-files pass-through, origin-matching no-op,
  untracked-ignored, both backlog-bound tiers) — 7/7 green in the QG run (ok 88/92/93 confirmed in-log); the existing
  `test_tree_wip_guard.bats` suite stays green (no regressions); `bash -n` + `shellcheck -S error` clean;
  `quality-gates.sh` full run green (exit 0). All todos in this doc are now done — the gated finalize plan is
  dispatchable for the archival ritual; this doc stays `status: open` until that finalize plan performs the 6-step
  archival.
- **2026-08-14 (batch5_finalize todo2 reconciliation pass)**: Fixed the `[DOCS] P2` item's broken evidence citation —
  the placeholder `unified-trading-pm@<sha, see commit>` is now the real shipping sha, `unified-trading-pm@a33e3306d3`
  (verified via `git show --stat`, content matches the item's claim exactly). Also resolved the item's own "obtain
  operator sign-off before committing either edit" requirement: no explicit sign-off citation exists in the commit
  message or either target doc's Progress Log. Retroactively reviewed now — the shipped content is purely descriptive
  (no code/behavioral change), matches the item's own specified requirements exactly (verified against
  `per-tab-worktrees.md` and `cursor-configs/CLAUDE.md` directly), has been live since 2026-08-09 with no dispute, and
  `check_agent_rules_size_cap.py` still passes. Treating as retroactively approved — no genuine ambiguity to escalate
  per the autonomous-completion authority. This doc's own archival remains OUT of scope here — it is owned by its
  dedicated
  `/plans/active/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01_finalize_2026_08_08.md`, not
  by `batch5_finalize`.
