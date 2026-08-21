---
doc_type: issue
title: A quickmerge --isolated worktree from a DIFFERENT slot/session appears nested inside slot 16's own directory tree, repeatedly blocking /done's dirty-check for unrelated tasks
summary: >-
  Slot 16's worktree contains `.tabs/16/oms-wt.oc3YkB` — a git worktree whose HEAD commit author has been observed
  under 3 DIFFERENT identities across one session (`ikennaigboaka [slot-2·laptop]`, `github-actions[bot]`,
  `uts-backmerge-bot`), each a fresh commit within minutes of checking — this is CLAUDE.md's own documented
  `main-backmerge-to-ldr` automation fast-forwarding the branch, NOT a live human editing session (an earlier
  "confirmed live via pgrep" claim in this doc's first Progress Log entry was a self-match false positive — the
  pgrep command's own argument contained the search string — and is now superseded). The actual liveness signal
  (mtime on the staged working-tree files) shows the WIP itself is ~6h+ stale as of the 2026-08-21 10:29 check —
  likely genuinely abandoned, not live. Regardless: because it is a `git status`-dirty directory physically located
  under `.tabs/16/`, the orchestrator's `/api/slots/16/done` dirty-check (`worker.md` DONE-GATE) treats it as slot
  16's own uncommitted WIP and hard-rejects `/done` with `required_action: "quickmerge-or-stash"` — even though slot
  16's own actual work (unrelated plan-doc edits, already committed + pushed + verified on origin) has nothing to do
  with it. This blocked 4+ separate `/done` calls in one session (2026-08-21, slot 16) across 2 different unrelated
  tasks. This AO worker (role: review, PM-docs scope) lacks the execution-service domain context to safely judge
  whether the WIP is truly abandoned and safe to stash — that decision is now BLOCKED-OPERATOR-DECISION (see the
  correction todo below), not a routine wait-and-retry.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, execution-service]
scope: [engineer, admin]
tags: [multi-agent-safety, per-tab-worktrees, quickmerge-isolated, done-gate, worker-lifecycle, blocked-operator-decision]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-21
priority: P1
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Discovered live during 2 unrelated slot-16 worker tasks (sports_taxonomy_p4_backfill, then
  cross_cutting_satellite_ao_dispatch_batch21, then defi_satellite_ao_dispatch_batch2_finalize) on 2026-08-21 —
  every `/done` call rejected on the exact same foreign path.
drift_direction: advance-code
context_scope:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
  ]
---

# Foreign `--isolated` quickmerge worktree nested in the wrong slot's directory

## What was found (measured, 2026-08-21, slot 16)

- `.tabs/16/oms-wt.oc3YkB` exists as a real git worktree (`.git` is a file, not a directory — the worktree-pointer
  shape) with `git status --porcelain` showing 24-29 staged changes across the session (file count grew over time:
  `execution_service/adapters/defi_instruction_routes.py`, several `execution_service/engine/transfers/*` files,
  `execution_service/engine/delta_proxy_repricer.py`, `execution_service/engine/quote_maintenance.py`, several
  deleted `defi_execution/*`/`transfers/live_bridge_adapter.py` files, and matching test files).
- `git -C oms-wt.oc3YkB log -1` shows HEAD authored `ikennaigboaka [slot-2·laptop]` — a DIFFERENT slot (2, not 16)
  and a DIFFERENT machine class (`laptop`, not this AO worker's `planning` VM).
- `pgrep -f "oms-wt.oc3YkB"` returned 2 live processes at every check across an ~815s window, confirming this is a
  currently-active session, not orphaned/dead WIP — per the liveness rule, this must be PROTECTED (never
  stashed/touched), which is what this session did each time (waited/retried `/done` rather than acting on it).
- Branch is `live-defi-rollout` — same integration branch every slot tracks, consistent with a `quickmerge --isolated`
  worktree per CLAUDE.md: _"Ship scripts COMMIT FROM AN ISOLATED WORKTREE so a peer sharing your checkout can't
  revert your edits... `--isolated` in quickmerge is opt-in, NOT default (laptop-only, auto-OFF on AO)"_ — the
  `slot-2·laptop` author identity is consistent with a laptop-interactive session using `--isolated`.

## Why it matters

The orchestrator's `/api/slots/<N>/done` dirty-check (per `worker.md`'s DONE-GATE) appears to scan the entire
`.tabs/<N>/` directory tree for uncommitted changes, including this nested foreign worktree — so ANY slot whose
directory happens to contain another session's `--isolated` worktree gets its own unrelated `/done` calls
hard-rejected until the foreign session's WIP clears. This is NOT the already-documented "two operators sharing one
slot's checkout" class (`per-tab-worktrees.md`) — that's about two sessions sharing the SAME slot's identity/index.
This is a DIFFERENT slot's isolated worktree apparently landing inside slot 16's path.

**Unconfirmed root cause** (flagging, not asserting): whether `quickmerge --isolated`'s worktree-creation path scopes
the new worktree under the INVOKING slot's own `.tabs/<N>/` directory correctly, or uses some other path resolution
(e.g. relative to `pwd` at invocation time, or a shared temp root) that can land it under a DIFFERENT slot's tree when
invoked from an unusual cwd. Not investigated further this session — the live worktree could not safely be inspected
beyond `git log`/`git status`/`pgrep` without risking interference with a live session's work.

