---
doc_type: issue
title: Slot 11 — an external process silently `git reset`-discarded 2 committed local commits (UTL + UAC)
summary:
  During a normal /boot task on slot 11, two already-committed local commits (unified-trading-library@a0ef1d67,
  unified-api-contracts@164a3937) vanished from HEAD — git reflog shows "Reset to origin/live-defi-rollout" entries I
  did not issue myself. Both commits were recovered via `git cherry-pick` from reflog; no work was permanently lost this
  time, but the mechanism is unidentified and could silently destroy uncommitted OR committed agent work fleet-wide.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-library, unified-api-contracts]
scope: [engineer, admin]
tags: [git-safety, incident, slot-infrastructure, data-loss-risk]
related: [codex/05-infrastructure/per-tab-worktrees.md]
created: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
source: [utl_reuse_phase7_low_lint_tail_2026_07_13.md, slot-11 backend-engineer task]
resolved_by:
  - "agent-orchestrator@911036c4 — ROOT CAUSE FIXED: `heal_dead_slot_branch_quarantine()` force-realigned slot repos via
    `git checkout -B <base> origin/<base>`, silently discarding committed-but-unpushed local commits when
    `classify_maker_liveness()` was called with `recent_edit=False` hardcoded (a false-negative for a genuinely-live
    worker with a stale .agent-claim). Now `_MIN_AHEAD_COMMIT_AGE_SECONDS_FOR_REALIGN=900` (_branch_state.py:383,460)
    REFUSES to touch any stop-state repo whose HEAD commit is <15 min old, leaving it quarantined for a human page
    instead. Fleet blast radius was 63+ real commits across 8 repos / 10 slots over 3+ weeks."
  - "agent-orchestrator@5297819 — independent SECOND layer (detection, via the superseded sibling
    slot6_git_reset_dataloss_2026_07_13): `HeadBackwardCanary`, wired into server.py lifespan"
  - "DATA RECOVERED: the two named commits are STILL-LOST as literal SHAs (they were the discarded originals) but their
    CONTENT shipped under recovery SHAs — unified-trading-library@ff387620 and unified-api-contracts@e910e6df, both
    reachable on origin/live-defi-rollout with identical messages + matching author-dates. No permanent loss."
  - "VERIFIED 2026-07-17 by independent skeptical audit (data-loss class held to a STRICT bar: a hypothesised root cause
    would NOT have counted). Root cause IDENTIFIED CONCLUSIVELY by reading the live code path, both claimed unit tests
    exist and their assertions match the refuse/preserve-and-realign behaviour, and the canary is verifiably running."
locked_by:
drift_direction: advance-code
depends_on: []
---

# Slot 11 — an external process silently `git reset`-discarded 2 committed local commits

## What I found

While shipping `utl_reuse_phase7_low_lint_tail_2026_07_13.md` from slot 11, I committed locally (not yet pushed) in 5
repos. Roughly ~20-25 minutes later, when I went to inspect 2 of those repos again, the commits were GONE from `HEAD` —
replaced by whatever `origin/live-defi-rollout` pointed to at that moment. `git reflog` in both repos shows the smoking
gun:

```
unified-trading-library:
a90da8f6 HEAD@{0}: checkout: moving from live-defi-rollout to live-defi-rollout
a90da8f6 HEAD@{1}: branch: Reset to origin/live-defi-rollout
a0ef1d67 HEAD@{2}: commit: feat(risk): add leg_snapshot_builder ...   <- MY COMMIT, DISCARDED

unified-api-contracts:
48bfadff HEAD@{1}: checkout: moving from live-defi-rollout to live-defi-rollout
48bfadff HEAD@{2}: branch: Reset to origin/live-defi-rollout
164a3937 HEAD@{3}: commit: fix(registry): sanction execution-service's ...   <- MY COMMIT, DISCARDED
```

Both `HEAD@{1}`/`HEAD@{2}` reflog messages say **"branch: Reset to origin/live-defi-rollout"** — this is NOT a
`git merge --ff-only` (which I used everywhere else and which produces a `merge: Fast-forward` reflog line, visible
elsewhere in the same reflogs) and NOT anything I ran myself (I never issued `git reset` in either repo this session).
Something ELSE — running with write access to my slot's repo clones — reset the branch ref straight to
`origin/live-defi-rollout`, silently discarding my already-committed work. The working tree was ALSO hard-reset (my new
files were physically deleted from disk, not just un-committed), so this was a `git reset --hard` or equivalent, not a
soft/mixed reset.

