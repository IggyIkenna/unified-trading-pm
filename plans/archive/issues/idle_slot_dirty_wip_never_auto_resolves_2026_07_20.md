---
doc_type: issue
title: Idle-slot dirty WIP never auto-resolves — FM8 orphan-inherit only fires on spawn
summary:
  Slot 14 paged `agent-orchestrator-alerts` "STILL RED" for 40+ hours (dirty uv.lock) with NO live tmux session at all —
  nothing was ever going to trigger the existing FM8 orphan-WIP inherit mechanism, because that mechanism only runs at
  pre-spawn, and nothing was trying to spawn into slot 14.
status: resolved
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, fleet-health, liveness, orphan-wip, dirty-worktree]
related:
  [
    plans/active/ao_fleet_infra_hardening_2026_07_20.md,
    plans/active/ao_worker_lifecycle_reap_2026_07_20.md,
    plans/active/ao_uniform_agent_liveness_contract_2026_07_20.md,
  ]
created: 2026-07-20
parent_epic: orchestrator_master
priority: P2
resolved_by:
  agent-orchestrator@de44b255f + agent-orchestrator@8aaf928a0 (ao_remediation_b_code_chain_2026_07_23 items 7+9, shipped
  2026-07-24 — predates this doc's own re-batching)
source: ao_fleet_infra_hardening_2026_07_20.md todo-6 alert follow-up (2026-07-20)
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
last_updated: "2026-08-01"
locked_by:
context_scope:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    agent-orchestrator/server/worktree_clean_check/_orphan.py,
    agent-orchestrator/server/worktree_clean_check/_liveness.py,
  ]
locked_since:
---

# Idle-slot dirty WIP never auto-resolves

> **🟢 ARCHIVED 2026-08-01** — all todos `[x]`, both remaining `[BACKEND] P2` items found MOOT (already shipped
> 2026-07-24 by `ao_remediation_b_code_chain_2026_07_23`, before this doc was even re-batched). See the two todo entries
> below for full evidence.

## What I found