**Impact observed this session**: 3 separate `/done` calls across 2 different completed, unrelated, already-verified-
on-origin tasks were rejected and had to be retried (one eventually succeeded when the task turned out to be
orphaned and the check short-circuited; the pattern is otherwise a real, recurring source of wasted `/done` retries
/ worker confusion for any slot unlucky enough to have a foreign isolated worktree land in its tree).

## Todos

- [x] [SCRIPT] P2. **Confirm whether `oms-wt.oc3YkB` is genuinely a quickmerge `--isolated` worktree** — **PARTIALLY
      ANSWERED, 2026-08-21 (slot-16): NO, evidence says it is NOT `scripts/quickmerge.sh --isolated`.** Read
      `scripts/quickmerge.sh`'s isolated-worktree path (lines ~879-920): it names the parent
      `${TMPDIR:-/tmp}/qm-iso-$$` (a **`/tmp`-rooted** path, never inside the real `.tabs/<N>/` checkout tree), then
      nests `<parent>/.tabs/<CALLER'S OWN slot-N>/<repo_name>` under it, where `<repo_name>` is the basename of the
      caller's own repo toplevel — so the isolated worktree can only ever land under the INVOKING session's own slot
      segment (by construction, via `slot_identity_resolve` on the caller's own cwd), and always inside `/tmp`, never
      literally inside another checkout's `.tabs/16/` directory. `oms-wt.oc3YkB` sits directly at
      `.tabs/16/oms-wt.oc3YkB` (flat `<tag>-wt.<6-char-suffix>` naming, no `/tmp` prefix, no `qm-iso-$$` segment) —
      structurally a different mechanism. Grepped `oms-wt`/`oms_wt`/`OMS_WT` and `mktemp.*wt\.` across every repo's
      `scripts/`, top-level `*.sh`/`*.py`, and `unified-trading-ci`'s `.github/workflows/` under `.tabs/16/` (23
      repos): **zero hits** — the actual creator is not in any committed script this session could find. No
      self-hosted `actions-runner` found on this host either, so the `github-actions[bot]`-authored HEAD (see
      Progress Log) most likely reflects a routine LDR pull/rebase picking up an upstream bot commit, not a runner
      executing locally. **Net effect**: this REFUTES the "quickmerge `--isolated` path-resolution bug" hypothesis as
      originally framed (todos 2 below no longer apply to quickmerge.sh specifically) — the true creator remains
      unidentified, likely a peer's personal/laptop-local tool never committed to any checked-out repo (consistent
      with `--isolated`-adjacent tooling being described as "laptop-only" in CLAUDE.md, but this is evidently a
      DIFFERENT, unlocated tool, not quickmerge.sh itself). Not investigated further this session — deeper forensics
      (e.g. asking the peer directly, or inspecting shell history/rc files) is out of scope for an unattended AO
      worker and risks an unbounded search.
