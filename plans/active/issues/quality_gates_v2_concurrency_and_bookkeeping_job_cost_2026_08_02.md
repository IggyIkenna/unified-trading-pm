---
doc_type: issue
title:
  quality-gates-v2 cancel-in-progress fixed for pull_request/workflow_dispatch (shipped); 3 fixed bookkeeping jobs still
  bill GitHub's 1-min floor on every run; PM promote-PR mechanism may have changed since ci-cd-flow.md was written
summary: >-
  A fresh CI-minutes sweep (2026-07-31/08-02) found quality-gates-v2's concurrency group only cancelled superseded
  `push` runs, never `pull_request`/`workflow_dispatch` ones — fixed and shipped (PM + fleet rollout in progress). Also
  measured: content-gate + the quality-gates-v2 aggregation job + record-qg-result bill GitHub's 1-minute floor on every
  run regardless of whether real gate work happens, ~129+ billed min/day on instruments-service alone — the largest
  single line item found, but NOT attempted as a direct edit here per this plan family's own "prove on ONE caller before
  fleet rollout" lesson (22+ callers key off these jobs' output names). Also surfaced: live quickmerge output for PM
  says its promote mechanism is now "frozen-per-SHA-ref" via a "churn fix, 2026-07-27", which appears to contradict
  codex/08-workflows/ci-cd-flow.md's still-live-branch-ref "PM Option-B standing LDR->main PR" description (codified
  2026-06-09) — flagging as a possible stale-SSOT, not verified further here.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, github-actions, cost, concurrency, quality-gates-v2, workflow-templates]
related: [/plans/active/github_actions_operator_gated_followups_2026_07_17.md, /codex/08-workflows/ci-cd-flow.md]
created: 2026-08-02
priority: P2
parent_epic: deployment_and_user_management_master
source:
  "Interactive session, operator asked for a CI-minutes cost breakdown + savings, then asked to ship the biggest safe
  ones. Companion plan (github_actions_operator_gated_followups_2026_07_17.md) is already at its 1000-line hard cap, so
  this new finding goes in its own issue doc per the findings-triage rule rather than pushing that plan over its line
  cap."
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
---

# quality-gates-v2 concurrency fix (shipped) + bookkeeping-job cost + a possible stale SSOT

## What shipped this session (2026-08-02)

