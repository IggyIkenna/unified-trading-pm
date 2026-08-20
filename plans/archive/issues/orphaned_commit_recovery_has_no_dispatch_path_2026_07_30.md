---
doc_type: issue
title: >-
  Ten-plus confirmed orphaned/preserved worker commits across four AO issue docs have no dispatch path at all — every
  recovery todo is `[WORKER]`/`[BACKEND/OPERATOR]` inside an `assigned_vm: NA` doc, so none is auto-dispatchable, and
  two of them are on a real GC clock
summary: >-
  Aggregation finding from the `/na-eligibility-audit ao` run (2026-07-30). Four separate `assigned_vm: NA` issue docs
  in the `ao` tranche each independently record confirmed, still-unrecovered committed worker work — orphaned by a
  `branch: Reset to origin/live-defi-rollout` (root-caused to `quickmerge.sh::cascade_dep_branch()`'s `checkout -B`,
  whose preserve-guard has a proven TOCTOU race), stranded off-origin on a dead slot, or successfully quarantined into a
  `refs/wip-preserve/cascade-*` ref that nothing then surfaces or re-applies. Individually each doc is correctly
  classified and correctly NA. Collectively they share ONE unowned root gap that no doc states: **there is no dispatch
  path for cross-slot commit recovery.** Every recovery todo is tagged `[WORKER]` or `[BACKEND/OPERATOR]` and lives in a
  non-dispatched doc; executing one needs read/write access to ANOTHER slot's worktree on `ip-172-31-5-118`, which the
  multi-agent-safety HARD RULE bars; and the main agent is charter-barred from pushing code or editing a foreign
  worktree. So the work cannot reach a worker by any existing route. `branch_reset_to_origin_orphans_unpushed_worker_
  commits_2026_07_27.md` says this outright in its own `⚠️ DISPATCH GAP` banner ("they will rot unless…") and escalated
  it 2026-07-27 — it has now sat unrouted for 3 days. Two of the items have real deadlines, not indefinite ones.
status:
  resolved # inventory 100% terminal (see banner); all todos now [x] (the 3 prevention todos the "stays OPEN"
  # comment referred to have since shipped). RULED 2026-08-02 (operator ruling on
  # plan_reconcile_parked_operator_decisions_2026_08_02.md § 3, option A): "stays OPEN to hold prevention todos" is the
  # anti-pattern the codex lifecycle SSOT names -- the correct pattern is ACKED-INTO-PLAN then archive (see
  # ci_satellite_ao_dispatch_batch1_2026_07_26.md's "Migrated from resolved incidents" section for that pattern applied
  # to 3 sibling docs the same day). This doc now has zero open todos, so status:resolved is simply correct, not a
  # contradiction of the ruling -- archival-eligible, tracked as a todo below rather than executed inline here to avoid
  # a large multi-referrer (6 files) repoint mid-batch.
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm, unified-api-contracts, features-service, strategy-service]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    per-slot-worktrees,
    orphaned-commit,
    wip-preserve,
    data-loss,
    dispatch-gap,
    multi-agent-safety,
    routing,
    big-finding,
  ]
