---
doc_type: issue
title: >-
  A concurrent process's `git pull --rebase --autostash` can silently DISCARD another session's uncommitted,
  never-staged edits in a shared checkout -- content loss, not just mis-attribution
summary: >-
  Empirically reproduced live 2026-08-07 (twice, in `.tabs/1/unified-trading-pm`) while root-causing
  `ao_local_mock_server_workflow_truncation_and_e2e_port_collision_2026_08_07.md`'s Finding 1: an uncommitted,
  never-staged local edit to `scripts/workflow-templates/rollout-workflow-templates.sh` vanished from disk twice within
  minutes, each time correlated (via file mtime + `git reflog` + `.git/index` mtime + `ps aux`) to a DIFFERENT,
  concurrently-running `bash scripts/quickmerge.sh` process (a different Claude Code session sharing the same `.tabs/1`
  slot checkout) executing `git pull --rebase --autostash origin live-defi-rollout -q` at that exact moment -- confirmed
  via a tight polling reproduction that pinned the loss to within 6 seconds of the other process's rebase. This is a
  MORE SEVERE, uncovered variant of the already-resolved
  `autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md`: that fix (shipped
  `unified-trading-pm@72bdb200e`/`@9669098c3`/`@461a5a0bc`) stops foreign STAGED content from being swept into someone
  else's commit under the wrong attribution -- it does not address, and does not claim to address, the case demonstrated
  here where the victim's edit was never staged at all and simply disappears from the working tree with no trace in the
  index, no conflict, no error, and (per this investigation) no proven recovery path. Directly explains why the ORIGINAL
  2026-08-07 workflow-truncation incident (5 `.github/workflows/*.yml` files truncated to ~13-15% of their size across
  22 repos) was never reproducible by re-running the suspected trigger (Playwright e2e tests) -- the real trigger was
  concurrent git activity from ANOTHER process in the same shared checkout, not anything agent-orchestrator's own code
  did. Landing THIS doc's own closing commit (for the sibling issue) fought the identical live hazard repeatedly during
  the same session, including a full loss of both new doc files' uncommitted content mid-edit -- direct, repeated,
  real-time confirmation this is neither rare nor theoretical under current fleet load.
status: open
nature: issue
asset_group: [ao, cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [git, autostash, shared-checkout, foreign-wip, data-loss, multi-agent-safety, process, big-finding, quickmerge]
related:
  [
    plans/archive/issues/autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md,
    plans/archive/issues/ao_local_mock_server_workflow_truncation_and_e2e_port_collision_2026_08_07.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    scripts/quickmerge.sh,
  ]
created: "2026-08-07"
author: ikennaigboaka [interactive session]
priority: P1
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
estimate_class: research
depends_on: []
parent_epic: infrastructure_master
resolved_by:
source:
  [
    "interactive session 2026-08-07 — root-causing the ao_local_mock_server_workflow_truncation issue's Finding 1; an
    uncommitted edit to rollout-workflow-templates.sh vanished live, twice, while investigating, and was empirically
    traced to a concurrent quickmerge.sh process in the same .tabs/1 checkout via mtime + reflog + ps aux correlation
    (tight polling loop pinned the loss to within 6 seconds of the other process's 'git pull --rebase --autostash');
    reproduced AGAIN, a third+fourth time, while landing this very doc's own closing commit under heavy concurrent fleet
    load",
  ]
locked_by:
locked_since:
context_scope: [scripts/quickmerge.sh, scripts/dev/safe-doc-push.sh, /codex/05-infrastructure/per-tab-worktrees.md]
---

# `git pull --rebase --autostash` can silently discard a concurrent session's uncommitted edits

## What was reproduced, and how

While investigating `ao_local_mock_server_workflow_truncation_and_e2e_port_collision_2026_08_07.md`'s Finding 1 (a
still-unexplained 2026-08-07 incident where 5 `.github/workflows/*.yml` files were found truncated to ~13-15% of their
size across 22 repos), this session made an uncommitted edit to
`scripts/workflow-templates/rollout-workflow-templates.sh` in `.tabs/1/unified-trading-pm`. The edit vanished from disk
**twice**, each time within minutes of being applied, with **no git error, no conflict marker, and nothing in
`git status` to explain it** — the file simply read back as byte-identical to `HEAD` each time.

To pin the mechanism, a tight polling loop (`grep`-checking a unique marker string in the file every 1s) was run
alongside a live tail of `/tmp/slot-cron-ff-pull.log` and periodic `ps aux` snapshots. The loop caught the loss
precisely:

- File mtime at the moment of loss: `Aug 7 19:30:06`.
- `git reflog` for `.tabs/1/unified-trading-pm` at that moment showed the TOP entries were
  `pull --rebase --autostash origin live-defi-rollout -q (finish)` / `(pick)` / `(start)` — **not**
  `slot-cron-ff-pull.sh`'s own `git merge --ff-only` (which is all that script ever runs, by its own explicit design:
  "Never destructive. Never runs `merge --no-ff`, never `rebase`, never `reset --hard`").
