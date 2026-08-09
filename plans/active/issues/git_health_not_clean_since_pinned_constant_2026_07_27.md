---
doc_type: issue
title: Fleet git-health `not_clean_since` reads a pinned constant across churning repos/slots
summary: >-
  Across 4+ consecutive review-agent poll ticks (2026-07-27 15:41-16:29Z), every dirty repo reported by `GET
  /api/fleet/git-health` carried the SAME `not_clean_since` value (`2026-07-27T06:12:04Z`) even as the actual set of
  dirty (host, slot, repo) triples churned — different slots (0, 1, 3), different repos (agent-orchestrator,
  deployment-api, deployment-ui, unified-trading-pm, features-service), different file counts each tick.
  `dirty_oldest_mtime` on the same repos was either null or showed genuinely fresh mtimes (minutes old), confirming
  these were live/active edits, not long-abandoned WIP. This breaks the review agent's long-dirty-worktree diagnostic
  (`unified-trading-pm/agents/review.md` § 3d), which relies on `not_clean_since` age to distinguish a stuck/orphaned
  worktree from normal interactive editing — as observed, EVERY dirty repo reads as ~9h+ stale regardless of when it
  actually went dirty.
status: open
nature: issue
asset_group:
  [ao, meta] # corrected 2026-08-02 (/ag-closeout-audit cross-cutting, operator-ruled) -- `infrastructure` -> `ao`; the
  # defect is in agent-orchestrator's own `server/routes/git_health.py` fleet reporter (repos: [agent-orchestrator],
  # parent_epic: orchestrator_master), i.e. ao-tranche, not generic infrastructure. Left multi-value (`meta` kept as
  # ruled: substitution only), so it stays exempt from check_ag_closeout_linkage.py by construction.
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [git-health, fleet-monitoring, worktree-health, reporter-bug, review-agent]
related: []
created: 2026-07-27
author: unknown
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
assigned_role: backend_engineer
source: >-
  Discovered by the persistent review agent (agent_id agt-160e62, slot 2) during its standing poll loop while
  spot-checking `/api/fleet/git-health` for long-dirty worktrees per review.md § 3d. Root-caused in chat by main (agent
  agt-c7dd49, 2026-07-27T16:31Z): `_propagate_not_clean_since` in `server/routes/git_health.py` (near L74-118) stamps
  `not_clean_since = snapshot_time` only the first time a repo is observed non-clean for a given (host, slot) key
  (looked up via `ss.get_slot_git_status_row(session, host, slot_id)` at L237-238), and otherwise carries the prior
  stamp forward — this looks CORRECT in isolation. Main's triage: the shared-constant behavior across different
  slots/repos points upstream of this function, to either (a) the reporter cron (`slot-git-status-report.sh`) posting a
  fixed/non-refreshing `reported_at` instead of the real post-time, or (b) the fleet-aggregation view collapsing to one
  global snapshot's `reported_at` rather than surfacing the correct per-(host,slot) value. A third possibility not yet
  ruled out: the hysteresis gate in the same function (`_DIRTY_CONSECUTIVE_TICKS_CONFIRM_THRESHOLD`, requires a
  CONFIRMED clean streak before clearing `not_clean_since`) may be legitimately never clearing for repos that are being
  edited on-and-off all day since 06:12 — in which case the field is doing what its docstring says, just in a way that
  makes it useless for one-shot "did this go dirty just now vs hours ago" checks on actively-touched repos, and the fix
  may be exposing a separate per-observation "last dirty transition" alongside the confirmed-clean-gated
  `not_clean_since`, rather than a bug fix to the existing field.
resolved_by:
locked_by:
archive_exempt: true
context_scope:
  [
    agent-orchestrator/server/routes/git_health.py,
    scripts/dev/slot-git-status-report.sh,
    agents/review.md,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch3_2026_07_30.md,
  ]
drift_direction: advance-code
depends_on: []
---

# Fleet git-health `not_clean_since` reads a pinned constant across churning repos/slots

## What I found

Fleet-wide `not_clean_since` on `GET /api/fleet/git-health` read the identical timestamp (`2026-07-27T06:12:04Z`) for
every dirty repo across 4 consecutive review-loop ticks spanning ~50 minutes (15:41Z, 15:58Z, 16:14Z, 16:29Z), even
though:

- The set of dirty (slot, repo) pairs changed every tick (slot 0: agent-orchestrator/deployment-ui/deployment-api; slot
  1: unified-trading-pm; slot 3: deployment-ui/deployment-api).
- `dirty_files` counts on the same repo changed tick-to-tick (e.g. slot 0 `deployment-ui` went 5→3 files).
- `dirty_oldest_mtime`, when non-null, showed mtimes only minutes old (e.g. `2026-07-27T15:52:29Z` at the 15:58Z tick) —
  i.e. real, fresh edits.
- The fleet git-health reporter itself was NOT stale during this window (`reporter_stale: false`, `ff_pull_last_run`
  advancing each tick, `ff_pull_last_result: skip:dirty`/`dirty:unconfirmed`).

## Why it matters

The review agent's worktree-health watch (`unified-trading-pm/agents/review.md` § 3d) is specced to use
`not_clean_since` age (">~30 min") to flag a genuinely stuck/orphaned worktree vs normal in-progress editing. As
observed, this field cannot currently distinguish the two cases — every dirty repo reads as ~9h+ old regardless of
actual dirty-since time, which would either mass-false-positive (if taken at face value) or force every consumer to fall
back to `dirty_oldest_mtime` + manual file-churn cross-checking (the mitigation the review agent used this session).

## Recommended decision

Someone with access to the live AO backend (planning VM) and the reporter cron should:

1. Confirm whether `slot-git-status-report.sh` computes `reported_at`/dirty-transition freshly per post, or reuses a
   fixed/boot-time value.
2. Confirm the fleet-aggregation view (`GET /api/fleet/git-health`) surfaces the correct per-(host, slot, repo)
   `not_clean_since` rather than a single collapsed/global snapshot value.
3. Decide whether the existing hysteresis-gated `not_clean_since` should stay as-is (last confirmed-non-clean streak
   start) with a NEW separate "most recent dirty transition" field added for the stuck-vs-active diagnostic, or whether
   the hysteresis logic itself needs a bugfix so `not_clean_since` resets correctly across distinct editing sessions.

## Todos

- [x] ✅ [BACKEND] P3. Instrument or trace `slot-git-status-report.sh`'s `reported_at`/dirty-transition posting to
      confirm whether it sends a fresh timestamp per run or a fixed value (repo: agent-orchestrator). **Already
      tracked**: combined with the next item into one open `[BACKEND] P3` todo in
      `/plans/archive/2026_07/infra_satellite_ao_dispatch_batch3_2026_07_30.md` (line ~160, status: active, assigned_vm:
      planning) — that todo explicitly sources this doc's items #1+#2 by path. **Verdict: (i) REFUTED** — reporter sends
      a fresh `reported_at` per run (`NOW_ISO="$(date -u +%Y-%m-%dT%H:%M:%SZ)"`, `slot-git-status-report.sh` line 173,
      computed fresh at invocation; confirmed live: `reported_at` advanced 06:22:04Z → 06:27:03Z across two consecutive
      cron ticks). Closed 2026-08-07 by finalize twin todo 1 — sha re-verified. unified-trading-pm@594aea342.
- [x] ✅ [BACKEND] P3. Audit `GET /api/fleet/git-health`'s aggregation path to confirm it surfaces
      `SlotGitStatusRow`-scoped `not_clean_since` per (host, slot, repo) rather than any global/shared snapshot value
      (repo: agent-orchestrator). **Already tracked** — same
      `/plans/archive/2026_07/infra_satellite_ao_dispatch_batch3_2026_07_30.md` todo as the item above. **Verdict: (ii)
      REFUTED** — aggregation does NOT collapse to a global value; `SlotGitStatusRow` keyed by `(host, slot_id)`,
      `_propagate_not_clean_since` builds `prior_by_name` keyed by repo name; live snapshot simultaneously showed
      distinct `not_clean_since` values (`null`, `2026-08-07T06:17:03Z`, `2026-08-07T06:27:03Z`) across slots/repos on
      the same host — impossible under a collapsed-global path. Closed 2026-08-07 by finalize twin todo 1.
      unified-trading-pm@594aea342.