related:
  [
    /plans/archive/issues/branch_reset_to_origin_orphans_unpushed_worker_commits_2026_07_27.md,
    /plans/archive/2026_08/wip_preserve_refs_silently_unrecovered_2026_07_29.md,
    /plans/archive/issues/idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md,
    /plans/archive/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md,
    /plans/archive/2026_08/issues/utl_shared_clone_commits_repeatedly_reset_2026_07_22.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: 2026-07-30
last_updated: 2026-08-01
priority: P1
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
resolved_by:
  bounded recovery sweep (2026-07-30, operator-authorized route (a)) + the 3 prevention todos it filed, all now [x] as
  of 2026-08-02
archive_exempt: true # inline status comment is stale (all 3 prevention todos now closed) -- archival routed through ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md's [REVIEW] P0 todo, not standalone (see na-eligibility-audit 2026-08-01 entry)
locked_by:
context_scope:
  [
    /plans/archive/2026_08/issues/utl_shared_clone_commits_repeatedly_reset_2026_07_22.md,
    /plans/archive/2026_08/wip_preserve_refs_silently_unrecovered_2026_07_29.md,
    agent-orchestrator/server/worktree_clean_check/_liveness.py,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
locked_since:
depends_on: []
source: >-
  /na-eligibility-audit ao run, 2026-07-30 (autonomous). Surfaced by reading all 39 of the tranche's assigned_vm:NA docs
  end to end: four of them independently record unrecovered committed work, and all four are blocked on the same missing
  routing mechanism rather than on any technical question.
---

# Orphaned/preserved commit recovery has no dispatch path

> **This doc adds no new incident.** Every item below is already documented, already root-caused, and already correctly
> classified in its own doc. What is NOT owned anywhere is the shared consequence: none of it can be dispatched, so none
> of it is moving. Filed per the findings-triage HARD RULE (data-loss-class + cross-repo) because the aggregate is
> invisible from any single doc.

> **✅ RESOLVED 2026-07-30 by the operator-authorized bounded recovery sweep (route (a)). Read the "Sweep result"
> section below before acting on anything in this doc — the inventory table's `State` column is the 07-27..07-30
> snapshot and is now STALE.** Headline: **all 10 rows reached a terminal verdict and ZERO recoveries were needed.** 8
> were already SUPERSEDED (the work had independently re-landed on `origin/live-defi-rollout`, in several cases 27-35
> minutes after the orphaning, by the same worker redoing it better), 1 is PROTECTED-LIVE, 1 is GONE (content no longer
> on disk, presumed duplicated). The 2 GC-clock objects are now branch-reachable AND independently confirmed superseded.
> **The data-loss exposure this doc escalated was, by the time it was executed, already zero** — see "What this sweep
> actually proves" for why that is a finding about the ESCALATION, not a reason to relax the fix.
>
> **`status` stays `open` deliberately**: the inventory is 100% terminal and the routing question is discharged, but the
> sweep filed 3 prevention todos (verifier, liveness triangulation, wip-preserve triage) that are genuinely open.
> Archive this doc when those close, not before.

## The inventory (each already evidenced in its own doc — not re-derived here)

`State` = the 07-27..07-30 snapshot as filed. `Verdict (07-30 sweep)` = the terminal, measured outcome — this column is
the authoritative one.

| Item                                                                           | Repo                     | Owning doc                                                 | State (as filed)                   | Verdict (07-30 sweep)                                       |
| ------------------------------------------------------------------------------ | ------------------------ | ---------------------------------------------------------- | ---------------------------------- | ----------------------------------------------------------- |
| slot-13 `207afd62` (census-manifest persistence)                               | features-service         | `branch_reset_to_origin_orphans_unpushed_worker_commits`   | orphaned, backstop patch saved     | **SUPERSEDED** by origin `a90256f5` (+27 min)               |
| slot-13 `d1c1ad8a` (per-venue accepted-quote extension)                        | features-service         | same                                                       | orphaned, backstop patch saved     | **SUPERSEDED** by origin `a9429cba` (+35 min)               |
| slot-9 `724bd9be` (`fix(registry)` VENUE_ORDER_SEMANTICS)                      | unified-api-contracts    | same                                                       | orphaned, backstop patch saved     | **SUPERSEDED** by origin `698b5b6f` (byte-identical)        |
| slot-12 `559452e` (`/api/backlog/{id}/reconcile-brief` route + 240-line test)  | agent-orchestrator       | same                                                       | orphaned, backstop patch saved     | **SUPERSEDED** by origin `09cda29` (same route, shipped)    |
| `refs/wip-preserve/cascade-strategy-service-a77eb6d170ca` (staging-lock-check) | strategy-service         | `wip_preserve_refs_silently_unrecovered`                   | preserved, unrecovered since 07-28 | **SUPERSEDED** — file byte-identical to origin              |
| slot-6 `44de0cf0` + `11ed7f09` (GMX cassette cleanup)                          | unified-api-contracts    | `idle_slot_dirty_wip_never_auto_resolves`                  | **dangling objects, GC-eligible**  | **GC-SAFED + SUPERSEDED** (ref created; 0 gmx on origin)    |
| slot-10 `4d235caf` (3 dead-script deletions)                                   | market-tick-data-service | same                                                       | 1 ahead / 1 behind                 | **SUPERSEDED** — 3 scripts already absent on origin         |
| slot-11 8 unpushed `docs(plans):` commits (top `c6610a36c`)                    | unified-trading-pm       | same                                                       | 8 ahead / 1 behind                 | **SUPERSEDED** — 7/8 on origin; 8th regressive (-143)       |
| slot-3 features-service WIP (19 files, 722+/714-)                              | features-service         | same                                                       | dirty, unowned                     | **GONE** — not in worktree, not in stash; presumed dup      |
| slot-16 / slot-10 / slot-5 stranded ahead-commits                              | agent-orchestrator, PM   | `killed_slot_orphans_committed_unpushed_work_no_push_path` | ahead/diverged, off-origin         | **RESOLVED** — all now `ahead=0`; slot-5 already SUPERSEDED |

## Why none of it moves (the actual finding)

Three independent blocks, all structural, none technical:

1. **Every recovery todo lives in an `assigned_vm: NA` doc**, so the backlog regenerator never derives a task from it.
   `branch_reset_to_origin_orphans_unpushed_worker_commits_2026_07_27.md`'s own banner states the consequence and the
   three ways out verbatim: "(a) migrated into a dispatched plan (`assigned_vm: planning`), (b) a worker is explicitly
   routed to them, or (c) main is authorized to run the quickmerge recovery directly… **Escalated to operator for
   routing.**" That escalation is 3 days old.
2. **Execution needs foreign-worktree access.** Recovery means cherry-picking from `.tabs/<n>/<repo>`'s reflog (or
   applying a host-local `.orch-orphan-commits-recovery/*.patch`) belonging to a DIFFERENT slot. CLAUDE.md's
   multi-agent-safety block bars exactly this ("Never edit unfamiliar/untracked/recently-pushed files… a dirty file you
   don't own"), and the rule is right — the liveness gate cannot be evaluated safely from another slot.
3. **The main agent is charter-barred** from pushing code and from editing a foreign worktree, which every one of these
   docs records independently. So the one actor with fleet-wide visibility is the one actor that cannot act.

The net is a closed loop: the docs are correctly NA, the todos are correctly tagged, the safety rule is correctly
enforced — and the work is correctly stuck.

## Why it is time-sensitive (two real clocks, not indefinite)

- **slot-6's `44de0cf0`/`11ed7f09` are DANGLING objects**, not branch-reachable — subject to `gc.pruneExpire` (git
  default ~2 weeks). Recorded orphaned 2026-07-25, so the practical deadline is **~2026-08-08**. Low content value (dead
  GMX fixtures) but a genuine deadline, and a legitimate decline-to-recover is fine IF recorded before GC makes the
  choice silently.
- **The reflog-only orphans** (`207afd62`, `d1c1ad8a`, `724bd9be`, `559452e`) sit under the 90-day reflog default, so
  ~2026-10-25 — comfortable, but only while those slot clones are never re-created. A `setup-tab-worktrees.sh` re-clone
  or a disk action ends it immediately, and this fleet has already had one disk resize (2026-07-27) in this window.
- `wip-preserve` refs are durable by construction (`git update-ref`, independent of reflog expiry) — those are safe; the
  problem there is purely that nothing surfaces them.

## The one thing that would unblock all of it

A single routing decision, not a design. Options, for an operator ruling:

- [x] ✅ **[OPERATOR-DECISION] P1 — RULED 2026-07-30: route (a) chosen and EXECUTED. Every inventory row now carries a
      terminal verdict (table above); zero recoveries were required.** See "Sweep result" below for the per-item
      evidence. Original options preserved for context: **(a) [RECOMMENDED]** Authorize a single named `infra`-role
      worker, dispatched ON `ip-172-31-5-118`, to run one bounded recovery sweep across the inventory above with an
      explicit liveness gate per slot (dead/expired `.agent-claim` → recover; live claim or mtime <120s → PROTECT and
      skip), shipping each recovered commit via `quickmerge --agent --files`, and recording a per-item recovered /
      superseded / deliberately-declined verdict. This is the smallest change: it needs no new mechanism, it reuses the
      liveness discriminator the FM8 gate already implements, and one sweep clears the whole backlog of items. **(b)**
      Authorize main to run the quickmerge recovery directly (a charter amendment — narrower in scope but changes a
      standing boundary). **(c)** Migrate the recovery todos into an existing active `assigned_vm: planning` plan and
      let normal dispatch pick them up (works, but each todo still hits the foreign-worktree bar, so it only helps if
      paired with (a)'s liveness-gate carve-out). **(d)** Explicitly write the whole inventory off with a recorded
      rationale — legitimate for the low-value items, and better than silent GC. **Done when**: this todo names the
      chosen route and each inventory row above reaches a recorded terminal verdict.

## Sweep result (2026-07-30, operator-authorized route (a), infra role)

Executed from a laptop slot against host `ip-172-31-5-118` (= EC2 `i-0c9b283b31d6b5ca7`, confirmed via
`aws ec2 describe-instances --filters Name=private-ip-address,Values=172.31.5.118`) read-only over AWS SSM
`AWS-RunShellScript`. **No foreign worktree file was written, no HEAD was moved, no branch was reset, nothing was
force-pushed, and no `git stash drop` / `reset --hard` / `clean` was run anywhere.** The only write of any kind across
the whole sweep was one additive `git update-ref` creating a new preserve branch (below), which touches neither HEAD,
index, worktree, nor any pre-existing ref.

### The GC-clock items are SAFE (item 5 of the brief — done first)

`refs/heads/preserve-gmx-cleanup-slot6` → `44de0cf0bd7ae48a5d1a8e90ce4d901e2ceed201`, created in
`.tabs/6/unified-api-contracts`. Verified: `git fsck --unreachable | grep -cE '44de0cf0|11ed7f09'` → **0** (both were
listed as unreachable before, neither is now). **They are no longer dangling and no longer on any `gc.pruneExpire`
clock.**

> **Correction to the recovery recipe in `idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md`**: that doc says
> "`git branch preserve-gmx-cleanup 11ed7f09` (un-orphans both — `44de0cf0` is its parent)". **The parentage is
> backwards** — measured, `44de0cf0`'s parent IS `11ed7f09` (`11ed7f09` → `18d53d63` → origin). Branching at `11ed7f09`
> as written would have saved only one of the two and silently let `44de0cf0` GC. The ref was therefore created at
> `44de0cf0` (the tip), which reaches both.

Belt-and-braces only, as it turns out: the content is **independently already on origin**.
`tests/test_ws_cassette_ coexistence.py` is byte-identical between `44de0cf0` and `origin/live-defi-rollout`, both
`gmx/__init__.py` and `gmx/mocks/gmx_arbitrum_ws.yaml` are absent from origin (the deletions landed), and
`git ls-tree -r --name-only origin/live-defi-rollout | grep -i gmx` returns **zero paths**. So the GMX cleanup is
complete upstream and nothing needs cherry-picking. The ref stays as a cheap permanent record.

### Liveness gate outcomes (measured 2026-07-30T10:31Z, re-checked through 10:40Z)

Gate inputs per slot: `tmux has-session`, `.agent-claim` presence + mtime, AO `/api/state`
(`worker_alive`/`tmux_alive`/`last_ping`), and `readlink /proc/<pid>/cwd` for any process rooted in the slot dir.

| Slot | Gate verdict  | Basis                                                                                        |
| ---- | ------------- | -------------------------------------------------------------------------------------------- |
| 3    | **LIVE**      | `.agent-claim` mtime 1 min, `orch-slot-3` up, `worker_alive=true`, working                   |
| 5    | LIVE          | `orch-slot-5` up, `worker_alive=true` (claim file long expired — claim alone lies)           |
| 6    | LIVE          | `orch-slot-6` up, `worker_alive=true`, on task `qg_size_gate_sentinel_skip_root_cause-004`   |
| 9    | dead at 10:31 | no tmux, no claim, `worker_alive=false`                                                      |
| 10   | dead at 10:31 | no tmux, no claim, `worker_alive=false`                                                      |
| 11   | **LIVE**      | `orch-slot-11` up (created 10:23), `worker_alive=true`, working                              |
| 12   | **LIVE**      | `orch-slot-12` up (created 10:24), `worker_alive=true`, working                              |
| 13   | **LIVE**      | `orch-slot-13` up (created 10:26), `worker_alive=true`, working                              |
| 15   | **LIVE**      | respawned MID-SWEEP — read dead at 10:31, then `orch-slot-15` up + PID 525907 `cwd=.tabs/15` |
| 16   | **LIVE**      | `.agent-claim` mtime 3 min, `worker_alive=true` (operator interactive slot)                  |

**The gate earned its keep twice.** (1) Slot 15 read DEAD at 10:31Z and LIVE at 10:40Z — it respawned inside the sweep
window, and it holds a genuine unpushed commit (below). Anything acting on the 10:31Z reading alone would have touched a
live worker's in-flight work. (2) Slot 5's `.agent-claim` was **46,102 minutes** (32 days) expired while the slot was
demonstrably alive — **an expired claim file is NOT sufficient evidence of death**; only the tmux + process +
`/api/state` triangulation is. Any future automated sweep must triangulate, not read the claim.

### Per-item findings that changed the picture

- **The dominant pattern is same-worker re-do, not data loss.** In the two features-service cases the orphaned commit
  was re-landed by the same slot **27 and 35 minutes later**, better: `207afd62` (16:50Z) → origin `a90256f5` (17:17Z,
  renames `_CENSUS_MANIFEST_PATH`→`_STABLE_CENSUS_MANIFEST_PATH` and sharpens the docstring); `d1c1ad8a` (22:52Z) →
  origin `a9429cba` (23:27Z, "make universe-filter quote gate venue-aware", which keeps the `@functools.cache`
  `_sorted_quotes_for_venue()` delegating to `accepted_quotes_for_venue` that the orphan had _removed_).
- **Four of the ten would have been REGRESSIONS if recovered blind.** `git diff origin <orphan>` is net-negative for
  `207afd62`, `d1c1ad8a`, `559452e` (−347/+290 across 4 files vs the shipped `09cda29` implementation) and `c6610a36c`
  (−143/+31 — origin's copy of that doc already carries the 287-league enumeration and the full 2026-07-25T12:54Z launch
  narrative). **Recovering an orphan without diffing it against origin FIRST is the real hazard here, and it is the
  opposite of the hazard the doc was filed about.**
- **slot-11's "8 unpushed commits" was really 1.** 7 of the 8 are already ancestors of `origin/live-defi-rollout`; only
  `c6610a36c` is not, and that one is the regressive doc revision above.
- **slot-3's 19-file / 722+/714- WIP no longer exists.** `.tabs/3/features-service` is `dirty=0 ahead=0`; the only stash
  present is an unrelated 2-file `cross_instrument/batch_handler` WIP dated **2026-06-16**. The 2026-07-25 content is
  not in the worktree, the index, the stash, or any ref. Per the owning doc's own prediction it was duplicated by
  slot-11's re-run of `batch2-001`. Recorded as GONE rather than recovered — there is nothing left to recover, and this
  is exactly the outcome the "record it before it silently disappears" instinct was meant to catch.

## What this sweep actually proves (the finding worth keeping)

The escalation was correct to make and the fix work should NOT be relaxed — but the **cost model in this doc was wrong
in a specific, correctable way.** Nothing was lost, and nothing was ever going to be lost, because the fleet's own re-do
behaviour had already closed all ten gaps within roughly a day of each orphaning. What the 3-day unrouted escalation
actually cost was **three days of carrying a false P1 data-loss exposure** — four issue docs, one aggregation doc, and
an operator decision, all describing risk that had already evaporated.

The missing capability is therefore **not** a recovery dispatch path. It is a **cheap, read-only, periodic
`is-it-still-orphaned?` verifier**: for each recorded orphan sha, `git merge-base --is-ancestor` plus a per-file blob
compare against `origin/live-defi-rollout`. That is seconds of work per item, needs no worktree write, no liveness gate,
and no operator authority — and it would have auto-closed 8 of these 10 rows without a human ever being asked. Recovery
authority is the expensive answer to a question that a verifier answers for free.

- [x] ✅ **SHIPPED 2026-08-01 — agent-orchestrator@623009e3.** Added a read-only `verify_orphan()` in
      `server/worktree_clean_check/_orphan_verify.py`: reports `git merge-base --is-ancestor <sha> origin/<branch>`,
      a per-touched-file blob-level `SAME-AS-ORIGIN`/`DIFFERS`/`ABSENT-ON-ORIGIN`/`ABSENT-IN-COMMIT` verdict, and the
      `git diff <remote>/<branch> <sha>` line-delta SIGN, emitting exactly `SUPERSEDED`/`STILL-ORPHANED`/`WOULD-REGRESS`
      (plus a 4th `GONE` state for a sha with no resolvable commit object at all — the slot-3 shape below).
      `discover_wip_preserve_refs`/`verify_wip_preserve_ref`/ `verify_all_wip_preserve_refs` cover both known ref
      namespaces (`refs/wip-preserve/**` local-only, `refs/heads/wip-preserve/**` pushed). Wired into the
      orphan-recording path via a new standalone `server/orphan_ref_verify_watchdog.py` (hourly, tunable
      `tuning.orphan_ref_verify_interval_seconds`; deliberately NOT folded into `WorkerLivenessWatchdog._tick_once`, a
      documented file-adjacency hot spot for two sibling batch-3 todos) — every tick logs `orphan_ref_verified` per ref
      plus a distinct `orphan_ref_self_closed` for a SUPERSEDED/GONE verdict, never mutating/deleting any ref.
      **Reproduction of this sweep's 10 verdicts**: the real 10 shas live in OTHER slots' (6/9/10/11/12/13/15/16) local
      git object stores on `ip-172-31-5-118`, not reachable from the session that built this verifier (neither
      filesystem nor an authorized SSM path for THIS task) — so the verifier is instead proven against synthetic repos
      reproducing each of the 4 distinct FACT PATTERNS this sweep's 10 rows actually exhibited (ancestor-supersede /
      byte-identical-supersede / net-negative-regress / gone), one test per pattern plus batch-discovery coverage, in
      `tests/test_orphan_still_orphaned_verifier.py` (11 tests, all green). This is the honest substitute for
      sha-literal reproduction, not a claim of having re-run against the real 10 shas.
- [x] ✅ **SHIPPED 2026-08-01 — agent-orchestrator@623009e3.** `classify_maker_liveness()`
      (`server/worktree_clean_check/_liveness.py`) now triangulates: when `slot_id` is supplied and this is NOT an
      active respawn (`replacing_session is None`), an otherwise dead/absent claim-based verdict is cross-checked
      against `/api/state.worker_alive` (DB `last_ping`, same formula `routes/state.py`/`stale_dispatch.py` already use)
      and a live `/proc/<pid>/cwd` under the slot (via `pgrep -f <path>` + a cwd readlink, the same pattern
      `worker_liveness/_git_alerts.py`'s git-staleness alert already uses) — either signal overrides to `"live"`. Gated
      off whenever `replacing_session` is set, so `_preserve_wip_before_kill`'s one caller (whose own slot IS alive at
      that exact instant, by design) keeps its untriangulated verdict. `_orphan.py`'s FM8 guard now re-asserts this
      immediately before EACH repo's write inside the commit loop (not once for the whole batch) — the exact "re-assert
      before any write" requirement. **Verified against both recorded shapes**:
      `test_liveness_triangulates_worker_alive_over_expired_claim` (slot-5: 32-day-expired claim, `worker_alive_fn`
      forced True → `"live"`) and `test_liveness_triangulates_proc_cwd_over_absent_claim` (slot-15: no claim/tmux,
      `proc_cwd_fn` forced True → `"live"`), both in `tests/test_dirty_state_resolution.py`, plus a dead-stays-dead
      control (slots 9/10 shape), a `replacing_session`-set control, and a zero-behavior-change-when-no-slot_id control.
      Quality gate green (2212 tests) before shipping.
- [x] [DATA] P3. **Triage the 24 previously-uninventoried `refs/wip-preserve/**` refs this sweep found fleet-wide.**
      This doc tracked exactly ONE (`cascade-strategy-service-a77eb6d170ca`, now verified SUPERSEDED); a fleet-wide
      `for-each-ref`found **25**, dated 2026-07-26..2026-07-29. First-pass blob-compare says ~16 are content-identical
      to origin (superseded) and the rest are near-misses:`slot-2 unified-api-contracts f1e109bc`and
      `slot-3 unified-api-contracts ce7d7d1e`are net-NEGATIVE vs origin (origin already ahead — would regress);
      `slot-12 deployment-service 0e62096`is fully upstream;`slot-9 strategy-service b76f37db`adds
      **comment-only** lines (the functional`runs-on: [self-hosted, glue]`migration is already on origin); the three
      `slot-11 scripts/setup.sh`refs are a cosmetic`uv==0.10.8`→`"uv==0.10.8"`shell-quoting nit. The only
      substantive residual found is`slot-12 unified-trading-library c927ec58`(docstring`lst_staking_yields`→
      `lst_yields`, 2 lines) — needs a check of which feature_group name is actually correct before shipping either way.
      **Done when**: each of the 25 refs has a recorded SUPERSEDED / RECOVER / DELETE verdict. Depends on the verifier
      above — do not hand-triage these one by one. **Attempted 2026-08-01 (batch3 todo 3), using the now-shipped
      verifier — 0/25 reachable from that session, checkbox deliberately left unresolved.** These refs are
      `refs/wip-preserve/cascade-*`/`refs/wip-preserve/quickmerge-*` (`quickmerge.sh`'s
      `cascade_dep_branch()`/STAGE-5-regate guard) — created via a LOCAL-ONLY `git update-ref`, never pushed, so they
      exist ONLY in the specific slot's OWN `.git` on the host that created them. The session that built the verifier
      ran on a laptop host with local filesystem access to slots 1-5 and 21-30 only (not 6/9/10/11/12/13/15/16 — those
      live on `ip-172-31-5-118`, a different physical host, not reachable from that session's filesystem or an
      authorized network path for that task). An exhaustive `git for-each-ref 'refs/wip-preserve/**'` across all 375
      git repos in every one of that session's reachable slots (1-5, 21-30) found ZERO local wip-preserve refs anywhere
      — confirming this specific 25-ref population genuinely has no presence outside the original sweep's host. (A much
      larger, UNRELATED, ongoing population of `refs/heads/wip-preserve/orchestrator-slot-<N>-<sha>` and
      `refs/heads/wip-preserve/slot-<N>-<repo>-<status>-<ts>` refs — pushed by
      `_orphan.py`/`_ahead_push.py`/`_branch_state.py`'s own routine mechanisms — IS visible via `git ls-remote origin`
      from any clone; that is a different, much bigger, continuously-growing population and is NOT this doc's 25.) This
      todo needs a session dispatched with reach into `ip-172-31-5-118` (or run directly from it) to actually execute —
      the verifier itself is ready and tested. **Completed 2026-08-01**: a later session DID have SSM reach into
      `ip-172-31-5-118` (the prior attempt only checked local filesystem access, never tried SSM) — ran the verifier
      against all 24 distinct repo paths across the 9 named slots (29 refs now, up from 25, 4 new cascade branches
      accumulated in the 2 intervening days). Result: **16 SUPERSEDED, 10 STILL-ORPHANED, 3 WOULD-REGRESS, 0 GONE** —
      full per-ref table in `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch3_2026_07_31.md`'s Progress Log (2026-08-01,
      "todo 3 sub-part 3 — completed" entry). Confirms this doc's own first-pass predictions: slot-2/3's near-misses are
      genuinely WOULD-REGRESS (net -139/-198), slot-12's `unified-trading-library c927ec58` residual is real
      (STILL-ORPHANED, net 0, the `lst_staking_yields`→`lst_yields` docstring question is still open), and the ~16
      SUPERSEDED estimate was accurate. Deliberately NOT recovered/deleted — verify+record was this todo's scope; acting
      on the 10 STILL-ORPHANED/3 WOULD-REGRESS rows is separate follow-up work, not required by this todo's own "done
      when" bar.