- `.git/index` mtime matched the same moment.
- `ps aux` at that exact moment showed a **different, concurrently-running Claude Code session** (PID 1679, then later
  PID 81767) executing `bash scripts/quickmerge.sh "<some other commit message>" --agent --files "<some other files>"`
  with its **cwd inside this same `.tabs/1/unified-trading-pm` checkout** — a genuinely different in-flight piece of
  work (e.g.
  `"fix(cicd): port squash-promote patch-fallback fix into semver-agent.yml.tmpl + extend make_reusable.py"`), unrelated
  in content to the file that vanished.
- The commit that landed via that reflog's rebase (`2fa317801d`, "port squash-promote patch-fallback + concurrency fix
  into semver-agent.yml.tmpl SSOT") does **not** touch `scripts/workflow-templates/rollout-workflow-templates.sh` at all
  — confirmed via `git show --stat`. A `git merge`/rebase that never touches a given path is documented git behavior to
  never disturb uncommitted local changes to that unrelated path. That guarantee did not hold here.

Re-applying the edit and waiting for the other process to exit (confirmed via `ps -p <pid>`), then committing
**immediately** (edit → `git add` → verify no unstaged delta → `git commit` → `git push`, all within one uninterrupted
sequence with zero other tool calls in between) succeeded cleanly on the first try — `agent-orchestrator@a3d058c63e`
landed with `ahead=0` and no further loss. This confirms the risk window is specifically **between an edit landing on
disk and that edit being committed** — once committed, the content is safe from this class of loss.

**Recurred a third and fourth time** later the same session, while landing the CLOSING commit for the sibling issue doc
(this doc + the archived `ao_local_mock_server_workflow_truncation...md`): under sustained heavy concurrent fleet load
(at times 5-7 simultaneous `quickmerge.sh`/`git commit` processes observed via `ps aux` in this same
`.tabs/1/unified-trading-pm` checkout, including at least one other session's own 30-attempt atomic retry-loop script
for unrelated na-eligibility-audit work), the SAME two new doc files were lost — this time deleted from disk ENTIRELY
(not just reverted to HEAD content), while in an untracked (`??`) state. `.git/FETCH_HEAD` was independently observed
truncated to 0 bytes during the same window, consistent with multiple concurrent `git fetch` processes racing to write
that same file. Recovery required locating a dangling git blob (`git fsck --unreachable`) for a partial version of one
file, plus reconstructing both files' final content from the last known-good commit in git history plus this session's
own precise memory of every edit applied on top of it — i.e., recovery was possible here only because the authoring
agent could accurately reconstruct lost content from context; a human editor would likely have lost the work outright.

## Why this is NOT the same issue as the already-resolved one

`autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md` (RESOLVED, 3 fixes shipped 2026-08-01/02) is about
`--autostash`'s restore step re-**staging** a foreign file that was already dirty, so a by-name `git add <my-file>` +
`git commit` sweeps it up under the wrong attribution. Its own summary is explicit: _"Not data loss. Content is intact
and on origin."_ The shipped fix (`git restore --staged .` immediately after the post-commit-case autostash pop, before
any of `quickmerge.sh`'s own `git add` calls) only prevents that mis-attribution — it unstages, it does not touch
working-tree content, and it does nothing for a file that was never staged in the first place. (This session directly
observed that shipped fix working as designed — `safe-doc-push.sh` logged
`unstaging foreign path picked up from a concurrent process sharing this checkout` for several files NOT in this
session's own `--files` list, correctly protecting against the mis-attribution case.)

What was reproduced here is different and more severe: the edit was **never staged**, and it did not end up
mis-attributed in someone else's commit — it simply **ceased to exist**, in either the working tree or the index, with
the file reading back as `HEAD` (first two reproductions) or being deleted outright (third/fourth reproduction, under
heavier load). Whether the content is recoverable via the autostash's own stash object (if one was created and not yet
dropped) was not conclusively established — one recovery in this session succeeded via a dangling blob found through
`git fsck --unreachable`, but that blob was an earlier, partial version of the file (missing several later edits), not
the final state.

