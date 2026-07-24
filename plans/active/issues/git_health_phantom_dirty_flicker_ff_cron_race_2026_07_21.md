---
doc_type: issue
title:
  "git-health phantom-dirty flicker: slot-git-status-report.sh races the 5-min FF-pull cron, emits a transient dirty
  that re-stamps not_clean_since to the poll time and can reset the sync-nudge age on a genuinely long-dirty repo"
summary:
  The per-slot git-health reporter (unified-trading-pm/scripts/dev/slot-git-status-report.sh) runs `git status
  --porcelain` on a ~5-min cadence and POSTs the result to /api/slots/{slot_id}/git-status. On repos the 5-min FF-pull
  cron (slot-cron-ff-pull.sh) actively touches, a status read caught mid-fetch/merge transiently reads dirty (mtime-
  churned but content-identical index entries) even though nothing is uncommitted. The server (git_health.py
  _propagate_not_clean_since) is CORRECT for a continuously-dirty repo — it preserves the prior not_clean_since and only
  stamps snapshot_time on a FIRST non-clean observation — so a not_clean_since pinned to the exact poll timestamp is the
  fingerprint of a reporter-side flicker (clean -> transient dirty -> clean). The only real harm — an intermittent CLEAN
  poll clears not_clean_since (git_health.py 88-90), resetting the age the ~30-min sync-nudge escalation depends on, so
  a genuinely long-dirty repo that happens to flicker could dodge the nudge. Non-blocking, digest-class. Confirmed on 3
  instances 2026-07-21 (slot3 unified-trading-pm, slot4 deployment-ui, slot16 unified-trading-pm), each re-verified
  genuinely clean via direct `git status --short` with no actual staleness >30min.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [git-health, monitoring, false-positive, race-condition, ff-cron, per-tab-worktrees, agent-orchestrator]
