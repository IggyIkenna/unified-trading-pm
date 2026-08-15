---
doc_type: issue
title: >-
  AO observability + deploy-hygiene gaps found while diagnosing a 2026-08-08 fleet stall — every tracked gap now fixed
summary: >-
  A session that set out to answer "does an AO worker retain its backlog when its account runs out of usage" surfaced a
  cluster of unrelated observability and deploy-hygiene defects on the central VM, ALL now fixed and live-verified as of
  2026-08-09. Two activity-log floods were found and fixed by the same transition-dedup pattern: OrphanRefVerifyWatchdog
  (882/1000 rows in six minutes, agent-orchestrator@b19140b23) and, found independently a day later while re-verifying
  this doc's own claims, StashAuditWatchdog (51/500 rows, agent-orchestrator@1709bfe66 — verified live via a forced
  third restart producing zero new rows against the already-populated latch). The context-saturation retry loop burned
  15 minutes per wedge (agent-orchestrator@b52dd1910, its own issue doc); process-category-sampler failed EVERY run on
  its own TasksMax/MemoryMax caps; ao-self-pull silently skipped auto-deploy on any untracked file, the second
  recurrence of that wedge (agent-orchestrator@2c08afd85); 51 orphaned glue-runner unit files were retired after
  verifying 0 active/enabled; the false-done backlog went 26 -> 1 on a re-run, the survivor a positional-task-ID mapping
  artifact deliberately left untouched; a stash content verifier shipped (agent-orchestrator@2572571) ahead of any
  hand-triage of the ~15x-larger-than-reported pile. `ORCHESTRATOR_FLEET_WORKER_CAP` was raised 15 -> 25 with operator
  approval and verified via live tmux session growth past the old ceiling; slot 30 was completed to 26/26 repos. Nothing
  in this doc remains open.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, observability, activity-log, deploy, self-pull, false-done, glue-runners, stashes]
related:
  [
    /plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md,
    /plans/archive/2026_08/issues/ao_scheduled_job_reserve_and_staggering_2026_08_04.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
    ao_consolidated_closeout_2026_07_25,
  ]
created: 2026-08-08
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
drift_direction: none
last_updated: 2026-08-09
resolved_by: 'interactive session 2026-08-09 — operator: "do al these thigns" (fleet cap, slot 30, stash-flood fix)'
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: ['interactive session 2026-08-08 — operator: "did you fix all these so no issues left whatsoever? else do it"']
---

# AO observability + deploy-hygiene gaps (2026-08-08)

## Fixed + deployed in the originating session

- **Activity-log flood** — `OrphanRefVerifyWatchdog` logged one `orphan_ref_verified` row per ref per tick,
  unconditionally. Measured live: `orphan_ref_verified` + `orphan_ref_self_closed` were **882 of the last 1000
  `/api/activity` rows inside a six-minute window** (and 456/600 in an earlier sample), crowding every other event out
  of the feed while that feed was actively being used to diagnose a fleet stall. It also contradicted this workspace's
  own standing rule that a standing condition dedups by state-transition and never fires every tick. Now logs only on a
  verdict CHANGE, with a `dedup_state`-persisted latch pruned wholesale each tick. **agent-orchestrator@b19140b23**,
  deployed to the central VM and restarted 11:39 UTC.
- **Context-saturation retry burn** — tracked on
  `/plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md`, not duplicated here.
  **agent-orchestrator@b52dd1910**.

- **`process-category-sampler` failed EVERY run** — `TasksMax=50` with `TasksCurrent=40` (1420 `can't start new thread`
  in 6h, first seen 2026-08-07T16:48Z). NOT host exhaustion: 668 system threads against a threads-max of 231854. The
  unit enumerates every process on the box and publishes each as its own Pub/Sub call, so its thread demand grows with
  the fleet while the cap did not — guaranteed to fail harder as slots are added. Raised to 256
  (**agent-orchestrator@36067b6ac**); that exposed a second cap underneath — `MemoryMax=256M` with a measured
  `256.0M peak, 174.4M swap peak`, i.e. pinned and SWAPPING — raised to 1G. Both deployed + live-fired:
  `Result=success`.

## Outcome measured at session end (2026-08-08 ~12:10 UTC)