## Why this plausibly explains the original workflow-truncation incident

The original incident (`ao_local_mock_server_workflow_truncation_and_e2e_port_collision_2026_08_07.md` Finding 1)
truncated exactly the kind of files (`.github/workflows/*.yml`, and the `scripts/workflow-templates/` templates that
generate them) that sit in the direct blast radius of `unified-trading-pm/scripts/workflow-templates/`-adjacent
quickmerge activity — the SAME directory this session's reproduction hit, repeatedly. That investigation spent
significant effort ruling out `CIReconcile`, `slot-cron-ff-pull.sh`, and `rollout-workflow-templates.sh`'s own
(non-existent) automated triggers as the direct writer, without success — because none of them ever writes truncated
content; a genuine `rollout-workflow-templates.sh` run, or any other legitimate writer, produces CORRECT full-size
content. A race where a file is mid-write (by any process, including the operator's own editor, an IDE auto-save, or a
partial `echo ... > file` mid-flight) at the exact moment a **different** concurrent `git pull --rebase --autostash`'s
stash/pop cycle touches the same working tree is a plausible mechanism for a PARTIAL, truncated result to land on disk —
matching the observed "shrunk to ~13-15%, not zeroed, not garbage" signature far better than any of the ruled-out
candidates did. This is circumstantial, not proven for that specific incident (the original incident is too old to
re-run), but it is now the single most evidence-backed explanation available, and it is a REAL, independently reproduced
FOUR TIMES in one session, currently-live hazard regardless of whether it explains that exact incident.

## Todos

- [ ] [INFRA] P1. **Determine whether the discarded content is recoverable from a dangling stash/blob object** —
      `git fsck --unreachable` / `git stash list` / reflog on the OTHER process's session (if still inspectable)
      immediately after a reproduction, before any `git gc` can prune it. This session's own partial recovery (a
      dangling blob via `git fsck --unreachable`, but only an EARLIER, incomplete version of the lost file) suggests
      blobs DO often survive but are not straightforward to locate or guaranteed to be the final version — establish
      whether this is reliably recoverable or just got lucky once.
- [x] ✅ [INFRA] P1. **Reproduce deliberately and minimally** — two throwaway clones of the same repo sharing nothing
      but intent to collide: clone A makes an uncommitted edit to file X and holds it dirty; clone B (simulating a
      concurrent quickmerge.sh) runs `git pull --rebase --autostash` against a remote with new commits that do NOT touch
      X. Confirm whether file X's content in clone A survives. If it does NOT reproduce in a clean 2-clone setup, the
      trigger requires something specific to this workspace's shared-checkout model (e.g. genuinely being the SAME
      `.git` directory two processes operate on concurrently, not just "the same remote") — narrow accordingly. **DONE
      2026-08-08 (`ao_satellite_ao_dispatch_batch8-004`)** — separate `.git` directories do NOT reproduce it (edit
      survives cleanly; a pure-concurrent-pull variant instead hits `fatal: Cannot rebase onto multiple branches` before
      ever reaching autostash). Narrowed + reproduced the real mechanism within the SAME `.git` directory
      (stash-interleaving: two processes' `git stash push` calls interleave, and the wrong process's `git stash pop`
      pops the OTHER process's top-of-stack entry, leaving the victim's own stash unpopped and its file reverted to
      HEAD). Full verdict recorded in the Progress Log entry below.