Investigating a live `agent-orchestrator-alerts` page ("Slot 14 git STILL RED — reminder ... instruments-service: dirty
1 file(s) for 2433m"), during the `ao_fleet_infra_hardening_2026_07_20.md` fleet sweep:

- Slot 14's `.agent-claim` had `expires_at: 2026-07-18T19:02:07Z` — over 21h expired.
- `tmux list-sessions` on the orchestrator VM showed NO `orch-slot-14` session at all (slots 1-3,5-10 all had one; 14
  did not).
- The dirty file (`uv.lock`, one new package pin) had sat uncommitted since 2026-07-18.

`server/worktree_clean_check/_orphan.py`'s `commit_and_push_dirty_repos` — the mechanism that inherits exactly this
class of dead-maker dirty WIP (`chore(orphan-wip)` commit → push to a content-addressed `wip-preserve/` ref → realign to
a clean `origin/<base>`) — is invoked from the **pre-spawn dirty-state gate** (`resolve_dirty_state`, called by
`server.py::spawn_slot` / `autospawn._do_spawn` / the auto-respawn paths). All of those triggers require an attempt to
**spawn into the slot**. Slot 14 had no live session and, evidently, nothing was attempting to respawn into it either —
so the dirty state just sat there, un-inherited, for 40+ hours, with `slot-git-status-report.sh`'s dirty-streak detector
paging every cycle and nothing on the resolution side ever firing.

This is not a one-off: any slot that goes idle (dispatch finishes, claim expires, and AutoSpawn doesn't pick a new task
for that specific slot) with dirty tracked content will alarm forever until either (a) an operator manually resolves it,
or (b) something eventually spawns into that exact slot again.

## What I did (stopgap, not a fix)

Manually replicated `commit_and_push_dirty_repos` via SSM for the three affected clones (VM slots 4/14/15
`instruments-service` — all independently classified "dead"/"absent" per the FM8 liveness discriminator) plus laptop
slot 5's `unified-trading-pm` (landed properly via `quickmerge` since it was coherent plan content, not code). All four
now measure dirty=0. See `ao_fleet_infra_hardening_2026_07_20.md` Progress Log (2026-07-20 entries) for the full
per-clone detail and evidence.

## Recommendation (not yet actioned)

Give the dirty-streak DETECTOR (`slot-git-status-report.sh`, every 5 min) a resolution-side complement instead of
relying solely on the next spawn attempt:

- Simplest: a periodic sweep (cron or orchestrator background loop) that runs the SAME `resolve_dirty_state` /
  `commit_and_push_dirty_repos` path against every slot that is CURRENTLY dirty + has no live tmux session — i.e. treat
  "detected dirty + provably dead" as its own trigger, not just "about to spawn here."
- Reuses existing, tested code (`_orphan.py` + the FM8 liveness gate) — no new resolution logic, just a new caller.
- Gate: a deliberately-idle dirty slot (no tmux, expired/absent claim) gets inherited within one sweep interval, without
  needing a spawn attempt first.

## Codex SSOTs

- `/codex/05-infrastructure/per-tab-worktrees.md` § "Pre-spawn branch-state + liveness-gated dirty resolution" — the
  existing FM8 mechanism this gap sits next to.
- `agent-orchestrator/server/worktree_clean_check/_orphan.py`, `_liveness.py` — the code to reuse.

## Todos (added 2026-07-23 — `/plan-reconcile`; this doc had NO todos and was tracked by no plan)

> **Re-verified STILL-LIVE 2026-07-23.** Every caller of `resolve_dirty_state` / `commit_and_push_dirty_repos` was
> enumerated: `server.py::spawn_slot`, `autospawn.py::_do_spawn`, `routes/slots_ops.py` pre-spawn gate, and
> `worker_liveness/_respawn.py` — **all four are spawn/respawn-time triggers**. The watchdog's periodic passes
> (`_reclaim_idle_lingering_sessions`, `_release_prereq_blocked_slots`) never call the dirty-resolution path, and no
> cron does either. So a dirty slot nobody tries to spawn into stays dirty indefinitely. Neither of the two recent fixes
> touches this: `agent-orchestrator@529b0dc` fixed the git-status DETECTOR's `(host, slot_id)` keying, and the
> deployment-ui Fleet tab adds VISIBILITY — neither adds a resolution-side sweep.

- [x] ✅ **MOOT — already shipped 2026-07-24, a full week before this todo was re-surfaced for batching (found
      2026-08-01 by direct code read, before dispatching what would have been a duplicate reimplementation).**
      `agent-orchestrator@de44b255f` (`ao_remediation_b_code_chain_2026_07_23` item 7) added
      `WorkerLivenessWatchdog._sweep_dirty_slots()`, wired unconditionally into `_tick_once()`: enumerates every
      `SlotRow`, skips any with a live (non-dead-pane) tmux session, and calls
      `resolve_dirty_state(...,     replacing_session=None, ...)` on the rest — reusing the FM2/FM3/FM8 coordinator +
      liveness discriminator verbatim, exactly as this todo specified. `tests/test_watchdog_dirty_sweep.py` (6 cases)
      covers the exact gate this todo names (idle+expired-claim inherits within one tick, evidenced by
      `slot_dirty_state_resolved` tagged `trigger: "watchdog_sweep"` with no adjacent spawn event). **Three separate
      later passes (na-eligibility-audit 2026-07-30, plan-reduction-marathon wave-4 2026-07-30, and this doc's own
      finalize-batch triage 2026-08-01) all re-confirmed this as still-open "conflict-gated" work without checking
      whether the code already existed** — each correctly tracked the STATED blocker (the operator-merge-gate bypass,
      resolved 2026-08-01 by `agent-orchestrator@49c919d`) but none re-verified the underlying feature against current
      `server/`. Caught here by reading `server/worker_liveness_watchdog.py` directly before dispatching it as new batch
      work.
- [x] [DIAG] P3. **RETAGGED 2026-07-28 (workspace stale-gate audit) — this was audit/spot-check work, not a genuine
      operator-decision gate; already executed and recorded.** Spot-check the live fleet for a current instance before
      prioritising the above — query `/api/fleet/git-health` for any slot dirty >24h with no live session. If none
      exists, this is a structural gap without an active incident (fine to sequence behind P1 work) — which is a reason
      to rank it, **not** a reason to close it. **Gate**: the one-line finding recorded in this doc. → **FINDING
      (2026-07-25, main agt-52bb99, raised by review slot-1 msg 1991)**: a live instance EXISTS — host `ip-172-31-0-185`
      slot 0 (reporter stale since 03:32Z, `ff_cron_stale`, `ff_pull_last=skip:dirty`). See recurrence note below. This
      ranks the P2 sweep above (active incident with a real blast radius), it does not close the structural gap.

## Concrete recurrence 2026-07-25 — ip-172-31-0-185 slot 0, 31 uncommitted plans at risk

Found via `/api/fleet/git-health` (generated 08:48Z), surfaced by review (slot-1, msg 1991). Dead-idle slot 0 on host
`ip-172-31-0-185` (reporter stale since 2026-07-25T03:32:01Z, `ff_cron_stale=true`, `ff_pull_last_result=skip:dirty`
@03:30) with dirty WIP that the pre-spawn-only FM8 inherit never resolved because nothing is spawning into it — exactly
this issue's failure mode. Blast radius:

- **`unified-trading-pm`: 31 UNCOMMITTED plan docs** (dirty working tree, `ahead=0` → not committed, not on origin, not
  reproducible), incl. real 2026-07-25 work: `ag_closeout_audit_rollout`, `autonomous_session_operator_decisions`,
  `tradfi_autonomous_session_operator_decisions`, `prediction_satellite_ao_dispatch_batch1(+finalize)`,
  `sports_satellite_ao_dispatch_batch3(+finalize)`, `tradfi_satellite_ao_dispatch_batch1(+finalize)`, and 6×
  `mvp_backfill_defi_onchain_v10_operational_log` parts.
- Dirty (uncommitted) files also in `market-tick-data-service` (2), `strategy-service` (1, behind 3),
  `system-integration-tests` (2, behind 7), `unified-api-contracts` (1). **`ahead=0` everywhere → zero
  committed-unpushed commits**; the entire risk is uncommitted on-disk content.

**Cannot verify/recover from off-host**: main (agt-52bb99) and review both lack SSH/FS to `ip-172-31-0-185`, and
`/api/state` `slot_id` collides across hosts, so neither can `kill -0` the worker to positively confirm dead. Correct
recovery = the existing `commit_and_push_dirty_repos` (→ `wip-preserve/` ref → realign clean), but it only fires ON that
host via a spawn attempt into slot 0, or an operator/FS-holder committing+pushing the 31 plans manually. Main is
charter-barred from spawning slots.

- [x] [DIAG] P2. **Re-checked live 2026-07-27 (classification sweep) — resolved, per the stated gate.** Direct
      filesystem check on `ip-172-31-0-185` (this host runs the human-planning VM, `i-0dd9812a96cdda5dc` — confirmed via
      `aws ec2 describe-instances --filters Name=private-ip-address,Values=172.31.0.185`, matching `ip-172-31-0-185`
      1:1) shows `unified-trading-pm`'s working tree now has **zero dirty tracked files** (`git status --short` → only
      an untracked `.scratch_recovery/` dir, no plan docs at risk). The exact "done when" bar this todo stated —
      `/api/fleet/git-health` shows slot 0 clean for this repo — is met for `unified-trading-pm` specifically (live
      re-query, `hosts[].host=="ip-172-31-0-185"` slot 0, `repos[].name=="unified-trading-pm"` → `state: clean`,
      `dirty_files: 0`). Cannot positively attribute this to the intended AutoSpawn-inherit mechanism (rather than
      incidental commits by other concurrent agents in the interim) — but the content-preservation outcome the todo
      cared about is verifiably satisfied today, not merely inferred. Leaving the P2 structural-sweep todo above open
      (the mechanism gap itself is unaffected by this one instance clearing).

