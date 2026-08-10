---
doc_type: issue
title:
  protected_live_peer dirty-state liveness check classified a confirmed-dead slot-12 session as liveness:live TWICE
  after resume was exhausted, stranding 2 real commits + uncommitted diffs in market-tick-data-service
summary: >-
  slot 12 (market-tick-data-service) went dirty at 2026-08-08T21:57:03Z with 2 unpushed commits (taxonomy/stalled-head
  detection work) + 4 modified-uncommitted files. Its tmux session was CONFIRMED dead (`tmux_session_lost@23:01:11Z` ->
  `slot_resume_respawned@23:02:37Z` -> died again `@23:04:26Z` with `released_task` set + `slot_resume_exhausted` 2/2 ->
  AutoSpawn then failed TWICE more, `spawn_retry_cap_reached@23:04:47Z` and `@23:15:39Z`, both
  `session_alive:false`/`pane_state:no_session`). Despite that terminal-dead evidence, the watchdog's
  `slot_dirty_state_resolved` event fired at `23:01:19Z` AND AGAIN at `23:15:44Z` (i.e. AFTER resume exhaustion),
  classifying the mtds worktree as `action:protected_live_peer`, `liveness:live`, and left it untouched both times —
  meaning the protection logic did not incorporate the session's own liveness signals it presumably has access to. A
  fresh session is now correctly idle on slot 12 (283 backlog tasks blocked on sports_taxonomy prereqs) but never
  inherited the orphaned mtds WIP (fresh-pull skip-if-dirty; nothing in the idle path reconciles pre-existing dirty
  state in an unrelated repo). Main independently verified the dirty state directly in the slot-12 worktree (git
  status/log matched review's report exactly: HEAD=89f525f7, origin=903505ca, 4 modified files) and mitigated the
  immediate work-loss risk by pushing 2 new backup refs to origin (`wip-preserve/orchestrator-slot-12-89f525f7` for the
  2 commits, `wip-preserve/orchestrator-slot-12-89f525f7-uncommitted` via `git stash create` — zero working-tree/index
  mutation, confirmed via a post-push `git status --short` showing the same 4 modified files unchanged). Reported by
  review (agt-e817dd, msg 4357, 2026-08-08T23:24:25Z), read-only investigation (git status/log only, no writes to slot
  12).
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, market-tick-data-service]
scope: [engineer, admin]
tags: [agent-orchestrator, liveness, dirty-state, work-loss-risk, live-incident, wip-preserve]
related:
  - /plans/archive/2026_08/issues/review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md
  - /plans/archive/2026_08/issues/defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md
created: 2026-08-08
author: agt-22de53 (main)
parent_epic: infrastructure_master
priority: P1
source: >-
  Review finding (agt-e817dd, msg 4357, 2026-08-08T23:24:25Z), verified live by main against the slot-12
  market-tick-data-service worktree directly.
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
  "fix agent-orchestrator@07894aa (_default_worker_alive death-signal cross-check) + reconciliation
  agent-orchestrator@9a5506f (orphaned-sibling-dirty-repo flag) + backup-branch superseded-verification (slot 5) +
  post-fix fleet-wide verification (slot 17, 2026-08-09) confirming no recurrence"
last_updated: 2026-08-09
locked_since:
context_scope: [agent-orchestrator/server/dirty_state.py, agent-orchestrator/server/watchdog.py]
---

> **ARCHIVED 2026-08-09** — all 4 todos resolved: fixed `_default_worker_alive` to cross-check
> `tmux_session_lost`/`slot_resume_exhausted`/`spawn_retry_cap_reached` activity events against `last_ping`
> (`agent-orchestrator@07894aa`), added orphaned-sibling-dirty-repo detection (`agent-orchestrator@9a5506f`), verified
> the mtds backup branches were superseded by independently re-landed work (no cherry-pick needed), and confirmed
> post-fix via `/api/activity` that no dead session has since been misclassified `liveness:live`. Original path:
> `plans/active/issues/protected_live_peer_liveness_misclassifies_dead_session_stranded_wip_2026_08_08.md`.