3 sibling repos in the SAME slot, committed in the SAME session, around the SAME time, were **not** affected
(strategy-service, execution-service, system-integration-tests, unified-trading-pm all still had my commits at `HEAD`
when I checked). So this isn't a blanket per-slot wipe — it hit 2 of 7 touched repos, seemingly at random (or by some
criterion I haven't identified — possibly whichever repos a periodic per-slot ff-pull/drift-repair script touched during
the window my commits existed unpushed).

**Recovery**: both commits were fully recoverable via `git reflog` + `git cherry-pick` (git never garbage-collects
reachable-via-reflog commits within the default 90-day window), so in THIS case no work was permanently lost. But if the
same mechanism fires on a repo where the agent has already moved on (reflog entry ages out, or the agent force-cleans
reflog, or simply doesn't think to check), this would be **silent, permanent loss of committed work** fleet-wide, for
any slot, any repo, any time between commit and push.

## Why it matters

This is the exact failure mode `codex/05-infrastructure/per-tab-worktrees.md` + `CLAUDE.md` § "Multi-agent safety" warn
AGENTS not to inflict on each other ("never force-push", "never git reset --hard ... uncommitted work") — but here the
actor was NOT an agent following documented git discipline; it was something else with write access to a slot clone that
used `git reset` instead of `git merge --ff-only`/`git pull --rebase --autostash` (which the worker/RULES.md docs
mandate for agents). If this is the same "structural pre-spawn branch-state gate" or "slot-cron-ff-pull.sh" mechanism
CLAUDE.md references (`worktree_clean_check.check_slot_branch_state` — "repairs a stale upstream + FFs when behind and
QUARANTINES a detached/wrong-branch/diverged clone"), it may have a bug where it treats "local HEAD ahead of origin with
uncommitted-to-origin work" the same as "diverged" and "repairs" it via a destructive `reset --hard` instead of the
documented non-destructive path (which would refuse to FF and leave the commits alone, or quarantine the clone for a
human to look at).

## UPDATE (same session, ~40 min later) — recurring, accelerating, targets T0-shared-lib repos specifically

The reset struck **again** on the exact same 2 repos, 3 times total for unified-api-contracts, 2 for
unified-trading-library, **zero** times for the other 4 repos I touched in the same session (strategy-service,
execution-service, system-integration-tests, unified-trading-pm):

```
unified-api-contracts reflog (--date=iso):
  Reset #1: 2026-07-13 11:36:06
  Reset #2: 2026-07-13 12:01:07   (24m 61s after #1 — looked periodic)
  Reset #3: 2026-07-13 12:10:22   (9m 15s after #2 — NOT periodic; breaks the 25-min theory)

unified-trading-library reflog:
  Reset #1: 2026-07-13 11:36:08
  Reset #2: 2026-07-13 12:01:09   (25m 1s after #1 — matches UAC #1→#2 almost exactly)
```

Both repos' reset #1→#2 gap is ~25 minutes (suspiciously matching the documented 25-min stale-slot heartbeat threshold
from `worker.md` — "The server flags you stale after 25 min with no ping" — though I was sending regular heartbeats
throughout, so if this IS the same watchdog it must be tracking staleness per-REPO, not per-slot). But UAC's #2→#3 gap
(9m 15s) breaks a clean fixed-period theory.

**Working theory**: `unified-api-contracts` and `unified-trading-library` are the workspace's two canonical T0
shared-dependency repos (schemas + events — see CLAUDE.md "System map": `schemas→UAC`, `events→UTL`) — every other repo
in the fleet holds a path-dep / `--reference` clone pointing at them. A plausible culprit is a fleet-wide "keep T0 deps
in sync" background job that force-syncs these two specific repos to origin on some (possibly load- dependent, hence
irregular) interval, independent of any given slot's activity — which would explain why ONLY these 2 of 7 touched repos
are hit, repeatedly, at irregular intervals, regardless of my own heartbeat cadence.

**Mitigation applied this session**: raced each repo through QG + `quickmerge` as fast as possible after each recovery
to minimize the unpushed-commit exposure window; UTL shipped successfully at commit `ff387620` (safe on origin now). UAC
has been recovered a 3rd time (`ac361e26`) and is mid-race as of this update.

## UPDATE 2 (13:26 UTC) — 4th occurrence, now hits a 3rd repo, confirmed SIMULTANEOUS across repos