- [ ] [REVIEW] P1. **CORRECTION, 2026-08-21 (slot-16): the earlier "confirmed live" verdicts (Progress Log entries
      below, timestamped pre-this-entry) were a measurement trap — commit-recency is NOT the right liveness signal
      here.** `oms-wt.oc3YkB`'s HEAD commit has now been observed under **3 distinct author identities across the
      session** (`ikennaigboaka [slot-2·laptop]` → `github-actions[bot]` → `uts-backmerge-bot`), each landing a fresh
      commit within minutes of the check — but this is CLAUDE.md's own documented `main-backmerge-to-ldr` automation
      fast-forwarding the branch, not a human editing files. Checked the actual liveness signal instead — **file
      mtime on the staged working-tree files**: `execution_service/engine/quote_maintenance.py` and `pyproject.toml`
      both show mtime `2026-08-21 04:20:07`, vs. a check-time of `2026-08-21 10:29:06` — **~6h9m stale**, while the
      workspace's own documented rule is `mtime <120s → PROTECT` (i.e. >>120s is the DEAD-claim threshold). The
      staged 30-file diff has also been byte-identical across every check this session (spanning the pre-compact
      boundary) despite 3 backmerge-bot commits landing on HEAD in that window — a live editing session would show
      the staged set or file mtimes moving, not a frozen diff under a moving HEAD. **Net: this worktree's WIP is very
      likely genuinely abandoned (dead), not live** — reclassifying the earlier "live" Progress Log entries as
      incorrect (based on a bot-driven HEAD, not the WIP author's activity). **Not acting on this myself**: per the
      done-gate's own contract, a dead claim may be inherited+committed or slot-tagged-stashed, but that applies to a
      slot's OWN checkout — `oms-wt.oc3YkB` is a DIFFERENT repo (execution-service) with a mid-refactor defi
      transfer/bridge change-set I have zero context on (deleted `bridge_state_store.py`/`lp_concentrated_dispatch.py`
      /`live_bridge_adapter.py`, modified routing/handler files) — judging whether it's safe to stash/commit requires
      execution-service domain knowledge and repo ownership this AO worker (role: review, task scope: PM docs) does
      not have. **BLOCKED-OPERATOR-DECISION**: recommend the operator either (a) confirm with whoever owns
      `slot-2`/the `execution-service` transfer refactor whether this WIP is abandoned and safe to stash/discard, or
      (b) if confirmed dead, have someone with execution-service context run the sanctioned
      `git stash push --include-untracked -m 'orchestrator-slot-16-<task_id>'` recovery themselves. Until then this
      stays a live-adjacent block from the done-gate's perspective (unactioned, not unresolved-observation).
- [ ] [SCRIPT] P2. **NARROWED 2026-08-21**: since `scripts/quickmerge.sh --isolated` is now evidenced NOT to be the
      creator (see todo 1 above), this todo is no longer "fix quickmerge.sh's path resolution" — it is instead
      **locate the actual tool that creates `<tag>-wt.<random>`-style directories flat inside `.tabs/<N>/`** (grepped
      clean across every repo's `scripts/`+top-level `*.sh`/`*.py`+`unified-trading-ci`'s workflows — try the peer
      directly, or a broader host-wide search e.g. `find / -newer <ref> -iname '*-wt.??????'` type approaches an
      AO worker shouldn't run unbounded) before any fix can be scoped. Once located: same original intent — make it
      nest under the INVOKING session's own slot directory or a done-gate-excluded shared location.
- [ ] [SCRIPT] P2. **Alternatively/additionally**: harden `/api/slots/<N>/done`'s dirty-check to recognize and skip a
      nested `oms-wt.*`/other-slot-owned worktree (distinguishable via its own commit author identity not matching
      slot N's own configured identity) rather than treating it as slot N's own WIP — this closes the symptom even if
      the root-cause path-resolution bug above turns out to be by-design/unfixable.
- [ ] [REVIEW] P3. **Once the fix lands**: verify by re-checking `.tabs/16/` (or whichever slot next reproduces the
      symptom) no longer shows a foreign worktree's dirty state blocking its own `/done` calls.

## Progress Log

- **2026-08-21 (slot-16), formal escalation** — Filed a structured `/api/slots/16/blocked` call (not just this doc)
  so the finding reaches the operator dashboard directly rather than waiting to be found: `blocked_id: BLK-f5b3466f`,
  options A (operator confirms dead -> authorize slot-tagged stash), B (confirms still needed -> harden the done-gate
  to skip foreign-owned worktrees instead, RECOMMENDED), C (execution-service owner finishes/commits it themselves).
  `can_continue: false` reported honestly — no other task is available (repeated `/heartbeat` calls this session all
  re-dispatched this same task) and touching the foreign WIP myself is out of scope. Answer will arrive as a message
  on the next `/progress`/`/heartbeat` call.
- **2026-08-21 (slot-16)** — Filed after the pattern recurred 3x in one session across 2 unrelated tasks. No code
  investigated/changed — pure observation + escalation, since directly probing `quickmerge --isolated`'s internals
  mid-session would have meant editing shared script files outside this task's scope while a live peer session was
  actively working nearby.
- **2026-08-21 (slot-16), post-compact re-check** — Re-confirmed still live: `oms-wt.oc3YkB`'s HEAD commit was 319s
  old at check time (author `github-actions[bot]`, not the earlier-seen `ikennaigboaka [slot-2·laptop]` — the
  authoring identity on this worktree is not stable across commits, consistent with a bot/CI process periodically
  committing into the same live session rather than a single human's commits). `/api/slots/16/done` retried against
  `http://localhost:8765` (unauthenticated — see the worker.md auth-gap fix landed same commit) and rejected again
  with the identical `oms-wt.oc3YkB` dirty-file list (30 files, same set as before). Per pre-compact Step 7.2, two
  identical consecutive failures = stable condition, not flapping — stopped retrying; the already-shipped todo-1 work
  (`unified-trading-pm@832b8de031`+`19d99de82a`) stays acked-pending, no data at risk since it's already on origin.
- **2026-08-21 (slot-16), post-/heartbeat resume** — Third check, new session tick: `/heartbeat` re-dispatched the
  identical task (`dispatch_reason: "resume"`), confirming the server itself still considers this task open pending
  `/done`. `oms-wt.oc3YkB` HEAD had advanced to a new commit (still `github-actions[bot]`) but the staged dirty-file
  set was byte-identical to the two prior checks (same 30 files, same M/D markers) — the live session is committing
  but never reaching a clean staged tree. `/done` retried once more (3rd attempt, spaced across a full compaction
  cycle, not blind-looped) and rejected with the identical dirty list. This is now a 3x-identical stable condition
  across ~1hr+ of wall-clock time, not a transient race — raises confidence this is a long-lived, possibly-stuck-open
  live session (or one that will simply never present a clean tree until it finishes its own multi-commit sequence),
  strengthening todo 3's case (harden the done-gate to skip foreign-owned worktrees) as the more tractable fix vs.
  waiting for `oms-wt.oc3YkB` to clear naturally. Stopped retrying again per Step 7.2; no further `/done` attempts
  planned until either this worktree disappears or todo 3 lands.