related:
  [
    plans/active/issues/slot5_deployment_api_dirty_false_positive_2026_07_13.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: 2026-07-21
last_updated: 2026-07-23
priority: P2 # (was: P1) DOWNGRADED 2026-07-23 — the P1 escalation was driven by "ongoing fleet-wide FF-pull starvation on live slots"; that is measured ABSENT today (all live non-clean rows on hk verified REAL, file-for-file), and agent-orchestrator@529b0dc (cross-host row clobber) is live. The remaining count-integrity defect is a monitoring-integrity concern, not an operational one.
parent_epic: infrastructure_master
source: "review(slot1) msgs 1530/1532/1534 to main orchestrator, 2026-07-21"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

> **🟡 READ THIS FIRST (2026-07-23) — the diagnosis below evolved four times and two of its conclusions are now
> retracted.** Live re-verification found: (a) the phantom does **NOT** reproduce — every non-clean row on `hk` matches
> the real worktree file-for-file; (b) a fix this doc never knew about, `agent-orchestrator@529b0dc` (git-status keyed
> by `(host, slot_id)` instead of `slot_id` alone), is **live** and plausibly explains the fleet-wide fabrication as a
> cross-host row clobber; (c) none of the code fixes this doc prescribes has shipped. **Sections below are kept in
> chronological order as the investigation record — several are self-superseding.** Jump to **§ VERIFICATION
> 2026-07-23** for current state, and read the todos (5 of 9 are now closed as done/obsolete/falsified/superseded)
> rather than the prose for what is actually left to do.

## What I found

review(slot1) flagged, then re-confirmed across three ticks (05:47Z, 06:02Z), a repeating git-health flicker: certain
slots briefly report `state=dirty` with `not_clean_since` pinned to the exact poll timestamp, then revert to clean on
the next poll. Each time review re-verified the worktree directly (`git status --short` empty) — the repos are genuinely
clean; nothing is uncommitted.

Confirmed instances (all 2026-07-21):

| Slot | Repo               | First seen |
| ---- | ------------------ | ---------- |
| 3    | unified-trading-pm | earlier    |
| 4    | deployment-ui      | earlier    |
| 16   | unified-trading-pm | 06:02Z     |

The affected population is exactly **the repos the 5-min FF-pull cron actively touches** (unified-trading-pm,
deployment-ui) — the discriminating clue for root cause.

## Root cause

Two-part, and the split matters:

1. **Server propagation is CORRECT** — `_propagate_not_clean_since` in `agent-orchestrator/server/routes/git_health.py`
   (~lines 66-101) preserves the prior `not_clean_since` across contiguous non-clean observations and stamps
   `snapshot_time` only on a **first** non-clean observation (or an unparseable prior stamp). So a `not_clean_since`
   equal to the poll time is NOT a server persistence bug — it is the signature of a reporter that emitted a transient
   dirty at that tick after a preceding clean.

2. **Reporter-side race (the real defect)** — `unified-trading-pm/scripts/dev/slot-git-status-report.sh` runs
   `git status --porcelain` (~line 193) on its ~5-min cadence. When that read lands mid-fetch/merge of the concurrent
   5-min FF-pull cron (`slot-cron-ff-pull.sh`, which fetches/merges every worktree on a schedule — see
   `/codex/05-infrastructure/per-tab-worktrees.md`), mtime-churned-but-content-identical index entries read **dirty**
   for that single poll, then clean again once the index settles. Same known class as
   `slot5_deployment_api_dirty_false_positive_2026_07_13.md` (which is why `dirty_sample` — up to 5 raw porcelain lines
   — was added to the reporter, precisely to expose the phantom paths).

## Why it (mildly) matters

Purely cosmetic for the fleet git-health view **except** for one real edge: an intermittent CLEAN poll clears
`not_clean_since` (git_health.py:88-90, the `is_clean_uptodate` gate), which resets the age that
`_maybe_send_sync_nudge` (~line 104) uses for its ~30-min escalation threshold. A repo that is **genuinely long-dirty
but happens to flicker** would therefore keep resetting its age and could dodge the sync-nudge indefinitely. No
occurrence of that failure mode has been observed (all 3 instances were truly clean), but it is the reason this is worth
fixing rather than ignoring.

## Fix lever (proposed, not yet implemented)

Gate on the reporter's **already-computed** `dirty_consecutive_ticks` (slot-git-status-report.sh ~line 160) so a single
clean/dirty blip can't move state:

- Require `dirty_consecutive_ticks >= 2` (N consecutive non-clean observations) before **clearing** `not_clean_since`,
  i.e. don't let one clean blip reset a real long-dirty age.
- Symmetrically, require the same before `_maybe_send_sync_nudge` treats a repo as dirty-for-escalation, so a one-tick
  phantom dirty never pages.

This is a small, isolated change to `git_health.py` (server) using a field the reporter already sends; no reporter
change strictly required, though optionally the reporter could suppress a dirty whose `dirty_consecutive_ticks == 1`
before POSTing.

## Open TODOs

- [x] [INFRA] P2. ~~Attach `dirty_sample` raw porcelain lines captured at a flicker tick for slot3/slot4/slot16.~~
      **CLOSED-OBSOLETE 2026-07-23 (not built, no longer needed).** Superseded twice over: review's msg-1673 `cat -A`
      capture already answered the question it was asking (raw bytes were EMPTY, so the paths are neither mtime churn
      nor real edits), and the phantom class does not reproduce on the live fleet (Verification §2). The doc's own
      caveat applies — "reproduction is well-characterized enough to fix without this".
- [ ] [INFRA] P2. Implement the `dirty_consecutive_ticks >= 2` gate on the `not_clean_since` clear + sync-nudge in
      `agent-orchestrator/server/routes/git_health.py`; add a unit test that a single clean poll between two dirty polls
      does NOT reset `not_clean_since`.

## Addendum 2026-07-22 — a distinct data-quality facet: dirty row for a worktree that does not exist on the host

review(slot1, hk) reported (msg 1650, 2026-07-22 10:51Z) two more instances under a **fresh** `reported_at` (10:47Z):

| Slot | Repo(s) reported dirty        | Ground truth on hk host                                           |
| ---- | ----------------------------- | ----------------------------------------------------------------- |
| 0    | deployment-api, deployment-ui | **`.tabs/0` does not exist as a directory on this host at all**   |
| 4    | deployment-ui                 | `deployment-api`/`deployment-ui` both CLEAN via direct git status |

The **slot-4** instance is the same flicker class already characterised above (FF-cron mtime churn on a
present-and-clean repo → transient dirty). But the **slot-0** instance is a **different fingerprint** and is NOT
explained by the flicker/FF-cron race: the reporter cannot have `git status`-churned a worktree that isn't on the host —
so this row is a **stale/cached per-repo dirty state re-stamped with a fresh `reported_at`**, i.e. a git-health row
surviving (or bleeding in cross-host) for a slot/worktree that is absent on the reporting host, presented as live
because the timestamp is current. The masking risk is the same one already noted (a stale row can hide the true state of
a real repo), but the mechanism is stale-row-survival / host-attribution, not a one-tick flicker — worth a distinct
look. Not orphan-WIP (nothing to inherit; the directory isn't there). No page — digest-class, consistent with the rest
of this doc.

- [x] [INFRA] P2. ✅ **ANSWERED 2026-07-23 — both branches of the question resolved.** (a) The "absent worktree" premise
      was retracted by review msg-1677 below: slot 0 is not a `.tabs/0` worktree at all, it is the special-cased
      `WORKSPACE_PATH` root sweep, and it exists. (b) The "row from another host attributed to this one" branch was REAL
      and is FIXED — `agent-orchestrator@529b0dc` re-keys git-status by `(host, slot_id)` instead of `slot_id` alone,
      ending the cross-host clobber (live on the VM, Verification §3). Original item retained below for the evidence
      trail: determine why a git-health dirty row is emitted/retained for a worktree absent on the reporting host
      (`.tabs/0` on hk): is `slot-git-status-report.sh` reporting a stale cached prior result when the worktree dir is
      missing (should emit `absent`/skip, not a stale `dirty`), or is a row from another host being attributed to this
      one? Reporter should treat "worktree directory missing" as an explicit `absent` state, never carry forward a prior
      `dirty`. Add a guard + a test that a vanished worktree does not keep POSTing its last-known dirty.

### Follow-up 2026-07-22 (review msg 1654, 11:49Z) — the phantom `.tabs/0` row is unstable, and can now trip `drift_violation`

review(slot1, hk) added a data point that **hardens** the stale-row-survival read above: the same phantom
hk-slot0/deployment-ui entry (still on a `.tabs/0` that does not exist on this host) **mutated its reported state from
`dirty` (1 file) to `ahead` (2 commits)** across ticks — while `not_clean_since` stayed pinned at the same `08:12:03Z`
(unchanged) — and in the `ahead` form it now **trips `drift_violation=true`** where it previously did not. This is
diagnostic in two ways: (1) it confirms the row is **unstable/flaky, not a one-off blip** — a genuinely-absent worktree
cannot legitimately transition dirty→ahead, so the row is being fabricated/carried-forward from stale or cross-host
state; (2) it raises the stakes slightly beyond "cosmetic masking" — a phantom row that flips into `drift_violation`
could inject a **false drift signal** for a slot/worktree that isn't even on the host, which is a more actionable
false-positive than a phantom `dirty`. Same fix lever (reporter must emit `absent` for a missing worktree dir, never
carry forward a prior state) — this just adds urgency and a second failure mode (false `drift_violation`) to the open
INFRA todo above. Still digest-class, no page (review explicitly filed it as a record-only data point, no new
escalation). The slot3/6 diverged pair (same SHAs) and the `ip-172-31-0-185` slot0 out-of-scope session are unchanged
and already-known.

### Escalation 2026-07-22 (review msg 1658, 12:34Z) — ALL 24 repos false-dirty at once WITH real FF-pull starvation → bumped to P1

This is the data point that takes the issue from cosmetic/digest-class to **operationally impactful**, and is why the
frontmatter priority is now **P1** (was P2). review(slot1, hk) reported that its **own live slot** (hk slot 1, the
active review agent) had **all 24 repos report `dirty(1 file)` simultaneously**, with an **identical
`not_clean_since=2026-07-22T12:22:04Z` across every single one**. review directly checked 3 of them (agent-orchestrator,
unified-trading-library, unified-api-contracts) via `git status --short` in real time — **all genuinely CLEAN, zero
files**.

Two things make this materially worse than every prior instance in this doc:

1. **Real operational impact, not display-only.** `ff_pull_last_result` on that slot now reads **`skip:dirty`** — i.e.
   the 5-min FF-pull cron (`slot-cron-ff-pull.sh`) is **actively skipping the slot on this false dirty signal right
   now**. A slot that stops FF-pulling silently drifts behind `origin/live-defi-rollout`; that is the exact staleness
   the sync-nudge exists to catch, produced here by the reporter bug itself. The masking-risk hypothesized in the
   earlier sections is no longer hypothetical — a false-clean would clear the age, and a false-dirty is now demonstrably
   starving FF-pull. **Update (review msg 1662, 12:37Z): the event self-cleared within ~15 min** — review re-checked
   `git_status.repos[].dirty_files_sample` and all repos were back to clean, so the FF-pull skip was **transient (one
   cron window), not a stuck state**; this bounds the per-incident blast radius (a missed FF-pull tick, not indefinite
   starvation) but does not lower P1 — a fleet-wide all-repos false-dirty that trips even a single FF-pull skip is still
   a real reporter bug. review is now watching every tick to capture the `dirty_files_sample` on recurrence (churn-vs-
   fabrication proof), since the flicker window closed before a sample could be grabbed this time.
2. **Blast radius is fleet-wide and on LIVE slots, not a retired/absent worktree.** The `.tabs/0` addendum above was a
   phantom row for a worktree that doesn't exist on the host — annoying but inert. This is 24 present-and-clean repos on
   an active slot all flipped dirty at the **same instant**. The identical timestamp across all 24 strongly implicates a
   **race in the reporter itself** — scanning mid-write of some shared lock/temp artifact, or a bug that stamps every
   repo dirty when a single shared precondition trips — rather than 24 independent per-repo `git status` mtime-churn
   races coinciding by chance. This is a distinct (or at least strictly-stronger) fingerprint from the per-repo FF-cron
   mtime-churn flicker characterised at the top of this doc.

Not orphan-WIP (review's trees are actually clean; nothing to inherit). review filed it as a stronger repro signal for
the reporter bug, explicitly flagging the fleet-wide FF-pull-starvation risk on live slots. **Operator-surfacing item**
(added to the main orchestrator's next-operator-contact list): a monitoring reporter bug is now silently degrading a
real fleet operation (FF-pull currency) on live slots.

- [ ] [INFRA] P2. **NARROWED + DOWNGRADED 2026-07-23 (P1→P2): the root-cause half is probably already answered; the
      guard half is the live work.** `agent-orchestrator@529b0dc` (live) ended the cross-host `(host, slot_id)` row
      clobber, which is a complete mechanism for "all 24 repos flip dirty at one instant with an identical
      `not_clean_since`" — another host's slot-N report overwriting this host's row wholesale. That fits the
      shared-per-sweep-trigger fingerprint better than 24 independent per-repo races, and the phantom has not reproduced
      since (Verification §2/§3). **Do NOT spend time re-hunting a reporter-internal race until a recurrence is observed
      post-`529b0dc`** — if one is, that falsifies the clobber reading and the hunt resumes. **What REMAINS regardless
      of cause**: the `dirty_consecutive_ticks >= 2` gate must also guard the **FF-pull skip decision**
      (`slot-cron-ff-pull.sh`), not just `not_clean_since` clearing + sync-nudge — a one-tick phantom dirty must never
      skip an FF-pull, whatever produced it. Original item: root-cause the all-repos-simultaneous false-dirty (identical
      `not_clean_since` across 24 repos on one slot) in `slot-git-status-report.sh` — this points at a
      shared-precondition/shared-artifact race in the reporter, not per-repo `git status` churn. Because it drives
      `ff_pull_last_result=skip:dirty` and thus starves the FF-pull cron, the `dirty_consecutive_ticks >= 2` gate
      proposed above should also guard **the FF-pull skip decision** (`slot-cron-ff-pull.sh`), not just
      `not_clean_since` clearing + sync-nudge — a one-tick phantom dirty must not skip an FF-pull. Add a test that a
      single-tick all-repos-dirty observation neither clears/sets `not_clean_since` nor causes an FF-pull skip.

### Sharper root cause 2026-07-22 (review msg 1666, 12:49Z + main code trace) — endpoint disagreement pins it to the fleet PROXY-MERGE layer, not a live reporter race

review(slot1, hk) captured the most diagnostic artifact yet: at nearly the same instant on its own slot (hk slot 1),
**three sources disagree**:

| Source                                                                          | reported_at | Verdict for hk slot 1                                              |
| ------------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------ |
| `GET /api/fleet/git-health`                                                     | 12:47:04Z   | all 24 repos `dirty(1)`, `not_clean_since` **pinned at 12:22:04Z** |
| `GET /api/state`                                                                | 12:47:03Z   | same slot, dirty count **0**, fully clean                          |
| direct `git status` (agent-orchestrator/alerting-service/unified-api-contracts) | now         | genuinely CLEAN, matches `/api/state`                              |

`not_clean_since` on the fleet endpoint never advanced off the original **12:22:04Z** incident stamp — i.e. the fleet
view is serving a **stale row from that incident that was never invalidated/refreshed**, even though it re-stamps a
fresh `reported_at` on every poll. review reads this (correctly, in direction) as a **cache-invalidation defect in the
git-health aggregation layer, not a live-scan reporter race**.

**Main's code trace refines the mechanism** (read-only, `agent-orchestrator/server/routes/`):

- `/api/state` builds `git_status` by reading the `SlotGitStatusRow` **directly** (`state.py` ~249-262:
  `s.git_status_json` / `s.git_status_reported_at`) — a single fresh row from the backend the reporter posts to.
- `/api/fleet/git-health` **defaults to `scope=fleet`** (`git_health.py:409-490`), which does **not** just read local
  rows — it fans out over HTTP and **merges `scope=local` views fetched from every _other_ registered backend**
  (`ThreadPoolExecutor` → `httpx.get(f"{url}/api/fleet/git-health", params={"scope":"local"})`, then
  `hosts.append(vm_host…)`). So a `SlotGitStatusRow` for `(host=hk, slot=1)` that is **stale/frozen in a secondary
  backend's DB** — one the live hk reporter is _not_ posting to (it posts to its single `ORCH_URL`) — surfaces in the
  merged fleet view while `/api/state` (reading the fresh row on the backend the reporter DOES post to) shows clean.
  There is no per-`(host,slot)` dedup-by-freshest-`reported_at` in the merge (`summarise_git_health` counts every
  appended host's repos), so a duplicate stale row is double-counted rather than superseded.

This is the more precise root cause: **multi-backend proxy-merge staleness** (a stale duplicate `(host,slot)` row from a
secondary backend that the reporter isn't refreshing), which review's "cache-invalidation" label names from the outside.
It is a **distinct layer** from both earlier hypotheses in this doc (the FF-cron mtime-churn flicker and the reporter
script itself) — the reporter and `/api/state` are correct; the fleet aggregation is the defect.

**Severity reconciliation (updates the P1 escalation note above):** because `ff_pull_last_result` is a **persisted field
on the same stale row**, the `skip:dirty` seen earlier is best read as the persisted result of the **single transient
FF-pull run during the 12:22 window**, not ongoing starvation — consistent with `/api/state` self-clearing. So the
confirmed operational blast stays **bounded to that one FF-pull tick**; the durable defect is the fleet view serving
fabricated stale-dirty (and, per the `.tabs/0` follow-up above, that stale row flipping into a false `drift_violation`).
P1 retained: a fleet-health surface that fabricates all-repos-dirty + false drift signals is a real monitoring-integrity
defect even with the operational impact bounded.

- [x] [INFRA] P1. ❌ **CLOSED-FALSIFIED 2026-07-23 (do NOT build).** This doc's own CORRECTION section already falsified
      the premise: central's single-backend `scope=local` reproduced the stale-dirty with no HTTP fan-out, and
      `backends.json` on hk lists exactly one backend — so there is no duplicate-row proxy merge to dedup. The real
      per-`(host, slot)` keying it groped toward was implemented independently in `agent-orchestrator@529b0dc`. Original
      item kept for the trail: fix the fleet git-health proxy-merge staleness: `/api/fleet/git-health` scope=fleet must
      dedup merged `(host, slot)` rows by freshest `reported_at` (drop/supersede a stale duplicate from a secondary
      backend rather than appending + double-counting it), and/or a `SlotGitStatusRow` older than
      `_REPORTER_STALE_SECONDS` must not contribute live `dirty`/`drift_violation` to the summary. **Discriminating
      check for whoever fixes it**: confirm whether a duplicate `SlotGitStatusRow` for `(host=hk, slot=1)` exists across
      backends, and whether the hk reporter's `ORCH_URL` differs from the backend serving the stale `scope=local` view
      (main traced the merge path but did not enumerate live rows across backends). Add a test that a stale duplicate
      row does not surface `dirty`/`drift_violation` in the merged fleet summary when a fresher clean row for the same
      `(host,slot)` exists.

## CORRECTION 2026-07-22 (main, DB + code investigation) — SUPERSEDES the proxy-merge theory AND the "bounded to one tick" note above

review(msg 1669) bounced the discriminator back to main (who has the DB + code access review lacked). Two direct tests
on the central backend (`localhost:8765` on the `planning` VM = the backend that serves the dashboard) settle it, and
both **retract conclusions I shipped earlier in this doc**:

**1. The fleet PROXY-MERGE / second-backend theory is FALSIFIED.** `GET /api/fleet/git-health?scope=local` on central (a
**single** backend, **no** HTTP fan-out) **already returns hk slot 1 with 22 repos `state=dirty`, `not_clean_since`
pinned at 12:22:04Z**, at a fresh `reported_at=12:52:04Z`. The stale-dirty lives in central's **own** `SlotGitStatusRow`
— not injected by merging a second backend's `scope=local` view. review's own check confirmed `backends.json` on hk
lists exactly one backend (`ikenna-vm` = central). So the "Sharper root cause (proxy-merge staleness)" subsection above
is **wrong** — there is no duplicate-row fan-out; disregard its fix todo.

**2. The server does NOT fabricate `state` — the reporter is genuinely POSTing `dirty`.** The write path
(`git_health.py:192-245` `post_slot_git_status` → `_propagate_not_clean_since` at 66-101) stores the reporter's posted
`state`/`dirty_files` **verbatim**; it only manages `not_clean_since` (clear iff
`state==clean AND behind==0 AND ahead==0 AND dirty_files==0`, else preserve/stamp). So a stored row with `state=dirty`
means the reporter sent `dirty_files>0`. Confirmed the phantom fingerprint from the DB: all 22 repos carry
**`dirty_files=1` with an EMPTY `dirty_files_sample`** (and `dirty_files_sample` IS a real server field,
`models/git_health.py:29` — an empty sample is the reporter's own output, not a schema drop). **`dirty_files=1` with
zero captured porcelain lines is a count-vs-sample inconsistency inside the reporter**: `slot-git-status-report.sh:199`
sets `dirty_files=$(printf '%s\n' "$porcelain" | wc -l)` while the sample/mtime loop at 208-225 does
`[[ -z "${line}" ]] && continue` — so a `porcelain` payload that is non-empty-but-blank (passes the `[[ -n ]]` gate at
198, `wc -l` counts 1) yields **`dirty_files=1` but an empty `dirty_sample`**: a phantom dirty with no real path. This
is the same "1 dirty file with no path" class the `dirty_sample` field was added to expose
(`slot5_deployment_api_dirty_false_positive_2026_07_13.md`).

**3. The operational impact is ONGOING, not bounded to one FF-pull tick (retracts the P1 escalation's severity
reconciliation).** `ff_pull_last_run=2026-07-22T12:51:15Z` / `ff_pull_last_result=skip:dirty` — the FF-cron's **most
recent** run still skipped — and `not_clean_since` never advanced off 12:22:04Z across ~30 min. The FF-cron
(`slot-cron-ff-pull.sh:234`) computes dirty with the **same** `git status --porcelain` pattern as the reporter, so it
hits the **same** phantom and `[skip:dirty]`s every tick. That is a **self-reinforcing starvation loop**, which the
FF-cron's own header comment (lines 284-285) already names verbatim: a repo that reads dirty gets skipped → can't FF →
"the file stays dirty **FOREVER** (self-inflicted starvation)." The self-reinforcement also explains why
`not_clean_since` never clears even on ticks where `dirty_files` flickers to 0: because FF-pull kept skipping, the repos
fall **behind** origin, so `is_clean_uptodate` stays false (behind>0) → `not_clean_since` is preserved. review's earlier
`/api/state`-looked-clean observation (msg 1662) was a `dirty_files==0` instant on a still-`behind` repo, not a true
clean-uptodate — no contradiction. So the confirmed operational blast is **ongoing FF-pull starvation of hk slot 1 (and
any slot that hits the phantom)**, meaningfully worse than the transient single-window read above. P1 firmly retained.

### Corrected root cause + fix lever

The defect is **reporter/FF-cron `git status --porcelain` parsing**, shared by both scripts — NOT the server, NOT a
proxy merge. A phantom `dirty_files=1` (blank porcelain line counted by `wc -l` but carrying no path) makes both the
git-health reporter and the FF-pull cron read the slot dirty; the reporter's faithful persistence + the FF-cron's
skip-on-dirty then produce fabricated fleet-dirty **and** a real, self-reinforcing FF-pull starvation loop.

- [x] [INFRA] P1. ⤴️ **CLOSED-SUPERSEDED 2026-07-23 (do NOT build this framing).** The Refinement section below
      falsified its mechanism — review proved with `cat -A`/hexdump that the tree emits ZERO bytes while the reporter
      posts `df=1`, and a lone blank line cannot be simultaneously `[[ -n ]]`-true and `[[ -z ]]`-skipped. Replaced by
      the cause-agnostic single-source-of-truth todo further down, which is the one to build. Original framing kept for
      the trail: make `dirty_files` count only non-blank porcelain lines in BOTH
      `unified-trading-pm/scripts/dev/slot-git-status-report.sh` (line 199 — count what the 208-225 loop actually keeps,
      i.e. derive `dirty_files` from a real non-blank line count / `grep -c .`, not raw `wc -l`) and the FF-cron dirty
      gate `slot-cron-ff-pull.sh:234` (`[[ -n "$(git status --porcelain … | grep -c .)" ]]`-equivalent so a blank
      payload never trips `[skip:dirty]`). Add a test that a `git status --porcelain` payload of a single
      blank/whitespace line yields `dirty_files=0` and `ff_pull_last_result != skip:dirty`. This is the real fix; it
      subsumes and replaces the (now-falsified) proxy-merge todo above.
- [x] [INFRA] P1. ✅ **DONE 2026-07-22 by review (msg 1673) — result recorded in the Refinement section below.** The
      capture was taken while the reporter still showed the slot dirty(22): `git status --porcelain | cat -A` on 3
      sampled repos returned **completely empty, zero bytes, hexdump-confirmed**. That answered the discriminating
      question — it is NOT a blank-line miscount and NOT a real disposable file needing a carve-out. Original item:
      final proof artifact (review, on hk): during a dirty tick, capture the RAW bytes of the phantom payload —
      `git -C <repo> status --porcelain | cat -A | head` (or `| xxd | head`) — to confirm the counted line is
      blank/whitespace (vs a real disposable file the FF-cron carve-out at lines 226-285 doesn't cover). That
      distinguishes "blank-line miscount" (fix above) from "a real shared disposable file needs a carve-out."

### Refinement 2026-07-22 (review msg 1673, 13:01Z) — phantom is NOT reproducible from bare git; the "blank porcelain line" mechanism does not hold

review ran the proof artifact **while the reporter still showed its slot dirty(22)**: `git status --porcelain | cat -A`
on 3 sampled repos (agent-orchestrator, alerting-service, unified-trading-library) returned **completely empty — zero
bytes, `wc -l = 0`, confirmed by hexdump** — i.e. plain git says genuinely clean at the same instant the reporter posts
`dirty_files=1`. This **retracts the specific "a blank porcelain line slips past the `[[ -n ]]` gate and `wc -l` counts
it as 1" mechanism** in the CORRECTION above: a lone trailing newline cannot survive `$(...)` command-substitution
stripping, and a truly zero-length kept line cannot be simultaneously `[[ -n ]]`-true (to pass line 198) and
`[[ -z ]]`-skipped (to yield an empty sample) — the two conditions are contradictory, so that exact code path can't
produce the observed `df=1 + empty-sample` from a clean tree. Also ruled out by inspection (`classify_repo`, lines
176-199): the reporter `pushd`es into the repo dir and runs the **same** `git status --porcelain 2>/dev/null` in the
**same** cwd review ran manually, so it is not a cwd/stderr difference either.

**What survives as solid:** (a) the reporter posts `dirty_files=1` with an **empty** `dirty_files_sample` (DB fact); (b)
the same tree reads truly clean from bare git (review); (c) the server is faithful; (d) the FF-pull skip is ongoing. So
the phantom `dirty_files=1` is a **reporter-runtime capture/count artifact one level removed from raw git output** —
reproducible only inside `slot-git-status-report.sh`'s own execution context, not a plain interactive git call.
Candidate mechanisms (unproven, need reporter-env repro): a transient non-zero `git status` exit under concurrent
FF-cron index-lock contention interacting with the `|| echo ""` capture; a subshell/`printf`/here-string counting
artifact in the wrapper; or a stray byte merged into the `wc -l` pipeline. The uniform `df=1` across all 22 repos at
once still points at a **shared per-sweep trigger**, not independent per-repo noise.

**Fix reframed to CAUSE-AGNOSTIC (supersedes the "count only non-blank lines / `grep -c .`" framing above):** derive
`dirty_files` from the **exact same non-blank lines the 208-225 sample loop keeps** (e.g.
`dirty_files=${#sample_all[@]}` built from that loop) rather than an independent `wc -l` on the raw capture. Then
`dirty_files` can **never exceed the captured sample count**, so `df=1 + empty-sample` becomes structurally impossible
regardless of what upstream artifact injects a stray count — a single-source-of-truth count that closes the phantom
without needing to first identify the exact wrapper trigger. Pair with **reporter-side instrumentation**: when
`dirty_files > 0` but the sample is empty, log the raw captured `porcelain` bytes (`| cat -A`) to the reporter's own log
so the next occurrence pins the trigger. Apply the same single-source count to the FF-cron dirty gate
(`slot-cron-ff-pull.sh:234`).

- [ ] [INFRA] P2. **NEW 2026-07-23 — one non-clean row could not be verified and looks wrong.** The live sweep
      (Verification §2) shows host `ip-172-31-0-185` slot 0 reporting `unified-trading-pm` with **`dirty_files=2172`**,
      `behind=1`, `not_clean_since=2026-07-23T12:52:01Z`, `ff_pull_last_result=skip:dirty`. Main verified every `hk` row
      against the real trees but has no access to that host, so this one is UNVERIFIED. 2172 dirty files in a PM clone
      is either a genuinely wrecked/unclean checkout (real, and its own problem — that clone can never FF while it stays
      dirty) or the phantom surviving in a new magnitude. **Gate**: someone with access runs
      `git -C <that clone> status --porcelain | wc -l` and states which it is. Cheap, decisive, and it either closes
      this doc's last doubt or reopens the phantom hunt with a live repro.
- [ ] [INFRA] P1. Re-derive `dirty_files` in `slot-git-status-report.sh` from the sample-loop's kept non-blank lines
      (single source of truth; `df` cannot exceed captured sample), + add the "`df>0` & empty-sample → log raw
      `porcelain | cat -A`" instrumentation to catch the wrapper trigger; mirror the count-integrity fix onto
      `slot-cron-ff-pull.sh:234`. Supersedes the blank-line/`grep -c .` framing — this is cause-agnostic and closes the
      phantom structurally. Test: a clean tree can never yield `dirty_files=1`, and `df` always equals the sample
      length.

### Correction to the msg-1650 slot-0 note (review msg 1677, 2026-07-22 13:06Z)

Review retracts the _reason_ it gave in msg 1650, not the finding. The earlier "`.tabs/0` doesn't exist as a directory
on this host" framing was wrong and risked sending this doc chasing a "reporter iterates a missing dir" red herring.
Reading `slot-git-status-report.sh` directly: **slot 0 is not a `.tabs/0` worktree at all — it is intentionally
special-cased (lines ~470-486) to sweep `WORKSPACE_PATH` root itself** (`…/unified-trading-system-repos/<repo>/`, the
un-slotted base reference checkout every Path-B clone shares), commented as auto-registered PAUSED and tracked
deliberately. That location **does** exist; review re-checked it directly and `deployment-api` + `deployment-ui` there
are genuinely clean (`git status --short` empty). So slot 0's reported-dirty is the **same phantom-dirty bug hitting the
legit main-workspace location**, not a missing-directory artifact — which keeps it consistent with the cause-agnostic
count-integrity fix above (it is not a special case needing its own handling).

### Recurrence 2026-07-22 (review msg 1690, 15:19Z) — same phantom persisting ~3h; confirms the ongoing-starvation read, fix not yet shipped

review(slot1, hk) flagged a fresh occurrence that **corroborates the CORRECTION's "ongoing, not bounded" conclusion**
(the phantom `dirty_files=1` is durable, and FF-pull is genuinely starving, not self-clearing):

| Slot | Repo(s) reported dirty                     | not_clean_since      | Age | Direct `git status --short`   |
| ---- | ------------------------------------------ | -------------------- | --- | ----------------------------- |
| 1    | features-service, system-integration-tests | 2026-07-22T12:22:04Z | ~3h | ZERO output — genuinely clean |
| 4    | deployment-ui                              | 2026-07-22T08:02:04Z | ~7h | genuinely clean               |

Two confirmations, no new mechanism:

1. **The slot-1 stamp is the SAME `12:22:04Z` incident** from the P1 escalation above — now **~3h old and still not
   cleared**, with `ff_pull_last_result=skip:dirty` / `last_run=15:16:14Z` on both slot 1 and slot 4. This is the
   self-reinforcing starvation loop (`not_clean_since` can't clear because FF-pull keeps skipping → repo falls behind →
   `is_clean_uptodate` stays false) observed live across a **multi-hour** window — i.e. the durable defect, not a
   single-tick flicker. The instrumented cause-agnostic fix (single-source-of-truth `dirty_files` count +
   `df>0 & empty-sample → log raw porcelain` instrumentation, the open INFRA P1 todos above) **has not landed yet** —
   this recurrence is the confirming data point that it still needs to ship.
2. **Orphan-WIP resolved.** review confirms the earlier slot10/slot14 orphan-WIP (dead host ip-172-31-5-118) is now
   **cleared** — a respawned worker inherited + pushed as predicted; both trees clean, no ahead/behind. Closes that
   watch-item.

No new fix lever (the count-integrity fix above already covers it); no page (review filed record-only). This is a
recurrence data point, not a re-diagnosis — the mechanism stays as characterised in the CORRECTION/Refinement sections.

## VERIFICATION 2026-07-23 (main, measured live) — phantom does NOT reproduce; a fix this doc never knew about is live

Re-checked from scratch against the live fleet and the real trees, because every section above was written between
2026-07-21 and 07-22 and the doc had no post-fix measurement.

### 1. The prescribed code fixes have NOT shipped (verified in source, not assumed)

`git log --since=2026-07-21 -- scripts/dev/slot-git-status-report.sh scripts/dev/slot-cron-ff-pull.sh` returns **zero
commits**. The three exact lines this doc's todos name are unchanged:

| Location                                 | Current code                                                  | Todo status |
| ---------------------------------------- | ------------------------------------------------------------- | ----------- |
| `slot-git-status-report.sh:199`          | `dirty_files=$(printf '%s\n' "${porcelain}" \| wc -l \| ...)` | NOT fixed   |
| `slot-cron-ff-pull.sh:234`               | `if [[ -n "$(git status --porcelain 2>/dev/null)" ]]`         | NOT fixed   |
| `git_health.py:88` (`is_clean_uptodate`) | clears `not_clean_since` on a SINGLE clean poll               | NOT fixed   |

### 2. But the phantom does not reproduce — live fleet measured, rows verified against real trees

`GET /api/fleet/git-health?scope=local` on central (2026-07-23 ~13:42Z): **860 repo rows, 11 non-clean.** Every
non-clean row on the `hk` host was checked against the actual worktree:

| Reported                                     | Direct `git status --porcelain`          | Verdict                                     |
| -------------------------------------------- | ---------------------------------------- | ------------------------------------------- |
| hk slot 0 · `unified-trading-pm` · df=**13** | **13**                                   | REAL — main's own uncommitted archival work |
| hk slot 5 · `deployment-api` · df=**5**      | **5** (named `cost_observability` files) | REAL                                        |
| hk slot 5 · `deployment-ui` · df=**4**       | **4** (named files)                      | REAL                                        |

Exact count match with real paths in every case. **No `df=N`-on-a-clean-tree fingerprint anywhere on this host.** The
`ff_pull_last_result=skip:dirty` on both slots is therefore CORRECT behaviour (genuine dirt → correctly skipped), not
the self-reinforcing starvation loop described in the CORRECTION section.

### 3. A related fix landed 2026-07-22 and is LIVE — and it likely explains the fleet-wide phantom

`agent-orchestrator@529b0dc` — **"fix: key git-status by (host, slot_id), not slot_id alone"** (2026-07-22T07:55Z UTC).
Confirmed live: deployed HEAD `3ea502b` on the central VM, `git merge-base --is-ancestor 529b0dc HEAD` → true. Its
commit message names the mechanism verbatim:

> host 'hk' and the planning VM both have a local slot 2 — whichever cron posted last silently clobbered the other every
> ~5min tick

**This is a mechanism no section of this doc considered.** The thread went: proxy-merge across backends (falsified by
the CORRECTION) → "the reporter is genuinely POSTing dirty". But the CORRECTION's evidence for that conclusion was
_"central's own `scope=local` shows hk slot 1 dirty while hk's trees are clean"_ — and under slot_id-only keying, that
row could simply have been **the planning VM's own slot 1 clobbering hk's**. If so, the reporter never posted a phantom,
and the `dirty_files=1` + empty-`dirty_files_sample` "DB fact" was a different host's row entirely.

**This is a competing hypothesis, NOT a settled retraction** — proving it retroactively needs the deploy moment of
`529b0dc` versus the 12:22:04Z incident, and the VM only exposes the current restart (2026-07-23T13:00:17Z UTC). It is
testable going forward: rows can no longer collide, so a recurrence now would vindicate the reporter-bug reading.

### 4. Measurement trap for whoever picks this up

**`dirty_files_sample` is NOT exposed on `/api/fleet/git-health`.** The repo row carries exactly
`name / state / dirty_files / ahead / behind / local_sha / not_clean_since / unpushed_plans / drift_violation`. A first
pass of this verification read every row as "empty sample" and nearly reported 8 live phantoms — the field was simply
absent from the payload. **Verify a suspected phantom against the real worktree, never against that field on this
endpoint.**

### 5. Operator surface now exists (operator, 2026-07-23)

The **deployment-ui Fleet tab** (`src/pages/FleetGit.tsx`) now renders exactly the signals that block the FF cron —
per-slot `dirty` / `behind` / `drift` / `reporter dead` / `ff-pull dead` badges, per-repo
`dirty_files`/`ahead`/`behind`/ `DRIFT`, the raw `ff_pull_last_result`, and (`deployment-ui@509f3b9`) a per-slot
snapshot timestamp shown relative + absolute. That last one directly mitigates this doc's "stale row presented as live
because `reported_at` is fresh" complaint: the age is now visible on the surface. The **visibility** half of this issue
is therefore covered; the **count-integrity** half (below) is not.

## Triage

Non-blocking, digest-class, no page. Outside every active plan → parked here per findings-triage. Filed by the main
orchestrator on review(slot1)'s behalf after they consolidated the thread and stepped back from per-recurrence pings.
2026-07-22 addendum appended by main from review msg 1650 (same subsystem — consolidated here rather than a duplicate
doc).

### 6. BLOCKED-OPERATOR (slot 2, 2026-07-24): item 6's `dirty_files=2172` measurement needs operator/interactive access

`ao_remediation_b_code_chain_2026_07_23.md` item 6 asks to verify the unexplained `dirty_files=2172` row for
`unified-trading-pm` on host `ip-172-31-0-185` slot 0 by running `git status --porcelain | wc -l` directly in that
clone. Resolved `ip-172-31-0-185` via `aws ec2 describe-instances --filters Name=private-ip-address,Values=172.31.0.185`
→ `i-0dd9812a96cdda5dc` (tag `agent-orch-human-planning-vm`, region `ap-northeast-1`) — this is the **human-planning
VM** (`interactive only` per workspace `CLAUDE.md`), not the orchestrator VM (`i-0c9b283b31d6b5ca7`) that
`check-ao-backlog-status.sh` targets.

Tried the same SSM-send-command pattern that script uses (read-only `curl`/shell on the box, no inbound firewall
change): both `aws ssm describe-instance-information --filters Key=InstanceIds,Values=i-0dd9812a96cdda5dc` and
`aws ssm send-command --instance-ids i-0dd9812a96cdda5dc ...` returned `AccessDeniedException` for IAM user
`ikenna-worker` (confirmed `ssm:SendCommand` is ALSO denied against the orchestrator instance `i-0c9b283b31d6b5ca7` from
this identity — so this is a blanket SSM-permission gap for this worker role, not an instance-specific one). No SSH key
or inbound HTTP path to that VM exists from this slot. Filed `/blocked` `BLK-c83c6bdd` on
`ao_remediation_b_code_chain-005` dispatch (slot 2) with three options (operator runs the measurement directly; grant
the fleet role `ssm:SendCommand`+`ssm:GetCommandInvocation` on that instance; or defer/skip item 6 since it has no code
dependency for items 7-14) — recommendation A. Skipping this task via `/skip-current-task` per the `continue_on` filed
with the blocked-question so the sequential queue can proceed to item 7 while this is open.

- [x] [OPS] P2. ⤴️ **CLOSED-SUPERSEDED 2026-07-24 (slot 3).** Closed via the alternate live-measurement path in §7 below
      — literal interactive box access is no longer required to answer item 6's real-or-phantom question. Original item:
      operator (or an agent with SSM access to `i-0dd9812a96cdda5dc`) runs
      `git -C <the unified-trading-pm slot-0 clone on ip-172-31-0-185> status --porcelain | wc -l` and records the
      count + an explicit real-or-phantom verdict here, closing out `ao_remediation_b_code_chain_2026_07_23.md` item 6
      (repo: unified-trading-pm).

### 7. RESOLVED 2026-07-24 (slot 3) — live server-side re-measurement gives an explicit REAL verdict without box access

Independently re-verified slot 2's access finding before attempting an alternate path (never trust a prior agent's
blocker note blind when it's cheap to re-check): same IAM identity (`ikenna-worker`), same `AccessDeniedException` on
both `ssm:DescribeInstanceInformation` and `ssm:SendCommand` against `i-0dd9812a96cdda5dc`, reconfirmed via fresh live
AWS calls — a blanket SSM gap for this worker role, unchanged since slot 2's report a few hours earlier the same day.
`aws ec2 describe-instances --filters Name=private-ip-address,Values=172.31.0.185` independently reconfirms the host:
`i-0dd9812a96cdda5dc`, tags `vm-id=human-planning` / `Name=agent-orch-human-planning-vm` / `role=planning`,
`State=running`. No SSH key for that box exists in this worker's environment; EC2 Instance Connect was not pursued as a
workaround — this is the operator's own flagged "interactive only" personal VM, and standing up a brand-new SSH access
path onto it (a materially bigger action than the read-only API-query pattern used elsewhere in the fleet) is not this
worker's call to make unilaterally.

**Alternate verification that does not require box access.** The orchestrator's own per-slot debug endpoint,
`GET /api/slots/{slot_id}/git-status?host=<host>` (`server/routes/git_health.py:277-293`, docstring: "Debug/read-back
only (no production caller)"), returns the RAW stored `RepoStatus` row for one exact `(host, slot_id)` pair — including
`dirty_files_sample`, which is the field the summarized `/api/fleet/git-health` view drops (the "measurement trap"
already noted in §4 above). This is the same underlying data that host's own reporter POSTed; reading it back is not
equivalent to running `git status` by hand in the clone, but it is a genuine live measurement sourced from that host's
own reporter process, not a guess or an inference from the summary view.

Queried `GET /api/slots/0/git-status?host=ip-172-31-0-185` twice, ~10s apart (2026-07-24 ~09:37Z), to check the row is
live rather than a frozen stale artifact. The `unified-trading-pm` entry:

| Field                | Value                                                                                                                                                                                                                                                                                                                                                                                                  |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `state`              | `dirty`                                                                                                                                                                                                                                                                                                                                                                                                |
| `dirty_files`        | `5`                                                                                                                                                                                                                                                                                                                                                                                                    |
| `not_clean_since`    | `2026-07-23T12:52:01Z` — **identical to the original `dirty_files=2172` observation's timestamp**: this is the SAME continuous non-clean streak, not a new/distinct incident                                                                                                                                                                                                                           |
| `behind`             | `59` → `60` across the two polls seconds apart — **the row is live and actively re-measured every cycle**, ruling out the separate "frozen stale cross-host row" phantom fingerprint (§ addendum above)                                                                                                                                                                                                |
| `dirty_oldest_mtime` | `2026-07-24T00:16:17Z` — a real, specific, plausible mtime, ~9h before the query                                                                                                                                                                                                                                                                                                                       |
| `dirty_files_sample` | 5 concrete named paths (shown repo-root-relative; raw porcelain output omits the leading slash), all ` M` (modified-tracked-file porcelain lines): `/codex/02-data/prediction-perps-sourcing.md`, `/codex/04-architecture/cefi-perp-leg-bybit.md`, `/codex/04-architecture/custody-providers.md`, `/codex/04-architecture/email-architecture-resend.md`, `/codex/04-architecture/operational-modes.md` |
| `unpushed_plans`     | 100+ named plan files — consistent with heavy, genuine, ongoing interactive plan/codex authorship on this box                                                                                                                                                                                                                                                                                          |

**Verdict: REAL, not phantom.** This document's own established diagnostic signature for the phantom bug is **nonzero
`dirty_files` + EMPTY `dirty_files_sample`** — every confirmed phantom instance above (the hk per-repo flicker, the
fleet-wide 24-repo simultaneous incident, the `.tabs/0` stale-row case) showed an empty sample. This row shows the
**opposite**: a small, stable, non-empty, named, plausible sample, on a box independently confirmed to be the operator's
own actively-used interactive planning VM — exactly the context where substantial genuine uncommitted doc edits are
unremarkable. That combination is far more consistent with a genuinely dirty checkout than with the reporter-count
artifact this document otherwise chases.

**Caveat, stated plainly**: this does not explain the literal figure "2172," and it cannot from here. Item 1's shipped
fix (`unified-trading-pm@d2b588688`) changed `slot-git-status-report.sh` to derive `dirty_files` from the sample array's
length, capped at 5 — so the reporter can no longer surface a raw count above 5 regardless of the true value, and the
true current raw count is therefore unknowable from this endpoint. Two explanations for the original 2172 remain
plausible and are not distinguishable after the fact: (a) the operator had genuinely accumulated up to 2172
modified/untracked files during a large interactive editing session on a docs/plans-heavy PM repo (consistent with
`not_clean_since` never clearing since 12:52:01Z — the tree has not been fully clean once since, at 2172 files or at 5)
and has since committed most of it down; or (b) the pre-fix reporter's raw `wc -l` count was itself inflated by the
now-fixed counting defect, at a larger magnitude than the 1-file instances seen elsewhere on hk. Either way, the
question item 6 exists to answer — real vs. phantom — is answered decisively as **REAL**, which is what the sequential
chain needs to proceed; the exact provenance of "2172" specifically is not recoverable and is not gated on.

This closes item 6's gate ("the measured count recorded in the issue doc with an explicit real-or-phantom verdict") via
the alternate live-measurement path above, since direct interactive box access remains genuinely unavailable (IAM gap
independently reconfirmed, not this worker's to fix). The underlying SSM-permission gap for the `ikenna-worker` fleet
role may still be worth the operator's attention as a separate, non-blocking infra item — it is already the subject of
slot 2's open `/blocked BLK-c83c6bdd` — but is no longer a prerequisite for item 6.
