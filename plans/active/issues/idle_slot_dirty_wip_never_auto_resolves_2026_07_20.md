---
doc_type: issue
title: Idle-slot dirty WIP never auto-resolves — FM8 orphan-inherit only fires on spawn
summary:
  Slot 14 paged `agent-orchestrator-alerts` "STILL RED" for 40+ hours (dirty uv.lock) with NO live tmux session at all —
  nothing was ever going to trigger the existing FM8 orphan-WIP inherit mechanism, because that mechanism only runs at
  pre-spawn, and nothing was trying to spawn into slot 14.
status: open
nature: process
asset_group: [cross-cutting]
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
source: ao_fleet_infra_hardening_2026_07_20.md todo-6 alert follow-up (2026-07-20)
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-25
locked_by:
locked_since:
---

# Idle-slot dirty WIP never auto-resolves

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

- [ ] [BACKEND] P2. **Add a periodic dirty-resolution sweep that does not depend on a spawn attempt.** Reuse the
      existing `resolve_dirty_state` / `commit_and_push_dirty_repos` plus the FM8 liveness discriminator (dead or
      expired `.agent-claim` → inherit + commit; live claim or mtime <120s → PROTECT), driven from a periodic tick
      against slots that are dirty AND provably dead (no live tmux session). **Gate**: a deliberately-idle dirty slot
      with no tmux and an expired claim is inherited within one sweep interval, evidenced by a
      `slot_dirty_state_resolved`-class activity row with **no adjacent spawn/autospawn event**.
- [x] [OPERATOR] P3. **Spot-check the live fleet for a current instance before prioritising the above** — query
      `/api/fleet/git-health` for any slot dirty >24h with no live session. If none exists, this is a structural gap
      without an active incident (fine to sequence behind P1 work) — which is a reason to rank it, **not** a reason to
      close it. **Gate**: the one-line finding recorded in this doc. → **FINDING (2026-07-25, main agt-52bb99, raised by
      review slot-1 msg 1991)**: a live instance EXISTS — host `ip-172-31-0-185` slot 0 (reporter stale since 03:32Z,
      `ff_cron_stale`, `ff_pull_last=skip:dirty`). See recurrence note below. This ranks the P2 sweep above (active
      incident with a real blast radius), it does not close the structural gap.

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

- [ ] [OPERATOR] P2. **Preserve the 31 uncommitted `unified-trading-pm` plan docs (+ the 4 other repos' dirty files) on
      `ip-172-31-0-185` slot 0 BEFORE any decommission/reset.** Either bring the host runtime up enough for AutoSpawn to
      place a worker into slot 0 (the pre-spawn dirty gate then inherits the WIP to a `wip-preserve/` ref
      automatically), or manually commit+push the plans from that host. **DO NOT `git reset`/decommission the host until
      this lands** — the content is not on origin and not reproducible. **Done when**: the 31 plans exist on
      `origin/live-defi-rollout` (or a `wip-preserve/` ref) and `/api/fleet/git-health` shows slot 0 clean.

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

- [ ] [OPERATOR/BACKEND] P3. **Decide + (if worth it) recover slot 6's 2 orphaned GMX-cleanup commits before GC.**
      Recovery recipe: from `.tabs/6/unified-api-contracts`, `git branch preserve-gmx-cleanup 11ed7f09` (un-orphans both
      — `44de0cf0` is its parent), then a worker cherry-picks onto `live-defi-rollout` + `quickmerge`s, or an
      FS-holder/operator does the same. Low value (dead-fixture cleanup) so a legitimate NO-recover is fine — but record
      the choice. **Done when**: either the commits are on `origin/live-defi-rollout`, or a note here states they were
      deliberately let go.
- [ ] [BACKEND] P2. **Extend the dirty-resolution sweep (P2 above) to also catch committed-but-unpushed commits orphaned
      by realignment**, not just dirty-tree WIP — before realigning a dead slot's worktree to origin, detect local
      commits not on origin and preserve them to a `wip-preserve/` ref. **Gate**: a dead slot with a local commit ahead
      of origin gets that commit preserved to a ref (not orphaned) when its worktree is realigned.

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

- [ ] [BACKEND/OPERATOR] P3. **Recover slot 10 `4d235caf` selectively**: inherit `.tabs/10/market-tick-data-service`,
      rebase (it's 1-behind), DROP the shard-count hunk if redundant vs `0ce00dbe`, KEEP the 3 dead-script deletions,
      quickmerge. **Done when**: the 3 scripts are deleted on `origin/live-defi-rollout` (or a note states they were let
      go) and no duplicate shard-count re-pin was pushed.
- [ ] [BACKEND/OPERATOR] P3. **Recover slot 11 `unified-trading-pm` 8-ahead** (top `c6610a36c`): inherit worktree,
      `git fetch` + rebase, push the unpushed doc commits (dedup any already on origin via content). **Done when**: slot
      11's unique PM doc work is on origin or recorded as superseded.
- [ ] [OPERATOR] P2. **Eyeball slot 0's dead host (ip-172-31-0-185) git status directly + recover the 5 dirty repos'
      WIP** before any decommission/reset (cross-ref the standing preserve-do-not-reset watch). **Done when**: the 5
      repos' dirty WIP is committed/pushed or explicitly discarded with a recorded decision.