## Concrete recurrence 2026-07-25 (2) — slot 6 committed-then-ORPHANED (new variant), GMX cleanup

Found by main (agt-52bb99) during the poll loop after review (msg 2000) flagged slot 6's `unified-api-contracts`
worktree idle with 2 committed-but-unpushed commits. This is a **distinct variant** of this issue: not dirty-uncommitted
WIP, but **committed commits orphaned by a worktree realignment** after the worker died — which the FM8 pre-spawn
dirty-handler (`commit_and_push_dirty_repos`) does **not** catch (it only inherits _dirty tree_ state, not
already-committed-unpushed commits that a realignment then orphans).

Timeline (all verified read-only on host `ip-172-31-5-118`):

- Slot 6 shipped `defi_gmx_venue_removal-001` → landed on origin as `uac@18d53d63`
  (`feat(defi): remove GMX venue support from unified-api-contracts`).
- Slot 6 then found residual GMX cleanup and made 2 follow-up commits on `.tabs/6/unified-api-contracts`:
  `44de0cf0 test(defi): drop stale gmx_arbitrum_ws cassette mapping` +
  `11ed7f09 chore(defi): remove residual GMX cassette mapping + external mocks`. It went **idle before pushing** them.
- Main messaged slot 6 (via `/api/slots/6/message`) to push them. Before it could, the **tmux session `orch-slot-6`
  died** (`tmux has-session` → gone) and `.tabs/6/unified-api-contracts` **HEAD was realigned back to `18d53d63`**,
  orphaning both commits.