The reset fired again — this time on BOTH `unified-api-contracts` (reflog: `Reset to origin/live-defi-rollout` at
`2026-07-13 13:26:25`) AND `execution-service` (same event at `2026-07-13 13:26:23`) — **2 seconds apart**. This is no
longer explainable as independent per-repo timers; it's a single coordinated sweep that hit 2 (of my session's 6
touched) repos in the same instant. `execution-service` had NOT been hit in any prior occurrence — this is a 3rd
distinct repo now affected (UTL 2x, UAC 3x, execution-service 1x; strategy-service/system-integration-tests/
unified-trading-pm — 0x each).

**New data point — already-pushed repos are immune**: at the moment of this 4th reset, `unified-trading-library`,
`strategy-service`, `unified-trading-pm`, and `system-integration-tests` all had `HEAD == origin` (already shipped via
quickmerge/push) and were completely unaffected — only the 2 repos with LOCAL commits not yet on origin
(`unified-api-contracts`, `execution-service`) got reset. This confirms the mechanism's trigger condition is
specifically "local HEAD ahead of origin," not a blanket per-repo timer, and validates that racing each fix to `origin`
ASAP (as this session has been doing) is the correct mitigation until the root cause is fixed. Both commits recovered
again via `git cherry-pick` (`unified-api-contracts@1729c3de`, `execution-service@5eafbcc2`) — no permanent loss.

## Recommended decision

Operator/main to investigate what actually issued the `Reset to origin/live-defi-rollout` reflog entries (likely
candidates: a per-slot cron health-check / drift-repair script, or a respawn/restart routine that resets a clone
believed-idle back to origin before reassigning it). Once identified: the repair path for "ahead of origin" must NEVER
be a `reset --hard` — it should either no-op (agent is mid-task, has local commits to push) or, at most, `git stash` the
divergent state somewhere recoverable (never silently discard). Given this can destroy real work fleet-wide with no
operator visibility unless the affected agent happens to notice (as I did here), this is a P0 data-safety gap. The
"already-pushed repos are immune" data point above should make this quick to isolate — it's a health-check job that
scans SPECIFICALLY for `HEAD != origin` clones and resets them, evidently on some sub-hourly cadence with more than one
repo processed per sweep.

## UPDATE 3 (slot 15, 2026-07-13) — fleet-wide audit confirms this is NOT slot-11-isolated: 276 signature hits, 18 real commits still at risk

Ran the `[VERIFY]` todo below: wrote `scripts/dev/audit-fleet-reflog-resets.sh` (read-only; `git reflog show` +
`git merge-base --is-ancestor` only, never mutates any slot) and swept every repo clone in every `.tabs/<slot>/` (16
slots, ~24 repos each) for the same `"branch: Reset to origin/<branch>"` reflog signature immediately preceded by a
discarded `commit:`/`commit (amend):` entry. Result: **this bug is fleet-wide and ongoing, not a slot-11 one-off.**

**Raw counts:**

