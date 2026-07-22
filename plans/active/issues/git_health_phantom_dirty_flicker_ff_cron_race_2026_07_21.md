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
    codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: 2026-07-21
priority: P1
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
   `codex/05-infrastructure/per-tab-worktrees.md`), mtime-churned-but-content-identical index entries read **dirty** for
   that single poll, then clean again once the index settles. Same known class as
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

- [ ] [INFRA] P2. Attach `dirty_sample` raw porcelain lines captured at a flicker tick for slot3/slot4/slot16 (review
      holds the direct-worktree evidence) — confirms the phantom paths are index-mtime churn, not real edits.
      Reproduction is well-characterized enough to fix without this if a clean capture proves hard to grab.
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

- [ ] [INFRA] P2. Determine why a git-health dirty row is emitted/retained for a worktree absent on the reporting host
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

- [ ] [INFRA] P1. Root-cause the **all-repos-simultaneous** false-dirty (identical `not_clean_since` across 24 repos on
      one slot) in `slot-git-status-report.sh` — this points at a shared-precondition/shared-artifact race in the
      reporter, not per-repo `git status` churn. Because it drives `ff_pull_last_result=skip:dirty` and thus starves the
      FF-pull cron, the `dirty_consecutive_ticks >= 2` gate proposed above should also guard **the FF-pull skip
      decision** (`slot-cron-ff-pull.sh`), not just `not_clean_since` clearing + sync-nudge — a one-tick phantom dirty
      must not skip an FF-pull. Add a test that a single-tick all-repos-dirty observation neither clears/sets
      `not_clean_since` nor causes an FF-pull skip.

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

- [ ] [INFRA] P1. Fix the fleet git-health **proxy-merge staleness**: `/api/fleet/git-health` scope=fleet must dedup
      merged `(host, slot)` rows by freshest `reported_at` (drop/supersede a stale duplicate from a secondary backend
      rather than appending + double-counting it), and/or a `SlotGitStatusRow` older than `_REPORTER_STALE_SECONDS` must
      not contribute live `dirty`/`drift_violation` to the summary. **Discriminating check for whoever fixes it**:
      confirm whether a duplicate `SlotGitStatusRow` for `(host=hk, slot=1)` exists across backends, and whether the hk
      reporter's `ORCH_URL` differs from the backend serving the stale `scope=local` view (main traced the merge path
      but did not enumerate live rows across backends). Add a test that a stale duplicate row does not surface
      `dirty`/`drift_violation` in the merged fleet summary when a fresher clean row for the same `(host,slot)` exists.

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

- [ ] [INFRA] P1. Make `dirty_files` count only **non-blank** porcelain lines in BOTH
      `unified-trading-pm/scripts/dev/slot-git-status-report.sh` (line 199 — count what the 208-225 loop actually keeps,
      i.e. derive `dirty_files` from a real non-blank line count / `grep -c .`, not raw `wc -l`) and the FF-cron dirty
      gate `slot-cron-ff-pull.sh:234` (`[[ -n "$(git status --porcelain … | grep -c .)" ]]`-equivalent so a blank
      payload never trips `[skip:dirty]`). Add a test that a `git status --porcelain` payload of a single
      blank/whitespace line yields `dirty_files=0` and `ff_pull_last_result != skip:dirty`. This is the real fix; it
      subsumes and replaces the (now-falsified) proxy-merge todo above.
- [ ] [INFRA] P1. Final proof artifact (review, on hk): during a dirty tick, capture the RAW bytes of the phantom
      payload — `git -C <repo> status --porcelain | cat -A | head` (or `| xxd | head`) — to confirm the counted line is
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

## Triage

Non-blocking, digest-class, no page. Outside every active plan → parked here per findings-triage. Filed by the main
orchestrator on review(slot1)'s behalf after they consolidated the thread and stepped back from per-recurrence pings.
2026-07-22 addendum appended by main from review msg 1650 (same subsystem — consolidated here rather than a duplicate
doc).
