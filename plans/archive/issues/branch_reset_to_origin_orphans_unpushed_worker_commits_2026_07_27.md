---
doc_type: issue
title: >-
  A per-slot "branch: Reset to origin/live-defi-rollout" hard-reset silently ORPHANED unpushed local worker commits in
  ≥2 slots around the 2026-07-27T16:55Z mass tmux reap — data-loss-class, the committed work is dropped off the branch
  (reflog-only, GC-eligible) and its content is NOT on origin. slot-14 (docs) recovered + pushed by main; slot-13 (a
  features-service code commit) still pending a worker quickmerge recovery.
summary: >-
  On 2026-07-27, following the mass tmux_session_lost reap at ~16:55Z (~16 slot sessions batch-reaped fleet-wide), the
  review role's git-health sweep flagged several dead slots (worker_alive=false, tmux_alive=false) carrying a single
  real, coherent, UNPUSHED local commit each. Investigating from the orchestrator vantage, main (agt-4d8de7) found the
  cause is worse than "unpushed": each affected worktree's `live-defi-rollout` branch had been HARD-RESET to origin via
  a reflog `branch: Reset to origin/live-defi-rollout` entry, which DROPPED the worker's committed work off the branch
  entirely. The commits survive only in the per-worktree reflog (GC-eligible, default 90d) and, critically, their
  CONTENT is NOT present on origin/live-defi-rollout — verified by diffing the orphaned blob against the origin blob
  (they differ; the orphaned commit's additions are absent upstream). This is data-loss-class, not cosmetic drift: a
  worker commits, the session dies in the reap, and something resets the branch to origin before the commit is pushed,
  so the work is silently gone from every branch. Two confirmed cases this host (ip-172-31-5-118): slot-14
  unified-trading-pm commit 0aa00b715 (docs(plans) Track C K1/K2 flip) and slot-13 features-service commit 207afd62
  (feat(scripts) census-manifest persistence, a dependency of the sports derived-features residue purge todo). Both
  patches were extracted to a durable host-local path before any further reset could GC them. A THIRD, distinct sub-case
  (slot-0 root PM clone) was staged-but-uncommitted WIP — different failure mode, already recovered separately
  (unified-trading-pm@7a5ffbd44). Likely shared root cause with the per-slot cron staleness observed the same day (disk
  resize 290G→484G + 2 orchestrator restarts) — see related issue. P1: this destroys committed worker output.
status: resolved
assigned_vm: NA
resolved_by:
locked_by:
nature: issue
asset_group: [ao] # corrected 2026-07-30 (/ag-closeout-audit ao) -- was [cross-cutting]; per-slot worktree/branch-reset
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm, features-service]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    per-slot-worktrees,
    ff-pull,
    branch-reset,
    data-loss,
    unpushed-commits,
    orphaned-commit,
    reflog,
    fleet-git-health,
  ]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/archive/issues/per_slot_ff_pull_status_report_crons_stale_fleet_wide_2026_07_27.md,
  ]
created: 2026-07-27
last_updated: 2026-07-30
priority: P1
parent_epic: orchestrator_master
source:
  "review role (msg 2392 + 2395 to main agt-4d8de7) reported dead slots with unpushed commits; main (agt-4d8de7)
  investigated, found the branch-reset-orphaning mechanism, recovered slot-0 (7a5ffbd44) + slot-14 (ae03d60ab), saved
  both orphaned patches, and captured this so the finding survives compaction (review role never commits)."
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# Branch-reset-to-origin silently orphans unpushed worker commits (data-loss)

> **ARCHIVED (2026-07-30) — complete.** All recovery + root-cause todos resolved: the mechanism was root-caused
> (`quickmerge.sh`'s `cascade_dep_branch()` unconditional `git checkout -B`, tracked/fixed in
> `utl_shared_clone_commits_repeatedly_reset_2026_07_22.md`); every listed orphaned commit was verified either already
> re-landed on origin (re-landing would have regressed it) or genuinely gone with no recoverable content. The
> unrouted-recovery-authority gap this doc surfaced was spun off into
> `/plans/archive/issues/orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md`.

## What happened (evidence)

Two worktrees on host `ip-172-31-5-118`, both on dead slots after the 16:55Z reap, showed identical reflog signatures:

**slot-14** (`.tabs/14/unified-trading-pm`), reflog:

```
0aa00b715 HEAD@{4}: pull --rebase … (pick): docs(plans): flip Track C K1/K2 re-verify todo …
0aa00b715 HEAD@{3}: pull --rebase … (finish): returning to refs/heads/live-defi-rollout
9bc93746a HEAD@{2}: branch: Reset to origin/live-defi-rollout   ← DROPS 0aa00b715
9bc93746a HEAD@{1}: checkout: moving from live-defi-rollout to live-defi-rollout
```

**slot-13** (`.tabs/13/features-service`), reflog:

```
207afd62  HEAD@{2}: commit: feat(scripts): persist a stable census manifest on every purge script invocation
96ac35a2  HEAD@{1}: branch: Reset to origin/live-defi-rollout   ← DROPS 207afd62
96ac35a2  HEAD@{0}: checkout: moving from live-defi-rollout to live-defi-rollout
```

In both, a `branch: Reset to origin/live-defi-rollout` moved HEAD off the worker's committed work to the origin tip.
Confirmed the content is genuinely NOT upstream: `git diff <orphan>:<file> origin/live-defi-rollout:<file>` shows the
orphaned commit's additions absent on origin (for slot-13, the `_CENSUS_MANIFEST_PATH` / `_write_census_manifest()`
additions; for slot-14, the two plan-todo flips).

## Durable rescue (done)

Both orphaned patches saved host-local before any GC:

- `/home/ubuntu/unified-trading-system-repos/.orch-orphan-commits-recovery/slot14_0aa00b715_docs.patch`
- `/home/ubuntu/unified-trading-system-repos/.orch-orphan-commits-recovery/slot13_207afd62_code.patch`

(Host-local, untracked — a same-host worker can read them; a cross-host worker should cherry-pick the SHA from the
worktree reflog or re-derive from this doc.)

## Recovery status

- [x] slot-14 `0aa00b715` (docs) — cherry-picked onto origin tip + pushed by main, landed
      `unified-trading-pm@ae03d60ab`.
- [x] slot-0 root PM staged WIP (distinct sub-case) — recovered `unified-trading-pm@7a5ffbd44`.
- [x] ✅ **SUPERSEDED 2026-07-30 (bounded recovery sweep, infra role) — do NOT cherry-pick; it would REGRESS origin.**
      The same worker re-landed this feature **27 minutes later** as `features-service@a90256f5` (2026-07-27T17:17:50Z,
      "feat(sports): always write stable derived_features residue census manifest") — origin's version is the same
      capability with better naming (`_STABLE_CENSUS_MANIFEST_PATH` / `_write_stable_census_manifest()` vs the orphan's
      `_CENSUS_MANIFEST_PATH` / `_write_census_manifest()`) and a sharper docstring. A `git diff` of origin against
      `207afd62` is net-negative on `scripts/purge_sports_derived_features_post_floor_residue_2026_07_27.py`, so
      applying the orphan would undo the rename and the docstring. The stated dependency is satisfied: the follow-up
      purge todo's stable census-manifest GCS path exists on origin today. Original instruction preserved: cherry-pick
      the orphaned commit onto current `origin/live-defi-rollout`, then SHIP VIA QUICKMERGE
      (`bash scripts/quickmerge.sh "feat(scripts): persist stable census manifest on purge invocation     (recovered orphaned slot-13 commit 207afd62)" --agent --files 'scripts/purge_sports_derived_features_post_floor_residue_2026_07_27.py'`).
      Code MUST go through quickmerge (QG + provenance trailer); a raw push is banned and would be rejected by the
      strict-quickmerge pre-push hook. This enhancement is a dependency of the sports derived-features residue purge
      todo (the follow-up purge reads the stable census-manifest GCS path this commit writes).

### Second wave — CONFIRMED RECURRENCE at the ~23:50Z reap (main agt-4d8de7, 2026-07-27T23:54Z)

The bug fired again on two more slots, and this time main directly CONFIRMED the orphaning mechanism from the live
reflog (not inferred) — proof the runtime respawn / orphan-wip-inheritance path does NOT recover a committed-ahead code
commit; it resets the branch to origin and drops it:

- **slot-13 `d1c1ad8a`** (features-service CODE,
  `fix(delta_one): wire per-venue accepted-quote extension into universe filter` + test) — **CONFIRMED ORPHANED.**
  `git merge-base --is-ancestor d1c1ad8a origin/live-defi-rollout` → NO (not on origin). Worktree HEAD is now `a9429cba`
  (== origin). Reflog: `d1c1ad8a HEAD@{2}: commit …` → `a9429cba HEAD@{1}: branch: Reset to origin/live-defi-rollout` →
  drops it. DISTINCT, later commit from the `207afd62` above (slot-13 did multiple pieces of work across the session,
  each orphaned in a successive reap). Backstop patch:
  `.orch-orphan-commits-recovery/slot13_d1c1ad8a_features-service.patch`.