# `protected_live_peer` liveness check misclassified a confirmed-dead slot-12 session as live, stranding real WIP

## What was found

- mtds (slot 12) dirty since `2026-08-08T21:57:03Z`: 2 unpushed commits (`1c868524` taxonomy/stalled-head-detection
  feature, `89f525f7` re-export fix) + 4 modified-uncommitted files (`QUALITY_GATE_BYPASS_AUDIT.md`,
  `_dex_swaps_stalled_head.py`, `dex_swaps_handler.py`, `scripts/quality-gates.sh`). 6 commits behind
  `origin/live-defi-rollout` the whole time (FF-pull skip:dirty).
- Session death sequence is unambiguous: `tmux_session_lost@23:01:11Z` -> 1 resume attempt
  (`slot_resume_respawned@23:02:37Z`) -> died again `@23:04:26Z` with `released_task` set + `slot_resume_exhausted`
  (2/2) -> AutoSpawn failed twice more (`spawn_retry_cap_reached@23:04:47Z` and `@23:15:39Z`, both
  `session_alive:false`, `pane_state:no_session`).
- Despite that, `slot_dirty_state_resolved` fired at `23:01:19Z` AND `23:15:44Z` (the second firing is AFTER resume
  exhaustion + 2 failed respawns were already logged) classifying the state as `action:protected_live_peer`,
  `liveness:live` — and left the dirty worktree untouched both times.
- A fresh session is now live+idle on slot 12 (correct — 283 backlog tasks genuinely blocked on sports_taxonomy prereqs)
  but has no path to inherit/reconcile the orphaned mtds dirty state in a DIFFERENT repo than whatever it's currently
  idling in.
- Main independently verified (direct `git status`/`git log` in the slot-12 mtds worktree) — matched review's report
  exactly. Mitigated via 2 new backup branches pushed to origin (commits + a `git stash create` snapshot of the
  uncommitted diffs) — zero mutation of the actual worktree, verified via a post-push `git status --short` diff.

## Why it matters

- Real, direct work-loss risk: 2 genuine feature/fix commits (subgraph-stalled-head taxonomy + detection) plus related
  uncommitted changes were one `git reset`/slot-recycle away from being silently discarded — the protection meant to
  prevent exactly this (`protected_live_peer`) had already stopped being true by the time it fired the second time.