## Follow-ups that are NOT this doc's scope

The prevention side is already owned and should not be duplicated here:
`/plans/archive/2026_08/issues/utl_shared_clone_commits_repeatedly_reset_2026_07_22.md` item 8 owns the `cascade_dep_branch`
prevention-vs-preserve fix (its item 7 proved the current preserve-guard has an inherent TOCTOU race), and
`/plans/archive/2026_08/wip_preserve_refs_silently_unrecovered_2026_07_29.md`'s `[SCRIPT] P3` owns the
`refs/wip-preserve/**` surfacing sweep. This doc is only about routing the ALREADY-orphaned backlog.

## Live worker commits observed but deliberately NOT touched (PROTECT)

Recorded so a later sweep does not mistake normal in-flight work for an orphan. All three are healthy workers holding
their own commits; none is orphaned, none is on any GC clock, and none needs intervention.

| Slot | Repo                     | Ahead | Newest commit     | Why protected                              |
| ---- | ------------------------ | ----- | ----------------- | ------------------------------------------ |
| 4    | deployment-service       | 1     | `5976da7` 10:32Z  | live, committed ~1 min before observation  |
| 7    | market-tick-data-service | 2     | `8016c7e4` 10:34Z | live, committed seconds before observation |
| 15   | instruments-service      | 1     | `570b9990` 08:03Z | respawned mid-sweep; live process in slot  |