- [x] ✅ [BACKEND] P3. Based on the above, either fix the upstream timestamp source, or add a distinct "last observed
      dirty transition" field alongside the existing hysteresis-gated `not_clean_since` so worktree-health consumers
      (review.md § 3d) can reliably distinguish a fresh edit from a genuinely long-stuck worktree (repo:
      agent-orchestrator). **Recommendation (verdict (iii) confirmed, 2026-08-07):** the bugfix-the-existing-field
      branch is provably right — swap `slot-git-status-report.sh` line 198's forwarded host-wide
      `dirty_consecutive_ticks` aggregate for a per-repo lookup via the already-existing `_read_repo_dirty_ticks` (keyed
      by repo path in the same `/tmp/slot-cron-ff-pull.result.json`) so `_propagate_not_clean_since`'s confirm-gate is
      keyed to the same repo it is clearing/preserving, matching `ff_one()`'s own per-repo confirm-gate logic. No
      schema/field addition required. **Server half shipped 2026-08-08 (agent-orchestrator@5d6752b)**:
      `RepoStatus.dirty_consecutive_ticks` + `_propagate_not_clean_since` already prefer a per-repo value when present,
      falling back to the slot-level scalar otherwise — but that commit's own message named an outstanding companion
      reporter change ("new reporters (slot-git-status-report.sh companion change) include per-repo values") that was
      never done. **Closed 2026-08-09**: added `read_repo_dirty_ticks()` to `slot-git-status-report.sh` (mirrors
      `slot-cron-ff-pull.sh`'s `_read_repo_dirty_ticks`, same `FF_RESULT_FILE` + same `repo_key` convention — the repo
      clone's resolved `pwd` post-pushd, matching `ff_one()`'s own `repo_key`); `classify_repo()` now computes it per
      repo and emits it as a 12th TSV column in every return path; `post_snapshot()`'s payload builder threads it into
      each repo's JSON dict as `dirty_consecutive_ticks`, which the already-shipped server code consumes. Verified
      locally: built a synthetic FF-cron result file with a per-repo `repo_dirty_ticks` map, confirmed `classify_repo` +
      the payload builder correctly produce `2` for a repo present in the map, `0` for a repo absent from the map, and
      `0` when the result file itself is missing entirely — matching `_read_repo_dirty_ticks`'s own fallback semantics.
      `bash -n` + `shellcheck` clean (only pre-existing unrelated SC2015 infos). unified-trading-pm@07dbb2cb9b.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Doc's own 'Recommended
  decision' section frames the remaining step as a field-design choice (new field vs. hysteresis bugfix) — genuine
  judgment call, diagnostic todos feed directly into it.
- **na-eligibility-audit 2026-08-02** (autonomous, tranche `ao`): KEEP-NA, valid — 2026-07-30 verdict re-affirmed. In
  scope this run only because of the 2026-08-02 `asset_group` retag `infrastructure` → `ao` (`6ef14a71e`); body content
  unchanged. All 3 `[BACKEND] P3` todos are diagnostics feeding the doc's own unresolved field-design choice (keep the
  hysteresis-gated `not_clean_since` and ADD a separate "last observed dirty transition" field, vs. bugfix the existing
  field's reset semantics) — a genuine judgment call.
- **na-eligibility-audit 2026-08-03** (ao tranche): **KEEP-NA, valid — citation fix only, no reclassify.** In scope
  because the doc was edited since the 2026-08-02 marker (`context_scope` backfill). New finding this run: todos #1 and
  #2 (the two diagnostic instrument/audit tasks) are already duplicated — combined into one open `[BACKEND] P3` todo in
  `/plans/archive/2026_07/infra_satellite_ao_dispatch_batch3_2026_07_30.md` (status: active, assigned_vm: planning, line
  ~160), which explicitly sources this doc's items #1+#2 by path and states its own done-when as writing the verdict
  back into this doc's Progress Log. Added a citation on both items above pointing at that live tracker so a future
  dispatch pass doesn't duplicate the diagnostic work. Doc stays NA overall — todo #3 (the field-design fork) remains a
  genuine root-cause-contingent architecture decision, unchanged from every prior pass, and
  `infra_satellite_ao_dispatch_batch3_2026_07_30.md`'s own combined todo explicitly excludes that branch from its
  bounded scope too ("a code change only if the verdict is (i) or (ii)... NOT a schema/field addition").