- [ ] [INFRA] P0 (pending the above). **If confirmed as a genuine cross-process working-tree race on the SAME `.git`
      directory**: this is a structural hazard in the "share one clone per slot across multiple concurrent Claude Code
      sessions" model CLAUDE.md's Multi-agent safety section already documents as an accepted operating mode ("Two
      teammates × multiple parallel agents") — and this session directly observed it is NOT a rare edge case under
      current fleet load (reproduced 4 times in one session; at peak, 5-7 simultaneous git-mutating processes were
      observed in ONE `.tabs/N` checkout via `ps aux`, including `.git/index.lock` contention and `.git/FETCH_HEAD`
      truncation to 0 bytes). Candidate mitigations to evaluate (do not implement without operator sign-off — this
      touches `scripts/quickmerge.sh` + `scripts/dev/safe-doc-push.sh`, both HIGH-RISK shared infrastructure): (a) a
      per-`.git`-directory lock (flock) around the pull-rebase-autostash sequence in both `quickmerge.sh` and
      `safe-doc-push.sh`, so two concurrent sessions in the same slot never overlap that specific window; (b)
      commit-then-reconcile ordering — stage+commit local work BEFORE fetching/rebasing rather than after, shrinking the
      vulnerable window to near-zero (this session's own recovery — edit, immediately `git add`+commit+push with no gap
      — suggests this is already the safer pattern and could become the documented default); (c) an explicit
      `git stash list` sanity check immediately after every autostash pop, comparing the working tree against a pre-pull
      snapshot hash, loud-failing if anything the operator didn't intend to touch changed; (d) consider whether the
      sheer VOLUME of concurrent sessions sharing one `.tabs/N` slot (5-7+ observed simultaneously) is itself the
      problem to address (a concurrency cap / queue per slot) rather than only hardening the git mechanics under
      unbounded concurrency.
- [ ] [DOC] P2. **Once a mitigation is decided, fold into `/codex/05-infrastructure/per-tab-worktrees.md`** alongside
      the existing (but non-covering) autostash-pop guidance, clearly distinguishing the two failure modes:
      mis-attribution (resolved 2026-08-02) vs. content loss (this doc).
- [ ] [INFRA] P2. **Safely audit and clear this specific checkout's (`.tabs/1/unified-trading-pm`) currently-orphaned
      `autostash` stash entries** — as of 2026-08-09 (round11 verification) `git stash list` showed 4 long-lived
      `autostash` entries plus this session's own safety-snapshot, none dropped since at least 2026-08-08. Per this
      doc's "Recoverability findings," a stale stash sitting at `stash@{0}` can get silently popped by a later,
      unrelated plain `git pull` (see Progress Log entry below) and revert freshly-landed work — every additional
      orphaned entry is latent re-trigger risk, not inert. For each entry: `git stash show -u --stat` to inspect
      content, diff each touched file against current HEAD to confirm the stash's content is a strict subset of
      already-landed commits (i.e. fully superseded, safe to drop) before `git stash drop` — never blind-drop, and
      never drop an entry whose content isn't provably redundant against HEAD.

## Corroborating reproduction — safe-doc-push.sh's own false-success path (2026-08-07, na-eligibility-audit run)

A separate `/na-eligibility-audit` run (~15 parallel sub-agents, same session type as this doc's own origin) hit a
distinct, more specific instance of this same root cause: `safe-doc-push.sh`'s "nothing staged for the named files --
checking if content already matches HEAD" branch (script lines ~186-192) reported
`✅ Named files already match HEAD (a concurrent session landed identical content) -- treating as success` and exited 0,
while **zero of the 12 target files' markers had actually been committed** (independently verified against the pushed
tree). Mechanism: a `git pull --rebase --autostash` step's rebase succeeded but its autostash pop did not complete,
leaving the caller's edits parked in an un-popped `stash@{0}` instead of restored to the working tree — so `git add`
staged nothing, and the subsequent `git diff --quiet` (working tree vs. index, not vs. origin) was ALSO clean,
satisfying the script's "already matches HEAD" heuristic on a false premise. This is worse than plain content loss (the
earlier reproductions above) because the caller gets an explicit, confident SUCCESS message instead of silence — nothing
prompts a verification check. At least 3 more of the ~15 sub-agents in that same run independently hit variants of this
(some recovered via `git stash` inspection, most via an isolated `git worktree` once they gave up fighting the shared
index). Directly implements candidate mitigation (c) above (an explicit `git stash list` sanity check after every
autostash pop) as the concrete fix for `safe-doc-push.sh` specifically: compare stash count/top-entry before vs. after
the pull; a remaining entry means the pop did not complete, so retry the pop or hard-fail (`exit 3`) rather than falling
through to the "already matches HEAD" branch. Also reinforces mitigation (b) (commit-immediately-after-edit) as the most
reliable practical mitigation available today — every successful recovery in that run either committed within one
uninterrupted edit→add→commit sequence or fell back to an isolated worktree, which structurally removes the shared-index
race entirely.