- [x] ✅ **DONE — `quality-gates-v2`'s `concurrency.cancel-in-progress` extended from `push`-only to unconditional
      `true`.** Before: `cancel-in-progress: ${{ github.event_name == 'push' }}` — a `pull_request` or
      `workflow_dispatch` run that got superseded by a newer commit on the same ref queued to full completion instead of
      being cancelled, billing in full for nothing. The group is already scoped per-ref
      (`quality-gates-v2-${{ github.ref }}`; a PR's ref is `refs/pull/<n>/merge`, unique per PR), so cancelling
      in-progress here cannot cross-cancel a different PR or a push to main. Fixed in both PM's own caller
      (`.github/workflows/quality-gates-v2.yml`) and the fleet template
      (`scripts/workflow-templates/quality-gates-v2.yml.tmpl`). PM shipped:
      `unified-trading-pm@f55f9b11e6b04cd5c553d4c0f825398d0f7c3665` (QG 150s clean, 1611 passed/11 skipped). Fleet
      rollout (22 repos via `rollout-workflow-templates.sh --template quality-gates-v2.yml.tmpl` + per-repo
      `quality-gates.sh --no-fix` + `quickmerge.sh --agent --files`) — **in progress as this doc is filed; see this
      plan's Progress Log entry below (todo #2) for the per-repo result table once the sequential ship completes.** The
      2 UI repos (`unified-trading-system-ui`, `deployment-ui`) correctly skipped — they call a separate
      `ui-quality-gates-v2.yml`, untouched by this fix.
- [ ] [VERIFY] P3. **Re-measure PM's `quality-gates-v2` push/pull_request/workflow_dispatch run-mix + cancellation rate
      a few days after this lands**, the same way the companion plan's own "re-measure billed job-minutes before/after"
      VERIFY todo already calls for. Before this fix, PM measured 157 success / 12 failure / 31 cancelled over a 5-day
      window — but that 31 was ENTIRELY push-triggered (the only path with `cancel-in-progress:true` before today), so
      it's not a valid baseline for the pull_request-triggered cancellation rate this fix newly enables. Don't estimate
      a % savings without this — see the caveat given to the operator in-session: expect a real but unquantified win
      concentrated wherever a ref gets multiple `synchronize`/`workflow_dispatch` events before the gate finishes (PM's
      own promote mechanism if it's still a moving ref — see the open question below — and `ldr-ci-monitor.yml`'s hourly
      re-dispatch during host-contention episodes specifically), and near-zero on the 22 fleet repos' frozen-per-SHA
      promote PRs in steady state (each tick gets a fresh PR number = a fresh concurrency group, so there was nothing to
      collide with there to begin with).

## Open question — does PM's promote mechanism still match ci-cd-flow.md's "Option-B standing PR" description?

`codex/08-workflows/ci-cd-flow.md` (read 2026-07-31, lines 1-645 of 1231; "PM Option-B standing LDR→main PR" section,
"codified 2026-06-09") describes PM's `ldr-to-main-promote.yml` as opening a PR whose head is the **live branch ref**
`live-defi-rollout` itself (not a frozen SHA) — a "standing sweep" where every commit riding it before it merges shares
one concurrency group, which is exactly the queue-not-cancel pattern this fix targets and the reason PM was expected to
be the main beneficiary of today's fix.

But the live `quickmerge.sh --agent` output for PM, THIS session (2026-08-02), says:

```
[unified-trading-pm] Option B: lands on LDR trunk; ldr-to-main-promote.yml drains to main (v2 on that PR is the gate)
[unified-trading-pm] ✅ Landed on live-defi-rollout (LDR trunk). ldr-to-main-promote.yml drains PM→main
   (frozen-per-SHA-ref, ~15-30min SLA) — quickmerge no longer opens a direct PR here (churn fix, 2026-07-27).
```

"frozen-per-SHA-ref" is the SAME pattern the 24 fleet repos use (`ldr-to-main-promote-fleet.yml`), not the
live-branch-ref standing-sweep pattern the codex doc describes — and it's dated to a "churn fix" on 2026-07-27,
**after** the codex doc's cited "codified 2026-06-09" date. Two possibilities, not distinguished here: (a) PM's promoter
was migrated to frozen-per-SHA-ref on 2026-07-27 and `ci-cd-flow.md`'s Option-B section is now stale (needs an update +
banner), or (b) the quickmerge script's own log message is stale/misleading and PM's promoter still behaves as
documented. **Not verified further in this session** — this changes where the concurrency fix's benefit concentrates (if
PM is now also frozen-per-SHA-ref, its promote-PR gate runs are no more collision-prone than the fleet's, and the fix's
main value shrinks to the `ldr-ci-monitor.yml` hourly-dispatch-during-contention case for everyone alike, not a
PM-specific win).