- **context-scout 2026-08-03**: refreshed context_scope (4 entries — added
  `infra_satellite_ao_dispatch_batch3_2026_07_30.md`, the doc that now actually tracks todos #1+#2's diagnostic work per
  the 2026-08-03 na-eligibility-audit citation above).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.

- **2026-08-07 ROOT-CAUSE VERDICT (slot 10, `infra_satellite_ao_dispatch_batch3_2026_07_30.md` todo
  `infra_satellite_ao_dispatch_batch3-002`)**: Tested all three candidate mechanisms named in this doc's `source` field,
  hypothesis (iii) first per the batch3 todo's instruction.

  **(i) REFUTED — reporter posts a fresh `reported_at`, not a fixed/boot-time value.** `slot-git-status-report.sh`'s
  `NOW_ISO="$(date -u +%Y-%m-%dT%H:%M:%SZ)"` (line 173) is computed fresh at the top of every script invocation and
  threaded through to every repo's POST for that run. Confirmed live: slot 10's `reported_at` advanced 06:22:04Z →
  06:27:03Z across two consecutive cron ticks (~5 min apart, matching the cron cadence) during this session.

  **(ii) REFUTED — the fleet aggregation does NOT collapse to a global/shared snapshot value.** `SlotGitStatusRow` is
  keyed by `(host, slot_id)` and its JSON blob is a per-repo-name list (`git_health.py` `_propagate_not_clean_since`,
  line 74-119, builds `prior_by_name` keyed by repo name); `slot_to_git_health` (line 311-357) reads `not_clean_since`
  straight off each `RepoStatus`, no cross-slot/cross-repo collapsing anywhere in the path. Confirmed live: one
  `GET /api/fleet/git-health?scope=local` snapshot simultaneously showed DIFFERENT `not_clean_since` values across
  different repos/slots on the same host — `null`, `2026-08-07T04:42:03Z`, `2026-08-07T06:17:03Z`,
  `2026-08-07T06:27:03Z` — which a truly global/collapsed value could not produce.

  **(iii) CONFIRMED as the root-cause mechanism — but more precisely than "simply never clears": the confirm-gate is
  keyed to the WRONG scope (host-wide, not per-repo).** `_DIRTY_CONSECUTIVE_TICKS_CONFIRM_THRESHOLD` (git_health.py:71)
  gates `_propagate_not_clean_since`'s clear branch (line 106) on a single `dirty_consecutive_ticks` int the caller
  passes in. That int is NOT per-repo. Trace: `slot-cron-ff-pull.sh:163` — `FF_RESULT_FILE` defaults to ONE fixed path
  per HOST (`${TMPDIR:-/tmp}/slot-cron-ff-pull.result.json`), not namespaced per slot or repo — confirmed live on host
  `ip-172-31-5-118`: exactly one `/tmp/slot-cron-ff-pull.result.json` shared by every slot on that box (alongside
  per-repo `lockhash`/`last-run` marker files, which ARE namespaced — only the result file isn't). `_write_ff_result`
  (slot-cron-ff-pull.sh:259-338) computes ONE aggregate `dirty_consecutive_ticks` scalar per sweep: it increments only
  when the sweep's HOST-WIDE worst outcome is `skip:dirty`/`dirty:unconfirmed` (line 281-288), and resets to 0 on ANY
  other outcome (`ok`/`fail`/`conflict`) from ANY repo anywhere on the host — the file's own comment (line 205-212)
  states this is "deliberately NOT a per-repo counter for that consumer", even though a real per-repo counter
  (`repo_dirty_ticks`, line 229-254, `_read_repo_dirty_ticks`) already exists and IS what `ff_one()`'s own confirm-gate
  reads (line 608+) — the per-repo fix from `ao_remediation_b_code_chain_2026_07_23.md` item 5 was wired into ONE
  consumer (`ff_one()`'s own skip-dirty decision) and never into the OTHER (`slot-git-status-report.sh`'s cross-check
  forwarded to the server). `slot-git-status-report.sh:184-203` reads that same host-wide aggregate into
  `FF_DIRTY_CONSECUTIVE_TICKS` and forwards it as ONE scalar (`dirty_ticks`, line 440, `argv[6]`) for the ENTIRE slot's
  payload (line 449) — every repo in that one slot's POST shares the identical value. `git_health.py:244`
  (`post_slot_git_status`) passes that scalar straight into
  `_propagate_not_clean_since(..., dirty_consecutive_ticks=req.dirty_consecutive_ticks)`, so a SPECIFIC repo's own
  `not_clean_since` can only clear when the WHOLE HOST's aggregate reads below threshold — regardless of that repo's own
  dirty history.

  **Reproduction (live, this session, 2026-08-07)**: Read 1 (`GET /api/fleet/git-health?scope=local`,
  `reported_at=2026-08-07T06:22:04Z`) showed slot 10 (host `ip-172-31-5-118`)'s 9 repos (alerting-service,
  batch-live-reconciliation-service, client-reporting-api, deployment-api, execution-service, features-service,
  fund-administration-service, greeks-service, ibkr-gateway-infra, instruments-service) ALL in `state=ahead` with
  `not_clean_since` pinned identically at `2026-08-07T04:32:03Z`, despite each repo carrying an independent, distinct
  leftover unpushed commit (from an earlier session's interrupted CI-template rollout). Pushed/fixed all 9 locally
  (verified `ahead=0`/`dirty=0` directly via `git rev-list`/`git status`). Read 2 (next tick,
  `reported_at=2026-08-07T06:27:03Z`) showed all 9 correctly flipped to `state=clean`, `not_clean_since=null` — a
  genuine dirty→clean transition, correctly cleared. At that exact tick, `/tmp/slot-cron-ff-pull.result.json`'s
  `dirty_consecutive_ticks` read **0** because `ff_pull_last_result=conflict` that sweep (an UNRELATED repo elsewhere on
  the host hit a merge conflict, which per the reset logic above zeroes the WHOLE host's aggregate regardless of which
  repo conflicted) — the confirm-gate happened to pass for these 9 repos purely because of unrelated fleet activity, not
  because of anything about these repos specifically. Cross-check at the same tick: `slot 0`'s `unified-trading-pm` was
  genuinely still dirty (5 files) with `not_clean_since` correctly pinned at `2026-08-07T04:42:03Z` (continuously dirty
  since then — expected, not a symptom) — proving the mechanism CAN track a repo correctly, while the shared-aggregate
  wiring means a DIFFERENT repo's clear-eligibility is coupled to whatever's happening elsewhere on the host, not its
  own state. This explains the original 2026-07-27 report (an identical `not_clean_since` pinned across many different
  actively-churning repos/slots for ~50 minutes): whenever the host-wide aggregate happens to stay ≥2 for a stretch (no
  repo anywhere hitting `ok`/`fail`/`conflict` in that window), EVERY repo on the host is blocked from clearing
  regardless of its own state — an unpredictable, racy coupling, not a permanent pin.

  **No code changed** — per the batch3 todo's explicit scope guard ("a code change only if the verdict is (i) or (ii)...
  NOT a schema/field addition"), a verdict of (iii) stays a recommendation only. **Recommendation**: swap the reporter's
  forwarded `dirty_consecutive_ticks` (host-wide aggregate, `slot-git-status-report.sh:198`) for a per-repo lookup via
  the already-existing `_read_repo_dirty_ticks` (keyed by repo path, same result-file JSON) so
  `_propagate_not_clean_since`'s confirm-gate is keyed to the SAME repo it's clearing/preserving — this is the
  bugfix-the-existing-field branch of todo #3's field-design fork below, which stays out of this todo's scope.

- **na-eligibility-audit 2026-08-07** (ao tranche, batch3of3): KEEP-NA, valid — doc stays NA overall (todos #1/#2 above
  closed today with commit evidence, `unified-trading-pm@594aea342`). **Flagging for the orchestrator's own
  conflict-check, not reclassifying myself**: the sole remaining open item (`[BACKEND] P3`, line ~117) no longer reads
  as an unresolved design fork — today's own root-cause section resolves verdict (iii) as CONFIRMED with a specific,
  bounded fix already named (swap `slot-git-status-report.sh`'s forwarded host-wide `dirty_consecutive_ticks` for the
  already-existing per-repo `_read_repo_dirty_ticks` lookup, no schema/field addition needed) — this looks like it
  crossed from "genuine judgment call between 2 design options" into "bounded, worker-determinable code fix with the
  exact target lines already identified," i.e. a candidate for RECLASSIFY on a future pass. Not flipping `assigned_vm`
  myself (needs the standing corpus conflict-check).

- **na-eligibility-audit 2026-08-08 (Phase 2/3, sub-agent conflict-check + apply)**: **RECLASSIFY, applied.**
  Re-verified the whole-doc bar independently: the sole remaining open item is now a fully bounded code fix with exact
  target lines already identified (per the 2026-08-07 root-cause section above) — no design/judgment call left
  undecided, clears `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope
  eligibility". Ran the shared conflict-check protocol
  (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3): grepped every `status: active`,
  `assigned_vm: planning` doc under `parent_epic: orchestrator_master` (and corpus-wide) for
  `dirty_consecutive_ticks`/`_read_repo_dirty_ticks`/`slot-git-status-report.sh` — zero overlap found.
  `infra_satellite_ao_dispatch_batch3_2026_07_30.md`'s own combined todo (now archived, `unified-trading-pm@594aea342`)
  explicitly excluded this exact scope ("a code change only if the verdict is (i) or (ii)... NOT a schema/field
  addition"), so no live claim on this ground anywhere else in the corpus. Verdict: clear. Applied: `assigned_vm: NA` ->
  `planning`, `execution_scope: local-only` -> `orchestrator-agent`, added `assigned_role: backend_engineer` (matches
  the sole remaining todo's `[BACKEND]` tag; the field was previously absent). **No separate finalize-plan twin
  authored**: `scripts/quality_gates/check_finalize_plan_coverage.py::_find_violations` scans `plans/active/*.md` only
  (non-recursive `Path.glob("*.md")`), never `plans/active/issues/*.md` — confirmed by direct code read, and confirmed
  live by the ~110 other `assigned_vm: planning` issue docs already sitting in `plans/active/issues/` with no companion
  finalize-plan file anywhere in the corpus. This doc (`doc_type: issue`, lives in `plans/active/issues/`) is
  structurally outside that gate's scanned population, matching `task_template.md` §4's own single-todo/self-contained
  carve-out in spirit — archival will be handled directly (by whichever worker closes the sole remaining todo, or a
  future `/na-eligibility-audit`/`/archive-candidates-audit` pass) once it reaches zero open todos, same as every other
  `assigned_vm: planning` issue doc in this corpus.
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
- **2026-08-09 (slot 13, backend_engineer)**: Closed the sole remaining todo. Shipped the companion reporter-side change
  `agent-orchestrator@5d6752b`'s commit message named but never landed: `slot-git-status-report.sh` now computes +
  forwards each repo's own `dirty_consecutive_ticks` (via a new `read_repo_dirty_ticks()`, mirroring
  `slot-cron-ff-pull.sh`'s `_read_repo_dirty_ticks` on the same `FF_RESULT_FILE` + `repo_key` convention), which the
  already-shipped server-side `RepoStatus.dirty_consecutive_ticks` / `_propagate_not_clean_since` code consumes in
  preference to the host-wide aggregate. Verified locally against a synthetic FF-cron result file (present-in-map → 2,
  absent-from-map → 0, missing-result-file → 0). All todos now closed, doc unlocked — unified-trading-pm@07dbb2cb9b.
  Flip committed with `archive_exempt: true` per `check_archive_candidates.sh`'s sanctioned flip-then-mv bridge
  (`check_archive_candidates_only_mode_no_flip_then_mv_exemption_2026_08_09.md`) — a plain edit at this still-active
  path, per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`'s "never combine the checkbox flip
  with the `git mv` in one commit" rule. Archival move follows immediately as the next commit.