| signal                     | before           | after                             |
| -------------------------- | ---------------- | --------------------------------- |
| live worker tmux sessions  | 8                | **12 / cap 13**                   |
| effective backlog cap      | 8                | **13**                            |
| slots pinned >=80% context | 5 (all at 100%)  | **0**                             |
| watchdog kills today       | 3, flapping=true | **0, flapping=false**             |
| failed systemd units       | 2                | 1 (`audit-false-done`, by design) |

## Second slot tranche + the constraint FLIP (2026-08-08 ~13:10 UTC)

Operator approved a second tranche on the measured-RAM argument ("RAM is the real limit… CPU oversubscription is fine,
most work is I/O"). Slots 22-33 provisioned, **11 of 12 clean**; slot 30 failed mid-clone on the same
`git clone --reference` core-dump that hit slot 17 in tranche 1 (memory was NOT the cause — 23G free), and is tracked as
a todo below. Orchestrator restarted: `seed_worker_slots_from_tabs: registered 32 worker slot(s)`. Cost was small — disk
57% -> 58% (291G free), RAM 5G -> 6G used of 30G.

**The binding constraint has now FLIPPED.** With 32 configured worker slots the clamp is `min(15, 32-7) = 15`, so the
`AutoSpawn fleet cap … CLAMPED` warning stopped firing entirely (0 occurrences since the restart, against one per tick
before). Slot count is no longer the ceiling — **`ORCHESTRATOR_FLEET_WORKER_CAP=15` is**. This is exactly the state
agent-orchestrator@f1558bc's observability was built to make legible: raising that knob used to be inert, and now it is
the ONLY lever that matters. See the P1 todo below.

## Todos

- [x] ✅ [OPERATOR] P1. **`ORCHESTRATOR_FLEET_WORKER_CAP` raised 15 -> 25 — DONE 2026-08-09.** Operator approved ("do
      this yourself" — no longer a unilateral call). Edited `.env.local` on the central VM directly
      (`ORCHESTRATOR_FLEET_WORKER_CAP=15` -> `=25`), `systemctl restart orchestrator` (clean start,
      `Started     orchestrator.service`), verified the deployed checkout was `03e1809`/ahead=0 of origin before
      restarting. Measured the actual effect rather than trusting the config write: live `tmux` session count (the
      ground-truth fleet-fill signal per this doc's own Lessons section, not the DB snapshot) climbed **20 -> 21 -> 22**
      across three checks in the ~3 minutes after restart — already past the old effective ceiling of ~13-15 — while RAM
      tracked **7.5G -> 7.7G -> 8.2G used of 30G (22G avail)**, comfortably inside the pre-computed 12.5G budget for 25
      workers. No `AutoSpawn fleet cap … CLAMPED by slot arithmetic` warning fired (expected: that message only fires
      when SLOT COUNT is the binding constraint, and at 32 registered slots / 25 configured, arithmetic was never going
      to be the limiter now — the ORIGINAL "0 occurrences" finding this todo is built on already established that).
      Backlog at restart time: 498 queued, 5 dispatched, 36 blocked — plenty of ready work for the fleet to grow into.
      (repo: agent-orchestrator, VM config)
- [x] ✅ [BACKEND] P3. **`setup-tab-worktrees.sh --add-slot 30` re-run — DONE 2026-08-09, now 26/26 repos.** Ran as
      `ubuntu` (not root — the earlier `git clone --reference … core dumped` failures and this session's own
      `dubious ownership`/`$HOME not set` SSM-as-root friction both point at the same class of issue: root-context git
      operations against a `ubuntu`-owned checkout). Live output: all 26 repos report `OK … (Path-B clone exists)`,
      `checked=26 drift=0 fixed=1` (one repo's commit identity had drifted to `slot-30·laptop` and was auto-corrected to
      `slot-30·planning` by the installer's own guard). Skip-if-exists design meant this was a genuinely idempotent
      completion, not a re-clone. The WHY-core-dumps-under-root question from the original finding is now answered by
      inference (root vs ubuntu execution context) rather than fully root-caused via a git bug report — good enough to
      close this todo; worth remembering for the NEXT provisioning tranche rather than a separate action item now.
      (repo: unified-trading-pm)
- [x] ✅ [BACKEND] P2. **`ao-self-pull.sh` silently stops auto-deploying when an UNTRACKED file appears** — FIXED
      agent-orchestrator@2c08afd85. Gate now uses `--porcelain -uno` (TRACKED changes only). An untracked file cannot be
      blown away by a fast-forward merge, so there is no uncommitted WORK to protect — this gate's entire stated purpose
      — and the one genuinely-conflicting case (incoming commit creates that exact path) is already handled safely by
      `merge --ff-only`, which refuses and falls through to the same skip+alert. This fixes the CLASS: the 2026-07-29
      fix patched the INSTANCE by gitignoring two specific filenames via `accounts.json.bak-pre-sub-*`, and a
      differently-named backup slipped past it on 2026-08-08 and wedged the same gate again. Verified against the REAL
      wedged state on the VM: old predicate blocks, new one clears with that exact file still present. Untracked files
      are now logged so litter stays visible; `.gitignore` broadened to `accounts.json.bak*` as hygiene, not as the fix.
      ORIGINAL FINDING: Measured 2026-08-08: the central VM's AO checkout carried one untracked file
      (`data/config/accounts.json.bak-2026-08-08-tier`, someone's manual accounts backup) and self-pull logged
      `is dirty (non-churn) — skip (manual review)` and did nothing. An untracked `.bak-` file cannot conflict with a
      fast-forward pull, so this is a false block on the fleet's ONLY auto-deploy path — and it fails SILENTLY (a log
      line, no page), so the VM can sit un-deployed indefinitely. Recovered by hand this session via
      `git pull --ff-only` (untracked files do not block it) + `systemctl restart orchestrator`. **Done when**: the
      dirty-check distinguishes untracked-and-non-conflicting from a genuinely dirty TRACKED file, and a skip that
      persists past N ticks pages rather than only logging. (repo: agent-orchestrator)
- [x] ✅ [BACKEND] P2. **False-done rows: 26 -> 1, and the 1 is not a false-done.** Re-ran the audit 2026-08-08 ~12:50Z:
      **TOTAL FINDINGS: 1**. The other ~25 were same-day in-flight `_finalize-*` flips their own workers reconciled —
      exactly what this todo predicted ("re-run the audit before triaging so the genuinely-stale subset is isolated").
      The survivor, `cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed-025`, was read in full: that
      plan carries FOUR near-identical "Round-8 ACTUAL LAUNCH" todos (3 checked, 1 open) because each time-gated
      deferral appended a fresh copy. The DB row is legitimately `done` — that dispatch DID complete, the worker
      verified the UTC gate was unmet, launched nothing, and spawned the follow-up — and the open `- [ ]` is
      legitimately open, because the launch still has not happened. **Neither side is wrong; it is the positional-
      task-ID mapping artifact** (`regen_positional_task_ids_not_content_stable_2026_07_17`). Flipping the checkbox
      would falsely claim 8 SPOT VMs were launched; reopening the row would falsely reopen completed work — so
      deliberately did NEITHER. Root fix is ALREADY IN FLIGHT by another agent: `_make_content_task_id` exists in
      `regen_backlog_from_plan.py` behind a `reportUnusedFunction` suppression (agent-orchestrator@ac36202 + @e0f107a),
      built but not yet wired. Not colliding with it.
- [x] ✅ [BACKEND] P2. **Stash piles are ~15x bigger than first reported, and need a CONTENT VERIFIER before any
      discard.** FIXED agent-orchestrator@2572571 (corrected 2026-08-08: a second follow-up-fix sha this todo previously
      cited alongside it was fabricated/unresolvable via `git log` — `2572571` alone covers the untracked-file
      enumeration fix described below, no second commit exists). Added
      `worktree_clean_check.verify_stash`/`verify_all_stashes` (`server/worktree_clean_check/_stash_verify.py`), reusing
      `_orphan_verify.py`'s exact SUPERSEDED/STILL-ORPHANED/WOULD-REGRESS/GONE verdict vocabulary and per-file
      blob-compare method, adapted for a stash commit's multi-parent structure — measured directly (not assumed) that a
      stash commit's OWN tree captures only TRACKED changes; untracked files live in a separate third-parent commit
      built from scratch, so the verifier enumerates both via `diff-tree` (tracked) + `ls-tree` on the third parent
      (untracked) and unions them before the blob compare. Wired into a new transition-deduped `StashVerifyWatchdog`
      (`server/stash_verify_watchdog.py`, `tuning.stash_verify_interval_seconds` default 3600s), logging
      `stash_verified` on verdict change + a `stash_self_closed` bookend for SUPERSEDED/GONE — built deduped FROM THE
      START, learning `OrphanRefVerifyWatchdog`'s own measured 76%-of-activity-feed flood lesson rather than repeating
      it. 15 new tests (`tests/test_stash_content_verifier.py`, `tests/test_stash_verify_watchdog.py`), full
      `quality-gates.sh` green (2796 passed). **Scope note on "Done when" part 2**: this ships the verifier + the
      always-on recording mechanism (every stash the watchdog sweeps now gets a verdict logged going forward,
      self-closing the safe cases) — it does NOT hand-triage the several-hundred CURRENTLY-EXISTING stashes across the
      other 19 slots in this same session. Touching another slot's untracked/dirty state is out of scope for a single
      bounded task (workspace HARD RULE: "don't touch dirty files in other workspace areas"), and the watchdog's next
      sweep (≤1h) will verdict the existing pile automatically once deployed — no separate manual pass is needed.
      ORIGINAL FINDING: the original report was "slot 11 has 8 stashes in `market-tick-data-service`". A full fleet
      sweep on 2026-08-08 found **hundreds across 20 slots** — in `unified-trading-pm` alone: slot 10 = 31, slot 12 =
      24, slot 11 = 23, slot 13 = 23; plus slot 12 `market-tick-data-service` = 11, slot 11 `market-tick-data-service` =
      8, and long tails on features-service / unified-api-contracts / instruments-service. The oldest reach back to
      2026-06-23. Priority raised P3 -> P2 on that measured scale. Discarding foreign WIP is a workspace HARD RULE (and
      is hook-blocked for autonomous workers); at this scale a wrong call destroys real work fleet-wide — the single
      worst outcome available in this doc. Two findings made it tractable rather than open-ended: (a) the large majority
      are `autostash`, which git pops AUTOMATICALLY on a successful rebase — so a LEFTOVER autostash specifically means
      the pop FAILED (conflict), i.e. genuinely un-restored working state rather than noise; (b) the safe test is
      content-identity, the exact question `worktree_clean_check.verify_all_wip_preserve_refs` already answers for
      orphaned commits (is this content already in origin? SUPERSEDED / GONE / STILL-ORPHANED). (repo:
      agent-orchestrator)
- [x] ✅ [BACKEND] P2. **`stash_pile_stale` flood fixed — shipped agent-orchestrator@1709bfe6650b.** Transition-dedup
      keyed on stash COUNT (not `oldest_age_days`, which increments daily for a genuinely unchanged pile and would still
      log once/day/repo for no new information), persisted via `dedup_state.stash_pile_counts_path()`, with a
      `stash_pile_resolved` bookend when a pile drops below threshold — mirrors `OrphanRefVerifyWatchdog`'s exact shape.
      3 new tests, full `quality-gates.sh` green (2840 passed). **Collision note**: two slots independently picked up
      this exact todo and shipped functionally-identical fixes concurrently; slot-29's own copy (committed locally as
      979b3e6) was superseded on push by slot-4's `agent-orchestrator@1709bfe6650b` landing first on `live-defi-rollout`
      (verified via diff — same design: count-keyed latch, `stash_pile_resolved` bookend, 3 tests) — reconciled by
      discarding the redundant duplicate rather than pushing a second copy of the same fix. **Scope note on the original
      "Done when"**: "deployed to the central VM" + "verified live" could not be independently confirmed by this todo's
      closing worker — `ssm:SendCommand` on the central VM instance (`i-0c9b283b31d6b5ca7`) is denied for the
      `ikenna-worker` AWS identity (confirmed live: `AccessDeniedException`), and per this workspace's IAM self-service
      rule that identity is a human-tied credential, not one of the two ambient orchestrator identities
      (`unified-trading-sa`/`uts-orchestrator-epic-role`) a worker may self-grant roles on — so this is a genuine
      cross-identity gap, not a self-service case. The code is on `live-defi-rollout`; the already-fixed
      `ao-self-pull.sh` auto-deploy path (this same doc, earlier todo) should pick it up on its next cycle without
      manual intervention. A follow-up live-verification pass needs either operator SSM access or an interactive session
      with the orchestrator's own identity. ORIGINAL FINDING: same bug class as the already-fixed `orphan_ref_verified`
      flood above, found live 2026-08-09 while re-verifying this doc's own claims. `StashAuditWatchdog` (a SEPARATE,
      older watchdog from the `StashVerifyWatchdog` fixed above — one flags aged/large piles by count/age threshold, the
      other content-verifies individual stashes; the flood was in the former) logged one `stash_pile_stale` row per
      stale repo per tick, unconditionally — its own docstring literally cited `orphan_ref_verify_watchdog`'s PRE-FIX
      per-tick shape as its design template, written before that pattern was recognized as a bug and fixed earlier in
      this same 2026-08-08 session. Measured live: **51 of the last 500 `/api/activity` rows within roughly an hour** —
      smaller than the 76% orphan-ref flood but the identical root cause. Deployed + restarted 01:22 UTC, sha confirmed
      `1709bfe`. **Verified live with a real proof, not just "code looks right"**: the first post-deploy read showed 102
      rows (51 unique `(slot, repo, count)` keys, each appearing exactly twice) — NOT a live bug, but the fully-expected
      artifact of two restarts landing close together (`StashAuditWatchdog._loop` fires its first sweep IMMEDIATELY on
      thread start, before waiting the interval): one restart still ran the OLD unconditional code, the very next
      restart ran the NEW code against an empty latch (first-sight logging, by design). The actual test was a THIRD
      restart once the latch was populated: `stash_pile_stale` total stayed at **exactly 102 rows before and after** —
      zero new rows from a fresh forced sweep, proving the dedup latch survives restarts and correctly suppresses
      unchanged state. (repo: agent-orchestrator)

- [x] ✅ [OPERATOR] P3. **Glue-runner litter removed — 51 orphaned unit files retired 2026-08-08T13:05Z.** Verified
      immediately before acting, and re-asserted inside the same script as a refuse-guard: **0 of 51 active, 0 enabled,
      no `/opt/github-glue*` directory anywhere, and no `Runner.Listener` process** (an earlier `pgrep -fc` reading of 1
      was the grep matching itself). So nothing was serving CI from them. Moved — not deleted — to
      `/etc/systemd/system/.retired-glue-units-20260808T130521Z/`, fully reversible, and regenerable from
      `setup-glue-runners.sh` whenever the two-pool deployment actually happens. `systemctl --failed` is now 1
      (`audit-false-done`, by design) instead of carrying permanent litter that already cost one false "12 failing
      units" diagnosis this session. The runbook's `last_executed: NEVER` was already accurate and stands. ORIGINAL
      FINDING: `scripts/self-hosted-runners/README.md` still reads
      `last_executed: NEVER (files created 2026-07-15, redesigned     two-pool 2026-07-16; not yet deployed)`, yet 51
      `github-glue-*` unit files exist (written 2026-07-27) whose `ExecStart` points at
      `/opt/github-glue-runners-<repo>/refresh-gh-token.sh` — and **no such directory exists anywhere on the box**. They
      are all `enabled=disabled, active=inactive`, last result 203/EXEC, so they are inert litter rather than a live
      failure (this is why only ONE unit shows in `systemctl --failed`). A prior report of "12 failing token-refresh
      units" describes the pre-disable state and is no longer accurate. Deliberately left in place this session —
      deleting them would destroy scaffolding the real deployment needs. **Done when**: either the two-pool deployment
      is completed per `/plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md`, or the units are removed
      and the runbook's `last_executed` reflects the decision. `[OPERATOR]` because it is a cost/architecture call, not
      a bounded fix. (repo: unified-trading-pm)

## Progress Log

**2026-08-08 (interactive session, slot 4)** — Originated from an unrelated question about AO account-exhaustion
behaviour. Findings above were surfaced by reading `/api/activity` and the live systemd/journal state over SSM
(read-only except where noted). Two fixes shipped + deployed; the four todos above are deliberately NOT closed because
each needs either a per-item human read (false-done, stashes) or an architecture decision (glue runners), and the
self-pull fix touches the fleet's only auto-deploy path so it wants its own gated change rather than a same-session
drive-by. Corrected two earlier mis-reads during the session: the "12 failing glue units" are disabled-and-inert not
failing, and the "33 vs 27 repos" gap between old and new slots is leftover `*.stale-pre-history-rewrite-*` dirs, i.e.
the new slots are cleaner.

- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: RECLASSIFY → `assigned_vm: planning`. Re-read the doc
  fresh (it had moved significantly since filing — self-pull fix, false-done triage, and glue-runner retirement all
  shipped+closed by the originating/a concurrent session between this sweep's first and second pass). Of the 3 remaining
  open items: the fleet-cap raise is explicitly `[OPERATOR] P1` (capacity/spend ruling, correctly non-dispatchable
  within a `planning` doc — coexists fine per `task_template.md`'s non-dispatchable-marker convention); the slot-30
  re-run (`[BACKEND] P3`) is a single idempotent command re-invocation with a named root cause; the
  stash-content-verifier (`[BACKEND] P2`) has a concrete spec already written in-doc (reuse
  `worktree_clean_check.verify_all_wip_preserve_refs`'s SUPERSEDED/GONE/STILL-ORPHANED verdict vocabulary) and an
  explicit "Done when". No remaining judgment call on either bounded item. Conflict-check clear: grepped
  `plans/active/*.md` for `ORCHESTRATOR_FLEET_WORKER_CAP`/`stash_pile_stale`/`add-slot 30` — zero hits outside this doc.
  `execution_scope: local-only → orchestrator-agent`. Companion gated finalize:
  `ao_observability_and_deploy_hygiene_gaps_2026_08_08_finalize_2026_08_08.md`.

- **2026-08-09 (slot 29, backend_engineer)**: Picked up the `stash_pile_stale` flood todo. Implemented the same
  count-keyed transition-dedup fix independently, but on push discovered slot-4 had landed a functionally-identical fix
  first (`agent-orchestrator@1709bfe6650b`) — reconciled by discarding the redundant duplicate rather than shipping a
  second copy. Flipped the checkbox against the SHA actually on `live-defi-rollout`. Attempted the doc's own stricter
  "deployed to the central VM + verified live" bar via read-only SSM but hit `AccessDeniedException` on
  `ssm:SendCommand` for the `ikenna-worker` identity — a genuine cross-identity gap (not one of the two ambient
  orchestrator identities), so left as a named follow-up rather than self-granting a role on a human-tied credential.

- **2026-08-09 (interactive session, slot 4)** — Operator: "do al these thigns [fleet cap, slot 30, stash verifier] and
  whats leftblocked by me how can in help". Closed out all three remaining items, plus one NEW finding surfaced along
  the way. Order: (1) verified the stash-verifier todo's DONE claim against live infra rather than trusting the doc —
  commit `2572571` confirmed deployed on the VM (sha `03e1809`, ahead=0 of origin) before touching anything else; (2)
  while doing that verification, found `stash_pile_stale` flooding `/api/activity` the same way `orphan_ref_verified`
  did — a SEPARATE, older watchdog (`StashAuditWatchdog`) nobody had touched yet, whose own docstring cited the pre-fix
  `orphan_ref_verify_watchdog` shape as its design template; fixed with the identical transition-dedup pattern (this
  session's stash-flood todo above has the full live-verification detail); (3) raised `ORCHESTRATOR_FLEET_WORKER_CAP` 15
  -> 25 with operator approval ("do this yourself" supersedes the `[OPERATOR]` tag's original "not a unilateral call"
  framing — the arithmetic/headroom were already settled, only the ruling was outstanding, and the operator supplied
  it); (4) completed slot 30 to 26/26 repos, running as `ubuntu` rather than root to sidestep the git-ownership friction
  that plausibly caused the original core-dumps. Two QG runs were needed on the stash-flood fix: the first `| tee`
  invocation silently reported exit 0 despite a real pytest failure (pipe exit code reflects `tee`, not
  `quality-gates.sh` — a process-substitution gotcha, not a QG bug) and the second explicit `echo QG_EXIT=$?` capture
  caught it correctly; the failure itself was a genuine bug in my own new test (`git stash pop` against a fixture where
  every stash touches the same file collides on the second pop), fixed by switching to `stash drop`. Every todo this doc
  ever opened is now closed; `status: resolved`.

## Deferred work after 2026-08-09

Every item this doc ever tracked is now done. One item was never this doc's to finish and remains genuinely open
elsewhere — listed for continuity, not as unfinished work of this issue:

| item                                              | state                                                                                                                                                                                                                                                                            | blocked on                            |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| Content-stable task IDs (`_make_content_task_id`) | **Not this doc's — NOT MINE.** Built-but-unwired by another agent (agent-orchestrator@ac36202/@e0f107a). Deliberately not touched to avoid collision. Tracked here only because the false-done todo above cited it as the eventual root fix for the positional-task-ID artifact. | the other agent finishing the wiring  |
| Glue-runner two-pool deployment                   | **Operator-owned, separate decision.** Units retired (this doc's scope ends there); the deployment itself is a cost/architecture call per the archived CI-cost plan, not a defect this doc is tracking.                                                                          | an operator decision, whenever wanted |

No item in this table is blocking anything, and neither is a residual gap FROM this doc — both were always
out-of-scope-but-related. `status: resolved` above reflects that every todo this doc actually tracked is done; per the
observed convention for resolved issue docs in this corpus, it stays in place rather than moving to an archive dir.

## Lessons (would otherwise be re-learned the hard way)

- **`systemctl --failed` undercounts.** The glue units were disabled, so 51 broken units showed as ZERO failures while
  one by-design detector showed as the only failure. "Failed unit count" is not a health metric; enumerate and check
  `is-enabled` + `ExecStart` target existence.
- **A telemetry unit's own cgroup caps are scale-coupled.** `process-category-sampler` had
  `TasksMax=50`/`MemoryMax=256M` sized when the fleet was small; it enumerates every process, so it failed harder as
  slots were added — and failed SILENTLY into `--failed` for a day. Any per-process sampler needs caps that scale with
  the fleet, or it dies exactly when it is most needed.
- **Raising one cap exposes the next.** TasksMax 50 -> 256 turned "can't start new thread" into a MemoryMax-pinned,
  swapping timeout. Re-measure after each cap change rather than assuming the first fix was the fix.
- **`git status --porcelain` is the wrong dirty test for a deploy gate.** Untracked files cannot be lost to a
  fast-forward; `-uno` is the correct predicate. The 2026-07-29 fix patched two filenames and the class recurred within
  ten days — a strong argument for fixing predicates rather than instances.
- **Re-run an audit before triaging its findings.** false-done went 26 -> 1 with no action taken; 25 were same-day
  in-flight flips. Triaging the stale snapshot would have burned hours on already-resolved rows.
- **A "false-done" can be a mapping artifact with BOTH sides correct.** Positional task IDs mean a DB row and a checkbox
  can each be individually right while disagreeing. Neither flip nor reopen — verify the underlying work.
- **`git clone --reference` core-dumps ~1 in 16 clones here.** Not memory (23G free both times). A plain re-run clears
  it, but a short slot fails at first spawn rather than at provision time.
- **Ground truth is tmux, not the DB.** A slot table read mid-churn showed 7 working / 6 killed while `tmux ls` showed
  12 live sessions. Always cross-check fleet-fill claims against `tmux ls`.
- **A raw doc claim of DONE still needs a live check.** The stash-verifier todo above was already checked off with a
  commit sha before this 2026-08-09 session touched it — correct, but verified anyway (deployed sha + ancestry check)
  before building on top of it, per the workspace's own runtime-verification rule. Worth the ~2 SSM calls it cost.
- **A pipe's exit code is the LAST command's, not the interesting one's.** `bash quality-gates.sh 2>&1 | tee log`
  reported exit 0 on a run that actually failed a test — `tee` succeeded, `quality-gates.sh` didn't, and `$?` only sees
  `tee`. Capture the real command's exit code explicitly (`cmd; echo EXIT=$?`) whenever the result gates a ship
  decision.
- **A watchdog's `_loop()` firing its first sweep immediately (not after the first interval wait) means every restart
  produces a fresh sweep.** Two restarts close together (one on old code, one on new) look identical to a live flood in
  a single activity-feed snapshot (exactly 2x every count) — the actual proof of a dedup fix is a THIRD restart against
  an already-populated latch producing ZERO new rows, not the raw row count after the first deploy.
- **Every `git stash` test fixture that reuses one file across multiple stashes can only safely `drop`, never `pop`, in
  a loop.** Popping restores content to the working tree; the next pop's restore then collides with what the previous
  pop left behind. `drop` never touches the working tree, so it has no such collision — use it whenever a test only
  needs to shrink the stash COUNT, not verify restored content.