- **276 total signature hits** across the fleet (231 currently `AT_RISK_REFLOG_ONLY` — the discarded SHA is reachable
  from neither current `HEAD` nor `origin`, i.e. recoverable only via reflog and gone once that entry expires; 45
  `RECOVERED` — the content made it back via cherry-pick/re-commit, same as slot 11's own recovery).
- Of the 276, **213 are `chore(orphan-wip): inherited WIP from predecessor...` commits** — this is the liveness-gated
  dead-claim inherit flow (`CLAUDE.md` § "Multi-agent safety": "dead claim → inherit + commit"), so it may be a
  DIFFERENT, possibly-by-design commit-then-later-discard flow rather than the same bug — flagging for whoever owns todo
  1 to check specifically, since if it IS the same bug it would make this the dominant failure mode by far (3.4× the
  real-work count).
- **The remaining 63 hits are real `feat`/`fix`/`refactor`/`test`/`docs` commits — unambiguously the SAME bug as the
  original slot-11 report** (same discarded-then-reset signature, same "not a `merge: Fast-forward` line" tell). Of
  these 63: **18 are STILL `AT_RISK_REFLOG_ONLY` right now** (never recovered/repushed) and **45 already `RECOVERED`**
  (someone noticed and cherry-picked, or the same content landed via a later independent commit).

**Confirms the T0-shared-dep theory (todo 4 below) at fleet scale, not just slot 11's 2 repos:** of the 63 real-commit
hits, `unified-api-contracts` alone accounts for 29 across 8 different slots (2,3,4,5,6,7,8,11,16) and
`unified-trading-library` accounts for 10 across 6 slots (2,3,4,6,9,11,16). Every other repo hit (`deployment-service`,
`instruments-service`, `market-tick-data-service`, `strategy-service`, `execution-service`, `features-service`,
`market-data-processing-service`, `unified-trading-pm`) shows only 1–2 hits each, scattered across slots 3–14 —
consistent with UAC/UTL being specifically targeted (not a blanket per-slot timer) while the rest is lower-rate
background noise from the same or a related mechanism.

**Oldest occurrence found**: 2026-06-22 (slot 1, orphan-wip). **Oldest still-at-risk REAL commit**: 2026-06-29 (slot 5,
`unified-api-contracts@16ce6a71`, "docs(book-summary): correct 24 -> 25 column count..."). This has been happening for
at least 3 weeks before the slot-11 session that first surfaced it.

**The 18 currently-at-risk real commits** (slot / repo / sha / message — recoverable via
`git -C <slot-repo> cherry-pick <sha>` from that clone's own reflog, TODAY, before any reflog-expiry or gc window
closes):

| Slot | Repo                     | SHA                | Message                                                                                      |
| ---- | ------------------------ | ------------------ | -------------------------------------------------------------------------------------------- |
| 3    | deployment-service       | e5c5f89            | fix(manifest-reader): avoid gcs_bucket substring in comment tripping STEP 5.11               |
| 4    | unified-trading-pm       | 7031ee42f          | docs(plans): file issue — slot 4 craft-scope mismatch on UI task dispatch                    |
| 5    | instruments-service      | e70d9fae           | test(goldens): regenerate cefi expected-universe golden to 73 tuples                         |
| 5    | unified-api-contracts    | 16ce6a71           | docs(book-summary): correct 24 -> 25 column count + add group breakdown                      |
| 6    | instruments-service      | 0a34152a           | fix(writers): stamp data_type='instruments' at emission (not blank)                          |
| 6    | market-tick-data-service | b9cb1aa2           | feat(live): add BITFINEX-SPOT + BITFINEX-FUTURES WSFeedConnectors                            |
| 6    | unified-trading-pm       | 510be6e9a          | docs(plans): file issue for stale PM fastapi ceiling blocking all quickmerges                |
| 8    | instruments-service      | 0c466a97           | fix(scripts): rank manifest candidates by content freshness, not blob.updated                |
| 9    | instruments-service      | 8f15fd3c           | feat(instruments-service): wire enumerate_expected_universe to TOTAL_UNIVERSE_AXES SSOT (B2) |
| 9    | market-tick-data-service | 64512679           | feat(live): BETFAIR + 3 sub-variants WSFeedConnector scaffold (BLOCKED-CREDENTIALS)          |
| 10   | instruments-service      | f8724cdb           | fix(cicd): pass SETUPTOOLS_SCM_PRETEND_VERSION to docker build (P0b)                         |
| 10   | market-tick-data-service | fcf05dc6           | feat(live): register Phase-3.5 DeFi LST/perp/specialty canonical keys — gap-014              |
| 11   | execution-service        | d4f79262           | refactor(algo_library): import build_leg_snapshots from UTL directly                         |
| 11   | unified-api-contracts    | 7d4f250b, 164a3937 | fix(registry): sanction execution-service's tracked MTDS reader import                       |
| 11   | unified-trading-library  | 1bdbac06, a0ef1d67 | feat(risk): add leg_snapshot_builder as single SSOT (the original report's own commits)      |
| 12   | deployment-service       | 0b0848b            | feat(registry): persist the D.1 host-metrics rolling window on the registry entry            |

Note two of these (slot 11's UAC/UTL rows) are the SAME commits already described in this doc's original report and
UPDATE sections above — they show as still `AT_RISK_REFLOG_ONLY` here because slot 11's clone reflog now only has the
FIRST occurrence's SHA reachable via reflog (the later amended/re-recovered SHAs superseded it in that clone's own
history) — not a new loss, just the audit script surfacing the full chain. The other 16 rows are genuinely
newly-surfaced instances this audit found, unrelated to the original slot-11 session.

**Recommendation**: none of this changes the fix (todos 1/2/4 below) — it just proves the blast radius is fleet-wide and
3+ weeks old, raising urgency. The 18 at-risk real commits above are not yet lost (git's default unreachable-object
grace period is ~2 weeks past last reflog activity even without the 90-day reflog expiry), but each slot's own
agent/operator should decide whether to cherry-pick recover them before that window closes — left as a judgment call
per-repo rather than this audit force-recovering content into worktrees it doesn't own.

Diagnostic script (read-only, reusable for future audits until this is confirmed fixed):
`scripts/dev/audit-fleet-reflog-resets.sh` (plain text or `--json` output).

## UPDATE 5 (slot 9, 2026-07-13) — checked slot 9's 2 flagged rows: both false alarms, already re-shipped independently

Per the urgent liveness message routed to slot 9 (its 2 rows in the UPDATE 3 table above:
`instruments-service@8f15fd3c`, `market-tick-data-service@64512679`), checked both via `git merge-base --is-ancestor` +
content diff before cherry-picking:

- `instruments-service@8f15fd3c` ("wire enumerate_expected_universe to TOTAL_UNIVERSE_AXES SSOT B2", 2026-07-06): NOT
  reachable from HEAD/origin (confirmed at-risk in the reflog-only sense), but the identical feature was independently
  re-implemented and shipped the next day as `7ded5940` ("feat(enumerator): wire enumerate_expected_universe to UAC
  TOTAL_UNIVERSE_AXES SSOT", 2026-07-07) — reachable from current HEAD, same guard assertion already present in
  `scripts/enumerate_expected_universe.py`. No cherry-pick needed.
- `market-tick-data-service@64512679` ("BETFAIR + 3 sub-variants WSFeedConnector scaffold, BLOCKED-CREDENTIALS",
  2026-07-06): also not reachable, but the same 4-venue-key scaffold shipped as `2115f867` ("feat(mtds): BETFAIR + 3
  sub-variants BLOCKED-CREDENTIALS scaffold (gap-009)") — already promoted to `main`. No cherry-pick needed.

Both slot-9 rows in the "18 currently-at-risk" table can be downgraded to "superseded, safe to ignore" — supports the
UPDATE 4 finding that this is a real, ongoing bug, but also suggests at least some of the 18 at-risk rows may turn out
to be non-issues on inspection (the feature got re-built rather than genuinely lost) rather than needing cherry-pick
recovery. Did not touch the other 16 rows (not this slot's repos) — left as a judgment call per-repo per the existing
recommendation.

## UPDATE 6 (slot 10, 2026-07-13) — checked slot 10's 2 flagged rows: both false alarms, same re-shipped-next-day pattern

Per the urgent liveness message routed to slot 10 (its 2 rows in the UPDATE 3 table above:
`instruments-service@f8724cdb`, `market-tick-data-service@fcf05dc6`), checked both via `git merge-base --is-ancestor` +
content diff before cherry-picking — same protocol as slot 9's UPDATE 5:

- `instruments-service@f8724cdb` ("pass SETUPTOOLS_SCM_PRETEND_VERSION to docker build, P0b", 2026-06-27): NOT reachable
  from HEAD/origin (confirmed at-risk in the reflog-only sense), but the fix was independently re-implemented more
  completely — current `Dockerfile`/`cloudbuild.yaml` already wire `SETUPTOOLS_SCM_PRETEND_VERSION` (unsuffixed, full
  `ENV` export + `publish-wheel` step) vs. the discarded commit's narrower
  `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_INSTRUMENTS_SERVICE` (2-line `ARG`/`ENV` only). No cherry-pick needed — current
  version is a strict superset.
- `market-tick-data-service@fcf05dc6` ("register Phase-3.5 DeFi LST/perp/specialty canonical keys, gap-014",
  2026-07-06): also not reachable, but the identical 10-connector scaffold set shipped the next day as `a49c0828`
  ("feat(live): 10 DeFi LST + perp + specialty WSFeedConnector scaffolds, wsfeedconnector_phase35_gap-014") — same
  gap-014 reference, all 9 individual connector files + registration present at current HEAD (self-contained, no
  `_defi_scaffold_ws` shared-module dependency the discarded commit used), test coverage present as
  `test_defi_lst_perp_specialty_ws_scaffolds.py` (renamed from the discarded commit's
  `test_defi_lst_perp_specialty_registration.py`). No cherry-pick needed.

Both slot-10 rows can be downgraded to "superseded, safe to ignore" — 3rd data point (after slot 9's 2) supporting that
the "re-implemented the next day" pattern, not permanent loss, is the common outcome once a slot notices and re-does the
work rather than waiting on reflog recovery. Did not touch the other 14 rows (not this slot's repos).

## UPDATE 4 (slot 15, 2026-07-13 14:58 UTC) — the bug hit THIS AUDIT'S OWN COMMITS, live, mid-session — breaks the T0-only theory

Meta-finding, discovered while shipping UPDATE 3: the exact same session that ran the fleet-wide audit above (slot 15,
`unified-trading-pm`) got hit by the bug itself, in real time. Timeline from `unified-trading-pm`'s own reflog:

```
14:47:01 UTC  commit 57f7f1421 — feat(scripts): add fleet-wide reflog-reset audit script
14:47:20 UTC  commit 77e428477 — docs(plans): flip VERIFY todo — fleet-wide reflog audit (UPDATE 3 above)
14:53:59 UTC  branch: Reset to origin/live-defi-rollout   <- both commits above silently discarded, 6m39s later
```

Both commits were still unpushed at the moment of reset (mid-session, about to quickmerge). Recovered via
`git cherry-pick 57f7f1421 77e428477` from this same slot's own reflog (still fresh) — no content lost, but this is live
confirmation the mechanism is still firing as of this update, not a historical/stale artifact.

**This breaks the "T0-shared-dep-only" theory (todo 4 below) as the sole explanation**: `unified-trading-pm` is not
`unified-api-contracts` or `unified-trading-library` and has no `--reference` dependents elsewhere in the fleet — yet it
was hit within ~7 minutes of the commits landing. The common factor across every hit in UPDATE 3 and this one is
simpler: **local HEAD ahead of origin at the moment some periodic sweep runs** — `unified-trading-pm` just churns
commits fast enough (frequent `docs(plans):` flips + `merge origin/live-defi-rollout: Fast-forward` every ~5 min per
this slot's own reflog above) that the exposure window keeps getting hit too. UAC/UTL being disproportionately
represented in UPDATE 3 is more likely explained by "many slots hold local commits to these 2 repos at any given time"
(everyone touches shared schemas/events) than a UAC/UTL-specific targeting rule — todo 4 should verify the sweep's
selection criterion directly rather than assume repo-name targeting.

## UPDATE 7 (slot 11, 2026-07-13) — ROOT CAUSE FOUND: `git checkout -B <base> origin/<base>`, not `reset --hard`

Traced the exact call path per todo 1. **The mechanism is `heal_dead_slot_branch_quarantine()`**
(`agent-orchestrator/server/worktree_clean_check/_branch_state.py`) and the sibling orphan-wip realign in
`commit_and_push_dirty_repos()` (`_orphan.py`) — both invoked from the `autospawn.py` pre-spawn branch-state gate
(around line 1228: `elif slot_path.exists():` → dirty-state resolution → `check_slot_branch_state` → on a STOP state
(`diverged`/`wrong_branch`/`detached`) → `heal_dead_slot_branch_quarantine`).

**The literal command is `git checkout -B <base> origin/<base>` — NOT `git reset --hard`.** Both functions' own code
comments explicitly claimed this checkout form "does NOT emit the `reset: moving to origin/<base>` reflog signature the
audit-reflog guard pages on" (i.e. that it was reflog-silent, unlike `reset --hard`). **That claim is factually wrong.**
Verified empirically in an isolated sandbox repo:

```
$ git checkout -B main origin/main   # HEAD had 1 local unpushed commit
Reset branch 'main'
$ git reflog show HEAD | head -2
<sha> HEAD@{0}: checkout: moving from main to main
<sha> HEAD@{1}: branch: Reset to origin/main       <-- THE SMOKING-GUN SIGNATURE
```

`git checkout -B <branch> <start-point>` force-resets the branch ref via the same internal path as `git branch -f`,
which writes `branch: Reset to <start-point>` to the reflog — **byte-identical to the "branch: Reset to
origin/live-defi-rollout" string** this doc's original report, UPDATE 3's fleet audit, and
`scripts/dev/audit-fleet-reflog-resets.sh`'s own grep pattern (`"Reset to origin"`) all match on. (For contrast,
`git reset --hard origin/main` writes a _different_ message, `reset: moving to origin/main` — the devs who wrote the
"avoids the reflog signature" comment tested against that wrong string.) The working tree also gets hard-reset to match
origin (files change on disk) — matching the original report's "my new files were physically deleted" detail exactly.

**Why it could hit a genuinely LIVE, mid-task worker** (not just a truly-dead predecessor, which is what this path is
supposed to gate on): `heal_dead_slot_branch_quarantine` only realigns a repo when (a) it's in a STOP state
(`diverged`/`wrong_branch`/`detached` — a repo with local commits AND behind origin reads as `diverged`, which any slot
touching a heavily-shared repo like UAC/UTL/PM hits routinely just from concurrent peer pushes, not genuine divergence
needing a human) **and** (b) `classify_maker_liveness()` doesn't return `"live"`. That liveness call was invoked with
`recent_edit=False` **hardcoded** — unlike the sibling dirty-state resolver, which correctly passes
`recent_edit=_wcc.has_recent_dirty_mtime(...)`. Liveness then depends entirely on a `.agent-claim` file + a matching
live tmux session — two signals that are NOT the same thing as, and can drift out of sync with, the HTTP `/progress`
heartbeat an active worker (this worker!) actually sends every ~10 min per `worker.md`. A worker with a stale/missing
claim file — genuinely alive and heartbeating — gets classified `"dead"`/`"absent"` here regardless, and its diverged
repo (which may just have raced a concurrent peer push) gets realigned, discarding its fresh commit (recoverable only
via reflog, exactly as this incident describes).

**Fix shipped** (todo 2): added a second, independent, git-native liveness backstop that doesn't depend on the claim
file at all — `heal_dead_slot_branch_quarantine` now refuses to touch (no preserve push, no checkout — genuine no-op)
any stop-state repo whose HEAD commit is younger than `_MIN_AHEAD_COMMIT_AGE_SECONDS_FOR_REALIGN` (900s / 15 min,
configurable via the new `min_ahead_age_seconds` param). Below that age, the repo is left quarantined so the existing
`_alert_branch_quarantine` path pages a human instead of silently discarding a fresh commit. Also corrected both
functions' code comments (they no longer claim `checkout -B` is reflog-silent — it isn't). 2 new/updated unit tests in
`tests/test_dirty_state_resolution.py`: `test_heal_refuses_realign_of_a_recent_ahead_commit` (new — asserts a fresh
ahead commit is left completely untouched even when claim/tmux liveness says "dead") and
`test_heal_dead_diverged_slot_preserves_and_realigns` (updated to pass `min_ahead_age_seconds=0`, since its fabricated
commit is instantaneous — it's testing the preserve+realign path, not the new age guard). Full test file green: 31/31
passed. Shipped `agent-orchestrator@911036c4`, full `quality-gates.sh` green (sentinel `ad86172e`).

**Left for follow-up (not in this todo's scope)**: `_orphan.py`'s realign already has a real recency guard
(`has_recent_dirty_mtime`, mtime-based) so it's lower-risk than `_branch_state.py` was, but it inherits the same
underlying `checkout -B` reflog-signature fact — comment corrected there too, behavior unchanged (already reasonably
guarded). The claim-file/heartbeat desync itself (the root reason liveness can false-negative a live worker) is a
separate, deeper fix (tie `.agent-claim` refresh to the `/progress` heartbeat) not attempted here — the recent-commit
guard is a sufficient, narrowly-scoped backstop for the specific data-loss symptom this doc tracks.

## Todos

- [x] ✅ [INFRA] P0. Identify the process that produced the "branch: Reset to origin/live-defi-rollout" reflog entries
      on slot 11 (unified-trading-library + unified-api-contracts) around 2026-07-13 11:30-11:50 UTC — check
      slot-cron-ff-pull.sh, worktree_clean_check.check_slot_branch_state, and any respawn/idle-reclaim routine for a
      `git reset --hard origin/<branch>` (or equivalent) call path. (repo: agent-orchestrator or
      unified-trading-pm/scripts, whichever owns the mechanism) — DONE, see UPDATE 7 above:
      `heal_dead_slot_branch_quarantine()` / `_orphan.py`'s orphan-wip realign, both via
      `git checkout -B <base>     origin/<base>` (empirically confirmed to emit the exact "branch: Reset to
      origin/<base>" reflog signature, contradicting the code's own prior comment).
- [x] ✅ [INFRA] P0. Whatever the mechanism, change its behavior for a clone with local commits not on origin: refuse
      (no-op + log) rather than reset; only auto-repair a clone that is BOTH commit-less-ahead AND has no reflog entries
      newer than N minutes (genuinely idle), never one with fresh local commits. (repo: same as above) — DONE, see
      UPDATE 7 above: `_MIN_AHEAD_COMMIT_AGE_SECONDS_FOR_REALIGN = 900` (15 min) guard in
      `heal_dead_slot_branch_quarantine` (`agent-orchestrator/server/worktree_clean_check/_branch_state.py`), 2 tests,
      full suite green.
- [x] ✅ [VERIFY] P1. Audit other active slots for the same reflog signature ("Reset to origin/<branch>" with a
      discarded commit reachable only via reflog) to see how widespread this already is / has been. (repo:
      unified-trading-pm — a fleet-wide grep script) — unified-trading-pm@57f7f1421, script
      `scripts/dev/audit-fleet-reflog-resets.sh`, results in "UPDATE 3" above: 276 signature hits fleet-wide (16 slots),
      63 are real (non-orphan-wip) discarded commits across 10 slots / 8 repos, 18 still `AT_RISK_REFLOG_ONLY` as of
      this audit. Confirms this is NOT slot-11-isolated and has been ongoing since at least 2026-06-22.
- [x] ✅ [INFRA] P0. Check specifically for a "keep T0 shared-dep repos in sync" fleet job/cron targeting
      unified-api-contracts + unified-trading-library specifically (see UPDATE section — 3 hits on UAC, 2 on UTL, 0 on 4
      sibling repos touched in the same session) — if found, it MUST check for local-commits-ahead-of-origin before
      resetting, same fix as the other INFRA todos above. (repo: whichever owns fleet T0-sync tooling) — **DONE
      2026-07-13 (slot 11), NO DEDICATED T0-SYNC JOB EXISTS.** Grepped every `.py`/`.sh`/`.yml`/`.yaml` under
      `agent-orchestrator/server/`, `agent-orchestrator/scripts/`, and `unified-trading-pm/scripts/` for
      `unified-api-contracts`/`unified-trading-library` combined with `sync`/`cron`/`schedule` — every hit is unrelated
      (OpenAPI/UI-reference generation, capability-manifest sync, QG benchmarking), none touches git branch state for
      these 2 repos specifically. Explicitly checked `slot-cron-ff-pull.sh` (the one standing periodic git-branch cron
      in the workspace): its own header states "Never destructive. Never runs `merge     --no-ff`, never `rebase`, never
      `reset --hard`" and it explicitly **skips** ahead/diverged/dirty repos — applies uniformly to every repo, no
      T0-specific carve-out. **This confirms UPDATE 4's own finding (same issue doc, slot 15) rather than contradicting
      it**: the UAC/UTL bias in the original counts is NOT repo-name targeting — it's
      `heal_dead_slot_branch_quarantine`/`_orphan.py`'s realign (see UPDATE 7 above, todo 1) firing on ANY repo that
      happens to be `diverged` at the moment the pre-spawn gate runs, and UAC/UTL/PM simply diverge far more often than
      a session-scoped repo like `strategy-service` because so many concurrent slots hold local commits to the fleet's 2
      canonical shared-schema/event repos at any given time — a probability effect, not a targeting rule. No separate
      fix needed here beyond todo 2's guard (already shipped, covers every repo uniformly including UAC/UTL).

## Update 2026-07-13 (slot 8, heartbeat nudge — a much older AT_RISK_REFLOG_ONLY hit, still unrecovered)

A `/heartbeat` message flagged `instruments-service@0c466a97`
(`fix(scripts): rank manifest candidates by content freshness, not blob.updated`, authored by this same slot 8 on
2026-07-06) as still recoverable via reflog on this slot's clone — one of the 18 `AT_RISK_REFLOG_ONLY` hits from the
fleet-wide audit above, this one **7 days old** (oldest confirmed case so far, well past this doc's "~2 weeks" outer
estimate for the gc window — worth revisiting whether 90 days, the git default, is the real ceiling rather than
something shorter, since this one survived 7 days intact). Attempted `git cherry-pick 0c466a97` onto current HEAD: real
content conflicts in both changed files (`scripts/measure_honest_coverage.py`,
`tests/unit/test_measure_honest_coverage.py` — the function has legitimately evolved in the 7 days since), not a
mechanical fast-forward. Aborted the cherry-pick rather than force a rushed manual resolution — this specific recovery
needs a dedicated pass to reconcile the 2026-07-06 fix's logic (content-freshness-based PRIMARY ranking, `--pin-primary`
escape hatch) against whatever changed `measure_honest_coverage.py` since, not a mechanical `--theirs`/`--ours` pick.
Flagging as its own recoverable-but-stale data point (not re-running the fleet audit script again for one instance) — if
nobody claims this within the reflog window, the original bug-3 fix (`cefi_layer1_denominator_gaps` item 011) is lost
and would need to be re-derived from scratch rather than recovered.