## Why this wasn't chased further this session

Confirming the exact git-internals mechanism (why does an unrelated-path rebase disturb an uncommitted edit at all —
this should not be possible per git's own documented merge/rebase semantics unless something else is also touching the
same `.git` directory, e.g. a genuinely overlapping SECOND `git pull --rebase --autostash` from a third process, or an
interaction with `slot-cron-ff-pull.sh`'s own concurrent `git merge --ff-only` on the SAME clone) needs controlled,
isolated reproduction outside this shared, actively-multi-tenant checkout — not safe or conclusive to chase further
live, in-session, in a directory multiple other real sessions are actively shipping real work through. The one shipped
mitigation from this session (a size-sanity write guard in `rollout-workflow-templates.sh`,
`unified-trading-pm@a3d058c63e`) is defense-in-depth against the WORST-CASE outcome (silent destructive truncation
reaching disk) regardless of whether this exact mechanism is what caused the original incident — it does not require
understanding the root cause to be valuable.

## Progress Log

- **na-eligibility-audit 2026-08-08** (ao tranche): KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` = **4**,
  matching. Todo 2 (deliberate minimal 2-clone reproduction) is individually bounded/AO-eligible on its own, but the
  other 3 stay genuine judgment/dependency work: todo 1 is opportunistic (needs a live reproduction in progress to
  investigate, not independently schedulable), todo 3 explicitly reads "do not implement without operator sign-off," and
  todo 4 is downstream of todo 3's decision — the whole-doc RECLASSIFY bar is not cleared. Tagging todo 2
  MISCLASSIFIED_LIKELY_AO_ELIGIBLE for a future `/ag-closeout-audit ao` satellite-batch extraction rather than forcing a
  whole-doc flip. Blocker tags: todo1=DEPENDENCY_BLOCKED(on todo2), todo2=GENUINE_WORK/MISCLASSIFIED_LIKELY_AO_ELIGIBLE,
  todo3=DEPENDENCY_BLOCKED(on todo2)+OPERATOR_QUESTION once unblocked, todo4=DEPENDENCY_BLOCKED(on todo3).

- **2026-08-08 (slot 4, ao_satellite_ao_dispatch_batch8-004)** — Deliberate minimal reproduction run (todos 1+2).
  **Clean 2-clone setup result: DOES NOT REPRODUCE.** Two separate git clones (separate `.git` directories) of the same
  remote were created in a throwaway scratchpad. Clone A held an uncommitted edit to `file_x.txt` (never staged). Clone
  A then ran `git pull --rebase --autostash origin master` against a remote that had new commits not touching
  `file_x.txt` — the edit **survived** (`file_x.txt` contained the marker after the pull, stash list was empty). A
  second test (5 concurrent `git pull --rebase --autostash` processes in the same directory) found all concurrent
  processes fail before reaching the autostash step: `fatal: Cannot rebase onto multiple branches` (concurrent writes
  race `.git/FETCH_HEAD`, corrupting it). The hazard does not trigger via pure concurrent-pull in a shared checkout
  either (git's own locking causes early failure, not silent data loss). **Conclusion: the trigger IS specific to the
  SAME `.git` directory — but requires a more targeted race than parallel `git pull` invocations.**

  **Stash-interleaving race: REPRODUCED (same `.git` directory).** Manual simulation of the mechanism: (1) Process A
  holds uncommitted edit to `file_x.txt`. (2) Process B runs `git stash push` — stashes ALL dirty working-tree files
  including file_x's edit; file_x reverts to HEAD ("vanishes" from working tree). `stash@{0}` = process-B-autostash. (3)
  Process C concurrently runs `git stash push` for its own dirty file — pushes on top: now `stash@{0}` = process-C and
  `stash@{1}` = process-B. (4) Process B runs `git stash pop` — pops `stash@{0}` (process C's entry), NOT its own.
  Process B's stash (with file_x edit) is left as `stash@{0}` (after C's is dropped), unpopped. `file_x.txt` remains at
  HEAD content. In the real fleet scenario, process B's quickmerge exits thinking everything is fine — the victim's edit
  disappears from disk with no error message.

  **Recoverability findings (immediate — before `git gc`):** (a) `git stash list` shows the stuck entry explicitly
  (`stash@{0}: On master: process-B-autostash`). (b) `git stash show -p stash@{0}` shows the **FULL, FINAL** edit
  content (not a partial/earlier version — in this controlled single-edit test). (c) `git stash pop` successfully
  restores the edit. (d) `git fsck --unreachable` shows dangling commits/trees/blobs from the dropped stash entries,
  providing a secondary recovery path. **Reliability verdict: HIGH if the stash was not explicitly dropped and `git gc`
  has not run** — the content survives in the stash ref. UNRELIABLE after `git gc` (which prunes unreachable objects) or
  if the process explicitly drops the stash. The live incident's partial-version recovery (earlier blob, not final
  state) may reflect multiple sequential edits where only intermediate blob versions survived — this controlled test
  involved a single edit so the final version was always current in the stash.

  **What this does NOT yet establish** (todo 1, still DEPENDENCY_BLOCKED pending a live reproduction opportunity): the
  exact timing window in which the stash interleaving occurs under real fleet load, and whether the blob is truly
  recoverable in the file-deleted-entirely case (third/fourth live reproductions). The stash-pop-failure path (where the
  pop exits non-zero and the stash is preserved but not applied) was also observed in this session under test
  contamination, producing a `stash@{0}: autostash` entry that remained after a failed pop — this is consistent with the
  `safe-doc-push.sh` false-success scenario described in the Corroborating section above.

  **Todos 1+2 verdict**: Todo 2 closed here (deliberate reproduction complete; verdict recorded). Todo 1 partially
  answered (recoverability: reliable via stash if not dropped/gc'd; final-version recovery confirmed in controlled
  setting; partial-version risk noted for multi-edit scenarios). Full todo 1 closure still requires a live reproduction
  opportunity per the original constraint.

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (3 entries), still accurate.

- **2026-08-09 (round11 na-eligibility-audit verification, main session)**: new live corroboration, a variant not
  previously captured — a plain `git pull --ff-only origin live-defi-rollout` (not `--rebase --autostash`) printed
  `Applied autostash` and reintroduced STALE content that reverted already-landed, ancestor-verified work: 33 files
  came back modified/deleted in the working tree, including two brand-new files
  (`ao_satellite_ao_dispatch_batch16_2026_08_09.md` + its finalize twin, committed and pushed minutes earlier in
  `82a36f4055`) showing as locally-deleted, and several other files had their round11 Progress Log citation markers
  stripped back out — a systematic revert to a pre-commit-82a36f4055 state, not random noise (confirmed via `git diff`
  on 3 separate files, all showing the same pattern: round11 markers removed, content reverted to an earlier point).
  Unlike the doc's existing stash-interleaving reproduction (wrong CONCURRENT process's entry popped), this instance's
  pop reportedly "succeeded" (no stuck `stash@{0}` left behind matching this specific pop) but reapplied an entry that
  was already stale relative to the current HEAD at pop time — i.e. the entry itself was old/orphaned (created at some
  earlier point, never cleaned up), and a routine `--ff-only` pull's autostash logic popped whatever sat at
  `stash@{0}` without checking its vintage. Root cause of the underlying commit's own `82a36f4055` push not being
  affected: the STASH pop only touches the working tree/index, not already-pushed commits — the corruption was
  entirely local and never reached origin. **Recovery**: `git stash push -u` (safety-snapshot, in case anything of
  value got swept in) followed by `git restore` back to HEAD; verified clean (`git status` empty) and the two batch16
  files back on disk with correct content. **New finding**: `git stash list` immediately after recovery showed 4
  MORE orphaned `autostash` entries still present (pre-dating this incident, from earlier rounds' concurrent
  `--rebase --autostash` pulls) — confirming the latent-risk pattern is ongoing, not a one-off; added as a new P2 todo
  above rather than acted on blind.
