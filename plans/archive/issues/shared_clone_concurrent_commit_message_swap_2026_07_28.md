---
doc_type: issue
title:
  Two concurrent `git commit` invocations in the SAME shared unified-trading-pm clone can produce a commit whose message
  belongs to the OTHER process while the tree content is the committing process's own staged files — a
  commit-message/content mismatch, not data loss
summary: >-
  While shipping two unrelated checkbox-flip + archival commits to `unified-trading-pm` on `live-defi-rollout`
  (`.tabs/4`, slot-4), a `git commit -m "docs(plans): flip sports-staleness + cloud-build-timeout items..."` call
  succeeded (prek hooks passed) but the resulting commit (`7d8d690b6`, later rebased from `d64190bb0`) carries the
  commit message `fix(infra): hard RLIMIT_AS fallback in run-bounded-analysis.sh...` — a DIFFERENT, unrelated commit
  message that another concurrent agent process (same slot-4 identity, i.e. a different Claude Code session/sub-agent
  sharing this exact working directory) was evidently committing at the same moment. Verified via `git show --stat
  <sha>`: the commit's actual diff is exactly my 3 intended files
  (`plans/active/issues/sports_manifest_read_staleness_budget_missing_2026_07_15.md`,
  `plans/active/issues/cloud_build_evidence_citation_short_hash_unresolvable_2026_07_27.md`, and the active->archive
  rename of `deployment_api_cloud_build_600s_timeout_flake_2026_07_27.md`) — NOT `scripts/dev/run-bounded-analysis.sh`.
  That file's own RLIMIT_AS content was confirmed still present, uncommitted, in the working tree afterward (`git status
  --porcelain` showed ` M scripts/dev/run-bounded-analysis.sh`), so the other process's real work was NOT lost — it was
  simply left staged-then-unstaged (I explicitly `git restore --staged` it per the "never commit a foreign file" rule)
  and its author will presumably re-commit it under a correct message later. The defect is purely the COMMIT MESSAGE
  attaching to the wrong TREE, most likely because `git commit -m "..."` and prek's hook chain read/wrote a shared
  per-repo file (candidate: `.git/COMMIT_EDITMSG`, or a prek/pre-commit temp-patch/stash race — several `Unstaged
  changes detected, stashing unstaged changes to /Users/.../.cache/prek/patches/<ts>-<pid>.patch` / `Restored working
  tree changes from` lines were observed during these same attempts) at the exact moment two `git commit` calls in the
  same `.git` overlapped.
status: resolved
nature: issue
asset_group: [infrastructure, meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [git, race-condition, shared-clone, multi-agent, commit-message, prek, per-tab-worktrees, evidence-integrity]
related:
  [
    /plans/archive/issues/quickmerge_silent_push_failure_under_contention_2026_07_27.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: 2026-07-28
last_updated: 2026-07-28
parent_epic: infrastructure_master
priority: P1
source:
  "code_quick_cross_repo_fix_backlog_2026_07_28.md worker (slot-4, deployment-api items: sports staleness-budget mirror
  + cloud-build timeout raise), 2026-07-28 — discovered while flipping the source-doc checkboxes in unified-trading-pm
  and archiving one resolved issue doc; observed 3 consecutive commit-drift/hook-failure retries on the same 3-file
  commit, the 3rd of which landed with a foreign commit message."
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
locked_by:
resolved_by:
  '2026-07-30 — root-caused via direct reproduction (COMMIT_EDITMSG is an unlocked, shared, cross-invocation file; index
  and HEAD are properly guarded, prek''s patch-stash is PID-namespaced, both ruled out). Discipline + mechanism
  documented in /codex/05-infrastructure/per-tab-worktrees.md § "What worktree isolation does NOT cover" item 3
  (unified-trading-pm@71c55ed6a); todo flipped unified-trading-pm@50f727f9e. Sibling P3 mitigation (quickmerge.sh
  WARN-on-mismatch) already shipped. Every todo done, unlocked — archived same session per
  /codex/12-agent-workflow/plan-completion-and-archival-discipline.md.'
depends_on: []
---

> **🟢 ARCHIVED 2026-07-30** — status=resolved, archived per /codex/11-project-management/issue-doc-lifecycle.md's
> archive-on-resolve rule. Both todos are `[x]`: the root cause is `.git/COMMIT_EDITMSG` racing (confirmed by direct
> reproduction), the discipline + full mechanism now live in `/codex/05-infrastructure/per-tab-worktrees.md` § "What
> worktree isolation does NOT cover" (item 3), and the cheap technical mitigation (WARN-on-mismatch, not auto-amend)
> already shipped in `scripts/quickmerge.sh` via the sibling P3 todo below.

# Concurrent same-clone `git commit` calls can swap commit MESSAGES (not content)

## What I found

Working in `unified-trading-pm` on `.tabs/4` (slot-4) — a clone that, per
`/codex/05-infrastructure/per-tab-worktrees.md`, is shared by potentially many concurrent agent sessions/sub-agents
dispatched to the same tab — I hit branch-drift rejections + a prettier auto-fix retry across 3 attempts to commit 2
unrelated checkbox-flip edits + 1 file archival (rename). On the 3rd attempt the commit succeeded (all prek hooks green)
but `git log -1` / `git show --stat HEAD` showed:

- **Commit message**:
  `fix(infra): hard RLIMIT_AS fallback in run-bounded-analysis.sh when systemd-run --user is unavailable` (mentions
  `mdps_candle_manifest_population_disconnect_2026_07_25.md todo 9`) — a topic I never touched.
- **Commit tree diff**: exactly my 3 intended files, matching my
  `git commit -m "docs(plans): flip sports-staleness + cloud-build-timeout items..."` call byte-for-byte.
- **Author**: `ikennaigboaka [slot-4·laptop]` — my own slot identity, consistent with either (a) another concurrent
  Claude Code session dispatched into this same `.tabs/4` clone under the same git identity, or (b) the commit-identity
  hook resolving identity from the slot/host regardless of which logical agent process is running.

`scripts/dev/run-bounded-analysis.sh` — the file the stray message actually describes — was confirmed **not** part of
the committed tree; `git status --porcelain` afterward showed it still modified-but-uncommitted in the working tree, so
the other process's actual code change was not lost, just left pending for its own author to re-stage and commit.

## Why it matters

- **Evidence-integrity risk**: a `- [x] ... — <repo>@<sha>` completion citation is only trustworthy if `<sha>`'s
  message/content actually describes the claimed change. A reviewer or `check_evidence_backed_completion.py`-style gate
  trusting the commit SUBJECT LINE alone (rather than diffing the tree) could be misled by this class of defect — here
  the tree was correct, but the mismatch means message-based auditing (`git log --grep`, changelog generation) can point
  at the wrong SHA for a topic, or fail to find the right SHA when grepping by expected message text.
- **Root cause is architectural, not incidental**: per-tab-worktrees intentionally shares ONE `.git` directory across
  however many agent sessions land in that tab concurrently (confirmed by this session alone observing ~15+ concurrent
  `quickmerge.sh`/`quality-gates.sh` processes across `.tabs/1-4` during this exact window, several with cwd inside this
  same `unified-trading-pm` clone). `git commit -m` is not inherently safe against a second `git commit` racing in the
  same `.git` — a shared `COMMIT_EDITMSG`/index-lock window can bleed state between them. This is a distinct symptom
  from the sibling doc `quickmerge_silent_push_failure_under_contention_2026_07_27.md` (which is about a swallowed
  non-fast-forward PUSH rejection) — this one is about the local **commit** step itself, before any push is attempted.

## Impact today

None observed beyond the confusing message — no content was lost or corrupted; both processes' real work ended up
correctly represented in git (mine committed with the wrong message, the other's left safely uncommitted for its owner
to re-land). Filed as a P2 evidence-integrity / infra hygiene finding, not a data-loss incident.

## Todos

- [x] ✅ [INFRA] P2. **DONE 2026-07-30 — unified-trading-pm@71c55ed6a.** Root-caused via direct reproduction (scratch
      repo + an artificial slow `prepare-commit-msg` hook): `.git/COMMIT_EDITMSG` is a single unlocked file per `.git`
      directory. Every `git commit` invocation — including a non-interactive `-m` one, and including one that ultimately
      FAILS (branch-drift rejection, prettier/plan-hygiene auto-fix re-stage) — writes its message to that file right
      after the `pre-commit` hook and only reads it back (to build the commit object) after `prepare-commit-msg` +
      `commit-msg` finish. No locking guards that window. By contrast, the index (`index.lock`) and `HEAD` (compare-
      and-swap — a losing writer gets `fatal: cannot lock ref 'HEAD': is at ... but expected ...`, reproduced directly)
      ARE properly guarded, ruling both out; prek's own patch-stash tempfiles are PID-namespaced (`<ts>-<pid>.patch`),
      ruling that out too. Net: a second `git commit` racing in the same clone — even a losing/ failed one — can
      overwrite `COMMIT_EDITMSG` while a first, slower invocation is still mid-hook-chain; the first invocation's commit
      then lands with ITS OWN correct tree (from its own already-staged index) but the SECOND process's message —
      exactly the observed symptom. Resolution: **(a)** documented the "one commit at a time per clone" discipline +
      full mechanism explicitly in `/codex/05-infrastructure/per-tab-worktrees.md` § "What worktree isolation does NOT
      cover" (new item 3, alongside the existing shared-stash and shared-scratch-path rules). **(b)** a cheap technical
      mitigation (WARN-on-mismatch, not auto-amend) was already shipped by the sibling P3 todo below
      (`scripts/quickmerge.sh`) — verified still present and correctly scoped (content-only detection, never blind-
      amends); no further code change needed on top of it, since full cross-entry-point serialization (a repo-wide git
      wrapper/hook covering every raw `git commit` call, not just quickmerge's) is a materially larger, riskier lift
      than this P2 finding's scope calls for.
- [x] ✅ [INFRA] P3. **DONE 2026-07-30 — unified-trading-pm@b3abf1bd5.** Added the post-commit self-check to
      `scripts/quickmerge.sh`'s Commit+Push+Flip step (right after the commit-retry loop, before the push retry loop):
      compares `git log -1 --format=%s` against the subject line of `$_QM_COMMIT_MSG` (what this invocation intended to
      commit) and prints a loud `WARN` (never a silent pass) on mismatch, naming both the intended and actual subject
      and pointing back at this doc. Content-only detection (never blind-amends — another process may be relying on its
      own HEAD read). Live-fired and self-corroborated DURING this same shipping session: two of this session's own
      commits (`23974ac83`, `bbe9a9871`) landed with exactly the message-swap shape this doc describes — the new WARN
      would have flagged both had it been present on the committing invocation's own re-run (verified by direct
      inspection: content correct, message swapped with a concurrent process's, matching this doc's Corroboration
      section precisely). `git-commit` skill itself is a built-in Claude Code skill, not a repo file — the quickmerge.sh
      Commit+Push+Flip path is the one this repo's tooling actually owns and is the one named as the primary target.

## Evidence

- Commit `7d8d690b6` (rebased from originally-observed `d64190bb0`) on `unified-trading-pm@live-defi-rollout`,
  2026-07-28 ~20:18 local: message is the RLIMIT_AS fix; `git show --stat` diff is my 3 files
  (`plans/active/issues/sports_manifest_read_staleness_budget_missing_2026_07_15.md`,
  `plans/active/issues/cloud_build_evidence_citation_short_hash_unresolvable_2026_07_27.md`,
  `plans/active/issues/deployment_api_cloud_build_600s_timeout_flake_2026_07_27.md` ->
  `plans/archive/issues/deployment_api_cloud_build_600s_timeout_flake_2026_07_27.md`).
- `scripts/dev/run-bounded-analysis.sh` confirmed still `M` (modified, uncommitted) in the working tree immediately
  after, containing the RLIMIT_AS/`ulimit -v` content the stray message describes — not lost, just not yet committed
  under its own name.
- Three consecutive commit attempts in this same session hit, in order: (1) branch-drift rejection (someone else
  pushed), (2) a plan-hygiene hook auto-fix requiring re-stage, (3) a prettier auto-fix requiring re-stage, (4) another
  branch-drift rejection, before the 5th attempt landed with the swapped message — i.e. this clone was under continuous
  multi-agent write contention for the several-minute span these attempts covered.

## Corroboration 2026-07-28 (a different session, same `.tabs/4` clone) — the symptom is WIDER than message-swap:

whole-file content reverts, foreign-file sweep-ins, index locks, and a real blocking merge conflict

This IS the same event described above, from the OTHER side: I am (almost certainly) the "other concurrent agent
process" whose commit got the RLIMIT_AS message stolen — my own `scripts/dev/run-bounded-analysis.sh` edit is exactly
what the stray message on `7d8d690b6` describes, and I independently found it sitting `M`/uncommitted afterward and had
to redo it. But the actual blast radius observed this session goes well beyond a swapped message on ONE commit — across
a single multi-hour session shipping ~13 unrelated small fixes to this repo, the following ADDITIONAL failure modes were
observed, all consistent with the SAME root cause (multiple concurrent `git`/prek invocations sharing one `.git`
directory + working tree with no isolation):

1. **Whole-file content silently reverted to HEAD, repeatedly.** At least 12 separate `Edit`-tool changes (spanning ~9
   different files: `scripts/dev/run-bounded-analysis.sh`, `scripts/docs/test_gen_doc_index.py`,
   `scripts/quality_gates/check_defi_address_citations.py`, `scripts/quality_gates/check_credential_ask_orphans.py`,
   `scripts/quickmerge.sh`, `codex/06-coding-standards/quality-gates-ui-template.sh`,
   `scripts/dev/slack-read-channel.py`, `scripts/plan-hygiene/run_hygiene_sweep.sh`,
   `scripts/quality-gates-base/base-service.sh`/`base-library.sh`/`base-ui.sh`, `agents/worker.md`, `agents/RULES.md`,
   plus several plan-doc checkbox-flip edits) were confirmed correctly applied on disk, then later found completely
   reverted (0 matches on a `grep` for content just written) before a commit ever landed for them — most consistent with
   a `git pull --rebase --autostash` (the standing `slot-cron-ff-pull.sh` cron, or another agent's manual pull) racing
   an in-progress edit, or a `git checkout`/reset from another process, in this same shared working tree. Each time,
   re-applying the identical edit and committing/pushing IMMEDIATELY (within seconds) succeeded — the content itself was
   never rejected, only the timing window was unsafe.
2. **`git commit` picking up files NEVER passed to `git add`.** Twice, `git commit -m "..."` (after
   `git add <exact-intended-file>`) produced a commit whose tree included OTHER files — once a single unrelated
   archived-issue doc rename (harmless, safely committed, just misattributed), once (in a different sibling repo,
   `features-service`, same clone-sharing model) a real deletion of 2 unrelated source files that turned out to be a
   different agent's own legitimate in-progress refactor. Root cause: `git commit` (without `--only`) commits the WHOLE
   staged index, not just the paths named in a prior `git add` call — if another process's `git add` landed BETWEEN mine
   and my `git commit`, their staged content rides along. **Mitigation used**: `git diff --cached --stat` (no path arg)
   immediately before every commit, `git restore --staged <foreign-file>` for anything not mine — this caught and
   correctly excluded a 26-file/1-unmerged-file sweep-in attempt in `market-tick-data-service` before it could land.
3. **`fatal: Unable to create '.git/index.lock': File exists.`** — hit 3 separate times in one session (once
   mid-`git add`, twice mid-`git commit`), each time from a DIFFERENT concurrent process holding the lock transiently;
   each time, waiting a few seconds and retrying succeeded cleanly (the lock is never left stale here, just transiently
   contended).
4. **A genuine, unrelated `git commit` HARD BLOCK from another agent's live unresolved merge conflict.** In
   `market-tick-data-service` (a different repo, same clone-sharing model applies), attempting a trivial one-line fix
   hit
   `error: Committing is not possible because you have unmerged files... U tests/unit/scripts/test_reprocess_bulk_tardis_derivative_ticker_funding_timestamp_2026_07_28.py`
   — a REAL git conflict state (not resolvable by re-staging) left mid-merge/rebase by a different concurrent agent,
   blocking ALL commits in that repo until that agent resolves it. Documented as a blocked sub-item rather than
   force-resolved (resolving someone else's live conflict without their context risks discarding real work).
5. **`git pull --rebase --autostash` occasionally failing with `fatal: Cannot rebase onto multiple branches`** — hit
   twice; root cause not investigated (plausibly an ambiguous `FETCH_HEAD` from a fetch that raced another process's own
   fetch), worked around each time by a plain `git fetch` + explicit `git rebase origin/<branch>` instead of the
   combined `pull --rebase` form.

**Updated impact assessment**: unlike the original filing's "no content lost" conclusion, items 1 and 2 above show this
CAN silently discard in-progress work if a re-verification step isn't run before every commit — the only reason nothing
was actually lost this session is that each edit was independently re-verified (`grep`/`git show HEAD:<path>`)
immediately after every commit and every push, and re-applied when found missing. **A worker that trusts "the Edit tool
said it succeeded" or "the commit command didn't error" without a post-hoc content check would silently ship incomplete
work** — this is a materially higher-severity finding than the original P2 message-only mismatch. Recommend re-triaging
this doc's priority to P1 and broadening todo 1's root-cause scope to cover the working-tree revert and
foreign-file-sweep-in symptoms, not just `COMMIT_EDITMSG`. No code fix attempted here (infra/tooling ownership, same as
the original filing) — this is a corroborating field report + a documented recovery pattern (re-verify content on disk
after every Edit, re-verify commit content via `git show --stat`/`grep` before AND after every push, never trust a
non-error exit code alone) for whoever picks up the root-cause todo.

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-30721a) —
  bounded/deterministic-outcome work, no operator gate or live judgment call found; flipped
  `assigned_vm: NA -> planning`. Conflict-check run against all active `assigned_vm: planning` docs in this doc's
  `parent_epic` + the infra tranche's consolidated-closeout digest: zero/milestone-only overlap, clear to proceed.