- The bug is specifically that the liveness classification for `protected_live_peer` does not appear to check the SAME
  slot's own recently-logged liveness signals (`tmux_session_lost`, `released_task`, `slot_resume_exhausted`,
  `spawn_retry_cap_reached`) before deciding `liveness:live` — a stale-default or fail-open path is the likely root
  cause (review's own hypothesis, unconfirmed pending a code read).
- Distinct from `review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md` — that doc tracks WHY slots keep dying
  (silent-no-compact wedge pattern); this doc tracks a SEPARATE bug in how the dirty-state watchdog decides whether a
  dead slot's WIP is safe to leave alone vs. needs reconciliation.

## Todos

- [x] ✅ [BACKEND] P1. Read `agent-orchestrator/server/dirty_state.py` (or wherever `slot_dirty_state_resolved` /
      `protected_live_peer` classification lives) and confirm whether the liveness check incorporates the slot's own
      `tmux_session_lost`/`slot_resume_exhausted`/`spawn_retry_cap_reached` activity events, or reads a separate/stale
      liveness signal. Fix so a slot with `slot_resume_exhausted` logged AFTER the dirty-state check's reference
      timestamp is never classified `liveness:live`. — agent-orchestrator@07894aa. Confirmed: `classify_maker_liveness`
      (`server/worktree_clean_check/_liveness.py`) never read those activity events — its `_triangulate` step only
      cross-checked `SlotRow.last_ping` recency (`_default_worker_alive`, 180s window) and a live `/proc/<pid>/cwd`
      match (`_default_proc_cwd_live`), a genuinely stale/separate signal set. Root cause: a doomed `--resume` attempt
      can send exactly one `/heartbeat` (refreshing `last_ping`) moments before dying again, so a claim-based
      dead/absent verdict got overridden to `live` by a ping that was already stale by the time the next sweep tick read
      it. Fix: `_default_worker_alive` now also queries `activity_log` for
      `tmux_session_lost`/`slot_resume_exhausted`/`spawn_retry_cap_reached` rows for the SAME slot with `ts > last_ping`
      — if one exists, the ping is proven stale and the function returns `False` regardless of the raw window check.
      Added 4 regression tests (one per death-event type + one predates-ping negative case) to
      `tests/test_dirty_state_resolution.py`. Full `quality-gates.sh` green (2827 passed).
- [x] ✅ [BACKEND] P2. Add a reconciliation path for orphaned dirty state in a repo the CURRENT fresh session on that
      slot isn't using — either surface it in the blocked/review queue for a worker to explicitly inherit, or extend the
      idle path to detect+flag (not silently ignore) pre-existing dirty state in sibling repos on the same slot. —
      agent-orchestrator@9a5506f. Added `WorkerLivenessWatchdog._flag_orphaned_sibling_dirty_repos` (runs every tick
      alongside `_sweep_dirty_slots`): scoped to slots WITH a live tmux session (exactly the slots `_sweep_dirty_slots`
      skips outright), it walks `check_slot_clean` and flags a dirty repo as orphaned iff none of its dirty files were
      touched within `RECENT_DIRTY_MTIME_SECONDS` (the same mtime-recency signal `_liveness.py` already trusts to mean
      "actively being edited right now"). Strictly read-only — logs `orphaned_sibling_dirty_repo_detected` /
      `orphaned_sibling_dirty_repo_resolved` (state-transition dedup via a new `_orphaned_sibling_dirty_flagged`
      tracker, mirroring the existing `_burn_flagged` pattern — fires once per episode, not once per tick) so a
      human/review worker can explicitly triage + inherit it, matching the todo's "detect+flag, not silently ignore"
      option. 4 new tests in `tests/test_watchdog_dirty_sweep.py` (flags a stale sibling-dirty repo under a live
      session, resolves once cleaned, skips a recently-edited repo, no-ops when no live session owns the slot). Full
      `quality-gates.sh` green (2827 backend + 262 dashboard tests).
- [x] ✅ [REVIEW] P2. Verify the 2 backup branches (`wip-preserve/orchestrator-slot-12-89f525f7`,
      `wip-preserve/orchestrator-slot-12-89f525f7-uncommitted`) contain the expected content, then route a worker to
      cherry-pick/rebase the taxonomy + stalled-head-detection work onto current `live-defi-rollout` (it is 6+ commits
      behind and drifting) — or explicitly determine it's superseded and safe to drop, citing the diff reviewed. —
      **Determined SUPERSEDED, safe to drop — no cherry-pick needed.** Both branches confirmed present in
      `market-tick-data-service` (`89f525f70f8379c0dd2adc39d98079218d1d2ab3` / commits ref,
      `a8d17559607327976bfb1dd7a766b248479426b6` / stash-create ref) and contain the expected content (2 commits
      `1c868524` taxonomy-detection feature + `89f525f7` re-export fix, plus the 4-file uncommitted diff
      `QUALITY_GATE_BYPASS_AUDIT.md` / `_dex_swaps_stalled_head.py` / `dex_swaps_handler.py` /
      `scripts/quality-gates.sh` exactly as the summary describes). Diff review against `origin/live-defi-rollout` (52
      commits ahead of the branches' merge-base): the taxonomy feature was independently cherry-picked/re-landed on LDR
      **at least 10 separate times** by other slots (`git log --all -S"EXPECTED_SUBGRAPH_STALLED_HEAD"` shows 531a07d8,
      8c5421ea, 3f11a8d6, fd9a1f37, 1c868524, 57c7faa0, 66a3791c, 0ce87ac5, 9a4403c8, 15ba9e3e, fdc86b13, 5bc795a5,
      c6edb663, 5d633923 — same commit message, repeated re-application) and the re-export fix likewise landed as
      `727184b7` ("index on live-defi-rollout: 89f525f7 …") — LDR's current `_dex_swaps_queries.py` already carries the
      re-export (`_SubgraphStalledHeadError`/`_is_subgraph_head_stale`/`probe_subgraph_head_and_raise_if_stale`/
      `record_stalled_head_empty` at lines 48-51/73-76) AND a further refinement not in the backup branch (a
      `record_indexer_empty()` consolidating helper). `tests/unit/test_dex_swaps_handler.py` is **byte-identical**
      between the backup branch and LDR (1415/1415 lines, zero diff) — direct proof of full content parity, not just
      message-text matching. For the uncommitted-stash branch's 4 files: `scripts/quality-gates.sh`'s `BE_EXCLUDE_GLOBS`
      already carries the `_dex_swaps_stalled_head.py` entry on LDR; `QUALITY_GATE_BYPASS_AUDIT.md` already carries an
      equivalent bypass-justification row for the same function (worded differently, same substance);
      `dex_swaps_handler.py`'s exception-handling consolidation is present on LDR via the differently-named
      `record_indexer_empty()` helper (functionally equivalent to the stash's `_record_deindexed_or_stalled_empty()`);
      the one textual difference — `probe_subgraph_head_and_raise_if_stale` checking `isinstance(data, dict)` (stash) vs
      `data is None` (LDR) — is not a real gap: `_execute_subgraph_query`'s own type signature is
      `tuple[dict[...] | None, int]`, so `data` can never be a non-dict, non-None value; the extra isinstance check is
      redundant given the existing type contract, not a bugfix. **Conclusion: zero unique work survives in either backup
      branch — everything is already on `live-defi-rollout`, in equal-or-better form.** No cherry-pick routed; no worker
      dispatch needed. Branches left in place (harmless, non-destructive) — verifying slot 5, 2026-08-09.
- [x] ✅ [REVIEW] P3. Once todo 1 lands, verify: re-check `/api/activity` for the next slot that hits
      `tmux_session_lost` -> `slot_resume_exhausted` while dirty, confirm `slot_dirty_state_resolved` no longer
      classifies it `liveness:live`. — **Confirmed fixed**, agent-orchestrator@07894aa (landed 2026-08-08 23:52:16Z).
      Cleanest post-fix case: slot 8, `market-tick-data-service` dirty (2 uncommitted-then-committed files pending),
      `tmux_session_lost` + `slot_resume_exhausted` (2/2) fired simultaneously at `2026-08-09T01:40:50Z` (task
      `defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02-001` released). The next two `slot_dirty_state_resolved`
      events for slot 8 — `01:46:49Z` (`action: quarantined`) and `01:46:54Z` (`action: inherited`, orphan commit
      `b21992e1` pushed) — both classified `liveness: dead`, with **no intervening `live` misfire** in the ~6-minute gap
      (contrast the original incident: `protected_live_peer`/`live` fired TWICE, including ~14 min after confirmed
      death). Cross-checked ~18 `slot_resume_exhausted` events fleet-wide since the fix landed (slots
      4/5/8/10/11/12/14): the large majority (11/18) go straight to a correct `dead`/`absent` classification with zero
      intervening `live` reads (e.g. slot 12: 4 separate exhaustion cycles between 09:15Z-12:02Z, every one resolved
      `dead`). A handful of `protected_live_peer`/`live` reads did occur within ~30-60s of an exhaustion event (slots
      4/5/12/14) — traced each to `classify_maker_liveness`'s separate, pre-triangulation `has_session(claim_session)`
      short-circuit (`server/worktree_clean_check/_liveness.py`): a `slot_resume_respawned`/`autospawn`/
      `kick_escalation` cycle had already put a NEW tmux session on the same `orch-slot-N` name by the time the check
      ran, so the claim's owning session genuinely still existed — a legitimately-live respawn, not the fixed
      last-ping-override bug (that path never calls `_default_worker_alive` at all). Consistent with that read: every
      one of those cases self-corrected to `dead`/`absent` within 1-3 min once the fresh attempt also failed (e.g. slot
      5: `live` at `10:27:54Z` -> `quarantined`/`absent` by `10:29:54Z`; slot 14: `live` at `13:55:10Z`/`13:55:46Z` ->
      `inherited`/`dead` by `13:58:14Z`) — no case left a confirmed-dead session stranded as `live` indefinitely, the
      specific work-loss failure mode this issue tracks. No code changes; verification-only.

## Progress log

- 2026-08-08 ~23:26Z (main agt-22de53): Filed after review msg 4357. Independently verified the dirty slot-12 mtds state
  directly (`git status`/`git log`, matched exactly) and mitigated the work-loss risk with 2 new backup refs pushed to
  origin: `wip-preserve/orchestrator-slot-12-89f525f7` (the 2 commits) and
  `wip-preserve/orchestrator-slot-12-89f525f7-uncommitted` (via `git stash create` — non-destructive, confirmed zero
  working-tree mutation via a post-push `git status --short`). Set `assigned_vm: planning` /
  `execution_scope: orchestrator-agent` directly (not `NA`) — the [BACKEND] todos are bounded/determinable (read a
  specific file, fix a specific classification gap), matching AO-eligibility criteria, and severity (active work-loss
  risk on a liveness-protection mechanism) justifies immediate dispatch over an ask-first NA default.
- 2026-08-09 (slot 19, backend_engineer): Landed todo 2 — agent-orchestrator@9a5506f. See the checkbox above for the
  full implementation summary.
- **context-scout 2026-08-09**: populated/refreshed context_scope (2 entries).
- 2026-08-09 (slot 5, review-craft worker): Landed todo 3 (verification only, no code shipped). Confirmed both backup
  branches exist with the expected content, then diffed each against `origin/live-defi-rollout`: the taxonomy commit's
  content is identical to work independently re-landed on LDR 10+ times by other slots, the re-export fix's content is
  on LDR via `727184b7`, and `tests/unit/test_dex_swaps_handler.py` is byte-identical between the backup branch and LDR
  (1415/1415 lines). The uncommitted-stash branch's 4-file diff is either already present on LDR (BE_EXCLUDE_GLOBS
  entry, audit-doc row, an equivalent exception-consolidation helper) or redundant given `_execute_subgraph_query`'s own
  `dict | None` return-type contract. Verdict: SUPERSEDED, safe to drop, no cherry-pick routed. See the checkbox above
  for full citation. `market-tick-data-service` unmodified (verification-only task).
- 2026-08-09 (slot 17, review-craft worker): Landed todo 4 — all todos now closed (verification only, no code shipped).
  Confirmed via `/api/activity` that `agent-orchestrator@07894aa` fixed the misclassification: the cleanest post-fix
  dead-session case (slot 8, `2026-08-09T01:40:50Z` exhaustion) resolved `dead` with zero intervening `live` misfires,
  and a fleet-wide sweep of ~18 post-fix exhaustion events found no case where a confirmed-dead session was left
  stranded as `live` (a few near-simultaneous `live` reads traced to the separate `has_session()` fresh-respawn
  short-circuit, not the fixed bug, and all self-corrected to `dead` within minutes). See the checkbox above for full
  citation.