- [x] ✅ [SCRIPT] P2. Read `unified-trading-pm/.github/workflows/ldr-to-main-promote.yml` directly (not the codex prose)
      to determine ground truth — does it still open one standing PR per LDR-ahead-of-main window (branch-ref head), or
      does it now create a `promote/unified-trading-pm/<shortsha>` frozen ref like the fleet promoter? If it changed,
      update `ci-cd-flow.md`'s "PM Option-B standing LDR→main PR" section (and the "Convergence + conflict-resolution
      model" / "Which repos squash vs. rebase on promote" table, which currently lists PM's own path as `--merge` not
      `--squash` — verify that claim too while in the file) to match, with a dated correction banner citing this issue
      doc, per the post-phase codex audit discipline. — **2026-08-02 (slot-15) — DONE.** Ground truth confirmed directly
      from the workflow's own source (not prose): it DOES now create a `promote/unified-trading-pm/<sha12>` immutable
      per-SHA ref, same pattern as the fleet bot — `git log -S "FROZEN HEAD"` pins the migration to
      `unified-trading-pm@40386f0274` (2026-07-18), 9 days BEFORE the "churn fix, 2026-07-27" date quickmerge's own log
      line credits (that later commit, `48800b7ad`, is a separate in-flight-validation-preemption refinement, not the
      frozen-head switch itself — both misattributions fixed). **Correction on the todo's own premise**: the
      squash/rebase table as found did NOT already say `--merge` — it said `--squash` (matching the fleet row, wrongly),
      directly contradicted by this same codex doc's own later "Scope note" at the silent-revert-loss section, which
      already correctly said `--merge`. Verified against the workflow's literal source: all 4 `gh pr merge` call sites
      use `--auto --merge --delete-branch`, never `--squash`. This is more than a wording fix — a real merge commit
      (unlike squash) keeps the frozen LDR sha as a genuine ancestor of `main`, so the table's "ancestor check is Never
      valid" verdict for PM's row was also substantively wrong; corrected to "Always valid" with the reasoning inline.
      Updated `codex/08-workflows/ci-cd-flow.md`: rewrote the "PM Option-B standing LDR→main PR" section (dated 🟡
      CORRECTED banner + the frozen-head model description + the old branch-ref model kept as explicit historical
      context, not deleted), fixed the stale "manual immediate drain" recipe (a `--head live-defi-rollout` PR would now
      be auto-closed by the bot's own bug#7 guard), fixed the CONTENT-verification note, and fixed the squash/rebase
      table row + its "Bottom line" paragraph. Also fixed the same misattribution in `scripts/quickmerge.sh`'s own
      comment + user-facing echo line (it credited the wrong commit/date for the frozen-head switch). Evidence:
      unified-trading-pm (this repo) — `codex/08-workflows/ci-cd-flow.md` + `scripts/quickmerge.sh`, this commit.

## Bookkeeping-job 1-minute-floor cost (measured, not yet actioned)

- [ ] [INFRA] P2. **`quality-gates-v2`'s 3 fixed bookkeeping jobs — `content-gate`, the aggregation job named
      `quality-gates-v2` (needs: `[content-gate, qg-slices]`), and `record-qg-result` (needs:
      `[qg-slices, supersede-check]`) — each bill GitHub's 1-minute-per-job floor on EVERY run, including a full
      content-sentinel HIT where no real gate work happens.** Measured live on instruments-service (2026-07-31): 43
      `quality-gates-v2` runs in a 19.3h sample ⇒ ≥129 billed min/day from this floor cost alone, on just 1 of 24 repos
      — the largest single aggregate line item found in this sweep, ahead of any individual repo's self-hosted-vs-hosted
      gap. `record-qg-result`'s own job (read in full this session,
      `.github/workflows/python-quality-gates-v2.yml:1159-1225`) does a live Firestore read-then-PATCH against
      `qg_last_conclusion/<repo>:<branch>` to drive the "QG Recovered" Slack notification — not the `ci_status`
      Firestore collection (`ci-status-update.yml` owns that separately), so it's lower-risk to fold than it first
      looked, but still a live external call whose exact ordering relative to other steps matters. **Do not attempt this
      as a single blind edit.** This exact plan family's own hard-won lesson applies directly
      (`github_actions_operator_gated_followups_2026_07_17.md`, "Composite-action manifest errors are NOT containable...
      Edit the manifest → prove on ONE caller → only then fan out — with 22 callers that is 22 simultaneous failures"):
      `content-gate`'s cache-key computation, its Firestore `qg_green_markers` CAS write/probe, and every one of the 22
      fleet repos' own `quality-gates-v2.yml` caller template has jobs (`escalate-ldr-qg-failure`,
      `dispatch-cloud-build` x2, `notify-ci-watcher`) keyed off `needs.quality-gates-v2.outputs.*` by job name — a
      careless merge risks silently breaking cloud-build dispatch or orchestrator escalation fleet-wide with zero
      textual conflict to catch it. **Deliverable**: a short design noting exactly which jobs/outputs survive under the
      merged name, proven on ONE caller first (`agent-orchestrator` — already self-hosted, so a break is cheap to
      notice/revert) before any fleet rollout, following the same discipline as the concurrency fix above.

## Progress Log

- **2026-08-02 (slot-15, data_engineering craft)**: the "Open question" `[SCRIPT] P2` todo done (see checkbox above for
  full evidence) — PM's promote mechanism confirmed frozen-per-SHA-ref (matching the fleet), `ci-cd-flow.md` and
  `quickmerge.sh`'s own comments corrected to match. The `[VERIFY] P3` re-measure todo and the `[INFRA] P2`
  bookkeeping-job-cost todo remain open, untouched by this session.
- **2026-08-02 (slot-15) — `[VERIFY] P3` re-measure todo dispatched next; declined as genuinely premature, not a
  design/ambiguity block.** The concurrency fix this todo re-measures against landed at `2026-08-02T11:36:28Z`
  (`unified-trading-pm@f55f9b11e6`, confirmed via `git show -s --format=%ad`); checked at `2026-08-02T11:57Z` — only ~21
  minutes of run history exist since the fix, nowhere near the todo's own explicit "a few days after this lands" bar,
  and its own caveat is direct: "Don't estimate a % savings without this." A same-day re-measurement would produce a
  near-zero or statistically meaningless cancellation-rate sample, not a real answer. Declining + skipping (no
  `/blocked` — nothing ambiguous to decide, just elapsed time that hasn't elapsed) rather than force a low-quality
  number; recommending this todo be dispatch-gated by calendar time rather than re-checked every cycle (main/operator
  backlog-tuning call, per `RULES.md` § 4 — not applied here). Resume point: re-run the same
  push/pull_request/workflow_dispatch run-mix + cancellation-rate measurement once at least a few days of real PR churn
  have accumulated against the fixed workflow (i.e. any time from ~2026-08-05 onward).
