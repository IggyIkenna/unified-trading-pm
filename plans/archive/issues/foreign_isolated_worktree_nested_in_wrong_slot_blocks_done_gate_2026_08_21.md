---
doc_type: issue
title: A quickmerge --isolated worktree from a DIFFERENT slot/session appears nested inside slot 16's own directory tree
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
status: resolved
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

> **CORRECTION (2026-08-21, slot-14) — the title's core premise is wrong.** `oms-wt.oc3YkB` is **NOT** a foreign
> worktree from a different slot — its own `.git` file's `gitdir:` pointer resolves to
> `.tabs/16/execution-service/.git/worktrees/oms-wt.oc3YkB` (confirmed both directions via the reverse `gitdir`
> pointer too), i.e. its parent clone IS slot 16's own `execution-service` checkout. It sits correctly inside its
> own slot. The commit-author identities below (`slot-2·laptop`, bots) are a genuine red herring — see todo 3's
> resolution and the 2026-08-21 (slot-14) Progress Log entry for the full evidence. Left the sections below
> unedited as the historical record of what was observed; do not re-chase the "wrong slot" hypothesis.

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
- [x] [REVIEW] P1. **CORRECTION, 2026-08-21 (slot-16): the earlier "confirmed live" verdicts (Progress Log entries
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
      **STILL OPEN 2026-08-21 (slot-14)**: unchanged by this session's work — todos 3/4's fix stops this WIP from
      blocking OTHER slots'/sessions' unrelated `/done` calls, but does not touch or resolve the WIP itself. The
      operator decision on whether it's safe to stash/discard is still needed.
      **RESOLVED 2026-08-21 (interactive slot 15, operator-directed)**: operator reviewed this doc's own evidence
      and directed discard. Re-verified before acting: same state persists, now 8h+ stale (file mtime unchanged at
      11:47 vs a 19:50 check), byte-identical 160-file staged diff, no live process (the only `pgrep` hit was a
      self-match on the search command's own argument — the identical false-positive trap this doc's REVIEW todo
      above already flagged and corrected). Confirmed via `grep` that no active plan references `deribit` or
      `execution_service/venues` — the staged content (a new Deribit venues facade module + a DeFi-protocol
      idempotency-removal refactor) has no backing design doc anywhere, and the OMS-persistence work its branch
      name references is separately, fully shipped already
      (`w_execution_orchestrator_oms_persistence_impl_2026_08_21.md`,
      `execution-service@bc2edc16874a3b0828ef692682b69174ddcab4bf` confirmed ancestor of
      `origin/live-defi-rollout`) — so nothing valuable was at risk. Resolved per the sanctioned recovery path
      above: `pyproject.toml`'s one conflict (trivial version-pin mismatch) taken to HEAD, remainder
      `git stash push`ed (parked as `stash@{0}` on the `execution-service` worktree, recoverable). Also pruned 5
      unrelated `prunable` isolated-quickmerge worktree registrations found alongside it (dirs already gone, pure
      bookkeeping cleanup). Full detail: `fleet_dispatch_stall_gemini_proxy_alias_mismatch_2026_08_21.md`'s
      quarantined-slot-WIP todo.
- [x] ✅ [SCRIPT] P2. **NARROWED 2026-08-21**: since `scripts/quickmerge.sh --isolated` is now evidenced NOT to be the
      creator (see todo 1 above), this todo is no longer "fix quickmerge.sh's path resolution" — it is instead
      **locate the actual tool that creates `<tag>-wt.<random>`-style directories flat inside `.tabs/<N>/`** (grepped
      clean across every repo's `scripts/`+top-level `*.sh`/`*.py`+`unified-trading-ci`'s workflows — try the peer
      directly, or a broader host-wide search e.g. `find / -newer <ref> -iname '*-wt.??????'` type approaches an
      AO worker shouldn't run unbounded) before any fix can be scoped. Once located: same original intent — make it
      nest under the INVOKING session's own slot directory or a done-gate-excluded shared location. **RESOLVED
      2026-08-21 (slot-14) — no tool located, ruled out with source evidence (full detail in Progress Log)**:
      quickmerge `--isolated`, `safe-doc-push.sh`'s always-on isolation, and `ship-from-worktree.sh` all root under
      `${TMPDIR:-/tmp}` with the literal repo name as leaf — none produce a flat `.tabs/<N>/<tag>.<random6>` path.
      Also checked this host's shell configs/`~/.local/bin`/crontab/systemd — nothing matches. Conclusion: no
      reusable tool exists; this is an ad-hoc `git worktree add` a worker session ran directly. **Also corrects this
      doc's own title/premise** (see the correction banner at the top): `oms-wt.oc3YkB`'s `gitdir` pointer resolves
      to slot 16's OWN `execution-service` clone — not a foreign slot's. "Nest under the invoking slot" was already
      true; the actionable remainder ("done-gate-excluded shared location") is implemented as todo 4 below — one
      commit closes both. — agent-orchestrator@01a82fd9f3
- [x] ✅ [SCRIPT] P2. **Alternatively/additionally**: harden `/api/slots/<N>/done`'s dirty-check to recognize and skip a
      nested `oms-wt.*`/other-slot-owned worktree (distinguishable via its own commit author identity not matching
      slot N's own configured identity) rather than treating it as slot N's own WIP — this closes the symptom even if
      the root-cause path-resolution bug above turns out to be by-design/unfixable. **DONE 2026-08-21 (slot-14),
      implemented differently than proposed**: commit-author identity is unreliable (proven a red herring by todo 3
      — it reflects whichever upstream commit a routine fast-forward last pulled in, not who created the worktree).
      Instead: `worktree_clean_check._report.check_slot_clean` now tags each `RepoDirtyReport.is_linked_worktree`
      (`.git` is a FILE, not a DIR) — reliable because no sanctioned isolation tool ever places a worktree flat under
      `.tabs/<N>/` (see todo 3), so a `.git`-file worktree found there is, by construction, never the current task's
      own shippable-unit WIP. `slots_worker._enforce_done_clean_gate` now excludes worktree-only dirt from the 409
      block (still blocks on any real primary-checkout dirt — verified via a mixed-dirt test) and logs it
      non-blocking instead. Deliberately did NOT change `SlotCleanReport.is_clean`'s own semantics or touch
      `_resolve.py`'s FM2/FM3/FM8 orphan-WIP coordinator, `slot0_self_clean.py`, or the `slots_ops.py` pre-spawn
      check — all consume `check_slot_clean` too but were out of this task's verified scope. New tests:
      `test_check_slot_clean_flags_linked_worktree_flat_under_slot`,
      `test_done_gate_ignores_dirty_linked_worktree_flat_under_slot`,
      `test_done_gate_blocks_on_primary_dirt_but_excludes_dirty_linked_worktree_from_payload`. Full
      `quality-gates.sh` green (5300 passed/2 skipped Python; 468/468 dashboard). —
      agent-orchestrator@01a82fd9f3
- [x] ✅ [REVIEW] P3. **Once the fix lands**: verify by re-checking `.tabs/16/` (or whichever slot next reproduces the
      symptom) no longer shows a foreign worktree's dirty state blocking its own `/done` calls. **VERIFIED
      2026-08-22 (slot-14)**: (1) confirmed `agent-orchestrator@01a82fd9f3` is an ancestor of
      `origin/live-defi-rollout` (`git merge-base --is-ancestor`, passed); (2) confirmed the live code —
      `worktree_clean_check/_report.py:350` sets `is_linked_worktree = (child / ".git").is_file()`, and
      `slots_worker.py:1382` builds `blocking_repos` as `[r for r in clean_report.dirty_repos if not
      r.is_linked_worktree]`, i.e. linked-worktree dirt is structurally excluded from the 409 trigger; (3) live-probed
      the actual `oms-wt.oc3YkB` worktree still sitting at `.tabs/16/oms-wt.oc3YkB` — its `.git` is confirmed an
      ASCII-text file (not a directory, so `is_linked_worktree` resolves `True` for it) and it is still dirty (75
      changed files via `git status --porcelain`), i.e. exactly the shape the fix targets. This confirms the fix is
      live and structurally correct for the reproducing case; did not additionally exercise a live `/done` call
      against slot 16 (out of scope / another slot's active session) since the code-path + live-fixture check above is
      sufficient. `oms-wt.oc3YkB` itself remains untouched — todo 2's operator-gated stash/discard decision is
      unaffected by this verification. — unified-trading-pm@$SHA

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
- **2026-08-21 (slot-14)** — Resolved todos 3 & 4 in one commit, `agent-orchestrator@01a82fd9f3`.
  **Tool search (todo 3)**: ruled out every candidate with source-level evidence — `quickmerge.sh`'s `--isolated`
  mode (`_qm_iso_wt="$_qm_iso_parent${_qm_slot_seg}/$_qm_repo_name"`,
  `_qm_iso_parent="${TMPDIR:-/tmp}/qm-iso-$$"`) and `safe-doc-push.sh`'s always-on isolation
  (`_sdp_iso_wt="$_sdp_iso_parent${_sdp_slot_seg}/unified-trading-pm"`, same `/tmp`-rooted parent shape) both use
  the LITERAL repo name as the leaf directory, never a dot-random suffix, and always root under
  `${TMPDIR:-/tmp}`; `ship-from-worktree.sh` names `${TMPDIR:-/tmp}/ship-wt-<repo>-<timestamp>-<pid>/<repo>` — same
  story. Also checked this host's `~/.bashrc`/`~/.bash_aliases`/`~/.profile`/`~/.local/bin/*.sh`/`~/.local/bin/*.py`
  /`crontab -l`/`/etc/cron.d`/systemd units for a personal tool matching `worktree|mktemp.*wt|oms-wt|pm-ship` —
  nothing. Conclusion: no reusable tool exists; `oms-wt.oc3YkB` (and the similarly-shaped `pm-ship.MpuQMt`,
  `pm-pred-XprePf`, `pm-qg-origin-N3l1QW` found in a fleet-wide `find .tabs -path '*/.git/worktrees/*'` sweep
  across other slots) is an ad-hoc `git worktree add` a worker session ran directly, inventing its own tag on the
  spot — not a bug in any committed tool.
  **Premise correction**: the same fleet-wide sweep located `oms-wt.oc3YkB`'s admin registration at
  `.tabs/16/execution-service/.git/worktrees/oms-wt.oc3YkB`, and the worktree's own `.git` file content
  (`gitdir: .tabs/16/execution-service/.git/worktrees/oms-wt.oc3YkB`) round-trips back to the same path — i.e. its
  parent clone IS slot 16's own execution-service checkout, not a foreign slot's. The commit-author identities
  this doc's earlier entries chased (`slot-2·laptop`, `github-actions[bot]`, `uts-backmerge-bot`) were a genuine
  red herring: the worktree's own `logs/HEAD` reflog shows every `merge origin/live-defi-rollout: Fast-forward`
  entry authored `ikennaigboaka [slot-16·planning]` — slot 16's OWN sessions did every fast-forward, via
  `worker.md`'s routine fresh-pull loop (`[ -e "$repo_dir/.git" ]` is true for a worktree `.git` FILE exactly as
  for a primary clone `.git` DIR — the loop's own comment already documents this tolerance: "`-e` also tolerates a
  legacy worktree `.git` FILE if any remain"). Each fast-forward pulled in whatever was on
  `origin/live-defi-rollout` at the time, including bot-authored upstream commits already in history — that's what
  produced the shifting author appearance across checks; nothing about it implies a different slot or a live human
  session. The reflog also shows `checkout: moving from slot16-oms-persistence to live-defi-rollout` — a named
  branch matching (by naming convention only; content does NOT match — the staged files are DeFi-transfer/bridge/
  repricer work, not the OMS-persistence plan's own files, which touch `postgresql.py`/`order_adapter.py`/`oms.py`
  instead) `w_execution_orchestrator_oms_persistence_impl_2026_08_21.md`, confirming this was a deliberate, if
  undocumented, worktree some session set up and later abandoned — not evidence the staged content itself came
  from that plan.
  **Fix (todo 4, converges with todo 3's own "done-gate-excluded shared location" alternative)**: since "nest
  under the invoking slot" was already true, the fix targets the done-gate directly rather than a worktree-creation
  path. `worktree_clean_check._report.check_slot_clean` now tags each `RepoDirtyReport.is_linked_worktree`
  (`.git` is a file vs. a directory); `slots_worker._enforce_done_clean_gate` splits `dirty_repos` into blocking
  (primary-checkout) vs. non-blocking (linked-worktree) before deciding whether to raise the 409, logging the
  non-blocking set instead of silently dropping it. Deliberately did NOT change `SlotCleanReport.is_clean`'s own
  semantics (kept it meaning "any dirty repo at all") or touch `_resolve.py`'s FM2/FM3/FM8 orphan-WIP coordinator,
  `slot0_self_clean.py`, or the `slots_ops.py` pre-spawn check — all three also consume `check_slot_clean` and
  were read (call sites enumerated) but not modified, since verifying their correctness under a changed `is_clean`
  was outside this task's scope; the fix is scoped to `_enforce_done_clean_gate` alone. Todo 2 (whether
  `oms-wt.oc3YkB`'s own staged DeFi-transfer WIP is safe to stash/discard) remains untouched and still gated on
  that same operator decision as before — this fix only stops it from blocking OTHER unrelated `/done` calls, it
  does not resolve or touch the WIP itself. Evidence: `quality-gates.sh` full run green (5300 passed, 2 skipped
  Python; 468/468 dashboard TS), 3 new tests added covering the tag + both the worktree-only-non-blocking and
  mixed-dirt-still-blocks cases, `agent-orchestrator@01a82fd9f3` ancestry-verified on `origin/live-defi-rollout`.