- **slot-11 `ffc02a8c`** (market-tick-data-service CODE,
  `fix(sports): add consecutive-non-422-failure counter to odds_api_adapter fetch loop` +
  `test_odds_api_consecutive_failures.py`) — **RECLASSIFIED 2026-07-28T00:29Z (main): NOT a dead orphan — LIVE-owned
  blocked-WIP, PROTECTED.** When msg 2450 flagged it the slot read dead; it has since RESPAWNED. Re-verified
  `/api/state`: slot-11 is flapping/booting (`tmux_alive=true`, `tmux_session=orch-slot-11`, `status=working`,
  `phase=pre_boot`, last_msg "waiting on repo-blocker RB-6ee2583c"). `ffc02a8c` is still `ahead=1` (NOT reset/orphaned;
  `merge-base` deferred because touching a live slot's worktree is banned). The live worker committed locally and is
  holding the push until RB-6ee2583c clears — legit blocked-WIP, not data loss. Liveness gate → PROTECT, do NOT recover.
  Backstop `.orch-orphan-commits-recovery/slot11_ffc02a8c_market-tick-data-service.patch` RETAINED only as a safety net
  should the in-flight respawn's branch-reset orphan it (third-wave PM-docs case proves that risk is real); it becomes a
  recovery candidate ONLY if a future reflog confirms `branch: Reset` dropped it. Corrected per review msg 2459.

### Fourth wave — the ROOT-CAUSE FIX itself is now orphan-at-risk on dead slot-5 (main agt-4d8de7, 2026-07-28T00:33Z)

> **🛑 SUPERSEDED 2026-07-28T01:1x (main agt-4d8de7): this wave's PREMISE IS WRONG — do NOT recover slot-5
> `3becc9ede`/`28ee61192`.** slot-7 landed an audit on origin (`unified-trading-pm@408a92200`, status=resolved) that
> CLEARS `scripts/dev/slot-cron-ff-pull.sh` — the SECOND independent confirmation. Its only ref-mutating paths are
> `git merge --ff-only` (fails, never resets) + a patch-id-verified adopt-rebase; it is NOT the branch-reset mechanism,
> so commit `3becc9ede`/`28ee61192` (`fix(ci): harden slot-cron-ff-pull.sh`) targets a MISDIAGNOSED cause and must NOT
> be landed. The REAL mechanism for the `branch: Reset to origin/live-defi-rollout` signature is `quickmerge.sh`
> `cascade_dep_branch()` (`git checkout -B`), already root-caused + partially fixed in
> `/plans/archive/2026_08/issues/utl_shared_clone_commits_repeatedly_reset_2026_07_22.md` (preserve-guard `06dc7632`; independent
> fetch-bug fix `8ca436599`). slot-5 has since reset to origin and dropped the commit — a benign instance of that
> tracked cascade reset. Backstops renamed `SUPERSEDED_by_408a92200_*`. **Live risk to chase there, NOT here:** why the
> preserve-guard did not fire for the 07-27 `unified-trading-library` discards (`61efd2e5`/`dbb93c3a`, now unreachable)
> — owned by the cascade_dep_branch canonical doc.

The runtime/operator had already dispatched a task to fix this very bug — **`slot_cron_ff_pull_toctou_reset_race-001`**
(the TOCTOU reset race in the ff-pull cron is the confirmed mechanism). slot-5 took it and COMPLETED the fix:

- **slot-5 `3becc9ede`** (unified-trading-pm CODE, `scripts/dev/slot-cron-ff-pull.sh`,
  `fix(ci): harden slot-cron-ff-pull.sh adopt-rebase against a check-then-act HEAD-moved window`, +39/-6). Slot-5 is
  **confirmed DEAD** (worker_alive=false, tmux_alive=false, tmux_session=null, last_ping 00:25:52Z, status=idle). Commit
  is still `ahead=1`, NOT yet orphaned (reflog HEAD@{0}=the commit over clean ff-pulls; no `branch: Reset` yet) — but a
  respawn would orphan it via the same bug it fixes. Backstop:
  `.orch-orphan-commits-recovery/slot5_3becc9ede_pm-scripts-ff-pull-hardening.patch`. **This is the highest-priority
  recovery of the set: landing it stops the bleeding.** CODE → main cannot quickmerge unilaterally; escalated with
  elevated priority.
  - **UPDATE 00:41Z:** slot-5 respawned and its ff-pull cron did the CORRECT thing this cycle — a
    `pull --rebase --autostash` cleanly REBASED the commit onto new origin tip `7f0c400ec`, so the fix now lives at
    **`28ee61192`** (identical +39/-6 content; `3becc9ede` is its pre-rebase sha, NOT orphaned — rebase preserved it).
    Slot-5 is now flapping (`tmux_alive=true`, `worker_alive=false`). Recovery TARGET is the current ahead HEAD of
    `.tabs/5/unified-trading-pm` (`28ee61192` as of now) or the saved backstop patch (content-identical) — do NOT chase
    the stale `3becc9ede` sha. Data point: the TOCTOU reset race is INTERMITTENT (it rebased cleanly here,
    reset-orphaned the PM docs earlier) — consistent with a check-then-act window that only sometimes loses the race.

- [x] ✅ **ALL THREE SUPERSEDED 2026-07-30 (bounded recovery sweep, infra role) — none recovered, none needed; each
      would have REGRESSED origin.** Verdicts, measured on `ip-172-31-5-118` read-only over SSM: **(1) slot-13
      `d1c1ad8a`** (features-service) → re-landed by the same slot **35 minutes later** as `a9429cba`
      (2026-07-27T23:27:46Z, "fix(delta_one): make universe-filter quote gate venue-aware"). Origin keeps the
      `@functools.cache _sorted_quotes_for_venue()` helper delegating to `accepted_quotes_for_venue` — which the orphan
      _deleted_ in favour of a flat `_SORTED_QUOTES`. `git diff --stat origin d1c1ad8a` on the test file is **+24/−49**;
      applying it would delete 49 lines of landed tests. Origin's per-venue accepted-quote wiring is confirmed present
      (`accepted_quotes_for_venue` at `mvp_universe_filter.py` lines 48/61/64/71/97/111). **(2) slot-9 `724bd9be`**
      (unified-api-contracts) → landed on origin as `698b5b6f` with the **identical subject** and **byte-identical
      content**: both `order_semantics.py` and `test_order_semantics_sim_backfill.py` have the same blob sha in the
      orphan and on origin. `.tabs/9/unified-api-contracts` now measures `ahead=0`. **(3) slot-12 `559452e`**
      (agent-orchestrator) → the route shipped independently as `09cda29` ("feat(backlog): add POST
      /api/backlog/{id}/reconcile-brief escape hatch"); origin carries the live route at `server/routes/backlog.py:391`
      plus a 225-line `tests/test_backlog_reconcile_brief.py`. `git diff --stat origin     559452e` across the 4 files
      is **+290/−347**, i.e. recovering it would overwrite the shipped implementation with the orphan's earlier one. The
      backstop patches under `.orch-orphan-commits-recovery/` can be retired. Original instruction preserved below for
      context: recover the confirmed dead-orphan CODE commits — **REVISED PRIORITY ORDER 2026-07-28 (slot-5 DROPPED —
      see SUPERSEDED banner above; its fix targeted a misdiagnosed cause):** (1) slot-13 `d1c1ad8a` (features-service),
      (2) slot-9 `unified-api-contracts` `724bd9be` (`fix(registry)` VENUE_ORDER_SEMANTICS CCXT live-routed), (3)
      slot-12 `agent-orchestrator` `559452e` (`feat` `/api/backlog/{id}/reconcile-brief` route + 240-line test, +417).
      Do NOT recover slot-5 `3becc9ede`/`28ee61192` (superseded by audit `408a92200`). Do NOT recover slot-11 `ffc02a8c`
      while slot-11 is alive (reclassified LIVE-owned blocked-WIP above). For each: cherry-pick from `.tabs/<n>/<repo>`
      reflog (or apply the saved backstop patch) onto current `origin/live-defi-rollout`, then SHIP VIA QUICKMERGE
      (`--agent --files <the named file(s)>`). All clean + complete (review-verified where noted). Code MUST go through
      quickmerge (QG + provenance trailer). Backstops for slot-9/12 saved this session (`slot9_724bd9be_*.patch`,
      `slot12_559452e_*.patch`).

> **✅ DISPATCH GAP CLOSED 2026-07-30 — route (a) authorized and executed; all recovery todos above are now flipped
> SUPERSEDED.** The operator authorized a single named infra-role worker to run one bounded, liveness-gated recovery
> sweep. Outcome across the whole cross-doc inventory: **8 SUPERSEDED, 1 PROTECTED-LIVE, 1 GONE, 0 recovered — because 0
> needed recovering.** Every orphan this doc chased had already been re-landed on origin (twice by the same worker
> within 35 minutes of the orphaning), and 4 of them would have REGRESSED origin if cherry-picked blind. The content was
> never at risk; what the 3-day unrouted escalation cost was 3 days of carrying a false P1 data-loss exposure. The
> durable fix is therefore a cheap read-only "is this orphan still orphaned?" verifier, not recovery authority — filed
> as `[SCRIPT] P2` in `/plans/archive/issues/orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md`, which also
> carries the full per-item evidence, the liveness-gate results, and two further findings (a 25-strong fleet-wide
> `refs/wip-preserve/**` population, and a liveness discriminator that trusts `.agent-claim` age too much). **Original
> banner, preserved:** these `[WORKER]` recovery todos live in an `assigned_vm: NA` issue doc, so they are NOT
> auto-dispatched to any worker — they will rot unless (a) migrated into a dispatched plan (`assigned_vm: planning`),
> (b) a worker is explicitly routed to them, or (c) main is authorized to run the quickmerge recovery directly. Content
> is not lost yet (backstop patches host-local on `ip-172-31-5-118` + 90d reflog), but this is why the first-wave
> `207afd62` todo has also sat unrecovered. Escalated to operator for routing.

### Third wave — the branch-reset dropped the runtime's OWN orphan-wip inheritance commit (main agt-4d8de7, 2026-07-28T00:25Z)

The most damning evidence yet: on slot-11's `unified-trading-pm` worktree, the runtime's pre-spawn dirty-state gate
correctly committed the dead predecessor's dirty WIP as `65c5b0a69`
(`chore(orphan-wip): inherited WIP from predecessor on slot 11 at 2026-07-28T00:18:03Z`,
`DirtyStateResolution.COMMIT_AND_PUSH`) — and then, within the SAME spawn, a `branch: Reset to origin/live-defi-rollout`
orphaned that very commit before it was pushed. Reflog: `65c5b0a69 HEAD@{3}: commit …` →
`fe7b19392 HEAD@{2}: branch: Reset to origin/live-defi-rollout` → FF-merge to `cd5c0bde1`.
`merge-base --is-ancestor 65c5b0a69 origin/live-defi-rollout` → NO. This proves the COMMIT_AND_PUSH resolution's
"…AND_PUSH" half never fires (or is undone by the reset) — the gate commits, the reset drops it, and nothing reaches
origin. **The orphan-wip mechanism is not a safety net; it is itself a victim of the reset.**

Payload was three DOCS (all main-recoverable): the new issue doc `defi_mev_events_pagination_gap_2026_07_28.md` (+112,
**untracked in the original WIP → zero reflog recovery for the source file; would have been permanently lost**), its
`[PM] P1` todo flip in `defi_satellite_ao_dispatch_batch1_2026_07_25.md`, and the archived-source xref update. A
coherent complete unit (a worker's finished `[PM] P1`).

- [x] slot-11 `65c5b0a69` (PM DOCS) — RECOVERED by main via docs carve-out (applied backstop patch onto origin tip,
      pushed `unified-trading-pm@9237aee43`). Backstop:
      `.orch-orphan-commits-recovery/slot11_65c5b0a69_orphan-wip-pm-docs.patch`.

**Root-cause note this adds:** whatever emits the reset runs AFTER the orphan-wip commit within the same spawn sequence
— so the fix target is narrowed: the spawn/re-init path itself resets the branch to origin immediately after its own
dirty-commit, discarding it. The dirty-state gate and the reset are the same code path's two halves and they contradict
each other.

## Investigation (root cause)

- [x] ✅ **RETAGGED from `[OPERATOR]` and RESOLVED (2026-07-28 gate-cleanup pass) — not an operator judgment call, a
      worker-determinable fact, now determined.** Re-grepped `unified-trading-pm/scripts/quickmerge.sh` to confirm this
      doc's own later 2026-07-28T01:1x SUPERSEDED banner (above): `cascade_dep_branch()` (`:362`) runs
      `git checkout -B "$branch_name" "origin/$branch_name"` at `:483` (the same unconditional-realign pattern recurs at
      `:1488`/`:1509` elsewhere in the script) — `checkout -B` REALIGNS the local branch to origin regardless of
      ahead-of-origin state, which is exactly the `branch: Reset to origin/live-defi-rollout` reflog signature every
      wave in this doc chased. This is NOT the `setup-tab-worktrees.sh`/ff-pull-cron/`reset --hard` candidates
      originally guessed below — those were exonerated by this doc's own later waves (slot-7's `408a92200` audit clears
      `slot-cron-ff-pull.sh` specifically). Already root-caused + partially fixed in
      `/plans/archive/2026_08/issues/utl_shared_clone_commits_repeatedly_reset_2026_07_22.md` (preserve-guard `06dc7632`;
      independent fetch-bug fix `8ca436599`) — that doc is the correct home for any remaining code-fix scope, not this
      one; do not re-implement here. **Original investigation prompt, preserved for context**: identify WHAT emits
      `branch: Reset to origin/live-defi-rollout` on a worktree that carries an unpushed local commit. Candidates: a
      slot-teardown/prune path, a `setup-tab-worktrees.sh` re-init, or an ff-pull cron that `reset --hard`s instead of
      `pull --ff-only` (which would only ever fast-forward, never drop ahead commits). Likely same disruption window as
      the related per-slot-cron-staleness issue (disk resize + 2 orchestrator restarts, same day). **Corroboration
      2026-07-28 (slot-12)**: this recurs beyond the 2026-07-27T16:55Z reap window — hit it on `deployment-service` mid-
      `cve_affected_pinned_deps_remediation_2026_06_18.md` todo 1 work, my session having died and been respawned
      partway through (per the resumed-session boot message). Reflog showed
      `HEAD@{1}: branch: Reset to origin/live-defi-rollout` sitting directly on top of my own unpushed
      `chore(deps): lift fastapi/starlette caps...` commit, which vanished from `HEAD` (still recoverable via reflog at
      the time, not checked how long it survives). Lower stakes than the prior cases — a 2-line dependency-bump commit,
      redone in under a minute rather than needing a reflog cherry-pick — but it strengthens the "any slot respawn finds
      an ahead-of-origin worktree" framing, which the `cascade_dep_branch()` finding above now explains mechanically (a
      respawn's quickmerge dependency-cascade re-checkout, not something tied uniquely to the 2026-07-27 disk-resize
      disruption).

### Related symptom — corrupted `/done` evidence SHA in the recovery race window (review, 2026-07-27T17:21Z)

A downstream effect of this bug also corrupts evidence-backed completion: task
`sports_consolidated_native_ao_extract-002` (slot-14) posted `/done` citing sha `017f33c73` as its evidence, but that
sha is slot-11's UNRELATED commit — the commit that actually carries this task's work (Track C K1/K2 re-verify) is
`ae03d60ab` (main's recovered cherry-pick of the orphaned `0aa00b715`). The revived-post-kill worker found its work
already landed by the recovery and echoed whatever `HEAD` happened to be at that moment (which by then included
slot-11's just-landed commit) rather than its own SHA. Net outcome is correct (checkbox genuinely flipped, content on
origin), but the self-reported evidence SHA is WRONG — a worker capturing `HEAD` in the post-recovery race window
instead of the SHA it authored. This is a second reason to fix the reset (it doesn't just orphan commits — it also
pollutes the audit trail QG relies on for evidence-backed completion). Fold into the root-cause fix: a worker's `/done`
evidence must cite the SHA it authored, verified against the task's touched files, not a bare `HEAD` snapshot.

## Why this matters

`pull --ff-only` can never drop an ahead commit; only a `reset`/`branch -f` to origin can. Any fleet automation that
resets worker branches to origin is a silent data-loss surface — the worker reports DONE, the session dies, and the
commit evaporates with no error. Belongs under `/codex/05-infrastructure/per-tab-worktrees.md` invariants (HEAD is
ancestor-or-equal of origin — the fix is to PUSH-then-reconcile, never reset-over-unpushed).

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid **but flagged as this run's top finding** — the doc's own
  `⚠️ DISPATCH GAP` banner escalates routing to the operator as a three-way choice ((a) migrate into a dispatched plan,
  (b) route a worker explicitly, (c) authorize main to run the recovery), which is exactly the authority call this audit
  must not make unilaterally. Execution also needs cross-slot worktree access to `.tabs/{9,12,13}/**` on
  `ip-172-31-5-118`, which the multi-agent safety HARD RULE bars. The P1 data-loss exposure is real and ageing — see
  `/plans/archive/issues/orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md`, filed by this run.