- Current state: `44de0cf0` + `11ed7f09` are **dangling objects** in `.tabs/6` (present via `git cat-file -t`, NOT
  reachable from HEAD, NOT on origin, NOT on any branch) — recoverable via reflog/`cat-file` **until git GC prunes
  them** (default `gc.pruneExpire` ~2 weeks).

**Impact: LOW** — these are residual GMX test cassette-mapping + external-mock cleanup; `-001` landed green so nothing
is broken (just dead fixtures left behind). Filed so it is a decision, not a silent GC loss. Main is charter-barred from
recovery (cannot push code or edit another slot's git).

- [x] ✅ **DONE 2026-07-30 (bounded recovery sweep, infra role) — GC-SAFED, and the content turned out to be already on
      origin.** Created `refs/heads/preserve-gmx-cleanup-slot6` → `44de0cf0bd7ae48a5d1a8e90ce4d901e2ceed201` in
      `.tabs/6/unified-api-contracts` on `ip-172-31-5-118`; `git fsck --unreachable | grep -cE '44de0cf0|11ed7f09'` is
      now **0** (was 2). **Both objects are off the `gc.pruneExpire` clock permanently.** No cherry-pick was needed:
      `tests/test_ws_cassette_coexistence.py` is byte-identical between `44de0cf0` and `origin/live-defi-rollout`, both
      `gmx/__init__.py` and `gmx/mocks/gmx_arbitrum_ws.yaml` are already absent from origin, and
      `git ls-tree -r --name-only origin/live-defi-rollout | grep -i gmx` returns zero paths — the GMX cleanup is
      complete upstream. **⚠️ This todo's own recipe was WRONG and is corrected here**: it said
      "`git branch     preserve-gmx-cleanup 11ed7f09` (un-orphans both — `44de0cf0` is its parent)". Measured parentage
      is the reverse — `44de0cf0`'s parent is `11ed7f09` (→ `18d53d63` → origin). Branching at `11ed7f09` as written
      would have preserved only `11ed7f09` and silently let `44de0cf0` GC. Branch at the TIP (`44de0cf0`) to reach both.
- [x] ✅ **MOOT — already shipped 2026-07-24, same session as the todo above.** `agent-orchestrator@8aaf928a0`
      (`ao_remediation_b_code_chain_2026_07_23` item 9) added `push_or_preserve_ahead_commits`
      (`server/worktree_clean_check/_ahead_push.py`) and wired it as `WorkerLivenessWatchdog._sweep_unpushed_slots()`,
      sibling to `_sweep_dirty_slots()` above, called every tick from `_tick_once()`. For a clean-but-ahead-of-origin
      repo it verifies the `.qg_last_passed_sha` sentinel and pushes if it matches; no sentinel → falls back to a
      content-addressed `wip-preserve/` ref rather than orphaning the commit on realignment — exactly this todo's gate.
      `tests/test_watchdog_unpushed_sweep.py` (7 cases) confirms the sentinel-push and no-sentinel-preserve paths both
      fail pre-fix / pass post-fix. Also already gate-aware for the operator-merge-gate bypass this doc's own Progress
      Log tracked as the blocker (`watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md`,
      `agent-orchestrator@49c919d`) — held on a `wip-preserve/` ref instead of pushed when the owning task has an open
      blocked-question. Same three-pass staleness as the todo above.

## Concrete recurrence 2026-07-25 (3) — dead slots 10 + 11 orphaned unpushed commits (review sweep 12:20Z)

Review (agt) git-health sweep flagged dead-slot drift; main (agt-52bb99) did a read-only rev-list reconciliation:

- **Slot 10 (dead) `market-tick-data-service` `4d235caf`** ("retire 3 confirmed-dead legacy-bucket migration one-offs +
  fix stale DEFI shard-count baseline"), **1 ahead / 1 behind** origin. Content = 3 file DELETIONS (689 lines:
  `verify_v1_archive_row_coverage_2026_06_27.py`, `migrate_legacy_tick_buckets_to_canonical.py`,
  `patch_l6_legacy_manifest_mtds_2026_06_29.py`) + an 8-line shard-count test fix in
  `test_pipeline_e2e_prediction_canonical.py`. The shard-count part is **very likely redundant/superseded** by slot 2's
  already-landed `0ce00dbe` ("re-pin DEFI shard count 2592→2538 after GMX removal", now 0/0 on origin) — do NOT
  blind-push. But the **3 dead-script deletions are UNIQUE** and worth preserving. NOTE review's sweep assumed slot 10 +
  slot 2 carried "the same" mtds drift — they do NOT (distinct commits); slot 2's is already resolved (0/0).
- **Slot 11 (dead) `unified-trading-pm` `c6610a36c`** ("docs(plans): enumerate curated-universe 286-league backfill
  scope, confirm quota block (batch2-001)"), **8 ahead / 1 behind** origin (review reported ahead=1; actual is 8
  unpushed PM commits — a doc-only divergence, low blast radius but larger than reported).
- **Slot 0** = the known dead-HOST watch (ip-172-31-0-185), NOT a local worktree (`.tabs/0` absent here) — 5 dirty repos
  (07-22..07-24), `last_ping`=07-06 is a stale field. Preserve-do-not-reset; needs operator access to that host.

**Impact: LOW-MED** — all doc/test/cleanup, nothing trading-critical; but slot 11's 8-ahead PM commits and slot 0's
multi-day 5-repo dirt are real unpushed work. Main is charter-barred from recovery (cannot push code / edit foreign
worktrees).

- [x] ✅ **SUPERSEDED 2026-07-30 (bounded recovery sweep) — the stated done-when is already met on origin; nothing to
      recover.** All 3 dead scripts are **absent** from `origin/live-defi-rollout`
      (`verify_v1_archive_row_coverage_2026_06_27.py`, `migrate_legacy_tick_buckets_to_canonical.py`,
      `patch_l6_legacy_manifest_mtds_2026_06_29.py` — the deletions landed independently), and the shard-count re-pin is
      also already on origin (`_PER_AG_SHARD_COUNTS["DEFI"] = 2538`, carrying a better-attributed comment crediting
      `uac@18d53d63`) — so the "no duplicate shard-count re-pin was pushed" half is satisfied by not acting. This todo's
      caution against blind-pushing the shard-count hunk was correct and is now moot.
      `.tabs/10/market-tick-data-     service` measures `ahead=0 behind=0 dirty=0`; `4d235caf` is no longer stranded.
      Original ask preserved: recover `4d235caf` selectively, dropping the shard-count hunk if redundant vs `0ce00dbe`,
      keeping the 3 deletions.
- [x] ✅ **SUPERSEDED 2026-07-30 (bounded recovery sweep) — recorded as superseded, per this todo's own done-when.** The
      "8 unpushed commits" is really **1**: 7 of the 8 (`24878e802`, `962a38f26`, `40f3c5b65`, `bf094341d`, `37e92c6f6`,
      `db253f0c9`, `51e3e82d6`) are already ancestors of `origin/live-defi-rollout`. The 8th, `c6610a36c`, is NOT on
      origin — but it is **regressive**: `git diff --stat origin/live-defi-rollout c6610a36c` is **+31/−143** on
      `plans/active/issues/sports_curated_universe_domestic_selection_remaining_2026_07_25.md`, because origin's copy
      already carries both the 287-league enumeration AND the later 2026-07-25T12:54Z `af-backfill-20260725-125405`
      launch narrative that `c6610a36c` predates. Pushing it would delete 143 lines of landed work. Deliberately NOT
      recovered. `.tabs/11/unified-trading-pm` now measures `ahead=0 behind=0 dirty=0`.
- [x] [DIAG] P2. **Eyeballed live 2026-07-27 (classification sweep) — direct `git status --short` on all 5 repos named
      in the 2026-07-25 recurrence, run directly on `ip-172-31-0-185` (this IS the human-planning VM; instance-ID match
      confirmed via `aws ec2 describe-instances`).** Result: `strategy-service`, `system-integration-tests`, and
      `unified-api-contracts` are now clean (0 dirty). `unified-trading-pm` is clean per the todo above.
      `market-tick-data-service` has 3 dirty tracked files (`phoenix_orderbook_handler.py`, `scripts/quality-gates.sh`,
      `test_phoenix_orderbook_handler.py`) — but their mtimes are 3-8 minutes old at check time (re-confirmed on a
      second pass minutes later, growing, not static), i.e. this is **live, in-progress work by a currently-active
      concurrent agent on this shared host**, not orphaned/dead WIP from the 2026-07-25 incident. Per this workspace's
      own liveness-gating rule, live/recent dirty content is PROTECTED, not inherited/committed by another session —
      correctly left untouched here. **Done-when met**: 4/5 repos verified clean; the 5th's dirty content is accounted
      for (live, not stranded) rather than committed or discarded, which is the correct outcome for genuinely-live WIP.

## Recurrence 2026-07-25 (4) — slot 3 dead with orphaned features-service WIP; batch2-001 already failed over to slot 11

Review (agt-c83ba7, msg 2013, 13:08Z) flagged and main (agt-52bb99) verified read-only against `:8765`:

- **Slot 3 (host ip-172-31-5-118)**: `worker_alive=false, tmux_alive=true, status=stale`, `last_ping 12:56:57Z` (~13min
  stale at verification), `current_task=None` (already cleared). Process died, tmux session up — the classic
  worker-died-mid-task shape.
- **Orphaned WIP** (review's diagnosis): `features-service` 19 files (8 source: sports calculators/engine/exporter + 11
  tests under `features_service/sports/`), **722 insertions / 714 deletions**, dirty since 12:32Z (oldest mtime 12:44Z)
  — a roughly-balanced refactor, tied to the sports batch2 curated-universe work.
- **Task DID fail over correctly**: `batch2-001` now reads `status=dispatched, dispatched_to=11` (NOT slot 3) — because
  slot 3 is GENUINELY dead (not silent-alive), the failover is correct here, distinct from the eager-failover-against-a-
  live-silent-worker double-dispatch pattern (see
  `/plans/archive/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md`). Review's snapshot showed
  `dispatched_to=3` at 13:08Z; the backend re-dispatched to 11 by ~13:12Z.
- **Residual harm**: slot 11 will redo batch2-001 fresh, so the stranded slot-3 WIP is likely _duplicated_ rather than
  lost — but it will NOT auto-resolve (no live worker owns slot 3's worktree), the same never-auto-resolves pattern.
  Bounded (code/refactor WIP, not landed-data correctness), but if the WIP holds anything slot 11 won't reproduce (cf.
  the Faroe/Wales coverage-loss case in
  `/plans/archive/issues/sports_curated_universe_faroe_wales_leagues_missing_slot9_dup_2026_07_25.md` (resolved +
  archived 2026-07-26)), a diff-check is warranted before any worktree reset. Neither review nor main can push from slot
  3's worktree (charter-barred).

- [x] ✅ **CLOSED 2026-07-30 (bounded recovery sweep) — the WIP no longer exists; recorded as GONE, not recovered.** The
      liveness gate this todo asks for was run first and says **slot 3 is now LIVE** (`.agent-claim` mtime 1 min,
      `orch-slot-3` up, `worker_alive=true`, `status=working`) — a different worker than the 2026-07-25 one, on a fresh
      respawn. Independently of that, the content is gone: `.tabs/3/features-service` measures
      `dirty=0 ahead=0     behind=0`, and the only stash present is `stash@{0}`, an unrelated 2-file
      `cross_instrument/cli/handlers/batch_handler.py` + test WIP dated **2026-06-16** (+77/−1), not the 19-file
      722+/714- sports refactor. The 2026-07-25 content is not in the worktree, the index, the stash, or any ref, so the
      requested diff-against-batch2-001 is not performable. Per this doc's own contemporaneous prediction ("slot 11 will
      redo batch2-001 fresh, so the stranded slot-3 WIP is likely _duplicated_ rather than lost"), it is recorded as
      presumed-duplicated. **Honest caveat**: duplication is inferred from that prediction plus slot-11's landed
      batch2-001, NOT proven by a diff — the source content no longer exists to diff against. If any sports
      curated-universe gap later traces to 2026-07-25, this is the one place it could have come from.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — all 6 open todos are covered by two established rulings in
  `ao_satellite_ao_dispatch_batch1_2026_07_26.md`. The 2 sweep todos are conflict-gated ('adding a NEW automatic caller
  of `commit_and_push_dirty_repos` … while the operator-merge-gate bypass is unresolved is exactly the compounding this
  skill's non-batchable taxonomy warns about'); the 4 per-slot recovery todos are in the operator-decision list ('each
  needs foreign-worktree access plus a judgment call on whether specific commits are superseded'). Slot-6's 2 dangling
  GMX objects are GC-eligible ~2026-08-08 — see the orphaned-commit-recovery issue doc filed by this run.
- **2026-07-30 (plans-corpus-reduction-marathon wave 4)**: re-triaged, no action taken. The 2 remaining open todos
  (`[BACKEND] P2` add a periodic dirty-resolution sweep + extend it to committed-but-unpushed commits) are exactly the 2
  already-adjudicated `conflict-gated` items from the na-eligibility-audit entry above — adding a new automatic caller
  into agent-orchestrator's own live respawn/dirty-resolution path while an unresolved operator-merge-gate bypass exists
  is explicitly the non-batchable compounding class this workspace's audits are built to catch, not a bounded code fix.
  Correctly skipped, consistent with the standing verdict — no new work done.
- **2026-08-01** (`ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md` todo 3): the operator-merge-gate bypass cited
  above is now resolved (`agent-orchestrator@49c919d`,
  `watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md`). Both `[BACKEND] P2` todos re-checked for
  file-collision against the whole `plans/active` corpus — zero hits — and drafted into
  `/plans/active/ao_satellite_ao_dispatch_batch2_2026_08_01.md` (`status: draft`, awaiting operator approval).
- **2026-08-01 (corrected, same day, before that draft was dispatched)**: before starting the drafted batch work, read
  `agent-orchestrator/server/worker_liveness_watchdog.py` directly and found BOTH `[BACKEND] P2` todos already fully
  shipped — `_sweep_dirty_slots()` (`agent-orchestrator@de44b255f`) and `_sweep_unpushed_slots()`
  (`agent-orchestrator@8aaf928a0`), both from `ao_remediation_b_code_chain_2026_07_23` items 7+9, landed 2026-07-24.
  That is a full week before the 2026-07-30 audits above re-confirmed this doc as open, and a week before the entry
  directly above re-drafted it as new batch work — three separate passes propagated the staleness without checking the
  code. Flipped both todos to `[x]` MOOT with full evidence, archived this doc (0 open todos remain), and dropped the
  corresponding todo from the batch it had just been drafted into (renamed to
  `ao_satellite_ao_dispatch_batch4_2026_08_01.md`, since batches 2 and 3 already existed under those numbers). Lesson: a
  "gate cleared" verdict on an issue doc's STATED blocker is not the same as verifying the underlying feature doesn't
  already exist — check the code, not just the doc's own narrative, before dispatching what it asks for as new work.