`slot-15@570b9990` (`fix(events): suppress AttributeError from publish_coordination_event in live+mock mode`, +7/−3) is
genuinely not on origin and is genuinely useful — it is left with its live owner to ship, which is the correct outcome,
not a declined recovery.

## Progress Log

- **2026-08-02 (operator ruling applied)**: `status` flipped `open → resolved` — see the frontmatter comment. The 3
  "prevention todos" the old `status: open` comment referred to (verifier, liveness triangulation, wip-preserve triage,
  logged in the entry below) are now all `[x]`. Not archived in this same edit — 6 files reference this doc's path and a
  full repoint sweep is out of scope for this batch.
  - [ ] [DOC] P3. **Archive this doc** (6-step ritual: banner, `git mv` to `plans/archive/2026_07/`, repoint all 6
        referrers — `branch_reset_to_origin_orphans_unpushed_worker_commits_2026_07_27.md` (already archived, its own
        copy's reference is historical, may not need a fix), `ao_open_issues_consolidated_close_out_2026_07_17.md`,
        `ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md`,
        `plan_reconcile_parked_operator_decisions_2026_08_02.md` (this run's own citation — will self-resolve once
        archived), `ao_satellite_ao_dispatch_batch3_2026_07_31.md`,
        `wip_preserve_refs_silently_unrecovered_2026_07_29.md`). Zero open todos, not locked — archival-eligible per
        `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`.
- **2026-07-30 (bounded recovery sweep, infra role, operator-authorized route (a))**: Executed the full 10-row inventory
  against `ip-172-31-5-118` read-only over AWS SSM. **Terminal verdicts: 8 SUPERSEDED, 1 PROTECTED-LIVE (slot-3 WIP's
  slot; the WIP itself GONE), 1 RESOLVED. Zero recoveries shipped, zero needed.** GC-clock items handled first and
  confirmed safe (`refs/heads/preserve-gmx-cleanup-slot6` → `44de0cf0`; `git fsck --unreachable` count 0); their content
  was additionally found already complete on origin. Found and corrected a backwards parentage claim in the owning doc's
  recovery recipe that would have GC'd `44de0cf0`. Liveness gate flipped two decisions (slot 15 respawned mid-sweep;
  slot 5's claim was 32 days expired while alive) — recorded as a hardening todo. Discovered that 4 of the 10 rows would
  have been REGRESSIONS if recovered blind, and that the fleet-wide `refs/wip-preserve/**` population is 25, not the 1
  this doc tracked. Three new `- [ ]` todos filed above (verifier, liveness triangulation, wip-preserve triage). No
  foreign worktree file written, no HEAD moved, no branch reset, nothing force-pushed.
- **2026-07-30** (`/na-eligibility-audit ao`, autonomous): Filed. Not a new incident — an aggregation across four
  `assigned_vm: NA` docs read end to end during the tranche's first-ever NA-eligibility pass. Each doc's own
  classification was left unchanged (all four verdicted KEEP-NA, correctly); this doc exists because the shared blocker
  — no dispatch path — is invisible from any one of them and had no owner. No commits were touched, no worktree was
  inspected, and no recovery was attempted by this run: every route requires the authority ruling above.
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): ARCHIVE-eligible (0 open
  todos; re-read the whole doc for prose-only remaining work per the corpus trap warning — none found, the "Live worker
  commits observed but deliberately NOT touched (PROTECT)" table is a record, not a todo; the stale `status: open`
  inline comment predates the 2026-08-01 completions). **Not archived independently** —
  `ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md` (active `assigned_vm: planning`) carries its own
  `[REVIEW] P0` todo explicitly naming this doc (with the caveat "likely still has open non-batched items — check before
  archiving") for the standard 6-step archival ritual. Archiving it here would duplicate that already-queued AO work.
